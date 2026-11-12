/*
 * flowchart.js
 *
 * Flowchart / Decision-flow renderer.
 *
 * Registers: "flowchart", "decision-flow"
 *
 * ctx.raw shape:
 *   nodes: [{ id, label, shape }]   shape: "rect" (process, default) |
 *                                   "diamond" (decision) | "oval" (start / end)
 *   links: [{ source, target, label? }]
 *
 * Layout (layered, Sugiyama-style):
 *   - Cycles are found with a DFS; back-edges and self-links are left out of
 *     the ranking (so it always terminates) and drawn dashed through a side
 *     channel beside the diagram, never through other nodes.
 *   - Ranks are longest-path ranks; ranks are at least the tallest node of
 *     the rank plus RANK_GAP apart and nodes in a rank at least NODE_GAP
 *     apart. Children are spread symmetrically under their parent.
 *   - Shapes are sized from their (wrapped, at most three lines) label.
 *   - The finished diagram is scaled down uniformly to fit the plot (never
 *     up), so nodes never overlap however small the chart is.
 *   - Forward edges are orthogonal connectors leaving the source's bottom
 *     (vertical) or right (horizontal) port; a branch leaving a decision
 *     sideways starts at the diamond's side vertex. Arrowheads follow the
 *     last segment.
 *
 * Orientation: "vertical" (top-to-bottom) / "horizontal" (left-to-right) when
 * the page sets `orientation` (or meta.orientation); otherwise the direction
 * that lets the diagram be drawn larger in the chart's box.
 *
 * "decision-flow" is the same diagram with fixed branch sides: the "Yes" /
 * "True" branch of a node is always placed before (left of / above) its
 * "No" / "False" branch.
 *
 * Node colour encodes the shape kind (process / decision / start-end), listed
 * in the legend. The accessible table lists every step with its next steps.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl } from "../svgdraw.js";


const FONT_SIZE = 11;
const CHAR_W = 6.3;
const LINE_H = 13;
const MAX_LINE_CHARS = 18;
const MAX_DECISION_LINE_CHARS = 12;
const MAX_LINES = 3;
const RECT_MIN_W = 72;
const RECT_MAX_W = 160;
const RECT_PAD_X = 12;
const RANK_GAP_VERTICAL = 30;
const RANK_GAP_HORIZONTAL = 44;
const NODE_GAP = 20;
const CHANNEL_GAP = 14;
const MARGIN = { top: 10, right: 10, bottom: 10, left: 10 };
const ARROW_SIZE = 7;

const SHAPE_KIND = {
  rect: { slot: 0, name: "Process" },
  diamond: { slot: 1, name: "Decision" },
  oval: { slot: 2, name: "Start / end" }
};

const SHAPE_ALIASES = {
  process: "rect",
  box: "rect",
  decision: "diamond",
  terminal: "oval",
  start: "oval",
  end: "oval",
  ellipse: "oval",
  circle: "oval"
};

const YES_LABELS = ["yes", "y", "true", "ok", "pass"];
const NO_LABELS = ["no", "n", "false", "fail"];


/* ---------- data ---------- */

function _shapeOf(value) {
  /*
   * Normalize a node shape name to rect / diamond / oval.
   */
  let shape = typeof value === "string" ? value.toLowerCase() : "rect";
  if (SHAPE_ALIASES[shape] !== undefined) {
    shape = SHAPE_ALIASES[shape];
  }
  if (SHAPE_KIND[shape] === undefined) {
    shape = "rect";
  }
  return shape;
}


function _wrapLabel(text, maxChars) {
  /*
   * Greedy word wrap into at most MAX_LINES lines; an over-long word is
   * split and the last line ends in an ellipsis when text is left over.
   */
  const words = String(text).split(/\s+/).filter((word) => word.length > 0);
  const lines = [];
  let current = "";
  let truncated = false;
  for (let w = 0; w < words.length; w = w + 1) {
    let word = words[w];
    while (word.length > maxChars) {
      if (current.length > 0) {
        lines.push(current);
        current = "";
      }
      lines.push(word.slice(0, maxChars));
      word = word.slice(maxChars);
    }
    if (current.length === 0) {
      current = word;
    } else if (current.length + 1 + word.length <= maxChars) {
      current = `${current} ${word}`;
    } else {
      lines.push(current);
      current = word;
    }
  }
  if (current.length > 0) {
    lines.push(current);
  }
  if (lines.length === 0) {
    lines.push("");
  }
  if (lines.length > MAX_LINES) {
    truncated = true;
    lines.length = MAX_LINES;
  }
  if (truncated === true) {
    const last = lines[MAX_LINES - 1];
    lines[MAX_LINES - 1] = `${last.slice(0, Math.max(maxChars - 1, 1))}…`;
  }
  return lines;
}


function _sizeNode(node) {
  /*
   * Half width / half height of a node's shape, from its wrapped label.
   */
  const maxChars = node.shape === "diamond" ? MAX_DECISION_LINE_CHARS : MAX_LINE_CHARS;
  node.lines = _wrapLabel(node.label, maxChars);
  let longest = 0;
  for (let l = 0; l < node.lines.length; l = l + 1) {
    longest = Math.max(longest, node.lines[l].length);
  }
  const textW = longest * CHAR_W;
  const textH = node.lines.length * LINE_H;

  if (node.shape === "diamond") {
    /* The text box must fit inside |x|/hw + |y|/hh <= 1. */
    node.hh = textH / 2 + 12;
    node.hw = Math.max((textW / 2 + 4) / (1 - (textH / 2) / node.hh), 30);
  } else if (node.shape === "oval") {
    node.hw = Math.max(textW / 2 + 16, 30);
    node.hh = Math.max(textH / 2 + 8, 18);
  } else {
    node.hw = Math.min(Math.max(textW + RECT_PAD_X * 2, RECT_MIN_W), RECT_MAX_W) / 2;
    node.hh = Math.max(textH + 16, 36) / 2;
  }
}


function _readGraph(raw) {
  /*
   * Normalize raw.nodes / raw.links into index-based records without
   * touching the data. Nodes without an id are skipped (a repeated id keeps
   * its first node); links with unknown ends are skipped.
   */
  const rawNodes = (raw && Array.isArray(raw.nodes)) ? raw.nodes : [];
  const rawLinks = (raw && Array.isArray(raw.links)) ? raw.links : [];
  const nodes = [];
  const indexOf = new Map();

  for (let i = 0; i < rawNodes.length; i = i + 1) {
    const entry = rawNodes[i];
    if (entry === null || typeof entry !== "object" || entry.id === null || entry.id === undefined) {
      continue;
    }
    const id = String(entry.id);
    if (indexOf.has(id) === true) {
      continue;
    }
    const hasLabel = entry.label !== null && entry.label !== undefined;
    const node = {
      id: id,
      label: hasLabel === true ? String(entry.label) : id,
      shape: _shapeOf(entry.shape),
      lines: [],
      hw: 0,
      hh: 0,
      x: 0,
      y: 0
    };
    _sizeNode(node);
    indexOf.set(id, nodes.length);
    nodes.push(node);
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
    const hasLabel = entry.label !== null && entry.label !== undefined && String(entry.label) !== "";
    links.push({ s: s, t: t, label: hasLabel === true ? String(entry.label) : null });
  }
  return { nodes: nodes, links: links };
}


function _branchSide(label) {
  /*
   * -1 for a "yes" branch label, +1 for a "no" label, 0 otherwise.
   */
  if (label === null) {
    return 0;
  }
  const text = label.trim().toLowerCase();
  let side = 0;
  if (YES_LABELS.indexOf(text) >= 0) {
    side = -1;
  } else if (NO_LABELS.indexOf(text) >= 0) {
    side = 1;
  }
  return side;
}


/* ---------- ranking ---------- */

function _findBackEdges(n, links) {
  /*
   * Iterative DFS: an edge into a node still on the DFS stack closes a
   * cycle (a back-edge); a self-link is one too.
   *
   * :returns: A Set of link indexes.
   */
  const out = [];
  for (let i = 0; i < n; i = i + 1) {
    out.push([]);
  }
  const back = new Set();
  for (let k = 0; k < links.length; k = k + 1) {
    if (links[k].s === links[k].t) {
      back.add(k);
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
      } else if (state[target] === 0) {
        state[target] = 1;
        stack.push({ node: target, next: 0 });
      }
    }
  }
  return back;
}


function _rankNodes(graph) {
  /*
   * Longest-path ranks over the acyclic part (Kahn's algorithm: every node
   * is dequeued once), then nodes grouped and ordered per rank.
   *
   * :returns: { rank, columns, backEdges, forward } -- forward[s] lists the
   *     forward link indexes leaving node s.
   */
  const n = graph.nodes.length;
  const links = graph.links;
  const backEdges = _findBackEdges(n, links);
  const forward = [];
  const inDegree = new Array(n).fill(0);
  for (let i = 0; i < n; i = i + 1) {
    forward.push([]);
  }
  for (let k = 0; k < links.length; k = k + 1) {
    if (backEdges.has(k) === false) {
      forward[links[k].s].push(k);
      inDegree[links[k].t] = inDegree[links[k].t] + 1;
    }
  }

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
    for (let f = 0; f < forward[current].length; f = f + 1) {
      const next = links[forward[current][f]].t;
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
  return { rank: rank, columns: columns, backEdges: backEdges, forward: forward };
}


/* ---------- placement ---------- */

function _placeNodes(graph, ranking, vertical, fixedSides) {
  /*
   * Assign x / y centres. The rank axis advances by each rank's largest
   * node plus the rank gap; along the cross axis each node aims at the
   * average of its parents' "child slots" (children spread symmetrically
   * under a parent, yes before no when fixedSides) and nodes are then
   * pushed apart to NODE_GAP.
   *
   * :returns: The placed node list (positions are written to the layout
   *     copies in graph.nodes, never to the data).
   */
  const nodes = graph.nodes;
  const links = graph.links;
  const columns = ranking.columns;
  const rankGap = vertical === true ? RANK_GAP_VERTICAL : RANK_GAP_HORIZONTAL;
  const along = (node) => (vertical === true ? node.hh : node.hw);
  const across = (node) => (vertical === true ? node.hw : node.hh);

  /* Rank axis. */
  let cursor = 0;
  const rankCentre = [];
  for (let r = 0; r < columns.length; r = r + 1) {
    let extent = 0;
    for (let c = 0; c < columns[r].length; c = c + 1) {
      extent = Math.max(extent, along(nodes[columns[r][c]]) * 2);
    }
    rankCentre.push(cursor + extent / 2);
    cursor = cursor + extent + rankGap;
  }

  /* Children of each node in the next rank, ordered (yes first when fixed). */
  const childSlot = new Map();
  for (let s = 0; s < nodes.length; s = s + 1) {
    const children = ranking.forward[s]
      .map((linkIndex, position) => ({ linkIndex: linkIndex, position: position }))
      .filter((entry) => ranking.rank[links[entry.linkIndex].t] === ranking.rank[s] + 1);
    if (fixedSides === true) {
      children.sort((a, b) => (_branchSide(links[a.linkIndex].label) - _branchSide(links[b.linkIndex].label)) ||
        (a.position - b.position));
    }
    let total = 0;
    for (let c = 0; c < children.length; c = c + 1) {
      total = total + across(nodes[links[children[c].linkIndex].t]) * 2;
    }
    total = total + NODE_GAP * Math.max(children.length - 1, 0);
    let offset = -total / 2;
    for (let c = 0; c < children.length; c = c + 1) {
      const size = across(nodes[links[children[c].linkIndex].t]) * 2;
      childSlot.set(children[c].linkIndex, offset + size / 2);
      offset = offset + size + NODE_GAP;
    }
  }

  const cross = new Array(nodes.length).fill(0);
  for (let r = 0; r < columns.length; r = r + 1) {
    const column = columns[r];
    const desired = new Map();
    for (let c = 0; c < column.length; c = c + 1) {
      desired.set(column[c], null);
    }
    if (r > 0) {
      const sums = new Map();
      for (let k = 0; k < links.length; k = k + 1) {
        if (ranking.backEdges.has(k) === true || desired.has(links[k].t) === false) {
          continue;
        }
        const slot = childSlot.has(k) === true ? childSlot.get(k) : 0;
        const entry = sums.get(links[k].t) || { sum: 0, count: 0 };
        entry.sum = entry.sum + cross[links[k].s] + slot;
        entry.count = entry.count + 1;
        sums.set(links[k].t, entry);
      }
      sums.forEach((entry, node) => {
        desired.set(node, entry.sum / entry.count);
      });
    }

    /* Order by desired position; nodes without parents keep data order. */
    const ordered = column.map((node, position) => ({
      node: node,
      position: position,
      want: desired.get(node)
    }));
    let fallback = 0;
    for (let o = 0; o < ordered.length; o = o + 1) {
      if (ordered[o].want === null) {
        ordered[o].want = fallback;
        fallback = fallback + across(nodes[ordered[o].node]) * 2 + NODE_GAP;
      }
    }
    ordered.sort((a, b) => (a.want - b.want) || (a.position - b.position));

    /* Push apart, then shift the rank back towards where it wanted to be. */
    let edge = -Infinity;
    let shiftSum = 0;
    for (let o = 0; o < ordered.length; o = o + 1) {
      const half = across(nodes[ordered[o].node]);
      const placed = Math.max(ordered[o].want, edge + NODE_GAP + half);
      cross[ordered[o].node] = placed;
      edge = placed + half;
      shiftSum = shiftSum + (placed - ordered[o].want);
    }
    const shift = ordered.length > 0 ? shiftSum / ordered.length : 0;
    for (let o = 0; o < ordered.length; o = o + 1) {
      cross[ordered[o].node] = cross[ordered[o].node] - shift;
    }
  }

  for (let i = 0; i < nodes.length; i = i + 1) {
    if (vertical === true) {
      nodes[i].x = cross[i];
      nodes[i].y = rankCentre[ranking.rank[i]];
    } else {
      nodes[i].x = rankCentre[ranking.rank[i]];
      nodes[i].y = cross[i];
    }
  }
  return nodes;
}


/* ---------- edge routing ---------- */

function _routeEdges(graph, ranking, vertical) {
  /*
   * Orthogonal routes for every link.
   *
   * Forward: from the source's bottom (vertical) / right (horizontal) port
   * to the target's top / left port, bending in the gap just before the
   * target. A decision whose branch goes sideways leaves from the diamond's
   * side (or top / bottom) vertex instead.
   * Back-edges: out of the source's right (vertical) / bottom (horizontal)
   * side into a channel outside the diagram, along it, and into the
   * target's same side. Self-links: a loop on that side.
   *
   * :returns: [{ link, points: [{x, y}], back, labelAt: {x, y, anchor} }]
   */
  const nodes = graph.nodes;
  const rankGap = vertical === true ? RANK_GAP_VERTICAL : RANK_GAP_HORIZONTAL;

  let maxRight = -Infinity;
  let maxBottom = -Infinity;
  for (let i = 0; i < nodes.length; i = i + 1) {
    maxRight = Math.max(maxRight, nodes[i].x + nodes[i].hw);
    maxBottom = Math.max(maxBottom, nodes[i].y + nodes[i].hh);
  }

  const routes = [];
  let channel = 0;
  for (let k = 0; k < graph.links.length; k = k + 1) {
    const link = graph.links[k];
    const s = nodes[link.s];
    const t = nodes[link.t];
    let points = [];
    const back = ranking.backEdges.has(k) === true;
    let labelAt = null;

    if (link.s === link.t) {
      if (vertical === true) {
        const x = s.x + s.hw;
        points = [{ x: x, y: s.y - 6 }, { x: x + 16, y: s.y - 6 }, { x: x + 16, y: s.y + 6 }, { x: x, y: s.y + 6 }];
        labelAt = { x: x + 19, y: s.y, anchor: "start" };
      } else {
        const y = s.y + s.hh;
        points = [{ x: s.x - 6, y: y }, { x: s.x - 6, y: y + 16 }, { x: s.x + 6, y: y + 16 }, { x: s.x + 6, y: y }];
        labelAt = { x: s.x + 9, y: y + 18, anchor: "start" };
      }
    } else if (back === true) {
      channel = channel + 1;
      if (vertical === true) {
        const cx = maxRight + CHANNEL_GAP * channel;
        points = [
          { x: s.x + s.hw, y: s.y },
          { x: cx, y: s.y },
          { x: cx, y: t.y },
          { x: t.x + t.hw, y: t.y }
        ];
        labelAt = { x: cx + 3, y: (s.y + t.y) / 2, anchor: "start" };
      } else {
        const cy = maxBottom + CHANNEL_GAP * channel;
        points = [
          { x: s.x, y: s.y + s.hh },
          { x: s.x, y: cy },
          { x: t.x, y: cy },
          { x: t.x, y: t.y + t.hh }
        ];
        labelAt = { x: (s.x + t.x) / 2, y: cy + 12, anchor: "middle" };
      }
    } else if (vertical === true) {
      const end = { x: t.x, y: t.y - t.hh };
      const sideways = s.shape === "diamond" && Math.abs(t.x - s.x) > s.hw * 0.5;
      if (sideways === true) {
        const dir = t.x < s.x ? -1 : 1;
        const start = { x: s.x + dir * s.hw, y: s.y };
        points = [start, { x: t.x, y: s.y }, end];
        labelAt = { x: start.x + dir * 6, y: s.y - 5, anchor: dir < 0 ? "end" : "start" };
      } else {
        const start = { x: s.x, y: s.y + s.hh };
        if (Math.abs(t.x - s.x) < 0.5) {
          points = [start, end];
        } else {
          const bendY = end.y - rankGap / 2;
          points = [start, { x: s.x, y: bendY }, { x: t.x, y: bendY }, end];
        }
        labelAt = { x: start.x + 5, y: start.y + 11, anchor: "start" };
      }
    } else {
      const end = { x: t.x - t.hw, y: t.y };
      const sideways = s.shape === "diamond" && Math.abs(t.y - s.y) > s.hh * 0.5;
      if (sideways === true) {
        const dir = t.y < s.y ? -1 : 1;
        const start = { x: s.x, y: s.y + dir * s.hh };
        points = [start, { x: s.x, y: t.y }, end];
        labelAt = { x: s.x + 5, y: start.y + dir * 10, anchor: "start" };
      } else {
        const start = { x: s.x + s.hw, y: s.y };
        if (Math.abs(t.y - s.y) < 0.5) {
          points = [start, end];
        } else {
          const bendX = end.x - rankGap / 2;
          points = [start, { x: bendX, y: s.y }, { x: bendX, y: t.y }, end];
        }
        labelAt = { x: start.x + 4, y: start.y - 5, anchor: "start" };
      }
    }
    routes.push({ link: link, points: points, back: back, labelAt: labelAt });
  }
  return routes;
}


function _layout(graph, vertical, fixedSides) {
  /*
   * Rank, place and route the diagram in one direction.
   *
   * :returns: { routes, bounds: {x0, y0, x1, y1} }.
   */
  const ranking = _rankNodes(graph);
  _placeNodes(graph, ranking, vertical, fixedSides);
  const routes = _routeEdges(graph, ranking, vertical);

  const bounds = { x0: Infinity, y0: Infinity, x1: -Infinity, y1: -Infinity };
  const include = (x, y) => {
    bounds.x0 = Math.min(bounds.x0, x);
    bounds.y0 = Math.min(bounds.y0, y);
    bounds.x1 = Math.max(bounds.x1, x);
    bounds.y1 = Math.max(bounds.y1, y);
  };
  for (let i = 0; i < graph.nodes.length; i = i + 1) {
    const node = graph.nodes[i];
    include(node.x - node.hw, node.y - node.hh);
    include(node.x + node.hw, node.y + node.hh);
  }
  for (let e = 0; e < routes.length; e = e + 1) {
    for (let p = 0; p < routes[e].points.length; p = p + 1) {
      include(routes[e].points[p].x, routes[e].points[p].y);
    }
    const label = routes[e].link.label;
    if (label !== null && routes[e].labelAt !== null) {
      const width = label.length * CHAR_W * 0.95;
      const at = routes[e].labelAt;
      const left = at.anchor === "end" ? at.x - width : (at.anchor === "middle" ? at.x - width / 2 : at.x);
      include(left, at.y - 10);
      include(left + width, at.y + 3);
    }
  }
  return { routes: routes, bounds: bounds };
}


function _snapshot(graph) {
  /*
   * Copy the node positions (the layout writes them into graph.nodes).
   */
  const copy = graph.nodes.map((node) => ({ x: node.x, y: node.y }));
  return copy;
}


/* ---------- drawing ---------- */

function _arrowheadPath(tx, ty, angle) {
  /*
   * Build an arrowhead polygon path at (tx,ty) pointing in direction `angle`.
   */
  const a1 = angle + Math.PI * 0.82;
  const a2 = angle - Math.PI * 0.82;
  const x1 = tx + ARROW_SIZE * Math.cos(a1);
  const y1 = ty + ARROW_SIZE * Math.sin(a1);
  const x2 = tx + ARROW_SIZE * Math.cos(a2);
  const y2 = ty + ARROW_SIZE * Math.sin(a2);
  return `${tx.toFixed(2)},${ty.toFixed(2)} ${x1.toFixed(2)},${y1.toFixed(2)} ${x2.toFixed(2)},${y2.toFixed(2)}`;
}


function _shapeElement(node, color) {
  /*
   * The SVG shape of a node.
   */
  const common = {
    fill: color,
    "fill-opacity": "0.16",
    stroke: color,
    "stroke-width": 2
  };
  let shape = null;
  if (node.shape === "diamond") {
    const pts = `${node.x.toFixed(2)},${(node.y - node.hh).toFixed(2)} ` +
      `${(node.x + node.hw).toFixed(2)},${node.y.toFixed(2)} ` +
      `${node.x.toFixed(2)},${(node.y + node.hh).toFixed(2)} ` +
      `${(node.x - node.hw).toFixed(2)},${node.y.toFixed(2)}`;
    shape = svgEl("polygon", { points: pts, ...common }, []);
  } else if (node.shape === "oval") {
    shape = svgEl("ellipse", {
      cx: node.x.toFixed(2),
      cy: node.y.toFixed(2),
      rx: node.hw.toFixed(2),
      ry: node.hh.toFixed(2),
      ...common
    }, []);
  } else {
    shape = svgEl("rect", {
      x: (node.x - node.hw).toFixed(2),
      y: (node.y - node.hh).toFixed(2),
      width: (node.hw * 2).toFixed(2),
      height: (node.hh * 2).toFixed(2),
      rx: 4,
      ...common
    }, []);
  }
  return shape;
}


function _drawNode(node, color, ariaLabel) {
  /*
   * Draw a single node shape. Returns a <g> (the interactive mark)
   * containing the shape and its wrapped label.
   */
  const g = svgEl("g", {
    part: "node",
    tabindex: "0",
    role: "img",
    "aria-label": ariaLabel
  }, []);
  g.appendChild(svgEl("title", null, node.label));
  g.appendChild(_shapeElement(node, color));

  const text = svgEl("text", {
    x: node.x.toFixed(2),
    y: node.y.toFixed(2),
    "text-anchor": "middle",
    "font-size": FONT_SIZE,
    fill: "var(--mj-text, #14181f)",
    "aria-hidden": "true",
    "pointer-events": "none"
  }, []);
  const firstDy = -((node.lines.length - 1) * LINE_H) / 2;
  for (let l = 0; l < node.lines.length; l = l + 1) {
    text.appendChild(svgEl("tspan", {
      x: node.x.toFixed(2),
      dy: (l === 0 ? firstDy + 4 : LINE_H).toFixed(2)
    }, node.lines[l]));
  }
  g.appendChild(text);
  return g;
}


function _drawEdge(route, graph, ctx) {
  /*
   * Draw one connector with its arrowhead (along the final segment) and
   * optional label.
   */
  const points = route.points;
  const stroke = route.back === true ? "var(--mj-text-muted, #6b7280)" : "var(--mj-border-strong, #9aa3b2)";
  const group = svgEl("g", { part: route.back === true ? "edge back-edge" : "edge" }, []);

  let pathD = "";
  for (let p = 0; p < points.length; p = p + 1) {
    pathD = pathD + `${p === 0 ? "M" : "L"}${points[p].x.toFixed(2)},${points[p].y.toFixed(2)} `;
  }
  const last = points[points.length - 1];
  const before = points[points.length - 2];
  const angle = Math.atan2(last.y - before.y, last.x - before.x);

  group.appendChild(svgEl("path", {
    d: pathD.trim(),
    fill: "none",
    stroke: stroke,
    "stroke-width": 1.5,
    "stroke-dasharray": route.back === true ? "5 3" : null
  }, []));
  group.appendChild(svgEl("polygon", {
    points: _arrowheadPath(last.x, last.y, angle),
    fill: stroke
  }, []));

  const link = route.link;
  if (link.label !== null && route.labelAt !== null) {
    group.appendChild(svgEl("text", {
      x: route.labelAt.x.toFixed(2),
      y: route.labelAt.y.toFixed(2),
      "text-anchor": route.labelAt.anchor,
      "font-size": 10,
      fill: "var(--mj-text-muted, #6b7280)",
      stroke: "var(--mj-surface, #ffffff)",
      "stroke-width": 3,
      "stroke-linejoin": "round",
      "paint-order": "stroke"
    }, link.label));
  }

  group.addEventListener("click", () => {
    ctx.emit("mj-chart-edge-click", {
      source: graph.nodes[link.s].id,
      target: graph.nodes[link.t].id,
      label: link.label
    });
  });
  return group;
}


function _nextSteps(graph) {
  /*
   * Per node, the "Target (label)" texts of its outgoing links.
   */
  const next = graph.nodes.map(() => []);
  for (let k = 0; k < graph.links.length; k = k + 1) {
    const link = graph.links[k];
    const suffix = link.label !== null ? ` (${link.label})` : "";
    next[link.s].push(`${graph.nodes[link.t].label}${suffix}`);
  }
  return next;
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


export function render(ctx) {
  /*
   * Render a flowchart or decision-flow diagram.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw;
  const root = svgEl("g", { part: "plot" }, []);
  const graph = _readGraph(raw);
  const fixedSides = ctx.type === "decision-flow";

  if (graph.nodes.length === 0) {
    ctx.setLegend([]);
    return root;
  }

  const plotW = Math.max(ctx.width - MARGIN.left - MARGIN.right, 10);
  const plotH = Math.max(ctx.height - MARGIN.top - MARGIN.bottom, 10);
  const fitScale = (bounds) => {
    const width = Math.max(bounds.x1 - bounds.x0, 1);
    const height = Math.max(bounds.y1 - bounds.y0, 1);
    return Math.min(1, plotW / width, plotH / height);
  };

  /* Direction: the page's choice, else whichever fits larger. */
  const explicit = _explicitOrientation(ctx);
  let vertical = explicit !== null ? explicit === "vertical" : true;
  let result = _layout(graph, vertical, fixedSides);
  if (explicit === null) {
    const verticalPositions = _snapshot(graph);
    const other = _layout(graph, false, fixedSides);
    if (fitScale(other.bounds) > fitScale(result.bounds) * 1.05) {
      vertical = false;
      result = other;
    } else {
      for (let i = 0; i < graph.nodes.length; i = i + 1) {
        graph.nodes[i].x = verticalPositions[i].x;
        graph.nodes[i].y = verticalPositions[i].y;
      }
    }
  }

  const bounds = result.bounds;
  const scale = fitScale(bounds);
  const drawnW = (bounds.x1 - bounds.x0) * scale;
  const drawnH = (bounds.y1 - bounds.y0) * scale;
  const offsetX = MARGIN.left + (plotW - drawnW) / 2 - bounds.x0 * scale;
  const offsetY = MARGIN.top + (plotH - drawnH) / 2 - bounds.y0 * scale;

  const plot = svgEl("g", {
    transform: `translate(${offsetX.toFixed(2)},${offsetY.toFixed(2)}) scale(${scale.toFixed(4)})`
  }, []);
  root.appendChild(plot);

  /* Edges first (behind nodes); decoration is hidden from screen readers. */
  const edgeLayer = svgEl("g", { "aria-hidden": "true" }, []);
  plot.appendChild(edgeLayer);
  for (let e = 0; e < result.routes.length; e = e + 1) {
    edgeLayer.appendChild(_drawEdge(result.routes[e], graph, ctx));
  }

  /* Nodes on top, coloured by shape kind. */
  const next = _nextSteps(graph);
  const shapesUsed = [];
  const nodeLayer = svgEl("g", {}, []);
  plot.appendChild(nodeLayer);
  for (let i = 0; i < graph.nodes.length; i = i + 1) {
    const node = graph.nodes[i];
    const kind = SHAPE_KIND[node.shape];
    if (shapesUsed.indexOf(node.shape) < 0) {
      shapesUsed.push(node.shape);
    }
    let ariaLabel = `${node.label} (${kind.name.toLowerCase()})`;
    if (next[i].length > 0) {
      ariaLabel = `${ariaLabel}, next: ${next[i].join(", ")}`;
    }
    const nodeGroup = _drawNode(node, ctx.colorFor(kind.slot), ariaLabel);

    const nodeClickHandler = () => {
      ctx.emit("mj-chart-node-click", {
        id: node.id,
        label: node.label
      });
    };
    nodeGroup.addEventListener("click", nodeClickHandler);
    nodeGroup.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        nodeClickHandler();
      }
    });
    nodeLayer.appendChild(nodeGroup);
  }

  /* Legend: one colour entry per shape kind present. */
  const order = ["rect", "diamond", "oval"];
  const legend = [];
  for (let o = 0; o < order.length; o = o + 1) {
    if (shapesUsed.indexOf(order[o]) >= 0) {
      legend.push({ label: SHAPE_KIND[order[o]].name, color: ctx.colorFor(SHAPE_KIND[order[o]].slot) });
    }
  }
  ctx.setLegend(legend);

  ctx.setTable({
    columns: ["Step", "Shape", "Next steps"],
    rows: graph.nodes.map((node, index) => [node.label, SHAPE_KIND[node.shape].name, next[index].join(", ")]),
    caption: `${graph.nodes.length} steps, ${graph.links.length} connections`
  });

  return root;
}


registerRenderer("flowchart", render, { legend: "none" });
registerRenderer("decision-flow", render, { legend: "none" });
