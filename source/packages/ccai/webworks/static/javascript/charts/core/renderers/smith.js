/*
 * smith.js
 *
 * Smith chart renderer — RF impedance / reflection-coefficient chart.
 *
 * Registered types:
 *   "smith"  - normalized impedance chart with constant-r/x grid circles
 *
 * Data:
 *   {
 *     meta:   { z0: 50 },                         (reference impedance, ohms)
 *     mode:   "impedance" | "admittance" | "both",
 *     grid:   { rLines: [0, 0.2, ...], xLines: [0.2, 0.5, ...] },
 *     series: [{ name, points: [...] }]
 *   }
 *   A point is one of
 *     { r, x }                normalised impedance z = r + jx
 *     { R, X }                impedance in ohms, normalised by meta.z0
 *     { g, b }                normalised admittance y = g + jb
 *     { gamma_re, gamma_im }  reflection coefficient Γ (e.g. S11)
 *   plus an optional freq_hz. The admittance chart is the impedance grid
 *   rotated by 180° (Γ -> −Γ); "both" overlays the two grids. Points are
 *   always placed at their reflection coefficient, which is the same in
 *   every mode.
 *
 * Coordinate system:
 *   The reflection coefficient Γ = (z - 1) / (z + 1) maps the normalized
 *   impedance plane to the unit disk |Γ| ≤ 1.
 *   Constant-resistance circles: center = (r/(r+1), 0), radius = 1/(r+1);
 *   each is labelled where it crosses the real axis, Γ = (r−1)/(r+1).
 *   Constant-reactance arcs: center = (1, 1/x), radius = 1/|x|; each is
 *   labelled where it meets the unit circle, Γ = ((x²−1) + 2jx)/(x²+1).
 *
 * Renderer contract: render(ctx) -> SVGElement  (a <g> within [0..width]x[0..height])
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";

const DEFAULT_R_LINES = [0, 0.2, 0.5, 1, 2, 5];
const DEFAULT_X_LINES = [0.2, 0.5, 1, 2, 5];

/* Samples per reactance arc. */
const ARC_SAMPLES = 64;


/* ── helpers ──────────────────────────────────────────────────── */

function _isNumber(value) {
  /*
   * True for a finite number.
   */
  const numeric = typeof value === "number" && Number.isFinite(value) === true
  return numeric
}


function _zToGamma(r, x) {
  /*
   * Convert normalized impedance (r, x) to reflection coefficient (re, im).
   * Γ = (z - 1) / (z + 1)  where z = r + jx
   */
  const denom = (r + 1) * (r + 1) + x * x
  if (denom < 1e-12) {
    return { re: 1, im: 0 }
  }
  const re = ((r * r) + (x * x) - 1) / denom
  const im = (2 * x) / denom
  return { re: re, im: im }
}


function _pointGamma(point, z0) {
  /*
   * The reflection coefficient and normalised impedance of a data point,
   * or null when the point has no usable coordinates.
   */
  if (point === null || typeof point !== "object") {
    return null
  }
  let gamma = null
  if (_isNumber(point.gamma_re) === true && _isNumber(point.gamma_im) === true) {
    gamma = { re: point.gamma_re, im: point.gamma_im }
  } else if (_isNumber(point.r) === true && _isNumber(point.x) === true) {
    gamma = _zToGamma(point.r, point.x)
  } else if (_isNumber(point.R) === true && _isNumber(point.X) === true) {
    gamma = _zToGamma(point.R / z0, point.X / z0)
  } else if (_isNumber(point.g) === true && _isNumber(point.b) === true) {
    /* y = g + jb -> Γ = (1 - y) / (1 + y) = −Γ(y as if it were z). */
    const asZ = _zToGamma(point.g, point.b)
    gamma = { re: -asZ.re, im: -asZ.im }
  }
  if (gamma === null) {
    return null
  }
  /* z = (1 + Γ) / (1 - Γ) */
  const denom = (1 - gamma.re) * (1 - gamma.re) + gamma.im * gamma.im
  let z = null
  if (denom > 1e-12) {
    z = {
      r: (1 - gamma.re * gamma.re - gamma.im * gamma.im) / denom,
      x: (2 * gamma.im) / denom
    }
  }
  return { gamma: gamma, z: z }
}


function _numberLines(value, fallback) {
  /*
   * The finite numbers of a grid list, or the fallback when it is missing.
   */
  if (Array.isArray(value) === false) {
    return fallback
  }
  return value.filter((v) => _isNumber(v) === true)
}


function _attachActivation(element, ctx, eventName, detail) {
  /*
   * Emit an interaction event on click and on Enter / Space.
   */
  const handler = () => { ctx.emit(eventName, detail) }
  element.addEventListener("click", handler)
  element.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      handler()
    }
  })
  return
}


/* ── grid ─────────────────────────────────────────────────────── */

function _drawGrid(group, rLines, xLines, layout, flip, style) {
  /*
   * Draw one Smith grid: constant-r circles and constant-x arcs, with
   * labels. `flip` is -1 for the admittance grid (Γ -> −Γ).
   */
  const { cx, cy, diskR } = layout
  const toPx = (re, im) => ({ x: cx + flip * re * diskR, y: cy - flip * im * diskR })

  for (let i = 0; i < rLines.length; i = i + 1) {
    const r = rLines[i]
    if (r < 0) {
      continue
    }
    const center = toPx(r / (r + 1), 0)
    const radius = diskR / (r + 1)
    if (radius >= 1 && r > 0) {
      group.appendChild(svgEl("circle", {
        cx: center.x.toFixed(1), cy: center.y.toFixed(1), r: radius.toFixed(1),
        fill: "none", stroke: style.stroke, "stroke-width": 0.75,
        "stroke-dasharray": style.dash
      }, []))
    }
    if (style.labels === true) {
      /* Label where the circle crosses the real axis on the far side. */
      const crossing = toPx((r - 1) / (r + 1), 0)
      group.appendChild(svgEl("text", {
        x: (crossing.x + 2 * flip).toFixed(1), y: (crossing.y - 3).toFixed(1),
        "text-anchor": flip > 0 ? "start" : "end",
        "font-size": 8, fill: "var(--mj-text-muted, #5f6673)"
      }, formatNumber(r)))
    }
  }

  for (let i = 0; i < xLines.length; i = i + 1) {
    const magnitude = Math.abs(xLines[i])
    if (magnitude < 1e-9) {
      continue
    }
    for (const sign of [1, -1]) {
      const x = sign * magnitude
      /* Sample the arc from the unit circle (r = 0) to Γ = 1 (r -> ∞). */
      let data = ""
      for (let k = 0; k <= ARC_SAMPLES; k = k + 1) {
        const t = k / ARC_SAMPLES
        const gamma = t >= 1 ? { re: 1, im: 0 } : _zToGamma(t / (1 - t), x)
        const p = toPx(gamma.re, gamma.im)
        data = data + `${k === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)} `
      }
      group.appendChild(svgEl("path", {
        d: data.trim(), fill: "none", stroke: style.stroke, "stroke-width": 0.75,
        "stroke-dasharray": style.dash
      }, []))

      if (style.labels === true) {
        /* Label just outside the unit circle where the arc meets it. */
        const edge = { re: (x * x - 1) / (x * x + 1), im: (2 * x) / (x * x + 1) }
        const p = toPx(edge.re * 1.09, edge.im * 1.09)
        const anchor = Math.abs(p.x - cx) < diskR * 0.2 ? "middle" : (p.x > cx ? "start" : "end")
        group.appendChild(svgEl("text", {
          x: p.x.toFixed(1), y: (p.y + 3).toFixed(1),
          "text-anchor": anchor,
          "font-size": 8, fill: "var(--mj-text-muted, #5f6673)"
        }, `${x > 0 ? "+" : "−"}j${formatNumber(magnitude)}`))
      }
    }
  }
  return
}


/* ── main renderer ────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Render a Smith chart.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const root = svgEl("g", { part: "plot" }, [])
  const meta = ctx.model.meta

  const margin = 34
  const cx = ctx.width / 2
  const cy = ctx.height / 2
  const diskR = Math.min(cx, cy) - margin
  if (diskR < 10) {
    return root
  }
  const layout = { cx: cx, cy: cy, diskR: diskR }

  const mode = raw.mode === "admittance" || raw.mode === "both" ? raw.mode : "impedance"
  const z0 = _isNumber(meta.z0) === true && meta.z0 > 0 ? meta.z0 : 50
  const gridSource = raw.grid !== null && typeof raw.grid === "object" ? raw.grid : {}
  const rLines = _numberLines(gridSource.rLines, DEFAULT_R_LINES)
  const xLines = _numberLines(gridSource.xLines, DEFAULT_X_LINES)

  const grid = svgEl("g", { "aria-hidden": "true", part: "grid" }, [])
  grid.appendChild(svgEl("circle", {
    cx: cx.toFixed(1), cy: cy.toFixed(1), r: diskR.toFixed(1),
    fill: "var(--mj-bg-subtle, #f7f8fa)",
    stroke: "var(--mj-border-strong, #878e9c)",
    "stroke-width": 1.5
  }, []))
  grid.appendChild(svgEl("line", {
    x1: (cx - diskR).toFixed(1), y1: cy.toFixed(1),
    x2: (cx + diskR).toFixed(1), y2: cy.toFixed(1),
    stroke: "var(--mj-border-strong, #878e9c)", "stroke-width": 1
  }, []))

  const primary = { stroke: "var(--mj-border-strong, #878e9c)", dash: null, labels: true }
  if (mode === "both") {
    _drawGrid(grid, rLines, xLines, layout, 1, primary)
    _drawGrid(grid, rLines, xLines, layout, -1,
      { stroke: "var(--mj-accent, #2563eb)", dash: "3,2", labels: false })
  } else {
    _drawGrid(grid, rLines, xLines, layout, mode === "admittance" ? -1 : 1, primary)
  }
  grid.appendChild(svgEl("circle", {
    cx: cx.toFixed(1), cy: cy.toFixed(1), r: 2.5,
    fill: "var(--mj-border-strong, #878e9c)"
  }, []))
  root.appendChild(grid)

  const tableRows = []
  const series = ctx.model.series
  const digits = { maximumFractionDigits: 3 }

  for (let s = 0; s < series.length; s = s + 1) {
    const ser = series[s]
    const pts = Array.isArray(ser.points) === true ? ser.points : []
    if (pts.length === 0) { continue }
    const color = ctx.colorFor(ser.name)
    const group = svgEl("g", { part: "series", "data-series": ser.name }, [])
    const mapped = pts.map((p) => _pointGamma(p, z0))
    const pixPts = mapped.map((m) => (m === null ? null : { x: cx + m.gamma.re * diskR, y: cy - m.gamma.im * diskR }))

    /* Locus path; a point without coordinates is a gap. */
    let pathData = ""
    let pen = false
    for (let p = 0; p < pixPts.length; p = p + 1) {
      if (pixPts[p] === null) {
        pen = false
        continue
      }
      pathData = pathData + `${pen === true ? "L" : "M"}${pixPts[p].x.toFixed(1)},${pixPts[p].y.toFixed(1)} `
      pen = true
    }
    if (pathData.length > 0) {
      group.appendChild(svgEl("path", {
        d: pathData.trim(),
        fill: "none",
        stroke: color,
        "stroke-width": 2,
        part: "locus"
      }, []))
    }

    for (let p = 0; p < pts.length; p = p + 1) {
      const pt = pts[p]
      const m = mapped[p]
      if (m === null) {
        continue
      }
      const freq = _isNumber(pt.freq_hz) === true ? `${formatNumber(pt.freq_hz / 1e6)} MHz: ` : ""
      const zText = m.z !== null
        ? `z ${formatNumber(m.z.r, digits)}${m.z.x < 0 ? " − " : " + "}j${formatNumber(Math.abs(m.z.x), digits)}`
        : "z ∞"
      const label = `${ser.name}, ${freq}${zText}, Γ ${formatNumber(m.gamma.re, digits)}` +
        `${m.gamma.im < 0 ? " − " : " + "}j${formatNumber(Math.abs(m.gamma.im), digits)}`
      const dot = svgEl("circle", {
        cx: pixPts[p].x.toFixed(1), cy: pixPts[p].y.toFixed(1), r: 4,
        fill: color,
        stroke: "var(--mj-surface, #fff)",
        "stroke-width": 1,
        part: "point",
        tabindex: "0",
        role: "img",
        "aria-label": label
      }, [svgEl("title", null, label)])
      _attachActivation(dot, ctx, "mj-chart-smith-click", {
        series: ser.name,
        freq_hz: pt.freq_hz,
        r: m.z !== null ? m.z.r : null,
        x: m.z !== null ? m.z.x : null,
        gamma_re: m.gamma.re,
        gamma_im: m.gamma.im
      })
      group.appendChild(dot)
      tableRows.push([ser.name, _isNumber(pt.freq_hz) === true ? pt.freq_hz : "",
        m.z !== null ? m.z.r : "", m.z !== null ? m.z.x : "", m.gamma.re, m.gamma.im])
    }
    root.appendChild(group)
  }

  ctx.setTable({
    columns: ["Series", "Frequency (Hz)", "r", "x", "Γ real", "Γ imaginary"],
    rows: tableRows
  })
  return root
}


registerRenderer("smith", render)
