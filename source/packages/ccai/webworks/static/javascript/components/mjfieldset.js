/*
 * mjfieldset.js
 *
 * <mj-fieldset> -- groups semantically related form controls under a common
 * legend. Maps directly to native <fieldset>/<legend> for group-role and
 * disabled propagation; adds collapsible, invalid, and theming support.
 */

import { MjElement, nextId } from "../core/mjelement.js";

const STYLES = `
:host {
  display: block;
}

.fieldset {
  border: 1px solid var(--mj-fieldset-border-color, var(--mj-border-strong));
  border-radius: var(--mj-fieldset-border-radius, var(--mj-radius-md));
  padding: var(--mj-space-3) var(--mj-space-4) var(--mj-space-4);
  margin: 0;
  min-width: 0;
}

:host([variant="borderless"]) .fieldset {
  border-color: transparent;
  padding-inline: 0;
}

:host([invalid]) .fieldset {
  border-color: var(--mj-fieldset-invalid-border-color, var(--mj-color-danger));
}

:host([disabled]) .fieldset {
  opacity: 0.55;
}

.legend {
  font-size: var(--mj-fieldset-legend-size, var(--mj-font-size-sm));
  color: var(--mj-fieldset-legend-color, var(--mj-text-muted));
  font-weight: var(--mj-font-weight-medium);
  padding: 0 var(--mj-space-1);
  display: flex;
  align-items: center;
  gap: var(--mj-space-1);
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.legend-btn {
  all: inherit;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: var(--mj-space-1);
  padding: 0;
  border: none;
  background: none;
}

.legend-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.indicator {
  color: var(--mj-color-danger, #b91c1c);
  aria-hidden: true;
}

.optional-badge {
  font-weight: var(--mj-font-weight-regular);
  color: var(--mj-text-muted);
}

.chevron {
  display: inline-block;
  width: 0.75em;
  height: 0.75em;
  flex-shrink: 0;
  transition: transform var(--mj-motion-fast) var(--mj-motion-ease);
}

:host([collapsible][open]) .chevron {
  transform: rotate(90deg);
}

.content-wrapper {
  display: grid;
  grid-template-rows: 1fr;
  overflow: hidden;
  transition: grid-template-rows var(--mj-motion-medium) var(--mj-motion-ease);
}

:host([collapsible]:not([open])) .content-wrapper {
  grid-template-rows: 0fr;
}

.content {
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: var(--mj-fieldset-gap, var(--mj-space-4));
  padding-top: var(--mj-space-3);
}

.footer {
  margin-top: var(--mj-space-2);
}
`;

export class MjFieldset extends MjElement {
  static tagName = "mj-fieldset";
  static styles = STYLES;
  static watched = ["legend", "disabled", "required", "optional", "invalid", "collapsible", "open", "variant", "name"];

  constructor() {
    super()
    this._contentId = nextId("mj-fieldset-content")
    this._fieldsetEl = null
    this._legendEl = null
    this._contentEl = null
  }

  render() {
    const markup = `
      <fieldset class="fieldset" part="fieldset">
        <legend class="legend" part="legend">
          <slot name="legend"></slot>
        </legend>
        <div class="content-wrapper">
          <div class="content" part="content" id="${this._contentId}">
            <slot></slot>
          </div>
        </div>
        <div class="footer" part="footer">
          <slot name="footer"></slot>
        </div>
      </fieldset>
    `
    return markup
  }

  afterRender() {
    this._fieldsetEl = this.$(".fieldset")
    this._legendEl = this.$(".legend")
    this._contentEl = this.$(".content")
    this._syncAll()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._fieldsetEl === null) {
      return
    }
    this._syncAll()
    return
  }

  _syncAll() {
    this._syncLegend()
    this._syncDisabled()
    this._syncCollapsible()
    return
  }

  _syncLegend() {
    const legendAttr = this.getAttribute("legend") || ""
    const required = this.hasAttribute("required")
    const optional = this.hasAttribute("optional") && required === false
    const collapsible = this.hasAttribute("collapsible")
    const open = this.hasAttribute("open") || !this.hasAttribute("collapsible")
    const reqLabel = this.getAttribute("required-label") || "*"
    const optLabel = this.getAttribute("optional-label") || "(optional)"

    let indicatorHtml = ""
    if (required === true) {
      indicatorHtml = `<span class="indicator" part="indicator" aria-hidden="true">${reqLabel}</span>`
    } else if (optional === true) {
      indicatorHtml = `<span class="optional-badge" part="indicator" aria-hidden="true">${optLabel}</span>`
    }

    if (legendAttr.length > 0) {
      if (collapsible === true) {
        this._legendEl.innerHTML = `
          <button class="legend-btn" aria-expanded="${open ? "true" : "false"}" aria-controls="${this._contentId}">
            <svg class="chevron" viewBox="0 0 10 10" aria-hidden="true" focusable="false">
              <path d="M3 2 L7 5 L3 8" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            ${legendAttr}${indicatorHtml}
          </button>
        `
        const btn = this._legendEl.querySelector(".legend-btn")
        this.listen(btn, "click", this._onLegendClick.bind(this))
      } else {
        this._legendEl.innerHTML = `${legendAttr}${indicatorHtml}`
      }
    }
    return
  }

  _syncDisabled() {
    const disabled = this.hasAttribute("disabled")
    if (disabled === true) {
      this._fieldsetEl.setAttribute("disabled", "")
    } else {
      this._fieldsetEl.removeAttribute("disabled")
    }
    return
  }

  _syncCollapsible() {
    const collapsible = this.hasAttribute("collapsible")
    if (collapsible === false) {
      return
    }
    const open = this.hasAttribute("open")
    const btn = this._legendEl !== null ? this._legendEl.querySelector(".legend-btn") : null
    if (btn !== null) {
      btn.setAttribute("aria-expanded", open ? "true" : "false")
    }
    return
  }

  _onLegendClick(event) {
    const currentlyOpen = this.hasAttribute("open")
    const nextOpen = !currentlyOpen

    const proceed = this.emit("mj-toggle", { open: nextOpen }, { cancelable: true })
    if (proceed === false) {
      return
    }

    this.reflectBoolean("open", nextOpen)
    return
  }

  /* ----- scriptable API ----- */

  get controls() {
    const all = this.querySelectorAll("input, select, textarea, [checkValidity]")
    return all
  }

  get disabled() {
    return this.hasAttribute("disabled")
  }

  set disabled(val) {
    this.reflectBoolean("disabled", val === true)
    return
  }

  get invalid() {
    return this.hasAttribute("invalid")
  }

  set invalid(val) {
    this.reflectBoolean("invalid", val === true)
    return
  }

  get open() {
    return this.hasAttribute("open")
  }

  set open(val) {
    this.reflectBoolean("open", val === true)
    return
  }
}
