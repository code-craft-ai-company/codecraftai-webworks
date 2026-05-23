/*
 * mjvirtuallist.js
 *
 * <mj-virtual-list> -- arbitrarily large one-dimensional virtualized list.
 * Only visible items + overscan are in the DOM. Supports infinite-scroll,
 * manual load-more, and paged strategies via DataSource adapter.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { DataSource, VirtualWindow } from "../core/collection.js";
import { announce } from "../core/announcer.js";

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
.scroll-container:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); }

.inner { position: relative; }

.vl-item {
  position: absolute;
  width: 100%;
  box-sizing: border-box;
  padding: 0;
  margin: 0;
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
  color: var(--mj-accent);
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

.error-region { color: var(--mj-color-danger); }

.spinner {
  display: inline-block;
  width: 1em; height: 1em;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: vl-spin 0.8s linear infinite;
}
@keyframes vl-spin { to { transform: rotate(360deg); } }
`;

export class MjVirtualList extends MjElement {
  static tagName = "mj-virtual-list";
  static styles = STYLES;
  static watched = ["item-height", "overscan", "page-size", "total", "loading", "error", "end-of-list", "load-more-label", "empty-label", "load-strategy"];

  constructor() {
    super()
    this._items = []
    this._dataSource = null
    this._vw = null
    this._observer = null
    this._renderItem = null
    this._keyExtractor = null
    this._loadOffset = 0
  }

  render() {
    const markup = `
      <div class="scroll-container" part="container" role="feed" aria-busy="false" tabindex="0">
        <div class="inner" part="inner"></div>
        <div class="sentinel" part="sentinel"></div>
        <div class="load-more-area"></div>
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
    this._statusRegion = this.$(".status-region")

    const itemH = parseInt(this.getAttribute("item-height") || "48", 10)
    const overscan = parseInt(this.getAttribute("overscan") || "3", 10)
    this._vw = new VirtualWindow({ rowHeight: itemH, overscan: overscan, total: 0 })

    this.listen(this._container, "scroll", this._onScroll.bind(this))
    this.listen(this._container, "keydown", this._onKeydown.bind(this))

    const strategy = this.getAttribute("load-strategy") || "intersection"
    if (strategy === "intersection" || strategy === "manual") {
      this._buildLoadMore()
    }

    if (strategy === "intersection") {
      this._setupIntersectionObserver()
    }

    if (this._items.length > 0) {
      this._vw.setTotal(this._items.length)
      this._renderWindow()
    } else if (this._dataSource === null) {
      this._showEmpty()
    } else {
      this._fetchNextPage()
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._container === undefined || this._container === null) {
      return
    }
    if (name === "loading") {
      this._container.setAttribute("aria-busy", newValue !== null ? "true" : "false")
    }
    if (name === "end-of-list") {
      this._syncLoadMore()
    }
    return
  }

  _buildLoadMore() {
    const label = this.getAttribute("load-more-label") || "Load more"
    const btn = document.createElement("button")
    btn.className = "load-more-btn"
    btn.setAttribute("part", "load-more-button")
    btn.textContent = label
    this.listen(btn, "click", () => { this._triggerLoadMore() })
    this._loadMoreArea.appendChild(btn)
    this._loadMoreBtn = btn
    return
  }

  _setupIntersectionObserver() {
    if (typeof IntersectionObserver === "undefined") {
      return
    }
    this._observer = new IntersectionObserver((entries) => {
      for (let i = 0; i < entries.length; i = i + 1) {
        const entry = entries[i]
        if (entry.isIntersecting === true) {
          this._triggerLoadMore()
        }
      }
    }, { root: this._container, threshold: 0.1 })
    this._observer.observe(this._sentinel)
    this.onTeardown(() => {
      if (this._observer !== null) {
        this._observer.disconnect()
      }
    })
    return
  }

  _syncLoadMore() {
    if (this._loadMoreBtn === undefined || this._loadMoreBtn === null) {
      return
    }
    const atEnd = this.hasAttribute("end-of-list")
    if (atEnd === true) {
      this._loadMoreBtn.style.display = "none"
    } else {
      this._loadMoreBtn.style.display = ""
    }
    return
  }

  _triggerLoadMore() {
    if (this.hasAttribute("loading") === true || this.hasAttribute("end-of-list") === true) {
      return
    }
    const pageSize = parseInt(this.getAttribute("page-size") || "50", 10)
    this.emit("mj-load-more", { offset: this._loadOffset, pageSize: pageSize })

    if (this._dataSource !== null) {
      this._fetchNextPage()
    }
    return
  }

  _fetchNextPage() {
    const pageSize = parseInt(this.getAttribute("page-size") || "50", 10)
    this.reflectBoolean("loading", true)
    this._container.setAttribute("aria-busy", "true")

    this._dataSource.query({ offset: this._loadOffset, limit: pageSize }).then((result) => {
      this.reflectBoolean("loading", false)
      this._container.setAttribute("aria-busy", "false")

      const newItems = result.items
      this._items = this._items.concat(newItems)
      this._loadOffset = this._items.length

      if (result.total !== undefined && result.total !== null) {
        this._vw.setTotal(result.total)
        this._container.setAttribute("aria-setsize", String(result.total))
      } else {
        this._vw.setTotal(this._items.length)
      }

      if (newItems.length < pageSize) {
        this.reflectBoolean("end-of-list", true)
        announce("End of list reached.")
      } else {
        this.reflectBoolean("end-of-list", false)
      }

      this._renderWindow()
      this._statusRegion.textContent = `${this._items.length} items loaded.`
      return
    }).catch((err) => {
      this.reflectBoolean("loading", false)
      this._container.setAttribute("aria-busy", "false")
      this.reflectBoolean("error", true)
      this._showError()
      announce("Failed to load items.", "assertive")
    })
    return
  }

  _renderWindow() {
    const scrollTop = this._container.scrollTop
    const viewH = this._container.clientHeight || 400
    const win = this._vw.range(scrollTop, viewH)
    const scrollHeight = this._vw.scrollHeight()

    this._inner.style.height = `${scrollHeight}px`
    this._sentinel.style.top = `${scrollHeight - 1}px`

    const existing = Array.from(this._inner.querySelectorAll(".vl-item"))
    const needed = win.end - win.start

    while (existing.length > needed) {
      const removed = existing.pop()
      removed.remove()
    }

    for (let i = win.start; i < win.end; i = i + 1) {
      const item = this._items[i]
      if (item === undefined) {
        continue
      }

      let itemEl = existing[i - win.start]
      if (itemEl === undefined || itemEl === null) {
        itemEl = document.createElement("div")
        itemEl.className = "vl-item"
        itemEl.setAttribute("part", "item")
        itemEl.setAttribute("role", "article")
        itemEl.tabIndex = -1
        this._inner.appendChild(itemEl)
      }

      const top = i * this._vw.rowHeight
      itemEl.style.top = `${top}px`
      itemEl.style.height = `${this._vw.rowHeight}px`
      itemEl.setAttribute("data-index", String(i))
      itemEl.setAttribute("aria-posinset", String(i + 1))

      const total = this._vw.total
      itemEl.setAttribute("aria-setsize", total > 0 ? String(total) : "-1")

      if (this._renderItem !== null) {
        const rendered = this._renderItem(item, i)
        if (typeof rendered === "string") {
          itemEl.innerHTML = rendered
        } else if (rendered instanceof HTMLElement) {
          itemEl.innerHTML = ""
          itemEl.appendChild(rendered)
        }
      } else {
        const label = typeof item === "string" ? item : (item.label || JSON.stringify(item))
        itemEl.textContent = label
      }

      const capturedIdx = i
      const capturedItem = item
      this.listen(itemEl, "click", () => {
        const key = this._keyExtractor !== null ? this._keyExtractor(capturedItem, capturedIdx) : String(capturedIdx)
        this.emit("mj-item-click", { index: capturedIdx, key: key, item: capturedItem })
      })
    }

    this.emit("mj-items-rendered", { startIndex: win.start, endIndex: win.end, total: this._vw.total })

    if (this._items.length === 0) {
      this._showEmpty()
    }
    return
  }

  _showEmpty() {
    this._inner.innerHTML = ""
    const emptyEl = document.createElement("div")
    emptyEl.className = "empty-region"
    emptyEl.setAttribute("part", "empty-state")
    const slot = document.createElement("slot")
    slot.setAttribute("name", "empty")
    emptyEl.appendChild(slot)
    emptyEl.textContent = this.getAttribute("empty-label") || "No items"
    this._inner.appendChild(emptyEl)
    return
  }

  _showError() {
    const errEl = document.createElement("div")
    errEl.className = "error-region"
    errEl.setAttribute("part", "error-state")
    errEl.setAttribute("role", "alert")
    const slot = document.createElement("slot")
    slot.setAttribute("name", "error")
    errEl.appendChild(slot)
    errEl.textContent = "Failed to load items."
    this._loadMoreArea.prepend(errEl)
    return
  }

  _onScroll() {
    window.requestAnimationFrame(() => {
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
    if (event.key === "Home") {
      event.preventDefault()
      this._container.scrollTop = 0
    } else if (event.key === "End") {
      event.preventDefault()
      this._container.scrollTop = this._container.scrollHeight
    } else if (event.key === "PageDown") {
      event.preventDefault()
      this._container.scrollTop = this._container.scrollTop + this._container.clientHeight
    } else if (event.key === "PageUp") {
      event.preventDefault()
      this._container.scrollTop = Math.max(0, this._container.scrollTop - this._container.clientHeight)
    }
    return
  }

  /* ----- scriptable API ----- */

  get items() {
    return this._items
  }

  set items(value) {
    this._items = Array.isArray(value) === true ? value : []
    if (this._vw !== null) {
      this._vw.setTotal(this._items.length)
    }
    if (this._inner !== undefined && this._inner !== null) {
      this._renderWindow()
    }
    return
  }

  get dataSource() {
    return this._dataSource
  }

  set dataSource(value) {
    if (value !== null && value !== undefined) {
      this._dataSource = new DataSource(value)
    } else {
      this._dataSource = null
    }
    if (this._inner !== undefined && this._inner !== null) {
      this._items = []
      this._loadOffset = 0
      this._fetchNextPage()
    }
    return
  }

  get renderItem() {
    return this._renderItem
  }

  set renderItem(fn) {
    this._renderItem = typeof fn === "function" ? fn : null
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
    if (this._vw !== null) {
      this._vw.setTotal(this._items.length)
    }
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
