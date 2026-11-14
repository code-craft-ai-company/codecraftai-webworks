/*
 * mjhelptext.js
 *
 * <mj-help-text> -- supplementary guidance for a form control. Describes the
 * control through aria-describedby; entirely passive (no events emitted).
 * Stops describing the control while hidden so it is not announced when
 * invisible.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { findById, waitForId, deferUntilDefined, addAriaReference, removeAriaReference } from "../core/aria.js";

const STYLES = `
:host {
  display: block;
}

:host([display="inline"]) {
  display: inline-block;
  vertical-align: baseline;
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
  margin: 0;
  margin-block-start: var(--mj-help-text-margin-top, var(--mj-space-1));
  line-height: var(--mj-line-height);
}

:host([display="inline"]) .container {
  display: inline-flex;
  margin-block-start: 0;
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

    /* The control currently described, and how to stop waiting for it. */
    this._controlRef = null
    this._stopWaiting = null
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

  onConnected() {
    /*
     * The id is assigned here, not in the constructor: a custom element
     * constructor must not add attributes (document.createElement fails).
     */
    if (this.id.length === 0) {
      this.id = nextId("mj-help")
    }
    this._associate()
    return
  }

  onDisconnected() {
    this._dissociate()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this.isConnected === false || this.id.length === 0) {
      return
    }
    if (name === "for" || name === "hidden") {
      this._dissociate()
      this._associate()
    }
    return
  }

  /*
   * Describe the `for` target with this element. Idempotent: called on
   * connect and whenever `for` or `hidden` changes.
   */
  _associate() {
    if (this.hasAttribute("hidden") === true || this._controlRef !== null) {
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
        })
      }
      return
    }

    const pending = deferUntilDefined(target, () => {
      if (this.isConnected === true) {
        this._associate()
      }
    })
    if (pending === true) {
      return
    }

    this._controlRef = target
    addAriaReference(target, "describedby", this)
    return
  }

  _dissociate() {
    if (this._stopWaiting !== null) {
      this._stopWaiting()
      this._stopWaiting = null
    }
    if (this._controlRef !== null) {
      removeAriaReference(this._controlRef, "describedby", this)
      this._controlRef = null
    }
    return
  }

  /* ----- scriptable API ----- */

  get control() {
    return this._controlRef
  }
}
