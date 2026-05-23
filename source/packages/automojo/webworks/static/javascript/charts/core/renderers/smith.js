/*
 * smith.js
 *
 * Smith chart renderer — RF impedance / reflection-coefficient chart.
 *
 * Registered types:
 *   "smith"  - normalized impedance chart with constant-r/x grid circles
 *
 * Renderer contract: render(ctx) -> SVGElement  (a <g> within [0..width]x[0..height])
 *
 * Coordinate system:
 *   The reflection coefficient Γ = (Z/Z0 - 1) / (Z/Z0 + 1)
 *   maps the normalized impedance plane to the unit disk |Γ| ≤ 1.
 *   Center of the unit disk maps to Γ = (0, 0) → normalized Z = 1 + 0j.
 *   Constant-resistance circles: center = (r/(r+1), 0), radius = 1/(r+1)
 *   Constant-reactance circles:  center = (1, 1/x),    radius = 1/|x|
 *   All coordinates are in the Γ-plane before mapping to pixels.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber } from "../svgdraw.js";


/* ── Γ-plane to pixel mapping ─────────────────────────────────── */

function _gammaToPixel(re, im, cx, cy, diskR) {
  /*
   * Map a reflection-coefficient (re, im) to SVG pixel coordinates.
   * The unit disk is centered at (cx, cy) with radius diskR.
   */
  return {
    x: cx + re * diskR,
    y: cy - im * diskR   /* SVG y-axis is inverted */
  }
}


/* ── impedance to Γ ───────────────────────────────────────────── */

function _zToGamma(r, x) {
  /*
   * Convert normalized impedance (r, x) to reflection coefficient (re, im).
   * Γ = (Z - 1) / (Z + 1)  where Z = r + jx
   */
  const denom = (r + 1) * (r + 1) + x * x
  if (denom < 1e-12) {
    return { re: 1, im: 0 }
  }
  const re = ((r * r) + (x * x) - 1) / denom
  const im = (2 * x) / denom
  return { re: re, im: im }
}


/* ── constant-resistance circle ───────────────────────────────── */

function _drawRCircle(plot, r, cx, cy, diskR, color, label) {
  /*
   * Draw a constant-resistance circle in the Γ-plane (all in pixel space).
   * Center in Γ: (r/(r+1), 0), radius: 1/(r+1)
   */
  const gammaCenter = r / (r + 1)
  const gammaRadius = 1 / (r + 1)

  const pcx = cx + gammaCenter * diskR
  const pcy = cy   /* im = 0 → no vertical offset */
  const pr = gammaRadius * diskR

  if (pr < 1) {
    return
  }

  plot.appendChild(svgEl("circle", {
    cx: pcx.toFixed(1), cy: pcy.toFixed(1), r: pr.toFixed(1),
    fill: "none",
    stroke: color,
    "stroke-width": 0.7
  }, []))

  if (label !== null && label !== undefined) {
    plot.appendChild(svgEl("text", {
      x: (pcx + pr).toFixed(1), y: (pcy + 10).toFixed(1),
      "font-size": 8,
      fill: "var(--mj-text-muted, #6b7280)"
    }, label))
  }
  return
}


/* ── constant-reactance arc ───────────────────────────────────── */

function _drawXArc(plot, x, cx, cy, diskR, color, clipId, label) {
  /*
   * Draw the portion of a constant-reactance circle inside the unit disk.
   * Circle center in Γ: (1, 1/x), radius: 1/|x|
   * Rendered as a full SVG circle clipped to the unit disk.
   */
  if (Math.abs(x) < 1e-6) {
    return
  }

  const gammaCy = 1 / x
  const gammaRadius = Math.abs(1 / x)

  const pcx = cx + 1 * diskR        /* Γ_re = 1 → rightmost point of unit disk */
  const pcy = cy - gammaCy * diskR   /* SVG y-inverted */
  const pr = gammaRadius * diskR

  if (pr < 1) {
    return
  }

  const circEl = svgEl("circle", {
    cx: pcx.toFixed(1), cy: pcy.toFixed(1), r: pr.toFixed(1),
    fill: "none",
    stroke: color,
    "stroke-width": 0.7,
    "clip-path": `url(#${clipId})`
  }, [])
  plot.appendChild(circEl)

  if (label !== null && label !== undefined && x > 0) {
    /* Label near the upper arc */
    const labelAngle = Math.PI * 0.1  /* small angle from rightmost */
    const lx = pcx + Math.cos(labelAngle) * pr
    const ly = pcy - Math.sin(labelAngle) * pr
    plot.appendChild(svgEl("text", {
      x: lx.toFixed(1), y: ly.toFixed(1),
      "font-size": 8,
      fill: "var(--mj-text-muted, #6b7280)"
    }, label))
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
  const raw = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])

  const margin = 40
  const cx = ctx.width / 2
  const cy = ctx.height / 2
  const diskR = Math.min(cx, cy) - margin

  if (diskR < 10) {
    return root
  }

  const mode = (raw !== null && raw !== undefined && raw.mode === "admittance")
    ? "admittance" : "impedance"

  /* clipPath for reactance arcs */
  const clipId = "smith-clip-" + Math.floor(Math.random() * 1e6)
  const defs = svgEl("defs", null, [])
  const clipPath = svgEl("clipPath", { id: clipId }, [])
  clipPath.appendChild(svgEl("circle", {
    cx: cx.toFixed(1), cy: cy.toFixed(1), r: (diskR - 0.5).toFixed(1)
  }, []))
  defs.appendChild(clipPath)
  root.appendChild(defs)

  /* Outer unit-circle boundary */
  root.appendChild(svgEl("circle", {
    cx: cx.toFixed(1), cy: cy.toFixed(1), r: diskR.toFixed(1),
    fill: "var(--mj-surface-subtle, #f7f8fa)",
    stroke: "var(--mj-border-strong, #c7ccd6)",
    "stroke-width": 1.5
  }, []))

  /* Real-axis line (Im = 0) */
  root.appendChild(svgEl("line", {
    x1: (cx - diskR).toFixed(1), y1: cy.toFixed(1),
    x2: (cx + diskR).toFixed(1), y2: cy.toFixed(1),
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1
  }, []))

  /* Grid definitions */
  const rLines = (raw !== null && raw !== undefined &&
    raw.grid !== null && raw.grid !== undefined &&
    raw.grid.rLines !== null)
    ? raw.grid.rLines : [0, 0.2, 0.5, 1, 2, 5]

  const xLines = (raw !== null && raw !== undefined &&
    raw.grid !== null && raw.grid !== undefined &&
    raw.grid.xLines !== null)
    ? raw.grid.xLines : [0.2, 0.5, 1, 2, 5]

  const rColor = "var(--mj-color-accent-300, #80a8ff)"
  const xColor = "var(--mj-color-success, #15803d)"

  /* Constant-resistance circles */
  for (let i = 0; i < rLines.length; i = i + 1) {
    const r = rLines[i]
    if (typeof r !== "number" || r < 0) { continue }
    _drawRCircle(root, r, cx, cy, diskR, rColor, formatNumber(r))
  }

  /* Constant-reactance arcs (positive and negative) */
  for (let i = 0; i < xLines.length; i = i + 1) {
    const xVal = xLines[i]
    if (typeof xVal !== "number" || xVal === 0) { continue }
    _drawXArc(root, xVal, cx, cy, diskR, xColor, clipId,
      "j" + formatNumber(xVal))
    _drawXArc(root, -xVal, cx, cy, diskR, xColor, clipId, null)
  }

  /* Center crosshair mark */
  root.appendChild(svgEl("circle", {
    cx: cx.toFixed(1), cy: cy.toFixed(1), r: 3,
    fill: "var(--mj-border-strong, #c7ccd6)"
  }, []))

  /* Axis labels */
  root.appendChild(svgEl("text", {
    x: (cx + diskR + 4).toFixed(1), y: (cy + 4).toFixed(1),
    "font-size": 9, fill: "var(--mj-text-muted, #6b7280)"
  }, "Re"))
  root.appendChild(svgEl("text", {
    x: cx.toFixed(1), y: (cy - diskR - 6).toFixed(1),
    "text-anchor": "middle", "font-size": 9,
    fill: "var(--mj-text-muted, #6b7280)"
  }, "+jIm"))

  /* Data series */
  const series = (raw !== null && raw !== undefined &&
    raw.series !== null && raw.series !== undefined)
    ? raw.series : []

  for (let s = 0; s < series.length; s = s + 1) {
    const ser = series[s]
    const pts = ser.points
    if (pts === null || pts === undefined || pts.length === 0) { continue }
    const color = ctx.colorFor(ser.name)

    const pixPts = pts.map((p) => {
      const gamma = _zToGamma(p.r, p.x)
      return _gammaToPixel(gamma.re, gamma.im, cx, cy, diskR)
    })

    /* Locus path */
    let pathData = "M" + pixPts[0].x.toFixed(1) + "," + pixPts[0].y.toFixed(1)
    for (let p = 1; p < pixPts.length; p = p + 1) {
      pathData = pathData + " L" + pixPts[p].x.toFixed(1) + "," + pixPts[p].y.toFixed(1)
    }
    root.appendChild(svgEl("path", {
      d: pathData,
      fill: "none",
      stroke: color,
      "stroke-width": 2,
      part: "locus"
    }, []))

    /* Interactive point markers */
    for (let p = 0; p < pts.length; p = p + 1) {
      const pt = pts[p]
      const px2 = pixPts[p]
      const gamma = _zToGamma(pt.r, pt.x)
      const label = escapeHtml(
        ser.name + " r=" + formatNumber(pt.r) + " x=" + formatNumber(pt.x) +
        " Γ=(" + formatNumber(gamma.re) + "," + formatNumber(gamma.im) + ")" +
        (pt.freq_hz !== undefined
          ? " f=" + formatNumber(pt.freq_hz / 1e6) + "MHz" : "")
      )
      const dot = svgEl("circle", {
        cx: px2.x.toFixed(1), cy: px2.y.toFixed(1), r: 4,
        fill: color,
        stroke: "var(--mj-surface, #fff)",
        "stroke-width": 1,
        part: "point",
        tabindex: "0",
        role: "img",
        "aria-label": label
      }, [])
      dot.appendChild(svgEl("title", null, label))
      const detail = {
        series: ser.name,
        freq_hz: pt.freq_hz,
        r: pt.r, x: pt.x,
        gamma_re: gamma.re, gamma_im: gamma.im
      }
      const handler = () => { ctx.emit("mj-chart-smith-click", detail) }
      dot.addEventListener("click", handler)
      dot.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })
      root.appendChild(dot)
    }
  }

  return root
}


registerRenderer("smith", render)
