/*
 * network.js
 *
 * Network / node-link renderer.
 *
 * Registers: "network", "arc-diagram", "node-link", "edge-bundling",
 *            "dependency-graph"
 *
 * ctx.raw shape:
 *   nodes: [{ id, label?, group?, value?, order?, x?, y?, status? }]
 *   links: [{ source, target, value?, label? }]
 *   criticalPath?: [nodeId, ...]   (dependency-graph) an ordered path
 *
 * Layout (the `layout` attribute, else raw.layout, else the type's default):
 *   "force"   -- Fruchterman-Reingold spring-repulsion simulation. Default of
 *                "network" and "node-link" (node-link is an alias of
 *                network: same layout and drawing).
 *   "arc"     -- nodes on one axis (in `nodes[].order`, else data order),
 *                links as half-ellipse arcs scaled to the available height.
 *                Default of "arc-diagram"; horizontal unless the page asks
 *                for orientation="vertical".
 *   "layered" -- longest-path layered (Sugiyama-style) layout with
 *                barycentre ordering and arrowheads. Default of
 *                "dependency-graph" (left-to-right unless orientation says
 *                otherwise). Cycles are detected with a DFS: back-edges and
 *                self-links are left out of the ranking and drawn dashed.
 *   "bundled" -- nodes on a ring grouped by `group`, links as Bezier curves
 *                routed through their groups' control points (hierarchical
 *                edge bundling). Default of "edge-bundling"; the `tension`
 *                attribute (or raw.tension, 0..1, default 0.85) sets the
 *                bundling strength (0 = straight chords).
 *   "static"  -- fixed `nodes[].x` / `nodes[].y` coordinates, fitted to the
 *                plot (also selected by mode="static").
 *
 * Node colour encodes `group` (one palette slot per distinct group, listed
 * in the legend); node radius encodes `value` (sqrt scale). The accessible
 * table lists every node with its group, value and links.
 *
 * dependency-graph draws each node as a labelled box (name, and `status`
 * when given: todo, in-progress, done, blocked or any text) whose border
 * shows the status (else the group), and grows to fit its columns
 * (ctx.setContentHeight). Nodes in `criticalPath`, and every link that
 * joins two consecutive entries of it, are highlighted (option
 * show-critical-path="false" turns that off). Every cycle is reported once
 * per data object with mj-chart-cycle-detect, and its nodes say so in
 * their accessible name.
 *
 * Events:
 *   mj-chart-node-click    { id, label, group, index }
 *   mj-chart-edge-click    { source, target, value, label }
 *   mj-chart-cycle-detect  { cycles: [[nodeId, ...]] }  (dependency-graph)
 *
 * Force positions are cached per data object (and plot aspect), so a resize
 * rescales the finished layout instead of re-running the simulation.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { sqrtScale, linearScale } from "../scales.js";
import { booleanOption } from "../chartoptions.js";


const MARGIN = { top: 12, right: 12, bottom: 12, left: 12 };
const MIN_RADIUS = 4;
const MAX_RADIUS = 16;
const LABEL_FONT = 10;
const LABEL_CHAR_W = 5.6;
const LABEL_SPACE = 14;
const ARROW_SIZE = 7;
const MAX_LABELLED_NODES = 60;
const DEFAULT_TENSION = 0.85;

/* Force simulation budget: about this many pair interactions per render. */
const FORCE_PAIR_BUDGET = 4000000;
const FORCE_MAX_ITERATIONS = 300;
const FORCE_MIN_ITERATIONS = 20;

/* Re-run the cached force layout when log2(plot aspect) moves this far. */
const ASPECT_TOLERANCE = 1.5;

/* nodes array -> { links, entries: Map(key -> normalized positions) } */
const _LAYOUT_CACHE = new WeakMap();

const _DEFAULT_LAYOUT = {
  "network": "force",
  "node-link": "force",
  "arc-diagram": "arc",
  "edge-bundling": "bundled",
  "dependency-graph": "layered"
};

const _KNOWN_LAYOUTS = ["force", "arc", "layered", "bundled", "static"];

/* dependency-graph boxes. */
const BOX_MAX_W = 160;
const BOX_MIN_W = 64;
const BOX_H = 40;
const BOX_H_PLAIN = 30;
const BOX_GAP = 14;

/* Status -> semantic colour of a dependency-graph box (a status, not a series). */
const STATUS_COLORS = {
  "todo":        "var(--mj-text-muted, #6b7280)",
  "planned":     "var(--mj-text-muted, #6b7280)",
  "in-progress": "var(--mj-accent, #2563eb)",
  "done":        "var(--mj-color-success, #15803d)",
  "completed":   "var(--mj-color-success, #15803d)",
  "blocked":     "var(--mj-color-danger, #b91c1c)"
};

const CRITICAL_COLOR = "var(--mj-color-warning, #b45309)";
const CYCLE_COLOR = "var(--mj-color-danger, #b91c1c)";

/* data object -> true once its cycles were reported (one event per data). */
const _CYCLES_REPORTED = new WeakMap();


/* ---------- data ---------- */

function _finiteNumber(value) {
  /*
   * True when value is a finite number.
   */
  const finite = typeof value === "number" && Number.isFinite(value) === true;
  return finite;
}


function _readGraph(raw) {
  /*
   * Normalize raw.nodes / raw.links into index-based records. Nodes without
   * an id are skipped, a repeated id keeps its first node, and links whose
   * ends are unknown are skipped. Nothing is written into the data.
   *
   * :returns: { nodes, links, groups } -- nodes [{ id, label, group, value,
   *     order, x, y, source }], links [{ s, t, value, label, source }] and
   *     the distinct groups in first-appearance order.
   */
  const rawNodes = (raw && Array.isArray(raw.nodes)) ? raw.nodes : [];
  const rawLinks = (raw && Array.isArray(raw.links)) ? raw.links : [];

  const nodes = [];
  const indexOf = new Map();
  const groups = [];
  for (let i = 0; i < rawNodes.length; i = i + 1) {
    const entry = rawNodes[i];
    if (entry === null || typeof entry !== "object") {
      continue;
    }
    if (entry.id === null || entry.id === undefined) {
      continue;
    }
    const id = String(entry.id);
    if (indexOf.has(id) === true) {
      continue;
    }
    const hasLabel = entry.label !== null && entry.label !== undefined;
    const hasGroup = entry.group !== null && entry.group !== undefined && String(entry.group) !== "";
    const group = hasGroup === true ? String(entry.group) : null;
    if (group !== null && groups.indexOf(group) < 0) {
      groups.push(group);
    }
    indexOf.set(id, nodes.length);
    nodes.push({
      id: id,
      label: hasLabel === true ? String(entry.label) : id,
      group: group,
      value: _finiteNumber(entry.value) === true ? entry.value : (_finiteNumber(entry.size) === true ? entry.size : null),
      order: _finiteNumber(entry.order) === true ? entry.order : null,
      x: _finiteNumber(entry.x) === true ? entry.x : null,
      y: _finiteNumber(entry.y) === true ? entry.y : null,
      status: entry.status !== null && entry.status !== undefined && String(entry.status) !== ""
        ? String(entry.status) : null,
      index: i,
      source: entry
    });
  }

  const links = [];
  for (let k = 0; k < rawLinks.length; k = k + 1) {
    const entry = rawLinks[k];
    if (entry === null || typeof entry !== "object") {
      continue;
    }
    const s = indexOf.get(String(entry.source));
    const t = indexOf.get(String(entry.target));
    if (s === undefined || t === undefined) {
      continue;
    }
    const value = _finiteNumber(entry.value) === true && entry.value >= 0 ? entry.value : 1;
    const hasLabel = entry.label !== null && entry.label !== undefined && String(entry.label) !== "";
    links.push({
      s: s,
      t: t,
      value: value,
      label: hasLabel === true ? String(entry.label) : null,
      source: entry
    });
  }

  return { nodes: nodes, links: links, groups: groups };
}


function _nodeRadii(nodes, maxRadius) {
  /*
   * Radius per node: a sqrt scale on node.value (area ~ value); nodes
   * without a value get the mid radius.
   */
  const top = Math.max(maxRadius, 2);
  const bottom = Math.min(MIN_RADIUS, top);
  let maxVal = 0;
  let hasValue = false;
  for (let i = 0; i < nodes.length; i = i + 1) {
    if (nodes[i].value !== null && nodes[i].value > maxVal) {
      maxVal = nodes[i].value;
      hasValue = true;
    }
  }
  const scale = sqrtScale([0, hasValue === true ? maxVal : 1], [bottom, top]);
  const radii = [];
  for (let i = 0; i < nodes.length; i = i + 1) {
    let r = (bottom + top) / 2;
    if (hasValue === true) {
      r = nodes[i].value !== null ? scale(nodes[i].value) : bottom;
    }
    radii.push(_finiteNumber(r) === true ? Math.max(r, 2) : bottom);
  }
  return radii;
}


function _labelWidth(text) {
  /*
   * Estimated pixel width of a node label.
   */
  const width = String(text).length * LABEL_CHAR_W;
  return width;
}


function _explicitOrientation(ctx) {
  /*
   * The orientation the page asked for (host attribute, else
   * meta.orientation), or null when it named none.
   */
  let value = ctx.attrs("orientation", null);
  if (value !== "horizontal" && value !== "vertical") {
    const meta = ctx.model && ctx.model.meta ? ctx.model.meta : {};
    value = meta.orientation === "horizontal" || meta.orientation === "vertical" ? meta.orientation : null;
  }
  return value;
}


function _resolveLayout(ctx, raw) {
  /*
   * The layout to draw: the `layout` attribute, else raw.layout, else
   * mode="static", else the type's default.
   */
  const type = typeof ctx.type === "string" ? ctx.type : "network";
  const fallback = _DEFAULT_LAYOUT[type] !== undefined ? _DEFAULT_LAYOUT[type] : "force";
  let layout = ctx.attrs("layout", null);
  if (_KNOWN_LAYOUTS.indexOf(layout) < 0 && raw && typeof raw.layout === "string") {
    layout = raw.layout;
  }
  if (layout === "bundle" || layout === "bundling" || layout === "radial") {
    layout = "bundled";
  }
  if (_KNOWN_LAYOUTS.indexOf(layout) < 0 && ctx.attrs("mode", null) === "static") {
    layout = "static";
  }
  if (_KNOWN_LAYOUTS.indexOf(layout) < 0) {
    layout = fallback;
  }
  return layout;
}


/* ---------- geometry helpers ---------- */

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


function _selfLoopPath(x, y, r) {
  /*
   * A small loop on the upper right of a node, for a self-link.
   */
  const sx = x + r * 0.5;
  const sy = y - r * 0.87;
  const ex = x + r * 0.87;
  const ey = y - r * 0.5;
  const reach = r + 14;
  const path = `M${sx.toFixed(2)},${sy.toFixed(2)} ` +
    `C${(sx + 4).toFixed(2)},${(y - reach).toFixed(2)} ` +
    `${(x + reach).toFixed(2)},${(ey - 4).toFixed(2)} ` +
    `${ex.toFixed(2)},${ey.toFixed(2)}`;
  return path;
}


function _plotBox(plotW, plotH, maxRadius, labelled) {
  /*
   * The box node centres may occupy: inset by the node radius, plus the
   * label line under the bottom row.
   */
  const inset = maxRadius + 2;
  const bottom = inset + (labelled === true ? LABEL_SPACE : 0);
  const box = {
    x0: inset,
    y0: inset,
    x1: Math.max(plotW - inset, inset + 1),
    y1: Math.max(plotH - bottom, inset + 1)
  };
  return box;
}


function _normalize(pos) {
  /*
   * Map positions into [0, 1] x [0, 1] by their bounding box (0.5 on an
   * axis with no extent).
   */
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (let i = 0; i < pos.length; i = i + 1) {
    minX = Math.min(minX, pos[i].x);
    maxX = Math.max(maxX, pos[i].x);
    minY = Math.min(minY, pos[i].y);
    maxY = Math.max(maxY, pos[i].y);
  }
  const spanX = maxX - minX;
  const spanY = maxY - minY;
  const out = [];
  for (let i = 0; i < pos.length; i = i + 1) {
    out.push({
      x: spanX > 1e-9 ? (pos[i].x - minX) / spanX : 0.5,
      y: spanY > 1e-9 ? (pos[i].y - minY) / spanY : 0.5
    });
  }
  return out;
}


function _toBox(normalized, box) {
  /*
   * Map normalized positions into a pixel box.
   */
  const out = [];
  for (let i = 0; i < normalized.length; i = i + 1) {
    out.push({
      x: box.x0 + normalized[i].x * (box.x1 - box.x0),
      y: box.y0 + normalized[i].y * (box.y1 - box.y0)
    });
  }
  return out;
}


function _separate(pos, radii, box, passes) {
  /*
   * Push overlapping nodes apart (a few relaxation passes), keeping them
   * inside the box.
   */
  const n = pos.length;
  for (let pass = 0; pass < passes; pass = pass + 1) {
    let moved = false;
    for (let i = 0; i < n; i = i + 1) {
      for (let j = i + 1; j < n; j = j + 1) {
        let dx = pos[j].x - pos[i].x;
        let dy = pos[j].y - pos[i].y;
        let dist = Math.sqrt(dx * dx + dy * dy);
        const need = radii[i] + radii[j] + 3;
        if (dist >= need) {
          continue;
        }
        if (dist < 1e-6) {
          /* Coincident: a deterministic direction from the pair. */
          const angle = ((i * 7919 + j * 104729) % 360) * Math.PI / 180;
          dx = Math.cos(angle);
          dy = Math.sin(angle);
          dist = 1;
        }
        const push = (need - Math.min(dist, need)) / 2;
        const ux = dx / dist;
        const uy = dy / dist;
        pos[i].x = pos[i].x - ux * push;
        pos[i].y = pos[i].y - uy * push;
        pos[j].x = pos[j].x + ux * push;
        pos[j].y = pos[j].y + uy * push;
        moved = true;
      }
    }
    for (let i = 0; i < n; i = i + 1) {
      pos[i].x = Math.min(Math.max(pos[i].x, box.x0), box.x1);
      pos[i].y = Math.min(Math.max(pos[i].y, box.y0), box.y1);
    }
    if (moved === false) {
      break;
    }
  }
  return pos;
}


/* ---------- force-directed layout ---------- */

function _forceLayout(graph, boxWidth, boxHeight) {
  /*
   * Fruchterman-Reingold layout: repulsion k^2/d between every pair,
   * attraction d^2/k along links, an elliptical pull to the centre whose
   * x / y strengths make the settled graph fill the simulation box (no
   * clamping at the box edge, which piles nodes on the border), and moves
   * capped by a cooling temperature. Distances are floored and every step
   * is checked for finite values, so the result is always finite. The start
   * is a deterministic sunflower spiral.
   *
   * The simulation box has the plot's area but only the square root of its
   * aspect ratio; the caller stretches the result to the plot. Laying out
   * at the full (often 4:1) aspect squeezes chains onto one line.
   *
   * :param boxWidth: Width of the plot box the result is fitted to.
   * :param boxHeight: Height of that box.
   * :returns: An array of {x, y} in the same order as graph.nodes.
   */
  const area = Math.max(boxWidth * boxHeight, 1);
  const width = Math.sqrt(area * Math.sqrt(Math.max(boxWidth, 1) / Math.max(boxHeight, 1)));
  const height = area / width;
  const n = graph.nodes.length;
  const cx = width / 2;
  const cy = height / 2;
  const pos = [];
  for (let i = 0; i < n; i = i + 1) {
    const radius = Math.sqrt((i + 0.5) / n);
    const angle = i * 2.399963229728653;
    pos.push({
      x: cx + radius * Math.cos(angle) * width * 0.45,
      y: cy + radius * Math.sin(angle) * height * 0.45
    });
  }
  if (n < 2) {
    return pos;
  }

  /* Unique undirected edges, self-links left out. */
  const seen = new Set();
  const edges = [];
  for (let k = 0; k < graph.links.length; k = k + 1) {
    const a = Math.min(graph.links[k].s, graph.links[k].t);
    const b = Math.max(graph.links[k].s, graph.links[k].t);
    if (a === b || seen.has(a * n + b) === true) {
      continue;
    }
    seen.add(a * n + b);
    edges.push([a, b]);
  }

  const k = Math.max(Math.sqrt((width * height) / n) * 0.6, 4);
  const minDist = k * 0.01 + 0.01;
  /* Equilibrium radius of n nodes under gravity G is k * sqrt(n / G). */
  const gravityX = Math.min((1.44 * height) / Math.max(width, 1), 50);
  const gravityY = Math.min((1.44 * width) / Math.max(height, 1), 50);
  const limit = Math.max(width, height) * 4;
  const iterations = Math.max(FORCE_MIN_ITERATIONS,
    Math.min(FORCE_MAX_ITERATIONS, Math.floor(FORCE_PAIR_BUDGET / (n * n))));
  const startTemperature = Math.max(width, height) / 8;

  const dispX = new Float64Array(n);
  const dispY = new Float64Array(n);

  for (let iter = 0; iter < iterations; iter = iter + 1) {
    dispX.fill(0);
    dispY.fill(0);

    for (let i = 0; i < n; i = i + 1) {
      for (let j = i + 1; j < n; j = j + 1) {
        let dx = pos[i].x - pos[j].x;
        let dy = pos[i].y - pos[j].y;
        let dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < minDist) {
          const angle = ((i * 7919 + j * 104729 + iter * 31) % 360) * Math.PI / 180;
          dx = Math.cos(angle) * minDist;
          dy = Math.sin(angle) * minDist;
          dist = minDist;
        }
        const force = (k * k) / dist;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        dispX[i] = dispX[i] + fx;
        dispY[i] = dispY[i] + fy;
        dispX[j] = dispX[j] - fx;
        dispY[j] = dispY[j] - fy;
      }
    }

    for (let e = 0; e < edges.length; e = e + 1) {
      const a = edges[e][0];
      const b = edges[e][1];
      const dx = pos[a].x - pos[b].x;
      const dy = pos[a].y - pos[b].y;
      const dist = Math.max(Math.sqrt(dx * dx + dy * dy), minDist);
      const force = (dist * dist) / k;
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;
      dispX[a] = dispX[a] - fx;
      dispY[a] = dispY[a] - fy;
      dispX[b] = dispX[b] + fx;
      dispY[b] = dispY[b] + fy;
    }

    const temperature = startTemperature * (1 - iter / iterations) + 0.5;
    for (let i = 0; i < n; i = i + 1) {
      dispX[i] = dispX[i] + (cx - pos[i].x) * gravityX;
      dispY[i] = dispY[i] + (cy - pos[i].y) * gravityY;
      const length = Math.sqrt(dispX[i] * dispX[i] + dispY[i] * dispY[i]);
      if (Number.isFinite(length) === false || length < 1e-9) {
        continue;
      }
      const step = Math.min(length, temperature);
      const nx = pos[i].x + (dispX[i] / length) * step;
      const ny = pos[i].y + (dispY[i] / length) * step;
      if (Number.isFinite(nx) === true && Number.isFinite(ny) === true) {
        pos[i].x = Math.min(Math.max(nx, cx - limit), cx + limit);
        pos[i].y = Math.min(Math.max(ny, cy - limit), cy + limit);
      }
    }
  }
  return pos;
}


function _cachedForce(graph, raw, box) {
  /*
   * Force layout normalized to [0, 1], cached per data object and node /
   * link count, so a resize only rescales it. The layout is recomputed only
   * when the plot's aspect ratio changes by more than ASPECT_TOLERANCE
   * (a factor of about 2.8), where stretching would distort it.
   */
  const width = box.x1 - box.x0;
  const height = box.y1 - box.y0;
  const aspect = Math.log2(Math.max(width, 1) / Math.max(height, 1));
  const key = `force|${graph.nodes.length}|${graph.links.length}`;

  let holder = null;
  const cacheKey = raw && Array.isArray(raw.nodes) ? raw.nodes : null;
  if (cacheKey !== null) {
    holder = _LAYOUT_CACHE.get(cacheKey);
    if (holder === undefined || holder.links !== raw.links) {
      holder = { links: raw.links, entries: new Map() };
      _LAYOUT_CACHE.set(cacheKey, holder);
    }
    const cached = holder.entries.get(key);
    if (cached !== undefined && Math.abs(cached.aspect - aspect) <= ASPECT_TOLERANCE) {
      return cached.normalized;
    }
  }

  const normalized = _normalize(_forceLayout(graph, width, height));
  if (holder !== null) {
    holder.entries.set(key, { aspect: aspect, normalized: normalized });
  }
  return normalized;
}


/* ---------- static layout ---------- */

function _staticLayout(graph) {
  /*
   * Normalized positions from nodes[].x / nodes[].y; nodes without both
   * coordinates go to the centre.
   */
  const pos = [];
  for (let i = 0; i < graph.nodes.length; i = i + 1) {
    const node = graph.nodes[i];
    pos.push({ x: node.x !== null ? node.x : 0, y: node.y !== null ? node.y : 0 });
  }
  return _normalize(pos);
}


/* ---------- layered layout ---------- */

function _findBackEdges(n, links) {
  /*
   * Iterative DFS over the links: an edge into a node that is still on the
   * DFS stack closes a cycle (a back-edge); a self-link is one too.
   *
   * :returns: A Set of link indexes to leave out of the ranking, with a
   *     `cycles` property: one array of node indexes per back-edge, in path
   *     order (the cycle that edge closes).
   */
  const out = [];
  for (let i = 0; i < n; i = i + 1) {
    out.push([]);
  }
  const back = new Set();
  const cycles = [];
  for (let k = 0; k < links.length; k = k + 1) {
    if (links[k].s === links[k].t) {
      back.add(k);
      cycles.push([links[k].s]);
    } else {
      out[links[k].s].push(k);
    }
  }

  /* 0 = unvisited, 1 = on the stack, 2 = finished */
  const state = new Uint8Array(n);
  for (let startNode = 0; startNode < n; startNode = startNode + 1) {
    if (state[startNode] !== 0) {
      continue;
    }
    const stack = [{ node: startNode, next: 0 }];
    state[startNode] = 1;
    while (stack.length > 0) {
      const frame = stack[stack.length - 1];
      const edgesOut = out[frame.node];
      if (frame.next >= edgesOut.length) {
        state[frame.node] = 2;
        stack.pop();
        continue;
      }
      const linkIndex = edgesOut[frame.next];
      frame.next = frame.next + 1;
      const target = links[linkIndex].t;
      if (state[target] === 1) {
        back.add(linkIndex);
        const from = stack.findIndex((entry) => entry.node === target);
        cycles.push(stack.slice(from).map((entry) => entry.node));
      } else if (state[target] === 0) {
        state[target] = 1;
        stack.push({ node: target, next: 0 });
      }
    }
  }
  back.cycles = cycles;
  return back;
}


function _layeredLayout(graph, box, horizontal) {
  /*
   * Longest-path ranks over the acyclic part of the graph (back-edges
   * removed first, so ranking always terminates), barycentre ordering
   * within ranks, then even spacing along both axes.
   *
   * :returns: { pos, backEdges }.
   */
  const n = graph.nodes.length;
  const links = graph.links;
  const backEdges = _findBackEdges(n, links);

  const succ = [];
  const pred = [];
  const inDegree = new Array(n).fill(0);
  for (let i = 0; i < n; i = i + 1) {
    succ.push([]);
    pred.push([]);
  }
  for (let k = 0; k < links.length; k = k + 1) {
    if (backEdges.has(k) === true) {
      continue;
    }
    succ[links[k].s].push(links[k].t);
    pred[links[k].t].push(links[k].s);
    inDegree[links[k].t] = inDegree[links[k].t] + 1;
  }

  /* Kahn's algorithm: each node is dequeued exactly once. */
  const rank = new Array(n).fill(0);
  const queue = [];
  for (let i = 0; i < n; i = i + 1) {
    if (inDegree[i] === 0) {
      queue.push(i);
    }
  }
  let head = 0;
  while (head < queue.length) {
    const current = queue[head];
    head = head + 1;
    for (let s = 0; s < succ[current].length; s = s + 1) {
      const next = succ[current][s];
      rank[next] = Math.max(rank[next], rank[current] + 1);
      inDegree[next] = inDegree[next] - 1;
      if (inDegree[next] === 0) {
        queue.push(next);
      }
    }
  }

  let maxRank = 0;
  for (let i = 0; i < n; i = i + 1) {
    maxRank = Math.max(maxRank, rank[i]);
  }
  const columns = [];
  for (let r = 0; r <= maxRank; r = r + 1) {
    columns.push([]);
  }
  for (let i = 0; i < n; i = i + 1) {
    columns[rank[i]].push(i);
  }

  /* Barycentre ordering: two down / up sweeps. */
  const orderIndex = new Array(n).fill(0);
  const refreshOrder = () => {
    for (let r = 0; r < columns.length; r = r + 1) {
      for (let c = 0; c < columns[r].length; c = c + 1) {
        orderIndex[columns[r][c]] = c;
      }
    }
  };
  const sortColumn = (column, neighbours) => {
    const keyed = column.map((node, position) => {
      const list = neighbours[node];
      let key = position;
      if (list.length > 0) {
        let sum = 0;
        for (let q = 0; q < list.length; q = q + 1) {
          sum = sum + orderIndex[list[q]];
        }
        key = sum / list.length;
      }
      return { node: node, key: key, position: position };
    });
    keyed.sort((a, b) => (a.key - b.key) || (a.position - b.position));
    return keyed.map((entry) => entry.node);
  };
  refreshOrder();
  for (let sweep = 0; sweep < 2; sweep = sweep + 1) {
    for (let r = 1; r < columns.length; r = r + 1) {
      columns[r] = sortColumn(columns[r], pred);
      refreshOrder();
    }
    for (let r = columns.length - 2; r >= 0; r = r - 1) {
      columns[r] = sortColumn(columns[r], succ);
      refreshOrder();
    }
  }

  const rankStart = horizontal === true ? box.x0 : box.y0;
  const rankEnd = horizontal === true ? box.x1 : box.y1;
  const crossStart = horizontal === true ? box.y0 : box.x0;
  const crossEnd = horizontal === true ? box.y1 : box.x1;
  const crossMid = (crossStart + crossEnd) / 2;
  const maxCrossGap = horizontal === true ? 70 : 140;

  let widest = 0;
  for (let r = 0; r < columns.length; r = r + 1) {
    widest = Math.max(widest, columns[r].length);
  }

  const pos = new Array(n);
  for (let r = 0; r < columns.length; r = r + 1) {
    const column = columns[r];
    const rankPos = columns.length > 1
      ? rankStart + (r / (columns.length - 1)) * (rankEnd - rankStart)
      : (rankStart + rankEnd) / 2;
    const gap = column.length > 1
      ? Math.min((crossEnd - crossStart) / (column.length - 1), maxCrossGap)
      : 0;
    const first = crossMid - (gap * (column.length - 1)) / 2;
    for (let c = 0; c < column.length; c = c + 1) {
      const crossPos = first + c * gap;
      pos[column[c]] = horizontal === true ? { x: rankPos, y: crossPos } : { x: crossPos, y: rankPos };
    }
  }
  return { pos: pos, backEdges: backEdges, rankCount: columns.length, widest: widest };
}


/* ---------- arc layout ---------- */

function _arcLayout(graph, plotW, plotH, horizontal) {
  /*
   * Nodes evenly along one axis (by nodes[].order, else data order). Node
   * radii are capped to half the spacing and the label band is sized to
   * the labels (rotated when they do not fit side by side).
   *
   * :returns: { pos, radiusCap, axis, rotateLabels, arcRoom }.
   */
  const n = graph.nodes.length;
  const order = graph.nodes.map((node, index) => index);
  order.sort((a, b) => {
    const oa = graph.nodes[a].order !== null ? graph.nodes[a].order : a;
    const ob = graph.nodes[b].order !== null ? graph.nodes[b].order : b;
    return (oa - ob) || (a - b);
  });

  let maxLabel = 0;
  for (let i = 0; i < n; i = i + 1) {
    maxLabel = Math.max(maxLabel, _labelWidth(graph.nodes[i].label));
  }

  const pos = new Array(n);
  let radiusCap = MAX_RADIUS;
  let rotateLabels = false;
  let axis = 0;
  let arcRoom = 0;

  if (horizontal === true) {
    const pad = Math.min(Math.max(maxLabel / 2, MAX_RADIUS), plotW / 4);
    const spacing = n > 1 ? (plotW - pad * 2) / (n - 1) : plotW;
    radiusCap = Math.max(Math.min(MAX_RADIUS, spacing * 0.4), 2);
    rotateLabels = maxLabel + 4 > spacing;
    const labelBand = rotateLabels === true
      ? Math.min(maxLabel * 0.72 + 8, plotH * 0.4)
      : LABEL_SPACE + 2;
    axis = plotH - labelBand - radiusCap;
    arcRoom = Math.max(axis - radiusCap - 4, 8);
    for (let p = 0; p < order.length; p = p + 1) {
      const x = n > 1 ? pad + p * spacing : plotW / 2;
      pos[order[p]] = { x: x, y: axis };
    }
  } else {
    const pad = MAX_RADIUS + 4;
    const spacing = n > 1 ? (plotH - pad * 2) / (n - 1) : plotH;
    radiusCap = Math.max(Math.min(MAX_RADIUS, spacing * 0.4), 2);
    const labelBand = Math.min(maxLabel + 8, plotW * 0.35);
    axis = labelBand + radiusCap;
    arcRoom = Math.max(plotW - axis - radiusCap - 4, 8);
    for (let p = 0; p < order.length; p = p + 1) {
      const y = n > 1 ? pad + p * spacing : plotH / 2;
      pos[order[p]] = { x: axis, y: y };
    }
  }
  return { pos: pos, radiusCap: radiusCap, axis: axis, rotateLabels: rotateLabels, arcRoom: arcRoom };
}


/* ---------- bundled (radial) layout ---------- */

function _radialLayout(graph, plotW, plotH) {
  /*
   * Nodes on a ring, grouped by `group` with an empty slot between groups.
   * Each group gets a control point at its circular-mean angle, half-way to
   * the centre; edges are bundled through those points.
   *
   * :returns: { pos, angles, radius, cx, cy, groupPoint: Map(group -> {x, y}) }.
   */
  const n = graph.nodes.length;
  const groupKeys = graph.groups.slice();
  const members = new Map();
  for (let g = 0; g < groupKeys.length; g = g + 1) {
    members.set(groupKeys[g], []);
  }
  const ungrouped = [];
  for (let i = 0; i < n; i = i + 1) {
    const group = graph.nodes[i].group;
    if (group === null) {
      ungrouped.push(i);
    } else {
      members.get(group).push(i);
    }
  }
  const blocks = groupKeys.map((key) => members.get(key));
  if (ungrouped.length > 0) {
    blocks.push(ungrouped);
  }

  const gapSlots = blocks.length > 1 ? blocks.length : 0;
  const totalSlots = Math.max(n + gapSlots, 1);

  let maxLabel = 0;
  for (let i = 0; i < n; i = i + 1) {
    maxLabel = Math.max(maxLabel, _labelWidth(graph.nodes[i].label));
  }
  const cx = plotW / 2;
  const cy = plotH / 2;
  const radius = Math.max(Math.min(plotW / 2 - maxLabel - 12, plotH / 2 - LABEL_SPACE - 4), 12);

  const pos = new Array(n);
  const angles = new Array(n);
  const groupPoint = new Map();
  let slot = 0;
  for (let b = 0; b < blocks.length; b = b + 1) {
    let sumSin = 0;
    let sumCos = 0;
    for (let m = 0; m < blocks[b].length; m = m + 1) {
      const node = blocks[b][m];
      const angle = (slot / totalSlots) * Math.PI * 2;
      angles[node] = angle;
      pos[node] = { x: cx + radius * Math.sin(angle), y: cy - radius * Math.cos(angle) };
      sumSin = sumSin + Math.sin(angle);
      sumCos = sumCos + Math.cos(angle);
      slot = slot + 1;
    }
    if (gapSlots > 0) {
      slot = slot + 1;
    }
    const meanAngle = Math.atan2(sumSin, sumCos);
    const pull = blocks.length > 1 ? 0.45 : 0;
    const key = b < groupKeys.length ? groupKeys[b] : null;
    groupPoint.set(key, {
      x: cx + radius * pull * Math.sin(meanAngle),
      y: cy - radius * pull * Math.cos(meanAngle)
    });
  }
  return { pos: pos, angles: angles, radius: radius, cx: cx, cy: cy, groupPoint: groupPoint, slots: totalSlots };
}


/* ---------- drawing ---------- */

function _nodeColor(ctx, graph, index) {
  /*
   * Fill of a node: its group's colour; a single palette colour when no
   * node has a group; the muted text colour for an ungrouped node in a
   * grouped graph (so it never shares a slot with a group).
   */
  const group = graph.nodes[index].group;
  let color = ctx.colorFor(0);
  if (graph.groups.length > 0) {
    color = group !== null ? ctx.colorFor(group) : "var(--mj-text-muted, #6b7280)";
  }
  return color;
}

function _edgeStrokeScale(links) {
  /*
   * Stroke width scale on link value (1-4px).
   */
  let maxLinkVal = 0;
  for (let k = 0; k < links.length; k = k + 1) {
    maxLinkVal = Math.max(maxLinkVal, links[k].value);
  }
  const scale = linearScale([0, maxLinkVal > 0 ? maxLinkVal : 1], [1, 4]);
  return scale;
}


function _edgeTitle(graph, link) {
  /*
   * Tooltip text of a link.
   */
  const source = graph.nodes[link.s].label;
  const target = graph.nodes[link.t].label;
  let text = `${source} → ${target}: ${formatNumber(link.value)}`;
  if (link.label !== null) {
    text = `${text} (${link.label})`;
  }
  return text;
}


function _wireEdge(element, graph, link, ctx) {
  /*
   * Click handler of an edge: mj-chart-edge-click with the data ids.
   */
  element.addEventListener("click", () => {
    ctx.emit("mj-chart-edge-click", {
      source: graph.nodes[link.s].id,
      target: graph.nodes[link.t].id,
      value: link.value,
      label: link.label
    });
  });
}


function _curveClearance(pos, radii, s, t, bow, boxStyle) {
  /*
   * Smallest gap between the edge s -> t (a quadratic curve whose control
   * point is offset `bow` px from the midpoint; 0 = straight) and the rim
   * of any other node, sampled at nine points along the curve. With
   * boxStyle the nodes are boxes of boxStyle.halfW x boxStyle.halfH.
   */
  const sx = pos[s].x;
  const sy = pos[s].y;
  const tx = pos[t].x;
  const ty = pos[t].y;
  const dist = Math.max(Math.sqrt((tx - sx) * (tx - sx) + (ty - sy) * (ty - sy)), 1e-6);
  const mx = (sx + tx) / 2 + (-(ty - sy) / dist) * bow;
  const my = (sy + ty) / 2 + ((tx - sx) / dist) * bow;
  let clearance = Infinity;
  for (let step = 1; step < 10; step = step + 1) {
    const u = step / 10;
    const px = (1 - u) * (1 - u) * sx + 2 * (1 - u) * u * mx + u * u * tx;
    const py = (1 - u) * (1 - u) * sy + 2 * (1 - u) * u * my + u * u * ty;
    for (let i = 0; i < pos.length; i = i + 1) {
      if (i === s || i === t) {
        continue;
      }
      let gap = Math.sqrt((pos[i].x - px) * (pos[i].x - px) + (pos[i].y - py) * (pos[i].y - py)) - radii[i];
      if (boxStyle !== null && boxStyle !== undefined) {
        gap = Math.max(Math.abs(pos[i].x - px) - boxStyle.halfW, Math.abs(pos[i].y - py) - boxStyle.halfH);
      }
      clearance = Math.min(clearance, gap);
    }
  }
  return clearance;
}


function _drawStraightLinks(layer, graph, pos, radii, ctx, drawArrows, backEdges, boxStyle) {
  /*
   * Straight edges (curved for back-edges and, in the layered layout, for
   * edges that would cross another node; loops for self-links), with
   * arrowheads at the target boundary for directed layouts.
   *
   * boxStyle (dependency-graph boxes, else null): { reach(i, angle) -> the
   * distance from a node's centre to its boundary, critical: Set of
   * critical link indexes }.
   */
  const strokeScale = _edgeStrokeScale(graph.links);
  const reach = (index, angle) => {
    const distance = boxStyle !== null ? boxStyle.reach(index, angle) : radii[index];
    return distance;
  };
  for (let k = 0; k < graph.links.length; k = k + 1) {
    const link = graph.links[k];
    const isBack = backEdges !== null && backEdges.has(k) === true;
    const isCritical = boxStyle !== null && boxStyle.critical.has(k) === true;
    let strokeW = boxStyle !== null ? 1.5 : strokeScale(link.value);
    let stroke = "var(--mj-text-muted, #6b7280)";
    if (isCritical === true) {
      stroke = CRITICAL_COLOR;
      strokeW = 2.5;
    } else if (isBack === true && boxStyle !== null) {
      stroke = CYCLE_COLOR;
    }
    const edge = svgEl("g", {
      part: isCritical === true ? "edge critical-path-edge" : "edge",
      "data-cycle-edge": isBack === true ? "true" : null
    }, []);

    if (link.s === link.t) {
      const p = pos[link.s];
      edge.appendChild(svgEl("path", {
        d: _selfLoopPath(p.x, p.y, radii[link.s]),
        fill: "none",
        stroke: stroke,
        "stroke-width": strokeW.toFixed(2),
        "stroke-opacity": "0.7",
        "stroke-dasharray": "4 3"
      }, [svgEl("title", null, _edgeTitle(graph, link))]));
      if (boxStyle !== null) {
        /* A box has no round rim: the loop sits on its upper right corner. */
        edge.firstChild.setAttribute("d", _selfLoopPath(p.x + boxStyle.halfW - 10, p.y - boxStyle.halfH + 4, 8));
      }
      _wireEdge(edge, graph, link, ctx);
      layer.appendChild(edge);
      continue;
    }

    const sx = pos[link.s].x;
    const sy = pos[link.s].y;
    const tx = pos[link.t].x;
    const ty = pos[link.t].y;
    const dist = Math.sqrt((tx - sx) * (tx - sx) + (ty - sy) * (ty - sy));
    if (dist < 1e-6) {
      continue;
    }

    /*
     * Bow (signed offset of the curve's control point from the midpoint):
     * a back-edge always bows to one side so it does not hide the forward
     * edge it mirrors; in the layered layout a forward edge that would run
     * through another node bows to the side with more clearance.
     */
    let bow = 0;
    if (isBack === true) {
      bow = Math.min(dist * 0.35, 60);
    } else if (backEdges !== null && _curveClearance(pos, radii, link.s, link.t, 0, boxStyle) < 4) {
      let bestClear = -Infinity;
      const candidates = [0.18, -0.18, 0.32, -0.32];
      for (let c = 0; c < candidates.length; c = c + 1) {
        const offset = Math.sign(candidates[c]) * Math.min(dist * Math.abs(candidates[c]), 70);
        const clear = _curveClearance(pos, radii, link.s, link.t, offset, boxStyle);
        if (clear > bestClear) {
          bestClear = clear;
          bow = offset;
        }
        if (clear >= 4) {
          break;
        }
      }
    }

    let pathD = "";
    let endAngle = Math.atan2(ty - sy, tx - sx);
    let ex = tx - reach(link.t, endAngle) * Math.cos(endAngle);
    let ey = ty - reach(link.t, endAngle) * Math.sin(endAngle);

    if (bow !== 0) {
      const mx = (sx + tx) / 2 + (-(ty - sy) / dist) * bow;
      const my = (sy + ty) / 2 + ((tx - sx) / dist) * bow;
      endAngle = Math.atan2(ty - my, tx - mx);
      ex = tx - reach(link.t, endAngle) * Math.cos(endAngle);
      ey = ty - reach(link.t, endAngle) * Math.sin(endAngle);
      const startAngle = Math.atan2(my - sy, mx - sx);
      const bx = sx + reach(link.s, startAngle) * Math.cos(startAngle);
      const by = sy + reach(link.s, startAngle) * Math.sin(startAngle);
      pathD = `M${bx.toFixed(2)},${by.toFixed(2)} Q${mx.toFixed(2)},${my.toFixed(2)} ${ex.toFixed(2)},${ey.toFixed(2)}`;
    } else {
      const startX = sx + reach(link.s, endAngle) * Math.cos(endAngle);
      const startY = sy + reach(link.s, endAngle) * Math.sin(endAngle);
      pathD = `M${startX.toFixed(2)},${startY.toFixed(2)} L${ex.toFixed(2)},${ey.toFixed(2)}`;
    }

    edge.appendChild(svgEl("path", {
      d: pathD,
      fill: "none",
      stroke: stroke,
      "stroke-width": strokeW.toFixed(2),
      "stroke-opacity": isCritical === true ? "1" : "0.7",
      "stroke-dasharray": isBack === true ? "5 4" : null
    }, [svgEl("title", null, _edgeTitle(graph, link))]));

    if (drawArrows === true) {
      edge.appendChild(svgEl("polygon", {
        points: _arrowPts(ex, ey, endAngle),
        fill: stroke
      }, []));
    }
    _wireEdge(edge, graph, link, ctx);
    layer.appendChild(edge);
  }
}


function _drawArcLinks(layer, graph, pos, ctx, horizontal, arcRoom, radiusCap) {
  /*
   * Links as half-ellipse arcs above (horizontal) or right of (vertical)
   * the node axis. The widest arc uses the whole free height; narrower
   * arcs are scaled down with their span so all of them stay in the plot.
   */
  const strokeScale = _edgeStrokeScale(graph.links);
  let maxSpan = 0;
  for (let k = 0; k < graph.links.length; k = k + 1) {
    const link = graph.links[k];
    const span = horizontal === true
      ? Math.abs(pos[link.t].x - pos[link.s].x)
      : Math.abs(pos[link.t].y - pos[link.s].y);
    maxSpan = Math.max(maxSpan, span);
  }

  for (let k = 0; k < graph.links.length; k = k + 1) {
    const link = graph.links[k];
    const sx = pos[link.s].x;
    const sy = pos[link.s].y;
    const tx = pos[link.t].x;
    const ty = pos[link.t].y;
    const color = _nodeColor(ctx, graph, link.s);

    let pathD = "";
    if (link.s === link.t) {
      pathD = _selfLoopPath(sx, sy, radiusCap);
    } else {
      const span = horizontal === true ? Math.abs(tx - sx) : Math.abs(ty - sy);
      const along = span / 2;
      const height = maxSpan > 0 ? Math.min(along, arcRoom * (span / maxSpan)) : along;
      const across = Math.max(height, 2);
      if (horizontal === true) {
        const sweep = sx < tx ? 1 : 0;
        pathD = `M${sx.toFixed(2)},${sy.toFixed(2)} ` +
          `A${along.toFixed(2)},${across.toFixed(2)} 0 0 ${sweep} ${tx.toFixed(2)},${ty.toFixed(2)}`;
      } else {
        const sweep = sy < ty ? 1 : 0;
        pathD = `M${sx.toFixed(2)},${sy.toFixed(2)} ` +
          `A${across.toFixed(2)},${along.toFixed(2)} 0 0 ${sweep} ${tx.toFixed(2)},${ty.toFixed(2)}`;
      }
    }

    const arc = svgEl("path", {
      d: pathD,
      fill: "none",
      stroke: color,
      "stroke-width": strokeScale(link.value).toFixed(2),
      "stroke-opacity": "0.6",
      part: "arc-link"
    }, [svgEl("title", null, _edgeTitle(graph, link))]);
    _wireEdge(arc, graph, link, ctx);
    layer.appendChild(arc);
  }
}


function _drawBundledLinks(layer, graph, radial, ctx, tension) {
  /*
   * Hierarchical edge bundling: each link is a Bezier curve whose control
   * points are its groups' points (straightened by 1 - tension), so links
   * between the same pair of groups run together.
   */
  const strokeScale = _edgeStrokeScale(graph.links);
  const straighten = (point, p0, p1, fraction) => {
    const lineX = p0.x + (p1.x - p0.x) * fraction;
    const lineY = p0.y + (p1.y - p0.y) * fraction;
    return {
      x: tension * point.x + (1 - tension) * lineX,
      y: tension * point.y + (1 - tension) * lineY
    };
  };

  for (let k = 0; k < graph.links.length; k = k + 1) {
    const link = graph.links[k];
    const p0 = radial.pos[link.s];
    const p1 = radial.pos[link.t];
    const sourceGroup = graph.nodes[link.s].group;
    const targetGroup = graph.nodes[link.t].group;
    const color = _nodeColor(ctx, graph, link.s);

    let pathD = "";
    if (link.s === link.t) {
      pathD = _selfLoopPath(p0.x, p0.y, 4);
    } else if (sourceGroup === targetGroup) {
      const g = radial.groupPoint.get(sourceGroup);
      const control = straighten(g !== undefined ? g : { x: radial.cx, y: radial.cy }, p0, p1, 0.5);
      pathD = `M${p0.x.toFixed(2)},${p0.y.toFixed(2)} Q${control.x.toFixed(2)},${control.y.toFixed(2)} ${p1.x.toFixed(2)},${p1.y.toFixed(2)}`;
    } else {
      const gs = radial.groupPoint.get(sourceGroup);
      const gt = radial.groupPoint.get(targetGroup);
      const c1 = straighten(gs !== undefined ? gs : { x: radial.cx, y: radial.cy }, p0, p1, 1 / 3);
      const c2 = straighten(gt !== undefined ? gt : { x: radial.cx, y: radial.cy }, p0, p1, 2 / 3);
      pathD = `M${p0.x.toFixed(2)},${p0.y.toFixed(2)} ` +
        `C${c1.x.toFixed(2)},${c1.y.toFixed(2)} ${c2.x.toFixed(2)},${c2.y.toFixed(2)} ${p1.x.toFixed(2)},${p1.y.toFixed(2)}`;
    }

    const curve = svgEl("path", {
      d: pathD,
      fill: "none",
      stroke: color,
      "stroke-width": strokeScale(link.value).toFixed(2),
      "stroke-opacity": "0.55",
      part: "edge"
    }, [svgEl("title", null, _edgeTitle(graph, link))]);
    _wireEdge(curve, graph, link, ctx);
    layer.appendChild(curve);
  }
}


function _nodeAriaLabel(graph, index, degree) {
  /*
   * Accessible name of a node mark: label, group, value and link count.
   */
  const node = graph.nodes[index];
  let text = node.label;
  if (node.group !== null) {
    text = `${text}, group ${node.group}`;
  }
  if (node.value !== null) {
    text = `${text}, value ${formatNumber(node.value)}`;
  }
  text = `${text}, ${degree[index]} link${degree[index] === 1 ? "" : "s"}`;
  return text;
}


function _drawNodes(nodeLayer, labelLayer, graph, pos, radii, ctx, labelMode, radial) {
  /*
   * Node circles (the interactive marks) and their labels. labelMode:
   * "below", "below-rotated", "left" (vertical arc axis), "radial", "none".
   */
  const degree = new Array(graph.nodes.length).fill(0);
  for (let k = 0; k < graph.links.length; k = k + 1) {
    degree[graph.links[k].s] = degree[graph.links[k].s] + 1;
    if (graph.links[k].t !== graph.links[k].s) {
      degree[graph.links[k].t] = degree[graph.links[k].t] + 1;
    }
  }

  for (let i = 0; i < graph.nodes.length; i = i + 1) {
    const node = graph.nodes[i];
    const r = radii[i];
    const x = pos[i].x;
    const y = pos[i].y;
    const color = _nodeColor(ctx, graph, i);

    let title = node.label;
    if (node.group !== null) {
      title = `${title} (${node.group})`;
    }
    if (node.value !== null) {
      title = `${title}: ${formatNumber(node.value)}`;
    }

    const circle = svgEl("circle", {
      cx: x.toFixed(2),
      cy: y.toFixed(2),
      r: r.toFixed(2),
      fill: color,
      "fill-opacity": "0.9",
      stroke: "var(--mj-surface, #ffffff)",
      "stroke-width": 1.5,
      part: "node",
      tabindex: "0",
      role: "img",
      "aria-label": _nodeAriaLabel(graph, i, degree),
      "data-mark": `node:${node.index}`
    }, [svgEl("title", null, title)]);

    const nodeClickHandler = () => {
      ctx.emit("mj-chart-node-click", {
        id: node.id,
        label: node.label,
        group: node.group,
        index: node.index
      });
    };
    circle.addEventListener("click", nodeClickHandler);
    circle.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        nodeClickHandler();
      }
    });
    nodeLayer.appendChild(circle);

    if (labelMode === "none") {
      continue;
    }
    const textAttrs = {
      "font-size": LABEL_FONT,
      fill: "var(--mj-text, #14181f)",
      stroke: "var(--mj-surface, #ffffff)",
      "stroke-width": 3,
      "stroke-linejoin": "round",
      "paint-order": "stroke",
      "pointer-events": "none"
    };
    if (labelMode === "below-rotated") {
      const ly = y + r + 6;
      textAttrs.x = x.toFixed(2);
      textAttrs.y = ly.toFixed(2);
      textAttrs["text-anchor"] = "end";
      textAttrs["dominant-baseline"] = "middle";
      textAttrs.transform = `rotate(-40 ${x.toFixed(2)} ${ly.toFixed(2)})`;
    } else if (labelMode === "left") {
      textAttrs.x = (x - r - 4).toFixed(2);
      textAttrs.y = y.toFixed(2);
      textAttrs["text-anchor"] = "end";
      textAttrs["dominant-baseline"] = "middle";
    } else if (labelMode === "radial") {
      const angle = radial.angles[i];
      const lr = radial.radius + r + 5;
      const sin = Math.sin(angle);
      textAttrs.x = (radial.cx + lr * sin).toFixed(2);
      textAttrs.y = (radial.cy - lr * Math.cos(angle)).toFixed(2);
      textAttrs["text-anchor"] = sin > 0.05 ? "start" : (sin < -0.05 ? "end" : "middle");
      textAttrs["dominant-baseline"] = "middle";
    } else {
      textAttrs.x = x.toFixed(2);
      textAttrs.y = (y + r + 11).toFixed(2);
      textAttrs["text-anchor"] = "middle";
    }
    labelLayer.appendChild(svgEl("text", textAttrs, node.label));
  }
}


function _criticalPath(ctx, raw, graph) {
  /*
   * The critical path of a dependency graph: { nodes: Set of node indexes,
   * links: Set of link indexes joining two consecutive path entries }.
   * Empty when the data has none or show-critical-path is "false".
   */
  const critical = { nodes: new Set(), links: new Set() };
  const path = raw && Array.isArray(raw.criticalPath) === true ? raw.criticalPath : [];
  if (path.length === 0 || booleanOption(ctx, "show-critical-path", true) === false) {
    return critical;
  }
  const indexOf = new Map();
  for (let i = 0; i < graph.nodes.length; i = i + 1) {
    indexOf.set(graph.nodes[i].id, i);
  }
  const steps = new Set();
  for (let p = 0; p < path.length; p = p + 1) {
    const index = indexOf.get(String(path[p]));
    if (index !== undefined) {
      critical.nodes.add(index);
    }
    if (p + 1 < path.length) {
      steps.add(`${String(path[p])}\u0000${String(path[p + 1])}`);
    }
  }
  for (let k = 0; k < graph.links.length; k = k + 1) {
    const link = graph.links[k];
    if (steps.has(`${graph.nodes[link.s].id}\u0000${graph.nodes[link.t].id}`) === true) {
      critical.links.add(k);
    }
  }
  return critical;
}


function _reportCycles(ctx, graph, cycles) {
  /*
   * Emit mj-chart-cycle-detect once per data object (not on every resize
   * redraw) when the graph has cycles.
   */
  const source = ctx.model && ctx.model.source ? ctx.model.source : null;
  if (cycles.length === 0 || source === null || typeof source !== "object") {
    return;
  }
  if (_CYCLES_REPORTED.has(source) === true) {
    return;
  }
  _CYCLES_REPORTED.set(source, true);
  ctx.emit("mj-chart-cycle-detect", {
    cycles: cycles.map((cycle) => cycle.map((index) => graph.nodes[index].id))
  });
}


function _boxSize(graph, plotW, rankCount, widest, horizontal) {
  /*
   * The size of a dependency-graph box: as wide as the columns allow
   * (64-160px), taller when the nodes carry a status line.
   */
  const hasStatus = graph.nodes.some((node) => node.status !== null);
  const height = hasStatus === true ? BOX_H : BOX_H_PLAIN;
  let width = BOX_MAX_W;
  if (horizontal === true) {
    width = plotW / Math.max(rankCount, 1) - 28;
  } else {
    width = plotW / Math.max(widest, 1) - BOX_GAP;
  }
  width = Math.min(Math.max(width, BOX_MIN_W), BOX_MAX_W);
  return { w: width, h: height, hasStatus: hasStatus };
}


function _boxReach(halfW, halfH, angle) {
  /*
   * Distance from a box's centre to its boundary in direction `angle`.
   */
  const cos = Math.abs(Math.cos(angle));
  const sin = Math.abs(Math.sin(angle));
  const alongX = cos > 1e-6 ? halfW / cos : Infinity;
  const alongY = sin > 1e-6 ? halfH / sin : Infinity;
  return Math.min(alongX, alongY) + 1;
}


function _drawBoxNodes(nodeLayer, graph, pos, size, ctx, critical, cycleNodes) {
  /*
   * dependency-graph nodes: a labelled box per node (name, then the status
   * after a status dot), bordered in its status colour (else its group's),
   * amber and thicker on the critical path, with a warning badge when the
   * node is on a cycle.
   */
  const degree = new Array(graph.nodes.length).fill(0);
  for (let k = 0; k < graph.links.length; k = k + 1) {
    degree[graph.links[k].s] = degree[graph.links[k].s] + 1;
    if (graph.links[k].t !== graph.links[k].s) {
      degree[graph.links[k].t] = degree[graph.links[k].t] + 1;
    }
  }

  for (let i = 0; i < graph.nodes.length; i = i + 1) {
    const node = graph.nodes[i];
    const cx = pos[i].x;
    const cy = pos[i].y;
    const left = cx - size.w / 2;
    const top = cy - size.h / 2;
    const isCritical = critical.has(i);
    const inCycle = cycleNodes.has(i);
    const statusKey = node.status !== null ? node.status.toLowerCase() : "";
    let color = "var(--mj-border-strong, #c7ccd6)";
    if (STATUS_COLORS[statusKey] !== undefined) {
      color = STATUS_COLORS[statusKey];
    } else if (graph.groups.length > 0) {
      color = _nodeColor(ctx, graph, i);
    }

    let ariaLabel = _nodeAriaLabel(graph, i, degree);
    if (node.status !== null) {
      ariaLabel = `${ariaLabel}, status ${node.status}`;
    }
    if (isCritical === true) {
      ariaLabel = `${ariaLabel}, on the critical path`;
    }
    if (inCycle === true) {
      ariaLabel = `${ariaLabel}, in a cycle`;
    }

    const box = svgEl("g", {
      part: isCritical === true ? "node critical-path-node" : "node",
      tabindex: "0",
      role: "img",
      "aria-label": ariaLabel,
      "data-mark": `node:${node.index}`
    }, [svgEl("title", null, ariaLabel)]);
    box.appendChild(svgEl("rect", {
      x: left.toFixed(2), y: top.toFixed(2), width: size.w.toFixed(2), height: size.h, rx: 4,
      fill: isCritical === true ? "var(--mj-color-warning-surface, var(--mj-surface, #ffffff))" : "var(--mj-surface, #ffffff)",
      stroke: isCritical === true ? CRITICAL_COLOR : color,
      "stroke-width": isCritical === true ? 2.5 : 1.5
    }, []));
    const nameY = size.hasStatus === true ? cy - 3 : cy + 4;
    const badgeRoom = inCycle === true ? 14 : 0;
    box.appendChild(svgEl("text", {
      x: (left + 8).toFixed(2), y: nameY.toFixed(2), "font-size": 11, "font-weight": 500,
      fill: "var(--mj-text, #14181f)", "aria-hidden": "true"
    }, _fitLabel(node.label, size.w - 16 - badgeRoom, 11)));
    if (node.status !== null) {
      box.appendChild(svgEl("circle", {
        cx: (left + 11).toFixed(2), cy: (cy + 9).toFixed(2), r: 3.5, fill: color, "aria-hidden": "true"
      }, []));
      box.appendChild(svgEl("text", {
        x: (left + 18).toFixed(2), y: (cy + 12.5).toFixed(2), "font-size": 10,
        fill: "var(--mj-text-muted, #6b7280)", "aria-hidden": "true"
      }, _fitLabel(node.status, size.w - 26, 10)));
    }
    if (inCycle === true) {
      box.appendChild(svgEl("text", {
        x: (left + size.w - 15).toFixed(2), y: (top + 13).toFixed(2), "font-size": 12,
        fill: CYCLE_COLOR, part: "cycle-badge", "aria-hidden": "true"
      }, "⚠"));
    }

    const emitNode = node;
    const activate = () => {
      ctx.emit("mj-chart-node-click", {
        id: emitNode.id,
        label: emitNode.label,
        group: emitNode.group,
        index: emitNode.index
      });
    };
    box.addEventListener("click", activate);
    box.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        activate();
      }
    });
    nodeLayer.appendChild(box);
  }
}


function _fitLabel(text, maxWidth, fontSize) {
  /*
   * Shorten a label with an ellipsis so it fits a width.
   */
  const value = String(text);
  let fitted = value;
  const charW = fontSize * 0.56;
  if (value.length * charW > maxWidth) {
    const maxChars = Math.floor(maxWidth / charW) - 1;
    fitted = maxChars >= 2 ? value.slice(0, maxChars) + "…" : "";
  }
  return fitted;
}


function _publishTable(ctx, graph, extras) {
  /*
   * Accessible table: one row per node with its group, value, status and
   * critical-path membership (when the data has them) and the nodes it
   * links to and from.
   *
   * extras: { critical: Set of node indexes, cycles: [[node index]] }.
   */
  const hasGroups = graph.groups.length > 0;
  const hasStatus = graph.nodes.some((node) => node.status !== null);
  const hasCritical = extras.critical.size > 0;
  let hasValues = false;
  for (let i = 0; i < graph.nodes.length; i = i + 1) {
    if (graph.nodes[i].value !== null) {
      hasValues = true;
    }
  }
  const outgoing = graph.nodes.map(() => []);
  const incoming = graph.nodes.map(() => []);
  for (let k = 0; k < graph.links.length; k = k + 1) {
    const link = graph.links[k];
    const suffix = link.label !== null ? ` (${link.label})` : "";
    outgoing[link.s].push(`${graph.nodes[link.t].label}${suffix}`);
    incoming[link.t].push(`${graph.nodes[link.s].label}${suffix}`);
  }

  const columns = ["Node"];
  if (hasGroups === true) {
    columns.push("Group");
  }
  if (hasValues === true) {
    columns.push("Value");
  }
  if (hasStatus === true) {
    columns.push("Status");
  }
  if (hasCritical === true) {
    columns.push("Critical path");
  }
  columns.push("Links to", "Linked from");

  const rows = [];
  for (let i = 0; i < graph.nodes.length; i = i + 1) {
    const node = graph.nodes[i];
    const row = [node.label];
    if (hasGroups === true) {
      row.push(node.group !== null ? node.group : "");
    }
    if (hasValues === true) {
      row.push(node.value !== null ? node.value : "");
    }
    if (hasStatus === true) {
      row.push(node.status !== null ? node.status : "");
    }
    if (hasCritical === true) {
      row.push(extras.critical.has(i) === true ? "yes" : "");
    }
    row.push(outgoing[i].join(", "), incoming[i].join(", "));
    rows.push(row);
  }
  let caption = `${graph.nodes.length} nodes, ${graph.links.length} links`;
  if (extras.cycles.length > 0) {
    caption = `${caption}, ${extras.cycles.length} cycle${extras.cycles.length === 1 ? "" : "s"}`;
  }
  ctx.setTable({
    columns: columns,
    rows: rows,
    caption: caption
  });
}


function _publishLegend(ctx, graph) {
  /*
   * One colour-only legend entry per group (none without groups). The
   * colours are requested in group order so slots follow the legend.
   */
  const entries = [];
  for (let g = 0; g < graph.groups.length; g = g + 1) {
    entries.push({ label: graph.groups[g], color: ctx.colorFor(graph.groups[g]) });
  }
  ctx.setLegend(entries);
}


export function render(ctx) {
  /*
   * Render a network / node-link / arc / bundled / dependency-graph chart.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw;
  const root = svgEl("g", { part: "plot" }, []);
  const graph = _readGraph(raw);
  const n = graph.nodes.length;

  _publishLegend(ctx, graph);
  if (n === 0) {
    return root;
  }

  const layout = _resolveLayout(ctx, raw);
  const boxes = ctx.type === "dependency-graph" && layout === "layered";
  const critical = ctx.type === "dependency-graph" ? _criticalPath(ctx, raw, graph) : { nodes: new Set(), links: new Set() };
  let cycles = [];
  const explicit = _explicitOrientation(ctx);
  const plotW = Math.max(ctx.width - MARGIN.left - MARGIN.right, 10);
  const plotH = Math.max(ctx.height - MARGIN.top - MARGIN.bottom, 10);
  const labelled = n <= MAX_LABELLED_NODES;

  /* Radii shrink when many nodes share the plot. */
  const crowdRadius = Math.sqrt((plotW * plotH) / n) / 3;
  let radii = _nodeRadii(graph.nodes, Math.min(MAX_RADIUS, crowdRadius));
  let maxRadius = 0;
  for (let i = 0; i < n; i = i + 1) {
    maxRadius = Math.max(maxRadius, radii[i]);
  }

  let pos = null;
  let boxSize = null;
  let labelMode = labelled === true ? "below" : "none";
  let backEdges = null;
  let drawArrows = raw && raw.directed === true;
  let arc = null;
  let radial = null;

  if (layout === "arc") {
    const horizontal = explicit !== null ? explicit === "horizontal" : true;
    arc = _arcLayout(graph, plotW, plotH, horizontal);
    pos = arc.pos;
    radii = radii.map((r) => Math.min(r, arc.radiusCap));
    if (labelled === true) {
      labelMode = horizontal === true ? (arc.rotateLabels === true ? "below-rotated" : "below") : "left";
    }
    arc.horizontal = horizontal;
  } else if (layout === "bundled") {
    radial = _radialLayout(graph, plotW, plotH);
    pos = radial.pos;
    const slotRadius = (Math.PI * 2 * radial.radius) / radial.slots / 2 - 1;
    radii = radii.map((r) => Math.max(Math.min(r, slotRadius, 7), 2));
    labelMode = labelled === true ? "radial" : "none";
  } else if (layout === "layered") {
    const horizontal = explicit !== null ? explicit === "horizontal" : ctx.orientation === "horizontal";
    const box = _plotBox(plotW, plotH, maxRadius, labelled);
    let layered = _layeredLayout(graph, box, horizontal);
    if (boxes === true) {
      /*
       * Boxes: size them from the column structure, ask for the height the
       * busiest column needs, and lay out again inside the box insets.
       */
      boxSize = _boxSize(graph, plotW, layered.rankCount, layered.widest, horizontal);
      const needed = horizontal === true
        ? layered.widest * (boxSize.h + BOX_GAP) + 24
        : layered.rankCount * (boxSize.h + 36) + 24;
      ctx.setContentHeight(MARGIN.top + MARGIN.bottom + needed);
      const halfW = boxSize.w / 2 + 2;
      const halfH = boxSize.h / 2 + 12;
      const inner = {
        x0: halfW, y0: halfH,
        x1: Math.max(plotW - halfW, halfW + 1),
        y1: Math.max(plotH - halfH, halfH + 1)
      };
      layered = _layeredLayout(graph, inner, horizontal);
    }
    pos = layered.pos;
    backEdges = layered.backEdges;
    cycles = layered.backEdges.cycles;
    drawArrows = true;
  } else {
    const box = _plotBox(plotW, plotH, maxRadius, labelled);
    const normalized = layout === "static" ? _staticLayout(graph) : _cachedForce(graph, raw, box);
    pos = _separate(_toBox(normalized, box), radii, box, n > 300 ? 4 : 20);
  }

  /* Last guard: every position is finite. */
  for (let i = 0; i < n; i = i + 1) {
    if (pos[i] === undefined || pos[i] === null ||
        Number.isFinite(pos[i].x) === false || Number.isFinite(pos[i].y) === false) {
      pos[i] = { x: plotW / 2, y: plotH / 2 };
    }
  }

  const plot = svgEl("g", { transform: `translate(${MARGIN.left},${MARGIN.top})` }, []);
  root.appendChild(plot);
  const edgeLayer = svgEl("g", { "aria-hidden": "true" }, []);
  const nodeLayer = svgEl("g", {}, []);
  const labelLayer = svgEl("g", { "aria-hidden": "true" }, []);
  plot.appendChild(edgeLayer);
  plot.appendChild(nodeLayer);
  plot.appendChild(labelLayer);

  if (arc !== null) {
    const first = arc.horizontal === true
      ? `M0,${arc.axis.toFixed(2)} L${plotW},${arc.axis.toFixed(2)}`
      : `M${arc.axis.toFixed(2)},0 L${arc.axis.toFixed(2)},${plotH}`;
    edgeLayer.appendChild(svgEl("path", {
      d: first,
      stroke: "var(--mj-border, #e1e4ea)",
      "stroke-width": 1
    }, []));
    _drawArcLinks(edgeLayer, graph, pos, ctx, arc.horizontal, arc.arcRoom, arc.radiusCap);
  } else if (radial !== null) {
    let tension = parseFloat(ctx.attrs("tension", raw && raw.tension !== undefined ? String(raw.tension) : String(DEFAULT_TENSION)));
    if (Number.isFinite(tension) === false) {
      tension = DEFAULT_TENSION;
    }
    tension = Math.min(Math.max(tension, 0), 1);
    _drawBundledLinks(edgeLayer, graph, radial, ctx, tension);
  } else if (boxSize !== null) {
    const size = boxSize;
    const boxStyle = {
      reach: (index, angle) => _boxReach(size.w / 2, size.h / 2, angle),
      critical: critical.links,
      halfW: size.w / 2,
      halfH: size.h / 2
    };
    _drawStraightLinks(edgeLayer, graph, pos, radii.map(() => size.h / 2 + 4), ctx, drawArrows, backEdges, boxStyle);
  } else {
    _drawStraightLinks(edgeLayer, graph, pos, radii, ctx, drawArrows, backEdges, null);
  }

  if (boxSize !== null) {
    const cycleNodes = new Set();
    for (let c = 0; c < cycles.length; c = c + 1) {
      for (let m = 0; m < cycles[c].length; m = m + 1) {
        cycleNodes.add(cycles[c][m]);
      }
    }
    _drawBoxNodes(nodeLayer, graph, pos, boxSize, ctx, critical.nodes, cycleNodes);
  } else {
    _drawNodes(nodeLayer, labelLayer, graph, pos, radii, ctx, labelMode, radial);
  }

  _publishTable(ctx, graph, { critical: critical.nodes, cycles: cycles });
  if (ctx.type === "dependency-graph") {
    _reportCycles(ctx, graph, cycles);
  }

  return root;
}


registerRenderer("network", render, { legend: "none" });
registerRenderer("arc-diagram", render, { legend: "none", orientation: "horizontal" });
registerRenderer("node-link", render, { legend: "none" });
registerRenderer("edge-bundling", render, { legend: "none" });
registerRenderer("dependency-graph", render, { legend: "none", orientation: "horizontal" });
