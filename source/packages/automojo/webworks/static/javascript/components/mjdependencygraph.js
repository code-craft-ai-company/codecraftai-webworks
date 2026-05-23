/*
 * mjdependencygraph.js
 *
 * <mj-dependency-graph> -- directed node/edge graph of work items or modules
 * with critical path highlighting and cycle detection.
 *
 * Layout is computed client-side with a simple topological sort.
 * SVG is aria-hidden; accessible adjacency list always present.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";

const NODE_W = 160;
const NODE_H = 48;
const NODE_GAP_X = 60;
const NODE_GAP_Y = 24;
const PAD = 24;

const STATUS_COLORS = {
  todo:        "var(--mj-color-accent-200)",
  "in-progress": "var(--mj-color-info)",
  done:        "var(--mj-color-success)",
  blocked:     "var(--mj-color-danger)",
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
.toolbar { display: flex; align-items: center; gap: var(--mj-space-2); padding: var(--mj-space-2) var(--mj-space-3); border-bottom: 1px solid var(--mj-border); flex-wrap: wrap; }
.toolbar button { font: inherit; font-size: var(--mj-font-size-xs); background: var(--mj-surface); border: 1px solid var(--mj-border-strong); border-radius: var(--mj-radius-sm); padding: 2px var(--mj-space-2); cursor: pointer; color: var(--mj-text); }
.toolbar button:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: var(--mj-focus-ring-offset); }
.cycle-banner { background: var(--mj-color-danger-surface); color: var(--mj-color-danger); padding: var(--mj-space-2) var(--mj-space-3); font-size: var(--mj-font-size-xs); font-weight: var(--mj-font-weight-medium); }
.svg-wrap { overflow: auto; }
svg { display: block; }
.node-el { cursor: pointer; }
.node-el:focus { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); }
.detail-panel { padding: var(--mj-space-3); background: var(--mj-surface-raised); border-top: 1px solid var(--mj-border); }
.detail-panel h3 { margin: 0 0 var(--mj-space-2); font-size: var(--mj-font-size-sm); }
.a11y-list-wrap { padding: var(--mj-space-3); }
.a11y-list-wrap dl { margin: 0; font-size: var(--mj-font-size-sm); }
.a11y-list-wrap dt { font-weight: var(--mj-font-weight-medium); margin-top: var(--mj-space-2); }
.a11y-list-wrap dd { margin-left: var(--mj-space-4); color: var(--mj-text-muted); }
[hidden] { display: none !important; }
`;

export class MjDependencyGraph extends MjElement {
  static tagName = "mj-dependency-graph";
  static styles = STYLES;
  static watched = ["graph-type", "show-critical-path", "show-minimap", "layout"];

  constructor() {
    super();
    this._data = null;
    this._selectedNode = null;
    this._cycles = [];
    this._zoom = 1;
    this._showList = false;
    this._listId = nextId("mj-dg-list");
    this._cycleBannerId = nextId("mj-dg-cycle");
  }

  render() {
    return `
      <div class="wrapper" part="wrapper">
        <div class="toolbar" part="toolbar">
          <button class="btn-toggle-list" aria-controls="${this._listId}" aria-expanded="false">Show dependency list</button>
        </div>
        <div id="${this._cycleBannerId}" class="cycle-banner" role="alert" hidden></div>
        <div class="svg-wrap" part="canvas">
          <svg part="svg" role="img" aria-label="Dependency graph" aria-hidden="true"></svg>
        </div>
        <div class="detail-panel" part="detail-panel" role="dialog" aria-modal="false" hidden>
          <button class="close-btn" aria-label="Close">&#x2715;</button>
          <h3></h3>
          <div class="detail-content"></div>
          <slot name="node-detail"></slot>
        </div>
        <div id="${this._listId}" class="a11y-list-wrap" hidden>
          <dl part="a11y-list"></dl>
        </div>
        <slot hidden></slot>
      </div>`;
  }

  afterRender() {
    this._svg = this.$("svg");
    this._detailPanel = this.$(".detail-panel");
    this._detailContent = this.$(".detail-content");
    this._listWrap = this.$("#" + this._listId);
    this._dlEl = this.$("dl");
    this._toggleBtn = this.$(".btn-toggle-list");
    this._cycleBanner = this.$("#" + this._cycleBannerId);
    this.listen(this._toggleBtn, "click", this._onToggleList.bind(this));
    this.listen(this.$(".close-btn"), "click", this._closeDetail.bind(this));
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

  get selectedNode() {
    return this._selectedNode;
  }

  get cycles() {
    return this._cycles;
  }

  get zoom() {
    return this._zoom;
  }

  _onToggleList() {
    this._showList = !this._showList;
    this._listWrap.hidden = !this._showList;
    this._toggleBtn.setAttribute("aria-expanded", String(this._showList));
    return;
  }

  _closeDetail() {
    this._detailPanel.hidden = true;
    this._selectedNode = null;
    this.emit("mj-node-deselect", {});
    return;
  }

  _detectCycles(nodes, edges) {
    const adj = {};
    nodes.forEach((n) => {
      adj[n.id || n.name] = [];
    });
    edges.forEach((e) => {
      if (adj[e.from] !== undefined) {
        adj[e.from].push(e.to);
      }
    });

    const visited = new Set();
    const inStack = new Set();
    const cycles = [];

    const dfs = (nodeId, path) => {
      if (inStack.has(nodeId)) {
        const cycleStart = path.indexOf(nodeId);
        cycles.push(path.slice(cycleStart));
        return;
      }
      if (visited.has(nodeId)) {
        return;
      }
      visited.add(nodeId);
      inStack.add(nodeId);
      const neighbors = adj[nodeId] || [];
      for (let i = 0; i < neighbors.length; i = i + 1) {
        dfs(neighbors[i], [...path, nodeId]);
      }
      inStack.delete(nodeId);
      return;
    };

    nodes.forEach((n) => {
      const id = n.id || n.name;
      if (!visited.has(id)) {
        dfs(id, []);
      }
    });

    return cycles;
  }

  _topoLevels(nodes, edges) {
    const inDegree = {};
    const adj = {};
    nodes.forEach((n) => {
      const id = n.id || n.name;
      inDegree[id] = 0;
      adj[id] = [];
    });
    edges.forEach((e) => {
      if (inDegree[e.to] !== undefined) {
        inDegree[e.to] = (inDegree[e.to] || 0) + 1;
      }
      if (adj[e.from] !== undefined) {
        adj[e.from].push(e.to);
      }
    });

    const levels = {};
    const queue = nodes.filter((n) => inDegree[n.id || n.name] === 0).map((n) => n.id || n.name);
    let level = 0;
    while (queue.length > 0) {
      const next = [];
      queue.forEach((id) => {
        levels[id] = level;
        (adj[id] || []).forEach((neighbor) => {
          inDegree[neighbor] = (inDegree[neighbor] || 1) - 1;
          if (inDegree[neighbor] === 0) {
            next.push(neighbor);
          }
        });
      });
      queue.length = 0;
      queue.push(...next);
      level = level + 1;
      if (level > nodes.length) {
        break;
      }
    }

    nodes.forEach((n) => {
      const id = n.id || n.name;
      if (levels[id] === undefined) {
        levels[id] = level;
      }
    });

    return levels;
  }

  _draw() {
    const d = this._data;
    if (d === null || d === undefined) {
      return;
    }
    const nodes = d.nodes || [];
    const edges = d.edges || [];
    const criticalPath = d.criticalPath || [];
    const showCritical = this.getAttribute("show-critical-path") !== "false";

    this._cycles = this._detectCycles(nodes, edges);

    if (this._cycles.length > 0) {
      const cycleNodeNames = this._cycles.map((c) => c.join(" → ")).join("; ");
      this._cycleBanner.textContent = `⚠ Cycle detected: ${cycleNodeNames}`;
      this._cycleBanner.hidden = false;
      this.emit("mj-cycle-detected", { cycles: this._cycles });
      announce(`Cycle detected in dependency graph: ${cycleNodeNames}`, "assertive");
    } else {
      this._cycleBanner.hidden = true;
    }

    const levels = this._topoLevels(nodes, edges);
    const maxLevel = Math.max(0, ...Object.values(levels));
    const nodesPerLevel = {};
    nodes.forEach((n) => {
      const id = n.id || n.name;
      const lv = levels[id] || 0;
      if (nodesPerLevel[lv] === undefined) {
        nodesPerLevel[lv] = [];
      }
      nodesPerLevel[lv].push(id);
    });

    const maxNodesInLevel = Object.values(nodesPerLevel).reduce((m, arr) => Math.max(m, arr.length), 0);
    const svgW = PAD * 2 + (maxLevel + 1) * (NODE_W + NODE_GAP_X);
    const svgH = PAD * 2 + maxNodesInLevel * (NODE_H + NODE_GAP_Y);

    const nodePos = {};
    Object.keys(nodesPerLevel).forEach((lv) => {
      const lvNum = parseInt(lv, 10);
      const arr = nodesPerLevel[lv];
      const totalH = arr.length * (NODE_H + NODE_GAP_Y) - NODE_GAP_Y;
      const startY = (svgH - totalH) / 2;
      arr.forEach((id, i) => {
        nodePos[id] = {
          x: PAD + lvNum * (NODE_W + NODE_GAP_X),
          y: startY + i * (NODE_H + NODE_GAP_Y),
        };
      });
    });

    const cycleNodeIds = new Set(this._cycles.flat());
    const criticalSet = new Set(criticalPath);

    let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${svgW}" height="${svgH}">`;
    svg += `<defs><marker id="dg-arrow" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="var(--mj-text-muted)"/></marker><marker id="dg-arrow-crit" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="var(--mj-color-warning)"/></marker></defs>`;

    edges.forEach((e) => {
      const fromPos = nodePos[e.from];
      const toPos = nodePos[e.to];
      if (fromPos === undefined || toPos === undefined) {
        return;
      }
      const isCrit = showCritical && criticalSet.has(e.from) && criticalSet.has(e.to);
      const x1 = fromPos.x + NODE_W;
      const y1 = fromPos.y + NODE_H / 2;
      const x2 = toPos.x;
      const y2 = toPos.y + NODE_H / 2;
      const midX = (x1 + x2) / 2;
      const stroke = isCrit ? "var(--mj-color-warning)" : "var(--mj-border-strong)";
      const strokeW = isCrit ? 2.5 : 1.5;
      svg += `<path part="${isCrit ? "critical-path-edge" : "edge"}" d="M${x1},${y1} C${midX},${y1} ${midX},${y2} ${x2},${y2}" stroke="${stroke}" stroke-width="${strokeW}" fill="none" marker-end="url(#${isCrit ? "dg-arrow-crit" : "dg-arrow"})" aria-hidden="true"/>`;
    });

    nodes.forEach((n) => {
      const id = n.id || n.name;
      const pos = nodePos[id];
      if (pos === undefined) {
        return;
      }
      const isCrit = showCritical && criticalSet.has(id);
      const hasCycle = cycleNodeIds.has(id);
      const color = STATUS_COLORS[n.status] || STATUS_COLORS.todo;
      const borderColor = isCrit ? "var(--mj-color-warning)" : "var(--mj-border-strong)";
      const borderW = isCrit ? 2.5 : 1.5;
      const bg = isCrit ? "var(--mj-color-warning-surface)" : "var(--mj-surface)";
      const critText = isCrit ? ", on critical path" : "";
      const cycleText = hasCycle ? ", in cycle" : "";
      const ariaLabel = `${n.name || id}, status: ${n.status || "todo"}${critText}${cycleText}`;

      svg += `<g class="node-el" part="${isCrit ? "critical-path-node" : "node"}" tabindex="0" role="button" aria-label="${this._esc(ariaLabel)}" data-node-id="${this._esc(id)}" ${isCrit ? 'data-critical="true"' : ""} ${hasCycle ? 'data-cycle="true"' : ""}>`;
      svg += `<rect x="${pos.x}" y="${pos.y}" width="${NODE_W}" height="${NODE_H}" rx="4" fill="${bg}" stroke="${borderColor}" stroke-width="${borderW}"/>`;
      svg += `<text x="${pos.x + (hasCycle ? 12 : 8)}" y="${pos.y + NODE_H / 2 - 6}" font-size="11" fill="var(--mj-text)" font-weight="500">${this._esc((n.name || id).length > 18 ? (n.name || id).slice(0, 16) + "…" : (n.name || id))}</text>`;
      svg += `<text x="${pos.x + 8}" y="${pos.y + NODE_H / 2 + 10}" font-size="10" fill="${color}">${this._esc(n.status || "todo")}</text>`;
      if (hasCycle) {
        svg += `<text x="${pos.x + NODE_W - 16}" y="${pos.y + 14}" font-size="12" fill="var(--mj-color-danger)" part="cycle-badge">⚠</text>`;
      }
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

    this._buildList(nodes, edges);
    this.emit("mj-data-load", { nodes: nodes.length, edges: edges.length, hasCycles: this._cycles.length > 0 });

    const wrapper = this.$(".wrapper");
    if (wrapper !== null) {
      wrapper.setAttribute("aria-label", `Dependency graph: ${nodes.length} nodes, ${edges.length} edges${criticalPath.length > 0 ? `, critical path: ${criticalPath.length} nodes` : ""}`);
    }
    return;
  }

  _buildList(nodes, edges) {
    if (this._dlEl === null || this._dlEl === undefined) {
      return;
    }
    const adj = {};
    edges.forEach((e) => {
      if (adj[e.to] === undefined) {
        adj[e.to] = [];
      }
      const fromNode = nodes.find((n) => (n.id || n.name) === e.from);
      if (fromNode !== undefined) {
        adj[e.to].push(fromNode.name || fromNode.id);
      }
    });

    const items = nodes.map((n) => {
      const id = n.id || n.name;
      const prereqs = adj[id] || [];
      const ddContent = prereqs.length > 0 ? `depends on: ${prereqs.join(", ")}` : "no dependencies";
      return `<dt>${this._esc(n.name || id)}</dt><dd>${this._esc(ddContent)}</dd>`;
    });
    this._dlEl.innerHTML = items.join("");
    return;
  }

  _onSvgClick(event) {
    const el = event.target.closest("[data-node-id]");
    if (el !== null) {
      const id = el.getAttribute("data-node-id");
      const nodes = (this._data && this._data.nodes) || [];
      const node = nodes.find((n) => (n.id || n.name) === id);
      if (node !== undefined) {
        this._selectedNode = node;
        const h3 = this._detailPanel.querySelector("h3");
        if (h3 !== null) {
          h3.textContent = node.name || id;
        }
        this._detailContent.innerHTML = `<p><strong>Status:</strong> ${this._esc(node.status || "todo")}</p>${node.estimate !== undefined ? `<p><strong>Estimate:</strong> ${node.estimate}</p>` : ""}`;
        this._detailPanel.hidden = false;
        this.emit("mj-node-select", { node });
      }
    }
    return;
  }

  _onSvgKeydown(event) {
    if (event.key === "Enter" || event.key === " ") {
      this._onSvgClick(event);
    }
    if (event.key === "Escape") {
      this._closeDetail();
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
