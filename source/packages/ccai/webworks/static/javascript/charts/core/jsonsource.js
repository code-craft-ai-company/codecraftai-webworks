/*
 * jsonsource.js
 *
 * Data ingestion for the chart controller. Chart data may be supplied as:
 *   1. a `data` JavaScript property (an object) -- highest priority;
 *   2. a `src` attribute (a URL fetched as JSON);
 *   3. an inline <script type="application/json"> child element.
 *
 * resolveChartData returns a Promise for the parsed data object.
 */


function _readInlineJson(host) {
  /*
   * Read JSON from an inline <script type="application/json"> child.
   *
   * :param host: The controller element.
   * :returns: The parsed object, or null when absent/invalid.
   */
  const script = host.querySelector('script[type="application/json"]')
  if (script === null) {
    return null
  }

  const raw = script.textContent
  if (raw === null || raw.trim().length === 0) {
    return null
  }

  let parsed = null
  try {
    parsed = JSON.parse(raw)
  } catch (error) {
    return null
  }
  return parsed
}


async function _fetchJson(url) {
  /*
   * Fetch and parse a JSON document.
   *
   * :param url: The URL to fetch.
   * :returns: The parsed object.
   * :raises: Error when the request fails or the body is not JSON.
   */
  const response = await fetch(url, { headers: { "Accept": "application/json" } })
  if (response.ok === false) {
    throw new Error(`Chart data request failed: ${response.status} ${url}`)
  }
  const parsed = await response.json()
  return parsed
}


export async function resolveChartData(host, dataProperty) {
  /*
   * Resolve the chart data for a controller element from, in order: the
   * `data` property, the `src` attribute, then an inline JSON script.
   *
   * :param host: The controller element.
   * :param dataProperty: The current value of the controller's `data`
   *     property (may be null).
   * :returns: A Promise for the parsed data object, or null when none.
   */
  if (dataProperty !== null && dataProperty !== undefined) {
    return dataProperty
  }

  const src = host.getAttribute("src")
  if (src !== null && src.trim().length > 0) {
    const fetched = await _fetchJson(src.trim())
    return fetched
  }

  const inline = _readInlineJson(host)
  if (inline !== null) {
    return inline
  }

  return null
}
