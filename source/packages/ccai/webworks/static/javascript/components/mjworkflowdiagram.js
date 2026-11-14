/*
 * mjworkflowdiagram.js
 *
 * <mj-workflow-diagram> -- state machine or cross-actor swimlane process flow.
 * Nodes vary by type: start (filled circle), end (double circle), decision
 * (diamond), state (rectangle). The current state, whatever its type, has a
 * pulsing ring.
 *
 * Layout: states are placed in columns by their longest path from the start
 * states, ignoring the transitions that loop back, so a rework loop does not
 * collapse the diagram. A transition that loops back is drawn as a return
 * edge around the nodes and a self-transition as a loop above its node. In
 * swimlane mode (diagram-type="swimlane" with `actors`) the column still
 * comes from the flow and the actor only selects the lane; states without a
 * known actor go to an "Unassigned" lane.
 *
 * The SVG is a labelled group whose states and transitions are keyboard
 * reachable (one tab stop, arrow keys between marks). A definition list with
 * the same structure can be disclosed from the toolbar.
 *
 * Data: `data` property, `src` attribute or inline JSON child --
 *   { states: [{ id, name, type, actor, description }],
 *     transitions: [{ from, to, label }], actors: [{ id, name }] }
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

const NODE_W = 120;
const NODE_H = 44;
const NODE_GAP_X = 64;
const NODE_GAP_Y = 20;
const SWIMLANE_LABEL_W = 100;
const LANE_PAD = 16;
const PAD = 20;
const CIRCLE_R = 15;
const FALLBACK_LANE_ID = "__mj-unassigned__";

/* Display text of the state types. */
const TYPE_LABEL_KEYS = {
  start:    "mj.workflowDiagram.type.start",
  end:      "mj.workflowDiagram.type.end",
  decision: "mj.workflowDiagram.type.decision",
  state:    "mj.workflowDiagram.type.state"
};

const STYLES = `
${PM_CHART_STYLES}
.edge-el .edge-hit { stroke: transparent; stroke-width: 24px; fill: none; pointer-events: stroke; }
.edge-el[data-selected="true"] .edge-line { stroke: var(--mj-accent); stroke-width: 3; }
.node-el[data-selected="true"] .node-frame { stroke: var(--mj-text); stroke-width: 3; }
.edge-label { paint-order: stroke; stroke: var(--mj-bg); stroke-width: 3px; stroke-linejoin: round; }
@keyframes mj-current-pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
.current-pulse { animation: mj-current-pulse var(--mj-current-state-pulse, 1.5s) ease-in-out infinite; }
@media (prefers-reduced-motion: reduce) { .current-pulse { animation: none; } }
`;

export class MjWorkflowDiagram extends PmChartElement {
  static tagName = "mj-workflow-diagram";
  static styles = STYLES;
  static watched = ["diagram-type", "current-state", "show-labels"];

  constructor() {
    super()
    this._selectedNode = null
    this._selectedTransition = null
    this._selectedKey = null

    /* The current-state value the diagram shows; a change emits mj-state-change. */
    this._shownCurrentState = ""

    /* The last unknown current-state id that was warned about. */
    this._warnedCurrentState = null

    this._listId = nextId("mj-wd-list")
    this._detailId = nextId("mj-wd-detail")
    this._arrowId = nextId("mj-wd-arrow")
  }

  render() {
    const markup = html`
      <div class="wrapper" part="wrapper" role="group" aria-label="${t("mj.workflowDiagram.label")}">
        <div class="toolbar" part="toolbar">
          <button class="chart-button btn-toggle-list" type="button" aria-controls="${this._listId}" aria-expanded="false">${t("mj.workflowDiagram.showAccessibleList")}</button>
        </div>
        <div class="chart-scroll svg-wrap" part="canvas">
          <svg part="svg" role="group" aria-label="${t("mj.workflowDiagram.label")}"></svg>
          ${emptyStateMarkup()}
        </div>
        ${detailPanelMarkup({ headingId: this._detailId, part: "detail-panel", slotName: "node-detail", placement: "inline" })}
        <div id="${this._listId}" class="a11y-list-wrap" hidden>
          <dl part="a11y-list"></dl>
        </div>
      </div>`
    return markup
  }

  afterRender() {
    this._svg = this.$("svg")
    this._wrapper = this.$(".wrapper")
    this._listEl = this.$("dl")
    this._shownCurrentState = this.getAttribute("current-state") || ""

    this._detail = new DetailPanel(this, this.$(".detail-panel"), () => {
      this._onDetailClosed()
    })

    wireMarks(this, this._svg, (mark) => {
      this._onMarkActivate(mark)
    }, (key) => {
      this._activeMarkKey = key
    })

    this.setupChart({
      alternativeButton: this.$(".btn-toggle-list"),
      alternativeRegion: this.$(`#${this._listId}`)
    })
    return
  }

  get selectedNode() {
    return this._selectedNode
  }

  get selectedTransition() {
    return this._selectedTransition
  }

  onDataChanged() {
    this._selectedNode = null
    this._selectedTransition = null
    this._selectedKey = null
    this._warnedCurrentState = null
    if (this._detail !== undefined) {
      this._detail.close(false)
    }
    return
  }

  onDataDrawn() {
    const data = this._data
    const states = Array.isArray(data.states) === true ? data.states : []
    const transitions = Array.isArray(data.transitions) === true ? data.transitions : []
    const actors = Array.isArray(data.actors) === true ? data.actors : []
    this.emit("mj-data-load", { states: states.length, transitions: transitions.length, actors: actors.length })
    return
  }

  onChartAttributeChanged(name, oldValue, newValue) {
    if (name === "current-state") {
      const current = newValue !== null ? newValue : ""
      if (current !== this._shownCurrentState) {
        const previous = this._shownCurrentState
        this._shownCurrentState = current
        this.drawChart()
        if (this._data !== null) {
          const state = this._states().find((candidate) => toText(candidate.id) === current)
          this.emit("mj-state-change", { from: previous, to: current })
          announce(t("mj.workflowDiagram.currentStateAnnouncement", { name: state !== undefined ? state.name : current }), "polite")
        }
      }
      return
    }

    this.drawChart()
    return
  }

  _onDetailClosed() {
    const hadNode = this._selectedNode !== null
    this._selectedNode = null
    this._selectedTransition = null
    this._selectedKey = null
    markSelection(this._svg, null)
    if (hadNode === true) {
      this.emit("mj-node-deselect", {})
    }
    return
  }

  _states() {
    const source = this._data !== null && Array.isArray(this._data.states) === true ? this._data.states : []
    const states = source.map((state, index) => {
      const safe = state !== null && typeof state === "object" ? state : {}
      const hasId = safe.id !== undefined && safe.id !== null
      const hasName = safe.name !== undefined && safe.name !== null && toText(safe.name).length > 0
      const id = hasId === true ? safe.id : (hasName === true ? safe.name : `state-${index + 1}`)
      const type = safe.type === "start" || safe.type === "end" || safe.type === "decision" ? safe.type : "state"
      let actor = null
      if (safe.actor !== undefined && safe.actor !== null) {
        actor = safe.actor
      } else if (safe.actorId !== undefined && safe.actorId !== null) {
        actor = safe.actorId
      }
      const described = { source: state, index: index, id: id, name: hasName === true ? toText(safe.name) : toText(id), type: type, actor: actor, description: safe.description }
      return described
    })
    return states
  }

  _transitions() {
    const source = this._data !== null && Array.isArray(this._data.transitions) === true ? this._data.transitions : []
    const transitions = source.map((transition, index) => {
      const safe = transition !== null && typeof transition === "object" ? transition : {}
      const described = { source: transition, index: index, from: safe.from, to: safe.to, label: toText(safe.label) }
      return described
    })
    return transitions
  }

  /* Half the width of the shape drawn for a state type, for edge anchors. */
  _shapeHalfWidth(type) {
    let half = NODE_W / 2
    if (type === "start" || type === "end") {
      half = CIRCLE_R
    } else if (type === "decision") {
      half = NODE_W / 2 - 4
    }
    return half
  }

  /*
   * Positions for every state: { centerX, centerY } keyed by id, plus the
   * lanes drawn in swimlane mode and the overall size.
   */
  _layoutNodes(states, transitions, actors) {
    const swimlane = this.getAttribute("diagram-type") === "swimlane" && actors.length > 0
    const startIds = states.filter((state) => state.type === "start").map((state) => state.id)
    const graph = layoutLayeredGraph(states.map((state) => state.id), transitions, { nodeHeight: NODE_H, rowGap: NODE_GAP_Y, rootIds: startIds })

    const topMargin = PAD + (graph.backEdgeCount > 0 ? 10 + graph.backEdgeCount * 10 : 0) + 14
    const rightMargin = PAD + (graph.backEdgeCount > 0 ? 16 + graph.backEdgeCount * 6 : 0)
    const originX = swimlane === true ? SWIMLANE_LABEL_W + PAD : PAD
    const levelX = (level) => {
      const x = originX + level * (NODE_W + NODE_GAP_X)
      return x
    }

    const positions = new Map()
    const lanes = []
    let contentHeight = graph.height

    if (swimlane === false) {
      states.forEach((state) => {
        const node = graph.nodes.get(state.id)
        positions.set(state.id, { level: node.level, centerX: levelX(node.level) + NODE_W / 2, centerY: topMargin + node.centerY })
      })
    } else {
      const laneIndex = new Map()
      actors.forEach((actor) => {
        const safe = actor !== null && typeof actor === "object" ? actor : {}
        const id = safe.id !== undefined && safe.id !== null ? safe.id : safe.name
        laneIndex.set(id, lanes.length)
        lanes.push({ id: id, name: toText(safe.name !== undefined && safe.name !== null ? safe.name : id), cells: new Map(), top: 0, height: 0 })
      })

      /* Each lane stacks the states that share a column. */
      states.forEach((state) => {
        let lane = laneIndex.has(state.actor) === true ? lanes[laneIndex.get(state.actor)] : null
        if (lane === null) {
          if (laneIndex.has(FALLBACK_LANE_ID) === false) {
            laneIndex.set(FALLBACK_LANE_ID, lanes.length)
            lanes.push({ id: FALLBACK_LANE_ID, name: t("mj.workflowDiagram.unassigned"), cells: new Map(), top: 0, height: 0 })
          }
          lane = lanes[laneIndex.get(FALLBACK_LANE_ID)]
        }
        const level = graph.nodes.get(state.id).level
        if (lane.cells.has(level) === false) {
          lane.cells.set(level, [])
        }
        lane.cells.get(level).push(state.id)
      })

      let cursor = topMargin
      lanes.forEach((lane) => {
        let tallest = 1
        lane.cells.forEach((cell) => {
          tallest = Math.max(tallest, cell.length)
        })
        lane.top = cursor
        lane.height = LANE_PAD * 2 + tallest * NODE_H + (tallest - 1) * NODE_GAP_Y
        lane.cells.forEach((cell, level) => {
          const cellHeight = cell.length * NODE_H + (cell.length - 1) * NODE_GAP_Y
          const cellTop = lane.top + (lane.height - cellHeight) / 2
          cell.forEach((stateId, position) => {
            positions.set(stateId, { level: level, centerX: levelX(level) + NODE_W / 2, centerY: cellTop + position * (NODE_H + NODE_GAP_Y) + NODE_H / 2 })
          })
        })
        cursor = cursor + lane.height
      })
      contentHeight = cursor - topMargin
    }

    const result = {
      swimlane: swimlane,
      graph: graph,
      positions: positions,
      lanes: lanes,
      topMargin: topMargin,
      levelX: levelX,
      width: Math.max(320, levelX(graph.levelCount - 1) + NODE_W + rightMargin),
      height: Math.max(160, topMargin + contentHeight + PAD)
    }
    return result
  }

  drawChart() {
    const states = this._states()
    const transitions = this._transitions()
    const actors = this._data !== null && Array.isArray(this._data.actors) === true ? this._data.actors : []
    const currentStateId = this._chartReady === true ? this._shownCurrentState : (this.getAttribute("current-state") || "")
    const showLabels = this.enabledUnlessFalse("show-labels")

    this._buildList(states, transitions)

    if (states.length === 0) {
      this.renderSvg(this._svg, 0, 0, "", null)
      this._svg.toggleAttribute("hidden", true)
      setEmptyState(this, "empty")
      this._wrapper.setAttribute("aria-label", t("mj.workflowDiagram.noStates"))
      return
    }

    this._svg.toggleAttribute("hidden", false)
    setEmptyState(this, "ready")

    const layout = this._layoutNodes(states, transitions, actors)
    const stateById = new Map()
    states.forEach((state) => {
      if (stateById.has(state.id) === false) {
        stateById.set(state.id, state)
      }
    })

    /* An unknown current-state id is ignored, with one console warning. */
    const currentKnown = states.some((state) => toText(state.id) === currentStateId)
    if (currentStateId.length > 0 && currentKnown === false && this._warnedCurrentState !== currentStateId) {
      this._warnedCurrentState = currentStateId
      console.warn(`mj-workflow-diagram: current-state "${currentStateId}" does not match any state id.`)
    }

    const parts = []
    parts.push(html`<defs><marker id="${this._arrowId}" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="var(--mj-text-muted)"/></marker></defs>`)

    if (layout.swimlane === true) {
      layout.lanes.forEach((lane, laneNumber) => {
        parts.push(html`<rect x="0" y="${lane.top}" width="${layout.width}" height="${lane.height}" fill="${laneNumber % 2 === 0 ? "var(--mj-bg)" : "var(--mj-bg-subtle)"}" stroke="var(--mj-border)" stroke-width="1" part="swimlane" aria-hidden="true"/>`)
        parts.push(html`<text x="${SWIMLANE_LABEL_W - 8}" y="${lane.top + lane.height / 2 + 4}" text-anchor="end" font-size="11" fill="var(--mj-text-muted)" part="swimlane-label"><title>${lane.name}</title>${truncateLabel(lane.name, 13)}</text>`)
      })
    }

    /* Transitions first, so the nodes sit on top of their ends. */
    let backLane = 0
    transitions.forEach((transition) => {
      const route = layout.graph.routes[transition.index]
      if (route.kind === "dangling") {
        return
      }
      const fromState = stateById.get(transition.from)
      const toState = stateById.get(transition.to)
      const from = layout.positions.get(transition.from)
      const to = layout.positions.get(transition.to)
      const fromRight = from.centerX + this._shapeHalfWidth(fromState.type)
      const toLeft = to.centerX - this._shapeHalfWidth(toState.type)
      let pathData = ""
      let labelX = 0
      let labelY = 0
      let dashed = false

      if (route.kind === "self") {
        /* A loop above the node. */
        const top = from.centerY - (fromState.type === "start" || fromState.type === "end" ? CIRCLE_R : NODE_H / 2)
        pathData = `M${from.centerX - 14},${top} C${from.centerX - 26},${top - 30} ${from.centerX + 26},${top - 30} ${from.centerX + 14},${top - 2}`
        labelX = from.centerX
        labelY = top - 26
      } else if (route.kind === "back") {
        /* A return edge: out to the right, over the top, back in from the left. */
        const laneY = layout.topMargin - 10 - backLane * 10
        const exitX = from.centerX + NODE_W / 2 + 12 + backLane * 6
        const entryX = to.centerX - NODE_W / 2 - 12 - backLane * 6
        backLane = backLane + 1
        pathData = roundedPath([{ x: fromRight, y: from.centerY }, { x: exitX, y: from.centerY }, { x: exitX, y: laneY }, { x: entryX, y: laneY }, { x: entryX, y: to.centerY }, { x: toLeft - 2, y: to.centerY }], 6)
        labelX = (exitX + entryX) / 2
        labelY = laneY - 4
        dashed = true
      } else if (layout.swimlane === true) {
        const span = to.level - from.level
        if (span > 1 && Math.abs(to.centerY - from.centerY) < NODE_H) {
          /* Skips a column in the same row: bow over the node in between. */
          const bow = NODE_H / 2 + 14
          pathData = `M${fromRight},${from.centerY} C${fromRight + 40},${from.centerY - bow * 2} ${toLeft - 40},${to.centerY - bow * 2} ${toLeft - 2},${to.centerY}`
          labelX = (fromRight + toLeft) / 2
          labelY = Math.min(from.centerY, to.centerY) - bow * 1.5 + 2
        } else {
          pathData = forwardEdgePath(fromRight, from.centerY, toLeft - 2, to.centerY, [])
          labelX = (fromRight + toLeft) / 2
          labelY = (from.centerY + to.centerY) / 2 - 6
        }
      } else {
        const waypoints = route.waypoints.map((slot) => ({ left: layout.levelX(slot.level), right: layout.levelX(slot.level) + NODE_W, y: layout.topMargin + slot.centerY }))
        pathData = forwardEdgePath(fromRight, from.centerY, toLeft - 2, to.centerY, waypoints)
        const firstTargetX = waypoints.length > 0 ? waypoints[0].left : toLeft
        const firstTargetY = waypoints.length > 0 ? waypoints[0].y : to.centerY
        labelX = (fromRight + firstTargetX) / 2
        labelY = (from.centerY + firstTargetY) / 2 - 6
      }

      const ariaLabel = transition.label.length > 0
        ? t("mj.workflowDiagram.transitionLabelNamed", { from: fromState.name, to: toState.name, label: transition.label })
        : t("mj.workflowDiagram.transitionLabel", { from: fromState.name, to: toState.name })
      const labelMarkup = showLabels === true && transition.label.length > 0 ? html`<text class="edge-label" x="${labelX}" y="${labelY}" text-anchor="middle" font-size="9" fill="var(--mj-text-muted)" part="transition-label">${truncateLabel(transition.label, 16)}</text>` : html``
      parts.push(html`<g class="edge-el" tabindex="-1" role="button" aria-label="${ariaLabel}" data-mark="transition:${transition.index}"><title>${ariaLabel}</title><path class="edge-hit" d="${pathData}"/><path class="edge-line" part="transition-edge" d="${pathData}" stroke="var(--mj-border-strong)" stroke-width="1.5" stroke-dasharray="${dashed === true ? "5 4" : "none"}" fill="none" marker-end="url(#${this._arrowId})"/>${labelMarkup}</g>`)
    })

    states.forEach((state) => {
      const position = layout.positions.get(state.id)
      if (position === undefined || stateById.get(state.id) !== state) {
        return
      }
      const centerX = position.centerX
      const centerY = position.centerY
      const isCurrent = currentKnown === true && toText(state.id) === currentStateId
      const typeText = t(TYPE_LABEL_KEYS[state.type])
      const ariaLabel = isCurrent === true
        ? t("mj.workflowDiagram.stateLabelCurrent", { name: state.name, type: typeText })
        : t("mj.workflowDiagram.stateLabel", { name: state.name, type: typeText })
      const fill = isCurrent === true ? "var(--mj-color-info-surface)" : "var(--mj-surface)"
      const stroke = isCurrent === true ? "var(--mj-color-info)" : "var(--mj-border-strong)"
      const shapes = []

      if (state.type === "start") {
        shapes.push(html`<circle class="node-frame" cx="${centerX}" cy="${centerY}" r="${CIRCLE_R}" fill="var(--mj-text)" stroke="${stroke}" stroke-width="1.5" part="start-node"/>`)
        shapes.push(html`<text x="${centerX}" y="${centerY + CIRCLE_R + 12}" text-anchor="middle" font-size="10" fill="var(--mj-text-muted)">${truncateLabel(state.name, 16)}</text>`)
        if (isCurrent === true) {
          shapes.push(html`<circle class="current-pulse" cx="${centerX}" cy="${centerY}" r="${CIRCLE_R + 5}" fill="none" stroke="var(--mj-color-info)" stroke-width="2.5" aria-hidden="true"/>`)
        }
      } else if (state.type === "end") {
        shapes.push(html`<circle class="node-frame" cx="${centerX}" cy="${centerY}" r="${CIRCLE_R}" fill="var(--mj-surface)" stroke="var(--mj-text)" stroke-width="3" part="end-node"/>`)
        shapes.push(html`<circle cx="${centerX}" cy="${centerY}" r="${CIRCLE_R - 5}" fill="var(--mj-text)"/>`)
        shapes.push(html`<text x="${centerX}" y="${centerY + CIRCLE_R + 12}" text-anchor="middle" font-size="10" fill="var(--mj-text-muted)">${truncateLabel(state.name, 16)}</text>`)
        if (isCurrent === true) {
          shapes.push(html`<circle class="current-pulse" cx="${centerX}" cy="${centerY}" r="${CIRCLE_R + 5}" fill="none" stroke="var(--mj-color-info)" stroke-width="2.5" aria-hidden="true"/>`)
        }
      } else if (state.type === "decision") {
        const halfWidth = NODE_W / 2 - 4
        const halfHeight = NODE_H / 2 - 2
        shapes.push(html`<polygon class="node-frame" points="${centerX - halfWidth},${centerY} ${centerX},${centerY - halfHeight} ${centerX + halfWidth},${centerY} ${centerX},${centerY + halfHeight}" fill="${fill}" stroke="${stroke}" stroke-width="1.5" part="decision-node"/>`)
        shapes.push(html`<text x="${centerX}" y="${centerY + 4}" text-anchor="middle" font-size="10" fill="var(--mj-text)">${truncateLabel(state.name, 10)}</text>`)
        if (isCurrent === true) {
          shapes.push(html`<polygon class="current-pulse" points="${centerX - halfWidth - 6},${centerY} ${centerX},${centerY - halfHeight - 4} ${centerX + halfWidth + 6},${centerY} ${centerX},${centerY + halfHeight + 4}" fill="none" stroke="var(--mj-color-info)" stroke-width="2.5" aria-hidden="true"/>`)
        }
      } else {
        shapes.push(html`<rect class="node-frame" x="${centerX - NODE_W / 2}" y="${centerY - NODE_H / 2}" width="${NODE_W}" height="${NODE_H}" rx="6" fill="${fill}" stroke="${stroke}" stroke-width="1.5"/>`)
        shapes.push(html`<text x="${centerX}" y="${centerY + 4}" text-anchor="middle" font-size="11" fill="var(--mj-text)">${truncateLabel(state.name, 16)}</text>`)
        if (isCurrent === true) {
          shapes.push(html`<rect class="current-pulse" x="${centerX - NODE_W / 2 - 3}" y="${centerY - NODE_H / 2 - 3}" width="${NODE_W + 6}" height="${NODE_H + 6}" rx="8" fill="none" stroke="var(--mj-color-info)" stroke-width="2.5" aria-hidden="true"/>`)
        }
      }

      if (isCurrent === true) {
        parts.push(html`<g class="node-el" part="state-node-current" tabindex="-1" role="button" aria-label="${ariaLabel}" aria-current="step" data-mark="node:${state.index}"><title>${ariaLabel}</title>${shapes}</g>`)
      } else {
        parts.push(html`<g class="node-el" part="state-node" tabindex="-1" role="button" aria-label="${ariaLabel}" data-mark="node:${state.index}"><title>${ariaLabel}</title>${shapes}</g>`)
      }
    })

    this.renderSvg(this._svg, layout.width, layout.height, html`${parts}`, this._selectedKey)

    const stateCount = t("mj.workflowDiagram.stateCount", { count: states.length })
    const transitionCount = t("mj.workflowDiagram.transitionCount", { count: transitions.length })
    const summary = actors.length > 0
      ? t("mj.workflowDiagram.summaryActors", { states: stateCount, transitions: transitionCount, actors: t("mj.workflowDiagram.actorCount", { count: actors.length }) })
      : t("mj.workflowDiagram.summary", { states: stateCount, transitions: transitionCount })
    this._wrapper.setAttribute("aria-label", summary)
    this._svg.setAttribute("aria-label", t("mj.workflowDiagram.svgLabel", { summary: summary }))
    return
  }

  _buildList(states, transitions) {
    const names = new Map()
    states.forEach((state) => {
      names.set(state.id, state.name)
    })
    const outgoing = new Map()
    transitions.forEach((transition) => {
      if (names.has(transition.from) === false || names.has(transition.to) === false) {
        return
      }
      if (outgoing.has(transition.from) === false) {
        outgoing.set(transition.from, [])
      }
      const target = transition.label.length > 0
        ? t("mj.workflowDiagram.listTargetNamed", { name: names.get(transition.to), label: transition.label })
        : names.get(transition.to)
      outgoing.get(transition.from).push(target)
    })

    const items = states.map((state) => {
      const targets = outgoing.has(state.id) === true ? outgoing.get(state.id) : []
      const description = targets.length > 0 ? t("mj.workflowDiagram.listGoesTo", { targets: targets.join("; ") }) : t("mj.workflowDiagram.listNoOutgoing")
      const item = html`<dt>${t("mj.workflowDiagram.listState", { name: state.name, type: t(TYPE_LABEL_KEYS[state.type]) })}</dt><dd>${description}</dd>`
      return item
    })
    this._listEl.innerHTML = String(html`${items}`)
    return
  }

  _onMarkActivate(mark) {
    const key = mark.getAttribute("data-mark")
    const separator = key.indexOf(":")
    const kind = key.slice(0, separator)
    const index = Number(key.slice(separator + 1))
    const findOpener = () => {
      const opener = findMark(this._svg, key)
      return opener
    }

    if (kind === "node") {
      const state = this._states()[index]
      if (state !== undefined) {
        this._selectedNode = state.source
        this._selectedTransition = null
        this._selectedKey = key
        markSelection(this._svg, key)
        const hasDescription = state.description !== undefined && state.description !== null && toText(state.description).length > 0
        const content = html`<p><strong>${t("mj.workflowDiagram.typeField")}</strong> ${t(TYPE_LABEL_KEYS[state.type])}</p>${state.actor !== null ? html`<p><strong>${t("mj.workflowDiagram.actorField")}</strong> ${toText(state.actor)}</p>` : html``}${hasDescription === true ? html`<p>${toText(state.description)}</p>` : html``}`
        this._detail.open(state.name, content, findOpener)
        this.emit("mj-node-select", { node: state.source })
      }
    } else if (kind === "transition") {
      const transition = this._transitions()[index]
      if (transition !== undefined) {
        const states = this._states()
        const fromState = states.find((state) => state.id === transition.from)
        const toState = states.find((state) => state.id === transition.to)
        this._selectedTransition = transition.source
        this._selectedNode = null
        this._selectedKey = key
        markSelection(this._svg, key)
        const content = html`<p><strong>${t("mj.workflowDiagram.fromField")}</strong> ${fromState !== undefined ? fromState.name : toText(transition.from)}</p><p><strong>${t("mj.workflowDiagram.toField")}</strong> ${toState !== undefined ? toState.name : toText(transition.to)}</p>${transition.label.length > 0 ? html`<p><strong>${t("mj.workflowDiagram.labelField")}</strong> ${transition.label}</p>` : html``}`
        this._detail.open(t("mj.workflowDiagram.transitionTitle"), content, findOpener)
        this.emit("mj-transition-select", { transition: transition.source })
      }
    }
    return
  }
}
