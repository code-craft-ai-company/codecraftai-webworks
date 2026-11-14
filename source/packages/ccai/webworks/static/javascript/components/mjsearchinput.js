/*
 * mjsearchinput.js
 *
 * <mj-search-input> -- search field with leading icon, clear button,
 * optional suggestions popup, and submit-on-Enter semantics.
 *
 * Value model: `this._value` (owned by FormControlMixin) is the single source
 * of truth; the `value` attribute is the default value and the shadow <input>
 * is rebuilt from `this._value` on every render.
 *
 * ARIA: without suggestions the input is a plain `searchbox`. As soon as the
 * host supplies suggestions (or sets `loading`) it becomes a `combobox` that
 * controls the listbox popup, following the WAI-ARIA combobox pattern.
 *
 * Validation (`required`, `maxlength` for a value set by script) is shown
 * like in the other text controls: an inline error and `mj-invalid` once
 * focus has left the component or a check / submit failed.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";
import { announce } from "../core/announcer.js";

const STYLES = `
:host {
  display: block;
  font-family: var(--mj-font-sans);
  font-size: var(--mj-font-size-md);
}

.search-wrap {
  position: relative;
}

.field {
  display: flex;
  align-items: center;
  min-height: var(--mj-control-height-md);
  background: var(--mj-surface);
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-pill);
  transition: border-color var(--mj-motion-fast) var(--mj-motion-ease);
  overflow: hidden;
}
.field:focus-within {
  border-color: var(--mj-accent);
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.search-icon {
  display: flex;
  align-items: center;
  padding: 0 var(--mj-space-3);
  color: var(--mj-text-muted);
  flex-shrink: 0;
  pointer-events: none;
}
.search-icon svg { width: 1rem; height: 1rem; }

input {
  flex: 1;
  min-width: 0;
  padding: 0 var(--mj-space-2);
  font: inherit;
  color: var(--mj-text);
  background: transparent;
  border: none;
  outline: none;
}
input::-webkit-search-cancel-button { display: none; }
input::placeholder { color: var(--mj-text-muted); }

.clear-btn, .submit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  margin-inline-end: var(--mj-space-1);
  padding: 0;
  background: transparent;
  border: none;
  border-radius: var(--mj-radius-circle);
  cursor: pointer;
  color: var(--mj-text-muted);
  flex-shrink: 0;
}
.clear-btn:hover, .submit-btn:hover { color: var(--mj-text); background: var(--mj-bg-muted); }
.clear-btn:focus-visible, .submit-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}
.clear-btn svg { width: 0.75rem; height: 0.75rem; }
.clear-btn[hidden] { display: none; }
.submit-btn[hidden] { display: none; }

.popup {
  position: absolute;
  top: calc(100% + var(--mj-space-1));
  inset-inline-start: 0;
  inset-inline-end: 0;
  background: var(--mj-surface-raised);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-md);
  box-shadow: var(--mj-elevation-2);
  max-height: 300px;
  overflow-y: auto;
  z-index: var(--mj-layer-popover);
}
.popup[hidden] { display: none; }

.option {
  padding: var(--mj-space-2) var(--mj-space-3);
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.option:hover, .option[data-active] { background: var(--mj-bg-muted); }
.option-description {
  display: block;
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
}

.loading-msg {
  padding: var(--mj-space-3);
  color: var(--mj-text-muted);
  font-size: var(--mj-font-size-sm);
}

.field[data-invalid] { border-color: var(--mj-color-danger); }

.help {
  margin-top: var(--mj-space-1);
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text-muted);
}
.help:empty { display: none; }

.error {
  display: none;
  margin-top: var(--mj-space-1);
  font-size: var(--mj-font-size-sm);
  color: var(--mj-color-danger);
}
.error[data-visible] { display: block; }

:host([disabled]) .field, .field[data-disabled] { opacity: 0.55; pointer-events: none; }
`;

/* Field name used for form submission when the host has no `name`. */
const DEFAULT_NAME = "q";

/*
 * The accessible name the page gave the host: `aria-labelledby`, then
 * `aria-label`, then an associated <label for> / wrapping <label>, then an
 * <mj-label for>. The shadow control cannot see any of these across the
 * shadow boundary, so the component copies the text onto it.
 */
function resolveHostLabel(host, internals) {
  let name = ""
  const root = host.getRootNode()

  const labelledBy = host.getAttribute("aria-labelledby") || ""
  if (labelledBy.trim().length > 0 && typeof root.getElementById === "function") {
    const parts = []
    const ids = labelledBy.trim().split(/\s+/)
    for (let index = 0; index < ids.length; index = index + 1) {
      const labelNode = root.getElementById(ids[index])
      if (labelNode !== null) {
        parts.push(labelNode.textContent.trim())
      }
    }
    name = parts.join(" ").trim()
  }

  if (name.length === 0) {
    name = (host.getAttribute("aria-label") || "").trim()
  }

  if (name.length === 0 && internals !== null && internals !== undefined && internals.labels !== undefined) {
    const parts = []
    for (let index = 0; index < internals.labels.length; index = index + 1) {
      parts.push(internals.labels[index].textContent.trim())
    }
    name = parts.join(" ").trim()
  }

  if (name.length === 0 && host.id.length > 0 && typeof root.querySelector === "function") {
    const mjLabel = root.querySelector(`mj-label[for="${CSS.escape(host.id)}"]`)
    if (mjLabel !== null) {
      name = mjLabel.textContent.trim()
    }
  }

  return name
}

/*
 * Accept `{ value, label, description }` objects and plain strings; anything
 * else is dropped. The original item is kept for event payloads.
 */
function normalizeSuggestions(items) {
  const normalized = []

  if (Array.isArray(items) === true) {
    for (let index = 0; index < items.length; index = index + 1) {
      const item = items[index]
      if (typeof item === "string" || typeof item === "number") {
        const text = String(item)
        normalized.push({ value: text, label: text, description: "", source: { value: text, label: text } })
      } else if (item !== null && typeof item === "object") {
        const value = item.value !== null && item.value !== undefined ? String(item.value) : ""
        const label = item.label !== null && item.label !== undefined && String(item.label).length > 0
          ? String(item.label)
          : value
        const description = item.description !== null && item.description !== undefined
          ? String(item.description)
          : ""
        normalized.push({ value: value, label: label, description: description, source: item })
      }
    }
  }

  return normalized
}

export class MjSearchInput extends FormControlMixin(MjElement) {
  static tagName = "mj-search-input";
  static styles = STYLES;
  static watched = [
    "value", "placeholder", "label", "help-text", "error-message", "disabled", "readonly",
    "required", "show-submit-button", "loading", "debounce", "min-chars", "no-clear-button",
    "maxlength", "autocomplete", "submit-label", "name", "aria-label", "aria-labelledby"
  ];

  constructor() {
    super()
    this._initFormControl()

    /* Suggestions as given by the host, and the normalized rows drawn. */
    this._suggestions = []
    this._rows = []
    this._activeIndex = -1

    /* True once the host has used suggestions; switches the ARIA pattern. */
    this._suggestMode = false

    this._debounceTimer = null

    /* The query most recently announced through mj-query-change. */
    this._lastQuery = ""

    /* The `value` attribute text most recently applied to the control. */
    this._appliedValueAttribute = null

    /* True while an ancestor <fieldset disabled> disables the control. */
    this._formDisabled = false

    /* Errors are shown once focus has left the component or a check failed. */
    this._showErrors = false

    this._popupId = nextId("mjsi-popup")
    this._helpId = nextId("mjsi-help")
    this._errorId = nextId("mjsi-error")
  }

  render() {
    const markup = html`
      <div role="search" part="search">
        <div class="search-wrap">
          <div class="field" part="field">
            <span class="search-icon" part="search-icon" aria-hidden="true">
              <slot name="search-icon">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
                  <circle cx="6.5" cy="6.5" r="4.5"/><path d="M10.5 10.5l3 3"/>
                </svg>
              </slot>
            </span>
            <input part="input" type="search" autocomplete="off" />
            <button class="clear-btn" part="clear-button" type="button" hidden>
              <svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" aria-hidden="true">
                <path d="M2 2l8 8M10 2l-8 8"/>
              </svg>
            </button>
            <button class="submit-btn" part="submit-button" type="button" hidden>
              <slot name="submit-icon"><span aria-hidden="true">&#x2192;</span></slot>
            </button>
          </div>
          <div class="popup" part="popup" id="${this._popupId}" role="listbox" hidden></div>
        </div>
        <span class="help" part="help" id="${this._helpId}"></span>
        <span class="error" part="error" id="${this._errorId}" role="alert"></span>
      </div>
    `
    return markup
  }

  afterRender() {
    this._searchEl = this.$("[role='search']")
    this._fieldEl = this.$(".field")
    this._input = this.$("input")
    this._clearBtn = this.$(".clear-btn")
    this._submitBtn = this.$(".submit-btn")
    this._popup = this.$(".popup")
    this._helpEl = this.$(".help")
    this._errorEl = this.$(".error")

    this._clearBtn.setAttribute("aria-label", t("mj.searchInput.clear"))

    /*
     * The shadow DOM is new: rebuild it from the stored state. Registering
     * the value also makes an untouched control submit an (empty) entry, as
     * a native one does.
     */
    this._setFormValue(this._value)
    this._input.value = this._value
    this._syncAll()
    this._renderPopup()

    this.listen(this._input, "input", this._onInput.bind(this))
    this.listen(this._input, "keydown", this._onKeydown.bind(this))
    this.listen(this._input, "focus", this._onFocus.bind(this))
    this.listen(this._clearBtn, "click", this._onClear.bind(this))
    this.listen(this._submitBtn, "click", this._onSubmit.bind(this))
    this.listen(this._popup, "mousedown", this._onPopupMousedown.bind(this))
    this.listen(this._popup, "click", this._onPopupClick.bind(this))
    this.listen(this.shadowRoot, "focusout", this._onFocusout.bind(this))
    this.listen(document, "click", this._onOutsideClick.bind(this))
    this.listen(this, "click", this._onHostClick.bind(this))
    this.listen(this, "invalid", this._onInvalid.bind(this))

    this.onTeardown(() => {
      this._cancelDebounce()
    })
    return
  }

  onConnected() {
    /* Labels outside the shadow root can only be resolved once connected. */
    this._syncAccessibleName()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "value") {
      this._applyValueAttribute(newValue)
    }
    if (name === "name") {
      /* The submitted entry name follows the attribute (default "q"). */
      this._setFormValue(this._value)
    }

    if (this._input === undefined || this._input === null) {
      return
    }

    if (name === "loading") {
      if (newValue !== null) {
        this._suggestMode = true
      }
      this._renderPopup()
      /* Said once when loading starts, while the user is in the field. */
      if (newValue !== null && oldValue === null && this.shadowRoot.activeElement === this._input) {
        announce(t("mj.searchInput.loadingSuggestions"))
      }
    }
    this._syncAll()
    return
  }

  /* The control is disabled by its own attribute or by a disabled fieldset. */
  _isDisabled() {
    const disabled = this.hasAttribute("disabled") === true || this._formDisabled === true
    return disabled
  }

  /*
   * Submit under the `name` attribute, or under "q" when the host has none
   * (searchinput.md: the default field name is "q").
   */
  _setFormValue(value) {
    super._setFormValue(value)

    const name = this.getAttribute("name") || ""
    if (name.length === 0 && this._internals !== null && this._internals !== undefined) {
      const entries = new FormData()
      entries.append(DEFAULT_NAME, value)
      this._internals.setFormValue(entries)
    }
    return
  }

  _syncAll() {
    const placeholder = this.getAttribute("placeholder")
    const helpText = this.getAttribute("help-text") || ""
    const submitLabel = this.getAttribute("submit-label") || ""
    const maxlength = this.getAttribute("maxlength")
    const autocomplete = this.getAttribute("autocomplete") || "off"
    const disabled = this._isDisabled()
    const readonly = this.hasAttribute("readonly")
    const required = this.hasAttribute("required")
    const showSubmit = this.hasAttribute("show-submit-button")

    this._input.placeholder = placeholder !== null ? placeholder : t("core.search")
    this._input.autocomplete = autocomplete
    this._input.disabled = disabled
    this._input.readOnly = readonly
    this._input.required = required
    this._input.setAttribute("aria-required", required === true ? "true" : "false")
    if (maxlength !== null) {
      this._input.setAttribute("maxlength", maxlength)
    } else {
      this._input.removeAttribute("maxlength")
    }

    this._fieldEl.toggleAttribute("data-disabled", disabled === true)

    this._helpEl.textContent = helpText

    this._submitBtn.hidden = showSubmit === false
    this._submitBtn.disabled = disabled
    this._submitBtn.setAttribute("aria-label", submitLabel.length > 0 ? submitLabel : t("core.search"))
    this._clearBtn.disabled = disabled

    this._syncAccessibleName()
    this._syncComboboxRole()
    this._updateClearButton()

    /* required / maxlength / error-message all feed validity. */
    this._refreshValidity()
    this._renderValidity(false)
    return
  }

  _updateDescribedBy() {
    const ids = []
    if (this._helpEl.textContent.length > 0) {
      ids.push(this._helpId)
    }
    if (this._errorEl.hasAttribute("data-visible") === true) {
      ids.push(this._errorId)
    }
    if (ids.length > 0) {
      this._input.setAttribute("aria-describedby", ids.join(" "))
    } else {
      this._input.removeAttribute("aria-describedby")
    }
    return
  }

  /*
   * Show or hide the inline error from the current validity. `error-message`
   * replaces the built-in text but never makes a valid field look invalid.
   * `announce` is true when the user (leaving the component) or a submit
   * attempt triggered the check; only then is `mj-invalid` emitted.
   */
  _renderValidity(announce) {
    if (this._errorEl === undefined || this._errorEl === null) {
      return
    }
    const message = this.validationMessage
    const invalid = message.length > 0 && this._showErrors === true

    if (invalid === true) {
      const override = this.getAttribute("error-message") || ""
      const displayMessage = override.length > 0 ? override : message
      this._errorEl.textContent = displayMessage
      this._errorEl.setAttribute("data-visible", "")
      this._fieldEl.setAttribute("data-invalid", "")
      this._input.setAttribute("aria-invalid", "true")
      this._updateDescribedBy()
      if (announce === true) {
        this.emit("mj-invalid", { validationMessage: displayMessage })
      }
    } else {
      this._errorEl.textContent = ""
      this._errorEl.removeAttribute("data-visible")
      this._fieldEl.removeAttribute("data-invalid")
      this._input.setAttribute("aria-invalid", "false")
      this._updateDescribedBy()
    }
    return
  }

  /*
   * Name the landmark and the input. `label` (default "Search") is the
   * built-in name; a name given to the host from outside takes its place.
   */
  _syncAccessibleName() {
    if (this._input === undefined || this._input === null) {
      return
    }

    const label = this.getAttribute("label") || ""
    const hostLabel = resolveHostLabel(this, this._internals)
    const explicit = this.hasAttribute("aria-label") === true || this.hasAttribute("aria-labelledby") === true

    let name = label.length > 0 ? label : t("core.search")
    if (hostLabel.length > 0 && (explicit === true || label.length === 0)) {
      name = hostLabel
    }

    this._searchEl.setAttribute("aria-label", name)
    this._input.setAttribute("aria-label", name)
    return
  }

  /*
   * `aria-expanded`, `aria-controls` and `aria-activedescendant` are only
   * valid on a combobox, so they are applied together with that role and
   * only once suggestions are in use.
   */
  _syncComboboxRole() {
    if (this._suggestMode === true) {
      const open = this._popup.hidden === false
      this._input.setAttribute("role", "combobox")
      this._input.setAttribute("aria-haspopup", "listbox")
      this._input.setAttribute("aria-autocomplete", "list")
      this._input.setAttribute("aria-controls", this._popupId)
      this._input.setAttribute("aria-expanded", open === true ? "true" : "false")
    } else {
      this._input.setAttribute("role", "searchbox")
      this._input.removeAttribute("aria-haspopup")
      this._input.removeAttribute("aria-autocomplete")
      this._input.removeAttribute("aria-controls")
      this._input.removeAttribute("aria-expanded")
      this._input.removeAttribute("aria-activedescendant")
    }
    return
  }

  _updateClearButton() {
    const noClear = this.hasAttribute("no-clear-button")
    const readonly = this.hasAttribute("readonly")
    const disabled = this._isDisabled()
    const hasValue = this._input.value.length > 0
    const showClear = noClear === false && hasValue === true && readonly === false && disabled === false
    this._clearBtn.hidden = showClear === false
    return
  }

  /*
   * Apply the `value` attribute. The attribute is delivered once before the
   * first render and again after it (see MjElement), so the text already
   * applied is remembered and a repeat delivery does not overwrite what the
   * user or a script has entered since.
   */
  _applyValueAttribute(attributeValue) {
    if (attributeValue === this._appliedValueAttribute) {
      return
    }
    this._appliedValueAttribute = attributeValue
    this._applyValue(attributeValue)
    return
  }

  /* The single entry point for every programmatic value change. */
  _applyValue(next) {
    const text = next === null || next === undefined ? "" : String(next)

    this._setFormValue(text)

    if (this._input !== undefined && this._input !== null) {
      if (this._input.value !== text) {
        this._input.value = text
      }
      this._updateClearButton()
      this._renderValidity(false)
    }
    return
  }

  _cancelDebounce() {
    if (this._debounceTimer !== null) {
      clearTimeout(this._debounceTimer)
      this._debounceTimer = null
    }
    return
  }

  /*
   * The query is no longer long enough for suggestions: drop the pending
   * debounce, close the popup and tell the host (once) that the query is
   * empty so it can discard its results.
   */
  _resetQuery() {
    this._cancelDebounce()
    this._closePopup()
    if (this._lastQuery.length > 0) {
      this._lastQuery = ""
      this.emit("mj-query-change", { value: "" })
    }
    return
  }

  _onInput(event) {
    const text = this._input.value
    this._setFormValue(text)
    this._updateClearButton()
    this._renderValidity(false)

    this.emit("mj-input", { value: text })

    const debounce = parseInt(this.getAttribute("debounce") || "300", 10)
    const minChars = parseInt(this.getAttribute("min-chars") || "1", 10)
    const delay = Number.isNaN(debounce) === true || debounce < 0 ? 300 : debounce
    const threshold = Number.isNaN(minChars) === true ? 1 : minChars

    if (text.length < threshold) {
      this._resetQuery()
      return
    }

    this._cancelDebounce()
    this._debounceTimer = setTimeout(() => {
      this._debounceTimer = null
      this._lastQuery = text
      this.emit("mj-query-change", { value: text })
    }, delay)
    return
  }

  _onKeydown(event) {
    const key = event.key

    if (key === "ArrowDown") {
      event.preventDefault()
      this._moveActive(1)
    } else if (key === "ArrowUp") {
      event.preventDefault()
      this._moveActive(-1)
    } else if (key === "Enter") {
      const popupOpen = this._popup.hidden === false
      if (popupOpen === true && this._activeIndex >= 0 && this._activeIndex < this._rows.length) {
        event.preventDefault()
        this._selectSuggestion(this._rows[this._activeIndex])
      } else {
        this._closePopup()
        this._submitSearch()
      }
    } else if (key === "Escape") {
      if (this._popup.hidden === false) {
        /* Consumed here: an enclosing dialog must not close as well. */
        event.preventDefault()
        event.stopPropagation()
        this._closePopup()
      }
    }
    return
  }

  _onFocus(event) {
    /* A label placed after the field in the document exists by now. */
    this._syncAccessibleName()
    return
  }

  /*
   * Focus left the component (Tab, click away): close the popup and show
   * what is wrong with the value, as the other text controls do on blur.
   */
  _onFocusout(event) {
    const next = event.relatedTarget
    const staysInside = next !== null && next !== undefined && this.shadowRoot.contains(next) === true
    if (staysInside === false) {
      this._closePopup()
      this._showErrors = true
      this._refreshValidity()
      this._renderValidity(true)
    }
    return
  }

  /* A failed checkValidity() / reportValidity() / form submit. */
  _onInvalid(event) {
    this._showErrors = true
    this._renderValidity(true)
    return
  }

  /* Keep focus in the input while a suggestion is being clicked. */
  _onPopupMousedown(event) {
    event.preventDefault()
    return
  }

  _onPopupClick(event) {
    const option = event.target.closest(".option")
    if (option !== null) {
      const index = parseInt(option.getAttribute("data-index"), 10)
      if (index >= 0 && index < this._rows.length) {
        this._selectSuggestion(this._rows[index])
      }
    }
    return
  }

  /*
   * Activating an associated <label> clicks the host; move focus to the
   * input as a native control would.
   */
  _onHostClick(event) {
    const path = event.composedPath()
    if (path.length > 0 && path[0] === this && this._isDisabled() === false) {
      this._input.focus()
    }
    return
  }

  _onClear(event) {
    const previous = this._input.value
    this._input.value = ""
    this._setFormValue("")
    this._updateClearButton()
    this._renderValidity(false)
    this._resetQuery()
    this.emit("mj-clear", { previousValue: previous })
    this.emit("mj-input", { value: "" })
    this._input.focus()
    return
  }

  _onSubmit(event) {
    if (this._isDisabled() === true) {
      return
    }
    this._closePopup()
    this._submitSearch()
    return
  }

  /*
   * The one submit path (Enter, submit button, suggestion pick): a cancelable
   * `mj-search`, then a form submit unless a listener cancelled it.
   */
  _submitSearch() {
    this._cancelDebounce()
    const notCanceled = this.emit("mj-search", { value: this._value }, { cancelable: true })
    if (notCanceled === true) {
      const form = this.form
      if (form !== null && form !== undefined && typeof form.requestSubmit === "function") {
        form.requestSubmit()
      }
    }
    return
  }

  _onOutsideClick(event) {
    if (this.contains(event.target) === false) {
      this._closePopup()
    }
    return
  }

  _moveActive(direction) {
    const count = this._rows.length
    if (count === 0 || this.hasAttribute("loading") === true) {
      return
    }

    let nextIndex = this._activeIndex + direction
    if (this._popup.hidden === true) {
      /* Arrow keys re-open a dismissed popup on its first or last row. */
      nextIndex = direction > 0 ? 0 : count - 1
    }
    if (nextIndex < 0) {
      nextIndex = count - 1
    }
    if (nextIndex >= count) {
      nextIndex = 0
    }

    this._activeIndex = nextIndex
    this._renderPopup()
    return
  }

  _selectSuggestion(row) {
    this._input.value = row.value
    this._setFormValue(row.value)
    this._updateClearButton()
    this._renderValidity(false)
    this._closePopup()
    this.emit("mj-suggestion-select", { suggestion: row.source })
    this._input.focus()
    this._submitSearch()
    return
  }

  _closePopup() {
    this._activeIndex = -1
    if (this._popup === undefined || this._popup === null) {
      return
    }
    this._popup.hidden = true
    this._popup.removeAttribute("aria-busy")
    this._input.removeAttribute("aria-activedescendant")
    this._syncComboboxRole()
    return
  }

  _renderPopup() {
    if (this._popup === undefined || this._popup === null) {
      return
    }

    const loading = this.hasAttribute("loading")
    this._popup.textContent = ""
    this._input.removeAttribute("aria-activedescendant")

    if (loading === true) {
      this._suggestMode = true
      const message = document.createElement("div")
      message.className = "loading-msg"
      message.setAttribute("part", "loading")
      /*
       * A listbox owns only options: the message is not one of its items.
       * It is announced through the shared live region when loading starts.
       */
      message.setAttribute("role", "none")
      message.textContent = t("mj.searchInput.loadingSuggestions")
      this._popup.appendChild(message)
      this._popup.setAttribute("aria-busy", "true")
      this._popup.hidden = false
      this._syncComboboxRole()
      return
    }

    this._popup.removeAttribute("aria-busy")

    if (this._rows.length === 0) {
      this._closePopup()
      return
    }

    for (let index = 0; index < this._rows.length; index = index + 1) {
      const row = this._rows[index]
      const active = index === this._activeIndex

      const option = document.createElement("div")
      option.className = "option"
      option.setAttribute("part", "option")
      option.setAttribute("role", "option")
      option.setAttribute("id", `${this._popupId}-opt-${index}`)
      option.setAttribute("data-index", String(index))
      option.setAttribute("aria-selected", active === true ? "true" : "false")
      option.textContent = row.label

      if (row.description.length > 0) {
        const description = document.createElement("span")
        description.className = "option-description"
        description.textContent = row.description
        option.appendChild(description)
      }

      if (active === true) {
        option.setAttribute("data-active", "")
        this._input.setAttribute("aria-activedescendant", option.id)
      }
      this._popup.appendChild(option)
    }

    this._popup.hidden = false
    this._syncComboboxRole()

    const activeOption = this._popup.querySelector("[data-active]")
    if (activeOption !== null && typeof activeOption.scrollIntoView === "function") {
      activeOption.scrollIntoView({ block: "nearest" })
    }
    return
  }

  _customValidity() {
    let message = ""
    const text = this._value === null || this._value === undefined ? "" : String(this._value)
    const maxlength = parseInt(this.getAttribute("maxlength") || "", 10)

    if (Number.isNaN(maxlength) === false && text.length > maxlength) {
      message = t("mj.searchInput.tooLong", { count: maxlength, current: text.length })
    }
    return message
  }

  _validationAnchor() {
    const anchor = this._input !== undefined ? this._input : null
    return anchor
  }

  onFormReset(initial) {
    this._showErrors = false
    this._applyValue(initial)
    this._cancelDebounce()
    this._lastQuery = ""
    this._closePopup()
    return
  }

  onFormRestore(state) {
    let restored = ""
    if (typeof state === "string") {
      restored = state
    } else if (state !== null && state !== undefined && typeof state.get === "function") {
      /* Without a `name` the submitted state is a FormData entry named "q". */
      const entry = state.get(DEFAULT_NAME)
      restored = typeof entry === "string" ? entry : ""
    }
    this._applyValue(restored)
    return
  }

  onFormDisabled(disabled) {
    this._formDisabled = disabled === true
    if (this._input !== undefined && this._input !== null) {
      this._syncAll()
    }
    return
  }

  get value() {
    return this._value
  }

  set value(next) {
    this._applyValue(next)
    return
  }

  reportValidity() {
    this._refreshValidity()
    const valid = super.reportValidity()
    return valid
  }

  get suggestions() {
    return this._suggestions
  }

  set suggestions(items) {
    this._suggestions = Array.isArray(items) === true ? items : []
    this._rows = normalizeSuggestions(this._suggestions)
    this._activeIndex = -1
    if (this._rows.length > 0) {
      this._suggestMode = true
    }
    /* Before the first render the rows are drawn by afterRender(). */
    this._renderPopup()
    return
  }

  get loading() {
    return this.hasAttribute("loading")
  }

  set loading(value) {
    this.reflectBoolean("loading", value === true)
    return
  }

  focus(options) {
    if (this._input !== undefined && this._input !== null) {
      this._input.focus(options)
    }
    return
  }
}
