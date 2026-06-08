/*
 * mjchart.js
 *
 * <mj-chart> -- the chart controller and the host of the default composed
 * chart. It ingests JSON data, builds the normalized model, sizes an SVG
 * drawing surface, dispatches to the renderer registered for its `type`,
 * and broadcasts the model + context to any coordinated chart part
 * components (legend, title, axis, data-table, tooltip) bound to it.
 *
 * Data sources, in priority order: the `data` JS property, the `src`
 * attribute (a JSON URL), or an inline <script type="application/json">.
 *
 * The component re-renders dynamically whenever `data`, `type`, or
 * `orientation` change. It extends MjElement, so it inherits theming,
 * docking/anchoring, and the context menu.
 */

import { MjElement } from "../core/mjelement.js";
import { resolveChartData } from "./core/jsonsource.js";
import { buildModel, buildTableModel } from "./core/chartmodel.js";
import { getRenderer, hasRenderer } from "./core/renderregistry.js";
import { ordinalColorScale } from "./core/scales.js";
import { svgRoot, svgEl, escapeHtml } from "./core/svgdraw.js";

const STYLES = `
:host {
  display: block;
  inline-size: 100%;
  min-block-size: var(--mj-chart-min-height, 280px);
  position: relative;
  color: var(--mj-text, #14181f);
  font-family: var(--mj-font-sans, system-ui, sans-serif);
}
.surface { inline-size: 100%; block-size: 100%; min-block-size: inherit; }
.surface svg { display: block; inline-size: 100%; block-size: 100%; }
.message {
  display: flex; align-items: center; justify-content: center;
  block-size: 100%; min-block-size: var(--mj-chart-min-height, 280px);
  color: var(--mj-text-muted, #6b7280); font-size: var(--mj-font-size-sm, 0.875rem);
  text-align: center; padding: var(--mj-space-4, 1rem);
}
.a11y-table {
  position: absolute; inline-size: 1px; block-size: 1px;
  margin: -1px; padding: 0; overflow: hidden;
  clip: rect(0 0 0 0); clip-path: inset(50%); white-space: nowrap;
}
`;


export class MjChart extends MjElement {
  static tagName = "mj-chart";
  static styles = STYLES;
  static watched = ["type", "orientation", "src"];

  constructor() {
    super()
    this._data = null
    this._model = null
    this._context = null
    this._parts = []
    this._resizeObserver = null
    this._renderScheduled = false
  }

  render() {
    const markup = `
      <div class="surface" part="surface" data-chart-surface></div>
      <div class="a11y-table" part="table" data-chart-table aria-live="polite"></div>
    `
    return markup
  }

  afterRender() {
    this._surface = this.$("[data-chart-surface]")
    this._tableHost = this.$("[data-chart-table]")
    this.setAttribute("role", "figure")
    return
  }

  onConnected() {
    if (typeof ResizeObserver === "function") {
      this._resizeObserver = new ResizeObserver(() => {
        this._scheduleRender()
      })
      this._resizeObserver.observe(this)
    }
    this._scheduleRender()
    return
  }

  onDisconnected() {
    if (this._resizeObserver !== null) {
      this._resizeObserver.disconnect()
      this._resizeObserver = null
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "type" || name === "orientation" || name === "src") {
      if (this._surface !== undefined) {
        this._scheduleRender()
      }
    }
    return
  }

  /* ----- data API ----- */

  get data() {
    return this._data
  }

  set data(value) {
    this._data = value
    if (this._surface !== undefined) {
      this._scheduleRender()
    }
    return
  }

  /* The normalized model -- chart parts pull this on connect. */
  get chartModel() {
    return this._model
  }

  /* The render context (size, orientation, colors) -- parts read this. */
  get chartContext() {
    return this._context
  }

  /* ----- coordinated parts ----- */

  registerPart(part) {
    if (this._parts.indexOf(part) < 0) {
      this._parts.push(part)
    }
    if (this._model !== null && typeof part.applyModel === "function") {
      part.applyModel(this._model, this._context)
    }
    return
  }

  unregisterPart(part) {
    const index = this._parts.indexOf(part)
    if (index >= 0) {
      this._parts.splice(index, 1)
    }
    return
  }

  _broadcast() {
    for (let index = 0; index < this._parts.length; index = index + 1) {
      const part = this._parts[index]
      if (typeof part.applyModel === "function") {
        part.applyModel(this._model, this._context)
      }
    }
    return
  }

  /* ----- rendering ----- */

  _scheduleRender() {
    if (this._renderScheduled === true) {
      return
    }
    this._renderScheduled = true
    window.requestAnimationFrame(() => {
      this._renderScheduled = false
      this._renderChart()
    })
    return
  }

  async _renderChart() {
    let raw = null
    try {
      raw = await resolveChartData(this, this._data)
    } catch (error) {
      this._showMessage(error.message)
      this.emit("mj-chart-error", { message: error.message })
      return
    }

    const model = buildModel(raw)
    this._model = model

    const type = this.getAttribute("type") || "bar"
    if (hasRenderer(type) === false) {
      this._showMessage(`No renderer for chart type "${type}".`)
      this.emit("mj-chart-error", { message: `Unknown chart type: ${type}` })
      return
    }

    if (model.isEmpty === true) {
      this._showMessage("No chart data supplied.")
      return
    }

    const rect = this.getBoundingClientRect()
    const width = Math.max(rect.width, 120)
    const height = Math.max(rect.height, 160)

    const colorScale = ordinalColorScale(model.series.map((s) => s.name))
    const context = {
      width: width,
      height: height,
      orientation: this.getAttribute("orientation") || model.meta.orientation || "vertical",
      colorScale: colorScale
    }
    this._context = context

    const renderFn = getRenderer(type)
    const ctx = {
      model: model,
      raw: model.raw,
      width: width,
      height: height,
      orientation: context.orientation,
      attrs: (name, fallback) => {
        const value = this.getAttribute(name)
        return value !== null ? value : fallback
      },
      colorFor: (keyOrIndex) => {
        if (typeof keyOrIndex === "number") {
          const name = model.series[keyOrIndex] !== undefined
            ? model.series[keyOrIndex].name
            : String(keyOrIndex)
          return colorScale(name)
        }
        return colorScale(keyOrIndex)
      },
      emit: (eventName, detail) => {
        this.emit(eventName, detail)
      }
    }

    let drawn = null
    try {
      drawn = renderFn(ctx)
    } catch (error) {
      this._showMessage(`Chart render error: ${error.message}`)
      this.emit("mj-chart-error", { message: error.message })
      return
    }

    const root = svgRoot(width, height)
    root.setAttribute("part", "svg")
    root.setAttribute("aria-hidden", "true")
    if (drawn !== null && drawn !== undefined) {
      root.appendChild(drawn)
    }

    this._surface.replaceChildren(root)
    this._renderTable(model)
    this._broadcast()

    this.emit("mj-chart-render", { type: type })
    return
  }

  _showMessage(text) {
    const message = svgEl("div", null, null)
    /* message is plain HTML, not SVG -- build a div instead. */
    const div = document.createElement("div")
    div.className = "message"
    div.setAttribute("part", "message")
    div.textContent = text
    this._surface.replaceChildren(div)
    return
  }

  _renderTable(model) {
    const table = buildTableModel(model)
    const rows = []
    rows.push("<table><caption>Chart data</caption><thead><tr>")
    for (let c = 0; c < table.columns.length; c = c + 1) {
      rows.push(`<th>${escapeHtml(table.columns[c])}</th>`)
    }
    rows.push("</tr></thead><tbody>")
    for (let r = 0; r < table.rows.length; r = r + 1) {
      rows.push("<tr>")
      const record = table.rows[r]
      for (let c = 0; c < record.length; c = c + 1) {
        rows.push(`<td>${escapeHtml(record[c])}</td>`)
      }
      rows.push("</tr>")
    }
    rows.push("</tbody></table>")
    this._tableHost.innerHTML = rows.join("")
    return
  }

  /* Force a synchronous re-render (useful for tests). */
  redraw() {
    this._renderChart()
    return
  }
}
