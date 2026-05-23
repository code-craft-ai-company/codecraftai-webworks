/*
 * mjpipelinechart.js
 *
 * <mj-pipeline-chart> -- CI/CD pipeline stage-flow diagram.
 *
 * Renders stage nodes, gate diamonds, directed edges, and a status legend.
 * Accessible <ol> always present alongside the SVG (SVG is aria-hidden).
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { formatDate } from "../core/intl.js";
import { announce } from "../core/announcer.js";

const STAGE_W = 140;
const STAGE_H = 64;
const STAGE_GAP = 48;
const GATE_SIZE = 32;

const STATUS_ICONS = {
  pending:   "○",
  running:   "◎",
  passed:    "✓",
  failed:    "✗",
  cancelled: "⊘",
  skipped:   "→",
};

const STATUS_COLORS = {
  pending:   "var(--mj-text-muted)",
  running:   "var(--mj-color-info)",
  passed:    "var(--mj-color-success)",
  failed:    "var(--mj-color-danger)",
  cancelled: "var(--mj-text-muted)",
  skipped:   "var(--mj-text-muted)",
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
.chart-scroll { overflow-x: auto; overflow-y: hidden; }
svg { display: block; }
.stage-box { cursor: pointer; }
.stage-box:focus { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); }
.log-panel { padding: var(--mj-space-3); background: var(--mj-bg-subtle); border-top: 1px solid var(--mj-border); font-family: var(--mj-font-mono); font-size: var(--mj-font-size-xs); max-height: 200px; overflow-y: auto; }
.legend { display: flex; flex-wrap: wrap; gap: var(--mj-space-3); padding: var(--mj-space-2) var(--mj-space-3); border-top: 1px solid var(--mj-border); font-size: var(--mj-font-size-xs); }
.legend-item { display: flex; align-items: center; gap: var(--mj-space-1); }
.a11y-list-wrap { padding: var(--mj-space-3); }
.a11y-list-wrap ol { margin: 0; padding-left: var(--mj-space-5); font-size: var(--mj-font-size-sm); }
[hidden] { display: none !important; }
.toggle-btn { font: inherit; font-size: var(--mj-font-size-xs); background: var(--mj-surface); border: 1px solid var(--mj-border-strong); border-radius: var(--mj-radius-sm); padding: 2px var(--mj-space-2); cursor: pointer; color: var(--mj-text); margin: var(--mj-space-2) var(--mj-space-3); }
.toggle-btn:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: var(--mj-focus-ring-offset); }
`;

export class MjPipelineChart extends MjElement {
  static tagName = "mj-pipeline-chart";
  static styles = STYLES;
  static watched = ["orientation", "density", "readonly", "live"];

  constructor() {
    super();
    this._data = null;
    this._selectedStage = null;
    this._showList = false;
    this._listId = nextId("mj-pc-list");
  }

  render() {
    return `
      <div class="wrapper" part="wrapper" role="img" aria-label="CI pipeline">
        <button class="toggle-btn" aria-controls="${this._listId}" aria-expanded="false">Show accessible list</button>
        <div class="chart-scroll"><svg part="svg" aria-hidden="true"></svg></div>
        <div class="log-panel" part="log-panel" role="log" aria-label="Stage logs" hidden></div>
        <div class="legend" part="status-legend" aria-label="Status legend"></div>
        <div id="${this._listId}" class="a11y-list-wrap" hidden>
          <ol part="a11y-list"></ol>
        </div>
        <slot hidden></slot>
      </div>`;
  }

  afterRender() {
    this._svg = this.$("svg");
    this._logPanel = this.$(".log-panel");
    this._legend = this.$(".legend");
    this._listWrap = this.$("#" + this._listId);
    this._listEl = this.$("ol");
    this._toggleBtn = this.$(".toggle-btn");
    this.listen(this._toggleBtn, "click", this._onToggleList.bind(this));
    this._buildLegend();
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

  get selectedStage() {
    return this._selectedStage;
  }

  get overallStatus() {
    const d = this._data;
    if (d === null || d === undefined) {
      return "pending";
    }
    const stages = d.stages || [];
    if (stages.some((s) => s.status === "failed")) {
      return "failed";
    }
    if (stages.some((s) => s.status === "running")) {
      return "running";
    }
    if (stages.every((s) => s.status === "passed")) {
      return "passed";
    }
    return "pending";
  }

  _onToggleList() {
    this._showList = !this._showList;
    this._listWrap.hidden = !this._showList;
    this._toggleBtn.setAttribute("aria-expanded", String(this._showList));
    return;
  }

  _buildLegend() {
    const items = Object.keys(STATUS_ICONS).map((s) => {
      return `<span class="legend-item" part="legend-item"><span aria-hidden="true" style="color:${STATUS_COLORS[s]}">${STATUS_ICONS[s]}</span> <span>${s}</span></span>`;
    });
    this._legend.innerHTML = items.join("");
    return;
  }

  _draw() {
    const d = this._data;
    if (d === null || d === undefined) {
      return;
    }
    const stages = d.stages || [];
    const gates = d.gates || [];
    const edges = d.edges || [];

    const totalW = stages.length * (STAGE_W + STAGE_GAP) + STAGE_GAP;
    const totalH = STAGE_H + GATE_SIZE + 80;

    let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${totalW}" height="${totalH}" viewBox="0 0 ${totalW} ${totalH}">`;

    const stageX = (i) => STAGE_GAP + i * (STAGE_W + STAGE_GAP);
    const stageCX = (i) => stageX(i) + STAGE_W / 2;
    const stageCY = GATE_SIZE + 8 + STAGE_H / 2;

    edges.forEach((e) => {
      const fromIdx = stages.findIndex((s) => s.id === e.from);
      const toIdx = stages.findIndex((s) => s.id === e.to);
      if (fromIdx < 0 || toIdx < 0) {
        return;
      }
      const x1 = stageX(fromIdx) + STAGE_W;
      const x2 = stageX(toIdx);
      const y = stageCY;
      svg += `<line part="edge" x1="${x1}" y1="${y}" x2="${x2}" y2="${y}" stroke="var(--mj-border-strong)" stroke-width="2" marker-end="url(#arrow)" aria-hidden="true"/>`;
    });

    svg += `<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="var(--mj-text-muted)"/></marker></defs>`;

    stages.forEach((s, i) => {
      const x = stageX(i);
      const y = GATE_SIZE + 8;
      const color = STATUS_COLORS[s.status] || STATUS_COLORS.pending;
      const icon = STATUS_ICONS[s.status] || "○";
      const label = `${this._esc(s.name)} stage, status: ${s.status || "pending"}`;
      svg += `<g class="stage-box" part="stage-node" tabindex="0" role="button" aria-label="${label}" aria-expanded="false" data-stage-id="${this._esc(s.id || s.name)}">`;
      svg += `<rect x="${x}" y="${y}" width="${STAGE_W}" height="${STAGE_H}" rx="6" ry="6" fill="var(--mj-surface)" stroke="${color}" stroke-width="2"/>`;
      svg += `<text x="${x + STAGE_W / 2}" y="${y + 22}" text-anchor="middle" font-size="12" fill="var(--mj-text)" font-weight="500">${this._esc(s.name)}</text>`;
      svg += `<text x="${x + 16}" y="${y + 42}" font-size="14" fill="${color}" aria-hidden="true">${icon}</text>`;
      svg += `<text x="${x + 34}" y="${y + 44}" font-size="11" fill="${color}">${s.status || "pending"}</text>`;
      svg += `</g>`;
    });

    gates.forEach((g, i) => {
      const fromIdx = stages.findIndex((s) => s.id === g.fromStage);
      const afterX = fromIdx >= 0 ? stageX(fromIdx) + STAGE_W + STAGE_GAP / 2 - GATE_SIZE / 2 : i * (STAGE_W + STAGE_GAP);
      const cy = stageCY;
      const hs = GATE_SIZE / 2;
      svg += `<g role="group" aria-label="${this._esc(g.name || "gate")} approval gate, status: ${g.status || "pending"}">`;
      svg += `<polygon part="gate-node" points="${afterX + hs},${cy - hs} ${afterX + GATE_SIZE},${cy} ${afterX + hs},${cy + hs} ${afterX},${cy}" fill="var(--mj-bg-muted)" stroke="var(--mj-color-warning)" stroke-width="2"/>`;
      svg += `</g>`;
    });

    svg += `</svg>`;

    this._svg.outerHTML = svg;
    const newSvg = this.shadowRoot.querySelector("svg");
    if (newSvg !== null) {
      this._svg = newSvg;
      this.listen(newSvg, "click", this._onSvgClick.bind(this));
      this.listen(newSvg, "keydown", this._onSvgKeydown.bind(this));
    }

    this._buildList(stages);

    const wrapper = this.$(".wrapper");
    if (wrapper !== null) {
      wrapper.setAttribute("aria-label", `CI pipeline: ${stages.length} stages, status: ${this.overallStatus}`);
    }
    return;
  }

  _buildList(stages) {
    if (this._listEl === null || this._listEl === undefined) {
      return;
    }
    const items = stages.map((s) => `<li>${this._esc(s.name)}: ${s.status || "pending"}${s.duration ? ", " + s.duration : ""}</li>`);
    this._listEl.innerHTML = items.join("");
    return;
  }

  _onSvgClick(event) {
    const node = event.target.closest("[data-stage-id]");
    if (node !== null) {
      const id = node.getAttribute("data-stage-id");
      const stages = (this._data && this._data.stages) || [];
      const stage = stages.find((s) => (s.id || s.name) === id);
      if (stage !== undefined) {
        this._selectedStage = stage;
        this.emit("mj-stage-select", { stage });
        if (stage.logs !== undefined && stage.logs !== null) {
          this._logPanel.textContent = stage.logs;
          this._logPanel.hidden = false;
          node.setAttribute("aria-expanded", "true");
        }
      }
    }
    return;
  }

  _onSvgKeydown(event) {
    if (event.key === "Enter" || event.key === " ") {
      this._onSvgClick(event);
    }
    if (event.key === "Escape") {
      this._logPanel.hidden = true;
      this._selectedStage = null;
      this.emit("mj-stage-deselect", {});
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
