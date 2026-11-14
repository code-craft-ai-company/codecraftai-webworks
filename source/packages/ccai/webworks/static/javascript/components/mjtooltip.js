/*
 * mjtooltip.js
 *
 * <mj-tooltip> -- hover/focus-triggered supplemental hint anchored to a
 * trigger slot element. Fully keyboard accessible; WCAG 1.4.13 compliant:
 * hoverable, dismissible (Escape, wherever focus is), and persistent while
 * pointer/focus is inside.
 *
 * Description wiring: the popup lives in this component's shadow root, where
 * an aria-describedby id from the light-DOM trigger can never resolve. The
 * tooltip text is therefore mirrored into a hidden light-DOM child of the
 * host (slot="mj-tooltip-description", which no slot renders) and the trigger
 * references that node. The description is available whenever the trigger
 * has focus, whether or not the popup is showing.
 *
 * `disabled` suppresses the tooltip only; the slotted trigger stays fully
 * interactive.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { position } from "../core/overlay.js";
import { html } from "../core/html.js";

const STYLES = `
:host { display: inline-block; position: relative; }

/*
 * The shared base sheet makes a disabled host ignore the pointer, and that
 * is inherited by the slotted trigger. Here "disabled" turns the tooltip
 * off, not the trigger.
 */
:host([disabled]) { pointer-events: auto; cursor: auto; }

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
  z-index: var(--mj-tooltip-z-index, var(--mj-layer-tooltip));
  width: var(--mj-tooltip-arrow-size, 6px);
  height: var(--mj-tooltip-arrow-size, 6px);
  background: var(--mj-tooltip-bg, var(--mj-color-neutral-800));
  transform: rotate(45deg);
  pointer-events: none;
}
.arrow[hidden] { display: none; }
`;

/* Slot name of the light-DOM description node; no slot with this name exists. */
const DESCRIPTION_SLOT = "mj-tooltip-description";

export class MjTooltip extends MjElement {
  static tagName = "mj-tooltip";
  static styles = STYLES;
  static watched = ["content", "placement", "trigger", "show-delay", "hide-delay", "open", "disabled", "arrow", "max-width"];

  constructor() {
    super()
    this._tooltipId = nextId("mj-tooltip")
    this._descriptionId = `${this._tooltipId}-description`
    this._showTimer = null
    this._hideTimer = null
    this._triggerEl = null
    this._popup = null
    this._arrow = null

    /* True while the popup is showing. The `open` attribute mirrors it. */
    this._isOpen = false

    /* Removers of the listeners attached to the current trigger element. */
    this._triggerDisposers = []

    /* Light-DOM node that carries the tooltip text for aria-describedby. */
    this._descriptionEl = null

    /* The span that shows the `content` attribute in the popup. */
    this._contentTextEl = null

    /* Handlers that exist only while the popup is open. */
    this._onDocumentKeyDown = this._handleDocumentKeyDown.bind(this)
    this._onViewportChange = this._reposition.bind(this)
    this._trackingOpen = false
  }

  /*
   * The `content` text sits next to the default slot instead of being its
   * fallback content: whitespace between the tags is slotted too and would
   * suppress a fallback. `_syncContent` shows it while nothing meaningful is
   * slotted.
   */
  render() {
    const content = this.getAttribute("content") || ""
    const markup = html`
      <span class="trigger-wrap" part="trigger"><slot name="trigger"></slot></span>
      <div class="popup" part="popup" id="${this._tooltipId}" role="tooltip" hidden>
        <div class="content" part="content"><slot></slot><span class="content-text">${content}</span></div>
      </div>
      <div class="arrow" part="arrow" aria-hidden="true" hidden></div>
    `
    return markup
  }

  afterRender() {
    this._popup = this.$(".popup")
    this._arrow = this.$(".arrow")
    this._triggerSlot = this.$("slot[name='trigger']")
    this._contentSlot = this.$("slot:not([name])")
    this._contentTextEl = this.$(".content-text")
    this._isOpen = false

    this.listen(this._triggerSlot, "slotchange", this._onSlotChange.bind(this))
    this.listen(this._contentSlot, "slotchange", this._onContentSlotChange.bind(this))
    this._syncContent()
    this._attachTriggerListeners()

    this.listen(this._popup, "pointerenter", this._cancelHide.bind(this))
    this.listen(this._popup, "pointerleave", this._scheduleHide.bind(this, "hover"))

    this._syncMaxWidth()

    if (this.hasAttribute("open")) {
      this._show("api")
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._popup === undefined || this._popup === null) {
      return
    }

    if (name === "open") {
      /*
       * _show and _hide write this attribute themselves, so act only when
       * the attribute disagrees with the state the popup is already in.
       */
      if (newValue !== null && this._isOpen === false) {
        this._show("api")
      } else if (newValue === null && this._isOpen === true) {
        this._hide("api")
      }
    }

    if (name === "content") {
      this._syncContent()
      this._syncDescription()
      if (this._isOpen === true) {
        this._reposition()
      }
    }

    if (name === "max-width") {
      this._syncMaxWidth()
    }

    if (name === "trigger") {
      this._detachTriggerListeners()
      this._attachTriggerListeners()
    }

    if (name === "placement" || name === "arrow") {
      if (this._isOpen === true) {
        this._reposition()
      }
    }

    if (name === "disabled" && newValue !== null) {
      this._cancelShow()
      if (this._isOpen === true) {
        this._hide("api")
      }
    }
    return
  }

  /* Apply the max-width attribute (a number of CSS px) to the popup. */
  _syncMaxWidth() {
    if (this._popup === undefined || this._popup === null) {
      return
    }
    const width = parseFloat(this.getAttribute("max-width"))
    if (Number.isFinite(width) === true && width > 0) {
      this._popup.style.maxWidth = `${width}px`
    } else {
      this._popup.style.maxWidth = ""
    }
    return
  }

  _onSlotChange() {
    this._detachTriggerListeners()
    this._attachTriggerListeners()
    return
  }

  /* Add a listener to the trigger element and remember how to remove it. */
  _listenToTrigger(type, handler) {
    const triggerEl = this._triggerEl
    triggerEl.addEventListener(type, handler)
    this._triggerDisposers.push(() => {
      triggerEl.removeEventListener(type, handler)
    })
    return
  }

  _attachTriggerListeners() {
    const slot = this._triggerSlot
    if (slot === undefined || slot === null) {
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
      this._listenToTrigger("pointerenter", this._onPointerEnter.bind(this))
      this._listenToTrigger("pointerleave", this._onPointerLeave.bind(this))
    }

    if (useFocus === true) {
      this._listenToTrigger("focusin", this._onFocusIn.bind(this))
      this._listenToTrigger("focusout", this._onFocusOut.bind(this))
    }

    this._attachDescription()
    return
  }

  _detachTriggerListeners() {
    for (let index = 0; index < this._triggerDisposers.length; index = index + 1) {
      const dispose = this._triggerDisposers[index]
      dispose()
    }
    this._triggerDisposers = []

    this._detachDescription()
    this._triggerEl = null
    return
  }

  /* ----- popup content ----- */

  /*
   * True when the default slot holds tooltip content: an element, or text
   * that is not only whitespace.
   */
  _hasSlottedContent() {
    let found = false
    if (this._contentSlot !== undefined && this._contentSlot !== null) {
      const nodes = this._contentSlot.assignedNodes({ flatten: true })
      for (let index = 0; index < nodes.length; index = index + 1) {
        const node = nodes[index]
        const isElement = node.nodeType === Node.ELEMENT_NODE
        const isText = node.nodeType === Node.TEXT_NODE && node.textContent.trim() !== ""
        if (isElement === true || isText === true) {
          found = true
          break
        }
      }
    }
    return found
  }

  /* Show the `content` text while nothing meaningful is slotted. */
  _syncContent() {
    if (this._contentTextEl === undefined || this._contentTextEl === null) {
      return
    }
    this._contentTextEl.textContent = this.getAttribute("content") || ""
    this._contentTextEl.hidden = this._hasSlottedContent() === true
    return
  }

  _onContentSlotChange() {
    this._syncContent()
    this._syncDescription()
    if (this._isOpen === true) {
      this._reposition()
    }
    return
  }

  /* ----- accessible description ----- */

  /* The tooltip text: the slotted content, else the `content` attribute. */
  _getTooltipText() {
    let text = ""
    if (this._contentSlot !== undefined && this._contentSlot !== null) {
      const nodes = this._contentSlot.assignedNodes({ flatten: true })
      for (let index = 0; index < nodes.length; index = index + 1) {
        text = text + nodes[index].textContent
      }
    }
    text = text.replace(/\s+/g, " ").trim()
    if (text === "") {
      text = this.getAttribute("content") || ""
    }
    return text
  }

  /*
   * Create the light-DOM description node and reference it from the trigger.
   * An aria-describedby the trigger already carries is kept.
   */
  _attachDescription() {
    const triggerEl = this._triggerEl
    if (triggerEl === null) {
      return
    }

    if (this._descriptionEl === null) {
      const description = document.createElement("span")
      description.id = this._descriptionId
      description.hidden = true
      description.setAttribute("slot", DESCRIPTION_SLOT)
      this._descriptionEl = description
    }
    if (this._descriptionEl.parentNode !== this) {
      this.appendChild(this._descriptionEl)
    }
    this._syncDescription()

    const existing = triggerEl.getAttribute("aria-describedby") || ""
    const ids = existing.split(/\s+/).filter((id) => id.length > 0)
    if (ids.indexOf(this._descriptionId) < 0) {
      ids.push(this._descriptionId)
      triggerEl.setAttribute("aria-describedby", ids.join(" "))
    }
    return
  }

  _detachDescription() {
    const triggerEl = this._triggerEl
    if (triggerEl !== null) {
      const existing = triggerEl.getAttribute("aria-describedby") || ""
      const ids = existing.split(/\s+/).filter((id) => id.length > 0 && id !== this._descriptionId)
      if (ids.length > 0) {
        triggerEl.setAttribute("aria-describedby", ids.join(" "))
      } else {
        triggerEl.removeAttribute("aria-describedby")
      }
    }

    if (this._descriptionEl !== null && this._descriptionEl.parentNode !== null) {
      this._descriptionEl.remove()
    }
    return
  }

  _syncDescription() {
    if (this._descriptionEl !== null) {
      const text = this._getTooltipText()
      if (this._descriptionEl.textContent !== text) {
        this._descriptionEl.textContent = text
      }
    }
    return
  }

  /* ----- trigger events ----- */

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

  /*
   * Escape dismisses the tooltip wherever focus is: a tooltip opened by
   * hover must be dismissible without moving the pointer or the focus.
   */
  /*
   * Escape closes an open tooltip and nothing else. The tooltip is placed with
   * position(), not autoPosition(), so the overlay layer does not know it is
   * open; preventDefault() is what tells a surrounding mj-dialog / mj-drawer
   * (claimEscape) that this key press was already handled.
   */
  _handleDocumentKeyDown(event) {
    if (event.key === "Escape" && this._isOpen === true && event.defaultPrevented === false) {
      event.preventDefault()
      this._cancelShow()
      this._cancelHide()
      this._hide("escape")
    }
    return
  }

  _delayFrom(attributeName, fallback) {
    const parsed = parseInt(this.getAttribute(attributeName), 10)
    const delay = Number.isFinite(parsed) === true && parsed >= 0 ? parsed : fallback
    return delay
  }

  /* One show timer at most: a second trigger event replaces the first. */
  _scheduleShow(trigger) {
    this._cancelShow()
    if (this.hasAttribute("disabled")) {
      return
    }
    const delay = this._delayFrom("show-delay", 300)
    this._showTimer = setTimeout(() => {
      this._showTimer = null
      this._show(trigger)
    }, delay)
    return
  }

  _scheduleHide(trigger) {
    this._cancelHide()
    const delay = this._delayFrom("hide-delay", 100)
    this._hideTimer = setTimeout(() => {
      this._hideTimer = null
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

  /* ----- show / hide ----- */

  _show(trigger) {
    const popup = this._popup
    if (popup === undefined || popup === null || this._isOpen === true) {
      return
    }

    const proceed = this.emit("mj-tooltip-show", { trigger: trigger }, { cancelable: true })
    if (proceed === false) {
      /* Vetoed: the attribute must not claim the tooltip is open. */
      if (this.hasAttribute("open") === true) {
        this.removeAttribute("open")
      }
      return
    }

    this._isOpen = true
    popup.hidden = false
    this._syncDescription()
    this._reposition()
    this._startOpenTracking()

    if (this.hasAttribute("open") === false) {
      this.setAttribute("open", "")
    }
    return
  }

  _hide(trigger) {
    if (this._isOpen === false) {
      return
    }

    const proceed = this.emit("mj-tooltip-hide", { trigger: trigger }, { cancelable: true })
    if (proceed === false) {
      /* Vetoed: the attribute must keep saying the tooltip is open. */
      if (this.hasAttribute("open") === false) {
        this.setAttribute("open", "")
      }
      return
    }

    this._isOpen = false
    this._stopOpenTracking()

    const popup = this._popup
    if (popup !== null) {
      popup.hidden = true
    }

    const arrow = this._arrow
    if (arrow !== null) {
      arrow.hidden = true
    }

    if (this.hasAttribute("open") === true) {
      this.removeAttribute("open")
    }
    return
  }

  /* While open: Escape anywhere dismisses, scroll and resize re-anchor. */
  _startOpenTracking() {
    if (this._trackingOpen === true) {
      return
    }
    this._trackingOpen = true
    document.addEventListener("keydown", this._onDocumentKeyDown, true)
    window.addEventListener("scroll", this._onViewportChange, true)
    window.addEventListener("resize", this._onViewportChange)
    return
  }

  _stopOpenTracking() {
    if (this._trackingOpen === false) {
      return
    }
    this._trackingOpen = false
    document.removeEventListener("keydown", this._onDocumentKeyDown, true)
    window.removeEventListener("scroll", this._onViewportChange, true)
    window.removeEventListener("resize", this._onViewportChange)
    return
  }

  /*
   * Translate the `placement` attribute into the vocabulary of the overlay
   * engine, whose "start" side is the physical left and "end" the physical
   * right. left / right are physical; start / end follow the direction.
   */
  _resolvePlacement() {
    const requested = this.getAttribute("placement") || "top"
    const parts = requested.split("-")
    let side = parts[0]

    const rtl = window.getComputedStyle(this).direction === "rtl"
    if (side === "left") {
      side = "start"
    } else if (side === "right") {
      side = "end"
    } else if (side === "start" && rtl === true) {
      side = "end"
    } else if (side === "end" && rtl === true) {
      side = "start"
    } else if (side !== "top" && side !== "bottom" && side !== "start" && side !== "end") {
      side = "top"
    }

    const placement = parts.length > 1 ? `${side}-${parts[1]}` : side
    return placement
  }

  /* Anchor the popup to the trigger and point the arrow at it. */
  _reposition() {
    const popup = this._popup
    const triggerEl = this._triggerEl
    if (popup === undefined || popup === null || triggerEl === null || this._isOpen === false) {
      return
    }

    const parsedOffset = parseInt(this.getAttribute("offset") || "8", 10)
    const offset = Number.isFinite(parsedOffset) === true ? parsedOffset : 8

    /* The engine may flip the popup to the other side; it returns where it ended up. */
    const resolved = position(popup, triggerEl, { placement: this._resolvePlacement(), offset: offset })

    /* The engine writes a popover z-index inline; the tooltip layer is in the stylesheet. */
    popup.style.zIndex = ""

    this._positionArrow(resolved)
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
    } else if (side === "start") {
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
    this._cancelShow()
    this._cancelHide()
    this._stopOpenTracking()
    this._detachTriggerListeners()

    /* The shadow DOM is rebuilt, closed, on the next connect. */
    this._isOpen = false
    return
  }

  get open() {
    return this.hasAttribute("open")
  }

  set open(value) {
    const open = Boolean(value)
    if (this._popup === undefined || this._popup === null) {
      /* Not rendered yet: the attribute is acted on at the first render. */
      this.toggleAttribute("open", open)
      return
    }

    if (open === true) {
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
