/*
 * wordcloud.js
 *
 * Word cloud / tag cloud renderer.
 *
 * JSON shape (ctx.raw):
 *   words[]      { text, value }  – array of word objects (entries without
 *                text or with a non-numeric value are skipped)
 *   max_words    optional integer cap (default 80; 0 draws nothing)
 *   rotation     "none" (default) | "mixed" (every fourth word vertical)
 *
 * Font size follows a zero-based square-root scale, so the area a word
 * covers (proportional to font-size squared) tracks its value; equal values
 * get equal sizes. Fonts are scaled down together when the words would not
 * fit the surface. Layout is a greedy Archimedean-spiral placement (stretched
 * to the box's aspect ratio) with measured text boxes and box collision
 * tests; the spiral runs out to the corners of the box, and a word that still
 * does not fit is retried at a smaller size before it is left out. The
 * accessible table lists every word and value, drawn or not.
 *
 * Interaction: each word is a focusable mark; click / Enter emits
 * `mj-chart-word-click` { text, value }.
 *
 * Registers: "word-cloud"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";

const DEFAULT_MAX_WORDS = 80
const MIN_FONT = 9
const MAX_FONT = 64
const BOX_GAP = 2
const PADDING = 4

/* Colour carries no meaning here; a few palette hues keep neighbours apart. */
const COLOR_SLOTS = 5

/* Spiral: distance between turns and arc length between candidates (px). */
const SPIRAL_SPACING = 5
const SPIRAL_STEP = 5

/* Retries at a smaller size before a word is left out. */
const SHRINK_FACTOR = 0.8
const SHRINK_TRIES = 3

let MEASURE_CONTEXT = null


function _fontFamily() {
  /*
   * The font family the chart text renders in (the library's sans token).
   */
  let family = ""
  try {
    family = getComputedStyle(document.documentElement).getPropertyValue("--mj-font-sans").trim()
  } catch (error) {
    family = ""
  }
  const resolved = family.length > 0 ? family : "system-ui, sans-serif"
  return resolved
}


function _measureWidth(text, fontSize, weight, family) {
  /*
   * Rendered width of a string, measured on a canvas in the chart font;
   * falls back to an estimate where no canvas is available.
   *
   * :returns: The width in pixels.
   */
  if (MEASURE_CONTEXT === null) {
    try {
      MEASURE_CONTEXT = document.createElement("canvas").getContext("2d")
    } catch (error) {
      MEASURE_CONTEXT = null
    }
  }
  let width = 0
  if (MEASURE_CONTEXT !== null && MEASURE_CONTEXT !== undefined) {
    MEASURE_CONTEXT.font = `${weight} ${fontSize}px ${family}`
    width = MEASURE_CONTEXT.measureText(text).width
  }
  if (width <= 0 || Number.isFinite(width) === false) {
    /* Wide (CJK / full-width) glyphs take about 1em, others about 0.6em. */
    let units = 0
    for (const character of text) {
      units = units + (character.codePointAt(0) > 0x2e80 ? 1 : 0.6)
    }
    width = units * fontSize
  }
  return width * 1.04
}


function _boxesOverlap(a, b) {
  /*
   * Test whether two boxes {x, y, w, h} overlap (keeping a small gap).
   *
   * :returns: True when the boxes intersect.
   */
  const apart = (
    a.x + a.w + BOX_GAP <= b.x ||
    b.x + b.w + BOX_GAP <= a.x ||
    a.y + a.h + BOX_GAP <= b.y ||
    b.y + b.h + BOX_GAP <= a.y
  )
  return apart === false
}


function _placeWord(placed, area, boxW, boxH) {
  /*
   * Find a free spot for a box on an Archimedean spiral around the centre
   * of the area, stretched to the area's aspect ratio. The spiral is
   * followed until it has passed the corners of the area.
   *
   * :param placed: The boxes placed so far.
   * :param area: { x, y, w, h } the box words must stay inside.
   * :returns: { x, y } top-left of the placed box, or null when none fits.
   */
  if (boxW > area.w || boxH > area.h) {
    return null
  }
  const cx = area.x + area.w / 2
  const cy = area.y + area.h / 2
  const stretchX = area.w >= area.h ? area.w / area.h : 1
  const stretchY = area.h > area.w ? area.h / area.w : 1
  const limit = Math.hypot(area.w / 2 / stretchX, area.h / 2 / stretchY) + SPIRAL_SPACING

  let angle = 0
  let radius = 0
  while (radius <= limit) {
    const x = cx + radius * Math.cos(angle) * stretchX - boxW / 2
    const y = cy + radius * Math.sin(angle) * stretchY - boxH / 2

    const inside = x >= area.x && y >= area.y &&
      x + boxW <= area.x + area.w && y + boxH <= area.y + area.h
    if (inside === true) {
      const candidate = { x: x, y: y, w: boxW, h: boxH }
      let collision = false
      for (let index = 0; index < placed.length; index = index + 1) {
        if (_boxesOverlap(candidate, placed[index]) === true) {
          collision = true
          break
        }
      }
      if (collision === false) {
        return { x: x, y: y }
      }
    }

    /* Advance about SPIRAL_STEP px along the curve; r grows one spacing per turn. */
    const advance = radius > SPIRAL_STEP ? SPIRAL_STEP / radius : 0.6
    angle = angle + advance
    radius = SPIRAL_SPACING * angle / (2 * Math.PI)
  }
  return null
}


function _readWords(raw) {
  /*
   * The usable words: entries with text and a finite, non-negative value,
   * sorted by value (largest first).
   */
  const list = raw !== null && raw !== undefined && Array.isArray(raw.words) === true ? raw.words : []
  const words = []
  for (let index = 0; index < list.length; index = index + 1) {
    const entry = list[index]
    if (entry === null || typeof entry !== "object") {
      continue
    }
    const text = entry.text !== null && entry.text !== undefined ? String(entry.text).trim() : ""
    const value = typeof entry.value === "number" ? entry.value : Number(entry.value)
    if (text.length === 0 || Number.isFinite(value) === false || value < 0) {
      continue
    }
    words.push({ text: text, value: value, source: entry, order: index })
  }
  words.sort((a, b) => {
    const byValue = b.value - a.value
    return byValue !== 0 ? byValue : a.order - b.order
  })
  return words
}


export function render(ctx) {
  /*
   * Render a word cloud.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const allWords = _readWords(raw)
  let maxWords = DEFAULT_MAX_WORDS
  if (typeof raw.max_words === "number" && Number.isFinite(raw.max_words) === true &&
      raw.max_words >= 0) {
    maxWords = Math.floor(raw.max_words)
  }
  const rotation = raw.rotation === "mixed" ? "mixed" : "none"

  const root = svgEl("g", { part: "plot" }, [])
  const words = allWords.slice(0, maxWords)

  ctx.setTable({
    columns: ["Word", "Value"],
    rows: words.map((word) => [word.text, word.value]),
    caption: ctx.label
  })

  if (words.length === 0) {
    return root
  }

  const area = {
    x: PADDING,
    y: PADDING,
    w: Math.max(ctx.width - PADDING * 2, 10),
    h: Math.max(ctx.height - PADDING * 2, 10)
  }
  const family = _fontFamily()
  const maxValue = words[0].value

  /* Zero-based sqrt scale: area ~ value. A degenerate domain uses one size. */
  let topFont = Math.min(MAX_FONT, area.h * 0.22, area.w * 0.12)
  const sizeOf = (value, top) => {
    const share = maxValue > 0 ? Math.sqrt(value / maxValue) : 1
    return Math.max(MIN_FONT, top * share)
  }

  /* Shrink every size together while the words need more than ~55% of the box. */
  for (let pass = 0; pass < 8; pass = pass + 1) {
    let needed = 0
    for (let index = 0; index < words.length; index = index + 1) {
      const size = sizeOf(words[index].value, topFont)
      const weight = words[index].value >= maxValue * 0.6 ? 600 : 400
      needed = needed + (_measureWidth(words[index].text, size, weight, family) + BOX_GAP) *
        (size * 1.15 + BOX_GAP)
    }
    const ratio = needed / (area.w * area.h * 0.55)
    if (ratio <= 1 || topFont <= MIN_FONT) {
      break
    }
    topFont = Math.max(MIN_FONT, topFont / Math.sqrt(ratio))
  }

  const placed = []
  const group = svgEl("g", {}, [])
  root.appendChild(group)

  for (let wi = 0; wi < words.length; wi = wi + 1) {
    const word = words[wi]
    const weight = word.value >= maxValue * 0.6 ? 600 : 400
    const vertical = rotation === "mixed" && wi % 4 === 3

    let fontSize = sizeOf(word.value, topFont)
    /* A word longer than the box is first scaled to fit its width. */
    const span = vertical === true ? area.h : area.w
    const natural = _measureWidth(word.text, fontSize, weight, family)
    if (natural > span * 0.98) {
      fontSize = Math.max(MIN_FONT, fontSize * span * 0.98 / natural)
    }
    let position = null
    let boxW = 0
    let boxH = 0
    for (let attempt = 0; attempt <= SHRINK_TRIES && position === null; attempt = attempt + 1) {
      if (attempt > 0) {
        fontSize = Math.max(MIN_FONT, fontSize * SHRINK_FACTOR)
      }
      const textW = _measureWidth(word.text, fontSize, weight, family)
      const textH = fontSize * 1.15
      boxW = vertical === true ? textH : textW
      boxH = vertical === true ? textW : textH
      position = _placeWord(placed, area, boxW, boxH)
    }
    if (position === null) {
      continue
    }
    placed.push({ x: position.x, y: position.y, w: boxW, h: boxH })

    const centerX = position.x + boxW / 2
    const centerY = position.y + boxH / 2
    const label = `${word.text}: ${formatNumber(word.value)}`

    const wordEl = svgEl("g", {
      tabindex: "0",
      role: "img",
      "aria-label": label,
      part: "word"
    }, [])

    const attrs = {
      x: centerX.toFixed(2),
      y: centerY.toFixed(2),
      "text-anchor": "middle",
      "dominant-baseline": "central",
      "font-size": fontSize.toFixed(1),
      "font-weight": String(weight),
      fill: ctx.colorFor(wi % COLOR_SLOTS)
    }
    if (vertical === true) {
      attrs.transform = `rotate(-90,${centerX.toFixed(2)},${centerY.toFixed(2)})`
    }
    wordEl.appendChild(svgEl("text", attrs, word.text))
    wordEl.appendChild(svgEl("title", null, label))

    const captured = word.source
    const handler = () => {
      ctx.emit("mj-chart-word-click", { text: captured.text, value: captured.value })
    }
    wordEl.addEventListener("click", handler)
    wordEl.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        handler()
      }
    })

    group.appendChild(wordEl)
  }

  return root
}


registerRenderer("word-cloud", render, { legend: "none" })
