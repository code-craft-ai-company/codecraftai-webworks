/*
 * mjworkflowdiagram.js
 *
 * <mj-workflow-diagram> -- state machine or cross-actor swimlane process flow.
 * Nodes vary by type: start (filled circle), end (double circle), decision
 * (diamond), state (rectangle). Current state has a pulsing ring.
 *
 * SVG is aria-hidden; accessible adjacency list always present.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";

const NODE_W = 120;
const NODE_H = 44;
const NODE_GAP_X = 56;
const NODE_GAP_Y = 20;
const SWIMLANE_LABEL_W = 100;
const PAD = 20;

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
.svg-wrap { overflow: auto; }
svg { display: block; }
.node-el { cursor: pointer; }
.node-el:focus { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); }
.edge-el { cursor: pointer; }
.edge-el:focus { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); }
.detail-panel { padding: var(--mj-space-3); background: var(--mj-surface-raised); border-top: 1px solid var(--mj-border); }
.detail-panel h3 { margin: 0 0 var(--mj-space-2); font-size: var(--mj-font-size-sm); }
.a11y-list-wrap { padding: var(--mj-space-3); }
.a11y-list-wrap dl { margin: 0; font-size: var(--mj-font-size-sm); }
.a11y-list-wrap dt { font-weight: var(--mj-font-weight-medium); margin-top: var(--mj-space-2); }
.a11y-list-wrap dd { margin-left: var(--mj-space-4); color: var(--mj-text-muted); }
[hidden] { display: none !important; }
@keyframes mj-current-pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
.current-pulse { animation: mj-current-pulse var(--mj-current-state-pulse, 1.5s) ease-in-out infinite; }
@media (prefers-reduced-motion: reduce) { .current-pulse { animation: none; } }
`;

export class MjWorkflowDiagram extends MjElement {
  static tagName = "mj-workflow-diagram";
  static styles = STYLES;
  static watched = ["diagram-type", "swimlane-direction", "current-state", "layout", "show-labels"];

  constructor() {
    super();
    this._data = null;
    this._selectedNode = null;
    this._selectedTransition = null;
    this._showList = false;
    this._prevCurrentState = null;
    this._listId = nextId("mj-wd-list");
  }

  render() {
    return `
      <div class="wrapper" part="wrapper" role="img" aria-label="Workflow diagram">
        <div class="toolbar" part="toolbar">
          <button class="btn-toggle-list" aria-controls="${this._listId}" aria-expanded="false">Show accessible list</button>
        </div>
        <div class="svg-wrap" part="canvas">
          <svg part="svg" aria-hidden="true"></svg>
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

  get selectedTransition() {
    return this._selectedTransition;
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
    this._selectedTransition = null;
    return;
  }

  _layoutNodes(states, transitions, actors) {
    const diagramType = this.getAttribute("diagram-type") || "state";
    const nodePos = {};

    if (diagramType === "swimlane" && actors !== null && actors !== undefined && actors.length > 0) {
      actors.forEach((actor, ai) => {
        const actorStates = states.filter((s) => (s.actor || s.actorId || "") === (actor.id || actor.name));
        actorStates.forEach((s, si) => {
          nodePos[s.id || s.name] = {
            x: SWIMLANE_LABEL_W + PAD + si * (NODE_W + NODE_GAP_X),
            y: PAD + ai * (NODE_H + NODE_GAP_Y * 3),
          };
        });
      });
    } else {
      const inDegree = {};
      const adj = {};
      states.forEach((s) => {
        const id = s.id || s.name;
        inDegree[id] = 0;
        adj[id] = [];
      });
      transitions.forEach((t) => {
        if (inDegree[t.to] !== undefined) {
          inDegree[t.to] = inDegree[t.to] + 1;
        }
        if (adj[t.from] !== undefined) {
          adj[t.from].push(t.to);
        }
      });

      const levels = {};
      const queue = states.filter((s) => inDegree[s.id || s.name] === 0).map((s) => s.id || s.name);
      let level = 0;
      const visited = new Set();
      while (queue.length > 0) {
        const next = [];
        queue.forEach((id) => {
          if (!visited.has(id)) {
            levels[id] = level;
            visited.add(id);
            (adj[id] || []).forEach((nb) => {
              inDegree[nb] = inDegree[nb] - 1;
              if (inDegree[nb] <= 0) {
                next.push(nb);
              }
            });
          }
        });
        queue.length = 0;
        queue.push(...next);
        level = level + 1;
        if (level > states.length + 1) {
          break;
        }
      }
      states.forEach((s) => {
        const id = s.id || s.name;
        if (levels[id] === undefined) {
          levels[id] = level;
        }
      });

      const nodesPerLevel = {};
      states.forEach((s) => {
        const id = s.id || s.name;
        const lv = levels[id] || 0;
        if (nodesPerLevel[lv] === undefined) {
          nodesPerLevel[lv] = [];
        }
        nodesPerLevel[lv].push(id);
      });

      const maxInLevel = Object.values(nodesPerLevel).reduce((m, a) => Math.max(m, a.length), 0);
      const totalH = maxInLevel * (NODE_H + NODE_GAP_Y);
      Object.keys(nodesPerLevel).forEach((lv) => {
        const arr = nodesPerLevel[lv];
        const startY = (totalH - arr.length * (NODE_H + NODE_GAP_Y)) / 2 + PAD;
        arr.forEach((id, i) => {
          nodePos[id] = {
            x: PAD + parseInt(lv, 10) * (NODE_W + NODE_GAP_X),
            y: startY + i * (NODE_H + NODE_GAP_Y),
          };
        });
      });
    }

    return nodePos;
  }

  _draw() {
    const d = this._data;
    if (d === null || d === undefined) {
      return;
    }
    const states = d.states || [];
    const transitions = d.transitions || [];
    const actors = d.actors || [];
    const currentStateId = this.getAttribute("current-state") || "";
    const showLabels = this.getAttribute("show-labels") !== "false";
    const diagramType = this.getAttribute("diagram-type") || "state";

    const nodePos = this._layoutNodes(states, transitions, actors);

    const allX = Object.values(nodePos).map((p) => p.x);
    const allY = Object.values(nodePos).map((p) => p.y);
    const svgW = Math.max(400, (allX.length > 0 ? Math.max(...allX) : 0) + NODE_W + PAD * 2);
    const svgH = Math.max(200, (allY.length > 0 ? Math.max(...allY) : 0) + NODE_H + PAD * 2);

    let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${svgW}" height="${svgH}">`;
    svg += `<defs><marker id="wd-arrow" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="var(--mj-text-muted)"/></marker></defs>`;

    if (diagramType === "swimlane" && actors.length > 0) {
      actors.forEach((actor, ai) => {
        const laneY = PAD + ai * (NODE_H + NODE_GAP_Y * 3) - NODE_GAP_Y;
        const laneH = NODE_H + NODE_GAP_Y * 2.5;
        const bgColor = ai % 2 === 0 ? "var(--mj-bg)" : "var(--mj-bg-subtle)";
        svg += `<rect x="0" y="${laneY}" width="${svgW}" height="${laneH}" fill="${bgColor}" part="swimlane" aria-hidden="true"/>`;
        svg += `<text x="${SWIMLANE_LABEL_W - 8}" y="${laneY + laneH / 2 + 4}" text-anchor="end" font-size="11" fill="var(--mj-text-muted)" part="swimlane-label">${this._esc(actor.name || actor.id)}</text>`;
      });
    }

    transitions.forEach((t, ti) => {
      const fromPos = nodePos[t.from];
      const toPos = nodePos[t.to];
      if (fromPos === undefined || toPos === undefined) {
        return;
      }
      const x1 = fromPos.x + NODE_W;
      const y1 = fromPos.y + NODE_H / 2;
      const x2 = toPos.x;
      const y2 = toPos.y + NODE_H / 2;
      const midX = (x1 + x2) / 2;
      const ariaLabel = `Transition from ${t.from} to ${t.to}${t.label ? ": " + t.label : ""}`;
      svg += `<path class="edge-el" part="transition-edge" tabindex="0" role="button" aria-label="${this._esc(ariaLabel)}" d="M${x1},${y1} C${midX},${y1} ${midX},${y2} ${x2},${y2}" stroke="var(--mj-border-strong)" stroke-width="1.5" fill="none" marker-end="url(#wd-arrow)" data-transition-idx="${ti}"/>`;
      if (showLabels && t.label !== undefined && t.label !== null && t.label !== "") {
        const lx = (x1 + x2) / 2;
        const ly = (y1 + y2) / 2 - 6;
        svg += `<text x="${lx}" y="${ly}" text-anchor="middle" font-size="9" fill="var(--mj-text-muted)" part="transition-label">${this._esc(t.label.length > 16 ? t.label.slice(0, 14) + "…" : t.label)}</text>`;
      }
    });

    states.forEach((s) => {
      const id = s.id || s.name;
      const pos = nodePos[id];
      if (pos === undefined) {
        return;
      }
      const isCurrent = id === currentStateId;
      const type = s.type || "state";
      const ariaLabel = `${s.name || id}, type: ${type}${isCurrent ? ", current state" : ""}`;
      const nodeBg = isCurrent ? "var(--mj-color-info-surface)" : "var(--mj-surface)";
      const nodeBorder = isCurrent ? "var(--mj-color-info)" : "var(--mj-border-strong)";

      svg += `<g class="node-el" part="${isCurrent ? "state-node-current" : "state-node"}" tabindex="0" role="button" aria-label="${this._esc(ariaLabel)}" data-node-id="${this._esc(id)}" ${isCurrent ? 'aria-current="step"' : ""}>`;

      if (type === "start") {
        const cx = pos.x + NODE_W / 2;
        const cy = pos.y + NODE_H / 2;
        svg += `<circle cx="${cx}" cy="${cy}" r="${NODE_H / 3}" fill="var(--mj-text)" part="start-node" aria-hidden="true"/>`;
      } else if (type === "end") {
        const cx = pos.x + NODE_W / 2;
        const cy = pos.y + NODE_H / 2;
        svg += `<circle cx="${cx}" cy="${cy}" r="${NODE_H / 3}" fill="none" stroke="var(--mj-text)" stroke-width="3" part="end-node" aria-hidden="true"/>`;
        svg += `<circle cx="${cx}" cy="${cy}" r="${NODE_H / 3 - 5}" fill="var(--mj-text)" aria-hidden="true"/>`;
      } else if (type === "decision") {
        const cx = pos.x + NODE_W / 2;
        const cy = pos.y + NODE_H / 2;
        const hw = NODE_W / 2 - 4;
        const hh = NODE_H / 2 - 2;
        svg += `<polygon points="${cx - hw},${cy} ${cx},${cy - hh} ${cx + hw},${cy} ${cx},${cy + hh}" fill="${nodeBg}" stroke="${nodeBorder}" stroke-width="1.5" part="decision-node" aria-hidden="true"/>`;
        svg += `<text x="${cx}" y="${cy + 4}" text-anchor="middle" font-size="10" fill="var(--mj-text)">${this._esc((s.name || id).slice(0, 10))}</text>`;
      } else {
        svg += `<rect x="${pos.x}" y="${pos.y}" width="${NODE_W}" height="${NODE_H}" rx="6" fill="${nodeBg}" stroke="${nodeBorder}" stroke-width="1.5" aria-hidden="true"/>`;
        if (isCurrent) {
          svg += `<rect class="current-pulse" x="${pos.x - 3}" y="${pos.y - 3}" width="${NODE_W + 6}" height="${NODE_H + 6}" rx="8" fill="none" stroke="var(--mj-color-info)" stroke-width="2.5" aria-hidden="true"/>`;
        }
        svg += `<text x="${pos.x + NODE_W / 2}" y="${pos.y + NODE_H / 2 + 4}" text-anchor="middle" font-size="11" fill="var(--mj-text)">${this._esc((s.name || id).length > 14 ? (s.name || id).slice(0, 12) + "…" : (s.name || id))}</text>`;
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

    this._buildList(states, transitions);
    this.emit("mj-data-load", { states: states.length, transitions: transitions.length, actors: actors.length });

    const wrapper = this.$(".wrapper");
    if (wrapper !== null) {
      wrapper.setAttribute("aria-label", `Workflow diagram: ${states.length} states, ${transitions.length} transitions${actors.length > 0 ? `, ${actors.length} actors` : ""}`);
    }
    return;
  }

  _buildList(states, transitions) {
    if (this._dlEl === null || this._dlEl === undefined) {
      return;
    }
    const outgoing = {};
    transitions.forEach((t) => {
      if (outgoing[t.from] === undefined) {
        outgoing[t.from] = [];
      }
      outgoing[t.from].push(t.to + (t.label ? ` (${t.label})` : ""));
    });

    const items = states.map((s) => {
      const id = s.id || s.name;
      const outs = outgoing[id] || [];
      const ddContent = outs.length > 0 ? outs.join("; ") : "no outgoing transitions";
      return `<dt>${this._esc(s.name || id)}</dt><dd>${this._esc(ddContent)}</dd>`;
    });
    this._dlEl.innerHTML = items.join("");
    return;
  }

  _onSvgClick(event) {
    const nodeEl = event.target.closest("[data-node-id]");
    if (nodeEl !== null) {
      const id = nodeEl.getAttribute("data-node-id");
      const states = (this._data && this._data.states) || [];
      const node = states.find((s) => (s.id || s.name) === id);
      if (node !== undefined) {
        this._selectedNode = node;
        const h3 = this._detailPanel.querySelector("h3");
        if (h3 !== null) {
          h3.textContent = node.name || id;
        }
        this._detailContent.innerHTML = `<p><strong>Type:</strong> ${this._esc(node.type || "state")}</p>${node.description ? `<p>${this._esc(node.description)}</p>` : ""}`;
        this._detailPanel.hidden = false;
        this.emit("mj-node-select", { node });
      }
      return;
    }

    const edgeEl = event.target.closest("[data-transition-idx]");
    if (edgeEl !== null) {
      const idx = parseInt(edgeEl.getAttribute("data-transition-idx"), 10);
      const transitions = (this._data && this._data.transitions) || [];
      const transition = transitions[idx];
      if (transition !== undefined) {
        this._selectedTransition = transition;
        this.emit("mj-transition-select", { transition });
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

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "current-state" && this._data !== null) {
      const prev = oldValue || "";
      if (newValue !== prev) {
        this.emit("mj-state-change", { from: prev, to: newValue || "" });
        announce(`Current state: ${newValue || ""}`, "polite");
      }
    }
    if (this._svg !== undefined && this._data !== null) {
      this._draw();
    }
    return;
  }

  _esc(str) {
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
}
