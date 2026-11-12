/*
 * sankey.js
 *
 * Sankey / Alluvial renderer.
 *
 * Registers: "sankey", "alluvial" (both default to orientation="horizontal")
 *
 * ctx.raw shape:
 *   nodes: [{ id, label?, group?, time? }]   (optional: nodes named only in
 *                                             `links` are added automatically)
 *   links: [{ source, target, value }]
 *
 * Options:
 *   orientation  "horizontal" (columns left to right, default) | "vertical"
 *                (columns top to bottom)
 *   mode         "alluvial" on type="sankey" selects the alluvial layout;
 *                type="alluvial" always uses it
 *
 * Layout:
 *   - Links whose value is not a positive number are not drawn. Self-links
 *     (source === target) and links that close a cycle (back-edges found by
 *     a depth-first search) are left out of the layout and the drawing and
 *     are listed in the accessible table, so cyclic data always terminates.
 *   - Sankey: a node's column is the longest path to it from a source node.
 *     Alluvial: columns come from each node's `time` field (sorted) or
 *     `group` field (first appearance); a link that does not run forward to
 *     a later column is left out like a back-edge.
 *   - One value-to-pixel scale serves every node and link: a node is as tall
 *     as the larger of its in- and outflow, and the ribbons leaving or
 *     entering it fill exactly that much of it.
 *   - Nodes are relaxed toward the weighted centre of their neighbours and
 *     de-overlapped; each node's ribbons are stacked in the order of the
 *     nodes at their far end, which keeps ribbons from crossing at a node.
 *
 * Accessibility: links and nodes are focusable marks with an aria-label; the
 * accessible table lists source, target and value for every link.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";


const NODE_WIDTH = 14;
const NODE_GAP = 10;
const MIN_NODE_SIZE = 2;
const MIN_LINK_WIDTH = 1;
const RELAX_ITERATIONS = 6;
const MARGIN = 8;
const HEADER_SIZE = 18;
const LABEL_FONT_SIZE = 11;
const CHAR_WIDTH = 6.2;


function _toKey(value) {
  /*
   * The map key of a node id; null and undefined have no key.
   */
  if (value === null || value === undefined) {
    return null;
  }
  return String(value);
}


function _linkValue(link) {
  /*
   * The drawable value of a link: a finite number above zero, else null.
   */
  const value = link !== null && typeof link === "object" ? link.value : null;
  if (typeof value !== "number" || Number.isFinite(value) === false || value <= 0) {
    return null;
  }
  return value;
}


function _truncate(text, maxWidth) {
  /*
   * Shorten a label to roughly maxWidth pixels with an ellipsis.
   */
  const maxChars = Math.max(Math.floor(maxWidth / CHAR_WIDTH), 1);
  if (text.length <= maxChars) {
    return text;
  }
  if (maxChars <= 1) {
    return "…";
  }
  return text.slice(0, maxChars - 1) + "…";
}


function _buildGraph(raw) {
  /*
   * Build the working graph from the raw data without changing it.
   *
   * :returns: { nodes: [node], byId: Map, links: [link], skipped: [link] }
   *     where every working link has { source, target, value, kind }.
   */
  const rawNodes = (raw && Array.isArray(raw.nodes)) ? raw.nodes : [];
  const rawLinks = (raw && Array.isArray(raw.links)) ? raw.links : [];

  const nodes = [];
  const byId = new Map();

  const addNode = (id, source) => {
    const node = {
      id: id,
      label: source !== null && source.label !== undefined && source.label !== null ?
        String(source.label) : id,
      group: source !== null && source.group !== undefined && source.group !== null ?
        String(source.group) : null,
      time: source !== null && source.time !== undefined && source.time !== null ?
        source.time : null,
      order: nodes.length,
      rank: 0,
      valueIn: 0,
      valueOut: 0,
      value: 0,
      size: 0,
      cross: 0,
      rankPos: 0,
      inLinks: [],
      outLinks: []
    };
    nodes.push(node);
    byId.set(id, node);
    return node;
  };

  for (let index = 0; index < rawNodes.length; index = index + 1) {
    const entry = rawNodes[index];
    if (entry === null || typeof entry !== "object") {
      continue;
    }
    const id = _toKey(entry.id);
    if (id === null || byId.has(id) === true) {
      continue;
    }
    addNode(id, entry);
  }

  const links = [];
  const skipped = [];
  for (let index = 0; index < rawLinks.length; index = index + 1) {
    const entry = rawLinks[index];
    if (entry === null || typeof entry !== "object") {
      continue;
    }
    const sourceId = _toKey(entry.source);
    const targetId = _toKey(entry.target);
    if (sourceId === null || targetId === null) {
      continue;
    }
    const value = _linkValue(entry);
    /*
     * Nodes named only by a drawable link are inferred; a link that is not
     * drawn only names its ends for the table.
     */
    const resolve = (id) => {
      if (byId.has(id) === true) {
        return byId.get(id);
      }
      if (value === null) {
        return { id: id, label: id };
      }
      return addNode(id, null);
    };
    const source = resolve(sourceId);
    const target = resolve(targetId);
    const link = {
      source: source,
      target: target,
      value: value !== null ? value : 0,
      rawValue: entry.value,
      kind: "flow",
      width: 0,
      sourceOffset: 0,
      targetOffset: 0
    };
    if (value === null) {
      link.kind = "invalid";
      skipped.push(link);
    } else if (source === target) {
      link.kind = "self";
      skipped.push(link);
    } else {
      links.push(link);
    }
  }

  return { nodes: nodes, byId: byId, links: links, skipped: skipped };
}


function _removeBackEdges(graph) {
  /*
   * Find the links that close a cycle with an iterative depth-first search
   * and move them from graph.links to graph.skipped (kind "cycle").
   * Sources (nodes without incoming links) are visited first so the edge
   * that is dropped is the one pointing back toward the start of the flow.
   */
  const outgoing = new Map();
  const inDegree = new Map();
  for (let index = 0; index < graph.nodes.length; index = index + 1) {
    outgoing.set(graph.nodes[index], []);
    inDegree.set(graph.nodes[index], 0);
  }
  for (let index = 0; index < graph.links.length; index = index + 1) {
    const link = graph.links[index];
    outgoing.get(link.source).push(link);
    inDegree.set(link.target, inDegree.get(link.target) + 1);
  }

  const starts = graph.nodes.filter((node) => inDegree.get(node) === 0);
  const rest = graph.nodes.filter((node) => inDegree.get(node) !== 0);
  const order = starts.concat(rest);

  /* 0 = unvisited, 1 = on the current path, 2 = finished */
  const state = new Map();
  const backEdges = new Set();

  for (let index = 0; index < order.length; index = index + 1) {
    const start = order[index];
    if (state.get(start) !== undefined) {
      continue;
    }
    const stack = [{ node: start, next: 0 }];
    state.set(start, 1);
    while (stack.length > 0) {
      const frame = stack[stack.length - 1];
      const edges = outgoing.get(frame.node);
      if (frame.next >= edges.length) {
        state.set(frame.node, 2);
        stack.pop();
        continue;
      }
      const link = edges[frame.next];
      frame.next = frame.next + 1;
      const targetState = state.get(link.target);
      if (targetState === 1) {
        backEdges.add(link);
      } else if (targetState === undefined) {
        state.set(link.target, 1);
        stack.push({ node: link.target, next: 0 });
      }
    }
  }

  if (backEdges.size > 0) {
    const kept = [];
    for (let index = 0; index < graph.links.length; index = index + 1) {
      const link = graph.links[index];
      if (backEdges.has(link) === true) {
        link.kind = "cycle";
        graph.skipped.push(link);
      } else {
        kept.push(link);
      }
    }
    graph.links = kept;
  }
}


function _assignRanksByTopology(graph) {
  /*
   * Longest-path ranks over the acyclic link set (Kahn's algorithm).
   *
   * :returns: The number of columns.
   */
  const inDegree = new Map();
  const outgoing = new Map();
  for (let index = 0; index < graph.nodes.length; index = index + 1) {
    inDegree.set(graph.nodes[index], 0);
    outgoing.set(graph.nodes[index], []);
    graph.nodes[index].rank = 0;
  }
  for (let index = 0; index < graph.links.length; index = index + 1) {
    const link = graph.links[index];
    inDegree.set(link.target, inDegree.get(link.target) + 1);
    outgoing.get(link.source).push(link);
  }

  const queue = graph.nodes.filter((node) => inDegree.get(node) === 0);
  let head = 0;
  let maxRank = 0;
  while (head < queue.length) {
    const node = queue[head];
    head = head + 1;
    const edges = outgoing.get(node);
    for (let index = 0; index < edges.length; index = index + 1) {
      const target = edges[index].target;
      if (target.rank < node.rank + 1) {
        target.rank = node.rank + 1;
      }
      inDegree.set(target, inDegree.get(target) - 1);
      if (inDegree.get(target) === 0) {
        queue.push(target);
      }
    }
    if (node.rank > maxRank) {
      maxRank = node.rank;
    }
  }
  return maxRank + 1;
}


function _assignRanksByColumnKey(graph) {
  /*
   * Alluvial columns: from `time` (sorted) when every node carries one,
   * else from `group` in order of first appearance. Nodes without a key
   * share one extra column at the end. Links that do not run forward are
   * moved to graph.skipped (kind "cycle").
   *
   * :returns: { count, headers } -- the number of columns and their labels;
   *     null when no node carries a column key (topology is used instead).
   */
  const useTime = graph.nodes.length > 0 &&
    graph.nodes.every((node) => node.time !== null);
  const hasGroup = graph.nodes.some((node) => node.group !== null);
  if (useTime === false && hasGroup === false) {
    return null;
  }

  const keys = [];
  const seen = new Set();
  for (let index = 0; index < graph.nodes.length; index = index + 1) {
    const node = graph.nodes[index];
    const key = useTime === true ? node.time : node.group;
    if (key !== null && seen.has(String(key)) === false) {
      seen.add(String(key));
      keys.push(key);
    }
  }

  if (useTime === true) {
    const numeric = keys.every((key) => typeof key === "number");
    keys.sort((left, right) => {
      if (numeric === true) {
        return left - right;
      }
      return String(left).localeCompare(String(right), undefined, { numeric: true });
    });
  }

  const columnOf = new Map();
  for (let index = 0; index < keys.length; index = index + 1) {
    columnOf.set(String(keys[index]), index);
  }
  const headers = keys.map((key) => String(key));
  let count = keys.length;
  let ungrouped = false;
  for (let index = 0; index < graph.nodes.length; index = index + 1) {
    const node = graph.nodes[index];
    const key = useTime === true ? node.time : node.group;
    if (key === null) {
      node.rank = keys.length;
      ungrouped = true;
    } else {
      node.rank = columnOf.get(String(key));
    }
  }
  if (ungrouped === true) {
    count = count + 1;
    headers.push("");
  }

  const kept = [];
  for (let index = 0; index < graph.links.length; index = index + 1) {
    const link = graph.links[index];
    if (link.target.rank > link.source.rank) {
      kept.push(link);
    } else {
      link.kind = "cycle";
      graph.skipped.push(link);
    }
  }
  graph.links = kept;

  return { count: count, headers: headers };
}


function _accumulateValues(graph) {
  /*
   * Sum the in- and outflow of every node over the drawn links.
   */
  for (let index = 0; index < graph.links.length; index = index + 1) {
    const link = graph.links[index];
    link.source.valueOut = link.source.valueOut + link.value;
    link.target.valueIn = link.target.valueIn + link.value;
    link.source.outLinks.push(link);
    link.target.inLinks.push(link);
  }
  for (let index = 0; index < graph.nodes.length; index = index + 1) {
    const node = graph.nodes[index];
    node.value = Math.max(node.valueIn, node.valueOut);
  }
}


function _center(node) {
  /*
   * Cross-axis centre of a node.
   */
  return node.cross + node.size / 2;
}


function _resolveCollisions(column, extent, gap) {
  /*
   * Sort a column by position and push its nodes apart so they keep `gap`
   * between them and stay within [0, extent].
   */
  column.sort((left, right) => left.cross - right.cross);

  let cursor = 0;
  for (let index = 0; index < column.length; index = index + 1) {
    const node = column[index];
    if (node.cross < cursor) {
      node.cross = cursor;
    }
    cursor = node.cross + node.size + gap;
  }

  cursor = extent;
  for (let index = column.length - 1; index >= 0; index = index - 1) {
    const node = column[index];
    if (node.cross + node.size > cursor) {
      node.cross = cursor - node.size;
    }
    cursor = node.cross - gap;
  }

  /* A column that is exactly full may have been pushed above 0: restack. */
  if (column.length > 0 && column[0].cross < 0) {
    let restack = 0;
    for (let index = 0; index < column.length; index = index + 1) {
      column[index].cross = restack;
      restack = restack + column[index].size + gap;
    }
  }
}


function _layout(graph, columnCount, rankExtent, crossExtent) {
  /*
   * Place nodes and size nodes and links with one value-to-pixel scale.
   *
   * :returns: The columns as arrays of nodes.
   */
  const columns = [];
  for (let index = 0; index < columnCount; index = index + 1) {
    columns.push([]);
  }
  for (let index = 0; index < graph.nodes.length; index = index + 1) {
    const node = graph.nodes[index];
    columns[node.rank].push(node);
  }

  let maxCount = 1;
  for (let index = 0; index < columns.length; index = index + 1) {
    maxCount = Math.max(maxCount, columns[index].length);
  }
  const gap = maxCount > 1 ? Math.min(NODE_GAP, (crossExtent * 0.4) / (maxCount - 1)) : 0;

  /* The one global scale: the fullest column fills the cross extent. */
  let scale = Infinity;
  for (let index = 0; index < columns.length; index = index + 1) {
    const column = columns[index];
    if (column.length === 0) {
      continue;
    }
    let total = 0;
    let empties = 0;
    for (let n = 0; n < column.length; n = n + 1) {
      total = total + column[n].value;
      if (column[n].value <= 0) {
        empties = empties + 1;
      }
    }
    const available = crossExtent - gap * (column.length - 1) - empties * MIN_NODE_SIZE;
    if (total > 0) {
      scale = Math.min(scale, Math.max(available, 0) / total);
    }
  }
  if (Number.isFinite(scale) === false) {
    scale = 0;
  }

  for (let index = 0; index < graph.nodes.length; index = index + 1) {
    const node = graph.nodes[index];
    node.size = node.value > 0 ? node.value * scale : MIN_NODE_SIZE;
  }
  for (let index = 0; index < graph.links.length; index = index + 1) {
    const link = graph.links[index];
    link.width = link.value * scale;
  }

  /* Column positions along the rank axis. */
  const step = columnCount > 1 ? (rankExtent - NODE_WIDTH) / (columnCount - 1) : 0;
  for (let index = 0; index < graph.nodes.length; index = index + 1) {
    const node = graph.nodes[index];
    node.rankPos = columnCount > 1 ? node.rank * step : (rankExtent - NODE_WIDTH) / 2;
  }

  /* Initial cross positions: stacked in data order, centred. */
  for (let index = 0; index < columns.length; index = index + 1) {
    const column = columns[index];
    let total = 0;
    for (let n = 0; n < column.length; n = n + 1) {
      total = total + column[n].size;
    }
    total = total + gap * Math.max(column.length - 1, 0);
    let cursor = Math.max((crossExtent - total) / 2, 0);
    for (let n = 0; n < column.length; n = n + 1) {
      column[n].cross = cursor;
      cursor = cursor + column[n].size + gap;
    }
  }

  /* Relax toward the weighted centre of the neighbours, both directions. */
  for (let iteration = 0; iteration < RELAX_ITERATIONS; iteration = iteration + 1) {
    const alpha = Math.pow(0.9, iteration);
    const forward = iteration % 2 === 0;
    for (let c = 0; c < columns.length; c = c + 1) {
      const columnIndex = forward === true ? c : columns.length - 1 - c;
      const column = columns[columnIndex];
      for (let n = 0; n < column.length; n = n + 1) {
        const node = column[n];
        const neighbours = forward === true ? node.inLinks : node.outLinks;
        let weight = 0;
        let sum = 0;
        for (let k = 0; k < neighbours.length; k = k + 1) {
          const link = neighbours[k];
          const other = forward === true ? link.source : link.target;
          sum = sum + _center(other) * link.value;
          weight = weight + link.value;
        }
        if (weight > 0) {
          node.cross = node.cross + (sum / weight - _center(node)) * alpha;
        }
      }
      _resolveCollisions(column, crossExtent, gap);
    }
  }

  /* Stack each node's ribbons in the order of their far ends. */
  for (let index = 0; index < graph.nodes.length; index = index + 1) {
    const node = graph.nodes[index];
    node.outLinks.sort((left, right) => _center(left.target) - _center(right.target));
    node.inLinks.sort((left, right) => _center(left.source) - _center(right.source));
    let offset = 0;
    for (let k = 0; k < node.outLinks.length; k = k + 1) {
      node.outLinks[k].sourceOffset = offset;
      offset = offset + node.outLinks[k].width;
    }
    offset = 0;
    for (let k = 0; k < node.inLinks.length; k = k + 1) {
      node.inLinks[k].targetOffset = offset;
      offset = offset + node.inLinks[k].width;
    }
  }

  return columns;
}


function _buildRibbonPath(sourceRank, targetRank, s0, s1, t0, t1, horizontal) {
  /*
   * Build a filled Sankey ribbon: two cubic Bézier edges between the
   * source span [s0, s1] and the target span [t0, t1] on the cross axis.
   * A filled band keeps its shape when it is wider than it is long, which
   * a thick stroke along a centre line does not.
   */
  const mid = (sourceRank + targetRank) / 2;
  const point = (rank, cross) => {
    const text = horizontal === true ?
      `${rank.toFixed(2)},${cross.toFixed(2)}` : `${cross.toFixed(2)},${rank.toFixed(2)}`;
    return text;
  };
  const data = `M${point(sourceRank, s0)} ` +
    `C${point(mid, s0)} ${point(mid, t0)} ${point(targetRank, t0)} ` +
    `L${point(targetRank, t1)} ` +
    `C${point(mid, t1)} ${point(mid, s1)} ${point(sourceRank, s1)} Z`;
  return data;
}


function _buildTable(graph) {
  /*
   * The accessible table: one row per link, drawn or not.
   */
  const notes = { self: "self-link, not drawn", cycle: "closes a cycle, not drawn",
    invalid: "no positive value, not drawn" };
  const all = graph.links.concat(graph.skipped);
  const hasSkipped = graph.skipped.length > 0;
  const columns = hasSkipped === true ? ["Source", "Target", "Value", "Note"] :
    ["Source", "Target", "Value"];
  const rows = [];
  for (let index = 0; index < all.length; index = index + 1) {
    const link = all[index];
    const value = typeof link.rawValue === "number" && Number.isFinite(link.rawValue) === true ?
      link.rawValue : "";
    const row = [link.source.label, link.target.label, value];
    if (hasSkipped === true) {
      row.push(link.kind === "flow" ? "" : notes[link.kind]);
    }
    rows.push(row);
  }
  return { columns: columns, rows: rows, caption: "Flows (source, target, value)" };
}


function _isEmpty(model) {
  /*
   * Nothing to draw: no link with a positive value between two nodes.
   */
  const raw = model !== null && model !== undefined ? model.raw : null;
  const links = (raw && Array.isArray(raw.links)) ? raw.links : [];
  const drawable = links.some((link) => {
    return _linkValue(link) !== null && _toKey(link.source) !== null &&
      _toKey(link.target) !== null && _toKey(link.source) !== _toKey(link.target);
  });
  return drawable === false;
}


function _activate(element, handler) {
  /*
   * Wire click and Enter / Space to a mark's handler.
   */
  element.addEventListener("click", handler);
  element.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      handler();
    }
  });
}


export function render(ctx) {
  /*
   * Render a Sankey or Alluvial diagram.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw;
  const horizontal = ctx.orientation !== "vertical";
  const isAlluvial = ctx.type === "alluvial" || ctx.attrs("mode", "sankey") === "alluvial";

  const root = svgEl("g", { part: "plot" }, []);

  const graph = _buildGraph(raw);
  if (graph.nodes.length === 0) {
    return root;
  }

  let columnCount = 0;
  let headers = null;
  if (isAlluvial === true) {
    const columnInfo = _assignRanksByColumnKey(graph);
    if (columnInfo !== null) {
      columnCount = columnInfo.count;
      headers = columnInfo.headers;
    }
  }
  /* Break cycles before ranking so a cyclic graph always terminates. */
  _removeBackEdges(graph);
  if (headers === null) {
    columnCount = _assignRanksByTopology(graph);
  }
  _accumulateValues(graph);

  ctx.setTable(_buildTable(graph));

  const top = MARGIN + (headers !== null && horizontal === true ? HEADER_SIZE : 0);
  const left = MARGIN + (headers !== null && horizontal === false ? HEADER_SIZE * 3 : 0);
  const plotW = Math.max(ctx.width - left - MARGIN, 10);
  const plotH = Math.max(ctx.height - top - MARGIN, 10);
  const rankExtent = horizontal === true ? plotW : plotH;
  const crossExtent = horizontal === true ? plotH : plotW;

  const columns = _layout(graph, columnCount, rankExtent, crossExtent);

  const plot = svgEl("g", { transform: `translate(${left},${top})` }, []);
  root.appendChild(plot);

  const linkLayer = svgEl("g", { part: "links" }, []);
  const nodeLayer = svgEl("g", { part: "nodes" }, []);
  const labelLayer = svgEl("g", { "aria-hidden": "true", "pointer-events": "none" }, []);
  plot.appendChild(linkLayer);
  plot.appendChild(nodeLayer);
  plot.appendChild(labelLayer);

  /* Ask for the node colours in data order so each node keeps its slot. */
  for (let index = 0; index < graph.nodes.length; index = index + 1) {
    ctx.colorFor(graph.nodes[index].id);
  }

  /* Links (behind the nodes). */
  for (let index = 0; index < graph.links.length; index = index + 1) {
    const link = graph.links[index];
    const src = link.source;
    const tgt = link.target;
    const drawWidth = Math.max(link.width, MIN_LINK_WIDTH);
    const sourceStart = src.cross + link.sourceOffset;
    const targetStart = tgt.cross + link.targetOffset;
    const pathData = _buildRibbonPath(src.rankPos + NODE_WIDTH, tgt.rankPos,
      sourceStart, sourceStart + drawWidth, targetStart, targetStart + drawWidth, horizontal);

    const text = `${src.label} → ${tgt.label}: ${formatNumber(link.value)}`;
    const path = svgEl("path", {
      d: pathData,
      fill: ctx.colorFor(src.id),
      "fill-opacity": "0.45",
      part: "link",
      tabindex: "0",
      role: "img",
      "aria-label": text
    }, [svgEl("title", null, text)]);

    _activate(path, () => {
      ctx.emit("mj-chart-link-click", {
        source: src.id,
        target: tgt.id,
        value: link.value
      });
    });
    linkLayer.appendChild(path);
  }

  /* Label room: the gap between two columns, less the node bar. */
  const step = columnCount > 1 ? (rankExtent - NODE_WIDTH) / (columnCount - 1) : rankExtent;
  const labelRoom = horizontal === true ?
    Math.max(step - NODE_WIDTH - 10, 24) : Math.max(crossExtent, 24);

  for (let c = 0; c < columns.length; c = c + 1) {
    const column = columns[c];
    for (let n = 0; n < column.length; n = n + 1) {
      const node = column[n];
      const color = ctx.colorFor(node.id);

      let rectX = 0;
      let rectY = 0;
      let rectW = 0;
      let rectH = 0;
      if (horizontal === true) {
        rectX = node.rankPos;
        rectY = node.cross;
        rectW = NODE_WIDTH;
        rectH = node.size;
      } else {
        rectX = node.cross;
        rectY = node.rankPos;
        rectW = node.size;
        rectH = NODE_WIDTH;
      }

      const text = `${node.label}: in ${formatNumber(node.valueIn)}, out ${formatNumber(node.valueOut)}`;
      const rect = svgEl("rect", {
        x: rectX.toFixed(2),
        y: rectY.toFixed(2),
        width: Math.max(rectW, MIN_NODE_SIZE).toFixed(2),
        height: Math.max(rectH, MIN_NODE_SIZE).toFixed(2),
        rx: 2,
        fill: color,
        part: "node",
        tabindex: "0",
        role: "img",
        "aria-label": text
      }, [svgEl("title", null, text)]);

      _activate(rect, () => {
        ctx.emit("mj-chart-node-click", {
          id: node.id,
          label: node.label
        });
      });
      nodeLayer.appendChild(rect);

      /* Node label beside the bar (inside the plot), with a halo. */
      let labelX = 0;
      let labelY = 0;
      let anchor = "start";
      let baseline = "middle";
      if (horizontal === true) {
        labelX = node.rankPos + NODE_WIDTH + 4;
        labelY = node.cross + node.size / 2;
        if (columnCount > 1 && node.rank === columnCount - 1) {
          labelX = node.rankPos - 4;
          anchor = "end";
        }
      } else {
        labelX = node.cross + node.size / 2;
        anchor = "middle";
        if (node.rank === columnCount - 1 && columnCount > 1) {
          labelY = node.rankPos - 3;
          baseline = "auto";
        } else {
          labelY = node.rankPos + NODE_WIDTH + 3;
          baseline = "hanging";
        }
      }
      const room = horizontal === true ? labelRoom : Math.max(node.size + NODE_GAP, 24);
      labelLayer.appendChild(svgEl("text", {
        x: labelX.toFixed(2),
        y: labelY.toFixed(2),
        "text-anchor": anchor,
        "dominant-baseline": baseline,
        "font-size": LABEL_FONT_SIZE,
        fill: "var(--mj-text, #14181f)",
        stroke: "var(--mj-surface, #ffffff)",
        "stroke-width": 3,
        "stroke-linejoin": "round",
        "paint-order": "stroke"
      }, _truncate(node.label, room)));
    }
  }

  /* Alluvial column headers. */
  if (headers !== null) {
    for (let c = 0; c < headers.length; c = c + 1) {
      if (headers[c] === "") {
        continue;
      }
      const pos = columnCount > 1 ? c * step : (rankExtent - NODE_WIDTH) / 2;
      let attrs = null;
      if (horizontal === true) {
        let anchor = "middle";
        let x = pos + NODE_WIDTH / 2;
        if (c === 0) {
          anchor = "start";
          x = pos;
        } else if (c === headers.length - 1) {
          anchor = "end";
          x = pos + NODE_WIDTH;
        }
        attrs = { x: x.toFixed(2), y: -6, "text-anchor": anchor };
      } else {
        attrs = { x: -6, y: (pos + NODE_WIDTH / 2).toFixed(2), "text-anchor": "end",
          "dominant-baseline": "middle" };
      }
      attrs["font-size"] = LABEL_FONT_SIZE;
      attrs["font-weight"] = "600";
      attrs.fill = "var(--mj-text-muted, #6b7280)";
      const headerRoom = horizontal === true ? Math.max(step, 24) : HEADER_SIZE * 3 - 8;
      labelLayer.appendChild(svgEl("text", attrs, _truncate(headers[c], headerRoom)));
    }
  }

  return root;
}


const OPTIONS = { orientation: "horizontal", legend: "none", isEmpty: _isEmpty };

registerRenderer("sankey", render, OPTIONS);
registerRenderer("alluvial", render, OPTIONS);
