/*
 * chartmodel.js
 *
 * Normalizes raw chart JSON into a consistent model the renderers and the
 * accessible data-table part both consume. The model is intentionally
 * permissive: it accepts the common envelope and the family-specific
 * shapes documented in chart-components-plan.md sec.3.4.
 *
 * The model never rewrites the data it is given: a null value stays null
 * (a gap), it does not become zero, and the raw object is not modified.
 */

import { formatNumber } from "./svgdraw.js";

/* The accessible table never holds more than this many data rows. */
export const TABLE_ROW_LIMIT = 500;

/* The generic table never has more than this many columns. */
const TABLE_COLUMN_LIMIT = 12;

/* A list of numbers inside a table cell is cut after this many entries. */
const CELL_LIST_LIMIT = 12;

/* Group name of the record built from top-level scalar fields. */
const SUMMARY_GROUP = "Summary";

/* Tree data is walked no deeper than this (a guard, not a design limit). */
const TREE_DEPTH_LIMIT = 64;

const SERIES_CORE_KEYS = ["name", "values", "points", "color"];


function _asArray(value) {
  /*
   * Coerce a value to an array.
   */
  if (Array.isArray(value) === true) {
    return value
  }
  if (value === null || value === undefined) {
    return []
  }
  return [value]
}


function _isPlainObject(value) {
  /*
   * True for a non-null object that is not an array or a Date.
   */
  const plain = value !== null && typeof value === "object" &&
    Array.isArray(value) === false && (value instanceof Date) === false
  return plain
}


function _normalizeSeries(rawSeries) {
  /*
   * Normalize a series list to [{ name, values, points, color, raw,
   * sourceIndex }]. `sourceIndex` is the entry's position in the data, which
   * stays the same when other series are hidden.
   */
  const series = []
  const list = _asArray(rawSeries)

  for (let index = 0; index < list.length; index = index + 1) {
    const entry = list[index]
    if (entry === null || entry === undefined) {
      continue
    }

    const name = entry.name !== undefined && entry.name !== null
      ? String(entry.name)
      : `Series ${index + 1}`
    const values = Array.isArray(entry.values) === true ? entry.values : []
    const points = Array.isArray(entry.points) === true ? entry.points : []
    const color = typeof entry.color === "string" && entry.color.trim().length > 0
      ? entry.color.trim()
      : null

    /* Spread the original entry first so renderers can read any
     * additional family-specific fields (samples, groups, kinds, ...)
     * straight off the normalized series object. */
    series.push({
      ...entry,
      name: name,
      values: values,
      points: points,
      color: color,
      raw: entry,
      sourceIndex: index
    })
  }
  return series
}


function _hasContent(value, depth) {
  /*
   * True when a nested value carries something a renderer could draw: a
   * number, a non-empty string, a non-empty array, or an object with at
   * least one such member.
   */
  if (value === null || value === undefined) {
    return false
  }
  if (typeof value === "number") {
    return Number.isNaN(value) === false
  }
  if (typeof value === "string") {
    return value.trim().length > 0
  }
  if (typeof value === "boolean") {
    return true
  }
  if (Array.isArray(value) === true) {
    return value.length > 0
  }
  if (typeof value === "object") {
    if (value instanceof Date) {
      return true
    }
    if (depth >= 4) {
      return true
    }
    const keys = Object.keys(value)
    for (let index = 0; index < keys.length; index = index + 1) {
      if (_hasContent(value[keys[index]], depth + 1) === true) {
        return true
      }
    }
  }
  return false
}


function _hasFamilyContent(value) {
  /*
   * True when a top-level, family-specific field holds data. A bare string
   * or boolean at the top level is an option or a status (`layout: "tree"`,
   * `status: "ok"`), not data; a number (a gauge's `value`), a non-empty
   * array and a non-empty object are.
   */
  if (typeof value === "string" || typeof value === "boolean") {
    return false
  }
  return _hasContent(value, 0)
}


function _seriesHasContent(entry) {
  /*
   * True when a normalized series has values, points, or any other
   * family-specific numeric / array / object field (samples, q1, ...).
   */
  if (entry.values.length > 0 || entry.points.length > 0) {
    return true
  }
  const source = entry.raw
  const keys = Object.keys(source)
  for (let index = 0; index < keys.length; index = index + 1) {
    const key = keys[index]
    if (SERIES_CORE_KEYS.indexOf(key) >= 0) {
      continue
    }
    if (_hasFamilyContent(source[key]) === true) {
      return true
    }
  }
  return false
}


export function buildModel(rawData, options) {
  /*
   * Build the normalized chart model from raw JSON.
   *
   * :param rawData: The parsed chart data object.
   * :param options: Optional { hiddenSeries: [name, ...] } -- series the
   *     user has switched off (see MjChart.hideSeries).
   * :returns: A model object:
   *     {
   *       meta:         the raw meta block (or {}),
   *       categories:   the category labels (`categories`, else `labels`,
   *                     else []),
   *       series:       normalized VISIBLE series list,
   *       allSeries:    every normalized series, hidden ones included,
   *       hiddenSeries: names of the hidden series that exist in the data,
   *       raw:          the original data (renderers may read family-specific
   *                     fields such as nodes/links, root, candles, regions);
   *                     when series are hidden it is a shallow copy whose
   *                     `series` holds the visible entries only,
   *       source:       the original data object, always unfiltered,
   *       isEmpty:      true when there is nothing to draw
   *     }
   */
  const data = rawData !== null && rawData !== undefined ? rawData : {}

  const meta = _isPlainObject(data.meta) === true ? data.meta : {}
  let categories = []
  if (Array.isArray(data.categories) === true) {
    categories = data.categories
  } else if (Array.isArray(data.labels) === true) {
    categories = data.labels
  }

  const allSeries = _normalizeSeries(data.series)

  const hiddenNames = options !== null && options !== undefined &&
    Array.isArray(options.hiddenSeries) === true ? options.hiddenSeries : []
  const series = []
  const hiddenSeries = []
  for (let index = 0; index < allSeries.length; index = index + 1) {
    const entry = allSeries[index]
    if (hiddenNames.indexOf(entry.name) >= 0) {
      if (hiddenSeries.indexOf(entry.name) < 0) {
        hiddenSeries.push(entry.name)
      }
    } else {
      series.push(entry)
    }
  }

  /* Renderers that read raw.series must not draw a hidden series either. */
  let raw = data
  if (hiddenSeries.length > 0) {
    raw = { ...data, series: series.map((entry) => entry.raw) }
  }

  /*
   * The model is empty when no series carries data AND no family-specific
   * field does. Renderers that use raw.tasks, raw.events, raw.candles,
   * raw.value (for gauges), raw.words, etc. are not empty even though they
   * have no `series` array; an empty array or object is not data. Hidden
   * series still count: a chart whose every series is switched off is not
   * "no data".
   */
  let hasSeries = false
  for (let index = 0; index < allSeries.length; index = index + 1) {
    if (_seriesHasContent(allSeries[index]) === true) {
      hasSeries = true
      break
    }
  }

  let hasFamily = false
  const allKeys = Object.keys(data)
  for (let index = 0; index < allKeys.length; index = index + 1) {
    const key = allKeys[index]
    if (key === "meta" || key === "series" || key === "categories" || key === "labels") {
      continue
    }
    if (_hasFamilyContent(data[key]) === true) {
      hasFamily = true
      break
    }
  }

  const model = {
    meta: meta,
    categories: categories,
    series: series,
    allSeries: allSeries,
    hiddenSeries: hiddenSeries,
    raw: raw,
    source: data,
    isEmpty: hasSeries === false && hasFamily === false
  }
  return model
}


/* ----- accessible table model ----- */

function _cellValue(value) {
  /*
   * Reduce any value to something a table cell can show: a number stays a
   * number (so it can be formatted for the locale), everything else
   * becomes text. Never throws and never follows object references, so
   * circular data is safe.
   */
  if (value === null || value === undefined) {
    return ""
  }
  if (typeof value === "number") {
    return Number.isNaN(value) === true ? "" : value
  }
  if (typeof value === "string") {
    return value
  }
  if (typeof value === "boolean") {
    return value === true ? "true" : "false"
  }
  if (value instanceof Date) {
    return Number.isNaN(value.getTime()) === true ? "" : value.toISOString()
  }
  if (Array.isArray(value) === true) {
    const shown = []
    let scalars = true
    for (let index = 0; index < value.length && index < CELL_LIST_LIMIT; index = index + 1) {
      const item = value[index]
      if (item !== null && typeof item === "object") {
        scalars = false
        break
      }
      shown.push(item === null || item === undefined ? "" : String(item))
    }
    if (scalars === false) {
      return `${value.length} items`
    }
    const more = value.length > CELL_LIST_LIMIT ? ", …" : ""
    return shown.join(", ") + more
  }
  return ""
}


function _headerText(key) {
  /*
   * Turn a data key into a column header: "source" -> "Source".
   */
  const text = String(key)
  const header = text.length > 0 ? text.charAt(0).toUpperCase() + text.slice(1) : text
  return header
}


function _recordFields(source, skipKeys) {
  /*
   * The table fields of one data record: its scalar members, lists of
   * scalars, and the scalar members of directly nested objects (as
   * "outer.inner"). Object references are not followed further.
   *
   * :returns: An array of [key, cellValue] pairs.
   */
  const fields = []
  const keys = Object.keys(source)

  for (let index = 0; index < keys.length; index = index + 1) {
    const key = keys[index]
    /* "_name" members are private bookkeeping, not data. */
    if (skipKeys.indexOf(key) >= 0 || key.startsWith("_") === true) {
      continue
    }
    const value = source[key]
    if (value === null || value === undefined || typeof value === "function") {
      continue
    }

    if (_isPlainObject(value) === true) {
      const innerKeys = Object.keys(value)
      for (let inner = 0; inner < innerKeys.length; inner = inner + 1) {
        const innerValue = value[innerKeys[inner]]
        if (innerValue !== null && innerValue !== undefined && typeof innerValue !== "object" &&
            typeof innerValue !== "function") {
          fields.push([`${key}.${innerKeys[inner]}`, _cellValue(innerValue)])
        }
      }
    } else {
      fields.push([key, _cellValue(value)])
    }
  }
  return fields
}


function _nodeLabel(node) {
  /*
   * The text that identifies a tree node to its children's rows.
   */
  const candidates = [node.name, node.label, node.id, node.title]
  for (let index = 0; index < candidates.length; index = index + 1) {
    const candidate = candidates[index]
    if (candidate !== null && candidate !== undefined && typeof candidate !== "object") {
      return String(candidate)
    }
  }
  return ""
}


function _collectTree(node, group, parentLabel, depth, seen, records) {
  /*
   * Append one record per node of a `children` tree, depth first. `seen`
   * holds the nodes already visited so a tree that a renderer has given
   * parent back-references (or any other cycle) is walked once.
   */
  if (_isPlainObject(node) === false || seen.has(node) === true || depth > TREE_DEPTH_LIMIT) {
    return
  }
  if (records.length > TABLE_ROW_LIMIT) {
    return
  }
  seen.add(node)

  const fields = _recordFields(node, ["children", "parent"])
  if (parentLabel !== null) {
    fields.push(["parent", parentLabel])
  }
  records.push({ group: group, fields: fields })

  const children = Array.isArray(node.children) === true ? node.children : []
  const label = _nodeLabel(node)
  for (let index = 0; index < children.length; index = index + 1) {
    _collectTree(children[index], group, label, depth + 1, seen, records)
  }
  return
}


function _collectRecords(data) {
  /*
   * Flatten family-specific raw data into table records.
   *
   * Top-level scalars (a gauge's value / min / max) form one record; every
   * array of objects contributes a record per element (`nodes`, `links`,
   * `candles`, `tasks`); a tree (`root` with `children`) a record per node;
   * an array of scalars or of arrays a record per entry.
   *
   * :returns: An array of { group, fields: [[key, cell], ...] } records.
   */
  const records = []
  const seen = new WeakSet()
  const scalars = []
  const keys = Object.keys(data)

  for (let index = 0; index < keys.length; index = index + 1) {
    const key = keys[index]
    const value = data[key]
    if (key === "meta" || value === null || value === undefined || typeof value === "function") {
      continue
    }
    if (records.length > TABLE_ROW_LIMIT) {
      break
    }

    if (Array.isArray(value) === true) {
      for (let item = 0; item < value.length && records.length <= TABLE_ROW_LIMIT; item = item + 1) {
        const element = value[item]
        if (_isPlainObject(element) === true) {
          if (Array.isArray(element.children) === true) {
            _collectTree(element, key, null, 0, seen, records)
          } else {
            records.push({ group: key, fields: _recordFields(element, ["parent"]) })
          }
        } else if (Array.isArray(element) === true) {
          records.push({ group: key, fields: [["row", item + 1], ["values", _cellValue(element)]] })
        } else if (element !== null && element !== undefined) {
          records.push({ group: key, fields: [["index", item + 1], ["value", _cellValue(element)]] })
        }
      }
    } else if (_isPlainObject(value) === true) {
      if (Array.isArray(value.children) === true) {
        _collectTree(value, key, null, 0, seen, records)
      } else {
        const fields = _recordFields(value, ["parent"])
        if (fields.length > 0) {
          records.push({ group: key, fields: fields })
        }
        /* Arrays of records one level down (kpi.items, gauge.bands, ...). */
        const innerKeys = Object.keys(value)
        for (let inner = 0; inner < innerKeys.length; inner = inner + 1) {
          const innerValue = value[innerKeys[inner]]
          if (Array.isArray(innerValue) === false) {
            continue
          }
          for (let item = 0; item < innerValue.length && records.length <= TABLE_ROW_LIMIT; item = item + 1) {
            if (_isPlainObject(innerValue[item]) === true) {
              records.push({
                group: `${key}.${innerKeys[inner]}`,
                fields: _recordFields(innerValue[item], ["parent", "children"])
              })
            }
          }
        }
      }
    } else {
      scalars.push([key, _cellValue(value)])
    }
  }

  if (scalars.length > 0) {
    records.unshift({ group: "", fields: scalars })
  }
  return records
}


function _recordsToTable(records) {
  /*
   * Lay records out as a table: one row per record, one column per field
   * key in first-seen order, and a leading "Group" column when the records
   * come from more than one collection.
   */
  const groups = []
  const fieldKeys = []

  for (let index = 0; index < records.length; index = index + 1) {
    const record = records[index]
    if (groups.indexOf(record.group) < 0) {
      groups.push(record.group)
    }
    for (let f = 0; f < record.fields.length; f = f + 1) {
      const key = record.fields[f][0]
      if (fieldKeys.indexOf(key) < 0 && fieldKeys.length < TABLE_COLUMN_LIMIT) {
        fieldKeys.push(key)
      }
    }
  }

  const grouped = groups.length > 1
  const columns = []
  if (grouped === true) {
    columns.push("Group")
  }
  for (let index = 0; index < fieldKeys.length; index = index + 1) {
    columns.push(_headerText(fieldKeys[index]))
  }

  const rows = []
  for (let index = 0; index < records.length; index = index + 1) {
    const record = records[index]
    const row = []
    if (grouped === true) {
      row.push(record.group.length > 0 ? record.group : SUMMARY_GROUP)
    }
    for (let k = 0; k < fieldKeys.length; k = k + 1) {
      let cell = ""
      for (let f = 0; f < record.fields.length; f = f + 1) {
        if (record.fields[f][0] === fieldKeys[k]) {
          cell = record.fields[f][1]
          break
        }
      }
      row.push(cell)
    }
    rows.push(row)
  }
  return { columns: columns, rows: rows }
}


function _pointsTable(series) {
  /*
   * A table of XY points: one row per point, with a column for every
   * scalar member the points carry (x, y, size, label, ...).
   */
  const records = []
  let total = 0
  for (let s = 0; s < series.length; s = s + 1) {
    const points = series[s].points
    total = total + points.length
    for (let p = 0; p < points.length && records.length < TABLE_ROW_LIMIT; p = p + 1) {
      const point = points[p]
      let fields = []
      if (Array.isArray(point) === true) {
        const axes = ["x", "y", "z"]
        for (let a = 0; a < point.length && a < axes.length; a = a + 1) {
          fields.push([axes[a], _cellValue(point[a])])
        }
      } else if (_isPlainObject(point) === true) {
        fields = _recordFields(point, ["parent"])
      } else {
        continue
      }
      fields.unshift(["series", series[s].name])
      records.push({ group: "", fields: fields })
    }
  }
  const table = _recordsToTable(records)
  table.totalRows = Math.max(total, table.rows.length)
  return table
}


function _genericTable(model) {
  /*
   * The table for data no renderer described: categories x series, series
   * values by position, XY points, or the flattened family-specific data.
   */
  const series = model.series
  const columns = []
  const rows = []

  /*
   * Every series is hidden: there is nothing visible to describe. Falling
   * through would list the categories of the raw data as Index/Value rows.
   */
  const hiddenSeries = Array.isArray(model.hiddenSeries) === true ? model.hiddenSeries : []
  if (series.length === 0 && hiddenSeries.length > 0) {
    return { columns: [], rows: [], totalRows: 0 }
  }

  let withValues = 0
  let withPoints = 0
  let longest = 0
  for (let s = 0; s < series.length; s = s + 1) {
    if (series[s].values.length > 0) {
      withValues = withValues + 1
      longest = Math.max(longest, series[s].values.length)
    }
    if (series[s].points.length > 0) {
      withPoints = withPoints + 1
    }
  }

  if (withValues > 0) {
    /* Categories label the rows; without them the position does. */
    const labelled = model.categories.length > 0
    const count = labelled === true ? Math.max(model.categories.length, longest) : longest
    columns.push(labelled === true ? "Category" : "#")
    for (let s = 0; s < series.length; s = s + 1) {
      columns.push(series[s].name)
    }
    for (let row = 0; row < count && row < TABLE_ROW_LIMIT; row = row + 1) {
      const category = model.categories[row]
      const record = [labelled === true && category !== undefined ? _cellValue(category) : row + 1]
      for (let s = 0; s < series.length; s = s + 1) {
        record.push(_cellValue(series[s].values[row]))
      }
      rows.push(record)
    }
    return { columns: columns, rows: rows, totalRows: count }
  }

  if (withPoints > 0) {
    return _pointsTable(series)
  }

  /*
   * Family-specific data: one row per record of the visible raw data. The
   * collection stops just past the row limit, so the total is a lower bound.
   */
  const records = _collectRecords(model.raw)
  const table = _recordsToTable(records)
  table.totalRows = table.rows.length
  return table
}


export function normalizeTable(table) {
  /*
   * Validate a table a renderer supplied through ctx.setTable or its
   * registered table function.
   *
   * :param table: { columns: [text, ...], rows: [[cell, ...], ...],
   *     caption: optional text }. A row may also be an object keyed by the
   *     column names.
   * :returns: { columns, rows, caption } with every cell a number or text,
   *     or null when the value is not a usable table.
   */
  if (_isPlainObject(table) === false || Array.isArray(table.columns) === false ||
      Array.isArray(table.rows) === false) {
    return null
  }

  /*
   * Every column header has text: an empty header (a corner cell) is not
   * announced and fails WCAG, so it is named "Row" (first column) or
   * "Column N".
   */
  const columns = table.columns.map((column, index) => {
    const text = String(_cellValue(column))
    let name = text
    if (text.trim().length === 0) {
      name = index === 0 ? "Row" : `Column ${index + 1}`
    }
    return name
  })
  const rows = []
  for (let index = 0; index < table.rows.length; index = index + 1) {
    const source = table.rows[index]
    const row = []
    if (Array.isArray(source) === true) {
      for (let c = 0; c < source.length; c = c + 1) {
        row.push(_cellValue(source[c]))
      }
    } else if (_isPlainObject(source) === true) {
      for (let c = 0; c < table.columns.length; c = c + 1) {
        row.push(_cellValue(source[table.columns[c]]))
      }
    } else {
      continue
    }
    rows.push(row)
  }

  const caption = typeof table.caption === "string" && table.caption.trim().length > 0
    ? table.caption.trim()
    : null
  return { columns: columns, rows: rows, caption: caption }
}


export function buildTableModel(model, supplied) {
  /*
   * Build a 2D table representation of the chart for the accessible
   * data table.
   *
   * :param model: A model from buildModel (null gives an empty table).
   * :param supplied: Optional table published by the renderer for this
   *     chart type ({ columns, rows, caption }); it replaces the generic
   *     table when it is usable.
   * :returns: { columns, rows, caption, totalRows, truncated } -- cells are
   *     numbers or text, `rows` holds at most TABLE_ROW_LIMIT rows,
   *     `truncated` says rows were cut, `totalRows` is the count before the
   *     cut (a lower bound for flattened family data) and `caption` is the
   *     renderer's caption or null. This function does not throw: data it
   *     cannot tabulate gives an empty table.
   */
  let table = null

  try {
    if (supplied !== null && supplied !== undefined) {
      table = normalizeTable(supplied)
    }
    if (table === null && model !== null && model !== undefined) {
      const generic = _genericTable(model)
      table = {
        columns: generic.columns,
        rows: generic.rows,
        caption: null,
        totalRows: generic.totalRows
      }
    }
  } catch (error) {
    table = null
  }

  if (table === null) {
    table = { columns: [], rows: [], caption: null }
  }

  const rows = table.rows.length > TABLE_ROW_LIMIT
    ? table.rows.slice(0, TABLE_ROW_LIMIT)
    : table.rows
  const totalRows = typeof table.totalRows === "number"
    ? Math.max(table.totalRows, table.rows.length)
    : table.rows.length
  const result = {
    columns: table.columns,
    rows: rows,
    caption: table.caption,
    totalRows: totalRows,
    truncated: totalRows > rows.length
  }
  return result
}


export function tableSignature(table) {
  /*
   * A text fingerprint of a table model, used to skip rebuilding table DOM
   * that would come out identical.
   */
  let signature = ""
  try {
    signature = JSON.stringify([table.columns, table.rows, table.caption, table.totalRows])
  } catch (error) {
    signature = `unserializable:${Date.now()}`
  }
  return signature
}


export function buildTableElement(table, caption, truncatedNote) {
  /*
   * Build the <table> element for a table model. Every value is written
   * as text (never markup). Column headers are `th scope="col"`, the first
   * cell of each row is its `th scope="row"` header shown as written, and
   * the other numeric cells are formatted for the library locale.
   *
   * :param table: A table model from buildTableModel.
   * :param caption: The caption text.
   * :param truncatedNote: Text for a footer row shown when the model was
   *     cut at the row limit ("{count}" is replaced by the rows shown).
   * :returns: The HTMLTableElement.
   */
  const element = document.createElement("table")

  const captionEl = document.createElement("caption")
  captionEl.textContent = caption
  element.appendChild(captionEl)

  const head = document.createElement("thead")
  const headRow = document.createElement("tr")
  for (let c = 0; c < table.columns.length; c = c + 1) {
    const cell = document.createElement("th")
    cell.setAttribute("scope", "col")
    cell.textContent = table.columns[c]
    headRow.appendChild(cell)
  }
  head.appendChild(headRow)
  element.appendChild(head)

  const body = document.createElement("tbody")
  for (let r = 0; r < table.rows.length; r = r + 1) {
    const record = table.rows[r]
    const row = document.createElement("tr")
    for (let c = 0; c < record.length; c = c + 1) {
      const value = record[c]
      const text = String(value)
      /* An empty first cell cannot name its row: it stays a data cell. */
      const isRowHeader = c === 0 && text.trim().length > 0
      const cell = document.createElement(isRowHeader === true ? "th" : "td")
      if (isRowHeader === true) {
        cell.setAttribute("scope", "row")
        cell.textContent = text
      } else if (c === 0) {
        cell.textContent = text
      } else {
        cell.textContent = typeof value === "number" ? formatNumber(value) : String(value)
      }
      row.appendChild(cell)
    }
    body.appendChild(row)
  }
  element.appendChild(body)

  if (table.truncated === true && typeof truncatedNote === "string") {
    const foot = document.createElement("tfoot")
    const footRow = document.createElement("tr")
    const note = document.createElement("td")
    note.setAttribute("colspan", String(Math.max(table.columns.length, 1)))
    note.textContent = truncatedNote.split("{count}").join(String(table.rows.length))
    footRow.appendChild(note)
    foot.appendChild(footRow)
    element.appendChild(foot)
  }
  return element
}
