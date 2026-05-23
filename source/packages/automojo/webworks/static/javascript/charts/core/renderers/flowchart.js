/*
 * flowchart.js
 *
 * Flowchart / Decision-flow renderer.
 *
 * Registers: "flowchart", "decision-flow"
 *
 * ctx.raw shape:
 *   nodes: [{ id, label, shape }]   shape: "rect" | "diamond" | "oval"
 *   links: [{ source, target, value, label? }]
 *
 * Layout:
 *   - Assigns ranks via BFS (Sugiyama-style layering), with cycle detection
 *     — back-edges are reversed to break cycles.
 *   - Nodes within a rank are spaced evenly along the cross-axis.
 *   - Edges are drawn as orthogonal connectors (elbow routing) with arrowheads.
 *
 * Orientation: "vertical" (top-to-bottom, default) / "horizontal" (left-to-right).
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml } from "../svgdraw.js";


const NODE_W = 110;
const NODE_H = 44;
const DIAMOND_SIZE = 52;
const OVAL_RX = 22;
const RANK_GAP = 72;
const NODE_GAP = 24;
const MARGIN = { top: 24, right: 24, bottom: 24, left: 24 };
const ARROW_SIZE = 8;


function _buildAdjacency(nodes, links) {
  /*
   * Build adjacency list and in-degree map.
   */
  const ids = nodes.map((n) => n.id);
  const outEdges = {};
  const inEdges = {};
  for (let i = 0; i < ids.length; i = i + 1) {
    outEdges[ids[i]] = [];
    inEdges[ids[i]] = [];
  }
  for (let k = 0; k < links.length; k = k + 1) {
    const link = links[k];
    if (outEdges[link.source] !== undefined && inEdges[link.target] !== undefined) {
      outEdges[link.source].push(link.target);
      inEdges[link.target].push(link.source);
    }
  }
  return { outEdges: outEdges, inEdges: inEdges };
}


function _assignRanks(nodes, links) {
  /*
   * BFS-based rank assignment; back edges (cycle detection via DFS) are
   * skipped so the layout remains acyclic. Returns a map id -> rank.
   */
  const ids = nodes.map((n) => n.id);
  const { outEdges } = _buildAdjacency(nodes, links);

  /* DFS to mark back-edges. */
  const visited = {};
  const inStack = {};
  const backEdges = new Set();

  const dfs = (node) => {
    visited[node] = true;
    inStack[node] = true;
    const neighbors = outEdges[node] || [];
    for (let n = 0; n < neighbors.length; n = n + 1) {
      const neighbor = neighbors[n];
      if (inStack[neighbor] === true) {
        backEdges.add(`${node}→${neighbor}`);
      } else if (visited[neighbor] !== true) {
        dfs(neighbor);
      }
    }
    inStack[node] = false;
  };
  for (let i = 0; i < ids.length; i = i + 1) {
    if (visited[ids[i]] !== true) {
      dfs(ids[i]);
    }
  }

  /* BFS rank assignment, ignoring back-edges. */
  const rank = {};
  const inDegree = {};
  for (let i = 0; i < ids.length; i = i + 1) {
    inDegree[ids[i]] = 0;
  }
  for (let k = 0; k < links.length; k = k + 1) {
    const link = links[k];
    const edgeKey = `${link.source}→${link.target}`;
    if (backEdges.has(edgeKey) === false &&
        inDegree[link.target] !== undefined) {
      inDegree[link.target] = inDegree[link.target] + 1;
    }
  }

  const queue = [];
  for (let i = 0; i < ids.length; i = i + 1) {
    if (inDegree[ids[i]] === 0) {
      rank[ids[i]] = 0;
      queue.push(ids[i]);
    }
  }
  if (queue.length === 0 && ids.length > 0) {
    rank[ids[0]] = 0;
    queue.push(ids[0]);
  }

  let head = 0;
  while (head < queue.length) {
    const current = queue[head];
    head = head + 1;
    const neighbors = outEdges[current] || [];
    for (let n = 0; n < neighbors.length; n = n + 1) {
      const neighbor = neighbors[n];
      const edgeKey = `${current}→${neighbor}`;
      if (backEdges.has(edgeKey) === true) {
        continue;
      }
      const candidateRank = rank[current] + 1;
      if (rank[neighbor] === undefined || rank[neighbor] < candidateRank) {
        rank[neighbor] = candidateRank;
        queue.push(neighbor);
      }
    }
  }
  for (let i = 0; i < ids.length; i = i + 1) {
    if (rank[ids[i]] === undefined) {
      rank[ids[i]] = 0;
    }
  }
  return { rank: rank, backEdges: backEdges };
}


function _groupByRank(nodes, rank) {
  /*
   * Collect node ids grouped by rank.
   */
  let maxRank = 0;
  const ids = nodes.map((n) => n.id);
  for (let i = 0; i < ids.length; i = i + 1) {
    if (rank[ids[i]] > maxRank) {
      maxRank = rank[ids[i]];
    }
  }
  const columns = [];
  for (let r = 0; r <= maxRank; r = r + 1) {
    columns.push([]);
  }
  for (let i = 0; i < ids.length; i = i + 1) {
    columns[rank[ids[i]]].push(ids[i]);
  }
  return columns;
}


function _computePositions(nodeMap, columns, plotW, plotH, horizontal) {
  /*
   * Assign pixel cx/cy to each node.
   */
  const numRanks = columns.length;
  for (let r = 0; r < columns.length; r = r + 1) {
    const column = columns[r];
    const n = column.length;
    const rankPos = numRanks > 1
      ? (r / (numRanks - 1)) * (horizontal ? plotW : plotH)
      : (horizontal ? plotW : plotH) / 2;

    const crossSpan = horizontal ? plotH : plotW;
    for (let c = 0; c < n; c = c + 1) {
      const crossPos = n > 1
        ? (c / (n - 1)) * (crossSpan - NODE_GAP * 2) + NODE_GAP
        : crossSpan / 2;

      const node = nodeMap[column[c]];
      if (horizontal === true) {
        node.cx = rankPos;
        node.cy = crossPos;
      } else {
        node.cx = crossPos;
        node.cy = rankPos;
      }
    }
  }
}


function _drawNode(node, color) {
  /*
   * Draw a single node shape. Returns a <g> containing the shape and label.
   */
  const g = svgEl("g", {
    part: "node",
    tabindex: "0",
    role: "img",
    "aria-label": escapeHtml(node.label)
  }, []);

  let shape = null;
  const shape_type = node.shape || "rect";

  if (shape_type === "diamond") {
    const s = DIAMOND_SIZE / 2;
    const pts = `${node.cx},${node.cy - s} ${node.cx + s},${node.cy} ` +
      `${node.cx},${node.cy + s} ${node.cx - s},${node.cy}`;
    shape = svgEl("polygon", {
      points: pts,
      fill: color,
      "fill-opacity": "0.15",
      stroke: color,
      "stroke-width": 2,
      rx: 2
    }, []);
  } else if (shape_type === "oval") {
    shape = svgEl("ellipse", {
      cx: node.cx.toFixed(2),
      cy: node.cy.toFixed(2),
      rx: OVAL_RX,
      ry: NODE_H / 2,
      fill: color,
      "fill-opacity": "0.15",
      stroke: color,
      "stroke-width": 2
    }, []);
  } else {
    shape = svgEl("rect", {
      x: (node.cx - NODE_W / 2).toFixed(2),
      y: (node.cy - NODE_H / 2).toFixed(2),
      width: NODE_W,
      height: NODE_H,
      rx: 4,
      fill: color,
      "fill-opacity": "0.15",
      stroke: color,
      "stroke-width": 2
    }, []);
  }

  shape.appendChild(svgEl("title", null, escapeHtml(node.label)));
  g.appendChild(shape);

  g.appendChild(svgEl("text", {
    x: node.cx.toFixed(2),
    y: node.cy.toFixed(2),
    "text-anchor": "middle",
    "dominant-baseline": "middle",
    "font-size": 11,
    fill: "var(--mj-text, #14181f)"
  }, escapeHtml(node.label)));

  return g;
}


function _nodeEdgePoint(node, toNode) {
  /*
   * Compute the nearest border point of a node toward toNode.
   */
  const shape = node.shape || "rect";
  const dx = toNode.cx - node.cx;
  const dy = toNode.cy - node.cy;
  const angle = Math.atan2(dy, dx);

  let hw, hh;
  if (shape === "diamond") {
    hw = DIAMOND_SIZE / 2;
    hh = DIAMOND_SIZE / 2;
  } else if (shape === "oval") {
    hw = OVAL_RX;
    hh = NODE_H / 2;
  } else {
    hw = NODE_W / 2;
    hh = NODE_H / 2;
  }

  const absAngle = Math.abs(angle);
  let edgeX, edgeY;
  if (absAngle <= Math.atan2(hh, hw)) {
    edgeX = node.cx + hw * Math.sign(dx);
    edgeY = node.cy + hw * Math.abs(Math.tan(angle)) * Math.sign(dy);
  } else {
    edgeX = node.cx + hh * (1 / Math.abs(Math.tan(angle))) * Math.sign(dx);
    edgeY = node.cy + hh * Math.sign(dy);
  }
  return { x: edgeX, y: edgeY };
}


function _arrowheadPath(tx, ty, angle) {
  /*
   * Build an arrowhead polygon path at (tx,ty) pointing in direction `angle`.
   */
  const a1 = angle + Math.PI * 0.8;
  const a2 = angle - Math.PI * 0.8;
  const x1 = tx + ARROW_SIZE * Math.cos(a1);
  const y1 = ty + ARROW_SIZE * Math.sin(a1);
  const x2 = tx + ARROW_SIZE * Math.cos(a2);
  const y2 = ty + ARROW_SIZE * Math.sin(a2);
  return `${tx.toFixed(2)},${ty.toFixed(2)} ${x1.toFixed(2)},${y1.toFixed(2)} ${x2.toFixed(2)},${y2.toFixed(2)}`;
}


export function render(ctx) {
  /*
   * Render a flowchart or decision-flow diagram.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw;
  const horizontal = ctx.orientation === "horizontal";
  const root = svgEl("g", { part: "plot" }, []);

  const nodes = (raw && Array.isArray(raw.nodes)) ? raw.nodes : [];
  const links = (raw && Array.isArray(raw.links)) ? raw.links : [];

  if (nodes.length === 0) {
    return root;
  }

  const plotW = Math.max(ctx.width - MARGIN.left - MARGIN.right, 10);
  const plotH = Math.max(ctx.height - MARGIN.top - MARGIN.bottom, 10);

  /* Build node map. */
  const nodeMap = {};
  for (let i = 0; i < nodes.length; i = i + 1) {
    const n = nodes[i];
    nodeMap[n.id] = {
      id: n.id,
      label: n.label !== undefined ? n.label : n.id,
      shape: n.shape || "rect",
      cx: 0,
      cy: 0
    };
  }

  const { rank, backEdges } = _assignRanks(nodes, links);
  const columns = _groupByRank(nodes, rank);
  _computePositions(nodeMap, columns, plotW, plotH, horizontal);

  const plot = svgEl("g", { transform: `translate(${MARGIN.left},${MARGIN.top})` }, []);
  root.appendChild(plot);

  /* Draw edges first (behind nodes). */
  for (let k = 0; k < links.length; k = k + 1) {
    const link = links[k];
    const src = nodeMap[link.source];
    const tgt = nodeMap[link.target];
    if (src === undefined || tgt === undefined) {
      continue;
    }

    const ep = _nodeEdgePoint(src, tgt);
    const tp = _nodeEdgePoint(tgt, src);
    const angle = Math.atan2(tp.y - ep.y, tp.x - ep.x);

    const isBack = backEdges.has(`${link.source}→${link.target}`);
    const strokeColor = isBack
      ? "var(--mj-color-warning, #b45309)"
      : "var(--mj-border-strong, #c7ccd6)";

    const edgeGroup = svgEl("g", { part: "edge" }, []);

    /* Orthogonal elbow connector. */
    let pathD;
    if (horizontal === true) {
      const midX = (ep.x + tp.x) / 2;
      pathD = `M${ep.x.toFixed(2)},${ep.y.toFixed(2)} ` +
        `L${midX.toFixed(2)},${ep.y.toFixed(2)} ` +
        `L${midX.toFixed(2)},${tp.y.toFixed(2)} ` +
        `L${tp.x.toFixed(2)},${tp.y.toFixed(2)}`;
    } else {
      const midY = (ep.y + tp.y) / 2;
      pathD = `M${ep.x.toFixed(2)},${ep.y.toFixed(2)} ` +
        `L${ep.x.toFixed(2)},${midY.toFixed(2)} ` +
        `L${tp.x.toFixed(2)},${midY.toFixed(2)} ` +
        `L${tp.x.toFixed(2)},${tp.y.toFixed(2)}`;
    }

    edgeGroup.appendChild(svgEl("path", {
      d: pathD,
      fill: "none",
      stroke: strokeColor,
      "stroke-width": 1.5
    }, []));

    /* Arrowhead. */
    const arrowPts = _arrowheadPath(tp.x, tp.y, angle);
    edgeGroup.appendChild(svgEl("polygon", {
      points: arrowPts,
      fill: strokeColor
    }, []));

    /* Edge label. */
    if (link.label) {
      const lx = (ep.x + tp.x) / 2;
      const ly = (ep.y + tp.y) / 2 - 6;
      edgeGroup.appendChild(svgEl("text", {
        x: lx.toFixed(2),
        y: ly.toFixed(2),
        "text-anchor": "middle",
        "font-size": 10,
        fill: "var(--mj-text-muted, #6b7280)"
      }, escapeHtml(link.label)));
    }

    const capturedLink = link;
    const clickHandler = () => {
      ctx.emit("mj-chart-edge-click", {
        source: capturedLink.source,
        target: capturedLink.target,
        label: capturedLink.label || null
      });
    };
    edgeGroup.addEventListener("click", clickHandler);
    plot.appendChild(edgeGroup);
  }

  /* Draw nodes on top. */
  const nodeIds = Object.keys(nodeMap);
  for (let i = 0; i < nodeIds.length; i = i + 1) {
    const node = nodeMap[nodeIds[i]];
    const color = ctx.colorFor(i);
    const nodeGroup = _drawNode(node, color);

    const capturedNode = node;
    const nodeClickHandler = () => {
      ctx.emit("mj-chart-node-click", {
        id: capturedNode.id,
        label: capturedNode.label
      });
    };
    nodeGroup.addEventListener("click", nodeClickHandler);
    nodeGroup.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        nodeClickHandler();
      }
    });
    plot.appendChild(nodeGroup);
  }

  return root;
}


registerRenderer("flowchart", render);
registerRenderer("decision-flow", render);
