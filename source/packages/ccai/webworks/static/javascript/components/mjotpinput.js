/*
 * mjotpinput.js
 *
 * <mj-otp-input> -- segmented verification code input with auto-advance,
 * paste-to-fill, and a single concatenated form value.
 *
 * State model: `this._chars` holds one entry per segment ("" when empty)
 * and is the single source of truth; the form value and the `value`
 * property are its concatenation. The segments are rebuilt from it whenever
 * they are re-created (first render, re-parenting, a change of `length`,
 * `inputtype` or `group-at`), so a value assigned before the element is
 * connected is shown and a rebuilt group never submits a stale code.
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

.group {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  flex-wrap: wrap;
}

.segment {
  width: 2.75rem;
  height: 3.5rem;
  padding: 0;
  text-align: center;
  font: inherit;
  font-size: var(--mj-font-size-xl);
  font-weight: var(--mj-font-weight-bold);
  color: var(--mj-text);
  background: var(--mj-surface);
  border: 2px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-md);
  outline: none;
  transition: border-color var(--mj-motion-fast) var(--mj-motion-ease);
  caret-color: var(--mj-accent);
}
:host([size="sm"]) .segment { width: 2.25rem; height: 2.75rem; font-size: var(--mj-font-size-lg); }
:host([size="lg"]) .segment { width: 3.25rem; height: 4rem; font-size: var(--mj-font-size-2xl); }
.segment:focus {
  border-color: var(--mj-accent);
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.segment[data-filled] { border-color: var(--mj-accent); }
.segment[data-invalid] { border-color: var(--mj-color-danger); }
.segment:disabled { opacity: 0.55; cursor: not-allowed; }

.separator {
  color: var(--mj-text-muted);
  font-weight: var(--mj-font-weight-bold);
  flex-shrink: 0;
}

.below { margin-top: var(--mj-space-1); }
.help { font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }
.help:empty { display: none; }
.error { font-size: var(--mj-font-size-sm); color: var(--mj-color-danger); display: none; }
.error[data-visible] { display: block; }

.announce { position: absolute; width:1px; height:1px; overflow:hidden; clip:rect(0,0,0,0); }
`;

const DEFAULT_LENGTH = 6;
const MAXIMUM_LENGTH = 12;

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

export class MjOtpInput extends FormControlMixin(MjElement) {
  static tagName = "mj-otp-input";
  static styles = STYLES;
  static watched = [
    "label", "help-text", "error-message", "value", "length", "inputtype",
    "required", "disabled", "readonly", "autocomplete", "group-at", "size",
    "aria-label", "aria-labelledby"
  ];

  constructor() {
    super()
    this._initFormControl()

    /* One entry per segment; "" for an empty segment. */
    this._chars = []

    /* True once mj-complete has fired for the current full code. */
    this._wasFull = false

    /* Value at the last mj-change, used to suppress no-op change events. */
    this._committedValue = ""

    /* The `value` attribute text most recently applied to the control. */
    this._appliedValueAttribute = null

    /* True while an ancestor <fieldset disabled> disables the control. */
    this._formDisabled = false

    /* Errors are shown once the user has left the group or a submit failed. */
    this._showErrors = false

    this._groupId = nextId("mjotp-group")
    this._labelId = nextId("mjotp-label")
    this._segmentIdPrefix = nextId("mjotp-seg")
    this._helpId = nextId("mjotp-help")
    this._errorId = nextId("mjotp-error")
    this._announceId = nextId("mjotp-announce")
  }

  render() {
    const markup = html`
      <label class="label" part="label" id="${this._labelId}" for="${this._segmentIdPrefix}-0"></label>
      <div class="group" part="group" role="group" id="${this._groupId}"></div>
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
    this._groupEl = this.$(".group")
    this._helpEl = this.$(".help")
    this._errorEl = this.$(".error")
    this._announceEl = this.$(".announce")

    /*
     * The shadow DOM is new: rebuild the segments from the stored code.
     * Registering the value also makes an untouched control submit an
     * (empty) entry, as a native one does.
     */
    this._setChars(this._chars)
    this._buildSegments()
    this._syncAll()

    this.listen(this._groupEl, "keydown", this._onGroupKeydown.bind(this))
    this.listen(this._groupEl, "input", this._onGroupInput.bind(this))
    this.listen(this._groupEl, "paste", this._onGroupPaste.bind(this))
    this.listen(this._groupEl, "focusin", this._onGroupFocusin.bind(this))
    this.listen(this.shadowRoot, "focusout", this._onFocusout.bind(this))
    this.listen(this, "invalid", this._onInvalid.bind(this))
    this.listen(this, "click", this._onHostClick.bind(this))
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
    if (name === "length" || name === "inputtype") {
      /* Re-fit the stored code to the new length / character set. */
      this._setChars(this._sanitize(this._chars.join("")).split(""))
    }

    if (this._groupEl === undefined || this._groupEl === null) {
      return
    }

    if (name === "length" || name === "inputtype" || name === "group-at") {
      this._buildSegments()
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

  _isEditable() {
    const editable = this._isDisabled() === false && this.hasAttribute("readonly") === false
    return editable
  }

  _getLength() {
    let length = parseInt(this.getAttribute("length") || String(DEFAULT_LENGTH), 10)
    if (Number.isNaN(length) === true || length < 1) {
      length = DEFAULT_LENGTH
    }
    return Math.min(length, MAXIMUM_LENGTH)
  }

  _getInputType() {
    const attribute = this.getAttribute("inputtype") || "numeric"
    const inputType = attribute === "alphanumeric" || attribute === "password" ? attribute : "numeric"
    return inputType
  }

  /*
   * Keep only the characters the current `inputtype` accepts: digits for
   * numeric and password codes, letters and digits (upper-cased) otherwise.
   */
  _sanitize(text) {
    const source = text === null || text === undefined ? "" : String(text)
    let cleaned = ""
    if (this._getInputType() === "alphanumeric") {
      cleaned = source.replace(/[^A-Za-z0-9]/g, "").toUpperCase()
    } else {
      cleaned = source.replace(/[^0-9]/g, "")
    }
    return cleaned
  }

  /* The segment inputs; an empty list before the first render. */
  _getSegments() {
    let segments = []
    if (this._groupEl !== undefined && this._groupEl !== null) {
      segments = Array.from(this._groupEl.querySelectorAll(".segment"))
    }
    return segments
  }

  /*
   * Store the code. `chars` is padded or truncated to the segment count;
   * the form value is the concatenation.
   */
  _setChars(chars) {
    const length = this._getLength()
    const next = []
    for (let index = 0; index < length; index = index + 1) {
      const character = chars[index]
      next.push(character !== undefined && character !== null ? character : "")
    }
    this._chars = next
    this._setFormValue(next.join(""))
    return
  }

  _isComplete() {
    let complete = this._chars.length > 0
    for (let index = 0; index < this._chars.length; index = index + 1) {
      if (this._chars[index].length === 0) {
        complete = false
      }
    }
    return complete
  }

  /* ----- rendering ----- */

  _buildSegments() {
    this._groupEl.textContent = ""

    const length = this._getLength()
    const inputType = this._getInputType()
    const groupAt = parseInt(this.getAttribute("group-at") || "0", 10)
    const positionLabelKey = inputType === "alphanumeric" ? "mj.otpInput.characterLabel" : "mj.otpInput.digitLabel"

    /* A length change may have changed the number of stored entries. */
    if (this._chars.length !== length) {
      this._setChars(this._chars)
    }

    for (let index = 0; index < length; index = index + 1) {
      if (groupAt > 0 && index === groupAt) {
        const separator = document.createElement("span")
        separator.className = "separator"
        separator.setAttribute("part", "separator")
        separator.setAttribute("aria-hidden", "true")
        const slot = document.createElement("slot")
        slot.setAttribute("name", "separator")
        slot.textContent = "–"
        separator.appendChild(slot)
        this._groupEl.appendChild(separator)
      }

      const segment = document.createElement("input")
      segment.className = "segment"
      segment.setAttribute("part", "segment")
      segment.setAttribute("id", `${this._segmentIdPrefix}-${index}`)
      segment.setAttribute("data-index", String(index))
      segment.type = inputType === "password" ? "password" : "text"
      segment.inputMode = inputType === "alphanumeric" ? "text" : "numeric"
      segment.setAttribute("aria-label", t(positionLabelKey, { position: index + 1, length: length }))
      this._groupEl.appendChild(segment)
    }

    this._renderChars()
    return
  }

  /* Write the stored code into the segments. */
  _renderChars() {
    const segments = this._getSegments()
    for (let index = 0; index < segments.length; index = index + 1) {
      const character = this._chars[index] !== undefined ? this._chars[index] : ""
      if (segments[index].value !== character) {
        segments[index].value = character
      }
      segments[index].toggleAttribute("data-filled", character.length > 0)
    }
    return
  }

  _syncAll() {
    const label = this.getAttribute("label") || ""
    const helpText = this.getAttribute("help-text") || ""
    const autocomplete = this.getAttribute("autocomplete") || "one-time-code"
    const disabled = this._isDisabled()
    const readonly = this.hasAttribute("readonly")
    const required = this.hasAttribute("required")

    this._labelEl.textContent = label
    this._labelEl.toggleAttribute("data-required", required === true)
    this._helpEl.textContent = helpText

    /* These apply to segments that already exist, not only to new ones. */
    const segments = this._getSegments()
    for (let index = 0; index < segments.length; index = index + 1) {
      const segment = segments[index]
      segment.disabled = disabled
      segment.readOnly = readonly
      segment.autocomplete = autocomplete
      if (index === 0) {
        segment.setAttribute("aria-required", required === true ? "true" : "false")
      }
    }

    this._syncAccessibleName()

    /* required / error-message feed validity. */
    this._refreshValidity()
    this._renderValidity(false)
    return
  }

  /*
   * Name the group: the visible label when there is one, otherwise the name
   * given to the host from outside, otherwise a generic fallback.
   */
  _syncAccessibleName() {
    if (this._groupEl === undefined || this._groupEl === null) {
      return
    }

    const label = this.getAttribute("label") || ""
    const hostLabel = resolveHostLabel(this, this._internals)
    const explicit = this.hasAttribute("aria-label") === true || this.hasAttribute("aria-labelledby") === true

    if (hostLabel.length > 0 && (explicit === true || label.length === 0)) {
      this._groupEl.removeAttribute("aria-labelledby")
      this._groupEl.setAttribute("aria-label", hostLabel)
    } else if (label.length > 0) {
      this._groupEl.removeAttribute("aria-label")
      this._groupEl.setAttribute("aria-labelledby", this._labelId)
    } else {
      this._groupEl.removeAttribute("aria-labelledby")
      this._groupEl.setAttribute("aria-label", t("mj.otpInput.groupLabel"))
    }
    return
  }

  /* Help and error text are described on the group and the first segment. */
  _updateDescribedBy() {
    const ids = []
    if (this._helpEl.textContent.length > 0) {
      ids.push(this._helpId)
    }
    if (this._errorEl.hasAttribute("data-visible") === true) {
      ids.push(this._errorId)
    }

    const segments = this._getSegments()
    const targets = [this._groupEl]
    if (segments.length > 0) {
      targets.push(segments[0])
    }
    for (let index = 0; index < targets.length; index = index + 1) {
      if (ids.length > 0) {
        targets[index].setAttribute("aria-describedby", ids.join(" "))
      } else {
        targets[index].removeAttribute("aria-describedby")
      }
    }
    return
  }

  /* ----- value ----- */

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
    this._setChars(this._sanitize(next).split(""))
    this._committedValue = this._value
    this._wasFull = this._isComplete()

    if (this._groupEl !== undefined && this._groupEl !== null) {
      this._renderChars()
      this._renderValidity(false)
    }
    return
  }

  /*
   * A change made by the user: publish the code, then emit `mj-input`,
   * `mj-complete` (once per completed code) and `mj-change` (when the code
   * is complete; an incomplete code is committed when focus leaves).
   */
  _commitUserChars() {
    this._setFormValue(this._chars.join(""))
    this._renderChars()
    this._renderValidity(false)

    const value = this._value
    const complete = this._isComplete()
    this.emit("mj-input", { value: value, complete: complete })

    if (complete === true && this._wasFull === false) {
      this._wasFull = true
      this._announceEl.textContent = t("mj.otpInput.complete")
      this.emit("mj-complete", { value: value })
    } else if (complete === false) {
      this._wasFull = false
      this._announceEl.textContent = ""
    }

    if (complete === true) {
      this._emitChangeIfNeeded()
    }
    return
  }

  _emitChangeIfNeeded() {
    if (this._value !== this._committedValue) {
      this._committedValue = this._value
      this.emit("mj-change", { value: this._value })
    }
    return
  }

  /*
   * Enter `text` starting at segment `startIndex`, one accepted character
   * per segment. A string exactly as long as the code fills it from the
   * first segment. Focus ends on the segment after the last one filled.
   */
  _distribute(text, startIndex) {
    const cleaned = this._sanitize(text)
    const segments = this._getSegments()
    if (cleaned.length === 0 || segments.length === 0) {
      return
    }

    const start = cleaned.length === segments.length ? 0 : startIndex
    let lastFilled = start
    for (let index = 0; index < cleaned.length && start + index < segments.length; index = index + 1) {
      this._chars[start + index] = cleaned[index]
      lastFilled = start + index
    }

    this._commitUserChars()

    const focusIndex = Math.min(lastFilled + 1, segments.length - 1)
    segments[focusIndex].focus()
    return
  }

  _clearSegment(index) {
    if (this._chars[index] !== "") {
      this._chars[index] = ""
      this._commitUserChars()
    }
    return
  }

  /* ----- events ----- */

  _segmentIndex(event) {
    let index = -1
    const segment = event.target !== null && typeof event.target.closest === "function"
      ? event.target.closest(".segment")
      : null
    if (segment !== null) {
      index = parseInt(segment.getAttribute("data-index"), 10)
    }
    return index
  }

  _onGroupFocusin(event) {
    const index = this._segmentIndex(event)
    if (index >= 0) {
      /* Selecting the content makes the next key replace it. */
      event.target.select()
    }
    return
  }

  /*
   * Every character that reaches a segment is filtered by `inputtype` here,
   * whatever produced it: a key, a soft keyboard, SMS autofill (which may
   * put the whole code into one segment) or a drop.
   */
  _onGroupInput(event) {
    const index = this._segmentIndex(event)
    if (index < 0) {
      return
    }

    const segment = event.target
    if (this._isEditable() === false) {
      segment.value = this._chars[index]
      return
    }

    const typedOne = event.inputType === "insertText" && typeof event.data === "string" && event.data.length === 1
    const text = typedOne === true ? event.data : segment.value

    if (segment.value.length === 0) {
      this._clearSegment(index)
    } else if (this._sanitize(text).length === 0) {
      /* Not a valid character for this code: put the segment back. */
      segment.value = this._chars[index]
      segment.select()
    } else {
      this._distribute(text, index)
    }
    return
  }

  _onGroupKeydown(event) {
    const index = this._segmentIndex(event)
    if (index < 0) {
      return
    }

    const segments = this._getSegments()
    const key = event.key
    const editable = this._isEditable()

    /* Under dir="rtl" the next segment is visually to the left. */
    const rtl = getComputedStyle(this._groupEl).direction === "rtl"
    const nextKey = rtl === true ? "ArrowLeft" : "ArrowRight"
    const previousKey = rtl === true ? "ArrowRight" : "ArrowLeft"

    if (key === "Backspace") {
      event.preventDefault()
      if (editable === true) {
        if (this._chars[index] !== "") {
          this._clearSegment(index)
        } else if (index > 0) {
          segments[index - 1].focus()
          this._clearSegment(index - 1)
        }
      }
    } else if (key === "Delete") {
      event.preventDefault()
      if (editable === true) {
        this._clearSegment(index)
      }
    } else if (key === nextKey) {
      event.preventDefault()
      if (index < segments.length - 1) {
        segments[index + 1].focus()
      }
    } else if (key === previousKey) {
      event.preventDefault()
      if (index > 0) {
        segments[index - 1].focus()
      }
    } else if (key === "Home") {
      event.preventDefault()
      segments[0].focus()
    } else if (key === "End") {
      event.preventDefault()
      segments[segments.length - 1].focus()
    }
    return
  }

  _onGroupPaste(event) {
    const index = this._segmentIndex(event)
    if (index < 0) {
      return
    }

    event.preventDefault()
    if (this._isEditable() === false) {
      return
    }

    const text = event.clipboardData !== null && event.clipboardData !== undefined
      ? event.clipboardData.getData("text/plain")
      : ""
    this._distribute(text, index)
    return
  }

  /* Focus left the group: commit an incomplete code and validate. */
  _onFocusout(event) {
    const next = event.relatedTarget
    const staysInside = next !== null && next !== undefined && this.shadowRoot.contains(next) === true
    if (staysInside === true) {
      return
    }

    this._emitChangeIfNeeded()
    this._showErrors = true
    this._refreshValidity()
    this._renderValidity(true)
    return
  }

  /* A failed checkValidity() / reportValidity() / form submit. */
  _onInvalid(event) {
    this._showErrors = true
    this._renderValidity(true)
    return
  }

  /*
   * Activating an associated <label> clicks the host; move focus into the
   * group as a native control would.
   */
  _onHostClick(event) {
    const path = event.composedPath()
    if (path.length > 0 && path[0] === this && this._isDisabled() === false) {
      this.focus()
    }
    return
  }

  /* ----- validation ----- */

  /*
   * Show or hide the inline error from the current validity. `error-message`
   * replaces the built-in text but never makes a valid field look invalid.
   * `announce` is true when the user (leaving the group) or a submit attempt
   * triggered the check; only then is `mj-invalid` emitted.
   */
  _renderValidity(announce) {
    const message = this.validationMessage
    const invalid = message.length > 0 && this._showErrors === true
    const segments = this._getSegments()

    if (invalid === true) {
      const override = this.getAttribute("error-message") || ""
      const displayMessage = override.length > 0 ? override : message
      this._errorEl.textContent = displayMessage
      this._errorEl.setAttribute("data-visible", "")
      for (let index = 0; index < segments.length; index = index + 1) {
        segments[index].setAttribute("data-invalid", "")
        segments[index].setAttribute("aria-invalid", "true")
      }
      this._updateDescribedBy()
      if (announce === true) {
        this.emit("mj-invalid", { validationMessage: displayMessage })
      }
    } else {
      this._errorEl.textContent = ""
      this._errorEl.removeAttribute("data-visible")
      for (let index = 0; index < segments.length; index = index + 1) {
        segments[index].removeAttribute("data-invalid")
        segments[index].setAttribute("aria-invalid", "false")
      }
      this._updateDescribedBy()
    }
    return
  }

  /* A required code must be complete; a partial one is not enough. */
  _customValidity() {
    let message = ""
    if (this.hasAttribute("required") === true && this._isComplete() === false) {
      message = t("mj.otpInput.incomplete")
    }
    return message
  }

  _validationAnchor() {
    const segments = this._getSegments()
    const anchor = segments.length > 0 ? segments[0] : null
    return anchor
  }

  onFormReset(initial) {
    this._showErrors = false
    this._announceEl.textContent = ""
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
    if (this._groupEl !== undefined && this._groupEl !== null) {
      this._syncAll()
    }
    return
  }

  /* ----- public API ----- */

  get value() {
    return this._chars.join("")
  }

  set value(next) {
    this._applyValue(next)
    return
  }

  get complete() {
    return this._isComplete()
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

  /* Focus the first empty segment, or the first one when the code is full. */
  focus(options) {
    const segments = this._getSegments()
    if (segments.length === 0) {
      return
    }

    let target = segments[0]
    for (let index = segments.length - 1; index >= 0; index = index - 1) {
      if (this._chars[index] === "") {
        target = segments[index]
      }
    }
    target.focus(options)
    return
  }
}
