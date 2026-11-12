/*
 * gauge.js
 *
 * Arc gauge renderer (dial chart / speedometer / progress ring).
 *
 * JSON shape (ctx.raw):
 *   gauge.value          numeric reading (a numeric string is accepted; a
 *                        missing / non-numeric value shows a "no data" dial)
 *   gauge.min            scale minimum  (default 0)
 *   gauge.max            scale maximum  (default 100); min >= max shows a
 *                        message instead of a dial
 *   gauge.unit           optional unit string
 *   gauge.thresholds[]   { value, label, color }  each threshold STARTS a
 *                        band that runs to the next threshold (or max) and
 *                        is coloured with its own `color` (a CSS colour or
 *                        a custom-property name such as "--mj-color-success";
 *                        without one, a palette step), drawn as a ring
 *                        outside the track. The range below the first
 *                        threshold is neutral. Thresholds are clamped into
 *                        [min, max].
 *   gauge.needle         boolean – draw a needle (default true)
 *   gauge.start_angle    degrees from 12-o'clock, clockwise (default -135)
 *   gauge.sweep_angle    total arc sweep in degrees (default 270; 360 draws
 *                        a full progress ring; a negative sweep runs
 *                        counter-clockwise)
 *
 * The value arc takes the colour of the band the value falls in. The value
 * label sits below the needle pivot and scales with the dial; a value
 * outside [min, max] pins the needle to the end and says "above range" /
 * "below range".
 *
 * Interaction: the dial is one focusable mark; click / Enter emits
 * `mj-chart-gauge-click` { value, min, max }.
 *
 * Registers: "gauge"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, arcPath, formatNumber } from "../svgdraw.js";
import { seriesColor } from "../scales.js";
import { textWidth } from "./bar.js";


const DEG = Math.PI / 180
const NEUTRAL = "var(--mj-bg-muted, #eef0f3)"
const LABEL_GAP = 18
const END_LABEL_SIZE = 11
/* Space kept between an end label and the edge of the drawing (px). */
const EDGE_PAD = 4


function _number(value) {
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


function _colorOf(token, fallback) {
  /*
   * A CSS colour from a threshold colour: "--name" becomes var(--name).
   */
  if (typeof token !== "string" || token.trim().length === 0) {
    return fallback
  }
  const text = token.trim()
  const color = text.startsWith("--") === true ? `var(${text})` : text
  return color
}


function _arc(cx, cy, innerR, outerR, a0, a1) {
  /*
   * An arc band between two angles in either order.
   */
  const d = arcPath(cx, cy, innerR, outerR, Math.min(a0, a1), Math.max(a0, a1))
  return d
}


function _dialExtent(startRad, sweepRad) {
  /*
   * Bounding box of a unit dial (radius 1, centre 0,0, y down) including
   * its centre: { left, right, top, bottom }.
   */
  let left = 0
  let right = 0
  let top = 0
  let bottom = 0
  const steps = 72
  for (let index = 0; index <= steps; index = index + 1) {
    const angle = startRad + sweepRad * index / steps
    const x = Math.sin(angle)
    const y = -Math.cos(angle)
    left = Math.min(left, x)
    right = Math.max(right, x)
    top = Math.min(top, y)
    bottom = Math.max(bottom, y)
  }
  return { left: left, right: right, top: top, bottom: bottom }
}


function _ringOuter(outerR) {
  /*
   * The outer radius of the threshold ring drawn just outside the track.
   */
  const trackWidth = outerR * 0.32
  const radius = outerR + 2 + Math.max(trackWidth * 0.16, 4)
  return radius
}


function _labelAnchor(angle) {
  /*
   * The text-anchor of a label placed outside the dial at `angle`: centred
   * above / below the dial, else leaning away from it.
   */
  const sin = Math.sin(angle)
  const anchor = Math.abs(sin) < 0.3 ? "middle" : (sin > 0 ? "start" : "end")
  return anchor
}


function _horizontalReach(cx, outerR, extent, endLabels) {
  /*
   * The horizontal span (px) the dial and its end labels cover.
   *
   * :param cx: The dial centre x.
   * :param outerR: The dial's outer radius.
   * :param extent: The unit dial's box (_dialExtent).
   * :param endLabels: [{ angle, text }] the min / max labels.
   * :returns: { left, right }.
   */
  const ringOuter = _ringOuter(outerR)
  let left = cx + extent.left * ringOuter
  let right = cx + extent.right * ringOuter
  for (let index = 0; index < endLabels.length; index = index + 1) {
    const label = endLabels[index]
    const x = cx + (ringOuter + LABEL_GAP * 0.55) * Math.sin(label.angle)
    const width = textWidth(label.text, END_LABEL_SIZE)
    const anchor = _labelAnchor(label.angle)
    if (anchor === "start") {
      right = Math.max(right, x + width)
      left = Math.min(left, x)
    } else if (anchor === "end") {
      left = Math.min(left, x - width)
      right = Math.max(right, x)
    } else {
      left = Math.min(left, x - width / 2)
      right = Math.max(right, x + width / 2)
    }
  }
  return { left: left, right: right }
}


export function render(ctx) {
  /*
   * Render a gauge (arc dial) chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const gauge = raw.gauge !== null && typeof raw.gauge === "object" ? raw.gauge : {}

  const value = _number(gauge.value)
  const minVal = _number(gauge.min) !== null ? _number(gauge.min) : 0
  const maxVal = _number(gauge.max) !== null ? _number(gauge.max) : 100
  const unit = gauge.unit !== undefined && gauge.unit !== null ? String(gauge.unit) : ""
  const showNeedle = gauge.needle !== false
  const startDeg = _number(gauge.start_angle) !== null ? _number(gauge.start_angle) : -135
  let sweepDeg = _number(gauge.sweep_angle) !== null ? _number(gauge.sweep_angle) : 270
  sweepDeg = Math.max(-360, Math.min(360, sweepDeg))
  if (sweepDeg === 0) {
    sweepDeg = 270
  }
  const fullRing = Math.abs(sweepDeg) >= 359.9

  const root = svgEl("g", { part: "plot" }, [])
  const valueText = value !== null ? `${formatNumber(value)}${unit}` : "—"

  /* Thresholds: finite, clamped into the range, sorted. */
  const thresholds = (Array.isArray(gauge.thresholds) === true ? gauge.thresholds : [])
    .filter((item) => item !== null && typeof item === "object" && _number(item.value) !== null)
    .map((item, index) => ({
      value: Math.max(Math.min(minVal, maxVal), Math.min(Math.max(minVal, maxVal), _number(item.value))),
      label: item.label !== undefined && item.label !== null ? String(item.label) : null,
      color: _colorOf(item.color, seriesColor(index)),
      source: item
    }))
    .sort((a, b) => a.value - b.value)

  const tableRows = [["Value", value], ["Minimum", minVal], ["Maximum", maxVal]]
  thresholds.forEach((item) => {
    tableRows.push([item.label !== null ? `${item.label} (from)` : "Threshold", item.value])
  })
  ctx.setTable({ columns: ["Measure", "Value"], rows: tableRows, caption: ctx.label })

  if (minVal >= maxVal) {
    root.appendChild(svgEl("text", {
      x: ctx.width / 2, y: ctx.height / 2, "text-anchor": "middle", "font-size": 13,
      fill: "var(--mj-text-muted, #5f6673)", part: "message"
    }, "Invalid gauge range (min ≥ max)"))
    return root
  }

  /* Geometry: fit the dial (and the label under the pivot) into the box. */
  const startRad = startDeg * DEG
  const sweepRad = sweepDeg * DEG
  const endRad = startRad + sweepRad
  const extent = _dialExtent(startRad, sweepRad)
  const centredLabel = fullRing === true || showNeedle === false
  const labelBand = centredLabel === true ? 0 : Math.max(Math.min(ctx.height * 0.2, 52), 26)
  const availableW = Math.max(ctx.width - LABEL_GAP * 4, 20)
  const availableH = Math.max(ctx.height - LABEL_GAP * 2, 20)
  /*
   * Height used: R * -top above the centre and max(R * bottom, labelBand)
   * below it; both terms must fit.
   */
  const above = Math.max(-extent.top, 0.05)
  let outerR = Math.min(
    availableW / Math.max(extent.right - extent.left, 0.05),
    availableH / Math.max(extent.bottom - extent.top, 0.05),
    Math.max(availableH - labelBand, 10) / above
  )
  outerR = Math.max(outerR, 12)

  /*
   * The min / max labels sit outside the ends of the arc; on a dial whose
   * ends point sideways (a 180 degree dial) they reach past the dial's own
   * box. Shrink the dial (and centre dial plus labels) until they fit.
   */
  const endLabels = [{ angle: startRad, text: formatNumber(minVal) }]
  if (fullRing === false) {
    endLabels.push({ angle: endRad, text: formatNumber(maxVal) })
  }
  let cx = ctx.width / 2 - (extent.left + extent.right) / 2 * outerR
  for (let attempt = 0; attempt < 6; attempt = attempt + 1) {
    cx = ctx.width / 2 - (extent.left + extent.right) / 2 * outerR
    const reach = _horizontalReach(cx, outerR, extent, endLabels)
    const available = ctx.width - EDGE_PAD * 2
    const span = reach.right - reach.left
    if (span <= available || outerR <= 12) {
      /* Fits: centre the dial and its labels together. */
      cx = cx + (EDGE_PAD + (available - span) / 2) - reach.left
      break
    }
    outerR = Math.max(outerR - (span - available), 12)
  }
  const innerR = outerR * 0.68
  const trackWidth = outerR - innerR
  const usedH = outerR * -extent.top + Math.max(extent.bottom * outerR, labelBand)
  const cy = (ctx.height - usedH) / 2 + outerR * -extent.top

  const fraction = (input) => (input - minVal) / (maxVal - minVal)
  const angleOf = (input) => startRad + sweepRad * Math.max(0, Math.min(1, fraction(input)))

  /*
   * Track (neutral) and the threshold bands as a thin ring just outside
   * it, so the zones stay visible under the value arc.
   */
  const decor = svgEl("g", { "aria-hidden": "true" }, [])
  root.appendChild(decor)
  decor.appendChild(svgEl("path", {
    d: _arc(cx, cy, innerR, outerR, startRad, endRad), fill: NEUTRAL, part: "gauge-track"
  }, []))
  const ringInner = outerR + 2
  const ringOuter = _ringOuter(outerR)
  for (let b = 0; b < thresholds.length; b = b + 1) {
    const from = thresholds[b].value
    const to = b + 1 < thresholds.length ? thresholds[b + 1].value : maxVal
    if (to <= from) {
      continue
    }
    decor.appendChild(svgEl("path", {
      d: _arc(cx, cy, ringInner, ringOuter, angleOf(from), angleOf(to)),
      fill: thresholds[b].color,
      part: "gauge-band"
    }, []))
  }

  /* The value arc, coloured by the band the value falls in. */
  let fillColor = thresholds.length > 0 ? NEUTRAL : seriesColor(0)
  let bandLabel = null
  if (value !== null) {
    for (let t = thresholds.length - 1; t >= 0; t = t - 1) {
      if (value >= thresholds[t].value) {
        fillColor = thresholds[t].color
        bandLabel = thresholds[t].label
        break
      }
    }
    if (fillColor === NEUTRAL) {
      fillColor = "var(--mj-text-muted, #5f6673)"
    }
  }

  const status = value === null
    ? "no data"
    : (value > maxVal ? "above range" : (value < minVal ? "below range" : null))
  const ariaLabel = `${valueText} (range ${formatNumber(minVal)}–${formatNumber(maxVal)}${unit})` +
    (bandLabel !== null ? `, ${bandLabel}` : "") + (status !== null ? `, ${status}` : "")

  const dial = svgEl("g", {
    tabindex: "0", role: "img", "aria-label": ariaLabel, part: "gauge-dial"
  }, [])
  root.appendChild(dial)
  dial.appendChild(svgEl("title", null, ariaLabel))

  if (value !== null && fraction(value) > 0) {
    dial.appendChild(svgEl("path", {
      d: _arc(cx, cy, innerR, outerR, startRad, angleOf(value)),
      fill: fillColor,
      part: "gauge-fill"
    }, []))
  }

  /* Track outline. */
  dial.appendChild(svgEl("path", {
    d: _arc(cx, cy, innerR, outerR, startRad, endRad),
    fill: "none", stroke: "var(--mj-border-strong, #878e9c)", "stroke-width": 1,
    "aria-hidden": "true"
  }, []))

  /* Needle and pivot. */
  const pivotR = Math.max(trackWidth * 0.22, 3)
  if (showNeedle === true && value !== null && fullRing === false) {
    const angle = angleOf(value)
    const needleLen = outerR + 4
    const base = pivotR * 0.45
    const tipX = cx + needleLen * Math.sin(angle)
    const tipY = cy - needleLen * Math.cos(angle)
    const leftX = cx + base * Math.sin(angle - Math.PI / 2)
    const leftY = cy - base * Math.cos(angle - Math.PI / 2)
    const rightX = cx + base * Math.sin(angle + Math.PI / 2)
    const rightY = cy - base * Math.cos(angle + Math.PI / 2)
    dial.appendChild(svgEl("path", {
      d: `M${leftX.toFixed(2)},${leftY.toFixed(2)} L${tipX.toFixed(2)},${tipY.toFixed(2)} ` +
        `L${rightX.toFixed(2)},${rightY.toFixed(2)} Z`,
      fill: "var(--mj-text, #14181f)", part: "gauge-needle", "aria-hidden": "true"
    }, []))
    dial.appendChild(svgEl("circle", {
      cx: cx.toFixed(2), cy: cy.toFixed(2), r: pivotR.toFixed(2),
      fill: "var(--mj-text, #14181f)", stroke: "var(--mj-surface, #ffffff)", "stroke-width": 1.5,
      part: "gauge-pivot", "aria-hidden": "true"
    }, []))
  }

  /* Value label: below the pivot on a dial, centred in a ring. */
  const fontSize = Math.max(Math.min(outerR * 0.3, 36), 12)
  const valueY = centredLabel === true
    ? cy + fontSize * 0.35
    : cy + pivotR + fontSize * 1.1 + 2
  dial.appendChild(svgEl("text", {
    x: cx.toFixed(2), y: valueY.toFixed(2),
    "text-anchor": "middle", "font-size": fontSize.toFixed(1), "font-weight": "600",
    fill: value !== null ? "var(--mj-text, #14181f)" : "var(--mj-text-muted, #5f6673)",
    part: "gauge-value", "aria-hidden": "true"
  }, valueText))
  if (status !== null && value !== null) {
    dial.appendChild(svgEl("text", {
      x: cx.toFixed(2), y: (valueY + 13).toFixed(2), "text-anchor": "middle", "font-size": 10,
      fill: "var(--mj-text-muted, #5f6673)", "aria-hidden": "true"
    }, status))
  }

  /* Min / max labels just outside the ends (one label on a full ring). */
  const labelAt = (angle, text, size) => {
    const radius = ringOuter + LABEL_GAP * 0.55
    const x = cx + radius * Math.sin(angle)
    const y = cy - radius * Math.cos(angle) + size * 0.35
    decor.appendChild(svgEl("text", {
      x: x.toFixed(2), y: y.toFixed(2), "text-anchor": _labelAnchor(angle), "font-size": size,
      fill: "var(--mj-text-muted, #5f6673)"
    }, text))
    return
  }
  for (let e = 0; e < endLabels.length; e = e + 1) {
    labelAt(endLabels[e].angle, endLabels[e].text, END_LABEL_SIZE)
  }
  for (let t = 0; t < thresholds.length; t = t + 1) {
    const item = thresholds[t]
    if (item.value <= minVal || item.value >= maxVal) {
      continue
    }
    labelAt(angleOf(item.value), item.label !== null ? item.label : formatNumber(item.value), 9)
  }

  const handler = () => {
    ctx.emit("mj-chart-gauge-click", { value: value, min: minVal, max: maxVal })
  }
  dial.addEventListener("click", handler)
  dial.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      handler()
    }
  })

  return root
}


registerRenderer("gauge", render, { legend: "none" })
