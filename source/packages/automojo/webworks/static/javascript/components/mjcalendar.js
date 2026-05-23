/*
 * mjcalendar.js
 *
 * <mj-calendar> -- calendar grid in month, week, day, or agenda view.
 * Locale-aware date math, event rendering, keyboard navigation per WAI-ARIA grid.
 * Fires mj-date-select, mj-event-click, mj-period-change, mj-view-change.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";
import { formatDate, getLocale } from "../core/intl.js";

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
  border-bottom: 1px solid var(--mj-border);
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
  border-bottom: 1px solid var(--mj-border);
}

.weekday-header {
  padding: var(--mj-space-2);
  text-align: center;
  font-size: var(--mj-font-size-xs);
  font-weight: var(--mj-font-weight-medium);
  color: var(--mj-text-muted);
  border-right: 1px solid var(--mj-border);
}
.weekday-header:last-child { border-right: none; }

.month-grid {
  display: flex;
  flex-direction: column;
}

.week-row {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  border-bottom: 1px solid var(--mj-border);
  min-height: var(--mj-cal-cell-min-height, 80px);
}
.week-row:last-child { border-bottom: none; }

.day-cell {
  padding: var(--mj-space-1) var(--mj-space-2);
  border-right: 1px solid var(--mj-border);
  cursor: pointer;
  min-height: var(--mj-cal-cell-min-height, 80px);
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.day-cell:last-child { border-right: none; }
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

.event-chip {
  display: block;
  background: var(--mj-accent);
  color: var(--mj-text-on-accent);
  border-radius: var(--mj-cal-event-radius, var(--mj-radius-sm));
  padding: 1px 4px;
  font-size: 0.7rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;
  border: none;
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
  padding: var(--mj-space-2) var(--mj-space-3);
  border-inline-start: 3px solid var(--mj-accent);
  background: var(--mj-bg-subtle);
  border-radius: 0 var(--mj-radius-sm) var(--mj-radius-sm) 0;
  cursor: pointer;
  font-size: var(--mj-font-size-sm);
}
.agenda-event:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); }
`;

const WEEK_DAYS_SHORT = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const WEEK_DAYS_LONG = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

export class MjCalendar extends MjElement {
  static tagName = "mj-calendar";
  static styles = STYLES;
  static watched = ["view", "value", "min", "max", "first-day-of-week", "loading", "event-overflow"];

  constructor() {
    super()
    this._events = []
    this._dataSource = null
    this._focusedDate = null
    this._selectedDate = null
    this._gridId = nextId("mj-cal-grid")
  }

  render() {
    const markup = `
      <div class="cal-header" part="header">
        <slot name="toolbar-start"></slot>
        <button class="nav-btn" part="prev-button" aria-label="Previous">&#8249;</button>
        <span class="period-label" aria-live="polite" aria-atomic="true"></span>
        <button class="nav-btn" part="next-button" aria-label="Next">&#8250;</button>
        <div class="view-switcher" part="view-switcher">
          <button class="view-btn" data-view="month">Month</button>
          <button class="view-btn" data-view="week">Week</button>
          <button class="view-btn" data-view="day">Day</button>
          <button class="view-btn" data-view="agenda">Agenda</button>
        </div>
        <slot name="toolbar-end"></slot>
      </div>
      <div class="cal-grid" part="grid" id="${this._gridId}" role="grid"
           aria-label="Calendar" tabindex="0"></div>
      <div class="status-region" aria-live="polite" aria-atomic="true"></div>
    `
    return markup
  }

  afterRender() {
    this._header = this.$(".cal-header")
    this._periodLabel = this.$(".period-label")
    this._calGrid = this.$(".cal-grid")
    this._statusRegion = this.$(".status-region")

    const prevBtn = this.$("[part='prev-button']")
    const nextBtn = this.$("[part='next-button']")
    this.listen(prevBtn, "click", () => { this._navigate(-1) })
    this.listen(nextBtn, "click", () => { this._navigate(1) })

    const viewBtns = this.$all(".view-btn")
    for (let i = 0; i < viewBtns.length; i = i + 1) {
      const btn = viewBtns[i]
      this.listen(btn, "click", () => {
        const v = btn.getAttribute("data-view")
        this.setAttribute("view", v)
      })
    }

    this.listen(this._calGrid, "keydown", this._onGridKeydown.bind(this))

    const valueAttr = this.getAttribute("value")
    this._currentDate = valueAttr !== null && valueAttr.length > 0 ? new Date(valueAttr) : new Date()
    if (isNaN(this._currentDate.getTime()) === true) {
      this._currentDate = new Date()
    }

    this._syncViewButtons()
    this._buildGrid()

    if (this._dataSource !== null) {
      this._fetchEvents()
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
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
    if (name === "value") {
      const d = new Date(newValue)
      if (isNaN(d.getTime()) === false) {
        this._currentDate = d
        this._buildGrid()
      }
    }
    if (name === "loading") {
      this._calGrid.setAttribute("aria-busy", newValue !== null ? "true" : "false")
    }
    return
  }

  _syncViewButtons() {
    const view = this.getAttribute("view") || "month"
    const btns = this.$all(".view-btn")
    for (let i = 0; i < btns.length; i = i + 1) {
      const btn = btns[i]
      if (btn.getAttribute("data-view") === view) {
        btn.className = "view-btn active"
      } else {
        btn.className = "view-btn"
      }
    }
    return
  }

  _navigate(delta) {
    const view = this.getAttribute("view") || "month"
    const d = new Date(this._currentDate)
    if (view === "month") {
      d.setMonth(d.getMonth() + delta)
    } else if (view === "week") {
      d.setDate(d.getDate() + delta * 7)
    } else if (view === "day") {
      d.setDate(d.getDate() + delta)
    } else if (view === "agenda") {
      d.setMonth(d.getMonth() + delta)
    }
    this._currentDate = d
    this._buildGrid()
    if (this._dataSource !== null) {
      this._fetchEvents()
    }
    const periodStart = this._getPeriodStart()
    const periodEnd = this._getPeriodEnd()
    this.emit("mj-period-change", {
      start: periodStart.toISOString().slice(0, 10),
      end: periodEnd.toISOString().slice(0, 10),
      view: view
    })
    return
  }

  _getPeriodStart() {
    const view = this.getAttribute("view") || "month"
    const d = new Date(this._currentDate)
    if (view === "month") {
      return new Date(d.getFullYear(), d.getMonth(), 1)
    }
    if (view === "week") {
      const dow = d.getDay()
      const start = parseInt(this.getAttribute("first-day-of-week") || "0", 10)
      const diff = (dow - start + 7) % 7
      const startD = new Date(d)
      startD.setDate(d.getDate() - diff)
      return startD
    }
    return new Date(d.getFullYear(), d.getMonth(), d.getDate())
  }

  _getPeriodEnd() {
    const view = this.getAttribute("view") || "month"
    const d = new Date(this._currentDate)
    if (view === "month") {
      return new Date(d.getFullYear(), d.getMonth() + 1, 0)
    }
    if (view === "week") {
      const start = this._getPeriodStart()
      const end = new Date(start)
      end.setDate(start.getDate() + 6)
      return end
    }
    return new Date(d.getFullYear(), d.getMonth(), d.getDate())
  }

  _fetchEvents() {
    if (this._dataSource === null || typeof this._dataSource.fetchEvents !== "function") {
      return
    }
    this.reflectBoolean("loading", true)
    const start = this._getPeriodStart()
    const end = this._getPeriodEnd()
    this._dataSource.fetchEvents(start, end).then((evts) => {
      this.reflectBoolean("loading", false)
      this._events = Array.isArray(evts) === true ? evts : []
      this._buildGrid()
      return
    }).catch(() => {
      this.reflectBoolean("loading", false)
    })
    return
  }

  _buildGrid() {
    const view = this.getAttribute("view") || "month"
    this._calGrid.innerHTML = ""
    this._updatePeriodLabel()

    if (view === "month") {
      this._buildMonthGrid()
    } else if (view === "agenda") {
      this._buildAgendaView()
    } else {
      this._buildSimpleGrid()
    }
    return
  }

  _updatePeriodLabel() {
    const view = this.getAttribute("view") || "month"
    const locale = this.getAttribute("locale") || getLocale()
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
    this._calGrid.setAttribute("aria-label", `Calendar, ${label}`)
    announce(`Showing ${label}`)
    return
  }

  _buildMonthGrid() {
    const locale = this.getAttribute("locale") || getLocale()
    const firstDow = parseInt(this.getAttribute("first-day-of-week") || "0", 10)
    const year = this._currentDate.getFullYear()
    const month = this._currentDate.getMonth()
    const today = new Date()

    const headerRow = document.createElement("div")
    headerRow.className = "weekday-headers"
    headerRow.setAttribute("role", "row")

    for (let d = 0; d < 7; d = d + 1) {
      const dow = (d + firstDow) % 7
      const cell = document.createElement("div")
      cell.className = "weekday-header"
      cell.setAttribute("role", "columnheader")
      cell.setAttribute("aria-label", WEEK_DAYS_LONG[dow])
      cell.textContent = WEEK_DAYS_SHORT[dow]
      headerRow.appendChild(cell)
    }
    this._calGrid.appendChild(headerRow)

    const monthGrid = document.createElement("div")
    monthGrid.className = "month-grid"

    const firstOfMonth = new Date(year, month, 1)
    const firstDayOfWeek = firstOfMonth.getDay()
    let startOffset = (firstDayOfWeek - firstDow + 7) % 7
    const startDate = new Date(year, month, 1 - startOffset)

    const maxVisible = parseInt(this.getAttribute("event-overflow") || "3", 10)
    const minAttr = this.getAttribute("min")
    const maxAttr = this.getAttribute("max")
    const minDate = minAttr !== null && minAttr.length > 0 ? new Date(minAttr) : null
    const maxDate = maxAttr !== null && maxAttr.length > 0 ? new Date(maxAttr) : null

    for (let week = 0; week < 6; week = week + 1) {
      const weekRow = document.createElement("div")
      weekRow.className = "week-row"
      weekRow.setAttribute("part", "week-row")
      weekRow.setAttribute("role", "row")

      let hasCurrentMonth = false

      for (let d = 0; d < 7; d = d + 1) {
        const cellDate = new Date(startDate)
        cellDate.setDate(startDate.getDate() + week * 7 + d)
        const isCurrentMonth = cellDate.getMonth() === month

        if (isCurrentMonth === true) {
          hasCurrentMonth = true
        }

        const cell = document.createElement("div")
        cell.className = isCurrentMonth === true ? "day-cell" : "day-cell other-month"
        cell.setAttribute("part", "day-cell")
        cell.setAttribute("role", "gridcell")
        cell.setAttribute("tabindex", "-1")

        const dateStr = cellDate.toISOString().slice(0, 10)
        cell.setAttribute("data-date", dateStr)

        const isToday = cellDate.toDateString() === today.toDateString()
        if (isToday === true) {
          cell.setAttribute("aria-current", "date")
          cell.setAttribute("part", "day-cell day-cell-today")
        }

        if (isCurrentMonth === false) {
          cell.setAttribute("part", "day-cell day-cell-other-month")
        }

        let disabled = false
        if (minDate !== null && cellDate < minDate) {
          disabled = true
        }
        if (maxDate !== null && cellDate > maxDate) {
          disabled = true
        }
        if (disabled === true) {
          cell.setAttribute("aria-disabled", "true")
        }

        const dayNum = document.createElement("span")
        dayNum.className = "day-number"
        dayNum.setAttribute("part", "day-number")
        dayNum.textContent = String(cellDate.getDate())
        cell.appendChild(dayNum)

        const dayEvents = this._getEventsForDate(cellDate)
        const visibleEvents = dayEvents.slice(0, maxVisible)
        const hiddenCount = dayEvents.length - visibleEvents.length

        for (let ei = 0; ei < visibleEvents.length; ei = ei + 1) {
          const ev = visibleEvents[ei]
          const chip = this._buildEventChip(ev)
          cell.appendChild(chip)
        }

        if (hiddenCount > 0) {
          const overflowBtn = document.createElement("button")
          overflowBtn.className = "overflow-btn"
          overflowBtn.setAttribute("part", "event-overflow")
          overflowBtn.setAttribute("aria-label", `${hiddenCount} more events on ${dateStr}`)
          overflowBtn.textContent = `+${hiddenCount} more`
          cell.appendChild(overflowBtn)
        }

        const eventCount = dayEvents.length
        const ariaLabel = `${cellDate.getDate()} ${new Intl.DateTimeFormat(locale, { month: "long" }).format(cellDate)} ${cellDate.getFullYear()}${eventCount > 0 ? `, ${eventCount} events` : ""}`
        cell.setAttribute("aria-label", ariaLabel)

        this.listen(cell, "click", () => {
          if (cell.getAttribute("aria-disabled") === "true") {
            return
          }
          this._selectedDate = dateStr
          const allCells = this._calGrid.querySelectorAll(".day-cell")
          for (let ci = 0; ci < allCells.length; ci = ci + 1) {
            allCells[ci].removeAttribute("aria-selected")
          }
          cell.setAttribute("aria-selected", "true")
          this.emit("mj-date-select", { date: dateStr })
          if (this.hasAttribute("readonly") === false) {
            this.emit("mj-event-create", { date: dateStr }, { cancelable: true })
          }
        })

        weekRow.appendChild(cell)
      }

      if (hasCurrentMonth === true || week === 0) {
        monthGrid.appendChild(weekRow)
      }
    }

    this._calGrid.appendChild(monthGrid)
    return
  }

  _buildSimpleGrid() {
    const view = this.getAttribute("view") || "week"
    const msg = document.createElement("div")
    msg.style.padding = "var(--mj-space-4)"
    msg.style.color = "var(--mj-text-muted)"
    msg.style.fontSize = "var(--mj-font-size-sm)"
    msg.textContent = `${view.charAt(0).toUpperCase() + view.slice(1)} view`
    this._calGrid.appendChild(msg)
    return
  }

  _buildAgendaView() {
    const list = document.createElement("div")
    list.className = "agenda-list"

    const sorted = this._events.slice().sort((a, b) => {
      const da = a.start instanceof Date ? a.start : new Date(a.start)
      const db = b.start instanceof Date ? b.start : new Date(b.start)
      return da.getTime() - db.getTime()
    })

    if (sorted.length === 0) {
      const empty = document.createElement("div")
      empty.style.color = "var(--mj-text-muted)"
      empty.textContent = "No events"
      list.appendChild(empty)
    }

    let lastDateStr = ""
    for (let i = 0; i < sorted.length; i = i + 1) {
      const ev = sorted[i]
      const start = ev.start instanceof Date ? ev.start : new Date(ev.start)
      const dateStr = start.toISOString().slice(0, 10)

      if (dateStr !== lastDateStr) {
        const dateLabel = document.createElement("div")
        dateLabel.className = "agenda-date"
        dateLabel.textContent = formatDate(start)
        list.appendChild(dateLabel)
        lastDateStr = dateStr
      }

      const evEl = document.createElement("div")
      evEl.className = "agenda-event"
      evEl.setAttribute("role", "button")
      evEl.setAttribute("tabindex", "0")
      evEl.textContent = ev.title
      if (ev.color !== undefined) {
        evEl.style.borderColor = ev.color
      }
      this.listen(evEl, "click", () => {
        this.emit("mj-event-click", { eventId: ev.id, event: ev })
      })
      list.appendChild(evEl)
    }

    this._calGrid.appendChild(list)
    return
  }

  _buildEventChip(ev) {
    const chip = document.createElement("button")
    chip.className = "event-chip"
    chip.setAttribute("part", "event-chip")
    const start = ev.start instanceof Date ? ev.start : new Date(ev.start)
    const end = ev.end instanceof Date ? ev.end : new Date(ev.end)
    const timeStr = `${start.getHours()}:${String(start.getMinutes()).padStart(2, "0")}–${end.getHours()}:${String(end.getMinutes()).padStart(2, "0")}`
    chip.setAttribute("aria-label", `${ev.title}, ${timeStr}`)
    chip.textContent = ev.title
    if (ev.color !== undefined) {
      chip.style.background = ev.color
    }
    this.listen(chip, "click", (e) => {
      e.stopPropagation()
      this.emit("mj-event-click", { eventId: ev.id, event: ev })
    })
    return chip
  }

  _getEventsForDate(date) {
    const dateStr = date.toISOString().slice(0, 10)
    const matching = this._events.filter((ev) => {
      const start = ev.start instanceof Date ? ev.start : new Date(ev.start)
      return start.toISOString().slice(0, 10) === dateStr
    })
    return matching
  }

  _onGridKeydown(event) {
    const cells = this._calGrid.querySelectorAll("[role='gridcell']")
    if (cells.length === 0) {
      return
    }

    const focused = this._calGrid.querySelector("[aria-selected='true']") || cells[0]
    let idx = Array.from(cells).indexOf(focused)

    if (event.key === "ArrowLeft") {
      event.preventDefault()
      idx = Math.max(0, idx - 1)
    } else if (event.key === "ArrowRight") {
      event.preventDefault()
      idx = Math.min(cells.length - 1, idx + 1)
    } else if (event.key === "ArrowUp") {
      event.preventDefault()
      idx = Math.max(0, idx - 7)
    } else if (event.key === "ArrowDown") {
      event.preventDefault()
      idx = Math.min(cells.length - 1, idx + 7)
    } else if (event.key === "PageUp") {
      event.preventDefault()
      this._navigate(-1)
      return
    } else if (event.key === "PageDown") {
      event.preventDefault()
      this._navigate(1)
      return
    } else if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      const cell = cells[idx]
      if (cell !== undefined) {
        cell.click()
      }
      return
    } else {
      return
    }

    for (let i = 0; i < cells.length; i = i + 1) {
      cells[i].tabIndex = -1
    }
    const target = cells[idx]
    if (target !== undefined) {
      target.tabIndex = 0
      target.focus()
    }
    return
  }

  /* ----- scriptable API ----- */

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
