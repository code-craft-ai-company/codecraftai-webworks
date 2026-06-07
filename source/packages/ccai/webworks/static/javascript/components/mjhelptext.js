/*
 * mjhelptext.js
 *
 * <mj-help-text> -- supplementary guidance for a form control. Links to the
 * control via aria-describedby; entirely passive (no events emitted). Removes
 * its id from aria-describedby when hidden so it is not announced when invisible.
 */

import { MjElement, nextId } from "../core/mjelement.js";

const STYLES = `
:host {
  display: block;
}

:host([hidden]) {
  display: none;
}

.container {
  display: flex;
  align-items: flex-start;
  gap: var(--mj-help-text-gap, var(--mj-space-1));
  font-size: var(--mj-help-text-font-size, var(--mj-font-size-xs));
  color: var(--mj-help-text-color, var(--mj-text-muted));
  margin-top: var(--mj-help-text-margin-top, var(--mj-space-1));
  line-height: var(--mj-line-height);
}

:host([disabled]) .container {
  color: var(--mj-help-text-disabled-color, var(--mj-text-muted));
  opacity: 0.55;
}

.icon-wrap {
  display: inline-flex;
  flex-shrink: 0;
}
`;

export class MjHelpText extends MjElement {
  static tagName = "mj-help-text";
  static styles = STYLES;
  static watched = ["for", "hidden", "disabled", "display"];

  constructor() {
    super()
    this._controlRef = null
    this._observer = null

    if (!this.id) {
      this.id = nextId("mj-help")
    }
  }

  render() {
    const markup = `
      <p class="container" part="container">
        <span class="icon-wrap" part="icon">
          <slot name="icon"></slot>
        </span>
        <slot></slot>
      </p>
    `
    return markup
  }

  afterRender() {
    this._syncDisplay()
    this._associate()
    return
  }

  onConnected() {
    this._associate()
    return
  }

  onDisconnected() {
    this._removeDescribedBy()
    if (this._observer !== null) {
      this._observer.disconnect()
      this._observer = null
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "for") {
      this._removeDescribedBy()
      this._controlRef = null
      this._associate()
    }
    if (name === "hidden") {
      if (newValue !== null) {
        this._removeDescribedBy()
      } else {
        this._associate()
      }
    }
    if (name === "display") {
      this._syncDisplay()
    }
    return
  }

  _syncDisplay() {
    const container = this.$(".container")
    if (container === null) {
      return
    }
    const displayVal = this.getAttribute("display") || "block"
    if (displayVal === "inline") {
      container.style.display = "inline-flex"
    } else {
      container.style.display = "flex"
    }
    return
  }

  _associate() {
    if (this.hasAttribute("hidden")) {
      return
    }
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
    this._addDescribedBy(target)
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
    this._controlRef = null
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
        this._addDescribedBy(target)
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
}
