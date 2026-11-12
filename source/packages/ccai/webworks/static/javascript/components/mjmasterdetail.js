/*
 * mjmasterdetail.js
 *
 * <mj-master-detail> -- split-panel layout with a master list and a contextual
 * detail view. Responsive: side-by-side above the breakpoint, stacked below.
 * Resizable divider, keyboard navigation, listbox / separator semantics.
 *
 * `layout` is the author's choice (auto | side-by-side | stacked) and is never
 * rewritten by the component. The layout in effect is exposed on the shadow
 * root element (`data-layout`), through the `resolvedLayout` property and the
 * `mj-layout-change` event.
 *
 * The master list is a listbox with one tab stop: ArrowUp / ArrowDown / Home /
 * End move between items, Enter / Space select. `detailDataSource(key,
 * { signal })` loads the detail; a newer selection aborts the signal and the
 * stale result is ignored. The loaded value is available as `detailData`.
 *
 * Not implemented yet: `master-type="table"` (the `columns` / `dataSource`
 * properties are stored for it but unused).
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";
import { t } from "../core/intl.js";

const STYLES = `
:host {
  display: block;
  font: inherit;
  color: var(--mj-text);
  height: 100%;
}

/*
 * As a dock band the host must not claim the whole dock container along the
 * axis the band consumes (see static/styles/base.css, Docking).
 */
:host([dock="top"]),
:host([dock="bottom"]) {
  block-size: auto;
}

.root {
  display: flex;
  height: 100%;
  overflow: hidden;
}

.root[data-layout="stacked"] {
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

.root[data-layout="stacked"] .master-panel {
  width: 100%;
  max-width: 100%;
  border-inline-end: none;
  border-block-end: 1px solid var(--mj-border);
  flex: 1;
}

.root[data-layout="stacked"] .master-panel[aria-hidden="true"] { display: none; }
.root[data-layout="stacked"] .detail-panel[aria-hidden="true"] { display: none; }

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
.root[data-layout="stacked"] .divider { display: none; }
.divider:not([tabindex]) { cursor: default; }
.divider:not([tabindex]):hover { background: var(--mj-md-divider-color, var(--mj-border)); }

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
  border-block-end: 1px solid var(--mj-border);
  cursor: pointer;
  font: inherit;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-accent);
  width: 100%;
  text-align: start;
}
.root[data-layout="stacked"] .back-btn { display: flex; }
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
.detail-error { padding: var(--mj-space-7); text-align: center; color: var(--mj-color-danger); }
.detail-empty[hidden], .detail-loading[hidden], .detail-data[hidden], .detail-error[hidden] { display: none; }

.spinner {
  display: inline-block;
  width: 1em; height: 1em;
  border: 2px solid currentColor;
  border-inline-end-color: transparent;
  border-radius: 50%;
  animation: md-spin 0.8s linear infinite;
}
@keyframes md-spin { to { transform: rotate(360deg); } }
`;

const DEFAULT_BREAKPOINT = 640;
const MASTER_MIN_WIDTH = 200;
const RESIZE_STEP = 8;

export class MjMasterDetail extends MjElement {
  static tagName = "mj-master-detail";
  static styles = STYLES;
  static watched = [
    "layout", "breakpoint", "master-type", "master-width", "selected-key", "resizable",
    "loading-detail", "master-label", "detail-label", "back-label"
  ];

  constructor() {
    super()
    this._items = []
    this._columns = []
    this._dataSource = null
    this._detailDataSource = null
    this._resizeObserver = null
    this._resizeDrag = null
    this._currentAbortController = null

    /* Layout in effect and, when stacked, which panel is showing. */
    this._stacked = false
    this._stackView = "master"

    /* Selection (as text), the item the roving tab stop is on, detail state. */
    this._selectedKey = null
    this._focusKey = null
    this._detailState = "empty"
    this._detailData = undefined
    this._loadGeneration = 0

    /* True while a click / key press is being turned into a selection. */
    this._userSelecting = false
  }

  render() {
    /* Labels are applied in afterRender with setAttribute / textContent. */
    const markup = `
      <div class="root" part="root" role="group" data-layout="side-by-side">
        <section class="master-panel" part="master-panel">
          <ul class="master-list" role="listbox"></ul>
          <slot name="master"></slot>
        </section>
        <div class="divider" part="divider" role="separator" aria-orientation="vertical"></div>
        <section class="detail-panel" part="detail-panel">
          <button type="button" class="back-btn" part="back-button">
            <span aria-hidden="true">←</span>
            <span class="back-label"></span>
          </button>
          <div class="detail-content">
            <div class="detail-empty" part="detail-empty">
              <slot name="detail-empty"></slot>
            </div>
            <div class="detail-loading" part="detail-loading" hidden>
              <span class="spinner" aria-hidden="true"></span>
              <slot name="detail-loading"></slot>
            </div>
            <div class="detail-error" part="detail-error" role="alert" hidden>
              <slot name="detail-error"></slot>
            </div>
            <div class="detail-data" hidden>
              <slot name="detail"></slot>
            </div>
          </div>
        </section>
      </div>
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
    this._backLabel = this.$(".back-label")
    this._detailEmpty = this.$(".detail-empty")
    this._detailLoading = this.$(".detail-loading")
    this._detailError = this.$(".detail-error")
    this._detailDataEl = this.$(".detail-data")
    this._root.setAttribute("aria-label", t("mj.masterDetail.label"))
    this.$("slot[name='detail-empty']").textContent = t("mj.masterDetail.detailEmpty")
    this.$("slot[name='detail-loading']").textContent = t("mj.masterDetail.detailLoading")
    this.$("slot[name='detail-error']").textContent = t("mj.masterDetail.detailError")

    /* A native <button> clicks on Enter / Space. */
    this.listen(this._backBtn, "click", () => { this._goToMaster(true) })

    /* Delegated listeners: the list is rebuilt whenever `items` changes. */
    this.listen(this._masterList, "click", this._onListClick.bind(this))
    this.listen(this._masterList, "keydown", this._onListKeydown.bind(this))

    this._setupDividerResize()
    this._setupResizeObserver()

    this._syncLabels()
    this._syncMasterWidth()
    this._syncDivider()
    this._renderMasterList()
    this._applyLayout(false)
    this._applyDetailState()

    const selectedKey = this.getAttribute("selected-key")
    if (selectedKey !== null && selectedKey.length > 0) {
      this._selectItem(selectedKey, false, false)
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._root === undefined || this._root === null) {
      return
    }
    if (name === "layout" || name === "breakpoint") {
      this._applyLayout(true)
    }
    if (name === "selected-key") {
      if (newValue !== null && newValue.length > 0) {
        this._selectItem(newValue, false, false)
      } else {
        this._clearSelection()
      }
    }
    if (name === "loading-detail") {
      this._applyDetailState()
    }
    if (name === "master-label" || name === "detail-label" || name === "back-label") {
      this._syncLabels()
    }
    if (name === "master-width") {
      this._syncMasterWidth()
    }
    if (name === "resizable") {
      this._syncDivider()
    }
    return
  }

  /* ----- labels and static state ----- */

  _selectedItem() {
    let found = undefined
    if (this._selectedKey !== null) {
      found = this._items.find((it) => String(it.key) === this._selectedKey)
    }
    return found
  }

  _syncLabels() {
    const masterLabel = this.getAttribute("master-label") || t("mj.masterDetail.masterLabel")
    const backLabel = this.getAttribute("back-label") || t("mj.masterDetail.back")
    this._masterPanel.setAttribute("aria-label", masterLabel)
    this._masterList.setAttribute("aria-label", masterLabel)
    this._backBtn.setAttribute("aria-label", backLabel)
    this._backLabel.textContent = backLabel

    const selected = this._selectedItem()
    let itemLabel = null
    if (selected !== undefined) {
      itemLabel = selected.label
    } else if (this._selectedKey !== null) {
      itemLabel = this._selectedKey
    }
    this._updateDetailLabel(itemLabel)
    return
  }

  _updateDetailLabel(itemLabel) {
    const base = this.getAttribute("detail-label") || t("mj.masterDetail.detailLabel")
    const label = itemLabel !== null && itemLabel !== undefined ? t("mj.masterDetail.detailItemLabel", { label: base, item: itemLabel }) : base
    this._detailPanel.setAttribute("aria-label", label)
    return
  }

  /* `master-width`: a number of pixels or any CSS length. */
  _syncMasterWidth() {
    const raw = this.getAttribute("master-width")
    if (raw !== null && raw.trim().length > 0) {
      const isNumber = /^\d+(\.\d+)?$/.test(raw.trim())
      this._masterPanel.style.width = isNumber === true ? `${raw.trim()}px` : raw.trim()
    } else if (this._resizeDrag === null) {
      this._masterPanel.style.width = ""
    }
    return
  }

  _isResizable() {
    const resizable = this.hasAttribute("resizable") === true && this.getAttribute("resizable") !== "false"
    return resizable
  }

  /*
   * The divider is an interactive separator (focusable, with a value) only
   * while the panels are side by side and `resizable` is set.
   */
  _syncDivider() {
    const interactive = this._isResizable() === true && this._stacked === false
    if (interactive === true) {
      const maxW = Math.round(this._root.offsetWidth * 0.6)
      this._divider.tabIndex = 0
      this._divider.setAttribute("aria-label", t("mj.masterDetail.resize"))
      this._divider.setAttribute("aria-valuemin", String(MASTER_MIN_WIDTH))
      this._divider.setAttribute("aria-valuemax", String(Math.max(MASTER_MIN_WIDTH, maxW)))
      this._divider.setAttribute("aria-valuenow", String(Math.round(this._masterPanel.offsetWidth)))
    } else {
      this._divider.removeAttribute("tabindex")
      this._divider.removeAttribute("aria-label")
      this._divider.removeAttribute("aria-valuemin")
      this._divider.removeAttribute("aria-valuemax")
      this._divider.removeAttribute("aria-valuenow")
    }
    return
  }

  /* ----- layout ----- */

  _breakpoint() {
    const parsed = parseInt(this.getAttribute("breakpoint") || "", 10)
    const breakpoint = Number.isNaN(parsed) === true || parsed <= 0 ? DEFAULT_BREAKPOINT : parsed
    return breakpoint
  }

  /*
   * Resolve the layout from the author's `layout` value and the current
   * width, and bring both panels in line with it. The `layout` attribute
   * itself is never written, so `auto` keeps following the width.
   */
  _applyLayout(notify) {
    const layout = this.getAttribute("layout") || "auto"
    let stacked = false
    if (layout === "stacked") {
      stacked = true
    } else if (layout === "side-by-side") {
      stacked = false
    } else {
      const width = this.getBoundingClientRect().width
      stacked = width > 0 && width < this._breakpoint()
    }

    const changed = stacked !== this._stacked
    this._stacked = stacked
    this._root.setAttribute("data-layout", stacked === true ? "stacked" : "side-by-side")
    this._syncPanels()
    this._syncDivider()

    if (changed === true && notify === true) {
      this.emit("mj-layout-change", { layout: this.resolvedLayout })
    }
    return
  }

  /* Side by side both panels are live; stacked only the current one is. */
  _syncPanels() {
    const hideMaster = this._stacked === true && this._stackView === "detail"
    const hideDetail = this._stacked === true && this._stackView === "master"
    this._setPanelHidden(this._masterPanel, hideMaster)
    this._setPanelHidden(this._detailPanel, hideDetail)
    return
  }

  _setPanelHidden(panel, hidden) {
    if (hidden === true) {
      panel.setAttribute("aria-hidden", "true")
      panel.setAttribute("inert", "")
    } else {
      panel.removeAttribute("aria-hidden")
      panel.removeAttribute("inert")
    }
    return
  }

  _setupResizeObserver() {
    if (typeof ResizeObserver === "undefined") {
      return
    }
    const observer = new ResizeObserver(() => {
      this._applyLayout(true)
    })
    observer.observe(this)
    this._resizeObserver = observer
    this.onTeardown(() => { observer.disconnect() })
    return
  }

  _goToDetail(moveFocus) {
    this._stackView = "detail"
    this._syncPanels()
    if (moveFocus === true && this._stacked === true) {
      this._backBtn.focus()
    }
    return
  }

  _goToMaster(moveFocus) {
    this._stackView = "master"
    this._syncPanels()
    if (moveFocus === true) {
      const target = this._tabStopItem()
      if (target !== null) {
        target.focus()
      }
    }
    this.emit("mj-back", {})
    return
  }

  /* ----- divider resize ----- */

  _setMasterWidth(width) {
    const maxW = Math.max(MASTER_MIN_WIDTH, this._root.offsetWidth * 0.6)
    const clamped = Math.round(Math.max(MASTER_MIN_WIDTH, Math.min(maxW, width)))
    this._masterPanel.style.width = `${clamped}px`
    this._divider.setAttribute("aria-valuenow", String(clamped))
    return clamped
  }

  _setupDividerResize() {
    this.listen(this._divider, "pointerdown", (e) => {
      if (this._stacked === true || this._isResizable() === false) {
        return
      }
      e.preventDefault()
      const direction = window.getComputedStyle(this).direction === "rtl" ? -1 : 1
      this._resizeDrag = { startX: e.clientX, startWidth: this._masterPanel.offsetWidth, direction: direction }
      if (typeof this._divider.setPointerCapture === "function" && e.pointerId !== undefined) {
        try {
          this._divider.setPointerCapture(e.pointerId)
        } catch (error) {
          /* Synthetic events carry no active pointer. */
        }
      }
    })

    this.listen(this._divider, "pointermove", (e) => {
      if (this._resizeDrag === null) {
        return
      }
      const delta = (e.clientX - this._resizeDrag.startX) * this._resizeDrag.direction
      this._setMasterWidth(this._resizeDrag.startWidth + delta)
    })

    const endDrag = () => {
      if (this._resizeDrag === null) {
        return
      }
      this._resizeDrag = null
      this.emit("mj-panel-resize", { masterWidth: this._masterPanel.offsetWidth })
    }
    this.listen(this._divider, "pointerup", endDrag)
    this.listen(this._divider, "pointercancel", endDrag)

    this.listen(this._divider, "keydown", (e) => {
      if (this._stacked === true || this._isResizable() === false) {
        return
      }
      const direction = window.getComputedStyle(this).direction === "rtl" ? -1 : 1
      const currentW = this._masterPanel.offsetWidth
      let nextW = null
      if (e.key === "ArrowLeft") {
        nextW = currentW - RESIZE_STEP * direction
      } else if (e.key === "ArrowRight") {
        nextW = currentW + RESIZE_STEP * direction
      } else if (e.key === "Home") {
        nextW = MASTER_MIN_WIDTH
      } else if (e.key === "End") {
        nextW = this._root.offsetWidth * 0.6
      }
      if (nextW !== null) {
        e.preventDefault()
        const applied = this._setMasterWidth(nextW)
        this.emit("mj-panel-resize", { masterWidth: applied })
      }
    })
    return
  }

  /* ----- master list ----- */

  _renderMasterList() {
    const focusWasInside = this._masterList.contains(this.shadowRoot.activeElement)
    this._masterList.replaceChildren()

    for (let idx = 0; idx < this._items.length; idx = idx + 1) {
      const item = this._items[idx]
      const li = document.createElement("li")
      li.className = "master-item"
      li.setAttribute("part", "master-item")
      li.setAttribute("role", "option")
      li.setAttribute("data-key", String(item.key))
      li.setAttribute("aria-selected", "false")
      li.tabIndex = -1

      const labelEl = document.createElement("span")
      labelEl.className = "item-label"
      labelEl.textContent = item.label
      li.appendChild(labelEl)

      if (item.meta !== undefined && item.meta !== null) {
        const metaEl = document.createElement("span")
        metaEl.className = "item-meta"
        metaEl.textContent = item.meta
        li.appendChild(metaEl)
      }

      this._masterList.appendChild(li)
    }

    /* A refreshed list shows the current selection again. */
    this._syncSelectionUI()
    if (focusWasInside === true) {
      const target = this._tabStopItem()
      if (target !== null) {
        target.focus()
      }
    }
    return
  }

  _itemElements() {
    const elements = Array.from(this._masterList.querySelectorAll(".master-item"))
    return elements
  }

  /*
   * Mark the selected option and keep exactly one option in the tab order:
   * the one focus was last on, else the selected one, else the first.
   */
  _syncSelectionUI() {
    const elements = this._itemElements()
    let tabStop = null
    let selectedEl = null

    for (let i = 0; i < elements.length; i = i + 1) {
      const el = elements[i]
      const key = el.getAttribute("data-key")
      const isSelected = this._selectedKey !== null && key === this._selectedKey
      el.setAttribute("aria-selected", isSelected === true ? "true" : "false")
      el.tabIndex = -1
      if (isSelected === true) {
        selectedEl = el
      }
      if (this._focusKey !== null && key === this._focusKey) {
        tabStop = el
      }
    }

    if (tabStop === null) {
      tabStop = selectedEl !== null ? selectedEl : (elements.length > 0 ? elements[0] : null)
    }
    if (tabStop !== null) {
      tabStop.tabIndex = 0
    }
    return
  }

  _tabStopItem() {
    const item = this._masterList.querySelector(".master-item[tabindex='0']")
    return item
  }

  _focusItemElement(el) {
    if (el === null || el === undefined) {
      return
    }
    this._focusKey = el.getAttribute("data-key")
    this._syncSelectionUI()
    el.focus()
    return
  }

  _itemFromEvent(event) {
    let found = null
    if (event.target instanceof Element) {
      const el = event.target.closest(".master-item")
      if (el !== null) {
        const key = el.getAttribute("data-key")
        const item = this._items.find((it) => String(it.key) === key)
        if (item !== undefined) {
          found = { element: el, item: item }
        }
      }
    }
    return found
  }

  _onListClick(event) {
    const hit = this._itemFromEvent(event)
    if (hit !== null) {
      this._focusKey = String(hit.item.key)
      this._handleItemClick(hit.item)
    }
    return
  }

  _onListKeydown(event) {
    const hit = this._itemFromEvent(event)
    if (hit === null) {
      return
    }
    const elements = this._itemElements()
    const index = elements.indexOf(hit.element)

    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      this._handleItemClick(hit.item)
    } else if (event.key === "ArrowDown") {
      event.preventDefault()
      this._focusItemElement(elements[Math.min(index + 1, elements.length - 1)])
    } else if (event.key === "ArrowUp") {
      event.preventDefault()
      this._focusItemElement(elements[Math.max(index - 1, 0)])
    } else if (event.key === "Home") {
      event.preventDefault()
      this._focusItemElement(elements[0])
    } else if (event.key === "End") {
      event.preventDefault()
      this._focusItemElement(elements[elements.length - 1])
    }
    return
  }

  /* ----- selection ----- */

  /*
   * A user picked an item. The selection itself goes through the
   * `selected-key` attribute (one code path, one detail load); re-activating
   * the selected item reloads its detail.
   */
  _handleItemClick(item) {
    const proceed = this.emit("mj-item-select", { key: item.key, item: item }, { cancelable: true })
    if (proceed === false) {
      return
    }
    const keyText = String(item.key)
    this._userSelecting = true
    if (this.getAttribute("selected-key") === keyText) {
      this._selectItem(keyText, true, true)
    } else {
      this.setAttribute("selected-key", keyText)
    }
    this._userSelecting = false
    return
  }

  /*
   * Show `key` as selected and load its detail. `force` reloads a key that
   * is already selected; `byUser` moves focus with the view when stacked.
   */
  _selectItem(key, force, byUser) {
    const keyText = String(key)
    const fromUser = byUser === true || this._userSelecting === true
    if (keyText === this._selectedKey && force !== true) {
      /* Replayed or repeated attribute value: nothing new to load. */
      this._syncSelectionUI()
      return
    }
    this._selectedKey = keyText
    this._syncSelectionUI()

    const selectedItem = this._selectedItem()
    const itemLabel = selectedItem !== undefined ? selectedItem.label : keyText
    this._updateDetailLabel(itemLabel)

    if (this._stacked === true) {
      this._goToDetail(fromUser)
    } else {
      this._stackView = "detail"
    }

    this._loadDetail(selectedItem !== undefined ? selectedItem.key : keyText, itemLabel)
    return
  }

  _clearSelection() {
    this._selectedKey = null
    this._loadGeneration = this._loadGeneration + 1
    this._abortPendingLoad()
    this._detailData = undefined
    this._detailState = "empty"
    this._stackView = "master"
    this._syncSelectionUI()
    this._updateDetailLabel(null)
    this._syncPanels()
    this._applyDetailState()
    return
  }

  /* ----- detail ----- */

  _abortPendingLoad() {
    if (this._currentAbortController !== null) {
      this._currentAbortController.abort()
      this._currentAbortController = null
    }
    return
  }

  _loadDetail(key, itemLabel) {
    this._loadGeneration = this._loadGeneration + 1
    const generation = this._loadGeneration
    this._abortPendingLoad()

    if (this._detailDataSource === null) {
      this._detailState = "data"
      this._applyDetailState()
      announce(t("mj.masterDetail.showingDetail", { item: itemLabel }))
      return
    }

    const controller = typeof AbortController !== "undefined" ? new AbortController() : null
    this._currentAbortController = controller
    this._detailState = "loading"
    this._applyDetailState()

    let pending = null
    try {
      const options = { signal: controller !== null ? controller.signal : undefined }
      pending = Promise.resolve(this._detailDataSource(key, options))
    } catch (error) {
      pending = Promise.reject(error)
    }

    pending.then((data) => {
      if (generation !== this._loadGeneration) {
        /* A newer selection took over; this result is stale. */
        return
      }
      this._currentAbortController = null
      this._detailData = data
      this._detailState = "data"
      this._applyDetailState()
      this.emit("mj-detail-load", { key: key, data: data })
      announce(t("mj.masterDetail.showingDetail", { item: itemLabel }))
      return
    }).catch((err) => {
      if (generation !== this._loadGeneration) {
        return
      }
      this._currentAbortController = null
      this._detailState = "error"
      this._applyDetailState()
      this.emit("mj-detail-error", { key: key, error: err })
    })
    return
  }

  /* Show exactly one of: empty, loading, error, data. */
  _applyDetailState() {
    let state = this._detailState
    if (this.hasAttribute("loading-detail") === true) {
      state = "loading"
    }
    this._detailEmpty.hidden = state !== "empty"
    this._detailLoading.hidden = state !== "loading"
    this._detailError.hidden = state !== "error"
    this._detailDataEl.hidden = state !== "data"
    this._detailPanel.setAttribute("aria-busy", state === "loading" ? "true" : "false")
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
      this._syncLabels()
    }
    return
  }

  /* Stored for the table master (`master-type="table"`), not used yet. */
  get columns() {
    return this._columns
  }

  set columns(value) {
    this._columns = Array.isArray(value) === true ? value : []
    return
  }

  /* Stored for the table master (`master-type="table"`), not used yet. */
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

  /* `(key, { signal }) => Promise<data>`; the signal aborts on a newer selection. */
  set detailDataSource(fn) {
    this._detailDataSource = typeof fn === "function" ? fn : null
    return
  }

  /* The value the last successful `detailDataSource` call resolved. */
  get detailData() {
    return this._detailData
  }

  /* The layout in effect: "stacked" or "side-by-side". */
  get resolvedLayout() {
    const layout = this._stacked === true ? "stacked" : "side-by-side"
    return layout
  }
}
