/*
 * step.js
 *
 * Step / staircase renderer.
 *
 * Registered types:
 *   "step" — step-line chart
 *
 * ctx.attrs recognised:
 *   step-position   "before" | "after" | "middle" (default "after")
 *                   Where the vertical jump sits relative to each x:
 *                   after  -- a value holds from its x until the next x
 *                   before -- a value holds from the previous x up to its x
 *                   middle -- the jump is half-way between two x values
 *   fill            boolean (default false) — fill the area down to zero
 *   show-points     boolean (default true) — change-point markers
 *   x-scale         see line.js
 *
 * Series data may use either:
 *   series[].points  [{x, y}, ...]
 *   series[].values  [...] aligned with model.categories
 *
 * Dates use a time scale (line.js rules), so a tread's length is the time
 * the level lasted. In "after" mode the axis runs one typical interval past
 * the last x so the final level has a tread of its own. A null value is
 * a gap: the previous level stops at the null's x and the line restarts at
 * the next value. The value axis always includes zero.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { booleanOption } from "../chartoptions.js";
import { trendSeries, trendFrame, sortedPixels, pointTargets } from "./line.js";


function _stepRuns(pixels, stepPosition, endX) {
  /*
   * The polylines of a step series, one per run of known values.
   *
   * :param pixels: [{x, y}] in x order; y null marks a gap.
   * :param stepPosition: "before" | "after" | "middle".
   * :param endX: The px where the last level of the series ends ("after").
   * :returns: An array of runs, each an array of {x, y} vertices.
   */
  const runs = []
  let current = null

  for (let index = 0; index < pixels.length; index = index + 1) {
    const point = pixels[index]
    if (point.y === null) {
      if (current !== null && stepPosition === "after") {
        /* The level holds until the x where the value goes missing. */
        const last = current[current.length - 1]
        current.push({ x: point.x, y: last.y })
      }
      current = null
      continue
    }
    if (current === null) {
      current = [{ x: point.x, y: point.y }]
      runs.push(current)
      continue
    }
    const previous = current[current.length - 1]
    if (stepPosition === "before") {
      current.push({ x: previous.x, y: point.y })
      current.push({ x: point.x, y: point.y })
    } else if (stepPosition === "middle") {
      const middle = (previous.x + point.x) / 2
      current.push({ x: middle, y: previous.y })
      current.push({ x: middle, y: point.y })
      current.push({ x: point.x, y: point.y })
    } else {
      current.push({ x: point.x, y: previous.y })
      current.push({ x: point.x, y: point.y })
    }
  }

  if (current !== null && stepPosition === "after") {
    const last = current[current.length - 1]
    if (endX > last.x) {
      current.push({ x: endX, y: last.y })
    }
  }
  return runs
}


function _runPath(run, closeTo) {
  /*
   * Path data of one run; closed down to `closeTo` (px) when it is a number.
   */
  let data = ""
  for (let index = 0; index < run.length; index = index + 1) {
    const command = index === 0 ? "M" : "L"
    data = data + `${command}${run[index].x.toFixed(2)},${run[index].y.toFixed(2)} `
  }
  if (typeof closeTo === "number") {
    const first = run[0]
    const last = run[run.length - 1]
    data = data + `L${last.x.toFixed(2)},${closeTo.toFixed(2)} L${first.x.toFixed(2)},${closeTo.toFixed(2)} Z`
  }
  return data.trim()
}


export function render(ctx) {
  /*
   * Render a step chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const root = svgEl("g", { part: "plot" }, [])

  const positionAttr = String(ctx.attrs("step-position", "after")).trim().toLowerCase()
  const stepPosition = positionAttr === "before" || positionAttr === "middle" ? positionAttr : "after"
  const fillArea = booleanOption(ctx, "fill", false)
  const showPoints = booleanOption(ctx, "show-points", true)

  const list = trendSeries(model)
  let yMin = 0
  let yMax = 0
  let anyValue = false
  for (let s = 0; s < list.length; s = s + 1) {
    for (let p = 0; p < list[s].points.length; p = p + 1) {
      const value = list[s].points[p].y
      if (value !== null) {
        anyValue = true
        yMin = Math.min(yMin, value)
        yMax = Math.max(yMax, value)
      }
    }
  }
  if (anyValue === false) {
    return root
  }
  if (yMin === yMax) {
    yMax = yMin + 1
  }

  const frame = trendFrame(ctx, list, model, {
    yDomain: [yMin, yMax],
    extendEnd: stepPosition === "after"
  })
  root.appendChild(frame.plot)
  const baseline = frame.y(0)

  if (yMin < 0) {
    frame.chrome.appendChild(svgEl("line", {
      x1: 0, y1: baseline, x2: frame.plotW, y2: baseline,
      stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
    }, []))
  }

  for (let s = 0; s < list.length; s = s + 1) {
    const series = list[s]
    const color = ctx.colorFor(series.name)
    const group = svgEl("g", { part: "series", "data-series": series.name }, [])
    const pixels = sortedPixels(series, frame)
    const runs = _stepRuns(pixels, stepPosition, frame.x.end)

    for (let r = 0; r < runs.length; r = r + 1) {
      if (fillArea === true) {
        group.appendChild(svgEl("path", {
          d: _runPath(runs[r], baseline),
          fill: color, "fill-opacity": 0.25, stroke: "none", part: "step-fill"
        }, []))
      }
      group.appendChild(svgEl("path", {
        d: _runPath(runs[r], null),
        fill: "none",
        stroke: color,
        "stroke-width": 2,
        "stroke-linejoin": "miter",
        part: "step-line"
      }, []))
    }

    const targets = []
    for (let index = 0; index < pixels.length; index = index + 1) {
      const pixel = pixels[index]
      if (pixel.y === null) {
        continue
      }
      if (showPoints === true) {
        group.appendChild(svgEl("circle", {
          cx: pixel.x.toFixed(2), cy: pixel.y.toFixed(2), r: 3,
          fill: color,
          stroke: "var(--mj-surface, #fff)",
          "stroke-width": 1.5,
          part: "dot"
        }, []))
      }
      const xLabel = frame.x.labelOf(pixel.point)
      targets.push({
        x: pixel.x, y: pixel.y,
        label: `${series.name}, ${xLabel}: ${formatNumber(pixel.value)}`,
        detail: { series: series.name, x: pixel.point.raw !== null ? pixel.point.raw : xLabel, y: pixel.value }
      })
    }
    pointTargets(group, targets, { ctx: ctx, eventName: "mj-chart-step-click", width: frame.plotW })

    frame.marks.appendChild(group)
  }

  return root
}


registerRenderer("step", render)
