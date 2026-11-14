/*
 * mjganttchart.js
 *
 * <mj-gantt-chart> -- a convenience wrapper for <mj-chart type="gantt">
 * with the project data shape of this component family.
 *
 * Drawing, layout, keyboard support, the data table and data loading are
 * the gantt chart type's (charts/core/renderers/gantt.js); the shared
 * wrapper base (pmchartwrapper.js) adds the toolbar, the selection and the
 * detail panel. This file maps the documented data and attributes onto the
 * chart type and its events back onto the documented ones.
 *
 * Data: `data` property, `src` attribute or inline JSON child --
 *   { tasks: [{ id, name, start, end, percentComplete, status, groupId,
 *               milestone }],
 *     groups: [{ id, name }], dependencies: [{ from, to }],
 *     markers: [{ name, date }], phases: [{ name, start, end }] }
 * A `YYYY-MM-DD` date is a local calendar day and an end date given that way
 * is inclusive. A task without an end date runs to the edge of the chart.
 *
 * Attributes: scale, start-date, end-date, today-marker, show-dependencies,
 * show-percent, density (as on the chart type, under these names).
 */

import { html } from "../core/html.js";
import { formatNumber, t } from "../core/intl.js";
import { PmChartWrapper } from "./pmchartwrapper.js";
import { formatChartDate, toNumber, toText } from "./pmchartsupport.js";
import "../charts/core/renderers/gantt.js";

/* A field that holds something (not null, undefined or ""). */
function given(value) {
  const present = value !== null && value !== undefined && value !== ""
  return present
}

export class MjGanttChart extends PmChartWrapper {
  static tagName = "mj-gantt-chart";
  static chartTypeKey = "gantt";
  static labelKey = "mj.ganttChart.label";
  static optionAliases = { "today": "today-marker", "show-progress": "show-percent" };
  static optionDefaults = { "row-height": (chart) => (chart.getAttribute("density") === "compact" ? "28" : "40") };
  static rendererEvents = ["mj-chart-bar-click", "mj-chart-marker-click", "mj-chart-group-toggle"];
  static toolbarSlot = "toolbar";
  static detailPanel = { part: "task-detail", slot: "task-detail", placement: "floating" };
  static deselectEvent = "mj-task-deselect";

  get selectedTask() {
    return this.selectedOf("task")
  }

  /* Ids of the collapsed groups (as the data names them). */
  get collapsedGroups() {
    const keys = new Set()
    const value = this.getAttribute("collapsed-groups")
    if (value !== null) {
      try {
        const parsed = JSON.parse(value)
        if (Array.isArray(parsed) === true) {
          parsed.forEach((key) => keys.add(String(key)))
        }
      } catch (error) {
        value.split(",").forEach((key) => keys.add(key.trim()))
      }
    }
    const ids = new Set()
    this._groups().forEach((group) => {
      if (keys.has(String(group.id)) === true) {
        ids.add(group.id)
      }
    })
    return ids
  }

  /* New data starts with every group expanded. */
  onDataAssigned() {
    this.removeAttribute("collapsed-groups")
    return
  }

  /* The documented groups as { id, name } (the id falls back to the name). */
  _groups() {
    const data = this.data !== null && typeof this.data === "object" ? this.data : {}
    const list = Array.isArray(data.groups) === true ? data.groups : []
    const groups = []
    list.forEach((group) => {
      if (group !== null && typeof group === "object" && (given(group.id) === true || given(group.name) === true)) {
        groups.push({ id: given(group.id) === true ? group.id : group.name, name: given(group.name) === true ? group.name : group.id })
      }
    })
    return groups
  }

  adaptData(data) {
    const tasks = Array.isArray(data.tasks) === true ? data.tasks : []
    const groups = Array.isArray(data.groups) === true ? data.groups : []
    const groupIds = new Set()
    const adaptedGroups = []
    groups.forEach((group) => {
      if (group !== null && typeof group === "object" && (given(group.id) === true || given(group.name) === true)) {
        const id = String(given(group.id) === true ? group.id : group.name)
        groupIds.add(id)
        adaptedGroups.push({ id: id, label: toText(given(group.name) === true ? group.name : id) })
      }
    })

    /* `dependencies` become each successor's `depends` list. */
    const depends = new Map()
    const dependencies = Array.isArray(data.dependencies) === true ? data.dependencies : []
    dependencies.forEach((link) => {
      if (link !== null && typeof link === "object" && given(link.from) === true && given(link.to) === true) {
        const target = String(link.to)
        if (depends.has(target) === false) {
          depends.set(target, [])
        }
        depends.get(target).push(String(link.from))
      }
    })

    const adapted = {
      tasks: tasks.map((task, index) => {
        const source = task !== null && typeof task === "object" ? task : {}
        const name = given(source.name) === true ? toText(source.name) : ""
        const id = given(source.id) === true ? String(source.id) : (name !== "" ? name : `task-${index + 1}`)
        const groupId = given(source.groupId) === true && groupIds.has(String(source.groupId)) === true ? String(source.groupId) : undefined
        return {
          id: id, label: name !== "" ? name : id, start: source.start, end: source.end,
          progress: Math.min(100, Math.max(0, toNumber(source.percentComplete, 0))) / 100,
          status: source.status, group: groupId, depends: depends.get(id),
          milestone: source.milestone === true || source.type === "milestone"
        }
      }),
      groups: adaptedGroups,
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
      tasks: Array.isArray(data.tasks) === true ? data.tasks.length : 0,
      groups: Array.isArray(data.groups) === true ? data.groups.length : 0
    }
    return detail
  }

  onRendererEvent(name, detail) {
    const data = this.data !== null && typeof this.data === "object" ? this.data : {}
    let selection = null

    if (name === "mj-chart-bar-click") {
      const task = Array.isArray(data.tasks) === true ? data.tasks[detail.index] : undefined
      if (task !== undefined && task !== null) {
        const source = typeof task === "object" ? task : {}
        const percent = Math.min(100, Math.max(0, toNumber(source.percentComplete, 0)))
        const endText = given(source.end) === true ? formatChartDate(source.end) : t("mj.ganttChart.openEnded")
        selection = {
          key: `task:${detail.index}`, kind: "task", item: task,
          title: given(source.name) === true ? toText(source.name) : toText(given(source.id) === true ? source.id : `task-${detail.index + 1}`),
          content: html`<p><strong>${t("mj.ganttChart.detailStart")}</strong> ${formatChartDate(source.start)}</p><p><strong>${t("mj.ganttChart.detailEnd")}</strong> ${endText}</p><p><strong>${t("mj.ganttChart.detailPercent")}</strong> ${formatNumber(percent)}%</p><p><strong>${t("mj.ganttChart.detailStatus")}</strong> ${toText(source.status)}</p>`,
          eventName: "mj-task-select", eventDetail: { task: task }
        }
      }
    } else if (name === "mj-chart-marker-click") {
      const marker = Array.isArray(data.markers) === true ? data.markers[detail.index] : undefined
      if (marker !== undefined && marker !== null) {
        selection = {
          key: `marker:${detail.index}`, kind: "marker", item: marker,
          title: toText(marker.name),
          content: html`<p><strong>${t("mj.ganttChart.detailDate")}</strong> ${formatChartDate(marker.date)}</p>`,
          eventName: "mj-marker-select", eventDetail: { marker: marker }
        }
      }
    } else if (name === "mj-chart-group-toggle") {
      const group = this._groups().find((candidate) => String(candidate.id) === String(detail.group))
      this.emit("mj-group-toggle", { groupId: group !== undefined ? group.id : detail.group, collapsed: detail.collapsed === true })
    }
    return selection
  }
}
