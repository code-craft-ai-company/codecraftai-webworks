/*
 * mjtoastregion.js
 *
 * <mj-toast-region> -- singleton placement and queuing manager for transient
 * notification toasts. Controls fixed-position region, enforces max-visible
 * limit, manages auto-dismiss with hover/focus pause, and sequences queued
 * toasts.
 */

import { MjElement, nextId } from "../core/mjelement.js";

const STYLES = `
:host {
  display: contents;
}

.region {
  position: fixed;
  display: flex;
  flex-direction: column;
  gap: var(--mj-toast-region-gap, var(--mj-space-3));
  z-index: var(--mj-layer-toast);
  pointer-events: none;
  list-style: none;
  margin: 0;
  padding: 0;
  max-width: var(--mj-toast-max-width, 24rem);
}

/* Placements */
:host([placement="bottom-end"]) .region,
:host(:not([placement])) .region {
  bottom: var(--mj-toast-region-offset-y, var(--mj-space-4));
  inset-inline-end: var(--mj-toast-region-offset-x, var(--mj-space-4));
  flex-direction: column-reverse;
}

:host([placement="bottom-start"]) .region {
  bottom: var(--mj-toast-region-offset-y, var(--mj-space-4));
  inset-inline-start: var(--mj-toast-region-offset-x, var(--mj-space-4));
  flex-direction: column-reverse;
}

:host([placement="bottom-center"]) .region {
  bottom: var(--mj-toast-region-offset-y, var(--mj-space-4));
  left: 50%; transform: translateX(-50%);
  flex-direction: column-reverse;
}

:host([placement="top-end"]) .region {
  top: var(--mj-toast-region-offset-y, var(--mj-space-4));
  inset-inline-end: var(--mj-toast-region-offset-x, var(--mj-space-4));
}

:host([placement="top-start"]) .region {
  top: var(--mj-toast-region-offset-y, var(--mj-space-4));
  inset-inline-start: var(--mj-toast-region-offset-x, var(--mj-space-4));
}

:host([placement="top-center"]) .region {
  top: var(--mj-toast-region-offset-y, var(--mj-space-4));
  left: 50%; transform: translateX(-50%);
}

.toast-item {
  pointer-events: all;
  display: flex;
  align-items: flex-start;
  gap: var(--mj-space-3);
  padding: var(--mj-space-3) var(--mj-space-4);
  background: var(--mj-surface-raised, var(--mj-surface));
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-md);
  box-shadow: var(--mj-elevation-2);
  color: var(--mj-text);
  font-size: var(--mj-font-size-sm);
  animation: mj-toast-in var(--mj-motion-medium) var(--mj-motion-ease) both;
}

.toast-item[data-dismissing] {
  animation: mj-toast-out var(--mj-motion-medium) var(--mj-motion-ease) both;
}

@keyframes mj-toast-in {
  from { opacity: 0; transform: translateY(0.5rem); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes mj-toast-out {
  from { opacity: 1; transform: translateY(0); }
  to   { opacity: 0; transform: translateY(0.5rem); }
}

.toast-severity {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: var(--mj-radius-circle);
  flex-shrink: 0;
  margin-top: 0.35rem;
}

.toast-item[data-severity="error"] .toast-severity   { background: var(--mj-color-danger); }
.toast-item[data-severity="warning"] .toast-severity { background: var(--mj-color-warning); }
.toast-item[data-severity="success"] .toast-severity { background: var(--mj-color-success); }
.toast-item[data-severity="info"] .toast-severity    { background: var(--mj-color-info); }

.toast-body { flex: 1; }
.toast-message { margin: 0; }
.toast-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: var(--mj-radius-md);
  cursor: pointer;
  color: var(--mj-text-muted);
  flex-shrink: 0;
  font-size: 0.75rem;
}

.toast-close:hover { background: var(--mj-bg-muted); color: var(--mj-text); }
.toast-close:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

@media (prefers-reduced-motion: reduce) {
  .toast-item, .toast-item[data-dismissing] { animation: none; }
}
`;

export class MjToastRegion extends MjElement {
  static tagName = "mj-toast-region";
  static styles = STYLES;
  static watched = ["placement", "max-visible"];

  constructor() {
    super()
    this._queue = []
    this._visible = []
    this._timers = new Map()
    this._regionEl = null
    this._paused = false
  }

  render() {
    const label = this.getAttribute("region-label") || "Notifications"
    const markup = `
      <ol class="region" part="region" role="region" aria-label="${label}" aria-live="polite" aria-atomic="false" aria-relevant="additions"></ol>
    `
    return markup
  }

  afterRender() {
    this._regionEl = this.$(".region")
    this.listen(this._regionEl, "pointerenter", this._onPointerEnter.bind(this))
    this.listen(this._regionEl, "pointerleave", this._onPointerLeave.bind(this))
    this.listen(this._regionEl, "focusin", this._onFocusIn.bind(this))
    this.listen(this._regionEl, "focusout", this._onFocusOut.bind(this))
    this.listen(this._regionEl, "keydown", this._onKeydown.bind(this))
    return
  }

  _onPointerEnter() {
    this._paused = true
    this._pauseTimers()
    return
  }

  _onPointerLeave() {
    this._paused = false
    this._resumeTimers()
    return
  }

  _onFocusIn() {
    this._paused = true
    this._pauseTimers()
    return
  }

  _onFocusOut(event) {
    const stillInside = this._regionEl.contains(event.relatedTarget)
    if (stillInside === false) {
      this._paused = false
      this._resumeTimers()
    }
    return
  }

  _onKeydown(event) {
    if (event.key === "Escape") {
      const focused = this._regionEl.querySelector(":focus")
      if (focused !== null) {
        const item = focused.closest(".toast-item")
        if (item !== null) {
          const toastId = item.dataset.toastId
          this._dismiss(toastId, "user")
        }
      }
    }
    return
  }

  _pauseTimers() {
    for (const [id, timerInfo] of this._timers.entries()) {
      if (timerInfo.timerId !== null) {
        window.clearTimeout(timerInfo.timerId)
        timerInfo.remaining = timerInfo.end - Date.now()
        timerInfo.timerId = null
      }
    }
    return
  }

  _resumeTimers() {
    for (const [id, timerInfo] of this._timers.entries()) {
      if (timerInfo.timerId === null && timerInfo.remaining > 0) {
        timerInfo.end = Date.now() + timerInfo.remaining
        timerInfo.timerId = window.setTimeout(() => {
          this._dismiss(id, "auto")
        }, timerInfo.remaining)
      }
    }
    return
  }

  _maxVisible() {
    const max = parseInt(this.getAttribute("max-visible") || "3", 10)
    return max
  }

  add(descriptor) {
    const id = descriptor.id || nextId("mj-toast")
    const item = Object.assign({}, descriptor, { id: id })

    this.emit("mj-toast-add", { id: id, descriptor: item })

    if (this._visible.length < this._maxVisible()) {
      this._show(item)
    } else {
      this._queue.push(item)
    }
    return id
  }

  _show(descriptor) {
    if (this._regionEl === null) {
      return
    }

    const severity = descriptor.severity || "info"
    const li = document.createElement("li")
    li.className = "toast-item"
    li.setAttribute("data-toast-id", descriptor.id)
    li.setAttribute("data-severity", severity)
    li.setAttribute("role", "listitem")

    li.innerHTML = `
      <span class="toast-severity" aria-hidden="true"></span>
      <div class="toast-body">
        <p class="toast-message">${descriptor.message || ""}</p>
      </div>
      <button class="toast-close" aria-label="Dismiss notification">&#x2715;</button>
    `

    const closeBtn = li.querySelector(".toast-close")
    if (closeBtn !== null) {
      closeBtn.addEventListener("click", () => {
        this._dismiss(descriptor.id, "user")
      })
    }

    const isAssertive = severity === "error" || severity === "warning"
    const forcePolite = this.getAttribute("polite") === "true" || this.hasAttribute("polite")
    if (isAssertive === true && forcePolite === false) {
      this._regionEl.setAttribute("aria-live", "assertive")
      window.setTimeout(() => {
        if (this._regionEl !== null) {
          this._regionEl.setAttribute("aria-live", "polite")
        }
      }, 100)
    }

    this._regionEl.appendChild(li)
    this._visible.push(descriptor)

    const duration = descriptor.duration === 0 ? 0 : (descriptor.duration || (severity === "error" ? 8000 : 5000))

    if (duration > 0) {
      const end = Date.now() + duration
      const timerId = window.setTimeout(() => {
        this._dismiss(descriptor.id, "auto")
      }, duration)
      this._timers.set(descriptor.id, { timerId: timerId, end: end, remaining: duration })
    }

    this.emit("mj-toast-show", { id: descriptor.id })
    return
  }

  _dismiss(toastId, reason) {
    const timerInfo = this._timers.get(toastId)
    if (timerInfo !== undefined) {
      if (timerInfo.timerId !== null) {
        window.clearTimeout(timerInfo.timerId)
      }
      this._timers.delete(toastId)
    }

    const li = this._regionEl !== null
      ? this._regionEl.querySelector(`[data-toast-id="${toastId}"]`)
      : null

    if (li !== null) {
      li.setAttribute("data-dismissing", "")
      const onEnd = () => {
        li.removeEventListener("animationend", onEnd)
        li.remove()
      }
      li.addEventListener("animationend", onEnd)

      window.setTimeout(() => {
        if (li.parentElement !== null) {
          li.remove()
        }
      }, 400)
    }

    const idx = this._visible.findIndex((v) => v.id === toastId)
    if (idx >= 0) {
      this._visible.splice(idx, 1)
    }

    this.emit("mj-toast-dismiss", { id: toastId, reason: reason })

    if (this._queue.length > 0 && this._visible.length < this._maxVisible()) {
      const next = this._queue.shift()
      this._show(next)
    }

    if (this._visible.length === 0 && this._queue.length === 0) {
      this.emit("mj-toast-queue-empty", {})
    }
    return
  }

  dismissAll() {
    const ids = this._visible.map((v) => v.id)
    for (let index = 0; index < ids.length; index = index + 1) {
      this._dismiss(ids[index], "api")
    }
    this._queue = []
    return
  }

  /* Read-only properties */

  get queue() {
    return this._queue.slice()
  }

  get visible() {
    return this._visible.slice()
  }

  get count() {
    return this._visible.length + this._queue.length
  }
}
