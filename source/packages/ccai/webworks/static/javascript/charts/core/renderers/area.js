/*
 * area.js
 *
 * Area / stacked-area / 100%-stacked-area renderer.
 *
 * Registered types:
 *   "area"         — single or multi-series filled area chart
 *   "stacked-area" — stacked area (also stack="stack" on type="area")
 *   "area100"      — 100% stacked area (also stack="stack100")
 *
 * ctx.attrs recognised:
 *   stack          "none" | "stack" | "stack100" (default from the type)
 *   curve          "linear" (default) | "monotone" | "step"
 *   fill-opacity   fill opacity of the areas (default 0.3)
 *   x-scale        see line.js
 *
 * Series data may use either:
 *   series[].points  [{x, y}, ...]
 *   series[].values  [...] aligned with model.categories
 *
 * X values follow the same time / linear / categorical rules as line.js. A
 * null value is a gap: the area is split around it (in the stacked modes
 * the layers above still stack on the ones below). An unstacked area fills
 * to y = 0, so all-negative data fills downward from zero. The stacked
 * modes stack positive values upward and negative values downward from
 * zero; stack100 shows each value's signed share of the absolute total at
 * that x. Each point has a focusable target that reads its value (and its
 * share in the stacked modes).
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { numericValue } from "./bar.js";
import {
  trendSeries, trendFrame, resolveXAxis, sortedPixels, curveMode, curvePath, bandPath,
  pointTargets, loneIndices
} from "./line.js";


function _stackMode(ctx) {
  /*
   * The stack mode from the type key and the `stack` attribute.
   */
  let fallback = "none"
  if (ctx.type === "stacked-area") {
    fallback = "stack"
  } else if (ctx.type === "area100") {
    fallback = "stack100"
  }
  const value = String(ctx.attrs("stack", fallback)).trim().toLowerCase()
  let mode = "none"
  if (value === "stack" || value === "stacked") {
    mode = "stack"
  } else if (value === "stack100") {
    mode = "stack100"
  }
  return mode
}


function _stackLayers(list, axis, mode) {
  /*
   * Stack the series over the shared x positions.
   *
   * :param axis: An x axis from resolveXAxis (only its keys are used).
   * :returns: [{ name, cells: [{ value, share, from, to, point } | null] }]
   *     -- cells are index-aligned with the sorted x keys; a missing or
   *     null value is null (a gap).
   */
  const keys = axis.keys
  const keyIndex = new Map()
  for (let index = 0; index < keys.length; index = index + 1) {
    keyIndex.set(keys[index].key, index)
  }

  /* values[s][k]: the series' value at key k, or null. */
  const values = list.map((series) => {
    const row = new Array(keys.length).fill(null)
    for (let p = 0; p < series.points.length; p = p + 1) {
      const point = series.points[p]
      const key = axis.keyOf(point)
      if (key === null || keyIndex.has(key) === false || point.y === null) {
        continue
      }
      row[keyIndex.get(key)] = { value: point.y, point: point }
    }
    return row
  })

  const totals = keys.map((entry, k) => {
    let sum = 0
    for (let s = 0; s < values.length; s = s + 1) {
      sum = sum + (values[s][k] !== null ? Math.abs(values[s][k].value) : 0)
    }
    return sum
  })

  const positive = new Array(keys.length).fill(0)
  const negative = new Array(keys.length).fill(0)
  const layers = []
  for (let s = 0; s < list.length; s = s + 1) {
    const cells = []
    for (let k = 0; k < keys.length; k = k + 1) {
      const entry = values[s][k]
      if (entry === null) {
        cells.push(null)
        continue
      }
      const share = totals[k] > 0 ? (entry.value / totals[k]) * 100 : 0
      const shown = mode === "stack100" ? share : entry.value
      let from = 0
      if (shown >= 0) {
        from = positive[k]
        positive[k] = positive[k] + shown
      } else {
        from = negative[k]
        negative[k] = negative[k] + shown
      }
      cells.push({ value: entry.value, share: share, from: from, to: from + shown, point: entry.point })
    }
    layers.push({ name: list[s].name, cells: cells })
  }
  return layers
}


export function render(ctx) {
  /*
   * Render an area chart (plain, stacked, or 100%-stacked).
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const root = svgEl("g", { part: "plot" }, [])

  const stackMode = _stackMode(ctx)
  const mode = curveMode(ctx, "linear")
  const opacity = numericValue(ctx.attrs("fill-opacity", "0.3"))
  const fillOpacity = opacity !== null ? Math.min(Math.max(opacity, 0), 1) : 0.3

  const list = trendSeries(model)
  let anyValue = false
  for (let s = 0; s < list.length && anyValue === false; s = s + 1) {
    anyValue = list[s].points.some((point) => point.y !== null)
  }
  if (anyValue === false) {
    return root
  }

  const stacked = stackMode !== "none"

  /*
   * The y domain needs the stacked sums, which need the shared x keys. The
   * keys (and their order) do not depend on the pixel range, so they are
   * read from a unit-range axis before the frame is laid out.
   */
  let yMin = 0
  let yMax = 0
  let layers = null
  if (stacked === true) {
    layers = _stackLayers(list, resolveXAxis(ctx, list, model, [0, 1], null), stackMode)
    for (let s = 0; s < layers.length; s = s + 1) {
      for (let k = 0; k < layers[s].cells.length; k = k + 1) {
        const cell = layers[s].cells[k]
        if (cell !== null) {
          yMin = Math.min(yMin, cell.from, cell.to)
          yMax = Math.max(yMax, cell.from, cell.to)
        }
      }
    }
    if (stackMode === "stack100") {
      yMin = yMin < 0 ? -100 : 0
      yMax = yMax > 0 || yMin === 0 ? 100 : 0
    }
  } else {
    for (let s = 0; s < list.length; s = s + 1) {
      for (let p = 0; p < list[s].points.length; p = p + 1) {
        const value = list[s].points[p].y
        if (value !== null) {
          yMin = Math.min(yMin, value)
          yMax = Math.max(yMax, value)
        }
      }
    }
  }
  if (yMin === yMax) {
    yMax = yMin + 1
  }

  const frame = trendFrame(ctx, list, model, {
    yDomain: [yMin, yMax],
    nice: stackMode !== "stack100",
    percent: stackMode === "stack100"
  })
  root.appendChild(frame.plot)
  const zero = frame.y(0)

  /* Zero line when the domain crosses zero. */
  if (yMin < 0) {
    frame.chrome.appendChild(svgEl("line", {
      x1: 0, y1: zero, x2: frame.plotW, y2: zero,
      stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
    }, []))
  }

  const areas = svgEl("g", { part: "areas" }, [])
  const strokes = svgEl("g", { part: "edges" }, [])
  const targetsGroup = svgEl("g", { part: "targets" }, [])
  frame.marks.appendChild(areas)
  frame.marks.appendChild(strokes)
  frame.marks.appendChild(targetsGroup)

  for (let s = 0; s < list.length; s = s + 1) {
    const name = list[s].name
    const color = ctx.colorFor(name)
    let top = []
    let bottom = zero
    const targets = []

    if (stacked === true) {
      const cells = layers[s].cells
      const keys = frame.x.keys
      top = cells.map((cell, k) => ({ x: keys[k].px, y: cell === null ? null : frame.y(cell.to) }))
      bottom = cells.map((cell, k) => ({ x: keys[k].px, y: cell === null ? null : frame.y(cell.from) }))
      for (let k = 0; k < cells.length; k = k + 1) {
        const cell = cells[k]
        if (cell === null) {
          continue
        }
        const xLabel = frame.x.labelOf(cell.point)
        const share = formatNumber(cell.share, { maximumFractionDigits: 1 })
        targets.push({
          x: keys[k].px, y: frame.y(cell.to),
          label: `${name}, ${xLabel}: ${formatNumber(cell.value)} (${share}%)`,
          detail: { series: name, x: cell.point.raw !== null ? cell.point.raw : xLabel, y: cell.value, share: cell.share }
        })
      }
    } else {
      const pixels = sortedPixels(list[s], frame)
      top = pixels.map((pixel) => ({ x: pixel.x, y: pixel.y }))
      for (let index = 0; index < pixels.length; index = index + 1) {
        const pixel = pixels[index]
        if (pixel.y === null) {
          continue
        }
        const xLabel = frame.x.labelOf(pixel.point)
        targets.push({
          x: pixel.x, y: pixel.y,
          label: `${name}, ${xLabel}: ${formatNumber(pixel.value)}`,
          detail: { series: name, x: pixel.point.raw !== null ? pixel.point.raw : xLabel, y: pixel.value }
        })
      }
    }

    const data = bandPath(top, bottom, mode)
    const area = svgEl("path", {
      d: data,
      fill: color,
      "fill-opacity": fillOpacity,
      stroke: "none",
      part: "area",
      "data-series": name
    }, [svgEl("title", null, name)])
    area.addEventListener("click", () => {
      ctx.emit("mj-chart-area-click", { series: name })
    })
    areas.appendChild(area)

    strokes.appendChild(svgEl("path", {
      d: curvePath(top, mode),
      fill: "none",
      stroke: color,
      "stroke-width": 1.5,
      "stroke-linejoin": "round",
      part: "area-line",
      "pointer-events": "none"
    }, []))

    /* A value with no neighbour has no area: mark it. */
    const lone = loneIndices(top)
    for (let index = 0; index < lone.length; index = index + 1) {
      strokes.appendChild(svgEl("circle", {
        cx: top[lone[index]].x.toFixed(2), cy: top[lone[index]].y.toFixed(2), r: 3,
        fill: color, part: "dot", "pointer-events": "none"
      }, []))
    }

    pointTargets(targetsGroup, targets, { ctx: ctx, eventName: "mj-chart-area-click", width: frame.plotW })
  }

  return root
}


registerRenderer("area", render)
registerRenderer("stacked-area", render)
registerRenderer("area100", render)
