/*
 * mjtooltip.js
 *
 * <mj-tooltip> -- hover/focus-triggered supplemental hint anchored to a
 * trigger slot element. Fully keyboard accessible; WCAG 1.4.13 compliant:
 * hoverable, dismissible (Escape), and persistent while pointer/focus is
 * inside.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { position } from "../core/overlay.js";

const STYLES = `
:host { display: inline-block; position: relative; }

.trigger-wrap { display: contents; }

.popup {
  position: fixed;
  z-index: var(--mj-tooltip-z-index, var(--mj-layer-tooltip));
  max-width: var(--mj-tooltip-max-width, 17.5rem);
  padding-block: var(--mj-tooltip-padding-block, var(--mj-space-1));
  padding-inline: var(--mj-tooltip-padding-inline, var(--mj-space-2));
  background: var(--mj-tooltip-bg, var(--mj-color-neutral-800));
  color: var(--mj-tooltip-color, var(--mj-color-neutral-50));
  border: 1px solid var(--mj-tooltip-border-color, transparent);
  border-radius: var(--mj-tooltip-border-radius, var(--mj-radius-sm));
  box-shadow: var(--mj-tooltip-shadow, var(--mj-elevation-2));
  font-size: var(--mj-tooltip-font-size, var(--mj-font-size-sm));
  line-height: var(--mj-line-height);
  pointer-events: auto;
  word-wrap: break-word;
  animation: mj-tooltip-in var(--mj-tooltip-animation-duration, var(--mj-motion-fast)) var(--mj-motion-ease);
}
.popup[hidden] { display: none; }

@keyframes mj-tooltip-in {
  from { opacity: 0; transform: scale(0.95); }
  to   { opacity: 1; transform: scale(1); }
}
@media (prefers-reduced-motion: reduce) {
  @keyframes mj-tooltip-in { from { opacity: 0; } to { opacity: 1; } }
}

.arrow {
  position: fixed;
  width: var(--mj-tooltip-arrow-size, 6px);
  height: var(--mj-tooltip-arrow-size, 6px);
  background: var(--mj-tooltip-bg, var(--mj-color-neutral-800));
  transform: rotate(45deg);
  pointer-events: none;
}
.arrow[hidden] { display: none; }
`;

export class MjTooltip extends MjElement {
  static tagName = "mj-tooltip";
  static styles = STYLES;
  static watched = ["content", "placement", "trigger", "show-delay", "hide-delay", "open", "disabled", "arrow", "max-width"];

  constructor() {
    super()
    this._tooltipId = nextId("mj-tooltip")
    this._showTimer = null
    this._hideTimer = null
    this._triggerEl = null
  }

  render() {
    const content = this.getAttribute("content") || ""
    const markup = `
      <span class="trigger-wrap" part="trigger"><slot name="trigger"></slot></span>
      <div class="popup" part="popup" id="${this._tooltipId}" role="tooltip" hidden>
        <div class="content" part="content"><slot>${content}</slot></div>
      </div>
      <div class="arrow" part="arrow" aria-hidden="true" hidden></div>
    `
    return markup
  }

  afterRender() {
    this._popup = this.$(".popup")
    this._arrow = this.$(".arrow")
    this._triggerSlot = this.$("slot[name='trigger']")
    this.listen(this._triggerSlot, "slotchange", this._onSlotChange.bind(this))
    this._attachTriggerListeners()

    this.listen(this._popup, "pointerenter", this._cancelHide.bind(this))
    this.listen(this._popup, "pointerleave", this._scheduleHide.bind(this, "hover"))

    if (this.hasAttribute("open")) {
      this._show("api")
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._popup === undefined) {
      return
    }

    if (name === "open") {
      if (newValue !== null) {
        this._show("api")
      } else {
        this._hide("api")
      }
    }

    if (name === "content") {
      const defaultSlot = this.$("slot:not([name])")
      if (defaultSlot !== null) {
        defaultSlot.textContent = newValue || ""
      }
    }

    if (name === "max-width") {
      if (this._popup !== null) {
        this._popup.style.maxWidth = newValue ? `${newValue}px` : ""
      }
    }
    return
  }

  _onSlotChange() {
    this._detachTriggerListeners()
    this._attachTriggerListeners()
    return
  }

  _attachTriggerListeners() {
    const slot = this._triggerSlot
    if (slot === null) {
      return
    }
    const assigned = slot.assignedElements()
    const el = assigned.length > 0 ? assigned[0] : null
    this._triggerEl = el

    if (el === null) {
      return
    }

    const triggerStr = this.getAttribute("trigger") || "hover focus"
    const useHover = triggerStr.includes("hover")
    const useFocus = triggerStr.includes("focus")

    if (useHover === true) {
      this._boundPointerEnter = this._onPointerEnter.bind(this)
      this._boundPointerLeave = this._onPointerLeave.bind(this)
      el.addEventListener("pointerenter", this._boundPointerEnter)
      el.addEventListener("pointerleave", this._boundPointerLeave)
    }

    if (useFocus === true) {
      this._boundFocusIn = this._onFocusIn.bind(this)
      this._boundFocusOut = this._onFocusOut.bind(this)
      el.addEventListener("focusin", this._boundFocusIn)
      el.addEventListener("focusout", this._boundFocusOut)
    }

    this._boundKeyDown = this._onTriggerKeyDown.bind(this)
    el.addEventListener("keydown", this._boundKeyDown)
    return
  }

  _detachTriggerListeners() {
    const el = this._triggerEl
    if (el === null) {
      return
    }
    if (this._boundPointerEnter !== undefined) {
      el.removeEventListener("pointerenter", this._boundPointerEnter)
      el.removeEventListener("pointerleave", this._boundPointerLeave)
    }
    if (this._boundFocusIn !== undefined) {
      el.removeEventListener("focusin", this._boundFocusIn)
      el.removeEventListener("focusout", this._boundFocusOut)
    }
    if (this._boundKeyDown !== undefined) {
      el.removeEventListener("keydown", this._boundKeyDown)
    }
    return
  }

  _onPointerEnter() {
    this._cancelHide()
    this._scheduleShow("hover")
    return
  }

  _onPointerLeave() {
    this._cancelShow()
    this._scheduleHide("hover")
    return
  }

  _onFocusIn() {
    this._cancelHide()
    this._scheduleShow("focus")
    return
  }

  _onFocusOut() {
    this._cancelShow()
    this._scheduleHide("focus")
    return
  }

  _onTriggerKeyDown(event) {
    if (event.key === "Escape" && this._popup !== null && this._popup.hidden === false) {
      this._cancelShow()
      this._cancelHide()
      this._hide("escape")
    }
    return
  }

  _scheduleShow(trigger) {
    if (this.hasAttribute("disabled")) {
      return
    }
    const delay = parseInt(this.getAttribute("show-delay") || "300", 10)
    this._showTimer = setTimeout(() => {
      this._show(trigger)
    }, delay)
    return
  }

  _scheduleHide(trigger) {
    const delay = parseInt(this.getAttribute("hide-delay") || "100", 10)
    this._hideTimer = setTimeout(() => {
      this._hide(trigger)
    }, delay)
    return
  }

  _cancelShow() {
    if (this._showTimer !== null) {
      clearTimeout(this._showTimer)
      this._showTimer = null
    }
    return
  }

  _cancelHide() {
    if (this._hideTimer !== null) {
      clearTimeout(this._hideTimer)
      this._hideTimer = null
    }
    return
  }

  _show(trigger) {
    const proceed = this.emit("mj-tooltip-show", { trigger: trigger }, { cancelable: true })
    if (proceed === false) {
      return
    }

    const popup = this._popup
    if (popup === null) {
      return
    }
    popup.hidden = false

    const triggerEl = this._triggerEl
    if (triggerEl !== null) {
      triggerEl.setAttribute("aria-describedby", this._tooltipId)

      const placement = this.getAttribute("placement") || "top"
      const offset = parseInt(this.getAttribute("offset") || "8", 10)
      position(popup, triggerEl, { placement: placement, offset: offset })
      this._positionArrow(placement)
    }

    this.setAttribute("open", "")
    return
  }

  _hide(trigger) {
    const proceed = this.emit("mj-tooltip-hide", { trigger: trigger }, { cancelable: true })
    if (proceed === false) {
      return
    }

    const popup = this._popup
    if (popup !== null) {
      popup.hidden = true
    }

    const arrow = this._arrow
    if (arrow !== null) {
      arrow.hidden = true
    }

    const triggerEl = this._triggerEl
    if (triggerEl !== null) {
      triggerEl.removeAttribute("aria-describedby")
    }

    this.removeAttribute("open")
    return
  }

  _positionArrow(placement) {
    const showArrow = this.getAttribute("arrow") !== "false"
    const arrow = this._arrow
    const popup = this._popup
    if (arrow === null || popup === null || showArrow === false) {
      if (arrow !== null) {
        arrow.hidden = true
      }
      return
    }

    const arrowSize = 6
    const popupRect = popup.getBoundingClientRect()
    let ax = 0
    let ay = 0
    const side = placement.split("-")[0]

    if (side === "top") {
      ax = popupRect.left + popupRect.width / 2 - arrowSize / 2
      ay = popupRect.bottom - arrowSize / 2
    } else if (side === "bottom") {
      ax = popupRect.left + popupRect.width / 2 - arrowSize / 2
      ay = popupRect.top - arrowSize / 2
    } else if (side === "start" || side === "left") {
      ax = popupRect.right - arrowSize / 2
      ay = popupRect.top + popupRect.height / 2 - arrowSize / 2
    } else {
      ax = popupRect.left - arrowSize / 2
      ay = popupRect.top + popupRect.height / 2 - arrowSize / 2
    }

    arrow.style.left = `${Math.round(ax)}px`
    arrow.style.top = `${Math.round(ay)}px`
    arrow.hidden = false
    return
  }

  onDisconnected() {
    this._detachTriggerListeners()
    this._cancelShow()
    this._cancelHide()
    return
  }

  get open() {
    return this.hasAttribute("open")
  }

  set open(value) {
    if (value === true) {
      this._show("api")
    } else {
      this._hide("api")
    }
    return
  }

  get triggerElement() {
    return this._triggerEl
  }
}
