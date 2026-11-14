/*
 * mjmap.js
 *
 * <mj-map> -- accessible geographic map wrapper with pluggable provider adapter,
 * keyboard pan/zoom, accessible marker list fallback, and popup panel.
 * No tile engine is bundled; the adapter is supplied by the host application.
 * Without an adapter a built-in SVG plot of the markers is drawn.
 *
 * Layout: the host is the sizing box (block-size from --mj-map-height, 400px
 * by default, or any height set on the element). Inside it the map area
 * takes the remaining space and clips the map; the marker list sits BELOW
 * the map area when `show-list` is set, so it is never clipped.
 *
 * Adapter contract
 *   Required: init(target, options), destroy(), panTo(lat, lng),
 *             setZoom(level), addMarker(marker) -> handle, removeMarker(handle)
 *   Optional: resize(), panBy(dx, dy), getCenter() -> { lat, lng },
 *             setMapType(type), setInteractive(flag),
 *             on(eventName, handler) with the events
 *               "move"        handler({ lat, lng, zoom? })   after a pan / drag
 *               "zoom"        handler(zoomLevel)             after a zoom
 *               "markerClick" handler(markerOrId)            a marker was activated
 *   init options: { lat, lng, zoom, minZoom, maxZoom, mapType, interactive,
 *                   ...adapterOptions }
 *   When `setMapType` / `setInteractive` are missing the adapter is destroyed
 *   and initialised again with the new options.
 *
 * State that survives a reconnect lives in fields (markers, selected marker,
 * adapter); `afterRender` rebuilds the shadow DOM from them.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { t } from "../core/intl.js";
import { escapeHtml, safeUrl } from "../core/html.js";

const SVG_NS = "http://www.w3.org/2000/svg";
const DEFAULT_ZOOM = 10;
const PAN_STEP_PX = 50;
const EVENT_DEBOUNCE_MS = 200;

const STYLES = `
:host {
  display: block;
  block-size: var(--mj-map-height, 400px);
}

.container {
  position: relative;
  display: flex;
  flex-direction: column;
  block-size: 100%;
  border-radius: var(--mj-map-radius, var(--mj-radius-md));
  overflow: hidden;
  background: var(--mj-bg-muted);
}

.map-area {
  position: relative;
  flex: 1 1 auto;
  min-block-size: 0;
  overflow: hidden;
}

.svg-map {
  inline-size: 100%;
  block-size: 100%;
  display: block;
  overflow: hidden;
}
.svg-map-background { fill: var(--mj-map-surface, var(--mj-bg-subtle)); }
.svg-map-grid {
  stroke: var(--mj-border);
  stroke-opacity: 0.6;
  stroke-width: 1;
}
.svg-map-marker {
  cursor: pointer;
}
.svg-map-marker circle {
  fill: var(--mj-accent);
  fill-opacity: 0.85;
  stroke: var(--mj-surface);
  stroke-width: 2;
}
.svg-map-marker text {
  font-size: 11px;
  font-family: var(--mj-font-sans);
  fill: var(--mj-text);
  stroke: var(--mj-surface);
  stroke-width: 3;
  paint-order: stroke;
}
.svg-map-marker:focus {
  outline: none;
}
.svg-map-marker:focus-visible circle {
  stroke-width: 3;
  stroke: var(--mj-focus-ring);
}
/* Selection is shown by a ring and a heavier label, not by colour alone. */
.svg-map-marker.selected circle {
  stroke: var(--mj-text);
  stroke-width: 3;
  fill-opacity: 1;
}
.svg-map-marker.selected text { font-weight: var(--mj-font-weight-bold); }

.map-target {
  inline-size: 100%;
  block-size: 100%;
  display: block;
  outline: none;
}
.map-target:focus-visible {
  box-shadow: inset 0 0 0 var(--mj-focus-ring-width) var(--mj-map-focus-ring, var(--mj-focus-ring));
}

.controls {
  position: absolute;
  inset-block-start: var(--mj-space-3);
  inset-inline-end: var(--mj-space-3);
  display: flex;
  flex-direction: column;
  gap: var(--mj-space-1);
  background: var(--mj-map-controls-bg, var(--mj-surface));
  border-radius: var(--mj-map-controls-radius, var(--mj-radius-sm));
  box-shadow: var(--mj-map-controls-shadow, var(--mj-elevation-2));
  padding: var(--mj-space-1);
  z-index: 10;
}

.ctrl-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  inline-size: 2rem;
  block-size: 2rem;
  background: transparent;
  border: none;
  border-radius: var(--mj-radius-sm);
  cursor: pointer;
  font-size: var(--mj-font-size-lg);
  font-weight: var(--mj-font-weight-bold);
  color: var(--mj-text);
  line-height: 1;
}
.ctrl-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}
.ctrl-btn[aria-disabled="true"] { opacity: 0.4; cursor: not-allowed; }

.marker-list {
  position: absolute;
  inline-size: 1px;
  block-size: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  clip-path: inset(50%);
  white-space: nowrap;
  margin: -1px;
  padding: 0;
  list-style: none;
}
/*
 * A hidden list is revealed while one of its links has keyboard focus, so
 * focus never lands on something that cannot be seen.
 */
.marker-list:not(.visible):focus-within {
  inset-block-end: var(--mj-space-3);
  inset-inline-start: var(--mj-space-3);
  inline-size: auto;
  block-size: auto;
  max-block-size: 60%;
  overflow-y: auto;
  clip: auto;
  clip-path: none;
  white-space: normal;
  margin: 0;
  padding: var(--mj-space-3);
  background: var(--mj-surface);
  border-radius: var(--mj-radius-md);
  box-shadow: var(--mj-elevation-3);
  z-index: 30;
}
.marker-list.visible {
  position: static;
  flex: 0 1 auto;
  inline-size: auto;
  block-size: auto;
  max-block-size: 45%;
  overflow-y: auto;
  clip: auto;
  clip-path: none;
  white-space: normal;
  margin: 0;
  padding: var(--mj-space-3);
  background: var(--mj-surface);
  border-block-start: 1px solid var(--mj-border);
}
.marker-list li { padding: var(--mj-space-1) 0; }
.marker-list a {
  color: var(--mj-accent);
  text-decoration: none;
  font-size: var(--mj-font-size-sm);
}
.marker-list a:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}
.marker-desc {
  position: absolute;
  inline-size: 1px;
  block-size: 1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
}

.popup {
  position: absolute;
  inset-block-start: var(--mj-space-3);
  inset-inline-start: var(--mj-space-3);
  inline-size: var(--mj-map-popup-width, 16rem);
  max-inline-size: calc(100% - 2 * var(--mj-space-3));
  box-sizing: border-box;
  background: var(--mj-map-popup-bg, var(--mj-surface));
  color: var(--mj-text);
  border-radius: var(--mj-radius-md);
  box-shadow: var(--mj-elevation-3);
  padding: var(--mj-space-3);
  z-index: 20;
  display: none;
}
.popup.open { display: block; }
.popup-title {
  font-weight: var(--mj-font-weight-medium);
  margin: 0 0 var(--mj-space-1);
  padding-inline-end: var(--mj-space-5);
}
.popup-desc { font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); margin: 0; }
.popup-close {
  position: absolute;
  inset-block-start: var(--mj-space-2);
  inset-inline-end: var(--mj-space-2);
  background: none;
  border: none;
  cursor: pointer;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text-muted);
  padding: var(--mj-space-1);
  border-radius: var(--mj-radius-sm);
}
.popup-close:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}

.loading {
  position: absolute;
  inset: 0;
  display: none;
  align-items: center;
  justify-content: center;
  background: var(--mj-bg-muted);
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text-muted);
  z-index: 40;
}
.loading.visible { display: flex; }

.error {
  position: absolute;
  inset: 0;
  display: none;
  align-items: center;
  justify-content: center;
  padding: var(--mj-space-4);
  background: var(--mj-bg-muted);
  color: var(--mj-color-danger);
  text-align: center;
  z-index: 40;
}
.error.visible { display: flex; }

.no-adapter {
  display: flex;
  align-items: center;
  justify-content: center;
  block-size: 100%;
  padding: var(--mj-space-4);
  box-sizing: border-box;
  text-align: center;
  color: var(--mj-text-muted);
  font-size: var(--mj-font-size-sm);
}

.live {
  position: absolute;
  inline-size: 1px; block-size: 1px;
  overflow: hidden; clip: rect(0 0 0 0); clip-path: inset(50%);
}
`;

function createSvg(name, attributes) {
  const element = document.createElementNS(SVG_NS, name)
  const names = Object.keys(attributes || {})
  for (let index = 0; index < names.length; index = index + 1) {
    element.setAttribute(names[index], String(attributes[names[index]]))
  }
  return element
}

export class MjMap extends MjElement {
  static tagName = "mj-map";
  static styles = STYLES;
  static watched = ["lat", "lng", "zoom", "min-zoom", "max-zoom",
    "map-type", "interactive", "show-list", "label", "loading"];

  constructor() {
    super()
    this._adapter = null
    this._adapterOptions = {}

    /* True while `_adapter` has been initialised into the current map target. */
    this._adapterReady = false

    /* Incremented on every adapter init; events of an earlier init are ignored. */
    this._adapterGeneration = 0

    /* True when the adapter reports pans through on("move"). */
    this._adapterReportsMoves = false

    this._markers = []
    this._selectedMarkerId = null
    this._markerHandles = new Map()

    /* What opened the popup ("svg" or "list"), so focus can go back there. */
    this._popupInvoker = null

    /* Centre and zoom as last reported by the adapter; null until it reports. */
    this._viewCenter = null
    this._viewZoom = null

    this._zoomDebounce = null
    this._moveDebounce = null
    this._resizeObserver = null

    this._sectionEl = null
    this._mapTargetEl = null
    this._popupEl = null
    this._markerListEl = null
    this._zoomInBtn = null
    this._zoomOutBtn = null
    this._loadingEl = null
    this._errorEl = null
    this._liveEl = null
    this._svgEl = null
    this._svgMarkersGroup = null
  }

  render() {
    const markup = `
      <section role="application" aria-label="" part="container" class="container">
        <div class="map-area" part="map-area">
          <div class="map-target" part="map-target" role="group" tabindex="0" aria-label="${escapeHtml(t("mj.map.label"))}"></div>
          <div class="controls" part="controls">
            <button type="button" class="ctrl-btn" part="zoom-in" aria-label="${escapeHtml(t("mj.map.zoomIn"))}">+</button>
            <button type="button" class="ctrl-btn" part="zoom-out" aria-label="${escapeHtml(t("mj.map.zoomOut"))}">−</button>
            <slot name="controls"></slot>
          </div>
          <div class="popup" part="popup" role="dialog" aria-label="" aria-modal="false">
            <button type="button" class="popup-close" aria-label="${escapeHtml(t("mj.map.closePopup"))}">✕</button>
            <p class="popup-title"></p>
            <p class="popup-desc"></p>
            <slot name="popup"></slot>
          </div>
          <div class="loading" part="loading" aria-live="polite">${escapeHtml(t("mj.map.loading"))}</div>
          <div class="error" part="error" role="alert" hidden></div>
        </div>
        <ul class="marker-list" part="marker-list"></ul>
        <div class="live" role="status" aria-live="polite" aria-atomic="true"></div>
      </section>
    `
    return markup
  }

  afterRender() {
    this._sectionEl = this.$("section")
    this._mapTargetEl = this.$(".map-target")
    this._popupEl = this.$(".popup")
    this._markerListEl = this.$(".marker-list")
    this._zoomInBtn = this.$("[part='zoom-in']")
    this._zoomOutBtn = this.$("[part='zoom-out']")
    this._loadingEl = this.$(".loading")
    this._errorEl = this.$(".error")
    this._liveEl = this.$(".live")

    this._svgEl = null
    this._svgMarkersGroup = null

    this._applyAttrs()
    this._wireControls()
    this._setupResize()
    this._initAdapter()

    /* A marker that was selected before a reconnect is shown again. */
    const selected = this._findMarkerById(this._selectedMarkerId)
    if (selected !== null) {
      this._showPopup(selected)
    } else {
      this._selectedMarkerId = null
    }
    return
  }

  /* ----- attributes ----- */

  _number(name, fallback) {
    const parsed = parseFloat(this.getAttribute(name) || "")
    const value = Number.isFinite(parsed) === true ? parsed : fallback
    return value
  }

  _minZoom() {
    const value = this._number("min-zoom", 1)
    return value
  }

  _maxZoom() {
    const value = this._number("max-zoom", 20)
    return value
  }

  _zoom() {
    const requested = this._number("zoom", DEFAULT_ZOOM)
    const clamped = Math.max(this._minZoom(), Math.min(this._maxZoom(), requested))
    return clamped
  }

  _isInteractive() {
    const interactive = this.getAttribute("interactive") !== "false"
    return interactive
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._sectionEl === null || this._sectionEl === undefined) { return }

    if (name === "label") {
      this._applyLabel()
    } else if (name === "show-list") {
      this._applyListVisibility()
    } else if (name === "loading") {
      this._applyLoading()
    } else if (name === "zoom" || name === "min-zoom" || name === "max-zoom") {
      this._applyZoom()
    } else if (name === "lat" || name === "lng") {
      if (this._adapterReady === true && oldValue !== newValue) {
        const lat = this._number("lat", 0)
        const lng = this._number("lng", 0)
        this._viewCenter = { lat: lat, lng: lng }
        this._adapter.panTo(lat, lng)
      }
    } else if (name === "map-type") {
      if (this._adapterReady === true && oldValue !== newValue) {
        if (typeof this._adapter.setMapType === "function") {
          this._adapter.setMapType(newValue || "road")
        } else {
          this._initAdapter()
        }
      }
    } else if (name === "interactive") {
      this._updateZoomButtons()
      if (this._adapterReady === true && oldValue !== newValue) {
        if (typeof this._adapter.setInteractive === "function") {
          this._adapter.setInteractive(this._isInteractive())
        } else {
          this._initAdapter()
        }
      }
    }
    return
  }

  _applyAttrs() {
    this._applyLabel()
    this._applyListVisibility()
    this._applyLoading()
    this._updateZoomButtons()
    return
  }

  _applyLabel() {
    const label = this.getAttribute("label") || ""
    this._sectionEl.setAttribute("aria-label", label)
    if (label.length === 0) {
      console.warn("<mj-map>: `label` attribute is required for accessibility.")
    }
    return
  }

  _applyListVisibility() {
    const showList = this.hasAttribute("show-list")
    this._markerListEl.classList.toggle("visible", showList)
    this._syncListTabStops()
    return
  }

  _applyLoading() {
    const loading = this.hasAttribute("loading") === true && this.getAttribute("loading") !== "false"
    this._loadingEl.classList.toggle("visible", loading)
    if (loading === true) {
      this._sectionEl.setAttribute("aria-busy", "true")
    } else {
      this._sectionEl.removeAttribute("aria-busy")
    }
    return
  }

  /* The `zoom` attribute (or its limits) changed: apply it without events. */
  _applyZoom() {
    const zoom = this._zoom()
    if (this._adapterReady === true) {
      if (this._viewZoom !== zoom) {
        this._adapter.setZoom(zoom)
      }
    } else {
      this._applySvgZoom()
    }
    this._viewZoom = zoom
    this._updateZoomButtons()
    return
  }

  /* ----- wiring ----- */

  _wireControls() {
    this.listen(this._zoomInBtn, "click", () => this._zoomBy(1))
    this.listen(this._zoomOutBtn, "click", () => this._zoomBy(-1))
    this.listen(this._mapTargetEl, "keydown", (event) => this._onMapKeyDown(event))

    /* One delegated pair for the built-in SVG markers, however often it is redrawn. */
    this.listen(this._mapTargetEl, "click", (event) => {
      const marker = this._markerFromEvent(event)
      if (marker !== null) {
        this._selectMarker(marker, "svg")
      }
    })

    /* One delegated listener for the marker list links. */
    this.listen(this._markerListEl, "click", (event) => {
      const link = event.target instanceof Element ? event.target.closest("a[data-marker-index]") : null
      if (link !== null) {
        event.preventDefault()
        const index = parseInt(link.getAttribute("data-marker-index"), 10)
        const marker = this._markers[index]
        if (marker !== undefined) {
          this._selectMarker(marker, "list")
        }
      }
    })

    /* Escape closes the popup wherever focus is inside the map, the popup included. */
    this.listen(this._sectionEl, "keydown", (event) => {
      if (event.key === "Escape" && this._popupEl.classList.contains("open") === true) {
        event.preventDefault()
        event.stopPropagation()
        this._closePopup()
      }
    })

    const closeBtn = this.$(".popup-close")
    this.listen(closeBtn, "click", () => this._closePopup())

    this.onTeardown(() => {
      clearTimeout(this._zoomDebounce)
      clearTimeout(this._moveDebounce)
      this._zoomDebounce = null
      this._moveDebounce = null
    })
    return
  }

  /* The marker whose built-in SVG node the event came from, or null. */
  _markerFromEvent(event) {
    const node = event.target instanceof Element ? event.target.closest(".svg-map-marker") : null
    let marker = null
    if (node !== null) {
      const index = parseInt(node.getAttribute("data-marker-index"), 10)
      if (this._markers[index] !== undefined) {
        marker = this._markers[index]
      }
    }
    return marker
  }

  _setupResize() {
    const observer = new ResizeObserver(() => {
      const width = this._mapTargetEl.clientWidth
      const height = this._mapTargetEl.clientHeight
      if (width === 0 || height === 0) {
        return
      }
      if (this._adapterReady === true) {
        if (typeof this._adapter.resize === "function") {
          this._adapter.resize()
        }
      } else if (this._adapter === null) {
        /* Re-render the built-in SVG map so it fills the new size. */
        this._renderSvgMap()
      }
    })
    observer.observe(this._mapTargetEl)
    this._resizeObserver = observer
    this.onTeardown(() => {
      observer.disconnect()
      if (this._resizeObserver === observer) {
        this._resizeObserver = null
      }
    })
    return
  }

  /* ----- adapter ----- */

  _destroyAdapter(adapter) {
    if (adapter !== null && this._adapterReady === true) {
      this._markerHandles.clear()
      if (typeof adapter.destroy === "function") {
        try {
          adapter.destroy()
        } catch (error) {
          console.warn("<mj-map>: adapter.destroy() failed.", error)
        }
      }
    }
    this._adapterReady = false
    this._adapterReportsMoves = false
    return
  }

  /*
   * (Re)initialise the map target for the current adapter -- or the built-in
   * SVG plot when there is none -- and apply the stored markers to it.
   */
  _initAdapter() {
    this._destroyAdapter(this._adapter)

    /* Whatever drew into the target before (fallback SVG, old adapter) goes. */
    this._mapTargetEl.textContent = ""
    this._svgEl = null
    this._svgMarkersGroup = null
    this._clearError()

    if (this._adapter === null) {
      this._applyMarkers()
      return
    }

    const zoom = this._zoom()
    const options = {
      lat: this._number("lat", 0),
      lng: this._number("lng", 0),
      zoom: zoom,
      minZoom: this._minZoom(),
      maxZoom: this._maxZoom(),
      mapType: this.getAttribute("map-type") || "road",
      interactive: this._isInteractive(),
      ...this._adapterOptions
    }

    try {
      this._adapter.init(this._mapTargetEl, options)
      this._adapterReady = true
      this._viewCenter = { lat: options.lat, lng: options.lng }
      this._viewZoom = zoom
      this._subscribeToAdapter()
      this._applyMarkers()
      this._updateZoomButtons()
      this.emit("mj-map-ready", {})
    } catch (error) {
      this._adapterReady = false
      this._showError(error !== null && error !== undefined && error.message ? error.message : String(error))
      this._buildMarkerList()
    }
    return
  }

  /* Translate adapter-reported interactions into component state and events. */
  _subscribeToAdapter() {
    const adapter = this._adapter
    if (typeof adapter.on !== "function") {
      return
    }

    /* Events from an earlier init, or from a replaced adapter, are ignored. */
    this._adapterGeneration = this._adapterGeneration + 1
    const generation = this._adapterGeneration
    const current = () => this._adapter === adapter && this._adapterReady === true &&
      this._adapterGeneration === generation

    this._adapterReportsMoves = true
    adapter.on("move", (position) => {
      if (current() === true && position !== null && position !== undefined) {
        this._onAdapterMove(position)
      }
    })
    adapter.on("zoom", (zoom) => {
      if (current() === true) {
        this._onAdapterZoom(Number(zoom))
      }
    })
    adapter.on("markerClick", (markerOrId) => {
      if (current() === true) {
        const id = markerOrId !== null && typeof markerOrId === "object" ? markerOrId.id : markerOrId
        const marker = this._findMarkerById(id)
        if (marker !== null) {
          this._selectMarker(marker, "adapter")
        }
      }
    })
    return
  }

  _onAdapterMove(position) {
    const lat = Number(position.lat)
    const lng = Number(position.lng)
    if (Number.isFinite(lat) === true && Number.isFinite(lng) === true) {
      this._viewCenter = { lat: lat, lng: lng }
    }
    const zoom = Number(position.zoom)
    if (Number.isFinite(zoom) === true) {
      this._viewZoom = zoom
      this._updateZoomButtons()
    }
    this._emitMoveSoon()
    return
  }

  _onAdapterZoom(zoom) {
    if (Number.isFinite(zoom) === false || zoom === this._viewZoom) {
      return
    }
    this._viewZoom = zoom
    this._updateZoomButtons()
    this._announceZoomSoon(zoom)
    return
  }

  _emitMoveSoon() {
    clearTimeout(this._moveDebounce)
    this._moveDebounce = setTimeout(() => {
      this._moveDebounce = null
      const center = this.center
      this.emit("mj-map-move", { lat: center.lat, lng: center.lng, zoom: this.currentZoom })
    }, EVENT_DEBOUNCE_MS)
    return
  }

  _announceZoomSoon(zoom) {
    clearTimeout(this._zoomDebounce)
    this._zoomDebounce = setTimeout(() => {
      this._zoomDebounce = null
      this._liveEl.textContent = t("mj.map.zoomedTo", { zoom: zoom })
      this.emit("mj-map-zoom-change", { zoom: zoom })
    }, EVENT_DEBOUNCE_MS)
    return
  }

  /* ----- markers ----- */

  _markerKey(marker, index) {
    const key = marker !== null && marker !== undefined && marker.id !== undefined && marker.id !== null
      ? `id:${String(marker.id)}`
      : `index:${index}`
    return key
  }

  _markerLabel(marker) {
    const label = marker !== null && marker !== undefined && marker.label !== undefined && marker.label !== null
      ? String(marker.label)
      : ""
    return label
  }

  _findMarkerById(id) {
    let found = null
    if (id !== null && id !== undefined) {
      for (let index = 0; index < this._markers.length && found === null; index = index + 1) {
        const marker = this._markers[index]
        if (marker !== null && marker !== undefined && marker.id !== undefined && String(marker.id) === String(id)) {
          found = marker
        }
      }
    }
    return found
  }

  /*
   * Show the stored markers: rebuild the list and hand them to the adapter,
   * or redraw the built-in SVG. Called after every (re)initialisation and
   * whenever `markers` is assigned.
   */
  _applyMarkers() {
    this._buildMarkerList()

    if (this._adapterReady === true) {
      this._markerHandles.forEach((handle) => { this._adapter.removeMarker(handle) })
      this._markerHandles.clear()
      for (let index = 0; index < this._markers.length; index = index + 1) {
        const marker = this._markers[index]
        const handle = this._adapter.addMarker(marker)
        this._markerHandles.set(this._markerKey(marker, index), handle)
      }
    } else if (this._adapter === null) {
      this._renderSvgMap()
    }

    /* A popup for a marker that no longer exists is closed. */
    if (this._selectedMarkerId !== null && this._findMarkerById(this._selectedMarkerId) === null) {
      const wasOpen = this._popupEl.classList.contains("open")
      this._popupEl.classList.remove("open")
      this._selectedMarkerId = null
      this._popupInvoker = null
      if (wasOpen === true) {
        this.emit("mj-map-marker-deselect", {})
      }
    }
    return
  }

  _buildMarkerList() {
    this._markerListEl.textContent = ""

    for (let index = 0; index < this._markers.length; index = index + 1) {
      const marker = this._markers[index]
      if (marker === null || marker === undefined) { continue }

      const item = document.createElement("li")
      const link = document.createElement("a")
      link.setAttribute("href", safeUrl(marker.href !== undefined && marker.href !== null ? marker.href : "#"))
      link.setAttribute("data-marker-index", String(index))
      link.textContent = this._markerLabel(marker)

      const description = marker.description !== undefined && marker.description !== null
        ? String(marker.description)
        : ""
      if (description.length > 0) {
        const descriptionId = nextId("mj-map-desc")
        const descriptionEl = document.createElement("span")
        descriptionEl.id = descriptionId
        descriptionEl.className = "marker-desc"
        descriptionEl.textContent = description
        item.appendChild(descriptionEl)
        link.setAttribute("aria-describedby", descriptionId)
      }

      item.appendChild(link)
      this._markerListEl.appendChild(item)
    }

    this._syncListTabStops()
    return
  }

  /*
   * While the list is visually hidden and the built-in SVG already offers a
   * focusable button per marker, the list links leave the tab order so a
   * keyboard user does not meet every marker twice. With an adapter the
   * links stay tabbable (the list is revealed while it has focus).
   */
  _syncListTabStops() {
    const hiddenDuplicate = this._markerListEl.classList.contains("visible") === false &&
      this._adapter === null
    const links = this._markerListEl.querySelectorAll("a")
    for (let index = 0; index < links.length; index = index + 1) {
      if (hiddenDuplicate === true) {
        links[index].setAttribute("tabindex", "-1")
      } else {
        links[index].removeAttribute("tabindex")
      }
    }
    return
  }

  /* ----- built-in SVG plot ----- */

  /* Scale of the marker layer for the current zoom (zoom 10 is 1:1). */
  _svgZoomTransform(width, height) {
    const scale = Math.max(0.5, this._zoom() / DEFAULT_ZOOM)
    const tx = (1 - scale) * width / (2 * scale)
    const ty = (1 - scale) * height / (2 * scale)
    const transform = `scale(${scale.toFixed(3)}) translate(${tx.toFixed(2)},${ty.toFixed(2)})`
    return transform
  }

  _renderSvgMap() {
    if (this._mapTargetEl === null || this._adapter !== null) { return }

    /* Keep keyboard focus on the same marker across a redraw. */
    const focused = this.shadowRoot.activeElement
    const focusedIndex = focused !== null && focused.classList.contains("svg-map-marker") === true
      ? focused.getAttribute("data-marker-index")
      : null

    const markers = []
    for (let index = 0; index < this._markers.length; index = index + 1) {
      const marker = this._markers[index]
      if (marker !== null && marker !== undefined &&
          Number.isFinite(Number(marker.lat)) === true && Number.isFinite(Number(marker.lng)) === true) {
        markers.push({ marker: marker, index: index, lat: Number(marker.lat), lng: Number(marker.lng) })
      }
    }

    this._mapTargetEl.textContent = ""
    this._svgEl = null
    this._svgMarkersGroup = null

    if (markers.length === 0) {
      const notice = document.createElement("div")
      notice.className = "no-adapter"
      notice.textContent = t("mj.map.noAdapter")
      this._mapTargetEl.appendChild(notice)
      return
    }

    // Use actual container dimensions for a responsive SVG; fall back to safe defaults
    const width = this._mapTargetEl.clientWidth || 800
    const height = this._mapTargetEl.clientHeight || 500

    // Margin fraction: reserve this fraction of each dimension on each side so
    // markers and their labels always sit well inside the SVG boundary.
    const MARGIN_FRAC = 0.14
    const drawX0 = width * MARGIN_FRAC
    const drawY0 = height * MARGIN_FRAC
    const drawW = width - 2 * drawX0
    const drawH = height - 2 * drawY0

    let minLat = markers[0].lat
    let maxLat = markers[0].lat
    let minLng = markers[0].lng
    let maxLng = markers[0].lng
    for (let i = 1; i < markers.length; i = i + 1) {
      const entry = markers[i]
      if (entry.lat < minLat) { minLat = entry.lat }
      if (entry.lat > maxLat) { maxLat = entry.lat }
      if (entry.lng < minLng) { minLng = entry.lng }
      if (entry.lng > maxLng) { maxLng = entry.lng }
    }

    // Enforce a minimum geographic extent so a single marker (or markers on
    // one line) does not collapse to a degenerate bounding box. It is about
    // 1 km: markers within one city, the common case, keep their own extent
    // and spread over the drawing instead of piling up in its middle.
    const MIN_EXTENT_DEG = 0.01
    let latSpan = maxLat - minLat
    let lngSpan = maxLng - minLng

    if (latSpan < MIN_EXTENT_DEG) {
      const expand = (MIN_EXTENT_DEG - latSpan) / 2
      minLat = minLat - expand
      maxLat = maxLat + expand
      latSpan = MIN_EXTENT_DEG
    }
    if (lngSpan < MIN_EXTENT_DEG) {
      const expand = (MIN_EXTENT_DEG - lngSpan) / 2
      minLng = minLng - expand
      maxLng = maxLng + expand
      lngSpan = MIN_EXTENT_DEG
    }

    // Apply generous padding (~22%) on top of the minimum-extent bounding box
    // so markers never sit right at the edge of the drawing region either.
    const PAD_FRAC = 0.22
    const viewMinLat = minLat - latSpan * PAD_FRAC
    const viewMaxLat = maxLat + latSpan * PAD_FRAC
    const viewMinLng = minLng - lngSpan * PAD_FRAC
    const viewMaxLng = maxLng + lngSpan * PAD_FRAC
    const viewLatSpan = viewMaxLat - viewMinLat
    const viewLngSpan = viewMaxLng - viewMinLng

    // Project a lat/lng into the inset drawing region (not the full canvas)
    const project = (lat, lng) => {
      const x = drawX0 + ((lng - viewMinLng) / viewLngSpan) * drawW
      const y = drawY0 + ((viewMaxLat - lat) / viewLatSpan) * drawH
      return { x: x, y: y }
    }

    /*
     * The SVG is exposed to assistive technology: its markers are real
     * buttons with a name, so it must not be aria-hidden. The decorative
     * background and graticule are hidden instead.
     */
    const svg = createSvg("svg", {
      class: "svg-map",
      viewBox: `0 0 ${width} ${height}`,
      focusable: "false"
    })

    svg.appendChild(createSvg("rect", {
      class: "svg-map-background", width: width, height: height, "aria-hidden": "true"
    }))

    const GRID_LINES = 5
    const graticule = createSvg("g", { class: "graticule", "aria-hidden": "true" })
    for (let i = 0; i <= GRID_LINES; i = i + 1) {
      const y = (drawY0 + (i / GRID_LINES) * drawH).toFixed(2)
      const x = (drawX0 + (i / GRID_LINES) * drawW).toFixed(2)
      graticule.appendChild(createSvg("line", { class: "svg-map-grid", x1: 0, y1: y, x2: width, y2: y }))
      graticule.appendChild(createSvg("line", { class: "svg-map-grid", x1: x, y1: 0, x2: x, y2: height }))
    }
    svg.appendChild(graticule)

    const markerGroup = createSvg("g", { class: "markers", transform: this._svgZoomTransform(width, height) })
    for (let i = 0; i < markers.length; i = i + 1) {
      const entry = markers[i]
      const marker = entry.marker
      const point = project(entry.lat, entry.lng)

      const rawSize = marker.size !== undefined ? marker.size : (marker.value !== undefined ? marker.value : null)
      const sizeNumber = Number(rawSize)
      const radius = rawSize !== null && Number.isFinite(sizeNumber) === true
        ? Math.min(24, Math.max(6, sizeNumber))
        : 10
      const label = this._markerLabel(marker)

      const node = createSvg("g", {
        class: "svg-map-marker",
        role: "button",
        tabindex: "0",
        "aria-label": label,
        "data-marker-index": entry.index,
        transform: `translate(${point.x.toFixed(2)},${point.y.toFixed(2)})`
      })
      if (this._selectedMarkerId !== null && marker.id !== undefined &&
          String(marker.id) === String(this._selectedMarkerId)) {
        node.classList.add("selected")
        node.setAttribute("aria-current", "true")
      }

      node.appendChild(createSvg("circle", { r: radius }))
      const text = createSvg("text", { dy: radius + 14, "text-anchor": "middle", "aria-hidden": "true" })
      text.textContent = label
      node.appendChild(text)
      markerGroup.appendChild(node)
    }
    svg.appendChild(markerGroup)

    this._mapTargetEl.appendChild(svg)
    this._svgEl = svg
    this._svgMarkersGroup = markerGroup

    if (focusedIndex !== null) {
      const again = markerGroup.querySelector(`.svg-map-marker[data-marker-index="${parseInt(focusedIndex, 10)}"]`)
      if (again !== null) {
        again.focus()
      }
    }
    return
  }

  _applySvgZoom() {
    if (this._svgMarkersGroup === null || this._svgMarkersGroup === undefined) { return }
    const width = this._mapTargetEl.clientWidth || 800
    const height = this._mapTargetEl.clientHeight || 500
    this._svgMarkersGroup.setAttribute("transform", this._svgZoomTransform(width, height))
    return
  }

  /* Mark the selected marker in the built-in SVG. */
  _syncSvgSelection() {
    if (this._svgMarkersGroup === null) { return }
    const nodes = this._svgMarkersGroup.querySelectorAll(".svg-map-marker")
    for (let index = 0; index < nodes.length; index = index + 1) {
      const marker = this._markers[parseInt(nodes[index].getAttribute("data-marker-index"), 10)]
      const selected = this._selectedMarkerId !== null && marker !== undefined && marker.id !== undefined &&
        String(marker.id) === String(this._selectedMarkerId)
      nodes[index].classList.toggle("selected", selected)
      if (selected === true) {
        nodes[index].setAttribute("aria-current", "true")
      } else {
        nodes[index].removeAttribute("aria-current")
      }
    }
    return
  }

  /* ----- zoom and pan ----- */

  /* A zoom step requested by the user (buttons or keyboard). */
  _zoomBy(delta) {
    if (this._isInteractive() === false) { return }

    const current = this.currentZoom
    const next = Math.max(this._minZoom(), Math.min(this._maxZoom(), current + delta))
    if (next === current) { return }

    /* Record the new level first so the attribute handler sees nothing left to do. */
    this._viewZoom = next
    if (this._adapterReady === true) {
      this._adapter.setZoom(next)
    }
    this.setAttribute("zoom", String(next))
    if (this._adapterReady === false) {
      this._applySvgZoom()
    }
    this._updateZoomButtons()
    this._announceZoomSoon(next)
    return
  }

  _updateZoomButtons() {
    if (this._zoomInBtn === null) { return }
    const zoom = this.currentZoom
    const interactive = this._isInteractive()
    const atMax = interactive === false || zoom >= this._maxZoom()
    const atMin = interactive === false || zoom <= this._minZoom()
    this._zoomInBtn.setAttribute("aria-disabled", atMax === true ? "true" : "false")
    this._zoomOutBtn.setAttribute("aria-disabled", atMin === true ? "true" : "false")
    return
  }

  _onMapKeyDown(event) {
    if (event.ctrlKey === true || event.metaKey === true || event.altKey === true) { return }

    const key = event.key

    /* Enter / Space on a built-in marker activates it. */
    if (key === "Enter" || key === " ") {
      const marker = this._markerFromEvent(event)
      if (marker !== null) {
        event.preventDefault()
        this._selectMarker(marker, "svg")
      }
      return
    }

    const panActions = {
      "ArrowUp": [0, -PAN_STEP_PX],
      "ArrowDown": [0, PAN_STEP_PX],
      "ArrowLeft": [-PAN_STEP_PX, 0],
      "ArrowRight": [PAN_STEP_PX, 0]
    }

    if (panActions[key] !== undefined) {
      if (this._isInteractive() === true && this._adapterReady === true && typeof this._adapter.panBy === "function") {
        event.preventDefault()
        const [dx, dy] = panActions[key]
        this._adapter.panBy(dx, dy)

        /* An adapter with on("move") reports the new centre itself. */
        if (this._adapterReportsMoves === false) {
          if (typeof this._adapter.getCenter === "function") {
            const center = this._adapter.getCenter()
            if (center !== null && center !== undefined) {
              this._onAdapterMove(center)
            }
          } else {
            this._emitMoveSoon()
          }
        }
      }
    } else if (key === "+" || key === "=") {
      event.preventDefault()
      this._zoomBy(1)
    } else if (key === "-") {
      event.preventDefault()
      this._zoomBy(-1)
    }
    return
  }

  /* ----- popup ----- */

  /* Fill and open the popup for `marker` without moving focus. */
  _showPopup(marker) {
    const label = this._markerLabel(marker)
    this._selectedMarkerId = marker.id !== undefined ? marker.id : null
    this._popupEl.setAttribute("aria-label", label)
    this._popupEl.querySelector(".popup-title").textContent = label
    this._popupEl.querySelector(".popup-desc").textContent =
      marker.description !== undefined && marker.description !== null ? String(marker.description) : ""
    this._popupEl.classList.add("open")
    this._syncSvgSelection()
    return
  }

  _selectMarker(marker, invoker) {
    /* Remember where focus was so closing the popup can return it. */
    this._popupInvoker = { kind: invoker || null, index: this._markers.indexOf(marker) }

    if (this._adapterReady === true && typeof this._adapter.panTo === "function" && invoker !== "adapter") {
      this._adapter.panTo(marker.lat, marker.lng)
    }

    this._showPopup(marker)
    this.emit("mj-map-marker-select", { marker: marker })
    this._popupEl.querySelector(".popup-close").focus()
    return
  }

  /* The element that should get focus back when the popup closes. */
  _popupReturnTarget() {
    let target = this._mapTargetEl
    const invoker = this._popupInvoker

    if (invoker !== null && invoker.index >= 0) {
      let candidate = null
      if (invoker.kind === "svg" && this._svgMarkersGroup !== null) {
        candidate = this._svgMarkersGroup.querySelector(`.svg-map-marker[data-marker-index="${invoker.index}"]`)
      } else if (invoker.kind === "list") {
        candidate = this._markerListEl.querySelector(`a[data-marker-index="${invoker.index}"]`)
      }
      if (candidate !== null) {
        target = candidate
      }
    }

    return target
  }

  /*
   * `silent` is true when the host cleared the selection through the
   * property; only a user action reports `mj-map-marker-deselect`.
   */
  _closePopup(silent) {
    if (this._popupEl.classList.contains("open") === false) {
      return
    }

    const hadFocus = this._popupEl.matches(":focus-within")
    const returnTarget = this._popupReturnTarget()

    this._popupEl.classList.remove("open")
    this._selectedMarkerId = null
    this._popupInvoker = null
    this._syncSvgSelection()
    if (silent !== true) {
      this.emit("mj-map-marker-deselect", {})
    }

    if (hadFocus === true) {
      returnTarget.focus()
    }
    return
  }

  _showError(message) {
    this._errorEl.textContent = message
    this._errorEl.removeAttribute("hidden")
    this._errorEl.classList.add("visible")
    this.emit("mj-map-error", { message: message })
    return
  }

  _clearError() {
    this._errorEl.textContent = ""
    this._errorEl.setAttribute("hidden", "")
    this._errorEl.classList.remove("visible")
    return
  }

  onDisconnected() {
    this._destroyAdapter(this._adapter)
    return
  }

  /* ----- scriptable API ----- */

  get adapter() { return this._adapter }
  set adapter(value) {
    const next = value !== undefined ? value : null
    if (next === this._adapter) { return }

    this._destroyAdapter(this._adapter)
    this._adapter = next
    /* While detached the adapter is only stored; afterRender initialises it. */
    if (this._mapTargetEl !== null && this.isConnected === true) {
      this._initAdapter()
    }
  }

  get adapterOptions() { return this._adapterOptions }
  set adapterOptions(value) { this._adapterOptions = value || {} }

  get markers() { return this._markers }
  set markers(value) {
    this._markers = Array.isArray(value) === true ? value : []

    /* Before the first render the markers are only stored; afterRender applies them. */
    if (this._markerListEl !== null && this.isConnected === true) {
      this._applyMarkers()
    }
  }

  /* The map centre: as last reported by the adapter, else the lat/lng attributes. */
  get center() {
    const center = this._viewCenter !== null
      ? { lat: this._viewCenter.lat, lng: this._viewCenter.lng }
      : { lat: this._number("lat", 0), lng: this._number("lng", 0) }
    return center
  }
  set center(value) {
    if (value === null || value === undefined) { return }
    /* The attribute handler forwards the new centre to the adapter. */
    this.setAttribute("lat", String(value.lat))
    this.setAttribute("lng", String(value.lng))
  }

  /* The zoom level: as last reported by the adapter, else the `zoom` attribute. */
  get currentZoom() {
    const zoom = this._viewZoom !== null ? this._viewZoom : this._zoom()
    return zoom
  }

  get selectedMarkerId() { return this._selectedMarkerId }
  set selectedMarkerId(id) {
    if (id === null || id === undefined) {
      if (this._popupEl !== null) {
        this._closePopup(true)
      }
      this._selectedMarkerId = null
      return
    }

    const marker = this._findMarkerById(id)
    if (marker !== null) {
      if (this._popupEl !== null && this.isConnected === true) {
        this._selectMarker(marker, null)
      } else {
        /* Not rendered yet: afterRender opens the popup for the stored id. */
        this._selectedMarkerId = marker.id
      }
    }
  }
}
