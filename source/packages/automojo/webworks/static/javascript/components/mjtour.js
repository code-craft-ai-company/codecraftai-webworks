/*
 * mjtour.js
 *
 * <mj-tour> -- sequences anchored popover coach-mark steps across page
 * elements to guide users through a feature or onboarding flow. Each step
 * spotlights a target element with a full-viewport overlay cutout.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";

const STYLES = `
:host {
  display: contents;
}

.spotlight {
  position: fixed;
  inset: 0;
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

:host(:not([active])) .spotlight { display: none; }

.card-wrapper {
  position: fixed;
  z-index: calc(var(--mj-layer-modal) + 1);
  pointer-events: auto;
}

:host(:not([active])) .card-wrapper { display: none; }

.card {
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
  margin-bottom: var(--mj-space-3);
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
  margin-bottom: var(--mj-space-4);
}

.card-counter {
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
  margin-bottom: var(--mj-space-3);
}

.progress-dots {
  display: flex;
  gap: var(--mj-space-1);
  margin-bottom: var(--mj-space-3);
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
}

.nav-btn.primary:hover { background: var(--mj-accent-hover); border-color: var(--mj-accent-hover); }
.nav-btn:hover:not(.primary) { background: var(--mj-bg-muted); }
.nav-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.nav-btn[hidden] { display: none; }

@media (prefers-reduced-motion: reduce) {
  .spotlight { transition: none; }
}
`;

export class MjTour extends MjElement {
  static tagName = "mj-tour";
  static styles = STYLES;
  static watched = ["active", "current-step", "variant", "show-progress-dots", "show-counter"];

  constructor() {
    super()
    this.steps = []
    this._spotlightEl = null
    this._cardWrapperEl = null
    this._cardEl = null
    this._resizeObserver = null
    this._preTourFocus = null
    this._overlay = null
    this.isComplete = false
    this.isDismissed = false
    this._tourId = nextId("mj-tour")
  }

  render() {
    const skipLabel = this.getAttribute("skip-label") || "Skip tour"
    const backLabel = this.getAttribute("back-label") || "Back"
    const nextLabel = this.getAttribute("next-label") || "Next"
    const doneLabel = this.getAttribute("done-label") || "Done"

    const markup = `
      <slot></slot>
      <div class="spotlight" part="spotlight" aria-hidden="true"></div>
      <div class="card-wrapper" part="popover">
        <div class="card" part="card" role="dialog" aria-modal="true"
             aria-labelledby="${this._tourId}-title" tabindex="-1">
          <div class="card-header">
            <slot name="step-title">
              <h3 class="card-title" id="${this._tourId}-title" part="title"></h3>
            </slot>
            <button class="skip-btn" part="skip-button"
                    aria-label="${skipLabel}" data-action="skip">&#x2715;</button>
          </div>
          <div class="card-counter" part="counter"></div>
          <div class="progress-dots" part="dots"></div>
          <div class="card-body" part="body">
            <slot name="step-body"></slot>
          </div>
          <div class="card-nav" part="navigation">
            <slot name="navigation">
              <button class="nav-btn" part="back-button" data-action="back">${backLabel}</button>
              <button class="nav-btn primary" part="next-button" data-action="next">${nextLabel}</button>
            </slot>
          </div>
        </div>
      </div>
      <div aria-live="polite" aria-atomic="true" style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;"></div>
    `
    return markup
  }

  afterRender() {
    this._spotlightEl = this.$(".spotlight")
    this._cardWrapperEl = this.$(".card-wrapper")
    this._cardEl = this.$(".card")
    this._statusEl = this.shadowRoot.querySelector("[aria-live]")

    this.listen(this._cardEl, "click", this._onCardClick.bind(this))
    this.listen(this._cardEl, "keydown", this._onCardKeydown.bind(this))

    if (this.hasAttribute("active") === true) {
      this._beginTour()
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "active" && this._cardEl !== null) {
      if (newValue !== null) {
        this._beginTour()
      } else {
        this._endTour()
      }
    }
    if (name === "current-step" && this.hasAttribute("active") === true && this._cardEl !== null) {
      this._showStep(parseInt(newValue || "0", 10))
    }
    return
  }

  onDisconnected() {
    this._stopTracking()
    this._hideOverlay()
    return
  }

  _beginTour() {
    const storageKey = this.getAttribute("storage-key")
    if (storageKey !== null && storageKey.length > 0) {
      try {
        const data = JSON.parse(localStorage.getItem(storageKey) || "{}")
        if (data.dismissed === true || data.completed === true) {
          return
        }
      } catch (err) {
        /* storage unavailable */
      }
    }

    if (this.steps.length === 0) {
      console.warn("<mj-tour>: no steps defined")
      return
    }

    this._preTourFocus = document.activeElement
    this._showOverlay()

    const startStep = parseInt(this.getAttribute("current-step") || "0", 10)
    this.emit("mj-tour-start", { totalSteps: this.steps.length })
    this._showStep(startStep)
    return
  }

  _showStep(index) {
    if (index < 0 || index >= this.steps.length) {
      return
    }

    const step = this.steps[index]
    const proceed = this.emit("mj-tour-step", {
      step: index,
      totalSteps: this.steps.length,
      stepDef: step
    }, { cancelable: true })

    if (proceed === false) {
      return
    }

    const targetEl = step.targetId ? document.getElementById(step.targetId) : null
    if (targetEl === null && step.targetId !== undefined) {
      console.warn(`<mj-tour>: target "${step.targetId}" not found, skipping step`)
      const next = index + 1
      if (next < this.steps.length) {
        this.setAttribute("current-step", String(next))
      } else {
        this._completeTour()
      }
      return
    }

    this.setAttribute("current-step", String(index))

    if (targetEl !== null) {
      const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches
      targetEl.scrollIntoView({ block: "center", behavior: reduced ? "instant" : "smooth" })

      requestAnimationFrame(() => {
        this._positionSpotlight(targetEl)
        this._positionCard(targetEl, step.placement || "bottom-start")
      })
    } else {
      this._centerCard()
      this._spotlightEl.style.display = "none"
    }

    this._updateCardContent(index, step)

    if (this._resizeObserver !== null) {
      this._resizeObserver.disconnect()
    }

    if (targetEl !== null && typeof ResizeObserver === "function") {
      this._resizeObserver = new ResizeObserver(() => {
        this._positionSpotlight(targetEl)
        this._positionCard(targetEl, step.placement || "bottom-start")
      })
      this._resizeObserver.observe(targetEl)
    }

    const nextBtn = this._cardEl.querySelector("[data-action='next']")
    if (nextBtn !== null) {
      nextBtn.focus()
    } else {
      this._cardEl.focus()
    }

    const counterFmt = this.getAttribute("counter-format") || "Step {current} of {total}"
    const counterText = counterFmt
      .replace("{current}", String(index + 1))
      .replace("{total}", String(this.steps.length))

    if (this._statusEl !== null) {
      this._statusEl.textContent = `${counterText}: ${step.title || ""}`
    }
    return
  }

  _positionSpotlight(targetEl) {
    if (this._spotlightEl === null) {
      return
    }
    const padding = parseInt(this.getAttribute("spotlight-padding") || "8", 10)
    const rect = targetEl.getBoundingClientRect()

    this._spotlightEl.style.top = `${rect.top - padding}px`
    this._spotlightEl.style.left = `${rect.left - padding}px`
    this._spotlightEl.style.width = `${rect.width + padding * 2}px`
    this._spotlightEl.style.height = `${rect.height + padding * 2}px`
    this._spotlightEl.style.display = ""
    return
  }

  _positionCard(targetEl, placement) {
    if (this._cardWrapperEl === null) {
      return
    }
    const padding = parseInt(this.getAttribute("spotlight-padding") || "8", 10)
    const rect = targetEl.getBoundingClientRect()
    const cardRect = this._cardEl.getBoundingClientRect()
    const offset = 12

    let top = 0
    let left = 0

    const side = placement.split("-")[0]

    if (side === "bottom") {
      top = rect.bottom + padding + offset
      left = rect.left
    } else if (side === "top") {
      top = rect.top - padding - offset - cardRect.height
      left = rect.left
    } else if (side === "end") {
      top = rect.top
      left = rect.right + padding + offset
    } else {
      top = rect.top
      left = rect.left - padding - offset - cardRect.width
    }

    const vw = window.innerWidth
    const vh = window.innerHeight

    if (left + cardRect.width > vw) {
      left = vw - cardRect.width - offset
    }
    if (left < offset) {
      left = offset
    }
    if (top + cardRect.height > vh) {
      top = vh - cardRect.height - offset
    }
    if (top < offset) {
      top = offset
    }

    this._cardWrapperEl.style.top = `${top}px`
    this._cardWrapperEl.style.left = `${left}px`
    return
  }

  _centerCard() {
    if (this._cardWrapperEl === null) {
      return
    }
    this._cardWrapperEl.style.top = "50%"
    this._cardWrapperEl.style.left = "50%"
    this._cardWrapperEl.style.transform = "translate(-50%, -50%)"
    return
  }

  _updateCardContent(index, step) {
    const titleEl = this._cardEl.querySelector(`#${this._tourId}-title`)
    if (titleEl !== null) {
      titleEl.textContent = step.title || ""
    }

    const bodySlot = this._cardEl.querySelector("[part='body']")
    if (bodySlot !== null && step.body !== undefined) {
      bodySlot.textContent = step.body
    }

    const counterEl = this._cardEl.querySelector("[part='counter']")
    if (counterEl !== null) {
      if (this.getAttribute("show-counter") !== "false") {
        const fmt = this.getAttribute("counter-format") || "Step {current} of {total}"
        counterEl.textContent = fmt
          .replace("{current}", String(index + 1))
          .replace("{total}", String(this.steps.length))
        counterEl.style.display = ""
      } else {
        counterEl.style.display = "none"
      }
    }

    const dotsEl = this._cardEl.querySelector("[part='dots']")
    if (dotsEl !== null) {
      if (this.getAttribute("show-progress-dots") !== "false") {
        dotsEl.innerHTML = ""
        for (let i = 0; i < this.steps.length; i = i + 1) {
          const dot = document.createElement("span")
          dot.className = "dot"
          dot.setAttribute("part", "dot")
          dot.setAttribute("aria-hidden", "true")
          dot.setAttribute("data-active", i === index ? "true" : "false")
          dotsEl.appendChild(dot)
        }
        dotsEl.style.display = ""
      } else {
        dotsEl.style.display = "none"
      }
    }

    const backBtn = this._cardEl.querySelector("[data-action='back']")
    if (backBtn !== null) {
      if (index === 0) {
        backBtn.hidden = true
      } else {
        backBtn.hidden = false
        backBtn.textContent = this.getAttribute("back-label") || "Back"
      }
    }

    const nextBtn = this._cardEl.querySelector("[data-action='next']")
    if (nextBtn !== null) {
      const isLast = index === this.steps.length - 1
      nextBtn.textContent = isLast
        ? (this.getAttribute("done-label") || "Done")
        : (this.getAttribute("next-label") || "Next")
    }
    return
  }

  _stopTracking() {
    if (this._resizeObserver !== null) {
      this._resizeObserver.disconnect()
      this._resizeObserver = null
    }
    return
  }

  _showOverlay() {
    if (this._overlay !== null) {
      return
    }
    const overlay = document.createElement("mj-overlay")
    overlay.setAttribute("visible", "")
    overlay.setAttribute("scroll-lock", "false")
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

  _endTour() {
    this._stopTracking()
    this._hideOverlay()

    const restoreEl = this._preTourFocus
    this._preTourFocus = null
    if (restoreEl !== null && typeof restoreEl.focus === "function") {
      restoreEl.focus()
    }
    return
  }

  _skipTour() {
    this.isDismissed = true
    this._persistState()
    this._stopTracking()
    this.removeAttribute("active")

    const currentStep = parseInt(this.getAttribute("current-step") || "0", 10)
    this.emit("mj-tour-skip", { step: currentStep })
    this._endTour()
    return
  }

  _completeTour() {
    this.isComplete = true
    this._persistState()
    this._stopTracking()
    this.removeAttribute("active")

    this.emit("mj-tour-complete", { totalSteps: this.steps.length })
    this._endTour()
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

  _onCardClick(event) {
    const btn = event.target.closest("[data-action]")
    if (btn === null) {
      return
    }
    const action = btn.getAttribute("data-action")
    const currentStep = parseInt(this.getAttribute("current-step") || "0", 10)

    if (action === "next") {
      const isLast = currentStep === this.steps.length - 1
      if (isLast === true) {
        this._completeTour()
      } else {
        this.emit("mj-tour-next", { step: currentStep + 1, totalSteps: this.steps.length })
        this.setAttribute("current-step", String(currentStep + 1))
      }
    } else if (action === "back") {
      if (currentStep > 0) {
        this.emit("mj-tour-back", { step: currentStep - 1, totalSteps: this.steps.length })
        this.setAttribute("current-step", String(currentStep - 1))
      }
    } else if (action === "skip") {
      this._skipTour()
    }
    return
  }

  _onCardKeydown(event) {
    if (event.key === "Escape") {
      this._skipTour()
      return
    }

    const currentStep = parseInt(this.getAttribute("current-step") || "0", 10)
    if (event.key === "ArrowRight") {
      const isLast = currentStep === this.steps.length - 1
      if (isLast === false) {
        this.setAttribute("current-step", String(currentStep + 1))
      }
    } else if (event.key === "ArrowLeft") {
      if (currentStep > 0) {
        this.setAttribute("current-step", String(currentStep - 1))
      }
    }
    return
  }

  /* Scriptable API */

  get active() {
    return this.hasAttribute("active")
  }

  set active(value) {
    this.reflectBoolean("active", value === true)
    return
  }

  get totalSteps() {
    return this.steps.length
  }

  start() {
    this.isDismissed = false
    this.isComplete = false
    this.setAttribute("current-step", "0")
    this.setAttribute("active", "")
    return
  }

  next() {
    const current = parseInt(this.getAttribute("current-step") || "0", 10)
    const nextIdx = current + 1
    if (nextIdx < this.steps.length) {
      this.setAttribute("current-step", String(nextIdx))
    } else {
      this._completeTour()
    }
    return
  }

  back() {
    const current = parseInt(this.getAttribute("current-step") || "0", 10)
    if (current > 0) {
      this.setAttribute("current-step", String(current - 1))
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
