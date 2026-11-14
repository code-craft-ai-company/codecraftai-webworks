/*
 * mjroadmapchart.js
 *
 * <mj-roadmap-chart> -- a convenience wrapper for <mj-chart type="roadmap">
 * with the initiative data shape of this component family.
 *
 * Drawing, layout (swimlanes with stacked bars, calendar-period or bucket
 * columns), keyboard support, the data table and data loading are the
 * roadmap chart type's (charts/core/renderers/gantt.js); the shared
 * wrapper base (pmchartwrapper.js) adds the toolbar, the selection and the
 * detail panel. This file maps the documented data and attributes onto the
 * chart type and its events back onto the documented ones.
 *
 * Data: `data` property, `src` attribute or inline JSON child --
 *   { swimlanes: [{ id, name }], buckets: [{ id, name }],
 *     initiatives: [{ id, name, swimlaneId, status, percentComplete,
 *                     description, columnId | startDate + endDate }],
 *     markers: [{ name, date }], phases: [{ name, start, end }] }
 * The aliases swimlane, start, end, bucket and column are accepted too. A
 * `YYYY-MM-DD` date is a local calendar day.
 *
 * Attributes: mode, scale, start-date, end-date, today-marker, density (as
 * on the chart type, under these names).
 */

import { html } from "../core/html.js";
import { formatNumber, t } from "../core/intl.js";
import { PmChartWrapper } from "./pmchartwrapper.js";
import { formatChartDate, toNumber, toText } from "./pmchartsupport.js";
import "../charts/core/renderers/gantt.js";

/* The first of `values` that holds something, else undefined. */
function firstGiven(...values) {
  const found = values.find((value) => value !== null && value !== undefined && value !== "")
  return found
}

/* Display text of the known initiative statuses; any other status shows as given. */
const STATUS_LABEL_KEYS = {
  planned:       "mj.roadmapChart.status.planned",
  "in-progress": "mj.roadmapChart.status.inProgress",
  done:          "mj.roadmapChart.status.done",
  "at-risk":     "mj.roadmapChart.status.atRisk",
  blocked:       "mj.roadmapChart.status.blocked"
};

function statusText(status) {
  const known = Object.prototype.hasOwnProperty.call(STATUS_LABEL_KEYS, status) === true
  const text = known === true ? t(STATUS_LABEL_KEYS[status]) : status
  return text
}

/* A { id, name } list as the chart type's { id, label } list. */
function idLabelList(list) {
  const entries = []
  const source = Array.isArray(list) === true ? list : []
  source.forEach((entry) => {
    if (entry !== null && typeof entry === "object") {
      const id = firstGiven(entry.id, entry.name)
      if (id !== undefined) {
        entries.push({ id: String(id), label: toText(firstGiven(entry.name, entry.id)) })
      }
    }
  })
  return entries
}

export class MjRoadmapChart extends PmChartWrapper {
  static tagName = "mj-roadmap-chart";
  static chartTypeKey = "roadmap";
  static labelKey = "mj.roadmapChart.label";
  static optionAliases = { "today": "today-marker" };
  static rendererEvents = ["mj-chart-bar-click"];
  static toolbarSlot = "legend";
  static detailPanel = { part: "initiative-detail", slot: "initiative-detail", placement: "inline" };
  static deselectEvent = "mj-initiative-deselect";

  get selectedInitiative() {
    return this.selectedOf("initiative")
  }

  _name(initiative, index) {
    const name = firstGiven(initiative.name, initiative.id)
    const text = name !== undefined ? toText(name) : t("mj.roadmapChart.defaultInitiativeName", { number: index + 1 })
    return text
  }

  adaptData(data) {
    const initiatives = Array.isArray(data.initiatives) === true ? data.initiatives : []
    const adapted = {
      tasks: initiatives.map((initiative, index) => {
        const source = initiative !== null && typeof initiative === "object" ? initiative : {}
        const lane = firstGiven(source.swimlaneId, source.swimlane)
        const bucket = firstGiven(source.columnId, source.bucket, source.column)
        const percent = source.percentComplete !== undefined && source.percentComplete !== null
          ? Math.min(100, Math.max(0, toNumber(source.percentComplete, 0))) / 100 : undefined
        return {
          id: source.id, label: this._name(source, index),
          start: firstGiven(source.startDate, source.start), end: firstGiven(source.endDate, source.end),
          status: firstGiven(source.status, "planned"), progress: percent,
          group: lane !== undefined ? String(lane) : undefined,
          bucket: bucket !== undefined ? String(bucket) : undefined,
          description: source.description
        }
      }),
      groups: idLabelList(data.swimlanes),
      buckets: idLabelList(data.buckets),
      markers: (Array.isArray(data.markers) === true ? data.markers : []).map((marker) => {
        const source = marker !== null && typeof marker === "object" ? marker : {}
        return { label: toText(source.name), date: source.date }
      }),
      phases: (Array.isArray(data.phases) === true ? data.phases : []).map((phase) => {
        const source = phase !== null && typeof phase === "object" ? phase : {}
        return { label: toText(source.name), start: source.start, end: source.end }
      })
    }
    return adapted
  }

  loadDetail(data) {
    const detail = {
      initiatives: Array.isArray(data.initiatives) === true ? data.initiatives.length : 0,
      swimlanes: Array.isArray(data.swimlanes) === true ? data.swimlanes.length : 0
    }
    return detail
  }

  onRendererEvent(name, detail) {
    const data = this.data !== null && typeof this.data === "object" ? this.data : {}
    const initiative = Array.isArray(data.initiatives) === true ? data.initiatives[detail.index] : undefined
    let selection = null

    if (initiative !== undefined && initiative !== null && typeof initiative === "object") {
      const percent = Math.min(100, Math.max(0, toNumber(initiative.percentComplete, 0)))
      const start = firstGiven(initiative.startDate, initiative.start)
      const end = firstGiven(initiative.endDate, initiative.end)
      const dates = start !== undefined
        ? html`<p><strong>${t("mj.roadmapChart.datesField")}</strong> ${t("mj.roadmapChart.dateRange", { start: formatChartDate(start), end: formatChartDate(end !== undefined ? end : start) })}</p>`
        : html``
      const description = firstGiven(initiative.description) !== undefined ? html`<p>${toText(initiative.description)}</p>` : html``
      selection = {
        key: `task:${detail.index}`, kind: "initiative", item: initiative,
        title: this._name(initiative, detail.index),
        content: html`<p><strong>${t("mj.roadmapChart.statusField")}</strong> ${statusText(toText(firstGiven(initiative.status, "planned")))}</p><p><strong>${t("mj.roadmapChart.percentField")}</strong> ${t("mj.roadmapChart.percent", { percent: formatNumber(percent) })}</p>${dates}${description}`,
        eventName: "mj-initiative-select", eventDetail: { initiative: initiative }
      }
    }
    return selection
  }
}
