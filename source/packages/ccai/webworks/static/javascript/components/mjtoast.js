/*
 * mjtoast.js
 *
 * <mj-toast> -- transient, non-modal notification with auto-dismiss and
 * optional countdown progress bar. Severity drives icon, color, and
 * live-region politeness.
 *
 * Placement: a toast inside <mj-toast-region> is laid out by the region. A
 * standalone toast is a fixed overlay at the viewport edge named by
 * `placement` (default "bottom-end"); `placement="inline"` leaves it in the
 * normal flow for pages that position toasts themselves.
 */

import { MjElement } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";
import { t } from "../core/intl.js";
import { html, raw } from "../core/html.js";

const ICONS = {
  info:    `<svg aria-hidden="true" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/></svg>`,
  success: `<svg aria-hidden="true" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>`,
  warning: `<svg aria-hidden="true" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>`,
  error:   `<svg aria-hidden="true" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>`
};

const STYLES = `
:host { display: block; }
:host(:not([open])) { display: none; }

/* Standalone (no mj-toast-region ancestor): a fixed overlay at the placement edge. */
:host([data-standalone]) {
  position: fixed;
  z-index: var(--mj-toast-z-index, var(--mj-layer-toast));
  inset-block-end: var(--mj-toast-offset-y, var(--mj-space-4));
  inset-inline-end: var(--mj-toast-offset-x, var(--mj-space-4));
}
:host([data-standalone][placement^="top"]) {
  inset-block-end: auto;
  inset-block-start: var(--mj-toast-offset-y, var(--mj-space-4));
}
:host([data-standalone][placement$="start"]) {
  inset-inline-end: auto;
  inset-inline-start: var(--mj-toast-offset-x, var(--mj-space-4));
}
:host([data-standalone][placement="top"]),
:host([data-standalone][placement="bottom"]) {
  inset-inline-end: auto;
  inset-inline-start: 50%;
  translate: -50% 0;
}
:host([data-standalone][placement="top"]:dir(rtl)),
:host([data-standalone][placement="bottom"]:dir(rtl)) { translate: 50% 0; }

:host([open]) .container {
  animation: mj-toast-enter var(--mj-toast-animation-duration, var(--mj-motion-medium)) var(--mj-motion-ease);
}
@keyframes mj-toast-enter {
  from { opacity: 0; transform: translateY(var(--mj-space-2)); }
  to   { opacity: 1; transform: translateY(0); }
}

.container {
  display: flex; align-items: flex-start;
  gap: var(--mj-space-3);
  padding-block: var(--mj-toast-padding-block, var(--mj-space-3));
  padding-inline: var(--mj-toast-padding-inline, var(--mj-space-4));
  min-width: var(--mj-toast-min-width, 18rem);
  max-width: var(--mj-toast-max-width, 28rem);
  background: var(--mj-toast-bg, var(--mj-surface-raised));
  border: 1px solid var(--mj-toast-border-color, var(--mj-border));
  border-radius: var(--mj-toast-border-radius, var(--mj-radius-lg));
  box-shadow: var(--mj-toast-shadow, var(--mj-elevation-3));
  color: var(--mj-toast-color, var(--mj-text));
  position: relative; overflow: hidden;
}

:host([severity="info"])    .icon { color: var(--mj-color-info); }
:host([severity="success"]) .icon { color: var(--mj-color-success); }
:host([severity="warning"]) .icon { color: var(--mj-color-warning); }
:host([severity="error"])   .icon { color: var(--mj-color-danger); }

.icon { flex-shrink: 0; width: 1.25rem; height: 1.25rem; margin-block-start: 0.125rem; }
.icon svg { width: 100%; height: 100%; }
:host([no-icon]) .icon { display: none; }

.body { flex: 1; min-width: 0; }
.title { font-weight: var(--mj-font-weight-medium); margin-block-end: var(--mj-space-1); }
.actions { margin-block-start: var(--mj-space-2); }

.dismiss {
  flex-shrink: 0; display: flex; align-items: center; justify-content: center;
  width: 1.75rem; height: 1.75rem;
  background: transparent; border: none; border-radius: var(--mj-radius-sm);
  cursor: pointer; color: var(--mj-text-muted); padding: 0; margin-block-start: -0.125rem;
}
.dismiss:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: var(--mj-focus-ring-offset); }
.dismiss:hover { background: var(--mj-bg-muted); }
.dismiss svg { width: 1rem; height: 1rem; }

.progress-bar {
  position: absolute; inset-block-end: 0; inset-inline-start: 0;
  height: 3px; width: 100%;
  background: var(--mj-border);
}
.progress-fill {
  height: 100%; width: 100%;
  background: var(--mj-toast-progress-color, var(--mj-accent));
  transition: width linear;
}
:host(:not([auto-dismiss])) .progress-bar,
:host([auto-dismiss="0"]) .progress-bar { display: none; }
`;

const MIN_DISMISS_MS = 1000;

export class MjToast extends MjElement {
  static tagName = "mj-toast";
  static styles = STYLES;
  static watched = ["severity", "open", "auto-dismiss", "heading", "no-icon", "placement"];

  constructor() {
    super()
    this._timer = null
    this._startTime = null
    this._remaining = Infinity
    this._paused = false

    this._dismissBtn = null
    this._progressFill = null

    /* Open state the component has acted on (announcement, event, timer). */
    this._openState = false

    /* Pending removal after a dismissal. */
    this._removeTimer = null
  }

  render() {
    const severity = this.getAttribute("severity") || "info"
    const heading = this.getAttribute("heading") || ""
    const markup = html`
      <div class="container" part="container">
        <span class="icon" part="icon"><slot name="icon">${raw(ICONS[severity] || ICONS.info)}</slot></span>
        <div class="body" part="content">
          <div class="title" part="title"><slot name="title">${heading}</slot></div>
          <div part="body"><slot></slot></div>
          <div class="actions" part="actions"><slot name="actions"></slot></div>
        </div>
        <button class="dismiss" part="dismiss" type="button" aria-label="${t("core.close")}">
          <svg aria-hidden="true" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/></svg>
        </button>
        <div class="progress-bar" part="progress"><div class="progress-fill"></div></div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._dismissBtn = this.$(".dismiss")
    this._progressFill = this.$(".progress-fill")
    this._iconSlot = this.$("slot[name='icon']")
    this._titleEl = this.$(".title")
    this._titleSlot = this.$("slot[name='title']")
    this._actionsEl = this.$(".actions")
    this._actionsSlot = this.$("slot[name='actions']")

    this.listen(this._dismissBtn, "click", () => { this._dismiss("user") })
    this.listen(this._actionsEl, "click", this._onActionClick.bind(this))
    this.listen(this._titleSlot, "slotchange", this._syncSections.bind(this))
    this.listen(this._actionsSlot, "slotchange", this._syncSections.bind(this))
    this.listen(this, "pointerenter", this.pauseTimer.bind(this))
    this.listen(this, "pointerleave", this.resumeTimer.bind(this))
    this.listen(this, "focusin", this.pauseTimer.bind(this))
    this.listen(this, "focusout", this.resumeTimer.bind(this))
    this.listen(this, "keydown", this._onKeyDown.bind(this))

    this._syncSections()
    return
  }

  onConnected() {
    /* Outside a toast region the toast places itself at the viewport edge. */
    const standalone = this.closest("mj-toast-region") === null && this.getAttribute("placement") !== "inline"
    this.toggleAttribute("data-standalone", standalone)

    if (this._openState === true && this.hasAttribute("open") === true) {
      /* Re-inserted while open: carry on with the time that was left. */
      this._paused = false
      this.removeAttribute("data-paused")
      this._startAutoTimer()
    } else {
      this._syncOpen()
    }
    return
  }

  onDisconnected() {
    /* No timer may fire for a toast that is no longer in the document. */
    this._holdTimer()
    if (this._removeTimer !== null) {
      clearTimeout(this._removeTimer)
      this._removeTimer = null
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._dismissBtn === undefined || this._dismissBtn === null) {
      return
    }

    if (name === "open") {
      this._syncOpen()
    }

    if (name === "auto-dismiss" && this._openState === true) {
      this._armTimer()
    }

    if (name === "severity" && this._iconSlot !== null) {
      /* Constant markup from the ICONS table. */
      this._iconSlot.innerHTML = ICONS[newValue] || ICONS.info
    }

    if (name === "heading") {
      this._titleSlot.textContent = newValue || ""
      this._syncSections()
    }

    if (name === "placement" && this._connected === true) {
      const standalone = this.closest("mj-toast-region") === null && newValue !== "inline"
      this.toggleAttribute("data-standalone", standalone)
    }
    return
  }

  /*
   * Act on the `open` attribute once per real change. The attribute may be
   * present before the first render and is delivered again afterwards, so
   * the state acted on is tracked in `_openState`.
   */
  _syncOpen() {
    const open = this.hasAttribute("open")
    if (open === this._openState) {
      return
    }
    this._openState = open

    if (open === true) {
      this._onOpen()
    } else {
      this._onClose()
    }
    return
  }

  _onOpen() {
    const severity = this.getAttribute("severity") || "info"
    const politeness = severity === "error" ? "assertive" : "polite"
    const heading = this.getAttribute("heading") || ""
    const text = `${heading} ${this.textContent}`.replace(/\s+/g, " ").trim()
    if (text.length > 0) {
      announce(text, politeness)
    }
    this.emit("mj-toast-open", { severity: severity })

    this._armTimer()
    return
  }

  /* `open` was removed: nothing may dismiss the hidden toast later. */
  _onClose() {
    this._clearTimer()
    this._paused = false
    this._remaining = Infinity
    this.removeAttribute("data-paused")
    return
  }

  /* The auto-dismiss duration in milliseconds; 0 when the toast is persistent. */
  _getDuration() {
    let duration = parseInt(this.getAttribute("auto-dismiss") || "0", 10)
    if (Number.isFinite(duration) === false || duration <= 0) {
      duration = 0
    } else if (duration < MIN_DISMISS_MS) {
      console.warn("<mj-toast> auto-dismiss clamped to minimum 1000ms")
      duration = MIN_DISMISS_MS
    }
    return duration
  }

  /* Start the countdown from the full `auto-dismiss` duration. */
  _armTimer() {
    this._clearTimer()

    const duration = this._getDuration()
    if (duration > 0) {
      this._remaining = duration
      this._startAutoTimer()
    } else {
      this._remaining = Infinity
    }
    return
  }

  _startAutoTimer() {
    this._clearTimer()
    const counting = Number.isFinite(this._remaining) === true && this._remaining > 0
    if (this._paused === true || counting === false) {
      return
    }
    this._startTime = performance.now()
    const totalDuration = this._getDuration()

    if (this._progressFill !== null && totalDuration > 0) {
      /*
       * Place the bar at the share of time that is left without animating,
       * then let it run down to empty over exactly that time.
       */
      const pct = Math.min(100, (this._remaining / totalDuration) * 100)
      this._progressFill.style.transitionDuration = "0ms"
      this._progressFill.style.width = `${pct}%`
      void this._progressFill.offsetWidth
      this._progressFill.style.transitionDuration = `${this._remaining}ms`
      this._progressFill.style.width = "0%"
    }

    this._timer = setTimeout(() => {
      this._timer = null
      this._dismiss("auto")
    }, this._remaining)
    return
  }

  _clearTimer() {
    if (this._timer !== null) {
      clearTimeout(this._timer)
      this._timer = null
    }
    return
  }

  /*
   * Stop the countdown, remember the time left and freeze the progress bar
   * where it is.
   */
  _holdTimer() {
    if (this._timer === null) {
      return
    }

    const elapsed = performance.now() - this._startTime
    this._remaining = Math.max(0, this._remaining - elapsed)
    this._clearTimer()

    if (this._progressFill !== null) {
      const frozenWidth = window.getComputedStyle(this._progressFill).width
      this._progressFill.style.transitionDuration = "0ms"
      this._progressFill.style.width = frozenWidth
    }
    return
  }

  pauseTimer() {
    if (this._timer === null || this._paused === true) {
      return
    }
    this._paused = true
    this.setAttribute("data-paused", "")
    this._holdTimer()
    return
  }

  resumeTimer() {
    if (this._paused === false) {
      return
    }
    this._paused = false
    this.removeAttribute("data-paused")
    this._startAutoTimer()
    return
  }

  /* Hide the title and actions wrappers (and their margins) while they are empty. */
  _syncSections() {
    if (this._titleEl === undefined || this._titleEl === null) {
      return
    }

    const heading = this.getAttribute("heading") || ""
    const hasTitle = heading.length > 0 || this._titleSlot.assignedNodes().length > 0
    const hasActions = this._actionsSlot.assignedNodes().length > 0

    this._titleEl.hidden = hasTitle === false
    this._actionsEl.hidden = hasActions === false
    return
  }

  /*
   * A slotted action (for example Undo) was activated: report it with the
   * `value` of the activated control, then dismiss the toast.
   */
  _onActionClick(event) {
    const path = event.composedPath()

    let action = null
    let found = false
    for (let index = 0; index < path.length; index = index + 1) {
      const node = path[index]
      if (node === this._actionsEl) {
        break
      }
      if (node.nodeType !== Node.ELEMENT_NODE) {
        continue
      }
      const isControl =
        node.localName === "button" ||
        node.localName === "a" ||
        node.localName.indexOf("-") >= 0 ||
        node.hasAttribute("value") === true
      if (isControl === true) {
        found = true
        action = node.getAttribute("value")
        if (action !== null) {
          break
        }
      }
    }

    if (found === false) {
      return
    }

    const severity = this.getAttribute("severity") || "info"
    this.emit("mj-toast-action", { severity: severity, action: action })
    this._dismiss("user")
    return
  }

  _dismiss(reason) {
    const severity = this.getAttribute("severity") || "info"
    const proceed = this.emit("mj-toast-dismiss", { severity: severity, reason: reason }, { cancelable: true })
    if (proceed === false) {
      return
    }
    this._clearTimer()
    this.removeAttribute("open")

    /* Removed shortly after, unless it was re-opened in the meantime. */
    if (this._removeTimer !== null) {
      clearTimeout(this._removeTimer)
    }
    this._removeTimer = setTimeout(() => {
      this._removeTimer = null
      if (this.hasAttribute("open") === false) {
        this.remove()
      }
    }, 350)
    return
  }

  _onKeyDown(event) {
    if (event.key === "Escape") {
      this._dismiss("user")
    }
    return
  }

  /* Dismiss the toast from script; fires mj-toast-dismiss with reason "api". */
  dismiss() {
    if (this.hasAttribute("open") === true) {
      this._dismiss("api")
    }
    return
  }

  get open() {
    return this.hasAttribute("open")
  }

  set open(value) {
    this.reflectBoolean("open", Boolean(value))
    return
  }

  get remainingTime() {
    return this._remaining
  }
}
