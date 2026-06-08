/*
 * mjcheckboxgroup.js
 *
 * <mj-checkbox-group> — labeled group of independent boolean choices with
 * optional tri-state "select all" parent checkbox and form participation.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { announce } from "../core/announcer.js";

const STYLES = `
:host { display: block; }

.group {
  display: flex;
  flex-direction: column;
  gap: var(--mj-checkbox-group-gap, var(--mj-space-2));
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

.checkbox-item {
  display: flex;
  align-items: center;
  gap: var(--mj-checkbox-label-gap, var(--mj-space-2));
  cursor: pointer;
  min-height: var(--mj-target-min);
}
.checkbox-item[aria-disabled="true"] { opacity: 0.45; cursor: not-allowed; }

.checkbox-control {
  flex-shrink: 0;
  width: var(--mj-checkbox-size, 1rem);
  height: var(--mj-checkbox-size, 1rem);
  border: 2px solid var(--mj-checkbox-border-color, var(--mj-border-strong));
  border-radius: var(--mj-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--mj-surface);
  transition: background var(--mj-motion-fast), border-color var(--mj-motion-fast);
  outline: none;
}
.checkbox-item:focus-within .checkbox-control {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.checkbox-item[aria-checked="true"] .checkbox-control {
  background: var(--mj-checkbox-color, var(--mj-accent));
  border-color: var(--mj-checkbox-color, var(--mj-accent));
}
.checkbox-item[aria-checked="mixed"] .checkbox-control {
  background: var(--mj-checkbox-indeterminate-color, var(--mj-accent));
  border-color: var(--mj-checkbox-indeterminate-color, var(--mj-accent));
}

.check-icon, .mixed-icon {
  width: 0.75em; height: 0.75em;
  color: white;
  display: none;
}
.checkbox-item[aria-checked="true"] .check-icon { display: block; }
.checkbox-item[aria-checked="mixed"] .mixed-icon { display: block; }

.checkbox-text { display: flex; flex-direction: column; gap: 2px; flex: 1; }
.checkbox-label { color: var(--mj-text); }
.checkbox-description { font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }

.select-all-wrapper {
  padding-bottom: var(--mj-space-2);
  border-bottom: 1px solid var(--mj-border);
  margin-bottom: var(--mj-space-1);
}
:host(:not([select-all])) .select-all-wrapper { display: none; }

:host([disabled]) .checkbox-item { opacity: 0.45; cursor: not-allowed; pointer-events: none; }
:host([invalid]) .group { outline: 2px solid var(--mj-color-danger); border-radius: var(--mj-radius-md); padding: var(--mj-space-1); }
`;

function checkboxItemHtml(id, label, checked, disabled, isMixed) {
  const checkedState = isMixed === true ? "mixed" : (checked === true ? "true" : "false")
  const disabledAttr = disabled === true ? ' aria-disabled="true"' : ""
  return `<div
    class="checkbox-item"
    part="checkbox"
    role="checkbox"
    id="${id}"
    aria-checked="${checkedState}"
    tabindex="${disabled === true ? "-1" : "0"}"
    data-value="${label}"
    ${disabledAttr}
  >
    <span class="checkbox-control" part="checkbox-input" aria-hidden="true">
      <svg class="check-icon" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
        <path d="M13.5 3.5 6 11 2.5 7.5l1-1L6 9 12.5 2.5z"/>
      </svg>
      <svg class="mixed-icon" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
        <path d="M3 8h10v1.5H3z"/>
      </svg>
    </span>
    <span class="checkbox-text">
      <span class="checkbox-label" part="checkbox-label">${label}</span>
    </span>
  </div>`
}

export class MjCheckboxGroup extends FormControlMixin(MjElement) {
  static tagName = "mj-checkbox-group";
  static styles = STYLES;
  static watched = ["value", "disabled", "readonly", "invalid", "select-all", "select-all-label", "orientation"];

  constructor() {
    super()
    this._initFormControl()
    this._checkedValues = new Set()
    this._checkboxData = []
    this._groupId = nextId("mj-cg")
    this._labelId = nextId("mj-cg-label")
    this._errorId = nextId("mj-cg-err")
  }

  render() {
    const label = this.getAttribute("label") || ""
    const labelAttr = label.length > 0 ? `aria-label="${label}"` : `aria-labelledby="${this._labelId}"`
    const markup = `
      <div
        class="group"
        part="group"
        role="group"
        ${labelAttr}
        aria-describedby="${this._errorId}"
      >
        <span class="group-label" part="group-label" id="${this._labelId}"><slot name="label"></slot></span>
        <div class="select-all-wrapper" part="select-all">
          ${checkboxItemHtml(nextId("mj-sa"), this.getAttribute("select-all-label") || "Select all", false, false, false)}
        </div>
        <div class="checkbox-items" part="checkboxes"></div>
        <span class="help" part="help"><slot name="help"></slot></span>
        <span class="error" part="error" id="${this._errorId}" role="alert"><slot name="error"></slot></span>
      </div>
    `
    return markup
  }

  afterRender() {
    this._group = this.$(".group")
    this._itemsEl = this.$(".checkbox-items")
    this._selectAllEl = this.$(".select-all-wrapper .checkbox-item")

    const slot = this.shadowRoot.querySelector("slot:not([name])")
    if (slot !== null) {
      this.listen(slot, "slotchange", () => this._buildCheckboxes())
    }

    if (this._selectAllEl !== null) {
      this.listen(this._selectAllEl, "click", this._onSelectAllClick.bind(this))
      this.listen(this._selectAllEl, "keydown", this._onCheckboxKeydown.bind(this, null))
    }

    this._buildCheckboxes()
    this._initValues()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "value") {
      this._initValues()
    }
    if (name === "invalid") {
      this._syncAccessibility()
    }
    return
  }

  _getMjCheckboxes() {
    return Array.from(this.querySelectorAll("mj-checkbox"))
  }

  _buildCheckboxes() {
    const els = this._getMjCheckboxes()
    this._checkboxData = els.map((el, idx) => ({
      id: nextId("mj-cb"),
      value: el.getAttribute("value") || "",
      label: el.textContent.trim(),
      disabled: el.hasAttribute("disabled"),
      index: idx,
      el: el
    }))
    this._renderCheckboxes()
    return
  }

  _initValues() {
    const attrVal = this.getAttribute("value") || ""
    this._checkedValues.clear()
    if (attrVal.length > 0) {
      attrVal.split(",").forEach((v) => {
        const t = v.trim()
        if (t.length > 0) {
          this._checkedValues.add(t)
        }
      })
    }
    this._syncFormValue()
    if (this._itemsEl !== undefined) {
      this._renderCheckboxes()
    }
    return
  }

  _renderCheckboxes() {
    let html = ""
    this._checkboxData.forEach((item) => {
      const checked = this._checkedValues.has(item.value)
      html += checkboxItemHtml(item.id, item.label, checked, item.disabled, false)
    })
    this._itemsEl.innerHTML = html

    const items = this._itemsEl.querySelectorAll(".checkbox-item")
    items.forEach((item) => {
      this.listen(item, "click", this._onCheckboxClick.bind(this))
      this.listen(item, "keydown", this._onCheckboxKeydown.bind(this, item))
    })

    this._updateSelectAll()
    return
  }

  _updateSelectAll() {
    if (this._selectAllEl === null) {
      return
    }
    const state = this.selectAllState
    if (state === "all") {
      this._selectAllEl.setAttribute("aria-checked", "true")
    } else if (state === "some") {
      this._selectAllEl.setAttribute("aria-checked", "mixed")
    } else {
      this._selectAllEl.setAttribute("aria-checked", "false")
    }
    return
  }

  get selectAllState() {
    const enabled = this._checkboxData.filter((d) => d.disabled !== true)
    if (enabled.length === 0) {
      return "none"
    }
    const checkedCount = enabled.filter((d) => this._checkedValues.has(d.value)).length
    if (checkedCount === 0) {
      return "none"
    }
    if (checkedCount === enabled.length) {
      return "all"
    }
    return "some"
  }

  get checkedValues() {
    return Array.from(this._checkedValues)
  }

  _onCheckboxClick(event) {
    const item = event.currentTarget
    if (item.getAttribute("aria-disabled") === "true" || this.hasAttribute("readonly")) {
      return
    }
    this._toggleCheckbox(item)
    return
  }

  _onCheckboxKeydown(item, event) {
    if (event.key === " " || event.key === "Enter") {
      event.preventDefault()
      const el = item || event.currentTarget
      if (el.getAttribute("aria-disabled") !== "true" && this.hasAttribute("readonly") === false) {
        if (el.classList.contains("checkbox-item")) {
          this._toggleCheckbox(el)
        }
      }
    }
    return
  }

  _toggleCheckbox(el) {
    const value = el.dataset.value
    const data = this._checkboxData.find((d) => d.label === value || d.value === value)
    if (data === undefined) {
      return
    }

    const wasChecked = this._checkedValues.has(data.value)
    if (wasChecked === true) {
      this._checkedValues.delete(data.value)
    } else {
      this._checkedValues.add(data.value)
    }

    el.setAttribute("aria-checked", wasChecked === true ? "false" : "true")
    this._syncFormValue()
    this._updateSelectAll()

    this.emit("mj-change", {
      checkedValues: this.checkedValues,
      changedCheckbox: data.el,
      checked: !wasChecked
    })
    return
  }

  _onSelectAllClick() {
    if (this.hasAttribute("readonly") || this.hasAttribute("disabled")) {
      return
    }
    const state = this.selectAllState
    const checkAll = state !== "all"

    this._checkboxData.forEach((item) => {
      if (item.disabled !== true) {
        if (checkAll === true) {
          this._checkedValues.add(item.value)
        } else {
          this._checkedValues.delete(item.value)
        }
      }
    })

    this._syncFormValue()
    this._renderCheckboxes()

    this.emit("mj-select-all", { checked: checkAll })
    this.emit("mj-change", { checkedValues: this.checkedValues, changedCheckbox: null, checked: checkAll })
    return
  }

  _syncFormValue() {
    const vals = Array.from(this._checkedValues)
    this._setFormValue(vals.join(","))
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
    if (required === true && this._checkedValues.size === 0) {
      return "At least one option must be selected."
    }
    return ""
  }

  _validationAnchor() {
    const first = this._itemsEl !== undefined ? this._itemsEl.querySelector(".checkbox-item") : null
    return first || this
  }

  onFormReset() {
    this._initValues()
    return
  }

  get checkboxes() {
    return this._getMjCheckboxes()
  }

  focus() {
    const first = this._itemsEl !== undefined ? this._itemsEl.querySelector("[tabindex='0']") : null
    if (first !== null) {
      first.focus()
    }
    return
  }
}
