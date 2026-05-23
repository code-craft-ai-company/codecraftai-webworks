/*
 * hierlayout.js
 *
 * Hierarchical layout renderer -- a single engine that handles four
 * space-filling / radial decomposition layouts, selected by the `layout`
 * attribute on the controller element:
 *
 *   layout="treemap"      Squarified treemap (Bruls et al.)
 *   layout="sunburst"     Radial partition -- arcs per depth ring
 *   layout="icicle"       Rectangular partition rows (or columns)
 *   layout="circle-pack"  Packed circles, area proportional to value
 *
 * A renderer is `render(ctx) -> SVGElement`:
 *   ctx.model       normalized model { meta, categories, series, raw }
 *   ctx.raw         the raw data object
 *   ctx.width       drawing surface width (px)
 *   ctx.height      drawing surface height (px)
 *   ctx.orientation "vertical" | "horizontal"
 *   ctx.attrs       (name, fallback) -> controller attribute value
 *   ctx.colorFor    (seriesIndex | seriesName) -> CSS color
 *   ctx.emit        (eventName, detail) -> dispatch an interaction event
 * It returns a <g> SVGElement drawn within [0..width] x [0..height].
 *
 * Registered type keys: "treemap", "sunburst", "icicle", "circle-pack"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, arcPath } from "../svgdraw.js";


/* -------------------------------------------------------------------------
 * Shared tree utilities
 * ---------------------------------------------------------------------- */

function _sumChildren(node) {
  /*
   * Recursively compute and attach `.total` to every node.
   * Leaf nodes use their own `value`; internal nodes sum their children.
   * Nodes whose value is missing or null fall back to their subtree sum.
   *
   * :param node: A hierarchical data node.
   * :returns: The numeric total for this subtree.
   */
  const children = node.children
  if (children === undefined || children === null || children.length === 0) {
    const leaf = typeof node.value === "number" && node.value >= 0
      ? node.value
      : 0
    node.total = leaf
    return leaf
  }

  let childSum = 0
  for (let index = 0; index < children.length; index = index + 1) {
    childSum = childSum + _sumChildren(children[index])
  }

  const own = typeof node.value === "number" && node.value >= 0
    ? node.value
    : childSum

  node.total = own
  return own
}


function _assignDepth(node, depth) {
  /*
   * Attach `.depth` to every node, traversing the tree recursively.
   *
   * :param node: A hierarchical data node.
   * :param depth: Current depth (root = 0).
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
   * Return the maximum depth in the subtree rooted at node.
   *
   * :param node: A hierarchical data node.
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


function _collectNodes(node, output) {
  /*
   * Collect all nodes in tree order (pre-order) into `output`.
   *
   * :param node: A hierarchical data node.
   * :param output: Array to push nodes into.
   */
  output.push(node)
  const children = node.children
  if (children === undefined || children === null) {
    return
  }
  for (let index = 0; index < children.length; index = index + 1) {
    _collectNodes(children[index], output)
  }
  return
}


/* -------------------------------------------------------------------------
 * Color helpers
 * ---------------------------------------------------------------------- */

const DEPTH_COLORS = [
  "var(--mj-color-accent-500, #2563eb)",
  "var(--mj-color-success, #15803d)",
  "var(--mj-color-warning, #b45309)",
  "var(--mj-color-danger, #b91c1c)",
  "var(--mj-color-accent-300, #80a8ff)",
  "var(--mj-color-accent-800, #122f78)",
  "var(--mj-color-neutral-500, #6b7280)",
  "var(--mj-color-info, #2563eb)"
]


function _colorForDepth(depth) {
  /*
   * Return a CSS color token for the given tree depth.
   *
   * :param depth: Numeric depth (root = 0).
   * :returns: CSS color string.
   */
  const color = DEPTH_COLORS[depth % DEPTH_COLORS.length]
  return color
}


/* -------------------------------------------------------------------------
 * Shared interactive node wiring
 * ---------------------------------------------------------------------- */

function _makeInteractive(element, partName, ariaLabel, titleText, emitFn, eventName, detail) {
  /*
   * Attach accessibility and interaction attributes/listeners to an SVG node.
   *
   * :param element: The SVGElement to wire up.
   * :param partName: CSS part name.
   * :param ariaLabel: ARIA label string.
   * :param titleText: Text for the <title> child.
   * :param emitFn: ctx.emit function.
   * :param eventName: Event name to fire.
   * :param detail: Event detail object.
   */
  element.setAttribute("part", partName)
  element.setAttribute("tabindex", "0")
  element.setAttribute("role", "img")
  element.setAttribute("aria-label", ariaLabel)
  element.appendChild(svgEl("title", null, titleText))

  const handler = () => {
    emitFn(eventName, detail)
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
 * Treemap layout -- squarified algorithm (Bruls et al.)
 * ---------------------------------------------------------------------- */

function _squarify(items, rect, result) {
  /*
   * Recursive squarified treemap layout. Items must carry `.area` (pixels²).
   * Each item receives `.x .y .w .h` in place.
   *
   * :param items: Array of items with `.area` set.
   * :param rect: { x, y, w, h } available pixel rectangle.
   * :param result: Output array to push laid-out items into.
   */
  if (items.length === 0) {
    return
  }

  /* Normalise areas to fill rect exactly. */
  let totalArea = 0
  for (let index = 0; index < items.length; index = index + 1) {
    totalArea = totalArea + items[index].area
  }

  const rectArea = rect.w * rect.h
  const scale = rectArea > 0 ? rectArea / totalArea : 1
  const scaled = []
  for (let index = 0; index < items.length; index = index + 1) {
    scaled.push(items[index].area * scale)
  }

  _squarifyRow(items, scaled, rect, 0, result)
  return
}


function _worstAspect(row, rowLen, short) {
  /*
   * Compute the worst (maximum) aspect ratio in a proposed row.
   * `row` contains pre-scaled areas; `rowLen` is the available short-side.
   *
   * :param row: Array of scaled area values.
   * :param rowLen: Length of the short side of the remaining rect.
   * :param short: Same as rowLen (passed for clarity).
   * :returns: Worst aspect ratio (>= 1).
   */
  if (row.length === 0 || short === 0) {
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
  const s = short
  const s2 = s * s
  const sum2 = sum * sum
  const worst = Math.max(
    (s2 * maxVal) / sum2,
    sum2 / (s2 * minVal)
  )
  return worst
}


function _squarifyRow(items, scaled, rect, start, result) {
  /*
   * Place rows of items into `rect` using the squarified heuristic.
   *
   * :param items: Original items array.
   * :param scaled: Scaled pixel areas matching `items`.
   * :param rect: Available { x, y, w, h } rectangle.
   * :param start: Index in `items` to begin from.
   * :param result: Output array.
   */
  if (start >= items.length) {
    return
  }
  if (rect.w <= 0 || rect.h <= 0) {
    return
  }

  const horizontal = rect.w >= rect.h
  const short = horizontal ? rect.h : rect.w

  let row = []
  let rowItems = []
  let bestWorst = Infinity

  let index = start
  while (index < items.length) {
    const candidate = row.concat([scaled[index]])
    const aspect = _worstAspect(candidate, short, short)
    if (row.length > 0 && aspect > bestWorst) {
      break
    }
    row = candidate
    rowItems.push(items[index])
    bestWorst = aspect
    index = index + 1
  }

  /* Lay out this row. */
  let rowSum = 0
  for (let k = 0; k < row.length; k = k + 1) {
    rowSum = rowSum + row[k]
  }
  const rowThick = short > 0 ? rowSum / short : 0
  let offset = 0

  for (let k = 0; k < rowItems.length; k = k + 1) {
    const item = rowItems[k]
    const breadth = rowThick > 0 ? row[k] / rowThick : 0
    if (horizontal === true) {
      item.x = rect.x
      item.y = rect.y + offset
      item.w = rowThick
      item.h = breadth
    } else {
      item.x = rect.x + offset
      item.y = rect.y
      item.w = breadth
      item.h = rowThick
    }
    result.push(item)
    offset = offset + breadth
  }

  /* Recurse into the remaining rectangle. */
  let nextRect
  if (horizontal === true) {
    nextRect = {
      x: rect.x + rowThick,
      y: rect.y,
      w: rect.w - rowThick,
      h: rect.h
    }
  } else {
    nextRect = {
      x: rect.x,
      y: rect.y + rowThick,
      w: rect.w,
      h: rect.h - rowThick
    }
  }

  _squarifyRow(items, scaled, nextRect, index, result)
  return
}


function _layoutTreemap(root, plotX, plotY, plotW, plotH) {
  /*
   * Compute squarified treemap rectangles for the entire tree, recursively.
   * Each node receives `.x .y .w .h` (plot-relative pixel coordinates).
   *
   * :param root: Tree root node (already has `.total`).
   * :param plotX: Left edge of bounding rect.
   * :param plotY: Top edge of bounding rect.
   * :param plotW: Width of bounding rect.
   * :param plotH: Height of bounding rect.
   */
  root.x = plotX
  root.y = plotY
  root.w = plotW
  root.h = plotH

  const children = root.children
  if (children === undefined || children === null || children.length === 0) {
    return
  }

  /* Filter children with positive totals. */
  const visible = []
  for (let index = 0; index < children.length; index = index + 1) {
    const child = children[index]
    if (child.total > 0) {
      visible.push({ node: child, area: child.total })
    }
  }
  if (visible.length === 0) {
    return
  }

  /* Lay out children inside root rect, with a 1px inset. */
  const inset = 1
  const innerRect = {
    x: plotX + inset,
    y: plotY + inset,
    w: Math.max(plotW - inset * 2, 0),
    h: Math.max(plotH - inset * 2, 0)
  }

  const laid = []
  _squarify(visible, innerRect, laid)

  for (let index = 0; index < laid.length; index = index + 1) {
    const item = laid[index]
    const node = item.node
    node.x = item.x
    node.y = item.y
    node.w = item.w
    node.h = item.h
    _layoutTreemap(node, item.x, item.y, item.w, item.h)
  }
  return
}


function _renderTreemap(root, plot, ctx) {
  /*
   * Walk the laid-out treemap tree and emit SVG <rect>/<text> elements.
   *
   * :param root: Tree root node (layout already computed).
   * :param plot: Parent <g> element to append into.
   * :param ctx: Renderer context.
   */
  const nodes = []
  _collectNodes(root, nodes)

  const MIN_LABEL_WIDTH = 30
  const MIN_LABEL_HEIGHT = 16

  let clipIndex = 0

  for (let index = 0; index < nodes.length; index = index + 1) {
    const node = nodes[index]
    if (node.w === undefined || node.w <= 0 || node.h === undefined || node.h <= 0) {
      continue
    }

    const color = _colorForDepth(node.depth)
    const isLeaf = node.children === undefined || node.children === null || node.children.length === 0

    /* Rect fill: leaves use depth color, internal nodes are transparent so
     * children tiles show through; the inner border is from the inset. */
    const fill = isLeaf ? color : "none"
    const stroke = "var(--mj-bg, #ffffff)"
    const strokeW = isLeaf ? 1 : 0

    const rect = svgEl("rect", {
      x: node.x, y: node.y, width: node.w, height: node.h,
      fill: fill,
      stroke: stroke,
      "stroke-width": strokeW,
      rx: isLeaf ? 3 : 0,
      "fill-opacity": isLeaf ? 0.85 : 0
    }, [])

    const label = escapeHtml(node.name)
    const valueText = typeof node.total === "number"
      ? String(Math.round(node.total))
      : ""
    const ariaLabel = valueText !== ""
      ? `${node.name}: ${valueText}`
      : node.name

    _makeInteractive(
      rect,
      "treemap-tile",
      ariaLabel,
      ariaLabel,
      ctx.emit,
      "mj-chart-node-click",
      { name: node.name, value: node.total, depth: node.depth }
    )
    plot.appendChild(rect)

    /* Label: only if tile is large enough. */
    if (node.w >= MIN_LABEL_WIDTH && node.h >= MIN_LABEL_HEIGHT) {
      const clipId = `mj-tm-clip-${clipIndex}`
      clipIndex = clipIndex + 1

      const clipRect = svgEl("rect", {
        x: node.x + 2, y: node.y + 2,
        width: Math.max(node.w - 4, 0),
        height: Math.max(node.h - 4, 0)
      }, [])
      const clipPath = svgEl("clipPath", { id: clipId }, [clipRect])
      plot.appendChild(clipPath)

      const textY = node.y + Math.min(14, node.h / 2 + 4)
      const textEl = svgEl("text", {
        x: node.x + 4, y: textY,
        "font-size": 11,
        fill: "var(--mj-bg, #ffffff)",
        "clip-path": `url(#${clipId})`,
        "pointer-events": "none"
      }, label)
      plot.appendChild(textEl)
    }
  }
  return
}


/* -------------------------------------------------------------------------
 * Sunburst layout -- radial partition by depth ring
 * ---------------------------------------------------------------------- */

function _layoutSunburst(node, startAngle, endAngle) {
  /*
   * Recursively assign `.startAngle` and `.endAngle` (radians) to every
   * node in the subtree.  Children partition the parent's angle span
   * proportionally to their `.total`.
   *
   * :param node: Tree node (already has `.total`).
   * :param startAngle: Start of this node's angular slice (radians, 0=up).
   * :param endAngle: End of this node's angular slice (radians).
   */
  node.startAngle = startAngle
  node.endAngle = endAngle

  const children = node.children
  if (children === undefined || children === null || children.length === 0) {
    return
  }

  /* Sum of children totals. */
  let childSum = 0
  for (let index = 0; index < children.length; index = index + 1) {
    childSum = childSum + children[index].total
  }
  if (childSum <= 0) {
    return
  }

  const span = endAngle - startAngle
  let cursor = startAngle

  for (let index = 0; index < children.length; index = index + 1) {
    const child = children[index]
    const childSpan = span * (child.total / childSum)
    _layoutSunburst(child, cursor, cursor + childSpan)
    cursor = cursor + childSpan
  }
  return
}


function _renderSunburst(root, plot, cx, cy, maxDepth, radius, ctx) {
  /*
   * Walk the angle-assigned tree and emit SVG <path> arc elements.
   *
   * :param root: Tree root (angles computed).
   * :param plot: Parent <g> element.
   * :param cx: Centre x.
   * :param cy: Centre y.
   * :param maxDepth: Maximum depth in tree.
   * :param radius: Outer radius of the entire sunburst.
   * :param ctx: Renderer context.
   */
  const nodes = []
  _collectNodes(root, nodes)

  /* Ring thickness per depth level, root gets a small inner disc. */
  const ringThick = maxDepth > 0 ? radius / (maxDepth + 1) : radius
  const MIN_ARC_SPAN = 0.01  /* radians — skip tiny slivers */

  for (let index = 0; index < nodes.length; index = index + 1) {
    const node = nodes[index]
    if (node.startAngle === undefined) {
      continue
    }
    const span = node.endAngle - node.startAngle
    if (span < MIN_ARC_SPAN) {
      continue
    }

    const innerR = node.depth * ringThick
    const outerR = (node.depth + 1) * ringThick
    const color = _colorForDepth(node.depth)

    const pathD = arcPath(cx, cy, innerR, outerR, node.startAngle, node.endAngle)
    const valueText = typeof node.total === "number"
      ? String(Math.round(node.total))
      : ""
    const ariaLabel = valueText !== ""
      ? `${node.name}: ${valueText}`
      : node.name

    const pathEl = svgEl("path", {
      d: pathD,
      fill: color,
      "fill-opacity": 0.85,
      stroke: "var(--mj-bg, #ffffff)",
      "stroke-width": 1
    }, [])

    _makeInteractive(
      pathEl,
      "sunburst-arc",
      ariaLabel,
      ariaLabel,
      ctx.emit,
      "mj-chart-node-click",
      { name: node.name, value: node.total, depth: node.depth }
    )
    plot.appendChild(pathEl)

    /* Label in arc midpoint -- only for arcs wide enough. */
    if (span > 0.2 && (outerR - innerR) > 14) {
      const midAngle = (node.startAngle + node.endAngle) / 2
      const midR = (innerR + outerR) / 2
      const lx = cx + midR * Math.sin(midAngle)
      const ly = cy - midR * Math.cos(midAngle)
      const charLimit = Math.max(3, Math.floor(span * midR / 7))
      const labelText = node.name.length > charLimit
        ? node.name.slice(0, charLimit - 1) + "…"
        : node.name

      plot.appendChild(svgEl("text", {
        x: lx.toFixed(2), y: ly.toFixed(2),
        "text-anchor": "middle",
        "dominant-baseline": "central",
        "font-size": 10,
        fill: "var(--mj-bg, #ffffff)",
        "pointer-events": "none"
      }, escapeHtml(labelText)))
    }
  }
  return
}


/* -------------------------------------------------------------------------
 * Icicle layout -- rectangular partition rows
 * ---------------------------------------------------------------------- */

function _layoutIcicle(node, x, y, w, h, totalW, totalH, bandH, horizontal) {
  /*
   * Recursively assign pixel rect coordinates for the icicle layout.
   *
   * :param node: Current tree node.
   * :param x: Left pixel of this node's rect.
   * :param y: Top pixel of this node's rect.
   * :param w: Width of this node's rect.
   * :param h: Height of this node's rect.
   * :param totalW: Total plot width (used for full-width root).
   * :param totalH: Total plot height (used for full-height root).
   * :param bandH: Height (or width) per depth level.
   * :param horizontal: True = flame-graph orientation.
   */
  node.x = x
  node.y = y
  node.w = w
  node.h = h

  const children = node.children
  if (children === undefined || children === null || children.length === 0) {
    return
  }

  let childSum = 0
  for (let index = 0; index < children.length; index = index + 1) {
    childSum = childSum + children[index].total
  }
  if (childSum <= 0) {
    return
  }

  let cursor = horizontal ? y : x

  for (let index = 0; index < children.length; index = index + 1) {
    const child = children[index]
    const fraction = child.total / childSum

    if (horizontal === true) {
      /* Flame graph: root at left, children grow rightward. */
      const childX = x + bandH
      const childY = cursor
      const childW = bandH
      const childH = h * fraction
      _layoutIcicle(child, childX, childY, childW, childH, totalW, totalH, bandH, horizontal)
      cursor = cursor + childH
    } else {
      /* Default icicle: root at top, children grow downward. */
      const childX = cursor
      const childY = y + bandH
      const childW = w * fraction
      const childH = bandH
      _layoutIcicle(child, childX, childY, childW, childH, totalW, totalH, bandH, horizontal)
      cursor = cursor + childW
    }
  }
  return
}


function _renderIcicle(root, plot, ctx) {
  /*
   * Emit <rect>/<text> elements for the pre-computed icicle layout.
   *
   * :param root: Tree root (layout computed).
   * :param plot: Parent <g>.
   * :param ctx: Renderer context.
   */
  const nodes = []
  _collectNodes(root, nodes)

  const MIN_SIZE = 4
  let clipIndex = 0

  for (let index = 0; index < nodes.length; index = index + 1) {
    const node = nodes[index]
    if (node.w === undefined || node.w < MIN_SIZE || node.h === undefined || node.h < MIN_SIZE) {
      continue
    }

    const color = _colorForDepth(node.depth)
    const rect = svgEl("rect", {
      x: node.x, y: node.y, width: node.w - 1, height: node.h - 1,
      fill: color,
      "fill-opacity": 0.85,
      stroke: "var(--mj-bg, #ffffff)",
      "stroke-width": 1,
      rx: 2
    }, [])

    const valueText = typeof node.total === "number"
      ? String(Math.round(node.total))
      : ""
    const ariaLabel = valueText !== ""
      ? `${node.name}: ${valueText}`
      : node.name

    _makeInteractive(
      rect,
      "icicle-tile",
      ariaLabel,
      ariaLabel,
      ctx.emit,
      "mj-chart-node-click",
      { name: node.name, value: node.total, depth: node.depth }
    )
    plot.appendChild(rect)

    /* Label when tile is wide and tall enough. */
    if (node.w >= 24 && node.h >= 14) {
      const clipId = `mj-ic-clip-${clipIndex}`
      clipIndex = clipIndex + 1

      const clipRect = svgEl("rect", {
        x: node.x + 2, y: node.y + 1,
        width: Math.max(node.w - 4, 0),
        height: Math.max(node.h - 2, 0)
      }, [])
      plot.appendChild(svgEl("clipPath", { id: clipId }, [clipRect]))

      plot.appendChild(svgEl("text", {
        x: node.x + 4,
        y: node.y + Math.min(12, node.h / 2 + 4),
        "font-size": 10,
        fill: "var(--mj-bg, #ffffff)",
        "clip-path": `url(#${clipId})`,
        "pointer-events": "none"
      }, escapeHtml(node.name)))
    }
  }
  return
}


/* -------------------------------------------------------------------------
 * Circle packing layout
 * ---------------------------------------------------------------------- */

function _packCircles(circles) {
  /*
   * Pack an array of { r } circles into an enclosing circle using an
   * incremental front-chain approach (Wang-Bhatt heuristic).
   * Each circle receives `.cx` and `.cy` on exit.
   *
   * :param circles: Array of objects with `.r` (radius).
   * :returns: Object { cx, cy, r } of the enclosing bounding circle.
   */
  if (circles.length === 0) {
    return { cx: 0, cy: 0, r: 0 }
  }
  if (circles.length === 1) {
    circles[0].cx = 0
    circles[0].cy = 0
    return { cx: 0, cy: 0, r: circles[0].r }
  }

  /* Place first two. */
  circles[0].cx = -circles[0].r
  circles[0].cy = 0
  circles[1].cx = circles[1].r
  circles[1].cy = 0

  if (circles.length === 2) {
    const boundR = circles[0].r + circles[1].r
    return { cx: 0, cy: 0, r: boundR / 2 }
  }

  /* Front chain: list of circles placed so far. */
  const chain = [circles[0], circles[1]]

  for (let index = 2; index < circles.length; index = index + 1) {
    const newC = circles[index]
    /* Try to place touching the last two chain entries. */
    const a = chain[chain.length - 2]
    const b = chain[chain.length - 1]
    const placed = _placeCircle(newC, a, b)
    if (placed === false) {
      /* Fall back: place on the right side of the current bound. */
      let maxCx = -Infinity
      for (let k = 0; k < chain.length; k = k + 1) {
        if (chain[k].cx + chain[k].r > maxCx) {
          maxCx = chain[k].cx + chain[k].r
        }
      }
      newC.cx = maxCx + newC.r
      newC.cy = 0
    }
    chain.push(newC)
  }

  /* Compute enclosing circle. */
  let maxDist = 0
  for (let index = 0; index < circles.length; index = index + 1) {
    const c = circles[index]
    const dist = Math.sqrt(c.cx * c.cx + c.cy * c.cy) + c.r
    if (dist > maxDist) {
      maxDist = dist
    }
  }
  return { cx: 0, cy: 0, r: maxDist }
}


function _placeCircle(newC, a, b) {
  /*
   * Try to place `newC` tangent to circles `a` and `b`.
   * Returns true when placement succeeded, false otherwise.
   *
   * :param newC: Circle to place (has .r).
   * :param a: First existing circle (has .cx, .cy, .r).
   * :param b: Second existing circle (has .cx, .cy, .r).
   * :returns: Boolean success.
   */
  const rA = a.r + newC.r
  const rB = b.r + newC.r
  const dx = b.cx - a.cx
  const dy = b.cy - a.cy
  const d2 = dx * dx + dy * dy
  const d = Math.sqrt(d2)

  if (d <= 0) {
    return false
  }

  const cosA = (d2 + rA * rA - rB * rB) / (2 * d * rA)
  if (cosA < -1 || cosA > 1) {
    return false
  }

  const angle = Math.atan2(dy, dx) + Math.acos(cosA)
  newC.cx = a.cx + rA * Math.cos(angle)
  newC.cy = a.cy + rA * Math.sin(angle)
  return true
}


function _layoutCirclePack(node, maxLeafValue, scale) {
  /*
   * Recursively assign `.cx .cy .r` to every node.
   * Leaf radius comes from sqrt-scale of node.total.
   * Internal node radius encloses all children.
   *
   * :param node: Tree node (already has `.total`).
   * :param maxLeafValue: Maximum leaf `.total` value in the entire tree.
   * :param scale: linearScale mapping [0..sqrt(maxLeafValue)] -> [0..maxR].
   * :returns: Enclosing radius for this node.
   */
  const children = node.children
  if (children === undefined || children === null || children.length === 0) {
    /* Leaf: radius from sqrt-scale. */
    const r = scale(Math.sqrt(Math.max(node.total, 0)))
    node.r = Math.max(r, 4)
    node.cx = 0
    node.cy = 0
    return node.r
  }

  /* Recurse to get children radii. */
  for (let index = 0; index < children.length; index = index + 1) {
    _layoutCirclePack(children[index], maxLeafValue, scale)
  }

  /* Sort children by radius descending for better packing. */
  const sorted = children.slice()
  sorted.sort((a, b) => b.r - a.r)

  const bound = _packCircles(sorted)

  /* Translate children back to bound.cx/cy = 0 origin. */
  for (let index = 0; index < sorted.length; index = index + 1) {
    sorted[index].cx = sorted[index].cx - bound.cx
    sorted[index].cy = sorted[index].cy - bound.cy
  }

  /* Internal node encloses children with a 4px padding. */
  node.r = Math.max(bound.r + 4, 6)
  node.cx = 0
  node.cy = 0
  return node.r
}


function _translateCircles(node, ox, oy) {
  /*
   * Translate a subtree's cx/cy by (ox, oy).
   *
   * :param node: Root of subtree.
   * :param ox: X offset.
   * :param oy: Y offset.
   */
  node.cx = node.cx + ox
  node.cy = node.cy + oy
  const children = node.children
  if (children === undefined || children === null) {
    return
  }
  for (let index = 0; index < children.length; index = index + 1) {
    _translateCircles(children[index], ox, oy)
  }
  return
}


function _renderCirclePack(root, plot, ctx) {
  /*
   * Emit <circle>/<text> elements for the pre-computed circle-pack layout.
   *
   * :param root: Tree root (cx/cy/r computed).
   * :param plot: Parent <g>.
   * :param ctx: Renderer context.
   */
  const nodes = []
  _collectNodes(root, nodes)

  const MIN_LABEL_R = 12

  for (let index = 0; index < nodes.length; index = index + 1) {
    const node = nodes[index]
    if (node.cx === undefined || node.r === undefined) {
      continue
    }

    const color = _colorForDepth(node.depth)
    const isLeaf = node.children === undefined || node.children === null || node.children.length === 0

    const circle = svgEl("circle", {
      cx: node.cx.toFixed(2), cy: node.cy.toFixed(2), r: node.r.toFixed(2),
      fill: color,
      "fill-opacity": isLeaf ? 0.75 : 0.2,
      stroke: color,
      "stroke-width": isLeaf ? 1 : 1.5
    }, [])

    const valueText = typeof node.total === "number"
      ? String(Math.round(node.total))
      : ""
    const ariaLabel = valueText !== ""
      ? `${node.name}: ${valueText}`
      : node.name

    _makeInteractive(
      circle,
      "pack-circle",
      ariaLabel,
      ariaLabel,
      ctx.emit,
      "mj-chart-node-click",
      { name: node.name, value: node.total, depth: node.depth }
    )
    plot.appendChild(circle)

    if (node.r >= MIN_LABEL_R) {
      const charLimit = Math.max(2, Math.floor((node.r * 1.4) / 7))
      const labelText = node.name.length > charLimit
        ? node.name.slice(0, charLimit - 1) + "…"
        : node.name

      plot.appendChild(svgEl("text", {
        x: node.cx.toFixed(2), y: node.cy.toFixed(2),
        "text-anchor": "middle",
        "dominant-baseline": "central",
        "font-size": Math.min(11, node.r * 0.5),
        fill: "var(--mj-text, #14181f)",
        "pointer-events": "none"
      }, escapeHtml(labelText)))
    }
  }
  return
}


/* -------------------------------------------------------------------------
 * Main render entry point
 * ---------------------------------------------------------------------- */

export function render(ctx) {
  /*
   * Render one of four hierarchical layout modes, selected by the `layout`
   * attribute: "treemap" (default), "sunburst", "icicle", "circle-pack".
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
  _sumChildren(dataRoot)
  _assignDepth(dataRoot, 0)

  if (dataRoot.total <= 0) {
    return root
  }

  const layout = ctx.attrs("layout", "treemap")

  const margin = { top: 8, right: 8, bottom: 8, left: 8 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  if (layout === "sunburst") {
    const cx = plotW / 2
    const cy = plotH / 2
    const radius = Math.min(plotW, plotH) / 2 - 2
    const depth = _maxDepth(dataRoot)

    _layoutSunburst(dataRoot, 0, 2 * Math.PI)
    _renderSunburst(dataRoot, plot, cx, cy, depth, radius, ctx)

  } else if (layout === "icicle") {
    const horizontal = ctx.orientation === "horizontal"
    const depth = _maxDepth(dataRoot)
    const levels = depth + 1
    const bandH = horizontal
      ? Math.max(plotW / levels, 4)
      : Math.max(plotH / levels, 4)

    _layoutIcicle(dataRoot, 0, 0, plotW, plotH, plotW, plotH, bandH, horizontal)
    _renderIcicle(dataRoot, plot, ctx)

  } else if (layout === "circle-pack") {
    /* Find max leaf value for the sqrt scale. */
    const allNodes = []
    _collectNodes(dataRoot, allNodes)
    let maxLeafVal = 0
    for (let index = 0; index < allNodes.length; index = index + 1) {
      const node = allNodes[index]
      const isLeaf = node.children === undefined || node.children === null || node.children.length === 0
      if (isLeaf && node.total > maxLeafVal) {
        maxLeafVal = node.total
      }
    }
    if (maxLeafVal <= 0) {
      maxLeafVal = 1
    }

    const maxR = Math.min(plotW, plotH) / 6
    const sqrtScale = (v) => {
      const fraction = v / Math.sqrt(maxLeafVal)
      const pixel = fraction * maxR
      return Math.max(pixel, 4)
    }

    _layoutCirclePack(dataRoot, maxLeafVal, sqrtScale)

    /* Centre the root in the plot. */
    const cx = plotW / 2
    const cy = plotH / 2
    _translateCircles(dataRoot, cx, cy)

    _renderCirclePack(dataRoot, plot, ctx)

  } else {
    /* Default: treemap */
    _layoutTreemap(dataRoot, 0, 0, plotW, plotH)
    _renderTreemap(dataRoot, plot, ctx)
  }

  return root
}


registerRenderer("treemap", render);
registerRenderer("sunburst", render);
registerRenderer("icicle", render);
registerRenderer("circle-pack", render);
