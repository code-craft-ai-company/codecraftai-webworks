/*
 * mjmasterdetail.js
 *
 * <mj-master-detail> -- split-panel layout with a master list and a contextual
 * detail view. Responsive: side-by-side above breakpoint, stacked below.
 * Resizable divider, keyboard navigation, ARIA group/navigation/separator semantics.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";

const STYLES = `
:host {
  display: block;
  font: inherit;
  color: var(--mj-text);
  height: 100%;
}

.root {
  display: flex;
  height: 100%;
  overflow: hidden;
}

:host([layout="stacked"]) .root {
  flex-direction: column;
}

.master-panel {
  width: var(--mj-md-master-width, 320px);
  min-width: var(--mj-md-master-min-width, 200px);
  max-width: var(--mj-md-master-max-width, 60%);
  overflow-y: auto;
  overflow-x: hidden;
  flex-shrink: 0;
  border-inline-end: 1px solid var(--mj-border);
  background: var(--mj-surface);
  display: flex;
  flex-direction: column;
}

:host([layout="stacked"]) .master-panel {
  width: 100%;
  max-width: 100%;
  border-inline-end: none;
  border-block-end: 1px solid var(--mj-border);
  flex: 1;
}

:host([layout="stacked"]) .master-panel[aria-hidden="true"] { display: none; }
:host([layout="stacked"]) .detail-panel[aria-hidden="true"] { display: none; }

.divider {
  width: var(--mj-md-divider-width, 4px);
  background: var(--mj-md-divider-color, var(--mj-border));
  cursor: col-resize;
  flex-shrink: 0;
  transition: background var(--mj-motion-fast);
}
.divider:hover, .divider:focus { background: var(--mj-accent); }
.divider:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
:host([layout="stacked"]) .divider { display: none; }

.detail-panel {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  background: var(--mj-md-detail-bg, var(--mj-surface));
  position: relative;
}

.back-btn {
  display: none;
  align-items: center;
  gap: var(--mj-space-2);
  padding: var(--mj-space-2) var(--mj-space-3);
  background: var(--mj-surface);
  border: none;
  border-bottom: 1px solid var(--mj-border);
  cursor: pointer;
  font: inherit;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-accent);
  width: 100%;
  text-align: start;
}
:host([layout="stacked"]) .back-btn { display: flex; }
.back-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.master-list {
  flex: 1;
  list-style: none;
  margin: 0;
  padding: var(--mj-space-2) 0;
}

.master-item {
  display: flex;
  align-items: center;
  padding: var(--mj-space-2) var(--mj-space-3);
  cursor: pointer;
  font-size: var(--mj-font-size-sm);
  gap: var(--mj-space-2);
  user-select: none;
  transition: background var(--mj-motion-fast);
}
.master-item:hover { background: var(--mj-bg-muted); }
.master-item:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: -2px;
}
.master-item[aria-selected="true"] {
  background: var(--mj-md-selected-item-bg, color-mix(in srgb, var(--mj-accent) 10%, transparent));
  color: var(--mj-text);
}

.item-label { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.item-meta { font-size: var(--mj-font-size-xs); color: var(--mj-text-muted); }

.detail-content { padding: var(--mj-space-4); }
.detail-empty { padding: var(--mj-space-7); text-align: center; color: var(--mj-text-muted); }
.detail-loading { padding: var(--mj-space-4); display: flex; align-items: center; gap: var(--mj-space-2); color: var(--mj-text-muted); }

.spinner {
  display: inline-block;
  width: 1em; height: 1em;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: md-spin 0.8s linear infinite;
}
@keyframes md-spin { to { transform: rotate(360deg); } }

.status-region {
  position: absolute; width: 1px; height: 1px;
  overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap;
}
`;

export class MjMasterDetail extends MjElement {
  static tagName = "mj-master-detail";
  static styles = STYLES;
  static watched = ["layout", "master-type", "selected-key", "resizable", "loading-detail", "master-label", "detail-label", "back-label"];

  constructor() {
    super()
    this._items = []
    this._columns = []
    this._dataSource = null
    this._detailDataSource = null
    this._resizeObserver = null
    this._isResizing = false
    this._currentAbortController = null
    this._stacked = false
    this._stackView = "master"
  }

  render() {
    const masterLabel = this.getAttribute("master-label") || "List"
    const detailLabel = this.getAttribute("detail-label") || "Detail"
    const backLabel = this.getAttribute("back-label") || "Back"

    const markup = `
      <div class="root" part="root" role="group" aria-label="Master detail view">
        <section class="master-panel" part="master-panel"
                 aria-label="${masterLabel}">
          <ul class="master-list" role="list" aria-label="${masterLabel}"></ul>
          <slot name="master"></slot>
        </section>
        <div class="divider" part="divider"
             role="separator"
             aria-orientation="vertical"
             aria-label="Resize panels"
             aria-valuenow="320"
             aria-valuemin="200"
             aria-valuemax="800"
             tabindex="0"></div>
        <section class="detail-panel" part="detail-panel"
                 aria-label="${detailLabel}">
          <button class="back-btn" part="back-button" aria-label="${backLabel}">
            ← ${backLabel}
          </button>
          <div class="detail-content">
            <div class="detail-empty" part="detail-empty">
              <slot name="detail-empty">Select an item to view details.</slot>
            </div>
            <div class="detail-loading" style="display:none" part="detail-loading">
              <span class="spinner" aria-hidden="true"></span>
              <slot name="detail-loading">Loading…</slot>
            </div>
            <div class="detail-data" style="display:none">
              <slot name="detail"></slot>
            </div>
          </div>
        </section>
      </div>
      <div class="status-region" aria-live="polite" aria-atomic="true"></div>
    `
    return markup
  }

  afterRender() {
    this._root = this.$(".root")
    this._masterPanel = this.$(".master-panel")
    this._masterList = this.$(".master-list")
    this._divider = this.$(".divider")
    this._detailPanel = this.$(".detail-panel")
    this._backBtn = this.$(".back-btn")
    this._detailEmpty = this.$(".detail-empty")
    this._detailLoading = this.$(".detail-loading")
    this._detailData = this.$(".detail-data")
    this._statusRegion = this.$(".status-region")

    this.listen(this._backBtn, "click", () => { this._goToMaster() })
    this.listen(this._backBtn, "keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault()
        this._goToMaster()
      }
    })

    if (this.hasAttribute("resizable") !== false) {
      this._setupDividerResize()
    }

    this._setupResizeObserver()
    this._syncLayout()

    if (this._items.length > 0) {
      this._renderMasterList()
    }

    const selectedKey = this.getAttribute("selected-key")
    if (selectedKey !== null && selectedKey.length > 0) {
      this._selectItem(selectedKey)
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._root === undefined || this._root === null) {
      return
    }
    if (name === "layout") {
      this._syncLayout()
    }
    if (name === "selected-key" && newValue !== null && newValue.length > 0) {
      this._selectItem(newValue)
    }
    if (name === "loading-detail") {
      this._syncDetailState()
    }
    if (name === "master-label") {
      this._masterPanel.setAttribute("aria-label", newValue || "List")
      this._masterList.setAttribute("aria-label", newValue || "List")
    }
    if (name === "detail-label") {
      this._updateDetailLabel(null)
    }
    if (name === "back-label") {
      this._backBtn.setAttribute("aria-label", newValue || "Back")
      this._backBtn.textContent = `← ${newValue || "Back"}`
    }
    return
  }

  _syncLayout() {
    const layout = this.getAttribute("layout") || "auto"
    if (layout === "side-by-side") {
      this._stacked = false
      this.setAttribute("layout", "side-by-side")
    } else if (layout === "stacked") {
      this._stacked = true
    }
    return
  }

  _setupResizeObserver() {
    if (typeof ResizeObserver === "undefined") {
      return
    }
    const breakpoint = 640
    this._resizeObserver = new ResizeObserver((entries) => {
      const entry = entries[0]
      if (entry === undefined) {
        return
      }
      const width = entry.contentRect.width
      const layout = this.getAttribute("layout") || "auto"
      if (layout !== "auto") {
        return
      }
      const shouldStack = width < breakpoint
      if (shouldStack !== this._stacked) {
        this._stacked = shouldStack
        const newLayout = shouldStack === true ? "stacked" : "side-by-side"
        this.setAttribute("layout", newLayout)
        this.emit("mj-layout-change", { layout: newLayout })
      }
    })
    this._resizeObserver.observe(this)
    this.onTeardown(() => { this._resizeObserver.disconnect() })
    return
  }

  _setupDividerResize() {
    let startX = 0
    let startWidth = 0

    const onMove = (e) => {
      const delta = e.clientX - startX
      const minW = 200
      const maxW = this._root.offsetWidth * 0.6
      const newW = Math.max(minW, Math.min(maxW, startWidth + delta))
      this._masterPanel.style.width = `${newW}px`
      this._divider.setAttribute("aria-valuenow", String(Math.round(newW)))
    }

    const onUp = (e) => {
      document.removeEventListener("pointermove", onMove)
      document.removeEventListener("pointerup", onUp)
      const finalWidth = parseFloat(this._masterPanel.style.width) || 320
      this.emit("mj-panel-resize", { masterWidth: finalWidth })
    }

    this.listen(this._divider, "pointerdown", (e) => {
      if (this._stacked === true) {
        return
      }
      startX = e.clientX
      startWidth = this._masterPanel.offsetWidth
      document.addEventListener("pointermove", onMove)
      document.addEventListener("pointerup", onUp)
    })

    this.listen(this._divider, "keydown", (e) => {
      const currentW = this._masterPanel.offsetWidth
      const minW = 200
      const maxW = this._root.offsetWidth * 0.6
      if (e.key === "ArrowLeft") {
        e.preventDefault()
        const newW = Math.max(minW, currentW - 8)
        this._masterPanel.style.width = `${newW}px`
        this._divider.setAttribute("aria-valuenow", String(newW))
      } else if (e.key === "ArrowRight") {
        e.preventDefault()
        const newW = Math.min(maxW, currentW + 8)
        this._masterPanel.style.width = `${newW}px`
        this._divider.setAttribute("aria-valuenow", String(newW))
      } else if (e.key === "Home") {
        e.preventDefault()
        this._masterPanel.style.width = `${minW}px`
        this._divider.setAttribute("aria-valuenow", String(minW))
      } else if (e.key === "End") {
        e.preventDefault()
        this._masterPanel.style.width = `${Math.round(maxW)}px`
        this._divider.setAttribute("aria-valuenow", String(Math.round(maxW)))
      }
    })
    return
  }

  _renderMasterList() {
    this._masterList.innerHTML = ""
    for (let idx = 0; idx < this._items.length; idx = idx + 1) {
      const item = this._items[idx]
      const li = document.createElement("li")
      li.className = "master-item"
      li.setAttribute("part", "master-item")
      li.setAttribute("role", "listitem")
      li.setAttribute("tabindex", "0")
      li.setAttribute("data-key", item.key)
      li.setAttribute("aria-selected", "false")

      const labelEl = document.createElement("span")
      labelEl.className = "item-label"
      labelEl.textContent = item.label

      li.appendChild(labelEl)

      if (item.meta !== undefined) {
        const metaEl = document.createElement("span")
        metaEl.className = "item-meta"
        metaEl.textContent = item.meta
        li.appendChild(metaEl)
      }

      this.listen(li, "click", () => {
        this._handleItemClick(item)
      })

      this.listen(li, "keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault()
          this._handleItemClick(item)
        } else if (e.key === "ArrowDown") {
          e.preventDefault()
          const next = li.nextElementSibling
          if (next !== null) {
            next.focus()
          }
        } else if (e.key === "ArrowUp") {
          e.preventDefault()
          const prev = li.previousElementSibling
          if (prev !== null) {
            prev.focus()
          }
        }
      })

      this._masterList.appendChild(li)
    }
    return
  }

  _handleItemClick(item) {
    const proceed = this.emit("mj-item-select", { key: item.key, item: item }, { cancelable: true })
    if (proceed === false) {
      return
    }
    this.setAttribute("selected-key", item.key)
    this._selectItem(item.key)
    return
  }

  _selectItem(key) {
    const items = this._masterList.querySelectorAll(".master-item")
    for (let i = 0; i < items.length; i = i + 1) {
      const item = items[i]
      item.setAttribute("aria-selected", item.getAttribute("data-key") === key ? "true" : "false")
    }

    const selectedItem = this._items.find((it) => it.key === key)
    const itemLabel = selectedItem !== undefined ? selectedItem.label : key
    this._updateDetailLabel(itemLabel)

    if (this._stacked === true) {
      this._goToDetail()
    }

    this._loadDetail(key, itemLabel)
    return
  }

  _loadDetail(key, itemLabel) {
    if (this._detailDataSource !== null && typeof this._detailDataSource === "function") {
      if (this._currentAbortController !== null) {
        this._currentAbortController.abort()
      }
      this._currentAbortController = typeof AbortController !== "undefined" ? new AbortController() : null
      this._showDetailLoading()

      this._detailDataSource(key).then((data) => {
        this._currentAbortController = null
        const slot = this.$("slot[name='detail']")
        if (slot !== null) {
          slot.host = data
        }
        this.emit("mj-detail-load", { key: key, data: data })
        this._showDetailData()
        this._statusRegion.textContent = `Showing detail for ${itemLabel}`
        announce(`Showing detail for ${itemLabel}`)
        return
      }).catch((err) => {
        this._currentAbortController = null
        this._showDetailError()
        this.emit("mj-detail-error", { key: key, error: err })
      })
    } else {
      this._showDetailData()
      this._statusRegion.textContent = `Showing detail for ${itemLabel}`
      announce(`Showing detail for ${itemLabel}`)
    }
    return
  }

  _showDetailLoading() {
    this._detailEmpty.style.display = "none"
    this._detailLoading.style.display = "flex"
    this._detailData.style.display = "none"
    this._detailPanel.setAttribute("aria-busy", "true")
    return
  }

  _showDetailData() {
    this._detailEmpty.style.display = "none"
    this._detailLoading.style.display = "none"
    this._detailData.style.display = ""
    this._detailPanel.setAttribute("aria-busy", "false")
    return
  }

  _showDetailError() {
    this._detailEmpty.style.display = "none"
    this._detailLoading.style.display = "none"
    this._detailData.style.display = "none"
    this._detailPanel.setAttribute("aria-busy", "false")
    const errEl = document.createElement("div")
    errEl.className = "detail-empty"
    errEl.setAttribute("part", "detail-error")
    const slot = document.createElement("slot")
    slot.setAttribute("name", "detail-error")
    errEl.appendChild(slot)
    errEl.textContent = "Failed to load details."
    this._detailPanel.querySelector(".detail-content").appendChild(errEl)
    return
  }

  _syncDetailState() {
    if (this.hasAttribute("loading-detail") === true) {
      this._showDetailLoading()
    }
    return
  }

  _updateDetailLabel(itemLabel) {
    const base = this.getAttribute("detail-label") || "Detail"
    const label = itemLabel !== null ? `${base}: ${itemLabel}` : base
    this._detailPanel.setAttribute("aria-label", label)
    return
  }

  _goToDetail() {
    this._stackView = "detail"
    this._masterPanel.setAttribute("aria-hidden", "true")
    this._masterPanel.setAttribute("inert", "")
    this._detailPanel.removeAttribute("aria-hidden")
    this._detailPanel.removeAttribute("inert")
    return
  }

  _goToMaster() {
    this._stackView = "master"
    this._masterPanel.removeAttribute("aria-hidden")
    this._masterPanel.removeAttribute("inert")
    this._detailPanel.setAttribute("aria-hidden", "true")
    this._detailPanel.setAttribute("inert", "")
    this.emit("mj-back", {})
    return
  }

  /* ----- scriptable API ----- */

  get items() {
    return this._items
  }

  set items(value) {
    this._items = Array.isArray(value) === true ? value : []
    if (this._masterList !== undefined && this._masterList !== null) {
      this._renderMasterList()
    }
    return
  }

  get columns() {
    return this._columns
  }

  set columns(value) {
    this._columns = Array.isArray(value) === true ? value : []
    return
  }

  get dataSource() {
    return this._dataSource
  }

  set dataSource(value) {
    this._dataSource = value !== null && value !== undefined ? value : null
    return
  }

  get detailDataSource() {
    return this._detailDataSource
  }

  set detailDataSource(fn) {
    this._detailDataSource = typeof fn === "function" ? fn : null
    return
  }
}
