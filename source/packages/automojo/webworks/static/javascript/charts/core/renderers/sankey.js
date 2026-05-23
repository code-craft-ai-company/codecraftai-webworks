/*
 * sankey.js
 *
 * Sankey / Alluvial renderer.
 *
 * Registers: "sankey", "alluvial"
 *
 * ctx.raw shape:
 *   nodes: [{ id, label?, group? }]
 *   links: [{ source, target, value }]
 *
 * Layout:
 *   - Compute node ranks from link topology (BFS from sources).
 *   - In alluvial mode, ranks come from the node `group` field instead.
 *   - Distribute nodes vertically within each rank column.
 *   - Draw node rectangles and cubic-Bézier link ribbons whose stroke-width
 *     encodes the link value.
 *
 * Orientation: horizontal (columns left→right, default) / vertical
 *   (columns top→bottom).
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber } from "../svgdraw.js";
import { linearScale } from "../scales.js";


const NODE_WIDTH = 16;
const NODE_GAP = 8;
const MARGIN = { top: 24, right: 24, bottom: 24, left: 24 };


function _buildNodeMap(nodes) {
  /*
   * Build a map from node id to a working node object.
   */
  const map = {};
  for (let index = 0; index < nodes.length; index = index + 1) {
    const node = nodes[index];
    map[node.id] = {
      id: node.id,
      label: node.label !== undefined ? node.label : node.id,
      group: node.group !== undefined ? node.group : null,
      rank: -1,
      x: 0,
      y: 0,
      height: 0,
      valueIn: 0,
      valueOut: 0,
      offsetIn: 0,
      offsetOut: 0
    };
  }
  return map;
}


function _assignRanksBFS(nodeMap, links) {
  /*
   * Assign column ranks via BFS from source nodes (those with no incoming
   * links). Returns the maximum rank found.
   */
  const inDegree = {};
  const ids = Object.keys(nodeMap);
  for (let i = 0; i < ids.length; i = i + 1) {
    inDegree[ids[i]] = 0;
  }
  for (let i = 0; i < links.length; i = i + 1) {
    const link = links[i];
    if (nodeMap[link.target] !== undefined) {
      inDegree[link.target] = (inDegree[link.target] || 0) + 1;
    }
  }

  const queue = [];
  for (let i = 0; i < ids.length; i = i + 1) {
    if (inDegree[ids[i]] === 0) {
      nodeMap[ids[i]].rank = 0;
      queue.push(ids[i]);
    }
  }
  if (queue.length === 0 && ids.length > 0) {
    nodeMap[ids[0]].rank = 0;
    queue.push(ids[0]);
  }

  const adjacency = {};
  for (let i = 0; i < ids.length; i = i + 1) {
    adjacency[ids[i]] = [];
  }
  for (let i = 0; i < links.length; i = i + 1) {
    const link = links[i];
    if (adjacency[link.source] !== undefined) {
      adjacency[link.source].push(link.target);
    }
  }

  let head = 0;
  while (head < queue.length) {
    const current = queue[head];
    head = head + 1;
    const neighbors = adjacency[current];
    for (let n = 0; n < neighbors.length; n = n + 1) {
      const neighbor = neighbors[n];
      const candidateRank = nodeMap[current].rank + 1;
      if (nodeMap[neighbor] !== undefined &&
          nodeMap[neighbor].rank < candidateRank) {
        nodeMap[neighbor].rank = candidateRank;
        queue.push(neighbor);
      }
    }
  }

  let maxRank = 0;
  for (let i = 0; i < ids.length; i = i + 1) {
    if (nodeMap[ids[i]].rank < 0) {
      nodeMap[ids[i]].rank = 0;
    }
    if (nodeMap[ids[i]].rank > maxRank) {
      maxRank = nodeMap[ids[i]].rank;
    }
  }
  return maxRank;
}


function _assignRanksFromGroups(nodeMap) {
  /*
   * In alluvial mode, derive column ranks from the node `group` field.
   * Groups are sorted by first appearance.
   */
  const groupOrder = [];
  const groupIndex = {};
  const ids = Object.keys(nodeMap);
  for (let i = 0; i < ids.length; i = i + 1) {
    const node = nodeMap[ids[i]];
    const g = node.group !== null ? node.group : "__default__";
    if (groupIndex[g] === undefined) {
      groupIndex[g] = groupOrder.length;
      groupOrder.push(g);
    }
    node.rank = groupIndex[g];
  }
  return groupOrder.length - 1;
}


function _groupByRank(nodeMap, maxRank) {
  /*
   * Collect node ids grouped into arrays by rank.
   */
  const columns = [];
  for (let r = 0; r <= maxRank; r = r + 1) {
    columns.push([]);
  }
  const ids = Object.keys(nodeMap);
  for (let i = 0; i < ids.length; i = i + 1) {
    const node = nodeMap[ids[i]];
    if (node.rank >= 0 && node.rank < columns.length) {
      columns[node.rank].push(ids[i]);
    }
  }
  return columns;
}


function _accumulateValues(nodeMap, links) {
  /*
   * Sum incoming and outgoing link values per node.
   */
  for (let i = 0; i < links.length; i = i + 1) {
    const link = links[i];
    const value = typeof link.value === "number" ? link.value : 1;
    if (nodeMap[link.source] !== undefined) {
      nodeMap[link.source].valueOut = nodeMap[link.source].valueOut + value;
    }
    if (nodeMap[link.target] !== undefined) {
      nodeMap[link.target].valueIn = nodeMap[link.target].valueIn + value;
    }
  }
}


function _layoutNodes(nodeMap, columns, plotW, plotH, horizontal) {
  /*
   * Assign pixel x/y and height to each node.
   * In horizontal mode: columns are positioned left-to-right across plotW.
   * In vertical mode: columns are positioned top-to-bottom across plotH.
   */
  const numCols = columns.length;
  const colStep = numCols > 1
    ? (horizontal ? plotW : plotH) / (numCols - 1)
    : (horizontal ? plotW : plotH);

  for (let r = 0; r < columns.length; r = r + 1) {
    const column = columns[r];
    const colNodes = column.map((id) => nodeMap[id]);

    let totalValue = 0;
    for (let n = 0; n < colNodes.length; n = n + 1) {
      const v = Math.max(colNodes[n].valueIn, colNodes[n].valueOut, 1);
      totalValue = totalValue + v;
    }

    const available = (horizontal ? plotH : plotW) - NODE_GAP * (colNodes.length - 1);
    const scale = available > 0 ? available / Math.max(totalValue, 1) : 1;

    let cursor = 0;
    for (let n = 0; n < colNodes.length; n = n + 1) {
      const node = colNodes[n];
      const v = Math.max(node.valueIn, node.valueOut, 1);
      const h = Math.max(v * scale, 4);
      const colPos = numCols > 1 ? r * colStep : (r === 0 ? 0 : colStep);

      if (horizontal === true) {
        node.x = colPos;
        node.y = cursor;
      } else {
        node.x = cursor;
        node.y = colPos;
      }
      node.height = h;
      cursor = cursor + h + NODE_GAP;
    }
  }
}


function _buildLinkPath(sx, sy, tx, ty, horizontal) {
  /*
   * Build a cubic Bézier path for a Sankey link ribbon.
   */
  if (horizontal === true) {
    const midX = (sx + tx) / 2;
    const data = `M${sx.toFixed(2)},${sy.toFixed(2)} ` +
      `C${midX.toFixed(2)},${sy.toFixed(2)} ` +
      `${midX.toFixed(2)},${ty.toFixed(2)} ` +
      `${tx.toFixed(2)},${ty.toFixed(2)}`;
    return data;
  }
  const midY = (sy + ty) / 2;
  const data = `M${sx.toFixed(2)},${sy.toFixed(2)} ` +
    `C${sx.toFixed(2)},${midY.toFixed(2)} ` +
    `${tx.toFixed(2)},${midY.toFixed(2)} ` +
    `${tx.toFixed(2)},${ty.toFixed(2)}`;
  return data;
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
  const mode = ctx.attrs("mode", "sankey");
  const isAlluvial = mode === "alluvial";

  const root = svgEl("g", { part: "plot" }, []);

  const nodes = (raw && Array.isArray(raw.nodes)) ? raw.nodes : [];
  const links = (raw && Array.isArray(raw.links)) ? raw.links : [];

  if (nodes.length === 0) {
    return root;
  }

  const plotW = Math.max(ctx.width - MARGIN.left - MARGIN.right, 10);
  const plotH = Math.max(ctx.height - MARGIN.top - MARGIN.bottom, 10);

  const nodeMap = _buildNodeMap(nodes);
  _accumulateValues(nodeMap, links);

  let maxRank = 0;
  if (isAlluvial === true) {
    maxRank = _assignRanksFromGroups(nodeMap);
  } else {
    maxRank = _assignRanksBFS(nodeMap, links);
  }
  const columns = _groupByRank(nodeMap, maxRank);
  _layoutNodes(nodeMap, columns, plotW, plotH, horizontal);

  const plot = svgEl("g", { transform: `translate(${MARGIN.left},${MARGIN.top})` }, []);
  root.appendChild(plot);

  /* Compute link value extent for stroke-width scaling. */
  let maxLinkValue = 1;
  for (let i = 0; i < links.length; i = i + 1) {
    const v = typeof links[i].value === "number" ? links[i].value : 1;
    if (v > maxLinkValue) {
      maxLinkValue = v;
    }
  }
  const strokeScale = linearScale([0, maxLinkValue], [2, 24]);

  /* Draw links first (behind nodes). */
  const linkOffsetOut = {};
  const linkOffsetIn = {};
  const ids = Object.keys(nodeMap);
  for (let i = 0; i < ids.length; i = i + 1) {
    linkOffsetOut[ids[i]] = 0;
    linkOffsetIn[ids[i]] = 0;
  }

  for (let i = 0; i < links.length; i = i + 1) {
    const link = links[i];
    const src = nodeMap[link.source];
    const tgt = nodeMap[link.target];
    if (src === undefined || tgt === undefined) {
      continue;
    }
    const value = typeof link.value === "number" ? link.value : 1;
    const strokeW = strokeScale(value);
    const halfStroke = strokeW / 2;

    let sx, sy, tx, ty;
    if (horizontal === true) {
      sx = src.x + NODE_WIDTH;
      sy = src.y + linkOffsetOut[src.id] + halfStroke;
      tx = tgt.x;
      ty = tgt.y + linkOffsetIn[tgt.id] + halfStroke;
    } else {
      sx = src.x + linkOffsetOut[src.id] + halfStroke;
      sy = src.y + NODE_WIDTH;
      tx = tgt.x + linkOffsetIn[tgt.id] + halfStroke;
      ty = tgt.y;
    }

    linkOffsetOut[src.id] = linkOffsetOut[src.id] + strokeW;
    linkOffsetIn[tgt.id] = linkOffsetIn[tgt.id] + strokeW;

    const color = ctx.colorFor(link.source);
    const pathData = _buildLinkPath(sx, sy, tx, ty, horizontal);
    const path = svgEl("path", {
      d: pathData,
      fill: "none",
      stroke: color,
      "stroke-width": strokeW.toFixed(2),
      "stroke-opacity": "0.45",
      part: "link",
      tabindex: "0",
      role: "img",
      "aria-label": `${escapeHtml(link.source)} → ${escapeHtml(link.target)}: ${formatNumber(value)}`
    }, []);
    path.appendChild(svgEl("title", null,
      `${link.source} → ${link.target}: ${formatNumber(value)}`));

    const capturedLink = link;
    const capturedValue = value;
    const clickHandler = () => {
      ctx.emit("mj-chart-link-click", {
        source: capturedLink.source,
        target: capturedLink.target,
        value: capturedValue
      });
    };
    path.addEventListener("click", clickHandler);
    path.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        clickHandler();
      }
    });
    plot.appendChild(path);
  }

  /* Draw nodes. */
  for (let i = 0; i < ids.length; i = i + 1) {
    const node = nodeMap[ids[i]];
    const color = ctx.colorFor(node.id);

    let rectX, rectY, rectW, rectH;
    if (horizontal === true) {
      rectX = node.x;
      rectY = node.y;
      rectW = NODE_WIDTH;
      rectH = node.height;
    } else {
      rectX = node.x;
      rectY = node.y;
      rectW = node.height;
      rectH = NODE_WIDTH;
    }

    const rect = svgEl("rect", {
      x: rectX.toFixed(2),
      y: rectY.toFixed(2),
      width: Math.max(rectW, 4).toFixed(2),
      height: Math.max(rectH, 4).toFixed(2),
      rx: 3,
      fill: color,
      part: "node",
      tabindex: "0",
      role: "img",
      "aria-label": `${escapeHtml(node.label)}: in ${formatNumber(node.valueIn)}, out ${formatNumber(node.valueOut)}`
    }, []);
    rect.appendChild(svgEl("title", null,
      `${node.label}: in ${formatNumber(node.valueIn)}, out ${formatNumber(node.valueOut)}`));

    const capturedNode = node;
    const nodeClickHandler = () => {
      ctx.emit("mj-chart-node-click", {
        id: capturedNode.id,
        label: capturedNode.label
      });
    };
    rect.addEventListener("click", nodeClickHandler);
    rect.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        nodeClickHandler();
      }
    });
    plot.appendChild(rect);

    /* Node label. */
    let labelX, labelY, anchor;
    if (horizontal === true) {
      labelX = node.x + NODE_WIDTH + 4;
      labelY = node.y + node.height / 2 + 4;
      anchor = "start";
      if (node.rank === maxRank) {
        labelX = node.x - 4;
        anchor = "end";
      }
    } else {
      labelX = node.x + node.height / 2;
      labelY = node.y - 4;
      anchor = "middle";
    }
    plot.appendChild(svgEl("text", {
      x: labelX.toFixed(2),
      y: labelY.toFixed(2),
      "text-anchor": anchor,
      "font-size": 11,
      fill: "var(--mj-text, #14181f)"
    }, escapeHtml(node.label)));
  }

  return root;
}


registerRenderer("sankey", render);
registerRenderer("alluvial", render);
