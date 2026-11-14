/*
 * mjbranchgraph.js
 *
 * <mj-branch-graph> -- branch network / commit history graph.
 *
 * Renders branch lanes, commit nodes, merge edges, milestone markers, and
 * phase bands on a shared linear time axis. The SVG is a labelled group
 * whose commit and marker marks are keyboard reachable (one tab stop, arrow
 * keys between marks); decorative shapes inside it are aria-hidden. A data
 * table with the same commits can be disclosed from the toolbar.
 *
 * Data: `data` property, `src` attribute or inline JSON child --
 *   { branches: [{ id, name }], commits: [{ id, sha, branch, date, message,
 *     author }], merges: [{ from, to }], markers: [{ name, date, type }],
 *     phases: [{ name, start, end }] }
 * A `YYYY-MM-DD` date is a local calendar day.
 */

import { nextId } from "../core/mjelement.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";
import {
  DAY_MS, PM_CHART_STYLES, PmChartElement, DetailPanel, chartEndTime, chartTime,
  detailPanelMarkup, emptyStateMarkup, findMark, formatChartDate, markSelection,
  resolveTimeRange, seriesColor, setEmptyState, timeTicks, toText, truncateLabel,
  wireMarks
} from "./pmchartsupport.js";

const LANE_HEIGHT_FULL = 48;
const LANE_HEIGHT_COMPACT = 32;
const LANE_GAP = 8;
const LABEL_W = 120;
const LABEL_W_MIN = 64;
const AXIS_H = 44;
const MARKER_ROW_Y = 14;
const TICK_ROW_Y = 34;
const COMMIT_R = 6;
const PLOT_PAD = 12;
const EDGE_PAD = 8;
const MIN_PX_PER_DAY = 4;
const MIN_PLOT_W = 160;
const TICK_SPACING = 80;
const CHAR_W = 6.5;

const STYLES = `
${PM_CHART_STYLES}
.lane-label { font-size: var(--mj-font-size-xs); fill: var(--mj-text); }
.axis-tick { font-size: var(--mj-font-size-xs); fill: var(--mj-text-muted); }
.phase-label { font-size: 10px; fill: var(--mj-text-muted); }
.milestone-line { stroke-dasharray: 4 3; }
.commit-node[data-selected="true"] { stroke: var(--mj-text); stroke-width: 3; }
.marker-mark[data-selected="true"] .marker-label { font-weight: var(--mj-font-weight-bold); text-decoration: underline; }
`;

export class MjBranchGraph extends PmChartElement {
  static tagName = "mj-branch-graph";
  static styles = STYLES;
  static watched = ["start-date", "end-date", "density", "readonly", "today-marker"];

  constructor() {
    super()
    this._selectedNode = null
    this._selectedMarker = null
    this._selectedKey = null
    this._tableId = nextId("mj-bg-table")
    this._detailId = nextId("mj-bg-detail")
  }

  render() {
    const chartLabel = t("mj.branchGraph.label")

    const markup = html`
      <div class="wrapper" part="wrapper" role="group" aria-label="${chartLabel}">
        <div class="toolbar" part="toolbar">
          <button class="chart-button btn-toggle-table" type="button" aria-controls="${this._tableId}" aria-expanded="false">${t("mj.branchGraph.showDataTable")}</button>
          <span class="toolbar-spacer"></span>
          <slot name="legend"></slot>
        </div>
        <div class="chart-frame">
          <div class="chart-scroll chart-area" part="chart-area">
            <svg part="svg" role="group" aria-label="${chartLabel}"></svg>
            ${emptyStateMarkup()}
          </div>
          ${detailPanelMarkup({ headingId: this._detailId, part: "detail-panel", slotName: "detail-panel", placement: "floating" })}
        </div>
        <div id="${this._tableId}" class="a11y-table-wrap" hidden>
          <table part="data-table">
            <caption>${t("mj.branchGraph.tableCaption")}</caption>
            <thead><tr><th scope="col">${t("mj.branchGraph.columnBranch")}</th><th scope="col">${t("mj.branchGraph.columnSha")}</th><th scope="col">${t("mj.branchGraph.columnMessage")}</th><th scope="col">${t("mj.branchGraph.columnAuthor")}</th><th scope="col">${t("mj.branchGraph.columnDate")}</th></tr></thead>
            <tbody class="table-body"></tbody>
          </table>
        </div>
      </div>`
    return markup
  }

  afterRender() {
    this._svg = this.$("svg")
    this._wrapper = this.$(".wrapper")
    this._chartArea = this.$(".chart-area")
    this._tableBody = this.$(".table-body")

    this._detail = new DetailPanel(this, this.$(".detail-panel"), () => {
      this._onDetailClosed()
    })

    wireMarks(this, this._svg, (mark) => {
      this._onMarkActivate(mark)
    }, (key) => {
      this._activeMarkKey = key
    })

    this.setupChart({
      alternativeButton: this.$(".btn-toggle-table"),
      alternativeRegion: this.$(`#${this._tableId}`),
      resizeTarget: this._chartArea
    })
    return
  }

  get selectedNode() {
    return this._selectedNode
  }

  get selectedMarker() {
    return this._selectedMarker
  }

  onDataChanged() {
    this._clearSelection()
    if (this._detail !== undefined) {
      this._detail.close(false)
    }
    return
  }

  onDataDrawn() {
    const data = this._data
    const branches = Array.isArray(data.branches) === true ? data.branches : []
    const commits = Array.isArray(data.commits) === true ? data.commits : []
    this.emit("mj-data-load", { branches: branches.length, commits: commits.length })
    return
  }

  onChartAttributeChanged(name, oldValue, newValue) {
    if (name === "readonly" && this.flag("readonly") === true) {
      this._detail.close(false)
    }
    this.drawChart()
    return
  }

  _clearSelection() {
    this._selectedNode = null
    this._selectedMarker = null
    this._selectedKey = null
    return
  }

  /* The panel was closed: drop the selection and tell the host. */
  _onDetailClosed() {
    const node = this._selectedNode
    const marker = this._selectedMarker
    this._clearSelection()
    markSelection(this._svg, null)

    if (node !== null) {
      this.emit("mj-node-deselect", { node: node })
    } else if (marker !== null) {
      this.emit("mj-marker-deselect", { marker: marker })
    }
    return
  }

  _branchKey(branch) {
    const key = branch.id !== undefined && branch.id !== null ? branch.id : branch.name
    return key
  }

  _shortSha(commit) {
    const source = toText(commit.sha !== undefined && commit.sha !== null ? commit.sha : commit.id)
    const short = source.slice(0, 7)
    return short
  }

  drawChart() {
    const data = this._data !== null ? this._data : {}
    const branches = Array.isArray(data.branches) === true ? data.branches : []
    const commits = Array.isArray(data.commits) === true ? data.commits : []
    const merges = Array.isArray(data.merges) === true ? data.merges : []
    const markers = Array.isArray(data.markers) === true ? data.markers : []
    const phases = Array.isArray(data.phases) === true ? data.phases : []

    this._buildTable(commits, branches)

    if (branches.length === 0) {
      this.renderSvg(this._svg, 0, 0, "", null)
      this._svg.toggleAttribute("hidden", true)
      setEmptyState(this, "empty")
      this._wrapper.setAttribute("aria-label", t("mj.branchGraph.noDataLabel"))
      return
    }

    this._svg.toggleAttribute("hidden", false)
    setEmptyState(this, "ready")

    const readonly = this.flag("readonly")
    const laneHeight = this.getAttribute("density") === "compact" ? LANE_HEIGHT_COMPACT : LANE_HEIGHT_FULL
    const laneStep = laneHeight + LANE_GAP

    /* Time range: explicit attributes win, otherwise the extent of the data. */
    const commitTimes = commits.map((commit) => chartTime(commit.date))
    const range = resolveTimeRange(commitTimes, this.getAttribute("start-date"), this.getAttribute("end-date"), 0)
    const timeSpan = range.max - range.min

    const containerWidth = this._chartArea.clientWidth > 0 ? this._chartArea.clientWidth : 800
    const labelWidth = Math.max(LABEL_W_MIN, Math.min(LABEL_W, Math.round(containerWidth * 0.3)))
    const fittedPlotWidth = containerWidth - labelWidth - EDGE_PAD
    const scaledPlotWidth = Math.round((timeSpan / DAY_MS) * MIN_PX_PER_DAY)
    const plotWidth = Math.max(MIN_PLOT_W, fittedPlotWidth, scaledPlotWidth)
    const totalWidth = labelWidth + plotWidth + EDGE_PAD
    const lanesHeight = branches.length * laneStep
    const totalHeight = AXIS_H + lanesHeight

    const plotLeft = labelWidth
    const plotRight = labelWidth + plotWidth
    const innerWidth = plotWidth - PLOT_PAD * 2
    const timeToX = (time) => {
      const x = plotLeft + PLOT_PAD + ((time - range.min) / timeSpan) * innerWidth
      return x
    }
    const inRange = (time) => {
      const inside = Number.isNaN(time) === false && time >= range.min && time <= range.max
      return inside
    }

    const branchIndex = new Map()
    branches.forEach((branch, index) => {
      branchIndex.set(this._branchKey(branch), index)
    })
    const laneY = (index) => {
      const y = AXIS_H + index * laneStep + laneHeight / 2
      return y
    }

    const clipId = `${this._detailId}-clip`
    const parts = []

    parts.push(html`<defs><clipPath id="${clipId}"><rect x="${plotLeft}" y="0" width="${plotWidth}" height="${totalHeight}"/></clipPath></defs>`)

    /* Phase bands with their names. */
    phases.forEach((phase, index) => {
      const startTime = chartTime(phase.start)
      const endTime = chartEndTime(phase.end)
      if (Number.isNaN(startTime) === true || Number.isNaN(endTime) === true) {
        return
      }
      const x1 = Math.max(plotLeft, timeToX(Math.max(startTime, range.min)))
      const x2 = Math.min(plotRight, timeToX(Math.min(endTime, range.max)))
      if (x2 <= x1) {
        return
      }
      parts.push(html`<rect class="phase-band" part="phase-band" x="${x1}" y="${AXIS_H}" width="${x2 - x1}" height="${lanesHeight}" fill="${seriesColor(index)}" opacity="0.10" aria-hidden="true"/>`)
      const phaseName = toText(phase.name)
      if (phaseName.length > 0) {
        const maxChars = Math.max(1, Math.floor((x2 - x1 - 8) / CHAR_W))
        parts.push(html`<text class="phase-label" part="phase-label" x="${x1 + 4}" y="${AXIS_H + 11}"><title>${phaseName}</title>${truncateLabel(phaseName, maxChars)}</text>`)
      }
    })

    /* Time axis. */
    const ticks = timeTicks(range.min, range.max, Math.floor(innerWidth / TICK_SPACING))
    ticks.times.forEach((time) => {
      const x = timeToX(time)
      parts.push(html`<line x1="${x}" y1="${AXIS_H - 6}" x2="${x}" y2="${totalHeight}" stroke="var(--mj-border)" stroke-width="1" aria-hidden="true"/>`)
      parts.push(html`<text class="axis-tick" part="time-axis" x="${x}" y="${TICK_ROW_Y}" text-anchor="middle">${formatChartDate(time, ticks.labelOptions)}</text>`)
    })

    /* Lanes and their labels. */
    const labelChars = Math.max(3, Math.floor((labelWidth - 16) / CHAR_W))
    branches.forEach((branch, index) => {
      const y = laneY(index)
      const branchName = toText(branch.name !== undefined && branch.name !== null ? branch.name : branch.id)
      parts.push(html`<line x1="${plotLeft}" y1="${y}" x2="${plotRight}" y2="${y}" stroke="${seriesColor(index)}" stroke-width="2" part="lane" aria-hidden="true"/>`)
      parts.push(html`<text class="lane-label" part="lane-label" x="${labelWidth - 8}" y="${y}" text-anchor="end" dominant-baseline="middle"><title>${branchName}</title>${truncateLabel(branchName, labelChars)}</text>`)
    })

    /* Commit positions: commits that share a lane and a date are spread out. */
    const placed = []
    const groups = new Map()
    commits.forEach((commit, index) => {
      const lane = branchIndex.get(commit.branch)
      const time = chartTime(commit.date)
      if (lane === undefined || inRange(time) === false) {
        return
      }
      const entry = { commit: commit, index: index, lane: lane, x: timeToX(time), y: laneY(lane) }
      const groupKey = `${lane}:${Math.round(entry.x)}`
      if (groups.has(groupKey) === false) {
        groups.set(groupKey, [])
      }
      groups.get(groupKey).push(entry)
      placed.push(entry)
    })
    groups.forEach((group) => {
      if (group.length > 1) {
        const spacing = Math.min(COMMIT_R * 2 + 2, 80 / (group.length - 1))
        const groupWidth = spacing * (group.length - 1)
        /* Centre the run on the date, then slide it back inside the plot. */
        let firstX = group[0].x - groupWidth / 2
        firstX = Math.min(firstX, plotRight - COMMIT_R - groupWidth)
        firstX = Math.max(firstX, plotLeft + COMMIT_R)
        group.forEach((entry, position) => {
          entry.x = firstX + position * spacing
        })
      }
    })
    const placedByCommit = new Map()
    placed.forEach((entry) => {
      const commitKey = entry.commit.id !== undefined && entry.commit.id !== null ? entry.commit.id : entry.commit.sha
      placedByCommit.set(commitKey, entry)
    })

    /* Merge edges between placed commits. */
    merges.forEach((merge) => {
      const from = placedByCommit.get(merge.from)
      const to = placedByCommit.get(merge.to)
      if (from === undefined || to === undefined) {
        return
      }
      const midX = (from.x + to.x) / 2
      parts.push(html`<path class="merge-edge" part="merge-edge" clip-path="url(#${clipId})" d="M${from.x},${from.y} C${midX},${from.y} ${midX},${to.y} ${to.x},${to.y}" stroke="var(--mj-border-strong)" stroke-width="1.5" fill="none" aria-hidden="true"/>`)
    })

    /* Commit nodes. */
    placed.forEach((entry) => {
      const commit = entry.commit
      const label = t("mj.branchGraph.commitLabel", { sha: this._shortSha(commit), message: toText(commit.message), date: formatChartDate(commit.date) })
      if (readonly === true) {
        parts.push(html`<circle class="commit-node" part="commit-node" cx="${entry.x}" cy="${entry.y}" r="${COMMIT_R}" fill="${seriesColor(entry.lane)}" stroke="var(--mj-surface)" stroke-width="2" role="img" aria-label="${label}"><title>${label}</title></circle>`)
      } else {
        parts.push(html`<circle class="commit-node" part="commit-node" cx="${entry.x}" cy="${entry.y}" r="${COMMIT_R}" fill="${seriesColor(entry.lane)}" stroke="var(--mj-surface)" stroke-width="2" tabindex="-1" role="button" aria-label="${label}" data-mark="commit:${entry.index}"><title>${label}</title></circle>`)
      }
    })

    /* Milestone markers: a full-height line plus a selectable flag and label. */
    let markerCount = 0
    markers.forEach((marker, index) => {
      const time = chartTime(marker.date)
      if (inRange(time) === false) {
        return
      }
      markerCount = markerCount + 1
      const x = timeToX(time)
      const color = this._markerColor(marker.type)
      const markerName = toText(marker.name)
      const label = t("mj.branchGraph.markerLabel", { name: markerName, type: this._markerTypeText(marker), date: formatChartDate(marker.date) })
      const labelText = truncateLabel(markerName, 24)
      const labelWidthPx = labelText.length * CHAR_W
      const flip = x + 10 + labelWidthPx > totalWidth - 2
      const textX = flip === true ? x - 10 : x + 10
      const anchor = flip === true ? "end" : "start"
      const flag = html`<polygon points="${x},${MARKER_ROW_Y - 10} ${x + 6},${MARKER_ROW_Y - 4} ${x},${MARKER_ROW_Y + 2} ${x - 6},${MARKER_ROW_Y - 4}" fill="${color}"/><text class="marker-label" x="${textX}" y="${MARKER_ROW_Y}" text-anchor="${anchor}" font-size="11" fill="${color}">${labelText}</text>`
      const line = html`<line class="milestone-line" x1="${x}" y1="${MARKER_ROW_Y}" x2="${x}" y2="${totalHeight}" stroke="${color}" stroke-width="2" pointer-events="none" aria-hidden="true"/>`

      if (readonly === true) {
        parts.push(html`<g class="marker-mark" part="milestone-marker" role="img" aria-label="${label}"><title>${label}</title>${line}${flag}</g>`)
      } else {
        parts.push(html`<g class="marker-mark" part="milestone-marker" tabindex="-1" role="button" aria-label="${label}" data-mark="marker:${index}"><title>${label}</title>${line}${flag}</g>`)
      }
    })

    /* Today line: on unless today-marker="false". */
    if (this.enabledUnlessFalse("today-marker") === true) {
      const now = Date.now()
      if (inRange(now) === true) {
        const todayX = timeToX(now)
        const flipToday = todayX + 40 > totalWidth
        parts.push(html`<line part="today-marker" x1="${todayX}" y1="${AXIS_H}" x2="${todayX}" y2="${totalHeight}" stroke="var(--mj-color-danger)" stroke-width="2" stroke-dasharray="6 3" aria-hidden="true"/>`)
        parts.push(html`<text x="${flipToday === true ? todayX - 4 : todayX + 4}" y="${totalHeight - 4}" text-anchor="${flipToday === true ? "end" : "start"}" font-size="10" fill="var(--mj-color-danger)">${t("mj.branchGraph.today")}</text>`)
      }
    }

    this.renderSvg(this._svg, totalWidth, totalHeight, html`${parts}`, this._selectedKey)

    const summary = t("mj.branchGraph.summary", {
      branches: t("mj.branchGraph.branchCount", { count: branches.length }),
      commits: t("mj.branchGraph.commitCount", { count: commits.length }),
      milestones: t("mj.branchGraph.milestoneCount", { count: markerCount })
    })
    this._wrapper.setAttribute("aria-label", summary)
    this._svg.setAttribute("aria-label", t("mj.branchGraph.svgLabel", { summary: summary }))
    return
  }

  /* Display text of a marker's type; "milestone" when it has none. */
  _markerTypeText(marker) {
    const hasType = marker.type !== undefined && marker.type !== null
    const text = hasType === true ? toText(marker.type) : t("mj.branchGraph.defaultMarkerType")
    return text
  }

  _markerColor(type) {
    let color = "var(--mj-color-info)"
    if (type === "release") {
      color = "var(--mj-color-success)"
    } else if (type === "freeze") {
      color = "var(--mj-color-warning)"
    }
    return color
  }

  _buildTable(commits, branches) {
    const branchNames = new Map()
    branches.forEach((branch) => {
      branchNames.set(this._branchKey(branch), toText(branch.name !== undefined && branch.name !== null ? branch.name : branch.id))
    })

    const rows = commits.map((commit) => {
      const branchName = branchNames.has(commit.branch) === true ? branchNames.get(commit.branch) : toText(commit.branch)
      const row = html`<tr><td>${branchName}</td><td>${this._shortSha(commit)}</td><td>${toText(commit.message)}</td><td>${toText(commit.author)}</td><td>${formatChartDate(commit.date)}</td></tr>`
      return row
    })
    this._tableBody.innerHTML = String(html`${rows}`)
    return
  }

  _onMarkActivate(mark) {
    const key = mark.getAttribute("data-mark")
    const separator = key.indexOf(":")
    const kind = key.slice(0, separator)
    const index = Number(key.slice(separator + 1))
    const data = this._data !== null ? this._data : {}
    const findOpener = () => {
      const opener = findMark(this._svg, key)
      return opener
    }

    if (kind === "commit") {
      const commits = Array.isArray(data.commits) === true ? data.commits : []
      const commit = commits[index]
      if (commit !== undefined) {
        this._selectedNode = commit
        this._selectedMarker = null
        this._selectedKey = key
        markSelection(this._svg, key)
        const content = html`<p><strong>${t("mj.branchGraph.detailBranch")}</strong> ${toText(commit.branch)}</p><p><strong>${t("mj.branchGraph.detailMessage")}</strong> ${toText(commit.message)}</p><p><strong>${t("mj.branchGraph.detailAuthor")}</strong> ${toText(commit.author)}</p><p><strong>${t("mj.branchGraph.detailDate")}</strong> ${formatChartDate(commit.date)}</p>`
        this._detail.open(t("mj.branchGraph.commitHeading", { sha: this._shortSha(commit) }), content, findOpener)
        this.emit("mj-node-select", { node: commit, branch: commit.branch })
      }
    } else if (kind === "marker") {
      const markers = Array.isArray(data.markers) === true ? data.markers : []
      const marker = markers[index]
      if (marker !== undefined) {
        this._selectedMarker = marker
        this._selectedNode = null
        this._selectedKey = key
        markSelection(this._svg, key)
        const content = html`<p><strong>${t("mj.branchGraph.detailType")}</strong> ${this._markerTypeText(marker)}</p><p><strong>${t("mj.branchGraph.detailDate")}</strong> ${formatChartDate(marker.date)}</p>`
        this._detail.open(toText(marker.name), content, findOpener)
        this.emit("mj-marker-select", { marker: marker })
      }
    }
    return
  }
}
