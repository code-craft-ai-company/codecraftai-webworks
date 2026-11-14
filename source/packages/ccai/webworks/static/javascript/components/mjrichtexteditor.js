/*
 * mjrichtexteditor.js
 *
 * <mj-rich-text-editor> -- WYSIWYG editor with accessible toolbar,
 * contenteditable region, HTML sanitization, and form participation.
 *
 * The allow-list HTML sanitizer lives in core/sanitize.js; this module
 * re-exports `sanitizeHtml` and the RICH_TEXT_* constants so existing imports
 * from "./mjrichtexteditor.js" keep working.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";
import { sanitizeHtml, RICH_TEXT_ALLOWED_TAGS } from "../core/sanitize.js";

export {
  sanitizeHtml, RICH_TEXT_ALLOWED_TAGS, RICH_TEXT_ALLOWED_ATTRIBUTES, RICH_TEXT_TAG_ALIASES
} from "../core/sanitize.js";

/* ----- <mj-rich-text-editor> ----- */

const STYLES = `
:host {
  display: block;
  font-family: var(--mj-font-sans);
  font-size: var(--mj-font-size-md);
}

.label {
  display: block;
  margin-block-end: var(--mj-space-1);
  font-size: var(--mj-font-size-sm);
  font-weight: var(--mj-font-weight-medium);
  color: var(--mj-text);
  cursor: default;
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
  border-block-end: 1px solid var(--mj-border);
}
.toolbar[hidden] { display: none; }

.toolbar-groups {
  display: flex;
  flex-wrap: wrap;
  gap: var(--mj-space-1);
}

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
.tb-btn:disabled { cursor: not-allowed; opacity: 0.55; }

.editor {
  min-height: 200px;
  padding: var(--mj-space-3);
  color: var(--mj-text);
  background: var(--mj-surface);
  outline: none;
  line-height: var(--mj-line-height);
  position: relative;
  overflow-wrap: anywhere;
}
.editor[data-empty]::before {
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
  border-block-start: 1px solid var(--mj-border);
}
.status-bar[hidden] { display: none; }
.status-bar[data-exceeded] { color: var(--mj-color-danger); }

.below { margin-block-start: var(--mj-space-1); }
.help { font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }
.help:empty { display: none; }
.error { font-size: var(--mj-font-size-sm); color: var(--mj-color-danger); display: none; }
.error[data-visible] { display: block; }

:host([disabled]) .editor-wrap { opacity: 0.55; pointer-events: none; }
`;

const TOOLBAR_GROUPS = [
  {
    labelKey: "mj.richTextEditor.textStyle",
    buttons: [
      { cmd: "bold",          labelKey: "mj.richTextEditor.bold",          icon: "B"  },
      { cmd: "italic",        labelKey: "mj.richTextEditor.italic",        icon: "I"  },
      { cmd: "underline",     labelKey: "mj.richTextEditor.underline",     icon: "U"  },
      { cmd: "strikeThrough", labelKey: "mj.richTextEditor.strikethrough", icon: "S̶"  }
    ]
  },
  {
    labelKey: "mj.richTextEditor.lists",
    buttons: [
      { cmd: "insertUnorderedList", labelKey: "mj.richTextEditor.bulletList",   icon: "• ≡" },
      { cmd: "insertOrderedList",   labelKey: "mj.richTextEditor.numberedList", icon: "1 ≡" }
    ]
  },
  {
    labelKey: "mj.richTextEditor.blocks",
    buttons: [
      { cmd: "formatBlock:h2",         labelKey: "mj.richTextEditor.heading2",   icon: "H₂" },
      { cmd: "formatBlock:h3",         labelKey: "mj.richTextEditor.heading3",   icon: "H₃" },
      { cmd: "formatBlock:blockquote", labelKey: "mj.richTextEditor.blockquote", icon: "❝"  }
    ]
  }
];

const FORMAT_BLOCK_PREFIX = "formatBlock:";
const INPUT_DEBOUNCE_MS = 150;

export class MjRichTextEditor extends FormControlMixin(MjElement) {
  static tagName = "mj-rich-text-editor";
  static styles = STYLES;
  static watched = [
    "label", "placeholder", "help-text", "error-message", "value",
    "toolbar", "required", "disabled", "readonly", "max-length", "allowed-tags",
    "aria-label"
  ];

  constructor() {
    super()
    this._initFormControl()

    this._defaultSanitizer = this._defaultSanitize.bind(this)
    this._sanitizer = this._defaultSanitizer
    this._debounceTimer = null

    /* Set once the value was changed by the user or through the property. */
    this._dirty = false

    /* The value when the editor took focus, compared on blur for mj-change. */
    this._valueAtFocus = ""

    /* The selection inside the editor when it last lost focus. */
    this._savedRange = null

    this._labelId = nextId("mjrte-label")
    this._editorId = nextId("mjrte-editor")
    this._helpId = nextId("mjrte-help")
    this._errorId = nextId("mjrte-error")
    this._toolbarId = nextId("mjrte-toolbar")

    /* Shadow references; null until the first render. */
    this._labelEl = null
    this._editorWrap = null
    this._toolbar = null
    this._toolbarGroups = null
    this._editorEl = null
    this._statusBar = null
    this._helpEl = null
    this._errorEl = null
  }

  render() {
    const markup = html`
      <span class="label" part="label" id="${this._labelId}"></span>
      <div class="editor-wrap" part="editor-wrap">
        <div class="toolbar" part="toolbar" id="${this._toolbarId}" role="toolbar" aria-label="${t("mj.richTextEditor.toolbarLabel")}"
          aria-controls="${this._editorId}">
          <span class="toolbar-groups"></span>
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
          data-mj-focus-target
        ></div>
        <div class="status-bar" part="status-bar" hidden></div>
      </div>
      <div class="below">
        <span class="help" part="help" id="${this._helpId}"></span>
        <span class="error" part="error" id="${this._errorId}" role="alert"></span>
      </div>
    `
    return markup
  }

  afterRender() {
    this._labelEl = this.$(".label")
    this._editorWrap = this.$(".editor-wrap")
    this._toolbar = this.$(".toolbar")
    this._toolbarGroups = this.$(".toolbar-groups")
    this._editorEl = this.$(".editor")
    this._statusBar = this.$(".status-bar")
    this._helpEl = this.$(".help")
    this._errorEl = this.$(".error")

    this._buildToolbar()

    /* The value attribute is the initial content until the user edits. */
    if (this._dirty === false && this.hasAttribute("value") === true) {
      this._setFormValue(this._cleanValue(this.getAttribute("value")))
    }
    this._writeEditor(this._value)

    this._syncAll()

    this.listen(this._labelEl, "click", this._onLabelClick.bind(this))
    this.listen(this._editorEl, "beforeinput", this._onBeforeInput.bind(this))
    this.listen(this._editorEl, "input", this._onEditorInput.bind(this))
    this.listen(this._editorEl, "blur", this._onEditorBlur.bind(this))
    this.listen(this._editorEl, "focus", this._onEditorFocus.bind(this))
    this.listen(this._editorEl, "keydown", this._onEditorKeydown.bind(this))
    this.listen(this._editorEl, "paste", this._onPaste.bind(this))
    this.listen(this._toolbar, "mousedown", this._onToolbarMousedown.bind(this))
    this.listen(this._toolbar, "click", this._onToolbarClick.bind(this))
    this.listen(this._toolbar, "keydown", this._onToolbarKeydown.bind(this))
    this.listen(document, "selectionchange", this._onSelectionChange.bind(this))
    this.listen(this, "invalid", this._onInvalid.bind(this))

    this.onTeardown(() => {
      if (this._debounceTimer !== null) {
        clearTimeout(this._debounceTimer)
        this._debounceTimer = null
      }
    })
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "value") {
      /* Like a native control, the attribute stops applying once edited. */
      if (this._dirty === false) {
        this._setFormValue(this._cleanValue(newValue))
        this._writeEditor(this._value)
      }
    }

    if (this._editorEl === undefined || this._editorEl === null) {
      return
    }

    if (name === "toolbar") {
      this._buildToolbar()
    }
    if (name === "allowed-tags" && this._dirty === false && this.hasAttribute("value") === true) {
      this._setFormValue(this._cleanValue(this.getAttribute("value")))
      this._writeEditor(this._value)
    }
    this._syncAll()

    if (name === "required" || name === "max-length") {
      this._refreshValidity()
    }
    return
  }

  /* ----- rendering helpers ----- */

  /*
   * Build the toolbar buttons with DOM APIs. `toolbar="minimal"` shows only
   * the text-style group. The first button is the single tab stop; arrow
   * keys move between buttons (roving tabindex).
   */
  _buildToolbar() {
    const mode = this.getAttribute("toolbar") || "full"
    const groups = mode === "minimal" ? TOOLBAR_GROUPS.slice(0, 1) : TOOLBAR_GROUPS

    this._toolbarGroups.textContent = ""

    for (let groupIndex = 0; groupIndex < groups.length; groupIndex = groupIndex + 1) {
      const group = groups[groupIndex]
      const groupEl = document.createElement("div")
      groupEl.className = "toolbar-group"
      groupEl.setAttribute("part", "toolbar-group")
      groupEl.setAttribute("role", "group")
      groupEl.setAttribute("aria-label", t(group.labelKey))

      for (let buttonIndex = 0; buttonIndex < group.buttons.length; buttonIndex = buttonIndex + 1) {
        const spec = group.buttons[buttonIndex]
        const button = document.createElement("button")
        button.className = "tb-btn"
        button.type = "button"
        button.setAttribute("part", "toolbar-button")
        const label = t(spec.labelKey)
        button.setAttribute("aria-label", label)
        button.setAttribute("aria-pressed", "false")
        button.setAttribute("data-cmd", spec.cmd)
        button.title = label
        button.tabIndex = groupIndex === 0 && buttonIndex === 0 ? 0 : -1
        button.textContent = spec.icon
        groupEl.appendChild(button)
      }

      this._toolbarGroups.appendChild(groupEl)
    }
    return
  }

  _syncAll() {
    const label = this.getAttribute("label") || ""
    const placeholder = this.getAttribute("placeholder") || ""
    const helpText = this.getAttribute("help-text") || ""
    const disabled = this.hasAttribute("disabled")
    const readonly = this.hasAttribute("readonly")
    const required = this.hasAttribute("required")
    const editable = disabled === false && readonly === false

    this._labelEl.textContent = label
    this._editorEl.setAttribute("data-placeholder", placeholder)
    this._editorEl.setAttribute("aria-required", required === true ? "true" : "false")
    this._editorEl.setAttribute("aria-readonly", readonly === true ? "true" : "false")
    this._editorEl.setAttribute("contenteditable", editable === true ? "true" : "false")
    this._editorEl.tabIndex = disabled === true ? -1 : 0
    this._toolbar.hidden = readonly
    this._helpEl.textContent = helpText

    if (disabled === true) {
      this._editorEl.setAttribute("aria-disabled", "true")
    } else {
      this._editorEl.removeAttribute("aria-disabled")
    }

    const buttons = this.$all(".tb-btn")
    for (let index = 0; index < buttons.length; index = index + 1) {
      buttons[index].disabled = editable === false
    }

    /* Accessible name: the visible label, else aria-label, else a default. */
    if (label.length > 0) {
      this._editorEl.setAttribute("aria-labelledby", this._labelId)
      this._editorEl.removeAttribute("aria-label")
    } else {
      this._editorEl.removeAttribute("aria-labelledby")
      this._editorEl.setAttribute("aria-label", this.getAttribute("aria-label") || placeholder || t("mj.richTextEditor.label"))
    }

    this._syncDescribedBy()
    this._syncEmptyState()
    this._updateStatusBar()
    return
  }

  _syncDescribedBy() {
    const ids = []
    if ((this.getAttribute("help-text") || "").length > 0) {
      ids.push(this._helpId)
    }
    if (this._errorEl.hasAttribute("data-visible") === true) {
      ids.push(this._errorId)
    }
    if (ids.length > 0) {
      this._editorEl.setAttribute("aria-describedby", ids.join(" "))
    } else {
      this._editorEl.removeAttribute("aria-describedby")
    }
    return
  }

  /* Plain text of the editor without the invisible characters editing leaves behind. */
  _plainText() {
    let text = ""
    if (this._editorEl !== undefined && this._editorEl !== null) {
      text = this._editorEl.textContent || ""
    }
    text = text.replace(/[​﻿]/g, "")
    return text
  }

  _isVisuallyEmpty() {
    const text = this._plainText().replace(/ /g, " ")
    const empty = text.trim().length === 0
    return empty
  }

  _syncEmptyState() {
    if (this._isVisuallyEmpty() === true) {
      this._editorEl.setAttribute("data-empty", "")
    } else {
      this._editorEl.removeAttribute("data-empty")
    }
    return
  }

  _maxLength() {
    const raw = this.getAttribute("max-length")
    let max = null
    if (raw !== null && raw !== "") {
      const parsed = parseInt(raw, 10)
      if (isNaN(parsed) === false && parsed >= 0) {
        max = parsed
      }
    }
    return max
  }

  _updateStatusBar() {
    const max = this._maxLength()
    if (max === null) {
      this._statusBar.hidden = true
      this._statusBar.textContent = ""
      return
    }

    const length = this._plainText().length
    this._statusBar.hidden = false
    this._statusBar.textContent = `${length}/${max}`
    if (length > max) {
      this._statusBar.setAttribute("data-exceeded", "")
    } else {
      this._statusBar.removeAttribute("data-exceeded")
    }
    return
  }

  /* Put already-sanitized markup into the contenteditable region. */
  _writeEditor(sanitized) {
    if (this._editorEl === undefined || this._editorEl === null) {
      return
    }
    this._editorEl.innerHTML = sanitized
    this._syncEmptyState()
    this._updateStatusBar()
    return
  }

  /* ----- sanitizing ----- */

  _defaultSanitize(markup) {
    const options = {}

    /* `allowed-tags` narrows the default allow-list; it can never widen it. */
    const allowedAttr = this.getAttribute("allowed-tags") || ""
    const requested = allowedAttr.split(/[\s,]+/).filter((tag) => tag.length > 0)
    if (requested.length > 0) {
      const narrowed = []
      for (let index = 0; index < requested.length; index = index + 1) {
        const tag = requested[index].toLowerCase()
        if (RICH_TEXT_ALLOWED_TAGS.indexOf(tag) !== -1) {
          narrowed.push(tag)
        }
      }
      options.allowedTags = narrowed
    }

    const sanitized = sanitizeHtml(markup, options)
    return sanitized
  }

  /*
   * Sanitize markup that comes from outside the editor (the value attribute
   * or property, a form reset). Markup that renders no text -- an empty
   * paragraph, a lone <br> -- is the empty value.
   */
  _cleanValue(markup) {
    const source = markup !== null && markup !== undefined ? String(markup) : ""
    let clean = this._sanitizer(source)

    if (typeof clean !== "string") {
      clean = ""
    }
    if (clean.length > 0) {
      const inertDocument = new DOMParser().parseFromString(clean, "text/html")
      const text = (inertDocument.body.textContent || "").replace(/[\u200b\ufeff\u00a0]/g, " ")
      if (text.trim().length === 0) {
        clean = ""
      }
    }
    return clean
  }

  /*
   * The sanitized HTML of the editor. A visually empty editor (only the
   * <br> or empty block the browser leaves after deleting everything) is
   * the empty string, so `required` sees it as missing.
   */
  _readEditorValue() {
    let value = ""
    if (this._isVisuallyEmpty() === false) {
      value = this._sanitizer(this._editorEl.innerHTML)
    }
    return value
  }

  /* ----- editing ----- */

  _onLabelClick() {
    this.focus()
    return
  }

  _selectedTextLength() {
    let length = 0
    const selection = this._getSelection()
    if (selection !== null && selection.rangeCount > 0) {
      const range = selection.getRangeAt(0)
      if (this._editorEl.contains(range.commonAncestorContainer) === true) {
        length = range.toString().length
      }
    }
    return length
  }

  /* Refuse insertions that would take the text past max-length. */
  _onBeforeInput(event) {
    const max = this._maxLength()
    if (max === null || event.inputType === undefined || event.inputType.startsWith("insert") === false) {
      return
    }
    if (event.inputType === "insertFromPaste" || event.inputType === "insertFromDrop") {
      /* Paste is trimmed in `_onPaste`; a drop is checked after the fact. */
      return
    }

    const incoming = typeof event.data === "string" ? event.data.length : 0
    const projected = this._plainText().length - this._selectedTextLength() + incoming
    if (incoming > 0 && projected > max) {
      event.preventDefault()
    }
    return
  }

  _onEditorInput(event) {
    const value = this._readEditorValue()
    this._dirty = true
    this._setFormValue(value)
    this._syncEmptyState()
    this._updateStatusBar()

    if (this._debounceTimer !== null) {
      clearTimeout(this._debounceTimer)
    }
    this._debounceTimer = setTimeout(() => {
      this._debounceTimer = null
      this.emit("mj-input", { html: this._value, text: this._plainText() })
    }, INPUT_DEBOUNCE_MS)

    if (this._errorEl.hasAttribute("data-visible") === true) {
      this._runValidation(true)
    }
    this._updateToolbarStates()
    return
  }

  _onEditorFocus(event) {
    this._editorWrap.setAttribute("data-focused", "")
    this._valueAtFocus = this._value

    /* New lines become <p>, which the allow-list can represent. */
    try {
      document.execCommand("defaultParagraphSeparator", false, "p")
    } catch (error) {
      /* Not supported: <div> lines are mapped to <p> by the sanitizer. */
    }
    this._updateToolbarStates()
    return
  }

  _onEditorBlur(event) {
    this._editorWrap.removeAttribute("data-focused")
    this._saveSelection()

    if (this._debounceTimer !== null) {
      clearTimeout(this._debounceTimer)
      this._debounceTimer = null
      this.emit("mj-input", { html: this._value, text: this._plainText() })
    }

    if (this._value !== this._valueAtFocus) {
      this._valueAtFocus = this._value
      this.emit("mj-change", { html: this._value, text: this._plainText() })
    }
    this._runValidation(false)
    return
  }

  _onEditorKeydown(event) {
    const key = event.key.toLowerCase()
    const mod = event.ctrlKey === true || event.metaKey === true
    if (mod === false || event.altKey === true) {
      return
    }
    if (this.hasAttribute("readonly") === true || this.hasAttribute("disabled") === true) {
      return
    }

    let command = null
    if (key === "b") {
      command = "bold"
    } else if (key === "i") {
      command = "italic"
    } else if (key === "u") {
      command = "underline"
    }

    if (command !== null) {
      event.preventDefault()
      this._execCmd(command)
    }
    return
  }

  _onPaste(event) {
    event.preventDefault()
    const clipData = event.clipboardData
    if (clipData === null || clipData === undefined) {
      return
    }
    if (this.hasAttribute("readonly") === true || this.hasAttribute("disabled") === true) {
      return
    }

    const pastedHtml = clipData.getData("text/html")
    let plain = clipData.getData("text/plain")
    let markup = ""

    const max = this._maxLength()
    let room = null
    if (max !== null) {
      room = Math.max(0, max - (this._plainText().length - this._selectedTextLength()))
    }

    if (pastedHtml.length > 0 && (room === null || plain.length <= room)) {
      markup = this._sanitizer(pastedHtml)
    } else {
      if (room !== null && plain.length > room) {
        plain = plain.substring(0, room)
      }
      markup = String(html`${plain}`).replace(/\r?\n/g, "<br>")
    }

    if (markup.length > 0) {
      document.execCommand("insertHTML", false, markup)
    }
    return
  }

  /* ----- toolbar ----- */

  _onToolbarMousedown(event) {
    /* Keep focus and the selection in the editor while a button is clicked. */
    const btn = event.target.closest(".tb-btn")
    if (btn !== null) {
      event.preventDefault()
    }
    return
  }

  _onToolbarClick(event) {
    const btn = event.target.closest(".tb-btn")
    if (btn === null || btn.disabled === true) {
      return
    }

    const editorHasFocus = this.shadowRoot.activeElement === this._editorEl
    if (editorHasFocus === false) {
      /* Keyboard activation: apply to the selection the editor had. */
      this._editorEl.focus()
      this._restoreSelection()
    }

    const cmd = btn.getAttribute("data-cmd") || ""
    this._execCmd(cmd)

    if (editorHasFocus === false) {
      /* Return to the toolbar so further buttons can be toggled by keyboard. */
      this._saveSelection()
      btn.focus()
    }
    return
  }

  /* Roving tabindex: arrows, Home and End move between the buttons. */
  _onToolbarKeydown(event) {
    const buttons = this.$all(".tb-btn")
    const current = buttons.indexOf(this.shadowRoot.activeElement)
    if (current === -1) {
      return
    }

    const rtl = getComputedStyle(this).direction === "rtl"
    let next = -1

    if (event.key === "ArrowRight") {
      next = rtl === true ? current - 1 : current + 1
    } else if (event.key === "ArrowLeft") {
      next = rtl === true ? current + 1 : current - 1
    } else if (event.key === "Home") {
      next = 0
    } else if (event.key === "End") {
      next = buttons.length - 1
    }

    if (next === -1 && event.key !== "ArrowLeft" && event.key !== "ArrowRight") {
      return
    }

    event.preventDefault()
    if (next < 0) {
      next = buttons.length - 1
    } else if (next >= buttons.length) {
      next = 0
    }

    for (let index = 0; index < buttons.length; index = index + 1) {
      buttons[index].tabIndex = index === next ? 0 : -1
    }
    buttons[next].focus()
    return
  }

  _getSelection() {
    let selection = null
    if (typeof this.shadowRoot.getSelection === "function") {
      selection = this.shadowRoot.getSelection()
    } else {
      selection = document.getSelection()
    }
    return selection
  }

  _saveSelection() {
    const selection = this._getSelection()
    if (selection !== null && selection.rangeCount > 0) {
      const range = selection.getRangeAt(0)
      if (this._editorEl.contains(range.commonAncestorContainer) === true) {
        this._savedRange = range.cloneRange()
      }
    }
    return
  }

  _restoreSelection() {
    const selection = this._getSelection()
    if (selection === null || this._savedRange === null) {
      return
    }
    if (this._editorEl.contains(this._savedRange.commonAncestorContainer) === false) {
      this._savedRange = null
      return
    }
    selection.removeAllRanges()
    selection.addRange(this._savedRange)
    return
  }

  _onSelectionChange() {
    if (this.shadowRoot.activeElement === this._editorEl) {
      this._updateToolbarStates()
    }
    return
  }

  _commandIsActive(cmd) {
    let active = false
    try {
      if (cmd.startsWith(FORMAT_BLOCK_PREFIX) === true) {
        const tag = cmd.substring(FORMAT_BLOCK_PREFIX.length)
        const current = String(document.queryCommandValue("formatBlock") || "").toLowerCase()
        active = current === tag
      } else {
        active = document.queryCommandState(cmd) === true
      }
    } catch (error) {
      active = false
    }
    return active
  }

  _execCmd(cmd) {
    if (this.hasAttribute("readonly") === true || this.hasAttribute("disabled") === true) {
      return
    }

    if (cmd.startsWith(FORMAT_BLOCK_PREFIX) === true) {
      /* Applying the block format that is already active turns it off. */
      const tag = cmd.substring(FORMAT_BLOCK_PREFIX.length)
      const target = this._commandIsActive(cmd) === true ? "p" : tag
      document.execCommand("formatBlock", false, `<${target}>`)
    } else {
      document.execCommand(cmd, false, null)
    }

    /* execCommand fires `input` when it changed something; sync regardless. */
    const value = this._readEditorValue()
    if (value !== this._value) {
      this._dirty = true
      this._setFormValue(value)
    }
    this._syncEmptyState()
    this._updateStatusBar()
    this._updateToolbarStates()

    this.emit("mj-format", { command: cmd, active: this._commandIsActive(cmd) })
    return
  }

  _updateToolbarStates() {
    const buttons = this.$all(".tb-btn")
    for (let index = 0; index < buttons.length; index = index + 1) {
      const btn = buttons[index]
      const cmd = btn.getAttribute("data-cmd") || ""
      btn.setAttribute("aria-pressed", this._commandIsActive(cmd) === true ? "true" : "false")
    }
    return
  }

  /* ----- validation ----- */

  /*
   * Render the inline error for the current validity. `quiet` suppresses
   * the mj-invalid event (used while the user is correcting the content).
   */
  _runValidation(quiet) {
    this._refreshValidity()
    const msg = this.validationMessage
    const overrideMsg = this.getAttribute("error-message") || ""
    const displayMsg = msg.length > 0 && overrideMsg.length > 0 ? overrideMsg : msg

    if (displayMsg.length > 0) {
      this._errorEl.textContent = displayMsg
      this._errorEl.setAttribute("data-visible", "")
      this._editorWrap.setAttribute("data-invalid", "")
      this._editorEl.setAttribute("aria-invalid", "true")
      if (quiet !== true) {
        this.emit("mj-invalid", { validationMessage: displayMsg })
      }
    } else {
      this._clearValidationUi()
    }
    this._syncDescribedBy()
    return
  }

  _clearValidationUi() {
    this._errorEl.textContent = ""
    this._errorEl.removeAttribute("data-visible")
    this._editorWrap.removeAttribute("data-invalid")
    this._editorEl.setAttribute("aria-invalid", "false")
    return
  }

  /* A failed checkValidity() / reportValidity() / form submit. */
  _onInvalid(event) {
    this._runValidation(false)
    return
  }

  _customValidity() {
    const max = this._maxLength()
    let message = ""
    if (max !== null && this._plainText().length > max) {
      message = t("mj.richTextEditor.maxLength", { count: max })
    }
    return message
  }

  _validationAnchor() {
    return this._editorEl
  }

  /*
   * Show the inline error state for the current value and return whether
   * the control is valid. <mj-form> calls this on a failed submit.
   */
  showValidation() {
    this._refreshValidity()

    /* An invalid control raises `invalid`, which renders the error. */
    const valid = this.checkValidity()
    if (valid === true && this._editorEl !== undefined && this._editorEl !== null) {
      this._clearValidationUi()
      this._syncDescribedBy()
    }
    return valid
  }

  reportValidity() {
    const valid = this.showValidation()
    return valid
  }

  onFormReset(initial) {
    const clean = this._cleanValue(initial)
    this._dirty = false
    this._setFormValue(clean)
    this._writeEditor(clean)
    this._valueAtFocus = clean
    if (this._editorEl !== undefined && this._editorEl !== null) {
      this._clearValidationUi()
      this._syncDescribedBy()
    }
    return
  }

  /* ----- scriptable API ----- */

  get htmlValue() {
    return this._value
  }

  /* Plain-text extraction of the editor content (read-only by intent). */
  get textContent() {
    let text = ""
    if (this._editorEl !== undefined && this._editorEl !== null) {
      text = this._plainText()
    }
    return text
  }

  set textContent(value) {
    super.textContent = value
    return
  }

  get sanitizer() {
    return this._sanitizer
  }

  set sanitizer(fn) {
    if (typeof fn === "function") {
      this._sanitizer = fn
    } else if (fn === null || fn === undefined) {
      this._sanitizer = this._defaultSanitizer
    }
    return
  }

  get value() {
    return this._value
  }

  set value(next) {
    const sanitized = this._cleanValue(next)
    this._dirty = true
    this._setFormValue(sanitized)
    this._writeEditor(sanitized)
    return
  }

  focus(options) {
    if (this._editorEl !== undefined && this._editorEl !== null) {
      this._editorEl.focus(options)
    }
    return
  }
}
