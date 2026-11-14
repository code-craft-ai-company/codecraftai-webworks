/*
 * mjdatatable.js
 *
 * <mj-data-table> -- interactive data grid with sorting, per-column and global
 * filtering, column resize, row selection, cell editing, and virtualized row
 * rendering. Implements the WAI-ARIA grid pattern with a roving tabindex over
 * header cells and data cells.
 *
 * Data comes from the `rows` property (client-side sort and filter) or from a
 * `dataSource` (array, fetcher function or adapter object -- see
 * core/collection.js), which is queried page by page for the visible window.
 *
 * Row identity: the `row-key` attribute names the field that identifies a row.
 * Without it a row's `__key` is used, and failing that an id that stays with
 * the row OBJECT for its lifetime, so selection and edits follow the record
 * through sorting and filtering.
 *
 * Keyboard: arrows / Home / End / Ctrl+Home / Ctrl+End / PageUp / PageDown move
 * between cells; Enter or Space on a sortable header cycles its sort; Space
 * toggles row selection (Shift+Space extends a range, Ctrl+A selects all in
 * multi-row mode); Enter or F2 edits a cell, Enter commits, Escape cancels.
 *
 * Events: mj-sort-change, mj-filter-change, mj-selection-change,
 * mj-cell-edit-start (cancelable), mj-cell-edit-commit (cancelable),
 * mj-column-resize, mj-load-more, mj-load-error.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { DataSource, VirtualWindow, sortItems, itemMatchesText, itemMatchesFilters } from "../core/collection.js";
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

/*
 * The header rows sit inside the body's scroll container and stick to its
 * top: they scroll sideways with the rows, and the grid's tab stop (a header
 * cell or a data cell) is always inside the region that scrolls. The header
 * is as wide as the columns, so its background and border follow the rows.
 */
.header-viewport {
  position: sticky;
  inset-block-start: 0;
  z-index: 1;
  inline-size: max-content;
  min-inline-size: 100%;
  background: var(--mj-dt-header-bg, var(--mj-bg-subtle));
  border-block-end: 2px solid var(--mj-border-strong);
}

.header-row,
.filter-row {
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
  position: relative;
  overflow: hidden;
  flex-shrink: 0;
  min-inline-size: 60px;
  box-sizing: border-box;
  cursor: default;
}
.header-cell[data-sortable="true"] { cursor: pointer; }
.header-cell[data-sortable="true"]:hover { background: var(--mj-bg-muted); }
.header-cell:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: -2px; }

.header-label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.sort-indicator { font-size: 0.7em; opacity: 0.5; margin-inline-start: auto; }
.sort-indicator.active { opacity: 1; }

.resize-handle {
  position: absolute;
  inset-inline-end: 0;
  inset-block: 0;
  inline-size: 6px;
  cursor: col-resize;
  background: transparent;
  touch-action: none;
}
.resize-handle:hover { background: var(--mj-accent); }

.filter-cell {
  flex-shrink: 0;
  min-inline-size: 60px;
  box-sizing: border-box;
  padding: 0 var(--mj-space-2) var(--mj-space-2) var(--mj-space-2);
}
.filter-input {
  inline-size: 100%;
  box-sizing: border-box;
  padding: var(--mj-space-1) var(--mj-space-2);
  font: inherit;
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text);
  background: var(--mj-surface);
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-sm);
}
.filter-input:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

/*
 * Without an explicit host height the body is as tall as its header and rows,
 * with the rows up to --mj-dt-body-max-height, then it scrolls. A host with
 * its own height wins: the body grows or shrinks to fill it.
 * --mj-dt-content-height (header and rows) and --_dt-header-height are set by
 * the component; the scroll padding keeps a row scrolled into view from
 * ending up under the sticky header.
 */
.body-scroll {
  flex: 1 1 min(
    var(--mj-dt-content-height, 0px),
    calc(var(--mj-dt-body-max-height, 400px) + var(--_dt-header-height, 0px))
  );
  min-block-size: 0;
  overflow: auto;
  position: relative;
  scroll-padding-block-start: var(--_dt-header-height, 0px);
}

.body-inner { position: relative; }

.row {
  display: flex;
  align-items: stretch;
  position: absolute;
  inset-inline: 0;
  box-sizing: border-box;
  border-block-end: 1px solid var(--mj-border);
  cursor: default;
}
.row:hover { background: var(--mj-bg-muted); }
.row[aria-selected="true"] { background: var(--mj-dt-selected-row-bg, color-mix(in srgb, var(--mj-accent) 10%, transparent)); }
.row[aria-busy="true"] { opacity: 0.5; }

.cell {
  display: flex;
  align-items: center;
  padding: var(--mj-space-2) var(--mj-space-3);
  font-size: var(--mj-font-size-sm);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex-shrink: 0;
  min-inline-size: 60px;
  box-sizing: border-box;
}
.cell:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: -2px;
}
.cell.editing { padding: 0; }
.cell.editing input {
  inline-size: 100%;
  block-size: 100%;
  box-sizing: border-box;
  padding: var(--mj-space-2) var(--mj-space-3);
  border: none;
  background: var(--mj-surface);
  font: inherit;
  color: inherit;
}

.footer {
  display: flex;
  align-items: center;
  gap: var(--mj-space-3);
  padding: var(--mj-space-2) var(--mj-space-3);
  border-block-start: 1px solid var(--mj-border);
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text-muted);
  flex-shrink: 0;
}

.load-error { color: var(--mj-color-danger); }
.load-error:empty { display: none; }

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--mj-space-7);
  color: var(--mj-text-muted);
}

/*
 * Loading: the rows stay readable (a fade would take muted cells under 4.5:1)
 * and take no input; the header's bottom border pulses in the accent colour,
 * and the grid reports aria-busy.
 */
:host([loading]) .body-inner { pointer-events: none; }
:host([loading]) .header-viewport {
  border-block-end-color: var(--mj-accent);
  animation: mj-dt-loading 1.2s ease-in-out infinite alternate;
}
@keyframes mj-dt-loading {
  from { border-block-end-color: var(--mj-border-strong); }
  to { border-block-end-color: var(--mj-accent); }
}
@media (prefers-reduced-motion: reduce) {
  :host([loading]) .header-viewport { animation: none; }
}
`;

const DEFAULT_COLUMN_WIDTH = "160px";
const MIN_COLUMN_WIDTH = 60;
const DEFAULT_PAGE_SIZE = 100;
const FILTER_DEBOUNCE_MS = 300;

/* Controls inside a cell whose click must not also toggle the row selection. */
const INTERACTIVE_SELECTOR = "a[href], button, input, select, textarea, label, mj-row-selector";

/*
 * Apply row-level styling / data hooks to a virtualized row.
 * Mirrors mj-table's row hooks so consumers can move data-table
 * styling onto ::part() and per-row class hooks. Same input
 * shape: `rowClass` is a string / string[] / callback; `rowAttrs`
 * is a `(row, idx) => attrs` callback.
 *
 * Returns the attribute names it set, so a recycled row element can
 * drop them before it shows another record.
 */
function _applyDataRowHooks(rowEl, row, rowIdx, rowClass, rowAttrs) {
    const appliedNames = []
    if (rowClass !== null && rowClass !== undefined) {
        let resolved = rowClass
        if (typeof rowClass === "function") {
            resolved = rowClass(row, rowIdx)
        }
        if (typeof resolved === "string" && resolved.length > 0) {
            for (const token of resolved.split(/\s+/)) {
                if (token.length > 0) {
                    rowEl.classList.add(token)
                }
            }
        } else if (Array.isArray(resolved) === true) {
            for (const token of resolved) {
                if (typeof token === "string" && token.length > 0) {
                    rowEl.classList.add(token)
                }
            }
        }
    }
    if (typeof rowAttrs === "function") {
        const attrs = rowAttrs(row, rowIdx) || {}
        for (const name of Object.keys(attrs)) {
            const value = attrs[name]
            if (value === null || value === undefined || value === false) {
                rowEl.removeAttribute(name)
            } else if (value === true) {
                rowEl.setAttribute(name, "")
                appliedNames.push(name)
            } else {
                rowEl.setAttribute(name, String(value))
                appliedNames.push(name)
            }
        }
    }
    return appliedNames
}

/*
 * Apply column-level cell hooks. `col.cellClass` is a string /
 * string[] / callback; `col.cellAttrs` is a callback returning a
 * name -> value map. Same shape as mj-table.
 */
function _applyDataCellHooks(cellEl, row, col, rowIdx) {
    if (col.cellClass !== null && col.cellClass !== undefined) {
        let resolved = col.cellClass
        if (typeof col.cellClass === "function") {
            resolved = col.cellClass(row, col, rowIdx)
        }
        if (typeof resolved === "string" && resolved.length > 0) {
            for (const token of resolved.split(/\s+/)) {
                if (token.length > 0) {
                    cellEl.classList.add(token)
                }
            }
        } else if (Array.isArray(resolved) === true) {
            for (const token of resolved) {
                if (typeof token === "string" && token.length > 0) {
                    cellEl.classList.add(token)
                }
            }
        }
    }
    if (typeof col.cellAttrs === "function") {
        const attrs = col.cellAttrs(row, col, rowIdx) || {}
        for (const name of Object.keys(attrs)) {
            const value = attrs[name]
            if (value === null || value === undefined || value === false) {
                cellEl.removeAttribute(name)
            } else if (value === true) {
                cellEl.setAttribute(name, "")
            } else {
                cellEl.setAttribute(name, String(value))
            }
        }
    }
    return
}

/*
 * Populate a single data-cell.
 *
 *   - When `col.render` is a function, call `render(row, col, rowIdx)`
 *     and use the return value:
 *       * a string / number -> textContent
 *       * a Node / Element -> appended as a child
 *       * an array or NodeList of nodes -> all appended
 *       * a DocumentFragment -> appended whole
 *       * null / undefined -> empty cell
 *   - Otherwise fall back to text rendering of the row's raw value
 *     (unchanged behavior for callers that don't supply `render`).
 *
 * Cells with a `render` hook stay non-editable: inline-edit only
 * makes sense for plain-text values where the cell's own content
 * is the canonical representation.
 */
function _fillDataCell(cell, value, row, col, rowIdx) {
    let rendered = value
    if (typeof col.render === "function") {
        rendered = col.render(row, col, rowIdx)
    }
    cell.replaceChildren()
    if (rendered === null || rendered === undefined) {
        cell.textContent = ""
        return
    }
    if (typeof rendered === "string" || typeof rendered === "number") {
        cell.textContent = String(rendered)
        return
    }
    if (rendered instanceof Node) {
        cell.appendChild(rendered)
        return
    }
    if (Array.isArray(rendered) === true || rendered instanceof NodeList) {
        for (const node of rendered) {
            if (node instanceof Node) {
                cell.appendChild(node)
            }
        }
        return
    }
    cell.textContent = String(rendered)
    return
}

/* The CSS width of a column: a number is pixels, a string is used as given. */
function _columnWidthCss(col) {
    let width = DEFAULT_COLUMN_WIDTH
    if (col.width !== undefined && col.width !== null && col.width !== "") {
        width = typeof col.width === "number" ? `${col.width}px` : String(col.width)
    }
    return width
}

function _columnLabel(col) {
    const label = col.label !== undefined && col.label !== null ? String(col.label) : String(col.key)
    return label
}

let ROW_KEY_SEQ = 0;

export class MjDataTable extends MjElement {
  static tagName = "mj-data-table";
  static styles = STYLES;
  static watched = [
    "mode", "selection", "sortable", "filterable", "resizable", "row-height", "row-key",
    "page-size", "loading", "empty-label", "label", "aria-label"
  ];

  constructor() {
    super()
    this._columns = []
    this._rows = []
    this._rowClass = null
    this._rowAttrs = null
    this._dataSource = null
    this._sortState = null
    this._filterState = {}
    this._globalFilter = ""
    this._filterTimers = {}

    /* Selection: row keys (strings), the row objects behind them, range anchor. */
    this._selectedRows = new Set()
    this._selectedRowData = new Map()
    this._selectionAnchor = -1

    /*
     * The focused cell in DATA coordinates: `row` is an index into the
     * current view (sorted and filtered), or -1 for the header row.
     */
    this._focus = { row: -1, col: 0 }
    this._tabStopEl = null

    /* Client mode: the sorted + filtered rows. Remote mode: loaded pages. */
    this._viewRows = []
    this._pages = new Map()
    this._pendingPages = new Set()
    this._generation = 0
    this._total = 0
    this._loadError = null

    /* Stable ids for row objects that carry no key of their own. */
    this._objectKeys = new WeakMap()

    /* Rendered row elements by view index, plus spares for recycling. */
    this._rowEls = new Map()
    this._rowPool = []
    this._hookAttrs = new WeakMap()
    this._dataVersion = 0

    this._vw = null
    this._tableId = nextId("mj-dt")
    this._resizeDrag = null
    this._suppressHeaderClick = false
    this._editingCell = null
    this._emptyEl = null
    this._scrollFrame = 0
  }

  render() {
    const markup = `
      <div class="toolbar" part="toolbar"><slot name="toolbar"></slot></div>
      <div class="grid-root" part="grid-root" role="grid"
           aria-rowcount="-1" aria-colcount="0">
        <div class="body-scroll" part="body">
          <div class="header-viewport">
            <div class="header-row" part="header-row" role="row" aria-rowindex="1"></div>
          </div>
          <div class="body-inner" part="body-inner"></div>
        </div>
      </div>
      <div class="footer" part="footer"><slot name="footer">
        <span class="row-count"></span>
        <span class="load-error" role="alert"></span>
      </slot></div>
    `
    return markup
  }

  afterRender() {
    this._gridRoot = this.$(".grid-root")
    this._headerViewport = this.$(".header-viewport")
    this._headerRow = this.$(".header-row")
    this._filterRow = null
    this._bodyScroll = this.$(".body-scroll")
    this._bodyInner = this.$(".body-inner")
    this._rowCount = this.$(".row-count")
    this._loadErrorEl = this.$(".load-error")
    this._rowCount.textContent = t("mj.dataTable.rowCount", { count: 0 })

    /* A fresh shadow tree: nothing rendered earlier is still attached. */
    this._rowEls = new Map()
    this._rowPool = []
    this._emptyEl = null
    this._tabStopEl = null
    this._editingCell = null

    const rowH = this._rowHeight()
    this._vw = new VirtualWindow({ rowHeight: rowH, overscan: 4, total: 0 })

    this.listen(this._gridRoot, "keydown", this._onGridKeydown.bind(this))
    this.listen(this._bodyScroll, "scroll", this._onScroll.bind(this))

    /* One delegated listener per interaction instead of one per cell. */
    this.listen(this._bodyInner, "click", this._onBodyClick.bind(this))
    this.listen(this._bodyInner, "dblclick", this._onBodyDblClick.bind(this))
    this.listen(this._bodyInner, "focusout", this._onBodyFocusOut.bind(this))
    this.listen(this._headerViewport, "click", this._onHeaderClick.bind(this))
    this.listen(this._headerViewport, "input", this._onFilterInput.bind(this))
    this.listen(this._headerViewport, "pointerdown", this._onResizePointerDown.bind(this))
    this.listen(this._headerViewport, "pointermove", this._onResizePointerMove.bind(this))
    this.listen(this._headerViewport, "pointerup", this._onResizePointerUp.bind(this))
    this.listen(this._headerViewport, "pointercancel", this._onResizePointerUp.bind(this))

    this._setupResizeObserver()
    this.onTeardown(() => { this._clearTimers() })

    this._syncGridLabel()
    this._gridRoot.setAttribute("aria-busy", this.hasAttribute("loading") === true ? "true" : "false")

    if (this._columns.length > 0) {
      this._buildGrid()
    } else if (this._dataSource !== null) {
      this._loadData()
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._gridRoot === undefined || this._gridRoot === null) {
      return
    }
    if (name === "loading") {
      this._gridRoot.setAttribute("aria-busy", newValue !== null ? "true" : "false")
      if (newValue !== null && oldValue === null) {
        announce(t("mj.dataTable.loadingAnnouncement"))
      }
    }
    if (name === "label" || name === "aria-label") {
      this._syncGridLabel()
    }
    if (name === "sortable" || name === "resizable" || name === "filterable") {
      this._renderHeaders()
      this._renderRows()
    }
    if (name === "row-height") {
      this._vw.rowHeight = this._rowHeight()
      this._invalidateRows()
      this._renderRows()
    }
    if (name === "selection") {
      if (newValue === null || newValue === "none") {
        this._selectedRows.clear()
        this._selectedRowData.clear()
      }
      this._invalidateRows()
      this._renderRows()
    }
    if (name === "row-key" && oldValue !== newValue) {
      this._selectedRows.clear()
      this._selectedRowData.clear()
      this._invalidateRows()
      this._renderRows()
    }
    if (name === "page-size" && oldValue !== newValue && this._dataSource !== null) {
      this._loadData()
    }
    if (name === "empty-label") {
      this._syncEmptyState()
    }
    return
  }

  /* Move focus to the cell that is the grid's single tab stop. */
  focus(options) {
    const target = this._focusTarget()
    if (target !== null) {
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

  _pageSize() {
    const parsed = parseInt(this.getAttribute("page-size") || String(DEFAULT_PAGE_SIZE), 10)
    const size = Number.isNaN(parsed) === true || parsed <= 0 ? DEFAULT_PAGE_SIZE : parsed
    return size
  }

  _selectionMode() {
    const mode = this.getAttribute("selection") || "none"
    return mode
  }

  _syncGridLabel() {
    const label = this.getAttribute("label") || this.getAttribute("aria-label") || t("mj.dataTable.label")
    this._gridRoot.setAttribute("aria-label", label)
    return
  }

  _isColumnSortable(col) {
    const tableSortable = this.hasAttribute("sortable")
    const sortable = (col.sortable !== false && tableSortable === true) || col.sortable === true
    return sortable
  }

  _isColumnEditable(col) {
    const mode = this.getAttribute("mode") || "grid"
    const editable = mode !== "view" && col.editable !== false && typeof col.render !== "function"
    return editable
  }

  /* Number of rows above the first data row (header, plus the filter row). */
  _headerRowCount() {
    const count = this._filterRow !== null ? 2 : 1
    return count
  }

  /*
   * The identity of a row: the `row-key` field, else `__key`, else an id
   * tied to the row object. Always a string.
   */
  _keyForRow(row, rowIndex) {
    let key = `index-${rowIndex}`

    if (row !== null && row !== undefined && typeof row === "object") {
      const field = this.getAttribute("row-key")
      if (field !== null && field.length > 0 && row[field] !== undefined && row[field] !== null) {
        key = String(row[field])
      } else if (row.__key !== undefined && row.__key !== null) {
        key = String(row.__key)
      } else {
        let generated = this._objectKeys.get(row)
        if (generated === undefined) {
          ROW_KEY_SEQ = ROW_KEY_SEQ + 1
          generated = `row-${ROW_KEY_SEQ}`
          this._objectKeys.set(row, generated)
        }
        key = generated
      }
    }

    return key
  }

  /* The row at a view index, or undefined when it is not loaded (yet). */
  _rowAt(rowIndex) {
    let row = undefined

    if (this._dataSource !== null) {
      const pageSize = this._pageSize()
      const page = this._pages.get(Math.floor(rowIndex / pageSize))
      if (page !== undefined) {
        row = page[rowIndex % pageSize]
      }
    } else {
      row = this._viewRows[rowIndex]
    }

    return row
  }

  /* ----- grid construction ----- */

  _buildGrid() {
    this._renderHeaders()
    this._loadData()
    return
  }

  _renderHeaders() {
    const focusWasInside = this._focusIsInGrid()
    this._headerRow.replaceChildren()
    const resizable = this.hasAttribute("resizable")

    for (let idx = 0; idx < this._columns.length; idx = idx + 1) {
      const col = this._columns[idx]
      const cell = document.createElement("div")
      cell.className = "header-cell"
      cell.setAttribute("part", "header-cell")
      cell.setAttribute("role", "columnheader")
      cell.setAttribute("data-col-key", col.key)
      cell.setAttribute("data-col-index", String(idx))
      cell.setAttribute("aria-colindex", String(idx + 1))
      cell.tabIndex = -1

      const isColSortable = this._isColumnSortable(col)
      if (isColSortable === true) {
        cell.setAttribute("data-sortable", "true")
        cell.setAttribute("aria-sort", "none")
      }

      cell.style.width = _columnWidthCss(col)

      const label = document.createElement("span")
      label.className = "header-label"
      label.textContent = _columnLabel(col)
      cell.appendChild(label)

      if (isColSortable === true) {
        const indicator = document.createElement("span")
        indicator.className = "sort-indicator"
        indicator.setAttribute("aria-hidden", "true")
        indicator.setAttribute("data-sort-key", col.key)
        indicator.textContent = "↕"
        cell.appendChild(indicator)
      }

      if (resizable === true || col.resizable === true) {
        const handle = document.createElement("div")
        handle.className = "resize-handle"
        handle.setAttribute("part", "resize-handle")
        handle.setAttribute("aria-hidden", "true")
        cell.appendChild(handle)
      }

      this._headerRow.appendChild(cell)
    }

    this._renderFilterRow()
    this._updateSortIndicators()
    this._gridRoot.setAttribute("aria-colcount", String(this._columns.length))

    if (this._focus.col >= this._columns.length) {
      this._focus.col = Math.max(0, this._columns.length - 1)
    }
    this._syncColumnMetrics()
    this._syncTabStop()
    if (focusWasInside === true) {
      this._restoreFocus()
    }
    return
  }

  /*
   * The second header row with one text filter per filterable column. Present
   * only while the `filterable` attribute is set.
   */
  _renderFilterRow() {
    if (this._filterRow !== null) {
      this._filterRow.remove()
      this._filterRow = null
    }
    if (this.hasAttribute("filterable") === false || this._columns.length === 0) {
      return
    }

    const filterRow = document.createElement("div")
    filterRow.className = "filter-row"
    filterRow.setAttribute("part", "filter-row")
    filterRow.setAttribute("role", "row")
    filterRow.setAttribute("aria-rowindex", "2")

    for (let idx = 0; idx < this._columns.length; idx = idx + 1) {
      const col = this._columns[idx]
      const cell = document.createElement("div")
      cell.className = "filter-cell"
      cell.setAttribute("role", "gridcell")
      cell.setAttribute("aria-colindex", String(idx + 1))
      cell.setAttribute("data-col-index", String(idx))
      cell.style.width = _columnWidthCss(col)

      if (col.filterable !== false) {
        const input = document.createElement("input")
        input.type = "search"
        input.className = "filter-input"
        input.setAttribute("part", "filter-input")
        input.setAttribute("data-filter-key", col.key)
        input.setAttribute("aria-label", t("mj.dataTable.filterColumn", { label: _columnLabel(col) }))
        const current = this._filterState[col.key]
        input.value = current !== undefined && current !== null ? String(current) : ""
        cell.appendChild(input)
      }

      filterRow.appendChild(cell)
    }

    this._headerViewport.appendChild(filterRow)
    this._filterRow = filterRow
    return
  }

  /*
   * Keep the rows as wide as the columns. The header shares the rows' scroll
   * container, so it needs no alignment of its own.
   */
  _syncColumnMetrics() {
    const headerCells = this._headerRow.querySelectorAll(".header-cell")
    let totalWidth = 0
    for (let i = 0; i < headerCells.length; i = i + 1) {
      totalWidth = totalWidth + headerCells[i].offsetWidth
    }
    this._bodyInner.style.minWidth = totalWidth > 0 ? `${totalWidth}px` : ""
    return
  }

  /* Height of the sticky header rows (column headers and filters). */
  _headerHeight() {
    const height = this._headerViewport.offsetHeight
    return height
  }

  /*
   * Height of the part of the scroll container that shows rows: below the
   * sticky header. 400 before the container has been laid out.
   */
  _rowViewHeight() {
    const clientHeight = this._bodyScroll.clientHeight
    let height = 400
    if (clientHeight > 0) {
      height = Math.max(0, clientHeight - this._headerHeight())
    }
    return height
  }

  /*
   * Size the scroll container for `contentHeight` px of rows (or empty state)
   * below the header; see the .body-scroll rule.
   */
  _setContentHeight(contentHeight) {
    const headerHeight = this._headerHeight()
    this._bodyScroll.style.setProperty("--_dt-header-height", `${headerHeight}px`)
    this._bodyScroll.style.setProperty("--mj-dt-content-height", `${headerHeight + contentHeight}px`)
    return
  }

  /* ----- data loading ----- */

  _loadData() {
    this._cancelEdit(false)
    this._dataVersion = this._dataVersion + 1

    if (this._dataSource !== null) {
      this._generation = this._generation + 1
      this._pages = new Map()
      this._pendingPages = new Set()
      this._total = 0
      this._setLoadError(null)
      this._requestPage(0)
      this._applyTotal()
    } else {
      let working = this._rows

      const columnKeys = this._columns.map((col) => col.key)
      const globalText = this._globalFilter
      if (globalText.trim().length > 0) {
        working = working.filter((row) => itemMatchesText(row, globalText, columnKeys))
      }
      if (Object.keys(this._filterState).length > 0) {
        working = working.filter((row) => itemMatchesFilters(row, this._filterState))
      }

      if (this._sortState !== null) {
        working = sortItems(working, this._sortRequest())
      } else if (working === this._rows) {
        working = working.slice()
      }

      this._viewRows = working
      this._total = working.length
      this._applyTotal()
    }
    return
  }

  /* The sort descriptor handed to the comparator / the data source. */
  _sortRequest() {
    let request = undefined

    if (this._sortState !== null) {
      const col = this._columns.find((c) => c.key === this._sortState.key)
      request = { key: this._sortState.key, direction: this._sortState.direction }
      if (col !== undefined) {
        if (col.type !== undefined) {
          request.type = col.type
        }
        if (typeof col.compare === "function") {
          request.compare = col.compare
        }
      }
    }

    return request
  }

  /* The filters with empty entries removed. */
  _activeFilters() {
    const active = {}
    const keys = Object.keys(this._filterState)
    for (let i = 0; i < keys.length; i = i + 1) {
      const value = this._filterState[keys[i]]
      if (value !== null && value !== undefined && String(value).trim().length > 0) {
        active[keys[i]] = String(value)
      }
    }
    return active
  }

  /*
   * Remote mode: fetch one page unless it is loaded or already on its way.
   * A response that belongs to an earlier sort / filter / source is dropped.
   */
  _requestPage(pageIndex) {
    if (this._dataSource === null || pageIndex < 0) {
      return
    }
    if (this._pages.has(pageIndex) === true || this._pendingPages.has(pageIndex) === true) {
      return
    }

    const pageSize = this._pageSize()
    const offset = pageIndex * pageSize
    const generation = this._generation
    const filters = this._activeFilters()
    const globalText = this._globalFilter.trim().length > 0 ? this._globalFilter : undefined

    this._pendingPages.add(pageIndex)
    this._gridRoot.setAttribute("aria-busy", "true")
    this.emit("mj-load-more", { offset: offset, pageSize: pageSize })

    this._dataSource.query({
      offset: offset,
      limit: pageSize,
      sort: this._sortRequest(),
      filter: globalText,
      filters: Object.keys(filters).length > 0 ? filters : undefined,
      filterKeys: this._columns.map((col) => col.key)
    }).then((result) => {
      if (generation !== this._generation || this._connected === false) {
        return
      }
      const items = Array.isArray(result.items) === true ? result.items : []
      this._pendingPages.delete(pageIndex)
      this._pages.set(pageIndex, items)

      if (result.total !== null && result.total !== undefined) {
        this._total = result.total
      } else {
        /* Unknown total: one extra row keeps the next page reachable. */
        const reached = offset + items.length + (items.length === pageSize ? 1 : 0)
        this._total = Math.max(this._total, reached)
      }

      this._setLoadError(null)
      this._dataVersion = this._dataVersion + 1
      this._applyTotal()
      return
    }).catch((error) => {
      if (generation !== this._generation || this._connected === false) {
        return
      }
      this._pendingPages.delete(pageIndex)
      this._setLoadError(error)
      this._applyTotal()
      this.emit("mj-load-error", { error: error, offset: offset })
      announce(t("mj.dataTable.loadFailed"), "assertive")
    })
    return
  }

  _setLoadError(error) {
    this._loadError = error
    if (this._loadErrorEl !== undefined && this._loadErrorEl !== null) {
      this._loadErrorEl.textContent = error !== null ? t("mj.dataTable.loadFailed") : ""
    }
    return
  }

  /* Push the current total into the virtual window, ARIA and the footer. */
  _applyTotal() {
    this._vw.setTotal(this._total)
    this._gridRoot.setAttribute("aria-rowcount", String(this._total + this._headerRowCount()))
    if (this._pendingPages.size === 0 && this.hasAttribute("loading") === false) {
      this._gridRoot.setAttribute("aria-busy", "false")
    }
    this._renderRows()
    this._updateFooter(this._total)
    return
  }

  /* ----- row rendering ----- */

  /* Force every rendered row to be populated again on the next render. */
  _invalidateRows() {
    this._dataVersion = this._dataVersion + 1
    return
  }

  _renderRows() {
    const total = this._total
    const focusWasInside = this._focusIsInGrid()

    if (this._focus.row >= total) {
      this._focus.row = total - 1
    }

    const scrollHeight = this._vw.scrollHeight()
    this._bodyInner.style.height = `${scrollHeight}px`
    this._setContentHeight(scrollHeight)
    this._syncEmptyState()

    /*
     * The rows start below the header in the scroll container, so a
     * scrollTop is also the offset of the first row in view.
     */
    const viewH = this._rowViewHeight()
    const win = this._vw.range(this._bodyScroll.scrollTop, viewH)

    /* The focused row stays rendered while scrolled away so focus survives. */
    const wanted = new Set()
    for (let i = win.start; i < win.end; i = i + 1) {
      wanted.add(i)
    }
    if (this._focus.row >= 0 && this._focus.row < total) {
      wanted.add(this._focus.row)
    }

    const renderedIndexes = Array.from(this._rowEls.keys())
    for (let ri = 0; ri < renderedIndexes.length; ri = ri + 1) {
      const index = renderedIndexes[ri]
      if (wanted.has(index) === false) {
        const stale = this._rowEls.get(index)
        this._rowEls.delete(index)
        stale.remove()
        this._rowPool.push(stale)
      }
    }

    const firstMissing = { start: -1, end: -1 }
    wanted.forEach((index) => {
      const row = this._rowAt(index)
      let rowEl = this._rowEls.get(index)

      if (rowEl === undefined) {
        rowEl = this._rowPool.length > 0 ? this._rowPool.pop() : this._createRowEl()
        rowEl._mjVersion = -1
        this._rowEls.set(index, rowEl)
        this._bodyInner.appendChild(rowEl)
      }

      if (rowEl._mjVersion !== this._dataVersion || rowEl._mjRow !== row) {
        this._populateRow(rowEl, row, index)
        rowEl._mjVersion = this._dataVersion
        rowEl._mjRow = row
      }

      if (row === undefined) {
        if (firstMissing.start < 0) {
          firstMissing.start = index
        }
        firstMissing.end = index
      }
    })

    if (this._dataSource !== null && firstMissing.start >= 0) {
      const pageSize = this._pageSize()
      const firstPage = Math.floor(firstMissing.start / pageSize)
      const lastPage = Math.floor(firstMissing.end / pageSize)
      for (let page = firstPage; page <= lastPage; page = page + 1) {
        this._requestPage(page)
      }
    }

    this._syncColumnMetrics()
    this._syncTabStop()
    if (focusWasInside === true) {
      this._restoreFocus()
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

  _populateRow(rowEl, row, rowIndex) {
    const selection = this._selectionMode()
    const rowKey = row !== undefined ? this._keyForRow(row, rowIndex) : ""
    const rowH = this._vw.rowHeight

    /* Drop whatever the previous record's hooks left on a recycled element. */
    const previousAttrs = this._hookAttrs.get(rowEl)
    if (previousAttrs !== undefined) {
      for (let ai = 0; ai < previousAttrs.length; ai = ai + 1) {
        rowEl.removeAttribute(previousAttrs[ai])
      }
    }
    rowEl.className = "row"

    rowEl.style.top = `${rowIndex * rowH}px`
    rowEl.style.height = `${rowH}px`
    rowEl.setAttribute("data-row-index", String(rowIndex))
    rowEl.setAttribute("data-row-key", rowKey)
    rowEl.setAttribute("aria-rowindex", String(rowIndex + 1 + this._headerRowCount()))

    if (selection !== "none" && row !== undefined) {
      const isSelected = this._selectedRows.has(rowKey)
      rowEl.setAttribute("aria-selected", isSelected === true ? "true" : "false")
    } else {
      rowEl.removeAttribute("aria-selected")
    }

    rowEl.replaceChildren()

    if (row === undefined) {
      /* Remote row that has not arrived yet. */
      rowEl.setAttribute("aria-busy", "true")
      this._hookAttrs.delete(rowEl)
    } else {
      rowEl.removeAttribute("aria-busy")
      const appliedAttrs = _applyDataRowHooks(rowEl, row, rowIndex, this._rowClass, this._rowAttrs)
      this._hookAttrs.set(rowEl, appliedAttrs)
    }

    for (let ci = 0; ci < this._columns.length; ci = ci + 1) {
      const col = this._columns[ci]
      const cellEl = document.createElement("div")
      cellEl.className = "cell"
      cellEl.setAttribute("part", "cell")
      cellEl.setAttribute("role", "gridcell")
      cellEl.setAttribute("aria-colindex", String(ci + 1))
      cellEl.setAttribute("data-row-key", rowKey)
      cellEl.setAttribute("data-col-key", col.key)
      cellEl.setAttribute("data-col-index", String(ci))
      cellEl.tabIndex = -1
      cellEl.style.width = _columnWidthCss(col)

      if (row !== undefined) {
        const value = row[col.key]
        _fillDataCell(cellEl, value, row, col, rowIndex)
        _applyDataCellHooks(cellEl, row, col, rowIndex)
      }

      rowEl.appendChild(cellEl)
    }
    return
  }

  /* Show the empty placeholder only while there is nothing to show. */
  _syncEmptyState() {
    const isEmpty = this._total === 0 && this._pendingPages.size === 0

    if (isEmpty === false) {
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
    const fallback = this._emptyEl.querySelector("slot")
    fallback.textContent = this.getAttribute("empty-label") || t("core.noResults")
    this._setContentHeight(this._emptyEl.offsetHeight)
    return
  }

  _updateFooter(total) {
    if (this._rowCount !== null) {
      this._rowCount.textContent = t("mj.dataTable.rowCount", { count: total })
    }
    return
  }

  /*
   * A new body size re-renders the rows. _renderRows() sets
   * --mj-dt-content-height on the observed .body-scroll (for the empty state
   * that height follows the width), which resizes it again when the grid has
   * no height of its own. Doing that inside the observer callback makes the
   * browser report "ResizeObserver loop completed with undelivered
   * notifications", so the render runs on the next animation frame, shared
   * with the scroll render; the resize it causes is then observed normally.
   */
  _setupResizeObserver() {
    if (typeof ResizeObserver === "undefined") {
      return
    }
    let lastHeight = -1
    let lastWidth = -1
    let lastHeaderHeight = -1
    const observer = new ResizeObserver(() => {
      const height = this._bodyScroll.clientHeight
      const width = this._bodyScroll.clientWidth
      const headerHeight = this._headerHeight()
      if (height !== lastHeight || width !== lastWidth || headerHeight !== lastHeaderHeight) {
        lastHeight = height
        lastWidth = width
        lastHeaderHeight = headerHeight
        this._scheduleRowRender()
      }
    })
    observer.observe(this._bodyScroll)
    /* The header can change height on its own (fonts, a wrapped filter row). */
    observer.observe(this._headerViewport)
    this.onTeardown(() => { observer.disconnect() })
    return
  }

  /* Render the rows on the next animation frame (once per frame). */
  _scheduleRowRender() {
    if (this._scrollFrame !== 0) {
      return
    }
    this._scrollFrame = window.requestAnimationFrame(() => {
      this._scrollFrame = 0
      this._renderRows()
    })
    return
  }

  _clearTimers() {
    const keys = Object.keys(this._filterTimers)
    for (let i = 0; i < keys.length; i = i + 1) {
      window.clearTimeout(this._filterTimers[keys[i]])
    }
    this._filterTimers = {}
    if (this._scrollFrame !== 0) {
      window.cancelAnimationFrame(this._scrollFrame)
      this._scrollFrame = 0
    }
    return
  }

  /* ----- focus (roving tabindex in data coordinates) ----- */

  /* The element for the focused cell, or null when it is not rendered. */
  _focusTarget() {
    let target = null

    if (this._headerRow === undefined || this._headerRow === null) {
      return target
    }

    if (this._focus.row < 0) {
      const headerCells = this._headerRow.querySelectorAll(".header-cell")
      if (headerCells.length > this._focus.col) {
        target = headerCells[this._focus.col]
      }
    } else {
      const rowEl = this._rowEls.get(this._focus.row)
      if (rowEl !== undefined && rowEl.children.length > this._focus.col) {
        target = rowEl.children[this._focus.col]
      }
    }

    return target
  }

  /* Exactly one cell is in the tab order: the focused one. */
  _syncTabStop() {
    const target = this._focusTarget()
    if (this._tabStopEl !== null && this._tabStopEl !== target) {
      this._tabStopEl.tabIndex = -1
    }
    if (target !== null) {
      target.tabIndex = 0
    }
    this._tabStopEl = target
    return
  }

  _focusIsInGrid() {
    let inside = false
    const active = this.shadowRoot.activeElement
    if (active !== null && active !== undefined && this._gridRoot !== undefined && this._gridRoot !== null) {
      const isFilterInput = active.classList.contains("filter-input")
      inside = this._gridRoot.contains(active) === true && isFilterInput === false
    }
    return inside
  }

  /* Put focus back on the focused cell after its element was replaced. */
  _restoreFocus() {
    const active = this.shadowRoot.activeElement
    const stillFocused = active !== null && active !== undefined && active.isConnected === true
    if (stillFocused === false) {
      const target = this._focusTarget()
      if (target !== null) {
        target.focus({ preventScroll: true })
      }
    }
    return
  }

  /*
   * Move the focused cell to (rowIndex, colIndex), scrolling the row into
   * the rendered window first. rowIndex -1 addresses the header row.
   */
  _focusCell(rowIndex, colIndex, moveFocus) {
    const lastRow = this._total - 1
    const lastCol = this._columns.length - 1
    if (lastCol < 0) {
      return
    }

    const row = Math.max(-1, Math.min(rowIndex, lastRow))
    const col = Math.max(0, Math.min(colIndex, lastCol))
    this._focus = { row: row, col: col }

    if (row >= 0) {
      const rowH = this._vw.rowHeight
      const top = row * rowH
      const viewH = this._rowViewHeight()
      if (top < this._bodyScroll.scrollTop) {
        this._bodyScroll.scrollTop = top
      } else if (top + rowH > this._bodyScroll.scrollTop + viewH) {
        this._bodyScroll.scrollTop = top + rowH - viewH
      }
    }

    this._renderRows()

    const target = this._focusTarget()
    if (target !== null && moveFocus !== false) {
      target.focus()
    }
    return
  }

  /* ----- sorting ----- */

  _handleSortClick(key) {
    const col = this._columns.find((c) => c.key === key)
    const label = col !== undefined ? _columnLabel(col) : key
    let direction = "asc"

    if (this._sortState !== null && this._sortState.key === key) {
      if (this._sortState.direction === "asc") {
        direction = "desc"
      } else {
        direction = null
      }
    }

    this._sortState = direction !== null ? { key: key, direction: direction } : null
    this._updateSortIndicators()
    this._loadData()
    this.emit("mj-sort-change", { key: key, direction: direction })

    if (direction === null) {
      announce(t("mj.dataTable.sortCleared"))
    } else if (direction === "asc") {
      announce(t("mj.dataTable.sortedAscending", { label: label }))
    } else {
      announce(t("mj.dataTable.sortedDescending", { label: label }))
    }
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

  _onHeaderClick(event) {
    if (this._suppressHeaderClick === true) {
      /* The click that ends a column-resize drag is not a sort request. */
      this._suppressHeaderClick = false
      return
    }
    const target = event.target
    if (!(target instanceof Element) || target.closest(".resize-handle") !== null) {
      return
    }
    const headerCell = target.closest(".header-cell")
    if (headerCell === null) {
      return
    }
    const colIndex = parseInt(headerCell.getAttribute("data-col-index"), 10)
    this._focus = { row: -1, col: colIndex }
    this._syncTabStop()
    if (headerCell.getAttribute("data-sortable") === "true") {
      this._handleSortClick(headerCell.getAttribute("data-col-key"))
    }
    return
  }

  /* ----- filtering ----- */

  _onFilterInput(event) {
    const input = event.target
    if (!(input instanceof HTMLInputElement) || input.classList.contains("filter-input") === false) {
      return
    }
    const key = input.getAttribute("data-filter-key")

    if (this._filterTimers[key] !== undefined) {
      window.clearTimeout(this._filterTimers[key])
    }
    this._filterTimers[key] = window.setTimeout(() => {
      delete this._filterTimers[key]
      this._applyColumnFilter(key, input.value)
    }, FILTER_DEBOUNCE_MS)
    return
  }

  /* Apply a filter typed by the user and report it. */
  _applyColumnFilter(key, value) {
    const text = value !== null && value !== undefined ? String(value) : ""
    const previous = this._filterState[key] !== undefined ? String(this._filterState[key]) : ""
    if (text === previous) {
      return
    }

    if (text.length > 0) {
      this._filterState[key] = text
    } else {
      delete this._filterState[key]
    }

    this._bodyScroll.scrollTop = 0
    this._loadData()
    this.emit("mj-filter-change", { key: key, value: text, filterState: Object.assign({}, this._filterState) })
    if (this._dataSource === null) {
      announce(t("mj.dataTable.resultCount", { count: this._total }))
    }
    return
  }

  /* ----- selection ----- */

  _onBodyClick(event) {
    const target = event.target
    if (!(target instanceof Element)) {
      return
    }
    const cell = target.closest(".cell")
    if (cell === null || cell.classList.contains("editing") === true) {
      return
    }
    const rowEl = cell.parentElement
    const rowIndex = parseInt(rowEl.getAttribute("data-row-index"), 10)
    const colIndex = parseInt(cell.getAttribute("data-col-index"), 10)

    this._focus = { row: rowIndex, col: colIndex }
    this._syncTabStop()

    /* A control rendered inside the cell handles its own click. */
    const interactive = target.closest(INTERACTIVE_SELECTOR)
    if (interactive !== null && cell.contains(interactive) === true) {
      return
    }

    this._selectFromInteraction(rowIndex, event.shiftKey === true)
    return
  }

  /*
   * Apply a user selection gesture to the row at `rowIndex`.
   *   single     the row becomes the only selected row
   *   multi-row  the row is toggled; with `extend` the range from the last
   *              toggled row to this one is selected
   */
  _selectFromInteraction(rowIndex, extend) {
    const selection = this._selectionMode()
    const row = this._rowAt(rowIndex)
    if (selection === "none" || row === undefined) {
      return
    }
    const rowKey = this._keyForRow(row, rowIndex)

    if (selection === "single") {
      this._selectedRows.clear()
      this._selectedRowData.clear()
      this._selectedRows.add(rowKey)
      this._selectedRowData.set(rowKey, row)
    } else if (selection === "multi-row") {
      if (extend === true && this._selectionAnchor >= 0) {
        const from = Math.min(this._selectionAnchor, rowIndex)
        const to = Math.max(this._selectionAnchor, rowIndex)
        for (let i = from; i <= to; i = i + 1) {
          const rangeRow = this._rowAt(i)
          if (rangeRow !== undefined) {
            const rangeKey = this._keyForRow(rangeRow, i)
            this._selectedRows.add(rangeKey)
            this._selectedRowData.set(rangeKey, rangeRow)
          }
        }
      } else if (this._selectedRows.has(rowKey) === true) {
        this._selectedRows.delete(rowKey)
        this._selectedRowData.delete(rowKey)
      } else {
        this._selectedRows.add(rowKey)
        this._selectedRowData.set(rowKey, row)
      }
    } else {
      return
    }

    this._selectionAnchor = rowIndex
    this._refreshSelectionUI()
    this._emitSelectionChange()
    return
  }

  _emitSelectionChange() {
    this.emit("mj-selection-change", {
      selectedRows: Array.from(this._selectedRows),
      rows: Array.from(this._selectedRowData.values()),
      selectedCell: null
    })
    return
  }

  _refreshSelectionUI() {
    if (this._bodyInner === undefined || this._bodyInner === null) {
      return
    }
    const selection = this._selectionMode()
    this._rowEls.forEach((rowEl) => {
      const rk = rowEl.getAttribute("data-row-key")
      if (selection === "none" || rowEl.hasAttribute("aria-busy") === true) {
        rowEl.removeAttribute("aria-selected")
      } else {
        rowEl.setAttribute("aria-selected", this._selectedRows.has(rk) === true ? "true" : "false")
      }
    })
    return
  }

  /* ----- cell editing ----- */

  _onBodyDblClick(event) {
    const target = event.target
    if (!(target instanceof Element)) {
      return
    }
    const cell = target.closest(".cell")
    if (cell === null || cell.classList.contains("editing") === true) {
      return
    }
    const rowIndex = parseInt(cell.parentElement.getAttribute("data-row-index"), 10)
    const colIndex = parseInt(cell.getAttribute("data-col-index"), 10)
    this._startCellEdit(rowIndex, colIndex)
    return
  }

  _startCellEdit(rowIndex, colIndex) {
    const col = this._columns[colIndex]
    const row = this._rowAt(rowIndex)
    const rowEl = this._rowEls.get(rowIndex)
    if (col === undefined || row === undefined || rowEl === undefined) {
      return
    }
    if (this._isColumnEditable(col) === false) {
      return
    }
    if (this._editingCell !== null) {
      this._commitEdit(false)
    }

    const cellEl = rowEl.children[colIndex]
    const rowKey = this._keyForRow(row, rowIndex)
    const currentValue = row[col.key]

    const proceed = this.emit("mj-cell-edit-start", { rowKey: rowKey, colKey: col.key, value: currentValue }, { cancelable: true })
    if (proceed === false) {
      return
    }

    const input = document.createElement("input")
    input.type = "text"
    input.setAttribute("aria-label", t("mj.dataTable.editCell", { label: _columnLabel(col) }))
    input.value = currentValue !== null && currentValue !== undefined ? String(currentValue) : ""
    cellEl.classList.add("editing")
    cellEl.replaceChildren(input)

    this._focus = { row: rowIndex, col: colIndex }
    this._syncTabStop()
    this._editingCell = {
      row: row, rowIndex: rowIndex, rowKey: rowKey, col: col, colKey: col.key,
      oldValue: currentValue, input: input, cell: cellEl
    }
    input.focus()
    input.select()
    return
  }

  /* Leaving the editor (click elsewhere, Tab) commits the edit. */
  _onBodyFocusOut(event) {
    if (this._editingCell !== null && event.target === this._editingCell.input) {
      this._commitEdit(false)
    }
    return
  }

  _commitEdit(refocus) {
    if (this._editingCell === null) {
      return
    }
    const ec = this._editingCell
    /* Cleared first: replacing the input fires focusout, which re-enters. */
    this._editingCell = null

    let newValue = ec.input.value
    if (typeof ec.oldValue === "number" && newValue.trim().length > 0 && Number.isNaN(Number(newValue)) === false) {
      /* A numeric column stays numeric so it keeps sorting as numbers. */
      newValue = Number(newValue)
    }

    const proceed = this.emit("mj-cell-edit-commit", {
      rowKey: ec.rowKey, colKey: ec.colKey, oldValue: ec.oldValue, newValue: newValue
    }, { cancelable: true })

    if (proceed === true) {
      ec.row[ec.colKey] = newValue
    }

    this._restoreEditedCell(ec, refocus)
    return
  }

  _cancelEdit(refocus) {
    if (this._editingCell === null) {
      return
    }
    const ec = this._editingCell
    this._editingCell = null
    this._restoreEditedCell(ec, refocus)
    return
  }

  _restoreEditedCell(ec, refocus) {
    ec.cell.classList.remove("editing")
    _fillDataCell(ec.cell, ec.row[ec.colKey], ec.row, ec.col, ec.rowIndex)
    if (refocus === true && ec.cell.isConnected === true) {
      ec.cell.focus()
    }
    return
  }

  /* ----- column resize ----- */

  _onResizePointerDown(event) {
    const target = event.target
    if (!(target instanceof Element) || target.classList.contains("resize-handle") === false) {
      return
    }
    event.preventDefault()
    const headerCell = target.parentElement
    const direction = window.getComputedStyle(this).direction === "rtl" ? -1 : 1

    this._resizeDrag = {
      colIndex: parseInt(headerCell.getAttribute("data-col-index"), 10),
      startX: event.clientX,
      startWidth: headerCell.offsetWidth,
      direction: direction,
      handle: target,
      width: headerCell.offsetWidth
    }

    /* Capture keeps move/up events coming while the pointer leaves the header. */
    if (typeof target.setPointerCapture === "function" && event.pointerId !== undefined) {
      try {
        target.setPointerCapture(event.pointerId)
      } catch (error) {
        /* Synthetic events carry no active pointer; the drag still works inside the header. */
      }
    }
    return
  }

  _onResizePointerMove(event) {
    if (this._resizeDrag === null) {
      return
    }
    const drag = this._resizeDrag
    const delta = (event.clientX - drag.startX) * drag.direction
    drag.width = Math.max(MIN_COLUMN_WIDTH, Math.round(drag.startWidth + delta))
    this._applyColumnWidth(drag.colIndex, drag.width)
    return
  }

  _onResizePointerUp(event) {
    if (this._resizeDrag === null) {
      return
    }
    const drag = this._resizeDrag
    this._resizeDrag = null
    const col = this._columns[drag.colIndex]

    /* Swallow the click this pointerup is about to produce on the header. */
    this._suppressHeaderClick = true
    window.setTimeout(() => { this._suppressHeaderClick = false }, 0)

    if (col !== undefined) {
      this.emit("mj-column-resize", { key: col.key, width: drag.width })
    }
    return
  }

  /* Store a new width on the column definition and apply it everywhere. */
  _applyColumnWidth(colIndex, width) {
    const col = this._columns[colIndex]
    if (col === undefined) {
      return
    }
    col.width = width
    const css = `${width}px`
    const selector = `[data-col-index="${colIndex}"]`
    const cells = this._gridRoot.querySelectorAll(`.header-cell${selector}, .filter-cell${selector}, .cell${selector}`)
    for (let i = 0; i < cells.length; i = i + 1) {
      cells[i].style.width = css
    }
    this._syncColumnMetrics()
    return
  }

  /* ----- scrolling ----- */

  /* The rows in view are rendered on the next frame. */
  _onScroll() {
    this._scheduleRowRender()
    return
  }

  /* ----- keyboard ----- */

  _onGridKeydown(event) {
    const target = event.target
    const key = event.key

    /* Keys typed into the cell editor belong to the editor. */
    if (this._editingCell !== null && target === this._editingCell.input) {
      if (key === "Enter") {
        event.preventDefault()
        this._commitEdit(true)
      } else if (key === "Escape") {
        event.preventDefault()
        event.stopPropagation()
        this._cancelEdit(true)
      }
      return
    }

    /* Filter inputs and controls rendered inside cells keep their own keys. */
    if (target instanceof Element) {
      const isCell = target.classList.contains("cell") === true || target.classList.contains("header-cell") === true
      if (isCell === false) {
        return
      }
    }

    const colCount = this._columns.length
    if (colCount === 0) {
      return
    }

    const cur = this._focus
    const lastRow = this._total - 1
    const pageRows = Math.max(1, Math.floor(this._rowViewHeight() / this._vw.rowHeight) - 1)
    const withCtrl = event.ctrlKey === true || event.metaKey === true
    let nextRow = cur.row
    let nextCol = cur.col
    let handled = true

    if (key === "ArrowDown") {
      nextRow = Math.min(cur.row + 1, lastRow)
    } else if (key === "ArrowUp") {
      nextRow = Math.max(cur.row - 1, -1)
    } else if (key === "ArrowRight") {
      nextCol = Math.min(cur.col + 1, colCount - 1)
    } else if (key === "ArrowLeft") {
      nextCol = Math.max(cur.col - 1, 0)
    } else if (key === "Home") {
      nextCol = 0
      if (withCtrl === true) {
        nextRow = lastRow >= 0 ? 0 : -1
      }
    } else if (key === "End") {
      nextCol = colCount - 1
      if (withCtrl === true) {
        nextRow = lastRow
      }
    } else if (key === "PageDown") {
      nextRow = Math.min(Math.max(cur.row, 0) + pageRows, lastRow)
    } else if (key === "PageUp") {
      nextRow = cur.row < 0 ? -1 : Math.max(cur.row - pageRows, 0)
    } else {
      handled = false
    }

    if (handled === true) {
      event.preventDefault()
      this._focusCell(nextRow, nextCol, true)
      return
    }

    if (cur.row < 0) {
      /* Header cell: Enter / Space cycles the sort. */
      if (key === "Enter" || key === " ") {
        const headerCell = this._focusTarget()
        if (headerCell !== null && headerCell.getAttribute("data-sortable") === "true") {
          event.preventDefault()
          this._handleSortClick(headerCell.getAttribute("data-col-key"))
        }
      }
      return
    }

    const col = this._columns[cur.col]
    const selection = this._selectionMode()

    if (key === " ") {
      if (selection !== "none") {
        event.preventDefault()
        this._selectFromInteraction(cur.row, event.shiftKey === true)
      }
    } else if (key === "F2") {
      event.preventDefault()
      this._startCellEdit(cur.row, cur.col)
    } else if (key === "Enter") {
      event.preventDefault()
      if (col !== undefined && this._isColumnEditable(col) === true) {
        this._startCellEdit(cur.row, cur.col)
      } else if (selection !== "none") {
        this._selectFromInteraction(cur.row, event.shiftKey === true)
      }
    } else if ((key === "a" || key === "A") && withCtrl === true && selection === "multi-row") {
      event.preventDefault()
      this.selectAll()
      this._emitSelectionChange()
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

  /*
   * Per-row hooks. Set `rowClass` to a string, a string[], or a
   * `(row, idx) => string | string[]` callback to add class names
   * to every virtualized row. Set `rowAttrs` to a callback
   * `(row, idx) => attrs` to stamp arbitrary attributes (typical:
   * row id for tests / styling).
   */
  get rowClass() {
    return this._rowClass
  }

  set rowClass(value) {
    this._rowClass = value
    if (this._bodyInner !== undefined && this._bodyInner !== null) {
      this._invalidateRows()
      this._renderRows()
    }
    return
  }

  get rowAttrs() {
    return this._rowAttrs
  }

  set rowAttrs(value) {
    this._rowAttrs = typeof value === "function" ? value : null
    if (this._bodyInner !== undefined && this._bodyInner !== null) {
      this._invalidateRows()
      this._renderRows()
    }
    return
  }

  get dataSource() {
    return this._dataSource
  }

  /*
   * An array, a fetcher `(query) => Promise<{ items, total }>`, or an adapter
   * object with `query(query)` / `fetch(query)` (which may resolve
   * `{ rows, total }`). null returns the table to the `rows` property.
   */
  set dataSource(value) {
    if (value instanceof DataSource) {
      this._dataSource = value
    } else if (value !== null && value !== undefined) {
      this._dataSource = new DataSource(value)
    } else {
      this._dataSource = null
    }
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

  /* Map of column key to filter text. Assigning it does not emit an event. */
  get filterState() {
    return this._filterState
  }

  set filterState(value) {
    const next = {}
    if (value !== null && value !== undefined && typeof value === "object") {
      const keys = Object.keys(value)
      for (let i = 0; i < keys.length; i = i + 1) {
        const text = value[keys[i]]
        if (text !== null && text !== undefined && String(text).length > 0) {
          next[keys[i]] = String(text)
        }
      }
    }
    this._filterState = next

    if (this._headerRow !== undefined && this._headerRow !== null) {
      const inputs = this._headerViewport.querySelectorAll(".filter-input")
      for (let i = 0; i < inputs.length; i = i + 1) {
        const text = next[inputs[i].getAttribute("data-filter-key")]
        inputs[i].value = text !== undefined ? text : ""
      }
      this._loadData()
    }
    return
  }

  /* Text matched against every column of a row (in addition to `filterState`). */
  get globalFilter() {
    return this._globalFilter
  }

  set globalFilter(value) {
    this._globalFilter = value !== null && value !== undefined ? String(value) : ""
    if (this._bodyInner !== undefined && this._bodyInner !== null) {
      this._loadData()
    }
    return
  }

  /* Number of rows after filtering (the reported total in remote mode). */
  get rowCount() {
    return this._total
  }

  get selectedRows() {
    return this._selectedRows
  }

  selectRow(key) {
    const rowKey = String(key)
    if (this._selectionMode() === "single") {
      this._selectedRows.clear()
      this._selectedRowData.clear()
    }
    this._selectedRows.add(rowKey)

    /* Remember the row object when it is loaded, for the event payload. */
    const rows = this._dataSource !== null ? [] : this._viewRows
    for (let i = 0; i < rows.length; i = i + 1) {
      if (this._keyForRow(rows[i], i) === rowKey) {
        this._selectedRowData.set(rowKey, rows[i])
        break
      }
    }
    this._refreshSelectionUI()
    return
  }

  /* Select every row of the current view (loaded rows in remote mode). */
  selectAll() {
    for (let i = 0; i < this._total; i = i + 1) {
      const row = this._rowAt(i)
      if (row !== undefined) {
        const rowKey = this._keyForRow(row, i)
        this._selectedRows.add(rowKey)
        this._selectedRowData.set(rowKey, row)
      }
    }
    this._refreshSelectionUI()
    return
  }

  clearSelection() {
    this._selectedRows.clear()
    this._selectedRowData.clear()
    this._selectionAnchor = -1
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
