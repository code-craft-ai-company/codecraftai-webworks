/*
 * mjdiagram.js
 *
 * <mj-diagram> -- accessible node/edge graph diagram with pluggable layout adapter,
 * keyboard pan/zoom, accessible node list, and selection panel. No layout engine
 * is bundled; the adapter is supplied by the host application.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";

/* ─── Built-in SVG renderer ──────────────────────────────────────────────── */

/**
    Compute a longest-path depth (layer) for each node using a simple BFS
    from root nodes (nodes with no incoming edges).

    :param nodes: Array of node objects { id, label, description? }
    :param edges: Array of edge objects { source, target, ... }

    :returns: Map of nodeId → layer index (0-based)
*/
function computeLayers(nodes, edges) {
    const incoming = new Map()
    for (let i = 0; i < nodes.length; i = i + 1) {
        incoming.set(nodes[i].id, 0)
    }
    for (let i = 0; i < edges.length; i = i + 1) {
        const t = edges[i].target
        if (incoming.has(t)) {
            incoming.set(t, (incoming.get(t) || 0) + 1)
        }
    }

    // Build adjacency list
    const adj = new Map()
    for (let i = 0; i < nodes.length; i = i + 1) {
        adj.set(nodes[i].id, [])
    }
    for (let i = 0; i < edges.length; i = i + 1) {
        const s = edges[i].source
        const t = edges[i].target
        if (adj.has(s)) {
            adj.get(s).push(t)
        }
    }

    const layer = new Map()
    const queue = []
    for (let i = 0; i < nodes.length; i = i + 1) {
        const id = nodes[i].id
        if (incoming.get(id) === 0) {
            layer.set(id, 0)
            queue.push(id)
        }
    }

    // BFS for nodes reachable from roots
    let qi = 0
    while (qi < queue.length) {
        const cur = queue[qi]
        qi = qi + 1
        const children = adj.get(cur) || []
        for (let i = 0; i < children.length; i = i + 1) {
            const child = children[i]
            const newLayer = (layer.get(cur) || 0) + 1
            if (!layer.has(child) || layer.get(child) < newLayer) {
                layer.set(child, newLayer)
                queue.push(child)
            }
        }
    }

    // Any disconnected nodes that never got assigned go to layer 0
    for (let i = 0; i < nodes.length; i = i + 1) {
        const id = nodes[i].id
        if (!layer.has(id)) {
            layer.set(id, 0)
        }
    }

    return layer
}

/**
    Render a graph as a layered SVG diagram inside a container element.

    :param container: DOM element to render into
    :param graph: { nodes, edges }
    :param currentTransform: { tx, ty, scale } current pan/zoom state
    :param onNodeClick: callback(node) when a node rect is clicked

    :returns: Object { svgEl, groupEl, nodeRects } for later manipulation
*/
function renderSvgDiagram(container, graph, currentTransform, onNodeClick) {
    const nodes = (graph && graph.nodes) || []
    const edges = (graph && graph.edges) || []

    const NODE_W = 140
    const NODE_H = 44
    const H_GAP = 80   // horizontal gap between layers
    const V_GAP = 32   // vertical gap between nodes in same layer

    const layerMap = computeLayers(nodes, edges)

    // Group nodes by layer
    const layerGroups = new Map()
    for (let i = 0; i < nodes.length; i = i + 1) {
        const l = layerMap.get(nodes[i].id) || 0
        if (!layerGroups.has(l)) {
            layerGroups.set(l, [])
        }
        layerGroups.get(l).push(nodes[i])
    }

    const maxLayer = layerGroups.size === 0 ? 0 : Math.max(...layerGroups.keys())

    // Compute max nodes in any column to size the SVG height
    let maxInLayer = 1
    for (const [, group] of layerGroups) {
        if (group.length > maxInLayer) {
            maxInLayer = group.length
        }
    }

    const totalLayers = maxLayer + 1
    const svgW = totalLayers * (NODE_W + H_GAP) + H_GAP
    const svgH = maxInLayer * (NODE_H + V_GAP) + V_GAP

    // Compute node centres
    const nodeCentre = new Map()
    for (const [layerIdx, group] of layerGroups) {
        const colX = H_GAP + layerIdx * (NODE_W + H_GAP) + NODE_W / 2
        const totalHeight = group.length * NODE_H + (group.length - 1) * V_GAP
        const startY = (svgH - totalHeight) / 2
        for (let i = 0; i < group.length; i = i + 1) {
            const cy = startY + i * (NODE_H + V_GAP) + NODE_H / 2
            nodeCentre.set(group[i].id, { x: colX, y: cy })
        }
    }

    // Build SVG — fill the container completely; diagram coordinates are
    // in logical pixel space and the <g> transform handles zoom/pan.
    const NS = "http://www.w3.org/2000/svg"
    const svg = document.createElementNS(NS, "svg")
    svg.setAttribute("width", "100%")
    svg.setAttribute("height", "100%")
    // No viewBox — we use transform on the <g> for pan/zoom instead.
    svg.setAttribute("xmlns", NS)
    svg.style.cssText = "display:block;width:100%;height:100%;overflow:hidden;"

    // Arrowhead marker
    const defs = document.createElementNS(NS, "defs")
    const marker = document.createElementNS(NS, "marker")
    marker.setAttribute("id", "mj-arrow")
    marker.setAttribute("markerWidth", "10")
    marker.setAttribute("markerHeight", "7")
    marker.setAttribute("refX", "9")
    marker.setAttribute("refY", "3.5")
    marker.setAttribute("orient", "auto")
    const arrowPath = document.createElementNS(NS, "path")
    arrowPath.setAttribute("d", "M 0 0 L 10 3.5 L 0 7 Z")
    arrowPath.setAttribute("fill", "var(--mj-diagram-edge, var(--mj-text-muted, #888))")
    marker.appendChild(arrowPath)
    defs.appendChild(marker)
    svg.appendChild(defs)

    // Main group (pan/zoom target)
    const g = document.createElementNS(NS, "g")
    g.setAttribute("aria-hidden", "true")
    const tx = currentTransform.tx || 0
    const ty = currentTransform.ty || 0
    const scale = currentTransform.scale || 1
    g.setAttribute("transform", `translate(${tx},${ty}) scale(${scale})`)
    svg.appendChild(g)

    // Draw edges first (behind nodes)
    for (let i = 0; i < edges.length; i = i + 1) {
        const edge = edges[i]
        const src = nodeCentre.get(edge.source)
        const tgt = nodeCentre.get(edge.target)
        if (src === undefined || tgt === undefined) { continue }

        // Line from right edge of source node to left edge of target node
        const x1 = src.x + NODE_W / 2
        const y1 = src.y
        const x2 = tgt.x - NODE_W / 2
        const y2 = tgt.y

        const line = document.createElementNS(NS, "path")
        const mx = (x1 + x2) / 2
        const d = `M ${x1} ${y1} C ${mx} ${y1} ${mx} ${y2} ${x2} ${y2}`
        line.setAttribute("d", d)
        line.setAttribute("fill", "none")
        line.setAttribute("stroke", "var(--mj-diagram-edge, var(--mj-text-muted, #888))")
        line.setAttribute("stroke-width", "1.5")
        line.setAttribute("marker-end", "url(#mj-arrow)")
        g.appendChild(line)

        // Edge label
        if (edge.label !== undefined && edge.label.length > 0) {
            const lx = (x1 + x2) / 2
            const ly = (y1 + y2) / 2 - 6
            const labelEl = document.createElementNS(NS, "text")
            labelEl.setAttribute("x", String(lx))
            labelEl.setAttribute("y", String(ly))
            labelEl.setAttribute("text-anchor", "middle")
            labelEl.setAttribute("font-size", "11")
            labelEl.setAttribute("fill", "var(--mj-text-muted, #888)")
            labelEl.textContent = edge.label
            g.appendChild(labelEl)
        }
    }

    // Draw nodes
    const nodeRects = new Map()
    for (let i = 0; i < nodes.length; i = i + 1) {
        const node = nodes[i]
        const centre = nodeCentre.get(node.id)
        if (centre === undefined) { continue }

        const rx = centre.x - NODE_W / 2
        const ry = centre.y - NODE_H / 2

        const rect = document.createElementNS(NS, "rect")
        rect.setAttribute("x", String(rx))
        rect.setAttribute("y", String(ry))
        rect.setAttribute("width", String(NODE_W))
        rect.setAttribute("height", String(NODE_H))
        rect.setAttribute("rx", "var(--mj-radius-md, 6)")
        rect.setAttribute("ry", "var(--mj-radius-md, 6)")
        rect.setAttribute("fill", "var(--mj-diagram-node-bg, var(--mj-surface-raised, #f0f4ff))")
        rect.setAttribute("stroke", "var(--mj-diagram-node-border, var(--mj-border, #c0c8e0))")
        rect.setAttribute("stroke-width", "1.5")
        rect.setAttribute("tabindex", "0")
        rect.setAttribute("role", "button")
        rect.setAttribute("aria-label", node.label || node.id)
        rect.style.cssText = "cursor:pointer;"
        rect.setAttribute("data-node-id", node.id)

        const capturedNode = node
        rect.addEventListener("click", () => { onNodeClick(capturedNode) })
        rect.addEventListener("keydown", (e) => {
            if (e.key === "Enter" || e.key === " ") {
                e.preventDefault()
                onNodeClick(capturedNode)
            }
        })

        g.appendChild(rect)
        nodeRects.set(node.id, rect)

        // Node label text
        const text = document.createElementNS(NS, "text")
        text.setAttribute("x", String(centre.x))
        text.setAttribute("y", String(centre.y + 5))
        text.setAttribute("text-anchor", "middle")
        text.setAttribute("font-size", "13")
        text.setAttribute("fill", "var(--mj-diagram-node-text, var(--mj-text, #1a1a2e))")
        text.setAttribute("font-family", "var(--mj-font-family, sans-serif)")
        text.setAttribute("pointer-events", "none")
        text.textContent = node.label || node.id
        g.appendChild(text)
    }

    return { svgEl: svg, groupEl: g, nodeRects: nodeRects }
}

/* ─── Styles ─────────────────────────────────────────────────────────────── */

const STYLES = `
:host { display: block; height: 100%; min-height: var(--mj-diagram-min-height, 280px); }

.container {
  position: relative;
  height: var(--mj-diagram-height, 100%);
  border-radius: var(--mj-diagram-radius, var(--mj-radius-md));
  overflow: hidden;
  background: var(--mj-diagram-bg, var(--mj-surface));
  display: flex;
}

.render-target {
  flex: 1;
  width: 100%;
  height: 100%;
  display: block;
  outline: none;
  cursor: default;
}
.render-target:focus-visible {
  box-shadow: inset 0 0 0 var(--mj-focus-ring-width) var(--mj-diagram-focus-ring, var(--mj-focus-ring));
}
.render-target.panning { cursor: grabbing; }

.controls {
  position: absolute;
  top: var(--mj-space-3);
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
.ctrl-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
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
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  clip-path: inset(50%);
  white-space: nowrap;
  margin: -1px;
}
.node-list.visible {
  position: static;
  width: var(--mj-diagram-selection-panel-width, 16rem);
  height: 100%;
  clip: unset;
  clip-path: unset;
  white-space: normal;
  margin: 0;
  overflow-y: auto;
  border-left: 1px solid var(--mj-border);
  background: var(--mj-surface);
  padding: var(--mj-space-3);
  list-style: none;
  flex-shrink: 0;
}
.node-list li { margin-bottom: var(--mj-space-2); }
.node-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--mj-accent);
  font-size: var(--mj-font-size-sm);
  text-align: left;
  padding: var(--mj-space-1) var(--mj-space-2);
  border-radius: var(--mj-radius-sm);
  width: 100%;
}
.node-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}
.node-btn.selected {
  background: var(--mj-color-accent-50, #eef4ff);
  font-weight: var(--mj-font-weight-medium);
}

.selection-panel {
  position: absolute;
  inset-inline-start: 0;
  top: 0;
  bottom: 0;
  width: var(--mj-diagram-selection-panel-width, 16rem);
  background: var(--mj-surface);
  box-shadow: var(--mj-elevation-3);
  padding: var(--mj-space-4);
  display: none;
  overflow-y: auto;
  z-index: 20;
}
.selection-panel.open { display: block; }
.selection-close {
  position: absolute;
  top: var(--mj-space-2);
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
}
.error { color: var(--mj-color-danger); }
.empty { color: var(--mj-text-muted); }
.error.visible, .empty.visible { display: flex; }

.live {
  position: absolute;
  width: 1px; height: 1px;
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
    this._graph = null
    this._selectedNodeId = null
    this._selectedEdgeId = null
    this._zoomDebounce = null
    this._panDebounce = null
    this._resizeObserver = null
    this._renderTargetEl = null
    this._nodeListEl = null
    this._selectionPanelEl = null
    this._liveEl = null
    // Built-in SVG renderer state
    this._svgEl = null
    this._svgGroupEl = null
    this._svgNodeRects = new Map()
    this._svgTransform = { tx: 0, ty: 0, scale: 1 }
  }

  render() {
    const markup = `
      <section role="application" aria-label="" part="container" class="container">
        <div class="render-target" part="render-target" tabindex="0"
          aria-label="Diagram canvas"></div>
        <div class="controls" part="controls">
          <button class="ctrl-btn" part="zoom-in" aria-label="Zoom in">+</button>
          <button class="ctrl-btn" part="zoom-out" aria-label="Zoom out">−</button>
          <button class="ctrl-btn" part="fit-btn" aria-label="Fit to view" title="Fit">⊡</button>
          <slot name="controls"></slot>
        </div>
        <ul class="node-list" part="node-list" aria-label="Diagram nodes"></ul>
        <div class="selection-panel" part="selection-panel" role="dialog" aria-label="Node details" aria-modal="true" tabindex="-1">
          <button class="selection-close" aria-label="Close">✕</button>
          <slot name="selection-panel"></slot>
        </div>
        <div class="loading" part="loading" aria-live="polite">Loading diagram…</div>
        <div class="error" part="error" role="alert"></div>
        <div class="empty" part="empty"><slot name="empty">No nodes to display.</slot></div>
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
    this._loadingEl = this.$(".loading")
    this._errorEl = this.$(".error")
    this._emptyEl = this.$(".empty")
    this._liveEl = this.$(".live")

    this._zoomInBtn = this.$("[part='zoom-in']")
    this._zoomOutBtn = this.$("[part='zoom-out']")
    this._fitBtn = this.$("[part='fit-btn']")

    this._applyAttrs()
    this._wireControls()
    this._setupResize()
    this._initAdapter()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._sectionEl === null || this._sectionEl === undefined) { return }
    if (name === "label") {
      this._sectionEl.setAttribute("aria-label", newValue || "")
      if (newValue === null || newValue.length === 0) {
        console.warn("<mj-diagram>: `label` attribute is required for accessibility.")
      }
    } else if (name === "show-list") {
      this._nodeListEl.classList.toggle("visible", newValue !== null)
    } else if (name === "zoom") {
      const z = parseFloat(newValue) || 1
      if (this._adapter !== null) {
        this._adapter.setZoom(z)
      } else {
        this._builtinSetZoom(z)
      }
      this._updateZoomButtons(z)
    }
    return
  }

  _applyAttrs() {
    const label = this.getAttribute("label") || ""
    this._sectionEl.setAttribute("aria-label", label)
    if (label.length === 0) {
      console.warn("<mj-diagram>: `label` attribute is required for accessibility.")
    }

    const showList = this.hasAttribute("show-list")
    this._nodeListEl.classList.toggle("visible", showList)

    const zoom = parseFloat(this.getAttribute("zoom") || "1")
    this._updateZoomButtons(zoom)
    return
  }

  _wireControls() {
    this.listen(this._zoomInBtn, "click", () => this._zoomBy(0.25))
    this.listen(this._zoomOutBtn, "click", () => this._zoomBy(-0.25))
    this.listen(this._fitBtn, "click", () => {
      if (this._adapter !== null && typeof this._adapter.fit === "function") {
        this._adapter.fit()
      } else {
        this._builtinFit()
      }
    })
    this.listen(this._renderTargetEl, "keydown", (e) => this._onKeyDown(e))

    const closeBtn = this.$(".selection-close")
    this.listen(closeBtn, "click", () => this._closeSelection())
    return
  }

  _setupResize() {
    this._resizeObserver = new ResizeObserver(() => {
      const w = this._renderTargetEl.clientWidth
      const h = this._renderTargetEl.clientHeight
      if (w === 0 || h === 0) { return }
      if (this._adapter !== null && typeof this._adapter.resize === "function") {
        this._adapter.resize()
      } else if (this._svgEl !== null) {
        // Re-fit the built-in diagram to the new dimensions
        this._builtinFit()
      }
    })
    this._resizeObserver.observe(this._renderTargetEl)
    this.onTeardown(() => {
      if (this._resizeObserver !== null) {
        this._resizeObserver.disconnect()
        this._resizeObserver = null
      }
    })
    return
  }

  _builtinFit() {
    if (this._adapter !== null || this._svgEl === null) { return }
    if (this._graph === null) { return }

    const ctW = this._renderTargetEl.clientWidth
    const ctH = this._renderTargetEl.clientHeight
    if (ctW === 0 || ctH === 0) { return }

    const nodes = this._graph.nodes || []
    const edges = this._graph.edges || []
    const NODE_W = 140
    const H_GAP = 80
    const NODE_H = 44
    const V_GAP = 32
    const MARGIN = 16
    const layerMap = computeLayers(nodes, edges)
    const layerSet = new Set(layerMap.values())
    const maxLayer = layerSet.size === 0 ? 0 : Math.max(...layerSet)
    const layerCounts = new Map()
    for (const l of layerMap.values()) {
      layerCounts.set(l, (layerCounts.get(l) || 0) + 1)
    }
    let maxInLayer = 1
    for (const c of layerCounts.values()) { if (c > maxInLayer) { maxInLayer = c } }
    const totalLayers = maxLayer + 1
    const contentW = totalLayers * (NODE_W + H_GAP) + H_GAP
    const contentH = maxInLayer * (NODE_H + V_GAP) + V_GAP
    const availW = ctW - MARGIN * 2
    const availH = ctH - MARGIN * 2
    const scaleX = availW / contentW
    const scaleY = availH / contentH
    const fitScale = Math.min(scaleX, scaleY, 1)
    const fitTx = (ctW - contentW * fitScale) / 2
    const fitTy = (ctH - contentH * fitScale) / 2
    this._svgTransform = { tx: fitTx, ty: fitTy, scale: fitScale }
    this._applySvgTransform()
    return
  }

  _builtinPanBy(dx, dy) {
    if (this._adapter !== null) { return }
    this._svgTransform.tx = this._svgTransform.tx + dx
    this._svgTransform.ty = this._svgTransform.ty + dy
    this._applySvgTransform()
    return
  }

  _builtinSetZoom(z) {
    if (this._adapter !== null) { return }
    this._svgTransform.scale = z
    this._applySvgTransform()
    return
  }

  _initAdapter() {
    if (this._adapter === null) {
      this._loadingEl.classList.remove("visible")
      if (this._graph === null || (this._graph.nodes || []).length === 0) {
        this._emptyEl.classList.add("visible")
      } else {
        this._renderBuiltin()
      }
      return
    }

    this._loadingEl.classList.add("visible")
    const minZoom = parseFloat(this.getAttribute("min-zoom") || "0.25")
    const maxZoom = parseFloat(this.getAttribute("max-zoom") || "4")
    const directed = this.getAttribute("directed") !== "false"

    try {
      this._adapter.init(this._renderTargetEl, { directed, minZoom, maxZoom, ...this._adapterOptions })

      if (this._adapter.on !== undefined) {
        this._adapter.on("nodeSelect", (node) => this._onAdapterNodeSelect(node))
        this._adapter.on("edgeSelect", (edge) => this._onAdapterEdgeSelect(edge))
        this._adapter.on("zoom", (z) => this._onAdapterZoom(z))
        this._adapter.on("pan", (pos) => this._onAdapterPan(pos))
      }

      this._loadingEl.classList.remove("visible")

      if (this._graph !== null) {
        this._adapter.setData(this._graph)
        const fitOnLoad = this.getAttribute("fit-on-load") !== "false"
        if (fitOnLoad === true && typeof this._adapter.fit === "function") {
          this._adapter.fit()
        }
      }

      this.emit("mj-diagram-ready", {})
    } catch (err) {
      this._showError(err.message)
    }
    return
  }

  _renderBuiltin() {
    if (this._adapter !== null) { return }
    if (this._graph === null) { return }
    const nodes = this._graph.nodes || []
    if (nodes.length === 0) { return }

    // Defer to the next animation frame if the container has no size yet
    // (common before layout settles on first paint).
    const ctW = this._renderTargetEl.clientWidth
    const ctH = this._renderTargetEl.clientHeight
    if (ctW === 0 || ctH === 0) {
      requestAnimationFrame(() => { this._renderBuiltin() })
      return
    }

    // Clear any prior SVG
    if (this._svgEl !== null && this._svgEl.parentNode === this._renderTargetEl) {
      this._renderTargetEl.removeChild(this._svgEl)
    }
    this._svgEl = null
    this._svgGroupEl = null
    this._svgNodeRects = new Map()

    // Compute initial fit transform from REAL measured dimensions.
    const edges = this._graph.edges || []
    const NODE_W = 140
    const H_GAP = 80
    const NODE_H = 44
    const V_GAP = 32
    const MARGIN = 16
    const layerMap = computeLayers(nodes, edges)
    const layerSet = new Set(layerMap.values())
    const maxLayer = layerSet.size === 0 ? 0 : Math.max(...layerSet)
    const layerCounts = new Map()
    for (const l of layerMap.values()) {
      layerCounts.set(l, (layerCounts.get(l) || 0) + 1)
    }
    let maxInLayer = 1
    for (const c of layerCounts.values()) { if (c > maxInLayer) { maxInLayer = c } }
    const totalLayers = maxLayer + 1
    const contentW = totalLayers * (NODE_W + H_GAP) + H_GAP
    const contentH = maxInLayer * (NODE_H + V_GAP) + V_GAP
    const availW = ctW - MARGIN * 2
    const availH = ctH - MARGIN * 2
    const scaleX = availW / contentW
    const scaleY = availH / contentH
    const fitScale = Math.min(scaleX, scaleY, 1)
    const fitTx = (ctW - contentW * fitScale) / 2
    const fitTy = (ctH - contentH * fitScale) / 2
    this._svgTransform = { tx: fitTx, ty: fitTy, scale: fitScale }

    const result = renderSvgDiagram(
      this._renderTargetEl,
      this._graph,
      this._svgTransform,
      (node) => this._onBuiltinNodeClick(node)
    )
    this._svgEl = result.svgEl
    this._svgGroupEl = result.groupEl
    this._svgNodeRects = result.nodeRects

    this._renderTargetEl.appendChild(this._svgEl)
    this._emptyEl.classList.remove("visible")

    // Wire mouse pan on the SVG (only once per render)
    this._wireBuiltinPan()
    return
  }

  _wireBuiltinPan() {
    const el = this._renderTargetEl
    let dragging = false
    let startX = 0
    let startY = 0
    let startTx = 0
    let startTy = 0

    const onMouseDown = (e) => {
      if (e.target.tagName === "rect") { return }
      dragging = true
      startX = e.clientX
      startY = e.clientY
      startTx = this._svgTransform.tx
      startTy = this._svgTransform.ty
      el.classList.add("panning")
    }
    const onMouseMove = (e) => {
      if (!dragging) { return }
      const dx = e.clientX - startX
      const dy = e.clientY - startY
      this._svgTransform.tx = startTx + dx
      this._svgTransform.ty = startTy + dy
      this._applySvgTransform()
    }
    const onMouseUp = () => {
      dragging = false
      el.classList.remove("panning")
    }

    el.addEventListener("mousedown", onMouseDown)
    el.addEventListener("mousemove", onMouseMove)
    el.addEventListener("mouseup", onMouseUp)
    el.addEventListener("mouseleave", onMouseUp)

    // Wheel zoom
    const onWheel = (e) => {
      e.preventDefault()
      const delta = e.deltaY < 0 ? 0.1 : -0.1
      const minZoom = parseFloat(this.getAttribute("min-zoom") || "0.25")
      const maxZoom = parseFloat(this.getAttribute("max-zoom") || "4")
      const newScale = Math.max(minZoom, Math.min(maxZoom, this._svgTransform.scale + delta))
      this._svgTransform.scale = newScale
      this._applySvgTransform()
      this._updateZoomButtons(newScale)
    }
    el.addEventListener("wheel", onWheel, { passive: false })

    this.onTeardown(() => {
      el.removeEventListener("mousedown", onMouseDown)
      el.removeEventListener("mousemove", onMouseMove)
      el.removeEventListener("mouseup", onMouseUp)
      el.removeEventListener("mouseleave", onMouseUp)
      el.removeEventListener("wheel", onWheel)
    })
    return
  }

  _applySvgTransform() {
    if (this._svgGroupEl === null) { return }
    const tx = this._svgTransform.tx
    const ty = this._svgTransform.ty
    const scale = this._svgTransform.scale
    this._svgGroupEl.setAttribute("transform", `translate(${tx},${ty}) scale(${scale})`)
    return
  }

  _onBuiltinNodeClick(node) {
    this._selectedNodeId = node.id
    this._highlightNodeBtn(node.id)
    this._highlightBuiltinNode(node.id)
    this.emit("mj-diagram-node-select", { node: node })
    if (this.hasAttribute("show-selection-panel") === true) {
      this._openSelection(node)
    }
    return
  }

  _highlightBuiltinNode(id) {
    for (const [nodeId, rect] of this._svgNodeRects) {
      if (nodeId === id) {
        rect.setAttribute("fill", "var(--mj-diagram-node-selected-bg, var(--mj-accent, #3b6bff))")
        rect.setAttribute("stroke", "var(--mj-diagram-node-selected-border, var(--mj-accent, #3b6bff))")
      } else {
        rect.setAttribute("fill", "var(--mj-diagram-node-bg, var(--mj-surface-raised, #f0f4ff))")
        rect.setAttribute("stroke", "var(--mj-diagram-node-border, var(--mj-border, #c0c8e0))")
      }
    }
    return
  }

  _buildNodeList() {
    this._nodeListEl.innerHTML = ""
    if (this._graph === null) { return }

    const nodes = this._graph.nodes || []
    const edges = this._graph.edges || []

    for (let i = 0; i < nodes.length; i = i + 1) {
      const node = nodes[i]
      const li = document.createElement("li")

      const btn = document.createElement("button")
      btn.className = "node-btn"
      btn.setAttribute("aria-label", node.label || node.id)
      btn.textContent = node.label || node.id

      if (node.description !== undefined && node.description.length > 0) {
        const descId = nextId("mj-diag-desc")
        const desc = document.createElement("span")
        desc.id = descId
        desc.textContent = node.description
        desc.style.cssText = "position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)"
        li.appendChild(desc)
        btn.setAttribute("aria-describedby", descId)
      }

      const capturedNode = node
      this.listen(btn, "click", () => {
        this._selectedNodeId = capturedNode.id
        if (this._adapter !== null) { this._adapter.selectNode(capturedNode.id) }
        this._highlightNodeBtn(capturedNode.id)
        this.emit("mj-diagram-node-select", { node: capturedNode })

        if (this.hasAttribute("show-selection-panel") === true) {
          this._openSelection(capturedNode)
        }
      })

      li.appendChild(btn)

      const connectedEdges = edges.filter(e => e.source === node.id || e.target === node.id)
      if (connectedEdges.length > 0) {
        const relList = document.createElement("ul")
        relList.style.cssText = "padding-left:1rem;font-size:0.75rem;color:var(--mj-text-muted);list-style:none"
        for (let j = 0; j < connectedEdges.length; j = j + 1) {
          const edge = connectedEdges[j]
          const other = edge.source === node.id ? edge.target : edge.source
          const rel = document.createElement("li")
          const dir = edge.source === node.id ? "→" : "←"
          rel.textContent = `${dir} ${other}${edge.label !== undefined ? ": " + edge.label : ""}`
          relList.appendChild(rel)
        }
        li.appendChild(relList)
      }

      this._nodeListEl.appendChild(li)
    }
    return
  }

  _highlightNodeBtn(id) {
    const btns = this._nodeListEl.querySelectorAll(".node-btn")
    for (let i = 0; i < btns.length; i = i + 1) {
      btns[i].classList.toggle("selected", btns[i].getAttribute("aria-label") === (
        (this._graph.nodes || []).find(n => n.id === id) || { label: "" }
      ).label)
    }
    return
  }

  _openSelection(node) {
    this._selectionPanelEl.setAttribute("aria-label", node.label || node.id)
    this._selectionPanelEl.classList.add("open")
    this._selectionPanelEl.focus()
    return
  }

  _closeSelection() {
    this._selectionPanelEl.classList.remove("open")
    this._selectedNodeId = null
    this.emit("mj-diagram-node-deselect", {})
    this._renderTargetEl.focus()
    return
  }

  _onAdapterNodeSelect(node) {
    this._selectedNodeId = node.id
    this.emit("mj-diagram-node-select", { node: node })
    if (this.hasAttribute("show-selection-panel") === true) {
      this._openSelection(node)
    }
    return
  }

  _onAdapterEdgeSelect(edge) {
    this._selectedEdgeId = edge.id
    this.emit("mj-diagram-edge-select", { edge: edge })
    return
  }

  _onAdapterZoom(z) {
    clearTimeout(this._zoomDebounce)
    this._zoomDebounce = setTimeout(() => {
      this._liveEl.textContent = `Zoom: ${z.toFixed(2)}`
      this.emit("mj-diagram-zoom-change", { zoom: z })
      this._updateZoomButtons(z)
    }, 200)
    return
  }

  _onAdapterPan(pos) {
    clearTimeout(this._panDebounce)
    this._panDebounce = setTimeout(() => {
      this.emit("mj-diagram-pan", { x: pos.x, y: pos.y })
    }, 200)
    return
  }

  _zoomBy(delta) {
    const current = parseFloat(this.getAttribute("zoom") || "1")
    const minZoom = parseFloat(this.getAttribute("min-zoom") || "0.25")
    const maxZoom = parseFloat(this.getAttribute("max-zoom") || "4")
    const next = Math.max(minZoom, Math.min(maxZoom, current + delta))
    this.setAttribute("zoom", String(next))
    return
  }

  _updateZoomButtons(zoom) {
    const minZoom = parseFloat(this.getAttribute("min-zoom") || "0.25")
    const maxZoom = parseFloat(this.getAttribute("max-zoom") || "4")
    this._zoomInBtn.setAttribute("aria-disabled", zoom >= maxZoom ? "true" : "false")
    this._zoomOutBtn.setAttribute("aria-disabled", zoom <= minZoom ? "true" : "false")
    return
  }

  _onKeyDown(event) {
    const key = event.key
    const panAmount = 50
    const panMap = {
      "ArrowUp": [0, -panAmount],
      "ArrowDown": [0, panAmount],
      "ArrowLeft": [-panAmount, 0],
      "ArrowRight": [panAmount, 0]
    }

    if (panMap[key] !== undefined) {
      event.preventDefault()
      const [dx, dy] = panMap[key]
      if (this._adapter !== null && typeof this._adapter.panBy === "function") {
        this._adapter.panBy(dx, dy)
      } else {
        this._builtinPanBy(dx, dy)
      }
    } else if (key === "+" || key === "=") {
      event.preventDefault()
      this._zoomBy(0.25)
    } else if (key === "-") {
      event.preventDefault()
      this._zoomBy(-0.25)
    } else if (key === "f" || key === "F") {
      event.preventDefault()
      if (this._adapter !== null && typeof this._adapter.fit === "function") {
        this._adapter.fit()
      } else {
        this._builtinFit()
      }
    } else if (key === "Escape") {
      this._closeSelection()
    }
    return
  }

  _showError(message) {
    this._loadingEl.classList.remove("visible")
    this._errorEl.textContent = message
    this._errorEl.classList.add("visible")
    this.emit("mj-diagram-error", { message: message })
    return
  }

  onDisconnected() {
    if (this._resizeObserver !== null) {
      this._resizeObserver.disconnect()
      this._resizeObserver = null
    }
    if (this._zoomDebounce !== null) { clearTimeout(this._zoomDebounce) }
    if (this._panDebounce !== null) { clearTimeout(this._panDebounce) }
    if (this._adapter !== null && typeof this._adapter.destroy === "function") {
      this._adapter.destroy()
    }
    return
  }

  /* ----- scriptable API ----- */

  get adapter() { return this._adapter }
  set adapter(v) {
    this._adapter = v
    if (this._renderTargetEl !== null) { this._initAdapter() }
  }

  get adapterOptions() { return this._adapterOptions }
  set adapterOptions(v) { this._adapterOptions = v || {} }

  get graph() { return this._graph }
  set graph(v) {
    this._graph = v
    if (this._nodeListEl !== null) {
      this._buildNodeList()
    }
    const nodes = (v && v.nodes) || []
    if (nodes.length === 0) {
      if (this._emptyEl !== null) {
        this._emptyEl.classList.add("visible")
      }
      return
    }
    if (this._emptyEl !== null) {
      this._emptyEl.classList.remove("visible")
    }
    if (this._adapter !== null) {
      try {
        this._adapter.setData(v)
        const fitOnLoad = this.getAttribute("fit-on-load") !== "false"
        if (fitOnLoad === true && typeof this._adapter.fit === "function") {
          this._adapter.fit()
        }
      } catch (err) {
        this._showError(err.message)
      }
    } else if (this._renderTargetEl !== null) {
      this._renderBuiltin()
    }
  }

  get selectedNodeId() { return this._selectedNodeId }
  set selectedNodeId(id) {
    const node = (this._graph && this._graph.nodes || []).find(n => n.id === id)
    if (node === undefined) {
      console.warn(`<mj-diagram>: Node id "${id}" not found in graph.`)
      this._selectedNodeId = null
      if (this._adapter !== null) { this._adapter.deselectAll() }
      return
    }
    this._selectedNodeId = id
    if (this._adapter !== null) { this._adapter.selectNode(id) }
    this._highlightNodeBtn(id)
  }

  get selectedEdgeId() { return this._selectedEdgeId }
  set selectedEdgeId(id) { this._selectedEdgeId = id }
}
