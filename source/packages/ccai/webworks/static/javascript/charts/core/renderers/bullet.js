/*
 * bullet.js
 *
 * Bullet chart renderer -- a compact, information-dense KPI chart that
 * compares a primary performance measure against qualitative ranges
 * (Poor / Satisfactory / Good) and a target marker. Multiple bullets
 * stack as independent rows (horizontal, the default) or columns
 * (orientation="vertical").
 *
 * A renderer is `render(ctx) -> SVGElement`:
 *   ctx.model       normalized model { meta, categories, series, raw }
 *   ctx.raw         the raw data object
 *   ctx.width       drawing surface width (px)
 *   ctx.height      drawing surface height (px)
 *   ctx.orientation "horizontal" (registered default) | "vertical"
 *   ctx.attrs       (name, fallback) -> controller attribute value
 *   ctx.colorFor    (seriesIndex | seriesName) -> CSS color
 *   ctx.emit        (eventName, detail) -> dispatch an interaction event
 * It returns a <g> SVGElement drawn within [0..width] x [0..height].
 *
 * Attributes:
 *   scale   "auto" (default) | "shared" | "independent" -- one value scale
 *           for all bullets, or one per bullet with its own tick labels.
 *           auto uses independent scales when the bullets' ranges differ.
 *
 * JSON shape per bullet series entry:
 *   { "name": "Revenue", "value": 275, "target": 300,
 *     "ranges": [200, 250, 350], "rangeLabels": ["Poor","Satisfactory","Good"] }
 *
 * `ranges` are thresholds, read in ascending order (the order given does not
 * matter); band i spans from the previous threshold (or 0) to threshold i,
 * darkest first. A bullet's track ends at its largest range (or its value /
 * target when larger); the performance bar is clipped to the track. Bands
 * are at most 32px thick and centred in their slot. The range labels form a
 * key above the bullets (and the chart's legend); the accessible table has
 * one row per bullet.
 *
 * Registered type keys: "bullet"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { linearScale, niceTicks, niceDomain } from "../scales.js";
import {
  LABEL_FONT_SIZE, textWidth, labelText, numericValue, inlineLegend, activate
} from "./bar.js";

const MAX_THICKNESS = 32;
const TICK_FONT_SIZE = 10;

const TARGET_COLOR = "var(--mj-text, #14181f)";


function _rangeFill(index, count) {
  /*
   * The fill of range band `index` (0 = lowest, darkest) of `count`: the
   * text colour mixed into the surface, so it reads in both themes. The
   * first three bands can be themed with --mj-chart-range-1..3.
   */
  const strength = count > 1 ? Math.round(34 - (index / (count - 1)) * 22) : 24
  const mixed = `color-mix(in oklab, var(--mj-text, #14181f) ${strength}%, var(--mj-surface, #ffffff))`
  const fill = index < 3 ? `var(--mj-chart-range-${index + 1}, ${mixed})` : mixed
  return fill
}


function _readBullet(entry) {
  /*
   * Normalise one bullet: numeric value / target, ascending ranges and
   * the track domain.
   */
  const value = numericValue(entry.value)
  const target = numericValue(entry.target)
  const labels = Array.isArray(entry.rangeLabels) === true ? entry.rangeLabels : []
  const given = Array.isArray(entry.ranges) === true ? entry.ranges : []
  const ranges = []
  for (let index = 0; index < given.length; index = index + 1) {
    const threshold = numericValue(given[index])
    if (threshold !== null) {
      const label = labels[index] !== undefined && labels[index] !== null ? String(labels[index]) : ""
      ranges.push({ threshold: threshold, label: label })
    }
  }
  ranges.sort((a, b) => a.threshold - b.threshold)

  let low = 0
  let high = 0
  const known = ranges.map((range) => range.threshold)
  if (value !== null) {
    known.push(value)
  }
  if (target !== null) {
    known.push(target)
  }
  for (let index = 0; index < known.length; index = index + 1) {
    low = Math.min(low, known[index])
    high = Math.max(high, known[index])
  }
  let domain = [low, high]
  if (ranges.length === 0 || high > ranges[ranges.length - 1].threshold) {
    domain = niceDomain(low, high === low ? low + 1 : high, 4)
  }
  if (domain[1] === domain[0]) {
    domain = [domain[0], domain[0] + 1]
  }

  const bullet = {
    name: entry.name, value: value, target: target, ranges: ranges, domain: domain
  }
  return bullet
}


function _rangeOf(bullet) {
  /*
   * The label of the band the value falls in, for the accessible name.
   */
  if (bullet.value === null) {
    return ""
  }
  let previous = 0
  for (let index = 0; index < bullet.ranges.length; index = index + 1) {
    const range = bullet.ranges[index]
    if (bullet.value <= range.threshold) {
      const name = range.label !== "" ? range.label : `range ${index + 1}`
      return `, ${name} (${formatNumber(previous)}–${formatNumber(range.threshold)})`
    }
    previous = range.threshold
  }
  return ""
}


function _drawBullet(group, bullet, scale, horizontal, trackStart, thickness, rangeCount, ctx) {
  /*
   * Draw one bullet: range bands, performance bar and target tick.
   *
   * :param scale: The bullet's value -> px scale along the track.
   * :param trackStart: px of the band's edge across the track.
   * :param thickness: Band thickness in px.
   */
  const toRect = (from, to, offset, size) => {
    const p1 = scale(from)
    const p2 = scale(to)
    const rect = horizontal === true
      ? { x: Math.min(p1, p2), y: offset, width: Math.abs(p2 - p1), height: size }
      : { x: offset, y: Math.min(p1, p2), width: size, height: Math.abs(p2 - p1) }
    return rect
  }

  const bands = svgEl("g", { "aria-hidden": "true", part: "bullet-ranges" }, [])
  let previous = Math.min(0, bullet.domain[0])
  for (let index = 0; index < bullet.ranges.length; index = index + 1) {
    const range = bullet.ranges[index]
    const rect = toRect(previous, range.threshold, trackStart, thickness)
    rect.fill = _rangeFill(index, rangeCount)
    bands.appendChild(svgEl("rect", rect, range.label !== "" ? [svgEl("title", null, range.label)] : []))
    previous = range.threshold
  }
  if (bullet.ranges.length === 0) {
    const rect = toRect(bullet.domain[0], bullet.domain[1], trackStart, thickness)
    rect.fill = _rangeFill(rangeCount - 1, rangeCount)
    bands.appendChild(svgEl("rect", rect, []))
  }
  group.appendChild(bands)

  /* Performance bar: 40% of the band, centred, clipped to the track. */
  const barSize = thickness * 0.4
  const value = bullet.value !== null ? bullet.value : 0
  const shown = Math.min(Math.max(value, bullet.domain[0]), bullet.domain[1])
  const rect = toRect(Math.min(Math.max(0, bullet.domain[0]), bullet.domain[1]), shown,
    trackStart + (thickness - barSize) / 2, barSize)
  rect.fill = ctx.colorFor(bullet.name)
  const targetText = bullet.target !== null ? `, target ${formatNumber(bullet.target)}` : ""
  const valueText = bullet.value !== null ? formatNumber(bullet.value) : "no value"
  const text = `${bullet.name}: ${valueText}${targetText}${_rangeOf(bullet)}`
  rect.part = "bullet-bar"
  rect.tabindex = "0"
  rect.role = "img"
  rect["aria-label"] = text
  const bar = svgEl("rect", rect, [svgEl("title", null, text)])
  activate(bar, () => {
    ctx.emit("mj-chart-bullet-click", { name: bullet.name, value: bullet.value, target: bullet.target })
  })
  group.appendChild(bar)

  /* Target tick: a short perpendicular line, haloed so it reads on any band. */
  if (bullet.target !== null) {
    const position = scale(Math.min(Math.max(bullet.target, bullet.domain[0]), bullet.domain[1]))
    const reach = thickness * 0.35
    const center = trackStart + thickness / 2
    const line = horizontal === true
      ? { x1: position, y1: center - reach, x2: position, y2: center + reach }
      : { x1: center - reach, y1: position, x2: center + reach, y2: position }
    group.appendChild(svgEl("line", {
      ...line, stroke: "var(--mj-surface, #ffffff)", "stroke-width": 5, "aria-hidden": "true"
    }, []))
    group.appendChild(svgEl("line", {
      ...line, stroke: TARGET_COLOR, "stroke-width": 3, "stroke-linecap": "butt", part: "bullet-target",
      "aria-hidden": "true"
    }, []))
  }
  return
}


function _ticks(group, scale, domain, horizontal, along, across, length) {
  /*
   * Tick labels of one value scale.
   *
   * :param along: px offset across the track where the labels sit.
   * :param length: The track length (to thin the ticks).
   */
  const labelRoom = horizontal === true
    ? textWidth(formatNumber(domain[1]), TICK_FONT_SIZE) + 14
    : TICK_FONT_SIZE * 2.4
  const count = Math.max(2, Math.min(6, Math.floor(length / labelRoom)))
  const ticks = niceTicks(domain[0], domain[1], count)
  for (let index = 0; index < ticks.length; index = index + 1) {
    const position = scale(ticks[index])
    if (horizontal === true) {
      group.appendChild(svgEl("line", {
        x1: position, y1: along, x2: position, y2: along + 3,
        stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1
      }, []))
      group.appendChild(svgEl("text", {
        x: position, y: along + 3 + TICK_FONT_SIZE, "text-anchor": "middle",
        "font-size": TICK_FONT_SIZE, fill: "var(--mj-text-muted, #5f6673)"
      }, formatNumber(ticks[index])))
    } else {
      group.appendChild(svgEl("line", {
        x1: across - 3, y1: position, x2: across, y2: position,
        stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1
      }, []))
      group.appendChild(svgEl("text", {
        x: across - 5, y: position + 3, "text-anchor": "end",
        "font-size": TICK_FONT_SIZE, fill: "var(--mj-text-muted, #5f6673)"
      }, formatNumber(ticks[index])))
    }
  }
  return
}


export function bulletTable(ctx) {
  /*
   * The accessible table: one row per bullet.
   */
  const rows = ctx.model.series.map((entry) => {
    const bullet = _readBullet(entry)
    const ranges = bullet.ranges.map((range) => {
      const label = range.label !== "" ? `${range.label} ` : ""
      return `${label}≤ ${formatNumber(range.threshold)}`
    }).join(", ")
    return [bullet.name, bullet.value !== null ? bullet.value : "", bullet.target !== null ? bullet.target : "", ranges]
  })
  return { columns: ["Measure", "Value", "Target", "Ranges"], rows: rows }
}


export function render(ctx) {
  /*
   * Render a bullet chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const horizontal = ctx.orientation !== "vertical"
  const root = svgEl("g", { part: "plot" }, [])

  const bullets = model.series.map((entry) => _readBullet(entry))
  if (bullets.length === 0) {
    return root
  }

  /* Shared or independent value scales. */
  const scaleMode = String(ctx.attrs("scale", "auto")).trim().toLowerCase()
  let sharedDomain = [Infinity, -Infinity]
  let identical = true
  for (let index = 0; index < bullets.length; index = index + 1) {
    const domain = bullets[index].domain
    sharedDomain = [Math.min(sharedDomain[0], domain[0]), Math.max(sharedDomain[1], domain[1])]
    if (domain[0] !== bullets[0].domain[0] || domain[1] !== bullets[0].domain[1]) {
      identical = false
    }
  }
  const independent = scaleMode === "independent" || (scaleMode !== "shared" && identical === false)

  /* Key of the range labels, also published as the legend. */
  let rangeCount = 1
  const keyLabels = []
  for (let index = 0; index < bullets.length; index = index + 1) {
    rangeCount = Math.max(rangeCount, bullets[index].ranges.length)
    for (let r = 0; r < bullets[index].ranges.length; r = r + 1) {
      if (keyLabels[r] === undefined && bullets[index].ranges[r].label !== "") {
        keyLabels[r] = bullets[index].ranges[r].label
      }
    }
  }
  const legend = []
  for (let r = 0; r < keyLabels.length; r = r + 1) {
    if (keyLabels[r] !== undefined) {
      legend.push({ label: keyLabels[r], color: _rangeFill(r, rangeCount) })
    }
  }
  if (bullets.some((bullet) => bullet.target !== null) === true) {
    legend.push({ label: "Target", color: TARGET_COLOR })
  }
  ctx.setLegend(legend)
  ctx.setTable(bulletTable(ctx))

  /* A bound <mj-chart-legend> shows the same entries: no inline key then. */
  const key = inlineLegend(ctx.hasLegendPart === true ? [] : legend, 0, 0, Math.max(ctx.width - 16, 40))
  const keyHeight = key.height > 0 ? key.height + 6 : 0

  let labelWidth = 0
  for (let index = 0; index < bullets.length; index = index + 1) {
    labelWidth = Math.max(labelWidth, textWidth(bullets[index].name, LABEL_FONT_SIZE, "600"))
  }

  const margin = { top: 8 + keyHeight, right: 16, bottom: 8, left: 16 }
  if (horizontal === true) {
    margin.left = Math.ceil(Math.min(labelWidth, ctx.width * 0.35) + 18)
    margin.right = Math.round(Math.max(16, textWidth(formatNumber(sharedDomain[1]), TICK_FONT_SIZE) / 2 + 6))
    margin.bottom = independent === true ? 8 : 26
  } else {
    margin.bottom = 26
    margin.left = Math.round(Math.max(28, textWidth(formatNumber(sharedDomain[1]), TICK_FONT_SIZE) + 12))
  }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const plot = svgEl("g", { transform: `translate(${margin.left},${margin.top})` }, [])
  const chrome = svgEl("g", { "aria-hidden": "true", part: "axes" }, [])
  plot.appendChild(chrome)
  root.appendChild(plot)
  key.group.setAttribute("transform", `translate(${8 - margin.left},${-keyHeight})`)
  plot.appendChild(key.group)

  const count = bullets.length
  const slot = (horizontal === true ? plotH : plotW) / count
  const tickRoom = independent === true && horizontal === true ? TICK_FONT_SIZE + 6 : 0
  const thickness = Math.max(4, Math.min(MAX_THICKNESS, slot - 10 - tickRoom))
  const length = horizontal === true ? plotW : plotH

  const sharedScale = horizontal === true
    ? linearScale(sharedDomain, [0, plotW])
    : linearScale(sharedDomain, [plotH, 0])

  for (let index = 0; index < count; index = index + 1) {
    const bullet = bullets[index]
    const scale = independent === true
      ? (horizontal === true ? linearScale(bullet.domain, [0, plotW]) : linearScale(bullet.domain, [plotH, 0]))
      : sharedScale
    const trackStart = index * slot + (slot - thickness - tickRoom) / 2
    const group = svgEl("g", { part: "bullet", "data-series": bullet.name }, [])
    _drawBullet(group, bullet, scale, horizontal, trackStart, thickness, rangeCount, ctx)
    plot.appendChild(group)

    if (horizontal === true) {
      chrome.appendChild(labelText({
        x: -8, y: trackStart + thickness / 2 + 4, "text-anchor": "end",
        "font-size": LABEL_FONT_SIZE, "font-weight": "600", fill: "var(--mj-text, #14181f)"
      }, bullet.name, margin.left - 12, LABEL_FONT_SIZE, "600"))
      if (independent === true) {
        _ticks(chrome, scale, bullet.domain, true, trackStart + thickness + 1, 0, length)
      }
    } else {
      chrome.appendChild(labelText({
        x: trackStart + thickness / 2, y: plotH + 18, "text-anchor": "middle",
        "font-size": LABEL_FONT_SIZE, "font-weight": "600", fill: "var(--mj-text, #14181f)"
      }, bullet.name, slot - 4, LABEL_FONT_SIZE, "600"))
      if (independent === true) {
        _ticks(chrome, scale, bullet.domain, false, 0, trackStart - 2, length)
      }
    }
  }

  if (independent === false) {
    if (horizontal === true) {
      _ticks(chrome, sharedScale, sharedDomain, true, plotH + 2, 0, length)
    } else {
      _ticks(chrome, sharedScale, sharedDomain, false, 0, -2, length)
    }
  }

  return root
}


registerRenderer("bullet", render, { orientation: "horizontal", table: bulletTable });
