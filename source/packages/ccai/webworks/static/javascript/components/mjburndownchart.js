/*
 * mjburndownchart.js
 *
 * <mj-burndown-chart> -- burndown / burnup chart with ideal line,
 * actual line, scope-change markers, and today marker.
 *
 * SVG is aria-hidden; accessible data table always present.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { formatDate, formatNumber } from "../core/intl.js";

const PAD_L = 56;
const PAD_R = 16;
const PAD_T = 16;
const PAD_B = 40;
const POINT_R = 4;

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
.status-badge { font-size: var(--mj-font-size-xs); font-weight: var(--mj-font-weight-medium); background: var(--mj-color-warning-surface); color: var(--mj-color-warning); border-radius: var(--mj-radius-pill); padding: 2px 8px; }
.status-badge[hidden] { display: none; }
.toggle-btn { font: inherit; font-size: var(--mj-font-size-xs); background: var(--mj-surface); border: 1px solid var(--mj-border-strong); border-radius: var(--mj-radius-sm); padding: 2px var(--mj-space-2); cursor: pointer; color: var(--mj-text); }
.toggle-btn:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: var(--mj-focus-ring-offset); }
.svg-wrap { overflow-x: auto; position: relative; }
svg { display: block; }
.point-el { cursor: pointer; }
.point-el:focus { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); }
.legend { display: flex; flex-wrap: wrap; gap: var(--mj-space-3); padding: var(--mj-space-2) var(--mj-space-3); border-top: 1px solid var(--mj-border); font-size: var(--mj-font-size-xs); }
.legend-item { display: flex; align-items: center; gap: var(--mj-space-1); }
.swatch { width: 24px; height: 3px; display: inline-block; border-radius: 2px; }
.a11y-table-wrap { padding: var(--mj-space-3); }
.a11y-table-wrap table { border-collapse: collapse; width: 100%; font-size: var(--mj-font-size-sm); }
.a11y-table-wrap th, .a11y-table-wrap td { border: 1px solid var(--mj-border); padding: var(--mj-space-1) var(--mj-space-2); text-align: left; }
[hidden] { display: none !important; }
`;

export class MjBurndownChart extends MjElement {
  static tagName = "mj-burndown-chart";
  static styles = STYLES;
  static watched = ["mode", "unit", "start-date", "end-date", "today-marker", "show-ideal", "show-scope-changes"];

  constructor() {
    super();
    this._data = null;
    this._selectedPoint = null;
    this._showTable = false;
    this._tableId = nextId("mj-bd-table");
  }

  render() {
    return `
      <div class="wrapper" part="wrapper">
        <div class="header">
          <strong style="font-size:var(--mj-font-size-sm)">Burndown Chart</strong>
          <span class="status-badge" hidden>Behind schedule</span>
          <span style="flex:1"></span>
          <button class="toggle-btn" aria-controls="${this._tableId}" aria-expanded="false">Show data table</button>
        </div>
        <div class="svg-wrap">
          <svg part="svg" role="img" aria-label="Burndown chart" aria-hidden="true"></svg>
        </div>
        <div class="legend" part="legend">
          <span class="legend-item"><span class="swatch" style="background:var(--mj-text-muted);border-top:2px dashed var(--mj-text-muted);height:0;margin-top:6px;"></span> Ideal</span>
          <span class="legend-item"><span class="swatch" style="background:var(--mj-accent);"></span> Actual</span>
        </div>
        <div id="${this._tableId}" class="a11y-table-wrap" hidden>
          <table part="data-table">
            <caption>Daily burndown values</caption>
            <thead><tr><th>Date</th><th>Remaining</th><th>Ideal</th><th>Scope Change</th></tr></thead>
            <tbody class="table-body"></tbody>
          </table>
        </div>
        <slot hidden></slot>
      </div>`;
  }

  afterRender() {
    this._svg = this.$("svg");
    this._statusBadge = this.$(".status-badge");
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

  get selectedPoint() {
    return this._selectedPoint;
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
    const dailyValues = d.dailyValues || [];
    const scopeChanges = d.scopeChanges || [];
    const totalScope = d.totalScope || 0;
    const mode = this.getAttribute("mode") || "burndown";
    const unit = this.getAttribute("unit") || "points";

    if (dailyValues.length === 0) {
      return;
    }

    const containerW = (this._svg.parentElement && this._svg.parentElement.clientWidth) || 700;
    const svgH = 300;
    const chartW = containerW - PAD_L - PAD_R;
    const chartH = svgH - PAD_T - PAD_B;

    const allTimes = dailyValues.map((v) => new Date(v.date).getTime()).filter((t) => !isNaN(t));
    const tMin = allTimes.length > 0 ? Math.min(...allTimes) : Date.now();
    const tMax = allTimes.length > 0 ? Math.max(...allTimes) : Date.now() + 86400000 * 14;
    const tRange = tMax - tMin || 86400000;

    const allValues = dailyValues.map((v) => v.value || 0);
    const maxVal = Math.max(totalScope, ...allValues) * 1.1 || 10;

    const tx = (ts) => PAD_L + ((ts - tMin) / tRange) * chartW;
    const ty = (val) => PAD_T + (1 - val / maxVal) * chartH;

    let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${containerW}" height="${svgH}">`;

    for (let i = 0; i <= 4; i = i + 1) {
      const val = (i / 4) * maxVal;
      const y = ty(val);
      svg += `<line x1="${PAD_L}" y1="${y}" x2="${containerW - PAD_R}" y2="${y}" stroke="var(--mj-border)" stroke-width="1" aria-hidden="true"/>`;
      svg += `<text x="${PAD_L - 6}" y="${y + 4}" text-anchor="end" font-size="10" fill="var(--mj-text-muted)">${formatNumber(Math.round(val))}</text>`;
    }

    const tickCount = Math.min(7, dailyValues.length);
    for (let i = 0; i <= tickCount; i = i + 1) {
      const t = tMin + (i / tickCount) * tRange;
      const x = tx(t);
      svg += `<text x="${x}" y="${svgH - 8}" text-anchor="middle" font-size="10" fill="var(--mj-text-muted)">${formatDate(new Date(t), { month: "short", day: "numeric" })}</text>`;
    }

    svg += `<line part="value-axis" x1="${PAD_L}" y1="${PAD_T}" x2="${PAD_L}" y2="${PAD_T + chartH}" stroke="var(--mj-border-strong)" stroke-width="1.5" aria-hidden="true"/>`;
    svg += `<line part="time-axis" x1="${PAD_L}" y1="${PAD_T + chartH}" x2="${containerW - PAD_R}" y2="${PAD_T + chartH}" stroke="var(--mj-border-strong)" stroke-width="1.5" aria-hidden="true"/>`;

    if (this.getAttribute("show-ideal") !== "false") {
      const idealStart = mode === "burndown" ? totalScope : 0;
      const idealEnd = mode === "burndown" ? 0 : totalScope;
      const x1 = tx(tMin);
      const y1 = ty(idealStart);
      const x2 = tx(tMax);
      const y2 = ty(idealEnd);
      svg += `<line part="ideal-line" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="var(--mj-text-muted)" stroke-width="1.5" stroke-dasharray="8 4" aria-hidden="true"/>`;
    }

    const today = Date.now();
    const pointsUpToToday = dailyValues.filter((v) => new Date(v.date).getTime() <= today);
    if (pointsUpToToday.length > 1) {
      const pts = pointsUpToToday.map((v) => `${tx(new Date(v.date).getTime())},${ty(v.value || 0)}`).join(" ");
      svg += `<polyline part="actual-line" points="${pts}" stroke="var(--mj-accent)" stroke-width="2" fill="none"/>`;
    }

    pointsUpToToday.forEach((v, i) => {
      const px = tx(new Date(v.date).getTime());
      const py = ty(v.value || 0);
      const ariaLabel = `Day ${formatDate(new Date(v.date))}: ${formatNumber(v.value || 0)} ${unit} ${mode === "burndown" ? "remaining" : "completed"}`;
      svg += `<circle class="point-el" part="data-point" cx="${px}" cy="${py}" r="${POINT_R}" fill="var(--mj-accent)" stroke="var(--mj-surface)" stroke-width="2" tabindex="0" role="button" aria-label="${this._esc(ariaLabel)}" data-point-idx="${i}"/>`;
    });

    if (this.getAttribute("show-scope-changes") !== "false") {
      scopeChanges.forEach((sc) => {
        const scx = tx(new Date(sc.date).getTime());
        const delta = sc.delta || 0;
        const deltaLabel = delta > 0 ? `+${delta}` : String(delta);
        svg += `<line part="scope-change-marker" x1="${scx}" y1="${PAD_T}" x2="${scx}" y2="${PAD_T + chartH}" stroke="var(--mj-color-warning)" stroke-width="1.5" stroke-dasharray="4 4" aria-label="${this._esc(`Scope change on ${formatDate(new Date(sc.date))}: ${deltaLabel} ${unit}`)}" aria-hidden="true"/>`;
        svg += `<text x="${scx + 4}" y="${PAD_T + 16}" font-size="10" fill="var(--mj-color-warning)">${deltaLabel}</text>`;
      });
    }

    if (this.getAttribute("today-marker") !== "false") {
      const todayX = tx(today);
      if (todayX >= PAD_L && todayX <= containerW - PAD_R) {
        svg += `<line part="today-marker" x1="${todayX}" y1="${PAD_T}" x2="${todayX}" y2="${PAD_T + chartH}" stroke="var(--mj-color-danger)" stroke-width="1.5" stroke-dasharray="6 3" aria-hidden="true"/>`;
        svg += `<text x="${todayX + 4}" y="${PAD_T + 12}" font-size="9" fill="var(--mj-color-danger)">Today</text>`;
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
    const newSvg = this.shadowRoot.querySelector("svg");
    if (newSvg !== null) {
      this._svg = newSvg;
      this.listen(newSvg, "click", this._onSvgClick.bind(this));
      this.listen(newSvg, "keydown", this._onSvgKeydown.bind(this));
    }

    const latestActual = pointsUpToToday[pointsUpToToday.length - 1];
    const idealAtToday = mode === "burndown" ? totalScope * (1 - (today - tMin) / tRange) : totalScope * ((today - tMin) / tRange);
    const isBehind = latestActual !== undefined && (mode === "burndown" ? (latestActual.value || 0) > idealAtToday : (latestActual.value || 0) < idealAtToday);
    if (this._statusBadge !== null) {
      this._statusBadge.hidden = !isBehind;
    }

    this._buildTable(dailyValues, totalScope, tMin, tMax, mode);

    const wrapper = this.$(".wrapper");
    if (wrapper !== null) {
      wrapper.setAttribute("aria-label", `Burndown chart: ${dailyValues.length} days, unit: ${unit}`);
    }
    return;
  }

  _buildTable(dailyValues, totalScope, tMin, tMax, mode) {
    if (this._tableBody === null || this._tableBody === undefined) {
      return;
    }
    const tRange = tMax - tMin || 1;
    const rows = dailyValues.map((v) => {
      const t = new Date(v.date).getTime();
      const ideal = mode === "burndown" ? totalScope * (1 - (t - tMin) / tRange) : totalScope * ((t - tMin) / tRange);
      return `<tr><td>${formatDate(new Date(v.date))}</td><td>${formatNumber(v.value || 0)}</td><td>${formatNumber(Math.round(ideal))}</td><td>${v.scopeChange || ""}</td></tr>`;
    });
    this._tableBody.innerHTML = rows.join("");
    return;
  }

  _onSvgClick(event) {
    const el = event.target.closest("[data-point-idx]");
    if (el !== null) {
      const idx = parseInt(el.getAttribute("data-point-idx"), 10);
      const values = (this._data && this._data.dailyValues) || [];
      const point = values[idx];
      if (point !== undefined) {
        this._selectedPoint = point;
        this.emit("mj-point-select", { point });
      }
    }
    return;
  }

  _onSvgKeydown(event) {
    if (event.key === "Enter" || event.key === " ") {
      this._onSvgClick(event);
    }
    if (event.key === "Escape") {
      this._selectedPoint = null;
      this.emit("mj-point-deselect", {});
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
