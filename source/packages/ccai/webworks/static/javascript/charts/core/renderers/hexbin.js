/*
 * hexbin.js
 *
 * Hexagonal-binning renderer.
 *
 * Registered chart types:
 *   "hexbin" — aggregates dense scatter points into hexagonal bins
 *
 * Data shape:
 *   model.series[].points: [{ x, y, value? }, ...]
 *   ctx.raw.hexbin?.radius  bin radius in pixels (default 20)
 *   ctx.raw.hexbin?.stat    "count" | "sum" | "mean" (default "count")
 *
 * Encoding:
 *   Default: fill color proportional to bin stat (sequential ramp).
 *   ctx.attrs("encoding") === "size" → hexagon drawn at radius proportional
 *   to stat; background cell always drawn at full radius for reference.
 *
 * The offset-grid hexbin algorithm is self-contained (no external library).
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, extent } from "../svgdraw.js";
import { linearScale, sqrtScale, niceTicks } from "../scales.js";


/* Sequential ramp for bin intensity. */
const HEX_RAMP = [
  "var(--mj-chart-heat-1, #eff6ff)",
  "var(--mj-chart-heat-2, #bfdbfe)",
  "var(--mj-chart-heat-3, #93c5fd)",
  "var(--mj-chart-heat-4, #60a5fa)",
  "var(--mj-chart-heat-5, #3b82f6)",
  "var(--mj-chart-heat-6, #2563eb)",
  "var(--mj-chart-heat-7, #1d4ed8)",
  "var(--mj-chart-heat-8, #1e40af)"
]


function _hexColor(fraction) {
  /*
   * Map a [0,1] fraction to a hex-ramp color.
   *
   * :param fraction: Normalized bin value in [0, 1].
   * :returns: CSS color string.
   */
  const index = Math.min(
    HEX_RAMP.length - 1,
    Math.floor(fraction * HEX_RAMP.length)
  )
  return HEX_RAMP[index]
}


function _hexPoints(cx, cy, r) {
  /*
   * Compute the six corner points of a regular hexagon (flat-top orientation).
   *
   * :param cx: Center x.
   * :param cy: Center y.
   * :param r: Circumradius.
   * :returns: SVG points string.
   */
  const pts = []
  for (let i = 0; i < 6; i = i + 1) {
    const angle = (Math.PI / 180) * (60 * i)
    const px = cx + r * Math.cos(angle)
    const py = cy + r * Math.sin(angle)
    pts.push(`${px.toFixed(2)},${py.toFixed(2)}`)
  }
  return pts.join(" ")
}


function _hexBin(points, xScale, yScale, radius) {
  /*
   * Bin XY points into hexagonal grid cells using offset-grid geometry.
   *
   * The grid uses pointy-top hexagons (rotated 30° from flat-top) in
   * axial coordinates; each point is assigned to its nearest hex center.
   *
   * :param points: Array of { x, y, value? } in data space.
   * :param xScale: Pixel scale for x.
   * :param yScale: Pixel scale for y.
   * :param radius: Hexagon circumradius in pixels.
   * :returns: Map from "col,row" key → { cx, cy, pts: [...] }.
   */
  /* Hexagonal grid constants for pointy-top orientation. */
  const w = Math.sqrt(3) * radius   /* width of one hex cell  */
  const h = 2 * radius              /* height of one hex cell */

  const bins = new Map()

  for (let i = 0; i < points.length; i = i + 1) {
    const pt = points[i]
    const px = xScale(pt.x)
    const py = yScale(pt.y)

    /* Axial grid coordinates. */
    const q = ((2 / 3) * px) / radius
    const r = ((-1 / 3) * px + (Math.sqrt(3) / 3) * py) / radius

    /* Round to nearest hex using cube rounding. */
    const s = -q - r
    let rq = Math.round(q)
    let rr = Math.round(r)
    const rs = Math.round(s)
    const dq = Math.abs(rq - q)
    const dr = Math.abs(rr - r)
    const ds = Math.abs(rs - s)
    if (dq > dr && dq > ds) {
      rq = -rr - rs
    } else if (dr > ds) {
      rr = -rq - rs
    }

    const key = `${rq},${rr}`
    if (bins.has(key) === false) {
      /* Compute center of this hex in pixel space. */
      const cx = radius * (3 / 2) * rq
      const cy = radius * (Math.sqrt(3) * rr + (Math.sqrt(3) / 2) * rq)
      bins.set(key, { cx: cx, cy: cy, pts: [] })
    }
    bins.get(key).pts.push(pt)
  }

  return bins
}


function _aggregateBin(pts, stat) {
  /*
   * Compute the bin statistic from accumulated points.
   *
   * :param pts: Array of { x, y, value? }.
   * :param stat: "count" | "sum" | "mean".
   * :returns: Numeric statistic value.
   */
  if (stat === "sum") {
    let total = 0
    for (let i = 0; i < pts.length; i = i + 1) {
      const v = pts[i].value
      if (typeof v === "number" && Number.isNaN(v) === false) {
        total = total + v
      }
    }
    return total
  }
  if (stat === "mean") {
    let total = 0
    let count = 0
    for (let i = 0; i < pts.length; i = i + 1) {
      const v = pts[i].value
      if (typeof v === "number" && Number.isNaN(v) === false) {
        total = total + v
        count = count + 1
      }
    }
    return count > 0 ? total / count : 0
  }
  /* Default: count */
  return pts.length
}


export function render(ctx) {
  /*
   * Render a hexbin chart.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const model = ctx.model
  const rawHex = (ctx.raw !== null && ctx.raw !== undefined)
    ? ctx.raw.hexbin || {}
    : {}

  const binRadius = Math.max(4, Number(rawHex.radius) || Number(ctx.attrs("radius", "20")))
  const stat = rawHex.stat || ctx.attrs("stat", "count")
  const encoding = ctx.attrs("encoding", "color")
  const showLabels = ctx.attrs("show-labels", "false") === "true"

  const root = svgEl("g", { part: "plot" }, [])

  const series = model.series
  if (series === null || series === undefined || series.length === 0) {
    return root
  }

  /* Collect all points (merge series for density). */
  let allPoints = []
  for (let s = 0; s < series.length; s = s + 1) {
    const pts = series[s].points
    if (pts === null || pts === undefined) {
      continue
    }
    for (let p = 0; p < pts.length; p = p + 1) {
      const pt = pts[p]
      const validX = typeof pt.x === "number" && Number.isNaN(pt.x) === false
      const validY = typeof pt.y === "number" && Number.isNaN(pt.y) === false
      if (validX === true && validY === true) {
        allPoints.push(pt)
      }
    }
  }

  if (allPoints.length === 0) {
    return root
  }

  const margin = { top: 16, right: 16, bottom: 44, left: 56 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const xVals = allPoints.map((pt) => pt.x)
  const yVals = allPoints.map((pt) => pt.y)
  const xDomain = extent(xVals)
  const yDomain = extent(yVals)

  const xPad = (xDomain[1] - xDomain[0]) * 0.05 || 1
  const yPad = (yDomain[1] - yDomain[0]) * 0.05 || 1

  const xScale = linearScale(
    [xDomain[0] - xPad, xDomain[1] + xPad],
    [0, plotW]
  )
  const yScale = linearScale(
    [yDomain[0] - yPad, yDomain[1] + yPad],
    [plotH, 0]
  )

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Grid lines + tick labels. */
  const xTicks = niceTicks(xScale.domain()[0], xScale.domain()[1], 5)
  for (let t = 0; t < xTicks.length; t = t + 1) {
    const tick = xTicks[t]
    const x = xScale(tick)
    plot.appendChild(svgEl("line", {
      x1: x, y1: 0, x2: x, y2: plotH,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    plot.appendChild(svgEl("text", {
      x: x, y: plotH + 16, "text-anchor": "middle",
      "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(tick)))
  }

  const yTicks = niceTicks(yScale.domain()[0], yScale.domain()[1], 5)
  for (let t = 0; t < yTicks.length; t = t + 1) {
    const tick = yTicks[t]
    const y = yScale(tick)
    plot.appendChild(svgEl("line", {
      x1: 0, y1: y, x2: plotW, y2: y,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    plot.appendChild(svgEl("text", {
      x: -8, y: y + 4, "text-anchor": "end",
      "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(tick)))
  }

  /* Clip path so hexagons don't overflow the plot area. */
  const clipId = "hexbin-clip-" + Math.random().toString(36).slice(2, 8)
  const defs = svgEl("defs", null, [])
  const clipPath = svgEl("clipPath", { id: clipId }, [])
  clipPath.appendChild(svgEl("rect", {
    x: 0, y: 0, width: plotW, height: plotH
  }, []))
  defs.appendChild(clipPath)
  plot.appendChild(defs)

  const hexGroup = svgEl("g", { "clip-path": `url(#${clipId})` }, [])
  plot.appendChild(hexGroup)

  /* Bin the points. */
  const bins = _hexBin(allPoints, xScale, yScale, binRadius)

  /* Compute bin statistics and domain. */
  const binStats = []
  bins.forEach((bin, key) => {
    const statValue = _aggregateBin(bin.pts, stat)
    binStats.push({ key: key, cx: bin.cx, cy: bin.cy, statValue: statValue, count: bin.pts.length })
  })

  const statValues = binStats.map((b) => b.statValue)
  const statDomain = extent(statValues)

  /* Size scale for size-encoding mode. */
  let sizeScale = null
  if (encoding === "size") {
    sizeScale = sqrtScale([0, statDomain[1]], [2, binRadius])
  }

  /* Draw hexagons. */
  for (let i = 0; i < binStats.length; i = i + 1) {
    const bin = binStats[i]
    const cx = bin.cx
    const cy = bin.cy

    /* Skip bins whose center is outside an expanded plot area. */
    if (cx < -binRadius * 2 || cx > plotW + binRadius * 2 ||
        cy < -binRadius * 2 || cy > plotH + binRadius * 2) {
      continue
    }

    const span = statDomain[1] - statDomain[0] || 1
    const fraction = Math.max(0, Math.min(1, (bin.statValue - statDomain[0]) / span))

    let drawRadius = binRadius
    let fillColor = _hexColor(fraction)

    if (encoding === "size") {
      /* Draw a faint full-size background hex first. */
      hexGroup.appendChild(svgEl("polygon", {
        points: _hexPoints(cx, cy, binRadius),
        fill: "var(--mj-chart-heat-1, #eff6ff)",
        stroke: "var(--mj-border, #e0e3e9)",
        "stroke-width": 0.5
      }, []))
      drawRadius = sizeScale !== null ? sizeScale(bin.statValue) : binRadius
      fillColor = "var(--mj-color-accent-500, #2563eb)"
    }

    const hexEl = svgEl("polygon", {
      points: _hexPoints(cx, cy, drawRadius),
      fill: fillColor,
      stroke: "var(--mj-surface, #ffffff)",
      "stroke-width": 0.5,
      part: "hexbin"
    }, [])

    hexEl.setAttribute("tabindex", "0")
    hexEl.setAttribute("role", "img")
    const ariaLabel = `Bin at (${cx.toFixed(1)}, ${cy.toFixed(1)}): ${stat}=${formatNumber(bin.statValue)}`
    hexEl.setAttribute("aria-label", ariaLabel)
    hexEl.appendChild(svgEl("title", null,
      `${stat}: ${formatNumber(bin.statValue)} (${bin.count} point${bin.count === 1 ? "" : "s"})`))

    const statVal = bin.statValue
    const binCx = cx
    const binCy = cy
    const handler = () => {
      ctx.emit("mj-chart-hexbin-click", {
        cx: binCx, cy: binCy,
        stat: stat, value: statVal, count: bin.count
      })
    }
    hexEl.addEventListener("click", handler)
    hexEl.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        handler()
      }
    })
    hexGroup.appendChild(hexEl)

    /* Optional count/stat label inside bin. */
    if (showLabels === true && drawRadius > 10) {
      hexGroup.appendChild(svgEl("text", {
        x: cx, y: cy + 4,
        "text-anchor": "middle",
        "font-size": Math.max(8, Math.min(11, drawRadius * 0.4)),
        fill: fraction > 0.6
          ? "var(--mj-text-on-strong, #ffffff)"
          : "var(--mj-text, #14181f)",
        "pointer-events": "none"
      }, formatNumber(bin.statValue)))
    }
  }

  /* Axis baselines. */
  plot.appendChild(svgEl("line", {
    x1: 0, y1: plotH, x2: plotW, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))
  plot.appendChild(svgEl("line", {
    x1: 0, y1: 0, x2: 0, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))

  return root
}


registerRenderer("hexbin", render)
