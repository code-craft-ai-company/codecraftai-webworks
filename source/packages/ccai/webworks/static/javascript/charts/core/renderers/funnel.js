/*
 * funnel.js
 *
 * Funnel / conversion-funnel renderer.
 *
 * Registers: "funnel"
 *
 * ctx.model shape (common envelope):
 *   categories: string[]          stage names
 *   series[0].values: number[]    stage counts / rates (non-negative)
 *
 * Modes (attribute `mode`):
 *   funnel   (default) stages run from the top (or left) and narrow toward
 *            the last stage
 *   pyramid  the same segments stacked the other way: the first stage is
 *            the base at the bottom (or right) and the shape narrows upward
 *
 * Orientation:
 *   "vertical"   stages top -> bottom (default)
 *   "horizontal" stages left -> right
 *
 * Each segment is a trapezoid whose wide edge is the stage's value and whose
 * narrow edge is the next stage's value (the last stage narrows to half its
 * own width), all on one scale relative to the largest stage. Stage names
 * sit beside the shape (above it when horizontal), the value is printed in
 * the segment when it fits and next to it otherwise, and the signed change
 * to the next stage ("-37.1%", "+12.0%") is annotated between stages.
 *
 * Stages without a numeric value are left out; a negative value is invalid,
 * left out, and reported with `mj-chart-error`.
 *
 * SVG primitives: <polygon> per segment, <text> for stage and value labels.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { linearScale } from "../scales.js";


const SEGMENT_GAP = 4;
const LABEL_FONT = 11;
const CHANGE_FONT = 10;
const OUTER_MARGIN = 12;
const LAST_STAGE_NECK = 0.5;


function _textWidth(text, fontSize) {
  /*
   * Estimate the rendered width of a label.
   */
  const width = String(text).length * fontSize * 0.58
  return width
}


function _fitText(text, maxWidth, fontSize) {
  /*
   * Shorten a label with an ellipsis so it fits a width.
   */
  const label = String(text)
  if (_textWidth(label, fontSize) <= maxWidth) {
    return label
  }
  const characters = Math.floor(maxWidth / (fontSize * 0.58)) - 1
  if (characters < 2) {
    return ""
  }
  const fitted = label.slice(0, characters) + "…"
  return fitted
}


function _changeText(from, to) {
  /*
   * The signed change between two stages ("-37.1%", "+12.0%"), or "" when
   * the first stage is zero.
   */
  if (from <= 0) {
    return ""
  }
  const change = ((to - from) / from) * 100
  const magnitude = formatNumber(Math.abs(change), { minimumFractionDigits: 1, maximumFractionDigits: 1 })
  const sign = change > 0 ? "+" : (change < 0 ? "-" : "")
  const text = `${sign}${magnitude}%`
  return text
}


function _collectStages(categories, values) {
  /*
   * The drawable stages in order, plus the names of invalid ones.
   *
   * :returns: { stages: [{ label, value, index }], negatives: [label] }
   */
  const stages = []
  const negatives = []
  for (let index = 0; index < categories.length; index = index + 1) {
    const value = values[index]
    if (typeof value !== "number" || Number.isFinite(value) === false) {
      continue
    }
    if (value < 0) {
      negatives.push(String(categories[index]))
      continue
    }
    stages.push({ label: String(categories[index]), value: value, index: index })
  }
  const collected = { stages: stages, negatives: negatives }
  return collected
}


export function render(ctx) {
  /*
   * Render a funnel or pyramid chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const isPyramid = ctx.attrs("mode", "funnel") === "pyramid"
  const horizontal = ctx.orientation === "horizontal"
  const root = svgEl("g", { part: "plot" }, [])

  const categories = model.categories
  const series = model.series
  if (categories.length === 0 || series.length === 0) {
    return root
  }

  const collected = _collectStages(categories, series[0].values)
  if (collected.negatives.length > 0) {
    ctx.emit("mj-chart-error", {
      message: `funnel: negative stage values are not drawn (${collected.negatives.join(", ")})`
    })
  }
  const stages = collected.stages
  const n = stages.length
  if (n === 0) {
    return root
  }

  for (let i = 0; i < n; i = i + 1) {
    stages[i].color = ctx.colorFor(stages[i].index)
    stages[i].change = i + 1 < n ? _changeText(stages[i].value, stages[i + 1].value) : ""
  }

  const valueName = String(series[0].name || "Value")
  ctx.setLegend(stages.map((stage) => {
    return { label: stage.label, color: stage.color }
  }))
  ctx.setTable({
    columns: ["Stage", valueName, "Change to next stage"],
    rows: stages.map((stage) => [stage.label, stage.value, stage.change])
  })

  /* Margins: stage names on one side, change annotations on the other. */
  let longestName = 0
  let longestChange = 0
  for (let i = 0; i < n; i = i + 1) {
    longestName = Math.max(longestName, _textWidth(stages[i].label, LABEL_FONT))
    longestChange = Math.max(longestChange, _textWidth(stages[i].change, CHANGE_FONT))
  }
  const margin = horizontal === true
    ? { top: LABEL_FONT + 10, right: OUTER_MARGIN, bottom: CHANGE_FONT + 10, left: OUTER_MARGIN }
    : {
        top: OUTER_MARGIN,
        right: Math.max(longestChange + 12, OUTER_MARGIN),
        bottom: OUTER_MARGIN,
        left: Math.min(longestName + 18, ctx.width * 0.35)
      }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  let maxValue = 0
  for (let i = 0; i < n; i = i + 1) {
    maxValue = Math.max(maxValue, stages[i].value)
  }
  if (maxValue <= 0) {
    maxValue = 1
  }

  /* Each stage gets equal space along the primary axis. */
  const primarySpan = horizontal === true ? plotW : plotH
  /* A vertical funnel is kept from stretching into a flat band on wide plots. */
  const crossSpan = horizontal === true ? plotH : Math.min(plotW, Math.max(plotH * 2.4, 240))
  const crossOffset = horizontal === true ? 0 : (plotW - crossSpan) / 2
  const segmentStep = Math.max((primarySpan - SEGMENT_GAP * (n - 1)) / n, 1)
  const halfWidthScale = linearScale([0, maxValue], [0, crossSpan / 2])
  const crossCenter = crossSpan / 2

  const plot = svgEl("g", { transform: `translate(${(margin.left + crossOffset).toFixed(2)},${margin.top})` }, [])
  root.appendChild(plot)
  const segments = svgEl("g", { part: "segments" }, [])
  plot.appendChild(segments)
  const labels = svgEl("g", { "aria-hidden": "true", "pointer-events": "none" }, [])
  plot.appendChild(labels)

  for (let i = 0; i < n; i = i + 1) {
    const stage = stages[i]
    const nextValue = i + 1 < n ? stages[i + 1].value : stage.value * LAST_STAGE_NECK

    /* Pyramid: the first stage is laid at the far end (the base). */
    const slot = isPyramid === true ? n - 1 - i : i
    const slotStart = slot * (segmentStep + SEGMENT_GAP)
    const slotEnd = slotStart + segmentStep
    const wideAt = isPyramid === true ? slotEnd : slotStart
    const narrowAt = isPyramid === true ? slotStart : slotEnd

    const halfWide = halfWidthScale(stage.value)
    const halfNarrow = halfWidthScale(nextValue)

    const corner = (primary, cross) => {
      const point = horizontal === true
        ? `${primary.toFixed(2)},${cross.toFixed(2)}`
        : `${cross.toFixed(2)},${primary.toFixed(2)}`
      return point
    }
    const points = [
      corner(wideAt, crossCenter - halfWide),
      corner(wideAt, crossCenter + halfWide),
      corner(narrowAt, crossCenter + halfNarrow),
      corner(narrowAt, crossCenter - halfNarrow)
    ].join(" ")

    const description = stage.change !== ""
      ? `${stage.label}: ${formatNumber(stage.value)} (${stage.change} to next stage)`
      : `${stage.label}: ${formatNumber(stage.value)}`
    const polygon = svgEl("polygon", {
      points: points,
      fill: stage.color,
      stroke: stage.color,
      "stroke-width": 1,
      "stroke-linejoin": "round",
      part: "segment",
      tabindex: "0",
      role: "img",
      "aria-label": description
    }, [svgEl("title", null, description)])

    const clickHandler = () => {
      ctx.emit("mj-chart-segment-click", {
        category: stage.label,
        value: stage.value,
        index: stage.index
      })
    }
    polygon.addEventListener("click", clickHandler)
    polygon.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        clickHandler()
      }
    })
    segments.appendChild(polygon)

    /* Value label: inside when the segment's narrow edge can hold it. */
    const midPrimary = slotStart + segmentStep / 2
    const valueText = formatNumber(stage.value)
    const valueWidth = _textWidth(valueText, LABEL_FONT)
    const inside = horizontal === true
      ? valueWidth + 8 <= segmentStep && halfNarrow * 2 >= LABEL_FONT + 4
      : valueWidth + 8 <= halfNarrow * 2 && segmentStep >= LABEL_FONT + 2

    if (horizontal === true) {
      labels.appendChild(svgEl("text", {
        x: midPrimary.toFixed(2),
        y: inside === true ? crossCenter.toFixed(2) : (crossCenter + Math.max(halfWide, halfNarrow) + LABEL_FONT).toFixed(2),
        "text-anchor": "middle",
        "dominant-baseline": "middle",
        "font-size": LABEL_FONT,
        "font-weight": "600",
        fill: inside === true ? "var(--mj-text-on-accent, #ffffff)" : "var(--mj-text, #14181f)"
      }, valueText))
      /* Stage name above its segment. */
      labels.appendChild(svgEl("text", {
        x: midPrimary.toFixed(2),
        y: -8,
        "text-anchor": "middle",
        "font-size": LABEL_FONT,
        fill: "var(--mj-text, #14181f)"
      }, _fitText(stage.label, segmentStep + SEGMENT_GAP - 4, LABEL_FONT)))
    } else {
      labels.appendChild(svgEl("text", {
        x: inside === true ? crossCenter.toFixed(2) : (crossCenter + Math.max(halfWide, halfNarrow) + 6).toFixed(2),
        y: midPrimary.toFixed(2),
        "text-anchor": inside === true ? "middle" : "start",
        "dominant-baseline": "middle",
        "font-size": LABEL_FONT,
        "font-weight": "600",
        fill: inside === true ? "var(--mj-text-on-accent, #ffffff)" : "var(--mj-text, #14181f)"
      }, valueText))
      /* Stage name to the left of the shape. */
      labels.appendChild(svgEl("text", {
        x: -10,
        y: midPrimary.toFixed(2),
        "text-anchor": "end",
        "dominant-baseline": "middle",
        "font-size": LABEL_FONT,
        fill: "var(--mj-text, #14181f)"
      }, _fitText(stage.label, margin.left + crossOffset - 14, LABEL_FONT)))
    }

    /* Change to the next stage, at the boundary between the two. */
    if (stage.change !== "") {
      const boundary = isPyramid === true ? slotStart - SEGMENT_GAP / 2 : slotEnd + SEGMENT_GAP / 2
      if (horizontal === true) {
        labels.appendChild(svgEl("text", {
          x: boundary.toFixed(2),
          y: (plotH + CHANGE_FONT + 4).toFixed(2),
          "text-anchor": "middle",
          "font-size": CHANGE_FONT,
          fill: "var(--mj-text-muted, #5f6673)"
        }, stage.change))
      } else {
        labels.appendChild(svgEl("text", {
          x: (crossCenter + halfNarrow + 10).toFixed(2),
          y: boundary.toFixed(2),
          "text-anchor": "start",
          "dominant-baseline": "middle",
          "font-size": CHANGE_FONT,
          fill: "var(--mj-text-muted, #5f6673)"
        }, stage.change))
      }
    }
  }

  return root
}


registerRenderer("funnel", render, { legend: "none" });
