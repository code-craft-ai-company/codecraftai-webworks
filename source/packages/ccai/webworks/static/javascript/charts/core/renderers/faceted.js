/*
 * faceted.js
 *
 * Faceted (small-multiples) renderer — tiles one chart type across groups
 * in a pure-SVG grid; it does NOT spawn child <mj-chart> controllers.
 *
 * Registered types:
 *   "faceted"
 *
 * ctx.raw shape:
 *   raw.childType     chart type key of the panels (default "bar")
 *   raw.panels        [{label, series:[{name, values:[]}], ...}] -- every
 *                     field of a panel is passed to the panel's chart, so
 *                     raw-driven types (gauge, kpi, ...) work too
 *   raw.categories    category labels shared by every panel (a panel may
 *                     carry its own `categories`)
 *   raw.grid          {cols:N, rowGap:px, colGap:px}
 *   raw.sharedScales  bool (default true)
 *
 * Attributes:
 *   child-type        overrides raw.childType (`facet-type` is still read)
 *   mode              "free-scale" lets every panel scale itself (the same
 *                     as sharedScales: false)
 *
 * Shared scales: for childType "bar", "column", "line" and "area" the
 * panels are drawn here with ONE value scale for every panel, so bar heights
 * and line positions compare across panels; the value axis is drawn on the
 * first column and the category labels on the bottom row only. Any other
 * child type (and free-scale mode) is drawn by that type's own renderer per
 * panel through a derived context (deriveContext), with its own scale.
 *
 * Series keep one colour across all panels (by series name), and the
 * legend lists every series name used by any panel. The accessible table
 * has one row per panel and category with a column per series.
 *
 * Interaction: built-in panels emit `mj-chart-series-click` { panelIndex,
 * panel, series, category, value }; delegated panels emit their child
 * type's events with { panelIndex, panel } added to the detail.
 */

import { registerRenderer, getRenderer, deriveContext } from "../renderregistry.js";
import { buildModel } from "../chartmodel.js";
import { svgEl, linePath, areaPath, formatNumber } from "../svgdraw.js";
import { linearScale, niceDomain, niceTicks, ordinalColorScale, seriesColor } from "../scales.js";

const SHARED_TYPES = ["bar", "column", "line", "area"]
const TITLE_H = 16
const AXIS_W = 40
const CATEGORY_H = 16
const FONT = 10


function _numeric(value) {
  /*
   * A finite number, or null (a gap).
   */
  let numeric = null
  if (typeof value === "number" && Number.isFinite(value) === true) {
    numeric = value
  } else if (typeof value === "string" && value.trim().length > 0 &&
      Number.isFinite(Number(value)) === true) {
    numeric = Number(value)
  }
  return numeric
}


function _fitText(text, maxWidth) {
  /*
   * Shorten a label with an ellipsis to about maxWidth pixels.
   */
  const value = String(text)
  const capacity = Math.max(Math.floor(maxWidth / (FONT * 0.58)), 1)
  if (value.length <= capacity) {
    return value
  }
  return value.slice(0, Math.max(capacity - 1, 1)) + "…"
}


function _panelModels(panels, categories) {
  /*
   * Build each panel's raw data (shared categories merged in) and its
   * normalised model.
   *
   * :returns: [{ raw, model }] one per panel.
   */
  const built = []
  for (let p = 0; p < panels.length; p = p + 1) {
    const panel = panels[p] !== null && typeof panels[p] === "object" ? panels[p] : {}
    const raw = { ...panel }
    if (Array.isArray(panel.categories) === false && Array.isArray(panel.labels) === false) {
      raw.categories = categories.slice()
    }
    built.push({ raw: raw, model: buildModel(raw, null) })
  }
  return built
}


function _sharedExtent(models, includeZero) {
  /*
   * [min, max] over every value of every panel (nulls skipped).
   */
  let low = includeZero === true ? 0 : Infinity
  let high = includeZero === true ? 0 : -Infinity
  for (let p = 0; p < models.length; p = p + 1) {
    const series = models[p].model.series
    for (let s = 0; s < series.length; s = s + 1) {
      for (let v = 0; v < series[s].values.length; v = v + 1) {
        const value = _numeric(series[s].values[v])
        if (value === null) {
          continue
        }
        low = Math.min(low, value)
        high = Math.max(high, value)
      }
    }
  }
  if (low === Infinity) {
    return [0, 1]
  }
  if (low === high) {
    return [low - 1, high + 1]
  }
  return [low, high]
}


function _onActivate(element, handler) {
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


function _drawSharedPanel(ctx, options) {
  /*
   * Draw one built-in panel (bar / line / area) on the shared value scale.
   *
   * :param options: { group, kind, model, panel, panelIndex, width, height,
   *     domain, ticks, colorOf, showAxis, showCategories }.
   */
  const group = options.group
  const model = options.model
  const width = options.width
  const height = options.height
  const categories = model.categories
  const count = categories.length
  const valueScale = linearScale(options.domain, [height, 0])
  const panelLabel = options.panel.label !== undefined && options.panel.label !== null
    ? String(options.panel.label)
    : `Panel ${options.panelIndex + 1}`

  /* Gridlines (every panel) and tick labels (first column only). */
  const chrome = svgEl("g", { "aria-hidden": "true" }, [])
  group.appendChild(chrome)
  for (let t = 0; t < options.ticks.length; t = t + 1) {
    const y = valueScale(options.ticks[t])
    chrome.appendChild(svgEl("line", {
      x1: 0, y1: y, x2: width, y2: y,
      stroke: options.ticks[t] === 0 ? "var(--mj-border-strong, #878e9c)" : "var(--mj-border, #e0e3e9)",
      "stroke-width": 1
    }, []))
    if (options.showAxis === true) {
      chrome.appendChild(svgEl("text", {
        x: -6, y: y + 3, "text-anchor": "end", "font-size": FONT,
        fill: "var(--mj-text-muted, #5f6673)"
      }, formatNumber(options.ticks[t], { notation: "compact", maximumFractionDigits: 1 })))
    }
  }

  const band = count > 0 ? width / count : width
  const centerOf = (index) => (index + 0.5) * band

  if (options.showCategories === true && count > 0) {
    const every = Math.max(1, Math.ceil((FONT * 0.58 * 4) / band))
    for (let c = 0; c < count; c = c + every) {
      chrome.appendChild(svgEl("text", {
        x: centerOf(c), y: height + 12, "text-anchor": "middle", "font-size": FONT,
        fill: "var(--mj-text-muted, #5f6673)"
      }, _fitText(categories[c], band * every - 2)))
    }
  }

  const series = model.series
  const zeroY = valueScale(Math.max(Math.min(0, options.domain[1]), options.domain[0]))

  const emitFor = (seriesName, categoryIndex, value) => {
    ctx.emit("mj-chart-series-click", {
      panelIndex: options.panelIndex,
      panel: options.panel,
      series: seriesName,
      category: categories[categoryIndex],
      value: value
    })
  }

  if (options.kind === "bar" || options.kind === "column") {
    const inner = band * 0.75
    const sub = series.length > 0 ? inner / series.length : inner
    for (let s = 0; s < series.length; s = s + 1) {
      const entry = series[s]
      const color = options.colorOf(entry.name)
      for (let c = 0; c < count; c = c + 1) {
        const value = _numeric(entry.values[c])
        if (value === null) {
          continue
        }
        const y = valueScale(value)
        const label = `${panelLabel}, ${entry.name}, ${categories[c]}: ${formatNumber(value)}`
        const bar = svgEl("rect", {
          x: (c * band + (band - inner) / 2 + s * sub).toFixed(2),
          y: Math.min(y, zeroY).toFixed(2),
          width: Math.max(sub - 1, 1).toFixed(2),
          height: Math.max(Math.abs(zeroY - y), 0.5).toFixed(2),
          fill: color, rx: 1, tabindex: "0", role: "img", "aria-label": label, part: "bar"
        }, [svgEl("title", null, label)])
        const seriesName = entry.name
        const categoryIndex = c
        _onActivate(bar, () => emitFor(seriesName, categoryIndex, value))
        group.appendChild(bar)
      }
    }
    return
  }

  /* line / area */
  for (let s = 0; s < series.length; s = s + 1) {
    const entry = series[s]
    const color = options.colorOf(entry.name)
    const points = []
    for (let c = 0; c < count; c = c + 1) {
      const value = _numeric(entry.values[c])
      points.push(value === null ? null : { x: centerOf(c), y: valueScale(value) })
    }
    if (options.kind === "area") {
      group.appendChild(svgEl("path", {
        d: areaPath(points, zeroY), fill: color, "fill-opacity": 0.25, stroke: "none",
        "aria-hidden": "true"
      }, []))
    }
    group.appendChild(svgEl("path", {
      d: linePath(points), fill: "none", stroke: color, "stroke-width": 2,
      "stroke-linejoin": "round", "aria-hidden": "true", part: "line"
    }, []))
    for (let c = 0; c < count; c = c + 1) {
      if (points[c] === null) {
        continue
      }
      const value = _numeric(entry.values[c])
      const label = `${panelLabel}, ${entry.name}, ${categories[c]}: ${formatNumber(value)}`
      const dot = svgEl("circle", {
        cx: points[c].x.toFixed(2), cy: points[c].y.toFixed(2), r: 3, fill: color,
        tabindex: "0", role: "img", "aria-label": label, part: "point"
      }, [svgEl("title", null, label)])
      const seriesName = entry.name
      const categoryIndex = c
      _onActivate(dot, () => emitFor(seriesName, categoryIndex, value))
      group.appendChild(dot)
    }
  }
  return
}


export function render(ctx) {
  /*
   * Render a faceted / small-multiples chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const root = svgEl("g", { part: "plot" }, [])

  const panels = Array.isArray(raw.panels) === true ? raw.panels : []
  const categories = Array.isArray(raw.categories) === true ? raw.categories : []
  if (panels.length === 0) {
    return root
  }

  const childTypeName = String(ctx.attrs("child-type", null) || ctx.attrs("facet-type", null) ||
    raw.childType || "bar").trim()
  const childRenderer = childTypeName === "faceted" ? null : getRenderer(childTypeName)
  if (childRenderer === null) {
    root.appendChild(svgEl("text", {
      x: 8, y: 20, "font-size": 12, fill: "var(--mj-text-muted, #5f6673)"
    }, `Faceted chart: unknown panel type "${childTypeName}".`))
    return root
  }

  const freeScale = ctx.attrs("mode", null) === "free-scale" || raw.sharedScales === false
  const builtIn = freeScale === false && SHARED_TYPES.indexOf(childTypeName) >= 0

  const gridConfig = raw.grid !== null && typeof raw.grid === "object" ? raw.grid : {}
  const wantedCols = Number.isInteger(gridConfig.cols) === true && gridConfig.cols > 0
    ? gridConfig.cols
    : Math.ceil(Math.sqrt(panels.length))
  /* Narrow surfaces drop columns so a panel stays at least ~140px wide. */
  const gridCols = Math.max(1, Math.min(wantedCols, panels.length, Math.floor(ctx.width / 140) || 1))
  const gridRows = Math.ceil(panels.length / gridCols)
  const colGap = Number.isFinite(gridConfig.colGap) === true ? gridConfig.colGap : 16
  const rowGap = Number.isFinite(gridConfig.rowGap) === true ? gridConfig.rowGap : 16

  const axisW = builtIn === true ? AXIS_W : 0
  const categoryH = builtIn === true ? CATEGORY_H : 0
  const margin = { top: 4, right: 8, bottom: 4, left: 4 + axisW }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom - categoryH, 10)
  const panelW = Math.max(Math.floor((plotW - (gridCols - 1) * colGap) / gridCols), 20)
  const panelH = Math.max(Math.floor((plotH - (gridRows - 1) * (rowGap + categoryH)) / gridRows), 24)

  const models = _panelModels(panels, categories)

  /* One colour per series name across every panel. */
  const names = []
  models.forEach((entry) => {
    entry.model.allSeries.forEach((series) => {
      if (names.indexOf(series.name) < 0) {
        names.push(series.name)
      }
    })
  })
  const colorScale = ordinalColorScale(names)
  const explicit = new Map()
  models.forEach((entry) => {
    entry.model.allSeries.forEach((series) => {
      if (series.color !== null && explicit.has(series.name) === false) {
        explicit.set(series.name, series.color)
      }
    })
  })
  const colorOf = (name) => (explicit.has(name) === true ? explicit.get(name) : colorScale(name))

  let domain = null
  let ticks = []
  if (builtIn === true) {
    const extent = _sharedExtent(models, childTypeName !== "line")
    domain = niceDomain(extent[0], extent[1], 4)
    ticks = niceTicks(domain[0], domain[1], Math.max(2, Math.min(5, Math.floor(panelH / 28))))
  }

  const plot = svgEl("g", { transform: `translate(${margin.left},${margin.top})` }, [])
  root.appendChild(plot)

  for (let p = 0; p < panels.length; p = p + 1) {
    const panel = models[p].raw
    const col = p % gridCols
    const row = Math.floor(p / gridCols)
    const panelX = col * (panelW + colGap)
    const panelY = row * (panelH + rowGap + categoryH)
    const label = panel.label !== null && panel.label !== undefined ? String(panel.label) : ""

    plot.appendChild(svgEl("rect", {
      x: panelX, y: panelY, width: panelW, height: panelH,
      fill: "none", stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1, rx: 3,
      "aria-hidden": "true"
    }, []))
    if (label.length > 0) {
      plot.appendChild(svgEl("text", {
        x: panelX + panelW / 2, y: panelY + TITLE_H - 3, "text-anchor": "middle",
        "font-size": FONT + 1, "font-weight": "600", fill: "var(--mj-text, #14181f)"
      }, _fitText(label, panelW - 8)))
    }

    const innerW = panelW
    const innerH = Math.max(panelH - TITLE_H - 4, 10)
    const inner = svgEl("g", {
      transform: `translate(${panelX},${panelY + TITLE_H})`, part: "panel",
      "aria-label": label.length > 0 ? label : null
    }, [])
    plot.appendChild(inner)

    if (builtIn === true) {
      _drawSharedPanel(ctx, {
        group: inner,
        kind: childTypeName,
        model: models[p].model,
        panel: panel,
        panelIndex: p,
        width: innerW,
        height: innerH,
        domain: domain,
        ticks: ticks,
        colorOf: colorOf,
        showAxis: col === 0,
        showCategories: row === gridRows - 1 || p + gridCols >= panels.length
      })
      continue
    }

    /* Delegate to the child type's renderer with a complete derived context. */
    const childModel = models[p].model
    const panelIndex = p
    const childColor = (keyOrIndex) => {
      if (typeof keyOrIndex === "number" && Number.isInteger(keyOrIndex) === true && keyOrIndex >= 0) {
        if (keyOrIndex < childModel.series.length) {
          return colorOf(childModel.series[keyOrIndex].name)
        }
        return seriesColor(names.length + keyOrIndex)
      }
      return colorOf(String(keyOrIndex))
    }
    const childCtx = deriveContext(ctx, {
      type: childTypeName,
      model: childModel,
      raw: childModel.raw,
      width: innerW,
      height: innerH,
      label: label.length > 0 ? label : ctx.label,
      colorFor: childColor,
      emit: (eventName, detail) => {
        ctx.emit(eventName, Object.assign({ panelIndex: panelIndex, panel: panels[panelIndex] }, detail))
      }
    })
    const drawn = childRenderer(childCtx)
    if (drawn !== null && drawn !== undefined) {
      inner.appendChild(drawn)
    }
  }

  /* Legend: every series name used by any panel (colour only). */
  if (names.length > 0) {
    ctx.setLegend(names.map((name) => ({ label: name, color: colorOf(name) })))
  } else {
    ctx.setLegend([])
  }

  /* Table: one row per panel and category, one column per series. */
  const hasCategories = models.some((entry) => entry.model.categories.length > 0)
  if (names.length > 0 && hasCategories === true) {
    const rows = []
    models.forEach((entry, p) => {
      const label = entry.raw.label !== undefined && entry.raw.label !== null
        ? String(entry.raw.label)
        : `Panel ${p + 1}`
      entry.model.categories.forEach((category, c) => {
        const cells = [label, category]
        names.forEach((name) => {
          const series = entry.model.allSeries.find((item) => item.name === name)
          cells.push(series !== undefined ? _numeric(series.values[c]) : null)
        })
        rows.push(cells)
      })
    })
    ctx.setTable({ columns: ["Panel", "Category"].concat(names), rows: rows, caption: ctx.label })
  }

  return root
}


registerRenderer("faceted", render)
