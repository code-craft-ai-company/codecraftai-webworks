/*
 * mjlistbox.js
 *
 * <mj-listbox> — permanently-visible scrollable list supporting single and
 * multiple selection with shift/ctrl-click, roving tabindex (single) or
 * aria-activedescendant (multi), and form participation.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { announce } from "../core/announcer.js";

const STYLES = `
:host {
  display: block;
}

.listbox {
  display: block;
  min-height: var(--mj-listbox-min-height, 8rem);
  max-height: var(--mj-listbox-max-height, 24rem);
  overflow-y: auto;
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-listbox-border-radius, var(--mj-radius-md));
  background: var(--mj-surface);
  outline: none;
}
.listbox:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.option {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  padding: var(--mj-listbox-option-padding, var(--mj-space-2) var(--mj-space-3));
  min-height: var(--mj-listbox-option-height, var(--mj-control-height-md));
  cursor: pointer;
  user-select: none;
  color: var(--mj-text);
  font-size: var(--mj-font-size-md);
}
.option:hover { background: var(--mj-bg-muted); }
.option[aria-selected="true"] { background: var(--mj-bg-subtle); }
.option[aria-disabled="true"] { opacity: 0.45; cursor: not-allowed; }
.option.focused { outline: 2px solid var(--mj-focus-ring); outline-offset: -2px; }

:host([size="sm"]) .option { min-height: var(--mj-control-height-sm); font-size: var(--mj-font-size-sm); padding: var(--mj-space-1) var(--mj-space-3); }
:host([size="lg"]) .option { min-height: var(--mj-control-height-lg); font-size: var(--mj-font-size-lg); }

.check {
  width: 1em; height: 1em; flex-shrink: 0;
  color: var(--mj-accent);
}
:host(:not([multiple])) .check { display: none; }

.optgroup-label {
  padding: var(--mj-space-1) var(--mj-space-3);
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text-muted);
  font-weight: var(--mj-font-weight-medium);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.empty {
  padding: var(--mj-space-4);
  color: var(--mj-text-muted);
  text-align: center;
  font-size: var(--mj-font-size-sm);
}
:host([disabled]) .listbox { opacity: 0.55; pointer-events: none; }
:host([invalid]) .listbox { border-color: var(--mj-color-danger); }
`;

export class MjListbox extends FormControlMixin(MjElement) {
  static tagName = "mj-listbox";
  static styles = STYLES;
  static watched = ["value", "multiple", "disabled", "readonly", "required", "invalid", "size"];

  constructor() {
    super()
    this._initFormControl()
    this._selectedValues = new Set()
    this._focusedIndex = -1
    this._lastClickedIndex = -1
    this._optionData = []
    this._listboxId = nextId("mj-listbox")
  }

  render() {
    const label = this.getAttribute("label") || ""
    const ariaLabel = label.length > 0 ? `aria-label="${label}"` : ""
    const isMulti = this.hasAttribute("multiple")
    const markup = `
      <div
        class="listbox"
        part="listbox"
        id="${this._listboxId}"
        role="listbox"
        tabindex="0"
        ${ariaLabel}
        ${isMulti === true ? 'aria-multiselectable="true"' : ""}
      ></div>
    `
    return markup
  }

  afterRender() {
    this._el = this.$(".listbox")
    this.listen(this._el, "keydown", this._onKeydown.bind(this))
    this.listen(this._el, "click", this._onClick.bind(this))

    const slot = this.shadowRoot.querySelector("slot")
    if (slot !== null) {
      this.listen(slot, "slotchange", () => {
        this._buildOptions()
      })
    }

    this._buildOptions()
    this._initValues()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "value") {
      this._initValues()
    }
    if (name === "multiple") {
      this._selectedValues.clear()
      this._initValues()
      this._rebuildOptions()
    }
    if (name === "disabled" || name === "invalid") {
      this._syncAccessibility()
    }
    return
  }

  /* ----- option management ----- */

  _getOptionEls() {
    return Array.from(this.querySelectorAll("mj-option"))
  }

  _buildOptions() {
    const optEls = this._getOptionEls()
    if (optEls.length === 0) {
      this._optionData = []
      this._el.innerHTML = `<div class="empty" part="empty"><slot name="empty">No options</slot></div>`
      return
    }

    this._optionData = optEls.map((el, idx) => {
      const id = nextId("mj-lb-opt")
      el._mjId = id
      return {
        id,
        value: el.getAttribute("value") || "",
        label: el.textContent.trim(),
        disabled: el.hasAttribute("disabled"),
        index: idx
      }
    })

    this._renderOptions()
    return
  }

  _rebuildOptions() {
    this._buildOptions()
    return
  }

  _renderOptions() {
    const isMulti = this.hasAttribute("multiple")
    let html = ""
    this._optionData.forEach((item) => {
      const selected = this._selectedValues.has(item.value)
      const disabledAttr = item.disabled === true ? ' aria-disabled="true"' : ""
      const selectedAttr = ` aria-selected="${selected === true ? "true" : "false"}"`
      const focusedCls = this._focusedIndex === item.index ? " focused" : ""
      html += `<div
        class="option${focusedCls}"
        part="option"
        role="option"
        id="${item.id}"
        data-value="${item.value}"
        data-index="${item.index}"
        ${selectedAttr}${disabledAttr}
      >
        ${isMulti === true ? `<svg class="check" aria-hidden="true" viewBox="0 0 16 16" fill="currentColor"><path d="M13.5 3.5 6 11 2.5 7.5l1-1L6 9 12.5 2.5z"/></svg>` : ""}
        <span class="option-label" part="option-label">${item.label}</span>
      </div>`
    })
    this._el.innerHTML = html
    return
  }

  _initValues() {
    const attrVal = this.getAttribute("value") || ""
    this._selectedValues.clear()
    if (attrVal.length > 0) {
      attrVal.split(",").forEach((v) => {
        const trimmed = v.trim()
        if (trimmed.length > 0) {
          this._selectedValues.add(trimmed)
        }
      })
    }
    this._syncFormValue()
    if (this._el !== undefined) {
      this._renderOptions()
    }
    return
  }

  _syncFormValue() {
    const vals = Array.from(this._selectedValues)
    this._setFormValue(vals.join(","))
    return
  }

  /* ----- selection ----- */

  _select(index, extend, toggle) {
    if (this.hasAttribute("readonly") || this.hasAttribute("disabled")) {
      return
    }

    const item = this._optionData[index]
    if (item === undefined || item.disabled === true) {
      return
    }

    const isMulti = this.hasAttribute("multiple")
    const previousValues = Array.from(this._selectedValues)

    if (isMulti === false) {
      this._selectedValues.clear()
      this._selectedValues.add(item.value)
    } else if (extend === true && this._lastClickedIndex >= 0) {
      const start = Math.min(this._lastClickedIndex, index)
      const end = Math.max(this._lastClickedIndex, index)
      for (let i = start; i <= end; i = i + 1) {
        const d = this._optionData[i]
        if (d !== undefined && d.disabled !== true) {
          this._selectedValues.add(d.value)
        }
      }
    } else if (toggle === true) {
      if (this._selectedValues.has(item.value)) {
        this._selectedValues.delete(item.value)
      } else {
        this._selectedValues.add(item.value)
      }
    } else {
      this._selectedValues.clear()
      this._selectedValues.add(item.value)
    }

    this._lastClickedIndex = index
    this._focusedIndex = index
    this._syncFormValue()
    this._renderOptions()
    this._scrollIntoView(index)

    const newValues = Array.from(this._selectedValues)
    this.emit("mj-change", {
      values: newValues,
      previousValues: previousValues
    })

    if (isMulti === true) {
      announce(`${newValues.length} items selected`, "polite")
    }
    return
  }

  _scrollIntoView(index) {
    const opts = this._el.querySelectorAll(".option")
    const opt = opts[index]
    if (opt !== undefined) {
      opt.scrollIntoView({ block: "nearest" })
    }
    return
  }

  /* ----- event handlers ----- */

  _onClick(event) {
    const optEl = event.target.closest(".option")
    if (optEl === null) {
      return
    }
    const index = parseInt(optEl.dataset.index, 10)
    const extend = event.shiftKey === true
    const toggle = event.ctrlKey === true || event.metaKey === true
    this._select(index, extend, toggle)
    this._el.focus()
    return
  }

  _onKeydown(event) {
    const count = this._optionData.length
    if (count === 0) {
      return
    }

    let current = this._focusedIndex >= 0 ? this._focusedIndex : -1
    const isMulti = this.hasAttribute("multiple")

    if (event.key === "ArrowDown") {
      event.preventDefault()
      let next = current + 1
      while (next < count && this._optionData[next].disabled === true) {
        next = next + 1
      }
      if (next < count) {
        this._focusedIndex = next
        if (event.shiftKey === true && isMulti === true) {
          this._select(next, true, false)
        } else {
          this._moveFocusOnly(next)
        }
      }
    } else if (event.key === "ArrowUp") {
      event.preventDefault()
      let prev = current - 1
      while (prev >= 0 && this._optionData[prev].disabled === true) {
        prev = prev - 1
      }
      if (prev >= 0) {
        this._focusedIndex = prev
        if (event.shiftKey === true && isMulti === true) {
          this._select(prev, true, false)
        } else {
          this._moveFocusOnly(prev)
        }
      }
    } else if (event.key === "Home") {
      event.preventDefault()
      this._moveFocusOnly(0)
    } else if (event.key === "End") {
      event.preventDefault()
      this._moveFocusOnly(count - 1)
    } else if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      if (current >= 0) {
        this._select(current, false, isMulti === true)
      }
    } else if (event.ctrlKey === true && event.key === "a" && isMulti === true) {
      event.preventDefault()
      this._optionData.forEach((item) => {
        if (item.disabled !== true) {
          this._selectedValues.add(item.value)
        }
      })
      this._syncFormValue()
      this._renderOptions()
    } else if (event.key.length === 1) {
      this._typeaheadNav(event.key)
    }
    return
  }

  _typeaheadNav(char) {
    const needle = char.toLowerCase()
    const start = this._focusedIndex + 1
    const data = this._optionData
    const count = data.length

    for (let i = 0; i < count; i = i + 1) {
      const idx = (start + i) % count
      const item = data[idx]
      if (item.disabled !== true && item.label.toLowerCase().startsWith(needle)) {
        this._moveFocusOnly(idx)
        break
      }
    }
    return
  }

  _moveFocusOnly(index) {
    this._focusedIndex = index
    this._renderOptions()
    this._scrollIntoView(index)
    const opts = this._el.querySelectorAll(".option")
    const opt = opts[index]
    if (opt !== undefined) {
      this._el.setAttribute("aria-activedescendant", opt.id)
    }
    this.emit("mj-option-focus", { option: this._optionData[index] })
    return
  }

  _syncAccessibility() {
    if (this._el === undefined) {
      return
    }
    const invalid = this.hasAttribute("invalid")
    if (invalid === true) {
      this._el.setAttribute("aria-invalid", "true")
    } else {
      this._el.removeAttribute("aria-invalid")
    }
    const disabled = this.hasAttribute("disabled")
    if (disabled === true) {
      this._el.setAttribute("aria-disabled", "true")
    } else {
      this._el.removeAttribute("aria-disabled")
    }
    return
  }

  _customValidity() {
    const required = this.hasAttribute("required")
    if (required === true && this._selectedValues.size === 0) {
      return this.getAttribute("required-message") || "At least one selection is required."
    }
    return ""
  }

  _validationAnchor() {
    return this._el || this
  }

  /* ----- scriptable API ----- */

  get selectedValues() {
    return Array.from(this._selectedValues)
  }

  set value(val) {
    this.setAttribute("value", val)
    return
  }

  get value() {
    return Array.from(this._selectedValues).join(",")
  }

  focus() {
    if (this._el !== undefined) {
      this._el.focus()
    }
    return
  }
}
