/*
 * mjlabel.js
 *
 * <mj-label> -- renders a visible, accessible label associated with a form
 * control. Clicking the label moves focus to the control and the control is
 * named by the label; renders optional required or optional indicators;
 * exposes a suffix slot for inline help-icon triggers.
 *
 * This module re-exports the field-association helpers (findById,
 * ariaTargetOf, addAriaReference, removeAriaReference, deferUntilDefined,
 * waitForId) from core/aria.js, where they now live, so existing imports
 * from "./mjlabel.js" keep working.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { t } from "../core/intl.js";
import { findById, addAriaReference, removeAriaReference, deferUntilDefined, waitForId } from "../core/aria.js";

export {
  findById, ariaTargetOf, addAriaReference, removeAriaReference, deferUntilDefined, waitForId
} from "../core/aria.js";

/* ----- <mj-label> ----- */

const STYLES = `
:host {
  display: flex;
  align-items: baseline;
  gap: var(--mj-label-gap, var(--mj-space-1));
  margin-block-end: var(--mj-label-margin, var(--mj-space-1));
}

:host([layout="inline"]) {
  display: inline-flex;
  align-items: center;
  margin-block-end: 0;
  margin-inline-end: var(--mj-label-inline-gap, var(--mj-space-2));
  vertical-align: middle;
}

.label {
  display: inline-flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: var(--mj-label-gap, var(--mj-space-1));
  font-size: var(--mj-label-font-size, var(--mj-font-size-sm));
  font-weight: var(--mj-label-font-weight, var(--mj-font-weight-medium));
  color: var(--mj-label-color, var(--mj-text));
  cursor: default;
}

:host([layout="inline"]) .label {
  align-items: center;
}

:host([disabled]) .label {
  color: var(--mj-label-disabled-color, var(--mj-text-muted));
  opacity: 0.6;
}

:host([visually-hidden]) {
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

/* Native controls a label can be associated with. */
const LABELABLE_SELECTOR = "input:not([type='hidden']), select, textarea, button, meter, output, progress";

/* Input types whose label activation is a click, not only a focus move. */
const CLICK_ACTIVATED_TYPES = ["checkbox", "radio", "file", "color", "button", "submit", "reset", "image"];

/* Elements inside the label whose own click must not be redirected. */
const INTERACTIVE_SELECTOR = "a[href], button, input, select, textarea, summary, [tabindex], [contenteditable]";

export class MjLabel extends MjElement {
  static tagName = "mj-label";
  static styles = STYLES;
  static watched = ["for", "required", "optional", "disabled", "layout", "visually-hidden", "required-label", "optional-label"];

  constructor() {
    super()
    this._labelEl = null
    this._indicatorEl = null

    /* The control this label currently names, and how to stop waiting for it. */
    this._controlRef = null
    this._stopWaiting = null
  }

  render() {
    const markup = `
      <label class="label" part="label">
        <slot></slot>
        <span class="indicator" part="indicator" aria-hidden="true" hidden></span>
      </label>
      <span class="suffix" part="suffix">
        <slot name="suffix"></slot>
      </span>
    `
    return markup
  }

  afterRender() {
    this._labelEl = this.$(".label")
    this._indicatorEl = this.$(".indicator")
    this.listen(this._labelEl, "click", this._onClick.bind(this))
    this.listen(this.$("slot:not([name])"), "slotchange", this._onSlotChange.bind(this))
    this._syncIndicator()
    return
  }

  onConnected() {
    if (this.id.length === 0) {
      this.id = nextId("mj-label")
    }
    this._associate()
    return
  }

  onDisconnected() {
    this._dissociate()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._labelEl === undefined || this._labelEl === null) {
      return
    }
    if (name === "for") {
      this._dissociate()
      this._associate()
    }
    if (name === "required" || name === "optional" || name === "required-label" || name === "optional-label") {
      this._syncIndicator()
    }
    return
  }

  /*
   * Find the labelled control: the `for` target in this element's tree, or,
   * without `for`, the first control placed inside the label (implicit
   * association, as with a native <label>).
   */
  _resolveControl() {
    const forValue = this.getAttribute("for") || ""
    let control = null

    if (forValue.length > 0) {
      control = findById(this, forValue)
    } else {
      const candidates = this.querySelectorAll("*")
      for (let index = 0; index < candidates.length && control === null; index = index + 1) {
        const candidate = candidates[index]
        const isNative = candidate.matches(LABELABLE_SELECTOR)
        const isCustomControl = candidate.localName.indexOf("-") !== -1 &&
          (typeof candidate.checkValidity === "function" || candidate.constructor.formAssociated === true)
        if (isNative === true || isCustomControl === true) {
          control = candidate
        }
      }
    }

    return control
  }

  /* Name the control with this label. Runs on connect and when `for` changes. */
  _associate() {
    if (this.isConnected === false || this.id.length === 0) {
      return
    }

    const control = this._resolveControl()
    if (control !== null && control === this._controlRef) {
      return
    }
    this._dissociate()

    if (control === null) {
      const forValue = this.getAttribute("for") || ""
      if (forValue.length > 0) {
        this._stopWaiting = waitForId(this, forValue, () => {
          this._stopWaiting = null
          this._associate()
        })
      }
      return
    }

    const pending = deferUntilDefined(control, () => {
      if (this.isConnected === true) {
        this._associate()
      }
    })
    if (pending === true) {
      return
    }

    this._controlRef = control
    addAriaReference(control, "labelledby", this)
    return
  }

  _dissociate() {
    if (this._stopWaiting !== null) {
      this._stopWaiting()
      this._stopWaiting = null
    }
    if (this._controlRef !== null) {
      removeAriaReference(this._controlRef, "labelledby", this)
      this._controlRef = null
    }
    return
  }

  _onSlotChange() {
    /* A wrapped control may have been added or removed. */
    const forValue = this.getAttribute("for") || ""
    if (forValue.length === 0) {
      this._associate()
    }
    return
  }

  _syncIndicator() {
    const required = this.hasAttribute("required")
    const optional = this.hasAttribute("optional") && required === false

    if (required === true) {
      this._indicatorEl.className = "indicator"
      this._indicatorEl.textContent = this.getAttribute("required-label") || "*"
      this._indicatorEl.hidden = false
    } else if (optional === true) {
      this._indicatorEl.className = "indicator indicator--optional"
      this._indicatorEl.textContent = this.getAttribute("optional-label") || t("mj.label.optional")
      this._indicatorEl.hidden = false
    } else {
      this._indicatorEl.textContent = ""
      this._indicatorEl.hidden = true
    }
    return
  }

  /*
   * Label activation: move focus to the control, and click it when it is a
   * checkbox-like native control, exactly as a native <label> does. A click
   * on the control itself or on a link or button inside the label is left
   * alone.
   */
  _onClick(event) {
    const control = this._controlRef !== null ? this._controlRef : this._resolveControl()
    this.emit("mj-click", { control: control })

    if (control === null || this.hasAttribute("disabled") === true) {
      return
    }

    const path = event.composedPath()
    let redirect = true
    for (let index = 0; index < path.length && path[index] !== this._labelEl; index = index + 1) {
      const node = path[index]
      if (node === control) {
        redirect = false
      } else if (node instanceof Element && node.matches(INTERACTIVE_SELECTOR) === true) {
        redirect = false
      }
    }

    if (redirect === false || control.disabled === true) {
      return
    }

    if (typeof control.focus === "function") {
      control.focus()
    }

    const isNativeInput = control instanceof HTMLInputElement
    const clickActivated = isNativeInput === true && CLICK_ACTIVATED_TYPES.indexOf(control.type) !== -1
    if (clickActivated === true || control instanceof HTMLButtonElement) {
      control.click()
    }
    return
  }

  /* ----- scriptable API ----- */

  get control() {
    const found = this._controlRef !== null ? this._controlRef : this._resolveControl()
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
