/*
 * collection.js
 *
 * Shared data + virtualization utilities for list/table/grid/picker
 * components.
 *
 *   - compareValues / isMissingValue / sortItems: type-aware, locale-aware ordering used by
 *     every client-side sort (numbers numerically, dates by time, text through
 *     `Intl.Collator`, missing values last).
 *   - itemMatchesText / itemMatchesFilters: text filtering over the VALUES of
 *     an item (never its property names).
 *   - DataSource: a uniform async, paged, filterable data adapter interface.
 *     A plain array, a fetcher function or an adapter object all satisfy it.
 *   - VirtualWindow: computes which fixed-height rows of a large collection
 *     fall inside a scroll viewport, so only those are rendered.
 */

import { getLocale } from "./intl.js";

/* True for Date objects, including Dates created in another frame. */
function isDate(value) {
  const result = Object.prototype.toString.call(value) === "[object Date]"
  return result
}

/* Text that is entirely a decimal number, e.g. "10", "-3.5", "1e3". */
const NUMERIC_TEXT_PATTERN = /^\s*[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?\s*$/;

let cachedCollator = null;
let cachedCollatorLocale = null;

/*
 * The collator used for text ordering: current locale, case-insensitive,
 * digit runs compared as numbers ("item 9" before "item 10").
 */
function textCollator() {
  const locale = getLocale()

  if (cachedCollator === null || cachedCollatorLocale !== locale) {
    try {
      cachedCollator = new Intl.Collator(locale, { numeric: true, sensitivity: "base" })
    } catch (error) {
      cachedCollator = new Intl.Collator(undefined, { numeric: true, sensitivity: "base" })
    }
    cachedCollatorLocale = locale
  }

  return cachedCollator
}

/* True for the values every sort places last: null, undefined, "" and NaN. */
export function isMissingValue(value) {
  let missing = false

  if (value === null || value === undefined) {
    missing = true
  } else if (typeof value === "string" && value.trim().length === 0) {
    missing = true
  } else if (typeof value === "number" && Number.isNaN(value) === true) {
    missing = true
  } else if (isDate(value) === true && Number.isNaN(value.getTime()) === true) {
    missing = true
  }

  return missing
}

/* The numeric reading of a value, or null when it is not a number. */
function toNumber(value) {
  let result = null

  if (typeof value === "number") {
    result = value
  } else if (typeof value === "bigint") {
    result = Number(value)
  } else if (typeof value === "boolean") {
    result = value === true ? 1 : 0
  } else if (typeof value === "string" && NUMERIC_TEXT_PATTERN.test(value) === true) {
    result = Number(value)
  }

  return result
}

/* The timestamp of a Date or a parsable date string, or null. */
function toTime(value) {
  let result = null

  if (isDate(value) === true) {
    result = value.getTime()
  } else if (typeof value === "string" || typeof value === "number") {
    const parsed = new Date(value).getTime()
    if (Number.isNaN(parsed) === false) {
      result = parsed
    }
  }

  return result
}

/* The text a value is filtered and collated by. */
function toText(value) {
  let text = ""

  if (value === null || value === undefined) {
    text = ""
  } else if (isDate(value) === true) {
    text = value.toISOString()
  } else if (typeof value === "object") {
    text = collectValueText(value, 0)
  } else {
    text = String(value)
  }

  return text
}

/*
 * Ascending comparison of two present (non-missing) values.
 *
 * `type` is an optional hint: "number", "date" or "text". Without a hint the
 * values decide: two numbers (or numeric strings) compare numerically, two
 * Dates by time, anything else as text through the locale collator. Mixed
 * pairs fall back to text, so the order stays consistent (a comparator that
 * returns 0 for unrelated types scatters them).
 */
function comparePresent(left, right, type) {
  let order = null

  if (type === "date" || (isDate(left) === true && isDate(right) === true)) {
    const leftTime = toTime(left)
    const rightTime = toTime(right)
    if (leftTime !== null && rightTime !== null) {
      order = leftTime - rightTime
    }
  }

  if (order === null && type !== "text" && type !== "date") {
    const leftNumber = toNumber(left)
    const rightNumber = toNumber(right)
    if (leftNumber !== null && rightNumber !== null) {
      order = leftNumber - rightNumber
    }
  }

  if (order === null) {
    order = textCollator().compare(toText(left), toText(right))
  }

  return order
}

/*
 * Compare two values for an ascending sort. Missing values (null, undefined,
 * empty text, NaN) sort after every present value.
 */
export function compareValues(left, right, type) {
  const leftMissing = isMissingValue(left)
  const rightMissing = isMissingValue(right)
  let order = 0

  if (leftMissing === true && rightMissing === true) {
    order = 0
  } else if (leftMissing === true) {
    order = 1
  } else if (rightMissing === true) {
    order = -1
  } else {
    order = comparePresent(left, right, type)
  }

  return order
}

/*
 * Return a sorted copy of `items`.
 *
 *   sort: { key, direction: "asc" | "desc", type?, compare? }
 *
 * `compare(leftValue, rightValue, leftItem, rightItem)` replaces the built-in
 * comparison when supplied. Missing values stay last in BOTH directions, and
 * the sort is stable: equal items keep their original order.
 */
export function sortItems(items, sort) {
  const sorted = items.slice()

  if (sort !== null && sort !== undefined && sort.key !== undefined && sort.key !== null) {
    const key = sort.key
    const descending = sort.direction === "desc"
    const custom = typeof sort.compare === "function" ? sort.compare : null

    sorted.sort((leftItem, rightItem) => {
      const left = leftItem !== null && leftItem !== undefined ? leftItem[key] : undefined
      const right = rightItem !== null && rightItem !== undefined ? rightItem[key] : undefined
      const leftMissing = isMissingValue(left)
      const rightMissing = isMissingValue(right)
      let order = 0

      if (leftMissing === true || rightMissing === true) {
        /* Missing values are not reversed by the direction. */
        order = compareValues(left, right, sort.type)
      } else {
        if (custom !== null) {
          order = custom(left, right, leftItem, rightItem)
        } else {
          order = comparePresent(left, right, sort.type)
        }
        if (descending === true) {
          order = -order
        }
      }

      return order
    })
  }

  return sorted
}

/*
 * Concatenate the values held by an object or array (not its property
 * names), recursing a few levels into nested data.
 */
function collectValueText(value, depth) {
  const parts = []

  if (value === null || value === undefined) {
    /* nothing to add */
  } else if (isDate(value) === true) {
    parts.push(value.toISOString())
  } else if (typeof value === "object") {
    if (depth < 4) {
      const children = Array.isArray(value) === true ? value : Object.values(value)
      for (let index = 0; index < children.length; index = index + 1) {
        parts.push(collectValueText(children[index], depth + 1))
      }
    }
  } else if (typeof value !== "function") {
    parts.push(String(value))
  }

  const text = parts.join("\n")
  return text
}

function normalizeNeedle(text) {
  const needle = String(text).trim().toLocaleLowerCase()
  return needle
}

/*
 * True when `needle` occurs (case-insensitively) in one of the item's values.
 * `keys` limits the search to those properties; without it every value is
 * searched. Property names never match.
 */
export function itemMatchesText(item, needle, keys) {
  const wanted = normalizeNeedle(needle)
  let matched = true

  if (wanted.length > 0) {
    let haystack = ""
    if (Array.isArray(keys) === true && item !== null && typeof item === "object") {
      const parts = []
      for (let index = 0; index < keys.length; index = index + 1) {
        parts.push(toText(item[keys[index]]))
      }
      haystack = parts.join("\n")
    } else {
      haystack = toText(item)
    }
    matched = haystack.toLocaleLowerCase().indexOf(wanted) >= 0
  }

  return matched
}

/*
 * True when the item satisfies every per-field filter in `filters`
 * ({ fieldKey: text }). Empty filter texts are ignored.
 */
export function itemMatchesFilters(item, filters) {
  let matched = true

  if (filters !== null && filters !== undefined && typeof filters === "object") {
    const keys = Object.keys(filters)
    for (let index = 0; index < keys.length; index = index + 1) {
      const key = keys[index]
      const text = filters[key]
      if (text === null || text === undefined) {
        continue
      }
      const wanted = normalizeNeedle(text)
      if (wanted.length === 0) {
        continue
      }
      const value = item !== null && item !== undefined ? item[key] : undefined
      if (toText(value).toLocaleLowerCase().indexOf(wanted) < 0) {
        matched = false
        break
      }
    }
  }

  return matched
}

/*
 * Wraps a static array, an async fetcher or an adapter object behind one
 * interface.
 *
 *   new DataSource(array)
 *   new DataSource((query) => Promise<{ items, total }>)
 *   new DataSource({ query(query) })           -- same contract as the function
 *   new DataSource({ fetch(query) })           -- may resolve { rows, total }
 *
 *   query: { offset, limit, filter, filters, sort }
 *     filter   text matched against all values of an item
 *     filters  { fieldKey: text } matched against that field only
 *     sort     { key, direction, type?, compare? }
 *
 * `query()` always resolves `{ items, total }`; `total` is null when the
 * source did not report one.
 */
export class DataSource {
  constructor(source) {
    this._isArray = Array.isArray(source)
    this._array = this._isArray === true ? source : []
    this._fetcher = null

    if (typeof source === "function") {
      this._fetcher = source
    } else if (source !== null && source !== undefined && this._isArray === false && typeof source === "object") {
      if (typeof source.query === "function") {
        this._fetcher = (request) => source.query(request)
      } else if (typeof source.fetch === "function") {
        this._fetcher = (request) => source.fetch(request)
      }
    }
  }

  /* True when the source can produce data at all. */
  get isUsable() {
    const usable = this._isArray === true || this._fetcher !== null
    return usable
  }

  /* Fetch a page. Always returns a Promise for a consistent caller contract. */
  query(request) {
    const req = request || {}
    const offset = req.offset || 0
    const limit = req.limit === undefined ? 50 : req.limit
    let result = null

    if (this._fetcher !== null) {
      let pending = null
      try {
        pending = Promise.resolve(this._fetcher(req))
      } catch (error) {
        pending = Promise.reject(error)
      }
      result = pending.then((page) => normalizePage(page))
    } else {
      let working = this._array

      let globalText = null
      let fieldFilters = req.filters
      if (req.filter !== null && req.filter !== undefined) {
        if (typeof req.filter === "object") {
          /* An object passed as `filter` is a per-field filter map. */
          fieldFilters = Object.assign({}, req.filter, fieldFilters || {})
        } else {
          globalText = String(req.filter)
        }
      }

      if (globalText !== null && globalText.trim().length > 0) {
        working = working.filter((item) => itemMatchesText(item, globalText, req.filterKeys))
      }

      if (fieldFilters !== null && fieldFilters !== undefined) {
        working = working.filter((item) => itemMatchesFilters(item, fieldFilters))
      }

      if (req.sort !== null && req.sort !== undefined) {
        working = sortItems(working, req.sort)
      }

      const total = working.length
      const page = working.slice(offset, offset + limit)
      result = Promise.resolve({ items: page, total: total })
    }

    return result
  }

  get length() {
    const count = this._isArray === true ? this._array.length : -1
    return count
  }
}

/* Bring whatever a fetcher resolved into the `{ items, total }` shape. */
function normalizePage(page) {
  let items = []
  let total = null

  if (Array.isArray(page) === true) {
    items = page
  } else if (page !== null && page !== undefined && typeof page === "object") {
    if (Array.isArray(page.items) === true) {
      items = page.items
    } else if (Array.isArray(page.rows) === true) {
      items = page.rows
    }
    if (typeof page.total === "number" && Number.isNaN(page.total) === false) {
      total = page.total
    }
  }

  const normalized = { items: items, total: total }
  return normalized
}

/*
 * Computes the visible window of fixed-height rows for a virtualized list.
 */
export class VirtualWindow {
  constructor(options) {
    const opts = options || {}
    this.rowHeight = opts.rowHeight || 36
    this.overscan = opts.overscan === undefined ? 4 : opts.overscan
    this.total = opts.total || 0
  }

  setTotal(total) {
    this.total = total
    return
  }

  /* Total scrollable height, used to size the scroll spacer. */
  scrollHeight() {
    const height = this.total * this.rowHeight
    return height
  }

  /*
   * Given the scroll offset and viewport height, return the half-open range
   * [start, end) of row indices to render plus the pixel offset of the first
   * row.
   */
  range(scrollTop, viewportHeight) {
    let start = Math.floor(scrollTop / this.rowHeight) - this.overscan
    if (start < 0) {
      start = 0
    }

    const visibleCount = Math.ceil(viewportHeight / this.rowHeight)
    let end = start + visibleCount + this.overscan * 2
    if (end > this.total) {
      end = this.total
    }

    const offsetY = start * this.rowHeight
    const window = { start: start, end: end, offsetY: offsetY }
    return window
  }
}
