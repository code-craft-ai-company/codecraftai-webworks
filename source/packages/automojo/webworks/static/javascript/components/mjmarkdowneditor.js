/*
 * mjmarkdowneditor.js
 *
 * <mj-markdown-editor> -- Markdown authoring with Edit/Split/Preview modes,
 * accessible toolbar, pluggable renderer/sanitizer, and form participation.
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
  min-height: 300px;
  display: flex;
  flex-direction: column;
}
.outer[data-focused] { border-color: var(--mj-accent); outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: var(--mj-focus-ring-offset); }
.outer[data-invalid] { border-color: var(--mj-color-danger); }

.header {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  padding: var(--mj-space-2);
  background: var(--mj-bg-subtle);
  border-bottom: 1px solid var(--mj-border);
  flex-shrink: 0;
}
.header[hidden] { display: none; }

.mode-tabs {
  display: flex;
  gap: 2px;
  background: var(--mj-bg-muted);
  border-radius: var(--mj-radius-sm);
  padding: 2px;
}
.mode-tab {
  padding: var(--mj-space-1) var(--mj-space-3);
  background: transparent;
  border: none;
  border-radius: var(--mj-radius-sm);
  cursor: pointer;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text-muted);
}
.mode-tab[aria-selected="true"] { background: var(--mj-surface); color: var(--mj-text); font-weight: var(--mj-font-weight-medium); }
.mode-tab:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); }

.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  flex: 1;
}
.toolbar[hidden] { display: none; }

.tb-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2rem;
  height: 2rem;
  padding: 0 var(--mj-space-1);
  background: transparent;
  border: none;
  border-radius: var(--mj-radius-sm);
  cursor: pointer;
  color: var(--mj-text-muted);
  font-size: 0.8rem;
  font-family: var(--mj-font-mono);
}
.tb-btn:hover { background: var(--mj-bg-muted); color: var(--mj-text); }
.tb-btn:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); }

.content-area {
  display: flex;
  flex: 1;
  min-height: 0;
}

.edit-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.edit-pane[hidden] { display: none; }

textarea {
  flex: 1;
  width: 100%;
  box-sizing: border-box;
  padding: var(--mj-space-3);
  font-family: var(--mj-font-mono);
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
  background: var(--mj-surface);
  border: none;
  outline: none;
  resize: none;
  line-height: 1.6;
  min-height: 200px;
}
textarea::placeholder { color: var(--mj-text-muted); }

.divider {
  width: 4px;
  background: var(--mj-border);
  cursor: col-resize;
  flex-shrink: 0;
}
.divider[hidden] { display: none; }

.preview-pane {
  flex: 1;
  overflow-y: auto;
  padding: var(--mj-space-3);
  background: var(--mj-bg-subtle);
  line-height: var(--mj-line-height);
  color: var(--mj-text);
}
.preview-pane[hidden] { display: none; }
.preview-pane[aria-live] {}

.status-bar {
  padding: var(--mj-space-1) var(--mj-space-3);
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
  background: var(--mj-bg-subtle);
  border-top: 1px solid var(--mj-border);
  display: flex;
  justify-content: flex-end;
}

.below { margin-top: var(--mj-space-1); }
.help { font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }
.help:empty { display: none; }
.error { font-size: var(--mj-font-size-sm); color: var(--mj-color-danger); display: none; }
.error[data-visible] { display: block; }

:host([disabled]) .outer { opacity: 0.55; pointer-events: none; }
`;

const MD_TOOLBAR = [
  { syntax: "**{sel}**",     label: "Bold",       icon: "**B**", key: "b" },
  { syntax: "_{sel}_",       label: "Italic",     icon: "_I_",   key: "i" },
  { syntax: "[{sel}](url)",  label: "Link",       icon: "🔗",    key: "k" },
  { syntax: "# {sel}",       label: "Heading 1",  icon: "H1",    key: null },
  { syntax: "## {sel}",      label: "Heading 2",  icon: "H2",    key: null },
  { syntax: "- {sel}",       label: "Bullet",     icon: "• —",  key: null },
  { syntax: "1. {sel}",      label: "Numbered",   icon: "1. —", key: null },
  { syntax: "> {sel}",       label: "Blockquote", icon: "❝",    key: null },
  { syntax: "`{sel}`",       label: "Code",       icon: "`c`",   key: null }
];

function _builtinRenderer(markdown) {
  let html = markdown
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/_(.+?)_/g, "<em>$1</em>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/^# (.+)$/gm, "<h1>$1</h1>")
    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
    .replace(/^### (.+)$/gm, "<h3>$1</h3>")
    .replace(/^> (.+)$/gm, "<blockquote>$1</blockquote>")
    .replace(/^\- (.+)$/gm, "<li>$1</li>")
    .replace(/^(\d+)\. (.+)$/gm, "<li>$2</li>")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>')
    .replace(/\n{2,}/g, "</p><p>")
    .replace(/\n/g, "<br>");
  return `<p>${html}</p>`;
}

export class MjMarkdownEditor extends FormControlMixin(MjElement) {
  static tagName = "mj-markdown-editor";
  static styles = STYLES;
  static watched = [
    "label", "placeholder", "help-text", "error-message", "value",
    "view", "required", "disabled", "readonly", "maxlength", "minlength", "count-words"
  ];

  constructor() {
    super();
    this._initFormControl();
    this._renderer = _builtinRenderer;
    this._sanitizer = (html) => html;
    this._previewDebounce = null;
    this._currentView = "edit";
    this._textareaId = nextId("mjmde-ta");
    this._previewId = nextId("mjmde-preview");
    this._helpId = nextId("mjmde-help");
    this._errorId = nextId("mjmde-error");
  }

  render() {
    const toolbarBtns = MD_TOOLBAR.map(btn => {
      return `<button class="tb-btn" type="button" aria-label="${btn.label}" data-syntax="${btn.syntax}">${btn.icon}</button>`;
    }).join("");

    const markup = `
      <label class="label" part="label"></label>
      <div class="outer" part="outer">
        <div class="header" part="header">
          <div class="mode-tabs" part="mode-tabs" role="tablist" aria-label="View mode">
            <button class="mode-tab" role="tab" aria-selected="true" data-view="edit">Edit</button>
            <button class="mode-tab" role="tab" aria-selected="false" data-view="split">Split</button>
            <button class="mode-tab" role="tab" aria-selected="false" data-view="preview">Preview</button>
          </div>
          <div class="toolbar" part="toolbar" role="toolbar" aria-label="Markdown formatting">
            <slot name="toolbar-start"></slot>
            ${toolbarBtns}
            <slot name="toolbar-end"></slot>
          </div>
        </div>
        <div class="content-area">
          <div class="edit-pane" part="edit-pane">
            <textarea
              part="textarea"
              id="${this._textareaId}"
              role="textbox"
              aria-multiline="true"
            ></textarea>
          </div>
          <div class="divider" part="divider" role="separator" hidden></div>
          <div class="preview-pane" part="preview-pane"
            id="${this._previewId}"
            role="region"
            aria-label="Preview"
            aria-live="polite"
            hidden>
            <slot name="preview-empty"></slot>
          </div>
        </div>
        <div class="status-bar" part="status-bar"></div>
      </div>
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
    this._previewPane = this.$(".preview-pane");
    this._divider = this.$(".divider");
    this._toolbar = this.$(".toolbar");
    this._statusBar = this.$(".status-bar");
    this._helpEl = this.$(".help");
    this._errorEl = this.$(".error");
    this._modeTabs = this.$all(".mode-tab");

    this._syncAll();

    this.listen(this._textarea, "input", this._onTextareaInput.bind(this));
    this.listen(this._textarea, "change", this._onTextareaChange.bind(this));
    this.listen(this._textarea, "blur", this._onTextareaBlur.bind(this));
    this.listen(this._textarea, "focus", this._onTextareaFocus.bind(this));
    this.listen(this._textarea, "keydown", this._onKeydown.bind(this));
    this.listen(this.$(".mode-tabs"), "click", this._onTabClick.bind(this));
    this.listen(this.$(".toolbar"), "click", this._onToolbarClick.bind(this));
    return;
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._textarea === undefined) {
      return;
    }
    if (name === "view") {
      this._setView(newValue || "edit");
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
    const maxlength = this.getAttribute("maxlength");
    const minlength = this.getAttribute("minlength");
    const view = this.getAttribute("view") || "edit";

    this._labelEl.textContent = label;
    this._textarea.placeholder = placeholder;
    this._textarea.disabled = disabled;
    this._textarea.readOnly = readonly;
    this._textarea.setAttribute("aria-required", required ? "true" : "false");
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

    if (readonly) {
      this._setView("preview");
      this.$(".header").hidden = true;
    } else {
      this.$(".header").hidden = false;
      if (this._currentView !== view) {
        this._setView(view);
      }
    }

    this._updateStatusBar();
    return;
  }

  _setView(view) {
    const valid = ["edit", "split", "preview"];
    const v = valid.includes(view) ? view : "edit";
    this._currentView = v;

    const editPane = this.$(".edit-pane");
    const divider = this._divider;
    const previewPane = this._previewPane;

    editPane.hidden = v === "preview";
    divider.hidden = v !== "split";
    previewPane.hidden = v === "edit";
    this._toolbar.hidden = v === "preview";

    this._modeTabs.forEach(tab => {
      const tabView = tab.getAttribute("data-view");
      tab.setAttribute("aria-selected", tabView === v ? "true" : "false");
    });

    if (v === "split" || v === "preview") {
      this._updatePreview();
    }

    this.emit("mj-view-change", { view: v });
    return;
  }

  _onTabClick(event) {
    const tab = event.target.closest(".mode-tab");
    if (tab === null) {
      return;
    }
    const view = tab.getAttribute("data-view");
    this.setAttribute("view", view);
    this._setView(view);
    return;
  }

  _onToolbarClick(event) {
    const btn = event.target.closest(".tb-btn");
    if (btn === null) {
      return;
    }
    const syntax = btn.getAttribute("data-syntax") || "";
    this._insertSyntax(syntax);
    this._textarea.focus();
    return;
  }

  _insertSyntax(syntax) {
    const start = this._textarea.selectionStart;
    const end = this._textarea.selectionEnd;
    const sel = this._textarea.value.substring(start, end);
    const inserted = syntax.replace("{sel}", sel || "text");
    this._textarea.setRangeText(inserted, start, end, "select");
    this._setFormValue(this._textarea.value);
    this._schedulePreview();
    return;
  }

  _onKeydown(event) {
    const key = event.key.toLowerCase();
    const mod = event.ctrlKey || event.metaKey;
    if (!mod) {
      return;
    }
    if (key === "b") {
      event.preventDefault();
      this._insertSyntax("**{sel}**");
      return;
    }
    if (key === "i") {
      event.preventDefault();
      this._insertSyntax("_{sel}_");
      return;
    }
    if (key === "k") {
      event.preventDefault();
      this._insertSyntax("[{sel}](url)");
      return;
    }
    return;
  }

  _onTextareaInput(event) {
    const val = this._textarea.value;
    this._setFormValue(val);
    this._updateStatusBar();
    this._schedulePreview();
    const words = val.match(/\S+/g);
    const wordCount = words !== null ? words.length : 0;
    this.emit("mj-input", { value: val, wordCount });
    return;
  }

  _onTextareaChange(event) {
    const val = this._textarea.value;
    const words = val.match(/\S+/g);
    const wordCount = words !== null ? words.length : 0;
    this.emit("mj-change", { value: val, wordCount });
    return;
  }

  _onTextareaFocus(event) {
    this._outerEl.setAttribute("data-focused", "");
    return;
  }

  _onTextareaBlur(event) {
    this._outerEl.removeAttribute("data-focused");
    this._runValidation();
    return;
  }

  _schedulePreview() {
    if (this._currentView === "edit") {
      return;
    }
    if (this._previewDebounce !== null) {
      clearTimeout(this._previewDebounce);
    }
    this._previewDebounce = setTimeout(() => {
      this._updatePreview();
    }, 200);
    return;
  }

  _updatePreview() {
    const md = this._textarea !== undefined ? this._textarea.value : "";
    const html = this._sanitizer(this._renderer(md));
    this._previewPane.innerHTML = html;
    return;
  }

  _updateStatusBar() {
    if (this._textarea === undefined) {
      return;
    }
    const val = this._textarea.value;
    const charCount = val.length;
    const words = val.match(/\S+/g);
    const wordCount = words !== null ? words.length : 0;
    const maxlength = this.getAttribute("maxlength");
    const countWords = this.hasAttribute("count-words");

    let status = "";
    if (maxlength !== null) {
      status = `${charCount}/${maxlength}`;
    }
    if (countWords) {
      const wordPart = `${wordCount} words`;
      status = status.length > 0 ? `${status} • ${wordPart}` : wordPart;
    }
    this._statusBar.textContent = status;
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
      const initialView = this.getAttribute("view") || "edit";
      this._setView(initialView);
      this._updateStatusBar();
      this._errorEl.removeAttribute("data-visible");
      this._outerEl.removeAttribute("data-invalid");
      this._textarea.setAttribute("aria-invalid", "false");
    }
    return;
  }

  get previewHtml() {
    if (this._previewPane === undefined) {
      return "";
    }
    return this._previewPane.innerHTML;
  }

  get wordCount() {
    if (this._textarea === undefined) {
      return 0;
    }
    const words = this._textarea.value.match(/\S+/g);
    return words !== null ? words.length : 0;
  }

  get renderer() {
    return this._renderer;
  }

  set renderer(fn) {
    if (typeof fn === "function") {
      this._renderer = fn;
      if (this._currentView !== "edit") {
        this._updatePreview();
      }
    }
    return;
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
    this._setFormValue(next);
    if (this._textarea !== undefined) {
      this._textarea.value = next;
      this._updateStatusBar();
      if (this._currentView !== "edit") {
        this._updatePreview();
      }
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
