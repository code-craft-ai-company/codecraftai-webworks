/*
 * wordcloud.js
 *
 * Word cloud / tag cloud renderer.
 *
 * JSON shape (ctx.raw):
 *   words[]      { text, value }  – array of word objects
 *   max_words    optional integer cap (default 80)
 *   rotation     "none" (default) | "mixed" (±90° allowed)
 *
 * Font size is driven by a sqrt scale so area tracks frequency.
 * Layout uses a greedy archimedean-spiral placement with AABB collision
 * detection – no external library.
 *
 * Registers: "word-cloud"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml } from "../svgdraw.js";
import { sqrtScale } from "../scales.js";


/* Categorical color tokens (supplementary; size is the primary encoding). */
const COLORS = [
  "var(--mj-color-accent-500, #2563eb)",
  "var(--mj-color-success, #15803d)",
  "var(--mj-color-warning, #b45309)",
  "var(--mj-color-danger, #b91c1c)",
  "var(--mj-color-accent-300, #80a8ff)",
  "var(--mj-color-accent-800, #122f78)",
  "var(--mj-color-neutral-500, #6b7280)"
]


function _approxTextWidth(text, fontSize) {
  /*
   * Approximate rendered width of a string at a given font size using an
   * average character-width ratio of ~0.58 for a proportional sans-serif.
   *
   * :returns: Estimated pixel width.
   */
  const width = text.length * fontSize * 0.58
  return width
}


function _boxesOverlap(a, b) {
  /*
   * Test whether two AABBs {x, y, w, h} overlap (with a 2px gap).
   *
   * :returns: True when the boxes intersect.
   */
  const gap = 2
  const noOverlap = (
    a.x + a.w + gap <= b.x ||
    b.x + b.w + gap <= a.x ||
    a.y + a.h + gap <= b.y ||
    b.y + b.h + gap <= a.y
  )
  return noOverlap === false
}


function _placeWord(placed, cx, cy, boxW, boxH, maxR) {
  /*
   * Try to place a word box (boxW x boxH) on an Archimedean spiral centred
   * at (cx, cy) within a maxR radius.
   *
   * :returns: { x, y } top-left of the placed box, or null on failure.
   */
  const a = 0.3
  const b = 0.25
  const maxSteps = 800

  for (let step = 0; step < maxSteps; step = step + 1) {
    const angle = step * 0.25
    const r = a + b * angle
    const tx = cx + r * Math.cos(angle) - boxW / 2
    const ty = cy + r * Math.sin(angle) - boxH / 2

    /* Reject if out of bounds. */
    if (tx < 0 || ty < 0 || tx + boxW > cx * 2 || ty + boxH > cy * 2) {
      if (r > maxR) {
        break
      }
      continue
    }

    const candidate = { x: tx, y: ty, w: boxW, h: boxH }
    let collision = false
    for (let p = 0; p < placed.length; p = p + 1) {
      if (_boxesOverlap(candidate, placed[p]) === true) {
        collision = true
        break
      }
    }
    if (collision === false) {
      return { x: tx, y: ty }
    }
  }

  return null
}


export function render(ctx) {
  /*
   * Render a word cloud.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw
  const rawWords = (raw !== null && raw !== undefined && Array.isArray(raw.words))
    ? raw.words
    : []
  const maxWords = (raw !== null && raw !== undefined && typeof raw.max_words === "number")
    ? raw.max_words
    : 80
  const rotation = (raw !== null && raw !== undefined)
    ? (raw.rotation || "none")
    : "none"

  const root = svgEl("g", { part: "plot" }, [])

  if (rawWords.length === 0) {
    return root
  }

  /* Sort by value descending, cap at max_words. */
  const sorted = rawWords.slice().sort((a, b) => {
    const av = typeof a.value === "number" ? a.value : 0
    const bv = typeof b.value === "number" ? b.value : 0
    return bv - av
  })
  const words = sorted.slice(0, maxWords)

  /* Find value extent. */
  let minVal = words[words.length - 1].value || 0
  let maxVal = words[0].value || 1
  if (minVal === maxVal) {
    maxVal = minVal + 1
  }

  /* Font-size scale: sqrt so area (proportional to size²) tracks value. */
  const minFont = 10
  const maxFont = Math.min(64, ctx.height * 0.22)
  const fontScale = sqrtScale([minVal, maxVal], [minFont, maxFont])

  const cx = ctx.width / 2
  const cy = ctx.height / 2
  const maxR = Math.min(cx, cy) * 0.95

  const placed = []
  const group = svgEl("g", {
    transform: `translate(0,0)`
  }, [])
  root.appendChild(group)

  for (let wi = 0; wi < words.length; wi = wi + 1) {
    const word = words[wi]
    const text = String(word.text || "")
    const value = typeof word.value === "number" ? word.value : 0
    const fontSize = Math.round(fontScale(value))

    const textW = _approxTextWidth(text, fontSize)
    const textH = fontSize * 1.2

    /* Optionally rotate ±90° in mixed mode. */
    let rotDeg = 0
    if (rotation === "mixed" && wi % 4 === 3) {
      rotDeg = 90
    }

    const boxW = rotDeg === 90 ? textH : textW
    const boxH = rotDeg === 90 ? textW : textH

    const pos = _placeWord(placed, cx, cy, boxW, boxH, maxR)
    if (pos === null) {
      continue
    }

    placed.push({ x: pos.x, y: pos.y, w: boxW, h: boxH })

    const color = COLORS[wi % COLORS.length]
    const ariaLabel = `${text}: ${value}`
    const textX = pos.x + boxW / 2
    const textY = pos.y + boxH / 2 + fontSize * 0.35

    const wordEl = svgEl("g", {
      tabindex: "0",
      role: "img",
      "aria-label": ariaLabel,
      part: "word"
    }, [])

    const attrs = {
      x: textX, y: textY,
      "text-anchor": "middle",
      "font-size": fontSize,
      "font-weight": value >= maxVal * 0.6 ? "600" : "400",
      fill: color
    }
    if (rotDeg !== 0) {
      attrs.transform = `rotate(${rotDeg},${textX},${textY - fontSize * 0.35})`
    }

    wordEl.appendChild(svgEl("text", attrs, escapeHtml(text)))
    wordEl.appendChild(svgEl("title", null, ariaLabel))

    const capturedWord = word
    const handler = () => {
      ctx.emit("mj-chart-word-click", {
        text: capturedWord.text,
        value: capturedWord.value
      })
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


registerRenderer("word-cloud", render)
