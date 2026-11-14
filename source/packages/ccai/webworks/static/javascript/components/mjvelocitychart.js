/*
 * mjvelocitychart.js
 *
 * <mj-velocity-chart> -- grouped bar chart of committed vs completed work
 * per sprint, with a rolling-average line overlay.
 *
 * The SVG is a labelled group whose sprint bar groups are keyboard reachable
 * (one tab stop, arrow keys between sprints); selecting a sprint outlines it
 * and writes its values to the read-out in the header. Sprint groups keep a
 * minimum width, so a long history scrolls horizontally instead of
 * collapsing. A data table with the same values can be disclosed from the
 * header.
 *
 * Data: `data` property, `src` attribute or inline JSON child --
 *   { sprints: [{ name, committed, completed }] }
 */

import { nextId } from "../core/mjelement.js";
import { html } from "../core/html.js";
import { formatNumber, t } from "../core/intl.js";
import {
  PM_CHART_STYLES, PmChartElement, SECONDARY_SERIES_FILL, SECONDARY_SERIES_STROKE,
  emptyStateMarkup, markSelection, setEmptyState, toNumber, toText, truncateMiddle,
  wireMarks
} from "./pmchartsupport.js";

const PAD_L = 52;
const PAD_R = 16;
const PAD_T = 24;
const PAD_B = 50;
const SVG_H = 300;
const BAR_GAP = 4;
const MIN_GROUP_W = 56;
const CAPTION_MIN_GROUP_W = 96;
const LABEL_CHAR_W = 6;
const DEFAULT_ROLLING_WINDOW = 3;

/* Display text of the delivery status of a sprint. */
const STATUS_LABEL_KEYS = {
  onTarget:       "mj.velocityChart.statusOnTarget",
  underDelivered: "mj.velocityChart.statusUnderDelivered",
  exceeded:       "mj.velocityChart.statusExceeded"
};

const STYLES = `
${PM_CHART_STYLES}
.sprint-readout { font-size: var(--mj-font-size-xs); color: var(--mj-text-muted); }
.bar-group-el[data-selected="true"] .selection-frame { stroke: var(--mj-text); }
.swatch { inline-size: 16px; block-size: 10px; display: inline-block; border-radius: 2px; }
.swatch-committed { background: ${SECONDARY_SERIES_FILL}; border: 1px solid ${SECONDARY_SERIES_STROKE}; }
.swatch-completed { background: var(--mj-accent); }
.swatch-average { block-size: 3px; background: var(--mj-color-warning); }
`;

export class MjVelocityChart extends PmChartElement {
  static tagName = "mj-velocity-chart";
  static styles = STYLES;
  static watched = ["unit", "bar-mode", "rolling-window", "show-average", "show-committed"];

  constructor() {
    super()
    this._selectedSprint = null
    this._selectedKey = null
    this._tableId = nextId("mj-vc-table")
  }

  render() {
    const chartLabel = t("mj.velocityChart.label")

    const markup = html`
      <div class="wrapper" part="wrapper" role="group" aria-label="${chartLabel}">
        <div class="toolbar header">
          <strong class="toolbar-title">${t("mj.velocityChart.title")}</strong>
          <span class="sprint-readout" part="sprint-detail" role="status"></span>
          <span class="toolbar-spacer"></span>
          <button class="chart-button toggle-btn" type="button" aria-controls="${this._tableId}" aria-expanded="false">${t("mj.velocityChart.showDataTable")}</button>
        </div>
        <div class="chart-scroll svg-wrap">
          <svg part="svg" role="group" aria-label="${chartLabel}"></svg>
          ${emptyStateMarkup()}
        </div>
        <div class="legend" part="legend">
          <span class="legend-item legend-committed" part="legend-committed"><span class="swatch swatch-committed"></span> ${t("mj.velocityChart.legendCommitted")}</span>
          <span class="legend-item" part="legend-completed"><span class="swatch swatch-completed"></span> ${t("mj.velocityChart.legendCompleted")}</span>
          <span class="legend-item legend-average" part="legend-average"><span class="swatch swatch-average"></span> ${t("mj.velocityChart.legendAverage")}</span>
        </div>
        <div id="${this._tableId}" class="a11y-table-wrap" hidden>
          <table part="data-table">
            <caption>${t("mj.velocityChart.tableCaption")}</caption>
            <thead><tr><th scope="col">${t("mj.velocityChart.columnSprint")}</th><th scope="col">${t("mj.velocityChart.columnCommitted")}</th><th scope="col">${t("mj.velocityChart.columnCompleted")}</th><th scope="col">${t("mj.velocityChart.columnDifference")}</th><th scope="col">${t("mj.velocityChart.columnAverage")}</th></tr></thead>
            <tbody class="table-body"></tbody>
          </table>
        </div>
      </div>`
    return markup
  }

  afterRender() {
    this._svg = this.$("svg")
    this._wrapper = this.$(".wrapper")
    this._svgWrap = this.$(".svg-wrap")
    this._readout = this.$(".sprint-readout")
    this._tableBody = this.$(".table-body")

    wireMarks(this, this._svg, (mark) => {
      this._onMarkActivate(mark)
    }, (key) => {
      this._activeMarkKey = key
    })

    this.listen(this.shadowRoot, "keydown", (event) => {
      if (event.key === "Escape" && this._selectedSprint !== null) {
        event.preventDefault()
        this._clearSelection(true)
      }
    })

    this.setupChart({
      alternativeButton: this.$(".toggle-btn"),
      alternativeRegion: this.$(`#${this._tableId}`),
      resizeTarget: this._svgWrap
    })
    return
  }

  get selectedSprint() {
    return this._selectedSprint
  }

  get rollingAverage() {
    const averages = this._computeRolling(this._sprints(), this._rollingWindow())
    return averages
  }

  onDataChanged() {
    this._clearSelection(false)
    return
  }

  onDataDrawn() {
    this.emit("mj-data-load", { sprints: this._sprints().length })
    return
  }

  _sprints() {
    const source = this._data !== null && Array.isArray(this._data.sprints) === true ? this._data.sprints : []
    const sprints = source.map((sprint, index) => {
      const safe = sprint !== null && typeof sprint === "object" ? sprint : {}
      const hasName = safe.name !== undefined && safe.name !== null && toText(safe.name).length > 0
      const described = {
        source: sprint,
        name: hasName === true ? toText(safe.name) : t("mj.velocityChart.fallbackName", { number: index + 1 }),
        committed: Math.max(0, toNumber(safe.committed, 0)),
        completed: Math.max(0, toNumber(safe.completed, 0))
      }
      return described
    })
    return sprints
  }

  /* The rolling window: a whole number of sprints, never below one. */
  _rollingWindow() {
    const parsed = parseInt(this.getAttribute("rolling-window"), 10)
    const size = Number.isFinite(parsed) === true && parsed >= 1 ? parsed : DEFAULT_ROLLING_WINDOW
    return size
  }

  _computeRolling(sprints, windowSize) {
    const size = Number.isFinite(windowSize) === true && windowSize >= 1 ? Math.floor(windowSize) : 1
    const averages = []
    for (let index = 0; index < sprints.length; index = index + 1) {
      const slice = sprints.slice(Math.max(0, index - size + 1), index + 1)
      const sum = slice.reduce((running, sprint) => running + toNumber(sprint.completed, 0), 0)
      averages.push(sum / slice.length)
    }
    return averages
  }

  /* "onTarget", "underDelivered" or "exceeded" (keys of STATUS_LABEL_KEYS). */
  _statusOf(sprint) {
    const difference = sprint.completed - sprint.committed
    let status = "onTarget"
    if (difference < -sprint.committed * 0.2) {
      status = "underDelivered"
    } else if (difference > 0) {
      status = "exceeded"
    }
    return status
  }

  _clearSelection(notify) {
    const hadSelection = this._selectedSprint !== null
    this._selectedSprint = null
    this._selectedKey = null
    if (this._svg !== undefined) {
      markSelection(this._svg, null)
      this._readout.textContent = ""
    }
    if (notify === true && hadSelection === true) {
      this.emit("mj-sprint-deselect", {})
    }
    return
  }

  drawChart() {
    const sprints = this._sprints()
    const rollingWindow = this._rollingWindow()
    const rollingAverages = this._computeRolling(sprints, rollingWindow)
    const unit = this.getAttribute("unit") !== null && this.getAttribute("unit").length > 0 ? this.getAttribute("unit") : t("mj.velocityChart.defaultUnit")
    const grouped = this.getAttribute("bar-mode") !== "overlay"
    const showAverage = this.enabledUnlessFalse("show-average")
    const showCommitted = this.enabledUnlessFalse("show-committed")

    this.$(".legend-committed").hidden = showCommitted === false
    this.$(".legend-average").hidden = showAverage === false
    this._buildTable(sprints, rollingAverages)

    if (sprints.length === 0) {
      this.renderSvg(this._svg, 0, 0, "", null)
      this._svg.toggleAttribute("hidden", true)
      this._readout.textContent = ""
      setEmptyState(this, "empty")
      this._wrapper.setAttribute("aria-label", t("mj.velocityChart.noDataLabel"))
      return
    }

    this._svg.toggleAttribute("hidden", false)
    setEmptyState(this, "ready")

    const highest = sprints.reduce((maximum, sprint) => Math.max(maximum, sprint.committed, sprint.completed), 0)
    const maxScale = highest > 0 ? highest * 1.15 : 10

    const containerWidth = this._svgWrap.clientWidth > 0 ? this._svgWrap.clientWidth : 700
    const groupWidth = Math.max(MIN_GROUP_W, (containerWidth - PAD_L - PAD_R) / sprints.length)
    const plotWidth = groupWidth * sprints.length
    const totalWidth = Math.ceil(plotWidth + PAD_L + PAD_R)
    const plotHeight = SVG_H - PAD_T - PAD_B
    const barBase = PAD_T + plotHeight
    const plotRight = PAD_L + plotWidth
    const barWidth = grouped === true ? (groupWidth - BAR_GAP * 3) / 2 : groupWidth - BAR_GAP * 2
    const valueToY = (value) => {
      const y = PAD_T + (1 - value / maxScale) * plotHeight
      return y
    }

    const parts = []

    for (let step = 0; step <= 4; step = step + 1) {
      const value = (step / 4) * maxScale
      const y = valueToY(value)
      parts.push(html`<line x1="${PAD_L}" y1="${y}" x2="${plotRight}" y2="${y}" stroke="var(--mj-border)" stroke-width="1" aria-hidden="true"/>`)
      parts.push(html`<text x="${PAD_L - 6}" y="${y + 4}" text-anchor="end" font-size="10" fill="var(--mj-text-muted)">${formatNumber(Math.round(value))}</text>`)
    }
    parts.push(html`<text part="value-axis-title" transform="rotate(-90)" x="${-(PAD_T + plotHeight / 2)}" y="12" text-anchor="middle" font-size="10" fill="var(--mj-text-muted)">${unit}</text>`)

    parts.push(html`<line part="value-axis" x1="${PAD_L}" y1="${PAD_T}" x2="${PAD_L}" y2="${barBase}" stroke="var(--mj-border-strong)" stroke-width="1.5" aria-hidden="true"/>`)
    parts.push(html`<line part="sprint-axis" x1="${PAD_L}" y1="${barBase}" x2="${plotRight}" y2="${barBase}" stroke="var(--mj-border-strong)" stroke-width="1.5" aria-hidden="true"/>`)

    const labelChars = Math.max(3, Math.floor((groupWidth - 4) / LABEL_CHAR_W))
    const averagePoints = []

    sprints.forEach((sprint, index) => {
      const groupX = PAD_L + index * groupWidth
      const centreX = groupX + groupWidth / 2
      const status = this._statusOf(sprint)
      const statusText = t(STATUS_LABEL_KEYS[status])
      const label = t("mj.velocityChart.sprintLabel", {
        name: sprint.name,
        committed: formatNumber(sprint.committed),
        completed: formatNumber(sprint.completed),
        unit: unit,
        status: statusText,
        average: formatNumber(Math.round(rollingAverages[index]))
      })
      const shapes = []

      /* A transparent frame makes the whole column the target and shows selection. */
      shapes.push(html`<rect class="selection-frame" x="${groupX + 1}" y="${PAD_T}" width="${groupWidth - 2}" height="${plotHeight}" fill="transparent" stroke="transparent" stroke-width="1.5" rx="3"/>`)

      const committedX = groupX + BAR_GAP
      const completedX = grouped === true ? groupX + BAR_GAP * 2 + barWidth : groupX + BAR_GAP
      if (showCommitted === true && sprint.committed > 0) {
        shapes.push(html`<rect part="committed-bar" x="${committedX}" y="${valueToY(sprint.committed)}" width="${barWidth}" height="${barBase - valueToY(sprint.committed)}" rx="3" fill="${SECONDARY_SERIES_FILL}" stroke="${SECONDARY_SERIES_STROKE}" stroke-width="1" aria-hidden="true"/>`)
      }
      const completedWidth = grouped === true ? barWidth : Math.max(4, barWidth - 12)
      const completedOffset = grouped === true ? 0 : (barWidth - completedWidth) / 2
      shapes.push(html`<rect part="completed-bar" x="${completedX + completedOffset}" y="${valueToY(sprint.completed)}" width="${completedWidth}" height="${barBase - valueToY(sprint.completed)}" rx="3" fill="var(--mj-accent)" aria-hidden="true"/>`)

      if (status !== "onTarget") {
        const captionColor = status === "exceeded" ? "var(--mj-color-success)" : "var(--mj-color-danger)"
        const captionY = valueToY(Math.max(sprint.completed, showCommitted === true ? sprint.committed : 0)) - 5
        /* Short of room the caption becomes an arrow; the tooltip has the words. */
        const captionText = groupWidth >= CAPTION_MIN_GROUP_W ? statusText : (status === "exceeded" ? "▲" : "▼")
        shapes.push(html`<text x="${centreX}" y="${captionY}" text-anchor="middle" font-size="9" fill="${captionColor}" aria-hidden="true">${captionText}</text>`)
      }

      parts.push(html`<g class="bar-group-el" part="bar-group" tabindex="-1" role="button" aria-label="${label}" data-mark="sprint:${index}"><title>${label}</title>${shapes}</g>`)
      parts.push(html`<text x="${centreX}" y="${barBase + 16}" text-anchor="middle" font-size="10" fill="var(--mj-text-muted)"><title>${sprint.name}</title>${truncateMiddle(sprint.name, labelChars)}</text>`)

      averagePoints.push({ x: centreX, y: valueToY(rollingAverages[index]) })
    })

    if (showAverage === true && averagePoints.length > 1) {
      const path = averagePoints.map((point) => `${point.x},${point.y}`).join(" ")
      parts.push(html`<polyline part="average-line" points="${path}" stroke="var(--mj-color-warning)" stroke-width="2" fill="none" pointer-events="none" aria-hidden="true"/>`)
      averagePoints.forEach((point) => {
        parts.push(html`<circle cx="${point.x}" cy="${point.y}" r="3" fill="var(--mj-color-warning)" pointer-events="none" aria-hidden="true"/>`)
      })
    }

    this.renderSvg(this._svg, totalWidth, SVG_H, html`${parts}`, this._selectedKey)
    if (this._selectedKey !== null) {
      const selectedMark = this._svg.querySelector("[data-selected='true']")
      this._readout.textContent = selectedMark !== null ? selectedMark.getAttribute("aria-label") : ""
    }

    const summary = t("mj.velocityChart.summary", { count: sprints.length, unit: unit, window: rollingWindow })
    this._wrapper.setAttribute("aria-label", summary)
    this._svg.setAttribute("aria-label", t("mj.velocityChart.svgLabel", { summary: summary }))
    return
  }

  _buildTable(sprints, rollingAverages) {
    const rows = sprints.map((sprint, index) => {
      const difference = sprint.completed - sprint.committed
      const row = html`<tr><td>${sprint.name}</td><td>${formatNumber(sprint.committed)}</td><td>${formatNumber(sprint.completed)}</td><td>${difference >= 0 ? "+" : ""}${formatNumber(difference)}</td><td>${formatNumber(Math.round(rollingAverages[index]))}</td></tr>`
      return row
    })
    this._tableBody.innerHTML = String(html`${rows}`)
    return
  }

  _onMarkActivate(mark) {
    const key = mark.getAttribute("data-mark")
    const index = Number(key.slice(key.indexOf(":") + 1))
    const source = this._data !== null && Array.isArray(this._data.sprints) === true ? this._data.sprints : []
    const sprint = source[index]

    if (sprint !== undefined) {
      this._selectedSprint = sprint
      this._selectedKey = key
      markSelection(this._svg, key)
      this._readout.textContent = mark.getAttribute("aria-label")
      this.emit("mj-sprint-select", { sprint: sprint })
    }
    return
  }
}
