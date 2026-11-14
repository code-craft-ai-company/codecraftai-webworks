/*
 * hierlayout.js
 *
 * Hierarchical layout renderer -- a single engine that handles four
 * space-filling / radial decomposition layouts:
 *
 *   treemap      Squarified treemap (Bruls et al.), internal nodes get a
 *                header strip with their name
 *   sunburst     Radial partition -- one ring per depth, root disc in the
 *                centre
 *   icicle       Rectangular partition bands (orientation="horizontal"
 *                gives a flame graph)
 *   circle-pack  Packed circles (front-chain sibling packing with an exact
 *                enclosing circle), area proportional to value
 *
 * The layout follows the chart type (`ctx.type`). An explicit `layout`
 * attribute overrides it: "treemap", "sunburst", "icicle", "circle-pack"
 * or the alias "pack".
 *
 * Data: `raw.root` is a nested tree { name, value, children: [...] }. Leaves
 * carry `value`; an internal node without its own value is the sum of its
 * children. Negative or missing values count as 0. A root given as an array
 * is treated as the children of an unnamed root.
 *
 * Colour: every node takes the colour of its top-level branch
 * (ctx.colorFor(branchIndex)); deeper levels are lighter (fill-opacity).
 * Labels use the theme text colour. The branches are published as the
 * legend, and one table row per node (name, parent, level, value, share)
 * is published as the accessible table.
 *
 * The renderer never writes into the data: it lays out a private copy.
 *
 * Registered type keys: "treemap", "sunburst", "icicle", "circle-pack"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, arcPath, formatNumber } from "../svgdraw.js";


/* Deepest level read from the data (protects against runaway recursion). */
const MAX_TREE_DEPTH = 64

/* Approximate glyph width per px of font size, for label truncation. */
const GLYPH_WIDTH_RATIO = 0.6

const LAYOUT_ALIASES = {
  "treemap": "treemap",
  "sunburst": "sunburst",
  "icicle": "icicle",
  "partition": "icicle",
  "circle-pack": "circle-pack",
  "pack": "circle-pack"
}

const LAYOUT_BY_TYPE = {
  "treemap": "treemap",
  "sunburst": "sunburst",
  "icicle": "icicle",
  "circle-pack": "circle-pack"
}

const TEXT_COLOR = "var(--mj-text, #14181f)"
const MUTED_TEXT_COLOR = "var(--mj-text-muted, #6b7280)"
const GAP_COLOR = "var(--mj-surface, #ffffff)"
const ROOT_FILL = "var(--mj-bg-muted, #eef0f3)"
const ROOT_STROKE = "var(--mj-border-strong, #c7ccd6)"


/* -------------------------------------------------------------------------
 * Private hierarchy built from the data
 * ---------------------------------------------------------------------- */

function _nodeName(source) {
  /*
   * The display name of a data node as a string ("" when it has none).
   *
   * :param source: A data node.
   * :returns: The name text.
   */
  let name = ""
  const candidates = [source.name, source.label, source.id]
  for (let index = 0; index < candidates.length; index = index + 1) {
    const candidate = candidates[index]
    if (typeof candidate === "string" && candidate.length > 0) {
      name = candidate
      break
    }
    if (typeof candidate === "number" && Number.isFinite(candidate) === true) {
      name = String(candidate)
      break
    }
  }
  return name
}


function _ownValue(source) {
  /*
   * The node's own non-negative numeric value, or null.
   */
  let value = null
  if (typeof source.value === "number" && Number.isFinite(source.value) === true) {
    value = Math.max(source.value, 0)
  }
  return value
}


function _rootSource(raw) {
  /*
   * The data root of the hierarchy, or null when there is none.
   *
   * :param raw: The raw chart data.
   * :returns: A data node object, or null.
   */
  if (raw === null || raw === undefined || typeof raw !== "object") {
    return null
  }
  const root = raw.root
  if (Array.isArray(root) === true) {
    return { name: "", children: root }
  }
  if (root === null || root === undefined || typeof root !== "object") {
    return null
  }
  return root
}


function _buildNode(source, parent, depth, ancestors) {
  /*
   * Copy one data node (and its subtree) into a private layout node.
   *
   * :param source: The data node.
   * :param parent: The layout parent (null for the root).
   * :param depth: Depth of this node (root = 0).
   * :param ancestors: Set of data nodes on the path from the root, used to
   *     skip a node that contains itself.
   * :returns: The layout node.
   */
  const node = {
    source: source,
    name: _nodeName(source),
    value: _ownValue(source),
    total: 0,
    depth: depth,
    parent: parent,
    branch: -1,
    children: []
  }

  const children = source.children
  if (Array.isArray(children) === true && depth < MAX_TREE_DEPTH) {
    ancestors.add(source)
    for (let index = 0; index < children.length; index = index + 1) {
      const child = children[index]
      if (child === null || typeof child !== "object" || ancestors.has(child) === true) {
        continue
      }
      node.children.push(_buildNode(child, node, depth + 1, ancestors))
    }
    ancestors.delete(source)
  }
  return node
}


function _sumTotals(node) {
  /*
   * Compute `.total` for every layout node: a leaf's own value (0 when it
   * has none), an internal node's own value or else its children's sum.
   *
   * :returns: The node's total.
   */
  if (node.children.length === 0) {
    node.total = node.value !== null ? node.value : 0
    return node.total
  }
  let childSum = 0
  for (let index = 0; index < node.children.length; index = index + 1) {
    childSum = childSum + _sumTotals(node.children[index])
  }
  node.total = node.value !== null ? node.value : childSum
  return node.total
}


function _assignBranches(root) {
  /*
   * Give every node the index of its top-level ancestor (root = -1).
   */
  const visit = (node, branch) => {
    node.branch = branch
    for (let index = 0; index < node.children.length; index = index + 1) {
      visit(node.children[index], branch)
    }
    return
  }
  for (let index = 0; index < root.children.length; index = index + 1) {
    visit(root.children[index], index)
  }
  return
}


function _buildHierarchy(raw) {
  /*
   * Build the private layout tree of the data.
   *
   * :returns: The layout root, or null when the data has no tree.
   */
  const source = _rootSource(raw)
  if (source === null) {
    return null
  }
  const root = _buildNode(source, null, 0, new Set())
  _sumTotals(root)
  _assignBranches(root)
  return root
}


function _collectNodes(node, output) {
  /*
   * Collect all layout nodes in pre-order.
   */
  output.push(node)
  for (let index = 0; index < node.children.length; index = index + 1) {
    _collectNodes(node.children[index], output)
  }
  return output
}


function _maxDepth(node) {
  /*
   * The deepest level below (and including) a node.
   */
  let max = node.depth
  for (let index = 0; index < node.children.length; index = index + 1) {
    const childMax = _maxDepth(node.children[index])
    if (childMax > max) {
      max = childMax
    }
  }
  return max
}


function _displayName(node) {
  /*
   * The name used in labels for assistive technology.
   */
  const name = node.name !== "" ? node.name : "(unnamed)"
  return name
}


function _isEmptyModel(model) {
  /*
   * Registered isEmpty test: no tree, or nothing with a positive value.
   */
  const root = _buildHierarchy(model.raw)
  const empty = root === null || root.total <= 0
  return empty
}


/* -------------------------------------------------------------------------
 * Colour, labels, table and legend
 * ---------------------------------------------------------------------- */

function _nodeColor(node, ctx) {
  /*
   * The fill colour of a node: its top-level branch colour.
   */
  if (node.branch < 0) {
    /* A root without children is the only mark: give it a series colour. */
    return node.children.length === 0 ? ctx.colorFor(0) : ROOT_FILL
  }
  const color = ctx.colorFor(node.branch)
  return color
}


function _depthOpacity(depth) {
  /*
   * Fill opacity per level: level 1 is the strongest, deeper is lighter.
   */
  const opacity = Math.max(0.85 - (depth - 1) * 0.17, 0.35)
  return opacity
}


function _fitText(text, maxWidth, fontSize) {
  /*
   * Shorten text with an ellipsis to fit an approximate pixel width.
   *
   * :returns: The text to draw ("" when not even two glyphs fit).
   */
  const glyph = fontSize * GLYPH_WIDTH_RATIO
  const capacity = Math.floor(maxWidth / glyph)
  if (capacity < 2) {
    return ""
  }
  if (text.length <= capacity) {
    return text
  }
  const shortened = text.slice(0, Math.max(capacity - 1, 1)) + "…"
  return shortened
}


function _valueText(node) {
  /*
   * The formatted total of a node.
   */
  const text = formatNumber(node.total)
  return text
}


function _ariaText(node, rootTotal) {
  /*
   * "Name: value (share%)" for a node's accessible name and tooltip.
   */
  let text = `${_displayName(node)}: ${_valueText(node)}`
  if (rootTotal > 0 && node.depth > 0) {
    text = text + ` (${formatNumber(node.total / rootTotal * 100, { maximumFractionDigits: 1 })}%)`
  }
  if (node.parent !== null && node.parent.name !== "") {
    text = text + `, in ${node.parent.name}`
  }
  return text
}


function _publishTable(root, ctx, layout) {
  /*
   * Publish one table row per node: name, parent, level, value, share.
   */
  const nodes = _collectNodes(root, [])
  const rows = []
  for (let index = 0; index < nodes.length; index = index + 1) {
    const node = nodes[index]
    const share = root.total > 0
      ? `${formatNumber(node.total / root.total * 100, { maximumFractionDigits: 1 })}%`
      : ""
    rows.push([
      _displayName(node),
      node.parent !== null ? _displayName(node.parent) : "",
      node.depth,
      node.total,
      share
    ])
  }
  ctx.setTable({
    columns: ["Node", "Parent", "Level", "Value", "Share of total"],
    rows: rows,
    caption: `${ctx.label} (${layout})`
  })
  return
}


function _publishLegend(root, ctx) {
  /*
   * Publish one colour-only legend entry per top-level branch.
   */
  const entries = []
  for (let index = 0; index < root.children.length; index = index + 1) {
    entries.push({ label: _displayName(root.children[index]), color: ctx.colorFor(index) })
  }
  ctx.setLegend(entries)
  return
}


/* -------------------------------------------------------------------------
 * Shared interactive node wiring
 * ---------------------------------------------------------------------- */

function _makeInteractive(element, partName, node, rootTotal, ctx) {
  /*
   * Make a node mark focusable and clickable; Enter / Space emit too.
   *
   * :param element: The SVGElement of the node.
   * :param partName: CSS part name.
   * :param node: The layout node.
   * :param rootTotal: The root's total, for the share in the label.
   * :param ctx: Renderer context.
   */
  const label = _ariaText(node, rootTotal)
  element.setAttribute("part", partName)
  element.setAttribute("tabindex", "0")
  element.setAttribute("role", "img")
  element.setAttribute("aria-label", label)
  element.appendChild(svgEl("title", null, label))

  const path = []
  let cursor = node
  while (cursor !== null) {
    path.unshift(cursor.name)
    cursor = cursor.parent
  }
  const detail = { name: node.name, value: node.total, depth: node.depth, path: path }

  const handler = () => {
    ctx.emit("mj-chart-node-click", detail)
  }
  element.addEventListener("click", handler)
  element.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      handler()
    }
  })
  return
}


function _label(x, y, text, fontSize, extra) {
  /*
   * A non-interactive text label (pointer events off).
   */
  const attrs = {
    x: x.toFixed(2),
    y: y.toFixed(2),
    "font-size": fontSize,
    fill: TEXT_COLOR,
    "pointer-events": "none",
    "aria-hidden": "true"
  }
  const keys = Object.keys(extra || {})
  for (let index = 0; index < keys.length; index = index + 1) {
    attrs[keys[index]] = extra[keys[index]]
  }
  const element = svgEl("text", attrs, text)
  return element
}


/* -------------------------------------------------------------------------
 * Treemap layout -- squarified algorithm (Bruls et al.)
 * ---------------------------------------------------------------------- */

const TREEMAP_HEADER = 17
const TREEMAP_PAD = 2


function _worstAspect(row, short) {
  /*
   * The worst (largest) aspect ratio of a proposed row of scaled areas
   * laid along a side of length `short`.
   */
  if (row.length === 0 || short <= 0) {
    return Infinity
  }
  let sum = 0
  let maxVal = 0
  let minVal = Infinity
  for (let index = 0; index < row.length; index = index + 1) {
    const area = row[index]
    sum = sum + area
    if (area > maxVal) {
      maxVal = area
    }
    if (area < minVal) {
      minVal = area
    }
  }
  if (minVal <= 0 || sum <= 0) {
    return Infinity
  }
  const s2 = short * short
  const sum2 = sum * sum
  const worst = Math.max((s2 * maxVal) / sum2, sum2 / (s2 * minVal))
  return worst
}


function _squarify(items, rect) {
  /*
   * Squarified layout of items ({ node, area }) inside a rectangle.
   *
   * :returns: An array of { node, x, y, w, h }.
   */
  const placed = []
  let totalArea = 0
  for (let index = 0; index < items.length; index = index + 1) {
    totalArea = totalArea + items[index].area
  }
  if (totalArea <= 0 || rect.w <= 0 || rect.h <= 0) {
    return placed
  }
  const scale = (rect.w * rect.h) / totalArea
  const scaled = items.map((item) => item.area * scale)

  let remaining = { x: rect.x, y: rect.y, w: rect.w, h: rect.h }
  let start = 0
  while (start < items.length && remaining.w > 0 && remaining.h > 0) {
    const horizontal = remaining.w >= remaining.h
    const short = horizontal === true ? remaining.h : remaining.w

    let row = []
    let bestWorst = Infinity
    let next = start
    while (next < items.length) {
      const candidate = row.concat([scaled[next]])
      const aspect = _worstAspect(candidate, short)
      if (row.length > 0 && aspect > bestWorst) {
        break
      }
      row = candidate
      bestWorst = aspect
      next = next + 1
    }

    let rowSum = 0
    for (let k = 0; k < row.length; k = k + 1) {
      rowSum = rowSum + row[k]
    }
    const thickness = short > 0 ? rowSum / short : 0
    let offset = 0
    for (let k = 0; k < row.length; k = k + 1) {
      const breadth = thickness > 0 ? row[k] / thickness : 0
      if (horizontal === true) {
        placed.push({ node: items[start + k].node, x: remaining.x, y: remaining.y + offset, w: thickness, h: breadth })
      } else {
        placed.push({ node: items[start + k].node, x: remaining.x + offset, y: remaining.y, w: breadth, h: thickness })
      }
      offset = offset + breadth
    }

    if (horizontal === true) {
      remaining = { x: remaining.x + thickness, y: remaining.y, w: remaining.w - thickness, h: remaining.h }
    } else {
      remaining = { x: remaining.x, y: remaining.y + thickness, w: remaining.w, h: remaining.h - thickness }
    }
    start = next
  }
  return placed
}


function _layoutTreemap(node, x, y, w, h, boxes) {
  /*
   * Lay a node out in a rectangle and its children inside it. An internal
   * node below the root keeps a header strip for its name when there is
   * room for one.
   *
   * :param boxes: Map layout node -> { x, y, w, h, header }.
   */
  const box = { x: x, y: y, w: w, h: h, header: false }
  boxes.set(node, box)

  const visible = []
  for (let index = 0; index < node.children.length; index = index + 1) {
    const child = node.children[index]
    if (child.total > 0) {
      visible.push({ node: child, area: child.total })
    }
  }
  if (visible.length === 0) {
    return
  }
  visible.sort((first, second) => second.area - first.area)

  let inner = { x: x, y: y, w: w, h: h }
  if (node.depth > 0) {
    box.header = h >= TREEMAP_HEADER * 2.5 && w >= 40
    const top = box.header === true ? TREEMAP_HEADER : TREEMAP_PAD
    inner = {
      x: x + TREEMAP_PAD,
      y: y + top,
      w: Math.max(w - TREEMAP_PAD * 2, 0),
      h: Math.max(h - top - TREEMAP_PAD, 0)
    }
  }

  const placed = _squarify(visible, inner)
  for (let index = 0; index < placed.length; index = index + 1) {
    const item = placed[index]
    _layoutTreemap(item.node, item.x, item.y, item.w, item.h, boxes)
  }
  return
}


function _renderTreemap(root, plot, plotW, plotH, ctx) {
  /*
   * Draw the treemap: group tiles with header strips, leaf tiles with a
   * name (and value when tall enough). The root itself is the plot.
   */
  const boxes = new Map()
  _layoutTreemap(root, 0, 0, plotW, plotH, boxes)

  const marks = svgEl("g", { part: "treemap" }, [])
  const labels = svgEl("g", { "aria-hidden": "true" }, [])
  plot.appendChild(marks)
  plot.appendChild(labels)

  const nodes = _collectNodes(root, [])
  for (let index = 0; index < nodes.length; index = index + 1) {
    const node = nodes[index]
    const box = boxes.get(node)
    const isLeaf = node.children.length === 0
    /* The root is the plot itself, unless it is the only node. */
    if ((node.depth === 0 && isLeaf === false) || box === undefined || box.w < 1 || box.h < 1) {
      continue
    }
    const color = _nodeColor(node, ctx)

    const rect = svgEl("rect", {
      x: box.x.toFixed(2), y: box.y.toFixed(2),
      width: Math.max(box.w, 0).toFixed(2), height: Math.max(box.h, 0).toFixed(2),
      fill: color,
      "fill-opacity": isLeaf === true ? _depthOpacity(Math.max(node.depth, 1)) : 0.18,
      stroke: GAP_COLOR,
      "stroke-width": 1,
      rx: isLeaf === true ? 2 : 3
    }, [])
    _makeInteractive(rect, "treemap-tile", node, root.total, ctx)
    marks.appendChild(rect)

    if (isLeaf === false) {
      if (box.header === true) {
        const text = _fitText(node.name, box.w - 8, 11)
        if (text !== "") {
          labels.appendChild(_label(box.x + 4, box.y + 12, text, 11, { "font-weight": "600" }))
        }
      }
      continue
    }

    if (box.w >= 24 && box.h >= 15) {
      const name = _fitText(node.name, box.w - 8, 11)
      if (name !== "") {
        labels.appendChild(_label(box.x + 4, box.y + 13, name, 11))
      }
      if (box.h >= 30) {
        const value = _fitText(_valueText(node), box.w - 8, 10)
        if (value !== "") {
          labels.appendChild(_label(box.x + 4, box.y + 26, value, 10, { "fill-opacity": 0.8 }))
        }
      }
    }
  }
  return
}


/* -------------------------------------------------------------------------
 * Partition layout shared by sunburst and icicle
 * ---------------------------------------------------------------------- */

function _partition(node, start, end, spans) {
  /*
   * Assign every node a [start, end] fraction of its parent's span,
   * proportional to the children's totals.
   *
   * :param spans: Map layout node -> { start, end }.
   */
  spans.set(node, { start: start, end: end })
  let childSum = 0
  for (let index = 0; index < node.children.length; index = index + 1) {
    childSum = childSum + node.children[index].total
  }
  if (childSum <= 0) {
    return
  }
  /* Children never take more than the parent's own span. */
  const used = node.total > 0 ? Math.min(childSum / node.total, 1) : 1
  const scale = (end - start) * used / childSum
  let cursor = start
  for (let index = 0; index < node.children.length; index = index + 1) {
    const child = node.children[index]
    const childEnd = cursor + child.total * scale
    _partition(child, cursor, childEnd, spans)
    cursor = childEnd
  }
  return
}


/* -------------------------------------------------------------------------
 * Sunburst
 * ---------------------------------------------------------------------- */

function _renderSunburst(root, plot, plotW, plotH, ctx) {
  /*
   * Draw the root disc and one ring per depth. A node that spans the full
   * circle draws a whole disc / ring.
   */
  const spans = new Map()
  _partition(root, 0, 2 * Math.PI, spans)

  const cx = plotW / 2
  const cy = plotH / 2
  const radius = Math.max(Math.min(plotW, plotH) / 2 - 2, 4)
  const depth = _maxDepth(root)
  const ringThick = radius / (depth + 1)
  const MIN_ARC_SPAN = 0.004

  const marks = svgEl("g", { part: "sunburst" }, [])
  const labels = svgEl("g", { "aria-hidden": "true" }, [])
  plot.appendChild(marks)
  plot.appendChild(labels)

  const nodes = _collectNodes(root, [])
  for (let index = 0; index < nodes.length; index = index + 1) {
    const node = nodes[index]
    const span = spans.get(node)
    if (span === undefined || span.end - span.start < MIN_ARC_SPAN || node.total <= 0) {
      continue
    }
    const innerR = node.depth === 0 ? 0 : node.depth * ringThick
    const outerR = (node.depth + 1) * ringThick
    const isRoot = node.depth === 0

    const pathEl = svgEl("path", {
      d: arcPath(cx, cy, innerR, outerR, span.start, span.end),
      fill: _nodeColor(node, ctx),
      "fill-opacity": isRoot === true ? 1 : _depthOpacity(node.depth),
      stroke: GAP_COLOR,
      "stroke-width": 1
    }, [])
    _makeInteractive(pathEl, "sunburst-arc", node, root.total, ctx)
    marks.appendChild(pathEl)

    if (isRoot === true) {
      const text = _fitText(node.name, ringThick * 1.8, 11)
      if (text !== "") {
        labels.appendChild(_label(cx, cy, text, 11, {
          "text-anchor": "middle", "dominant-baseline": "central", "font-weight": "600"
        }))
      }
      continue
    }

    /*
     * The label runs along the radius (narrow wedges) or along the ring
     * (wide wedges), whichever shows more of the name; it is turned so it
     * never reads upside down.
     */
    const midAngle = (span.start + span.end) / 2
    const midR = (innerR + outerR) / 2
    const ring = outerR - innerR
    const arcLength = (span.end - span.start) * midR
    if (arcLength < 12 || ring < 14) {
      continue
    }
    const radialText = _fitText(node.name, ring - 6, 10)
    const chord = 2 * Math.sqrt(Math.max(outerR * outerR - midR * midR, 0))
    const tangentialText = _fitText(node.name, Math.min(arcLength, chord) - 6, 10)
    const tangential = tangentialText.length > radialText.length
    const text = tangential === true ? tangentialText : radialText
    if (text === "") {
      continue
    }
    const lx = cx + midR * Math.sin(midAngle)
    const ly = cy - midR * Math.cos(midAngle)
    const degrees = midAngle * 180 / Math.PI
    let rotation = degrees < 180 ? degrees - 90 : degrees + 90
    if (tangential === true) {
      rotation = degrees > 90 && degrees < 270 ? degrees - 180 : degrees
    }
    labels.appendChild(_label(lx, ly, text, 10, {
      "text-anchor": "middle",
      "dominant-baseline": "central",
      transform: `rotate(${rotation.toFixed(2)} ${lx.toFixed(2)} ${ly.toFixed(2)})`
    }))
  }
  return
}


/* -------------------------------------------------------------------------
 * Icicle
 * ---------------------------------------------------------------------- */

function _renderIcicle(root, plot, plotW, plotH, horizontal, ctx) {
  /*
   * Draw one band per depth; within a band each node's breadth is its
   * share of its parent. Vertical: root band on top. Horizontal: root band
   * on the left (flame graph).
   */
  const breadth = horizontal === true ? plotH : plotW
  const spans = new Map()
  _partition(root, 0, breadth, spans)

  const levels = _maxDepth(root) + 1
  const bandSize = (horizontal === true ? plotW : plotH) / levels

  const marks = svgEl("g", { part: "icicle" }, [])
  const labels = svgEl("g", { "aria-hidden": "true" }, [])
  plot.appendChild(marks)
  plot.appendChild(labels)

  const nodes = _collectNodes(root, [])
  for (let index = 0; index < nodes.length; index = index + 1) {
    const node = nodes[index]
    const span = spans.get(node)
    if (span === undefined || span.end - span.start < 1 || node.total <= 0) {
      continue
    }
    let x = span.start
    let y = node.depth * bandSize
    let w = span.end - span.start
    let h = bandSize
    if (horizontal === true) {
      x = node.depth * bandSize
      y = span.start
      w = bandSize
      h = span.end - span.start
    }

    const rect = svgEl("rect", {
      x: x.toFixed(2), y: y.toFixed(2),
      width: Math.max(w - 1, 0.5).toFixed(2), height: Math.max(h - 1, 0.5).toFixed(2),
      fill: _nodeColor(node, ctx),
      "fill-opacity": node.depth === 0 ? 1 : _depthOpacity(node.depth),
      stroke: GAP_COLOR,
      "stroke-width": 1,
      rx: 2
    }, [])
    _makeInteractive(rect, "icicle-tile", node, root.total, ctx)
    marks.appendChild(rect)

    if (w >= 24 && h >= 15) {
      const text = _fitText(node.name, w - 8, 10)
      if (text !== "") {
        labels.appendChild(_label(x + 4, y + Math.min(13, h / 2 + 4), text, 10,
          node.depth === 0 ? { "font-weight": "600" } : null))
      }
    }
  }
  return
}


/* -------------------------------------------------------------------------
 * Circle packing -- front-chain sibling packing and enclosing circles
 * (after Wang et al. 2006, as implemented by d3-hierarchy)
 * ---------------------------------------------------------------------- */

function _place(b, a, c) {
  /*
   * Position circle c tangent to circles a and b.
   */
  const dx = b.x - a.x
  const dy = b.y - a.y
  const d2 = dx * dx + dy * dy
  if (d2 > 0) {
    let a2 = a.r + c.r
    a2 = a2 * a2
    let b2 = b.r + c.r
    b2 = b2 * b2
    if (a2 > b2) {
      const x = (d2 + b2 - a2) / (2 * d2)
      const y = Math.sqrt(Math.max(0, b2 / d2 - x * x))
      c.x = b.x - x * dx - y * dy
      c.y = b.y - x * dy + y * dx
    } else {
      const x = (d2 + a2 - b2) / (2 * d2)
      const y = Math.sqrt(Math.max(0, a2 / d2 - x * x))
      c.x = a.x + x * dx - y * dy
      c.y = a.y + x * dy + y * dx
    }
  } else {
    c.x = a.x + c.r
    c.y = a.y
  }
  return
}


function _intersects(a, b) {
  /*
   * True when two circles overlap (beyond a rounding tolerance).
   */
  const dr = a.r + b.r - 1e-6
  const dx = b.x - a.x
  const dy = b.y - a.y
  const overlaps = dr > 0 && dr * dr > dx * dx + dy * dy
  return overlaps
}


function _chainScore(link) {
  /*
   * Squared distance from the origin to the weighted midpoint of a front
   * chain link and its successor.
   */
  const a = link.circle
  const b = link.next.circle
  const ab = a.r + b.r
  const dx = (a.x * b.r + b.x * a.r) / ab
  const dy = (a.y * b.r + b.y * a.r) / ab
  return dx * dx + dy * dy
}


function _encloses(a, b) {
  /*
   * True when circle a contains circle b (with a small tolerance).
   */
  const dr = a.r - b.r + Math.max(a.r, b.r, 1) * 1e-9
  const dx = b.x - a.x
  const dy = b.y - a.y
  const inside = dr > 0 && dr * dr > dx * dx + dy * dy
  return inside
}


function _enclosesNot(a, b) {
  /*
   * True when circle a does not contain circle b.
   */
  const dr = a.r - b.r
  const dx = b.x - a.x
  const dy = b.y - a.y
  const outside = dr < 0 || dr * dr < dx * dx + dy * dy
  return outside
}


function _enclosesAll(a, basis) {
  /*
   * True when circle a contains every circle of the basis.
   */
  for (let index = 0; index < basis.length; index = index + 1) {
    if (_encloses(a, basis[index]) === false) {
      return false
    }
  }
  return true
}


function _encloseTwo(a, b) {
  /*
   * The smallest circle enclosing two circles.
   */
  const x21 = b.x - a.x
  const y21 = b.y - a.y
  const r21 = b.r - a.r
  const length = Math.sqrt(x21 * x21 + y21 * y21)
  if (length === 0) {
    return { x: a.x, y: a.y, r: Math.max(a.r, b.r) }
  }
  const circle = {
    x: (a.x + b.x + x21 / length * r21) / 2,
    y: (a.y + b.y + y21 / length * r21) / 2,
    r: (length + a.r + b.r) / 2
  }
  return circle
}


function _encloseThree(a, b, c) {
  /*
   * The smallest circle enclosing (tangent to) three circles.
   */
  const x1 = a.x
  const y1 = a.y
  const r1 = a.r
  const a2 = x1 - b.x
  const a3 = x1 - c.x
  const b2 = y1 - b.y
  const b3 = y1 - c.y
  const c2 = b.r - r1
  const c3 = c.r - r1
  const d1 = x1 * x1 + y1 * y1 - r1 * r1
  const d2 = d1 - b.x * b.x - b.y * b.y + b.r * b.r
  const d3 = d1 - c.x * c.x - c.y * c.y + c.r * c.r
  const ab = a3 * b2 - a2 * b3
  const xa = (b2 * d3 - b3 * d2) / (ab * 2) - x1
  const xb = (b3 * c2 - b2 * c3) / ab
  const ya = (a3 * d2 - a2 * d3) / (ab * 2) - y1
  const yb = (a2 * c3 - a3 * c2) / ab
  const qa = xb * xb + yb * yb - 1
  const qb = 2 * (r1 + xa * xb + ya * yb)
  const qc = xa * xa + ya * ya - r1 * r1
  const r = -(Math.abs(qa) > 1e-6 ? (qb + Math.sqrt(qb * qb - 4 * qa * qc)) / (2 * qa) : qc / qb)
  const circle = { x: x1 + xa + xb * r, y: y1 + ya + yb * r, r: r }
  return circle
}


function _encloseBasis(basis) {
  /*
   * The enclosing circle of a 1-3 circle basis.
   */
  if (basis.length === 1) {
    return { x: basis[0].x, y: basis[0].y, r: basis[0].r }
  }
  if (basis.length === 2) {
    return _encloseTwo(basis[0], basis[1])
  }
  return _encloseThree(basis[0], basis[1], basis[2])
}


function _extendBasis(basis, circle) {
  /*
   * Smallest basis that encloses the old basis and a new circle, or null.
   */
  if (_enclosesAll(circle, basis) === true) {
    return [circle]
  }
  for (let i = 0; i < basis.length; i = i + 1) {
    if (_enclosesNot(circle, basis[i]) === true &&
        _enclosesAll(_encloseTwo(basis[i], circle), basis) === true) {
      return [basis[i], circle]
    }
  }
  for (let i = 0; i < basis.length - 1; i = i + 1) {
    for (let j = i + 1; j < basis.length; j = j + 1) {
      if (_enclosesNot(_encloseTwo(basis[i], basis[j]), circle) === true &&
          _enclosesNot(_encloseTwo(basis[i], circle), basis[j]) === true &&
          _enclosesNot(_encloseTwo(basis[j], circle), basis[i]) === true &&
          _enclosesAll(_encloseThree(basis[i], basis[j], circle), basis) === true) {
        return [basis[i], basis[j], circle]
      }
    }
  }
  return null
}


function _boundingCircle(circles) {
  /*
   * A simple (not minimal) enclosing circle: used only when the exact
   * algorithm fails numerically.
   */
  let cx = 0
  let cy = 0
  for (let index = 0; index < circles.length; index = index + 1) {
    cx = cx + circles[index].x
    cy = cy + circles[index].y
  }
  cx = cx / circles.length
  cy = cy / circles.length
  let r = 0
  for (let index = 0; index < circles.length; index = index + 1) {
    const c = circles[index]
    r = Math.max(r, Math.hypot(c.x - cx, c.y - cy) + c.r)
  }
  return { x: cx, y: cy, r: r }
}


function _encloseCircles(circles) {
  /*
   * The smallest circle enclosing every circle (Welzl's move-to-front
   * algorithm over a deterministically shuffled list).
   */
  const list = circles.slice()
  /* Deterministic shuffle (linear congruential generator). */
  let seed = 1
  for (let index = list.length - 1; index > 0; index = index - 1) {
    seed = (seed * 1664525 + 1013904223) % 4294967296
    const swap = Math.floor((seed / 4294967296) * (index + 1))
    const held = list[index]
    list[index] = list[swap]
    list[swap] = held
  }

  let basis = []
  let enclosing = null
  let index = 0
  let guard = 0
  const guardLimit = list.length * list.length * 8 + 64
  while (index < list.length) {
    guard = guard + 1
    if (guard > guardLimit) {
      return _boundingCircle(circles)
    }
    const circle = list[index]
    if (enclosing !== null && _encloses(enclosing, circle) === true) {
      index = index + 1
      continue
    }
    const extended = _extendBasis(basis, circle)
    if (extended === null) {
      return _boundingCircle(circles)
    }
    basis = extended
    enclosing = _encloseBasis(basis)
    index = 0
  }
  if (enclosing === null || Number.isFinite(enclosing.r) === false) {
    return _boundingCircle(circles)
  }
  return enclosing
}


function _packSiblings(circles) {
  /*
   * Pack circles ({ r }) around the origin without overlap, each placed
   * tangent to two circles of the front chain; sets `.x` and `.y`.
   *
   * :returns: The radius of the enclosing circle (circles are translated
   *     so it is centred on the origin).
   */
  const count = circles.length
  if (count === 0) {
    return 0
  }
  let first = circles[0]
  first.x = 0
  first.y = 0
  if (count === 1) {
    return first.r
  }
  const second = circles[1]
  first.x = -second.r
  second.x = first.r
  second.y = 0
  if (count === 2) {
    /* Enclosing circle of two tangent circles, re-centred. */
    const shift = (first.x - first.r + second.x + second.r) / 2
    first.x = first.x - shift
    second.x = second.x - shift
    return first.r + second.r
  }
  _place(second, first, circles[2])

  /* Front chain as a circular doubly linked list. */
  let a = { circle: first, next: null, previous: null }
  let b = { circle: second, next: null, previous: null }
  let c = { circle: circles[2], next: null, previous: null }
  a.next = b
  c.previous = b
  b.next = c
  a.previous = c
  c.next = a
  b.previous = a

  let index = 3
  let attempts = 0
  const attemptLimit = count * count * 4 + 64
  while (index < count) {
    attempts = attempts + 1
    if (attempts > attemptLimit) {
      break
    }
    const circle = circles[index]
    _place(a.circle, b.circle, circle)
    c = { circle: circle, next: null, previous: null }

    /* Find the closest intersecting circle on the front chain, if any. */
    let j = b.next
    let k = a.previous
    let sj = b.circle.r
    let sk = a.circle.r
    let restarted = false
    do {
      if (sj <= sk) {
        if (_intersects(j.circle, c.circle) === true) {
          b = j
          a.next = b
          b.previous = a
          restarted = true
          break
        }
        sj = sj + j.circle.r
        j = j.next
      } else {
        if (_intersects(k.circle, c.circle) === true) {
          a = k
          a.next = b
          b.previous = a
          restarted = true
          break
        }
        sk = sk + k.circle.r
        k = k.previous
      }
    } while (j !== k.next)
    if (restarted === true) {
      continue
    }

    /* Insert c between a and b, then pick the pair closest to the centre. */
    c.previous = a
    c.next = b
    a.next = c
    b.previous = c
    b = c
    let bestScore = _chainScore(a)
    let cursor = c.next
    while (cursor !== b) {
      const score = _chainScore(cursor)
      if (score < bestScore) {
        a = cursor
        bestScore = score
      }
      cursor = cursor.next
    }
    b = a.next
    index = index + 1
  }

  /* Enclose the front chain and centre it on the origin. */
  const chain = [b.circle]
  let cursor = b.next
  while (cursor !== b) {
    chain.push(cursor.circle)
    cursor = cursor.next
  }
  const enclosing = _encloseCircles(chain)
  for (let i = 0; i < count; i = i + 1) {
    circles[i].x = circles[i].x - enclosing.x
    circles[i].y = circles[i].y - enclosing.y
  }
  return enclosing.r
}


function _packNode(node, padding, circles) {
  /*
   * Compute every node's radius and its centre relative to its parent's
   * centre (bottom-up). Leaf radius = sqrt(value).
   *
   * :param padding: Space kept around each child, in layout units.
   * :param circles: Map layout node -> { x, y, r } (relative).
   * :returns: The node's circle.
   */
  const own = { x: 0, y: 0, r: 0 }
  circles.set(node, own)
  if (node.children.length === 0) {
    own.r = Math.sqrt(Math.max(node.total, 0))
    return own
  }

  const childCircles = []
  for (let index = 0; index < node.children.length; index = index + 1) {
    const child = node.children[index]
    if (child.total <= 0) {
      continue
    }
    const circle = _packNode(child, padding, circles)
    circle.r = circle.r + padding
    childCircles.push(circle)
  }
  if (childCircles.length === 0) {
    own.r = Math.sqrt(Math.max(node.total, 0))
    return own
  }
  /* Larger circles first pack tighter; layout order only. */
  const ordered = childCircles.slice().sort((first, second) => second.r - first.r)
  const enclosing = _packSiblings(ordered)
  for (let index = 0; index < childCircles.length; index = index + 1) {
    childCircles[index].r = childCircles[index].r - padding
  }
  own.r = enclosing + padding
  return own
}


function _resolveCircles(node, parentX, parentY, scale, circles, output) {
  /*
   * Turn relative circles into absolute pixel circles (top-down), so every
   * descendant moves with its packed parent.
   *
   * :param output: Map layout node -> { cx, cy, r } in pixels.
   */
  const circle = circles.get(node)
  if (circle === undefined) {
    return
  }
  const cx = parentX + circle.x * scale
  const cy = parentY + circle.y * scale
  output.set(node, { cx: cx, cy: cy, r: circle.r * scale })
  for (let index = 0; index < node.children.length; index = index + 1) {
    _resolveCircles(node.children[index], cx, cy, scale, circles, output)
  }
  return
}


function _layoutCirclePack(root, plotW, plotH) {
  /*
   * Pack the whole tree and scale it to fit the plot.
   *
   * :returns: Map layout node -> { cx, cy, r } in plot pixels.
   */
  const budget = Math.max(Math.min(plotW, plotH) / 2 - 1, 2)
  const PADDING_PX = 3

  /* First pass without padding finds the layout-unit size of a pixel. */
  const unpadded = new Map()
  const rawRadius = _packNode(root, 0, unpadded).r
  const unitsPerPixel = rawRadius > 0 ? rawRadius / budget : 1

  const circles = new Map()
  const rootCircle = _packNode(root, PADDING_PX * unitsPerPixel, circles)
  const scale = rootCircle.r > 0 ? budget / rootCircle.r : 1

  const output = new Map()
  _resolveCircles(root, plotW / 2 - rootCircle.x * scale, plotH / 2 - rootCircle.y * scale,
    scale, circles, output)
  return output
}


function _renderCirclePack(root, plot, plotW, plotH, ctx) {
  /*
   * Draw the packed circles: the root as a faint outline, groups as light
   * discs in their branch colour, leaves as stronger discs with labels.
   */
  const placed = _layoutCirclePack(root, plotW, plotH)

  const marks = svgEl("g", { part: "circle-pack" }, [])
  const labels = svgEl("g", { "aria-hidden": "true" }, [])
  plot.appendChild(marks)
  plot.appendChild(labels)

  const nodes = _collectNodes(root, [])
  for (let index = 0; index < nodes.length; index = index + 1) {
    const node = nodes[index]
    const circle = placed.get(node)
    if (circle === undefined || circle.r < 0.5) {
      continue
    }
    const isLeaf = node.children.length === 0
    const isRoot = node.depth === 0
    const color = _nodeColor(node, ctx)

    let fillOpacity = isLeaf === true ? _depthOpacity(node.depth) : 0.14 + 0.06 * node.depth
    if (isRoot === true) {
      fillOpacity = 0.35
    }
    const element = svgEl("circle", {
      cx: circle.cx.toFixed(2), cy: circle.cy.toFixed(2), r: circle.r.toFixed(2),
      fill: color,
      "fill-opacity": fillOpacity.toFixed(2),
      stroke: isRoot === true ? ROOT_STROKE : color,
      "stroke-opacity": isLeaf === true ? 0 : 0.8,
      "stroke-width": 1
    }, [])
    _makeInteractive(element, "pack-circle", node, root.total, ctx)
    marks.appendChild(element)

    if (isLeaf === true && circle.r >= 12) {
      const fontSize = Math.min(11, Math.max(8, circle.r * 0.4))
      const text = _fitText(node.name, circle.r * 1.8, fontSize)
      if (text !== "") {
        labels.appendChild(_label(circle.cx, circle.cy, text, fontSize.toFixed(1), {
          "text-anchor": "middle", "dominant-baseline": "central"
        }))
      }
    }
  }

  /* Group names along the top inside edge of their circle, above children. */
  for (let index = 0; index < nodes.length; index = index + 1) {
    const node = nodes[index]
    const circle = placed.get(node)
    if (node.depth !== 1 || node.children.length === 0 || circle === undefined || circle.r < 28) {
      continue
    }
    const text = _fitText(node.name, circle.r * 1.2, 10)
    if (text !== "") {
      labels.appendChild(_label(circle.cx, circle.cy - circle.r - 3, text, 10, {
        "text-anchor": "middle", "font-weight": "600", fill: MUTED_TEXT_COLOR
      }))
    }
  }
  return
}


/* -------------------------------------------------------------------------
 * Main render entry point
 * ---------------------------------------------------------------------- */

function _resolveLayout(ctx) {
  /*
   * The layout to draw: an explicit, recognised `layout` attribute, else
   * the one of the chart type, else treemap.
   */
  const requested = ctx.attrs("layout", null)
  if (typeof requested === "string" && LAYOUT_ALIASES[requested.trim()] !== undefined) {
    return LAYOUT_ALIASES[requested.trim()]
  }
  const byType = LAYOUT_BY_TYPE[ctx.type]
  const layout = byType !== undefined ? byType : "treemap"
  return layout
}


export function render(ctx) {
  /*
   * Render a treemap, sunburst, icicle or circle-pack chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const root = svgEl("g", { part: "plot" }, [])

  const hierarchy = _buildHierarchy(ctx.raw)
  if (hierarchy === null || hierarchy.total <= 0) {
    return root
  }

  const layout = _resolveLayout(ctx)
  _publishTable(hierarchy, ctx, layout)
  _publishLegend(hierarchy, ctx)

  /* Circle pack keeps room above the top-level circles for their names. */
  const topMargin = layout === "circle-pack" ? 14 : 8
  const margin = { top: topMargin, right: 8, bottom: 8, left: 8 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  if (layout === "sunburst") {
    _renderSunburst(hierarchy, plot, plotW, plotH, ctx)
  } else if (layout === "icicle") {
    _renderIcicle(hierarchy, plot, plotW, plotH, ctx.orientation === "horizontal", ctx)
  } else if (layout === "circle-pack") {
    _renderCirclePack(hierarchy, plot, plotW, plotH, ctx)
  } else {
    _renderTreemap(hierarchy, plot, plotW, plotH, ctx)
  }

  return root
}


const REGISTRATION = { isEmpty: _isEmptyModel }

registerRenderer("treemap", render, REGISTRATION);
registerRenderer("sunburst", render, REGISTRATION);
registerRenderer("icicle", render, REGISTRATION);
registerRenderer("circle-pack", render, REGISTRATION);
