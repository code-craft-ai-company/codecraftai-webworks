/*
 * mjdatatable.js
 *
 * <mj-data-table> -- full-featured interactive data grid with sorting, filtering,
 * column resize, row selection, cell editing, and virtualized row rendering.
 * Implements WAI-ARIA grid pattern with roving tabindex cell navigation.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { DataSource, VirtualWindow } from "../core/collection.js";
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
  background: var(--mj-dt-header-bg, var(--mj-bg-subtle));
  border-bottom: 2px solid var(--mj-border-strong);
  user-select: none;
}

.header-cell {
  display: flex;
  align-items: center;
  gap: var(--mj-space-1);
  padding: var(--mj-space-2) var(--mj-space-3);
  font-weight: var(--mj-font-weight-medium);
  font-size: var(--mj-font-size-sm);
  position: relative;
  overflow: hidden;
  flex-shrink: 0;
  min-width: 60px;
  cursor: default;
}
.header-cell[data-sortable="true"] { cursor: pointer; }
.header-cell[data-sortable="true"]:hover { background: var(--mj-bg-muted); }
.header-cell:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: -2px; }

.sort-indicator { font-size: 0.7em; opacity: 0.5; margin-inline-start: auto; }
.sort-indicator.active { opacity: 1; }

.resize-handle {
  position: absolute;
  right: 0; top: 0; bottom: 0;
  width: 4px;
  cursor: col-resize;
  background: transparent;
}
.resize-handle:hover { background: var(--mj-accent); }

.body-scroll {
  flex: 1;
  overflow-y: auto;
  overflow-x: auto;
  position: relative;
}

.body-inner { position: relative; }

.row {
  display: flex;
  align-items: stretch;
  border-bottom: 1px solid var(--mj-border);
  cursor: default;
}
.row:hover { background: var(--mj-bg-muted); }
.row[aria-selected="true"] { background: var(--mj-dt-selected-row-bg, color-mix(in srgb, var(--mj-accent) 10%, transparent)); }

.cell {
  display: flex;
  align-items: center;
  padding: var(--mj-space-2) var(--mj-space-3);
  font-size: var(--mj-font-size-sm);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex-shrink: 0;
  min-width: 60px;
}
.cell:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: -2px;
}
.cell.editing { padding: 0; }
.cell.editing input {
  width: 100%; height: 100%;
  padding: var(--mj-space-2) var(--mj-space-3);
  border: none;
  background: transparent;
  font: inherit;
  color: inherit;
}

.spacer { flex-shrink: 0; }

.footer {
  display: flex;
  align-items: center;
  gap: var(--mj-space-3);
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

:host([loading]) .body-scroll { opacity: 0.5; pointer-events: none; }
`;

export class MjDataTable extends MjElement {
  static tagName = "mj-data-table";
  static styles = STYLES;
  static watched = ["mode", "selection", "sortable", "filterable", "resizable", "row-height", "loading", "empty-label", "select-all"];

  constructor() {
    super()
    this._columns = []
    this._rows = []
    this._dataSource = null
    this._sortState = null
    this._filterState = {}
    this._selectedRows = new Set()
    this._focusedCell = { row: 0, col: 0 }
    this._vw = null
    this._allRows = []
    this._tableId = nextId("mj-dt")
    this._filterTimers = {}
    this._resizeDrag = null
    this._editingCell = null
  }

  render() {
    const markup = `
      <div class="toolbar" part="toolbar"><slot name="toolbar"></slot></div>
      <div class="grid-root" part="grid-root" role="grid" tabindex="0"
           aria-rowcount="-1" aria-colcount="0" aria-label="Data table">
        <div class="header-row" part="header-row" role="row"></div>
        <div class="body-scroll" part="body">
          <div class="body-inner" part="body-inner"></div>
        </div>
      </div>
      <div class="footer" part="footer"><slot name="footer">
        <span class="row-count">0 rows</span>
      </slot></div>
    `
    return markup
  }

  afterRender() {
    this._gridRoot = this.$(".grid-root")
    this._headerRow = this.$(".header-row")
    this._bodyScroll = this.$(".body-scroll")
    this._bodyInner = this.$(".body-inner")
    this._rowCount = this.$(".row-count")

    const rowH = parseInt(this.getAttribute("row-height") || "40", 10)
    this._vw = new VirtualWindow({ rowHeight: rowH, overscan: 4, total: 0 })

    this.listen(this._gridRoot, "keydown", this._onGridKeydown.bind(this))
    this.listen(this._bodyScroll, "scroll", this._onScroll.bind(this))

    if (this._columns.length > 0) {
      this._buildGrid()
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._gridRoot === undefined || this._gridRoot === null) {
      return
    }
    if (name === "loading") {
      this._gridRoot.setAttribute("aria-busy", newValue !== null ? "true" : "false")
      if (newValue !== null) {
        announce("Loading data.")
      }
    }
    return
  }

  /* ----- grid construction ----- */

  _buildGrid() {
    this._renderHeaders()
    this._loadData()
    return
  }

  _renderHeaders() {
    this._headerRow.innerHTML = ""
    const sortable = this.hasAttribute("sortable")

    for (let idx = 0; idx < this._columns.length; idx = idx + 1) {
      const col = this._columns[idx]
      const cell = document.createElement("div")
      cell.className = "header-cell"
      cell.setAttribute("part", "header-cell")
      cell.setAttribute("role", "columnheader")
      cell.setAttribute("data-col-key", col.key)
      cell.tabIndex = idx === 0 ? 0 : -1

      const isColSortable = (col.sortable !== false && sortable === true) || col.sortable === true
      if (isColSortable === true) {
        cell.setAttribute("data-sortable", "true")
        cell.setAttribute("aria-sort", "none")
        this.listen(cell, "click", () => { this._handleSortClick(col.key) })
      }

      const width = col.width || "160px"
      cell.style.width = typeof width === "number" ? `${width}px` : width

      const label = document.createElement("span")
      label.textContent = col.label || col.key
      cell.appendChild(label)

      if (isColSortable === true) {
        const indicator = document.createElement("span")
        indicator.className = "sort-indicator"
        indicator.setAttribute("aria-hidden", "true")
        indicator.setAttribute("data-sort-key", col.key)
        indicator.textContent = "↕"
        cell.appendChild(indicator)
      }

      if (this.hasAttribute("resizable") === true || col.resizable === true) {
        const handle = document.createElement("div")
        handle.className = "resize-handle"
        handle.setAttribute("part", "resize-handle")
        handle.setAttribute("role", "separator")
        handle.setAttribute("aria-orientation", "vertical")
        this.listen(handle, "pointerdown", (e) => { this._startResize(e, col.key) })
        cell.appendChild(handle)
      }

      this._headerRow.appendChild(cell)
    }

    this._gridRoot.setAttribute("aria-colcount", String(this._columns.length))
    return
  }

  _loadData() {
    if (this._dataSource !== null) {
      const sortParam = this._sortState !== null ? this._sortState : undefined
      const filterKeys = Object.keys(this._filterState)
      const filterValue = filterKeys.length > 0 ? this._filterState[filterKeys[0]] : undefined
      this._dataSource.query({
        offset: 0,
        limit: 1000,
        sort: sortParam,
        filter: filterValue
      }).then((result) => {
        this._allRows = result.items
        this._vw.setTotal(result.total)
        this._gridRoot.setAttribute("aria-rowcount", String(result.total))
        this._renderRows()
        this._updateFooter(result.total)
        return
      })
    } else {
      let working = this._rows.slice()

      if (this._sortState !== null) {
        const key = this._sortState.key
        const dir = this._sortState.direction === "desc" ? -1 : 1
        working = working.sort((a, b) => {
          let order = 0
          if (a[key] < b[key]) {
            order = -1
          } else if (a[key] > b[key]) {
            order = 1
          }
          return order * dir
        })
      }

      const filterKeys = Object.keys(this._filterState)
      for (let fi = 0; fi < filterKeys.length; fi = fi + 1) {
        const fk = filterKeys[fi]
        const fv = this._filterState[fk]
        if (fv !== null && fv !== undefined && fv.length > 0) {
          const needle = fv.toLowerCase()
          working = working.filter((row) => {
            const cell = row[fk]
            if (cell === null || cell === undefined) {
              return false
            }
            return String(cell).toLowerCase().indexOf(needle) >= 0
          })
        }
      }

      this._allRows = working
      this._vw.setTotal(working.length)
      this._gridRoot.setAttribute("aria-rowcount", String(working.length))
      this._renderRows()
      this._updateFooter(working.length)
    }
    return
  }

  _renderRows() {
    const scrollTop = this._bodyScroll.scrollTop
    const viewH = this._bodyScroll.clientHeight || 400
    const win = this._vw.range(scrollTop, viewH)
    const scrollHeight = this._vw.scrollHeight()

    this._bodyInner.style.height = `${scrollHeight}px`
    this._bodyInner.style.position = "relative"

    const existing = this._bodyInner.querySelectorAll(".row")
    const existingArr = Array.from(existing)

    for (let i = win.start; i < win.end; i = i + 1) {
      const row = this._allRows[i]
      if (row === undefined) {
        continue
      }
      const top = win.offsetY + (i - win.start) * this._vw.rowHeight
      let rowEl = existingArr[i - win.start]

      if (rowEl === undefined || rowEl === null) {
        rowEl = this._createRowEl()
        this._bodyInner.appendChild(rowEl)
      }

      this._populateRow(rowEl, row, i, top)
    }

    const toRemove = existingArr.slice(win.end - win.start)
    for (let ri = 0; ri < toRemove.length; ri = ri + 1) {
      toRemove[ri].remove()
    }

    if (this._allRows.length === 0) {
      this._showEmpty()
    }
    return
  }

  _createRowEl() {
    const rowEl = document.createElement("div")
    rowEl.className = "row"
    rowEl.setAttribute("part", "row")
    rowEl.setAttribute("role", "row")
    return rowEl
  }

  _populateRow(rowEl, row, rowIndex, top) {
    const selection = this.getAttribute("selection") || "none"
    const rowKey = row.__key || String(rowIndex)

    rowEl.style.position = "absolute"
    rowEl.style.top = `${top}px`
    rowEl.style.width = "100%"
    rowEl.setAttribute("data-row-key", rowKey)
    rowEl.setAttribute("aria-rowindex", String(rowIndex + 1))

    const isSelected = this._selectedRows.has(rowKey)
    if (selection !== "none") {
      rowEl.setAttribute("aria-selected", isSelected === true ? "true" : "false")
    }

    rowEl.innerHTML = ""

    for (let ci = 0; ci < this._columns.length; ci = ci + 1) {
      const col = this._columns[ci]
      const cellEl = document.createElement("div")
      cellEl.className = "cell"
      cellEl.setAttribute("part", "cell")
      cellEl.setAttribute("role", "gridcell")
      cellEl.setAttribute("aria-colindex", String(ci + 1))
      cellEl.setAttribute("data-row-key", rowKey)
      cellEl.setAttribute("data-col-key", col.key)
      cellEl.tabIndex = -1

      const width = col.width || "160px"
      cellEl.style.width = typeof width === "number" ? `${width}px` : width

      const value = row[col.key]
      cellEl.textContent = value !== undefined && value !== null ? String(value) : ""

      if (selection !== "none") {
        this.listen(cellEl, "click", () => { this._handleCellClick(rowKey, ci) })
      }

      this.listen(cellEl, "dblclick", () => { this._startCellEdit(rowEl, cellEl, rowKey, col.key, value) })

      rowEl.appendChild(cellEl)
    }

    const rowH = this._vw.rowHeight
    rowEl.style.height = `${rowH}px`
    return
  }

  _showEmpty() {
    this._bodyInner.innerHTML = ""
    const emptyEl = document.createElement("div")
    emptyEl.className = "empty-state"
    const slot = document.createElement("slot")
    slot.setAttribute("name", "empty")
    slot.textContent = this.getAttribute("empty-label") || "No results"
    emptyEl.appendChild(slot)
    this._bodyInner.appendChild(emptyEl)
    return
  }

  _updateFooter(total) {
    if (this._rowCount !== null) {
      this._rowCount.textContent = `${total} row${total !== 1 ? "s" : ""}`
    }
    return
  }

  _handleSortClick(key) {
    let direction = "asc"
    if (this._sortState !== null && this._sortState.key === key) {
      if (this._sortState.direction === "asc") {
        direction = "desc"
      } else {
        this._sortState = null
        this._updateSortIndicators()
        this._loadData()
        this.emit("mj-sort-change", { key: key, direction: null })
        announce("Sort cleared.")
        return
      }
    }
    this._sortState = { key: key, direction: direction }
    this._updateSortIndicators()
    this._loadData()
    this.emit("mj-sort-change", { key: key, direction: direction })
    announce(`Sorted by ${key} ${direction}.`)
    return
  }

  _updateSortIndicators() {
    const indicators = this._headerRow.querySelectorAll(".sort-indicator")
    const headers = this._headerRow.querySelectorAll("[aria-sort]")

    for (let i = 0; i < indicators.length; i = i + 1) {
      const ind = indicators[i]
      const sk = ind.getAttribute("data-sort-key")
      ind.className = "sort-indicator"
      if (this._sortState !== null && this._sortState.key === sk) {
        ind.className = "sort-indicator active"
        ind.textContent = this._sortState.direction === "asc" ? "↑" : "↓"
      } else {
        ind.textContent = "↕"
      }
    }

    for (let j = 0; j < headers.length; j = j + 1) {
      const hdr = headers[j]
      const ck = hdr.getAttribute("data-col-key")
      if (this._sortState !== null && this._sortState.key === ck) {
        hdr.setAttribute("aria-sort", this._sortState.direction === "asc" ? "ascending" : "descending")
      } else {
        hdr.setAttribute("aria-sort", "none")
      }
    }
    return
  }

  _handleCellClick(rowKey, colIdx) {
    const selection = this.getAttribute("selection") || "none"
    if (selection === "none") {
      return
    }
    if (selection === "single") {
      this._selectedRows.clear()
      this._selectedRows.add(rowKey)
    } else if (selection === "multi-row") {
      if (this._selectedRows.has(rowKey) === true) {
        this._selectedRows.delete(rowKey)
      } else {
        this._selectedRows.add(rowKey)
      }
    }
    this._refreshSelectionUI()
    this.emit("mj-selection-change", {
      selectedRows: Array.from(this._selectedRows),
      selectedCell: null
    })
    return
  }

  _refreshSelectionUI() {
    const rows = this._bodyInner.querySelectorAll(".row")
    for (let i = 0; i < rows.length; i = i + 1) {
      const rowEl = rows[i]
      const rk = rowEl.getAttribute("data-row-key")
      rowEl.setAttribute("aria-selected", this._selectedRows.has(rk) === true ? "true" : "false")
    }
    return
  }

  _startCellEdit(rowEl, cellEl, rowKey, colKey, currentValue) {
    const mode = this.getAttribute("mode") || "grid"
    if (mode === "view") {
      return
    }
    const col = this._columns.find((c) => c.key === colKey)
    if (col !== undefined && col.editable === false) {
      return
    }
    const proceed = this.emit("mj-cell-edit-start", { rowKey: rowKey, colKey: colKey, value: currentValue }, { cancelable: true })
    if (proceed === false) {
      return
    }
    cellEl.className = "cell editing"
    const input = document.createElement("input")
    input.type = "text"
    input.value = currentValue !== null && currentValue !== undefined ? String(currentValue) : ""
    cellEl.innerHTML = ""
    cellEl.appendChild(input)
    input.focus()
    this._editingCell = { rowKey: rowKey, colKey: colKey, oldValue: currentValue, input: input, cell: cellEl }

    const commit = () => {
      this._commitEdit()
    }
    this.listen(input, "blur", commit)
    this.listen(input, "keydown", (e) => {
      if (e.key === "Enter") {
        this._commitEdit()
      } else if (e.key === "Escape") {
        this._cancelEdit()
      }
    })
    return
  }

  _commitEdit() {
    if (this._editingCell === null) {
      return
    }
    const ec = this._editingCell
    const newValue = ec.input.value
    const proceed = this.emit("mj-cell-edit-commit", {
      rowKey: ec.rowKey, colKey: ec.colKey, oldValue: ec.oldValue, newValue: newValue
    }, { cancelable: true })

    if (proceed === true) {
      const rowIdx = this._allRows.findIndex((r) => (r.__key || "") === ec.rowKey)
      if (rowIdx >= 0) {
        this._allRows[rowIdx][ec.colKey] = newValue
      }
    }

    ec.cell.className = "cell"
    ec.cell.textContent = proceed === true ? newValue : String(ec.oldValue)
    this._editingCell = null
    return
  }

  _cancelEdit() {
    if (this._editingCell === null) {
      return
    }
    const ec = this._editingCell
    ec.cell.className = "cell"
    ec.cell.textContent = ec.oldValue !== null && ec.oldValue !== undefined ? String(ec.oldValue) : ""
    this._editingCell = null
    return
  }

  _startResize(event, colKey) {
    event.preventDefault()
    const startX = event.clientX
    const colIdx = this._columns.findIndex((c) => c.key === colKey)
    const headerCells = this._headerRow.querySelectorAll(".header-cell")
    const headerCell = headerCells[colIdx]
    const startWidth = headerCell.offsetWidth

    const onMove = (e) => {
      const delta = e.clientX - startX
      const newWidth = Math.max(60, startWidth + delta)
      headerCell.style.width = `${newWidth}px`
      const bodyCells = this._bodyInner.querySelectorAll(`.cell[aria-colindex="${colIdx + 1}"]`)
      for (let i = 0; i < bodyCells.length; i = i + 1) {
        bodyCells[i].style.width = `${newWidth}px`
      }
    }

    const onUp = (e) => {
      document.removeEventListener("pointermove", onMove)
      document.removeEventListener("pointerup", onUp)
      const finalWidth = Math.max(60, startWidth + (e.clientX - startX))
      this.emit("mj-column-resize", { key: colKey, width: finalWidth })
    }

    document.addEventListener("pointermove", onMove)
    document.addEventListener("pointerup", onUp)
    return
  }

  _onScroll() {
    window.requestAnimationFrame(() => {
      this._renderRows()
    })
    return
  }

  _onGridKeydown(event) {
    const cells = this._bodyInner.querySelectorAll(".cell")
    if (cells.length === 0) {
      return
    }

    const colCount = this._columns.length
    const rowCount = Math.floor(cells.length / colCount)
    const cur = this._focusedCell
    let nextRow = cur.row
    let nextCol = cur.col

    if (event.key === "ArrowDown") {
      event.preventDefault()
      nextRow = Math.min(nextRow + 1, rowCount - 1)
    } else if (event.key === "ArrowUp") {
      event.preventDefault()
      nextRow = Math.max(nextRow - 1, 0)
    } else if (event.key === "ArrowRight") {
      event.preventDefault()
      nextCol = Math.min(nextCol + 1, colCount - 1)
    } else if (event.key === "ArrowLeft") {
      event.preventDefault()
      nextCol = Math.max(nextCol - 1, 0)
    } else if (event.key === "Home") {
      event.preventDefault()
      nextCol = 0
    } else if (event.key === "End") {
      event.preventDefault()
      nextCol = colCount - 1
    } else if (event.key === "Escape" && this._editingCell !== null) {
      this._cancelEdit()
      return
    } else {
      return
    }

    const targetIdx = nextRow * colCount + nextCol
    const targetCell = cells[targetIdx]
    if (targetCell !== undefined && targetCell !== null) {
      for (let i = 0; i < cells.length; i = i + 1) {
        cells[i].tabIndex = -1
      }
      targetCell.tabIndex = 0
      targetCell.focus()
      this._focusedCell = { row: nextRow, col: nextCol }
    }
    return
  }

  _onScroll() {
    window.requestAnimationFrame(() => {
      this._renderRows()
    })
    return
  }

  /* ----- scriptable API ----- */

  get columns() {
    return this._columns
  }

  set columns(value) {
    this._columns = Array.isArray(value) === true ? value : []
    if (this._headerRow !== undefined && this._headerRow !== null) {
      this._buildGrid()
    }
    return
  }

  get rows() {
    return this._rows
  }

  set rows(value) {
    this._rows = Array.isArray(value) === true ? value : []
    if (this._bodyInner !== undefined && this._bodyInner !== null) {
      this._loadData()
    }
    return
  }

  get dataSource() {
    return this._dataSource
  }

  set dataSource(value) {
    this._dataSource = value !== null && value !== undefined ? new DataSource(value) : null
    if (this._bodyInner !== undefined && this._bodyInner !== null) {
      this._loadData()
    }
    return
  }

  get sortState() {
    return this._sortState
  }

  set sortState(value) {
    this._sortState = value !== null && value !== undefined ? value : null
    if (this._headerRow !== undefined && this._headerRow !== null) {
      this._updateSortIndicators()
      this._loadData()
    }
    return
  }

  get selectedRows() {
    return this._selectedRows
  }

  selectRow(key) {
    this._selectedRows.add(key)
    this._refreshSelectionUI()
    return
  }

  clearSelection() {
    this._selectedRows.clear()
    this._refreshSelectionUI()
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
