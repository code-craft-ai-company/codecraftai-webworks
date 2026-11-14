/*
 * mjbuildstatusboard.js
 *
 * <mj-build-status-board> -- big-board table of pipeline / branch build and
 * deploy statuses. Sortable, filterable, groupable, paginated and
 * live-updatable.
 *
 * Implemented as a native <table> (no external DataTable dependency): the
 * sortable column headers hold real buttons, every row has a selection
 * checkbox, and the pipeline name is a link (rows with a `url`) or a button
 * that emits `mj-row-activate`, so each row can be activated from the
 * keyboard. Listeners are delegated to the stable table parts and
 * registered once.
 *
 * Data: `data` property, `src` attribute or inline JSON child --
 *   { rows: [{ id, name, status, deployTarget, lastRun, duration, actor, url }] }
 * `duration` is in seconds; `lastRun` is an ISO date-time.
 */

import { nextId } from "../core/mjelement.js";
import { html, safeUrl } from "../core/html.js";
import { announce } from "../core/announcer.js";
import { t } from "../core/intl.js";
import {
  PM_CHART_STYLES, PmChartElement, chartTime, emptyStateMarkup, formatChartDate,
  setEmptyState, toNumber, toText
} from "./pmchartsupport.js";

const DEFAULT_PAGE_SIZE = 25;
const DEFAULT_POLL_MS = 30000;
const MIN_POLL_MS = 5000;

/* `labelKey` is the string key of the visible label, resolved with t() at use time. */
const STATUS_META = {
  pending:   { icon: "○", labelKey: "mj.buildStatusBoard.status.pending",   color: "var(--mj-text-muted)"    },
  running:   { icon: "◎", labelKey: "mj.buildStatusBoard.status.running",   color: "var(--mj-color-info)"    },
  passed:    { icon: "✓", labelKey: "mj.buildStatusBoard.status.passed",    color: "var(--mj-color-success)" },
  failed:    { icon: "✗", labelKey: "mj.buildStatusBoard.status.failed",    color: "var(--mj-color-danger)"  },
  cancelled: { icon: "⊘", labelKey: "mj.buildStatusBoard.status.cancelled", color: "var(--mj-text-muted)"    },
  skipped:   { icon: "→", labelKey: "mj.buildStatusBoard.status.skipped",   color: "var(--mj-text-muted)"    },
  unknown:   { icon: "?", labelKey: "mj.buildStatusBoard.status.unknown",   color: "var(--mj-text-muted)"    }
};

const COLUMNS = [
  { key: "name", labelKey: "mj.buildStatusBoard.column.pipeline", sortable: true },
  { key: "status", labelKey: "mj.buildStatusBoard.column.status", sortable: true },
  { key: "deployTarget", labelKey: "mj.buildStatusBoard.column.deployTarget", sortable: true },
  { key: "lastRun", labelKey: "mj.buildStatusBoard.column.lastRun", sortable: true },
  { key: "duration", labelKey: "mj.buildStatusBoard.column.duration", sortable: true },
  { key: "actor", labelKey: "mj.buildStatusBoard.column.actor", sortable: false }
];

const SORTABLE_KEYS = COLUMNS.filter((column) => column.sortable === true).map((column) => column.key);

const STYLES = `
${PM_CHART_STYLES}
.board-title { font-weight: var(--mj-font-weight-medium); font-size: var(--mj-font-size-sm); }
.live-badge { display: inline-flex; align-items: center; gap: 4px; font-size: var(--mj-font-size-xs); color: var(--mj-color-info); }
.live-dot { inline-size: 7px; block-size: 7px; border-radius: 50%; background: var(--mj-color-info); animation: mj-pulse 1.4s ease-in-out infinite; }
@keyframes mj-pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }
@media (prefers-reduced-motion: reduce) { .live-dot { animation: none; } }
.filter-bar { display: flex; align-items: center; gap: var(--mj-space-2); padding: var(--mj-space-2) var(--mj-space-3); border-block-end: 1px solid var(--mj-border); flex-wrap: wrap; }
.filter-bar input, .filter-bar select { font: inherit; font-size: var(--mj-font-size-xs); background: var(--mj-surface); border: 1px solid var(--mj-border-strong); border-radius: var(--mj-radius-sm); padding: 2px 8px; min-block-size: 24px; color: var(--mj-text); max-inline-size: 100%; }
.filter-bar input:focus-visible, .filter-bar select:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: var(--mj-focus-ring-offset); }
.results-count { font-size: var(--mj-font-size-xs); color: var(--mj-text-muted); padding: 2px var(--mj-space-2); }
.table-wrap { overflow-x: auto; }
table { border-collapse: collapse; inline-size: 100%; font-size: var(--mj-font-size-sm); }
caption { font-size: var(--mj-font-size-xs); color: var(--mj-text-muted); text-align: start; padding: var(--mj-space-2) var(--mj-space-3); }
th { padding: var(--mj-space-2) var(--mj-space-3); text-align: start; background: var(--mj-bg-subtle); border-block-end: 2px solid var(--mj-border); font-weight: var(--mj-font-weight-medium); white-space: nowrap; }
th[data-col] { padding: 0; }
.sort-btn { font: inherit; font-weight: inherit; color: inherit; background: none; border: none; inline-size: 100%; text-align: start; padding: var(--mj-space-2) var(--mj-space-3); min-block-size: 24px; cursor: pointer; white-space: nowrap; }
.sort-btn:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: calc(0px - var(--mj-focus-ring-width)); }
.sort-indicator { font-size: 10px; margin-inline-start: 4px; color: var(--mj-text-muted); }
td { padding: var(--mj-space-2) var(--mj-space-3); border-block-end: 1px solid var(--mj-border); vertical-align: middle; }
:host([density="compact"]) td, :host([density="compact"]) .sort-btn { padding-block: 2px; }
tr[data-status="failed"] { background: var(--mj-color-danger-surface); }
tr[data-status="running"] { background: var(--mj-color-info-surface); }
tr[data-selected="true"] { background: var(--mj-bg-muted); box-shadow: inset 3px 0 0 var(--mj-accent); }
.group-row th { background: var(--mj-bg-muted); font-size: var(--mj-font-size-xs); }
.status-badge { display: inline-flex; align-items: center; gap: 4px; font-size: var(--mj-font-size-xs); font-weight: var(--mj-font-weight-medium); }
.status-icon { font-size: 13px; }
.pipeline-link { color: var(--mj-accent); text-decoration: none; font: inherit; background: none; border: none; padding: 0; cursor: pointer; text-align: start; }
.pipeline-link:hover { text-decoration: underline; }
.pipeline-link:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: 2px; }
.check-cell { inline-size: 36px; text-align: center; }
.bulk-bar { display: flex; align-items: center; gap: var(--mj-space-2); padding: var(--mj-space-2) var(--mj-space-3); background: var(--mj-bg-muted); border-block-start: 1px solid var(--mj-border); font-size: var(--mj-font-size-xs); }
.pagination { display: flex; align-items: center; gap: var(--mj-space-2); padding: var(--mj-space-2) var(--mj-space-3); border-block-start: 1px solid var(--mj-border); font-size: var(--mj-font-size-xs); }
.chart-button:disabled { opacity: 0.4; cursor: default; }
`;

export class MjBuildStatusBoard extends PmChartElement {
  static tagName = "mj-build-status-board";
  static styles = STYLES;
  static watched = ["group-by", "density", "live", "poll-interval", "filter-status", "filter-pattern", "page-size", "sort-column", "sort-direction"];

  constructor() {
    super()
    this._selectedRows = new Set()
    this._sortColumn = "lastRun"
    this._sortDirection = "desc"
    this._filterStatus = ""
    this._filterPattern = ""
    this._pageSize = DEFAULT_PAGE_SIZE
    this._page = 0
    this._pollTimer = null
    this._captionId = nextId("mj-bsb-cap")
    this._statusSelectId = nextId("mj-bsb-status")
    this._patternInputId = nextId("mj-bsb-pattern")
  }

  render() {
    const statusOptions = Object.keys(STATUS_META).map((status) => html`<option value="${status}">${t(STATUS_META[status].labelKey)}</option>`)
    const headerCells = COLUMNS.map((column) => {
      let cell = html`<th scope="col" part="header-cell">${t(column.labelKey)}</th>`
      if (column.sortable === true) {
        cell = html`<th scope="col" data-col="${column.key}" aria-sort="none" part="header-cell"><button class="sort-btn" type="button">${t(column.labelKey)}<span class="sort-indicator" aria-hidden="true"></span></button></th>`
      }
      return cell
    })

    const markup = html`
      <div class="wrapper" part="wrapper">
        <div class="toolbar board-header">
          <span class="board-title">${t("mj.buildStatusBoard.title")}</span>
          <span class="live-badge" part="live-indicator" hidden><span class="live-dot" aria-hidden="true"></span> ${t("mj.buildStatusBoard.live")}</span>
        </div>
        <div class="filter-bar" part="filter-bar">
          <label for="${this._statusSelectId}" class="mj-visually-hidden">${t("mj.buildStatusBoard.filterByStatus")}</label>
          <select id="${this._statusSelectId}" class="filter-status">
            <option value="">${t("mj.buildStatusBoard.allStatuses")}</option>
            ${statusOptions}
          </select>
          <label for="${this._patternInputId}" class="mj-visually-hidden">${t("mj.buildStatusBoard.filterByName")}</label>
          <input id="${this._patternInputId}" class="filter-pattern" type="search" placeholder="${t("mj.buildStatusBoard.filterPlaceholder")}"/>
          <button class="chart-button clear-filters-btn" type="button">${t("mj.buildStatusBoard.clearFilters")}</button>
          <span class="results-count" role="status"></span>
        </div>
        <div class="table-wrap">
          <table part="table" aria-describedby="${this._captionId}">
            <caption id="${this._captionId}" part="caption">${t("mj.buildStatusBoard.caption")}</caption>
            <thead>
              <tr class="header-row" part="header-row">
                <th class="check-cell" scope="col"><input type="checkbox" class="select-all" aria-label="${t("mj.buildStatusBoard.selectAllFiltered")}"/></th>
                ${headerCells}
              </tr>
            </thead>
            <tbody class="table-body" part="table-body"></tbody>
          </table>
          ${emptyStateMarkup()}
        </div>
        <div class="bulk-bar" part="bulk-action-bar" role="toolbar" aria-label="${t("mj.buildStatusBoard.pipelinesSelected", { count: 0 })}" hidden>
          <span class="selected-count">${t("mj.buildStatusBoard.selectedCount", { count: 0 })}</span>
          <slot name="bulk-actions"></slot>
        </div>
        <div class="pagination" part="pagination">
          <button class="chart-button prev-page-btn" type="button" disabled>&#x2039; ${t("mj.buildStatusBoard.previousPage")}</button>
          <span class="page-info"></span>
          <button class="chart-button next-page-btn" type="button">${t("core.next")} &#x203A;</button>
        </div>
      </div>`
    return markup
  }

  afterRender() {
    this._tableBody = this.$(".table-body")
    this._captionEl = this.$(`#${this._captionId}`)
    this._statusSel = this.$(".filter-status")
    this._patternInput = this.$(".filter-pattern")
    this._resultsCount = this.$(".results-count")
    this._bulkBar = this.$(".bulk-bar")
    this._pageInfo = this.$(".page-info")
    this._prevPageBtn = this.$(".prev-page-btn")
    this._nextPageBtn = this.$(".next-page-btn")
    this._selectAllChk = this.$(".select-all")
    this._liveBadge = this.$(".live-badge")

    this.listen(this._statusSel, "change", () => {
      this._setFilters(this._statusSel.value, this._filterPattern, true)
    })
    this.listen(this._patternInput, "input", () => {
      this._setFilters(this._filterStatus, this._patternInput.value, true)
    })
    this.listen(this.$(".clear-filters-btn"), "click", () => {
      this._setFilters("", "", true)
    })
    this.listen(this._prevPageBtn, "click", () => {
      if (this._page > 0) {
        this._page = this._page - 1
        this._renderRows()
      }
    })
    this.listen(this._nextPageBtn, "click", () => {
      this._page = this._page + 1
      this._renderRows()
    })
    this.listen(this._selectAllChk, "change", () => {
      this._onSelectAll(this._selectAllChk.checked)
    })

    /* Sorting: one listener on the header row (a click on the th or its button). */
    this.listen(this.$(".header-row"), "click", (event) => {
      const header = event.target.closest("th[data-col]")
      if (header !== null) {
        this._onSort(header.getAttribute("data-col"))
      }
    })

    /* Row checkboxes and name activation: one listener each on the body. */
    this.listen(this._tableBody, "change", (event) => {
      const checkbox = event.target.closest("input[type=checkbox]")
      const row = event.target.closest("tr[data-row-id]")
      if (checkbox !== null && row !== null) {
        this._onRowToggle(row, checkbox.checked)
      }
    })
    this.listen(this._tableBody, "click", (event) => {
      const activator = event.target.closest(".pipeline-link")
      const row = event.target.closest("tr[data-row-id]")
      if (activator !== null && row !== null) {
        const rowData = this._findRow(row.getAttribute("data-row-id"))
        this.emit("mj-row-activate", { row: rowData !== null ? rowData : { id: row.getAttribute("data-row-id") } })
      }
    })

    this._readAttributes()
    this._syncFilterControls()
    this.setupChart({})
    this._syncLive()
    return
  }

  onDisconnected() {
    this._stopPolling()
    return
  }

  get selectedRows() {
    return this._selectedRows
  }

  /* The filtered rows in display order (grouped first when group-by is set). */
  get filteredRows() {
    const rows = this._rows()
    let working = rows

    if (this._filterStatus !== "") {
      working = working.filter((row) => this._statusKey(row) === this._filterStatus)
    }
    if (this._filterPattern.length > 0) {
      const pattern = this._filterPattern.toLowerCase()
      working = working.filter((row) => toText(row.name).toLowerCase().includes(pattern))
    }

    const groupBy = this._groupBy()
    working = working.slice().sort((a, b) => {
      let order = 0
      if (groupBy !== null) {
        order = this._compareValues(this._sortValue(a, groupBy), this._sortValue(b, groupBy), 1)
      }
      if (order === 0) {
        order = this._compareValues(this._sortValue(a, this._sortColumn), this._sortValue(b, this._sortColumn), this._sortDirection === "desc" ? -1 : 1)
      }
      return order
    })
    return working
  }

  onDataChanged() {
    /* Keep only selections that still name a row. */
    const ids = new Set(this._rows().map((row) => this._rowId(row)))
    this._selectedRows.forEach((rowId) => {
      if (ids.has(rowId) === false) {
        this._selectedRows.delete(rowId)
      }
    })
    return
  }

  onDataDrawn() {
    this.emit("mj-data-load", { rows: this._rows().length })
    return
  }

  /*
   * Only the changed attribute is read again: the sort a user picked with a
   * header and the filters typed in the filter bar stay while an unrelated
   * attribute (density, group-by, page-size) changes.
   */
  onChartAttributeChanged(name, oldValue, newValue) {
    if (name === "live" || name === "poll-interval") {
      this._syncLive()
      return
    }
    if (name === "sort-column") {
      this._readSortColumn()
    } else if (name === "sort-direction") {
      this._readSortDirection()
    } else if (name === "filter-status") {
      this._readFilterStatus()
      this._page = 0
      this._syncFilterControls()
    } else if (name === "filter-pattern") {
      this._readFilterPattern()
      this._page = 0
      this._syncFilterControls()
    } else if (name === "page-size") {
      this._readPageSize()
    }
    this._renderRows()
    return
  }

  drawChart() {
    this._renderRows()
    return
  }

  /* ----- state ----- */

  _readAttributes() {
    this._readSortColumn()
    this._readSortDirection()
    this._readFilterStatus()
    this._readFilterPattern()
    this._readPageSize()
    return
  }

  _readSortColumn() {
    const sortColumn = this.getAttribute("sort-column")
    this._sortColumn = SORTABLE_KEYS.indexOf(sortColumn) >= 0 ? sortColumn : "lastRun"
    return
  }

  _readSortDirection() {
    this._sortDirection = this.getAttribute("sort-direction") === "asc" ? "asc" : "desc"
    return
  }

  _readFilterStatus() {
    const status = this.getAttribute("filter-status")
    this._filterStatus = status !== null && STATUS_META[status] !== undefined ? status : ""
    return
  }

  _readFilterPattern() {
    this._filterPattern = this.getAttribute("filter-pattern") || ""
    return
  }

  _readPageSize() {
    const pageSize = parseInt(this.getAttribute("page-size"), 10)
    this._pageSize = Number.isFinite(pageSize) === true && pageSize >= 0 ? pageSize : DEFAULT_PAGE_SIZE
    return
  }

  _syncFilterControls() {
    if (this._statusSel.value !== this._filterStatus) {
      this._statusSel.value = this._filterStatus
    }
    if (this._patternInput.value !== this._filterPattern) {
      this._patternInput.value = this._filterPattern
    }
    return
  }

  /* A filter change made by the user: re-render and report it. */
  _setFilters(status, pattern, notify) {
    this._filterStatus = STATUS_META[status] !== undefined ? status : ""
    this._filterPattern = toText(pattern)
    this._page = 0
    this._syncFilterControls()
    this._renderRows()
    if (notify === true) {
      this.emit("mj-filter-change", { status: this._filterStatus, pattern: this._filterPattern })
    }
    return
  }

  _groupBy() {
    const attr = this.getAttribute("group-by")
    const groupBy = attr !== null && COLUMNS.some((column) => column.key === attr) === true && attr !== "lastRun" && attr !== "duration" ? attr : null
    return groupBy
  }

  _rows() {
    const rows = this._data !== null && Array.isArray(this._data.rows) === true ? this._data.rows.filter((row) => row !== null && typeof row === "object") : []
    return rows
  }

  _rowId(row) {
    const rowId = toText(row.id !== undefined && row.id !== null ? row.id : row.name)
    return rowId
  }

  _findRow(rowId) {
    const found = this._rows().find((row) => this._rowId(row) === rowId)
    return found !== undefined ? found : null
  }

  /* Statuses outside the known set are shown, styled and filtered as "unknown". */
  _statusKey(row) {
    const key = STATUS_META[row.status] !== undefined ? row.status : "unknown"
    return key
  }

  _sortValue(row, column) {
    let value = null
    if (column === "lastRun") {
      value = chartTime(row.lastRun)
    } else if (column === "duration") {
      value = toNumber(row.duration, Number.NaN)
    } else if (column === "status") {
      value = this._statusKey(row)
    } else {
      value = toText(row[column]).toLowerCase()
    }
    return value
  }

  /*
   * Compare two sort values; `direction` is 1 (ascending) or -1. Missing
   * values (NaN or "") sort after present ones in either direction.
   */
  _compareValues(left, right, direction) {
    const leftMissing = left === "" || (typeof left === "number" && Number.isNaN(left) === true)
    const rightMissing = right === "" || (typeof right === "number" && Number.isNaN(right) === true)
    let order = 0
    if (leftMissing === true && rightMissing === false) {
      order = 1
    } else if (leftMissing === false && rightMissing === true) {
      order = -1
    } else if (leftMissing === false && rightMissing === false) {
      if (left < right) {
        order = -direction
      } else if (left > right) {
        order = direction
      }
    }
    return order
  }

  /* ----- rendering ----- */

  _renderRows() {
    if (this._tableBody === undefined) {
      return
    }

    const filtered = this.filteredRows
    const pageSize = this._pageSize > 0 ? this._pageSize : Math.max(1, filtered.length)
    const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize))
    if (this._page >= totalPages) {
      this._page = totalPages - 1
    }
    const pageRows = filtered.slice(this._page * pageSize, (this._page + 1) * pageSize)
    const groupBy = this._groupBy()
    const groupColumn = COLUMNS.find((column) => column.key === groupBy)

    const lines = []
    let currentGroup = null
    pageRows.forEach((row) => {
      if (groupBy !== null) {
        const groupValue = groupBy === "status" ? t(STATUS_META[this._statusKey(row)].labelKey) : toText(row[groupBy])
        if (groupValue !== currentGroup) {
          currentGroup = groupValue
          const count = filtered.filter((candidate) => (groupBy === "status" ? t(STATUS_META[this._statusKey(candidate)].labelKey) : toText(candidate[groupBy])) === groupValue).length
          const groupText = t("mj.buildStatusBoard.groupHeading", { column: t(groupColumn.labelKey), value: groupValue.length > 0 ? groupValue : t("mj.buildStatusBoard.groupNone"), count: count })
          lines.push(html`<tr class="group-row" part="group-row"><th scope="colgroup" colspan="${COLUMNS.length + 1}">${groupText}</th></tr>`)
        }
      }
      lines.push(this._rowMarkup(row))
    })

    this._tableBody.innerHTML = String(html`${lines}`)
    if (filtered.length > 0) {
      setEmptyState(this, "ready")
    } else if (this._rows().length > 0) {
      /* The board has rows but the filters exclude all of them. */
      setEmptyState(this, "no-match", t("mj.buildStatusBoard.noMatch"))
    } else {
      setEmptyState(this, "empty")
    }

    this._updateBulkBar()
    this._updateSelectAll(filtered)
    this._updateSortHeaders()
    this._updatePagination(totalPages)
    this._resultsCount.textContent = t("mj.buildStatusBoard.resultCount", { count: filtered.length })
    this._captionEl.textContent = t("mj.buildStatusBoard.captionCount", { count: filtered.length })
    return
  }

  _rowMarkup(row) {
    const statusKey = this._statusKey(row)
    const meta = STATUS_META[statusKey]
    const rowId = this._rowId(row)
    const name = toText(row.name).length > 0 ? toText(row.name) : rowId
    const selected = this._selectedRows.has(rowId)
    const lastRun = formatChartDate(row.lastRun, { dateStyle: "short", timeStyle: "short" })
    const duration = this._formatDuration(toNumber(row.duration, 0))
    const href = row.url !== undefined && row.url !== null && toText(row.url).length > 0 ? safeUrl(toText(row.url), "") : ""
    const nameMarkup = href.length > 0
      ? html`<a class="pipeline-link" href="${href}" target="_blank" rel="noopener noreferrer">${name}<span class="mj-visually-hidden"> (${t("mj.buildStatusBoard.opensInNewTab")})</span></a>`
      : html`<button class="pipeline-link" type="button">${name}</button>`

    const markup = html`<tr part="data-row" data-status="${statusKey}" data-selected="${selected === true ? "true" : "false"}" data-row-id="${rowId}">
        <td class="check-cell" part="check-cell"><input type="checkbox" aria-label="${t("mj.buildStatusBoard.selectRow", { name: name })}"${selected === true ? html` checked` : html``}></td>
        <td>${nameMarkup}</td>
        <td part="status-cell"><span class="status-badge" part="status-badge"><span class="status-icon" aria-hidden="true" style="color:${meta.color}">${meta.icon}</span><span style="color:${meta.color}">${t(meta.labelKey)}</span></span></td>
        <td>${toText(row.deployTarget)}</td>
        <td>${lastRun}</td>
        <td part="duration-cell">${duration}</td>
        <td part="actor-cell">${toText(row.actor)}</td>
      </tr>`
    return markup
  }

  _formatDuration(seconds) {
    let text = "—"
    if (Number.isFinite(seconds) === true && seconds > 0) {
      const whole = Math.round(seconds)
      const hours = Math.floor(whole / 3600)
      const minutes = Math.floor((whole % 3600) / 60)
      const rest = whole % 60
      if (hours > 0) {
        text = t("mj.buildStatusBoard.durationHours", { hours: hours, minutes: minutes })
      } else if (minutes > 0) {
        text = t("mj.buildStatusBoard.durationMinutes", { minutes: minutes, seconds: rest })
      } else {
        text = t("mj.buildStatusBoard.durationSeconds", { seconds: rest })
      }
    }
    return text
  }

  _updateBulkBar() {
    const count = this._selectedRows.size
    this._bulkBar.hidden = count === 0
    this._bulkBar.setAttribute("aria-label", t("mj.buildStatusBoard.pipelinesSelected", { count: count }))
    this._bulkBar.querySelector(".selected-count").textContent = t("mj.buildStatusBoard.selectedCount", { count: count })
    return
  }

  _updateSelectAll(filtered) {
    const selectedCount = filtered.filter((row) => this._selectedRows.has(this._rowId(row))).length
    this._selectAllChk.checked = filtered.length > 0 && selectedCount === filtered.length
    this._selectAllChk.indeterminate = selectedCount > 0 && selectedCount < filtered.length
    this._selectAllChk.disabled = filtered.length === 0
    return
  }

  _updateSortHeaders() {
    this.$all("th[data-col]").forEach((header) => {
      const active = header.getAttribute("data-col") === this._sortColumn
      const indicator = header.querySelector(".sort-indicator")
      header.setAttribute("aria-sort", active === true ? (this._sortDirection === "asc" ? "ascending" : "descending") : "none")
      indicator.textContent = active === true ? (this._sortDirection === "asc" ? "↑" : "↓") : ""
    })
    return
  }

  _updatePagination(totalPages) {
    this._pageInfo.textContent = t("mj.buildStatusBoard.pageOf", { page: this._page + 1, total: totalPages })
    this._prevPageBtn.disabled = this._page === 0
    this._nextPageBtn.disabled = this._page >= totalPages - 1
    return
  }

  /* ----- interaction ----- */

  _onSort(column) {
    if (column === this._sortColumn) {
      this._sortDirection = this._sortDirection === "asc" ? "desc" : "asc"
    } else {
      this._sortColumn = column
      this._sortDirection = "asc"
    }
    this._renderRows()
    this.emit("mj-sort-change", { column: this._sortColumn, direction: this._sortDirection })
    return
  }

  _onRowToggle(rowElement, checked) {
    const rowId = rowElement.getAttribute("data-row-id")
    if (checked === true) {
      this._selectedRows.add(rowId)
    } else {
      this._selectedRows.delete(rowId)
    }
    rowElement.setAttribute("data-selected", checked === true ? "true" : "false")

    const rowData = this._findRow(rowId)
    this.emit("mj-row-select", { row: rowData !== null ? rowData : { id: rowId }, selected: checked })
    this._emitSelectionChange()
    this._updateBulkBar()
    this._updateSelectAll(this.filteredRows)
    return
  }

  /* Select or clear every filtered row (on all pages). */
  _onSelectAll(checked) {
    const filtered = this.filteredRows
    filtered.forEach((row) => {
      if (checked === true) {
        this._selectedRows.add(this._rowId(row))
      } else {
        this._selectedRows.delete(this._rowId(row))
      }
    })
    this._renderRows()
    this._emitSelectionChange()
    announce(t("mj.buildStatusBoard.pipelinesSelected", { count: this._selectedRows.size }), "polite")
    return
  }

  _emitSelectionChange() {
    const rows = this._rows().filter((row) => this._selectedRows.has(this._rowId(row)))
    this.emit("mj-selection-change", { rows: rows, count: rows.length })
    return
  }

  /* ----- live mode ----- */

  _pollInterval() {
    const parsed = parseInt(this.getAttribute("poll-interval"), 10)
    const interval = Number.isFinite(parsed) === true ? Math.max(MIN_POLL_MS, parsed) : DEFAULT_POLL_MS
    return interval
  }

  _syncLive() {
    this._stopPolling()
    const live = this.flag("live")
    if (this._liveBadge !== undefined) {
      this._liveBadge.hidden = live === false
    }
    if (live === true && this.isConnected === true) {
      this._pollTimer = window.setInterval(() => {
        this.emit("mj-poll-tick", {})
      }, this._pollInterval())
    }
    return
  }

  _stopPolling() {
    if (this._pollTimer !== null) {
      window.clearInterval(this._pollTimer)
      this._pollTimer = null
    }
    return
  }

  updateRowStatus(rowId, newStatus) {
    const row = this._findRow(toText(rowId))
    if (row === null) {
      return
    }
    const previous = row.status
    row.status = newStatus
    this._renderRows()
    this.emit("mj-status-change", { rowId: rowId, previous: previous, current: newStatus })
    const label = STATUS_META[newStatus] !== undefined ? t(STATUS_META[newStatus].labelKey) : toText(newStatus)
    announce(t("mj.buildStatusBoard.statusChanged", { name: toText(row.name).length > 0 ? toText(row.name) : toText(rowId), status: label }), newStatus === "failed" ? "assertive" : "polite")
    return
  }
}
