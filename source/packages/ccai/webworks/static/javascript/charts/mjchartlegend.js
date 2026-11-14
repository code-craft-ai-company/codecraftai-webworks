/*
 * mjchartlegend.js
 *
 * <mj-chart-legend> -- a coordinated chart part that lists what the chart's
 * colours stand for. It binds to its <mj-chart> controller by the `chart`
 * attribute id (or nearest ancestor) and can be placed and docked anywhere.
 * `orientation` lays the legend out as a row or a column.
 *
 * The entries come from the controller (context.legend): what the renderer
 * published for its chart type, or one entry per series. A series entry is
 * a toggle button -- pressing it hides or shows that series in the chart
 * through the controller's series-visibility API; `aria-pressed="true"`
 * means the series is shown. An entry that only explains a colour (a pie
 * slice, a node) is plain text.
 *
 * `disabled` disables the toggle buttons: they take neither focus nor
 * activation, so the series can be toggled neither by pointer nor by
 * keyboard from this legend (the chart's own API still works).
 *
 * Events
 *   mj-chart-legend-toggle  { series, seriesIndex, visible, hidden }
 */

import { MjElement } from "../core/mjelement.js";
import { ChartPart } from "./core/chartpart.js";

const STYLES = `
:host { display: block; }
.legend {
  display: flex; flex-wrap: wrap; gap: var(--mj-space-2, 0.5rem);
  list-style: none; margin: 0; padding: 0;
}
:host([orientation="vertical"]) .legend { flex-direction: column; }
.entry { display: flex; }
.item {
  display: inline-flex; align-items: center; gap: var(--mj-space-2, 0.5rem);
  font: inherit;
  font-size: var(--mj-font-size-sm, 0.875rem); color: var(--mj-text, #14181f);
  background: none; border: 0; padding: var(--mj-space-1, 0.25rem);
  border-radius: var(--mj-radius-sm, 0.25rem);
}
button.item { cursor: pointer; }
button.item:hover { background: var(--mj-bg-muted, #eef0f3); }
button.item:focus-visible {
  outline: var(--mj-focus-ring-width, 2px) solid var(--mj-focus-ring, #4d83f7);
  outline-offset: 1px;
}
button.item:disabled { cursor: not-allowed; opacity: 0.55; }
button.item:disabled:hover { background: none; }
.swatch {
  inline-size: 0.85rem; block-size: 0.85rem; border-radius: 3px; flex: none;
  border: 2px solid var(--mj-chart-legend-swatch, var(--mj-accent, #2563eb));
  background: var(--mj-chart-legend-swatch, var(--mj-accent, #2563eb));
}
/* A hidden series: hollow swatch and struck-through name, not colour alone. */
.item[aria-pressed="false"] { color: var(--mj-text-muted, #5f6673); }
.item[aria-pressed="false"] .swatch { background: transparent; }
.item[aria-pressed="false"] .label { text-decoration: line-through; }
`;


export class MjChartLegend extends ChartPart(MjElement) {
  static tagName = "mj-chart-legend";
  static styles = STYLES;
  static watched = ["chart", "orientation"];

  constructor() {
    super()
    /* The entries currently drawn and the structure they were built for. */
    this._entries = []
    this._structure = null
  }

  render() {
    const markup = `<ul class="legend" part="legend" role="list"></ul>`
    return markup
  }

  afterRender() {
    this._legendEl = this.$(".legend")
    this._entries = []
    this._structure = null

    /* One delegated listener serves every entry, however often they redraw. */
    this.listen(this._legendEl, "click", (event) => {
      this._onClick(event)
    })
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    super.onAttributeChanged(name, oldValue, newValue)
    if (this._legendEl === undefined || this._legendEl === null) {
      return
    }
    if (name === "disabled") {
      this._applyDisabled()
    }
    return
  }

  /*
   * A disabled legend disables its toggle buttons, so keyboard activation
   * is blocked as well as the pointer (the base stylesheet only stops
   * pointer events on the host).
   */
  _applyDisabled() {
    const disabled = this.hasAttribute("disabled")
    const buttons = this._legendEl.querySelectorAll("button.item")
    for (let index = 0; index < buttons.length; index = index + 1) {
      if (buttons[index].disabled !== disabled) {
        buttons[index].disabled = disabled
      }
    }
    return
  }

  /*
   * The entries to show: the controller's legend, or one per series when
   * the context carries none.
   */
  _readEntries(model, context) {
    let entries = []

    if (context !== null && context !== undefined && Array.isArray(context.legend) === true) {
      entries = context.legend
    } else if (model !== null && model !== undefined) {
      const series = Array.isArray(model.allSeries) === true ? model.allSeries : model.series
      const hidden = Array.isArray(model.hiddenSeries) === true ? model.hiddenSeries : []
      entries = series.map((entry, index) => {
        const color = context !== null && context !== undefined &&
          typeof context.colorScale === "function" ? context.colorScale(entry.name) : null
        return {
          key: `${index}:${entry.name}`,
          label: entry.name,
          color: color,
          series: entry.name,
          hidden: hidden.indexOf(entry.name) >= 0
        }
      })
    }
    return entries
  }

  drawPart(model, context) {
    if (this._legendEl === undefined || this._legendEl === null) {
      return
    }

    const entries = this._readEntries(model, context)
    const structure = entries.map((entry) => {
      return `${entry.key}|${entry.series !== null && entry.series !== undefined ? "toggle" : "static"}`
    }).join("\n")

    /*
     * A redraw with the same entries (a resize, a toggle) updates the
     * existing items, so the button that has focus keeps it.
     */
    if (structure !== this._structure) {
      const items = []
      for (let index = 0; index < entries.length; index = index + 1) {
        items.push(this._buildItem(entries[index], index))
      }
      this._legendEl.replaceChildren(...items)
      this._structure = structure
    }

    this._entries = entries
    const items = this._legendEl.children
    for (let index = 0; index < entries.length && index < items.length; index = index + 1) {
      this._updateItem(items[index], entries[index])
    }
    this._applyDisabled()
    return
  }

  _buildItem(entry, index) {
    const toggles = entry.series !== null && entry.series !== undefined

    const item = document.createElement("li")
    item.className = "entry"
    item.setAttribute("part", "entry")

    const control = document.createElement(toggles === true ? "button" : "span")
    control.className = "item"
    control.setAttribute("part", "item")
    if (toggles === true) {
      control.type = "button"
      control.dataset.index = String(index)
    }

    const swatch = document.createElement("span")
    swatch.className = "swatch"
    swatch.setAttribute("part", "swatch")
    swatch.setAttribute("aria-hidden", "true")

    const label = document.createElement("span")
    label.className = "label"

    control.appendChild(swatch)
    control.appendChild(label)
    item.appendChild(control)
    return item
  }

  _updateItem(item, entry) {
    const control = item.firstElementChild
    const swatch = control.querySelector(".swatch")
    const label = control.querySelector(".label")

    if (label.textContent !== entry.label) {
      label.textContent = entry.label
    }
    if (typeof entry.color === "string" && entry.color.length > 0) {
      swatch.style.setProperty("--mj-chart-legend-swatch", entry.color)
    } else {
      swatch.style.removeProperty("--mj-chart-legend-swatch")
    }
    if (control.localName === "button") {
      /* Pressed means the series is shown. */
      control.setAttribute("aria-pressed", entry.hidden === true ? "false" : "true")
    }
    return
  }

  _onClick(event) {
    const target = event.target
    const control = target !== null && typeof target.closest === "function"
      ? target.closest("button[data-index]")
      : null
    if (control === null) {
      return
    }
    const entry = this._entries[Number(control.dataset.index)]
    if (entry !== undefined) {
      this._toggle(entry)
    }
    return
  }

  /*
   * Hide or show the entry's series in the chart. The controller re-renders
   * and delivers the new legend, which updates this part in place.
   */
  _toggle(entry) {
    const controller = this.controller
    if (controller === null || typeof controller.toggleSeries !== "function") {
      return
    }
    if (this.hasAttribute("disabled") === true) {
      return
    }

    const visible = controller.toggleSeries(entry.series)

    let seriesIndex = -1
    const model = controller.chartModel
    const allSeries = model !== null && model !== undefined && Array.isArray(model.allSeries) === true
      ? model.allSeries
      : []
    for (let index = 0; index < allSeries.length; index = index + 1) {
      if (allSeries[index].name === entry.series) {
        seriesIndex = allSeries[index].sourceIndex
        break
      }
    }

    this.emit("mj-chart-legend-toggle", {
      series: entry.series,
      seriesIndex: seriesIndex,
      visible: visible,
      hidden: visible === false
    })
    return
  }
}
