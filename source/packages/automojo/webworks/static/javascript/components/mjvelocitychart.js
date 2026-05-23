/*
 * mjvelocitychart.js
 *
 * <mj-velocity-chart> -- grouped bar chart of committed vs completed work
 * per sprint, with a rolling-average line overlay.
 *
 * SVG is aria-hidden; accessible data table always present.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { formatNumber } from "../core/intl.js";

const PAD_L = 52;
const PAD_R = 16;
const PAD_T = 16;
const PAD_B = 50;
const BAR_GAP = 4;

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
.header { display: flex; align-items: center; gap: var(--mj-space-2); padding: var(--mj-space-2) var(--mj-space-3); border-bottom: 1px solid var(--mj-border); flex-wrap: wrap; }
.toggle-btn { font: inherit; font-size: var(--mj-font-size-xs); background: var(--mj-surface); border: 1px solid var(--mj-border-strong); border-radius: var(--mj-radius-sm); padding: 2px var(--mj-space-2); cursor: pointer; color: var(--mj-text); }
.toggle-btn:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: var(--mj-focus-ring-offset); }
.svg-wrap { overflow-x: auto; }
svg { display: block; }
.bar-group-el { cursor: pointer; }
.bar-group-el:focus { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); }
.legend { display: flex; flex-wrap: wrap; gap: var(--mj-space-3); padding: var(--mj-space-2) var(--mj-space-3); border-top: 1px solid var(--mj-border); font-size: var(--mj-font-size-xs); }
.legend-item { display: flex; align-items: center; gap: var(--mj-space-1); }
.swatch { width: 16px; height: 10px; display: inline-block; border-radius: 2px; }
.a11y-table-wrap { padding: var(--mj-space-3); }
.a11y-table-wrap table { border-collapse: collapse; width: 100%; font-size: var(--mj-font-size-sm); }
.a11y-table-wrap th, .a11y-table-wrap td { border: 1px solid var(--mj-border); padding: var(--mj-space-1) var(--mj-space-2); text-align: left; }
[hidden] { display: none !important; }
`;

export class MjVelocityChart extends MjElement {
  static tagName = "mj-velocity-chart";
  static styles = STYLES;
  static watched = ["unit", "bar-mode", "rolling-window", "show-average", "show-committed"];

  constructor() {
    super();
    this._data = null;
    this._selectedSprint = null;
    this._showTable = false;
    this._tableId = nextId("mj-vc-table");
  }

  render() {
    return `
      <div class="wrapper" part="wrapper" role="img" aria-label="Velocity chart">
        <div class="header">
          <strong style="font-size:var(--mj-font-size-sm)">Velocity Chart</strong>
          <span style="flex:1"></span>
          <button class="toggle-btn" aria-controls="${this._tableId}" aria-expanded="false">Show data table</button>
        </div>
        <div class="svg-wrap">
          <svg part="svg" aria-hidden="true"></svg>
        </div>
        <div class="legend" part="legend">
          <span class="legend-item" part="legend-committed"><span class="swatch" style="background:var(--mj-color-accent-200)"></span> Committed</span>
          <span class="legend-item" part="legend-completed"><span class="swatch" style="background:var(--mj-accent)"></span> Completed</span>
          <span class="legend-item" part="legend-average"><span class="swatch" style="background:var(--mj-color-warning);height:3px;margin-top:4px;"></span> Rolling Avg</span>
        </div>
        <div id="${this._tableId}" class="a11y-table-wrap" hidden>
          <table part="data-table">
            <caption>Sprint velocity data</caption>
            <thead><tr><th>Sprint</th><th>Committed</th><th>Completed</th><th>Difference</th><th>Rolling Average</th></tr></thead>
            <tbody class="table-body"></tbody>
          </table>
        </div>
        <slot hidden></slot>
      </div>`;
  }

  afterRender() {
    this._svg = this.$("svg");
    this._tableBody = this.$(".table-body");
    this._tableWrap = this.$("#" + this._tableId);
    this._toggleBtn = this.$(".toggle-btn");
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

  get selectedSprint() {
    return this._selectedSprint;
  }

  get rollingAverage() {
    const sprints = (this._data && this._data.sprints) || [];
    const window = parseInt(this.getAttribute("rolling-window") || "3", 10);
    return this._computeRolling(sprints, window);
  }

  _computeRolling(sprints, window) {
    const avgs = [];
    for (let i = 0; i < sprints.length; i = i + 1) {
      const slice = sprints.slice(Math.max(0, i - window + 1), i + 1);
      const avg = slice.reduce((sum, s) => sum + (s.completed || 0), 0) / slice.length;
      avgs.push(avg);
    }
    return avgs;
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
    const sprints = d.sprints || [];
    if (sprints.length === 0) {
      return;
    }

    const unit = this.getAttribute("unit") || "points";
    const barMode = this.getAttribute("bar-mode") || "grouped";
    const rollingWindow = parseInt(this.getAttribute("rolling-window") || "3", 10);
    const showAverage = this.getAttribute("show-average") !== "false";
    const showCommitted = this.getAttribute("show-committed") !== "false";
    const rollingAvgs = this._computeRolling(sprints, rollingWindow);

    const maxVal = sprints.reduce((m, s) => Math.max(m, s.committed || 0, s.completed || 0), 0) * 1.15 || 10;

    const containerW = (this._svg.parentElement && this._svg.parentElement.clientWidth) || 700;
    const svgH = 300;
    const chartW = containerW - PAD_L - PAD_R;
    const chartH = svgH - PAD_T - PAD_B;

    const groupW = chartW / sprints.length;
    const singleBarW = barMode === "grouped" ? (groupW - BAR_GAP * 3) / 2 : groupW - BAR_GAP * 2;
    const ty = (val) => PAD_T + (1 - val / maxVal) * chartH;
    const barBase = PAD_T + chartH;

    let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${containerW}" height="${svgH}">`;

    for (let i = 0; i <= 4; i = i + 1) {
      const val = (i / 4) * maxVal;
      const y = ty(val);
      svg += `<line x1="${PAD_L}" y1="${y}" x2="${containerW - PAD_R}" y2="${y}" stroke="var(--mj-border)" stroke-width="1" aria-hidden="true"/>`;
      svg += `<text x="${PAD_L - 6}" y="${y + 4}" text-anchor="end" font-size="10" fill="var(--mj-text-muted)">${formatNumber(Math.round(val))}</text>`;
    }

    svg += `<line part="value-axis" x1="${PAD_L}" y1="${PAD_T}" x2="${PAD_L}" y2="${barBase}" stroke="var(--mj-border-strong)" stroke-width="1.5" aria-hidden="true"/>`;
    svg += `<line part="sprint-axis" x1="${PAD_L}" y1="${barBase}" x2="${containerW - PAD_R}" y2="${barBase}" stroke="var(--mj-border-strong)" stroke-width="1.5" aria-hidden="true"/>`;

    const avgPts = [];

    sprints.forEach((sprint, i) => {
      const gx = PAD_L + i * groupW;
      const completed = sprint.completed || 0;
      const committed = sprint.committed || 0;
      const diff = completed - committed;
      const statusLabel = diff < -committed * 0.2 ? "Under-delivered" : diff > 0 ? "Exceeded" : "On target";
      const ariaLabel = `Sprint ${this._esc(sprint.name || String(i + 1))}: committed ${formatNumber(committed)}, completed ${formatNumber(completed)}, ${statusLabel}`;

      svg += `<g class="bar-group-el" part="bar-group" tabindex="0" role="button" aria-label="${ariaLabel}" data-sprint-idx="${i}">`;

      if (barMode === "grouped") {
        if (showCommitted && committed > 0) {
          const bx = gx + BAR_GAP;
          svg += `<rect part="committed-bar" x="${bx}" y="${ty(committed)}" width="${singleBarW}" height="${barBase - ty(committed)}" rx="3" fill="var(--mj-color-accent-200)" aria-hidden="true"/>`;
        }
        const bx2 = gx + BAR_GAP * 2 + singleBarW;
        svg += `<rect part="completed-bar" x="${bx2}" y="${ty(completed)}" width="${singleBarW}" height="${barBase - ty(completed)}" rx="3" fill="var(--mj-accent)" aria-hidden="true"/>`;
      } else {
        if (showCommitted && committed > 0) {
          svg += `<rect part="committed-bar" x="${gx + BAR_GAP}" y="${ty(committed)}" width="${singleBarW}" height="${barBase - ty(committed)}" rx="3" fill="var(--mj-color-accent-200)" aria-hidden="true"/>`;
        }
        svg += `<rect part="completed-bar" x="${gx + BAR_GAP}" y="${ty(completed)}" width="${singleBarW}" height="${barBase - ty(completed)}" rx="3" fill="var(--mj-accent)" aria-hidden="true"/>`;
      }

      if (diff < -committed * 0.2) {
        svg += `<text x="${gx + groupW / 2}" y="${ty(completed) - 4}" text-anchor="middle" font-size="9" fill="var(--mj-color-danger)">Under-delivered</text>`;
      } else if (diff > 0) {
        svg += `<text x="${gx + groupW / 2}" y="${ty(completed) - 4}" text-anchor="middle" font-size="9" fill="var(--mj-color-success)">Exceeded</text>`;
      }

      svg += `</g>`;

      const avgX = gx + groupW / 2;
      const avgY = ty(rollingAvgs[i] || 0);
      avgPts.push(`${avgX},${avgY}`);

      svg += `<text x="${gx + groupW / 2}" y="${barBase + 16}" text-anchor="middle" font-size="10" fill="var(--mj-text-muted)">${this._esc((sprint.name || `S${i + 1}`).slice(0, 8))}</text>`;
    });

    if (showAverage && avgPts.length > 1) {
      svg += `<polyline part="average-line" points="${avgPts.join(" ")}" stroke="var(--mj-color-warning)" stroke-width="2" fill="none" aria-hidden="true"/>`;
      avgPts.forEach((pt) => {
        const parts = pt.split(",");
        svg += `<circle cx="${parts[0]}" cy="${parts[1]}" r="3" fill="var(--mj-color-warning)" aria-hidden="true"/>`;
      });
    }

    svg += `</svg>`;

    const svgWrap = this.$(".svg-wrap");
    if (svgWrap !== null) {
      const oldSvg = svgWrap.querySelector("svg");
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

    this._buildTable(sprints, rollingAvgs);

    const wrapper = this.$(".wrapper");
    if (wrapper !== null) {
      wrapper.setAttribute("aria-label", `Velocity chart: ${sprints.length} sprints, unit: ${unit}, rolling window: ${rollingWindow}`);
    }
    return;
  }

  _buildTable(sprints, rollingAvgs) {
    if (this._tableBody === null || this._tableBody === undefined) {
      return;
    }
    const rows = sprints.map((s, i) => {
      const diff = (s.completed || 0) - (s.committed || 0);
      return `<tr><td>${this._esc(s.name || String(i + 1))}</td><td>${formatNumber(s.committed || 0)}</td><td>${formatNumber(s.completed || 0)}</td><td>${diff >= 0 ? "+" : ""}${formatNumber(diff)}</td><td>${formatNumber(Math.round(rollingAvgs[i] || 0))}</td></tr>`;
    });
    this._tableBody.innerHTML = rows.join("");
    return;
  }

  _onSvgClick(event) {
    const el = event.target.closest("[data-sprint-idx]");
    if (el !== null) {
      const idx = parseInt(el.getAttribute("data-sprint-idx"), 10);
      const sprints = (this._data && this._data.sprints) || [];
      const sprint = sprints[idx];
      if (sprint !== undefined) {
        this._selectedSprint = sprint;
        this.emit("mj-sprint-select", { sprint });
      }
    }
    return;
  }

  _onSvgKeydown(event) {
    if (event.key === "Enter" || event.key === " ") {
      this._onSvgClick(event);
    }
    if (event.key === "Escape") {
      this._selectedSprint = null;
      this.emit("mj-sprint-deselect", {});
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
