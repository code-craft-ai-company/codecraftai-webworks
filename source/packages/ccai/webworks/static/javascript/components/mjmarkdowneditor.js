/*
 * mjmarkdowneditor.js
 *
 * <mj-markdown-editor> -- Markdown authoring with Edit/Split/Preview modes,
 * accessible toolbar, pluggable renderer/sanitizer, and form participation.
 *
 * The preview never shows unsanitized markup: the output of the renderer
 * (built-in or injected) always passes through the sanitizer, which by
 * default is the shared allow-list sanitizer from mjrichtexteditor.js.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { html, escapeHtml, safeUrl } from "../core/html.js";
import { t } from "../core/intl.js";
import { sanitizeHtml } from "../core/sanitize.js";

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
  border-block-end: 1px solid var(--mj-border);
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
  font: inherit;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text-muted);
}
.mode-tab[aria-checked="true"] { background: var(--mj-surface); color: var(--mj-text); font-weight: var(--mj-font-weight-medium); }
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
.tb-btn:disabled { cursor: not-allowed; opacity: 0.55; }

.content-area {
  display: flex;
  flex: 1;
  min-height: 0;
}

.edit-pane {
  flex: 1;
  min-width: 0;
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
  width: 1px;
  background: var(--mj-border);
  flex-shrink: 0;
}
.divider[hidden] { display: none; }

.preview-pane {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  padding: var(--mj-space-3);
  background: var(--mj-bg-subtle);
  line-height: var(--mj-line-height);
  color: var(--mj-text);
  overflow-wrap: anywhere;
}
.preview-pane[hidden] { display: none; }
.preview-content > :first-child { margin-block-start: 0; }
.preview-content > :last-child { margin-block-end: 0; }
.preview-content img { max-width: 100%; }

.status-bar {
  padding: var(--mj-space-1) var(--mj-space-3);
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
  background: var(--mj-bg-subtle);
  border-block-start: 1px solid var(--mj-border);
  display: flex;
  justify-content: flex-end;
}
.status-bar:empty { display: none; }

.below { margin-block-start: var(--mj-space-1); }
.help { font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }
.help:empty { display: none; }
.error { font-size: var(--mj-font-size-sm); color: var(--mj-color-danger); display: none; }
.error[data-visible] { display: block; }

:host([disabled]) .outer { opacity: 0.55; pointer-events: none; }
`;

const MD_TOOLBAR = [
  { syntax: "**{sel}**",     labelKey: "mj.markdownEditor.bold",       icon: "**B**" },
  { syntax: "_{sel}_",       labelKey: "mj.markdownEditor.italic",     icon: "_I_"   },
  { syntax: "[{sel}](url)",  labelKey: "mj.markdownEditor.link",       icon: "🔗"    },
  { syntax: "# {sel}",       labelKey: "mj.markdownEditor.heading1",   icon: "H1"    },
  { syntax: "## {sel}",      labelKey: "mj.markdownEditor.heading2",   icon: "H2"    },
  { syntax: "- {sel}",       labelKey: "mj.markdownEditor.bullet",     icon: "• —"  },
  { syntax: "1. {sel}",      labelKey: "mj.markdownEditor.numbered",   icon: "1. —" },
  { syntax: "> {sel}",       labelKey: "mj.markdownEditor.blockquote", icon: "❝"    },
  { syntax: "`{sel}`",       labelKey: "mj.markdownEditor.code",       icon: "`c`"   }
];

const VIEW_MODES = [
  { view: "edit",    labelKey: "mj.markdownEditor.viewEdit"    },
  { view: "split",   labelKey: "mj.markdownEditor.viewSplit"   },
  { view: "preview", labelKey: "mj.markdownEditor.viewPreview" }
];

/* What the preview may contain: the rich text set plus common Markdown output. */
const PREVIEW_SANITIZE_OPTIONS = {
  allowedTags: [
    "b", "i", "u", "s", "em", "strong", "a", "ul", "ol", "li",
    "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "pre", "code", "br", "p",
    "hr", "img", "table", "thead", "tbody", "tfoot", "tr", "th", "td",
    "del", "ins", "sup", "sub", "kbd", "dl", "dt", "dd"
  ],
  allowedAttributes: {
    a: ["href", "title"],
    img: ["src", "alt", "title", "width", "height"],
    th: ["colspan", "rowspan", "align"],
    td: ["colspan", "rowspan", "align"],
    ol: ["start"],
    code: ["class"]
  },
  aliases: {
    strike: "s"
  }
};

const PREVIEW_DEBOUNCE_MS = 200;

/* Private-use characters that bracket a placeholder index during inline rendering. */
const PLACEHOLDER_OPEN = "";
const PLACEHOLDER_CLOSE = "";
const PLACEHOLDER_PATTERN = /(\d+)/g;

/*
 * Render the inline Markdown of one run of text to HTML. Code spans and
 * links are lifted out first (their content must not be re-interpreted),
 * the rest is escaped, emphasis is applied, and the lifted parts are put
 * back. Link targets go through `safeUrl`; a rejected target leaves only
 * the link text.
 */
function renderInline(source) {
  const placeholders = []

  const hold = (markup) => {
    placeholders.push(markup)
    const token = `${PLACEHOLDER_OPEN}${placeholders.length - 1}${PLACEHOLDER_CLOSE}`
    return token
  }

  let text = source.replace(/[]/g, "")

  text = text.replace(/`([^`\n]+)`/g, (match, code) => {
    return hold(`<code>${escapeHtml(code)}</code>`)
  })

  text = text.replace(/\[([^\]\n]+)\]\(([^)\s]+)(?:\s+"([^"\n]*)")?\)/g, (match, label, target, title) => {
    const labelMarkup = renderEmphasis(escapeHtml(label))
    const checked = safeUrl(target, null)
    let markup = labelMarkup
    if (checked !== null) {
      const titleAttribute = title !== undefined ? ` title="${escapeHtml(title)}"` : ""
      markup = `<a href="${escapeHtml(checked)}"${titleAttribute}>${labelMarkup}</a>`
    }
    return hold(markup)
  })

  let rendered = renderEmphasis(escapeHtml(text))

  rendered = rendered.replace(PLACEHOLDER_PATTERN, (match, index) => {
    return placeholders[parseInt(index, 10)]
  })
  return rendered
}

/*
 * Apply bold and italic to already-escaped text. Underscore emphasis needs
 * a word boundary on both sides so snake_case_names stay intact.
 */
function renderEmphasis(escaped) {
  const rendered = escaped
    .replace(/\*\*([^*\n]+?)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[^\w])__([^_\n]+?)__(?=[^\w]|$)/g, "$1<strong>$2</strong>")
    .replace(/\*([^*\s][^*\n]*?)\*/g, "<em>$1</em>")
    .replace(/(^|[^\w])_([^_\s](?:[^_\n]*[^_\s])?)_(?=[^\w]|$)/g, "$1<em>$2</em>")
  return rendered
}

const HEADING_PATTERN = /^(#{1,6})\s+(.*?)\s*#*\s*$/;
const BLOCKQUOTE_PATTERN = /^\s{0,3}>\s?/;
const BULLET_PATTERN = /^\s{0,3}[-*+]\s+/;
const ORDERED_PATTERN = /^\s{0,3}(\d+)[.)]\s+/;
const RULE_PATTERN = /^\s{0,3}(?:-{3,}|\*{3,}|_{3,})\s*$/;
const FENCE_PATTERN = /^\s{0,3}```/;

function startsBlock(line) {
  const starts = HEADING_PATTERN.test(line) === true ||
    BLOCKQUOTE_PATTERN.test(line) === true ||
    BULLET_PATTERN.test(line) === true ||
    ORDERED_PATTERN.test(line) === true ||
    RULE_PATTERN.test(line) === true ||
    FENCE_PATTERN.test(line) === true
  return starts
}

/*
 * The built-in Markdown renderer: headings, paragraphs, block quotes,
 * bullet and numbered lists, fenced code, rules, and inline bold, italic,
 * code and links. Block structure is recognised on the raw lines first and
 * every piece of text is escaped as it is emitted, so the result contains
 * only the markup produced here. Empty input renders the empty string.
 */
function builtinRenderer(markdown) {
  const source = markdown !== null && markdown !== undefined ? String(markdown) : ""
  const lines = source.replace(/\r\n?/g, "\n").split("\n")
  const blocks = []
  let index = 0

  while (index < lines.length) {
    const line = lines[index]

    if (line.trim().length === 0) {
      index = index + 1
    } else if (FENCE_PATTERN.test(line) === true) {
      const codeLines = []
      index = index + 1
      while (index < lines.length && FENCE_PATTERN.test(lines[index]) === false) {
        codeLines.push(lines[index])
        index = index + 1
      }
      index = index + 1
      blocks.push(`<pre><code>${escapeHtml(codeLines.join("\n"))}</code></pre>`)
    } else if (RULE_PATTERN.test(line) === true) {
      blocks.push("<hr>")
      index = index + 1
    } else if (HEADING_PATTERN.test(line) === true) {
      const match = line.match(HEADING_PATTERN)
      const level = match[1].length
      blocks.push(`<h${level}>${renderInline(match[2])}</h${level}>`)
      index = index + 1
    } else if (BLOCKQUOTE_PATTERN.test(line) === true) {
      const quoted = []
      while (index < lines.length && BLOCKQUOTE_PATTERN.test(lines[index]) === true) {
        quoted.push(lines[index].replace(BLOCKQUOTE_PATTERN, ""))
        index = index + 1
      }
      blocks.push(`<blockquote>${builtinRenderer(quoted.join("\n"))}</blockquote>`)
    } else if (BULLET_PATTERN.test(line) === true) {
      const items = []
      while (index < lines.length && BULLET_PATTERN.test(lines[index]) === true) {
        items.push(`<li>${renderInline(lines[index].replace(BULLET_PATTERN, ""))}</li>`)
        index = index + 1
      }
      blocks.push(`<ul>${items.join("")}</ul>`)
    } else if (ORDERED_PATTERN.test(line) === true) {
      const items = []
      const first = parseInt(line.match(ORDERED_PATTERN)[1], 10)
      while (index < lines.length && ORDERED_PATTERN.test(lines[index]) === true) {
        items.push(`<li>${renderInline(lines[index].replace(ORDERED_PATTERN, ""))}</li>`)
        index = index + 1
      }
      const startAttribute = first !== 1 ? ` start="${first}"` : ""
      blocks.push(`<ol${startAttribute}>${items.join("")}</ol>`)
    } else {
      const paragraph = []
      while (index < lines.length && lines[index].trim().length > 0 && startsBlock(lines[index]) === false) {
        paragraph.push(renderInline(lines[index]))
        index = index + 1
      }
      blocks.push(`<p>${paragraph.join("<br>")}</p>`)
    }
  }

  const rendered = blocks.join("")
  return rendered
}

function defaultPreviewSanitizer(markup) {
  const sanitized = sanitizeHtml(markup, PREVIEW_SANITIZE_OPTIONS)
  return sanitized
}

function countWords(text) {
  const words = text.match(/\S+/g)
  const count = words !== null ? words.length : 0
  return count
}

export class MjMarkdownEditor extends FormControlMixin(MjElement) {
  static tagName = "mj-markdown-editor";
  static styles = STYLES;
  static watched = [
    "label", "placeholder", "help-text", "error-message", "value",
    "view", "required", "disabled", "readonly", "maxlength", "minlength", "count-words",
    "aria-label"
  ];

  constructor() {
    super()
    this._initFormControl()
    this._renderer = builtinRenderer
    this._sanitizer = defaultPreviewSanitizer
    this._previewDebounce = null

    /* True while a toolbar edit is in flight (see _insertSyntax). */
    this._suppressInput = false

    /* The view currently shown; null until the first render applies one. */
    this._currentView = null

    /* Set once the value was changed by the user or through the property. */
    this._dirty = false

    /* The value when the textarea took focus, compared on blur for mj-change. */
    this._valueAtFocus = ""

    this._textareaId = nextId("mjmde-ta")
    this._previewId = nextId("mjmde-preview")
    this._helpId = nextId("mjmde-help")
    this._errorId = nextId("mjmde-error")

    /* Shadow references; null until the first render. */
    this._labelEl = null
    this._outerEl = null
    this._headerEl = null
    this._textarea = null
    this._editPane = null
    this._previewPane = null
    this._previewContent = null
    this._previewEmptySlot = null
    this._divider = null
    this._toolbar = null
    this._statusBar = null
    this._helpEl = null
    this._errorEl = null
    this._modeTabs = []
  }

  render() {
    const toolbarButtons = MD_TOOLBAR.map((button) => {
      const label = t(button.labelKey)
      return html`<button class="tb-btn" part="toolbar-button" type="button" aria-label="${label}" title="${label}" data-syntax="${button.syntax}">${button.icon}</button>`
    })

    const modeButtons = VIEW_MODES.map((mode) => {
      return html`<button class="mode-tab" part="mode-tab" type="button" role="radio" aria-checked="false" tabindex="-1" data-view="${mode.view}">${t(mode.labelKey)}</button>`
    })

    const markup = html`
      <label class="label" part="label" for="${this._textareaId}"></label>
      <div class="outer" part="outer">
        <div class="header" part="header">
          <div class="mode-tabs" part="mode-tabs" role="radiogroup" aria-label="${t("mj.markdownEditor.viewModeLabel")}">
            ${modeButtons}
          </div>
          <div class="toolbar" part="toolbar" role="toolbar" aria-label="${t("mj.markdownEditor.toolbarLabel")}" aria-controls="${this._textareaId}">
            <slot name="toolbar-start"></slot>
            ${toolbarButtons}
            <slot name="toolbar-end"></slot>
          </div>
        </div>
        <div class="content-area">
          <div class="edit-pane" part="edit-pane">
            <textarea
              part="textarea"
              id="${this._textareaId}"
              data-mj-focus-target
            ></textarea>
          </div>
          <div class="divider" part="divider" aria-hidden="true" hidden></div>
          <div class="preview-pane" part="preview-pane"
            id="${this._previewId}"
            role="region"
            aria-label="${t("mj.markdownEditor.previewLabel")}"
            hidden>
            <div class="preview-content" part="preview-content"></div>
            <slot name="preview-empty"></slot>
          </div>
        </div>
        <div class="status-bar" part="status-bar"></div>
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
    this._outerEl = this.$(".outer")
    this._headerEl = this.$(".header")
    this._textarea = this.$("textarea")
    this._editPane = this.$(".edit-pane")
    this._previewPane = this.$(".preview-pane")
    this._previewContent = this.$(".preview-content")
    this._previewEmptySlot = this.$("slot[name='preview-empty']")
    this._divider = this.$(".divider")
    this._toolbar = this.$(".toolbar")
    this._statusBar = this.$(".status-bar")
    this._helpEl = this.$(".help")
    this._errorEl = this.$(".error")
    this._modeTabs = this.$all(".mode-tab")

    /* The value attribute is the initial content until the user edits. */
    if (this._dirty === false && this.hasAttribute("value") === true) {
      this._setFormValue(this.getAttribute("value"))
    }
    this._textarea.value = this._value

    /* A fresh shadow DOM starts in edit layout: apply the wanted view again. */
    this._currentView = null
    this._syncAll()

    this.listen(this._textarea, "input", this._onTextareaInput.bind(this))
    this.listen(this._textarea, "blur", this._onTextareaBlur.bind(this))
    this.listen(this._textarea, "focus", this._onTextareaFocus.bind(this))
    this.listen(this._textarea, "keydown", this._onKeydown.bind(this))
    this.listen(this.$(".mode-tabs"), "click", this._onTabClick.bind(this))
    this.listen(this.$(".mode-tabs"), "keydown", this._onTabKeydown.bind(this))
    this.listen(this._toolbar, "click", this._onToolbarClick.bind(this))
    this.listen(this, "invalid", this._onInvalid.bind(this))

    this.onTeardown(() => {
      if (this._previewDebounce !== null) {
        clearTimeout(this._previewDebounce)
        this._previewDebounce = null
      }
    })
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "value") {
      /* Like a native control, the attribute stops applying once edited. */
      if (this._dirty === false) {
        this._setFormValue(newValue !== null ? newValue : "")
        if (this._textarea !== undefined && this._textarea !== null) {
          this._textarea.value = this._value
        }
      }
    }

    if (this._textarea === undefined || this._textarea === null) {
      return
    }

    this._syncAll()

    if (name === "value" && this._currentView !== "edit") {
      this._updatePreview()
    }
    if (name === "required" || name === "minlength" || name === "maxlength") {
      this._refreshValidity()
    }
    return
  }

  /* ----- rendering helpers ----- */

  _syncAll() {
    const label = this.getAttribute("label") || ""
    const placeholder = this.getAttribute("placeholder") || ""
    const helpText = this.getAttribute("help-text") || ""
    const disabled = this.hasAttribute("disabled")
    const readonly = this.hasAttribute("readonly")
    const required = this.hasAttribute("required")
    const maxlength = this.getAttribute("maxlength")
    const editable = disabled === false && readonly === false

    this._labelEl.textContent = label
    this._textarea.placeholder = placeholder
    this._textarea.disabled = disabled
    this._textarea.readOnly = readonly
    this._textarea.required = required
    this._helpEl.textContent = helpText

    if (label.length > 0) {
      this._textarea.removeAttribute("aria-label")
    } else {
      this._textarea.setAttribute("aria-label", this.getAttribute("aria-label") || placeholder || t("mj.markdownEditor.label"))
    }

    if (maxlength !== null) {
      this._textarea.setAttribute("maxlength", maxlength)
    } else {
      this._textarea.removeAttribute("maxlength")
    }

    const buttons = this.$all(".tb-btn")
    for (let index = 0; index < buttons.length; index = index + 1) {
      buttons[index].disabled = editable === false
    }
    for (let index = 0; index < this._modeTabs.length; index = index + 1) {
      this._modeTabs[index].disabled = disabled
    }

    this._headerEl.hidden = readonly
    this._applyView(this._effectiveView())
    this._syncDescribedBy()
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
      this._textarea.setAttribute("aria-describedby", ids.join(" "))
    } else {
      this._textarea.removeAttribute("aria-describedby")
    }
    return
  }

  /* The view to show: the `view` attribute, or preview while read-only. */
  _effectiveView() {
    const requested = this.getAttribute("view") || "edit"
    let view = "edit"
    for (let index = 0; index < VIEW_MODES.length; index = index + 1) {
      if (VIEW_MODES[index].view === requested) {
        view = requested
      }
    }
    if (this.hasAttribute("readonly") === true) {
      view = "preview"
    }
    return view
  }

  /*
   * Show `view`. A no-op when it is already shown, so attribute changes
   * that do not affect the view cost nothing. Returns true when the view
   * changed.
   */
  _applyView(view) {
    if (this._currentView === view) {
      return false
    }
    this._currentView = view

    this._editPane.hidden = view === "preview"
    this._divider.hidden = view !== "split"
    this._previewPane.hidden = view === "edit"
    this._toolbar.hidden = view === "preview"

    for (let index = 0; index < this._modeTabs.length; index = index + 1) {
      const tab = this._modeTabs[index]
      const selected = tab.getAttribute("data-view") === view
      tab.setAttribute("aria-checked", selected === true ? "true" : "false")
      tab.tabIndex = selected === true ? 0 : -1
    }

    if (view !== "edit") {
      this._updatePreview()
    }
    return true
  }

  /* The user picked a view: reflect it and announce the change once. */
  _selectView(view) {
    const before = this._currentView
    this.setAttribute("view", view)
    if (this._currentView !== before) {
      this.emit("mj-view-change", { view: this._currentView })
    }
    return
  }

  _onTabClick(event) {
    const tab = event.target.closest(".mode-tab")
    if (tab === null) {
      return
    }
    this._selectView(tab.getAttribute("data-view"))
    return
  }

  /* Radio-group keyboard model: arrows move and select, Home/End jump. */
  _onTabKeydown(event) {
    const current = this._modeTabs.indexOf(this.shadowRoot.activeElement)
    if (current === -1) {
      return
    }

    const rtl = getComputedStyle(this).direction === "rtl"
    const count = this._modeTabs.length
    let next = -1

    if (event.key === "ArrowRight" || event.key === "ArrowDown") {
      next = event.key === "ArrowRight" && rtl === true ? current - 1 : current + 1
    } else if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
      next = event.key === "ArrowLeft" && rtl === true ? current + 1 : current - 1
    } else if (event.key === "Home") {
      next = 0
    } else if (event.key === "End") {
      next = count - 1
    } else {
      return
    }

    event.preventDefault()
    next = (next + count) % count
    this._selectView(this._modeTabs[next].getAttribute("data-view"))
    this._modeTabs[next].focus()
    return
  }

  /* ----- editing ----- */

  _isEditable() {
    const editable = this.hasAttribute("disabled") === false && this.hasAttribute("readonly") === false
    return editable
  }

  _onToolbarClick(event) {
    const btn = event.target.closest(".tb-btn")
    if (btn === null || btn.disabled === true || this._isEditable() === false) {
      return
    }
    const syntax = btn.getAttribute("data-syntax") || ""
    this._textarea.focus()
    this._insertSyntax(syntax)
    return
  }

  /*
   * Wrap the selection in `syntax` and select the result. The edit goes
   * through `insertText` so it lands in the undo history, and is then
   * committed through the same path as typing: form value, status bar,
   * preview and mj-input.
   */
  _insertSyntax(syntax) {
    if (this._isEditable() === false) {
      return
    }

    const start = this._textarea.selectionStart
    const end = this._textarea.selectionEnd
    const selected = this._textarea.value.substring(start, end)
    const inserted = syntax.replace("{sel}", selected.length > 0 ? selected : "text")

    /*
     * A multi-line insertion can raise several `input` events; they are
     * held back so the edit is committed, and mj-input emitted, once.
     */
    let handled = false
    this._suppressInput = true
    try {
      handled = document.execCommand("insertText", false, inserted) === true
    } catch (error) {
      handled = false
    }
    this._suppressInput = false

    if (handled === false) {
      this._textarea.setRangeText(inserted, start, end, "end")
    }
    this._commitTextareaValue()

    this._textarea.setSelectionRange(start, start + inserted.length)
    return
  }

  _onKeydown(event) {
    const key = event.key.toLowerCase()
    const mod = event.ctrlKey === true || event.metaKey === true
    if (mod === false || event.altKey === true) {
      return
    }

    let syntax = null
    if (key === "b") {
      syntax = "**{sel}**"
    } else if (key === "i") {
      syntax = "_{sel}_"
    } else if (key === "k") {
      syntax = "[{sel}](url)"
    }

    if (syntax !== null) {
      event.preventDefault()
      this._insertSyntax(syntax)
    }
    return
  }

  /* One path for every change of the textarea, typed or made by the toolbar. */
  _commitTextareaValue() {
    const val = this._textarea.value
    this._dirty = true
    this._setFormValue(val)
    this._updateStatusBar()
    this._schedulePreview()
    if (this._errorEl.hasAttribute("data-visible") === true) {
      this._runValidation(true)
    }
    this.emit("mj-input", { value: val, wordCount: countWords(val) })
    return
  }

  _onTextareaInput(event) {
    if (this._suppressInput === true) {
      return
    }
    this._commitTextareaValue()
    return
  }

  _onTextareaFocus(event) {
    this._outerEl.setAttribute("data-focused", "")
    this._valueAtFocus = this._value
    return
  }

  _onTextareaBlur(event) {
    this._outerEl.removeAttribute("data-focused")
    if (this._value !== this._valueAtFocus) {
      this._valueAtFocus = this._value
      this.emit("mj-change", { value: this._value, wordCount: countWords(this._value) })
    }
    this._runValidation(false)
    return
  }

  /* ----- preview ----- */

  _schedulePreview() {
    if (this._currentView === "edit") {
      return
    }
    if (this._previewDebounce !== null) {
      clearTimeout(this._previewDebounce)
    }
    this._previewDebounce = setTimeout(() => {
      this._previewDebounce = null
      this._updatePreview()
    }, PREVIEW_DEBOUNCE_MS)
    return
  }

  /*
   * Render the Markdown into its own container. The preview-empty slot is a
   * sibling, never overwritten, and is shown while there is nothing to
   * preview.
   */
  _updatePreview() {
    if (this._previewContent === undefined || this._previewContent === null) {
      return
    }

    const markdown = this._value !== null && this._value !== undefined ? String(this._value) : ""
    let markup = ""

    if (markdown.trim().length > 0) {
      let rendered = ""
      try {
        rendered = this._renderer(markdown)
      } catch (error) {
        console.error("[mj-markdown-editor] renderer error:", error)
        rendered = String(html`<pre>${markdown}</pre>`)
      }
      const sanitized = this._sanitizer(rendered !== null && rendered !== undefined ? String(rendered) : "")
      markup = typeof sanitized === "string" ? sanitized : ""
    }

    this._previewContent.innerHTML = markup
    this._previewContent.hidden = markup.length === 0
    this._previewEmptySlot.hidden = markup.length > 0
    return
  }

  _updateStatusBar() {
    if (this._statusBar === undefined || this._statusBar === null) {
      return
    }
    const val = this._textarea.value
    const maxlength = this.getAttribute("maxlength")
    const showWords = this.hasAttribute("count-words")

    let status = ""
    if (maxlength !== null) {
      status = `${val.length}/${maxlength}`
    }
    if (showWords === true) {
      const wordCount = countWords(val)
      const wordPart = t("mj.markdownEditor.wordCount", { count: wordCount })
      status = status.length > 0 ? `${status} • ${wordPart}` : wordPart
    }
    this._statusBar.textContent = status
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
      this._outerEl.setAttribute("data-invalid", "")
      this._textarea.setAttribute("aria-invalid", "true")
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
    this._outerEl.removeAttribute("data-invalid")
    this._textarea.setAttribute("aria-invalid", "false")
    return
  }

  /* A failed checkValidity() / reportValidity() / form submit. */
  _onInvalid(event) {
    this._runValidation(false)
    return
  }

  /* minlength / maxlength, which the inner textarea does not forward. */
  _customValidity() {
    const value = this._value !== null && this._value !== undefined ? String(this._value) : ""
    const minlength = parseInt(this.getAttribute("minlength") || "", 10)
    const maxlength = parseInt(this.getAttribute("maxlength") || "", 10)
    let message = ""

    if (isNaN(minlength) === false && value.length > 0 && value.length < minlength) {
      message = t("mj.markdownEditor.minLength", { count: minlength })
    } else if (isNaN(maxlength) === false && value.length > maxlength) {
      message = t("mj.markdownEditor.maxLength", { count: maxlength })
    }
    return message
  }

  _validationAnchor() {
    return this._textarea
  }

  /*
   * Show the inline error state for the current value and return whether
   * the control is valid. <mj-form> calls this on a failed submit.
   */
  showValidation() {
    this._refreshValidity()

    /* An invalid control raises `invalid`, which renders the error. */
    const valid = this.checkValidity()
    if (valid === true && this._textarea !== undefined && this._textarea !== null) {
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
    this._dirty = false
    this._valueAtFocus = initial
    if (this._textarea !== undefined && this._textarea !== null) {
      this._textarea.value = initial
      this._updateStatusBar()
      if (this._currentView !== "edit") {
        this._updatePreview()
      }
      this._clearValidationUi()
      this._syncDescribedBy()
    }
    return
  }

  /* ----- scriptable API ----- */

  get previewHtml() {
    let markup = ""
    if (this._previewContent !== undefined && this._previewContent !== null) {
      markup = this._previewContent.innerHTML
    }
    return markup
  }

  get wordCount() {
    const count = countWords(this._value !== null && this._value !== undefined ? String(this._value) : "")
    return count
  }

  get renderer() {
    return this._renderer
  }

  set renderer(fn) {
    if (typeof fn === "function") {
      this._renderer = fn
    } else if (fn === null || fn === undefined) {
      this._renderer = builtinRenderer
    }
    if (this._currentView !== null && this._currentView !== "edit") {
      this._updatePreview()
    }
    return
  }

  get sanitizer() {
    return this._sanitizer
  }

  set sanitizer(fn) {
    if (typeof fn === "function") {
      this._sanitizer = fn
    } else if (fn === null || fn === undefined) {
      this._sanitizer = defaultPreviewSanitizer
    }
    if (this._currentView !== null && this._currentView !== "edit") {
      this._updatePreview()
    }
    return
  }

  get value() {
    return this._value
  }

  set value(next) {
    const text = next !== null && next !== undefined ? String(next) : ""
    this._dirty = true
    this._setFormValue(text)
    if (this._textarea !== undefined && this._textarea !== null) {
      this._textarea.value = text
      this._updateStatusBar()
      if (this._currentView !== "edit") {
        this._updatePreview()
      }
    }
    return
  }

  focus(options) {
    if (this._textarea !== undefined && this._textarea !== null) {
      if (this._currentView === "preview") {
        const selected = this._modeTabs[2]
        if (this.hasAttribute("readonly") === false && selected !== undefined) {
          selected.focus(options)
        }
      } else {
        this._textarea.focus(options)
      }
    }
    return
  }
}
