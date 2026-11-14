/*
 * mjmentioninput.js
 *
 * <mj-mention-input> -- contenteditable text field with @ and # trigger
 * detection, suggestion popup, and inline mention token rendering.
 * Form-associated via ElementInternals.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { autoPosition } from "../core/overlay.js";
import { announce } from "../core/announcer.js";
import { html, safeUrl } from "../core/html.js";
import { t } from "../core/intl.js";

const STYLES = `
:host {
  display: block;
}

.mention-root {
  display: flex;
  flex-direction: column;
  gap: var(--mj-space-1);
}

.mention-label {
  font-size: var(--mj-font-size-sm);
  font-weight: var(--mj-font-weight-medium);
  color: var(--mj-text);
}

:host(:not([label])) .mention-label { display: none; }

.mention-wrapper {
  position: relative;
  border: 1px solid var(--mj-mention-border, var(--mj-border-strong));
  border-radius: var(--mj-radius-md);
  background: var(--mj-surface);
  transition: border-color var(--mj-motion-fast) var(--mj-motion-ease);
}

.mention-wrapper:focus-within {
  border-color: var(--mj-mention-focus-ring, var(--mj-focus-ring));
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

:host([disabled]) .mention-wrapper,
.mention-wrapper[data-disabled="true"] {
  opacity: 0.55;
  pointer-events: none;
}

:host([readonly]) .mention-wrapper {
  background: var(--mj-bg-subtle);
}

.mention-label[hidden],
.counter[hidden] { display: none; }

.editable {
  min-height: var(--mj-mention-min-height, var(--mj-control-height-md));
  max-height: var(--mj-mention-max-height, 200px);
  padding: var(--mj-space-2) var(--mj-space-3);
  overflow-y: auto;
  word-break: break-word;
  line-height: var(--mj-line-height);
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
  outline: none;
  white-space: pre-wrap;
}

.editable[data-empty="true"]::before {
  content: attr(data-placeholder);
  color: var(--mj-text-muted);
  pointer-events: none;
}

.mention-token {
  display: inline-block;
  background: var(--mj-mention-token-bg, color-mix(in srgb, var(--mj-accent) 12%, transparent));
  color: var(--mj-mention-token-color, var(--mj-accent));
  border-radius: var(--mj-mention-token-radius, var(--mj-radius-sm));
  padding: 0 var(--mj-space-1);
  font-weight: var(--mj-font-weight-medium);
  cursor: default;
  user-select: none;
  white-space: nowrap;
}

.suggestion-popup {
  position: fixed;
  z-index: var(--mj-layer-popover);
  background: var(--mj-surface-raised);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-md);
  box-shadow: var(--mj-elevation-2);
  min-width: 220px;
  max-height: 240px;
  overflow-y: auto;
  padding: var(--mj-space-1) 0;
}

.suggestion-popup[hidden] { display: none; }

.suggestion-item {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  padding: var(--mj-space-2) var(--mj-space-3);
  cursor: pointer;
  font: inherit;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
  background: transparent;
  border: none;
  width: 100%;
  text-align: start;
}

.suggestion-item:hover,
.suggestion-item[aria-selected="true"] {
  background: var(--mj-bg-muted);
}

.suggestion-item:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: calc(-1 * var(--mj-focus-ring-offset));
}

.suggestion-avatar {
  width: 24px;
  height: 24px;
  border-radius: var(--mj-radius-circle);
  background: var(--mj-bg-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--mj-font-size-xs);
  font-weight: var(--mj-font-weight-bold);
  color: var(--mj-text-muted);
  flex-shrink: 0;
  overflow: hidden;
}

.suggestion-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.suggestion-name { flex: 1; }
.suggestion-subtitle { font-size: var(--mj-font-size-xs); color: var(--mj-text-muted); }

.no-suggestions {
  padding: var(--mj-space-2) var(--mj-space-3);
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text-muted);
}

.counter {
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
  text-align: end;
}

.counter[data-over-limit="true"] { color: var(--mj-color-danger); }
`;

function initials(name) {
  const text = name !== null && name !== undefined ? String(name).trim() : ""
  if (text.length === 0) {
    return "?"
  }
  const parts = text.split(/\s+/)
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  }
  return parts[0][0].toUpperCase()
}

/*
 * `contenteditable="plaintext-only"` keeps pasted and dropped content plain
 * and inserts line breaks as text. Where it is not supported the attribute
 * value is invalid and the element would not be editable at all, so the
 * component falls back to "true" and filters paste itself.
 */
function detectPlaintextOnly() {
  let supported = false
  if (typeof document !== "undefined") {
    const probe = document.createElement("div")
    try {
      probe.contentEditable = "plaintext-only"
      supported = probe.contentEditable === "plaintext-only"
    } catch (error) {
      supported = false
    }
  }
  return supported
}

const PLAINTEXT_ONLY_SUPPORTED = detectPlaintextOnly();

/*
 * Collect the plain text of the editable region into `parts`. Mention tokens
 * contribute their visible text, <br> is a line break, and a block element
 * (the <div> some browsers wrap a new line in) starts a new line. A <br>
 * that is the last node of its parent only keeps an empty line open.
 */
function collectText(node, parts) {
  const children = node.childNodes

  for (let i = 0; i < children.length; i = i + 1) {
    const child = children[i]

    if (child.nodeType === Node.TEXT_NODE) {
      parts.push(child.data)
    } else if (child.nodeType === Node.ELEMENT_NODE) {
      if (child.classList.contains("mention-token") === true) {
        parts.push(child.textContent)
      } else if (child.localName === "br") {
        if (i < children.length - 1) {
          parts.push("\n")
        }
      } else {
        const isBlock = child.localName === "div" || child.localName === "p"
        if (isBlock === true && parts.length > 0) {
          parts.push("\n")
        }
        collectText(child, parts)
      }
    }
  }
  return
}

export class MjMentionInput extends FormControlMixin(MjElement) {
  static tagName = "mj-mention-input";
  static styles = STYLES;
  static watched = [
    "placeholder", "multiline", "max-length", "triggers", "disabled", "readonly", "required", "label", "name"
  ];

  constructor() {
    super()
    this._initFormControl()
    this._mentionSource = null
    this._activeTrigger = null
    this._activeQuery = ""
    this._suggestions = []
    this._selectedSuggestionIndex = -1
    this._debounceTimer = null

    /* Incremented per suggestion request and on close; older responses are dropped. */
    this._requestSequence = 0
    this._positionDispose = null
    this._formDisabled = false
    this._lastValue = ""

    /* A value assigned before the first render, applied by afterRender. */
    this._pendingValue = null

    /* The editable's nodes (text and tokens), carried across a reconnect. */
    this._savedContent = null

    this._labelId = nextId("mj-mi-label")
    this._popupId = nextId("mj-mi-popup")

    this._editable = null
    this._popup = null
    this._counter = null
    this._labelEl = null
    this._wrapper = null
  }

  render() {
    /*
     * A re-render replaces the shadow DOM. Lift the typed content out first
     * so afterRender can put the same nodes (mention tokens included) back.
     */
    if (this._editable !== null) {
      const saved = document.createDocumentFragment()
      while (this._editable.firstChild !== null) {
        saved.appendChild(this._editable.firstChild)
      }
      this._savedContent = saved
    }

    const markup = html`
      <label class="mention-label" part="label" id="${this._labelId}" hidden></label>
      <div class="mention-wrapper">
        <div class="editable" part="editable"
             role="textbox"
             aria-autocomplete="list"
             aria-haspopup="listbox"
             aria-controls="${this._popupId}"
             spellcheck="true"></div>
      </div>
      <div class="counter" part="counter" aria-live="polite" hidden></div>
      <div class="suggestion-popup" part="suggestion-popup"
           role="listbox" aria-label="${t("mj.mentionInput.suggestionsLabel")}"
           id="${this._popupId}" hidden></div>
    `
    return markup
  }

  afterRender() {
    this._editable = this.$(".editable")
    this._popup = this.$(".suggestion-popup")
    this._counter = this.$(".counter")
    this._labelEl = this.$(".mention-label")
    this._wrapper = this.$(".mention-wrapper")

    this.listen(this._editable, "beforeinput", this._onBeforeInput.bind(this))
    this.listen(this._editable, "input", this._onInput.bind(this))
    this.listen(this._editable, "keydown", this._onKeydown.bind(this))
    this.listen(this._editable, "paste", this._onPaste.bind(this))
    this.listen(this._editable, "blur", this._onBlur.bind(this))
    this.listen(this._popup, "click", this._onPopupClick.bind(this))
    /* Keep focus (and the caret) in the editable while a suggestion is clicked. */
    this.listen(this._popup, "mousedown", (event) => { event.preventDefault() })
    this.listen(this._labelEl, "click", () => { this.focus() })

    this.onTeardown(() => {
      this._cancelSuggestions()
    })

    /* Content: carried over from before a reconnect, assigned early, or the attribute. */
    if (this._savedContent !== null) {
      this._editable.appendChild(this._savedContent)
      this._savedContent = null
    } else if (this._pendingValue !== null) {
      this._editable.textContent = this._pendingValue
    } else if (this.hasAttribute("value") === true) {
      this._editable.textContent = this.getAttribute("value")
    }
    this._pendingValue = null

    this._syncLabels()
    this._syncEditableState()
    this._afterContentChange()
    this._lastValue = this.value
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._editable === undefined || this._editable === null) {
      return
    }

    if (name === "disabled" || name === "readonly") {
      this._syncEditableState()
    } else if (name === "placeholder" || name === "label" || name === "multiline") {
      this._syncLabels()
    } else if (name === "required") {
      this._syncLabels()
      this._refreshValidity()
    } else if (name === "max-length") {
      this._updateCounter()
      this._refreshValidity()
    }
    return
  }

  onFormDisabled(disabled) {
    this._formDisabled = disabled === true
    /* The platform can call this before the first render (a `disabled` attribute in the markup). */
    if (this._editable !== undefined && this._editable !== null) {
      this._syncEditableState()
    }
    return
  }

  onFormReset(initial) {
    this._applyValue(initial)
    return
  }

  onFormRestore(state) {
    this._applyValue(typeof state === "string" ? state : "")
    return
  }

  _validationAnchor() {
    return this._editable
  }

  _customValidity() {
    let message = ""
    const maxLength = this._maxLength()
    if (maxLength > 0 && this.value.length > maxLength) {
      message = t("mj.mentionInput.tooLong", { count: maxLength })
    }
    return message
  }

  /* ----- state helpers ----- */

  _maxLength() {
    const parsed = parseInt(this.getAttribute("max-length") || "0", 10)
    const maxLength = Number.isFinite(parsed) === true && parsed > 0 ? parsed : 0
    return maxLength
  }

  _isMultiline() {
    const multiline = this.getAttribute("multiline") !== "false"
    return multiline
  }

  _isEditable() {
    const editable = this.hasAttribute("disabled") === false && this._formDisabled === false &&
      this.hasAttribute("readonly") === false
    return editable
  }

  /* Label, placeholder and the ARIA attributes derived from them. */
  _syncLabels() {
    const label = this.getAttribute("label") || ""
    const placeholder = this.getAttribute("placeholder") || ""

    this._labelEl.textContent = label
    this._labelEl.hidden = label.length === 0

    if (label.length > 0) {
      this._editable.setAttribute("aria-labelledby", this._labelId)
      this._editable.removeAttribute("aria-label")
    } else {
      this._editable.removeAttribute("aria-labelledby")
      this._editable.setAttribute("aria-label", placeholder)
    }

    this._editable.setAttribute("aria-placeholder", placeholder)
    this._editable.setAttribute("data-placeholder", placeholder)
    this._editable.setAttribute("aria-multiline", this._isMultiline() === true ? "true" : "false")
    this._editable.setAttribute("aria-required", this.hasAttribute("required") === true ? "true" : "false")
    return
  }

  /*
   * disabled: not editable, not focusable, aria-disabled.
   * readonly: not editable but still focusable so the text can be read and
   * copied, aria-readonly.
   */
  _syncEditableState() {
    const disabled = this.hasAttribute("disabled") === true || this._formDisabled === true
    const readonly = this.hasAttribute("readonly") === true

    if (disabled === true || readonly === true) {
      this._editable.setAttribute("contenteditable", "false")
      this._closePopup()
    } else {
      this._editable.setAttribute("contenteditable", PLAINTEXT_ONLY_SUPPORTED === true ? "plaintext-only" : "true")
    }

    if (disabled === true) {
      this._editable.removeAttribute("tabindex")
      this._editable.setAttribute("aria-disabled", "true")
      this._wrapper.setAttribute("data-disabled", "true")
    } else {
      this._editable.removeAttribute("aria-disabled")
      this._wrapper.removeAttribute("data-disabled")
    }

    if (readonly === true && disabled === false) {
      this._editable.setAttribute("tabindex", "0")
      this._editable.setAttribute("aria-readonly", "true")
    } else {
      this._editable.removeAttribute("aria-readonly")
      if (disabled === false) {
        this._editable.removeAttribute("tabindex")
      }
    }
    return
  }

  /* Bring form value, counter and placeholder in line with the editable's content. */
  _afterContentChange() {
    let text = this.value

    /* Browsers leave a lone <br> or newline behind when everything is deleted. */
    const hasTokens = this._editable.querySelector(".mention-token") !== null
    if (hasTokens === false && (text === "" || text === "\n") && this._editable.firstChild !== null) {
      this._editable.textContent = ""
      text = ""
    }

    this._editable.setAttribute("data-empty", text.length === 0 && hasTokens === false ? "true" : "false")
    this._setFormValue(text)
    this._updateCounter()
    return
  }

  _updateCounter() {
    const maxLength = this._maxLength()
    this._counter.hidden = maxLength <= 0
    if (maxLength > 0) {
      const length = this.value.length
      this._counter.textContent = `${length} / ${maxLength}`
      this._counter.setAttribute("data-over-limit", length > maxLength ? "true" : "false")
    }
    return
  }

  /* Replace the content with plain text (tokens are dropped). */
  _applyValue(text) {
    const next = text !== null && text !== undefined ? String(text) : ""
    if (this._editable === null) {
      this._pendingValue = next
      this._value = next
      return
    }
    this._closePopup()
    this._editable.textContent = next
    this._afterContentChange()
    this._lastValue = this.value
    return
  }

  /* ----- selection ----- */

  /*
   * The caret inside the editable, or null. `window.getSelection()` reports
   * a caret in a shadow tree retargeted to the host's parent, so the range
   * is read with getComposedRanges (standard) or the shadow root's own
   * getSelection (Chromium), falling back to the document selection where
   * neither exists (older Firefox does not retarget).
   */
  _getCaretRange() {
    const selection = document.getSelection()
    if (selection === null) {
      return null
    }

    const candidates = []

    if (typeof selection.getComposedRanges === "function") {
      try {
        const composed = selection.getComposedRanges({ shadowRoots: [this.shadowRoot] })
        if (composed.length > 0) {
          candidates.push(composed[0])
        }
      } catch (error) {
        /* Older signature; tried next. */
      }
      try {
        const composed = selection.getComposedRanges(this.shadowRoot)
        if (composed.length > 0) {
          candidates.push(composed[0])
        }
      } catch (error) {
        /* Not supported in this form. */
      }
    }

    if (typeof this.shadowRoot.getSelection === "function") {
      const shadowSelection = this.shadowRoot.getSelection()
      if (shadowSelection !== null && shadowSelection.rangeCount > 0) {
        candidates.push(shadowSelection.getRangeAt(0))
      }
    }

    if (selection.rangeCount > 0) {
      candidates.push(selection.getRangeAt(0))
    }

    let found = null
    for (let i = 0; i < candidates.length && found === null; i = i + 1) {
      const candidate = candidates[i]
      if (this._editable.contains(candidate.startContainer) === true &&
          this._editable.contains(candidate.endContainer) === true) {
        found = candidate
      }
    }
    return found
  }

  _setCaret(node, offset) {
    const selection = document.getSelection()
    if (selection !== null) {
      selection.setBaseAndExtent(node, offset, node, offset)
    }
    return
  }

  /* Number of characters the current selection would replace. */
  _selectedLength() {
    let length = 0
    const caret = this._getCaretRange()
    if (caret !== null && caret.collapsed === false) {
      const range = document.createRange()
      range.setStart(caret.startContainer, caret.startOffset)
      range.setEnd(caret.endContainer, caret.endOffset)
      length = range.toString().length
    }
    return length
  }

  /* ----- input ----- */

  /* Refuse input that would exceed max-length (before it changes the content). */
  _onBeforeInput(event) {
    const maxLength = this._maxLength()
    const inputType = event.inputType || ""
    if (maxLength <= 0 || inputType.startsWith("insert") === false || event.cancelable === false) {
      return
    }

    let insertedLength = 1
    if (typeof event.data === "string") {
      insertedLength = event.data.length
    } else if (event.dataTransfer !== null && event.dataTransfer !== undefined) {
      insertedLength = event.dataTransfer.getData("text/plain").length
    }

    const resulting = this.value.length - this._selectedLength() + insertedLength
    if (resulting > maxLength) {
      event.preventDefault()
      announce(t("mj.mentionInput.maxLengthReached", { count: maxLength }), "polite")
    }
    return
  }

  /*
   * Input that could not be refused beforehand (an IME composition is not
   * cancelable) is trimmed here: the overflow is removed from the text just
   * before the caret, leaving mention tokens untouched.
   */
  _trimOverflow() {
    const maxLength = this._maxLength()
    if (maxLength <= 0) {
      return
    }
    const overflow = this.value.length - maxLength
    if (overflow <= 0) {
      return
    }

    const caret = this._getCaretRange()
    if (caret !== null && caret.startContainer.nodeType === Node.TEXT_NODE && caret.startOffset >= overflow) {
      const textNode = caret.startContainer
      const start = caret.startOffset - overflow
      textNode.deleteData(start, overflow)
      this._setCaret(textNode, start)
      announce(t("mj.mentionInput.maxLengthReached", { count: maxLength }), "polite")
    }
    return
  }

  _onInput() {
    this._trimOverflow()
    this._afterContentChange()
    this._detectTrigger()
    this.emit("mj-input", { value: this.value, mentions: this.mentions })
    return
  }

  /* Paste as plain text; single-line fields take no line breaks. */
  _onPaste(event) {
    if (event.clipboardData === null || event.clipboardData === undefined) {
      return
    }
    event.preventDefault()
    if (this._isEditable() === false) {
      return
    }

    let text = event.clipboardData.getData("text/plain")
    if (this._isMultiline() === false) {
      text = text.replace(/\s*[\r\n]+\s*/g, " ")
    }

    const maxLength = this._maxLength()
    if (maxLength > 0) {
      const room = Math.max(0, maxLength - (this.value.length - this._selectedLength()))
      if (text.length > room) {
        text = text.slice(0, room)
        announce(t("mj.mentionInput.maxLengthReached", { count: maxLength }), "polite")
      }
    }

    if (text.length > 0) {
      this._insertTextAtCaret(text)
    }
    return
  }

  /*
   * Insert plain text at the caret. The editing command keeps the browser's
   * undo history and fires the input events; where it is refused the text
   * is inserted through the DOM.
   */
  _insertTextAtCaret(text) {
    let inserted = false
    try {
      inserted = document.execCommand("insertText", false, text)
    } catch (error) {
      inserted = false
    }

    if (inserted === false) {
      const caret = this._getCaretRange()
      const textNode = document.createTextNode(text)
      if (caret !== null) {
        const range = document.createRange()
        range.setStart(caret.startContainer, caret.startOffset)
        range.setEnd(caret.endContainer, caret.endOffset)
        range.deleteContents()
        range.insertNode(textNode)
      } else {
        this._editable.appendChild(textNode)
      }
      this._setCaret(textNode, textNode.length)
      this._onInput()
    }
    return
  }

  /* ----- trigger detection and suggestions ----- */

  _detectTrigger() {
    if (this._isEditable() === false) {
      return
    }

    const caret = this._getCaretRange()
    if (caret === null || caret.collapsed === false || caret.startContainer.nodeType !== Node.TEXT_NODE) {
      this._closePopup()
      return
    }

    const textBefore = caret.startContainer.data.slice(0, caret.startOffset)
    const triggers = this.getAttribute("triggers") || "@#"
    const minLen = parseInt(this.getAttribute("min-trigger-length") || "1", 10)

    /* Scan backward for a trigger character. */
    for (let i = textBefore.length - 1; i >= 0; i = i - 1) {
      const ch = textBefore[i]
      if (/\s/.test(ch) === true) {
        /* Whitespace between the caret and any trigger: not a mention. */
        break
      }
      if (triggers.indexOf(ch) >= 0) {
        /* A trigger opens a mention only at the start of a word (not in a@b.c). */
        const atWordStart = i === 0 || /\s/.test(textBefore[i - 1]) === true
        const query = textBefore.slice(i + 1)
        if (atWordStart === true && query.length >= minLen) {
          if (this._activeTrigger !== ch || this._activeQuery !== query) {
            this._activeTrigger = ch
            this._activeQuery = query
            this.emit("mj-mention-trigger", { trigger: ch, query: query })
            this._fetchSuggestions(ch, query)
          }
          return
        }
        break
      }
    }

    this._closePopup()
    return
  }

  _fetchSuggestions(trigger, query) {
    if (this._mentionSource === null || this._mentionSource === undefined) {
      this._closePopup()
      return
    }

    if (this._debounceTimer !== null) {
      window.clearTimeout(this._debounceTimer)
    }

    this._requestSequence = this._requestSequence + 1
    const sequence = this._requestSequence

    this._debounceTimer = window.setTimeout(() => {
      this._debounceTimer = null

      let request = null
      try {
        request = Promise.resolve(this._mentionSource.suggest(trigger, query))
      } catch (error) {
        request = Promise.reject(error)
      }

      request.then(
        (suggestions) => {
          /* The popup was closed, or a newer query issued, while this one ran. */
          if (sequence === this._requestSequence) {
            this._suggestions = Array.isArray(suggestions) === true ? suggestions : []
            this._renderPopup()
          }
        },
        (error) => {
          if (sequence === this._requestSequence) {
            this._closePopup()
          }
        }
      )
    }, 200)

    return
  }

  _renderPopup() {
    this._popup.textContent = ""

    if (this._suggestions.length === 0) {
      const emptyEl = document.createElement("div")
      emptyEl.className = "no-suggestions"
      emptyEl.textContent = t("mj.mentionInput.noMatches")
      this._popup.appendChild(emptyEl)
      this._selectedSuggestionIndex = -1
      this._editable.removeAttribute("aria-activedescendant")
      this._popup.hidden = false
      this._positionPopup()
      announce(t("mj.mentionInput.noMatches"), "polite")
      return
    }

    for (let i = 0; i < this._suggestions.length; i = i + 1) {
      const suggestion = this._suggestions[i]
      const displayName = suggestion.displayName !== undefined && suggestion.displayName !== null
        ? String(suggestion.displayName)
        : String(suggestion.id)
      const btn = document.createElement("button")
      btn.className = "suggestion-item"
      btn.id = `${this._popupId}-opt-${i}`
      btn.setAttribute("part", "suggestion-item")
      btn.setAttribute("role", "option")
      btn.setAttribute("aria-selected", "false")
      btn.setAttribute("type", "button")
      btn.setAttribute("tabindex", "-1")
      btn.setAttribute("data-index", String(i))

      const avatarUrl = safeUrl(suggestion.avatarUrl, "")
      const avatar = avatarUrl.length > 0
        ? html`<img src="${avatarUrl}" alt="">`
        : initials(displayName)
      const hasSubtitle = suggestion.subtitle !== undefined && suggestion.subtitle !== null
      const subtitle = hasSubtitle === true
        ? html`<span class="suggestion-subtitle">${suggestion.subtitle}</span>`
        : ""

      btn.innerHTML = String(html`
        <span class="suggestion-avatar" aria-hidden="true">${avatar}</span>
        <span class="suggestion-name">${displayName}</span>
        ${subtitle}
      `)
      this._popup.appendChild(btn)
    }

    this._popup.hidden = false
    this._positionPopup()

    /* Highlight the first suggestion so Enter picks it. */
    this._selectedSuggestionIndex = -1
    this._highlightSuggestion(0)
    announce(t("mj.mentionInput.suggestionsAvailable"), "polite")
    return
  }

  _positionPopup() {
    if (this._positionDispose !== null) {
      this._positionDispose()
      this._positionDispose = null
    }
    this._positionDispose = autoPosition(this._popup, this._wrapper, { placement: "bottom-start", offset: 4 })
    return
  }

  /* Stop the debounce timer, invalidate in-flight requests, stop positioning. */
  _cancelSuggestions() {
    if (this._debounceTimer !== null) {
      window.clearTimeout(this._debounceTimer)
      this._debounceTimer = null
    }
    this._requestSequence = this._requestSequence + 1
    if (this._positionDispose !== null) {
      this._positionDispose()
      this._positionDispose = null
    }
    return
  }

  _closePopup() {
    this._cancelSuggestions()
    if (this._popup !== null) {
      this._popup.hidden = true
      this._popup.textContent = ""
    }
    if (this._editable !== null) {
      this._editable.removeAttribute("aria-activedescendant")
    }
    this._activeTrigger = null
    this._activeQuery = ""
    this._suggestions = []
    this._selectedSuggestionIndex = -1
    return
  }

  /* Dismiss the popup without a selection and tell the host. */
  _cancelMention() {
    const trigger = this._activeTrigger
    const wasActive = trigger !== null
    this._closePopup()
    if (wasActive === true) {
      this.emit("mj-mention-cancel", { trigger: trigger })
    }
    return
  }

  /*
   * Mark one option as the highlighted one. DOM focus stays in the textbox;
   * aria-activedescendant tells assistive technology which option is active.
   * (aria-expanded is not set: it is not an allowed attribute on a textbox.)
   */
  _highlightSuggestion(index) {
    const items = this._popup.querySelectorAll(".suggestion-item")
    for (let i = 0; i < items.length; i = i + 1) {
      items[i].setAttribute("aria-selected", i === index ? "true" : "false")
    }

    this._selectedSuggestionIndex = index
    if (index >= 0 && index < items.length) {
      this._editable.setAttribute("aria-activedescendant", items[index].id)
      items[index].scrollIntoView({ block: "nearest" })
    } else {
      this._editable.removeAttribute("aria-activedescendant")
    }
    return
  }

  _moveSuggestion(delta) {
    const count = this._popup.querySelectorAll(".suggestion-item").length
    if (count === 0) {
      return
    }

    let next = this._selectedSuggestionIndex + delta
    if (next < 0) {
      next = count - 1
    }
    if (next >= count) {
      next = 0
    }
    this._highlightSuggestion(next)
    return
  }

  _selectSuggestion(index) {
    const suggestion = this._suggestions[index]
    const trigger = this._activeTrigger
    const query = this._activeQuery
    if (suggestion === undefined || trigger === null) {
      return
    }

    this.emit("mj-mention-select", { trigger: trigger, suggestion: suggestion })

    /* Replace the trigger + query text before the caret with the token. */
    const caret = this._getCaretRange()
    if (caret !== null && caret.startContainer.nodeType === Node.TEXT_NODE) {
      const textNode = caret.startContainer
      const typed = trigger + query
      const triggerPos = textNode.data.lastIndexOf(typed, Math.max(0, caret.startOffset - typed.length))
      if (triggerPos >= 0) {
        textNode.deleteData(triggerPos, typed.length)
        const tail = textNode.splitText(triggerPos)
        const token = this._createTokenEl(trigger, suggestion)
        tail.parentNode.insertBefore(token, tail)
        /* A space after the token, with the caret behind it. */
        tail.insertData(0, " ")
        this._setCaret(tail, 1)
      }
    }

    this._closePopup()
    this._afterContentChange()
    this.emit("mj-input", { value: this.value, mentions: this.mentions })
    return
  }

  _createTokenEl(trigger, suggestion) {
    const displayName = suggestion.displayName !== undefined && suggestion.displayName !== null
      ? String(suggestion.displayName)
      : String(suggestion.id)
    const span = document.createElement("span")
    span.className = "mention-token"
    span.setAttribute("part", "token")
    span.setAttribute("role", "img")
    span.setAttribute("aria-label", `${trigger}${displayName}`)
    span.setAttribute("contenteditable", "false")
    span.setAttribute("data-mention-id", String(suggestion.id))
    span.setAttribute("data-trigger", trigger)
    span.textContent = `${trigger}${displayName}`

    /* The structured mention travels with its token; `mentions` reads it back. */
    span._mjMention = {
      trigger: trigger,
      id: suggestion.id,
      displayName: displayName,
      type: suggestion.type || "user"
    }
    return span
  }

  /* ----- keyboard ----- */

  /* The mention token directly before (direction -1) or after (1) a collapsed caret. */
  _tokenBesideCaret(direction) {
    let token = null
    const caret = this._getCaretRange()

    if (caret !== null && caret.collapsed === true) {
      const node = caret.startContainer
      let neighbour = null

      if (node.nodeType === Node.TEXT_NODE) {
        if (direction < 0 && caret.startOffset === 0) {
          neighbour = node.previousSibling
        } else if (direction > 0 && caret.startOffset === node.data.length) {
          neighbour = node.nextSibling
        }
      } else if (node === this._editable) {
        const position = direction < 0 ? caret.startOffset - 1 : caret.startOffset
        neighbour = position >= 0 && position < node.childNodes.length ? node.childNodes[position] : null
      }

      /* Empty text nodes left behind by edits are transparent. */
      while (neighbour !== null && neighbour.nodeType === Node.TEXT_NODE && neighbour.data.length === 0) {
        neighbour = direction < 0 ? neighbour.previousSibling : neighbour.nextSibling
      }

      if (neighbour !== null && neighbour.nodeType === Node.ELEMENT_NODE &&
          neighbour.classList.contains("mention-token") === true) {
        token = neighbour
      }
    }
    return token
  }

  _submit() {
    this.emit("mj-submit", { value: this.value, mentions: this.mentions }, { cancelable: true })
    return
  }

  _onKeydown(event) {
    if (this._isEditable() === false) {
      return
    }

    const popupVisible = this._popup.hidden === false
    const multiline = this._isMultiline()
    const composing = event.isComposing === true || event.keyCode === 229

    if (popupVisible === true) {
      const hasOptions = this._suggestions.length > 0

      if (event.key === "ArrowDown" && hasOptions === true) {
        event.preventDefault()
        this._moveSuggestion(1)
        return
      }
      if (event.key === "ArrowUp" && hasOptions === true) {
        event.preventDefault()
        this._moveSuggestion(-1)
        return
      }
      if (event.key === "Enter" && composing === false && hasOptions === true && this._selectedSuggestionIndex >= 0) {
        event.preventDefault()
        this._selectSuggestion(this._selectedSuggestionIndex)
        return
      }
      if (event.key === "Escape") {
        event.preventDefault()
        event.stopPropagation()
        this._cancelMention()
        return
      }
      if (event.key === "Tab") {
        this._cancelMention()
        return
      }
      if (event.key === "Enter" && composing === false) {
        /* "No matches": nothing to pick, so Enter acts as it does without a popup. */
        this._cancelMention()
      }
    }

    if (event.key === "Escape" && this._activeTrigger !== null) {
      /* Suggestions were requested but are not shown yet: drop the request. */
      this._cancelMention()
      return
    }

    if (event.key === "Enter" && composing === false) {
      if (multiline === false || event.shiftKey === false) {
        event.preventDefault()
        this._submit()
      }
      return
    }

    if (event.key === "Backspace" || event.key === "Delete") {
      const token = this._tokenBesideCaret(event.key === "Backspace" ? -1 : 1)
      if (token !== null) {
        event.preventDefault()
        token.remove()
        this._afterContentChange()
        this.emit("mj-input", { value: this.value, mentions: this.mentions })
      }
    }

    return
  }

  _onPopupClick(event) {
    const btn = event.target.closest(".suggestion-item")
    if (btn === null) {
      return
    }
    const index = parseInt(btn.getAttribute("data-index") || "0", 10)
    this._selectSuggestion(index)
    this._editable.focus()
    return
  }

  _onBlur() {
    const currentValue = this.value
    if (currentValue !== this._lastValue) {
      this._lastValue = currentValue
      this.emit("mj-change", { value: currentValue, mentions: this.mentions })
    }
    /* Clicking a suggestion does not blur (see the mousedown listener). */
    this._cancelMention()
    return
  }

  /* ----- public API ----- */

  /*
   * The plain text of the field. Mention tokens appear as their visible
   * text (`@Alice Martin`) and line breaks as "\n". Assigning replaces the
   * content with plain text.
   */
  get value() {
    let text = ""
    if (this._editable === null) {
      text = this._pendingValue !== null ? this._pendingValue : ""
    } else {
      const parts = []
      collectText(this._editable, parts)
      text = parts.join("")
    }
    return text
  }

  set value(text) {
    this._applyValue(text)
    return
  }

  /*
   * The resolved mentions, read from the tokens currently in the field, in
   * document order: { trigger, id, displayName, type }.
   */
  get mentions() {
    const mentions = []
    if (this._editable !== null) {
      const tokens = this._editable.querySelectorAll(".mention-token")
      for (let i = 0; i < tokens.length; i = i + 1) {
        const token = tokens[i]
        if (token._mjMention !== undefined) {
          mentions.push(token._mjMention)
        } else {
          const trigger = token.getAttribute("data-trigger") || ""
          mentions.push({
            trigger: trigger,
            id: token.getAttribute("data-mention-id"),
            displayName: token.textContent.slice(trigger.length),
            type: "user"
          })
        }
      }
    }
    return mentions
  }

  get mentionSource() {
    return this._mentionSource
  }

  set mentionSource(source) {
    this._mentionSource = source !== undefined ? source : null
    return
  }

  focus(options) {
    if (this._editable !== null) {
      this._editable.focus(options)
    }
    return
  }
}
