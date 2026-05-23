/*
 * mjchatmessage.js
 *
 * <mj-chat-message> -- single message bubble in a chat thread.
 * Supports incoming/outgoing/system variants, delivery status, reactions,
 * consecutive grouping, reply previews, and action menu.
 * Designed to live inside role="feed" per APG.
 */

import { MjElement, nextId } from "../core/mjelement.js";

const STYLES = `
:host {
  display: block;
}

.msg-article {
  display: flex;
  gap: var(--mj-space-2);
  align-items: flex-end;
  padding: var(--mj-space-1) var(--mj-space-3);
  position: relative;
  outline: none;
}

:host([variant="outgoing"]) .msg-article {
  flex-direction: row-reverse;
}

:host([variant="system"]) .msg-article {
  justify-content: center;
  padding: var(--mj-space-2);
}

:host([consecutive]) .msg-article {
  padding-top: var(--mj-space-1);
}

.msg-avatar {
  width: var(--mj-msg-avatar-size, 32px);
  height: var(--mj-msg-avatar-size, 32px);
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

.msg-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

:host([consecutive]) .msg-avatar { visibility: hidden; }
:host([variant="outgoing"]) .msg-avatar { display: none; }
:host([variant="system"]) .msg-avatar { display: none; }

.msg-main {
  display: flex;
  flex-direction: column;
  gap: var(--mj-space-1);
  max-width: var(--mj-msg-max-width, 70%);
  min-width: 60px;
}

:host([variant="system"]) .msg-main { max-width: 80%; text-align: center; }

.msg-header {
  display: flex;
  align-items: baseline;
  gap: var(--mj-space-2);
}

:host([variant="outgoing"]) .msg-header { flex-direction: row-reverse; }
:host([consecutive]) .msg-header { display: none; }
:host([variant="system"]) .msg-header { justify-content: center; }

.msg-author-name {
  font-size: var(--mj-font-size-xs);
  font-weight: var(--mj-font-weight-medium);
  color: var(--mj-text-muted);
}

.msg-timestamp {
  font-size: var(--mj-font-size-xs);
  color: var(--mj-msg-timestamp-color, var(--mj-text-muted));
}

.msg-bubble {
  background: var(--mj-msg-bubble-bg-incoming, var(--mj-surface));
  border-radius: var(--mj-msg-bubble-radius, var(--mj-radius-lg));
  border-end-start-radius: var(--mj-radius-sm);
  padding: var(--mj-space-2) var(--mj-space-3);
  word-break: break-word;
  overflow-wrap: break-word;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
  line-height: var(--mj-line-height);
  box-shadow: var(--mj-elevation-1);
  position: relative;
}

:host([variant="outgoing"]) .msg-bubble {
  background: var(--mj-msg-bubble-bg-outgoing, var(--mj-accent));
  color: var(--mj-msg-bubble-color-outgoing, var(--mj-text-on-accent));
  border-end-start-radius: var(--mj-msg-bubble-radius, var(--mj-radius-lg));
  border-end-end-radius: var(--mj-radius-sm);
}

:host([variant="system"]) .msg-bubble {
  background: var(--mj-bg-subtle);
  color: var(--mj-text-muted);
  font-style: italic;
  box-shadow: none;
  border-radius: var(--mj-radius-pill);
  font-size: var(--mj-font-size-xs);
}

.reply-preview {
  background: rgba(0,0,0,0.08);
  border-inline-start: 3px solid currentColor;
  opacity: 0.8;
  padding: var(--mj-space-1) var(--mj-space-2);
  border-radius: var(--mj-radius-sm) var(--mj-radius-sm) 0 0;
  font-size: var(--mj-font-size-xs);
  margin-bottom: var(--mj-space-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reply-preview[hidden] { display: none; }

.msg-status {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--mj-space-1);
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
  padding-block-start: var(--mj-space-1);
}

:host(:not([variant="outgoing"])) .msg-status { display: none; }

.status-icon { font-size: 0.75em; }

.status-read .status-icon { color: var(--mj-msg-status-color-read, var(--mj-accent)); }
.status-failed .status-icon { color: var(--mj-color-danger); }

.reaction-bar {
  display: flex;
  gap: var(--mj-space-1);
  flex-wrap: wrap;
  margin-top: var(--mj-space-1);
}

.reaction-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: var(--mj-space-1) var(--mj-space-2);
  background: transparent;
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-pill);
  cursor: pointer;
  font: inherit;
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text);
}

.reaction-chip[aria-pressed="true"] {
  background: var(--mj-bg-muted);
  border-color: var(--mj-accent);
  color: var(--mj-accent);
}

.reaction-chip:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}

.actions-trigger {
  position: absolute;
  inset-block-start: 50%;
  translate: 0 -50%;
  inset-inline-end: calc(-1 * var(--mj-control-height-sm) - var(--mj-space-1));
  opacity: 0;
  background: var(--mj-surface);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-sm);
  cursor: pointer;
  width: var(--mj-control-height-sm);
  height: var(--mj-control-height-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--mj-text-muted);
  font-size: var(--mj-font-size-sm);
  transition: opacity var(--mj-motion-fast) var(--mj-motion-ease);
  box-shadow: var(--mj-elevation-1);
}

.msg-article:hover .actions-trigger,
.msg-article:focus-within .actions-trigger {
  opacity: 1;
}

.actions-trigger:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  opacity: 1;
}

:host(:not([allow-actions])) .actions-trigger,
:host([allow-actions="false"]) .actions-trigger { display: none; }

.context-menu {
  position: fixed;
  z-index: var(--mj-layer-popover);
  background: var(--mj-surface-raised);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-md);
  box-shadow: var(--mj-elevation-2);
  padding: var(--mj-space-1) 0;
  min-width: 140px;
  list-style: none;
  margin: 0;
}

.context-menu[hidden] { display: none; }

.ctx-item {
  display: flex;
  width: 100%;
  padding: var(--mj-space-2) var(--mj-space-4);
  background: none;
  border: none;
  text-align: start;
  cursor: pointer;
  font: inherit;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
}

.ctx-item:hover { background: var(--mj-bg-muted); }
.ctx-item:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: calc(-1 * var(--mj-focus-ring-offset));
}

.ctx-item[data-action="delete"] { color: var(--mj-color-danger); }
`;

const STATUS_ICONS = {
  sent: "&#10003;",
  delivered: "&#10003;&#10003;",
  read: "&#10003;&#10003;",
  failed: "&#9888;"
};

const STATUS_LABELS = {
  sent: "Sent",
  delivered: "Delivered",
  read: "Read",
  failed: "Failed to send"
};

function relativeTime(ts) {
  if (ts === null || ts === undefined || ts === "") {
    return ""
  }
  const diff = Date.now() - new Date(ts).getTime()
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  if (seconds < 60) { return "just now" }
  if (minutes < 60) { return `${minutes}m ago` }
  if (hours < 24) { return `${hours}h ago` }
  return `${days}d ago`
}

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

function sanitizeHtml(html) {
  // Minimal allowlist sanitization
  const allowed = new Set(["b", "i", "em", "strong", "a", "br", "p", "span", "mark", "code", "pre"])
  const temp = document.createElement("div")
  temp.innerHTML = html
  const allEls = temp.querySelectorAll("*")
  for (let i = 0; i < allEls.length; i = i + 1) {
    const el = allEls[i]
    if (allowed.has(el.tagName.toLowerCase()) === false) {
      el.replaceWith(document.createTextNode(el.textContent))
    }
  }
  // Remove all event-handler attributes
  const remaining = temp.querySelectorAll("*")
  for (let i = 0; i < remaining.length; i = i + 1) {
    const el = remaining[i]
    const attrs = Array.from(el.attributes)
    for (let j = 0; j < attrs.length; j = j + 1) {
      const attr = attrs[j]
      if (attr.name.startsWith("on") || attr.name === "href" && !attr.value.startsWith("https") && !attr.value.startsWith("http") && !attr.value.startsWith("/")) {
        el.removeAttribute(attr.name)
      }
    }
  }
  return temp.innerHTML
}

export class MjChatMessage extends MjElement {
  static tagName = "mj-chat-message";
  static styles = STYLES;
  static watched = [
    "variant", "consecutive", "author-name", "author-id", "author-avatar",
    "timestamp", "status", "message-id", "allow-reactions", "allow-actions"
  ];

  constructor() {
    super()
    this._bodyHtml = null
    this._attachments = []
    this._reactions = []
    this._replyTo = null
    this._currentUserId = ""
    this._menuOpen = false
    this._headerId = nextId("mj-msg-hdr")
    this._articleEl = null
    this._contextMenu = null
  }

  render() {
    const variant = this.getAttribute("variant") || "incoming"
    const authorName = this.getAttribute("author-name") || ""
    const authorAvatar = this.getAttribute("author-avatar") || ""
    const timestamp = this.getAttribute("timestamp") || ""
    const status = this.getAttribute("status") || "sent"
    const msgId = this.getAttribute("message-id") || nextId("mj-msg")
    const consecutive = this.hasAttribute("consecutive")
    const allowReactions = this.getAttribute("allow-reactions") !== "false"

    const relTs = relativeTime(timestamp)
    const absTs = timestamp !== "" ? new Date(timestamp).toLocaleString() : ""

    const avatarHtml = authorAvatar.length > 0
      ? `<img src="${authorAvatar}" alt="${authorName}"/>`
      : initials(authorName)

    const statusHtml = variant === "outgoing"
      ? `<div class="msg-status status-${status}" part="status"
              aria-label="${STATUS_LABELS[status] || status}">
           <span class="status-icon" aria-hidden="true">${STATUS_ICONS[status] || ""}</span>
           <span class="sr-only" style="position:absolute;opacity:0;">${STATUS_LABELS[status] || status}</span>
         </div>`
      : ""

    const consecutiveAriaLabel = consecutive && authorName.length > 0
      ? `aria-label="Message from ${authorName}"`
      : ""

    const markup = `
      <article class="msg-article" part="root" tabindex="-1"
               aria-labelledby="${this._headerId}"
               ${consecutiveAriaLabel}>
        <div class="msg-avatar" part="avatar" aria-hidden="true">
          ${avatarHtml}
        </div>
        <div class="msg-main">
          <header class="msg-header" part="header" id="${this._headerId}">
            <strong class="msg-author-name" part="author-name">${authorName}</strong>
            <time class="msg-timestamp" part="timestamp"
                  datetime="${timestamp}" title="${absTs}">${relTs}</time>
          </header>
          <div class="msg-bubble" part="bubble">
            <div class="reply-preview" part="reply-preview" hidden></div>
            <div class="msg-body" part="body">
              <slot name="body"></slot>
            </div>
          </div>
          <div class="reaction-bar" part="reaction-bar"></div>
          ${statusHtml}
        </div>
        <button class="actions-trigger" part="actions-trigger" type="button"
                aria-label="Message actions" aria-haspopup="menu"
                aria-expanded="false">&#8943;</button>
      </article>
      <ul class="context-menu" part="context-menu" role="menu"
          aria-label="Message actions" hidden></ul>
    `
    return markup
  }

  afterRender() {
    this._articleEl = this.$(".msg-article")
    this._bodyEl = this.$(".msg-body")
    this._replyPreviewEl = this.$(".reply-preview")
    this._reactionBar = this.$(".reaction-bar")
    this._actionsTrigger = this.$(".actions-trigger")
    this._contextMenu = this.$(".context-menu")

    if (this._bodyHtml !== null) {
      this._renderBodyHtml()
    }
    if (this._reactions.length > 0) {
      this._renderReactions()
    }
    if (this._replyTo !== null) {
      this._renderReplyPreview()
    }

    this.listen(this._actionsTrigger, "click", this._onActionsClick.bind(this))
    this.listen(this._articleEl, "keydown", this._onArticleKeydown.bind(this))

    // Close menu on outside click
    this.listen(document, "click", (event) => {
      if (this._menuOpen === true && !this.contains(event.target)) {
        this._closeMenu()
      }
    })

    this._buildContextMenu()
    return
  }

  _buildContextMenu() {
    if (this._contextMenu === null) {
      return
    }
    const msgId = this.getAttribute("message-id") || ""
    const actions = [
      { action: "reply", label: "Reply" },
      { action: "copy", label: "Copy text" }
    ]

    const variant = this.getAttribute("variant") || "incoming"
    if (variant === "outgoing") {
      actions.push({ action: "edit", label: "Edit" })
      actions.push({ action: "delete", label: "Delete" })
    }

    this._contextMenu.innerHTML = ""
    for (let i = 0; i < actions.length; i = i + 1) {
      const item = actions[i]
      const li = document.createElement("li")
      li.setAttribute("role", "presentation")
      const btn = document.createElement("button")
      btn.className = "ctx-item"
      btn.setAttribute("role", "menuitem")
      btn.setAttribute("type", "button")
      btn.setAttribute("data-action", item.action)
      btn.textContent = item.label
      this.listen(btn, "click", this._onContextAction.bind(this, item.action, msgId))
      li.appendChild(btn)
      this._contextMenu.appendChild(li)
    }
    return
  }

  _onActionsClick() {
    if (this._menuOpen === true) {
      this._closeMenu()
    } else {
      this._openMenu()
    }
    return
  }

  _openMenu() {
    if (this._contextMenu === null || this._actionsTrigger === null) {
      return
    }
    this._menuOpen = true
    this._contextMenu.hidden = false
    this._actionsTrigger.setAttribute("aria-expanded", "true")

    const rect = this._actionsTrigger.getBoundingClientRect()
    this._contextMenu.style.position = "fixed"
    this._contextMenu.style.top = `${rect.bottom + 4}px`
    this._contextMenu.style.left = `${rect.left}px`

    const firstItem = this._contextMenu.querySelector(".ctx-item")
    if (firstItem !== null) {
      firstItem.focus()
    }
    return
  }

  _closeMenu() {
    if (this._contextMenu === null) {
      return
    }
    this._menuOpen = false
    this._contextMenu.hidden = true
    if (this._actionsTrigger !== null) {
      this._actionsTrigger.setAttribute("aria-expanded", "false")
    }
    return
  }

  _onContextAction(action, msgId) {
    this._closeMenu()

    if (action === "reply") {
      this.emit("mj-message-reply", { messageId: msgId })
    } else {
      this.emit("mj-message-action", { messageId: msgId, action: action })
    }
    return
  }

  _onArticleKeydown(event) {
    if (event.key === "Escape" && this._menuOpen === true) {
      event.preventDefault()
      this._closeMenu()
      if (this._actionsTrigger !== null) {
        this._actionsTrigger.focus()
      }
    }
    return
  }

  _renderBodyHtml() {
    if (this._bodyEl === null || this._bodyHtml === null) {
      return
    }
    const sanitized = sanitizeHtml(this._bodyHtml)
    const existingSlot = this._bodyEl.querySelector("slot")
    if (existingSlot !== null) {
      existingSlot.remove()
    }
    this._bodyEl.innerHTML = sanitized

    // Intercept links
    const links = this._bodyEl.querySelectorAll("a")
    const msgId = this.getAttribute("message-id") || ""
    for (let i = 0; i < links.length; i = i + 1) {
      const link = links[i]
      this.listen(link, "click", (event) => {
        const proceed = this.emit("mj-message-link-click", {
          href: link.href,
          messageId: msgId
        }, { cancelable: true })
        if (proceed === false) {
          event.preventDefault()
        }
      })
    }
    return
  }

  _renderReactions() {
    if (this._reactionBar === null) {
      return
    }
    const allowReactions = this.getAttribute("allow-reactions") !== "false"
    if (allowReactions === false || this._reactions.length === 0) {
      this._reactionBar.innerHTML = ""
      return
    }

    const msgId = this.getAttribute("message-id") || ""
    this._reactionBar.innerHTML = ""
    for (let i = 0; i < this._reactions.length; i = i + 1) {
      const r = this._reactions[i]
      const active = Array.isArray(r.userIds) &&
        this._currentUserId.length > 0 &&
        r.userIds.indexOf(this._currentUserId) >= 0

      const chip = document.createElement("button")
      chip.className = "reaction-chip"
      chip.setAttribute("type", "button")
      chip.setAttribute("aria-pressed", active ? "true" : "false")
      chip.setAttribute("aria-label", `React with ${r.emoji}, ${r.count} reactions`)
      chip.setAttribute("data-emoji", r.emoji)
      chip.innerHTML = `${r.emoji} <span>${r.count}</span>`

      this.listen(chip, "click", () => {
        const wasActive = chip.getAttribute("aria-pressed") === "true"
        chip.setAttribute("aria-pressed", wasActive ? "false" : "true")
        this.emit("mj-message-react", {
          messageId: msgId,
          emoji: r.emoji,
          active: !wasActive
        })
      })
      this._reactionBar.appendChild(chip)
    }
    return
  }

  _renderReplyPreview() {
    if (this._replyPreviewEl === null) {
      return
    }
    if (this._replyTo === null) {
      this._replyPreviewEl.hidden = true
      return
    }
    this._replyPreviewEl.hidden = false
    this._replyPreviewEl.textContent = `${this._replyTo.authorName}: ${this._replyTo.preview}`
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "allow-reactions" && this._reactionBar !== null) {
      this._renderReactions()
    }
    return
  }

  get bodyHtml() {
    return this._bodyHtml
  }

  set bodyHtml(html) {
    this._bodyHtml = html !== null && html !== undefined ? String(html) : null
    if (this._bodyEl !== null) {
      this._renderBodyHtml()
    }
    return
  }

  get attachments() {
    return this._attachments
  }

  set attachments(value) {
    this._attachments = Array.isArray(value) ? value : []
    return
  }

  get reactions() {
    return this._reactions
  }

  set reactions(value) {
    this._reactions = Array.isArray(value) ? value : []
    if (this._reactionBar !== null) {
      this._renderReactions()
    }
    return
  }

  get replyTo() {
    return this._replyTo
  }

  set replyTo(value) {
    this._replyTo = value !== undefined ? value : null
    if (this._replyPreviewEl !== null) {
      this._renderReplyPreview()
    }
    return
  }

  get currentUserId() {
    return this._currentUserId
  }

  set currentUserId(id) {
    this._currentUserId = id || ""
    if (this._reactionBar !== null) {
      this._renderReactions()
    }
    return
  }
}
