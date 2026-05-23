/*
 * polar.js
 *
 * Radial bar / area chart family renderer.
 *
 * Registered types:
 *   "polar"        - continuous polar line/area chart (angle + radius)
 *   "wind-rose"    - directional frequency chart with stacked wedge petals
 *   "nightingale"  - polar area (coxcomb) chart, area encodes value
 *   "coxcomb"      - alias for nightingale
 *
 * Renderer contract: render(ctx) -> SVGElement  (a <g> within [0..width]x[0..height])
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber, arcPath, polarPoint } from "../svgdraw.js";
import { linearScale, sqrtScale, niceTicks } from "../scales.js";


/* ── helpers ──────────────────────────────────────────────────── */

function _toRadians(theta, unit) {
  /*
   * Convert theta to radians.  unit is "degrees" (default) or "radians".
   */
  const radians = unit === "radians" ? theta : theta * (Math.PI / 180)
  return radians
}


function _drawGrid(plot, cx, cy, maxR, rTicks) {
  /*
   * Draw concentric-ring and spoke gridlines.
   */
  const spokeCount = 8
  for (let i = 0; i < rTicks.length; i = i + 1) {
    const r = rTicks[i]
    if (r <= 0) {
      continue
    }
    plot.appendChild(svgEl("circle", {
      cx: cx, cy: cy, r: r,
      fill: "none",
      stroke: "var(--mj-border, #e0e3e9)",
      "stroke-width": 1
    }, []))
  }

  for (let s = 0; s < spokeCount; s = s + 1) {
    const angle = (s / spokeCount) * Math.PI * 2
    const end = polarPoint(cx, cy, maxR, angle)
    plot.appendChild(svgEl("line", {
      x1: cx, y1: cy, x2: end.x, y2: end.y,
      stroke: "var(--mj-border, #e0e3e9)",
      "stroke-width": 1
    }, []))
  }
  return
}


function _drawRadialLabels(plot, cx, cy, maxR, rScale, rTicks) {
  /*
   * Draw radial (r-axis) tick labels just inside the top spoke.
   */
  for (let i = 0; i < rTicks.length; i = i + 1) {
    const tick = rTicks[i]
    if (tick <= 0) {
      continue
    }
    const rPx = rScale(tick)
    plot.appendChild(svgEl("text", {
      x: cx + 4, y: cy - rPx + 4,
      "font-size": 9,
      fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(tick)))
  }
  return
}


/* ── polar (line / area) ───────────────────────────────────────── */

function _renderPolar(ctx) {
  /*
   * Render a polar line or area chart.
   */
  const raw = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])

  const series = (raw.series !== null && raw.series !== undefined)
    ? raw.series : []
  if (series.length === 0) {
    return root
  }

  const margin = 40
  const cx = ctx.width / 2
  const cy = ctx.height / 2
  const maxR = Math.min(cx, cy) - margin

  const thetaUnit = (raw.thetaUnit !== null && raw.thetaUnit !== undefined)
    ? raw.thetaUnit : "degrees"
  const fillArea = ctx.attrs("fill", "false") === "true"

  /* Collect all r values to build r scale. */
  let rMin = (raw.rMin !== null && raw.rMin !== undefined) ? raw.rMin : 0
  let rMax = rMin

  for (let s = 0; s < series.length; s = s + 1) {
    const pts = series[s].points
    if (pts === null || pts === undefined) {
      continue
    }
    for (let p = 0; p < pts.length; p = p + 1) {
      const r = pts[p].r
      if (typeof r === "number" && r > rMax) {
        rMax = r
      }
    }
  }
  if (rMax === rMin) {
    rMax = rMin + 1
  }

  const rScale = linearScale([rMin, rMax], [0, maxR])
  const rTicks = niceTicks(rMin, rMax, 4)
  const rTickPx = rTicks.map((t) => rScale(t))

  /* Grid */
  _drawGrid(root, cx, cy, maxR, rTickPx)
  _drawRadialLabels(root, cx, cy, maxR, rScale, rTicks)

  /* Series */
  for (let s = 0; s < series.length; s = s + 1) {
    const ser = series[s]
    const pts = ser.points
    if (pts === null || pts === undefined || pts.length === 0) {
      continue
    }
    const color = ctx.colorFor(ser.name)
    const pixPts = []

    for (let p = 0; p < pts.length; p = p + 1) {
      const theta = _toRadians(pts[p].theta, thetaUnit)
      const r = typeof pts[p].r === "number" ? pts[p].r : 0
      const rPx = rScale(r)
      pixPts.push(polarPoint(cx, cy, rPx, theta))
    }

    /* Close path back to first point */
    const closedPts = pixPts.concat([pixPts[0]])

    let pathData = "M" + closedPts[0].x.toFixed(2) + "," + closedPts[0].y.toFixed(2)
    for (let p = 1; p < closedPts.length; p = p + 1) {
      pathData = pathData + " L" + closedPts[p].x.toFixed(2) + "," + closedPts[p].y.toFixed(2)
    }

    if (fillArea === true) {
      const fillEl = svgEl("path", {
        d: pathData + " Z",
        fill: color,
        "fill-opacity": 0.2,
        stroke: color,
        "stroke-width": 1.5
      }, [])
      root.appendChild(fillEl)
    } else {
      const lineEl = svgEl("path", {
        d: pathData,
        fill: "none",
        stroke: color,
        "stroke-width": 2
      }, [])
      root.appendChild(lineEl)
    }

    /* Interactive marks per data point */
    for (let p = 0; p < pts.length; p = p + 1) {
      const pt = pts[p]
      const px = pixPts[p]
      const label = escapeHtml(
        ser.name + " θ=" + pt.theta + " r=" + formatNumber(pt.r)
      )
      const dot = svgEl("circle", {
        cx: px.x, cy: px.y, r: 4,
        fill: color,
        stroke: "var(--mj-surface, #fff)",
        "stroke-width": 1,
        part: "point",
        tabindex: "0",
        role: "img",
        "aria-label": label
      }, [])
      dot.appendChild(svgEl("title", null, label))
      const detail = { series: ser.name, theta: pt.theta, r: pt.r }
      const handler = () => { ctx.emit("mj-chart-polar-click", detail) }
      dot.addEventListener("click", handler)
      dot.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })
      root.appendChild(dot)
    }
  }

  /* Angular labels around perimeter */
  const angleLabels = ["0°", "45°", "90°", "135°", "180°", "225°", "270°", "315°"]
  const labelR = maxR + 14
  for (let i = 0; i < angleLabels.length; i = i + 1) {
    const angle = (i / angleLabels.length) * Math.PI * 2
    const pos = polarPoint(cx, cy, labelR, angle)
    root.appendChild(svgEl("text", {
      x: pos.x, y: pos.y + 4,
      "text-anchor": "middle",
      "font-size": 10,
      fill: "var(--mj-text-muted, #6b7280)"
    }, angleLabels[i]))
  }

  return root
}


/* ── wind-rose ────────────────────────────────────────────────── */

function _renderWindRose(ctx) {
  /*
   * Render a directional wind-rose chart with stacked wedge petals.
   */
  const raw = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])

  const directions = (raw.directions !== null && raw.directions !== undefined)
    ? raw.directions : []
  const series = (raw.series !== null && raw.series !== undefined)
    ? raw.series : []

  if (directions.length === 0 || series.length === 0) {
    return root
  }

  const margin = 40
  const cx = ctx.width / 2
  const cy = ctx.height / 2
  const maxR = Math.min(cx, cy) - margin
  const dirCount = directions.length
  const angleStep = (Math.PI * 2) / dirCount
  const halfStep = angleStep / 2

  /* Compute stacked max for r scale */
  let rMax = 0
  for (let d = 0; d < dirCount; d = d + 1) {
    let stack = 0
    for (let s = 0; s < series.length; s = s + 1) {
      const v = series[s].values[d]
      stack = stack + (typeof v === "number" ? v : 0)
    }
    if (stack > rMax) {
      rMax = stack
    }
  }
  if (rMax === 0) {
    rMax = 1
  }

  const rScale = linearScale([0, rMax], [0, maxR])
  const rTicks = niceTicks(0, rMax, 4)
  const rTickPx = rTicks.map((t) => rScale(t))

  _drawGrid(root, cx, cy, maxR, rTickPx)
  _drawRadialLabels(root, cx, cy, maxR, rScale, rTicks)

  /* Draw petals per direction */
  for (let d = 0; d < dirCount; d = d + 1) {
    /* North-up: direction index 0 = north = angle 0 (up) */
    const centerAngle = (d / dirCount) * Math.PI * 2
    const startAngle = centerAngle - halfStep
    const endAngle = centerAngle + halfStep

    let stackBase = 0

    for (let s = 0; s < series.length; s = s + 1) {
      const value = typeof series[s].values[d] === "number" ? series[s].values[d] : 0
      if (value <= 0) {
        stackBase = stackBase + value
        continue
      }
      const innerR = rScale(stackBase)
      const outerR = rScale(stackBase + value)
      const color = ctx.colorFor(series[s].name)
      const pathData = arcPath(cx, cy, innerR, outerR, startAngle, endAngle)
      const label = escapeHtml(
        directions[d] + " " + series[s].name + ": " + formatNumber(value)
      )
      const wedge = svgEl("path", {
        d: pathData,
        fill: color,
        "fill-opacity": 0.85,
        stroke: "var(--mj-surface, #fff)",
        "stroke-width": 0.5,
        part: "petal",
        tabindex: "0",
        role: "img",
        "aria-label": label
      }, [])
      wedge.appendChild(svgEl("title", null, label))
      const detail = {
        direction: directions[d],
        series: series[s].name,
        value: value
      }
      const handler = () => { ctx.emit("mj-chart-windrose-click", detail) }
      wedge.addEventListener("click", handler)
      wedge.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })
      root.appendChild(wedge)
      stackBase = stackBase + value
    }

    /* Direction label */
    const labelPos = polarPoint(cx, cy, maxR + 14, centerAngle)
    root.appendChild(svgEl("text", {
      x: labelPos.x, y: labelPos.y + 4,
      "text-anchor": "middle",
      "font-size": 10,
      fill: "var(--mj-text, #14181f)"
    }, escapeHtml(directions[d])))
  }

  return root
}


/* ── nightingale / coxcomb ────────────────────────────────────── */

function _renderNightingale(ctx) {
  /*
   * Render a Nightingale rose (polar area / coxcomb) chart.
   * Area encodes value via sqrt scale.
   */
  const model = ctx.model
  const root = svgEl("g", { part: "plot" }, [])

  const categories = model.categories
  const series = model.series

  if (categories.length === 0 || series.length === 0) {
    return root
  }

  const margin = 40
  const cx = ctx.width / 2
  const cy = ctx.height / 2
  const maxR = Math.min(cx, cy) - margin
  const catCount = categories.length
  const angleStep = (Math.PI * 2) / catCount

  /* Compute stacked max */
  let vMax = 0
  for (let c = 0; c < catCount; c = c + 1) {
    let stack = 0
    for (let s = 0; s < series.length; s = s + 1) {
      const v = series[s].values[c]
      stack = stack + (typeof v === "number" ? v : 0)
    }
    if (stack > vMax) {
      vMax = stack
    }
  }
  if (vMax === 0) {
    vMax = 1
  }

  /* sqrt scale so area is proportional to value */
  const rScale = sqrtScale([0, vMax], [0, maxR])
  const rTicks = niceTicks(0, vMax, 4)
  const rTickPx = rTicks.map((t) => rScale(t))

  _drawGrid(root, cx, cy, maxR, rTickPx)
  _drawRadialLabels(root, cx, cy, maxR, rScale, rTicks)

  for (let c = 0; c < catCount; c = c + 1) {
    const startAngle = (c / catCount) * Math.PI * 2
    const endAngle = startAngle + angleStep

    let stackBase = 0

    for (let s = 0; s < series.length; s = s + 1) {
      const value = typeof series[s].values[c] === "number" ? series[s].values[c] : 0
      if (value <= 0) {
        stackBase = stackBase + value
        continue
      }
      const innerR = rScale(stackBase)
      const outerR = rScale(stackBase + value)
      const color = ctx.colorFor(series[s].name)
      const pathData = arcPath(cx, cy, innerR, outerR, startAngle, endAngle)
      const label = escapeHtml(
        categories[c] + " " + series[s].name + ": " + formatNumber(value)
      )
      const wedge = svgEl("path", {
        d: pathData,
        fill: color,
        "fill-opacity": 0.85,
        stroke: "var(--mj-surface, #fff)",
        "stroke-width": 0.5,
        part: "sector",
        tabindex: "0",
        role: "img",
        "aria-label": label
      }, [])
      wedge.appendChild(svgEl("title", null, label))
      const detail = {
        category: categories[c],
        series: series[s].name,
        value: value
      }
      const handler = () => { ctx.emit("mj-chart-nightingale-click", detail) }
      wedge.addEventListener("click", handler)
      wedge.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })
      root.appendChild(wedge)
      stackBase = stackBase + value
    }

    /* Category label */
    const midAngle = startAngle + angleStep / 2
    const labelPos = polarPoint(cx, cy, maxR + 14, midAngle)
    root.appendChild(svgEl("text", {
      x: labelPos.x, y: labelPos.y + 4,
      "text-anchor": "middle",
      "font-size": 10,
      fill: "var(--mj-text, #14181f)"
    }, escapeHtml(categories[c])))
  }

  return root
}


/* ── dispatch ─────────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Dispatch to the correct polar-family sub-renderer.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const type = (ctx.raw !== null && ctx.raw !== undefined && ctx.raw.meta !== undefined)
    ? ctx.attrs("type", "polar") : ctx.attrs("type", "polar")

  /* Use the controller-level type attribute to route */
  const chartType = ctx.attrs("type", "polar")

  if (chartType === "wind-rose") {
    return _renderWindRose(ctx)
  }
  if (chartType === "nightingale" || chartType === "coxcomb") {
    return _renderNightingale(ctx)
  }
  return _renderPolar(ctx)
}


registerRenderer("polar", render)
registerRenderer("wind-rose", render)
registerRenderer("nightingale", render)
registerRenderer("coxcomb", render)
