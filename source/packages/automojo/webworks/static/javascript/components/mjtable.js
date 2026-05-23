/*
 * mjtable.js
 *
 * <mj-table> -- static, read-only tabular data with native <table> semantics.
 * Supports striped/bordered/compact variants, responsive strategies (scroll,
 * priority column hiding, stacked-card), optional sticky header, caption, and
 * a configurable empty state slot.
 */

import { MjElement } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";

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
caption:empty { display: none; }

th, td {
  padding: var(--mj-table-cell-padding-y, 10px) var(--mj-table-cell-padding-x, 12px);
  text-align: start;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  border-bottom: 1px solid var(--mj-table-border-color, var(--mj-border));
}

thead th {
  background: var(--mj-table-header-bg, var(--mj-bg-subtle));
  font-weight: var(--mj-font-weight-medium);
  border-bottom: 2px solid var(--mj-table-border-color, var(--mj-border-strong));
}

:host([sticky-header]) thead th {
  position: sticky;
  top: 0;
  z-index: var(--mj-layer-sticky);
  box-shadow: var(--mj-elevation-1);
}

:host([variant="striped"]) tbody tr:nth-child(odd) td {
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

@container (max-width: var(--mj-table-stack-breakpoint, 480px)) {
  :host([responsive="stack"]) table,
  :host([responsive="stack"]) thead,
  :host([responsive="stack"]) tbody,
  :host([responsive="stack"]) th,
  :host([responsive="stack"]) td,
  :host([responsive="stack"]) tr {
    display: block;
  }
  :host([responsive="stack"]) thead tr {
    position: absolute;
    top: -9999px;
    left: -9999px;
  }
  :host([responsive="stack"]) td::before {
    content: attr(data-label);
    font-weight: var(--mj-font-weight-medium);
    display: inline-block;
    margin-inline-end: var(--mj-space-2);
  }
}
`;

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
  static watched = ["caption", "variant", "responsive", "sticky-header", "loading", "col-widths"];

  constructor() {
    super()
    this._columns = []
    this._rows = []
    this._resizeObserver = null
  }

  render() {
    const markup = `
      <div class="scroll-wrapper" part="scroll-wrapper" role="region" tabindex="0">
        <table part="table" aria-busy="false">
          <caption part="caption"><slot name="caption"></slot></caption>
          <colgroup part="colgroup"></colgroup>
          <thead part="thead"><tr></tr></thead>
          <tbody part="tbody"></tbody>
          <tfoot part="tfoot"><slot name="footer"></slot></tfoot>
        </table>
      </div>
    `
    return markup
  }

  afterRender() {
    this._wrapper = this.$(".scroll-wrapper")
    this._table = this.$("table")
    this._caption = this.$("caption")
    this._colgroup = this.$("colgroup")
    this._thead = this.$("thead tr")
    this._tbody = this.$("tbody")

    this._syncCaption()
    this._syncAriaLabel()

    this.listen(this._wrapper, "keydown", this._onWrapperKeydown.bind(this))

    const captionAttr = this.getAttribute("caption")
    if (captionAttr !== null && captionAttr.length > 0) {
      this._caption.textContent = captionAttr
    }

    if (this._columns.length > 0 || this._rows.length > 0) {
      this._renderTable()
    }

    this._setupResizeObserver()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._wrapper === undefined || this._wrapper === null) {
      return
    }
    if (name === "caption") {
      this._syncCaption()
      this._syncAriaLabel()
    }
    if (name === "loading") {
      const isLoading = newValue !== null
      this._table.setAttribute("aria-busy", isLoading === true ? "true" : "false")
      if (isLoading === true) {
        announce("Loading table data.")
      }
    }
    return
  }

  _syncCaption() {
    const text = this.getAttribute("caption") || ""
    const slotted = this.$("slot[name='caption']")
    if (slotted !== null && slotted.assignedNodes().length === 0) {
      this._caption.textContent = text
    }
    return
  }

  _syncAriaLabel() {
    const captionText = this.getAttribute("caption") || this.getAttribute("aria-label") || "Table"
    this._wrapper.setAttribute("aria-label", captionText)

    const summaryId = this.getAttribute("summary")
    if (summaryId !== null && summaryId.length > 0) {
      this._wrapper.setAttribute("aria-describedby", summaryId)
    }
    return
  }

  _setupResizeObserver() {
    if (typeof ResizeObserver === "undefined") {
      return
    }
    this._resizeObserver = new ResizeObserver(() => {
      this._checkOverflow()
    })
    this._resizeObserver.observe(this._wrapper)
    this.onTeardown(() => {
      this._resizeObserver.disconnect()
    })
    return
  }

  _checkOverflow() {
    const isOverflowing = this._table.scrollWidth > this._wrapper.clientWidth
    this.emit("mj-table-overflow", { overflowing: isOverflowing })
    return
  }

  _onWrapperKeydown(event) {
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
    return
  }

  _renderColgroup() {
    const widths = this._parseColWidths()
    this._colgroup.innerHTML = ""
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

  _renderThead() {
    this._thead.innerHTML = ""
    for (let idx = 0; idx < this._columns.length; idx = idx + 1) {
      const col = this._columns[idx]
      const th = document.createElement("th")
      th.setAttribute("scope", "col")
      th.setAttribute("part", "th")
      th.textContent = col.label || col.key
      if (col.width !== undefined) {
        th.style.width = col.width
      }
      this._thead.appendChild(th)
    }
    return
  }

  _renderTbody() {
    this._tbody.innerHTML = ""
    if (this._rows.length === 0) {
      const emptyRow = document.createElement("tr")
      emptyRow.className = "empty-row"
      const td = document.createElement("td")
      td.setAttribute("colspan", String(this._columns.length || 1))
      const emptySlot = document.createElement("slot")
      emptySlot.setAttribute("name", "empty")
      emptySlot.textContent = "No data"
      td.appendChild(emptySlot)
      emptyRow.appendChild(td)
      this._tbody.appendChild(emptyRow)
      return
    }

    const responsive = this.getAttribute("responsive") || "scroll"

    for (let rowIdx = 0; rowIdx < this._rows.length; rowIdx = rowIdx + 1) {
      const row = this._rows[rowIdx]
      const tr = document.createElement("tr")
      tr.setAttribute("part", "tr")

      for (let colIdx = 0; colIdx < this._columns.length; colIdx = colIdx + 1) {
        const col = this._columns[colIdx]
        const isFirst = colIdx === 0
        const cell = isFirst === true ? document.createElement("th") : document.createElement("td")
        if (isFirst === true) {
          cell.setAttribute("scope", "row")
          cell.setAttribute("part", "th")
        } else {
          cell.setAttribute("part", "td")
        }

        const value = row[col.key]
        _fillCell(cell, value, row, col, rowIdx)

        if (responsive === "stack") {
          cell.setAttribute("data-label", col.label || col.key)
        }

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

  get loading() {
    return this.hasAttribute("loading")
  }

  set loading(value) {
    this.reflectBoolean("loading", value === true)
    return
  }
}
