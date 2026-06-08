/*
 * mjcharactercounter.js
 *
 * <mj-character-counter> -- displays a live character or word count for a
 * text input or textarea. Updates via polite live-region announcements on
 * threshold crossings. Associates with the control via the `for` attribute.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { formatNumber } from "../core/intl.js";

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

export class MjCharacterCounter extends MjElement {
  static tagName = "mj-character-counter";
  static styles = STYLES;
  static watched = ["for", "max", "mode", "unit", "format", "warn-at", "error-at", "announce-at", "announce-interval", "disabled"];

  constructor() {
    super()
    this._controlRef = null
    this._observer = null
    this._current = 0
    this._wasExceeded = false
    this._wasWarned = false
    this._inputHandler = null

    if (!this.id) {
      this.id = nextId("mj-counter")
    }
  }

  render() {
    const markup = `
      <output class="counter" part="counter">
        <span class="count" part="count">0</span>
        <span class="separator" part="separator" style="display:none">/</span>
        <span class="max-val" part="max" style="display:none"></span>
      </output>
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
    this._attachControl()
    return
  }

  onConnected() {
    this._attachControl()
    return
  }

  onDisconnected() {
    this._detachControl()
    if (this._observer !== null) {
      this._observer.disconnect()
      this._observer = null
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "for") {
      this._detachControl()
      this._controlRef = null
      this._attachControl()
    }
    if (this._controlRef !== null) {
      this._update()
    }
    return
  }

  _attachControl() {
    const forValue = this.getAttribute("for") || ""
    if (forValue.length === 0) {
      return
    }
    const target = document.getElementById(forValue)
    if (target === null) {
      this._watchForTarget(forValue)
      return
    }
    this._controlRef = target
    this._inputHandler = this._onInput.bind(this)
    target.addEventListener("input", this._inputHandler)
    this._update()
    return
  }

  _detachControl() {
    if (this._controlRef !== null && this._inputHandler !== null) {
      this._controlRef.removeEventListener("input", this._inputHandler)
      this._inputHandler = null
    }
    this._removeExceededState()
    return
  }

  _onInput() {
    if (this.hasAttribute("disabled")) {
      return
    }
    this._update()
    return
  }

  _countValue(value) {
    const unit = this.getAttribute("unit") || "characters"
    if (unit === "words") {
      const trimmed = value.trim()
      if (trimmed.length === 0) {
        return 0
      }
      const words = trimmed.split(/\s+/).filter((w) => w.length > 0)
      return words.length
    }
    const chars = [...value]
    return chars.length
  }

  _update() {
    if (this._controlRef === null || this._countEl === null) {
      return
    }
    const value = this._controlRef.value || ""
    const current = this._countValue(value)
    this._current = current

    const maxAttr = this.getAttribute("max")
    const max = maxAttr !== null && maxAttr !== "" ? parseInt(maxAttr, 10) : null
    const remaining = max !== null ? max - current : null
    const exceeded = max !== null ? current > max : false

    this._renderDisplay(current, remaining, max)
    this._updateState(current, remaining, max, exceeded)

    const detail = {
      current,
      remaining,
      exceeded,
      unit: this.getAttribute("unit") || "characters"
    }
    this.emit("mj-count-change", detail)

    this._handleThresholds(current, remaining, max, exceeded)
    return
  }

  _renderDisplay(current, remaining, max) {
    const mode = this.getAttribute("mode") || "remaining"
    const format = this.getAttribute("format") || "compact"

    if (format === "used/max" && max !== null) {
      this._countEl.textContent = formatNumber(current)
      this._separatorEl.style.display = "inline"
      this._maxEl.style.display = "inline"
      this._maxEl.textContent = formatNumber(max)
    } else {
      this._separatorEl.style.display = "none"
      this._maxEl.style.display = "none"
      if (mode === "remaining" && remaining !== null) {
        this._countEl.textContent = formatNumber(remaining)
      } else {
        this._countEl.textContent = formatNumber(current)
      }
    }
    return
  }

  _updateState(current, remaining, max, exceeded) {
    if (max === null) {
      this.removeAttribute("data-state")
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
      if (this._controlRef !== null) {
        const curr = this._controlRef.getAttribute("aria-describedby") || ""
        const parts = curr.split(" ").filter((s) => s.length > 0)
        if (parts.indexOf(this.id) === -1) {
          parts.push(this.id)
          this._controlRef.setAttribute("aria-describedby", parts.join(" "))
        }
        this._controlRef.setAttribute("aria-invalid", "true")
      }
    } else {
      this._removeExceededState()
    }
    return
  }

  _removeExceededState() {
    if (this._controlRef === null) {
      return
    }
    const curr = this._controlRef.getAttribute("aria-describedby") || ""
    const parts = curr.split(" ").filter((s) => s.length > 0 && s !== this.id)
    if (parts.length > 0) {
      this._controlRef.setAttribute("aria-describedby", parts.join(" "))
    } else {
      this._controlRef.removeAttribute("aria-describedby")
    }
    this._controlRef.removeAttribute("aria-invalid")
    return
  }

  _handleThresholds(current, remaining, max, exceeded) {
    if (max === null || this._statusEl === null) {
      return
    }

    const announceAt = this._getThreshold("announce-at", 90)
    const announceInterval = parseInt(this.getAttribute("announce-interval") || "10", 10)
    const usedPct = max > 0 ? (current / max) * 100 : 0
    const unit = this.getAttribute("unit") || "characters"

    if (exceeded === true && this._wasExceeded === false) {
      this._wasExceeded = true
      const over = current - max
      const label = this.getAttribute("exceeded-label") || `${unit} over the limit`
      this._statusEl.textContent = `${formatNumber(over)} ${label}`
      this.emit("mj-exceed", { current, max })
    } else if (exceeded === false && this._wasExceeded === true) {
      this._wasExceeded = false
      this._statusEl.textContent = ""
      this.emit("mj-recover", { current, max })
    }

    const warnAt = this._getThreshold("warn-at", null)
    if (warnAt !== null && usedPct >= warnAt && this._wasWarned === false) {
      this._wasWarned = true
      this.emit("mj-warn", { current, remaining, threshold: warnAt })
    } else if (warnAt !== null && usedPct < warnAt) {
      this._wasWarned = false
    }

    if (remaining !== null && usedPct >= announceAt) {
      if (remaining <= 0 && exceeded === false) {
        const remLabel = this.getAttribute("remaining-label") || `${unit} remaining`
        this._statusEl.textContent = `0 ${remLabel}`
      } else if (remaining > 0) {
        const shouldAnnounce = remaining % announceInterval === 0 || remaining <= announceInterval
        if (shouldAnnounce === true) {
          const remLabel = this.getAttribute("remaining-label") || `${unit} remaining`
          this._statusEl.textContent = `${formatNumber(remaining)} ${remLabel}`
        }
      }
    }
    return
  }

  _getThreshold(attr, defaultVal) {
    const raw = this.getAttribute(attr)
    if (raw === null || raw === "") {
      return defaultVal
    }
    const parsed = parseFloat(raw)
    if (isNaN(parsed) === true) {
      return defaultVal
    }
    return parsed
  }

  _watchForTarget(forValue) {
    if (this._observer !== null) {
      this._observer.disconnect()
    }
    this._observer = new MutationObserver(() => {
      const target = document.getElementById(forValue)
      if (target !== null) {
        this._observer.disconnect()
        this._observer = null
        this._controlRef = target
        this._inputHandler = this._onInput.bind(this)
        target.addEventListener("input", this._inputHandler)
        this._update()
      }
    })
    this._observer.observe(document.body, { childList: true, subtree: true })
    this.onTeardown(() => {
      if (this._observer !== null) {
        this._observer.disconnect()
        this._observer = null
      }
    })
    return
  }

  /* ----- scriptable API ----- */

  get current() {
    return this._current
  }

  get remaining() {
    const maxAttr = this.getAttribute("max")
    if (maxAttr === null || maxAttr === "") {
      return null
    }
    const max = parseInt(maxAttr, 10)
    return max - this._current
  }

  get exceeded() {
    const maxAttr = this.getAttribute("max")
    if (maxAttr === null || maxAttr === "") {
      return false
    }
    const max = parseInt(maxAttr, 10)
    return this._current > max
  }

  get control() {
    return this._controlRef
  }

  /* Force a count refresh (for programmatic value changes). */
  sync() {
    this._update()
    return
  }
}
