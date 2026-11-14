/*
 * marimekko.js
 *
 * Marimekko (Mekko / mosaic bar) renderer.
 *
 * Registers: "marimekko"
 *
 * ctx.model.categories  -- column labels (e.g. countries)
 * ctx.model.series      -- breakdown series; values[i] = magnitude for column i
 *
 * Column widths are proportional to column totals as a share of the grand
 * total. Segment heights within each column are normalized to 100%.
 *
 * Magnitudes must be non-negative: a null (or non-number) is a gap (no
 * segment); a negative value is invalid, drawn as nothing, and reported
 * with `mj-chart-error` (it is never turned into a positive share). Column
 * names and width shares are only printed where they fit the column (a
 * name is shortened with an ellipsis first); the tooltip, the legend and
 * the accessible table always carry the full names.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { linearScale, niceTicks } from "../scales.js";


const LABEL_FONT = 11;
const SEGMENT_FONT = 10;


function _textWidth(text, fontSize) {
  /*
   * Estimate the rendered width of a label.
   */
  const width = String(text).length * fontSize * 0.58
  return width
}


function _fitText(text, maxWidth, fontSize) {
  /*
   * Shorten a label with an ellipsis so it fits a width; "" when even a
   * two-character stub does not fit.
   */
  const label = String(text)
  if (_textWidth(label, fontSize) <= maxWidth) {
    return label
  }
  const characters = Math.floor(maxWidth / (fontSize * 0.58)) - 1
  if (characters < 2) {
    return ""
  }
  const fitted = label.slice(0, characters) + "…"
  return fitted
}


function _magnitude(value) {
  /*
   * A drawable magnitude: the value when it is a non-negative number, else 0.
   */
  const usable = typeof value === "number" && Number.isFinite(value) === true && value > 0
  return usable === true ? value : 0
}


export function render(ctx) {
  /*
   * Render a Marimekko chart.
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

  /* Column totals over the valid magnitudes; collect invalid cells. */
  const colTotals = []
  const negatives = []
  for (let c = 0; c < categories.length; c = c + 1) {
    let total = 0
    for (let s = 0; s < series.length; s = s + 1) {
      const value = series[s].values[c]
      if (typeof value === "number" && value < 0) {
        negatives.push(`${series[s].name} / ${categories[c]}`)
      }
      total = total + _magnitude(value)
    }
    colTotals.push(total)
  }
  if (negatives.length > 0) {
    ctx.emit("mj-chart-error", {
      message: `marimekko: negative values are not drawn (${negatives.join(", ")})`
    })
  }

  let grandTotal = 0
  for (let c = 0; c < colTotals.length; c = c + 1) {
    grandTotal = grandTotal + colTotals[c]
  }
  if (grandTotal === 0) {
    return root
  }

  const margin = { top: 16, right: 16, bottom: 40, left: 44 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const plot = svgEl("g", { transform: `translate(${margin.left},${margin.top})` }, [])
  root.appendChild(plot)

  /* Y axis: 0-100% with gridlines (decoration). */
  const axis = svgEl("g", { "aria-hidden": "true" }, [])
  plot.appendChild(axis)
  const yScale = linearScale([0, 100], [plotH, 0])
  const yTicks = niceTicks(0, 100, 5)
  for (let t = 0; t < yTicks.length; t = t + 1) {
    const y = yScale(yTicks[t])
    axis.appendChild(svgEl("line", {
      x1: 0, y1: y.toFixed(2), x2: plotW, y2: y.toFixed(2),
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    axis.appendChild(svgEl("text", {
      x: -8, y: (y + 4).toFixed(2), "text-anchor": "end",
      "font-size": 11, fill: "var(--mj-text-muted, #5f6673)"
    }, `${yTicks[t]}%`))
  }

  const cells = svgEl("g", { part: "segments" }, [])
  plot.appendChild(cells)
  const labels = svgEl("g", { "aria-hidden": "true", "pointer-events": "none" }, [])
  plot.appendChild(labels)

  /* Columns. */
  let xCursor = 0
  for (let c = 0; c < categories.length; c = c + 1) {
    const category = String(categories[c])
    const colTotal = colTotals[c]
    const colWidthFraction = colTotal / grandTotal
    const colWidthPx = colWidthFraction * plotW

    let yCursor = 100
    for (let s = 0; s < series.length; s = s + 1) {
      const rawValue = series[s].values[c]
      const value = _magnitude(rawValue)
      if (value === 0 || colTotal === 0) {
        continue
      }
      const pct = (value / colTotal) * 100
      const segTop = yScale(yCursor)
      const segBot = yScale(yCursor - pct)
      const segH = Math.abs(segBot - segTop)
      const description = `${series[s].name}, ${category}: ${formatNumber(value)} ` +
        `(${formatNumber(pct, { maximumFractionDigits: 1 })}% of ${category})`

      const rect = svgEl("rect", {
        x: xCursor.toFixed(2),
        y: Math.min(segTop, segBot).toFixed(2),
        width: Math.max(colWidthPx - 1, 1).toFixed(2),
        height: Math.max(segH, 1).toFixed(2),
        fill: ctx.colorFor(series[s].name),
        stroke: "var(--mj-surface, #ffffff)",
        "stroke-width": 0.5,
        part: "segment",
        tabindex: "0",
        role: "img",
        "aria-label": description
      }, [svgEl("title", null, description)])

      const handler = () => {
        ctx.emit("mj-chart-segment-click", {
          series: series[s].name,
          category: category,
          value: value,
          pct: pct
        })
      }
      rect.addEventListener("click", handler)
      rect.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })
      cells.appendChild(rect)

      /* Segment share when the segment can hold it. */
      const pctText = `${formatNumber(pct, { maximumFractionDigits: 0 })}%`
      if (segH >= SEGMENT_FONT + 4 && colWidthPx >= _textWidth(pctText, SEGMENT_FONT) + 6) {
        labels.appendChild(svgEl("text", {
          x: (xCursor + colWidthPx / 2).toFixed(2),
          y: (Math.min(segTop, segBot) + segH / 2).toFixed(2),
          "text-anchor": "middle",
          "dominant-baseline": "middle",
          "font-size": SEGMENT_FONT,
          fill: "var(--mj-text-on-accent, #ffffff)"
        }, pctText))
      }

      yCursor = yCursor - pct
    }

    /* Category name and width share, each only where it fits. */
    const name = _fitText(category, colWidthPx - 4, LABEL_FONT)
    if (name !== "") {
      labels.appendChild(svgEl("text", {
        x: (xCursor + colWidthPx / 2).toFixed(2),
        y: (plotH + 16).toFixed(2),
        "text-anchor": "middle",
        "font-size": LABEL_FONT,
        fill: "var(--mj-text, #14181f)"
      }, name))
    }
    const widthText = `${formatNumber(colWidthFraction * 100, { maximumFractionDigits: 0 })}%`
    if (colWidthPx >= _textWidth(widthText, 9) + 6) {
      labels.appendChild(svgEl("text", {
        x: (xCursor + colWidthPx / 2).toFixed(2),
        y: (plotH + 29).toFixed(2),
        "text-anchor": "middle",
        "font-size": 9,
        fill: "var(--mj-text-muted, #5f6673)"
      }, widthText))
    }

    xCursor = xCursor + colWidthPx
  }

  /* Axis baseline. */
  axis.appendChild(svgEl("line", {
    x1: 0, y1: plotH, x2: plotW, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))

  return root
}


registerRenderer("marimekko", render);
