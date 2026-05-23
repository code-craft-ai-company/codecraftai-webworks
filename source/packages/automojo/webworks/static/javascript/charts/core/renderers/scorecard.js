/*
 * scorecard.js
 *
 * Scorecard renderer — a grid of KPI tiles each showing a headline value,
 * label, delta indicator, trend arrow, optional progress bar, and sparkline.
 *
 * Registered types:
 *   "scorecard"
 *
 * ctx.raw shape:
 *   raw.metrics  [{label, value, format?, target?, delta?, trend?, sparkline?}]
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber, linePath } from "../svgdraw.js";
import { linearScale } from "../scales.js";


/* ── arrow paths ─────────────────────────────────────────────────────── */

function _trendArrow(cx, cy, size, direction) {
  /*
   * Draw a trend-direction arrow glyph.
   *
   * :param direction: "up" | "down" | "flat"
   * :returns: SVGElement.
   */
  const h = size / 2
  let d = null
  if (direction === "up") {
    d = `M${cx},${cy - h} L${cx - h},${cy + h} L${cx + h},${cy + h} Z`
  } else if (direction === "down") {
    d = `M${cx},${cy + h} L${cx - h},${cy - h} L${cx + h},${cy - h} Z`
  } else {
    /* flat */
    d = `M${cx - h},${cy} L${cx + h},${cy}`
  }
  const color = direction === "up"
    ? "var(--mj-color-success, #15803d)"
    : direction === "down"
      ? "var(--mj-color-danger, #b91c1c)"
      : "var(--mj-text-muted, #6b7280)"
  const el = svgEl("path", {
    d: d,
    fill: direction === "flat" ? "none" : color,
    stroke: color,
    "stroke-width": direction === "flat" ? 2 : 0,
    "stroke-linecap": "round"
  }, [])
  return el
}


/* ── sparkline ────────────────────────────────────────────────────────── */

function _sparkline(values, x, y, w, h) {
  /*
   * Render a miniature line sparkline from a value array.
   *
   * :returns: SVGElement or null.
   */
  if (values === null || values === undefined || values.length < 2) {
    return null
  }
  let lo = Infinity
  let hi = -Infinity
  for (let i = 0; i < values.length; i = i + 1) {
    const v = values[i]
    if (typeof v !== "number") {
      continue
    }
    if (v < lo) {
      lo = v
    }
    if (v > hi) {
      hi = v
    }
  }
  if (lo === Infinity) {
    return null
  }
  if (lo === hi) {
    hi = lo + 1
  }

  const xScale = linearScale([0, values.length - 1], [x, x + w])
  const yScale = linearScale([lo, hi], [y + h, y])
  const points = []
  for (let i = 0; i < values.length; i = i + 1) {
    const v = values[i]
    if (typeof v !== "number") {
      points.push(null)
      continue
    }
    points.push({ x: xScale(i), y: yScale(v) })
  }

  const d = linePath(points)
  if (d === "") {
    return null
  }
  const el = svgEl("path", {
    d: d,
    fill: "none",
    stroke: "var(--mj-color-accent-500, #2563eb)",
    "stroke-width": 1.5,
    "stroke-linecap": "round",
    "stroke-linejoin": "round"
  }, [])
  el.setAttribute("aria-hidden", "true")
  return el
}


/* ── renderer ────────────────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Render a scorecard grid of KPI tiles.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw  = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])

  const metrics = (raw !== null && raw !== undefined && Array.isArray(raw.metrics))
    ? raw.metrics
    : []

  if (metrics.length === 0) {
    return root
  }

  const horizontal = ctx.orientation !== "vertical"
  const mode       = ctx.attrs("mode", "full")

  const margin = { top: 8, right: 8, bottom: 8, left: 8 }
  const plotW  = Math.max(ctx.width  - margin.left - margin.right,  10)
  const plotH  = Math.max(ctx.height - margin.top  - margin.bottom, 10)

  const tileCount = metrics.length
  let tileW = 0
  let tileH = 0

  if (horizontal === true) {
    tileW = Math.floor(plotW / tileCount)
    tileH = plotH
  } else {
    tileW = plotW
    tileH = Math.floor(plotH / tileCount)
  }

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  for (let m = 0; m < metrics.length; m = m + 1) {
    const metric = metrics[m]
    const tileX  = horizontal ? m * tileW : 0
    const tileY  = horizontal ? 0 : m * tileH
    const pad    = 12

    /* Tile background */
    const tileRect = svgEl("rect", {
      x: tileX + 1, y: tileY + 1,
      width: tileW - 2, height: tileH - 2,
      rx: 6,
      fill: "var(--mj-surface-raised, #f3f4f6)",
      stroke: "var(--mj-border, #e0e3e9)",
      "stroke-width": 1
    }, [])
    tileRect.setAttribute("part", "tile")
    tileRect.setAttribute("tabindex", "0")
    tileRect.setAttribute("role", "region")
    const valueLabel = typeof metric.value === "number"
      ? formatNumber(metric.value)
      : String(metric.value ?? "")
    tileRect.setAttribute("aria-label",
      `${metric.label || ""}: ${valueLabel}`)
    tileRect.appendChild(svgEl("title", null,
      `${metric.label || ""}: ${valueLabel}`))
    const capturedMetric = metric
    const handler = () => {
      ctx.emit("mj-chart-tile-click", { metric: capturedMetric })
    }
    tileRect.addEventListener("click", handler)
    tileRect.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        handler()
      }
    })
    plot.appendChild(tileRect)

    /* Label */
    plot.appendChild(svgEl("text", {
      x: tileX + pad, y: tileY + pad + 12,
      "font-size": 11,
      fill: "var(--mj-text-muted, #6b7280)"
    }, escapeHtml(metric.label || "")))

    /* Headline value */
    const valueFontSize = Math.min(Math.max(tileH * 0.28, 22), 40)
    plot.appendChild(svgEl("text", {
      x: tileX + pad, y: tileY + pad + 12 + valueFontSize,
      "font-size": valueFontSize,
      "font-weight": "700",
      fill: "var(--mj-text, #14181f)"
    }, valueLabel))

    if (mode === "compact") {
      continue
    }

    /* Delta + trend arrow */
    if (typeof metric.delta === "number") {
      const deltaY    = tileY + pad + 12 + valueFontSize + 18
      const deltaText = (metric.delta >= 0 ? "+" : "") +
        formatNumber(metric.delta * 100, { maximumFractionDigits: 1 }) + "%"
      const deltaColor = metric.delta >= 0
        ? "var(--mj-color-success, #15803d)"
        : "var(--mj-color-danger, #b91c1c)"

      const direction = metric.trend === "up" ? "up"
        : metric.trend === "down" ? "down"
          : metric.delta > 0 ? "up"
            : metric.delta < 0 ? "down"
              : "flat"

      const arrow = _trendArrow(tileX + pad + 6, deltaY - 4, 8, direction)
      arrow.setAttribute("aria-hidden", "true")
      plot.appendChild(arrow)

      plot.appendChild(svgEl("text", {
        x: tileX + pad + 16, y: deltaY,
        "font-size": 11,
        fill: deltaColor
      }, deltaText))
    }

    /* Progress bar toward target */
    if (typeof metric.target === "number" && typeof metric.value === "number") {
      const barY  = tileY + tileH - pad - 8
      const barW  = tileW - pad * 2
      const scale = linearScale([0, metric.target], [0, barW])
      const fillW = Math.max(0, Math.min(barW, scale(metric.value)))

      plot.appendChild(svgEl("rect", {
        x: tileX + pad, y: barY,
        width: barW, height: 6,
        rx: 3,
        fill: "var(--mj-surface, #ffffff)",
        stroke: "var(--mj-border, #e0e3e9)",
        "stroke-width": 1,
        "aria-hidden": "true"
      }, []))
      plot.appendChild(svgEl("rect", {
        x: tileX + pad, y: barY,
        width: fillW, height: 6,
        rx: 3,
        fill: "var(--mj-color-accent-500, #2563eb)",
        "aria-hidden": "true"
      }, []))
    }

    /* Sparkline */
    if (Array.isArray(metric.sparkline) === true && metric.sparkline.length >= 2) {
      const sparkH = Math.min(tileH * 0.25, 30)
      const sparkY = tileY + tileH - pad - sparkH -
        (typeof metric.target === "number" ? 16 : 0)
      const sparkW = tileW - pad * 2
      const sparkEl = _sparkline(
        metric.sparkline,
        tileX + pad, sparkY, sparkW, sparkH
      )
      if (sparkEl !== null) {
        plot.appendChild(sparkEl)
      }
    }
  }

  return root
}


registerRenderer("scorecard", render)
