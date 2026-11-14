/*
 * mjerrormessage.js
 *
 * <mj-error-message> -- displays a field-level validation error linked to a
 * control via aria-describedby. Marks the control aria-invalid while visible.
 * Uses role="alert" for assertive announcement on first show; live-region
 * updates are debounced at 300ms to avoid spamming screen readers.
 *
 * With the opt-in `auto` attribute the element follows the constraint
 * validation state of its control: it shows the control's validation message
 * when the control reports invalid (a failed submit, or a blur while
 * invalid) and hides again as soon as the control is valid.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import {
  findById, waitForId, deferUntilDefined, ariaTargetOf, addAriaReference, removeAriaReference
} from "../core/aria.js";

const STYLES = `
:host {
  display: block;
}

:host(:not([visible]):not([always-render])) {
  display: none;
}

:host([always-render]:not([visible])) .container {
  visibility: hidden;
}

.container {
  display: flex;
  align-items: flex-start;
  gap: var(--mj-error-gap, var(--mj-space-1));
  font-size: var(--mj-error-font-size, var(--mj-font-size-xs));
  color: var(--mj-error-color, var(--mj-color-danger, #b91c1c));
  margin-block-start: var(--mj-error-margin-top, var(--mj-space-1));
  line-height: var(--mj-line-height);
}

.icon-wrap {
  display: inline-flex;
  flex-shrink: 0;
  font-size: var(--mj-error-icon-size, var(--mj-space-4));
}

.message:empty {
  display: none;
}
`;

const ANNOUNCE_DELAY_MS = 300;

export class MjErrorMessage extends MjElement {
  static tagName = "mj-error-message";
  static styles = STYLES;
  static watched = ["for", "visible", "always-render", "message", "auto"];

  constructor() {
    super()
    this._container = null
    this._messageEl = null
    this._slotEl = null

    this._controlRef = null
    this._stopWaiting = null
    this._announceTimer = null
    this._wasVisible = false

    /* True while this element is the one that set aria-invalid on the control. */
    this._setInvalidState = false
    this._previousInvalid = null

    /* The validation message shown in `auto` mode when there is no own text. */
    this._autoMessage = ""

    this._onControlInvalid = this._handleControlInvalid.bind(this)
    this._onControlChanged = this._handleControlChanged.bind(this)
    this._onControlBlur = this._handleControlBlur.bind(this)
    this._autoListeningTo = null
  }

  render() {
    const markup = `
      <span class="container" part="container" role="alert" aria-atomic="true">
        <span class="icon-wrap" part="icon">
          <slot name="icon"></slot>
        </span>
        <span class="message" part="message"></span>
        <slot></slot>
      </span>
    `
    return markup
  }

  afterRender() {
    this._container = this.$(".container")
    this._messageEl = this.$(".message")
    this._slotEl = this.$("slot:not([name])")
    this._renderMessage()
    this._syncHiddenState()
    return
  }

  onConnected() {
    /*
     * The id is assigned here, not in the constructor: a custom element
     * constructor must not add attributes (document.createElement fails).
     */
    if (this.id.length === 0) {
      this.id = nextId("mj-err")
    }
    this._associate()
    this._syncVisible()
    return
  }

  onDisconnected() {
    this._cancelAnnounce()
    this._dissociate()

    /* A later reconnect must re-apply the visible state to the control. */
    this._wasVisible = false
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._container === undefined || this._container === null || this.isConnected === false) {
      return
    }

    if (name === "for" || name === "auto") {
      this._dissociate()
      this._associate()
      this._applyControlState()
    }
    if (name === "visible" || name === "always-render") {
      this._syncVisible()
    }
    if (name === "message") {
      if (this.hasAttribute("visible") === true) {
        this._scheduleAnnounce()
      } else {
        this._renderMessage()
      }
    }
    return
  }

  /* ----- control association ----- */

  _associate() {
    if (this._controlRef !== null || this.id.length === 0) {
      return
    }

    const forValue = this.getAttribute("for") || ""
    if (forValue.length === 0) {
      return
    }

    const target = findById(this, forValue)
    if (target === null) {
      if (this._stopWaiting === null) {
        this._stopWaiting = waitForId(this, forValue, () => {
          this._stopWaiting = null
          this._associate()
          this._applyControlState()
        })
      }
      return
    }

    const pending = deferUntilDefined(target, () => {
      if (this.isConnected === true) {
        this._associate()
        this._applyControlState()
      }
    })
    if (pending === true) {
      return
    }

    this._controlRef = target
    this._attachAutoListeners()
    return
  }

  _dissociate() {
    if (this._stopWaiting !== null) {
      this._stopWaiting()
      this._stopWaiting = null
    }
    this._detachAutoListeners()
    this._clearControlState()
    this._controlRef = null
    return
  }

  /*
   * Mirror the visible state onto the control: while the error is shown the
   * control is described by it and marked invalid. Only the aria-invalid
   * this element set is ever removed, so state owned by the control or by
   * another error message survives.
   */
  _applyControlState() {
    const control = this._controlRef
    if (control === null) {
      return
    }

    if (this.hasAttribute("visible") === true) {
      addAriaReference(control, "describedby", this)

      const target = ariaTargetOf(control)
      if (this._setInvalidState === false && target.getAttribute("aria-invalid") !== "true") {
        this._previousInvalid = target.getAttribute("aria-invalid")
        target.setAttribute("aria-invalid", "true")
        this._setInvalidState = true
      }
    } else {
      this._clearControlState()
    }
    return
  }

  _clearControlState() {
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

  /* ----- auto mode ----- */

  _attachAutoListeners() {
    const control = this._controlRef
    if (control === null || this.hasAttribute("auto") === false || this._autoListeningTo !== null) {
      return
    }
    control.addEventListener("invalid", this._onControlInvalid)
    control.addEventListener("input", this._onControlChanged)
    control.addEventListener("change", this._onControlChanged)
    control.addEventListener("focusout", this._onControlBlur)
    this._autoListeningTo = control
    return
  }

  _detachAutoListeners() {
    const control = this._autoListeningTo
    if (control === null) {
      return
    }
    control.removeEventListener("invalid", this._onControlInvalid)
    control.removeEventListener("input", this._onControlChanged)
    control.removeEventListener("change", this._onControlChanged)
    control.removeEventListener("focusout", this._onControlBlur)
    this._autoListeningTo = null
    return
  }

  _controlIsValid() {
    const control = this._controlRef
    let valid = true
    if (control !== null && control.validity !== null && control.validity !== undefined) {
      valid = control.validity.valid === true
    }
    return valid
  }

  _handleControlInvalid() {
    this._showAuto()
    return
  }

  _handleControlChanged() {
    /* Typing only ever hides the error; it is shown again on blur or submit. */
    if (this._controlIsValid() === true) {
      this._hideAuto()
    }
    return
  }

  _handleControlBlur() {
    if (this._controlIsValid() === true) {
      this._hideAuto()
    } else {
      this._showAuto()
    }
    return
  }

  _showAuto() {
    const control = this._controlRef
    const message = control !== null && typeof control.validationMessage === "string" ? control.validationMessage : ""
    const changed = message !== this._autoMessage
    this._autoMessage = message

    if (this.hasAttribute("visible") === false) {
      this._renderMessage()
      this.setAttribute("visible", "")
    } else if (changed === true) {
      this._scheduleAnnounce()
    }
    return
  }

  _hideAuto() {
    if (this.hasAttribute("visible") === true) {
      this.removeAttribute("visible")
    }
    this._autoMessage = ""
    return
  }

  /*
   * Re-evaluate the control in `auto` mode: show when it is invalid and
   * `show` is true (a submit attempt), hide when it is valid. <mj-form>
   * calls this after validating and after a reset.
   */
  refresh(show) {
    if (this.hasAttribute("auto") === false || this._controlRef === null) {
      return
    }
    if (this._controlIsValid() === true) {
      this._hideAuto()
    } else if (show === true) {
      this._showAuto()
    }
    return
  }

  /* ----- visibility and text ----- */

  _syncHiddenState() {
    const visible = this.hasAttribute("visible")
    const alwaysRender = this.hasAttribute("always-render")

    if (alwaysRender === true && visible === false) {
      this._container.setAttribute("aria-hidden", "true")
    } else {
      this._container.removeAttribute("aria-hidden")
    }
    return
  }

  _syncVisible() {
    if (this._container === undefined || this._container === null) {
      return
    }

    const visible = this.hasAttribute("visible")
    this._syncHiddenState()

    if (visible === true && this._wasVisible === false) {
      this._wasVisible = true
      this._renderMessage()
      this._applyControlState()
      this.emit("mj-show", { message: this._getCurrentMessage() })
    } else if (visible === false && this._wasVisible === true) {
      this._wasVisible = false
      this._cancelAnnounce()
      this._clearControlState()
      this.emit("mj-hide", {})
    }
    return
  }

  /*
   * The text to show: the `message` attribute, else the element's own
   * content, else (in `auto` mode) the control's validation message.
   */
  _getCurrentMessage() {
    const msgAttr = this.getAttribute("message") || ""
    let message = msgAttr

    if (message.length === 0) {
      message = this.textContent.trim()
    }
    if (message.length === 0) {
      message = this._autoMessage
    }
    return message
  }

  /*
   * Write the scripted message into its own span next to the slot. The
   * default slot is only hidden while a scripted message replaces it, so
   * clearing `message` brings the slotted text back.
   */
  _renderMessage() {
    if (this._messageEl === undefined || this._messageEl === null) {
      return
    }

    const msgAttr = this.getAttribute("message") || ""
    const ownText = this.textContent.trim()

    let scripted = msgAttr
    if (scripted.length === 0 && ownText.length === 0) {
      scripted = this._autoMessage
    }

    this._messageEl.textContent = scripted
    this._slotEl.hidden = msgAttr.length > 0
    return
  }

  /* Debounce text updates while visible so the alert is not re-read per change. */
  _scheduleAnnounce() {
    this._cancelAnnounce()
    this._announceTimer = setTimeout(() => {
      this._announceTimer = null
      this._renderMessage()
    }, ANNOUNCE_DELAY_MS)
    return
  }

  _cancelAnnounce() {
    if (this._announceTimer !== null) {
      clearTimeout(this._announceTimer)
      this._announceTimer = null
    }
    return
  }

  /* ----- scriptable API ----- */

  get control() {
    return this._controlRef
  }

  get text() {
    return this._getCurrentMessage()
  }

  get visible() {
    return this.hasAttribute("visible")
  }

  set visible(val) {
    this.reflectBoolean("visible", Boolean(val) === true)
    return
  }
}
