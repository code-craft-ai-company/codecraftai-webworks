/*
 * mjcharactercounter.js
 *
 * <mj-character-counter> -- displays a live character or word count for a
 * text input or textarea. The visible count is silent; a separate polite
 * live region announces threshold crossings. Associates with the control via
 * the `for` attribute.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { formatNumber, t } from "../core/intl.js";
import {
  findById, waitForId, deferUntilDefined, ariaTargetOf, addAriaReference, removeAriaReference
} from "../core/aria.js";

const STYLES = `
:host {
  display: inline-block;
  font-size: var(--mj-counter-font-size, var(--mj-font-size-xs));
  color: var(--mj-counter-color, var(--mj-text-muted));
}

:host([disabled]) {
  color: var(--mj-counter-disabled-color, var(--mj-text-muted));
  opacity: 0.55;
}

:host([data-state="warning"]) {
  color: var(--mj-counter-warn-color, var(--mj-color-warning, #b45309));
}

:host([data-state="error"]) {
  color: var(--mj-counter-error-color, var(--mj-color-danger, #b91c1c));
}

.counter {
  display: inline-flex;
  align-items: baseline;
  gap: var(--mj-space-1);
}

.status {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0 0 0 0);
  clip-path: inset(50%);
  white-space: nowrap;
}
`;

/*
 * Announcement keys of the built-in units; each is a plural entry whose form
 * follows the plural rules of the active locale. Other units use the
 * generic keys, which insert the unit name as written.
 */
const REMAINING_LABEL_KEYS = {
  characters: "mj.characterCounter.charactersRemaining",
  words: "mj.characterCounter.wordsRemaining"
};

const EXCEEDED_LABEL_KEYS = {
  characters: "mj.characterCounter.charactersExceeded",
  words: "mj.characterCounter.wordsExceeded"
};

export class MjCharacterCounter extends MjElement {
  static tagName = "mj-character-counter";
  static styles = STYLES;
  static watched = [
    "for", "max", "mode", "unit", "format", "warn-at", "error-at", "announce-at",
    "announce-interval", "disabled", "remaining-label", "exceeded-label"
  ];

  constructor() {
    super()

    /* Shadow references; null until the first render. */
    this._counterEl = null
    this._countEl = null
    this._separatorEl = null
    this._maxEl = null
    this._statusEl = null

    this._controlRef = null
    this._stopWaiting = null
    this._listeningTo = null
    this._listeningForm = null

    this._current = 0
    this._wasExceeded = false
    this._wasWarned = false

    /* The detail of the last mj-count-change, to emit only real changes. */
    this._lastEmitted = null

    /* The remaining count that was last announced, to announce each once. */
    this._lastAnnounced = null

    /* True while this element is the one that set aria-invalid on the control. */
    this._setInvalidState = false
    this._previousInvalid = null

    this._onControlInput = this._handleControlInput.bind(this)
    this._onFormReset = this._handleFormReset.bind(this)
  }

  render() {
    const markup = `
      <span class="counter" part="counter">
        <span class="count" part="count">0</span>
        <span class="separator" part="separator" hidden>/</span>
        <span class="max-val" part="max" hidden></span>
      </span>
      <span class="status" role="status" aria-live="polite" aria-atomic="true"></span>
    `
    return markup
  }

  afterRender() {
    this._counterEl = this.$(".counter")
    this._countEl = this.$(".count")
    this._separatorEl = this.$(".separator")
    this._maxEl = this.$(".max-val")
    this._statusEl = this.$(".status")
    return
  }

  onConnected() {
    /*
     * The id is assigned here, not in the constructor: a custom element
     * constructor must not add attributes (document.createElement fails).
     */
    if (this.id.length === 0) {
      this.id = nextId("mj-counter")
    }
    this._attachControl()
    return
  }

  onDisconnected() {
    this._detachControl()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._countEl === undefined || this._countEl === null || this.isConnected === false) {
      return
    }
    if (name === "for") {
      this._detachControl()
      this._attachControl()
    } else {
      /* Attribute-driven refreshes update the display without emitting. */
      this._update(false)
    }
    return
  }

  /* ----- control wiring ----- */

  /*
   * Resolve the `for` target and listen to it. This is the single place a
   * listener is added, and it always detaches first, so repeated calls never
   * stack handlers.
   */
  _attachControl() {
    this._detachControl()

    const forValue = this.getAttribute("for") || ""
    if (forValue.length === 0) {
      return
    }

    const target = findById(this, forValue)
    if (target === null) {
      this._stopWaiting = waitForId(this, forValue, () => {
        this._stopWaiting = null
        this._attachControl()
      })
      return
    }

    const pending = deferUntilDefined(target, () => {
      if (this.isConnected === true) {
        this._attachControl()
      }
    })
    if (pending === true) {
      return
    }

    this._controlRef = target
    target.addEventListener("input", this._onControlInput)
    target.addEventListener("change", this._onControlInput)
    this._listeningTo = target

    const form = target.form
    if (form !== null && form !== undefined && typeof form.addEventListener === "function") {
      form.addEventListener("reset", this._onFormReset)
      this._listeningForm = form
    }

    this._update(false)
    return
  }

  _detachControl() {
    if (this._stopWaiting !== null) {
      this._stopWaiting()
      this._stopWaiting = null
    }
    if (this._listeningTo !== null) {
      this._listeningTo.removeEventListener("input", this._onControlInput)
      this._listeningTo.removeEventListener("change", this._onControlInput)
      this._listeningTo = null
    }
    if (this._listeningForm !== null) {
      this._listeningForm.removeEventListener("reset", this._onFormReset)
      this._listeningForm = null
    }
    this._removeExceededState()
    this._controlRef = null
    return
  }

  _handleControlInput() {
    if (this.hasAttribute("disabled") === true) {
      return
    }
    this._update(true)
    return
  }

  _handleFormReset() {
    /* The controls take their reset values after the reset event. */
    queueMicrotask(() => {
      if (this._controlRef !== null) {
        this._update(true)
      }
    })
    return
  }

  /* ----- counting ----- */

  _countValue(value) {
    const unit = this.getAttribute("unit") || "characters"
    let count = 0

    if (unit === "words") {
      const trimmed = value.trim()
      if (trimmed.length > 0) {
        const words = trimmed.split(/\s+/).filter((word) => word.length > 0)
        count = words.length
      }
    } else {
      const chars = [...value]
      count = chars.length
    }
    return count
  }

  _readMax() {
    const maxAttr = this.getAttribute("max")
    let max = null
    if (maxAttr !== null && maxAttr !== "") {
      const parsed = parseInt(maxAttr, 10)
      if (isNaN(parsed) === false) {
        max = parsed
      }
    }
    return max
  }

  /*
   * Recount and refresh the display, state and announcements. `notify` is
   * true for user-driven changes; mj-count-change is emitted only then and
   * only when the numbers actually changed.
   */
  _update(notify) {
    if (this._controlRef === null || this._countEl === undefined || this._countEl === null) {
      return
    }

    const rawValue = this._controlRef.value
    const value = rawValue !== null && rawValue !== undefined ? String(rawValue) : ""
    const current = this._countValue(value)
    this._current = current

    const max = this._readMax()
    const remaining = max !== null ? max - current : null
    const exceeded = max !== null ? current > max : false
    const unit = this.getAttribute("unit") || "characters"

    this._renderDisplay(current, remaining, max)
    this._updateState(current, max, exceeded)

    const last = this._lastEmitted
    const changed = last === null || last.current !== current || last.remaining !== remaining ||
      last.exceeded !== exceeded || last.unit !== unit

    if (changed === true) {
      const detail = { current: current, remaining: remaining, exceeded: exceeded, unit: unit }
      this._lastEmitted = detail
      if (notify === true) {
        this.emit("mj-count-change", detail)
      }
    }

    this._handleThresholds(current, remaining, max, exceeded, notify)
    return
  }

  _renderDisplay(current, remaining, max) {
    const mode = this.getAttribute("mode") || "remaining"
    const format = this.getAttribute("format") || "compact"

    if (format === "used/max" && max !== null) {
      this._countEl.textContent = formatNumber(current)
      this._separatorEl.hidden = false
      this._maxEl.hidden = false
      this._maxEl.textContent = formatNumber(max)
    } else {
      this._separatorEl.hidden = true
      this._maxEl.hidden = true
      if (mode === "remaining" && remaining !== null) {
        this._countEl.textContent = formatNumber(remaining)
      } else {
        this._countEl.textContent = formatNumber(current)
      }
    }
    return
  }

  _updateState(current, max, exceeded) {
    if (max === null) {
      this.removeAttribute("data-state")
      this._removeExceededState()
      return
    }

    const errorAt = this._getThreshold("error-at", 100)
    const warnAt = this._getThreshold("warn-at", null)
    const usedPct = max > 0 ? (current / max) * 100 : 0

    if (exceeded === true || usedPct >= errorAt) {
      this.setAttribute("data-state", "error")
    } else if (warnAt !== null && usedPct >= warnAt) {
      this.setAttribute("data-state", "warning")
    } else {
      this.removeAttribute("data-state")
    }

    if (exceeded === true) {
      this._applyExceededState()
    } else {
      this._removeExceededState()
    }
    return
  }

  /*
   * While over the limit the control is described by the counter and marked
   * invalid. aria-invalid is only touched when nothing else has already set
   * it, and only that change is undone later.
   */
  _applyExceededState() {
    const control = this._controlRef
    if (control === null) {
      return
    }

    addAriaReference(control, "describedby", this)

    const target = ariaTargetOf(control)
    if (this._setInvalidState === false && target.getAttribute("aria-invalid") !== "true") {
      this._previousInvalid = target.getAttribute("aria-invalid")
      target.setAttribute("aria-invalid", "true")
      this._setInvalidState = true
    }
    return
  }

  _removeExceededState() {
    const control = this._controlRef
    if (control === null) {
      return
    }

    removeAriaReference(control, "describedby", this)

    if (this._setInvalidState === true) {
      const target = ariaTargetOf(control)
      if (target.getAttribute("aria-invalid") === "true") {
        if (this._previousInvalid !== null) {
          target.setAttribute("aria-invalid", this._previousInvalid)
        } else {
          target.removeAttribute("aria-invalid")
        }
      }
      this._setInvalidState = false
      this._previousInvalid = null
    }
    return
  }

  /* ----- announcements ----- */

  /*
   * Build an announcement such as "5 characters remaining". The label
   * attribute may contain a {count} token; without one the formatted count
   * is placed in front of it. Without the attribute the localized default
   * for the unit is used ("1 character remaining"); `exceeded` picks the
   * over-the-limit wording instead of the remaining one.
   */
  _formatAnnouncement(count, labelAttribute, exceeded) {
    const formatted = formatNumber(count)
    const custom = this.getAttribute(labelAttribute)
    let message = ""

    if (custom !== null && custom.length > 0) {
      if (custom.indexOf("{count}") !== -1) {
        message = custom.split("{count}").join(formatted)
      } else {
        message = `${formatted} ${custom}`
      }
    } else {
      const unit = this.getAttribute("unit") || "characters"
      const keys = exceeded === true ? EXCEEDED_LABEL_KEYS : REMAINING_LABEL_KEYS
      const params = { count: count, countText: formatted, unit: unit }

      if (Object.prototype.hasOwnProperty.call(keys, unit) === true) {
        message = t(keys[unit], params)
      } else if (exceeded === true) {
        message = t("mj.characterCounter.unitExceeded", params)
      } else {
        message = t("mj.characterCounter.unitRemaining", params)
      }
    }
    return message
  }

  _handleThresholds(current, remaining, max, exceeded, notify) {
    if (max === null || this._statusEl === null) {
      return
    }

    const announceAt = this._getThreshold("announce-at", 90)
    const parsedInterval = parseInt(this.getAttribute("announce-interval") || "10", 10)
    const announceInterval = isNaN(parsedInterval) === false && parsedInterval > 0 ? parsedInterval : 10
    const usedPct = max > 0 ? (current / max) * 100 : 0

    if (exceeded === true && this._wasExceeded === false) {
      this._wasExceeded = true
      this._lastAnnounced = null
      this._statusEl.textContent = this._formatAnnouncement(current - max, "exceeded-label", true)
      if (notify === true) {
        this.emit("mj-exceed", { current: current, max: max })
      }
    } else if (exceeded === false && this._wasExceeded === true) {
      this._wasExceeded = false
      this._statusEl.textContent = ""
      if (notify === true) {
        this.emit("mj-recover", { current: current, max: max })
      }
    }

    const warnAt = this._getThreshold("warn-at", null)
    if (warnAt !== null && usedPct >= warnAt && this._wasWarned === false) {
      this._wasWarned = true
      if (notify === true) {
        this.emit("mj-warn", { current: current, remaining: remaining, threshold: warnAt })
      }
    } else if (warnAt !== null && usedPct < warnAt) {
      this._wasWarned = false
    }

    if (exceeded === true || remaining === null) {
      return
    }

    if (usedPct < announceAt) {
      /* Left the announcement zone: stay quiet and forget the last message. */
      if (this._lastAnnounced !== null) {
        this._lastAnnounced = null
        this._statusEl.textContent = ""
      }
      return
    }

    /*
     * Inside the zone, speak when entering it, on each multiple of the
     * interval and when the limit is reached -- not on every keystroke.
     */
    const entering = this._lastAnnounced === null
    const onInterval = remaining % announceInterval === 0
    if ((entering === true || onInterval === true) && this._lastAnnounced !== remaining) {
      this._lastAnnounced = remaining
      this._statusEl.textContent = this._formatAnnouncement(remaining, "remaining-label", false)
    }
    return
  }

  _getThreshold(attr, defaultVal) {
    const raw = this.getAttribute(attr)
    let threshold = defaultVal
    if (raw !== null && raw !== "") {
      const parsed = parseFloat(raw)
      if (isNaN(parsed) === false) {
        threshold = parsed
      }
    }
    return threshold
  }

  /* ----- scriptable API ----- */

  get current() {
    return this._current
  }

  get remaining() {
    const max = this._readMax()
    const remaining = max !== null ? max - this._current : null
    return remaining
  }

  get exceeded() {
    const max = this._readMax()
    const exceeded = max !== null ? this._current > max : false
    return exceeded
  }

  get control() {
    return this._controlRef
  }

  /* Force a count refresh (for programmatic value changes). */
  sync() {
    this._update(true)
    return
  }
}
