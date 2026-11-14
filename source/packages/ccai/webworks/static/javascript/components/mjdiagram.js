/*
 * mjdiagram.js
 *
 * <mj-diagram> -- accessible node/edge graph diagram with pluggable layout adapter,
 * keyboard pan/zoom, accessible node list, and selection panel. No layout engine
 * is bundled; the adapter is supplied by the host application. Without an
 * adapter a built-in layered SVG renderer draws the graph.
 *
 * Adapter contract
 *   Required: init(target, options), destroy(), setData(graph), setZoom(level),
 *             fit(), selectNode(id), deselectAll()
 *   Optional: resize(), panBy(dx, dy), clear(),
 *             on(eventName, handler) with the events
 *               "nodeSelect" handler(node)   "edgeSelect" handler(edge)
 *               "zoom"       handler(level)  "pan"        handler({ x, y })
 *   init options: { directed, interactive, minZoom, maxZoom, ...adapterOptions }
 *
 * Built-in renderer
 *   - Layering is cycle-safe: back edges are found with a depth-first search
 *     and left out of the layering, so any graph (cycles and self-loops
 *     included) is laid out in time linear in its size.
 *   - One zoom state: the scale of the SVG transform. It is reflected to the
 *     `zoom` attribute, the +/- buttons step from it, and it zooms about the
 *     centre of the viewport (or the pointer / pinch centre).
 *   - Pointer events drive panning, so mouse, pen and touch all work; two
 *     pointers pinch-zoom. The wheel zooms only while the diagram has focus
 *     or Ctrl / Meta is held, so the page can be scrolled across a diagram.
 *   - `interactive="false"` turns pan, zoom and node selection off;
 *     `directed="false"` draws edges without arrowheads.
 *
 * State that survives a reconnect lives in fields (graph, selection, adapter);
 * `afterRender` rebuilds the shadow DOM from them.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { t } from "../core/intl.js";
import { escapeHtml } from "../core/html.js";

/* ─── Built-in SVG renderer ──────────────────────────────────────────────── */

const SVG_NS = "http://www.w3.org/2000/svg";

const NODE_W = 140;
const NODE_H = 44;
const H_GAP = 80;   // horizontal gap between layers
const V_GAP = 32;   // vertical gap between nodes in the same layer
const FIT_MARGIN = 16;
const NODE_LABEL_MAX = 18;

const ZOOM_STEP = 0.25;
const WHEEL_ZOOM_STEP = 0.1;
const PAN_STEP_PX = 50;
const EVENT_DEBOUNCE_MS = 200;

function createSvg(name, attributes) {
    const element = document.createElementNS(SVG_NS, name)
    const names = Object.keys(attributes || {})
    for (let index = 0; index < names.length; index = index + 1) {
        element.setAttribute(names[index], String(attributes[names[index]]))
    }
    return element
}

/**
    The nodes of a graph with a usable id, first occurrence of each id only.

    :param graph: { nodes, edges } or null

    :returns: Array of node objects
*/
function uniqueNodes(graph) {
    const source = graph !== null && graph !== undefined && Array.isArray(graph.nodes) === true ? graph.nodes : []
    const seen = new Set()
    const nodes = []

    for (let i = 0; i < source.length; i = i + 1) {
        const node = source[i]
        if (node === null || node === undefined || node.id === undefined || node.id === null) {
            continue
        }
        const key = String(node.id)
        if (seen.has(key) === true) {
            continue
        }
        seen.add(key)
        nodes.push(node)
    }

    return nodes
}

/**
    Log every node id that occurs more than once (the first occurrence wins).

    :param graph: { nodes, edges } or null
*/
function reportDuplicateIds(graph) {
    const source = graph !== null && graph !== undefined && Array.isArray(graph.nodes) === true ? graph.nodes : []
    const seen = new Set()
    for (let i = 0; i < source.length; i = i + 1) {
        const node = source[i]
        if (node === null || node === undefined || node.id === undefined || node.id === null) {
            continue
        }
        const key = String(node.id)
        if (seen.has(key) === true) {
            console.error(`<mj-diagram>: duplicate node id "${key}"; the first occurrence is used.`)
        }
        seen.add(key)
    }
    return
}

function graphEdges(graph) {
    const source = graph !== null && graph !== undefined && Array.isArray(graph.edges) === true ? graph.edges : []
    const edges = []
    for (let i = 0; i < source.length; i = i + 1) {
        if (source[i] !== null && source[i] !== undefined) {
            edges.push(source[i])
        }
    }
    return edges
}

function nodeLabel(node) {
    const label = node.label !== undefined && node.label !== null && String(node.label).length > 0
        ? String(node.label)
        : String(node.id)
    return label
}

/**
    Compute a longest-path depth (layer) for each node.

    The graph may contain cycles. A depth-first search classifies every edge
    that points back to a node still on the search path as a back edge; those
    edges (and self-loops) take no part in the layering. What remains is
    acyclic, so a topological pass assigns each node the length of the
    longest path that reaches it. Both passes are iterative and visit every
    node and edge once.

    :param nodes: Array of node objects { id, label, description? }
    :param edges: Array of edge objects { source, target, ... }

    :returns: Map of node id (string) → layer index (0-based)
*/
function computeLayers(nodes, edges) {
    const ids = []
    const adjacency = new Map()
    for (let i = 0; i < nodes.length; i = i + 1) {
        const id = String(nodes[i].id)
        ids.push(id)
        adjacency.set(id, [])
    }

    for (let i = 0; i < edges.length; i = i + 1) {
        const source = String(edges[i].source)
        const target = String(edges[i].target)
        if (source !== target && adjacency.has(source) === true && adjacency.has(target) === true) {
            adjacency.get(source).push(target)
        }
    }

    // Pass 1: depth-first search; keep only the edges that do not close a cycle.
    const UNVISITED = 0
    const ON_PATH = 1
    const DONE = 2
    const state = new Map()
    const forward = new Map()
    const incoming = new Map()
    for (let i = 0; i < ids.length; i = i + 1) {
        state.set(ids[i], UNVISITED)
        forward.set(ids[i], [])
        incoming.set(ids[i], 0)
    }

    for (let i = 0; i < ids.length; i = i + 1) {
        if (state.get(ids[i]) !== UNVISITED) {
            continue
        }

        const stack = [{ id: ids[i], next: 0 }]
        state.set(ids[i], ON_PATH)

        while (stack.length > 0) {
            const frame = stack[stack.length - 1]
            const children = adjacency.get(frame.id)

            if (frame.next >= children.length) {
                state.set(frame.id, DONE)
                stack.pop()
                continue
            }

            const child = children[frame.next]
            frame.next = frame.next + 1

            const childState = state.get(child)
            if (childState === ON_PATH) {
                // Back edge: it would close a cycle, so it is not layered.
                continue
            }

            forward.get(frame.id).push(child)
            incoming.set(child, incoming.get(child) + 1)

            if (childState === UNVISITED) {
                state.set(child, ON_PATH)
                stack.push({ id: child, next: 0 })
            }
        }
    }

    // Pass 2: longest path over the acyclic remainder, in topological order.
    const layer = new Map()
    const queue = []
    for (let i = 0; i < ids.length; i = i + 1) {
        layer.set(ids[i], 0)
        if (incoming.get(ids[i]) === 0) {
            queue.push(ids[i])
        }
    }

    let head = 0
    while (head < queue.length) {
        const current = queue[head]
        head = head + 1
        const children = forward.get(current)
        for (let i = 0; i < children.length; i = i + 1) {
            const child = children[i]
            const candidate = layer.get(current) + 1
            if (candidate > layer.get(child)) {
                layer.set(child, candidate)
            }
            incoming.set(child, incoming.get(child) - 1)
            if (incoming.get(child) === 0) {
                queue.push(child)
            }
        }
    }

    return layer
}

/**
    Lay the graph out in layers (columns), left to right.

    :param nodes: Array of unique node objects
    :param edges: Array of edge objects

    :returns: { width, height, centres } where `centres` maps a node id
              (string) to the { x, y } centre of its box in diagram units
*/
function computeLayout(nodes, edges) {
    const layerMap = computeLayers(nodes, edges)

    const layerGroups = new Map()
    let maxLayer = 0
    let maxInLayer = 1
    for (let i = 0; i < nodes.length; i = i + 1) {
        const layerIndex = layerMap.get(String(nodes[i].id)) || 0
        if (layerGroups.has(layerIndex) === false) {
            layerGroups.set(layerIndex, [])
        }
        const group = layerGroups.get(layerIndex)
        group.push(nodes[i])
        if (layerIndex > maxLayer) { maxLayer = layerIndex }
        if (group.length > maxInLayer) { maxInLayer = group.length }
    }

    const width = (maxLayer + 1) * (NODE_W + H_GAP) + H_GAP
    const height = maxInLayer * (NODE_H + V_GAP) + V_GAP

    const centres = new Map()
    for (const [layerIndex, group] of layerGroups) {
        const columnX = H_GAP + layerIndex * (NODE_W + H_GAP) + NODE_W / 2
        const totalHeight = group.length * NODE_H + (group.length - 1) * V_GAP
        const startY = (height - totalHeight) / 2
        for (let i = 0; i < group.length; i = i + 1) {
            const centreY = startY + i * (NODE_H + V_GAP) + NODE_H / 2
            centres.set(String(group[i].id), { x: columnX, y: centreY })
        }
    }

    return { width: width, height: height, centres: centres }
}

/**
    Build the SVG for a laid-out graph. Everything is created with DOM calls;
    labels are set as text, never as markup.

    :param nodes: Array of unique node objects
    :param edges: Array of edge objects
    :param layout: Result of computeLayout
    :param options: { directed, interactive, transform: { tx, ty, scale } }

    :returns: Object { svgEl, groupEl, nodeEls } for later manipulation
*/
function renderSvgDiagram(nodes, edges, layout, options) {
    const svg = createSvg("svg", { class: "diagram-svg", focusable: "false" })

    const arrowId = nextId("mj-diagram-arrow")
    if (options.directed === true) {
        const defs = createSvg("defs", {})
        const marker = createSvg("marker", {
            id: arrowId, markerWidth: 10, markerHeight: 7, refX: 9, refY: 3.5, orient: "auto"
        })
        marker.appendChild(createSvg("path", { class: "diagram-arrow", d: "M 0 0 L 10 3.5 L 0 7 Z" }))
        defs.appendChild(marker)
        svg.appendChild(defs)
    }

    // Main group (pan/zoom target). It is NOT aria-hidden: the node buttons
    // inside it must be reachable. The decorative edges are hidden one by one.
    const group = createSvg("g", { class: "diagram-content" })
    const transform = options.transform
    group.setAttribute("transform", `translate(${transform.tx},${transform.ty}) scale(${transform.scale})`)
    svg.appendChild(group)

    // Draw edges first (behind nodes)
    for (let i = 0; i < edges.length; i = i + 1) {
        const edge = edges[i]
        const source = layout.centres.get(String(edge.source))
        const target = layout.centres.get(String(edge.target))
        if (source === undefined || target === undefined || source === target) { continue }

        // From the right edge of the source box to the left edge of the target box
        const x1 = source.x + NODE_W / 2
        const y1 = source.y
        const x2 = target.x - NODE_W / 2
        const y2 = target.y
        const middleX = (x1 + x2) / 2

        const path = createSvg("path", {
            class: "diagram-edge",
            d: `M ${x1} ${y1} C ${middleX} ${y1} ${middleX} ${y2} ${x2} ${y2}`,
            "aria-hidden": "true"
        })
        if (options.directed === true) {
            path.setAttribute("marker-end", `url(#${arrowId})`)
        }
        group.appendChild(path)

        if (edge.label !== undefined && edge.label !== null && String(edge.label).length > 0) {
            const label = createSvg("text", {
                class: "diagram-edge-label",
                x: middleX, y: (y1 + y2) / 2 - 6,
                "text-anchor": "middle", "aria-hidden": "true"
            })
            label.textContent = String(edge.label)
            group.appendChild(label)
        }
    }

    // Draw nodes
    const nodeEls = new Map()
    for (let i = 0; i < nodes.length; i = i + 1) {
        const node = nodes[i]
        const id = String(node.id)
        const centre = layout.centres.get(id)
        if (centre === undefined) { continue }

        const label = nodeLabel(node)
        const nodeEl = createSvg("g", { class: "diagram-node", "data-node-id": id, "aria-label": label })
        if (options.interactive === true) {
            nodeEl.setAttribute("role", "button")
            nodeEl.setAttribute("tabindex", "0")
        } else {
            nodeEl.setAttribute("role", "img")
        }

        nodeEl.appendChild(createSvg("rect", {
            x: centre.x - NODE_W / 2, y: centre.y - NODE_H / 2,
            width: NODE_W, height: NODE_H, rx: 6, ry: 6
        }))

        const text = createSvg("text", {
            x: centre.x, y: centre.y + 5, "text-anchor": "middle", "aria-hidden": "true"
        })
        text.textContent = label.length > NODE_LABEL_MAX ? `${label.slice(0, NODE_LABEL_MAX - 1)}…` : label
        nodeEl.appendChild(text)

        if (label.length > NODE_LABEL_MAX) {
            const title = createSvg("title", {})
            title.textContent = label
            nodeEl.appendChild(title)
        }

        group.appendChild(nodeEl)
        nodeEls.set(id, nodeEl)
    }

    return { svgEl: svg, groupEl: group, nodeEls: nodeEls }
}

/* ─── Styles ─────────────────────────────────────────────────────────────── */

const STYLES = `
:host { display: block; block-size: 100%; min-block-size: var(--mj-diagram-min-height, 280px); }

/*
 * As a dock band the host must not claim the whole dock container along the
 * axis the band consumes (see static/styles/base.css, Docking).
 */
:host([dock="top"]),
:host([dock="bottom"]) {
  block-size: auto;
}

.container {
  position: relative;
  block-size: var(--mj-diagram-height, 100%);
  min-block-size: inherit;
  border-radius: var(--mj-diagram-radius, var(--mj-radius-md));
  overflow: hidden;
  background: var(--mj-diagram-bg, var(--mj-surface));
  display: flex;
}

.render-target {
  position: relative;
  flex: 1;
  min-inline-size: 0;
  block-size: 100%;
  display: block;
  outline: none;
  cursor: grab;
  touch-action: none;
}
.container.static .render-target {
  cursor: default;
  touch-action: auto;
}
.render-target:focus-visible {
  box-shadow: inset 0 0 0 var(--mj-focus-ring-width) var(--mj-diagram-focus-ring, var(--mj-focus-ring));
}
.render-target.panning { cursor: grabbing; }

.diagram-svg {
  display: block;
  inline-size: 100%;
  block-size: 100%;
  overflow: hidden;
}
.diagram-edge {
  fill: none;
  stroke: var(--mj-diagram-edge, var(--mj-text-muted));
  stroke-width: 1.5;
}
.diagram-arrow { fill: var(--mj-diagram-edge, var(--mj-text-muted)); }
.diagram-edge-label {
  font-size: 11px;
  font-family: var(--mj-font-sans);
  fill: var(--mj-text-muted);
  stroke: var(--mj-diagram-bg, var(--mj-surface));
  stroke-width: 3;
  paint-order: stroke;
}
.diagram-node { cursor: pointer; }
.container.static .diagram-node { cursor: default; }
.diagram-node rect {
  fill: var(--mj-diagram-node-bg, var(--mj-bg-subtle));
  stroke: var(--mj-diagram-node-border, var(--mj-border-strong));
  stroke-width: 1.5;
}
.diagram-node text {
  font-size: 13px;
  font-family: var(--mj-font-sans);
  fill: var(--mj-diagram-node-text, var(--mj-text));
  pointer-events: none;
}
.diagram-node:focus { outline: none; }
.diagram-node:focus-visible rect {
  stroke: var(--mj-diagram-focus-ring, var(--mj-focus-ring));
  stroke-width: 3;
}
/* Selection is a filled box with a heavier outline and bold label, not colour alone. */
.diagram-node.selected rect {
  fill: var(--mj-diagram-node-selected-bg, var(--mj-accent));
  stroke: var(--mj-diagram-node-selected-border, var(--mj-text));
  stroke-width: 3;
}
.diagram-node.selected text {
  fill: var(--mj-diagram-node-selected-text, var(--mj-text-on-accent));
  font-weight: var(--mj-font-weight-bold);
}

.controls {
  position: absolute;
  inset-block-start: var(--mj-space-3);
  inset-inline-end: var(--mj-space-3);
  display: flex;
  flex-direction: column;
  gap: var(--mj-space-1);
  background: var(--mj-diagram-controls-bg, var(--mj-surface));
  border-radius: var(--mj-radius-sm);
  box-shadow: var(--mj-diagram-controls-shadow, var(--mj-elevation-2));
  padding: var(--mj-space-1);
  z-index: 10;
}
.container.list-visible .controls {
  inset-inline-end: calc(var(--mj-diagram-selection-panel-width, 16rem) + var(--mj-space-3));
}
.ctrl-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  inline-size: 2rem;
  block-size: 2rem;
  background: transparent;
  border: none;
  border-radius: var(--mj-radius-sm);
  cursor: pointer;
  font-size: var(--mj-font-size-md);
  font-weight: var(--mj-font-weight-bold);
  color: var(--mj-text);
  line-height: 1;
}
.ctrl-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}
.ctrl-btn[aria-disabled="true"] { opacity: 0.4; cursor: not-allowed; }

.node-list {
  position: absolute;
  inline-size: 1px;
  block-size: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  clip-path: inset(50%);
  white-space: nowrap;
  margin: -1px;
  padding: 0;
  list-style: none;
}
/*
 * A hidden list is revealed while one of its buttons has keyboard focus, so
 * focus never lands on something that cannot be seen.
 */
.node-list:not(.visible):focus-within {
  inset-block: var(--mj-space-3);
  inset-inline-end: var(--mj-space-3);
  inline-size: var(--mj-diagram-selection-panel-width, 16rem);
  max-inline-size: calc(100% - 2 * var(--mj-space-3));
  block-size: auto;
  box-sizing: border-box;
  overflow-y: auto;
  clip: auto;
  clip-path: none;
  white-space: normal;
  margin: 0;
  padding: var(--mj-space-3);
  background: var(--mj-surface);
  border-radius: var(--mj-radius-md);
  box-shadow: var(--mj-elevation-3);
  z-index: 30;
}
.node-list.visible {
  position: static;
  inline-size: var(--mj-diagram-selection-panel-width, 16rem);
  block-size: auto;
  box-sizing: border-box;
  clip: auto;
  clip-path: none;
  white-space: normal;
  margin: 0;
  overflow-y: auto;
  border-inline-start: 1px solid var(--mj-border);
  background: var(--mj-surface);
  padding: var(--mj-space-3);
  flex-shrink: 0;
}
.node-list li { margin-block-end: var(--mj-space-2); }
.node-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--mj-accent);
  font-size: var(--mj-font-size-sm);
  text-align: start;
  padding: var(--mj-space-1) var(--mj-space-2);
  border-radius: var(--mj-radius-sm);
  inline-size: 100%;
}
.node-btn:disabled { cursor: default; color: var(--mj-text); }
.node-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}
.node-btn.selected {
  background: var(--mj-color-accent-50, var(--mj-bg-muted));
  color: var(--mj-color-accent-700, var(--mj-accent));
  font-weight: var(--mj-font-weight-bold);
  text-decoration: underline;
}
.node-relations {
  margin: 0;
  padding-inline-start: var(--mj-space-4);
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
  list-style: none;
}
.node-relations li { margin-block-end: 0; }
.node-desc {
  position: absolute;
  inline-size: 1px;
  block-size: 1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
}

.selection-panel {
  position: absolute;
  inset-inline-start: 0;
  inset-block: 0;
  inline-size: var(--mj-diagram-selection-panel-width, 16rem);
  max-inline-size: 100%;
  box-sizing: border-box;
  background: var(--mj-surface);
  color: var(--mj-text);
  box-shadow: var(--mj-elevation-3);
  padding: var(--mj-space-4);
  display: none;
  overflow-y: auto;
  z-index: 20;
}
.selection-panel.open { display: block; }
.selection-panel:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: calc(-1 * var(--mj-focus-ring-width));
}
.selection-title {
  margin: 0 0 var(--mj-space-2);
  padding-inline-end: var(--mj-space-5);
  font-size: var(--mj-font-size-md);
  font-weight: var(--mj-font-weight-bold);
}
.selection-desc {
  margin: 0 0 var(--mj-space-3);
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text-muted);
}
.selection-desc:empty { display: none; }
.selection-links {
  margin: 0;
  padding: 0;
  list-style: none;
  font-size: var(--mj-font-size-sm);
}
.selection-close {
  position: absolute;
  inset-block-start: var(--mj-space-2);
  inset-inline-end: var(--mj-space-2);
  background: none;
  border: none;
  cursor: pointer;
  color: var(--mj-text-muted);
  font-size: var(--mj-font-size-sm);
  padding: var(--mj-space-1);
  border-radius: var(--mj-radius-sm);
}
.selection-close:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}

.loading {
  position: absolute;
  inset: 0;
  display: none;
  align-items: center;
  justify-content: center;
  background: var(--mj-surface);
  color: var(--mj-text-muted);
  font-size: var(--mj-font-size-sm);
  z-index: 40;
}
.loading.visible { display: flex; }

.error, .empty {
  position: absolute;
  inset: 0;
  display: none;
  align-items: center;
  justify-content: center;
  padding: var(--mj-space-4);
  text-align: center;
  background: var(--mj-diagram-bg, var(--mj-surface));
}
.error { color: var(--mj-color-danger); z-index: 40; }
.empty { color: var(--mj-text-muted); }
.error.visible, .empty.visible { display: flex; }

.live {
  position: absolute;
  inline-size: 1px; block-size: 1px;
  overflow: hidden; clip: rect(0 0 0 0); clip-path: inset(50%);
}
`;

export class MjDiagram extends MjElement {
  static tagName = "mj-diagram";
  static styles = STYLES;
  static watched = ["directed", "interactive", "show-list", "show-selection-panel",
    "fit-on-load", "zoom", "min-zoom", "max-zoom", "label", "loading"];

  constructor() {
    super()
    this._adapter = null
    this._adapterOptions = {}

    /* True while `_adapter` has been initialised into the current render target. */
    this._adapterReady = false

    /* Incremented on every adapter init; events of an earlier init are ignored. */
    this._adapterGeneration = 0

    /* Zoom level as last reported by the adapter; null until it reports. */
    this._adapterZoom = null

    this._graph = null
    this._selectedNodeId = null
    this._selectedEdgeId = null

    /* What opened the selection ("svg" or "list"), so focus can go back there. */
    this._selectionInvoker = null

    this._zoomDebounce = null
    this._panDebounce = null
    this._resizeObserver = null

    /* Every element reference is null until afterRender has run. */
    this._sectionEl = null
    this._renderTargetEl = null
    this._nodeListEl = null
    this._selectionPanelEl = null
    this._selectionSlot = null
    this._loadingEl = null
    this._errorEl = null
    this._emptyEl = null
    this._liveEl = null
    this._zoomInBtn = null
    this._zoomOutBtn = null
    this._fitBtn = null

    /* Built-in SVG renderer state. */
    this._svgEl = null
    this._svgGroupEl = null
    this._svgNodeEls = new Map()
    this._svgLayout = null
    this._svgTransform = { tx: 0, ty: 0, scale: 1 }

    /* True when the graph is waiting for the render target to get a size. */
    this._builtinRenderPending = false

    /* True once the user has panned or zoomed; a resize then keeps their view. */
    this._viewTouched = false

    /* True while the component writes its own zoom state to the `zoom` attribute. */
    this._reflectingZoom = false
  }

  render() {
    const markup = `
      <section role="application" aria-label="" part="container" class="container">
        <div class="render-target" part="render-target" role="group" tabindex="0"
          aria-label="${escapeHtml(t("mj.diagram.canvasLabel"))}"></div>
        <div class="controls" part="controls">
          <button type="button" class="ctrl-btn" part="zoom-in" aria-label="${escapeHtml(t("mj.diagram.zoomIn"))}">+</button>
          <button type="button" class="ctrl-btn" part="zoom-out" aria-label="${escapeHtml(t("mj.diagram.zoomOut"))}">−</button>
          <button type="button" class="ctrl-btn" part="fit-btn" aria-label="${escapeHtml(t("mj.diagram.fitToView"))}" title="${escapeHtml(t("mj.diagram.fit"))}">⊡</button>
          <slot name="controls"></slot>
        </div>
        <ul class="node-list" part="node-list" aria-label="${escapeHtml(t("mj.diagram.nodeList"))}"></ul>
        <div class="selection-panel" part="selection-panel" role="dialog" aria-label="${escapeHtml(t("mj.diagram.nodeDetails"))}" aria-modal="false" tabindex="-1">
          <button type="button" class="selection-close" aria-label="${escapeHtml(t("core.close"))}">✕</button>
          <slot name="selection-panel">
            <div class="selection-default">
              <h3 class="selection-title"></h3>
              <p class="selection-desc"></p>
              <ul class="selection-links"></ul>
            </div>
          </slot>
        </div>
        <div class="loading" part="loading" aria-live="polite">${escapeHtml(t("mj.diagram.loading"))}</div>
        <div class="error" part="error" role="alert"></div>
        <div class="empty" part="empty"><slot name="empty">${escapeHtml(t("mj.diagram.empty"))}</slot></div>
        <div class="live" role="status" aria-live="polite" aria-atomic="true"></div>
      </section>
    `
    return markup
  }

  afterRender() {
    this._sectionEl = this.$("section")
    this._renderTargetEl = this.$(".render-target")
    this._nodeListEl = this.$(".node-list")
    this._selectionPanelEl = this.$(".selection-panel")
    this._selectionSlot = this.$("slot[name='selection-panel']")
    this._loadingEl = this.$(".loading")
    this._errorEl = this.$(".error")
    this._emptyEl = this.$(".empty")
    this._liveEl = this.$(".live")

    this._zoomInBtn = this.$("[part='zoom-in']")
    this._zoomOutBtn = this.$("[part='zoom-out']")
    this._fitBtn = this.$("[part='fit-btn']")

    this._svgEl = null
    this._svgGroupEl = null
    this._svgNodeEls = new Map()
    this._svgLayout = null
    this._builtinRenderPending = false
    this._viewTouched = false

    this._applyAttrs()
    this._wireControls()
    this._wireBuiltinPan()
    this._setupResize()
    this._initAdapter()

    /* A node that was selected before a reconnect is shown as selected again. */
    const selected = this._findNode(this._selectedNodeId)
    if (selected !== null) {
      this._highlightSelection()
      if (this.hasAttribute("show-selection-panel") === true) {
        this._openSelection(selected, false)
      }
    } else {
      this._selectedNodeId = null
    }
    return
  }

  /* ----- attributes ----- */

  _number(name, fallback) {
    const parsed = parseFloat(this.getAttribute(name) || "")
    const value = Number.isFinite(parsed) === true ? parsed : fallback
    return value
  }

  _minZoom() {
    const value = this._number("min-zoom", 0.25)
    return value
  }

  _maxZoom() {
    const value = this._number("max-zoom", 4)
    return value
  }

  _isInteractive() {
    const interactive = this.getAttribute("interactive") !== "false"
    return interactive
  }

  _isDirected() {
    const directed = this.getAttribute("directed") !== "false"
    return directed
  }

  /* The zoom level the controls step from: the one actually on screen. */
  _currentZoom() {
    let zoom = this._number("zoom", 1)
    if (this._adapter === null) {
      zoom = this._svgTransform.scale
    } else if (this._adapterZoom !== null) {
      zoom = this._adapterZoom
    }
    return zoom
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._sectionEl === null || this._sectionEl === undefined) { return }

    if (name === "label") {
      this._applyLabel()
    } else if (name === "show-list") {
      this._applyListVisibility()
    } else if (name === "loading") {
      this._applyLoading()
    } else if (name === "zoom") {
      this._applyZoomAttribute()
    } else if (name === "min-zoom" || name === "max-zoom") {
      this._updateZoomButtons()
    } else if (name === "interactive" || name === "directed") {
      if (oldValue !== newValue) {
        this._applyInteractive()
        if (this._adapterReady === true) {
          this._initAdapter()
        } else {
          this._buildNodeList()
          this._renderBuiltin(false)
        }
      }
    } else if (name === "show-selection-panel") {
      if (newValue === null && this._selectionPanelEl.classList.contains("open") === true) {
        this._selectionPanelEl.classList.remove("open")
      }
    }
    return
  }

  _applyAttrs() {
    this._applyLabel()
    this._applyListVisibility()
    this._applyLoading()
    this._applyInteractive()
    this._updateZoomButtons()
    return
  }

  _applyLabel() {
    const label = this.getAttribute("label") || ""
    this._sectionEl.setAttribute("aria-label", label)
    if (label.length === 0) {
      console.warn("<mj-diagram>: `label` attribute is required for accessibility.")
    }
    return
  }

  _applyListVisibility() {
    const showList = this.hasAttribute("show-list")
    this._nodeListEl.classList.toggle("visible", showList)
    this._sectionEl.classList.toggle("list-visible", showList)
    this._syncListTabStops()
    return
  }

  _applyLoading() {
    const loading = this.hasAttribute("loading") === true && this.getAttribute("loading") !== "false"
    this._loadingEl.classList.toggle("visible", loading)
    if (loading === true) {
      this._sectionEl.setAttribute("aria-busy", "true")
    } else {
      this._sectionEl.removeAttribute("aria-busy")
    }
    return
  }

  _applyInteractive() {
    this._sectionEl.classList.toggle("static", this._isInteractive() === false)
    this._updateZoomButtons()
    return
  }

  /* The `zoom` attribute was written from outside: apply it without events. */
  _applyZoomAttribute() {
    /* The component is writing its own zoom state to the attribute. */
    if (this._reflectingZoom === true) {
      return
    }

    const requested = parseFloat(this.getAttribute("zoom") || "")
    if (Number.isFinite(requested) === false) {
      return
    }

    if (this._adapter === null) {
      /* The reflected value is rounded to three decimals. */
      if (Math.abs(requested - this._svgTransform.scale) > 0.001) {
        this._setBuiltinZoom(requested, null, false)
      }
    } else if (this._adapterReady === true && requested !== this._adapterZoom) {
      this._adapterZoom = requested
      this._adapter.setZoom(requested)
    }
    this._updateZoomButtons()
    return
  }

  /* ----- wiring ----- */

  _wireControls() {
    this.listen(this._zoomInBtn, "click", () => this._zoomBy(ZOOM_STEP))
    this.listen(this._zoomOutBtn, "click", () => this._zoomBy(-ZOOM_STEP))
    this.listen(this._fitBtn, "click", () => this._fit())
    this.listen(this._renderTargetEl, "keydown", (event) => this._onKeyDown(event))

    /* One delegated click listener for the built-in SVG nodes. */
    this.listen(this._renderTargetEl, "click", (event) => {
      const node = this._nodeFromEvent(event)
      if (node !== null && this._isInteractive() === true) {
        this._selectNode(node, "svg")
      }
    })

    /* One delegated click listener for the node list buttons. */
    this.listen(this._nodeListEl, "click", (event) => {
      const button = event.target instanceof Element ? event.target.closest(".node-btn") : null
      if (button !== null && this._isInteractive() === true) {
        const node = this._findNode(button.getAttribute("data-node-id"))
        if (node !== null) {
          this._selectNode(node, "list")
        }
      }
    })

    /* Escape clears the selection from anywhere inside the diagram, the panel included. */
    this.listen(this._sectionEl, "keydown", (event) => {
      if (event.key === "Escape" && this._selectedNodeId !== null) {
        event.preventDefault()
        event.stopPropagation()
        this._closeSelection()
      }
    })

    this.listen(this._selectionSlot, "slotchange", () => this._fillSelectionPanel())

    const closeBtn = this.$(".selection-close")
    this.listen(closeBtn, "click", () => this._closeSelection())

    this.onTeardown(() => {
      clearTimeout(this._zoomDebounce)
      clearTimeout(this._panDebounce)
      this._zoomDebounce = null
      this._panDebounce = null
    })
    return
  }

  /* The node whose built-in SVG element the event came from, or null. */
  _nodeFromEvent(event) {
    const element = event.target instanceof Element ? event.target.closest(".diagram-node") : null
    const node = element !== null ? this._findNode(element.getAttribute("data-node-id")) : null
    return node
  }

  _setupResize() {
    const observer = new ResizeObserver(() => {
      const width = this._renderTargetEl.clientWidth
      const height = this._renderTargetEl.clientHeight
      if (width === 0 || height === 0) { return }

      if (this._adapterReady === true) {
        if (typeof this._adapter.resize === "function") {
          this._adapter.resize()
        }
      } else if (this._adapter === null) {
        if (this._builtinRenderPending === true) {
          /* The graph was assigned while the target had no size: draw it now. */
          this._renderBuiltin(true)
        } else if (this._svgEl !== null && this._viewTouched === false) {
          /* Keep the diagram fitted until the user takes over the view. */
          this._builtinFit(false)
        }
      }
    })
    observer.observe(this._renderTargetEl)
    this._resizeObserver = observer
    this.onTeardown(() => {
      observer.disconnect()
      if (this._resizeObserver === observer) {
        this._resizeObserver = null
      }
    })
    return
  }

  /*
   * Pointer panning, pinch zoom and wheel zoom for the built-in renderer.
   * Wired once per render; the handlers do nothing while an adapter draws
   * the diagram or the diagram is not interactive.
   */
  _wireBuiltinPan() {
    const el = this._renderTargetEl
    const pointers = new Map()
    let drag = null
    let pinch = null

    const enabled = () => this._adapter === null && this._isInteractive() === true && this._svgGroupEl !== null

    const localPoint = (clientX, clientY) => {
      const rect = el.getBoundingClientRect()
      return { x: clientX - rect.left, y: clientY - rect.top }
    }

    const startDrag = (point) => {
      drag = { x: point.x, y: point.y, tx: this._svgTransform.tx, ty: this._svgTransform.ty }
      return
    }

    const pinchState = () => {
      const points = Array.from(pointers.values())
      const dx = points[0].x - points[1].x
      const dy = points[0].y - points[1].y
      const centre = localPoint((points[0].x + points[1].x) / 2, (points[0].y + points[1].y) / 2)
      return { distance: Math.max(1, Math.sqrt(dx * dx + dy * dy)), centre: centre }
    }

    const endPointer = (event) => {
      if (pointers.has(event.pointerId) === false) { return }
      pointers.delete(event.pointerId)
      if (typeof el.releasePointerCapture === "function" && el.hasPointerCapture(event.pointerId) === true) {
        el.releasePointerCapture(event.pointerId)
      }

      pinch = null
      drag = null
      if (pointers.size === 1) {
        /* One finger of a pinch stays down: it carries on as a pan. */
        startDrag(Array.from(pointers.values())[0])
      } else if (pointers.size === 0) {
        el.classList.remove("panning")
      }
      return
    }

    this.listen(el, "pointerdown", (event) => {
      if (enabled() === false) { return }
      if (event.pointerType === "mouse" && event.button !== 0) { return }

      /* A press that starts on a node is a selection, not a pan. */
      const onNode = event.target instanceof Element && event.target.closest(".diagram-node") !== null
      if (onNode === true && pointers.size === 0) { return }

      pointers.set(event.pointerId, { x: event.clientX, y: event.clientY })
      if (typeof el.setPointerCapture === "function") {
        try {
          el.setPointerCapture(event.pointerId)
        } catch (error) {
          /* Synthetic pointers cannot be captured; panning still works inside the target. */
        }
      }

      if (pointers.size === 1) {
        startDrag({ x: event.clientX, y: event.clientY })
        el.classList.add("panning")
      } else if (pointers.size === 2) {
        drag = null
        const state = pinchState()
        pinch = { distance: state.distance, scale: this._svgTransform.scale }
      }
    })

    this.listen(el, "pointermove", (event) => {
      if (pointers.has(event.pointerId) === false) { return }
      pointers.set(event.pointerId, { x: event.clientX, y: event.clientY })

      if (pinch !== null && pointers.size >= 2) {
        const state = pinchState()
        this._setBuiltinZoom(pinch.scale * (state.distance / pinch.distance), state.centre, true)
      } else if (drag !== null) {
        this._svgTransform.tx = drag.tx + (event.clientX - drag.x)
        this._svgTransform.ty = drag.ty + (event.clientY - drag.y)
        this._viewTouched = true
        this._applySvgTransform()
        this._emitPanSoon()
      }
    })

    this.listen(el, "pointerup", endPointer)
    this.listen(el, "pointercancel", endPointer)

    this.listen(el, "wheel", (event) => {
      if (enabled() === false) { return }

      /*
       * The wheel belongs to the page unless the user has put focus in the
       * diagram or holds Ctrl / Meta. Otherwise scrolling a page would stop
       * dead whenever the pointer crossed a diagram.
       */
      const focused = this._sectionEl.matches(":focus-within")
      if (focused === false && event.ctrlKey === false && event.metaKey === false) {
        return
      }

      event.preventDefault()
      const delta = event.deltaY < 0 ? WHEEL_ZOOM_STEP : -WHEEL_ZOOM_STEP
      this._setBuiltinZoom(this._svgTransform.scale + delta, localPoint(event.clientX, event.clientY), true)
    }, { passive: false })
    return
  }

  /* ----- adapter ----- */

  _destroyAdapter(adapter) {
    if (adapter !== null && this._adapterReady === true && typeof adapter.destroy === "function") {
      try {
        adapter.destroy()
      } catch (error) {
        console.warn("<mj-diagram>: adapter.destroy() failed.", error)
      }
    }
    this._adapterReady = false
    this._adapterZoom = null
    return
  }

  _removeBuiltinSvg() {
    if (this._svgEl !== null && this._svgEl.parentNode !== null) {
      this._svgEl.parentNode.removeChild(this._svgEl)
    }
    this._svgEl = null
    this._svgGroupEl = null
    this._svgNodeEls = new Map()
    this._svgLayout = null
    this._builtinRenderPending = false
    return
  }

  /*
   * (Re)initialise the render target for the current adapter -- or the
   * built-in renderer when there is none -- and show the stored graph in it.
   */
  _initAdapter() {
    this._destroyAdapter(this._adapter)
    this._removeBuiltinSvg()
    this._renderTargetEl.textContent = ""
    this._clearError()

    if (this._adapter === null) {
      this._applyGraph()
      return
    }

    const options = {
      directed: this._isDirected(),
      interactive: this._isInteractive(),
      minZoom: this._minZoom(),
      maxZoom: this._maxZoom(),
      ...this._adapterOptions
    }

    try {
      this._adapter.init(this._renderTargetEl, options)
      this._adapterReady = true
      this._subscribeToAdapter()
      this._applyGraph()
      this.emit("mj-diagram-ready", {})
    } catch (error) {
      this._adapterReady = false
      this._showError(error !== null && error !== undefined && error.message ? error.message : String(error))
      this._buildNodeList()
    }
    return
  }

  _subscribeToAdapter() {
    const adapter = this._adapter
    if (typeof adapter.on !== "function") {
      return
    }

    /* Events from an earlier init, or from a replaced adapter, are ignored. */
    this._adapterGeneration = this._adapterGeneration + 1
    const generation = this._adapterGeneration
    const current = () => this._adapter === adapter && this._adapterReady === true &&
      this._adapterGeneration === generation

    adapter.on("nodeSelect", (node) => {
      if (current() === true && node !== null && node !== undefined) {
        this._onAdapterNodeSelect(node)
      }
    })
    adapter.on("edgeSelect", (edge) => {
      if (current() === true && edge !== null && edge !== undefined) {
        this._onAdapterEdgeSelect(edge)
      }
    })
    adapter.on("zoom", (zoom) => {
      if (current() === true) {
        this._onAdapterZoom(Number(zoom))
      }
    })
    adapter.on("pan", (position) => {
      if (current() === true && position !== null && position !== undefined) {
        this._emitPanSoon({ x: position.x, y: position.y })
      }
    })
    return
  }

  /* ----- graph ----- */

  _nodes() {
    const nodes = uniqueNodes(this._graph)
    return nodes
  }

  _findNode(id) {
    let found = null
    if (id !== null && id !== undefined) {
      const nodes = this._nodes()
      for (let index = 0; index < nodes.length && found === null; index = index + 1) {
        if (String(nodes[index].id) === String(id)) {
          found = nodes[index]
        }
      }
    }
    return found
  }

  /*
   * Show the stored graph: rebuild the node list, then hand the graph to the
   * adapter or draw it with the built-in renderer. An empty graph shows the
   * empty state and removes the previous drawing.
   */
  _applyGraph() {
    this._buildNodeList()

    const nodes = this._nodes()
    const empty = nodes.length === 0
    this._emptyEl.classList.toggle("visible", empty)

    /* A selection that points at a node which is gone is dropped. */
    if (this._selectedNodeId !== null && this._findNode(this._selectedNodeId) === null) {
      const wasOpen = this._selectionPanelEl.classList.contains("open")
      this._selectionPanelEl.classList.remove("open")
      this._selectedNodeId = null
      this._selectionInvoker = null
      if (wasOpen === true) {
        this.emit("mj-diagram-node-deselect", {})
      }
    }

    if (this._adapter !== null) {
      if (this._adapterReady === false) {
        return
      }
      try {
        if (empty === true) {
          /* The adapter is not handed empty data; it is asked to clear when it can. */
          if (typeof this._adapter.clear === "function") {
            this._adapter.clear()
          }
        } else {
          this._adapter.setData(this._graph)
          const fitOnLoad = this.getAttribute("fit-on-load") !== "false"
          if (fitOnLoad === true && typeof this._adapter.fit === "function") {
            this._adapter.fit()
          }
        }
      } catch (error) {
        this._showError(error !== null && error !== undefined && error.message ? error.message : String(error))
      }
      return
    }

    if (empty === true) {
      this._removeBuiltinSvg()
    } else {
      this._renderBuiltin(true)
    }
    return
  }

  /* ----- built-in renderer ----- */

  /* The transform that centres `layout` in the render target at a fitting scale. */
  _fitTransform(layout) {
    const width = this._renderTargetEl.clientWidth
    const height = this._renderTargetEl.clientHeight
    const scaleX = (width - FIT_MARGIN * 2) / layout.width
    const scaleY = (height - FIT_MARGIN * 2) / layout.height
    const scale = Math.max(0.05, Math.min(scaleX, scaleY, 1))
    const transform = {
      tx: (width - layout.width * scale) / 2,
      ty: (height - layout.height * scale) / 2,
      scale: scale
    }
    return transform
  }

  /*
   * Draw the stored graph with the built-in renderer. `resetView` re-fits
   * the view (or applies the `zoom` attribute when fit-on-load is off);
   * otherwise the current pan and zoom are kept.
   */
  _renderBuiltin(resetView) {
    if (this._adapter !== null || this._renderTargetEl === null) { return }

    const nodes = this._nodes()
    if (nodes.length === 0) { return }

    /*
     * Without a size there is nothing to fit to. The ResizeObserver draws
     * the graph as soon as the target gets one -- no polling, and nothing
     * left running if the element is removed first.
     */
    if (this._renderTargetEl.clientWidth === 0 || this._renderTargetEl.clientHeight === 0) {
      this._builtinRenderPending = true
      return
    }

    const focusedId = this._focusedSvgNodeId()
    const keepView = resetView === false && this._svgEl !== null

    const previousTransform = this._svgTransform
    this._removeBuiltinSvg()

    const edges = graphEdges(this._graph)
    const layout = computeLayout(nodes, edges)

    if (keepView === true) {
      this._svgTransform = previousTransform
    } else if (this.getAttribute("fit-on-load") === "false") {
      const scale = Math.max(this._minZoom(), Math.min(this._maxZoom(), this._number("zoom", 1)))
      this._svgTransform = { tx: FIT_MARGIN, ty: FIT_MARGIN, scale: scale }
    } else {
      this._svgTransform = this._fitTransform(layout)
      this._viewTouched = false
    }

    const result = renderSvgDiagram(nodes, edges, layout, {
      directed: this._isDirected(),
      interactive: this._isInteractive(),
      transform: this._svgTransform
    })
    this._svgEl = result.svgEl
    this._svgGroupEl = result.groupEl
    this._svgNodeEls = result.nodeEls
    this._svgLayout = layout

    this._renderTargetEl.appendChild(this._svgEl)
    this._highlightSelection()
    this._reflectZoom(this._svgTransform.scale)
    this._updateZoomButtons()
    this._syncListTabStops()

    if (focusedId !== null && this._svgNodeEls.has(focusedId) === true) {
      this._svgNodeEls.get(focusedId).focus()
    }
    return
  }

  _focusedSvgNodeId() {
    const focused = this.shadowRoot.activeElement
    const id = focused !== null && focused.classList.contains("diagram-node") === true
      ? focused.getAttribute("data-node-id")
      : null
    return id
  }

  _applySvgTransform() {
    if (this._svgGroupEl === null) { return }
    const transform = this._svgTransform
    this._svgGroupEl.setAttribute(
      "transform",
      `translate(${transform.tx},${transform.ty}) scale(${transform.scale})`
    )
    return
  }

  /* Write the on-screen scale to the `zoom` attribute (the handler sees no difference). */
  _reflectZoom(scale) {
    const text = String(Math.round(scale * 1000) / 1000)
    if (this.getAttribute("zoom") !== text) {
      this._reflectingZoom = true
      try {
        this.setAttribute("zoom", text)
      } finally {
        this._reflectingZoom = false
      }
    }
    return
  }

  /*
   * Fit the built-in diagram to the render target. `announce` is true for a
   * fit the user asked for; automatic fits stay silent.
   */
  _builtinFit(announce) {
    if (this._adapter !== null || this._svgEl === null || this._svgLayout === null) { return }
    if (this._renderTargetEl.clientWidth === 0 || this._renderTargetEl.clientHeight === 0) { return }

    this._svgTransform = this._fitTransform(this._svgLayout)
    this._viewTouched = false
    this._applySvgTransform()
    this._reflectZoom(this._svgTransform.scale)
    this._updateZoomButtons()

    if (announce === true) {
      this._announceZoomSoon(this._svgTransform.scale)
      this._emitPanSoon()
    }
    return
  }

  _builtinPanBy(dx, dy) {
    if (this._adapter !== null || this._svgGroupEl === null) { return }
    this._svgTransform.tx = this._svgTransform.tx + dx
    this._svgTransform.ty = this._svgTransform.ty + dy
    this._viewTouched = true
    this._applySvgTransform()
    this._emitPanSoon()
    return
  }

  /*
   * Set the built-in zoom level, keeping the diagram point under `anchor`
   * (render-target coordinates; the viewport centre when null) where it is.
   * `announce` is true for a change the user made.
   */
  _setBuiltinZoom(requested, anchor, announce) {
    if (this._adapter !== null) { return }

    const previous = this._svgTransform.scale
    const scale = Math.max(this._minZoom(), Math.min(this._maxZoom(), requested))
    if (Number.isFinite(scale) === false || scale === previous) {
      this._updateZoomButtons()
      return
    }

    const point = anchor !== null && anchor !== undefined
      ? anchor
      : { x: this._renderTargetEl.clientWidth / 2, y: this._renderTargetEl.clientHeight / 2 }
    const ratio = scale / previous

    this._svgTransform.tx = point.x - (point.x - this._svgTransform.tx) * ratio
    this._svgTransform.ty = point.y - (point.y - this._svgTransform.ty) * ratio
    this._svgTransform.scale = scale
    this._applySvgTransform()
    this._reflectZoom(scale)
    this._updateZoomButtons()

    if (announce === true) {
      this._viewTouched = true
      this._announceZoomSoon(scale)
    }
    return
  }

  /* ----- zoom / pan (both renderers) ----- */

  _fit() {
    if (this._adapter !== null) {
      if (this._adapterReady === true && typeof this._adapter.fit === "function") {
        this._adapter.fit()
      }
    } else {
      this._builtinFit(true)
    }
    return
  }

  /* A zoom step requested by the user (buttons or keyboard). */
  _zoomBy(delta) {
    if (this._isInteractive() === false) { return }

    const current = this._currentZoom()
    const next = Math.max(this._minZoom(), Math.min(this._maxZoom(), current + delta))
    if (next === current) { return }

    if (this._adapter === null) {
      this._setBuiltinZoom(next, null, true)
    } else if (this._adapterReady === true) {
      /* Record the level first so the attribute handler sees nothing left to do. */
      this._adapterZoom = next
      this._adapter.setZoom(next)
      this._reflectZoom(next)
      this._updateZoomButtons()
      this._announceZoomSoon(next)
    }
    return
  }

  _announceZoomSoon(zoom) {
    clearTimeout(this._zoomDebounce)
    this._zoomDebounce = setTimeout(() => {
      this._zoomDebounce = null
      this._liveEl.textContent = t("mj.diagram.zoomLevel", { percent: Math.round(zoom * 100) })
      this.emit("mj-diagram-zoom-change", { zoom: zoom })
    }, EVENT_DEBOUNCE_MS)
    return
  }

  /* Report a pan; `position` defaults to the built-in translation. */
  _emitPanSoon(position) {
    clearTimeout(this._panDebounce)
    this._panDebounce = setTimeout(() => {
      this._panDebounce = null
      const detail = position !== undefined
        ? { x: position.x, y: position.y }
        : { x: this._svgTransform.tx, y: this._svgTransform.ty }
      this.emit("mj-diagram-pan", detail)
    }, EVENT_DEBOUNCE_MS)
    return
  }

  _updateZoomButtons() {
    if (this._zoomInBtn === null) { return }
    const zoom = this._currentZoom()
    const interactive = this._isInteractive()
    const atMax = interactive === false || zoom >= this._maxZoom()
    const atMin = interactive === false || zoom <= this._minZoom()
    this._zoomInBtn.setAttribute("aria-disabled", atMax === true ? "true" : "false")
    this._zoomOutBtn.setAttribute("aria-disabled", atMin === true ? "true" : "false")
    this._fitBtn.setAttribute("aria-disabled", interactive === false ? "true" : "false")
    return
  }

  _onAdapterZoom(zoom) {
    if (Number.isFinite(zoom) === false) { return }
    this._adapterZoom = zoom
    this._reflectZoom(zoom)
    this._updateZoomButtons()
    this._announceZoomSoon(zoom)
    return
  }

  /* ----- node list ----- */

  _buildNodeList() {
    this._nodeListEl.textContent = ""

    const nodes = this._nodes()
    const edges = graphEdges(this._graph)
    const directed = this._isDirected()
    const interactive = this._isInteractive()

    const labels = new Map()
    for (let i = 0; i < nodes.length; i = i + 1) {
      labels.set(String(nodes[i].id), nodeLabel(nodes[i]))
    }

    for (let i = 0; i < nodes.length; i = i + 1) {
      const node = nodes[i]
      const id = String(node.id)
      const item = document.createElement("li")

      const button = document.createElement("button")
      button.type = "button"
      button.className = "node-btn"
      button.setAttribute("data-node-id", id)
      button.setAttribute("aria-label", labels.get(id))
      button.textContent = labels.get(id)
      if (interactive === false) {
        button.disabled = true
      }

      const description = node.description !== undefined && node.description !== null
        ? String(node.description)
        : ""
      if (description.length > 0) {
        const descriptionId = nextId("mj-diag-desc")
        const descriptionEl = document.createElement("span")
        descriptionEl.id = descriptionId
        descriptionEl.className = "node-desc"
        descriptionEl.textContent = description
        item.appendChild(descriptionEl)
        button.setAttribute("aria-describedby", descriptionId)
      }

      item.appendChild(button)

      const relations = this._relationTexts(node, edges, labels, directed)
      if (relations.length > 0) {
        const relationList = document.createElement("ul")
        relationList.className = "node-relations"
        for (let j = 0; j < relations.length; j = j + 1) {
          const relation = document.createElement("li")
          relation.textContent = relations[j]
          relationList.appendChild(relation)
        }
        item.appendChild(relationList)
      }

      this._nodeListEl.appendChild(item)
    }

    this._highlightSelection()
    this._syncListTabStops()
    return
  }

  /* One line of text per edge that touches `node`. */
  _relationTexts(node, edges, labels, directed) {
    const id = String(node.id)
    const texts = []

    for (let i = 0; i < edges.length; i = i + 1) {
      const edge = edges[i]
      const source = String(edge.source)
      const target = String(edge.target)
      if (source !== id && target !== id) { continue }

      const otherId = source === id ? target : source
      const other = labels.has(otherId) === true ? labels.get(otherId) : otherId
      let arrow = "—"
      if (directed === true) {
        arrow = source === id ? "→" : "←"
      }
      const suffix = edge.label !== undefined && edge.label !== null && String(edge.label).length > 0
        ? `: ${String(edge.label)}`
        : ""
      texts.push(`${arrow} ${other}${suffix}`)
    }

    return texts
  }

  /*
   * While the list is visually hidden and the built-in SVG already offers a
   * focusable button per node, the list buttons leave the tab order so a
   * keyboard user does not meet every node twice. With an adapter they stay
   * tabbable (the list is revealed while it has focus).
   */
  _syncListTabStops() {
    if (this._nodeListEl === null) { return }
    const hiddenDuplicate = this._nodeListEl.classList.contains("visible") === false &&
      this._adapter === null && this._svgEl !== null
    const buttons = this._nodeListEl.querySelectorAll(".node-btn")
    for (let index = 0; index < buttons.length; index = index + 1) {
      if (hiddenDuplicate === true) {
        buttons[index].setAttribute("tabindex", "-1")
      } else {
        buttons[index].removeAttribute("tabindex")
      }
    }
    return
  }

  /* ----- selection ----- */

  /* Show the selected node in the node list and in the built-in SVG. */
  _highlightSelection() {
    if (this._nodeListEl === null) { return }
    const selectedId = this._selectedNodeId !== null ? String(this._selectedNodeId) : null

    const buttons = this._nodeListEl.querySelectorAll(".node-btn")
    for (let index = 0; index < buttons.length; index = index + 1) {
      const selected = selectedId !== null && buttons[index].getAttribute("data-node-id") === selectedId
      buttons[index].classList.toggle("selected", selected)
      if (selected === true) {
        buttons[index].setAttribute("aria-current", "true")
      } else {
        buttons[index].removeAttribute("aria-current")
      }
    }

    for (const [nodeId, nodeEl] of this._svgNodeEls) {
      const selected = selectedId !== null && nodeId === selectedId
      nodeEl.classList.toggle("selected", selected)
      if (selected === true) {
        nodeEl.setAttribute("aria-current", "true")
      } else {
        nodeEl.removeAttribute("aria-current")
      }
    }
    return
  }

  _selectNode(node, invoker) {
    this._selectedNodeId = node.id
    this._selectionInvoker = invoker || null

    if (this._adapterReady === true && invoker !== "adapter" && typeof this._adapter.selectNode === "function") {
      this._adapter.selectNode(node.id)
    }

    this._highlightSelection()
    this.emit("mj-diagram-node-select", { node: node })

    if (this.hasAttribute("show-selection-panel") === true) {
      this._openSelection(node, true)
    }
    return
  }

  /* Default panel content, and the `detail` property for slotted content. */
  _fillSelectionPanel() {
    const node = this._findNode(this._selectedNodeId)
    if (node === null) { return }

    const label = nodeLabel(node)
    this._selectionPanelEl.setAttribute("aria-label", label)
    this._selectionPanelEl.querySelector(".selection-title").textContent = label
    this._selectionPanelEl.querySelector(".selection-desc").textContent =
      node.description !== undefined && node.description !== null ? String(node.description) : ""

    const nodes = this._nodes()
    const labels = new Map()
    for (let i = 0; i < nodes.length; i = i + 1) {
      labels.set(String(nodes[i].id), nodeLabel(nodes[i]))
    }
    const relations = this._relationTexts(node, graphEdges(this._graph), labels, this._isDirected())
    const links = this._selectionPanelEl.querySelector(".selection-links")
    links.textContent = ""
    for (let i = 0; i < relations.length; i = i + 1) {
      const item = document.createElement("li")
      item.textContent = relations[i]
      links.appendChild(item)
    }

    const slotted = this._selectionSlot.assignedElements()
    for (let i = 0; i < slotted.length; i = i + 1) {
      slotted[i].detail = { node: node }
    }
    return
  }

  _openSelection(node, moveFocus) {
    this._fillSelectionPanel()
    this._selectionPanelEl.classList.add("open")
    if (moveFocus === true) {
      this._selectionPanelEl.focus()
    }
    return
  }

  /* The element that should get focus back when the selection is cleared. */
  _selectionReturnTarget() {
    let target = this._renderTargetEl
    const id = this._selectedNodeId !== null ? String(this._selectedNodeId) : null

    if (id !== null) {
      let candidate = null
      if (this._selectionInvoker === "svg" && this._svgNodeEls.has(id) === true) {
        candidate = this._svgNodeEls.get(id)
      } else if (this._selectionInvoker === "list") {
        const buttons = this._nodeListEl.querySelectorAll(".node-btn")
        for (let index = 0; index < buttons.length && candidate === null; index = index + 1) {
          if (buttons[index].getAttribute("data-node-id") === id) {
            candidate = buttons[index]
          }
        }
      }
      if (candidate !== null) {
        target = candidate
      }
    }

    return target
  }

  /*
   * Clear the selection: close the panel, drop the highlight, restore focus.
   * `silent` is true when the host cleared it through the property; only a
   * user action reports `mj-diagram-node-deselect`.
   */
  _closeSelection(silent) {
    const hadSelection = this._selectedNodeId !== null
    const panelHadFocus = this._selectionPanelEl.matches(":focus-within")
    const returnTarget = this._selectionReturnTarget()

    this._selectionPanelEl.classList.remove("open")
    this._selectedNodeId = null
    this._selectionInvoker = null
    this._highlightSelection()

    if (this._adapterReady === true && typeof this._adapter.deselectAll === "function") {
      this._adapter.deselectAll()
    }

    if (hadSelection === true && silent !== true) {
      this.emit("mj-diagram-node-deselect", {})
    }
    if (panelHadFocus === true) {
      returnTarget.focus()
    }
    return
  }

  _onAdapterNodeSelect(node) {
    const known = this._findNode(node.id)
    this._selectNode(known !== null ? known : node, "adapter")
    return
  }

  _onAdapterEdgeSelect(edge) {
    this._selectedEdgeId = edge.id
    this.emit("mj-diagram-edge-select", { edge: edge })
    return
  }

  /* ----- keyboard ----- */

  _onKeyDown(event) {
    if (event.ctrlKey === true || event.metaKey === true || event.altKey === true) { return }

    const key = event.key

    /* Enter / Space on a built-in node activates it. */
    if (key === "Enter" || key === " ") {
      const node = this._nodeFromEvent(event)
      if (node !== null && this._isInteractive() === true) {
        event.preventDefault()
        this._selectNode(node, "svg")
      }
      return
    }

    if (this._isInteractive() === false) { return }

    const panMap = {
      "ArrowUp": [0, -PAN_STEP_PX],
      "ArrowDown": [0, PAN_STEP_PX],
      "ArrowLeft": [-PAN_STEP_PX, 0],
      "ArrowRight": [PAN_STEP_PX, 0]
    }

    if (panMap[key] !== undefined) {
      event.preventDefault()
      const [dx, dy] = panMap[key]
      if (this._adapter !== null) {
        if (this._adapterReady === true && typeof this._adapter.panBy === "function") {
          this._adapter.panBy(dx, dy)
        }
      } else {
        this._builtinPanBy(dx, dy)
      }
    } else if (key === "+" || key === "=") {
      event.preventDefault()
      this._zoomBy(ZOOM_STEP)
    } else if (key === "-") {
      event.preventDefault()
      this._zoomBy(-ZOOM_STEP)
    } else if (key === "f" || key === "F") {
      event.preventDefault()
      this._fit()
    }
    return
  }

  _showError(message) {
    this._errorEl.textContent = message
    this._errorEl.classList.add("visible")
    this.emit("mj-diagram-error", { message: message })
    return
  }

  _clearError() {
    this._errorEl.textContent = ""
    this._errorEl.classList.remove("visible")
    return
  }

  onDisconnected() {
    this._destroyAdapter(this._adapter)
    this._builtinRenderPending = false
    return
  }

  /* ----- scriptable API ----- */

  get adapter() { return this._adapter }
  set adapter(value) {
    const next = value !== undefined ? value : null
    if (next === this._adapter) { return }

    this._destroyAdapter(this._adapter)
    this._adapter = next

    /* While detached the adapter is only stored; afterRender initialises it. */
    if (this._renderTargetEl !== null && this.isConnected === true) {
      this._initAdapter()
    }
  }

  get adapterOptions() { return this._adapterOptions }
  set adapterOptions(value) { this._adapterOptions = value || {} }

  get graph() { return this._graph }
  set graph(value) {
    this._graph = value !== undefined ? value : null
    reportDuplicateIds(this._graph)

    /* Before the first render the graph is only stored; afterRender shows it. */
    if (this._renderTargetEl !== null && this.isConnected === true) {
      this._applyGraph()
    }
  }

  get selectedNodeId() { return this._selectedNodeId }
  set selectedNodeId(id) {
    if (id === null || id === undefined) {
      if (this._selectionPanelEl !== null) {
        this._closeSelection(true)
      }
      this._selectedNodeId = null
      return
    }

    const node = this._findNode(id)
    if (node === null) {
      console.warn(`<mj-diagram>: Node id "${id}" not found in graph.`)
      if (this._selectionPanelEl !== null) {
        this._closeSelection(true)
      }
      this._selectedNodeId = null
      return
    }

    this._selectedNodeId = node.id
    if (this._selectionPanelEl !== null && this.isConnected === true) {
      if (this._adapterReady === true && typeof this._adapter.selectNode === "function") {
        this._adapter.selectNode(node.id)
      }
      this._highlightSelection()
      if (this._selectionPanelEl.classList.contains("open") === true) {
        this._fillSelectionPanel()
      }
    }
  }

  get selectedEdgeId() { return this._selectedEdgeId }
  set selectedEdgeId(id) { this._selectedEdgeId = id }
}
