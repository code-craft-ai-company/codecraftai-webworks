/*
 * mjbuildstatusboard.js
 *
 * <mj-build-status-board> -- grid / big-board view of pipeline/branch build
 * and deploy statuses. Sortable, filterable, live-updatable table.
 *
 * Implemented as a self-contained table (no external DataTable dependency).
 * Accessible <table> with role="grid" is the primary visual.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { formatDate } from "../core/intl.js";
import { announce } from "../core/announcer.js";

const STATUS_META = {
  pending:   { icon: "○", label: "Pending",   color: "var(--mj-text-muted)"    },
  running:   { icon: "◎", label: "Running",   color: "var(--mj-color-info)"    },
  passed:    { icon: "✓", label: "Passed",    color: "var(--mj-color-success)" },
  failed:    { icon: "✗", label: "Failed",    color: "var(--mj-color-danger)"  },
  cancelled: { icon: "⊘", label: "Cancelled", color: "var(--mj-text-muted)"    },
  skipped:   { icon: "→", label: "Skipped",   color: "var(--mj-text-muted)"    },
  unknown:   { icon: "?", label: "Unknown",   color: "var(--mj-text-muted)"    },
};

const STYLES = `
:host {
  display: block;
  font-family: var(--mj-font-sans);
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
  background: var(--mj-bg);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-md);
  overflow: hidden;
}
.wrapper { display: flex; flex-direction: column; }
.board-header { display: flex; align-items: center; gap: var(--mj-space-2); padding: var(--mj-space-2) var(--mj-space-3); border-bottom: 1px solid var(--mj-border); flex-wrap: wrap; }
.board-title { font-weight: var(--mj-font-weight-medium); font-size: var(--mj-font-size-sm); }
.live-badge { display: inline-flex; align-items: center; gap: 4px; font-size: var(--mj-font-size-xs); color: var(--mj-color-info); }
.live-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--mj-color-info); animation: mj-pulse 1.4s ease-in-out infinite; }
@keyframes mj-pulse { 0%,100%{opacity:1;} 50%{opacity:0.3;} }
@media (prefers-reduced-motion:reduce) { .live-dot { animation:none; } }
.filter-bar { display: flex; gap: var(--mj-space-2); padding: var(--mj-space-2) var(--mj-space-3); border-bottom: 1px solid var(--mj-border); flex-wrap: wrap; }
.filter-bar input, .filter-bar select { font: inherit; font-size: var(--mj-font-size-xs); background: var(--mj-surface); border: 1px solid var(--mj-border-strong); border-radius: var(--mj-radius-sm); padding: 2px 8px; color: var(--mj-text); }
.filter-bar input:focus, .filter-bar select:focus { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: var(--mj-focus-ring-offset); }
.filter-bar button { font: inherit; font-size: var(--mj-font-size-xs); background: var(--mj-surface); border: 1px solid var(--mj-border-strong); border-radius: var(--mj-radius-sm); padding: 2px 8px; cursor: pointer; color: var(--mj-text); }
.results-count { font-size: var(--mj-font-size-xs); color: var(--mj-text-muted); padding: 2px var(--mj-space-2); }
.table-wrap { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: var(--mj-font-size-sm); }
caption { font-size: var(--mj-font-size-xs); color: var(--mj-text-muted); text-align: left; padding: var(--mj-space-2) var(--mj-space-3); }
th { padding: var(--mj-space-2) var(--mj-space-3); text-align: left; background: var(--mj-bg-subtle); border-bottom: 2px solid var(--mj-border); font-weight: var(--mj-font-weight-medium); white-space: nowrap; }
th[aria-sort] { cursor: pointer; }
th[aria-sort]:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: -2px; }
th .sort-indicator { font-size: 10px; margin-left: 4px; color: var(--mj-text-muted); }
td { padding: var(--mj-space-2) var(--mj-space-3); border-bottom: 1px solid var(--mj-border); vertical-align: middle; }
tr[data-status="failed"] { background: var(--mj-color-danger-surface); }
tr[data-status="running"] { background: var(--mj-color-info-surface); }
tr[aria-selected="true"] { background: var(--mj-color-accent-50); }
.status-badge { display: inline-flex; align-items: center; gap: 4px; font-size: var(--mj-font-size-xs); font-weight: var(--mj-font-weight-medium); }
.status-icon { font-size: 13px; }
.pipeline-link { color: var(--mj-accent); text-decoration: none; }
.pipeline-link:hover { text-decoration: underline; }
.pipeline-link:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); }
.check-cell { width: 36px; text-align: center; }
.bulk-bar { display: flex; align-items: center; gap: var(--mj-space-2); padding: var(--mj-space-2) var(--mj-space-3); background: var(--mj-color-accent-50); border-top: 1px solid var(--mj-border); font-size: var(--mj-font-size-xs); }
.pagination { display: flex; align-items: center; gap: var(--mj-space-2); padding: var(--mj-space-2) var(--mj-space-3); border-top: 1px solid var(--mj-border); font-size: var(--mj-font-size-xs); }
.pagination button { font: inherit; font-size: var(--mj-font-size-xs); background: var(--mj-surface); border: 1px solid var(--mj-border-strong); border-radius: var(--mj-radius-sm); padding: 2px 8px; cursor: pointer; color: var(--mj-text); }
.pagination button:disabled { opacity: 0.4; cursor: default; }
.pagination button:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: var(--mj-focus-ring-offset); }
[hidden] { display: none !important; }
`;

export class MjBuildStatusBoard extends MjElement {
  static tagName = "mj-build-status-board";
  static styles = STYLES;
  static watched = ["group-by", "density", "live", "filter-status", "filter-pattern", "page-size", "sort-column", "sort-direction"];

  constructor() {
    super();
    this._data = null;
    this._selectedRows = new Set();
    this._sortColumn = "lastRun";
    this._sortDirection = "desc";
    this._filterStatus = "";
    this._filterPattern = "";
    this._pageSize = 25;
    this._page = 0;
    this._pollTimer = null;
    this._captionId = nextId("mj-bsb-cap");
  }

  render() {
    return `
      <div class="wrapper" part="wrapper">
        <div class="board-header" part="live-indicator">
          <span class="board-title">Build Status Board</span>
          <div class="live-badge" hidden><span class="live-dot" aria-hidden="true"></span> Live</div>
          <span style="flex:1"></span>
        </div>
        <div class="filter-bar" part="filter-bar">
          <label for="filter-status-sel" class="visually-hidden">Filter by status</label>
          <select id="filter-status-sel" aria-label="Filter by status">
            <option value="">All statuses</option>
            ${Object.keys(STATUS_META).map((s) => `<option value="${s}">${STATUS_META[s].label}</option>`).join("")}
          </select>
          <label for="filter-pattern-inp" class="visually-hidden">Filter by name</label>
          <input id="filter-pattern-inp" type="text" placeholder="Filter by name…" aria-label="Filter by pipeline name"/>
          <button class="clear-filters-btn">Clear filters</button>
          <span class="results-count"></span>
        </div>
        <div class="table-wrap">
          <table part="table" role="grid">
            <caption id="${this._captionId}" part="caption">Build status board</caption>
            <thead>
              <tr class="header-row" part="header-row">
                <th class="check-cell" scope="col"><input type="checkbox" aria-label="Select all pipelines"/></th>
                <th scope="col" tabindex="0" data-col="name" aria-sort="none" part="header-cell">Pipeline <span class="sort-indicator"></span></th>
                <th scope="col" tabindex="0" data-col="status" aria-sort="none" part="header-cell">Status <span class="sort-indicator"></span></th>
                <th scope="col" tabindex="0" data-col="deployTarget" aria-sort="none" part="header-cell">Deploy target <span class="sort-indicator"></span></th>
                <th scope="col" tabindex="0" data-col="lastRun" aria-sort="descending" part="header-cell">Last run <span class="sort-indicator">↓</span></th>
                <th scope="col" tabindex="0" data-col="duration" aria-sort="none" part="header-cell">Duration <span class="sort-indicator"></span></th>
                <th scope="col" part="header-cell">Actor</th>
              </tr>
            </thead>
            <tbody class="table-body" part="table-body"></tbody>
          </table>
        </div>
        <div class="bulk-bar" part="bulk-action-bar" role="toolbar" aria-label="0 pipelines selected" hidden>
          <span class="selected-count">0 selected</span>
          <slot name="bulk-actions"></slot>
        </div>
        <div class="pagination" part="pagination">
          <button class="prev-page-btn" disabled>&#x2039; Prev</button>
          <span class="page-info"></span>
          <button class="next-page-btn">Next &#x203A;</button>
        </div>
        <slot hidden></slot>
      </div>`;
  }

  afterRender() {
    this._tableBody = this.$(".table-body");
    this._captionEl = this.$("#" + this._captionId);
    this._statusSel = this.$("#filter-status-sel");
    this._patternInput = this.$("#filter-pattern-inp");
    this._clearBtn = this.$(".clear-filters-btn");
    this._resultsCount = this.$(".results-count");
    this._bulkBar = this.$(".bulk-bar");
    this._pageInfo = this.$(".page-info");
    this._prevPageBtn = this.$(".prev-page-btn");
    this._nextPageBtn = this.$(".next-page-btn");
    this._selectAllChk = this.$("thead input[type=checkbox]");
    this._liveBadge = this.$(".live-badge");

    this._sortColumn = this.getAttribute("sort-column") || "lastRun";
    this._sortDirection = this.getAttribute("sort-direction") || "desc";
    this._filterStatus = this.getAttribute("filter-status") || "";
    this._filterPattern = this.getAttribute("filter-pattern") || "";
    this._pageSize = parseInt(this.getAttribute("page-size") || "25", 10);

    if (this._statusSel !== null) {
      if (this._filterStatus !== "") {
        this._statusSel.value = this._filterStatus;
      }
      this.listen(this._statusSel, "change", (e) => {
        this._filterStatus = e.target.value;
        this._page = 0;
        this.emit("mj-filter-change", { status: this._filterStatus, pattern: this._filterPattern });
        this._renderRows();
      });
    }
    if (this._patternInput !== null) {
      this.listen(this._patternInput, "input", (e) => {
        this._filterPattern = e.target.value;
        this._page = 0;
        this._renderRows();
      });
    }
    if (this._clearBtn !== null) {
      this.listen(this._clearBtn, "click", () => {
        this._filterStatus = "";
        this._filterPattern = "";
        if (this._statusSel !== null) {
          this._statusSel.value = "";
        }
        if (this._patternInput !== null) {
          this._patternInput.value = "";
        }
        this._page = 0;
        this._renderRows();
      });
    }
    if (this._prevPageBtn !== null) {
      this.listen(this._prevPageBtn, "click", () => {
        if (this._page > 0) {
          this._page = this._page - 1;
          this._renderRows();
        }
      });
    }
    if (this._nextPageBtn !== null) {
      this.listen(this._nextPageBtn, "click", () => {
        this._page = this._page + 1;
        this._renderRows();
      });
    }
    if (this._selectAllChk !== null) {
      this.listen(this._selectAllChk, "change", (e) => {
        const filtered = this.filteredRows;
        if (e.target.checked === true) {
          filtered.forEach((r) => { this._selectedRows.add(r.id || r.name); });
        } else {
          this._selectedRows.clear();
        }
        this._renderRows();
      });
    }

    this.$all("th[data-col]").forEach((th) => {
      this.listen(th, "click", (e) => {
        const col = e.currentTarget.getAttribute("data-col");
        if (col === this._sortColumn) {
          this._sortDirection = this._sortDirection === "asc" ? "desc" : "asc";
        } else {
          this._sortColumn = col;
          this._sortDirection = "asc";
        }
        this.emit("mj-sort-change", { column: this._sortColumn, direction: this._sortDirection });
        this._renderRows();
      });
      this.listen(th, "keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          th.click();
        }
      });
    });

    if (this.hasAttribute("live") && this.getAttribute("live") !== "false") {
      this._startLive();
    }

    if (this._data !== null) {
      this._renderRows();
    }
    return;
  }

  get data() {
    return this._data;
  }

  set data(value) {
    this._data = value;
    if (this._tableBody !== undefined) {
      this._renderRows();
    }
    return;
  }

  get selectedRows() {
    return this._selectedRows;
  }

  get filteredRows() {
    const rows = (this._data && this._data.rows) || [];
    let working = rows;
    if (this._filterStatus !== "") {
      working = working.filter((r) => (r.status || "") === this._filterStatus);
    }
    if (this._filterPattern !== "" && this._filterPattern.length > 0) {
      const pattern = this._filterPattern.toLowerCase();
      working = working.filter((r) => (r.name || "").toLowerCase().includes(pattern));
    }
    working = working.slice().sort((a, b) => {
      const col = this._sortColumn;
      let av = a[col] || "";
      let bv = b[col] || "";
      if (col === "lastRun") {
        av = new Date(av).getTime();
        bv = new Date(bv).getTime();
      }
      let order = 0;
      if (av < bv) {
        order = -1;
      } else if (av > bv) {
        order = 1;
      }
      return this._sortDirection === "desc" ? -order : order;
    });
    return working;
  }

  _renderRows() {
    if (this._tableBody === null || this._tableBody === undefined) {
      return;
    }
    const filtered = this.filteredRows;
    const pageSize = this._pageSize > 0 ? this._pageSize : filtered.length;
    const totalPages = Math.ceil(filtered.length / pageSize) || 1;
    if (this._page >= totalPages) {
      this._page = totalPages - 1;
    }
    const pageRows = filtered.slice(this._page * pageSize, (this._page + 1) * pageSize);

    const rows = pageRows.map((row) => {
      const status = row.status || "unknown";
      const sm = STATUS_META[status] || STATUS_META.unknown;
      const isSelected = this._selectedRows.has(row.id || row.name);
      const lastRun = row.lastRun ? formatDate(new Date(row.lastRun), { dateStyle: "short", timeStyle: "short" }) : "—";
      const duration = this._formatDuration(row.duration || 0);
      return `<tr part="data-row" data-status="${status}" aria-selected="${isSelected}" data-row-id="${this._esc(row.id || row.name)}">
        <td class="check-cell" part="check-cell"><input type="checkbox" aria-label="Select ${this._esc(row.name || "")}" ${isSelected ? "checked" : ""}></td>
        <td>${row.url ? `<a class="pipeline-link" href="${this._esc(row.url)}" target="_blank">${this._esc(row.name || "")}</a>` : this._esc(row.name || "")}</td>
        <td part="status-cell"><span class="status-badge" part="status-badge"><span class="status-icon" aria-hidden="true" style="color:${sm.color}">${sm.icon}</span><span style="color:${sm.color}">${sm.label}</span></span></td>
        <td>${this._esc(row.deployTarget || "")}</td>
        <td>${lastRun}</td>
        <td part="duration-cell">${this._esc(duration)}</td>
        <td part="actor-cell">${this._esc(row.actor || "")}</td>
      </tr>`;
    });

    this._tableBody.innerHTML = rows.join("");

    this._tableBody.querySelectorAll("tr").forEach((tr) => {
      const chk = tr.querySelector("input[type=checkbox]");
      if (chk !== null) {
        this.listen(chk, "change", (e) => {
          const rowId = tr.getAttribute("data-row-id");
          if (e.target.checked === true) {
            this._selectedRows.add(rowId);
          } else {
            this._selectedRows.delete(rowId);
          }
          const allRows = (this._data && this._data.rows) || [];
          const rowData = allRows.find((r) => (r.id || r.name) === rowId);
          this.emit("mj-row-select", { row: rowData || { id: rowId }, selected: e.target.checked });
          this._updateBulkBar();
          this._updateSelectAll(filtered.length);
        });
      }
      const link = tr.querySelector(".pipeline-link");
      if (link !== null) {
        this.listen(link, "click", (e) => {
          const rowId = tr.getAttribute("data-row-id");
          const allRows = (this._data && this._data.rows) || [];
          const rowData = allRows.find((r) => (r.id || r.name) === rowId);
          this.emit("mj-row-activate", { row: rowData || { id: rowId } });
        });
      }
    });

    this._updateBulkBar();
    this._updateSelectAll(filtered.length);
    this._updateSortHeaders();
    this._updatePagination(filtered.length, pageSize, totalPages);

    if (this._resultsCount !== null) {
      this._resultsCount.textContent = `${filtered.length} result${filtered.length !== 1 ? "s" : ""}`;
    }
    if (this._captionEl !== null) {
      this._captionEl.textContent = `Build status board: ${filtered.length} pipelines`;
    }

    this.emit("mj-data-load", { rows: filtered.length });
    return;
  }

  _updateBulkBar() {
    const count = this._selectedRows.size;
    if (this._bulkBar !== null) {
      this._bulkBar.hidden = count === 0;
      this._bulkBar.setAttribute("aria-label", `${count} pipeline${count !== 1 ? "s" : ""} selected`);
      const span = this._bulkBar.querySelector(".selected-count");
      if (span !== null) {
        span.textContent = `${count} selected`;
      }
    }
    return;
  }

  _updateSelectAll(totalFiltered) {
    if (this._selectAllChk === null) {
      return;
    }
    const filtered = this.filteredRows;
    const selectedCount = filtered.filter((r) => this._selectedRows.has(r.id || r.name)).length;
    if (selectedCount === 0) {
      this._selectAllChk.checked = false;
      this._selectAllChk.indeterminate = false;
    } else if (selectedCount === totalFiltered) {
      this._selectAllChk.checked = true;
      this._selectAllChk.indeterminate = false;
    } else {
      this._selectAllChk.checked = false;
      this._selectAllChk.indeterminate = true;
    }
    return;
  }

  _updateSortHeaders() {
    this.$all("th[data-col]").forEach((th) => {
      const col = th.getAttribute("data-col");
      const indicator = th.querySelector(".sort-indicator");
      if (col === this._sortColumn) {
        th.setAttribute("aria-sort", this._sortDirection === "asc" ? "ascending" : "descending");
        if (indicator !== null) {
          indicator.textContent = this._sortDirection === "asc" ? "↑" : "↓";
        }
      } else {
        th.setAttribute("aria-sort", "none");
        if (indicator !== null) {
          indicator.textContent = "";
        }
      }
    });
    return;
  }

  _updatePagination(total, pageSize, totalPages) {
    if (this._pageInfo !== null) {
      this._pageInfo.textContent = `Page ${this._page + 1} of ${totalPages}`;
    }
    if (this._prevPageBtn !== null) {
      this._prevPageBtn.disabled = this._page === 0;
    }
    if (this._nextPageBtn !== null) {
      this._nextPageBtn.disabled = this._page >= totalPages - 1;
    }
    return;
  }

  _formatDuration(seconds) {
    if (seconds === 0 || seconds === undefined || seconds === null) {
      return "—";
    }
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    if (h > 0) {
      return `${h}h ${m}m`;
    }
    if (m > 0) {
      return `${m}m ${s}s`;
    }
    return `${s}s`;
  }

  _startLive() {
    if (this._liveBadge !== null) {
      this._liveBadge.hidden = false;
    }
    const interval = parseInt(this.getAttribute("poll-interval") || "30000", 10);
    this._pollTimer = setInterval(() => {
      this.emit("mj-poll-tick", {});
    }, interval);
    this.onTeardown(() => {
      if (this._pollTimer !== null) {
        clearInterval(this._pollTimer);
        this._pollTimer = null;
      }
    });
    return;
  }

  updateRowStatus(rowId, newStatus) {
    const rows = (this._data && this._data.rows) || [];
    const row = rows.find((r) => (r.id || r.name) === rowId);
    if (row === undefined) {
      return;
    }
    const previous = row.status;
    row.status = newStatus;
    this._renderRows();
    this.emit("mj-status-change", { rowId, previous, current: newStatus });
    announce(`${row.name || rowId} status changed to ${newStatus}`, newStatus === "failed" ? "assertive" : "polite");
    return;
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "filter-status") {
      this._filterStatus = newValue || "";
    }
    if (name === "filter-pattern") {
      this._filterPattern = newValue || "";
    }
    if (name === "sort-column") {
      this._sortColumn = newValue || "lastRun";
    }
    if (name === "sort-direction") {
      this._sortDirection = newValue || "desc";
    }
    if (name === "page-size") {
      this._pageSize = parseInt(newValue || "25", 10);
    }
    if (this._tableBody !== undefined && this._data !== null) {
      this._renderRows();
    }
    return;
  }

  _esc(str) {
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
}
