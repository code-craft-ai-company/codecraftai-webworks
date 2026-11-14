/*
 * glyph.js
 *
 * Glyph chart renderer — tiles miniature multi-variable star / radar /
 * bar glyphs (one glyph per series = observation) in a grid.
 *
 * Registered types:
 *   "glyph"
 *
 * ctx.raw shape:
 *   raw.axes      [string]                axis names (variables)
 *   raw.series    [{name, values:[...]}]  one entry per observation; a
 *                 null / missing value is "no data" (drawn at the centre
 *                 with a hollow marker and said so in the label)
 *   raw.glyphType "star" | "radar" (default) | "bar-glyph"; the `mode`
 *                 attribute is the fallback
 *   raw.grid      {cols: N}
 *   raw.domains   optional [[min, max], ...] per axis, or raw.domain
 *                 [min, max] for every axis
 *   raw.scale     "absolute" (default) | "relative"
 *
 * Scale: by default every axis runs from 0 (the centre) to 1 when all of
 * its values lie in [0, 1], else from 0 to the axis maximum -- so glyph size
 * is proportional to the value and equal values never collapse. "relative"
 * rescales each axis to the observed [min, max] (the key then says
 * "relative"). Each glyph has reference rings at half and full scale.
 *
 * The first grid cell is a key glyph with the axis names around it.
 *
 * Interaction: each glyph is one focusable mark; click / Enter emits
 * `mj-chart-glyph-click` { series, values }.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";


function _number(value) {
  /*
   * A finite number, else null.
   */
  const numeric = typeof value === "number" && Number.isFinite(value) === true ? value : null
  return numeric
}


function _axisDomains(raw, axes, series) {
  /*
   * [min, max] per axis; see the file header for the rules.
   */
  const domains = []
  const relative = raw.scale === "relative"
  for (let a = 0; a < axes.length; a = a + 1) {
    const given = Array.isArray(raw.domains) === true ? raw.domains[a] : raw.domain
    if (Array.isArray(given) === true && given.length === 2 && _number(given[0]) !== null &&
        _number(given[1]) !== null && given[0] !== given[1]) {
      domains.push([Math.min(given[0], given[1]), Math.max(given[0], given[1])])
      continue
    }
    const values = series.map((entry) => _number(entry.values[a])).filter((value) => value !== null)
    const low = values.length > 0 ? Math.min(...values) : 0
    const high = values.length > 0 ? Math.max(...values) : 1
    if (relative === true && high > low) {
      domains.push([low, high])
    } else if (low >= 0 && high <= 1) {
      domains.push([0, 1])
    } else if (low >= 0) {
      domains.push([0, high])
    } else {
      domains.push([low, high > low ? high : low + 1])
    }
  }
  return domains
}


function _angle(index, count) {
  /*
   * Spoke angle (radians, 0 = up, clockwise).
   */
  return (index / count) * 2 * Math.PI - Math.PI / 2
}


function _drawGlyph(cx, cy, r, shares, glyphType, color) {
  /*
   * One glyph: rings, spokes and the value shape.
   *
   * :param shares: Per axis share of the radius in [0, 1], or null.
   */
  const group = svgEl("g", {}, [])
  const count = shares.length
  const frame = svgEl("g", { "aria-hidden": "true" }, [])
  group.appendChild(frame)
  frame.appendChild(svgEl("circle", {
    cx: cx, cy: cy, r: r, fill: "none", stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 0.75
  }, []))
  frame.appendChild(svgEl("circle", {
    cx: cx, cy: cy, r: r / 2, fill: "none", stroke: "var(--mj-border, #e0e3e9)",
    "stroke-width": 0.5, "stroke-dasharray": "2 2"
  }, []))
  for (let a = 0; a < count; a = a + 1) {
    const angle = _angle(a, count)
    frame.appendChild(svgEl("line", {
      x1: cx, y1: cy, x2: cx + r * Math.cos(angle), y2: cy + r * Math.sin(angle),
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 0.5
    }, []))
  }

  const at = (a, share) => {
    const angle = _angle(a, count)
    return { x: cx + share * r * Math.cos(angle), y: cy + share * r * Math.sin(angle) }
  }

  if (glyphType === "bar-glyph") {
    for (let a = 0; a < count; a = a + 1) {
      if (shares[a] === null) {
        continue
      }
      const end = at(a, shares[a])
      group.appendChild(svgEl("line", {
        x1: cx, y1: cy, x2: end.x.toFixed(2), y2: end.y.toFixed(2), stroke: color,
        "stroke-width": Math.max(Math.min(r * 0.12, 4), 2), "stroke-linecap": "round"
      }, []))
    }
  } else {
    const points = shares.map((share, a) => at(a, share === null ? 0 : share))
    group.appendChild(svgEl("polygon", {
      points: points.map((point) => `${point.x.toFixed(2)},${point.y.toFixed(2)}`).join(" "),
      fill: color, "fill-opacity": glyphType === "radar" ? "0.25" : "0",
      stroke: color, "stroke-width": 1.5, "stroke-linejoin": "round"
    }, []))
    points.forEach((point, a) => {
      group.appendChild(svgEl("circle", {
        cx: point.x.toFixed(2), cy: point.y.toFixed(2), r: 2,
        fill: shares[a] === null ? "var(--mj-surface, #ffffff)" : color,
        stroke: color, "stroke-width": shares[a] === null ? 1 : 0
      }, []))
    })
  }
  return group
}


export function render(ctx) {
  /*
   * Render a glyph chart (tiled star / radar / bar-glyph observations).
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const root = svgEl("g", { part: "plot" }, [])
  const axes = (Array.isArray(raw.axes) === true ? raw.axes : []).map((axis) => String(axis))
  const series = ctx.model.series

  ctx.setTable({
    columns: ["Series"].concat(axes),
    rows: series.map((entry) => [entry.name].concat(axes.map((axis, a) => _number(entry.values[a])))),
    caption: ctx.label
  })

  if (axes.length === 0 || series.length === 0) {
    return root
  }

  const typeSource = raw.glyphType !== undefined && raw.glyphType !== null ? raw.glyphType : ctx.attrs("mode", "radar")
  const glyphType = typeSource === "star" || typeSource === "bar-glyph" ? typeSource : "radar"
  const domains = _axisDomains(raw, axes, series)
  const relative = raw.scale === "relative"

  const cellsNeeded = series.length + 1
  const requested = raw.grid !== null && typeof raw.grid === "object" && Number.isInteger(raw.grid.cols) === true &&
    raw.grid.cols > 0 ? raw.grid.cols : null
  const fit = Math.max(Math.floor(ctx.width / 90), 1)
  const gridCols = Math.max(1, Math.min(requested !== null ? requested + 1 : Math.ceil(Math.sqrt(cellsNeeded * 2)),
    fit, cellsNeeded))
  const gridRows = Math.ceil(cellsNeeded / gridCols)
  const pad = 6
  const plotW = Math.max(ctx.width - pad * 2, 10)
  const plotH = Math.max(ctx.height - pad * 2, 10)
  const cellW = plotW / gridCols
  const cellH = plotH / gridRows
  const labelH = 14
  const glyphR = Math.max(Math.min(cellW * 0.32, (cellH - labelH) * 0.36), 4)

  const center = (slot) => ({
    x: pad + (slot % gridCols) * cellW + cellW / 2,
    y: pad + Math.floor(slot / gridCols) * cellH + (cellH - labelH) / 2 + 2
  })

  /* Key glyph: axis names around a frame. */
  const key = svgEl("g", { "aria-hidden": "true", part: "glyph-key" }, [])
  root.appendChild(key)
  const keySpot = center(0)
  /* The key frame is smaller than a glyph so the axis names fit beside it. */
  const keyR = Math.max(Math.min(glyphR, cellW * 0.18), 4)
  key.appendChild(_drawGlyph(keySpot.x, keySpot.y, keyR, axes.map(() => null), "bar-glyph",
    "var(--mj-text-muted, #5f6673)"))
  const maxChars = Math.max(Math.floor((cellW / 2 - keyR - 8) / (8 * 0.6)), 3)
  for (let a = 0; a < axes.length; a = a + 1) {
    const angle = _angle(a, axes.length)
    const cos = Math.cos(angle)
    const text = axes[a].length > maxChars ? axes[a].slice(0, maxChars - 1) + "…" : axes[a]
    key.appendChild(svgEl("text", {
      x: (keySpot.x + (keyR + 4) * cos).toFixed(2),
      y: (keySpot.y + (keyR + 6) * Math.sin(angle)).toFixed(2),
      "text-anchor": Math.abs(cos) < 0.3 ? "middle" : (cos > 0 ? "start" : "end"),
      "dominant-baseline": "middle", "font-size": 8, fill: "var(--mj-text-muted, #5f6673)"
    }, text))
  }
  key.appendChild(svgEl("text", {
    x: keySpot.x, y: keySpot.y + glyphR + labelH, "text-anchor": "middle", "font-size": 10,
    "font-style": "italic", fill: "var(--mj-text-muted, #5f6673)"
  }, relative === true ? "Key (relative scale)" : "Key"))

  for (let s = 0; s < series.length; s = s + 1) {
    const entry = series[s]
    const spot = center(s + 1)
    const color = ctx.colorFor(entry.name)
    const shares = axes.map((axis, a) => {
      const value = _number(entry.values[a])
      if (value === null) {
        return null
      }
      const domain = domains[a]
      const share = (value - domain[0]) / (domain[1] - domain[0])
      return Math.max(0, Math.min(1, share))
    })
    const summary = axes.map((axis, a) => {
      const value = _number(entry.values[a])
      return `${axis}: ${value !== null ? formatNumber(value) : "no data"}`
    }).join(", ")

    const glyph = _drawGlyph(spot.x, spot.y, glyphR, shares, glyphType, color)
    glyph.setAttribute("part", "glyph")
    glyph.setAttribute("tabindex", "0")
    glyph.setAttribute("role", "img")
    glyph.setAttribute("aria-label", `${entry.name}: ${summary}`)
    glyph.appendChild(svgEl("title", null, `${entry.name}: ${summary}`))
    glyph.insertBefore(svgEl("circle", {
      cx: spot.x, cy: spot.y, r: glyphR, fill: "transparent", stroke: "none"
    }, []), glyph.firstChild)
    const nameChars = Math.max(Math.floor((cellW - 4) / 6), 3)
    glyph.appendChild(svgEl("text", {
      x: spot.x, y: spot.y + glyphR + labelH, "text-anchor": "middle", "font-size": 10,
      fill: "var(--mj-text, #14181f)", "aria-hidden": "true"
    }, entry.name.length > nameChars ? entry.name.slice(0, nameChars - 1) + "…" : entry.name))

    const capturedName = entry.name
    const capturedValues = entry.values
    const handler = () => {
      ctx.emit("mj-chart-glyph-click", { series: capturedName, values: capturedValues })
    }
    glyph.addEventListener("click", handler)
    glyph.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        handler()
      }
    })
    root.appendChild(glyph)
  }

  return root
}


registerRenderer("glyph", render)
