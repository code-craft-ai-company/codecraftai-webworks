/*
 * mjcombobox.js
 *
 * <mj-combobox> — filterable/searchable input with popup suggestion list.
 * Supports sync options, async data source, free-text mode, and clearable.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { autoPosition } from "../core/overlay.js";
import { announce } from "../core/announcer.js";

const STYLES = `
:host { display: inline-block; vertical-align: middle; }
:host([block]) { display: block; }

.wrapper {
  display: flex;
  align-items: center;
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-combobox-border-radius, var(--mj-radius-md));
  background: var(--mj-surface);
  min-height: var(--mj-combobox-input-height, var(--mj-control-height-md));
  transition: border-color var(--mj-motion-fast) var(--mj-motion-ease);
  overflow: hidden;
}
.wrapper:focus-within { border-color: var(--mj-accent); }
:host([invalid]) .wrapper { border-color: var(--mj-color-danger); }
:host([disabled]) .wrapper { opacity: 0.55; pointer-events: none; }

.prefix { padding: 0 var(--mj-space-2); color: var(--mj-text-muted); display: flex; align-items: center; }
.input {
  flex: 1;
  min-width: 0;
  padding: 0 var(--mj-space-3);
  border: none;
  outline: none;
  background: transparent;
  font: inherit;
  font-size: var(--mj-font-size-md);
  color: var(--mj-text);
  height: 100%;
  min-height: var(--mj-combobox-input-height, var(--mj-control-height-md));
}
.clear, .toggle {
  flex-shrink: 0;
  padding: 0 var(--mj-space-2);
  background: none;
  border: none;
  cursor: pointer;
  color: var(--mj-text-muted);
  display: flex;
  align-items: center;
}
.clear:hover, .toggle:hover { color: var(--mj-text); }
.clear:focus-visible, .toggle:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}
:host(:not([clearable])) .clear { display: none; }
.clear.hidden { display: none; }

.popup {
  position: fixed;
  background: var(--mj-surface-raised, var(--mj-surface));
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-combobox-border-radius, var(--mj-radius-md));
  box-shadow: var(--mj-elevation-2);
  max-height: var(--mj-combobox-popup-max-height, 18rem);
  overflow-y: auto;
  min-width: var(--mj-combobox-popup-min-width, 0);
  z-index: var(--mj-layer-popover);
  display: none;
}
:host([open]) .popup { display: block; }

.listbox { padding: var(--mj-space-1) 0; }

.option {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  padding: var(--mj-space-2) var(--mj-space-3);
  cursor: pointer;
  color: var(--mj-text);
  font-size: var(--mj-font-size-md);
}
.option:hover, .option.focused { background: var(--mj-bg-muted); }
.option[aria-selected="true"] { background: var(--mj-bg-subtle); }
.option[aria-disabled="true"] { opacity: 0.45; cursor: not-allowed; }

.no-results, .error-inline {
  padding: var(--mj-space-3);
  color: var(--mj-text-muted);
  text-align: center;
  font-size: var(--mj-font-size-sm);
}
.error-inline { color: var(--mj-color-danger); }

mark {
  background: transparent;
  color: var(--mj-combobox-match-color, var(--mj-accent));
  font-weight: var(--mj-font-weight-medium);
}
`;

export class MjCombobox extends FormControlMixin(MjElement) {
  static tagName = "mj-combobox";
  static styles = STYLES;
  static watched = ["value", "open", "disabled", "readonly", "invalid", "placeholder", "clearable", "free-text", "size"];

  constructor() {
    super()
    this._initFormControl()
    this._inputValue = ""
    this._focusedIndex = -1
    this._optionData = []
    this._debounceTimer = null
    this._disposePosition = null
    this._listboxId = nextId("mj-cb-lb")
    this._inputId = nextId("mj-cb-in")
  }

  render() {
    const ph = this.getAttribute("placeholder") || ""
    const markup = `
      <div class="wrapper" part="wrapper">
        <span class="prefix" part="prefix" aria-hidden="true"><slot name="prefix"></slot></span>
        <input
          class="input"
          part="input"
          id="${this._inputId}"
          role="combobox"
          aria-haspopup="listbox"
          aria-expanded="false"
          aria-autocomplete="list"
          aria-controls="${this._listboxId}"
          autocomplete="off"
          placeholder="${ph}"
          type="text"
        />
        <button class="clear hidden" part="clear" type="button" tabindex="-1" aria-label="Clear">
          <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
            <path d="M12 4 8 8l4 4-1 1-4-4-4 4-1-1 4-4-4-4 1-1 4 4 4-4z"/>
          </svg>
        </button>
        <button class="toggle" part="toggle" type="button" tabindex="-1" aria-label="Toggle suggestions" aria-hidden="true">
          <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
            <path d="M8 10.5 3 5.5h10z"/>
          </svg>
        </button>
      </div>
      <div class="popup" part="popup">
        <div class="listbox" part="listbox" id="${this._listboxId}" role="listbox" tabindex="-1"></div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._input = this.$(".input")
    this._popup = this.$(".popup")
    this._listbox = this.$(".listbox")
    this._clearBtn = this.$(".clear")
    this._wrapper = this.$(".wrapper")

    this.listen(this._input, "input", this._onInput.bind(this))
    this.listen(this._input, "keydown", this._onKeydown.bind(this))
    this.listen(this._input, "blur", this._onBlur.bind(this))
    this.listen(this._clearBtn, "click", this._onClear.bind(this))
    this.listen(document, "click", this._onDocClick.bind(this))

    this._buildOptions()
    this._syncClearBtn()

    const attrVal = this.getAttribute("value") || ""
    if (attrVal.length > 0) {
      this._setFormValue(attrVal)
      this._inputValue = this._labelForValue(attrVal)
      this._input.value = this._inputValue
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "value" && this._input !== undefined) {
      this._setFormValue(newValue || "")
      this._inputValue = this._labelForValue(newValue || "")
      this._input.value = this._inputValue
      this._syncClearBtn()
    }
    if (name === "open") {
      this._syncOpen()
    }
    return
  }

  /* ----- options ----- */

  _getOptionEls() {
    return Array.from(this.querySelectorAll("mj-option"))
  }

  _buildOptions() {
    const els = this._getOptionEls()
    this._optionData = els.map((el, idx) => ({
      id: nextId("mj-cb-opt"),
      value: el.getAttribute("value") || "",
      label: el.textContent.trim(),
      disabled: el.hasAttribute("disabled"),
      index: idx
    }))
    return
  }

  _labelForValue(val) {
    const match = this._optionData.find((d) => d.value === val)
    return match !== undefined ? match.label : val
  }

  _filteredOptions(query) {
    if (query.length === 0) {
      return this._optionData
    }
    const needle = query.toLowerCase()
    return this._optionData.filter((d) => d.label.toLowerCase().includes(needle))
  }

  _renderOptions(query) {
    const filtered = this._filteredOptions(query || "")
    if (filtered.length === 0) {
      this._listbox.innerHTML = `<div class="no-results" part="no-results"><slot name="no-results">No results</slot></div>`
      return
    }

    let html = ""
    filtered.forEach((item) => {
      const disabledAttr = item.disabled === true ? ' aria-disabled="true"' : ""
      const selectedAttr = ` aria-selected="${item.value === this._value ? "true" : "false"}"`
      const labelHtml = this._highlight(item.label, query || "")
      html += `<div
        class="option"
        part="option"
        role="option"
        id="${item.id}"
        data-value="${item.value}"
        data-label="${item.label}"
        data-idx="${item.index}"
        ${selectedAttr}${disabledAttr}
      ><span class="option-label" part="option-label">${labelHtml}</span></div>`
    })
    this._listbox.innerHTML = html

    const optNodes = this._listbox.querySelectorAll(".option")
    optNodes.forEach((node) => {
      this.listen(node, "click", this._onOptionClick.bind(this))
      this.listen(node, "mouseover", (e) => {
        const opts = Array.from(this._listbox.querySelectorAll(".option"))
        opts.forEach((o) => o.classList.remove("focused"))
        e.currentTarget.classList.add("focused")
        this._focusedIndex = opts.indexOf(e.currentTarget)
        this._input.setAttribute("aria-activedescendant", e.currentTarget.id)
      })
    })
    this._focusedIndex = -1
    return
  }

  _highlight(label, query) {
    if (query.length === 0) {
      return label
    }
    const idx = label.toLowerCase().indexOf(query.toLowerCase())
    if (idx < 0) {
      return label
    }
    const before = label.slice(0, idx)
    const match = label.slice(idx, idx + query.length)
    const after = label.slice(idx + query.length)
    return `${before}<mark aria-hidden="true">${match}</mark>${after}`
  }

  /* ----- open/close ----- */

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
    return
  }

  _syncOpen() {
    const isOpen = this.hasAttribute("open")
    this._input.setAttribute("aria-expanded", isOpen === true ? "true" : "false")
    if (isOpen === true) {
      this._popup.style.minWidth = `${this._wrapper.offsetWidth}px`
      this._disposePosition = autoPosition(this._popup, this._wrapper, {
        placement: "bottom-start"
      })
      this._renderOptions(this._inputValue)
    } else {
      if (this._disposePosition !== null) {
        this._disposePosition()
        this._disposePosition = null
      }
    }
    return
  }

  _syncClearBtn() {
    if (this._clearBtn === undefined) {
      return
    }
    const hasValue = this._value.length > 0 || this._inputValue.length > 0
    const clearable = this.hasAttribute("clearable")
    if (clearable === true && hasValue === true) {
      this._clearBtn.classList.remove("hidden")
    } else {
      this._clearBtn.classList.add("hidden")
    }
    return
  }

  /* ----- event handlers ----- */

  _onInput(event) {
    this._inputValue = this._input.value
    this.emit("mj-input", { inputValue: this._inputValue })
    this._syncClearBtn()

    clearTimeout(this._debounceTimer)
    const delay = parseInt(this.getAttribute("debounce") || "300", 10)
    const minChars = parseInt(this.getAttribute("min-chars") || "1", 10)

    this._debounceTimer = setTimeout(() => {
      if (this._inputValue.length >= minChars) {
        this._open()
        this._renderOptions(this._inputValue)
        this.emit("mj-filter", { query: this._inputValue })
      } else {
        this._close()
      }
    }, delay)
    return
  }

  _onKeydown(event) {
    const isOpen = this.hasAttribute("open")
    const opts = isOpen === true ? Array.from(this._listbox.querySelectorAll(".option")) : []

    if (event.key === "ArrowDown") {
      event.preventDefault()
      if (isOpen === false) {
        this._open()
        this._renderOptions(this._inputValue)
        return
      }
      const next = Math.min(this._focusedIndex + 1, opts.length - 1)
      this._setFocused(opts, next)
    } else if (event.key === "ArrowUp") {
      event.preventDefault()
      if (isOpen === false) {
        return
      }
      const prev = Math.max(this._focusedIndex - 1, 0)
      this._setFocused(opts, prev)
    } else if (event.key === "Home" && isOpen === true) {
      event.preventDefault()
      this._setFocused(opts, 0)
    } else if (event.key === "End" && isOpen === true) {
      event.preventDefault()
      this._setFocused(opts, opts.length - 1)
    } else if (event.key === "Enter") {
      if (isOpen === true && this._focusedIndex >= 0 && opts[this._focusedIndex] !== undefined) {
        event.preventDefault()
        this._commitOption(opts[this._focusedIndex])
      } else if (this.hasAttribute("free-text") === true) {
        event.preventDefault()
        this._commitFreeText()
      }
    } else if (event.key === "Escape") {
      event.preventDefault()
      this._revert()
      this._close()
    } else if (event.key === "Tab") {
      if (isOpen === true) {
        if (this.hasAttribute("free-text") === true) {
          this._commitFreeText()
        } else {
          this._revert()
        }
        this._close()
      }
    } else if (event.altKey === true && event.key === "ArrowDown") {
      event.preventDefault()
      this._open()
      this._renderOptions(this._inputValue)
    } else if (event.altKey === true && event.key === "ArrowUp") {
      event.preventDefault()
      this._close()
    }
    return
  }

  _setFocused(opts, index) {
    opts.forEach((o) => o.classList.remove("focused"))
    const opt = opts[index]
    if (opt !== undefined) {
      opt.classList.add("focused")
      opt.scrollIntoView({ block: "nearest" })
      this._focusedIndex = index
      this._input.setAttribute("aria-activedescendant", opt.id)
    }
    return
  }

  _onOptionClick(event) {
    const node = event.currentTarget
    if (node.getAttribute("aria-disabled") === "true") {
      return
    }
    this._commitOption(node)
    return
  }

  _commitOption(node) {
    const value = node.dataset.value
    const label = node.dataset.label
    const prevValue = this._value
    this._setFormValue(value)
    this.setAttribute("value", value)
    this._inputValue = label
    this._input.value = label
    this._syncClearBtn()
    this.emit("mj-change", { value: value, previousValue: prevValue, option: null })
    this._close()
    this._input.focus()
    return
  }

  _commitFreeText() {
    const text = this._inputValue.trim()
    if (text.length === 0) {
      return
    }
    const prevValue = this._value
    this._setFormValue(text)
    this.setAttribute("value", text)
    this._syncClearBtn()
    this.emit("mj-change", { value: text, previousValue: prevValue, option: null })
    return
  }

  _revert() {
    const label = this._labelForValue(this._value)
    this._inputValue = label
    this._input.value = label
    return
  }

  _onBlur() {
    setTimeout(() => {
      if (this.hasAttribute("open") === false) {
        return
      }
      if (this.hasAttribute("free-text") === true) {
        this._commitFreeText()
      } else {
        this._revert()
      }
      this._close()
    }, 150)
    return
  }

  _onClear() {
    const prevValue = this._value
    this._setFormValue("")
    this.setAttribute("value", "")
    this._inputValue = ""
    this._input.value = ""
    this._syncClearBtn()
    this.emit("mj-change", { value: "", previousValue: prevValue, option: null })
    this.emit("mj-clear", {})
    this._input.focus()
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

  _validationAnchor() {
    return this._input || this
  }

  /* ----- scriptable API ----- */

  get inputValue() {
    return this._inputValue
  }

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

  focus() {
    if (this._input !== undefined) {
      this._input.focus()
    }
    return
  }
}
