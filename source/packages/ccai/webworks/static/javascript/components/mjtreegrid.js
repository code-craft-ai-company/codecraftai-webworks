/*
 * mjtreegrid.js
 *
 * <mj-tree-grid> -- hierarchical tabular data grid following the WAI-ARIA
 * treegrid pattern. Rows have parent/child relationships; expansion is in-place.
 * Uses a flattened visible-row list driven through VirtualWindow for performance.
 *
 * Rows: `{ key, data?, children?, hasChildren? }`; values live in `data` or on
 * the node itself. A node with `hasChildren: true` and no `children` is a lazy
 * parent: handle `mj-row-expand` and supply its rows with `setChildren()`.
 *
 * Keyboard (row focus, roving tabindex): ArrowDown / ArrowUp move between rows,
 * ArrowRight expands a collapsed parent or moves to its first child, ArrowLeft
 * collapses an expanded parent or moves to the parent row, Home / End go to
 * the first / last row, Enter toggles expansion, Space toggles selection.
 * Sortable headers are focusable and cycle on Enter / Space.
 *
 * Events: mj-row-expand (cancelable), mj-row-collapse (cancelable),
 * mj-selection-change, mj-sort-change, mj-children-load.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { VirtualWindow, compareValues, isMissingValue } from "../core/collection.js";
import { announce } from "../core/announcer.js";
import { t } from "../core/intl.js";

const STYLES = `
:host {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  font: inherit;
  color: var(--mj-text);
  background: var(--mj-surface);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-md);
}

.toolbar { padding: var(--mj-space-2); border-block-end: 1px solid var(--mj-border); }

.grid-root {
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  min-block-size: 0;
  overflow: hidden;
  outline: none;
}

.header-viewport {
  overflow: hidden;
  flex-shrink: 0;
  background: var(--mj-bg-subtle);
  border-block-end: 2px solid var(--mj-border-strong);
}

.header-row {
  display: flex;
  min-inline-size: max-content;
  box-sizing: content-box;
  user-select: none;
}

.header-cell {
  display: flex;
  align-items: center;
  gap: var(--mj-space-1);
  padding: var(--mj-space-2) var(--mj-space-3);
  font-weight: var(--mj-font-weight-medium);
  font-size: var(--mj-font-size-sm);
  flex-shrink: 0;
  min-inline-size: 80px;
  box-sizing: border-box;
  overflow: hidden;
}
.header-cell[data-sortable="true"] { cursor: pointer; }
.header-cell[data-sortable="true"]:hover { background: var(--mj-bg-muted); }
.header-cell:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: -2px; }

.header-label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sort-indicator { font-size: 0.7em; opacity: 0.5; margin-inline-start: auto; }
.sort-indicator.active { opacity: 1; }

/*
 * Without an explicit host height the body is as tall as its rows up to
 * --mj-tg-body-max-height, then it scrolls; a host height wins.
 */
.body-scroll {
  flex: 1 1 min(var(--mj-tg-content-height, 0px), var(--mj-tg-body-max-height, 400px));
  min-block-size: 0;
  overflow: auto;
  position: relative;
}
.body-inner { position: relative; }

:host([loading]) .body-scroll { opacity: 0.5; pointer-events: none; }

.row {
  display: flex;
  align-items: center;
  box-sizing: border-box;
  border-block-end: 1px solid var(--mj-border);
  position: absolute;
  inset-inline: 0;
  outline: none;
}
.row:hover { background: var(--mj-tg-hover-bg, var(--mj-bg-muted)); }
.row[aria-selected="true"] { background: var(--mj-tg-selected-bg, color-mix(in srgb, var(--mj-accent) 10%, transparent)); }
.row:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: -2px;
}

.expander-cell {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  padding: var(--mj-space-2);
  min-inline-size: 80px;
  box-sizing: border-box;
  gap: var(--mj-space-1);
  font-size: var(--mj-font-size-sm);
  overflow: hidden;
}

.expander-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--mj-tg-expander-size, 20px);
  height: var(--mj-tg-expander-size, 20px);
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  color: var(--mj-text-muted);
  font-size: 0.75em;
  flex-shrink: 0;
  border-radius: var(--mj-radius-sm);
}
.expander-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.expander-btn.leaf { visibility: hidden; pointer-events: none; }

.row-label {
  flex: 1 1 auto;
  min-inline-size: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cell {
  display: block;
  padding: var(--mj-space-2) var(--mj-space-3);
  font-size: var(--mj-font-size-sm);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex-shrink: 0;
  min-inline-size: 80px;
  box-sizing: border-box;
}

.footer {
  display: flex;
  align-items: center;
  padding: var(--mj-space-2) var(--mj-space-3);
  border-block-start: 1px solid var(--mj-border);
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text-muted);
  flex-shrink: 0;
}
.footer.is-empty { display: none; }

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--mj-space-7);
  color: var(--mj-text-muted);
}
`;

const FIRST_COLUMN_WIDTH = "160px";
const OTHER_COLUMN_WIDTH = "120px";
const INDENT_PER_LEVEL = 20;

/* Indentation stops growing here so deep rows keep room for their label. */
const MAX_INDENT_LEVELS = 6;

function columnWidthCss(col, fallback) {
  let width = fallback
  if (col !== undefined && col.width !== undefined && col.width !== null && col.width !== "") {
    width = typeof col.width === "number" ? `${col.width}px` : String(col.width)
  }
  return width
}

function columnLabel(col) {
  const label = col.label !== undefined && col.label !== null ? String(col.label) : String(col.key)
  return label
}

function rowHasChildren(row) {
  const has = (Array.isArray(row.children) === true && row.children.length > 0) || row.hasChildren === true
  return has
}

/* Values live in `row.data` or directly on the row node. */
function rowData(row) {
  const data = row.data !== undefined && row.data !== null ? row.data : row
  return data
}

export class MjTreeGrid extends MjElement {
  static tagName = "mj-tree-grid";
  static styles = STYLES;
  static watched = ["mode", "selection", "sortable", "loading", "expand-depth", "row-height", "empty-label", "label", "aria-label"];

  constructor() {
    super()
    this._columns = []
    this._rows = []
    this._flatList = []

    /* Both sets hold row keys exactly as the rows supply them. */
    this._expandedKeys = new Set()
    this._selectedRows = new Set()

    this._vw = null
    this._focusedRowIdx = 0
    this._sortState = null
    this._dataSource = null

    /* `expand-depth` is applied to the first data load only. */
    this._autoExpanded = false

    this._rowEls = new Map()
    this._renderVersion = 0
    this._emptyEl = null
    this._scrollFrame = 0
    this._gridId = nextId("mj-tg")
  }

  render() {
    const markup = `
      <div class="toolbar" part="toolbar"><slot name="toolbar"></slot></div>
      <div class="grid-root" part="grid-root" role="treegrid" aria-rowcount="-1">
        <div class="header-viewport">
          <div class="header-row" part="header-row" role="row" aria-rowindex="1"></div>
        </div>
        <div class="body-scroll" part="body">
          <div class="body-inner"></div>
        </div>
      </div>
      <div class="footer" part="footer"><slot name="footer"></slot></div>
    `
    return markup
  }

  afterRender() {
    this._gridRoot = this.$(".grid-root")
    this._headerViewport = this.$(".header-viewport")
    this._headerRow = this.$(".header-row")
    this._bodyScroll = this.$(".body-scroll")
    this._bodyInner = this.$(".body-inner")
    this._footer = this.$(".footer")
    this._rowEls = new Map()
    this._emptyEl = null

    this._vw = new VirtualWindow({ rowHeight: this._rowHeight(), overscan: 4, total: 0 })

    this.listen(this._bodyInner, "keydown", this._onKeydown.bind(this))
    this.listen(this._bodyInner, "click", this._onBodyClick.bind(this))
    this.listen(this._bodyScroll, "scroll", this._onScroll.bind(this))
    this.listen(this._headerRow, "click", this._onHeaderClick.bind(this))
    this.listen(this._headerRow, "keydown", this._onHeaderKeydown.bind(this))

    const footerSlot = this._footer.querySelector("slot")
    const syncFooter = () => {
      this._footer.classList.toggle("is-empty", footerSlot.assignedNodes().length === 0)
    }
    this.listen(footerSlot, "slotchange", syncFooter)
    syncFooter()

    this._setupResizeObserver()
    this.onTeardown(() => {
      if (this._scrollFrame !== 0) {
        window.cancelAnimationFrame(this._scrollFrame)
        this._scrollFrame = 0
      }
    })

    this._syncGridLabel()
    this._gridRoot.setAttribute("aria-busy", this.hasAttribute("loading") === true ? "true" : "false")
    this._initialize()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._gridRoot === undefined || this._gridRoot === null) {
      return
    }
    if (name === "loading") {
      this._gridRoot.setAttribute("aria-busy", newValue !== null ? "true" : "false")
    }
    if (name === "label" || name === "aria-label") {
      this._syncGridLabel()
    }
    if (name === "row-height") {
      this._vw.rowHeight = this._rowHeight()
      this._refresh()
    }
    if (name === "expand-depth" && oldValue !== newValue) {
      /* An explicit new depth replaces the current expansion state. */
      this._expandedKeys = new Set()
      this._autoExpand(this._rows, 0, this._expandDepth())
      this._buildFlatList()
      this._refresh()
    }
    if (name === "selection" || name === "mode") {
      if (this._selectionMode() === "none") {
        this._selectedRows.clear()
      }
      this._refresh()
    }
    if (name === "sortable") {
      if (newValue === null) {
        this._sortState = null
        this._buildFlatList()
      }
      this._renderHeaders()
      this._refresh()
    }
    if (name === "empty-label") {
      this._refresh()
    }
    return
  }

  /* Move focus to the row that is the grid's tab stop. */
  focus(options) {
    const target = this._rowEls !== undefined ? this._rowEls.get(this._focusedRowIdx) : undefined
    if (target !== undefined) {
      target.focus(options)
    } else {
      super.focus(options)
    }
    return
  }

  /* ----- small readers ----- */

  _rowHeight() {
    const parsed = parseInt(this.getAttribute("row-height") || "40", 10)
    const height = Number.isNaN(parsed) === true || parsed <= 0 ? 40 : parsed
    return height
  }

  _expandDepth() {
    const parsed = parseInt(this.getAttribute("expand-depth") || "1", 10)
    const depth = Number.isNaN(parsed) === true || parsed < 0 ? 1 : parsed
    return depth
  }

  /* `mode="view"` is read-only: rows cannot be selected. */
  _selectionMode() {
    let mode = this.getAttribute("selection") || "none"
    if (this.getAttribute("mode") === "view") {
      mode = "none"
    }
    return mode
  }

  _syncGridLabel() {
    const label = this.getAttribute("label") || this.getAttribute("aria-label") || t("mj.treeGrid.label")
    this._gridRoot.setAttribute("aria-label", label)
    return
  }

  _isColumnSortable(col) {
    const sortable = (this.hasAttribute("sortable") === true && col.sortable !== false) || col.sortable === true
    return sortable
  }

  /* The text that names a row: its first-column value, else its key. */
  _rowLabel(item) {
    const firstColKey = this._columns.length > 0 ? this._columns[0].key : "label"
    const value = item.data[firstColKey]
    const label = value !== undefined && value !== null ? String(value) : String(item.key)
    return label
  }

  /* ----- model ----- */

  _initialize() {
    if (this._autoExpanded === false && this._rows.length > 0) {
      this._autoExpand(this._rows, 0, this._expandDepth())
      this._autoExpanded = true
    }
    this._buildFlatList()
    this._renderHeaders()
    this._refresh()
    return
  }

  _autoExpand(rows, depth, maxDepth) {
    if (depth >= maxDepth) {
      return
    }
    for (let i = 0; i < rows.length; i = i + 1) {
      const row = rows[i]
      if (row.children !== undefined && row.children !== null && row.children.length > 0) {
        this._expandedKeys.add(row.key)
        this._autoExpand(row.children, depth + 1, maxDepth)
      }
    }
    return
  }

  _buildFlatList() {
    const focusedItem = this._flatList[this._focusedRowIdx]
    this._flatList = []
    this._flattenRows(this._rows, 0, -1)
    this._renderVersion = this._renderVersion + 1

    /* Keep focus on the same row when rows above it appear or disappear. */
    if (focusedItem !== undefined) {
      const sameIdx = this._flatList.findIndex((item) => item.key === focusedItem.key)
      if (sameIdx >= 0) {
        this._focusedRowIdx = sameIdx
      }
    }
    if (this._focusedRowIdx >= this._flatList.length) {
      this._focusedRowIdx = Math.max(0, this._flatList.length - 1)
    }

    if (this._vw !== null) {
      this._vw.setTotal(this._flatList.length)
    }
    if (this._gridRoot !== undefined && this._gridRoot !== null) {
      this._gridRoot.setAttribute("aria-rowcount", String(this._flatList.length + 1))
    }
    return
  }

  /* Siblings in display order: as given, or sorted by the active column. */
  _orderedSiblings(rows) {
    let ordered = rows

    if (this._sortState !== null) {
      const key = this._sortState.key
      const descending = this._sortState.direction === "desc"
      const col = this._columns.find((c) => c.key === key)
      const type = col !== undefined ? col.type : undefined
      const custom = col !== undefined && typeof col.compare === "function" ? col.compare : null

      ordered = rows.slice().sort((leftRow, rightRow) => {
        const left = rowData(leftRow)[key]
        const right = rowData(rightRow)[key]
        /* Missing values stay last in both directions. */
        let order = 0
        if (isMissingValue(left) === true || isMissingValue(right) === true) {
          order = compareValues(left, right, type)
        } else {
          order = custom !== null ? custom(left, right, leftRow, rightRow) : compareValues(left, right, type)
          if (descending === true) {
            order = -order
          }
        }
        return order
      })
    }

    return ordered
  }

  _flattenRows(rows, level, parentIdx) {
    const ordered = this._orderedSiblings(rows)
    const sibCount = ordered.length
    for (let i = 0; i < ordered.length; i = i + 1) {
      const row = ordered[i]
      const hasChildren = rowHasChildren(row)
      const isExpanded = hasChildren === true && this._expandedKeys.has(row.key)

      this._flatList.push({
        key: row.key,
        row: row,
        data: rowData(row),
        level: level,
        hasChildren: hasChildren,
        isExpanded: isExpanded,
        setsize: sibCount,
        posinset: i + 1,
        parentIdx: parentIdx,
        children: Array.isArray(row.children) === true ? row.children : []
      })

      if (isExpanded === true && Array.isArray(row.children) === true) {
        this._flattenRows(row.children, level + 1, this._flatList.length - 1)
      }
    }
    return
  }

  /* ----- rendering ----- */

  _renderHeaders() {
    this._headerRow.replaceChildren()

    for (let i = 0; i < this._columns.length; i = i + 1) {
      const col = this._columns[i]
      const cell = document.createElement("div")
      cell.className = "header-cell"
      cell.setAttribute("part", "header-cell")
      cell.setAttribute("role", "columnheader")
      cell.setAttribute("aria-colindex", String(i + 1))
      cell.setAttribute("data-col-key", col.key)
      cell.style.width = columnWidthCss(col, i === 0 ? FIRST_COLUMN_WIDTH : OTHER_COLUMN_WIDTH)

      const label = document.createElement("span")
      label.className = "header-label"
      label.textContent = columnLabel(col)
      cell.appendChild(label)

      if (this._isColumnSortable(col) === true) {
        cell.setAttribute("data-sortable", "true")
        cell.tabIndex = 0
        const indicator = document.createElement("span")
        indicator.className = "sort-indicator"
        indicator.setAttribute("aria-hidden", "true")
        cell.appendChild(indicator)
      }

      this._headerRow.appendChild(cell)
    }

    this._gridRoot.setAttribute("aria-colcount", String(this._columns.length))
    this._updateSortIndicators()
    return
  }

  _updateSortIndicators() {
    const headers = this._headerRow.querySelectorAll("[data-sortable='true']")
    for (let i = 0; i < headers.length; i = i + 1) {
      const header = headers[i]
      const indicator = header.querySelector(".sort-indicator")
      const isActive = this._sortState !== null && this._sortState.key === header.getAttribute("data-col-key")
      if (isActive === true) {
        const ascending = this._sortState.direction === "asc"
        header.setAttribute("aria-sort", ascending === true ? "ascending" : "descending")
        indicator.className = "sort-indicator active"
        indicator.textContent = ascending === true ? "↑" : "↓"
      } else {
        header.setAttribute("aria-sort", "none")
        indicator.className = "sort-indicator"
        indicator.textContent = "↕"
      }
    }
    return
  }

  /* Re-render every visible row from the model. */
  _refresh() {
    this._renderVersion = this._renderVersion + 1
    this._renderRows()
    return
  }

  _renderRows() {
    const total = this._flatList.length
    const scrollHeight = this._vw.scrollHeight()
    const focusWasInside = this._bodyInner.contains(this.shadowRoot.activeElement)

    this._bodyInner.style.height = `${scrollHeight}px`
    this._bodyScroll.style.setProperty("--mj-tg-content-height", `${scrollHeight}px`)
    this._syncEmptyState()
    this._syncColumnMetrics()

    const viewH = this._bodyScroll.clientHeight || 400
    const win = this._vw.range(this._bodyScroll.scrollTop, viewH)

    /* The focused row stays rendered while scrolled away so focus survives. */
    const wanted = new Set()
    for (let i = win.start; i < win.end; i = i + 1) {
      wanted.add(i)
    }
    if (total > 0) {
      wanted.add(this._focusedRowIdx)
    }

    const renderedIndexes = Array.from(this._rowEls.keys())
    for (let ri = 0; ri < renderedIndexes.length; ri = ri + 1) {
      const index = renderedIndexes[ri]
      if (wanted.has(index) === false) {
        this._rowEls.get(index).remove()
        this._rowEls.delete(index)
      }
    }

    wanted.forEach((index) => {
      const item = this._flatList[index]
      if (item === undefined) {
        return
      }
      let rowEl = this._rowEls.get(index)
      if (rowEl === undefined) {
        rowEl = document.createElement("div")
        rowEl.className = "row"
        rowEl.setAttribute("role", "row")
        rowEl._mjVersion = -1
        this._rowEls.set(index, rowEl)
        this._bodyInner.appendChild(rowEl)
      }
      if (rowEl._mjVersion !== this._renderVersion) {
        this._populateRow(rowEl, item, index)
        rowEl._mjVersion = this._renderVersion
      }
      rowEl.tabIndex = index === this._focusedRowIdx ? 0 : -1
    })

    if (focusWasInside === true && this._bodyInner.contains(this.shadowRoot.activeElement) === false) {
      const target = this._rowEls.get(this._focusedRowIdx)
      if (target !== undefined) {
        target.focus({ preventScroll: true })
      }
    }
    return
  }

  _populateRow(rowEl, item, rowIdx) {
    const rowH = this._vw.rowHeight
    rowEl.replaceChildren()
    rowEl.setAttribute("part", item.isExpanded === true ? "row row-expanded" : "row")
    rowEl.setAttribute("aria-level", String(item.level + 1))
    rowEl.setAttribute("aria-setsize", String(item.setsize))
    rowEl.setAttribute("aria-posinset", String(item.posinset))
    rowEl.setAttribute("aria-rowindex", String(rowIdx + 2))
    rowEl.setAttribute("data-key", String(item.key))
    rowEl.setAttribute("data-row-index", String(rowIdx))
    rowEl.style.top = `${rowIdx * rowH}px`
    rowEl.style.height = `${rowH}px`

    if (item.hasChildren === true) {
      rowEl.setAttribute("aria-expanded", item.isExpanded === true ? "true" : "false")
    } else {
      rowEl.removeAttribute("aria-expanded")
    }

    if (this._selectionMode() !== "none") {
      rowEl.setAttribute("aria-selected", this._selectedRows.has(item.key) === true ? "true" : "false")
    } else {
      rowEl.removeAttribute("aria-selected")
    }

    const label = this._rowLabel(item)
    const indentPx = Math.min(item.level, MAX_INDENT_LEVELS) * INDENT_PER_LEVEL

    const expanderCell = document.createElement("div")
    expanderCell.className = "expander-cell"
    expanderCell.setAttribute("part", "expander-cell")
    expanderCell.setAttribute("role", "gridcell")
    expanderCell.setAttribute("aria-colindex", "1")
    expanderCell.style.width = columnWidthCss(this._columns[0], FIRST_COLUMN_WIDTH)

    const btn = document.createElement("button")
    btn.type = "button"
    btn.className = item.hasChildren === true ? "expander-btn" : "expander-btn leaf"
    btn.setAttribute("part", "expander-button")
    btn.style.marginInlineStart = `${indentPx}px`
    /* The row is the tab stop; the button is a pointer target only. */
    btn.tabIndex = -1
    if (item.hasChildren === true) {
      btn.setAttribute("aria-label", item.isExpanded === true ? t("mj.treeGrid.collapseRow", { label: label }) : t("mj.treeGrid.expandRow", { label: label }))
      btn.textContent = item.isExpanded === true ? "▼" : "▶"
    } else {
      btn.setAttribute("aria-hidden", "true")
    }
    expanderCell.appendChild(btn)

    const labelSpan = document.createElement("span")
    labelSpan.className = "row-label"
    labelSpan.textContent = label
    labelSpan.setAttribute("title", label)
    expanderCell.appendChild(labelSpan)
    rowEl.appendChild(expanderCell)

    for (let ci = 1; ci < this._columns.length; ci = ci + 1) {
      const col = this._columns[ci]
      const cellEl = document.createElement("div")
      cellEl.className = "cell"
      cellEl.setAttribute("part", "cell")
      cellEl.setAttribute("role", "gridcell")
      cellEl.setAttribute("aria-colindex", String(ci + 1))
      cellEl.style.width = columnWidthCss(col, OTHER_COLUMN_WIDTH)
      const val = item.data[col.key]
      cellEl.textContent = val !== undefined && val !== null ? String(val) : ""
      rowEl.appendChild(cellEl)
    }
    return
  }

  /* The empty placeholder exists only while there are no rows. */
  _syncEmptyState() {
    if (this._flatList.length > 0) {
      if (this._emptyEl !== null) {
        this._emptyEl.remove()
        this._emptyEl = null
      }
      return
    }

    if (this._emptyEl === null) {
      const emptyEl = document.createElement("div")
      emptyEl.className = "empty-state"
      emptyEl.setAttribute("part", "empty-state")
      const slot = document.createElement("slot")
      slot.setAttribute("name", "empty")
      emptyEl.appendChild(slot)
      this._bodyScroll.appendChild(emptyEl)
      this._emptyEl = emptyEl
    }

    /* Fallback content of the slot: shown unless the host slots its own. */
    this._emptyEl.querySelector("slot").textContent = this.getAttribute("empty-label") || t("mj.treeGrid.empty")
    this._bodyScroll.style.setProperty("--mj-tg-content-height", `${this._emptyEl.offsetHeight}px`)
    return
  }

  /* Keep the body as wide as the columns and the header aligned with it. */
  _syncColumnMetrics() {
    const headerCells = this._headerRow.children
    let totalWidth = 0
    for (let i = 0; i < headerCells.length; i = i + 1) {
      totalWidth = totalWidth + headerCells[i].offsetWidth
    }
    this._bodyInner.style.minWidth = totalWidth > 0 ? `${totalWidth}px` : ""

    const gutter = this._bodyScroll.offsetWidth - this._bodyScroll.clientWidth
    this._headerRow.style.paddingInlineEnd = gutter > 0 ? `${gutter}px` : "0"
    this._headerViewport.scrollLeft = this._bodyScroll.scrollLeft
    return
  }

  _setupResizeObserver() {
    if (typeof ResizeObserver === "undefined") {
      return
    }
    let lastHeight = -1
    const observer = new ResizeObserver(() => {
      const height = this._bodyScroll.clientHeight
      if (height !== lastHeight) {
        lastHeight = height
        this._renderRows()
      }
    })
    observer.observe(this._bodyScroll)
    this.onTeardown(() => { observer.disconnect() })
    return
  }

  /* ----- expansion, selection, sorting ----- */

  _toggleExpand(key) {
    const item = this._flatList.find((r) => r.key === key)
    if (item === undefined || item.hasChildren === false) {
      return
    }
    const label = this._rowLabel(item)

    if (item.isExpanded === true) {
      const proceed = this.emit("mj-row-collapse", { key: key, level: item.level }, { cancelable: true })
      if (proceed === false) {
        return
      }
      this._expandedKeys.delete(key)
      announce(t("mj.treeGrid.rowCollapsed", { label: label }))
    } else {
      const proceed = this.emit("mj-row-expand", { key: key, level: item.level }, { cancelable: true })
      if (proceed === false) {
        return
      }
      this._expandedKeys.add(key)
      const childCount = item.children.length
      announce(t("mj.treeGrid.rowExpanded", { label: label, count: childCount }))
    }

    this._buildFlatList()
    this._renderRows()
    return
  }

  _handleRowClick(key) {
    const selection = this._selectionMode()
    if (selection === "none") {
      return
    }
    if (this._selectedRows.has(key) === true) {
      this._selectedRows.delete(key)
    } else {
      if (selection === "single") {
        this._selectedRows.clear()
      }
      this._selectedRows.add(key)
    }
    this._refreshSelectionUI()
    this.emit("mj-selection-change", { selectedRows: Array.from(this._selectedRows) })
    return
  }

  /* Selection is looked up by the row's own key, whatever its type. */
  _refreshSelectionUI() {
    const selection = this._selectionMode()
    this._rowEls.forEach((rowEl, index) => {
      const item = this._flatList[index]
      if (selection === "none" || item === undefined) {
        rowEl.removeAttribute("aria-selected")
      } else {
        rowEl.setAttribute("aria-selected", this._selectedRows.has(item.key) === true ? "true" : "false")
      }
    })
    return
  }

  _cycleSort(key) {
    let direction = "asc"
    if (this._sortState !== null && this._sortState.key === key) {
      direction = this._sortState.direction === "asc" ? "desc" : null
    }
    this._sortState = direction !== null ? { key: key, direction: direction } : null
    this._updateSortIndicators()
    this._buildFlatList()
    this._renderRows()
    this.emit("mj-sort-change", { key: key, direction: direction })

    const col = this._columns.find((c) => c.key === key)
    const label = col !== undefined ? columnLabel(col) : key
    if (direction === null) {
      announce(t("mj.treeGrid.sortCleared"))
    } else if (direction === "asc") {
      announce(t("mj.treeGrid.sortedAscending", { label: label }))
    } else {
      announce(t("mj.treeGrid.sortedDescending", { label: label }))
    }
    return
  }

  /* ----- events ----- */

  _sortableHeaderFromEvent(event) {
    let header = null
    if (event.target instanceof Element) {
      header = event.target.closest(".header-cell[data-sortable='true']")
    }
    return header
  }

  _onHeaderClick(event) {
    const header = this._sortableHeaderFromEvent(event)
    if (header !== null) {
      this._cycleSort(header.getAttribute("data-col-key"))
    }
    return
  }

  _onHeaderKeydown(event) {
    const header = this._sortableHeaderFromEvent(event)
    if (header !== null && (event.key === "Enter" || event.key === " ")) {
      event.preventDefault()
      this._cycleSort(header.getAttribute("data-col-key"))
    }
    return
  }

  _onBodyClick(event) {
    const target = event.target
    if (!(target instanceof Element)) {
      return
    }
    const rowEl = target.closest(".row")
    if (rowEl === null) {
      return
    }
    const rowIdx = parseInt(rowEl.getAttribute("data-row-index"), 10)
    const item = this._flatList[rowIdx]
    if (item === undefined) {
      return
    }

    this._setFocusedRow(rowIdx)

    if (target.closest(".expander-btn") !== null) {
      this._toggleExpand(item.key)
      /* The clicked button was re-rendered; keep focus on its row. */
      const focusedEl = this._rowEls.get(this._focusedRowIdx)
      if (focusedEl !== undefined) {
        focusedEl.focus({ preventScroll: true })
      }
    } else {
      this._handleRowClick(item.key)
    }
    return
  }

  _setFocusedRow(rowIdx) {
    if (rowIdx === this._focusedRowIdx) {
      return
    }
    const previous = this._rowEls.get(this._focusedRowIdx)
    if (previous !== undefined) {
      previous.tabIndex = -1
    }
    this._focusedRowIdx = rowIdx
    const current = this._rowEls.get(rowIdx)
    if (current !== undefined) {
      current.tabIndex = 0
    }
    return
  }

  /* Scroll row `rowIdx` into view, render it and give it focus. */
  _focusRow(rowIdx) {
    const total = this._flatList.length
    if (total === 0) {
      return
    }
    const clamped = Math.max(0, Math.min(rowIdx, total - 1))
    const rowH = this._vw.rowHeight
    const top = clamped * rowH
    const viewH = this._bodyScroll.clientHeight

    if (top < this._bodyScroll.scrollTop) {
      this._bodyScroll.scrollTop = top
    } else if (top + rowH > this._bodyScroll.scrollTop + viewH) {
      this._bodyScroll.scrollTop = top + rowH - viewH
    }

    this._setFocusedRow(clamped)
    this._renderRows()

    const target = this._rowEls.get(clamped)
    if (target !== undefined) {
      target.focus()
    }
    return
  }

  _onScroll() {
    if (this._headerViewport.scrollLeft !== this._bodyScroll.scrollLeft) {
      this._headerViewport.scrollLeft = this._bodyScroll.scrollLeft
    }
    if (this._scrollFrame !== 0) {
      return
    }
    this._scrollFrame = window.requestAnimationFrame(() => {
      this._scrollFrame = 0
      this._renderRows()
    })
    return
  }

  _onKeydown(event) {
    const key = event.key
    const idx = this._focusedRowIdx
    const item = this._flatList[idx]
    if (item === undefined) {
      return
    }
    const pageRows = Math.max(1, Math.floor(this._bodyScroll.clientHeight / this._vw.rowHeight) - 1)

    if (key === "ArrowDown") {
      event.preventDefault()
      this._focusRow(idx + 1)
    } else if (key === "ArrowUp") {
      event.preventDefault()
      this._focusRow(idx - 1)
    } else if (key === "ArrowRight") {
      event.preventDefault()
      if (item.hasChildren === true && item.isExpanded === false) {
        this._toggleExpand(item.key)
      } else if (item.isExpanded === true && item.children.length > 0) {
        this._focusRow(idx + 1)
      }
    } else if (key === "ArrowLeft") {
      event.preventDefault()
      if (item.isExpanded === true) {
        this._toggleExpand(item.key)
      } else if (item.parentIdx >= 0) {
        this._focusRow(item.parentIdx)
      }
    } else if (key === "Home") {
      event.preventDefault()
      this._focusRow(0)
    } else if (key === "End") {
      event.preventDefault()
      this._focusRow(this._flatList.length - 1)
    } else if (key === "PageDown") {
      event.preventDefault()
      this._focusRow(idx + pageRows)
    } else if (key === "PageUp") {
      event.preventDefault()
      this._focusRow(idx - pageRows)
    } else if (key === "Enter") {
      event.preventDefault()
      if (item.hasChildren === true) {
        this._toggleExpand(item.key)
      }
    } else if (key === " ") {
      event.preventDefault()
      this._handleRowClick(item.key)
    }
    return
  }

  /* ----- scriptable API ----- */

  get columns() {
    return this._columns
  }

  set columns(value) {
    this._columns = Array.isArray(value) === true ? value : []
    if (this._headerRow !== undefined && this._headerRow !== null) {
      this._initialize()
    }
    return
  }

  get rows() {
    return this._rows
  }

  /*
   * Assigning rows keeps the current expansion state; `expand-depth` is
   * applied to the first non-empty assignment only.
   */
  set rows(value) {
    this._rows = Array.isArray(value) === true ? value : []
    if (this._bodyInner !== undefined && this._bodyInner !== null) {
      this._initialize()
    }
    return
  }

  /*
   * Supply the children of a lazy parent (`hasChildren: true`). The parent
   * stays expanded or collapsed as it is; emits `mj-children-load`.
   */
  setChildren(parentKey, children) {
    const rows = Array.isArray(children) === true ? children : []
    const parent = this._findRow(this._rows, parentKey)
    if (parent === null) {
      return
    }
    parent.children = rows
    parent.hasChildren = rows.length > 0
    if (this._bodyInner !== undefined && this._bodyInner !== null) {
      this._buildFlatList()
      this._renderRows()
    }
    this.emit("mj-children-load", { parentKey: parentKey, rows: rows })
    return
  }

  _findRow(rows, key) {
    let found = null
    for (let i = 0; i < rows.length && found === null; i = i + 1) {
      const row = rows[i]
      if (row.key === key) {
        found = row
      } else if (Array.isArray(row.children) === true) {
        found = this._findRow(row.children, key)
      }
    }
    return found
  }

  get expandedKeys() {
    return this._expandedKeys
  }

  set expandedKeys(value) {
    this._expandedKeys = value instanceof Set ? value : new Set(value)
    /* The caller has taken over expansion; do not auto-expand afterwards. */
    this._autoExpanded = true
    if (this._bodyInner !== undefined && this._bodyInner !== null) {
      this._buildFlatList()
      this._renderRows()
    }
    return
  }

  get selectedRows() {
    return this._selectedRows
  }

  get sortState() {
    return this._sortState
  }

  set sortState(value) {
    this._sortState = value !== null && value !== undefined ? value : null
    if (this._bodyInner !== undefined && this._bodyInner !== null) {
      this._updateSortIndicators()
      this._buildFlatList()
      this._renderRows()
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
