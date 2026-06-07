/*
 * mjfeed.js
 *
 * <mj-feed> -- a scrollable list of feed articles implementing the WAI-ARIA
 * feed role. Supports infinite scroll, button-triggered loading, and the APG
 * feed keyboard navigation pattern.
 */

import { MjElement } from "../core/mjelement.js";

const STYLES = `
:host {
  display: block;
}

.root {
  position: relative;
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
  static watched = ["load-mode", "loading", "has-more", "reversed"];

  constructor() {
    super()
    this._intersectionObserver = null
    this._mutationObserver = null
    this._prevItemCount = 0
  }

  render() {
    const loadMode = this.getAttribute("load-mode") || "scroll"
    const loadMoreLabel = this.getAttribute("load-more-label") || "Load more"
    const loadingLabel = this.getAttribute("loading-label") || "Loading"
    const markup = `
      <div class="root" part="root" role="feed" aria-busy="false">
        <div class="items-container" part="items-container">
          <slot></slot>
        </div>
        <div class="sentinel" aria-hidden="true"></div>
        <button class="load-more-btn" part="load-more-button"
          style="${loadMode === "scroll" ? "display:none" : ""}">
          ${loadMoreLabel}
        </button>
        <div class="loading-indicator" part="loading-indicator" aria-hidden="true">${loadingLabel}</div>
        <div class="live-region" aria-live="polite" aria-atomic="true"></div>
        <div part="empty" style="display:none"><slot name="empty"></slot></div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._rootEl = this.$(".root")
    this._sentinel = this.$(".sentinel")
    this._loadMoreBtn = this.$(".load-more-btn")
    this._liveRegion = this.$(".live-region")
    this._emptyRegion = this.$("[part='empty']")

    this.listen(this._loadMoreBtn, "click", this._onLoadMore.bind(this))
    this.listen(this, "keydown", this._onKeyDown.bind(this))

    this._setupIntersectionObserver()
    this._syncState()
    this._updateEmptyState()
    return
  }

  onConnected() {
    this._mutationObserver = new MutationObserver((mutations) => {
      let addedCount = 0
      for (const mutation of mutations) {
        addedCount = addedCount + mutation.addedNodes.length
      }
      if (addedCount > 0) {
        this._announceNewItems(addedCount)
      }
      this._updatePositions()
      this._updateEmptyState()
    })
    this._mutationObserver.observe(this, { childList: true })
    return
  }

  onDisconnected() {
    if (this._intersectionObserver !== null) {
      this._intersectionObserver.disconnect()
      this._intersectionObserver = null
    }
    if (this._mutationObserver !== null) {
      this._mutationObserver.disconnect()
      this._mutationObserver = null
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._rootEl !== undefined) {
      this._syncState()
    }
    return
  }

  _syncState() {
    if (this._rootEl === null || this._rootEl === undefined) {
      return
    }

    const loading = this.hasAttribute("loading")
    this._rootEl.setAttribute("aria-busy", loading === true ? "true" : "false")

    if (this._loadMoreBtn !== null) {
      this._loadMoreBtn.disabled = loading === true
    }

    const loadMode = this.getAttribute("load-mode") || "scroll"
    if (this._loadMoreBtn !== null) {
      this._loadMoreBtn.style.display = loadMode === "button" ? "" : "none"
    }
    if (this._sentinel !== null) {
      this._sentinel.style.display = loadMode === "scroll" ? "" : "none"
    }
    return
  }

  _setupIntersectionObserver() {
    if (typeof IntersectionObserver !== "function") {
      return
    }
    if (this._intersectionObserver !== null) {
      this._intersectionObserver.disconnect()
    }
    this._intersectionObserver = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting === true) {
          const loadMode = this.getAttribute("load-mode") || "scroll"
          const loading = this.hasAttribute("loading")
          const hasMore = this.getAttribute("has-more") !== "false"
          if (loadMode === "scroll" && loading === false && hasMore === true) {
            this._onLoadMore()
          }
        }
      }
    }, { rootMargin: "200px" })

    if (this._sentinel !== null) {
      this._intersectionObserver.observe(this._sentinel)
    }
    return
  }

  _onLoadMore() {
    const items = this.items
    this.emit("mj-feed-load-more", { itemCount: items.length })
    return
  }

  _announceNewItems(count) {
    if (this._liveRegion === null) {
      return
    }
    this._liveRegion.textContent = `${count} new item${count > 1 ? "s" : ""} added`
    setTimeout(() => {
      if (this._liveRegion !== null) {
        this._liveRegion.textContent = ""
      }
    }, 3000)
    return
  }

  _updatePositions() {
    const items = this.items
    const total = items.length
    for (let i = 0; i < total; i = i + 1) {
      items[i].setAttribute("aria-posinset", String(i + 1))
      items[i].setAttribute("aria-setsize", String(total))
    }
    return
  }

  _updateEmptyState() {
    const items = this.items
    const loading = this.hasAttribute("loading")
    const isEmpty = items.length === 0 && loading === false
    if (this._emptyRegion !== null) {
      this._emptyRegion.style.display = isEmpty === true ? "" : "none"
    }
    return
  }

  _onKeyDown(event) {
    const items = this.items
    if (items.length === 0) {
      return
    }

    const focused = document.activeElement
    let focusedItemIndex = -1
    for (let i = 0; i < items.length; i = i + 1) {
      if (items[i].contains(focused) === true || items[i] === focused) {
        focusedItemIndex = i
        break
      }
    }

    if (event.key === "PageDown") {
      event.preventDefault()
      const next = Math.min(focusedItemIndex + 1, items.length - 1)
      items[next].focus()
      this.emit("mj-feed-item-focus", { item: items[next], index: next })
    } else if (event.key === "PageUp") {
      event.preventDefault()
      const prev = Math.max(focusedItemIndex - 1, 0)
      items[prev].focus()
      this.emit("mj-feed-item-focus", { item: items[prev], index: prev })
    } else if (event.ctrlKey === true && event.key === "End") {
      event.preventDefault()
      const last = items.length - 1
      items[last].focus()
      this.emit("mj-feed-item-focus", { item: items[last], index: last })
    } else if (event.ctrlKey === true && event.key === "Home") {
      event.preventDefault()
      items[0].focus()
      this.emit("mj-feed-item-focus", { item: items[0], index: 0 })
    }
    return
  }

  get items() {
    const children = Array.from(this.children)
    const feedItems = children.filter((el) => el.tagName.toLowerCase() === "mj-feed-item")
    return feedItems
  }

  get itemCount() {
    return this.items.length
  }
}
