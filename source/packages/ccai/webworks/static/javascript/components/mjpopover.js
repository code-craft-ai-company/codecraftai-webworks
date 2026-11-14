/*
 * mjpopover.js
 *
 * <mj-popover> -- anchored, non-modal overlay for rich contextual content.
 * Supports click (popover, help) and hover / focus (hovercard) trigger
 * modes. Uses the overlay.js positioning engine for viewport-aware placement
 * in the top layer.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";
import { autoPosition, pushLayer, removeLayer, claimEscape } from "../core/overlay.js";
import { getFocusable, deepActiveElement, flatContains } from "../core/focustrap.js";

const STYLES = `
:host {
  display: contents;
}

/*
 * The open popup carries no transform once its entry animation has ended,
 * so position: fixed popups opened inside it (a select, a date picker) are
 * not positioned against it.
 */
.popup {
  position: fixed;
  z-index: var(--mj-layer-popover);
  box-sizing: border-box;
  margin: 0;
  width: var(--mj-popover-width, 18rem);
  background: var(--mj-surface);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-popover-radius, var(--mj-radius-md));
  box-shadow: var(--mj-popover-shadow, var(--mj-elevation-3));
  padding: var(--mj-popover-padding, var(--mj-space-4));
  color: var(--mj-text);
  outline: none;
  overflow: visible;
}

:host([open]) .popup {
  animation: mj-popover-in var(--mj-motion-fast) var(--mj-motion-ease);
}

:host(:not([open])) .popup {
  pointer-events: none;
  visibility: hidden;
}

@keyframes mj-popover-in {
  from { opacity: 0; transform: translateY(-4px); }
  to   { opacity: 1; transform: none; }
}

.popup-header {
  font-weight: var(--mj-font-weight-bold);
  margin-block-end: var(--mj-space-2);
}

.popup-header[hidden] { display: none; }

.popup-footer {
  margin-block-start: var(--mj-space-3);
  border-block-start: 1px solid var(--mj-border);
  padding-block-start: var(--mj-space-3);
}

.popup-footer[hidden] { display: none; }

.close-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  position: absolute;
  inset-block-start: var(--mj-space-2);
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

/*
 * Arrow: a rotated square on the edge that faces the anchor, clipped to the
 * half that sticks out. overlay.js publishes the resolved side in
 * data-mj-placement and the anchor's centre in --mj-anchor-offset.
 */
.arrow {
  display: none;
  position: absolute;
  box-sizing: border-box;
  width: var(--mj-popover-arrow-size, 10px);
  height: var(--mj-popover-arrow-size, 10px);
  background: var(--mj-surface);
  border: 1px solid var(--mj-border);
  rotate: 45deg;
}

:host([arrow]:not([arrow="false"])) .arrow { display: block; }

.popup[data-mj-placement^="bottom"] .arrow {
  inset-block-start: calc(var(--mj-popover-arrow-size, 10px) / -2 - 1px);
  left: calc(var(--mj-anchor-offset, 50%) - var(--mj-popover-arrow-size, 10px) / 2 - 1px);
  clip-path: polygon(0 0, 100% 0, 0 100%);
}

.popup[data-mj-placement^="top"] .arrow {
  inset-block-end: calc(var(--mj-popover-arrow-size, 10px) / -2 - 1px);
  left: calc(var(--mj-anchor-offset, 50%) - var(--mj-popover-arrow-size, 10px) / 2 - 1px);
  clip-path: polygon(100% 0, 100% 100%, 0 100%);
}

.popup[data-mj-placement^="start"] .arrow {
  inset-inline-end: calc(var(--mj-popover-arrow-size, 10px) / -2 - 1px);
  top: calc(var(--mj-anchor-offset, 50%) - var(--mj-popover-arrow-size, 10px) / 2 - 1px);
  clip-path: polygon(0 0, 100% 0, 100% 100%);
}

.popup[data-mj-placement^="end"] .arrow {
  inset-inline-start: calc(var(--mj-popover-arrow-size, 10px) / -2 - 1px);
  top: calc(var(--mj-anchor-offset, 50%) - var(--mj-popover-arrow-size, 10px) / 2 - 1px);
  clip-path: polygon(0 0, 100% 100%, 0 100%);
}

/* In RTL the start side is the right-hand side, so the arrows swap halves. */
:host(:dir(rtl)) .popup[data-mj-placement^="start"] .arrow {
  clip-path: polygon(0 0, 100% 100%, 0 100%);
}

:host(:dir(rtl)) .popup[data-mj-placement^="end"] .arrow {
  clip-path: polygon(0 0, 100% 0, 100% 100%);
}

@media (prefers-reduced-motion: reduce) {
  :host([open]) .popup { animation: none; }
}
`;

export class MjPopover extends MjElement {
  static tagName = "mj-popover";
  static styles = STYLES;
  static watched = ["open", "variant", "placement", "offset", "arrow", "light-dismiss",
                    "hover-delay", "hover-out-delay", "trigger-id", "no-close-button",
                    "label", "close-label"];

  constructor() {
    super()
    this._popup = null
    this._header = null
    this._footer = null
    this._closeBtn = null
    this._triggerEl = null
    this._positionDispose = null
    this._layer = null
    this._hoverInTimer = null
    this._hoverOutTimer = null
    this._popupId = nextId("mj-popup")
    this._headerId = nextId("mj-popup-header")
    this._computedPlacement = null

    /* True from a successful open until the close has completed. */
    this._isOpen = false

    /* True while the window-level light-dismiss listener is installed. */
    this._lightDismissInstalled = false

    /* One bound function per listener, so each can be removed exactly. */
    this._onLightDismissBound = this._onLightDismiss.bind(this)
    this._onTriggerClick = this._handleTriggerClick.bind(this)
    this._onTriggerKeydown = this._handleTriggerKeydown.bind(this)
    this._onTriggerPointerEnter = this._handleTriggerPointerEnter.bind(this)
    this._onTriggerPointerLeave = this._handleTriggerPointerLeave.bind(this)
    this._onTriggerFocusIn = this._handleTriggerFocusIn.bind(this)
    this._onTriggerFocusOut = this._handleTriggerFocusOut.bind(this)
  }

  render() {
    const markup = html`
      <slot name="trigger"></slot>
      <div class="popup" part="popup" id="${this._popupId}" role="dialog" tabindex="-1">
        <div class="arrow" part="arrow" aria-hidden="true"></div>
        <div class="popup-header" part="header" id="${this._headerId}"><slot name="header"></slot></div>
        <div class="popup-body" part="body"><slot></slot></div>
        <div class="popup-footer" part="footer"><slot name="footer"></slot></div>
        <button class="close-btn" part="close-button" type="button" data-action="close">&#x2715;</button>
      </div>
    `
    return markup
  }

  afterRender() {
    this._popup = this.$(".popup")
    this._header = this.$(".popup-header")
    this._footer = this.$(".popup-footer")
    this._closeBtn = this.$(".close-btn")

    this.listen(this._popup, "click", this._onPopupClick.bind(this))
    this.listen(this._popup, "keydown", this._onKeydown.bind(this))
    this.listen(this._popup, "pointerenter", this._onPopupPointerEnter.bind(this))
    this.listen(this._popup, "pointerleave", this._onPopupPointerLeave.bind(this))
    this.listen(this._popup, "focusout", this._onPopupFocusOut.bind(this))

    /* A trigger may be slotted after the element has connected. */
    this.listen(this.$("slot[name='trigger']"), "slotchange", this._resolveTrigger.bind(this))
    this.listen(this.$("slot[name='header']"), "slotchange", this._syncSections.bind(this))
    this.listen(this.$("slot[name='footer']"), "slotchange", this._syncSections.bind(this))

    this._applyLabels()
    this._syncSections()
    this._resolveTrigger()

    if (this.hasAttribute("open") === true) {
      this._openPopover("api")
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._popup === undefined || this._popup === null) {
      return
    }

    if (name === "open") {
      if (newValue !== null) {
        this._openPopover("api")
      } else if (this._isOpen === true) {
        const closed = this._closePopover("api")
        if (closed === false) {
          /* The close was vetoed: the attribute must keep matching reality. */
          this.setAttribute("open", "")
        }
      }
    } else if (name === "trigger-id") {
      this._resolveTrigger()
    } else if (name === "placement" || name === "offset" || name === "arrow") {
      if (this._isOpen === true) {
        this._startPositioning()
      }
    } else if (name === "label" || name === "close-label") {
      this._applyLabels()
    } else if (name === "light-dismiss") {
      this._syncLightDismiss()
    }
    return
  }

  onDisconnected() {
    this._clearHoverTimers()
    this._leaveOpenState()
    this._isOpen = false
    this._detachTrigger()
    return
  }

  _variant() {
    const variant = this.getAttribute("variant") || "popover"
    return variant
  }

  /* ----- attribute-driven rendering ----- */

  _applyLabels() {
    this._closeBtn.setAttribute("aria-label", this.getAttribute("close-label") || t("core.close"))
    this._applyPopupName()
    return
  }

  /*
   * The popup is a (non-modal) dialog and needs a name: the `label`
   * attribute, else the header slot, else the text of the trigger.
   */
  _applyPopupName() {
    const label = this.getAttribute("label") || ""
    const headerSlot = this.$("slot[name='header']")
    const hasHeader = headerSlot !== null && headerSlot.assignedNodes().length > 0

    if (label.length > 0) {
      this._popup.setAttribute("aria-label", label)
      this._popup.removeAttribute("aria-labelledby")
    } else if (hasHeader === true) {
      this._popup.removeAttribute("aria-label")
      this._popup.setAttribute("aria-labelledby", this._headerId)
    } else {
      const triggerText = this._triggerEl !== null ? (this._triggerEl.textContent || "").trim() : ""
      this._popup.removeAttribute("aria-labelledby")
      if (triggerText.length > 0) {
        this._popup.setAttribute("aria-label", triggerText)
      } else {
        this._popup.removeAttribute("aria-label")
      }
    }
    return
  }

  /* Header and footer take no space while nothing is slotted into them. */
  _syncSections() {
    const headerSlot = this.$("slot[name='header']")
    const footerSlot = this.$("slot[name='footer']")
    this._header.hidden = headerSlot.assignedNodes().length === 0
    this._footer.hidden = footerSlot.assignedNodes().length === 0
    this._applyPopupName()
    return
  }

  /* ----- trigger wiring ----- */

  _resolveTrigger() {
    const triggerId = this.getAttribute("trigger-id")
    let triggerEl = null

    if (triggerId !== null && triggerId.length > 0) {
      triggerEl = document.getElementById(triggerId)
      if (triggerEl === null) {
        console.error(`<mj-popover>: trigger-id "${triggerId}" not found`)
      }
    } else {
      const slot = this.shadowRoot.querySelector("slot[name='trigger']")
      if (slot !== null) {
        const assigned = slot.assignedElements()
        triggerEl = assigned.length > 0 ? assigned[0] : null
      }
    }

    if (triggerEl === this._triggerEl) {
      return
    }

    this._detachTrigger()
    this._triggerEl = triggerEl

    if (triggerEl !== null) {
      triggerEl.addEventListener("click", this._onTriggerClick)
      triggerEl.addEventListener("keydown", this._onTriggerKeydown)
      triggerEl.addEventListener("pointerenter", this._onTriggerPointerEnter)
      triggerEl.addEventListener("pointerleave", this._onTriggerPointerLeave)
      triggerEl.addEventListener("focusin", this._onTriggerFocusIn)
      triggerEl.addEventListener("focusout", this._onTriggerFocusOut)

      /*
       * No aria-controls: the popup lives in this shadow root and an id
       * reference from the light-DOM trigger could not resolve.
       */
      triggerEl.setAttribute("aria-haspopup", "dialog")
      triggerEl.setAttribute("aria-expanded", this._isOpen === true ? "true" : "false")
    }

    this._applyPopupName()
    if (this._isOpen === true) {
      this._startPositioning()
    }
    return
  }

  /* Undo everything `_resolveTrigger` did to the current trigger. */
  _detachTrigger() {
    const triggerEl = this._triggerEl
    if (triggerEl === null) {
      return
    }

    triggerEl.removeEventListener("click", this._onTriggerClick)
    triggerEl.removeEventListener("keydown", this._onTriggerKeydown)
    triggerEl.removeEventListener("pointerenter", this._onTriggerPointerEnter)
    triggerEl.removeEventListener("pointerleave", this._onTriggerPointerLeave)
    triggerEl.removeEventListener("focusin", this._onTriggerFocusIn)
    triggerEl.removeEventListener("focusout", this._onTriggerFocusOut)
    triggerEl.removeAttribute("aria-haspopup")
    triggerEl.removeAttribute("aria-expanded")
    this._triggerEl = null
    return
  }

  _handleTriggerClick() {
    if (this._variant() === "hovercard") {
      return
    }
    if (this._isOpen === true) {
      this._closePopover("trigger")
    } else {
      this._openPopover("trigger")
    }
    return
  }

  _handleTriggerKeydown(event) {
    if (event.key === "Escape" && this._isOpen === true) {
      /* Escape on the trigger dismisses the popup it opened. */
      event.preventDefault()
      event.stopPropagation()
      this._closePopover("escape")
      return
    }

    const isActivation = event.key === "Enter" || event.key === " "
    const nativeControl = event.currentTarget instanceof HTMLButtonElement ||
      event.currentTarget instanceof HTMLAnchorElement

    /* A native button already turns Enter / Space into a click. */
    if (isActivation === true && nativeControl === false && this._variant() !== "hovercard") {
      event.preventDefault()
      this._handleTriggerClick()
    }
    return
  }

  _handleTriggerPointerEnter() {
    if (this._variant() !== "hovercard") {
      return
    }
    this._clearHoverTimers()
    const delay = this._delay("hover-delay", 200)
    this._hoverInTimer = window.setTimeout(() => {
      this._hoverInTimer = null
      this._openPopover("hover")
    }, delay)
    return
  }

  _handleTriggerPointerLeave() {
    if (this._variant() !== "hovercard") {
      return
    }
    this._clearHoverInTimer()
    this._scheduleHoverClose()
    return
  }

  /* A hovercard is also reachable from the keyboard: it opens on focus. */
  _handleTriggerFocusIn() {
    if (this._variant() !== "hovercard") {
      return
    }
    this._clearHoverTimers()
    this._openPopover("focus")
    return
  }

  _handleTriggerFocusOut(event) {
    if (this._variant() !== "hovercard") {
      return
    }
    const movedIntoPopup = event.relatedTarget !== null && flatContains(this._popup, event.relatedTarget) === true
    if (movedIntoPopup === false) {
      this._scheduleHoverClose()
    }
    return
  }

  _onPopupPointerEnter() {
    this._clearHoverOutTimer()
    return
  }

  _onPopupPointerLeave() {
    if (this._variant() !== "hovercard") {
      return
    }
    this._scheduleHoverClose()
    return
  }

  _onPopupFocusOut(event) {
    if (this._variant() !== "hovercard" || this._isOpen === false) {
      return
    }
    const next = event.relatedTarget
    const stillInside = next !== null &&
      (flatContains(this._popup, next) === true ||
       (this._triggerEl !== null && this._triggerEl.contains(next) === true))
    if (stillInside === false) {
      this._scheduleHoverClose()
    }
    return
  }

  _delay(attribute, fallback) {
    const parsed = parseInt(this.getAttribute(attribute) || "", 10)
    const delay = Number.isFinite(parsed) === true && parsed >= 0 ? parsed : fallback
    return delay
  }

  _scheduleHoverClose() {
    this._clearHoverOutTimer()
    const delay = this._delay("hover-out-delay", 300)
    this._hoverOutTimer = window.setTimeout(() => {
      this._hoverOutTimer = null

      /*
       * Keyboard focus keeps a hovercard open just as the pointer does: it
       * closes once focus has left both the trigger and the popup.
       */
      const active = deepActiveElement()
      const focusHeld = active !== null &&
        (flatContains(this._popup, active) === true ||
         (this._triggerEl !== null && flatContains(this._triggerEl, active) === true))
      if (focusHeld === false) {
        this._closePopover("hover")
      }
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

  /* ----- open / close ----- */

  /*
   * Open the popover. Every route (trigger, hover, focus, show(), the `open`
   * attribute) ends here, and an already open popover is left alone, so the
   * open events fire once and listeners are installed once.
   */
  _openPopover(reason) {
    if (this._popup === null || this._isOpen === true || this.isConnected === false) {
      return false
    }

    const proceed = this.emit("mj-popover-before-open", { reason: reason }, { cancelable: true })
    if (proceed === false) {
      /* Vetoed: an `open` attribute that asked for this is taken back. */
      if (this.hasAttribute("open") === true) {
        this.removeAttribute("open")
      }
      return false
    }

    this._isOpen = true
    if (this.hasAttribute("open") === false) {
      this.setAttribute("open", "")
    }

    if (this._triggerEl !== null) {
      this._triggerEl.setAttribute("aria-expanded", "true")
    }

    this._startPositioning()

    /*
     * A click-opened popover takes focus (its first focusable element, or
     * the popup itself). A hovercard leaves focus where it is.
     */
    const takesFocus = reason !== "hover" && reason !== "focus" && this._variant() !== "hovercard"
    if (takesFocus === true) {
      const focusable = getFocusable(this._popup)
      if (focusable.length > 0) {
        focusable[0].focus()
      } else {
        this._popup.focus()
      }
    }

    this._syncLightDismiss()

    this.emit("mj-popover-open", {
      placement: this._computedPlacement || this.getAttribute("placement") || "bottom"
    })
    return true
  }

  /*
   * Close the popover. Returns true when it closed and false when it was not
   * open or a `mj-popover-before-close` listener vetoed the close.
   */
  _closePopover(reason) {
    if (this._popup === null || this._isOpen === false) {
      return false
    }

    const proceed = this.emit("mj-popover-before-close", { reason: reason }, { cancelable: true })
    if (proceed === false) {
      return false
    }

    /* Decide about focus before the popup is hidden and focus is lost. */
    const active = deepActiveElement()
    const focusInside = active !== null && flatContains(this._popup, active) === true

    this._isOpen = false
    this._leaveOpenState()

    if (this.hasAttribute("open") === true) {
      this.removeAttribute("open")
    }

    /*
     * Focus goes back to the trigger only when it would otherwise be lost
     * with the popup. A user who has moved on keeps their focus.
     */
    if (focusInside === true && this._triggerEl !== null && typeof this._triggerEl.focus === "function") {
      this._triggerEl.focus()
    }

    this.emit("mj-popover-close", { reason: reason })
    return true
  }

  _leaveOpenState() {
    this._clearHoverTimers()
    this._stopPositioning()
    this._removeLightDismiss()
    this._computedPlacement = null

    if (this._triggerEl !== null) {
      this._triggerEl.setAttribute("aria-expanded", "false")
    }
    return
  }

  _startPositioning() {
    this._stopPositioning()

    const anchor = this._triggerEl || this
    const placement = this.getAttribute("placement") || "bottom"
    const parsedOffset = parseInt(this.getAttribute("offset") || "", 10)
    const offset = Number.isFinite(parsedOffset) === true ? parsedOffset : 8
    const hasArrow = this.hasAttribute("arrow") === true && this.getAttribute("arrow") !== "false"

    this._positionDispose = autoPosition(this._popup, anchor, {
      placement: placement,
      offset: offset,
      arrow: hasArrow,
      hideWhenDetached: true,
      onPlacement: (resolved) => {
        const changed = this._computedPlacement !== null && this._computedPlacement !== resolved
        this._computedPlacement = resolved
        if (changed === true) {
          this.emit("mj-popover-placement-change", { placement: resolved })
        }
      }
    })
    return
  }

  _stopPositioning() {
    if (this._positionDispose !== null) {
      this._positionDispose()
      this._positionDispose = null
      this._popup.style.visibility = ""
    }
    return
  }

  /* ----- light dismiss ----- */

  /*
   * While open with light dismiss enabled, the popover closes on a pointer
   * press outside it and on Escape wherever focus is (it registers as a
   * layer for the latter). Installed at most once; removed on close.
   */
  _syncLightDismiss() {
    const wanted = this._isOpen === true && this.getAttribute("light-dismiss") !== "false"

    if (wanted === true && this._lightDismissInstalled === false) {
      this._lightDismissInstalled = true
      window.addEventListener("pointerdown", this._onLightDismissBound, true)
      this._layer = pushLayer({
        surface: this._popup,
        modal: false,
        onEscape: () => {
          this._closePopover("escape")
        }
      })
    } else if (wanted === false) {
      this._removeLightDismiss()
    }
    return
  }

  _removeLightDismiss() {
    if (this._lightDismissInstalled === true) {
      this._lightDismissInstalled = false
      window.removeEventListener("pointerdown", this._onLightDismissBound, true)
    }
    if (this._layer !== null) {
      removeLayer(this._layer)
      this._layer = null
    }
    return
  }

  _onLightDismiss(event) {
    /*
     * composedPath, not event.target: on a window listener the target is
     * retargeted to the outermost shadow host, which would make every press
     * inside a popover nested in another component look like an outside one.
     */
    const path = event.composedPath()
    const inside = path.includes(this) === true || path.includes(this._popup) === true
    const onTrigger = this._triggerEl !== null && path.includes(this._triggerEl) === true
    if (inside === false && onTrigger === false) {
      this._closePopover("light-dismiss")
    }
    return
  }

  _onKeydown(event) {
    if (event.key === "Escape") {
      /* A popup open inside this one (a select, a menu) closes first. */
      const mine = claimEscape(event, this._layer)
      event.preventDefault()
      if (mine === true) {
        this._closePopover("escape")
      }
    }
    return
  }

  _onPopupClick(event) {
    const btn = event.target.closest("[data-action='close']")
    if (btn !== null && btn.getRootNode() === this.shadowRoot) {
      this._closePopover("close-button")
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

  /* The placement in effect after flipping; null while closed. */
  get computedPlacement() {
    const placement = this._isOpen === true ? this._computedPlacement : null
    return placement
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
