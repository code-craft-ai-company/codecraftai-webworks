/*
 * horizon.js
 *
 * Horizon chart renderer — banded, folded area chart for dense time-series.
 *
 * Registered types:
 *   "horizon" — horizon chart
 *
 * ctx.attrs recognised:
 *   horizon-bands   integer >= 1 (default 3) — number of magnitude bands
 *   row-height      integer px (default 36) — height of each series row
 *   diverging       "true" | "false" (default "false")
 *                   When true, negative values are folded downward using
 *                   a contrasting hue.
 *
 * Time axis is always horizontal (time on x). Each series becomes a fixed-
 * height row. A time-axis tick row is drawn at the bottom.
 *
 * Series data: series[].points [{x, y}] or series[].values [] + categories.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber, linePath, extent } from "../svgdraw.js";
import { linearScale, pointScale, niceTicks } from "../scales.js";


function _getXY(ser, categories) {
  /*
   * Flatten a series to [{x, y}] regardless of points/values shape.
   */
  const xy = []
  if (ser.points !== undefined && ser.points !== null && ser.points.length > 0) {
    for (let p = 0; p < ser.points.length; p = p + 1) {
      const pt = ser.points[p]
      xy.push({ x: String(pt.x), y: typeof pt.y === "number" ? pt.y : 0 })
    }
  } else if (ser.values !== undefined && ser.values !== null) {
    for (let v = 0; v < ser.values.length; v = v + 1) {
      const cat = categories[v] !== undefined ? String(categories[v]) : String(v)
      xy.push({ x: cat, y: typeof ser.values[v] === "number" ? ser.values[v] : 0 })
    }
  }
  return xy
}


function _bandColor(bandIndex, bandCount, positive) {
  /*
   * Choose a sequential CSS color for a horizon band by index.
   * Positive bands use the accent ramp; negative bands use the danger ramp.
   *
   * :param bandIndex: Zero-based band index (0 = lowest magnitude).
   * :param bandCount: Total number of bands.
   * :param positive: True for positive values.
   * :returns: CSS color string.
   */
  const alpha = 0.2 + (bandIndex / Math.max(bandCount - 1, 1)) * 0.65
  if (positive) {
    return `color-mix(in srgb, var(--mj-color-accent-500, #2563eb) ${Math.round(alpha * 100)}%, transparent)`
  }
  return `color-mix(in srgb, var(--mj-color-danger, #b91c1c) ${Math.round(alpha * 100)}%, transparent)`
}


function _buildHorizonPaths(xy, xScale, bandMax, bandCount, rowH) {
  /*
   * For a single series, compute one closed <path> per band.
   *
   * The horizon technique folds the area: each band represents a magnitude
   * slice [bandIndex*step, (bandIndex+1)*step]. Values exceeding the band
   * are clipped by rendering all bands at the same y=0..rowH clip region,
   * but offsetting the path upward so higher-value data paints the lower
   * bands.
   *
   * :param xy: Array of {x, y} data points (y >= 0; caller normalises sign).
   * :param xScale: Pixel x scale.
   * :param bandMax: Maximum y value (domain top of all bands).
   * :param bandCount: Number of bands.
   * :param rowH: Row height in pixels.
   * :returns: Array of {bandIndex, pathData, positive} objects.
   */
  const step = bandMax / bandCount
  const bands = []

  for (let b = 0; b < bandCount; b = b + 1) {
    /* Each band occupies [b*step, (b+1)*step] in data space.
     * We render values in this slice by shifting the pixel y so the
     * slice [b*step .. (b+1)*step] maps to [rowH .. 0]. */
    const yLo = b * step
    const yHi = (b + 1) * step
    const yScale = linearScale([yLo, yHi], [rowH, 0])

    const pixelPts = []
    for (let p = 0; p < xy.length; p = p + 1) {
      const y = Math.max(0, Math.min(xy[p].y, yHi))
      pixelPts.push({ x: xScale(xy[p].x), y: yScale(y) })
    }

    const topPath = linePath(pixelPts)
    if (topPath === "") {
      continue
    }
    /* Close to the bottom of the row. */
    const first = pixelPts[0]
    const last = pixelPts[pixelPts.length - 1]
    const closePart = ` L${last.x.toFixed(2)},${rowH.toFixed(2)} ` +
      `L${first.x.toFixed(2)},${rowH.toFixed(2)} Z`
    const pathData = `${topPath}${closePart}`

    bands.push({ bandIndex: b, pathData: pathData, positive: true })
  }

  return bands
}


export function render(ctx) {
  /*
   * Render a horizon chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const root = svgEl("g", { part: "plot" }, [])

  if (model.series.length === 0) {
    return root
  }

  const bandCountAttr = ctx.attrs("horizon-bands",
    model.raw !== undefined && model.raw["horizon-bands"] !== undefined
      ? String(model.raw["horizon-bands"]) : "3")
  const bandCount = Math.max(1, parseInt(bandCountAttr, 10) || 3)
  const rowH = Math.max(8, parseInt(ctx.attrs("row-height", "36"), 10) || 36)
  const diverging = ctx.attrs("diverging", "false") === "true"

  /* Normalise all series. */
  const normSeries = []
  for (let s = 0; s < model.series.length; s = s + 1) {
    const ser = model.series[s]
    const xy = _getXY(ser, model.categories)
    normSeries.push({ name: ser.name, xy: xy })
  }

  /* Collect x labels. */
  const xLabelSet = []
  const xLabelSeen = {}
  for (let s = 0; s < normSeries.length; s = s + 1) {
    for (let p = 0; p < normSeries[s].xy.length; p = p + 1) {
      const label = normSeries[s].xy[p].x
      if (xLabelSeen[label] !== true) {
        xLabelSet.push(label)
        xLabelSeen[label] = true
      }
    }
  }

  if (xLabelSet.length === 0) {
    return root
  }

  /* Compute global y extent. */
  const allY = []
  for (let s = 0; s < normSeries.length; s = s + 1) {
    for (let p = 0; p < normSeries[s].xy.length; p = p + 1) {
      allY.push(normSeries[s].xy[p].y)
    }
  }
  const yExt = extent(allY)
  const bandMax = Math.max(Math.abs(yExt[0]), Math.abs(yExt[1]))

  /* Layout dimensions. */
  const labelColW = 72
  const timeAxisH = 24
  const totalH = normSeries.length * rowH + timeAxisH
  const plotW = Math.max(ctx.width - labelColW, 40)

  const xScale = pointScale(xLabelSet, [0, plotW])

  const plot = svgEl("g", {
    transform: `translate(${labelColW},0)`
  }, [])
  root.appendChild(plot)

  /* Draw each series row. */
  for (let s = 0; s < normSeries.length; s = s + 1) {
    const ser = normSeries[s]
    const rowY = s * rowH

    /* Row background. */
    plot.appendChild(svgEl("rect", {
      x: 0, y: rowY, width: plotW, height: rowH,
      fill: "var(--mj-surface-alt, #f3f4f6)"
    }, []))

    /* Row label on the left. */
    root.appendChild(svgEl("text", {
      x: labelColW - 6,
      y: rowY + rowH / 2 + 4,
      "text-anchor": "end",
      "font-size": 11,
      fill: "var(--mj-text, #14181f)"
    }, escapeHtml(ser.name)))

    /* Define a clip region for this row. The rowGroup is translated by
     * (0, rowY) below, so the clip rect must be expressed in the row's
     * LOCAL coordinates (y: 0 .. rowH), not absolute plot coordinates --
     * otherwise the second and later rows are clipped away entirely. */
    const clipId = `mj-horizon-clip-${s}`
    const defs = svgEl("defs", null, [])
    const clipPath = svgEl("clipPath", { id: clipId }, [])
    clipPath.appendChild(svgEl("rect", {
      x: 0, y: 0, width: plotW, height: rowH
    }, []))
    defs.appendChild(clipPath)
    plot.appendChild(defs)

    const rowGroup = svgEl("g", {
      transform: `translate(0,${rowY})`,
      "clip-path": `url(#${clipId})`
    }, [])

    /* Positive bands. */
    const posXY = ser.xy.map((pt) => ({ x: pt.x, y: Math.max(0, pt.y) }))
    const posBands = _buildHorizonPaths(posXY, xScale, bandMax, bandCount, rowH)
    for (let b = 0; b < posBands.length; b = b + 1) {
      const band = posBands[b]
      const bandEl = svgEl("path", {
        d: band.pathData,
        fill: _bandColor(band.bandIndex, bandCount, true),
        part: "horizon-band"
      }, [])
      rowGroup.appendChild(bandEl)
    }

    /* Negative bands (diverging mode). */
    if (diverging === true) {
      const negXY = ser.xy.map((pt) => ({ x: pt.x, y: Math.max(0, -pt.y) }))
      const negBands = _buildHorizonPaths(negXY, xScale, bandMax, bandCount, rowH)
      for (let b = 0; b < negBands.length; b = b + 1) {
        const band = negBands[b]
        const bandEl = svgEl("path", {
          d: band.pathData,
          fill: _bandColor(band.bandIndex, bandCount, false),
          part: "horizon-band-neg"
        }, [])
        rowGroup.appendChild(bandEl)
      }
    }

    /* Interactive overlay covering the whole row. */
    const hitRect = svgEl("rect", {
      x: 0, y: 0, width: plotW, height: rowH,
      fill: "transparent",
      tabindex: "0",
      role: "img",
      "aria-label": escapeHtml(ser.name)
    }, [])
    hitRect.appendChild(svgEl("title", null, ser.name))
    const capturedName = ser.name
    const handler = () => {
      ctx.emit("mj-chart-horizon-click", { series: capturedName })
    }
    hitRect.addEventListener("click", handler)
    hitRect.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        handler()
      }
    })
    rowGroup.appendChild(hitRect)

    /* Row border. */
    rowGroup.appendChild(svgEl("line", {
      x1: 0, y1: rowH - 0.5, x2: plotW, y2: rowH - 0.5,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 0.5
    }, []))

    plot.appendChild(rowGroup)
  }

  /* Time-axis labels below. */
  const axisY = normSeries.length * rowH + 14
  const tickStep = Math.max(1, Math.ceil(xLabelSet.length / 8))
  for (let i = 0; i < xLabelSet.length; i = i + tickStep) {
    const label = xLabelSet[i]
    const x = xScale(label)
    plot.appendChild(svgEl("text", {
      x: x, y: axisY, "text-anchor": "middle",
      "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, escapeHtml(label)))
  }

  /* Axis baseline. */
  plot.appendChild(svgEl("line", {
    x1: 0, y1: normSeries.length * rowH,
    x2: plotW, y2: normSeries.length * rowH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1
  }, []))

  return root
}


registerRenderer("horizon", render)
