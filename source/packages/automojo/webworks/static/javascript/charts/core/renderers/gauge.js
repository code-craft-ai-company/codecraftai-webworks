/*
 * gauge.js
 *
 * Arc gauge renderer (dial chart / speedometer).
 *
 * JSON shape (ctx.raw):
 *   gauge.value          numeric reading
 *   gauge.min            scale minimum  (default 0)
 *   gauge.max            scale maximum  (default 100)
 *   gauge.unit           optional unit string
 *   gauge.thresholds[]   { value, label, color }  threshold band edges
 *   gauge.needle         boolean – draw a needle (default true)
 *   gauge.start_angle    degrees from 12-o'clock, clockwise (default -135)
 *   gauge.sweep_angle    total arc sweep in degrees (default 270)
 *
 * Registers: "gauge"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, arcPath, formatNumber, escapeHtml } from "../svgdraw.js";
import { linearScale } from "../scales.js";


const DEG = Math.PI / 180


function _toRad(degrees) {
  /*
   * Convert degrees (0 = up, clockwise) to radians for arcPath.
   */
  const radians = degrees * DEG
  return radians
}


export function render(ctx) {
  /*
   * Render a gauge (arc dial) chart.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw
  const gauge = (raw !== null && raw !== undefined && raw.gauge !== null && raw.gauge !== undefined)
    ? raw.gauge
    : {}

  const value = typeof gauge.value === "number" ? gauge.value : 0
  const minVal = typeof gauge.min === "number" ? gauge.min : 0
  const maxVal = typeof gauge.max === "number" ? gauge.max : 100
  const unit = gauge.unit || ""
  const thresholds = Array.isArray(gauge.thresholds) ? gauge.thresholds : []
  const showNeedle = gauge.needle !== false
  const startDeg = typeof gauge.start_angle === "number" ? gauge.start_angle : -135
  const sweepDeg = typeof gauge.sweep_angle === "number" ? gauge.sweep_angle : 270

  const root = svgEl("g", { part: "plot" }, [])

  const cx = ctx.width / 2
  const cy = ctx.height * 0.58
  const outerR = Math.min(cx, cy) * 0.82
  const innerR = outerR * 0.62
  const trackWidth = outerR - innerR

  /* Angle scale: maps [minVal, maxVal] -> [startAngle, startAngle+sweepAngle]. */
  const startRad = _toRad(startDeg)
  const endRad = _toRad(startDeg + sweepDeg)
  const angleScale = linearScale([minVal, maxVal], [startRad, endRad])

  /* Build threshold color bands. */
  const bandColors = [
    "var(--mj-color-success, #15803d)",
    "var(--mj-color-warning, #b45309)",
    "var(--mj-color-danger, #b91c1c)"
  ]

  /* Sort thresholds by value, then build arc segments from min upward. */
  const sortedThresholds = thresholds.slice().sort((a, b) => a.value - b.value)

  const bandEdges = [minVal]
  for (let t = 0; t < sortedThresholds.length; t = t + 1) {
    bandEdges.push(sortedThresholds[t].value)
  }
  bandEdges.push(maxVal)

  for (let b = 0; b < bandEdges.length - 1; b = b + 1) {
    const segStart = angleScale(bandEdges[b])
    const segEnd = angleScale(bandEdges[b + 1])
    const segColor = thresholds.length > 0
      ? bandColors[b % bandColors.length]
      : "var(--mj-color-accent-500, #2563eb)"

    const d = arcPath(cx, cy, innerR, outerR, segStart, segEnd)
    const arc = svgEl("path", {
      d: d,
      fill: segColor,
      opacity: 0.25
    }, [])
    root.appendChild(arc)
  }

  /* Filled value arc from start to current value. */
  const valueClamped = Math.max(minVal, Math.min(maxVal, value))
  const valueRad = angleScale(valueClamped)

  /* Determine color based on which band the value falls in. */
  let fillColor = "var(--mj-color-accent-500, #2563eb)"
  if (thresholds.length > 0) {
    for (let t = sortedThresholds.length - 1; t >= 0; t = t - 1) {
      if (valueClamped >= sortedThresholds[t].value) {
        const colorToken = sortedThresholds[t].color || ""
        const cssVar = colorToken.startsWith("--") ? `var(${colorToken})` : colorToken
        if (cssVar !== "") {
          fillColor = cssVar
        } else {
          fillColor = bandColors[t % bandColors.length]
        }
        break
      }
    }
  }

  if (valueRad > startRad) {
    const valueArc = arcPath(cx, cy, innerR, outerR, startRad, valueRad)
    const filledArc = svgEl("path", {
      d: valueArc,
      fill: fillColor,
      part: "gauge-fill"
    }, [])
    filledArc.setAttribute("role", "meter")
    filledArc.setAttribute("aria-valuenow", String(value))
    filledArc.setAttribute("aria-valuemin", String(minVal))
    filledArc.setAttribute("aria-valuemax", String(maxVal))
    filledArc.setAttribute("aria-label", `${value}${unit} (range ${minVal}–${maxVal})`)
    filledArc.appendChild(svgEl("title", null,
      `${value}${unit} of ${maxVal}${unit}`))
    const handler = () => {
      ctx.emit("mj-chart-gauge-click", { value: value, min: minVal, max: maxVal })
    }
    filledArc.setAttribute("tabindex", "0")
    filledArc.addEventListener("click", handler)
    filledArc.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        handler()
      }
    })
    root.appendChild(filledArc)
  }

  /* Track outline (unfilled arc). */
  const trackArc = arcPath(cx, cy, innerR, outerR, startRad, endRad)
  root.appendChild(svgEl("path", {
    d: trackArc,
    fill: "none",
    stroke: "var(--mj-border, #e0e3e9)",
    "stroke-width": 1
  }, []))

  /* Needle. */
  if (showNeedle === true) {
    const needleAngle = valueRad
    const pivotR = trackWidth * 0.25
    const needleLen = outerR + 4
    const sinA = Math.sin(needleAngle)
    const cosA = Math.cos(needleAngle)
    const tipX = cx + needleLen * sinA
    const tipY = cy - needleLen * cosA
    const leftX = cx + pivotR * Math.sin(needleAngle - Math.PI / 2) * 0.4
    const leftY = cy - pivotR * Math.cos(needleAngle - Math.PI / 2) * 0.4
    const rightX = cx + pivotR * Math.sin(needleAngle + Math.PI / 2) * 0.4
    const rightY = cy - pivotR * Math.cos(needleAngle + Math.PI / 2) * 0.4

    const needlePath = `M${leftX.toFixed(2)},${leftY.toFixed(2)} ` +
      `L${tipX.toFixed(2)},${tipY.toFixed(2)} ` +
      `L${rightX.toFixed(2)},${rightY.toFixed(2)} Z`

    root.appendChild(svgEl("path", {
      d: needlePath,
      fill: "var(--mj-text, #14181f)",
      part: "gauge-needle"
    }, []))

    root.appendChild(svgEl("circle", {
      cx: cx, cy: cy, r: pivotR,
      fill: "var(--mj-text, #14181f)",
      part: "gauge-pivot"
    }, []))
  }

  /* Min / max tick labels. */
  const minPt = {
    x: cx + (outerR + 10) * Math.sin(startRad),
    y: cy - (outerR + 10) * Math.cos(startRad)
  }
  const maxPt = {
    x: cx + (outerR + 10) * Math.sin(endRad),
    y: cy - (outerR + 10) * Math.cos(endRad)
  }
  root.appendChild(svgEl("text", {
    x: minPt.x.toFixed(2), y: minPt.y.toFixed(2),
    "text-anchor": "middle", "font-size": 11,
    fill: "var(--mj-text-muted, #6b7280)"
  }, formatNumber(minVal)))
  root.appendChild(svgEl("text", {
    x: maxPt.x.toFixed(2), y: maxPt.y.toFixed(2),
    "text-anchor": "middle", "font-size": 11,
    fill: "var(--mj-text-muted, #6b7280)"
  }, formatNumber(maxVal)))

  /* Centre value label. */
  const labelY = cy + trackWidth * 0.3
  root.appendChild(svgEl("text", {
    x: cx, y: labelY,
    "text-anchor": "middle", "font-size": 28,
    "font-weight": "600",
    fill: "var(--mj-text, #14181f)",
    part: "gauge-value"
  }, formatNumber(value) + escapeHtml(unit)))

  /* Threshold labels. */
  for (let t = 0; t < sortedThresholds.length; t = t + 1) {
    const tRad = angleScale(sortedThresholds[t].value)
    const labelR = outerR + 16
    const tx = cx + labelR * Math.sin(tRad)
    const ty = cy - labelR * Math.cos(tRad)
    root.appendChild(svgEl("text", {
      x: tx.toFixed(2), y: ty.toFixed(2),
      "text-anchor": "middle", "font-size": 9,
      fill: "var(--mj-text-muted, #6b7280)"
    }, escapeHtml(sortedThresholds[t].label || formatNumber(sortedThresholds[t].value))))
  }

  return root
}


registerRenderer("gauge", render)
