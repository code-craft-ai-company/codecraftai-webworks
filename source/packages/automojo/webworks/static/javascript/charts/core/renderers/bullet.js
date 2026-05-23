/*
 * bullet.js
 *
 * Bullet chart renderer -- a compact, information-dense KPI chart that
 * compares a primary performance measure against qualitative ranges
 * (Poor / Satisfactory / Good) and a target marker. Multiple bullets
 * stack as independent rows (horizontal) or columns (vertical).
 *
 * A renderer is `render(ctx) -> SVGElement`:
 *   ctx.model       normalized model { meta, categories, series, raw }
 *   ctx.raw         the raw data object
 *   ctx.width       drawing surface width (px)
 *   ctx.height      drawing surface height (px)
 *   ctx.orientation "horizontal" (canonical) | "vertical"
 *   ctx.attrs       (name, fallback) -> controller attribute value
 *   ctx.colorFor    (seriesIndex | seriesName) -> CSS color
 *   ctx.emit        (eventName, detail) -> dispatch an interaction event
 * It returns a <g> SVGElement drawn within [0..width] x [0..height].
 *
 * JSON shape per bullet series entry:
 *   { "name": "Revenue", "value": 275, "target": 300,
 *     "ranges": [200, 250, 350], "rangeLabels": ["Poor","Satisfactory","Good"] }
 *
 * Registered type keys: "bullet"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber } from "../svgdraw.js";
import { linearScale, niceTicks } from "../scales.js";


/* Qualitative range fill tokens, from darkest (worst) to lightest (best). */
const RANGE_FILLS = [
  "var(--mj-chart-range-1, #d1d5db)",
  "var(--mj-chart-range-2, #e5e7eb)",
  "var(--mj-chart-range-3, #f3f4f6)"
]


function _drawBullet(plot, bullet, scaleVal, horizontal, trackStart,
    trackCenter, trackLength, bandThickness, index, ctx) {
  /*
   * Draw a single bullet (range bands, performance bar, target tick).
   *
   * :param plot: The parent <g> element to append into.
   * :param bullet: The series entry describing this bullet.
   * :param scaleVal: The shared linear scale (value -> pixels along track).
   * :param horizontal: True for horizontal layout.
   * :param trackStart: Pixel start position perpendicular to the track axis.
   * :param trackCenter: Pixel centre perpendicular to the track axis.
   * :param trackLength: Pixel length along the track axis.
   * :param bandThickness: Pixel thickness of the full band.
   * :param index: Series index (for event detail).
   * :param ctx: The renderer context.
   */
  const ranges = Array.isArray(bullet.ranges) ? bullet.ranges : []
  const rangeLabels = Array.isArray(bullet.rangeLabels) ? bullet.rangeLabels : []
  const value = typeof bullet.value === "number" ? bullet.value : 0
  const target = typeof bullet.target === "number" ? bullet.target : null
  const barThickness = bandThickness * 0.4
  const barOffset = (bandThickness - barThickness) / 2

  /* Range bands -- drawn from largest to smallest so smaller overdraws. */
  for (let r = ranges.length - 1; r >= 0; r = r - 1) {
    const bandMax = ranges[r]
    const bandMin = r > 0 ? ranges[r - 1] : 0
    const fillIndex = r < RANGE_FILLS.length ? r : RANGE_FILLS.length - 1
    const fill = RANGE_FILLS[fillIndex]

    const pStart = scaleVal(bandMin)
    const pEnd = scaleVal(bandMax)

    let rx, ry, rw, rh
    if (horizontal === true) {
      rx = Math.min(pStart, pEnd)
      ry = trackStart
      rw = Math.abs(pEnd - pStart)
      rh = bandThickness
    } else {
      rx = trackStart
      ry = Math.min(pStart, pEnd)
      rw = bandThickness
      rh = Math.abs(pEnd - pStart)
    }

    const rangeLabel = rangeLabels[r] || ""
    plot.appendChild(svgEl("rect", {
      x: rx, y: ry, width: rw, height: rh,
      fill: fill
    }, rangeLabel ? [svgEl("title", null, rangeLabel)] : []))
  }

  /* Performance bar -- narrower and centered in the band. */
  const zero = scaleVal(0)
  const valuePos = scaleVal(value)

  let bx, by, bw, bh
  if (horizontal === true) {
    bx = Math.min(zero, valuePos)
    by = trackStart + barOffset
    bw = Math.abs(valuePos - zero)
    bh = barThickness
  } else {
    bx = trackStart + barOffset
    by = Math.min(zero, valuePos)
    bw = barThickness
    bh = Math.abs(valuePos - zero)
  }

  const barColor = ctx.colorFor(bullet.name || index)
  const bar = svgEl("rect", {
    x: bx, y: by, width: bw, height: bh,
    fill: barColor,
    part: "bullet-bar",
    tabindex: "0",
    role: "img",
    "aria-label": `${escapeHtml(bullet.name || "")}: ${formatNumber(value)}`
  }, [])

  bar.appendChild(svgEl("title", null,
    `${bullet.name || ""}: ${formatNumber(value)}`))

  const handler = () => {
    ctx.emit("mj-chart-bullet-click", {
      name: bullet.name, value: value, target: target
    })
  }
  bar.addEventListener("click", handler)
  bar.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      handler()
    }
  })
  plot.appendChild(bar)

  /* Target tick -- short perpendicular line. */
  if (target !== null) {
    const targetPos = scaleVal(target)
    const tickHalf = bandThickness * 0.35
    let tx1, ty1, tx2, ty2

    if (horizontal === true) {
      tx1 = targetPos
      ty1 = trackCenter - tickHalf
      tx2 = targetPos
      ty2 = trackCenter + tickHalf
    } else {
      tx1 = trackCenter - tickHalf
      ty1 = targetPos
      tx2 = trackCenter + tickHalf
      ty2 = targetPos
    }

    plot.appendChild(svgEl("line", {
      x1: tx1, y1: ty1, x2: tx2, y2: ty2,
      stroke: "var(--mj-text, #14181f)",
      "stroke-width": 3,
      "stroke-linecap": "square"
    }, []))
  }

  return
}


export function render(ctx) {
  /*
   * Render a bullet chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const horizontal = ctx.orientation !== "vertical"

  const root = svgEl("g", { part: "plot" }, [])

  const series = model.series
  if (series.length === 0) {
    return root
  }

  /* Build a shared value domain: span of all ranges, values, and targets. */
  let domainMin = 0
  let domainMax = 1
  for (let s = 0; s < series.length; s = s + 1) {
    const bullet = series[s]
    if (typeof bullet.value === "number") {
      if (bullet.value > domainMax) {
        domainMax = bullet.value
      }
      if (bullet.value < domainMin) {
        domainMin = bullet.value
      }
    }
    if (typeof bullet.target === "number") {
      if (bullet.target > domainMax) {
        domainMax = bullet.target
      }
      if (bullet.target < domainMin) {
        domainMin = bullet.target
      }
    }
    const ranges = Array.isArray(bullet.ranges) ? bullet.ranges : []
    for (let r = 0; r < ranges.length; r = r + 1) {
      if (typeof ranges[r] === "number") {
        if (ranges[r] > domainMax) {
          domainMax = ranges[r]
        }
        if (ranges[r] < domainMin) {
          domainMin = ranges[r]
        }
      }
    }
  }
  if (domainMax === domainMin) {
    domainMax = domainMin + 1
  }

  const bulletCount = series.length
  const margin = { top: 16, right: 16, bottom: 40, left: 72 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  /* Divide the plot area equally among bullets, adding a small gap. */
  const bulletSlot = horizontal
    ? plotH / bulletCount
    : plotW / bulletCount
  const bulletGap = 8
  const bandThickness = Math.max(bulletSlot - bulletGap, 4)

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Shared scale along the track axis. */
  const valScale = horizontal
    ? linearScale([domainMin, domainMax], [0, plotW])
    : linearScale([domainMin, domainMax], [plotH, 0])

  /* Value axis ticks. */
  const ticks = niceTicks(domainMin, domainMax, 5)
  for (let t = 0; t < ticks.length; t = t + 1) {
    const tick = ticks[t]
    if (horizontal === true) {
      const x = valScale(tick)
      plot.appendChild(svgEl("text", {
        x: x, y: plotH + 16, "text-anchor": "middle",
        "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
      }, formatNumber(tick)))
      plot.appendChild(svgEl("line", {
        x1: x, y1: plotH, x2: x, y2: plotH + 4,
        stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1
      }, []))
    } else {
      const y = valScale(tick)
      plot.appendChild(svgEl("text", {
        x: -8, y: y + 4, "text-anchor": "end",
        "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
      }, formatNumber(tick)))
      plot.appendChild(svgEl("line", {
        x1: -4, y1: y, x2: 0, y2: y,
        stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1
      }, []))
    }
  }

  /* Value axis baseline. */
  if (horizontal === true) {
    plot.appendChild(svgEl("line", {
      x1: 0, y1: plotH, x2: plotW, y2: plotH,
      stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
    }, []))
  } else {
    plot.appendChild(svgEl("line", {
      x1: 0, y1: 0, x2: 0, y2: plotH,
      stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
    }, []))
  }

  /* Draw each bullet. */
  for (let s = 0; s < series.length; s = s + 1) {
    const bullet = series[s]
    let trackStart, trackCenter

    if (horizontal === true) {
      trackStart = s * bulletSlot + bulletGap / 2
      trackCenter = trackStart + bandThickness / 2
    } else {
      trackStart = s * bulletSlot + bulletGap / 2
      trackCenter = trackStart + bandThickness / 2
    }

    _drawBullet(plot, bullet, valScale, horizontal, trackStart, trackCenter,
      horizontal ? plotW : plotH, bandThickness, s, ctx)

    /* Bullet label. */
    const labelText = escapeHtml(bullet.name || "")
    if (horizontal === true) {
      plot.appendChild(svgEl("text", {
        x: -8, y: trackStart + bandThickness / 2 + 4, "text-anchor": "end",
        "font-size": 11, fill: "var(--mj-text, #14181f)"
      }, labelText))
    } else {
      plot.appendChild(svgEl("text", {
        x: trackStart + bandThickness / 2, y: plotH + 18, "text-anchor": "middle",
        "font-size": 11, fill: "var(--mj-text, #14181f)"
      }, labelText))
    }
  }

  return root
}


registerRenderer("bullet", render);
