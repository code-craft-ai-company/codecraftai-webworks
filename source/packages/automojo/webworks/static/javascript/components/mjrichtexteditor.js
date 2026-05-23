/*
 * mjrichtexteditor.js
 *
 * <mj-rich-text-editor> -- WYSIWYG editor with accessible toolbar,
 * contenteditable region, HTML sanitization, and form participation.
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

.editor-wrap {
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-md);
  overflow: hidden;
  transition: border-color var(--mj-motion-fast) var(--mj-motion-ease);
}
.editor-wrap[data-focused] {
  border-color: var(--mj-accent);
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.editor-wrap[data-invalid] { border-color: var(--mj-color-danger); }

.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: var(--mj-space-1);
  padding: var(--mj-space-2);
  background: var(--mj-bg-subtle);
  border-bottom: 1px solid var(--mj-border);
}
.toolbar[hidden] { display: none; }

.toolbar-group {
  display: flex;
  gap: 2px;
}
.toolbar-group + .toolbar-group {
  padding-inline-start: var(--mj-space-2);
  border-inline-start: 1px solid var(--mj-border);
  margin-inline-start: var(--mj-space-1);
}

.tb-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: var(--mj-radius-sm);
  cursor: pointer;
  color: var(--mj-text-muted);
  font-size: 0.875rem;
  font-weight: var(--mj-font-weight-bold);
  transition: background var(--mj-motion-fast);
}
.tb-btn:hover { background: var(--mj-bg-muted); color: var(--mj-text); }
.tb-btn[aria-pressed="true"] { background: var(--mj-accent); color: var(--mj-text-on-accent); }
.tb-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}

.editor {
  min-height: 200px;
  padding: var(--mj-space-3);
  color: var(--mj-text);
  background: var(--mj-surface);
  outline: none;
  line-height: var(--mj-line-height);
  position: relative;
}
.editor:empty::before {
  content: attr(data-placeholder);
  color: var(--mj-text-muted);
  pointer-events: none;
  position: absolute;
}

.toolbar-slots {
  display: flex;
  align-items: center;
  gap: var(--mj-space-1);
  margin-inline-start: auto;
}

.status-bar {
  display: flex;
  justify-content: flex-end;
  padding: var(--mj-space-1) var(--mj-space-3);
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
  background: var(--mj-bg-subtle);
  border-top: 1px solid var(--mj-border);
}
.status-bar[hidden] { display: none; }

.below { margin-top: var(--mj-space-1); }
.help { font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }
.help:empty { display: none; }
.error { font-size: var(--mj-font-size-sm); color: var(--mj-color-danger); display: none; }
.error[data-visible] { display: block; }

:host([disabled]) .editor-wrap { opacity: 0.55; pointer-events: none; }
`;

const ALLOWED_TAGS = new Set([
  "b", "i", "u", "s", "em", "strong", "a", "ul", "ol", "li",
  "h1", "h2", "h3", "h4", "blockquote", "pre", "code", "br", "p"
]);

const TOOLBAR_GROUPS = [
  [
    { cmd: "bold",          label: "Bold",          key: "b",  icon: "B"  },
    { cmd: "italic",        label: "Italic",        key: "i",  icon: "I"  },
    { cmd: "underline",     label: "Underline",     key: "u",  icon: "U"  },
    { cmd: "strikeThrough", label: "Strikethrough", key: null, icon: "S̶"  }
  ],
  [
    { cmd: "insertUnorderedList", label: "Bullet list",   key: null, icon: "• ≡" },
    { cmd: "insertOrderedList",   label: "Numbered list", key: null, icon: "1 ≡" }
  ],
  [
    { cmd: "formatBlock:h2",  label: "Heading 2", key: null, icon: "H₂" },
    { cmd: "formatBlock:h3",  label: "Heading 3", key: null, icon: "H₃" },
    { cmd: "blockquote",      label: "Blockquote", key: null, icon: "❝"  }
  ]
];

export class MjRichTextEditor extends FormControlMixin(MjElement) {
  static tagName = "mj-rich-text-editor";
  static styles = STYLES;
  static watched = [
    "label", "placeholder", "help-text", "error-message", "value",
    "toolbar", "inline", "required", "disabled", "readonly", "max-length"
  ];

  constructor() {
    super();
    this._initFormControl();
    this._sanitizer = this._defaultSanitize.bind(this);
    this._debounceTimer = null;
    this._editorId = nextId("mjrte-editor");
    this._helpId = nextId("mjrte-help");
    this._errorId = nextId("mjrte-error");
    this._toolbarId = nextId("mjrte-toolbar");
  }

  render() {
    const toolbarHtml = this._buildToolbarHtml();
    const markup = `
      <label class="label" part="label"></label>
      <div class="editor-wrap" part="editor-wrap">
        <div class="toolbar" part="toolbar" id="${this._toolbarId}" role="toolbar" aria-label="Formatting">
          ${toolbarHtml}
          <span class="toolbar-slots">
            <slot name="toolbar-start"></slot>
            <slot name="toolbar-end"></slot>
          </span>
        </div>
        <div
          class="editor"
          part="editor"
          id="${this._editorId}"
          contenteditable="true"
          role="textbox"
          aria-multiline="true"
        ></div>
        <div class="status-bar" part="status-bar" hidden></div>
      </div>
      <div class="below">
        <span class="help" part="help" id="${this._helpId}"></span>
        <span class="error" part="error" id="${this._errorId}" role="alert"></span>
      </div>
    `;
    return markup;
  }

  _buildToolbarHtml() {
    return TOOLBAR_GROUPS.map((group, gi) => {
      const btns = group.map(btn => {
        return `<button class="tb-btn" part="toolbar-button" type="button"
          aria-label="${btn.label}" aria-pressed="false"
          data-cmd="${btn.cmd}">${btn.icon}</button>`;
      }).join("");
      return `<div class="toolbar-group" part="toolbar-group" role="group" aria-label="Format group ${gi + 1}">${btns}</div>`;
    }).join("");
  }

  afterRender() {
    this._labelEl = this.$(".label");
    this._editorWrap = this.$(".editor-wrap");
    this._toolbar = this.$(".toolbar");
    this._editorEl = this.$(".editor");
    this._statusBar = this.$(".status-bar");
    this._helpEl = this.$(".help");
    this._errorEl = this.$(".error");

    this._syncAll();

    this.listen(this._editorEl, "input", this._onEditorInput.bind(this));
    this.listen(this._editorEl, "blur", this._onEditorBlur.bind(this));
    this.listen(this._editorEl, "focus", this._onEditorFocus.bind(this));
    this.listen(this._editorEl, "keydown", this._onEditorKeydown.bind(this));
    this.listen(this._editorEl, "paste", this._onPaste.bind(this));
    this.listen(this._toolbar, "click", this._onToolbarClick.bind(this));
    return;
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._editorEl === undefined) {
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
    const toolbarMode = this.getAttribute("toolbar") || "full";

    this._labelEl.textContent = label;
    this._editorEl.setAttribute("data-placeholder", placeholder);
    this._editorEl.setAttribute("aria-required", required ? "true" : "false");
    this._editorEl.contentEditable = (disabled || readonly) ? "false" : "true";
    this._toolbar.hidden = readonly;
    this._helpEl.textContent = helpText;

    const ids = [];
    if (helpText.length > 0) {
      ids.push(this._helpId);
    }
    if (this._errorEl.hasAttribute("data-visible")) {
      ids.push(this._errorId);
    }
    if (ids.length > 0) {
      this._editorEl.setAttribute("aria-describedby", ids.join(" "));
    } else {
      this._editorEl.removeAttribute("aria-describedby");
    }
    return;
  }

  _defaultSanitize(html) {
    const tmp = document.createElement("div");
    tmp.innerHTML = html;
    this._stripDisallowed(tmp);
    return tmp.innerHTML;
  }

  _stripDisallowed(node) {
    const children = Array.from(node.childNodes);
    for (let i = 0; i < children.length; i = i + 1) {
      const child = children[i];
      if (child.nodeType === Node.ELEMENT_NODE) {
        const tag = child.tagName.toLowerCase();
        if (!ALLOWED_TAGS.has(tag)) {
          while (child.firstChild !== null) {
            node.insertBefore(child.firstChild, child);
          }
          node.removeChild(child);
        } else {
          this._stripDisallowed(child);
        }
      }
    }
    return;
  }

  _onEditorInput(event) {
    const html = this._sanitizer(this._editorEl.innerHTML);
    const text = this._editorEl.textContent || "";
    this._setFormValue(html);

    if (this._debounceTimer !== null) {
      clearTimeout(this._debounceTimer);
    }
    this._debounceTimer = setTimeout(() => {
      this.emit("mj-input", { html, text });
    }, 150);

    this._updateToolbarStates();
    return;
  }

  _onEditorFocus(event) {
    this._editorWrap.setAttribute("data-focused", "");
    return;
  }

  _onEditorBlur(event) {
    this._editorWrap.removeAttribute("data-focused");
    const html = this._sanitizer(this._editorEl.innerHTML);
    const text = this._editorEl.textContent || "";
    const prev = this._value;
    if (html !== prev) {
      this._setFormValue(html);
      this.emit("mj-change", { html, text });
    }
    this._runValidation();
    return;
  }

  _onEditorKeydown(event) {
    const key = event.key.toLowerCase();
    const mod = event.ctrlKey || event.metaKey;
    if (!mod) {
      return;
    }
    if (key === "b") {
      event.preventDefault();
      this._execCmd("bold");
      return;
    }
    if (key === "i") {
      event.preventDefault();
      this._execCmd("italic");
      return;
    }
    if (key === "u") {
      event.preventDefault();
      this._execCmd("underline");
      return;
    }
    return;
  }

  _onPaste(event) {
    event.preventDefault();
    const clipData = event.clipboardData;
    if (clipData === null) {
      return;
    }
    let html = clipData.getData("text/html");
    if (html.length > 0) {
      html = this._sanitizer(html);
    } else {
      const text = clipData.getData("text/plain");
      html = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n/g, "<br>");
    }
    document.execCommand("insertHTML", false, html);
    return;
  }

  _onToolbarClick(event) {
    const btn = event.target.closest(".tb-btn");
    if (btn === null) {
      return;
    }
    const cmd = btn.getAttribute("data-cmd") || "";
    this._execCmd(cmd);
    this._editorEl.focus();
    return;
  }

  _execCmd(cmd) {
    if (cmd.startsWith("formatBlock:")) {
      const tag = cmd.split(":")[1];
      document.execCommand("formatBlock", false, tag);
    } else {
      document.execCommand(cmd, false, null);
    }
    this._updateToolbarStates();
    const html = this._sanitizer(this._editorEl.innerHTML);
    this._setFormValue(html);
    const active = document.queryCommandState(cmd.startsWith("formatBlock:") ? "formatBlock" : cmd);
    this.emit("mj-format", { command: cmd, active });
    return;
  }

  _updateToolbarStates() {
    const buttons = this.$all(".tb-btn");
    for (let i = 0; i < buttons.length; i = i + 1) {
      const btn = buttons[i];
      const cmd = btn.getAttribute("data-cmd") || "";
      if (!cmd.startsWith("formatBlock:")) {
        const active = document.queryCommandState(cmd);
        btn.setAttribute("aria-pressed", active ? "true" : "false");
      }
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
      this._editorWrap.setAttribute("data-invalid", "");
      this._editorEl.setAttribute("aria-invalid", "true");
      this.emit("mj-invalid", { validationMessage: displayMsg });
    } else {
      this._errorEl.removeAttribute("data-visible");
      this._editorWrap.removeAttribute("data-invalid");
      this._editorEl.setAttribute("aria-invalid", "false");
    }
    return;
  }

  _customValidity() {
    const maxLength = this.getAttribute("max-length");
    if (maxLength !== null) {
      const text = this._editorEl !== undefined ? (this._editorEl.textContent || "") : "";
      if (text.length > parseInt(maxLength, 10)) {
        return `Content must be ${maxLength} characters or fewer.`;
      }
    }
    return "";
  }

  _validationAnchor() {
    return this._editorEl;
  }

  onFormReset(initial) {
    if (this._editorEl !== undefined) {
      this._editorEl.innerHTML = this._sanitizer(initial);
      this._errorEl.removeAttribute("data-visible");
      this._editorWrap.removeAttribute("data-invalid");
      this._editorEl.setAttribute("aria-invalid", "false");
    }
    return;
  }

  get htmlValue() {
    return this._value;
  }

  get textContent() {
    if (this._editorEl === undefined) {
      return "";
    }
    return this._editorEl.textContent || "";
  }

  get sanitizer() {
    return this._sanitizer;
  }

  set sanitizer(fn) {
    if (typeof fn === "function") {
      this._sanitizer = fn;
    }
    return;
  }

  get value() {
    return this._value;
  }

  set value(next) {
    const sanitized = this._sanitizer(next);
    this._setFormValue(sanitized);
    if (this._editorEl !== undefined) {
      this._editorEl.innerHTML = sanitized;
    }
    return;
  }

  focus() {
    if (this._editorEl !== undefined) {
      this._editorEl.focus();
    }
    return;
  }
}
