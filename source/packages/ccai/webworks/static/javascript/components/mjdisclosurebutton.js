/*
 * mjdisclosurebutton.js
 *
 * <mj-disclosure-button> -- a button that shows or hides a related content region.
 *
 * Exposes `aria-expanded` and `aria-controls` so assistive technology understands
 * the relationship between the trigger and the controlled panel. Fires a cancelable
 * `mj-change` event before the state changes; fires `mj-expanded` after. An optional
 * decorative chevron rotates 180° to indicate expanded/collapsed state.
 */

import { MjElement, nextId } from "../core/mjelement.js";

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
  min-height: var(--mj-disclosure-button-height, var(--mj-control-height-md));
  min-width: var(--mj-target-min);
  padding: 0 var(--mj-disclosure-button-padding-x, var(--mj-space-4));
  font: inherit;
  font-weight: var(--mj-font-weight-medium);
  line-height: 1;
  color: var(--mj-disclosure-button-color, var(--mj-text));
  background: var(--mj-disclosure-button-bg, transparent);
  border: 1px solid transparent;
  border-radius: var(--mj-disclosure-button-border-radius, var(--mj-radius-md));
  cursor: pointer;
  user-select: none;
  width: 100%;
  justify-content: space-between;
  transition: background var(--mj-motion-fast) var(--mj-motion-ease);
}
.btn:hover { background: var(--mj-bg-muted); }
.btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-disclosure-button-focus-ring-color, var(--mj-focus-ring));
  outline-offset: var(--mj-focus-ring-offset);
}
.btn[aria-expanded="true"] {
  color: var(--mj-disclosure-button-color-expanded, var(--mj-text));
  background: var(--mj-disclosure-button-bg-expanded, var(--mj-bg-muted));
}

/* Variants */
:host([variant="primary"]) .btn {
  color: var(--mj-text-on-accent);
  background: var(--mj-accent);
  border-color: var(--mj-accent);
  justify-content: center;
}
:host([variant="secondary"]) .btn {
  background: var(--mj-surface);
  border-color: var(--mj-border-strong);
  justify-content: center;
}

/* Sizes */
:host([size="sm"]) .btn { min-height: var(--mj-control-height-sm); padding: 0 var(--mj-space-3); font-size: var(--mj-font-size-sm); }
:host([size="lg"]) .btn { min-height: var(--mj-control-height-lg); padding: 0 var(--mj-space-5); font-size: var(--mj-font-size-lg); }

/* Icon-only */
:host([icon-only]) .btn { padding: 0; aspect-ratio: 1; justify-content: center; }

/* Disabled */
:host([disabled]) .btn { opacity: 0.55; cursor: not-allowed; }

/* Chevron */
.chevron {
  display: inline-flex;
  flex-shrink: 0;
  width: var(--mj-disclosure-button-chevron-size, 1em);
  height: var(--mj-disclosure-button-chevron-size, 1em);
  transition: transform var(--mj-disclosure-button-chevron-transition, var(--mj-motion-medium)) var(--mj-motion-ease);
}
:host(:not([chevron])) .chevron,
:host([chevron="false"]) .chevron { display: none; }
.btn[aria-expanded="true"] .chevron { transform: rotate(180deg); }

.left-group { display: inline-flex; align-items: center; gap: var(--mj-space-2); }

@media (prefers-reduced-motion: reduce) {
  .btn { transition: none; }
  .chevron { transition: none; }
}
`;

const CHEVRON_SVG = `<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><polyline points="4 6 8 10 12 6"/></svg>`;

export class MjDisclosureButton extends MjElement {
  static tagName = "mj-disclosure-button";
  static styles = STYLES;
  static watched = ["expanded", "controls", "variant", "size", "disabled", "chevron", "icon-only", "label", "block"];

  constructor() {
    super()
    this._button = null
  }

  render() {
    const markup = `
      <button class="btn" part="button" type="button" aria-expanded="false">
        <span class="left-group">
          <span class="icon" part="icon"><slot name="icon"></slot></span>
          <span class="label" part="label"><slot></slot></span>
        </span>
        <span class="chevron" part="chevron" aria-hidden="true">${CHEVRON_SVG}</span>
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
    if (this._button !== null) {
      this._syncAccessibility()
      if (name === "controls") {
        this._wireControls()
      }
    }
    return
  }

  onConnected() {
    this._wireControls()
    return
  }

  _wireControls() {
    if (this._button === null) {
      return
    }

    const controlsId = this.getAttribute("controls")
    if (controlsId === null || controlsId.length === 0) {
      this._button.removeAttribute("aria-controls")
      return
    }

    let panelEl = document.getElementById(controlsId)
    if (panelEl === null) {
      panelEl = document.querySelector(controlsId)
    }

    if (panelEl === null) {
      console.warn(`<mj-disclosure-button>: controls="${controlsId}" does not resolve to a document element.`)
      this._button.removeAttribute("aria-controls")
      return
    }

    if (panelEl.id === null || panelEl.id.length === 0) {
      const generatedId = nextId("mj-panel")
      panelEl.id = generatedId
      console.info(`<mj-disclosure-button>: assigned id "${generatedId}" to the controlled panel.`)
    }

    this._button.setAttribute("aria-controls", panelEl.id)
    return
  }

  _syncAccessibility() {
    const disabled = this.hasAttribute("disabled")
    const expanded = this.hasAttribute("expanded")
    const iconOnly = this.hasAttribute("icon-only")

    this._button.disabled = disabled
    this._button.setAttribute("aria-expanded", expanded === true ? "true" : "false")

    if (iconOnly === true) {
      const accessibleName = this.getAttribute("label") || this.getAttribute("aria-label")
      if (accessibleName !== null && accessibleName.length > 0) {
        this._button.setAttribute("aria-label", accessibleName)
      } else {
        console.warn("<mj-disclosure-button>: icon-only is set but no label attribute is provided.")
        this._button.setAttribute("aria-label", "")
      }
    } else {
      this._button.removeAttribute("aria-label")
    }
    return
  }

  _onClick(event) {
    const blocked = this.hasAttribute("disabled")
    if (blocked === true) {
      event.stopImmediatePropagation()
      event.preventDefault()
      return
    }

    const nextExpanded = !this.expanded
    const proceed = this.emit("mj-change", { expanded: nextExpanded, originalEvent: event }, { cancelable: true })
    if (proceed === false) {
      return
    }

    this.expanded = nextExpanded
    this.emit("mj-expanded", { expanded: nextExpanded })
    return
  }

  /* ----- scriptable API ----- */

  get expanded() {
    const value = this.hasAttribute("expanded")
    return value
  }

  set expanded(value) {
    this.reflectBoolean("expanded", value === true)
    return
  }

  get controls() {
    const value = this.getAttribute("controls")
    return value
  }

  set controls(value) {
    if (value === null || value === undefined) {
      this.removeAttribute("controls")
    } else {
      this.setAttribute("controls", value)
    }
    return
  }

  get panelEl() {
    const controlsId = this.getAttribute("controls")
    if (controlsId === null || controlsId.length === 0) {
      return null
    }
    const found = document.getElementById(controlsId)
    return found
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
