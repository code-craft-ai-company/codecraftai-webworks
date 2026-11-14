/*
 * bar.js
 *
 * Bar / column renderer -- the REFERENCE renderer, and the pattern every
 * other renderer follows. It also exports the small chart-chrome helpers the
 * comparison and trend renderers share (text measuring, label truncation,
 * option parsing, the category / value frame and an inline legend).
 *
 * A renderer is `render(ctx) -> SVGElement`:
 *   ctx.type        the type key the page asked for ("bar" | "column")
 *   ctx.model       normalized model { meta, categories, series, raw }
 *   ctx.raw         the raw data object
 *   ctx.width       drawing surface width (px)
 *   ctx.height      drawing surface height (px)
 *   ctx.orientation "vertical" (columns) | "horizontal" (bars)
 *   ctx.attrs       (name, fallback) -> controller attribute value
 *   ctx.colorFor    (seriesIndex | seriesName) -> CSS color
 *   ctx.emit        (eventName, detail) -> dispatch an interaction event
 * It returns an <g> SVGElement drawn within [0..width] x [0..height].
 *
 * Attributes:
 *   group   "cluster" (default) | "stack" | "stack100"; "grouped" and
 *           "stacked" are read as "cluster" and "stack", any other value as
 *           "cluster"
 *   sort    "none" (default) | "asc" | "desc" -- order categories by their
 *           total across the visible series
 *
 * Missing values (null, non-numeric text) draw no bar; numeric strings such
 * as "10" are read as numbers. Categories are positioned by index, so two
 * categories with the same label keep their own bars. In stack100 mode each
 * value becomes its signed share of the category's absolute total: positive
 * shares stack upward from zero, negative shares downward.
 *
 * Consolidated catalog names: Bar, Column (orientation), Grouped/Stacked/
 * 100%-stacked bar (the `group` attribute), Sorted bar (`sort`).
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { linearScale, bandScale, niceTicks, niceDomain } from "../scales.js";

/* Font size of axis and category labels. */
export const LABEL_FONT_SIZE = 11;

/* Rotation of crowded category labels (degrees, counter-clockwise). */
const LABEL_ROTATION = 40;

/* A tick label wider than this switches the value axis to compact numbers. */
const COMPACT_TICK_WIDTH = 52;

const GROUP_MODES = { cluster: "cluster", grouped: "cluster", stack: "stack", stacked: "stack", stack100: "stack100" };

/* Canvas context used to measure label text (created on first use). */
let MEASURE_CONTEXT = null;

/* Counter that keeps clip-path ids unique inside one shadow root. */
let CLIP_COUNTER = 0;


export function textWidth(text, fontSize, fontWeight) {
  /*
   * Measure the rendered width of a label.
   *
   * :param text: The label text.
   * :param fontSize: Font size in px (default LABEL_FONT_SIZE).
   * :param fontWeight: Optional CSS font weight ("600").
   * :returns: The width in px (an estimate when no canvas is available).
   */
  const value = text === null || text === undefined ? "" : String(text)
  const size = typeof fontSize === "number" && fontSize > 0 ? fontSize : LABEL_FONT_SIZE
  const weight = fontWeight !== undefined && fontWeight !== null ? fontWeight : "400"

  if (MEASURE_CONTEXT === null && typeof document !== "undefined") {
    const canvas = document.createElement("canvas")
    MEASURE_CONTEXT = canvas.getContext("2d")
  }

  let width = value.length * size * 0.6
  if (MEASURE_CONTEXT !== null && MEASURE_CONTEXT !== undefined) {
    MEASURE_CONTEXT.font = `${weight} ${size}px system-ui, -apple-system, "Segoe UI", sans-serif`
    width = MEASURE_CONTEXT.measureText(value).width * 1.04
  }
  return width
}


export function truncateText(text, maxWidth, fontSize, fontWeight) {
  /*
   * Shorten a label with an ellipsis so it fits a width.
   *
   * :param text: The label text.
   * :param maxWidth: The available width in px.
   * :param fontSize: Font size in px.
   * :returns: The label, or its longest prefix that fits followed by "…".
   */
  const value = text === null || text === undefined ? "" : String(text)
  if (textWidth(value, fontSize, fontWeight) <= maxWidth) {
    return value
  }

  let low = 0
  let high = value.length
  while (low < high) {
    const middle = Math.ceil((low + high) / 2)
    const candidate = value.slice(0, middle) + "…"
    if (textWidth(candidate, fontSize, fontWeight) <= maxWidth) {
      low = middle
    } else {
      high = middle - 1
    }
  }
  const shortened = low > 0 ? value.slice(0, low).trimEnd() + "…" : "…"
  return shortened
}


export function labelText(attrs, text, maxWidth, fontSize, fontWeight) {
  /*
   * Build a <text> element whose content is truncated to a width; a
   * truncated label carries its full text in a <title>.
   *
   * :param attrs: The <text> attributes.
   * :param text: The full label.
   * :param maxWidth: The available width in px (Infinity: no limit).
   * :returns: The SVG <text> element.
   */
  const full = text === null || text === undefined ? "" : String(text)
  const size = typeof fontSize === "number" ? fontSize : LABEL_FONT_SIZE
  const shown = Number.isFinite(maxWidth) === true
    ? truncateText(full, Math.max(maxWidth, 8), size, fontWeight)
    : full
  const children = [shown]
  if (shown !== full) {
    children.push(svgEl("title", null, full))
  }
  const element = svgEl("text", attrs, children)
  return element
}


/*
 * booleanOption lives in ../chartoptions.js (shared by every renderer); it is
 * re-exported here for renderers and pages that import it from bar.js.
 */
export { booleanOption } from "../chartoptions.js";


export function numericValue(value) {
  /*
   * Read a data value as a number.
   *
   * :param value: A number, a numeric string ("10", " 2.5 ") or anything.
   * :returns: A finite number, or null for a missing / non-numeric value.
   */
  let numeric = null
  if (typeof value === "number") {
    numeric = Number.isFinite(value) === true ? value : null
  } else if (typeof value === "string" && value.trim().length > 0) {
    const parsed = Number(value)
    numeric = Number.isFinite(parsed) === true ? parsed : null
  }
  return numeric
}


export function nextClipId(prefix) {
  /*
   * A clip-path id that is unique within the page.
   */
  CLIP_COUNTER = CLIP_COUNTER + 1
  const id = `${prefix}-${CLIP_COUNTER}`
  return id
}


export function categoryOrder(model, sortMode) {
  /*
   * The categories in drawing order, each with its data index, optionally
   * sorted by the category's total across the visible series. Ordering by
   * index keeps duplicate labels apart.
   *
   * :param model: The chart model.
   * :param sortMode: "asc" | "desc" | anything else (data order).
   * :returns: An array of { label, index }.
   */
  const entries = model.categories.map((category, index) => {
    let sum = 0
    for (let s = 0; s < model.series.length; s = s + 1) {
      const value = numericValue(model.series[s].values[index])
      sum = sum + (value !== null ? value : 0)
    }
    const label = category === null || category === undefined ? "" : String(category)
    return { label: label, index: index, sum: sum }
  })

  if (sortMode === "asc" || sortMode === "desc") {
    /* Stable sort: equal totals keep their data order. */
    entries.sort((a, b) => {
      const difference = sortMode === "asc" ? a.sum - b.sum : b.sum - a.sum
      return difference !== 0 ? difference : a.index - b.index
    })
  }
  const ordered = entries.map((entry) => ({ label: entry.label, index: entry.index }))
  return ordered
}


export function tickFormatter(ticks, percent) {
  /*
   * Choose the label format of value ticks: plain locale numbers, compact
   * numbers ("10M") when plain labels would be too wide, and a "%" suffix
   * for percentage axes.
   *
   * :param ticks: The tick values.
   * :param percent: True for a percentage axis.
   * :returns: A function (value) -> label.
   */
  let compact = false
  for (let index = 0; index < ticks.length; index = index + 1) {
    if (textWidth(formatNumber(ticks[index])) > COMPACT_TICK_WIDTH) {
      compact = true
      break
    }
  }
  const suffix = percent === true ? "%" : ""
  const format = (value) => {
    const text = compact === true
      ? formatNumber(value, { notation: "compact", maximumFractionDigits: 1 })
      : formatNumber(value)
    return `${text}${suffix}`
  }
  return format
}


export function valueTicks(domain, length, labelWidth) {
  /*
   * Nice ticks for a value axis, thinned so their labels do not collide.
   *
   * :param domain: The [min, max] value domain.
   * :param length: The axis length in px.
   * :param labelWidth: The room one tick label needs along the axis.
   * :returns: An array of tick values inside the domain.
   */
  const room = Math.max(labelWidth, 1)
  const count = Math.max(2, Math.min(6, Math.floor(length / room)))
  const ticks = niceTicks(domain[0], domain[1], count)
  return ticks
}


export function categoryValueFrame(ctx, options) {
  /*
   * Lay out a chart with a category axis and a value axis (bar, lollipop,
   * dot plot): margins sized from the measured tick and category labels,
   * category labels truncated with an ellipsis and thinned or rotated when
   * crowded, gridlines and labels drawn in an aria-hidden group.
   *
   * :param ctx: The renderer context.
   * :param options: {
   *     labels:      category labels in drawing order,
   *     domain:      [min, max] data value range (nice-rounded here),
   *     horizontal:  true when categories run down the y axis,
   *     percent:     true for a percentage value axis,
   *     fixedDomain: true to use the domain exactly (stack100),
   *     padding:     band padding (0..1),
   *     valueInset:  px kept free at both ends of the value range
   *   }
   * :returns: { plot, chrome, marks, cat, val, plotW, plotH, margin, format }
   *     where `plot` is the translated plot group, `chrome` the aria-hidden
   *     group for axes and `marks` the group for the data marks.
   */
  const labels = options.labels
  const horizontal = options.horizontal === true
  const inset = typeof options.valueInset === "number" ? options.valueInset : 0
  const count = Math.max(labels.length, 1)

  let domain = options.domain
  if (options.fixedDomain !== true) {
    domain = niceDomain(domain[0], domain[1], 5)
  }
  const roughTicks = niceTicks(domain[0], domain[1], 5)
  const format = tickFormatter(roughTicks, options.percent === true)
  let tickWidth = 0
  for (let t = 0; t < roughTicks.length; t = t + 1) {
    tickWidth = Math.max(tickWidth, textWidth(format(roughTicks[t])))
  }

  let labelWidth = 0
  for (let index = 0; index < labels.length; index = index + 1) {
    labelWidth = Math.max(labelWidth, textWidth(labels[index]))
  }

  const margin = { top: 12, right: 16, bottom: 28, left: 28 }
  let labelMax = Infinity
  let every = 1
  let rotated = false

  if (horizontal === true) {
    margin.left = Math.ceil(Math.min(labelWidth, ctx.width * 0.4) + 16)
    margin.left = Math.max(margin.left, 28)
    margin.right = Math.round(Math.max(16, tickWidth / 2 + 6))
    labelMax = margin.left - 13
    const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)
    every = Math.max(1, Math.ceil((LABEL_FONT_SIZE + 3) / (plotH / count)))
  } else {
    margin.left = Math.round(Math.max(28, tickWidth + 14))
    let plotW = Math.max(ctx.width - margin.left - margin.right, 10)
    let step = plotW / count
    if (labelWidth + 6 <= step) {
      labelMax = step - 4
    } else if (labelWidth + 6 <= step * 3) {
      every = Math.ceil((labelWidth + 6) / step)
      labelMax = step * every - 6
    } else {
      rotated = true
      const radians = LABEL_ROTATION * Math.PI / 180
      labelMax = Math.min(labelWidth, Math.max(56, ctx.height * 0.3), 150)
      margin.bottom = Math.round(labelMax * Math.sin(radians) + LABEL_FONT_SIZE + 12)
      /* The first rotated label reaches left of its band. */
      const reach = labelMax * Math.cos(radians) - step / 2 + 4
      margin.left = Math.round(Math.max(margin.left, reach))
      plotW = Math.max(ctx.width - margin.left - margin.right, 10)
      step = plotW / count
      every = Math.max(1, Math.ceil((LABEL_FONT_SIZE + 3) / Math.sin(radians) / step))
    }
  }

  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)
  const padding = typeof options.padding === "number" ? options.padding : 0.2

  const cat = bandScale(labels, horizontal === true ? [0, plotH] : [0, plotW], padding)
  const val = horizontal === true
    ? linearScale(domain, [inset, plotW - inset])
    : linearScale(domain, [plotH - inset, inset])

  const plot = svgEl("g", { transform: `translate(${margin.left},${margin.top})` }, [])
  const chrome = svgEl("g", { "aria-hidden": "true", part: "axes" }, [])
  const marks = svgEl("g", { part: "marks" }, [])
  plot.appendChild(chrome)
  plot.appendChild(marks)

  /* Value gridlines + tick labels. */
  const valueLength = horizontal === true ? plotW : plotH
  const ticks = valueTicks(domain, valueLength, horizontal === true ? tickWidth + 14 : LABEL_FONT_SIZE * 2.6)
  for (let t = 0; t < ticks.length; t = t + 1) {
    const tick = ticks[t]
    const position = val(tick)
    if (horizontal === true) {
      chrome.appendChild(svgEl("line", {
        x1: position, y1: 0, x2: position, y2: plotH,
        stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
      }, []))
      chrome.appendChild(svgEl("text", {
        x: position, y: plotH + 16, "text-anchor": "middle",
        "font-size": LABEL_FONT_SIZE, fill: "var(--mj-text-muted, #5f6673)"
      }, format(tick)))
    } else {
      chrome.appendChild(svgEl("line", {
        x1: 0, y1: position, x2: plotW, y2: position,
        stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
      }, []))
      chrome.appendChild(svgEl("text", {
        x: -8, y: position + 4, "text-anchor": "end",
        "font-size": LABEL_FONT_SIZE, fill: "var(--mj-text-muted, #5f6673)"
      }, format(tick)))
    }
  }

  /* Category labels, by position so duplicate labels stay apart. */
  for (let index = 0; index < labels.length; index = index + every) {
    const center = cat.centerAt(index)
    if (horizontal === true) {
      chrome.appendChild(labelText({
        x: -8, y: center + 4, "text-anchor": "end",
        "font-size": LABEL_FONT_SIZE, fill: "var(--mj-text, #14181f)"
      }, labels[index], labelMax))
    } else if (rotated === true) {
      chrome.appendChild(labelText({
        x: center, y: plotH + 14, "text-anchor": "end",
        transform: `rotate(-${LABEL_ROTATION} ${center.toFixed(2)} ${plotH + 14})`,
        "font-size": LABEL_FONT_SIZE, fill: "var(--mj-text, #14181f)"
      }, labels[index], labelMax))
    } else {
      chrome.appendChild(labelText({
        x: center, y: plotH + 18, "text-anchor": "middle",
        "font-size": LABEL_FONT_SIZE, fill: "var(--mj-text, #14181f)"
      }, labels[index], labelMax))
    }
  }

  const frame = {
    plot: plot, chrome: chrome, marks: marks, cat: cat, val: val,
    plotW: plotW, plotH: plotH, margin: margin, format: format
  }
  return frame
}


export function clipToPlot(frame, prefix) {
  /*
   * Clip a frame's mark group to its plot box so nothing draws past the
   * axes.
   *
   * :param frame: A frame from categoryValueFrame (or any { plot, marks,
   *     plotW, plotH }).
   * :param prefix: The clip id prefix.
   */
  const clipId = nextClipId(prefix)
  const clip = svgEl("clipPath", { id: clipId }, [
    svgEl("rect", { x: -1, y: -1, width: frame.plotW + 2, height: frame.plotH + 2 }, [])
  ])
  frame.plot.insertBefore(svgEl("defs", null, [clip]), frame.plot.firstChild)
  frame.marks.setAttribute("clip-path", `url(#${clipId})`)
  return
}


export function zeroLine(frame, horizontal) {
  /*
   * Draw the zero baseline of a category / value frame (when zero is in the
   * value domain).
   */
  const domain = frame.val.domain()
  const low = Math.min(domain[0], domain[1])
  const high = Math.max(domain[0], domain[1])
  if (low > 0 || high < 0) {
    return
  }
  const zero = frame.val(0)
  const attrs = horizontal === true
    ? { x1: zero, y1: 0, x2: zero, y2: frame.plotH }
    : { x1: 0, y1: zero, x2: frame.plotW, y2: zero }
  attrs.stroke = "var(--mj-border-strong, #c7ccd6)"
  attrs["stroke-width"] = 1.5
  frame.chrome.appendChild(svgEl("line", attrs, []))
  return
}


export function inlineLegend(entries, x, y, maxWidth) {
  /*
   * Build a wrapping row of colour swatches and labels.
   *
   * :param entries: [{ label, color }].
   * :param x: Left edge in px.
   * :param y: Top edge in px.
   * :param maxWidth: Width available before wrapping.
   * :returns: { group, height } -- the aria-hidden <g> and its height.
   */
  const group = svgEl("g", { "aria-hidden": "true", part: "legend" }, [])
  const rowHeight = 16
  let cursorX = 0
  let row = 0

  for (let index = 0; index < entries.length; index = index + 1) {
    const entry = entries[index]
    const text = truncateText(entry.label, Math.max(maxWidth - 18, 24))
    const width = 14 + textWidth(text) + 14
    if (cursorX > 0 && cursorX + width > maxWidth) {
      cursorX = 0
      row = row + 1
    }
    const top = y + row * rowHeight
    group.appendChild(svgEl("rect", {
      x: x + cursorX, y: top + 1, width: 10, height: 10, rx: 2, fill: entry.color
    }, []))
    group.appendChild(svgEl("text", {
      x: x + cursorX + 14, y: top + 10,
      "font-size": LABEL_FONT_SIZE, fill: "var(--mj-text, #14181f)"
    }, text))
    cursorX = cursorX + width
  }

  const height = entries.length > 0 ? (row + 1) * rowHeight : 0
  return { group: group, height: height }
}


export function nudgeLabels(items, minGap, low, high) {
  /*
   * Spread label centres so neighbours are at least `minGap` apart while
   * staying inside [low, high]: a downward pass, then an upward pass from
   * the bottom limit, then a final downward pass from the top limit.
   *
   * :param items: [{ y }] (modified in place).
   * :returns: The items sorted by y.
   */
  const sorted = items.slice().sort((a, b) => a.y - b.y)
  for (let index = 0; index < sorted.length; index = index + 1) {
    sorted[index].y = Math.min(Math.max(sorted[index].y, low), high)
    if (index > 0 && sorted[index].y - sorted[index - 1].y < minGap) {
      sorted[index].y = sorted[index - 1].y + minGap
    }
  }
  for (let index = sorted.length - 1; index >= 0; index = index - 1) {
    const limit = index === sorted.length - 1 ? high : sorted[index + 1].y - minGap
    if (sorted[index].y > limit) {
      sorted[index].y = limit
    }
  }
  for (let index = 0; index < sorted.length; index = index + 1) {
    const limit = index === 0 ? low : sorted[index - 1].y + minGap
    if (sorted[index].y < limit) {
      sorted[index].y = limit
    }
  }
  return sorted
}


export function activate(element, handler) {
  /*
   * Run a handler on click and on Enter / Space.
   */
  element.addEventListener("click", handler)
  element.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      handler()
    }
  })
  return
}


function _groupMode(value) {
  /*
   * Read the `group` attribute; unknown values fall back to "cluster".
   */
  const key = String(value === null || value === undefined ? "" : value).trim().toLowerCase()
  const mode = Object.prototype.hasOwnProperty.call(GROUP_MODES, key) === true ? GROUP_MODES[key] : "cluster"
  return mode
}


function _stackSegments(series, dataIndex, mode) {
  /*
   * The stacked segments of one category: positive values stack upward
   * from zero and negative values downward; in stack100 mode every value is
   * its signed share (percent) of the category's absolute total.
   *
   * :returns: An array (one entry per series) of { value, shown, from, to }
   *     or null for a missing value.
   */
  let total = 0
  for (let s = 0; s < series.length; s = s + 1) {
    const value = numericValue(series[s].values[dataIndex])
    total = total + (value !== null ? Math.abs(value) : 0)
  }

  const segments = []
  let positive = 0
  let negative = 0
  for (let s = 0; s < series.length; s = s + 1) {
    const value = numericValue(series[s].values[dataIndex])
    if (value === null) {
      segments.push(null)
      continue
    }
    let shown = value
    if (mode === "stack100") {
      shown = total > 0 ? (value / total) * 100 : 0
    }
    let from = 0
    if (shown >= 0) {
      from = positive
      positive = positive + shown
    } else {
      from = negative
      negative = negative + shown
    }
    segments.push({ value: value, shown: shown, from: from, to: from + shown })
  }
  return segments
}


export function render(ctx) {
  /*
   * Render a bar/column chart.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const model = ctx.model
  const horizontal = ctx.orientation === "horizontal"
  const group = _groupMode(ctx.attrs("group", "cluster"))
  const sortMode = ctx.attrs("sort", "none")

  const root = svgEl("g", { part: "plot" }, [])

  const order = categoryOrder(model, sortMode)
  const series = model.series
  if (order.length === 0 || series.length === 0) {
    return root
  }

  /* Segments per category, in drawing order. */
  const stacked = group === "stack" || group === "stack100"
  const columns = order.map((entry) => {
    if (stacked === true) {
      return _stackSegments(series, entry.index, group)
    }
    return series.map((item) => {
      const value = numericValue(item.values[entry.index])
      return value === null ? null : { value: value, shown: value, from: 0, to: value }
    })
  })

  /* The value domain always includes zero. */
  let valueMin = 0
  let valueMax = 0
  for (let c = 0; c < columns.length; c = c + 1) {
    for (let s = 0; s < columns[c].length; s = s + 1) {
      const segment = columns[c][s]
      if (segment === null) {
        continue
      }
      valueMin = Math.min(valueMin, segment.from, segment.to)
      valueMax = Math.max(valueMax, segment.from, segment.to)
    }
  }
  let fixedDomain = false
  if (group === "stack100") {
    valueMin = valueMin < 0 ? -100 : 0
    valueMax = valueMax > 0 || valueMin === 0 ? 100 : 0
    fixedDomain = true
  }
  if (valueMax === valueMin) {
    valueMax = valueMin + 1
  }

  const frame = categoryValueFrame(ctx, {
    labels: order.map((entry) => entry.label),
    domain: [valueMin, valueMax],
    horizontal: horizontal,
    percent: group === "stack100",
    fixedDomain: fixedDomain,
    padding: 0.2
  })
  root.appendChild(frame.plot)
  clipToPlot(frame, "mj-bar-clip")

  const val = frame.val
  const bandwidth = frame.cat.bandwidth()
  const subWidth = stacked === true ? bandwidth : bandwidth / series.length

  /* Draw the bars. */
  for (let c = 0; c < order.length; c = c + 1) {
    const category = order[c].label
    const bandStart = frame.cat.at(c)

    for (let s = 0; s < series.length; s = s + 1) {
      const segment = columns[c][s]
      if (segment === null) {
        continue
      }
      const color = ctx.colorFor(series[s].name)
      const offset = stacked === true ? bandStart : bandStart + s * subWidth
      const thickness = stacked === true ? bandwidth : Math.max(subWidth - 1, 1)
      const p1 = val(segment.from)
      const p2 = val(segment.to)

      let rect = null
      if (horizontal === true) {
        rect = svgEl("rect", {
          x: Math.min(p1, p2), y: offset,
          width: Math.abs(p2 - p1), height: thickness, rx: 2, fill: color
        }, [])
      } else {
        rect = svgEl("rect", {
          x: offset, y: Math.min(p1, p2),
          width: thickness, height: Math.abs(p2 - p1), rx: 2, fill: color
        }, [])
      }

      const valueText = formatNumber(segment.value)
      const share = group === "stack100"
        ? ` (${formatNumber(segment.shown, { maximumFractionDigits: 1 })}%)`
        : ""
      rect.setAttribute("part", "bar")
      rect.setAttribute("tabindex", "0")
      rect.setAttribute("role", "img")
      rect.setAttribute("aria-label", `${series[s].name}, ${category}: ${valueText}${share}`)
      rect.appendChild(svgEl("title", null, `${series[s].name} - ${category}: ${valueText}${share}`))

      const detail = { series: series[s].name, category: category, value: segment.value }
      activate(rect, () => {
        ctx.emit("mj-chart-bar-click", detail)
      })
      frame.marks.appendChild(rect)
    }
  }

  zeroLine(frame, horizontal)
  return root
}


registerRenderer("bar", render);
registerRenderer("column", render);
