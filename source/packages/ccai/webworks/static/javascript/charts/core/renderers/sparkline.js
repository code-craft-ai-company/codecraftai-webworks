/*
 * sparkline.js
 *
 * Sparkline renderer — compact, minimal-chrome inline trend.
 *
 * Registered types:
 *   "sparkline" — line or bar sparkline (default block size 48px, no
 *                 legend; give the host its own size, e.g.
 *                 style="width:120px;height:30px", for word-sized use)
 *
 * ctx.attrs recognised:
 *   sparkline-variant  "line" | "bar" (default "line")
 *   show-markers       boolean (default true) — first/last/min/max dots
 *   show-last-value    boolean (default false) — trailing text label
 *   x-scale            see line.js (line variant)
 *
 * No axes or legends are drawn; the chart fills the surface, keeping just
 * enough margin for the markers and the last-value label. The line variant
 * places points with the same time / linear / categorical x rules as
 * line.js; the bar variant draws one bar per value from a zero baseline.
 * A sparkline shows one series: further series are not drawn (a console
 * warning says so). Hovering the line shows the nearest point; without
 * markers the line itself is focusable and the arrow keys step through the
 * points.
 *
 * Series data may use:
 *   series[].points  [{x, y}, ...]
 *   series[].values  [...]
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, linePath } from "../svgdraw.js";
import { linearScale, bandScale } from "../scales.js";
import { textWidth, activate } from "./bar.js";
import { booleanOption } from "../chartoptions.js";
import { trendSeries, resolveXAxis, sortedPixels, loneIndices } from "./line.js";

const MARKER_RADIUS = 2.5;

/* Data objects already warned about, so a resize does not warn again. */
const WARNED = new WeakSet();


function _warnExtraSeries(model) {
  /*
   * Tell the author once that only the first series is drawn.
   */
  const source = model.source
  if (model.series.length > 1 && source !== null && typeof source === "object" && WARNED.has(source) === false) {
    WARNED.add(source)
    console.warn(`mj-chart sparkline: only the first series ("${model.series[0].name}") is drawn; ` +
      `${model.series.length - 1} more were ignored.`)
  }
  return
}


function _readout(plot, pixels, plotW, plotH, color, ctx, focusable, summary) {
  /*
   * A plot-wide overlay that follows the pointer to the nearest point and
   * shows a marker for it; when `focusable`, it is the chart's tab stop and
   * Arrow / Home / End keys move between the points.
   */
  const valid = pixels.filter((pixel) => pixel.y !== null)
  if (valid.length === 0) {
    return
  }

  const marker = svgEl("circle", {
    r: MARKER_RADIUS + 1, cx: valid[0].x.toFixed(2), cy: valid[0].y.toFixed(2),
    fill: color, stroke: "var(--mj-surface, #fff)", "stroke-width": 1,
    visibility: "hidden", "pointer-events": "none", part: "spark-focus"
  }, [])
  const title = svgEl("title", null, summary)
  const overlay = svgEl("rect", {
    x: 0, y: 0, width: plotW, height: plotH, fill: "transparent", part: "spark-overlay"
  }, [title])
  if (focusable === true) {
    overlay.setAttribute("tabindex", "0")
    overlay.setAttribute("role", "img")
    overlay.setAttribute("aria-label", summary)
  }

  let current = valid.length - 1
  const show = (index) => {
    current = Math.min(Math.max(index, 0), valid.length - 1)
    const pixel = valid[current]
    marker.setAttribute("cx", pixel.x.toFixed(2))
    marker.setAttribute("cy", pixel.y.toFixed(2))
    marker.setAttribute("visibility", "visible")
    const text = `${pixel.label}: ${formatNumber(pixel.value)}`
    title.textContent = text
    if (focusable === true) {
      overlay.setAttribute("aria-label", text)
    }
    return
  }

  overlay.addEventListener("pointermove", (event) => {
    const box = overlay.getBoundingClientRect()
    const scale = box.width > 0 ? plotW / box.width : 1
    const localX = (event.clientX - box.left) * scale
    let nearest = 0
    for (let index = 1; index < valid.length; index = index + 1) {
      if (Math.abs(valid[index].x - localX) < Math.abs(valid[nearest].x - localX)) {
        nearest = index
      }
    }
    show(nearest)
  })
  overlay.addEventListener("pointerleave", () => {
    marker.setAttribute("visibility", "hidden")
    title.textContent = summary
  })
  activate(overlay, () => {
    const pixel = valid[current]
    ctx.emit("mj-chart-sparkline-click", { x: pixel.label, y: pixel.value })
  })
  if (focusable === true) {
    overlay.addEventListener("keydown", (event) => {
      let next = null
      if (event.key === "ArrowRight" || event.key === "ArrowUp") {
        next = current + 1
      } else if (event.key === "ArrowLeft" || event.key === "ArrowDown") {
        next = current - 1
      } else if (event.key === "Home") {
        next = 0
      } else if (event.key === "End") {
        next = valid.length - 1
      }
      if (next !== null) {
        event.preventDefault()
        show(next)
      }
    })
    overlay.addEventListener("blur", () => {
      marker.setAttribute("visibility", "hidden")
    })
  }

  plot.appendChild(overlay)
  plot.appendChild(marker)
  return
}


export function render(ctx) {
  /*
   * Render a sparkline chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const root = svgEl("g", { part: "plot" }, [])

  const variant = String(ctx.attrs("sparkline-variant", "line")).trim().toLowerCase() === "bar" ? "bar" : "line"
  const showMarkers = booleanOption(ctx, "show-markers", true)
  const showLastValue = booleanOption(ctx, "show-last-value", false)

  if (model.series.length === 0) {
    return root
  }
  _warnExtraSeries(model)

  /* Sparklines are single-series by convention: the first is drawn. */
  const list = trendSeries({ ...model, series: [model.series[0]] })
  const series = list[0]
  const color = ctx.colorFor(model.series[0].name)
  const values = series.points.filter((point) => point.y !== null).map((point) => point.y)
  if (values.length === 0) {
    return root
  }

  const lastValue = values[values.length - 1]
  const fontSize = Math.max(8, Math.min(11, ctx.height * 0.45))
  const lastText = formatNumber(lastValue)
  const edge = Math.ceil(MARKER_RADIUS + 1.5)
  const margin = { top: edge, right: edge, bottom: edge, left: edge }
  if (showLastValue === true) {
    margin.right = Math.ceil(textWidth(lastText, fontSize) + edge + 4)
  }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 4)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 4)

  let yMin = Math.min(...values)
  let yMax = Math.max(...values)
  if (variant === "bar") {
    yMin = Math.min(yMin, 0)
    yMax = Math.max(yMax, 0)
  }
  if (yMin === yMax) {
    yMin = yMin - 1
    yMax = yMax + 1
  }
  const yScale = linearScale([yMin, yMax], [plotH, 0])

  const plot = svgEl("g", { transform: `translate(${margin.left},${margin.top})` }, [])
  root.appendChild(plot)

  let lastY = yScale(lastValue)

  if (variant === "bar") {
    /* One bar per value from the zero baseline, in data order. */
    const slots = series.points.map((point, index) => index)
    const band = bandScale(slots, [0, plotW], 0.2)
    const baseline = yScale(0)
    for (let index = 0; index < series.points.length; index = index + 1) {
      const point = series.points[index]
      if (point.y === null) {
        continue
      }
      const top = yScale(point.y)
      const label = point.raw !== null ? String(point.raw) : String(index + 1)
      const bar = svgEl("rect", {
        x: band.at(index).toFixed(2),
        y: Math.min(top, baseline).toFixed(2),
        width: Math.max(band.bandwidth(), 1).toFixed(2),
        height: Math.max(Math.abs(top - baseline), 1).toFixed(2),
        fill: color,
        part: "spark-bar",
        tabindex: "0",
        role: "img",
        "aria-label": `${label}: ${formatNumber(point.y)}`
      }, [svgEl("title", null, `${label}: ${formatNumber(point.y)}`)])
      activate(bar, () => {
        ctx.emit("mj-chart-sparkline-click", { x: label, y: point.y })
      })
      plot.appendChild(bar)
    }
    lastY = yScale(lastValue)
  } else {
    const xAxis = resolveXAxis(ctx, list, model, [0, plotW], null)
    const frame = { x: xAxis, y: yScale }
    const pixels = sortedPixels(series, frame).map((pixel) => ({
      x: pixel.x, y: pixel.y, value: pixel.value, label: xAxis.labelOf(pixel.point), point: pixel.point
    }))
    const data = linePath(pixels.map((pixel) => pixel.y === null ? null : { x: pixel.x, y: pixel.y }))
    if (data !== "") {
      plot.appendChild(svgEl("path", {
        d: data,
        fill: "none",
        stroke: color,
        "stroke-width": 1.5,
        "stroke-linejoin": "round",
        "stroke-linecap": "round",
        part: "spark-line"
      }, []))
    }

    /* A value between two gaps has no line: give it a dot. */
    const lone = loneIndices(pixels)
    for (let index = 0; index < lone.length; index = index + 1) {
      plot.appendChild(svgEl("circle", {
        cx: pixels[lone[index]].x.toFixed(2), cy: pixels[lone[index]].y.toFixed(2), r: 1.5,
        fill: color, part: "spark-dot", "pointer-events": "none"
      }, []))
    }

    const valid = pixels.filter((pixel) => pixel.y !== null)
    const first = valid[0]
    const last = valid[valid.length - 1]
    lastY = last.y
    let minPixel = first
    let maxPixel = first
    for (let index = 1; index < valid.length; index = index + 1) {
      if (valid[index].value < minPixel.value) {
        minPixel = valid[index]
      }
      if (valid[index].value > maxPixel.value) {
        maxPixel = valid[index]
      }
    }
    const summary = `${model.series[0].name}: first ${formatNumber(first.value)}, last ${formatNumber(last.value)}, ` +
      `min ${formatNumber(minPixel.value)}, max ${formatNumber(maxPixel.value)}`

    /* The overlay sits under the markers so the markers stay clickable. */
    _readout(plot, pixels, plotW, plotH, color, ctx, showMarkers === false, summary)

    if (showMarkers === true) {
      const marked = []
      for (const pixel of [first, last, minPixel, maxPixel]) {
        if (marked.indexOf(pixel) < 0) {
          marked.push(pixel)
        }
      }
      for (let index = 0; index < marked.length; index = index + 1) {
        const pixel = marked[index]
        const text = `${pixel.label}: ${formatNumber(pixel.value)}`
        const dot = svgEl("circle", {
          cx: pixel.x.toFixed(2), cy: pixel.y.toFixed(2), r: MARKER_RADIUS,
          fill: color,
          stroke: "var(--mj-surface, #fff)",
          "stroke-width": 1,
          part: "spark-marker",
          tabindex: "0",
          role: "img",
          "aria-label": text
        }, [svgEl("title", null, text)])
        activate(dot, () => {
          ctx.emit("mj-chart-sparkline-click", { x: pixel.label, y: pixel.value })
        })
        plot.appendChild(dot)
      }
    }
  }

  /* Optional last-value label, kept inside the drawing. */
  if (showLastValue === true) {
    const half = fontSize / 2
    const labelY = Math.min(Math.max(lastY, half - margin.top + 1), plotH + margin.bottom - half - 1)
    plot.appendChild(svgEl("text", {
      x: plotW + edge + 2,
      y: labelY,
      "dominant-baseline": "central",
      "font-size": fontSize.toFixed(1),
      fill: "var(--mj-text-muted, #5f6673)",
      "aria-hidden": "true"
    }, lastText))
  }

  return root
}


registerRenderer("sparkline", render, { minHeight: 48, legend: "none" })
