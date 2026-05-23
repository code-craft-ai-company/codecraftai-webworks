/*
 * faceted.js
 *
 * Faceted (small-multiples) renderer — tiles the same child chart type
 * across groups in a pure-SVG grid.  Delegates to the registered
 * childType renderer for each panel; does NOT spawn child <mj-chart>
 * controllers.
 *
 * Registered types:
 *   "faceted"
 *
 * ctx.raw shape:
 *   raw.childType     chart type key for inner renderer (e.g. "bar")
 *   raw.panels        [{label, series:[{name, values:[]}]}]
 *   raw.categories    shared category labels
 *   raw.grid          {cols:N, rowGap:px, colGap:px}
 *   raw.sharedScales  bool (default true)
 *
 * attrs:
 *   facet-type        overrides raw.childType
 */

import { registerRenderer, getRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml } from "../svgdraw.js";


/* ── shared domain computation ───────────────────────────────────────── */

function _unionDomain(panels) {
  /*
   * Compute the union [min, max] across all series values in all panels.
   *
   * :returns: [min, max].
   */
  let lo = Infinity
  let hi = -Infinity

  for (let p = 0; p < panels.length; p = p + 1) {
    const panel = panels[p]
    const series = panel.series || []
    for (let s = 0; s < series.length; s = s + 1) {
      const values = series[s].values || []
      for (let v = 0; v < values.length; v = v + 1) {
        const val = values[v]
        if (typeof val !== "number") {
          continue
        }
        if (val < lo) {
          lo = val
        }
        if (val > hi) {
          hi = val
        }
      }
    }
  }

  if (lo === Infinity) {
    return [0, 1]
  }
  if (lo === hi) {
    return [lo - 1, hi + 1]
  }
  return [lo, hi]
}


/* ── renderer ─────────────────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Render a faceted / small-multiples chart.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw  = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])

  const panels     = (raw !== null && raw !== undefined && Array.isArray(raw.panels))
    ? raw.panels
    : []
  const categories = (raw !== null && raw !== undefined && Array.isArray(raw.categories))
    ? raw.categories
    : []

  if (panels.length === 0) {
    return root
  }

  /* Resolve child renderer type */
  const childTypeName = ctx.attrs("facet-type", null)
    || (raw !== null && raw !== undefined ? raw.childType : null)
    || "bar"

  const childRenderer = getRenderer(childTypeName)
  if (childRenderer === null) {
    /* Draw an error message rather than silently producing nothing */
    root.appendChild(svgEl("text", {
      x: 8, y: 20,
      "font-size": 12,
      fill: "var(--mj-color-danger, #b91c1c)"
    }, `faceted: unknown child type "${childTypeName}"`))
    return root
  }

  const gridConfig  = (raw !== null && raw !== undefined && raw.grid) ? raw.grid : {}
  const gridCols    = gridConfig.cols || Math.ceil(Math.sqrt(panels.length))
  const gridRows    = Math.ceil(panels.length / gridCols)
  const colGap      = gridConfig.colGap !== undefined ? gridConfig.colGap : 16
  const rowGap      = gridConfig.rowGap !== undefined ? gridConfig.rowGap : 16
  const sharedScales = (raw !== null && raw !== undefined && raw.sharedScales === false)
    ? false
    : true

  const TITLE_H = 16
  const margin  = { top: 8, right: 8, bottom: 8, left: 8 }
  const plotW   = Math.max(ctx.width  - margin.left - margin.right,  10)
  const plotH   = Math.max(ctx.height - margin.top  - margin.bottom, 10)

  const panelW  = Math.max(
    Math.floor((plotW - (gridCols - 1) * colGap) / gridCols),
    20
  )
  const panelH  = Math.max(
    Math.floor((plotH - (gridRows - 1) * rowGap) / gridRows),
    20
  )

  /* Shared domain (union across all panels) */
  let sharedDomain = null
  if (sharedScales === true) {
    sharedDomain = _unionDomain(panels)
  }

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  for (let p = 0; p < panels.length; p = p + 1) {
    const panel   = panels[p]
    const col     = p % gridCols
    const row     = Math.floor(p / gridCols)
    const panelX  = col * (panelW + colGap)
    const panelY  = row * (panelH + rowGap)

    /* Panel background */
    plot.appendChild(svgEl("rect", {
      x: panelX, y: panelY,
      width: panelW, height: panelH,
      fill: "none",
      stroke: "var(--mj-border, #e0e3e9)",
      "stroke-width": 1,
      rx: 3
    }, []))

    /* Panel title */
    if (panel.label !== null && panel.label !== undefined) {
      plot.appendChild(svgEl("text", {
        x: panelX + panelW / 2, y: panelY + TITLE_H - 2,
        "text-anchor": "middle",
        "font-size": 10,
        "font-weight": "600",
        fill: "var(--mj-text, #14181f)"
      }, escapeHtml(String(panel.label))))
    }

    /* Build a normalised model for the child renderer */
    const panelSeries = panel.series || []
    const childModel = {
      meta:       { title: panel.label || "" },
      categories: categories.slice(),
      series:     panelSeries,
      raw:        panel
    }

    /* Attach shared domain if applicable */
    const childRaw = { categories: categories.slice(), series: panelSeries }
    if (sharedScales === true && sharedDomain !== null) {
      childRaw._sharedDomain = sharedDomain
    }

    /* Sub-context for the child renderer */
    const childWidth  = panelW
    const childHeight = panelH - TITLE_H

    const childCtx = {
      model:       childModel,
      raw:         childRaw,
      width:       childWidth,
      height:      childHeight,
      orientation: ctx.orientation,
      attrs:       ctx.attrs,
      colorFor:    ctx.colorFor,
      emit:        (eventName, detail) => {
        ctx.emit(eventName, Object.assign({ panelIndex: p, panel: panel }, detail))
      }
    }

    const childG = childRenderer(childCtx)

    /* Translate the child group into the panel's inner region */
    const innerG = svgEl("g", {
      transform: `translate(${panelX},${panelY + TITLE_H})`
    }, [])
    innerG.appendChild(childG)
    plot.appendChild(innerG)
  }

  return root
}


registerRenderer("faceted", render)
