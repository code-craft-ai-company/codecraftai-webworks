/*
 * mjtable.js
 *
 * <mj-table> -- static, read-only tabular data with native <table> semantics.
 * Supports striped/bordered/compact variants, responsive strategies (scroll,
 * priority column hiding, stacked-card), optional sticky header, caption, and
 * a configurable empty state slot.
 *
 * Data comes from the `columns` / `rows` properties, or from a light-DOM
 * <table> child, which is read once into columns and rows (so the page still
 * shows a plain table when scripting is unavailable).
 *
 * Column options: `{ key, label, labelHidden?, width?, rowHeader?, priority?,
 * render?, cellClass?, cellAttrs? }`. The first column is the row header (`<th
 * scope="row">`) unless it sets `rowHeader: false`; any column may opt in with
 * `rowHeader: true`. With `responsive="priority"` the columns with the highest
 * `priority` number are hidden first when the table does not fit.
 * `labelHidden: true` keeps the label for screen readers only (a selection or
 * action column with no visible heading still has a named header).
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";
import { t } from "../core/intl.js";

const STYLES = `
:host {
  display: block;
  font: inherit;
  color: var(--mj-text);
}

.scroll-wrapper {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}
.scroll-wrapper:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

/*
 * A sticky header needs a vertically scrolling ancestor: the wrapper is that
 * ancestor, bounded by --mj-table-max-height.
 */
:host([sticky-header]) .scroll-wrapper {
  max-block-size: var(--mj-table-max-height, 24rem);
  overflow-y: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--mj-font-size-sm);
}

caption {
  text-align: start;
  font-weight: var(--mj-font-weight-medium);
  padding-block-end: var(--mj-space-2);
  color: var(--mj-text);
}
caption[hidden], tfoot[hidden] { display: none; }

th, td {
  padding: var(--mj-table-cell-padding-y, 10px) var(--mj-table-cell-padding-x, 12px);
  text-align: start;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  border-block-end: 1px solid var(--mj-table-border-color, var(--mj-border));
}

thead th {
  background: var(--mj-table-header-bg, var(--mj-bg-subtle));
  font-weight: var(--mj-font-weight-medium);
  border-block-end: 2px solid var(--mj-table-border-color, var(--mj-border-strong));
}

tbody th { font-weight: var(--mj-table-row-header-weight, var(--mj-font-weight-medium)); }

:host([sticky-header]) thead th {
  position: sticky;
  inset-block-start: 0;
  z-index: var(--mj-layer-sticky);
  box-shadow: var(--mj-elevation-1);
}

:host([variant="striped"]) tbody tr:nth-child(odd) > th,
:host([variant="striped"]) tbody tr:nth-child(odd) > td {
  background: var(--mj-table-stripe-bg, var(--mj-bg-subtle));
}

:host([variant="bordered"]) th,
:host([variant="bordered"]) td {
  border: 1px solid var(--mj-table-border-color, var(--mj-border));
}

:host([variant="compact"]) th,
:host([variant="compact"]) td {
  padding-block: 4px;
}

:host([loading]) {
  opacity: 0.7;
  pointer-events: none;
}

.empty-row td {
  text-align: center;
  color: var(--mj-text-muted);
  font-style: italic;
}

.col-hidden { display: none; }

.summary,
.sr-label {
  position: absolute;
  width: 1px; height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}

/*
 * responsive="stack": below the breakpoint (toggled from a ResizeObserver,
 * see _syncResponsive) every row becomes a card of label / value lines.
 */
.scroll-wrapper[data-stacked] table,
.scroll-wrapper[data-stacked] tbody,
.scroll-wrapper[data-stacked] tfoot,
.scroll-wrapper[data-stacked] tr,
.scroll-wrapper[data-stacked] tbody th,
.scroll-wrapper[data-stacked] td {
  display: block;
}
.scroll-wrapper[data-stacked] colgroup { display: none; }
.scroll-wrapper[data-stacked] thead {
  position: absolute;
  width: 1px; height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
}
.scroll-wrapper[data-stacked] tbody th,
.scroll-wrapper[data-stacked] tbody td {
  white-space: normal;
  border-block-end: none;
}
.scroll-wrapper[data-stacked] tbody tr {
  border-block-end: 1px solid var(--mj-table-border-color, var(--mj-border));
  padding-block: var(--mj-space-2);
}
.scroll-wrapper[data-stacked] tbody th[data-label]::before,
.scroll-wrapper[data-stacked] tbody td[data-label]::before {
  content: attr(data-label);
  font-weight: var(--mj-font-weight-medium);
  display: inline-block;
  margin-inline-end: var(--mj-space-2);
}
`;

const DEFAULT_STACK_BREAKPOINT = 480;

/*
 * Apply row-level styling / data hooks to a freshly-created <tr>.
 *
 *   rowClass    -- a string, a string[], or a callback
 *                  `(row, idx) => string | string[]`. Adds the
 *                  resolved class names to the row's classList in
 *                  addition to the part="tr" identifier the
 *                  component owns.
 *   rowAttrs    -- a callback `(row, idx) => { [name]: value }`.
 *                  Each name/value pair is applied via
 *                  setAttribute, so consumers can stamp data-
 *                  attributes (typical: a row id for keyboard /
 *                  tests) without webworks knowing the schema.
 *
 * Both inputs are optional -- callers that supply neither get
 * the existing behavior.
 */
function _applyRowHooks(tr, row, rowIdx, rowClass, rowAttrs) {
    if (rowClass !== null && rowClass !== undefined) {
        let resolved = rowClass
        if (typeof rowClass === "function") {
            resolved = rowClass(row, rowIdx)
        }
        if (typeof resolved === "string" && resolved.length > 0) {
            for (const token of resolved.split(/\s+/)) {
                if (token.length > 0) {
                    tr.classList.add(token)
                }
            }
        } else if (Array.isArray(resolved) === true) {
            for (const token of resolved) {
                if (typeof token === "string" && token.length > 0) {
                    tr.classList.add(token)
                }
            }
        }
    }
    if (typeof rowAttrs === "function") {
        const attrs = rowAttrs(row, rowIdx) || {}
        for (const name of Object.keys(attrs)) {
            const value = attrs[name]
            if (value === null || value === undefined || value === false) {
                tr.removeAttribute(name)
            } else if (value === true) {
                tr.setAttribute(name, "")
            } else {
                tr.setAttribute(name, String(value))
            }
        }
    }
    return
}

/*
 * Apply column-level cell hooks. Mirrors row hooks but scoped to
 * one column; consumers add per-cell classes / data-attributes
 * via `col.cellClass` and `col.cellAttrs` on the column schema.
 */
function _applyCellHooks(cell, row, col, rowIdx) {
    if (col.cellClass !== null && col.cellClass !== undefined) {
        let resolved = col.cellClass
        if (typeof col.cellClass === "function") {
            resolved = col.cellClass(row, col, rowIdx)
        }
        if (typeof resolved === "string" && resolved.length > 0) {
            for (const token of resolved.split(/\s+/)) {
                if (token.length > 0) {
                    cell.classList.add(token)
                }
            }
        } else if (Array.isArray(resolved) === true) {
            for (const token of resolved) {
                if (typeof token === "string" && token.length > 0) {
                    cell.classList.add(token)
                }
            }
        }
    }
    if (typeof col.cellAttrs === "function") {
        const attrs = col.cellAttrs(row, col, rowIdx) || {}
        for (const name of Object.keys(attrs)) {
            const value = attrs[name]
            if (value === null || value === undefined || value === false) {
                cell.removeAttribute(name)
            } else if (value === true) {
                cell.setAttribute(name, "")
            } else {
                cell.setAttribute(name, String(value))
            }
        }
    }
    return
}

/*
 * Populate a single cell.
 *
 *   - When `col.render` is a function, call `render(row, col, rowIdx)`
 *     and use the return value:
 *       * a string -> textContent (with a matching title for hover)
 *       * a Node / Element -> appended as a child
 *       * an array or NodeList of nodes -> all appended
 *       * a DocumentFragment -> appended whole
 *       * null / undefined -> empty cell
 *   - Otherwise fall back to text rendering of the row's raw value
 *     (unchanged behavior for callers that don't supply `render`).
 */
function _fillCell(cell, value, row, col, rowIdx) {
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
        const text = String(rendered)
        cell.textContent = text
        if (text.length > 0) {
            cell.setAttribute("title", text)
        }
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

export class MjTable extends MjElement {
  static tagName = "mj-table";
  static styles = STYLES;
  static watched = ["caption", "summary", "variant", "responsive", "sticky-header", "loading", "col-widths", "aria-label"];

  constructor() {
    super()
    this._columns = []
    this._rows = []
    this._rowClass = null
    this._rowAttrs = null
    this._resizeObserver = null
    this._resizeFrame = 0
    this._overflowing = null
    this._hiddenColumns = new Set()
    this._summaryId = nextId("mj-table-summary")

    /* Set when columns / rows were read from a light-DOM <table>. */
    this._fromLightTable = false
  }

  render() {
    const markup = `
      <div class="scroll-wrapper" part="scroll-wrapper">
        <table part="table" aria-busy="false">
          <caption part="caption" hidden><slot name="caption"><span class="caption-text"></span></slot></caption>
          <colgroup part="colgroup"></colgroup>
          <thead part="thead"><tr></tr></thead>
          <tbody part="tbody"></tbody>
          <tfoot part="tfoot" hidden><tr><td class="footer-cell"><slot name="footer"></slot></td></tr></tfoot>
        </table>
      </div>
      <div class="summary" id="${this._summaryId}"></div>
    `
    return markup
  }

  afterRender() {
    this._wrapper = this.$(".scroll-wrapper")
    this._table = this.$("table")
    this._caption = this.$("caption")
    this._captionSlot = this.$("slot[name='caption']")
    this._captionText = this.$(".caption-text")
    this._colgroup = this.$("colgroup")
    this._thead = this.$("thead tr")
    this._tbody = this.$("tbody")
    this._tfoot = this.$("tfoot")
    this._footerCell = this.$(".footer-cell")
    this._footerSlot = this.$("slot[name='footer']")
    this._summaryEl = this.$(".summary")
    this._overflowing = null

    this.listen(this._wrapper, "keydown", this._onWrapperKeydown.bind(this))
    this.listen(this._captionSlot, "slotchange", () => { this._syncCaption() })
    this.listen(this._footerSlot, "slotchange", () => { this._syncFooter() })

    this._readLightTable()
    this._syncCaption()
    this._syncAriaLabel()
    this._syncSummary()
    this._syncFooter()
    this._table.setAttribute("aria-busy", this.hasAttribute("loading") === true ? "true" : "false")

    this._renderTable()
    this._setupResizeObserver()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._wrapper === undefined || this._wrapper === null) {
      return
    }
    if (name === "caption" || name === "aria-label") {
      this._syncCaption()
      this._syncAriaLabel()
    }
    if (name === "summary") {
      this._syncSummary()
    }
    if (name === "loading") {
      const isLoading = newValue !== null
      this._table.setAttribute("aria-busy", isLoading === true ? "true" : "false")
      if (isLoading === true && oldValue === null) {
        announce(t("mj.table.loadingAnnouncement"))
      }
    }
    if (name === "col-widths") {
      this._renderColgroup()
      this._syncResponsive()
    }
    if (name === "responsive") {
      this._syncResponsive()
    }
    return
  }

  /*
   * The caption shows the slotted `caption` content when there is any,
   * otherwise the `caption` attribute (the slot's fallback text).
   */
  _syncCaption() {
    const text = this.getAttribute("caption") || ""
    this._captionText.textContent = text
    const hasSlotted = this._captionSlot.assignedNodes().length > 0
    this._caption.hidden = hasSlotted === false && text.length === 0
    return
  }

  _accessibleName() {
    const name = this.getAttribute("caption") || this.getAttribute("aria-label") || t("mj.table.label")
    return name
  }

  _syncAriaLabel() {
    const hasVisibleCaption = (this.getAttribute("caption") || "").length > 0
    if (hasVisibleCaption === true) {
      /* The <caption> names the table. */
      this._table.removeAttribute("aria-label")
    } else {
      this._table.setAttribute("aria-label", this._accessibleName())
    }
    if (this._wrapper.hasAttribute("role") === true) {
      this._wrapper.setAttribute("aria-label", this._accessibleName())
    }
    return
  }

  /* `summary` is helper text: rendered visually hidden and referenced by id. */
  _syncSummary() {
    const summary = this.getAttribute("summary") || ""
    this._summaryEl.textContent = summary
    if (summary.length > 0) {
      this._table.setAttribute("aria-describedby", this._summaryId)
    } else {
      this._table.removeAttribute("aria-describedby")
    }
    return
  }

  _syncFooter() {
    const hasFooter = this._footerSlot.assignedNodes().length > 0
    this._tfoot.hidden = hasFooter === false
    this._footerCell.setAttribute("colspan", String(this._columns.length || 1))
    return
  }

  /*
   * Declarative path: derive columns and rows from a light-DOM <table> child
   * when no data was assigned through the properties.
   */
  _readLightTable() {
    if (this._columns.length > 0 || this._rows.length > 0) {
      return
    }
    const source = this.querySelector(":scope > table")
    if (source === null) {
      return
    }

    const columns = []
    const rows = []
    const sourceRows = Array.from(source.rows)
    const headerRow = source.tHead !== null && source.tHead.rows.length > 0 ? source.tHead.rows[0] : sourceRows[0]

    if (headerRow !== undefined) {
      for (let ci = 0; ci < headerRow.cells.length; ci = ci + 1) {
        columns.push({ key: `col${ci}`, label: headerRow.cells[ci].textContent.trim() })
      }
    }

    for (let ri = 0; ri < sourceRows.length; ri = ri + 1) {
      const sourceRow = sourceRows[ri]
      const inFooter = sourceRow.parentElement !== null && sourceRow.parentElement.localName === "tfoot"
      if (sourceRow === headerRow || inFooter === true) {
        continue
      }
      const row = {}
      for (let ci = 0; ci < columns.length; ci = ci + 1) {
        const cell = sourceRow.cells[ci]
        row[columns[ci].key] = cell !== undefined ? cell.textContent.trim() : ""
      }
      rows.push(row)
    }

    this._columns = columns
    this._rows = rows
    this._fromLightTable = true

    if (source.caption !== null && this.hasAttribute("caption") === false) {
      this.setAttribute("caption", source.caption.textContent.trim())
    }
    return
  }

  /*
   * Stacking or hiding columns changes the size of the observed wrapper.
   * Doing that inside the observer callback would make the browser report
   * "ResizeObserver loop completed with undelivered notifications", so the
   * responsive pass runs on the next animation frame (once per frame); the
   * size change it causes is then observed normally, and the pass is
   * idempotent for an unchanged width.
   */
  _setupResizeObserver() {
    if (typeof ResizeObserver === "undefined") {
      return
    }
    this._resizeObserver = new ResizeObserver(() => {
      if (this._resizeFrame !== 0) {
        return
      }
      this._resizeFrame = window.requestAnimationFrame(() => {
        this._resizeFrame = 0
        this._syncResponsive()
      })
    })
    this._resizeObserver.observe(this._wrapper)
    /*
     * The table also changes size without a render (web fonts, custom
     * elements in cells upgrading), and a sticky-header wrapper at its max
     * height then keeps its size. The passes above hide and show columns
     * within one task, so an unchanged net size is not reported.
     */
    this._resizeObserver.observe(this._table)
    this.onTeardown(() => {
      this._resizeObserver.disconnect()
      if (this._resizeFrame !== 0) {
        window.cancelAnimationFrame(this._resizeFrame)
        this._resizeFrame = 0
      }
    })
    return
  }

  /* The width at or below which responsive="stack" switches to cards. */
  _stackBreakpoint() {
    const raw = window.getComputedStyle(this).getPropertyValue("--mj-table-stack-breakpoint")
    const parsed = parseFloat(raw)
    const breakpoint = Number.isNaN(parsed) === true ? DEFAULT_STACK_BREAKPOINT : parsed
    return breakpoint
  }

  /* Apply the responsive strategy for the current width. */
  _syncResponsive() {
    const responsive = this.getAttribute("responsive") || "scroll"

    const shouldStack = responsive === "stack" && this._wrapper.clientWidth <= this._stackBreakpoint()
    if (shouldStack === true) {
      this._wrapper.setAttribute("data-stacked", "")
    } else {
      this._wrapper.removeAttribute("data-stacked")
    }

    if (responsive === "priority") {
      this._applyPriorityHiding()
    } else if (this._hiddenColumns.size > 0) {
      this._hiddenColumns = new Set()
      this._applyHiddenColumns()
    }

    this._checkOverflow()
    return
  }

  /*
   * responsive="priority": while the table is wider than its wrapper, hide
   * the visible column with the highest `priority` number. Columns without a
   * priority are never hidden.
   */
  _applyPriorityHiding() {
    this._hiddenColumns = new Set()
    this._applyHiddenColumns()

    let guard = this._columns.length
    while (guard > 0 && this._table.scrollWidth > this._wrapper.clientWidth) {
      guard = guard - 1
      let candidate = -1
      for (let idx = 0; idx < this._columns.length; idx = idx + 1) {
        const priority = this._columns[idx].priority
        if (typeof priority !== "number" || this._hiddenColumns.has(idx) === true) {
          continue
        }
        if (candidate < 0 || priority >= this._columns[candidate].priority) {
          candidate = idx
        }
      }
      if (candidate < 0) {
        break
      }
      this._hiddenColumns.add(candidate)
      this._applyHiddenColumns()
    }
    return
  }

  _applyHiddenColumns() {
    const cols = this._colgroup.children
    const tableRows = this._table.querySelectorAll("thead tr, tbody tr:not(.empty-row)")
    for (let idx = 0; idx < this._columns.length; idx = idx + 1) {
      const hidden = this._hiddenColumns.has(idx)
      if (cols[idx] !== undefined) {
        cols[idx].classList.toggle("col-hidden", hidden)
      }
      for (let ri = 0; ri < tableRows.length; ri = ri + 1) {
        const cell = tableRows[ri].children[idx]
        if (cell !== undefined) {
          cell.classList.toggle("col-hidden", hidden)
        }
      }
    }
    return
  }

  /*
   * The wrapper is a focusable, labelled region only while the table
   * overflows it (so keyboard users can scroll it): wider than the wrapper,
   * or taller than a bounded wrapper (sticky-header, --mj-table-max-height).
   * `mj-table-overflow` fires when that state changes.
   */
  _checkOverflow() {
    const isWider = this._table.scrollWidth > this._wrapper.clientWidth
    /* 1px of slack: the two heights round differently at fractional zoom. */
    const isTaller = this._wrapper.scrollHeight > this._wrapper.clientHeight + 1
    const isOverflowing = isWider === true || isTaller === true
    if (isOverflowing === true) {
      this._wrapper.setAttribute("role", "region")
      this._wrapper.setAttribute("aria-label", this._accessibleName())
      this._wrapper.tabIndex = 0
    } else {
      this._wrapper.removeAttribute("role")
      this._wrapper.removeAttribute("aria-label")
      this._wrapper.removeAttribute("tabindex")
    }
    if (isOverflowing !== this._overflowing) {
      this._overflowing = isOverflowing
      this.emit("mj-table-overflow", { overflowing: isOverflowing })
    }
    return
  }

  _onWrapperKeydown(event) {
    if (event.target !== this._wrapper) {
      return
    }
    if (event.key === "ArrowLeft") {
      this._wrapper.scrollLeft = this._wrapper.scrollLeft - 80
    } else if (event.key === "ArrowRight") {
      this._wrapper.scrollLeft = this._wrapper.scrollLeft + 80
    }
    return
  }

  _renderTable() {
    this._renderColgroup()
    this._renderThead()
    this._renderTbody()
    this._syncFooter()
    this._syncResponsive()
    return
  }

  _renderColgroup() {
    const widths = this._parseColWidths()
    this._colgroup.replaceChildren()
    for (let idx = 0; idx < this._columns.length; idx = idx + 1) {
      const col = document.createElement("col")
      if (widths[idx] !== undefined && widths[idx] !== "") {
        col.style.width = widths[idx]
      }
      this._colgroup.appendChild(col)
    }
    return
  }

  _parseColWidths() {
    const raw = this.getAttribute("col-widths") || ""
    if (raw.length === 0) {
      return []
    }
    const parts = raw.split(",")
    const widths = parts.map((part) => {
      return part.trim()
    })
    return widths
  }

  _columnLabel(col) {
    const label = col.label !== undefined && col.label !== null ? String(col.label) : String(col.key)
    return label
  }

  /* The first column is the row header unless it opts out; others opt in. */
  _isRowHeader(col, colIdx) {
    let isHeader = colIdx === 0
    if (col.rowHeader === true) {
      isHeader = true
    } else if (col.rowHeader === false) {
      isHeader = false
    }
    return isHeader
  }

  _renderThead() {
    this._thead.replaceChildren()
    for (let idx = 0; idx < this._columns.length; idx = idx + 1) {
      const col = this._columns[idx]
      const th = document.createElement("th")
      th.setAttribute("scope", "col")
      th.setAttribute("part", "th")
      if (col.labelHidden === true) {
        const label = document.createElement("span")
        label.className = "sr-label"
        label.textContent = this._columnLabel(col)
        th.appendChild(label)
      } else {
        th.textContent = this._columnLabel(col)
      }
      if (col.width !== undefined && col.width !== null) {
        th.style.width = typeof col.width === "number" ? `${col.width}px` : String(col.width)
      }
      this._thead.appendChild(th)
    }
    return
  }

  _renderTbody() {
    this._tbody.replaceChildren()
    if (this._rows.length === 0) {
      const emptyRow = document.createElement("tr")
      emptyRow.className = "empty-row"
      const td = document.createElement("td")
      td.setAttribute("colspan", String(this._columns.length || 1))
      const emptySlot = document.createElement("slot")
      emptySlot.setAttribute("name", "empty")
      emptySlot.textContent = t("mj.table.empty")
      td.appendChild(emptySlot)
      emptyRow.appendChild(td)
      this._tbody.appendChild(emptyRow)
      return
    }

    for (let rowIdx = 0; rowIdx < this._rows.length; rowIdx = rowIdx + 1) {
      const row = this._rows[rowIdx]
      const tr = document.createElement("tr")
      tr.setAttribute("part", "tr")
      _applyRowHooks(tr, row, rowIdx, this._rowClass, this._rowAttrs)

      for (let colIdx = 0; colIdx < this._columns.length; colIdx = colIdx + 1) {
        const col = this._columns[colIdx]
        const isHeader = this._isRowHeader(col, colIdx)
        const cell = isHeader === true ? document.createElement("th") : document.createElement("td")
        if (isHeader === true) {
          cell.setAttribute("scope", "row")
          cell.setAttribute("part", "th")
        } else {
          cell.setAttribute("part", "td")
        }

        const value = row[col.key]
        _fillCell(cell, value, row, col, rowIdx)
        _applyCellHooks(cell, row, col, rowIdx)

        /* Shown as the line label when responsive="stack" is active (not for a hidden label). */
        cell.setAttribute("data-label", col.labelHidden === true ? "" : this._columnLabel(col))

        tr.appendChild(cell)
      }

      this._tbody.appendChild(tr)
    }
    return
  }

  /* ----- scriptable API ----- */

  get columns() {
    return this._columns
  }

  set columns(value) {
    this._columns = Array.isArray(value) === true ? value : []
    if (this._fromLightTable === true) {
      /* Explicit columns replace what was read from the light-DOM table. */
      this._fromLightTable = false
      this._rows = []
    }
    if (this._tbody !== undefined && this._tbody !== null) {
      this._renderTable()
    }
    return
  }

  get rows() {
    return this._rows
  }

  set rows(value) {
    this._rows = Array.isArray(value) === true ? value : []
    if (this._tbody !== undefined && this._tbody !== null) {
      this._renderTable()
    }
    return
  }

  /*
   * Per-row hooks. Set `rowClass` to a string, a string[], or a
   * `(row, idx) => string | string[]` callback to add class names
   * to every <tr>. Set `rowAttrs` to a `(row, idx) => attrs`
   * callback to stamp arbitrary attributes (typically a row id
   * so consumers can target individual rows from tests or
   * styles).
   */
  get rowClass() {
    return this._rowClass
  }

  set rowClass(value) {
    this._rowClass = value
    if (this._tbody !== undefined && this._tbody !== null) {
      this._renderTable()
    }
    return
  }

  get rowAttrs() {
    return this._rowAttrs
  }

  set rowAttrs(value) {
    this._rowAttrs = typeof value === "function" ? value : null
    if (this._tbody !== undefined && this._tbody !== null) {
      this._renderTable()
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
