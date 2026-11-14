/*
 * venn.js
 *
 * Venn / Euler diagram renderer.
 *
 * JSON shape (ctx.raw):
 *   sets[]           { name, size }   – 1 to 3 sets
 *   intersections[]  { sets[], size } – pairwise and triple intersections
 *                    (inclusive sizes: |A ∩ B| counts the triple region too)
 *   proportional     boolean; default false for "venn", true for "euler"
 *
 * Proportional mode (euler default): circle AREA is proportional to set
 * size (r = sqrt(size / pi), no floor) and every pair of centres is placed
 * at the distance whose lens area equals the declared pairwise intersection
 * (binary search on the circle-intersection formula). An undeclared pair is
 * disjoint, and an intersection as large as the smaller set nests that set
 * inside the other. Three sets are placed from the three pairwise distances
 * (triangle construction, then a least-squares relaxation when the
 * distances are not consistent). The triple region is not fitted: its
 * declared size is printed in it.
 *
 * Schematic mode (venn default): equal circles in the classic 2- or 3-set
 * arrangement, so every region is visible; sizes are printed, not encoded
 * by area.
 *
 * Either way the layout is fitted to the box (scaled and centred on its
 * bounding box), and every region label is placed at a point that lies
 * inside its member circles and outside the others.
 *
 * With 4 or more sets the chart shows a message recommending type="upset"
 * (and still emits mj-chart-error) instead of a partial diagram.
 *
 * Interaction: each set is a focusable mark; click / Enter emits
 * `mj-chart-venn-click` { name, size }.
 *
 * Registers: "venn", "euler"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";

const PADDING = 8
const MAX_SETS = 3


function _circleIntersectionArea(r1, r2, d) {
  /*
   * Intersection area of two circles with radii r1, r2 whose centres are d
   * apart; 0 when they do not overlap.
   */
  if (d >= r1 + r2) {
    return 0
  }
  if (d <= Math.abs(r1 - r2)) {
    const smaller = Math.min(r1, r2)
    return Math.PI * smaller * smaller
  }
  const d2 = d * d
  const r12 = r1 * r1
  const r22 = r2 * r2
  const alpha = Math.acos(Math.max(-1, Math.min(1, (d2 + r12 - r22) / (2 * d * r1))))
  const beta = Math.acos(Math.max(-1, Math.min(1, (d2 + r22 - r12) / (2 * d * r2))))
  const area = r12 * alpha + r22 * beta -
    r12 * Math.sin(2 * alpha) / 2 -
    r22 * Math.sin(2 * beta) / 2
  return Math.max(area, 0)
}


function _targetDistance(r1, r2, targetArea) {
  /*
   * Centre distance whose overlap area is targetArea: r1 + r2 (touching)
   * for no overlap, a nested position for a full overlap, else a binary
   * search between the two.
   */
  if (targetArea <= 0) {
    return r1 + r2
  }
  const smaller = Math.min(r1, r2)
  const maxOverlap = Math.PI * smaller * smaller
  if (targetArea >= maxOverlap * 0.999) {
    return Math.abs(r1 - r2) * 0.5
  }

  let lo = Math.abs(r1 - r2)
  let hi = r1 + r2
  for (let iter = 0; iter < 60; iter = iter + 1) {
    const mid = (lo + hi) / 2
    const area = _circleIntersectionArea(r1, r2, mid)
    if (area > targetArea) {
      lo = mid
    } else {
      hi = mid
    }
  }
  return (lo + hi) / 2
}


function _readSets(raw) {
  /*
   * Normalise sets and intersections.
   *
   * :returns: { sets: [{name, size, source}], intersections: [{members:
   *     [set indexes], size, names}] } -- intersections that name an
   *     unknown set, fewer than two sets, or repeat a combination are
   *     dropped.
   */
  const sets = []
  const byName = new Map()
  const list = Array.isArray(raw.sets) === true ? raw.sets : []
  for (let index = 0; index < list.length; index = index + 1) {
    const entry = list[index]
    if (entry === null || typeof entry !== "object" || entry.name === undefined || entry.name === null) {
      continue
    }
    const name = String(entry.name)
    if (byName.has(name) === true) {
      continue
    }
    const size = typeof entry.size === "number" && Number.isFinite(entry.size) === true
      ? Math.max(entry.size, 0)
      : 0
    byName.set(name, sets.length)
    sets.push({ name: name, size: size, source: entry })
  }

  const intersections = []
  const seen = new Set()
  const rawIntersections = Array.isArray(raw.intersections) === true ? raw.intersections : []
  for (let index = 0; index < rawIntersections.length; index = index + 1) {
    const entry = rawIntersections[index]
    if (entry === null || typeof entry !== "object" || Array.isArray(entry.sets) === false) {
      continue
    }
    const members = []
    let valid = true
    for (let m = 0; m < entry.sets.length; m = m + 1) {
      const position = byName.get(String(entry.sets[m]))
      if (position === undefined) {
        valid = false
        break
      }
      if (members.indexOf(position) < 0) {
        members.push(position)
      }
    }
    const size = typeof entry.size === "number" && Number.isFinite(entry.size) === true
      ? Math.max(entry.size, 0)
      : null
    if (valid === false || members.length < 2 || size === null) {
      continue
    }
    members.sort((a, b) => a - b)
    const key = members.join(",")
    if (seen.has(key) === true) {
      continue
    }
    seen.add(key)
    intersections.push({ members: members, size: size, names: members.map((m) => sets[m].name) })
  }
  return { sets: sets, intersections: intersections }
}


function _pairSize(intersections, a, b) {
  /*
   * Declared size of the pair (a, b), or 0 when it is not declared.
   */
  const low = Math.min(a, b)
  const high = Math.max(a, b)
  const found = intersections.find((item) => item.members.length === 2 &&
    item.members[0] === low && item.members[1] === high)
  return found !== undefined ? found.size : 0
}


function _proportionalLayout(sets, intersections) {
  /*
   * Circles in data units: area = size, centre distances from the
   * pairwise intersection sizes.
   *
   * :returns: [{x, y, r}] one per set.
   */
  const circles = sets.map((set) => ({ x: 0, y: 0, r: Math.sqrt(Math.max(set.size, 0) / Math.PI) }))
  const count = circles.length
  if (count === 1) {
    return circles
  }

  /* Target distance of every pair. */
  const target = []
  for (let i = 0; i < count; i = i + 1) {
    target.push(new Array(count).fill(0))
  }
  for (let i = 0; i < count; i = i + 1) {
    for (let j = i + 1; j < count; j = j + 1) {
      const distance = _targetDistance(circles[i].r, circles[j].r, _pairSize(intersections, i, j))
      target[i][j] = distance
      target[j][i] = distance
    }
  }

  circles[1].x = target[0][1]
  if (count === 2) {
    return circles
  }

  /* Third centre by the law of cosines (clamped when inconsistent). */
  const d01 = Math.max(target[0][1], 1e-6)
  const d02 = target[0][2]
  const d12 = target[1][2]
  let cosine = (d01 * d01 + d02 * d02 - d12 * d12) / (2 * d01 * Math.max(d02, 1e-6))
  cosine = Math.max(-1, Math.min(1, cosine))
  circles[2].x = d02 * cosine
  circles[2].y = -d02 * Math.sqrt(1 - cosine * cosine)

  /* Least-squares relaxation of the pairwise distances. */
  const scale = Math.max(circles[0].r, circles[1].r, circles[2].r, 1e-6)
  for (let iter = 0; iter < 300; iter = iter + 1) {
    const moves = circles.map(() => ({ x: 0, y: 0 }))
    for (let i = 0; i < count; i = i + 1) {
      for (let j = i + 1; j < count; j = j + 1) {
        const dx = circles[j].x - circles[i].x
        const dy = circles[j].y - circles[i].y
        const distance = Math.max(Math.hypot(dx, dy), 1e-9)
        const error = (distance - target[i][j]) / distance
        moves[i].x = moves[i].x + dx * error * 0.25
        moves[i].y = moves[i].y + dy * error * 0.25
        moves[j].x = moves[j].x - dx * error * 0.25
        moves[j].y = moves[j].y - dy * error * 0.25
      }
    }
    let largest = 0
    for (let i = 0; i < count; i = i + 1) {
      circles[i].x = circles[i].x + moves[i].x
      circles[i].y = circles[i].y + moves[i].y
      largest = Math.max(largest, Math.abs(moves[i].x), Math.abs(moves[i].y))
    }
    if (largest < scale * 1e-5) {
      break
    }
  }
  return circles
}


function _schematicLayout(count) {
  /*
   * Equal circles in the classic arrangement (unit radius).
   */
  if (count === 1) {
    return [{ x: 0, y: 0, r: 1 }]
  }
  if (count === 2) {
    return [{ x: 0, y: 0, r: 1 }, { x: 1.1, y: 0, r: 1 }]
  }
  const side = 1.1
  return [
    { x: 0, y: 0, r: 1 },
    { x: side, y: 0, r: 1 },
    { x: side / 2, y: side * Math.sqrt(3) / 2, r: 1 }
  ]
}


function _fit(circles, width, height) {
  /*
   * Scale and centre data-unit circles into the drawing box.
   *
   * :returns: New [{x, y, r}] in pixels.
   */
  let minX = Infinity
  let minY = Infinity
  let maxX = -Infinity
  let maxY = -Infinity
  for (let i = 0; i < circles.length; i = i + 1) {
    const circle = circles[i]
    minX = Math.min(minX, circle.x - circle.r)
    minY = Math.min(minY, circle.y - circle.r)
    maxX = Math.max(maxX, circle.x + circle.r)
    maxY = Math.max(maxY, circle.y + circle.r)
  }
  const spanX = Math.max(maxX - minX, 1e-9)
  const spanY = Math.max(maxY - minY, 1e-9)
  const availableW = Math.max(width - PADDING * 2, 10)
  const availableH = Math.max(height - PADDING * 2, 10)
  const scale = Math.min(availableW / spanX, availableH / spanY)
  const offsetX = (width - spanX * scale) / 2 - minX * scale
  const offsetY = (height - spanY * scale) / 2 - minY * scale
  const fitted = circles.map((circle) => ({
    x: circle.x * scale + offsetX,
    y: circle.y * scale + offsetY,
    r: circle.r * scale
  }))
  return fitted
}


function _regionPoint(circles, members, strict) {
  /*
   * A point inside every member circle and (when strict) outside every
   * other circle, as far from the region's edges as a grid search finds.
   *
   * :returns: {x, y} or null when the region is empty.
   */
  let minX = -Infinity
  let maxX = Infinity
  let minY = -Infinity
  let maxY = Infinity
  for (let m = 0; m < members.length; m = m + 1) {
    const circle = circles[members[m]]
    minX = Math.max(minX, circle.x - circle.r)
    maxX = Math.min(maxX, circle.x + circle.r)
    minY = Math.max(minY, circle.y - circle.r)
    maxY = Math.min(maxY, circle.y + circle.r)
  }
  if (minX >= maxX || minY >= maxY) {
    return null
  }
  const steps = 36
  let best = null
  let bestMargin = 0
  for (let ix = 0; ix <= steps; ix = ix + 1) {
    for (let iy = 0; iy <= steps; iy = iy + 1) {
      const x = minX + (maxX - minX) * ix / steps
      const y = minY + (maxY - minY) * iy / steps
      let margin = Infinity
      for (let c = 0; c < circles.length; c = c + 1) {
        const distance = Math.hypot(x - circles[c].x, y - circles[c].y)
        if (members.indexOf(c) >= 0) {
          margin = Math.min(margin, circles[c].r - distance)
        } else if (strict === true) {
          margin = Math.min(margin, distance - circles[c].r)
        }
      }
      if (margin > bestMargin) {
        bestMargin = margin
        best = { x: x, y: y }
      }
    }
  }
  return best
}


export function render(ctx) {
  /*
   * Render a Venn or Euler diagram.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const data = _readSets(raw)
  const sets = data.sets
  const intersections = data.intersections
  const isEuler = ctx.type === "euler"
  const proportional = isEuler === true ? raw.proportional !== false : raw.proportional === true

  const root = svgEl("g", { part: "plot" }, [])

  const rows = sets.map((set) => [set.name, set.size])
  intersections.forEach((item) => {
    rows.push([item.names.join(" ∩ "), item.size])
  })
  ctx.setTable({ columns: ["Sets", "Size"], rows: rows, caption: ctx.label })

  if (sets.length === 0) {
    return root
  }

  if (sets.length > MAX_SETS) {
    ctx.emit("mj-chart-error", {
      message: "Venn / Euler diagrams support at most 3 sets. Consider using type=\"upset\" for 4+ sets."
    })
    ctx.setLegend([])
    root.appendChild(svgEl("text", {
      x: ctx.width / 2, y: ctx.height / 2, "text-anchor": "middle", "font-size": 13,
      fill: "var(--mj-text-muted, #5f6673)", part: "message"
    }, `${sets.length} sets are too many for a ${isEuler === true ? "Euler" : "Venn"} diagram; ` +
      "use type=\"upset\"."))
    return root
  }

  const layout = proportional === true
    ? _proportionalLayout(sets, intersections)
    : _schematicLayout(sets.length)
  /* An all-zero proportional layout has nothing to scale: draw it schematic. */
  const usable = layout.some((circle) => circle.r > 0)
  const circles = _fit(usable === true ? layout : _schematicLayout(sets.length), ctx.width, ctx.height)

  ctx.setLegend(sets.map((set, i) => ({ label: set.name, color: ctx.colorFor(i) })))

  /* Circles. */
  for (let i = 0; i < sets.length; i = i + 1) {
    const set = sets[i]
    const color = ctx.colorFor(i)
    const ariaLabel = `${set.name}: ${formatNumber(set.size)}`
    const circleEl = svgEl("g", {
      tabindex: "0", role: "img", "aria-label": ariaLabel, part: "venn-set"
    }, [])
    circleEl.appendChild(svgEl("circle", {
      cx: circles[i].x.toFixed(2),
      cy: circles[i].y.toFixed(2),
      r: Math.max(circles[i].r, 0).toFixed(2),
      fill: color, "fill-opacity": "0.25",
      stroke: color, "stroke-width": "1.5"
    }, []))
    circleEl.appendChild(svgEl("title", null, ariaLabel))

    const captured = set.source
    const handler = () => {
      ctx.emit("mj-chart-venn-click", { name: captured.name, size: captured.size })
    }
    circleEl.addEventListener("click", handler)
    circleEl.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        handler()
      }
    })
    root.appendChild(circleEl)
  }

  /* Labels, each inside its own region. */
  const labels = svgEl("g", { "aria-hidden": "true", "pointer-events": "none" }, [])
  root.appendChild(labels)

  for (let i = 0; i < sets.length; i = i + 1) {
    let point = _regionPoint(circles, [i], true)
    if (point === null) {
      /* Nested set: label at its centre. */
      point = { x: circles[i].x, y: circles[i].y }
    }
    labels.appendChild(svgEl("text", {
      x: point.x.toFixed(2), y: (point.y - 2).toFixed(2),
      "text-anchor": "middle", "font-size": 12, "font-weight": "600",
      fill: "var(--mj-text, #14181f)"
    }, sets[i].name))
    labels.appendChild(svgEl("text", {
      x: point.x.toFixed(2), y: (point.y + 12).toFixed(2),
      "text-anchor": "middle", "font-size": 11,
      fill: "var(--mj-text-muted, #5f6673)"
    }, formatNumber(sets[i].size)))
  }

  for (let k = 0; k < intersections.length; k = k + 1) {
    const item = intersections[k]
    /* A pair equal to its smaller set is containment: the set label says it. */
    const smallest = Math.min(...item.members.map((m) => sets[m].size))
    if (item.members.length === 2 && smallest > 0 && item.size >= smallest) {
      continue
    }
    let point = _regionPoint(circles, item.members, true)
    if (point === null) {
      point = _regionPoint(circles, item.members, false)
    }
    if (point === null) {
      continue
    }
    labels.appendChild(svgEl("text", {
      x: point.x.toFixed(2), y: (point.y + 4).toFixed(2),
      "text-anchor": "middle", "font-size": 11,
      fill: "var(--mj-text, #14181f)", part: "venn-intersection"
    }, formatNumber(item.size)))
  }

  return root
}


registerRenderer("venn", render)
registerRenderer("euler", render)
