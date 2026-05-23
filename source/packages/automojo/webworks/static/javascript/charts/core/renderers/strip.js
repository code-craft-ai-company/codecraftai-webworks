/*
 * strip.js
 *
 * Strip plot and swarm plot renderer.
 *
 * Registers: "strip", "swarm"
 *
 * ctx.model.series data shape:
 *   series[].groups[]: { category, samples: [n, …] }
 *
 * Relevant ctx.attrs:
 *   jitter   "random" (default) | "none" | "swarm"
 *            "swarm" is also the default when the "swarm" type key is used.
 *   r        point radius in px (default 4)
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { linearScale, bandScale, niceTicks } from "../scales.js";


/* ── jitter helpers ──────────────────────────────────────────────────────── */

function _deterministicSeed(value, index) {
  /*
   * Deterministic pseudo-random jitter offset in [−1, 1] derived from
   * the sample value and its index — stable across re-renders.
   */
  const raw = Math.sin(value * 9301 + index * 49297 + 233) * 0.5 + 0.5
  return raw * 2 - 1
}


function _swarmPlace(samples, valScale, halfBand, r) {
  /*
   * Greedy beeswarm placement.
   * Sorts points by value, then places each at the first perpendicular
   * offset that does not collide with already-placed points.
   *
   * :param samples: Raw numeric samples.
   * :param valScale: Continuous scale for the value axis.
   * :param halfBand: Half the available band width (maximum jitter).
   * :param r: Circle radius.
   * :returns: Array of { value, offset } parallel to sorted order.
   */
  const diameter = r * 2 + 1

  /* Work in pixel space along the value axis. */
  const pts = samples.map((v, i) => ({ value: v, px: valScale(v), offset: 0 }))
  pts.sort((a, b) => a.px - b.px)

  const placed = []  /* { px, offset } */

  for (let i = 0; i < pts.length; i = i + 1) {
    const pt = pts[i]
    /* Collect candidates that could overlap on the value axis. */
    const nearby = placed.filter((p) => Math.abs(p.px - pt.px) < diameter)

    /* Try offsets starting from 0, ±1 diameter, ±2 diameter … */
    let bestOffset = 0
    let found = false
    for (let step = 0; step <= Math.ceil(halfBand / diameter) && found === false; step = step + 1) {
      const candidates = step === 0 ? [0] : [step * diameter, -step * diameter]
      for (let ci = 0; ci < candidates.length && found === false; ci = ci + 1) {
        const offset = candidates[ci]
        if (Math.abs(offset) > halfBand) { continue }
        const collision = nearby.some((p) => {
          const dx = pt.px - p.px
          const dy = offset - p.offset
          return Math.sqrt(dx * dx + dy * dy) < diameter
        })
        if (collision === false) {
          bestOffset = offset
          found = true
        }
      }
    }
    pt.offset = bestOffset
    placed.push({ px: pt.px, offset: bestOffset })
  }

  /* Map back to original sample order. */
  const result = samples.map((v) => {
    const match = pts.find((p) => p.value === v)
    return { value: v, offset: match ? match.offset : 0 }
  })
  return result
}


/* ── main render ─────────────────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Render a strip plot or swarm plot.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const model = ctx.model
  const horizontal = ctx.orientation === "horizontal"

  /* "swarm" type key implies jitter="swarm"; attr overrides. */
  const typeIsSwarm = false  /* determined at registration time via wrapper */
  const defaultJitter = ctx.attrs("_swarm_default", "random")
  const jitter = ctx.attrs("jitter", defaultJitter)
  const r = parseFloat(ctx.attrs("r", "4")) || 4

  const root = svgEl("g", { part: "plot" }, [])

  const series = model.series
  const categories = model.categories
  if (series === null || series === undefined || series.length === 0) {
    return root
  }
  if (categories === null || categories === undefined || categories.length === 0) {
    return root
  }

  /* Global value extent. */
  let valMin = Infinity
  let valMax = -Infinity
  for (let si = 0; si < series.length; si = si + 1) {
    const groups = series[si].groups || []
    for (let gi = 0; gi < groups.length; gi = gi + 1) {
      const samples = groups[gi].samples || []
      for (let vi = 0; vi < samples.length; vi = vi + 1) {
        if (samples[vi] < valMin) { valMin = samples[vi] }
        if (samples[vi] > valMax) { valMax = samples[vi] }
      }
    }
  }
  if (valMin === Infinity) {
    return root
  }
  const pad = (valMax - valMin) * 0.1 || 1
  valMin = valMin - pad
  valMax = valMax + pad

  const margin = { top: 16, right: 16, bottom: 40, left: 52 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const cat = bandScale(categories, [0, horizontal ? plotH : plotW], 0.2)
  const val = horizontal
    ? linearScale([valMin, valMax], [0, plotW])
    : linearScale([valMin, valMax], [plotH, 0])

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Value gridlines + tick labels. */
  const ticks = niceTicks(valMin, valMax, 5)
  for (let ti = 0; ti < ticks.length; ti = ti + 1) {
    const tick = ticks[ti]
    if (horizontal === true) {
      const x = val(tick)
      plot.appendChild(svgEl("line", {
        x1: x, y1: 0, x2: x, y2: plotH,
        stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
      }, []))
      plot.appendChild(svgEl("text", {
        x: x, y: plotH + 16, "text-anchor": "middle",
        "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
      }, formatNumber(tick)))
    } else {
      const y = val(tick)
      plot.appendChild(svgEl("line", {
        x1: 0, y1: y, x2: plotW, y2: y,
        stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
      }, []))
      plot.appendChild(svgEl("text", {
        x: -8, y: y + 4, "text-anchor": "end",
        "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
      }, formatNumber(tick)))
    }
  }

  /* Category labels. */
  for (let ci = 0; ci < categories.length; ci = ci + 1) {
    const category = categories[ci]
    const bandCenter = cat(category) + cat.bandwidth() / 2
    if (horizontal === true) {
      plot.appendChild(svgEl("text", {
        x: -8, y: bandCenter + 4, "text-anchor": "end",
        "font-size": 11, fill: "var(--mj-text, #14181f)"
      }, String(category)))
    } else {
      plot.appendChild(svgEl("text", {
        x: bandCenter, y: plotH + 18, "text-anchor": "middle",
        "font-size": 11, fill: "var(--mj-text, #14181f)"
      }, String(category)))
    }
  }

  const bandwidth = cat.bandwidth()
  const halfBand = bandwidth / 2

  for (let si = 0; si < series.length; si = si + 1) {
    const s = series[si]
    const color = ctx.colorFor(si)
    const groups = s.groups || []
    const clusterWidth = series.length > 1 ? bandwidth / series.length : bandwidth
    const clusterHalfBand = clusterWidth / 2 * 0.8

    for (let gi = 0; gi < groups.length; gi = gi + 1) {
      const group = groups[gi]
      const samples = group.samples || []
      if (samples.length === 0) { continue }

      const bandStart = cat(group.category)
      const clusterOffset = series.length > 1 ? si * clusterWidth : 0
      const bandCenter = bandStart + clusterOffset + clusterWidth / 2

      /* Compute per-point positions. */
      const useSwarm = jitter === "swarm"
      let placedPoints = null

      if (useSwarm === true) {
        placedPoints = _swarmPlace(samples, val, clusterHalfBand, r)
      } else {
        placedPoints = samples.map((v, pi) => {
          const offset = jitter === "none" ? 0 : _deterministicSeed(v, pi) * clusterHalfBand
          return { value: v, offset: offset }
        })
      }

      for (let pi = 0; pi < placedPoints.length; pi = pi + 1) {
        const { value, offset } = placedPoints[pi]
        const cx = horizontal ? val(value) : bandCenter + offset
        const cy = horizontal ? bandCenter + offset : val(value)

        const dot = svgEl("circle", {
          cx: cx, cy: cy, r: r,
          fill: color, opacity: 0.75
        }, [])
        dot.setAttribute("part", "point")
        dot.setAttribute("tabindex", "0")
        dot.setAttribute("role", "img")
        dot.setAttribute("aria-label",
          `${s.name}, ${group.category}: ${formatNumber(value)}`)
        dot.appendChild(svgEl("title", null,
          `${s.name} — ${group.category}: ${formatNumber(value)}`))
        const handlerValue = value
        const handlerGroup = group
        const handlerSeries = s
        const clickHandler = () => {
          ctx.emit("mj-chart-point-click", {
            series: handlerSeries.name,
            category: handlerGroup.category,
            value: handlerValue
          })
        }
        dot.addEventListener("click", clickHandler)
        dot.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault()
            clickHandler()
          }
        })
        plot.appendChild(dot)
      }
    }
  }

  return root
}


function _renderSwarm(ctx) {
  /*
   * Wrapper that forces jitter="swarm" as default for the "swarm" type key.
   * Passes a sentinel attr so the shared render() picks up the right default.
   */
  const origAttrs = ctx.attrs
  const wrappedCtx = Object.assign({}, ctx, {
    attrs: (name, fallback) => {
      if (name === "_swarm_default") { return "swarm" }
      return origAttrs(name, fallback)
    }
  })
  return render(wrappedCtx)
}


registerRenderer("strip", render)
registerRenderer("swarm", _renderSwarm)
