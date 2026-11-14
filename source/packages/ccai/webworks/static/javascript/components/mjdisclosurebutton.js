/*
 * mjdisclosurebutton.js
 *
 * <mj-disclosure-button> -- a button that shows or hides a related content region.
 *
 * Exposes `aria-expanded` and `aria-controls` so assistive technology understands
 * the relationship between the trigger and the controlled panel. Fires a cancelable
 * `mj-change` event before the state changes; once the change is committed it
 * fires the native-style `change` event and `mj-expanded`. A decorative chevron
 * (shown unless chevron="false") rotates 180° to indicate the state.
 *
 * The element named by `controls` (an id in the button's own tree, or a CSS
 * selector) is shown and hidden with the button: its `hidden` property follows
 * `expanded`. Set the `manual` attribute to keep the panel under the control of
 * the page or of a wrapper such as an accordion.
 */

import { MjElement } from "../core/mjelement.js";

const STYLES = `
:host {
  display: inline-block;
  vertical-align: middle;
}
:host([block]) { display: block; }

.btn {
  position: relative;
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

/* Icon-only: the label stays in the accessibility tree but is not shown. */
:host([icon-only]) .btn { padding: 0; aspect-ratio: 1; justify-content: center; }
:host([icon-only]) .label {
  position: absolute;
  width: 1px; height: 1px; margin: -1px; padding: 0; border: 0;
  overflow: hidden; clip: rect(0 0 0 0); clip-path: inset(50%); white-space: nowrap;
}

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
  static watched = [
    "expanded", "controls", "variant", "size", "disabled", "chevron", "icon-only", "label", "block", "manual"
  ];

  constructor() {
    super()
    this._button = null

    /* Pending retry for a panel that is parsed or inserted after the button. */
    this._panelRetryTimer = null

    /* True once the corresponding console warning was logged. */
    this._warnedMissingName = false
    this._warnedMissingPanel = false
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
    if (this._button === undefined || this._button === null) {
      return
    }

    this._syncAccessibility()
    if (name === "controls" || name === "expanded" || name === "manual") {
      this._wireControls()
    }
    return
  }

  onConnected() {
    this._wireControls()

    /*
     * The panel usually follows the button in the markup, so it does not
     * exist yet while the parser connects the button. Wire it once more when
     * the document has been parsed, or on the next task for script-built
     * trees.
     */
    if (this._resolvePanel() === null && this.getAttribute("controls") !== null) {
      if (document.readyState === "loading") {
        this.listen(document, "DOMContentLoaded", this._wireControls.bind(this))
      }
      this._panelRetryTimer = window.setTimeout(() => {
        this._panelRetryTimer = null
        this._wireControls()
      }, 0)
      this.onTeardown(() => {
        if (this._panelRetryTimer !== null) {
          window.clearTimeout(this._panelRetryTimer)
          this._panelRetryTimer = null
        }
      })
    }
    return
  }

  /* `expanded="false"` (for example from a server template) is collapsed. */
  _isExpanded() {
    const value = this.getAttribute("expanded")
    const expanded = value !== null && value !== "false"
    return expanded
  }

  /*
   * Find the controlled panel. `controls` is an id looked up in the tree the
   * button lives in (the document or an enclosing shadow root); when no
   * element has that id it is tried as a CSS selector. Resolved on every
   * call so a panel added later is found.
   */
  _resolvePanel() {
    let panel = null

    const controls = this.getAttribute("controls")
    if (controls !== null && controls.length > 0) {
      const root = this.getRootNode()

      if (typeof root.getElementById === "function") {
        panel = root.getElementById(controls)
      }

      if (panel === null && typeof root.querySelector === "function") {
        try {
          panel = root.querySelector(controls)
        } catch (error) {
          /* Not a valid selector (for example an id such as "1panel"). */
          panel = null
        }
      }
    }

    return panel
  }

  /*
   * Expose the button/panel relationship and keep the panel's visibility in
   * step with `expanded`.
   */
  _wireControls() {
    if (this._button === undefined || this._button === null) {
      return
    }

    const panel = this._resolvePanel()

    /*
     * The button is in this component's shadow root and the panel is outside
     * it, so an aria-controls id could never resolve. The element itself is
     * assigned instead.
     */
    if ("ariaControlsElements" in this._button) {
      this._button.ariaControlsElements = panel !== null ? [panel] : null
    }

    if (panel !== null && this.hasAttribute("manual") === false) {
      const hidden = this._isExpanded() === false
      if (panel.hidden !== hidden) {
        panel.hidden = hidden
      }
    }
    return
  }

  _syncAccessibility() {
    const disabled = this.hasAttribute("disabled")
    const expanded = this._isExpanded()
    const iconOnly = this.hasAttribute("icon-only")

    this._button.disabled = disabled
    this._button.setAttribute("aria-expanded", expanded === true ? "true" : "false")

    if (iconOnly === true) {
      const accessibleName = this.getAttribute("label") || this.getAttribute("aria-label")
      if (accessibleName !== null && accessibleName.length > 0) {
        this._button.setAttribute("aria-label", accessibleName)
      } else {
        /*
         * The slotted label text is visually hidden but still names the
         * button; only a button with neither is reported, once.
         */
        this._button.removeAttribute("aria-label")
        const slottedText = this.textContent !== null ? this.textContent.trim() : ""
        if (slottedText === "" && this._warnedMissingName === false) {
          this._warnedMissingName = true
          console.warn("<mj-disclosure-button>: icon-only is set but no label attribute is provided.")
        }
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

    /*
     * `mj-change` is the cancelable request. It is dispatched directly, not
     * through emit(), because emit() would fire the native-style `change`
     * right away -- before the state changes and even for a vetoed toggle.
     */
    const request = new CustomEvent("mj-change", {
      detail: { expanded: nextExpanded, originalEvent: event },
      bubbles: true,
      cancelable: true,
      composed: true
    })
    const proceed = this.dispatchEvent(request)
    if (proceed === false) {
      return
    }

    const controls = this.getAttribute("controls")
    const unresolved = controls !== null && controls.length > 0 && this._resolvePanel() === null
    if (unresolved === true && this._warnedMissingPanel === false) {
      this._warnedMissingPanel = true
      console.warn("<mj-disclosure-button>: the `controls` attribute does not resolve to an element.", this)
    }

    this.expanded = nextExpanded
    this.dispatchEvent(new Event("change", { bubbles: true, composed: true }))
    this.emit("mj-expanded", { expanded: nextExpanded })
    return
  }

  /* ----- scriptable API ----- */

  get expanded() {
    const value = this._isExpanded()
    return value
  }

  set expanded(value) {
    this.reflectBoolean("expanded", Boolean(value))
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

  /* The controlled panel element, or null when `controls` does not resolve. */
  get panelEl() {
    const found = this._resolvePanel()
    return found
  }

  get disabled() {
    const value = this.hasAttribute("disabled")
    return value
  }

  set disabled(value) {
    this.reflectBoolean("disabled", Boolean(value))
    return
  }

  /*
   * Toggles the disclosure as a user click would (mj-change, change, mj-
   * expanded). HTMLElement.click() would only dispatch a click at the host,
   * which never reaches the inner button. Disabled / busy states are
   * honoured by the inner handler.
   */
  click() {
    if (this._button !== undefined && this._button !== null) {
      this._button.click()
    }
    return
  }

  focus(options) {
    if (this._button !== undefined && this._button !== null) {
      this._button.focus(options)
    }
    return
  }
}
