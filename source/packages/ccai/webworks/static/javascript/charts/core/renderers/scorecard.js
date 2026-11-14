/*
 * scorecard.js
 *
 * Scorecard renderer — a grid of KPI tiles, each showing a label, a
 * headline value, a change indicator with trend arrow, a sparkline and a
 * progress bar toward a target. Every element has its own band in the tile,
 * so nothing is drawn over the text.
 *
 * Registered types:
 *   "scorecard"
 *
 * ctx.raw shape:
 *   raw.metrics  [{label, value, format?, target?, delta?, trend?, good?,
 *                 sparkline?}]
 *     value      a number or numeric string ("—" when missing)
 *     format     number format (heatmaptable.js formatValue): ",.0f",
 *                "$,.2s", ".1%", "compact", "percent", Intl options
 *     delta      fractional change (0.12 = +12%)
 *     trend      "up" | "down" | "flat" arrow override
 *     good       "up" (default) | "down" | "neutral": which direction is good
 *                (churn, cost and latency are "down"), used for the colour
 *     target     the progress bar shows attainment of the target: value /
 *                target, or target / value when lower is better
 *   raw.columns  optional number of tile columns
 *
 * Layout: tiles wrap into a grid. orientation "horizontal" (default) fills
 * rows of tiles at least ~150px wide; "vertical" stacks one tile per row.
 * mode="compact" (attribute) shows only label and value.
 *
 * Interaction: each tile is one focusable group; click / Enter anywhere on
 * it emits `mj-chart-tile-click` { metric, index }.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { formatValue } from "./heatmaptable.js";
import { readNumber, changeInfo, trendArrow, sparkline, fitFontSize } from "./kpi.js";

const MIN_TILE_W = 150
const GAP = 8
const PAD = 12


function _truncate(text, maxWidth, fontSize) {
  /*
   * Shorten a label with an ellipsis to about maxWidth pixels.
   */
  const value = String(text)
  const capacity = Math.max(Math.floor(maxWidth / (fontSize * 0.6)), 1)
  if (value.length <= capacity) {
    return value
  }
  return value.slice(0, Math.max(capacity - 1, 1)) + "…"
}


export function render(ctx) {
  /*
   * Render a scorecard grid of KPI tiles.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const root = svgEl("g", { part: "plot" }, [])
  const metrics = (Array.isArray(raw.metrics) === true ? raw.metrics : [])
    .filter((metric) => metric !== null && typeof metric === "object")

  ctx.setTable({
    columns: ["Metric", "Value", "Target", "Change (%)"],
    rows: metrics.map((metric) => {
      const delta = readNumber(metric.delta)
      return [
        metric.label !== undefined && metric.label !== null ? String(metric.label) : "",
        readNumber(metric.value),
        readNumber(metric.target),
        delta !== null ? delta * 100 : null
      ]
    }),
    caption: ctx.label
  })

  if (metrics.length === 0) {
    return root
  }

  const vertical = ctx.orientation === "vertical"
  const compact = ctx.attrs("mode", "full") === "compact"
  const plotW = Math.max(ctx.width - 2, 10)
  const plotH = Math.max(ctx.height - 2, 10)

  let cols = 1
  if (vertical === false) {
    const requested = Number.isInteger(raw.columns) === true && raw.columns > 0 ? raw.columns : null
    const fit = Math.max(Math.floor((plotW + GAP) / (MIN_TILE_W + GAP)), 1)
    cols = Math.min(metrics.length, requested !== null ? requested : fit)
  }
  const rows = Math.ceil(metrics.length / cols)
  const tileW = Math.max((plotW - GAP * (cols - 1)) / cols, 40)
  const tileH = Math.max((plotH - GAP * (rows - 1)) / rows, 40)
  const innerW = Math.max(tileW - PAD * 2, 10)

  for (let m = 0; m < metrics.length; m = m + 1) {
    const metric = metrics[m]
    const tileX = 1 + (m % cols) * (tileW + GAP)
    const tileY = 1 + Math.floor(m / cols) * (tileH + GAP)
    const label = metric.label !== undefined && metric.label !== null ? String(metric.label) : ""
    const value = readNumber(metric.value)
    const format = metric.format !== undefined ? metric.format : null
    const valueText = value !== null ? formatValue(value, format) : "—"
    const good = metric.good === "down" || metric.good === "neutral" ? metric.good : "up"

    /* Change indicator. */
    const delta = readNumber(metric.delta)
    let change = null
    if (delta !== null) {
      let direction = delta > 0 ? "up" : (delta < 0 ? "down" : "flat")
      if (metric.trend === "up" || metric.trend === "down" || metric.trend === "flat") {
        direction = metric.trend
      }
      const sign = delta > 0 ? "+" : (delta < 0 ? "−" : "±")
      change = {
        text: `${sign}${formatNumber(Math.abs(delta) * 100, { maximumFractionDigits: 1 })}%`,
        info: changeInfo(direction, good)
      }
    }

    /* Attainment of the target. */
    const target = readNumber(metric.target)
    let attainment = null
    if (value !== null && target !== null && target > 0 && value >= 0) {
      if (good === "down") {
        attainment = value > 0 ? Math.min(target / value, 1) : 1
      } else {
        attainment = Math.min(value / target, 1)
      }
    }

    /* Bands from the top: label, value, change; from the bottom: progress, spark. */
    const labelH = 16
    const changeH = compact === false && change !== null ? 16 : 0
    const progressH = compact === false && attainment !== null ? 14 : 0
    const sparkValues = Array.isArray(metric.sparkline) === true ? metric.sparkline : []
    const fixedH = PAD * 2 + labelH + changeH + progressH
    const valueFont = fitFontSize(valueText, innerW, Math.min(Math.max((tileH - fixedH) * 0.45, 14), 34), 11)
    const sparkRoom = tileH - fixedH - valueFont - 8
    const sparkH = compact === false && sparkValues.length >= 2 && sparkRoom >= 14 ? Math.min(sparkRoom, 34) : 0

    const ariaParts = [`${label}: ${value !== null ? valueText : "no data"}`]
    if (change !== null) {
      ariaParts.push(`${change.info.direction} ${change.text} (${change.info.verdict})`)
    }
    if (attainment !== null) {
      ariaParts.push(`${formatNumber(attainment * 100, { maximumFractionDigits: 0 })}% of target ` +
        formatValue(target, format))
    }
    const ariaLabel = ariaParts.join(", ")

    const tile = svgEl("g", {
      tabindex: "0", role: "img", "aria-label": ariaLabel, part: "tile"
    }, [svgEl("title", null, ariaLabel)])
    root.appendChild(tile)

    tile.appendChild(svgEl("rect", {
      x: tileX, y: tileY, width: tileW, height: tileH, rx: 6,
      fill: "var(--mj-surface-raised, #ffffff)", stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))

    const left = tileX + PAD
    let cursor = tileY + PAD
    tile.appendChild(svgEl("text", {
      x: left, y: cursor + 11, "font-size": 11, fill: "var(--mj-text-muted, #5f6673)",
      "aria-hidden": "true"
    }, _truncate(label, innerW, 11)))
    cursor = cursor + labelH

    tile.appendChild(svgEl("text", {
      x: left, y: (cursor + valueFont * 0.85).toFixed(2), "font-size": valueFont.toFixed(1),
      "font-weight": "700", "aria-hidden": "true",
      fill: value !== null ? "var(--mj-text, #14181f)" : "var(--mj-text-muted, #5f6673)"
    }, valueText))
    cursor = cursor + valueFont + 4

    if (changeH > 0) {
      tile.appendChild(trendArrow(change.info.direction, left + 4, cursor + 6, 8, change.info.color))
      tile.appendChild(svgEl("text", {
        x: left + 12, y: cursor + 10, "font-size": 11, "font-weight": "600",
        fill: change.info.color, "aria-hidden": "true"
      }, change.text))
      cursor = cursor + changeH
    }

    let bottom = tileY + tileH - PAD
    if (progressH > 0) {
      const barY = bottom - 6
      tile.appendChild(svgEl("rect", {
        x: left, y: barY, width: innerW, height: 6, rx: 3,
        fill: "var(--mj-bg-muted, #eef0f3)", "aria-hidden": "true"
      }, []))
      tile.appendChild(svgEl("rect", {
        x: left, y: barY, width: (innerW * attainment).toFixed(2), height: 6, rx: 3,
        fill: ctx.colorFor(0), "aria-hidden": "true", part: "progress"
      }, []))
      bottom = bottom - progressH
    }
    if (sparkH > 0) {
      const sparkEl = sparkline(sparkValues, left, bottom - sparkH, innerW, sparkH, ctx.colorFor(0))
      if (sparkEl !== null) {
        tile.appendChild(sparkEl)
      }
    }

    const capturedMetric = metric
    const index = m
    const handler = () => {
      ctx.emit("mj-chart-tile-click", { metric: capturedMetric, index: index })
    }
    tile.addEventListener("click", handler)
    tile.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        handler()
      }
    })
  }

  return root
}


registerRenderer("scorecard", render, { orientation: "horizontal", legend: "none" })
