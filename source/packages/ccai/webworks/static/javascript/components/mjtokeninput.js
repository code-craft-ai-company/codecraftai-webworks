/*
 * mjtokeninput.js
 *
 * <mj-token-input> -- multi-value chip/tag input with optional suggestion
 * popup, delimiter-based token commit, and form participation.
 *
 * State model: `this._tokens` is the single source of truth. Each token is
 * submitted as its own FormData entry under `name`; `this._value` (the
 * `value` property) is the comma-joined list. The `value` attribute holds
 * the initial, comma-separated tokens and is what a form reset returns to.
 * Chips are rebuilt from `this._tokens` on every render.
 *
 * Keyboard: the chips form a listbox. Arrow Left (or Backspace) in the empty
 * input moves focus to the last chip; Arrow Left / Right walk the chips;
 * Delete or Backspace removes the focused chip and returns focus to the
 * input.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";

const STYLES = `
:host {
  display: block;
  font-family: var(--mj-font-sans);
  font-size: var(--mj-font-size-md);
}

.label {
  display: block;
  margin-bottom: var(--mj-space-1);
  font-size: var(--mj-font-size-sm);
  font-weight: var(--mj-font-weight-medium);
  color: var(--mj-text);
}
.label:empty { display: none; }
.label[data-required]::after {
  content: " *";
  color: var(--mj-color-danger);
}

.container {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--mj-space-1);
  min-height: var(--mj-control-height-md);
  padding: var(--mj-space-1) var(--mj-space-2);
  background: var(--mj-surface);
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-md);
  cursor: text;
  transition: border-color var(--mj-motion-fast) var(--mj-motion-ease);
}
.container:focus-within {
  border-color: var(--mj-accent);
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.container[data-invalid] { border-color: var(--mj-color-danger); }

.chips {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--mj-space-1);
  min-width: 0;
  max-width: 100%;
}
.chips:empty { display: none; }

.chip {
  display: inline-flex;
  align-items: center;
  gap: var(--mj-space-1);
  padding: var(--mj-space-1) var(--mj-space-2);
  background: var(--mj-bg-muted);
  border-radius: var(--mj-radius-pill);
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
  max-width: 200px;
  outline: none;
}
.chip[aria-selected="true"] {
  background: var(--mj-accent);
  color: var(--mj-text-on-accent);
}
.chip:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.chip[data-flash] { animation: mj-token-flash 0.6s ease-in-out; }
@keyframes mj-token-flash {
  0%, 100% { background: var(--mj-bg-muted); }
  50% { background: var(--mj-color-warning-surface); }
}
@media (prefers-reduced-motion: reduce) {
  .chip[data-flash] { animation: none; outline: 2px solid var(--mj-color-warning); }
}

.chip-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chip-remove {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1rem;
  height: 1rem;
  padding: 0;
  background: transparent;
  border: none;
  cursor: pointer;
  color: inherit;
  border-radius: var(--mj-radius-circle);
  font-size: 0.75rem;
  line-height: 1;
  flex-shrink: 0;
}
.chip-remove:hover { background: color-mix(in srgb, currentColor 15%, transparent); }

.chip-remove[hidden] { display: none; }

input {
  flex: 1;
  min-width: 120px;
  height: 1.75rem;
  padding: 0 var(--mj-space-1);
  font: inherit;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
  background: transparent;
  border: none;
  outline: none;
}
input[hidden] { display: none; }
input::placeholder { color: var(--mj-text-muted); }

.popup {
  position: absolute;
  inset-inline-start: 0;
  inset-inline-end: 0;
  top: calc(100% + var(--mj-space-1));
  background: var(--mj-surface-raised);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-md);
  box-shadow: var(--mj-elevation-2);
  max-height: 250px;
  overflow-y: auto;
  z-index: var(--mj-layer-popover);
}
.popup[hidden] { display: none; }

.option {
  padding: var(--mj-space-2) var(--mj-space-3);
  cursor: pointer;
  font-size: var(--mj-font-size-sm);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.option:hover, .option[data-active] { background: var(--mj-bg-muted); }

.loading-msg {
  padding: var(--mj-space-3);
  color: var(--mj-text-muted);
  font-size: var(--mj-font-size-sm);
}

.container-wrap { position: relative; }

.max-msg {
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
  padding: var(--mj-space-1);
}
.max-msg[hidden] { display: none; }

.below { margin-top: var(--mj-space-1); }
.help { font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }
.help:empty { display: none; }
.error { font-size: var(--mj-font-size-sm); color: var(--mj-color-danger); display: none; }
.error[data-visible] { display: block; }

.announce, .chip-hint { position: absolute; width:1px; height:1px; overflow:hidden; clip:rect(0,0,0,0); }

:host([disabled]) .container, .container[data-disabled] { opacity: 0.55; pointer-events: none; }
`;

const DEFAULT_DELIMITERS = ",\n";

/* How long a duplicate chip stays highlighted, in milliseconds. */
const FLASH_DURATION_MS = 700;

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
 * Accept `{ value, label }` objects and plain strings; anything else is
 * dropped. The original item is kept for event payloads.
 */
function normalizeSuggestions(items) {
  const normalized = []

  if (Array.isArray(items) === true) {
    for (let index = 0; index < items.length; index = index + 1) {
      const item = items[index]
      if (typeof item === "string" || typeof item === "number") {
        const text = String(item)
        normalized.push({ value: text, label: text, source: { value: text, label: text } })
      } else if (item !== null && typeof item === "object") {
        const value = item.value !== null && item.value !== undefined ? String(item.value) : ""
        const label = item.label !== null && item.label !== undefined && String(item.label).length > 0
          ? String(item.label)
          : value
        normalized.push({ value: value, label: label, source: item })
      }
    }
  }

  return normalized
}

/* Split `text` on every character of `delimiters` and on line breaks. */
function splitOnDelimiters(text, delimiters) {
  let pieces = [text]
  const separators = `${delimiters}\n\r`

  for (let index = 0; index < separators.length; index = index + 1) {
    const separator = separators[index]
    const next = []
    for (let pieceIndex = 0; pieceIndex < pieces.length; pieceIndex = pieceIndex + 1) {
      const parts = pieces[pieceIndex].split(separator)
      for (let partIndex = 0; partIndex < parts.length; partIndex = partIndex + 1) {
        next.push(parts[partIndex])
      }
    }
    pieces = next
  }

  return pieces
}

/* Normalize anything assigned to `tokens` / `value` into a string array. */
function toTokenList(source) {
  const list = []

  if (Array.isArray(source) === true) {
    for (let index = 0; index < source.length; index = index + 1) {
      const item = source[index]
      if (item !== null && item !== undefined && String(item).length > 0) {
        list.push(String(item))
      }
    }
  } else if (typeof source === "string" && source.length > 0) {
    const parts = source.split(",")
    for (let index = 0; index < parts.length; index = index + 1) {
      const trimmed = parts[index].trim()
      if (trimmed.length > 0) {
        list.push(trimmed)
      }
    }
  }

  return list
}

export class MjTokenInput extends FormControlMixin(MjElement) {
  static tagName = "mj-token-input";
  static styles = STYLES;
  static watched = [
    "label", "placeholder", "help-text", "error-message", "value", "name",
    "delimiters", "max-tokens", "allow-duplicates", "required",
    "disabled", "readonly", "trim", "loading", "debounce", "min-chars",
    "constrained", "commit-on-blur", "aria-label", "aria-labelledby"
  ];

  constructor() {
    super()
    this._initFormControl()

    this._tokens = []

    /* Suggestions as given by the host, and the normalized rows drawn. */
    this._suggestions = []
    this._rows = []
    this._activeIndex = -1

    /* True once the host has used suggestions; switches the ARIA pattern. */
    this._suggestMode = false

    this._debounceTimer = null
    this._flashTimer = null

    /* The query most recently announced through mj-query-change. */
    this._lastQuery = ""

    this._validateToken = null

    /* Message from a rejected token; cleared by the next edit or add. */
    this._tokenError = ""

    /* The `value` attribute text most recently applied to the control. */
    this._appliedValueAttribute = null

    /* True while an ancestor <fieldset disabled> disables the control. */
    this._formDisabled = false

    /* Errors are shown once the user has left the field or a submit failed. */
    this._showErrors = false

    this._groupId = nextId("mjti-group")
    this._inputId = nextId("mjti-input")
    this._listId = nextId("mjti-list")
    this._popupId = nextId("mjti-popup")
    this._helpId = nextId("mjti-help")
    this._errorId = nextId("mjti-error")
    this._hintId = nextId("mjti-hint")
    this._announceId = nextId("mjti-announce")
  }

  render() {
    const markup = html`
      <label class="label" part="label" for="${this._inputId}"></label>
      <div class="container-wrap">
        <div class="container" part="container" role="group" id="${this._groupId}">
          <div class="chips" part="tokens" role="listbox" aria-orientation="horizontal"
            id="${this._listId}" aria-describedby="${this._hintId}"></div>
          <input part="input" type="text" id="${this._inputId}" autocomplete="off" />
          <span class="max-msg" role="status" hidden></span>
        </div>
        <div class="popup" part="popup" id="${this._popupId}" role="listbox" hidden></div>
      </div>
      <span class="chip-hint" id="${this._hintId}">Press Delete or Backspace to remove the focused tag.</span>
      <span class="announce" id="${this._announceId}" aria-live="polite" role="status"></span>
      <div class="below">
        <span class="help" part="help" id="${this._helpId}"></span>
        <span class="error" part="error" id="${this._errorId}" role="alert"></span>
      </div>
    `
    return markup
  }

  afterRender() {
    this._labelEl = this.$(".label")
    this._container = this.$(".container")
    this._chipsEl = this.$(".chips")
    this._input = this.$("input")
    this._popup = this.$(".popup")
    this._maxMsg = this.$(".max-msg")
    this._helpEl = this.$(".help")
    this._errorEl = this.$(".error")
    this._announceEl = this.$(".announce")

    /* The shadow DOM is new: rebuild it from the stored state. */
    this._refreshFormValue()
    this._renderTokens()
    this._syncAll()
    this._renderPopup()

    this.listen(this._input, "keydown", this._onKeydown.bind(this))
    this.listen(this._input, "input", this._onInput.bind(this))
    this.listen(this._input, "paste", this._onPaste.bind(this))
    this.listen(this._input, "focus", this._onFocus.bind(this))
    this.listen(this._chipsEl, "keydown", this._onChipKeydown.bind(this))
    this.listen(this._chipsEl, "click", this._onChipClick.bind(this))
    this.listen(this._chipsEl, "focusin", this._onChipFocusChange.bind(this))
    this.listen(this._chipsEl, "focusout", this._onChipFocusChange.bind(this))
    this.listen(this._container, "click", this._onContainerClick.bind(this))
    this.listen(this._popup, "mousedown", this._onPopupMousedown.bind(this))
    this.listen(this._popup, "click", this._onPopupClick.bind(this))
    this.listen(this.shadowRoot, "focusout", this._onFocusout.bind(this))
    this.listen(document, "click", this._onOutsideClick.bind(this))
    this.listen(this, "invalid", this._onInvalid.bind(this))
    this.listen(this, "click", this._onHostClick.bind(this))

    this.onTeardown(() => {
      this._cancelDebounce()
      if (this._flashTimer !== null) {
        clearTimeout(this._flashTimer)
        this._flashTimer = null
      }
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
      /* Token entries are submitted under the current name. */
      this._refreshFormValue()
    }

    if (this._input === undefined || this._input === null) {
      return
    }

    if (name === "loading") {
      this._renderPopup()
    }
    if (name === "disabled" || name === "readonly") {
      this._renderTokens()
    }
    this._syncAll()
    return
  }

  /* ----- state helpers ----- */

  /* The control is disabled by its own attribute or by a disabled fieldset. */
  _isDisabled() {
    const disabled = this.hasAttribute("disabled") === true || this._formDisabled === true
    return disabled
  }

  /* True when tokens may be added or removed by the user. */
  _isEditable() {
    const editable = this._isDisabled() === false && this.hasAttribute("readonly") === false
    return editable
  }

  _getMaxTokens() {
    const max = parseInt(this.getAttribute("max-tokens") || "", 10)
    return max
  }

  _isAtMax() {
    const max = this._getMaxTokens()
    const atMax = Number.isNaN(max) === false && this._tokens.length >= max
    return atMax
  }

  _getDelimiters() {
    const attribute = this.getAttribute("delimiters")
    const delimiters = attribute !== null && attribute.length > 0 ? attribute : DEFAULT_DELIMITERS
    return delimiters
  }

  _announce(message) {
    if (this._announceEl !== undefined && this._announceEl !== null) {
      this._announceEl.textContent = message
    }
    return
  }

  /* ----- sync ----- */

  _syncAll() {
    const label = this.getAttribute("label") || ""
    const placeholder = this.getAttribute("placeholder") || ""
    const helpText = this.getAttribute("help-text") || ""
    const disabled = this._isDisabled()
    const readonly = this.hasAttribute("readonly")
    const required = this.hasAttribute("required")
    const atMax = this._isAtMax()

    this._labelEl.textContent = label
    this._labelEl.toggleAttribute("data-required", required === true)
    this._container.toggleAttribute("data-disabled", disabled === true)
    /* The chips are not operable while disabled: say so on their listbox. */
    if (disabled === true) {
      this._chipsEl.setAttribute("aria-disabled", "true")
    } else {
      this._chipsEl.removeAttribute("aria-disabled")
    }

    this._input.placeholder = placeholder
    this._input.disabled = disabled
    this._input.setAttribute("aria-required", required === true ? "true" : "false")
    this._helpEl.textContent = helpText

    /*
     * At the limit (and when read-only) there is nothing to type. If the
     * input is about to disappear while it has focus, focus moves to the
     * last chip first so the keyboard user is not dropped to <body>.
     */
    const hideInput = atMax === true || readonly === true
    const inputHadFocus = this.shadowRoot.activeElement === this._input
    this._input.hidden = hideInput
    this._maxMsg.hidden = atMax === false
    const maxMessage = atMax === true ? t("mj.tokenInput.maxReached", { count: this._getMaxTokens() }) : ""
    if (this._maxMsg.textContent !== maxMessage) {
      this._maxMsg.textContent = maxMessage
    }

    this._syncChipTabStops()
    if (hideInput === true && inputHadFocus === true) {
      this._focusChip(this._tokens.length - 1)
    }

    this._syncAccessibleName()
    this._syncComboboxRole()

    /* required / error-message feed validity. */
    this._refreshValidity()
    this._renderValidity(false)
    return
  }

  /*
   * Name the group, the chip list and the input. The visible <label for>
   * names the input when `label` is set; otherwise a name given to the host
   * from outside is used, and "Add tag" is the last resort.
   */
  _syncAccessibleName() {
    if (this._input === undefined || this._input === null) {
      return
    }

    const label = this.getAttribute("label") || ""
    const hostLabel = resolveHostLabel(this, this._internals)
    const explicit = this.hasAttribute("aria-label") === true || this.hasAttribute("aria-labelledby") === true

    let name = label
    if (hostLabel.length > 0 && (explicit === true || label.length === 0)) {
      name = hostLabel
    }

    if (name.length > 0 && name === label) {
      /* Named by the built-in <label for>. */
      this._input.removeAttribute("aria-label")
    } else if (name.length > 0) {
      this._input.setAttribute("aria-label", name)
    } else {
      this._input.setAttribute("aria-label", t("mj.tokenInput.addTag"))
    }

    const groupName = name.length > 0 ? name : t("mj.tokenInput.groupLabel")
    this._container.setAttribute("aria-label", groupName)
    this._chipsEl.setAttribute("aria-label", t("mj.tokenInput.selectedTags", { name: groupName }))
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
      this._input.removeAttribute("role")
      this._input.removeAttribute("aria-haspopup")
      this._input.removeAttribute("aria-autocomplete")
      this._input.removeAttribute("aria-controls")
      this._input.removeAttribute("aria-expanded")
      this._input.removeAttribute("aria-activedescendant")
    }
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

  /* ----- value / form ----- */

  /*
   * Apply the `value` attribute (comma-separated initial tokens). The
   * attribute is delivered once before the first render and again after it
   * (see MjElement), so the text already applied is remembered and a repeat
   * delivery does not overwrite what the user has entered since.
   */
  _applyValueAttribute(attributeValue) {
    if (attributeValue === this._appliedValueAttribute) {
      return
    }
    this._appliedValueAttribute = attributeValue
    this._applyTokens(toTokenList(attributeValue === null ? "" : attributeValue))
    return
  }

  /* The single entry point for every programmatic change of the tokens. */
  _applyTokens(list) {
    this._tokens = list
    this._tokenError = ""
    this._refreshFormValue()

    if (this._container !== undefined && this._container !== null) {
      this._renderTokens()
      this._syncAll()
    }
    return
  }

  /*
   * Publish the tokens to the form: one entry per token under `name` (none
   * when the host has no name), with the token list as restorable state.
   */
  _refreshFormValue() {
    this._value = this._tokens.join(",")

    if (this._internals !== null && this._internals !== undefined) {
      const name = this.getAttribute("name") || ""
      if (name.length > 0) {
        const entries = new FormData()
        for (let index = 0; index < this._tokens.length; index = index + 1) {
          entries.append(name, this._tokens[index])
        }
        this._internals.setFormValue(entries, JSON.stringify(this._tokens))
      } else {
        this._internals.setFormValue(null, JSON.stringify(this._tokens))
      }
    }

    this._refreshValidity()
    return
  }

  /*
   * `required` means at least one token. The mixin's generic check looks at
   * a string value, so validity is computed here from the token list.
   */
  _refreshValidity() {
    if (this._internals === null || this._internals === undefined) {
      return
    }

    const required = this.hasAttribute("required")
    const anchor = this._validationAnchor()

    if (required === true && this._tokens.length === 0) {
      const message = this.getAttribute("required-message") || t("mj.tokenInput.required")
      if (anchor !== null && anchor !== undefined) {
        this._internals.setValidity({ valueMissing: true }, message, anchor)
      } else {
        this._internals.setValidity({ valueMissing: true }, message)
      }
    } else {
      this._internals.setValidity({})
    }
    return
  }

  _validationAnchor() {
    /* Only a visible input can take the browser's validation bubble. */
    let anchor = null
    if (this._input !== undefined && this._input !== null && this._input.hidden === false) {
      anchor = this._input
    }
    return anchor
  }

  /* ----- adding / removing ----- */

  /*
   * Try to add one token. Returns true when the token was added. A value
   * rejected by `validateToken` (or by `constrained`) stays in the input
   * with its message shown, so the user can correct it.
   */
  _tryAddToken(rawValue) {
    const trim = this.getAttribute("trim") !== "false"
    const value = trim === true ? rawValue.trim() : rawValue
    let added = false

    if (value.length === 0 || this._isEditable() === false || this._isAtMax() === true) {
      return added
    }

    const allowDuplicates = this.hasAttribute("allow-duplicates")
    const duplicateIndex = this._tokens.indexOf(value)
    if (allowDuplicates === false && duplicateIndex >= 0) {
      this._announce(t("mj.tokenInput.duplicate", { value: value }))
      this._flashChip(duplicateIndex)
      return added
    }

    let rejection = ""
    if (this.hasAttribute("constrained") === true && this._isSuggestedValue(value) === false) {
      rejection = t("mj.tokenInput.notInList")
    } else if (this._validateToken !== null) {
      const verdict = this._validateToken(value)
      if (verdict !== true) {
        rejection = typeof verdict === "string" && verdict.length > 0 ? verdict : t("mj.tokenInput.invalidValue")
      }
    }

    if (rejection.length > 0) {
      this._tokenError = rejection
      this._renderValidity(false)
      this.emit("mj-invalid", { validationMessage: rejection, value: value })
      return added
    }

    const notCanceled = this.emit("mj-token-add", { value: value, tokens: [...this._tokens] }, { cancelable: true })
    if (notCanceled === false) {
      return added
    }

    this._tokens.push(value)
    this._tokenError = ""
    this._refreshFormValue()
    this._renderTokens()
    this._syncAll()
    this.emit("mj-change", { tokens: [...this._tokens] })
    this._announce(t("mj.tokenInput.added", { value: value }))
    added = true
    return added
  }

  _isSuggestedValue(value) {
    let found = false
    for (let index = 0; index < this._rows.length; index = index + 1) {
      if (this._rows[index].value === value) {
        found = true
      }
    }
    return found
  }

  /*
   * Commit the text in the input as a token. The text is cleared when it
   * became a token or duplicated one; a rejected value is left in place.
   */
  _commitInputText() {
    const text = this._input.value
    if (text.trim().length === 0) {
      return
    }
    const hadError = this._tokenError.length > 0
    const added = this._tryAddToken(text)
    const rejected = added === false && this._tokenError.length > 0
    if (rejected === false) {
      this._input.value = ""
    } else if (hadError === false) {
      /* Keep the rejected text selected so it is easy to replace. */
      this._input.select()
    }
    return
  }

  /* Remove the token at `index`. Returns true when it was removed. */
  _removeTokenAt(index) {
    let removed = false
    if (index < 0 || index >= this._tokens.length || this._isEditable() === false) {
      return removed
    }

    const value = this._tokens[index]
    const notCanceled = this.emit("mj-token-remove", { value: value, tokens: [...this._tokens] }, { cancelable: true })
    if (notCanceled === false) {
      return removed
    }

    this._tokens.splice(index, 1)
    this._refreshFormValue()
    this._renderTokens()
    this._syncAll()
    this.emit("mj-change", { tokens: [...this._tokens] })
    this._announce(t("mj.tokenInput.removed", { value: value }))
    removed = true
    return removed
  }

  /*
   * After a removal the chips have been rebuilt and the element that had
   * focus is gone: put focus back on the input (visible again once below
   * the limit) or, when read-only hides it, on a remaining chip.
   */
  _restoreFocusAfterRemoval(index) {
    if (this._input.hidden === false && this._input.disabled === false) {
      this._input.focus()
    } else if (this._tokens.length > 0) {
      this._focusChip(Math.min(index, this._tokens.length - 1))
    }
    return
  }

  /* ----- chips ----- */

  _getChips() {
    const chips = Array.from(this._chipsEl.querySelectorAll(".chip"))
    return chips
  }

  _renderTokens() {
    const editable = this._isEditable()
    this._chipsEl.textContent = ""

    for (let index = 0; index < this._tokens.length; index = index + 1) {
      const token = this._tokens[index]

      const chip = document.createElement("div")
      chip.className = "chip"
      chip.setAttribute("part", "token")
      chip.setAttribute("role", "option")
      chip.setAttribute("id", `${this._listId}-chip-${index}`)
      chip.setAttribute("data-index", String(index))
      chip.setAttribute("aria-selected", "false")
      chip.setAttribute("aria-label", token)
      chip.tabIndex = -1
      chip.title = token

      const label = document.createElement("span")
      label.className = "chip-label"
      label.setAttribute("part", "token-label")
      label.textContent = token

      /*
       * The remove control is a pointer affordance only. Keyboard and
       * screen reader users remove the focused chip with Delete /
       * Backspace, as the listbox description says. An option may not
       * contain an interactive element (a button is focusable by click
       * even with tabindex="-1"), so this is a plain hidden-from-AT span;
       * its click is handled by _onChipClick.
       */
      const removeControl = document.createElement("span")
      removeControl.className = "chip-remove"
      removeControl.setAttribute("part", "token-remove")
      removeControl.setAttribute("aria-hidden", "true")
      removeControl.title = t("mj.tokenInput.removeToken", { token: token })
      removeControl.textContent = "×"
      removeControl.hidden = editable === false

      chip.appendChild(label)
      chip.appendChild(removeControl)
      this._chipsEl.appendChild(chip)
    }

    this._syncChipTabStops()
    return
  }

  /*
   * While the input is available it is the component's tab stop and chips
   * are reached with Arrow Left. When it is hidden (limit reached,
   * read-only) the last chip becomes the tab stop instead.
   */
  _syncChipTabStops() {
    const chips = this._getChips()
    const inputAvailable = this._input.hidden === false
    const disabled = this._isDisabled()

    for (let index = 0; index < chips.length; index = index + 1) {
      const isStop = inputAvailable === false && disabled === false && index === chips.length - 1
      chips[index].tabIndex = isStop === true ? 0 : -1
    }
    return
  }

  _focusChip(index) {
    const chips = this._getChips()
    if (index >= 0 && index < chips.length && this._isDisabled() === false) {
      chips[index].focus()
    }
    return
  }

  /* The focused chip is the selected one (pending removal). */
  _onChipFocusChange(event) {
    const chips = this._getChips()
    const focused = this.shadowRoot.activeElement
    for (let index = 0; index < chips.length; index = index + 1) {
      chips[index].setAttribute("aria-selected", chips[index] === focused ? "true" : "false")
    }
    return
  }

  _flashChip(index) {
    const chips = this._getChips()
    if (index < 0 || index >= chips.length) {
      return
    }

    const chip = chips[index]
    chip.setAttribute("data-flash", "")
    if (this._flashTimer !== null) {
      clearTimeout(this._flashTimer)
    }
    this._flashTimer = setTimeout(() => {
      this._flashTimer = null
      chip.removeAttribute("data-flash")
    }, FLASH_DURATION_MS)
    return
  }

  _onChipClick(event) {
    const removeButton = event.target.closest(".chip-remove")
    const chip = event.target.closest(".chip")
    if (chip === null) {
      return
    }

    const index = parseInt(chip.getAttribute("data-index"), 10)
    if (removeButton !== null) {
      event.stopPropagation()
      const removed = this._removeTokenAt(index)
      if (removed === true) {
        this._restoreFocusAfterRemoval(index)
      }
    } else if (this._isDisabled() === false) {
      chip.focus()
    }
    return
  }

  _onChipKeydown(event) {
    const chip = event.target.closest(".chip")
    if (chip === null) {
      return
    }

    const index = parseInt(chip.getAttribute("data-index"), 10)
    const lastIndex = this._tokens.length - 1
    const key = event.key
    const inputAvailable = this._input.hidden === false && this._input.disabled === false

    if (key === "ArrowLeft" || key === "ArrowUp") {
      event.preventDefault()
      this._focusChip(Math.max(0, index - 1))
    } else if (key === "ArrowRight" || key === "ArrowDown") {
      event.preventDefault()
      if (index < lastIndex) {
        this._focusChip(index + 1)
      } else if (inputAvailable === true) {
        this._input.focus()
      }
    } else if (key === "Home") {
      event.preventDefault()
      this._focusChip(0)
    } else if (key === "End") {
      event.preventDefault()
      this._focusChip(lastIndex)
    } else if (key === "Delete" || key === "Backspace") {
      event.preventDefault()
      const removed = this._removeTokenAt(index)
      if (removed === true) {
        this._restoreFocusAfterRemoval(index)
      }
    } else if (key === "Escape") {
      if (inputAvailable === true) {
        event.preventDefault()
        this._input.focus()
      }
    } else if (key.length === 1 && event.ctrlKey === false && event.metaKey === false && event.altKey === false) {
      /* Typing resumes in the input. */
      if (inputAvailable === true) {
        this._input.focus()
      }
    }
    return
  }

  /* ----- input ----- */

  _onContainerClick(event) {
    if (event.target === this._container && this._input.hidden === false) {
      this._input.focus()
    }
    return
  }

  /*
   * Activating an associated <label> clicks the host; move focus to the
   * input as a native control would.
   */
  _onHostClick(event) {
    const path = event.composedPath()
    if (path.length > 0 && path[0] === this && this._isDisabled() === false && this._input.hidden === false) {
      this._input.focus()
    }
    return
  }

  _onFocus(event) {
    /* A label placed after the field in the document exists by now. */
    this._syncAccessibleName()
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
    /* Editing the text dismisses the message from a rejected token. */
    if (this._tokenError.length > 0) {
      this._tokenError = ""
      this._renderValidity(false)
    }

    const text = this._input.value
    this.emit("mj-input", { value: text })

    const delimiters = this._getDelimiters()
    let hasDelimiter = false
    for (let index = 0; index < delimiters.length; index = index + 1) {
      if (text.includes(delimiters[index]) === true) {
        hasDelimiter = true
      }
    }

    if (hasDelimiter === true) {
      /*
       * Everything before the last delimiter is committed. What stays in
       * the input is the text after it, preceded by any piece that was
       * rejected so the user can correct it.
       */
      const pieces = splitOnDelimiters(text, delimiters)
      const kept = []
      for (let index = 0; index < pieces.length - 1; index = index + 1) {
        const piece = pieces[index]
        const added = this._tryAddToken(piece)
        if (added === false && this._tokenError.length > 0 && piece.trim().length > 0) {
          kept.push(piece.trim())
        }
      }
      const remainder = pieces[pieces.length - 1]
      if (remainder.trim().length > 0) {
        kept.push(remainder.trim())
      }
      this._input.value = kept.join(" ")
      this._resetQuery()
      return
    }

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

  /*
   * A pasted list ("alpha, beta" or one value per line) becomes several
   * tokens at once. A paste without any separator is left to the browser.
   */
  _onPaste(event) {
    const text = event.clipboardData !== null && event.clipboardData !== undefined
      ? event.clipboardData.getData("text/plain")
      : ""
    const pieces = splitOnDelimiters(text, this._getDelimiters())
    if (pieces.length < 2 || this._isEditable() === false) {
      return
    }

    event.preventDefault()
    const rejected = []
    for (let index = 0; index < pieces.length; index = index + 1) {
      const piece = pieces[index]
      const added = this._tryAddToken(piece)
      if (added === false && this._tokenError.length > 0 && piece.trim().length > 0) {
        rejected.push(piece.trim())
      }
    }
    if (rejected.length > 0) {
      this._input.value = rejected.join(", ")
    }
    return
  }

  _onKeydown(event) {
    const key = event.key
    const text = this._input.value
    const popupOpen = this._popup.hidden === false

    if (key === "Enter") {
      event.preventDefault()
      if (popupOpen === true && this._activeIndex >= 0 && this._activeIndex < this._rows.length) {
        this._selectSuggestion(this._rows[this._activeIndex])
      } else if (text.length > 0) {
        this._commitInputText()
      }
    } else if (key === "Tab" && text.length > 0) {
      /* Commit and let focus move on; the default action is kept. */
      this._commitInputText()
    } else if ((key === "Backspace" || key === "ArrowLeft") && text.length === 0 && this._tokens.length > 0) {
      event.preventDefault()
      this._focusChip(this._tokens.length - 1)
    } else if (key === "ArrowDown") {
      event.preventDefault()
      this._moveActive(1)
    } else if (key === "ArrowUp") {
      event.preventDefault()
      this._moveActive(-1)
    } else if (key === "Escape") {
      if (popupOpen === true) {
        /* Consumed here: an enclosing dialog must not close as well. */
        event.preventDefault()
        event.stopPropagation()
        this._closePopup()
      }
    }
    return
  }

  /*
   * Focus left the component: close the popup and, unless
   * `commit-on-blur="false"`, turn text still in the input into a token so
   * it is not silently dropped from the submitted value.
   */
  _onFocusout(event) {
    const next = event.relatedTarget
    const staysInside = next !== null && next !== undefined && this.shadowRoot.contains(next) === true
    if (staysInside === true) {
      return
    }

    this._closePopup()
    this._cancelDebounce()

    if (this.getAttribute("commit-on-blur") !== "false" && this._input.value.trim().length > 0) {
      this._commitInputText()
    }

    this._showErrors = true
    this._refreshValidity()
    this._renderValidity(true)
    return
  }

  _onOutsideClick(event) {
    if (this.contains(event.target) === false) {
      this._closePopup()
    }
    return
  }

  /* ----- suggestions popup ----- */

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
    const added = this._tryAddToken(row.value)
    const rejected = added === false && this._tokenError.length > 0
    if (rejected === false) {
      this._input.value = ""
    }
    this._closePopup()
    this.emit("mj-suggestion-select", { suggestion: row.source })
    if (this._input.hidden === false) {
      this._input.focus()
    }
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
      message.setAttribute("role", "status")
      message.textContent = t("mj.tokenInput.loadingSuggestions")
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

  /* ----- validation ----- */

  /* A failed checkValidity() / reportValidity() / form submit. */
  _onInvalid(event) {
    this._showErrors = true
    this._renderValidity(true)
    return
  }

  /*
   * Show or hide the inline error. A rejected-token message is shown at
   * once; the `required` message appears after the user has left the field
   * or a submit failed. `error-message` replaces the constraint text but
   * never makes a valid field look invalid. `announce` is true when the user
   * (leaving the field) or a submit attempt triggered the check; only then
   * is `mj-invalid` emitted for the constraint.
   */
  _renderValidity(announce) {
    const constraintMessage = this.validationMessage
    const constraintInvalid = constraintMessage.length > 0 && this._showErrors === true
    let displayMessage = ""

    if (this._tokenError.length > 0) {
      displayMessage = this._tokenError
    } else if (constraintInvalid === true) {
      const override = this.getAttribute("error-message") || ""
      displayMessage = override.length > 0 ? override : constraintMessage
    }

    if (displayMessage.length > 0) {
      this._errorEl.textContent = displayMessage
      this._errorEl.setAttribute("data-visible", "")
      this._container.setAttribute("data-invalid", "")
      this._input.setAttribute("aria-invalid", "true")
      this._updateDescribedBy()
      if (announce === true && constraintInvalid === true && this._tokenError.length === 0) {
        this.emit("mj-invalid", { validationMessage: displayMessage })
      }
    } else {
      this._errorEl.textContent = ""
      this._errorEl.removeAttribute("data-visible")
      this._container.removeAttribute("data-invalid")
      this._input.setAttribute("aria-invalid", "false")
      this._updateDescribedBy()
    }
    return
  }

  onFormReset(initial) {
    this._showErrors = false
    if (this._input !== undefined && this._input !== null) {
      this._input.value = ""
    }
    this._applyTokens(toTokenList(initial))
    return
  }

  onFormRestore(state) {
    let restored = []
    if (typeof state === "string") {
      try {
        restored = toTokenList(JSON.parse(state))
      } catch (error) {
        restored = toTokenList(state)
      }
    } else if (state !== null && state !== undefined && typeof state.getAll === "function") {
      restored = toTokenList(state.getAll(this.getAttribute("name") || ""))
    }
    this._applyTokens(restored)
    return
  }

  onFormDisabled(disabled) {
    this._formDisabled = disabled === true
    if (this._input !== undefined && this._input !== null) {
      this._renderTokens()
      this._syncAll()
    }
    return
  }

  /* ----- public API ----- */

  get tokens() {
    return [...this._tokens]
  }

  set tokens(list) {
    this._applyTokens(toTokenList(Array.isArray(list) === true ? list : []))
    return
  }

  /* The tokens as one comma-separated string. */
  get value() {
    return this._tokens.join(",")
  }

  set value(next) {
    const list = Array.isArray(next) === true ? toTokenList(next) : toTokenList(next === null || next === undefined ? "" : String(next))
    this._applyTokens(list)
    return
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

  get validateToken() {
    return this._validateToken
  }

  set validateToken(validator) {
    this._validateToken = typeof validator === "function" ? validator : null
    return
  }

  checkValidity() {
    this._refreshValidity()
    const valid = super.checkValidity()
    return valid
  }

  reportValidity() {
    this._refreshValidity()
    const valid = super.reportValidity()
    return valid
  }

  focus(options) {
    if (this._input === undefined || this._input === null) {
      return
    }
    if (this._input.hidden === false) {
      this._input.focus(options)
    } else {
      this._focusChip(this._tokens.length - 1)
    }
    return
  }
}
