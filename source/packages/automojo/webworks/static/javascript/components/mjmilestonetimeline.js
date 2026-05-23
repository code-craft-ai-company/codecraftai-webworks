/*
 * mjmilestonetimeline.js
 *
 * <mj-milestone-timeline> -- single horizontal (or vertical) axis of named
 * milestones, key dates, and phase bands. Lightest timeline visualization.
 *
 * SVG is aria-hidden; accessible <ol> always present.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { formatDate } from "../core/intl.js";

const AXIS_Y = 60;
const MARKER_R = 8;
const DIAMOND_HALF = 9;

const MARKER_SHAPES = {
  release:   "diamond",
  freeze:    "triangle",
  milestone: "circle",
  tag:       "diamond",
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
.svg-wrap { overflow-x: auto; }
svg { display: block; }
.marker-el:focus { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); }
.detail-popover { position: absolute; background: var(--mj-surface-raised); border: 1px solid var(--mj-border-strong); border-radius: var(--mj-radius-md); padding: var(--mj-space-3); box-shadow: var(--mj-elevation-2); min-width: 180px; top: var(--mj-space-3); left: 50%; transform: translateX(-50%); z-index: 10; }
.detail-popover h3 { margin: 0 0 var(--mj-space-1); font-size: var(--mj-font-size-sm); }
.detail-popover .close-btn { float: right; background: none; border: none; cursor: pointer; font-size: 1rem; color: var(--mj-text-muted); }
.a11y-list-wrap { padding: var(--mj-space-3); }
.a11y-list-wrap ol { margin: 0; padding-left: var(--mj-space-5); font-size: var(--mj-font-size-sm); }
.relative-wrap { position: relative; }
[hidden] { display: none !important; }
`;

export class MjMilestoneTimeline extends MjElement {
  static tagName = "mj-milestone-timeline";
  static styles = STYLES;
  static watched = ["start-date", "end-date", "orientation", "density", "today-marker"];

  constructor() {
    super();
    this._data = null;
    this._selectedMarker = null;
    this._showList = false;
    this._listId = nextId("mj-mt-list");
    this._popoverId = nextId("mj-mt-popover");
  }

  render() {
    return `
      <div class="wrapper" part="wrapper" role="img" aria-label="Milestone timeline">
        <div class="toolbar">
          <button class="btn-toggle-list" aria-controls="${this._listId}" aria-expanded="false">Show accessible list</button>
        </div>
        <div class="svg-wrap relative-wrap">
          <svg part="svg" aria-hidden="true" style="min-height:120px;"></svg>
          <div class="detail-popover" part="detail-popover" id="${this._popoverId}" role="dialog" aria-modal="false" hidden>
            <button class="close-btn" aria-label="Close">&#x2715;</button>
            <h3></h3>
            <div class="popover-content"></div>
            <slot name="marker-detail"></slot>
          </div>
        </div>
        <div id="${this._listId}" class="a11y-list-wrap" hidden>
          <ol part="a11y-list"></ol>
        </div>
        <slot hidden></slot>
      </div>`;
  }

  afterRender() {
    this._svg = this.$("svg");
    this._popover = this.$(".detail-popover");
    this._popoverContent = this.$(".popover-content");
    this._listWrap = this.$("#" + this._listId);
    this._listEl = this.$("ol");
    this._toggleBtn = this.$(".btn-toggle-list");
    this.listen(this._toggleBtn, "click", this._onToggleList.bind(this));
    this.listen(this.$(".close-btn"), "click", this._closePopover.bind(this));
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

  get selectedMarker() {
    return this._selectedMarker;
  }

  _onToggleList() {
    this._showList = !this._showList;
    this._listWrap.hidden = !this._showList;
    this._toggleBtn.setAttribute("aria-expanded", String(this._showList));
    return;
  }

  _closePopover() {
    this._popover.hidden = true;
    this._selectedMarker = null;
    this.emit("mj-marker-deselect", {});
    return;
  }

  _markerColor(type) {
    if (type === "release") {
      return "var(--mj-color-success)";
    }
    if (type === "freeze") {
      return "var(--mj-color-warning)";
    }
    if (type === "tag") {
      return "var(--mj-color-info)";
    }
    return "var(--mj-accent)";
  }

  _markerState(date) {
    const t = new Date(date).getTime();
    const now = Date.now();
    if (t < now - 86400000) {
      return "past";
    }
    if (t <= now + 86400000) {
      return "current";
    }
    return "upcoming";
  }

  _draw() {
    const d = this._data;
    if (d === null || d === undefined) {
      return;
    }
    const markers = d.markers || [];
    const phases = d.phases || [];

    const containerW = (this._svg.parentElement && this._svg.parentElement.clientWidth) || 700;
    const startAttr = this.getAttribute("start-date");
    const endAttr = this.getAttribute("end-date");
    const allTimes = markers.map((m) => new Date(m.date).getTime()).filter((t) => !isNaN(t));
    const tMin = startAttr !== null ? new Date(startAttr).getTime() : (allTimes.length > 0 ? Math.min(...allTimes) - 86400000 * 3 : Date.now() - 86400000 * 30);
    const tMax = endAttr !== null ? new Date(endAttr).getTime() : (allTimes.length > 0 ? Math.max(...allTimes) + 86400000 * 3 : Date.now() + 86400000 * 30);
    const tRange = tMax - tMin || 1;
    const PAD = 24;
    const tx = (ts) => PAD + ((ts - tMin) / tRange) * (containerW - PAD * 2);

    const svgH = 140;
    let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${containerW}" height="${svgH}">`;

    phases.forEach((ph, i) => {
      const x1 = tx(new Date(ph.start).getTime());
      const x2 = tx(new Date(ph.end).getTime());
      const colors = ["#4d83f7","#15803d","#b45309","#b91c1c"];
      svg += `<rect part="phase-band" x="${x1}" y="${AXIS_Y - 20}" width="${Math.max(0, x2 - x1)}" height="40" fill="${colors[i % colors.length]}" opacity="0.10" aria-hidden="true"/>`;
    });

    svg += `<line part="time-axis" x1="${PAD}" y1="${AXIS_Y}" x2="${containerW - PAD}" y2="${AXIS_Y}" stroke="var(--mj-border-strong)" stroke-width="2" aria-hidden="true"/>`;

    const tickCount = Math.min(8, Math.floor((containerW - PAD * 2) / 80));
    for (let i = 0; i <= tickCount; i = i + 1) {
      const t = tMin + (i / tickCount) * tRange;
      const x = tx(t);
      svg += `<line x1="${x}" y1="${AXIS_Y - 4}" x2="${x}" y2="${AXIS_Y + 4}" stroke="var(--mj-border-strong)" stroke-width="1.5" aria-hidden="true"/>`;
      svg += `<text x="${x}" y="${AXIS_Y + 16}" text-anchor="middle" font-size="10" fill="var(--mj-text-muted)">${formatDate(new Date(t), { month: "short", day: "numeric" })}</text>`;
    }

    if (this.getAttribute("today-marker") !== "false") {
      const todayX = tx(Date.now());
      if (todayX >= PAD && todayX <= containerW - PAD) {
        svg += `<line part="today-marker" x1="${todayX}" y1="${AXIS_Y - 25}" x2="${todayX}" y2="${AXIS_Y + 25}" stroke="var(--mj-color-danger)" stroke-width="2" stroke-dasharray="4 3" aria-hidden="true"/>`;
        svg += `<text x="${todayX}" y="${AXIS_Y - 28}" text-anchor="middle" font-size="9" fill="var(--mj-color-danger)">Today</text>`;
      }
    }

    markers.forEach((m, idx) => {
      const mx = tx(new Date(m.date).getTime());
      const stagger = idx % 2 === 0;
      const labelY = stagger ? AXIS_Y - 28 : AXIS_Y + 38;
      const color = this._markerColor(m.type);
      const state = this._markerState(m.date);
      const opacity = state === "past" ? 0.5 : 1.0;
      const shape = MARKER_SHAPES[m.type] || "circle";
      const ariaLabel = `${m.name}, ${m.type || "milestone"}, ${formatDate(new Date(m.date))}, ${state}`;

      svg += `<g class="marker-el" part="marker" tabindex="0" role="button" aria-label="${this._esc(ariaLabel)}" data-marker-idx="${idx}" opacity="${opacity}">`;
      if (shape === "diamond") {
        svg += `<polygon points="${mx},${AXIS_Y - DIAMOND_HALF} ${mx + DIAMOND_HALF},${AXIS_Y} ${mx},${AXIS_Y + DIAMOND_HALF} ${mx - DIAMOND_HALF},${AXIS_Y}" fill="${color}" stroke="var(--mj-surface)" stroke-width="2"/>`;
      } else if (shape === "triangle") {
        svg += `<polygon points="${mx},${AXIS_Y - DIAMOND_HALF} ${mx + DIAMOND_HALF},${AXIS_Y + DIAMOND_HALF / 2} ${mx - DIAMOND_HALF},${AXIS_Y + DIAMOND_HALF / 2}" fill="${color}" stroke="var(--mj-surface)" stroke-width="2"/>`;
      } else {
        svg += `<circle cx="${mx}" cy="${AXIS_Y}" r="${MARKER_R}" fill="${color}" stroke="var(--mj-surface)" stroke-width="2"/>`;
      }
      svg += `<line x1="${mx}" y1="${stagger ? AXIS_Y - DIAMOND_HALF - 1 : AXIS_Y + DIAMOND_HALF + 1}" x2="${mx}" y2="${stagger ? labelY + 14 : labelY - 4}" stroke="${color}" stroke-width="1" opacity="0.5" aria-hidden="true"/>`;
      const labelText = m.name.length > 16 ? m.name.slice(0, 14) + "…" : m.name;
      svg += `<text x="${mx}" y="${labelY}" text-anchor="middle" font-size="10" fill="var(--mj-text)" part="marker-label">${this._esc(labelText)}</text>`;
      svg += `</g>`;
    });

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

    this._buildList(markers);

    const wrapper = this.$(".wrapper");
    if (wrapper !== null) {
      wrapper.setAttribute("aria-label", `Milestone timeline: ${markers.length} markers`);
    }
    return;
  }

  _buildList(markers) {
    if (this._listEl === null || this._listEl === undefined) {
      return;
    }
    const items = markers.map((m) => `<li>${this._esc(m.name)}, ${m.type || "milestone"}, ${formatDate(new Date(m.date), { dateStyle: "long" })}</li>`);
    this._listEl.innerHTML = items.join("");
    return;
  }

  _onSvgClick(event) {
    const node = event.target.closest("[data-marker-idx]");
    if (node !== null) {
      const idx = parseInt(node.getAttribute("data-marker-idx"), 10);
      const markers = (this._data && this._data.markers) || [];
      const marker = markers[idx];
      if (marker !== undefined) {
        this._selectedMarker = marker;
        const h3 = this._popover.querySelector("h3");
        if (h3 !== null) {
          h3.textContent = marker.name;
        }
        this._popoverContent.innerHTML = `<p><strong>Type:</strong> ${this._esc(marker.type || "milestone")}</p><p><strong>Date:</strong> ${formatDate(new Date(marker.date), { dateStyle: "long" })}</p>${marker.description ? `<p>${this._esc(marker.description)}</p>` : ""}`;
        this._popover.hidden = false;
        this.emit("mj-marker-select", { marker });
      }
    }
    return;
  }

  _onSvgKeydown(event) {
    if (event.key === "Enter" || event.key === " ") {
      this._onSvgClick(event);
    }
    if (event.key === "Escape") {
      this._closePopover();
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
