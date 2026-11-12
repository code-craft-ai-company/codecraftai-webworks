/*
 * mjchartdatatable.js
 *
 * <mj-chart-data-table> -- a coordinated chart part that renders the
 * chart's data as a real, visible <table>. It binds to its <mj-chart>
 * controller and can be placed/docked anywhere. It doubles as the
 * accessible representation of the chart and as a data inspector.
 *
 * The table is the one the controller built for the render: the renderer's
 * own table for its chart type when it publishes one, else the generic
 * table of the data. Hidden series are left out; when every series is
 * hidden a short note says so instead of a table. At most TABLE_ROW_LIMIT
 * rows are shown, with a note when rows were cut.
 *
 * Attributes
 *   chart     id of the <mj-chart> to bind to
 *   caption   table caption (defaults to the renderer's caption for its
 *             table, else the chart's accessible name, else the localized
 *             "Chart data")
 */

import { MjElement } from "../core/mjelement.js";
import { t } from "../core/intl.js";
import { ChartPart } from "./core/chartpart.js";
import { buildTableModel, buildTableElement, tableSignature } from "./core/chartmodel.js";

const STYLES = `
:host { display: block; overflow: auto; }
table {
  border-collapse: collapse; inline-size: 100%;
  font-size: var(--mj-font-size-sm, 0.875rem); color: var(--mj-text, #14181f);
}
caption {
  text-align: start; font-weight: var(--mj-font-weight-medium, 500);
  padding-block-end: var(--mj-space-2, 0.5rem);
}
th, td {
  text-align: start; padding: var(--mj-space-2, 0.5rem) var(--mj-space-3, 0.75rem);
  border-block-end: 1px solid var(--mj-border, #e0e3e9);
}
thead th {
  background: var(--mj-bg-subtle, #f7f8fa);
  color: var(--mj-text-muted, #5f6673);
  font-size: var(--mj-font-size-xs, 0.75rem);
  text-transform: uppercase; letter-spacing: 0.05em;
}
tbody th { font-weight: var(--mj-font-weight-medium, 500); }
tbody tr:hover { background: var(--mj-bg-muted, #eef0f3); }
tfoot td { color: var(--mj-text-muted, #5f6673); font-style: italic; }
.empty {
  margin: 0; padding-block: var(--mj-space-2, 0.5rem);
  font-size: var(--mj-font-size-sm, 0.875rem); color: var(--mj-text-muted, #5f6673);
  font-style: italic;
}
`;


export class MjChartDataTable extends ChartPart(MjElement) {
  static tagName = "mj-chart-data-table";
  static styles = STYLES;
  static watched = ["chart", "caption"];

  constructor() {
    super()
    /* Fingerprint of the table currently in the DOM. */
    this._signature = null
  }

  render() {
    const markup = `<div part="container" data-table-host></div>`
    return markup
  }

  afterRender() {
    this._host = this.$("[data-table-host]")
    this._signature = null
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    super.onAttributeChanged(name, oldValue, newValue)
    if (this._host === undefined || this._host === null) {
      return
    }
    if (name === "caption") {
      this.drawPart(this._lastModel, this._lastContext)
    }
    return
  }

  drawPart(model, context) {
    if (this._host === undefined || this._host === null) {
      return
    }

    if (model === null || model === undefined) {
      this._host.replaceChildren()
      this._signature = null
      return
    }

    const hasContext = context !== null && context !== undefined
    const table = hasContext === true && context.table !== null && context.table !== undefined
      ? context.table
      : buildTableModel(model, null)

    let caption = this.getAttribute("caption")
    if (caption === null || caption.trim().length === 0) {
      caption = table.caption
    }
    if ((caption === null || caption === undefined) && hasContext === true &&
        typeof context.label === "string" && context.label.length > 0) {
      caption = context.label
    }
    if (caption === null || caption === undefined) {
      caption = t("mj.chart.tableCaption")
    }

    /*
     * Every series switched off: there is no data to list. The generic
     * table would fall back to listing the rest of the data (the category
     * labels), so a note takes the table's place instead.
     */
    const allHidden = Array.isArray(model.hiddenSeries) === true && model.hiddenSeries.length > 0 &&
      Array.isArray(model.series) === true && model.series.length === 0

    /* The chart re-broadcasts on every resize; identical tables are kept. */
    const signature = allHidden === true
      ? "all-series-hidden"
      : `${caption}|${tableSignature(table)}`
    if (signature === this._signature) {
      return
    }
    this._signature = signature

    if (allHidden === true) {
      const note = document.createElement("p")
      note.className = "empty"
      note.setAttribute("part", "empty")
      note.textContent = t("mj.chart.tableAllSeriesHidden")
      this._host.replaceChildren(note)
      return
    }

    if (table.columns.length === 0) {
      this._host.replaceChildren()
      return
    }

    const truncatedNote = t("mj.chart.tableTruncated", { count: table.rows.length })
    const element = buildTableElement(table, caption, truncatedNote)
    element.setAttribute("part", "table")
    this._host.replaceChildren(element)
    return
  }
}
