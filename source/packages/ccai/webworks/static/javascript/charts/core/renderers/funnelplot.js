/*
 * funnelplot.js
 *
 * Funnel plot renderer — publication-bias / small-study-effects scatter
 * with funnel boundary overlay.
 *
 * Registers: "funnel-plot"
 *
 * JSON shape (ctx.raw):
 *   series: [{ name, points: [{ x, y, label? }] }]
 *   funnel?: {
 *     summary_effect: number,
 *     pseudo_ci?: [{ se, lower, upper }]
 *   }
 *
 *   x     — study effect estimate
 *   y     — standard error; the y-axis is INVERTED (SE 0, the most
 *           precise, at the top)
 *   label — optional study label
 *
 *   funnel.summary_effect  — pooled effect: the vertical reference line,
 *                            drawn whenever it is a number
 *   funnel.pseudo_ci       — funnel bounds at each SE level; when it is
 *                            missing the 95% funnel summary +/- 1.96 x SE
 *                            is drawn from the summary effect
 *
 * Options:
 *   contours         contour-enhanced funnel: shades where a study would be
 *                    significant against the null effect (`null-value`,
 *                    default 0) at p < 0.05 and p < 0.01
 *   null-value       the null effect of the contours (0 for differences
 *                    and log ratios)
 *   labels           study labels (placed right of the point, flipped left
 *                    near the right edge, nudged or dropped on overlap)
 *
 * Events:
 *   mj-chart-study-click { series, x, y, label }
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { linearScale, niceDomain, niceTicks } from "../scales.js";
import { booleanOption } from "../chartoptions.js";


const Z_95 = 1.959964;
const Z_99 = 2.575829;
const LABEL_FONT = 9;
const CHAR_WIDTH = 0.56;

const CONTOUR_BANDS = [
  { label: "p < 0.01", color: "var(--mj-bg-muted, #eef0f3)" },
  { label: "0.01 ≤ p < 0.05", color: "var(--mj-bg-subtle, #f8f9fb)" }
];


function _number(value) {
  /*
   * A finite number from a number or numeric string, else null.
   */
  if (value === null || value === undefined || value === "" || typeof value === "boolean") {
    return null
  }
  const numeric = Number(value)
  const result = Number.isFinite(numeric) === true ? numeric : null
  return result
}


function _funnelBounds(funnel, summary, seMax) {
  /*
   * The funnel bounds to draw: the data's pseudo_ci sorted by SE, else the
   * 95% funnel around the summary effect.
   *
   * :returns: [{ se, lower, upper }] (possibly empty).
   */
  const bounds = []
  if (funnel !== null && Array.isArray(funnel.pseudo_ci) === true) {
    for (let index = 0; index < funnel.pseudo_ci.length; index = index + 1) {
      const entry = funnel.pseudo_ci[index]
      if (entry === null || typeof entry !== "object") {
        continue
      }
      const se = _number(entry.se)
      const lower = _number(entry.lower)
      const upper = _number(entry.upper)
      if (se !== null && lower !== null && upper !== null) {
        bounds.push({ se: se, lower: lower, upper: upper })
      }
    }
    bounds.sort((a, b) => a.se - b.se)
  }
  if (bounds.length < 2 && summary !== null) {
    bounds.length = 0
    bounds.push({ se: 0, lower: summary, upper: summary })
    bounds.push({ se: seMax, lower: summary - Z_95 * seMax, upper: summary + Z_95 * seMax })
  }
  return bounds
}


export function render(ctx) {
  /*
   * Render a funnel plot.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const showContours = booleanOption(ctx, "contours", false)
  const showLabels = booleanOption(ctx, "labels", false)
  const nullAttr = _number(ctx.attrs("null-value", null))
  const nullValue = nullAttr !== null ? nullAttr : 0

  const root = svgEl("g", { part: "plot" }, [])

  const funnel = raw.funnel !== null && typeof raw.funnel === "object" ? raw.funnel : null
  const summary = funnel !== null ? _number(funnel.summary_effect) : null

  /* Studies. */
  const series = []
  const rawSeries = Array.isArray(raw.series) === true ? raw.series : []
  for (let s = 0; s < rawSeries.length; s = s + 1) {
    const entry = rawSeries[s]
    if (entry === null || typeof entry !== "object") {
      continue
    }
    const points = []
    const source = Array.isArray(entry.points) === true ? entry.points : []
    for (let p = 0; p < source.length; p = p + 1) {
      const point = source[p]
      if (point === null || typeof point !== "object") {
        continue
      }
      const x = _number(point.x)
      const y = _number(point.y)
      if (x === null || y === null || y < 0) {
        continue
      }
      points.push({ source: point, x: x, y: y,
        label: point.label !== undefined && point.label !== null ? String(point.label) : "" })
    }
    series.push({ name: entry.name !== undefined ? String(entry.name) : `Series ${s + 1}`, points: points })
  }

  ctx.setTable({
    columns: ["Study", "Series", "Effect", "Standard error"],
    rows: [].concat(...series.map((entry) => entry.points.map((point) => [
      point.label, entry.name, point.x, point.y
    ])))
  })
  const legend = series.length > 1 ? series.map((entry) => ({ label: entry.name, series: entry.name })) : []
  if (showContours === true) {
    for (let b = 0; b < CONTOUR_BANDS.length; b = b + 1) {
      legend.push({ label: CONTOUR_BANDS[b].label, color: CONTOUR_BANDS[b].color })
    }
  }
  ctx.setLegend(legend)

  /* Domains. */
  let xMin = Infinity
  let xMax = -Infinity
  let seMax = 0
  for (let s = 0; s < series.length; s = s + 1) {
    for (let p = 0; p < series[s].points.length; p = p + 1) {
      const point = series[s].points[p]
      xMin = Math.min(xMin, point.x)
      xMax = Math.max(xMax, point.x)
      seMax = Math.max(seMax, point.y)
    }
  }
  if (xMin === Infinity && summary === null) {
    return root
  }
  if (funnel !== null && Array.isArray(funnel.pseudo_ci) === true) {
    for (let c = 0; c < funnel.pseudo_ci.length; c = c + 1) {
      const se = funnel.pseudo_ci[c] !== null && typeof funnel.pseudo_ci[c] === "object"
        ? _number(funnel.pseudo_ci[c].se) : null
      if (se !== null) {
        seMax = Math.max(seMax, se)
      }
    }
  }
  if (seMax <= 0) {
    seMax = 1
  }
  const bounds = _funnelBounds(funnel, summary, seMax)
  for (let b = 0; b < bounds.length; b = b + 1) {
    xMin = Math.min(xMin, bounds[b].lower)
    xMax = Math.max(xMax, bounds[b].upper)
  }
  if (summary !== null) {
    xMin = Math.min(xMin, summary)
    xMax = Math.max(xMax, summary)
  }
  if (xMin === xMax) {
    xMin = xMin - 1
    xMax = xMax + 1
  }
  const xPad = (xMax - xMin) * 0.05
  const xDomain = niceDomain(xMin - xPad, xMax + xPad, 5)
  const yDomain = niceDomain(0, seMax, 5)

  const margin = { top: 16, right: 16, bottom: 44, left: 60 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  /* y is inverted: SE 0 at the top. */
  const xScale = linearScale(xDomain, [0, plotW])
  const yScale = linearScale(yDomain, [0, plotH])

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)
  const clipId = "mj-funnel-plot-clip"
  plot.appendChild(svgEl("clipPath", { id: clipId }, [
    svgEl("rect", { x: 0, y: 0, width: plotW, height: plotH }, [])
  ]))
  const shading = svgEl("g", { "aria-hidden": "true", "clip-path": `url(#${clipId})` }, [])
  const axis = svgEl("g", { "aria-hidden": "true" }, [])
  const overlay = svgEl("g", { "aria-hidden": "true", "clip-path": `url(#${clipId})` }, [])
  const marks = svgEl("g", null, [])
  const labels = svgEl("g", { "aria-hidden": "true" }, [])
  plot.appendChild(shading)
  plot.appendChild(axis)
  plot.appendChild(overlay)
  plot.appendChild(marks)
  plot.appendChild(labels)

  /* Contour-enhanced shading around the null effect. */
  if (showContours === true) {
    const seBottom = yDomain[1]
    const wedge = (z) => {
      const points = `${xScale(nullValue)},${yScale(0)} ` +
        `${xScale(nullValue + z * seBottom)},${yScale(seBottom)} ` +
        `${xScale(nullValue - z * seBottom)},${yScale(seBottom)}`
      return points
    }
    shading.appendChild(svgEl("rect", {
      x: 0, y: 0, width: plotW, height: plotH, fill: CONTOUR_BANDS[0].color
    }, []))
    shading.appendChild(svgEl("polygon", { points: wedge(Z_99), fill: CONTOUR_BANDS[1].color }, []))
    shading.appendChild(svgEl("polygon", { points: wedge(Z_95), fill: "var(--mj-surface, #ffffff)" }, []))
  }

  const yTicks = niceTicks(yDomain[0], yDomain[1], 5)
  for (let t = 0; t < yTicks.length; t = t + 1) {
    const y = yScale(yTicks[t])
    axis.appendChild(svgEl("line", {
      x1: 0, y1: y, x2: plotW, y2: y,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    axis.appendChild(svgEl("text", {
      x: -8, y: y + 4, "text-anchor": "end",
      "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(yTicks[t])))
  }
  const xTicks = niceTicks(xDomain[0], xDomain[1], Math.max(4, Math.floor(plotW / 80)))
  for (let t = 0; t < xTicks.length; t = t + 1) {
    const x = xScale(xTicks[t])
    axis.appendChild(svgEl("line", {
      x1: x, y1: 0, x2: x, y2: plotH,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    axis.appendChild(svgEl("text", {
      x: x, y: plotH + 16, "text-anchor": "middle",
      "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(xTicks[t])))
  }
  axis.appendChild(svgEl("text", {
    x: plotW / 2, y: plotH + 34, "text-anchor": "middle",
    "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
  }, "Effect estimate"))
  axis.appendChild(svgEl("text", {
    transform: `translate(-44,${plotH / 2}) rotate(-90)`,
    "text-anchor": "middle",
    "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
  }, "Standard error"))

  /* Funnel boundaries and the summary effect. */
  if (bounds.length >= 2) {
    const edge = (key) => {
      let d = ""
      for (let b = 0; b < bounds.length; b = b + 1) {
        d = d + `${b === 0 ? "M" : " L"}${xScale(bounds[b][key]).toFixed(2)},${yScale(bounds[b].se).toFixed(2)}`
      }
      return d
    }
    overlay.appendChild(svgEl("path", {
      d: edge("lower"), fill: "none",
      stroke: "var(--mj-text-muted, #6b7280)", "stroke-width": 1.25, "stroke-dasharray": "5 3"
    }, []))
    overlay.appendChild(svgEl("path", {
      d: edge("upper"), fill: "none",
      stroke: "var(--mj-text-muted, #6b7280)", "stroke-width": 1.25, "stroke-dasharray": "5 3"
    }, []))
  }
  if (summary !== null) {
    const xSummary = xScale(summary)
    overlay.appendChild(svgEl("line", {
      x1: xSummary, y1: 0, x2: xSummary, y2: plotH,
      stroke: "var(--mj-text, #14181f)", "stroke-width": 1.5
    }, []))
  }

  /* Studies; labels avoid each other and the right edge. */
  const placed = []
  const overlaps = (box) => {
    for (let k = 0; k < placed.length; k = k + 1) {
      const other = placed[k]
      if (box.x1 < other.x2 && box.x2 > other.x1 && box.y1 < other.y2 && box.y2 > other.y1) {
        return true
      }
    }
    return false
  }
  /* Every point is an obstacle for every label. */
  for (let s = 0; s < series.length; s = s + 1) {
    for (let p = 0; p < series[s].points.length; p = p + 1) {
      const px = xScale(series[s].points[p].x)
      const py = yScale(series[s].points[p].y)
      placed.push({ x1: px - 5, x2: px + 5, y1: py - 5, y2: py + 5 })
    }
  }
  for (let s = 0; s < series.length; s = s + 1) {
    const entry = series[s]
    const color = ctx.colorFor(entry.name)
    for (let p = 0; p < entry.points.length; p = p + 1) {
      const point = entry.points[p]
      const px = xScale(point.x)
      const py = yScale(point.y)
      const ariaLabel = (point.label !== "" ? `${point.label}: ` : "") +
        `effect ${formatNumber(point.x)}, SE ${formatNumber(point.y)}`

      const circle = svgEl("circle", {
        cx: px, cy: py, r: 4.5, fill: color,
        stroke: "var(--mj-surface, #ffffff)", "stroke-width": 1,
        part: "study", tabindex: "0", role: "img", "aria-label": ariaLabel
      }, [])
      circle.appendChild(svgEl("title", null, ariaLabel))
      const emitPoint = point
      const handler = () => {
        ctx.emit("mj-chart-study-click", {
          series: entry.name, x: emitPoint.x, y: emitPoint.y, label: emitPoint.source.label
        })
      }
      circle.addEventListener("click", handler)
      circle.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })
      marks.appendChild(circle)

      if (showLabels === true && point.label !== "") {
        const width = point.label.length * LABEL_FONT * CHAR_WIDTH
        const candidates = [
          { x: px + 7, anchor: "start", dy: 0 },
          { x: px - 7, anchor: "end", dy: 0 },
          { x: px + 7, anchor: "start", dy: -10 },
          { x: px + 7, anchor: "start", dy: 10 },
          { x: px - 7, anchor: "end", dy: -10 },
          { x: px - 7, anchor: "end", dy: 10 }
        ]
        for (let c = 0; c < candidates.length; c = c + 1) {
          const candidate = candidates[c]
          const x1 = candidate.anchor === "start" ? candidate.x : candidate.x - width
          const box = { x1: x1, x2: x1 + width, y1: py + candidate.dy - 6, y2: py + candidate.dy + 4 }
          if (box.x1 < -margin.left + 2 || box.x2 > plotW + margin.right - 2 || overlaps(box) === true) {
            continue
          }
          placed.push(box)
          labels.appendChild(svgEl("text", {
            x: candidate.x, y: py + candidate.dy + 3, "text-anchor": candidate.anchor,
            "font-size": LABEL_FONT, fill: "var(--mj-text-muted, #6b7280)"
          }, point.label))
          break
        }
      }
    }
  }

  axis.appendChild(svgEl("line", {
    x1: 0, y1: plotH, x2: plotW, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))
  axis.appendChild(svgEl("line", {
    x1: 0, y1: 0, x2: 0, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))

  return root
}


registerRenderer("funnel-plot", render)
