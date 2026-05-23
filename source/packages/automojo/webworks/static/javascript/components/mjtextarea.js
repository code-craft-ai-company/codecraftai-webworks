/*
 * mjtextarea.js
 *
 * <mj-textarea> -- multi-line text entry with optional auto-grow,
 * configurable min/max rows, and character/word counter.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";

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

.wrapper {
  display: block;
  background: var(--mj-surface);
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-md);
  transition: border-color var(--mj-motion-fast) var(--mj-motion-ease);
}
.wrapper:focus-within {
  border-color: var(--mj-accent);
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.wrapper[data-invalid] { border-color: var(--mj-color-danger); }

textarea {
  display: block;
  width: 100%;
  box-sizing: border-box;
  padding: var(--mj-space-2) var(--mj-space-3);
  font: inherit;
  font-size: var(--mj-font-size-md);
  :host([size="sm"]) & { font-size: var(--mj-font-size-sm); }
  :host([size="lg"]) & { font-size: var(--mj-font-size-lg); }
  color: var(--mj-text);
  background: transparent;
  border: none;
  outline: none;
  resize: vertical;
  line-height: var(--mj-line-height);
}
textarea::placeholder { color: var(--mj-text-muted); }
textarea[data-no-resize] { resize: none; }
textarea[data-auto-grow] { resize: none; overflow: hidden; }

.footer-slot { padding: 0 var(--mj-space-3) var(--mj-space-2); }

.below {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--mj-space-2);
  margin-top: var(--mj-space-1);
}
.help { font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }
.help:empty { display: none; }
.error { font-size: var(--mj-font-size-sm); color: var(--mj-color-danger); display: none; }
.error[data-visible] { display: block; }
.counter { font-size: var(--mj-font-size-xs); color: var(--mj-text-muted); text-align: end; flex-shrink: 0; }
.counter[hidden] { display: none; }
.counter[data-near-limit] { color: var(--mj-color-warning); }

:host([disabled]) .wrapper { opacity: 0.55; pointer-events: none; }
`;

export class MjTextarea extends FormControlMixin(MjElement) {
  static tagName = "mj-textarea";
  static styles = STYLES;
  static watched = [
    "label", "placeholder", "help-text", "error-message", "value",
    "rows", "min-rows", "max-rows", "auto-grow", "no-resize",
    "maxlength", "minlength", "count-words", "required", "disabled",
    "readonly", "spellcheck", "autocomplete", "wrap", "size"
  ];

  constructor() {
    super();
    this._initFormControl();
    this._prevValue = "";
    this._rafPending = false;
    this._textareaId = nextId("mjta-ta");
    this._helpId = nextId("mjta-help");
    this._errorId = nextId("mjta-error");
    this._counterId = nextId("mjta-counter");
  }

  render() {
    const markup = `
      <label class="label" part="label" for="${this._textareaId}"></label>
      <div class="wrapper" part="wrapper">
        <textarea
          part="textarea"
          id="${this._textareaId}"
          rows="3"
        ></textarea>
        <div class="footer-slot"><slot name="footer"></slot></div>
      </div>
      <div class="below">
        <span>
          <span class="help" part="help" id="${this._helpId}"></span>
          <span class="error" part="error" id="${this._errorId}" role="alert"></span>
        </span>
        <span class="counter" part="counter" id="${this._counterId}" role="status" aria-live="polite" hidden></span>
      </div>
    `;
    return markup;
  }

  afterRender() {
    this._ta = this.$("textarea");
    this._labelEl = this.$(".label");
    this._wrapEl = this.$(".wrapper");
    this._helpEl = this.$(".help");
    this._errorEl = this.$(".error");
    this._counterEl = this.$(".counter");

    this._syncAll();

    this.listen(this._ta, "input", this._onInput.bind(this));
    this.listen(this._ta, "change", this._onChange.bind(this));
    this.listen(this._ta, "blur", this._onBlur.bind(this));
    return;
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._ta === undefined) {
      return;
    }
    this._syncAll();
    return;
  }

  _syncAll() {
    const label = this.getAttribute("label") || "";
    const placeholder = this.getAttribute("placeholder") || "";
    const helpText = this.getAttribute("help-text") || "";
    const rows = parseInt(this.getAttribute("rows") || "3", 10);
    const disabled = this.hasAttribute("disabled");
    const readonly = this.hasAttribute("readonly");
    const required = this.hasAttribute("required");
    const autoGrow = this.hasAttribute("auto-grow");
    const noResize = this.hasAttribute("no-resize");
    const maxlength = this.getAttribute("maxlength");
    const minlength = this.getAttribute("minlength");
    const spellcheck = this.getAttribute("spellcheck") !== "false";
    const autocomplete = this.getAttribute("autocomplete") || "on";
    const wrap = this.getAttribute("wrap") || "soft";

    this._labelEl.textContent = label;
    this._ta.placeholder = placeholder;
    this._ta.rows = rows;
    this._ta.disabled = disabled;
    this._ta.readOnly = readonly;
    this._ta.required = required;
    this._ta.spellcheck = spellcheck;
    this._ta.autocomplete = autocomplete;
    this._ta.wrap = wrap;
    this._ta.setAttribute("aria-required", required ? "true" : "false");

    if (maxlength !== null) {
      this._ta.setAttribute("maxlength", maxlength);
    } else {
      this._ta.removeAttribute("maxlength");
    }
    if (minlength !== null) {
      this._ta.setAttribute("minlength", minlength);
    } else {
      this._ta.removeAttribute("minlength");
    }

    if (autoGrow) {
      this._ta.setAttribute("data-auto-grow", "");
    } else {
      this._ta.removeAttribute("data-auto-grow");
    }
    if (noResize && !autoGrow) {
      this._ta.setAttribute("data-no-resize", "");
    } else {
      this._ta.removeAttribute("data-no-resize");
    }

    this._helpEl.textContent = helpText;
    this._updateDescribedBy();
    this._updateCounter();

    const minRows = parseInt(this.getAttribute("min-rows") || "2", 10);
    const maxRows = this.getAttribute("max-rows");
    const lineHeight = parseFloat(getComputedStyle(this._ta).lineHeight) || 20;
    this._ta.style.minHeight = `${minRows * lineHeight}px`;
    if (maxRows !== null) {
      this._ta.style.maxHeight = `${parseInt(maxRows, 10) * lineHeight}px`;
    }
    return;
  }

  _updateDescribedBy() {
    const ids = [];
    if (this._helpEl.textContent.length > 0) {
      ids.push(this._helpId);
    }
    if (this._errorEl.hasAttribute("data-visible")) {
      ids.push(this._errorId);
    }
    if (ids.length > 0) {
      this._ta.setAttribute("aria-describedby", ids.join(" "));
    } else {
      this._ta.removeAttribute("aria-describedby");
    }
    return;
  }

  _updateCounter() {
    const maxlength = this.getAttribute("maxlength");
    const countWords = this.hasAttribute("count-words");
    const val = this._ta.value;

    if (maxlength === null && !countWords) {
      this._counterEl.hidden = true;
      return;
    }
    this._counterEl.hidden = false;

    if (countWords) {
      const words = val.match(/\S+/g);
      const count = words !== null ? words.length : 0;
      this._counterEl.textContent = `${count} words`;
      if (maxlength !== null) {
        const charCount = val.length;
        const max = parseInt(maxlength, 10);
        this._counterEl.textContent = `${charCount}/${max} • ${count} words`;
        const nearLimit = charCount >= max * 0.9;
        if (nearLimit) {
          this._counterEl.setAttribute("data-near-limit", "");
        } else {
          this._counterEl.removeAttribute("data-near-limit");
        }
      }
    } else if (maxlength !== null) {
      const charCount = val.length;
      const max = parseInt(maxlength, 10);
      this._counterEl.textContent = `${charCount}/${max}`;
      const nearLimit = charCount >= max * 0.9;
      if (nearLimit) {
        this._counterEl.setAttribute("data-near-limit", "");
      } else {
        this._counterEl.removeAttribute("data-near-limit");
      }
    }
    return;
  }

  _autoGrow() {
    if (!this.hasAttribute("auto-grow")) {
      return;
    }
    if (this._rafPending) {
      return;
    }
    this._rafPending = true;
    requestAnimationFrame(() => {
      this._rafPending = false;
      this._ta.style.height = "auto";
      const scrollH = this._ta.scrollHeight;
      this._ta.style.height = `${scrollH}px`;
    });
    return;
  }

  _onInput(event) {
    const val = this._ta.value;
    this._setFormValue(val);
    this._autoGrow();
    this._updateCounter();

    const words = val.match(/\S+/g);
    const wordCount = words !== null ? words.length : 0;
    this.emit("mj-input", { value: val, charCount: val.length, wordCount });
    return;
  }

  _onChange(event) {
    const val = this._ta.value;
    if (val !== this._prevValue) {
      this._prevValue = val;
      const words = val.match(/\S+/g);
      const wordCount = words !== null ? words.length : 0;
      this.emit("mj-change", { value: val, charCount: val.length, wordCount });
    }
    return;
  }

  _onBlur(event) {
    this._runValidation();
    return;
  }

  _runValidation() {
    this._refreshValidity();
    const msg = this.validationMessage;
    const overrideMsg = this.getAttribute("error-message") || "";
    const displayMsg = overrideMsg.length > 0 ? overrideMsg : msg;

    if (displayMsg.length > 0) {
      this._errorEl.textContent = displayMsg;
      this._errorEl.setAttribute("data-visible", "");
      this._wrapEl.setAttribute("data-invalid", "");
      this._ta.setAttribute("aria-invalid", "true");
      this.emit("mj-invalid", { validationMessage: displayMsg });
    } else {
      this._errorEl.removeAttribute("data-visible");
      this._wrapEl.removeAttribute("data-invalid");
      this._ta.setAttribute("aria-invalid", "false");
    }
    this._updateDescribedBy();
    return;
  }

  _validationAnchor() {
    return this._ta;
  }

  onFormReset(initial) {
    if (this._ta !== undefined) {
      this._ta.value = initial;
      this._updateCounter();
      this._autoGrow();
      this._errorEl.removeAttribute("data-visible");
      this._wrapEl.removeAttribute("data-invalid");
      this._ta.setAttribute("aria-invalid", "false");
    }
    return;
  }

  get wordCount() {
    if (this._ta === undefined) {
      return 0;
    }
    const val = this._ta.value;
    const words = val.match(/\S+/g);
    return words !== null ? words.length : 0;
  }

  get value() {
    return this._value;
  }

  set value(next) {
    this._setFormValue(next);
    if (this._ta !== undefined) {
      this._ta.value = next;
      this._updateCounter();
      this._autoGrow();
    }
    return;
  }

  focus() {
    if (this._ta !== undefined) {
      this._ta.focus();
    }
    return;
  }
}
