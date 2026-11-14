/*
 * mjtour.js
 *
 * <mj-tour> -- sequences anchored popover coach-mark steps across page
 * elements to guide users through a feature or onboarding flow. Each step
 * spotlights a target element with a full-viewport cutout and shows a card
 * next to it. While the tour runs it is modal: focus stays in the card and
 * the page behind is inert.
 *
 * Steps are supplied through the `steps` property:
 *   { targetId?, title, body, placement? }   // placement e.g. "bottom-start"
 * A step without `targetId` is shown centred. Titles and bodies are text.
 *
 * `variant`: `anchored` (default) anchors each card to its step's target;
 * `floating` shows every card centred with the page dimmed evenly, without
 * scrolling to, spotlighting or requiring the targets. (The spec's `modal`
 * variant, which shows the step in an <mj-dialog>, is not implemented and
 * behaves as `anchored`.)
 *
 * Focus: each step focuses the last control of the card's navigation row --
 * the built-in Next / Done button, or, when the `navigation` slot is
 * filled, the slotted control with `autofocus`, else the last focusable
 * slotted control (the forward button by convention). The card itself when
 * there is none.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";
import { trapFocus, getFocusable, deepActiveElement } from "../core/focustrap.js";
import {
  position, pushLayer, removeLayer, claimEscape, showInTopLayer, removeFromTopLayer
} from "../core/overlay.js";

/* Gap between the spotlight cutout and the card. */
const CARD_OFFSET = 12;

/* Longest wait for a smooth scroll to settle before positioning anyway. */
const SCROLL_SETTLE_MS = 600;

const STYLES = `
:host {
  display: contents;
}

/*
 * Only top / left / width / height are set on the spotlight: with insets on
 * both sides as well the box would be over-constrained, and in RTL "left"
 * is the value the browser ignores.
 */
.spotlight {
  position: fixed;
  top: 0;
  left: 0;
  width: 0;
  height: 0;
  margin: 0;
  padding: 0;
  border: 0 none;
  overflow: visible;
  z-index: var(--mj-layer-modal);
  pointer-events: none;
  background: transparent;
  box-shadow: 0 0 0 9999px var(--mj-tour-spotlight-color, rgba(14, 18, 27, 0.7));
  border-radius: 4px;
  transition: top var(--mj-motion-medium) var(--mj-motion-ease),
              left var(--mj-motion-medium) var(--mj-motion-ease),
              width var(--mj-motion-medium) var(--mj-motion-ease),
              height var(--mj-motion-medium) var(--mj-motion-ease);
}

/* A centred step has no target: the whole page is dimmed evenly. */
.spotlight[data-centred] {
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  transition: none;
}

:host(:not([active])) .spotlight { display: none; }
:host([spotlight="false"]) .spotlight { display: none; }

.card-wrapper {
  position: fixed;
  margin: 0;
  padding: 0;
  border: 0 none;
  overflow: visible;
  background: transparent;
  z-index: calc(var(--mj-layer-modal) + 1);
  pointer-events: auto;
}

:host(:not([active])) .card-wrapper { display: none; }

.card {
  box-sizing: border-box;
  width: var(--mj-tour-card-width, 20rem);
  max-width: calc(100vw - var(--mj-space-6));
  background: var(--mj-surface);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-tour-card-radius, var(--mj-radius-lg));
  box-shadow: var(--mj-tour-card-shadow, var(--mj-elevation-3));
  padding: var(--mj-tour-card-padding, var(--mj-space-5));
  color: var(--mj-text);
  outline: none;
}

.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--mj-space-2);
  margin-block-end: var(--mj-space-3);
}

.card-title {
  font-size: var(--mj-font-size-md);
  font-weight: var(--mj-font-weight-bold);
  margin: 0;
  flex: 1;
}

.skip-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.75rem;
  height: 1.75rem;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: var(--mj-radius-md);
  cursor: pointer;
  color: var(--mj-text-muted);
  font-size: 0.8rem;
  flex-shrink: 0;
}

.skip-btn:hover { background: var(--mj-bg-muted); color: var(--mj-text); }
.skip-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.card-body {
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text-muted);
  line-height: var(--mj-line-height);
  margin-block-end: var(--mj-space-4);
}

.card-body-text { margin: 0; }

.card-counter {
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
  margin-block-end: var(--mj-space-3);
}

.card-counter[hidden], .progress-dots[hidden] { display: none; }

.progress-dots {
  display: flex;
  gap: var(--mj-space-1);
  margin-block-end: var(--mj-space-3);
}

.dot {
  width: var(--mj-tour-dot-size, 8px);
  height: var(--mj-tour-dot-size, 8px);
  border-radius: var(--mj-radius-circle);
  background: var(--mj-border-strong);
  transition: background var(--mj-motion-fast);
}

.dot[data-active="true"] {
  background: var(--mj-tour-dot-active-color, var(--mj-accent));
}

.card-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--mj-space-2);
}

.nav-btn {
  padding: var(--mj-space-2) var(--mj-space-4);
  font: inherit;
  font-size: var(--mj-font-size-sm);
  font-weight: var(--mj-font-weight-medium);
  border-radius: var(--mj-radius-md);
  border: 1px solid var(--mj-border-strong);
  cursor: pointer;
  background: var(--mj-surface);
  color: var(--mj-text);
}

.nav-btn.primary {
  background: var(--mj-accent);
  border-color: var(--mj-accent);
  color: var(--mj-text-on-accent);
  margin-inline-start: auto;
}

.nav-btn.primary:hover { background: var(--mj-accent-hover); border-color: var(--mj-accent-hover); }
.nav-btn:hover:not(.primary) { background: var(--mj-bg-muted); }
.nav-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.nav-btn[hidden] { display: none; }

.tour-status {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  clip-path: inset(50%);
  white-space: nowrap;
}

@media (prefers-reduced-motion: reduce) {
  .spotlight { transition: none; }
}
`;

/*
 * Map a tour placement ("bottom-start", "end", "start-end"...) to the
 * placement vocabulary of core/overlay.js, where the alignment of a
 * start/end card is "top" or "bottom".
 */
function toOverlayPlacement(placement) {
  const parts = String(placement || "bottom-start").split("-")
  const side = ["top", "bottom", "start", "end"].indexOf(parts[0]) >= 0 ? parts[0] : "bottom"
  let align = parts.length > 1 ? parts[1] : ""

  if (side === "start" || side === "end") {
    if (align === "start") {
      align = "top"
    } else if (align === "end") {
      align = "bottom"
    }
  }

  const resolved = align.length > 0 ? `${side}-${align}` : side
  return resolved
}

export class MjTour extends MjElement {
  static tagName = "mj-tour";
  static styles = STYLES;
  static watched = [
    "active", "current-step", "variant", "show-progress-dots", "show-counter",
    "skip-label", "back-label", "next-label", "done-label", "counter-format", "spotlight-padding",
    "scroll-lock"
  ];

  constructor() {
    super()
    this._steps = []
    this._spotlightEl = null
    this._cardWrapperEl = null
    this._cardEl = null
    this._statusEl = null
    this._resizeObserver = null
    this._preTourFocus = null
    this._overlay = null
    this._layer = null
    this._trapDispose = null
    this._tourId = nextId("mj-tour")

    /* True while the tour is running (between begin and end). */
    this._running = false

    /* The step on screen, and its target element (null for a centred step). */
    this._currentIndex = -1
    this._currentTarget = null

    /* True while the component itself writes `current-step`. */
    this._syncingStep = false

    this._repositionFrame = null
    this._settleTimer = null
    this._onViewportChange = this._scheduleReposition.bind(this)

    this.isComplete = false
    this.isDismissed = false
  }

  render() {
    const markup = html`
      <slot></slot>
      <div class="spotlight" part="spotlight" aria-hidden="true"></div>
      <div class="card-wrapper" part="popover">
        <div class="card" part="card" role="dialog" aria-modal="true"
             aria-labelledby="${this._tourId}-title" aria-describedby="${this._tourId}-body" tabindex="-1">
          <div class="card-header">
            <slot name="step-title">
              <h3 class="card-title" id="${this._tourId}-title" part="title"></h3>
            </slot>
            <button class="skip-btn" part="skip-button" type="button" data-action="skip">&#x2715;</button>
          </div>
          <div class="card-counter" part="counter"></div>
          <div class="progress-dots" part="dots"></div>
          <div class="card-body" part="body" id="${this._tourId}-body">
            <slot name="step-body"><p class="card-body-text"></p></slot>
          </div>
          <div class="card-nav" part="navigation">
            <slot name="navigation">
              <button class="nav-btn" part="back-button" type="button" data-action="back"></button>
              <button class="nav-btn primary" part="next-button" type="button" data-action="next"></button>
            </slot>
          </div>
          <div class="tour-status" aria-live="polite" aria-atomic="true"></div>
        </div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._spotlightEl = this.$(".spotlight")
    this._cardWrapperEl = this.$(".card-wrapper")
    this._cardEl = this.$(".card")
    this._statusEl = this.$(".tour-status")

    this.listen(this._cardEl, "click", this._onCardClick.bind(this))
    this.listen(this._cardEl, "keydown", this._onCardKeydown.bind(this))

    this._applyLabels()

    if (this.hasAttribute("active") === true) {
      this._beginTour()
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._cardEl === undefined || this._cardEl === null) {
      return
    }

    if (name === "active") {
      if (newValue !== null && this._running === false) {
        this._beginTour()
      } else if (newValue === null && this._running === true) {
        this._endTour()
      }
    } else if (name === "current-step") {
      /*
       * Only a real change from outside moves the tour: the component's own
       * writes and re-assignments of the same value are ignored, so showing
       * a step can never re-enter itself.
       */
      if (oldValue === newValue || this._syncingStep === true || this._running === false) {
        return
      }
      const index = parseInt(newValue || "0", 10)
      this._goTo(Number.isFinite(index) === true ? index : 0)
    } else if (name === "skip-label" || name === "back-label" || name === "next-label" || name === "done-label") {
      this._applyLabels()
    } else if (name === "scroll-lock") {
      if (this._overlay !== null) {
        this._overlay.setAttribute("scroll-lock", this._scrollLockWanted() === true ? "true" : "false")
      }
    } else if (name === "variant") {
      /* The step on screen is re-anchored (or centred) in place. */
      if (this._running === true && this._currentIndex >= 0) {
        this._currentTarget = this._targetOf(this._steps[this._currentIndex])
        this._trackTarget(this._currentTarget)
        this._reposition()
      }
    } else if (this._running === true && this._currentIndex >= 0) {
      this._updateCardContent(this._currentIndex, this._steps[this._currentIndex])
      this._reposition()
    }
    return
  }

  onDisconnected() {
    /* Removed while running: release everything without events or refocus. */
    if (this._running === true) {
      this._running = false
      this._releaseTour()
    }
    return
  }

  /* ----- labels ----- */

  _applyLabels() {
    const skipBtn = this.$("[data-action='skip']")
    skipBtn.setAttribute("aria-label", this.getAttribute("skip-label") || t("mj.tour.skip"))

    const backBtn = this.$("[data-action='back']")
    backBtn.textContent = this.getAttribute("back-label") || t("mj.tour.back")

    this._applyNextLabel()
    return
  }

  _applyNextLabel() {
    const nextBtn = this.$("[data-action='next']")
    const isLast = this._currentIndex >= 0 && this._currentIndex === this._steps.length - 1
    nextBtn.textContent = isLast === true
      ? (this.getAttribute("done-label") || t("mj.tour.done"))
      : (this.getAttribute("next-label") || t("mj.tour.next"))
    return
  }

  /* ----- lifecycle of a run ----- */

  /* Take `active` back without persisting anything or emitting events. */
  _withdrawActive() {
    if (this.hasAttribute("active") === true) {
      this.removeAttribute("active")
    }
    return
  }

  _isSuppressedByStorage() {
    let suppressed = false
    const storageKey = this.getAttribute("storage-key")
    if (storageKey !== null && storageKey.length > 0) {
      try {
        const data = JSON.parse(localStorage.getItem(storageKey) || "{}")
        suppressed = data !== null && (data.dismissed === true || data.completed === true)
      } catch (err) {
        /* storage unavailable or unreadable: run the tour */
      }
    }
    return suppressed
  }

  _beginTour() {
    if (this._running === true || this.isConnected === false) {
      return
    }

    /* A tour that does not start leaves no card on the screen. */
    if (this._isSuppressedByStorage() === true) {
      this._withdrawActive()
      return
    }
    if (this._steps.length === 0) {
      console.warn("<mj-tour>: no steps defined")
      this._withdrawActive()
      return
    }

    this._running = true
    this._currentIndex = -1
    this._preTourFocus = deepActiveElement()

    /* Spotlight first, then backdrop and card, so they stack in this order. */
    showInTopLayer(this._spotlightEl)
    this._showOverlay()

    this._layer = pushLayer({
      surface: this._cardWrapperEl,
      modal: true,
      onEscape: () => {
        this._skipTour()
      }
    })
    this._trapDispose = trapFocus(this._cardEl, this._stepFocusTarget(), { contain: true })

    window.addEventListener("scroll", this._onViewportChange, true)
    window.addEventListener("resize", this._onViewportChange)

    const parsed = parseInt(this.getAttribute("current-step") || "0", 10)
    const startStep = Number.isFinite(parsed) === true ? parsed : 0

    this.emit("mj-tour-start", { totalSteps: this._steps.length })
    this._goTo(Math.max(0, Math.min(startStep, this._steps.length - 1)))
    return
  }

  /* Undo everything a run set up. */
  _releaseTour() {
    this._stopTracking()
    window.removeEventListener("scroll", this._onViewportChange, true)
    window.removeEventListener("resize", this._onViewportChange)

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
    if (this._spotlightEl !== null) {
      removeFromTopLayer(this._spotlightEl)
    }
    this._currentTarget = null
    return
  }

  _endTour() {
    if (this._running === false) {
      return
    }
    this._running = false
    this._releaseTour()

    const restoreEl = this._preTourFocus
    this._preTourFocus = null
    if (restoreEl !== null && restoreEl.isConnected === true && typeof restoreEl.focus === "function") {
      restoreEl.focus()
    }
    return
  }

  _skipTour() {
    if (this._running === false) {
      return
    }
    const step = this._currentIndex
    this.isDismissed = true
    this._persistState()
    this._withdrawActive()
    this._endTour()

    this.emit("mj-tour-skip", { step: step })
    return
  }

  _completeTour() {
    if (this._running === false) {
      return
    }
    this.isComplete = true
    this._persistState()
    this._withdrawActive()
    this._endTour()

    this.emit("mj-tour-complete", { totalSteps: this._steps.length })
    return
  }

  _persistState() {
    const storageKey = this.getAttribute("storage-key")
    if (storageKey === null || storageKey.length === 0) {
      return
    }
    try {
      const data = {
        dismissed: this.isDismissed,
        completed: this.isComplete
      }
      localStorage.setItem(storageKey, JSON.stringify(data))
    } catch (err) {
      /* storage unavailable */
    }
    return
  }

  /*
   * `scroll-lock` is a boolean attribute like every other in the library:
   * present (any value but "false") locks page scrolling while the tour runs.
   */
  _scrollLockWanted() {
    const value = this.getAttribute("scroll-lock")
    const wanted = value !== null && value !== "false"
    return wanted
  }

  /*
   * The backdrop. Only the spotlight's shadow dims the page, so the overlay
   * is the invisible "block" variant: it keeps pointer events off the page,
   * makes everything but the card inert and stacks the card in the top
   * layer. Scroll lock follows the `scroll-lock` attribute (off by default:
   * the spotlight follows the page when it scrolls), also while the tour runs.
   */
  _showOverlay() {
    if (this._overlay !== null) {
      return
    }
    const overlay = document.createElement("mj-overlay")
    overlay.surface = this._cardWrapperEl
    overlay.setAttribute("variant", "block")
    overlay.setAttribute("top-layer", "")
    overlay.setAttribute("scroll-lock", this._scrollLockWanted() === true ? "true" : "false")
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

  /* ----- steps ----- */

  /* True for `variant="floating"`: every card centred, targets ignored. */
  _isFloating() {
    const floating = this.getAttribute("variant") === "floating"
    return floating
  }

  /* The element a step is anchored to; null for a centred step. */
  _targetOf(step) {
    let target = null
    const wantsTarget = step.targetId !== undefined && step.targetId !== null && String(step.targetId).length > 0
    if (wantsTarget === true && this._isFloating() === false) {
      target = document.getElementById(String(step.targetId))
    }
    return target
  }

  _hasMissingTarget(step) {
    const wantsTarget = step.targetId !== undefined && step.targetId !== null && String(step.targetId).length > 0
    const missing = wantsTarget === true && this._isFloating() === false && this._targetOf(step) === null
    return missing
  }

  /*
   * The control a step focuses: the last control of the navigation row
   * (built-in Next / Done, or the slotted forward button), a slotted control
   * with `autofocus` first, and the card when there is nothing to focus.
   */
  _stepFocusTarget() {
    let target = this._cardEl
    const navigationRow = this.$(".card-nav")

    if (navigationRow !== null) {
      const focusable = getFocusable(navigationRow)
      const preferred = focusable.find((element) => element.hasAttribute("autofocus") === true)
      if (preferred !== undefined) {
        target = preferred
      } else if (focusable.length > 0) {
        target = focusable[focusable.length - 1]
      }
    }
    return target
  }

  /*
   * Move to step `index`. Steps whose target is missing are skipped in the
   * direction of travel; running past the last step completes the tour.
   */
  _goTo(index) {
    if (this._running === false) {
      return
    }

    const direction = index < this._currentIndex ? -1 : 1
    let candidate = index

    while (candidate >= 0 && candidate < this._steps.length && this._hasMissingTarget(this._steps[candidate]) === true) {
      console.warn(`<mj-tour>: target "${this._steps[candidate].targetId}" not found, skipping step`)
      candidate = candidate + direction
    }

    if (candidate >= this._steps.length) {
      this._completeTour()
      return
    }
    if (candidate < 0) {
      this._syncStepAttribute()
      return
    }

    this._showStep(candidate)
    return
  }

  /* Write `current-step` without the attribute handler reacting to it. */
  _syncStepAttribute() {
    if (this._currentIndex < 0) {
      return
    }
    const value = String(this._currentIndex)
    if (this.getAttribute("current-step") !== value) {
      this._syncingStep = true
      try {
        this.setAttribute("current-step", value)
      } finally {
        this._syncingStep = false
      }
    }
    return
  }

  _showStep(index) {
    const step = this._steps[index]
    const proceed = this.emit("mj-tour-step", {
      step: index,
      totalSteps: this._steps.length,
      stepDef: step
    }, { cancelable: true })

    if (proceed === false) {
      /* Vetoed: stay where we are, and say so in the attribute. */
      this._syncStepAttribute()
      return
    }

    this._currentIndex = index
    this._syncStepAttribute()

    const targetEl = this._targetOf(step)
    this._currentTarget = targetEl

    this._updateCardContent(index, step)
    this._trackTarget(targetEl)

    if (targetEl !== null) {
      const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches
      targetEl.scrollIntoView({ block: "center", behavior: reduced === true ? "instant" : "smooth" })
      this._reposition()
      this._waitForScrollToSettle()
    } else {
      this._reposition()
    }

    this._stepFocusTarget().focus()

    if (this._statusEl !== null) {
      this._statusEl.textContent = `${this._counterText(index)}: ${this._text(step.title)}`
    }
    return
  }

  _text(value) {
    const text = value !== undefined && value !== null ? String(value) : ""
    return text
  }

  _counterText(index) {
    let text = ""
    const counterFmt = this.getAttribute("counter-format")
    if (counterFmt !== null && counterFmt.length > 0) {
      text = counterFmt
        .replace("{current}", String(index + 1))
        .replace("{total}", String(this._steps.length))
    } else {
      text = t("mj.tour.counter", { current: index + 1, total: this._steps.length })
    }
    return text
  }

  /* ----- positioning ----- */

  _reposition() {
    if (this._running === false || this._currentIndex < 0) {
      return
    }

    const step = this._steps[this._currentIndex]
    const targetEl = this._currentTarget

    if (targetEl !== null && targetEl.isConnected === true) {
      this._positionSpotlight(targetEl)
      this._positionCard(targetEl, step.placement || "bottom-start")
    } else {
      this._spotlightEl.setAttribute("data-centred", "")
      this._spotlightEl.style.top = ""
      this._spotlightEl.style.left = ""
      this._spotlightEl.style.width = ""
      this._spotlightEl.style.height = ""
      this._centerCard()
    }
    return
  }

  /* Scroll and resize updates are coalesced into one per animation frame. */
  _scheduleReposition() {
    if (this._repositionFrame !== null) {
      return
    }
    this._repositionFrame = window.requestAnimationFrame(() => {
      this._repositionFrame = null
      this._reposition()
    })
    return
  }

  /*
   * A smooth scroll moves the target for a while after the step appears.
   * Scroll events keep the spotlight on it; once the scroll ends (or after
   * SCROLL_SETTLE_MS without a scrollend event) it is positioned once more.
   */
  _waitForScrollToSettle() {
    if (this._settleTimer !== null) {
      window.clearTimeout(this._settleTimer)
    }
    const settle = () => {
      window.removeEventListener("scrollend", settle, true)
      if (this._settleTimer !== null) {
        window.clearTimeout(this._settleTimer)
        this._settleTimer = null
      }
      this._reposition()
    }
    window.addEventListener("scrollend", settle, { capture: true, once: true })
    this._settleTimer = window.setTimeout(settle, SCROLL_SETTLE_MS)
    return
  }

  _trackTarget(targetEl) {
    if (this._resizeObserver !== null) {
      this._resizeObserver.disconnect()
      this._resizeObserver = null
    }

    if (targetEl !== null && typeof ResizeObserver === "function") {
      this._resizeObserver = new ResizeObserver(() => {
        this._scheduleReposition()
      })
      this._resizeObserver.observe(targetEl)
      this._resizeObserver.observe(this._cardEl)
    }
    return
  }

  _spotlightPadding() {
    const parsed = parseInt(this.getAttribute("spotlight-padding") || "", 10)
    const padding = Number.isFinite(parsed) === true ? parsed : 8
    return padding
  }

  _positionSpotlight(targetEl) {
    const padding = this._spotlightPadding()
    const rect = targetEl.getBoundingClientRect()

    this._spotlightEl.removeAttribute("data-centred")
    this._spotlightEl.style.top = `${rect.top - padding}px`
    this._spotlightEl.style.left = `${rect.left - padding}px`
    this._spotlightEl.style.width = `${rect.width + padding * 2}px`
    this._spotlightEl.style.height = `${rect.height + padding * 2}px`
    return
  }

  /*
   * Place the card next to its target with the overlay engine: logical
   * start/end follow the reading direction, the alignment suffix is
   * honoured, and the card flips and shifts to stay in the viewport.
   */
  _positionCard(targetEl, placement) {
    /* A centred step before this one left a transform behind. */
    this._cardWrapperEl.style.transform = ""

    position(this._cardWrapperEl, targetEl, {
      placement: toOverlayPlacement(placement),
      offset: this._spotlightPadding() + CARD_OFFSET,
      padding: CARD_OFFSET,
      topLayer: false
    })
    this._cardWrapperEl.style.zIndex = ""
    return
  }

  _centerCard() {
    this._cardWrapperEl.style.top = "50%"
    this._cardWrapperEl.style.left = "50%"
    this._cardWrapperEl.style.transform = "translate(-50%, -50%)"
    return
  }

  _stopTracking() {
    if (this._resizeObserver !== null) {
      this._resizeObserver.disconnect()
      this._resizeObserver = null
    }
    if (this._repositionFrame !== null) {
      window.cancelAnimationFrame(this._repositionFrame)
      this._repositionFrame = null
    }
    if (this._settleTimer !== null) {
      window.clearTimeout(this._settleTimer)
      this._settleTimer = null
    }
    return
  }

  /* ----- card content ----- */

  _updateCardContent(index, step) {
    const titleEl = this._cardEl.querySelector(".card-title")
    if (titleEl !== null) {
      titleEl.textContent = this._text(step.title)
    }

    /* The text lives in the slot's fallback, so a slotted body still projects. */
    const bodyText = this._cardEl.querySelector(".card-body-text")
    if (bodyText !== null) {
      bodyText.textContent = this._text(step.body)
    }

    const counterEl = this._cardEl.querySelector("[part='counter']")
    if (counterEl !== null) {
      const showCounter = this.getAttribute("show-counter") !== "false"
      counterEl.textContent = showCounter === true ? this._counterText(index) : ""
      counterEl.hidden = showCounter === false
    }

    const dotsEl = this._cardEl.querySelector("[part='dots']")
    if (dotsEl !== null) {
      const showDots = this.getAttribute("show-progress-dots") !== "false"
      dotsEl.textContent = ""
      if (showDots === true) {
        for (let i = 0; i < this._steps.length; i = i + 1) {
          const dot = document.createElement("span")
          dot.className = "dot"
          dot.setAttribute("part", "dot")
          dot.setAttribute("aria-hidden", "true")
          dot.setAttribute("data-active", i === index ? "true" : "false")
          dotsEl.appendChild(dot)
        }
      }
      dotsEl.hidden = showDots === false
    }

    const backBtn = this._cardEl.querySelector("[data-action='back']")
    if (backBtn !== null) {
      backBtn.hidden = index === 0
    }

    this._applyNextLabel()
    return
  }

  /* ----- events ----- */

  _next() {
    const nextIdx = this._currentIndex + 1
    if (nextIdx >= this._steps.length) {
      this._completeTour()
    } else {
      this.emit("mj-tour-next", { step: nextIdx, totalSteps: this._steps.length })
      this._goTo(nextIdx)
    }
    return
  }

  _back() {
    if (this._currentIndex > 0) {
      const prevIdx = this._currentIndex - 1
      this.emit("mj-tour-back", { step: prevIdx, totalSteps: this._steps.length })
      this._goTo(prevIdx)
    }
    return
  }

  _onCardClick(event) {
    const btn = event.target.closest("[data-action]")
    if (btn === null || btn.getRootNode() !== this.shadowRoot) {
      return
    }
    const action = btn.getAttribute("data-action")

    if (action === "next") {
      this._next()
    } else if (action === "back") {
      this._back()
    } else if (action === "skip") {
      this._skipTour()
    }
    return
  }

  _onCardKeydown(event) {
    if (event.key === "Escape") {
      const mine = claimEscape(event, this._layer)
      event.preventDefault()
      if (mine === true) {
        this._skipTour()
      }
      return
    }

    /* The arrow pointing to the inline end goes forward (ArrowLeft in RTL). */
    const rtl = window.getComputedStyle(this._cardEl).direction === "rtl"
    const forwardKey = rtl === true ? "ArrowLeft" : "ArrowRight"
    const backwardKey = rtl === true ? "ArrowRight" : "ArrowLeft"

    if (event.key === forwardKey) {
      event.preventDefault()
      if (this._currentIndex < this._steps.length - 1) {
        this._next()
      }
    } else if (event.key === backwardKey) {
      event.preventDefault()
      this._back()
    }
    return
  }

  /* Scriptable API */

  /*
   * The steps. An accessor (not a plain field) so that a value assigned
   * before the element was upgraded is picked up. Assigning steps while the
   * tour runs re-shows the current step (or completes it when it is gone).
   */
  get steps() {
    return this._steps
  }

  set steps(value) {
    this._steps = Array.isArray(value) ? value.filter((step) => step !== null && typeof step === "object") : []

    if (this._running === true) {
      if (this._steps.length === 0) {
        this._withdrawActive()
        this._endTour()
      } else {
        this._goTo(Math.min(Math.max(this._currentIndex, 0), this._steps.length - 1))
      }
    } else if (this.hasAttribute("active") === true && this._cardEl !== null) {
      /* `active` was set before there were steps: start now. */
      this._beginTour()
    }
    return
  }

  get active() {
    return this.hasAttribute("active")
  }

  set active(value) {
    this.reflectBoolean("active", value === true)
    return
  }

  get totalSteps() {
    return this._steps.length
  }

  start() {
    this.isDismissed = false
    this.isComplete = false
    if (this._running === true) {
      this._goTo(0)
      return
    }
    this._syncingStep = true
    try {
      this.setAttribute("current-step", "0")
    } finally {
      this._syncingStep = false
    }
    this.setAttribute("active", "")
    return
  }

  next() {
    if (this._running === true) {
      this._next()
    }
    return
  }

  back() {
    if (this._running === true) {
      this._back()
    }
    return
  }

  skip() {
    this._skipTour()
    return
  }

  reset() {
    this.isDismissed = false
    this.isComplete = false
    const storageKey = this.getAttribute("storage-key")
    if (storageKey !== null && storageKey.length > 0) {
      try {
        localStorage.removeItem(storageKey)
      } catch (err) {
        /* storage unavailable */
      }
    }
    return
  }
}
