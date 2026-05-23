/*
 * mjradiogroup.js
 *
 * <mj-radio-group> — mutually exclusive radio group with roving tabindex,
 * ARIA radiogroup semantics, and form participation.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { RovingTabindex } from "../core/focustrap.js";

const STYLES = `
:host { display: block; }

.group {
  display: flex;
  flex-direction: column;
  gap: var(--mj-radio-group-gap, var(--mj-space-2));
}
:host([orientation="horizontal"]) .group { flex-direction: row; flex-wrap: wrap; }

.group-label {
  font-weight: var(--mj-font-weight-medium);
  margin-bottom: var(--mj-space-1);
  color: var(--mj-text);
}

.help, .error {
  font-size: var(--mj-font-size-sm);
  margin-top: var(--mj-space-1);
}
.help { color: var(--mj-text-muted); }
.error { color: var(--mj-color-danger); }
:host(:not([invalid])) .error { display: none; }

.radio-item {
  display: flex;
  align-items: flex-start;
  gap: var(--mj-radio-label-gap, var(--mj-space-2));
  cursor: pointer;
  min-height: var(--mj-target-min);
  align-items: center;
}
.radio-item[aria-disabled="true"] { opacity: 0.45; cursor: not-allowed; }

.radio-control {
  flex-shrink: 0;
  width: var(--mj-radio-size, 1rem);
  height: var(--mj-radio-size, 1rem);
  border-radius: 50%;
  border: 2px solid var(--mj-radio-border-color, var(--mj-border-strong));
  display: flex;
  align-items: center;
  justify-content: center;
  transition: border-color var(--mj-motion-fast);
  outline: none;
}
.radio-item[aria-checked="true"] .radio-control {
  border-color: var(--mj-radio-color, var(--mj-accent));
  background: var(--mj-radio-color, var(--mj-accent));
}
.radio-control:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.radio-dot {
  width: 40%;
  height: 40%;
  border-radius: 50%;
  background: white;
  opacity: 0;
  transition: opacity var(--mj-motion-fast);
}
.radio-item[aria-checked="true"] .radio-dot { opacity: 1; }

.radio-text { display: flex; flex-direction: column; gap: 2px; }
.radio-label { color: var(--mj-text); }
.radio-description { font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }

/* Button variant */
:host([variant="button"]) .radio-item {
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-md);
  padding: var(--mj-space-2) var(--mj-space-3);
  min-height: var(--mj-control-height-md);
  gap: var(--mj-space-2);
}
:host([variant="button"]) .radio-item[aria-checked="true"] {
  border-color: var(--mj-accent);
  background: var(--mj-bg-subtle);
}
:host([variant="button"]) .radio-control { display: none; }

:host([disabled]) .radio-item { opacity: 0.45; cursor: not-allowed; pointer-events: none; }
:host([invalid]) .group { outline: 2px solid var(--mj-color-danger); border-radius: var(--mj-radius-md); padding: var(--mj-space-1); }
`;

export class MjRadioGroup extends FormControlMixin(MjElement) {
  static tagName = "mj-radio-group";
  static styles = STYLES;
  static watched = ["value", "disabled", "readonly", "invalid", "orientation", "variant"];

  constructor() {
    super()
    this._initFormControl()
    this._radioData = []
    this._roving = null
    this._groupId = nextId("mj-rg")
    this._labelId = nextId("mj-rg-label")
    this._errorId = nextId("mj-rg-err")
  }

  render() {
    const label = this.getAttribute("label") || ""
    const labelAttr = label.length > 0 ? `aria-label="${label}"` : `aria-labelledby="${this._labelId}"`
    const markup = `
      <div
        class="group"
        part="group"
        role="radiogroup"
        ${labelAttr}
        aria-describedby="${this._errorId}"
      >
        <span class="group-label" part="group-label" id="${this._labelId}"><slot name="label"></slot></span>
        <div class="radio-items" part="radios"></div>
        <span class="help" part="help"><slot name="help"></slot></span>
        <span class="error" part="error" id="${this._errorId}" role="alert"><slot name="error"></slot></span>
      </div>
    `
    return markup
  }

  afterRender() {
    this._group = this.$(".group")
    this._itemsEl = this.$(".radio-items")

    const slot = this.shadowRoot.querySelector("slot:not([name])")
    if (slot !== null) {
      this.listen(slot, "slotchange", () => this._buildRadios())
    }

    this._buildRadios()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "value") {
      this._setFormValue(newValue || "")
      this._updateChecked()
    }
    if (name === "disabled" || name === "invalid") {
      this._syncAccessibility()
    }
    return
  }

  _getMjRadios() {
    return Array.from(this.querySelectorAll("mj-radio"))
  }

  _buildRadios() {
    const radios = this._getMjRadios()
    if (radios.length === 0) {
      this._itemsEl.innerHTML = ""
      return
    }

    this._radioData = radios.map((el, idx) => ({
      id: nextId("mj-radio"),
      value: el.getAttribute("value") || "",
      label: el.textContent.trim(),
      disabled: el.hasAttribute("disabled"),
      index: idx,
      el: el
    }))

    const currentValue = this._value || ""
    let html = ""
    this._radioData.forEach((item) => {
      const checked = item.value === currentValue
      const disabledAttr = item.disabled === true ? ' aria-disabled="true"' : ""
      const tabindex = (checked === true || (currentValue.length === 0 && item.index === 0)) ? "0" : "-1"
      html += `<div
        class="radio-item"
        part="radio"
        role="radio"
        id="${item.id}"
        aria-checked="${checked === true ? "true" : "false"}"
        aria-labelledby="${item.id}-label"
        tabindex="${tabindex}"
        data-value="${item.value}"
        data-index="${item.index}"
        ${disabledAttr}
      >
        <span class="radio-control" part="radio-input" aria-hidden="true">
          <span class="radio-dot"></span>
        </span>
        <span class="radio-text">
          <span class="radio-label" part="radio-label" id="${item.id}-label">${item.label}</span>
        </span>
      </div>`
    })
    this._itemsEl.innerHTML = html

    const items = this._itemsEl.querySelectorAll(".radio-item")
    items.forEach((item) => {
      this.listen(item, "click", this._onRadioClick.bind(this))
      this.listen(item, "keydown", this._onKeydown.bind(this))
    })

    this._setupRoving()
    return
  }

  _setupRoving() {
    if (this._roving !== null) {
      this._roving._disposeHandler && this._roving._disposeHandler()
    }

    const items = Array.from(this._itemsEl.querySelectorAll(".radio-item:not([aria-disabled='true'])"))
    const orientation = this.getAttribute("orientation") === "horizontal" ? "horizontal" : "vertical"

    this._roving = new RovingTabindex({
      items: items,
      orientation: orientation,
      wrap: true
    })

    const currentValue = this._value || ""
    const checkedIdx = this._radioData.findIndex((d) => d.value === currentValue && d.disabled !== true)
    const startIdx = checkedIdx >= 0 ? checkedIdx : 0
    this._roving.index = startIdx

    const disposeKey = this._roving.attach(this._itemsEl)
    this._roving._disposeHandler = disposeKey
    return
  }

  _updateChecked() {
    if (this._itemsEl === undefined) {
      return
    }
    const val = this._value || ""
    const items = this._itemsEl.querySelectorAll(".radio-item")
    items.forEach((item) => {
      const checked = item.dataset.value === val
      item.setAttribute("aria-checked", checked === true ? "true" : "false")
    })

    const enabledItems = Array.from(this._itemsEl.querySelectorAll(".radio-item:not([aria-disabled='true'])"))
    enabledItems.forEach((item, idx) => {
      const checked = item.dataset.value === val
      item.tabIndex = checked === true ? 0 : -1
      if (checked === true && this._roving !== null) {
        this._roving.index = idx
      }
    })
    return
  }

  _onRadioClick(event) {
    const item = event.currentTarget
    if (item.getAttribute("aria-disabled") === "true") {
      return
    }
    if (this.hasAttribute("readonly")) {
      return
    }
    this._selectValue(item.dataset.value)
    return
  }

  _onKeydown(event) {
    if (event.key === " ") {
      event.preventDefault()
      const item = event.currentTarget
      if (item.getAttribute("aria-disabled") !== "true" && this.hasAttribute("readonly") === false) {
        this._selectValue(item.dataset.value)
      }
    }
    return
  }

  _selectValue(newValue) {
    const previousValue = this._value
    this._setFormValue(newValue)
    this.setAttribute("value", newValue)
    this._updateChecked()

    const radio = this._radioData.find((d) => d.value === newValue)
    this.emit("mj-change", {
      value: newValue,
      previousValue: previousValue,
      radio: radio !== undefined ? radio.el : null
    })
    return
  }

  _syncAccessibility() {
    if (this._group === undefined) {
      return
    }
    const invalid = this.hasAttribute("invalid")
    if (invalid === true) {
      this._group.setAttribute("aria-invalid", "true")
    } else {
      this._group.removeAttribute("aria-invalid")
    }
    return
  }

  _customValidity() {
    const required = this.hasAttribute("required")
    if (required === true && (this._value === undefined || this._value === "")) {
      return "A selection is required."
    }
    return ""
  }

  _validationAnchor() {
    const firstRadio = this._itemsEl !== undefined ? this._itemsEl.querySelector(".radio-item") : null
    return firstRadio || this
  }

  onFormReset() {
    const initial = this.getAttribute("value") || ""
    this._setFormValue(initial)
    this._updateChecked()
    return
  }

  get radios() {
    return this._getMjRadios()
  }

  get selectedRadio() {
    const val = this._value
    const data = this._radioData.find((d) => d.value === val)
    return data !== undefined ? data.el : null
  }

  focus() {
    const first = this._itemsEl !== undefined ? this._itemsEl.querySelector("[tabindex='0']") : null
    if (first !== null) {
      first.focus()
    }
    return
  }
}
