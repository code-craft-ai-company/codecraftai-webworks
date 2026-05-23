/*
 * mjchartdatatable.js
 *
 * <mj-chart-data-table> -- a coordinated chart part that renders the
 * chart's data as a real, visible <table>. It binds to its <mj-chart>
 * controller and can be placed/docked anywhere. It doubles as the
 * accessible representation of the chart and as a data inspector.
 */

import { MjElement } from "../core/mjelement.js";
import { ChartPart } from "./core/chartpart.js";
import { buildTableModel } from "./core/chartmodel.js";
import { escapeHtml } from "./core/svgdraw.js";

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
  color: var(--mj-text-muted, #6b7280);
  font-size: var(--mj-font-size-xs, 0.75rem);
  text-transform: uppercase; letter-spacing: 0.05em;
}
tbody tr:hover { background: var(--mj-bg-muted, #eef0f3); }
`;


export class MjChartDataTable extends ChartPart(MjElement) {
  static tagName = "mj-chart-data-table";
  static styles = STYLES;
  static watched = ["chart", "caption"];

  render() {
    const markup = `<div part="container" data-table-host></div>`
    return markup
  }

  afterRender() {
    this._host = this.$("[data-table-host]")
    return
  }

  drawPart(model, context) {
    if (model === null || model === undefined) {
      this._host.innerHTML = ""
      return
    }

    const table = buildTableModel(model)
    const caption = this.getAttribute("caption") || "Chart data"

    const parts = []
    parts.push(`<table part="table"><caption>${escapeHtml(caption)}</caption>`)
    parts.push("<thead><tr>")
    for (let c = 0; c < table.columns.length; c = c + 1) {
      parts.push(`<th scope="col">${escapeHtml(table.columns[c])}</th>`)
    }
    parts.push("</tr></thead><tbody>")
    for (let r = 0; r < table.rows.length; r = r + 1) {
      parts.push("<tr>")
      const record = table.rows[r]
      for (let c = 0; c < record.length; c = c + 1) {
        parts.push(`<td>${escapeHtml(record[c])}</td>`)
      }
      parts.push("</tr>")
    }
    parts.push("</tbody></table>")

    this._host.innerHTML = parts.join("")
    return
  }
}
