/*
 * mjlightbox.js
 *
 * <mj-lightbox> -- full-screen modal media viewer. Presents images/videos
 * with prev/next navigation, zoom (images), captions, and keyboard/swipe
 * controls. Built on top of a modal dialog pattern with a focus trap.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { trapFocus } from "../core/focustrap.js";
import { announce } from "../core/announcer.js";

const STYLES = `
:host {
  display: contents;
}

.lb-backdrop {
  position: fixed;
  inset: 0;
  z-index: var(--mj-layer-modal);
  background: var(--mj-lightbox-bg, rgba(14, 18, 27, 0.95));
  display: flex;
  flex-direction: column;
  opacity: 0;
  transition: opacity var(--mj-motion-medium) var(--mj-motion-ease);
}

:host([open]) .lb-backdrop {
  opacity: 1;
}

:host(:not([open])) .lb-backdrop {
  pointer-events: none;
  visibility: hidden;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--mj-space-2);
  padding: var(--mj-space-3) var(--mj-space-4);
  flex-shrink: 0;
  background: var(--mj-lightbox-toolbar-bg, rgba(0,0,0,0.4));
}

.counter {
  flex: 1;
  color: rgba(255,255,255,0.8);
  font-size: var(--mj-font-size-sm);
}

.tb-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.25rem;
  height: 2.25rem;
  padding: 0;
  background: rgba(255,255,255,0.1);
  border: none;
  border-radius: var(--mj-radius-md);
  cursor: pointer;
  color: #fff;
  font-size: var(--mj-font-size-md);
  line-height: 1;
}

.tb-btn:hover { background: rgba(255,255,255,0.25); }
.tb-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.tb-btn:disabled { opacity: 0.35; cursor: not-allowed; }

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

.media-el {
  max-width: 100%;
  max-height: calc(100dvh - 10rem);
  object-fit: contain;
  display: block;
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
  background: rgba(0,0,0,0.5);
  border: none;
  border-radius: var(--mj-radius-circle);
  cursor: pointer;
  color: #fff;
  font-size: var(--mj-font-size-xl);
  z-index: 1;
}

.nav-btn:hover { background: rgba(0,0,0,0.75); }
.nav-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.nav-btn:disabled { opacity: 0.25; cursor: not-allowed; }

.nav-prev { inset-inline-start: var(--mj-space-3); }
.nav-next { inset-inline-end: var(--mj-space-3); }

.caption-bar {
  flex-shrink: 0;
  padding: var(--mj-space-3) var(--mj-space-5);
  background: var(--mj-lightbox-caption-bg, rgba(0,0,0,0.5));
  color: rgba(255,255,255,0.9);
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
  static watched = ["open", "current-index", "loop", "zoom-enabled", "show-caption", "show-counter"];

  constructor() {
    super()
    this.items = []
    this._trapDispose = null
    this._backdrop = null
    this._mediaEl = null
    this._captionEl = null
    this._counterEl = null
    this._prevBtn = null
    this._nextBtn = null
    this._zoomLevel = 1
    this._returnFocusEl = null
    this._touchStartX = null
    this._overlay = null
    this._lbId = nextId("mj-lightbox")
  }

  render() {
    const closeLabel = this.getAttribute("close-label") || "Close"
    const prevLabel = this.getAttribute("prev-label") || "Previous"
    const nextLabel = this.getAttribute("next-label") || "Next"
    const zoomInLabel = this.getAttribute("zoom-in-label") || "Zoom in"
    const zoomOutLabel = this.getAttribute("zoom-out-label") || "Zoom out"
    const dialogLabel = this.getAttribute("label") || "Media viewer"

    const markup = `
      <slot></slot>
      <div class="lb-backdrop" part="dialog" role="dialog" aria-modal="true"
           aria-label="${dialogLabel}" aria-labelledby="${this._lbId}-counter" tabindex="-1">
        <div class="toolbar" part="toolbar">
          <span class="counter" part="caption-bar" id="${this._lbId}-counter"></span>
          <slot name="toolbar-actions"></slot>
          <button class="tb-btn" part="zoom-out" aria-label="${zoomOutLabel}" data-action="zoom-out">&#x2212;</button>
          <button class="tb-btn" part="zoom-in" aria-label="${zoomInLabel}" data-action="zoom-in">&#x2b;</button>
          <button class="tb-btn" part="close-button" aria-label="${closeLabel}" data-action="close">&#x2715;</button>
        </div>
        <div class="viewport" part="viewport">
          <button class="nav-btn nav-prev" part="prev-button" aria-label="${prevLabel}" data-action="prev">
            <slot name="prev-icon">&#x2039;</slot>
          </button>
          <div class="media-wrap" part="zoom-container">
            <img class="media-el" part="media" src="" alt="" />
          </div>
          <button class="nav-btn nav-next" part="next-button" aria-label="${nextLabel}" data-action="next">
            <slot name="next-icon">&#x203a;</slot>
          </button>
        </div>
        <div class="caption-bar" part="caption-bar"><slot name="caption"></slot></div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._backdrop = this.$(".lb-backdrop")
    this._mediaEl = this.$(".media-el")
    this._captionEl = this.$(".caption-bar")
    this._counterEl = this.$(`#${this._lbId}-counter`)
    this._prevBtn = this.$(".nav-prev")
    this._nextBtn = this.$(".nav-next")

    this.listen(this._backdrop, "click", this._onBackdropClick.bind(this))
    this.listen(this._backdrop, "keydown", this._onKeydown.bind(this))
    this.listen(this._backdrop, "touchstart", this._onTouchStart.bind(this), { passive: true })
    this.listen(this._backdrop, "touchend", this._onTouchEnd.bind(this))

    const closeBtn = this.$("[data-action='close']")
    if (closeBtn !== null) {
      this.listen(closeBtn, "click", () => this._closeLightbox("close-button"))
    }

    this.$("[data-action='prev']") && this.listen(this.$("[data-action='prev']"), "click", () => this._navigate(-1))
    this.$("[data-action='next']") && this.listen(this.$("[data-action='next']"), "click", () => this._navigate(1))
    this.$("[data-action='zoom-in']") && this.listen(this.$("[data-action='zoom-in']"), "click", () => this._zoom(0.5))
    this.$("[data-action='zoom-out']") && this.listen(this.$("[data-action='zoom-out']"), "click", () => this._zoom(-0.5))

    if (this.hasAttribute("open") === true) {
      this._openLightbox("api")
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "open" && this._backdrop !== null) {
      if (newValue !== null) {
        this._openLightbox("api")
      } else {
        this._closeLightbox("api")
      }
    }
    if (name === "current-index" && this.hasAttribute("open") === true) {
      this._renderCurrentItem()
    }
    return
  }

  onDisconnected() {
    this._cleanupTrap()
    this._hideOverlay()
    return
  }

  _openLightbox(reason) {
    if (this.items.length === 0) {
      console.warn("<mj-lightbox>: no items defined")
      return
    }

    this._returnFocusEl = document.activeElement
    this._showOverlay()
    this._trapDispose = trapFocus(this._backdrop, this.$("[data-action='close']"))
    this._renderCurrentItem()

    this.emit("mj-lightbox-open", {
      index: this._currentIndex(),
      item: this._currentItem()
    })
    return
  }

  _closeLightbox(reason) {
    const restoreEl = this._returnFocusEl
    this._returnFocusEl = null

    this._cleanupTrap()
    this._hideOverlay()
    this.removeAttribute("open")

    if (restoreEl !== null && typeof restoreEl.focus === "function") {
      restoreEl.focus()
    }

    this.emit("mj-lightbox-close", { reason: reason })
    return
  }

  _cleanupTrap() {
    if (this._trapDispose !== null) {
      this._trapDispose()
      this._trapDispose = null
    }
    return
  }

  _showOverlay() {
    if (this._overlay !== null) {
      return
    }
    const overlay = document.createElement("mj-overlay")
    overlay.setAttribute("visible", "")
    overlay.setAttribute("scroll-lock", "true")
    document.body.appendChild(overlay)
    this._overlay = overlay
    return
  }

  _hideOverlay() {
    if (this._overlay === null) {
      return
    }
    this._overlay.remove()
    this._overlay = null
    return
  }

  _currentIndex() {
    const idx = parseInt(this.getAttribute("current-index") || "0", 10)
    const clamped = Math.max(0, Math.min(idx, this.items.length - 1))
    return clamped
  }

  _currentItem() {
    const idx = this._currentIndex()
    if (idx < this.items.length) {
      return this.items[idx]
    }
    return null
  }

  _renderCurrentItem() {
    const item = this._currentItem()
    if (item === null) {
      return
    }

    const idx = this._currentIndex()
    const total = this.items.length

    if (this._mediaEl !== null) {
      this._mediaEl.src = item.src || ""
      this._mediaEl.alt = item.alt || ""
    }

    if (this._captionEl !== null) {
      this._captionEl.textContent = item.caption || ""
    }

    if (this._counterEl !== null) {
      const fmt = this.getAttribute("counter-format") || "{current} of {total}"
      const text = fmt.replace("{current}", String(idx + 1)).replace("{total}", String(total))
      this._counterEl.textContent = text
    }

    const loop = this.getAttribute("loop") !== "false"
    if (this._prevBtn !== null) {
      this._prevBtn.disabled = loop === false && idx === 0
    }
    if (this._nextBtn !== null) {
      this._nextBtn.disabled = loop === false && idx === total - 1
    }

    announce(`Image ${idx + 1} of ${total}: ${item.alt || item.caption || ""}`, "polite")
    return
  }

  _navigate(delta) {
    const loop = this.getAttribute("loop") !== "false"
    const total = this.items.length
    const current = this._currentIndex()
    const prev = current

    let next = current + delta
    if (next < 0) {
      next = loop === true ? total - 1 : 0
    }
    if (next >= total) {
      next = loop === true ? 0 : total - 1
    }

    if (next === current) {
      return
    }

    this.setAttribute("current-index", String(next))
    this.emit("mj-lightbox-change", {
      index: next,
      previousIndex: prev,
      item: this._currentItem()
    })
    return
  }

  _zoom(delta) {
    const maxZoom = parseFloat(this.getAttribute("max-zoom") || "4")
    this._zoomLevel = Math.max(1, Math.min(this._zoomLevel + delta, maxZoom))
    if (this._mediaEl !== null) {
      this._mediaEl.parentElement.style.transform = `scale(${this._zoomLevel})`
    }
    this.emit("mj-lightbox-zoom", { level: this._zoomLevel })
    return
  }

  _onKeydown(event) {
    if (event.key === "Escape") {
      event.preventDefault()
      this._closeLightbox("escape")
      return
    }
    if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
      this._navigate(-1)
      return
    }
    if (event.key === "ArrowRight" || event.key === "ArrowDown") {
      this._navigate(1)
      return
    }
    if (event.key === "+" || event.key === "=") {
      this._zoom(0.5)
      return
    }
    if (event.key === "-") {
      this._zoom(-0.5)
      return
    }
    if (event.key === "0") {
      this._zoomLevel = 1
      if (this._mediaEl !== null) {
        this._mediaEl.parentElement.style.transform = "scale(1)"
      }
      return
    }
    if (event.key === "Home") {
      this.setAttribute("current-index", "0")
      return
    }
    if (event.key === "End") {
      this.setAttribute("current-index", String(this.items.length - 1))
      return
    }
    return
  }

  _onBackdropClick(event) {
    const isViewport = event.target === this._backdrop
    if (isViewport === true) {
      this._closeLightbox("backdrop")
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

    if (deltaX < -threshold) {
      this._navigate(1)
    } else if (deltaX > threshold) {
      this._navigate(-1)
    }
    return
  }

  /* Scriptable API */

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

  show(index) {
    if (index !== undefined) {
      this.setAttribute("current-index", String(index))
    }
    this.setAttribute("open", "")
    return
  }

  close() {
    this._closeLightbox("api")
    return
  }
}
