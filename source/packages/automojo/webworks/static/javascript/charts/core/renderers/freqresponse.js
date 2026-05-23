/*
 * freqresponse.js
 *
 * Frequency-response chart renderers (Nyquist and Bode).
 *
 * Registered types:
 *   "nyquist"  - Nyquist plot: complex-plane locus Re vs Im
 *   "bode"     - Bode diagram: stacked magnitude (dB) and phase (deg) panels
 *
 * Renderer contract: render(ctx) -> SVGElement  (a <g> within [0..width]x[0..height])
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber, linePath } from "../svgdraw.js";
import { linearScale, logScale, niceTicks } from "../scales.js";


/* ── shared axis helpers ──────────────────────────────────────── */

function _hGridLines(plot, plotW, plotH, yScale, ticks) {
  for (let i = 0; i < ticks.length; i = i + 1) {
    const py = yScale(ticks[i])
    plot.appendChild(svgEl("line", {
      x1: 0, y1: py, x2: plotW, y2: py,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    plot.appendChild(svgEl("text", {
      x: -6, y: py + 4, "text-anchor": "end",
      "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(ticks[i])))
  }
  return
}

function _vGridLines(plot, plotW, plotH, xScale, ticks, logLabels) {
  for (let i = 0; i < ticks.length; i = i + 1) {
    const px = xScale(ticks[i])
    plot.appendChild(svgEl("line", {
      x1: px, y1: 0, x2: px, y2: plotH,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    const label = logLabels === true
      ? "10" + _superscript(Math.round(Math.log10(ticks[i])))
      : formatNumber(ticks[i])
    plot.appendChild(svgEl("text", {
      x: px, y: plotH + 14, "text-anchor": "middle",
      "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, label))
  }
  return
}

function _superscript(exp) {
  const map = {
    "-": "⁻", "0": "⁰", "1": "¹", "2": "²", "3": "³",
    "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹"
  }
  const s = String(exp)
  let result = ""
  for (let i = 0; i < s.length; i = i + 1) {
    result = result + (map[s[i]] || s[i])
  }
  return result
}


/* ── arrowhead for Nyquist direction ticks ────────────────────── */

function _arrowhead(x, y, angle, size, color) {
  const tip = { x: x + Math.cos(angle) * size, y: y + Math.sin(angle) * size }
  const left = {
    x: x + Math.cos(angle + Math.PI * 0.8) * size * 0.5,
    y: y + Math.sin(angle + Math.PI * 0.8) * size * 0.5
  }
  const right = {
    x: x + Math.cos(angle - Math.PI * 0.8) * size * 0.5,
    y: y + Math.sin(angle - Math.PI * 0.8) * size * 0.5
  }
  const pts = `${tip.x.toFixed(1)},${tip.y.toFixed(1)} ` +
    `${left.x.toFixed(1)},${left.y.toFixed(1)} ` +
    `${right.x.toFixed(1)},${right.y.toFixed(1)}`
  return svgEl("polygon", { points: pts, fill: color }, [])
}


/* ── Nyquist renderer ─────────────────────────────────────────── */

function _renderNyquist(ctx) {
  /*
   * Render a Nyquist (complex-plane frequency-response) plot.
   */
  const raw = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])

  if (raw === null || raw === undefined) {
    return root
  }

  const series = (raw.series !== null && raw.series !== undefined) ? raw.series : []
  if (series.length === 0) {
    return root
  }

  const margin = { top: 24, right: 24, bottom: 46, left: 58 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  /* Find Re/Im extents across all series */
  let reMin = Infinity; let reMax = -Infinity
  let imMin = Infinity; let imMax = -Infinity

  for (let s = 0; s < series.length; s = s + 1) {
    const pts = series[s].points
    if (pts === null || pts === undefined) { continue }
    for (let p = 0; p < pts.length; p = p + 1) {
      if (pts[p].re < reMin) { reMin = pts[p].re }
      if (pts[p].re > reMax) { reMax = pts[p].re }
      if (pts[p].im < imMin) { imMin = pts[p].im }
      if (pts[p].im > imMax) { imMax = pts[p].im }
    }
  }

  /* Include critical point in domain */
  const crit = (raw.criticalPoint !== null && raw.criticalPoint !== undefined)
    ? raw.criticalPoint : { re: -1, im: 0 }
  if (crit.re < reMin) { reMin = crit.re }
  if (crit.re > reMax) { reMax = crit.re }
  if (crit.im < imMin) { imMin = crit.im }
  if (crit.im > imMax) { imMax = crit.im }

  /* Symmetric Im domain for mirror */
  const imAbsMax = Math.max(Math.abs(imMin), Math.abs(imMax))
  imMin = -imAbsMax
  imMax = imAbsMax

  if (reMin === Infinity) { reMin = -2; reMax = 2; imMin = -2; imMax = 2 }
  if (reMin === reMax) { reMax = reMin + 1 }
  if (imMin === imMax) { imMax = imMin + 1 }

  const rePad = (reMax - reMin) * 0.1
  const imPad = (imMax - imMin) * 0.1
  const xScale = linearScale([reMin - rePad, reMax + rePad], [0, plotW])
  const yScale = linearScale([imMin - imPad, imMax + imPad], [plotH, 0])

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Grid */
  const reTicks = niceTicks(reMin - rePad, reMax + rePad, 6)
  const imTicks = niceTicks(imMin - imPad, imMax + imPad, 6)
  _vGridLines(plot, plotW, plotH, xScale, reTicks, false)
  _hGridLines(plot, plotW, plotH, yScale, imTicks)

  /* Axes through origin */
  const ox = xScale(0)
  const oy = yScale(0)
  plot.appendChild(svgEl("line", {
    x1: ox, y1: 0, x2: ox, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))
  plot.appendChild(svgEl("line", {
    x1: 0, y1: oy, x2: plotW, y2: oy,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))

  /* Axis labels */
  const meta = (raw.meta !== null && raw.meta !== undefined) ? raw.meta : null
  const xLabel = (meta !== null && meta.xLabel) ? meta.xLabel : "Re(H)"
  const yLabel = (meta !== null && meta.yLabel) ? meta.yLabel : "Im(H)"
  plot.appendChild(svgEl("text", {
    x: plotW / 2, y: plotH + 32, "text-anchor": "middle",
    "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
  }, escapeHtml(xLabel)))
  plot.appendChild(svgEl("text", {
    transform: `rotate(-90) translate(${-plotH / 2}, -40)`,
    "text-anchor": "middle",
    "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
  }, escapeHtml(yLabel)))

  /* Unit circle if requested */
  if (ctx.attrs("showUnitCircle", "false") === "true") {
    const r1px = Math.abs(xScale(1) - xScale(0))
    plot.appendChild(svgEl("circle", {
      cx: ox, cy: oy, r: r1px,
      fill: "none",
      stroke: "var(--mj-border, #e0e3e9)",
      "stroke-width": 1,
      "stroke-dasharray": "4,3"
    }, []))
  }

  /* Series loci */
  for (let s = 0; s < series.length; s = s + 1) {
    const ser = series[s]
    const pts = ser.points
    if (pts === null || pts === undefined || pts.length === 0) { continue }
    const color = ctx.colorFor(ser.name)

    /* Forward locus */
    const pixPts = pts.map((p) => ({ x: xScale(p.re), y: yScale(p.im) }))
    const pathData = linePath(pixPts)
    if (pathData !== "") {
      const pathEl = svgEl("path", {
        d: pathData,
        fill: "none",
        stroke: color,
        "stroke-width": 2,
        part: "locus"
      }, [])
      plot.appendChild(pathEl)

      /* Direction arrow at ~1/3 along path */
      const idx = Math.floor(pts.length / 3)
      if (idx > 0 && idx < pixPts.length) {
        const p0 = pixPts[idx - 1]
        const p1 = pixPts[idx]
        const angle = Math.atan2(p1.y - p0.y, p1.x - p0.x)
        plot.appendChild(_arrowhead(p1.x, p1.y, angle, 6, color))
      }
    }

    /* Mirror (conjugate, negative-frequency locus) */
    if (ser.mirror === true) {
      const mirrorPts = pts.map((p) => ({ x: xScale(p.re), y: yScale(-p.im) }))
      const mirrorPath = linePath(mirrorPts)
      if (mirrorPath !== "") {
        plot.appendChild(svgEl("path", {
          d: mirrorPath,
          fill: "none",
          stroke: color,
          "stroke-width": 1.5,
          "stroke-dasharray": "5,3",
          part: "locus-mirror"
        }, []))
      }
    }

    /* Interactive point markers */
    for (let p = 0; p < pts.length; p = p + 1) {
      const pt = pts[p]
      const px2 = pixPts[p]
      const label = escapeHtml(
        ser.name + " ω=" + formatNumber(pt.omega) +
        " re=" + formatNumber(pt.re) +
        " im=" + formatNumber(pt.im)
      )
      const dot = svgEl("circle", {
        cx: px2.x.toFixed(1), cy: px2.y.toFixed(1), r: 3,
        fill: color,
        part: "point",
        tabindex: "0",
        role: "img",
        "aria-label": label
      }, [])
      dot.appendChild(svgEl("title", null, label))
      const detail = { series: ser.name, omega: pt.omega, re: pt.re, im: pt.im }
      const handler = () => { ctx.emit("mj-chart-nyquist-click", detail) }
      dot.addEventListener("click", handler)
      dot.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })
      plot.appendChild(dot)
    }
  }

  /* Critical point marker */
  const cpx = xScale(crit.re)
  const cpy = yScale(crit.im)
  plot.appendChild(svgEl("circle", {
    cx: cpx.toFixed(1), cy: cpy.toFixed(1), r: 6,
    fill: "none",
    stroke: "var(--mj-color-danger, #b91c1c)",
    "stroke-width": 2,
    part: "critical-point"
  }, []))
  plot.appendChild(svgEl("text", {
    x: (cpx + 8).toFixed(1), y: (cpy - 6).toFixed(1),
    "font-size": 10,
    fill: "var(--mj-color-danger, #b91c1c)"
  }, "−1+0j"))

  return root
}


/* ── Bode renderer ────────────────────────────────────────────── */

function _renderBode(ctx) {
  /*
   * Render a Bode plot: magnitude (dB) and phase (deg) stacked panels.
   */
  const raw = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])

  if (raw === null || raw === undefined) {
    return root
  }

  const series = (raw.series !== null && raw.series !== undefined) ? raw.series : []
  if (series.length === 0) {
    return root
  }

  const margin = { top: 16, right: 24, bottom: 40, left: 58 }
  const gapBetweenPanels = 20
  const totalH = Math.max(ctx.height - margin.top - margin.bottom - gapBetweenPanels, 20)
  const panelH = Math.floor(totalH / 2)
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)

  /* Collect omega, magnitude_db, phase_deg extents */
  let omegaMin = Infinity; let omegaMax = -Infinity
  let dbMin = Infinity; let dbMax = -Infinity
  let degMin = Infinity; let degMax = -Infinity

  for (let s = 0; s < series.length; s = s + 1) {
    const pts = series[s].points
    if (pts === null || pts === undefined) { continue }
    for (let p = 0; p < pts.length; p = p + 1) {
      const pt = pts[p]
      if (pt.omega > 0 && pt.omega < omegaMin) { omegaMin = pt.omega }
      if (pt.omega > omegaMax) { omegaMax = pt.omega }
      if (typeof pt.magnitude_db === "number") {
        if (pt.magnitude_db < dbMin) { dbMin = pt.magnitude_db }
        if (pt.magnitude_db > dbMax) { dbMax = pt.magnitude_db }
      }
      if (typeof pt.phase_deg === "number") {
        if (pt.phase_deg < degMin) { degMin = pt.phase_deg }
        if (pt.phase_deg > degMax) { degMax = pt.phase_deg }
      }
    }
  }
  if (omegaMin === Infinity) { omegaMin = 0.1; omegaMax = 100 }
  if (omegaMin <= 0) { omegaMin = 1e-3 }
  if (omegaMin === omegaMax) { omegaMax = omegaMin * 100 }
  if (dbMin === Infinity) { dbMin = -60; dbMax = 20 }
  if (dbMin === dbMax) { dbMax = dbMin + 1 }
  if (degMin === Infinity) { degMin = -180; degMax = 0 }
  if (degMin === degMax) { degMax = degMin + 1 }

  const xScale = logScale([omegaMin, omegaMax], [0, plotW])
  const magScale = linearScale([dbMin, dbMax], [panelH, 0])
  const phScale = linearScale([degMin, degMax], [panelH, 0])

  const magPanel = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(magPanel)

  const phPanel = svgEl("g", {
    transform: `translate(${margin.left},${margin.top + panelH + gapBetweenPanels})`
  }, [])
  root.appendChild(phPanel)

  /* Shared x-axis grid (log-frequency) */
  const xTicks = xScale.ticks(6)
  for (let i = 0; i < xTicks.length; i = i + 1) {
    const px = xScale(xTicks[i])
    magPanel.appendChild(svgEl("line", {
      x1: px, y1: 0, x2: px, y2: panelH,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    phPanel.appendChild(svgEl("line", {
      x1: px, y1: 0, x2: px, y2: panelH,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    phPanel.appendChild(svgEl("text", {
      x: px, y: panelH + 14, "text-anchor": "middle",
      "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, "10" + _superscript(Math.round(Math.log10(xTicks[i])))))
  }

  /* Magnitude panel y-grid */
  const dbTicks = niceTicks(dbMin, dbMax, 5)
  _hGridLines(magPanel, plotW, panelH, magScale, dbTicks)

  /* 0 dB reference line */
  if (dbMin <= 0 && dbMax >= 0) {
    const y0db = magScale(0)
    magPanel.appendChild(svgEl("line", {
      x1: 0, y1: y0db, x2: plotW, y2: y0db,
      stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5,
      "stroke-dasharray": "4,2"
    }, []))
  }

  magPanel.appendChild(svgEl("text", {
    transform: `rotate(-90) translate(${-panelH / 2}, -40)`,
    "text-anchor": "middle",
    "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
  }, "Magnitude (dB)"))

  /* Phase panel y-grid */
  const degTicks = niceTicks(degMin, degMax, 5)
  _hGridLines(phPanel, plotW, panelH, phScale, degTicks)

  /* −180° reference line */
  if (degMin <= -180 && degMax >= -180) {
    const y180 = phScale(-180)
    phPanel.appendChild(svgEl("line", {
      x1: 0, y1: y180, x2: plotW, y2: y180,
      stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5,
      "stroke-dasharray": "4,2"
    }, []))
  }

  phPanel.appendChild(svgEl("text", {
    transform: `rotate(-90) translate(${-panelH / 2}, -40)`,
    "text-anchor": "middle",
    "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
  }, "Phase (deg)"))

  /* x-axis label below phase panel */
  const meta = (raw.meta !== null && raw.meta !== undefined) ? raw.meta : null
  const xLabel = (meta !== null && meta.xLabel) ? meta.xLabel : "Frequency (rad/s)"
  phPanel.appendChild(svgEl("text", {
    x: plotW / 2, y: panelH + 30, "text-anchor": "middle",
    "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
  }, escapeHtml(xLabel)))

  /* Series */
  for (let s = 0; s < series.length; s = s + 1) {
    const ser = series[s]
    const pts = ser.points
    if (pts === null || pts === undefined || pts.length === 0) { continue }
    const color = ctx.colorFor(ser.name)

    const magPts = pts.filter((p) => typeof p.magnitude_db === "number" && p.omega > 0)
      .map((p) => ({ x: xScale(p.omega), y: magScale(p.magnitude_db) }))
    const phPts = pts.filter((p) => typeof p.phase_deg === "number" && p.omega > 0)
      .map((p) => ({ x: xScale(p.omega), y: phScale(p.phase_deg) }))

    const magPath = linePath(magPts)
    if (magPath !== "") {
      magPanel.appendChild(svgEl("path", {
        d: magPath,
        fill: "none",
        stroke: color,
        "stroke-width": 2,
        part: "magnitude-curve"
      }, []))
    }

    const phPath = linePath(phPts)
    if (phPath !== "") {
      phPanel.appendChild(svgEl("path", {
        d: phPath,
        fill: "none",
        stroke: color,
        "stroke-width": 2,
        part: "phase-curve"
      }, []))
    }

    /* Asymptote overlays */
    if (raw.asymptotes === true && magPts.length >= 2) {
      const p0 = magPts[0]
      const pN = magPts[magPts.length - 1]
      magPanel.appendChild(svgEl("line", {
        x1: p0.x.toFixed(1), y1: p0.y.toFixed(1),
        x2: pN.x.toFixed(1), y2: pN.y.toFixed(1),
        stroke: color,
        "stroke-width": 1,
        "stroke-dasharray": "6,3",
        opacity: 0.5,
        part: "asymptote"
      }, []))
    }

    /* Interactive points on magnitude curve */
    for (let p = 0; p < pts.length; p = p + 1) {
      const pt = pts[p]
      if (typeof pt.magnitude_db !== "number" || pt.omega <= 0) { continue }
      const px2 = xScale(pt.omega)
      const py2 = magScale(pt.magnitude_db)
      const label = escapeHtml(
        ser.name + " ω=" + formatNumber(pt.omega) +
        " |H|=" + formatNumber(pt.magnitude_db) + "dB"
      )
      const dot = svgEl("circle", {
        cx: px2.toFixed(1), cy: py2.toFixed(1), r: 3,
        fill: color,
        part: "point",
        tabindex: "0",
        role: "img",
        "aria-label": label
      }, [])
      dot.appendChild(svgEl("title", null, label))
      const detail = {
        series: ser.name, omega: pt.omega,
        magnitude_db: pt.magnitude_db, phase_deg: pt.phase_deg
      }
      const handler = () => { ctx.emit("mj-chart-bode-click", detail) }
      dot.addEventListener("click", handler)
      dot.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })
      magPanel.appendChild(dot)
    }
  }

  return root
}


/* ── dispatch ─────────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Dispatch to Nyquist or Bode sub-renderer.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const chartType = ctx.attrs("type", "nyquist")
  if (chartType === "bode") {
    return _renderBode(ctx)
  }
  return _renderNyquist(ctx)
}


registerRenderer("nyquist", render)
registerRenderer("bode", render)
