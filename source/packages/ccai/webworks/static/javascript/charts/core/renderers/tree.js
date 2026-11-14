/*
 * tree.js
 *
 * Node-link tree renderer -- a tidy-tree layout engine that handles five
 * chart modes. The mode follows the chart type (`ctx.type`); an explicit
 * `mode` attribute overrides it:
 *
 *   tree           Standard tidy tree (curved or elbow connectors)
 *   dendrogram     Leaves aligned at distance 0, each merge drawn at the
 *                  parent's merge distance, with a distance axis
 *   org-chart      Rectangular cards with a name and a role line
 *                  (alias mode="org")
 *   mindmap        Root in the centre, branches growing to the right and
 *                  left, coloured per first-level branch
 *   decision-tree  Rectangular decision / outcome nodes with condition
 *                  labels on the edges (alias mode="decision")
 *
 * Data: `raw.root` is a nested tree { name, children: [...] }. Optional
 * node fields: `value`; `role` (org-chart); `distance` / `height` / `value`
 * (dendrogram merge distance; leaves default to 0); `edgeLabel` (or `label`
 * when the node also has a `name`) for the edge from the parent
 * (decision-tree). Names may be numbers; a missing name draws no label.
 *
 * Options: `orientation` ("vertical": root at top; "horizontal": root at
 * left -- the dendrogram defaults to horizontal with leaves on the left),
 * `edge-style` ("curve" | "elbow"; org charts default to elbow).
 *
 * A layout larger than the plot is scaled down to fit. The renderer never
 * writes into the data: it lays out a private copy, and it publishes one
 * table row per node (node, parent, level and the mode's fields).
 *
 * Registered type keys: "tree", "dendrogram", "org-chart", "mindmap",
 *                        "decision-tree"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { linearScale, niceDomain, niceTicks } from "../scales.js";


/* Deepest level read from the data (protects against runaway recursion). */
const MAX_TREE_DEPTH = 64

/* Approximate glyph width per px of font size, for text measurement. */
const GLYPH_WIDTH_RATIO = 0.6

const MODE_ALIASES = {
  "tree": "tree",
  "dendrogram": "dendrogram",
  "org-chart": "org-chart",
  "org": "org-chart",
  "mindmap": "mindmap",
  "decision-tree": "decision-tree",
  "decision": "decision-tree"
}

const MODE_BY_TYPE = {
  "tree": "tree",
  "dendrogram": "dendrogram",
  "org-chart": "org-chart",
  "mindmap": "mindmap",
  "decision-tree": "decision-tree"
}

const TEXT_COLOR = "var(--mj-text, #14181f)"
const MUTED_TEXT_COLOR = "var(--mj-text-muted, #6b7280)"
const SURFACE_COLOR = "var(--mj-surface, #ffffff)"
const ACCENT_COLOR = "var(--mj-accent, #2563eb)"
const ON_ACCENT_COLOR = "var(--mj-text-on-accent, #ffffff)"
const EDGE_COLOR = "var(--mj-border-strong, #c7ccd6)"


/* -------------------------------------------------------------------------
 * Private tree built from the data
 * ---------------------------------------------------------------------- */

function _textOf(value) {
  /*
   * A string or finite number as text, else null.
   */
  if (typeof value === "string" && value.length > 0) {
    return value
  }
  if (typeof value === "number" && Number.isFinite(value) === true) {
    return String(value)
  }
  return null
}


function _numberOf(value) {
  /*
   * A finite number, else null.
   */
  const number = typeof value === "number" && Number.isFinite(value) === true ? value : null
  return number
}


function _rootSource(raw) {
  /*
   * The data root of the tree, or null when there is none. A root given
   * as an array is treated as the children of an unnamed root.
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
   * :param ancestors: Set of data nodes on the path from the root, used to
   *     skip a node that contains itself.
   */
  const name = _textOf(source.name)
  const label = _textOf(source.label)
  const id = _textOf(source.id)

  let edgeLabel = _textOf(source.edgeLabel)
  if (edgeLabel === null && name !== null) {
    edgeLabel = label
  }

  let distance = _numberOf(source.distance)
  if (distance === null) {
    distance = _numberOf(source.height)
  }
  if (distance === null) {
    distance = _numberOf(source.value)
  }

  const node = {
    source: source,
    name: name !== null ? name : (label !== null ? label : (id !== null ? id : "")),
    role: _textOf(source.role),
    value: _numberOf(source.value),
    distance: distance,
    edgeLabel: edgeLabel,
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


function _buildTree(raw) {
  /*
   * The private layout tree of the data, or null.
   */
  const source = _rootSource(raw)
  if (source === null) {
    return null
  }
  const root = _buildNode(source, null, 0, new Set())
  const mark = (node, branch) => {
    node.branch = branch
    for (let index = 0; index < node.children.length; index = index + 1) {
      mark(node.children[index], branch)
    }
    return
  }
  for (let index = 0; index < root.children.length; index = index + 1) {
    mark(root.children[index], index)
  }
  return root
}


function _collectAll(node, output) {
  /*
   * All layout nodes in pre-order.
   */
  output.push(node)
  for (let index = 0; index < node.children.length; index = index + 1) {
    _collectAll(node.children[index], output)
  }
  return output
}


function _collectLeaves(node, output) {
  /*
   * Leaf nodes in left-to-right order.
   */
  if (node.children.length === 0) {
    output.push(node)
    return output
  }
  for (let index = 0; index < node.children.length; index = index + 1) {
    _collectLeaves(node.children[index], output)
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


function _isEmptyModel(model) {
  /*
   * Registered isEmpty test: there is no tree root.
   */
  const empty = _rootSource(model.raw) === null
  return empty
}


/* -------------------------------------------------------------------------
 * Text helpers
 * ---------------------------------------------------------------------- */

function _textWidth(text, fontSize) {
  /*
   * Approximate rendered width of text.
   */
  const width = text.length * fontSize * GLYPH_WIDTH_RATIO
  return width
}


function _fitText(text, maxWidth, fontSize) {
  /*
   * Shorten text with an ellipsis to fit an approximate pixel width.
   */
  const capacity = Math.floor(maxWidth / (fontSize * GLYPH_WIDTH_RATIO))
  if (capacity < 2) {
    return ""
  }
  if (text.length <= capacity) {
    return text
  }
  const shortened = text.slice(0, Math.max(capacity - 1, 1)) + "…"
  return shortened
}


function _displayName(node) {
  /*
   * The name used for assistive technology.
   */
  const name = node.name !== "" ? node.name : "(unnamed)"
  return name
}


function _label(x, y, text, fontSize, extra) {
  /*
   * A non-interactive label with a halo in the surface colour, so lines
   * under it do not hurt legibility.
   */
  const attrs = {
    x: x.toFixed(2),
    y: y.toFixed(2),
    "font-size": fontSize,
    fill: TEXT_COLOR,
    stroke: SURFACE_COLOR,
    "stroke-width": 3,
    "stroke-linejoin": "round",
    "paint-order": "stroke",
    "pointer-events": "none"
  }
  const keys = Object.keys(extra || {})
  for (let index = 0; index < keys.length; index = index + 1) {
    attrs[keys[index]] = extra[keys[index]]
  }
  const element = svgEl("text", attrs, text)
  return element
}


/* -------------------------------------------------------------------------
 * Bounding boxes and fitting
 * ---------------------------------------------------------------------- */

function _emptyBox() {
  /*
   * A bounding box that contains nothing yet.
   */
  return { minX: Infinity, minY: Infinity, maxX: -Infinity, maxY: -Infinity }
}


function _growBox(box, x0, y0, x1, y1) {
  /*
   * Extend a bounding box by a rectangle.
   */
  box.minX = Math.min(box.minX, x0, x1)
  box.maxX = Math.max(box.maxX, x0, x1)
  box.minY = Math.min(box.minY, y0, y1)
  box.maxY = Math.max(box.maxY, y0, y1)
  return
}


function _fitTransform(box, plotW, plotH) {
  /*
   * The transform that centres content in the plot, scaled down (never
   * up) when it is larger than the plot.
   *
   * :returns: { transform, scale }.
   */
  if (Number.isFinite(box.minX) === false) {
    return { transform: "", scale: 1 }
  }
  const contentW = Math.max(box.maxX - box.minX, 1)
  const contentH = Math.max(box.maxY - box.minY, 1)
  const scale = Math.min(1, plotW / contentW, plotH / contentH)
  const tx = (plotW - contentW * scale) / 2 - box.minX * scale
  const ty = (plotH - contentH * scale) / 2 - box.minY * scale
  const transform = scale < 1
    ? `translate(${tx.toFixed(2)},${ty.toFixed(2)}) scale(${scale.toFixed(4)})`
    : `translate(${tx.toFixed(2)},${ty.toFixed(2)})`
  return { transform: transform, scale: scale }
}


/* -------------------------------------------------------------------------
 * Edge / connector path builders
 * ---------------------------------------------------------------------- */

function _elbowPath(px, py, cx, cy, horizontal) {
  /*
   * Elbow connector with the crossbar halfway between parent and child.
   */
  if (horizontal === true) {
    const midX = (px + cx) / 2
    return `M${px.toFixed(2)},${py.toFixed(2)} H${midX.toFixed(2)} V${cy.toFixed(2)} H${cx.toFixed(2)}`
  }
  const midY = (py + cy) / 2
  return `M${px.toFixed(2)},${py.toFixed(2)} V${midY.toFixed(2)} H${cx.toFixed(2)} V${cy.toFixed(2)}`
}


function _curvePath(px, py, cx, cy, horizontal) {
  /*
   * Cubic Bezier connector from parent to child.
   */
  if (horizontal === true) {
    const mx = (px + cx) / 2
    return `M${px.toFixed(2)},${py.toFixed(2)} C${mx.toFixed(2)},${py.toFixed(2)} ` +
      `${mx.toFixed(2)},${cy.toFixed(2)} ${cx.toFixed(2)},${cy.toFixed(2)}`
  }
  const my = (py + cy) / 2
  return `M${px.toFixed(2)},${py.toFixed(2)} C${px.toFixed(2)},${my.toFixed(2)} ` +
    `${cx.toFixed(2)},${my.toFixed(2)} ${cx.toFixed(2)},${cy.toFixed(2)}`
}


/* -------------------------------------------------------------------------
 * Interaction, table
 * ---------------------------------------------------------------------- */

function _ariaText(node, mode) {
  /*
   * The accessible name of a node mark.
   */
  let text = _displayName(node)
  if (node.role !== null) {
    text = text + `, ${node.role}`
  }
  if (mode === "dendrogram" && node.distance !== null) {
    text = text + `: distance ${formatNumber(node.distance)}`
  } else if (node.value !== null && mode !== "dendrogram") {
    text = text + `: ${formatNumber(node.value)}`
  }
  if (node.parent !== null) {
    text = text + ` (under ${_displayName(node.parent)}`
    if (mode === "decision-tree" && node.edgeLabel !== null) {
      text = text + `, ${node.edgeLabel}`
    }
    text = text + ")"
  }
  return text
}


function _makeInteractive(element, partName, node, mode, ctx) {
  /*
   * Make a node mark focusable and clickable; Enter / Space emit too.
   */
  const label = _ariaText(node, mode)
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
  const detail = {
    name: node.name, value: node.value, depth: node.depth, role: node.role, path: path
  }
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


function _publishTable(root, mode, ctx) {
  /*
   * One row per node: node, parent, level, plus the fields the mode uses.
   */
  const nodes = _collectAll(root, [])
  const hasRole = nodes.some((node) => node.role !== null)
  const hasValue = mode !== "dendrogram" && nodes.some((node) => node.value !== null)
  const hasDistance = mode === "dendrogram" && nodes.some((node) => node.distance !== null)
  const hasCondition = mode === "decision-tree" && nodes.some((node) => node.edgeLabel !== null)

  const columns = ["Node", "Parent", "Level"]
  if (hasRole === true) {
    columns.push("Role")
  }
  if (hasCondition === true) {
    columns.push("Condition")
  }
  if (hasValue === true) {
    columns.push("Value")
  }
  if (hasDistance === true) {
    columns.push("Distance")
  }

  const rows = []
  for (let index = 0; index < nodes.length; index = index + 1) {
    const node = nodes[index]
    const row = [_displayName(node), node.parent !== null ? _displayName(node.parent) : "", node.depth]
    if (hasRole === true) {
      row.push(node.role !== null ? node.role : "")
    }
    if (hasCondition === true) {
      row.push(node.edgeLabel !== null ? node.edgeLabel : "")
    }
    if (hasValue === true) {
      row.push(node.value !== null ? node.value : "")
    }
    if (hasDistance === true) {
      row.push(node.distance !== null ? node.distance : "")
    }
    rows.push(row)
  }
  ctx.setTable({ columns: columns, rows: rows, caption: ctx.label })
  return
}


/* -------------------------------------------------------------------------
 * Tidy tree (tree, org-chart, decision-tree)
 * ---------------------------------------------------------------------- */

function _assignLeafSlots(root, slots) {
  /*
   * Leaves get consecutive slots; an internal node sits midway between its
   * first and last child.
   *
   * :param slots: Map layout node -> slot number.
   * :returns: The number of leaves.
   */
  let counter = 0
  const visit = (node) => {
    if (node.children.length === 0) {
      slots.set(node, counter)
      counter = counter + 1
      return
    }
    for (let index = 0; index < node.children.length; index = index + 1) {
      visit(node.children[index])
    }
    const first = slots.get(node.children[0])
    const last = slots.get(node.children[node.children.length - 1])
    slots.set(node, (first + last) / 2)
    return
  }
  visit(root)
  return counter
}


function _nodeSizes(nodes, mode, cardW) {
  /*
   * The drawn box of every node: { w, h }.
   *
   * :param cardW: Card width for org charts, and the widest box a
   *     decision node may take.
   * :returns: Map layout node -> { w, h }.
   */
  const sizes = new Map()
  for (let index = 0; index < nodes.length; index = index + 1) {
    const node = nodes[index]
    if (mode === "org-chart") {
      sizes.set(node, { w: cardW, h: node.role !== null ? 42 : 30 })
    } else if (mode === "decision-tree") {
      const width = Math.min(Math.max(_textWidth(node.name, 11) + 16, 44), cardW)
      sizes.set(node, { w: width, h: 24 })
    } else {
      sizes.set(node, { w: 10, h: 10 })
    }
  }
  return sizes
}


function _layoutTidy(root, mode, horizontal, plotW, plotH) {
  /*
   * Positions for a tidy tree in content coordinates, spread to fill the
   * plot when there is room.
   *
   * :returns: { positions: Map node -> {x, y}, sizes: Map node -> {w, h},
   *     leafSpacing } (leafSpacing: pixels between neighbouring leaves).
   */
  const nodes = _collectAll(root, [])
  const leaves = _collectLeaves(root, [])
  const slots = new Map()
  const leafCount = _assignLeafSlots(root, slots)
  const levels = _maxDepth(root) + 1
  const leafAxis = horizontal === true ? plotH : plotW
  const depthAxis = horizontal === true ? plotW : plotH

  /*
   * Boxes narrow (down to a floor, text is shortened) before the whole
   * layout is scaled, so text stays legible as long as possible.
   */
  let cardW = mode === "org-chart" ? 120 : 150
  if (horizontal === false) {
    const perLeaf = leafAxis / Math.max(leafCount, 1) - 12
    cardW = Math.max(Math.min(perLeaf, cardW), mode === "org-chart" ? 64 : 56)
  }
  const sizes = _nodeSizes(nodes, mode, cardW)

  let maxW = 0
  let maxH = 0
  for (let index = 0; index < nodes.length; index = index + 1) {
    const size = sizes.get(nodes[index])
    maxW = Math.max(maxW, size.w)
    maxH = Math.max(maxH, size.h)
  }

  /* Longest leaf label (tree mode draws leaf labels beside / below nodes). */
  let leafLabelW = 0
  for (let index = 0; index < leaves.length; index = index + 1) {
    leafLabelW = Math.max(leafLabelW, _textWidth(leaves[index].name, 11))
  }
  leafLabelW = Math.min(leafLabelW, 140)

  /* Minimum spacing between leaves and between levels. */
  let leafSlot = 0
  let depthSlot = 0
  if (mode === "tree") {
    /* Vertical leaf labels are shortened / staggered before scaling. */
    const fair = leafAxis / Math.max(leafCount, 1)
    leafSlot = horizontal === true ? 22 : Math.max(Math.min(leafLabelW + 10, 96, fair), 28)
    depthSlot = horizontal === true ? 90 : 52
  } else {
    leafSlot = (horizontal === true ? maxH : maxW) + 12
    depthSlot = (horizontal === true ? maxW : maxH) + (mode === "decision-tree" ? 40 : 30)
  }

  /* Reserved room at the ends of each axis (node boxes and leaf labels). */
  const leafReserve = horizontal === true ? maxH + 4 : (mode === "tree" ? leafSlot : maxW)
  let depthReserve = horizontal === true ? maxW : maxH
  if (mode === "tree") {
    depthReserve = horizontal === true ? leafLabelW + 30 : 44
  }

  const leafSpacing = leafCount > 1
    ? Math.max(leafSlot, (leafAxis - leafReserve) / (leafCount - 1))
    : leafSlot
  const depthSpacing = levels > 1
    ? Math.max(depthSlot, (depthAxis - depthReserve) / (levels - 1))
    : depthSlot

  const positions = new Map()
  for (let index = 0; index < nodes.length; index = index + 1) {
    const node = nodes[index]
    const along = slots.get(node) * leafSpacing
    const down = node.depth * depthSpacing
    positions.set(node, horizontal === true ? { x: down, y: along } : { x: along, y: down })
  }
  /* Vertical tree labels alternate between two rows when they are crowded. */
  const stagger = mode === "tree" && horizontal === false && leafCount > 2 &&
    _textWidth(leaves.reduce((longest, leaf) => leaf.name.length > longest.length ? leaf.name : longest, ""), 11) >
    leafSpacing - 4
  return { positions: positions, sizes: sizes, leafSpacing: leafSpacing, slots: slots, stagger: stagger }
}


function _renderTidy(root, mode, horizontal, plot, plotW, plotH, ctx) {
  /*
   * Draw a tree, org chart or decision tree.
   */
  const layout = _layoutTidy(root, mode, horizontal, plotW, plotH)
  const positions = layout.positions
  const sizes = layout.sizes
  const nodes = _collectAll(root, [])
  const box = _emptyBox()

  const defaultEdge = mode === "org-chart" ? "elbow" : "curve"
  const edgeStyle = ctx.attrs("edge-style", defaultEdge) === "elbow" ? "elbow" : "curve"

  const content = svgEl("g", {}, [])
  const edges = svgEl("g", { "aria-hidden": "true" }, [])
  const edgeLabels = svgEl("g", { "aria-hidden": "true" }, [])
  const marks = svgEl("g", { part: "nodes" }, [])
  const labels = svgEl("g", { "aria-hidden": "true" }, [])
  content.appendChild(edges)
  content.appendChild(marks)
  content.appendChild(labels)
  content.appendChild(edgeLabels)
  plot.appendChild(content)

  /* Edges (and decision conditions at their midpoints). */
  for (let index = 0; index < nodes.length; index = index + 1) {
    const node = nodes[index]
    if (node.parent === null) {
      continue
    }
    const from = positions.get(node.parent)
    const to = positions.get(node)
    const pathD = edgeStyle === "elbow"
      ? _elbowPath(from.x, from.y, to.x, to.y, horizontal)
      : _curvePath(from.x, from.y, to.x, to.y, horizontal)
    edges.appendChild(svgEl("path", {
      d: pathD, fill: "none", stroke: EDGE_COLOR, "stroke-width": 1.5
    }, []))

    if (mode === "decision-tree" && node.edgeLabel !== null) {
      const midX = (from.x + to.x) / 2
      const midY = (from.y + to.y) / 2
      edgeLabels.appendChild(_label(midX, midY, _fitText(node.edgeLabel, 90, 10), 10, {
        "text-anchor": "middle", "dominant-baseline": "central", fill: MUTED_TEXT_COLOR,
        "font-style": "italic"
      }))
      _growBox(box, midX - 45, midY - 8, midX + 45, midY + 8)
    }
  }

  /* Nodes and their labels. */
  for (let index = 0; index < nodes.length; index = index + 1) {
    const node = nodes[index]
    const point = positions.get(node)
    const size = sizes.get(node)
    const isLeaf = node.children.length === 0
    let shape = null

    if (mode === "org-chart") {
      shape = svgEl("rect", {
        x: (point.x - size.w / 2).toFixed(2), y: (point.y - size.h / 2).toFixed(2),
        width: size.w, height: size.h, rx: 6, ry: 6,
        fill: SURFACE_COLOR, stroke: ACCENT_COLOR, "stroke-width": 1.5
      }, [])
      const nameY = node.role !== null ? point.y - 4 : point.y + 4
      const nameText = _fitText(node.name, size.w - 10, 11)
      if (nameText !== "") {
        labels.appendChild(_label(point.x, nameY, nameText, 11, {
          "text-anchor": "middle", "font-weight": "600", stroke: "none"
        }))
      }
      if (node.role !== null) {
        labels.appendChild(_label(point.x, point.y + 12, _fitText(node.role, size.w - 10, 10), 10, {
          "text-anchor": "middle", fill: MUTED_TEXT_COLOR, stroke: "none"
        }))
      }
      _growBox(box, point.x - size.w / 2, point.y - size.h / 2, point.x + size.w / 2, point.y + size.h / 2)
    } else if (mode === "decision-tree") {
      shape = svgEl("rect", {
        x: (point.x - size.w / 2).toFixed(2), y: (point.y - size.h / 2).toFixed(2),
        width: size.w.toFixed(2), height: size.h, rx: isLeaf === true ? 12 : 4,
        fill: isLeaf === true ? ACCENT_COLOR : SURFACE_COLOR,
        "fill-opacity": isLeaf === true ? 0.16 : 1,
        stroke: ACCENT_COLOR, "stroke-width": 1.5
      }, [])
      const text = _fitText(node.name, size.w - 10, 11)
      if (text !== "") {
        labels.appendChild(_label(point.x, point.y, text, 11, {
          "text-anchor": "middle", "dominant-baseline": "central", stroke: "none",
          "font-weight": isLeaf === true ? "600" : "400"
        }))
      }
      _growBox(box, point.x - size.w / 2, point.y - size.h / 2, point.x + size.w / 2, point.y + size.h / 2)
    } else {
      const radius = 5
      shape = svgEl("circle", {
        cx: point.x.toFixed(2), cy: point.y.toFixed(2), r: radius,
        fill: isLeaf === true ? ACCENT_COLOR : SURFACE_COLOR,
        stroke: ACCENT_COLOR, "stroke-width": 1.5
      }, [])
      _growBox(box, point.x - radius, point.y - radius, point.x + radius, point.y + radius)

      if (node.name !== "") {
        if (horizontal === true) {
          if (isLeaf === true) {
            const text = _fitText(node.name, 140, 11)
            labels.appendChild(_label(point.x + 9, point.y, text, 11, { "dominant-baseline": "central" }))
            _growBox(box, point.x, point.y - 7, point.x + 9 + _textWidth(text, 11), point.y + 7)
          } else {
            const text = _fitText(node.name, 120, 11)
            labels.appendChild(_label(point.x, point.y - 10, text, 11, { "text-anchor": "middle" }))
            const half = _textWidth(text, 11) / 2
            _growBox(box, point.x - half, point.y - 22, point.x + half, point.y)
          }
        } else {
          let room = isLeaf === true ? Math.max(layout.leafSpacing - 4, 20) : 140
          let drop = 19
          if (isLeaf === true && layout.stagger === true) {
            room = Math.max(layout.leafSpacing * 2 - 6, 20)
            drop = layout.slots.get(node) % 2 === 1 ? 33 : 19
          }
          const text = _fitText(node.name, room, 11)
          const half = _textWidth(text, 11) / 2
          if (isLeaf === true) {
            labels.appendChild(_label(point.x, point.y + drop, text, 11, { "text-anchor": "middle" }))
            _growBox(box, point.x - half, point.y, point.x + half, point.y + drop + 4)
          } else {
            labels.appendChild(_label(point.x, point.y - 10, text, 11, { "text-anchor": "middle" }))
            _growBox(box, point.x - half, point.y - 22, point.x + half, point.y)
          }
        }
      }
    }

    const partName = mode === "org-chart" ? "org-node" : (mode === "decision-tree" ? "decision-node" : "tree-node")
    _makeInteractive(shape, partName, node, mode, ctx)
    marks.appendChild(shape)
  }

  const fit = _fitTransform(box, plotW, plotH)
  if (fit.transform !== "") {
    content.setAttribute("transform", fit.transform)
  }
  return
}


/* -------------------------------------------------------------------------
 * Dendrogram
 * ---------------------------------------------------------------------- */

function _mergeDistances(root, distances) {
  /*
   * The merge distance of every node: its own `distance` / `height` /
   * `value`, never below its children's; leaves default to 0. Without any
   * distance in the data every merge is one level above its tallest child.
   *
   * :param distances: Map layout node -> distance.
   * :returns: True when the data carries distances on internal nodes.
   */
  const nodes = _collectAll(root, [])
  const explicit = nodes.some((node) => node.children.length > 0 && node.distance !== null)

  const visit = (node) => {
    if (node.children.length === 0) {
      const leafDistance = explicit === true && node.distance !== null ? Math.max(node.distance, 0) : 0
      distances.set(node, leafDistance)
      return leafDistance
    }
    let tallest = 0
    for (let index = 0; index < node.children.length; index = index + 1) {
      tallest = Math.max(tallest, visit(node.children[index]))
    }
    let own = tallest + 1
    if (explicit === true) {
      own = node.distance !== null ? Math.max(node.distance, tallest) : tallest
    }
    distances.set(node, own)
    return own
  }
  visit(root)
  return explicit
}


function _renderDendrogram(root, horizontal, plot, plotW, plotH, ctx) {
  /*
   * Draw a dendrogram. Horizontal: leaves on the left at distance 0, the
   * distance axis runs to the right. Vertical: leaves on top, distance
   * grows downward. Each child's stem runs to its parent's merge distance,
   * where the crossbar joins the siblings.
   */
  const distances = new Map()
  const explicit = _mergeDistances(root, distances)
  const leaves = _collectLeaves(root, [])
  const nodes = _collectAll(root, [])
  const slots = new Map()
  const leafCount = _assignLeafSlots(root, slots)

  let maxDistance = 0
  for (let index = 0; index < nodes.length; index = index + 1) {
    maxDistance = Math.max(maxDistance, distances.get(nodes[index]))
  }
  const domain = explicit === true ? niceDomain(0, maxDistance > 0 ? maxDistance : 1, 5) : [0, Math.max(maxDistance, 1)]

  let labelSpace = 0
  for (let index = 0; index < leaves.length; index = index + 1) {
    labelSpace = Math.max(labelSpace, _textWidth(leaves[index].name, 11))
  }
  const axisSpace = explicit === true ? 22 : 0

  /* Leaf axis and distance axis extents in plot pixels. */
  let leafStart = 0
  let leafEnd = 0
  let distStart = 0
  let distEnd = 0
  if (horizontal === true) {
    labelSpace = Math.min(labelSpace + 8, plotW * 0.35)
    leafStart = 0
    leafEnd = plotH - axisSpace
    distStart = labelSpace
    distEnd = plotW - 6
  } else {
    labelSpace = 16
    leafStart = explicit === true ? 34 : 0
    leafEnd = plotW
    distStart = labelSpace
    distEnd = plotH - 4
  }
  const leafStep = (leafEnd - leafStart) / Math.max(leafCount, 1)
  const distanceScale = linearScale(domain, [distStart, distEnd])

  const pointOf = (node) => {
    const along = leafStart + (slots.get(node) + 0.5) * leafStep
    const across = distanceScale(distances.get(node))
    return horizontal === true ? { x: across, y: along } : { x: along, y: across }
  }

  const edges = svgEl("g", { "aria-hidden": "true" }, [])
  const marks = svgEl("g", { part: "nodes" }, [])
  const labels = svgEl("g", { "aria-hidden": "true" }, [])
  const axis = svgEl("g", { "aria-hidden": "true" }, [])
  plot.appendChild(axis)
  plot.appendChild(edges)
  plot.appendChild(marks)
  plot.appendChild(labels)

  for (let index = 0; index < nodes.length; index = index + 1) {
    const node = nodes[index]
    const point = pointOf(node)
    if (node.parent !== null) {
      const parentPoint = pointOf(node.parent)
      const pathD = horizontal === true
        ? `M${point.x.toFixed(2)},${point.y.toFixed(2)} H${parentPoint.x.toFixed(2)} V${parentPoint.y.toFixed(2)}`
        : `M${point.x.toFixed(2)},${point.y.toFixed(2)} V${parentPoint.y.toFixed(2)} H${parentPoint.x.toFixed(2)}`
      edges.appendChild(svgEl("path", {
        d: pathD, fill: "none", stroke: ACCENT_COLOR, "stroke-opacity": 0.75, "stroke-width": 1.5
      }, []))
    }

    const isLeaf = node.children.length === 0
    const dot = svgEl("circle", {
      cx: point.x.toFixed(2), cy: point.y.toFixed(2), r: isLeaf === true ? 3.5 : 3,
      fill: isLeaf === true ? ACCENT_COLOR : SURFACE_COLOR, stroke: ACCENT_COLOR, "stroke-width": 1.5
    }, [])
    _makeInteractive(dot, "tree-node", node, "dendrogram", ctx)
    marks.appendChild(dot)

    if (isLeaf === true && node.name !== "" && leafStep >= 9) {
      if (horizontal === true) {
        const text = _fitText(node.name, labelSpace - 8, 11)
        labels.appendChild(_label(point.x - 7, point.y, text, 11, {
          "text-anchor": "end", "dominant-baseline": "central"
        }))
      } else {
        const text = _fitText(node.name, leafStep - 2, 10)
        labels.appendChild(_label(point.x, point.y - 7, text, 10, { "text-anchor": "middle" }))
      }
    }
  }

  /* Distance axis. */
  if (explicit === true) {
    const ticks = niceTicks(domain[0], domain[1], 5)
    if (horizontal === true) {
      const axisY = leafEnd + 2
      axis.appendChild(svgEl("line", {
        x1: distStart, y1: axisY, x2: distEnd, y2: axisY, stroke: EDGE_COLOR, "stroke-width": 1
      }, []))
      for (let index = 0; index < ticks.length; index = index + 1) {
        const x = distanceScale(ticks[index])
        axis.appendChild(svgEl("line", { x1: x.toFixed(2), y1: axisY, x2: x.toFixed(2), y2: axisY + 4, stroke: EDGE_COLOR }, []))
        axis.appendChild(svgEl("text", {
          x: x.toFixed(2), y: axisY + 15, "font-size": 10, "text-anchor": "middle", fill: MUTED_TEXT_COLOR
        }, formatNumber(ticks[index])))
      }
    } else {
      const axisX = leafStart - 4
      axis.appendChild(svgEl("line", {
        x1: axisX, y1: distStart, x2: axisX, y2: distEnd, stroke: EDGE_COLOR, "stroke-width": 1
      }, []))
      for (let index = 0; index < ticks.length; index = index + 1) {
        const y = distanceScale(ticks[index])
        axis.appendChild(svgEl("line", { x1: axisX - 4, y1: y.toFixed(2), x2: axisX, y2: y.toFixed(2), stroke: EDGE_COLOR }, []))
        axis.appendChild(svgEl("text", {
          x: axisX - 6, y: y.toFixed(2), "font-size": 10, "text-anchor": "end",
          "dominant-baseline": "central", fill: MUTED_TEXT_COLOR
        }, formatNumber(ticks[index])))
      }
    }
  }
  return
}


/* -------------------------------------------------------------------------
 * Mindmap -- balanced two-sided (or one-sided) horizontal tree
 * ---------------------------------------------------------------------- */

const BUBBLE_H = 22
const BUBBLE_GAP_X = 34
const BUBBLE_SLOT = 28


function _bubbleWidth(node) {
  /*
   * The width of a node's label bubble.
   */
  const width = Math.max(Math.min(_textWidth(node.name, 11), 150) + 18, 34)
  return width
}


function _layoutMindmapSide(branches, direction, rootHalfW, slot, positions) {
  /*
   * Lay out a set of first-level branches on one side of the root as a
   * tidy tree growing outward. Columns are as wide as their widest bubble.
   *
   * :param direction: 1 for the right side, -1 for the left side.
   * :param positions: Map layout node -> { x, y } (filled in).
   * :returns: The number of leaf slots used.
   */
  const columnWidth = []
  const measure = (node) => {
    const level = node.depth
    columnWidth[level] = Math.max(columnWidth[level] || 0, _bubbleWidth(node))
    for (let index = 0; index < node.children.length; index = index + 1) {
      measure(node.children[index])
    }
    return
  }
  for (let index = 0; index < branches.length; index = index + 1) {
    measure(branches[index])
  }

  /* Centre x of each column, outward from the root bubble. */
  const columnX = []
  let edge = rootHalfW
  for (let level = 1; level < columnWidth.length; level = level + 1) {
    const width = columnWidth[level] || 0
    columnX[level] = edge + BUBBLE_GAP_X + width / 2
    edge = edge + BUBBLE_GAP_X + width
  }

  let counter = 0
  const ys = new Map()
  const visit = (node) => {
    if (node.children.length === 0) {
      ys.set(node, counter)
      counter = counter + 1
      return
    }
    for (let index = 0; index < node.children.length; index = index + 1) {
      visit(node.children[index])
    }
    const first = ys.get(node.children[0])
    const last = ys.get(node.children[node.children.length - 1])
    ys.set(node, (first + last) / 2)
    return
  }
  for (let index = 0; index < branches.length; index = index + 1) {
    visit(branches[index])
  }

  const middle = (counter - 1) / 2
  ys.forEach((slotIndex, node) => {
    positions.set(node, { x: direction * columnX[node.depth], y: (slotIndex - middle) * slot })
  })
  return counter
}


function _layoutMindmap(root, twoSided, slot) {
  /*
   * Mindmap positions in content coordinates (root at the origin).
   *
   * :param twoSided: True to split the branches right / left, false to put
   *     every branch on the right.
   * :returns: Map layout node -> { x, y }.
   */
  const positions = new Map()
  positions.set(root, { x: 0, y: 0 })
  const branches = root.children
  const rootHalfW = _bubbleWidth(root) / 2

  let splitAt = branches.length
  if (twoSided === true && branches.length > 1) {
    const leafCounts = branches.map((branch) => _collectLeaves(branch, []).length)
    let total = 0
    for (let index = 0; index < leafCounts.length; index = index + 1) {
      total = total + leafCounts[index]
    }
    let best = Infinity
    let running = 0
    for (let index = 1; index < branches.length; index = index + 1) {
      running = running + leafCounts[index - 1]
      const imbalance = Math.abs(total - 2 * running)
      if (imbalance < best) {
        best = imbalance
        splitAt = index
      }
    }
  }
  _layoutMindmapSide(branches.slice(0, splitAt), 1, rootHalfW, slot, positions)
  if (splitAt < branches.length) {
    _layoutMindmapSide(branches.slice(splitAt), -1, rootHalfW, slot, positions)
  }
  return positions
}


function _mindmapBox(nodes, positions) {
  /*
   * Bounding box of all bubbles.
   */
  const box = _emptyBox()
  for (let index = 0; index < nodes.length; index = index + 1) {
    const point = positions.get(nodes[index])
    const half = _bubbleWidth(nodes[index]) / 2
    _growBox(box, point.x - half, point.y - BUBBLE_H / 2, point.x + half, point.y + BUBBLE_H / 2)
  }
  return box
}


function _renderMindmap(root, plot, plotW, plotH, ctx) {
  /*
   * Draw a mindmap: root bubble in the accent colour, branch connectors
   * and bubble outlines in the first-level branch colour.
   */
  const nodes = _collectAll(root, [])

  /* Choose the arrangement (two-sided or one-sided) that needs less scaling. */
  let best = null
  const arrangements = [true, false]
  for (let index = 0; index < arrangements.length; index = index + 1) {
    const probe = _layoutMindmap(root, arrangements[index], BUBBLE_SLOT)
    const probeBox = _mindmapBox(nodes, probe)
    const fit = _fitTransform(probeBox, plotW, plotH)
    if (best === null || fit.scale > best.scale * 1.05) {
      best = { twoSided: arrangements[index], scale: fit.scale, box: probeBox }
    }
  }
  /* Spread the rows when the plot is taller than the content. */
  const rows = Math.max((best.box.maxY - best.box.minY - BUBBLE_H) / BUBBLE_SLOT + 1, 1)
  const slot = best.scale >= 1 ? Math.max(BUBBLE_SLOT, Math.min((plotH - BUBBLE_H) / Math.max(rows - 1, 1), 40)) : BUBBLE_SLOT
  const positions = _layoutMindmap(root, best.twoSided, slot)
  const fit = _fitTransform(_mindmapBox(nodes, positions), plotW, plotH)

  const content = svgEl("g", { transform: fit.transform }, [])
  const edges = svgEl("g", { "aria-hidden": "true" }, [])
  const marks = svgEl("g", { part: "nodes" }, [])
  const labels = svgEl("g", { "aria-hidden": "true" }, [])
  content.appendChild(edges)
  content.appendChild(marks)
  content.appendChild(labels)
  plot.appendChild(content)

  for (let index = 0; index < nodes.length; index = index + 1) {
    const node = nodes[index]
    const point = positions.get(node)
    const width = _bubbleWidth(node)
    const isRoot = node.depth === 0
    const color = isRoot === true ? ACCENT_COLOR : ctx.colorFor(node.branch)

    if (node.parent !== null) {
      const parentPoint = positions.get(node.parent)
      const direction = point.x >= parentPoint.x ? 1 : -1
      const startX = parentPoint.x + direction * _bubbleWidth(node.parent) / 2
      const endX = point.x - direction * width / 2
      edges.appendChild(svgEl("path", {
        d: _curvePath(startX, parentPoint.y, endX, point.y, true),
        fill: "none",
        stroke: color,
        "stroke-width": Math.max(1.5, 3.5 - node.depth * 0.7).toFixed(1),
        "stroke-linecap": "round"
      }, []))
    }

    const bubble = svgEl("rect", {
      x: (point.x - width / 2).toFixed(2), y: (point.y - BUBBLE_H / 2).toFixed(2),
      width: width.toFixed(2), height: BUBBLE_H, rx: BUBBLE_H / 2,
      fill: isRoot === true ? ACCENT_COLOR : SURFACE_COLOR,
      stroke: color,
      "stroke-width": node.depth <= 1 ? 2 : 1.5
    }, [])
    _makeInteractive(bubble, "mindmap-node", node, "mindmap", ctx)
    marks.appendChild(bubble)

    const text = _fitText(node.name, width - 14, 11)
    if (text !== "") {
      labels.appendChild(svgEl("text", {
        x: point.x.toFixed(2), y: point.y.toFixed(2),
        "text-anchor": "middle", "dominant-baseline": "central", "font-size": 11,
        "font-weight": node.depth <= 1 ? "600" : "400",
        fill: isRoot === true ? ON_ACCENT_COLOR : TEXT_COLOR,
        "pointer-events": "none"
      }, text))
    }
  }
  return
}


/* -------------------------------------------------------------------------
 * Main render entry point
 * ---------------------------------------------------------------------- */

function _resolveMode(ctx) {
  /*
   * The mode to draw: an explicit, recognised `mode` attribute, else the
   * one of the chart type, else "tree".
   */
  const requested = ctx.attrs("mode", null)
  if (typeof requested === "string" && MODE_ALIASES[requested.trim()] !== undefined) {
    return MODE_ALIASES[requested.trim()]
  }
  const byType = MODE_BY_TYPE[ctx.type]
  const mode = byType !== undefined ? byType : "tree"
  return mode
}


export function render(ctx) {
  /*
   * Render a node-link tree in one of five modes.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const root = svgEl("g", { part: "plot" }, [])

  const tree = _buildTree(ctx.raw)
  if (tree === null) {
    return root
  }

  const mode = _resolveMode(ctx)
  const horizontal = ctx.orientation === "horizontal"
  _publishTable(tree, mode, ctx)

  const margin = { top: 12, right: 12, bottom: 12, left: 12 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  if (mode === "mindmap") {
    _renderMindmap(tree, plot, plotW, plotH, ctx)
  } else if (mode === "dendrogram") {
    _renderDendrogram(tree, horizontal, plot, plotW, plotH, ctx)
  } else {
    _renderTidy(tree, mode, horizontal, plot, plotW, plotH, ctx)
  }
  return root
}


registerRenderer("tree", render, { isEmpty: _isEmptyModel });
registerRenderer("dendrogram", render, { isEmpty: _isEmptyModel, orientation: "horizontal" });
registerRenderer("org-chart", render, { isEmpty: _isEmptyModel });
registerRenderer("mindmap", render, { isEmpty: _isEmptyModel, legend: "none" });
registerRenderer("decision-tree", render, { isEmpty: _isEmptyModel });
