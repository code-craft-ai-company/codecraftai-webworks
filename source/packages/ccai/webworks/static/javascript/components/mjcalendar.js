/*
 * mjcalendar.js
 *
 * <mj-calendar> -- calendar grid in month, week, day, or agenda view.
 * Locale-aware date math, event rendering, keyboard navigation per the
 * WAI-ARIA grid pattern. Fires mj-date-select, mj-event-click,
 * mj-event-create (cancelable), mj-period-change and mj-view-change.
 *
 * Dates are calendar days in local time. `value`, `min` and `max` given as
 * `YYYY-MM-DD` are local days (never parsed as UTC), and every date the
 * component reports (`data-date`, event details) is the local `YYYY-MM-DD`.
 * The `value` attribute follows the displayed anchor date.
 *
 * Week and day views show the period's days with all of their events; the
 * hourly time grid of the spec is not implemented yet.
 *
 * Form participation: the element is form-associated. With a `name` it
 * submits the selected day (`YYYY-MM-DD`, nothing while no day is selected);
 * `required` makes it invalid until a day is selected. The `value`
 * attribute and property stay the displayed anchor date. Form reset clears
 * the selection; a disabled <fieldset> / form stops day selection.
 *
 * Keyboard (one day cell is the tab stop): arrows move by day / week,
 * Home / End to the start / end of the week, PageUp / PageDown to the
 * previous / next month (Shift: year), crossing into other periods as
 * needed; Enter / Space select the focused day. Event chips are buttons and
 * keep their own Enter / Space.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { announce } from "../core/announcer.js";
import { getLocale, t } from "../core/intl.js";

const STYLES = `
:host {
  display: flex;
  flex-direction: column;
  font: inherit;
  color: var(--mj-text);
  background: var(--mj-surface);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-md);
  overflow: hidden;
}

.cal-header {
  display: flex;
  align-items: center;
  gap: var(--mj-space-3);
  padding: var(--mj-space-3);
  border-block-end: 1px solid var(--mj-border);
  background: var(--mj-bg-subtle);
}

.cal-header .period-label {
  font-weight: var(--mj-font-weight-medium);
  flex: 1;
}

.nav-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem; height: 2rem;
  background: none;
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-sm);
  cursor: pointer;
  color: var(--mj-text);
  font-size: 1rem;
}
.nav-btn:hover { background: var(--mj-bg-muted); }
.nav-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.view-switcher {
  display: flex;
  gap: var(--mj-space-1);
}
.view-btn {
  padding: var(--mj-space-1) var(--mj-space-2);
  background: none;
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-sm);
  cursor: pointer;
  font: inherit;
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text);
}
.view-btn.active {
  background: var(--mj-accent);
  color: var(--mj-text-on-accent);
  border-color: var(--mj-accent);
}
.view-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.cal-grid {
  flex: 1;
  overflow: auto;
  outline: none;
}
.cal-grid:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); }

.weekday-headers {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  border-block-end: 1px solid var(--mj-border);
}
.cal-grid[data-view="day"] .weekday-headers,
.cal-grid[data-view="day"] .week-row { grid-template-columns: 1fr; }
.cal-grid[data-view="week"] .week-row,
.cal-grid[data-view="day"] .week-row { min-height: var(--mj-cal-period-min-height, 240px); }

.weekday-header {
  padding: var(--mj-space-2);
  text-align: center;
  font-size: var(--mj-font-size-xs);
  font-weight: var(--mj-font-weight-medium);
  color: var(--mj-text-muted);
  border-inline-end: 1px solid var(--mj-border);
}
.weekday-header:last-child { border-inline-end: none; }

.month-grid {
  display: flex;
  flex-direction: column;
}

.week-row {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  border-block-end: 1px solid var(--mj-border);
  min-height: var(--mj-cal-cell-min-height, 80px);
}
.week-row:last-child { border-block-end: none; }

.day-cell {
  padding: var(--mj-space-1) var(--mj-space-2);
  border-inline-end: 1px solid var(--mj-border);
  cursor: pointer;
  min-width: 0;
  min-height: var(--mj-cal-cell-min-height, 80px);
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.day-cell:last-child { border-inline-end: none; }
.day-cell:hover { background: var(--mj-bg-muted); }
.day-cell:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: -2px;
}
.day-cell[aria-current="date"] { background: var(--mj-cal-today-bg, color-mix(in srgb, var(--mj-accent) 10%, transparent)); }
.day-cell[aria-selected="true"] { background: color-mix(in srgb, var(--mj-accent) 15%, transparent); }
.day-cell[aria-disabled="true"] { opacity: var(--mj-cal-other-month-opacity, 0.4); pointer-events: none; }
.day-cell.other-month { opacity: var(--mj-cal-other-month-opacity, 0.4); }

.day-number {
  font-size: var(--mj-font-size-xs);
  font-weight: var(--mj-font-weight-medium);
  line-height: 1.4;
}

/*
 * An event's colour (--mj-cal-event-color, written on the chip from the
 * event's color field) is the start stripe and a light tint of the surface
 * behind the text. The text stays --mj-text, so it keeps its contrast with
 * any colour in both themes (a solid fill under fixed text cannot).
 */
.event-chip {
  display: block;
  background: color-mix(in srgb, var(--mj-cal-event-color, var(--mj-accent)) 18%, var(--mj-surface));
  color: var(--mj-text);
  border-radius: var(--mj-cal-event-radius, var(--mj-radius-sm));
  padding: 1px 4px;
  font-size: 0.7rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;
  border: none;
  border-inline-start: 3px solid var(--mj-cal-event-color, var(--mj-accent));
  width: 100%;
  text-align: start;
}
.event-chip:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: 1px;
}

.overflow-btn {
  font-size: 0.7rem;
  color: var(--mj-text-muted);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  text-align: start;
}
.overflow-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}

.status-region {
  position: absolute; width: 1px; height: 1px;
  overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap;
}

.agenda-list {
  padding: var(--mj-space-3);
  display: flex;
  flex-direction: column;
  gap: var(--mj-space-3);
}
.agenda-date { font-weight: var(--mj-font-weight-medium); font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }
.agenda-event {
  display: block;
  inline-size: 100%;
  padding: var(--mj-space-2) var(--mj-space-3);
  border: none;
  border-inline-start: 3px solid var(--mj-cal-event-color, var(--mj-accent));
  background: var(--mj-bg-subtle);
  border-start-start-radius: 0;
  border-end-start-radius: 0;
  border-start-end-radius: var(--mj-radius-sm);
  border-end-end-radius: var(--mj-radius-sm);
  cursor: pointer;
  font: inherit;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
  text-align: start;
}
.agenda-empty { color: var(--mj-text-muted); }
.agenda-event:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); }
`;

const VIEWS = ["month", "week", "day", "agenda"];

/* Label key of each view-switcher button, by its data-view. */
const VIEW_LABEL_KEYS = {
  month: "mj.calendar.viewMonth",
  week: "mj.calendar.viewWeek",
  day: "mj.calendar.viewDay",
  agenda: "mj.calendar.viewAgenda"
};

const DATE_ONLY_PATTERN = /^(\d{4})-(\d{2})-(\d{2})$/;

/* A known Sunday, used to read weekday names from Intl. */
const REFERENCE_SUNDAY = new Date(2024, 0, 7);

/*
 * Parse a date value. `YYYY-MM-DD` text is a local calendar day; other
 * text and numbers go through Date. Returns null when unusable.
 */
function toDate(value) {
  let date = null

  /* Tag check rather than instanceof: Dates may come from another frame. */
  if (Object.prototype.toString.call(value) === "[object Date]") {
    date = new Date(value.getTime())
  } else if (typeof value === "string") {
    const match = value.trim().match(DATE_ONLY_PATTERN)
    if (match !== null) {
      date = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]))
    } else if (value.trim().length > 0) {
      date = new Date(value)
    }
  } else if (typeof value === "number") {
    date = new Date(value)
  }

  if (date !== null && Number.isNaN(date.getTime()) === true) {
    date = null
  }
  return date
}

function startOfDay(date) {
  const day = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  return day
}

function addDays(date, count) {
  const moved = new Date(date.getFullYear(), date.getMonth(), date.getDate() + count)
  return moved
}

/* Move by whole months, keeping the day of month where it exists (31 Jan + 1 = 29 Feb). */
function addMonths(date, count) {
  const firstOfTarget = new Date(date.getFullYear(), date.getMonth() + count, 1)
  const daysInTarget = new Date(firstOfTarget.getFullYear(), firstOfTarget.getMonth() + 1, 0).getDate()
  const moved = new Date(firstOfTarget.getFullYear(), firstOfTarget.getMonth(), Math.min(date.getDate(), daysInTarget))
  return moved
}

/* The local calendar day of a date as `YYYY-MM-DD`. */
function dateKey(date) {
  const month = String(date.getMonth() + 1).padStart(2, "0")
  const day = String(date.getDate()).padStart(2, "0")
  const key = `${date.getFullYear()}-${month}-${day}`
  return key
}

export class MjCalendar extends FormControlMixin(MjElement) {
  static tagName = "mj-calendar";
  static styles = STYLES;
  static watched = ["view", "value", "min", "max", "first-day-of-week", "locale", "loading", "event-overflow", "readonly", "required"];

  constructor() {
    super()
    this._initFormControl()

    /* True while an ancestor <fieldset disabled> (or form) disables the calendar. */
    this._formDisabled = false
    this._events = []
    this._dataSource = null
    this._currentDate = startOfDay(new Date())
    this._anchorFromValue = null

    /* Day keys (`YYYY-MM-DD`): keyboard focus, selection, expanded "+N more". */
    this._focusedDate = null
    this._selectedDate = null
    this._expandedDate = null

    this._reflectingValue = false
    this._fetchGeneration = 0
    this._gridId = nextId("mj-cal-grid")
  }

  render() {
    const markup = `
      <div class="cal-header" part="header">
        <slot name="toolbar-start"></slot>
        <button type="button" class="nav-btn" part="prev-button">&#8249;</button>
        <span class="period-label" aria-live="polite" aria-atomic="true"></span>
        <button type="button" class="nav-btn" part="next-button">&#8250;</button>
        <div class="view-switcher" part="view-switcher" role="group">
          <button type="button" class="view-btn" data-view="month"></button>
          <button type="button" class="view-btn" data-view="week"></button>
          <button type="button" class="view-btn" data-view="day"></button>
          <button type="button" class="view-btn" data-view="agenda"></button>
        </div>
        <slot name="toolbar-end"></slot>
      </div>
      <div class="cal-grid" part="grid" id="${this._gridId}"></div>
    `
    return markup
  }

  afterRender() {
    this._header = this.$(".cal-header")
    this._periodLabel = this.$(".period-label")
    this._calGrid = this.$(".cal-grid")

    const prevBtn = this.$("[part='prev-button']")
    const nextBtn = this.$("[part='next-button']")
    prevBtn.setAttribute("aria-label", t("core.previous"))
    nextBtn.setAttribute("aria-label", t("core.next"))
    this.listen(prevBtn, "click", () => { this._navigate(-1) })
    this.listen(nextBtn, "click", () => { this._navigate(1) })
    this.$(".view-switcher").setAttribute("aria-label", t("mj.calendar.viewSwitcherLabel"))
    const viewBtns = this.$all(".view-btn")
    for (let i = 0; i < viewBtns.length; i = i + 1) {
      viewBtns[i].textContent = t(VIEW_LABEL_KEYS[viewBtns[i].getAttribute("data-view")])
    }
    this.listen(this.$(".view-switcher"), "click", this._onViewButtonClick.bind(this))

    this.listen(this._calGrid, "keydown", this._onGridKeydown.bind(this))
    this.listen(this._calGrid, "click", this._onGridClick.bind(this))

    /* The anchor survives a reconnect; `value` is reflected from it. */
    const valueDate = toDate(this.getAttribute("value"))
    if (valueDate !== null) {
      this._currentDate = startOfDay(valueDate)
    }

    this._syncViewButtons()
    this._buildGrid()

    if (this._dataSource !== null) {
      this._fetchEvents()
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "required") {
      this._refreshValidity()
    }
    if (this._calGrid === undefined || this._calGrid === null) {
      return
    }
    if (name === "view") {
      this._syncViewButtons()
      this._buildGrid()
      if (this._dataSource !== null) {
        this._fetchEvents()
      }
    }
    if (name === "value" && this._reflectingValue === false) {
      const date = toDate(newValue)
      if (date !== null && dateKey(date) !== dateKey(this._currentDate)) {
        this._currentDate = startOfDay(date)
        this._buildGrid()
        if (this._dataSource !== null) {
          this._fetchEvents()
        }
      }
    }
    if (name === "min" || name === "max" || name === "first-day-of-week" || name === "locale" || name === "event-overflow") {
      this._buildGrid()
    }
    if (name === "loading") {
      this._calGrid.setAttribute("aria-busy", newValue !== null ? "true" : "false")
    }
    return
  }

  /* ----- readers ----- */

  _view() {
    const view = this.getAttribute("view") || "month"
    const known = VIEWS.indexOf(view) >= 0 ? view : "month"
    return known
  }

  /* The `locale` attribute when it is a valid BCP 47 tag, else the library locale. */
  _locale() {
    let locale = getLocale()
    const requested = this.getAttribute("locale")
    if (requested !== null && requested.trim().length > 0) {
      try {
        locale = Intl.getCanonicalLocales(requested.trim())[0]
      } catch (error) {
        locale = getLocale()
      }
    }
    return locale
  }

  /* `first-day-of-week`, else the locale's week start, else Sunday. */
  _firstDayOfWeek() {
    const attr = parseInt(this.getAttribute("first-day-of-week") || "", 10)
    let first = 0
    if (Number.isNaN(attr) === false && attr >= 0 && attr <= 6) {
      first = attr
    } else {
      try {
        const info = new Intl.Locale(this._locale())
        const weekInfo = typeof info.getWeekInfo === "function" ? info.getWeekInfo() : info.weekInfo
        if (weekInfo !== undefined && weekInfo !== null && typeof weekInfo.firstDay === "number") {
          first = weekInfo.firstDay % 7
        }
      } catch (error) {
        first = 0
      }
    }
    return first
  }

  _weekdayName(dow, style) {
    const date = addDays(REFERENCE_SUNDAY, dow)
    const name = new Intl.DateTimeFormat(this._locale(), { weekday: style }).format(date)
    return name
  }

  _limitDate(name) {
    const date = toDate(this.getAttribute(name))
    const limit = date !== null ? startOfDay(date) : null
    return limit
  }

  _isDisabledDate(date) {
    const minDate = this._limitDate("min")
    const maxDate = this._limitDate("max")
    let disabled = false
    if (minDate !== null && date < minDate) {
      disabled = true
    }
    if (maxDate !== null && date > maxDate) {
      disabled = true
    }
    return disabled
  }

  /* ----- period ----- */

  _getPeriodStart() {
    const view = this._view()
    const d = this._currentDate
    let start = startOfDay(d)
    if (view === "month" || view === "agenda") {
      start = new Date(d.getFullYear(), d.getMonth(), 1)
    } else if (view === "week") {
      const diff = (d.getDay() - this._firstDayOfWeek() + 7) % 7
      start = addDays(d, -diff)
    }
    return start
  }

  _getPeriodEnd() {
    const view = this._view()
    const d = this._currentDate
    let end = startOfDay(d)
    if (view === "month" || view === "agenda") {
      end = new Date(d.getFullYear(), d.getMonth() + 1, 0)
    } else if (view === "week") {
      end = addDays(this._getPeriodStart(), 6)
    }
    return end
  }

  _isInPeriod(date) {
    const inPeriod = date >= this._getPeriodStart() && date <= this._getPeriodEnd()
    return inPeriod
  }

  _navigate(delta) {
    const view = this._view()
    let next = this._currentDate
    if (view === "month" || view === "agenda") {
      next = addMonths(this._currentDate, delta)
    } else if (view === "week") {
      next = addDays(this._currentDate, delta * 7)
    } else {
      next = addDays(this._currentDate, delta)
    }
    this._setAnchor(next)
    return
  }

  /* Show the period that contains `date`, reflect it to `value`, report it. */
  _setAnchor(date) {
    const previousStart = dateKey(this._getPeriodStart())
    this._currentDate = startOfDay(date)

    this._reflectingValue = true
    this.setAttribute("value", dateKey(this._currentDate))
    this._reflectingValue = false

    this._buildGrid()
    if (dateKey(this._getPeriodStart()) !== previousStart) {
      if (this._dataSource !== null) {
        this._fetchEvents()
      }
      announce(t("mj.calendar.showingPeriod", { period: this._periodLabel.textContent }))
      this.emit("mj-period-change", {
        start: dateKey(this._getPeriodStart()),
        end: dateKey(this._getPeriodEnd()),
        view: this._view()
      })
    }
    return
  }

  _fetchEvents() {
    if (this._dataSource === null || typeof this._dataSource.fetchEvents !== "function") {
      return
    }
    this._fetchGeneration = this._fetchGeneration + 1
    const generation = this._fetchGeneration
    this.reflectBoolean("loading", true)

    const start = this._getPeriodStart()
    const end = this._getPeriodEnd()
    let pending = null
    try {
      pending = Promise.resolve(this._dataSource.fetchEvents(start, end))
    } catch (error) {
      pending = Promise.reject(error)
    }
    pending.then((evts) => {
      if (generation !== this._fetchGeneration) {
        return
      }
      this.reflectBoolean("loading", false)
      this._events = Array.isArray(evts) === true ? evts : []
      this._buildGrid()
      return
    }).catch((error) => {
      if (generation !== this._fetchGeneration) {
        return
      }
      this.reflectBoolean("loading", false)
      this.emit("mj-load-error", { error: error })
    })
    return
  }

  /* ----- events data ----- */

  /*
   * The local days an event covers: { start, end, firstDay, lastDay }, or
   * null when its start is unusable. A missing or invalid end means the
   * event ends when it starts; an end at midnight does not cover that day.
   */
  _eventRange(ev) {
    const start = ev !== null && ev !== undefined ? toDate(ev.start) : null
    if (start === null) {
      return null
    }
    let end = toDate(ev.end)
    if (end === null || end < start) {
      end = start
    }
    let lastDay = startOfDay(end)
    if (end > start && end.getTime() === lastDay.getTime()) {
      lastDay = addDays(lastDay, -1)
    }
    const range = { start: start, end: end, firstDay: startOfDay(start), lastDay: lastDay, hasEnd: toDate(ev.end) !== null }
    return range
  }

  /* Events touching `date`, earliest first, as { ev, index, range }. */
  _getEventsForDate(date) {
    const matching = []
    for (let i = 0; i < this._events.length; i = i + 1) {
      const range = this._eventRange(this._events[i])
      if (range !== null && range.firstDay <= date && date <= range.lastDay) {
        matching.push({ ev: this._events[i], index: i, range: range })
      }
    }
    matching.sort((a, b) => a.range.start - b.range.start)
    return matching
  }

  /* ----- rendering ----- */

  _syncViewButtons() {
    const view = this._view()
    const btns = this.$all(".view-btn")
    for (let i = 0; i < btns.length; i = i + 1) {
      const active = btns[i].getAttribute("data-view") === view
      btns[i].className = active === true ? "view-btn active" : "view-btn"
      btns[i].setAttribute("aria-pressed", active === true ? "true" : "false")
    }
    return
  }

  _onViewButtonClick(event) {
    const btn = event.target instanceof Element ? event.target.closest(".view-btn") : null
    if (btn === null) {
      return
    }
    const view = btn.getAttribute("data-view")
    if (view !== this._view()) {
      this.setAttribute("view", view)
      this.emit("mj-view-change", { view: view })
      announce(t("mj.calendar.showingPeriod", { period: this._periodLabel.textContent }))
    }
    return
  }

  _buildGrid() {
    const view = this._view()
    const focusWasInGrid = this._calGrid.contains(this.shadowRoot.activeElement)
    const focusedOverflow = focusWasInGrid === true && this.shadowRoot.activeElement.classList.contains("overflow-btn")

    this._calGrid.replaceChildren()
    this._calGrid.setAttribute("data-view", view)
    this._updatePeriodLabel()

    if (view === "agenda") {
      /* A list of buttons, not a grid of cells. */
      this._calGrid.setAttribute("role", "region")
      this._buildAgendaView()
    } else {
      this._calGrid.setAttribute("role", "grid")
      const periodStart = this._getPeriodStart()
      if (view === "month") {
        const firstDow = this._firstDayOfWeek()
        const offset = (periodStart.getDay() - firstDow + 7) % 7
        this._buildDayGrid(addDays(periodStart, -offset), 7, 6, true)
      } else if (view === "week") {
        this._buildDayGrid(periodStart, 7, 1, false)
      } else {
        this._buildDayGrid(periodStart, 1, 1, false)
      }
      this._syncTabStop()
      if (focusWasInGrid === true) {
        const target = focusedOverflow === true
          ? this._cellFor(this._focusedDate) !== null ? this._cellFor(this._focusedDate).querySelector(".overflow-btn") : null
          : this._cellFor(this._focusedDate)
        if (target !== null) {
          target.focus()
        }
      }
    }
    return
  }

  _updatePeriodLabel() {
    const view = this._view()
    const locale = this._locale()
    const d = this._currentDate
    let label = ""

    if (view === "month" || view === "agenda") {
      label = new Intl.DateTimeFormat(locale, { month: "long", year: "numeric" }).format(d)
    } else if (view === "week") {
      const start = this._getPeriodStart()
      const end = this._getPeriodEnd()
      label = `${new Intl.DateTimeFormat(locale, { month: "short", day: "numeric" }).format(start)} – ${new Intl.DateTimeFormat(locale, { month: "short", day: "numeric", year: "numeric" }).format(end)}`
    } else {
      label = new Intl.DateTimeFormat(locale, { weekday: "long", month: "long", day: "numeric", year: "numeric" }).format(d)
    }

    this._periodLabel.textContent = label
    this._calGrid.setAttribute("aria-label", t("mj.calendar.gridLabel", { period: label }))
    return
  }

  /*
   * Rows of day cells starting at `firstDate`, `columns` per row. In month
   * view (`isMonth`) trailing rows that hold no day of the month are left out.
   */
  _buildDayGrid(firstDate, columns, rows, isMonth) {
    const month = this._currentDate.getMonth()

    const headerRow = document.createElement("div")
    headerRow.className = "weekday-headers"
    headerRow.setAttribute("role", "row")
    for (let d = 0; d < columns; d = d + 1) {
      const dow = addDays(firstDate, d).getDay()
      const cell = document.createElement("div")
      cell.className = "weekday-header"
      cell.setAttribute("role", "columnheader")
      cell.setAttribute("aria-label", this._weekdayName(dow, "long"))
      cell.textContent = this._weekdayName(dow, "short")
      headerRow.appendChild(cell)
    }
    this._calGrid.appendChild(headerRow)

    const body = document.createElement("div")
    body.className = "month-grid"
    body.setAttribute("role", "rowgroup")

    for (let week = 0; week < rows; week = week + 1) {
      const weekRow = document.createElement("div")
      weekRow.className = "week-row"
      weekRow.setAttribute("part", "week-row")
      weekRow.setAttribute("role", "row")
      let hasCurrentMonth = false

      for (let d = 0; d < columns; d = d + 1) {
        const cellDate = addDays(firstDate, week * columns + d)
        const otherMonth = isMonth === true && cellDate.getMonth() !== month
        if (otherMonth === false) {
          hasCurrentMonth = true
        }
        weekRow.appendChild(this._buildDayCell(cellDate, otherMonth, isMonth))
      }

      if (hasCurrentMonth === true || week === 0) {
        body.appendChild(weekRow)
      }
    }

    this._calGrid.appendChild(body)
    return
  }

  _buildDayCell(cellDate, otherMonth, limitEvents) {
    const locale = this._locale()
    const key = dateKey(cellDate)
    const parts = ["day-cell"]

    const cell = document.createElement("div")
    cell.className = otherMonth === true ? "day-cell other-month" : "day-cell"
    cell.setAttribute("role", "gridcell")
    cell.setAttribute("tabindex", "-1")
    cell.setAttribute("data-date", key)

    if (key === dateKey(new Date())) {
      cell.setAttribute("aria-current", "date")
      parts.push("day-cell-today")
    }
    if (otherMonth === true) {
      parts.push("day-cell-other-month")
    }
    cell.setAttribute("part", parts.join(" "))

    if (this._isDisabledDate(cellDate) === true) {
      cell.setAttribute("aria-disabled", "true")
    }
    if (key === this._selectedDate) {
      cell.setAttribute("aria-selected", "true")
    }

    const dayNum = document.createElement("span")
    dayNum.className = "day-number"
    dayNum.setAttribute("part", "day-number")
    dayNum.setAttribute("aria-hidden", "true")
    dayNum.textContent = String(cellDate.getDate())
    cell.appendChild(dayNum)

    const dayEvents = this._getEventsForDate(cellDate)
    const parsedMax = parseInt(this.getAttribute("event-overflow") || "3", 10)
    const maxVisible = Number.isNaN(parsedMax) === true || parsedMax < 0 ? 3 : parsedMax
    const expanded = limitEvents === false || this._expandedDate === key
    const visibleEvents = expanded === true ? dayEvents : dayEvents.slice(0, maxVisible)
    const hiddenCount = dayEvents.length - visibleEvents.length

    for (let ei = 0; ei < visibleEvents.length; ei = ei + 1) {
      cell.appendChild(this._buildEventChip(visibleEvents[ei]))
    }

    if (hiddenCount > 0 || (expanded === true && limitEvents === true && dayEvents.length > maxVisible)) {
      const overflowBtn = document.createElement("button")
      overflowBtn.type = "button"
      overflowBtn.className = "overflow-btn"
      overflowBtn.setAttribute("part", "event-overflow")
      overflowBtn.setAttribute("tabindex", "-1")
      overflowBtn.setAttribute("aria-expanded", expanded === true ? "true" : "false")
      if (expanded === true) {
        overflowBtn.textContent = t("mj.calendar.showLess")
      } else {
        overflowBtn.setAttribute("aria-label", t("mj.calendar.moreEventsLabel", { count: hiddenCount }))
        overflowBtn.textContent = t("mj.calendar.moreEvents", { count: hiddenCount })
      }
      cell.appendChild(overflowBtn)
    }

    const dateText = new Intl.DateTimeFormat(locale, { weekday: "long", day: "numeric", month: "long", year: "numeric" }).format(cellDate)
    const eventCount = dayEvents.length
    cell.setAttribute("aria-label", eventCount > 0 ? t("mj.calendar.dayWithEvents", { date: dateText, count: eventCount }) : dateText)
    return cell
  }

  _buildEventChip(entry) {
    const ev = entry.ev
    const range = entry.range
    const title = ev.title !== undefined && ev.title !== null ? String(ev.title) : ""
    const timeFormat = new Intl.DateTimeFormat(this._locale(), { hour: "numeric", minute: "2-digit" })

    const chip = document.createElement("button")
    chip.type = "button"
    chip.className = "event-chip"
    chip.setAttribute("part", "event-chip")
    chip.setAttribute("data-event-index", String(entry.index))
    chip.setAttribute("tabindex", "-1")
    let timeStr = timeFormat.format(range.start)
    if (range.hasEnd === true && range.end > range.start) {
      timeStr = `${timeStr}–${timeFormat.format(range.end)}`
    }
    chip.setAttribute("aria-label", t("mj.calendar.eventLabel", { title: title, time: timeStr }))
    chip.textContent = title
    if (ev.color !== undefined && ev.color !== null) {
      chip.style.setProperty("--mj-cal-event-color", String(ev.color))
    }
    return chip
  }

  /* Events of the displayed month, grouped by their first day in it. */
  _buildAgendaView() {
    const list = document.createElement("div")
    list.className = "agenda-list"
    list.setAttribute("role", "list")

    const periodStart = this._getPeriodStart()
    const periodEnd = this._getPeriodEnd()
    const entries = []
    for (let i = 0; i < this._events.length; i = i + 1) {
      const range = this._eventRange(this._events[i])
      if (range !== null && range.firstDay <= periodEnd && range.lastDay >= periodStart) {
        const listDay = range.firstDay < periodStart ? periodStart : range.firstDay
        entries.push({ ev: this._events[i], index: i, range: range, listDay: listDay })
      }
    }
    entries.sort((a, b) => (a.listDay - b.listDay) || (a.range.start - b.range.start))

    if (entries.length === 0) {
      const empty = document.createElement("div")
      empty.className = "agenda-empty"
      empty.setAttribute("role", "listitem")
      empty.textContent = t("mj.calendar.noEvents")
      list.appendChild(empty)
    }

    const dayFormat = new Intl.DateTimeFormat(this._locale(), { dateStyle: "medium" })
    let lastKey = ""
    let group = null
    for (let i = 0; i < entries.length; i = i + 1) {
      const entry = entries[i]
      const key = dateKey(entry.listDay)
      if (key !== lastKey) {
        group = document.createElement("div")
        group.setAttribute("role", "listitem")
        const dateLabel = document.createElement("div")
        dateLabel.className = "agenda-date"
        dateLabel.textContent = dayFormat.format(entry.listDay)
        group.appendChild(dateLabel)
        list.appendChild(group)
        lastKey = key
      }

      const evEl = document.createElement("button")
      evEl.type = "button"
      evEl.className = "agenda-event"
      evEl.setAttribute("data-event-index", String(entry.index))
      evEl.textContent = entry.ev.title !== undefined && entry.ev.title !== null ? String(entry.ev.title) : ""
      if (entry.ev.color !== undefined && entry.ev.color !== null) {
        evEl.style.setProperty("--mj-cal-event-color", String(entry.ev.color))
      }
      group.appendChild(evEl)
    }

    this._calGrid.appendChild(list)
    return
  }

  /* ----- focus and selection ----- */

  _cellFor(key) {
    let found = null
    if (key !== null && key !== undefined) {
      const cells = this._calGrid.querySelectorAll(".day-cell")
      for (let i = 0; i < cells.length; i = i + 1) {
        if (cells[i].getAttribute("data-date") === key) {
          found = cells[i]
          break
        }
      }
    }
    return found
  }

  /*
   * One day cell is the tab stop: the focused day, else the selected day,
   * else the anchor day, else the first day of the period.
   */
  _syncTabStop() {
    const candidates = [this._focusedDate, this._selectedDate, dateKey(this._currentDate), dateKey(this._getPeriodStart())]
    let target = null
    for (let i = 0; i < candidates.length && target === null; i = i + 1) {
      const cell = this._cellFor(candidates[i])
      if (cell !== null && cell.classList.contains("other-month") === false) {
        target = cell
      }
    }
    if (target !== null) {
      target.tabIndex = 0
      this._focusedDate = target.getAttribute("data-date")
    }
    return
  }

  /* Focus the cell of `date`, showing the period that contains it first. */
  _focusDate(date) {
    const key = dateKey(date)
    const view = this._view()
    let needsNewPeriod = this._isInPeriod(date) === false
    if (view === "day") {
      needsNewPeriod = key !== dateKey(this._currentDate)
    }

    this._focusedDate = key
    if (needsNewPeriod === true) {
      this._setAnchor(date)
    } else {
      const cells = this._calGrid.querySelectorAll(".day-cell[tabindex='0']")
      for (let i = 0; i < cells.length; i = i + 1) {
        cells[i].tabIndex = -1
      }
    }
    const cell = this._cellFor(key)
    if (cell !== null) {
      cell.tabIndex = 0
      cell.focus()
    }
    return
  }

  /*
   * The user activated a day. In an editable calendar that is a request to
   * create an event on it: `mj-event-create` is emitted first and its
   * default action is the selection itself (selected day, form value,
   * `mj-date-select`), so preventDefault() leaves the calendar as it was. A
   * readonly calendar selects without asking.
   */
  _selectDate(key) {
    const cell = this._cellFor(key)
    if (cell === null || cell.getAttribute("aria-disabled") === "true") {
      return
    }
    if (this.hasAttribute("disabled") === true || this._formDisabled === true) {
      return
    }

    this._focusedDate = key
    if (this.hasAttribute("readonly") === false) {
      const proceed = this.emit("mj-event-create", { date: key }, { cancelable: true })
      if (proceed === false) {
        return
      }
    }

    /* A listener may have changed the period, so the cell is looked up again. */
    const target = this._cellFor(key)
    this._selectedDate = key
    this._setFormValue(key)
    const selected = this._calGrid.querySelectorAll(".day-cell[aria-selected]")
    for (let i = 0; i < selected.length; i = i + 1) {
      selected[i].removeAttribute("aria-selected")
    }
    if (target !== null) {
      target.setAttribute("aria-selected", "true")
    }

    this.emit("mj-date-select", { date: key })
    return
  }

  _emitEventClick(element) {
    const ev = this._events[parseInt(element.getAttribute("data-event-index"), 10)]
    if (ev !== undefined) {
      this.emit("mj-event-click", { eventId: ev.id, event: ev })
    }
    return
  }

  _onGridClick(event) {
    const target = event.target instanceof Element ? event.target : null
    if (target === null) {
      return
    }
    const chip = target.closest(".event-chip, .agenda-event")
    const overflowBtn = target.closest(".overflow-btn")
    const cell = target.closest(".day-cell")

    if (chip !== null) {
      this._emitEventClick(chip)
    } else if (overflowBtn !== null && cell !== null) {
      /* "+N more" expands the day in place; "Show less" collapses it. */
      const key = cell.getAttribute("data-date")
      this._expandedDate = this._expandedDate === key ? null : key
      this._focusedDate = key
      this._buildGrid()
      const rebuilt = this._cellFor(key)
      const button = rebuilt !== null ? rebuilt.querySelector(".overflow-btn") : null
      if (button !== null) {
        button.focus()
      }
    } else if (cell !== null) {
      this._selectDate(cell.getAttribute("data-date"))
    }
    return
  }

  _onGridKeydown(event) {
    const target = event.target
    /* Keys pressed on an event chip or overflow button belong to that button. */
    if (!(target instanceof Element) || target.classList.contains("day-cell") === false) {
      return
    }
    const current = toDate(target.getAttribute("data-date"))
    if (current === null) {
      return
    }
    const rtl = window.getComputedStyle(this).direction === "rtl"
    const forward = rtl === true ? -1 : 1
    const firstDow = this._firstDayOfWeek()
    const weekOffset = (current.getDay() - firstDow + 7) % 7
    let next = null

    if (event.key === "ArrowLeft") {
      next = addDays(current, -forward)
    } else if (event.key === "ArrowRight") {
      next = addDays(current, forward)
    } else if (event.key === "ArrowUp") {
      next = addDays(current, -7)
    } else if (event.key === "ArrowDown") {
      next = addDays(current, 7)
    } else if (event.key === "Home") {
      next = addDays(current, -weekOffset)
    } else if (event.key === "End") {
      next = addDays(current, 6 - weekOffset)
    } else if (event.key === "PageUp") {
      next = addMonths(current, event.shiftKey === true ? -12 : -1)
    } else if (event.key === "PageDown") {
      next = addMonths(current, event.shiftKey === true ? 12 : 1)
    } else if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      this._selectDate(target.getAttribute("data-date"))
      return
    } else {
      return
    }

    event.preventDefault()
    this._focusDate(next)
    return
  }

  /* ----- form participation ----- */

  /* Select `key` (`YYYY-MM-DD`) or clear the selection (null) without events. */
  _applySelection(key) {
    this._selectedDate = key
    this._setFormValue(key)
    if (this._calGrid !== undefined && this._calGrid !== null) {
      const selected = this._calGrid.querySelectorAll(".day-cell[aria-selected]")
      for (let i = 0; i < selected.length; i = i + 1) {
        selected[i].removeAttribute("aria-selected")
      }
      const cell = key !== null ? this._cellFor(key) : null
      if (cell !== null) {
        cell.setAttribute("aria-selected", "true")
      }
    }
    return
  }

  formResetCallback() {
    this._applySelection(null)
    return
  }

  formStateRestoreCallback(state) {
    const date = typeof state === "string" ? toDate(state) : null
    this._applySelection(date !== null ? dateKey(date) : null)
    return
  }

  onFormDisabled(disabled) {
    this._formDisabled = disabled === true
    return
  }

  /* ----- scriptable API ----- */

  /* The displayed anchor date as `YYYY-MM-DD` (the `value` attribute). */
  get value() {
    return dateKey(this._currentDate)
  }

  set value(next) {
    const date = toDate(next)
    if (date !== null) {
      this.setAttribute("value", dateKey(date))
    }
    return
  }

  get events() {
    return this._events
  }

  set events(value) {
    this._events = Array.isArray(value) === true ? value : []
    if (this._calGrid !== undefined && this._calGrid !== null) {
      this._buildGrid()
    }
    return
  }

  get dataSource() {
    return this._dataSource
  }

  set dataSource(value) {
    this._dataSource = value !== null && value !== undefined ? value : null
    if (this._calGrid !== undefined && this._calGrid !== null && this._dataSource !== null) {
      this._fetchEvents()
    }
    return
  }

  /* The selected day as `YYYY-MM-DD`, or null. */
  get selectedDate() {
    return this._selectedDate
  }

  get displayedPeriod() {
    return {
      start: this._getPeriodStart(),
      end: this._getPeriodEnd()
    }
  }

  get loading() {
    return this.hasAttribute("loading")
  }

  set loading(value) {
    this.reflectBoolean("loading", value === true)
    return
  }
}
