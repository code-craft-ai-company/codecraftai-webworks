/*
 * mjchartlegend.js
 *
 * <mj-chart-legend> -- a coordinated chart part that lists the chart's
 * series with color swatches. It binds to its <mj-chart> controller by the
 * `chart` attribute id (or nearest ancestor) and can be placed and docked
 * anywhere. `orientation` lays the legend out as a row or a column.
 * Clicking a legend item emits `mj-chart-legend-toggle`.
 */

import { MjElement } from "../core/mjelement.js";
import { ChartPart } from "./core/chartpart.js";
import { escapeHtml } from "./core/svgdraw.js";

const STYLES = `
:host { display: block; }
.legend { display: flex; flex-wrap: wrap; gap: var(--mj-space-2, 0.5rem); }
:host([orientation="vertical"]) .legend { flex-direction: column; }
.item {
  display: inline-flex; align-items: center; gap: var(--mj-space-2, 0.5rem);
  font-size: var(--mj-font-size-sm, 0.875rem); color: var(--mj-text, #14181f);
  background: none; border: 0; padding: var(--mj-space-1, 0.25rem); cursor: pointer;
  border-radius: var(--mj-radius-sm, 0.25rem);
}
.item:hover { background: var(--mj-bg-muted, #eef0f3); }
.item:focus-visible {
  outline: var(--mj-focus-ring-width, 2px) solid var(--mj-focus-ring, #4d83f7);
  outline-offset: 1px;
}
.item[aria-pressed="true"] { opacity: 0.45; }
.swatch {
  inline-size: 0.85rem; block-size: 0.85rem; border-radius: 3px; flex: none;
}
`;


export class MjChartLegend extends ChartPart(MjElement) {
  static tagName = "mj-chart-legend";
  static styles = STYLES;
  static watched = ["chart", "orientation"];

  constructor() {
    super()
    this._hidden = {}
  }

  render() {
    const markup = `<div class="legend" part="legend" role="list"></div>`
    return markup
  }

  afterRender() {
    this._legendEl = this.$(".legend")
    return
  }

  drawPart(model, context) {
    const series = model !== null && model.series !== undefined ? model.series : []
    const items = []

    for (let index = 0; index < series.length; index = index + 1) {
      const name = series[index].name
      const color = context !== null && context.colorScale !== undefined
        ? context.colorScale(name)
        : "var(--mj-accent, #2563eb)"
      const pressed = this._hidden[name] === true ? "true" : "false"

      const button = document.createElement("button")
      button.type = "button"
      button.className = "item"
      button.setAttribute("part", "item")
      button.setAttribute("role", "listitem")
      button.setAttribute("aria-pressed", pressed)
      button.dataset.series = name
      button.innerHTML =
        `<span class="swatch" part="swatch" style="background:${color}"></span>` +
        `<span>${escapeHtml(name)}</span>`
      this.listen(button, "click", () => {
        this._toggle(name)
      })
      items.push(button)
    }

    this._legendEl.replaceChildren(...items)
    return
  }

  _toggle(name) {
    const next = this._hidden[name] !== true
    this._hidden[name] = next
    this.emit("mj-chart-legend-toggle", { series: name, hidden: next })
    if (this._lastModel !== null) {
      this.drawPart(this._lastModel, this._lastContext)
    }
    return
  }
}
