/*
 * mjactivityfeed.js
 *
 * <mj-activity-feed> -- chronological stream of activity events with
 * APG Feed pattern (role="feed"), real-time prepend, load-older, and
 * relative timestamp refresh.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";

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

.item-actions {
  display: flex;
  gap: var(--mj-space-2);
  margin-top: var(--mj-space-2);
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

function relativeTime(timestamp) {
  const now = Date.now()
  const then = new Date(timestamp).getTime()
  const diff = now - then
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (seconds < 60) {
    return "just now"
  }
  if (minutes < 60) {
    return `${minutes}m ago`
  }
  if (hours < 24) {
    return `${hours}h ago`
  }
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

export class MjActivityFeed extends MjElement {
  static tagName = "mj-activity-feed";
  static styles = STYLES;
  static watched = ["label", "compact", "group-by", "load-mode", "realtime", "empty-message", "timestamp-format"];

  constructor() {
    super()
    this._items = []
    this._dataSource = null
    this._cursor = null
    this._newItemCount = 0
    this._timestampTimer = null
    this._intersectionObserver = null
  }

  render() {
    const label = this.getAttribute("label") || "Activity feed"
    const markup = `
      <div class="feed-root" role="feed" part="root"
           aria-label="${label}" aria-busy="false">
        <button class="new-banner" part="new-banner" hidden type="button"
                role="status" aria-live="polite"></button>
        <div class="feed-list" part="feed-list"></div>
        <button class="load-more" part="load-more" type="button" hidden>
          Load older activity
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
    this._loadMoreBtn = this.$(".load-more")
    this._sentinel = this.$(".sentinel")

    this.listen(this._newBanner, "click", this._onBannerClick.bind(this))
    this.listen(this._loadMoreBtn, "click", this._onLoadMore.bind(this))
    this.listen(this._feedRoot, "keydown", this._onFeedKeydown.bind(this))

    this._renderItems()
    this._setupInfiniteScroll()
    this._startTimestampRefresh()

    if (this._dataSource !== null) {
      this._fetchInitial()
    }

    return
  }

  onDisconnected() {
    if (this._timestampTimer !== null) {
      window.clearInterval(this._timestampTimer)
      this._timestampTimer = null
    }
    return
  }

  _fetchInitial() {
    if (this._dataSource === null) {
      return
    }
    this._feedRoot.setAttribute("aria-busy", "true")
    const promise = this._dataSource.query({ cursor: null })
    Promise.resolve(promise).then((result) => {
      this._items = result.items || []
      this._cursor = result.cursor || null
      this._feedRoot.setAttribute("aria-busy", "false")
      this._renderItems()
    }).catch(() => {
      this._feedRoot.setAttribute("aria-busy", "false")
    })
    return
  }

  _renderItems() {
    if (this._feedList === null) {
      return
    }
    this._feedList.innerHTML = ""

    const groupBy = this.getAttribute("group-by") || ""
    const emptyMsg = this.getAttribute("empty-message") || "No activity yet."
    const loadMode = this.getAttribute("load-mode") || "button"

    if (this._items.length === 0) {
      this._feedList.innerHTML = `
        <div class="empty-state" part="empty-state">
          <slot name="empty">${emptyMsg}</slot>
        </div>
      `
      this._loadMoreBtn.hidden = true
      return
    }

    let currentGroup = null

    for (let i = 0; i < this._items.length; i = i + 1) {
      const item = this._items[i]

      if (groupBy === "date" && item.timestamp !== undefined) {
        const dateStr = new Date(item.timestamp).toDateString()
        if (dateStr !== currentGroup) {
          currentGroup = dateStr
          const heading = document.createElement("div")
          heading.className = "group-heading"
          heading.setAttribute("part", "group-heading")
          heading.setAttribute("aria-hidden", "true")
          heading.textContent = dateStr
          this._feedList.appendChild(heading)
        }
      }

      const articleEl = this._buildItemEl(item, i)
      this._feedList.appendChild(articleEl)
    }

    if (loadMode === "button") {
      this._loadMoreBtn.hidden = false
    }

    return
  }

  _buildItemEl(item, posInSet) {
    const headerId = nextId("mj-af-hdr")
    const article = document.createElement("article")
    article.className = "activity-item"
    article.setAttribute("part", "item")
    article.setAttribute("aria-labelledby", headerId)
    article.setAttribute("aria-setsize", "-1")
    article.setAttribute("aria-posinset", String(posInSet + 1))

    const actor = item.actor || {}
    const avatarHtml = actor.avatarUrl !== undefined
      ? `<img src="${actor.avatarUrl}" alt="${actor.name || ""}"/>`
      : initials(actor.name || "?")

    const tsFormat = this.getAttribute("timestamp-format") || "relative"
    const ts = item.timestamp || ""
    const relTs = ts !== "" ? relativeTime(ts) : ""
    const absTs = ts !== "" ? new Date(ts).toLocaleString() : ""
    const tsDisplay = tsFormat === "absolute" ? absTs : relTs
    const tsTitle = tsFormat === "relative" && absTs !== "" ? absTs : ""

    const bodyHtml = item.body !== undefined && item.body !== null
      ? `<div class="item-body" part="item-body">${this._escapeHtml(String(item.body))}</div>`
      : ""

    article.innerHTML = `
      <div class="item-avatar" part="item-avatar" aria-hidden="true">${avatarHtml}</div>
      <div class="item-content">
        <div class="item-header" id="${headerId}">
          <span class="item-actor" part="item-actor">${this._escapeHtml(actor.name || "System")}</span>
          <span class="item-action-text" part="item-action-text">${this._escapeHtml(item.action || "")}</span>
          <time class="item-timestamp" part="item-timestamp"
                datetime="${ts}" title="${tsTitle}">${tsDisplay}</time>
        </div>
        ${bodyHtml}
      </div>
    `
    return article
  }

  _onBannerClick() {
    const count = this._newItemCount
    this._newItemCount = 0
    this._newBanner.hidden = true
    this.emit("mj-new-items-viewed", { count: count })
    // Scroll to top of feed
    this._feedRoot.scrollIntoView({ behavior: "smooth" })
    return
  }

  _onLoadMore() {
    this.emit("mj-load-older", { cursor: this._cursor })
    if (this._dataSource !== null) {
      this._loadMoreOlderFromSource()
    }
    return
  }

  _loadMoreOlderFromSource() {
    if (this._dataSource === null) {
      return
    }
    const promise = this._dataSource.query({ cursor: this._cursor })
    Promise.resolve(promise).then((result) => {
      const newItems = result.items || []
      if (newItems.length === 0) {
        this._loadMoreBtn.hidden = true
        announce("All activity loaded", "polite")
        return
      }
      this._items = this._items.concat(newItems)
      this._cursor = result.cursor || null
      this._renderItems()
    }).catch(() => {})
    return
  }

  _setupInfiniteScroll() {
    const loadMode = this.getAttribute("load-mode") || "button"
    if (loadMode !== "infinite") {
      return
    }
    if (typeof IntersectionObserver === "undefined") {
      return
    }
    this._intersectionObserver = new IntersectionObserver((entries) => {
      for (let i = 0; i < entries.length; i = i + 1) {
        if (entries[i].isIntersecting === true) {
          this._onLoadMore()
        }
      }
    }, { threshold: 0.5 })

    if (this._sentinel !== null) {
      this._intersectionObserver.observe(this._sentinel)
    }
    this.onTeardown(() => {
      if (this._intersectionObserver !== null) {
        this._intersectionObserver.disconnect()
        this._intersectionObserver = null
      }
    })
    return
  }

  _startTimestampRefresh() {
    this._timestampTimer = window.setInterval(() => {
      // Update timestamps silently without live-region re-announce
      const timeEls = this._feedList.querySelectorAll("time.item-timestamp")
      for (let i = 0; i < timeEls.length; i = i + 1) {
        const el = timeEls[i]
        const ts = el.getAttribute("datetime")
        if (ts !== null && ts !== "") {
          const tsFormat = this.getAttribute("timestamp-format") || "relative"
          if (tsFormat !== "absolute") {
            el.textContent = relativeTime(ts)
          }
        }
      }
    }, 60000)
    return
  }

  _onFeedKeydown(event) {
    const articles = this._feedList.querySelectorAll("article")
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

    if (event.key === "PageDown") {
      event.preventDefault()
      const next = currentIndex + 1 < articles.length ? currentIndex + 1 : 0
      articles[next].focus()
    } else if (event.key === "PageUp") {
      event.preventDefault()
      const prev = currentIndex - 1 >= 0 ? currentIndex - 1 : articles.length - 1
      articles[prev].focus()
    } else if (event.key === "Home") {
      event.preventDefault()
      articles[0].focus()
    } else if (event.key === "End") {
      event.preventDefault()
      articles[articles.length - 1].focus()
    }
    return
  }

  _escapeHtml(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
  }

  addItem(item) {
    const existing = this._items.find((i) => i.id === item.id)
    if (existing !== undefined) {
      return
    }

    this._items.unshift(item)
    this._newItemCount = this._newItemCount + 1

    const isScrolledToTop = this._feedRoot.scrollTop <= 10
    if (isScrolledToTop === false && this.hasAttribute("realtime")) {
      this._newBanner.hidden = false
      this._newBanner.textContent = `${this._newItemCount} new event${this._newItemCount > 1 ? "s" : ""}. Click to view.`
      announce(`${this._newItemCount} new activities`, "polite")
    }

    this._renderItems()
    return
  }

  get items() {
    return this._items
  }

  set items(value) {
    this._items = Array.isArray(value) ? value : []
    if (this._feedList !== null) {
      this._renderItems()
    }
    return
  }

  get dataSource() {
    return this._dataSource
  }

  set dataSource(source) {
    this._dataSource = source
    if (source !== null && source !== undefined && this._feedList !== null) {
      this._fetchInitial()
    }
    return
  }

  get newItemCount() {
    return this._newItemCount
  }
}
