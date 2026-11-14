/*
 * pie.js
 *
 * Pie and Donut renderer.
 *
 * Registers: "pie", "donut"
 *
 * ctx.model.categories  -- slice labels (up to 12; excess collapsed to "Other")
 * ctx.model.series[0]   -- first series only; .values are the slice magnitudes
 * ctx.attrs("inner-radius", ...) -- fraction 0-0.95 of the outer radius; > 0
 *                          draws a ring. Default 0 for "pie", 0.5 for "donut".
 * ctx.model.meta["center-label"] -- optional string drawn at the centre (donut)
 *
 * Values must be non-negative numbers. A null (or any non-number) is a gap:
 * the category gets no slice. A negative value is invalid: it is left out
 * and the chart emits `mj-chart-error` naming the categories, while the
 * remaining slices are still drawn.
 *
 * Every slice has its own colour (ctx.colorFor(categoryIndex)), and the
 * legend lists the slices. When there is room beside the pie, each slice is
 * also labelled outside the circle (name and share, with a leader line and
 * de-collided per side); otherwise wide slices carry their share inside and
 * the legend names them.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, arcPath, formatNumber } from "../svgdraw.js";


const MAX_SLICES = 12;
const TWO_PI = Math.PI * 2;
const MARGIN = 12;
const LABEL_FONT = 11;
const LABEL_LINE = 14;
const INSIDE_LABEL_MIN_FRACTION = 0.07;
const MIN_LABELLED_RADIUS = 48;


function _textWidth(text, fontSize) {
  /*
   * Estimate the rendered width of a label (no layout pass is available
   * while the drawing is built).
   */
  const width = String(text).length * fontSize * 0.58
  return width
}


function _fitText(text, maxWidth, fontSize) {
  /*
   * Shorten a label with an ellipsis so it fits a width.
   *
   * :returns: The label, possibly truncated; "" when nothing fits.
   */
  const label = String(text)
  if (_textWidth(label, fontSize) <= maxWidth) {
    return label
  }
  const characters = Math.floor(maxWidth / (fontSize * 0.58)) - 1
  if (characters < 2) {
    return ""
  }
  const fitted = label.slice(0, characters) + "…"
  return fitted
}


function _percentText(fraction) {
  /*
   * A share as a percentage label ("23%", "0.4%").
   */
  const percent = fraction * 100
  const digits = percent > 0 && percent < 1 ? 1 : 0
  const text = `${formatNumber(percent, { maximumFractionDigits: digits })}%`
  return text
}


function _innerFraction(ctx) {
  /*
   * The ring's inner radius as a fraction of the outer radius: the
   * inner-radius attribute when it is a number, else the type's default.
   */
  const fallback = ctx.type === "donut" ? "0.5" : "0"
  const parsed = parseFloat(ctx.attrs("inner-radius", fallback))
  let fraction = Number.isFinite(parsed) === true ? parsed : parseFloat(fallback)
  fraction = Math.min(Math.max(fraction, 0), 0.95)
  return fraction
}


function _collectEntries(categories, values) {
  /*
   * Pair categories with their values and split out the invalid ones.
   *
   * :returns: { entries: [{ label, value, colorIndex }], negatives: [label] }
   *     with only the positive, finite values in `entries`.
   */
  const entries = []
  const negatives = []
  for (let index = 0; index < categories.length; index = index + 1) {
    const value = values[index]
    if (typeof value !== "number" || Number.isFinite(value) === false) {
      continue
    }
    if (value < 0) {
      negatives.push(String(categories[index]))
      continue
    }
    if (value === 0) {
      continue
    }
    entries.push({ label: String(categories[index]), value: value, colorIndex: index })
  }
  const collected = { entries: entries, negatives: negatives }
  return collected
}


function _buildSlices(entries) {
  /*
   * Collapse excess slices into "Other" and compute fractions and angles.
   *
   * :param entries: [{ label, value, colorIndex }] with positive values.
   * :returns: Array of { label, value, fraction, startAngle, endAngle,
   *     colorIndex }, or [] when there is nothing to draw.
   */
  let kept = entries.slice()
  if (kept.length > MAX_SLICES) {
    const head = kept.slice(0, MAX_SLICES - 1)
    let otherSum = 0
    for (let index = MAX_SLICES - 1; index < kept.length; index = index + 1) {
      otherSum = otherSum + kept[index].value
    }
    head.push({ label: "Other", value: otherSum, colorIndex: kept[MAX_SLICES - 1].colorIndex })
    kept = head
  }

  let total = 0
  for (let index = 0; index < kept.length; index = index + 1) {
    total = total + kept[index].value
  }
  if (total <= 0) {
    return []
  }

  const slices = []
  let cursor = 0
  for (let index = 0; index < kept.length; index = index + 1) {
    const entry = kept[index]
    const fraction = entry.value / total
    const endAngle = index === kept.length - 1 ? TWO_PI : cursor + fraction * TWO_PI
    slices.push({
      label: entry.label,
      value: entry.value,
      fraction: fraction,
      startAngle: cursor,
      endAngle: endAngle,
      colorIndex: entry.colorIndex
    })
    cursor = endAngle
  }
  return slices
}


function _declutter(labels, top, bottom) {
  /*
   * Spread the outside labels of one side vertically so they do not
   * overlap, keeping each as close to its slice as possible.
   *
   * :param labels: [{ y }] on one side; `y` is adjusted in place.
   * :param top: The smallest allowed y.
   * :param bottom: The largest allowed y.
   */
  labels.sort((a, b) => a.y - b.y)
  for (let index = 0; index < labels.length; index = index + 1) {
    const previous = index > 0 ? labels[index - 1].y + LABEL_LINE : top
    labels[index].y = Math.max(labels[index].y, previous)
  }
  /* Pushed past the bottom: shift the run back up from the end. */
  for (let index = labels.length - 1; index >= 0; index = index - 1) {
    const next = index < labels.length - 1 ? labels[index + 1].y - LABEL_LINE : bottom
    labels[index].y = Math.min(labels[index].y, next)
  }
  return
}


function _pieTable(slices, valueName) {
  /*
   * The accessible table: one row per slice.
   */
  const rows = slices.map((slice) => {
    return [slice.label, slice.value, _percentText(slice.fraction)]
  })
  const table = { columns: ["Category", valueName, "Share"], rows: rows }
  return table
}


export function render(ctx) {
  /*
   * Render a pie or donut chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const root = svgEl("g", { part: "plot" }, [])

  const series = model.series
  const categories = model.categories
  if (categories.length === 0 || series.length === 0) {
    return root
  }

  const firstSeries = series[0]
  const collected = _collectEntries(categories, firstSeries.values)
  if (collected.negatives.length > 0) {
    ctx.emit("mj-chart-error", {
      message: `${ctx.type}: negative values are not drawn (${collected.negatives.join(", ")})`
    })
  }

  const slices = _buildSlices(collected.entries)
  if (slices.length === 0) {
    return root
  }

  for (let index = 0; index < slices.length; index = index + 1) {
    slices[index].color = ctx.colorFor(slices[index].colorIndex)
  }

  ctx.setLegend(slices.map((slice) => {
    return { label: slice.label, color: slice.color }
  }))
  ctx.setTable(_pieTable(slices, String(firstSeries.name || "Value")))

  const innerFraction = _innerFraction(ctx)
  const plotW = Math.max(ctx.width - MARGIN * 2, 10)
  const plotH = Math.max(ctx.height - MARGIN * 2, 10)
  const cx = MARGIN + plotW / 2
  const cy = MARGIN + plotH / 2

  /*
   * Room for outside labels: the longest "name 00%" beside the pie on
   * both sides, capped so the pie keeps most of the width.
   */
  let longest = 0
  for (let index = 0; index < slices.length; index = index + 1) {
    const text = `${slices[index].label} ${_percentText(slices[index].fraction)}`
    longest = Math.max(longest, _textWidth(text, LABEL_FONT))
  }
  const labelSpace = Math.min(longest + 24, plotW * 0.3)
  const labelledRadius = Math.min((plotW - labelSpace * 2) / 2, plotH / 2 - 4)
  const outsideLabels = labelledRadius >= MIN_LABELLED_RADIUS
  const outerRadius = outsideLabels === true ? labelledRadius : Math.max(Math.min(plotW, plotH) / 2, 4)
  const innerRadius = outerRadius * innerFraction

  /* Draw wedges. */
  const wedges = svgEl("g", { part: "slices" }, [])
  root.appendChild(wedges)
  const decoration = svgEl("g", { "aria-hidden": "true", "pointer-events": "none" }, [])
  root.appendChild(decoration)

  for (let index = 0; index < slices.length; index = index + 1) {
    const slice = slices[index]
    const share = _percentText(slice.fraction)
    const description = `${slice.label}: ${formatNumber(slice.value)} (${share})`

    const wedge = svgEl("path", {
      d: arcPath(cx, cy, innerRadius, outerRadius, slice.startAngle, slice.endAngle),
      fill: slice.color,
      stroke: slices.length > 1 ? "var(--mj-surface, #ffffff)" : "none",
      "stroke-width": 1.5,
      part: "slice",
      tabindex: "0",
      role: "img",
      "aria-label": description
    }, [svgEl("title", null, description)])

    const handler = () => {
      ctx.emit("mj-chart-slice-click", {
        label: slice.label,
        value: slice.value,
        fraction: slice.fraction
      })
    }
    wedge.addEventListener("click", handler)
    wedge.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        handler()
      }
    })
    wedges.appendChild(wedge)

    /* Share inside the wedge when there are no outside labels. */
    if (outsideLabels === false && slice.fraction >= INSIDE_LABEL_MIN_FRACTION && outerRadius >= 30) {
      const midAngle = (slice.startAngle + slice.endAngle) / 2
      const labelRadius = slices.length === 1 && innerRadius === 0
        ? 0
        : innerRadius + (outerRadius - innerRadius) * 0.6
      decoration.appendChild(svgEl("text", {
        x: (cx + labelRadius * Math.sin(midAngle)).toFixed(2),
        y: (cy - labelRadius * Math.cos(midAngle)).toFixed(2),
        "text-anchor": "middle",
        "dominant-baseline": "middle",
        "font-size": LABEL_FONT,
        "font-weight": "600",
        fill: "var(--mj-text-on-accent, #ffffff)"
      }, share))
    }
  }

  /* Outside labels: name and share, leader line, de-collided per side. */
  if (outsideLabels === true) {
    const left = []
    const right = []
    for (let index = 0; index < slices.length; index = index + 1) {
      const slice = slices[index]
      const midAngle = slices.length === 1 ? Math.PI / 2 : (slice.startAngle + slice.endAngle) / 2
      const anchor = {
        slice: slice,
        angle: midAngle,
        y: cy - (outerRadius + 10) * Math.cos(midAngle)
      }
      if (Math.sin(midAngle) >= 0) {
        right.push(anchor)
      } else {
        left.push(anchor)
      }
    }
    const top = MARGIN + LABEL_LINE / 2
    const bottom = ctx.height - MARGIN - LABEL_LINE / 2
    _declutter(left, top, bottom)
    _declutter(right, top, bottom)

    const sides = [{ labels: left, sign: -1 }, { labels: right, sign: 1 }]
    for (let side = 0; side < sides.length; side = side + 1) {
      const sign = sides[side].sign
      const labels = sides[side].labels
      for (let index = 0; index < labels.length; index = index + 1) {
        const label = labels[index]
        const edge = { x: cx + outerRadius * Math.sin(label.angle), y: cy - outerRadius * Math.cos(label.angle) }
        const elbowX = cx + sign * (outerRadius + 10)
        const textX = cx + sign * (outerRadius + 16)
        const room = sign > 0 ? ctx.width - MARGIN - textX : textX - MARGIN
        const share = _percentText(label.slice.fraction)
        const name = _fitText(label.slice.label, room - _textWidth(` ${share}`, LABEL_FONT), LABEL_FONT)

        decoration.appendChild(svgEl("polyline", {
          points: `${edge.x.toFixed(2)},${edge.y.toFixed(2)} ` +
            `${elbowX.toFixed(2)},${label.y.toFixed(2)} ` +
            `${(textX - sign * 3).toFixed(2)},${label.y.toFixed(2)}`,
          fill: "none",
          stroke: "var(--mj-text-muted, #5f6673)",
          "stroke-width": 1
        }, []))
        decoration.appendChild(svgEl("text", {
          x: textX.toFixed(2),
          y: label.y.toFixed(2),
          "text-anchor": sign > 0 ? "start" : "end",
          "dominant-baseline": "middle",
          "font-size": LABEL_FONT,
          fill: "var(--mj-text, #14181f)"
        }, [
          name.length > 0 ? `${name} ` : "",
          svgEl("tspan", { "font-weight": "600" }, share)
        ]))
      }
    }
  }

  /* Centre label (rings only). */
  const centerLabel = model.meta !== null && model.meta !== undefined ? model.meta["center-label"] : null
  if (centerLabel !== null && centerLabel !== undefined && innerRadius > 0) {
    const fontSize = Math.max(Math.min(16, innerRadius / 3), 9)
    const text = _fitText(String(centerLabel), innerRadius * 1.8, fontSize)
    decoration.appendChild(svgEl("text", {
      x: cx.toFixed(2),
      y: cy.toFixed(2),
      "text-anchor": "middle",
      "dominant-baseline": "middle",
      "font-size": fontSize.toFixed(1),
      "font-weight": "600",
      fill: "var(--mj-text, #14181f)"
    }, text))
  }

  return root
}


function _isEmpty(model) {
  /*
   * Nothing to draw: the first visible series has no positive value.
   */
  if (model.series.length === 0) {
    return true
  }
  const values = model.series[0].values
  for (let index = 0; index < values.length; index = index + 1) {
    const value = values[index]
    if (typeof value === "number" && Number.isFinite(value) === true && value > 0) {
      return false
    }
  }
  return true
}


registerRenderer("pie", render, { legend: "categories", isEmpty: _isEmpty });
registerRenderer("donut", render, { legend: "categories", isEmpty: _isEmpty });
