/*
 * pareto.js
 *
 * Pareto chart renderer (sorted bars + cumulative % line on secondary axis).
 *
 * Registers: "pareto"
 *
 * ctx.model.categories       -- defect / category labels (may repeat; bars
 *                               are placed by position)
 * ctx.model.series[0].values -- frequencies / counts (need not be pre-sorted)
 * ctx.model.meta["pareto-line"] -- set false to suppress the 80% reference line
 *
 * Left Y axis:  absolute count, linear [0, grand total]
 * Right Y axis: cumulative %, linear [0, 100]
 * X axis:       categories sorted descending by value (ties keep data order)
 *
 * Counts must be non-negative: a null (or non-number) is a gap and its
 * category is left out; a negative count is invalid, left out, and reported
 * with `mj-chart-error`. Category labels are drawn level when they fit,
 * rotated when they do not, and thinned out when even rotated labels would
 * collide; every bar keeps its full name in its tooltip and the table.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, linePath } from "../svgdraw.js";
import { linearScale, bandScale, niceTicks } from "../scales.js";


const LABEL_FONT = 11;
const MAX_LABEL_CHARS = 18;
const ROTATION = 40;
const REFERENCE_PERCENT = 80;


function _textWidth(text, fontSize) {
  /*
   * Estimate the rendered width of a label.
   */
  const width = String(text).length * fontSize * 0.58
  return width
}


function _shorten(text, characters) {
  /*
   * Cut a label to a number of characters with an ellipsis.
   */
  const label = String(text)
  if (label.length <= characters) {
    return label
  }
  const cut = label.slice(0, Math.max(characters - 1, 1)) + "…"
  return cut
}


function _percentText(percent) {
  /*
   * A cumulative share label ("83.4%").
   */
  const text = `${formatNumber(percent, { maximumFractionDigits: 1 })}%`
  return text
}


export function render(ctx) {
  /*
   * Render a Pareto chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const root = svgEl("g", { part: "plot" }, [])

  const categories = model.categories
  const series = model.series
  if (categories.length === 0 || series.length === 0) {
    return root
  }

  const firstSeries = series[0]
  const showParetoLine = !(model.meta && model.meta["pareto-line"] === false)

  /* Keep the valid counts and sort them descending (stable for ties). */
  const indexed = []
  const negatives = []
  for (let index = 0; index < categories.length; index = index + 1) {
    const value = firstSeries.values[index]
    if (typeof value !== "number" || Number.isFinite(value) === false) {
      continue
    }
    if (value < 0) {
      negatives.push(String(categories[index]))
      continue
    }
    indexed.push({ category: String(categories[index]), value: value, origIndex: index })
  }
  if (negatives.length > 0) {
    ctx.emit("mj-chart-error", {
      message: `pareto: negative counts are not drawn (${negatives.join(", ")})`
    })
  }
  indexed.sort((a, b) => b.value - a.value || a.origIndex - b.origIndex)

  let grandTotal = 0
  for (let index = 0; index < indexed.length; index = index + 1) {
    grandTotal = grandTotal + indexed[index].value
  }
  if (grandTotal <= 0) {
    return root
  }

  let cumSum = 0
  for (let index = 0; index < indexed.length; index = index + 1) {
    cumSum = cumSum + indexed[index].value
    indexed[index].cumulative = (cumSum / grandTotal) * 100
  }

  const valueName = String(firstSeries.name || "Count")
  const barColor = ctx.colorFor(0)
  const lineColor = ctx.colorFor("Cumulative %")
  ctx.setLegend([
    { label: valueName, color: barColor },
    { label: "Cumulative %", color: lineColor }
  ])
  ctx.setTable({
    columns: ["Category", valueName, "Cumulative %"],
    rows: indexed.map((entry) => [entry.category, entry.value, _percentText(entry.cumulative)])
  })

  /* Category label layout: level, rotated, or rotated and thinned. */
  const leftTickWidth = _textWidth(formatNumber(grandTotal), 11)
  let marginLeft = Math.max(leftTickWidth + 14, 40)
  const marginRight = 44
  let longest = 0
  for (let index = 0; index < indexed.length; index = index + 1) {
    longest = Math.max(longest, _textWidth(indexed[index].category, LABEL_FONT))
  }
  const rotate = longest > (ctx.width - marginLeft - marginRight) / indexed.length - 4
  const rotatedLength = Math.min(longest, _textWidth("x".repeat(MAX_LABEL_CHARS), LABEL_FONT))
  const rotatedExtent = rotate === true ? Math.sin(ROTATION * Math.PI / 180) * rotatedLength + 10 : 0
  if (rotate === true) {
    /* The first rotated label runs down-left from its bar: keep it inside. */
    const reach = Math.cos(ROTATION * Math.PI / 180) * rotatedLength
    const firstCenter = (ctx.width - marginLeft - marginRight) / indexed.length / 2
    marginLeft = Math.min(Math.max(marginLeft, reach - firstCenter + 6), ctx.width * 0.3)
  }
  const plotW = Math.max(ctx.width - marginLeft - marginRight, 10)
  const step = plotW / indexed.length
  const labelEvery = rotate === true ? Math.max(Math.ceil((LABEL_FONT + 3) / step), 1) : 1
  const marginBottom = Math.min(rotate === true ? rotatedExtent + 16 : 28, ctx.height * 0.4)
  const marginTop = 16
  const plotH = Math.max(ctx.height - marginTop - marginBottom, 10)

  const cat = bandScale(indexed.map((entry) => entry.category), [0, plotW], 0.15)
  const leftVal = linearScale([0, grandTotal], [plotH, 0])
  const rightVal = linearScale([0, 100], [plotH, 0])
  const bandwidth = cat.bandwidth()

  const plot = svgEl("g", { transform: `translate(${marginLeft},${marginTop})` }, [])
  root.appendChild(plot)

  /* Axes, gridlines and tick labels: decoration. */
  const axis = svgEl("g", { "aria-hidden": "true" }, [])
  plot.appendChild(axis)
  const leftTicks = niceTicks(0, grandTotal, 5)
  for (let t = 0; t < leftTicks.length; t = t + 1) {
    const y = leftVal(leftTicks[t])
    axis.appendChild(svgEl("line", {
      x1: 0, y1: y.toFixed(2), x2: plotW, y2: y.toFixed(2),
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    axis.appendChild(svgEl("text", {
      x: -8, y: (y + 4).toFixed(2), "text-anchor": "end",
      "font-size": 11, fill: "var(--mj-text-muted, #5f6673)"
    }, formatNumber(leftTicks[t])))
  }
  const rightTicks = niceTicks(0, 100, 5)
  for (let t = 0; t < rightTicks.length; t = t + 1) {
    const y = rightVal(rightTicks[t])
    axis.appendChild(svgEl("text", {
      x: plotW + 8, y: (y + 4).toFixed(2), "text-anchor": "start",
      "font-size": 11, fill: "var(--mj-text-muted, #5f6673)"
    }, `${rightTicks[t]}%`))
  }
  const axisLines = [
    { x1: 0, y1: plotH, x2: plotW, y2: plotH },
    { x1: 0, y1: 0, x2: 0, y2: plotH },
    { x1: plotW, y1: 0, x2: plotW, y2: plotH }
  ]
  for (let index = 0; index < axisLines.length; index = index + 1) {
    axis.appendChild(svgEl("line", {
      ...axisLines[index],
      stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
    }, []))
  }

  /* Category labels. */
  for (let index = 0; index < indexed.length; index = index + 1) {
    if (index % labelEvery !== 0) {
      continue
    }
    const x = cat.centerAt(index)
    if (rotate === true) {
      axis.appendChild(svgEl("text", {
        x: x.toFixed(2),
        y: (plotH + 12).toFixed(2),
        "text-anchor": "end",
        transform: `rotate(-${ROTATION} ${x.toFixed(2)} ${(plotH + 12).toFixed(2)})`,
        "font-size": LABEL_FONT,
        fill: "var(--mj-text, #14181f)"
      }, _shorten(indexed[index].category, MAX_LABEL_CHARS)))
    } else {
      axis.appendChild(svgEl("text", {
        x: x.toFixed(2),
        y: (plotH + 18).toFixed(2),
        "text-anchor": "middle",
        "font-size": LABEL_FONT,
        fill: "var(--mj-text, #14181f)"
      }, indexed[index].category))
    }
  }

  /* 80% reference line. */
  if (showParetoLine === true) {
    const refY = rightVal(REFERENCE_PERCENT)
    axis.appendChild(svgEl("line", {
      x1: 0, y1: refY.toFixed(2), x2: plotW, y2: refY.toFixed(2),
      stroke: "var(--mj-text-muted, #5f6673)",
      "stroke-width": 1,
      "stroke-dasharray": "6,3"
    }, []))
    axis.appendChild(svgEl("text", {
      x: (plotW - 4).toFixed(2),
      y: (refY - 4).toFixed(2),
      "text-anchor": "end",
      "font-size": 10,
      fill: "var(--mj-text-muted, #5f6673)"
    }, `${REFERENCE_PERCENT}%`))
  }

  /* Sorted bars. */
  const bars = svgEl("g", { part: "bars" }, [])
  plot.appendChild(bars)
  for (let index = 0; index < indexed.length; index = index + 1) {
    const entry = indexed[index]
    const barTop = leftVal(entry.value)
    const description = `${entry.category}: ${formatNumber(entry.value)} (${_percentText(entry.cumulative)} cumulative)`

    const rect = svgEl("rect", {
      x: cat.at(index).toFixed(2),
      y: barTop.toFixed(2),
      width: Math.max(bandwidth, 1).toFixed(2),
      height: Math.max(plotH - barTop, 1).toFixed(2),
      rx: 2,
      fill: barColor,
      part: "bar",
      tabindex: "0",
      role: "img",
      "aria-label": description
    }, [svgEl("title", null, description)])

    const handler = () => {
      ctx.emit("mj-chart-bar-click", {
        category: entry.category,
        value: entry.value,
        cumulativePct: entry.cumulative
      })
    }
    rect.addEventListener("click", handler)
    rect.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        handler()
      }
    })
    bars.appendChild(rect)
  }

  /* Cumulative % line and its points (the bars carry the focus stops). */
  const linePoints = indexed.map((entry, index) => {
    return { x: cat.centerAt(index), y: rightVal(entry.cumulative) }
  })
  const line = svgEl("g", { part: "cumulative" }, [])
  plot.appendChild(line)
  const pathData = linePath(linePoints)
  if (pathData !== "") {
    line.appendChild(svgEl("path", {
      d: pathData,
      fill: "none",
      stroke: lineColor,
      "stroke-width": 2
    }, []))
  }
  const dotRadius = Math.min(4, Math.max(step / 4, 1.5))
  for (let index = 0; index < linePoints.length; index = index + 1) {
    const point = linePoints[index]
    const entry = indexed[index]
    const dot = svgEl("circle", {
      cx: point.x.toFixed(2),
      cy: point.y.toFixed(2),
      r: dotRadius.toFixed(2),
      fill: lineColor,
      stroke: "var(--mj-surface, #ffffff)",
      "stroke-width": 1.5,
      part: "dot"
    }, [svgEl("title", null, `${entry.category}: ${_percentText(entry.cumulative)} cumulative`)])
    dot.addEventListener("click", () => {
      ctx.emit("mj-chart-dot-click", {
        category: entry.category,
        cumulativePct: entry.cumulative
      })
    })
    line.appendChild(dot)
  }

  return root
}


registerRenderer("pareto", render);
