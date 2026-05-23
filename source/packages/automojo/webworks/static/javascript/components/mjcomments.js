/*
 * mjcomments.js
 *
 * <mj-comments> -- threaded comment section with replies, inline editing,
 * emoji reactions, relative timestamps, and APG Feed pattern.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";

const STYLES = `
:host {
  display: block;
}

.comments-root {
  display: flex;
  flex-direction: column;
  gap: var(--mj-space-4);
}

.count-heading {
  font-size: var(--mj-font-size-md);
  font-weight: var(--mj-font-weight-bold);
  color: var(--mj-text);
  margin: 0;
}

.composer-area {
  background: var(--mj-comments-composer-bg, var(--mj-bg-subtle));
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-md);
  padding: var(--mj-space-3);
  display: flex;
  flex-direction: column;
  gap: var(--mj-space-2);
}

:host([readonly]) .composer-area { display: none; }

.composer-textarea {
  width: 100%;
  min-height: var(--mj-control-height-lg);
  padding: var(--mj-space-2);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-sm);
  font: inherit;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
  background: var(--mj-surface);
  resize: vertical;
  box-sizing: border-box;
}

.composer-textarea:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}

.composer-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--mj-space-2);
}

.composer-submit-btn {
  padding: var(--mj-space-2) var(--mj-space-4);
  background: var(--mj-accent);
  color: var(--mj-text-on-accent);
  border: none;
  border-radius: var(--mj-radius-md);
  font: inherit;
  font-size: var(--mj-font-size-sm);
  cursor: pointer;
}

.composer-submit-btn:hover { background: var(--mj-accent-hover); }
.composer-submit-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.feed-list {
  display: flex;
  flex-direction: column;
  gap: var(--mj-comments-gap, var(--mj-space-5));
}

.comment-article {
  display: flex;
  gap: var(--mj-space-3);
  align-items: flex-start;
  position: relative;
}

.comment-avatar {
  width: var(--mj-comments-avatar-size, 32px);
  height: var(--mj-comments-avatar-size, 32px);
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

.comment-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.comment-content {
  flex: 1;
  min-width: 0;
}

.comment-header {
  display: flex;
  align-items: baseline;
  gap: var(--mj-space-2);
  margin-bottom: var(--mj-space-1);
  flex-wrap: wrap;
}

.comment-author {
  font-weight: var(--mj-font-weight-medium);
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
}

.comment-time {
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
}

.comment-body {
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
  line-height: var(--mj-line-height);
  white-space: pre-wrap;
  word-break: break-word;
}

.comment-body[data-deleted="true"] {
  font-style: italic;
  color: var(--mj-text-muted);
}

.comment-actions {
  display: flex;
  gap: var(--mj-space-2);
  margin-top: var(--mj-space-2);
  flex-wrap: wrap;
}

.action-btn {
  background: none;
  border: none;
  cursor: pointer;
  font: inherit;
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
  padding: var(--mj-space-1) var(--mj-space-2);
  border-radius: var(--mj-radius-sm);
}

.action-btn:hover { background: var(--mj-bg-muted); color: var(--mj-text); }
.action-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}

.reaction-bar {
  display: flex;
  gap: var(--mj-space-1);
  margin-top: var(--mj-space-2);
  flex-wrap: wrap;
}

.reaction-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: var(--mj-space-1) var(--mj-space-2);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-pill);
  background: transparent;
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

.reply-thread {
  margin-inline-start: var(--mj-comments-reply-indent, 2.5rem);
  margin-block-start: var(--mj-space-3);
  border-inline-start: var(--mj-comments-thread-line, 2px solid var(--mj-border));
  padding-inline-start: var(--mj-space-3);
  display: flex;
  flex-direction: column;
  gap: var(--mj-space-3);
}

.reply-composer {
  margin-inline-start: var(--mj-comments-reply-indent, 2.5rem);
  margin-block-start: var(--mj-space-2);
}

.show-more-replies-btn {
  background: none;
  border: none;
  cursor: pointer;
  font: inherit;
  font-size: var(--mj-font-size-xs);
  color: var(--mj-accent);
  padding: var(--mj-space-1) 0;
}

.empty-state {
  padding: var(--mj-space-5);
  text-align: center;
  color: var(--mj-text-muted);
  font-size: var(--mj-font-size-sm);
}

.load-older-btn {
  display: block;
  width: 100%;
  padding: var(--mj-space-2);
  background: none;
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-md);
  font: inherit;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text-muted);
  cursor: pointer;
  text-align: center;
}

.load-older-btn:hover { background: var(--mj-bg-muted); }
`;

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

export class MjComments extends MjElement {
  static tagName = "mj-comments";
  static styles = STYLES;
  static watched = [
    "current-user-id", "readonly", "max-depth", "max-visible-replies",
    "allow-reactions", "composer-position", "empty-message", "label"
  ];

  constructor() {
    super()
    this._comments = []
    this._dataSource = null
    this._mentionSource = null
    this._cursor = null
    this._timestampTimer = null
  }

  render() {
    const label = this.getAttribute("label") || "Comments"
    const composerPos = this.getAttribute("composer-position") || "bottom"

    const composerHtml = `
      <div class="composer-area" part="top-composer">
        <slot name="composer-header"></slot>
        <textarea class="composer-textarea" placeholder="Write a comment…"
                  aria-label="New comment"></textarea>
        <div class="composer-actions">
          <button class="composer-submit-btn" type="button"
                  aria-label="Post comment">Post</button>
        </div>
      </div>
    `

    const markup = `
      <div class="comments-root" role="feed" part="root"
           aria-label="${label}" aria-busy="false">
        ${composerPos === "top" ? composerHtml : ""}
        <h3 class="count-heading" part="count-heading">0 comments</h3>
        <div class="feed-list" part="feed-list"></div>
        <button class="load-older-btn" part="load-older" type="button" hidden>
          Load earlier comments
        </button>
        ${composerPos !== "top" ? composerHtml : ""}
      </div>
    `
    return markup
  }

  afterRender() {
    this._feedRoot = this.$(".comments-root")
    this._countHeading = this.$(".count-heading")
    this._feedList = this.$(".feed-list")
    this._loadOlderBtn = this.$(".load-older-btn")
    this._composerTextarea = this.$(".composer-textarea")
    this._composerSubmit = this.$(".composer-submit-btn")

    if (this._composerSubmit !== null) {
      this.listen(this._composerSubmit, "click", this._onTopLevelPost.bind(this))
    }
    if (this._composerTextarea !== null) {
      this.listen(this._composerTextarea, "keydown", this._onComposerKeydown.bind(this))
    }
    if (this._loadOlderBtn !== null) {
      this.listen(this._loadOlderBtn, "click", this._onLoadOlder.bind(this))
    }

    this._renderComments()
    this._startTimestampRefresh()
    return
  }

  onDisconnected() {
    if (this._timestampTimer !== null) {
      window.clearInterval(this._timestampTimer)
      this._timestampTimer = null
    }
    return
  }

  _onComposerKeydown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault()
      this._onTopLevelPost()
    }
    return
  }

  _onTopLevelPost() {
    if (this._composerTextarea === null) {
      return
    }
    const body = this._composerTextarea.value.trim()
    if (body.length === 0) {
      return
    }
    this.emit("mj-comment-post", { body: body, parentId: null, mentions: [] })
    this._composerTextarea.value = ""

    if (this._dataSource !== null && typeof this._dataSource.post === "function") {
      const promise = this._dataSource.post({ body: body, parentId: null })
      Promise.resolve(promise).then((comment) => {
        if (comment !== null && comment !== undefined) {
          this.addComment(comment)
        }
      }).catch(() => {})
    }
    return
  }

  _onLoadOlder() {
    this.emit("mj-load-older", { cursor: this._cursor })
    return
  }

  _renderComments() {
    if (this._feedList === null) {
      return
    }
    this._feedList.innerHTML = ""

    const emptyMsg = this.getAttribute("empty-message") || "Be the first to comment."
    const count = this._comments.length
    if (this._countHeading !== null) {
      this._countHeading.textContent = `${count} ${count === 1 ? "comment" : "comments"}`
    }

    if (count === 0) {
      this._feedList.innerHTML = `
        <div class="empty-state" part="empty-state">
          <slot name="empty">${emptyMsg}</slot>
        </div>
      `
      return
    }

    for (let i = 0; i < this._comments.length; i = i + 1) {
      const comment = this._comments[i]
      const articleEl = this._buildCommentEl(comment, null, 0, i)
      this._feedList.appendChild(articleEl)
    }
    return
  }

  _buildCommentEl(comment, parentId, depth, posInSet) {
    const headerId = nextId("mj-cmt-hdr")
    const article = document.createElement("article")
    article.className = "comment-article"
    article.setAttribute("part", "comment")
    article.setAttribute("aria-labelledby", headerId)
    article.setAttribute("aria-setsize", "-1")
    article.setAttribute("aria-posinset", String(posInSet + 1))
    article.setAttribute("data-comment-id", comment.id)

    const avatarHtml = comment.authorAvatar !== undefined && comment.authorAvatar !== null
      ? `<img src="${comment.authorAvatar}" alt="${comment.authorName || ""}"/>`
      : initials(comment.authorName || "?")

    const ts = comment.createdAt || ""
    const relTs = relativeTime(ts)
    const readonly = this.hasAttribute("readonly")
    const currentUserId = this.getAttribute("current-user-id") || ""
    const isOwn = currentUserId.length > 0 && comment.authorId === currentUserId
    const allowReactions = this.getAttribute("allow-reactions") !== "false"
    const maxDepth = parseInt(this.getAttribute("max-depth") || "3", 10)

    const editBtn = isOwn && !readonly ? `<button class="action-btn" data-action="edit" aria-label="Edit comment">Edit</button>` : ""
    const deleteBtn = isOwn && !readonly ? `<button class="action-btn" data-action="delete" aria-label="Delete comment">Delete</button>` : ""
    const replyBtn = !readonly && depth < maxDepth ? `<button class="action-btn" data-action="reply" aria-label="Reply to comment">Reply</button>` : ""

    const reactionsHtml = allowReactions && Array.isArray(comment.reactions) && comment.reactions.length > 0
      ? `<div class="reaction-bar" part="reaction-bar">
          ${comment.reactions.map((r) => {
            const active = Array.isArray(r.userIds) && currentUserId.length > 0 && r.userIds.indexOf(currentUserId) >= 0
            return `<button class="reaction-chip" aria-pressed="${active ? "true" : "false"}"
                             aria-label="React with ${r.emoji}, ${r.count} reactions"
                             data-emoji="${r.emoji}">${r.emoji} ${r.count}</button>`
          }).join("")}
        </div>`
      : ""

    const bodyText = comment.deleted === true ? "[Comment deleted]" : (comment.body || "")
    const bodyAttr = comment.deleted === true ? `data-deleted="true"` : ""

    article.innerHTML = `
      <div class="comment-avatar" aria-hidden="true">${avatarHtml}</div>
      <div class="comment-content">
        <header class="comment-header" id="${headerId}">
          <strong class="comment-author" part="comment-author">${this._escapeHtml(comment.authorName || "Unknown")}</strong>
          <time class="comment-time" part="comment-time" datetime="${ts}">${relTs}</time>
        </header>
        <div class="comment-body" part="comment-body" ${bodyAttr}>${this._escapeHtml(bodyText)}</div>
        ${reactionsHtml}
        <div class="comment-actions" part="comment-actions">
          ${replyBtn}
          ${editBtn}
          ${deleteBtn}
        </div>
      </div>
    `

    // Replies
    const maxVisible = parseInt(this.getAttribute("max-visible-replies") || "3", 10)
    const replies = comment.replies || []
    if (replies.length > 0 && depth < maxDepth) {
      const replyThread = document.createElement("div")
      replyThread.className = "reply-thread"
      replyThread.setAttribute("role", "group")
      replyThread.setAttribute("aria-label", `Replies to ${comment.authorName || "Unknown"}`)
      replyThread.setAttribute("part", "reply-thread")

      const visibleReplies = replies.slice(0, maxVisible)
      for (let i = 0; i < visibleReplies.length; i = i + 1) {
        const replyEl = this._buildCommentEl(visibleReplies[i], comment.id, depth + 1, i)
        replyThread.appendChild(replyEl)
      }

      if (replies.length > maxVisible) {
        const showMoreBtn = document.createElement("button")
        showMoreBtn.className = "show-more-replies-btn"
        showMoreBtn.textContent = `Show ${replies.length - maxVisible} more replies`
        this.listen(showMoreBtn, "click", () => {
          this.emit("mj-load-replies", { commentId: comment.id, cursor: null })
        })
        replyThread.appendChild(showMoreBtn)
      }

      // Wrap article + thread together
      const wrapper = document.createElement("div")
      wrapper.style.display = "contents"
      wrapper.appendChild(article)
      wrapper.appendChild(replyThread)
      this._wireArticleActions(article, comment, parentId, depth)
      return wrapper
    }

    this._wireArticleActions(article, comment, parentId, depth)
    return article
  }

  _wireArticleActions(article, comment, parentId, depth) {
    const actionBtns = article.querySelectorAll(".action-btn")
    for (let i = 0; i < actionBtns.length; i = i + 1) {
      const btn = actionBtns[i]
      const action = btn.getAttribute("data-action")
      if (action === "reply") {
        this.listen(btn, "click", () => this._openReplyComposer(article, comment))
      } else if (action === "edit") {
        this.listen(btn, "click", () => this._openEditComposer(article, comment))
      } else if (action === "delete") {
        this.listen(btn, "click", () => this._onDeleteComment(comment))
      }
    }

    const reactionChips = article.querySelectorAll(".reaction-chip")
    for (let i = 0; i < reactionChips.length; i = i + 1) {
      const chip = reactionChips[i]
      const emoji = chip.getAttribute("data-emoji")
      this.listen(chip, "click", () => {
        const active = chip.getAttribute("aria-pressed") === "true"
        this.emit("mj-comment-react", { commentId: comment.id, emoji: emoji, active: !active })
      })
    }
    return
  }

  _openReplyComposer(article, parentComment) {
    // Remove existing reply composers
    const existing = this._feedList.querySelector(".reply-composer")
    if (existing !== null) {
      existing.remove()
    }

    const composer = document.createElement("div")
    composer.className = "reply-composer composer-area"
    composer.setAttribute("part", "reply-composer")
    composer.innerHTML = `
      <textarea class="composer-textarea" placeholder="Write a reply…"
                aria-label="Reply to ${this._escapeHtml(parentComment.authorName || "comment")}"></textarea>
      <div class="composer-actions">
        <button type="button" class="action-btn cancel-reply-btn">Cancel</button>
        <button type="button" class="composer-submit-btn" aria-label="Post reply">Reply</button>
      </div>
    `

    const textarea = composer.querySelector(".composer-textarea")
    const submitBtn = composer.querySelector(".composer-submit-btn")
    const cancelBtn = composer.querySelector(".cancel-reply-btn")

    this.listen(submitBtn, "click", () => {
      const body = textarea.value.trim()
      if (body.length === 0) { return }
      this.emit("mj-comment-post", { body: body, parentId: parentComment.id, mentions: [] })
      composer.remove()
    })

    this.listen(cancelBtn, "click", () => { composer.remove() })

    this.listen(textarea, "keydown", (event) => {
      if (event.key === "Escape") {
        composer.remove()
      }
    })

    article.after(composer)
    textarea.focus()
    return
  }

  _openEditComposer(article, comment) {
    const bodyEl = article.querySelector(".comment-body")
    if (bodyEl === null) {
      return
    }
    const originalText = comment.body || ""
    bodyEl.innerHTML = `
      <textarea class="composer-textarea" aria-label="Edit comment"
                style="width:100%;box-sizing:border-box;">${this._escapeHtml(originalText)}</textarea>
      <div class="composer-actions" style="margin-top:var(--mj-space-1)">
        <button type="button" class="action-btn cancel-edit-btn">Cancel</button>
        <button type="button" class="composer-submit-btn" aria-label="Save edit">Save</button>
      </div>
    `
    const textarea = bodyEl.querySelector(".composer-textarea")
    const saveBtn = bodyEl.querySelector(".composer-submit-btn")
    const cancelBtn = bodyEl.querySelector(".cancel-edit-btn")

    this.listen(saveBtn, "click", () => {
      const body = textarea.value.trim()
      if (body.length === 0) { return }
      this.emit("mj-comment-edit", { commentId: comment.id, body: body })
      comment.body = body
      bodyEl.innerHTML = this._escapeHtml(body)
    })

    this.listen(cancelBtn, "click", () => {
      bodyEl.innerHTML = this._escapeHtml(originalText)
    })

    this.listen(textarea, "keydown", (event) => {
      if (event.key === "Escape") {
        bodyEl.innerHTML = this._escapeHtml(originalText)
      }
    })

    textarea.focus()
    return
  }

  _onDeleteComment(comment) {
    const confirmed = window.confirm("Delete this comment?")
    if (confirmed === true) {
      this.emit("mj-comment-delete", { commentId: comment.id })
      comment.deleted = true
      this._renderComments()
      announce("Comment deleted", "assertive")
    }
    return
  }

  _startTimestampRefresh() {
    this._timestampTimer = window.setInterval(() => {
      const timeEls = this._feedList.querySelectorAll("time.comment-time")
      for (let i = 0; i < timeEls.length; i = i + 1) {
        const el = timeEls[i]
        const ts = el.getAttribute("datetime")
        if (ts !== null && ts !== "") {
          el.textContent = relativeTime(ts)
        }
      }
    }, 60000)
    return
  }

  _escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
  }

  addComment(comment) {
    const composerPos = this.getAttribute("composer-position") || "bottom"
    if (composerPos === "bottom") {
      this._comments.push(comment)
    } else {
      this._comments.unshift(comment)
    }
    if (this._feedList !== null) {
      this._renderComments()
    }
    return
  }

  get comments() {
    return this._comments
  }

  set comments(value) {
    this._comments = Array.isArray(value) ? value : []
    if (this._feedList !== null) {
      this._renderComments()
    }
    return
  }

  get dataSource() {
    return this._dataSource
  }

  set dataSource(source) {
    this._dataSource = source
    return
  }

  get mentionSource() {
    return this._mentionSource
  }

  set mentionSource(source) {
    this._mentionSource = source
    return
  }
}
