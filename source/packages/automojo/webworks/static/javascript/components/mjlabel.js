/*
 * mjlabel.js
 *
 * <mj-label> -- renders a visible, accessible label associated with a form
 * control. Wraps a native <label> for click-to-focus; renders optional required
 * or optional indicators; exposes a suffix slot for inline help-icon triggers.
 */

import { MjElement } from "../core/mjelement.js";

const STYLES = `
:host {
  display: inline-flex;
  align-items: baseline;
  gap: var(--mj-label-gap, var(--mj-space-1));
}

:host([layout="inline"]) {
  flex-direction: row;
  align-items: center;
}

.label {
  display: inline-flex;
  align-items: baseline;
  gap: var(--mj-label-gap, var(--mj-space-1));
  font-size: var(--mj-label-font-size, var(--mj-font-size-sm));
  font-weight: var(--mj-label-font-weight, var(--mj-font-weight-medium));
  color: var(--mj-label-color, var(--mj-text));
  cursor: default;
}

:host([disabled]) .label {
  color: var(--mj-label-disabled-color, var(--mj-text-muted));
  opacity: 0.6;
}

:host([visually-hidden]) .label {
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

.indicator {
  color: var(--mj-label-required-color, var(--mj-color-danger, #b91c1c));
}

.indicator--optional {
  color: var(--mj-text-muted);
  font-weight: var(--mj-font-weight-regular);
}

.suffix {
  display: inline-flex;
  align-items: center;
}
`;

export class MjLabel extends MjElement {
  static tagName = "mj-label";
  static styles = STYLES;
  static watched = ["for", "required", "optional", "disabled", "layout", "visually-hidden", "required-label", "optional-label"];

  constructor() {
    super()
    this._labelEl = null
    this._indicatorEl = null
  }

  render() {
    const markup = `
      <label class="label" part="label">
        <slot></slot>
      </label>
      <span class="suffix" part="suffix">
        <slot name="suffix"></slot>
      </span>
    `
    return markup
  }

  afterRender() {
    this._labelEl = this.$(".label")
    this.listen(this._labelEl, "click", this._onClick.bind(this))
    this._syncFor()
    this._syncIndicator()
    return
  }

  onConnected() {
    this._syncFor()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._labelEl === null) {
      return
    }
    if (name === "for") {
      this._syncFor()
    }
    if (name === "required" || name === "optional" || name === "required-label" || name === "optional-label") {
      this._syncIndicator()
    }
    return
  }

  _syncFor() {
    const forValue = this.getAttribute("for") || ""
    if (forValue.length > 0) {
      this._labelEl.setAttribute("for", forValue)
    } else {
      this._labelEl.removeAttribute("for")
    }
    return
  }

  _syncIndicator() {
    const existing = this._labelEl.querySelector(".indicator")
    if (existing !== null) {
      existing.remove()
    }

    const required = this.hasAttribute("required")
    const optional = this.hasAttribute("optional") && required === false

    if (required === true) {
      const span = document.createElement("span")
      span.className = "indicator"
      span.setAttribute("part", "indicator")
      span.setAttribute("aria-hidden", "true")
      span.textContent = this.getAttribute("required-label") || "*"
      this._labelEl.appendChild(span)
    } else if (optional === true) {
      const span = document.createElement("span")
      span.className = "indicator indicator--optional"
      span.setAttribute("part", "indicator")
      span.setAttribute("aria-hidden", "true")
      span.textContent = this.getAttribute("optional-label") || "(optional)"
      this._labelEl.appendChild(span)
    }
    return
  }

  _onClick() {
    const forValue = this.getAttribute("for") || ""
    let control = null
    if (forValue.length > 0) {
      control = document.getElementById(forValue)
    }
    this.emit("mj-click", { control })
    return
  }

  /* ----- scriptable API ----- */

  get control() {
    const forValue = this.getAttribute("for") || ""
    if (forValue.length === 0) {
      return null
    }
    const found = document.getElementById(forValue)
    return found
  }

  get htmlFor() {
    const val = this.getAttribute("for") || ""
    return val
  }

  set htmlFor(val) {
    this.setAttribute("for", val)
    return
  }
}
