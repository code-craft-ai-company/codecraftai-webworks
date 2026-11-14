/*
 * mjmaskedinput.js
 *
 * <mj-masked-input> -- pattern-constrained text input with auto-caret
 * advancement, ghost overlay, and raw/formatted value exposure.
 *
 * Mask characters: `9` digit, `a` letter, `*` letter or digit; every other
 * character is a literal that the component inserts itself.
 *
 * Value model: `this._raw` is the string of characters the user has entered,
 * without literals and without placeholder characters; it always fills the
 * editable mask positions from the first one. Everything else is derived:
 *   - `value` / the form value: the entered characters with the mask's
 *     literals between them ("" when nothing is entered),
 *   - `rawValue`: `this._raw`,
 *   - the text in the <input>: `value` plus the literals that follow the
 *     last entered character (eager mode), or `this._raw` alone while a
 *     lazy-mode field has focus.
 * Every way text can reach the input -- keys, paste, drop, IME, autofill,
 * the `value` attribute and property -- goes through the same per-position
 * matcher, so a character can never land in a position of the wrong type.
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

.field {
  display: flex;
  align-items: center;
  min-height: var(--mj-control-height-md);
  background: var(--mj-surface);
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-md);
  position: relative;
  transition: border-color var(--mj-motion-fast) var(--mj-motion-ease);
  overflow: hidden;
  font-family: var(--mj-font-mono);
}
:host([size="sm"]) .field { min-height: var(--mj-control-height-sm); }
:host([size="lg"]) .field { min-height: var(--mj-control-height-lg); }
.field:focus-within {
  border-color: var(--mj-accent);
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.field[data-invalid] { border-color: var(--mj-color-danger); }

.prefix, .suffix {
  display: flex;
  align-items: center;
  padding: 0 var(--mj-space-2);
  color: var(--mj-text-muted);
  flex-shrink: 0;
}
.prefix[hidden], .suffix[hidden] { display: none; }

.input-wrap {
  flex: 1;
  position: relative;
  min-width: 0;
}

.mask-overlay {
  position: absolute;
  inset: 0;
  padding: 0 var(--mj-space-3);
  display: flex;
  align-items: center;
  pointer-events: none;
  color: var(--mj-text-muted);
  font-family: inherit;
  white-space: pre;
  overflow: hidden;
}
.mask-overlay[hidden] { display: none; }
.mask-overlay .typed { visibility: hidden; }

input {
  position: relative;
  width: 100%;
  height: 100%;
  padding: 0 var(--mj-space-3);
  font: inherit;
  color: var(--mj-text);
  background: transparent;
  border: none;
  outline: none;
  font-family: inherit;
}
input::placeholder { color: var(--mj-text-muted); }
input:disabled { cursor: not-allowed; }

.below { margin-top: var(--mj-space-1); }
.help { font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }
.help:empty { display: none; }
.error { font-size: var(--mj-font-size-sm); color: var(--mj-color-danger); display: none; }
.error[data-visible] { display: block; }

:host([disabled]) .field, .field[data-disabled] { opacity: 0.55; pointer-events: none; }
`;

const DEFAULT_PLACEHOLDER_CHAR = "_";

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

/* True when `character` may occupy an editable position of `type`. */
function characterMatches(character, type) {
  let matches = false
  if (type === "digit") {
    matches = /^[0-9]$/.test(character)
  } else if (type === "letter") {
    matches = /^[a-zA-Z]$/.test(character)
  } else if (type === "alnum") {
    matches = /^[a-zA-Z0-9]$/.test(character)
  }
  return matches
}

export class MjMaskedInput extends FormControlMixin(MjElement) {
  static tagName = "mj-masked-input";
  static styles = STYLES;
  static watched = [
    "mask", "label", "help-text", "error-message", "value", "placeholder",
    "placeholder-char", "mode", "show-mask",
    "required", "disabled", "readonly", "inputmode", "autocomplete", "size",
    "aria-label", "aria-labelledby"
  ];

  constructor() {
    super()
    this._initFormControl()

    /* Parsed mask: one { type, literal } per mask character. */
    this._maskParts = []

    /* Mask index of every editable position, and its type. */
    this._slots = []

    /* The mask text the two arrays above were parsed from. */
    this._parsedMask = null

    /* The mask text an "unusable mask" console message was last logged for. */
    this._warnedMask = null

    /* Characters entered so far (no literals, no placeholders). */
    this._raw = ""

    /* True while the shadow input has focus. */
    this._focused = false

    /* Whether the mask was complete after the last change. */
    this._wasComplete = false

    /* Value at the last mj-change, used to suppress no-op change events. */
    this._committedValue = ""

    /* The `value` attribute text most recently applied to the control. */
    this._appliedValueAttribute = null

    /* True while an ancestor <fieldset disabled> disables the control. */
    this._formDisabled = false

    /* Errors are shown once the user has left the field or a submit failed. */
    this._showErrors = false

    this._inputId = nextId("mjmi-input")
    this._helpId = nextId("mjmi-help")
    this._errorId = nextId("mjmi-error")
  }

  render() {
    const markup = html`
      <label class="label" part="label" for="${this._inputId}"></label>
      <div class="field" part="field">
        <span class="prefix" part="prefix"><slot name="prefix"></slot></span>
        <div class="input-wrap">
          <span class="mask-overlay" part="mask-overlay" aria-hidden="true" hidden><span class="typed"></span><span class="remaining"></span></span>
          <input part="input" id="${this._inputId}" type="text" autocomplete="off" />
        </div>
        <span class="suffix" part="suffix"><slot name="suffix"></slot></span>
      </div>
      <div class="below">
        <span class="help" part="help" id="${this._helpId}"></span>
        <span class="error" part="error" id="${this._errorId}" role="alert"></span>
      </div>
    `
    return markup
  }

  afterRender() {
    this._input = this.$("input")
    this._labelEl = this.$(".label")
    this._maskOverlay = this.$(".mask-overlay")
    this._overlayTyped = this.$(".mask-overlay .typed")
    this._overlayRemaining = this.$(".mask-overlay .remaining")
    this._helpEl = this.$(".help")
    this._errorEl = this.$(".error")
    this._fieldEl = this.$(".field")

    /* Empty prefix / suffix wrappers take no room (see _syncAffixes). */
    this._syncAffixes()
    const affixSlots = this.$all("[part='prefix'] slot, [part='suffix'] slot")
    for (let index = 0; index < affixSlots.length; index = index + 1) {
      this.listen(affixSlots[index], "slotchange", this._syncAffixes.bind(this))
    }

    /* The shadow DOM is new: nothing in it has focus yet. */
    this._focused = false
    this._ensureMaskParsed()
    this._warnAboutMask()

    /* An untouched control still submits its value, as a native one does. */
    this._storeRaw(this._raw)
    this._syncAll()

    this.listen(this._input, "beforeinput", this._onBeforeInput.bind(this))
    this.listen(this._input, "input", this._onInputEvent.bind(this))
    this.listen(this._input, "compositionend", this._onCompositionEnd.bind(this))
    this.listen(this._input, "keydown", this._onKeydown.bind(this))
    this.listen(this._input, "paste", this._onPaste.bind(this))
    this.listen(this._input, "focus", this._onFocus.bind(this))
    this.listen(this._input, "blur", this._onBlur.bind(this))
    this.listen(this, "invalid", this._onInvalid.bind(this))
    this.listen(this, "click", this._onHostClick.bind(this))
    return
  }


  /*
   * An affix wrapper is shown only while its slot has content: an empty one
   * would still take its padding and indent the input.
   */
  _syncAffixes() {
    const wrappers = this.$all("[part='prefix'], [part='suffix']")
    for (let index = 0; index < wrappers.length; index = index + 1) {
      const wrapper = wrappers[index]
      const slot = wrapper.querySelector("slot")
      const assigned = slot !== null ? slot.assignedNodes({ flatten: true }) : []
      wrapper.hidden = assigned.length === 0
    }
    return
  }

  onConnected() {
    /* Labels outside the shadow root can only be resolved once connected. */
    this._syncAccessibleName()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "mask") {
      this._ensureMaskParsed()
    }
    if (name === "value") {
      this._applyValueAttribute(newValue)
    }

    if (this._input === undefined || this._input === null) {
      return
    }

    if (name === "mask") {
      this._warnAboutMask()
    }
    this._syncAll()
    return
  }

  /* ----- mask model ----- */

  /*
   * Parse the `mask` attribute if it differs from the mask already parsed.
   * Called before any value is mapped onto the mask, including before the
   * first render, so `value` and `mask` may arrive in either order. When the
   * mask changes, the characters already entered are re-fitted to it.
   */
  _ensureMaskParsed() {
    const mask = this.getAttribute("mask") || ""
    if (mask === this._parsedMask) {
      return
    }

    const hadMask = this._parsedMask !== null
    this._parsedMask = mask
    this._maskParts = []
    this._slots = []

    for (let index = 0; index < mask.length; index = index + 1) {
      const character = mask[index]
      let type = "literal"
      if (character === "9") {
        type = "digit"
      } else if (character === "a") {
        type = "letter"
      } else if (character === "*") {
        type = "alnum"
      }

      if (type === "literal") {
        this._maskParts.push({ type: type, literal: character })
      } else {
        this._maskParts.push({ type: type, literal: null })
        this._slots.push({ position: index, type: type })
      }
    }

    if (hadMask === true) {
      /* Re-fit what was entered, or set before the mask arrived. */
      this._storeRaw(this._rawFromText(this._raw))
      this._committedValue = this._value
    }
    return
  }

  /* Report an unusable mask once per mask text. */
  _warnAboutMask() {
    if (this._warnedMask === this._parsedMask) {
      return
    }
    this._warnedMask = this._parsedMask

    if (this._parsedMask.length === 0) {
      console.warn("[mj-masked-input] no mask set; behaving as a plain text field")
    } else if (this._slots.length === 0) {
      console.error("[mj-masked-input] mask contains no editable positions; showing it read-only")
    }
    return
  }

  /* True when a mask with at least one editable position is in effect. */
  _hasEditableMask() {
    const editable = this._slots.length > 0
    return editable
  }

  /* True when the mask consists of literals only. */
  _isLiteralOnlyMask() {
    const literalOnly = this._maskParts.length > 0 && this._slots.length === 0
    return literalOnly
  }

  /*
   * Formatted text for `raw`: the entered characters with the mask's
   * literals between them. Text stops after the last entered character
   * unless the mask is complete; `withPendingLiterals` also appends the
   * literals that directly follow it, which is what eager mode displays so
   * the next key lands in the next editable position.
   */
  _format(raw, withPendingLiterals) {
    if (this._maskParts.length === 0 || raw.length === 0) {
      return raw
    }

    let text = ""
    let rawIndex = 0
    let finished = false

    for (let index = 0; index < this._maskParts.length && finished === false; index = index + 1) {
      const part = this._maskParts[index]
      if (part.type === "literal") {
        const allEntered = rawIndex >= raw.length
        const maskComplete = rawIndex >= this._slots.length
        if (allEntered === true && maskComplete === false && withPendingLiterals === false) {
          finished = true
        } else {
          text = text + part.literal
        }
      } else if (rawIndex < raw.length) {
        text = text + raw[rawIndex]
        rawIndex = rawIndex + 1
      } else {
        finished = true
      }
    }
    return text
  }

  /*
   * Read `text` as already formatted for this mask: every character must be
   * the literal, or a valid character, of its mask position. Returns the
   * entered characters, or null when the text does not follow the mask.
   */
  _rawFromFormatted(text) {
    let raw = ""
    let follows = text.length <= this._maskParts.length

    for (let index = 0; index < text.length && follows === true; index = index + 1) {
      const part = this._maskParts[index]
      const character = text[index]
      if (part.type === "literal") {
        follows = character === part.literal
      } else if (characterMatches(character, part.type) === true) {
        raw = raw + character
      } else {
        follows = false
      }
    }

    const result = follows === true ? raw : null
    return result
  }

  /*
   * Append to `head` every character of `text` that fits the next editable
   * position; characters that do not fit (literals, separators, anything of
   * the wrong type) are skipped. Stops when the mask is full.
   */
  _appendMatching(head, text) {
    let raw = head
    for (let index = 0; index < text.length && raw.length < this._slots.length; index = index + 1) {
      const slot = this._slots[raw.length]
      if (characterMatches(text[index], slot.type) === true) {
        raw = raw + text[index]
      }
    }
    return raw
  }

  /*
   * Map arbitrary text -- formatted ("(555) 123-4567") or unformatted
   * ("5551234567") -- onto the mask and return the entered characters.
   */
  _rawFromText(text) {
    const source = text === null || text === undefined ? "" : String(text)
    let raw = source

    if (this._hasEditableMask() === true) {
      const formatted = this._rawFromFormatted(source)
      raw = formatted !== null ? formatted : this._appendMatching("", source)
    } else if (this._isLiteralOnlyMask() === true) {
      raw = ""
    }
    return raw
  }

  /*
   * Replace the entered characters [start, end) with the fitting characters
   * of `inserted`, then re-fit the characters that followed. Returns the new
   * raw string, the caret (as an index into it) and how many characters of
   * `inserted` were accepted.
   */
  _spliceRaw(start, end, inserted) {
    const head = this._raw.slice(0, start)
    const withInserted = this._appendMatching(head, inserted)
    const accepted = withInserted.length - head.length
    const next = this._appendMatching(withInserted, this._raw.slice(end))
    const result = { raw: next, caret: withInserted.length, accepted: accepted }
    return result
  }

  /* True while the input shows the bare entered characters (lazy mode). */
  _showsRawText() {
    const mode = this.getAttribute("mode") || "eager"
    const rawText = mode === "lazy" && this._focused === true && this._hasEditableMask() === true
    return rawText
  }

  /* The text the <input> should show for the current state. */
  _displayText() {
    let text = ""
    if (this._isLiteralOnlyMask() === true) {
      text = this._parsedMask
    } else if (this._showsRawText() === true) {
      text = this._raw
    } else {
      text = this._format(this._raw, true)
    }
    return text
  }

  /* Convert a caret offset in the <input> to an index into `this._raw`. */
  _rawIndexFromCaret(offset) {
    let rawIndex = 0
    if (this._showsRawText() === true || this._hasEditableMask() === false) {
      rawIndex = offset
    } else {
      for (let index = 0; index < this._slots.length; index = index + 1) {
        if (this._slots[index].position < offset) {
          rawIndex = rawIndex + 1
        }
      }
    }
    return Math.min(rawIndex, this._raw.length)
  }

  /* Convert an index into `this._raw` to a caret offset in the <input>. */
  _caretFromRawIndex(rawIndex) {
    let offset = 0
    if (this._showsRawText() === true || this._hasEditableMask() === false) {
      offset = Math.min(rawIndex, this._raw.length)
    } else if (rawIndex >= this._raw.length) {
      offset = this._displayText().length
    } else {
      offset = this._slots[rawIndex].position
    }
    return offset
  }

  /* Store `raw` and the form value derived from it; no rendering. */
  _storeRaw(raw) {
    this._raw = raw
    this._wasComplete = this.complete
    this._setFormValue(this._format(raw, false))
    return
  }

  /* Write the display text (and optionally the caret) into the <input>. */
  _renderInput(caretRawIndex) {
    const text = this._displayText()
    if (this._input.value !== text) {
      this._input.value = text
    }
    if (caretRawIndex !== null && caretRawIndex !== undefined && this._focused === true) {
      const offset = this._caretFromRawIndex(caretRawIndex)
      this._input.setSelectionRange(offset, offset)
    }
    this._updateOverlay()
    return
  }

  /*
   * A change made by the user: store, redraw, and emit `mj-input` when the
   * value changed and `mj-complete` when the mask has just become complete.
   */
  _commitUserRaw(raw, caretRawIndex) {
    const previousValue = this._value
    const wasComplete = this._wasComplete

    this._storeRaw(raw)
    this._renderInput(caretRawIndex)
    this._renderValidity(false)

    const complete = this.complete
    if (this._value !== previousValue) {
      this.emit("mj-input", { value: this._value, rawValue: this._raw, complete: complete })
    }
    if (complete === true && wasComplete === false) {
      this.emit("mj-complete", { value: this._value, rawValue: this._raw })
    }
    return
  }

  /* ----- attribute / state sync ----- */

  /* The control is disabled by its own attribute or by a disabled fieldset. */
  _isDisabled() {
    const disabled = this.hasAttribute("disabled") === true || this._formDisabled === true
    return disabled
  }

  _getPlaceholderChar() {
    const attribute = this.getAttribute("placeholder-char") || ""
    const character = attribute.length > 0 ? Array.from(attribute)[0] : DEFAULT_PLACEHOLDER_CHAR
    return character
  }

  _syncAll() {
    const label = this.getAttribute("label") || ""
    const helpText = this.getAttribute("help-text") || ""
    const placeholder = this.getAttribute("placeholder") || ""
    const disabled = this._isDisabled()
    const readonly = this.hasAttribute("readonly") === true || this._isLiteralOnlyMask() === true
    const required = this.hasAttribute("required")
    const inputmode = this.getAttribute("inputmode") || this._deriveInputmode()
    const autocomplete = this.getAttribute("autocomplete") || "off"
    const showMask = this.hasAttribute("show-mask")

    this._labelEl.textContent = label
    this._labelEl.toggleAttribute("data-required", required === true)
    this._fieldEl.toggleAttribute("data-disabled", disabled === true)

    this._input.disabled = disabled
    this._input.readOnly = readonly
    this._input.inputMode = inputmode
    this._input.autocomplete = autocomplete
    this._input.setAttribute("aria-required", required === true ? "true" : "false")

    /* The ghost overlay takes the place of a placeholder. */
    this._input.placeholder = showMask === true ? "" : placeholder

    this._helpEl.textContent = helpText
    this._maskOverlay.hidden = showMask === false || this._hasEditableMask() === false

    this._syncAccessibleName()
    this._renderInput(null)

    /* required / mask / error-message all feed validity. */
    this._refreshValidity()
    this._renderValidity(false)
    return
  }

  /*
   * Name the shadow input. The built-in <label for> covers the `label`
   * attribute; a name given to the host from outside is copied across.
   */
  _syncAccessibleName() {
    if (this._input === undefined || this._input === null) {
      return
    }

    const label = this.getAttribute("label") || ""
    const hostLabel = resolveHostLabel(this, this._internals)
    const explicit = this.hasAttribute("aria-label") === true || this.hasAttribute("aria-labelledby") === true

    if (hostLabel.length > 0 && (explicit === true || label.length === 0)) {
      this._input.setAttribute("aria-label", hostLabel)
    } else {
      this._input.removeAttribute("aria-label")
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

  _deriveInputmode() {
    let allDigits = this._slots.length > 0
    for (let index = 0; index < this._slots.length; index = index + 1) {
      if (this._slots[index].type !== "digit") {
        allDigits = false
      }
    }
    const inputmode = allDigits === true ? "numeric" : "text"
    return inputmode
  }

  /*
   * Ghost text behind the input: an invisible copy of what is typed (so the
   * rest lines up in any font) followed by the unfilled part of the mask.
   */
  _updateOverlay() {
    if (this.hasAttribute("show-mask") === false || this._hasEditableMask() === false) {
      return
    }

    const placeholderChar = this._getPlaceholderChar()
    const shown = this._input.value
    let remaining = ""

    if (this._showsRawText() === true) {
      const missing = this._slots.length - this._raw.length
      for (let count = 0; count < missing; count = count + 1) {
        remaining = remaining + placeholderChar
      }
    } else {
      for (let index = shown.length; index < this._maskParts.length; index = index + 1) {
        const part = this._maskParts[index]
        remaining = remaining + (part.type === "literal" ? part.literal : placeholderChar)
      }
    }

    this._overlayTyped.textContent = shown
    this._overlayRemaining.textContent = remaining
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

  /*
   * The single entry point for every programmatic value change. Accepts
   * formatted or unformatted text and fits it to the mask.
   */
  _applyValue(next) {
    this._ensureMaskParsed()
    this._storeRaw(this._rawFromText(next))
    this._committedValue = this._value

    if (this._input !== undefined && this._input !== null) {
      this._renderInput(null)
      this._renderValidity(false)
    }
    return
  }

  /* ----- user input ----- */

  /*
   * Every edit the browser is about to make is intercepted here and applied
   * to the model instead, whatever produced it: hardware or soft keyboard,
   * drag-and-drop, cut, spell-check replacement. IME composition cannot be
   * cancelled; it is fitted to the mask when it ends (see _onInputEvent).
   */
  _onBeforeInput(event) {
    if (this._hasEditableMask() === false) {
      return
    }

    const inputType = event.inputType || ""
    if (event.isComposing === true || inputType === "insertCompositionText") {
      return
    }

    const selectionStart = this._input.selectionStart !== null ? this._input.selectionStart : this._input.value.length
    const selectionEnd = this._input.selectionEnd !== null ? this._input.selectionEnd : selectionStart
    const start = this._rawIndexFromCaret(selectionStart)
    const end = this._rawIndexFromCaret(selectionEnd)
    const hasSelection = selectionEnd > selectionStart

    let handled = true

    if (inputType === "insertLineBreak" || inputType === "insertParagraph") {
      /* Enter: nothing to insert; leave implicit submission to the browser. */
      handled = false
    } else if (inputType.indexOf("insert") === 0) {
      let text = event.data
      if ((text === null || text === undefined) && event.dataTransfer !== null && event.dataTransfer !== undefined) {
        text = event.dataTransfer.getData("text/plain")
      }
      if (text !== null && text !== undefined && text.length > 0) {
        this._insertText(start, end, text)
      }
    } else if (hasSelection === true && inputType.indexOf("delete") === 0) {
      this._deleteRange(start, end)
    } else if (inputType === "deleteContentBackward") {
      this._deleteRange(Math.max(0, start - 1), start)
    } else if (inputType === "deleteContentForward") {
      this._deleteRange(start, Math.min(this._raw.length, start + 1))
    } else if (inputType.indexOf("delete") === 0 && inputType.indexOf("Backward") > 0) {
      /* Word / line deletion: there are no words in a masked value. */
      this._deleteRange(0, start)
    } else if (inputType.indexOf("delete") === 0 && inputType.indexOf("Forward") > 0) {
      this._deleteRange(start, this._raw.length)
    } else if (inputType === "historyUndo" || inputType === "historyRedo") {
      /* The model has no history; the native one would bypass the mask. */
    } else {
      handled = false
    }

    if (handled === true) {
      event.preventDefault()
    }
    return
  }

  /* Insert text at the raw range; text with no fitting character is ignored. */
  _insertText(start, end, text) {
    const result = this._spliceRaw(start, end, text)
    if (result.accepted === 0) {
      return
    }
    this._commitUserRaw(result.raw, result.caret)
    return
  }

  _deleteRange(start, end) {
    if (end <= start) {
      /* Nothing to remove; only put the caret on an editable position. */
      this._renderInput(start)
      return
    }
    const result = this._spliceRaw(start, end, "")
    this._commitUserRaw(result.raw, start)
    return
  }

  /*
   * Fallback for text that reached the input without a cancellable
   * `beforeinput`: IME composition, autofill, a scripted `input` event.
   * The whole text is fitted to the mask again.
   */
  _onInputEvent(event) {
    if (event.isComposing === true) {
      return
    }
    this._adoptInputText()
    return
  }

  _onCompositionEnd(event) {
    this._adoptInputText()
    return
  }

  _adoptInputText() {
    const text = this._input.value
    if (text === this._displayText()) {
      return
    }
    const raw = this._rawFromText(text)
    /* Without a mask the browser has already placed the caret correctly. */
    const caret = this._hasEditableMask() === true ? raw.length : null
    this._commitUserRaw(raw, caret)
    return
  }

  _onPaste(event) {
    if (this._hasEditableMask() === false) {
      return
    }
    event.preventDefault()

    if (this._isDisabled() === true || this.hasAttribute("readonly") === true) {
      return
    }

    const text = event.clipboardData !== null && event.clipboardData !== undefined
      ? event.clipboardData.getData("text/plain")
      : ""
    const start = this._rawIndexFromCaret(this._input.selectionStart)
    const end = this._rawIndexFromCaret(this._input.selectionEnd)

    if (start === 0 && end >= this._raw.length) {
      /* Replacing everything: the clipboard may hold a formatted value. */
      const raw = this._rawFromText(text)
      if (text.length === 0 || raw.length > 0) {
        this._commitUserRaw(raw, raw.length)
      }
    } else {
      this._insertText(start, end, text)
    }
    return
  }

  /*
   * Caret keys move between editable positions so the caret never rests
   * inside a run of literals. With Shift (extending a selection) or a
   * modifier the browser's own behaviour is kept.
   */
  _onKeydown(event) {
    const modified = event.shiftKey === true || event.ctrlKey === true || event.metaKey === true || event.altKey === true
    if (modified === true || this._hasEditableMask() === false || this._showsRawText() === true) {
      return
    }

    const key = event.key
    const selectionStart = this._input.selectionStart
    const selectionEnd = this._input.selectionEnd
    const collapsed = selectionStart === selectionEnd
    let target = null

    if (key === "ArrowLeft") {
      const rawIndex = this._rawIndexFromCaret(selectionStart)
      target = collapsed === true ? Math.max(0, rawIndex - 1) : rawIndex
    } else if (key === "ArrowRight") {
      const rawIndex = this._rawIndexFromCaret(selectionEnd)
      target = collapsed === true ? Math.min(this._raw.length, rawIndex + 1) : rawIndex
    } else if (key === "Home") {
      target = 0
    } else if (key === "End") {
      target = this._raw.length
    }

    if (target !== null) {
      event.preventDefault()
      const offset = this._caretFromRawIndex(target)
      this._input.setSelectionRange(offset, offset)
    }
    return
  }

  _onFocus(event) {
    /* A label placed after the field in the document exists by now. */
    this._syncAccessibleName()

    this._focused = true
    if (this._showsRawText() === true) {
      /* Lazy mode: edit the bare characters; separators return on blur. */
      this._renderInput(this._raw.length)
    }
    return
  }

  _onBlur(event) {
    this._focused = false
    this._renderInput(null)

    this._showErrors = true
    this._refreshValidity()
    this._renderValidity(true)

    if (this._value !== this._committedValue) {
      this._committedValue = this._value
      this.emit("mj-change", { value: this._value, rawValue: this._raw, complete: this.complete })
    }
    return
  }

  /* A failed checkValidity() / reportValidity() / form submit. */
  _onInvalid(event) {
    this._showErrors = true
    this._renderValidity(true)
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

  /* ----- validation ----- */

  /*
   * Show or hide the inline error from the current validity. `error-message`
   * replaces the built-in text but never makes a valid field look invalid.
   * `announce` is true when the user (blur) or a submit attempt triggered
   * the check; only then is `mj-invalid` emitted.
   */
  _renderValidity(announce) {
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
   * A value that does not fill the mask is a pattern mismatch whether or
   * not the field is required; an empty optional field is valid and an
   * empty required one is `valueMissing` (handled by the mixin).
   */
  _refreshValidity() {
    const incomplete = this._hasEditableMask() === true && this._raw.length > 0 && this.complete === false

    if (incomplete === true && this._internals !== null && this._internals !== undefined) {
      const anchor = this._validationAnchor()
      const flags = { patternMismatch: true }
      const message = t("mj.maskedInput.incomplete")
      if (anchor !== null && anchor !== undefined) {
        this._internals.setValidity(flags, message, anchor)
      } else {
        this._internals.setValidity(flags, message)
      }
      return
    }
    super._refreshValidity()
    return
  }

  _validationAnchor() {
    const anchor = this._input !== undefined ? this._input : null
    return anchor
  }

  onFormReset(initial) {
    this._showErrors = false
    this._applyValue(initial)
    return
  }

  onFormRestore(state) {
    const restored = typeof state === "string" ? state : ""
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

  reportValidity() {
    this._refreshValidity()
    const valid = super.reportValidity()
    return valid
  }

  /* ----- public API ----- */

  get value() {
    return this._value
  }

  set value(next) {
    this._applyValue(next)
    return
  }

  /* The entered characters without literals. */
  get rawValue() {
    return this._raw
  }

  /* True when every editable position of the mask is filled. */
  get complete() {
    const complete = this._slots.length > 0 && this._raw.length === this._slots.length
    return complete
  }

  focus(options) {
    if (this._input !== undefined && this._input !== null) {
      this._input.focus(options)
    }
    return
  }
}
