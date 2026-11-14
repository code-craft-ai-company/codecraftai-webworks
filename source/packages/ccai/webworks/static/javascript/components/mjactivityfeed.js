/*
 * mjactivityfeed.js
 *
 * <mj-activity-feed> -- chronological stream of activity events with
 * APG Feed pattern (role="feed"), real-time prepend, load-older, and
 * relative timestamp refresh.
 *
 * The feed element holds articles only: a day heading (`group-by="date"`)
 * is shown between them but hidden from assistive technology and describes
 * the first article of its day instead, and the empty state sits outside
 * the feed.
 *
 * Paging: "Load older activity" is offered while `hasMore` is true. A
 * dataSource maintains it from its cursor; without one it starts false and
 * the host that answers `mj-load-older` sets it. Until the host answers
 * (assigns `items` or `hasMore`) the feed is busy and does not ask again.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";
import { html, safeUrl } from "../core/html.js";
import { formatDate, formatRelativeTime, t } from "../core/intl.js";

const STYLES = `
:host {
  display: block;
}

.feed-root {
  display: flex;
  flex-direction: column;
  gap: 0;
  position: relative;
}

.new-banner {
  font: inherit;
  width: 100%;
  position: sticky;
  top: 0;
  z-index: var(--mj-layer-sticky);
  background: var(--mj-feed-new-banner-bg, var(--mj-bg-muted));
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-md);
  padding: var(--mj-space-2) var(--mj-space-4);
  text-align: center;
  cursor: pointer;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-accent);
  margin-bottom: var(--mj-space-2);
}

.new-banner[hidden] { display: none; }

.feed-list {
  display: flex;
  flex-direction: column;
  gap: var(--mj-feed-gap, var(--mj-space-4));
}

/* An empty feed that is not loading is taken out of the page (a feed holds articles). */
.feed-list[hidden] { display: none; }

.activity-item {
  display: flex;
  gap: var(--mj-space-3);
  align-items: flex-start;
  position: relative;
}

.activity-item::before {
  content: "";
  position: absolute;
  inset-inline-start: calc(var(--mj-feed-avatar-size, 32px) / 2);
  top: calc(var(--mj-feed-avatar-size, 32px) + var(--mj-space-1));
  bottom: calc(-1 * var(--mj-feed-gap, var(--mj-space-4)));
  width: var(--mj-feed-line-width, 2px);
  background: var(--mj-feed-line-color, var(--mj-border));
}

.activity-item:last-child::before {
  display: none;
}

.activity-item:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
  border-radius: var(--mj-radius-sm);
}

.item-avatar {
  width: var(--mj-feed-avatar-size, 32px);
  height: var(--mj-feed-avatar-size, 32px);
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

.item-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.item-content {
  flex: 1;
  min-width: 0;
}

.item-header {
  display: flex;
  align-items: baseline;
  gap: var(--mj-space-2);
  flex-wrap: wrap;
  margin-bottom: var(--mj-space-1);
}

.item-actor {
  font-weight: var(--mj-font-weight-medium);
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
}

.item-action-text {
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
}

.item-timestamp {
  font-size: var(--mj-font-size-xs);
  color: var(--mj-feed-timestamp-color, var(--mj-text-muted));
  margin-inline-start: auto;
  white-space: nowrap;
}

.item-body {
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text-muted);
  margin-top: var(--mj-space-1);
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-body.is-expanded {
  display: block;
  -webkit-line-clamp: unset;
  overflow: visible;
}

.body-toggle,
.item-action-btn,
.retry-btn {
  background: none;
  border: none;
  padding: 0;
  font: inherit;
  font-size: var(--mj-font-size-xs);
  color: var(--mj-accent);
  cursor: pointer;
}

.body-toggle {
  margin-top: var(--mj-space-1);
}

.body-toggle[hidden] { display: none; }

.body-toggle:focus-visible,
.item-action-btn:focus-visible,
.retry-btn:focus-visible,
.new-banner:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
  border-radius: var(--mj-radius-sm);
}

.item-actions {
  display: flex;
  gap: var(--mj-space-2);
  margin-top: var(--mj-space-2);
}

.feed-error {
  margin-top: var(--mj-space-3);
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

:host([compact]) .feed-list {
  gap: var(--mj-feed-gap, var(--mj-space-2));
}

:host([compact]) .item-avatar {
  width: var(--mj-feed-avatar-size, 20px);
  height: var(--mj-feed-avatar-size, 20px);
  font-size: 0.625rem;
}

:host([compact]) .activity-item::before {
  inset-inline-start: calc(var(--mj-feed-avatar-size, 20px) / 2);
  top: calc(var(--mj-feed-avatar-size, 20px) + var(--mj-space-1));
  bottom: calc(-1 * var(--mj-feed-gap, var(--mj-space-2)));
}

:host([compact]) .item-header {
  flex-wrap: nowrap;
  margin-bottom: 0;
}

:host([compact]) .item-action-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

:host([compact]) .item-body,
:host([compact]) .body-toggle,
:host([compact]) .item-actions {
  display: none;
}

.group-heading {
  font-size: var(--mj-font-size-xs);
  font-weight: var(--mj-font-weight-medium);
  color: var(--mj-text-muted);
  padding: var(--mj-space-2) 0 var(--mj-space-1);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.load-more {
  display: block;
  width: 100%;
  margin-top: var(--mj-space-4);
  padding: var(--mj-space-3);
  background: var(--mj-surface);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-md);
  font: inherit;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
  cursor: pointer;
  text-align: center;
}

.load-more:hover { background: var(--mj-bg-muted); }
.load-more:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}

.load-more[hidden] { display: none; }
.load-more[aria-disabled="true"] { cursor: progress; opacity: 0.6; }

.empty-state[hidden] { display: none; }

.empty-state {
  padding: var(--mj-space-6);
  text-align: center;
  color: var(--mj-text-muted);
  font-size: var(--mj-font-size-sm);
}

.skeleton {
  background: linear-gradient(90deg, var(--mj-bg-muted) 25%, var(--mj-bg-subtle) 50%, var(--mj-bg-muted) 75%);
  background-size: 200% 100%;
  animation: mj-shimmer var(--mj-motion-slow) ease-in-out infinite;
  border-radius: var(--mj-radius-sm);
}

@keyframes mj-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
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

function absoluteTime(date) {
  const text = formatDate(date, { dateStyle: "medium", timeStyle: "short" })
  return text
}

/* The text and tooltip a timestamp shows for a `timestamp-format` value. */
function describeTimestamp(date, format) {
  const relative = relativeTime(date)
  const absolute = absoluteTime(date)
  let description = { text: relative, title: absolute }

  if (format === "absolute") {
    description = { text: absolute, title: "" }
  } else if (format === "both") {
    description = { text: `${relative} · ${absolute}`, title: "" }
  }
  return description
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

export class MjActivityFeed extends MjElement {
  static tagName = "mj-activity-feed";
  static styles = STYLES;
  static watched = ["label", "compact", "group-by", "load-mode", "realtime", "empty-message", "timestamp-format"];

  constructor() {
    super()
    this._items = []
    this._dataSource = null
    this._cursor = null

    /*
     * Whether older items can be loaded. A dataSource sets it from its
     * cursor; without one the host opts in by setting `hasMore`.
     */
    this._hasMore = false

    /* True from a host-answered `mj-load-older` until the host assigns `items` or `hasMore`. */
    this._awaitingHost = false

    /* True while a data-source request is in flight. */
    this._loading = false
    this._loadFailed = false

    /* Incremented per request so a response for a replaced source is dropped. */
    this._fetchSequence = 0

    this._newItemCount = 0
    this._intersectionObserver = null
    this._topObserver = null

    /* Items whose clamped body the user expanded; survives re-rendering. */
    this._expandedItems = new WeakSet()

    this._feedRoot = null
    this._newBanner = null
    this._feedList = null
    this._emptyEl = null
    this._loadMoreBtn = null
    this._errorEl = null
    this._sentinel = null
    this._topSentinel = null
  }

  render() {
    const markup = html`
      <div class="feed-root" part="root">
        <div class="top-sentinel" style="height:1px" aria-hidden="true"></div>
        <button class="new-banner" part="new-banner" hidden type="button"></button>
        <div class="feed-list" role="feed" part="feed-list" aria-busy="false"></div>
        <div class="empty-state" part="empty-state" hidden><slot name="empty"></slot></div>
        <div class="feed-error" role="alert" hidden>
          <span class="feed-error-text">${t("mj.activityFeed.loadError")}</span>
          <button class="retry-btn" type="button">${t("mj.activityFeed.retry")}</button>
        </div>
        <button class="load-more" part="load-more" type="button" hidden>
          ${t("mj.activityFeed.loadOlder")}
        </button>
        <div class="sentinel" style="height:1px" aria-hidden="true"></div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._feedRoot = this.$(".feed-root")
    this._newBanner = this.$(".new-banner")
    this._feedList = this.$(".feed-list")
    this._emptyEl = this.$(".empty-state")
    this._loadMoreBtn = this.$(".load-more")
    this._errorEl = this.$(".feed-error")
    this._sentinel = this.$(".sentinel")
    this._topSentinel = this.$(".top-sentinel")

    this._feedList.setAttribute("aria-label", this.getAttribute("label") || t("mj.activityFeed.label"))

    this.listen(this._newBanner, "click", this._onBannerClick.bind(this))
    this.listen(this._loadMoreBtn, "click", this._onLoadMore.bind(this))
    this.listen(this._feedList, "keydown", this._onFeedKeydown.bind(this))
    this.listen(this._feedList, "click", this._onFeedClick.bind(this))
    this.listen(this.$(".retry-btn"), "click", this._onRetry.bind(this))

    this._renderItems()
    this._syncBanner()
    this._setupTopObserver()
    this._setupInfiniteScroll()
    this._startTimestampRefresh()

    if (this._dataSource !== null && this._items.length === 0) {
      this._fetchInitial()
    }

    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._feedList === undefined || this._feedList === null) {
      return
    }

    if (name === "label") {
      this._feedList.setAttribute("aria-label", newValue || t("mj.activityFeed.label"))
    } else if (name === "group-by" || name === "empty-message" || name === "timestamp-format") {
      this._renderItems()
    } else if (name === "load-mode") {
      this._renderItems()
      this._setupInfiniteScroll()
    } else if (name === "realtime") {
      this._syncBanner()
    }
    return
  }

  /* ----- data source ----- */

  /* Adapters expose `query` (library DataSource) or `fetch` (the spec name). */
  _requestPage(cursor) {
    const source = this._dataSource
    let request = null
    try {
      if (typeof source.query === "function") {
        request = Promise.resolve(source.query({ cursor: cursor }))
      } else {
        request = Promise.resolve(source.fetch({ cursor: cursor }))
      }
    } catch (error) {
      request = Promise.reject(error)
    }
    return request
  }

  /* Record the paging state a page result carries. */
  _applyPageState(result) {
    const cursor = result.cursor !== undefined ? result.cursor : null
    this._cursor = cursor
    if (result.hasMore === true || result.hasMore === false) {
      this._hasMore = result.hasMore
    } else {
      /* Without a cursor there is no next page to ask for. */
      this._hasMore = cursor !== null
    }
    return
  }

  _setLoading(loading) {
    this._loading = loading
    this._syncBusy()
    return
  }

  /*
   * The feed is busy while the data source loads or the host has been asked
   * for older items; the Load older button is inert meanwhile.
   */
  _syncBusy() {
    const busy = this._loading === true || this._awaitingHost === true
    if (this._feedList !== null) {
      this._feedList.setAttribute("aria-busy", busy === true ? "true" : "false")
      this._feedList.hidden = this._items.length === 0 && busy === false
    }
    if (this._loadMoreBtn !== null) {
      if (busy === true) {
        this._loadMoreBtn.setAttribute("aria-disabled", "true")
      } else {
        this._loadMoreBtn.removeAttribute("aria-disabled")
      }
    }
    return
  }

  _setLoadFailed(failed) {
    this._loadFailed = failed
    if (this._errorEl !== null) {
      this._errorEl.hidden = failed === false
    }
    return
  }

  _fetchInitial() {
    if (this._dataSource === null || this._feedList === null) {
      return
    }

    this._fetchSequence = this._fetchSequence + 1
    const sequence = this._fetchSequence
    this._cursor = null
    this._hasMore = true
    this._setLoadFailed(false)
    this._setLoading(true)

    this._requestPage(null).then(
      (result) => {
        if (sequence === this._fetchSequence) {
          const page = result !== null && result !== undefined ? result : {}
          this._items = Array.isArray(page.items) === true ? page.items : []
          this._applyPageState(page)
          this._setLoading(false)
          this._renderItems()
          this._recheckSentinel()
        }
      },
      (error) => {
        if (sequence === this._fetchSequence) {
          this._setLoading(false)
          this._setLoadFailed(true)
          this._renderItems()
        }
      }
    )
    return
  }

  _loadOlderFromSource() {
    if (this._dataSource === null || this._loading === true || this._hasMore === false) {
      return
    }

    this._fetchSequence = this._fetchSequence + 1
    const sequence = this._fetchSequence
    this._setLoadFailed(false)
    this._setLoading(true)

    this._requestPage(this._cursor).then(
      (result) => {
        if (sequence === this._fetchSequence) {
          const page = result !== null && result !== undefined ? result : {}
          const newItems = Array.isArray(page.items) === true ? page.items : []
          this._applyPageState(page)
          if (newItems.length === 0) {
            this._hasMore = false
          }
          this._items = this._items.concat(newItems)
          this._setLoading(false)
          this._renderItems()
          if (this._hasMore === false) {
            announce(t("mj.activityFeed.allLoaded"), "polite")
          }
          this._recheckSentinel()
        }
      },
      (error) => {
        if (sequence === this._fetchSequence) {
          this._setLoading(false)
          this._setLoadFailed(true)
          this._renderItems()
        }
      }
    )
    return
  }

  _onRetry() {
    if (this._items.length === 0) {
      this._fetchInitial()
    } else {
      this._loadOlderFromSource()
    }
    return
  }

  /* ----- rendering ----- */

  _renderItems() {
    if (this._feedList === undefined || this._feedList === null) {
      return
    }

    /* Remember which item had focus so a rebuild does not drop it. */
    const activeEl = this.shadowRoot.activeElement
    let focusedItem = null
    let loadMoreHadFocus = false
    if (activeEl !== null) {
      const focusedArticle = activeEl.closest("article")
      if (focusedArticle !== null) {
        focusedItem = focusedArticle._mjItem
      }
      loadMoreHadFocus = activeEl === this._loadMoreBtn
    }

    this._feedList.textContent = ""
    this._syncBusy()

    const groupBy = this.getAttribute("group-by") || ""
    const loadMode = this.getAttribute("load-mode") || "button"

    /* The empty state is a sibling of the feed: a feed holds articles only. */
    this._emptyEl.querySelector("slot").textContent = this.getAttribute("empty-message") || t("mj.activityFeed.empty")
    this._emptyEl.hidden = this._items.length > 0 || this._loading === true || this._loadFailed === true

    if (this._items.length === 0) {
      this._loadMoreBtn.hidden = true
      return
    }

    let currentGroup = null
    let groupHeadingId = null
    let articleToFocus = null

    for (let i = 0; i < this._items.length; i = i + 1) {
      const item = this._items[i]

      if (groupBy === "date") {
        const date = parseTimestamp(item.timestamp)
        if (date !== null) {
          const groupKey = `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`
          if (groupKey !== currentGroup) {
            /*
             * Shown, but not a child the feed exposes: it describes the
             * first article of its day instead.
             */
            currentGroup = groupKey
            groupHeadingId = nextId("mj-af-day")
            const heading = document.createElement("div")
            heading.className = "group-heading"
            heading.id = groupHeadingId
            heading.setAttribute("part", "group-heading")
            heading.setAttribute("aria-hidden", "true")
            heading.textContent = formatDate(date, { dateStyle: "full" })
            this._feedList.appendChild(heading)
          } else {
            groupHeadingId = null
          }
        }
      }

      const articleEl = this._buildItemEl(item, i)
      if (groupHeadingId !== null) {
        articleEl.setAttribute("aria-describedby", groupHeadingId)
        groupHeadingId = null
      }
      this._feedList.appendChild(articleEl)
      if (item === focusedItem) {
        articleToFocus = articleEl
      }
    }

    this._loadMoreBtn.hidden = loadMode !== "button" || this._hasMore === false
    this._syncBodyToggles()

    if (articleToFocus !== null) {
      articleToFocus.focus()
    } else if (loadMoreHadFocus === true && this._loadMoreBtn.hidden === true) {
      /* The button the user was on is gone: keep focus on the last item. */
      const articles = this._feedList.querySelectorAll("article")
      articles[articles.length - 1].focus()
    }

    return
  }

  _buildItemEl(item, posInSet) {
    const headerId = nextId("mj-af-hdr")
    const article = document.createElement("article")
    article.className = "activity-item"
    article.setAttribute("part", "item")
    article.setAttribute("tabindex", "0")
    article.setAttribute("aria-labelledby", headerId)
    article.setAttribute("aria-setsize", "-1")
    article.setAttribute("aria-posinset", String(posInSet + 1))
    article.setAttribute("data-index", String(posInSet))
    article._mjItem = item

    const actor = item.actor || {}
    const actorName = actor.name !== undefined && actor.name !== null ? String(actor.name) : ""
    const avatarUrl = safeUrl(actor.avatarUrl, "")
    const avatar = avatarUrl.length > 0
      ? html`<img src="${avatarUrl}" alt="">`
      : initials(actorName)

    const hasBody = item.body !== undefined && item.body !== null
    const bodyId = nextId("mj-af-body")
    const expanded = this._expandedItems.has(item)
    const body = hasBody === true
      ? html`
          <div class="item-body${expanded === true ? " is-expanded" : ""}" part="item-body" id="${bodyId}">${item.body}</div>
          <button class="body-toggle" type="button" hidden aria-controls="${bodyId}"
                  aria-expanded="${expanded === true ? "true" : "false"}">${expanded === true ? t("mj.activityFeed.showLess") : t("mj.activityFeed.showMore")}</button>
        `
      : ""

    const actionList = Array.isArray(item.actions) === true ? item.actions : []
    const actions = actionList.length > 0
      ? html`
          <div class="item-actions" part="item-actions">
            ${actionList.map((entry) => html`
              <button class="item-action-btn" type="button" data-action="${entry.action}">${entry.label || entry.action}</button>
            `)}
          </div>
        `
      : ""

    article.innerHTML = String(html`
      <div class="item-avatar" part="item-avatar" aria-hidden="true">${avatar}</div>
      <div class="item-content">
        <div class="item-header" part="item-header" id="${headerId}">
          <span class="item-actor" part="item-actor">${actorName.length > 0 ? actorName : t("mj.activityFeed.systemActor")}</span>
          <span class="item-action-text" part="item-action-text">${item.action || ""}</span>
        </div>
        ${body}
        ${actions}
      </div>
    `)

    const hasTimestamp = item.timestamp !== undefined && item.timestamp !== null && item.timestamp !== ""
    if (hasTimestamp === true) {
      const timeEl = document.createElement("time")
      timeEl.className = "item-timestamp"
      timeEl.setAttribute("part", "item-timestamp")
      const date = parseTimestamp(item.timestamp)
      if (date !== null) {
        timeEl.setAttribute("datetime", date.toISOString())
        this._fillTimestamp(timeEl, date)
      } else {
        /* An unparseable value is shown as given rather than as "NaN". */
        timeEl.textContent = String(item.timestamp)
      }
      article.querySelector(".item-header").appendChild(timeEl)
    }

    return article
  }

  _fillTimestamp(timeEl, date) {
    const format = this.getAttribute("timestamp-format") || "relative"
    const description = describeTimestamp(date, format)
    timeEl.textContent = description.text
    if (description.title.length > 0) {
      timeEl.setAttribute("title", description.title)
    } else {
      timeEl.removeAttribute("title")
    }
    return
  }

  /* Offer "Show more" only on bodies the four-line clamp actually cut off. */
  _syncBodyToggles() {
    const toggles = this._feedList.querySelectorAll(".body-toggle")
    for (let i = 0; i < toggles.length; i = i + 1) {
      const toggle = toggles[i]
      const bodyEl = toggle.previousElementSibling
      const expanded = toggle.getAttribute("aria-expanded") === "true"
      const clamped = bodyEl.scrollHeight > bodyEl.clientHeight + 1
      toggle.hidden = expanded === false && clamped === false
    }
    return
  }

  _onFeedClick(event) {
    const article = event.target.closest("article")
    if (article === null) {
      return
    }
    const item = article._mjItem

    const toggle = event.target.closest(".body-toggle")
    if (toggle !== null) {
      const expand = toggle.getAttribute("aria-expanded") !== "true"
      const bodyEl = toggle.previousElementSibling
      if (expand === true) {
        this._expandedItems.add(item)
      } else {
        this._expandedItems.delete(item)
      }
      bodyEl.classList.toggle("is-expanded", expand)
      toggle.setAttribute("aria-expanded", expand === true ? "true" : "false")
      toggle.textContent = expand === true ? t("mj.activityFeed.showLess") : t("mj.activityFeed.showMore")
      return
    }

    const actionBtn = event.target.closest(".item-action-btn")
    if (actionBtn !== null) {
      this.emit("mj-item-action", {
        itemId: item.id,
        action: actionBtn.getAttribute("data-action"),
        item: item
      })
    }
    return
  }

  /* ----- new-items banner ----- */

  /*
   * True when the start of the feed is on screen: inside the viewport and
   * inside every scrolling ancestor. `.feed-root` itself never scrolls.
   */
  _isTopInView() {
    const topRect = this._topSentinel.getBoundingClientRect()
    let inView = topRect.top >= -10 && topRect.top <= window.innerHeight

    let ancestor = this.parentNode
    while (inView === true && ancestor !== null && ancestor !== undefined) {
      if (ancestor instanceof ShadowRoot) {
        ancestor = ancestor.host
      } else if (ancestor instanceof Element) {
        const overflowY = getComputedStyle(ancestor).overflowY
        if (overflowY === "auto" || overflowY === "scroll") {
          const ancestorRect = ancestor.getBoundingClientRect()
          inView = topRect.top >= ancestorRect.top - 10 && topRect.top <= ancestorRect.bottom
        }
        ancestor = ancestor.parentNode
      } else {
        ancestor = null
      }
    }
    return inView
  }

  _syncBanner() {
    if (this._newBanner === null) {
      return
    }
    const show = this.hasAttribute("realtime") === true && this._newItemCount > 0
    this._newBanner.hidden = show === false
    if (show === true) {
      const count = this._newItemCount
      this._newBanner.textContent = t("mj.activityFeed.newEventsBanner", { count: count })
    }
    return
  }

  /* The reader has reached the top: the prepended items are no longer new. */
  _markNewItemsViewed() {
    const count = this._newItemCount
    if (count === 0) {
      return
    }
    const bannerHadFocus = this.shadowRoot.activeElement === this._newBanner
    this._newItemCount = 0
    this._syncBanner()
    if (bannerHadFocus === true) {
      const firstArticle = this._feedList.querySelector("article")
      if (firstArticle !== null) {
        firstArticle.focus({ preventScroll: true })
      }
    }
    this.emit("mj-new-items-viewed", { count: count })
    return
  }

  _onBannerClick() {
    this._feedRoot.scrollIntoView({ behavior: "smooth", block: "start" })
    this._markNewItemsViewed()
    return
  }

  /* Dismiss the banner when the reader scrolls back to the top unaided. */
  _setupTopObserver() {
    if (typeof IntersectionObserver === "undefined") {
      return
    }
    this._topObserver = new IntersectionObserver((entries) => {
      for (let i = 0; i < entries.length; i = i + 1) {
        if (entries[i].isIntersecting === true) {
          this._markNewItemsViewed()
        }
      }
    })
    this._topObserver.observe(this._topSentinel)
    this.onTeardown(() => {
      if (this._topObserver !== null) {
        this._topObserver.disconnect()
        this._topObserver = null
      }
    })
    return
  }

  /* ----- load older ----- */

  _onLoadMore() {
    if (this._loading === true || this._awaitingHost === true || this._hasMore === false) {
      return
    }
    this.emit("mj-load-older", { cursor: this._cursor })
    if (this._dataSource !== null) {
      this._loadOlderFromSource()
    } else {
      /* One request at a time: wait for the host to assign `items` or `hasMore`. */
      this._awaitingHost = true
      this._syncBusy()
    }
    return
  }

  /*
   * Arm (or disarm) the bottom sentinel for `load-mode="infinite"`. Safe to
   * call again when the attribute changes.
   */
  _setupInfiniteScroll() {
    if (this._intersectionObserver !== null) {
      this._intersectionObserver.disconnect()
      this._intersectionObserver = null
    }

    const loadMode = this.getAttribute("load-mode") || "button"
    if (loadMode !== "infinite" || typeof IntersectionObserver === "undefined") {
      return
    }

    this._intersectionObserver = new IntersectionObserver((entries) => {
      for (let i = 0; i < entries.length; i = i + 1) {
        /* Nothing is older than an empty feed; the initial fetch fills it. */
        if (entries[i].isIntersecting === true && this._items.length > 0) {
          this._onLoadMore()
        }
      }
    })
    this._intersectionObserver.observe(this._sentinel)

    this.onTeardown(() => {
      if (this._intersectionObserver !== null) {
        this._intersectionObserver.disconnect()
        this._intersectionObserver = null
      }
    })
    return
  }

  /*
   * An IntersectionObserver reports changes only. After a short page the
   * sentinel is still in view, so it is observed afresh, which reports its
   * current state and loads the next page if there is room.
   */
  _recheckSentinel() {
    if (this._intersectionObserver !== null && this._hasMore === true) {
      this._intersectionObserver.unobserve(this._sentinel)
      this._intersectionObserver.observe(this._sentinel)
    }
    return
  }

  /* ----- timestamps ----- */

  _refreshTimestamps() {
    const timeEls = this._feedList.querySelectorAll("time.item-timestamp[datetime]")
    for (let i = 0; i < timeEls.length; i = i + 1) {
      const date = parseTimestamp(timeEls[i].getAttribute("datetime"))
      if (date !== null) {
        this._fillTimestamp(timeEls[i], date)
      }
    }
    return
  }

  _startTimestampRefresh() {
    /* Timestamps update silently; they are not in a live region. */
    const timer = window.setInterval(() => {
      this._refreshTimestamps()
    }, 60000)
    this.onTeardown(() => {
      window.clearInterval(timer)
    })
    return
  }

  /* ----- keyboard ----- */

  /*
   * APG feed keys: Page Down / Page Up move between articles, Home / End go
   * to the first / last one. A key is consumed only when focus moves, so
   * normal page scrolling still works at either end of the feed.
   */
  _onFeedKeydown(event) {
    const articles = Array.from(this._feedList.querySelectorAll("article"))
    if (articles.length === 0) {
      return
    }

    const activeEl = this.shadowRoot.activeElement
    let currentIndex = -1
    for (let i = 0; i < articles.length; i = i + 1) {
      if (articles[i] === activeEl || articles[i].contains(activeEl)) {
        currentIndex = i
        break
      }
    }

    let targetIndex = -1
    if (event.key === "PageDown") {
      targetIndex = currentIndex + 1
    } else if (event.key === "PageUp") {
      targetIndex = currentIndex - 1
    } else if (event.key === "Home") {
      targetIndex = 0
    } else if (event.key === "End") {
      targetIndex = articles.length - 1
    }

    if (targetIndex >= 0 && targetIndex < articles.length && targetIndex !== currentIndex) {
      event.preventDefault()
      articles[targetIndex].focus()
    }
    return
  }

  /* ----- public API ----- */

  /*
   * Prepend a new item. In `realtime` mode, when the reader is not at the
   * top of the feed, the item counts towards the "N new events" banner.
   */
  addItem(item) {
    if (item === null || item === undefined) {
      return
    }

    /* Items without an id cannot be told apart, so they are never deduplicated. */
    if (item.id !== undefined && item.id !== null) {
      const existing = this._items.find((candidate) => candidate.id === item.id)
      if (existing !== undefined) {
        console.warn(`mj-activity-feed: ignoring item with duplicate id "${item.id}"`)
        return
      }
    }

    this._items.unshift(item)

    if (this._feedList === null) {
      return
    }

    if (this.hasAttribute("realtime") === true && this._isTopInView() === false) {
      this._newItemCount = this._newItemCount + 1
      announce(t("mj.activityFeed.newActivities", { count: this._newItemCount }), "polite")
    }

    this._renderItems()
    this._syncBanner()
    return
  }

  get items() {
    return this._items
  }

  set items(value) {
    this._items = Array.isArray(value) ? value : []
    this._awaitingHost = false
    this._renderItems()
    this._recheckSentinel()
    return
  }

  get dataSource() {
    return this._dataSource
  }

  set dataSource(source) {
    this._dataSource = source !== undefined ? source : null
    this._awaitingHost = false
    if (this._dataSource !== null) {
      this._fetchInitial()
    }
    return
  }

  /*
   * Whether older items can still be loaded. Maintained from the data
   * source's cursor; a host that pages by itself (through `mj-load-older`)
   * sets it to true to offer the load-older control and to false at the end.
   */
  get hasMore() {
    return this._hasMore
  }

  set hasMore(value) {
    this._hasMore = value === true
    this._awaitingHost = false
    this._renderItems()
    this._recheckSentinel()
    return
  }

  get newItemCount() {
    return this._newItemCount
  }
}
