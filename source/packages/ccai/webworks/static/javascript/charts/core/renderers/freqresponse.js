/*
 * freqresponse.js
 *
 * Frequency-response chart renderers (Nyquist and Bode).
 *
 * Registered types (dispatched on ctx.type):
 *   "nyquist"  - Nyquist plot: complex-plane locus Re vs Im
 *   "bode"     - Bode diagram: stacked magnitude (dB) and phase (deg) panels
 *
 * Data:
 *   nyquist  { series: [{ name, mirror?, points: [{ omega, re, im }] }],
 *              criticalPoint?: { re, im },   (default -1+0j)
 *              showUnitCircle?: true }       (or the `showUnitCircle` attribute)
 *            Re and Im share one pixels-per-unit factor, so the unit circle
 *            is round and angles are true. The Im range is symmetric only
 *            when a series draws its mirror (negative-frequency) locus.
 *   bode     { series: [{ name, points: [{ omega, ... }] }], asymptotes? }
 *            Each point gives the magnitude as `magnitude_db`, as linear
 *            `magnitude` (converted with 20 log10) or as `re` / `im`, and the
 *            phase as `phase_deg` (or from `re` / `im`). The phase is
 *            unwrapped (no jumps of more than 180 degrees between samples).
 *            `asymptotes: true` draws the low- and high-frequency
 *            asymptotes, slopes rounded to multiples of 20 dB/decade, meeting
 *            at the corner frequency.
 *
 * Events: mj-chart-nyquist-click { series, omega, re, im },
 *         mj-chart-bode-click { series, omega, magnitude_db, phase_deg }
 *
 * Renderer contract: render(ctx) -> SVGElement  (a <g> within [0..width]x[0..height])
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, linePath } from "../svgdraw.js";
import { linearScale, logScale, niceTicks } from "../scales.js";
import { booleanOption } from "../chartoptions.js";


/* ── shared helpers ───────────────────────────────────────────── */

function _isNumber(value) {
  /*
   * True for a finite number.
   */
  const numeric = typeof value === "number" && Number.isFinite(value) === true
  return numeric
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


function _pointsOf(series) {
  /*
   * The point list of a normalized series ([] when it has none).
   */
  const points = Array.isArray(series.points) === true ? series.points : []
  return points.filter((p) => p !== null && typeof p === "object")
}


function _hGridLines(group, plotW, yScale, ticks) {
  /*
   * Horizontal gridlines with tick labels on the left.
   */
  for (let i = 0; i < ticks.length; i = i + 1) {
    const py = yScale(ticks[i])
    group.appendChild(svgEl("line", {
      x1: 0, y1: py, x2: plotW, y2: py,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    group.appendChild(svgEl("text", {
      x: -6, y: py + 4, "text-anchor": "end",
      "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(ticks[i])))
  }
  return
}


function _vGridLines(group, plotH, xScale, ticks, withLabels) {
  /*
   * Vertical gridlines with tick labels below.
   */
  for (let i = 0; i < ticks.length; i = i + 1) {
    const px = xScale(ticks[i])
    group.appendChild(svgEl("line", {
      x1: px, y1: 0, x2: px, y2: plotH,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    if (withLabels === true) {
      group.appendChild(svgEl("text", {
        x: px, y: plotH + 14, "text-anchor": "middle",
        "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
      }, formatNumber(ticks[i])))
    }
  }
  return
}


function _superscript(exp) {
  /*
   * An integer exponent in superscript digits ("-2" -> "⁻²").
   */
  const map = {
    "-": "⁻", "0": "⁰", "1": "¹", "2": "²", "3": "³",
    "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹"
  }
  const s = String(exp)
  let result = ""
  for (let i = 0; i < s.length; i = i + 1) {
    result = result + (map[s[i]] !== undefined ? map[s[i]] : s[i])
  }
  return result
}


function _logTickLabel(value) {
  /*
   * A decade as a power of ten (10³), any other tick as a number.
   */
  const exponent = Math.log10(value)
  if (Math.abs(exponent - Math.round(exponent)) < 1e-9) {
    return "10" + _superscript(Math.round(exponent))
  }
  return formatNumber(value, { maximumSignificantDigits: 3 })
}


function _arrowhead(x, y, angle, size, color) {
  /*
   * An arrowhead polygon with its tip at (x, y), pointing along the screen
   * angle (Math.atan2(dy, dx)).
   */
  const back = (offset) => ({
    x: x - Math.cos(angle + offset) * size,
    y: y - Math.sin(angle + offset) * size
  })
  const left = back(0.45)
  const right = back(-0.45)
  const pts = `${x.toFixed(1)},${y.toFixed(1)} ` +
    `${left.x.toFixed(1)},${left.y.toFixed(1)} ` +
    `${right.x.toFixed(1)},${right.y.toFixed(1)}`
  return svgEl("polygon", { points: pts, fill: color }, [])
}


function _complexText(re, im) {
  /*
   * A complex number as text: "−1+0j", "0.5−0.25j".
   */
  const sign = im < 0 ? "−" : "+"
  const real = formatNumber(re, { maximumFractionDigits: 3 }).replace("-", "−")
  const text = `${real}${sign}${formatNumber(Math.abs(im), { maximumFractionDigits: 3 })}j`
  return text
}


/* ── Nyquist renderer ─────────────────────────────────────────── */

function _renderNyquist(ctx) {
  /*
   * Render a Nyquist (complex-plane frequency-response) plot.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const root = svgEl("g", { part: "plot" }, [])
  const series = ctx.model.series
  const meta = ctx.model.meta

  const valid = (p) => _isNumber(p.re) === true && _isNumber(p.im) === true

  let drawable = 0
  let anyMirror = false
  let reMin = 0
  let reMax = 0
  let imMin = 0
  let imMax = 0
  for (let s = 0; s < series.length; s = s + 1) {
    const pts = _pointsOf(series[s])
    if (series[s].mirror === true) {
      anyMirror = true
    }
    for (let p = 0; p < pts.length; p = p + 1) {
      if (valid(pts[p]) === false) {
        continue
      }
      drawable = drawable + 1
      reMin = Math.min(reMin, pts[p].re)
      reMax = Math.max(reMax, pts[p].re)
      imMin = Math.min(imMin, pts[p].im)
      imMax = Math.max(imMax, pts[p].im)
    }
  }
  if (drawable === 0) {
    return root
  }

  const critSource = raw.criticalPoint !== null && typeof raw.criticalPoint === "object"
    ? raw.criticalPoint : {}
  const crit = {
    re: _isNumber(critSource.re) === true ? critSource.re : -1,
    im: _isNumber(critSource.im) === true ? critSource.im : 0
  }
  reMin = Math.min(reMin, crit.re)
  reMax = Math.max(reMax, crit.re)
  imMin = Math.min(imMin, crit.im)
  imMax = Math.max(imMax, crit.im)

  const showUnitCircle = booleanOption(ctx, "showUnitCircle", raw.showUnitCircle === true)
  if (showUnitCircle === true) {
    reMin = Math.min(reMin, -1)
    reMax = Math.max(reMax, 1)
    imMin = Math.min(imMin, -1)
    imMax = Math.max(imMax, 1)
  }

  if (anyMirror === true) {
    const imAbsMax = Math.max(Math.abs(imMin), Math.abs(imMax))
    imMin = -imAbsMax
    imMax = imAbsMax
  }
  if (reMax - reMin <= 0) {
    reMin = reMin - 1
    reMax = reMax + 1
  }
  if (imMax - imMin <= 0) {
    imMin = imMin - 1
    imMax = imMax + 1
  }
  const rePad = (reMax - reMin) * 0.08
  const imPad = (imMax - imMin) * 0.08
  reMin = reMin - rePad
  reMax = reMax + rePad
  imMin = imMin - imPad
  imMax = imMax + imPad

  const margin = { top: 20, right: 24, bottom: 46, left: 58 }
  const availW = Math.max(ctx.width - margin.left - margin.right, 10)
  const availH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  /* One pixels-per-unit factor for both axes; the plot box is centred. */
  const unit = Math.min(availW / (reMax - reMin), availH / (imMax - imMin))
  const plotW = (reMax - reMin) * unit
  const plotH = (imMax - imMin) * unit
  const left = margin.left + (availW - plotW) / 2
  const top = margin.top + (availH - plotH) / 2
  const xScale = linearScale([reMin, reMax], [0, plotW])
  const yScale = linearScale([imMin, imMax], [plotH, 0])

  const plot = svgEl("g", {
    transform: `translate(${left.toFixed(2)},${top.toFixed(2)})`
  }, [])
  root.appendChild(plot)

  /* Grid, axes through the origin, axis titles and the unit circle. */
  const axes = svgEl("g", { "aria-hidden": "true", part: "axes" }, [])
  /* The same tick step on both axes, as the units are equal. */
  const reTicks = niceTicks(reMin, reMax, Math.max(Math.round(plotW / 50), 4))
  const step = reTicks.length > 1 ? reTicks[1] - reTicks[0] : 1
  const imTicks = []
  for (let v = Math.ceil(imMin / step) * step; v <= imMax + 1e-9 && imTicks.length < 60; v = v + step) {
    imTicks.push(Number(v.toFixed(10)))
  }
  _vGridLines(axes, plotH, xScale, reTicks, true)
  _hGridLines(axes, plotW, yScale, imTicks)
  const ox = xScale(0)
  const oy = yScale(0)
  axes.appendChild(svgEl("line", {
    x1: ox, y1: 0, x2: ox, y2: plotH,
    stroke: "var(--mj-border-strong, #878e9c)", "stroke-width": 1.25
  }, []))
  axes.appendChild(svgEl("line", {
    x1: 0, y1: oy, x2: plotW, y2: oy,
    stroke: "var(--mj-border-strong, #878e9c)", "stroke-width": 1.25
  }, []))
  const xLabel = typeof meta.xLabel === "string" && meta.xLabel.length > 0 ? meta.xLabel : "Re(H)"
  const yLabel = typeof meta.yLabel === "string" && meta.yLabel.length > 0 ? meta.yLabel : "Im(H)"
  axes.appendChild(svgEl("text", {
    x: plotW / 2, y: plotH + 32, "text-anchor": "middle",
    "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
  }, xLabel))
  axes.appendChild(svgEl("text", {
    transform: `rotate(-90) translate(${-plotH / 2}, -40)`,
    "text-anchor": "middle",
    "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
  }, yLabel))
  if (showUnitCircle === true) {
    axes.appendChild(svgEl("circle", {
      cx: ox, cy: oy, r: unit,
      fill: "none",
      stroke: "var(--mj-border-strong, #878e9c)",
      "stroke-width": 1,
      "stroke-dasharray": "4,3",
      part: "unit-circle"
    }, []))
  }
  plot.appendChild(axes)

  const tableRows = []

  for (let s = 0; s < series.length; s = s + 1) {
    const ser = series[s]
    const pts = _pointsOf(ser)
    if (pts.length === 0) { continue }
    const color = ctx.colorFor(ser.name)
    const group = svgEl("g", { part: "series", "data-series": ser.name }, [])

    /* Forward locus; an invalid point is a gap. */
    const pixPts = pts.map((p) => (valid(p) === true ? { x: xScale(p.re), y: yScale(p.im) } : null))
    const pathData = linePath(pixPts)
    if (pathData !== "") {
      group.appendChild(svgEl("path", {
        d: pathData,
        fill: "none",
        stroke: color,
        "stroke-width": 2,
        part: "locus"
      }, []))
      /* Direction of increasing ω, at about a third of the locus. */
      const drawn = pixPts.filter((p) => p !== null)
      const idx = Math.max(Math.floor(drawn.length / 3), 1)
      if (idx < drawn.length) {
        const p0 = drawn[idx - 1]
        const p1 = drawn[idx]
        if (Math.hypot(p1.x - p0.x, p1.y - p0.y) > 0.5) {
          group.appendChild(_arrowhead((p0.x + p1.x) / 2, (p0.y + p1.y) / 2,
            Math.atan2(p1.y - p0.y, p1.x - p0.x), 7, color))
        }
      }
    }

    /* Mirror (conjugate, negative-frequency locus) */
    if (ser.mirror === true) {
      const mirrorPts = pts.map((p) => (valid(p) === true ? { x: xScale(p.re), y: yScale(-p.im) } : null))
      const mirrorPath = linePath(mirrorPts)
      if (mirrorPath !== "") {
        group.appendChild(svgEl("path", {
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
      if (px2 === null) {
        continue
      }
      const omegaText = _isNumber(pt.omega) === true ? `ω ${formatNumber(pt.omega)}: ` : ""
      const label = `${ser.name}, ${omegaText}${_complexText(pt.re, pt.im)}`
      const dot = svgEl("circle", {
        cx: px2.x.toFixed(1), cy: px2.y.toFixed(1), r: 3,
        fill: color,
        part: "point",
        tabindex: "0",
        role: "img",
        "aria-label": label
      }, [svgEl("title", null, label)])
      _attachActivation(dot, ctx, "mj-chart-nyquist-click", { series: ser.name, omega: pt.omega, re: pt.re, im: pt.im })
      group.appendChild(dot)
      tableRows.push([ser.name, _isNumber(pt.omega) === true ? pt.omega : "", pt.re, pt.im])
    }
    plot.appendChild(group)
  }

  /* Critical point marker, labelled with its configured value. */
  const cpx = xScale(crit.re)
  const cpy = yScale(crit.im)
  const critical = svgEl("g", { "aria-hidden": "true", part: "critical-point" }, [])
  critical.appendChild(svgEl("circle", {
    cx: cpx.toFixed(1), cy: cpy.toFixed(1), r: 6,
    fill: "none",
    stroke: "var(--mj-color-danger, #b91c1c)",
    "stroke-width": 2
  }, []))
  critical.appendChild(svgEl("text", {
    x: (cpx + 8).toFixed(1), y: (cpy - 8).toFixed(1),
    "font-size": 10,
    fill: "var(--mj-color-danger, #b91c1c)"
  }, _complexText(crit.re, crit.im)))
  plot.appendChild(critical)

  ctx.setTable({ columns: ["Series", "ω", "Re", "Im"], rows: tableRows })
  return root
}


/* ── Bode renderer ────────────────────────────────────────────── */

function _bodeSamples(points) {
  /*
   * Normalise Bode points to [{ omega, db, deg, source }] sorted by omega:
   * magnitude from magnitude_db, linear magnitude or re/im; phase from
   * phase_deg or re/im, unwrapped so neighbours differ by at most 180°.
   * Samples with omega <= 0 cannot be drawn on the log axis and are left
   * out; a missing magnitude or phase is null (a gap in that panel).
   */
  const samples = []
  for (let p = 0; p < points.length; p = p + 1) {
    const pt = points[p]
    if (_isNumber(pt.omega) === false || pt.omega <= 0) {
      continue
    }
    const complex = _isNumber(pt.re) === true && _isNumber(pt.im) === true
    let db = null
    if (_isNumber(pt.magnitude_db) === true) {
      db = pt.magnitude_db
    } else if (_isNumber(pt.magnitude) === true && pt.magnitude > 0) {
      db = 20 * Math.log10(pt.magnitude)
    } else if (complex === true && Math.hypot(pt.re, pt.im) > 0) {
      db = 20 * Math.log10(Math.hypot(pt.re, pt.im))
    }
    let deg = null
    if (_isNumber(pt.phase_deg) === true) {
      deg = pt.phase_deg
    } else if (_isNumber(pt.phase) === true) {
      deg = pt.phase
    } else if (complex === true) {
      deg = (Math.atan2(pt.im, pt.re) * 180) / Math.PI
    }
    samples.push({ omega: pt.omega, db: db, deg: deg, source: pt })
  }
  samples.sort((a, b) => a.omega - b.omega)

  let previous = null
  let offset = 0
  for (let i = 0; i < samples.length; i = i + 1) {
    if (samples[i].deg === null) {
      continue
    }
    let value = samples[i].deg + offset
    if (previous !== null) {
      while (value - previous > 180) {
        offset = offset - 360
        value = value - 360
      }
      while (value - previous < -180) {
        offset = offset + 360
        value = value + 360
      }
    }
    samples[i].deg = value
    previous = value
  }
  return samples
}


function _asymptotes(samples) {
  /*
   * The low- and high-frequency asymptotes of a magnitude curve, each with
   * its slope rounded to a multiple of 20 dB/decade, as line segments in
   * (log10 omega, dB): [{ x0, y0, x1, y1 }, ...]. Empty when there are
   * fewer than two magnitude samples.
   */
  const pts = samples.filter((s) => s.db !== null).map((s) => ({ x: Math.log10(s.omega), y: s.db }))
  if (pts.length < 2) {
    return []
  }
  const slopeOf = (a, b) => (b.x - a.x > 0 ? (b.y - a.y) / (b.x - a.x) : 0)
  const round20 = (slope) => Math.round(slope / 20) * 20
  const first = pts[0]
  const last = pts[pts.length - 1]
  const lowSlope = round20(slopeOf(pts[0], pts[1]))
  const highSlope = round20(slopeOf(pts[pts.length - 2], pts[pts.length - 1]))

  /* Low asymptote through the first sample, high through the last. */
  const low = (x) => first.y + lowSlope * (x - first.x)
  const high = (x) => last.y + highSlope * (x - last.x)
  if (lowSlope === highSlope) {
    return [{ x0: first.x, y0: low(first.x), x1: last.x, y1: low(last.x) }]
  }
  /* Corner: low(x) = high(x). */
  let corner = (last.y - highSlope * last.x - first.y + lowSlope * first.x) / (lowSlope - highSlope)
  corner = Math.min(Math.max(corner, first.x), last.x)
  const segments = [
    { x0: first.x, y0: low(first.x), x1: corner, y1: low(corner) },
    { x0: corner, y0: high(corner), x1: last.x, y1: high(last.x) }
  ]
  return segments
}


function _renderBode(ctx) {
  /*
   * Render a Bode plot: magnitude (dB) and phase (deg) stacked panels.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const root = svgEl("g", { part: "plot" }, [])
  const series = ctx.model.series
  const meta = ctx.model.meta

  const prepared = series.map((ser) => ({ series: ser, samples: _bodeSamples(_pointsOf(ser)) }))

  let omegaMin = Infinity
  let omegaMax = -Infinity
  let dbMin = Infinity
  let dbMax = -Infinity
  let degMin = Infinity
  let degMax = -Infinity
  for (let s = 0; s < prepared.length; s = s + 1) {
    const samples = prepared[s].samples
    for (let i = 0; i < samples.length; i = i + 1) {
      omegaMin = Math.min(omegaMin, samples[i].omega)
      omegaMax = Math.max(omegaMax, samples[i].omega)
      if (samples[i].db !== null) {
        dbMin = Math.min(dbMin, samples[i].db)
        dbMax = Math.max(dbMax, samples[i].db)
      }
      if (samples[i].deg !== null) {
        degMin = Math.min(degMin, samples[i].deg)
        degMax = Math.max(degMax, samples[i].deg)
      }
    }
  }
  if (omegaMin === Infinity) {
    return root
  }
  if (dbMin === Infinity) { dbMin = -20; dbMax = 0 }
  if (degMin === Infinity) { degMin = -180; degMax = 0 }

  /* Decade-aligned frequency domain; nice dB and degree domains. */
  const decadeLow = Math.pow(10, Math.floor(Math.log10(omegaMin) + 1e-9))
  let decadeHigh = Math.pow(10, Math.ceil(Math.log10(omegaMax) - 1e-9))
  if (decadeHigh <= decadeLow) {
    decadeHigh = decadeLow * 10
  }
  const dbTicks = niceTicks(dbMin === dbMax ? dbMin - 1 : dbMin, dbMin === dbMax ? dbMax + 1 : dbMax, 5)
  const dbLow = Math.min(dbTicks[0], dbMin)
  const dbHigh = Math.max(dbTicks[dbTicks.length - 1], dbMax)
  const degSpan = Math.max(degMax - degMin, 1)
  const roomForTicks = Math.max(Math.floor((ctx.height - 100) / 2 / 22), 2)
  const degStep = degSpan / 45 <= roomForTicks ? 45 : (degSpan / 90 <= roomForTicks ? 90 : 180)
  const degLow = Math.floor((degMin === degMax ? degMin - 1 : degMin) / degStep) * degStep
  const degHigh = Math.ceil((degMin === degMax ? degMax + 1 : degMax) / degStep) * degStep
  const degTicks = []
  for (let v = degLow; v <= degHigh + 1e-9 && degTicks.length < 40; v = v + degStep) {
    degTicks.push(v)
  }

  const margin = { top: 16, right: 24, bottom: 40, left: 58 }
  const gapBetweenPanels = 20
  const totalH = Math.max(ctx.height - margin.top - margin.bottom - gapBetweenPanels, 20)
  const panelH = Math.floor(totalH / 2)
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)

  const xScale = logScale([decadeLow, decadeHigh], [0, plotW])
  const magScale = linearScale([dbLow, dbHigh], [panelH, 0])
  const phScale = linearScale([degLow, degHigh], [panelH, 0])

  const magPanel = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(magPanel)
  const phPanel = svgEl("g", {
    transform: `translate(${margin.left},${margin.top + panelH + gapBetweenPanels})`
  }, [])
  root.appendChild(phPanel)

  const magAxes = svgEl("g", { "aria-hidden": "true", part: "axes" }, [])
  const phAxes = svgEl("g", { "aria-hidden": "true", part: "axes" }, [])
  magPanel.appendChild(magAxes)
  phPanel.appendChild(phAxes)

  /* Shared log-frequency grid: decades labelled, 2..9 minor lines. */
  const decades = Math.round(Math.log10(decadeHigh / decadeLow))
  for (let d = 0; d < decades && decades <= 6; d = d + 1) {
    const base = decadeLow * Math.pow(10, d)
    for (let m = 2; m <= 9; m = m + 1) {
      const px = xScale(base * m)
      for (const axes of [magAxes, phAxes]) {
        axes.appendChild(svgEl("line", {
          x1: px, y1: 0, x2: px, y2: panelH,
          stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 0.5, "stroke-opacity": 0.7
        }, []))
      }
    }
  }
  const xTicks = xScale.ticks(6)
  for (let i = 0; i < xTicks.length; i = i + 1) {
    const px = xScale(xTicks[i])
    for (const axes of [magAxes, phAxes]) {
      axes.appendChild(svgEl("line", {
        x1: px, y1: 0, x2: px, y2: panelH,
        stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
      }, []))
    }
    phAxes.appendChild(svgEl("text", {
      x: px, y: panelH + 14, "text-anchor": "middle",
      "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, _logTickLabel(xTicks[i])))
  }

  _hGridLines(magAxes, plotW, magScale, dbTicks)
  if (dbLow <= 0 && dbHigh >= 0) {
    const y0db = magScale(0)
    magAxes.appendChild(svgEl("line", {
      x1: 0, y1: y0db, x2: plotW, y2: y0db,
      stroke: "var(--mj-border-strong, #878e9c)", "stroke-width": 1.25,
      "stroke-dasharray": "4,2"
    }, []))
  }
  magAxes.appendChild(svgEl("text", {
    transform: `rotate(-90) translate(${-panelH / 2}, -42)`,
    "text-anchor": "middle",
    "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
  }, "Magnitude (dB)"))

  _hGridLines(phAxes, plotW, phScale, degTicks)
  if (degLow <= -180 && degHigh >= -180) {
    const y180 = phScale(-180)
    phAxes.appendChild(svgEl("line", {
      x1: 0, y1: y180, x2: plotW, y2: y180,
      stroke: "var(--mj-border-strong, #878e9c)", "stroke-width": 1.25,
      "stroke-dasharray": "4,2"
    }, []))
  }
  phAxes.appendChild(svgEl("text", {
    transform: `rotate(-90) translate(${-panelH / 2}, -42)`,
    "text-anchor": "middle",
    "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
  }, "Phase (deg)"))

  const xLabel = typeof meta.xLabel === "string" && meta.xLabel.length > 0 ? meta.xLabel : "Frequency (rad/s)"
  phAxes.appendChild(svgEl("text", {
    x: plotW / 2, y: panelH + 30, "text-anchor": "middle",
    "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
  }, xLabel))

  const tableRows = []

  for (let s = 0; s < prepared.length; s = s + 1) {
    const ser = prepared[s].series
    const samples = prepared[s].samples
    if (samples.length === 0) { continue }
    const color = ctx.colorFor(ser.name)

    const magPts = samples.map((p) => (p.db === null ? null : { x: xScale(p.omega), y: magScale(p.db) }))
    const phPts = samples.map((p) => (p.deg === null ? null : { x: xScale(p.omega), y: phScale(p.deg) }))
    const magGroup = svgEl("g", { part: "series", "data-series": ser.name }, [])
    const phGroup = svgEl("g", { part: "series", "data-series": ser.name }, [])

    const magPath = linePath(magPts)
    if (magPath !== "") {
      magGroup.appendChild(svgEl("path", {
        d: magPath, fill: "none", stroke: color, "stroke-width": 2, part: "magnitude-curve"
      }, []))
    }
    const phPath = linePath(phPts)
    if (phPath !== "") {
      phGroup.appendChild(svgEl("path", {
        d: phPath, fill: "none", stroke: color, "stroke-width": 2, part: "phase-curve"
      }, []))
    }

    if (raw.asymptotes === true) {
      const segments = _asymptotes(samples)
      for (let i = 0; i < segments.length; i = i + 1) {
        const seg = segments[i]
        magGroup.appendChild(svgEl("line", {
          x1: xScale(Math.pow(10, seg.x0)).toFixed(1), y1: magScale(seg.y0).toFixed(1),
          x2: xScale(Math.pow(10, seg.x1)).toFixed(1), y2: magScale(seg.y1).toFixed(1),
          stroke: color,
          "stroke-width": 1.25,
          "stroke-dasharray": "6,3",
          "stroke-opacity": 0.75,
          part: "asymptote",
          "aria-hidden": "true"
        }, []))
      }
    }

    /* Interactive points on both curves */
    for (let i = 0; i < samples.length; i = i + 1) {
      const sample = samples[i]
      const parts = [`ω ${formatNumber(sample.omega)}`]
      if (sample.db !== null) {
        parts.push(`${formatNumber(sample.db, { maximumFractionDigits: 2 })} dB`)
      }
      if (sample.deg !== null) {
        parts.push(`${formatNumber(sample.deg, { maximumFractionDigits: 1 })}°`)
      }
      const label = `${ser.name}: ${parts.join(", ")}`
      const detail = { series: ser.name, omega: sample.omega, magnitude_db: sample.db, phase_deg: sample.deg }
      if (magPts[i] !== null) {
        const dot = svgEl("circle", {
          cx: magPts[i].x.toFixed(1), cy: magPts[i].y.toFixed(1), r: 3,
          fill: color, part: "point", tabindex: "0", role: "img", "aria-label": label
        }, [svgEl("title", null, label)])
        _attachActivation(dot, ctx, "mj-chart-bode-click", detail)
        magGroup.appendChild(dot)
      }
      if (phPts[i] !== null) {
        const dot = svgEl("circle", {
          cx: phPts[i].x.toFixed(1), cy: phPts[i].y.toFixed(1), r: 3,
          fill: color, part: "point", tabindex: "0", role: "img", "aria-label": label
        }, [svgEl("title", null, label)])
        _attachActivation(dot, ctx, "mj-chart-bode-click", detail)
        phGroup.appendChild(dot)
      }
      tableRows.push([ser.name, sample.omega, sample.db === null ? "" : sample.db,
        sample.deg === null ? "" : sample.deg])
    }
    magPanel.appendChild(magGroup)
    phPanel.appendChild(phGroup)
  }

  ctx.setTable({ columns: ["Series", "ω", "Magnitude (dB)", "Phase (°)"], rows: tableRows })
  return root
}


/* ── dispatch ─────────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Dispatch to the Nyquist or Bode sub-renderer.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const chartType = typeof ctx.type === "string" ? ctx.type : ctx.attrs("type", "nyquist")
  let root = null
  if (chartType === "bode") {
    root = _renderBode(ctx)
  } else {
    root = _renderNyquist(ctx)
  }
  return root
}


registerRenderer("nyquist", render)
registerRenderer("bode", render)
