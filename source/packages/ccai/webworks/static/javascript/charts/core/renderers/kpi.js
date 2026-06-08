/*
 * kpi.js
 *
 * KPI card renderer (big-number metric card / scorecard tile).
 *
 * JSON shape (ctx.raw):
 *   kpi.value          primary metric value (number)
 *   kpi.format         optional Intl.NumberFormat options string (not used for
 *                      complex options; renderer uses formatNumber)
 *   kpi.label          optional sub-label below the value
 *   kpi.comparison     optional { value, label } – prior-period baseline
 *   kpi.trend          "up" | "down" | "flat" – manual override; computed from
 *                      comparison when omitted
 *   kpi.spark          optional array of numbers – sparkline values
 *
 * Registers: "kpi"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, linePath, formatNumber, escapeHtml } from "../svgdraw.js";
import { linearScale } from "../scales.js";


function _trendArrow(trend, cx, cy, size, color) {
  /*
   * Build a trend-arrow <path> element.  The arrow never encodes trend by
   * color alone – an aria-label is added to the containing group.
   *
   * :returns: An SVGPathElement.
   */
  const half = size / 2
  let d = ""
  if (trend === "up") {
    d = `M${cx},${cy - half} L${cx + half},${cy + half} L${cx - half},${cy + half} Z`
  } else if (trend === "down") {
    d = `M${cx},${cy + half} L${cx + half},${cy - half} L${cx - half},${cy - half} Z`
  } else {
    /* flat – horizontal bar */
    d = `M${cx - half},${cy - 2} L${cx + half},${cy - 2} L${cx + half},${cy + 2} L${cx - half},${cy + 2} Z`
  }
  const arrow = svgEl("path", { d: d, fill: color }, [])
  return arrow
}


function _sparkline(values, x, y, width, height, color) {
  /*
   * Render a small sparkline <path> within the given bounding box.
   *
   * :returns: An SVGElement group.
   */
  if (values.length < 2) {
    return null
  }

  let minV = values[0]
  let maxV = values[0]
  for (let i = 1; i < values.length; i = i + 1) {
    const v = values[i]
    if (v < minV) { minV = v }
    if (v > maxV) { maxV = v }
  }
  if (minV === maxV) {
    maxV = minV + 1
  }

  const xScale = linearScale([0, values.length - 1], [x, x + width])
  const yScale = linearScale([minV, maxV], [y + height, y])

  const points = values.map((v, i) => {
    return { x: xScale(i), y: yScale(v) }
  })

  const d = linePath(points)
  const spark = svgEl("g", { part: "spark" }, [
    svgEl("path", {
      d: d,
      fill: "none",
      stroke: color,
      "stroke-width": 1.5,
      "stroke-linejoin": "round",
      "stroke-linecap": "round"
    }, [])
  ])
  return spark
}


export function render(ctx) {
  /*
   * Render a KPI card.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw
  const kpi = (raw !== null && raw !== undefined && raw.kpi !== null && raw.kpi !== undefined)
    ? raw.kpi
    : {}

  const value = typeof kpi.value === "number" ? kpi.value : 0
  const label = kpi.label || ""
  const comparison = kpi.comparison || null
  const spark = Array.isArray(kpi.spark) ? kpi.spark : []

  const root = svgEl("g", { part: "plot" }, [])

  const w = ctx.width
  const h = ctx.height
  const midX = w / 2

  /* Determine trend direction. */
  let trend = kpi.trend || null
  if (trend === null && comparison !== null && typeof comparison.value === "number") {
    if (value > comparison.value) {
      trend = "up"
    } else if (value < comparison.value) {
      trend = "down"
    } else {
      trend = "flat"
    }
  }

  /* Background card. */
  root.appendChild(svgEl("rect", {
    x: 0, y: 0, width: w, height: h,
    rx: 8,
    fill: "var(--mj-surface, #ffffff)",
    stroke: "var(--mj-border, #e0e3e9)",
    "stroke-width": 1
  }, []))

  /* Primary value text. */
  const valueText = formatNumber(value)
  const valueFontSize = Math.min(Math.floor(h * 0.28), 56)
  const valueY = h * 0.44

  root.appendChild(svgEl("text", {
    x: midX, y: valueY,
    "text-anchor": "middle",
    "font-size": valueFontSize,
    "font-weight": "700",
    fill: "var(--mj-text, #14181f)",
    part: "kpi-value"
  }, valueText))

  /* Sub-label. */
  if (label !== "") {
    root.appendChild(svgEl("text", {
      x: midX, y: valueY + Math.floor(valueFontSize * 0.55),
      "text-anchor": "middle",
      "font-size": 13,
      fill: "var(--mj-text-muted, #6b7280)",
      part: "kpi-label"
    }, escapeHtml(label)))
  }

  /* Delta / comparison badge. */
  if (comparison !== null && typeof comparison.value === "number") {
    const delta = value - comparison.value
    const deltaPct = comparison.value !== 0
      ? (delta / Math.abs(comparison.value)) * 100
      : 0

    let deltaColor = "var(--mj-color-neutral-500, #6b7280)"
    if (trend === "up") {
      deltaColor = "var(--mj-color-success, #15803d)"
    } else if (trend === "down") {
      deltaColor = "var(--mj-color-danger, #b91c1c)"
    }

    const trendLabel = trend === "up" ? "up" : trend === "down" ? "down" : "flat"
    const deltaStr = (delta >= 0 ? "+" : "") + formatNumber(deltaPct, { maximumFractionDigits: 1 }) + "%"
    const compLabel = comparison.label || "vs prior"
    const ariaLabel = `Trend: ${trendLabel}, ${deltaStr} ${compLabel}`

    const badgeY = valueY + Math.floor(valueFontSize * 0.55) + 20
    const badgeW = 80
    const badgeH = 22
    const badgeX = midX - badgeW / 2

    const badge = svgEl("g", {
      "aria-label": ariaLabel,
      part: "kpi-delta"
    }, [])

    badge.appendChild(svgEl("rect", {
      x: badgeX, y: badgeY,
      width: badgeW, height: badgeH,
      rx: 4,
      fill: deltaColor,
      opacity: 0.12
    }, []))

    const arrowSize = 8
    const arrowX = badgeX + 10
    const arrowCY = badgeY + badgeH / 2
    const arrow = _trendArrow(trendLabel, arrowX, arrowCY, arrowSize, deltaColor)
    badge.appendChild(arrow)

    badge.appendChild(svgEl("text", {
      x: arrowX + arrowSize, y: badgeY + badgeH / 2 + 4,
      "font-size": 11, "font-weight": "600",
      fill: deltaColor
    }, escapeHtml(deltaStr)))

    badge.appendChild(svgEl("text", {
      x: badgeX + badgeW + 4, y: badgeY + badgeH / 2 + 4,
      "font-size": 10,
      fill: "var(--mj-text-muted, #6b7280)"
    }, escapeHtml(compLabel)))

    badge.setAttribute("tabindex", "0")
    badge.setAttribute("role", "img")
    root.appendChild(badge)
  }

  /* Sparkline. */
  if (spark.length >= 2) {
    const sparkMargin = 12
    const sparkH = Math.min(40, h * 0.2)
    const sparkY = h - sparkMargin - sparkH
    const sparkColor = ctx.colorFor(0)
    const sparkEl = _sparkline(
      spark,
      sparkMargin, sparkY,
      w - sparkMargin * 2, sparkH,
      sparkColor
    )
    if (sparkEl !== null) {
      root.appendChild(sparkEl)
    }
  }

  /* Interactive wrapper for the whole card. */
  root.setAttribute("tabindex", "0")
  root.setAttribute("role", "img")
  root.setAttribute("aria-label",
    `KPI: ${valueText}${label !== "" ? " " + label : ""}`)
  root.appendChild(svgEl("title", null, `${valueText}${label !== "" ? " — " + label : ""}`))

  const handler = () => {
    ctx.emit("mj-chart-kpi-click", { value: value, label: label })
  }
  root.addEventListener("click", handler)
  root.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      handler()
    }
  })

  return root
}


registerRenderer("kpi", render)
