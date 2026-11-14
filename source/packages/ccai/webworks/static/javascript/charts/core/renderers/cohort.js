/*
 * cohort.js
 *
 * Cohort retention renderers: the cohort grid ("cohort") and the retention
 * curve ("retention", also "retention-curve").
 *
 * JSON shape (ctx.raw):
 *   cohorts[]          array of { label, size, periods[] }
 *     label            cohort row label
 *     size             cohort starting size (shown in its own column)
 *     periods[]        retention per period: rates (mode "rate") or user
 *                      counts (mode "count"); null or a non-number is a
 *                      period without data
 *   period_labels[]    column header labels ("Week 0", "Week 1", …)
 *   mode               "rate" (default) | "count"; the `mode` attribute
 *                      overrides it
 *   unit               rate mode: "fraction" (0–1) | "percent" (0–100);
 *                      when absent it is decided once for the whole data
 *                      set (percent when any rate is above 1)
 *
 * In count mode a cell's rate is count / size (or / the first period when
 * there is no size). Periods a cohort has not reached yet and periods
 * without data are greyed out.
 *
 * "cohort" draws the grid: one row per cohort (label, size, one cell per
 * period coloured by retention, with the value printed when it fits) and a
 * 0–100% colour key. "retention" draws retention curves: one line per
 * cohort over the periods on a 0–100% axis, with a legend of cohorts.
 *
 * Interaction: grid cells and curve points emit `mj-chart-cohort-click`
 * { cohort, period, value, rate }.
 *
 * Registers: "cohort", "retention", "retention-curve"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, linePath } from "../svgdraw.js";
import { linearScale } from "../scales.js";
import { sequentialFill, labelColorFor, applyContrastText, EMPTY_CELL_FILL } from "./heatmaptable.js";

const CHAR_WIDTH = 0.6


function _fit(text, maxWidth, fontSize) {
  /*
   * Shorten a label with an ellipsis to about maxWidth pixels.
   */
  const value = String(text)
  const capacity = Math.max(Math.floor(maxWidth / (fontSize * CHAR_WIDTH)), 1)
  if (value.length <= capacity) {
    return value
  }
  return value.slice(0, Math.max(capacity - 1, 1)) + "…"
}


function _readCohorts(ctx) {
  /*
   * Normalise the cohorts and compute every cell's rate.
   *
   * :returns: { cohorts: [{label, size, cells: [{value, rate} | null]}],
   *     periods: count, periodLabels: [...], mode }
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const attrMode = ctx.attrs("mode", null)
  const modeSource = attrMode !== null ? attrMode : raw.mode
  const mode = modeSource === "count" ? "count" : "rate"
  const list = (Array.isArray(raw.cohorts) === true ? raw.cohorts : [])
    .filter((cohort) => cohort !== null && typeof cohort === "object")

  /* Rate mode: one unit for the whole data set. */
  let percent = raw.unit === "percent"
  if (mode === "rate" && raw.unit !== "percent" && raw.unit !== "fraction") {
    percent = list.some((cohort) => Array.isArray(cohort.periods) === true &&
      cohort.periods.some((value) => typeof value === "number" && Number.isFinite(value) === true &&
        value > 1))
  }

  let periods = 0
  const cohorts = list.map((cohort, index) => {
    const values = Array.isArray(cohort.periods) === true ? cohort.periods : []
    periods = Math.max(periods, values.length)
    const size = typeof cohort.size === "number" && Number.isFinite(cohort.size) === true ? cohort.size : null
    const firstNumber = values.find((value) => typeof value === "number" && Number.isFinite(value) === true)
    const base = size !== null && size > 0 ? size : (firstNumber !== undefined && firstNumber > 0 ? firstNumber : null)
    const cells = values.map((value) => {
      if (typeof value !== "number" || Number.isFinite(value) === false) {
        return null
      }
      let rate = null
      if (mode === "count") {
        rate = base !== null ? value / base : null
      } else {
        rate = percent === true ? value / 100 : value
      }
      return { value: value, rate: rate }
    })
    const label = cohort.label !== undefined && cohort.label !== null ? String(cohort.label) : `Cohort ${index + 1}`
    return { label: label, size: size, cells: cells, source: cohort }
  })

  const given = Array.isArray(raw.period_labels) === true ? raw.period_labels : []
  const periodLabels = []
  for (let p = 0; p < periods; p = p + 1) {
    periodLabels.push(p < given.length && given[p] !== null && given[p] !== undefined
      ? String(given[p])
      : `Period ${p}`)
  }
  return { cohorts: cohorts, periods: periods, periodLabels: periodLabels, mode: mode }
}


function _cellText(cell, mode) {
  /*
   * Display text of a cell.
   */
  if (cell === null) {
    return "—"
  }
  if (mode === "count") {
    return formatNumber(cell.value)
  }
  return formatNumber(cell.rate * 100, { maximumFractionDigits: 0 }) + "%"
}


function _publishTable(ctx, data) {
  /*
   * Accessible table: one row per cohort, a column per period.
   */
  const columns = ["Cohort", "Size"].concat(data.periodLabels)
  const rows = data.cohorts.map((cohort) => {
    const row = [cohort.label, cohort.size]
    for (let p = 0; p < data.periods; p = p + 1) {
      const cell = p < cohort.cells.length ? cohort.cells[p] : null
      row.push(cell === null ? null : (data.mode === "count" ? cell.value : _cellText(cell, data.mode)))
    }
    return row
  })
  ctx.setTable({ columns: columns, rows: rows, caption: ctx.label })
  return
}


function _activate(element, handler) {
  /*
   * Run a handler on click and on Enter / Space.
   */
  element.addEventListener("click", handler)
  element.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      handler()
    }
  })
  return
}


function _renderGrid(ctx, data) {
  /*
   * Render the cohort grid.
   */
  const root = svgEl("g", { part: "plot" }, [])
  const cohorts = data.cohorts
  const periods = data.periods
  const showSize = cohorts.some((cohort) => cohort.size !== null)

  let longest = 0
  cohorts.forEach((cohort) => {
    longest = Math.max(longest, cohort.label.length * 11 * CHAR_WIDTH)
  })
  const labelW = Math.min(Math.max(longest + 8, 36), ctx.width * 0.3)
  const sizeW = showSize === true ? 52 : 0
  const margin = { top: 24, right: 8, bottom: 22, left: labelW + sizeW + 6 }
  const gridW = Math.max(ctx.width - margin.left - margin.right, 10)
  const gridH = Math.max(ctx.height - margin.top - margin.bottom, 10)
  const cellW = gridW / periods
  const cellH = gridH / cohorts.length

  const plot = svgEl("g", { transform: `translate(${margin.left},${margin.top})` }, [])
  root.appendChild(plot)
  const decor = svgEl("g", { "aria-hidden": "true" }, [])
  plot.appendChild(decor)

  /* Headers: thinned and truncated when the columns are narrow. */
  const headerFont = 10
  let widest = 0
  data.periodLabels.forEach((label) => {
    widest = Math.max(widest, label.length * headerFont * CHAR_WIDTH)
  })
  const every = Math.max(1, Math.ceil((Math.min(widest, 60) + 6) / cellW))
  for (let p = 0; p < periods; p = p + every) {
    decor.appendChild(svgEl("text", {
      x: p * cellW + cellW / 2, y: -8, "text-anchor": "middle", "font-size": headerFont,
      fill: "var(--mj-text-muted, #5f6673)"
    }, _fit(data.periodLabels[p], cellW * every - 4, headerFont)))
  }
  if (showSize === true) {
    decor.appendChild(svgEl("text", {
      x: -8, y: -8, "text-anchor": "end", "font-size": headerFont,
      fill: "var(--mj-text-muted, #5f6673)"
    }, "Size"))
  }

  const valueFont = Math.min(11, cellH * 0.45)
  for (let r = 0; r < cohorts.length; r = r + 1) {
    const cohort = cohorts[r]
    const rowY = r * cellH
    decor.appendChild(svgEl("text", {
      x: -(sizeW + 8), y: rowY + cellH / 2 + 4, "text-anchor": "end", "font-size": 11,
      fill: "var(--mj-text, #14181f)"
    }, [_fit(cohort.label, labelW - 4, 11), svgEl("title", null, cohort.label)]))
    if (showSize === true) {
      decor.appendChild(svgEl("text", {
        x: -8, y: rowY + cellH / 2 + 4, "text-anchor": "end", "font-size": 10,
        fill: "var(--mj-text-muted, #5f6673)"
      }, cohort.size !== null ? formatNumber(cohort.size) : ""))
    }

    for (let p = 0; p < periods; p = p + 1) {
      const cell = p < cohort.cells.length ? cohort.cells[p] : null
      const x = p * cellW
      if (cell === null || cell.rate === null) {
        decor.appendChild(svgEl("rect", {
          x: x, y: rowY, width: Math.max(cellW - 1, 0.5), height: Math.max(cellH - 1, 0.5),
          fill: EMPTY_CELL_FILL
        }, []))
        continue
      }
      const text = _cellText(cell, data.mode)
      const ariaLabel = `${cohort.label}, ${data.periodLabels[p]}: ${text}` +
        (data.mode === "count" ? ` (${formatNumber(cell.rate * 100, { maximumFractionDigits: 0 })}%)` : "")
      const group = svgEl("g", {
        tabindex: "0", role: "img", "aria-label": ariaLabel, part: "cohort-cell"
      }, [])
      group.appendChild(svgEl("rect", {
        x: x, y: rowY, width: Math.max(cellW - 1, 0.5), height: Math.max(cellH - 1, 0.5),
        fill: sequentialFill(cell.rate)
      }, []))
      if (cellH >= 14 && cellW >= text.length * valueFont * CHAR_WIDTH + 4) {
        const label = svgEl("text", {
          x: x + cellW / 2, y: rowY + cellH / 2 + valueFont * 0.35, "text-anchor": "middle",
          "font-size": valueFont, fill: labelColorFor(cell.rate), "pointer-events": "none"
        }, text)
        applyContrastText(label, sequentialFill(cell.rate), cell.rate)
        group.appendChild(label)
      }
      group.appendChild(svgEl("title", null, ariaLabel))
      const capturedCohort = cohort.source.label
      const period = p
      _activate(group, () => {
        ctx.emit("mj-chart-cohort-click", {
          cohort: capturedCohort, period: period, value: cell.value, rate: cell.rate
        })
      })
      plot.appendChild(group)
    }
  }

  /* Colour key: 0% [ramp] 100%. */
  const keyY = gridH + 8
  const key = svgEl("g", { "aria-hidden": "true", part: "legend" }, [])
  decor.appendChild(key)
  const keyW = Math.min(120, gridW * 0.4)
  const rampX = gridW - keyW - 22
  const steps = 6
  key.appendChild(svgEl("text", {
    x: rampX - 4, y: keyY + 8, "text-anchor": "end", "font-size": 9,
    fill: "var(--mj-text-muted, #5f6673)"
  }, "0%"))
  for (let s = 0; s < steps; s = s + 1) {
    key.appendChild(svgEl("rect", {
      x: rampX + s * keyW / steps, y: keyY, width: keyW / steps, height: 9,
      fill: sequentialFill(s / (steps - 1))
    }, []))
  }
  key.appendChild(svgEl("text", {
    x: rampX + keyW + 4, y: keyY + 8, "text-anchor": "start", "font-size": 9,
    fill: "var(--mj-text-muted, #5f6673)"
  }, "100%"))

  return root
}


function _renderCurve(ctx, data) {
  /*
   * Render retention curves: rate (0–100%) over periods, one line per cohort.
   */
  const root = svgEl("g", { part: "plot" }, [])
  const margin = { top: 12, right: 28, bottom: 28, left: 40 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)
  const plot = svgEl("g", { transform: `translate(${margin.left},${margin.top})` }, [])
  root.appendChild(plot)

  let top = 1
  data.cohorts.forEach((cohort) => {
    cohort.cells.forEach((cell) => {
      if (cell !== null && cell.rate !== null) {
        top = Math.max(top, cell.rate)
      }
    })
  })
  top = Math.ceil(top * 4) / 4
  const yScale = linearScale([0, top], [plotH, 0])
  const xScale = linearScale([0, Math.max(data.periods - 1, 1)], [0, plotW])

  const decor = svgEl("g", { "aria-hidden": "true" }, [])
  plot.appendChild(decor)
  for (let tick = 0; tick <= top + 1e-9; tick = tick + 0.25) {
    const y = yScale(tick)
    decor.appendChild(svgEl("line", {
      x1: 0, y1: y, x2: plotW, y2: y,
      stroke: tick === 0 ? "var(--mj-border-strong, #878e9c)" : "var(--mj-border, #e0e3e9)",
      "stroke-width": 1
    }, []))
    decor.appendChild(svgEl("text", {
      x: -6, y: y + 3, "text-anchor": "end", "font-size": 10, fill: "var(--mj-text-muted, #5f6673)"
    }, formatNumber(tick, { style: "percent", maximumFractionDigits: 0 })))
  }
  const every = Math.max(1, Math.ceil(56 / Math.max(plotW / Math.max(data.periods, 1), 1)))
  for (let p = 0; p < data.periods; p = p + every) {
    decor.appendChild(svgEl("text", {
      x: xScale(p), y: plotH + 16, "text-anchor": "middle", "font-size": 10,
      fill: "var(--mj-text-muted, #5f6673)"
    }, _fit(data.periodLabels[p], plotW / data.periods * every - 4, 10)))
  }

  for (let c = 0; c < data.cohorts.length; c = c + 1) {
    const cohort = data.cohorts[c]
    const color = ctx.colorFor(c)
    const points = cohort.cells.map((cell, p) => (cell === null || cell.rate === null
      ? null
      : { x: xScale(p), y: yScale(cell.rate) }))
    plot.appendChild(svgEl("path", {
      d: linePath(points), fill: "none", stroke: color, "stroke-width": 2,
      "stroke-linejoin": "round", "aria-hidden": "true", part: "retention-line"
    }, []))
    for (let p = 0; p < points.length; p = p + 1) {
      if (points[p] === null) {
        continue
      }
      const cell = cohort.cells[p]
      const label = `${cohort.label}, ${data.periodLabels[p]}: ` +
        `${formatNumber(cell.rate * 100, { maximumFractionDigits: 0 })}%`
      const dot = svgEl("circle", {
        cx: points[p].x.toFixed(2), cy: points[p].y.toFixed(2), r: 3, fill: color,
        tabindex: "0", role: "img", "aria-label": label, part: "retention-point"
      }, [svgEl("title", null, label)])
      const capturedCohort = cohort.source.label
      const period = p
      _activate(dot, () => {
        ctx.emit("mj-chart-cohort-click", {
          cohort: capturedCohort, period: period, value: cell.value, rate: cell.rate
        })
      })
      plot.appendChild(dot)
    }
  }

  ctx.setLegend(data.cohorts.map((cohort, c) => ({ label: cohort.label, color: ctx.colorFor(c) })))
  return root
}


export function render(ctx) {
  /*
   * Draw the requested type: the grid for "cohort", curves for
   * "retention" / "retention-curve".
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const data = _readCohorts(ctx)
  _publishTable(ctx, data)
  if (data.cohorts.length === 0 || data.periods === 0) {
    return svgEl("g", { part: "plot" }, [])
  }
  if (ctx.type === "retention" || ctx.type === "retention-curve") {
    const curve = _renderCurve(ctx, data)
    return curve
  }
  const grid = _renderGrid(ctx, data)
  return grid
}


registerRenderer("cohort", render, { legend: "none" })
registerRenderer("retention", render)
registerRenderer("retention-curve", render)
