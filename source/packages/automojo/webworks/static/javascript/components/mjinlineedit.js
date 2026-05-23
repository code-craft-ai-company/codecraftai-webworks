/*
 * mjinlineedit.js
 *
 * <mj-inline-edit> -- click-to-edit inline text with explicit commit/cancel
 * actions and constraint validation at commit time.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";

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

.display-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--mj-text);
  cursor: default;
}
:host(:not([readonly]):not([disabled])[trigger="click"]) .display-text {
  cursor: pointer;
}
:host(:not([readonly]):not([disabled])[trigger="click"]) .display-text:hover {
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
input[data-invalid], textarea[data-invalid] { border-color: var(--mj-color-danger); }
textarea { resize: vertical; min-height: 3rem; }

.actions {
  display: flex;
  gap: var(--mj-space-1);
  flex-shrink: 0;
}
:host([compact]) .actions { display: none; }

.action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2rem;
  height: 2rem;
  padding: 0 var(--mj-space-2);
  background: var(--mj-surface);
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
  margin-top: var(--mj-space-1);
  display: none;
}
.error[data-visible] { display: block; }

:host([disabled]) { opacity: 0.55; pointer-events: none; }
`;

export class MjInlineEdit extends FormControlMixin(MjElement) {
  static tagName = "mj-inline-edit";
  static styles = STYLES;
  static watched = [
    "value", "label", "trigger", "multiline", "compact", "required",
    "maxlength", "minlength", "pattern", "disabled", "readonly",
    "error-message", "edit-label", "commit-label", "cancel-label"
  ];

  constructor() {
    super();
    this._initFormControl();
    this._editing = false;
    this._pendingValue = "";
    this._inputId = nextId("mjie-input");
    this._errorId = nextId("mjie-error");
  }

  render() {
    const editLabel = this.getAttribute("edit-label") || "Edit";
    const commitLabel = this.getAttribute("commit-label") || "Save";
    const cancelLabel = this.getAttribute("cancel-label") || "Cancel";
    const markup = `
      <div class="display-wrap" part="display-wrap">
        <slot name="display">
          <span class="display-text" part="display-text" tabindex="0"></span>
        </slot>
        <button class="edit-trigger" part="edit-trigger" type="button" aria-label="${editLabel}">
          <slot name="edit-icon">✏</slot>
        </button>
      </div>
      <div class="edit-wrap" hidden>
        <input part="input" id="${this._inputId}" type="text" />
        <div class="actions" part="actions">
          <button class="action-btn commit-btn" part="commit-button" type="button" aria-label="${commitLabel}">${commitLabel}</button>
          <button class="action-btn cancel-btn" part="cancel-button" type="button" aria-label="${cancelLabel}">${cancelLabel}</button>
        </div>
      </div>
      <span class="error" part="error" id="${this._errorId}" role="alert"></span>
    `;
    return markup;
  }

  afterRender() {
    this._displayWrap = this.$(".display-wrap");
    this._displayText = this.$(".display-text");
    this._editTrigger = this.$(".edit-trigger");
    this._editWrap = this.$(".edit-wrap");
    this._errorEl = this.$(".error");

    this._syncDisplay();

    this.listen(this._editTrigger, "click", this._onTriggerClick.bind(this));
    this.listen(this._editTrigger, "keydown", this._onTriggerKeydown.bind(this));
    this.listen(this._displayText, "click", this._onDisplayClick.bind(this));
    this.listen(this._displayText, "keydown", this._onDisplayKeydown.bind(this));
    this.listen(document, "focusin", this._onDocumentFocusin.bind(this));
    return;
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._displayText === undefined) {
      return;
    }
    this._syncDisplay();
    if (name === "edit-label") {
      this._editTrigger.setAttribute("aria-label", newValue || "Edit");
    }
    return;
  }

  _syncDisplay() {
    const val = this._value || "";
    this._displayText.textContent = val.length > 0 ? val : (this.getAttribute("placeholder") || "—");
    this._displayText.title = val;
    this._editTrigger.setAttribute("aria-label", `${this.getAttribute("edit-label") || "Edit"} ${val}`);
    return;
  }

  _onDisplayClick(event) {
    const trigger = this.getAttribute("trigger") || "click";
    if (trigger === "click" && !this.hasAttribute("disabled") && !this.hasAttribute("readonly")) {
      this._enterEditMode();
    }
    return;
  }

  _onDisplayKeydown(event) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      this._enterEditMode();
    }
    return;
  }

  _onTriggerClick(event) {
    this._enterEditMode();
    return;
  }

  _onTriggerKeydown(event) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      this._enterEditMode();
    }
    return;
  }

  _onDocumentFocusin(event) {
    if (!this._editing) {
      return;
    }
    if (!this.contains(event.target)) {
      this._cancelEdit();
    }
    return;
  }

  _enterEditMode() {
    if (this._editing) {
      return;
    }
    const notCanceled = this.emit("mj-edit-start", { value: this._value }, { cancelable: true });
    if (!notCanceled) {
      return;
    }

    this._editing = true;
    this._pendingValue = this._value;
    this._displayWrap.hidden = true;
    this._editWrap.hidden = false;

    const multiline = this.hasAttribute("multiline");
    this._editWrap.innerHTML = "";

    let inputEl;
    if (multiline) {
      inputEl = document.createElement("textarea");
    } else {
      inputEl = document.createElement("input");
      inputEl.type = "text";
    }
    inputEl.setAttribute("part", "input");
    inputEl.id = this._inputId;
    inputEl.value = this._value;
    inputEl.setAttribute("aria-label", this.getAttribute("label") || "Edit value");

    const maxlength = this.getAttribute("maxlength");
    if (maxlength !== null) {
      inputEl.setAttribute("maxlength", maxlength);
    }

    const compact = this.hasAttribute("compact");
    const commitLabel = this.getAttribute("commit-label") || "Save";
    const cancelLabel = this.getAttribute("cancel-label") || "Cancel";

    const actionsHtml = compact ? "" : `
      <div class="actions" part="actions">
        <button class="action-btn commit-btn" part="commit-button" type="button" aria-label="${commitLabel}">${commitLabel}</button>
        <button class="action-btn cancel-btn" part="cancel-button" type="button" aria-label="${cancelLabel}">${cancelLabel}</button>
      </div>
    `;

    this._editWrap.appendChild(inputEl);
    if (!compact) {
      const actionsDiv = document.createElement("div");
      actionsDiv.className = "actions";
      actionsDiv.setAttribute("part", "actions");
      actionsDiv.innerHTML = `
        <button class="action-btn commit-btn" part="commit-button" type="button" aria-label="${commitLabel}">${commitLabel}</button>
        <button class="action-btn cancel-btn" part="cancel-button" type="button" aria-label="${cancelLabel}">${cancelLabel}</button>
      `;
      this._editWrap.appendChild(actionsDiv);
      actionsDiv.querySelector(".commit-btn").addEventListener("click", () => this._commitEdit());
      actionsDiv.querySelector(".cancel-btn").addEventListener("click", () => this._cancelEdit());
    }

    this._activeInput = inputEl;
    inputEl.addEventListener("keydown", this._onInputKeydown.bind(this));
    inputEl.addEventListener("input", () => { this._pendingValue = this._activeInput.value; });

    inputEl.focus();
    if (inputEl.select !== undefined) {
      inputEl.select();
    }
    return;
  }

  _onInputKeydown(event) {
    const multiline = this.hasAttribute("multiline");
    const key = event.key;

    if (!multiline && key === "Enter") {
      event.preventDefault();
      this._commitEdit();
      return;
    }
    if (multiline && key === "Enter" && (event.ctrlKey || event.metaKey)) {
      event.preventDefault();
      this._commitEdit();
      return;
    }
    if (key === "Escape") {
      this._cancelEdit();
      return;
    }
    return;
  }

  _commitEdit() {
    const newValue = this._activeInput.value;
    const errMsg = this._validatePending(newValue);

    if (errMsg.length > 0) {
      this._errorEl.textContent = errMsg;
      this._errorEl.setAttribute("data-visible", "");
      this._activeInput.setAttribute("data-invalid", "");
      this._activeInput.setAttribute("aria-describedby", this._errorId);
      this.emit("mj-invalid", { validationMessage: errMsg });
      return;
    }

    const previousValue = this._value;

    if (newValue !== previousValue) {
      const notCanceled = this.emit("mj-change", { value: newValue, previousValue }, { cancelable: true });
      if (!notCanceled) {
        return;
      }
      this._setFormValue(newValue);
    }

    this._exitEditMode();
    this._syncDisplay();
    return;
  }

  _cancelEdit() {
    this.emit("mj-edit-cancel", { value: this._value });
    this._exitEditMode();
    return;
  }

  _exitEditMode() {
    this._editing = false;
    this._editWrap.hidden = true;
    this._displayWrap.hidden = false;
    this._errorEl.removeAttribute("data-visible");
    this._editTrigger.focus();
    return;
  }

  _validatePending(val) {
    const required = this.hasAttribute("required");
    const minlength = this.getAttribute("minlength");
    const maxlength = this.getAttribute("maxlength");
    const pattern = this.getAttribute("pattern");

    if (required && val.trim().length === 0) {
      return this.getAttribute("error-message") || "This field is required.";
    }
    if (minlength !== null && val.length < parseInt(minlength, 10)) {
      return this.getAttribute("error-message") || `Minimum ${minlength} characters required.`;
    }
    if (maxlength !== null && val.length > parseInt(maxlength, 10)) {
      return this.getAttribute("error-message") || `Maximum ${maxlength} characters allowed.`;
    }
    if (pattern !== null && pattern.length > 0) {
      const re = new RegExp(pattern);
      if (!re.test(val)) {
        return this.getAttribute("error-message") || "Value does not match the required format.";
      }
    }
    return "";
  }

  get editing() {
    return this._editing;
  }

  get pendingValue() {
    return this._pendingValue;
  }

  get value() {
    return this._value;
  }

  set value(next) {
    this._setFormValue(next);
    if (this._displayText !== undefined) {
      this._syncDisplay();
    }
    return;
  }

  onFormReset(initial) {
    if (this._editing) {
      this._cancelEdit();
    }
    if (this._displayText !== undefined) {
      this._syncDisplay();
    }
    return;
  }

  focus() {
    if (this._editTrigger !== undefined) {
      this._editTrigger.focus();
    }
    return;
  }
}
