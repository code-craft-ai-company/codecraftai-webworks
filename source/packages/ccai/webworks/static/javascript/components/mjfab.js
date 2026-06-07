/*
 * mjfab.js
 *
 * <mj-fab> -- Floating Action Button component.
 *
 * Provides a prominent, fixed-position button for the single most important
 * action on a screen. Supports standard (icon-only) and extended (icon + label)
 * modes, four viewport-corner positions, and an optional speed-dial that reveals
 * sub-action buttons.
 */

import { MjElement } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";

const STYLES = `
:host {
  position: fixed;
  display: block;
  z-index: var(--mj-fab-z-index, var(--mj-layer-overlay));
}
:host([position="bottom-end"])   { inset-block-end: var(--mj-fab-offset-y, 1rem); inset-inline-end: var(--mj-fab-offset-x, 1rem); }
:host([position="bottom-start"]) { inset-block-end: var(--mj-fab-offset-y, 1rem); inset-inline-start: var(--mj-fab-offset-x, 1rem); }
:host([position="top-end"])      { inset-block-start: var(--mj-fab-offset-y, 1rem); inset-inline-end: var(--mj-fab-offset-x, 1rem); }
:host([position="top-start"])    { inset-block-start: var(--mj-fab-offset-y, 1rem); inset-inline-start: var(--mj-fab-offset-x, 1rem); }

.fab {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--mj-space-2);
  width: var(--mj-fab-size, 3.5rem);
  height: var(--mj-fab-size, 3.5rem);
  min-width: var(--mj-target-min);
  min-height: var(--mj-target-min);
  padding: 0;
  font: inherit;
  font-weight: var(--mj-font-weight-medium);
  color: var(--mj-fab-color, var(--mj-text-on-accent));
  background: var(--mj-fab-bg, var(--mj-accent));
  border: none;
  border-radius: var(--mj-fab-border-radius, var(--mj-radius-circle));
  box-shadow: var(--mj-fab-elevation, var(--mj-elevation-3));
  cursor: pointer;
  user-select: none;
  transition: background var(--mj-motion-fast) var(--mj-motion-ease),
              box-shadow var(--mj-motion-fast) var(--mj-motion-ease);
}
.fab:hover { background: var(--mj-accent-hover); box-shadow: var(--mj-elevation-3); }
.fab:active { background: var(--mj-accent-active); box-shadow: var(--mj-elevation-2); }
.fab:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-fab-focus-ring-color, var(--mj-focus-ring));
  outline-offset: var(--mj-focus-ring-offset);
}

:host([size="sm"]) .fab { width: 2.5rem; height: 2.5rem; }
:host([size="lg"]) .fab { width: 4rem; height: 4rem; }
:host([size="extended"]) .fab {
  width: auto;
  height: var(--mj-control-height-lg);
  padding: 0 var(--mj-space-5);
  border-radius: var(--mj-radius-pill);
}

:host(:not([size="extended"])) .label { display: none; }

:host([disabled]) .fab,
:host([loading]) .fab { opacity: 0.55; cursor: not-allowed; }
:host([loading]) .fab { cursor: progress; }

.spinner {
  width: 1.25em; height: 1.25em;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: var(--mj-radius-circle);
  animation: mj-fab-spin var(--mj-motion-slow) linear infinite;
}
:host(:not([loading])) .spinner { display: none; }
@keyframes mj-fab-spin { to { transform: rotate(360deg); } }

.speed-dial-list {
  list-style: none;
  margin: 0;
  padding: var(--mj-space-2) 0;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--mj-fab-speed-dial-gap, var(--mj-space-3));
  position: absolute;
  inset-block-end: calc(100% + var(--mj-space-3));
  inset-inline-end: 0;
}
:host(:not([expanded])) .speed-dial-list,
:host([expanded="false"]) .speed-dial-list { display: none; }

@media (prefers-reduced-motion: reduce) {
  .fab { transition: none; }
}
`;

export class MjFab extends MjElement {
  static tagName = "mj-fab";
  static styles = STYLES;
  static watched = ["size", "label", "position", "loading", "speed-dial", "expanded", "offset-x", "offset-y"];

  constructor() {
    super()
    this._button = null
    this._speedDialList = null
  }

  render() {
    const markup = `
      <button class="fab" part="button" type="button">
        <span class="spinner" part="spinner" aria-hidden="true"></span>
        <span class="icon" part="icon"><slot name="icon"></slot></span>
        <span class="label" part="label"><slot></slot></span>
      </button>
      <ul class="speed-dial-list" part="speed-dial-list" role="menu" aria-hidden="true">
        <slot name="speed-dial-item"></slot>
      </ul>
    `
    return markup
  }

  afterRender() {
    this._button = this.$(".fab")
    this._speedDialList = this.$(".speed-dial-list")
    this.listen(this._button, "click", this._onClick.bind(this))
    this.listen(document, "keydown", this._onKeydown.bind(this))
    this.listen(document, "click", this._onDocClick.bind(this))
    this._syncAccessibility()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._button !== null) {
      this._syncAccessibility()
    }
    return
  }

  _syncAccessibility() {
    const disabled = this.hasAttribute("disabled")
    const loading = this.hasAttribute("loading")
    const inert = disabled === true || loading === true
    const isSpeedDial = this.hasAttribute("speed-dial")
    const expanded = this.hasAttribute("expanded")
    const label = this.getAttribute("label") || ""

    this._button.disabled = inert
    this._button.setAttribute("aria-busy", loading === true ? "true" : "false")

    if (label.length > 0) {
      this._button.setAttribute("aria-label", label)
    }

    if (isSpeedDial === true) {
      this._button.setAttribute("aria-haspopup", "menu")
      this._button.setAttribute("aria-expanded", expanded === true ? "true" : "false")
    } else {
      this._button.removeAttribute("aria-haspopup")
      this._button.removeAttribute("aria-expanded")
    }

    if (this._speedDialList !== null) {
      this._speedDialList.setAttribute("aria-hidden", expanded === true ? "false" : "true")
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

    const isSpeedDial = this.hasAttribute("speed-dial")
    if (isSpeedDial === true) {
      this.expanded = !this.expanded
      return
    }

    this.emit("mj-click", { originalEvent: event })
    return
  }

  _onKeydown(event) {
    if (event.key === "Escape" && this.expanded === true) {
      this.expanded = false
      this._button.focus()
    }
    return
  }

  _onDocClick(event) {
    if (this.expanded === true && this.contains(event.target) === false) {
      this.expanded = false
    }
    return
  }

  /* ----- scriptable API ----- */

  get expanded() {
    const value = this.hasAttribute("expanded")
    return value
  }

  set expanded(value) {
    this.reflectBoolean("expanded", value === true)
    this.emit("mj-expanded", { expanded: value === true })
    return
  }

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

  focus() {
    this._button.focus()
    return
  }
}
