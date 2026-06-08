/*
 * mjtreegrid.js
 *
 * <mj-tree-grid> -- hierarchical tabular data grid following the WAI-ARIA
 * treegrid pattern. Rows have parent/child relationships; expansion is in-place.
 * Uses a flattened visible-row list driven through VirtualWindow for performance.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { VirtualWindow } from "../core/collection.js";
import { announce } from "../core/announcer.js";

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

.toolbar { padding: var(--mj-space-2); border-bottom: 1px solid var(--mj-border); }

.grid-root {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
  outline: none;
}
.grid-root:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); }

.header-row {
  display: flex;
  background: var(--mj-bg-subtle);
  border-bottom: 2px solid var(--mj-border-strong);
  user-select: none;
}

.header-cell {
  display: flex;
  align-items: center;
  padding: var(--mj-space-2) var(--mj-space-3);
  font-weight: var(--mj-font-weight-medium);
  font-size: var(--mj-font-size-sm);
  flex-shrink: 0;
  min-width: 80px;
  overflow: hidden;
}
.header-cell[data-sortable="true"] { cursor: pointer; }
.header-cell[data-sortable="true"]:hover { background: var(--mj-bg-muted); }

.body-scroll { flex: 1; overflow-y: auto; overflow-x: auto; position: relative; }
.body-inner { position: relative; }

.row {
  display: flex;
  align-items: center;
  border-bottom: 1px solid var(--mj-border);
  position: absolute;
  width: 100%;
}
.row:hover { background: var(--mj-tg-hover-bg, var(--mj-bg-muted)); }
.row[aria-selected="true"] { background: var(--mj-tg-selected-bg, color-mix(in srgb, var(--mj-accent) 10%, transparent)); }

.expander-cell {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  padding: var(--mj-space-2);
  min-width: 160px;
  gap: var(--mj-space-1);
}

.expander-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--mj-tg-expander-size, 20px);
  height: var(--mj-tg-expander-size, 20px);
  background: none;
  border: none;
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

.cell {
  display: flex;
  align-items: center;
  padding: var(--mj-space-2) var(--mj-space-3);
  font-size: var(--mj-font-size-sm);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex-shrink: 0;
  min-width: 80px;
}
.cell:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: -2px; }

.footer {
  display: flex;
  align-items: center;
  padding: var(--mj-space-2) var(--mj-space-3);
  border-top: 1px solid var(--mj-border);
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text-muted);
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--mj-space-7);
  color: var(--mj-text-muted);
}
`;

export class MjTreeGrid extends MjElement {
  static tagName = "mj-tree-grid";
  static styles = STYLES;
  static watched = ["mode", "selection", "sortable", "loading", "expand-depth", "row-height"];

  constructor() {
    super()
    this._columns = []
    this._rows = []
    this._flatList = []
    this._expandedKeys = new Set()
    this._selectedRows = new Set()
    this._vw = null
    this._focusedRowIdx = 0
    this._dataSource = null
  }

  render() {
    const markup = `
      <div class="toolbar" part="toolbar"><slot name="toolbar"></slot></div>
      <div class="grid-root" part="grid-root" role="treegrid" tabindex="0"
           aria-rowcount="-1" aria-label="Tree grid">
        <div class="header-row" part="header-row" role="row"></div>
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
    this._headerRow = this.$(".header-row")
    this._bodyScroll = this.$(".body-scroll")
    this._bodyInner = this.$(".body-inner")

    const rowH = parseInt(this.getAttribute("row-height") || "40", 10)
    this._vw = new VirtualWindow({ rowHeight: rowH, overscan: 4, total: 0 })

    this.listen(this._gridRoot, "keydown", this._onKeydown.bind(this))
    this.listen(this._bodyScroll, "scroll", this._onScroll.bind(this))

    if (this._columns.length > 0 && this._rows.length > 0) {
      this._initialize()
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._gridRoot === undefined || this._gridRoot === null) {
      return
    }
    if (name === "loading") {
      this._gridRoot.setAttribute("aria-busy", newValue !== null ? "true" : "false")
    }
    return
  }

  _initialize() {
    const expandDepth = parseInt(this.getAttribute("expand-depth") || "1", 10)
    this._autoExpand(this._rows, 0, expandDepth)
    this._buildFlatList()
    this._renderHeaders()
    this._renderRows()
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
    this._flatList = []
    this._flattenRows(this._rows, 0, null)
    this._vw.setTotal(this._flatList.length)
    this._gridRoot.setAttribute("aria-rowcount", String(this._flatList.length))
    return
  }

  _flattenRows(rows, level, parentKey) {
    const sibCount = rows.length
    for (let i = 0; i < rows.length; i = i + 1) {
      const row = rows[i]
      const hasChildren = (row.children !== undefined && row.children !== null && row.children.length > 0) ||
                          row.hasChildren === true
      const isExpanded = this._expandedKeys.has(row.key)

      this._flatList.push({
        key: row.key,
        data: row.data || row,
        level: level,
        hasChildren: hasChildren,
        isExpanded: isExpanded,
        setsize: sibCount,
        posinset: i + 1,
        children: row.children || []
      })

      if (hasChildren === true && isExpanded === true && row.children !== undefined) {
        this._flattenRows(row.children, level + 1, row.key)
      }
    }
    return
  }

  _renderHeaders() {
    this._headerRow.innerHTML = ""
    const sortable = this.hasAttribute("sortable")

    const expanderHeader = document.createElement("div")
    expanderHeader.className = "header-cell"
    expanderHeader.setAttribute("role", "columnheader")
    expanderHeader.style.width = "160px"
    expanderHeader.textContent = this._columns.length > 0 ? (this._columns[0].label || this._columns[0].key) : ""
    if (sortable === true && this._columns.length > 0 && this._columns[0].sortable !== false) {
      expanderHeader.setAttribute("data-sortable", "true")
      expanderHeader.setAttribute("aria-sort", "none")
    }
    this._headerRow.appendChild(expanderHeader)

    for (let i = 1; i < this._columns.length; i = i + 1) {
      const col = this._columns[i]
      const cell = document.createElement("div")
      cell.className = "header-cell"
      cell.setAttribute("role", "columnheader")
      cell.style.width = col.width ? (typeof col.width === "number" ? `${col.width}px` : col.width) : "120px"
      cell.textContent = col.label || col.key
      this._headerRow.appendChild(cell)
    }
    return
  }

  _renderRows() {
    const scrollTop = this._bodyScroll.scrollTop
    const viewH = this._bodyScroll.clientHeight || 400
    const win = this._vw.range(scrollTop, viewH)
    const scrollHeight = this._vw.scrollHeight()

    this._bodyInner.style.height = `${scrollHeight}px`
    this._bodyInner.innerHTML = ""

    if (this._flatList.length === 0) {
      const emptyEl = document.createElement("div")
      emptyEl.className = "empty-state"
      emptyEl.appendChild(document.createElement("slot")).setAttribute("name", "empty")
      emptyEl.textContent = "No data"
      this._bodyInner.appendChild(emptyEl)
      return
    }

    for (let i = win.start; i < win.end; i = i + 1) {
      const item = this._flatList[i]
      if (item === undefined) {
        continue
      }
      const top = win.offsetY + (i - win.start) * this._vw.rowHeight
      const rowEl = this._createRowEl(item, i, top)
      this._bodyInner.appendChild(rowEl)
    }
    return
  }

  _createRowEl(item, rowIdx, top) {
    const rowEl = document.createElement("div")
    rowEl.className = "row"
    rowEl.setAttribute("part", "row")
    rowEl.setAttribute("role", "row")
    rowEl.setAttribute("aria-level", String(item.level + 1))
    rowEl.setAttribute("aria-setsize", String(item.setsize))
    rowEl.setAttribute("aria-posinset", String(item.posinset))
    rowEl.setAttribute("aria-rowindex", String(rowIdx + 1))
    rowEl.setAttribute("data-key", item.key)
    rowEl.style.top = `${top}px`
    rowEl.style.height = `${this._vw.rowHeight}px`

    if (item.hasChildren === true) {
      rowEl.setAttribute("aria-expanded", item.isExpanded === true ? "true" : "false")
    }

    const isSelected = this._selectedRows.has(item.key)
    if (this.getAttribute("selection") !== "none") {
      rowEl.setAttribute("aria-selected", isSelected === true ? "true" : "false")
    }

    if (item.hasChildren === true && rowEl.hasAttribute("part")) {
      if (item.isExpanded === true) {
        rowEl.setAttribute("part", "row row-expanded")
      }
    }

    const indentPx = item.level * 20
    const expanderCell = document.createElement("div")
    expanderCell.className = "expander-cell"
    expanderCell.setAttribute("part", "expander-cell")
    expanderCell.setAttribute("role", "gridcell")
    expanderCell.style.width = "160px"

    const btn = document.createElement("button")
    btn.className = item.hasChildren === true ? "expander-btn" : "expander-btn leaf"
    btn.setAttribute("part", "expander-button")
    btn.style.marginInlineStart = `${indentPx}px`
    if (item.hasChildren === true) {
      btn.setAttribute("aria-label", (item.isExpanded === true ? "Collapse" : "Expand") + " " + item.key)
      btn.textContent = item.isExpanded === true ? "▼" : "▶"
      this.listen(btn, "click", (e) => {
        e.stopPropagation()
        this._toggleExpand(item.key)
      })
    } else {
      btn.textContent = ""
    }
    expanderCell.appendChild(btn)

    const labelSpan = document.createElement("span")
    const firstColKey = this._columns.length > 0 ? this._columns[0].key : "label"
    const cellValue = item.data[firstColKey]
    labelSpan.textContent = cellValue !== undefined && cellValue !== null ? String(cellValue) : item.key
    expanderCell.appendChild(labelSpan)
    rowEl.appendChild(expanderCell)

    for (let ci = 1; ci < this._columns.length; ci = ci + 1) {
      const col = this._columns[ci]
      const cellEl = document.createElement("div")
      cellEl.className = "cell"
      cellEl.setAttribute("role", "gridcell")
      cellEl.setAttribute("aria-colindex", String(ci + 1))
      const width = col.width ? (typeof col.width === "number" ? `${col.width}px` : col.width) : "120px"
      cellEl.style.width = width
      const val = item.data[col.key]
      cellEl.textContent = val !== undefined && val !== null ? String(val) : ""
      rowEl.appendChild(cellEl)
    }

    this.listen(rowEl, "click", () => {
      this._focusedRowIdx = rowIdx
      this._handleRowClick(item.key)
    })

    return rowEl
  }

  _toggleExpand(key) {
    const item = this._flatList.find((r) => r.key === key)
    if (item === undefined || item.hasChildren === false) {
      return
    }

    if (item.isExpanded === true) {
      const proceed = this.emit("mj-row-collapse", { key: key, level: item.level }, { cancelable: true })
      if (proceed === false) {
        return
      }
      this._expandedKeys.delete(key)
      announce(`Row ${key} collapsed.`)
    } else {
      const proceed = this.emit("mj-row-expand", { key: key, level: item.level }, { cancelable: true })
      if (proceed === false) {
        return
      }
      this._expandedKeys.add(key)
      const childCount = item.children.length
      announce(`Row ${key} expanded, ${childCount} children.`)
    }

    this._buildFlatList()
    this._renderRows()
    return
  }

  _handleRowClick(key) {
    const selection = this.getAttribute("selection") || "none"
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

  _refreshSelectionUI() {
    const rows = this._bodyInner.querySelectorAll(".row")
    for (let i = 0; i < rows.length; i = i + 1) {
      const rowEl = rows[i]
      const k = rowEl.getAttribute("data-key")
      rowEl.setAttribute("aria-selected", this._selectedRows.has(k) === true ? "true" : "false")
    }
    return
  }

  _onScroll() {
    window.requestAnimationFrame(() => {
      this._renderRows()
    })
    return
  }

  _onKeydown(event) {
    const key = event.key
    let idx = this._focusedRowIdx

    if (key === "ArrowDown") {
      event.preventDefault()
      idx = Math.min(idx + 1, this._flatList.length - 1)
    } else if (key === "ArrowUp") {
      event.preventDefault()
      idx = Math.max(idx - 1, 0)
    } else if (key === "ArrowRight") {
      event.preventDefault()
      const item = this._flatList[idx]
      if (item !== undefined && item.hasChildren === true && item.isExpanded === false) {
        this._toggleExpand(item.key)
        return
      }
    } else if (key === "ArrowLeft") {
      event.preventDefault()
      const item = this._flatList[idx]
      if (item !== undefined && item.isExpanded === true) {
        this._toggleExpand(item.key)
        return
      }
    } else if (key === "Enter") {
      event.preventDefault()
      const item = this._flatList[idx]
      if (item !== undefined && item.hasChildren === true) {
        this._toggleExpand(item.key)
      }
      return
    } else if (key === " ") {
      event.preventDefault()
      const item = this._flatList[idx]
      if (item !== undefined) {
        this._handleRowClick(item.key)
      }
      return
    } else {
      return
    }

    this._focusedRowIdx = idx
    const rows = this._bodyInner.querySelectorAll(".row")
    if (rows[idx] !== undefined) {
      rows[idx].focus()
    }
    return
  }

  /* ----- scriptable API ----- */

  get columns() {
    return this._columns
  }

  set columns(value) {
    this._columns = Array.isArray(value) === true ? value : []
    if (this._headerRow !== undefined && this._headerRow !== null && this._rows.length > 0) {
      this._initialize()
    }
    return
  }

  get rows() {
    return this._rows
  }

  set rows(value) {
    this._rows = Array.isArray(value) === true ? value : []
    if (this._bodyInner !== undefined && this._bodyInner !== null) {
      this._initialize()
    }
    return
  }

  get expandedKeys() {
    return this._expandedKeys
  }

  set expandedKeys(value) {
    this._expandedKeys = value instanceof Set ? value : new Set(value)
    if (this._bodyInner !== undefined && this._bodyInner !== null) {
      this._buildFlatList()
      this._renderRows()
    }
    return
  }

  get selectedRows() {
    return this._selectedRows
  }

  get loading() {
    return this.hasAttribute("loading")
  }

  set loading(value) {
    this.reflectBoolean("loading", value === true)
    return
  }
}
