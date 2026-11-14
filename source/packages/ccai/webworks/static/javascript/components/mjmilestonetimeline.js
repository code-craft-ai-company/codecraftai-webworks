/*
 * mjmilestonetimeline.js
 *
 * <mj-milestone-timeline> -- a convenience wrapper for
 * <mj-chart type="milestone"> with the marker data shape of this component
 * family.
 *
 * Drawing (marker shape and colour by kind, labels in tiers above and below
 * the axis, phase bands, the today line, past markers faded), keyboard
 * support, the data table and data loading are the milestone chart type's
 * (charts/core/renderers/timeline.js); the shared wrapper base
 * (pmchartwrapper.js) adds the toolbar, the selection and the detail
 * panel. This file maps the documented data and attributes onto the chart
 * type and its events back onto the documented ones.
 *
 * Data: `data` property, `src` attribute or inline JSON child --
 *   { markers: [{ name, date, type, description }],
 *     phases: [{ name, start, end }] }
 * `type` is release, freeze, tag or milestone (the default). A
 * `YYYY-MM-DD` date is a local calendar day.
 *
 * Attributes: start-date, end-date, density, today-marker (as on the chart
 * type, under these names). Past markers are always drawn faded here
 * (the chart type's dim-past option).
 */

import { html } from "../core/html.js";
import { t } from "../core/intl.js";
import { PmChartWrapper } from "./pmchartwrapper.js";
import { formatChartDate, toText } from "./pmchartsupport.js";
import "../charts/core/renderers/timeline.js";

const WRAPPER_HEIGHT = `
:host { --mj-chart-min-height: 200px; }
`;

export class MjMilestoneTimeline extends PmChartWrapper {
  static tagName = "mj-milestone-timeline";
  static styles = PmChartWrapper.styles + WRAPPER_HEIGHT;
  static chartTypeKey = "milestone";
  static labelKey = "mj.milestoneTimeline.label";
  static optionAliases = { "today": "today-marker" };
  static optionDefaults = { "dim-past": "true" };
  static rendererEvents = ["mj-chart-event-click"];
  static toolbarSlot = null;
  static detailPanel = { part: "detail-popover", slot: "marker-detail", placement: "inline" };
  static deselectEvent = "mj-marker-deselect";

  get selectedMarker() {
    return this.selectedOf("marker")
  }

  /* The name shown for marker `index`: its name, else "Marker N". */
  _name(marker, index) {
    const hasName = marker.name !== undefined && marker.name !== null && toText(marker.name).length > 0
    const name = hasName === true ? toText(marker.name) : t("mj.milestoneTimeline.fallbackName", { number: index + 1 })
    return name
  }

  /* The type as shown to the user: the data value, else the localized default. */
  _typeText(marker) {
    const hasType = marker.type !== undefined && marker.type !== null && toText(marker.type).length > 0
    const text = hasType === true ? toText(marker.type) : t("mj.milestoneTimeline.defaultType")
    return text
  }

  adaptData(data) {
    const markers = Array.isArray(data.markers) === true ? data.markers : []
    const adapted = {
      events: markers.map((marker, index) => {
        const source = marker !== null && typeof marker === "object" ? marker : {}
        const kind = source.type !== undefined && source.type !== null && toText(source.type).length > 0 ? toText(source.type) : "milestone"
        return { id: source.id, label: this._name(source, index), date: source.date, kind: kind, description: source.description }
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
      markers: Array.isArray(data.markers) === true ? data.markers.length : 0,
      phases: Array.isArray(data.phases) === true ? data.phases.length : 0
    }
    return detail
  }

  onRendererEvent(name, detail) {
    const data = this.data !== null && typeof this.data === "object" ? this.data : {}
    const marker = Array.isArray(data.markers) === true ? data.markers[detail.index] : undefined
    let selection = null

    if (marker !== undefined && marker !== null && typeof marker === "object") {
      const hasDescription = marker.description !== undefined && marker.description !== null && toText(marker.description).length > 0
      selection = {
        key: `event:${detail.index}`, kind: "marker", item: marker,
        title: this._name(marker, detail.index),
        content: html`<p><strong>${t("mj.milestoneTimeline.detailType")}</strong> ${this._typeText(marker)}</p><p><strong>${t("mj.milestoneTimeline.detailDate")}</strong> ${formatChartDate(marker.date, { dateStyle: "long" })}</p>${hasDescription === true ? html`<p>${toText(marker.description)}</p>` : html``}`,
        eventName: "mj-marker-select", eventDetail: { marker: marker }
      }
    }
    return selection
  }
}
