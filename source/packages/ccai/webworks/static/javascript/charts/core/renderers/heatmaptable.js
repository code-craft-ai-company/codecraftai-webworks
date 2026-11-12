/*
 * heatmaptable.js
 *
 * Heatmap-table, bar-in-cell, and conditional-format-table renderers.
 *
 * These types are tables first: each draws a real DOM <table> (thead / tbody,
 * th scope="col" / scope="row") inside an SVG <foreignObject>, so the text can
 * be selected and copied as a table and a screen reader reads rows and
 * columns. The visual encoding is added to the cells: an intensity fill
 * (heatmap-table), an in-cell SVG bar drawn from zero (bar-in-cell), or a
 * rules-based fill / text colour / icon (conditional-format-table). The table
 * scrolls inside the chart box when it has more rows or columns than fit, and
 * its header row stays visible while scrolling. The same rows are published
 * as the chart's accessible table (ctx.setTable).
 *
 * Registered types:
 *   "heatmap-table"            per-cell intensity fill (sequential/diverging)
 *   "bar-in-cell"              horizontal bar inside each `render: "bar"` cell
 *   "conditional-format-table" rules-based highlight fill + icon glyph
 *
 * ctx.raw shape (shared envelope):
 *   raw.columns    [{key, label, type?, render?, domain?, format?}]
 *                  `type` "number" marks a numeric column; without a type a
 *                  column whose values are all numbers is numeric.
 *                  `format` is a number format: a d3-style subset
 *                  (",.0f", ".1%", "$,.2f", ".3s", "d") or "compact",
 *                  "percent", or an Intl.NumberFormat options object.
 *   raw.rows       [{[key]: value, label?}]  `label` (when no column uses
 *                  that key) is shown as the row header.
 *   raw.domain     [min, max]  colour domain (heatmap-table) or the bar
 *                  domain (bar-in-cell); auto-computed when absent
 *   raw.scale      "table" (default) | "column"  heatmap-table: one colour
 *                  domain for the table, or one per numeric column
 *   raw.colorScale "sequential" | "diverging"  (heatmap-table); the
 *                  `variant` attribute "diverging" does the same
 *   raw.midpoint   diverging centre value (default 0)
 *   raw.rules      [{column?, op, value, style:{fill?, color?, icon?, weight?}}]
 *                  conditional-format-table; ops lt, lte, gt, gte, eq, neq,
 *                  contains; string values compare as text; a rule without
 *                  `column` applies to every cell; the first match wins.
 *
 * Shared helpers exported for the other grid renderers of this family
 * (calendar-heatmap, pixel, cohort, matrix): sequentialFill, divergingFill,
 * divergingPosition, labelColorFor, contrastTextColor, applyContrastText,
 * formatValue, EMPTY_CELL_FILL.
 *
 * Text on a coloured cell is black or white, picked by the browser from the
 * cell's resolved fill (WCAG relative luminance, through CSS relative colour
 * syntax), so every label reaches 4.5:1 in either theme and follows a live
 * theme switch. Browsers without relative colours keep the intensity-based
 * colour from labelColorFor().
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { seriesColor } from "../scales.js";

const XHTML_NS = "http://www.w3.org/1999/xhtml";


/* ── colour helpers (shared) ─────────────────────────────────────────────── */

/*
 * Fill of a cell that has no value. --mj-bg-muted differs from the page and
 * surface colour in both themes, so empty cells stay visible as a grid.
 */
export const EMPTY_CELL_FILL = "var(--mj-bg-muted, #eef0f3)"

/* The low end of every ramp mixes toward the surface the chart sits on. */
const RAMP_BASE = "var(--mj-surface, #ffffff)"

/* Share of the ramp colour at intensity 0 (so a zero differs from "empty"). */
const RAMP_FLOOR = 12

/* Intensity at and above which a label switches to the on-accent colour. */
const LABEL_SWITCH = 0.75


function _clampUnit(value) {
  /*
   * Clamp a number into [0, 1]; non-finite values become 0.
   */
  if (typeof value !== "number" || Number.isFinite(value) === false) {
    return 0
  }
  const clamped = Math.max(0, Math.min(1, value))
  return clamped
}


export function sequentialFill(t) {
  /*
   * Sequential fill for an intensity t in [0, 1] (clamped): the surface
   * colour tinted with the first series colour.
   *
   * :returns: A CSS colour string.
   */
  const share = RAMP_FLOOR + _clampUnit(t) * (100 - RAMP_FLOOR)
  const fill = `color-mix(in oklab, ${seriesColor(0)} ${share.toFixed(1)}%, ${RAMP_BASE})`
  return fill
}


export function divergingFill(position) {
  /*
   * Diverging fill for a signed position in [-1, 1] (clamped): negative
   * values tint toward the second series colour, positive ones toward the
   * first, 0 is the neutral surface colour.
   *
   * :returns: A CSS colour string.
   */
  let signed = typeof position === "number" && Number.isFinite(position) === true ? position : 0
  signed = Math.max(-1, Math.min(1, signed))
  const share = Math.abs(signed) * 100
  const hue = signed < 0 ? seriesColor(1) : seriesColor(0)
  const fill = `color-mix(in oklab, ${hue} ${share.toFixed(1)}%, ${RAMP_BASE})`
  return fill
}


export function divergingPosition(value, domain, midpoint) {
  /*
   * Map a value to a signed position in [-1, 1] around a midpoint; the two
   * halves are scaled separately so the midpoint is always neutral.
   *
   * :param value: The value.
   * :param domain: [min, max].
   * :param midpoint: The neutral value (usually 0).
   * :returns: The clamped position.
   */
  const low = Math.min(domain[0], domain[1])
  const high = Math.max(domain[0], domain[1])
  let position = 0
  if (value > midpoint) {
    const span = high - midpoint
    position = span > 0 ? (value - midpoint) / span : 1
  } else if (value < midpoint) {
    const span = midpoint - low
    position = span > 0 ? -(midpoint - value) / span : -1
  }
  position = Math.max(-1, Math.min(1, position))
  return position
}


export function labelColorFor(intensity) {
  /*
   * Text colour for a label drawn on a ramp fill of the given intensity
   * (0..1, or the absolute diverging position): the normal text colour on
   * light tints, the on-accent colour on strong ones.
   *
   * :returns: A CSS colour string.
   */
  const color = _clampUnit(Math.abs(intensity)) >= LABEL_SWITCH
    ? "var(--mj-text-on-accent, #ffffff)"
    : "var(--mj-text, #14181f)"
  return color
}


/*
 * Relative luminance (WCAG 2) at which black and white text have the same
 * contrast against the fill (about 4.58:1 each): darker fills take white
 * text, lighter fills black.
 */
const LUMINANCE_SWITCH = 0.1791


function _luminanceExpression() {
  /*
   * A CSS calc() expression of the WCAG relative luminance of the origin
   * colour of a relative rgb() colour (channels r, g, b in 0..255).
   */
  const linear = (channel) => `pow((${channel} / 255 + 0.055) / 1.055, 2.4)`
  const expression = `(0.2126 * ${linear("r")} + 0.7152 * ${linear("g")} + 0.0722 * ${linear("b")})`
  return expression
}


export function contrastTextColor(fill) {
  /*
   * The text colour for a label drawn on `fill`: black on light fills,
   * white on dark ones, computed by the browser from the resolved fill.
   *
   * :param fill: A CSS colour (hex, var(), color-mix(), ...).
   * :returns: A CSS colour string (relative colour syntax).
   */
  const level = `clamp(0, (${LUMINANCE_SWITCH} - ${_luminanceExpression()}) * 100000, 255)`
  const color = `rgb(from ${fill} ${level} ${level} ${level})`
  return color
}


export function applyContrastText(element, fill, intensity) {
  /*
   * Colour the text of an element (an HTML cell, or an SVG <text>) for its
   * background `fill`: the intensity-based colour first (kept by browsers
   * without relative colours), then the contrast colour from the fill.
   *
   * :param element: The element whose text is drawn on the fill.
   * :param fill: The background colour (CSS).
   * :param intensity: The ramp intensity (0..1 or a signed position) for
   *     the fallback colour.
   */
  const property = element.namespaceURI === "http://www.w3.org/2000/svg" ? "fill" : "color"
  element.style.setProperty(property, labelColorFor(intensity))
  element.style.setProperty(property, contrastTextColor(fill))
  return
}


/* ── number formats (shared) ─────────────────────────────────────────────── */

const FORMAT_PATTERN = /^(\$)?(,)?(?:\.(\d+))?(~)?([fdes%])?$/


export function formatValue(value, spec) {
  /*
   * Format a number with a column / metric format.
   *
   * :param value: The value; null and NaN give "", text is returned as is.
   * :param spec: Optional format: an Intl.NumberFormat options object; the
   *     keywords "compact", "percent", "integer"; or a d3-style string
   *     "[$][,][.precision][~][f|d|e|s|%]" (",.0f" grouped integer, ".1%"
   *     percent with one decimal, "$,.2f" currency, ".3s" compact with 3
   *     significant digits). Anything else uses the locale default.
   * :returns: The formatted text.
   */
  if (typeof value !== "number") {
    const text = formatNumber(value)
    return text
  }

  let options = null
  if (spec !== null && typeof spec === "object") {
    options = spec
  } else if (spec === "compact") {
    options = { notation: "compact", maximumFractionDigits: 1 }
  } else if (spec === "percent") {
    options = { style: "percent", maximumFractionDigits: 1 }
  } else if (spec === "integer") {
    options = { maximumFractionDigits: 0 }
  } else if (typeof spec === "string") {
    const match = FORMAT_PATTERN.exec(spec.trim())
    if (match !== null) {
      const currency = match[1] !== undefined
      const grouping = match[2] !== undefined
      const precision = match[3] !== undefined ? Number(match[3]) : null
      const kind = match[5] !== undefined ? match[5] : "f"
      options = { useGrouping: grouping }
      if (kind === "%") {
        options.style = "percent"
      } else if (kind === "s") {
        options.notation = "compact"
        options.useGrouping = true
      } else if (kind === "e") {
        options.notation = "scientific"
      }
      if (currency === true) {
        options.style = "currency"
        options.currency = "USD"
      }
      if (kind === "d") {
        options.maximumFractionDigits = 0
      } else if (precision !== null && kind === "s") {
        options.maximumSignificantDigits = Math.max(1, Math.min(precision, 21))
      } else if (precision !== null) {
        const digits = Math.min(precision, 20)
        options.minimumFractionDigits = digits
        options.maximumFractionDigits = digits
      }
    }
  }

  const text = options !== null ? formatNumber(value, options) : formatNumber(value)
  return text
}


/* ── table envelope ──────────────────────────────────────────────────────── */

function _isFiniteNumber(value) {
  /*
   * True for a finite number.
   */
  const finite = typeof value === "number" && Number.isFinite(value) === true
  return finite
}


function _readTable(raw) {
  /*
   * Normalise the shared envelope.
   *
   * :returns: { columns: [{key, label, numeric, render, domain, format,
   *     source}], rows: [object], rowHeader: true when a separate row
   *     header column (rows[].label) is shown first }.
   */
  const source = raw !== null && raw !== undefined ? raw : {}
  const rows = Array.isArray(source.rows) === true
    ? source.rows.filter((row) => row !== null && typeof row === "object")
    : []

  let given = Array.isArray(source.columns) === true
    ? source.columns.filter((column) => column !== null && typeof column === "object" &&
        column.key !== undefined && column.key !== null)
    : []

  /* Without column descriptors, the keys of the first row are the columns. */
  if (given.length === 0 && rows.length > 0) {
    given = Object.keys(rows[0]).filter((key) => key !== "label").map((key) => {
      return { key: key, label: key }
    })
  }

  const columns = given.map((column) => {
    const key = String(column.key)
    let numeric = column.type === "number"
    if (column.type === undefined || column.type === null) {
      let seen = 0
      let allNumbers = true
      for (let r = 0; r < rows.length; r = r + 1) {
        const value = rows[r][key]
        if (value === null || value === undefined || value === "") {
          continue
        }
        seen = seen + 1
        if (_isFiniteNumber(value) === false) {
          allNumbers = false
          break
        }
      }
      numeric = seen > 0 && allNumbers === true
    }
    const label = column.label !== undefined && column.label !== null ? String(column.label) : key
    return {
      key: key,
      label: label,
      numeric: numeric,
      render: column.render,
      domain: Array.isArray(column.domain) === true && column.domain.length === 2 &&
        _isFiniteNumber(column.domain[0]) === true && _isFiniteNumber(column.domain[1]) === true
        ? column.domain
        : null,
      format: column.format !== undefined ? column.format : null,
      source: column
    }
  })

  const usesLabelKey = columns.some((column) => column.key === "label")
  const rowHeader = usesLabelKey === false && rows.some((row) => row.label !== undefined &&
    row.label !== null)

  const table = { columns: columns, rows: rows, rowHeader: rowHeader }
  return table
}


function _extentOf(rows, keys) {
  /*
   * [min, max] of the finite numbers in the given columns, or null.
   */
  let min = Infinity
  let max = -Infinity
  for (let r = 0; r < rows.length; r = r + 1) {
    for (let k = 0; k < keys.length; k = k + 1) {
      const value = rows[r][keys[k]]
      if (_isFiniteNumber(value) === false) {
        continue
      }
      min = Math.min(min, value)
      max = Math.max(max, value)
    }
  }
  if (min === Infinity) {
    return null
  }
  return [min, max]
}


function _validDomain(value) {
  /*
   * A usable [min, max] pair from the data, or null.
   */
  const valid = Array.isArray(value) === true && value.length === 2 &&
    _isFiniteNumber(value[0]) === true && _isFiniteNumber(value[1]) === true
  return valid === true ? [Math.min(value[0], value[1]), Math.max(value[0], value[1])] : null
}


function _cellText(column, value) {
  /*
   * Display text of a cell value.
   */
  if (value === null || value === undefined) {
    return ""
  }
  if (_isFiniteNumber(value) === true) {
    const text = formatValue(value, column.format)
    return text
  }
  return String(value)
}


/* ── DOM helpers ─────────────────────────────────────────────────────────── */

const TABLE_STYLES = `
.mjvt-scroll {
  box-sizing: border-box; inline-size: 100%; block-size: 100%;
  overflow: auto; font-size: var(--mj-font-size-sm, 0.8125rem);
  color: var(--mj-text, #14181f);
}
.mjvt-table {
  border-collapse: separate; border-spacing: 0; inline-size: 100%;
  font-variant-numeric: tabular-nums;
}
.mjvt-table caption {
  caption-side: top; text-align: start; padding-block: 0 4px;
  color: var(--mj-text-muted, #5f6673); font-size: 0.75rem;
}
.mjvt-table th, .mjvt-table td {
  padding: 4px 8px; border-block-end: 1px solid var(--mj-border, #e0e3e9);
  text-align: start; white-space: nowrap; max-inline-size: 16em;
  overflow: hidden; text-overflow: ellipsis;
}
.mjvt-table thead th {
  position: sticky; inset-block-start: 0; z-index: 1;
  background: var(--mj-surface, #ffffff); font-weight: 600;
  border-block-end: 1px solid var(--mj-border-strong, #878e9c);
}
.mjvt-table tbody th { font-weight: 600; }
.mjvt-table .mjvt-num { text-align: end; }
.mjvt-table td[tabindex]:focus-visible {
  outline: var(--mj-focus-ring-width, 2px) solid var(--mj-focus-ring, #4d83f7);
  outline-offset: -2px;
}
.mjvt-bar { display: flex; align-items: center; gap: 6px; }
.mjvt-bar span { flex: 0 0 auto; min-inline-size: 3.5em; text-align: end; }
.mjvt-icon { display: inline-flex; align-items: center; gap: 4px; justify-content: flex-end;
  inline-size: 100%; }
.mjvt-legend {
  display: flex; align-items: center; gap: 6px; padding-block: 0 6px;
  font-size: 0.75rem; color: var(--mj-text-muted, #5f6673);
}
.mjvt-ramp { inline-size: 120px; block-size: 10px; border-radius: 2px;
  border: 1px solid var(--mj-border, #e0e3e9); }
`;


function _html(name, attrs, text) {
  /*
   * Build an HTML element for the foreignObject table. Text is set as a
   * text node, never parsed as markup.
   */
  const element = document.createElementNS(XHTML_NS, name)
  if (attrs !== null && attrs !== undefined) {
    const keys = Object.keys(attrs)
    for (let index = 0; index < keys.length; index = index + 1) {
      const value = attrs[keys[index]]
      if (value !== null && value !== undefined) {
        element.setAttribute(keys[index], String(value))
      }
    }
  }
  if (text !== null && text !== undefined) {
    element.textContent = String(text)
  }
  return element
}


function _tableShell(ctx, tableData, legendNode) {
  /*
   * Build the foreignObject, scroll container, <table> and header row.
   *
   * :returns: { root, table, tbody } -- root is the <g> the renderer returns.
   */
  const root = svgEl("g", { part: "plot" }, [])
  const foreign = svgEl("foreignObject", {
    x: 0, y: 0, width: ctx.width, height: ctx.height
  }, [])
  root.appendChild(foreign)

  const scroller = _html("div", { class: "mjvt-scroll", part: "table-scroll" }, null)
  const style = _html("style", null, TABLE_STYLES)
  scroller.appendChild(style)
  if (legendNode !== null) {
    scroller.appendChild(legendNode)
  }
  foreign.appendChild(scroller)

  const table = _html("table", { class: "mjvt-table", part: "table" }, null)
  scroller.appendChild(table)

  const thead = _html("thead", null, null)
  const headRow = _html("tr", null, null)
  if (tableData.rowHeader === true) {
    headRow.appendChild(_html("th", { scope: "col" }, ""))
  }
  for (let c = 0; c < tableData.columns.length; c = c + 1) {
    const column = tableData.columns[c]
    headRow.appendChild(_html("th", {
      scope: "col",
      class: column.numeric === true ? "mjvt-num" : null,
      title: column.label
    }, column.label))
  }
  thead.appendChild(headRow)
  table.appendChild(thead)

  const tbody = _html("tbody", null, null)
  table.appendChild(tbody)

  const shell = { root: root, table: table, tbody: tbody }
  return shell
}


function _rowHeaderText(tableData, row) {
  /*
   * The text that identifies a row: its label, else its first cell.
   */
  if (tableData.rowHeader === true) {
    return String(row.label)
  }
  if (tableData.columns.length > 0) {
    return _cellText(tableData.columns[0], row[tableData.columns[0].key])
  }
  return ""
}


function _appendCell(ctx, tableRow, tableData, rowIndex, columnIndex, row, cellNode) {
  /*
   * Append a data cell. The first column (when there is no separate row
   * header) is the row header <th scope="row">; other cells are <td>s that
   * are focusable marks emitting mj-chart-cell-click on click / Enter.
   */
  const column = tableData.columns[columnIndex]
  const value = row[column.key]
  const isHeader = tableData.rowHeader === false && columnIndex === 0

  const cell = isHeader === true
    ? _html("th", { scope: "row" }, null)
    : _html("td", { tabindex: "0", part: "cell" }, null)
  if (column.numeric === true) {
    cell.setAttribute("class", "mjvt-num")
  }
  cell.appendChild(cellNode)

  const text = _cellText(column, value)
  if (text.length > 0) {
    cell.setAttribute("title", `${_rowHeaderText(tableData, row)}, ${column.label}: ${text}`)
  }

  if (isHeader === false) {
    const handler = () => {
      ctx.emit("mj-chart-cell-click", { row: rowIndex, column: column.key, value: value })
    }
    cell.addEventListener("click", handler)
    cell.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        handler()
      }
    })
  }
  tableRow.appendChild(cell)
  return cell
}


function _publishTable(ctx, tableData) {
  /*
   * Publish the same rows as the chart's accessible table (raw numbers, so
   * the core formats them for the locale).
   */
  const columns = []
  if (tableData.rowHeader === true) {
    columns.push("Row")
  }
  for (let c = 0; c < tableData.columns.length; c = c + 1) {
    columns.push(tableData.columns[c].label)
  }
  const rows = tableData.rows.map((row) => {
    const cells = []
    if (tableData.rowHeader === true) {
      cells.push(String(row.label))
    }
    for (let c = 0; c < tableData.columns.length; c = c + 1) {
      const value = row[tableData.columns[c].key]
      cells.push(value === undefined ? null : value)
    }
    return cells
  })
  ctx.setTable({ columns: columns, rows: rows, caption: ctx.label })
  return
}


function _rampLegend(lowText, highText, lowFill, midFill, highFill) {
  /*
   * A small colour-ramp key: "low [gradient] high".
   */
  const legend = _html("div", { class: "mjvt-legend", part: "legend", "aria-hidden": "true" }, null)
  legend.appendChild(_html("span", null, lowText))
  const stops = midFill !== null ? `${lowFill}, ${midFill}, ${highFill}` : `${lowFill}, ${highFill}`
  legend.appendChild(_html("span", {
    class: "mjvt-ramp",
    style: `background: linear-gradient(to right, ${stops})`
  }, null))
  legend.appendChild(_html("span", null, highText))
  return legend
}


/* ── heatmap-table renderer ──────────────────────────────────────────────── */

export function renderHeatmapTable(ctx) {
  /*
   * Render a heatmap table: a DOM table whose numeric cells are filled by
   * value intensity (sequential, or diverging around `midpoint`).
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const tableData = _readTable(raw)
  if (tableData.columns.length === 0 || tableData.rows.length === 0) {
    return svgEl("g", { part: "plot" }, [])
  }

  const variant = ctx.attrs("style", null)
  const mode = variant === "diverging" || raw.colorScale === "diverging" ? "diverging" : "sequential"
  const midpoint = _isFiniteNumber(raw.midpoint) === true ? raw.midpoint : 0
  const perColumn = raw.scale === "column"

  const numericKeys = tableData.columns.filter((column) => column.numeric === true)
    .map((column) => column.key)
  const tableDomain = _validDomain(raw.domain) !== null
    ? _validDomain(raw.domain)
    : _extentOf(tableData.rows, numericKeys)

  const domainOf = (column) => {
    if (column.domain !== null) {
      return [Math.min(column.domain[0], column.domain[1]), Math.max(column.domain[0], column.domain[1])]
    }
    if (perColumn === true) {
      return _extentOf(tableData.rows, [column.key])
    }
    return tableDomain
  }

  let legend = null
  if (tableDomain !== null && perColumn === false) {
    legend = mode === "diverging"
      ? _rampLegend(formatNumber(tableDomain[0]), formatNumber(tableDomain[1]),
        divergingFill(-1), divergingFill(0), divergingFill(1))
      : _rampLegend(formatNumber(tableDomain[0]), formatNumber(tableDomain[1]),
        sequentialFill(0), null, sequentialFill(1))
  }

  const shell = _tableShell(ctx, tableData, legend)

  for (let r = 0; r < tableData.rows.length; r = r + 1) {
    const row = tableData.rows[r]
    const tableRow = _html("tr", null, null)
    if (tableData.rowHeader === true) {
      tableRow.appendChild(_html("th", { scope: "row", title: String(row.label) }, String(row.label)))
    }
    for (let c = 0; c < tableData.columns.length; c = c + 1) {
      const column = tableData.columns[c]
      const value = row[column.key]
      const text = _cellText(column, value)
      const cell = _appendCell(ctx, tableRow, tableData, r, c, row, document.createTextNode(text))

      const domain = column.numeric === true ? domainOf(column) : null
      if (domain !== null && _isFiniteNumber(value) === true && cell.localName === "td") {
        let fill = null
        let intensity = 0
        if (mode === "diverging") {
          intensity = divergingPosition(value, domain, midpoint)
          fill = divergingFill(intensity)
        } else {
          const span = domain[1] - domain[0]
          intensity = span > 0 ? (value - domain[0]) / span : 1
          fill = sequentialFill(intensity)
        }
        cell.style.setProperty("background", fill)
        applyContrastText(cell, fill, intensity)
      }
    }
    shell.tbody.appendChild(tableRow)
  }

  _publishTable(ctx, tableData)
  return shell.root
}


/* ── bar-in-cell renderer ────────────────────────────────────────────────── */

const BAR_TRACK_H = 12
const BAR_TRACK_W = 100


function _barSvg(value, domain) {
  /*
   * An in-cell SVG bar: a track and a bar drawn from zero (or from the
   * domain end nearest zero when zero is outside the domain).
   */
  const low = domain[0]
  const high = domain[1]
  const span = high - low
  const toX = (v) => {
    const fraction = span > 0 ? (v - low) / span : 1
    return Math.max(0, Math.min(1, fraction)) * BAR_TRACK_W
  }
  const zero = toX(Math.max(low, Math.min(high, 0)))
  const end = toX(value)

  const svg = svgEl("svg", {
    viewBox: `0 0 ${BAR_TRACK_W} ${BAR_TRACK_H}`,
    width: BAR_TRACK_W,
    height: BAR_TRACK_H,
    preserveAspectRatio: "none",
    "aria-hidden": "true",
    style: `position: static; display: block; flex: 1 1 auto; inline-size: 100%; ` +
      `min-inline-size: 40px; block-size: ${BAR_TRACK_H}px`
  }, [])
  svg.appendChild(svgEl("rect", {
    x: 0, y: 0, width: BAR_TRACK_W, height: BAR_TRACK_H, rx: 2,
    fill: "var(--mj-bg-muted, #eef0f3)"
  }, []))
  svg.appendChild(svgEl("rect", {
    x: Math.min(zero, end), y: 0,
    width: Math.abs(end - zero), height: BAR_TRACK_H, rx: 2,
    fill: value < 0 ? seriesColor(1) : seriesColor(0),
    part: "bar"
  }, []))
  if (zero > 0 && zero < BAR_TRACK_W) {
    svg.appendChild(svgEl("line", {
      x1: zero, y1: 0, x2: zero, y2: BAR_TRACK_H,
      stroke: "var(--mj-text-muted, #5f6673)", "stroke-width": 1,
      "vector-effect": "non-scaling-stroke"
    }, []))
  }
  return svg
}


export function renderBarInCell(ctx) {
  /*
   * Render a bar-in-cell table: columns with render "bar" show a bar from
   * zero plus the formatted value; other columns show their text.
   *
   * Bar domain per column: column.domain, else raw.domain, else the column's
   * [min(0, lo), max(0, hi)] so bar length is proportional to the value.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const tableData = _readTable(raw)
  if (tableData.columns.length === 0 || tableData.rows.length === 0) {
    return svgEl("g", { part: "plot" }, [])
  }

  const sharedDomain = _validDomain(raw.domain)
  const domains = new Map()
  for (let c = 0; c < tableData.columns.length; c = c + 1) {
    const column = tableData.columns[c]
    if (column.render !== "bar" || column.numeric === false) {
      continue
    }
    let domain = column.domain !== null
      ? [Math.min(column.domain[0], column.domain[1]), Math.max(column.domain[0], column.domain[1])]
      : sharedDomain
    if (domain === null) {
      const found = _extentOf(tableData.rows, [column.key])
      domain = found !== null ? [Math.min(0, found[0]), Math.max(0, found[1])] : [0, 1]
    }
    domains.set(column.key, domain)
  }

  const shell = _tableShell(ctx, tableData, null)

  for (let r = 0; r < tableData.rows.length; r = r + 1) {
    const row = tableData.rows[r]
    const tableRow = _html("tr", null, null)
    if (tableData.rowHeader === true) {
      tableRow.appendChild(_html("th", { scope: "row", title: String(row.label) }, String(row.label)))
    }
    for (let c = 0; c < tableData.columns.length; c = c + 1) {
      const column = tableData.columns[c]
      const value = row[column.key]
      const text = _cellText(column, value)
      const domain = domains.get(column.key)

      let content = document.createTextNode(text)
      const isHeader = tableData.rowHeader === false && c === 0
      if (domain !== undefined && _isFiniteNumber(value) === true && isHeader === false) {
        content = _html("div", { class: "mjvt-bar" }, null)
        content.appendChild(_barSvg(value, domain))
        content.appendChild(_html("span", null, text))
      }
      _appendCell(ctx, tableRow, tableData, r, c, row, content)
    }
    shell.tbody.appendChild(tableRow)
  }

  _publishTable(ctx, tableData)
  return shell.root
}


/* ── conditional-format-table renderer ───────────────────────────────────── */

function _evalRule(rule, value) {
  /*
   * Evaluate a single conditional-format rule against a value. Numbers
   * compare numerically; anything else compares as text (eq / neq /
   * contains, and lt / gt in text order).
   *
   * :returns: true when the rule matches.
   */
  if (value === null || value === undefined || rule === null || typeof rule !== "object") {
    return false
  }
  const op = rule.op
  const reference = rule.value
  let left = value
  let right = reference
  if (_isFiniteNumber(value) === false || _isFiniteNumber(reference) === false) {
    left = String(value)
    right = reference === null || reference === undefined ? "" : String(reference)
  }
  let matched = false
  if (op === "lt") {
    matched = left < right
  } else if (op === "lte") {
    matched = left <= right
  } else if (op === "gt") {
    matched = left > right
  } else if (op === "gte") {
    matched = left >= right
  } else if (op === "eq") {
    matched = left === right
  } else if (op === "neq") {
    matched = left !== right
  } else if (op === "contains") {
    matched = String(value).toLowerCase().indexOf(String(right).toLowerCase()) >= 0
  }
  return matched
}


const ICON_SIZE = 12


function _iconSvg(icon) {
  /*
   * A small inline SVG icon: "warning", "check", "info" or "cross".
   *
   * :returns: An <svg> element, or null for an unknown icon name.
   */
  const shapes = []
  const stroke = "currentColor"
  if (icon === "warning") {
    shapes.push(svgEl("path", {
      d: "M6,1 L11.5,11 L0.5,11 Z", fill: "none", stroke: stroke,
      "stroke-width": 1.2, "stroke-linejoin": "round"
    }, []))
    shapes.push(svgEl("path", { d: "M6,4.5 L6,7.5", stroke: stroke, "stroke-width": 1.4,
      "stroke-linecap": "round" }, []))
    shapes.push(svgEl("circle", { cx: 6, cy: 9.3, r: 0.8, fill: stroke }, []))
  } else if (icon === "check") {
    shapes.push(svgEl("path", {
      d: "M1.5,6.5 L4.5,9.5 L10.5,2.5", fill: "none", stroke: stroke,
      "stroke-width": 1.6, "stroke-linecap": "round", "stroke-linejoin": "round"
    }, []))
  } else if (icon === "cross") {
    shapes.push(svgEl("path", {
      d: "M2,2 L10,10 M10,2 L2,10", fill: "none", stroke: stroke,
      "stroke-width": 1.6, "stroke-linecap": "round"
    }, []))
  } else if (icon === "info") {
    shapes.push(svgEl("circle", { cx: 6, cy: 6, r: 5.2, fill: "none", stroke: stroke,
      "stroke-width": 1.1 }, []))
    shapes.push(svgEl("path", { d: "M6,5.4 L6,9", stroke: stroke, "stroke-width": 1.4,
      "stroke-linecap": "round" }, []))
    shapes.push(svgEl("circle", { cx: 6, cy: 3.5, r: 0.8, fill: stroke }, []))
  }
  if (shapes.length === 0) {
    return null
  }
  const svg = svgEl("svg", {
    viewBox: `0 0 ${ICON_SIZE} ${ICON_SIZE}`,
    width: ICON_SIZE, height: ICON_SIZE,
    "aria-hidden": "true",
    style: `position: static; display: inline-block; flex: 0 0 auto; ` +
      `inline-size: ${ICON_SIZE}px; block-size: ${ICON_SIZE}px`
  }, shapes)
  return svg
}


export function renderConditionalFormatTable(ctx) {
  /*
   * Render a conditional-format table with rules-based cell highlights.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const tableData = _readTable(raw)
  const rules = Array.isArray(raw.rules) === true
    ? raw.rules.filter((rule) => rule !== null && typeof rule === "object")
    : []
  if (tableData.columns.length === 0 || tableData.rows.length === 0) {
    return svgEl("g", { part: "plot" }, [])
  }

  const shell = _tableShell(ctx, tableData, null)

  for (let r = 0; r < tableData.rows.length; r = r + 1) {
    const row = tableData.rows[r]
    const tableRow = _html("tr", null, null)
    if (tableData.rowHeader === true) {
      tableRow.appendChild(_html("th", { scope: "row", title: String(row.label) }, String(row.label)))
    }
    for (let c = 0; c < tableData.columns.length; c = c + 1) {
      const column = tableData.columns[c]
      const value = row[column.key]
      const text = _cellText(column, value)

      /* First matching rule for this cell's column (or a table-wide rule). */
      let matched = null
      for (let index = 0; index < rules.length; index = index + 1) {
        const rule = rules[index]
        const appliesHere = rule.column === undefined || rule.column === null ||
          String(rule.column) === column.key
        if (appliesHere === true && _evalRule(rule, value) === true) {
          matched = rule
          break
        }
      }
      const style = matched !== null && matched.style !== null && typeof matched.style === "object"
        ? matched.style
        : null

      let content = document.createTextNode(text)
      const icon = style !== null && typeof style.icon === "string" ? _iconSvg(style.icon) : null
      if (icon !== null) {
        content = _html("span", { class: "mjvt-icon" }, null)
        content.appendChild(_html("span", null, text))
        content.appendChild(icon)
      }
      const cell = _appendCell(ctx, tableRow, tableData, r, c, row, content)

      if (style !== null) {
        if (typeof style.fill === "string" && style.fill.length > 0) {
          cell.style.setProperty("background", style.fill)
          /* A rule that sets only a fill gets readable text for it. */
          if (typeof style.color !== "string" || style.color.length === 0) {
            applyContrastText(cell, style.fill, 0)
          }
        }
        if (typeof style.color === "string" && style.color.length > 0) {
          cell.style.setProperty("color", style.color)
        }
        if (style.weight !== undefined && style.weight !== null) {
          cell.style.setProperty("font-weight", String(style.weight))
        }
        if (typeof style.icon === "string" && icon !== null) {
          const title = cell.getAttribute("title")
          cell.setAttribute("title", `${title !== null ? title : text} (${style.icon})`)
        }
      }
    }
    shell.tbody.appendChild(tableRow)
  }

  _publishTable(ctx, tableData)
  return shell.root
}


registerRenderer("heatmap-table", renderHeatmapTable, { legend: "none" })
registerRenderer("bar-in-cell", renderBarInCell, { legend: "none" })
registerRenderer("conditional-format-table", renderConditionalFormatTable, { legend: "none" })
