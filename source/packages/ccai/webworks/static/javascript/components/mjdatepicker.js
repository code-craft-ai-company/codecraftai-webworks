/*
 * mjdatepicker.js
 *
 * <mj-date-picker> — date / time / datetime / range picker with a calendar
 * grid, accessible keyboard navigation, and form participation.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { autoPosition } from "../core/overlay.js";
import { trapFocus } from "../core/focustrap.js";
import { announce } from "../core/announcer.js";

const STYLES = `
:host { display: inline-block; vertical-align: middle; }
:host([block]) { display: block; }

.field {
  display: flex;
  align-items: center;
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-md);
  background: var(--mj-surface);
  min-height: var(--mj-control-height-md);
  transition: border-color var(--mj-motion-fast);
}
.field:focus-within { border-color: var(--mj-accent); }
:host([invalid]) .field { border-color: var(--mj-color-danger); }
:host([disabled]) .field { opacity: 0.55; pointer-events: none; }

.date-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  padding: 0 var(--mj-space-3);
  font: inherit;
  font-size: var(--mj-font-size-md);
  color: var(--mj-text);
  min-height: var(--mj-control-height-md);
}
.cal-trigger, .clear-btn {
  flex-shrink: 0;
  padding: 0 var(--mj-space-2);
  background: none;
  border: none;
  cursor: pointer;
  color: var(--mj-text-muted);
  display: flex;
  align-items: center;
  min-height: var(--mj-control-height-md);
}
.cal-trigger:hover, .clear-btn:hover { color: var(--mj-text); }
.cal-trigger:focus-visible, .clear-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}
:host(:not([clearable])) .clear-btn { display: none; }
.clear-btn.hidden { display: none; }

.popup {
  position: fixed;
  width: var(--mj-date-picker-popup-width, 20rem);
  background: var(--mj-surface-raised, var(--mj-surface));
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-md);
  box-shadow: var(--mj-elevation-3);
  z-index: var(--mj-layer-popover);
  display: none;
  padding: var(--mj-space-3);
}
:host([open]) .popup { display: block; }

.cal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--mj-space-2);
}
.cal-nav-btn {
  background: none;
  border: 1px solid transparent;
  border-radius: var(--mj-radius-sm);
  cursor: pointer;
  color: var(--mj-text);
  padding: var(--mj-space-1) var(--mj-space-2);
  font: inherit;
}
.cal-nav-btn:hover { background: var(--mj-bg-muted); }
.cal-nav-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}
.cal-month-year {
  font-weight: var(--mj-font-weight-medium);
  font-size: var(--mj-font-size-md);
  color: var(--mj-text);
  cursor: pointer;
}
.cal-month-year:hover { color: var(--mj-accent); }

.day-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
}
.weekday-header {
  text-align: center;
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
  font-weight: var(--mj-font-weight-medium);
  padding: var(--mj-space-1);
}
.day-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--mj-date-picker-cell-size, 2.25rem);
  height: var(--mj-date-picker-cell-size, 2.25rem);
  background: none;
  border: 1px solid transparent;
  border-radius: 50%;
  font: inherit;
  font-size: var(--mj-font-size-sm);
  cursor: pointer;
  color: var(--mj-text);
  margin: auto;
}
.day-btn:hover:not([disabled]) { background: var(--mj-bg-muted); }
.day-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.day-btn[aria-selected="true"] {
  background: var(--mj-date-picker-selected-color, var(--mj-accent));
  color: var(--mj-text-on-accent);
  border-color: transparent;
}
.day-btn.today { border-color: var(--mj-accent); }
.day-btn.other-month { color: var(--mj-text-muted); }
.day-btn[disabled] { opacity: 0.35; cursor: not-allowed; }
.day-btn.range-fill { background: var(--mj-bg-subtle); border-radius: 0; }
.day-btn.range-start { border-radius: 50% 0 0 50%; }
.day-btn.range-end { border-radius: 0 50% 50% 0; }

.time-panel {
  display: flex;
  gap: var(--mj-space-2);
  margin-top: var(--mj-space-2);
  align-items: center;
}
.time-input {
  width: 3rem;
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-sm);
  padding: var(--mj-space-1) var(--mj-space-2);
  text-align: center;
  font: inherit;
  font-size: var(--mj-font-size-md);
  color: var(--mj-text);
  background: var(--mj-surface);
}
.time-sep { color: var(--mj-text-muted); font-weight: var(--mj-font-weight-medium); }
`;

const DAYS_SHORT = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]

export class MjDatePicker extends FormControlMixin(MjElement) {
  static tagName = "mj-date-picker";
  static styles = STYLES;
  static watched = ["value", "mode", "open", "disabled", "readonly", "invalid", "clearable", "min", "max"];

  constructor() {
    super()
    this._initFormControl()
    this._displayMonth = new Date()
    this._displayMonth.setDate(1)
    this._rangeStart = null
    this._rangeEnd = null
    this._hoverDate = null
    this._disposePosition = null
    this._disposeTrap = null
    this._focusedDate = null
    this._popupId = nextId("mj-dp-popup")
    this._inputId = nextId("mj-dp-in")
  }

  render() {
    const ph = this.getAttribute("placeholder") || "Select date"
    const markup = `
      <div class="field" part="field">
        <input
          class="date-input"
          part="input"
          id="${this._inputId}"
          role="combobox"
          aria-haspopup="dialog"
          aria-expanded="false"
          aria-autocomplete="none"
          aria-controls="${this._popupId}"
          placeholder="${ph}"
          type="text"
          autocomplete="off"
        />
        <button class="clear-btn hidden" part="clear" type="button" aria-label="Clear date">
          <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
            <path d="M12 4 8 8l4 4-1 1-4-4-4 4-1-1 4-4-4-4 1-1 4 4 4-4z"/>
          </svg>
        </button>
        <button class="cal-trigger" part="calendar-trigger" type="button" aria-label="Open calendar">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <rect x="3" y="4" width="18" height="18" rx="2"/>
            <line x1="16" y1="2" x2="16" y2="6"/>
            <line x1="8" y1="2" x2="8" y2="6"/>
            <line x1="3" y1="10" x2="21" y2="10"/>
          </svg>
        </button>
      </div>
      <div class="popup" part="popup" id="${this._popupId}" role="dialog" aria-label="Choose a date">
        <div class="cal-header" part="calendar-header">
          <button class="cal-nav-btn" part="prev" type="button" aria-label="Previous month">&#8249;</button>
          <span class="cal-month-year" part="month-year"></span>
          <button class="cal-nav-btn" part="next" type="button" aria-label="Next month">&#8250;</button>
        </div>
        <div class="day-grid" part="day-grid" role="grid" aria-label="Calendar"></div>
        <div class="time-panel" part="time-panel" style="display:none">
          <input class="time-input" type="number" aria-label="Hour" min="0" max="23" placeholder="HH" />
          <span class="time-sep">:</span>
          <input class="time-input" type="number" aria-label="Minute" min="0" max="59" placeholder="MM" />
        </div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._dateInput = this.$(".date-input")
    this._clearBtn = this.$(".clear-btn")
    this._calTrigger = this.$(".cal-trigger")
    this._popup = this.$(".popup")
    this._dayGrid = this.$(".day-grid")
    this._monthYearEl = this.$(".cal-month-year")
    this._prevBtn = this.$(".cal-nav-btn[part='prev']")
    this._nextBtn = this.$(".cal-nav-btn[part='next']")
    this._timePanel = this.$(".time-panel")

    this.listen(this._dateInput, "click", () => this._open())
    this.listen(this._calTrigger, "click", () => this._open())
    this.listen(this._prevBtn, "click", () => this._navigateMonth(-1))
    this.listen(this._nextBtn, "click", () => this._navigateMonth(1))
    this.listen(this._dateInput, "keydown", this._onInputKeydown.bind(this))
    this.listen(this._clearBtn, "click", this._onClear.bind(this))
    this.listen(document, "click", this._onDocClick.bind(this))

    const mode = this.getAttribute("mode") || "date"
    if (mode === "datetime" || mode === "time") {
      this._timePanel.style.display = "flex"
    }

    const attrVal = this.getAttribute("value") || ""
    if (attrVal.length > 0) {
      this._setFormValue(attrVal)
      this._dateInput.value = this._formatForDisplay(attrVal)
      this._syncClearBtn()
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "value" && this._dateInput !== undefined) {
      this._setFormValue(newValue || "")
      this._dateInput.value = this._formatForDisplay(newValue || "")
      this._syncClearBtn()
    }
    if (name === "open") {
      this._syncOpen()
    }
    return
  }

  _formatForDisplay(isoStr) {
    if (isoStr.length === 0) {
      return ""
    }
    const locale = this.getAttribute("locale") || navigator.language || "en"
    try {
      const date = new Date(isoStr)
      const mode = this.getAttribute("mode") || "date"
      if (mode === "time") {
        return isoStr
      }
      const opts = mode === "datetime"
        ? { dateStyle: "medium", timeStyle: "short" }
        : { dateStyle: "medium" }
      return new Intl.DateTimeFormat(locale, opts).format(date)
    } catch {
      return isoStr
    }
  }

  _syncClearBtn() {
    if (this._clearBtn === undefined) {
      return
    }
    const hasVal = (this._value || "").length > 0
    const clearable = this.hasAttribute("clearable")
    if (clearable === true && hasVal === true) {
      this._clearBtn.classList.remove("hidden")
    } else {
      this._clearBtn.classList.add("hidden")
    }
    return
  }

  _open() {
    if (this.hasAttribute("disabled") || this.hasAttribute("readonly")) {
      return
    }
    const proceed = this.emit("mj-open", {}, { cancelable: true })
    if (proceed === false) {
      return
    }
    this.setAttribute("open", "")
    return
  }

  _close() {
    if (this.hasAttribute("open") === false) {
      return
    }
    this.removeAttribute("open")
    this.emit("mj-close", {})
    return
  }

  _syncOpen() {
    const isOpen = this.hasAttribute("open")
    this._dateInput.setAttribute("aria-expanded", isOpen === true ? "true" : "false")
    if (isOpen === true) {
      this._disposePosition = autoPosition(this._popup, this._calTrigger, { placement: "bottom-start" })
      this._renderCalendar()
      this._disposeTrap = trapFocus(this._popup, this._prevBtn)
    } else {
      if (this._disposePosition !== null) {
        this._disposePosition()
        this._disposePosition = null
      }
      if (this._disposeTrap !== null) {
        this._disposeTrap()
        this._disposeTrap = null
      }
    }
    return
  }

  _renderCalendar() {
    const year = this._displayMonth.getFullYear()
    const month = this._displayMonth.getMonth()
    const locale = this.getAttribute("locale") || navigator.language || "en"

    const monthName = new Intl.DateTimeFormat(locale, { month: "long", year: "numeric" }).format(this._displayMonth)
    this._monthYearEl.textContent = monthName

    const firstDay = new Date(year, month, 1).getDay()
    const daysInMonth = new Date(year, month + 1, 0).getDate()

    const today = new Date()
    const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`
    const selectedStr = this._value || ""

    let html = ""
    DAYS_SHORT.forEach((day) => {
      html += `<div class="weekday-header" part="week-header" role="columnheader">${day}</div>`
    })

    for (let i = 0; i < firstDay; i = i + 1) {
      html += `<div></div>`
    }

    for (let d = 1; d <= daysInMonth; d = d + 1) {
      const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`
      const isToday = dateStr === todayStr
      const isSelected = dateStr === selectedStr
      const isDisabled = this._isDateDisabled(dateStr)
      const clsList = ["day-btn"]
      if (isToday === true) {
        clsList.push("today")
      }

      const ariaLabel = `${d}, ${monthName}${isToday === true ? ", today" : ""}`
      html += `<div role="gridcell" part="day-cell">
        <button
          class="${clsList.join(" ")}"
          type="button"
          tabindex="${isSelected === true ? "0" : "-1"}"
          aria-label="${ariaLabel}"
          aria-selected="${isSelected === true ? "true" : "false"}"
          data-date="${dateStr}"
          ${isDisabled === true ? "disabled" : ""}
        >${d}</button>
      </div>`
    }

    this._dayGrid.innerHTML = html

    const dayCells = this._dayGrid.querySelectorAll(".day-btn:not([disabled])")
    dayCells.forEach((btn) => {
      this.listen(btn, "click", this._onDayClick.bind(this))
      this.listen(btn, "keydown", this._onDayKeydown.bind(this))
    })
    return
  }

  _isDateDisabled(dateStr) {
    const min = this.getAttribute("min") || ""
    const max = this.getAttribute("max") || ""
    if (min.length > 0 && dateStr < min) {
      return true
    }
    if (max.length > 0 && dateStr > max) {
      return true
    }
    return false
  }

  _navigateMonth(delta) {
    this._displayMonth.setMonth(this._displayMonth.getMonth() + delta)
    const locale = this.getAttribute("locale") || navigator.language || "en"
    const monthName = new Intl.DateTimeFormat(locale, { month: "long", year: "numeric" }).format(this._displayMonth)
    announce(monthName, "polite")
    this.emit("mj-month-change", {
      month: this._displayMonth.getMonth() + 1,
      year: this._displayMonth.getFullYear()
    })
    this._renderCalendar()
    return
  }

  _onDayClick(event) {
    const btn = event.currentTarget
    const dateStr = btn.dataset.date
    const mode = this.getAttribute("mode") || "date"

    if (mode === "range") {
      if (this._rangeStart === null || (this._rangeStart !== null && this._rangeEnd !== null)) {
        this._rangeStart = dateStr
        this._rangeEnd = null
      } else {
        if (dateStr < this._rangeStart) {
          this._rangeEnd = this._rangeStart
          this._rangeStart = dateStr
        } else {
          this._rangeEnd = dateStr
        }
        const rangeVal = `${this._rangeStart}/${this._rangeEnd}`
        this._setFormValue(rangeVal)
        this.setAttribute("value", rangeVal)
        this._dateInput.value = this._formatForDisplay(this._rangeStart) + " – " + this._formatForDisplay(this._rangeEnd)
        this.emit("mj-change", {
          value: rangeVal,
          date: null,
          startDate: new Date(this._rangeStart),
          endDate: new Date(this._rangeEnd)
        })
        this._close()
      }
      this._renderCalendar()
    } else {
      this._setFormValue(dateStr)
      this.setAttribute("value", dateStr)
      this._dateInput.value = this._formatForDisplay(dateStr)
      this._syncClearBtn()
      this.emit("mj-change", { value: dateStr, date: new Date(dateStr), startDate: null, endDate: null })
      this._close()
      this._calTrigger.focus()
    }
    return
  }

  _onDayKeydown(event) {
    const btn = event.currentTarget
    const dateStr = btn.dataset.date
    const date = new Date(dateStr)

    let newDate = null
    if (event.key === "ArrowLeft") {
      event.preventDefault()
      newDate = new Date(date)
      newDate.setDate(newDate.getDate() - 1)
    } else if (event.key === "ArrowRight") {
      event.preventDefault()
      newDate = new Date(date)
      newDate.setDate(newDate.getDate() + 1)
    } else if (event.key === "ArrowUp") {
      event.preventDefault()
      newDate = new Date(date)
      newDate.setDate(newDate.getDate() - 7)
    } else if (event.key === "ArrowDown") {
      event.preventDefault()
      newDate = new Date(date)
      newDate.setDate(newDate.getDate() + 7)
    } else if (event.key === "PageUp") {
      event.preventDefault()
      this._navigateMonth(event.shiftKey === true ? -12 : -1)
      return
    } else if (event.key === "PageDown") {
      event.preventDefault()
      this._navigateMonth(event.shiftKey === true ? 12 : 1)
      return
    } else if (event.key === "Escape") {
      this._close()
      this._calTrigger.focus()
      return
    }

    if (newDate !== null) {
      const newDateStr = `${newDate.getFullYear()}-${String(newDate.getMonth() + 1).padStart(2, "0")}-${String(newDate.getDate()).padStart(2, "0")}`
      if (newDate.getMonth() !== date.getMonth()) {
        this._displayMonth = new Date(newDate.getFullYear(), newDate.getMonth(), 1)
        this._renderCalendar()
      }
      const target = this._dayGrid.querySelector(`[data-date="${newDateStr}"]`)
      if (target !== null) {
        btn.tabIndex = -1
        target.tabIndex = 0
        target.focus()
      }
    }
    return
  }

  _onInputKeydown(event) {
    if (event.key === "Enter" || event.key === " " || event.key === "ArrowDown") {
      event.preventDefault()
      this._open()
    }
    return
  }

  _onClear() {
    this._setFormValue("")
    this.setAttribute("value", "")
    this._dateInput.value = ""
    this._rangeStart = null
    this._rangeEnd = null
    this._syncClearBtn()
    this.emit("mj-change", { value: "", date: null, startDate: null, endDate: null })
    return
  }

  _onDocClick(event) {
    if (this.hasAttribute("open") === false) {
      return
    }
    const inside = event.composedPath().includes(this)
    if (inside === false) {
      this._close()
    }
    return
  }

  _validationAnchor() {
    return this._dateInput || this
  }

  get valueAsDate() {
    const val = this._value
    if (val === null || val === undefined || val.length === 0) {
      return null
    }
    return new Date(val)
  }

  get displayMonth() {
    return new Date(this._displayMonth)
  }

  get open() {
    return this.hasAttribute("open")
  }

  set open(value) {
    if (value === true) {
      this._open()
    } else {
      this._close()
    }
    return
  }

  focus() {
    if (this._dateInput !== undefined) {
      this._dateInput.focus()
    }
    return
  }
}
