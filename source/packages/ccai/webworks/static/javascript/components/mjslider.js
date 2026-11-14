/*
 * mjslider.js
 *
 * <mj-slider> -- single or dual-thumb range slider with tick marks,
 * value label, and full keyboard support.
 *
 * Value model: `this._valueA` (the value, or the lower value in range mode)
 * and `this._valueB` (the upper value) are the single source of truth; null
 * means "not set", which reads as `min` and `max` respectively. The `value`
 * and `value-end` attributes are the default values: they are applied when
 * first seen and when they themselves change, never when an unrelated
 * attribute changes, and a form reset returns to them. Positions are drawn
 * from the two fields on every render.
 *
 * Form value: single mode submits `name`=value. Range mode submits
 * `name-start`=value and `name-end`=value-end; when neither is given it
 * submits `name`="value,value-end".
 *
 * Validation: `required` means "moved off the default position", so the
 * slider is valueMissing while the value equals `min` (range mode: while the
 * range still spans `min`..`max`). The inline error (`error-message`
 * replaces its text) and `mj-invalid` appear once focus has left the
 * slider or a check / submit failed.
 *
 * `tickLabels` ([{ value, label }]) draws text labels under the track; a
 * thumb resting on a labelled value announces the label as its value text.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";

const STYLES = `
:host {
  display: block;
  font-family: var(--mj-font-sans);
  font-size: var(--mj-font-size-md);
}

.label {
  display: block;
  margin-bottom: var(--mj-space-1);
  font-size: var(--mj-font-size-sm);
  font-weight: var(--mj-font-weight-medium);
  color: var(--mj-text);
}
.label:empty { display: none; }

/* The padded wrapper, not the thin track, is the pointer target. */
.slider-wrap {
  position: relative;
  padding: var(--mj-space-3) 0;
  touch-action: none;
  cursor: pointer;
}

.track {
  position: relative;
  block-size: var(--mj-slider-track-height, 4px);
  background: var(--mj-bg-muted);
  border-radius: var(--mj-radius-pill);
}

.fill {
  position: absolute;
  inset-inline-start: var(--mj-slider-fill-start, 0%);
  inline-size: var(--mj-slider-fill-size, 0%);
  block-size: 100%;
  background: var(--mj-accent);
  border-radius: var(--mj-radius-pill);
  pointer-events: none;
}

/*
 * The thumb is centred on its position with logical margins instead of a
 * physical translate, so it sits on its value in both text directions.
 */
.thumb {
  position: absolute;
  top: 50%;
  inset-inline-start: var(--mj-slider-position, 0%);
  inline-size: var(--mj-slider-thumb-size, 20px);
  block-size: var(--mj-slider-thumb-size, 20px);
  margin-block-start: calc(var(--mj-slider-thumb-size, 20px) / -2);
  margin-inline-start: calc(var(--mj-slider-thumb-size, 20px) / -2);
  box-sizing: border-box;
  background: var(--mj-surface);
  border: 2px solid var(--mj-accent);
  border-radius: var(--mj-radius-circle);
  cursor: pointer;
  touch-action: none;
  transition: box-shadow var(--mj-motion-fast) var(--mj-motion-ease);
  outline: none;
}
.thumb[hidden] { display: none; }
.thumb:focus-visible {
  box-shadow: 0 0 0 var(--mj-focus-ring-width) var(--mj-focus-ring);
}
.thumb:hover { transform: scale(1.15); }
.thumb[data-active] { z-index: 1; }
.thumb[aria-disabled="true"] { cursor: not-allowed; opacity: 0.55; }
.thumb[aria-readonly="true"] { cursor: default; }
@media (prefers-reduced-motion: reduce) {
  .thumb { transition: none; }
  .thumb:hover { transform: none; }
}

.value-label {
  position: absolute;
  inset-block-end: calc(100% + var(--mj-space-2));
  inset-inline-start: 50%;
  transform: translateX(-50%);
  background: var(--mj-text);
  color: var(--mj-surface);
  font-size: var(--mj-font-size-xs);
  padding: 2px var(--mj-space-1);
  border-radius: var(--mj-radius-sm);
  white-space: nowrap;
  pointer-events: none;
  display: none;
}
:host(:dir(rtl)) .value-label { transform: translateX(50%); }

/* The bubble appears only with show-value-label: while dragging, on keyboard focus. */
:host([show-value-label]) .thumb[data-active] .value-label,
:host([show-value-label]) .thumb:focus-visible .value-label { display: block; }

.ticks {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.tick {
  position: absolute;
  top: 50%;
  inset-inline-start: var(--mj-slider-position, 0%);
  inline-size: var(--mj-slider-tick-size, 4px);
  block-size: var(--mj-slider-tick-size, 4px);
  margin-block-start: calc(var(--mj-slider-tick-size, 4px) / -2);
  margin-inline-start: calc(var(--mj-slider-tick-size, 4px) / -2);
  background: var(--mj-border-strong);
  border-radius: var(--mj-radius-circle);
}

/* Below the track, clear of the thumb (which overhangs the track by half its size). */
.tick-labels {
  position: relative;
  block-size: 1.5em;
  margin-top: calc(var(--mj-slider-thumb-size, 20px) / 2);
  pointer-events: none;
}
.tick-labels[hidden] { display: none; }
.tick-label {
  position: absolute;
  inset-block-start: 0;
  inset-inline-start: var(--mj-slider-position, 0%);
  transform: translateX(-50%);
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
  white-space: nowrap;
}
:host(:dir(rtl)) .tick-label { transform: translateX(50%); }
/* Labels on the track ends line up with the ends instead of overhanging them. */
.tick-label[data-edge="start"] { transform: none; }
.tick-label[data-edge="end"] { transform: translateX(-100%); }
:host(:dir(rtl)) .tick-label[data-edge="start"] { transform: none; }
:host(:dir(rtl)) .tick-label[data-edge="end"] { transform: translateX(100%); }

.thumb[aria-invalid="true"] { border-color: var(--mj-color-danger); }

.track-labels {
  display: flex;
  justify-content: space-between;
  margin-top: var(--mj-space-1);
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
}

.below { margin-top: var(--mj-space-2); }
.help { font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }
.help:empty { display: none; }
.error { font-size: var(--mj-font-size-sm); color: var(--mj-color-danger); display: none; }
.error[data-visible] { display: block; }

:host([disabled]) .slider-wrap, .slider-wrap[data-disabled] { opacity: 0.55; pointer-events: none; }
:host([readonly]) .slider-wrap { cursor: default; }

/*
 * Vertical: the track runs along the block axis, the minimum at the bottom.
 * Positions are applied from the block end instead of the inline start.
 */
:host([orientation="vertical"]) .slider-wrap {
  display: inline-block;
  padding: 0 var(--mj-space-3);
  block-size: var(--mj-slider-length, 200px);
}
:host([orientation="vertical"]) .track {
  inline-size: var(--mj-slider-track-height, 4px);
  block-size: 100%;
}
:host([orientation="vertical"]) .fill {
  inset-inline-start: 0;
  inline-size: 100%;
  inset-block-end: var(--mj-slider-fill-start, 0%);
  block-size: var(--mj-slider-fill-size, 0%);
}
:host([orientation="vertical"]) .thumb,
:host([orientation="vertical"]) .tick {
  top: auto;
  inset-inline-start: 50%;
  inset-block-end: var(--mj-slider-position, 0%);
  margin-block-start: 0;
}
:host([orientation="vertical"]) .thumb { margin-block-end: calc(var(--mj-slider-thumb-size, 20px) / -2); }
:host([orientation="vertical"]) .tick { margin-block-end: calc(var(--mj-slider-tick-size, 4px) / -2); }
:host([orientation="vertical"]) .value-label {
  inset-block-end: auto;
  top: 50%;
  inset-inline-start: calc(100% + var(--mj-space-2));
  transform: translateY(-50%);
}
:host([orientation="vertical"]) .track-labels { display: none; }
:host([orientation="vertical"]) .tick-labels {
  position: absolute;
  inset-block: 0;
  inset-inline-start: calc(var(--mj-space-3) + var(--mj-slider-track-height, 4px) / 2 + var(--mj-slider-thumb-size, 20px) / 2 + var(--mj-space-1));
  block-size: auto;
  margin-top: 0;
}
:host([orientation="vertical"]) .tick-label {
  inset-block-start: auto;
  inset-inline-start: 0;
  inset-block-end: var(--mj-slider-position, 0%);
  transform: translateY(50%);
}
:host([orientation="vertical"]) .tick-label[data-edge="start"] { transform: none; }
:host([orientation="vertical"]) .tick-label[data-edge="end"] { transform: translateY(100%); }
`;

/* Arrow keys step once; Page Up / Page Down step this many times. */
const PAGE_STEP_MULTIPLIER = 10;

/* More ticks than this are not drawn. */
const MAXIMUM_TICKS = 50;

/*
 * The accessible name the page gave the host: `aria-labelledby`, then
 * `aria-label`, then an associated <label for> / wrapping <label>, then an
 * <mj-label for>. The shadow control cannot see any of these across the
 * shadow boundary, so the component copies the text onto it.
 */
function resolveHostLabel(host, internals) {
  let name = ""
  const root = host.getRootNode()

  const labelledBy = host.getAttribute("aria-labelledby") || ""
  if (labelledBy.trim().length > 0 && typeof root.getElementById === "function") {
    const parts = []
    const ids = labelledBy.trim().split(/\s+/)
    for (let index = 0; index < ids.length; index = index + 1) {
      const labelNode = root.getElementById(ids[index])
      if (labelNode !== null) {
        parts.push(labelNode.textContent.trim())
      }
    }
    name = parts.join(" ").trim()
  }

  if (name.length === 0) {
    name = (host.getAttribute("aria-label") || "").trim()
  }

  if (name.length === 0 && internals !== null && internals !== undefined && internals.labels !== undefined) {
    const parts = []
    for (let index = 0; index < internals.labels.length; index = index + 1) {
      parts.push(internals.labels[index].textContent.trim())
    }
    name = parts.join(" ").trim()
  }

  if (name.length === 0 && host.id.length > 0 && typeof root.querySelector === "function") {
    const mjLabel = root.querySelector(`mj-label[for="${CSS.escape(host.id)}"]`)
    if (mjLabel !== null) {
      name = mjLabel.textContent.trim()
    }
  }

  return name
}

/* Number of digits after the decimal point in the shortest form of `value`. */
function countDecimals(value) {
  let decimals = 0

  if (Number.isFinite(value) === true) {
    const text = String(value)
    const exponentIndex = text.indexOf("e-")
    if (exponentIndex >= 0) {
      const mantissa = text.slice(0, exponentIndex)
      const mantissaDot = mantissa.indexOf(".")
      const mantissaDecimals = mantissaDot >= 0 ? mantissa.length - mantissaDot - 1 : 0
      decimals = parseInt(text.slice(exponentIndex + 2), 10) + mantissaDecimals
    } else {
      const dot = text.indexOf(".")
      if (dot >= 0) {
        decimals = text.length - dot - 1
      }
    }
  }

  return Math.min(decimals, 20)
}

/* Parse a plain decimal attribute or property value; NaN when unusable. */
function parsePlainNumber(value) {
  let parsed = NaN

  if (typeof value === "number") {
    parsed = Number.isFinite(value) === true ? value : NaN
  } else if (value !== null && value !== undefined) {
    const text = String(value).trim()
    if (text.length > 0) {
      const candidate = Number(text)
      parsed = Number.isFinite(candidate) === true ? candidate : NaN
    }
  }

  return parsed
}

export class MjSlider extends FormControlMixin(MjElement) {
  static tagName = "mj-slider";
  static styles = STYLES;
  static watched = [
    "label", "help-text", "error-message", "value", "value-end",
    "min", "max", "step", "range", "orientation",
    "disabled", "readonly", "required", "ticks", "show-value-label",
    "name", "name-start", "name-end", "aria-label", "aria-labelledby"
  ];

  constructor() {
    super()
    this._initFormControl()

    /* Current values; null means "not set" (reads as min / max). */
    this._valueA = null
    this._valueB = null

    /* The attribute texts most recently applied to the two values. */
    this._appliedValueAttribute = null
    this._appliedValueEndAttribute = null

    /* "a" or "b" while a thumb is being dragged, otherwise null. */
    this._dragging = null

    /* Values when the current drag started, to detect a real change. */
    this._dragStartA = 0
    this._dragStartB = 0

    /* True while an ancestor <fieldset disabled> disables the control. */
    this._formDisabled = false

    this._tickLabels = []

    /* Errors are shown once focus has left the slider or a check failed. */
    this._showErrors = false

    /* min|max and tick settings a console message was last logged for. */
    this._reportedRange = null
    this._reportedTicks = null

    this._helpId = nextId("mjsl-help")
    this._errorId = nextId("mjsl-error")
    this._thumbAId = nextId("mjsl-thumb-a")
    this._thumbBId = nextId("mjsl-thumb-b")
  }

  render() {
    const markup = html`
      <label class="label" part="label"></label>
      <div class="slider-wrap" part="slider-wrap">
        <div class="track" part="track">
          <div class="fill" part="fill"></div>
          <div class="ticks" part="ticks" aria-hidden="true"></div>
          <div class="thumb" part="thumb thumb-a" id="${this._thumbAId}"
            role="slider" tabindex="0"
            aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"
          >
            <span class="value-label" part="value-label" aria-hidden="true"></span>
          </div>
          <div class="thumb" part="thumb thumb-b" id="${this._thumbBId}"
            role="slider" tabindex="0"
            aria-valuemin="0" aria-valuemax="100" aria-valuenow="100"
            hidden
          >
            <span class="value-label" part="value-label" aria-hidden="true"></span>
          </div>
        </div>
        <div class="tick-labels" part="tick-labels" aria-hidden="true" hidden></div>
        <div class="track-labels">
          <slot name="start-label"></slot>
          <slot name="end-label"></slot>
        </div>
      </div>
      <div class="below">
        <span class="help" part="help" id="${this._helpId}"></span>
        <span class="error" part="error" id="${this._errorId}" role="alert"></span>
      </div>
    `
    return markup
  }

  afterRender() {
    this._labelEl = this.$(".label")
    this._wrapEl = this.$(".slider-wrap")
    this._trackEl = this.$(".track")
    this._fillEl = this.$(".fill")
    this._ticksEl = this.$(".ticks")
    this._tickLabelsEl = this.$(".tick-labels")
    this._thumbA = this.$(`#${this._thumbAId}`)
    this._thumbB = this.$(`#${this._thumbBId}`)
    this._helpEl = this.$(".help")
    this._errorEl = this.$(".error")

    /* The shadow DOM is new: no drag can be in progress in it. */
    this._dragging = null
    this._syncAll()

    this.listen(this._wrapEl, "pointerdown", this._onPointerdown.bind(this))
    this.listen(window, "pointermove", this._onPointermove.bind(this))
    this.listen(window, "pointerup", this._onPointerup.bind(this))
    this.listen(window, "pointercancel", this._onPointerEnd.bind(this))
    this.listen(this._thumbA, "lostpointercapture", this._onPointerEnd.bind(this))
    this.listen(this._thumbB, "lostpointercapture", this._onPointerEnd.bind(this))
    this.listen(this._thumbA, "keydown", (event) => this._onKeydown(event, "a"))
    this.listen(this._thumbB, "keydown", (event) => this._onKeydown(event, "b"))
    this.listen(this._labelEl, "click", this._onLabelClick.bind(this))
    this.listen(this, "click", this._onHostClick.bind(this))
    this.listen(this.shadowRoot, "focusout", this._onFocusout.bind(this))
    this.listen(this, "invalid", this._onInvalid.bind(this))
    return
  }

  onConnected() {
    /* Labels outside the shadow root can only be resolved once connected. */
    this._syncAccessibleName()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    /*
     * The value attributes are read only when they themselves change. Any
     * other attribute (label, disabled, ...) leaves the current position,
     * which the user may have moved, untouched.
     */
    if (name === "value" && newValue !== this._appliedValueAttribute) {
      this._appliedValueAttribute = newValue
      this._valueA = this._attributeToValue(newValue)
    }
    if (name === "value-end" && newValue !== this._appliedValueEndAttribute) {
      this._appliedValueEndAttribute = newValue
      this._valueB = this._attributeToValue(newValue)
    }

    if (this._thumbA === undefined || this._thumbA === null) {
      this._publishFormValue()
      return
    }

    this._syncAll()
    return
  }

  /* ----- numeric helpers ----- */

  _getMin() {
    const parsed = parsePlainNumber(this.getAttribute("min"))
    const min = Number.isNaN(parsed) === true ? 0 : parsed
    return min
  }

  _getMax() {
    const parsed = parsePlainNumber(this.getAttribute("max"))
    const min = this._getMin()
    let max = Number.isNaN(parsed) === true ? 100 : parsed
    if (max < min) {
      /* An inverted range collapses to the minimum. */
      max = min
    }
    return max
  }

  /* `step` must be a positive number; "any", 0 and junk fall back to 1. */
  _getStep() {
    const parsed = parsePlainNumber(this.getAttribute("step"))
    const step = Number.isNaN(parsed) === true || parsed <= 0 ? 1 : parsed
    return step
  }

  _clamp(value) {
    const clamped = Math.min(this._getMax(), Math.max(this._getMin(), value))
    return clamped
  }

  /*
   * Move `value` to the nearest step counted from `min`, rounded to the
   * precision of `step` and `min` so 0.1 + 0.2 is 0.3, not 0.30000000000000004.
   */
  _snapToStep(value) {
    const step = this._getStep()
    const min = this._getMin()
    const precision = Math.max(countDecimals(step), countDecimals(min))
    const snapped = Math.round((value - min) / step) * step + min
    const rounded = Number(snapped.toFixed(precision))
    return rounded
  }

  /* Snap and clamp a value coming from an attribute, property or pointer. */
  _normalize(value) {
    const normalized = this._clamp(this._snapToStep(value))
    return normalized
  }

  _attributeToValue(attributeValue) {
    const parsed = parsePlainNumber(attributeValue)
    const value = Number.isNaN(parsed) === true ? null : parsed
    return value
  }

  _isRange() {
    return this.hasAttribute("range")
  }

  _isVertical() {
    return this.getAttribute("orientation") === "vertical"
  }

  /* The value, or the lower value in range mode. */
  _currentA() {
    let value = this._valueA === null ? this._getMin() : this._normalize(this._valueA)
    if (this._isRange() === true && this._valueB !== null) {
      value = Math.min(value, this._normalize(this._valueB))
    }
    return value
  }

  /* The upper value in range mode. */
  _currentB() {
    const upper = this._valueB === null ? this._getMax() : this._normalize(this._valueB)
    const value = Math.max(upper, this._currentA())
    return value
  }

  _percent(value) {
    const min = this._getMin()
    const max = this._getMax()
    let percent = 0
    if (max > min) {
      percent = ((value - min) / (max - min)) * 100
    }
    return percent
  }

  _formatValue(value) {
    const locale = document.documentElement.lang || navigator.language || "en-US"
    let formatted = String(value)
    try {
      formatted = new Intl.NumberFormat(locale, { maximumFractionDigits: 20 }).format(value)
    } catch (error) {
      formatted = String(value)
    }
    return formatted
  }

  /* The control is disabled by its own attribute or by a disabled fieldset. */
  _isDisabled() {
    const disabled = this.hasAttribute("disabled") === true || this._formDisabled === true
    return disabled
  }

  _isInteractive() {
    const interactive = this._isDisabled() === false && this.hasAttribute("readonly") === false
    return interactive
  }

  /* ----- rendering ----- */

  _syncAll() {
    const label = this.getAttribute("label") || ""
    const helpText = this.getAttribute("help-text") || ""
    const disabled = this._isDisabled()
    const readonly = this.hasAttribute("readonly")
    const required = this.hasAttribute("required")
    const isRange = this._isRange()
    const orientation = this._isVertical() === true ? "vertical" : "horizontal"
    const min = this._getMin()
    const max = this._getMax()

    const rangeKey = `${this.getAttribute("min")}|${this.getAttribute("max")}`
    if (parsePlainNumber(this.getAttribute("max")) < min && this._reportedRange !== rangeKey) {
      this._reportedRange = rangeKey
      console.error("[mj-slider] max is less than min; the slider is fixed at min")
    }

    this._labelEl.textContent = label
    this._helpEl.textContent = helpText
    this._wrapEl.toggleAttribute("data-disabled", disabled === true)
    this._thumbB.hidden = isRange === false

    const thumbs = [this._thumbA, this._thumbB]
    for (let index = 0; index < thumbs.length; index = index + 1) {
      const thumb = thumbs[index]
      thumb.setAttribute("aria-orientation", orientation)
      thumb.setAttribute("aria-valuemin", String(min))
      thumb.setAttribute("aria-valuemax", String(max))
      thumb.setAttribute("aria-disabled", disabled === true ? "true" : "false")
      thumb.setAttribute("aria-required", required === true ? "true" : "false")
      if (readonly === true) {
        thumb.setAttribute("aria-readonly", "true")
      } else {
        thumb.removeAttribute("aria-readonly")
      }

      /* A disabled slider is not a tab stop. */
      if (disabled === true) {
        thumb.removeAttribute("tabindex")
      } else {
        thumb.setAttribute("tabindex", "0")
      }
    }

    this._syncAccessibleName()
    this._renderTicks()
    this._renderTickLabels()
    this._renderPositions()
    this._publishFormValue()
    this._renderValidity(false)
    return
  }

  /* Help text and a shown error describe both thumbs. */
  _updateDescribedBy() {
    const ids = []
    if (this._helpEl.textContent.length > 0) {
      ids.push(this._helpId)
    }
    if (this._errorEl.hasAttribute("data-visible") === true) {
      ids.push(this._errorId)
    }
    const thumbs = [this._thumbA, this._thumbB]
    for (let index = 0; index < thumbs.length; index = index + 1) {
      if (ids.length > 0) {
        thumbs[index].setAttribute("aria-describedby", ids.join(" "))
      } else {
        thumbs[index].removeAttribute("aria-describedby")
      }
    }
    return
  }

  /*
   * Name the thumbs: the `label`, or failing that the name given to the
   * host from outside, or a generic word, so a thumb is never unnamed.
   */
  _syncAccessibleName() {
    if (this._thumbA === undefined || this._thumbA === null) {
      return
    }

    const label = this.getAttribute("label") || ""
    const hostLabel = resolveHostLabel(this, this._internals)
    const explicit = this.hasAttribute("aria-label") === true || this.hasAttribute("aria-labelledby") === true

    let name = label
    if (hostLabel.length > 0 && (explicit === true || label.length === 0)) {
      name = hostLabel
    }

    if (this._isRange() === true) {
      this._thumbA.setAttribute("aria-label", name.length > 0 ? t("mj.slider.minimumNamed", { name: name }) : t("mj.slider.minimum"))
      this._thumbB.setAttribute("aria-label", name.length > 0 ? t("mj.slider.maximumNamed", { name: name }) : t("mj.slider.maximum"))
    } else {
      this._thumbA.setAttribute("aria-label", name.length > 0 ? name : t("mj.slider.value"))
    }
    return
  }

  _renderTicks() {
    this._ticksEl.textContent = ""
    if (this.hasAttribute("ticks") === false) {
      return
    }

    const min = this._getMin()
    const max = this._getMax()
    const step = this._getStep()
    const count = Math.round((max - min) / step) + 1

    if (count > MAXIMUM_TICKS) {
      const ticksKey = `${min}|${max}|${step}`
      if (this._reportedTicks !== ticksKey) {
        this._reportedTicks = ticksKey
        console.warn("[mj-slider] too many ticks; hiding tick marks (use a coarser step)")
      }
      return
    }

    for (let index = 0; index < count; index = index + 1) {
      const tick = document.createElement("span")
      tick.className = "tick"
      tick.style.setProperty("--mj-slider-position", `${this._percent(min + index * step)}%`)
      this._ticksEl.appendChild(tick)
    }
    return
  }

  /*
   * The labels of `tickLabels` that fall inside min..max, placed along the
   * track. Labels are plain text.
   */
  _renderTickLabels() {
    this._tickLabelsEl.textContent = ""
    const min = this._getMin()
    const max = this._getMax()
    let count = 0

    for (let index = 0; index < this._tickLabels.length; index = index + 1) {
      const entry = this._tickLabels[index]
      const value = entry !== null && entry !== undefined ? parsePlainNumber(entry.value) : NaN
      if (Number.isNaN(value) === true || value < min || value > max) {
        continue
      }
      const text = entry.label !== null && entry.label !== undefined ? String(entry.label) : ""
      const label = document.createElement("span")
      label.className = "tick-label"
      label.setAttribute("part", "tick-label")
      const percent = this._percent(value)
      label.style.setProperty("--mj-slider-position", `${percent}%`)
      if (percent <= 0) {
        label.setAttribute("data-edge", "start")
      } else if (percent >= 100) {
        label.setAttribute("data-edge", "end")
      }
      label.textContent = text
      this._tickLabelsEl.appendChild(label)
      count = count + 1
    }

    this._tickLabelsEl.hidden = count === 0
    return
  }

  /* The text for a value: its tick label when it has one, else the number. */
  _valueText(value) {
    let text = this._formatValue(value)
    for (let index = 0; index < this._tickLabels.length; index = index + 1) {
      const entry = this._tickLabels[index]
      if (entry !== null && entry !== undefined && parsePlainNumber(entry.value) === value) {
        const label = entry.label !== null && entry.label !== undefined ? String(entry.label) : ""
        if (label.length > 0) {
          text = label
        }
      }
    }
    return text
  }

  /* Draw thumbs, fill and ARIA values from the current values. */
  _renderPositions() {
    const valueA = this._currentA()
    const percentA = this._percent(valueA)
    const textA = this._valueText(valueA)

    this._thumbA.style.setProperty("--mj-slider-position", `${percentA}%`)
    this._thumbA.setAttribute("aria-valuenow", String(valueA))
    this._thumbA.setAttribute("aria-valuetext", textA)
    this._thumbA.querySelector(".value-label").textContent = textA

    if (this._isRange() === true) {
      const valueB = this._currentB()
      const percentB = this._percent(valueB)
      const textB = this._valueText(valueB)

      this._thumbB.style.setProperty("--mj-slider-position", `${percentB}%`)
      this._thumbB.setAttribute("aria-valuenow", String(valueB))
      this._thumbB.setAttribute("aria-valuetext", textB)
      this._thumbB.querySelector(".value-label").textContent = textB

      this._fillEl.style.setProperty("--mj-slider-fill-start", `${percentA}%`)
      this._fillEl.style.setProperty("--mj-slider-fill-size", `${percentB - percentA}%`)
    } else {
      this._fillEl.style.setProperty("--mj-slider-fill-start", "0%")
      this._fillEl.style.setProperty("--mj-slider-fill-size", `${percentA}%`)
    }
    return
  }

  /* ----- form value ----- */

  /*
   * Publish the current values to the form. Range mode sends both ends:
   * under `name-start` / `name-end`, or as "lower,upper" under `name` when
   * neither is given.
   */
  _publishFormValue() {
    const valueA = this._currentA()
    this._value = String(valueA)

    if (this._internals !== null && this._internals !== undefined) {
      if (this._isRange() === true) {
        const valueB = this._currentB()
        const nameStart = this.getAttribute("name-start") || ""
        const nameEnd = this.getAttribute("name-end") || ""
        const state = `${valueA},${valueB}`

        if (nameStart.length > 0 || nameEnd.length > 0) {
          const entries = new FormData()
          if (nameStart.length > 0) {
            entries.append(nameStart, String(valueA))
          }
          if (nameEnd.length > 0) {
            entries.append(nameEnd, String(valueB))
          }
          this._internals.setFormValue(entries, state)
        } else {
          this._internals.setFormValue(state, state)
        }
      } else {
        this._internals.setFormValue(String(valueA), String(valueA))
      }
    }

    this._refreshValidity()
    return
  }

  /* ----- value changes ----- */

  _eventDetail() {
    const detail = {
      value: this._currentA(),
      valueEnd: this._isRange() === true ? this._currentB() : undefined
    }
    return detail
  }

  /*
   * Move one thumb to `value` on behalf of the user. In range mode a thumb
   * stops at the other one. Returns true when a value actually changed.
   */
  _moveThumb(thumb, value) {
    const beforeA = this._currentA()
    const beforeB = this._currentB()
    const target = this._normalize(value)

    if (thumb === "a") {
      this._valueA = this._isRange() === true ? Math.min(target, beforeB) : target
    } else {
      this._valueB = Math.max(target, beforeA)
    }

    const changed = this._currentA() !== beforeA || this._currentB() !== beforeB
    if (changed === true) {
      this._renderPositions()
      this._publishFormValue()
      this._renderValidity(false)
    }
    return changed
  }

  /* Map a pointer position to a value along the track. */
  _pointerToValue(event) {
    const rect = this._trackEl.getBoundingClientRect()
    let fraction = 0

    if (this._isVertical() === true) {
      /* The minimum is at the bottom. */
      fraction = rect.height > 0 ? (rect.bottom - event.clientY) / rect.height : 0
    } else {
      fraction = rect.width > 0 ? (event.clientX - rect.left) / rect.width : 0
      if (getComputedStyle(this._trackEl).direction === "rtl") {
        /* The track starts at the right edge in a right-to-left page. */
        fraction = 1 - fraction
      }
    }

    fraction = Math.max(0, Math.min(1, fraction))
    const min = this._getMin()
    const max = this._getMax()
    const value = this._normalize(min + fraction * (max - min))
    return value
  }

  /* The thumb a press on the track should move. */
  _nearestThumb(value) {
    let thumb = "a"
    if (this._isRange() === true) {
      const valueA = this._currentA()
      const valueB = this._currentB()
      const distanceA = Math.abs(value - valueA)
      const distanceB = Math.abs(value - valueB)
      if (distanceB < distanceA) {
        thumb = "b"
      } else if (distanceA === distanceB) {
        /* Overlapping thumbs: the side of the press decides. */
        thumb = value > valueB ? "b" : "a"
      }
    }
    return thumb
  }

  _thumbElement(thumb) {
    const element = thumb === "a" ? this._thumbA : this._thumbB
    return element
  }

  _onPointerdown(event) {
    if (event.button !== 0 || this._isInteractive() === false) {
      return
    }

    const value = this._pointerToValue(event)
    let thumb = null
    if (event.target === this._thumbA || this._thumbA.contains(event.target) === true) {
      thumb = "a"
    } else if (event.target === this._thumbB || this._thumbB.contains(event.target) === true) {
      thumb = "b"
    }

    const onThumb = thumb !== null
    if (onThumb === false) {
      thumb = this._nearestThumb(value)
    } else if (this._isRange() === true && this._currentA() === this._currentB()) {
      /*
       * Two thumbs on the same spot: the top one was hit, but the thumb to
       * move is decided by the first movement (see _onPointermove).
       */
      thumb = "b"
    }

    event.preventDefault()
    this._dragging = thumb
    this._dragStartA = this._currentA()
    this._dragStartB = this._currentB()

    const element = this._thumbElement(thumb)
    element.setAttribute("data-active", "")
    element.focus()
    try {
      element.setPointerCapture(event.pointerId)
    } catch (error) {
      /* No active pointer with this id (synthetic event): drag without capture. */
    }

    if (onThumb === false) {
      const changed = this._moveThumb(thumb, value)
      if (changed === true) {
        this.emit("mj-input", this._eventDetail())
      }
    }
    return
  }

  _onPointermove(event) {
    if (this._dragging === null) {
      return
    }

    const value = this._pointerToValue(event)

    /*
     * In range mode the dragged thumb passes through the other one: when it
     * crosses, the two swap roles so value <= value-end always holds.
     */
    if (this._isRange() === true) {
      if (this._dragging === "b" && value < this._currentA()) {
        this._switchDraggedThumb("a")
      } else if (this._dragging === "a" && value > this._currentB()) {
        this._switchDraggedThumb("b")
      }
    }

    const changed = this._moveThumb(this._dragging, value)
    if (changed === true) {
      this.emit("mj-input", this._eventDetail())
    }
    return
  }

  _switchDraggedThumb(thumb) {
    const previous = this._thumbElement(this._dragging)
    const next = this._thumbElement(thumb)

    /* Park the thumb being left on the other thumb's position. */
    if (thumb === "a") {
      this._valueB = this._currentA()
    } else {
      this._valueA = this._currentB()
    }

    previous.removeAttribute("data-active")
    next.setAttribute("data-active", "")
    next.focus()
    this._dragging = thumb
    return
  }

  _onPointerup(event) {
    this._endDrag(true)
    return
  }

  /* pointercancel / lostpointercapture: the drag is over, keep the value. */
  _onPointerEnd(event) {
    this._endDrag(true)
    return
  }

  _endDrag(commit) {
    if (this._dragging === null) {
      return
    }

    this._thumbA.removeAttribute("data-active")
    this._thumbB.removeAttribute("data-active")
    this._dragging = null

    const changed = this._currentA() !== this._dragStartA || this._currentB() !== this._dragStartB
    if (commit === true && changed === true) {
      this.emit("mj-change", this._eventDetail())
    }
    return
  }

  _onKeydown(event, thumb) {
    if (this._isInteractive() === false) {
      return
    }

    const step = this._getStep()
    const key = event.key
    const current = thumb === "a" ? this._currentA() : this._currentB()
    let target = null

    if (key === "ArrowRight" || key === "ArrowUp") {
      target = current + step
    } else if (key === "ArrowLeft" || key === "ArrowDown") {
      target = current - step
    } else if (key === "PageUp") {
      target = current + step * PAGE_STEP_MULTIPLIER
    } else if (key === "PageDown") {
      target = current - step * PAGE_STEP_MULTIPLIER
    } else if (key === "Home") {
      target = this._getMin()
    } else if (key === "End") {
      target = this._getMax()
    }

    if (target === null) {
      return
    }

    event.preventDefault()

    const changed = this._moveThumb(thumb, target)
    if (changed === true) {
      this.emit("mj-input", this._eventDetail())
      this.emit("mj-change", this._eventDetail())
    }
    return
  }

  /* The visible label behaves like a <label for>: it focuses the thumb. */
  _onLabelClick(event) {
    if (this._isDisabled() === false) {
      this._thumbA.focus()
    }
    return
  }

  /*
   * Activating an associated <label> clicks the host; move focus to the
   * thumb as a native control would.
   */
  _onHostClick(event) {
    const path = event.composedPath()
    if (path.length > 0 && path[0] === this && this._isDisabled() === false) {
      this._thumbA.focus()
    }
    return
  }

  /* Focus left both thumbs: validate where the slider was left. */
  _onFocusout(event) {
    const next = event.relatedTarget
    const staysInside = next !== null && next !== undefined && this.shadowRoot.contains(next) === true
    if (staysInside === true) {
      return
    }
    this._showErrors = true
    this._refreshValidity()
    this._renderValidity(true)
    return
  }

  /* A failed checkValidity() / reportValidity() / form submit. */
  _onInvalid(event) {
    this._showErrors = true
    this._renderValidity(true)
    return
  }

  /* ----- validation ----- */

  /*
   * Show or hide the inline error from the current validity. `error-message`
   * replaces the built-in text but never makes a valid slider look invalid.
   * `announce` is true when the user (leaving the slider) or a submit
   * attempt triggered the check; only then is `mj-invalid` emitted.
   */
  _renderValidity(announce) {
    if (this._errorEl === undefined || this._errorEl === null) {
      return
    }
    const message = this.validationMessage
    const invalid = message.length > 0 && this._showErrors === true
    const thumbs = [this._thumbA, this._thumbB]

    if (invalid === true) {
      const override = this.getAttribute("error-message") || ""
      const displayMessage = override.length > 0 ? override : message
      this._errorEl.textContent = displayMessage
      this._errorEl.setAttribute("data-visible", "")
      for (let index = 0; index < thumbs.length; index = index + 1) {
        thumbs[index].setAttribute("aria-invalid", "true")
      }
      this._updateDescribedBy()
      if (announce === true) {
        this.emit("mj-invalid", { validationMessage: displayMessage })
      }
    } else {
      this._errorEl.textContent = ""
      this._errorEl.removeAttribute("data-visible")
      for (let index = 0; index < thumbs.length; index = index + 1) {
        thumbs[index].removeAttribute("aria-invalid")
      }
      this._updateDescribedBy()
    }
    return
  }

  /*
   * `required` means the slider was moved off its default position: the
   * value is not `min` (range mode: the range does not span min..max). The
   * form value is never empty, so the mixin's generic check would never fire.
   */
  _refreshValidity() {
    if (this._internals === null || this._internals === undefined) {
      return
    }

    let untouched = this._currentA() === this._getMin()
    if (this._isRange() === true) {
      untouched = untouched === true && this._currentB() === this._getMax()
    }

    if (this.hasAttribute("required") === true && untouched === true) {
      const message = this.getAttribute("required-message") || t("core.required")
      const anchor = this._validationAnchor()
      if (anchor !== null && anchor !== undefined) {
        this._internals.setValidity({ valueMissing: true }, message, anchor)
      } else {
        this._internals.setValidity({ valueMissing: true }, message)
      }
    } else {
      this._internals.setValidity({})
    }
    return
  }

  _validationAnchor() {
    const anchor = this._thumbA !== undefined && this._thumbA !== null ? this._thumbA : null
    return anchor
  }

  /* ----- form callbacks ----- */

  onFormReset(initial) {
    this._showErrors = false
    this._valueA = this._attributeToValue(this.getAttribute("value"))
    this._valueB = this._attributeToValue(this.getAttribute("value-end"))
    this._afterProgrammaticChange()
    return
  }

  onFormRestore(state) {
    if (typeof state === "string" && state.length > 0) {
      const parts = state.split(",")
      this._valueA = this._attributeToValue(parts[0])
      if (parts.length > 1) {
        this._valueB = this._attributeToValue(parts[1])
      }
    }
    this._afterProgrammaticChange()
    return
  }

  onFormDisabled(disabled) {
    this._formDisabled = disabled === true
    if (this._thumbA !== undefined && this._thumbA !== null) {
      this._endDrag(false)
      this._syncAll()
    }
    return
  }

  _afterProgrammaticChange() {
    if (this._thumbA !== undefined && this._thumbA !== null) {
      this._renderPositions()
    }
    this._publishFormValue()
    this._renderValidity(false)
    return
  }

  /* ----- public API ----- */

  get value() {
    return String(this._currentA())
  }

  set value(next) {
    this._valueA = this._attributeToValue(next)
    this._afterProgrammaticChange()
    return
  }

  get valueEnd() {
    return String(this._currentB())
  }

  set valueEnd(next) {
    this._valueB = this._attributeToValue(next)
    this._afterProgrammaticChange()
    return
  }

  get valueAsNumber() {
    return this._currentA()
  }

  set valueAsNumber(next) {
    this.value = next
    return
  }

  get valueStartAsNumber() {
    return this._currentA()
  }

  get valueEndAsNumber() {
    return this._currentB()
  }

  get tickLabels() {
    return this._tickLabels
  }

  set tickLabels(labels) {
    this._tickLabels = Array.isArray(labels) === true ? labels.slice() : []
    if (this._thumbA !== undefined && this._thumbA !== null) {
      this._renderTickLabels()
      this._renderPositions()
    }
    return
  }

  checkValidity() {
    this._refreshValidity()
    const valid = super.checkValidity()
    return valid
  }

  reportValidity() {
    this._refreshValidity()
    const valid = super.reportValidity()
    return valid
  }

  focus(options) {
    if (this._thumbA !== undefined && this._thumbA !== null) {
      this._thumbA.focus(options)
    }
    return
  }
}
