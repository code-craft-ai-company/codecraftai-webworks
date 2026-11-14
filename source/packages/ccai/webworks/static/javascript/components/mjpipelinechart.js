/*
 * mjpipelinechart.js
 *
 * <mj-pipeline-chart> -- CI/CD pipeline stage-flow diagram.
 *
 * Stages are laid out by topological level, so stages that run in parallel
 * are stacked in one column and fan-out / fan-in edges are routed between
 * the boxes. Without an `edges` array the stages form a sequence. Gate
 * diamonds sit after the stage they follow and show their status; a pending
 * gate offers Approve / Reject unless the chart is `readonly`.
 *
 * The SVG is a labelled group whose stage and gate marks are keyboard
 * reachable (one tab stop, arrow keys between marks). An ordered list with
 * the same stages and gates can be disclosed above the chart.
 *
 * Data: `data` property, `src` attribute or inline JSON child --
 *   { stages: [{ id, name, status, duration, logs }],
 *     gates: [{ name, fromStage, status }], edges: [{ from, to }] }
 */

import { nextId } from "../core/mjelement.js";
import { html } from "../core/html.js";
import { announce } from "../core/announcer.js";
import { t } from "../core/intl.js";
import {
  PM_CHART_STYLES, PmChartElement, DetailPanel, detailPanelMarkup, emptyStateMarkup,
  findMark, forwardEdgePath, layoutLayeredGraph, markSelection, roundedPath,
  setEmptyState, toText, truncateLabel, wireMarks
} from "./pmchartsupport.js";

const STAGE_W_FULL = 140;
const STAGE_H_FULL = 64;
const STAGE_W_COMPACT = 112;
const STAGE_H_COMPACT = 48;
const STAGE_GAP_X = 64;
const STAGE_GAP_Y = 20;
const GATE_SIZE = 28;
const PAD = 24;
const CHAR_W = 6.8;

const STATUS_ICONS = {
  pending:   "○",
  running:   "◎",
  passed:    "✓",
  failed:    "✗",
  cancelled: "⊘",
  skipped:   "→"
};

const STATUS_COLORS = {
  pending:   "var(--mj-text-muted)",
  running:   "var(--mj-color-info)",
  passed:    "var(--mj-color-success)",
  failed:    "var(--mj-color-danger)",
  cancelled: "var(--mj-text-muted)",
  skipped:   "var(--mj-text-muted)"
};

/* Display text of the known stage statuses; any other status shows as given. */
const STATUS_LABEL_KEYS = {
  pending:   "mj.pipelineChart.status.pending",
  running:   "mj.pipelineChart.status.running",
  passed:    "mj.pipelineChart.status.passed",
  failed:    "mj.pipelineChart.status.failed",
  cancelled: "mj.pipelineChart.status.cancelled",
  skipped:   "mj.pipelineChart.status.skipped"
};

const GATE_STATUS_LABEL_KEYS = {
  pending:  "mj.pipelineChart.gateStatus.pending",
  approved: "mj.pipelineChart.gateStatus.approved",
  rejected: "mj.pipelineChart.gateStatus.rejected",
  auto:     "mj.pipelineChart.gateStatus.auto"
};

/* The display text of a stage status. */
function stageStatusText(status) {
  const known = Object.prototype.hasOwnProperty.call(STATUS_LABEL_KEYS, status) === true
  const text = known === true ? t(STATUS_LABEL_KEYS[status]) : status
  return text
}

/* The display text of a gate status. */
function gateStatusText(status) {
  const known = Object.prototype.hasOwnProperty.call(GATE_STATUS_LABEL_KEYS, status) === true
  const text = known === true ? t(GATE_STATUS_LABEL_KEYS[status]) : status
  return text
}

const GATE_STATUS = {
  pending:  { icon: "◎", color: "var(--mj-color-warning)" },
  approved: { icon: "✓", color: "var(--mj-color-success)" },
  rejected: { icon: "✗", color: "var(--mj-color-danger)" },
  auto:     { icon: "→", color: "var(--mj-text-muted)" }
};

const STYLES = `
${PM_CHART_STYLES}
.toggle-btn { margin: var(--mj-space-2) var(--mj-space-3); align-self: flex-start; }
.log-panel { padding: var(--mj-space-3); background: var(--mj-bg-subtle); border-block-start: 1px solid var(--mj-border); font-family: var(--mj-font-mono); font-size: var(--mj-font-size-xs); max-block-size: 200px; overflow-y: auto; white-space: pre-wrap; overflow-wrap: anywhere; }
.log-title { font-family: var(--mj-font-sans); font-weight: var(--mj-font-weight-medium); margin-block-end: var(--mj-space-1); }
.stage-box[data-selected="true"] .stage-frame { stroke-width: 4; }
.gate-box[data-selected="true"] .gate-frame { stroke-width: 4; }
.gate-actions { display: flex; gap: var(--mj-space-2); margin-block-start: var(--mj-space-2); }
`;

export class MjPipelineChart extends PmChartElement {
  static tagName = "mj-pipeline-chart";
  static styles = STYLES;
  static watched = ["density", "readonly", "live"];

  constructor() {
    super()
    this._selectedStage = null
    this._selectedGateIndex = -1
    this._selectedKey = null

    /* Gate statuses decided in this chart, by gate index; host data is not changed. */
    this._gateDecisions = new Map()

    /* Stage statuses of the previous data, by stage id, for live change events. */
    this._previousStatuses = new Map()

    this._listId = nextId("mj-pc-list")
    this._gateDetailId = nextId("mj-pc-gate")
    this._arrowId = nextId("mj-pc-arrow")
  }

  render() {
    const legendItems = Object.keys(STATUS_ICONS).map((status) => {
      const item = html`<span class="legend-item" part="legend-item"><span aria-hidden="true" style="color:${STATUS_COLORS[status]}">${STATUS_ICONS[status]}</span> <span>${stageStatusText(status)}</span></span>`
      return item
    })

    const markup = html`
      <div class="wrapper" part="wrapper" role="group" aria-label="${t("mj.pipelineChart.label")}">
        <button class="chart-button toggle-btn" type="button" aria-controls="${this._listId}" aria-expanded="false">${t("mj.pipelineChart.showAccessibleList")}</button>
        <div class="chart-scroll">
          <svg part="svg" role="group" aria-label="${t("mj.pipelineChart.label")}"></svg>
          ${emptyStateMarkup()}
        </div>
        <div class="log-panel" part="log-panel" role="region" aria-label="${t("mj.pipelineChart.stageLogs")}" tabindex="0" hidden>
          <div class="log-title"></div>
          <div class="log-text"></div>
        </div>
        ${detailPanelMarkup({ headingId: this._gateDetailId, part: "gate-detail", slotName: "gate-detail", placement: "inline" })}
        <div class="legend" part="status-legend" role="group" aria-label="${t("mj.pipelineChart.statusLegend")}">${legendItems}</div>
        <div id="${this._listId}" class="a11y-list-wrap" hidden>
          <ol part="a11y-list"></ol>
        </div>
      </div>`
    return markup
  }

  afterRender() {
    this._svg = this.$("svg")
    this._wrapper = this.$(".wrapper")
    this._logPanel = this.$(".log-panel")
    this._logTitle = this.$(".log-title")
    this._logText = this.$(".log-text")
    this._listEl = this.$("ol")

    this._gateDetail = new DetailPanel(this, this.$(".detail-panel"), () => {
      this._selectedGateIndex = -1
      if (this._selectedStage === null) {
        this._selectedKey = null
        markSelection(this._svg, null)
      }
    })

    /* Approve / Reject buttons are rebuilt per gate; one listener serves them. */
    this.listen(this.$(".detail-content"), "click", (event) => {
      const button = event.target.closest("[data-gate-action]")
      if (button !== null) {
        this._onGateAction(button.getAttribute("data-gate-action"))
      }
    })

    wireMarks(this, this._svg, (mark) => {
      this._onMarkActivate(mark)
    }, (key) => {
      this._activeMarkKey = key
    })

    this.listen(this.shadowRoot, "keydown", (event) => {
      if (event.key === "Escape" && this._selectedStage !== null) {
        event.preventDefault()
        this._deselectStage(true)
      }
    })

    this.setupChart({
      alternativeButton: this.$(".toggle-btn"),
      alternativeRegion: this.$(`#${this._listId}`)
    })
    return
  }

  get selectedStage() {
    return this._selectedStage
  }

  /*
   * failed    any stage failed
   * running   otherwise, any stage running
   * cancelled otherwise, any stage cancelled
   * passed    every stage passed or skipped, and at least one passed
   * skipped   every stage skipped
   * pending   anything else, including a pipeline without stages
   */
  get overallStatus() {
    const stages = this._stages()
    const statuses = stages.map((stage) => stage.status)
    let overall = "pending"

    if (statuses.indexOf("failed") >= 0) {
      overall = "failed"
    } else if (statuses.indexOf("running") >= 0) {
      overall = "running"
    } else if (statuses.indexOf("cancelled") >= 0) {
      overall = "cancelled"
    } else if (statuses.length > 0 && statuses.every((status) => status === "passed" || status === "skipped") === true) {
      overall = statuses.indexOf("passed") >= 0 ? "passed" : "skipped"
    }

    return overall
  }

  onDataChanged() {
    this._selectedStage = null
    this._selectedGateIndex = -1
    this._selectedKey = null
    this._gateDecisions = new Map()
    if (this._gateDetail !== undefined) {
      this._gateDetail.close(false)
      this._logPanel.hidden = true
    }
    return
  }

  onDataDrawn() {
    const stages = this._stages()
    const data = this._data

    /* Live mode: report the stages whose status differs from the previous data. */
    if (this.flag("live") === true) {
      stages.forEach((stage) => {
        const previous = this._previousStatuses.get(stage.id)
        if (previous !== undefined && previous !== stage.status) {
          this.emit("mj-status-change", { stageId: stage.id, previous: previous, current: stage.status })
          announce(t("mj.pipelineChart.statusChanged", { name: stage.name, status: stageStatusText(stage.status) }), stage.status === "failed" ? "assertive" : "polite")
        }
      })
    }
    this._previousStatuses = new Map()
    stages.forEach((stage) => {
      this._previousStatuses.set(stage.id, stage.status)
    })

    this.emit("mj-data-load", { stages: stages.length, runId: toText(data.id) })
    return
  }

  _stages() {
    const source = this._data !== null && Array.isArray(this._data.stages) === true ? this._data.stages : []
    const stages = source.map((stage, index) => {
      const safe = stage !== null && typeof stage === "object" ? stage : {}
      const hasId = safe.id !== undefined && safe.id !== null
      const hasName = safe.name !== undefined && safe.name !== null && toText(safe.name).length > 0
      const id = hasId === true ? safe.id : (hasName === true ? safe.name : `stage-${index + 1}`)
      const described = {
        source: stage,
        index: index,
        id: id,
        name: hasName === true ? toText(safe.name) : toText(id),
        status: safe.status !== undefined && safe.status !== null && toText(safe.status).length > 0 ? toText(safe.status) : "pending",
        duration: toText(safe.duration),
        logs: safe.logs !== undefined && safe.logs !== null ? toText(safe.logs) : null
      }
      return described
    })
    return stages
  }

  _gates() {
    const source = this._data !== null && Array.isArray(this._data.gates) === true ? this._data.gates : []
    const gates = source.map((gate, index) => {
      const safe = gate !== null && typeof gate === "object" ? gate : {}
      const declared = safe.status !== undefined && safe.status !== null && toText(safe.status).length > 0 ? toText(safe.status) : "pending"
      const described = {
        source: gate,
        index: index,
        name: safe.name !== undefined && safe.name !== null && toText(safe.name).length > 0 ? toText(safe.name) : t("mj.pipelineChart.defaultGateName"),
        fromStage: safe.fromStage,
        status: this._gateDecisions.has(index) === true ? this._gateDecisions.get(index) : declared
      }
      return described
    })
    return gates
  }

  /* Declared edges, or a chain through the stages when none are declared. */
  _edges(stages) {
    const declared = this._data !== null && Array.isArray(this._data.edges) === true ? this._data.edges : []
    let edges = declared

    if (declared.length === 0) {
      edges = []
      for (let index = 0; index < stages.length - 1; index = index + 1) {
        edges.push({ from: stages[index].id, to: stages[index + 1].id })
      }
    }

    return edges
  }

  drawChart() {
    const stages = this._stages()
    const gates = this._gates()

    this._buildList(stages, gates)

    if (stages.length === 0) {
      this.renderSvg(this._svg, 0, 0, "", null)
      this._svg.toggleAttribute("hidden", true)
      setEmptyState(this, "empty")
      this._wrapper.setAttribute("aria-label", t("mj.pipelineChart.noStages"))
      return
    }

    this._svg.toggleAttribute("hidden", false)
    setEmptyState(this, "ready")

    const compact = this.getAttribute("density") === "compact"
    const stageWidth = compact === true ? STAGE_W_COMPACT : STAGE_W_FULL
    const stageHeight = compact === true ? STAGE_H_COMPACT : STAGE_H_FULL
    const edges = this._edges(stages)
    const layout = layoutLayeredGraph(stages.map((stage) => stage.id), edges, { nodeHeight: stageHeight, rowGap: STAGE_GAP_Y })

    /* Return edges run above the stages; reserve a lane for each. */
    const topMargin = PAD + (layout.backEdgeCount > 0 ? 10 + layout.backEdgeCount * 10 : 0)
    const rightMargin = PAD + (layout.backEdgeCount > 0 ? 16 + layout.backEdgeCount * 6 : 0)
    const levelX = (level) => {
      const x = PAD + level * (stageWidth + STAGE_GAP_X)
      return x
    }
    const totalWidth = levelX(layout.levelCount - 1) + stageWidth + rightMargin
    const totalHeight = topMargin + layout.height + PAD + 14

    const boxOf = (id) => {
      const node = layout.nodes.get(id)
      const box = { left: levelX(node.level), right: levelX(node.level) + stageWidth, centerY: topMargin + node.centerY }
      return box
    }

    const parts = []
    parts.push(html`<defs><marker id="${this._arrowId}" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="var(--mj-text-muted)"/></marker></defs>`)

    /* Edges first, so the stage boxes sit on top of their ends. */
    let backLane = 0
    layout.routes.forEach((route) => {
      if (route.kind === "forward") {
        const from = boxOf(route.from)
        const to = boxOf(route.to)
        const waypoints = route.waypoints.map((slot) => ({ left: levelX(slot.level), right: levelX(slot.level) + stageWidth, y: topMargin + slot.centerY }))
        parts.push(html`<path part="edge" d="${forwardEdgePath(from.right, from.centerY, to.left - 2, to.centerY, waypoints)}" stroke="var(--mj-border-strong)" stroke-width="2" fill="none" marker-end="url(#${this._arrowId})" aria-hidden="true"/>`)
      } else if (route.kind === "back") {
        const from = boxOf(route.from)
        const to = boxOf(route.to)
        const laneY = topMargin - 10 - backLane * 10
        const exitX = from.right + 12 + backLane * 6
        const entryX = to.left - 12 - backLane * 6
        backLane = backLane + 1
        const points = [{ x: from.right, y: from.centerY }, { x: exitX, y: from.centerY }, { x: exitX, y: laneY }, { x: entryX, y: laneY }, { x: entryX, y: to.centerY }, { x: to.left - 2, y: to.centerY }]
        parts.push(html`<path part="edge" data-return-edge="true" d="${roundedPath(points, 6)}" stroke="var(--mj-border-strong)" stroke-width="2" stroke-dasharray="5 4" fill="none" marker-end="url(#${this._arrowId})" aria-hidden="true"/>`)
      }
    })

    const nameChars = Math.max(4, Math.floor((stageWidth - 16) / CHAR_W))
    stages.forEach((stage) => {
      if (layout.nodes.has(stage.id) === false) {
        return
      }
      const box = boxOf(stage.id)
      const top = box.centerY - stageHeight / 2
      const color = STATUS_COLORS[stage.status] !== undefined ? STATUS_COLORS[stage.status] : STATUS_COLORS.pending
      const icon = STATUS_ICONS[stage.status] !== undefined ? STATUS_ICONS[stage.status] : STATUS_ICONS.pending
      const statusText = stageStatusText(stage.status)
      const label = stage.duration.length > 0
        ? t("mj.pipelineChart.stageLabelDuration", { name: stage.name, status: statusText, duration: stage.duration })
        : t("mj.pipelineChart.stageLabel", { name: stage.name, status: statusText })
      const nameY = top + (compact === true ? 18 : 22)
      const statusY = top + stageHeight - (compact === true ? 10 : 18)

      parts.push(html`<g class="stage-box" part="stage-node" tabindex="-1" role="button" aria-label="${label}" aria-expanded="false" data-mark="stage:${stage.index}"><title>${label}</title><rect class="stage-frame" x="${box.left}" y="${top}" width="${stageWidth}" height="${stageHeight}" rx="6" ry="6" fill="var(--mj-surface)" stroke="${color}" stroke-width="2"/><text x="${box.left + stageWidth / 2}" y="${nameY}" text-anchor="middle" font-size="12" fill="var(--mj-text)" font-weight="500">${truncateLabel(stage.name, nameChars)}</text><text x="${box.left + 14}" y="${statusY}" font-size="14" fill="${color}" aria-hidden="true">${icon}</text><text x="${box.left + 32}" y="${statusY}" font-size="11" fill="${color}">${truncateLabel(statusText, Math.max(3, nameChars - 4))}</text></g>`)
    })

    /* Gates, in the gap after the stage they follow. */
    const gatesPerStage = new Map()
    gates.forEach((gate) => {
      if (layout.nodes.has(gate.fromStage) === false) {
        return
      }
      const box = boxOf(gate.fromStage)
      const stacked = gatesPerStage.has(gate.fromStage) === true ? gatesPerStage.get(gate.fromStage) : 0
      gatesPerStage.set(gate.fromStage, stacked + 1)
      const half = GATE_SIZE / 2
      const centerX = box.right + STAGE_GAP_X / 2
      const centerY = box.centerY + stacked * (GATE_SIZE + 14)
      const config = GATE_STATUS[gate.status] !== undefined ? GATE_STATUS[gate.status] : GATE_STATUS.pending
      const gateStatus = gateStatusText(gate.status)
      const label = t("mj.pipelineChart.gateLabel", { name: gate.name, status: gateStatus })
      parts.push(html`<g class="gate-box" tabindex="-1" role="button" aria-label="${label}" data-mark="gate:${gate.index}"><title>${label}</title><polygon class="gate-frame" part="gate-node" points="${centerX},${centerY - half} ${centerX + half},${centerY} ${centerX},${centerY + half} ${centerX - half},${centerY}" fill="var(--mj-bg-muted)" stroke="${config.color}" stroke-width="2"/><text x="${centerX}" y="${centerY + 4}" text-anchor="middle" font-size="12" fill="${config.color}" aria-hidden="true">${config.icon}</text><text x="${centerX}" y="${centerY + half + 11}" text-anchor="middle" font-size="9" fill="${config.color}">${truncateLabel(gateStatus, 10)}</text></g>`)
    })

    this.renderSvg(this._svg, totalWidth, totalHeight, html`${parts}`, this._selectedKey)
    this._syncStageExpansion(this._logPanel.hidden === false ? this._selectedKey : null)

    const summary = t("mj.pipelineChart.summary", { count: stages.length, status: stageStatusText(this.overallStatus) })
    this._wrapper.setAttribute("aria-label", summary)
    this._svg.setAttribute("aria-label", t("mj.pipelineChart.svgLabel", { summary: summary }))
    return
  }

  _buildList(stages, gates) {
    const stageItems = stages.map((stage) => {
      const statusText = stageStatusText(stage.status)
      const text = stage.duration.length > 0
        ? t("mj.pipelineChart.listStageDuration", { name: stage.name, status: statusText, duration: stage.duration })
        : t("mj.pipelineChart.listStage", { name: stage.name, status: statusText })
      const item = html`<li>${text}</li>`
      return item
    })
    const gateItems = gates.map((gate) => {
      const fromStage = stages.find((stage) => stage.id === gate.fromStage)
      const gateStatus = gateStatusText(gate.status)
      const text = fromStage !== undefined
        ? t("mj.pipelineChart.listGateAfter", { name: gate.name, stage: fromStage.name, status: gateStatus })
        : t("mj.pipelineChart.listGate", { name: gate.name, status: gateStatus })
      const item = html`<li>${text}</li>`
      return item
    })
    this._listEl.innerHTML = String(html`${stageItems}${gateItems}`)
    return
  }

  _onMarkActivate(mark) {
    const key = mark.getAttribute("data-mark")
    const separator = key.indexOf(":")
    const kind = key.slice(0, separator)
    const index = Number(key.slice(separator + 1))

    if (kind === "stage") {
      const stage = this._stages()[index]
      if (stage !== undefined) {
        this._selectStage(stage, key)
      }
    } else if (kind === "gate") {
      const gate = this._gates()[index]
      if (gate !== undefined) {
        this._openGate(gate, key)
      }
    }
    return
  }

  /* Select a stage: every selection updates the log panel or hides it. */
  _selectStage(stage, key) {
    this._gateDetail.close(false)
    this._selectedStage = stage.source
    this._selectedKey = key
    markSelection(this._svg, key)

    const hasLogs = stage.logs !== null
    if (hasLogs === true) {
      this._logTitle.textContent = t("mj.pipelineChart.stageLogsTitle", { name: stage.name })
      this._logText.textContent = stage.logs
      this._logPanel.setAttribute("aria-label", t("mj.pipelineChart.stageLogsTitle", { name: stage.name }))
    }
    this._logPanel.hidden = hasLogs === false
    this._syncStageExpansion(hasLogs === true ? key : null)

    this.emit("mj-stage-select", { stage: stage.source })
    return
  }

  /* aria-expanded is true only on the stage whose logs are showing. */
  _syncStageExpansion(expandedKey) {
    const marks = this._svg.querySelectorAll(".stage-box")
    for (let index = 0; index < marks.length; index = index + 1) {
      const mark = marks[index]
      const expanded = expandedKey !== null && mark.getAttribute("data-mark") === expandedKey
      mark.setAttribute("aria-expanded", expanded === true ? "true" : "false")
      /* Stages carry aria-expanded, so the selection is shown by data-selected only. */
      if (mark.getAttribute("data-mark") === this._selectedKey) {
        mark.setAttribute("data-selected", "true")
      } else {
        mark.removeAttribute("data-selected")
      }
    }
    return
  }

  _deselectStage(notify) {
    const hadSelection = this._selectedStage !== null
    this._selectedStage = null
    this._selectedKey = null
    this._logPanel.hidden = true
    markSelection(this._svg, null)
    this._syncStageExpansion(null)
    if (notify === true && hadSelection === true) {
      this.emit("mj-stage-deselect", {})
    }
    return
  }

  _openGate(gate, key) {
    if (this._selectedStage !== null) {
      this._deselectStage(true)
    }
    this._selectedGateIndex = gate.index
    this._selectedKey = key
    markSelection(this._svg, key)

    const fromStage = this._stages().find((stage) => stage.id === gate.fromStage)
    const canDecide = gate.status === "pending" && this.flag("readonly") === false
    const content = html`<p><strong>${t("mj.pipelineChart.statusField")}</strong> <span class="gate-status-text">${gateStatusText(gate.status)}</span></p>${fromStage !== undefined ? html`<p><strong>${t("mj.pipelineChart.afterStageField")}</strong> ${fromStage.name}</p>` : html``}${canDecide === true ? html`<div class="gate-actions" part="gate-controls"><button class="chart-button" type="button" data-gate-action="approve">${t("mj.pipelineChart.approve")}</button><button class="chart-button" type="button" data-gate-action="reject">${t("mj.pipelineChart.reject")}</button></div>` : html``}`
    this._gateDetail.open(t("mj.pipelineChart.gateTitle", { name: gate.name }), content, () => {
      const opener = findMark(this._svg, key)
      return opener
    })
    return
  }

  /*
   * Approve or reject the open gate. `mj-gate-approve` is cancelable: when
   * the host cancels it the gate stays pending. Otherwise the decision is
   * shown here; the host's data object is left as it was.
   */
  _onGateAction(action) {
    const gate = this._gates()[this._selectedGateIndex]
    if (gate === undefined || gate.status !== "pending" || this.flag("readonly") === true) {
      return
    }

    const proceed = this.emit("mj-gate-approve", { gate: gate.source, action: action }, { cancelable: true })
    if (proceed === false) {
      return
    }

    const status = action === "approve" ? "approved" : "rejected"
    const key = `gate:${gate.index}`
    this._gateDecisions.set(gate.index, status)
    this._gateDetail.close(false)
    this.drawChart()

    const mark = findMark(this._svg, key)
    if (mark !== null) {
      mark.focus()
    }
    announce(t("mj.pipelineChart.gateDecided", { name: gate.name, status: gateStatusText(status) }), "polite")
    return
  }
}
