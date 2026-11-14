/*
 * jsonsource.js
 *
 * Data ingestion for the chart controller. Chart data may be supplied as:
 *   1. a `data` JavaScript property (an object) -- highest priority;
 *   2. a `src` attribute (a URL fetched as JSON);
 *   3. an inline <script type="application/json"> child element.
 *
 * The controller reads the three sources through `validateChartData`,
 * `ChartSourceCache` and `readInlineJson`. `resolveChartData` is the
 * one-call form: it returns a Promise for the parsed data object.
 */

/* A `src` request that has not answered after this long is abandoned. */
export const DEFAULT_FETCH_TIMEOUT_MS = 30000;

const INLINE_SELECTOR = 'script[type="application/json"]';


export function validateChartData(data) {
  /*
   * Check that resolved chart data is something a renderer can read.
   *
   * :param data: The value from the `data` property, a response body or
   *     the inline script.
   * :returns: The data, unchanged (null and undefined pass as "no data").
   * :raises: Error when the value is not an object -- a JSON string, a
   *     number or a boolean would otherwise draw a silent blank chart.
   */
  if (data === null || data === undefined) {
    return data
  }
  if (typeof data !== "object") {
    throw new Error(`Chart data must be an object, not a ${typeof data}.`)
  }
  return data
}


export function readInlineText(host) {
  /*
   * Read the text of an inline <script type="application/json"> child.
   *
   * :param host: The controller element.
   * :returns: The script text, or null when there is no script or it is
   *     blank.
   */
  const script = host.querySelector(INLINE_SELECTOR)
  if (script === null) {
    return null
  }

  const text = script.textContent
  if (text === null || text.trim().length === 0) {
    return null
  }
  return text
}


export function parseInlineJson(text) {
  /*
   * Parse inline chart JSON.
   *
   * :param text: The script text.
   * :returns: The parsed data.
   * :raises: Error naming the parser's complaint when the text is not
   *     valid JSON, so a typo reaches the chart's error state instead of
   *     reading as "no data".
   */
  let parsed = null
  try {
    parsed = JSON.parse(text)
  } catch (error) {
    throw new Error(`Inline chart data is not valid JSON: ${error.message}`)
  }
  return parsed
}


export function readInlineJson(host) {
  /*
   * Read JSON from an inline <script type="application/json"> child.
   *
   * :param host: The controller element.
   * :returns: The parsed object, or null when the script is absent or blank.
   * :raises: Error when the script holds malformed JSON.
   */
  const text = readInlineText(host)
  if (text === null) {
    return null
  }
  const parsed = parseInlineJson(text)
  return parsed
}


export async function fetchChartJson(url, options) {
  /*
   * Fetch and parse a JSON document.
   *
   * :param url: The URL to fetch.
   * :param options: Optional { signal, timeout }: an AbortSignal that
   *     cancels the request, and a time limit in milliseconds (default
   *     DEFAULT_FETCH_TIMEOUT_MS; 0 disables it).
   * :returns: The parsed object.
   * :raises: Error when the request fails, times out, is aborted, or the
   *     body is not JSON.
   */
  const given = options !== null && options !== undefined ? options : {}
  const timeout = typeof given.timeout === "number" ? given.timeout : DEFAULT_FETCH_TIMEOUT_MS

  /* One controller serves both the caller's abort and the time limit. */
  const controller = new AbortController()
  let timedOut = false
  let timer = null

  const onCallerAbort = () => {
    controller.abort()
  }
  if (given.signal !== null && given.signal !== undefined) {
    if (given.signal.aborted === true) {
      controller.abort()
    } else {
      given.signal.addEventListener("abort", onCallerAbort, { once: true })
    }
  }
  if (timeout > 0) {
    timer = setTimeout(() => {
      timedOut = true
      controller.abort()
    }, timeout)
  }

  let parsed = null
  try {
    const response = await fetch(url, {
      headers: { "Accept": "application/json" },
      signal: controller.signal
    })
    if (response.ok === false) {
      throw new Error(`Chart data request failed: ${response.status} ${url}`)
    }
    try {
      parsed = await response.json()
    } catch (error) {
      if (controller.signal.aborted === true) {
        throw error
      }
      throw new Error(`Chart data response is not valid JSON: ${url}`)
    }
  } catch (error) {
    if (timedOut === true) {
      throw new Error(`Chart data request timed out after ${timeout} ms: ${url}`)
    }
    throw error
  } finally {
    if (timer !== null) {
      clearTimeout(timer)
    }
    if (given.signal !== null && given.signal !== undefined) {
      given.signal.removeEventListener("abort", onCallerAbort)
    }
  }
  return parsed
}


/*
 * Remembers the outcome of the controller's current `src` so a re-render
 * (a resize frame, a type or orientation change, a legend toggle) does not
 * go back to the network. One URL is held at a time: asking for a
 * different URL aborts the request still in flight for the old one and
 * forgets its outcome. A failure is remembered as well, so a URL that
 * answered 404 is not requested again on every frame; `clear()` forgets
 * everything and the next `load` fetches afresh.
 */
export class ChartSourceCache {
  constructor() {
    this._url = null
    this._loaded = false
    this._payload = null
    this._error = null
    this._pending = null
    this._abort = null
  }

  /* True when the payload of `url` is already held. */
  has(url) {
    const held = this._loaded === true && this._url === url
    return held
  }

  /* The payload held for `url`, or null when it is not loaded. */
  get(url) {
    const payload = this.has(url) === true ? this._payload : null
    return payload
  }

  /* The error the last request for `url` ended with, or null. */
  failure(url) {
    const error = this._url === url ? this._error : null
    return error
  }

  /*
   * Load `url`, sharing one request between callers that ask while it is
   * in flight.
   *
   * :returns: A Promise for the parsed payload. It rejects when the
   *     request fails (also for a remembered failure) or is aborted
   *     because another URL was requested.
   */
  load(url) {
    if (this.has(url) === true) {
      return Promise.resolve(this._payload)
    }
    if (this.failure(url) !== null) {
      return Promise.reject(this._error)
    }
    if (this._pending !== null && this._url === url) {
      return this._pending
    }

    this.clear()
    const controller = new AbortController()
    this._url = url
    this._abort = controller

    const request = fetchChartJson(url, { signal: controller.signal }).then((payload) => {
      if (this._abort === controller) {
        this._loaded = true
        this._payload = payload
        this._pending = null
        this._abort = null
      }
      return payload
    }, (error) => {
      if (this._abort === controller) {
        this._error = error
        this._pending = null
        this._abort = null
      }
      throw error
    })

    this._pending = request
    return request
  }

  /* Abort any request in flight and forget the held outcome. */
  clear() {
    if (this._abort !== null) {
      const controller = this._abort
      this._abort = null
      controller.abort()
    }
    this._url = null
    this._loaded = false
    this._payload = null
    this._error = null
    this._pending = null
    return
  }

  /* Abort a request in flight but keep an outcome that already arrived. */
  abortPending() {
    if (this._abort !== null) {
      this.clear()
    }
    return
  }
}


/*
 * Top-level data fields that may hold a URL instead of the object itself
 * (a map's boundaries are usually a separate file). The controller fetches
 * them before the renderer runs.
 */
export const REFERENCE_FIELDS = ["geojson", "topology"];


function _referenceUrl(value) {
  /*
   * The URL held by a reference field, or null when the field already
   * holds data (an object) or text that is inline JSON.
   */
  if (typeof value !== "string") {
    return null
  }
  const text = value.trim()
  if (text.length === 0 || text.charAt(0) === "{" || text.charAt(0) === "[") {
    return null
  }
  return text
}


/*
 * Fetches the documents that reference fields point at, once per URL, and
 * hands back a copy of the chart data with the URLs replaced by the parsed
 * documents. The copy is reused while the data object and the documents
 * stay the same, so re-renders see a stable data identity.
 */
export class ChartReferenceCache {
  constructor() {
    /* url -> { payload, error, pending } */
    this._entries = new Map()
    this._lastInput = null
    this._lastOutput = null
  }

  /*
   * Resolve the reference fields of `data`.
   *
   * :param data: The chart data (any value).
   * :returns: { data, pending } -- `data` is ready to render when `pending`
   *     is null; otherwise `pending` is a Promise for it.
   * :raises: Error when a referenced document already failed to load.
   */
  resolve(data) {
    const result = { data: data, pending: null }
    if (data === null || data === undefined || typeof data !== "object" || Array.isArray(data) === true) {
      return result
    }

    const urls = []
    for (let index = 0; index < REFERENCE_FIELDS.length; index = index + 1) {
      const field = REFERENCE_FIELDS[index]
      const url = _referenceUrl(data[field])
      if (url !== null) {
        urls.push({ field: field, url: url })
      }
    }
    if (urls.length === 0) {
      return result
    }

    const waiting = []
    for (let index = 0; index < urls.length; index = index + 1) {
      const entry = this._entries.get(urls[index].url)
      if (entry !== undefined && entry.error !== null) {
        throw entry.error
      }
      if (entry === undefined || entry.pending !== null) {
        waiting.push(this._load(urls[index].url))
      }
    }

    if (waiting.length > 0) {
      result.data = null
      result.pending = Promise.all(waiting).then(() => {
        const settled = this.resolve(data)
        return settled.data
      })
      return result
    }

    if (this._lastInput === data && this._lastOutput !== null) {
      result.data = this._lastOutput
      return result
    }

    const resolved = { ...data }
    for (let index = 0; index < urls.length; index = index + 1) {
      resolved[urls[index].field] = this._entries.get(urls[index].url).payload
    }
    this._lastInput = data
    this._lastOutput = resolved
    result.data = resolved
    return result
  }

  _load(url) {
    const known = this._entries.get(url)
    if (known !== undefined && known.pending !== null) {
      return known.pending
    }

    const entry = { payload: null, error: null, pending: null }
    entry.pending = fetchChartJson(url).then((payload) => {
      entry.payload = payload
      entry.pending = null
      this._lastOutput = null
      return payload
    }, (error) => {
      entry.error = error
      entry.pending = null
      throw error
    })
    this._entries.set(url, entry)
    return entry.pending
  }

  /* Forget every document (reload). */
  clear() {
    this._entries = new Map()
    this._lastInput = null
    this._lastOutput = null
    return
  }
}


export async function resolveChartData(host, dataProperty) {
  /*
   * Resolve the chart data for a controller element from, in order: the
   * `data` property, the `src` attribute, then an inline JSON script.
   * Nothing is cached here; <mj-chart> itself goes through
   * ChartSourceCache so repeated renders reuse one response.
   *
   * :param host: The controller element.
   * :param dataProperty: The current value of the controller's `data`
   *     property (may be null).
   * :returns: A Promise for the parsed data object, or null when none.
   * :raises: Error when the request fails, the inline JSON is malformed, or
   *     the data is not an object (validateChartData): a JSON string,
   *     number or boolean is an error, never a silently empty chart.
   */
  let resolved = null
  if (dataProperty !== null && dataProperty !== undefined) {
    resolved = dataProperty
  } else {
    const src = host.getAttribute("src")
    if (src !== null && src.trim().length > 0) {
      resolved = await fetchChartJson(src.trim())
    } else {
      resolved = readInlineJson(host)
    }
  }
  const validated = validateChartData(resolved)
  return validated
}
