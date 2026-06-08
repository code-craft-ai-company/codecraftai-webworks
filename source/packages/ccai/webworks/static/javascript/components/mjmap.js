/*
 * mjmap.js
 *
 * <mj-map> -- accessible geographic map wrapper with pluggable provider adapter,
 * keyboard pan/zoom, accessible marker list fallback, and popup panel.
 * No tile engine is bundled; the adapter is supplied by the host application.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";

const STYLES = `
:host { display: block; }

.container {
  position: relative;
  border-radius: var(--mj-map-radius, var(--mj-radius-md));
  overflow: hidden;
  height: var(--mj-map-height, 400px);
  background: var(--mj-bg-muted);
}

.svg-map {
  width: 100%;
  height: 100%;
  display: block;
  overflow: hidden;
}

.svg-map-marker {
  cursor: pointer;
}
.svg-map-marker:focus {
  outline: none;
}
.svg-map-marker:focus circle {
  stroke-width: 3;
  stroke: var(--mj-focus-ring, #0078d4);
}

.map-target {
  width: 100%;
  height: 100%;
  display: block;
  outline: none;
}
.map-target:focus-visible {
  box-shadow: inset 0 0 0 var(--mj-focus-ring-width) var(--mj-map-focus-ring, var(--mj-focus-ring));
}

.controls {
  position: absolute;
  top: var(--mj-space-3);
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
  width: 2rem;
  height: 2rem;
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
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  clip-path: inset(50%);
  white-space: nowrap;
  margin: -1px;
}
.marker-list.visible {
  position: static;
  width: auto;
  height: auto;
  clip: unset;
  clip-path: unset;
  white-space: normal;
  margin: 0;
  padding: var(--mj-space-3);
  list-style: none;
  border-top: 1px solid var(--mj-border);
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

.popup {
  position: absolute;
  top: var(--mj-space-3);
  inset-inline-start: var(--mj-space-3);
  width: var(--mj-map-popup-width, 16rem);
  background: var(--mj-map-popup-bg, var(--mj-surface));
  border-radius: var(--mj-radius-md);
  box-shadow: var(--mj-elevation-3);
  padding: var(--mj-space-3);
  z-index: 20;
  display: none;
}
.popup.open { display: block; }
.popup-title { font-weight: var(--mj-font-weight-medium); margin: 0 0 var(--mj-space-1); }
.popup-desc { font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); margin: 0; }
.popup-close {
  position: absolute;
  top: var(--mj-space-2);
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
}
.loading.visible { display: flex; }

.error {
  position: absolute;
  inset: 0;
  display: none;
  align-items: center;
  justify-content: center;
  padding: var(--mj-space-4);
  color: var(--mj-color-danger);
  text-align: center;
}
.error.visible { display: flex; }

.no-adapter {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--mj-text-muted);
  font-size: var(--mj-font-size-sm);
}

.live {
  position: absolute;
  width: 1px; height: 1px;
  overflow: hidden; clip: rect(0 0 0 0); clip-path: inset(50%);
}
`;

export class MjMap extends MjElement {
  static tagName = "mj-map";
  static styles = STYLES;
  static watched = ["lat", "lng", "zoom", "min-zoom", "max-zoom",
    "map-type", "interactive", "show-list", "label", "loading"];

  constructor() {
    super()
    this._adapter = null
    this._adapterOptions = {}
    this._markers = []
    this._selectedMarkerId = null
    this._markerHandles = new Map()
    this._zoomDebounce = null
    this._resizeObserver = null
    this._mapTargetEl = null
    this._popupEl = null
    this._markerListEl = null
    this._zoomInBtn = null
    this._zoomOutBtn = null
    this._liveEl = null
    this._svgEl = null
    this._svgMarkersGroup = null
  }

  render() {
    const markup = `
      <section role="application" aria-label="" part="container" class="container">
        <div class="map-target" part="map-target" tabindex="0" aria-label="Map"></div>
        <div class="controls" part="controls">
          <button class="ctrl-btn" part="zoom-in" aria-label="Zoom in">+</button>
          <button class="ctrl-btn" part="zoom-out" aria-label="Zoom out">−</button>
          <slot name="controls"></slot>
        </div>
        <div class="popup" part="popup" role="dialog" aria-label="" aria-modal="false">
          <button class="popup-close" aria-label="Close popup">✕</button>
          <p class="popup-title"></p>
          <p class="popup-desc"></p>
          <slot name="popup"></slot>
        </div>
        <ul class="marker-list" part="marker-list"></ul>
        <div class="loading" part="loading" aria-live="polite">Loading map…</div>
        <div class="error" part="error" role="alert" hidden></div>
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

    this._applyAttrs()
    this._wireControls()
    this._setupResize()
    this._initAdapter()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._sectionEl === null || this._sectionEl === undefined) { return }
    if (name === "label") {
      this._sectionEl.setAttribute("aria-label", newValue || "")
      if (newValue === null || newValue.length === 0) {
        console.warn("<mj-map>: `label` attribute is required for accessibility.")
      }
    } else if (name === "show-list") {
      this._markerListEl.classList.toggle("visible", newValue !== null)
    } else if (name === "zoom") {
      const z = parseFloat(newValue) || 10
      if (this._adapter !== null) {
        this._adapter.setZoom(z)
      } else {
        this._applySvgZoom()
      }
      this._updateZoomButtons(z)
    }
    return
  }

  _applyAttrs() {
    const label = this.getAttribute("label") || ""
    this._sectionEl.setAttribute("aria-label", label)
    if (label.length === 0) {
      console.warn("<mj-map>: `label` attribute is required for accessibility.")
    }

    const showList = this.hasAttribute("show-list")
    this._markerListEl.classList.toggle("visible", showList)

    const zoom = parseFloat(this.getAttribute("zoom") || "10")
    this._updateZoomButtons(zoom)
    return
  }

  _wireControls() {
    this.listen(this._zoomInBtn, "click", () => this._zoomBy(1))
    this.listen(this._zoomOutBtn, "click", () => this._zoomBy(-1))
    this.listen(this._mapTargetEl, "keydown", (e) => this._onMapKeyDown(e))

    const closeBtn = this.$(".popup-close")
    this.listen(closeBtn, "click", () => this._closePopup())
    return
  }

  _setupResize() {
    this._resizeObserver = new ResizeObserver(() => {
      if (this._adapter !== null && typeof this._adapter.resize === "function") {
        this._adapter.resize()
      } else if (this._svgEl !== null) {
        // Re-render the built-in SVG map so it fills the new container size
        this._renderSvgMap()
      }
    })
    this._resizeObserver.observe(this._sectionEl)
    this.onTeardown(() => {
      if (this._resizeObserver !== null) {
        this._resizeObserver.disconnect()
        this._resizeObserver = null
      }
    })
    return
  }

  _initAdapter() {
    if (this._adapter === null) {
      this._loadingEl.classList.remove("visible")
      this._renderSvgMap()
      return
    }

    this._loadingEl.classList.add("visible")
    const lat = parseFloat(this.getAttribute("lat") || "0")
    const lng = parseFloat(this.getAttribute("lng") || "0")
    const zoom = parseFloat(this.getAttribute("zoom") || "10")
    const mapType = this.getAttribute("map-type") || "road"

    try {
      this._adapter.init(this._mapTargetEl, { lat, lng, zoom, mapType, ...this._adapterOptions })
      this._loadingEl.classList.remove("visible")
      this.emit("mj-map-ready", {})
    } catch (err) {
      this._showError(err.message)
    }
    return
  }

  _renderSvgMap() {
    if (this._mapTargetEl === null) { return }

    const markers = this._markers
    if (markers.length === 0) {
      this._mapTargetEl.innerHTML = `<div class="no-adapter">No map adapter configured. Set the <code>adapter</code> property.</div>`
      console.warn("<mj-map>: No adapter set and no markers. Marker list is the only accessible output.")
      return
    }

    // Use actual container dimensions for a responsive SVG; fall back to safe defaults
    const containerW = this._mapTargetEl.clientWidth || 800
    const containerH = this._mapTargetEl.clientHeight || 500
    const W = containerW
    const H = containerH

    // Margin fraction: reserve this fraction of each dimension on each side so
    // markers and their labels always sit well inside the SVG boundary.
    const MARGIN_FRAC = 0.14

    const marginX = W * MARGIN_FRAC
    const marginY = H * MARGIN_FRAC

    // Drawing region within which markers are projected
    const drawX0 = marginX
    const drawY0 = marginY
    const drawW = W - 2 * marginX
    const drawH = H - 2 * marginY

    let minLat = markers[0].lat
    let maxLat = markers[0].lat
    let minLng = markers[0].lng
    let maxLng = markers[0].lng
    for (let i = 1; i < markers.length; i = i + 1) {
      const m = markers[i]
      if (m.lat < minLat) { minLat = m.lat }
      if (m.lat > maxLat) { maxLat = m.lat }
      if (m.lng < minLng) { minLng = m.lng }
      if (m.lng > maxLng) { maxLng = m.lng }
    }

    // Enforce a minimum geographic extent so close-together (or single) markers
    // don't collapse to a degenerate bounding box.
    const MIN_EXTENT_DEG = 0.5

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
    const latPad = latSpan * PAD_FRAC
    const lngPad = lngSpan * PAD_FRAC

    const viewMinLat = minLat - latPad
    const viewMaxLat = maxLat + latPad
    const viewMinLng = minLng - lngPad
    const viewMaxLng = maxLng + lngPad
    const viewLatSpan = viewMaxLat - viewMinLat
    const viewLngSpan = viewMaxLng - viewMinLng

    // Project a lat/lng into the inset drawing region (not the full W×H canvas)
    const project = (lat, lng) => {
      const x = drawX0 + ((lng - viewMinLng) / viewLngSpan) * drawW
      const y = drawY0 + ((viewMaxLat - lat) / viewLatSpan) * drawH
      return { x: x, y: y }
    }

    const zoom = parseFloat(this.getAttribute("zoom") || "10")
    const scale = Math.max(0.5, zoom / 10)

    const GRID_LINES = 5
    const latStep = viewLatSpan / GRID_LINES
    const lngStep = viewLngSpan / GRID_LINES

    let gridLines = ""
    for (let i = 0; i <= GRID_LINES; i = i + 1) {
      const gridLat = viewMinLat + i * latStep
      const yPos = drawY0 + ((viewMaxLat - gridLat) / viewLatSpan) * drawH
      gridLines += `<line x1="0" y1="${yPos.toFixed(2)}" x2="${W}" y2="${yPos.toFixed(2)}" stroke="var(--mj-border, #dde)" stroke-opacity="0.4" stroke-width="1" />`

      const gridLng = viewMinLng + i * lngStep
      const xPos = drawX0 + ((gridLng - viewMinLng) / viewLngSpan) * drawW
      gridLines += `<line x1="${xPos.toFixed(2)}" y1="0" x2="${xPos.toFixed(2)}" y2="${H}" stroke="var(--mj-border, #dde)" stroke-opacity="0.4" stroke-width="1" />`
    }

    let markerEls = ""
    for (let i = 0; i < markers.length; i = i + 1) {
      const marker = markers[i]
      const pt = project(marker.lat, marker.lng)
      const rawSize = marker.size !== undefined ? marker.size : (marker.value !== undefined ? marker.value : null)
      const baseR = rawSize !== null ? Math.min(24, Math.max(6, Number(rawSize))) : 10
      const r = baseR
      const labelOffset = r + 4
      const markerId = marker.id !== undefined ? String(marker.id) : String(i)
      markerEls += `<g class="svg-map-marker" role="button" tabindex="0" aria-label="${this._escAttr(marker.label)}" data-marker-id="${this._escAttr(markerId)}" transform="translate(${pt.x.toFixed(2)},${pt.y.toFixed(2)})">
  <circle r="${r}" fill="var(--mj-accent, #0078d4)" fill-opacity="0.85" stroke="var(--mj-surface, #fff)" stroke-width="2" />
  <text dy="${labelOffset + 10}" text-anchor="middle" font-size="11" font-family="var(--mj-font-sans, sans-serif)" fill="var(--mj-text, #222)" stroke="var(--mj-surface, #fff)" stroke-width="3" paint-order="stroke">${this._escText(marker.label)}</text>
</g>`
    }

    const svgId = nextId("mj-map-svg")
    const svgMarkup = `<svg id="${svgId}" class="svg-map" viewBox="0 0 ${W} ${H}" aria-hidden="true" focusable="false" xmlns="http://www.w3.org/2000/svg">
  <rect width="${W}" height="${H}" fill="var(--mj-map-surface, #e8edf4)" />
  <g class="graticule">${gridLines}</g>
  <g class="markers" transform="scale(${scale.toFixed(3)}) translate(${((1 - scale) * W / (2 * scale)).toFixed(2)},${((1 - scale) * H / (2 * scale)).toFixed(2)})">${markerEls}</g>
</svg>`

    this._mapTargetEl.innerHTML = svgMarkup
    this._svgEl = this._mapTargetEl.querySelector("svg")
    this._svgMarkersGroup = this._mapTargetEl.querySelector(".markers")

    const markerNodes = this._mapTargetEl.querySelectorAll(".svg-map-marker")
    for (let i = 0; i < markerNodes.length; i = i + 1) {
      const node = markerNodes[i]
      const markerId = node.getAttribute("data-marker-id")
      const marker = this._findMarkerById(markerId, i)
      if (marker !== null) {
        const capturedMarker = marker
        this.listen(node, "click", () => { this._selectMarker(capturedMarker) })
        this.listen(node, "keydown", (e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault()
            this._selectMarker(capturedMarker)
          }
        })
      }
    }
    return
  }

  _findMarkerById(id, fallbackIndex) {
    for (let i = 0; i < this._markers.length; i = i + 1) {
      const m = this._markers[i]
      if (m.id !== undefined && String(m.id) === id) { return m }
    }
    if (fallbackIndex >= 0 && fallbackIndex < this._markers.length) {
      return this._markers[fallbackIndex]
    }
    return null
  }

  _escAttr(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
  }

  _escText(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
  }

  _applySvgZoom() {
    if (this._svgMarkersGroup === null || this._svgMarkersGroup === undefined) { return }
    const W = this._mapTargetEl !== null ? (this._mapTargetEl.clientWidth || 800) : 800
    const H = this._mapTargetEl !== null ? (this._mapTargetEl.clientHeight || 500) : 500
    const zoom = parseFloat(this.getAttribute("zoom") || "10")
    const scale = Math.max(0.5, zoom / 10)
    const tx = ((1 - scale) * W / (2 * scale)).toFixed(2)
    const ty = ((1 - scale) * H / (2 * scale)).toFixed(2)
    this._svgMarkersGroup.setAttribute("transform", `scale(${scale.toFixed(3)}) translate(${tx},${ty})`)
    return
  }

  _zoomBy(delta) {
    const current = parseFloat(this.getAttribute("zoom") || "10")
    const minZoom = parseFloat(this.getAttribute("min-zoom") || "1")
    const maxZoom = parseFloat(this.getAttribute("max-zoom") || "20")
    const next = Math.max(minZoom, Math.min(maxZoom, current + delta))
    this.setAttribute("zoom", String(next))

    if (this._adapter !== null) {
      this._adapter.setZoom(next)
    } else {
      this._applySvgZoom()
    }
    this._updateZoomButtons(next)

    clearTimeout(this._zoomDebounce)
    this._zoomDebounce = setTimeout(() => {
      const msg = `Zoomed to level ${next}`
      this._liveEl.textContent = msg
      this.emit("mj-map-zoom-change", { zoom: next })
    }, 200)
    return
  }

  _updateZoomButtons(zoom) {
    const minZoom = parseFloat(this.getAttribute("min-zoom") || "1")
    const maxZoom = parseFloat(this.getAttribute("max-zoom") || "20")
    this._zoomInBtn.setAttribute("aria-disabled", zoom >= maxZoom ? "true" : "false")
    this._zoomOutBtn.setAttribute("aria-disabled", zoom <= minZoom ? "true" : "false")
    return
  }

  _onMapKeyDown(event) {
    const key = event.key
    const panActions = {
      "ArrowUp": [0, -50],
      "ArrowDown": [0, 50],
      "ArrowLeft": [-50, 0],
      "ArrowRight": [50, 0]
    }

    if (panActions[key] !== undefined) {
      event.preventDefault()
      if (this._adapter !== null && typeof this._adapter.panBy === "function") {
        const [dx, dy] = panActions[key]
        this._adapter.panBy(dx, dy)
        this.emit("mj-map-move", {
          lat: parseFloat(this.getAttribute("lat") || "0"),
          lng: parseFloat(this.getAttribute("lng") || "0"),
          zoom: parseFloat(this.getAttribute("zoom") || "10")
        })
      }
    } else if (key === "+" || key === "=") {
      event.preventDefault()
      this._zoomBy(1)
    } else if (key === "-") {
      event.preventDefault()
      this._zoomBy(-1)
    } else if (key === "Escape") {
      this._closePopup()
    }
    return
  }

  _buildMarkerList() {
    this._markerListEl.innerHTML = ""
    for (let i = 0; i < this._markers.length; i = i + 1) {
      const marker = this._markers[i]
      const li = document.createElement("li")
      const a = document.createElement("a")
      a.href = marker.href || "#"
      a.textContent = marker.label

      if (marker.description !== undefined && marker.description.length > 0) {
        const descId = nextId("mj-map-desc")
        const desc = document.createElement("span")
        desc.id = descId
        desc.textContent = marker.description
        desc.style.cssText = "position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)"
        li.appendChild(desc)
        a.setAttribute("aria-describedby", descId)
      }

      const capturedMarker = marker
      this.listen(a, "click", (e) => {
        e.preventDefault()
        this._selectMarker(capturedMarker)
      })

      li.appendChild(a)
      this._markerListEl.appendChild(li)
    }
    return
  }

  _selectMarker(marker) {
    this._selectedMarkerId = marker.id

    if (this._adapter !== null && typeof this._adapter.panTo === "function") {
      this._adapter.panTo(marker.lat, marker.lng)
    }

    this._popupEl.setAttribute("aria-label", marker.label)
    this._popupEl.querySelector(".popup-title").textContent = marker.label
    this._popupEl.querySelector(".popup-desc").textContent = marker.description || ""
    this._popupEl.classList.add("open")

    this.emit("mj-map-marker-select", { marker: marker })
    this._popupEl.querySelector(".popup-close").focus()
    return
  }

  _closePopup() {
    this._popupEl.classList.remove("open")
    this._selectedMarkerId = null
    this.emit("mj-map-marker-deselect", {})
    this._mapTargetEl.focus()
    return
  }

  _showError(message) {
    this._loadingEl.classList.remove("visible")
    this._errorEl.textContent = message
    this._errorEl.removeAttribute("hidden")
    this._errorEl.classList.add("visible")
    this.emit("mj-map-error", { message: message })
    return
  }

  onDisconnected() {
    if (this._resizeObserver !== null) {
      this._resizeObserver.disconnect()
      this._resizeObserver = null
    }
    if (this._zoomDebounce !== null) {
      clearTimeout(this._zoomDebounce)
      this._zoomDebounce = null
    }
    if (this._adapter !== null && typeof this._adapter.destroy === "function") {
      this._adapter.destroy()
    }
    return
  }

  /* ----- scriptable API ----- */

  get adapter() { return this._adapter }
  set adapter(v) {
    this._adapter = v
    if (this._mapTargetEl !== null) { this._initAdapter() }
  }

  get adapterOptions() { return this._adapterOptions }
  set adapterOptions(v) { this._adapterOptions = v || {} }

  get markers() { return this._markers }
  set markers(v) {
    this._markers = Array.isArray(v) ? v : []
    this._buildMarkerList()
    if (this._adapter !== null) {
      this._markerHandles.forEach((handle) => { this._adapter.removeMarker(handle) })
      this._markerHandles.clear()
      for (let i = 0; i < this._markers.length; i = i + 1) {
        const handle = this._adapter.addMarker(this._markers[i])
        this._markerHandles.set(this._markers[i].id, handle)
      }
    } else if (this._mapTargetEl !== null) {
      this._renderSvgMap()
    }
  }

  get center() {
    const lat = parseFloat(this.getAttribute("lat") || "0")
    const lng = parseFloat(this.getAttribute("lng") || "0")
    return { lat: lat, lng: lng }
  }
  set center(v) {
    this.setAttribute("lat", String(v.lat))
    this.setAttribute("lng", String(v.lng))
    if (this._adapter !== null) { this._adapter.panTo(v.lat, v.lng) }
  }

  get selectedMarkerId() { return this._selectedMarkerId }
  set selectedMarkerId(id) {
    const marker = this._markers.find(m => m.id === id)
    if (marker !== undefined) {
      this._selectMarker(marker)
    }
  }
}
