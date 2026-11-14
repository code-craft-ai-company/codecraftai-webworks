/*
 * renderregistry.js
 *
 * Registry of chart renderers, keyed by chart `type`. Each renderer module
 * imports `registerRenderer` and registers itself, so importing a renderer
 * file is enough to make its `type` available. The controller resolves a
 * renderer with `getRenderer(type)` and its declared defaults with
 * `getRendererOptions(type)`.
 *
 * A renderer is a function `render(ctx) -> SVGElement` where ctx carries:
 *   type         the chart type key the page asked for (one function may be
 *                registered under several keys and dispatch on this)
 *   model        normalized model { meta, categories, series, allSeries,
 *                hiddenSeries, raw, isEmpty }; `series` holds the visible
 *                series only
 *   raw          the raw data object (family-specific fields live here)
 *   width        drawing surface width in pixels
 *   height       drawing surface height in pixels
 *   orientation  "horizontal" | "vertical"
 *   defaults     the options this type was registered with (see below)
 *   label        the chart's accessible name
 *   hasLegendPart true when an <mj-chart-legend> is bound to the chart; a
 *                renderer that draws an inline key of its own leaves it
 *                out then (the legend part lists the same entries)
 *   attrs        a function (name, fallback) reading controller attributes
 *   colorFor     a function (index|key) -> CSS color string; distinct for
 *                every index and key, stable across renders
 *   emit         a function (eventName, detail) to dispatch interaction events
 *   setTable     a function ({ columns, rows, caption }) publishing the
 *                accessible data table for this render
 *   setLegend    a function ([{ label, color, series }]) publishing the
 *                legend entries for this render
 * and returns an SVGElement (a <g> or nested <svg>) drawn within the surface.
 *
 * Registration options (all optional; the two-argument form uses the
 * defaults, which is the behaviour every renderer had before options existed):
 *   orientation  default orientation when neither the host attribute nor
 *                meta.orientation names one ("vertical")
 *   minHeight    default block size of the host, in pixels, when the page
 *                gives the chart no height of its own (280)
 *   legend       "series" (default), "categories", "none", or a function
 *                (ctx) -> [{ label, color, series }]
 *   table        a function (ctx) -> { columns, rows, caption } building the
 *                accessible table for the type, or null for the generic one
 *   isEmpty      a function (model) -> boolean overriding the generic
 *                "nothing to draw" test, or null
 */

const DEFAULT_ORIENTATION = "vertical";
const DEFAULT_MIN_HEIGHT = 280;
const DEFAULT_LEGEND = "series";

/* type key -> { render, options } */
const RENDERERS = new Map();


function _normalizeOptions(options) {
  /*
   * Fill a registration's options with the defaults.
   *
   * :param options: The options object given to registerRenderer (may be
   *     undefined).
   * :returns: A frozen options object with every field present.
   */
  const given = options !== null && options !== undefined ? options : {}

  let orientation = DEFAULT_ORIENTATION
  if (given.orientation === "horizontal" || given.orientation === "vertical") {
    orientation = given.orientation
  }

  let minHeight = DEFAULT_MIN_HEIGHT
  if (typeof given.minHeight === "number" && Number.isFinite(given.minHeight) === true &&
      given.minHeight > 0) {
    minHeight = given.minHeight
  }

  let legend = DEFAULT_LEGEND
  if (given.legend === "categories" || given.legend === "none" ||
      typeof given.legend === "function") {
    legend = given.legend
  }

  const normalized = {
    orientation: orientation,
    minHeight: minHeight,
    legend: legend,
    table: typeof given.table === "function" ? given.table : null,
    isEmpty: typeof given.isEmpty === "function" ? given.isEmpty : null
  }
  return Object.freeze(normalized)
}


/* Options reported for a type that is not registered. */
const UNREGISTERED_OPTIONS = _normalizeOptions(undefined);


export function registerRenderer(type, renderFn, options) {
  /*
   * Register a renderer under a chart `type` key.
   *
   * :param type: The chart type key, e.g. "bar".
   * :param renderFn: The renderer function.
   * :param options: Optional defaults for the type; see the file header.
   * :raises: Error when the type is not a string or the renderer is not a
   *     function, so a broken registration fails where it is written.
   */
  if (typeof type !== "string" || type.length === 0) {
    throw new Error("registerRenderer expects a non-empty chart type key")
  }
  if (typeof renderFn !== "function") {
    throw new Error(`registerRenderer("${type}") expects a renderer function`)
  }

  RENDERERS.set(type, { render: renderFn, options: _normalizeOptions(options) })
  return
}


export function getRenderer(type) {
  /*
   * Resolve a renderer by chart type.
   *
   * :param type: The chart type key.
   * :returns: The renderer function, or null when unknown.
   */
  const entry = RENDERERS.get(type)
  if (entry === undefined) {
    return null
  }
  return entry.render
}


export function getRendererOptions(type) {
  /*
   * Resolve the defaults a chart type was registered with.
   *
   * :param type: The chart type key.
   * :returns: A frozen { orientation, minHeight, legend, table, isEmpty }
   *     object; the library defaults when the type is unknown.
   */
  const entry = RENDERERS.get(type)
  if (entry === undefined) {
    return UNREGISTERED_OPTIONS
  }
  return entry.options
}


export function deriveContext(parent, overrides) {
  /*
   * Build a complete render context for a renderer that one renderer calls
   * on behalf of another (faceted panels, small multiples). Every field of
   * the parent is kept, the overrides replace fields (type, model, raw,
   * width, height, emit, ...), and setTable / setLegend become no-ops
   * unless the overrides supply them, so a child cannot replace the
   * parent's accessible table or legend. `defaults` follows `type`.
   *
   * :param parent: The context the calling renderer received.
   * :param overrides: The fields that differ for the child.
   * :returns: A new context object.
   */
  const given = overrides !== null && overrides !== undefined ? overrides : {}
  const child = {
    ...parent,
    setTable: () => {
      return
    },
    setLegend: () => {
      return
    },
    ...given
  }
  if (given.defaults === undefined && typeof child.type === "string") {
    child.defaults = getRendererOptions(child.type)
  }
  return child
}


export function hasRenderer(type) {
  /*
   * Report whether a renderer is registered for a type.
   *
   * :param type: The chart type key.
   * :returns: True when a renderer exists.
   */
  const exists = RENDERERS.has(type)
  return exists
}


export function rendererTypes() {
  /*
   * List every registered chart type.
   *
   * :returns: A sorted array of type keys.
   */
  const keys = Array.from(RENDERERS.keys())
  keys.sort()
  return keys
}
