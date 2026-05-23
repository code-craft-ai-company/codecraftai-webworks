/*
 * chartmodel.js
 *
 * Normalizes raw chart JSON into a consistent model the renderers and the
 * accessible data-table part both consume. The model is intentionally
 * permissive: it accepts the common envelope and the family-specific
 * shapes documented in chart-components-plan.md sec.3.4.
 */


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


function _normalizeSeries(rawSeries) {
  /*
   * Normalize a series list to [{ name, values, points, color }].
   */
  const series = []
  const list = _asArray(rawSeries)

  for (let index = 0; index < list.length; index = index + 1) {
    const entry = list[index]
    if (entry === null || entry === undefined) {
      continue
    }

    const name = entry.name !== undefined ? String(entry.name) : `Series ${index + 1}`
    const values = Array.isArray(entry.values) === true ? entry.values : []
    const points = Array.isArray(entry.points) === true ? entry.points : []
    const color = entry.color !== undefined ? entry.color : null

    /* Spread the original entry first so renderers can read any
     * additional family-specific fields (samples, groups, kinds, ...)
     * straight off the normalized series object. */
    series.push({
      ...entry,
      name: name,
      values: values,
      points: points,
      color: color,
      raw: entry
    })
  }
  return series
}


export function buildModel(rawData) {
  /*
   * Build the normalized chart model from raw JSON.
   *
   * :param rawData: The parsed chart data object.
   * :returns: A model object:
   *     {
   *       meta:       the raw meta block (or {}),
   *       categories: the category labels (or []),
   *       series:     normalized series list,
   *       raw:        the original data (renderers may read family-specific
   *                   fields such as nodes/links, root, candles, regions),
   *       isEmpty:    true when there is nothing to draw
   *     }
   */
  const data = rawData !== null && rawData !== undefined ? rawData : {}

  const meta = data.meta !== null && data.meta !== undefined ? data.meta : {}
  const categories = Array.isArray(data.categories) === true ? data.categories : []
  const series = _normalizeSeries(data.series)

  /*
   * The model is empty only when the data has no series AND no
   * family-specific payload. Renderers that use raw.tasks, raw.events,
   * raw.candles, raw.value (for gauges), raw.words, etc. are not empty
   * even though they have no `series` array. Treat any key beyond `meta`
   * as a non-empty signal.
   */
  const hasSeries = series.length > 0
  let hasFamily = false
  const allKeys = Object.keys(data)
  for (let index = 0; index < allKeys.length; index = index + 1) {
    const key = allKeys[index]
    if (key !== "meta" && key !== "series" && key !== "categories") {
      hasFamily = true
      break
    }
  }

  const model = {
    meta: meta,
    categories: categories,
    series: series,
    raw: data,
    isEmpty: hasSeries === false && hasFamily === false
  }
  return model
}


export function buildTableModel(model) {
  /*
   * Build a 2D table representation of the model for the accessible
   * data-table part: { columns: [...], rows: [[...], ...] }.
   *
   * :param model: A model from buildModel.
   * :returns: { columns, rows }.
   */
  const columns = []
  const rows = []

  if (model.categories.length > 0 && model.series.length > 0) {
    columns.push("Category")
    for (let index = 0; index < model.series.length; index = index + 1) {
      columns.push(model.series[index].name)
    }
    for (let row = 0; row < model.categories.length; row = row + 1) {
      const record = [model.categories[row]]
      for (let s = 0; s < model.series.length; s = s + 1) {
        const value = model.series[s].values[row]
        record.push(value === undefined ? "" : value)
      }
      rows.push(record)
    }
    return { columns: columns, rows: rows }
  }

  if (model.series.length > 0 && model.series[0].points.length > 0) {
    columns.push("Series", "X", "Y")
    for (let s = 0; s < model.series.length; s = s + 1) {
      const points = model.series[s].points
      for (let p = 0; p < points.length; p = p + 1) {
        rows.push([model.series[s].name, points[p].x, points[p].y])
      }
    }
    return { columns: columns, rows: rows }
  }

  /* Family-specific data: render a generic key/value table from raw. */
  columns.push("Field", "Value")
  const keys = Object.keys(model.raw)
  for (let index = 0; index < keys.length; index = index + 1) {
    const key = keys[index]
    if (key === "meta") {
      continue
    }
    const value = model.raw[key]
    const summary = Array.isArray(value) === true
      ? `${value.length} item(s)`
      : JSON.stringify(value)
    rows.push([key, summary])
  }
  return { columns: columns, rows: rows }
}
