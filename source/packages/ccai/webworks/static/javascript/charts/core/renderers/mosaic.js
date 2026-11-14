/*
 * mosaic.js
 *
 * Mosaic plot (spine plot / contingency mosaic) renderer.
 *
 * Registers: "mosaic"
 *
 * ctx.model.categories        -- column variable levels (e.g. passenger class)
 * ctx.model.series            -- row variable levels; series[s].values[c] = cell frequency
 * ctx.model.meta["equal-widths"] -- true -> spine plot (all columns equal width)
 * ctx.model.meta["residuals"]    -- true -> shade each cell by its Pearson
 *                                   residual (observed - expected) / sqrt(expected)
 *                                   under independence: blue tints for cells
 *                                   above expectation, orange below, neutral
 *                                   for |r| < 2; the legend lists the bands
 *
 * Column widths are proportional to column marginal totals (unless equal-widths).
 * Segment heights within each column are proportional to conditional frequency.
 * Without residual shading the cells take their row variable's series colour
 * and the legend lists the row levels.
 *
 * Frequencies must be non-negative: a null (or non-number) is a gap (empty
 * cell); a negative value is invalid, treated as 0 and reported with
 * `mj-chart-error`.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { linearScale, niceTicks, seriesColor } from "../scales.js";


const LABEL_FONT = 11;
const CELL_FONT = 10;

/*
 * Residual shading bands (Friendly's cut-offs). Tints mix a palette hue
 * toward the chart surface, so they follow the theme.
 */
const POSITIVE_HUE = seriesColor(0);
const NEGATIVE_HUE = seriesColor(1);
const RESIDUAL_BANDS = [
  { label: "r ≥ 4", test: (r) => r >= 4, hue: POSITIVE_HUE, keep: 100 },
  { label: "2 ≤ r < 4", test: (r) => r >= 2, hue: POSITIVE_HUE, keep: 55 },
  { label: "|r| < 2", test: (r) => r > -2, hue: null, keep: 0 },
  { label: "-4 < r ≤ -2", test: (r) => r > -4, hue: NEGATIVE_HUE, keep: 55 },
  { label: "r ≤ -4", test: () => true, hue: NEGATIVE_HUE, keep: 100 }
];


function _textWidth(text, fontSize) {
  /*
   * Estimate the rendered width of a label.
   */
  const width = String(text).length * fontSize * 0.58
  return width
}


function _fitText(text, maxWidth, fontSize) {
  /*
   * Shorten a label with an ellipsis so it fits a width.
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


function _bandColor(band) {
  /*
   * The fill of a residual band.
   */
  if (band.hue === null) {
    return "var(--mj-bg-muted, #eef0f3)"
  }
  if (band.keep >= 100) {
    return band.hue
  }
  const color = `color-mix(in oklab, ${band.hue} ${band.keep}%, var(--mj-surface, #ffffff))`
  return color
}


function _residualBand(residual) {
  /*
   * The shading band a Pearson residual falls in.
   */
  for (let index = 0; index < RESIDUAL_BANDS.length; index = index + 1) {
    if (RESIDUAL_BANDS[index].test(residual) === true) {
      return RESIDUAL_BANDS[index]
    }
  }
  return RESIDUAL_BANDS[RESIDUAL_BANDS.length - 1]
}


export function render(ctx) {
  /*
   * Render a mosaic plot.
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

  const meta = model.meta !== null && model.meta !== undefined ? model.meta : {}
  const equalWidths = meta["equal-widths"] === true
  const residuals = meta.residuals === true

  /* Observed frequencies (invalid -> 0) and the marginal totals. */
  const observed = []
  const negatives = []
  for (let s = 0; s < series.length; s = s + 1) {
    const row = []
    for (let c = 0; c < categories.length; c = c + 1) {
      const value = series[s].values[c]
      let frequency = 0
      if (typeof value === "number" && Number.isFinite(value) === true) {
        if (value < 0) {
          negatives.push(`${series[s].name} / ${categories[c]}`)
        } else {
          frequency = value
        }
      }
      row.push(frequency)
    }
    observed.push(row)
  }
  if (negatives.length > 0) {
    ctx.emit("mj-chart-error", {
      message: `mosaic: negative frequencies are treated as 0 (${negatives.join(", ")})`
    })
  }

  const colTotals = categories.map((category, c) => {
    let total = 0
    for (let s = 0; s < series.length; s = s + 1) {
      total = total + observed[s][c]
    }
    return total
  })
  const rowTotals = observed.map((row) => row.reduce((sum, value) => sum + value, 0))
  const grandTotal = colTotals.reduce((sum, value) => sum + value, 0)
  if (grandTotal === 0) {
    return root
  }

  /* Pearson residuals under independence. */
  const residualOf = (s, c) => {
    const expected = (rowTotals[s] * colTotals[c]) / grandTotal
    const residual = expected > 0 ? (observed[s][c] - expected) / Math.sqrt(expected) : 0
    return residual
  }

  if (residuals === true) {
    ctx.setLegend(RESIDUAL_BANDS.map((band) => {
      return { label: band.label, color: _bandColor(band) }
    }))
  }
  const tableColumns = residuals === true
    ? ["Column", "Row", "Frequency", "Share of column", "Pearson residual"]
    : ["Column", "Row", "Frequency", "Share of column"]
  const tableRows = []
  for (let c = 0; c < categories.length; c = c + 1) {
    for (let s = 0; s < series.length; s = s + 1) {
      const share = colTotals[c] > 0 ? (observed[s][c] / colTotals[c]) * 100 : 0
      const row = [String(categories[c]), String(series[s].name), observed[s][c],
        `${formatNumber(share, { maximumFractionDigits: 1 })}%`]
      if (residuals === true) {
        row.push(formatNumber(residualOf(s, c), { maximumFractionDigits: 2 }))
      }
      tableRows.push(row)
    }
  }
  ctx.setTable({ columns: tableColumns, rows: tableRows })

  /* Right margin holds the row-level names next to the last column. */
  let longestRow = 0
  for (let s = 0; s < series.length; s = s + 1) {
    longestRow = Math.max(longestRow, _textWidth(series[s].name, CELL_FONT))
  }
  const rightLabels = ctx.width >= 360
  const marginRight = rightLabels === true ? Math.min(longestRow + 14, ctx.width * 0.25) : 12
  const margin = { top: 12, right: marginRight, bottom: 40, left: 12 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const plot = svgEl("g", { transform: `translate(${margin.left},${margin.top})` }, [])
  root.appendChild(plot)

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
  }

  const cells = svgEl("g", { part: "cells" }, [])
  plot.appendChild(cells)
  const labels = svgEl("g", { "aria-hidden": "true", "pointer-events": "none" }, [])
  plot.appendChild(labels)

  const colCount = categories.length
  const gapPx = colCount > 1 ? Math.min(4, plotW * 0.01) : 0
  const availW = plotW - gapPx * (colCount - 1)

  let xCursor = 0
  let lastColumn = null
  for (let c = 0; c < categories.length; c = c + 1) {
    const category = String(categories[c])
    const colTotal = colTotals[c]
    const colWidthFraction = equalWidths === true ? 1 / colCount : colTotal / grandTotal
    const colWidthPx = colWidthFraction * availW
    const columnCells = []

    let yCursor = 100
    for (let s = 0; s < series.length; s = s + 1) {
      const value = observed[s][c]
      const pct = colTotal > 0 ? (value / colTotal) * 100 : 0
      const segTop = yScale(yCursor)
      const segBot = yScale(yCursor - pct)
      const segH = Math.abs(segBot - segTop)
      const residual = residualOf(s, c)
      const band = _residualBand(residual)
      const fill = residuals === true ? _bandColor(band) : ctx.colorFor(series[s].name)
      const darkFill = residuals === false || band.keep >= 100
      const residualText = residuals === true
        ? `, residual ${formatNumber(residual, { maximumFractionDigits: 2 })}`
        : ""
      const description = `${series[s].name}, ${category}: ${formatNumber(value)} ` +
        `(${formatNumber(pct, { maximumFractionDigits: 1 })}%${residualText})`
      columnCells.push({ name: String(series[s].name), mid: Math.min(segTop, segBot) + segH / 2, height: segH })

      if (value > 0 && colWidthPx > 0) {
        const rect = svgEl("rect", {
          x: xCursor.toFixed(2),
          y: Math.min(segTop, segBot).toFixed(2),
          width: Math.max(colWidthPx, 1).toFixed(2),
          height: Math.max(segH, 1).toFixed(2),
          fill: fill,
          stroke: residuals === true ? "var(--mj-border-strong, #c7ccd6)" : "var(--mj-surface, #ffffff)",
          "stroke-width": residuals === true ? 1 : 0.5,
          part: "cell",
          tabindex: "0",
          role: "img",
          "aria-label": description
        }, [svgEl("title", null, description)])

        const handler = () => {
          ctx.emit("mj-chart-cell-click", {
            series: series[s].name,
            category: category,
            value: value,
            pct: pct,
            residual: residual
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

        /* Frequency inside the cell when it fits. */
        const text = formatNumber(value)
        if (segH >= CELL_FONT + 4 && colWidthPx >= _textWidth(text, CELL_FONT) + 6) {
          labels.appendChild(svgEl("text", {
            x: (xCursor + colWidthPx / 2).toFixed(2),
            y: (Math.min(segTop, segBot) + segH / 2).toFixed(2),
            "text-anchor": "middle",
            "dominant-baseline": "middle",
            "font-size": CELL_FONT,
            fill: darkFill === true ? "var(--mj-text-on-accent, #ffffff)" : "var(--mj-text, #14181f)"
          }, text))
        }
      }

      yCursor = yCursor - pct
    }
    lastColumn = columnCells

    /* Column name and marginal total below the column. */
    const labelX = xCursor + colWidthPx / 2
    const name = _fitText(category, colWidthPx + gapPx - 2, LABEL_FONT)
    if (name !== "") {
      labels.appendChild(svgEl("text", {
        x: labelX.toFixed(2),
        y: (plotH + 16).toFixed(2),
        "text-anchor": "middle",
        "font-size": LABEL_FONT,
        fill: "var(--mj-text, #14181f)"
      }, name))
    }
    const totalText = `n = ${formatNumber(colTotal)}`
    if (colWidthPx >= _textWidth(totalText, 9) + 4) {
      labels.appendChild(svgEl("text", {
        x: labelX.toFixed(2),
        y: (plotH + 30).toFixed(2),
        "text-anchor": "middle",
        "font-size": 9,
        fill: "var(--mj-text-muted, #5f6673)"
      }, totalText))
    }

    xCursor = xCursor + colWidthPx + gapPx
  }

  /* Row-level names beside the last column, where its cells sit. */
  if (rightLabels === true && lastColumn !== null) {
    let previousY = -Infinity
    for (let s = 0; s < lastColumn.length; s = s + 1) {
      const entry = lastColumn[s]
      const y = Math.max(entry.mid, previousY + CELL_FONT + 2)
      if (y > plotH) {
        break
      }
      labels.appendChild(svgEl("text", {
        x: (plotW + 6).toFixed(2),
        y: y.toFixed(2),
        "text-anchor": "start",
        "dominant-baseline": "middle",
        "font-size": CELL_FONT,
        fill: "var(--mj-text-muted, #5f6673)"
      }, _fitText(entry.name, marginRight - 8, CELL_FONT)))
      previousY = y
    }
  }

  return root
}


registerRenderer("mosaic", render);
