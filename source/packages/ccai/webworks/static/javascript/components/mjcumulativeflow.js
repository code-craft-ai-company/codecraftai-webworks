/*
 * mjcumulativeflow.js
 *
 * <mj-cumulative-flow> -- stacked area chart of work items per workflow state
 * over time, with WIP and lead-time callouts.
 *
 * SVG is aria-hidden; accessible data table always present.
 * Color is supplemented by fill patterns in <defs>.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { formatDate, formatNumber } from "../core/intl.js";

const PAD_L = 52;
const PAD_R = 16;
const PAD_T = 16;
const PAD_B = 40;

const BAND_COLORS = ["#4d83f7","#15803d","#b45309","#b91c1c","#7c3aed","#0891b2","#c2410c","#4f46e5"];
const PATTERN_STYLES = ["none","lines","dots","cross","diagonal","zigzag","grid","waves"];

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
.legend { display: flex; flex-wrap: wrap; gap: var(--mj-space-3); padding: var(--mj-space-2) var(--mj-space-3); border-top: 1px solid var(--mj-border); font-size: var(--mj-font-size-xs); }
.legend-btn { display: flex; align-items: center; gap: var(--mj-space-1); background: none; border: 1px solid var(--mj-border); border-radius: var(--mj-radius-sm); padding: 2px var(--mj-space-2); cursor: pointer; font: inherit; font-size: var(--mj-font-size-xs); color: var(--mj-text); }
.legend-btn:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: var(--mj-focus-ring-offset); }
.legend-btn[aria-pressed="false"] { opacity: 0.4; text-decoration: line-through; }
.swatch { width: 14px; height: 14px; display: inline-block; border-radius: 2px; }
.a11y-table-wrap { padding: var(--mj-space-3); }
.a11y-table-wrap table { border-collapse: collapse; width: 100%; font-size: var(--mj-font-size-sm); }
.a11y-table-wrap th, .a11y-table-wrap td { border: 1px solid var(--mj-border); padding: var(--mj-space-1) var(--mj-space-2); text-align: left; }
[hidden] { display: none !important; }
`;

export class MjCumulativeFlow extends MjElement {
  static tagName = "mj-cumulative-flow";
  static styles = STYLES;
  static watched = ["type", "normalized", "start-date", "end-date", "today-marker"];

  constructor() {
    super();
    this._data = null;
    this._selectedDate = null;
    this._hiddenStates = new Set();
    this._showTable = false;
    this._tableId = nextId("mj-cfd-table");
  }

  render() {
    return `
      <div class="wrapper" part="wrapper">
        <div class="header">
          <strong style="font-size:var(--mj-font-size-sm)">Cumulative Flow Diagram</strong>
          <span style="flex:1"></span>
          <button class="toggle-btn" aria-controls="${this._tableId}" aria-expanded="false">Show data table</button>
        </div>
        <div class="svg-wrap">
          <svg part="svg" role="img" aria-label="Cumulative flow diagram" aria-hidden="true"></svg>
        </div>
        <div class="legend" part="legend" role="group" aria-label="Workflow states"></div>
        <div id="${this._tableId}" class="a11y-table-wrap" hidden>
          <table part="data-table"><thead><tr class="thead-row"></tr></thead><tbody class="table-body"></tbody></table>
        </div>
        <slot hidden></slot>
      </div>`;
  }

  afterRender() {
    this._svg = this.$("svg");
    this._legend = this.$(".legend");
    this._tableBody = this.$(".table-body");
    this._theadRow = this.$(".thead-row");
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

  get selectedDate() {
    return this._selectedDate;
  }

  get hiddenStates() {
    return this._hiddenStates;
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
    const states = (d.states || []).filter((s) => !this._hiddenStates.has(s.id || s.name));
    const allStates = d.states || [];
    const dailySeries = d.dailySeries || [];

    if (dailySeries.length === 0 || states.length === 0) {
      return;
    }

    const containerW = (this._svg.parentElement && this._svg.parentElement.clientWidth) || 700;
    const svgH = 300;
    const chartW = containerW - PAD_L - PAD_R;
    const chartH = svgH - PAD_T - PAD_B;
    const normalized = this.hasAttribute("normalized") && this.getAttribute("normalized") !== "false";

    const allTimes = dailySeries.map((row) => new Date(row.date).getTime()).filter((t) => !isNaN(t));
    const tMin = allTimes.length > 0 ? Math.min(...allTimes) : Date.now();
    const tMax = allTimes.length > 0 ? Math.max(...allTimes) : Date.now() + 86400000 * 14;
    const tRange = tMax - tMin || 86400000;

    const maxTotal = dailySeries.reduce((maxV, row) => {
      const total = states.reduce((sum, s) => sum + (row[s.id || s.name] || 0), 0);
      return Math.max(maxV, total);
    }, 0) * 1.1 || 10;

    const tx = (ts) => PAD_L + ((ts - tMin) / tRange) * chartW;
    const ty = (val) => PAD_T + (1 - val / (normalized ? 100 : maxTotal)) * chartH;

    let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${containerW}" height="${svgH}">`;
    svg += `<defs>`;
    BAND_COLORS.forEach((c, i) => {
      svg += `<pattern id="cfd-pat-${i}" patternUnits="userSpaceOnUse" width="8" height="8">`;
      svg += `<rect width="8" height="8" fill="${c}" opacity="0.7"/>`;
      if (i % 2 === 1) {
        svg += `<line x1="0" y1="8" x2="8" y2="0" stroke="rgba(255,255,255,0.35)" stroke-width="1"/>`;
      } else if (i % 3 === 2) {
        svg += `<circle cx="4" cy="4" r="1.5" fill="rgba(255,255,255,0.4)"/>`;
      }
      svg += `</pattern>`;
    });
    svg += `</defs>`;

    for (let i = 0; i <= 4; i = i + 1) {
      const val = (i / 4) * (normalized ? 100 : maxTotal);
      const y = ty(val);
      svg += `<line x1="${PAD_L}" y1="${y}" x2="${containerW - PAD_R}" y2="${y}" stroke="var(--mj-border)" stroke-width="1" aria-hidden="true"/>`;
      svg += `<text x="${PAD_L - 6}" y="${y + 4}" text-anchor="end" font-size="10" fill="var(--mj-text-muted)">${formatNumber(Math.round(val))}${normalized ? "%" : ""}</text>`;
    }

    const tickCount = Math.min(7, dailySeries.length);
    for (let i = 0; i <= tickCount; i = i + 1) {
      const t = tMin + (i / tickCount) * tRange;
      svg += `<text x="${tx(t)}" y="${svgH - 8}" text-anchor="middle" font-size="10" fill="var(--mj-text-muted)">${formatDate(new Date(t), { month: "short", day: "numeric" })}</text>`;
    }

    svg += `<line part="value-axis" x1="${PAD_L}" y1="${PAD_T}" x2="${PAD_L}" y2="${PAD_T + chartH}" stroke="var(--mj-border-strong)" stroke-width="1.5" aria-hidden="true"/>`;
    svg += `<line part="time-axis" x1="${PAD_L}" y1="${PAD_T + chartH}" x2="${containerW - PAD_R}" y2="${PAD_T + chartH}" stroke="var(--mj-border-strong)" stroke-width="1.5" aria-hidden="true"/>`;

    for (let si = 0; si < states.length; si = si + 1) {
      const statesBelow = states.slice(0, si);
      const statesUpTo = states.slice(0, si + 1);
      const colorIdx = si % BAND_COLORS.length;

      const topPoints = dailySeries.map((row) => {
        const total = row.total || states.reduce((s, st) => s + (row[st.id || st.name] || 0), 0) || maxTotal;
        const cumTop = statesUpTo.reduce((sum, s) => sum + (row[s.id || s.name] || 0), 0);
        const val = normalized ? (cumTop / total) * 100 : cumTop;
        return `${tx(new Date(row.date).getTime())},${ty(val)}`;
      });
      const botPoints = dailySeries.map((row) => {
        const total = row.total || states.reduce((s, st) => s + (row[st.id || st.name] || 0), 0) || maxTotal;
        const cumBot = statesBelow.reduce((sum, s) => sum + (row[s.id || s.name] || 0), 0);
        const val = normalized ? (cumBot / total) * 100 : cumBot;
        return `${tx(new Date(row.date).getTime())},${ty(val)}`;
      }).reverse();

      const allPts = [...topPoints, ...botPoints].join(" ");
      svg += `<polygon part="state-band" points="${allPts}" fill="url(#cfd-pat-${colorIdx})" stroke="${BAND_COLORS[colorIdx]}" stroke-width="1" opacity="0.85" aria-hidden="true"/>`;
    }

    if (this.getAttribute("today-marker") !== "false") {
      const todayX = tx(Date.now());
      if (todayX >= PAD_L && todayX <= containerW - PAD_R) {
        svg += `<line part="today-marker" x1="${todayX}" y1="${PAD_T}" x2="${todayX}" y2="${PAD_T + chartH}" stroke="var(--mj-color-danger)" stroke-width="1.5" stroke-dasharray="6 3" aria-hidden="true"/>`;
      }
    }

    svg += `</svg>`;

    const svgWrap = this.$(".svg-wrap");
    if (svgWrap !== null) {
      const oldSvg = svgWrap.querySelector("svg");
      if (oldSvg !== null) {
        oldSvg.outerHTML = svg;
      }
    }

    this._buildLegend(allStates);
    this._buildTable(dailySeries, allStates);

    const wrapper = this.$(".wrapper");
    if (wrapper !== null) {
      wrapper.setAttribute("aria-label", `Cumulative flow diagram: ${allStates.length} states`);
    }
    return;
  }

  _buildLegend(states) {
    if (this._legend === null || this._legend === undefined) {
      return;
    }
    const items = states.map((s, i) => {
      const id = s.id || s.name;
      const hidden = this._hiddenStates.has(id);
      const color = BAND_COLORS[i % BAND_COLORS.length];
      return `<button class="legend-btn" part="legend-item" data-state-id="${this._esc(id)}" aria-pressed="${hidden ? "false" : "true"}" aria-label="${this._esc(id)}, currently ${hidden ? "hidden" : "visible"}"><span class="swatch" style="background:${color}"></span>${this._esc(s.name || id)}</button>`;
    });
    this._legend.innerHTML = items.join("");
    this._legend.querySelectorAll(".legend-btn").forEach((btn) => {
      this.listen(btn, "click", (e) => {
        const stateId = e.currentTarget.getAttribute("data-state-id");
        if (this._hiddenStates.has(stateId)) {
          this._hiddenStates.delete(stateId);
        } else {
          this._hiddenStates.add(stateId);
        }
        this.emit("mj-state-toggle", { stateId, visible: !this._hiddenStates.has(stateId) });
        this._draw();
      });
    });
    return;
  }

  _buildTable(dailySeries, states) {
    if (this._tableBody === null || this._tableBody === undefined) {
      return;
    }
    if (this._theadRow !== null) {
      const headers = ["Date", ...states.map((s) => s.name || s.id)];
      this._theadRow.innerHTML = headers.map((h) => `<th>${this._esc(h)}</th>`).join("");
    }
    const rows = dailySeries.map((row) => {
      const cells = [`<td>${formatDate(new Date(row.date))}</td>`, ...states.map((s) => `<td>${formatNumber(row[s.id || s.name] || 0)}</td>`)];
      return `<tr>${cells.join("")}</tr>`;
    });
    this._tableBody.innerHTML = rows.join("");
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
