/*
 * mjerrormessage.js
 *
 * <mj-error-message> -- displays a field-level validation error linked to a
 * control via aria-describedby. Sets aria-invalid on the control when visible.
 * Uses role="alert" for assertive announcement on first show; live-region
 * updates are debounced at 300ms to avoid spamming screen readers.
 */

import { MjElement, nextId } from "../core/mjelement.js";

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

:host([always-render]:not([visible])) .container {
  aria-hidden: true;
}

.container {
  display: flex;
  align-items: flex-start;
  gap: var(--mj-error-gap, var(--mj-space-1));
  font-size: var(--mj-error-font-size, var(--mj-font-size-xs));
  color: var(--mj-error-color, var(--mj-color-danger, #b91c1c));
  margin-top: var(--mj-error-margin-top, var(--mj-space-1));
  line-height: var(--mj-line-height);
}

.icon-wrap {
  display: inline-flex;
  flex-shrink: 0;
  font-size: var(--mj-error-icon-size, var(--mj-space-4));
}
`;

export class MjErrorMessage extends MjElement {
  static tagName = "mj-error-message";
  static styles = STYLES;
  static watched = ["for", "visible", "always-render", "message"];

  constructor() {
    super()
    this._controlRef = null
    this._observer = null
    this._announceTimer = null
    this._wasVisible = false

    if (!this.id) {
      this.id = nextId("mj-err")
    }
  }

  render() {
    const markup = `
      <span class="container" part="container" role="alert" aria-live="assertive" aria-atomic="true">
        <span class="icon-wrap" part="icon">
          <slot name="icon"></slot>
        </span>
        <slot></slot>
      </span>
    `
    return markup
  }

  afterRender() {
    this._container = this.$(".container")
    this._syncVisible()
    this._associate()
    return
  }

  onConnected() {
    this._associate()
    return
  }

  onDisconnected() {
    this._removeDescribedBy()
    this._clearInvalid()
    if (this._observer !== null) {
      this._observer.disconnect()
      this._observer = null
    }
    if (this._announceTimer !== null) {
      clearTimeout(this._announceTimer)
      this._announceTimer = null
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "for") {
      this._removeDescribedBy()
      this._clearInvalid()
      this._controlRef = null
      this._associate()
    }
    if (name === "visible") {
      this._syncVisible()
    }
    if (name === "message") {
      if (this.hasAttribute("visible")) {
        this._scheduleAnnounce()
      }
    }
    return
  }

  _associate() {
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
    if (this.hasAttribute("visible")) {
      this._addDescribedBy(target)
      this._setInvalid(target)
    }
    return
  }

  _syncVisible() {
    const visible = this.hasAttribute("visible")
    const alwaysRender = this.hasAttribute("always-render")

    if (this._container !== null && this._container !== undefined) {
      if (alwaysRender === true) {
        if (visible === true) {
          this._container.style.visibility = ""
          this._container.removeAttribute("aria-hidden")
        } else {
          this._container.style.visibility = "hidden"
          this._container.setAttribute("aria-hidden", "true")
        }
      }
    }

    if (visible === true && this._wasVisible === false) {
      if (this._controlRef !== null) {
        this._addDescribedBy(this._controlRef)
        this._setInvalid(this._controlRef)
      }
      this._scheduleAnnounce()
      this.emit("mj-show", { message: this._getCurrentMessage() })
    } else if (visible === false && this._wasVisible === true) {
      this._removeDescribedBy()
      this._clearInvalid()
      this._cancelAnnounce()
      this.emit("mj-hide", {})
    }

    this._wasVisible = visible
    return
  }

  _getCurrentMessage() {
    const msgAttr = this.getAttribute("message") || ""
    if (msgAttr.length > 0) {
      return msgAttr
    }
    return this.textContent.trim()
  }

  _scheduleAnnounce() {
    if (this._announceTimer !== null) {
      clearTimeout(this._announceTimer)
    }
    this._announceTimer = setTimeout(() => {
      this._announceTimer = null
      if (this._container !== null) {
        const msg = this.getAttribute("message") || ""
        if (msg.length > 0) {
          this._container.textContent = msg
        }
      }
    }, 300)
    return
  }

  _cancelAnnounce() {
    if (this._announceTimer !== null) {
      clearTimeout(this._announceTimer)
      this._announceTimer = null
    }
    return
  }

  _addDescribedBy(target) {
    const current = target.getAttribute("aria-describedby") || ""
    const parts = current.split(" ").filter((s) => s.length > 0)
    if (parts.indexOf(this.id) === -1) {
      parts.push(this.id)
      target.setAttribute("aria-describedby", parts.join(" "))
    }
    return
  }

  _removeDescribedBy() {
    if (this._controlRef === null) {
      return
    }
    const current = this._controlRef.getAttribute("aria-describedby") || ""
    const parts = current.split(" ").filter((s) => s.length > 0 && s !== this.id)
    if (parts.length > 0) {
      this._controlRef.setAttribute("aria-describedby", parts.join(" "))
    } else {
      this._controlRef.removeAttribute("aria-describedby")
    }
    return
  }

  _setInvalid(target) {
    target.setAttribute("aria-invalid", "true")
    return
  }

  _clearInvalid() {
    if (this._controlRef === null) {
      return
    }
    this._controlRef.removeAttribute("aria-invalid")
    return
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
        if (this.hasAttribute("visible")) {
          this._addDescribedBy(target)
          this._setInvalid(target)
        }
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
    this.reflectBoolean("visible", val === true)
    return
  }
}
