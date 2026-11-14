/*
 * mjburndownchart.js
 *
 * <mj-burndown-chart> -- burndown / burnup chart with ideal line, actual
 * line, scope-change markers, and today marker.
 *
 * The SVG is a labelled group whose data points are keyboard reachable (one
 * tab stop, arrow keys between points); selecting a point enlarges it and
 * writes its values to the read-out in the header. A data table with the
 * same values can be disclosed from the header.
 *
 * Data: `data` property, `src` attribute or inline JSON child --
 *   { totalScope, dailyValues: [{ date, value }],
 *     scopeChanges: [{ date, delta }], startDate, endDate }
 * A `YYYY-MM-DD` date is a local calendar day.
 *
 * The sprint runs from `start-date` to `end-date` (attributes), else from
 * `data.startDate` to `data.endDate`, else over the extent of the daily
 * values. The ideal line spans the sprint, and "Behind schedule" compares
 * the latest actual value with the ideal at min(today, sprint end). When no
 * sprint end is declared and the latest value is from today or yesterday the
 * sprint is taken to be still running, its end is unknown, and no verdict is
 * shown.
 */

import { nextId } from "../core/mjelement.js";
import { html } from "../core/html.js";
import { formatNumber, t } from "../core/intl.js";
import {
  DAY_MS, PM_CHART_STYLES, PmChartElement, chartEndTime, chartTime,
  emptyStateMarkup, formatChartDate, isDateOnly, localDateKey, markSelection,
  resolveTimeRange, setEmptyState, timeTicks, toNumber, wireMarks
} from "./pmchartsupport.js";

const PAD_L = 56;
const PAD_R = 16;
const PAD_T = 16;
const PAD_B = 40;
const SVG_H = 300;
const POINT_R = 5;
const POINT_R_SELECTED = 8;
const MIN_PLOT_W = 240;
const TICK_SPACING = 72;

const STYLES = `
${PM_CHART_STYLES}
.status-badge { font-size: var(--mj-font-size-xs); font-weight: var(--mj-font-weight-medium); color: var(--mj-color-danger); background: var(--mj-color-danger-surface); border: 1px solid var(--mj-color-danger); border-radius: var(--mj-radius-pill); padding: 0 var(--mj-space-2); }
.point-readout { font-size: var(--mj-font-size-xs); color: var(--mj-text-muted); }
.swatch { inline-size: 16px; block-size: 10px; display: inline-block; border-radius: 2px; }
.swatch-ideal { block-size: 0; border-block-start: 2px dashed var(--mj-text-muted); }
.swatch-actual { background: var(--mj-accent); }
.swatch-scope { block-size: 0; border-block-start: 2px dashed var(--mj-color-warning); }
`;

export class MjBurndownChart extends PmChartElement {
  static tagName = "mj-burndown-chart";
  static styles = STYLES;
  static watched = ["mode", "unit", "start-date", "end-date", "today-marker", "show-ideal", "show-scope-changes"];

  constructor() {
    super()
    this._selectedPoint = null
    this._selectedKey = null
    this._tableId = nextId("mj-bd-table")
  }

  render() {
    const chartLabel = t("mj.burndownChart.labelBurndown")

    const markup = html`
      <div class="wrapper" part="wrapper" role="group" aria-label="${chartLabel}">
        <div class="toolbar header">
          <strong class="toolbar-title chart-title">${t("mj.burndownChart.titleBurndown")}</strong>
          <span class="status-badge" part="status-badge" hidden>${t("mj.burndownChart.behindSchedule")}</span>
          <span class="point-readout" part="point-detail" role="status"></span>
          <span class="toolbar-spacer"></span>
          <button class="chart-button toggle-btn" type="button" aria-controls="${this._tableId}" aria-expanded="false">${t("mj.burndownChart.showDataTable")}</button>
        </div>
        <div class="chart-scroll svg-wrap">
          <svg part="svg" role="group" aria-label="${chartLabel}"></svg>
          ${emptyStateMarkup()}
        </div>
        <div class="legend" part="legend">
          <span class="legend-item legend-ideal"><span class="swatch swatch-ideal"></span> ${t("mj.burndownChart.legendIdeal")}</span>
          <span class="legend-item"><span class="swatch swatch-actual"></span> ${t("mj.burndownChart.legendActual")}</span>
          <span class="legend-item legend-scope"><span class="swatch swatch-scope"></span> ${t("mj.burndownChart.legendScopeChange")}</span>
        </div>
        <div id="${this._tableId}" class="a11y-table-wrap" hidden>
          <table part="data-table">
            <caption class="table-caption">${t("mj.burndownChart.captionBurndown")}</caption>
            <thead><tr><th scope="col">${t("mj.burndownChart.columnDate")}</th><th scope="col" class="value-header">${t("mj.burndownChart.columnRemaining")}</th><th scope="col">${t("mj.burndownChart.columnIdeal")}</th><th scope="col">${t("mj.burndownChart.columnScopeChange")}</th></tr></thead>
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
    this._statusBadge = this.$(".status-badge")
    this._readout = this.$(".point-readout")
    this._tableBody = this.$(".table-body")

    wireMarks(this, this._svg, (mark) => {
      this._onMarkActivate(mark)
    }, (key) => {
      this._activeMarkKey = key
    })

    /* Escape clears the selected point. */
    this.listen(this.shadowRoot, "keydown", (event) => {
      if (event.key === "Escape" && this._selectedPoint !== null) {
        event.preventDefault()
        this._clearSelection(true)
      }
    })

    this.setupChart({
      alternativeButton: this.$(".toggle-btn"),
      alternativeRegion: this.$(`#${this._tableId}`),
      resizeTarget: this._svgWrap
    })
    return
  }

  get selectedPoint() {
    return this._selectedPoint
  }

  onDataChanged() {
    this._clearSelection(false)
    return
  }

  onDataDrawn() {
    const values = Array.isArray(this._data.dailyValues) === true ? this._data.dailyValues : []
    this.emit("mj-data-load", { days: values.length, unit: this._unit() })
    return
  }

  _unit() {
    const attr = this.getAttribute("unit")
    const unit = attr !== null && attr.length > 0 ? attr : "points"
    return unit
  }

  /* The unit as shown to the user: the attribute, else the localized default. */
  _unitText() {
    const attr = this.getAttribute("unit")
    const unit = attr !== null && attr.length > 0 ? attr : t("mj.burndownChart.defaultUnit")
    return unit
  }

  _mode() {
    const mode = this.getAttribute("mode") === "burnup" ? "burnup" : "burndown"
    return mode
  }

  _clearSelection(notify) {
    const hadSelection = this._selectedPoint !== null
    this._selectedPoint = null
    this._selectedKey = null
    if (this._svg !== undefined) {
      this._applySelection()
    }
    if (notify === true && hadSelection === true) {
      this.emit("mj-point-deselect", {})
    }
    return
  }

  /* Reflect the selection on the points and in the read-out. */
  _applySelection() {
    markSelection(this._svg, this._selectedKey)
    const points = this._svg.querySelectorAll("[data-mark]")
    for (let index = 0; index < points.length; index = index + 1) {
      const selected = points[index].getAttribute("data-mark") === this._selectedKey
      points[index].setAttribute("r", String(selected === true ? POINT_R_SELECTED : POINT_R))
    }

    let readout = ""
    if (this._selectedKey !== null) {
      const selectedMark = this._svg.querySelector("[data-selected='true']")
      if (selectedMark !== null) {
        readout = selectedMark.getAttribute("aria-label")
      }
    }
    this._readout.textContent = readout
    return
  }

  /*
   * Resolve the sprint: its time range and whether the end was declared.
   * Declared means it came from an attribute or a data field rather than
   * from the extent of the daily values.
   */
  _resolveSprint(data, times) {
    const startAttr = this.getAttribute("start-date")
    const endAttr = this.getAttribute("end-date")
    const startValue = startAttr !== null && Number.isNaN(chartTime(startAttr)) === false ? startAttr : data.startDate
    const endValue = endAttr !== null && Number.isNaN(chartTime(endAttr)) === false ? endAttr : data.endDate

    /* A sprint that ends on a calendar day includes that day's value. */
    const endForRange = isDateOnly(endValue) === true ? new Date(chartTime(endValue)) : endValue
    const range = resolveTimeRange(times, startValue !== undefined ? startValue : null, endForRange !== undefined ? endForRange : null, 0)
    const sprint = {
      min: range.min,
      max: range.max,
      endDeclared: Number.isNaN(chartEndTime(endValue)) === false
    }
    return sprint
  }

  drawChart() {
    const data = this._data !== null ? this._data : {}
    const mode = this._mode()
    const unit = this._unitText()
    const showIdeal = this.enabledUnlessFalse("show-ideal")
    const showScope = this.enabledUnlessFalse("show-scope-changes")

    this._syncChrome(mode, showIdeal, showScope)

    /* Daily values sorted by date; each keeps its index in the source array. */
    const dailyValues = Array.isArray(data.dailyValues) === true ? data.dailyValues : []
    const points = []
    dailyValues.forEach((entry, index) => {
      const safe = entry !== null && typeof entry === "object" ? entry : {}
      const time = chartTime(safe.date)
      points.push({ source: entry, index: index, time: time, value: toNumber(safe.value, 0), valid: Number.isNaN(time) === false })
    })
    const plotted = points.filter((point) => point.valid === true).sort((a, b) => a.time - b.time)

    const scopeChanges = (Array.isArray(data.scopeChanges) === true ? data.scopeChanges : []).map((change) => {
      const safe = change !== null && typeof change === "object" ? change : {}
      const described = { time: chartTime(safe.date), date: safe.date, delta: toNumber(safe.delta, 0) }
      return described
    }).filter((change) => Number.isNaN(change.time) === false && change.delta !== 0)

    const maxValue = plotted.reduce((highest, point) => Math.max(highest, point.value), 0)
    const totalScope = toNumber(data.totalScope, plotted.length > 0 ? (mode === "burndown" ? plotted[0].value : maxValue) : 0)
    const sprint = this._resolveSprint(data, plotted.map((point) => point.time))
    const sprintSpan = sprint.max - sprint.min

    const idealAt = (time) => {
      const fraction = Math.min(1, Math.max(0, (time - sprint.min) / sprintSpan))
      const ideal = mode === "burndown" ? totalScope * (1 - fraction) : totalScope * fraction
      return ideal
    }

    this._buildTable(points, scopeChanges, idealAt, sprint)

    if (plotted.length === 0) {
      this.renderSvg(this._svg, 0, 0, "", null)
      this._svg.toggleAttribute("hidden", true)
      this._statusBadge.hidden = true
      this._readout.textContent = ""
      setEmptyState(this, "empty")
      this._wrapper.setAttribute("aria-label", mode === "burndown" ? t("mj.burndownChart.noDataBurndown") : t("mj.burndownChart.noDataBurnup"))
      return
    }

    this._svg.toggleAttribute("hidden", false)
    setEmptyState(this, "ready")

    /* The axis covers the sprint and any values recorded outside it. */
    const axisMin = Math.min(sprint.min, plotted[0].time)
    const axisMax = Math.max(sprint.max, plotted[plotted.length - 1].time)
    const axisSpan = axisMax - axisMin

    const containerWidth = this._svgWrap.clientWidth > 0 ? this._svgWrap.clientWidth : 700
    const plotWidth = Math.max(MIN_PLOT_W, containerWidth - PAD_L - PAD_R)
    const totalWidth = plotWidth + PAD_L + PAD_R
    const plotHeight = SVG_H - PAD_T - PAD_B
    const plotBottom = PAD_T + plotHeight
    const plotRight = PAD_L + plotWidth
    const valueCeiling = Math.max(totalScope, maxValue) * 1.1
    const maxScale = valueCeiling > 0 ? valueCeiling : 10

    const timeToX = (time) => {
      const x = PAD_L + ((time - axisMin) / axisSpan) * plotWidth
      return x
    }
    const valueToY = (value) => {
      const y = PAD_T + (1 - value / maxScale) * plotHeight
      return y
    }

    const parts = []

    for (let step = 0; step <= 4; step = step + 1) {
      const value = (step / 4) * maxScale
      const y = valueToY(value)
      parts.push(html`<line x1="${PAD_L}" y1="${y}" x2="${plotRight}" y2="${y}" stroke="var(--mj-border)" stroke-width="1" aria-hidden="true"/>`)
      parts.push(html`<text x="${PAD_L - 6}" y="${y + 4}" text-anchor="end" font-size="10" fill="var(--mj-text-muted)">${formatNumber(Math.round(value))}</text>`)
    }
    /* The unit is the title of the value axis. */
    const axisTitle = mode === "burndown" ? t("mj.burndownChart.axisTitleBurndown", { unit: unit }) : t("mj.burndownChart.axisTitleBurnup", { unit: unit })
    parts.push(html`<text part="value-axis-title" transform="rotate(-90)" x="${-(PAD_T + plotHeight / 2)}" y="12" text-anchor="middle" font-size="10" fill="var(--mj-text-muted)">${axisTitle}</text>`)

    const ticks = timeTicks(axisMin, axisMax, Math.floor(plotWidth / TICK_SPACING))
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

    if (showIdeal === true) {
      parts.push(html`<line part="ideal-line" x1="${timeToX(sprint.min)}" y1="${valueToY(idealAt(sprint.min))}" x2="${timeToX(sprint.max)}" y2="${valueToY(idealAt(sprint.max))}" stroke="var(--mj-text-muted)" stroke-width="1.5" stroke-dasharray="8 4" aria-hidden="true"/>`)
    }

    /* Values dated after today are plans, not actuals: they are not plotted. */
    const now = Date.now()
    const actual = plotted.filter((point) => point.time <= now)
    if (actual.length > 1) {
      const path = actual.map((point) => `${timeToX(point.time)},${valueToY(point.value)}`).join(" ")
      parts.push(html`<polyline part="actual-line" points="${path}" stroke="var(--mj-accent)" stroke-width="2" fill="none" aria-hidden="true"/>`)
    }

    if (showScope === true) {
      scopeChanges.forEach((change) => {
        if (change.time < axisMin || change.time > axisMax) {
          return
        }
        const x = timeToX(change.time)
        const deltaLabel = change.delta > 0 ? `+${formatNumber(change.delta)}` : formatNumber(change.delta)
        const label = t("mj.burndownChart.scopeChangeLabel", { date: formatChartDate(change.date), delta: deltaLabel, unit: unit })
        const flip = x + 30 > plotRight
        parts.push(html`<g part="scope-change-marker" role="img" aria-label="${label}"><title>${label}</title><line x1="${x}" y1="${PAD_T}" x2="${x}" y2="${plotBottom}" stroke="var(--mj-color-warning)" stroke-width="1.5" stroke-dasharray="4 4"/><text x="${flip === true ? x - 4 : x + 4}" y="${PAD_T + 26}" text-anchor="${flip === true ? "end" : "start"}" font-size="10" fill="var(--mj-color-warning)">${deltaLabel}</text></g>`)
      })
    }

    if (this.enabledUnlessFalse("today-marker") === true && now >= axisMin && now <= axisMax) {
      const todayX = timeToX(now)
      const flipToday = todayX + 40 > plotRight
      parts.push(html`<line part="today-marker" x1="${todayX}" y1="${PAD_T}" x2="${todayX}" y2="${plotBottom}" stroke="var(--mj-color-danger)" stroke-width="1.5" stroke-dasharray="6 3" aria-hidden="true"/>`)
      parts.push(html`<text x="${flipToday === true ? todayX - 4 : todayX + 4}" y="${PAD_T + 12}" text-anchor="${flipToday === true ? "end" : "start"}" font-size="9" fill="var(--mj-color-danger)">${t("mj.burndownChart.today")}</text>`)
    }

    actual.forEach((point) => {
      const pointParams = { date: formatChartDate(point.source.date), value: formatNumber(point.value), unit: unit, ideal: formatNumber(Math.round(idealAt(point.time))) }
      const label = mode === "burndown" ? t("mj.burndownChart.pointLabelBurndown", pointParams) : t("mj.burndownChart.pointLabelBurnup", pointParams)
      parts.push(html`<circle class="point-el" part="data-point" cx="${timeToX(point.time)}" cy="${valueToY(point.value)}" r="${POINT_R}" fill="var(--mj-accent)" stroke="var(--mj-surface)" stroke-width="2" tabindex="-1" role="button" aria-label="${label}" data-mark="point:${point.index}"><title>${label}</title></circle>`)
    })

    this.renderSvg(this._svg, totalWidth, SVG_H, html`${parts}`, this._selectedKey)
    this._applySelection()

    /* Behind-schedule verdict (see the file header for the rule). */
    let isBehind = false
    if (actual.length > 0 && totalScope > 0) {
      const latest = actual[actual.length - 1]
      const sprintRunningWithUnknownEnd = sprint.endDeclared === false && now - latest.time < 2 * DAY_MS
      if (sprintRunningWithUnknownEnd === false) {
        const ideal = idealAt(Math.min(now, sprint.max))
        const tolerance = totalScope * 0.0001
        isBehind = mode === "burndown" ? latest.value > ideal + tolerance : latest.value < ideal - tolerance
      }
    }
    this._statusBadge.hidden = isBehind === false

    const summaryParams = {
      title: mode === "burndown" ? t("mj.burndownChart.labelBurndown") : t("mj.burndownChart.labelBurnup"),
      count: plotted.length,
      start: formatChartDate(sprint.min),
      end: formatChartDate(sprint.max),
      unit: unit
    }
    const summary = isBehind === true ? t("mj.burndownChart.summaryBehind", summaryParams) : t("mj.burndownChart.summary", summaryParams)
    this._wrapper.setAttribute("aria-label", summary)
    this._svg.setAttribute("aria-label", t("mj.burndownChart.svgLabel", { summary: summary }))
    return
  }

  /* Title, caption, column header and legend follow the mode and switches. */
  _syncChrome(mode, showIdeal, showScope) {
    this.$(".chart-title").textContent = mode === "burndown" ? t("mj.burndownChart.titleBurndown") : t("mj.burndownChart.titleBurnup")
    this.$(".table-caption").textContent = mode === "burndown" ? t("mj.burndownChart.captionBurndown") : t("mj.burndownChart.captionBurnup")
    this.$(".value-header").textContent = mode === "burndown" ? t("mj.burndownChart.columnRemaining") : t("mj.burndownChart.columnCompleted")
    this.$(".legend-ideal").hidden = showIdeal === false
    this.$(".legend-scope").hidden = showScope === false
    return
  }

  /*
   * One table row per daily value, in date order, with the scope changes of
   * that day in the last column. A scope change on a day without a value
   * gets a row of its own.
   */
  _buildTable(points, scopeChanges, idealAt, sprint) {
    const deltaByDay = new Map()
    scopeChanges.forEach((change) => {
      const dayKey = localDateKey(new Date(change.time))
      deltaByDay.set(dayKey, (deltaByDay.has(dayKey) === true ? deltaByDay.get(dayKey) : 0) + change.delta)
    })

    const rowsData = []
    const seenDays = new Set()
    points.forEach((point) => {
      const dayKey = point.valid === true ? localDateKey(new Date(point.time)) : null
      if (dayKey !== null) {
        seenDays.add(dayKey)
      }
      rowsData.push({ time: point.time, dateText: formatChartDate(point.source !== null && point.source !== undefined ? point.source.date : null), value: formatNumber(point.value), dayKey: dayKey, valid: point.valid })
    })
    scopeChanges.forEach((change) => {
      const dayKey = localDateKey(new Date(change.time))
      if (seenDays.has(dayKey) === false) {
        seenDays.add(dayKey)
        rowsData.push({ time: change.time, dateText: formatChartDate(change.date), value: "", dayKey: dayKey, valid: true })
      }
    })
    rowsData.sort((a, b) => {
      /* Rows without a usable date go last, in their original order. */
      const left = a.valid === true ? a.time : Number.POSITIVE_INFINITY
      const right = b.valid === true ? b.time : Number.POSITIVE_INFINITY
      const order = left === right ? 0 : (left < right ? -1 : 1)
      return order
    })

    const rows = rowsData.map((rowData) => {
      const ideal = rowData.valid === true ? formatNumber(Math.round(idealAt(rowData.time))) : ""
      let scopeText = ""
      if (rowData.dayKey !== null && deltaByDay.has(rowData.dayKey) === true) {
        const delta = deltaByDay.get(rowData.dayKey)
        scopeText = delta > 0 ? `+${formatNumber(delta)}` : formatNumber(delta)
      }
      const row = html`<tr><td>${rowData.dateText}</td><td>${rowData.value}</td><td>${ideal}</td><td>${scopeText}</td></tr>`
      return row
    })
    this._tableBody.innerHTML = String(html`${rows}`)
    return
  }

  _onMarkActivate(mark) {
    const key = mark.getAttribute("data-mark")
    const index = Number(key.slice(key.indexOf(":") + 1))
    const values = this._data !== null && Array.isArray(this._data.dailyValues) === true ? this._data.dailyValues : []
    const point = values[index]

    if (point !== undefined) {
      this._selectedPoint = point
      this._selectedKey = key
      this._applySelection()
      this.emit("mj-point-select", { point: point })
    }
    return
  }
}
