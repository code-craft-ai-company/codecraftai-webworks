/*
 * pmchartwrapper.js
 *
 * Base class of the project-management chart tags that are thin wrappers
 * over one <mj-chart> chart type:
 *
 *   <mj-gantt-chart>         type "gantt"
 *   <mj-roadmap-chart>       type "roadmap"
 *   <mj-milestone-timeline>  type "milestone"
 *   <mj-dependency-graph>    type "dependency-graph"
 *
 * The chart type is the one implementation: drawing, layout, the keyboard
 * model (one tab stop, arrow keys between marks), the accessible data
 * table, data loading (`data` property, `src`, inline JSON), the loading /
 * empty / error states and resizing all come from <mj-chart> and the
 * type's renderer. This class is not a component and is registered by no
 * tag; a wrapper subclass declares
 *
 *   static chartTypeKey      the <mj-chart> type it draws
 *   static labelKey          intl key of its default accessible name
 *   static optionAliases     { rendererOption: "own-attribute" }
 *   static optionDefaults    { rendererOption: "value" | (element) => value }
 *   static rendererEvents    renderer event names it turns into its own
 *   static toolbarSlot       name of a slot in the toolbar, or null
 *   static detailPanel       { part, slot, placement: "floating" | "inline" }
 *   static deselectEvent     event emitted when the detail panel closes
 *
 * and implements
 *
 *   adaptData(data)                 its documented data -> the type's data
 *   loadDetail(data)                detail of mj-data-load for its data
 *   onRendererEvent(name, detail)   a selection { key, kind, item, title,
 *                                   content, eventName, eventDetail } to
 *                                   show and announce, or null
 *
 * What this class adds to the chart:
 *   - assigning `data` draws at once (like the components it replaces);
 *   - mj-data-load once per data object, mj-error { message } for a data
 *     failure (once per message);
 *   - a toolbar whose button discloses the chart's data table, plus an
 *     optional named slot;
 *   - the selection: the activated mark is marked `aria-current` /
 *     `data-selected` (kept across redraws), its details open in the shared
 *     non-modal detail panel (with a named slot for extra content), Escape
 *     or Close closes it and returns focus to the mark.
 */

import { nextId } from "../core/mjelement.js";
import { html, raw } from "../core/html.js";
import { t } from "../core/intl.js";
import { MjChart } from "../charts/mjchart.js";
import { DetailPanel, PM_CHART_STYLES, detailPanelMarkup, findMark } from "./pmchartsupport.js";

const WRAPPER_STYLES = `
.toolbar { flex: 0 0 auto; }
.detail-panel.is-inline { flex: 0 0 auto; }
.a11y-table-wrap { flex: 0 0 auto; max-block-size: 24rem; overflow: auto; border-block-start: 1px solid var(--mj-border); }
.surface svg [data-selected="true"] > :is(rect, polygon, circle):not([part~="bar-fill"]),
.surface svg :is(rect, polygon, circle)[data-selected="true"] {
  stroke: var(--mj-text);
  stroke-width: 2.5px;
}
`;


export class PmChartWrapper extends MjChart {
  static styles = PM_CHART_STYLES + MjChart.styles + WRAPPER_STYLES;

  static chartTypeKey = "bar";
  static labelKey = "mj.pmChart.noData";
  static optionAliases = {};
  static optionDefaults = {};
  static rendererEvents = [];
  static toolbarSlot = null;
  static detailPanel = { part: "detail-panel", slot: "detail", placement: "inline" };
  static deselectEvent = null;

  constructor() {
    super()

    /* The page's data object the adapted data was built from, and the result. */
    this._adaptedFrom = undefined
    this._adapted = null

    /* The data object whose mj-data-load was emitted, and the last mj-error text. */
    this._loadedFrom = undefined
    this._lastError = null

    /* The selected item: { key, kind, item } or null. */
    this._selection = null

    /* True while the data table is disclosed; survives a reconnect. */
    this._tableShown = false

    this._tableRegionId = nextId("mj-pm-table")
    this._detailHeadingId = nextId("mj-pm-detail")
  }

  /* ----- <mj-chart> subclass hooks ----- */

  get chartType() {
    return this.constructor.chartTypeKey
  }

  get defaultChartLabel() {
    return t(this.constructor.labelKey)
  }

  /*
   * Renderer options under this element's own attribute names, with this
   * element's defaults.
   */
  readOption(name, fallback) {
    const aliases = this.constructor.optionAliases
    const defaults = this.constructor.optionDefaults
    let value = null
    if (Object.prototype.hasOwnProperty.call(aliases, name) === true) {
      value = this.getAttribute(aliases[name])
    } else {
      value = super.readOption(name, null)
    }
    if (value === null && Object.prototype.hasOwnProperty.call(defaults, name) === true) {
      const preset = defaults[name]
      value = typeof preset === "function" ? preset(this) : preset
    }
    const result = value !== null && value !== undefined ? value : fallback
    return result
  }

  /* The type's data, built once per data object of the page. */
  adaptChartData(data) {
    if (data === null || data === undefined) {
      return data
    }
    if (data !== this._adaptedFrom) {
      this._adapted = this.adaptData(data)
      this._adaptedFrom = data
    }
    return this._adapted
  }

  /* ----- subclass hooks ----- */

  adaptData(data) {
    return data
  }

  loadDetail(data) {
    return {}
  }

  onRendererEvent(name, detail) {
    return null
  }

  /* New data was assigned (before it is drawn). */
  onDataAssigned() {
    return
  }

  /* mj-data-load was emitted for `data`. */
  onDataLoaded(data) {
    return
  }

  /* Markup placed between the toolbar and the chart (a banner). */
  renderExtras() {
    return html``
  }

  /* ----- data ----- */

  get data() {
    return super.data
  }

  /* Assigning data draws it at once and clears the selection. */
  set data(value) {
    super.data = value
    this._loadedFrom = undefined
    this._lastError = null
    this._clearSelection()
    this.onDataAssigned()
    if (this._surface !== undefined && this._surface !== null && this.isConnected === true) {
      this.redraw()
    }
    return
  }

  /* Redraw after an in-place change of the data: adapt it again. */
  redraw() {
    this._adaptedFrom = undefined
    const finished = super.redraw()
    return finished
  }

  reload() {
    this._adaptedFrom = undefined
    this._loadedFrom = undefined
    const finished = super.reload()
    return finished
  }

  /* ----- shadow DOM ----- */

  render() {
    const config = this.constructor
    const slotName = config.toolbarSlot
    const markup = html`
      <div class="toolbar" part="toolbar">
        <button class="chart-button table-toggle" type="button" aria-controls="${this._tableRegionId}" aria-expanded="false">${t("mj.pmChart.showDataTable")}</button>
        ${slotName !== null ? html`<slot name="${slotName}"></slot>` : html``}
      </div>
      ${this.renderExtras()}
      ${raw(super.render())}
      ${detailPanelMarkup({ headingId: this._detailHeadingId, part: config.detailPanel.part, slotName: config.detailPanel.slot, placement: config.detailPanel.placement })}`
    return markup
  }

  afterRender() {
    super.afterRender()

    /* The chart's table doubles as the disclosed table (part data-table). */
    this._tableHost.id = this._tableRegionId
    this._tableHost.setAttribute("part", "table data-table")
    this._tableButton = this.$(".table-toggle")
    this._applyTableDisclosure()
    this.listen(this._tableButton, "click", () => {
      this._tableShown = this._tableShown === false
      this._applyTableDisclosure()
    })

    this._detail = new DetailPanel(this, this.$(".detail-panel"), () => {
      this._onDetailClosed()
    })

    const names = this.constructor.rendererEvents
    for (let index = 0; index < names.length; index = index + 1) {
      this.listen(this, names[index], (event) => {
        this._onRendererEvent(event)
      })
    }
    this.listen(this, "mj-chart-render", () => {
      this._onDrawn()
    })
    this.listen(this, "mj-chart-empty", () => {
      this._onDrawn()
    })
    this.listen(this, "mj-chart-error", (event) => {
      this._onChartError(event)
    })
    return
  }

  _applyTableDisclosure() {
    this._tableButton.setAttribute("aria-expanded", this._tableShown === true ? "true" : "false")
    this._tableHost.classList.toggle("a11y-table", this._tableShown === false)
    this._tableHost.classList.toggle("a11y-table-wrap", this._tableShown === true)
    return
  }

  /* ----- events ----- */

  _onDrawn() {
    this._lastError = null
    this._markSelected()

    const source = this._adaptedFrom
    if (source !== undefined && source !== null && source !== this._loadedFrom) {
      this._loadedFrom = source
      this.emit("mj-data-load", this.loadDetail(source))
      this.onDataLoaded(source)
    }
    return
  }

  _onChartError(event) {
    const message = event.detail !== null && event.detail !== undefined ? String(event.detail.message) : ""
    if (message !== this._lastError) {
      this._lastError = message
      this.emit("mj-error", { message: message })
    }
    return
  }

  _onRendererEvent(event) {
    const selection = this.onRendererEvent(event.type, event.detail !== null && event.detail !== undefined ? event.detail : {})
    if (selection === null || selection === undefined) {
      return
    }

    this._selection = { key: selection.key, kind: selection.kind, item: selection.item }
    this._markSelected()
    const key = selection.key
    this._detail.open(selection.title, selection.content, () => {
      const opener = findMark(this.shadowRoot, key)
      return opener
    })
    this.emit(selection.eventName, selection.eventDetail)
    return
  }

  _onDetailClosed() {
    const hadSelection = this._selection !== null
    this._selection = null
    this._markSelected()
    const name = this.constructor.deselectEvent
    if (hadSelection === true && name !== null) {
      this.emit(name, {})
    }
    return
  }

  /* Drop the selection without an event (new data). */
  _clearSelection() {
    this._selection = null
    if (this._detail !== undefined && this._detail !== null) {
      this._detail.close(false)
    }
    this._markSelected()
    return
  }

  /* Reflect the selection on the marks of the current drawing. */
  _markSelected() {
    if (this._surface === undefined || this._surface === null) {
      return
    }
    const key = this._selection !== null ? this._selection.key : null
    const marks = this._surface.querySelectorAll("[data-mark]")
    for (let index = 0; index < marks.length; index = index + 1) {
      const mark = marks[index]
      if (key !== null && mark.getAttribute("data-mark") === key) {
        mark.setAttribute("data-selected", "true")
        mark.setAttribute("aria-current", "true")
      } else if (mark.hasAttribute("data-selected") === true) {
        mark.removeAttribute("data-selected")
        mark.removeAttribute("aria-current")
      }
    }
    return
  }

  /* The selected item of `kind`, or null. */
  selectedOf(kind) {
    const item = this._selection !== null && this._selection.kind === kind ? this._selection.item : null
    return item
  }
}
