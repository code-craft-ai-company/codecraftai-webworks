/*
 * mjdependencygraph.js
 *
 * <mj-dependency-graph> -- a convenience wrapper for
 * <mj-chart type="dependency-graph"> with the work-item data shape of this
 * component family.
 *
 * Drawing (labelled boxes in longest-path columns, status colours, the
 * critical path, dashed cycle edges), keyboard support, the data table and
 * data loading are the dependency-graph chart type's
 * (charts/core/renderers/network.js); the shared wrapper base
 * (pmchartwrapper.js) adds the toolbar, the selection and the detail
 * panel. This file maps the documented data onto the chart type, its
 * events back onto the documented ones, and names the cycles in a banner.
 *
 * Data: `data` property, `src` attribute or inline JSON child --
 *   { nodes: [{ id, name, status, estimate }], edges: [{ from, to }],
 *     criticalPath: [nodeId, ...] }
 * An edge runs from the prerequisite to the dependent item.
 *
 * Attributes: show-critical-path (as on the chart type).
 */

import { html } from "../core/html.js";
import { t } from "../core/intl.js";
import { PmChartWrapper } from "./pmchartwrapper.js";
import { toText } from "./pmchartsupport.js";
import "../charts/core/renderers/network.js";

const BANNER_STYLES = `
.cycle-banner { flex: 0 0 auto; background: var(--mj-color-danger-surface); color: var(--mj-color-danger); padding: var(--mj-space-2) var(--mj-space-3); font-size: var(--mj-font-size-xs); font-weight: var(--mj-font-weight-medium); overflow-wrap: anywhere; }
`;

/* Display text of the known statuses; any other status is shown as given. */
const STATUS_LABEL_KEYS = {
  todo:          "mj.dependencyGraph.statusTodo",
  "in-progress": "mj.dependencyGraph.statusInProgress",
  done:          "mj.dependencyGraph.statusDone",
  blocked:       "mj.dependencyGraph.statusBlocked"
};

function statusText(status) {
  const known = Object.prototype.hasOwnProperty.call(STATUS_LABEL_KEYS, status) === true
  const text = known === true ? t(STATUS_LABEL_KEYS[status]) : status
  return text
}

/* A node field that holds text. */
function hasText(value) {
  const present = value !== undefined && value !== null && toText(value).length > 0
  return present
}

export class MjDependencyGraph extends PmChartWrapper {
  static tagName = "mj-dependency-graph";
  static styles = PmChartWrapper.styles + BANNER_STYLES;
  static chartTypeKey = "dependency-graph";
  static labelKey = "mj.dependencyGraph.label";
  static rendererEvents = ["mj-chart-node-click", "mj-chart-cycle-detect"];
  static toolbarSlot = null;
  static detailPanel = { part: "detail-panel", slot: "node-detail", placement: "inline" };
  static deselectEvent = "mj-node-deselect";

  constructor() {
    super()
    this._cycles = []
  }

  get selectedNode() {
    return this.selectedOf("node")
  }

  /* Every cycle of the current data, as arrays of node ids. */
  get cycles() {
    return this._cycles
  }

  /* The graph does not zoom (a tall graph scrolls). */
  get zoom() {
    return 1
  }

  renderExtras() {
    const markup = html`<div class="cycle-banner" part="cycle-banner" role="alert" hidden></div>`
    return markup
  }

  afterRender() {
    super.afterRender()
    this._banner = this.$(".cycle-banner")
    this._syncBanner()
    return
  }

  /* The node id the data gives a node (its id, else its name, else node-N). */
  _nodeId(node, index) {
    let id = `node-${index + 1}`
    if (node.id !== undefined && node.id !== null) {
      id = node.id
    } else if (hasText(node.name) === true) {
      id = node.name
    }
    return id
  }

  adaptData(data) {
    this._cycles = []
    const nodes = Array.isArray(data.nodes) === true ? data.nodes : []
    const edges = Array.isArray(data.edges) === true ? data.edges : []
    const adapted = {
      nodes: nodes.map((node, index) => {
        const source = node !== null && typeof node === "object" ? node : {}
        const id = this._nodeId(source, index)
        return {
          id: String(id), label: hasText(source.name) === true ? toText(source.name) : toText(id),
          status: hasText(source.status) === true ? toText(source.status) : "todo"
        }
      }),
      links: edges.map((edge) => {
        const source = edge !== null && typeof edge === "object" ? edge : {}
        return { source: source.from, target: source.to }
      }),
      criticalPath: Array.isArray(data.criticalPath) === true ? data.criticalPath : []
    }
    return adapted
  }

  loadDetail(data) {
    const detail = {
      nodes: Array.isArray(data.nodes) === true ? data.nodes.length : 0,
      edges: Array.isArray(data.edges) === true ? data.edges.length : 0,
      hasCycles: this._cycles.length > 0
    }
    return detail
  }

  /* After mj-data-load: the cycle event, once per data. */
  onDataLoaded(data) {
    this._syncBanner()
    if (this._cycles.length > 0) {
      this.emit("mj-cycle-detected", { cycles: this._cycles })
    }
    return
  }

  onRendererEvent(name, detail) {
    let selection = null

    if (name === "mj-chart-cycle-detect") {
      this._cycles = Array.isArray(detail.cycles) === true ? detail.cycles : []
      this._syncBanner()
    } else {
      const data = this.data !== null && typeof this.data === "object" ? this.data : {}
      const node = Array.isArray(data.nodes) === true ? data.nodes[detail.index] : undefined
      if (node !== undefined && node !== null && typeof node === "object") {
        const status = hasText(node.status) === true ? toText(node.status) : "todo"
        const hasEstimate = node.estimate !== undefined && node.estimate !== null
        selection = {
          key: `node:${detail.index}`, kind: "node", item: node,
          title: hasText(node.name) === true ? toText(node.name) : toText(this._nodeId(node, detail.index)),
          content: html`<p><strong>${t("mj.dependencyGraph.detailStatus")}</strong> ${statusText(status)}</p>${hasEstimate === true ? html`<p><strong>${t("mj.dependencyGraph.detailEstimate")}</strong> ${toText(node.estimate)}</p>` : html``}`,
          eventName: "mj-node-select", eventDetail: { node: node }
        }
      }
    }
    return selection
  }

  /* The banner is a live alert: its text only changes when the cycles do. */
  _syncBanner() {
    if (this._banner === undefined || this._banner === null) {
      return
    }
    let text = ""
    if (this._cycles.length > 0) {
      const names = new Map()
      const data = this.data !== null && typeof this.data === "object" ? this.data : {}
      const nodes = Array.isArray(data.nodes) === true ? data.nodes : []
      nodes.forEach((node, index) => {
        const source = node !== null && typeof node === "object" ? node : {}
        names.set(String(this._nodeId(source, index)), hasText(source.name) === true ? toText(source.name) : String(this._nodeId(source, index)))
      })
      const described = this._cycles.map((cycle) => {
        const path = cycle.concat(cycle.length > 0 ? [cycle[0]] : [])
        return path.map((id) => (names.has(String(id)) === true ? names.get(String(id)) : toText(id))).join(" → ")
      }).join("; ")
      text = t("mj.dependencyGraph.cycleDetected", { cycles: described })
    }
    if (this._banner.textContent !== text) {
      this._banner.textContent = text
    }
    this._banner.hidden = text.length === 0
    return
  }
}
