/*
 * mjinlineedit.js
 *
 * <mj-inline-edit> -- click-to-edit inline text with explicit commit/cancel
 * actions and constraint validation at commit time.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";

const STYLES = `
:host {
  display: inline-block;
  max-width: 100%;
  font-family: var(--mj-font-sans);
  font-size: var(--mj-font-size-md);
}

.display-wrap {
  display: inline-flex;
  align-items: center;
  gap: var(--mj-space-1);
  max-width: 100%;
}
.display-wrap[hidden] { display: none; }

.display-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--mj-text);
  cursor: default;
}
.display-text[data-empty] { color: var(--mj-text-muted); }
:host(:not([readonly]):not([disabled]):not([trigger="button"])) .display-text {
  cursor: pointer;
}
:host(:not([readonly]):not([disabled]):not([trigger="button"])) .display-text:hover {
  text-decoration: underline dotted;
}

.edit-trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: var(--mj-radius-sm);
  cursor: pointer;
  color: var(--mj-text-muted);
  opacity: 0;
  transition: opacity var(--mj-motion-fast);
  flex-shrink: 0;
}
.display-wrap:hover .edit-trigger,
.edit-trigger:focus-visible { opacity: 1; }
.edit-trigger:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}
:host([readonly]) .edit-trigger,
:host([disabled]) .edit-trigger { display: none; }

.edit-wrap {
  display: flex;
  align-items: flex-start;
  gap: var(--mj-space-2);
  width: 100%;
}
.edit-wrap[hidden] { display: none; }

input, textarea {
  flex: 1;
  min-width: 0;
  padding: var(--mj-space-1) var(--mj-space-2);
  font: inherit;
  color: var(--mj-text);
  background: var(--mj-surface);
  border: 1px solid var(--mj-accent);
  border-radius: var(--mj-radius-sm);
  outline: none;
}
input:focus, textarea:focus {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
input[aria-invalid="true"], textarea[aria-invalid="true"] { border-color: var(--mj-color-danger); }
textarea { resize: vertical; min-height: 3rem; }

.actions {
  display: flex;
  gap: var(--mj-space-1);
  flex-shrink: 0;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2rem;
  height: 2rem;
  padding: 0 var(--mj-space-2);
  background: var(--mj-surface);
  color: var(--mj-text);
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-sm);
  cursor: pointer;
  font: inherit;
  font-size: var(--mj-font-size-sm);
}
.action-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}
.commit-btn { background: var(--mj-accent); color: var(--mj-text-on-accent); border-color: var(--mj-accent); }
.commit-btn:hover { background: var(--mj-accent-hover); }

.error {
  font-size: var(--mj-font-size-sm);
  color: var(--mj-color-danger);
  margin-block-start: var(--mj-space-1);
  display: none;
}
.error[data-visible] { display: block; }

:host([disabled]) { opacity: 0.55; pointer-events: none; }
`;

const EMPTY_DISPLAY = "—";

export class MjInlineEdit extends FormControlMixin(MjElement) {
  static tagName = "mj-inline-edit";
  static styles = STYLES;
  static watched = [
    "value", "label", "placeholder", "trigger", "multiline", "compact", "required",
    "maxlength", "minlength", "pattern", "disabled", "readonly",
    "error-message", "edit-label", "commit-label", "cancel-label"
  ];

  constructor() {
    super()
    this._initFormControl()
    this._editing = false
    this._pendingValue = ""

    /* Set once the value was changed by the user or through the property. */
    this._dirty = false

    this._inputId = nextId("mjie-input")
    this._errorId = nextId("mjie-error")

    /* Shadow references; null until the first render. */
    this._displayWrap = null
    this._displaySlot = null
    this._displayText = null
    this._editTrigger = null
    this._editWrap = null
    this._errorEl = null
    this._activeInput = null
  }

  render() {
    const markup = html`
      <div class="display-wrap" part="display-wrap">
        <slot name="display">
          <span class="display-text" part="display-text"></span>
        </slot>
        <button class="edit-trigger" part="edit-trigger" type="button">
          <slot name="edit-icon">✏</slot>
        </button>
      </div>
      <div class="edit-wrap" part="edit-wrap" hidden></div>
      <span class="error" part="error" id="${this._errorId}" role="alert"></span>
    `
    return markup
  }

  afterRender() {
    this._displayWrap = this.$(".display-wrap")
    this._displaySlot = this.$("slot[name='display']")
    this._displayText = this.$(".display-text")
    this._editTrigger = this.$(".edit-trigger")
    this._editWrap = this.$(".edit-wrap")
    this._errorEl = this.$(".error")
    this._activeInput = null

    /* The value attribute is the initial value until the user edits. */
    if (this._dirty === false && this.hasAttribute("value") === true) {
      this._setFormValue(this.getAttribute("value"))
    }
    this._syncDisplay()

    this.listen(this._editTrigger, "click", this._onTriggerClick.bind(this))
    this.listen(this._displaySlot, "click", this._onDisplayClick.bind(this))

    /* The edit controls are rebuilt per edit, so their events are delegated. */
    this.listen(this._editWrap, "keydown", this._onEditKeydown.bind(this))
    this.listen(this._editWrap, "input", this._onEditInput.bind(this))
    this.listen(this._editWrap, "click", this._onEditClick.bind(this))

    this.listen(document, "focusin", this._onDocumentFocusin.bind(this))
    this.listen(this, "invalid", this._onInvalid.bind(this))
    return
  }

  onDisconnected() {
    /* The shadow DOM is rebuilt in display mode on the next connect. */
    if (this._editing === true) {
      this._editing = false
      this._activeInput = null
      this.emit("mj-edit-cancel", { value: this._value })
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "value") {
      /* Like a native control, the attribute stops applying once edited. */
      if (this._dirty === false) {
        this._setFormValue(newValue !== null ? newValue : "")
      }
    }

    if (this._displayText === undefined || this._displayText === null) {
      return
    }

    if ((name === "disabled" || name === "readonly") && newValue !== null && this._editing === true) {
      this._cancelEdit(false)
    }

    this._syncDisplay()

    if (name === "required" || name === "minlength" || name === "maxlength" || name === "pattern") {
      this._refreshValidity()
    }
    return
  }

  /* ----- display mode ----- */

  _syncDisplay() {
    const val = this._value !== null && this._value !== undefined ? String(this._value) : ""
    const label = this.getAttribute("label") || ""
    const editLabel = this.getAttribute("edit-label") || t("mj.inlineEdit.edit")

    if (val.length > 0) {
      this._displayText.textContent = val
      this._displayText.removeAttribute("data-empty")
    } else {
      this._displayText.textContent = this.getAttribute("placeholder") || EMPTY_DISPLAY
      this._displayText.setAttribute("data-empty", "")
    }
    this._displayText.title = val

    /* The pencil button is the keyboard entry point; name it for its field. */
    const subject = label.length > 0 ? label : val
    this._editTrigger.setAttribute("aria-label", subject.length > 0 ? `${editLabel} ${subject}` : editLabel)
    return
  }

  _canEdit() {
    const allowed = this.hasAttribute("disabled") === false && this.hasAttribute("readonly") === false
    return allowed
  }

  _onDisplayClick(event) {
    const trigger = this.getAttribute("trigger") || "click"
    if (trigger === "click") {
      this._enterEditMode()
    }
    return
  }

  _onTriggerClick(event) {
    this._enterEditMode()
    return
  }

  /*
   * Focus moved somewhere in the document. When it left this component the
   * edit is cancelled, and focus is left where the user put it.
   * `composedPath` is used because `event.target` is retargeted to the
   * outermost shadow host when this component is inside another shadow root.
   */
  _onDocumentFocusin(event) {
    if (this._editing === false) {
      return
    }
    const inside = event.composedPath().indexOf(this) !== -1
    if (inside === false) {
      this._cancelEdit(false)
    }
    return
  }

  /* ----- edit mode ----- */

  _enterEditMode() {
    if (this._editing === true || this._canEdit() === false) {
      return
    }
    const proceed = this.emit("mj-edit-start", { value: this._value }, { cancelable: true })
    if (proceed === false) {
      return
    }

    this._editing = true
    this._pendingValue = this._value

    const multiline = this.hasAttribute("multiline")
    const compact = this.hasAttribute("compact")
    const commitLabel = this.getAttribute("commit-label") || t("mj.inlineEdit.save")
    const cancelLabel = this.getAttribute("cancel-label") || t("mj.inlineEdit.cancel")

    let inputEl = null
    if (multiline === true) {
      inputEl = document.createElement("textarea")
    } else {
      inputEl = document.createElement("input")
      inputEl.type = "text"
    }
    inputEl.setAttribute("part", "input")
    inputEl.id = this._inputId
    inputEl.value = this._value
    inputEl.setAttribute("aria-label", this.getAttribute("label") || this.getAttribute("edit-label") || t("mj.inlineEdit.editValue"))
    if (this.hasAttribute("required") === true) {
      inputEl.setAttribute("aria-required", "true")
    }

    const maxlength = this.getAttribute("maxlength")
    if (maxlength !== null) {
      inputEl.setAttribute("maxlength", maxlength)
    }

    this._editWrap.textContent = ""
    this._editWrap.appendChild(inputEl)

    if (compact === false) {
      const actions = document.createElement("div")
      actions.className = "actions"
      actions.setAttribute("part", "actions")

      const commitButton = document.createElement("button")
      commitButton.type = "button"
      commitButton.className = "action-btn commit-btn"
      commitButton.setAttribute("part", "commit-button")
      commitButton.textContent = commitLabel

      const cancelButton = document.createElement("button")
      cancelButton.type = "button"
      cancelButton.className = "action-btn cancel-btn"
      cancelButton.setAttribute("part", "cancel-button")
      cancelButton.textContent = cancelLabel

      actions.appendChild(commitButton)
      actions.appendChild(cancelButton)
      this._editWrap.appendChild(actions)
    }

    this._activeInput = inputEl
    this._displayWrap.hidden = true
    this._editWrap.hidden = false

    inputEl.focus()
    inputEl.select()
    return
  }

  _onEditInput(event) {
    if (this._activeInput !== null) {
      this._pendingValue = this._activeInput.value
    }
    return
  }

  _onEditClick(event) {
    const button = event.target.closest(".action-btn")
    if (button === null) {
      return
    }
    if (button.classList.contains("commit-btn") === true) {
      this._commitEdit()
    } else {
      this._cancelEdit(true)
    }
    return
  }

  _onEditKeydown(event) {
    if (event.target !== this._activeInput) {
      return
    }

    const multiline = this.hasAttribute("multiline")
    const key = event.key
    const withModifier = event.ctrlKey === true || event.metaKey === true

    if (key === "Enter" && event.isComposing === false && (multiline === false || withModifier === true)) {
      /*
       * Enter commits the edit. The default is prevented so an enclosing
       * <mj-form> does not treat the key as an implicit submission.
       */
      event.preventDefault()
      this._commitEdit()
    } else if (key === "Escape") {
      /* Escape belongs to the edit, not to an enclosing dialog. */
      event.preventDefault()
      event.stopPropagation()
      this._cancelEdit(true)
    }
    return
  }

  _commitEdit() {
    if (this._editing === false || this._activeInput === null) {
      return
    }

    const newValue = this._activeInput.value
    const errMsg = this._validateValue(newValue, true)

    if (errMsg.length > 0) {
      this._errorEl.textContent = errMsg
      this._errorEl.setAttribute("data-visible", "")
      this._activeInput.setAttribute("aria-invalid", "true")
      this._activeInput.setAttribute("aria-describedby", this._errorId)
      this.emit("mj-invalid", { validationMessage: errMsg })
      return
    }

    const previousValue = this._value

    if (newValue !== previousValue) {
      /*
       * The value is applied before the event so `event.target.value` is
       * the new value in every listener, and rolled back when the event is
       * cancelled. The bridged native `change` is dispatched here, after a
       * successful commit only, instead of by `emit`.
       */
      this._setFormValue(newValue)

      const changeEvent = new CustomEvent("mj-change", {
        detail: { value: newValue, previousValue: previousValue },
        bubbles: true,
        cancelable: true,
        composed: true
      })
      const proceed = this.dispatchEvent(changeEvent)

      if (proceed === false) {
        this._setFormValue(previousValue)
        return
      }

      this._dirty = true
      this.dispatchEvent(new Event("change", { bubbles: true, composed: true }))
    }

    this._exitEditMode(true)
    this._syncDisplay()
    return
  }

  /*
   * Leave edit mode without saving. `restoreFocus` is true for the explicit
   * exits (Escape, the Cancel button) and false when focus already moved
   * elsewhere or the component was disabled.
   */
  _cancelEdit(restoreFocus) {
    if (this._editing === false) {
      return
    }
    this.emit("mj-edit-cancel", { value: this._value })
    this._exitEditMode(restoreFocus)
    return
  }

  _exitEditMode(restoreFocus) {
    this._editing = false
    this._activeInput = null
    this._editWrap.hidden = true
    this._editWrap.textContent = ""
    this._displayWrap.hidden = false
    this._errorEl.textContent = ""
    this._errorEl.removeAttribute("data-visible")

    if (restoreFocus === true && this._canEdit() === true) {
      this._editTrigger.focus()
    }
    return
  }

  /* ----- validation ----- */

  /*
   * Compile the `pattern` attribute the way a native input does: the whole
   * value must match. An invalid expression is ignored, as it is natively.
   */
  _compilePattern() {
    const pattern = this.getAttribute("pattern")
    let expression = null

    if (pattern !== null && pattern.length > 0) {
      try {
        expression = new RegExp(`^(?:${pattern})$`, "u")
      } catch (error) {
        expression = null
      }
    }
    return expression
  }

  /*
   * Return the validation message for `val`, or the empty string when it is
   * acceptable. `includeRequired` adds the required check, which the form
   * mixin performs itself for the committed value.
   */
  _validateValue(val, includeRequired) {
    const text = val !== null && val !== undefined ? String(val) : ""
    const custom = this.getAttribute("error-message") || ""
    const minlength = parseInt(this.getAttribute("minlength") || "", 10)
    const maxlength = parseInt(this.getAttribute("maxlength") || "", 10)
    let message = ""

    if (includeRequired === true && this.hasAttribute("required") === true && text.trim().length === 0) {
      message = this.getAttribute("required-message") || t("core.required")
    } else if (isNaN(minlength) === false && text.length > 0 && text.length < minlength) {
      message = t("mj.inlineEdit.minLength", { count: minlength })
    } else if (isNaN(maxlength) === false && text.length > maxlength) {
      message = t("mj.inlineEdit.maxLength", { count: maxlength })
    } else if (text.length > 0) {
      const expression = this._compilePattern()
      if (expression !== null && expression.test(text) === false) {
        message = t("mj.inlineEdit.patternMismatch")
      }
    }

    if (message.length > 0 && custom.length > 0) {
      message = custom
    }
    return message
  }

  /* The commit-time rules also apply to an initial or programmatic value. */
  _customValidity() {
    const message = this._validateValue(this._value, false)
    return message
  }

  _validationAnchor() {
    let anchor = this._editTrigger
    if (this._activeInput !== null && this._activeInput !== undefined) {
      anchor = this._activeInput
    }
    return anchor
  }

  /*
   * Show the inline error state for the committed value and return whether
   * the control is valid. <mj-form> calls this on a failed submit.
   */
  showValidation() {
    this._refreshValidity()

    /* An invalid control raises `invalid`, which renders the error. */
    const valid = this.checkValidity()
    if (valid === true && this._errorEl !== undefined && this._errorEl !== null && this._editing === false) {
      this._errorEl.textContent = ""
      this._errorEl.removeAttribute("data-visible")
    }
    return valid
  }

  /* A failed checkValidity() / reportValidity() / form submit. */
  _onInvalid(event) {
    if (this._errorEl === undefined || this._errorEl === null || this._editing === true) {
      return
    }
    const message = this.validationMessage
    if (message.length > 0) {
      const custom = this.getAttribute("error-message") || ""
      const displayMessage = custom.length > 0 ? custom : message
      this._errorEl.textContent = displayMessage
      this._errorEl.setAttribute("data-visible", "")
      this.emit("mj-invalid", { validationMessage: displayMessage })
    }
    return
  }

  reportValidity() {
    const valid = this.showValidation()
    return valid
  }

  /* ----- scriptable API ----- */

  get editing() {
    return this._editing
  }

  get pendingValue() {
    return this._pendingValue
  }

  get value() {
    return this._value
  }

  set value(next) {
    this._dirty = true
    this._setFormValue(next !== null && next !== undefined ? String(next) : "")
    if (this._displayText !== undefined && this._displayText !== null) {
      this._syncDisplay()
    }
    return
  }

  onFormReset(initial) {
    this._dirty = false
    if (this._displayText !== undefined && this._displayText !== null) {
      if (this._editing === true) {
        this._cancelEdit(false)
      }
      this._errorEl.textContent = ""
      this._errorEl.removeAttribute("data-visible")
      this._syncDisplay()
    }
    return
  }

  focus(options) {
    if (this._activeInput !== null && this._activeInput !== undefined) {
      this._activeInput.focus(options)
    } else if (this._editTrigger !== undefined && this._editTrigger !== null) {
      this._editTrigger.focus(options)
    }
    return
  }
}
