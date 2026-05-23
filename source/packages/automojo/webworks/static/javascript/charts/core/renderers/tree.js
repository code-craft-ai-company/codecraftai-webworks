/*
 * tree.js
 *
 * Node-link tree renderer -- a tidy-tree layout engine (Reingold-Tilford)
 * that handles five chart modes, selected by the `mode` attribute:
 *
 *   mode="tree"          Standard tidy tree (default)
 *   mode="dendrogram"    Branch height encodes merge distance / value
 *   mode="org-chart"     Rectangular node cards with role / name lines
 *   mode="mindmap"       Radial layout from a central root node
 *   mode="decision-tree" Left-to-right tidy tree with decision labels on edges
 *
 * A renderer is `render(ctx) -> SVGElement`:
 *   ctx.model       normalized model { meta, categories, series, raw }
 *   ctx.raw         the raw data object
 *   ctx.width       drawing surface width (px)
 *   ctx.height      drawing surface height (px)
 *   ctx.orientation "vertical" (root top) | "horizontal" (root left)
 *   ctx.attrs       (name, fallback) -> controller attribute value
 *   ctx.colorFor    (seriesIndex | seriesName) -> CSS color
 *   ctx.emit        (eventName, detail) -> dispatch an interaction event
 * It returns a <g> SVGElement drawn within [0..width] x [0..height].
 *
 * Registered type keys: "tree", "dendrogram", "org-chart", "mindmap",
 *                        "decision-tree"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml } from "../svgdraw.js";


/* -------------------------------------------------------------------------
 * Shared depth / size utilities
 * ---------------------------------------------------------------------- */

function _assignDepth(node, depth) {
  /*
   * Attach `.depth` to every node recursively (root = 0).
   *
   * :param node: Tree node.
   * :param depth: Depth integer.
   */
  node.depth = depth
  const children = node.children
  if (children === undefined || children === null) {
    return
  }
  for (let index = 0; index < children.length; index = index + 1) {
    _assignDepth(children[index], depth + 1)
  }
  return
}


function _maxDepth(node) {
  /*
   * Return the maximum depth in this subtree.
   *
   * :param node: Tree node (depth already set).
   * :returns: Integer maximum depth.
   */
  const children = node.children
  if (children === undefined || children === null || children.length === 0) {
    return node.depth
  }
  let max = node.depth
  for (let index = 0; index < children.length; index = index + 1) {
    const childMax = _maxDepth(children[index])
    if (childMax > max) {
      max = childMax
    }
  }
  return max
}


function _collectLeaves(node, output) {
  /*
   * Collect leaf nodes (no children) in left-to-right order.
   *
   * :param node: Tree node.
   * :param output: Array to push into.
   */
  const children = node.children
  if (children === undefined || children === null || children.length === 0) {
    output.push(node)
    return
  }
  for (let index = 0; index < children.length; index = index + 1) {
    _collectLeaves(children[index], output)
  }
  return
}


function _collectAll(node, output) {
  /*
   * Collect all nodes in pre-order.
   *
   * :param node: Tree node.
   * :param output: Array to push into.
   */
  output.push(node)
  const children = node.children
  if (children === undefined || children === null) {
    return
  }
  for (let index = 0; index < children.length; index = index + 1) {
    _collectAll(children[index], output)
  }
  return
}


/* -------------------------------------------------------------------------
 * Reingold-Tilford tidy tree layout
 * -------------------------------------------------------------------------
 * A simplified RT algorithm: positions leaves equidistantly on one axis,
 * and centred internal nodes on their children span.  The second axis maps
 * depth to an even spacing.  This gives a pleasing, non-overlapping layout.
 * ---------------------------------------------------------------------- */

function _assignLeafPositions(root, leafStep) {
  /*
   * Assign `.leafPos` (0-based counter) to every leaf in traversal order.
   * Internal nodes get the average `.leafPos` of their children.
   *
   * :param root: Tree root.
   * :param leafStep: Pixel step between leaves (unused here; assigned later).
   * :returns: Count of leaves.
   */
  let counter = 0

  function _visit(node) {
    const children = node.children
    if (children === undefined || children === null || children.length === 0) {
      node.leafPos = counter
      counter = counter + 1
      return
    }
    for (let index = 0; index < children.length; index = index + 1) {
      _visit(children[index])
    }
    /* Centre over children. */
    const first = children[0]
    const last = children[children.length - 1]
    node.leafPos = (first.leafPos + last.leafPos) / 2
    return
  }

  _visit(root)
  return counter
}


function _applyTidyLayout(root, plotW, plotH, horizontal, depthSpacing, leafSpacing) {
  /*
   * Compute pixel `.x` and `.y` for every node using depth and leafPos.
   *
   * :param root: Tree root (depth + leafPos already set).
   * :param plotW: Plot width.
   * :param plotH: Plot height.
   * :param horizontal: True = root at left, leaves at right.
   * :param depthSpacing: Pixel gap per depth level.
   * :param leafSpacing: Pixel gap between leaves.
   */
  function _visit(node) {
    if (horizontal === true) {
      node.x = node.depth * depthSpacing
      node.y = node.leafPos * leafSpacing
    } else {
      node.x = node.leafPos * leafSpacing
      node.y = node.depth * depthSpacing
    }
    const children = node.children
    if (children === undefined || children === null) {
      return
    }
    for (let index = 0; index < children.length; index = index + 1) {
      _visit(children[index])
    }
    return
  }

  _visit(root)
  return
}


/* -------------------------------------------------------------------------
 * Edge / connector path builders
 * ---------------------------------------------------------------------- */

function _elbowPath(px, py, cx, cy, horizontal) {
  /*
   * Build an elbow (right-angle) connector from parent to child.
   *
   * :param px: Parent x.
   * :param py: Parent y.
   * :param cx: Child x.
   * :param cy: Child y.
   * :param horizontal: True = horizontal tree (parent left, child right).
   * :returns: SVG path data string.
   */
  if (horizontal === true) {
    const midX = (px + cx) / 2
    const data = `M${px.toFixed(2)},${py.toFixed(2)} ` +
      `H${midX.toFixed(2)} ` +
      `V${cy.toFixed(2)} ` +
      `H${cx.toFixed(2)}`
    return data
  }
  const midY = (py + cy) / 2
  const data = `M${px.toFixed(2)},${py.toFixed(2)} ` +
    `V${midY.toFixed(2)} ` +
    `H${cx.toFixed(2)} ` +
    `V${cy.toFixed(2)}`
  return data
}


function _curvePath(px, py, cx, cy, horizontal) {
  /*
   * Build a cubic Bezier connector from parent to child.
   *
   * :param px: Parent x.
   * :param py: Parent y.
   * :param cx: Child x.
   * :param cy: Child y.
   * :param horizontal: True = horizontal tree.
   * :returns: SVG path data string.
   */
  if (horizontal === true) {
    const mx = (px + cx) / 2
    const data = `M${px.toFixed(2)},${py.toFixed(2)} ` +
      `C${mx.toFixed(2)},${py.toFixed(2)} ` +
      `${mx.toFixed(2)},${cy.toFixed(2)} ` +
      `${cx.toFixed(2)},${cy.toFixed(2)}`
    return data
  }
  const my = (py + cy) / 2
  const data = `M${px.toFixed(2)},${py.toFixed(2)} ` +
    `C${px.toFixed(2)},${my.toFixed(2)} ` +
    `${cx.toFixed(2)},${my.toFixed(2)} ` +
    `${cx.toFixed(2)},${cy.toFixed(2)}`
  return data
}


/* -------------------------------------------------------------------------
 * Shared node interaction wiring
 * ---------------------------------------------------------------------- */

function _makeInteractive(element, partName, ariaLabel, titleText, emitFn, detail) {
  /*
   * Attach accessibility attributes and interaction listeners to an element.
   *
   * :param element: SVGElement.
   * :param partName: CSS part name.
   * :param ariaLabel: ARIA label string.
   * :param titleText: <title> text.
   * :param emitFn: ctx.emit.
   * :param detail: Event detail object.
   */
  element.setAttribute("part", partName)
  element.setAttribute("tabindex", "0")
  element.setAttribute("role", "img")
  element.setAttribute("aria-label", ariaLabel)
  element.appendChild(svgEl("title", null, titleText))

  const handler = () => {
    emitFn("mj-chart-node-click", detail)
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


/* -------------------------------------------------------------------------
 * Branch color ramp (used by mindmap at depth 1)
 * ---------------------------------------------------------------------- */

const BRANCH_COLORS = [
  "var(--mj-color-accent-500, #2563eb)",
  "var(--mj-color-success, #15803d)",
  "var(--mj-color-warning, #b45309)",
  "var(--mj-color-danger, #b91c1c)",
  "var(--mj-color-accent-300, #80a8ff)",
  "var(--mj-color-accent-800, #122f78)",
  "var(--mj-color-neutral-500, #6b7280)",
  "var(--mj-color-info, #2563eb)"
]


function _assignBranchColors(root) {
  /*
   * Assign `.branchColor` to every node, inheriting from the depth-1
   * ancestor (used by mindmap mode).
   *
   * :param root: Tree root.
   */
  root.branchColor = "var(--mj-text, #14181f)"
  const children = root.children
  if (children === undefined || children === null) {
    return
  }
  for (let index = 0; index < children.length; index = index + 1) {
    const child = children[index]
    child.branchColor = BRANCH_COLORS[index % BRANCH_COLORS.length]
    _inheritBranchColor(child, child.branchColor)
  }
  return
}


function _inheritBranchColor(node, color) {
  /*
   * Set `.branchColor` to `color` on all nodes in this subtree.
   *
   * :param node: Tree node.
   * :param color: CSS color string.
   */
  node.branchColor = color
  const children = node.children
  if (children === undefined || children === null) {
    return
  }
  for (let index = 0; index < children.length; index = index + 1) {
    _inheritBranchColor(children[index], color)
  }
  return
}


/* -------------------------------------------------------------------------
 * Mindmap radial layout
 * ---------------------------------------------------------------------- */

function _layoutMindmap(root, cx, cy, maxR) {
  /*
   * Place nodes radially: root at centre, first-level children at an even
   * angular distribution, deeper nodes constrained to a half-plane away
   * from the root direction.
   *
   * :param root: Tree root.
   * :param cx: Centre x.
   * :param cy: Centre y.
   * :param maxR: Maximum radius for leaves.
   */
  root.x = cx
  root.y = cy

  const children = root.children
  if (children === undefined || children === null || children.length === 0) {
    return
  }

  const depthMax = _maxDepth(root)
  const rStep = depthMax > 0 ? maxR / depthMax : maxR

  /* Distribute first-level children evenly around the full circle. */
  for (let index = 0; index < children.length; index = index + 1) {
    const angle = (2 * Math.PI * index) / children.length - Math.PI / 2
    _layoutMindmapSubtree(children[index], cx, cy, angle, Math.PI / children.length, rStep)
  }
  return
}


function _layoutMindmapSubtree(node, parentX, parentY, centerAngle, halfSpan, rStep) {
  /*
   * Recursively position a subtree in a half-plane.
   *
   * :param node: Current node.
   * :param parentX: Parent's x.
   * :param parentY: Parent's y.
   * :param centerAngle: Central direction angle (radians, 0 = up).
   * :param halfSpan: Half the angular sector available to this subtree.
   * :param rStep: Radius increment per depth level.
   */
  const r = rStep
  node.x = parentX + r * Math.sin(centerAngle)
  node.y = parentY - r * Math.cos(centerAngle)

  const children = node.children
  if (children === undefined || children === null || children.length === 0) {
    return
  }

  /* Distribute children evenly within the half-plane sector. */
  const childSpan = (2 * halfSpan) / children.length
  const startAngle = centerAngle - halfSpan + childSpan / 2

  for (let index = 0; index < children.length; index = index + 1) {
    const childAngle = startAngle + index * childSpan
    _layoutMindmapSubtree(children[index], node.x, node.y, childAngle, childSpan / 2, rStep)
  }
  return
}


/* -------------------------------------------------------------------------
 * Mode renderers
 * ---------------------------------------------------------------------- */

function _renderEdges(allNodes, plot, edgeStyle, horizontal) {
  /*
   * Draw connector paths from each node to its parent.
   *
   * :param allNodes: All tree nodes (each has .x, .y, .parent).
   * :param plot: Parent <g> element.
   * :param edgeStyle: "curve" | "elbow".
   * :param horizontal: Orientation flag.
   */
  for (let index = 0; index < allNodes.length; index = index + 1) {
    const node = allNodes[index]
    if (node.parent === undefined || node.parent === null) {
      continue
    }
    const px = node.parent.x
    const py = node.parent.y
    const cx = node.x
    const cy = node.y

    let pathD
    if (edgeStyle === "curve") {
      pathD = _curvePath(px, py, cx, cy, horizontal)
    } else {
      pathD = _elbowPath(px, py, cx, cy, horizontal)
    }

    plot.appendChild(svgEl("path", {
      d: pathD,
      fill: "none",
      stroke: "var(--mj-border-strong, #c7ccd6)",
      "stroke-width": 1.5
    }, []))
  }
  return
}


function _renderEdgesMindmap(allNodes, plot) {
  /*
   * Draw curved connectors using branch colors and tapering stroke width.
   *
   * :param allNodes: All tree nodes.
   * :param plot: Parent <g>.
   */
  for (let index = 0; index < allNodes.length; index = index + 1) {
    const node = allNodes[index]
    if (node.parent === undefined || node.parent === null) {
      continue
    }
    const strokeWidth = Math.max(1.5, 4 - node.depth * 0.8)
    const pathD = _curvePath(node.parent.x, node.parent.y, node.x, node.y, false)
    plot.appendChild(svgEl("path", {
      d: pathD,
      fill: "none",
      stroke: node.branchColor || "var(--mj-border-strong, #c7ccd6)",
      "stroke-width": strokeWidth.toFixed(1),
      "stroke-linecap": "round"
    }, []))
  }
  return
}


function _renderTreeNodes(allNodes, plot, ctx, nodeShape) {
  /*
   * Draw circle or rect nodes for standard tree / dendrogram / decision-tree.
   *
   * :param allNodes: All tree nodes with .x, .y, .name.
   * :param plot: Parent <g>.
   * :param ctx: Renderer context.
   * :param nodeShape: "circle" | "rect".
   */
  const nodeR = 8
  const isLeaf = (node) => {
    const ch = node.children
    return ch === undefined || ch === null || ch.length === 0
  }

  for (let index = 0; index < allNodes.length; index = index + 1) {
    const node = allNodes[index]
    if (node.x === undefined) {
      continue
    }

    const leaf = isLeaf(node)
    const fillColor = leaf
      ? "var(--mj-color-accent-500, #2563eb)"
      : "var(--mj-bg, #ffffff)"
    const strokeColor = "var(--mj-color-accent-500, #2563eb)"

    let shape
    if (nodeShape === "rect") {
      shape = svgEl("rect", {
        x: (node.x - nodeR).toFixed(2), y: (node.y - nodeR).toFixed(2),
        width: nodeR * 2, height: nodeR * 2,
        rx: 3,
        fill: fillColor,
        stroke: strokeColor,
        "stroke-width": 1.5
      }, [])
    } else {
      shape = svgEl("circle", {
        cx: node.x.toFixed(2), cy: node.y.toFixed(2), r: nodeR,
        fill: fillColor,
        stroke: strokeColor,
        "stroke-width": 1.5
      }, [])
    }

    const valueText = typeof node.value === "number"
      ? `: ${node.value}`
      : ""
    const ariaLabel = `${node.name}${valueText}`

    _makeInteractive(
      shape,
      "tree-node",
      ariaLabel,
      ariaLabel,
      ctx.emit,
      { name: node.name, value: node.value, depth: node.depth }
    )
    plot.appendChild(shape)

    /* Node label */
    const textAnchor = node.x < 20 ? "start" : "middle"
    const labelX = nodeShape === "circle" ? node.x : node.x
    const labelY = node.y - nodeR - 4

    plot.appendChild(svgEl("text", {
      x: labelX.toFixed(2), y: labelY.toFixed(2),
      "text-anchor": "middle",
      "font-size": 11,
      fill: "var(--mj-text, #14181f)",
      "pointer-events": "none"
    }, escapeHtml(node.name)))
  }
  return
}


function _renderOrgNodes(allNodes, plot, ctx) {
  /*
   * Draw rectangular org-chart node cards with name and role text.
   *
   * :param allNodes: All tree nodes with .x, .y, .name, optional .role.
   * :param plot: Parent <g>.
   * :param ctx: Renderer context.
   */
  const cardW = 100
  const cardH = 40

  for (let index = 0; index < allNodes.length; index = index + 1) {
    const node = allNodes[index]
    if (node.x === undefined) {
      continue
    }

    const cx = node.x
    const cy = node.y
    const rx = cx - cardW / 2
    const ry = cy - cardH / 2

    const card = svgEl("rect", {
      x: rx.toFixed(2), y: ry.toFixed(2),
      width: cardW, height: cardH,
      rx: 6, ry: 6,
      fill: "var(--mj-bg, #ffffff)",
      stroke: "var(--mj-color-accent-500, #2563eb)",
      "stroke-width": 1.5
    }, [])

    const roleLine = node.role !== undefined && node.role !== null
      ? String(node.role)
      : ""
    const ariaLabel = roleLine !== ""
      ? `${node.name}, ${roleLine}`
      : node.name

    _makeInteractive(
      card,
      "org-node",
      ariaLabel,
      ariaLabel,
      ctx.emit,
      { name: node.name, role: node.role, depth: node.depth }
    )
    plot.appendChild(card)

    /* Name line */
    plot.appendChild(svgEl("text", {
      x: cx.toFixed(2), y: (cy - 6).toFixed(2),
      "text-anchor": "middle",
      "font-size": 11,
      "font-weight": "bold",
      fill: "var(--mj-text, #14181f)",
      "pointer-events": "none"
    }, escapeHtml(node.name)))

    /* Role line */
    if (roleLine !== "") {
      plot.appendChild(svgEl("text", {
        x: cx.toFixed(2), y: (cy + 10).toFixed(2),
        "text-anchor": "middle",
        "font-size": 10,
        fill: "var(--mj-text-muted, #6b7280)",
        "pointer-events": "none"
      }, escapeHtml(roleLine)))
    }
  }
  return
}


function _renderMindmapNodes(allNodes, plot, ctx) {
  /*
   * Draw rounded label bubbles for mindmap nodes.
   *
   * :param allNodes: All tree nodes with .x, .y, .name, .branchColor.
   * :param plot: Parent <g>.
   * :param ctx: Renderer context.
   */
  const CHAR_W = 7
  const PAD = 8
  const H = 22

  for (let index = 0; index < allNodes.length; index = index + 1) {
    const node = allNodes[index]
    if (node.x === undefined) {
      continue
    }

    const label = escapeHtml(node.name)
    const w = Math.max(node.name.length * CHAR_W + PAD * 2, 32)
    const color = node.branchColor || "var(--mj-color-accent-500, #2563eb)"
    const isRoot = node.depth === 0

    const bubble = svgEl("rect", {
      x: (node.x - w / 2).toFixed(2), y: (node.y - H / 2).toFixed(2),
      width: w, height: H,
      rx: H / 2,
      fill: isRoot ? color : "var(--mj-bg, #ffffff)",
      stroke: color,
      "stroke-width": isRoot ? 2 : 1.5
    }, [])

    _makeInteractive(
      bubble,
      "mindmap-node",
      node.name,
      node.name,
      ctx.emit,
      { name: node.name, value: node.value, depth: node.depth }
    )
    plot.appendChild(bubble)

    plot.appendChild(svgEl("text", {
      x: node.x.toFixed(2), y: (node.y + 4).toFixed(2),
      "text-anchor": "middle",
      "font-size": 11,
      fill: isRoot ? "var(--mj-bg, #ffffff)" : "var(--mj-text, #14181f)",
      "pointer-events": "none"
    }, label))
  }
  return
}


function _renderDecisionEdgeLabels(allNodes, plot, horizontal) {
  /*
   * Overlay small "Yes" / "No" labels on edges for decision-tree mode.
   * Uses node.label if present, otherwise falls back to Yes/No heuristic.
   *
   * :param allNodes: All tree nodes.
   * :param plot: Parent <g>.
   * :param horizontal: Orientation flag.
   */
  for (let index = 0; index < allNodes.length; index = index + 1) {
    const node = allNodes[index]
    if (node.parent === undefined || node.parent === null) {
      continue
    }
    const parent = node.parent
    const siblings = parent.children
    if (siblings === undefined || siblings === null || siblings.length < 2) {
      continue
    }
    const posInParent = siblings.indexOf(node)
    let edgeLabel = node.label !== undefined && node.label !== null
      ? String(node.label)
      : (posInParent === 0 ? "Yes" : "No")

    const midX = (node.x + parent.x) / 2
    const midY = (node.y + parent.y) / 2

    plot.appendChild(svgEl("text", {
      x: midX.toFixed(2), y: (midY - 4).toFixed(2),
      "text-anchor": "middle",
      "font-size": 10,
      fill: "var(--mj-text-muted, #6b7280)",
      "pointer-events": "none"
    }, escapeHtml(edgeLabel)))
  }
  return
}


/* -------------------------------------------------------------------------
 * Parent back-pointers (needed for edge labels and mindmap edges)
 * ---------------------------------------------------------------------- */

function _attachParents(node, parent) {
  /*
   * Attach `.parent` to every non-root node.
   *
   * :param node: Current tree node.
   * :param parent: Parent node (null for root).
   */
  node.parent = parent
  const children = node.children
  if (children === undefined || children === null) {
    return
  }
  for (let index = 0; index < children.length; index = index + 1) {
    _attachParents(children[index], node)
  }
  return
}


/* -------------------------------------------------------------------------
 * Main render entry point
 * ---------------------------------------------------------------------- */

export function render(ctx) {
  /*
   * Render a node-link tree in one of five modes.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const root = svgEl("g", { part: "plot" }, [])

  const raw = ctx.raw
  if (raw === null || raw === undefined || raw.root === null || raw.root === undefined) {
    return root
  }

  const dataRoot = raw.root
  _assignDepth(dataRoot, 0)
  _attachParents(dataRoot, null)

  const mode = ctx.attrs("mode", "tree")
  const edgeStyle = ctx.attrs("edge-style", "curve")
  const horizontal = ctx.orientation === "horizontal"

  /* Common margins */
  const margin = { top: 24, right: 24, bottom: 24, left: 24 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* ------------------------------------------------------------------
   * Mindmap: fully radial, independent layout path
   * ------------------------------------------------------------------ */
  if (mode === "mindmap") {
    const cx = plotW / 2
    const cy = plotH / 2
    const maxR = Math.min(plotW, plotH) / 2 - 20

    _assignBranchColors(dataRoot)
    _layoutMindmap(dataRoot, cx, cy, maxR)

    const allNodes = []
    _collectAll(dataRoot, allNodes)

    _renderEdgesMindmap(allNodes, plot)
    _renderMindmapNodes(allNodes, plot, ctx)

    return root
  }

  /* ------------------------------------------------------------------
   * Dendrogram: leaf positions equidistant, x/y driven by node.value
   * ------------------------------------------------------------------ */
  if (mode === "dendrogram") {
    const leaves = []
    _collectLeaves(dataRoot, leaves)
    const leafCount = leaves.length
    if (leafCount === 0) {
      return root
    }

    /* Find max value for the distance axis. */
    const allForMax = []
    _collectAll(dataRoot, allForMax)
    let maxVal = 0
    for (let index = 0; index < allForMax.length; index = index + 1) {
      const v = typeof allForMax[index].value === "number" ? allForMax[index].value : 0
      if (v > maxVal) {
        maxVal = v
      }
    }
    if (maxVal <= 0) {
      maxVal = 1
    }

    /* Map value -> pixel distance axis; leaf axis -> equidistant. */
    const leafStep = horizontal
      ? plotH / Math.max(leafCount, 1)
      : plotW / Math.max(leafCount, 1)
    const distRange = horizontal ? plotW : plotH

    /* Assign leaf positions first. */
    for (let index = 0; index < leaves.length; index = index + 1) {
      leaves[index].leafIndex = index
    }

    function _visitDendrogram(node) {
      const ch = node.children
      const isLeaf = ch === undefined || ch === null || ch.length === 0
      const distFraction = typeof node.value === "number"
        ? (maxVal > 0 ? node.value / maxVal : 0)
        : (isLeaf ? 0 : 1)
      const distPx = distFraction * distRange

      if (isLeaf) {
        const leafPx = (node.leafIndex + 0.5) * leafStep
        if (horizontal === true) {
          /* horizontal: leaves on left (x=0), root on right */
          node.x = distPx
          node.y = leafPx
        } else {
          /* vertical: leaves at top (y=0), root at bottom */
          node.x = leafPx
          node.y = plotH - distPx
        }
        return
      }

      for (let index = 0; index < ch.length; index = index + 1) {
        _visitDendrogram(ch[index])
      }

      /* Internal node: average child leaf-axis position */
      let sum = 0
      for (let index = 0; index < ch.length; index = index + 1) {
        sum = sum + (horizontal ? ch[index].y : ch[index].x)
      }
      const mid = sum / ch.length

      if (horizontal === true) {
        node.x = distPx
        node.y = mid
      } else {
        node.x = mid
        node.y = plotH - distPx
      }
      return
    }

    _visitDendrogram(dataRoot)

    const allNodes = []
    _collectAll(dataRoot, allNodes)

    _renderEdges(allNodes, plot, "elbow", horizontal)
    _renderTreeNodes(allNodes, plot, ctx, "circle")

    return root
  }

  /* ------------------------------------------------------------------
   * Standard tidy tree (tree, org-chart, decision-tree)
   * ------------------------------------------------------------------ */
  const leaves = []
  _collectLeaves(dataRoot, leaves)
  const leafCount = leaves.length
  if (leafCount === 0) {
    return root
  }

  /* Org-chart nodes are bigger -- add spacing. */
  const orgMode = mode === "org-chart"
  const cardW = orgMode ? 110 : 0
  const cardH = orgMode ? 50 : 0

  const depthMax = _maxDepth(dataRoot)
  const depthLevels = depthMax + 1

  const depthSpacing = horizontal
    ? Math.max(plotW / depthLevels, orgMode ? cardW + 20 : 48)
    : Math.max(plotH / depthLevels, orgMode ? cardH + 20 : 48)

  const leafSpacing = horizontal
    ? Math.max(plotH / Math.max(leafCount, 1), orgMode ? cardH + 12 : 28)
    : Math.max(plotW / Math.max(leafCount, 1), orgMode ? cardW + 12 : 28)

  const leafCount2 = _assignLeafPositions(dataRoot, leafSpacing)
  _applyTidyLayout(dataRoot, plotW, plotH, horizontal, depthSpacing, leafSpacing)

  /* Offset to centre the whole tree within the plot. */
  const allNodes = []
  _collectAll(dataRoot, allNodes)

  let minX = Infinity
  let maxX = -Infinity
  let minY = Infinity
  let maxY = -Infinity
  for (let index = 0; index < allNodes.length; index = index + 1) {
    const n = allNodes[index]
    if (n.x < minX) { minX = n.x }
    if (n.x > maxX) { maxX = n.x }
    if (n.y < minY) { minY = n.y }
    if (n.y > maxY) { maxY = n.y }
  }

  const treeW = maxX - minX
  const treeH = maxY - minY
  const offsetX = (plotW - treeW) / 2 - minX
  const offsetY = (plotH - treeH) / 2 - minY

  for (let index = 0; index < allNodes.length; index = index + 1) {
    allNodes[index].x = allNodes[index].x + offsetX
    allNodes[index].y = allNodes[index].y + offsetY
  }

  /* Draw edges */
  _renderEdges(allNodes, plot, edgeStyle, horizontal)

  /* Draw decision edge labels */
  if (mode === "decision-tree") {
    _renderDecisionEdgeLabels(allNodes, plot, horizontal)
  }

  /* Draw nodes */
  if (orgMode === true) {
    _renderOrgNodes(allNodes, plot, ctx)
  } else {
    _renderTreeNodes(allNodes, plot, ctx, "circle")
  }

  return root
}


registerRenderer("tree", render);
registerRenderer("dendrogram", render);
registerRenderer("org-chart", render);
registerRenderer("mindmap", render);
registerRenderer("decision-tree", render);
