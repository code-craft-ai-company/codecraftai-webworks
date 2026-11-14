/*
 * mjfieldset.js
 *
 * <mj-fieldset> -- groups semantically related form controls under a common
 * legend. Renders a native <fieldset>/<legend> for the group role, and adds
 * disabled propagation to the slotted controls, collapsible, invalid, and
 * theming support.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";
import { listFormControls, DisabledPropagation } from "../core/formcontrols.js";

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

/* The base rule blocks pointer events on a disabled host; keep the legend usable. */
:host([disabled]) {
  pointer-events: auto;
  cursor: auto;
}

.legend {
  font-size: var(--mj-fieldset-legend-size, var(--mj-font-size-sm));
  color: var(--mj-fieldset-legend-color, var(--mj-text-muted));
  font-weight: var(--mj-font-weight-medium);
  padding: 0 var(--mj-space-1);
  max-width: 100%;
}

.legend-content {
  display: inline-flex;
  align-items: center;
  gap: var(--mj-space-1);
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.legend-text:empty {
  display: none;
}

.legend-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--mj-space-1);
  max-width: 100%;
  margin: 0;
  padding: 0;
  border: none;
  background: none;
  color: inherit;
  font: inherit;
  cursor: pointer;
}

.legend-btn[hidden] {
  display: none;
}

.legend-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.indicator {
  color: var(--mj-color-danger, #b91c1c);
}

.indicator[hidden] {
  display: none;
}

.indicator--optional {
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
  padding-block-start: var(--mj-space-3);
  visibility: visible;
  transition: visibility 0s linear 0s;
}

/*
 * Collapsed content is taken out of the accessibility tree and the tab
 * order (it is also inert, see _syncCollapsible); visibility flips only
 * after the collapse transition has finished.
 */
:host([collapsible]:not([open])) .content {
  visibility: hidden;
  transition: visibility 0s linear var(--mj-motion-medium);
}

.footer {
  margin-block-start: var(--mj-space-2);
}

:host([collapsible]:not([open])) .footer {
  display: none;
}
`;

export class MjFieldset extends MjElement {
  static tagName = "mj-fieldset";
  static styles = STYLES;
  static watched = [
    "legend", "disabled", "required", "optional", "invalid", "collapsible", "open", "variant", "name",
    "required-label", "optional-label"
  ];

  constructor() {
    super()
    this._contentId = nextId("mj-fieldset-content")

    /* Shadow references; null until the first render. */
    this._fieldsetEl = null
    this._legendEl = null
    this._legendButton = null
    this._legendContent = null
    this._legendText = null
    this._indicatorEl = null
    this._contentEl = null

    this._disabledControls = new DisabledPropagation()
    this._controlObserver = null

    /* Custom element names inside the fieldset still waiting for their definition. */
    this._pendingDefinitions = new Set()
  }

  /*
   * The legend holds one content group (text, the legend slot and the
   * indicator) and one toggle button. Both exist for the lifetime of the
   * shadow DOM; `collapsible` only decides whether the content group sits
   * inside the button, so toggling never replaces the focused button.
   */
  render() {
    const markup = html`
      <fieldset class="fieldset" part="fieldset">
        <legend class="legend" part="legend">
          <button class="legend-btn" part="legend-button" type="button" aria-controls="${this._contentId}" hidden>
            <svg class="chevron" viewBox="0 0 10 10" aria-hidden="true" focusable="false">
              <path d="M3 2 L7 5 L3 8" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
          <span class="legend-content">
            <span class="legend-text"></span>
            <slot name="legend"></slot>
            <span class="indicator" part="indicator" aria-hidden="true" hidden></span>
          </span>
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
    this._legendButton = this.$(".legend-btn")
    this._legendContent = this.$(".legend-content")
    this._legendText = this.$(".legend-text")
    this._indicatorEl = this.$(".indicator")
    this._contentEl = this.$(".content")

    this.listen(this._legendButton, "click", this._onLegendClick.bind(this))
    this._syncAll()
    return
  }

  onConnected() {
    this._syncDisabled()
    return
  }

  onDisconnected() {
    this._stopObservingControls()
    this._disabledControls.release()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._fieldsetEl === undefined || this._fieldsetEl === null) {
      return
    }

    if (name === "disabled") {
      this._syncDisabled()
    } else if (name === "open" || name === "collapsible") {
      this._syncCollapsible()
    } else if (name === "name") {
      this._syncName()
    } else {
      this._syncLegend()
    }
    return
  }

  _syncAll() {
    this._syncLegend()
    this._syncName()
    this._syncCollapsible()
    return
  }

  /* Legend text and indicator are written as text, never parsed as markup. */
  _syncLegend() {
    const legendAttr = this.getAttribute("legend") || ""
    const required = this.hasAttribute("required")
    const optional = this.hasAttribute("optional") && required === false

    this._legendText.textContent = legendAttr

    if (required === true) {
      this._indicatorEl.className = "indicator"
      this._indicatorEl.textContent = this.getAttribute("required-label") || "*"
      this._indicatorEl.hidden = false
    } else if (optional === true) {
      this._indicatorEl.className = "indicator indicator--optional"
      this._indicatorEl.textContent = this.getAttribute("optional-label") || t("mj.fieldset.optional")
      this._indicatorEl.hidden = false
    } else {
      this._indicatorEl.textContent = ""
      this._indicatorEl.hidden = true
    }
    return
  }

  _syncName() {
    const name = this.getAttribute("name")
    if (name !== null) {
      this._fieldsetEl.setAttribute("name", name)
    } else {
      this._fieldsetEl.removeAttribute("name")
    }
    return
  }

  /*
   * A <fieldset disabled> in the shadow root does not reach slotted
   * controls: disabling follows DOM ancestry, and slotted nodes stay in the
   * light DOM. The controls inside the host are therefore disabled here,
   * and exactly those are re-enabled later. Controls added while disabled
   * are picked up by the observer.
   */
  _syncDisabled() {
    const disabled = this.hasAttribute("disabled")

    if (disabled === true) {
      this._fieldsetEl.setAttribute("disabled", "")
      this._fieldsetEl.setAttribute("aria-disabled", "true")
      this._applyDisabledToControls()
      this._observeControls()
    } else {
      this._fieldsetEl.removeAttribute("disabled")
      this._fieldsetEl.removeAttribute("aria-disabled")
      this._stopObservingControls()
      this._disabledControls.release()
    }
    return
  }

  /*
   * Disable the controls inside the fieldset. A custom element that is not
   * upgraded yet cannot be recognised as a control, so the fieldset applies
   * the state again once its definition is registered.
   */
  _applyDisabledToControls() {
    this._disabledControls.apply(listFormControls(this))

    const pending = this.querySelectorAll(":not(:defined)")
    for (let index = 0; index < pending.length; index = index + 1) {
      const localName = pending[index].localName
      if (localName.indexOf("-") !== -1 && this._pendingDefinitions.has(localName) === false) {
        this._pendingDefinitions.add(localName)
        customElements.whenDefined(localName).then(() => {
          this._pendingDefinitions.delete(localName)
          if (this.isConnected === true && this.hasAttribute("disabled") === true) {
            this._disabledControls.apply(listFormControls(this))
          }
        })
      }
    }
    return
  }

  _observeControls() {
    if (this._controlObserver !== null || this.isConnected === false) {
      return
    }
    this._controlObserver = new MutationObserver(() => {
      if (this.hasAttribute("disabled") === true) {
        this._applyDisabledToControls()
      }
    })
    this._controlObserver.observe(this, { childList: true, subtree: true })
    return
  }

  _stopObservingControls() {
    if (this._controlObserver !== null) {
      this._controlObserver.disconnect()
      this._controlObserver = null
    }
    return
  }

  /*
   * Place the legend content inside the toggle button when collapsible and
   * directly in the legend otherwise, and reflect the open state. Collapsed
   * content is inert so it cannot be focused or read.
   */
  _syncCollapsible() {
    const collapsible = this.hasAttribute("collapsible")
    const open = this.hasAttribute("open") === true || collapsible === false

    if (collapsible === true) {
      if (this._legendContent.parentNode !== this._legendButton) {
        this._legendButton.appendChild(this._legendContent)
      }
      this._legendButton.hidden = false
      this._legendButton.setAttribute("aria-expanded", open === true ? "true" : "false")
    } else {
      if (this._legendContent.parentNode !== this._legendEl) {
        this._legendEl.appendChild(this._legendContent)
      }
      this._legendButton.hidden = true
      this._legendButton.removeAttribute("aria-expanded")
    }

    this._contentEl.inert = open === false
    return
  }

  _onLegendClick(event) {
    const currentlyOpen = this.hasAttribute("open")
    const nextOpen = currentlyOpen === false

    const proceed = this.emit("mj-toggle", { open: nextOpen }, { cancelable: true })
    if (proceed === false) {
      return
    }

    this.reflectBoolean("open", nextOpen)
    return
  }

  /* ----- scriptable API ----- */

  /* The form controls inside the fieldset, native and mj-*. */
  get controls() {
    const found = listFormControls(this)
    return found
  }

  get disabled() {
    return this.hasAttribute("disabled")
  }

  set disabled(val) {
    this.reflectBoolean("disabled", Boolean(val) === true)
    return
  }

  get invalid() {
    return this.hasAttribute("invalid")
  }

  set invalid(val) {
    this.reflectBoolean("invalid", Boolean(val) === true)
    return
  }

  get open() {
    return this.hasAttribute("open")
  }

  set open(val) {
    this.reflectBoolean("open", Boolean(val) === true)
    return
  }
}
