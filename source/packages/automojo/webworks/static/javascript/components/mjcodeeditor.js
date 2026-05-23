/*
 * mjcodeeditor.js
 *
 * <mj-code-editor> -- syntax-highlighted code authoring with a plain
 * <textarea> fallback, line numbers, proper Tab handling, and form participation.
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

.outer {
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-md);
  overflow: hidden;
  transition: border-color var(--mj-motion-fast) var(--mj-motion-ease);
}
.outer[data-focused] { border-color: var(--mj-accent); outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: var(--mj-focus-ring-offset); }
.outer[data-invalid] { border-color: var(--mj-color-danger); }

.toolbar-slot { border-bottom: 1px solid var(--mj-border); background: var(--mj-bg-subtle); }
.toolbar-slot:empty { display: none; }

.container {
  display: flex;
  min-height: 200px;
  position: relative;
}

.gutter {
  width: 3rem;
  padding: var(--mj-space-2) var(--mj-space-1);
  background: var(--mj-bg-subtle);
  border-inline-end: 1px solid var(--mj-border);
  font-family: var(--mj-font-mono);
  font-size: var(--mj-font-size-sm);
  line-height: 1.6;
  color: var(--mj-text-muted);
  text-align: end;
  user-select: none;
  overflow: hidden;
  flex-shrink: 0;
}
.gutter[hidden] { display: none; }
.gutter-line { display: block; }

.editor-area {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.highlight-layer {
  position: absolute;
  inset: 0;
  padding: var(--mj-space-2) var(--mj-space-3);
  margin: 0;
  font-family: var(--mj-font-mono);
  font-size: var(--mj-font-size-sm);
  line-height: 1.6;
  color: var(--mj-text);
  background: var(--mj-surface);
  white-space: pre;
  overflow: auto;
  tab-size: 4;
  pointer-events: none;
}

textarea {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  padding: var(--mj-space-2) var(--mj-space-3);
  box-sizing: border-box;
  font-family: var(--mj-font-mono);
  font-size: var(--mj-font-size-sm);
  line-height: 1.6;
  color: transparent;
  caret-color: var(--mj-text);
  background: transparent;
  border: none;
  outline: none;
  resize: none;
  overflow: auto;
  tab-size: 4;
  white-space: pre;
  spellcheck: false;
}
:host([word-wrap]) textarea { white-space: pre-wrap; word-break: break-all; }
:host([word-wrap]) .highlight-layer { white-space: pre-wrap; word-break: break-all; }

.below { margin-top: var(--mj-space-1); }
.help { font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }
.help:empty { display: none; }
.error { font-size: var(--mj-font-size-sm); color: var(--mj-color-danger); display: none; }
.error[data-visible] { display: block; }

.exit-announce {
  position: absolute;
  width: 1px; height: 1px;
  overflow: hidden;
  clip: rect(0,0,0,0);
}

:host([disabled]) .outer { opacity: 0.55; pointer-events: none; }
`;

export class MjCodeEditor extends FormControlMixin(MjElement) {
  static tagName = "mj-code-editor";
  static styles = STYLES;
  static watched = [
    "label", "placeholder", "help-text", "error-message", "value",
    "language", "line-numbers", "word-wrap", "tab-size", "tab-inserts-spaces",
    "required", "disabled", "readonly", "maxlength", "minlength", "size"
  ];

  constructor() {
    super();
    this._initFormControl();
    this._highlighter = null;
    this._highlightDebounce = null;
    this._exitMode = false;
    this._prevValue = "";
    this._textareaId = nextId("mjce-ta");
    this._helpId = nextId("mjce-help");
    this._errorId = nextId("mjce-error");
    this._announceId = nextId("mjce-announce");
  }

  render() {
    const markup = `
      <label class="label" part="label" for="${this._textareaId}"></label>
      <div class="outer" part="outer">
        <div class="toolbar-slot" part="toolbar"><slot name="toolbar"></slot></div>
        <div class="container" part="container">
          <div class="gutter" part="gutter" aria-hidden="true"></div>
          <div class="editor-area">
            <pre class="highlight-layer" part="highlight-layer" aria-hidden="true"></pre>
            <textarea
              part="textarea"
              id="${this._textareaId}"
              role="textbox"
              aria-multiline="true"
              spellcheck="false"
              autocorrect="off"
              autocapitalize="off"
            ></textarea>
          </div>
        </div>
      </div>
      <div class="exit-announce" id="${this._announceId}" aria-live="polite" role="status"></div>
      <div class="below">
        <span class="help" part="help" id="${this._helpId}"></span>
        <span class="error" part="error" id="${this._errorId}" role="alert"></span>
      </div>
    `;
    return markup;
  }

  afterRender() {
    this._labelEl = this.$(".label");
    this._outerEl = this.$(".outer");
    this._textarea = this.$("textarea");
    this._gutter = this.$(".gutter");
    this._highlightLayer = this.$(".highlight-layer");
    this._helpEl = this.$(".help");
    this._errorEl = this.$(".error");
    this._announceEl = this.$(".exit-announce");

    this._syncAll();

    this.listen(this._textarea, "input", this._onInput.bind(this));
    this.listen(this._textarea, "change", this._onChange.bind(this));
    this.listen(this._textarea, "focus", this._onFocus.bind(this));
    this.listen(this._textarea, "blur", this._onBlur.bind(this));
    this.listen(this._textarea, "keydown", this._onKeydown.bind(this));
    this.listen(this._textarea, "scroll", this._onScroll.bind(this));
    return;
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._textarea === undefined) {
      return;
    }
    this._syncAll();
    return;
  }

  _syncAll() {
    const label = this.getAttribute("label") || "";
    const placeholder = this.getAttribute("placeholder") || "";
    const helpText = this.getAttribute("help-text") || "";
    const disabled = this.hasAttribute("disabled");
    const readonly = this.hasAttribute("readonly");
    const required = this.hasAttribute("required");
    const lineNumbers = this.getAttribute("line-numbers") !== "false";
    const tabSize = parseInt(this.getAttribute("tab-size") || "4", 10);
    const maxlength = this.getAttribute("maxlength");
    const minlength = this.getAttribute("minlength");

    this._labelEl.textContent = label;
    this._textarea.placeholder = placeholder;
    this._textarea.disabled = disabled;
    this._textarea.readOnly = readonly;
    this._textarea.setAttribute("aria-required", required ? "true" : "false");
    this._textarea.style.tabSize = String(tabSize);
    this._highlightLayer.style.tabSize = String(tabSize);
    this._gutter.hidden = !lineNumbers;
    this._helpEl.textContent = helpText;

    if (maxlength !== null) {
      this._textarea.setAttribute("maxlength", maxlength);
    } else {
      this._textarea.removeAttribute("maxlength");
    }
    if (minlength !== null) {
      this._textarea.setAttribute("minlength", minlength);
    } else {
      this._textarea.removeAttribute("minlength");
    }

    const ids = [];
    if (helpText.length > 0) {
      ids.push(this._helpId);
    }
    if (this._errorEl.hasAttribute("data-visible")) {
      ids.push(this._errorId);
    }
    if (ids.length > 0) {
      this._textarea.setAttribute("aria-describedby", ids.join(" "));
    } else {
      this._textarea.removeAttribute("aria-describedby");
    }
    return;
  }

  _onInput(event) {
    const val = this._textarea.value.replace(/\r\n/g, "\n");
    this._setFormValue(val);
    this._exitMode = false;

    this._updateGutter(val);

    if (this._highlightDebounce !== null) {
      clearTimeout(this._highlightDebounce);
    }
    const debounceMs = 100;
    this._highlightDebounce = setTimeout(() => {
      this._updateHighlight(val);
    }, debounceMs);

    const lineCount = val.split("\n").length;
    this.emit("mj-input", { value: val, lineCount });
    return;
  }

  _onChange(event) {
    const val = this._textarea.value;
    if (val !== this._prevValue) {
      this._prevValue = val;
      const lineCount = val.split("\n").length;
      this.emit("mj-change", { value: val, lineCount });
    }
    return;
  }

  _onFocus(event) {
    this._outerEl.setAttribute("data-focused", "");
    this._exitMode = false;
    return;
  }

  _onBlur(event) {
    this._outerEl.removeAttribute("data-focused");
    this._exitMode = false;
    this._announceEl.textContent = "";
    this._runValidation();
    return;
  }

  _onScroll(event) {
    this._highlightLayer.scrollTop = this._textarea.scrollTop;
    this._highlightLayer.scrollLeft = this._textarea.scrollLeft;
    return;
  }

  _onKeydown(event) {
    const key = event.key;

    if (key === "Escape") {
      this._exitMode = true;
      this._announceEl.textContent = "Press Tab to move focus out of the code editor.";
      return;
    }

    if (key === "Tab") {
      if (this._exitMode) {
        this._exitMode = false;
        this._announceEl.textContent = "";
        return;
      }
      event.preventDefault();
      this._handleTab(event.shiftKey);
      return;
    }
    return;
  }

  _handleTab(isShift) {
    const tabInsertSpaces = this.getAttribute("tab-inserts-spaces") !== "false";
    const tabSize = parseInt(this.getAttribute("tab-size") || "4", 10);
    const indent = tabInsertSpaces ? " ".repeat(tabSize) : "\t";

    const start = this._textarea.selectionStart;
    const end = this._textarea.selectionEnd;
    const val = this._textarea.value;

    if (!isShift) {
      this._textarea.setRangeText(indent, start, end, "end");
    } else {
      const lineStart = val.lastIndexOf("\n", start - 1) + 1;
      const linePrefix = val.substring(lineStart, start);
      if (tabInsertSpaces) {
        const toRemove = Math.min(tabSize, linePrefix.match(/^ */)[0].length);
        if (toRemove > 0) {
          this._textarea.setRangeText("", lineStart, lineStart + toRemove, "preserve");
        }
      } else {
        if (linePrefix.startsWith("\t")) {
          this._textarea.setRangeText("", lineStart, lineStart + 1, "preserve");
        }
      }
    }

    const newVal = this._textarea.value.replace(/\r\n/g, "\n");
    this._setFormValue(newVal);
    this._updateGutter(newVal);
    this._updateHighlight(newVal);
    return;
  }

  _updateGutter(val) {
    if (this._gutter.hidden) {
      return;
    }
    const lines = val.split("\n");
    const fragments = [];
    for (let i = 0; i < lines.length; i = i + 1) {
      fragments.push(`<span class="gutter-line">${i + 1}</span>`);
    }
    this._gutter.innerHTML = fragments.join("");
    return;
  }

  _updateHighlight(val) {
    if (this._highlighter !== null) {
      try {
        const lang = this.getAttribute("language") || "plaintext";
        const html = this._highlighter(val, lang);
        this._highlightLayer.innerHTML = html;
      } catch (err) {
        console.error("[mj-code-editor] highlighter error:", err);
        this._highlightLayer.textContent = val;
      }
    } else {
      this._highlightLayer.textContent = val;
    }
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
      this._outerEl.setAttribute("data-invalid", "");
      this._textarea.setAttribute("aria-invalid", "true");
      this.emit("mj-invalid", { validationMessage: displayMsg });
    } else {
      this._errorEl.removeAttribute("data-visible");
      this._outerEl.removeAttribute("data-invalid");
      this._textarea.setAttribute("aria-invalid", "false");
    }
    return;
  }

  _validationAnchor() {
    return this._textarea;
  }

  onFormReset(initial) {
    if (this._textarea !== undefined) {
      this._textarea.value = initial;
      this._setFormValue(initial);
      this._updateGutter(initial);
      this._updateHighlight(initial);
      this._errorEl.removeAttribute("data-visible");
      this._outerEl.removeAttribute("data-invalid");
      this._textarea.setAttribute("aria-invalid", "false");
    }
    return;
  }

  get highlighter() {
    return this._highlighter;
  }

  set highlighter(fn) {
    if (typeof fn === "function") {
      this._highlighter = fn;
      if (this._textarea !== undefined) {
        this._updateHighlight(this._textarea.value);
      }
    }
    return;
  }

  get lineCount() {
    if (this._textarea === undefined) {
      return 0;
    }
    return this._textarea.value.split("\n").length;
  }

  get value() {
    return this._value;
  }

  set value(next) {
    this._setFormValue(next);
    if (this._textarea !== undefined) {
      this._textarea.value = next;
      this._updateGutter(next);
      this._updateHighlight(next);
    }
    return;
  }

  focus() {
    if (this._textarea !== undefined) {
      this._textarea.focus();
    }
    return;
  }
}
