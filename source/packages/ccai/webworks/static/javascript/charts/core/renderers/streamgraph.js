/*
 * streamgraph.js
 *
 * Streamgraph renderer — flowing symmetric stacked area.
 *
 * Registered types:
 *   "streamgraph" — streamgraph (wiggle/silhouette/zero baseline)
 *
 * ctx.attrs recognised:
 *   baseline   "wiggle" | "silhouette" | "zero" (default "wiggle")
 *              wiggle     — ThemeRiver / Byron & Wattenberg: the baseline
 *                           moves so the weighted slope of the streams is
 *                           as small as possible
 *              silhouette — centred stack (symmetric around y=0)
 *              zero       — bottom-aligned (equivalent to stacked area)
 *   curve      "monotone" (default) | "linear" | "step"
 *   x-scale    see line.js
 *
 * The y-axis is hidden because y positions are layout artefacts. Each
 * stream is labelled at its thickest point when it is tall enough; the
 * streams that cannot hold a label are listed in a key below the axis.
 * Every value has a focusable target reading the value and its share of
 * the total at that x. Values are stacked as given; a stream cannot be
 * negative, so a negative value is drawn as zero and mj-chart-error
 * reports it. A null value is a gap in that stream.
 *
 * Series data: series[].points [{x, y}] or series[].values [].
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { LABEL_FONT_SIZE, textWidth, truncateText, inlineLegend } from "./bar.js";
import {
  trendSeries, trendFrame, resolveXAxis, curveMode, bandPath, pointTargets
} from "./line.js";

const LABEL_MIN_THICKNESS = 14;


function _valueGrid(list, axis) {
  /*
   * values[s][k]: the value of series s at x key k (null when missing), with
   * negative values raised to zero.
   *
   * :returns: { values, points, negatives } -- points[s][k] is the data point.
   */
  const keyIndex = new Map()
  for (let index = 0; index < axis.keys.length; index = index + 1) {
    keyIndex.set(axis.keys[index].key, index)
  }
  let negatives = 0
  const values = []
  const points = []
  for (let s = 0; s < list.length; s = s + 1) {
    const row = new Array(axis.keys.length).fill(null)
    const pointRow = new Array(axis.keys.length).fill(null)
    for (let p = 0; p < list[s].points.length; p = p + 1) {
      const point = list[s].points[p]
      const key = axis.keyOf(point)
      if (key === null || keyIndex.has(key) === false || point.y === null) {
        continue
      }
      let value = point.y
      if (value < 0) {
        negatives = negatives + 1
        value = 0
      }
      row[keyIndex.get(key)] = value
      pointRow[keyIndex.get(key)] = point
    }
    values.push(row)
    points.push(pointRow)
  }
  return { values: values, points: points, negatives: negatives }
}


export function streamBaseline(values, baseline) {
  /*
   * The lower edge of the stack at every x.
   *
   * :param values: values[s][k] (null counts as 0).
   * :param baseline: "wiggle" | "silhouette" | "zero".
   * :returns: An array g[k] of the baseline at each x.
   */
  const n = values.length
  const m = n > 0 ? values[0].length : 0
  const at = (s, k) => {
    const value = values[s][k]
    return value === null || value === undefined ? 0 : value
  }
  const offsets = new Array(m).fill(0)

  if (baseline === "silhouette") {
    for (let k = 0; k < m; k = k + 1) {
      let total = 0
      for (let s = 0; s < n; s = s + 1) {
        total = total + at(s, k)
      }
      offsets[k] = -total / 2
    }
  } else if (baseline === "wiggle") {
    /*
     * Minimised weighted wiggle (Byron & Wattenberg 2008, as in d3's
     * stackOffsetWiggle): the baseline moves from x to x by
     *   -sum_i f_i * (f_i' / 2 + sum_{j<i} f_j') / sum_i f_i
     * where f' is the change of a stream since the previous x.
     */
    let level = 0
    for (let k = 1; k < m; k = k + 1) {
      let total = 0
      let weighted = 0
      for (let s = 0; s < n; s = s + 1) {
        const current = at(s, k)
        let below = 0
        for (let j = 0; j < s; j = j + 1) {
          below = below + (at(j, k) - at(j, k - 1))
        }
        const slope = (current - at(s, k - 1)) / 2 + below
        total = total + current
        weighted = weighted + slope * current
      }
      if (total > 0) {
        level = level - weighted / total
      }
      offsets[k] = level
    }
    /* Centre the stream on y = 0 (the y position itself carries no meaning). */
    let middle = 0
    for (let k = 0; k < m; k = k + 1) {
      let total = 0
      for (let s = 0; s < n; s = s + 1) {
        total = total + at(s, k)
      }
      middle = middle + offsets[k] + total / 2
    }
    middle = m > 0 ? middle / m : 0
    for (let k = 0; k < m; k = k + 1) {
      offsets[k] = offsets[k] - middle
    }
  }
  return offsets
}


export function render(ctx) {
  /*
   * Render a streamgraph.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const root = svgEl("g", { part: "plot" }, [])

  const list = trendSeries(model)
  if (list.length === 0) {
    return root
  }

  const baselineAttr = String(ctx.attrs("baseline", "wiggle")).trim().toLowerCase()
  const baselineMode = baselineAttr === "silhouette" || baselineAttr === "zero" ? baselineAttr : "wiggle"
  const mode = curveMode(ctx, "monotone")

  const grid = _valueGrid(list, resolveXAxis(ctx, list, model, [0, 1], null))
  if (grid.negatives > 0) {
    ctx.emit("mj-chart-error", {
      message: `streamgraph: ${grid.negatives} negative value(s) drawn as 0; a stream cannot be negative`
    })
  }
  const values = grid.values
  const offsets = streamBaseline(values, baselineMode)
  const keyCount = offsets.length
  if (keyCount === 0) {
    return root
  }

  /* y0 / y1 of every stream at every x. */
  const layers = []
  for (let k = 0; k < keyCount; k = k + 1) {
    let level = offsets[k]
    for (let s = 0; s < values.length; s = s + 1) {
      if (k === 0) {
        layers.push([])
      }
      const value = values[s][k]
      const size = value === null ? 0 : value
      layers[s].push({ y0: level, y1: level + size, value: value, point: grid.points[s][k] })
      level = level + size
    }
  }

  let yMin = Infinity
  let yMax = -Infinity
  for (let s = 0; s < layers.length; s = s + 1) {
    for (let k = 0; k < keyCount; k = k + 1) {
      yMin = Math.min(yMin, layers[s][k].y0)
      yMax = Math.max(yMax, layers[s][k].y1)
    }
  }
  if (yMax - yMin <= 0) {
    yMax = yMin + 1
  }
  const totals = []
  for (let k = 0; k < keyCount; k = k + 1) {
    let total = 0
    for (let s = 0; s < values.length; s = s + 1) {
      total = total + (values[s][k] === null ? 0 : values[s][k])
    }
    totals.push(total)
  }

  /*
   * Lay out twice when needed: first find which streams can hold a label,
   * then reserve room for a key of the others below the axis.
   */
  let legendHeight = 0
  let frame = null
  let unlabelled = []
  let placements = []
  for (let pass = 0; pass < 2; pass = pass + 1) {
    frame = trendFrame(ctx, list, model, {
      yDomain: [yMin, yMax], nice: false, showYAxis: false, bottomExtra: legendHeight
    })
    placements = []
    unlabelled = []
    for (let s = 0; s < layers.length; s = s + 1) {
      /* Prefer positions where the whole label fits inside the plot. */
      const half = textWidth(truncateText(list[s].name, frame.plotW * 0.4)) / 2 + 2
      const inside = (k) => frame.x.keys[k].px >= half && frame.x.keys[k].px <= frame.plotW - half
      const anyInside = frame.x.keys.some((key, k) => inside(k))
      let best = -1
      let bestThickness = 0
      for (let k = 0; k < keyCount; k = k + 1) {
        if (layers[s][k].value === null || (anyInside === true && inside(k) === false)) {
          continue
        }
        const thickness = Math.abs(frame.y(layers[s][k].y0) - frame.y(layers[s][k].y1))
        if (thickness > bestThickness) {
          bestThickness = thickness
          best = k
        }
      }
      if (best >= 0 && bestThickness >= LABEL_MIN_THICKNESS) {
        placements.push({ series: s, key: best })
      } else {
        unlabelled.push(s)
      }
    }
    /* A bound <mj-chart-legend> lists every series: no inline key then. */
    if (unlabelled.length === 0 || legendHeight > 0 || ctx.hasLegendPart === true) {
      break
    }
    const probe = inlineLegend(unlabelled.map((s) => ({ label: list[s].name, color: ctx.colorFor(list[s].name) })),
      0, 0, Math.max(ctx.width - 32, 40))
    legendHeight = probe.height + 6
  }
  root.appendChild(frame.plot)

  const streams = svgEl("g", { part: "streams" }, [])
  const labels = svgEl("g", { part: "labels", "aria-hidden": "true", "pointer-events": "none" }, [])
  const targetsGroup = svgEl("g", { part: "targets" }, [])
  frame.marks.appendChild(streams)
  frame.marks.appendChild(labels)
  frame.marks.appendChild(targetsGroup)

  for (let s = 0; s < layers.length; s = s + 1) {
    const name = list[s].name
    const color = ctx.colorFor(name)
    const top = []
    const bottom = []
    const targets = []
    for (let k = 0; k < keyCount; k = k + 1) {
      const cell = layers[s][k]
      const px = frame.x.keys[k].px
      top.push({ x: px, y: cell.value === null ? null : frame.y(cell.y1) })
      bottom.push({ x: px, y: cell.value === null ? null : frame.y(cell.y0) })
      if (cell.value !== null && cell.point !== null) {
        const xLabel = frame.x.labelOf(cell.point)
        const share = totals[k] > 0 ? (cell.value / totals[k]) * 100 : 0
        const shareText = formatNumber(share, { maximumFractionDigits: 1 })
        targets.push({
          x: px, y: frame.y((cell.y0 + cell.y1) / 2),
          label: `${name}, ${xLabel}: ${formatNumber(cell.point.y)} (${shareText}% of total)`,
          detail: { series: name, x: cell.point.raw !== null ? cell.point.raw : xLabel, y: cell.point.y, share: share }
        })
      }
    }

    const data = bandPath(top, bottom, mode)
    if (data !== "") {
      const stream = svgEl("path", {
        d: data,
        fill: color,
        "fill-opacity": "0.85",
        stroke: "var(--mj-surface, #fff)",
        "stroke-width": 0.5,
        part: "stream",
        "data-series": name
      }, [svgEl("title", null, name)])
      stream.addEventListener("click", () => {
        ctx.emit("mj-chart-stream-click", { series: name })
      })
      streams.appendChild(stream)
    }
    pointTargets(targetsGroup, targets, { ctx: ctx, eventName: "mj-chart-stream-click", width: frame.plotW, radius: 5 })
  }

  /* Labels at each stream's thickest point, with a halo for contrast. */
  for (let index = 0; index < placements.length; index = index + 1) {
    const placement = placements[index]
    const cell = layers[placement.series][placement.key]
    const name = list[placement.series].name
    const text = truncateText(name, frame.plotW * 0.4)
    const half = textWidth(text) / 2
    const px = Math.min(Math.max(frame.x.keys[placement.key].px, half + 2), frame.plotW - half - 2)
    labels.appendChild(svgEl("text", {
      x: px.toFixed(2), y: (frame.y((cell.y0 + cell.y1) / 2) + 4).toFixed(2),
      "text-anchor": "middle",
      "font-size": LABEL_FONT_SIZE,
      fill: "var(--mj-text, #14181f)",
      stroke: "var(--mj-surface, #ffffff)",
      "stroke-width": 3,
      "stroke-opacity": 0.85,
      "stroke-linejoin": "round",
      "paint-order": "stroke"
    }, text))
  }

  /* Key for the streams too thin to label. */
  if (unlabelled.length > 0 && ctx.hasLegendPart !== true) {
    const key = inlineLegend(unlabelled.map((s) => ({ label: list[s].name, color: ctx.colorFor(list[s].name) })),
      0, frame.plotH + 24, Math.max(ctx.width - frame.margin.left - 16, 40))
    frame.plot.appendChild(key.group)
  }

  return root
}


registerRenderer("streamgraph", render)
