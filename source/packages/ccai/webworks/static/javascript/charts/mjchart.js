/*
 * mjchart.js
 *
 * <mj-chart> -- the chart controller and the host of the default composed
 * chart. It ingests JSON data, builds the normalized model, sizes an SVG
 * drawing surface, dispatches to the renderer registered for its `type`,
 * and broadcasts the model + context to any coordinated chart part
 * components (legend, title, data-table) bound to it.
 *
 * Data sources, in priority order: the `data` JS property, the `src`
 * attribute (a JSON URL), or an inline <script type="application/json">.
 * A `src` response is fetched once and reused by every later render;
 * `reload()` fetches it again.
 *
 * The component re-renders whenever `data`, `src`, the inline JSON, `type`,
 * `orientation`, any renderer option attribute, the set of hidden series or
 * its size change. It extends MjElement, so it inherits theming,
 * docking/anchoring, and the context menu.
 *
 * Attributes
 *   type          chart type key (default "bar")
 *   orientation   "vertical" | "horizontal"; defaults to meta.orientation,
 *                 then to the orientation the renderer registered
 *   src           URL of the JSON data
 *   label         accessible name of the chart (falls back to `title`, a
 *                 bound <mj-chart-title>, meta.title, then "<type> chart")
 *   description   longer text alternative, read with the chart
 *   variant       renderer drawing variant (what renderers read as the
 *                 "style" option; the `style` attribute itself is CSS)
 *   (any other)   renderer options, read through ctx.attrs(name, fallback)
 *
 * Size: the chart fills the block size the page gives its host (inline
 * style, a class, a grid or flex cell). With no height of its own it is
 * `--mj-chart-min-height` tall, else the renderer's registered minHeight,
 * else 280px.
 *
 * Events
 *   mj-chart-render         { type, duration }  after a successful draw
 *   mj-chart-empty          { type }            the data holds nothing to draw
 *   mj-chart-error          { message }         data or renderer failure
 *   mj-chart-series-toggle  { series, seriesIndex, visible, hidden,
 *                             hiddenSeries }    a series was hidden or shown
 *   mj-chart-connect        { }                 the controller connected
 *
 * Accessibility: the host is a `figure` named by `label`. The drawing is
 * exposed (not aria-hidden); its focusable marks form one tab stop with
 * arrow-key movement between them. A visually hidden data table, built by
 * the renderer for its chart type or generically from the data, follows
 * the drawing. It is not a live region.
 *
 * Slots: chart parts (<mj-chart-title>, <mj-chart-legend>,
 * <mj-chart-data-table>) nested in the chart; `empty` replaces the text
 * shown when the data holds nothing to draw.
 *
 * Subclassing: an element that is one chart type with its own data shape
 * (<mj-gantt-chart> is type "gantt") extends this class and overrides
 *   get chartType()            the type key to draw (default: the `type`
 *                              attribute, else "bar")
 *   get defaultChartLabel()    the accessible name used when the page names
 *                              none (default: "<type> chart")
 *   adaptChartData(data)       the data the renderer reads, from the data
 *                              the page gave (default: unchanged). Return
 *                              the same object for the same input, so
 *                              colours and cached layouts stay put.
 *   readOption(name, fallback) a renderer option (ctx.attrs); override to
 *                              map the element's own attribute names or
 *                              defaults onto the renderer's options.
 */

import { MjElement } from "../core/mjelement.js";
import { t } from "../core/intl.js";
import {
  ChartSourceCache, ChartReferenceCache, readInlineText, parseInlineJson, validateChartData
} from "./core/jsonsource.js";
import {
  buildModel, buildTableModel, buildTableElement, tableSignature
} from "./core/chartmodel.js";
import { CONTROLLER_CONNECT_EVENT } from "./core/chartregistry.js";
import { getRenderer, getRendererOptions, hasRenderer } from "./core/renderregistry.js";
import { seriesColor } from "./core/scales.js";
import { svgRoot } from "./core/svgdraw.js";

const STYLES = `
:host {
  display: flex;
  flex-direction: column;
  inline-size: 100%;
  position: relative;
  color: var(--mj-text, #14181f);
  font-family: var(--mj-font-sans, system-ui, sans-serif);
}
/*
 * The surface is the flex item that takes the host's block size: all of it
 * when the page gives the host a height, the default height otherwise. The
 * drawing is positioned over it, so the SVG's own aspect ratio never feeds
 * back into the layout.
 */
.surface {
  position: relative;
  flex: 1 1 max(
    var(--mj-chart-min-height, var(--mj-chart-default-height, 280px)),
    var(--mj-chart-content-height, 0px)
  );
  min-block-size: 0;
  inline-size: 100%;
  overflow-x: hidden;
  overflow-y: auto;
}
/* Only the drawing root: SVGs nested inside it (foreignObject cells) keep their own size. */
.surface > svg {
  position: absolute; inset: 0;
  display: block; inline-size: 100%; block-size: 100%;
}
/* Content taller than a fixed-height host: draw it full height and scroll. */
.surface > svg[data-overflow] { inset-block-end: auto; block-size: auto; }
.surface svg [tabindex]:focus-visible {
  outline: var(--mj-focus-ring-width, 2px) solid var(--mj-focus-ring, #4d83f7);
  outline-offset: 1px;
}
/*
 * A quiet mark: invisible until hovered or focused. Renderers keep one per
 * data point when their visible markers are switched off, so the chart
 * still has a tab stop and click targets.
 */
.surface svg [data-quiet-mark]:hover,
.surface svg [data-quiet-mark]:focus-visible { fill-opacity: 1; }
.message {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  color: var(--mj-text-muted, #5f6673); font-size: var(--mj-font-size-sm, 0.875rem);
  text-align: center; padding: var(--mj-space-4, 1rem);
}
.a11y-table, .description {
  position: absolute; inline-size: 1px; block-size: 1px;
  margin: -1px; padding: 0; overflow: hidden;
  clip: rect(0 0 0 0); clip-path: inset(50%); white-space: nowrap;
}
/* Chart parts nested in the controller: title above, the rest below. */
::slotted(*) { flex: 0 0 auto; }
::slotted(mj-chart-title) { order: -1; }
/* Only the default slot holds chart parts; named slots (empty) show their content. */
slot:not([name])::slotted(:not(mj-chart-title):not(mj-chart-legend):not(mj-chart-data-table)) {
  display: none;
}
`;

/*
 * Host attributes that never change what the renderer draws. A change of
 * any other attribute re-renders the chart, because renderers read their
 * options from host attributes through ctx.attrs().
 */
const NON_RENDER_ATTRIBUTES = [
  "style", "class", "id", "role", "slot", "part", "tabindex", "hidden",
  "dock", "anchor", "theme", "data-theme", "disabled", "context-menu",
  "context-menu-label",
  /* Handled by onAttributeChanged. */
  "type", "orientation", "src", "label", "description"
];

/* The drawing box is never treated as smaller than this (pixels). */
const MIN_DRAW_SIZE = 16;

/* ctx.setContentHeight never asks for more than this (pixels). */
const MAX_CONTENT_HEIGHT = 20000;


export class MjChart extends MjElement {
  static tagName = "mj-chart";
  static styles = STYLES;
  static watched = ["type", "orientation", "src", "label", "description"];

  constructor() {
    super()
    this._data = null
    this._model = null
    this._context = null
    this._table = null
    this._tableSignature = null
    this._parts = []
    this._state = "idle"

    this._resizeObserver = null
    this._mutationObserver = null
    this._renderScheduled = false
    this._lastWidth = -1
    this._lastHeight = -1

    /* True while what is on the surface depends on the surface's size. */
    this._sizeDependent = false

    /* Every render takes the next number; only the latest may paint. */
    this._renderSequence = 0

    this._sourceCache = new ChartSourceCache()
    this._referenceCache = new ChartReferenceCache()
    this._inlineText = null
    this._inlineData = null

    /*
     * The block size the renderer last said its content needs
     * (ctx.setContentHeight), 0 when it did not say.
     */
    this._contentHeight = 0

    /* Names of the series the user switched off. Survives re-renders. */
    this._hiddenSeries = []

    /*
     * The generic table of the current data, built before the renderer
     * runs (renderers may write layout fields into the data) and reused by
     * re-renders of the same data object and hidden-series set.
     */
    this._genericTableCache = null

    /* Colour slots handed to non-series keys, kept while the data lives. */
    this._colorSlots = new Map()
    this._colorSource = null

    /* Focusable marks of the current drawing and the one in the tab order. */
    this._marks = []
    this._activeMark = 0

    /* The aria-label this component wrote, to tell it from an author's. */
    this._appliedLabel = null
    this._messageText = null
  }

  render() {
    const markup = `
      <p class="description" part="description" data-chart-description hidden></p>
      <div class="surface" part="surface" data-chart-surface></div>
      <slot></slot>
      <div class="a11y-table" part="table" data-chart-table></div>
    `
    return markup
  }

  afterRender() {
    this._surface = this.$("[data-chart-surface]")
    this._tableHost = this.$("[data-chart-table]")
    this._descriptionEl = this.$("[data-chart-description]")

    /* The shadow DOM is new: nothing drawn, no table, no marks. */
    this._tableSignature = null
    this._messageText = null
    this._marks = []
    this._lastWidth = -1
    this._lastHeight = -1

    if (this.hasAttribute("role") === false) {
      this.setAttribute("role", "figure")
    }

    this.listen(this._surface, "keydown", (event) => {
      this._onSurfaceKeydown(event)
    })
    this.listen(this._surface, "focusin", (event) => {
      this._onSurfaceFocusIn(event)
    })
    return
  }

  onConnected() {
    if (typeof ResizeObserver === "function") {
      this._resizeObserver = new ResizeObserver(() => {
        this._onResize()
      })
      this._resizeObserver.observe(this._surface)
    }

    if (typeof MutationObserver === "function") {
      this._mutationObserver = new MutationObserver((records) => {
        this._onMutations(records)
      })
      this._mutationObserver.observe(this, {
        attributes: true, childList: true, characterData: true, subtree: true
      })
    }

    this._scheduleRender()

    /* Parts that were waiting for this controller can bind now. */
    this.emit(CONTROLLER_CONNECT_EVENT, {})
    return
  }

  onDisconnected() {
    if (this._resizeObserver !== null) {
      this._resizeObserver.disconnect()
      this._resizeObserver = null
    }
    if (this._mutationObserver !== null) {
      this._mutationObserver.disconnect()
      this._mutationObserver = null
    }
    /* A response that arrives after removal has nothing to paint. */
    this._renderSequence = this._renderSequence + 1
    this._sourceCache.abortPending()

    /*
     * Bound parts stop showing this chart. They stay registered, so a
     * re-inserted chart fills them again with its next render.
     */
    const parts = this._parts.slice()
    for (let index = 0; index < parts.length; index = index + 1) {
      if (typeof parts[index].applyModel === "function") {
        try {
          parts[index].applyModel(null, null)
        } catch (error) {
          console.warn("mj-chart: a chart part failed to clear", error)
        }
      }
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._surface === undefined || this._surface === null) {
      return
    }
    if (name === "type" || name === "orientation" || name === "src" ||
        name === "label" || name === "description") {
      this._scheduleRender()
    }
    return
  }

  /*
   * Host mutations the attribute callback does not see: a renderer option
   * attribute, the `id` parts bind by, and edits to the inline JSON script.
   */
  _onMutations(records) {
    let needsRender = false
    let idChanged = false

    for (let index = 0; index < records.length; index = index + 1) {
      const record = records[index]

      if (record.type === "attributes") {
        if (record.target !== this) {
          continue
        }
        const name = record.attributeName
        if (name === "id") {
          idChanged = true
        } else if (NON_RENDER_ATTRIBUTES.indexOf(name) < 0 && name.startsWith("aria-") === false) {
          needsRender = true
        }
        continue
      }

      /* childList / characterData: only the inline JSON script matters. */
      let node = record.target
      if (node.nodeType !== Node.ELEMENT_NODE) {
        node = node.parentNode
      }
      const inScript = node !== null && node !== this && node.localName === "script"
      if (inScript === true || record.target === this) {
        needsRender = true
      }
    }

    if (idChanged === true) {
      this.emit(CONTROLLER_CONNECT_EVENT, {})
    }
    if (needsRender === true) {
      this._scheduleRender()
    }
    return
  }

  _onResize() {
    /*
     * A message (loading, empty, data error) looks the same at any size,
     * and a render still waiting for its data measures when it paints.
     */
    if (this._sizeDependent === false) {
      return
    }
    const rect = this._surface.getBoundingClientRect()
    if (rect.width === this._lastWidth && rect.height === this._lastHeight) {
      return
    }
    this._scheduleRender()
    return
  }

  /* ----- data API ----- */

  get data() {
    return this._data
  }

  set data(value) {
    this._data = value
    this._genericTableCache = null
    if (this._surface !== undefined && this._surface !== null) {
      this._scheduleRender()
    }
    return
  }

  /* The normalized model -- chart parts pull this on connect. */
  get chartModel() {
    return this._model
  }

  /*
   * The context of the last render, delivered to chart parts with the
   * model: { type, width, height, orientation, label, colorScale,
   * colorFor, hiddenSeries, legend, table }. Null before the first render
   * and after a data failure.
   */
  get chartContext() {
    return this._context
  }

  /* The accessible table of the last render: { columns, rows, caption, ... }. */
  get chartTable() {
    return this._table
  }

  /* "idle" | "loading" | "ready" | "empty" | "error" | "deferred". */
  get chartState() {
    return this._state
  }

  /* The accessible name the chart currently carries. */
  get chartLabel() {
    return this._resolveLabel()
  }

  /* ----- series visibility ----- */

  /* Names of the hidden series (a copy). */
  get hiddenSeries() {
    return this._hiddenSeries.slice()
  }

  isSeriesHidden(name) {
    const hidden = this._hiddenSeries.indexOf(String(name)) >= 0
    return hidden
  }

  /*
   * Hide a series by name and re-render.
   *
   * :returns: True when the series was visible before.
   */
  hideSeries(name) {
    const changed = this._setSeriesHidden(String(name), true)
    return changed
  }

  /*
   * Show a hidden series again and re-render.
   *
   * :returns: True when the series was hidden before.
   */
  showSeries(name) {
    const changed = this._setSeriesHidden(String(name), false)
    return changed
  }

  /*
   * Flip a series between hidden and shown.
   *
   * :returns: True when the series is visible afterwards.
   */
  toggleSeries(name) {
    const key = String(name)
    const hide = this.isSeriesHidden(key) === false
    this._setSeriesHidden(key, hide)
    return hide === false
  }

  /* Show every series again. */
  showAllSeries() {
    const names = this._hiddenSeries.slice()
    for (let index = 0; index < names.length; index = index + 1) {
      this._setSeriesHidden(names[index], false)
    }
    return
  }

  _setSeriesHidden(name, hidden) {
    const position = this._hiddenSeries.indexOf(name)
    const isHidden = position >= 0
    if (isHidden === hidden) {
      return false
    }

    if (hidden === true) {
      this._hiddenSeries.push(name)
    } else {
      this._hiddenSeries.splice(position, 1)
    }

    let seriesIndex = -1
    const all = this._model !== null ? this._model.allSeries : []
    for (let index = 0; index < all.length; index = index + 1) {
      if (all[index].name === name) {
        seriesIndex = all[index].sourceIndex
        break
      }
    }

    this._renderChart()
    this.emit("mj-chart-series-toggle", {
      series: name,
      seriesIndex: seriesIndex,
      visible: hidden === false,
      hidden: hidden,
      hiddenSeries: this._hiddenSeries.slice()
    })
    return true
  }

  /* ----- coordinated parts ----- */

  registerPart(part) {
    const hadLegend = this.hasLegendPart()
    if (this._parts.indexOf(part) < 0) {
      this._parts.push(part)
    }
    if (this._model !== null) {
      this._deliver(part)
    }
    /* A title part may now supply the chart's accessible name. */
    this.refreshLabel()
    this._legendPartsChanged(hadLegend)
    return
  }

  unregisterPart(part) {
    const hadLegend = this.hasLegendPart()
    const index = this._parts.indexOf(part)
    if (index >= 0) {
      this._parts.splice(index, 1)
      this.refreshLabel()
      this._legendPartsChanged(hadLegend)
    }
    return
  }

  /*
   * Whether an <mj-chart-legend> is bound to this chart. Renderers that
   * draw an inline key of their own (radar, parallel, bullet, streamgraph)
   * leave it out then (ctx.hasLegendPart), so the series are not listed
   * twice.
   */
  hasLegendPart() {
    const found = this._parts.some((part) => part.localName === "mj-chart-legend")
    return found
  }

  /* Redraw when a legend part came or went: the inline key depends on it. */
  _legendPartsChanged(hadLegend) {
    if (hadLegend !== this.hasLegendPart() && this._model !== null) {
      this._scheduleRender()
    }
    return
  }

  /*
   * Re-read the chart's accessible name. A bound <mj-chart-title> calls
   * this when its text changes, and registering or unregistering a part
   * does too. When the name changed, the parts get the model again, so a
   * part showing the name (a data table's default caption) follows at
   * once instead of on the next render.
   */
  refreshLabel() {
    if (this._surface === undefined || this._surface === null) {
      return
    }
    const previousLabel = this._context !== null ? this._context.label : null
    this._applyLabel()
    if (this._table !== null) {
      this._renderTable(this._table)
    }
    if (this._model !== null && this._context !== null && this._context.label !== previousLabel) {
      this._broadcast()
    }
    return
  }

  _deliver(part) {
    if (typeof part.applyModel !== "function") {
      return
    }
    try {
      part.applyModel(this._model, this._context)
    } catch (error) {
      /* One failing part must not stop the chart or the other parts. */
      console.warn("mj-chart: a chart part failed to draw", error)
    }
    return
  }

  _broadcast() {
    const parts = this._parts.slice()
    for (let index = 0; index < parts.length; index = index + 1) {
      this._deliver(parts[index])
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

  /*
   * Render the chart from its current data source.
   *
   * Data held locally (the `data` property, inline JSON, a `src` payload
   * already fetched) is drawn before this method returns. A `src` that
   * still has to be fetched is drawn when the response arrives -- unless a
   * newer render has started meanwhile, in which case the stale result is
   * dropped, so renders always paint in the order they were requested.
   *
   * :returns: A Promise that settles once this render has painted or has
   *     been superseded. It never rejects.
   */
  _renderChart() {
    let finished = Promise.resolve()

    if (this._surface === undefined || this._surface === null || this.isConnected === false) {
      return finished
    }

    this._renderSequence = this._renderSequence + 1
    const sequence = this._renderSequence

    let source = null
    try {
      source = this._resolveSource()
    } catch (error) {
      this._setBusy(false)
      this._finishError(this._publicMessage(error), error.message, true)
      return finished
    }

    /* geojson / topology given as URLs are fetched before the renderer runs. */
    let pending = source.pending
    if (pending === null) {
      let references = null
      try {
        references = this._referenceCache.resolve(source.data)
      } catch (error) {
        this._setBusy(false)
        this._finishError(t("mj.chart.loadFailed"), error.message, true)
        return finished
      }
      if (references.pending === null) {
        this._setBusy(false)
        this._renderData(references.data)
        return finished
      }
      pending = references.pending
    } else {
      pending = pending.then((data) => {
        const references = this._referenceCache.resolve(data)
        const ready = references.pending === null ? references.data : references.pending
        return ready
      })
    }

    this._setBusy(true)
    finished = pending.then((data) => {
      if (sequence === this._renderSequence) {
        this._setBusy(false)
        this._renderData(data)
      }
    }, (error) => {
      if (sequence === this._renderSequence) {
        this._setBusy(false)
        this._finishError(t("mj.chart.loadFailed"), error.message, true)
      }
    })
    return finished
  }

  /*
   * Find the chart data: the `data` property, then `src`, then the inline
   * JSON script.
   *
   * :returns: { data, pending } -- `pending` is null when the data is
   *     available now, else a Promise for it.
   * :raises: Error for malformed inline JSON, a non-object `data` value,
   *     or a `src` that already failed.
   */
  _resolveSource() {
    const resolved = { data: null, pending: null }

    if (this._data !== null && this._data !== undefined) {
      this._sourceCache.abortPending()
      resolved.data = validateChartData(this._data)
      return resolved
    }

    const srcAttribute = this.getAttribute("src")
    const src = srcAttribute !== null ? srcAttribute.trim() : ""
    if (src.length > 0) {
      const failure = this._sourceCache.failure(src)
      if (failure !== null) {
        throw failure
      }
      if (this._sourceCache.has(src) === true) {
        resolved.data = validateChartData(this._sourceCache.get(src))
      } else {
        resolved.pending = this._sourceCache.load(src).then((payload) => {
          return validateChartData(payload)
        })
      }
      return resolved
    }

    this._sourceCache.abortPending()

    /* The inline script is parsed once per distinct text. */
    const text = readInlineText(this)
    if (text !== this._inlineText) {
      this._inlineData = null
      this._inlineText = text
      if (text !== null) {
        try {
          this._inlineData = validateChartData(parseInlineJson(text))
        } catch (error) {
          /* Parse again next time rather than reuse the failed result. */
          this._inlineText = null
          throw error
        }
      }
    }
    resolved.data = this._inlineData
    return resolved
  }

  /* The text shown in the chart for a data failure; details go to the event. */
  _publicMessage(error) {
    const fromSrc = this.getAttribute("src") !== null &&
      (this._data === null || this._data === undefined)
    const text = fromSrc === true ? t("mj.chart.loadFailed") : t("mj.chart.invalidData")
    return text
  }

  /*
   * Fetch `src` again (or re-read the inline JSON) and render.
   *
   * :returns: A Promise that settles when the chart has rendered.
   */
  reload() {
    this._sourceCache.clear()
    this._referenceCache.clear()
    this._inlineText = null
    this._inlineData = null
    this._genericTableCache = null
    const finished = this._renderChart()
    return finished
  }

  /*
   * Render now instead of on the next animation frame.
   *
   * With local data (`data` property or inline JSON) the chart is redrawn
   * before this returns; with a `src` still loading the returned Promise
   * settles when it has been drawn. Call it after changing the `data`
   * object in place: the table is rebuilt from the data as it is now.
   *
   * :returns: A Promise that settles once the render has painted.
   */
  redraw() {
    this._genericTableCache = null
    const finished = this._renderChart()
    return finished
  }

  _setBusy(busy) {
    if (busy === true) {
      this.setAttribute("aria-busy", "true")
      /* Keep a drawn chart on screen while its replacement loads. */
      if (this._surface.querySelector("svg") === null) {
        this._state = "loading"
        this._showMessage(t("core.loading"), "loading")
      }
    } else if (this.hasAttribute("aria-busy") === true) {
      this.removeAttribute("aria-busy")
    }
    return
  }

  /*
   * Build the model for `raw` and draw it. Everything here is synchronous,
   * so a render that reaches this point always completes.
   */
  _renderData(given) {
    const started = performance.now()
    const type = this.chartType
    const options = getRendererOptions(type)

    let raw = given
    try {
      raw = this.adaptChartData(given)
    } catch (error) {
      this._finishError(t("mj.chart.invalidData"), error.message, true)
      return
    }

    this._surface.style.setProperty("--mj-chart-default-height", `${options.minHeight}px`)

    /* New data: non-series colour keys are handed out afresh. */
    if (raw !== this._colorSource) {
      this._colorSource = raw
      this._colorSlots = new Map()
    }

    const model = buildModel(raw, { hiddenSeries: this._hiddenSeries })
    this._model = model
    this._applyLabel()

    const orientation = this.getAttribute("orientation") || model.meta.orientation ||
      options.orientation
    const colorFor = this._buildColorResolver(model)
    const colorScale = (key) => colorFor(String(key))
    colorScale.domain = () => model.allSeries.map((entry) => entry.name)
    colorScale.kind = "color"

    const rect = this._surface.getBoundingClientRect()
    this._lastWidth = rect.width
    this._lastHeight = rect.height
    const visible = rect.width > 0 && rect.height > 0
    const width = Math.max(rect.width, MIN_DRAW_SIZE)
    /*
     * A renderer that said its content needs more room than the surface
     * has (a host with a fixed height) is drawn that tall and scrolls.
     */
    const height = Math.max(rect.height, MIN_DRAW_SIZE, this._contentHeight)

    const context = {
      type: type,
      width: width,
      height: height,
      orientation: orientation,
      label: this._resolveLabel(),
      colorScale: colorScale,
      colorFor: colorFor,
      hiddenSeries: model.hiddenSeries.slice(),
      legend: [],
      table: null
    }
    this._context = context

    /* What the renderer publishes during this render. */
    const published = { table: null, legend: null, contentHeight: 0 }
    const ctx = {
      type: type,
      model: model,
      raw: model.raw,
      width: width,
      height: height,
      orientation: orientation,
      defaults: options,
      label: context.label,
      hasLegendPart: this.hasLegendPart(),
      attrs: (name, fallback) => this.readOption(name, fallback),
      colorFor: colorFor,
      emit: (eventName, detail) => {
        this.emit(eventName, detail)
      },
      setTable: (table) => {
        published.table = table
      },
      setLegend: (entries) => {
        published.legend = entries
      },
      setContentHeight: (pixels) => {
        const numeric = Number(pixels)
        if (Number.isFinite(numeric) === true && numeric > 0) {
          published.contentHeight = Math.min(Math.ceil(numeric), MAX_CONTENT_HEIGHT)
        }
      },
      valueDomain: null
    }

    const genericTable = this._genericTable(model)

    if (hasRenderer(type) === false) {
      this._sizeDependent = false
      context.legend = this._buildLegend(null, "series", ctx)
      this._table = genericTable
      context.table = this._table
      this._finishError(t("mj.chart.noRenderer", { type: type }), `Unknown chart type: ${type}`, false)
      return
    }

    let empty = model.isEmpty
    if (options.isEmpty !== null) {
      try {
        empty = options.isEmpty(model) === true
      } catch (error) {
        empty = model.isEmpty
      }
    }
    if (empty === true) {
      this._sizeDependent = false
      this._table = buildTableModel(null, null)
      context.table = this._table
      this._state = "empty"
      this._showMessage(t("mj.chart.empty"), "empty")
      this._renderTable(this._table)
      this._broadcast()
      this.emit("mj-chart-empty", { type: type })
      return
    }

    /* From here on the outcome depends on the box: redraw when it changes. */
    this._sizeDependent = true

    let root = null
    if (visible === true) {
      try {
        const drawn = getRenderer(type)(ctx)
        root = svgRoot(width, height)
        root.setAttribute("part", "svg")
        if (drawn !== null && drawn !== undefined) {
          root.appendChild(drawn)
        }
      } catch (error) {
        context.legend = this._buildLegend(null, "series", ctx)
        this._table = genericTable
        context.table = this._table
        this._finishError(t("mj.chart.renderError", { message: error.message }), error.message, false)
        return
      }
    }

    context.legend = this._buildLegend(published.legend, options.legend, ctx)
    this._table = genericTable
    const supplied = this._suppliedTable(published.table, options, ctx)
    if (supplied !== null) {
      const custom = buildTableModel(null, supplied)
      if (custom.columns.length > 0) {
        this._table = custom
      }
    }
    context.table = this._table

    if (root !== null) {
      if (height > rect.height + 1) {
        root.setAttribute("data-overflow", "")
        root.setAttribute("height", String(height))
      }
      this._showDrawing(root)
      this._state = "ready"
      this._applyContentHeight(published.contentHeight)
    } else {
      /* A 0 x 0 box (display: none, a closed tab): draw when it gets a size. */
      this._state = "deferred"
    }

    this._renderTable(this._table)
    this._broadcast()

    if (root !== null) {
      this.emit("mj-chart-render", { type: type, duration: performance.now() - started })
    }
    return
  }

  /*
   * Record the block size the renderer asked for. The surface grows to it
   * when the host's height is free (CSS flex basis), and the next render
   * draws at that size; with a fixed host height the drawing scrolls. Only
   * a changed request schedules a new render, so the size settles.
   */
  _applyContentHeight(requested) {
    const next = requested > 0 ? requested : 0
    if (Math.abs(next - this._contentHeight) <= 1) {
      return
    }
    this._contentHeight = next
    if (next > 0) {
      this._surface.style.setProperty("--mj-chart-content-height", `${next}px`)
    } else {
      this._surface.style.removeProperty("--mj-chart-content-height")
    }
    this._scheduleRender()
    return
  }

  /*
   * The generic accessible table of a model, cached per data object and
   * set of hidden series (see _genericTableCache).
   */
  _genericTable(model) {
    const hiddenKey = model.hiddenSeries.join("\u0000")
    const cache = this._genericTableCache
    if (cache !== null && cache.source === model.source && cache.hiddenKey === hiddenKey) {
      return cache.table
    }

    const table = buildTableModel(model, null)
    this._genericTableCache = { source: model.source, hiddenKey: hiddenKey, table: table }
    return table
  }

  /*
   * Read a renderer option from the host (ctx.attrs). `style` is a global
   * attribute holding inline CSS, so the option renderers call "style"
   * lives in the `variant` attribute and never returns the host's CSS
   * text. A subclass may override this to map its own attribute names.
   */
  readOption(name, fallback) {
    let value = null

    if (name === "style") {
      value = this.getAttribute("variant")
      /*
       * Compatibility: a bare word in `style` (style="roadmap") was the old
       * way to pick a variant. Inline CSS always holds a ":" and is never
       * returned as an option.
       */
      const legacy = this.getAttribute("style")
      if (value === null && legacy !== null && legacy.indexOf(":") < 0 &&
          legacy.trim().length > 0) {
        value = legacy.trim()
      }
    } else {
      value = this.getAttribute(name)
    }

    const result = value !== null ? value : fallback
    return result
  }

  /*
   * Build ctx.colorFor for one render.
   *
   * A series keeps the palette slot of its position in the data (or its
   * own `color`), whether it is asked for by name or by index and whether
   * or not other series are hidden. Any other integer index and any other
   * string key gets a slot of its own, so slices, nodes and categories are
   * told apart; string keys keep their slot for as long as the data lives.
   */
  _buildColorResolver(model) {
    const allSeries = model.allSeries
    const visibleSeries = model.series
    const hiddenCount = allSeries.length - visibleSeries.length
    const keySlots = this._colorSlots

    const colorOfSeries = (entry) => {
      const color = entry.color !== null ? entry.color : seriesColor(entry.sourceIndex)
      return color
    }

    const seriesByName = new Map()
    for (let index = 0; index < allSeries.length; index = index + 1) {
      if (seriesByName.has(allSeries[index].name) === false) {
        seriesByName.set(allSeries[index].name, allSeries[index])
      }
    }

    const colorOfKey = (key) => {
      const entry = seriesByName.get(key)
      if (entry !== undefined) {
        return colorOfSeries(entry)
      }
      let slot = keySlots.get(key)
      if (slot === undefined) {
        slot = allSeries.length + keySlots.size
        keySlots.set(key, slot)
      }
      return seriesColor(slot)
    }

    const colorOfIndex = (index) => {
      if (index < visibleSeries.length) {
        return colorOfSeries(visibleSeries[index])
      }
      /* Past the series: skip the slots the hidden series still own. */
      return seriesColor(index + hiddenCount)
    }

    const colorFor = (keyOrIndex) => {
      let color = null
      if (keyOrIndex === null || keyOrIndex === undefined) {
        color = colorOfIndex(0)
      } else if (typeof keyOrIndex === "number" && Number.isInteger(keyOrIndex) === true &&
          keyOrIndex >= 0) {
        color = colorOfIndex(keyOrIndex)
      } else {
        color = colorOfKey(String(keyOrIndex))
      }
      return color
    }
    return colorFor
  }

  /*
   * The legend entries of this render: what the renderer published, else
   * what its registration declares, else one entry per series.
   *
   * :returns: [{ key, label, color, series, hidden }] -- `series` is the
   *     name of the series the entry toggles, or null for an entry that
   *     only explains a colour.
   */
  _buildLegend(publishedEntries, declared, ctx) {
    const model = ctx.model
    let source = null

    try {
      if (Array.isArray(publishedEntries) === true) {
        source = publishedEntries
      } else if (typeof declared === "function") {
        const built = declared(ctx)
        source = Array.isArray(built) === true ? built : null
      } else if (declared === "categories") {
        source = model.categories.map((category, index) => {
          return { label: category, color: ctx.colorFor(index) }
        })
      } else if (declared === "none") {
        source = []
      }
    } catch (error) {
      console.warn("mj-chart: the legend for this chart type could not be built", error)
      source = null
    }

    if (source === null) {
      source = model.allSeries.map((entry) => {
        return { label: entry.name, series: entry.name }
      })
    }

    const entries = []
    for (let index = 0; index < source.length; index = index + 1) {
      const item = source[index]
      if (item === null || item === undefined || typeof item !== "object") {
        continue
      }
      const series = item.series !== null && item.series !== undefined ? String(item.series) : null
      const labelSource = item.label !== null && item.label !== undefined ? item.label : series
      const label = labelSource !== null ? String(labelSource) : ""
      let color = typeof item.color === "string" && item.color.length > 0 ? item.color : null
      if (color === null) {
        color = ctx.colorFor(series !== null ? series : label)
      }
      entries.push({
        key: `${index}:${label}`,
        label: label,
        color: color,
        series: series,
        hidden: series !== null && this._hiddenSeries.indexOf(series) >= 0
      })
    }
    return entries
  }

  /*
   * The table the renderer supplied for this render: ctx.setTable first,
   * then the type's registered table function. A failure here falls back
   * to the generic table; it never aborts the render.
   */
  _suppliedTable(publishedTable, options, ctx) {
    let supplied = publishedTable !== null && publishedTable !== undefined ? publishedTable : null

    if (supplied === null && options.table !== null) {
      try {
        const built = options.table(ctx)
        supplied = built !== null && built !== undefined ? built : null
      } catch (error) {
        console.warn("mj-chart: the table for this chart type could not be built", error)
        supplied = null
      }
    }
    return supplied
  }

  /*
   * Finish a render that could not draw.
   *
   * :param text: The message shown in place of the drawing.
   * :param detail: The message carried by the mj-chart-error event.
   * :param dataLost: True when the data itself failed (fetch / parse): the
   *     model, context and table are dropped so parts do not keep showing
   *     the previous chart. False when the data is fine but could not be
   *     drawn (unknown type, renderer exception): parts keep the model.
   */
  _finishError(text, detail, dataLost) {
    if (dataLost === true) {
      this._model = null
      this._context = null
      this._table = buildTableModel(null, null)
      this._sizeDependent = false
    }
    this._state = "error"
    this._showMessage(text, "error")
    this._renderTable(this._table)
    this._broadcast()
    this.emit("mj-chart-error", { message: detail })
    return
  }

  _showMessage(text, kind) {
    const key = `${kind}:${text}`
    if (this._messageText === key) {
      return
    }
    const div = document.createElement("div")
    div.className = "message"
    div.setAttribute("part", `message ${kind}`)
    if (kind === "empty") {
      /* The page may put its own text in the `empty` slot. */
      const slot = document.createElement("slot")
      slot.setAttribute("name", "empty")
      slot.textContent = text
      div.appendChild(slot)
    } else {
      div.textContent = text
    }
    this._surface.replaceChildren(div)
    this._surface.dataset.state = kind
    this._messageText = key
    this._marks = []
    return
  }

  /*
   * Put a new drawing on the surface, keeping keyboard focus on the mark
   * that had it (by position) when the previous drawing is replaced.
   */
  _showDrawing(root) {
    const focused = this.shadowRoot.activeElement
    const focusedIndex = focused !== null ? this._marks.indexOf(focused) : -1

    this._surface.replaceChildren(root)
    this._surface.dataset.state = "ready"
    this._messageText = null

    const candidates = root.querySelectorAll("[tabindex]")
    const marks = []
    for (let index = 0; index < candidates.length; index = index + 1) {
      if (candidates[index].getAttribute("tabindex") !== "-1") {
        marks.push(candidates[index])
      }
    }
    this._marks = marks

    if (focusedIndex >= 0) {
      this._activeMark = focusedIndex
    }
    if (this._activeMark >= marks.length) {
      this._activeMark = Math.max(marks.length - 1, 0)
    }
    this._applyRovingTabindex()

    if (focusedIndex >= 0 && marks.length > 0) {
      marks[this._activeMark].focus({ preventScroll: true })
    }
    return
  }

  /* ----- keyboard: the marks are one tab stop, arrows move between them ----- */

  _applyRovingTabindex() {
    for (let index = 0; index < this._marks.length; index = index + 1) {
      this._marks[index].setAttribute("tabindex", index === this._activeMark ? "0" : "-1")
    }
    return
  }

  _onSurfaceFocusIn(event) {
    const index = this._marks.indexOf(event.target)
    if (index >= 0 && index !== this._activeMark) {
      this._activeMark = index
      this._applyRovingTabindex()
    }
    return
  }

  _onSurfaceKeydown(event) {
    /* A renderer that handles the key itself has already claimed it. */
    if (event.defaultPrevented === true) {
      return
    }
    const index = this._marks.indexOf(event.target)
    if (index < 0) {
      return
    }

    let next = index
    let handled = true
    if (event.key === "ArrowRight" || event.key === "ArrowDown") {
      next = Math.min(index + 1, this._marks.length - 1)
    } else if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
      next = Math.max(index - 1, 0)
    } else if (event.key === "Home") {
      next = 0
    } else if (event.key === "End") {
      next = this._marks.length - 1
    } else {
      handled = false
    }

    if (handled === true) {
      event.preventDefault()
      if (next !== index) {
        this._activeMark = next
        this._applyRovingTabindex()
        this._marks[next].focus()
      }
    }
    return
  }

  /* ----- accessible name, description and table ----- */

  /*
   * The chart's accessible name: an aria-label the page wrote, the `label`
   * attribute, the `title` attribute, a bound title part, meta.title, and
   * finally the chart type.
   */
  _resolveLabel() {
    const authored = this.getAttribute("aria-label")
    if (authored !== null && authored !== this._appliedLabel && authored.trim().length > 0) {
      return authored.trim()
    }

    const candidates = [this.getAttribute("label"), this.getAttribute("title")]
    for (let index = 0; index < this._parts.length; index = index + 1) {
      const part = this._parts[index]
      if (typeof part.chartLabel === "string") {
        candidates.push(part.chartLabel)
      }
    }
    if (this._model !== null && this._model.meta.title !== undefined &&
        this._model.meta.title !== null) {
      candidates.push(String(this._model.meta.title))
    }

    for (let index = 0; index < candidates.length; index = index + 1) {
      const candidate = candidates[index]
      if (candidate !== null && candidate !== undefined && candidate.trim().length > 0) {
        return candidate.trim()
      }
    }

    const label = this.defaultChartLabel
    return label
  }

  /* ----- subclass hooks (see the file header) ----- */

  /* The chart type key this element draws. */
  get chartType() {
    const type = this.getAttribute("type") || "bar"
    return type
  }

  /* The accessible name of a chart the page did not name: "<type> chart" (mj.chart.figureLabel). */
  get defaultChartLabel() {
    const type = this.chartType.split("-").join(" ")
    const label = type.endsWith("chart") === true ? type : t("mj.chart.figureLabel", { type: type })
    return label
  }

  /*
   * The data the renderer reads, built from the data the page supplied
   * (`data`, `src` or inline JSON, already checked to be an object or
   * null). Must return the same object for the same input.
   */
  adaptChartData(data) {
    return data
  }

  _applyLabel() {
    const label = this._resolveLabel()

    /* The page's own aria-label / aria-labelledby is never overwritten. */
    const authored = this.getAttribute("aria-label")
    const authorOwned = this.hasAttribute("aria-labelledby") === true ||
      (authored !== null && authored !== this._appliedLabel)
    if (authorOwned === false && authored !== label) {
      this._appliedLabel = label
      this.setAttribute("aria-label", label)
    }

    let description = this.getAttribute("description")
    if (description === null && this._model !== null &&
        typeof this._model.meta.description === "string") {
      description = this._model.meta.description
    }
    const text = description !== null ? description.trim() : ""
    if (this._descriptionEl.textContent !== text) {
      this._descriptionEl.textContent = text
    }
    this._descriptionEl.hidden = text.length === 0

    if (this._context !== null) {
      this._context.label = label
    }
    return
  }

  /*
   * Write the visually hidden data table. The DOM is rebuilt only when the
   * table or its caption changed, so a resize re-render leaves it alone.
   */
  _renderTable(table) {
    const caption = table.caption !== null ? table.caption : this._resolveLabel()
    const signature = `${caption}|${tableSignature(table)}`
    if (signature === this._tableSignature) {
      return
    }
    this._tableSignature = signature

    if (table.columns.length === 0) {
      this._tableHost.replaceChildren()
      return
    }

    const element = buildTableElement(
      table,
      caption.length > 0 ? caption : t("mj.chart.tableCaption"),
      t("mj.chart.tableTruncated", { count: table.rows.length })
    )
    this._tableHost.replaceChildren(element)
    return
  }
}
