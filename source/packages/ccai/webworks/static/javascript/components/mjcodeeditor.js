/*
 * mjcodeeditor.js
 *
 * <mj-code-editor> -- code authoring on a plain <textarea> with a mirrored
 * display layer, line numbers, proper Tab handling, and form participation.
 * Syntax colouring is supplied by the page through the `highlighter`
 * property; without one the code is shown as plain text.
 *
 * The highlighter returns markup of inline elements carrying a `class`
 * (sanitized to HIGHLIGHT_SANITIZE_OPTIONS). The layer lives in the shadow
 * root, so the page styles the tokens in one of two ways:
 *   - `highlightStyles`: CSS text (or a CSSStyleSheet) adopted into the
 *     shadow root, so a class-based theme applies as written
 *     (`.tok-keyword { color: ... }`);
 *   - parts: every element in the output is exported as part `token` plus
 *     `token-<class>` per class (`mj-code-editor::part(token-tok-keyword)`).
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";
import { sanitizeHtml } from "../core/sanitize.js";

const STYLES = `
:host {
  display: block;
  font-family: var(--mj-font-sans);
  font-size: var(--mj-font-size-md);
  --mj-code-editor-font-size: var(--mj-font-size-sm);
}
:host([size="sm"]) { --mj-code-editor-font-size: var(--mj-font-size-xs); }
:host([size="lg"]) { --mj-code-editor-font-size: var(--mj-font-size-md); }

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
}
.outer[data-focused] { border-color: var(--mj-accent); outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: var(--mj-focus-ring-offset); }
.outer[data-invalid] { border-color: var(--mj-color-danger); }

.toolbar-slot { border-block-end: 1px solid var(--mj-border); background: var(--mj-bg-subtle); }
.toolbar-slot[hidden] { display: none; }

/*
 * One height model with or without the gutter: the container has a fixed
 * block size (the rows attribute or --mj-code-editor-height) and the code
 * scrolls inside it.
 */
.container {
  display: flex;
  position: relative;
  block-size: var(--mj-code-editor-height, 12.5rem);
}

.gutter {
  min-inline-size: 3rem;
  padding: var(--mj-space-2) var(--mj-space-1);
  background: var(--mj-bg-subtle);
  border-inline-end: 1px solid var(--mj-border);
  font-family: var(--mj-font-mono);
  font-size: var(--mj-code-editor-font-size);
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
  min-inline-size: 0;
  position: relative;
  overflow: hidden;
}

.highlight-layer,
.measure,
textarea {
  padding: var(--mj-space-2) var(--mj-space-3);
  margin: 0;
  border: none;
  box-sizing: border-box;
  font-family: var(--mj-font-mono);
  font-size: var(--mj-code-editor-font-size);
  line-height: 1.6;
  letter-spacing: normal;
  tab-size: 4;
  white-space: pre;
}

.highlight-layer {
  position: absolute;
  inset: 0;
  color: var(--mj-text);
  background: var(--mj-surface);
  overflow: hidden;
  pointer-events: none;
}

textarea {
  position: absolute;
  inset: 0;
  inline-size: 100%;
  block-size: 100%;
  color: transparent;
  caret-color: var(--mj-text);
  background: transparent;
  outline: none;
  resize: none;
  overflow: auto;
}
textarea::placeholder { color: var(--mj-text-muted); }

.measure {
  position: absolute;
  inset-block-start: 0;
  inset-inline-start: 0;
  block-size: 0;
  padding-block: 0;
  overflow: hidden;
  visibility: hidden;
  pointer-events: none;
}

:host([word-wrap]) textarea,
:host([word-wrap]) .highlight-layer,
:host([word-wrap]) .measure { white-space: pre-wrap; word-break: break-all; }

.below { margin-block-start: var(--mj-space-1); }
.help { font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }
.help:empty { display: none; }
.error { font-size: var(--mj-font-size-sm); color: var(--mj-color-danger); display: none; }
.error[data-visible] { display: block; }

:host([disabled]) .outer { opacity: 0.55; pointer-events: none; }
`;

/* What a highlighter may return: inline token wrappers carrying a class. */
const HIGHLIGHT_SANITIZE_OPTIONS = {
  allowedTags: ["span", "b", "i", "em", "strong", "mark", "code", "br"],
  allowedAttributes: { "*": ["class"] },
  aliases: {}
};

const HIGHLIGHT_DEBOUNCE_MS = 100;
const LINE_HEIGHT_EM = 1.6;

export class MjCodeEditor extends FormControlMixin(MjElement) {
  static tagName = "mj-code-editor";
  static styles = STYLES;
  static watched = [
    "label", "placeholder", "help-text", "error-message", "value",
    "language", "line-numbers", "word-wrap", "tab-size", "tab-inserts-spaces",
    "required", "disabled", "readonly", "maxlength", "minlength", "size", "rows",
    "aria-label"
  ];

  constructor() {
    super()
    this._initFormControl()
    this._highlighter = null
    this._highlightDebounce = null
    this._exitMode = false

    /* Page CSS for the highlighter's classes, adopted into the shadow root. */
    this._highlightStyles = null
    this._highlightSheet = null

    /* True while a programmatic edit is in flight (see _replaceRange). */
    this._suppressInput = false

    /* Set once the value was changed by the user or through the property. */
    this._dirty = false

    /* The value when the textarea took focus, compared on blur for mj-change. */
    this._valueAtFocus = ""

    this._textareaId = nextId("mjce-ta")
    this._helpId = nextId("mjce-help")
    this._errorId = nextId("mjce-error")
    this._hintId = nextId("mjce-hint")
    this._announceId = nextId("mjce-announce")

    /* Shadow references; null until the first render. */
    this._labelEl = null
    this._outerEl = null
    this._containerEl = null
    this._toolbarWrap = null
    this._toolbarSlot = null
    this._textarea = null
    this._gutter = null
    this._highlightLayer = null
    this._measureEl = null
    this._helpEl = null
    this._errorEl = null
    this._announceEl = null
    this._resizeObserver = null
  }

  render() {
    const markup = html`
      <label class="label" part="label" for="${this._textareaId}"></label>
      <div class="outer" part="outer">
        <div class="toolbar-slot" part="toolbar" hidden><slot name="toolbar"></slot></div>
        <div class="container" part="container">
          <div class="gutter" part="gutter" aria-hidden="true"></div>
          <div class="editor-area">
            <pre class="highlight-layer" part="highlight-layer" aria-hidden="true"></pre>
            <textarea
              part="textarea"
              id="${this._textareaId}"
              spellcheck="false"
              autocorrect="off"
              autocapitalize="off"
              autocomplete="off"
              wrap="off"
              data-mj-focus-target
            ></textarea>
            <div class="measure" aria-hidden="true"></div>
          </div>
        </div>
      </div>
      <span class="mj-visually-hidden" id="${this._hintId}">${t("mj.codeEditor.keyboardHint")}</span>
      <div class="mj-visually-hidden" id="${this._announceId}" aria-live="polite" role="status"></div>
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
    this._containerEl = this.$(".container")
    this._toolbarWrap = this.$(".toolbar-slot")
    this._toolbarSlot = this.$("slot[name='toolbar']")
    this._textarea = this.$("textarea")
    this._gutter = this.$(".gutter")
    this._highlightLayer = this.$(".highlight-layer")
    this._measureEl = this.$(".measure")
    this._helpEl = this.$(".help")
    this._errorEl = this.$(".error")
    this._announceEl = this.$(`#${this._announceId}`)

    /* The value attribute is the initial content until the user edits. */
    if (this._dirty === false && this.hasAttribute("value") === true) {
      this._setFormValue(this._normalize(this.getAttribute("value")))
    }
    this._textarea.value = this._value

    this._syncAll()
    this._syncToolbarSlot()
    this._renderCode(this._value, true)

    this.listen(this._textarea, "input", this._onInput.bind(this))
    this.listen(this._textarea, "focus", this._onFocus.bind(this))
    this.listen(this._textarea, "blur", this._onBlur.bind(this))
    this.listen(this._textarea, "keydown", this._onKeydown.bind(this))
    this.listen(this._textarea, "scroll", this._onScroll.bind(this))
    this.listen(this._toolbarSlot, "slotchange", this._syncToolbarSlot.bind(this))
    this.listen(this, "invalid", this._onInvalid.bind(this))

    /* Wrapped lines change height with the width: re-measure the gutter. */
    if (typeof ResizeObserver === "function") {
      this._resizeObserver = new ResizeObserver(() => {
        if (this.hasAttribute("word-wrap") === true) {
          this._updateGutter(this._textarea.value)
        }
      })
      this._resizeObserver.observe(this._textarea)
    }

    this.onTeardown(() => {
      if (this._resizeObserver !== null) {
        this._resizeObserver.disconnect()
        this._resizeObserver = null
      }
      if (this._highlightDebounce !== null) {
        clearTimeout(this._highlightDebounce)
        this._highlightDebounce = null
      }
    })
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "value") {
      /* Like a native control, the attribute stops applying once edited. */
      if (this._dirty === false) {
        this._setFormValue(this._normalize(newValue))
        if (this._textarea !== undefined && this._textarea !== null) {
          this._textarea.value = this._value
        }
      }
    }

    if (this._textarea === undefined || this._textarea === null) {
      return
    }

    this._syncAll()

    if (name === "value" || name === "line-numbers" || name === "word-wrap" || name === "language" || name === "size") {
      this._renderCode(this._textarea.value, true)
    }
    if (name === "required" || name === "minlength" || name === "maxlength") {
      this._refreshValidity()
    }
    return
  }

  /* ----- rendering helpers ----- */

  _normalize(value) {
    const text = value !== null && value !== undefined ? String(value) : ""
    const normalized = text.replace(/\r\n?/g, "\n")
    return normalized
  }

  _tabSize() {
    const parsed = parseInt(this.getAttribute("tab-size") || "4", 10)
    const size = isNaN(parsed) === false && parsed > 0 && parsed <= 16 ? parsed : 4
    return size
  }

  _syncAll() {
    const label = this.getAttribute("label") || ""
    const placeholder = this.getAttribute("placeholder") || ""
    const helpText = this.getAttribute("help-text") || ""
    const disabled = this.hasAttribute("disabled")
    const readonly = this.hasAttribute("readonly")
    const required = this.hasAttribute("required")
    const lineNumbers = this.getAttribute("line-numbers") !== "false"
    const wordWrap = this.hasAttribute("word-wrap")
    const tabSize = String(this._tabSize())
    const maxlength = this.getAttribute("maxlength")
    const rows = parseInt(this.getAttribute("rows") || "", 10)

    this._labelEl.textContent = label
    this._textarea.placeholder = placeholder
    this._textarea.disabled = disabled
    this._textarea.readOnly = readonly
    this._textarea.required = required
    this._textarea.wrap = wordWrap === true ? "soft" : "off"
    this._textarea.style.tabSize = tabSize
    this._highlightLayer.style.tabSize = tabSize
    this._measureEl.style.tabSize = tabSize
    this._gutter.hidden = lineNumbers === false
    this._helpEl.textContent = helpText

    if (label.length > 0) {
      this._textarea.removeAttribute("aria-label")
    } else {
      this._textarea.setAttribute("aria-label", this.getAttribute("aria-label") || placeholder || t("mj.codeEditor.label"))
    }

    if (maxlength !== null) {
      this._textarea.setAttribute("maxlength", maxlength)
    } else {
      this._textarea.removeAttribute("maxlength")
    }

    if (isNaN(rows) === false && rows > 0) {
      this._containerEl.style.blockSize =
        `calc(${rows} * ${LINE_HEIGHT_EM} * var(--mj-code-editor-font-size) + 2 * var(--mj-space-2))`
    } else {
      this._containerEl.style.blockSize = ""
    }

    this._syncDescribedBy()
    return
  }

  _syncDescribedBy() {
    const ids = []
    const editable = this.hasAttribute("readonly") === false && this.hasAttribute("disabled") === false

    /* The Tab-trap instructions are part of the description up front. */
    if (editable === true) {
      ids.push(this._hintId)
    }
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

  /* The toolbar wrapper (and its border) only shows when something is slotted. */
  _syncToolbarSlot() {
    const assigned = this._toolbarSlot.assignedNodes({ flatten: true })
    this._toolbarWrap.hidden = assigned.length === 0
    return
  }

  /*
   * Refresh everything derived from the code: the gutter, and the display
   * layer under the transparent textarea. The plain text is written at
   * once so typing is always visible; the highlighter pass is debounced
   * unless `immediate` is true.
   */
  _renderCode(val, immediate) {
    this._updateGutter(val)
    this._writePlainLayer(val)

    if (this._highlightDebounce !== null) {
      clearTimeout(this._highlightDebounce)
      this._highlightDebounce = null
    }

    if (this._highlighter !== null) {
      if (immediate === true) {
        this._applyHighlighter(val)
      } else {
        this._highlightDebounce = setTimeout(() => {
          this._highlightDebounce = null
          this._applyHighlighter(this._textarea.value)
        }, HIGHLIGHT_DEBOUNCE_MS)
      }
    }
    this._onScroll()
    return
  }

  _writePlainLayer(val) {
    /* A trailing newline needs a character after it to get a line box. */
    this._highlightLayer.textContent = val.endsWith("\n") === true ? `${val} ` : val
    return
  }

  _applyHighlighter(val) {
    try {
      const lang = this.getAttribute("language") || "plaintext"
      const markup = this._highlighter(val, lang)
      this._highlightLayer.innerHTML = sanitizeHtml(String(markup), HIGHLIGHT_SANITIZE_OPTIONS)
      this._exportTokenParts()
      if (val.endsWith("\n") === true) {
        this._highlightLayer.appendChild(document.createTextNode(" "))
      }
    } catch (error) {
      console.error("[mj-code-editor] highlighter error:", error)
      this._writePlainLayer(val)
    }
    return
  }

  /*
   * Export each highlighted element as part `token` plus `token-<class>`
   * for each of its classes, so the page can style it with ::part().
   */
  _exportTokenParts() {
    const tokens = this._highlightLayer.querySelectorAll("*")
    for (let index = 0; index < tokens.length; index = index + 1) {
      const token = tokens[index]
      const names = ["token"]
      for (let classIndex = 0; classIndex < token.classList.length; classIndex = classIndex + 1) {
        names.push(`token-${token.classList[classIndex]}`)
      }
      token.setAttribute("part", names.join(" "))
    }
    return
  }

  /*
   * Adopt the page's highlight stylesheet after the component's own sheets,
   * replacing the one adopted before.
   */
  _adoptHighlightSheet() {
    const sheets = this.shadowRoot.adoptedStyleSheets.filter((sheet) => sheet !== this._highlightSheet)
    let next = null
    if (this._highlightStyles instanceof CSSStyleSheet) {
      next = this._highlightStyles
    } else if (typeof this._highlightStyles === "string" && this._highlightStyles.length > 0) {
      next = new CSSStyleSheet()
      next.replaceSync(this._highlightStyles)
    }
    if (next !== null) {
      sheets.push(next)
    }
    this._highlightSheet = next
    this.shadowRoot.adoptedStyleSheets = sheets
    return
  }

  /*
   * One gutter row per source line. With word-wrap a source line can span
   * several visual rows, so each row is given the measured height of its
   * wrapped line; the measurement element has the textarea's text width.
   */
  _updateGutter(val) {
    if (this._gutter.hidden === true) {
      return
    }

    const lines = val.split("\n")
    const wrap = this.hasAttribute("word-wrap")
    let heights = null

    if (wrap === true) {
      const styles = getComputedStyle(this._textarea)
      const paddingInline = parseFloat(styles.paddingInlineStart) + parseFloat(styles.paddingInlineEnd)
      const textWidth = this._textarea.clientWidth - paddingInline

      if (textWidth > 0) {
        this._measureEl.style.inlineSize = `${this._textarea.clientWidth}px`
        const fragment = document.createDocumentFragment()
        for (let index = 0; index < lines.length; index = index + 1) {
          const row = document.createElement("div")
          row.textContent = lines[index].length > 0 ? lines[index] : "​"
          fragment.appendChild(row)
        }
        this._measureEl.textContent = ""
        this._measureEl.appendChild(fragment)

        heights = []
        const rows = this._measureEl.children
        for (let index = 0; index < rows.length; index = index + 1) {
          heights.push(rows[index].getBoundingClientRect().height)
        }
        this._measureEl.textContent = ""
      }
    }

    const fragment = document.createDocumentFragment()
    for (let index = 0; index < lines.length; index = index + 1) {
      const row = document.createElement("span")
      row.className = "gutter-line"
      row.textContent = String(index + 1)
      if (heights !== null) {
        row.style.blockSize = `${heights[index]}px`
      }
      fragment.appendChild(row)
    }
    this._gutter.textContent = ""
    this._gutter.appendChild(fragment)
    return
  }

  /* ----- editing ----- */

  /* One path for every change of the textarea, typed or made by Tab. */
  _commitTextareaValue() {
    const val = this._normalize(this._textarea.value)
    this._dirty = true
    this._setFormValue(val)
    this._exitMode = false

    this._renderCode(val, false)

    if (this._errorEl.hasAttribute("data-visible") === true) {
      this._runValidation(true)
    }

    const lineCount = val.split("\n").length
    this.emit("mj-input", { value: val, lineCount: lineCount })
    return
  }

  _onInput(event) {
    if (this._suppressInput === true) {
      return
    }
    this._commitTextareaValue()
    return
  }

  _onFocus(event) {
    this._outerEl.setAttribute("data-focused", "")
    this._exitMode = false
    this._valueAtFocus = this._value
    return
  }

  _onBlur(event) {
    this._outerEl.removeAttribute("data-focused")
    this._exitMode = false
    this._announceEl.textContent = ""

    if (this._value !== this._valueAtFocus) {
      this._valueAtFocus = this._value
      const lineCount = this._value.split("\n").length
      this.emit("mj-change", { value: this._value, lineCount: lineCount })
    }
    this._runValidation(false)
    return
  }

  _onScroll() {
    this._highlightLayer.scrollTop = this._textarea.scrollTop
    this._highlightLayer.scrollLeft = this._textarea.scrollLeft
    this._gutter.scrollTop = this._textarea.scrollTop
    return
  }

  _onKeydown(event) {
    const key = event.key
    const editable = this.hasAttribute("readonly") === false && this.hasAttribute("disabled") === false

    /* A read-only editor never traps Tab: focus simply moves on. */
    if (editable === false) {
      return
    }

    if (key === "Escape") {
      if (this._exitMode === false) {
        /* Arm the exit: this Escape belongs to the editor, not to a dialog. */
        this._exitMode = true
        this._announceEl.textContent = t("mj.codeEditor.exitAnnouncement")
        event.stopPropagation()
      }
      return
    }

    if (key === "Tab" && event.ctrlKey === false && event.altKey === false && event.metaKey === false) {
      if (this._exitMode === true) {
        this._exitMode = false
        this._announceEl.textContent = ""
        return
      }
      event.preventDefault()
      this._handleTab(event.shiftKey)
      return
    }
    return
  }

  /*
   * Replace [start, end) of the textarea with `text`. `insertText` keeps
   * the edit in the native undo history and raises `input`, which runs the
   * native undo history; where it is unavailable the range is set
   * directly. Either way the change path runs once afterwards.
   */
  _replaceRange(start, end, text) {
    const existing = this._textarea.value.substring(start, end)
    if (existing === text) {
      return
    }

    this._textarea.setSelectionRange(start, end)

    /*
     * A multi-line insertion can raise several `input` events; they are
     * held back so the edit is committed, and mj-input emitted, once.
     */
    let handled = false
    this._suppressInput = true
    try {
      if (text.length > 0) {
        handled = document.execCommand("insertText", false, text) === true
      } else {
        handled = document.execCommand("delete", false, null) === true
      }
    } catch (error) {
      handled = false
    }
    this._suppressInput = false

    if (handled === false) {
      this._textarea.setRangeText(text, start, end, "end")
    }
    this._commitTextareaValue()
    return
  }

  /* Remove one level of indentation from the start of `line`. */
  _outdentLine(line, tabSize) {
    let removed = 0
    if (line.startsWith("\t") === true) {
      removed = 1
    } else {
      const leading = line.match(/^ */)[0].length
      removed = Math.min(tabSize, leading)
    }
    const outdented = line.substring(removed)
    return outdented
  }

  /*
   * Tab with a collapsed caret inserts one indent. With a selection, Tab
   * indents and Shift+Tab outdents every selected line, and the selection
   * keeps covering the same text. Shift+Tab without a selection outdents
   * the caret's line.
   */
  _handleTab(isShift) {
    const insertSpaces = this.getAttribute("tab-inserts-spaces") !== "false"
    const tabSize = this._tabSize()
    const indent = insertSpaces === true ? " ".repeat(tabSize) : "\t"

    const start = this._textarea.selectionStart
    const end = this._textarea.selectionEnd
    const val = this._textarea.value

    if (start === end && isShift === false) {
      this._replaceRange(start, end, indent)
      return
    }

    /* The block of whole lines the selection touches. */
    const blockStart = val.lastIndexOf("\n", start - 1) + 1
    let lastTouched = end
    if (end > start && val.charAt(end - 1) === "\n") {
      /* A selection ending at the start of a line does not include that line. */
      lastTouched = end - 1
    }
    let blockEnd = val.indexOf("\n", lastTouched)
    if (blockEnd === -1) {
      blockEnd = val.length
    }

    const lines = val.substring(blockStart, blockEnd).split("\n")
    const changed = []
    for (let index = 0; index < lines.length; index = index + 1) {
      if (isShift === true) {
        changed.push(this._outdentLine(lines[index], tabSize))
      } else {
        changed.push(lines[index].length > 0 ? `${indent}${lines[index]}` : lines[index])
      }
    }

    const firstDelta = changed[0].length - lines[0].length
    const replacement = changed.join("\n")
    const totalDelta = replacement.length - (blockEnd - blockStart)

    if (totalDelta === 0) {
      return
    }

    this._replaceRange(blockStart, blockEnd, replacement)

    const newStart = Math.max(blockStart, start + firstDelta)
    const newEnd = start === end ? newStart : Math.max(newStart, end + totalDelta)
    this._textarea.setSelectionRange(newStart, newEnd)
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
      message = t("mj.codeEditor.minLength", { count: minlength })
    } else if (isNaN(maxlength) === false && value.length > maxlength) {
      message = t("mj.codeEditor.maxLength", { count: maxlength })
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
    const text = this._normalize(initial)
    this._dirty = false
    this._valueAtFocus = text
    if (text !== initial) {
      this._setFormValue(text)
    }
    if (this._textarea !== undefined && this._textarea !== null) {
      this._textarea.value = text
      this._renderCode(text, true)
      this._clearValidationUi()
      this._syncDescribedBy()
    }
    return
  }

  /* ----- scriptable API ----- */

  get highlighter() {
    return this._highlighter
  }

  set highlighter(fn) {
    if (typeof fn === "function") {
      this._highlighter = fn
    } else if (fn === null || fn === undefined) {
      this._highlighter = null
    }
    if (this._textarea !== undefined && this._textarea !== null) {
      this._renderCode(this._textarea.value, true)
    }
    return
  }

  get highlightStyles() {
    return this._highlightStyles
  }

  /*
   * CSS for the highlighter's classes: a string of CSS text or a
   * CSSStyleSheet (shareable between editors); null removes it.
   */
  set highlightStyles(styles) {
    if (styles instanceof CSSStyleSheet || typeof styles === "string") {
      this._highlightStyles = styles
    } else {
      this._highlightStyles = null
    }
    this._adoptHighlightSheet()
    return
  }

  get lineCount() {
    const value = this._value !== null && this._value !== undefined ? String(this._value) : ""
    const count = value.split("\n").length
    return count
  }

  get value() {
    return this._value
  }

  set value(next) {
    const text = this._normalize(next)
    this._dirty = true
    this._setFormValue(text)
    if (this._textarea !== undefined && this._textarea !== null) {
      this._textarea.value = text
      this._renderCode(text, true)
    }
    return
  }

  focus(options) {
    if (this._textarea !== undefined && this._textarea !== null) {
      this._textarea.focus(options)
    }
    return
  }
}
