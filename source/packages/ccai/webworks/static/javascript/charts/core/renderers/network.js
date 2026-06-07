/*
 * network.js
 *
 * Network / node-link renderer.
 *
 * Registers: "network", "arc-diagram", "node-link", "edge-bundling",
 *            "dependency-graph"
 *
 * ctx.raw shape:
 *   nodes: [{ id, label?, group?, value? }]
 *   links: [{ source, target, value? }]
 *
 * Layouts (selected via ctx.attrs("layout", "force")):
 *   "force"   — iterative spring-repulsion (default for network/node-link/
 *               edge-bundling)
 *   "arc"     — nodes on a single horizontal axis, edges as arcs
 *   "layered" — BFS-rank Sugiyama layout (default for dependency-graph)
 *
 * Orientation: "horizontal" / "vertical" — relevant only for "layered" and
 *   "arc" layouts.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber } from "../svgdraw.js";
import { sqrtScale, linearScale } from "../scales.js";


const MARGIN = { top: 24, right: 24, bottom: 24, left: 24 };
const MIN_RADIUS = 5;
const MAX_RADIUS = 18;
const ARROW_SIZE = 7;
const FORCE_ITERATIONS = 180;
const FORCE_REPULSION = 2400;
const FORCE_LINK_STRENGTH = 0.06;
const FORCE_DAMPING = 0.82;


/* ---------- shared helpers ---------- */

function _buildIndexMap(nodes) {
  /*
   * Map node id to array index.
   */
  const map = {};
  for (let i = 0; i < nodes.length; i = i + 1) {
    map[nodes[i].id] = i;
  }
  return map;
}


function _nodeRadius(nodes, indexMap, nodeValues) {
  /*
   * Build a sqrt scale for node radii based on optional node.value.
   */
  let maxVal = 1;
  for (let i = 0; i < nodes.length; i = i + 1) {
    const v = typeof nodes[i].value === "number" ? nodes[i].value : 1;
    if (v > maxVal) {
      maxVal = v;
    }
  }
  const scale = sqrtScale([0, maxVal], [MIN_RADIUS, MAX_RADIUS]);
  const radii = [];
  for (let i = 0; i < nodes.length; i = i + 1) {
    const v = typeof nodes[i].value === "number" ? nodes[i].value : 1;
    radii.push(scale(v));
  }
  return radii;
}


function _arrowPts(tx, ty, angle) {
  /*
   * Arrowhead polygon string at (tx,ty) pointing in `angle` direction.
   */
  const a1 = angle + Math.PI * 0.8;
  const a2 = angle - Math.PI * 0.8;
  const x1 = tx + ARROW_SIZE * Math.cos(a1);
  const y1 = ty + ARROW_SIZE * Math.sin(a1);
  const x2 = tx + ARROW_SIZE * Math.cos(a2);
  const y2 = ty + ARROW_SIZE * Math.sin(a2);
  return `${tx.toFixed(2)},${ty.toFixed(2)} ${x1.toFixed(2)},${y1.toFixed(2)} ${x2.toFixed(2)},${y2.toFixed(2)}`;
}


/* ---------- force-directed layout ---------- */

function _forceLayout(nodes, links, plotW, plotH, indexMap) {
  /*
   * Iterative spring-repulsion layout.  Returns an array of {x, y} positions
   * in the same order as `nodes`.
   */
  const n = nodes.length;
  const pos = [];
  const vel = [];

  /* Initialise on a circle to avoid degenerate start. */
  for (let i = 0; i < n; i = i + 1) {
    const angle = (2 * Math.PI * i) / n;
    pos.push({
      x: plotW / 2 + (plotW / 3) * Math.cos(angle),
      y: plotH / 2 + (plotH / 3) * Math.sin(angle)
    });
    vel.push({ x: 0, y: 0 });
  }

  /* Desired link length proportional to canvas diagonal. */
  const linkLen = Math.sqrt(plotW * plotW + plotH * plotH) / Math.max(n, 4) * 2;

  for (let iter = 0; iter < FORCE_ITERATIONS; iter = iter + 1) {
    const force = [];
    for (let i = 0; i < n; i = i + 1) {
      force.push({ x: 0, y: 0 });
    }

    /* Repulsion: every pair of nodes repels. */
    for (let i = 0; i < n; i = i + 1) {
      for (let j = i + 1; j < n; j = j + 1) {
        const dx = pos[j].x - pos[i].x;
        const dy = pos[j].y - pos[i].y;
        const dist2 = dx * dx + dy * dy;
        const dist = Math.sqrt(dist2) + 0.01;
        const mag = FORCE_REPULSION / dist2;
        const fx = (dx / dist) * mag;
        const fy = (dy / dist) * mag;
        force[i].x = force[i].x - fx;
        force[i].y = force[i].y - fy;
        force[j].x = force[j].x + fx;
        force[j].y = force[j].y + fy;
      }
    }

    /* Attraction: links pull connected nodes together. */
    for (let k = 0; k < links.length; k = k + 1) {
      const si = indexMap[links[k].source];
      const ti = indexMap[links[k].target];
      if (si === undefined || ti === undefined) {
        continue;
      }
      const dx = pos[ti].x - pos[si].x;
      const dy = pos[ti].y - pos[si].y;
      const dist = Math.sqrt(dx * dx + dy * dy) + 0.01;
      const mag = FORCE_LINK_STRENGTH * (dist - linkLen);
      const fx = (dx / dist) * mag;
      const fy = (dy / dist) * mag;
      force[si].x = force[si].x + fx;
      force[si].y = force[si].y + fy;
      force[ti].x = force[ti].x - fx;
      force[ti].y = force[ti].y - fy;
    }

    /* Centering force (weak). */
    for (let i = 0; i < n; i = i + 1) {
      force[i].x = force[i].x + (plotW / 2 - pos[i].x) * 0.01;
      force[i].y = force[i].y + (plotH / 2 - pos[i].y) * 0.01;
    }

    /* Integrate. */
    for (let i = 0; i < n; i = i + 1) {
      vel[i].x = (vel[i].x + force[i].x) * FORCE_DAMPING;
      vel[i].y = (vel[i].y + force[i].y) * FORCE_DAMPING;
      pos[i].x = pos[i].x + vel[i].x;
      pos[i].y = pos[i].y + vel[i].y;
      /* Clamp to canvas. */
      if (pos[i].x < MAX_RADIUS) { pos[i].x = MAX_RADIUS; }
      if (pos[i].x > plotW - MAX_RADIUS) { pos[i].x = plotW - MAX_RADIUS; }
      if (pos[i].y < MAX_RADIUS) { pos[i].y = MAX_RADIUS; }
      if (pos[i].y > plotH - MAX_RADIUS) { pos[i].y = plotH - MAX_RADIUS; }
    }
  }

  return pos;
}


/* ---------- arc layout ---------- */

function _arcLayout(nodes, plotW, plotH, horizontal) {
  /*
   * Place nodes evenly along one axis.
   */
  const n = nodes.length;
  const pos = [];
  for (let i = 0; i < n; i = i + 1) {
    const t = n > 1 ? i / (n - 1) : 0.5;
    if (horizontal === true) {
      pos.push({ x: MAX_RADIUS + t * (plotW - MAX_RADIUS * 2), y: plotH * 0.7 });
    } else {
      pos.push({ x: plotW * 0.5, y: MAX_RADIUS + t * (plotH - MAX_RADIUS * 2) });
    }
  }
  return pos;
}


/* ---------- layered (BFS rank) layout ---------- */

function _layeredLayout(nodes, links, plotW, plotH, horizontal, indexMap) {
  /*
   * Assign positions via BFS ranks (Sugiyama-style).
   */
  const n = nodes.length;
  const ids = nodes.map((nd) => nd.id);

  const outEdges = {};
  const inDegree = {};
  for (let i = 0; i < n; i = i + 1) {
    outEdges[ids[i]] = [];
    inDegree[ids[i]] = 0;
  }
  for (let k = 0; k < links.length; k = k + 1) {
    const lk = links[k];
    if (outEdges[lk.source] !== undefined && inDegree[lk.target] !== undefined) {
      outEdges[lk.source].push(lk.target);
      inDegree[lk.target] = inDegree[lk.target] + 1;
    }
  }

  const rank = {};
  const queue = [];
  for (let i = 0; i < n; i = i + 1) {
    if (inDegree[ids[i]] === 0) {
      rank[ids[i]] = 0;
      queue.push(ids[i]);
    }
  }
  if (queue.length === 0 && n > 0) {
    rank[ids[0]] = 0;
    queue.push(ids[0]);
  }

  let head = 0;
  while (head < queue.length) {
    const cur = queue[head];
    head = head + 1;
    const nbrs = outEdges[cur] || [];
    for (let nb = 0; nb < nbrs.length; nb = nb + 1) {
      const candidate = rank[cur] + 1;
      if (rank[nbrs[nb]] === undefined || rank[nbrs[nb]] < candidate) {
        rank[nbrs[nb]] = candidate;
        queue.push(nbrs[nb]);
      }
    }
  }

  let maxRank = 0;
  for (let i = 0; i < n; i = i + 1) {
    if (rank[ids[i]] === undefined) { rank[ids[i]] = 0; }
    if (rank[ids[i]] > maxRank) { maxRank = rank[ids[i]]; }
  }

  const columns = [];
  for (let r = 0; r <= maxRank; r = r + 1) { columns.push([]); }
  for (let i = 0; i < n; i = i + 1) { columns[rank[ids[i]]].push(ids[i]); }

  const pos = new Array(n);
  for (let r = 0; r < columns.length; r = r + 1) {
    const col = columns[r];
    const numCols = columns.length;
    const rankPos = numCols > 1
      ? (r / (numCols - 1)) * (horizontal ? plotW - MAX_RADIUS * 2 : plotH - MAX_RADIUS * 2) + MAX_RADIUS
      : (horizontal ? plotW : plotH) / 2;
    const crossSpan = horizontal ? plotH : plotW;
    for (let c = 0; c < col.length; c = c + 1) {
      const crossPos = col.length > 1
        ? (c / (col.length - 1)) * (crossSpan - MAX_RADIUS * 2) + MAX_RADIUS
        : crossSpan / 2;
      const ni = indexMap[col[c]];
      if (ni !== undefined) {
        if (horizontal === true) {
          pos[ni] = { x: rankPos, y: crossPos };
        } else {
          pos[ni] = { x: crossPos, y: rankPos };
        }
      }
    }
  }
  return pos;
}


/* ---------- renderer core ---------- */

function _drawLinks(plot, links, pos, radii, indexMap, ctx, drawArrows) {
  /*
   * Draw link lines / arcs between nodes.
   */
  let maxLinkVal = 1;
  for (let k = 0; k < links.length; k = k + 1) {
    const v = typeof links[k].value === "number" ? links[k].value : 1;
    if (v > maxLinkVal) { maxLinkVal = v; }
  }
  const strokeScale = linearScale([0, maxLinkVal], [1, 4]);

  for (let k = 0; k < links.length; k = k + 1) {
    const link = links[k];
    const si = indexMap[link.source];
    const ti = indexMap[link.target];
    if (si === undefined || ti === undefined) { continue; }

    const value = typeof link.value === "number" ? link.value : 1;
    const strokeW = strokeScale(value);

    const sx = pos[si].x;
    const sy = pos[si].y;
    const tx = pos[ti].x;
    const ty = pos[ti].y;
    const angle = Math.atan2(ty - sy, tx - sx);
    const dist = Math.sqrt((tx - sx) * (tx - sx) + (ty - sy) * (ty - sy));
    const tr = radii[ti];

    const ex = tx - tr * Math.cos(angle);
    const ey = ty - tr * Math.sin(angle);

    const edgeG = svgEl("g", { part: "edge" }, []);
    edgeG.appendChild(svgEl("line", {
      x1: sx.toFixed(2),
      y1: sy.toFixed(2),
      x2: ex.toFixed(2),
      y2: ey.toFixed(2),
      stroke: "var(--mj-border-strong, #c7ccd6)",
      "stroke-width": strokeW.toFixed(2),
      "stroke-opacity": "0.7"
    }, []));

    if (drawArrows === true) {
      const arrowPts = _arrowPts(ex, ey, angle);
      edgeG.appendChild(svgEl("polygon", {
        points: arrowPts,
        fill: "var(--mj-border-strong, #c7ccd6)"
      }, []));
    }

    const capturedLink = link;
    const capturedValue = value;
    edgeG.addEventListener("click", () => {
      ctx.emit("mj-chart-edge-click", {
        source: capturedLink.source,
        target: capturedLink.target,
        value: capturedValue
      });
    });
    plot.appendChild(edgeG);
  }
}


function _drawArcLinks(plot, links, pos, indexMap, ctx, horizontal) {
  /*
   * Draw links as arcs above (or to the left of) the node axis.
   */
  for (let k = 0; k < links.length; k = k + 1) {
    const link = links[k];
    const si = indexMap[link.source];
    const ti = indexMap[link.target];
    if (si === undefined || ti === undefined) { continue; }

    const sx = pos[si].x;
    const sy = pos[si].y;
    const tx = pos[ti].x;
    const ty = pos[ti].y;

    /* Arc: half circle through midpoint. */
    const midX = (sx + tx) / 2;
    const midY = (sy + ty) / 2;
    const span = horizontal
      ? Math.abs(tx - sx)
      : Math.abs(ty - sy);
    const arcR = span / 2;

    let pathD;
    if (horizontal === true) {
      const sweep = sx < tx ? 1 : 0;
      pathD = `M${sx.toFixed(2)},${sy.toFixed(2)} ` +
        `A${arcR.toFixed(2)},${arcR.toFixed(2)} 0 0 ${sweep} ` +
        `${tx.toFixed(2)},${ty.toFixed(2)}`;
    } else {
      const sweep = sy < ty ? 1 : 0;
      pathD = `M${sx.toFixed(2)},${sy.toFixed(2)} ` +
        `A${arcR.toFixed(2)},${arcR.toFixed(2)} 0 0 ${sweep} ` +
        `${tx.toFixed(2)},${ty.toFixed(2)}`;
    }

    const arcPath = svgEl("path", {
      d: pathD,
      fill: "none",
      stroke: "var(--mj-color-accent-500, #2563eb)",
      "stroke-width": "1.5",
      "stroke-opacity": "0.55",
      part: "arc-link"
    }, []);
    arcPath.appendChild(svgEl("title", null,
      `${link.source} → ${link.target}`));
    const capturedLink = link;
    arcPath.addEventListener("click", () => {
      ctx.emit("mj-chart-edge-click", {
        source: capturedLink.source,
        target: capturedLink.target
      });
    });
    plot.appendChild(arcPath);
  }
}


function _drawNodes(plot, nodes, pos, radii, ctx) {
  /*
   * Draw node circles and labels.
   */
  for (let i = 0; i < nodes.length; i = i + 1) {
    const node = nodes[i];
    const r = radii[i];
    const color = ctx.colorFor(node.group !== undefined ? node.group : i);

    const circle = svgEl("circle", {
      cx: pos[i].x.toFixed(2),
      cy: pos[i].y.toFixed(2),
      r: r.toFixed(2),
      fill: color,
      "fill-opacity": "0.85",
      stroke: "var(--mj-bg, #ffffff)",
      "stroke-width": 1.5,
      part: "node",
      tabindex: "0",
      role: "img",
      "aria-label": escapeHtml(node.label || node.id)
    }, []);
    circle.appendChild(svgEl("title", null,
      `${node.label || node.id}${node.value !== undefined ? ': ' + formatNumber(node.value) : ''}`));

    const capturedNode = node;
    const nodeClickHandler = () => {
      ctx.emit("mj-chart-node-click", {
        id: capturedNode.id,
        label: capturedNode.label || capturedNode.id,
        group: capturedNode.group || null
      });
    };
    circle.addEventListener("click", nodeClickHandler);
    circle.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        nodeClickHandler();
      }
    });
    plot.appendChild(circle);

    /* Label below (or right of) the node. */
    plot.appendChild(svgEl("text", {
      x: pos[i].x.toFixed(2),
      y: (pos[i].y + r + 12).toFixed(2),
      "text-anchor": "middle",
      "font-size": 10,
      fill: "var(--mj-text, #14181f)"
    }, escapeHtml(node.label || node.id)));
  }
}


export function render(ctx) {
  /*
   * Render a network / node-link / arc / dependency-graph chart.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw;
  const type = ctx.attrs("type", "network");
  const horizontal = ctx.orientation === "horizontal";

  /* Default layout depends on registered type. Caller can override. */
  const defaultLayout = (type === "dependency-graph") ? "layered" : "force";
  const layout = ctx.attrs("layout", defaultLayout);
  const isArc = layout === "arc";
  const isLayered = layout === "layered";
  const drawArrows = isLayered || (type === "dependency-graph");

  const root = svgEl("g", { part: "plot" }, []);

  const nodes = (raw && Array.isArray(raw.nodes)) ? raw.nodes : [];
  const links = (raw && Array.isArray(raw.links)) ? raw.links : [];

  if (nodes.length === 0) {
    return root;
  }

  const plotW = Math.max(ctx.width - MARGIN.left - MARGIN.right, 10);
  const plotH = Math.max(ctx.height - MARGIN.top - MARGIN.bottom, 10);

  const plot = svgEl("g", { transform: `translate(${MARGIN.left},${MARGIN.top})` }, []);
  root.appendChild(plot);

  const indexMap = _buildIndexMap(nodes);
  const radii = _nodeRadius(nodes, indexMap, null);

  let pos;
  if (isArc === true) {
    pos = _arcLayout(nodes, plotW, plotH, horizontal);
  } else if (isLayered === true) {
    pos = _layeredLayout(nodes, links, plotW, plotH, horizontal, indexMap);
  } else {
    pos = _forceLayout(nodes, links, plotW, plotH, indexMap);
  }

  /* Replace any undefined positions with a fallback. */
  for (let i = 0; i < nodes.length; i = i + 1) {
    if (pos[i] === undefined || pos[i] === null) {
      pos[i] = { x: plotW / 2, y: plotH / 2 };
    }
  }

  /* Draw edges, then nodes (nodes on top). */
  if (isArc === true) {
    _drawArcLinks(plot, links, pos, indexMap, ctx, horizontal);
  } else {
    _drawLinks(plot, links, pos, radii, indexMap, ctx, drawArrows);
  }
  _drawNodes(plot, nodes, pos, radii, ctx);

  return root;
}


registerRenderer("network", render);
registerRenderer("arc-diagram", render);
registerRenderer("node-link", render);
registerRenderer("edge-bundling", render);
registerRenderer("dependency-graph", render);
