/*
 * renderregistry.js
 *
 * Registry of chart renderers, keyed by chart `type`. Each renderer module
 * imports `registerRenderer` and registers itself, so importing a renderer
 * file is enough to make its `type` available. The controller resolves a
 * renderer with `getRenderer(type)`.
 *
 * A renderer is a function `render(ctx) -> SVGElement` where ctx carries:
 *   model        normalized model { meta, categories, series, raw }
 *   raw          the raw data object (family-specific fields live here)
 *   width        drawing surface width in pixels
 *   height       drawing surface height in pixels
 *   orientation  "horizontal" | "vertical"
 *   attrs        a function (name, fallback) reading controller attributes
 *   colorFor     a function (index|key) -> CSS color string
 *   emit         a function (eventName, detail) to dispatch interaction events
 * and returns an SVGElement (a <g> or nested <svg>) drawn within the surface.
 */

const RENDERERS = {};


export function registerRenderer(type, renderFn) {
  /*
   * Register a renderer under a chart `type` key.
   *
   * :param type: The chart type key, e.g. "bar".
   * :param renderFn: The renderer function.
   */
  RENDERERS[type] = renderFn
  return
}


export function getRenderer(type) {
  /*
   * Resolve a renderer by chart type.
   *
   * :param type: The chart type key.
   * :returns: The renderer function, or null when unknown.
   */
  const renderFn = RENDERERS[type]
  if (renderFn === undefined) {
    return null
  }
  return renderFn
}


export function hasRenderer(type) {
  /*
   * Report whether a renderer is registered for a type.
   *
   * :param type: The chart type key.
   * :returns: True when a renderer exists.
   */
  const exists = type in RENDERERS
  return exists
}


export function rendererTypes() {
  /*
   * List every registered chart type.
   *
   * :returns: A sorted array of type keys.
   */
  const keys = Object.keys(RENDERERS)
  keys.sort()
  return keys
}
