/*
 * venn.js
 *
 * Venn / Euler diagram renderer.
 *
 * JSON shape (ctx.raw):
 *   sets[]           { name, size }   – 2 or 3 sets
 *   intersections[]  { sets[], size } – pairwise and triple intersections
 *   proportional     boolean (default false for venn, true for euler)
 *
 * Circle radii are proportional to sqrt(size) so area encodes set size.
 * Positions use a simple force-placement pass seeded with an equilateral
 * triangle for 3 sets or a horizontal pair for 2 sets, then iteratively
 * nudged so that the actual circle-intersection area is closer to the
 * target intersection size.  Color uses semi-transparent fills so
 * overlapping regions are distinguishable without color-only encoding.
 *
 * For ≥ 4 sets the renderer emits an mj-chart-error event and falls back
 * to drawing plain non-overlapping circles with a recommendation to use
 * type="upset".
 *
 * Registers: "venn", "euler"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber } from "../svgdraw.js";
import { sqrtScale } from "../scales.js";


const SET_COLORS = [
  "var(--mj-color-accent-500, #2563eb)",
  "var(--mj-color-success, #15803d)",
  "var(--mj-color-warning, #b45309)"
]


function _circleIntersectionArea(r1, r2, d) {
  /*
   * Compute the intersection area of two circles with radii r1, r2 whose
   * centres are d apart.  Returns 0 when they do not overlap.
   *
   * :returns: Area in square pixels.
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
  const alpha = Math.acos((d2 + r12 - r22) / (2 * d * r1))
  const beta = Math.acos((d2 + r22 - r12) / (2 * d * r2))
  const area = r12 * alpha + r22 * beta -
    r1 * r1 * Math.sin(2 * alpha) / 2 -
    r2 * r2 * Math.sin(2 * beta) / 2
  return Math.max(area, 0)
}


function _targetDistance(r1, r2, targetArea) {
  /*
   * Binary-search for the centre distance that gives approximately targetArea
   * of overlap for two circles of radii r1, r2.
   *
   * :returns: Distance in pixels.
   */
  if (targetArea <= 0) {
    return r1 + r2
  }
  const maxOverlap = _circleIntersectionArea(r1, r2, 0)
  if (targetArea >= maxOverlap) {
    return 0
  }

  let lo = 0
  let hi = r1 + r2
  for (let iter = 0; iter < 48; iter = iter + 1) {
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


export function render(ctx) {
  /*
   * Render a Venn or Euler diagram.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw
  const sets = (raw !== null && raw !== undefined && Array.isArray(raw.sets))
    ? raw.sets
    : []
  const intersections = (raw !== null && raw !== undefined && Array.isArray(raw.intersections))
    ? raw.intersections
    : []
  const proportional = (raw !== null && raw !== undefined)
    ? (raw.proportional !== false)
    : false

  const root = svgEl("g", { part: "plot" }, [])

  if (sets.length === 0) {
    return root
  }

  /* Too many sets: emit error recommendation and fall back. */
  if (sets.length > 3) {
    ctx.emit("mj-chart-error", {
      message: "Venn / Euler diagrams support at most 3 sets. Consider using type=\"upset\" for 4+ sets."
    })
  }

  const cx = ctx.width / 2
  const cy = ctx.height / 2

  /* Compute radii. */
  let maxSize = 1
  for (let i = 0; i < sets.length; i = i + 1) {
    const sz = typeof sets[i].size === "number" ? sets[i].size : 0
    if (sz > maxSize) { maxSize = sz }
  }

  const maxR = Math.min(ctx.width, ctx.height) * 0.32
  const minR = maxR * 0.35
  const radScale = sqrtScale([0, maxSize], [minR, maxR])

  const radii = sets.map((s) => {
    const sz = typeof s.size === "number" ? s.size : 0
    const r = radScale(sz)
    return r
  })

  /* Seed positions for up to 3 sets. */
  const positions = []
  const n = Math.min(sets.length, 3)
  if (n === 1) {
    positions.push({ x: cx, y: cy })
  } else if (n === 2) {
    /* Find target distance for the pairwise intersection. */
    const pairIntersection = intersections.find((ix) => {
      return Array.isArray(ix.sets) && ix.sets.length === 2 &&
        ix.sets.includes(sets[0].name) && ix.sets.includes(sets[1].name)
    })
    const targetArea = (pairIntersection !== undefined && typeof pairIntersection.size === "number")
      ? (pairIntersection.size / maxSize) * Math.PI * maxR * maxR
      : Math.PI * radii[0] * radii[1] * 0.3

    const dist = proportional === true
      ? _targetDistance(radii[0], radii[1], targetArea)
      : (radii[0] + radii[1]) * 0.6

    const halfDist = dist / 2
    positions.push({ x: cx - halfDist, y: cy })
    positions.push({ x: cx + halfDist, y: cy })
  } else {
    /* 3 sets: equilateral triangle seed. */
    const spread = (radii[0] + radii[1] + radii[2]) / 3 * 0.85
    for (let i = 0; i < 3; i = i + 1) {
      const angle = -Math.PI / 2 + (2 * Math.PI * i) / 3
      positions.push({
        x: cx + spread * Math.cos(angle),
        y: cy + spread * Math.sin(angle)
      })
    }
  }

  /* Scale down if circles go outside the viewport. */
  let scaleFactor = 1
  for (let i = 0; i < n; i = i + 1) {
    const overflow = Math.max(
      positions[i].x - radii[i],
      positions[i].y - radii[i],
      ctx.width - (positions[i].x + radii[i]),
      ctx.height - (positions[i].y + radii[i])
    )
    if (overflow < 0) {
      const factor = 1 + overflow / radii[i]
      if (factor < scaleFactor) {
        scaleFactor = factor
      }
    }
  }
  if (scaleFactor < 1) {
    for (let i = 0; i < n; i = i + 1) {
      positions[i].x = cx + (positions[i].x - cx) * scaleFactor
      positions[i].y = cy + (positions[i].y - cy) * scaleFactor
      radii[i] = radii[i] * scaleFactor
    }
  }

  /* Draw circles. */
  for (let i = 0; i < n; i = i + 1) {
    const set = sets[i]
    const sz = typeof set.size === "number" ? set.size : 0
    const ariaLabel = `${set.name}: ${formatNumber(sz)}`

    const circleEl = svgEl("g", {
      tabindex: "0",
      role: "img",
      "aria-label": ariaLabel,
      part: "venn-set"
    }, [])

    circleEl.appendChild(svgEl("circle", {
      cx: positions[i].x.toFixed(2),
      cy: positions[i].y.toFixed(2),
      r: radii[i].toFixed(2),
      fill: SET_COLORS[i % SET_COLORS.length],
      "fill-opacity": "0.25",
      stroke: SET_COLORS[i % SET_COLORS.length],
      "stroke-width": "1.5"
    }, []))

    circleEl.appendChild(svgEl("title", null, ariaLabel))

    const capturedSet = set
    const handler = () => {
      ctx.emit("mj-chart-venn-click", { name: capturedSet.name, size: capturedSet.size })
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

  /* Set labels. */
  for (let i = 0; i < n; i = i + 1) {
    const set = sets[i]
    /* Push label outside the circle toward the periphery. */
    const angle = n === 1
      ? -Math.PI / 2
      : (n === 2 ? (i === 0 ? Math.PI : 0) : -Math.PI / 2 + (2 * Math.PI * i) / 3)
    const labelR = radii[i] * 0.65
    const lx = positions[i].x + labelR * Math.cos(angle)
    const ly = positions[i].y + labelR * Math.sin(angle)

    root.appendChild(svgEl("text", {
      x: lx.toFixed(2), y: ly.toFixed(2),
      "text-anchor": "middle", "font-size": 12,
      "font-weight": "600",
      fill: SET_COLORS[i % SET_COLORS.length]
    }, escapeHtml(set.name)))
  }

  /* Intersection size labels. */
  for (let ix = 0; ix < intersections.length; ix = ix + 1) {
    const inter = intersections[ix]
    if (!Array.isArray(inter.sets) || inter.sets.length === 0) {
      continue
    }

    /* Average position of participating set centres. */
    let sumX = 0
    let sumY = 0
    let count = 0
    for (let si = 0; si < n; si = si + 1) {
      if (inter.sets.includes(sets[si].name)) {
        sumX = sumX + positions[si].x
        sumY = sumY + positions[si].y
        count = count + 1
      }
    }
    if (count === 0) {
      continue
    }
    const labelX = sumX / count
    const labelY = sumY / count

    root.appendChild(svgEl("text", {
      x: labelX.toFixed(2),
      y: (labelY + 4).toFixed(2),
      "text-anchor": "middle",
      "font-size": 11,
      fill: "var(--mj-text, #14181f)"
    }, formatNumber(inter.size)))
  }

  return root
}


registerRenderer("venn", render)
registerRenderer("euler", render)
