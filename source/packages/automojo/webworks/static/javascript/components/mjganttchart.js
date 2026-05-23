/*
 * mjganttchart.js
 *
 * <mj-gantt-chart> -- Gantt chart with task bars, dependency arrows,
 * percent-complete fills, milestone diamonds, and phase bands.
 *
 * Accessible data table always present alongside the SVG.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { formatDate, formatNumber } from "../core/intl.js";

const ROW_H = 40;
const LABEL_W = 260;
const AXIS_H = 40;
const DIAMOND_R = 8;

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
.toolbar { display: flex; align-items: center; gap: var(--mj-space-2); padding: var(--mj-space-2) var(--mj-space-3); border-bottom: 1px solid var(--mj-border); flex-wrap: wrap; }
.toolbar button { font: inherit; font-size: var(--mj-font-size-xs); background: var(--mj-surface); border: 1px solid var(--mj-border-strong); border-radius: var(--mj-radius-sm); padding: 2px var(--mj-space-2); cursor: pointer; color: var(--mj-text); }
.toolbar button:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: var(--mj-focus-ring-offset); }
.chart-area { flex: 1; overflow: auto; position: relative; }
svg { display: block; }
.task-label { font-size: var(--mj-font-size-xs); fill: var(--mj-text); dominant-baseline: middle; }
.axis-tick { font-size: var(--mj-font-size-xs); fill: var(--mj-text-muted); }
.task-bar-el { cursor: pointer; }
.task-bar-el:focus { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); }
.detail-panel { position: absolute; top: var(--mj-space-3); right: var(--mj-space-3); min-width: 220px; background: var(--mj-surface-raised); border: 1px solid var(--mj-border-strong); border-radius: var(--mj-radius-md); padding: var(--mj-space-3); box-shadow: var(--mj-elevation-2); z-index: 10; }
.detail-panel h3 { margin: 0 0 var(--mj-space-2); font-size: var(--mj-font-size-sm); }
.detail-panel .close-btn { float: right; background: none; border: none; cursor: pointer; font-size: 1rem; color: var(--mj-text-muted); }
.a11y-table-wrap { padding: var(--mj-space-3); }
.a11y-table-wrap table { border-collapse: collapse; width: 100%; font-size: var(--mj-font-size-sm); }
.a11y-table-wrap th, .a11y-table-wrap td { border: 1px solid var(--mj-border); padding: var(--mj-space-1) var(--mj-space-2); text-align: left; }
[hidden] { display: none !important; }
`;

export class MjGanttChart extends MjElement {
  static tagName = "mj-gantt-chart";
  static styles = STYLES;
  static watched = ["scale", "start-date", "end-date", "today-marker", "show-dependencies", "show-percent", "density"];

  constructor() {
    super();
    this._data = null;
    this._selectedTask = null;
    this._collapsedGroups = new Set();
    this._showTable = false;
    this._tableId = nextId("mj-gc-table");
    this._detailId = nextId("mj-gc-detail");
  }

  render() {
    return `
      <div class="wrapper" part="wrapper">
        <div class="toolbar" part="toolbar">
          <button class="btn-toggle-table" aria-controls="${this._tableId}" aria-expanded="false">Show data table</button>
          <slot name="toolbar"></slot>
        </div>
        <div class="chart-area" part="chart-area">
          <svg part="svg" role="img" aria-label="Gantt chart" aria-hidden="true"></svg>
          <div class="detail-panel" part="task-detail" role="dialog" aria-modal="false" aria-labelledby="${this._detailId}" hidden>
            <button class="close-btn" aria-label="Close">&#x2715;</button>
            <h3 id="${this._detailId}">Task</h3>
            <div class="detail-content"></div>
            <slot name="task-detail"></slot>
          </div>
        </div>
        <div id="${this._tableId}" class="a11y-table-wrap" hidden>
          <table part="data-table">
            <caption>Gantt chart tasks</caption>
            <thead><tr><th>Task</th><th>Start</th><th>End</th><th>% Complete</th><th>Status</th></tr></thead>
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
    this.listen(this.$(".close-btn"), "click", this._closeDetail.bind(this));
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

  get selectedTask() {
    return this._selectedTask;
  }

  get collapsedGroups() {
    return this._collapsedGroups;
  }

  _onToggleTable() {
    this._showTable = !this._showTable;
    this._tableWrap.hidden = !this._showTable;
    this._toggleBtn.setAttribute("aria-expanded", String(this._showTable));
    return;
  }

  _closeDetail() {
    this._detailPanel.hidden = true;
    this._selectedTask = null;
    this.emit("mj-task-deselect", {});
    return;
  }

  _draw() {
    const d = this._data;
    if (d === null || d === undefined) {
      return;
    }
    const tasks = d.tasks || [];
    const markers = d.markers || [];
    const phases = d.phases || [];
    const deps = d.dependencies || [];

    if (tasks.length === 0) {
      return;
    }

    const allTimes = tasks.flatMap((t) => [new Date(t.start).getTime(), new Date(t.end).getTime()]).filter((t) => !isNaN(t));
    const startAttr = this.getAttribute("start-date");
    const endAttr = this.getAttribute("end-date");
    const tMin = startAttr !== null ? new Date(startAttr).getTime() : Math.min(...allTimes);
    const tMax = endAttr !== null ? new Date(endAttr).getTime() : Math.max(...allTimes);
    const tRange = tMax - tMin || 86400000;

    const containerW = (this._svg.parentElement && this._svg.parentElement.clientWidth) || 900;
    const chartW = containerW - LABEL_W - 16;
    const totalH = AXIS_H + tasks.length * ROW_H + 16;

    const tx = (ts) => LABEL_W + ((ts - tMin) / tRange) * chartW;

    let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${containerW}" height="${totalH}">`;
    svg += `<defs><marker id="dep-arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="var(--mj-text-muted)"/></marker></defs>`;

    phases.forEach((ph, i) => {
      const x1 = tx(new Date(ph.start).getTime());
      const x2 = tx(new Date(ph.end).getTime());
      const colors = ["#4d83f7","#15803d","#b45309","#b91c1c","#7c3aed","#0891b2"];
      svg += `<rect part="phase-band" x="${x1}" y="${AXIS_H}" width="${Math.max(0, x2 - x1)}" height="${tasks.length * ROW_H}" fill="${colors[i % colors.length]}" opacity="0.08" aria-hidden="true"/>`;
    });

    const tickCount = Math.min(10, Math.floor(chartW / 80));
    for (let i = 0; i <= tickCount; i = i + 1) {
      const t = tMin + (i / tickCount) * tRange;
      const x = tx(t);
      svg += `<line x1="${x}" y1="${AXIS_H - 6}" x2="${x}" y2="${totalH}" stroke="var(--mj-border)" stroke-width="1" aria-hidden="true"/>`;
      svg += `<text class="axis-tick" part="time-axis" x="${x}" y="${AXIS_H - 8}" text-anchor="middle">${formatDate(new Date(t), { month: "short", day: "numeric" })}</text>`;
    }

    svg += `<rect x="0" y="0" width="${LABEL_W}" height="${AXIS_H}" fill="var(--mj-bg)" aria-hidden="true"/>`;
    svg += `<text x="8" y="${AXIS_H - 10}" class="axis-tick" font-weight="500">Task</text>`;

    tasks.forEach((task, i) => {
      const y = AXIS_H + i * ROW_H;
      const midY = y + ROW_H / 2;
      const x1 = tx(new Date(task.start).getTime());
      const x2 = tx(new Date(task.end || task.start).getTime());
      const barW = Math.max(4, x2 - x1);
      const pct = task.percentComplete || 0;
      const fillW = barW * (pct / 100);
      const barLabel = `${task.name}: ${formatDate(new Date(task.start))} to ${formatDate(new Date(task.end))}, ${formatNumber(pct)}% complete`;

      svg += `<line x1="0" y1="${y + ROW_H}" x2="${containerW}" y2="${y + ROW_H}" stroke="var(--mj-border)" stroke-width="1" aria-hidden="true"/>`;
      svg += `<rect x="0" y="${y}" width="${LABEL_W}" height="${ROW_H}" fill="var(--mj-bg)" aria-hidden="true"/>`;
      svg += `<text class="task-label" part="task-list-panel" x="8" y="${midY}">${this._esc(task.name.length > 30 ? task.name.slice(0, 28) + "…" : task.name)}</text>`;

      svg += `<g class="task-bar-el" part="task-bar" tabindex="0" role="button" aria-label="${this._esc(barLabel)}" data-task-id="${this._esc(task.id || task.name)}">`;
      svg += `<rect x="${x1}" y="${y + 8}" width="${barW}" height="${ROW_H - 16}" rx="3" fill="var(--mj-accent)" opacity="0.5" part="task-bar"/>`;
      if (fillW > 0) {
        svg += `<rect x="${x1}" y="${y + 8}" width="${fillW}" height="${ROW_H - 16}" rx="3" fill="var(--mj-accent)" part="task-bar-fill"/>`;
      }
      svg += `</g>`;
    });

    if (this.getAttribute("show-dependencies") !== "false") {
      deps.forEach((dep) => {
        const fromIdx = tasks.findIndex((t) => (t.id || t.name) === dep.from);
        const toIdx = tasks.findIndex((t) => (t.id || t.name) === dep.to);
        if (fromIdx < 0 || toIdx < 0) {
          return;
        }
        const fromTask = tasks[fromIdx];
        const toTask = tasks[toIdx];
        const x1 = tx(new Date(fromTask.end || fromTask.start).getTime());
        const y1 = AXIS_H + fromIdx * ROW_H + ROW_H / 2;
        const x2 = tx(new Date(toTask.start).getTime());
        const y2 = AXIS_H + toIdx * ROW_H + ROW_H / 2;
        svg += `<path part="dependency-arrow" d="M${x1},${y1} C${x1 + 20},${y1} ${x2 - 20},${y2} ${x2},${y2}" stroke="var(--mj-text-muted)" stroke-width="1.5" fill="none" marker-end="url(#dep-arrow)" aria-hidden="true"/>`;
      });
    }

    markers.forEach((m) => {
      const mx = tx(new Date(m.date).getTime());
      const my = AXIS_H;
      svg += `<line part="milestone-marker" x1="${mx}" y1="${my}" x2="${mx}" y2="${totalH}" stroke="var(--mj-color-warning)" stroke-width="1.5" stroke-dasharray="5 3" aria-hidden="true"/>`;
      svg += `<polygon points="${mx - DIAMOND_R},${my + DIAMOND_R} ${mx},${my} ${mx + DIAMOND_R},${my + DIAMOND_R} ${mx},${my + DIAMOND_R * 2}" fill="var(--mj-color-warning)" aria-hidden="true"/>`;
      svg += `<text x="${mx + DIAMOND_R + 4}" y="${my + DIAMOND_R * 2}" font-size="10" fill="var(--mj-color-warning)">${this._esc(m.name)}</text>`;
    });

    if (this.getAttribute("today-marker") !== "false") {
      const todayX = tx(Date.now());
      if (todayX >= LABEL_W && todayX <= containerW) {
        svg += `<line part="today-marker" x1="${todayX}" y1="${AXIS_H}" x2="${todayX}" y2="${totalH}" stroke="var(--mj-color-danger)" stroke-width="2" stroke-dasharray="6 3" aria-hidden="true"/>`;
        svg += `<text x="${todayX + 4}" y="${AXIS_H + 12}" font-size="10" fill="var(--mj-color-danger)">Today</text>`;
      }
    }

    svg += `</svg>`;
    const area = this.$(".chart-area");
    if (area !== null) {
      const oldSvg = area.querySelector("svg");
      if (oldSvg !== null) {
        oldSvg.outerHTML = svg;
      }
    }
    const newSvg = this.shadowRoot.querySelector("svg");
    if (newSvg !== null) {
      this._svg = newSvg;
      this.listen(newSvg, "click", this._onSvgClick.bind(this));
      this.listen(newSvg, "keydown", this._onSvgKeydown.bind(this));
    }

    this._buildTable(tasks);

    const wrapper = this.$(".wrapper");
    if (wrapper !== null) {
      wrapper.setAttribute("aria-label", `Gantt chart: ${tasks.length} tasks`);
    }
    return;
  }

  _buildTable(tasks) {
    if (this._tableBody === null || this._tableBody === undefined) {
      return;
    }
    const rows = tasks.map((t) => {
      return `<tr><td>${this._esc(t.name)}</td><td>${formatDate(new Date(t.start))}</td><td>${formatDate(new Date(t.end))}</td><td>${formatNumber(t.percentComplete || 0)}%</td><td>${this._esc(t.status || "")}</td></tr>`;
    });
    this._tableBody.innerHTML = rows.join("");
    return;
  }

  _onSvgClick(event) {
    const node = event.target.closest("[data-task-id]");
    if (node !== null) {
      const id = node.getAttribute("data-task-id");
      const tasks = (this._data && this._data.tasks) || [];
      const task = tasks.find((t) => (t.id || t.name) === id);
      if (task !== undefined) {
        this._selectedTask = task;
        const h3 = this._detailPanel.querySelector("h3");
        if (h3 !== null) {
          h3.textContent = task.name;
        }
        this._detailContent.innerHTML = `<p><strong>Start:</strong> ${formatDate(new Date(task.start))}</p><p><strong>End:</strong> ${formatDate(new Date(task.end))}</p><p><strong>% Complete:</strong> ${formatNumber(task.percentComplete || 0)}%</p><p><strong>Status:</strong> ${this._esc(task.status || "")}</p>`;
        this._detailPanel.hidden = false;
        this.emit("mj-task-select", { task });
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
