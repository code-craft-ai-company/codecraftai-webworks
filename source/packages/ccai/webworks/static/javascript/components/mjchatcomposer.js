/*
 * mjchatcomposer.js
 *
 * <mj-chat-composer> -- message-entry bar composing a mention input, attach
 * button, emoji button, attachment previews, and a send button. Manages
 * send-on-Enter convention and loading state during message delivery.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";

/* Emoji offered by the built-in picker (shown unless `mj-emoji-request` is canceled). */
const EMOJI_CHOICES = [
  "\u{1F600}", "\u{1F602}", "\u{1F60A}", "\u{1F60D}", "\u{1F914}", "\u{1F62E}",
  "\u{1F622}", "\u{1F44D}", "\u{1F64F}", "\u{1F389}", "\u{2764}\u{FE0F}", "\u{1F525}"
];

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

:host([disabled]) .input-textarea {
  opacity: 0.55;
}
/* Sending: the text is read-only, not inactive, so it stays readable (muted, 4.5:1) rather than faded. */
:host([loading]) .input-textarea {
  color: var(--mj-text-muted);
}

:host([disabled]) .composer-root {
  cursor: not-allowed;
}

.composer-root[data-drag-over="true"] {
  border-color: var(--mj-accent);
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
  max-width: var(--mj-composer-attachment-max-width, 240px);
  min-width: 0;
}

.attachment-item.is-error {
  border-color: var(--mj-color-danger);
  background: var(--mj-color-danger-surface);
}

.attachment-thumb {
  width: var(--mj-composer-attachment-size, 56px);
  height: var(--mj-composer-attachment-size, 56px);
  object-fit: cover;
  border-radius: var(--mj-radius-sm);
  flex-shrink: 0;
}

.attachment-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

.attachment-reason {
  color: var(--mj-color-danger);
  white-space: nowrap;
}

.attachment-progress {
  width: 40px;
  height: 4px;
  background: var(--mj-border);
  border-radius: var(--mj-radius-pill);
  overflow: hidden;
  flex-shrink: 0;
}

.attachment-progress-bar {
  height: 100%;
  background: var(--mj-accent);
  transition: width var(--mj-motion-fast) linear;
}

.emoji-panel {
  display: flex;
  flex-wrap: wrap;
  gap: var(--mj-space-1);
  padding: var(--mj-space-2) var(--mj-space-3);
  border-top: 1px solid var(--mj-border);
}

.emoji-panel[hidden] { display: none; }

.emoji-option {
  background: transparent;
  border: none;
  border-radius: var(--mj-radius-sm);
  cursor: pointer;
  font-size: var(--mj-font-size-md);
  line-height: 1;
  padding: var(--mj-space-1);
}

.emoji-option:hover { background: var(--mj-bg-muted); }
.emoji-option:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}

.toolbar-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.file-input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
  width: 1px;
  height: 1px;
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

/* True when `file` satisfies an `accept` list of MIME types, MIME groups and extensions. */
function fileMatchesAccept(file, accept) {
  const patterns = accept.split(",").map((part) => part.trim()).filter((part) => part.length > 0)
  let matches = patterns.length === 0

  for (let i = 0; i < patterns.length && matches === false; i = i + 1) {
    const pattern = patterns[i].toLowerCase()
    if (pattern === "*/*") {
      matches = true
    } else if (pattern.endsWith("/*") === true) {
      matches = file.type.toLowerCase().startsWith(pattern.slice(0, -1))
    } else if (pattern.startsWith(".") === true) {
      matches = file.name.toLowerCase().endsWith(pattern)
    } else {
      matches = file.type.toLowerCase() === pattern
    }
  }
  return matches
}

export class MjChatComposer extends MjElement {
  static tagName = "mj-chat-composer";
  static styles = STYLES;
  static watched = [
    "placeholder", "max-length", "send-key", "allow-attachments",
    "allow-emoji", "disabled", "loading", "accept", "label", "max-attachment-size"
  ];

  constructor() {
    super()

    /* Everything the user entered lives in fields so a reconnect restores it. */
    this._draft = ""
    this._attachments = []
    this._rejected = []
    this._replyTo = null
    this._emojiOpen = false
    this._mentionSource = null

    this._emojiPanelId = nextId("mj-cc-emoji")

    this._root = null
    this._textarea = null
    this._fileInput = null
    this._attachmentBar = null
    this._sendBtn = null
    this._replyPreview = null
    this._replyPreviewText = null
    this._counter = null
    this._attachBtn = null
    this._emojiBtn = null
    this._emojiPanel = null
  }

  render() {
    const markup = html`
      <div class="composer-root" part="root">
        <div class="reply-preview" part="reply-preview" hidden role="note"
             aria-label="${t("mj.chatComposer.replyPreviewLabel")}">
          <span class="reply-preview-text" part="reply-preview-text"></span>
          <button class="reply-cancel-btn" part="reply-cancel" type="button"
                  aria-label="${t("mj.chatComposer.cancelReply")}">&#x2715;</button>
        </div>
        <ul class="attachment-bar" part="attachment-bar"
            aria-label="${t("mj.chatComposer.attachmentsLabel")}" hidden></ul>
        <div class="input-area">
          <textarea class="input-textarea" part="input" rows="1"></textarea>
        </div>
        <div class="counter" part="counter" aria-live="polite" hidden></div>
        <div class="emoji-panel" role="group" aria-label="${t("mj.chatComposer.emojiPanelLabel")}" id="${this._emojiPanelId}" hidden>
          ${EMOJI_CHOICES.map((emoji) => html`
            <button class="emoji-option" type="button" data-emoji="${emoji}" aria-label="${t("mj.chatComposer.insertEmojiOption", { emoji: emoji })}">${emoji}</button>
          `)}
        </div>
        <div class="toolbar-row" part="toolbar">
          <slot name="toolbar-start"></slot>
          <button class="toolbar-btn attach-btn" part="attach-button" type="button"
                  aria-label="${t("mj.chatComposer.attachFile")}" title="${t("mj.chatComposer.attachFile")}">&#128206;</button>
          <button class="toolbar-btn emoji-btn" part="emoji-button" type="button"
                  aria-label="${t("mj.chatComposer.insertEmoji")}" title="${t("mj.chatComposer.insertEmoji")}"
                  aria-expanded="false" aria-controls="${this._emojiPanelId}">&#128512;</button>
          <slot name="toolbar-end"></slot>
          <div class="spacer"></div>
          <button class="send-btn" part="send-button" type="button"
                  aria-label="${t("mj.chatComposer.sendMessage")}" aria-disabled="true">
            <span class="spinner" aria-hidden="true"></span>
            <span class="send-label">${t("mj.chatComposer.send")}</span>
          </button>
        </div>
      </div>
      <input class="file-input" type="file" multiple aria-hidden="true" tabindex="-1">
    `
    return markup
  }

  afterRender() {
    this._root = this.$(".composer-root")
    this._textarea = this.$(".input-textarea")
    this._fileInput = this.$("input[type=file]")
    this._attachmentBar = this.$(".attachment-bar")
    this._sendBtn = this.$(".send-btn")
    this._replyPreview = this.$(".reply-preview")
    this._replyPreviewText = this.$(".reply-preview-text")
    this._counter = this.$(".counter")
    this._attachBtn = this.$(".attach-btn")
    this._emojiBtn = this.$(".emoji-btn")
    this._emojiPanel = this.$(".emoji-panel")

    this.listen(this._textarea, "input", this._onTextInput.bind(this))
    this.listen(this._textarea, "keydown", this._onKeydown.bind(this))
    this.listen(this._textarea, "paste", this._onPaste.bind(this))
    this.listen(this._sendBtn, "click", this._onSend.bind(this))
    this.listen(this._attachBtn, "click", this._onAttachClick.bind(this))
    this.listen(this._fileInput, "change", this._onFilesSelected.bind(this))
    this.listen(this.$(".reply-cancel-btn"), "click", this._onReplyCancel.bind(this))
    this.listen(this._emojiBtn, "click", this._onEmojiClick.bind(this))
    this.listen(this._emojiPanel, "click", this._onEmojiPanelClick.bind(this))
    this.listen(this._emojiPanel, "keydown", this._onEmojiPanelKeydown.bind(this))
    this.listen(this._attachmentBar, "click", this._onAttachmentBarClick.bind(this))
    this.listen(this._attachmentBar, "keydown", this._onAttachmentBarKeydown.bind(this))
    this.listen(this._root, "dragover", this._onDragOver.bind(this))
    this.listen(this._root, "dragleave", this._onDragLeave.bind(this))
    this.listen(this._root, "drop", this._onDrop.bind(this))

    this.onTeardown(() => {
      this._releasePreviews()
    })

    /* Rebuild the view from the fields: draft, attachments, reply target. */
    this._textarea.value = this._draft
    this._syncAttributes()
    this._renderAttachments()
    this._syncReplyPreview()
    this._syncEmojiPanel()
    this._syncText()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._textarea === undefined || this._textarea === null) {
      return
    }
    this._syncAttributes()
    this._syncText()
    return
  }

  /* ----- state helpers ----- */

  _maxLength() {
    const parsed = parseInt(this.getAttribute("max-length") || "0", 10)
    const maxLength = Number.isFinite(parsed) === true && parsed > 0 ? parsed : 0
    return maxLength
  }

  _isBusy() {
    const busy = this.hasAttribute("disabled") === true || this.hasAttribute("loading") === true
    return busy
  }

  _attachmentsAllowed() {
    const allowed = this.getAttribute("allow-attachments") !== "false"
    return allowed
  }

  /* Apply every attribute-derived piece of state to the shadow DOM. */
  _syncAttributes() {
    const placeholder = this.getAttribute("placeholder") || t("mj.chatComposer.placeholder")
    const label = this.getAttribute("label") || t("mj.chatComposer.label")
    const accept = this.getAttribute("accept")
    const maxLength = this._maxLength()
    const disabled = this.hasAttribute("disabled")
    const loading = this.hasAttribute("loading")
    const busy = disabled === true || loading === true

    /*
     * role="form" is a landmark and must be named. Only a label the page
     * gives makes the composer one, so several composers with the default
     * name do not repeat the same landmark; without it the root is a plain
     * container. The textarea always carries the name.
     */
    if (this.hasAttribute("label") === true) {
      this._root.setAttribute("role", "form")
      this._root.setAttribute("aria-label", label)
    } else {
      this._root.removeAttribute("role")
      this._root.removeAttribute("aria-label")
    }
    this._root.setAttribute("aria-busy", loading === true ? "true" : "false")
    this._textarea.setAttribute("placeholder", placeholder)
    this._textarea.setAttribute("aria-label", label)

    if (accept !== null && accept.length > 0) {
      this._fileInput.setAttribute("accept", accept)
    } else {
      this._fileInput.removeAttribute("accept")
    }

    /* The native limit stops typing and pasting beyond max-length. */
    if (maxLength > 0) {
      this._textarea.setAttribute("maxlength", String(maxLength))
    } else {
      this._textarea.removeAttribute("maxlength")
    }

    /*
     * disabled takes the textarea out of the tab order; loading keeps focus
     * where it is but makes the text read-only until the send completes.
     */
    this._textarea.disabled = disabled
    this._textarea.readOnly = loading
    this._attachBtn.disabled = busy
    this._emojiBtn.disabled = busy
    this._fileInput.disabled = busy
    this._sendBtn.setAttribute("aria-label", loading === true ? t("mj.chatComposer.sending") : t("mj.chatComposer.sendMessage"))

    const chipButtons = this._attachmentBar.querySelectorAll(".attachment-remove")
    for (let i = 0; i < chipButtons.length; i = i + 1) {
      chipButtons[i].disabled = busy
    }

    if (busy === true && this._emojiOpen === true) {
      this._emojiOpen = false
      this._syncEmojiPanel()
    }
    return
  }

  /* Counter, textarea height and send-button state, from the current text. */
  _syncText() {
    if (this._textarea === null) {
      return
    }

    const maxLength = this._maxLength()
    const length = this._textarea.value.length

    this._counter.hidden = maxLength <= 0
    if (maxLength > 0) {
      this._counter.textContent = `${length} / ${maxLength}`
      this._counter.setAttribute("data-over-limit", length > maxLength ? "true" : "false")
    }

    /* Auto-grow the textarea. */
    this._textarea.style.height = "auto"
    this._textarea.style.height = `${this._textarea.scrollHeight}px`

    this._updateSendState()
    return
  }

  _canSend() {
    const maxLength = this._maxLength()
    const value = this.value
    const hasContent = value.trim().length > 0 || this._attachments.length > 0
    const overLimit = maxLength > 0 && value.length > maxLength
    const sendable = hasContent === true && overLimit === false && this._isBusy() === false
    return sendable
  }

  _updateSendState() {
    if (this._sendBtn === null) {
      return
    }
    this._sendBtn.setAttribute("aria-disabled", this._canSend() === true ? "false" : "true")
    return
  }

  /* ----- text ----- */

  _onTextInput() {
    this._draft = this._textarea.value
    this._syncText()
    this.emit("mj-input", { value: this.value, mentions: this.mentions })
    return
  }

  _onKeydown(event) {
    const sendKey = this.getAttribute("send-key") || "enter"
    /* The Enter that confirms an IME composition must not send. */
    const composing = event.isComposing === true || event.keyCode === 229
    const modifier = event.ctrlKey === true || event.metaKey === true

    if (event.key === "Enter" && composing === false) {
      if (sendKey === "enter" && event.shiftKey === false) {
        event.preventDefault()
        this._onSend()
      } else if (sendKey === "ctrl+enter" && modifier === true) {
        event.preventDefault()
        this._onSend()
      }
    } else if (event.key === "Escape") {
      if (this._emojiOpen === true) {
        event.preventDefault()
        this._emojiOpen = false
        this._syncEmojiPanel()
      } else if (this._replyTo !== null) {
        this._onReplyCancel()
      }
    }
    return
  }

  _onSend() {
    if (this._isBusy() === true) {
      return
    }

    const value = this.value
    const maxLength = this._maxLength()
    const hasContent = value.trim().length > 0 || this._attachments.length > 0

    if (hasContent === false) {
      return
    }
    if (maxLength > 0 && value.length > maxLength) {
      announce(t("mj.chatComposer.tooLong", { count: maxLength }), "assertive")
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

  /* ----- emoji ----- */

  /*
   * The emoji button first asks the host: `mj-emoji-request` is cancelable,
   * and a host that cancels it shows its own picker and calls `insertText()`.
   * Otherwise the built-in panel of common emoji is toggled.
   */
  _onEmojiClick() {
    if (this._isBusy() === true) {
      return
    }
    if (this._emojiOpen === true) {
      this._emojiOpen = false
      this._syncEmojiPanel()
      return
    }

    const proceed = this.emit("mj-emoji-request", {}, { cancelable: true })
    if (proceed !== false) {
      this._emojiOpen = true
      this._syncEmojiPanel()
      this._emojiPanel.querySelector(".emoji-option").focus()
    }
    return
  }

  _syncEmojiPanel() {
    this._emojiPanel.hidden = this._emojiOpen === false
    this._emojiBtn.setAttribute("aria-expanded", this._emojiOpen === true ? "true" : "false")
    return
  }

  _onEmojiPanelClick(event) {
    const option = event.target.closest(".emoji-option")
    if (option === null) {
      return
    }
    this.insertText(option.getAttribute("data-emoji"))
    this._emojiOpen = false
    this._syncEmojiPanel()
    this._textarea.focus()
    return
  }

  _onEmojiPanelKeydown(event) {
    const options = Array.from(this._emojiPanel.querySelectorAll(".emoji-option"))
    const current = options.indexOf(this.shadowRoot.activeElement)

    if (event.key === "Escape") {
      event.preventDefault()
      event.stopPropagation()
      this._emojiOpen = false
      this._syncEmojiPanel()
      this._emojiBtn.focus()
    } else if (event.key === "ArrowRight" || event.key === "ArrowLeft") {
      event.preventDefault()
      const step = event.key === "ArrowRight" ? 1 : -1
      const next = (current + step + options.length) % options.length
      options[next].focus()
    }
    return
  }

  /* ----- attachments ----- */

  _onAttachClick() {
    if (this._isBusy() === true) {
      return
    }
    this._fileInput.click()
    return
  }

  _onFilesSelected(event) {
    const rawFiles = Array.from(event.target.files || [])
    this._fileInput.value = ""
    this._addFiles(rawFiles)
    return
  }

  /* Files pasted into the text (a screenshot, a copied file) become attachments. */
  _onPaste(event) {
    const files = event.clipboardData !== null && event.clipboardData !== undefined
      ? Array.from(event.clipboardData.files || [])
      : []
    if (files.length > 0 && this._attachmentsAllowed() === true && this._isBusy() === false) {
      event.preventDefault()
      this._addFiles(files)
    }
    return
  }

  _dragHasFiles(event) {
    const dt = event.dataTransfer
    const hasFiles = dt !== null && dt !== undefined && dt.types !== undefined &&
      Array.from(dt.types).indexOf("Files") >= 0
    return hasFiles
  }

  _onDragOver(event) {
    if (this._dragHasFiles(event) === true && this._attachmentsAllowed() === true && this._isBusy() === false) {
      event.preventDefault()
      this._root.setAttribute("data-drag-over", "true")
    }
    return
  }

  _onDragLeave() {
    this._root.removeAttribute("data-drag-over")
    return
  }

  _onDrop(event) {
    this._root.removeAttribute("data-drag-over")
    if (this._dragHasFiles(event) === true && this._attachmentsAllowed() === true && this._isBusy() === false) {
      event.preventDefault()
      this._addFiles(Array.from(event.dataTransfer.files))
    }
    return
  }

  /*
   * Queue files as attachments. A file that fails the `accept` list or
   * `max-attachment-size` is not dropped silently: it is reported with
   * `mj-attachment-reject` and shown as a dismissible error chip.
   */
  _addFiles(rawFiles) {
    const maxSize = parseInt(this.getAttribute("max-attachment-size") || "0", 10)
    const accept = this.getAttribute("accept") || ""
    const newEntries = []
    const rejected = []

    for (let i = 0; i < rawFiles.length; i = i + 1) {
      const file = rawFiles[i]
      let reason = null

      if (fileMatchesAccept(file, accept) === false) {
        reason = t("mj.chatComposer.typeNotAllowed")
      } else if (maxSize > 0 && file.size > maxSize) {
        reason = t("mj.chatComposer.tooLarge", { size: formatSize(maxSize) })
      }

      if (reason !== null) {
        rejected.push({ id: nextId("mj-att-rejected"), file: file, reason: reason })
      } else {
        newEntries.push({
          id: nextId("mj-att"), file: file, status: "queued", progress: 0, error: undefined, previewUrl: null
        })
      }
    }

    this._attachments = this._attachments.concat(newEntries)
    this._rejected = this._rejected.concat(rejected)
    this._renderAttachments()
    this._updateSendState()

    if (newEntries.length > 0) {
      this.emit("mj-attachment-add", { files: newEntries })
    }
    if (rejected.length > 0) {
      this.emit("mj-attachment-reject", { rejectedFiles: rejected })
      announce(t("mj.chatComposer.notAttached", { count: rejected.length }), "assertive")
    }
    return
  }

  /* Object URLs for image thumbnails are released when no longer shown. */
  _releasePreview(entry) {
    if (entry.previewUrl !== null && entry.previewUrl !== undefined) {
      URL.revokeObjectURL(entry.previewUrl)
      entry.previewUrl = null
    }
    return
  }

  _releasePreviews() {
    for (let i = 0; i < this._attachments.length; i = i + 1) {
      this._releasePreview(this._attachments[i])
    }
    return
  }

  _renderAttachments() {
    if (this._attachmentBar === null) {
      return
    }

    this._attachmentBar.textContent = ""
    this._attachmentBar.hidden = this._attachments.length === 0 && this._rejected.length === 0
    const busy = this._isBusy()

    for (let i = 0; i < this._attachments.length; i = i + 1) {
      const att = this._attachments[i]
      const li = document.createElement("li")
      li.className = "attachment-item"
      li.setAttribute("part", "attachment-item")
      li.setAttribute("data-att-id", att.id)

      if (att.file.type.startsWith("image/") === true) {
        if (att.previewUrl === null || att.previewUrl === undefined) {
          att.previewUrl = URL.createObjectURL(att.file)
        }
        const thumb = document.createElement("img")
        thumb.className = "attachment-thumb"
        thumb.alt = ""
        thumb.src = att.previewUrl
        li.appendChild(thumb)
      }

      const nameEl = document.createElement("span")
      nameEl.className = "attachment-name"
      nameEl.title = att.file.name
      nameEl.textContent = att.file.name
      li.appendChild(nameEl)

      const statusEl = document.createElement("span")
      statusEl.className = "attachment-status"
      li.appendChild(statusEl)

      const removeBtn = document.createElement("button")
      removeBtn.className = "attachment-remove"
      removeBtn.type = "button"
      removeBtn.setAttribute("part", "attachment-remove")
      removeBtn.setAttribute("aria-label", t("mj.chatComposer.removeAttachment", { name: att.file.name }))
      removeBtn.textContent = "✕"
      removeBtn.disabled = busy
      li.appendChild(removeBtn)

      this._attachmentBar.appendChild(li)
      this._updateAttachmentChip(att)
    }

    for (let i = 0; i < this._rejected.length; i = i + 1) {
      const rejection = this._rejected[i]
      const li = document.createElement("li")
      li.className = "attachment-item is-error"
      li.setAttribute("part", "attachment-item")
      li.setAttribute("data-rejected-id", rejection.id)
      li.innerHTML = String(html`
        <span class="attachment-name" title="${rejection.file.name}">${rejection.file.name}</span>
        <span class="attachment-reason">${rejection.reason}</span>
        <button class="attachment-remove" part="attachment-remove" type="button"
                aria-label="${t("mj.chatComposer.dismissRejected", { name: rejection.file.name, reason: rejection.reason })}">&#x2715;</button>
      `)
      this._attachmentBar.appendChild(li)
    }
    return
  }

  /* Reflect one attachment's upload state (progress bar or error) on its chip. */
  _updateAttachmentChip(att) {
    const chips = this._attachmentBar.querySelectorAll("[data-att-id]")
    let chip = null
    for (let i = 0; i < chips.length; i = i + 1) {
      if (chips[i].getAttribute("data-att-id") === att.id) {
        chip = chips[i]
      }
    }
    if (chip === null) {
      return
    }

    const statusEl = chip.querySelector(".attachment-status")
    chip.classList.toggle("is-error", att.status === "error")

    if (att.status === "uploading") {
      const progress = Math.max(0, Math.min(100, Math.round(Number(att.progress) || 0)))
      let progressEl = statusEl.querySelector(".attachment-progress")
      if (progressEl === null) {
        statusEl.textContent = ""
        progressEl = document.createElement("span")
        progressEl.className = "attachment-progress"
        progressEl.setAttribute("role", "progressbar")
        progressEl.setAttribute("aria-valuemin", "0")
        progressEl.setAttribute("aria-valuemax", "100")
        progressEl.setAttribute("aria-label", t("mj.chatComposer.uploading", { name: att.file.name }))
        const barEl = document.createElement("span")
        barEl.className = "attachment-progress-bar"
        barEl.style.display = "block"
        progressEl.appendChild(barEl)
        statusEl.appendChild(progressEl)
      }
      progressEl.setAttribute("aria-valuenow", String(progress))
      progressEl.querySelector(".attachment-progress-bar").style.width = `${progress}%`
    } else if (att.status === "error") {
      statusEl.textContent = ""
      const reasonEl = document.createElement("span")
      reasonEl.className = "attachment-reason"
      reasonEl.textContent = att.error || t("mj.chatComposer.uploadError")
      statusEl.appendChild(reasonEl)
    } else {
      statusEl.textContent = ""
    }
    return
  }

  /* Remove the chip a remove button belongs to and keep focus in the bar. */
  _removeChip(button) {
    const chip = button.closest(".attachment-item")
    const buttons = Array.from(this._attachmentBar.querySelectorAll(".attachment-remove"))
    const position = buttons.indexOf(button)
    const attId = chip.getAttribute("data-att-id")

    if (attId !== null) {
      const removed = this._attachments.filter((att) => att.id === attId)
      for (let i = 0; i < removed.length; i = i + 1) {
        this._releasePreview(removed[i])
      }
      this._attachments = this._attachments.filter((att) => att.id !== attId)
    } else {
      const rejectedId = chip.getAttribute("data-rejected-id")
      this._rejected = this._rejected.filter((rejection) => rejection.id !== rejectedId)
    }

    this._renderAttachments()
    this._updateSendState()

    /* Focus the chip that took the removed one's place, else the text. */
    const remaining = this._attachmentBar.querySelectorAll(".attachment-remove")
    if (remaining.length > 0) {
      remaining[Math.min(position, remaining.length - 1)].focus()
    } else {
      this._textarea.focus()
    }

    if (attId !== null) {
      this.emit("mj-attachment-remove", { fileId: attId })
    }
    return
  }

  _onAttachmentBarClick(event) {
    const button = event.target.closest(".attachment-remove")
    if (button !== null && this._isBusy() === false) {
      this._removeChip(button)
    }
    return
  }

  _onAttachmentBarKeydown(event) {
    if (event.key !== "Delete" && event.key !== "Backspace") {
      return
    }
    const button = event.target.closest(".attachment-remove")
    if (button !== null && this._isBusy() === false) {
      event.preventDefault()
      this._removeChip(button)
    }
    return
  }

  /* ----- reply ----- */

  _syncReplyPreview() {
    if (this._replyPreview === null) {
      return
    }
    const replyTo = this._replyTo
    if (replyTo !== null) {
      const preview = replyTo.preview !== undefined && replyTo.preview !== null ? String(replyTo.preview) : ""
      this._replyPreview.hidden = false
      this._replyPreviewText.textContent = t("mj.chatComposer.replyingTo", { preview: preview })
      this._replyPreview.setAttribute("aria-label", t("mj.chatComposer.replyingTo", { preview: preview.length > 0 ? preview : t("mj.chatComposer.replyTargetFallback") }))
    } else {
      this._replyPreview.hidden = true
    }
    return
  }

  _onReplyCancel() {
    const cancelHadFocus = this.shadowRoot.activeElement !== null &&
      this._replyPreview.contains(this.shadowRoot.activeElement) === true
    this._replyTo = null
    this._syncReplyPreview()
    if (cancelHadFocus === true) {
      this._textarea.focus()
    }
    this.emit("mj-reply-cancel", {})
    return
  }

  /* ----- public API ----- */

  get value() {
    const text = this._textarea !== null ? this._textarea.value : this._draft
    return text
  }

  set value(text) {
    this._draft = text !== null && text !== undefined ? String(text) : ""
    if (this._textarea !== null) {
      this._textarea.value = this._draft
      this._syncText()
    }
    return
  }

  /*
   * Mention tokens are not produced yet: the composer edits plain text.
   * The property is kept so `mj-send` / `mj-input` payloads have a stable shape.
   */
  get mentions() {
    return []
  }

  get attachments() {
    return this._attachments
  }

  get replyTo() {
    return this._replyTo
  }

  set replyTo(value) {
    this._replyTo = value !== undefined ? value : null
    this._syncReplyPreview()
    return
  }

  get mentionSource() {
    return this._mentionSource
  }

  set mentionSource(source) {
    this._mentionSource = source
    return
  }

  /*
   * Insert text (an emoji, a canned reply) at the caret, replacing the
   * selection. Text beyond `max-length` is cut off. Emits `mj-input`.
   */
  insertText(text) {
    const insertion = text !== null && text !== undefined ? String(text) : ""
    if (insertion.length === 0) {
      return
    }

    if (this._textarea === null) {
      this._draft = this._draft + insertion
      return
    }

    const start = this._textarea.selectionStart
    const end = this._textarea.selectionEnd
    const maxLength = this._maxLength()
    let allowed = insertion
    if (maxLength > 0) {
      const room = Math.max(0, maxLength - (this._textarea.value.length - (end - start)))
      allowed = Array.from(insertion).slice(0, room).join("")
      if (allowed.length > room) {
        allowed = ""
      }
    }

    if (allowed.length > 0) {
      this._textarea.setRangeText(allowed, start, end, "end")
      this._draft = this._textarea.value
      this._syncText()
      this.emit("mj-input", { value: this.value, mentions: this.mentions })
    }
    return
  }

  /* Report an attachment's upload state: { status, progress, error }. */
  updateAttachment(attachmentId, updates) {
    let entry = null
    for (let i = 0; i < this._attachments.length; i = i + 1) {
      if (this._attachments[i].id === attachmentId) {
        entry = this._attachments[i]
      }
    }

    if (entry !== null && updates !== null && updates !== undefined) {
      if (updates.status !== undefined) {
        entry.status = updates.status
      }
      if (updates.progress !== undefined) {
        entry.progress = updates.progress
      }
      if (updates.error !== undefined) {
        entry.error = updates.error
      }
      if (this._attachmentBar !== null) {
        this._updateAttachmentChip(entry)
      }
    }
    return
  }

  clear() {
    this._draft = ""
    this._releasePreviews()
    this._attachments = []
    this._rejected = []
    this._replyTo = null
    this._emojiOpen = false

    if (this._textarea !== null) {
      this._textarea.value = ""
      this._renderAttachments()
      this._syncReplyPreview()
      this._syncEmojiPanel()
      this._syncText()
    }
    return
  }

  /* The text field is the composer's focus target. */
  focus(options) {
    if (this._textarea !== null) {
      this._textarea.focus(options)
    }
    return
  }
}
