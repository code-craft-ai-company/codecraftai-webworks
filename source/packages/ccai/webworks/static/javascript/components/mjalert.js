/*
 * mjalert.js
 *
 * <mj-alert> -- contextual feedback message (info, success, warning, error).
 * Covers inline, banner, and callout placement variants.
 *
 * Announcements: the container carries role="alert" / role="status" for its
 * semantics, but the message is spoken through the shared announcer only --
 * once when the alert is inserted into a loaded page and again each time it
 * is re-opened. An alert that is part of the initial page, or that is merely
 * moved in the DOM, is not announced.
 *
 * `open` is true unless the attribute is exactly "false"; removing the
 * attribute shows the alert.
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

/*
 * Keys of the text that names the severity, so the meaning is not carried by
 * colour and icon alone. Resolved through t() at use time.
 */
const SEVERITY_LABEL_KEYS = {
  info: "mj.alert.info",
  success: "mj.alert.success",
  warning: "mj.alert.warning",
  error: "mj.alert.error"
};

/* Candidates for receiving focus when a focused alert is dismissed. */
const FOCUSABLE_SELECTOR =
  "a[href], button:not([disabled]), input:not([disabled]):not([type='hidden']), " +
  "select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex='-1'])";

const STYLES = `
:host { display: block; }
:host([open="false"]), :host([hidden]) { display: none; }

/*
 * The severity colours live in the internal --mj-alert-severity-* properties,
 * so the public --mj-alert-bg / -border-color / -icon-color set on the host
 * (or any ancestor) override them for every severity.
 */
.container {
  --mj-alert-severity-bg: var(--mj-color-info-surface);
  --mj-alert-severity-border-color: var(--mj-color-info);
  --mj-alert-severity-icon-color: var(--mj-color-info);

  display: flex;
  align-items: flex-start;
  gap: var(--mj-alert-gap, var(--mj-space-3));
  padding-block: var(--mj-alert-padding-block, var(--mj-space-3));
  padding-inline: var(--mj-alert-padding-inline, var(--mj-space-4));
  background: var(--mj-alert-bg, var(--mj-alert-severity-bg, var(--mj-color-info-surface)));
  border: 1px solid var(--mj-alert-border-color, var(--mj-alert-severity-border-color, var(--mj-color-info)));
  border-radius: var(--mj-alert-border-radius, var(--mj-radius-md));
  color: var(--mj-alert-color, var(--mj-text));
}

:host([variant="banner"]) .container { border-radius: 0; border-inline: none; border-block-start: none; }
:host([variant="callout"]) .container {
  border-inline-start: var(--mj-alert-callout-accent-width, 4px) solid var(--mj-alert-border-color, var(--mj-alert-severity-border-color, var(--mj-color-info)));
  border-block: none; border-inline-end: none;
  border-radius: 0;
}

:host([severity="info"])    .container { --mj-alert-severity-bg: var(--mj-color-info-surface); --mj-alert-severity-border-color: var(--mj-color-info); --mj-alert-severity-icon-color: var(--mj-color-info); }
:host([severity="success"]) .container { --mj-alert-severity-bg: var(--mj-color-success-surface); --mj-alert-severity-border-color: var(--mj-color-success); --mj-alert-severity-icon-color: var(--mj-color-success); }
:host([severity="warning"]) .container { --mj-alert-severity-bg: var(--mj-color-warning-surface); --mj-alert-severity-border-color: var(--mj-color-warning); --mj-alert-severity-icon-color: var(--mj-color-warning); }
:host([severity="error"])   .container { --mj-alert-severity-bg: var(--mj-color-danger-surface); --mj-alert-severity-border-color: var(--mj-color-danger); --mj-alert-severity-icon-color: var(--mj-color-danger); }

.icon { flex-shrink: 0; width: 1.25rem; height: 1.25rem; color: var(--mj-alert-icon-color, var(--mj-alert-severity-icon-color, var(--mj-color-info))); margin-block-start: 0.125rem; }
.icon svg { width: 100%; height: 100%; }
:host([no-icon]) .icon { display: none; }

.body { flex: 1; min-width: 0; position: relative; }
.title { font-weight: var(--mj-font-weight-medium); margin-block-end: var(--mj-space-1); }
.actions { margin-block-start: var(--mj-space-2); }
.region { display: contents; }
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
  static watched = ["severity", "variant", "dismissible", "heading", "no-icon", "open", "icon", "dismiss-label", "label"];

  constructor() {
    super()

    /* Open state last reported through mj-alert-open / mj-alert-close. */
    this._openState = true

    /* True once the message has been announced for its insertion. */
    this._announcedInsertion = false

    /* Pending removal after a dismissal. */
    this._removeTimer = null
  }

  /* The severity, limited to the known values. */
  _getSeverity() {
    const value = this.getAttribute("severity")
    const severity = value !== null && SEVERITY_LABEL_KEYS[value] !== undefined ? value : "info"
    return severity
  }

  /*
   * Markup of the default icon: the one named by the `icon` attribute when it
   * names a built-in icon, otherwise the icon of the severity. Both come from
   * the constant ICONS table.
   */
  _getIconMarkup() {
    const iconName = this.getAttribute("icon")
    let markup = ICONS[this._getSeverity()]
    if (iconName !== null && Object.prototype.hasOwnProperty.call(ICONS, iconName) === true) {
      markup = ICONS[iconName]
    }
    return markup
  }

  render() {
    const severity = this._getSeverity()
    const heading = this.getAttribute("heading") || ""
    const role = severity === "error" ? "alert" : "status"
    const markup = html`
      <div class="region" part="region">
        <div class="container" part="container" role="${role}" aria-atomic="true" aria-live="off">
          <span class="icon" part="icon"><slot name="icon">${raw(this._getIconMarkup())}</slot></span>
          <div class="body" part="content">
            <span class="severity-label mj-visually-hidden"></span>
            <div class="title" part="title"><slot name="title">${heading}</slot></div>
            <div part="body"><slot></slot></div>
            <div class="actions" part="actions"><slot name="actions"></slot></div>
          </div>
          <button class="dismiss" part="dismiss" type="button" aria-label="${t("core.close")}">
            <svg aria-hidden="true" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/></svg>
          </button>
        </div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._region = this.$(".region")
    this._container = this.$(".container")
    this._dismissBtn = this.$(".dismiss")
    this._iconSlot = this.$("slot[name='icon']")
    this._titleEl = this.$(".title")
    this._titleSlot = this.$("slot[name='title']")
    this._actionsEl = this.$(".actions")
    this._actionsSlot = this.$("slot[name='actions']")
    this._severityLabel = this.$(".severity-label")

    this.listen(this._dismissBtn, "click", this._onDismiss.bind(this))
    this.listen(this._dismissBtn, "keydown", this._onDismissKey.bind(this))
    this.listen(this._titleSlot, "slotchange", this._syncSections.bind(this))
    this.listen(this._actionsSlot, "slotchange", this._syncSections.bind(this))

    this._openState = this.open
    this._syncSections()
    this._syncLabels()
    return
  }

  onConnected() {
    /*
     * Announce an alert that is inserted into a page that has finished
     * loading. Alerts that are part of the initial document are static
     * content, and an alert that is only moved was announced before.
     */
    const insertedLater = document.readyState === "complete"
    if (this._announcedInsertion === false) {
      this._announcedInsertion = true
      if (insertedLater === true && this.open === true) {
        this._announceContent()
      }
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._container === undefined || this._container === null) {
      return
    }

    if (name === "severity" || name === "icon") {
      const role = this._getSeverity() === "error" ? "alert" : "status"
      this._container.setAttribute("role", role)
      if (this._iconSlot !== null) {
        /* Constant markup from the ICONS table. */
        this._iconSlot.innerHTML = this._getIconMarkup()
      }
    }

    if (name === "heading") {
      if (this._titleSlot !== null) {
        this._titleSlot.textContent = newValue || ""
      }
      this._syncSections()
    }

    this._syncLabels()

    if (name === "open") {
      this._reportOpen()
    }
    return
  }

  /*
   * Report a real change of the open state, once. A missing attribute is the
   * open state, so removing `open="false"` re-opens the alert.
   */
  _reportOpen() {
    const nowOpen = this.open
    if (nowOpen === this._openState) {
      return
    }
    this._openState = nowOpen

    const detail = { severity: this.getAttribute("severity"), variant: this.getAttribute("variant") }
    if (nowOpen === true) {
      this._cancelRemoval()
      this._announceContent()
      this.emit("mj-alert-open", detail)
    } else {
      this.emit("mj-alert-close", detail)
    }
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

  /* Severity prefix, dismiss-button name and the banner landmark. */
  _syncLabels() {
    const severityLabel = t(SEVERITY_LABEL_KEYS[this._getSeverity()])
    this._severityLabel.textContent = `${severityLabel}: `

    const dismissLabel = this.getAttribute("dismiss-label")
    this._dismissBtn.setAttribute(
      "aria-label",
      dismissLabel !== null && dismissLabel !== "" ? dismissLabel : t("core.close")
    )

    if (this.getAttribute("variant") === "banner") {
      const label = this.getAttribute("label") || this.getAttribute("heading") || severityLabel
      this._region.setAttribute("role", "region")
      this._region.setAttribute("aria-label", label)
    } else {
      this._region.removeAttribute("role")
      this._region.removeAttribute("aria-label")
    }
    return
  }

  _announceContent() {
    const severity = this._getSeverity()
    const politeness = severity === "error" ? "assertive" : "polite"
    const heading = this.getAttribute("heading") || ""
    const text = `${heading} ${this.textContent}`.replace(/\s+/g, " ").trim()
    if (text.length > 0) {
      announce(`${t(SEVERITY_LABEL_KEYS[severity])}: ${text}`, politeness)
    }
    return
  }

  /*
   * A dismissed alert disappears while its dismiss button has focus. Move
   * focus first -- to the element named by `return-focus`, else to the next
   * focusable element after the alert, else to the previous one -- so it does
   * not fall back to the top of the document.
   */
  _moveFocusAway() {
    const root = this.getRootNode()
    const active = root.activeElement
    const hasFocus = active !== null && active !== undefined && (active === this || this.contains(active) === true)
    if (hasFocus === false) {
      return
    }

    let target = null

    const returnId = this.getAttribute("return-focus")
    if (returnId !== null && returnId !== "" && typeof root.getElementById === "function") {
      target = root.getElementById(returnId)
    }

    if (target === null) {
      const candidates = root.querySelectorAll(FOCUSABLE_SELECTOR)
      let previous = null
      for (let index = 0; index < candidates.length; index = index + 1) {
        const candidate = candidates[index]
        if (this.contains(candidate) === true) {
          continue
        }
        const relation = this.compareDocumentPosition(candidate)
        if ((relation & Node.DOCUMENT_POSITION_FOLLOWING) !== 0) {
          target = candidate
          break
        }
        previous = candidate
      }
      if (target === null) {
        target = previous
      }
    }

    if (target !== null && typeof target.focus === "function") {
      target.focus()
    }
    return
  }

  _cancelRemoval() {
    if (this._removeTimer !== null) {
      clearTimeout(this._removeTimer)
      this._removeTimer = null
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

    this._moveFocusAway()
    this.setAttribute("open", "false")

    /* Removed shortly after, unless it was re-opened in the meantime. */
    this._cancelRemoval()
    this._removeTimer = setTimeout(() => {
      this._removeTimer = null
      if (this.open === false) {
        this.remove()
      }
    }, 400)
    this.onTeardown(this._cancelRemoval.bind(this))
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
    this.setAttribute("open", Boolean(value) === true ? "true" : "false")
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
