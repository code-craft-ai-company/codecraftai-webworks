/*
 * collection.js
 *
 * Shared data + virtualization utilities for list/table/grid/picker
 * components.
 *
 *   - DataSource: a uniform async, paged, filterable data adapter interface.
 *     A plain array or a custom fetcher both satisfy it.
 *   - VirtualWindow: computes which fixed-height rows of a large collection
 *     fall inside a scroll viewport, so only those are rendered.
 */

/*
 * Wraps either a static array or an async fetcher behind one interface.
 *   fetcher(query) -> Promise<{ items, total }>
 *   query: { offset, limit, filter, sort }
 */
export class DataSource {
  constructor(source) {
    this._isArray = Array.isArray(source)
    this._array = this._isArray === true ? source : []
    this._fetcher = typeof source === "function" ? source : null
  }

  /* Fetch a page. Always returns a Promise for a consistent caller contract. */
  query(request) {
    const req = request || {}
    const offset = req.offset || 0
    const limit = req.limit === undefined ? 50 : req.limit

    if (this._fetcher !== null) {
      const promise = Promise.resolve(this._fetcher(req))
      return promise
    }

    let working = this._array

    if (req.filter !== null && req.filter !== undefined && req.filter !== "") {
      const needle = String(req.filter).toLowerCase()
      working = working.filter((item) => {
        const haystack = JSON.stringify(item).toLowerCase()
        const matched = haystack.indexOf(needle) >= 0
        return matched
      })
    }

    if (req.sort !== null && req.sort !== undefined) {
      const key = req.sort.key
      const direction = req.sort.direction === "desc" ? -1 : 1
      working = working.slice().sort((left, right) => {
        let order = 0
        if (left[key] < right[key]) {
          order = -1
        } else if (left[key] > right[key]) {
          order = 1
        }
        return order * direction
      })
    }

    const total = working.length
    const page = working.slice(offset, offset + limit)
    const result = Promise.resolve({ items: page, total: total })
    return result
  }

  get length() {
    const count = this._isArray === true ? this._array.length : -1
    return count
  }
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
   * Given the scroll offset and viewport height, return the inclusive range
   * of row indices to render plus the pixel offset of the first row.
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
