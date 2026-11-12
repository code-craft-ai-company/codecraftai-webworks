/*
 * mjfeed.js
 *
 * <mj-feed> -- a scrollable list of feed articles implementing the WAI-ARIA
 * feed role. Supports infinite scroll, button-triggered loading, and the APG
 * feed keyboard navigation pattern.
 *
 * Items are the feed's element children -- any element works (an <article>,
 * a <div>, an <mj-card>, or the conventional <mj-feed-item> tag, which is a
 * plain element; no separate component is needed). Children assigned to a
 * named slot, such as slot="empty", are not items. The feed manages on every
 * item:
 *   role="article"               unless the author gave the item a role
 *   aria-posinset / aria-setsize its position; the size is -1 while more
 *                                items can still be loaded
 *   aria-labelledby              the item's first heading, when the item has
 *                                no accessible name of its own
 *   tabindex                     a roving tab stop: one item is in the tab
 *                                order, Page Up / Page Down move between them
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";
import { findById } from "../core/aria.js";

const DEFAULT_LOAD_MORE_LABEL_KEY = "mj.feed.loadMore";

/* How long a new-items announcement stays in the live region. */
const ANNOUNCEMENT_MS = 3000;

const STYLES = `
:host {
  display: block;
}

.root {
  position: relative;
  display: flex;
  flex-direction: column;
}

.items-container {
  display: flex;
  flex-direction: column;
  gap: var(--mj-feed-gap, var(--mj-space-4));
  max-inline-size: var(--mj-feed-max-width, none);
  padding: var(--mj-feed-padding, 0);
}

:host([reversed]) .items-container {
  flex-direction: column-reverse;
}

/* Reversed (chat-style) feeds load older items at the top. */
:host([reversed]) .sentinel,
:host([reversed]) .load-more-btn,
:host([reversed]) .loading-indicator {
  order: -1;
}

:host([reversed]) .load-more-btn {
  margin-block: 0 var(--mj-space-4);
}

::slotted(:focus-visible) {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.sentinel {
  block-size: 1px;
  inline-size: 100%;
  visibility: hidden;
}

.load-more-btn {
  display: block;
  margin-block-start: var(--mj-space-4);
  margin-inline: auto;
  padding: var(--mj-space-2) var(--mj-space-5);
  background: var(--mj-surface);
  color: var(--mj-text);
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-md);
  cursor: pointer;
  font: inherit;
  font-size: var(--mj-font-size-sm);
  min-block-size: var(--mj-control-height-md);
}

.load-more-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.load-more-btn:disabled { opacity: 0.55; cursor: not-allowed; }

.loading-indicator {
  text-align: center;
  padding: var(--mj-space-4);
  color: var(--mj-text-muted);
  font-size: var(--mj-font-size-sm);
}

:host(:not([loading])) .loading-indicator { display: none; }
:host([has-more="false"]) .sentinel,
:host([has-more="false"]) .load-more-btn { display: none !important; }

.live-region {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0,0,0,0);
  white-space: nowrap;
}
`;

export class MjFeed extends MjElement {
  static tagName = "mj-feed";
  static styles = STYLES;
  static watched = ["load-mode", "loading", "has-more", "reversed", "load-more-label", "loading-label", "aria-label", "aria-labelledby"];

  constructor() {
    super()
    this._intersectionObserver = null
    this._mutationObserver = null
    this._announceTimer = null
    this._rootEl = null
    this._feedEl = null
    this._sentinel = null
    this._loadMoreBtn = null
    this._loadingIndicator = null
    this._liveRegion = null
    this._emptyRegion = null

    /* The item that holds the feed's tab stop. */
    this._tabStopItem = null

    /* What the feed wrote on each item, so only that is updated or removed. */
    this._itemRecords = new WeakMap()

    /* True while a load request is waiting for `loading` or new items. */
    this._sentinelVisible = false
  }

  /*
   * Only the items are inside the role="feed" element: a feed may own
   * nothing but articles, so the load-more sentinel and button, the loading
   * indicator, the live region and the empty state are its siblings.
   */
  render() {
    const markup = html`
      <div class="root" part="root">
        <div class="items-container" part="items-container" role="feed" aria-busy="false">
          <slot></slot>
        </div>
        <div class="sentinel" aria-hidden="true"></div>
        <button type="button" class="load-more-btn" part="load-more-button"></button>
        <div class="loading-indicator" part="loading-indicator" aria-hidden="true"></div>
        <div class="live-region" aria-live="polite" aria-atomic="true"></div>
        <div part="empty" hidden><slot name="empty"></slot></div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._rootEl = this.$(".root")
    this._feedEl = this.$(".items-container")
    this._sentinel = this.$(".sentinel")
    this._loadMoreBtn = this.$(".load-more-btn")
    this._loadingIndicator = this.$(".loading-indicator")
    this._liveRegion = this.$(".live-region")
    this._emptyRegion = this.$("[part='empty']")

    this.listen(this._loadMoreBtn, "click", this._onLoadMore.bind(this))
    this.listen(this, "keydown", this._onKeyDown.bind(this))
    this.listen(this, "focusin", this._onFocusIn.bind(this))

    this._syncState()
    this._syncAccessibleName()
    this._updatePositions()
    this._updateEmptyState()
    return
  }

  onConnected() {
    /* Elements named by aria-labelledby can only be resolved once connected. */
    this._syncAccessibleName()

    this._mutationObserver = new MutationObserver((mutations) => {
      this._onChildrenChanged(mutations)
    })
    this._mutationObserver.observe(this, { childList: true })

    this._setupIntersectionObserver()

    this.onTeardown(() => {
      if (this._intersectionObserver !== null) {
        this._intersectionObserver.disconnect()
        this._intersectionObserver = null
      }
      if (this._mutationObserver !== null) {
        this._mutationObserver.disconnect()
        this._mutationObserver = null
      }
      if (this._announceTimer !== null) {
        window.clearTimeout(this._announceTimer)
        this._announceTimer = null
      }
      this._sentinelVisible = false
    })
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._rootEl === undefined || this._rootEl === null) {
      return
    }

    this._syncState()

    if (name === "aria-label" || name === "aria-labelledby") {
      this._syncAccessibleName()
    }

    if (name === "loading" || name === "has-more" || name === "load-mode") {
      this._updateEmptyState()
      this._updatePositions()
      /* Loading finished while the sentinel is still in view: ask again. */
      this._recheckSentinel()
    }
    return
  }

  /*
   * The feed role sits on an element inside the shadow root, so a name given
   * on the host (aria-label, or aria-labelledby pointing at elements in the
   * host's tree) is copied onto it as text: id references cannot cross the
   * shadow boundary.
   */
  _syncAccessibleName() {
    if (this._feedEl === null || this._feedEl === undefined) {
      return
    }

    let name = this.getAttribute("aria-label") || ""
    if (name.length === 0) {
      const ids = (this.getAttribute("aria-labelledby") || "").split(/\s+/)
      const parts = []
      for (let index = 0; index < ids.length; index = index + 1) {
        const labelEl = findById(this, ids[index])
        if (labelEl !== null) {
          parts.push(labelEl.textContent.trim())
        }
      }
      name = parts.join(" ").trim()
    }

    if (name.length > 0) {
      this._feedEl.setAttribute("aria-label", name)
    } else {
      this._feedEl.removeAttribute("aria-label")
    }
    return
  }

  _syncState() {
    if (this._rootEl === null || this._rootEl === undefined) {
      return
    }

    const loading = this.hasAttribute("loading")
    const loadMode = this.getAttribute("load-mode") || "scroll"
    const loadMoreLabel = this.getAttribute("load-more-label")
    const loadingLabel = this.getAttribute("loading-label")

    this._feedEl.setAttribute("aria-busy", loading === true ? "true" : "false")
    this._loadMoreBtn.disabled = loading === true
    this._loadMoreBtn.hidden = loadMode !== "button"
    this._sentinel.hidden = loadMode !== "scroll"

    this._loadMoreBtn.textContent = loadMoreLabel !== null && loadMoreLabel.length > 0
      ? loadMoreLabel
      : t(DEFAULT_LOAD_MORE_LABEL_KEY)
    this._loadingIndicator.textContent = loadingLabel !== null && loadingLabel.length > 0
      ? loadingLabel
      : t("core.loading")
    return
  }

  /* ----- loading ----- */

  _canRequestMore() {
    const loadMode = this.getAttribute("load-mode") || "scroll"
    const loading = this.hasAttribute("loading")
    const hasMore = this.getAttribute("has-more") !== "false"
    const allowed = loadMode === "scroll" && loading === false && hasMore === true
    return allowed
  }

  _setupIntersectionObserver() {
    if (typeof IntersectionObserver !== "function" || this._sentinel === null) {
      return
    }
    if (this._intersectionObserver !== null) {
      this._intersectionObserver.disconnect()
    }

    this._intersectionObserver = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        this._sentinelVisible = entry.isIntersecting === true
        if (this._sentinelVisible === true && this._canRequestMore() === true) {
          this._onLoadMore()
        }
      }
    }, { rootMargin: "200px" })

    this._intersectionObserver.observe(this._sentinel)
    return
  }

  /*
   * The observer only reports CHANGES of visibility. When loading ends or
   * items arrive and the sentinel is still in view (a short page on a tall
   * screen), observe it afresh so its current state is reported again.
   */
  _recheckSentinel() {
    if (this._intersectionObserver === null || this._sentinel === null) {
      return
    }
    if (this._sentinelVisible === true && this._canRequestMore() === true) {
      this._intersectionObserver.unobserve(this._sentinel)
      this._intersectionObserver.observe(this._sentinel)
    }
    return
  }

  _onLoadMore() {
    const items = this.items
    this.emit("mj-feed-load-more", { itemCount: items.length })
    return
  }

  /* ----- items ----- */

  _onChildrenChanged(mutations) {
    let addedCount = 0

    for (const mutation of mutations) {
      for (const node of mutation.addedNodes) {
        const isItem = node.nodeType === Node.ELEMENT_NODE && node.parentNode === this &&
          node.hasAttribute("slot") === false
        if (isItem === true) {
          addedCount = addedCount + 1
        }
      }
      for (const node of mutation.removedNodes) {
        if (node.nodeType === Node.ELEMENT_NODE && node.parentNode !== this) {
          this._releaseItem(node)
        }
      }
    }

    /* Children the parser is still adding are the initial content, not news. */
    if (addedCount > 0 && document.readyState !== "loading") {
      this._announceNewItems(addedCount)
    }

    this._updatePositions()
    this._updateEmptyState()
    this._recheckSentinel()
    return
  }

  _announceNewItems(count) {
    if (this._liveRegion === null) {
      return
    }

    this._liveRegion.textContent = t("mj.feed.newItems", { count: count })

    if (this._announceTimer !== null) {
      window.clearTimeout(this._announceTimer)
    }
    this._announceTimer = window.setTimeout(() => {
      this._announceTimer = null
      if (this._liveRegion !== null) {
        this._liveRegion.textContent = ""
      }
    }, ANNOUNCEMENT_MS)
    return
  }

  /* The first heading inside an item, used as its accessible name. */
  _findItemHeading(item) {
    const heading = item.querySelector("h1, h2, h3, h4, h5, h6, [role='heading']")
    return heading
  }

  /*
   * Give each item its article semantics, position, name and roving
   * tabindex. Attributes the author set are left alone.
   */
  _updatePositions() {
    const items = this.items
    const total = items.length
    const loadMode = this.getAttribute("load-mode") || "scroll"
    const complete = this.getAttribute("has-more") === "false" || loadMode === "none"
    const setSize = complete === true ? String(total) : "-1"

    if (items.indexOf(this._tabStopItem) < 0) {
      this._tabStopItem = total > 0 ? items[0] : null
    }

    for (let index = 0; index < total; index = index + 1) {
      const item = items[index]
      let record = this._itemRecords.get(item)
      if (record === undefined) {
        record = {
          role: false,
          labelledBy: null,
          tabIndex: item.hasAttribute("tabindex") === false
        }
        this._itemRecords.set(item, record)
      }

      if (item.hasAttribute("role") === false) {
        item.setAttribute("role", "article")
        record.role = true
      }

      item.setAttribute("aria-posinset", String(index + 1))
      item.setAttribute("aria-setsize", setSize)

      const ownName = item.hasAttribute("aria-label") === true ||
        (item.hasAttribute("aria-labelledby") === true && item.getAttribute("aria-labelledby") !== record.labelledBy)
      if (ownName === false) {
        const heading = this._findItemHeading(item)
        if (heading !== null) {
          if (heading.id.length === 0) {
            heading.id = nextId("mj-feed-item-heading")
          }
          record.labelledBy = heading.id
          item.setAttribute("aria-labelledby", heading.id)
        }
      }

      if (record.tabIndex === true) {
        item.setAttribute("tabindex", item === this._tabStopItem ? "0" : "-1")
      }
    }
    return
  }

  _releaseItem(item) {
    const record = this._itemRecords.get(item)
    if (record === undefined) {
      return
    }

    item.removeAttribute("aria-posinset")
    item.removeAttribute("aria-setsize")
    if (record.role === true) {
      item.removeAttribute("role")
    }
    if (record.labelledBy !== null && item.getAttribute("aria-labelledby") === record.labelledBy) {
      item.removeAttribute("aria-labelledby")
    }
    if (record.tabIndex === true) {
      item.removeAttribute("tabindex")
    }
    this._itemRecords.delete(item)
    return
  }

  _updateEmptyState() {
    if (this._emptyRegion === null || this._emptyRegion === undefined) {
      return
    }

    const isEmpty = this.items.length === 0 && this.hasAttribute("loading") === false
    this._emptyRegion.hidden = isEmpty === false

    /*
     * A feed must own at least one article unless it is busy: while it has
     * no item and is not loading, the container has no role and the empty
     * state (outside it) is what is shown.
     */
    if (isEmpty === true) {
      this._feedEl.removeAttribute("role")
    } else {
      this._feedEl.setAttribute("role", "feed")
    }
    return
  }

  /* ----- keyboard ----- */

  /* The item that contains `node`, or -1. */
  _itemIndexOf(node) {
    const items = this.items
    let found = -1

    for (let index = 0; index < items.length && found < 0; index = index + 1) {
      if (items[index] === node || items[index].contains(node) === true) {
        found = index
      }
    }

    return found
  }

  /* The item last focused keeps the tab stop, so Tab returns to it. */
  _onFocusIn(event) {
    const index = this._itemIndexOf(event.target)
    if (index >= 0) {
      const item = this.items[index]
      if (item !== this._tabStopItem) {
        this._tabStopItem = item
        this._updatePositions()
      }
    }
    return
  }

  _focusItem(index) {
    const item = this.items[index]
    this._tabStopItem = item
    this._updatePositions()
    item.focus()
    this.emit("mj-feed-item-focus", { item: item, index: index })
    return
  }

  _onKeyDown(event) {
    const items = this.items
    if (items.length === 0) {
      return
    }

    const current = this._itemIndexOf(event.target)
    const last = items.length - 1
    let target = null

    if (event.key === "PageDown") {
      target = Math.min(current + 1, last)
    } else if (event.key === "PageUp") {
      target = Math.max(current - 1, 0)
    } else if (event.ctrlKey === true && event.key === "End") {
      target = last
    } else if (event.ctrlKey === true && event.key === "Home") {
      target = 0
    }

    /* Keep native paging when focus would not move to a different item. */
    const moves = target !== null && (target !== current || items[target] !== event.target)
    if (moves === true) {
      event.preventDefault()
      this._focusItem(target)
    }
    return
  }

  get items() {
    const children = Array.from(this.children)
    const feedItems = children.filter((element) => element.hasAttribute("slot") === false)
    return feedItems
  }

  get itemCount() {
    return this.items.length
  }
}
