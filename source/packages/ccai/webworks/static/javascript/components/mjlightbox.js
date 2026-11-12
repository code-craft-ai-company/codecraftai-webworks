/*
 * mjlightbox.js
 *
 * <mj-lightbox> -- full-screen modal media viewer. Presents images and
 * videos with prev/next navigation, zoom and pan (images), captions, and
 * keyboard/swipe controls. A modal surface: focus is trapped, the page
 * behind is inert and scroll-locked, and the viewer sits in the top layer.
 *
 * Items are supplied through the `items` property:
 *   lightbox.items = [{ src, alt, caption, type }]   // type: "image" | "video"
 */

import { MjElement } from "../core/mjelement.js";
import { html, safeUrl } from "../core/html.js";
import { t } from "../core/intl.js";
import { trapFocus, deepActiveElement } from "../core/focustrap.js";
import { pushLayer, removeLayer, claimEscape } from "../core/overlay.js";
import { announce } from "../core/announcer.js";

/* Zoom changes by this much per step (button, + / - key). */
const ZOOM_STEP = 0.5;

/* Distance in CSS pixels one arrow-key press pans a zoomed image. */
const PAN_KEY_STEP = 40;

/* Pointer travel beyond which a press counts as a drag, not a click. */
const DRAG_THRESHOLD = 4;

/*
 * The viewer keeps a dark surround in both themes (media reads best on it),
 * so its colours are not the page tokens. Each one is a component custom
 * property whose fallback is the default: --mj-lightbox-bg, -color,
 * -muted-color (counter, status), -toolbar-bg, -caption-bg, -control-color,
 * -control-bg, -control-bg-hover (toolbar buttons), -nav-bg, -nav-bg-hover.
 */
const STYLES = `
:host {
  display: contents;
}

.lb-backdrop {
  position: fixed;
  inset: 0;
  z-index: var(--mj-layer-modal);
  box-sizing: border-box;
  margin: 0;
  padding: 0;
  border: 0 none;
  width: 100%;
  height: 100%;
  background: var(--mj-lightbox-bg, rgba(14, 18, 27, 0.95));
  color: var(--mj-lightbox-color, rgba(255, 255, 255, 0.9));
  display: flex;
  flex-direction: column;
  outline: none;
  opacity: 0;
  pointer-events: none;
  visibility: hidden;
  transition: opacity var(--mj-motion-medium) var(--mj-motion-ease);
}

/* Shown only while the viewer really is open (it needs items to open). */
.lb-backdrop[data-active] {
  opacity: 1;
  pointer-events: auto;
  visibility: visible;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--mj-space-2);
  padding: var(--mj-space-3) var(--mj-space-4);
  flex-shrink: 0;
  background: var(--mj-lightbox-toolbar-bg, rgba(0, 0, 0, 0.4));
}

.counter {
  flex: 1;
  color: var(--mj-lightbox-muted-color, rgba(255, 255, 255, 0.8));
  font-size: var(--mj-font-size-sm);
}

:host([show-counter="false"]) .counter { visibility: hidden; }

.tb-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.25rem;
  height: 2.25rem;
  padding: 0;
  background: var(--mj-lightbox-control-bg, rgba(255, 255, 255, 0.1));
  border: none;
  border-radius: var(--mj-radius-md);
  cursor: pointer;
  color: var(--mj-lightbox-control-color, #fff);
  font-size: var(--mj-font-size-md);
  line-height: 1;
}

.tb-btn:hover { background: var(--mj-lightbox-control-bg-hover, rgba(255, 255, 255, 0.25)); }
.tb-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.tb-btn:disabled { opacity: 0.35; cursor: not-allowed; }
.tb-btn[hidden] { display: none; }

.viewport {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  min-height: 0;
}

.media-wrap {
  max-width: 100%;
  max-height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform var(--mj-motion-medium) var(--mj-motion-ease);
}

.viewport[data-zoomed] .media-wrap { cursor: grab; }
.viewport[data-panning] .media-wrap { cursor: grabbing; transition: none; }

.media-el {
  max-width: 100%;
  max-height: calc(100dvh - 10rem);
  object-fit: contain;
  display: block;
  user-select: none;
  -webkit-user-drag: none;
}

.media-el[hidden] { display: none; }

.viewport[data-state="error"] .media-el { display: none; }

.media-status {
  position: absolute;
  inset-block-end: var(--mj-space-3);
  inset-inline: 0;
  text-align: center;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-lightbox-muted-color, rgba(255, 255, 255, 0.8));
  pointer-events: none;
}

.viewport[data-state="error"] .media-status {
  inset-block: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 3rem;
  height: 3rem;
  background: var(--mj-lightbox-nav-bg, rgba(0, 0, 0, 0.5));
  border: none;
  border-radius: var(--mj-radius-circle);
  cursor: pointer;
  color: var(--mj-lightbox-control-color, #fff);
  font-size: var(--mj-font-size-xl);
  z-index: 1;
}

.nav-btn:hover { background: var(--mj-lightbox-nav-bg-hover, rgba(0, 0, 0, 0.75)); }
.nav-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.nav-btn:disabled { opacity: 0.25; cursor: not-allowed; }

.nav-prev { inset-inline-start: var(--mj-space-3); }
.nav-next { inset-inline-end: var(--mj-space-3); }

/* The chevrons are drawn for LTR; mirror them with the reading direction. */
:host(:dir(rtl)) .nav-btn { transform: translateY(-50%) scaleX(-1); }

.caption-bar {
  flex-shrink: 0;
  padding: var(--mj-space-3) var(--mj-space-5);
  background: var(--mj-lightbox-caption-bg, rgba(0, 0, 0, 0.5));
  font-size: var(--mj-font-size-sm);
  text-align: center;
  min-height: 2.5rem;
}

:host(:not([show-caption])) .caption-bar { display: none; }
:host([show-caption="false"]) .caption-bar { display: none; }

@media (prefers-reduced-motion: reduce) {
  .lb-backdrop, .media-wrap { transition: none; }
}
`;

export class MjLightbox extends MjElement {
  static tagName = "mj-lightbox";
  static styles = STYLES;
  static watched = [
    "open", "current-index", "loop", "variant", "zoom-enabled", "show-caption", "show-counter",
    "label", "close-label", "prev-label", "next-label", "zoom-in-label", "zoom-out-label",
    "counter-format"
  ];

  constructor() {
    super()
    this._items = []
    this._trapDispose = null
    this._layer = null
    this._backdrop = null
    this._viewport = null
    this._mediaWrap = null
    this._mediaEl = null
    this._videoEl = null
    this._statusEl = null
    this._captionEl = null
    this._counterEl = null
    this._prevBtn = null
    this._nextBtn = null
    this._zoomInBtn = null
    this._zoomOutBtn = null
    this._closeBtn = null
    this._returnFocusEl = null
    this._touchStartX = null
    this._overlay = null

    /* True from a successful open until the close has completed. */
    this._isOpen = false

    /* Zoom multiplier (1 = fit) and pan offset of the current image. */
    this._zoomLevel = 1
    this._panX = 0
    this._panY = 0

    /* Pointer-drag pan in progress: the pointer and where it started. */
    this._panPointerId = null
    this._panStart = null
    this._dragged = false

    /* True when the pointer press that precedes a click began on the backdrop. */
    this._pressOnBackdrop = false
  }

  render() {
    const markup = html`
      <slot></slot>
      <div class="lb-backdrop" part="dialog" role="dialog" aria-modal="true" tabindex="-1">
        <div class="toolbar" part="toolbar">
          <span class="counter" part="counter"></span>
          <slot name="toolbar-actions"></slot>
          <button class="tb-btn" part="zoom-out" type="button" data-action="zoom-out">&#x2212;</button>
          <button class="tb-btn" part="zoom-in" type="button" data-action="zoom-in">&#x2b;</button>
          <button class="tb-btn" part="close-button" type="button" data-action="close">&#x2715;</button>
        </div>
        <div class="viewport" part="viewport">
          <button class="nav-btn nav-prev" part="prev-button" type="button" data-action="prev">
            <slot name="prev-icon">&#x2039;</slot>
          </button>
          <div class="media-wrap" part="zoom-container">
            <img class="media-el" part="media" alt="" draggable="false" />
            <video class="media-el media-video" part="media" controls hidden></video>
          </div>
          <div class="media-status" part="status" role="status"></div>
          <button class="nav-btn nav-next" part="next-button" type="button" data-action="next">
            <slot name="next-icon">&#x203a;</slot>
          </button>
        </div>
        <div class="caption-bar" part="caption-bar">
          <slot name="caption"><span class="caption-text"></span></slot>
        </div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._backdrop = this.$(".lb-backdrop")
    this._viewport = this.$(".viewport")
    this._mediaWrap = this.$(".media-wrap")
    this._mediaEl = this.$("img.media-el")
    this._videoEl = this.$("video.media-el")
    this._statusEl = this.$(".media-status")
    this._captionEl = this.$(".caption-text")
    this._counterEl = this.$(".counter")
    this._prevBtn = this.$(".nav-prev")
    this._nextBtn = this.$(".nav-next")
    this._zoomInBtn = this.$("[data-action='zoom-in']")
    this._zoomOutBtn = this.$("[data-action='zoom-out']")
    this._closeBtn = this.$("[data-action='close']")

    this.listen(this._backdrop, "keydown", this._onKeydown.bind(this))
    this.listen(this._backdrop, "touchstart", this._onTouchStart.bind(this), { passive: true })
    this.listen(this._backdrop, "touchend", this._onTouchEnd.bind(this))

    this.listen(this._closeBtn, "click", () => this._closeLightbox("close-button"))
    this.listen(this._prevBtn, "click", () => this._navigate(-1))
    this.listen(this._nextBtn, "click", () => this._navigate(1))
    this.listen(this._zoomInBtn, "click", () => this._zoom(ZOOM_STEP))
    this.listen(this._zoomOutBtn, "click", () => this._zoom(-ZOOM_STEP))

    this.listen(this._viewport, "click", this._onViewportClick.bind(this))
    this.listen(this._viewport, "dblclick", this._onViewportDoubleClick.bind(this))
    this.listen(this._viewport, "pointerdown", this._onPanStart.bind(this))
    this.listen(this._viewport, "pointermove", this._onPanMove.bind(this))
    this.listen(this._viewport, "pointerup", this._onPanEnd.bind(this))
    this.listen(this._viewport, "pointercancel", this._onPanEnd.bind(this))

    this.listen(this._mediaEl, "load", () => this._setMediaState("ready"))
    this.listen(this._mediaEl, "error", () => this._setMediaState("error"))
    this.listen(this._videoEl, "loadeddata", () => this._setMediaState("ready"))
    this.listen(this._videoEl, "error", () => this._setMediaState("error"))

    this._applyLabels()
    this._applyZoomControls()

    if (this.hasAttribute("open") === true) {
      this._openLightbox()
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._backdrop === undefined || this._backdrop === null) {
      return
    }

    if (name === "open") {
      if (newValue !== null) {
        this._openLightbox()
      } else {
        this._closeLightbox("api")
      }
    } else if (name === "current-index") {
      if (this._isOpen === true && oldValue !== newValue) {
        this._resetZoom()
        this._renderCurrentItem()
      }
    } else if (name === "zoom-enabled") {
      this._applyZoomControls()
    } else if (name === "loop" || name === "counter-format" || name === "variant") {
      if (this._isOpen === true) {
        this._renderCurrentItem()
      }
    } else if (name !== "show-caption" && name !== "show-counter") {
      this._applyLabels()
    }
    return
  }

  onDisconnected() {
    /* Removed while open: release everything without events or refocus. */
    if (this._isOpen === true) {
      this._leaveOpenState()
      this._isOpen = false
    }
    return
  }

  /* ----- attribute-driven rendering ----- */

  _applyLabels() {
    this._backdrop.setAttribute("aria-label", this.getAttribute("label") || t("mj.lightbox.label"))
    this._closeBtn.setAttribute("aria-label", this.getAttribute("close-label") || t("core.close"))
    this._prevBtn.setAttribute("aria-label", this.getAttribute("prev-label") || t("core.previous"))
    this._nextBtn.setAttribute("aria-label", this.getAttribute("next-label") || t("core.next"))
    this._zoomInBtn.setAttribute("aria-label", this.getAttribute("zoom-in-label") || t("mj.lightbox.zoomIn"))
    this._zoomOutBtn.setAttribute("aria-label", this.getAttribute("zoom-out-label") || t("mj.lightbox.zoomOut"))
    return
  }

  _zoomAllowed() {
    const item = this._currentItem()
    const enabled = this.getAttribute("zoom-enabled") !== "false"
    const allowed = enabled === true && (item === null || this._isVideo(item) === false)
    return allowed
  }

  /* Zoom buttons exist only where zoom applies; their state follows the level. */
  _applyZoomControls() {
    const allowed = this._zoomAllowed()
    const maxZoom = this._maxZoom()

    this._zoomInBtn.hidden = allowed === false
    this._zoomOutBtn.hidden = allowed === false
    this._zoomInBtn.disabled = this._zoomLevel >= maxZoom
    this._zoomOutBtn.disabled = this._zoomLevel <= 1

    if (allowed === false && this._zoomLevel !== 1) {
      this._resetZoom()
    }
    return
  }

  _maxZoom() {
    const parsed = parseFloat(this.getAttribute("max-zoom") || "")
    const maxZoom = Number.isFinite(parsed) === true && parsed >= 1 ? parsed : 4
    return maxZoom
  }

  /* ----- open / close ----- */

  /*
   * Open the viewer. With no items there is nothing to show: the `open`
   * attribute is remembered and the viewer opens as soon as `items` is
   * assigned (the usual declarative order: markup first, data second).
   */
  _openLightbox() {
    if (this._backdrop === null || this._isOpen === true || this.isConnected === false) {
      return
    }
    if (this._items.length === 0) {
      return
    }

    this._isOpen = true
    this._returnFocusEl = deepActiveElement()
    this._resetZoom()

    this._backdrop.setAttribute("data-active", "")
    this._showOverlay()
    this._layer = pushLayer({
      surface: this._backdrop,
      modal: true,
      onEscape: () => {
        this._closeLightbox("escape")
      }
    })
    this._trapDispose = trapFocus(this._backdrop, this._closeBtn, { contain: true })
    this._renderCurrentItem()

    this.emit("mj-lightbox-open", {
      index: this._currentIndex(),
      item: this._currentItem()
    })
    return
  }

  _leaveOpenState() {
    if (this._layer !== null) {
      removeLayer(this._layer)
      this._layer = null
    }

    if (this._trapDispose !== null) {
      /* Focus is restored by the caller, once nothing is inert any more. */
      this._trapDispose({ restoreFocus: false })
      this._trapDispose = null
    }

    this._hideOverlay()

    if (this._backdrop !== null) {
      this._backdrop.removeAttribute("data-active")
    }
    if (this._videoEl !== null) {
      this._videoEl.pause()
    }
    this._resetZoom()
    return
  }

  _closeLightbox(reason) {
    if (this._isOpen === false) {
      return
    }

    this._isOpen = false
    this._leaveOpenState()

    if (this.hasAttribute("open") === true) {
      this.removeAttribute("open")
    }

    const restoreEl = this._returnFocusEl
    this._returnFocusEl = null
    if (restoreEl !== null && restoreEl.isConnected === true && typeof restoreEl.focus === "function") {
      restoreEl.focus()
    }

    this.emit("mj-lightbox-close", { reason: reason })
    return
  }

  /*
   * The viewer paints its own full-screen background, so <mj-overlay> is
   * transparent here: it makes the page inert, locks scrolling and puts the
   * viewer in the top layer.
   */
  _showOverlay() {
    if (this._overlay !== null) {
      return
    }
    const overlay = document.createElement("mj-overlay")
    overlay.surface = this._backdrop
    overlay.setAttribute("variant", "transparent")
    overlay.setAttribute("top-layer", "")
    overlay.setAttribute("visible", "")
    document.body.appendChild(overlay)
    this._overlay = overlay
    return
  }

  /*
   * retire() releases inert and the scroll lock at once (so focus can be
   * restored right after) and removes the element when its fade has ended.
   */
  _hideOverlay() {
    if (this._overlay === null) {
      return
    }
    const overlay = this._overlay
    this._overlay = null
    if (typeof overlay.retire === "function") {
      overlay.retire()
    } else {
      overlay.remove()
    }
    return
  }

  /* ----- items ----- */

  _currentIndex() {
    const parsed = parseInt(this.getAttribute("current-index") || "0", 10)
    const idx = Number.isFinite(parsed) === true ? parsed : 0
    const clamped = Math.max(0, Math.min(idx, this._items.length - 1))
    return clamped
  }

  _currentItem() {
    const idx = this._currentIndex()
    if (idx >= 0 && idx < this._items.length) {
      return this._items[idx]
    }
    return null
  }

  _isVideo(item) {
    let video = this.getAttribute("variant") === "video"
    if (item.type === "video") {
      video = true
    } else if (item.type === "image") {
      video = false
    }
    return video
  }

  _counterText(position, total) {
    let text = ""
    const format = this.getAttribute("counter-format")
    if (format !== null && format.length > 0) {
      text = format.replace("{current}", String(position)).replace("{total}", String(total))
    } else {
      text = t("mj.lightbox.counter", { current: position, total: total })
    }
    return text
  }

  _setMediaState(state) {
    this._viewport.setAttribute("data-state", state)

    let message = ""
    if (state === "loading") {
      message = t("core.loading")
    } else if (state === "error") {
      message = t("mj.lightbox.loadError")
    }
    this._statusEl.textContent = message
    return
  }

  _renderCurrentItem() {
    const item = this._currentItem()
    if (item === null) {
      return
    }

    const idx = this._currentIndex()
    const total = this._items.length
    const source = safeUrl(item.src, "")
    const description = item.alt || item.caption || ""

    this._setMediaState(source.length > 0 ? "loading" : "error")

    if (this._isVideo(item) === true) {
      this._mediaEl.hidden = true
      this._mediaEl.removeAttribute("src")
      this._videoEl.hidden = false
      this._videoEl.setAttribute("aria-label", description)
      if (this._videoEl.getAttribute("src") !== source) {
        this._videoEl.setAttribute("src", source)
      }
    } else {
      this._videoEl.pause()
      this._videoEl.hidden = true
      this._videoEl.removeAttribute("src")
      this._mediaEl.hidden = false
      this._mediaEl.alt = item.alt || ""
      if (this._mediaEl.getAttribute("src") !== source) {
        this._mediaEl.setAttribute("src", source)
      } else if (this._mediaEl.complete === true) {
        /* Same image as before: no load event will come, so settle now. */
        this._setMediaState(this._mediaEl.naturalWidth > 0 ? "ready" : "error")
      }
    }

    /* The caption text lives in the slot's fallback, so the slot survives. */
    this._captionEl.textContent = item.caption || ""

    const counterText = this._counterText(idx + 1, total)
    this._counterEl.textContent = counterText

    const loop = this.getAttribute("loop") !== "false"
    this._prevBtn.disabled = total < 2 || (loop === false && idx === 0)
    this._nextBtn.disabled = total < 2 || (loop === false && idx === total - 1)

    this._applyZoomControls()

    const announcement = description.length > 0 ? `${counterText}: ${description}` : counterText
    announce(announcement, "polite")
    return
  }

  /* Show the item at `index`; every user-driven change goes through here. */
  _goTo(index) {
    const total = this._items.length
    const previous = this._currentIndex()
    if (total === 0 || index < 0 || index >= total || index === previous) {
      return
    }

    this.setAttribute("current-index", String(index))
    this.emit("mj-lightbox-change", {
      index: index,
      previousIndex: previous,
      item: this._currentItem()
    })
    return
  }

  _navigate(delta) {
    const loop = this.getAttribute("loop") !== "false"
    const total = this._items.length
    if (total === 0) {
      return
    }

    let next = this._currentIndex() + delta
    if (next < 0) {
      next = loop === true ? total - 1 : 0
    }
    if (next >= total) {
      next = loop === true ? 0 : total - 1
    }

    this._goTo(next)
    return
  }

  /* ----- zoom and pan ----- */

  _applyTransform() {
    const zoomed = this._zoomLevel > 1
    if (zoomed === true) {
      this._mediaWrap.style.transform = `translate(${this._panX}px, ${this._panY}px) scale(${this._zoomLevel})`
      this._viewport.setAttribute("data-zoomed", "")
    } else {
      this._mediaWrap.style.transform = ""
      this._viewport.removeAttribute("data-zoomed")
    }
    return
  }

  /* Keep the zoomed image from being dragged completely out of view. */
  _clampPan() {
    const viewWidth = this._viewport.clientWidth
    const viewHeight = this._viewport.clientHeight
    const limitX = (viewWidth * (this._zoomLevel - 1)) / 2
    const limitY = (viewHeight * (this._zoomLevel - 1)) / 2
    this._panX = Math.max(-limitX, Math.min(this._panX, limitX))
    this._panY = Math.max(-limitY, Math.min(this._panY, limitY))
    return
  }

  _setZoom(level) {
    if (this._zoomAllowed() === false) {
      return
    }

    const clamped = Math.max(1, Math.min(level, this._maxZoom()))
    if (clamped === this._zoomLevel) {
      return
    }

    this._zoomLevel = clamped
    if (clamped === 1) {
      this._panX = 0
      this._panY = 0
    } else {
      this._clampPan()
    }

    this._applyTransform()
    this._applyZoomControls()
    this.emit("mj-lightbox-zoom", { level: this._zoomLevel })
    return
  }

  _zoom(delta) {
    this._setZoom(this._zoomLevel + delta)
    return
  }

  /* Back to fit, silently: used when the item changes or the viewer closes. */
  _resetZoom() {
    this._zoomLevel = 1
    this._panX = 0
    this._panY = 0
    this._panPointerId = null
    this._panStart = null
    if (this._mediaWrap !== null) {
      this._applyTransform()
      this._viewport.removeAttribute("data-panning")
    }
    return
  }

  _pan(deltaX, deltaY) {
    this._panX = this._panX + deltaX
    this._panY = this._panY + deltaY
    this._clampPan()
    this._applyTransform()
    return
  }

  _onPanStart(event) {
    this._dragged = false
    this._pressOnBackdrop = event.target === this._viewport || event.target === this._mediaWrap
    const onMedia = event.target === this._mediaEl
    if (this._zoomLevel <= 1 || onMedia === false) {
      return
    }

    this._panPointerId = event.pointerId
    this._panStart = { x: event.clientX, y: event.clientY, panX: this._panX, panY: this._panY }
    this._viewport.setAttribute("data-panning", "")
    try {
      this._viewport.setPointerCapture(event.pointerId)
    } catch (error) {
      /* The pointer is already gone; the drag simply will not track. */
    }
    return
  }

  _onPanMove(event) {
    if (this._panStart === null || event.pointerId !== this._panPointerId) {
      return
    }

    const deltaX = event.clientX - this._panStart.x
    const deltaY = event.clientY - this._panStart.y
    if (Math.abs(deltaX) > DRAG_THRESHOLD || Math.abs(deltaY) > DRAG_THRESHOLD) {
      this._dragged = true
    }

    this._panX = this._panStart.panX + deltaX
    this._panY = this._panStart.panY + deltaY
    this._clampPan()
    this._applyTransform()
    return
  }

  _onPanEnd(event) {
    if (this._panStart === null || event.pointerId !== this._panPointerId) {
      return
    }
    this._panPointerId = null
    this._panStart = null
    this._viewport.removeAttribute("data-panning")
    return
  }

  /* ----- events ----- */

  /*
   * The dark area around the media is the backdrop: the viewport itself or
   * the zoom wrapper, but not the media element or a navigation button.
   */
  _onViewportClick(event) {
    const onBackdrop = event.target === this._viewport || event.target === this._mediaWrap

    /*
     * A real click must also have STARTED on the backdrop: while an image is
     * being panned the pointer is captured, which redirects the click that
     * ends the drag to the viewport. A scripted click has no press at all.
     */
    const scripted = event.detail === 0
    const pressedHere = scripted === true || this._pressOnBackdrop === true

    if (onBackdrop === true && pressedHere === true && this._dragged === false) {
      this._closeLightbox("backdrop")
    }
    this._dragged = false
    this._pressOnBackdrop = false
    return
  }

  _onViewportDoubleClick(event) {
    if (event.target !== this._mediaEl) {
      return
    }
    this._setZoom(this._zoomLevel > 1 ? 1 : 2)
    return
  }

  _onKeydown(event) {
    if (event.key === "Escape") {
      const mine = claimEscape(event, this._layer)
      event.preventDefault()
      if (mine === true) {
        this._closeLightbox("escape")
      }
      return
    }

    /* Keys typed into a slotted toolbar field are not viewer shortcuts. */
    const path = event.composedPath()
    const origin = path.length > 0 ? path[0] : event.target
    const typing = origin instanceof HTMLInputElement || origin instanceof HTMLTextAreaElement ||
      origin instanceof HTMLSelectElement || (origin instanceof HTMLElement && origin.isContentEditable === true)
    if (typing === true) {
      return
    }

    const zoomed = this._zoomLevel > 1
    const rtl = window.getComputedStyle(this._backdrop).direction === "rtl"
    const inlineStep = rtl === true ? -1 : 1

    if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
      event.preventDefault()
      const towardsRight = event.key === "ArrowRight"
      if (zoomed === true) {
        /* Pan: the arrow moves the view, so the image moves the other way. */
        this._pan(towardsRight === true ? -PAN_KEY_STEP : PAN_KEY_STEP, 0)
      } else {
        /* Navigate: the arrow pointing at the inline end is "next". */
        this._navigate(towardsRight === true ? inlineStep : -inlineStep)
      }
      return
    }

    if (event.key === "ArrowUp" || event.key === "ArrowDown") {
      event.preventDefault()
      const down = event.key === "ArrowDown"
      if (zoomed === true) {
        this._pan(0, down === true ? -PAN_KEY_STEP : PAN_KEY_STEP)
      } else {
        this._navigate(down === true ? 1 : -1)
      }
      return
    }

    if (event.key === "+" || event.key === "=") {
      this._zoom(ZOOM_STEP)
      return
    }
    if (event.key === "-") {
      this._zoom(-ZOOM_STEP)
      return
    }
    if (event.key === "0") {
      this._setZoom(1)
      return
    }
    if (event.key === "Home") {
      event.preventDefault()
      this._goTo(0)
      return
    }
    if (event.key === "End") {
      event.preventDefault()
      this._goTo(this._items.length - 1)
      return
    }
    return
  }

  _onTouchStart(event) {
    const touch = event.touches[0]
    this._touchStartX = touch.clientX
    return
  }

  _onTouchEnd(event) {
    if (this._touchStartX === null) {
      return
    }
    const touch = event.changedTouches[0]
    const deltaX = touch.clientX - this._touchStartX
    const threshold = window.innerWidth * 0.3
    this._touchStartX = null

    /* While zoomed a horizontal drag pans the image instead. */
    if (this._zoomLevel > 1) {
      return
    }

    const rtl = window.getComputedStyle(this._backdrop).direction === "rtl"
    const inlineStep = rtl === true ? -1 : 1
    if (deltaX < -threshold) {
      this._navigate(inlineStep)
    } else if (deltaX > threshold) {
      this._navigate(-inlineStep)
    }
    return
  }

  /* Scriptable API */

  /*
   * The media items. An accessor (not a plain field) so that a value
   * assigned before the element was upgraded is picked up, and so that
   * assigning it later renders: the viewer opens if `open` is already set,
   * refreshes if it is open, and closes if the list became empty.
   */
  get items() {
    return this._items
  }

  set items(value) {
    this._items = Array.isArray(value) ? value.slice() : []

    if (this._backdrop === null) {
      return
    }

    if (this._isOpen === true) {
      if (this._items.length === 0) {
        this._closeLightbox("api")
      } else {
        this._resetZoom()
        this._renderCurrentItem()
      }
    } else if (this.hasAttribute("open") === true) {
      this._openLightbox()
    }
    return
  }

  get open() {
    return this.hasAttribute("open")
  }

  set open(value) {
    this.reflectBoolean("open", value === true)
    return
  }

  get currentItem() {
    return this._currentItem()
  }

  get zoomLevel() {
    return this._zoomLevel
  }

  get isPanning() {
    return this._panStart !== null
  }

  show(index) {
    if (this._items.length === 0) {
      console.warn("<mj-lightbox>: no items defined")
      return
    }
    if (index !== undefined) {
      this.setAttribute("current-index", String(index))
    }
    this.setAttribute("open", "")
    return
  }

  close() {
    if (this._isOpen === true) {
      this._closeLightbox("api")
    } else if (this.hasAttribute("open") === true) {
      /* `open` was waiting for items: withdraw it. */
      this.removeAttribute("open")
    }
    return
  }
}
