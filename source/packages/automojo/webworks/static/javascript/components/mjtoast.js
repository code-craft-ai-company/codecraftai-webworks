/*
 * mjtoast.js
 *
 * <mj-toast> -- transient, non-modal notification with auto-dismiss and
 * optional countdown progress bar. Severity drives icon, color, and
 * live-region politeness.
 */

import { MjElement } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";
import { t } from "../core/intl.js";

const ICONS = {
  info:    `<svg aria-hidden="true" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/></svg>`,
  success: `<svg aria-hidden="true" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>`,
  warning: `<svg aria-hidden="true" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>`,
  error:   `<svg aria-hidden="true" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>`
};

const STYLES = `
:host { display: block; }
:host(:not([open])) { display: none; }

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
.title:empty { display: none; }
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
  transform-origin: inline-start center;
  transition: width linear;
}
:host(:not([auto-dismiss])) .progress-bar,
:host([auto-dismiss="0"]) .progress-bar { display: none; }
`;

const MIN_DISMISS_MS = 1000;

export class MjToast extends MjElement {
  static tagName = "mj-toast";
  static styles = STYLES;
  static watched = ["severity", "open", "auto-dismiss", "heading", "no-icon"];

  constructor() {
    super()
    this._timer = null
    this._startTime = null
    this._remaining = Infinity
    this._paused = false
  }

  render() {
    const severity = this.getAttribute("severity") || "info"
    const heading = this.getAttribute("heading") || ""
    const markup = `
      <div class="container" part="container">
        <span class="icon" part="icon"><slot name="icon">${ICONS[severity] || ICONS.info}</slot></span>
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
    this.listen(this._dismissBtn, "click", () => { this._dismiss("user") })
    this.listen(this, "pointerenter", this.pauseTimer.bind(this))
    this.listen(this, "pointerleave", this.resumeTimer.bind(this))
    this.listen(this, "focusin", this.pauseTimer.bind(this))
    this.listen(this, "focusout", this.resumeTimer.bind(this))
    this.listen(this, "keydown", this._onKeyDown.bind(this))
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "open") {
      if (newValue !== null) {
        this._onOpen()
      }
    }
    return
  }

  _onOpen() {
    const severity = this.getAttribute("severity") || "info"
    const politeness = severity === "error" ? "assertive" : "polite"
    const text = this.textContent.trim()
    if (text.length > 0) {
      announce(text, politeness)
    }
    this.emit("mj-toast-open", { severity: severity })

    let duration = parseInt(this.getAttribute("auto-dismiss") || "0", 10)
    if (duration > 0) {
      if (duration < MIN_DISMISS_MS) {
        console.warn("<mj-toast> auto-dismiss clamped to minimum 1000ms")
        duration = MIN_DISMISS_MS
      }
      this._remaining = duration
      this._startAutoTimer()
    }
    return
  }

  _startAutoTimer() {
    this._clearTimer()
    if (this._paused === true || this._remaining <= 0) {
      return
    }
    this._startTime = performance.now()
    const duration = this._getAttribute("auto-dismiss")
    const totalDuration = parseInt(duration || "0", 10)

    if (this._progressFill !== null && totalDuration > 0) {
      const pct = (this._remaining / totalDuration) * 100
      this._progressFill.style.width = `${pct}%`
      this._progressFill.style.transitionDuration = `${this._remaining}ms`
      requestAnimationFrame(() => {
        this._progressFill.style.width = "0%"
      })
    }

    this._timer = setTimeout(() => {
      this._dismiss("auto")
    }, this._remaining)
    return
  }

  _getAttribute(name) {
    return this.getAttribute(name)
  }

  _clearTimer() {
    if (this._timer !== null) {
      clearTimeout(this._timer)
      this._timer = null
    }
    return
  }

  pauseTimer() {
    if (this._timer === null || this._paused === true) {
      return
    }
    this._paused = true
    this.setAttribute("data-paused", "")
    const elapsed = performance.now() - this._startTime
    this._remaining = Math.max(0, this._remaining - elapsed)
    this._clearTimer()
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

  _dismiss(reason) {
    const severity = this.getAttribute("severity") || "info"
    const proceed = this.emit("mj-toast-dismiss", { severity: severity, reason: reason }, { cancelable: true })
    if (proceed === false) {
      return
    }
    this._clearTimer()
    this.removeAttribute("open")
    const onEnd = () => { this.remove() }
    this.addEventListener("transitionend", onEnd, { once: true })
    setTimeout(onEnd, 350)
    return
  }

  _onKeyDown(event) {
    if (event.key === "Escape") {
      this._dismiss("user")
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

  get remainingTime() {
    return this._remaining
  }
}
