/*
 * mjmentioninput.js
 *
 * <mj-mention-input> -- contenteditable text field with @ and # trigger
 * detection, suggestion popup, and inline mention token rendering.
 * Form-associated via ElementInternals.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { autoPosition } from "../core/overlay.js";
import { announce } from "../core/announcer.js";

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

:host([disabled]) .mention-wrapper {
  opacity: 0.55;
  pointer-events: none;
}

:host([readonly]) .mention-wrapper {
  background: var(--mj-bg-subtle);
}

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

.editable:empty::before {
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
  if (name === null || name === undefined || name.length === 0) {
    return "?"
  }
  const parts = name.trim().split(/\s+/)
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  }
  return parts[0][0].toUpperCase()
}

export class MjMentionInput extends MjElement {
  static tagName = "mj-mention-input";
  static styles = STYLES;
  static watched = ["placeholder", "multiline", "max-length", "triggers", "disabled", "readonly", "required", "label"];
  static formAssociated = true;

  constructor() {
    super()
    this._mentions = []
    this._mentionSource = null
    this._activeTrigger = null
    this._activeQuery = ""
    this._suggestions = []
    this._selectedSuggestionIndex = -1
    this._debounceTimer = null
    this._positionDispose = null
    this._internals = typeof this.attachInternals === "function" ? this.attachInternals() : null
    this._editable = null
    this._popup = null
  }

  render() {
    const label = this.getAttribute("label") || ""
    const placeholder = this.getAttribute("placeholder") || ""
    const maxLength = parseInt(this.getAttribute("max-length") || "0", 10)
    const labelHtml = label.length > 0
      ? `<label class="mention-label" part="label">${label}</label>`
      : ""
    const counterHtml = maxLength > 0
      ? `<div class="counter" part="counter" aria-live="polite">0 / ${maxLength}</div>`
      : ""
    const labelId = nextId("mj-mi-label")
    const editId = nextId("mj-mi-edit")
    const popupId = nextId("mj-mi-popup")

    const markup = `
      ${labelHtml}
      <div class="mention-wrapper">
        <div class="editable" part="editable"
             contenteditable="true"
             role="textbox"
             aria-multiline="${this.getAttribute("multiline") !== "false" ? "true" : "false"}"
             aria-placeholder="${placeholder}"
             aria-label="${label.length > 0 ? label : placeholder}"
             aria-required="${this.hasAttribute("required") ? "true" : "false"}"
             aria-autocomplete="list"
             aria-controls="${popupId}"
             data-placeholder="${placeholder}"
             id="${editId}"
             spellcheck="true"></div>
      </div>
      ${counterHtml}
      <div class="suggestion-popup" part="suggestion-popup"
           role="listbox" aria-label="Suggestions"
           id="${popupId}" hidden></div>
    `
    return markup
  }

  afterRender() {
    this._editable = this.$(".editable")
    this._popup = this.$(".suggestion-popup")
    this._counter = this.$(".counter")

    this.listen(this._editable, "input", this._onInput.bind(this))
    this.listen(this._editable, "keydown", this._onKeydown.bind(this))
    this.listen(this._editable, "blur", this._onBlur.bind(this))
    this.listen(this._popup, "click", this._onPopupClick.bind(this))

    return
  }

  _onInput() {
    this._syncFormValue()
    this._updateCounter()

    const maxLength = parseInt(this.getAttribute("max-length") || "0", 10)
    if (maxLength > 0) {
      const text = this._editable.textContent || ""
      if (text.length > maxLength) {
        // Trim to max-length
        const sel = window.getSelection()
        this._editable.textContent = text.slice(0, maxLength)
        // Move cursor to end
        if (sel !== null) {
          const range = document.createRange()
          range.selectNodeContents(this._editable)
          range.collapse(false)
          sel.removeAllRanges()
          sel.addRange(range)
        }
        announce(`Maximum length of ${maxLength} characters reached`, "polite")
      }
    }

    this._detectTrigger()
    this.emit("mj-input", { value: this.value, mentions: this._mentions })
    return
  }

  _detectTrigger() {
    const sel = window.getSelection()
    if (sel === null || sel.rangeCount === 0) {
      return
    }

    const range = sel.getRangeAt(0)
    if (range.startContainer.nodeType !== Node.TEXT_NODE) {
      return
    }

    const textBefore = range.startContainer.textContent.slice(0, range.startOffset)
    const triggers = this.getAttribute("triggers") || "@#"
    const minLen = parseInt(this.getAttribute("min-trigger-length") || "1", 10)

    // Scan backward for a trigger character
    for (let i = textBefore.length - 1; i >= 0; i = i - 1) {
      const ch = textBefore[i]
      if (ch === " " || ch === "\n") {
        // Whitespace before trigger — not a valid trigger context
        this._closePopup()
        return
      }
      if (triggers.indexOf(ch) >= 0) {
        const query = textBefore.slice(i + 1)
        if (query.length < minLen) {
          this._closePopup()
          return
        }
        if (this._activeTrigger !== ch || this._activeQuery !== query) {
          this._activeTrigger = ch
          this._activeQuery = query
          this._fetchSuggestions(ch, query)
        }
        return
      }
    }

    this._closePopup()
    return
  }

  _fetchSuggestions(trigger, query) {
    if (this._mentionSource === null) {
      this._closePopup()
      return
    }

    if (this._debounceTimer !== null) {
      window.clearTimeout(this._debounceTimer)
    }

    this._debounceTimer = window.setTimeout(() => {
      this._debounceTimer = null
      const promise = this._mentionSource.suggest(trigger, query)
      Promise.resolve(promise).then((suggestions) => {
        this._suggestions = suggestions || []
        this._selectedSuggestionIndex = -1
        this._renderPopup()
      }).catch(() => {
        this._closePopup()
      })
    }, 200)

    return
  }

  _renderPopup() {
    if (this._popup === null) {
      return
    }

    if (this._suggestions.length === 0) {
      this._popup.innerHTML = `<div class="no-suggestions">No matches</div>`
      this._popup.hidden = false
      this._positionPopup()
      return
    }

    this._popup.innerHTML = ""
    for (let i = 0; i < this._suggestions.length; i = i + 1) {
      const s = this._suggestions[i]
      const btn = document.createElement("button")
      btn.className = "suggestion-item"
      btn.setAttribute("role", "option")
      btn.setAttribute("aria-selected", "false")
      btn.setAttribute("type", "button")
      btn.setAttribute("data-index", String(i))

      const avatarHtml = s.avatarUrl !== undefined
        ? `<img src="${s.avatarUrl}" alt="${s.displayName || ""}"/>`
        : initials(s.displayName || "?")
      const subtitleHtml = s.subtitle !== undefined
        ? `<span class="suggestion-subtitle">${s.subtitle}</span>`
        : ""

      btn.innerHTML = `
        <span class="suggestion-avatar" aria-hidden="true">${avatarHtml}</span>
        <span class="suggestion-name">${s.displayName || s.id}</span>
        ${subtitleHtml}
      `
      this._popup.appendChild(btn)
    }

    this._popup.hidden = false
    this._positionPopup()
    announce("Suggestions available. Use arrow key to navigate.", "polite")
    return
  }

  _positionPopup() {
    if (this._positionDispose !== null) {
      this._positionDispose()
      this._positionDispose = null
    }
    const wrapper = this.$(".mention-wrapper")
    if (wrapper !== null && this._popup !== null) {
      this._positionDispose = autoPosition(this._popup, wrapper, { placement: "bottom-start", offset: 4 })
      this.onTeardown(() => {
        if (this._positionDispose !== null) {
          this._positionDispose()
          this._positionDispose = null
        }
      })
    }
    return
  }

  _closePopup() {
    if (this._popup !== null) {
      this._popup.hidden = true
      this._popup.innerHTML = ""
    }
    if (this._positionDispose !== null) {
      this._positionDispose()
      this._positionDispose = null
    }
    this._activeTrigger = null
    this._activeQuery = ""
    this._suggestions = []
    this._selectedSuggestionIndex = -1
    return
  }

  _selectSuggestion(index) {
    const suggestion = this._suggestions[index]
    if (suggestion === undefined) {
      return
    }

    this.emit("mj-mention-select", { trigger: this._activeTrigger, suggestion: suggestion })

    // Remove the trigger+query text and insert the token
    const sel = window.getSelection()
    if (sel !== null && sel.rangeCount > 0) {
      const range = sel.getRangeAt(0)
      const textNode = range.startContainer
      if (textNode.nodeType === Node.TEXT_NODE) {
        const offset = range.startOffset
        const text = textNode.textContent
        const triggerPos = text.lastIndexOf(this._activeTrigger + this._activeQuery, offset)
        if (triggerPos >= 0) {
          textNode.deleteData(triggerPos, this._activeQuery.length + 1)
          const token = this._createTokenEl(this._activeTrigger, suggestion)
          const space = document.createTextNode(" ")
          const newRange = document.createRange()
          newRange.setStart(textNode, triggerPos)
          newRange.collapse(true)
          newRange.insertNode(space)
          newRange.insertNode(token)

          // Move cursor after space
          const afterRange = document.createRange()
          afterRange.setStartAfter(space)
          afterRange.collapse(true)
          sel.removeAllRanges()
          sel.addRange(afterRange)
        }
      }
    }

    const mentionToken = {
      trigger: this._activeTrigger,
      id: suggestion.id,
      displayName: suggestion.displayName,
      type: suggestion.type || "user"
    }
    this._mentions.push(mentionToken)
    this._closePopup()
    this._syncFormValue()
    this.emit("mj-input", { value: this.value, mentions: this._mentions })
    return
  }

  _createTokenEl(trigger, suggestion) {
    const span = document.createElement("span")
    span.className = "mention-token"
    span.setAttribute("part", "token")
    span.setAttribute("role", "img")
    span.setAttribute("aria-label", `${trigger}${suggestion.displayName}`)
    span.setAttribute("contenteditable", "false")
    span.setAttribute("data-mention-id", suggestion.id)
    span.setAttribute("data-trigger", trigger)
    span.textContent = `${trigger}${suggestion.displayName}`
    return span
  }

  _onKeydown(event) {
    const popupVisible = this._popup !== null && this._popup.hidden === false
    const multiline = this.getAttribute("multiline") !== "false"

    if (popupVisible === true) {
      if (event.key === "ArrowDown") {
        event.preventDefault()
        this._moveSuggestion(1)
      } else if (event.key === "ArrowUp") {
        event.preventDefault()
        this._moveSuggestion(-1)
      } else if (event.key === "Enter") {
        if (this._selectedSuggestionIndex >= 0) {
          event.preventDefault()
          this._selectSuggestion(this._selectedSuggestionIndex)
        }
      } else if (event.key === "Escape") {
        event.preventDefault()
        const trigger = this._activeTrigger
        this._closePopup()
        this.emit("mj-mention-cancel", { trigger: trigger })
      } else if (event.key === "Tab") {
        this._closePopup()
      }
      return
    }

    if (event.key === "Enter") {
      if (multiline === false || event.shiftKey === false) {
        const proceed = multiline === false || (multiline === true && !event.shiftKey)
        if (proceed === true) {
          event.preventDefault()
          const notCanceled = this.emit("mj-submit", { value: this.value, mentions: this._mentions }, { cancelable: true })
          if (notCanceled === false) {
            return
          }
        }
      }
    }

    if (event.key === "Backspace") {
      const sel = window.getSelection()
      if (sel !== null && sel.rangeCount > 0) {
        const range = sel.getRangeAt(0)
        const node = range.startContainer
        const prev = node.previousSibling
        if (prev !== null && prev.nodeType === Node.ELEMENT_NODE &&
            prev.classList.contains("mention-token")) {
          event.preventDefault()
          const mentionId = prev.getAttribute("data-mention-id")
          prev.remove()
          this._mentions = this._mentions.filter((m) => m.id !== mentionId)
          this._syncFormValue()
          this.emit("mj-input", { value: this.value, mentions: this._mentions })
        }
      }
    }

    return
  }

  _moveSuggestion(delta) {
    const items = this._popup.querySelectorAll(".suggestion-item")
    const count = items.length
    if (count === 0) {
      return
    }

    // Reset previous
    if (this._selectedSuggestionIndex >= 0 && items[this._selectedSuggestionIndex] !== undefined) {
      items[this._selectedSuggestionIndex].setAttribute("aria-selected", "false")
    }

    this._selectedSuggestionIndex = this._selectedSuggestionIndex + delta
    if (this._selectedSuggestionIndex < 0) {
      this._selectedSuggestionIndex = count - 1
    }
    if (this._selectedSuggestionIndex >= count) {
      this._selectedSuggestionIndex = 0
    }

    const selected = items[this._selectedSuggestionIndex]
    if (selected !== undefined) {
      selected.setAttribute("aria-selected", "true")
      selected.scrollIntoView({ block: "nearest" })
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
    const prevValue = this._lastValue || ""
    const currentValue = this.value
    if (currentValue !== prevValue) {
      this._lastValue = currentValue
      this.emit("mj-change", { value: currentValue, mentions: this._mentions })
    }
    // Close popup on blur with small delay to allow click
    window.setTimeout(() => {
      if (this._popup !== null && this._popup.hidden === false) {
        const trigger = this._activeTrigger
        this._closePopup()
        this.emit("mj-mention-cancel", { trigger: trigger })
      }
    }, 150)
    return
  }

  _updateCounter() {
    if (this._counter === null) {
      return
    }
    const maxLength = parseInt(this.getAttribute("max-length") || "0", 10)
    if (maxLength <= 0) {
      return
    }
    const text = this._editable !== null ? (this._editable.textContent || "") : ""
    const len = text.length
    this._counter.textContent = `${len} / ${maxLength}`
    this._counter.setAttribute("data-over-limit", len > maxLength ? "true" : "false")
    return
  }

  _syncFormValue() {
    if (this._internals !== null) {
      this._internals.setFormValue(this.value)
    }
    return
  }

  get value() {
    if (this._editable === null) {
      return ""
    }
    return this._editable.textContent || ""
  }

  set value(text) {
    if (this._editable !== null) {
      this._editable.textContent = text || ""
      this._syncFormValue()
    }
    return
  }

  get mentions() {
    return this._mentions
  }

  get mentionSource() {
    return this._mentionSource
  }

  set mentionSource(source) {
    this._mentionSource = source
    return
  }

  focus() {
    if (this._editable !== null) {
      this._editable.focus()
    }
    return
  }
}
