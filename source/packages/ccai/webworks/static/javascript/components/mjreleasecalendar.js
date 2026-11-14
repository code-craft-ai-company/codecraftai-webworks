/*
 * mjreleasecalendar.js
 *
 * <mj-release-calendar> -- month / week calendar grid showing releases,
 * freezes, blackouts, and key dates as event chips; a multi-day event shows
 * on every day it covers.
 *
 * SVG-free: a CSS grid with ARIA grid semantics (rows of gridcells). One day
 * cell is in the tab order; the arrow keys move a day or a week, Home / End
 * go to the start / end of the week and PageUp / PageDown move a month
 * (crossing into the next period when needed). Tab from the focused day
 * reaches its event chips. Enter on a day, or its "+N more" button, lists
 * all of that day's events. The detail panel sits below the grid, takes
 * focus when it opens, and Escape or Close returns focus to where it came
 * from. An ordered list of all events can be disclosed from the header.
 *
 * Data: `data` property, `src` attribute or inline JSON child --
 *   { events: [{ id, name, type, startDate, endDate, description, url }] }
 * A `YYYY-MM-DD` date is a local calendar day.
 *
 * Without events the grid stays (it can still be navigated) and a status
 * block above it says so: the `empty` slot's text, "Loading…" while a `src`
 * is fetched, or the error when the data could not be loaded or is not an
 * object (mj-error is emitted as well).
 */

import { nextId } from "../core/mjelement.js";
import { html, safeUrl } from "../core/html.js";
import { getLocale, t } from "../core/intl.js";
import {
  PM_CHART_STYLES, PmChartElement, DetailPanel, detailPanelMarkup, emptyStateMarkup,
  localDateKey, parseChartDate, setEmptyState, toText
} from "./pmchartsupport.js";

const EVENT_COLORS = {
  release:   { bg: "var(--mj-color-success-surface)", border: "var(--mj-color-success)", text: "var(--mj-color-success)" },
  freeze:    { bg: "var(--mj-color-warning-surface)", border: "var(--mj-color-warning)", text: "var(--mj-color-warning)" },
  blackout:  { bg: "var(--mj-color-danger-surface)",  border: "var(--mj-color-danger)",  text: "var(--mj-color-danger)"  },
  milestone: { bg: "var(--mj-color-info-surface)",    border: "var(--mj-color-info)",    text: "var(--mj-color-info)"    },
  holiday:   { bg: "var(--mj-bg-muted)",              border: "var(--mj-border-strong)", text: "var(--mj-text-muted)"    }
};

const EVENT_ICONS = {
  release:   "🚀",
  freeze:    "❄",
  blackout:  "⛔",
  milestone: "◆",
  holiday:   "🗓"
};

/* Display text of the known event types; any other type shows as given. */
const TYPE_LABEL_KEYS = {
  release:   "mj.releaseCalendar.type.release",
  freeze:    "mj.releaseCalendar.type.freeze",
  blackout:  "mj.releaseCalendar.type.blackout",
  milestone: "mj.releaseCalendar.type.milestone",
  holiday:   "mj.releaseCalendar.type.holiday",
  event:     "mj.releaseCalendar.type.event"
};

/* The display text of an event type. */
function typeText(type) {
  const known = Object.prototype.hasOwnProperty.call(TYPE_LABEL_KEYS, type) === true
  const text = known === true ? t(TYPE_LABEL_KEYS[type]) : type
  return text
}

const MAX_CHIPS_MONTH = 3;
const MAX_CHIPS_WEEK = 8;

const STYLES = `
${PM_CHART_STYLES}
.cal-header { display: flex; align-items: center; gap: var(--mj-space-2); padding: var(--mj-space-2) var(--mj-space-3); border-block-end: 1px solid var(--mj-border); flex-wrap: wrap; }
.cal-title { font-weight: var(--mj-font-weight-medium); font-size: var(--mj-font-size-md); flex: 1; min-inline-size: 8rem; }
.nav-btn { font: inherit; font-size: 1.1rem; line-height: 1; background: none; border: 1px solid var(--mj-border-strong); border-radius: var(--mj-radius-sm); padding: 2px 8px; min-block-size: 24px; min-inline-size: 24px; cursor: pointer; color: var(--mj-text); }
.nav-btn.today-btn { font-size: var(--mj-font-size-xs); }
.nav-btn:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: var(--mj-focus-ring-offset); }
.view-switcher { display: inline-flex; gap: var(--mj-space-1); }
.view-btn[aria-pressed="true"] { background: var(--mj-accent); color: var(--mj-text-on-accent); border-color: var(--mj-accent); }
.cal-grid { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); }
.cal-row { display: contents; }
.day-header { padding: var(--mj-space-1); font-size: var(--mj-font-size-xs); font-weight: var(--mj-font-weight-medium); color: var(--mj-text-muted); text-align: center; border-block-end: 1px solid var(--mj-border); background: var(--mj-bg-subtle); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.day-cell { min-block-size: 80px; min-inline-size: 0; padding: var(--mj-space-1); border-inline-end: 1px solid var(--mj-border); border-block-end: 1px solid var(--mj-border); position: relative; }
.cal-grid[data-view="week"] .day-cell { min-block-size: 160px; }
.day-cell:nth-child(7n) { border-inline-end: none; }
.day-cell:focus { outline: none; }
.day-cell:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: calc(0px - var(--mj-focus-ring-width)); }
.day-cell.today { background: var(--mj-color-info-surface); }
/* Days of the month in --mj-text, the neighbouring months' days muted: both keep 4.5:1. */
.day-num { font-size: var(--mj-font-size-xs); color: var(--mj-text); margin-block-end: 2px; }
.day-cell.other-month .day-num { color: var(--mj-text-muted); }
.day-cell.today .day-num { font-weight: var(--mj-font-weight-bold); color: var(--mj-color-info); }
.event-chip { display: flex; align-items: center; gap: 3px; inline-size: 100%; font: inherit; font-size: 11px; border-radius: 3px; padding: 1px 4px; margin-block-end: 2px; min-block-size: 20px; cursor: pointer; border: 1px solid transparent; text-align: start; }
.event-chip:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: 1px; }
.event-chip[aria-pressed="true"] { box-shadow: inset 0 0 0 2px currentColor; }
.event-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; min-inline-size: 0; }
.event-icon { font-size: 10px; flex: none; }
.more-btn { font: inherit; font-size: 10px; color: var(--mj-text-muted); background: none; border: none; cursor: pointer; padding: 1px 4px; min-block-size: 20px; text-decoration: underline; }
.more-btn:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: 1px; }
.day-events { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: var(--mj-space-1); }
.empty-state { padding: var(--mj-space-2) var(--mj-space-3); border-block-end: 1px solid var(--mj-border); }
`;

export class MjReleaseCalendar extends PmChartElement {
  static tagName = "mj-release-calendar";
  static styles = STYLES;
  static watched = ["view", "current-date", "today-marker", "first-day-of-week", "locale"];

  constructor() {
    super()
    this._selectedEvent = null
    this._selectedEventIndex = -1
    this._view = "month"
    this._currentDate = this._today()

    /* Local date key of the day that holds the grid's tab stop, or null. */
    this._focusedDay = null

    this._listId = nextId("mj-cal-list")
    this._detailId = nextId("mj-cal-detail")
  }

  render() {
    const markup = html`
      <div class="wrapper" part="wrapper" role="group" aria-label="${t("mj.releaseCalendar.label")}">
        <div class="cal-header" part="nav-controls">
          <button class="nav-btn prev-btn" type="button" aria-label="${t("mj.releaseCalendar.previousMonth")}">&#x2039;</button>
          <span class="cal-title" aria-live="polite"></span>
          <button class="nav-btn next-btn" type="button" aria-label="${t("mj.releaseCalendar.nextMonth")}">&#x203A;</button>
          <button class="nav-btn today-btn" type="button">${t("mj.releaseCalendar.today")}</button>
          <span class="view-switcher" part="view-switcher" role="group" aria-label="${t("mj.releaseCalendar.viewSwitcher")}">
            <button class="chart-button view-btn" type="button" data-view="month" aria-pressed="true">${t("mj.releaseCalendar.viewMonth")}</button>
            <button class="chart-button view-btn" type="button" data-view="week" aria-pressed="false">${t("mj.releaseCalendar.viewWeek")}</button>
          </span>
          <button class="chart-button toggle-list-btn" type="button" aria-controls="${this._listId}" aria-expanded="false">${t("mj.releaseCalendar.showEventList")}</button>
        </div>
        ${emptyStateMarkup()}
        <div class="cal-grid" part="calendar-grid" role="grid" aria-label="${t("mj.releaseCalendar.gridLabel")}"></div>
        ${detailPanelMarkup({ headingId: this._detailId, part: "detail-popover", slotName: "event-detail", placement: "inline" })}
        <div id="${this._listId}" class="a11y-list-wrap" hidden>
          <ol part="a11y-list"></ol>
        </div>
      </div>`
    return markup
  }

  afterRender() {
    this._grid = this.$(".cal-grid")
    this._title = this.$(".cal-title")
    this._listEl = this.$("ol")
    this._prevBtn = this.$(".prev-btn")
    this._nextBtn = this.$(".next-btn")

    this._detail = new DetailPanel(this, this.$(".detail-panel"), () => {
      this._onDetailClosed()
    })

    this.listen(this._prevBtn, "click", () => {
      this._navigate(-1)
    })
    this.listen(this._nextBtn, "click", () => {
      this._navigate(1)
    })
    this.listen(this.$(".today-btn"), "click", () => {
      this._currentDate = this._today()
      this._focusedDay = localDateKey(this._currentDate)
      this._renderCalendar()
      this._emitPeriodChange()
    })
    this.listen(this.$(".view-switcher"), "click", (event) => {
      const button = event.target.closest(".view-btn")
      if (button !== null) {
        this._switchView(button.getAttribute("data-view"))
      }
    })

    /* Delegated grid handlers: registered once, the cells are rebuilt per render. */
    this.listen(this._grid, "click", (event) => {
      this._onGridClick(event)
    })
    this.listen(this._grid, "keydown", (event) => {
      this._onGridKeydown(event)
    })
    this.listen(this._grid, "focusin", (event) => {
      const cell = event.target.closest(".day-cell")
      if (cell !== null) {
        this._focusedDay = cell.getAttribute("data-day")
        this._syncRoving()
      }
    })
    this.listen(this.$(".detail-content"), "click", (event) => {
      const button = event.target.closest("[data-event-index]")
      if (button !== null) {
        this._openEvent(Number(button.getAttribute("data-event-index")), this._detailOpenerFinder())
      }
    })

    this.setupChart({
      alternativeButton: this.$(".toggle-list-btn"),
      alternativeRegion: this.$(`#${this._listId}`)
    })
    return
  }

  get selectedEvent() {
    return this._selectedEvent
  }

  get visiblePeriod() {
    const period = this._period()
    const visible = { start: period.start, end: period.end }
    return visible
  }

  onDataChanged() {
    this._selectedEvent = null
    this._selectedEventIndex = -1
    if (this._detail !== undefined) {
      this._detail.close(false)
    }
    return
  }

  onDataDrawn() {
    this.emit("mj-data-load", { events: this._events().length })
    return
  }

  /* Attribute changes update the shown period or view; they emit nothing. */
  onChartAttributeChanged(name, oldValue, newValue) {
    if (name === "current-date") {
      const parsed = parseChartDate(newValue)
      if (parsed !== null) {
        this._currentDate = new Date(parsed.getFullYear(), parsed.getMonth(), parsed.getDate())
      }
    }
    if (name === "view") {
      this._view = newValue === "week" ? "week" : "month"
    }
    this._renderCalendar()
    return
  }

  drawChart() {
    this._renderCalendar()
    return
  }

  _today() {
    const now = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    return today
  }

  _locale() {
    const attr = this.getAttribute("locale")
    let locale = getLocale()
    if (attr !== null && attr.trim().length > 0) {
      try {
        locale = Intl.getCanonicalLocales(attr.trim())[0]
      } catch (error) {
        /* An invalid tag falls back to the library locale. */
        locale = getLocale()
      }
    }
    return locale
  }

  _format(date, options) {
    const formatter = new Intl.DateTimeFormat(this._locale(), options)
    const formatted = formatter.format(date)
    return formatted
  }

  /* A date value formatted for this calendar, or "" when it is not a date. */
  _formatValue(value, options) {
    const parsed = parseChartDate(value)
    const formatted = parsed !== null ? this._format(parsed, options !== undefined ? options : { dateStyle: "medium" }) : ""
    return formatted
  }

  _firstDayOfWeek() {
    const parsed = parseInt(this.getAttribute("first-day-of-week"), 10)
    const day = Number.isInteger(parsed) === true && parsed >= 0 && parsed <= 6 ? parsed : 0
    return day
  }

  _weekStart(date) {
    let offset = date.getDay() - this._firstDayOfWeek()
    if (offset < 0) {
      offset = offset + 7
    }
    const start = new Date(date.getFullYear(), date.getMonth(), date.getDate() - offset)
    return start
  }

  /* The visible period: { start, end } as local-midnight dates (end inclusive). */
  _period() {
    const current = this._currentDate
    let period = null
    if (this._view === "week") {
      const start = this._weekStart(current)
      period = { start: start, end: new Date(start.getFullYear(), start.getMonth(), start.getDate() + 6) }
    } else {
      period = { start: new Date(current.getFullYear(), current.getMonth(), 1), end: new Date(current.getFullYear(), current.getMonth() + 1, 0) }
    }
    return period
  }

  _emitPeriodChange() {
    const period = this._period()
    this.emit("mj-period-change", { start: localDateKey(period.start), end: localDateKey(period.end), view: this._view })
    return
  }

  _navigate(delta) {
    const current = this._currentDate
    if (this._view === "week") {
      this._currentDate = new Date(current.getFullYear(), current.getMonth(), current.getDate() + delta * 7)
    } else {
      this._currentDate = new Date(current.getFullYear(), current.getMonth() + delta, 1)
    }
    this._renderCalendar()
    this._emitPeriodChange()
    return
  }

  _switchView(view) {
    const next = view === "week" ? "week" : "month"
    if (next === this._view) {
      return
    }
    this._view = next
    this._renderCalendar()
    this.emit("mj-view-change", { view: next })
    this._emitPeriodChange()
    return
  }

  /*
   * The events with their local day span: { source, index, name, type,
   * startKey, endKey, startTime }. Events without a usable start date get
   * null keys and appear only in the event list.
   */
  _events() {
    const source = this._data !== null && Array.isArray(this._data.events) === true ? this._data.events : []
    const events = source.map((event, index) => {
      const safe = event !== null && typeof event === "object" ? event : {}
      const startValue = safe.startDate !== undefined && safe.startDate !== null ? safe.startDate : safe.start
      const endValue = safe.endDate !== undefined && safe.endDate !== null ? safe.endDate : safe.end
      const start = parseChartDate(startValue)
      const end = parseChartDate(endValue)
      const startKey = start !== null ? localDateKey(start) : null
      let endKey = end !== null ? localDateKey(end) : startKey
      if (startKey !== null && endKey < startKey) {
        endKey = startKey
      }
      const hasName = safe.name !== undefined && safe.name !== null && toText(safe.name).length > 0
      const described = {
        source: event,
        index: index,
        name: hasName === true ? toText(safe.name) : t("mj.releaseCalendar.defaultEventName", { number: index + 1 }),
        type: safe.type !== undefined && safe.type !== null && toText(safe.type).length > 0 ? toText(safe.type) : "event",
        startValue: startValue,
        endValue: endValue,
        startKey: startKey,
        endKey: endKey,
        startTime: start !== null ? start.getTime() : Number.NaN,
        multiDay: startKey !== null && endKey !== startKey,
        description: safe.description,
        url: safe.url
      }
      return described
    })
    return events
  }

  _dateText(event, style) {
    const options = { dateStyle: style }
    const startText = this._formatValue(event.startValue, options)
    let text = startText.length > 0 ? startText : t("mj.releaseCalendar.noDate")
    if (event.multiDay === true) {
      text = t("mj.releaseCalendar.dateRange", { start: startText, end: this._formatValue(event.endValue, options) })
    }
    return text
  }

  _renderCalendar() {
    if (this._grid === undefined || this._grid === null) {
      return
    }

    const period = this._period()
    const month = this._currentDate.getMonth()
    const isWeek = this._view === "week"
    const todayKey = localDateKey(this._today())
    const highlightToday = this.enabledUnlessFalse("today-marker")
    const events = this._events()

    this._syncHeader(period)
    this._grid.setAttribute("data-view", this._view)
    setEmptyState(this, events.length === 0 ? "empty" : "ready")

    /* Cells: whole weeks covering the period. */
    const firstCell = this._weekStart(period.start)
    const lastCellWeekStart = this._weekStart(period.end)
    const lastCell = new Date(lastCellWeekStart.getFullYear(), lastCellWeekStart.getMonth(), lastCellWeekStart.getDate() + 6)
    const days = []
    for (let cursor = new Date(firstCell.getTime()); cursor <= lastCell; cursor = new Date(cursor.getFullYear(), cursor.getMonth(), cursor.getDate() + 1)) {
      days.push(cursor)
    }

    const headerCells = []
    for (let column = 0; column < 7; column = column + 1) {
      const sample = days[column]
      headerCells.push(html`<div class="day-header" role="columnheader" aria-label="${this._format(sample, { weekday: "long" })}">${this._format(sample, { weekday: "short" })}</div>`)
    }

    const maxChips = isWeek === true ? MAX_CHIPS_WEEK : MAX_CHIPS_MONTH
    const rows = [html`<div class="cal-row" role="row">${headerCells}</div>`]

    for (let weekStart = 0; weekStart < days.length; weekStart = weekStart + 7) {
      const cells = days.slice(weekStart, weekStart + 7).map((day) => {
        const dayKey = localDateKey(day)
        const dayEvents = events.filter((event) => event.startKey !== null && dayKey >= event.startKey && dayKey <= event.endKey)
        const inFreeze = dayEvents.some((event) => event.type === "freeze" || event.type === "blackout")
        const isToday = dayKey === todayKey && highlightToday === true
        const outside = isWeek === false && day.getMonth() !== month

        const chips = dayEvents.slice(0, maxChips).map((event) => {
          const colors = EVENT_COLORS[event.type] !== undefined ? EVENT_COLORS[event.type] : EVENT_COLORS.milestone
          const icon = EVENT_ICONS[event.type] !== undefined ? EVENT_ICONS[event.type] : EVENT_ICONS.milestone
          const label = t("mj.releaseCalendar.eventSummary", { name: event.name, type: typeText(event.type), date: this._dateText(event, "medium") })
          const selected = event.index === this._selectedEventIndex
          const chip = html`<button class="event-chip" part="event-chip" type="button" tabindex="-1" aria-label="${label}" aria-pressed="${selected === true ? "true" : "false"}" title="${label}" data-event-index="${event.index}" style="background:${colors.bg};border-color:${colors.border};color:${colors.text};"><span class="event-icon" aria-hidden="true">${icon}</span><span class="event-name" part="event-icon">${event.name}</span></button>`
          return chip
        })

        const overflow = dayEvents.length - maxChips
        const dateLabel = this._format(day, { weekday: "long", month: "long", day: "numeric", year: "numeric" })
        const moreButton = overflow > 0 ? html`<button class="more-btn" part="more-events" type="button" tabindex="-1" data-more-day="${dayKey}" aria-label="${t("mj.releaseCalendar.moreEventsLabel", { count: overflow, date: dateLabel })}">${t("mj.releaseCalendar.moreEvents", { count: overflow })}</button>` : html``

        const countText = dayEvents.length === 0 ? t("mj.releaseCalendar.noEventsCount") : t("mj.releaseCalendar.eventCount", { count: dayEvents.length })
        const cellLabel = inFreeze === true
          ? t("mj.releaseCalendar.dayLabelFreeze", { date: dateLabel, events: countText })
          : t("mj.releaseCalendar.dayLabel", { date: dateLabel, events: countText })
        const classes = `day-cell${isToday === true ? " today" : ""}${outside === true ? " other-month" : ""}`
        const cellPart = isToday === true ? "today-cell day-cell" : "day-cell"
        const cell = html`<div class="${classes}" part="${cellPart}" role="gridcell" tabindex="-1" aria-label="${cellLabel}" data-day="${dayKey}"${isToday === true ? html` aria-current="date"` : html``}><div class="day-num" aria-hidden="true">${String(day.getDate())}</div>${chips}${moreButton}</div>`
        return cell
      })
      rows.push(html`<div class="cal-row" role="row">${cells}</div>`)
    }

    /* Keep focus on the same day if it was inside the grid. */
    const active = this.shadowRoot.activeElement
    const hadFocus = active !== null && this._grid.contains(active) === true
    const focusedChip = hadFocus === true && active.hasAttribute("data-event-index") === true ? active.getAttribute("data-event-index") : null

    this._grid.innerHTML = String(html`${rows}`)
    this._syncRoving()

    if (hadFocus === true) {
      const cell = this._cellFor(this._focusedDay)
      let target = cell
      if (cell !== null && focusedChip !== null) {
        const chip = cell.querySelector(`[data-event-index="${focusedChip}"]`)
        target = chip !== null ? chip : cell
      }
      if (target !== null) {
        target.focus({ preventScroll: true })
      }
    }

    this._buildList(events)
    return
  }

  _syncHeader(period) {
    const isWeek = this._view === "week"
    let title = this._format(period.start, { month: "long", year: "numeric" })
    if (isWeek === true) {
      const formatter = new Intl.DateTimeFormat(this._locale(), { month: "short", day: "numeric", year: "numeric" })
      title = typeof formatter.formatRange === "function" ? formatter.formatRange(period.start, period.end) : `${formatter.format(period.start)} – ${formatter.format(period.end)}`
    }
    this._title.textContent = title
    this._prevBtn.setAttribute("aria-label", isWeek === true ? t("mj.releaseCalendar.previousWeek") : t("mj.releaseCalendar.previousMonth"))
    this._nextBtn.setAttribute("aria-label", isWeek === true ? t("mj.releaseCalendar.nextWeek") : t("mj.releaseCalendar.nextMonth"))
    this.$all(".view-btn").forEach((button) => {
      button.setAttribute("aria-pressed", button.getAttribute("data-view") === this._view ? "true" : "false")
    })
    return
  }

  _cellFor(dayKey) {
    let cell = null
    if (dayKey !== null && dayKey !== undefined) {
      cell = this._grid.querySelector(`.day-cell[data-day="${dayKey}"]`)
    }
    return cell
  }

  /*
   * One day cell is in the tab order: the focused day if it is shown, else
   * today, else the first day of the period. Its chips are reachable with
   * Tab; the chips of other days are not.
   */
  _syncRoving() {
    const period = this._period()
    let active = this._cellFor(this._focusedDay)
    if (active === null) {
      active = this._cellFor(localDateKey(this._today()))
    }
    if (active === null) {
      active = this._cellFor(localDateKey(period.start))
    }

    const cells = this._grid.querySelectorAll(".day-cell")
    for (let index = 0; index < cells.length; index = index + 1) {
      const cell = cells[index]
      const isActive = cell === active
      cell.setAttribute("tabindex", isActive === true ? "0" : "-1")
      const controls = cell.querySelectorAll("button")
      for (let position = 0; position < controls.length; position = position + 1) {
        controls[position].setAttribute("tabindex", isActive === true ? "0" : "-1")
      }
    }
    return
  }

  /* Move the grid focus to `date`, changing the period when it is not shown. */
  _focusDate(date) {
    const dayKey = localDateKey(date)
    this._focusedDay = dayKey
    let cell = this._cellFor(dayKey)
    const period = this._period()
    const insidePeriod = date >= period.start && date <= period.end

    if (cell === null || (insidePeriod === false && this._view === "week")) {
      this._currentDate = new Date(date.getFullYear(), date.getMonth(), date.getDate())
      this._renderCalendar()
      this._emitPeriodChange()
      cell = this._cellFor(dayKey)
    } else {
      this._syncRoving()
    }

    if (cell !== null) {
      cell.focus()
    }
    return
  }

  _onGridKeydown(event) {
    const cell = event.target.closest(".day-cell")
    if (cell === null || event.target !== cell) {
      return
    }

    const day = parseChartDate(cell.getAttribute("data-day"))
    let target = null

    if (event.key === "ArrowLeft") {
      target = new Date(day.getFullYear(), day.getMonth(), day.getDate() - 1)
    } else if (event.key === "ArrowRight") {
      target = new Date(day.getFullYear(), day.getMonth(), day.getDate() + 1)
    } else if (event.key === "ArrowUp") {
      target = new Date(day.getFullYear(), day.getMonth(), day.getDate() - 7)
    } else if (event.key === "ArrowDown") {
      target = new Date(day.getFullYear(), day.getMonth(), day.getDate() + 7)
    } else if (event.key === "Home") {
      target = this._weekStart(day)
    } else if (event.key === "End") {
      const start = this._weekStart(day)
      target = new Date(start.getFullYear(), start.getMonth(), start.getDate() + 6)
    } else if (event.key === "PageUp" || event.key === "PageDown") {
      const delta = event.key === "PageUp" ? -1 : 1
      const lastOfTarget = new Date(day.getFullYear(), day.getMonth() + delta + 1, 0).getDate()
      target = new Date(day.getFullYear(), day.getMonth() + delta, Math.min(day.getDate(), lastOfTarget))
    } else if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      this._openDay(cell.getAttribute("data-day"))
      return
    }

    if (target !== null) {
      event.preventDefault()
      this._focusDate(target)
    }
    return
  }

  _onGridClick(event) {
    const chip = event.target.closest("[data-event-index]")
    const more = event.target.closest("[data-more-day]")
    const cell = event.target.closest(".day-cell")

    if (cell !== null) {
      this._focusedDay = cell.getAttribute("data-day")
    }

    if (chip !== null) {
      const index = Number(chip.getAttribute("data-event-index"))
      const dayKey = cell !== null ? cell.getAttribute("data-day") : null
      this._openEvent(index, () => {
        const dayCell = this._cellFor(dayKey)
        const opener = dayCell !== null ? dayCell.querySelector(`[data-event-index="${index}"]`) : null
        return opener !== null ? opener : dayCell
      })
    } else if (more !== null) {
      this._openDay(more.getAttribute("data-more-day"))
    }
    return
  }

  /* The opener for an event opened from the day list: the day's cell. */
  _detailOpenerFinder() {
    const dayKey = this._focusedDay
    const finder = () => {
      const cell = this._cellFor(dayKey)
      return cell
    }
    return finder
  }

  /* List every event of one day in the detail panel. */
  _openDay(dayKey) {
    const day = parseChartDate(dayKey)
    if (day === null) {
      return
    }
    this._focusedDay = dayKey
    const dayEvents = this._events().filter((event) => event.startKey !== null && dayKey >= event.startKey && dayKey <= event.endKey)
    const items = dayEvents.map((event) => {
      const item = html`<li><button class="chart-button" type="button" data-event-index="${event.index}">${event.name}</button> ${typeText(event.type)}</li>`
      return item
    })
    const content = dayEvents.length > 0 ? html`<ul class="day-events">${items}</ul>` : html`<p>${t("mj.releaseCalendar.noEvents")}</p>`
    this._detail.open(this._format(day, { weekday: "long", month: "long", day: "numeric", year: "numeric" }), content, this._detailOpenerFinder())
    return
  }

  _openEvent(index, findOpener) {
    const event = this._events()[index]
    if (event === undefined) {
      return
    }

    this._selectedEvent = event.source
    this._selectedEventIndex = index
    this._syncChipSelection()

    const hasDescription = event.description !== undefined && event.description !== null && toText(event.description).length > 0
    const hasUrl = event.url !== undefined && event.url !== null && toText(event.url).length > 0
    const href = hasUrl === true ? safeUrl(toText(event.url), "") : ""
    const content = html`<p><strong>${t("mj.releaseCalendar.typeField")}</strong> ${typeText(event.type)}</p><p><strong>${t("mj.releaseCalendar.dateField")}</strong> ${this._dateText(event, "long")}</p>${hasDescription === true ? html`<p>${toText(event.description)}</p>` : html``}${href.length > 0 ? html`<p><a href="${href}" target="_blank" rel="noopener noreferrer">${t("mj.releaseCalendar.moreInfo")}<span class="mj-visually-hidden"> (${t("mj.releaseCalendar.opensInNewTab")})</span></a></p>` : html``}`
    this._detail.open(event.name, content, findOpener)
    this.emit("mj-event-select", { event: event.source })
    return
  }

  _syncChipSelection() {
    const chips = this._grid.querySelectorAll(".event-chip")
    for (let index = 0; index < chips.length; index = index + 1) {
      const selected = Number(chips[index].getAttribute("data-event-index")) === this._selectedEventIndex
      chips[index].setAttribute("aria-pressed", selected === true ? "true" : "false")
    }
    return
  }

  _onDetailClosed() {
    const hadSelection = this._selectedEvent !== null
    this._selectedEvent = null
    this._selectedEventIndex = -1
    this._syncChipSelection()
    if (hadSelection === true) {
      this.emit("mj-event-deselect", {})
    }
    return
  }

  _buildList(events) {
    const sorted = events.slice().sort((a, b) => {
      const left = Number.isNaN(a.startTime) === true ? Number.POSITIVE_INFINITY : a.startTime
      const right = Number.isNaN(b.startTime) === true ? Number.POSITIVE_INFINITY : b.startTime
      const order = left === right ? a.index - b.index : (left < right ? -1 : 1)
      return order
    })
    const items = sorted.map((event) => {
      const item = html`<li>${t("mj.releaseCalendar.eventSummary", { name: event.name, type: typeText(event.type), date: this._dateText(event, "medium") })}</li>`
      return item
    })
    this._listEl.innerHTML = String(html`${items}`)
    return
  }
}
