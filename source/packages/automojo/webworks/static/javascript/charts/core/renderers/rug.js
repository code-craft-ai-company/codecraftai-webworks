/*
 * rug.js
 *
 * Rug plot renderer — tick marks along an axis showing raw observations.
 *
 * Registers: "rug"
 *
 * ctx.model.series data shape:
 *   series[]: { name, samples: [n, …] }
 *
 * Relevant ctx.attrs:
 *   tick-height   height of each tick in px (default 8)
 *   opacity       per-tick opacity (default 0.6; denser data gets lower default)
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { linearScale, niceTicks } from "../scales.js";


export function render(ctx) {
  /*
   * Render a rug plot.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const model = ctx.model
  const horizontal = ctx.orientation === "horizontal"
  const tickHeight = parseFloat(ctx.attrs("tick-height", "8")) || 8
  const opacityAttr = parseFloat(ctx.attrs("opacity", "0")) || 0

  const root = svgEl("g", { part: "plot" }, [])

  const series = model.series
  if (series === null || series === undefined || series.length === 0) {
    return root
  }

  /* Global value extent across all series. */
  let valMin = Infinity
  let valMax = -Infinity
  let totalPoints = 0
  for (let si = 0; si < series.length; si = si + 1) {
    const samples = series[si].samples || []
    totalPoints = totalPoints + samples.length
    for (let vi = 0; vi < samples.length; vi = vi + 1) {
      if (samples[vi] < valMin) { valMin = samples[vi] }
      if (samples[vi] > valMax) { valMax = samples[vi] }
    }
  }
  if (valMin === Infinity) {
    return root
  }
  const pad = (valMax - valMin) * 0.05 || 0.5
  valMin = valMin - pad
  valMax = valMax + pad

  /* Opacity: if not set by attr, auto-scale with density. */
  const autoOpacity = totalPoints > 200 ? 0.3 : totalPoints > 50 ? 0.5 : 0.7
  const tickOpacity = opacityAttr > 0 ? opacityAttr : autoOpacity

  /*
   * Layout: the rug occupies a strip along one edge. The value axis runs the
   * full width/height; the rug strip itself is thin (tickHeight + margins).
   * We provide a minimal axis with tick labels.
   */
  const margin = { top: 8, right: 16, bottom: 28, left: 48 }
  const rugAreaH = tickHeight + 4   /* strip height for per-series rows */
  const totalStripH = series.length * rugAreaH

  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const valScale = horizontal
    ? linearScale([valMin, valMax], [0, plotW])
    : linearScale([valMin, valMax], [plotH, 0])

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Value axis tick labels. */
  const ticks = niceTicks(valMin, valMax, 6)
  for (let ti = 0; ti < ticks.length; ti = ti + 1) {
    const tick = ticks[ti]
    if (horizontal === true) {
      const x = valScale(tick)
      plot.appendChild(svgEl("text", {
        x: x, y: plotH + 16, "text-anchor": "middle",
        "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
      }, formatNumber(tick)))
      /* Light gridlines */
      plot.appendChild(svgEl("line", {
        x1: x, y1: 0, x2: x, y2: plotH,
        stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
      }, []))
    } else {
      const y = valScale(tick)
      plot.appendChild(svgEl("text", {
        x: -8, y: y + 4, "text-anchor": "end",
        "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
      }, formatNumber(tick)))
      plot.appendChild(svgEl("line", {
        x1: 0, y1: y, x2: plotW, y2: y,
        stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
      }, []))
    }
  }

  /* Axis baseline. */
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

  /* Draw rug ticks — each series gets its own row offset so they don't overlap. */
  for (let si = 0; si < series.length; si = si + 1) {
    const s = series[si]
    const color = ctx.colorFor(si)
    const samples = s.samples || []

    /* Row offset: distribute series rows along the cross-axis. */
    const rowOffset = si * rugAreaH

    for (let vi = 0; vi < samples.length; vi = vi + 1) {
      const v = samples[vi]
      const px = valScale(v)

      let tick = null
      if (horizontal === true) {
        /* Tick runs vertically; value position is along x. */
        const y0 = plotH - rowOffset
        const y1 = y0 - tickHeight
        tick = svgEl("line", {
          x1: px, y1: y0, x2: px, y2: y1,
          stroke: color, "stroke-width": 1.5,
          opacity: tickOpacity
        }, [])
      } else {
        /* Tick runs horizontally; value position is along y. */
        const x0 = rowOffset
        const x1 = x0 + tickHeight
        tick = svgEl("line", {
          x1: x0, y1: px, x2: x1, y2: px,
          stroke: color, "stroke-width": 1.5,
          opacity: tickOpacity
        }, [])
      }

      tick.setAttribute("part", "rug-tick")
      tick.setAttribute("tabindex", "0")
      tick.setAttribute("role", "img")
      tick.setAttribute("aria-label", `${s.name}: ${formatNumber(v)}`)
      tick.appendChild(svgEl("title", null, `${s.name}: ${formatNumber(v)}`))
      const handlerValue = v
      const handlerSeries = s
      const clickHandler = () => {
        ctx.emit("mj-chart-rug-click", {
          series: handlerSeries.name, value: handlerValue
        })
      }
      tick.addEventListener("click", clickHandler)
      tick.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          clickHandler()
        }
      })
      plot.appendChild(tick)
    }

    /* Series label next to its row. */
    if (series.length > 1) {
      if (horizontal === true) {
        const labelY = plotH - rowOffset - tickHeight / 2 + 4
        plot.appendChild(svgEl("text", {
          x: -6, y: labelY, "text-anchor": "end",
          "font-size": 10, fill: ctx.colorFor(si)
        }, String(s.name)))
      } else {
        const labelX = rowOffset + tickHeight / 2
        plot.appendChild(svgEl("text", {
          x: labelX, y: -4, "text-anchor": "middle",
          "font-size": 10, fill: ctx.colorFor(si)
        }, String(s.name)))
      }
    }
  }

  return root
}


registerRenderer("rug", render)
