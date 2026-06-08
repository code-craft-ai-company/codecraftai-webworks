/*
 * beeswarm.js
 *
 * Beeswarm plot renderer — distributes individual observations as
 * non-overlapping dots along one axis using a greedy collision-avoidance
 * algorithm.  The perpendicular axis carries no semantic meaning.
 *
 * Registered types:
 *   "beeswarm"
 *
 * ctx.raw shape:
 *   raw.series   [{name, points:[{x?, y?, label?}]}]
 *   raw.radius   dot radius (default 4)
 *   raw.padding  gap between dots (default 1)
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber } from "../svgdraw.js";
import { linearScale, niceTicks } from "../scales.js";
import { extent } from "../svgdraw.js";


/* ── collision-avoidance placement ───────────────────────────────────── */

function _placeDots(sorted, radius, padding, perpCenter, perpMax) {
  /*
   * Greedy beeswarm placement.  Each dot is placed at the nearest
   * perpendicular offset (starting at perpCenter) that does not
   * intersect any already-placed dot.
   *
   * sorted: [{px (pixel along value axis), seriesName, label, value}]
   *
   * :returns: Array of {px, py, ...original fields}.
   */
  const gap     = radius * 2 + padding
  const placed  = []

  for (let i = 0; i < sorted.length; i = i + 1) {
    const dot = sorted[i]
    const px  = dot.px

    /* Try offsets: 0, ±gap, ±2gap … */
    let bestPy = perpCenter
    let found  = false
    let step   = 0

    while (found === false) {
      const candidates = step === 0
        ? [perpCenter]
        : [perpCenter - step * gap, perpCenter + step * gap]

      for (let ci = 0; ci < candidates.length; ci = ci + 1) {
        const py  = candidates[ci]
        const ok  = py - radius >= 0 && py + radius <= perpMax
        if (ok === false) {
          continue
        }
        let collision = false
        for (let j = 0; j < placed.length; j = j + 1) {
          const other = placed[j]
          const dx    = px - other.px
          const dy    = py - other.py
          const dist  = Math.sqrt(dx * dx + dy * dy)
          if (dist < gap) {
            collision = true
            break
          }
        }
        if (collision === false) {
          bestPy = py
          found  = true
          break
        }
      }

      step = step + 1
      if (step > 200) {
        /* Safety valve: just place overlapping rather than infinite loop */
        found = true
      }
    }

    placed.push({ px: px, py: bestPy, seriesName: dot.seriesName,
                  label: dot.label, value: dot.value })
  }

  return placed
}


/* ── renderer ─────────────────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Render a beeswarm plot.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw  = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])

  const series = (raw !== null && raw !== undefined && Array.isArray(raw.series))
    ? raw.series
    : []
  if (series.length === 0) {
    return root
  }

  /* Decide value axis from the data. The controller defaults orientation
   * to "vertical" so a 1-D beeswarm with only `x` values would otherwise
   * read undefined `y` and render nothing. Pick whichever axis the data
   * carries values for; an explicit `orientation="horizontal"` still
   * wins. */
  let sawX = false
  let sawY = false
  for (let s = 0; s < series.length; s = s + 1) {
    const pts = series[s].points || []
    for (let p = 0; p < pts.length; p = p + 1) {
      if (typeof pts[p].x === "number") { sawX = true }
      if (typeof pts[p].y === "number") { sawY = true }
    }
  }
  let horizontal
  if (ctx.orientation === "horizontal") {
    horizontal = true
  } else if (sawX === true && sawY === false) {
    horizontal = true
  } else {
    horizontal = false
  }
  const mode       = ctx.attrs("mode", "beeswarm")
  const radius     = (raw !== null && raw !== undefined && typeof raw.radius === "number")
    ? raw.radius
    : 4
  const padding    = (raw !== null && raw !== undefined && typeof raw.padding === "number")
    ? raw.padding
    : 1

  const margin = { top: 16, right: 16, bottom: 36, left: 52 }
  const plotW  = Math.max(ctx.width  - margin.left - margin.right,  10)
  const plotH  = Math.max(ctx.height - margin.top  - margin.bottom, 10)

  /* Collect all values across series for domain */
  const allValues = []
  for (let s = 0; s < series.length; s = s + 1) {
    const pts = series[s].points || []
    for (let p = 0; p < pts.length; p = p + 1) {
      const v = horizontal ? pts[p].x : pts[p].y
      if (typeof v === "number") {
        allValues.push(v)
      }
    }
  }

  if (allValues.length === 0) {
    return root
  }

  const domainExt = extent(allValues)
  let   lo        = domainExt[0]
  let   hi        = domainExt[1]
  if (lo === hi) {
    lo = lo - 1
    hi = hi + 1
  }

  /* Value axis (the one with semantic meaning) */
  const valueScale = horizontal
    ? linearScale([lo, hi], [0, plotW])
    : linearScale([lo, hi], [plotH, 0])

  const perpCenter = horizontal ? plotH / 2 : plotW / 2
  const perpMax    = horizontal ? plotH : plotW

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Gridlines + tick labels on the value axis */
  const ticks = niceTicks(lo, hi, 5)
  for (let t = 0; t < ticks.length; t = t + 1) {
    const tick  = ticks[t]
    const pixel = valueScale(tick)
    if (horizontal === true) {
      plot.appendChild(svgEl("line", {
        x1: pixel, y1: 0, x2: pixel, y2: plotH,
        stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
      }, []))
      plot.appendChild(svgEl("text", {
        x: pixel, y: plotH + 16,
        "text-anchor": "middle",
        "font-size": 11,
        fill: "var(--mj-text-muted, #6b7280)"
      }, formatNumber(tick)))
    } else {
      plot.appendChild(svgEl("line", {
        x1: 0, y1: pixel, x2: plotW, y2: pixel,
        stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
      }, []))
      plot.appendChild(svgEl("text", {
        x: -8, y: pixel + 4,
        "text-anchor": "end",
        "font-size": 11,
        fill: "var(--mj-text-muted, #6b7280)"
      }, formatNumber(tick)))
    }
  }

  /* Median / mean line (optional) */
  if (allValues.length > 0) {
    const sorted = allValues.slice().sort((a, b) => a - b)
    const mid    = sorted[Math.floor(sorted.length / 2)]
    const midPx  = valueScale(mid)
    if (horizontal === true) {
      plot.appendChild(svgEl("line", {
        x1: midPx, y1: 4, x2: midPx, y2: plotH - 4,
        stroke: "var(--mj-color-neutral-500, #6b7280)",
        "stroke-width": 1.5,
        "stroke-dasharray": "4 3"
      }, []))
    } else {
      plot.appendChild(svgEl("line", {
        x1: 4, y1: midPx, x2: plotW - 4, y2: midPx,
        stroke: "var(--mj-color-neutral-500, #6b7280)",
        "stroke-width": 1.5,
        "stroke-dasharray": "4 3"
      }, []))
    }
  }

  /* Collect dots and sort by value for stable placement */
  const allDots = []
  for (let s = 0; s < series.length; s = s + 1) {
    const ser  = series[s]
    const pts  = ser.points || []
    const color = ctx.colorFor(ser.name)
    for (let p = 0; p < pts.length; p = p + 1) {
      const pt  = pts[p]
      const val = horizontal ? pt.x : pt.y
      if (typeof val !== "number") {
        continue
      }
      const px = valueScale(val)
      allDots.push({
        px: px,
        seriesName: ser.name,
        color: color,
        label: pt.label || ser.name,
        value: val
      })
    }
  }

  allDots.sort((a, b) => a.px - b.px)

  let placed = null
  if (mode === "strip") {
    /* No jitter — place all at perpCenter */
    placed = allDots.map((dot) => ({
      px: dot.px, py: perpCenter,
      seriesName: dot.seriesName, color: dot.color,
      label: dot.label, value: dot.value
    }))
  } else {
    placed = _placeDots(allDots, radius, padding, perpCenter, perpMax)
    /* Reattach color after placement (placement doesn't carry color) */
    for (let i = 0; i < placed.length; i = i + 1) {
      placed[i].color = allDots[i].color
    }
  }

  /* Draw dots */
  for (let i = 0; i < placed.length; i = i + 1) {
    const dot = placed[i]
    const cx  = horizontal ? dot.px : dot.py
    const cy  = horizontal ? dot.py : dot.px

    const circle = svgEl("circle", {
      cx: cx, cy: cy, r: radius,
      fill: dot.color,
      "fill-opacity": "0.85"
    }, [])
    circle.setAttribute("part", "dot")
    circle.setAttribute("tabindex", "0")
    circle.setAttribute("role", "img")
    circle.setAttribute("aria-label",
      `${dot.seriesName}: ${formatNumber(dot.value)}`)
    circle.appendChild(svgEl("title", null,
      `${dot.label} — ${dot.seriesName}: ${formatNumber(dot.value)}`))
    const capturedDot = dot
    const handler = () => {
      ctx.emit("mj-chart-dot-click", {
        series: capturedDot.seriesName,
        value: capturedDot.value,
        label: capturedDot.label
      })
    }
    circle.addEventListener("click", handler)
    circle.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        handler()
      }
    })
    plot.appendChild(circle)
  }

  return root
}


registerRenderer("beeswarm", render)
