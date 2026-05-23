/*
 * mjalert.js
 *
 * <mj-alert> -- contextual feedback message (info, success, warning, error).
 * Covers inline, banner, and callout placement variants.
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
:host([open="false"]), :host([hidden]) { display: none; }

.container {
  display: flex;
  align-items: flex-start;
  gap: var(--mj-alert-gap, var(--mj-space-3));
  padding-block: var(--mj-alert-padding-block, var(--mj-space-3));
  padding-inline: var(--mj-alert-padding-inline, var(--mj-space-4));
  background: var(--mj-alert-bg, var(--mj-color-info-surface));
  border: 1px solid var(--mj-alert-border-color, var(--mj-color-info));
  border-radius: var(--mj-alert-border-radius, var(--mj-radius-md));
  color: var(--mj-alert-color, var(--mj-text));
}

:host([variant="banner"]) .container { border-radius: 0; border-inline: none; border-block-start: none; }
:host([variant="callout"]) .container {
  border-inline-start: var(--mj-alert-callout-accent-width, 4px) solid var(--mj-alert-border-color, var(--mj-color-info));
  border-block: none; border-inline-end: none;
  border-radius: 0;
  background: var(--mj-alert-bg, var(--mj-color-info-surface));
}

:host([severity="info"])    .container { --mj-alert-bg: var(--mj-color-info-surface); --mj-alert-border-color: var(--mj-color-info); --mj-alert-icon-color: var(--mj-color-info); }
:host([severity="success"]) .container { --mj-alert-bg: var(--mj-color-success-surface); --mj-alert-border-color: var(--mj-color-success); --mj-alert-icon-color: var(--mj-color-success); }
:host([severity="warning"]) .container { --mj-alert-bg: var(--mj-color-warning-surface); --mj-alert-border-color: var(--mj-color-warning); --mj-alert-icon-color: var(--mj-color-warning); }
:host([severity="error"])   .container { --mj-alert-bg: var(--mj-color-danger-surface); --mj-alert-border-color: var(--mj-color-danger); --mj-alert-icon-color: var(--mj-color-danger); }

.icon { flex-shrink: 0; width: 1.25rem; height: 1.25rem; color: var(--mj-alert-icon-color, var(--mj-color-info)); margin-block-start: 0.125rem; }
.icon svg { width: 100%; height: 100%; }
:host([no-icon]) .icon { display: none; }

.body { flex: 1; min-width: 0; }
.title { font-weight: var(--mj-font-weight-medium); margin-block-end: var(--mj-space-1); }
.title:empty { display: none; }
.actions { margin-block-start: var(--mj-space-2); }
slot[name="actions"]::slotted(*) { display: inline-flex; gap: var(--mj-space-2); }

.dismiss {
  flex-shrink: 0; display: flex; align-items: center; justify-content: center;
  width: 1.75rem; height: 1.75rem;
  background: transparent; border: none; border-radius: var(--mj-radius-sm);
  cursor: pointer; color: var(--mj-text-muted); padding: 0;
}
.dismiss:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: var(--mj-focus-ring-offset); }
.dismiss:hover { background: var(--mj-bg-muted); }
.dismiss svg { width: 1rem; height: 1rem; }
:host(:not([dismissible])) .dismiss { display: none; }
`;

export class MjAlert extends MjElement {
  static tagName = "mj-alert";
  static styles = STYLES;
  static watched = ["severity", "variant", "dismissible", "heading", "no-icon", "open"];

  render() {
    const severity = this.getAttribute("severity") || "info";
    const heading = this.getAttribute("heading") || "";
    const role = severity === "error" ? "alert" : "status";
    const markup = `
      <div class="container" part="container" role="${role}" aria-atomic="true">
        <span class="icon" part="icon"><slot name="icon">${ICONS[severity] || ICONS.info}</slot></span>
        <div class="body" part="content">
          <div class="title" part="title"><slot name="title">${heading}</slot></div>
          <div part="body"><slot></slot></div>
          <div class="actions" part="actions"><slot name="actions"></slot></div>
        </div>
        <button class="dismiss" part="dismiss" type="button" aria-label="${t("core.close")}">
          <svg aria-hidden="true" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/></svg>
        </button>
      </div>
    `
    return markup
  }

  afterRender() {
    this._container = this.$(".container")
    this._dismissBtn = this.$(".dismiss")
    this._iconSlot = this.$("slot[name='icon']")
    this.listen(this._dismissBtn, "click", this._onDismiss.bind(this))
    this.listen(this._dismissBtn, "keydown", this._onDismissKey.bind(this))
    this._announceContent()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._container === undefined) {
      return
    }

    if (name === "severity") {
      const role = (newValue === "error") ? "alert" : "status"
      this._container.setAttribute("role", role)
      const iconSpan = this.$(".icon")
      if (iconSpan !== null) {
        const defaultIcon = ICONS[newValue] || ICONS.info
        const existing = this._iconSlot
        if (existing !== null) {
          existing.innerHTML = defaultIcon
        }
      }
    }

    if (name === "heading") {
      const titleSlot = this.$("slot[name='title']")
      if (titleSlot !== null) {
        titleSlot.textContent = newValue || ""
      }
    }

    if (name === "open") {
      const wasHidden = oldValue === "false"
      const nowOpen = newValue !== "false" && newValue !== null
      if (wasHidden === true && nowOpen === true) {
        setTimeout(() => {
          this._announceContent()
          this.emit("mj-alert-open", { severity: this.getAttribute("severity"), variant: this.getAttribute("variant") })
        }, 0)
      } else if (nowOpen === false) {
        this.emit("mj-alert-close", { severity: this.getAttribute("severity"), variant: this.getAttribute("variant") })
      }
    }
    return
  }

  _announceContent() {
    const severity = this.getAttribute("severity") || "info"
    const politeness = severity === "error" ? "assertive" : "polite"
    const text = this.textContent.trim()
    if (text.length > 0) {
      announce(text, politeness)
    }
    return
  }

  _onDismiss() {
    const severity = this.getAttribute("severity") || "info"
    const variant = this.getAttribute("variant") || "inline"
    const proceed = this.emit("mj-alert-dismiss", { severity: severity, variant: variant }, { cancelable: true })
    if (proceed === false) {
      return
    }

    this.setAttribute("open", "false")
    const onEnd = () => {
      this.remove()
    }
    this.addEventListener("transitionend", onEnd, { once: true })
    setTimeout(onEnd, 400)
    return
  }

  _onDismissKey(event) {
    if (event.key === "Escape") {
      this._onDismiss()
    }
    return
  }

  get open() {
    const value = this.getAttribute("open")
    return value !== "false"
  }

  set open(value) {
    this.setAttribute("open", value === true ? "true" : "false")
    return
  }

  get severity() {
    const value = this.getAttribute("severity") || "info"
    return value
  }

  set severity(value) {
    this.setAttribute("severity", value)
    return
  }
}
