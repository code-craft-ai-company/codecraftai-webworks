/*
 * mjchatcomposer.js
 *
 * <mj-chat-composer> -- message-entry bar composing a mention input, attach
 * button, emoji button, attachment previews, and a send button. Manages
 * send-on-Enter convention and loading state during message delivery.
 */

import { MjElement, nextId } from "../core/mjelement.js";

const STYLES = `
:host {
  display: block;
}

.composer-root {
  background: var(--mj-composer-bg, var(--mj-surface));
  border: 1px solid var(--mj-composer-border, var(--mj-border));
  border-radius: var(--mj-composer-radius, var(--mj-radius-lg));
  display: flex;
  flex-direction: column;
  gap: 0;
  overflow: hidden;
}

.reply-preview {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  padding: var(--mj-space-2) var(--mj-space-3);
  background: var(--mj-bg-muted);
  border-bottom: 1px solid var(--mj-border);
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
}

.reply-preview[hidden] { display: none; }

.reply-preview-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reply-cancel-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--mj-text-muted);
  padding: var(--mj-space-1);
  border-radius: var(--mj-radius-sm);
  line-height: 1;
  font-size: var(--mj-font-size-xs);
}

.reply-cancel-btn:hover { color: var(--mj-text); }
.reply-cancel-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}

.input-area {
  padding: var(--mj-space-2) var(--mj-space-3);
  min-height: var(--mj-composer-min-height, var(--mj-control-height-md));
  max-height: var(--mj-composer-max-height, 200px);
  overflow-y: auto;
}

.input-textarea {
  width: 100%;
  border: none;
  background: transparent;
  resize: none;
  font: inherit;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
  outline: none;
  min-height: var(--mj-control-height-sm);
  max-height: var(--mj-composer-max-height, 200px);
  overflow: hidden;
  padding: 0;
}

.input-textarea::placeholder { color: var(--mj-text-muted); }

:host([disabled]) .input-textarea,
:host([loading]) .input-textarea {
  pointer-events: none;
  opacity: 0.55;
}

.attachment-bar {
  display: flex;
  gap: var(--mj-space-2);
  padding: var(--mj-space-2) var(--mj-space-3) 0;
  flex-wrap: wrap;
  list-style: none;
  margin: 0;
}

.attachment-bar[hidden] { display: none; }

.attachment-item {
  display: flex;
  align-items: center;
  gap: var(--mj-space-1);
  padding: var(--mj-space-1) var(--mj-space-2);
  background: var(--mj-bg-muted);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-sm);
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text);
  max-width: var(--mj-composer-attachment-size, 56px);
}

.attachment-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 80px;
}

.attachment-remove {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--mj-text-muted);
  padding: 0;
  line-height: 1;
  font-size: 0.7em;
}

.attachment-remove:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  border-radius: 2px;
}

.toolbar-row {
  display: flex;
  align-items: center;
  gap: var(--mj-composer-toolbar-gap, var(--mj-space-1));
  padding: var(--mj-space-2) var(--mj-space-3);
  border-top: 1px solid var(--mj-border);
}

.toolbar-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--mj-control-height-sm);
  height: var(--mj-control-height-sm);
  background: transparent;
  border: none;
  border-radius: var(--mj-radius-sm);
  cursor: pointer;
  color: var(--mj-text-muted);
  font-size: var(--mj-font-size-md);
  line-height: 1;
  padding: 0;
}

.toolbar-btn:hover { background: var(--mj-bg-muted); color: var(--mj-text); }
.toolbar-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

:host([allow-attachments="false"]) .attach-btn { display: none; }
:host([allow-emoji="false"]) .emoji-btn { display: none; }

.spacer { flex: 1; }

.send-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: var(--mj-space-1) var(--mj-space-3);
  background: var(--mj-accent);
  color: var(--mj-text-on-accent);
  border: none;
  border-radius: var(--mj-radius-md);
  font: inherit;
  font-size: var(--mj-font-size-sm);
  font-weight: var(--mj-font-weight-medium);
  cursor: pointer;
  min-width: var(--mj-target-min);
  transition: background var(--mj-motion-fast) var(--mj-motion-ease);
}

.send-btn:hover { background: var(--mj-accent-hover); }
.send-btn[aria-disabled="true"] { opacity: 0.45; cursor: not-allowed; }
.send-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.spinner {
  display: none;
  width: 1em; height: 1em;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: var(--mj-radius-circle);
  animation: mj-spin var(--mj-motion-slow) linear infinite;
}

:host([loading]) .spinner { display: inline-block; }
:host([loading]) .send-label { display: none; }

@keyframes mj-spin { to { transform: rotate(360deg); } }

.counter {
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
  padding: 0 var(--mj-space-3) var(--mj-space-1);
  text-align: end;
}

.counter[data-over-limit="true"] { color: var(--mj-color-danger); }
.counter[hidden] { display: none; }
`;

function formatSize(bytes) {
  if (bytes < 1024) { return `${bytes} B` }
  if (bytes < 1024 * 1024) { return `${(bytes / 1024).toFixed(1)} KB` }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export class MjChatComposer extends MjElement {
  static tagName = "mj-chat-composer";
  static styles = STYLES;
  static watched = [
    "placeholder", "max-length", "send-key", "allow-attachments",
    "allow-emoji", "disabled", "loading", "accept"
  ];

  constructor() {
    super()
    this._attachments = []
    this._replyTo = null
    this._mentionSource = null
    this._textarea = null
    this._fileInput = null
    this._attachmentBar = null
    this._sendBtn = null
    this._replyPreview = null
    this._counter = null
  }

  render() {
    const placeholder = this.getAttribute("placeholder") || "Type a message…"
    const label = this.getAttribute("label") || "Message composer"
    const maxLength = parseInt(this.getAttribute("max-length") || "0", 10)
    const counterHtml = maxLength > 0
      ? `<div class="counter" part="counter" aria-live="polite" hidden></div>`
      : ""

    const markup = `
      <div class="composer-root" role="form" part="root" aria-label="${label}">
        <div class="reply-preview" part="reply-preview" hidden role="note"
             aria-label="Replying to message">
          <span class="reply-preview-text" part="reply-preview-text"></span>
          <button class="reply-cancel-btn" part="reply-cancel" type="button"
                  aria-label="Cancel reply">&#x2715;</button>
        </div>
        <ul class="attachment-bar" part="attachment-bar"
            aria-label="Attachments" hidden></ul>
        <div class="input-area">
          <textarea class="input-textarea" part="input"
                    placeholder="${placeholder}"
                    aria-label="${label}"
                    aria-multiline="true"
                    rows="1"></textarea>
        </div>
        ${counterHtml}
        <div class="toolbar-row" part="toolbar">
          <slot name="toolbar-start"></slot>
          <button class="toolbar-btn attach-btn" part="attach-button" type="button"
                  aria-label="Attach file" title="Attach file">&#128206;</button>
          <button class="toolbar-btn emoji-btn" part="emoji-button" type="button"
                  aria-label="Insert emoji" title="Insert emoji">&#128512;</button>
          <slot name="toolbar-end"></slot>
          <div class="spacer"></div>
          <button class="send-btn" part="send-button" type="button"
                  aria-label="Send message" aria-disabled="true">
            <span class="spinner" aria-hidden="true"></span>
            <span class="send-label">Send</span>
          </button>
        </div>
      </div>
      <input type="file" aria-hidden="true" tabindex="-1"
             style="position:absolute;opacity:0;pointer-events:none;width:1px;height:1px;"
             ${this.getAttribute("accept") !== null ? `accept="${this.getAttribute("accept")}"` : ""}>
    `
    return markup
  }

  afterRender() {
    this._textarea = this.$(".input-textarea")
    this._fileInput = this.$("input[type=file]")
    this._attachmentBar = this.$(".attachment-bar")
    this._sendBtn = this.$(".send-btn")
    this._replyPreview = this.$(".reply-preview")
    this._replyPreviewText = this.$(".reply-preview-text")
    this._counter = this.$(".counter")
    this._attachBtn = this.$(".attach-btn")
    this._emojiBtn = this.$(".emoji-btn")
    this._replyCancelBtn = this.$(".reply-cancel-btn")

    this.listen(this._textarea, "input", this._onTextInput.bind(this))
    this.listen(this._textarea, "keydown", this._onKeydown.bind(this))
    this.listen(this._sendBtn, "click", this._onSend.bind(this))
    this.listen(this._attachBtn, "click", this._onAttachClick.bind(this))
    this.listen(this._fileInput, "change", this._onFilesSelected.bind(this))
    this.listen(this._replyCancelBtn, "click", this._onReplyCancel.bind(this))

    if (this._emojiBtn !== null) {
      this.listen(this._emojiBtn, "click", () => {
        // Emoji picker integration placeholder — inserts a sample emoji
        // In production this would open an emoji picker popover
      })
    }

    return
  }

  _onTextInput() {
    const maxLength = parseInt(this.getAttribute("max-length") || "0", 10)
    const text = this._textarea.value

    if (maxLength > 0 && this._counter !== null) {
      this._counter.hidden = false
      this._counter.textContent = `${text.length} / ${maxLength}`
      this._counter.setAttribute("data-over-limit", text.length > maxLength ? "true" : "false")
    }

    // Auto-grow textarea
    this._textarea.style.height = "auto"
    this._textarea.style.height = `${this._textarea.scrollHeight}px`

    this._updateSendState()

    this.emit("mj-input", { value: this.value, mentions: this.mentions })
    return
  }

  _onKeydown(event) {
    const sendKey = this.getAttribute("send-key") || "enter"

    if (sendKey === "enter" && event.key === "Enter" && !event.shiftKey) {
      event.preventDefault()
      this._onSend()
    } else if (sendKey === "ctrl+enter" && event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
      event.preventDefault()
      this._onSend()
    } else if (event.key === "Escape" && this._replyTo !== null) {
      this._onReplyCancel()
    }
    return
  }

  _onSend() {
    if (this.hasAttribute("loading") || this.hasAttribute("disabled")) {
      return
    }

    const value = this.value
    const hasContent = value.trim().length > 0 || this._attachments.length > 0

    if (hasContent === false) {
      return
    }

    const replyToId = this._replyTo !== null ? this._replyTo.messageId : null

    const proceed = this.emit("mj-send", {
      value: value,
      mentions: this.mentions,
      attachments: this._attachments,
      replyTo: replyToId
    }, { cancelable: true })

    if (proceed !== false) {
      this.clear()
    }
    return
  }

  _onAttachClick() {
    if (this.hasAttribute("disabled")) {
      return
    }
    this._fileInput.click()
    return
  }

  _onFilesSelected(event) {
    const rawFiles = Array.from(event.target.files || [])
    const maxSize = parseInt(this.getAttribute("max-attachment-size") || "0", 10)
    const newEntries = []

    for (let i = 0; i < rawFiles.length; i = i + 1) {
      const file = rawFiles[i]
      if (maxSize > 0 && file.size > maxSize) {
        continue
      }
      newEntries.push({ id: `mj-att-${Date.now()}-${i}`, file: file, status: "queued", progress: 0 })
    }

    this._attachments = this._attachments.concat(newEntries)
    this._fileInput.value = ""
    this._renderAttachments()
    this._updateSendState()

    if (newEntries.length > 0) {
      this.emit("mj-attachment-add", { files: newEntries })
    }
    return
  }

  _renderAttachments() {
    if (this._attachmentBar === null) {
      return
    }

    if (this._attachments.length === 0) {
      this._attachmentBar.hidden = true
      this._attachmentBar.innerHTML = ""
      return
    }

    this._attachmentBar.hidden = false
    this._attachmentBar.innerHTML = ""

    for (let i = 0; i < this._attachments.length; i = i + 1) {
      const att = this._attachments[i]
      const li = document.createElement("li")
      li.className = "attachment-item"
      li.setAttribute("part", "attachment-item")
      li.innerHTML = `
        <span class="attachment-name" title="${att.file.name}">${att.file.name}</span>
        <button class="attachment-remove" part="attachment-remove" type="button"
                aria-label="Remove attachment ${att.file.name}"
                data-att-id="${att.id}">&#x2715;</button>
      `
      const removeBtn = li.querySelector(".attachment-remove")
      if (removeBtn !== null) {
        this.listen(removeBtn, "click", this._onAttachmentRemove.bind(this, att.id, att.file.name))
      }
      this._attachmentBar.appendChild(li)
    }
    return
  }

  _onAttachmentRemove(attId, filename) {
    this._attachments = this._attachments.filter((a) => a.id !== attId)
    this._renderAttachments()
    this._updateSendState()
    this.emit("mj-attachment-remove", { fileId: attId })
    return
  }

  _onReplyCancel() {
    this._replyTo = null
    if (this._replyPreview !== null) {
      this._replyPreview.hidden = true
    }
    this.emit("mj-reply-cancel", {})
    return
  }

  _updateSendState() {
    if (this._sendBtn === null) {
      return
    }
    const hasContent = this.value.trim().length > 0 || this._attachments.length > 0
    this._sendBtn.setAttribute("aria-disabled", hasContent ? "false" : "true")
    return
  }

  get value() {
    return this._textarea !== null ? this._textarea.value : ""
  }

  set value(text) {
    if (this._textarea !== null) {
      this._textarea.value = text || ""
      this._updateSendState()
    }
    return
  }

  get mentions() {
    // When using raw textarea there are no structured tokens
    // This would integrate with MjMentionInput in production
    return []
  }

  get attachments() {
    return this._attachments
  }

  get replyTo() {
    return this._replyTo
  }

  set replyTo(value) {
    this._replyTo = value
    if (this._replyPreview !== null) {
      if (value !== null && value !== undefined) {
        this._replyPreview.hidden = false
        if (this._replyPreviewText !== null) {
          const preview = value.preview || ""
          this._replyPreviewText.textContent = `Replying to: ${preview}`
        }
        this._replyPreview.setAttribute("aria-label", `Replying to: ${value.preview || "message"}`)
      } else {
        this._replyPreview.hidden = true
      }
    }
    return
  }

  get mentionSource() {
    return this._mentionSource
  }

  set mentionSource(source) {
    this._mentionSource = source
    return
  }

  clear() {
    if (this._textarea !== null) {
      this._textarea.value = ""
      this._textarea.style.height = "auto"
    }
    this._attachments = []
    this._renderAttachments()
    this._replyTo = null
    if (this._replyPreview !== null) {
      this._replyPreview.hidden = true
    }
    this._updateSendState()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "loading" && this._sendBtn !== null) {
      const loading = newValue !== null
      this._sendBtn.setAttribute("aria-label", loading ? "Sending…" : "Send message")
    }
    return
  }
}
