/*
 * mjcomments.js
 *
 * <mj-comments> -- threaded comment section with replies, inline editing,
 * emoji reactions, relative timestamps, and APG Feed pattern.
 *
 * Replies nest up to `max-depth` levels below the top level. Replies deeper
 * than that are not dropped: they are shown in the deepest thread, after
 * the reply they answer, in thread order (with `max-depth="0"`, at the top
 * level). The count heading therefore counts every comment that can be
 * shown.
 *
 * The role="feed" list holds only the top-level comment articles: a
 * comment's replies (a role="group" thread of articles) sit inside the
 * comment's own <article>, so Page Down / Page Up move between top-level
 * comments and a reply is read as part of the comment it answers.
 *
 * `readonly` removes every write action: the composer, Reply, Edit, Delete
 * and the reaction controls (existing reactions are shown as plain counts).
 *
 * `addComment()` ignores a comment whose id is already in the thread.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";
import { html, safeUrl } from "../core/html.js";
import { formatDate, formatRelativeTime, t } from "../core/intl.js";

/* Emoji offered by the "add reaction" control. */
const REACTION_CHOICES = ["\u{1F44D}", "\u{2764}\u{FE0F}", "\u{1F604}", "\u{1F389}", "\u{1F62E}", "\u{1F622}"];

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

/* An empty feed that is not loading is taken out of the page (a feed holds articles). */
.feed-list[hidden] { display: none; }

/*
 * Avatar and content side by side; the comment's reply thread (inside the
 * article, see _appendComment) spans both columns below them.
 */
.comment-article {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  column-gap: var(--mj-space-3);
  align-items: start;
  position: relative;
}

.comment-article > .reply-thread {
  grid-column: 1 / -1;
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

/* Read-only: reactions are counts, not controls. */
span.reaction-chip { cursor: default; }

span.reaction-chip.is-mine {
  background: var(--mj-bg-muted);
  border-color: var(--mj-accent);
  color: var(--mj-accent);
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

.empty-state[hidden] { display: none; }

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
.load-older-btn[hidden] { display: none; }

.load-older-btn:focus-visible,
.show-more-replies-btn:focus-visible,
.retry-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.comment-article:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
  border-radius: var(--mj-radius-sm);
}

.comment-article .reply-composer {
  margin-inline-start: 0;
}

.comment-editor {
  display: flex;
  flex-direction: column;
  gap: var(--mj-space-1);
}

.composer-submit-btn[aria-disabled="true"] {
  opacity: 0.6;
  cursor: progress;
}

.composer-error {
  font-size: var(--mj-font-size-xs);
  color: var(--mj-color-danger);
}

.composer-error[hidden] { display: none; }

.feed-error {
  padding: var(--mj-space-3);
  border: 1px solid var(--mj-color-danger);
  border-radius: var(--mj-radius-md);
  background: var(--mj-color-danger-surface);
  color: var(--mj-text);
  font-size: var(--mj-font-size-sm);
  display: flex;
  gap: var(--mj-space-3);
  align-items: baseline;
}

.feed-error[hidden] { display: none; }

.retry-btn {
  background: none;
  border: none;
  padding: 0;
  font: inherit;
  color: var(--mj-accent);
  cursor: pointer;
}

.reaction-picker {
  display: inline-flex;
  gap: var(--mj-space-1);
}
`;

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

  if (value instanceof Date) {
    date = value
  } else if (typeof value === "number") {
    date = new Date(value)
  } else if (typeof value === "string" && value.length > 0) {
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

/*
 * Comment field readers. The documented shape is flat
 * ({ authorName, authorAvatar, createdAt }); a nested `author` object and a
 * `timestamp` field are read as well.
 */
function authorNameOf(comment) {
  let name = comment.authorName
  if ((name === undefined || name === null) && comment.author !== undefined && comment.author !== null) {
    name = comment.author.name
  }
  const text = name !== undefined && name !== null ? String(name) : ""
  return text
}

function authorAvatarOf(comment) {
  let url = comment.authorAvatar
  if ((url === undefined || url === null) && comment.author !== undefined && comment.author !== null) {
    url = comment.author.avatarUrl
  }
  const safe = url !== undefined && url !== null ? safeUrl(url, "") : ""
  return safe
}

function createdAtOf(comment) {
  const value = comment.createdAt !== undefined && comment.createdAt !== null ? comment.createdAt : comment.timestamp
  return value
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

    /* Cursor for the next page of earlier comments; null when there is none. */
    this._cursor = null
    this._loading = false
    this._loadFailed = false
    this._sourceLoaded = false
    this._fetchSequence = 0

    /* Ids (as strings) of comments whose replies are all shown. */
    this._expandedThreads = new Set()

    /* Editor state lives in fields so a re-render or reconnect keeps it. */
    this._editingId = null
    this._editDraft = ""
    this._replyingToId = null
    this._replyDraft = ""
    this._replyError = ""
    this._replyPosting = false
    this._composerDraft = ""
    this._composerError = ""
    this._posting = false
    this._reactionPickerFor = null
    this._deleteDialog = null

    this._rootEl = null
    this._countHeading = null
    this._feedList = null
    this._emptyEl = null
    this._loadOlderBtn = null
    this._errorEl = null
    this._composerEl = null
    this._composerTextarea = null
    this._composerSubmit = null
    this._composerErrorEl = null
  }

  render() {
    const markup = html`
      <div class="comments-root" part="root">
        <h3 class="count-heading" part="count-heading">${t("mj.comments.count", { count: 0 })}</h3>
        <button class="load-older-btn" part="load-older" type="button" hidden>
          ${t("mj.comments.loadEarlier")}
        </button>
        <div class="feed-list" role="feed" part="feed-list" aria-busy="false"></div>
        <div class="empty-state" part="empty-state" hidden><slot name="empty"></slot></div>
        <div class="feed-error" role="alert" hidden>
          <span>${t("mj.comments.loadError")}</span>
          <button class="retry-btn" type="button">${t("mj.comments.retry")}</button>
        </div>
        <div class="composer-area top-composer" part="top-composer">
          <slot name="composer-header"></slot>
          <textarea class="composer-textarea" placeholder="${t("mj.comments.placeholder")}"
                    aria-label="${t("mj.comments.newCommentLabel")}"></textarea>
          <div class="composer-error" role="alert" hidden></div>
          <div class="composer-actions">
            <button class="composer-submit-btn" type="button"
                    aria-label="${t("mj.comments.postCommentLabel")}">${t("mj.comments.post")}</button>
          </div>
        </div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._rootEl = this.$(".comments-root")
    this._countHeading = this.$(".count-heading")
    this._feedList = this.$(".feed-list")
    this._emptyEl = this.$(".empty-state")
    this._loadOlderBtn = this.$(".load-older-btn")
    this._errorEl = this.$(".feed-error")
    this._composerEl = this.$(".top-composer")
    this._composerTextarea = this._composerEl.querySelector(".composer-textarea")
    this._composerSubmit = this._composerEl.querySelector(".composer-submit-btn")
    this._composerErrorEl = this._composerEl.querySelector(".composer-error")

    this._feedList.setAttribute("aria-label", this.getAttribute("label") || t("mj.comments.label"))

    this.listen(this._composerSubmit, "click", this._onTopLevelPost.bind(this))
    this.listen(this._composerTextarea, "keydown", this._onComposerKeydown.bind(this))
    this.listen(this._composerTextarea, "input", this._onComposerInput.bind(this))
    this.listen(this._loadOlderBtn, "click", this._onLoadOlder.bind(this))
    this.listen(this.$(".retry-btn"), "click", this._onRetry.bind(this))

    /* One delegated listener per event type covers every comment. */
    this.listen(this._feedList, "click", this._onFeedClick.bind(this))
    this.listen(this._feedList, "input", this._onFeedInput.bind(this))
    this.listen(this._feedList, "keydown", this._onFeedKeydown.bind(this))

    this.onTeardown(() => {
      this._discardDeleteDialog()
    })

    /* Restore everything held in fields (drafts, pending state, errors). */
    this._composerTextarea.value = this._composerDraft
    this._syncComposerState()
    this._placeComposer()
    this._errorEl.hidden = this._loadFailed === false
    this._renderComments(null)
    this._startTimestampRefresh()

    if (this._dataSource !== null && this._sourceLoaded === false) {
      this._fetchComments(false)
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._feedList === undefined || this._feedList === null) {
      return
    }

    if (name === "label") {
      this._feedList.setAttribute("aria-label", newValue || t("mj.comments.label"))
    } else if (name === "composer-position") {
      this._placeComposer()
    } else if (name === "readonly") {
      if (newValue !== null) {
        /* Read-only shows no editors and no reaction picker. */
        this._editingId = null
        this._replyingToId = null
        this._reactionPickerFor = null
      }
      this._renderComments()
    } else if (
      name === "current-user-id" || name === "max-depth" || name === "max-visible-replies" ||
      name === "allow-reactions" || name === "empty-message"
    ) {
      this._renderComments()
    }
    return
  }

  /* ----- small helpers ----- */

  _composerPosition() {
    const position = this.getAttribute("composer-position") === "top" ? "top" : "bottom"
    return position
  }

  _positiveIntAttr(name, fallback) {
    const parsed = parseInt(this.getAttribute(name) || "", 10)
    const value = Number.isFinite(parsed) === true && parsed >= 0 ? parsed : fallback
    return value
  }

  /*
   * The comments from the top level down to the one with id `idKey`
   * (inclusive), or an empty list when it is not in the tree.
   */
  _pathTo(idKey) {
    let found = []

    const visit = (list, ancestors) => {
      for (let i = 0; i < list.length && found.length === 0; i = i + 1) {
        const comment = list[i]
        const path = ancestors.concat([comment])
        if (String(comment.id) === idKey) {
          found = path
        } else if (Array.isArray(comment.replies) === true) {
          visit(comment.replies, path)
        }
      }
      return
    }

    visit(this._comments, [])
    return found
  }

  /* The nesting level of a comment in the data (top level 0), or 0 when unknown. */
  _depthOf(idKey) {
    const path = this._pathTo(idKey)
    const depth = path.length > 0 ? path.length - 1 : 0
    return depth
  }

  /* Find a comment anywhere in the tree by its id (compared as strings). */
  _findComment(idKey) {
    let found = null

    const visit = (list, parent) => {
      for (let i = 0; i < list.length && found === null; i = i + 1) {
        const comment = list[i]
        if (String(comment.id) === idKey) {
          found = { comment: comment, parent: parent }
        } else if (Array.isArray(comment.replies) === true) {
          visit(comment.replies, comment)
        }
      }
      return
    }

    visit(this._comments, null)
    return found
  }

  /*
   * The comments shown at `depth`, in order: those of `list` and, from the
   * deepest nesting level on, the replies below each of them, flattened in
   * thread order (they get no thread of their own there).
   */
  _threadEntries(list, depth, maxDepth) {
    const entries = []

    const flatten = (comment) => {
      const replies = Array.isArray(comment.replies) === true ? comment.replies : []
      for (let i = 0; i < replies.length; i = i + 1) {
        entries.push(replies[i])
        flatten(replies[i])
      }
      return
    }

    for (let i = 0; i < list.length; i = i + 1) {
      entries.push(list[i])
      if (depth >= maxDepth) {
        flatten(list[i])
      }
    }
    return entries
  }

  /* Comments that are not tombstones, replies included. */
  _countComments(list) {
    let count = 0
    for (let i = 0; i < list.length; i = i + 1) {
      const comment = list[i]
      if (comment.deleted !== true) {
        count = count + 1
      }
      if (Array.isArray(comment.replies) === true) {
        count = count + this._countComments(comment.replies)
      }
    }
    return count
  }

  /*
   * The composer sits above the heading or after the list. Earlier comments
   * load at the end the oldest comment is on: above the list when new ones
   * are appended (composer at the bottom), below it otherwise.
   */
  _placeComposer() {
    const root = this._rootEl
    if (this._composerPosition() === "top") {
      root.appendChild(this._composerEl)
      root.appendChild(this._countHeading)
      root.appendChild(this._feedList)
      root.appendChild(this._errorEl)
      root.appendChild(this._loadOlderBtn)
    } else {
      root.appendChild(this._countHeading)
      root.appendChild(this._loadOlderBtn)
      root.appendChild(this._feedList)
      root.appendChild(this._errorEl)
      root.appendChild(this._composerEl)
    }
    return
  }

  /* ----- top-level composer ----- */

  _syncComposerState() {
    this._composerSubmit.setAttribute("aria-disabled", this._posting === true ? "true" : "false")
    this._composerTextarea.readOnly = this._posting
    this._composerEl.setAttribute("aria-busy", this._posting === true ? "true" : "false")
    this._composerErrorEl.textContent = this._composerError
    this._composerErrorEl.hidden = this._composerError.length === 0
    return
  }

  _onComposerInput() {
    this._composerDraft = this._composerTextarea.value
    return
  }

  _onComposerKeydown(event) {
    /* Enter that confirms an IME composition must not submit. */
    const composing = event.isComposing === true || event.keyCode === 229
    if (event.key === "Enter" && event.shiftKey === false && composing === false) {
      event.preventDefault()
      this._onTopLevelPost()
    }
    return
  }

  _onTopLevelPost() {
    if (this._composerTextarea === null || this._posting === true || this.hasAttribute("readonly") === true) {
      return
    }
    const body = this._composerTextarea.value.trim()
    if (body.length === 0) {
      return
    }
    this._submitComment(body, null)
    return
  }

  /*
   * Shared submit path for the top-level composer (parentComment null) and
   * the reply composer. The host always gets `mj-comment-post`. With a data
   * source the text is kept, and the composer held busy, until `post()`
   * settles: success clears the composer and inserts the returned comment,
   * failure shows an error and leaves the text in place.
   */
  _submitComment(body, parentComment) {
    const parentId = parentComment !== null ? parentComment.id : null
    this.emit("mj-comment-post", { body: body, parentId: parentId, mentions: [] })

    const canPost = this._dataSource !== null && typeof this._dataSource.post === "function"
    if (canPost === false) {
      this._finishPost(parentComment, null)
      return
    }

    this._setPosting(parentComment, true, "")

    let request = null
    try {
      request = Promise.resolve(this._dataSource.post({ body: body, parentId: parentId }))
    } catch (error) {
      request = Promise.reject(error)
    }

    request.then(
      (comment) => {
        this._setPosting(parentComment, false, "")
        this._finishPost(parentComment, comment)
      },
      (error) => {
        this._setPosting(parentComment, false, t("mj.comments.postError"))
        announce(t("mj.comments.postErrorAnnouncement"), "assertive")
      }
    )
    return
  }

  _setPosting(parentComment, pending, errorText) {
    if (parentComment === null) {
      this._posting = pending
      this._composerError = errorText
      if (this._composerTextarea !== null) {
        this._syncComposerState()
      }
    } else {
      this._replyPosting = pending
      this._replyError = errorText
      this._renderComments()
    }
    return
  }

  _finishPost(parentComment, comment) {
    const hasComment = comment !== null && comment !== undefined

    if (parentComment === null) {
      this._composerDraft = ""
      this._composerError = ""
      if (this._composerTextarea !== null) {
        this._composerTextarea.value = ""
        this._syncComposerState()
      }
      if (hasComment === true) {
        this.addComment(comment)
      }
    } else {
      const parentKey = String(parentComment.id)
      if (this._replyingToId === parentKey) {
        this._replyingToId = null
        this._replyDraft = ""
        this._replyError = ""
      }
      if (hasComment === true) {
        this._insertComment(comment, parentComment.id)
        this._renderComments({ commentId: String(comment.id), key: "article" })
      } else {
        this._renderComments({ commentId: parentKey, key: "reply" })
      }
    }
    return
  }

  /* ----- data source ----- */

  _canFetch() {
    const source = this._dataSource
    const able = source !== null && (typeof source.fetch === "function" || typeof source.query === "function")
    return able
  }

  _requestPage(cursor) {
    const source = this._dataSource
    let request = null
    try {
      if (typeof source.fetch === "function") {
        request = Promise.resolve(source.fetch({ cursor: cursor }))
      } else {
        request = Promise.resolve(source.query({ cursor: cursor }))
      }
    } catch (error) {
      request = Promise.reject(error)
    }
    return request
  }

  _setLoading(loading, failed) {
    this._loading = loading
    this._loadFailed = failed
    if (this._feedList !== null) {
      this._feedList.setAttribute("aria-busy", loading === true ? "true" : "false")
      this._feedList.hidden = this._comments.length === 0 && loading === false
      this._errorEl.hidden = failed === false
    }
    return
  }

  /*
   * Load comments from the data source: the first page (older false), or
   * the page of earlier comments the stored cursor points at.
   */
  _fetchComments(older) {
    if (this._canFetch() === false || this._feedList === null || this._loading === true) {
      return
    }

    this._fetchSequence = this._fetchSequence + 1
    const sequence = this._fetchSequence
    const cursor = older === true ? this._cursor : null
    this._setLoading(true, false)

    this._requestPage(cursor).then(
      (result) => {
        if (sequence === this._fetchSequence) {
          let items = []
          let nextCursor = null
          if (Array.isArray(result) === true) {
            items = result
          } else if (result !== null && result !== undefined) {
            if (Array.isArray(result.items) === true) {
              items = result.items
            } else if (Array.isArray(result.comments) === true) {
              items = result.comments
            }
            nextCursor = result.cursor !== undefined ? result.cursor : null
          }

          if (older === false) {
            this._comments = items
          } else if (this._composerPosition() === "top") {
            this._comments = this._comments.concat(items)
          } else {
            this._comments = items.concat(this._comments)
          }

          this._cursor = nextCursor
          this._sourceLoaded = true
          this._setLoading(false, false)
          this._renderComments()
        }
      },
      (error) => {
        if (sequence === this._fetchSequence) {
          this._setLoading(false, true)
          this._renderComments()
        }
      }
    )
    return
  }

  _onLoadOlder() {
    this.emit("mj-load-older", { cursor: this._cursor })
    if (this._canFetch() === true) {
      this._fetchComments(true)
    }
    return
  }

  _onRetry() {
    this._fetchComments(this._sourceLoaded)
    return
  }

  /* ----- rendering ----- */

  /*
   * Rebuild the comment list from the fields. `focusTarget` names the
   * control to focus afterwards ({ commentId, key }); when omitted, focus
   * is put back on whatever had it before the rebuild; null leaves focus alone.
   */
  _renderComments(focusTarget) {
    if (this._feedList === undefined || this._feedList === null) {
      return
    }

    const restore = focusTarget !== undefined ? focusTarget : this._captureFocus()
    const loadOlderHadFocus = this.shadowRoot.activeElement === this._loadOlderBtn

    this._feedList.textContent = ""

    const count = this._countComments(this._comments)
    this._countHeading.textContent = t("mj.comments.count", { count: count })
    this._loadOlderBtn.hidden = this._cursor === null || this._cursor === undefined

    /* The empty state is a sibling of the feed: a feed holds articles only. */
    this._emptyEl.querySelector("slot").textContent = this.getAttribute("empty-message") || t("mj.comments.empty")
    this._emptyEl.hidden = this._comments.length > 0 || this._loading === true || this._loadFailed === true
    this._feedList.hidden = this._comments.length === 0 && this._loading === false

    const maxDepth = this._positiveIntAttr("max-depth", 3)
    const topLevel = this._threadEntries(this._comments, 0, maxDepth)
    for (let i = 0; i < topLevel.length; i = i + 1) {
      this._appendComment(this._feedList, topLevel[i], 0, i)
    }

    this._restoreFocus(restore)

    if (loadOlderHadFocus === true && this._loadOlderBtn.hidden === true) {
      const firstArticle = this._feedList.querySelector("article")
      if (firstArticle !== null) {
        firstArticle.focus()
      }
    }
    return
  }

  /*
   * Append a comment's article to `container`. Its reply thread goes inside
   * the article: the feed (and a thread) holds articles only.
   */
  _appendComment(container, comment, depth, posInSet) {
    const idKey = String(comment.id)
    const headerId = nextId("mj-cmt-hdr")
    const authorName = authorNameOf(comment)
    const deleted = comment.deleted === true
    const readonly = this.hasAttribute("readonly")
    const currentUserId = this.getAttribute("current-user-id") || ""
    const isOwn = currentUserId.length > 0 && String(comment.authorId) === currentUserId
    const allowReactions = this.getAttribute("allow-reactions") !== "false"
    const maxDepth = this._positiveIntAttr("max-depth", 3)
    const canWrite = readonly === false && deleted === false
    const editing = canWrite === true && this._editingId === idKey
    const replying = canWrite === true && this._replyingToId === idKey

    const article = document.createElement("article")
    article.className = "comment-article"
    article.setAttribute("part", "comment")
    article.setAttribute("tabindex", "0")
    article.setAttribute("aria-labelledby", headerId)
    article.setAttribute("aria-setsize", "-1")
    article.setAttribute("aria-posinset", String(posInSet + 1))
    article.setAttribute("data-comment-id", idKey)

    const avatarUrl = authorAvatarOf(comment)
    const avatar = avatarUrl.length > 0
      ? html`<img src="${avatarUrl}" alt="">`
      : initials(authorName)

    let bodyBlock = null
    if (deleted === true) {
      bodyBlock = html`<div class="comment-body" part="comment-body" data-deleted="true">${t("mj.comments.deletedPlaceholder")}</div>`
    } else if (editing === true) {
      bodyBlock = html`
        <div class="comment-editor">
          <textarea class="composer-textarea edit-textarea" aria-label="${t("mj.comments.editCommentLabel")}" data-focus-key="editor"></textarea>
          <div class="composer-actions">
            <button type="button" class="action-btn" data-action="cancel-edit" data-focus-key="cancel-edit">${t("mj.comments.cancel")}</button>
            <button type="button" class="composer-submit-btn" data-action="save-edit" data-focus-key="save-edit"
                    aria-label="${t("mj.comments.saveEditLabel")}">${t("mj.comments.save")}</button>
          </div>
        </div>
      `
    } else {
      bodyBlock = html`<div class="comment-body" part="comment-body">${comment.body || ""}</div>`
    }

    let reactionBlock = ""
    if (allowReactions === true && deleted === false && readonly === true) {
      /* Read-only: the counts are shown, nothing can be toggled or added. */
      const reactions = Array.isArray(comment.reactions) === true ? comment.reactions : []
      if (reactions.length > 0) {
        reactionBlock = html`
          <div class="reaction-bar" part="reaction-bar">
            ${reactions.map((reaction) => {
              const userIds = Array.isArray(reaction.userIds) === true ? reaction.userIds.map((userId) => String(userId)) : []
              const mine = currentUserId.length > 0 && userIds.indexOf(currentUserId) >= 0
              return html`<span class="reaction-chip${mine === true ? " is-mine" : ""}">${reaction.emoji} ${reaction.count}</span>`
            })}
          </div>
        `
      }
    } else if (allowReactions === true && deleted === false) {
      const reactions = Array.isArray(comment.reactions) === true ? comment.reactions : []
      const pickerOpen = this._reactionPickerFor === idKey
      reactionBlock = html`
        <div class="reaction-bar" part="reaction-bar">
          ${reactions.map((reaction) => {
            const userIds = Array.isArray(reaction.userIds) === true ? reaction.userIds.map((userId) => String(userId)) : []
            const active = currentUserId.length > 0 && userIds.indexOf(currentUserId) >= 0
            return html`
              <button class="reaction-chip" type="button" data-action="react"
                      aria-pressed="${active === true ? "true" : "false"}"
                      aria-label="${t("mj.comments.reactionChipLabel", { emoji: reaction.emoji, count: reaction.count })}"
                      data-emoji="${reaction.emoji}" data-focus-key="react:${reaction.emoji}">${reaction.emoji} ${reaction.count}</button>
            `
          })}
          <button class="reaction-chip add-reaction-btn" type="button" data-action="toggle-reaction-picker"
                  data-focus-key="add-reaction" aria-label="${t("mj.comments.addReaction")}"
                  aria-expanded="${pickerOpen === true ? "true" : "false"}">+</button>
          ${pickerOpen === true ? html`
            <span class="reaction-picker" role="group" aria-label="${t("mj.comments.chooseReaction")}">
              ${REACTION_CHOICES.map((emoji) => html`
                <button class="reaction-chip" type="button" data-action="pick-reaction"
                        data-emoji="${emoji}" data-focus-key="pick:${emoji}"
                        aria-label="${t("mj.comments.reactWith", { emoji: emoji })}">${emoji}</button>
              `)}
            </span>
          ` : ""}
        </div>
      `
    }

    let actionBlock = ""
    if (canWrite === true) {
      const showReply = depth < maxDepth
      actionBlock = html`
        <div class="comment-actions" part="comment-actions">
          ${showReply === true ? html`<button class="action-btn" type="button" data-action="reply" data-focus-key="reply" aria-label="${t("mj.comments.replyToComment")}">${t("mj.comments.reply")}</button>` : ""}
          ${isOwn === true ? html`<button class="action-btn" type="button" data-action="edit" data-focus-key="edit" aria-label="${t("mj.comments.editCommentLabel")}">${t("mj.comments.edit")}</button>` : ""}
          ${isOwn === true ? html`<button class="action-btn" type="button" data-action="delete" data-focus-key="delete" aria-label="${t("mj.comments.deleteCommentLabel")}">${t("mj.comments.delete")}</button>` : ""}
        </div>
      `
    }

    const replyBlock = replying === true
      ? html`
          <div class="reply-composer composer-area" part="reply-composer">
            <textarea class="composer-textarea reply-textarea" placeholder="${t("mj.comments.replyPlaceholder")}"
                      aria-label="${t("mj.comments.replyToAuthor", { name: authorName.length > 0 ? authorName : t("mj.comments.replyTargetFallback") })}"
                      data-focus-key="reply-editor"></textarea>
            <div class="composer-error" role="alert" hidden></div>
            <div class="composer-actions">
              <button type="button" class="action-btn" data-action="cancel-reply" data-focus-key="cancel-reply">${t("mj.comments.cancel")}</button>
              <button type="button" class="composer-submit-btn" data-action="post-reply" data-focus-key="post-reply"
                      aria-label="${t("mj.comments.postReplyLabel")}">${t("mj.comments.reply")}</button>
            </div>
          </div>
        `
      : ""

    article.innerHTML = String(html`
      <div class="comment-avatar" aria-hidden="true">${avatar}</div>
      <div class="comment-content">
        <header class="comment-header" part="comment-header" id="${headerId}">
          <strong class="comment-author" part="comment-author">${authorName.length > 0 ? authorName : t("mj.comments.unknownAuthor")}</strong>
        </header>
        ${bodyBlock}
        ${reactionBlock}
        ${actionBlock}
        ${replyBlock}
      </div>
    `)

    const createdAt = createdAtOf(comment)
    if (createdAt !== undefined && createdAt !== null && createdAt !== "") {
      const timeEl = document.createElement("time")
      timeEl.className = "comment-time"
      timeEl.setAttribute("part", "comment-time")
      const date = parseTimestamp(createdAt)
      if (date !== null) {
        timeEl.setAttribute("datetime", date.toISOString())
        timeEl.setAttribute("title", formatDate(date, { dateStyle: "medium", timeStyle: "short" }))
        timeEl.textContent = relativeTime(date)
      } else {
        timeEl.textContent = String(createdAt)
      }
      article.querySelector(".comment-header").appendChild(timeEl)
    }

    if (editing === true) {
      article.querySelector(".edit-textarea").value = this._editDraft
    }
    if (replying === true) {
      const replyTextarea = article.querySelector(".reply-textarea")
      const replyErrorEl = article.querySelector(".composer-error")
      replyTextarea.value = this._replyDraft
      replyTextarea.readOnly = this._replyPosting
      replyErrorEl.textContent = this._replyError
      replyErrorEl.hidden = this._replyError.length === 0
      article.querySelector("[data-action='post-reply']").setAttribute(
        "aria-disabled", this._replyPosting === true ? "true" : "false"
      )
    }

    container.appendChild(article)

    /*
     * Replies. `replyCount` may announce more replies than are loaded. At
     * the deepest level the thread also carries the deeper replies,
     * flattened (see `_threadEntries`).
     */
    const replies = Array.isArray(comment.replies) === true ? comment.replies : []
    const threadReplies = depth < maxDepth ? this._threadEntries(replies, depth + 1, maxDepth) : []
    const announcedCount = Number(comment.replyCount)
    const unloadedReplies = Number.isFinite(announcedCount) === true ? Math.max(0, announcedCount - replies.length) : 0
    const totalReplies = threadReplies.length + unloadedReplies

    if (totalReplies > 0 && depth < maxDepth) {
      const maxVisible = this._positiveIntAttr("max-visible-replies", 3)
      const expanded = this._expandedThreads.has(idKey)
      const visibleReplies = expanded === true ? threadReplies : threadReplies.slice(0, maxVisible)

      const replyThread = document.createElement("div")
      replyThread.className = "reply-thread"
      replyThread.setAttribute("role", "group")
      replyThread.setAttribute("aria-label", t("mj.comments.repliesTo", { name: authorName.length > 0 ? authorName : t("mj.comments.unknownAuthor") }))
      replyThread.setAttribute("part", "reply-thread")

      for (let i = 0; i < visibleReplies.length; i = i + 1) {
        this._appendComment(replyThread, visibleReplies[i], depth + 1, i)
      }

      const remaining = totalReplies - visibleReplies.length
      if (remaining > 0) {
        const showMoreBtn = document.createElement("button")
        showMoreBtn.className = "show-more-replies-btn"
        showMoreBtn.type = "button"
        showMoreBtn.setAttribute("part", "load-more-replies")
        showMoreBtn.setAttribute("data-action", "show-replies")
        showMoreBtn.setAttribute("data-focus-key", "show-replies")
        showMoreBtn.setAttribute("data-comment-id", idKey)
        showMoreBtn.textContent = t("mj.comments.showMoreReplies", { count: remaining })
        replyThread.appendChild(showMoreBtn)
      }

      article.appendChild(replyThread)
    }
    return
  }

  /* ----- focus bookkeeping across re-renders ----- */

  /* Describe the focused control inside the list as { commentId, key }. */
  _captureFocus() {
    let descriptor = null
    const active = this.shadowRoot.activeElement

    if (active !== null && this._feedList.contains(active) === true) {
      const owner = active.closest("[data-comment-id]")
      if (owner !== null) {
        const isArticle = active === owner && active.localName === "article"
        descriptor = {
          commentId: owner.getAttribute("data-comment-id"),
          key: isArticle === true ? "article" : active.getAttribute("data-focus-key")
        }
        if (active.localName === "textarea") {
          descriptor.selectionStart = active.selectionStart
          descriptor.selectionEnd = active.selectionEnd
        }
      }
    }
    return descriptor
  }

  /* Focus the control a descriptor names; fall back to the comment itself. */
  _restoreFocus(descriptor) {
    if (descriptor === null || descriptor === undefined) {
      return
    }

    const owners = this._feedList.querySelectorAll("[data-comment-id]")
    let article = null
    let target = null

    for (let i = 0; i < owners.length && target === null; i = i + 1) {
      const owner = owners[i]
      if (owner.getAttribute("data-comment-id") === descriptor.commentId) {
        if (owner.localName === "article") {
          article = owner
        }
        if (owner.getAttribute("data-focus-key") === descriptor.key) {
          target = owner
        } else if (descriptor.key !== "article" && descriptor.key !== null) {
          /* The comment's own controls, not those of the replies nested in its article. */
          const candidates = owner.querySelectorAll("[data-focus-key]")
          for (let j = 0; j < candidates.length && target === null; j = j + 1) {
            const candidate = candidates[j]
            const ownControl = candidate.closest("[data-comment-id]") === owner
            if (ownControl === true && candidate.getAttribute("data-focus-key") === descriptor.key) {
              target = candidate
            }
          }
        }
      }
    }

    if (target === null) {
      target = article
    }

    if (target !== null) {
      target.focus()
      if (target.localName === "textarea") {
        const end = target.value.length
        const start = descriptor.selectionStart !== undefined ? descriptor.selectionStart : end
        const finish = descriptor.selectionEnd !== undefined ? descriptor.selectionEnd : end
        target.setSelectionRange(start, finish)
      }
    }
    return
  }

  /* ----- delegated list events ----- */

  _onFeedClick(event) {
    const control = event.target.closest("[data-action]")
    if (control === null || this._feedList.contains(control) === false) {
      return
    }
    const owner = control.closest("[data-comment-id]")
    if (owner === null) {
      return
    }
    const idKey = owner.getAttribute("data-comment-id")
    const found = this._findComment(idKey)
    if (found === null) {
      return
    }

    this._runAction(control.getAttribute("data-action"), found.comment, idKey, control)
    return
  }

  _runAction(action, comment, idKey, control) {
    const reactionAction = action === "react" || action === "toggle-reaction-picker" || action === "pick-reaction"
    if (reactionAction === true && this.hasAttribute("readonly") === true) {
      return
    }

    if (action === "reply") {
      if (this._replyPosting === false) {
        this._replyingToId = idKey
        this._replyDraft = ""
        this._replyError = ""
        this._renderComments({ commentId: idKey, key: "reply-editor" })
      }
    } else if (action === "cancel-reply") {
      if (this._replyPosting === false) {
        this._replyingToId = null
        this._replyDraft = ""
        this._replyError = ""
        this._renderComments({ commentId: idKey, key: "reply" })
      }
    } else if (action === "post-reply") {
      const body = this._replyDraft.trim()
      if (body.length > 0 && this._replyPosting === false) {
        this._submitComment(body, comment)
      }
    } else if (action === "edit") {
      this._editingId = idKey
      this._editDraft = comment.body || ""
      this._renderComments({ commentId: idKey, key: "editor" })
    } else if (action === "cancel-edit") {
      this._editingId = null
      this._editDraft = ""
      this._renderComments({ commentId: idKey, key: "edit" })
    } else if (action === "save-edit") {
      const body = this._editDraft.trim()
      if (body.length > 0) {
        this.emit("mj-comment-edit", { commentId: comment.id, body: body })
        comment.body = body
        this._editingId = null
        this._editDraft = ""
        this._renderComments({ commentId: idKey, key: "edit" })
        announce(t("mj.comments.updated"), "polite")
      }
    } else if (action === "delete") {
      this._requestDelete(comment, idKey)
    } else if (action === "react") {
      const active = control.getAttribute("aria-pressed") === "true"
      this.emit("mj-comment-react", {
        commentId: comment.id,
        emoji: control.getAttribute("data-emoji"),
        active: active === false
      })
    } else if (action === "toggle-reaction-picker") {
      const opening = this._reactionPickerFor !== idKey
      this._reactionPickerFor = opening === true ? idKey : null
      this._renderComments({
        commentId: idKey,
        key: opening === true ? `pick:${REACTION_CHOICES[0]}` : "add-reaction"
      })
    } else if (action === "pick-reaction") {
      this._reactionPickerFor = null
      this.emit("mj-comment-react", {
        commentId: comment.id,
        emoji: control.getAttribute("data-emoji"),
        active: true
      })
      this._renderComments({ commentId: idKey, key: "add-reaction" })
    } else if (action === "show-replies") {
      this._showReplies(comment, idKey)
    }
    return
  }

  /*
   * "Show N more replies": reveal every reply already in the data, and ask
   * the host for more only when `replyCount` says some are not loaded yet.
   */
  _showReplies(comment, idKey) {
    const ownReplies = Array.isArray(comment.replies) === true ? comment.replies : []
    const depth = this._depthOf(idKey)
    const maxDepth = this._positiveIntAttr("max-depth", 3)
    const replies = this._threadEntries(ownReplies, depth + 1, maxDepth)
    const maxVisible = this._positiveIntAttr("max-visible-replies", 3)
    const wasExpanded = this._expandedThreads.has(idKey)
    const announcedCount = Number(comment.replyCount)
    const unloaded = Number.isFinite(announcedCount) === true && announcedCount > ownReplies.length

    if (wasExpanded === false && replies.length > maxVisible) {
      this._expandedThreads.add(idKey)
      /* Focus the first reply that was hidden until now. */
      this._renderComments({ commentId: String(replies[maxVisible].id), key: "article" })
    } else {
      this._expandedThreads.add(idKey)
    }

    if (unloaded === true) {
      const cursor = comment.repliesCursor !== undefined ? comment.repliesCursor : null
      this.emit("mj-load-replies", { commentId: comment.id, cursor: cursor })
    }
    return
  }

  _onFeedInput(event) {
    const target = event.target
    if (target.classList.contains("edit-textarea") === true) {
      this._editDraft = target.value
    } else if (target.classList.contains("reply-textarea") === true) {
      this._replyDraft = target.value
    }
    return
  }

  _onFeedKeydown(event) {
    const target = event.target
    const isTextarea = target.localName === "textarea"
    const composing = event.isComposing === true || event.keyCode === 229

    if (isTextarea === true) {
      const owner = target.closest("[data-comment-id]")
      const idKey = owner !== null ? owner.getAttribute("data-comment-id") : null
      const found = idKey !== null ? this._findComment(idKey) : null
      const isEdit = target.classList.contains("edit-textarea")

      if (found !== null && event.key === "Escape") {
        event.preventDefault()
        event.stopPropagation()
        this._runAction(isEdit === true ? "cancel-edit" : "cancel-reply", found.comment, idKey, target)
      } else if (found !== null && event.key === "Enter" && event.shiftKey === false && composing === false) {
        event.preventDefault()
        this._runAction(isEdit === true ? "save-edit" : "post-reply", found.comment, idKey, target)
      }
      return
    }

    if (event.key === "Escape" && this._reactionPickerFor !== null && target.closest(".reaction-bar") !== null) {
      const idKey = this._reactionPickerFor
      event.preventDefault()
      event.stopPropagation()
      this._reactionPickerFor = null
      this._renderComments({ commentId: idKey, key: "add-reaction" })
      return
    }

    if (event.key === "PageDown" || event.key === "PageUp") {
      this._moveBetweenTopLevel(event)
    }
    return
  }

  /*
   * APG feed keys: Page Down / Page Up move between top-level comments, the
   * articles of the feed (a reply is inside the article it belongs to).
   * The key is consumed only when focus actually moves.
   */
  _moveBetweenTopLevel(event) {
    const active = this.shadowRoot.activeElement
    const topLevel = Array.from(this._feedList.children).filter((child) => child.localName === "article")
    let currentIndex = -1

    for (let i = 0; i < topLevel.length; i = i + 1) {
      if (active !== null && topLevel[i].contains(active) === true) {
        currentIndex = i
      }
    }

    const targetIndex = event.key === "PageDown" ? currentIndex + 1 : currentIndex - 1
    if (targetIndex >= 0 && targetIndex < topLevel.length) {
      event.preventDefault()
      topLevel[targetIndex].focus()
    }
    return
  }

  /* ----- delete ----- */

  /*
   * Ask for confirmation in an <mj-dialog>. The dialog is appended to the
   * document body: its backdrop makes every other body child inert, which
   * would include a dialog nested in this component's shadow tree.
   */
  _requestDelete(comment, idKey) {
    if (this._deleteDialog !== null) {
      return
    }

    if (customElements.get("mj-dialog") === undefined) {
      /* Used standalone, without the dialog component registered. */
      if (window.confirm(t("mj.comments.deleteConfirm")) === true) {
        this._deleteComment(comment, idKey)
      }
      return
    }

    const dialog = document.createElement("mj-dialog")
    dialog.setAttribute("variant", "confirmation")
    dialog.setAttribute("label", t("mj.comments.deleteCommentLabel"))
    dialog.setAttribute("confirm-label", t("mj.comments.delete"))
    const message = document.createElement("p")
    message.textContent = t("mj.comments.deleteConfirm")
    dialog.appendChild(message)

    let confirmed = false
    dialog.addEventListener("mj-dialog-confirm", () => {
      confirmed = true
    })
    dialog.addEventListener("mj-dialog-close", () => {
      this._discardDeleteDialog()
      /*
       * The backdrop releases the page (it clears `inert`) only after this
       * event, and an inert element cannot take focus, so focus is restored
       * in the next task.
       */
      window.setTimeout(() => {
        if (confirmed === true) {
          this._deleteComment(comment, idKey)
        } else {
          this._restoreFocus({ commentId: idKey, key: "delete" })
        }
      }, 0)
    })

    this._deleteDialog = dialog
    document.body.appendChild(dialog)
    dialog.returnFocusEl = this.shadowRoot.activeElement
    dialog.setAttribute("open", "")
    return
  }

  _discardDeleteDialog() {
    if (this._deleteDialog !== null) {
      this._deleteDialog.remove()
      this._deleteDialog = null
    }
    return
  }

  _deleteComment(comment, idKey) {
    this.emit("mj-comment-delete", { commentId: comment.id })
    comment.deleted = true
    if (this._editingId === idKey) {
      this._editingId = null
    }
    if (this._replyingToId === idKey) {
      this._replyingToId = null
    }
    /* The buttons are gone; the tombstoned comment itself takes focus. */
    this._renderComments({ commentId: idKey, key: "article" })
    announce(t("mj.comments.deleted"), "assertive")
    return
  }

  /* ----- timestamps ----- */

  _startTimestampRefresh() {
    const timer = window.setInterval(() => {
      const timeEls = this._feedList.querySelectorAll("time.comment-time[datetime]")
      for (let i = 0; i < timeEls.length; i = i + 1) {
        const date = parseTimestamp(timeEls[i].getAttribute("datetime"))
        if (date !== null) {
          timeEls[i].textContent = relativeTime(date)
        }
      }
    }, 60000)
    this.onTeardown(() => {
      window.clearInterval(timer)
    })
    return
  }

  /* ----- public API ----- */

  /* Put a comment into the tree without re-rendering. */
  _insertComment(comment, parentId) {
    let targetParentId = parentId
    if (targetParentId === undefined || targetParentId === null) {
      targetParentId = comment.parentId
    }

    let inserted = false
    if (targetParentId !== undefined && targetParentId !== null) {
      const found = this._findComment(String(targetParentId))
      if (found !== null) {
        if (Array.isArray(found.comment.replies) === false) {
          found.comment.replies = []
        }
        found.comment.replies.push(comment)
        /*
         * Show the whole thread so the new reply is not hidden behind "Show
         * more" -- every thread up to the top, since below `max-depth` the
         * reply is shown in an ancestor's thread.
         */
        const path = this._pathTo(String(targetParentId))
        for (let i = 0; i < path.length; i = i + 1) {
          this._expandedThreads.add(String(path[i].id))
        }
        inserted = true
      }
    }

    if (inserted === false) {
      if (this._composerPosition() === "bottom") {
        this._comments.push(comment)
      } else {
        this._comments.unshift(comment)
      }
    }
    return
  }

  /*
   * Add a comment in real time. With `parentId` (or `comment.parentId`) it
   * becomes a reply under that comment; otherwise it joins the top level at
   * the composer's end of the list.
   */
  addComment(comment, parentId) {
    if (comment === null || comment === undefined) {
      return
    }

    /* A comment that is already in the thread (a repeated realtime push, say) is not added twice. */
    if (comment.id !== undefined && comment.id !== null && this._findComment(String(comment.id)) !== null) {
      console.warn(`mj-comments: ignoring comment with duplicate id "${comment.id}"`)
      return
    }

    this._insertComment(comment, parentId)
    this._renderComments()
    return
  }

  get comments() {
    return this._comments
  }

  set comments(value) {
    this._comments = Array.isArray(value) ? value : []
    this._renderComments()
    return
  }

  get dataSource() {
    return this._dataSource
  }

  set dataSource(source) {
    this._dataSource = source !== undefined ? source : null
    this._sourceLoaded = false
    this._loading = false
    if (this._dataSource !== null) {
      this._fetchComments(false)
    }
    return
  }

  /*
   * Cursor for earlier comments. The "Load earlier comments" button shows
   * while it is not null. A data source maintains it; a host that pages by
   * itself (through `mj-load-older`) assigns it.
   */
  get cursor() {
    return this._cursor
  }

  set cursor(value) {
    this._cursor = value !== undefined ? value : null
    if (this._loadOlderBtn !== null) {
      this._loadOlderBtn.hidden = this._cursor === null
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
}
