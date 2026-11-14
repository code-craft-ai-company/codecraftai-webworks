/*
 * mjdatepicker.js
 *
 * <mj-date-picker> — date / time / datetime / range picker with a calendar
 * grid, accessible keyboard navigation, and form participation.
 *
 * Values are ISO 8601 strings and always denote LOCAL calendar days and wall
 * clock times -- they are never parsed as UTC:
 *   mode="date"      YYYY-MM-DD
 *   mode="time"      HH:mm
 *   mode="datetime"  YYYY-MM-DDTHH:mm
 *   mode="range"     YYYY-MM-DD/YYYY-MM-DD
 *
 * The text field is a combobox: the user may type a date (ISO, the locale's
 * numeric order, or with a month name) and it is parsed on Enter or blur, or
 * open the calendar dialog with the trigger button or ArrowDown.
 *
 * The `value` attribute is the INITIAL value. Picking a date updates the
 * `value` property and the form value but is not written back to the
 * attribute, so a form reset can restore what the author wrote.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { autoPosition } from "../core/overlay.js";
import { trapFocus } from "../core/focustrap.js";
import { announce } from "../core/announcer.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";

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
:host([invalid]) .field, .field.text-invalid { border-color: var(--mj-color-danger); }
:host([disabled]) .field,
:host(:disabled) .field { opacity: 0.55; pointer-events: none; }

.date-input {
  flex: 1;
  min-width: 0;
  border: none;
  outline: none;
  background: transparent;
  padding: 0 var(--mj-space-3);
  font: inherit;
  font-size: var(--mj-font-size-md);
  color: var(--mj-text);
  min-height: var(--mj-control-height-md);
}
.date-input:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: -2px;
  border-radius: var(--mj-radius-md);
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
.cal-trigger:disabled, .clear-btn:disabled { cursor: not-allowed; opacity: 0.55; }
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
.popup.time-only { width: auto; }

.cal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--mj-space-1);
  margin-block-end: var(--mj-space-2);
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
:host(:dir(rtl)) .cal-nav-btn { transform: scaleX(-1); }
.cal-month-year {
  flex: 1;
  text-align: center;
  font-weight: var(--mj-font-weight-medium);
  font-size: var(--mj-font-size-md);
  color: var(--mj-text);
}

.week-row {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
  margin-block-end: 2px;
}
.weekday-header {
  text-align: center;
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
  font-weight: var(--mj-font-weight-medium);
  padding: var(--mj-space-1);
}
.day-cell { display: flex; }
.day-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--mj-date-picker-cell-size, 2.25rem);
  height: var(--mj-date-picker-cell-size, 2.25rem);
  background: none;
  border: 1px solid transparent;
  border-radius: var(--mj-radius-circle);
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
.day-btn.today { border-color: var(--mj-accent); }
.day-btn[disabled] { opacity: var(--mj-date-picker-disabled-opacity, 0.4); cursor: not-allowed; }
.day-btn.range-fill {
  background: var(--mj-date-picker-range-fill-color, var(--mj-bg-muted));
  border-radius: 0;
  width: 100%;
}
.day-btn.selected,
.day-btn.selected:hover:not([disabled]) {
  background: var(--mj-date-picker-selected-color, var(--mj-accent));
  color: var(--mj-text-on-accent);
  border-color: transparent;
}
.day-btn.range-start, .day-btn.range-end { width: 100%; border-radius: 0; }
.day-btn.range-start {
  border-start-start-radius: var(--mj-radius-pill);
  border-end-start-radius: var(--mj-radius-pill);
}
.day-btn.range-end {
  border-start-end-radius: var(--mj-radius-pill);
  border-end-end-radius: var(--mj-radius-pill);
}

.time-panel {
  display: flex;
  gap: var(--mj-space-2);
  margin-block-start: var(--mj-space-2);
  align-items: center;
}
.popup.time-only .time-panel { margin-block-start: 0; }
.time-input {
  width: 3.5rem;
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-sm);
  padding: var(--mj-space-1) var(--mj-space-2);
  text-align: center;
  font: inherit;
  font-size: var(--mj-font-size-md);
  color: var(--mj-text);
  background: var(--mj-surface);
}
.time-input:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}
.time-input.invalid { border-color: var(--mj-color-danger); }
.time-sep { color: var(--mj-text-muted); font-weight: var(--mj-font-weight-medium); }
.done-btn {
  margin-inline-start: auto;
  padding: var(--mj-space-1) var(--mj-space-3);
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-sm);
  background: var(--mj-surface);
  color: var(--mj-text);
  font: inherit;
  font-size: var(--mj-font-size-sm);
  cursor: pointer;
}
.done-btn:hover { background: var(--mj-bg-muted); }
.done-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
`;

/* ----- local-calendar helpers: a "day" is a YYYY-MM-DD string or a local Date ----- */

function pad2(value) {
  const text = String(value).padStart(2, "0")
  return text
}

function isoFromParts(year, month, day) {
  const text = `${String(year).padStart(4, "0")}-${pad2(month)}-${pad2(day)}`
  return text
}

/* The local calendar day of a Date as YYYY-MM-DD. */
function isoFromDate(date) {
  const text = isoFromParts(date.getFullYear(), date.getMonth() + 1, date.getDate())
  return text
}

/*
 * Parse YYYY-MM-DD into a Date at local midnight, or null when the text is
 * not a real calendar day. `new Date("YYYY-MM-DD")` is deliberately not used:
 * it yields UTC midnight, which is the previous day west of Greenwich.
 */
function parseIsoDate(text) {
  let date = null

  const match = typeof text === "string" ? text.match(/^(\d{4})-(\d{2})-(\d{2})$/) : null
  if (match !== null) {
    const year = Number(match[1])
    const month = Number(match[2])
    const day = Number(match[3])
    const candidate = new Date(2000, month - 1, day)
    candidate.setFullYear(year)
    const real = candidate.getFullYear() === year && candidate.getMonth() === month - 1 && candidate.getDate() === day
    if (real === true) {
      date = candidate
    }
  }

  return date
}

/* Parse HH:mm (seconds tolerated) into `{ hour, minute }`, or null. */
function parseIsoTime(text) {
  let time = null

  const match = typeof text === "string" ? text.match(/^(\d{1,2}):(\d{2})(?::\d{2}(?:\.\d+)?)?$/) : null
  if (match !== null) {
    const hour = Number(match[1])
    const minute = Number(match[2])
    if (hour >= 0 && hour <= 23 && minute >= 0 && minute <= 59) {
      time = { hour: hour, minute: minute }
    }
  }

  return time
}

function formatIsoTime(time) {
  const text = `${pad2(time.hour)}:${pad2(time.minute)}`
  return text
}

/* The same day-of-month `count` months away, clamped to that month's length. */
function shiftMonth(date, count) {
  const target = new Date(date.getFullYear(), date.getMonth() + count, 1)
  const lastDay = new Date(target.getFullYear(), target.getMonth() + 1, 0).getDate()
  target.setDate(Math.min(date.getDate(), lastDay))
  return target
}

/*
 * Text content of `node` with the subtree of `skip` left out, whitespace
 * collapsed. Used to read a wrapping <label> without the picker's own text.
 */
function textExcluding(node, skip) {
  const parts = []
  const visit = (current) => {
    if (current === skip) {
      return
    }
    if (current.nodeType === Node.TEXT_NODE) {
      parts.push(current.textContent)
      return
    }
    const children = current.childNodes
    for (let index = 0; index < children.length; index = index + 1) {
      visit(children[index])
    }
  }
  visit(node)
  const rtnval = parts.join(" ").replace(/\s+/g, " ").trim()
  return rtnval
}

export class MjDatePicker extends FormControlMixin(MjElement) {
  static tagName = "mj-date-picker";
  static styles = STYLES;
  static watched = [
    "value", "mode", "open", "disabled", "readonly", "required", "invalid", "clearable",
    "min", "max", "placeholder", "locale", "first-day-of-week",
    "label", "aria-label", "aria-labelledby"
  ];

  constructor() {
    super()
    this._initFormControl()

    const today = new Date()
    this._displayMonth = new Date(today.getFullYear(), today.getMonth(), 1)

    /* Range mode: the chosen ends (YYYY-MM-DD) and the day under the pointer. */
    this._rangeStart = null
    this._rangeEnd = null
    this._hoverDate = null

    /* The day that holds the grid's single tab stop (YYYY-MM-DD). */
    this._focusedDate = null

    /* Whether opening should move focus into the dialog. */
    this._focusDialogOnOpen = false

    /* The value when the popup opened; Escape goes back to it. */
    this._valueBeforeOpen = null

    /* The value text as last given, before it was normalised for the mode. */
    this._rawValue = ""

    /* True while the text field holds something that is not a date. */
    this._textInvalid = false

    this._disposePosition = null
    this._disposeTrap = null
    this._popupId = nextId("mj-dp-popup")
    this._inputId = nextId("mj-dp-in")

    /* True when the `value` attribute was applied before the first render. */
    this._valueReplayPending = false

    /* True while an ancestor <fieldset disabled> disables the control. */
    this._formDisabled = false

    this._dateInput = null
    this._popup = null
  }

  render() {
    const markup = html`
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
          type="text"
          autocomplete="off"
        />
        <button class="clear-btn hidden" part="clear" type="button" aria-label="${t("mj.datePicker.clearDate")}">
          <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
            <path d="M12 4 8 8l4 4-1 1-4-4-4 4-1-1 4-4-4-4 1-1 4 4 4-4z"/>
          </svg>
        </button>
        <button class="cal-trigger" part="calendar-trigger" type="button" aria-label="${t("mj.datePicker.openCalendar")}">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <rect x="3" y="4" width="18" height="18" rx="2"/>
            <line x1="16" y1="2" x2="16" y2="6"/>
            <line x1="8" y1="2" x2="8" y2="6"/>
            <line x1="3" y1="10" x2="21" y2="10"/>
          </svg>
        </button>
      </div>
      <div class="popup" part="popup" id="${this._popupId}" role="dialog" aria-label="${t("mj.datePicker.chooseDate")}">
        <div class="cal-header" part="calendar-header">
          <button class="cal-nav-btn" part="prev-year" type="button" aria-label="${t("mj.datePicker.previousYear")}" data-months="-12">&#171;</button>
          <button class="cal-nav-btn" part="prev" type="button" aria-label="${t("mj.datePicker.previousMonth")}" data-months="-1">&#8249;</button>
          <span class="cal-month-year" part="month-year"></span>
          <button class="cal-nav-btn" part="next" type="button" aria-label="${t("mj.datePicker.nextMonth")}" data-months="1">&#8250;</button>
          <button class="cal-nav-btn" part="next-year" type="button" aria-label="${t("mj.datePicker.nextYear")}" data-months="12">&#187;</button>
        </div>
        <div class="day-grid" part="day-grid" role="grid"></div>
        <div class="time-panel" part="time-panel" hidden>
          <input class="time-input hour-input" type="number" aria-label="${t("mj.datePicker.hour")}" min="0" max="23" placeholder="${t("mj.datePicker.hourPlaceholder")}" />
          <span class="time-sep" aria-hidden="true">:</span>
          <input class="time-input minute-input" type="number" aria-label="${t("mj.datePicker.minute")}" min="0" max="59" placeholder="${t("mj.datePicker.minutePlaceholder")}" />
          <button class="done-btn" type="button">${t("mj.datePicker.done")}</button>
        </div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._field = this.$(".field")
    this._dateInput = this.$(".date-input")
    this._clearBtn = this.$(".clear-btn")
    this._calTrigger = this.$(".cal-trigger")
    this._popup = this.$(".popup")
    this._calHeader = this.$(".cal-header")
    this._dayGrid = this.$(".day-grid")
    this._monthYearEl = this.$(".cal-month-year")
    this._timePanel = this.$(".time-panel")
    this._hourInput = this.$(".hour-input")
    this._minuteInput = this.$(".minute-input")
    this._doneBtn = this.$(".done-btn")

    this.listen(this._dateInput, "click", this._onInputClick.bind(this))
    this.listen(this._dateInput, "focus", this._syncAccessibility.bind(this))
    this.listen(this, "click", this._onHostClick.bind(this))
    this.listen(this._dateInput, "input", this._onInputTyped.bind(this))
    this.listen(this._dateInput, "change", this._commitTypedText.bind(this))
    this.listen(this._dateInput, "keydown", this._onInputKeydown.bind(this))
    this.listen(this._calTrigger, "click", this._onTriggerClick.bind(this))
    this.listen(this._clearBtn, "click", this._onClear.bind(this))
    this.listen(this._calHeader, "click", this._onHeaderClick.bind(this))
    this.listen(this._dayGrid, "click", this._onDayClick.bind(this))
    this.listen(this._dayGrid, "keydown", this._onDayKeydown.bind(this))
    this.listen(this._dayGrid, "mouseover", this._onDayHover.bind(this))
    this.listen(this._dayGrid, "mouseleave", this._onGridLeave.bind(this))
    this.listen(this._hourInput, "change", this._onTimeChange.bind(this))
    this.listen(this._minuteInput, "change", this._onTimeChange.bind(this))
    this.listen(this._doneBtn, "click", this._onDoneClick.bind(this))
    this.listen(this._popup, "keydown", this._onPopupKeydown.bind(this))
    this.listen(this.shadowRoot, "focusout", this._onFocusOut.bind(this))
    this.listen(document, "click", this._onDocClick.bind(this))

    /* Everything below paints the fresh shadow DOM from the fields. */
    this._syncPlaceholder()
    this._syncMode()
    this._syncEditable()
    this._syncAccessibility()
    this._syncDisplay()
    this._syncOpen()
    return
  }

  onDisconnected() {
    /* A removed picker must not keep tracking scroll/resize or trapping Tab. */
    this._releaseOverlay()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "value") {
      if (this._rendered === false) {
        this._valueReplayPending = true
        this._applyValue(newValue || "")
      } else if (this._valueReplayPending === true) {
        /* The same change was applied before the first render. */
        this._valueReplayPending = false
      } else {
        this._applyValue(newValue || "")
      }
    }
    if (name === "mode") {
      /* The value as it was last given is re-read under the new mode's format. */
      this._applyValue(this._rawValue)
      this._syncMode()
    }
    if (name === "placeholder") {
      this._syncPlaceholder()
    }
    if (name === "disabled" || name === "readonly" || name === "clearable") {
      this._syncEditable()
      this._syncClearBtn()
    }
    if (name === "required" && this._internals !== undefined) {
      this._refreshValidity()
    }
    if (name === "required" || name === "label" || name === "aria-label" || name === "aria-labelledby") {
      this._syncAccessibility()
    }
    if (name === "min" || name === "max" || name === "locale" || name === "first-day-of-week") {
      this._syncDisplay()
    }
    if (name === "open") {
      this._syncOpen()
    }
    return
  }

  onFormReset(initial) {
    this._applyValue(initial)
    return
  }

  onFormRestore(state) {
    if (typeof state === "string") {
      this._applyValue(state)
    }
    return
  }

  /* An ancestor <fieldset disabled> was switched on or off. */
  onFormDisabled(disabled) {
    this._formDisabled = disabled === true
    this._syncEditable()
    this._syncClearBtn()
    return
  }

  /* Typed text that is not a date keeps the form from submitting a stale value. */
  _customValidity() {
    const message = this._textInvalid === true ? t("mj.datePicker.invalidDate") : ""
    return message
  }

  _mode() {
    const raw = this.getAttribute("mode") || "date"
    const known = raw === "date" || raw === "time" || raw === "datetime" || raw === "range"
    const mode = known === true ? raw : "date"
    return mode
  }

  _locale() {
    const locale = this.getAttribute("locale") || navigator.language || "en"
    return locale
  }

  _formatter(options) {
    let formatter = null
    try {
      formatter = new Intl.DateTimeFormat(this._locale(), options)
    } catch (error) {
      /* An unknown locale tag falls back to the browser's. */
      formatter = new Intl.DateTimeFormat(undefined, options)
    }
    return formatter
  }

  /* 0 = Sunday ... 6 = Saturday: the attribute, else the locale's convention. */
  _firstDayOfWeek() {
    let first = 0

    const attr = this.getAttribute("first-day-of-week")
    const parsed = attr !== null ? parseInt(attr, 10) : NaN
    if (Number.isNaN(parsed) === false && parsed >= 0 && parsed <= 6) {
      first = parsed
    } else {
      try {
        const localeInfo = new Intl.Locale(this._locale())
        let weekInfo = null
        if (typeof localeInfo.getWeekInfo === "function") {
          weekInfo = localeInfo.getWeekInfo()
        } else if (localeInfo.weekInfo !== undefined) {
          weekInfo = localeInfo.weekInfo
        }
        if (weekInfo !== null && typeof weekInfo.firstDay === "number") {
          /* Intl counts 1 = Monday ... 7 = Sunday. */
          first = weekInfo.firstDay % 7
        }
      } catch (error) {
        first = 0
      }
    }

    return first
  }

  /* ----- value handling ----- */

  /*
   * Split a value into its parts for the current mode. Returns
   * `{ value, date, time, start, end }` where `value` is the canonical string
   * ("" when the text is not a valid value for the mode).
   */
  _parseValue(text) {
    const mode = this._mode()
    const raw = typeof text === "string" ? text.trim() : ""
    const parts = { value: "", date: null, time: null, start: null, end: null }

    if (mode === "time") {
      const time = parseIsoTime(raw)
      if (time !== null) {
        parts.time = time
        parts.value = formatIsoTime(time)
      }
    } else if (mode === "datetime") {
      const pieces = raw.split("T")
      const date = parseIsoDate(pieces[0])
      const time = pieces.length > 1 ? parseIsoTime(pieces[1]) : { hour: 0, minute: 0 }
      if (date !== null && time !== null) {
        parts.date = pieces[0]
        parts.time = time
        parts.value = `${pieces[0]}T${formatIsoTime(time)}`
      }
    } else if (mode === "range") {
      const pieces = raw.split("/")
      const start = parseIsoDate(pieces[0])
      const end = pieces.length > 1 ? parseIsoDate(pieces[1]) : null
      if (start !== null && end !== null) {
        /* ISO days sort as text, so the earlier one is always the start. */
        parts.start = pieces[0] <= pieces[1] ? pieces[0] : pieces[1]
        parts.end = pieces[0] <= pieces[1] ? pieces[1] : pieces[0]
        parts.value = `${parts.start}/${parts.end}`
      }
    } else {
      const datePart = raw.slice(0, 10)
      if (parseIsoDate(datePart) !== null) {
        parts.date = datePart
        parts.value = datePart
      }
    }

    return parts
  }

  /*
   * Take a value from the attribute, the property, or a form reset. Text that
   * is not valid for the mode clears the picker. No event is emitted.
   */
  _applyValue(text) {
    const parts = this._parseValue(text)
    this._rawValue = typeof text === "string" ? text : ""
    this._rangeStart = parts.start
    this._rangeEnd = parts.end
    this._hoverDate = null
    this._textInvalid = false
    this._setFormValue(parts.value)
    this._syncDisplay()
    return
  }

  /* The user chose `text`: store it and, when it differs, tell listeners. */
  _commitValue(text) {
    const previous = this._value || ""
    this._applyValue(text)
    if ((this._value || "") !== previous) {
      this._emitChange()
    }
    return
  }

  _emitChange() {
    const parts = this._parseValue(this._value || "")
    let date = null
    if (parts.date !== null) {
      date = parseIsoDate(parts.date)
      if (parts.time !== null) {
        date.setHours(parts.time.hour, parts.time.minute, 0, 0)
      }
    }
    this.emit("mj-change", {
      value: parts.value,
      date: date,
      startDate: parts.start !== null ? parseIsoDate(parts.start) : null,
      endDate: parts.end !== null ? parseIsoDate(parts.end) : null
    })
    return
  }

  _formatDay(isoDay) {
    const date = parseIsoDate(isoDay)
    const text = date !== null ? this._formatter({ dateStyle: "medium" }).format(date) : isoDay
    return text
  }

  /* The text shown in the field for a canonical value. */
  _formatForDisplay(value) {
    const parts = this._parseValue(value)
    let text = ""

    if (parts.value.length === 0) {
      text = ""
    } else if (parts.start !== null) {
      text = `${this._formatDay(parts.start)} – ${this._formatDay(parts.end)}`
    } else if (parts.date !== null && parts.time !== null) {
      const date = parseIsoDate(parts.date)
      date.setHours(parts.time.hour, parts.time.minute, 0, 0)
      text = this._formatter({ dateStyle: "medium", timeStyle: "short" }).format(date)
    } else if (parts.date !== null) {
      text = this._formatDay(parts.date)
    } else {
      text = parts.value
    }

    return text
  }

  /* ----- typed text ----- */

  /* Parse a typed day into YYYY-MM-DD, or null. */
  _parseTypedDay(text) {
    const typed = text.trim().replace(/,+$/, "").trim()
    let iso = null

    if (parseIsoDate(typed) !== null) {
      return typed
    }

    const numbers = typed.match(/\d+/g)
    const hasLetters = /\p{L}/u.test(typed)

    /* The locale's own order of day, month and year. */
    const order = this._formatter({ year: "numeric", month: "numeric", day: "numeric" })
      .formatToParts(new Date(2001, 10, 22))
      .filter((part) => part.type === "day" || part.type === "month" || part.type === "year")
      .map((part) => part.type)

    const build = (fields) => {
      let year = fields.year
      if (year < 100) {
        year = year + 2000
      }
      const candidate = isoFromParts(year, fields.month, fields.day)
      return parseIsoDate(candidate) !== null ? candidate : null
    }

    if (numbers !== null && numbers.length === 3 && hasLetters === false) {
      const fields = {}
      for (let index = 0; index < 3; index = index + 1) {
        fields[order[index]] = Number(numbers[index])
      }
      iso = build(fields)
    } else if (numbers !== null && numbers.length === 2 && hasLetters === true) {
      /* A month name with a day and a year, e.g. "15 mars 2026" or "Mar 15, 2026". */
      const lowered = typed.toLocaleLowerCase(this._locale())
      let month = 0
      for (let index = 0; index < 12 && month === 0; index = index + 1) {
        const reference = new Date(2001, index, 1)
        const longName = this._formatter({ month: "long" }).format(reference).toLocaleLowerCase(this._locale())
        const shortName = this._formatter({ month: "short" }).format(reference).toLocaleLowerCase(this._locale()).replace(/\.$/, "")
        if (lowered.includes(longName) === true || lowered.includes(shortName) === true) {
          month = index + 1
        }
      }
      if (month > 0) {
        const first = Number(numbers[0])
        const second = Number(numbers[1])
        const dayFirst = order.indexOf("day") < order.indexOf("year")
        const firstIsYear = numbers[0].length > 2 || (dayFirst === false && numbers[1].length <= 2)
        iso = firstIsYear === true
          ? build({ year: first, month: month, day: second })
          : build({ year: second, month: month, day: first })
      }
    }

    return iso
  }

  /* Parse a typed clock time ("14:30", "2:30 pm") into `{ hour, minute }`, or null. */
  _parseTypedTime(text) {
    let time = null

    const match = text.trim().match(/^(\d{1,2})[:.](\d{2})\s*([ap])?\.?\s*m?\.?$/i)
    if (match !== null) {
      let hour = Number(match[1])
      const minute = Number(match[2])
      const meridiem = match[3] !== undefined ? match[3].toLowerCase() : ""
      if (meridiem === "p" && hour < 12) {
        hour = hour + 12
      } else if (meridiem === "a" && hour === 12) {
        hour = 0
      }
      if (hour >= 0 && hour <= 23 && minute >= 0 && minute <= 59) {
        time = { hour: hour, minute: minute }
      }
    }

    return time
  }

  /* Turn what the user typed into a canonical value, or null when it is not one. */
  _parseTypedValue(text) {
    const mode = this._mode()
    const typed = text.trim()
    let value = null

    /* The canonical ISO form is always accepted. */
    const canonical = this._parseValue(typed)
    if (canonical.value.length > 0) {
      return canonical.value
    }

    if (mode === "time") {
      const time = this._parseTypedTime(typed)
      if (time !== null) {
        value = formatIsoTime(time)
      }
    } else if (mode === "datetime") {
      const timeMatch = typed.match(/(\d{1,2}[:.]\d{2}\s*(?:[ap]\.?\s*m\.?)?)\s*$/i)
      const time = timeMatch !== null ? this._parseTypedTime(timeMatch[1]) : { hour: 0, minute: 0 }
      const dayText = timeMatch !== null ? typed.slice(0, timeMatch.index) : typed
      const day = this._parseTypedDay(dayText.replace(/[\sT,]+$/, ""))
      if (day !== null && time !== null) {
        value = `${day}T${formatIsoTime(time)}`
      }
    } else if (mode === "range") {
      const pieces = typed.split(/\s+[–—-]\s+|\s+to\s+/i)
      if (pieces.length === 2) {
        const first = this._parseTypedDay(pieces[0])
        const second = this._parseTypedDay(pieces[1])
        if (first !== null && second !== null) {
          value = this._parseValue(`${first}/${second}`).value
        }
      }
    } else {
      value = this._parseTypedDay(typed)
    }

    return value
  }

  _onInputTyped() {
    this.emit("mj-input", { inputValue: this._dateInput.value })
    return
  }

  /*
   * Parse the field's text (Enter, blur). A valid date is committed; empty
   * text clears the value; anything else is flagged and blocks validity so
   * the text and the submitted value cannot silently disagree.
   */
  _commitTypedText() {
    if (this._isEditable() === false) {
      return
    }
    const typed = this._dateInput.value
    if (typed === this._formatForDisplay(this._value || "") && this._textInvalid === false) {
      return
    }

    if (typed.trim().length === 0) {
      this._commitValue("")
      return
    }

    const value = this._parseTypedValue(typed)
    const selectable = value !== null && this._isValueSelectable(value) === true
    if (selectable === true) {
      this._commitValue(value)
    } else {
      this._textInvalid = true
      this._field.classList.add("text-invalid")
      this._dateInput.setAttribute("aria-invalid", "true")
      this._refreshValidity()
    }
    return
  }

  /* A typed value must respect min / max like a clicked day does. */
  _isValueSelectable(value) {
    const parts = this._parseValue(value)
    let selectable = true
    if (parts.date !== null && this._isDateDisabled(parts.date) === true) {
      selectable = false
    }
    if (parts.start !== null && (this._isDateDisabled(parts.start) === true || this._isDateDisabled(parts.end) === true)) {
      selectable = false
    }
    return selectable
  }

  /* ----- field state ----- */

  /* Disabled by its own attribute or by an ancestor <fieldset disabled>. */
  _isDisabled() {
    const disabled = this.hasAttribute("disabled") === true || this._formDisabled === true
    return disabled
  }

  _isEditable() {
    const blocked = this._isDisabled() === true || this.hasAttribute("readonly") === true
    return blocked === false
  }

  /*
   * The text that names the field: the `label` attribute, then the host's
   * `aria-label`, then the elements named by the host's `aria-labelledby`,
   * then any <label> associated with the host (wrapping or `for`). The
   * inner input cannot point at light-DOM ids, so the text is copied.
   */
  _computeAccessibleName() {
    const labelAttr = (this.getAttribute("label") || "").trim()
    if (labelAttr.length > 0) {
      return labelAttr
    }
    const ariaLabel = (this.getAttribute("aria-label") || "").trim()
    if (ariaLabel.length > 0) {
      return ariaLabel
    }
    const labelledBy = (this.getAttribute("aria-labelledby") || "").trim()
    if (labelledBy.length > 0) {
      const root = this.getRootNode()
      const texts = []
      labelledBy.split(/\s+/).forEach((id) => {
        const target = typeof root.getElementById === "function" ? root.getElementById(id) : null
        if (target !== null) {
          texts.push(textExcluding(target, this))
        }
      })
      const joined = texts.filter((text) => text.length > 0).join(" ")
      if (joined.length > 0) {
        return joined
      }
    }
    let labels = []
    try {
      labels = this._internals !== null && this._internals.labels ? Array.from(this._internals.labels) : []
    } catch (error) {
      labels = []
    }
    const rtnval = labels
      .map((labelEl) => textExcluding(labelEl, this))
      .filter((text) => text.length > 0)
      .join(" ")
    return rtnval
  }

  /* Name the text field and mirror `required` onto it. */
  _syncAccessibility() {
    if (this._dateInput === undefined || this._dateInput === null) {
      return
    }
    const name = this._computeAccessibleName()
    if (name.length > 0) {
      this._dateInput.setAttribute("aria-label", name)
    } else {
      this._dateInput.removeAttribute("aria-label")
    }
    if (this.hasAttribute("required") === true) {
      this._dateInput.setAttribute("aria-required", "true")
    } else {
      this._dateInput.removeAttribute("aria-required")
    }
    return
  }

  /*
   * A click aimed at the host itself (not at a part inside it) is what an
   * associated <label> dispatches when it is clicked: move focus to the
   * text field the way a native control would.
   */
  _onHostClick(event) {
    const origin = event.composedPath()[0]
    if (origin === this && this._dateInput !== null && this._isDisabled() === false) {
      this._dateInput.focus()
    }
    return
  }

  _syncPlaceholder() {
    if (this._dateInput === undefined || this._dateInput === null) {
      return
    }
    const fallback = this._mode() === "time" ? t("mj.datePicker.selectTime") : t("mj.datePicker.selectDate")
    this._dateInput.placeholder = this.getAttribute("placeholder") || fallback
    return
  }

  /* Mirror disabled / readonly onto the inner controls. */
  _syncEditable() {
    if (this._dateInput === undefined || this._dateInput === null) {
      return
    }
    const disabled = this._isDisabled()
    const editable = this._isEditable()
    this._dateInput.disabled = disabled
    this._dateInput.readOnly = this.hasAttribute("readonly")
    this._calTrigger.disabled = editable === false
    this._clearBtn.disabled = editable === false
    if (editable === false && this.hasAttribute("open") === true) {
      this._close()
    }
    return
  }

  /* Show the parts of the dialog the mode uses. */
  _syncMode() {
    if (this._popup === undefined || this._popup === null) {
      return
    }
    const mode = this._mode()
    const timeOnly = mode === "time"
    this._calHeader.hidden = timeOnly
    this._dayGrid.hidden = timeOnly
    this._timePanel.hidden = (mode === "time" || mode === "datetime") === false
    this._popup.classList.toggle("time-only", timeOnly)
    this._popup.setAttribute("aria-label", timeOnly === true ? t("mj.datePicker.chooseTime") : t("mj.datePicker.chooseDate"))
    this._calTrigger.setAttribute("aria-label", timeOnly === true ? t("mj.datePicker.openTimePicker") : t("mj.datePicker.openCalendar"))
    this._clearBtn.setAttribute("aria-label", timeOnly === true ? t("mj.datePicker.clearTime") : t("mj.datePicker.clearDate"))
    this._syncPlaceholder()
    return
  }

  /* Write the current value into the field, the time inputs and the open calendar. */
  _syncDisplay() {
    if (this._dateInput === undefined || this._dateInput === null) {
      return
    }
    this._dateInput.value = this._formatForDisplay(this._value || "")
    this._dateInput.removeAttribute("aria-invalid")
    this._field.classList.remove("text-invalid")
    this._syncClearBtn()
    this._syncTimeInputs()
    if (this.hasAttribute("open") === true) {
      this._renderCalendar()
    }
    return
  }

  _syncClearBtn() {
    if (this._clearBtn === undefined || this._clearBtn === null) {
      return
    }
    const hasVal = (this._value || "").length > 0
    const clearable = this.hasAttribute("clearable")
    if (clearable === true && hasVal === true && this._isEditable() === true) {
      this._clearBtn.classList.remove("hidden")
    } else {
      this._clearBtn.classList.add("hidden")
    }
    return
  }

  _syncTimeInputs() {
    const parts = this._parseValue(this._value || "")
    if (parts.time !== null) {
      this._hourInput.value = pad2(parts.time.hour)
      this._minuteInput.value = pad2(parts.time.minute)
    } else if (this.shadowRoot.activeElement !== this._hourInput && this.shadowRoot.activeElement !== this._minuteInput) {
      this._hourInput.value = ""
      this._minuteInput.value = ""
    }
    this._hourInput.classList.remove("invalid")
    this._minuteInput.classList.remove("invalid")
    return
  }

  /* ----- open / close ----- */

  _open(focusDialog) {
    if (this._isEditable() === false) {
      return
    }
    if (this.hasAttribute("open") === true) {
      if (focusDialog === true) {
        this._focusDialog()
      }
      return
    }
    const proceed = this.emit("mj-open", {}, { cancelable: true })
    if (proceed === false) {
      return
    }
    this._focusDialogOnOpen = focusDialog === true
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

  /* Stop tracking the popup position and release the focus trap. */
  _releaseOverlay() {
    if (this._disposePosition !== null) {
      this._disposePosition()
      this._disposePosition = null
    }
    if (this._disposeTrap !== null) {
      /* Where focus goes on close is decided by `_syncOpen`, not by the trap. */
      this._disposeTrap({ restoreFocus: false })
      this._disposeTrap = null
    }
    return
  }

  /*
   * Bring the overlay machinery in line with the `open` attribute. Safe to
   * call before the first render (it returns) and repeatedly.
   */
  _syncOpen() {
    if (this._dateInput === undefined || this._dateInput === null) {
      return
    }
    const isOpen = this.hasAttribute("open")
    this._dateInput.setAttribute("aria-expanded", isOpen === true ? "true" : "false")

    if (isOpen === true) {
      if (this._disposePosition === null) {
        this._valueBeforeOpen = this._value || ""
        this._showValueMonth()
        this._renderCalendar()
        this._syncTimeInputs()
        this._disposePosition = autoPosition(this._popup, this._field, { placement: "bottom-start" })

        /*
         * The trap keeps Tab inside the dialog once focus is in it. Opening
         * from the text field leaves focus there so the user can keep typing.
         */
        const focusDialog = this._focusDialogOnOpen
        this._focusDialogOnOpen = false
        const initial = focusDialog === true ? this._dialogFocusTarget() : this._currentFocus()
        this._disposeTrap = trapFocus(this._popup, initial)
      }
    } else {
      /*
       * Focus returns to the field only when it was still inside the dialog
       * (Escape, a day pick, Done). After an outside click focus is already
       * where the user put it and must stay there.
       */
      const wasOpen = this._disposePosition !== null
      const focusInside = this._popup.contains(this.shadowRoot.activeElement)
      this._releaseOverlay()
      this._hoverDate = null
      if (wasOpen === true && focusInside === true) {
        this._dateInput.focus()
      }
    }
    return
  }

  /* The element that has focus now, so the trap can be set without moving it. */
  _currentFocus() {
    let current = this.shadowRoot.activeElement
    if (current === null) {
      current = document.activeElement
    }
    if (current === null || typeof current.focus !== "function") {
      current = document.body
    }
    return current
  }

  /* Where focus lands inside the dialog: the grid's tab stop, or the hour field. */
  _dialogFocusTarget() {
    let target = null
    if (this._mode() === "time") {
      target = this._hourInput
    } else {
      target = this._dayGrid.querySelector(".day-btn[tabindex='0']")
      if (target === null) {
        target = this.$(".cal-nav-btn")
      }
    }
    return target
  }

  _focusDialog() {
    const target = this._dialogFocusTarget()
    if (target !== null) {
      target.focus()
    }
    return
  }

  /* Open on the month of the value (or today), kept inside min / max. */
  _showValueMonth() {
    const parts = this._parseValue(this._value || "")
    let day = parts.date !== null ? parts.date : parts.start
    if (day === null) {
      day = isoFromDate(new Date())
    }

    const min = this._boundary("min")
    const max = this._boundary("max")
    if (min !== null && day < min) {
      day = min
    }
    if (max !== null && day > max) {
      day = max
    }

    const date = parseIsoDate(day)
    this._displayMonth = new Date(date.getFullYear(), date.getMonth(), 1)
    this._focusedDate = day
    return
  }

  /* The day part of `min` / `max` as YYYY-MM-DD, or null when absent or malformed. */
  _boundary(name) {
    const raw = (this.getAttribute(name) || "").slice(0, 10)
    const boundary = parseIsoDate(raw) !== null ? raw : null
    return boundary
  }

  _isDateDisabled(dateStr) {
    const min = this._boundary("min")
    const max = this._boundary("max")
    let disabled = false
    if (min !== null && dateStr < min) {
      disabled = true
    }
    if (max !== null && dateStr > max) {
      disabled = true
    }
    return disabled
  }

  /* ----- calendar ----- */

  /* Keep the grid's tab stop on an enabled day of the displayed month. */
  _ensureFocusedDate() {
    const year = this._displayMonth.getFullYear()
    const month = this._displayMonth.getMonth()
    const daysInMonth = new Date(year, month + 1, 0).getDate()
    const inMonth = (isoDay) => {
      const date = isoDay !== null ? parseIsoDate(isoDay) : null
      return date !== null && date.getFullYear() === year && date.getMonth() === month &&
        this._isDateDisabled(isoDay) === false
    }

    if (inMonth(this._focusedDate) === true) {
      return
    }

    const parts = this._parseValue(this._value || "")
    const candidates = [parts.date, parts.start, this._rangeStart, isoFromDate(new Date())]
    let chosen = null
    for (let index = 0; index < candidates.length && chosen === null; index = index + 1) {
      if (inMonth(candidates[index]) === true) {
        chosen = candidates[index]
      }
    }
    for (let day = 1; day <= daysInMonth && chosen === null; day = day + 1) {
      const isoDay = isoFromParts(year, month + 1, day)
      if (this._isDateDisabled(isoDay) === false) {
        chosen = isoDay
      }
    }

    this._focusedDate = chosen
    return
  }

  _renderCalendar() {
    if (this._dayGrid === undefined || this._dayGrid === null) {
      return
    }
    const year = this._displayMonth.getFullYear()
    const month = this._displayMonth.getMonth()

    const monthName = this._formatter({ month: "long", year: "numeric" }).format(this._displayMonth)
    this._monthYearEl.textContent = monthName
    this._dayGrid.setAttribute("aria-label", monthName)

    /* Rebuilding the grid destroys the focused day; remember to restore it. */
    const hadFocus = this._dayGrid.contains(this.shadowRoot.activeElement)

    this._ensureFocusedDate()

    const firstDayOfWeek = this._firstDayOfWeek()
    const shortFormat = this._formatter({ weekday: "short" })
    const longFormat = this._formatter({ weekday: "long" })
    const fullFormat = this._formatter({ dateStyle: "full" })

    /* 1 January 2023 is a Sunday, so day `1 + n` has weekday `n`. */
    const headers = []
    for (let column = 0; column < 7; column = column + 1) {
      const reference = new Date(2023, 0, 1 + ((firstDayOfWeek + column) % 7))
      headers.push(html`<div class="weekday-header" part="week-header" role="columnheader"
        aria-label="${longFormat.format(reference)}">${shortFormat.format(reference)}</div>`)
    }

    const leading = (new Date(year, month, 1).getDay() - firstDayOfWeek + 7) % 7
    const daysInMonth = new Date(year, month + 1, 0).getDate()
    const todayStr = isoFromDate(new Date())

    const cells = []
    for (let blank = 0; blank < leading; blank = blank + 1) {
      cells.push(html`<div role="gridcell" class="day-cell"></div>`)
    }
    for (let day = 1; day <= daysInMonth; day = day + 1) {
      const dateStr = isoFromParts(year, month + 1, day)
      const isToday = dateStr === todayStr
      const isDisabled = this._isDateDisabled(dateStr)
      const fullLabel = fullFormat.format(new Date(year, month, day))
      const ariaLabel = isToday === true ? t("mj.datePicker.todayLabel", { date: fullLabel }) : fullLabel
      const disabledAttr = isDisabled === true ? html` disabled` : ""

      cells.push(html`<div role="gridcell" part="day-cell" class="day-cell" aria-selected="false">
        <button
          class="${isToday === true ? "day-btn today" : "day-btn"}"
          type="button"
          tabindex="-1"
          aria-label="${ariaLabel}"
          data-date="${dateStr}"
          ${disabledAttr}
        >${day}</button>
      </div>`)
    }
    while (cells.length % 7 !== 0) {
      cells.push(html`<div role="gridcell" class="day-cell"></div>`)
    }

    const rows = [html`<div class="week-row" role="row">${headers}</div>`]
    for (let start = 0; start < cells.length; start = start + 7) {
      rows.push(html`<div class="week-row" part="week-row" role="row">${cells.slice(start, start + 7)}</div>`)
    }

    this._dayGrid.innerHTML = String(html`${rows}`)
    this._refreshDayStates()

    if (hadFocus === true) {
      const stop = this._dayGrid.querySelector(".day-btn[tabindex='0']")
      if (stop !== null) {
        stop.focus()
      }
    }
    return
  }

  /*
   * Mark the selected day or range and the tab stop on the rendered days.
   * Done in place so a hover preview or a new selection does not rebuild the
   * grid under the pointer or the focus.
   */
  _refreshDayStates() {
    const parts = this._parseValue(this._value || "")
    const mode = this._mode()

    let rangeStart = this._rangeStart
    let rangeEnd = this._rangeEnd
    let preview = false
    if (mode === "range" && rangeStart !== null && rangeEnd === null && this._hoverDate !== null) {
      /* One end chosen: preview the range up to the hovered day. */
      preview = true
      rangeEnd = this._hoverDate >= rangeStart ? this._hoverDate : rangeStart
      rangeStart = this._hoverDate >= rangeStart ? rangeStart : this._hoverDate
    }

    const buttons = this._dayGrid.querySelectorAll(".day-btn")
    buttons.forEach((btn) => {
      const dateStr = btn.dataset.date
      let selected = false
      let isStart = false
      let isEnd = false
      let isFill = false

      if (mode === "range") {
        if (rangeStart !== null && rangeEnd !== null) {
          isStart = dateStr === rangeStart
          isEnd = dateStr === rangeEnd
          isFill = dateStr > rangeStart && dateStr < rangeEnd
          selected = preview === true ? dateStr === this._rangeStart : (isStart || isEnd)
        } else if (rangeStart !== null) {
          selected = dateStr === rangeStart
        }
      } else {
        selected = parts.date !== null && dateStr === parts.date
      }

      const inSelection = selected === true || (preview === false && isFill === true)
      btn.classList.toggle("selected", selected)
      btn.classList.toggle("range-start", isStart && rangeStart !== rangeEnd)
      btn.classList.toggle("range-end", isEnd && rangeStart !== rangeEnd)
      btn.classList.toggle("range-fill", isFill)
      btn.parentElement.setAttribute("aria-selected", inSelection === true ? "true" : "false")
      btn.tabIndex = dateStr === this._focusedDate ? 0 : -1
    })
    return
  }

  _announceMonth() {
    const monthName = this._formatter({ month: "long", year: "numeric" }).format(this._displayMonth)
    announce(monthName, "polite")
    this.emit("mj-month-change", {
      month: this._displayMonth.getMonth() + 1,
      year: this._displayMonth.getFullYear()
    })
    return
  }

  _navigateMonth(delta) {
    this._displayMonth = new Date(this._displayMonth.getFullYear(), this._displayMonth.getMonth() + delta, 1)
    this._focusedDate = null
    this._announceMonth()
    this._renderCalendar()
    return
  }

  _onHeaderClick(event) {
    const btn = event.target.closest(".cal-nav-btn")
    if (btn !== null) {
      this._navigateMonth(Number(btn.dataset.months))
    }
    return
  }

  /* Move the grid's tab stop (and focus) to `isoDay`, turning the page if needed. */
  _moveFocusTo(isoDay) {
    if (this._isDateDisabled(isoDay) === true) {
      return
    }
    const date = parseIsoDate(isoDay)
    this._focusedDate = isoDay

    const sameMonth = date.getFullYear() === this._displayMonth.getFullYear() &&
      date.getMonth() === this._displayMonth.getMonth()
    if (sameMonth === false) {
      this._displayMonth = new Date(date.getFullYear(), date.getMonth(), 1)
      this._announceMonth()
      this._renderCalendar()
    } else {
      this._refreshDayStates()
    }

    const target = this._dayGrid.querySelector(".day-btn[tabindex='0']")
    if (target !== null) {
      target.focus()
    }
    return
  }

  _onDayClick(event) {
    const btn = event.target.closest(".day-btn")
    if (btn === null || btn.disabled === true || this._isEditable() === false) {
      return
    }
    const dateStr = btn.dataset.date
    const mode = this._mode()
    this._focusedDate = dateStr

    if (mode === "range") {
      const startsNewRange = this._rangeStart === null || this._rangeEnd !== null
      if (startsNewRange === true) {
        /* First click: one end is chosen, nothing is committed yet. */
        this._rangeStart = dateStr
        this._rangeEnd = null
        this._hoverDate = null
        this._refreshDayStates()
      } else {
        this._commitValue(`${this._rangeStart}/${dateStr}`)
        this._close()
      }
    } else if (mode === "datetime") {
      /* The dialog stays open so the time can be adjusted; Done closes it. */
      const time = this._readTimeInputs()
      const chosen = time !== null ? time : { hour: 0, minute: 0 }
      this._commitValue(`${dateStr}T${formatIsoTime(chosen)}`)
    } else {
      this._commitValue(dateStr)
      this._close()
    }
    return
  }

  _onDayHover(event) {
    const btn = event.target.closest(".day-btn")
    const previewing = this._mode() === "range" && this._rangeStart !== null && this._rangeEnd === null
    if (btn === null || previewing === false || btn.disabled === true) {
      return
    }
    if (this._hoverDate !== btn.dataset.date) {
      this._hoverDate = btn.dataset.date
      this._refreshDayStates()
    }
    return
  }

  _onGridLeave() {
    if (this._hoverDate !== null) {
      this._hoverDate = null
      this._refreshDayStates()
    }
    return
  }

  _onDayKeydown(event) {
    const btn = event.target.closest(".day-btn")
    if (btn === null) {
      return
    }
    const date = parseIsoDate(btn.dataset.date)
    const year = date.getFullYear()
    const month = date.getMonth()
    const day = date.getDate()

    /* Local calendar arithmetic: the Date constructor normalises overflow. */
    let target = null
    if (event.key === "ArrowLeft") {
      target = new Date(year, month, day - 1)
    } else if (event.key === "ArrowRight") {
      target = new Date(year, month, day + 1)
    } else if (event.key === "ArrowUp") {
      target = new Date(year, month, day - 7)
    } else if (event.key === "ArrowDown") {
      target = new Date(year, month, day + 7)
    } else if (event.key === "Home") {
      const offset = (date.getDay() - this._firstDayOfWeek() + 7) % 7
      target = new Date(year, month, day - offset)
    } else if (event.key === "End") {
      const offset = (date.getDay() - this._firstDayOfWeek() + 7) % 7
      target = new Date(year, month, day + (6 - offset))
    } else if (event.key === "PageUp") {
      target = shiftMonth(date, event.shiftKey === true ? -12 : -1)
    } else if (event.key === "PageDown") {
      target = shiftMonth(date, event.shiftKey === true ? 12 : 1)
    }

    if (target !== null) {
      event.preventDefault()
      this._moveFocusTo(isoFromDate(target))
    }
    return
  }

  /* ----- time panel ----- */

  /* The hour and minute fields as `{ hour, minute }`, or null when incomplete or out of range. */
  _readTimeInputs() {
    const hourText = this._hourInput.value.trim()
    const minuteText = this._minuteInput.value.trim()
    let time = null

    if (/^\d{1,2}$/.test(hourText) === true && /^\d{1,2}$/.test(minuteText) === true) {
      const hour = Number(hourText)
      const minute = Number(minuteText)
      if (hour <= 23 && minute <= 59) {
        time = { hour: hour, minute: minute }
      }
    }

    return time
  }

  _onTimeChange() {
    if (this._isEditable() === false) {
      return
    }
    const hourOk = /^\d{1,2}$/.test(this._hourInput.value.trim()) === true && Number(this._hourInput.value) <= 23
    const minuteOk = /^\d{1,2}$/.test(this._minuteInput.value.trim()) === true && Number(this._minuteInput.value) <= 59
    this._hourInput.classList.toggle("invalid", hourOk === false && this._hourInput.value !== "")
    this._minuteInput.classList.toggle("invalid", minuteOk === false && this._minuteInput.value !== "")

    const time = this._readTimeInputs()
    if (time === null) {
      return
    }

    if (this._mode() === "time") {
      this._commitValue(formatIsoTime(time))
    } else {
      /* Without a chosen day the time waits for the day click. */
      const parts = this._parseValue(this._value || "")
      if (parts.date !== null) {
        this._commitValue(`${parts.date}T${formatIsoTime(time)}`)
      }
    }
    return
  }

  _onDoneClick() {
    this._onTimeChange()
    this._close()
    return
  }

  /* ----- field and dialog events ----- */

  /* A click in the text field shows the calendar but leaves focus for typing. */
  _onInputClick() {
    this._open(false)
    return
  }

  _onTriggerClick() {
    if (this.hasAttribute("open") === true) {
      this._close()
    } else {
      this._open(true)
    }
    return
  }

  _onInputKeydown(event) {
    if (event.key === "ArrowDown") {
      event.preventDefault()
      this._commitTypedText()
      this._open(true)
    } else if (event.key === "Enter") {
      this._commitTypedText()
      if (this.hasAttribute("open") === true && this._textInvalid === false) {
        event.preventDefault()
        this._close()
      }
    } else if (event.key === "Escape" && this.hasAttribute("open") === true) {
      event.preventDefault()
      this._cancel()
    }
    return
  }

  _onPopupKeydown(event) {
    if (event.key === "Escape") {
      event.preventDefault()
      event.stopPropagation()
      this._cancel()
    }
    return
  }

  /* Escape: close, put back the value the dialog opened with, focus the field. */
  _cancel() {
    const before = this._valueBeforeOpen
    this._rangeStart = null
    this._rangeEnd = null
    if (before !== null && before !== (this._value || "")) {
      this._commitValue(before)
    } else {
      this._applyValue(this._value || "")
    }
    this._close()
    this._dateInput.focus()
    return
  }

  /* Focus moved to another control on the page: the dialog is dismissed. */
  _onFocusOut(event) {
    if (this.hasAttribute("open") === false) {
      return
    }
    const next = event.relatedTarget
    if (next !== null && next !== undefined && this.shadowRoot.contains(next) === false) {
      this._close()
    }
    return
  }

  _onClear() {
    if (this._isEditable() === false) {
      return
    }
    this._commitValue("")
    this._dateInput.focus()
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
    const anchor = this._dateInput !== undefined ? this._dateInput : null
    return anchor
  }

  /* ----- scriptable API ----- */

  /* The current value as an ISO 8601 string in the mode's format. */
  get value() {
    return this._value
  }

  set value(next) {
    const text = next !== null && next !== undefined ? String(next) : ""
    this._applyValue(text)
    return
  }

  /* The selected day (and time) as a local Date; null in time and range modes. */
  get valueAsDate() {
    const parts = this._parseValue(this._value || "")
    let date = null
    if (parts.date !== null) {
      date = parseIsoDate(parts.date)
      if (parts.time !== null) {
        date.setHours(parts.time.hour, parts.time.minute, 0, 0)
      }
    }
    return date
  }

  get startDate() {
    const date = this._rangeStart !== null ? parseIsoDate(this._rangeStart) : null
    return date
  }

  get endDate() {
    const date = this._rangeEnd !== null ? parseIsoDate(this._rangeEnd) : null
    return date
  }

  get displayMonth() {
    return new Date(this._displayMonth)
  }

  get open() {
    return this.hasAttribute("open")
  }

  set open(value) {
    if (value === true) {
      this._open(false)
    } else {
      this._close()
    }
    return
  }

  focus(options) {
    if (this._dateInput !== undefined && this._dateInput !== null) {
      this._dateInput.focus(options)
    }
    return
  }
}
