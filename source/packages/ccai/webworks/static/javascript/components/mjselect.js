/*
 * mjselect.js
 *
 * <mj-select> — single-choice dropdown with rich option content, keyboard
 * navigation, and full form participation via ElementInternals.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { autoPosition } from "../core/overlay.js";
import { announce } from "../core/announcer.js";

const STYLES = `
:host {
  display: inline-block;
  position: relative;
  vertical-align: middle;
}
:host([block]) { display: block; }

.trigger {
  display: inline-flex;
  align-items: center;
  gap: var(--mj-space-2);
  min-height: var(--mj-control-height-md);
  min-width: var(--mj-target-min);
  width: 100%;
  padding: 0 var(--mj-space-3);
  font: inherit;
  font-size: var(--mj-font-size-md);
  color: var(--mj-text);
  background: var(--mj-surface);
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-select-border-radius, var(--mj-radius-md));
  cursor: pointer;
  user-select: none;
  transition: border-color var(--mj-motion-fast) var(--mj-motion-ease);
  text-align: start;
}
.trigger:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.trigger:hover:not([disabled]) { border-color: var(--mj-accent); }

:host([size="sm"]) .trigger { min-height: var(--mj-control-height-sm); font-size: var(--mj-font-size-sm); }
:host([size="lg"]) .trigger { min-height: var(--mj-control-height-lg); font-size: var(--mj-font-size-lg); }

.label { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.placeholder { color: var(--mj-text-muted); }
.chevron {
  width: 1em; height: 1em; flex-shrink: 0;
  transition: transform var(--mj-motion-fast) var(--mj-motion-ease);
}
:host([open]) .chevron { transform: rotate(180deg); }

:host([disabled]) .trigger { opacity: 0.55; cursor: not-allowed; }
:host([invalid]) .trigger { border-color: var(--mj-color-danger); }
:host([readonly]) .trigger { cursor: default; }

.popup {
  position: fixed;
  background: var(--mj-surface-raised, var(--mj-surface));
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-select-border-radius, var(--mj-radius-md));
  box-shadow: var(--mj-elevation-2);
  min-width: var(--mj-select-popup-min-width, 0);
  max-height: var(--mj-select-popup-max-height, 18rem);
  overflow-y: auto;
  z-index: var(--mj-layer-popover);
  display: none;
}
:host([open]) .popup { display: block; }

.listbox { padding: var(--mj-space-1) 0; }

.option {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  padding: var(--mj-select-option-padding, var(--mj-space-2) var(--mj-space-3));
  cursor: pointer;
  user-select: none;
  font-size: var(--mj-font-size-md);
  color: var(--mj-text);
}
.option:hover { background: var(--mj-bg-muted); }
.option[aria-selected="true"] { background: var(--mj-bg-subtle); font-weight: var(--mj-font-weight-medium); }
.option[aria-disabled="true"] { opacity: 0.45; cursor: not-allowed; }
.option.focused { background: var(--mj-bg-muted); outline: none; }

.optgroup-label {
  padding: var(--mj-space-1) var(--mj-space-3);
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text-muted);
  font-weight: var(--mj-font-weight-medium);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.no-results {
  padding: var(--mj-space-3);
  color: var(--mj-text-muted);
  text-align: center;
  font-size: var(--mj-font-size-sm);
}
.check { width: 1em; height: 1em; flex-shrink: 0; opacity: 0; }
.option[aria-selected="true"] .check { opacity: 1; }
`;

export class MjSelect extends FormControlMixin(MjElement) {
  static tagName = "mj-select";
  static styles = STYLES;
  static watched = ["value", "open", "disabled", "readonly", "invalid", "placeholder", "size"];

  constructor() {
    super()
    this._initFormControl()
    this._focusedIndex = -1
    this._typeahead = ""
    this._typeaheadTimer = null
    this._disposePosition = null
    this._listboxId = nextId("mj-select-lb")
    this._triggerId = nextId("mj-select-tr")
  }

  render() {
    const markup = `
      <button
        class="trigger"
        part="trigger"
        id="${this._triggerId}"
        role="combobox"
        aria-haspopup="listbox"
        aria-expanded="false"
        aria-controls="${this._listboxId}"
        type="button"
      >
        <span class="label" part="selected-label"></span>
        <svg class="chevron" part="chevron" aria-hidden="true" viewBox="0 0 16 16" fill="currentColor">
          <path d="M8 10.5 3 5.5h10z"/>
        </svg>
      </button>
      <div class="popup" part="popup">
        <div
          class="listbox"
          part="listbox"
          id="${this._listboxId}"
          role="listbox"
          tabindex="-1"
        ></div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._trigger = this.$(".trigger")
    this._popup = this.$(".popup")
    this._listbox = this.$(".listbox")

    this.listen(this._trigger, "click", this._onTriggerClick.bind(this))
    this.listen(this._trigger, "keydown", this._onKeydown.bind(this))
    this.listen(document, "click", this._onDocClick.bind(this))

    this._buildOptions()
    this._syncTriggerLabel()

    const slotEl = this.shadowRoot.querySelector("slot")
    if (slotEl !== null) {
      this.listen(slotEl, "slotchange", () => {
        this._buildOptions()
        this._syncTriggerLabel()
      })
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "value") {
      this._setFormValue(newValue || "")
      this._syncTriggerLabel()
      this._updateOptionSelected()
    }
    if (name === "open") {
      this._syncOpen()
    }
    if (name === "disabled" || name === "readonly") {
      this._syncAccessibility()
    }
    return
  }

  /* ----- option building ----- */

  _getOptionEls() {
    const els = Array.from(this.querySelectorAll("mj-option"))
    return els
  }

  _buildOptions() {
    const optionEls = this._getOptionEls()
    if (optionEls.length === 0) {
      this._listbox.innerHTML = `<div class="no-results" part="no-results"><slot name="no-results">No options</slot></div>`
      return
    }

    const items = []
    optionEls.forEach((opt, idx) => {
      const value = opt.getAttribute("value") || ""
      const label = opt.textContent.trim()
      const disabled = opt.hasAttribute("disabled")
      const id = nextId("mj-opt")
      opt._mjId = id
      items.push({ id, value, label, disabled, index: idx })
    })

    this._optionData = items
    let html = ""
    items.forEach((item) => {
      const disabledAttr = item.disabled === true ? ' aria-disabled="true"' : ""
      const selectedAttr = item.value === this._value ? ' aria-selected="true"' : ' aria-selected="false"'
      html += `<div
        class="option"
        part="option"
        role="option"
        id="${item.id}"
        data-value="${item.value}"
        data-index="${item.index}"
        ${selectedAttr}${disabledAttr}
      >
        <svg class="check" aria-hidden="true" viewBox="0 0 16 16" fill="currentColor"><path d="M13.5 3.5 6 11 2.5 7.5l1-1L6 9 12.5 2.5z"/></svg>
        <span class="option-label" part="option-label">${item.label}</span>
      </div>`
    })
    this._listbox.innerHTML = html

    const optionNodes = this._listbox.querySelectorAll(".option")
    optionNodes.forEach((node) => {
      this.listen(node, "click", this._onOptionClick.bind(this))
      this.listen(node, "mouseover", this._onOptionHover.bind(this))
    })
    return
  }

  _syncTriggerLabel() {
    if (this._trigger === undefined) {
      return
    }
    const labelEl = this._trigger.querySelector(".label")
    if (labelEl === null) {
      return
    }
    const val = this._value || ""
    const data = this._optionData || []
    const match = data.find((d) => d.value === val)
    if (match !== undefined) {
      labelEl.textContent = match.label
      labelEl.classList.remove("placeholder")
    } else {
      const ph = this.getAttribute("placeholder") || ""
      labelEl.textContent = ph
      labelEl.classList.add("placeholder")
    }
    return
  }

  _updateOptionSelected() {
    if (this._listbox === undefined) {
      return
    }
    const opts = this._listbox.querySelectorAll(".option")
    opts.forEach((opt) => {
      const selected = opt.dataset.value === this._value
      opt.setAttribute("aria-selected", selected === true ? "true" : "false")
    })
    return
  }

  /* ----- open/close ----- */

  _syncOpen() {
    const isOpen = this.hasAttribute("open")
    this._trigger.setAttribute("aria-expanded", isOpen === true ? "true" : "false")

    if (isOpen === true) {
      this._popup.style.minWidth = `${this._trigger.offsetWidth}px`
      this._disposePosition = autoPosition(this._popup, this._trigger, {
        placement: "bottom-start"
      })
      this._focusedIndex = this._currentOptionIndex()
      this._moveFocus(this._focusedIndex >= 0 ? this._focusedIndex : 0)
    } else {
      if (this._disposePosition !== null) {
        this._disposePosition()
        this._disposePosition = null
      }
      this._clearFocus()
    }
    return
  }

  _open() {
    if (this.hasAttribute("disabled") || this.hasAttribute("readonly")) {
      return
    }
    const proceed = this.emit("mj-open", {}, { cancelable: true })
    if (proceed === false) {
      return
    }
    this.setAttribute("open", "")
    return
  }

  _close() {
    if (this.hasAttribute("open") === false) {
      return
    }
    this.removeAttribute("open")
    this.emit("mj-close", {})
    this._trigger.focus()
    return
  }

  _currentOptionIndex() {
    const data = this._optionData || []
    const idx = data.findIndex((d) => d.value === this._value && d.disabled !== true)
    return idx
  }

  _moveFocus(index) {
    const opts = this._listbox.querySelectorAll(".option")
    opts.forEach((el) => el.classList.remove("focused"))
    if (index < 0 || index >= opts.length) {
      return
    }
    this._focusedIndex = index
    const focused = opts[index]
    focused.classList.add("focused")
    focused.scrollIntoView({ block: "nearest" })
    this._trigger.setAttribute("aria-activedescendant", focused.id)
    return
  }

  _clearFocus() {
    const opts = this._listbox.querySelectorAll(".option")
    opts.forEach((el) => el.classList.remove("focused"))
    this._trigger.removeAttribute("aria-activedescendant")
    this._focusedIndex = -1
    return
  }

  /* ----- event handlers ----- */

  _onTriggerClick() {
    if (this.hasAttribute("open")) {
      this._close()
    } else {
      this._open()
    }
    return
  }

  _onOptionClick(event) {
    const node = event.currentTarget
    if (node.getAttribute("aria-disabled") === "true") {
      return
    }
    this._selectValue(node.dataset.value)
    return
  }

  _onOptionHover(event) {
    const node = event.currentTarget
    const index = parseInt(node.dataset.index, 10)
    this._moveFocus(index)
    return
  }

  _onDocClick(event) {
    if (this.hasAttribute("open") === false) {
      return
    }
    const inside = event.composedPath().includes(this)
    if (inside === false) {
      this._close()
    }
    return
  }

  _onKeydown(event) {
    const isOpen = this.hasAttribute("open")
    const data = this._optionData || []
    const enabled = data.filter((d) => d.disabled !== true)

    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      if (isOpen === false) {
        this._open()
      } else {
        const focused = this._listbox.querySelector(".option.focused")
        if (focused !== null && focused.getAttribute("aria-disabled") !== "true") {
          this._selectValue(focused.dataset.value)
        }
      }
    } else if (event.key === "Escape") {
      event.preventDefault()
      this._close()
    } else if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault()
      if (isOpen === false) {
        this._open()
        return
      }
      const delta = event.key === "ArrowDown" ? 1 : -1
      const allOpts = Array.from(this._listbox.querySelectorAll(".option"))
      const current = this._focusedIndex >= 0 ? this._focusedIndex : -1
      let next = current + delta
      while (next >= 0 && next < allOpts.length) {
        if (allOpts[next].getAttribute("aria-disabled") !== "true") {
          break
        }
        next = next + delta
      }
      if (next >= 0 && next < allOpts.length) {
        this._moveFocus(next)
      }
    } else if (event.key === "Home") {
      event.preventDefault()
      if (isOpen === true) {
        this._moveFocus(0)
      }
    } else if (event.key === "End") {
      event.preventDefault()
      if (isOpen === true) {
        const allOpts = this._listbox.querySelectorAll(".option")
        this._moveFocus(allOpts.length - 1)
      }
    } else if (event.key === "Tab") {
      if (isOpen === true) {
        this._close()
      }
    } else if (event.key.length === 1) {
      if (isOpen === true) {
        this._typeaheadMatch(event.key)
      }
    }
    return
  }

  _typeaheadMatch(char) {
    clearTimeout(this._typeaheadTimer)
    this._typeahead = this._typeahead + char.toLowerCase()
    this._typeaheadTimer = setTimeout(() => {
      this._typeahead = ""
    }, 500)

    const allOpts = Array.from(this._listbox.querySelectorAll(".option"))
    const match = allOpts.find((el) => {
      const label = el.querySelector(".option-label")
      const text = label !== null ? label.textContent.toLowerCase() : ""
      return text.startsWith(this._typeahead) && el.getAttribute("aria-disabled") !== "true"
    })
    if (match !== null && match !== undefined) {
      const index = parseInt(match.dataset.index, 10)
      this._moveFocus(index)
    }
    return
  }

  _selectValue(newValue) {
    const previousValue = this._value
    this._setFormValue(newValue)
    this.setAttribute("value", newValue)
    this._syncTriggerLabel()
    this._updateOptionSelected()
    this.emit("mj-change", { value: newValue, previousValue: previousValue })
    this._close()
    return
  }

  /* ----- accessibility ----- */

  _syncAccessibility() {
    if (this._trigger === undefined) {
      return
    }
    const disabled = this.hasAttribute("disabled")
    this._trigger.disabled = disabled
    const readonly = this.hasAttribute("readonly")
    if (readonly === true) {
      this._trigger.setAttribute("aria-readonly", "true")
    } else {
      this._trigger.removeAttribute("aria-readonly")
    }
    const invalid = this.hasAttribute("invalid")
    if (invalid === true) {
      this._trigger.setAttribute("aria-invalid", "true")
    } else {
      this._trigger.removeAttribute("aria-invalid")
    }
    return
  }

  _validationAnchor() {
    return this._trigger || this
  }

  /* ----- scriptable API ----- */

  get open() {
    return this.hasAttribute("open")
  }

  set open(value) {
    if (value === true) {
      this._open()
    } else {
      this._close()
    }
    return
  }

  get disabled() {
    return this.hasAttribute("disabled")
  }

  set disabled(value) {
    this.reflectBoolean("disabled", value === true)
    return
  }

  focus() {
    if (this._trigger !== undefined) {
      this._trigger.focus()
    }
    return
  }
}
