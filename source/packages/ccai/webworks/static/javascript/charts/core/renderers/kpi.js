/*
 * kpi.js
 *
 * KPI card renderer (big-number metric card).
 *
 * JSON shape (ctx.raw):
 *   kpi.value          primary metric value (a number or numeric string; a
 *                      missing / non-numeric value shows "—", never 0)
 *   kpi.format         optional number format (see heatmaptable.js
 *                      formatValue): ",.0f", "$,.0f", ".1%", ".3s",
 *                      "compact", "percent", or Intl.NumberFormat options
 *   kpi.label          optional sub-label below the value
 *   kpi.comparison     optional { value, label } – prior-period baseline
 *   kpi.trend          "up" | "down" | "flat" – manual override of the arrow;
 *                      computed from comparison when omitted
 *   kpi.good           "up" (default) | "down" | "neutral" – which direction
 *                      is good, so a falling cost or churn reads as good
 *   kpi.spark          optional array of numbers – sparkline values (nulls
 *                      are gaps)
 *
 * The change badge shows the percentage change against the comparison; when
 * the baseline is 0 the percentage is undefined and the absolute change is
 * shown instead. The headline font is fitted to the card width.
 *
 * Interaction: the card is one focusable mark; click / Enter emits
 * `mj-chart-kpi-click` { value, label }.
 *
 * Shared helpers (used by scorecard.js): readNumber, changeInfo, trendArrow,
 * sparkline, fitFontSize, estimateWidth.
 *
 * Registers: "kpi"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, linePath, formatNumber } from "../svgdraw.js";
import { linearScale } from "../scales.js";
import { formatValue } from "./heatmaptable.js";

const CHAR_WIDTH = 0.6
const GOOD_COLOR = "var(--mj-color-success, #15803d)"
const BAD_COLOR = "var(--mj-color-danger, #b91c1c)"
const NEUTRAL_COLOR = "var(--mj-text-muted, #5f6673)"


export function readNumber(value) {
  /*
   * A finite number from a number or numeric string, else null.
   */
  let numeric = null
  if (typeof value === "number" && Number.isFinite(value) === true) {
    numeric = value
  } else if (typeof value === "string" && value.trim().length > 0 &&
      Number.isFinite(Number(value)) === true) {
    numeric = Number(value)
  }
  return numeric
}


export function estimateWidth(text, fontSize) {
  /*
   * Estimated rendered width of a label.
   */
  const width = String(text).length * fontSize * CHAR_WIDTH
  return width
}


export function fitFontSize(text, maxWidth, preferred, minimum) {
  /*
   * The largest font size up to `preferred` at which text fits maxWidth.
   */
  const length = Math.max(String(text).length, 1)
  const fitted = Math.min(preferred, maxWidth / (length * CHAR_WIDTH))
  return Math.max(fitted, minimum)
}


export function changeInfo(direction, good) {
  /*
   * Meaning of a change: its arrow direction and the colour that says
   * whether it is good, from the direction that is good for the metric.
   *
   * :param direction: "up" | "down" | "flat".
   * :param good: "up" | "down" | "neutral".
   * :returns: { direction, color, verdict } -- verdict "good" | "bad" |
   *     "neutral".
   */
  let verdict = "neutral"
  if (direction !== "flat" && good !== "neutral") {
    verdict = direction === good ? "good" : "bad"
  }
  const color = verdict === "good" ? GOOD_COLOR : (verdict === "bad" ? BAD_COLOR : NEUTRAL_COLOR)
  return { direction: direction, color: color, verdict: verdict }
}


export function trendArrow(direction, cx, cy, size, color) {
  /*
   * A trend arrow <path> (a bar for "flat"). Direction is also spelled out
   * in the containing mark's label, so it is never colour alone.
   */
  const half = size / 2
  let d = ""
  if (direction === "up") {
    d = `M${cx},${cy - half} L${cx + half},${cy + half} L${cx - half},${cy + half} Z`
  } else if (direction === "down") {
    d = `M${cx},${cy + half} L${cx + half},${cy - half} L${cx - half},${cy - half} Z`
  } else {
    d = `M${cx - half},${cy - 1.5} L${cx + half},${cy - 1.5} L${cx + half},${cy + 1.5} ` +
      `L${cx - half},${cy + 1.5} Z`
  }
  const arrow = svgEl("path", { d: d, fill: color, "aria-hidden": "true" }, [])
  return arrow
}


export function sparkline(values, x, y, width, height, color) {
  /*
   * A small sparkline <path> within a box; null entries are gaps.
   *
   * :returns: An SVG <g>, or null when fewer than two values are numbers.
   */
  const numbers = values.map((value) => readNumber(value))
  const finite = numbers.filter((value) => value !== null)
  if (finite.length < 2 || width <= 0 || height <= 0) {
    return null
  }
  let low = Math.min(...finite)
  let high = Math.max(...finite)
  if (low === high) {
    low = low - 1
    high = high + 1
  }
  const xScale = linearScale([0, Math.max(values.length - 1, 1)], [x, x + width])
  const yScale = linearScale([low, high], [y + height, y])
  const points = numbers.map((value, index) => (value === null ? null : { x: xScale(index), y: yScale(value) }))
  const spark = svgEl("g", { part: "spark", "aria-hidden": "true" }, [
    svgEl("path", {
      d: linePath(points), fill: "none", stroke: color, "stroke-width": 1.5,
      "stroke-linejoin": "round", "stroke-linecap": "round"
    }, [])
  ])
  return spark
}


export function render(ctx) {
  /*
   * Render a KPI card.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const kpi = raw.kpi !== null && typeof raw.kpi === "object" ? raw.kpi : {}

  const value = readNumber(kpi.value)
  const format = kpi.format !== undefined ? kpi.format : null
  const label = kpi.label !== undefined && kpi.label !== null ? String(kpi.label) : ""
  const comparison = kpi.comparison !== null && typeof kpi.comparison === "object" ? kpi.comparison : null
  const baseline = comparison !== null ? readNumber(comparison.value) : null
  const spark = Array.isArray(kpi.spark) === true ? kpi.spark : []
  const good = kpi.good === "down" || kpi.good === "neutral" ? kpi.good : "up"

  const root = svgEl("g", { part: "plot" }, [])
  const w = ctx.width
  const h = ctx.height
  const midX = w / 2
  const pad = 12

  const valueText = value !== null ? formatValue(value, format) : "—"

  /* Change against the comparison. */
  let change = null
  if (value !== null && baseline !== null) {
    const delta = value - baseline
    let direction = delta > 0 ? "up" : (delta < 0 ? "down" : "flat")
    if (kpi.trend === "up" || kpi.trend === "down" || kpi.trend === "flat") {
      direction = kpi.trend
    }
    const sign = delta > 0 ? "+" : (delta < 0 ? "−" : "±")
    const text = baseline !== 0
      ? `${sign}${formatNumber(Math.abs(delta / baseline) * 100, { maximumFractionDigits: 1 })}%`
      : `${sign}${formatValue(Math.abs(delta), format)}`
    change = {
      delta: delta,
      percent: baseline !== 0 ? delta / Math.abs(baseline) : null,
      text: text,
      label: comparison.label !== undefined && comparison.label !== null
        ? String(comparison.label)
        : "vs prior",
      info: changeInfo(direction, good)
    }
  }

  /* Accessible table. */
  const rows = [["Value", value]]
  if (baseline !== null) {
    rows.push([change !== null ? `Comparison (${change.label})` : "Comparison", baseline])
  }
  if (change !== null) {
    rows.push(["Change", change.delta])
    rows.push(["Change (%)", change.percent !== null ? change.text : "n/a"])
  }
  ctx.setTable({ columns: [label.length > 0 ? label : "Measure", "Value"], rows: rows, caption: ctx.label })

  /* Vertical bands: value, label, badge, sparkline (dropped when short). */
  const sparkH = spark.length >= 2 && h >= 150 ? Math.min(40, h * 0.18) : 0
  const badgeH = change !== null ? 22 : 0
  const labelH = label.length > 0 ? 18 : 0
  const room = Math.max(h - pad * 2 - sparkH - badgeH - labelH - (sparkH > 0 ? 8 : 0), 16)
  const valueFont = fitFontSize(valueText, w - pad * 2, Math.min(room * 0.9, 56), 12)
  const blockH = valueFont + labelH + (badgeH > 0 ? badgeH + 8 : 0)
  const top = pad + Math.max((h - pad * 2 - sparkH - blockH) / 2, 0)

  const card = svgEl("g", {
    tabindex: "0", role: "img", part: "kpi-card",
    "aria-label": `${label.length > 0 ? label + ": " : ""}${value !== null ? valueText : "no data"}` +
      (change !== null
        ? `, ${change.info.direction} ${change.text} ${change.label} (${change.info.verdict})`
        : "")
  }, [])
  root.appendChild(card)

  card.appendChild(svgEl("rect", {
    x: 0.5, y: 0.5, width: Math.max(w - 1, 1), height: Math.max(h - 1, 1), rx: 8,
    fill: "var(--mj-surface, #ffffff)", stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
  }, []))

  const valueY = top + valueFont * 0.85
  card.appendChild(svgEl("text", {
    x: midX, y: valueY.toFixed(2), "text-anchor": "middle",
    "font-size": valueFont.toFixed(1), "font-weight": "700",
    fill: value !== null ? "var(--mj-text, #14181f)" : "var(--mj-text-muted, #5f6673)",
    part: "kpi-value"
  }, valueText))

  let cursor = top + valueFont
  if (labelH > 0) {
    card.appendChild(svgEl("text", {
      x: midX, y: (cursor + 14).toFixed(2), "text-anchor": "middle", "font-size": 13,
      fill: "var(--mj-text-muted, #5f6673)", part: "kpi-label"
    }, label))
    cursor = cursor + labelH
  }

  if (change !== null) {
    /* Arrow, change and comparison label as one centred group. */
    let font = 11
    const arrowSize = 8
    let contentW = arrowSize + 4 + estimateWidth(change.text, font) + 8 +
      estimateWidth(change.label, font - 1)
    if (contentW > w - pad * 2) {
      font = Math.max(8, font * (w - pad * 2) / contentW)
      contentW = arrowSize + 4 + estimateWidth(change.text, font) + 8 + estimateWidth(change.label, font - 1)
    }
    const badgeW = arrowSize + 4 + estimateWidth(change.text, font) + 12
    const startX = midX - contentW / 2
    const badgeY = cursor + 8
    const badge = svgEl("g", { part: "kpi-delta", "aria-hidden": "true" }, [])
    badge.appendChild(svgEl("rect", {
      x: (startX - 6).toFixed(2), y: badgeY.toFixed(2), width: badgeW.toFixed(2), height: badgeH,
      rx: 4, fill: change.info.color, "fill-opacity": 0.12
    }, []))
    badge.appendChild(trendArrow(change.info.direction, startX + arrowSize / 2,
      badgeY + badgeH / 2, arrowSize, change.info.color))
    badge.appendChild(svgEl("text", {
      x: (startX + arrowSize + 4).toFixed(2), y: (badgeY + badgeH / 2 + font * 0.35).toFixed(2),
      "font-size": font.toFixed(1), "font-weight": "600", fill: change.info.color
    }, change.text))
    badge.appendChild(svgEl("text", {
      x: (startX - 6 + badgeW + 6).toFixed(2), y: (badgeY + badgeH / 2 + font * 0.35).toFixed(2),
      "font-size": (font - 1).toFixed(1), fill: "var(--mj-text-muted, #5f6673)"
    }, change.label))
    card.appendChild(badge)
  }

  if (sparkH > 0) {
    const sparkEl = sparkline(spark, pad, h - pad - sparkH, w - pad * 2, sparkH, ctx.colorFor(0))
    if (sparkEl !== null) {
      card.appendChild(sparkEl)
    }
  }

  card.appendChild(svgEl("title", null, card.getAttribute("aria-label")))
  const handler = () => {
    ctx.emit("mj-chart-kpi-click", { value: value, label: label })
  }
  card.addEventListener("click", handler)
  card.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      handler()
    }
  })

  return root
}


registerRenderer("kpi", render, { legend: "none" })
