/*
 * mjpopover.js
 *
 * <mj-popover> -- anchored, non-modal overlay for rich contextual content.
 * Supports click/focus and hover (hovercard) trigger modes. Uses the
 * overlay.js positioning engine for viewport-aware placement.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { autoPosition } from "../core/overlay.js";
import { getFocusable } from "../core/focustrap.js";

const STYLES = `
:host {
  display: contents;
}

.popup {
  position: fixed;
  z-index: var(--mj-layer-popover);
  width: var(--mj-popover-width, 18rem);
  background: var(--mj-surface);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-popover-radius, var(--mj-radius-md));
  box-shadow: var(--mj-popover-shadow, var(--mj-elevation-3));
  padding: var(--mj-popover-padding, var(--mj-space-4));
  color: var(--mj-text);
  opacity: 0;
  transform: translateY(-4px);
  transition: opacity var(--mj-motion-fast) var(--mj-motion-ease),
              transform var(--mj-motion-fast) var(--mj-motion-ease);
  outline: none;
}

:host([open]) .popup {
  opacity: 1;
  transform: translateY(0);
}

:host(:not([open])) .popup {
  pointer-events: none;
  visibility: hidden;
}

.popup-header {
  font-weight: var(--mj-font-weight-bold);
  margin-bottom: var(--mj-space-2);
}

.popup-header:empty { display: none; }

.popup-footer {
  margin-top: var(--mj-space-3);
  border-top: 1px solid var(--mj-border);
  padding-top: var(--mj-space-3);
}

.popup-footer:empty { display: none; }

.close-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  position: absolute;
  top: var(--mj-space-2);
  inset-inline-end: var(--mj-space-2);
  width: 1.75rem;
  height: 1.75rem;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: var(--mj-radius-md);
  cursor: pointer;
  color: var(--mj-text-muted);
  font-size: var(--mj-font-size-sm);
}

.close-btn:hover { background: var(--mj-bg-muted); color: var(--mj-text); }
.close-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

:host([no-close-button]) .close-btn { display: none; }

@media (prefers-reduced-motion: reduce) {
  .popup { transition: none; }
}
`;

export class MjPopover extends MjElement {
  static tagName = "mj-popover";
  static styles = STYLES;
  static watched = ["open", "variant", "placement", "offset", "arrow", "light-dismiss",
                    "hover-delay", "hover-out-delay", "trigger-id", "no-close-button"];

  constructor() {
    super()
    this._popup = null
    this._triggerEl = null
    this._positionDispose = null
    this._hoverInTimer = null
    this._hoverOutTimer = null
    this._popupId = nextId("mj-popup")
    this._lastFocused = null
  }

  render() {
    const closeLabel = this.getAttribute("close-label") || "Close"
    const markup = `
      <slot name="trigger"></slot>
      <div class="popup" part="popup" id="${this._popupId}" role="region" tabindex="-1">
        <div class="popup-header" part="header"><slot name="header"></slot></div>
        <div class="popup-body" part="body"><slot></slot></div>
        <div class="popup-footer" part="footer"><slot name="footer"></slot></div>
        <button class="close-btn" part="close-button" aria-label="${closeLabel}" data-action="close">&#x2715;</button>
      </div>
    `
    return markup
  }

  afterRender() {
    this._popup = this.$(".popup")
    this._wireListeners()
    this._resolveTrigger()

    if (this.hasAttribute("open") === true) {
      this._openPopover("api")
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "open" && this._popup !== null) {
      if (newValue !== null && oldValue === null) {
        this._openPopover("api")
      } else if (newValue === null && oldValue !== null) {
        this._closePopover("api")
      }
    }
    if (name === "trigger-id") {
      this._resolveTrigger()
    }
    return
  }

  onDisconnected() {
    this._stopPositioning()
    this._clearHoverTimers()
    return
  }

  _wireListeners() {
    this.listen(this._popup, "click", this._onPopupClick.bind(this))
    this.listen(this._popup, "keydown", this._onKeydown.bind(this))
    this.listen(this._popup, "pointerenter", this._onPopupPointerEnter.bind(this))
    this.listen(this._popup, "pointerleave", this._onPopupPointerLeave.bind(this))
    return
  }

  _resolveTrigger() {
    const triggerId = this.getAttribute("trigger-id")
    let triggerEl = null

    if (triggerId !== null && triggerId.length > 0) {
      triggerEl = document.getElementById(triggerId)
      if (triggerEl === null) {
        console.error(`<mj-popover>: trigger-id "${triggerId}" not found`)
        return
      }
    } else {
      const slot = this.shadowRoot.querySelector("slot[name='trigger']")
      if (slot !== null) {
        const assigned = slot.assignedElements()
        triggerEl = assigned.length > 0 ? assigned[0] : null
      }
    }

    if (this._triggerEl !== null) {
      this._triggerEl.removeEventListener("click", this._onTriggerClick)
      this._triggerEl.removeEventListener("keydown", this._onTriggerKeydown)
      this._triggerEl.removeEventListener("pointerenter", this._onTriggerPointerEnter)
      this._triggerEl.removeEventListener("pointerleave", this._onTriggerPointerLeave)
    }

    this._triggerEl = triggerEl

    if (triggerEl !== null) {
      this._onTriggerClick = this._handleTriggerClick.bind(this)
      this._onTriggerKeydown = this._handleTriggerKeydown.bind(this)
      this._onTriggerPointerEnter = this._handleTriggerPointerEnter.bind(this)
      this._onTriggerPointerLeave = this._handleTriggerPointerLeave.bind(this)

      triggerEl.addEventListener("click", this._onTriggerClick)
      triggerEl.addEventListener("keydown", this._onTriggerKeydown)
      triggerEl.addEventListener("pointerenter", this._onTriggerPointerEnter)
      triggerEl.addEventListener("pointerleave", this._onTriggerPointerLeave)

      triggerEl.setAttribute("aria-haspopup", "true")
      triggerEl.setAttribute("aria-expanded", "false")
      triggerEl.setAttribute("aria-controls", this._popupId)
    }
    return
  }

  _handleTriggerClick() {
    const variant = this.getAttribute("variant") || "popover"
    if (variant === "hovercard") {
      return
    }
    if (this.hasAttribute("open") === true) {
      this._closePopover("trigger")
    } else {
      this._openPopover("trigger")
    }
    return
  }

  _handleTriggerKeydown(event) {
    if (event.key === "Enter" || event.key === " ") {
      const variant = this.getAttribute("variant") || "popover"
      if (variant !== "hovercard") {
        event.preventDefault()
        this._handleTriggerClick()
      }
    }
    return
  }

  _handleTriggerPointerEnter() {
    const variant = this.getAttribute("variant") || "popover"
    if (variant !== "hovercard") {
      return
    }
    this._clearHoverOutTimer()
    const delay = parseInt(this.getAttribute("hover-delay") || "200", 10)
    this._hoverInTimer = window.setTimeout(() => {
      this._openPopover("hover")
    }, delay)
    return
  }

  _handleTriggerPointerLeave() {
    const variant = this.getAttribute("variant") || "popover"
    if (variant !== "hovercard") {
      return
    }
    this._clearHoverInTimer()
    const delay = parseInt(this.getAttribute("hover-out-delay") || "300", 10)
    this._hoverOutTimer = window.setTimeout(() => {
      this._closePopover("hover")
    }, delay)
    return
  }

  _onPopupPointerEnter() {
    this._clearHoverOutTimer()
    return
  }

  _onPopupPointerLeave() {
    const variant = this.getAttribute("variant") || "popover"
    if (variant !== "hovercard") {
      return
    }
    const delay = parseInt(this.getAttribute("hover-out-delay") || "300", 10)
    this._hoverOutTimer = window.setTimeout(() => {
      this._closePopover("hover")
    }, delay)
    return
  }

  _clearHoverInTimer() {
    if (this._hoverInTimer !== null) {
      window.clearTimeout(this._hoverInTimer)
      this._hoverInTimer = null
    }
    return
  }

  _clearHoverOutTimer() {
    if (this._hoverOutTimer !== null) {
      window.clearTimeout(this._hoverOutTimer)
      this._hoverOutTimer = null
    }
    return
  }

  _clearHoverTimers() {
    this._clearHoverInTimer()
    this._clearHoverOutTimer()
    return
  }

  _openPopover(reason) {
    const beforeOk = this.emit("mj-popover-before-open", {}, { cancelable: true })
    if (beforeOk === false) {
      return
    }

    this._lastFocused = document.activeElement
    this.setAttribute("open", "")

    if (this._triggerEl !== null) {
      this._triggerEl.setAttribute("aria-expanded", "true")
    }

    const anchor = this._triggerEl || this
    const placement = this.getAttribute("placement") || "bottom"
    const offset = parseInt(this.getAttribute("offset") || "8", 10)
    this._stopPositioning()
    this._positionDispose = autoPosition(this._popup, anchor, { placement: placement, offset: offset })

    if (this.getAttribute("variant") !== "hovercard") {
      const focusable = getFocusable(this._popup)
      if (focusable.length > 0) {
        focusable[0].focus()
      } else {
        this._popup.focus()
      }
    }

    if (this.getAttribute("light-dismiss") !== "false") {
      this._lightDismissHandler = this._onLightDismiss.bind(this)
      window.addEventListener("pointerdown", this._lightDismissHandler, true)
      this.onTeardown(() => {
        window.removeEventListener("pointerdown", this._lightDismissHandler, true)
      })
    }

    this.emit("mj-popover-open", { placement: placement })
    return
  }

  _closePopover(reason) {
    const beforeOk = this.emit("mj-popover-before-close", { reason: reason }, { cancelable: true })
    if (beforeOk === false) {
      return
    }

    this.removeAttribute("open")

    if (this._triggerEl !== null) {
      this._triggerEl.setAttribute("aria-expanded", "false")
    }

    this._stopPositioning()

    if (this._lightDismissHandler !== undefined) {
      window.removeEventListener("pointerdown", this._lightDismissHandler, true)
      this._lightDismissHandler = undefined
    }

    const restoreEl = this._lastFocused
    this._lastFocused = null
    if (restoreEl !== null && typeof restoreEl.focus === "function") {
      restoreEl.focus()
    }

    this.emit("mj-popover-close", { reason: reason })
    return
  }

  _stopPositioning() {
    if (this._positionDispose !== null) {
      this._positionDispose()
      this._positionDispose = null
    }
    return
  }

  _onLightDismiss(event) {
    const inside = this.contains(event.target) || this.shadowRoot.contains(event.target)
    const onTrigger = this._triggerEl !== null && this._triggerEl.contains(event.target)
    if (inside === false && onTrigger === false) {
      this._closePopover("light-dismiss")
    }
    return
  }

  _onKeydown(event) {
    if (event.key === "Escape") {
      event.stopPropagation()
      this._closePopover("escape")
    }
    return
  }

  _onPopupClick(event) {
    const btn = event.target.closest("[data-action='close']")
    if (btn !== null) {
      this._closePopover("trigger")
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

  get triggerEl() {
    return this._triggerEl
  }

  get popupEl() {
    return this._popup
  }

  show() {
    this._openPopover("api")
    return
  }

  close() {
    this._closePopover("api")
    return
  }
}
