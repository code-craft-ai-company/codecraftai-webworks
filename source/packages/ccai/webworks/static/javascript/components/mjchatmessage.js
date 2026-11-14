/*
 * mjchatmessage.js
 *
 * <mj-chat-message> -- single message bubble in a chat thread.
 * Supports incoming/outgoing/system variants, delivery status, reactions,
 * consecutive grouping, reply previews, and action menu.
 * Designed to live inside role="feed" per APG.
 *
 * `author-id` identifies the author for the host: it is exposed as
 * `authorId` and carried in the detail of every event this message fires,
 * so a thread can tell whose message was reacted to or acted on. It changes
 * nothing in the rendering, so it is not observed.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { autoPosition } from "../core/overlay.js";
import { safeUrl, safeLinkUrl } from "../core/html.js";
import { sanitizeHtmlToFragment } from "../core/sanitize.js";
import { formatDate, formatRelativeTime, t } from "../core/intl.js";

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

/* Tinted from the bubble's own text colour, so it shows on light, dark and accent bubbles. */
.reply-preview {
  background: var(--mj-msg-reply-bg, color-mix(in srgb, currentColor 8%, transparent));
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

.msg-html[hidden],
.msg-attachments[hidden] { display: none; }

.msg-html a,
.attachment-link {
  color: inherit;
  text-decoration: underline;
}

.msg-attachments {
  list-style: none;
  margin: var(--mj-space-2) 0 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: var(--mj-space-2);
}

.attachment-link {
  display: inline-flex;
  align-items: center;
  gap: var(--mj-space-1);
  font-size: var(--mj-font-size-xs);
}

.attachment-link:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.attachment-image {
  display: block;
  max-width: var(--mj-msg-attachment-size, 160px);
  max-height: var(--mj-msg-attachment-size, 160px);
  border-radius: var(--mj-radius-sm);
  object-fit: cover;
}

.attachment-size {
  opacity: 0.75;
}

.msg-article:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: calc(-1 * var(--mj-focus-ring-width));
}

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
  align-self: center;
  flex-shrink: 0;
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
  sent: "✓",
  delivered: "✓✓",
  read: "✓✓",
  failed: "⚠"
};

/* Keys of the status labels; resolved with t() when the status is shown. */
const STATUS_LABEL_KEYS = {
  sent: "mj.chatMessage.status.sent",
  delivered: "mj.chatMessage.status.delivered",
  read: "mj.chatMessage.status.read",
  failed: "mj.chatMessage.status.failed"
};

/* Tags a message body may contain. Everything else is unwrapped or dropped. */
const BODY_ALLOWED_TAGS = ["b", "i", "em", "strong", "a", "br", "p", "span", "mark", "code", "pre"];

/* Attributes kept per tag. No tag keeps style, class, id, target or on*. */
const BODY_ALLOWED_ATTRIBUTES = {
  a: ["href", "title"]
};

/*
 * Message bodies go through the shared allow-list sanitizer (core/sanitize.js):
 * parsed in an inert document, only the tags and attributes above kept, link
 * targets through safeLinkUrl (no script, data: or blob: URLs), every link
 * forced to rel="noopener noreferrer", and the result imported as nodes --
 * never re-parsed in the page. Unknown wrappers (a <div>) are unwrapped.
 */
const BODY_SANITIZE_OPTIONS = {
  allowedTags: BODY_ALLOWED_TAGS,
  allowedAttributes: BODY_ALLOWED_ATTRIBUTES,
  aliases: {},
  linkRel: "noopener noreferrer"
};

/*
 * Text that may be a date: ISO 8601 or a written date with a four-digit year,
 * made only of the characters dates use. Anything else is not parsed.
 */
const TIMESTAMP_TEXT_PATTERN = /^(?=.*\d{4})[0-9A-Za-z ,.:+\-\/]+$/;

/*
 * Parse a timestamp into a Date, or null when it cannot be parsed. A bare
 * `YYYY-MM-DD` is a local calendar day, not midnight UTC.
 */
function parseTimestamp(value) {
  let date = null

  if (typeof value === "string" && value.length > 0) {
    const dayMatch = value.match(/^(\d{4})-(\d{2})-(\d{2})$/)
    if (dayMatch !== null) {
      date = new Date(Number(dayMatch[1]), Number(dayMatch[2]) - 1, Number(dayMatch[3]))
    } else if (TIMESTAMP_TEXT_PATTERN.test(value) === true) {
      /*
       * The engine's date parser is lenient and reads arbitrary text with a
       * number in it as some date, so only date-like text is handed to it.
       */
      date = new Date(value)
    }
  }

  if (date !== null && Number.isNaN(date.getTime()) === true) {
    date = null
  }
  return date
}

/* Locale-aware "5 minutes ago" / "in 2 hours" / "now" for a Date. */
function relativeTime(date) {
  const diffSeconds = Math.round((date.getTime() - Date.now()) / 1000)
  const magnitude = Math.abs(diffSeconds)
  const direction = diffSeconds < 0 ? -1 : 1
  let text = ""

  if (magnitude < 60) {
    text = formatRelativeTime(0, "second")
  } else if (magnitude < 3600) {
    text = formatRelativeTime(direction * Math.floor(magnitude / 60), "minute")
  } else if (magnitude < 86400) {
    text = formatRelativeTime(direction * Math.floor(magnitude / 3600), "hour")
  } else {
    text = formatRelativeTime(direction * Math.floor(magnitude / 86400), "day")
  }
  return text
}

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

function formatSize(bytes) {
  if (bytes < 1024) { return `${bytes} B` }
  if (bytes < 1024 * 1024) { return `${(bytes / 1024).toFixed(1)} KB` }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

/*
 * One timer refreshes the relative timestamp of every connected message,
 * however many there are. It runs only while at least one is connected.
 */
const TICK_SUBSCRIBERS = new Set();
let tickTimer = null;

function subscribeTick(message) {
  TICK_SUBSCRIBERS.add(message)
  if (tickTimer === null) {
    tickTimer = window.setInterval(() => {
      TICK_SUBSCRIBERS.forEach((subscriber) => {
        subscriber._syncTimestamp()
      })
    }, 60000)
  }
  return
}

function unsubscribeTick(message) {
  TICK_SUBSCRIBERS.delete(message)
  if (TICK_SUBSCRIBERS.size === 0 && tickTimer !== null) {
    window.clearInterval(tickTimer)
    tickTimer = null
  }
  return
}

export class MjChatMessage extends MjElement {
  static tagName = "mj-chat-message";
  static styles = STYLES;
  static watched = [
    "variant", "consecutive", "author-name", "author-avatar",
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
    this._menuPositionDispose = null
    this._onDocumentPointerDown = this._handleDocumentPointerDown.bind(this)
    this._headerId = nextId("mj-msg-hdr")
    this._menuId = nextId("mj-msg-menu")

    this._articleEl = null
    this._avatarEl = null
    this._authorEl = null
    this._timeEl = null
    this._bodySlot = null
    this._htmlEl = null
    this._attachmentsEl = null
    this._replyPreviewEl = null
    this._reactionBar = null
    this._statusEl = null
    this._actionsTrigger = null
    this._contextMenu = null
  }

  /*
   * The markup holds no attribute or property values or localized text;
   * `afterRender`, `_syncAttributes` and the render helpers fill it in with
   * textContent / setAttribute.
   */
  render() {
    const markup = `
      <article class="msg-article" part="root" tabindex="-1">
        <div class="msg-avatar" part="avatar" aria-hidden="true"></div>
        <div class="msg-main">
          <header class="msg-header" part="header" id="${this._headerId}">
            <strong class="msg-author-name" part="author-name"></strong>
            <time class="msg-timestamp" part="timestamp"></time>
          </header>
          <div class="msg-bubble" part="bubble">
            <div class="reply-preview" part="reply-preview" hidden></div>
            <div class="msg-body" part="body"><slot name="body"><slot></slot></slot><div class="msg-html" hidden></div></div>
            <ul class="msg-attachments" part="attachments" hidden></ul>
          </div>
          <div class="reaction-bar" part="reaction-bar"></div>
          <div class="msg-status" part="status" role="img">
            <span class="status-icon" aria-hidden="true"></span>
          </div>
        </div>
        <button class="actions-trigger" part="actions-trigger" type="button"
                aria-haspopup="menu"
                aria-expanded="false" aria-controls="${this._menuId}">&#8943;</button>
      </article>
      <ul class="context-menu" part="context-menu" role="menu" id="${this._menuId}"
          hidden></ul>
    `
    return markup
  }

  afterRender() {
    this._articleEl = this.$(".msg-article")
    this._avatarEl = this.$(".msg-avatar")
    this._authorEl = this.$(".msg-author-name")
    this._timeEl = this.$(".msg-timestamp")
    this._bodySlot = this.$("slot[name=body]")
    this._htmlEl = this.$(".msg-html")
    this._attachmentsEl = this.$(".msg-attachments")
    this._replyPreviewEl = this.$(".reply-preview")
    this._reactionBar = this.$(".reaction-bar")
    this._statusEl = this.$(".msg-status")
    this._actionsTrigger = this.$(".actions-trigger")
    this._contextMenu = this.$(".context-menu")
    this._menuOpen = false

    this._attachmentsEl.setAttribute("aria-label", t("mj.chatMessage.attachmentsLabel"))
    this._actionsTrigger.setAttribute("aria-label", t("mj.chatMessage.actionsLabel"))
    this._contextMenu.setAttribute("aria-label", t("mj.chatMessage.actionsLabel"))

    this.listen(this._actionsTrigger, "click", this._onActionsClick.bind(this))
    this.listen(this._contextMenu, "click", this._onMenuClick.bind(this))
    this.listen(this._contextMenu, "keydown", this._onMenuKeydown.bind(this))
    this.listen(this._reactionBar, "click", this._onReactionClick.bind(this))
    this.listen(this._htmlEl, "click", this._onBodyLinkClick.bind(this))

    subscribeTick(this)
    this.onTeardown(() => {
      unsubscribeTick(this)
      this._closeMenu()
    })

    this._syncAttributes()
    this._renderBodyHtml()
    this._renderAttachments()
    this._renderReactions()
    this._renderReplyPreview()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._articleEl === undefined || this._articleEl === null) {
      return
    }

    if (name === "allow-reactions") {
      this._renderReactions()
    } else if (name === "allow-actions") {
      if (this._actionsAllowed() === false) {
        this._closeMenu()
      }
    } else {
      this._syncAttributes()
      if (name === "variant" || name === "status") {
        /* The menu's items depend on both; an open menu would be stale. */
        this._closeMenu()
      }
    }
    return
  }

  /* ----- attribute-derived content ----- */

  _messageId() {
    const messageId = this.getAttribute("message-id") || ""
    return messageId
  }

  _authorId() {
    const authorId = this.getAttribute("author-id") || ""
    return authorId
  }

  _actionsAllowed() {
    const allowed = this.hasAttribute("allow-actions") === true && this.getAttribute("allow-actions") !== "false"
    return allowed
  }

  /* Author, avatar, timestamp, status and the article's accessible name. */
  _syncAttributes() {
    const authorName = this.getAttribute("author-name") || ""
    const consecutive = this.hasAttribute("consecutive")

    this._authorEl.textContent = authorName

    /* Avatar: an image when the URL is acceptable, initials otherwise. */
    const avatarUrl = safeUrl(this.getAttribute("author-avatar") || "", "")
    this._avatarEl.textContent = ""
    if (avatarUrl.length > 0) {
      const img = document.createElement("img")
      img.alt = ""
      img.src = avatarUrl
      this._avatarEl.appendChild(img)
    } else {
      this._avatarEl.textContent = initials(authorName)
    }

    /*
     * A consecutive message hides its header, so the article is named
     * directly; otherwise the visible header names it.
     */
    if (consecutive === true && authorName.length > 0) {
      this._articleEl.removeAttribute("aria-labelledby")
      this._articleEl.setAttribute("aria-label", t("mj.chatMessage.messageFrom", { name: authorName }))
    } else {
      this._articleEl.removeAttribute("aria-label")
      this._articleEl.setAttribute("aria-labelledby", this._headerId)
    }

    const statusValue = this.getAttribute("status") || "sent"
    const knownStatus = Object.prototype.hasOwnProperty.call(STATUS_LABEL_KEYS, statusValue)
    const status = knownStatus === true ? statusValue : "sent"
    this._statusEl.className = `msg-status status-${status}`
    this._statusEl.setAttribute("aria-label", t(STATUS_LABEL_KEYS[status]))
    this._statusEl.querySelector(".status-icon").textContent = STATUS_ICONS[status]

    this._syncTimestamp()
    return
  }

  /* Also called by the shared ticker to keep the relative time current. */
  _syncTimestamp() {
    if (this._timeEl === null) {
      return
    }
    const raw = this.getAttribute("timestamp") || ""
    const date = parseTimestamp(raw)

    if (date !== null) {
      this._timeEl.setAttribute("datetime", date.toISOString())
      this._timeEl.setAttribute("title", formatDate(date, { dateStyle: "medium", timeStyle: "short" }))
      this._timeEl.textContent = relativeTime(date)
    } else {
      /* Not a date: shown as given, never as "NaN". */
      this._timeEl.removeAttribute("datetime")
      this._timeEl.removeAttribute("title")
      this._timeEl.textContent = raw
    }
    return
  }

  /* ----- body, attachments, reply preview ----- */

  _renderBodyHtml() {
    if (this._htmlEl === null) {
      return
    }

    if (this._bodyHtml === null) {
      /* No HTML body: the slotted content (or plain child text) shows again. */
      this._htmlEl.textContent = ""
      this._htmlEl.hidden = true
      this._bodySlot.hidden = false
    } else {
      this._htmlEl.replaceChildren(sanitizeHtmlToFragment(this._bodyHtml, BODY_SANITIZE_OPTIONS))
      this._htmlEl.hidden = false
      this._bodySlot.hidden = true
    }
    return
  }

  /* Links in the HTML body can be intercepted by the host. */
  _onBodyLinkClick(event) {
    const link = event.target.closest("a")
    if (link === null || link.hasAttribute("href") === false) {
      return
    }
    const proceed = this.emit("mj-message-link-click", {
      href: link.href,
      messageId: this._messageId(),
      authorId: this._authorId()
    }, { cancelable: true })
    if (proceed === false) {
      event.preventDefault()
    }
    return
  }

  /* Image attachments show a thumbnail; other files a named link with their size. */
  _renderAttachments() {
    if (this._attachmentsEl === null) {
      return
    }

    this._attachmentsEl.textContent = ""
    this._attachmentsEl.hidden = this._attachments.length === 0

    for (let i = 0; i < this._attachments.length; i = i + 1) {
      const attachment = this._attachments[i]
      const name = attachment.name !== undefined && attachment.name !== null ? String(attachment.name) : t("mj.chatMessage.attachmentFallbackName")
      const url = safeLinkUrl(attachment.url, "")
      const mimeType = typeof attachment.mimeType === "string" ? attachment.mimeType : ""
      const thumbnailUrl = safeUrl(attachment.thumbnailUrl !== undefined ? attachment.thumbnailUrl : attachment.url, "")

      const li = document.createElement("li")
      const holder = url.length > 0 ? document.createElement("a") : document.createElement("span")
      holder.className = "attachment-link"
      if (url.length > 0) {
        holder.setAttribute("href", url)
        holder.setAttribute("target", "_blank")
        holder.setAttribute("rel", "noopener noreferrer")
      }

      if (mimeType.startsWith("image/") === true && thumbnailUrl.length > 0) {
        const img = document.createElement("img")
        img.className = "attachment-image"
        img.alt = name
        img.src = thumbnailUrl
        holder.appendChild(img)
      } else {
        const nameEl = document.createElement("span")
        nameEl.textContent = name
        holder.appendChild(nameEl)
        const size = Number(attachment.size)
        if (Number.isFinite(size) === true && size > 0) {
          const sizeEl = document.createElement("span")
          sizeEl.className = "attachment-size"
          sizeEl.textContent = `(${formatSize(size)})`
          holder.appendChild(sizeEl)
        }
      }

      li.appendChild(holder)
      this._attachmentsEl.appendChild(li)
    }
    return
  }

  _renderReplyPreview() {
    if (this._replyPreviewEl === null) {
      return
    }
    if (this._replyTo === null) {
      this._replyPreviewEl.hidden = true
      this._replyPreviewEl.textContent = ""
      return
    }
    const authorName = this._replyTo.authorName !== undefined && this._replyTo.authorName !== null ? String(this._replyTo.authorName) : ""
    const preview = this._replyTo.preview !== undefined && this._replyTo.preview !== null ? String(this._replyTo.preview) : ""
    this._replyPreviewEl.hidden = false
    this._replyPreviewEl.textContent = authorName.length > 0 ? `${authorName}: ${preview}` : preview
    return
  }

  /* ----- reactions ----- */

  _renderReactions() {
    if (this._reactionBar === null) {
      return
    }

    const hadFocusOn = this.shadowRoot.activeElement !== null && this._reactionBar.contains(this.shadowRoot.activeElement) === true
      ? this.shadowRoot.activeElement.getAttribute("data-emoji")
      : null

    this._reactionBar.textContent = ""

    const allowReactions = this.getAttribute("allow-reactions") !== "false"
    if (allowReactions === false) {
      return
    }

    for (let i = 0; i < this._reactions.length; i = i + 1) {
      const reaction = this._reactions[i]
      const emoji = String(reaction.emoji)
      const userIds = Array.isArray(reaction.userIds) === true ? reaction.userIds.map((userId) => String(userId)) : []
      const active = this._currentUserId.length > 0 && userIds.indexOf(this._currentUserId) >= 0

      const chip = document.createElement("button")
      chip.className = "reaction-chip"
      chip.setAttribute("type", "button")
      chip.setAttribute("aria-pressed", active === true ? "true" : "false")
      chip.setAttribute("aria-label", t("mj.chatMessage.reactWith", { emoji: emoji, count: reaction.count }))
      chip.setAttribute("data-emoji", emoji)

      const emojiEl = document.createElement("span")
      emojiEl.textContent = emoji
      const countEl = document.createElement("span")
      countEl.textContent = String(reaction.count)
      chip.appendChild(emojiEl)
      chip.appendChild(countEl)

      this._reactionBar.appendChild(chip)
      if (hadFocusOn === emoji) {
        chip.focus()
      }
    }
    return
  }

  _onReactionClick(event) {
    const chip = event.target.closest(".reaction-chip")
    if (chip === null) {
      return
    }
    const wasActive = chip.getAttribute("aria-pressed") === "true"
    chip.setAttribute("aria-pressed", wasActive === true ? "false" : "true")
    this.emit("mj-message-react", {
      messageId: this._messageId(),
      authorId: this._authorId(),
      emoji: chip.getAttribute("data-emoji"),
      active: wasActive === false
    })
    return
  }

  /* ----- action menu ----- */

  /* Build the menu items for the message as it is now (variant, status). */
  _buildContextMenu() {
    const actions = [
      { action: "reply", label: t("mj.chatMessage.reply") },
      { action: "copy", label: t("mj.chatMessage.copyText") }
    ]

    const variant = this.getAttribute("variant") || "incoming"
    if (variant === "outgoing") {
      if (this.getAttribute("status") === "failed") {
        actions.push({ action: "retry", label: t("mj.chatMessage.retry") })
      }
      actions.push({ action: "edit", label: t("mj.chatMessage.edit") })
      actions.push({ action: "delete", label: t("mj.chatMessage.delete") })
    }

    this._contextMenu.textContent = ""
    for (let i = 0; i < actions.length; i = i + 1) {
      const item = actions[i]
      const li = document.createElement("li")
      li.setAttribute("role", "none")
      const btn = document.createElement("button")
      btn.className = "ctx-item"
      btn.setAttribute("role", "menuitem")
      btn.setAttribute("type", "button")
      btn.setAttribute("tabindex", "-1")
      btn.setAttribute("data-action", item.action)
      btn.textContent = item.label
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
    if (this._contextMenu === null || this._actionsAllowed() === false) {
      return
    }

    this._buildContextMenu()
    this._menuOpen = true
    this._contextMenu.hidden = false
    this._actionsTrigger.setAttribute("aria-expanded", "true")

    /* Kept against the trigger while scrolling; flips and shifts into view. */
    this._menuPositionDispose = autoPosition(this._contextMenu, this._actionsTrigger, {
      placement: "bottom-start",
      offset: 4
    })

    /* The outside-press listener exists only while this menu is open. */
    document.addEventListener("pointerdown", this._onDocumentPointerDown, true)

    const firstItem = this._contextMenu.querySelector(".ctx-item")
    if (firstItem !== null) {
      firstItem.focus()
    }
    return
  }

  _closeMenu() {
    if (this._contextMenu === null || this._menuOpen === false) {
      return
    }
    this._menuOpen = false
    this._contextMenu.hidden = true
    this._actionsTrigger.setAttribute("aria-expanded", "false")

    if (this._menuPositionDispose !== null) {
      this._menuPositionDispose()
      this._menuPositionDispose = null
    }
    document.removeEventListener("pointerdown", this._onDocumentPointerDown, true)
    return
  }

  _handleDocumentPointerDown(event) {
    const path = typeof event.composedPath === "function" ? event.composedPath() : []
    const inside = path.indexOf(this._contextMenu) >= 0 || path.indexOf(this._actionsTrigger) >= 0
    if (inside === false) {
      this._closeMenu()
    }
    return
  }

  _onMenuClick(event) {
    const item = event.target.closest(".ctx-item")
    if (item === null) {
      return
    }
    const action = item.getAttribute("data-action")
    const messageId = this._messageId()

    this._closeMenu()
    this._actionsTrigger.focus()

    if (action === "reply") {
      this.emit("mj-message-reply", { messageId: messageId, authorId: this._authorId() })
    } else {
      this.emit("mj-message-action", { messageId: messageId, authorId: this._authorId(), action: action })
    }
    return
  }

  /* APG menu keys. Enter and Space activate the focused button natively. */
  _onMenuKeydown(event) {
    const items = Array.from(this._contextMenu.querySelectorAll(".ctx-item"))
    const current = items.indexOf(this.shadowRoot.activeElement)
    let target = -1

    if (event.key === "Escape") {
      event.preventDefault()
      event.stopPropagation()
      this._closeMenu()
      this._actionsTrigger.focus()
    } else if (event.key === "Tab") {
      /* Focus leaves the menu; it must not stay open behind it. */
      this._closeMenu()
    } else if (event.key === "ArrowDown") {
      target = current + 1 < items.length ? current + 1 : 0
    } else if (event.key === "ArrowUp") {
      target = current - 1 >= 0 ? current - 1 : items.length - 1
    } else if (event.key === "Home") {
      target = 0
    } else if (event.key === "End") {
      target = items.length - 1
    }

    if (target >= 0 && target < items.length) {
      event.preventDefault()
      items[target].focus()
    }
    return
  }

  /* ----- public API ----- */

  /* A parent feed moves focus to a message; the article is the focus target. */
  focus(options) {
    if (this._articleEl !== null) {
      this._articleEl.focus(options)
    } else {
      super.focus(options)
    }
    return
  }

  get bodyHtml() {
    return this._bodyHtml
  }

  /*
   * HTML for the body (for example the output of a Markdown renderer). It is
   * sanitized against an allowlist before it is shown. null restores the
   * slotted body.
   */
  set bodyHtml(html) {
    this._bodyHtml = html !== null && html !== undefined ? String(html) : null
    this._renderBodyHtml()
    return
  }

  get attachments() {
    return this._attachments
  }

  set attachments(value) {
    this._attachments = Array.isArray(value) ? value : []
    this._renderAttachments()
    return
  }

  get reactions() {
    return this._reactions
  }

  set reactions(value) {
    this._reactions = Array.isArray(value) ? value : []
    this._renderReactions()
    return
  }

  get replyTo() {
    return this._replyTo
  }

  set replyTo(value) {
    this._replyTo = value !== undefined ? value : null
    this._renderReplyPreview()
    return
  }

  /* The `author-id` attribute ("" when absent). */
  get authorId() {
    return this._authorId()
  }

  set authorId(value) {
    if (value === null || value === undefined) {
      this.removeAttribute("author-id")
    } else {
      this.setAttribute("author-id", String(value))
    }
    return
  }

  get currentUserId() {
    return this._currentUserId
  }

  set currentUserId(id) {
    this._currentUserId = id !== null && id !== undefined ? String(id) : ""
    this._renderReactions()
    return
  }
}
