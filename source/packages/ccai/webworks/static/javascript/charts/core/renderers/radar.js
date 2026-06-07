/*
 * radar.js
 *
 * Radar chart renderer (spider chart, web chart) -- compares multiple entities
 * across several quantitative dimensions simultaneously. Each spoke maps an
 * independent linear scale from 0 (or domainMin) to domainMax. Spoke angles
 * are evenly distributed starting from the top (0 radians = up, clockwise).
 *
 * A renderer is `render(ctx) -> SVGElement`:
 *   ctx.model       normalized model { meta, categories, series, raw }
 *   ctx.raw         the raw data object
 *   ctx.width       drawing surface width (px)
 *   ctx.height      drawing surface height (px)
 *   ctx.orientation n/a -- radially symmetric
 *   ctx.attrs       (name, fallback) -> controller attribute value
 *   ctx.colorFor    (seriesIndex | seriesName) -> CSS color
 *   ctx.emit        (eventName, detail) -> dispatch an interaction event
 * It returns a <g> SVGElement drawn within [0..width] x [0..height].
 *
 * Attributes:
 *   fill         "true" (default) | "false"  -- filled polygon vs. outline
 *   grid-shape   "polygon" (default) | "circle"  -- ring gridline shape
 *
 * Registered type keys: "radar"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber, polarPoint } from "../svgdraw.js";
import { linearScale, niceTicks } from "../scales.js";


const RING_COUNT = 4
const SPOKE_LABEL_PAD = 14
const AREA_OPACITY = "var(--mj-chart-area-opacity, 0.3)"


function _spokeAngle(index, total) {
  /*
   * Angle of the nth spoke in radians (0 = up, clockwise).
   *
   * :param index: Spoke index.
   * :param total: Total number of spokes.
   * :returns: Angle in radians.
   */
  const angle = (2 * Math.PI * index) / total
  return angle
}


function _polygonPoints(cx, cy, maxRadius, spokeCount, fraction) {
  /*
   * Compute SVG polygon points string for a regular polygon at a given
   * fraction of the maximum radius.
   *
   * :param cx: Centre x.
   * :param cy: Centre y.
   * :param maxRadius: Full radius at fraction = 1.
   * :param spokeCount: Number of vertices.
   * :param fraction: 0..1 fraction of maxRadius.
   * :returns: SVG points attribute string.
   */
  const radius = maxRadius * fraction
  const parts = []
  for (let i = 0; i < spokeCount; i = i + 1) {
    const angle = _spokeAngle(i, spokeCount)
    const pt = polarPoint(cx, cy, radius, angle)
    parts.push(`${pt.x.toFixed(2)},${pt.y.toFixed(2)}`)
  }
  const pointStr = parts.join(" ")
  return pointStr
}


function _seriesPolygonPoints(cx, cy, maxRadius, values, scales) {
  /*
   * Build the polygon points array for one series, using per-spoke scales.
   *
   * :param cx: Centre x.
   * :param cy: Centre y.
   * :param maxRadius: Maximum radius (corresponds to domain max).
   * :param values: Array of numeric values (one per spoke).
   * :param scales: Array of linear scales (one per spoke), mapping value -> [0,1].
   * :returns: Array of {x, y} objects.
   */
  const points = []
  for (let i = 0; i < values.length; i = i + 1) {
    const rawVal = values[i]
    const numeric = typeof rawVal === "number" ? rawVal : 0
    const fraction = scales[i](numeric)
    const angle = _spokeAngle(i, values.length)
    const pt = polarPoint(cx, cy, maxRadius * fraction, angle)
    points.push(pt)
  }
  return points
}


function _pointsToAttr(points) {
  /*
   * Convert an array of {x, y} objects to an SVG points attribute string.
   *
   * :param points: Array of {x, y} objects.
   * :returns: SVG points string.
   */
  const parts = points.map((p) => `${p.x.toFixed(2)},${p.y.toFixed(2)}`)
  const str = parts.join(" ")
  return str
}


export function render(ctx) {
  /*
   * Render a radar chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const root = svgEl("g", { part: "plot" }, [])

  const categories = model.categories    /* spoke labels */
  const series = model.series
  if (categories.length === 0 || series.length === 0) {
    return root
  }

  const fillEnabled = ctx.attrs("fill", "true") !== "false"
  const gridShape = ctx.attrs("grid-shape", "polygon")
  const spokeCount = categories.length

  const margin = { top: 40, right: 40, bottom: 40, left: 40 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)
  const cx = plotW / 2
  const cy = plotH / 2
  const maxRadius = Math.min(plotW, plotH) / 2 - SPOKE_LABEL_PAD

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Build per-spoke linear scales mapping value -> fraction [0, 1]. */
  const spokeScales = []
  for (let i = 0; i < spokeCount; i = i + 1) {
    let spokeMin = 0
    let spokeMax = 0
    for (let s = 0; s < series.length; s = s + 1) {
      const value = series[s].values[i]
      if (typeof value === "number" && value > spokeMax) {
        spokeMax = value
      }
    }
    if (spokeMax === 0) {
      spokeMax = 1
    }
    /* Allow per-series domainMin/domainMax if present on raw data. */
    const rawDimensions = model.raw && Array.isArray(model.raw.dimensions)
      ? model.raw.dimensions
      : []
    if (rawDimensions[i] !== undefined) {
      if (typeof rawDimensions[i].domainMin === "number") {
        spokeMin = rawDimensions[i].domainMin
      }
      if (typeof rawDimensions[i].domainMax === "number") {
        spokeMax = rawDimensions[i].domainMax
      }
    }
    if (spokeMax === spokeMin) {
      spokeMax = spokeMin + 1
    }
    spokeScales.push(linearScale([spokeMin, spokeMax], [0, 1]))
  }

  /* Ring gridlines. */
  for (let ring = 1; ring <= RING_COUNT; ring = ring + 1) {
    const fraction = ring / RING_COUNT

    if (gridShape === "circle") {
      plot.appendChild(svgEl("circle", {
        cx: cx, cy: cy, r: maxRadius * fraction,
        fill: "none",
        stroke: "var(--mj-border, #e0e3e9)",
        "stroke-width": 1
      }, []))
    } else {
      const polyPoints = _polygonPoints(cx, cy, maxRadius, spokeCount, fraction)
      plot.appendChild(svgEl("polygon", {
        points: polyPoints,
        fill: "none",
        stroke: "var(--mj-border, #e0e3e9)",
        "stroke-width": 1
      }, []))
    }

    /* Ring value label (uses first spoke scale for reference). */
    const ringValue = spokeScales[0].invert(fraction)
    plot.appendChild(svgEl("text", {
      x: cx + 4, y: cy - maxRadius * fraction + 4,
      "font-size": 9, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(ringValue, { maximumFractionDigits: 1 })))
  }

  /* Spoke lines and axis labels. */
  for (let i = 0; i < spokeCount; i = i + 1) {
    const angle = _spokeAngle(i, spokeCount)
    const tipPt = polarPoint(cx, cy, maxRadius, angle)

    plot.appendChild(svgEl("line", {
      x1: cx, y1: cy, x2: tipPt.x, y2: tipPt.y,
      stroke: "var(--mj-border, #e0e3e9)",
      "stroke-width": 1
    }, []))

    /* Position label beyond the tip. */
    const labelPt = polarPoint(cx, cy, maxRadius + SPOKE_LABEL_PAD, angle)
    const anchor = labelPt.x < cx - 2 ? "end" : labelPt.x > cx + 2 ? "start" : "middle"
    plot.appendChild(svgEl("text", {
      x: labelPt.x, y: labelPt.y + 4,
      "text-anchor": anchor,
      "font-size": 11, fill: "var(--mj-text, #14181f)"
    }, escapeHtml(categories[i])))
  }

  /* Series areas and dot markers. */
  for (let s = 0; s < series.length; s = s + 1) {
    const color = ctx.colorFor(series[s].name)
    const points = _seriesPolygonPoints(cx, cy, maxRadius,
      series[s].values, spokeScales)
    const pointsAttr = _pointsToAttr(points)

    if (fillEnabled === true) {
      const area = svgEl("polygon", {
        points: pointsAttr,
        fill: color,
        "fill-opacity": AREA_OPACITY,
        stroke: color,
        "stroke-width": 2,
        "stroke-linejoin": "round",
        part: "radar-area",
        tabindex: "0",
        role: "img",
        "aria-label": `${series[s].name}`
      }, [])
      area.appendChild(svgEl("title", null, series[s].name))
      const handler = () => {
        ctx.emit("mj-chart-radar-click", { series: series[s].name })
      }
      area.addEventListener("click", handler)
      area.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })
      plot.appendChild(area)
    } else {
      const outline = svgEl("polygon", {
        points: pointsAttr,
        fill: "none",
        stroke: color,
        "stroke-width": 2,
        "stroke-linejoin": "round",
        part: "radar-outline",
        tabindex: "0",
        role: "img",
        "aria-label": `${series[s].name}`
      }, [])
      outline.appendChild(svgEl("title", null, series[s].name))
      const handler = () => {
        ctx.emit("mj-chart-radar-click", { series: series[s].name })
      }
      outline.addEventListener("click", handler)
      outline.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })
      plot.appendChild(outline)
    }

    /* Dot markers at each data point. */
    for (let i = 0; i < points.length; i = i + 1) {
      const rawValue = series[s].values[i]
      const value = typeof rawValue === "number" ? rawValue : 0
      const dot = svgEl("circle", {
        cx: points[i].x, cy: points[i].y, r: 4,
        fill: color,
        part: "dot",
        tabindex: "0",
        role: "img",
        "aria-label": `${series[s].name}, ${categories[i]}: ${value}`
      }, [])

      dot.appendChild(svgEl("title", null,
        `${series[s].name} - ${categories[i]}: ${value}`))

      const handler = () => {
        ctx.emit("mj-chart-radar-dot-click", {
          series: series[s].name, category: categories[i], value: value
        })
      }
      dot.addEventListener("click", handler)
      dot.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })
      plot.appendChild(dot)
    }
  }

  /* Legend -- one row per series below the radar. */
  if (series.length > 1) {
    const legendY = margin.top + plotH + 12
    let legendX = margin.left
    for (let s = 0; s < series.length; s = s + 1) {
      const color = ctx.colorFor(series[s].name)
      const swatchEl = svgEl("rect", {
        x: legendX, y: legendY, width: 10, height: 10,
        fill: color, rx: 2
      }, [])
      root.appendChild(swatchEl)
      const textEl = svgEl("text", {
        x: legendX + 14, y: legendY + 9,
        "font-size": 11, fill: "var(--mj-text, #14181f)"
      }, escapeHtml(series[s].name))
      root.appendChild(textEl)
      legendX = legendX + 14 + series[s].name.length * 7 + 12
    }
  }

  return root
}


registerRenderer("radar", render);
