/*
 * mjbranchgraph.js
 *
 * <mj-branch-graph> -- branch network / commit history graph.
 *
 * Renders branch lanes, commit nodes, merge edges, milestone markers, and
 * phase bands on a shared linear time axis. Accessible data table always
 * present in the shadow DOM alongside the SVG (SVG is aria-hidden).
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { formatDate, formatNumber } from "../core/intl.js";
import { announce } from "../core/announcer.js";

const LANE_HEIGHT = 48;
const LANE_GAP = 8;
const LABEL_W = 120;
const AXIS_H = 32;
const COMMIT_R = 6;

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
.wrapper { display: flex; flex-direction: column; height: 100%; }
.toolbar { display: flex; align-items: center; gap: var(--mj-space-2); padding: var(--mj-space-2) var(--mj-space-3); border-bottom: 1px solid var(--mj-border); }
.toolbar button { font: inherit; font-size: var(--mj-font-size-xs); background: var(--mj-surface); border: 1px solid var(--mj-border-strong); border-radius: var(--mj-radius-sm); padding: 2px var(--mj-space-2); cursor: pointer; color: var(--mj-text); }
.toolbar button:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: var(--mj-focus-ring-offset); }
.chart-area { flex: 1; overflow: auto; position: relative; }
svg { display: block; }
.lane-label { font-size: var(--mj-font-size-xs); fill: var(--mj-text); dominant-baseline: middle; }
.axis-tick { font-size: var(--mj-font-size-xs); fill: var(--mj-text-muted); }
.commit-node { cursor: pointer; }
.commit-node:focus { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: 2px; }
.phase-band { opacity: 0.12; }
.milestone-line { stroke-dasharray: 4 3; }
.detail-panel { position: absolute; top: var(--mj-space-3); right: var(--mj-space-3); min-width: 200px; background: var(--mj-surface-raised); border: 1px solid var(--mj-border-strong); border-radius: var(--mj-radius-md); padding: var(--mj-space-3); box-shadow: var(--mj-elevation-2); }
.detail-panel h3 { margin: 0 0 var(--mj-space-2); font-size: var(--mj-font-size-sm); }
.detail-panel button { float: right; background: none; border: none; cursor: pointer; font-size: 1rem; color: var(--mj-text-muted); }
.a11y-table-wrap { padding: var(--mj-space-3); }
.a11y-table-wrap table { border-collapse: collapse; width: 100%; font-size: var(--mj-font-size-sm); }
.a11y-table-wrap th, .a11y-table-wrap td { border: 1px solid var(--mj-border); padding: var(--mj-space-1) var(--mj-space-2); text-align: left; }
.visually-hidden { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
[hidden] { display: none !important; }
`;

const BAND_COLORS = ["#4d83f7","#15803d","#b45309","#b91c1c","#7c3aed","#0891b2","#c2410c","#4f46e5"];

export class MjBranchGraph extends MjElement {
  static tagName = "mj-branch-graph";
  static styles = STYLES;
  static watched = ["start-date", "end-date", "density", "orientation", "readonly", "today-marker"];

  constructor() {
    super();
    this._data = null;
    this._selectedNode = null;
    this._selectedMarker = null;
    this._showTable = false;
    this._tableId = nextId("mj-bg-table");
    this._detailId = nextId("mj-bg-detail");
  }

  render() {
    return `
      <div class="wrapper" part="wrapper">
        <div class="toolbar" part="toolbar">
          <button class="btn-toggle-table" aria-controls="${this._tableId}" aria-expanded="false">Show data table</button>
          <span class="spacer" style="flex:1"></span>
          <slot name="legend"></slot>
        </div>
        <div class="chart-area" part="chart-area">
          <svg part="svg" aria-hidden="true"></svg>
          <div class="detail-panel" part="detail-panel" role="dialog" aria-modal="false" aria-labelledby="${this._detailId}" hidden>
            <button class="close-detail" aria-label="Close detail">&#x2715;</button>
            <h3 id="${this._detailId}">Detail</h3>
            <div class="detail-content"></div>
          </div>
        </div>
        <div id="${this._tableId}" class="a11y-table-wrap" hidden>
          <table part="data-table">
            <caption>Branch graph data</caption>
            <thead><tr><th>Branch</th><th>SHA</th><th>Message</th><th>Author</th><th>Date</th></tr></thead>
            <tbody class="table-body"></tbody>
          </table>
        </div>
        <slot hidden></slot>
      </div>`;
  }

  afterRender() {
    this._svg = this.$("svg");
    this._detailPanel = this.$(".detail-panel");
    this._detailContent = this.$(".detail-content");
    this._tableBody = this.$(".table-body");
    this._tableWrap = this.$("#" + this._tableId);
    this._toggleTableBtn = this.$(".btn-toggle-table");
    this.listen(this._toggleTableBtn, "click", this._onToggleTable.bind(this));
    this.listen(this.$(".close-detail"), "click", this._closeDetail.bind(this));
    if (this._data !== null) {
      this._draw();
    }
    return;
  }

  get data() {
    return this._data;
  }

  set data(value) {
    this._data = value;
    if (this._svg !== undefined) {
      this._draw();
    }
    return;
  }

  get selectedNode() {
    return this._selectedNode;
  }

  get selectedMarker() {
    return this._selectedMarker;
  }

  _onToggleTable() {
    this._showTable = !this._showTable;
    this._tableWrap.hidden = !this._showTable;
    this._toggleTableBtn.setAttribute("aria-expanded", String(this._showTable));
    return;
  }

  _closeDetail() {
    this._detailPanel.hidden = true;
    this._selectedNode = null;
    this._selectedMarker = null;
    return;
  }

  _draw() {
    const d = this._data;
    if (d === null || d === undefined) {
      return;
    }
    const branches = d.branches || [];
    const commits = d.commits || [];
    const merges = d.merges || [];
    const markers = d.markers || [];
    const phases = d.phases || [];

    if (branches.length === 0) {
      this._svg.innerHTML = "";
      return;
    }

    const allDates = commits.map((c) => new Date(c.date).getTime()).filter((t) => !isNaN(t));
    if (allDates.length === 0) {
      return;
    }
    const startAttr = this.getAttribute("start-date");
    const endAttr = this.getAttribute("end-date");
    const tMin = startAttr !== null ? new Date(startAttr).getTime() : Math.min(...allDates);
    const tMax = endAttr !== null ? new Date(endAttr).getTime() : Math.max(...allDates);
    const tRange = tMax - tMin || 1;

    const totalH = AXIS_H + branches.length * (LANE_HEIGHT + LANE_GAP);
    const totalW = this._svg.parentElement.clientWidth || 800;
    const chartW = totalW - LABEL_W - 16;

    const tx = (ts) => LABEL_W + ((ts - tMin) / tRange) * chartW;

    const branchIndex = {};
    branches.forEach((b, i) => {
      branchIndex[b.id || b.name] = i;
    });
    const laneY = (idx) => AXIS_H + idx * (LANE_HEIGHT + LANE_GAP) + LANE_HEIGHT / 2;

    let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${totalW}" height="${totalH}" viewBox="0 0 ${totalW} ${totalH}">`;
    svg += `<defs>`;
    BAND_COLORS.forEach((c, i) => {
      svg += `<pattern id="pat${i}" patternUnits="userSpaceOnUse" width="6" height="6"><rect width="6" height="6" fill="${c}" opacity="0.15"/><line x1="0" y1="6" x2="6" y2="0" stroke="${c}" stroke-width="1" opacity="0.4"/></pattern>`;
    });
    svg += `</defs>`;

    phases.forEach((ph, i) => {
      const x1 = tx(new Date(ph.start).getTime());
      const x2 = tx(new Date(ph.end).getTime());
      const colorIdx = i % BAND_COLORS.length;
      svg += `<rect class="phase-band" part="phase-band" x="${x1}" y="${AXIS_H}" width="${x2 - x1}" height="${branches.length * (LANE_HEIGHT + LANE_GAP)}" fill="${BAND_COLORS[colorIdx]}" opacity="0.10" aria-hidden="true"/>`;
    });

    const tickCount = Math.min(8, Math.floor(chartW / 80));
    for (let i = 0; i <= tickCount; i = i + 1) {
      const t = tMin + (i / tickCount) * tRange;
      const x = tx(t);
      svg += `<line x1="${x}" y1="${AXIS_H - 6}" x2="${x}" y2="${AXIS_H + branches.length * (LANE_HEIGHT + LANE_GAP)}" stroke="var(--mj-border)" stroke-width="1" aria-hidden="true"/>`;
      svg += `<text class="axis-tick" part="time-axis" x="${x}" y="${AXIS_H - 10}" text-anchor="middle">${formatDate(new Date(t), { month: "short", day: "numeric" })}</text>`;
    }

    branches.forEach((b, i) => {
      const y = laneY(i);
      const bColor = BAND_COLORS[i % BAND_COLORS.length];
      svg += `<line x1="${LABEL_W}" y1="${y}" x2="${totalW - 8}" y2="${y}" stroke="${bColor}" stroke-width="2" part="lane" aria-hidden="true"/>`;
      svg += `<text class="lane-label" part="lane-label" x="${LABEL_W - 8}" y="${y}" text-anchor="end" dominant-baseline="middle">${this._esc(b.name)}</text>`;
    });

    merges.forEach((m) => {
      const fromCommit = commits.find((c) => c.id === m.from);
      const toCommit = commits.find((c) => c.id === m.to);
      if (fromCommit === undefined || toCommit === undefined) {
        return;
      }
      const x1 = tx(new Date(fromCommit.date).getTime());
      const y1 = laneY(branchIndex[fromCommit.branch] || 0);
      const x2 = tx(new Date(toCommit.date).getTime());
      const y2 = laneY(branchIndex[toCommit.branch] || 0);
      const midX = (x1 + x2) / 2;
      svg += `<path class="merge-edge" part="merge-edge" d="M${x1},${y1} C${midX},${y1} ${midX},${y2} ${x2},${y2}" stroke="var(--mj-border-strong)" stroke-width="1.5" fill="none" aria-hidden="true"/>`;
    });

    commits.forEach((c) => {
      const bIdx = branchIndex[c.branch];
      if (bIdx === undefined) {
        return;
      }
      const cx = tx(new Date(c.date).getTime());
      const cy = laneY(bIdx);
      const bColor = BAND_COLORS[bIdx % BAND_COLORS.length];
      const label = `Commit ${(c.sha || c.id || "").slice(0, 7)}: ${c.message || ""}, ${formatDate(new Date(c.date))}`;
      svg += `<circle class="commit-node" part="commit-node" cx="${cx}" cy="${cy}" r="${COMMIT_R}" fill="${bColor}" stroke="var(--mj-surface)" stroke-width="2" tabindex="0" role="button" aria-label="${this._esc(label)}" data-commit-id="${this._esc(c.id || c.sha || "")}"/>`;
    });

    markers.forEach((m) => {
      const mx = tx(new Date(m.date).getTime());
      const mColor = m.type === "release" ? "var(--mj-color-success)" : m.type === "freeze" ? "var(--mj-color-warning)" : "var(--mj-color-info)";
      svg += `<line class="milestone-line" part="milestone-marker" x1="${mx}" y1="0" x2="${mx}" y2="${totalH}" stroke="${mColor}" stroke-width="2" aria-hidden="true"/>`;
      svg += `<text x="${mx + 4}" y="14" font-size="11" fill="${mColor}">${this._esc(m.name)}</text>`;
    });

    if (this.hasAttribute("today-marker") !== false && this.getAttribute("today-marker") !== "false") {
      const todayX = tx(Date.now());
      if (todayX >= LABEL_W && todayX <= totalW) {
        svg += `<line part="today-marker" x1="${todayX}" y1="${AXIS_H}" x2="${todayX}" y2="${totalH}" stroke="var(--mj-color-danger)" stroke-width="2" stroke-dasharray="6 3" aria-hidden="true"/>`;
        svg += `<text x="${todayX + 4}" y="${AXIS_H + 14}" font-size="10" fill="var(--mj-color-danger)">Today</text>`;
      }
    }

    svg += `</svg>`;
    this._svg.outerHTML = svg;
    this._svg = this.$("svg") || this._svg;

    const newSvg = this.shadowRoot.querySelector("svg");
    if (newSvg !== null) {
      this.listen(newSvg, "click", this._onSvgClick.bind(this));
      this.listen(newSvg, "keydown", this._onSvgKeydown.bind(this));
    }

    this._buildTable(commits, branches);
    this.setAttribute("aria-label", `Branch graph: ${branches.length} branches, ${commits.length} commits, ${markers.length} milestones`);
    this.setAttribute("role", "img");
    return;
  }

  _buildTable(commits, branches) {
    if (this._tableBody === null || this._tableBody === undefined) {
      return;
    }
    const rows = commits.map((c) => {
      return `<tr><td>${this._esc(c.branch)}</td><td>${this._esc((c.sha || c.id || "").slice(0, 7))}</td><td>${this._esc(c.message || "")}</td><td>${this._esc(c.author || "")}</td><td>${formatDate(new Date(c.date))}</td></tr>`;
    });
    this._tableBody.innerHTML = rows.join("");
    return;
  }

  _onSvgClick(event) {
    const node = event.target.closest("[data-commit-id]");
    if (node !== null) {
      const id = node.getAttribute("data-commit-id");
      const commits = (this._data && this._data.commits) || [];
      const commit = commits.find((c) => (c.id || c.sha || "") === id);
      if (commit !== undefined) {
        this._selectedNode = commit;
        this._showDetail(`Commit ${(commit.sha || commit.id || "").slice(0, 7)}`, `<p><strong>Branch:</strong> ${this._esc(commit.branch)}</p><p><strong>Message:</strong> ${this._esc(commit.message || "")}</p><p><strong>Author:</strong> ${this._esc(commit.author || "")}</p><p><strong>Date:</strong> ${formatDate(new Date(commit.date))}</p>`);
        this.emit("mj-node-select", { node: commit, branch: commit.branch });
      }
    }
    return;
  }

  _onSvgKeydown(event) {
    if (event.key === "Enter" || event.key === " ") {
      this._onSvgClick(event);
    }
    if (event.key === "Escape") {
      this._closeDetail();
    }
    return;
  }

  _showDetail(title, html) {
    const h3 = this._detailPanel.querySelector("h3");
    if (h3 !== null) {
      h3.textContent = title;
    }
    this._detailContent.innerHTML = html;
    this._detailPanel.hidden = false;
    return;
  }

  _esc(str) {
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._svg !== undefined && this._data !== null) {
      this._draw();
    }
    return;
  }
}
