/*
 * mjbutton.js
 *
 * <mj-button> -- the primary action component and the REFERENCE pattern for
 * the whole mj-* library. Other components follow the structure used here:
 *   - extend MjElement (or a mixin of it),
 *   - declare `tagName`, `styles`, `watched`,
 *   - build shadow DOM in `render`, wire events in `afterRender`,
 *   - reflect state via attributes, expose scriptable properties,
 *   - emit namespaced `mj-*` events,
 *   - source every visual value from a design token (themeable),
 *   - expose ::part() hooks,
 *   - participate in docking/anchoring through MjElement.
 *
 * Catalog synonyms (primary/secondary/tertiary/link/icon/submit/reset/close/
 * back/next/previous/toolbar buttons) are all variants here, not separate
 * components.
 */

import { MjElement } from "../core/mjelement.js";

const STYLES = `
:host {
  display: inline-block;
  vertical-align: middle;
}
:host([block]) { display: block; }

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--mj-space-2);
  min-height: var(--mj-control-height-md);
  min-width: var(--mj-target-min);
  padding: 0 var(--mj-space-4);
  font: inherit;
  font-weight: var(--mj-font-weight-medium);
  line-height: 1;
  color: var(--mj-text);
  background: var(--mj-surface);
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-md);
  cursor: pointer;
  user-select: none;
  transition: background var(--mj-motion-fast) var(--mj-motion-ease),
              border-color var(--mj-motion-fast) var(--mj-motion-ease);
}
.btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

/* Variants */
:host([variant="primary"]) .btn {
  color: var(--mj-text-on-accent);
  background: var(--mj-accent);
  border-color: var(--mj-accent);
}
:host([variant="primary"]) .btn:hover { background: var(--mj-accent-hover); border-color: var(--mj-accent-hover); }
:host([variant="primary"]) .btn:active { background: var(--mj-accent-active); }

:host([variant="secondary"]) .btn:hover { background: var(--mj-bg-muted); }

:host([variant="tertiary"]) .btn,
:host([variant="link"]) .btn {
  background: transparent;
  border-color: transparent;
}
:host([variant="tertiary"]) .btn:hover { background: var(--mj-bg-muted); }
:host([variant="link"]) .btn {
  color: var(--mj-accent);
  text-decoration: underline;
  padding-inline: var(--mj-space-1);
  min-width: auto;
}

/* Sizes */
:host([size="sm"]) .btn { min-height: var(--mj-control-height-sm); padding: 0 var(--mj-space-3); font-size: var(--mj-font-size-sm); }
:host([size="lg"]) .btn { min-height: var(--mj-control-height-lg); padding: 0 var(--mj-space-5); font-size: var(--mj-font-size-lg); }

/* Icon-only */
:host([icon-only]) .btn { padding: 0; aspect-ratio: 1; }

/* States */
:host([disabled]) .btn,
:host([loading]) .btn { opacity: 0.55; cursor: not-allowed; }
:host([loading]) .btn { cursor: progress; }

.spinner {
  width: 1em; height: 1em;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: var(--mj-radius-circle);
  animation: mj-spin var(--mj-motion-slow) linear infinite;
}
:host(:not([loading])) .spinner { display: none; }
@keyframes mj-spin { to { transform: rotate(360deg); } }

::slotted([slot="icon"]) { display: inline-flex; }
`;

export class MjButton extends MjElement {
  static tagName = "mj-button";
  static styles = STYLES;
  static watched = ["variant", "size", "type", "loading", "icon-only", "block"];
  static formAssociated = true;

  constructor() {
    super()
    if (typeof this.attachInternals === "function") {
      this._internals = this.attachInternals()
    } else {
      this._internals = null
    }
  }

  render() {
    const markup = `
      <button class="btn" part="button" type="button">
        <span class="spinner" part="spinner" aria-hidden="true"></span>
        <slot name="icon"></slot>
        <span class="label" part="label"><slot></slot></span>
      </button>
    `
    return markup
  }

  afterRender() {
    this._button = this.$(".btn")
    this.listen(this._button, "click", this._onClick.bind(this))
    this._syncAccessibility()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._button !== undefined) {
      this._syncAccessibility()
    }
    return
  }

  /* Keep the inner control's ARIA/disabled state in sync with the host. */
  _syncAccessibility() {
    const disabled = this.hasAttribute("disabled")
    const loading = this.hasAttribute("loading")
    const inert = disabled === true || loading === true

    this._button.disabled = inert
    this._button.setAttribute("aria-busy", loading === true ? "true" : "false")

    const iconOnly = this.hasAttribute("icon-only")
    if (iconOnly === true) {
      const accessibleName = this.getAttribute("label") || this.getAttribute("aria-label")
      if (accessibleName !== null) {
        this._button.setAttribute("aria-label", accessibleName)
      }
    } else {
      this._button.removeAttribute("aria-label")
    }
    return
  }

  _onClick(event) {
    const blocked = this.hasAttribute("disabled") || this.hasAttribute("loading")
    if (blocked === true) {
      event.stopImmediatePropagation()
      event.preventDefault()
      return
    }

    const proceed = this.emit("mj-click", { source: this }, { cancelable: true })
    if (proceed === false) {
      return
    }

    const type = this.getAttribute("type") || "button"
    const form = this._internals !== null ? this._internals.form : null
    if (form !== null && form !== undefined) {
      if (type === "submit") {
        form.requestSubmit()
      } else if (type === "reset") {
        form.reset()
      }
    }
    return
  }

  /* ----- scriptable API ----- */

  get loading() {
    const value = this.hasAttribute("loading")
    return value
  }

  set loading(value) {
    this.reflectBoolean("loading", value === true)
    return
  }

  get disabled() {
    const value = this.hasAttribute("disabled")
    return value
  }

  set disabled(value) {
    this.reflectBoolean("disabled", value === true)
    return
  }

  /* Programmatically activate the button. */
  click() {
    this._button.click()
    return
  }

  focus() {
    this._button.focus()
    return
  }
}
