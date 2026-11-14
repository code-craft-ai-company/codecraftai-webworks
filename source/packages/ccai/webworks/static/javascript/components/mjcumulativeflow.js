/*
 * mjcumulativeflow.js
 *
 * <mj-cumulative-flow> -- stacked area chart of work items per workflow state
 * over time, with a WIP and approximate lead-time read-out for the selected
 * day.
 *
 * Each state keeps the color and fill pattern of its position in
 * `data.states`, whether or not other states are hidden, and the legend
 * swatches use the same pattern as the bands. The legend buttons toggle a
 * state's band. The SVG is a labelled group whose day columns are keyboard
 * reachable (one tab stop, arrow keys between days); selecting a day shows
 * its counts, WIP and approximate lead time. A data table with the same
 * values can be disclosed from the header.
 *
 * Data: `data` property, `src` attribute or inline JSON child --
 *   { states: [{ id, name }], dailySeries: [{ date, <stateId>: count }] }
 * A `YYYY-MM-DD` date is a local calendar day.
 *
 * WIP is the number of items in the states between the first and the last
 * one. The approximate lead time is how long ago the items that have left
 * the first state numbered what the last state holds on the selected day.
 */

import { nextId } from "../core/mjelement.js";
import { html } from "../core/html.js";
import { formatNumber, t } from "../core/intl.js";
import {
  DAY_MS, PM_CHART_STYLES, PmChartElement, chartTime, emptyStateMarkup,
  formatChartDate, localDateKey, markSelection, resolveTimeRange, seriesColor,
  seriesPatternMarkup, setEmptyState, timeTicks, toNumber, toText, wireMarks
} from "./pmchartsupport.js";

const PAD_L = 52;
const PAD_R = 16;
const PAD_T = 16;
const PAD_B = 40;
const SVG_H = 300;
const MIN_PLOT_W = 240;
const TICK_SPACING = 72;

const STYLES = `
${PM_CHART_STYLES}
.column-readout { font-size: var(--mj-font-size-xs); color: var(--mj-text-muted); }
.legend-btn { display: flex; align-items: center; gap: var(--mj-space-1); background: none; border: 1px solid var(--mj-border-strong); border-radius: var(--mj-radius-sm); padding: 2px var(--mj-space-2); min-block-size: 24px; cursor: pointer; font: inherit; font-size: var(--mj-font-size-xs); color: var(--mj-text); }
.legend-btn:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: var(--mj-focus-ring-offset); }
.legend-btn[aria-pressed="false"] { color: var(--mj-text-muted); text-decoration: line-through; border-style: dashed; }
.legend-btn[aria-pressed="false"] .swatch { opacity: 0.35; }
.swatch { inline-size: 14px; block-size: 14px; display: inline-block; border-radius: 2px; flex: none; }
.column-hit { fill: transparent; }
.column-hit[data-selected="true"] { fill: var(--mj-text); fill-opacity: 0.08; stroke: var(--mj-text); stroke-width: 1; }
`;

export class MjCumulativeFlow extends PmChartElement {
  static tagName = "mj-cumulative-flow";
  static styles = STYLES;
  static watched = ["normalized", "start-date", "end-date", "today-marker"];

  constructor() {
    super()
    this._selectedDate = null
    this._selectedKey = null
    this._hiddenStates = new Set()
    this._tableId = nextId("mj-cfd-table")
    this._patternPrefix = nextId("mj-cfd-pat")
  }

  render() {
    const chartLabel = t("mj.cumulativeFlow.label")

    const markup = html`
      <div class="wrapper" part="wrapper" role="group" aria-label="${chartLabel}">
        <div class="toolbar header">
          <strong class="toolbar-title">${t("mj.cumulativeFlow.title")}</strong>
          <span class="column-readout" part="column-detail" role="status"></span>
          <span class="toolbar-spacer"></span>
          <button class="chart-button toggle-btn" type="button" aria-controls="${this._tableId}" aria-expanded="false">${t("mj.cumulativeFlow.showDataTable")}</button>
        </div>
        <div class="chart-scroll svg-wrap">
          <svg part="svg" role="group" aria-label="${chartLabel}"></svg>
          ${emptyStateMarkup()}
        </div>
        <div class="legend" part="legend" role="group" aria-label="${t("mj.cumulativeFlow.legendLabel")}"></div>
        <div id="${this._tableId}" class="a11y-table-wrap" hidden>
          <table part="data-table">
            <caption>${t("mj.cumulativeFlow.tableCaption")}</caption>
            <thead><tr class="thead-row"></tr></thead>
            <tbody class="table-body"></tbody>
          </table>
        </div>
      </div>`
    return markup
  }

  afterRender() {
    this._svg = this.$("svg")
    this._wrapper = this.$(".wrapper")
    this._svgWrap = this.$(".svg-wrap")
    this._legend = this.$(".legend")
    this._readout = this.$(".column-readout")
    this._tableBody = this.$(".table-body")
    this._theadRow = this.$(".thead-row")

    /* The legend buttons are rebuilt with the data; one listener serves them all. */
    this.listen(this._legend, "click", (event) => {
      const button = event.target.closest(".legend-btn")
      if (button !== null) {
        this._onLegendToggle(button)
      }
    })

    wireMarks(this, this._svg, (mark) => {
      this._onMarkActivate(mark)
    }, (key) => {
      this._activeMarkKey = key
    })

    this.listen(this.shadowRoot, "keydown", (event) => {
      if (event.key === "Escape" && this._selectedDate !== null) {
        event.preventDefault()
        this._clearSelection(true)
      }
    })

    this._buildLegend()
    this.setupChart({
      alternativeButton: this.$(".toggle-btn"),
      alternativeRegion: this.$(`#${this._tableId}`),
      resizeTarget: this._svgWrap
    })
    return
  }

  get selectedDate() {
    return this._selectedDate
  }

  get hiddenStates() {
    return this._hiddenStates
  }

  onDataChanged() {
    this._clearSelection(false)
    /* Forget hidden states the new data does not have. */
    const known = new Set(this._states().map((state) => state.id))
    this._hiddenStates.forEach((stateId) => {
      if (known.has(stateId) === false) {
        this._hiddenStates.delete(stateId)
      }
    })
    this._buildLegend()
    return
  }

  onDataDrawn() {
    const series = Array.isArray(this._data.dailySeries) === true ? this._data.dailySeries : []
    this.emit("mj-data-load", { states: this._states().length, days: series.length })
    return
  }

  /* The declared states as { id, name, index }; `index` fixes color and pattern. */
  _states() {
    const source = this._data !== null && Array.isArray(this._data.states) === true ? this._data.states : []
    const states = source.map((state, index) => {
      const safe = state !== null && typeof state === "object" ? state : {}
      const id = toText(safe.id !== undefined && safe.id !== null ? safe.id : safe.name)
      const described = { id: id, name: toText(safe.name !== undefined && safe.name !== null ? safe.name : id), index: index }
      return described
    })
    return states
  }

  _clearSelection(notify) {
    const hadSelection = this._selectedDate !== null
    this._selectedDate = null
    this._selectedKey = null
    if (this._svg !== undefined) {
      markSelection(this._svg, null)
      this._readout.textContent = ""
    }
    if (notify === true && hadSelection === true) {
      this.emit("mj-column-deselect", {})
    }
    return
  }

  /* Build the legend buttons. Called when the data changes, not per toggle. */
  _buildLegend() {
    const items = this._states().map((state) => {
      const visible = this._hiddenStates.has(state.id) === false
      const patternId = `${this._patternPrefix}-legend-${state.index}`
      const item = html`<button class="legend-btn" type="button" part="legend-item" data-state-id="${state.id}" aria-pressed="${visible === true ? "true" : "false"}"><svg class="swatch" viewBox="0 0 14 14" aria-hidden="true"><defs>${seriesPatternMarkup(patternId, state.index)}</defs><rect width="14" height="14" fill="url(#${patternId})" stroke="${seriesColor(state.index)}" stroke-width="1"/></svg><span>${state.name}</span></button>`
      return item
    })
    this._legend.innerHTML = String(html`${items}`)
    return
  }

  /* Toggle one state. The button stays in place, so it keeps focus. */
  _onLegendToggle(button) {
    const stateId = button.getAttribute("data-state-id")
    const nowVisible = this._hiddenStates.has(stateId) === true

    if (nowVisible === true) {
      this._hiddenStates.delete(stateId)
    } else {
      this._hiddenStates.add(stateId)
    }
    button.setAttribute("aria-pressed", nowVisible === true ? "true" : "false")

    this.drawChart()
    this.emit("mj-state-toggle", { stateId: stateId, visible: nowVisible })
    return
  }

  /* Valid rows inside the requested range, in date order. */
  _rows(states) {
    const data = this._data !== null ? this._data : {}
    const series = Array.isArray(data.dailySeries) === true ? data.dailySeries : []
    const rows = []

    series.forEach((entry, index) => {
      const safe = entry !== null && typeof entry === "object" ? entry : {}
      const time = chartTime(safe.date)
      const counts = {}
      states.forEach((state) => {
        counts[state.id] = Math.max(0, toNumber(safe[state.id], 0))
      })
      rows.push({ source: entry, index: index, time: time, date: safe.date, counts: counts, valid: Number.isNaN(time) === false })
    })

    return rows
  }

  /* WIP and approximate lead time (in days, or null) for `rows[position]`. */
  _flowMetrics(rows, position, states) {
    const metrics = { wip: 0, leadTimeDays: null }
    if (states.length === 0) {
      return metrics
    }

    const first = states[0].id
    const last = states[states.length - 1].id
    const row = rows[position]
    const total = states.reduce((sum, state) => sum + row.counts[state.id], 0)
    metrics.wip = states.length >= 3 ? total - row.counts[first] - row.counts[last] : total - row.counts[last]

    if (states.length >= 3) {
      const arrivals = (candidate) => {
        const sum = states.reduce((running, state) => running + candidate.counts[state.id], 0)
        const arrived = sum - candidate.counts[first]
        return arrived
      }
      const departed = row.counts[last]

      if (departed >= arrivals(row)) {
        metrics.leadTimeDays = 0
      } else {
        /* Walk back to the moment the arrivals curve was at today's departures. */
        for (let index = position - 1; index >= 0; index = index - 1) {
          const earlier = arrivals(rows[index])
          const later = arrivals(rows[index + 1])
          if (earlier <= departed && later >= departed) {
            const fraction = later > earlier ? (departed - earlier) / (later - earlier) : 0
            const crossing = rows[index].time + fraction * (rows[index + 1].time - rows[index].time)
            metrics.leadTimeDays = (row.time - crossing) / DAY_MS
            break
          }
        }
      }
    }

    return metrics
  }

  drawChart() {
    const allStates = this._states()
    const visibleStates = allStates.filter((state) => this._hiddenStates.has(state.id) === false)
    const allRows = this._rows(allStates)

    this._buildTable(allRows, allStates)

    const range = resolveTimeRange(allRows.map((row) => row.time), this.getAttribute("start-date"), this.getAttribute("end-date"), 0)
    const rows = allRows.filter((row) => row.valid === true && row.time >= range.min && row.time <= range.max).sort((a, b) => a.time - b.time)

    if (rows.length === 0 || allStates.length === 0) {
      this.renderSvg(this._svg, 0, 0, "", null)
      this._svg.toggleAttribute("hidden", true)
      this._readout.textContent = ""
      setEmptyState(this, "empty")
      this._wrapper.setAttribute("aria-label", t("mj.cumulativeFlow.noDataLabel"))
      return
    }

    this._svg.toggleAttribute("hidden", false)
    setEmptyState(this, "ready")

    const normalized = this.flag("normalized")
    const containerWidth = this._svgWrap.clientWidth > 0 ? this._svgWrap.clientWidth : 700
    const plotWidth = Math.max(MIN_PLOT_W, containerWidth - PAD_L - PAD_R)
    const totalWidth = plotWidth + PAD_L + PAD_R
    const plotHeight = SVG_H - PAD_T - PAD_B
    const plotBottom = PAD_T + plotHeight
    const plotRight = PAD_L + plotWidth
    const timeSpan = range.max - range.min

    const visibleTotal = (row) => {
      const total = visibleStates.reduce((sum, state) => sum + row.counts[state.id], 0)
      return total
    }
    const highest = rows.reduce((maximum, row) => Math.max(maximum, visibleTotal(row)), 0)
    const maxScale = normalized === true ? 100 : (highest > 0 ? highest * 1.1 : 10)

    const timeToX = (time) => {
      const x = PAD_L + ((time - range.min) / timeSpan) * plotWidth
      return x
    }
    const valueToY = (value) => {
      const y = PAD_T + (1 - value / maxScale) * plotHeight
      return y
    }

    /*
     * A band needs two samples to have an area. A single day is drawn as a
     * bar by sampling it half a day either side.
     */
    let samples = rows.map((row) => ({ time: row.time, row: row }))
    if (rows.length === 1) {
      samples = [
        { time: rows[0].time - DAY_MS / 2, row: rows[0] },
        { time: rows[0].time + DAY_MS / 2, row: rows[0] }
      ]
    }

    const parts = []
    parts.push(html`<defs>${visibleStates.map((state) => seriesPatternMarkup(`${this._patternPrefix}-${state.index}`, state.index))}</defs>`)

    for (let step = 0; step <= 4; step = step + 1) {
      const value = (step / 4) * maxScale
      const y = valueToY(value)
      parts.push(html`<line x1="${PAD_L}" y1="${y}" x2="${plotRight}" y2="${y}" stroke="var(--mj-border)" stroke-width="1" aria-hidden="true"/>`)
      parts.push(html`<text x="${PAD_L - 6}" y="${y + 4}" text-anchor="end" font-size="10" fill="var(--mj-text-muted)">${formatNumber(Math.round(value))}${normalized === true ? "%" : ""}</text>`)
    }

    const ticks = timeTicks(range.min, range.max, Math.floor(plotWidth / TICK_SPACING))
    ticks.times.forEach((time) => {
      const x = timeToX(time)
      /* Labels at either end are anchored inward so they are not clipped. */
      let anchor = "middle"
      if (x - PAD_L < 24) {
        anchor = "start"
      } else if (plotRight - x < 24) {
        anchor = "end"
      }
      parts.push(html`<text x="${x}" y="${SVG_H - 8}" text-anchor="${anchor}" font-size="10" fill="var(--mj-text-muted)">${formatChartDate(time, ticks.labelOptions)}</text>`)
    })

    parts.push(html`<line part="value-axis" x1="${PAD_L}" y1="${PAD_T}" x2="${PAD_L}" y2="${plotBottom}" stroke="var(--mj-border-strong)" stroke-width="1.5" aria-hidden="true"/>`)
    parts.push(html`<line part="time-axis" x1="${PAD_L}" y1="${plotBottom}" x2="${plotRight}" y2="${plotBottom}" stroke="var(--mj-border-strong)" stroke-width="1.5" aria-hidden="true"/>`)

    /* Bands, first state at the bottom. */
    visibleStates.forEach((state, stackPosition) => {
      const below = visibleStates.slice(0, stackPosition)
      const scaled = (sample, value) => {
        const total = visibleTotal(sample.row)
        const result = normalized === true ? (total > 0 ? (value / total) * 100 : 0) : value
        return result
      }
      const topPoints = samples.map((sample) => {
        const base = below.reduce((sum, lower) => sum + sample.row.counts[lower.id], 0)
        const point = `${timeToX(sample.time)},${valueToY(scaled(sample, base + sample.row.counts[state.id]))}`
        return point
      })
      const bottomPoints = samples.map((sample) => {
        const base = below.reduce((sum, lower) => sum + sample.row.counts[lower.id], 0)
        const point = `${timeToX(sample.time)},${valueToY(scaled(sample, base))}`
        return point
      }).reverse()

      parts.push(html`<polygon part="state-band" points="${topPoints.concat(bottomPoints).join(" ")}" fill="url(#${this._patternPrefix}-${state.index})" stroke="${seriesColor(state.index)}" stroke-width="1" aria-hidden="true"/>`)
    })

    if (this.enabledUnlessFalse("today-marker") === true) {
      const now = Date.now()
      if (now >= range.min && now <= range.max) {
        const todayX = timeToX(now)
        parts.push(html`<line part="today-marker" x1="${todayX}" y1="${PAD_T}" x2="${todayX}" y2="${plotBottom}" stroke="var(--mj-color-danger)" stroke-width="1.5" stroke-dasharray="6 3" aria-hidden="true"/>`)
      }
    }

    /* One selectable column per day, from midpoint to midpoint. */
    rows.forEach((row, position) => {
      const x = timeToX(row.time)
      const left = position > 0 ? (timeToX(rows[position - 1].time) + x) / 2 : PAD_L
      const right = position < rows.length - 1 ? (x + timeToX(rows[position + 1].time)) / 2 : plotRight
      const label = this._columnLabel(rows, position, allStates)
      parts.push(html`<rect class="column-hit" part="day-column" x="${left}" y="${PAD_T}" width="${Math.max(2, right - left)}" height="${plotHeight}" tabindex="-1" role="button" aria-label="${label}" data-mark="col:${row.index}"><title>${label}</title></rect>`)
    })

    this.renderSvg(this._svg, totalWidth, SVG_H, html`${parts}`, this._selectedKey)
    if (this._selectedKey !== null) {
      const selectedMark = this._svg.querySelector("[data-selected='true']")
      this._readout.textContent = selectedMark !== null ? selectedMark.getAttribute("aria-label") : ""
    }

    const hiddenCount = allStates.length - visibleStates.length
    let statesText = t("mj.cumulativeFlow.stateCount", { count: allStates.length })
    if (hiddenCount > 0) {
      statesText = t("mj.cumulativeFlow.stateCountHidden", { count: allStates.length, hidden: hiddenCount })
    }
    const summary = t("mj.cumulativeFlow.summary", {
      states: statesText,
      days: t("mj.cumulativeFlow.dayCount", { count: rows.length }),
      start: formatChartDate(rows[0].date),
      end: formatChartDate(rows[rows.length - 1].date)
    })
    this._wrapper.setAttribute("aria-label", summary)
    this._svg.setAttribute("aria-label", t("mj.cumulativeFlow.svgLabel", { summary: summary }))
    return
  }

  /* "May 4, 2026: Backlog 27, Ready 9, ... WIP 18, approximate lead time 3 days". */
  _columnLabel(rows, position, states) {
    const row = rows[position]
    const counts = states.map((state) => t("mj.cumulativeFlow.stateValue", { name: state.name, value: formatNumber(row.counts[state.id]) })).join(", ")
    const metrics = this._flowMetrics(rows, position, states)
    const labelParams = { date: formatChartDate(row.date), counts: counts, wip: formatNumber(metrics.wip) }
    let label = t("mj.cumulativeFlow.columnLabel", labelParams)
    if (metrics.leadTimeDays !== null) {
      const leadTime = Math.round(metrics.leadTimeDays * 10) / 10
      labelParams.count = leadTime
      labelParams.leadTime = formatNumber(leadTime)
      label = t("mj.cumulativeFlow.columnLabelLeadTime", labelParams)
    }
    return label
  }

  _buildTable(rows, states) {
    const headers = [html`<th scope="col">${t("mj.cumulativeFlow.columnDate")}</th>`].concat(states.map((state) => html`<th scope="col">${state.name}</th>`))
    this._theadRow.innerHTML = String(html`${headers}`)

    const body = rows.map((row) => {
      const cells = states.map((state) => html`<td>${formatNumber(row.counts[state.id])}</td>`)
      const line = html`<tr><th scope="row">${formatChartDate(row.date)}</th>${cells}</tr>`
      return line
    })
    this._tableBody.innerHTML = String(html`${body}`)
    return
  }

  _onMarkActivate(mark) {
    const key = mark.getAttribute("data-mark")
    const index = Number(key.slice(key.indexOf(":") + 1))
    const states = this._states()
    const rows = this._rows(states)
    const row = rows[index]

    if (row !== undefined && row.valid === true) {
      this._selectedDate = localDateKey(new Date(row.time))
      this._selectedKey = key
      markSelection(this._svg, key)
      this._readout.textContent = mark.getAttribute("aria-label")
      this.emit("mj-column-select", { date: this._selectedDate, values: Object.assign({}, row.counts) })
    }
    return
  }
}
