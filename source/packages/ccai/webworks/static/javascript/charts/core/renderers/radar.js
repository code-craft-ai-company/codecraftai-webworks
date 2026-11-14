/*
 * radar.js
 *
 * Radar chart renderer (spider chart, web chart) -- compares multiple entities
 * across several quantitative dimensions simultaneously. Spoke angles are
 * evenly distributed starting from the top (0 radians = up, clockwise).
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
 * Several series get a key row under the radar; it is left out when an
 * <mj-chart-legend> is bound to the chart (ctx.hasLegendPart).
 *
 * Attributes:
 *   fill         boolean (default true)  -- filled polygon vs. outline
 *   grid-shape   "polygon" (default) | "circle"  -- ring gridline shape
 *
 * Scales: every spoke shares one value scale from 0 (or the smallest value,
 * when a value is negative) to a nice maximum above the largest value, so
 * spokes can be compared and the rings are labelled with values. A spoke
 * gets its own scale only when the data supplies one:
 *   "dimensions": [{ "domainMin": 0, "domainMax": 5 }, ...]   (by spoke index)
 * The rings are then unlabelled and each spoke label shows its range.
 * Values outside a spoke's scale are drawn at its centre or rim.
 *
 * Each series has one value per spoke; extra values are ignored and a
 * missing / null value is a gap (the outline is open there and not
 * filled). All polygons are drawn before all dots, so every dot stays
 * hoverable.
 *
 * Registered type keys: "radar"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, polarPoint } from "../svgdraw.js";
import { linearScale, niceTicks, niceDomain } from "../scales.js";
import {
  LABEL_FONT_SIZE, textWidth, truncateText, numericValue, inlineLegend, activate
} from "./bar.js";
import { booleanOption } from "../chartoptions.js";

const SPOKE_LABEL_PAD = 10;
const AREA_OPACITY = "var(--mj-chart-area-opacity, 0.3)";


function _spokeAngle(index, total) {
  /*
   * Angle of the nth spoke in radians (0 = up, clockwise).
   */
  const angle = (2 * Math.PI * index) / total
  return angle
}


function _ringPoints(cx, cy, radius, spokeCount) {
  /*
   * SVG points of a regular polygon ring.
   */
  const parts = []
  for (let index = 0; index < spokeCount; index = index + 1) {
    const point = polarPoint(cx, cy, radius, _spokeAngle(index, spokeCount))
    parts.push(`${point.x.toFixed(2)},${point.y.toFixed(2)}`)
  }
  return parts.join(" ")
}


function _spokeDomains(model, values, spokeCount) {
  /*
   * The value domain of every spoke: a shared nice domain, replaced per
   * spoke by data-supplied dimensions[i].domainMin / domainMax.
   *
   * :returns: { domains: [[min, max]], shared: [min, max], uniform: bool }
   */
  let low = 0
  let high = 0
  for (let s = 0; s < values.length; s = s + 1) {
    for (let i = 0; i < spokeCount; i = i + 1) {
      if (values[s][i] !== null) {
        low = Math.min(low, values[s][i])
        high = Math.max(high, values[s][i])
      }
    }
  }
  if (high === low) {
    high = low + 1
  }
  const shared = niceDomain(low, high, 4)

  const dimensions = model.raw !== null && model.raw !== undefined && Array.isArray(model.raw.dimensions) === true
    ? model.raw.dimensions
    : []
  const domains = []
  let uniform = true
  for (let i = 0; i < spokeCount; i = i + 1) {
    const dimension = dimensions[i] !== null && typeof dimensions[i] === "object" ? dimensions[i] : null
    let domain = shared
    if (dimension !== null) {
      const min = numericValue(dimension.domainMin)
      const max = numericValue(dimension.domainMax)
      if (min !== null || max !== null) {
        domain = [min !== null ? min : shared[0], max !== null ? max : shared[1]]
        if (domain[1] === domain[0]) {
          domain = [domain[0], domain[0] + 1]
        }
        uniform = false
      }
    }
    domains.push(domain)
  }
  return { domains: domains, shared: shared, uniform: uniform }
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

  const categories = model.categories.map((category) => String(category))
  const series = model.series
  if (categories.length === 0 || series.length === 0) {
    return root
  }

  const fillEnabled = booleanOption(ctx, "fill", true)
  const gridShape = ctx.attrs("grid-shape", "polygon") === "circle" ? "circle" : "polygon"
  const spokeCount = categories.length

  /* One value (or null) per spoke and series. */
  const values = series.map((entry) => {
    const row = []
    for (let i = 0; i < spokeCount; i = i + 1) {
      row.push(numericValue(entry.values[i]))
    }
    return row
  })
  const scales = _spokeDomains(model, values, spokeCount)
  const fractionOf = scales.domains.map((domain) => linearScale(domain, [0, 1]))

  /*
   * Legend row below the radar for several series, unless an
   * <mj-chart-legend> is bound (it lists the series as toggles).
   */
  const legendEntries = series.length > 1 && ctx.hasLegendPart !== true
    ? series.map((entry) => ({ label: entry.name, color: ctx.colorFor(entry.name) }))
    : []
  const legend = inlineLegend(legendEntries, 0, 0, Math.max(ctx.width - 24, 40))
  const legendHeight = legend.height > 0 ? legend.height + 8 : 0

  /* Radius: leave room for the spoke labels at the sides. */
  const labelCap = ctx.width * 0.22
  let sideLabel = 0
  for (let i = 0; i < spokeCount; i = i + 1) {
    const angle = _spokeAngle(i, spokeCount)
    if (Math.abs(Math.sin(angle)) > 0.3) {
      sideLabel = Math.max(sideLabel, Math.min(textWidth(categories[i]), labelCap))
    }
  }
  const topRoom = scales.uniform === true ? 20 : 32
  const availableH = Math.max(ctx.height - legendHeight - 2 * topRoom, 20)
  const maxRadius = Math.max(16, Math.min(availableH / 2, ctx.width / 2 - sideLabel - SPOKE_LABEL_PAD - 10))
  const cx = ctx.width / 2
  const cy = topRoom + availableH / 2

  const plot = svgEl("g", { part: "radar" }, [])
  const chrome = svgEl("g", { "aria-hidden": "true", part: "axes" }, [])
  plot.appendChild(chrome)
  root.appendChild(plot)

  /* Rings: at the shared scale's ticks when every spoke shares it. */
  let rings = [0.25, 0.5, 0.75, 1].map((fraction) => ({ fraction: fraction, label: null }))
  if (scales.uniform === true) {
    const shared = scales.shared
    const ticks = niceTicks(shared[0], shared[1], 4).filter((tick) => tick > shared[0])
    const ringScale = linearScale(shared, [0, 1])
    rings = ticks.map((tick) => ({ fraction: ringScale(tick), label: formatNumber(tick) }))
  }
  for (let r = 0; r < rings.length; r = r + 1) {
    const radius = maxRadius * rings[r].fraction
    if (gridShape === "circle") {
      chrome.appendChild(svgEl("circle", {
        cx: cx, cy: cy, r: radius, fill: "none", stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
      }, []))
    } else {
      chrome.appendChild(svgEl("polygon", {
        points: _ringPoints(cx, cy, radius, spokeCount),
        fill: "none", stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
      }, []))
    }
    if (rings[r].label !== null) {
      chrome.appendChild(svgEl("text", {
        x: cx + 4, y: cy - radius + 10,
        "font-size": 9, fill: "var(--mj-text-muted, #5f6673)"
      }, rings[r].label))
    }
  }

  /* Spokes and their labels (with the spoke's range when it has its own). */
  for (let i = 0; i < spokeCount; i = i + 1) {
    const angle = _spokeAngle(i, spokeCount)
    const tip = polarPoint(cx, cy, maxRadius, angle)
    chrome.appendChild(svgEl("line", {
      x1: cx, y1: cy, x2: tip.x, y2: tip.y, stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))

    const at = polarPoint(cx, cy, maxRadius + SPOKE_LABEL_PAD, angle)
    const anchor = at.x < cx - 2 ? "end" : at.x > cx + 2 ? "start" : "middle"
    const room = anchor === "middle" ? ctx.width : (anchor === "end" ? at.x - 2 : ctx.width - at.x - 2)
    const above = Math.cos(angle) > 0.3
    const below = Math.cos(angle) < -0.3
    const baseY = above === true ? at.y - 2 : below === true ? at.y + 10 : at.y + 4
    const label = svgEl("text", {
      x: at.x, y: baseY, "text-anchor": anchor,
      "font-size": LABEL_FONT_SIZE, fill: "var(--mj-text, #14181f)"
    }, truncateText(categories[i], Math.min(room, labelCap)))
    chrome.appendChild(label)
    if (scales.uniform === false) {
      const domain = scales.domains[i]
      chrome.appendChild(svgEl("text", {
        x: at.x, y: baseY + (above === true ? -12 : 12), "text-anchor": anchor,
        "font-size": 9, fill: "var(--mj-text-muted, #5f6673)"
      }, `${formatNumber(domain[0])} to ${formatNumber(domain[1])}`))
    }
  }

  /* Vertex positions; null values are gaps. */
  const vertices = values.map((row) => row.map((value, i) => {
    if (value === null) {
      return null
    }
    const fraction = Math.min(Math.max(fractionOf[i](value), 0), 1)
    return polarPoint(cx, cy, maxRadius * fraction, _spokeAngle(i, spokeCount))
  }))

  /* All polygons first ... */
  const areas = svgEl("g", { part: "areas" }, [])
  const markers = svgEl("g", { part: "dots" }, [])
  plot.appendChild(areas)
  plot.appendChild(markers)

  for (let s = 0; s < series.length; s = s + 1) {
    const name = series[s].name
    const color = ctx.colorFor(name)
    const points = vertices[s]
    const complete = points.every((point) => point !== null)
    const summary = categories.map((category, i) => `${category} ${values[s][i] !== null ? formatNumber(values[s][i]) : "no value"}`)
    const text = `${name}: ${summary.join(", ")}`

    let data = ""
    if (complete === true) {
      data = points.map((point, i) => `${i === 0 ? "M" : "L"}${point.x.toFixed(2)},${point.y.toFixed(2)}`).join(" ") + " Z"
    } else {
      /* Open runs of consecutive vertices, wrapping round the last spoke. */
      const start = points.findIndex((point) => point === null)
      let drawing = false
      for (let step = 1; step <= spokeCount; step = step + 1) {
        const point = points[(start + step) % spokeCount]
        if (point === null) {
          drawing = false
          continue
        }
        data = data + `${drawing === true ? "L" : "M"}${point.x.toFixed(2)},${point.y.toFixed(2)} `
        drawing = true
      }
    }

    const area = svgEl("path", {
      d: data.trim(),
      fill: fillEnabled === true && complete === true ? color : "none",
      "fill-opacity": fillEnabled === true && complete === true ? AREA_OPACITY : null,
      stroke: color,
      "stroke-width": 2,
      "stroke-linejoin": "round",
      part: fillEnabled === true ? "radar-area" : "radar-outline",
      "data-series": name,
      tabindex: "0",
      role: "img",
      "aria-label": text
    }, [svgEl("title", null, text)])
    activate(area, () => {
      ctx.emit("mj-chart-radar-click", { series: name })
    })
    areas.appendChild(area)

    /* ... then every dot. */
    for (let i = 0; i < spokeCount; i = i + 1) {
      const point = points[i]
      if (point === null) {
        continue
      }
      const value = values[s][i]
      const dotText = `${name}, ${categories[i]}: ${formatNumber(value)}`
      const dot = svgEl("circle", {
        cx: point.x.toFixed(2), cy: point.y.toFixed(2), r: 4,
        fill: color,
        stroke: "var(--mj-surface, #fff)",
        "stroke-width": 1,
        part: "dot",
        tabindex: "0",
        role: "img",
        "aria-label": dotText
      }, [svgEl("title", null, dotText)])
      activate(dot, () => {
        ctx.emit("mj-chart-radar-dot-click", { series: name, category: categories[i], value: value })
      })
      markers.appendChild(dot)
    }
  }

  if (legend.height > 0) {
    legend.group.setAttribute("transform", `translate(12,${ctx.height - legendHeight + 4})`)
    root.appendChild(legend.group)
  }

  return root
}


registerRenderer("radar", render);
