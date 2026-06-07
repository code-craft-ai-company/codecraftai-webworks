/*
 * mjlocalepicker.js
 *
 * <mj-locale-picker> — specialized combobox over language, country/region,
 * or full locale datasets using Intl APIs for display names.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { autoPosition } from "../core/overlay.js";
import { announce } from "../core/announcer.js";

const STYLES = `
:host { display: inline-block; vertical-align: middle; }
:host([block]) { display: block; }

.field {
  display: flex;
  align-items: center;
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-locale-picker-border-radius, var(--mj-radius-md));
  background: var(--mj-surface);
  min-height: var(--mj-control-height-md);
  transition: border-color var(--mj-motion-fast);
  overflow: hidden;
}
.field:focus-within { border-color: var(--mj-accent); }
:host([invalid]) .field { border-color: var(--mj-color-danger); }
:host([disabled]) .field { opacity: 0.55; pointer-events: none; }

.flag {
  padding: 0 var(--mj-space-2);
  font-size: var(--mj-locale-picker-flag-size, 1.25rem);
  flex-shrink: 0;
  line-height: 1;
}

.input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  padding: 0 var(--mj-space-2);
  font: inherit;
  font-size: var(--mj-font-size-md);
  color: var(--mj-text);
  min-height: var(--mj-control-height-md);
}

.clear-btn {
  flex-shrink: 0;
  padding: 0 var(--mj-space-2);
  background: none;
  border: none;
  cursor: pointer;
  color: var(--mj-text-muted);
  display: flex;
  align-items: center;
}
.clear-btn.hidden { display: none; }
:host(:not([clearable])) .clear-btn { display: none; }
.clear-btn:hover { color: var(--mj-text); }
.clear-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}

.popup {
  position: fixed;
  background: var(--mj-surface-raised, var(--mj-surface));
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-locale-picker-border-radius, var(--mj-radius-md));
  box-shadow: var(--mj-elevation-2);
  max-height: var(--mj-locale-picker-popup-max-height, 18rem);
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
  padding: var(--mj-space-2) var(--mj-space-3);
  min-height: var(--mj-locale-picker-option-height, 2.5rem);
  cursor: pointer;
  color: var(--mj-text);
}
.option:hover, .option.focused { background: var(--mj-bg-muted); }
.option[aria-selected="true"] { background: var(--mj-bg-subtle); }

.option-flag { font-size: var(--mj-locale-picker-flag-size, 1.25rem); flex-shrink: 0; }
.option-names { display: flex; flex-direction: column; flex: 1; min-width: 0; }
.option-native { font-size: var(--mj-font-size-sm); font-weight: var(--mj-font-weight-medium); }
.option-english { font-size: var(--mj-font-size-xs); color: var(--mj-text-muted); }
.option-code {
  font-size: var(--mj-font-size-xs);
  color: var(--mj-locale-picker-code-color, var(--mj-text-muted));
  font-family: var(--mj-font-mono);
  flex-shrink: 0;
}
.check {
  width: 1em; height: 1em; color: var(--mj-accent); flex-shrink: 0;
  opacity: 0;
}
.option[aria-selected="true"] .check { opacity: 1; }

.no-results {
  padding: var(--mj-space-3);
  text-align: center;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text-muted);
}
`;

function getCountryFlag(code) {
  if (code.length !== 2) {
    return "🌐"
  }
  const upper = code.toUpperCase()
  const codePoints = Array.from(upper).map((ch) => 0x1F1E6 + ch.charCodeAt(0) - 65)
  return String.fromCodePoint(...codePoints)
}

function buildLanguageDataset(displayLocale) {
  const locale = displayLocale || navigator.language || "en"
  const displayNames = new Intl.DisplayNames([locale], { type: "language" })
  const nativeNames = new Intl.DisplayNames(["und"], { type: "language", languageDisplay: "dialect" })

  const commonLangs = [
    "en", "es", "fr", "de", "it", "pt", "ja", "ko", "zh",
    "ar", "ru", "pl", "nl", "sv", "da", "no", "fi", "tr",
    "cs", "hu", "ro", "el", "he", "hi", "id", "th", "vi",
    "uk", "sk", "bg", "hr", "lt", "lv", "et", "sl"
  ]

  return commonLangs.map((code) => {
    let displayName = code
    let nativeName = code
    try {
      displayName = displayNames.of(code) || code
    } catch { /* empty */ }
    try {
      nativeName = new Intl.DisplayNames([code], { type: "language" }).of(code) || code
    } catch { /* empty */ }
    return { code, nativeName, displayName, flag: "" }
  })
}

function buildCountryDataset(displayLocale) {
  const locale = displayLocale || navigator.language || "en"
  const displayNames = new Intl.DisplayNames([locale], { type: "region" })

  const commonCountries = [
    "US", "GB", "DE", "FR", "ES", "IT", "JP", "KR", "CN",
    "IN", "BR", "CA", "AU", "MX", "RU", "AR", "NG", "ZA",
    "EG", "SA", "AE", "PL", "NL", "SE", "NO", "DK", "FI",
    "CH", "AT", "BE", "PT", "GR", "TR", "UA", "CZ", "HU",
    "RO", "BG", "HR", "SK", "SL", "LT", "LV", "EE"
  ]

  return commonCountries.map((code) => {
    let displayName = code
    try {
      displayName = displayNames.of(code) || code
    } catch { /* empty */ }
    const flag = getCountryFlag(code)
    return { code, nativeName: displayName, displayName, flag }
  }).sort((a, b) => a.displayName.localeCompare(b.displayName))
}

export class MjLocalePicker extends FormControlMixin(MjElement) {
  static tagName = "mj-locale-picker";
  static styles = STYLES;
  static watched = ["value", "mode", "open", "disabled", "invalid", "clearable", "allowed", "excluded", "show-flag", "show-code", "show-native-name"];

  constructor() {
    super()
    this._initFormControl()
    this._inputValue = ""
    this._allOptions = []
    this._filteredOptions = []
    this._focusedIndex = -1
    this._selectedLocale = null
    this._disposePosition = null
    this._listboxId = nextId("mj-lp-lb")
    this._inputId = nextId("mj-lp-in")
  }

  render() {
    const ph = this.getAttribute("placeholder") || "Select a language"
    const markup = `
      <div class="field" part="field">
        <span class="flag" part="trigger-icon" aria-hidden="true"><slot name="trigger-icon">🌐</slot></span>
        <input
          class="input"
          part="input"
          id="${this._inputId}"
          role="combobox"
          aria-haspopup="listbox"
          aria-expanded="false"
          aria-autocomplete="list"
          aria-controls="${this._listboxId}"
          placeholder="${ph}"
          autocomplete="off"
          type="text"
        />
        <button class="clear-btn hidden" part="clear" type="button" aria-label="Clear selection">
          <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
            <path d="M12 4 8 8l4 4-1 1-4-4-4 4-1-1 4-4-4-4 1-1 4 4 4-4z"/>
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
    this._field = this.$(".field")
    this._input = this.$(".input")
    this._popup = this.$(".popup")
    this._listbox = this.$(".listbox")
    this._clearBtn = this.$(".clear-btn")
    this._flagIcon = this.$(".flag")

    this.listen(this._input, "input", this._onInput.bind(this))
    this.listen(this._input, "keydown", this._onKeydown.bind(this))
    this.listen(this._input, "blur", this._onBlur.bind(this))
    this.listen(this._clearBtn, "click", this._onClear.bind(this))
    this.listen(document, "click", this._onDocClick.bind(this))

    this._buildDataset()

    const attrVal = this.getAttribute("value") || ""
    if (attrVal.length > 0) {
      this._applyValue(attrVal)
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "value" && this._input !== undefined) {
      this._applyValue(newValue || "")
    }
    if (name === "open") {
      this._syncOpen()
    }
    if (name === "mode") {
      this._buildDataset()
    }
    return
  }

  _buildDataset() {
    const mode = this.getAttribute("mode") || "language"
    const displayLocale = this.getAttribute("display-locale") || navigator.language || "en"
    const allowedAttr = this.getAttribute("allowed") || ""
    const excludedAttr = this.getAttribute("excluded") || ""

    let items = []
    if (mode === "country" || mode === "locale") {
      items = buildCountryDataset(displayLocale)
    } else {
      items = buildLanguageDataset(displayLocale)
    }

    if (allowedAttr.length > 0) {
      let allowed = []
      try {
        allowed = JSON.parse(allowedAttr)
      } catch { /* empty */ }
      if (allowed.length > 0) {
        items = items.filter((item) => allowed.includes(item.code))
      }
    }

    if (excludedAttr.length > 0) {
      let excluded = []
      try {
        excluded = JSON.parse(excludedAttr)
      } catch { /* empty */ }
      if (excluded.length > 0) {
        items = items.filter((item) => excluded.includes(item.code) === false)
      }
    }

    this._allOptions = items
    this._filteredOptions = items.slice()
    return
  }

  _applyValue(code) {
    if (code.length === 0) {
      this._selectedLocale = null
      this._setFormValue("")
      this._inputValue = ""
      if (this._input !== undefined) {
        this._input.value = ""
      }
      this._syncFlagIcon(null)
      this._syncClearBtn()
      return
    }

    const found = this._allOptions.find((opt) => opt.code === code)
    if (found !== undefined) {
      this._selectedLocale = found
      this._setFormValue(code)
      this._inputValue = found.displayName
      if (this._input !== undefined) {
        this._input.value = found.displayName
      }
      this._syncFlagIcon(found)
    } else {
      this._setFormValue(code)
      this._inputValue = code
      if (this._input !== undefined) {
        this._input.value = code
      }
    }
    this._syncClearBtn()
    return
  }

  _syncFlagIcon(locale) {
    if (this._flagIcon === undefined) {
      return
    }
    const showFlag = this.hasAttribute("show-flag") === false || this.getAttribute("show-flag") !== "false"
    if (showFlag === false || locale === null) {
      this._flagIcon.textContent = "🌐"
    } else {
      this._flagIcon.textContent = locale.flag || "🌐"
    }
    return
  }

  _syncClearBtn() {
    if (this._clearBtn === undefined) {
      return
    }
    const hasVal = (this._value || "").length > 0
    const clearable = this.hasAttribute("clearable")
    if (clearable === true && hasVal === true) {
      this._clearBtn.classList.remove("hidden")
    } else {
      this._clearBtn.classList.add("hidden")
    }
    return
  }

  _filterOptions(query) {
    if (query.length === 0) {
      return this._allOptions.slice()
    }
    const q = query.normalize("NFKD").toLowerCase()
    return this._allOptions.filter((opt) => {
      const native = (opt.nativeName || "").normalize("NFKD").toLowerCase()
      const display = (opt.displayName || "").normalize("NFKD").toLowerCase()
      const code = (opt.code || "").toLowerCase()
      return native.includes(q) || display.includes(q) || code.includes(q)
    })
  }

  _renderOptions(query) {
    const filtered = this._filterOptions(query || "")
    this._filteredOptions = filtered
    const showNative = this.getAttribute("show-native-name") !== "false"
    const showCode = this.getAttribute("show-code") === "true"
    const showFlag = this.getAttribute("show-flag") !== "false"

    if (filtered.length === 0) {
      this._listbox.innerHTML = `<div class="no-results" part="no-results"><slot name="no-results">No results</slot></div>`
      announce("No results found", "polite")
      return
    }

    let html = ""
    filtered.forEach((opt, idx) => {
      const selected = opt.code === this._value ? ' aria-selected="true"' : ' aria-selected="false"'
      const flagHtml = showFlag === true && opt.flag !== undefined && opt.flag.length > 0
        ? `<span class="option-flag" part="option-flag" aria-hidden="true">${opt.flag}</span>`
        : ""
      const nativeHtml = showNative === true
        ? `<span class="option-native" part="option-native-name" dir="auto">${opt.nativeName}</span>`
        : ""
      const englishHtml = `<span class="option-english" part="option-english-name">${opt.displayName}</span>`
      const codeHtml = showCode === true
        ? `<span class="option-code" part="option-code">${opt.code}</span>`
        : ""
      const ariaLabel = `${opt.nativeName} – ${opt.displayName}`

      html += `<div
        class="option"
        part="option"
        role="option"
        id="${nextId("mj-lp-opt")}"
        ${selected}
        data-code="${opt.code}"
        data-idx="${idx}"
        aria-label="${ariaLabel}"
      >
        ${flagHtml}
        <span class="option-names">
          ${nativeHtml}
          ${englishHtml}
        </span>
        ${codeHtml}
        <svg class="check" aria-hidden="true" viewBox="0 0 16 16" fill="currentColor">
          <path d="M13.5 3.5 6 11 2.5 7.5l1-1L6 9 12.5 2.5z"/>
        </svg>
      </div>`
    })
    this._listbox.innerHTML = html

    const opts = this._listbox.querySelectorAll(".option")
    opts.forEach((opt) => {
      this.listen(opt, "click", this._onOptionClick.bind(this))
      this.listen(opt, "mouseover", (e) => {
        opts.forEach((o) => o.classList.remove("focused"))
        e.currentTarget.classList.add("focused")
        this._focusedIndex = parseInt(e.currentTarget.dataset.idx, 10)
        this._input.setAttribute("aria-activedescendant", e.currentTarget.id)
      })
    })
    this._focusedIndex = -1
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
    return
  }

  _syncOpen() {
    const isOpen = this.hasAttribute("open")
    this._input.setAttribute("aria-expanded", isOpen === true ? "true" : "false")
    if (isOpen === true) {
      this._popup.style.minWidth = `${this._field.offsetWidth}px`
      this._disposePosition = autoPosition(this._popup, this._field, { placement: "bottom-start" })
      this._renderOptions(this._inputValue)
    } else {
      if (this._disposePosition !== null) {
        this._disposePosition()
        this._disposePosition = null
      }
    }
    return
  }

  _onInput() {
    this._inputValue = this._input.value
    this.emit("mj-input", { inputValue: this._inputValue })
    this._open()
    this._renderOptions(this._inputValue)
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
      const prev = Math.max(this._focusedIndex - 1, 0)
      this._setFocused(opts, prev)
    } else if (event.key === "Home" && isOpen === true) {
      event.preventDefault()
      this._setFocused(opts, 0)
    } else if (event.key === "End" && isOpen === true) {
      event.preventDefault()
      this._setFocused(opts, opts.length - 1)
    } else if (event.key === "Enter" && isOpen === true && this._focusedIndex >= 0) {
      event.preventDefault()
      const opt = opts[this._focusedIndex]
      if (opt !== undefined) {
        this._commitOption(opt)
      }
    } else if (event.key === "Escape") {
      event.preventDefault()
      this._revert()
      this._close()
    } else if (event.key === "Tab") {
      if (isOpen === true) {
        this._revert()
        this._close()
      }
    } else if (event.altKey === true && event.key === "ArrowDown") {
      event.preventDefault()
      this._open()
      this._renderOptions(this._inputValue)
    } else if (event.altKey === true && event.key === "ArrowUp") {
      event.preventDefault()
      this._close()
    } else if (event.key === "Backspace") {
      this._syncClearBtn()
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
    this._commitOption(event.currentTarget)
    return
  }

  _commitOption(node) {
    const code = node.dataset.code
    const locale = this._allOptions.find((opt) => opt.code === code)
    const prevValue = this._value
    this._applyValue(code)
    this._selectedLocale = locale || null
    this.setAttribute("value", code)
    this.emit("mj-change", { value: code, previousValue: prevValue, locale: locale || null })
    this._close()
    this._input.focus()
    return
  }

  _revert() {
    const val = this._value || ""
    if (val.length > 0) {
      const found = this._allOptions.find((opt) => opt.code === val)
      if (found !== undefined) {
        this._inputValue = found.displayName
        this._input.value = found.displayName
      }
    } else {
      this._inputValue = ""
      this._input.value = ""
    }
    return
  }

  _onBlur() {
    setTimeout(() => {
      if (this.hasAttribute("open") === false) {
        return
      }
      this._revert()
      this._close()
    }, 150)
    return
  }

  _onClear() {
    const prevValue = this._value
    this._applyValue("")
    this.setAttribute("value", "")
    this.emit("mj-change", { value: "", previousValue: prevValue, locale: null })
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

  get selectedLocale() {
    return this._selectedLocale
  }

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
