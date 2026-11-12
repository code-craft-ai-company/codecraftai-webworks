/*
 * mjvirtuallist.js
 *
 * <mj-virtual-list> -- arbitrarily large one-dimensional virtualized list.
 * Only visible items + overscan are in the DOM. Supports infinite-scroll and
 * manual load-more strategies, either host-driven (`mj-load-more` +
 * `appendItems`) or through a `dataSource` (array, fetcher function or adapter
 * object -- see core/collection.js).
 *
 * When the source reports a total the scroller is sized for it and the page
 * that covers the visible range is fetched; without a total, pages are
 * appended one after another.
 *
 * Completeness: a list offers more (Load more button, intersection
 * sentinel, `mj-load-more`) until it is complete. A host-driven list is
 * complete when `end-of-list` is set or when it holds `total` items; a
 * `dataSource` list when the source is exhausted (it then sets
 * `end-of-list` itself). Only a complete list announces `aria-setsize`
 * from what it holds; otherwise the size is `total` or unknown (-1).
 *
 * Follows the WAI-ARIA feed pattern: each item is an `article` in a roving
 * tab order. PageDown / PageUp (and ArrowDown / ArrowUp) move between items,
 * Home / End go to the first / last loaded item, Enter / Space activate the
 * focused item (`mj-item-click`).
 *
 * `renderItem(item, index)` may return a Node, the result of the `html` tag
 * from core/html.js, or a string. A string is inserted AS MARKUP: escape any
 * data you interpolate into it with `escapeHtml` / `html` from core/html.js,
 * or return a Node built with `textContent`.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { DataSource, VirtualWindow } from "../core/collection.js";
import { announce } from "../core/announcer.js";
import { t } from "../core/intl.js";

const STYLES = `
:host {
  display: block;
  height: var(--mj-vl-container-height, 400px);
  font: inherit;
  color: var(--mj-text);
}

.scroll-container {
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  position: relative;
  outline: none;
}

.inner { position: relative; }

.vl-item {
  position: absolute;
  inset-inline: 0;
  box-sizing: border-box;
  padding: 0;
  margin: 0;
  overflow: hidden;
}
.vl-item:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: -2px; }

.sentinel { position: absolute; height: 1px; width: 100%; }

.status-region {
  position: absolute;
  width: 1px; height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}

.load-more-btn {
  display: block;
  width: 100%;
  padding: var(--mj-space-3);
  text-align: center;
  background: var(--mj-surface);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-md);
  cursor: pointer;
  /* --mj-accent as text is under 4.5:1 on the dark --mj-surface. */
  color: var(--mj-text);
  font: inherit;
  font-size: var(--mj-font-size-sm);
}
.load-more-btn:hover { background: var(--mj-bg-muted); }
.load-more-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.load-more-btn[disabled] { opacity: 0.5; cursor: not-allowed; pointer-events: none; }

.end-region, .loading-region, .error-region, .empty-region {
  padding: var(--mj-space-3);
  text-align: center;
  color: var(--mj-text-muted);
  font-size: var(--mj-font-size-sm);
}
.end-region[hidden], .loading-region[hidden], .error-region[hidden] { display: none; }

.error-region { color: var(--mj-color-danger); }

.spinner {
  display: inline-block;
  width: 1em; height: 1em;
  margin-inline-end: var(--mj-space-2);
  vertical-align: middle;
  border: 2px solid currentColor;
  border-inline-end-color: transparent;
  border-radius: 50%;
  animation: vl-spin 0.8s linear infinite;
}
@keyframes vl-spin { to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) {
  .spinner { animation: none; }
}
`;

const DEFAULT_ITEM_HEIGHT = 48;
const DEFAULT_OVERSCAN = 3;
const DEFAULT_PAGE_SIZE = 50;

function parsePositiveInt(text, fallback) {
  const parsed = parseInt(text !== null && text !== undefined ? text : "", 10)
  const value = Number.isNaN(parsed) === true || parsed < 0 ? fallback : parsed
  return value
}

export class MjVirtualList extends MjElement {
  static tagName = "mj-virtual-list";
  static styles = STYLES;
  static watched = ["item-height", "overscan", "page-size", "total", "loading", "error", "end-of-list", "load-more-label", "empty-label", "load-strategy"];

  constructor() {
    super()
    /* In remote mode with a known total this array may have holes. */
    this._items = []
    this._dataSource = null
    this._vw = null
    this._observer = null
    this._renderItem = null
    this._keyExtractor = null

    /* Remote loading state. */
    this._generation = 0
    this._loadedPages = new Set()
    this._pendingPages = new Set()
    this._remoteTotal = null
    this._remoteEnd = false

    /* Rendered item elements by index, and a version to force re-rendering. */
    this._itemEls = new Map()
    this._renderVersion = 0
    this._focusIndex = 0
    this._scrollFrame = 0
    this._listId = nextId("mj-vl")
  }

  /*
   * The scroll container holds the feed and, outside it, the sentinel, the
   * empty state and the load-more area: a feed may own nothing but its
   * articles, so the button, the loading / error / end regions and the
   * empty placeholder are siblings of the role="feed" element (.inner).
   */
  render() {
    const markup = `
      <div class="scroll-container" part="container">
        <div class="inner" part="inner" role="feed" aria-busy="false"></div>
        <div class="sentinel" part="sentinel"></div>
        <div class="load-more-area">
          <div class="loading-region" part="loading-state" hidden>
            <span class="spinner" aria-hidden="true"></span><slot name="loading"></slot>
          </div>
          <div class="error-region" part="error-state" role="alert" hidden>
            <slot name="error"></slot>
          </div>
          <div class="end-region" part="end-state" hidden>
            <slot name="end"></slot>
          </div>
        </div>
      </div>
      <div class="status-region" part="status-region" aria-live="polite" aria-atomic="true"></div>
    `
    return markup
  }

  afterRender() {
    this._container = this.$(".scroll-container")
    this._inner = this.$(".inner")
    this._sentinel = this.$(".sentinel")
    this._loadMoreArea = this.$(".load-more-area")
    this._loadingRegion = this.$(".loading-region")
    this._errorRegion = this.$(".error-region")
    this._endRegion = this.$(".end-region")
    this._statusRegion = this.$(".status-region")
    this.$("slot[name='loading']").textContent = t("mj.virtualList.loading")
    this.$("slot[name='error']").textContent = t("mj.virtualList.loadFailed")
    this.$("slot[name='end']").textContent = t("mj.virtualList.end")
    this._emptyEl = null
    this._loadMoreBtn = null
    this._observer = null
    this._itemEls = new Map()

    const itemH = parsePositiveInt(this.getAttribute("item-height"), DEFAULT_ITEM_HEIGHT) || DEFAULT_ITEM_HEIGHT
    const overscan = parsePositiveInt(this.getAttribute("overscan"), DEFAULT_OVERSCAN)
    this._vw = new VirtualWindow({ rowHeight: itemH, overscan: overscan, total: 0 })

    this.listen(this._container, "scroll", this._onScroll.bind(this))
    this.listen(this._container, "keydown", this._onKeydown.bind(this))
    /* One delegated click listener; the item index is read from the element. */
    this.listen(this._inner, "click", this._onItemClick.bind(this))
    this.listen(this._inner, "focusin", this._onItemFocusIn.bind(this))
    this.onTeardown(() => {
      if (this._scrollFrame !== 0) {
        window.cancelAnimationFrame(this._scrollFrame)
        this._scrollFrame = 0
      }
    })

    this._syncStrategy()
    this._syncStatusRegions()

    if (this._dataSource !== null && this._loadedPages.size === 0) {
      this._resetRemote()
    } else {
      this._applyTotal()
      this._renderWindow()
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._container === undefined || this._container === null) {
      return
    }
    if (name === "loading") {
      this._inner.setAttribute("aria-busy", newValue !== null ? "true" : "false")
      this._syncStatusRegions()
      this._syncFeedRole()
    }
    if (name === "end-of-list" || name === "error") {
      this._syncStatusRegions()
    }
    if (name === "item-height") {
      this._vw.rowHeight = parsePositiveInt(newValue, DEFAULT_ITEM_HEIGHT) || DEFAULT_ITEM_HEIGHT
      this._renderVersion = this._renderVersion + 1
      this._renderWindow()
    }
    if (name === "overscan") {
      this._vw.overscan = parsePositiveInt(newValue, DEFAULT_OVERSCAN)
      this._renderWindow()
    }
    if (name === "total") {
      this._renderVersion = this._renderVersion + 1
      this._renderWindow()
    }
    if (name === "load-more-label") {
      if (this._loadMoreBtn !== null) {
        this._loadMoreBtn.textContent = newValue || t("mj.virtualList.loadMore")
      }
    }
    if (name === "empty-label") {
      this._syncEmpty()
    }
    if (name === "load-strategy") {
      this._syncStrategy()
    }
    return
  }

  /* Move focus to the item that is the list's tab stop. */
  focus(options) {
    const target = this._itemEls !== undefined ? this._itemEls.get(this._focusIndex) : undefined
    if (target !== undefined) {
      target.focus(options)
    } else {
      super.focus(options)
    }
    return
  }

  _pageSize() {
    const size = parsePositiveInt(this.getAttribute("page-size"), DEFAULT_PAGE_SIZE) || DEFAULT_PAGE_SIZE
    return size
  }

  /* ----- load-more button, sentinel, status regions ----- */

  /* Build or remove the load-more button and the sentinel observer. */
  _syncStrategy() {
    const strategy = this.getAttribute("load-strategy") || "intersection"
    const wantsButton = strategy === "intersection" || strategy === "manual"

    if (wantsButton === true && this._loadMoreBtn === null) {
      const btn = document.createElement("button")
      btn.type = "button"
      btn.className = "load-more-btn"
      btn.setAttribute("part", "load-more-button")
      btn.textContent = this.getAttribute("load-more-label") || t("mj.virtualList.loadMore")
      this.listen(btn, "click", () => { this._triggerLoadMore() })
      this._loadMoreArea.appendChild(btn)
      this._loadMoreBtn = btn
    } else if (wantsButton === false && this._loadMoreBtn !== null) {
      this._loadMoreBtn.remove()
      this._loadMoreBtn = null
    }

    if (strategy === "intersection" && this._observer === null) {
      this._setupIntersectionObserver()
    } else if (strategy !== "intersection" && this._observer !== null) {
      this._observer.disconnect()
      this._observer = null
    }

    this._syncStatusRegions()
    return
  }

  _setupIntersectionObserver() {
    if (typeof IntersectionObserver === "undefined") {
      return
    }
    const observer = new IntersectionObserver((entries) => {
      for (let i = 0; i < entries.length; i = i + 1) {
        const entry = entries[i]
        if (entry.isIntersecting === true) {
          this._triggerLoadMore()
        }
      }
    }, { root: this._container, threshold: 0.1 })
    observer.observe(this._sentinel)
    this._observer = observer
    this.onTeardown(() => { observer.disconnect() })
    return
  }

  /*
   * An IntersectionObserver reports changes only. After a page arrives the
   * sentinel may still be visible (short pages), so it is observed afresh to
   * get a new report and load the next page.
   */
  _rearmSentinel() {
    if (this._observer !== null) {
      this._observer.unobserve(this._sentinel)
      this._observer.observe(this._sentinel)
    }
    return
  }

  /*
   * Everything there is to load is loaded (see the file header): the
   * `end-of-list` attribute, or a host-driven list that holds `total` items.
   */
  _isComplete() {
    let complete = this.hasAttribute("end-of-list")
    if (complete === false && this._dataSource === null) {
      const totalAttr = parseInt(this.getAttribute("total") || "", 10)
      complete = Number.isNaN(totalAttr) === false && totalAttr >= 0 && this._items.length >= totalAttr
    }
    return complete
  }

  /* Show the loading / error / end regions and the button as state dictates. */
  _syncStatusRegions() {
    const loading = this.hasAttribute("loading")
    const atEnd = this._isComplete()
    const failed = this.hasAttribute("error")
    const hasItems = this._vw !== null && this._vw.total > 0

    this._loadingRegion.hidden = loading === false
    this._errorRegion.hidden = failed === false
    this._endRegion.hidden = (atEnd === true && hasItems === true && loading === false) === false

    if (this._loadMoreBtn !== null) {
      this._loadMoreBtn.style.display = atEnd === true ? "none" : ""
      this._loadMoreBtn.disabled = loading === true
    }
    return
  }

  /*
   * The inner element is the feed while it owns at least one article or
   * is loading (aria-busy): a feed with neither would be an empty feed,
   * which is invalid. The size of the feed is announced on each article
   * (aria-setsize), never on the feed itself.
   */
  _syncFeedRole() {
    if (this._inner === undefined || this._inner === null) {
      return
    }
    const isFeed = this._itemEls.size > 0 || this.hasAttribute("loading") === true
    if (isFeed === true) {
      this._inner.setAttribute("role", "feed")
    } else {
      this._inner.removeAttribute("role")
    }
    return
  }

  /* The empty placeholder exists only while the list has nothing to show. */
  _syncEmpty() {
    const isEmpty = this._vw.total === 0 && this.hasAttribute("loading") === false

    if (isEmpty === false) {
      if (this._emptyEl !== null) {
        this._emptyEl.remove()
        this._emptyEl = null
      }
      return
    }

    if (this._emptyEl === null) {
      const emptyEl = document.createElement("div")
      emptyEl.className = "empty-region"
      emptyEl.setAttribute("part", "empty-state")
      const slot = document.createElement("slot")
      slot.setAttribute("name", "empty")
      emptyEl.appendChild(slot)
      this._container.insertBefore(emptyEl, this._inner)
      this._emptyEl = emptyEl
    }

    /* Fallback content of the slot: shown unless the host slots its own. */
    this._emptyEl.querySelector("slot").textContent = this.getAttribute("empty-label") || t("mj.virtualList.empty")
    return
  }

  /* ----- loading ----- */

  _triggerLoadMore() {
    if (this.hasAttribute("loading") === true || this._isComplete() === true) {
      return
    }

    if (this._dataSource !== null) {
      const nextPage = this._nextMissingPage()
      if (nextPage >= 0) {
        this._fetchPage(nextPage)
      }
    } else {
      const pageSize = this._pageSize()
      this.emit("mj-load-more", { offset: this._items.length, pageSize: pageSize })
    }
    return
  }

  /* The lowest page index not loaded yet, or -1 when everything is loaded. */
  _nextMissingPage() {
    const pageSize = this._pageSize()
    let pageCount = -1
    if (this._remoteTotal !== null) {
      pageCount = Math.ceil(this._remoteTotal / pageSize)
    }

    let found = -1
    if (this._remoteEnd === false) {
      let page = 0
      while (found < 0 && (pageCount < 0 || page < pageCount)) {
        if (this._loadedPages.has(page) === false) {
          found = page
        }
        page = page + 1
      }
    }
    return found
  }

  /* Forget everything loaded and start again from the first page. */
  _resetRemote() {
    this._generation = this._generation + 1
    this._items = []
    this._loadedPages = new Set()
    this._pendingPages = new Set()
    this._remoteTotal = null
    this._remoteEnd = false
    this._focusIndex = 0
    this._renderVersion = this._renderVersion + 1
    this.reflectBoolean("end-of-list", false)
    this.reflectBoolean("error", false)
    this.reflectBoolean("loading", false)

    if (this._container !== undefined && this._container !== null) {
      this._container.scrollTop = 0
      this._applyTotal()
      this._renderWindow()
      if (this._dataSource !== null) {
        this._fetchPage(0)
      }
    }
    return
  }

  /*
   * Fetch one page from the data source. Responses are tagged with the
   * generation that asked for them; one that arrives after the source was
   * replaced or cleared is ignored.
   */
  _fetchPage(pageIndex) {
    if (this._dataSource === null) {
      return
    }
    if (this._loadedPages.has(pageIndex) === true || this._pendingPages.has(pageIndex) === true) {
      return
    }

    const pageSize = this._pageSize()
    const offset = pageIndex * pageSize
    const generation = this._generation

    this._pendingPages.add(pageIndex)
    this.reflectBoolean("loading", true)
    this.emit("mj-load-more", { offset: offset, pageSize: pageSize })

    this._dataSource.query({ offset: offset, limit: pageSize }).then((result) => {
      if (generation !== this._generation) {
        return
      }
      const newItems = Array.isArray(result.items) === true ? result.items : []
      this._pendingPages.delete(pageIndex)
      this._loadedPages.add(pageIndex)

      for (let i = 0; i < newItems.length; i = i + 1) {
        this._items[offset + i] = newItems[i]
      }

      if (result.total !== undefined && result.total !== null) {
        this._remoteTotal = result.total
      }
      if (this._remoteTotal === null && newItems.length < pageSize) {
        this._remoteEnd = true
      }

      const allLoaded = this._nextMissingPage() < 0
      this.reflectBoolean("error", false)
      this.reflectBoolean("loading", this._pendingPages.size > 0)
      this.reflectBoolean("end-of-list", allLoaded === true)
      if (allLoaded === true) {
        announce(t("mj.virtualList.endReached"))
      }

      this._renderVersion = this._renderVersion + 1
      this._applyTotal()
      this._renderWindow()
      this._rearmSentinel()
      this._statusRegion.textContent = t("mj.virtualList.itemsLoaded", { count: this._loadedCount() })
      return
    }).catch((error) => {
      if (generation !== this._generation) {
        return
      }
      this._pendingPages.delete(pageIndex)
      this.reflectBoolean("loading", this._pendingPages.size > 0)
      this.reflectBoolean("error", true)
      this._syncEmpty()
      this.emit("mj-load-error", { error: error, offset: offset })
      announce(t("mj.virtualList.loadFailed"), "assertive")
    })
    return
  }

  _loadedCount() {
    let count = 0
    for (let i = 0; i < this._items.length; i = i + 1) {
      if (this._items[i] !== undefined) {
        count = count + 1
      }
    }
    return count
  }

  /* Size the virtual window: the reported total, else what is loaded. */
  _applyTotal() {
    if (this._vw === null) {
      return
    }
    let total = this._items.length
    if (this._dataSource !== null && this._remoteTotal !== null) {
      total = this._remoteTotal
    }
    this._vw.setTotal(total)
    return
  }

  /* The size announced to assistive technology (aria-setsize), or -1. */
  _setSize() {
    let size = -1
    if (this._dataSource !== null) {
      if (this._remoteTotal !== null) {
        size = this._remoteTotal
      } else if (this._remoteEnd === true) {
        size = this._items.length
      }
    } else {
      const totalAttr = parseInt(this.getAttribute("total") || "", 10)
      if (Number.isNaN(totalAttr) === false && totalAttr >= this._items.length) {
        size = totalAttr
      } else if (this._isComplete() === true) {
        size = this._items.length
      }
    }
    return size
  }

  /* ----- rendering ----- */

  _renderWindow() {
    const total = this._vw.total
    const viewH = this._container.clientHeight || 400
    const win = this._vw.range(this._container.scrollTop, viewH)
    const scrollHeight = this._vw.scrollHeight()
    const focusWasInside = this._inner.contains(this.shadowRoot.activeElement)

    this._inner.style.height = `${scrollHeight}px`
    this._sentinel.style.top = `${Math.max(0, scrollHeight - 1)}px`

    if (this._focusIndex >= total) {
      this._focusIndex = Math.max(0, total - 1)
    }

    /* The focused item stays rendered while scrolled away so focus survives. */
    const wanted = new Set()
    for (let i = win.start; i < win.end; i = i + 1) {
      wanted.add(i)
    }
    if (total > 0) {
      wanted.add(this._focusIndex)
    }

    const renderedIndexes = Array.from(this._itemEls.keys())
    for (let ri = 0; ri < renderedIndexes.length; ri = ri + 1) {
      const index = renderedIndexes[ri]
      if (wanted.has(index) === false || this._items[index] === undefined) {
        this._itemEls.get(index).remove()
        this._itemEls.delete(index)
      }
    }

    const setSize = this._setSize()
    const missingPages = new Set()

    wanted.forEach((index) => {
      const item = this._items[index]
      if (item === undefined) {
        /* Not loaded yet: ask for the page that holds it. */
        if (this._dataSource !== null && index < total) {
          missingPages.add(Math.floor(index / this._pageSize()))
        }
        return
      }

      let itemEl = this._itemEls.get(index)
      if (itemEl === undefined) {
        itemEl = document.createElement("div")
        itemEl.className = "vl-item"
        itemEl.setAttribute("part", "item")
        itemEl.setAttribute("role", "article")
        itemEl.setAttribute("data-index", String(index))
        itemEl.setAttribute("aria-posinset", String(index + 1))
        this._itemEls.set(index, itemEl)
        this._inner.appendChild(itemEl)
      }

      itemEl.tabIndex = index === this._focusIndex ? 0 : -1
      itemEl.setAttribute("aria-setsize", String(setSize))

      if (itemEl._mjVersion !== this._renderVersion || itemEl._mjItem !== item) {
        itemEl.style.top = `${index * this._vw.rowHeight}px`
        itemEl.style.height = `${this._vw.rowHeight}px`
        this._fillItem(itemEl, item, index)
        itemEl._mjVersion = this._renderVersion
        itemEl._mjItem = item
      }
    })

    missingPages.forEach((pageIndex) => { this._fetchPage(pageIndex) })

    this._syncFeedRole()
    this._syncEmpty()
    this._syncStatusRegions()

    if (focusWasInside === true && this._inner.contains(this.shadowRoot.activeElement) === false) {
      const target = this._itemEls.get(this._focusIndex)
      if (target !== undefined) {
        target.focus({ preventScroll: true })
      }
    }

    this.emit("mj-items-rendered", { startIndex: win.start, endIndex: win.end, total: total })
    return
  }

  /* Render one item's content into its element. */
  _fillItem(itemEl, item, index) {
    if (this._renderItem !== null) {
      const rendered = this._renderItem(item, index)
      if (rendered instanceof Node) {
        itemEl.replaceChildren(rendered)
      } else if (typeof rendered === "string") {
        /* Documented contract: a string is markup the caller has escaped. */
        itemEl.innerHTML = rendered
      } else if (rendered !== null && rendered !== undefined && typeof rendered.markup === "string") {
        /* Result of the `html` tag from core/html.js. */
        itemEl.innerHTML = rendered.markup
      } else if (rendered === null || rendered === undefined) {
        itemEl.replaceChildren()
      } else {
        itemEl.textContent = String(rendered)
      }
    } else {
      let label = ""
      if (item !== null && typeof item === "object") {
        label = item.label !== undefined && item.label !== null ? String(item.label) : JSON.stringify(item)
      } else {
        label = String(item)
      }
      itemEl.textContent = label
    }
    return
  }

  /* ----- interaction ----- */

  _itemFromEvent(event) {
    let itemEl = null
    const target = event.target
    if (target instanceof Element) {
      itemEl = target.closest(".vl-item")
    }
    return itemEl
  }

  _emitItemClick(index) {
    const item = this._items[index]
    if (item === undefined) {
      return
    }
    const key = this._keyExtractor !== null ? this._keyExtractor(item, index) : String(index)
    this.emit("mj-item-click", { index: index, key: key, item: item })
    return
  }

  _onItemClick(event) {
    const itemEl = this._itemFromEvent(event)
    if (itemEl === null) {
      return
    }
    const index = parseInt(itemEl.getAttribute("data-index"), 10)
    this._setFocusIndex(index)
    this._emitItemClick(index)
    return
  }

  /* Focus that lands in an item (click, Tab into its content) moves the tab stop. */
  _onItemFocusIn(event) {
    const itemEl = this._itemFromEvent(event)
    if (itemEl !== null) {
      this._setFocusIndex(parseInt(itemEl.getAttribute("data-index"), 10))
    }
    return
  }

  _setFocusIndex(index) {
    if (index === this._focusIndex) {
      return
    }
    const previous = this._itemEls.get(this._focusIndex)
    if (previous !== undefined) {
      previous.tabIndex = -1
    }
    this._focusIndex = index
    const current = this._itemEls.get(index)
    if (current !== undefined) {
      current.tabIndex = 0
    }
    return
  }

  /* Scroll item `index` into view, render it and give it focus. */
  _focusItem(index) {
    const total = this._vw.total
    if (total === 0) {
      return
    }
    const clamped = Math.max(0, Math.min(index, total - 1))
    const itemH = this._vw.rowHeight
    const top = clamped * itemH
    const viewH = this._container.clientHeight

    if (top < this._container.scrollTop) {
      this._container.scrollTop = top
    } else if (top + itemH > this._container.scrollTop + viewH) {
      this._container.scrollTop = top + itemH - viewH
    }

    this._setFocusIndex(clamped)
    this._renderWindow()

    const target = this._itemEls.get(clamped)
    if (target !== undefined) {
      target.focus()
    }
    return
  }

  _onScroll() {
    if (this._scrollFrame !== 0) {
      return
    }
    this._scrollFrame = window.requestAnimationFrame(() => {
      this._scrollFrame = 0
      this._renderWindow()
      const scrollTop = this._container.scrollTop
      const scrollHeight = this._container.scrollHeight
      const clientH = this._container.clientHeight
      if (scrollTop + clientH >= scrollHeight - 50) {
        this.emit("mj-scroll-end", { scrollTop: scrollTop })
      }
    })
    return
  }

  _onKeydown(event) {
    const itemEl = this._itemFromEvent(event)
    if (itemEl === null) {
      return
    }
    const key = event.key
    const onItemItself = event.target === itemEl
    const index = parseInt(itemEl.getAttribute("data-index"), 10)

    /* Feed pattern: PageDown / PageUp work from anywhere inside an article. */
    if (key === "PageDown") {
      event.preventDefault()
      this._focusItem(index + 1)
    } else if (key === "PageUp") {
      event.preventDefault()
      this._focusItem(index - 1)
    } else if (onItemItself === true) {
      /* The remaining keys must not be taken from controls inside an item. */
      if (key === "ArrowDown") {
        event.preventDefault()
        this._focusItem(index + 1)
      } else if (key === "ArrowUp") {
        event.preventDefault()
        this._focusItem(index - 1)
      } else if (key === "Home") {
        event.preventDefault()
        this._focusItem(0)
      } else if (key === "End") {
        event.preventDefault()
        this._focusItem(this._lastLoadedIndex())
      } else if (key === "Enter" || key === " ") {
        event.preventDefault()
        this._emitItemClick(index)
      }
    }
    return
  }

  _lastLoadedIndex() {
    let last = 0
    for (let i = this._items.length - 1; i >= 0; i = i - 1) {
      if (this._items[i] !== undefined) {
        last = i
        break
      }
    }
    return last
  }

  /* ----- scriptable API ----- */

  get items() {
    return this._items
  }

  set items(value) {
    this._items = Array.isArray(value) === true ? value : []
    this._renderVersion = this._renderVersion + 1
    this._applyTotal()
    if (this._inner !== undefined && this._inner !== null) {
      this._renderWindow()
    }
    return
  }

  get dataSource() {
    return this._dataSource
  }

  /*
   * An array, a fetcher `({ offset, limit }) => Promise<{ items, total }>`, or
   * an adapter object exposing `query({ offset, limit })` / `fetch(...)`.
   * Assigning null clears the list.
   */
  set dataSource(value) {
    if (value instanceof DataSource) {
      this._dataSource = value
    } else if (value !== null && value !== undefined) {
      this._dataSource = new DataSource(value)
    } else {
      this._dataSource = null
    }
    this._resetRemote()
    return
  }

  get renderItem() {
    return this._renderItem
  }

  set renderItem(fn) {
    this._renderItem = typeof fn === "function" ? fn : null
    this._renderVersion = this._renderVersion + 1
    if (this._inner !== undefined && this._inner !== null) {
      this._renderWindow()
    }
    return
  }

  get keyExtractor() {
    return this._keyExtractor
  }

  set keyExtractor(fn) {
    this._keyExtractor = typeof fn === "function" ? fn : null
    return
  }

  appendItems(newItems) {
    const arr = Array.isArray(newItems) === true ? newItems : []
    this._items = this._items.concat(arr)
    this._applyTotal()
    if (this._inner !== undefined && this._inner !== null) {
      this._renderWindow()
    }
    return
  }

  get loading() {
    return this.hasAttribute("loading")
  }

  set loading(value) {
    this.reflectBoolean("loading", value === true)
    return
  }
}
