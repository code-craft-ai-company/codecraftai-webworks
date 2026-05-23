/*
 * mjroadmapchart.js
 *
 * <mj-roadmap-chart> -- initiative roadmap chart with swimlane rows and
 * calendar-column or named-bucket columns.
 *
 * SVG is aria-hidden; accessible data table always present.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { formatDate } from "../core/intl.js";

const ROW_H = 64;
const LABEL_W = 200;
const HEADER_H = 40;
const COL_MIN_W = 120;

const STATUS_COLORS = {
  planned:     "var(--mj-color-accent-400)",
  "in-progress": "var(--mj-color-info)",
  done:        "var(--mj-color-success)",
  "at-risk":   "var(--mj-color-warning)",
  blocked:     "var(--mj-color-danger)",
};

const STATUS_ICONS = {
  planned:     "○",
  "in-progress": "◎",
  done:        "✓",
  "at-risk":   "⚠",
  blocked:     "⊘",
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
.toolbar { display: flex; align-items: center; gap: var(--mj-space-2); padding: var(--mj-space-2) var(--mj-space-3); border-bottom: 1px solid var(--mj-border); }
.toolbar button { font: inherit; font-size: var(--mj-font-size-xs); background: var(--mj-surface); border: 1px solid var(--mj-border-strong); border-radius: var(--mj-radius-sm); padding: 2px var(--mj-space-2); cursor: pointer; color: var(--mj-text); }
.toolbar button:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: var(--mj-focus-ring-offset); }
.chart-scroll { overflow: auto; }
svg { display: block; }
.bar-el { cursor: pointer; }
.bar-el:focus { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); }
.detail-panel { padding: var(--mj-space-3); background: var(--mj-surface-raised); border-top: 1px solid var(--mj-border); }
.detail-panel h3 { margin: 0 0 var(--mj-space-2); font-size: var(--mj-font-size-sm); }
.a11y-table-wrap { padding: var(--mj-space-3); }
.a11y-table-wrap table { border-collapse: collapse; width: 100%; font-size: var(--mj-font-size-sm); }
.a11y-table-wrap th, .a11y-table-wrap td { border: 1px solid var(--mj-border); padding: var(--mj-space-1) var(--mj-space-2); text-align: left; }
[hidden] { display: none !important; }
`;

export class MjRoadmapChart extends MjElement {
  static tagName = "mj-roadmap-chart";
  static styles = STYLES;
  static watched = ["mode", "scale", "start-date", "end-date", "today-marker", "density"];

  constructor() {
    super();
    this._data = null;
    this._selectedInitiative = null;
    this._showTable = false;
    this._tableId = nextId("mj-rc-table");
  }

  render() {
    return `
      <div class="wrapper" part="wrapper" role="img" aria-label="Roadmap chart">
        <div class="toolbar" part="toolbar">
          <button class="btn-toggle-table" aria-controls="${this._tableId}" aria-expanded="false">Show data table</button>
          <slot name="legend"></slot>
        </div>
        <div class="chart-scroll">
          <svg part="svg" aria-hidden="true"></svg>
        </div>
        <div class="detail-panel" part="initiative-detail" hidden>
          <h3></h3>
          <div class="detail-content"></div>
          <slot name="initiative-detail"></slot>
        </div>
        <div id="${this._tableId}" class="a11y-table-wrap" hidden>
          <table part="data-table">
            <caption>Roadmap initiatives</caption>
            <thead><tr><th>Initiative</th><th>Swimlane</th><th>Column/Timeframe</th><th>Status</th><th>% Complete</th></tr></thead>
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
    this._toggleBtn = this.$(".btn-toggle-table");
    this.listen(this._toggleBtn, "click", this._onToggleTable.bind(this));
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

  get selectedInitiative() {
    return this._selectedInitiative;
  }

  _onToggleTable() {
    this._showTable = !this._showTable;
    this._tableWrap.hidden = !this._showTable;
    this._toggleBtn.setAttribute("aria-expanded", String(this._showTable));
    return;
  }

  _draw() {
    const d = this._data;
    if (d === null || d === undefined) {
      return;
    }
    const swimlanes = d.swimlanes || [{ id: "default", name: "" }];
    const initiatives = d.initiatives || [];
    const markers = d.markers || [];
    const phases = d.phases || [];
    const buckets = d.buckets || null;

    const mode = this.getAttribute("mode") || "calendar";
    let columns = [];

    if (mode === "bucket" && buckets !== null && buckets.length > 0) {
      columns = buckets.map((b) => ({ id: b.id || b.name, label: b.name }));
    } else {
      const startAttr = this.getAttribute("start-date");
      const endAttr = this.getAttribute("end-date");
      const allTimes = initiatives.flatMap((ini) => [new Date(ini.startDate || ini.start || Date.now()).getTime(), new Date(ini.endDate || ini.end || Date.now()).getTime()]);
      const tMin = startAttr !== null ? new Date(startAttr).getTime() : (allTimes.length > 0 ? Math.min(...allTimes) : Date.now());
      const tMax = endAttr !== null ? new Date(endAttr).getTime() : (allTimes.length > 0 ? Math.max(...allTimes) : Date.now() + 86400000 * 90);
      const scale = this.getAttribute("scale") || "quarter";
      columns = this._buildCalendarColumns(tMin, tMax, scale);
    }

    const colW = Math.max(COL_MIN_W, 160);
    const totalW = LABEL_W + columns.length * colW;
    const totalH = HEADER_H + swimlanes.length * ROW_H;

    let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${totalW}" height="${totalH}">`;

    svg += `<rect x="0" y="0" width="${LABEL_W}" height="${totalH}" fill="var(--mj-bg-subtle)" aria-hidden="true"/>`;
    columns.forEach((col, ci) => {
      const x = LABEL_W + ci * colW;
      svg += `<rect x="${x}" y="0" width="${colW}" height="${HEADER_H}" fill="var(--mj-bg-muted)" aria-hidden="true"/>`;
      svg += `<line x1="${x}" y1="0" x2="${x}" y2="${totalH}" stroke="var(--mj-border)" stroke-width="1" aria-hidden="true"/>`;
      svg += `<text x="${x + colW / 2}" y="${HEADER_H / 2 + 5}" text-anchor="middle" font-size="12" fill="var(--mj-text)" font-weight="500" part="column-header">${this._esc(col.label)}</text>`;
    });

    swimlanes.forEach((lane, li) => {
      const laneY = HEADER_H + li * ROW_H;
      svg += `<line x1="0" y1="${laneY}" x2="${totalW}" y2="${laneY}" stroke="var(--mj-border)" stroke-width="1" aria-hidden="true"/>`;
      svg += `<text x="8" y="${laneY + ROW_H / 2 + 5}" font-size="12" fill="var(--mj-text)" part="swimlane-label">${this._esc(lane.name || lane.id || "")}</text>`;

      const laneInitiatives = initiatives.filter((ini) => (ini.swimlaneId || ini.swimlane || "default") === (lane.id || lane.name));
      laneInitiatives.forEach((ini) => {
        const colIdx = columns.findIndex((c) => c.id === (ini.columnId || ini.bucket || ini.column || ""));
        const effectiveColIdx = colIdx >= 0 ? colIdx : 0;
        const barX = LABEL_W + effectiveColIdx * colW + 4;
        const barY = laneY + 8;
        const barW = colW - 8;
        const barH = ROW_H - 16;
        const color = STATUS_COLORS[ini.status] || STATUS_COLORS.planned;
        const icon = STATUS_ICONS[ini.status] || "○";
        const iniColumn = columns[effectiveColIdx]
        const iniColumnLabel = iniColumn !== undefined ? iniColumn.label : ""
        const barLabel = `${ini.name}, ${ini.status || "planned"}, ${iniColumnLabel}`;
        svg += `<g class="bar-el" part="initiative-bar" tabindex="0" role="gridcell" aria-label="${this._esc(barLabel)}" data-ini-id="${this._esc(ini.id || ini.name)}">`;
        svg += `<rect x="${barX}" y="${barY}" width="${barW}" height="${barH}" rx="4" fill="${color}" opacity="0.2" stroke="${color}" stroke-width="1.5"/>`;
        svg += `<text x="${barX + 20}" y="${barY + barH / 2 + 4}" font-size="11" fill="var(--mj-text)" part="initiative-label">${this._esc(ini.name.length > 18 ? ini.name.slice(0, 16) + "…" : ini.name)}</text>`;
        svg += `<text x="${barX + 6}" y="${barY + barH / 2 + 4}" font-size="12" fill="${color}" aria-hidden="true">${icon}</text>`;
        svg += `</g>`;
      });
    });

    if (this.getAttribute("today-marker") !== "false" && mode === "calendar") {
      svg += `<!-- today marker would be positioned based on time scale -->`;
    }

    svg += `</svg>`;

    const scrollArea = this.$(".chart-scroll");
    if (scrollArea !== null) {
      scrollArea.innerHTML = svg;
      const newSvg = scrollArea.querySelector("svg");
      if (newSvg !== null) {
        this._svg = newSvg;
        this.listen(newSvg, "click", this._onSvgClick.bind(this));
        this.listen(newSvg, "keydown", this._onSvgKeydown.bind(this));
      }
    }

    this._buildTable(initiatives, columns);

    const wrapper = this.$(".wrapper");
    if (wrapper !== null) {
      wrapper.setAttribute("aria-label", `Roadmap: ${initiatives.length} initiatives across ${swimlanes.length} swimlanes`);
    }
    return;
  }

  _buildCalendarColumns(tMin, tMax, scale) {
    const cols = [];
    const d = new Date(tMin);
    d.setDate(1);
    d.setHours(0, 0, 0, 0);
    const endDate = new Date(tMax);
    while (d <= endDate) {
      if (scale === "quarter") {
        const q = Math.floor(d.getMonth() / 3) + 1;
        cols.push({ id: `Q${q}-${d.getFullYear()}`, label: `Q${q} ${d.getFullYear()}` });
        d.setMonth(d.getMonth() + 3);
      } else if (scale === "month") {
        cols.push({ id: `${d.getFullYear()}-${d.getMonth()}`, label: formatDate(d, { month: "short", year: "numeric" }) });
        d.setMonth(d.getMonth() + 1);
      } else {
        cols.push({ id: `H${d.getMonth() < 6 ? 1 : 2}-${d.getFullYear()}`, label: `H${d.getMonth() < 6 ? 1 : 2} ${d.getFullYear()}` });
        d.setMonth(d.getMonth() + 6);
      }
      if (cols.length > 20) {
        break;
      }
    }
    return cols;
  }

  _buildTable(initiatives, columns) {
    if (this._tableBody === null || this._tableBody === undefined) {
      return;
    }
    const rows = initiatives.map((ini) => {
      const col = columns.find((c) => c.id === (ini.columnId || ini.bucket || ini.column || ""));
      return `<tr><td>${this._esc(ini.name)}</td><td>${this._esc(ini.swimlaneId || ini.swimlane || "")}</td><td>${this._esc(col ? col.label : "")}</td><td>${this._esc(ini.status || "")}</td><td>${ini.percentComplete || 0}%</td></tr>`;
    });
    this._tableBody.innerHTML = rows.join("");
    return;
  }

  _onSvgClick(event) {
    const node = event.target.closest("[data-ini-id]");
    if (node !== null) {
      const id = node.getAttribute("data-ini-id");
      const initiatives = (this._data && this._data.initiatives) || [];
      const ini = initiatives.find((i) => (i.id || i.name) === id);
      if (ini !== undefined) {
        this._selectedInitiative = ini;
        const h3 = this._detailPanel.querySelector("h3");
        if (h3 !== null) {
          h3.textContent = ini.name;
        }
        this._detailContent.innerHTML = `<p><strong>Status:</strong> ${this._esc(ini.status || "")}</p>`;
        this._detailPanel.hidden = false;
        this.emit("mj-initiative-select", { initiative: ini });
      }
    }
    return;
  }

  _onSvgKeydown(event) {
    if (event.key === "Enter" || event.key === " ") {
      this._onSvgClick(event);
    }
    if (event.key === "Escape") {
      this._detailPanel.hidden = true;
      this._selectedInitiative = null;
      this.emit("mj-initiative-deselect", {});
    }
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
