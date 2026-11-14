/*
 * mjoverlay.js
 *
 * <mj-overlay> -- dimming/blocking backdrop primitive composed by dialog,
 * drawer, lightbox, command palette and tour. Not intended for direct use by
 * application authors.
 *
 * Manages:
 *   - Visual backdrop (dim / block / transparent variants)
 *   - Reference-counted scroll lock on the document
 *   - Reference-counted `inert` on background content
 *   - `mj-overlay-click` emission for light-dismiss
 *   - Optionally (`top-layer`) the top-layer stacking of the backdrop and of
 *     the surface it belongs to, so stacked modals layer in opening order
 *
 * A composer creates the element, configures it and appends it; the overlay
 * becomes active once it is BOTH connected and `visible`, in whichever order
 * those happen, and follows later changes of `scroll-lock`, `inert-target`,
 * `top-layer` and `surface`:
 *
 *   const overlay = document.createElement("mj-overlay")
 *   overlay.surface = panelElement      // stays interactive; the rest is inert
 *   overlay.setAttribute("top-layer", "")
 *   overlay.setAttribute("visible", "")
 *   document.body.appendChild(overlay)
 *   ...
 *   overlay.retire()                    // fade out, then remove
 */

import { MjElement } from "../core/mjelement.js";
import { flatParent } from "../core/focustrap.js";
import { showInTopLayer, removeFromTopLayer } from "../core/overlay.js";

/* ---- Shared scroll lock (reference-counted across all overlays) ---- */

let scrollLockCount = 0;

/* Inline styles the lock replaced, restored when the last lock is released. */
let scrollLockSaved = null;

function acquireScrollLock() {
  scrollLockCount = scrollLockCount + 1
  if (scrollLockCount === 1) {
    const root = document.documentElement
    const body = document.body

    scrollLockSaved = {
      rootOverflow: root.style.overflow,
      rootGutter: root.style.scrollbarGutter,
      bodyOverflow: body.style.overflow,
      bodyPadding: body.style.paddingInlineEnd
    }

    /*
     * Hiding the scrollbar widens the page by the scrollbar's width. Keep
     * that space reserved so nothing jumps sideways when a modal opens.
     */
    const scrollbarWidth = window.innerWidth - root.clientWidth
    if (scrollbarWidth > 0) {
      const gutterSupported = typeof CSS !== "undefined" && CSS.supports("scrollbar-gutter", "stable")
      if (gutterSupported === true) {
        root.style.scrollbarGutter = "stable"
      } else {
        const currentPadding = parseFloat(window.getComputedStyle(body).paddingInlineEnd) || 0
        body.style.paddingInlineEnd = `${currentPadding + scrollbarWidth}px`
      }
    }

    /* Both: an application may scroll on <html> or on <body>. */
    root.style.overflow = "hidden"
    body.style.overflow = "hidden"
  }
  return
}

function releaseScrollLock() {
  if (scrollLockCount > 0) {
    scrollLockCount = scrollLockCount - 1
    if (scrollLockCount === 0 && scrollLockSaved !== null) {
      const root = document.documentElement
      const body = document.body
      root.style.overflow = scrollLockSaved.rootOverflow
      root.style.scrollbarGutter = scrollLockSaved.rootGutter
      body.style.overflow = scrollLockSaved.bodyOverflow
      body.style.paddingInlineEnd = scrollLockSaved.bodyPadding
      scrollLockSaved = null
    }
  }
  return
}

/* ---- Shared inert bookkeeping (reference-counted per element) ---- */

/* element -> number of overlays that currently need it inert. */
const inertCounts = new WeakMap();

/* Elements that were already inert before any overlay touched them. */
const authorInert = new WeakSet();

function acquireInert(element) {
  const count = inertCounts.get(element) || 0
  if (count === 0) {
    if (element.hasAttribute("inert") === true) {
      authorInert.add(element)
    } else {
      element.setAttribute("inert", "")
    }
  }
  inertCounts.set(element, count + 1)
  return
}

function releaseInert(element) {
  const count = inertCounts.get(element) || 0
  if (count > 1) {
    inertCounts.set(element, count - 1)
  } else if (count === 1) {
    inertCounts.delete(element)
    if (authorInert.has(element) === true) {
      /* The application made it inert; that is not ours to undo. */
      authorInert.delete(element)
    } else {
      element.removeAttribute("inert")
    }
  }
  return
}

/* Elements that never become inert: other backdrops must stay clickable. */
function isInertExempt(element) {
  const name = element.localName
  const exempt = name === "mj-overlay" || name === "script" || name === "style" ||
    name === "link" || name === "template"
  return exempt
}

const STYLES = `
:host {
  display: contents;
}

.backdrop {
  position: fixed;
  inset: 0;
  z-index: var(--mj-overlay-z-index, var(--mj-layer-overlay));
  background: var(--mj-overlay-color, var(--mj-overlay-scrim));
  opacity: 0;
  transition: opacity var(--mj-overlay-duration, var(--mj-motion-medium)) var(--mj-motion-ease);
  cursor: default;
}

:host([visible]) .backdrop {
  opacity: 1;
}

/* block: invisible, but still swallows pointer events. */
:host([variant="block"]) .backdrop {
  background: transparent;
}

/* transparent: no visual change and pointer events pass through. */
:host([variant="transparent"]) .backdrop {
  background: transparent;
  pointer-events: none;
}

:host(:not([visible])) .backdrop {
  pointer-events: none;
  opacity: 0;
}

:host([animation="false"]) .backdrop { transition: none; }

@media (prefers-reduced-motion: reduce) {
  .backdrop { transition: none; }
}

@media (forced-colors: active) {
  .backdrop { background: Canvas; opacity: 0.85; }
  :host([variant="block"]) .backdrop,
  :host([variant="transparent"]) .backdrop { background: transparent; }
}
`;

export class MjOverlay extends MjElement {
  static tagName = "mj-overlay";
  static styles = STYLES;
  static watched = ["visible", "variant", "scroll-lock", "inert-target", "top-layer", "z-index", "animation"];

  constructor() {
    super()
    this._inertEls = []
    this._lockHeld = false
    this._backdrop = null
    this._surface = null
    this._active = false
    this._settleTimer = null
    this._settlePending = null
    this._retireTimer = null
  }

  render() {
    const markup = `<div class="backdrop" part="backdrop" role="presentation" aria-hidden="true"></div>`
    return markup
  }

  afterRender() {
    this._backdrop = this.$(".backdrop")
    this.listen(this._backdrop, "click", this._onBackdropClick.bind(this))
    this._applyZIndex()
    return
  }

  onConnected() {
    /* `visible` may have been set while the element was still detached. */
    this._syncActive()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._backdrop === undefined || this._backdrop === null) {
      return
    }

    if (name === "visible") {
      this._syncActive()
    } else if (name === "scroll-lock") {
      this._syncScrollLock()
    } else if (name === "inert-target") {
      this._refreshInert()
    } else if (name === "top-layer") {
      this._syncTopLayer()
    } else if (name === "z-index") {
      this._applyZIndex()
    }
    return
  }

  onDisconnected() {
    this._clearTimers()
    this._deactivate(false)
    return
  }

  /*
   * Active means: connected, rendered and `visible`. Everything the overlay
   * does to the page (scroll lock, inert, top layer) follows this one state,
   * so the order in which a composer sets attributes and appends the element
   * does not matter.
   */
  _syncActive() {
    const shouldBeActive = this.isConnected === true &&
      this._backdrop !== null &&
      this.hasAttribute("visible") === true

    if (shouldBeActive === true && this._active === false) {
      this._activate()
    } else if (shouldBeActive === false && this._active === true) {
      this._deactivate(true)
    }
    return
  }

  _activate() {
    this._active = true
    this._syncScrollLock()
    this._applyInert()
    this._syncTopLayer()
    this._emitWhenSettled("mj-overlay-visible")
    return
  }

  /*
   * Scroll lock and inert are released at once, not after the fade: the
   * composer restores focus to its trigger right after closing, and an
   * element that is still inert cannot take focus.
   */
  _deactivate(announce) {
    if (this._active === false) {
      return
    }
    this._active = false

    this._leaveTopLayer()
    this._releaseInert()
    if (this._lockHeld === true) {
      releaseScrollLock()
      this._lockHeld = false
    }

    if (announce === true) {
      this._emitWhenSettled("mj-overlay-hidden")
    }
    return
  }

  _syncScrollLock() {
    const wanted = this._active === true && this.getAttribute("scroll-lock") !== "false"

    if (wanted === true && this._lockHeld === false) {
      acquireScrollLock()
      this._lockHeld = true
    } else if (wanted === false && this._lockHeld === true) {
      releaseScrollLock()
      this._lockHeld = false
    }
    return
  }

  /*
   * Elements to make inert, in order of precedence:
   *   1. `inert-target` -- everything the selector matches, or nothing for
   *      the keyword "none" (a native modal <dialog> is inert-managed by the
   *      browser).
   *   2. `surface` -- everything that is not the surface or one of its
   *      ancestors: at each level from the surface up to <body> (through
   *      slots and shadow roots) the siblings of the ancestor chain.
   *   3. Neither -- the siblings of the overlay element itself.
   */
  _inertTargets() {
    const selector = this.getAttribute("inert-target")
    let targets = []

    if (selector === "none") {
      targets = []
    } else if (selector !== null && selector.length > 0) {
      let validSelector = true
      try {
        targets = Array.from(document.querySelectorAll(selector))
      } catch (error) {
        validSelector = false
        console.warn(`<mj-overlay>: inert-target "${selector}" is not a valid selector`)
      }
      if (validSelector === true && targets.length === 0) {
        console.warn(`<mj-overlay>: inert-target "${selector}" matches no elements`)
      }
    } else if (this._surface !== null && this._surface.isConnected === true) {
      let node = this._surface

      while (node !== null && node !== document.body && node !== document.documentElement) {
        let siblings = []
        const slot = node.assignedSlot
        if (slot !== null && slot !== undefined) {
          siblings = slot.assignedElements()
        } else if (node.parentNode !== null) {
          siblings = Array.from(node.parentNode.children)
        }

        for (let index = 0; index < siblings.length; index = index + 1) {
          if (siblings[index] !== node) {
            targets.push(siblings[index])
          }
        }

        node = flatParent(node)
      }
    } else if (this.parentElement !== null) {
      targets = Array.from(this.parentElement.children)
    }

    const filtered = targets.filter((el) => el !== this && isInertExempt(el) === false)
    return filtered
  }

  _applyInert() {
    const targets = this._inertTargets()
    for (let index = 0; index < targets.length; index = index + 1) {
      acquireInert(targets[index])
      this._inertEls.push(targets[index])
    }
    return
  }

  _releaseInert() {
    for (let index = 0; index < this._inertEls.length; index = index + 1) {
      releaseInert(this._inertEls[index])
    }
    this._inertEls = []
    return
  }

  _refreshInert() {
    if (this._active === true) {
      this._releaseInert()
      this._applyInert()
    }
    return
  }

  /*
   * With `top-layer`, the backdrop and then the surface are shown in the top
   * layer, in that order, so the pair stacks above every modal opened before
   * it and below every one opened after -- independent of z-index, DOM order
   * and stacking contexts around the surface.
   */
  _syncTopLayer() {
    if (this._active === true && this.hasAttribute("top-layer") === true) {
      showInTopLayer(this._backdrop)
      if (this._surface !== null) {
        showInTopLayer(this._surface)
      }
    } else {
      this._leaveTopLayer()
    }
    return
  }

  _leaveTopLayer() {
    if (this._backdrop !== null) {
      removeFromTopLayer(this._backdrop)
    }
    if (this._surface !== null) {
      removeFromTopLayer(this._surface)
    }
    return
  }

  _applyZIndex() {
    if (this._backdrop === null) {
      return
    }
    const value = this.getAttribute("z-index")
    const numeric = value !== null && value.trim().length > 0 && Number.isFinite(Number(value))
    this._backdrop.style.zIndex = numeric === true ? String(Number(value)) : ""
    return
  }

  /* Duration of the backdrop fade in milliseconds (0 when it does not animate). */
  _fadeDuration() {
    let duration = 0
    if (this._backdrop !== null && this.isConnected === true) {
      const style = window.getComputedStyle(this._backdrop)
      const durations = style.transitionDuration.split(",")
      const delays = style.transitionDelay.split(",")
      const seconds = (parseFloat(durations[0]) || 0) + (parseFloat(delays[0]) || 0)
      duration = Math.round(seconds * 1000)
    }
    return duration
  }

  /*
   * `mj-overlay-visible` / `mj-overlay-hidden` report the finished state:
   * they fire when the fade has ended, or at once when there is none. A
   * toggle during a fade delivers the pending event first, so listeners
   * always see every change, in order.
   */
  _emitWhenSettled(type) {
    this._flushSettleEvent()

    const duration = this._fadeDuration()
    if (duration <= 0) {
      this.emit(type, {})
      return
    }

    this._settlePending = type
    this._settleTimer = window.setTimeout(() => {
      this._settleTimer = null
      this._settlePending = null
      this.emit(type, {})
    }, duration)
    return
  }

  _flushSettleEvent() {
    if (this._settleTimer !== null) {
      window.clearTimeout(this._settleTimer)
      this._settleTimer = null
      const pending = this._settlePending
      this._settlePending = null
      if (pending !== null) {
        this.emit(pending, {})
      }
    }
    return
  }

  _clearTimers() {
    this._flushSettleEvent()
    if (this._retireTimer !== null) {
      window.clearTimeout(this._retireTimer)
      this._retireTimer = null
    }
    return
  }

  /*
   * The composer decides whether a backdrop click dismisses its surface; a
   * listener that calls preventDefault() on this event vetoes the dismissal.
   */
  _onBackdropClick(event) {
    this.emit("mj-overlay-click", { target: event.target }, { cancelable: true })
    return
  }

  /* Scriptable API */

  get visible() {
    const value = this.hasAttribute("visible")
    return value
  }

  set visible(value) {
    this.reflectBoolean("visible", value === true)
    return
  }

  /*
   * The element this backdrop belongs to (a dialog panel, a drawer panel).
   * It and its ancestors stay interactive; with `top-layer` it is stacked
   * directly above the backdrop.
   */
  get surface() {
    return this._surface
  }

  set surface(element) {
    const next = element instanceof Element ? element : null
    if (next === this._surface) {
      return
    }

    if (this._surface !== null) {
      removeFromTopLayer(this._surface)
    }
    this._surface = next

    if (this._active === true) {
      this._refreshInert()
      this._syncTopLayer()
    }
    return
  }

  get lockCount() {
    return scrollLockCount
  }

  get inertEls() {
    return this._inertEls.slice()
  }

  show() {
    this.visible = true
    return
  }

  hide() {
    this.visible = false
    return
  }

  /*
   * Hide the backdrop and remove the element from the document once the
   * fade-out has finished. Composers call this instead of remove() so the
   * backdrop does not vanish abruptly. Scroll lock and inert are released
   * immediately.
   */
  retire() {
    this.removeAttribute("visible")

    const duration = this._fadeDuration()
    if (duration <= 0) {
      this.remove()
      return
    }

    if (this._retireTimer !== null) {
      window.clearTimeout(this._retireTimer)
    }
    this._retireTimer = window.setTimeout(() => {
      this._retireTimer = null
      this.remove()
    }, duration)
    return
  }
}
