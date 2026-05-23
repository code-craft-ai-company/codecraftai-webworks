/*
 * spiral.js
 *
 * Spiral chart renderer — maps time series data onto an Archimedean spiral
 * so that repeating cycles (day/week/year) align radially.
 *
 * Registered types:
 *   "spiral"
 *
 * ctx.raw shape:
 *   raw.cycle   "week" | "year" | "day"  (default "week")
 *   raw.series  [{name, points:[{t, value}]}]
 *
 * Archimedean spiral: r = a + b·θ
 *   a = inner radius,  b = radial band width / (2π)
 *   θ = time mapped to [0, N·2π]  where N = number of full cycles
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber } from "../svgdraw.js";
import { linearScale } from "../scales.js";
import { extent } from "../svgdraw.js";


/* ── cycle helpers ───────────────────────────────────────────────────── */

const CYCLE_MS = {
  day:  24 * 60 * 60 * 1000,
  week: 7  * 24 * 60 * 60 * 1000,
  year: 365.25 * 24 * 60 * 60 * 1000
}

const CYCLE_TICK_COUNT = {
  day:  24,
  week: 7,
  year: 12
}

const CYCLE_TICK_LABELS = {
  day:  ["12a","1a","2a","3a","4a","5a","6a","7a","8a","9a","10a","11a",
         "12p","1p","2p","3p","4p","5p","6p","7p","8p","9p","10p","11p"],
  week: ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],
  year: ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
}


function _toMs(t) {
  /*
   * Convert a time value to epoch milliseconds.
   */
  if (t instanceof Date) {
    return t.getTime()
  }
  if (typeof t === "number") {
    return t
  }
  return new Date(t).getTime()
}


/* ── renderer ─────────────────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Render a spiral chart.
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

  const cycle    = (raw !== null && raw !== undefined && raw.cycle) ? raw.cycle : "week"
  const cycleMs  = CYCLE_MS[cycle] || CYCLE_MS.week
  const mode     = ctx.attrs("mode", "line")

  const margin  = { top: 8, right: 8, bottom: 8, left: 8 }
  const plotW   = Math.max(ctx.width  - margin.left - margin.right,  10)
  const plotH   = Math.max(ctx.height - margin.top  - margin.bottom, 10)
  const cx      = plotW / 2
  const cy      = plotH / 2
  const maxR    = Math.min(cx, cy) * 0.92

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Collect all time-value pairs */
  const allTimes  = []
  const allValues = []
  for (let s = 0; s < series.length; s = s + 1) {
    const pts = series[s].points || []
    for (let p = 0; p < pts.length; p = p + 1) {
      const ms = _toMs(pts[p].t)
      if (isNaN(ms) === false) {
        allTimes.push(ms)
      }
      if (typeof pts[p].value === "number") {
        allValues.push(pts[p].value)
      }
    }
  }

  if (allTimes.length === 0) {
    return root
  }

  const tMin = Math.min(...allTimes)
  const tMax = Math.max(...allTimes)

  /* Number of full cycles spanned */
  const totalMs  = tMax - tMin || cycleMs
  const numCycles = Math.max(1, totalMs / cycleMs)

  /* Spiral parameters */
  const bandW = maxR / (numCycles + 1)
  const a     = bandW                          /* inner radius */
  const b     = bandW / (2 * Math.PI)          /* radial growth per radian */

  /* θ from time: map [tMin, tMax] → [0, numCycles * 2π] */
  const thetaScale = linearScale([tMin, tMax], [0, numCycles * 2 * Math.PI])

  /* Value scale for radial offset (mode="line") or stroke intensity */
  const valExt   = extent(allValues.length > 0 ? allValues : [0, 1])
  const valScale = linearScale(valExt, [0, bandW * 0.7])

  /* Radial tick labels */
  const tickCount  = CYCLE_TICK_COUNT[cycle] || 7
  const tickLabels = CYCLE_TICK_LABELS[cycle] || []
  for (let ti = 0; ti < tickCount; ti = ti + 1) {
    const angle  = (ti / tickCount) * 2 * Math.PI - Math.PI / 2
    const labelR = maxR + 12
    const lx     = cx + labelR * Math.cos(angle)
    const ly     = cy + labelR * Math.sin(angle)
    const label  = tickLabels[ti] || String(ti)
    plot.appendChild(svgEl("text", {
      x: lx, y: ly,
      "text-anchor": "middle",
      "dominant-baseline": "middle",
      "font-size": 9,
      fill: "var(--mj-text-muted, #6b7280)"
    }, label))

    /* Spoke */
    const spokeX = cx + maxR * Math.cos(angle)
    const spokeY = cy + maxR * Math.sin(angle)
    plot.appendChild(svgEl("line", {
      x1: cx, y1: cy, x2: spokeX, y2: spokeY,
      stroke: "var(--mj-border, #e0e3e9)",
      "stroke-width": 0.5,
      "pointer-events": "none"
    }, []))
  }

  /* Centre dot */
  plot.appendChild(svgEl("circle", {
    cx: cx, cy: cy, r: 3,
    fill: "var(--mj-text-muted, #6b7280)",
    "pointer-events": "none"
  }, []))

  /* Draw each series */
  for (let s = 0; s < series.length; s = s + 1) {
    const ser   = series[s]
    const pts   = ser.points || []
    const color = ctx.colorFor(ser.name)

    /* Sort points by time */
    const sortedPts = pts.slice().sort((pa, pb) => _toMs(pa.t) - _toMs(pb.t))

    if (mode === "bar") {
      /* Radial bar wedges */
      for (let p = 0; p < sortedPts.length; p = p + 1) {
        const pt  = sortedPts[p]
        const ms  = _toMs(pt.t)
        const theta = thetaScale(ms)
        const r     = a + b * theta
        const angle = theta - Math.PI / 2
        const barR  = typeof pt.value === "number" ? valScale(pt.value) : 0
        const x1 = cx + r * Math.cos(angle)
        const y1 = cy + r * Math.sin(angle)
        const x2 = cx + (r + barR) * Math.cos(angle)
        const y2 = cy + (r + barR) * Math.sin(angle)

        const barEl = svgEl("line", {
          x1: x1, y1: y1, x2: x2, y2: y2,
          stroke: color,
          "stroke-width": 2,
          "stroke-linecap": "round"
        }, [])
        barEl.setAttribute("part", "bar")
        barEl.setAttribute("tabindex", "0")
        barEl.setAttribute("role", "img")
        barEl.setAttribute("aria-label",
          `${ser.name}: ${formatNumber(pt.value)}`)
        barEl.appendChild(svgEl("title", null,
          `${ser.name} at ${pt.t}: ${formatNumber(pt.value)}`))
        const capturedPt = pt
        const capturedSer = ser.name
        const handler = () => {
          ctx.emit("mj-chart-bar-click", {
            series: capturedSer, t: capturedPt.t, value: capturedPt.value
          })
        }
        barEl.addEventListener("click", handler)
        barEl.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault()
            handler()
          }
        })
        plot.appendChild(barEl)
      }
    } else {
      /* Line path along the spiral, optionally offset by value */
      let pathD = ""
      for (let p = 0; p < sortedPts.length; p = p + 1) {
        const pt    = sortedPts[p]
        const ms    = _toMs(pt.t)
        const theta = thetaScale(ms)
        const rBase = a + b * theta
        const rOffset = typeof pt.value === "number" ? valScale(pt.value) : 0
        const r     = rBase + rOffset
        const angle = theta - Math.PI / 2
        const px    = cx + r * Math.cos(angle)
        const py    = cy + r * Math.sin(angle)
        const cmd   = p === 0 ? "M" : "L"
        pathD = pathD + `${cmd}${px.toFixed(2)},${py.toFixed(2)} `
      }

      if (pathD !== "") {
        const pathEl = svgEl("path", {
          d: pathD.trim(),
          fill: "none",
          stroke: color,
          "stroke-width": 2,
          "stroke-linecap": "round",
          "stroke-linejoin": "round"
        }, [])
        pathEl.setAttribute("part", "line")
        pathEl.setAttribute("tabindex", "0")
        pathEl.setAttribute("role", "img")
        pathEl.setAttribute("aria-label", escapeHtml(ser.name))
        pathEl.appendChild(svgEl("title", null, ser.name))
        const capturedName = ser.name
        const handler = () => {
          ctx.emit("mj-chart-series-click", { series: capturedName })
        }
        pathEl.addEventListener("click", handler)
        pathEl.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault()
            handler()
          }
        })
        plot.appendChild(pathEl)
      }
    }
  }

  return root
}


registerRenderer("spiral", render)
