/*
 * waterfall.js
 *
 * Waterfall (bridge / cascade) renderer.
 *
 * Registers: "waterfall"
 *
 * ctx.model.categories            -- bar labels (may repeat; bars are placed
 *                                    by position)
 * ctx.model.series[0].values      -- one step per category, either
 *                                      a number (the amount), with the kind in
 *                                      series[0].kinds[i], or
 *                                      an object { v | value, kind | type }
 *                                    null (or { v: null }) on a subtotal or
 *                                    total means "computed from the running sum"
 * ctx.model.series[0].kinds       -- optional, parallel to values
 * ctx.orientation                 -- "vertical" (default) | "horizontal"
 *
 * Kinds (case-insensitive):
 *   start              opening bar, grounded at zero; sets the running total
 *   delta              floating step by the signed amount (the default)
 *   add / increase     floating step up by |amount|
 *   subtract / decrease  floating step down by |amount|
 *   subtotal / total   grounded bar at the running total; a numeric amount is
 *                      an explicit checkpoint that sets the running total
 * An unknown kind is drawn as a delta and the chart emits `mj-chart-error`.
 *
 * Increases use --mj-chart-positive, decreases --mj-chart-negative (both
 * default to a colour-vision-safe blue / orange pair from the series
 * palette); start, subtotal and total bars are neutral. Every bar carries a
 * value label (signed for steps), dashed connectors join each bar's end
 * level to the next bar, and the legend explains the three colours.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { linearScale, bandScale, niceTicks, niceDomain, seriesColor } from "../scales.js";


const COLOR_POSITIVE = `var(--mj-chart-positive, ${seriesColor(0)})`;
const COLOR_NEGATIVE = `var(--mj-chart-negative, ${seriesColor(1)})`;
const COLOR_NEUTRAL = "var(--mj-chart-neutral, var(--mj-text-muted, #5f6673))";

const VALUE_FONT = 11;
const LABEL_FONT = 11;

const KIND_ALIASES = {
  start: "start",
  delta: "delta",
  add: "add",
  increase: "add",
  subtract: "subtract",
  decrease: "subtract",
  subtotal: "subtotal",
  total: "total"
};


function _textWidth(text, fontSize) {
  /*
   * Estimate the rendered width of a label.
   */
  const width = String(text).length * fontSize * 0.58
  return width
}


function _fitText(text, maxWidth, fontSize) {
  /*
   * Shorten a label with an ellipsis so it fits a width.
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


function _readStep(rawValue, rawKind) {
  /*
   * Read one step from either the number + kinds form or the object form.
   *
   * :returns: { amount: number|null, kindText: string }
   */
  let amount = rawValue
  let kindText = rawKind
  if (rawValue !== null && typeof rawValue === "object") {
    amount = rawValue.v !== undefined ? rawValue.v : rawValue.value
    const ownKind = rawValue.kind !== undefined ? rawValue.kind : rawValue.type
    if (ownKind !== undefined && ownKind !== null) {
      kindText = ownKind
    }
  }
  const numeric = typeof amount === "number" && Number.isFinite(amount) === true ? amount : null
  const text = kindText === undefined || kindText === null || kindText === "" ? "delta" : String(kindText)
  const step = { amount: numeric, kindText: text }
  return step
}


function _signed(value) {
  /*
   * A step amount with an explicit sign ("+120", "-80").
   */
  const magnitude = formatNumber(Math.abs(value))
  const text = value > 0 ? `+${magnitude}` : (value < 0 ? `-${magnitude}` : magnitude)
  return text
}


function _buildBars(categories, values, kinds) {
  /*
   * Compute the running total and each bar's [base, top] in data units.
   *
   * :returns: { bars: [{ category, index, kind, amount, value, base, top,
   *     end, color, label }], unknownKinds: [text] }
   */
  const bars = []
  const unknownKinds = []
  let running = 0

  for (let index = 0; index < categories.length; index = index + 1) {
    const step = _readStep(values[index], Array.isArray(kinds) === true ? kinds[index] : undefined)
    let kind = KIND_ALIASES[step.kindText.toLowerCase()]
    if (kind === undefined) {
      unknownKinds.push(step.kindText)
      kind = "delta"
    }

    let base = 0
    let top = 0
    let value = 0
    let color = COLOR_NEUTRAL
    let label = ""
    let group = "total"

    if (kind === "start") {
      value = step.amount !== null ? step.amount : 0
      base = 0
      top = value
      running = value
      label = formatNumber(value)
    } else if (kind === "subtotal" || kind === "total") {
      if (step.amount !== null) {
        running = step.amount
      }
      value = running
      base = 0
      top = running
      label = formatNumber(value)
    } else {
      let amount = step.amount !== null ? step.amount : 0
      if (kind === "add") {
        amount = Math.abs(amount)
      } else if (kind === "subtract") {
        amount = -Math.abs(amount)
      }
      value = amount
      base = running
      top = running + amount
      running = top
      color = amount >= 0 ? COLOR_POSITIVE : COLOR_NEGATIVE
      group = amount >= 0 ? "increase" : "decrease"
      label = _signed(amount)
    }

    bars.push({
      category: String(categories[index]),
      index: index,
      kind: kind,
      group: group,
      value: value,
      base: base,
      top: top,
      end: running,
      color: color,
      label: label
    })
  }
  const built = { bars: bars, unknownKinds: unknownKinds }
  return built
}


export function render(ctx) {
  /*
   * Render a waterfall chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const horizontal = ctx.orientation === "horizontal"
  const root = svgEl("g", { part: "plot" }, [])

  const categories = model.categories
  const series = model.series
  if (categories.length === 0 || series.length === 0) {
    return root
  }

  const firstSeries = series[0]
  const built = _buildBars(categories, firstSeries.values, firstSeries.kinds)
  const bars = built.bars
  if (built.unknownKinds.length > 0) {
    ctx.emit("mj-chart-error", {
      message: `waterfall: unknown step kind(s) drawn as deltas (${built.unknownKinds.join(", ")})`
    })
  }

  ctx.setTable({
    columns: ["Step", "Kind", "Amount", "Running total"],
    rows: bars.map((bar) => [bar.category, bar.kind, bar.kind === "subtotal" || bar.kind === "total" ? bar.value : bar.label, bar.end])
  })
  const legend = []
  const groupsSeen = new Set(bars.map((bar) => bar.group))
  if (groupsSeen.has("increase") === true) {
    legend.push({ label: "Increase", color: COLOR_POSITIVE })
  }
  if (groupsSeen.has("decrease") === true) {
    legend.push({ label: "Decrease", color: COLOR_NEGATIVE })
  }
  if (groupsSeen.has("total") === true) {
    legend.push({ label: "Total", color: COLOR_NEUTRAL })
  }
  ctx.setLegend(legend)

  /* Value domain spans all bases and tops, widened to tick boundaries. */
  let valueMin = 0
  let valueMax = 0
  for (let index = 0; index < bars.length; index = index + 1) {
    valueMin = Math.min(valueMin, bars[index].base, bars[index].top)
    valueMax = Math.max(valueMax, bars[index].base, bars[index].top)
  }
  if (valueMax === valueMin) {
    valueMax = valueMin + 1
  }
  const domain = niceDomain(valueMin, valueMax, 5)

  /* Margins: tick labels on the value side, category labels on the other. */
  let longestCategory = 0
  for (let index = 0; index < bars.length; index = index + 1) {
    longestCategory = Math.max(longestCategory, _textWidth(bars[index].category, LABEL_FONT))
  }
  const tickWidth = Math.max(_textWidth(formatNumber(domain[0]), 11), _textWidth(formatNumber(domain[1]), 11))
  const margin = horizontal === true
    ? { top: 12, right: 48, bottom: 28, left: Math.min(Math.max(longestCategory + 12, 40), ctx.width * 0.3) }
    : { top: 20, right: 16, bottom: 34, left: Math.max(tickWidth + 14, 36) }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const cat = bandScale(bars.map((bar) => bar.category), [0, horizontal === true ? plotH : plotW], 0.25)
  const val = horizontal === true
    ? linearScale(domain, [0, plotW])
    : linearScale(domain, [plotH, 0])
  const bandwidth = cat.bandwidth()
  const step = cat.step()

  const plot = svgEl("g", { transform: `translate(${margin.left},${margin.top})` }, [])
  root.appendChild(plot)

  /* Gridlines, tick labels and the zero line: decoration. */
  const axis = svgEl("g", { "aria-hidden": "true" }, [])
  plot.appendChild(axis)
  const ticks = niceTicks(domain[0], domain[1], 5)
  for (let t = 0; t < ticks.length; t = t + 1) {
    const position = val(ticks[t])
    if (horizontal === true) {
      axis.appendChild(svgEl("line", {
        x1: position.toFixed(2), y1: 0, x2: position.toFixed(2), y2: plotH,
        stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
      }, []))
      axis.appendChild(svgEl("text", {
        x: position.toFixed(2), y: plotH + 16, "text-anchor": "middle",
        "font-size": 11, fill: "var(--mj-text-muted, #5f6673)"
      }, formatNumber(ticks[t])))
    } else {
      axis.appendChild(svgEl("line", {
        x1: 0, y1: position.toFixed(2), x2: plotW, y2: position.toFixed(2),
        stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
      }, []))
      axis.appendChild(svgEl("text", {
        x: -8, y: (position + 4).toFixed(2), "text-anchor": "end",
        "font-size": 11, fill: "var(--mj-text-muted, #5f6673)"
      }, formatNumber(ticks[t])))
    }
  }
  const zero = val(0)
  if (horizontal === true) {
    axis.appendChild(svgEl("line", {
      x1: zero.toFixed(2), y1: 0, x2: zero.toFixed(2), y2: plotH,
      stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
    }, []))
  } else {
    axis.appendChild(svgEl("line", {
      x1: 0, y1: zero.toFixed(2), x2: plotW, y2: zero.toFixed(2),
      stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
    }, []))
  }

  /* Connectors: from each bar's end level to the next bar, every pair. */
  const connectors = svgEl("g", { "aria-hidden": "true" }, [])
  plot.appendChild(connectors)
  for (let index = 0; index < bars.length - 1; index = index + 1) {
    const level = val(bars[index].end)
    const from = cat.at(index) + bandwidth
    const to = cat.at(index + 1)
    if (horizontal === true) {
      connectors.appendChild(svgEl("line", {
        x1: level.toFixed(2), y1: from.toFixed(2), x2: level.toFixed(2), y2: to.toFixed(2),
        stroke: "var(--mj-text-muted, #5f6673)", "stroke-width": 1, "stroke-dasharray": "3,2"
      }, []))
    } else {
      connectors.appendChild(svgEl("line", {
        x1: from.toFixed(2), y1: level.toFixed(2), x2: to.toFixed(2), y2: level.toFixed(2),
        stroke: "var(--mj-text-muted, #5f6673)", "stroke-width": 1, "stroke-dasharray": "3,2"
      }, []))
    }
  }

  /* Bars. */
  const marks = svgEl("g", { part: "bars" }, [])
  plot.appendChild(marks)
  const labels = svgEl("g", { "aria-hidden": "true", "pointer-events": "none" }, [])
  plot.appendChild(labels)

  const labelFits = horizontal === true
    ? bandwidth >= VALUE_FONT
    : bars.every((bar) => _textWidth(bar.label, VALUE_FONT) <= step - 2)
  const valueFont = labelFits === true || horizontal === true ? VALUE_FONT : 9

  for (let index = 0; index < bars.length; index = index + 1) {
    const bar = bars[index]
    const bandStart = cat.at(index)
    const p1 = val(bar.base)
    const p2 = val(bar.top)
    const description = bar.kind === "subtotal" || bar.kind === "total" || bar.kind === "start"
      ? `${bar.category} (${bar.kind}): ${formatNumber(bar.value)}`
      : `${bar.category}: ${bar.label}, running total ${formatNumber(bar.end)}`

    const attributes = horizontal === true
      ? {
          x: Math.min(p1, p2).toFixed(2),
          y: bandStart.toFixed(2),
          width: Math.max(Math.abs(p2 - p1), 1).toFixed(2),
          height: Math.max(bandwidth, 1).toFixed(2)
        }
      : {
          x: bandStart.toFixed(2),
          y: Math.min(p1, p2).toFixed(2),
          width: Math.max(bandwidth, 1).toFixed(2),
          height: Math.max(Math.abs(p2 - p1), 1).toFixed(2)
        }
    const rect = svgEl("rect", {
      ...attributes,
      rx: 2,
      fill: bar.color,
      part: "bar",
      tabindex: "0",
      role: "img",
      "aria-label": description
    }, [svgEl("title", null, description)])

    const handler = () => {
      ctx.emit("mj-chart-bar-click", {
        category: bar.category,
        index: bar.index,
        value: bar.value,
        kind: bar.kind,
        runningTotal: bar.end
      })
    }
    rect.addEventListener("click", handler)
    rect.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        handler()
      }
    })
    marks.appendChild(rect)

    /* Value label beyond the bar's outer end (above an increase, below a fall). */
    const upward = bar.top >= bar.base
    if (horizontal === true) {
      const outer = upward === true ? Math.max(p1, p2) + 4 : Math.min(p1, p2) - 4
      labels.appendChild(svgEl("text", {
        x: outer.toFixed(2),
        y: (bandStart + bandwidth / 2).toFixed(2),
        "text-anchor": upward === true ? "start" : "end",
        "dominant-baseline": "middle",
        "font-size": valueFont,
        fill: "var(--mj-text, #14181f)"
      }, bar.label))
    } else if (labelFits === true || valueFont < VALUE_FONT) {
      const outer = upward === true ? Math.min(p1, p2) - 4 : Math.max(p1, p2) + valueFont + 2
      labels.appendChild(svgEl("text", {
        x: (bandStart + bandwidth / 2).toFixed(2),
        y: outer.toFixed(2),
        "text-anchor": "middle",
        "font-size": valueFont,
        fill: "var(--mj-text, #14181f)"
      }, bar.label))
    }

    /* Category label. */
    if (horizontal === true) {
      labels.appendChild(svgEl("text", {
        x: -8,
        y: (bandStart + bandwidth / 2).toFixed(2),
        "text-anchor": "end",
        "dominant-baseline": "middle",
        "font-size": LABEL_FONT,
        fill: "var(--mj-text, #14181f)"
      }, _fitText(bar.category, margin.left - 12, LABEL_FONT)))
    } else {
      labels.appendChild(svgEl("text", {
        x: (bandStart + bandwidth / 2).toFixed(2),
        y: (plotH + 18).toFixed(2),
        "text-anchor": "middle",
        "font-size": LABEL_FONT,
        fill: "var(--mj-text, #14181f)"
      }, _fitText(bar.category, step - 2, LABEL_FONT)))
    }
  }

  return root
}


registerRenderer("waterfall", render, { legend: "none" });
