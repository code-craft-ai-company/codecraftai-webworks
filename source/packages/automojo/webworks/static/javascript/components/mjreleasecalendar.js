/*
 * mjreleasecalendar.js
 *
 * <mj-release-calendar> -- month/week/day calendar grid showing releases,
 * freezes, blackouts, and key dates as event chips and multi-day bars.
 *
 * SVG-free: uses a CSS grid calendar. Accessible event list always present.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { formatDate } from "../core/intl.js";

const EVENT_COLORS = {
  release:   { bg: "var(--mj-color-success-surface)", border: "var(--mj-color-success)", text: "var(--mj-color-success)" },
  freeze:    { bg: "var(--mj-color-warning-surface)", border: "var(--mj-color-warning)", text: "var(--mj-color-warning)" },
  blackout:  { bg: "var(--mj-color-danger-surface)",  border: "var(--mj-color-danger)",  text: "var(--mj-color-danger)"  },
  milestone: { bg: "var(--mj-color-info-surface)",    border: "var(--mj-color-info)",    text: "var(--mj-color-info)"    },
  holiday:   { bg: "var(--mj-bg-muted)",              border: "var(--mj-border-strong)", text: "var(--mj-text-muted)"    },
};

const EVENT_ICONS = {
  release:   "🚀",
  freeze:    "❄",
  blackout:  "⛔",
  milestone: "◆",
  holiday:   "🗓",
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
.cal-header { display: flex; align-items: center; gap: var(--mj-space-2); padding: var(--mj-space-2) var(--mj-space-3); border-bottom: 1px solid var(--mj-border); flex-wrap: wrap; }
.cal-title { font-weight: var(--mj-font-weight-medium); font-size: var(--mj-font-size-md); flex: 1; }
.nav-btn { font: inherit; font-size: 1.1rem; background: none; border: 1px solid var(--mj-border); border-radius: var(--mj-radius-sm); padding: 2px 8px; cursor: pointer; color: var(--mj-text); }
.nav-btn:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: var(--mj-focus-ring-offset); }
.view-btn { font: inherit; font-size: var(--mj-font-size-xs); background: var(--mj-surface); border: 1px solid var(--mj-border-strong); border-radius: var(--mj-radius-sm); padding: 2px var(--mj-space-2); cursor: pointer; color: var(--mj-text); }
.view-btn[aria-pressed="true"] { background: var(--mj-accent); color: var(--mj-text-on-accent); border-color: var(--mj-accent); }
.view-btn:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: var(--mj-focus-ring-offset); }
.cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); }
.day-header { padding: var(--mj-space-1) var(--mj-space-2); font-size: var(--mj-font-size-xs); font-weight: var(--mj-font-weight-medium); color: var(--mj-text-muted); text-align: center; border-bottom: 1px solid var(--mj-border); background: var(--mj-bg-subtle); }
.day-cell { min-height: 80px; padding: var(--mj-space-1); border-right: 1px solid var(--mj-border); border-bottom: 1px solid var(--mj-border); vertical-align: top; position: relative; }
.day-cell:nth-child(7n) { border-right: none; }
.day-cell.today { background: var(--mj-color-info-surface); }
.day-cell.other-month { opacity: 0.45; }
.day-num { font-size: var(--mj-font-size-xs); color: var(--mj-text-muted); margin-bottom: 2px; }
.day-cell.today .day-num { font-weight: var(--mj-font-weight-bold); color: var(--mj-color-info); }
.event-chip { display: flex; align-items: center; gap: 3px; font-size: 11px; border-radius: 3px; padding: 1px 4px; margin-bottom: 2px; cursor: pointer; border: 1px solid transparent; background: var(--mj-bg-muted); }
.event-chip:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: 1px; }
.event-icon { font-size: 10px; }
.more-chip { font-size: 10px; color: var(--mj-text-muted); cursor: pointer; padding: 1px 4px; }
.toggle-list-btn { font: inherit; font-size: var(--mj-font-size-xs); background: var(--mj-surface); border: 1px solid var(--mj-border-strong); border-radius: var(--mj-radius-sm); padding: 2px var(--mj-space-2); cursor: pointer; color: var(--mj-text); }
.toggle-list-btn:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: var(--mj-focus-ring-offset); }
.a11y-list-wrap { padding: var(--mj-space-3); }
.a11y-list-wrap ol { margin: 0; padding-left: var(--mj-space-5); font-size: var(--mj-font-size-sm); }
.detail-panel { position: fixed; z-index: var(--mj-layer-popover); background: var(--mj-surface-raised); border: 1px solid var(--mj-border-strong); border-radius: var(--mj-radius-md); padding: var(--mj-space-3); box-shadow: var(--mj-elevation-3); min-width: 200px; }
.detail-panel h3 { margin: 0 0 var(--mj-space-2); font-size: var(--mj-font-size-sm); }
.detail-panel .close-btn { float: right; background: none; border: none; cursor: pointer; font-size: 1rem; }
[hidden] { display: none !important; }
`;

export class MjReleaseCalendar extends MjElement {
  static tagName = "mj-release-calendar";
  static styles = STYLES;
  static watched = ["view", "current-date", "today-marker", "first-day-of-week", "locale"];

  constructor() {
    super();
    this._data = null;
    this._selectedEvent = null;
    this._view = "month";
    this._currentDate = new Date();
    this._showList = false;
    this._listId = nextId("mj-cal-list");
  }

  render() {
    return `
      <div class="wrapper" part="wrapper" role="region" aria-label="Release calendar">
        <div class="cal-header" part="nav-controls">
          <button class="nav-btn prev-btn" aria-label="Previous month">&#x2039;</button>
          <span class="cal-title"></span>
          <button class="nav-btn next-btn" aria-label="Next month">&#x203A;</button>
          <button class="nav-btn today-btn" aria-label="Go to today" style="font-size:var(--mj-font-size-xs);padding:2px 8px;">Today</button>
          <span role="radiogroup" part="view-switcher" aria-label="Calendar view">
            <button class="view-btn" data-view="month" aria-pressed="true">Month</button>
            <button class="view-btn" data-view="week" aria-pressed="false">Week</button>
          </span>
          <button class="toggle-list-btn" aria-controls="${this._listId}" aria-expanded="false">Show event list</button>
        </div>
        <div class="cal-grid" part="calendar-grid" role="grid" aria-label="Calendar"></div>
        <div class="detail-panel" part="detail-popover" role="dialog" aria-modal="false" hidden>
          <button class="close-btn" aria-label="Close">&#x2715;</button>
          <h3></h3>
          <div class="detail-content"></div>
          <slot name="event-detail"></slot>
        </div>
        <div id="${this._listId}" class="a11y-list-wrap" hidden>
          <ol part="a11y-list"></ol>
        </div>
        <slot hidden></slot>
      </div>`;
  }

  afterRender() {
    this._grid = this.$(".cal-grid");
    this._title = this.$(".cal-title");
    this._detailPanel = this.$(".detail-panel");
    this._detailContent = this.$(".detail-content");
    this._listWrap = this.$("#" + this._listId);
    this._listEl = this.$("ol");
    this.listen(this.$(".prev-btn"), "click", () => { this._navigate(-1); });
    this.listen(this.$(".next-btn"), "click", () => { this._navigate(1); });
    this.listen(this.$(".today-btn"), "click", () => { this._currentDate = new Date(); this._renderCalendar(); });
    this.listen(this.$(".close-btn"), "click", () => { this._detailPanel.hidden = true; this._selectedEvent = null; });
    this.listen(this.$(".toggle-list-btn"), "click", this._onToggleList.bind(this));
    this.$all(".view-btn").forEach((btn) => {
      this.listen(btn, "click", (e) => { this._switchView(e.currentTarget.getAttribute("data-view")); });
    });
    const cdAttr = this.getAttribute("current-date");
    if (cdAttr !== null && cdAttr !== "") {
      this._currentDate = new Date(cdAttr);
    }
    this._view = this.getAttribute("view") || "month";
    this._renderCalendar();
    return;
  }

  get data() {
    return this._data;
  }

  set data(value) {
    this._data = value;
    if (this._grid !== undefined) {
      this._renderCalendar();
    }
    return;
  }

  get selectedEvent() {
    return this._selectedEvent;
  }

  get visiblePeriod() {
    const y = this._currentDate.getFullYear();
    const m = this._currentDate.getMonth();
    return { start: new Date(y, m, 1), end: new Date(y, m + 1, 0) };
  }

  _navigate(delta) {
    if (this._view === "month") {
      this._currentDate = new Date(this._currentDate.getFullYear(), this._currentDate.getMonth() + delta, 1);
    } else {
      this._currentDate = new Date(this._currentDate.getTime() + delta * 7 * 86400000);
    }
    this._renderCalendar();
    const period = this.visiblePeriod;
    this.emit("mj-period-change", { start: period.start.toISOString(), end: period.end.toISOString(), view: this._view });
    return;
  }

  _switchView(view) {
    this._view = view;
    this._renderCalendar();
    this.$all(".view-btn").forEach((btn) => {
      btn.setAttribute("aria-pressed", String(btn.getAttribute("data-view") === view));
    });
    this.emit("mj-view-change", { view });
    return;
  }

  _onToggleList() {
    this._showList = !this._showList;
    this._listWrap.hidden = !this._showList;
    this.$(".toggle-list-btn").setAttribute("aria-expanded", String(this._showList));
    return;
  }

  _renderCalendar() {
    if (this._grid === null || this._grid === undefined) {
      return;
    }
    const y = this._currentDate.getFullYear();
    const m = this._currentDate.getMonth();
    const firstDow = parseInt(this.getAttribute("first-day-of-week") || "0", 10);
    const today = new Date();

    if (this._title !== null) {
      this._title.textContent = formatDate(new Date(y, m, 1), { month: "long", year: "numeric" });
    }

    const DOW_NAMES = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
    const dowOrder = [];
    for (let i = 0; i < 7; i = i + 1) {
      dowOrder.push(DOW_NAMES[(firstDow + i) % 7]);
    }

    const firstDay = new Date(y, m, 1);
    let startDow = firstDay.getDay() - firstDow;
    if (startDow < 0) {
      startDow = startDow + 7;
    }
    const daysInMonth = new Date(y, m + 1, 0).getDate();
    const totalCells = Math.ceil((startDow + daysInMonth) / 7) * 7;

    const events = (this._data && this._data.events) || [];

    let html = dowOrder.map((name) => `<div class="day-header" role="columnheader">${this._esc(name)}</div>`).join("");

    for (let ci = 0; ci < totalCells; ci = ci + 1) {
      const dayOffset = ci - startDow;
      const cellDate = new Date(y, m, dayOffset + 1);
      const isThisMonth = cellDate.getMonth() === m;
      const isToday = cellDate.toDateString() === today.toDateString();
      const dateStr = cellDate.toISOString().slice(0, 10);

      const dayEvents = events.filter((ev) => {
        const evStart = ev.startDate || ev.start || "";
        const evEnd = ev.endDate || ev.end || evStart;
        return dateStr >= evStart.slice(0, 10) && dateStr <= evEnd.slice(0, 10);
      });

      const isFreezeDay = dayEvents.some((ev) => ev.type === "freeze" || ev.type === "blackout");
      const freezeLabel = isFreezeDay ? " in freeze window" : "";
      const todayHighlight = isToday && this.getAttribute("today-marker") !== "false";

      let cellClass = "day-cell";
      if (todayHighlight) {
        cellClass += " today";
      }
      if (!isThisMonth) {
        cellClass += " other-month";
      }

      const maxVisible = 3;
      const visibleEvents = dayEvents.slice(0, maxVisible);
      const overflow = dayEvents.length - maxVisible;

      const chips = visibleEvents.map((ev) => {
        const colors = EVENT_COLORS[ev.type] || EVENT_COLORS.milestone;
        const icon = EVENT_ICONS[ev.type] || "◆";
        const endDate = ev.endDate || ev.end || "";
        const isMultiDay = endDate !== "" && endDate.slice(0, 10) !== (ev.startDate || ev.start || "").slice(0, 10);
        const ariaLabel = isMultiDay
          ? `${ev.name}, ${ev.type || "event"}, ${formatDate(new Date(ev.startDate || ev.start))} to ${formatDate(new Date(endDate))}`
          : `${ev.name}, ${ev.type || "event"}, ${formatDate(new Date(ev.startDate || ev.start))}`;
        return `<button class="event-chip" part="event-chip" role="button" aria-label="${this._esc(ariaLabel)}" data-event-id="${this._esc(ev.id || ev.name)}" style="background:${colors.bg};border-color:${colors.border};color:${colors.text};"><span class="event-icon" aria-hidden="true">${icon}</span><span part="event-icon">${this._esc(ev.name.length > 14 ? ev.name.slice(0, 12) + "…" : ev.name)}</span></button>`;
      }).join("");

      const moreChip = overflow > 0 ? `<div class="more-chip" aria-label="${overflow} more events on ${formatDate(cellDate)}">+${overflow} more</div>` : "";

      const ariaLabel = `${cellDate.getDate()}${freezeLabel}`;
      html += `<div class="day-cell ${cellClass}" part="${todayHighlight ? "today-cell day-cell" : "day-cell"}" role="gridcell" aria-label="${ariaLabel}"><div class="day-num">${cellDate.getDate()}</div>${chips}${moreChip}</div>`;
    }

    this._grid.innerHTML = html;
    this._grid.querySelectorAll(".event-chip").forEach((chip) => {
      this.listen(chip, "click", (e) => { this._onChipClick(e); });
    });

    this._buildList(events);
    return;
  }

  _buildList(events) {
    if (this._listEl === null || this._listEl === undefined) {
      return;
    }
    const sorted = events.slice().sort((a, b) => {
      const ta = new Date(a.startDate || a.start || "").getTime();
      const tb = new Date(b.startDate || b.start || "").getTime();
      return ta - tb;
    });
    const items = sorted.map((ev) => {
      const start = formatDate(new Date(ev.startDate || ev.start || ""), { dateStyle: "medium" });
      const end = ev.endDate && ev.endDate !== ev.startDate ? ` to ${formatDate(new Date(ev.endDate), { dateStyle: "medium" })}` : "";
      return `<li>${this._esc(ev.name)}, ${ev.type || "event"}, ${start}${end}</li>`;
    });
    this._listEl.innerHTML = items.join("");
    return;
  }

  _onChipClick(event) {
    const chip = event.currentTarget;
    const id = chip.getAttribute("data-event-id");
    const events = (this._data && this._data.events) || [];
    const ev = events.find((e) => (e.id || e.name) === id);
    if (ev !== undefined) {
      this._selectedEvent = ev;
      const h3 = this._detailPanel.querySelector("h3");
      if (h3 !== null) {
        h3.textContent = ev.name;
      }
      const start = formatDate(new Date(ev.startDate || ev.start || ""), { dateStyle: "long" });
      const end = ev.endDate && ev.endDate !== ev.startDate ? ` to ${formatDate(new Date(ev.endDate), { dateStyle: "long" })}` : "";
      this._detailContent.innerHTML = `<p><strong>Type:</strong> ${this._esc(ev.type || "event")}</p><p><strong>Date:</strong> ${start}${end}</p>${ev.description ? `<p>${this._esc(ev.description)}</p>` : ""}${ev.url ? `<p><a href="${this._esc(ev.url)}" target="_blank">More info</a></p>` : ""}`;
      this._detailPanel.hidden = false;
      this.emit("mj-event-select", { event: ev });
    }
    return;
  }

  _esc(str) {
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "view") {
      this._view = newValue || "month";
    }
    if (name === "current-date" && newValue !== null && newValue !== "") {
      this._currentDate = new Date(newValue);
    }
    if (this._grid !== undefined) {
      this._renderCalendar();
    }
    return;
  }
}
