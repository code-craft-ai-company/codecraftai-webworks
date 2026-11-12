/*
 * mjfab.js
 *
 * <mj-fab> -- Floating Action Button component.
 *
 * Provides a prominent, fixed-position button for the single most important
 * action on a screen. Supports standard (icon-only) and extended (icon + label)
 * modes, four viewport-corner positions, and an optional speed-dial that reveals
 * sub-action buttons.
 */

import { MjElement } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";

const STYLES = `
:host {
  position: fixed;
  display: block;
  z-index: var(--mj-fab-z-index, var(--mj-layer-overlay));
}
:host(:not([position]):not([anchor])),
:host([position="bottom-end"])   { inset-block-end: var(--mj-fab-offset-y, 1rem); inset-inline-end: var(--mj-fab-offset-x, 1rem); }
:host([position="bottom-start"]) { inset-block-end: var(--mj-fab-offset-y, 1rem); inset-inline-start: var(--mj-fab-offset-x, 1rem); }
:host([position="top-end"])      { inset-block-start: var(--mj-fab-offset-y, 1rem); inset-inline-end: var(--mj-fab-offset-x, 1rem); }
:host([position="top-start"])    { inset-block-start: var(--mj-fab-offset-y, 1rem); inset-inline-start: var(--mj-fab-offset-x, 1rem); }

.fab {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--mj-space-2);
  width: var(--mj-fab-size, 3.5rem);
  height: var(--mj-fab-size, 3.5rem);
  min-width: var(--mj-target-min);
  min-height: var(--mj-target-min);
  padding: 0;
  font: inherit;
  font-weight: var(--mj-font-weight-medium);
  color: var(--mj-fab-color, var(--mj-text-on-accent));
  background: var(--mj-fab-bg, var(--mj-accent));
  border: none;
  border-radius: var(--mj-fab-border-radius, var(--mj-radius-circle));
  box-shadow: var(--mj-fab-elevation, var(--mj-elevation-3));
  cursor: pointer;
  user-select: none;
  transition: background var(--mj-motion-fast) var(--mj-motion-ease),
              box-shadow var(--mj-motion-fast) var(--mj-motion-ease);
}
.fab:hover { background: var(--mj-accent-hover); box-shadow: var(--mj-elevation-3); }
.fab:active { background: var(--mj-accent-active); box-shadow: var(--mj-elevation-2); }
.fab:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-fab-focus-ring-color, var(--mj-focus-ring));
  outline-offset: var(--mj-focus-ring-offset);
}

:host([size="sm"]) .fab { width: 2.5rem; height: 2.5rem; }
:host([size="lg"]) .fab { width: 4rem; height: 4rem; }
:host([size="extended"]) .fab {
  width: auto;
  height: var(--mj-control-height-lg);
  padding: 0 var(--mj-space-5);
  border-radius: var(--mj-radius-pill);
}

:host(:not([size="extended"])) .label { display: none; }

:host([disabled]) .fab,
:host([loading]) .fab { opacity: 0.55; cursor: not-allowed; }
:host([loading]) .fab { cursor: progress; }

.spinner {
  width: 1.25em; height: 1.25em;
  border: 2px solid currentColor;
  border-inline-end-color: transparent;
  border-radius: var(--mj-radius-circle);
  animation: mj-fab-spin var(--mj-motion-slow) linear infinite;
}
:host(:not([loading])) .spinner { display: none; }
@keyframes mj-fab-spin { to { transform: rotate(360deg); } }

.speed-dial-list {
  list-style: none;
  margin: 0;
  padding: var(--mj-space-2) 0;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--mj-fab-speed-dial-gap, var(--mj-space-3));
  position: absolute;
  inset-block-end: calc(100% + var(--mj-space-3));
  inset-inline-end: 0;
}
/* Pinned to the top edge: the list opens below the button, not off-screen. */
:host([position^="top"]) .speed-dial-list {
  inset-block-end: auto;
  inset-block-start: calc(100% + var(--mj-space-3));
}
/* Pinned to the start edge: the list grows toward the viewport, not out of it. */
:host([position$="start"]) .speed-dial-list {
  align-items: flex-start;
  inset-inline-end: auto;
  inset-inline-start: 0;
}
:host(:not([expanded])) .speed-dial-list,
:host([expanded="false"]) .speed-dial-list { display: none; }

@media (prefers-reduced-motion: reduce) {
  .fab { transition: none; }
}
`;

/* True when `element` is a custom element (its focus is delegated inside). */
function isCustomElement(element) {
  const custom = element.localName.indexOf("-") >= 0
  return custom
}

export class MjFab extends MjElement {
  static tagName = "mj-fab";
  static styles = STYLES;
  static watched = ["size", "label", "position", "loading", "speed-dial", "expanded", "offset-x", "offset-y"];

  constructor() {
    super()
    this._button = null
    this._speedDialList = null
    this._speedDialSlot = null

    /* Expanded state last reported through mj-expanded. */
    this._expandedState = false

    /* True once the missing-label warning was logged. */
    this._warnedMissingLabel = false
  }

  render() {
    const markup = `
      <button class="fab" part="button" type="button">
        <span class="spinner" part="spinner" aria-hidden="true"></span>
        <span class="icon" part="icon"><slot name="icon"></slot></span>
        <span class="label" part="label"><slot></slot></span>
      </button>
      <div class="speed-dial-list" part="speed-dial-list" role="menu" aria-hidden="true">
        <slot name="speed-dial-item"></slot>
      </div>
    `
    return markup
  }

  afterRender() {
    this._button = this.$(".fab")
    this._speedDialList = this.$(".speed-dial-list")
    this._speedDialSlot = this.$("slot[name='speed-dial-item']")
    const labelSlot = this.$(".label slot")

    this.listen(this._button, "click", this._onClick.bind(this))
    this.listen(this._button, "keydown", this._onButtonKeydown.bind(this))
    this.listen(this._speedDialList, "click", this._onItemClick.bind(this))
    this.listen(this._speedDialList, "keydown", this._onListKeydown.bind(this))
    this.listen(this._speedDialSlot, "slotchange", this._syncItems.bind(this))
    this.listen(labelSlot, "slotchange", this._syncAccessibility.bind(this))

    /* Escape and focus loss are handled only while focus is in the component. */
    this.listen(this, "keydown", this._onKeydown.bind(this))
    this.listen(this, "focusout", this._onFocusOut.bind(this))
    this.listen(document, "click", this._onDocClick.bind(this))

    this._expandedState = this._isExpanded()
    this._syncOffsets()
    this._syncItems()
    this._syncAccessibility()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._button === undefined || this._button === null) {
      return
    }

    if (name === "offset-x" || name === "offset-y") {
      this._syncOffsets()
    }

    this._syncAccessibility()

    if (name === "expanded") {
      this._reportExpanded()
    }
    return
  }

  /* `expanded="false"` is collapsed, matching the stylesheet. */
  _isExpanded() {
    const value = this.getAttribute("expanded")
    const expanded = value !== null && value !== "false"
    return expanded
  }

  /*
   * Notify listeners when the open state really changed, whichever way it was
   * changed (property, attribute, user). A repeated or replayed attribute
   * change with the same boolean state reports nothing.
   */
  _reportExpanded() {
    const expanded = this._isExpanded()
    if (expanded === this._expandedState) {
      return
    }
    this._expandedState = expanded
    this.emit("mj-expanded", { expanded: expanded })
    return
  }

  /* Map the offset-x / offset-y attributes onto the custom properties the styles read. */
  _syncOffsets() {
    const offsetX = this.getAttribute("offset-x")
    const offsetY = this.getAttribute("offset-y")

    if (offsetX !== null && offsetX !== "") {
      this.style.setProperty("--mj-fab-offset-x", offsetX)
    } else {
      this.style.removeProperty("--mj-fab-offset-x")
    }

    if (offsetY !== null && offsetY !== "") {
      this.style.setProperty("--mj-fab-offset-y", offsetY)
    } else {
      this.style.removeProperty("--mj-fab-offset-y")
    }
    return
  }

  /* The slotted speed-dial actions, in document order. */
  _getItems() {
    let items = []
    if (this._speedDialSlot !== null) {
      items = this._speedDialSlot.assignedElements({ flatten: true })
    }
    return items
  }

  /*
   * Give every slotted action the menuitem role. Actions are reached with
   * the arrow keys, so native controls are taken out of the tab order;
   * custom elements manage their own inner focus target.
   */
  _syncItems() {
    const items = this._getItems()
    for (let index = 0; index < items.length; index = index + 1) {
      const item = items[index]
      if (item.hasAttribute("role") === false) {
        item.setAttribute("role", "menuitem")
      }
      if (isCustomElement(item) === false && item.hasAttribute("tabindex") === false) {
        item.setAttribute("tabindex", "-1")
      }
    }
    return
  }

  _isItemDisabled(item) {
    const disabled =
      item.hasAttribute("disabled") === true || item.getAttribute("aria-disabled") === "true"
    return disabled
  }

  /* Index of the action that currently holds focus, or -1. */
  _focusedItemIndex(items) {
    let focusedIndex = -1
    const active = this.getRootNode().activeElement
    for (let index = 0; index < items.length; index = index + 1) {
      const item = items[index]
      if (item === active || item.contains(active) === true) {
        focusedIndex = index
        break
      }
    }
    return focusedIndex
  }

  /* Focus the enabled action at `startIndex`, or the next one in `step` direction. */
  _focusItem(items, startIndex, step) {
    const count = items.length
    let index = startIndex

    for (let attempt = 0; attempt < count; attempt = attempt + 1) {
      const wrapped = ((index % count) + count) % count
      const item = items[wrapped]
      if (this._isItemDisabled(item) === false) {
        item.focus()
        break
      }
      index = index + step
    }
    return
  }

  _syncAccessibility() {
    if (this._button === undefined || this._button === null) {
      return
    }

    const disabled = this.hasAttribute("disabled")
    const loading = this.hasAttribute("loading")
    const inert = disabled === true || loading === true
    const isSpeedDial = this.hasAttribute("speed-dial")
    const expanded = this._isExpanded()

    this._button.disabled = inert
    this._button.setAttribute("aria-busy", loading === true ? "true" : "false")

    /*
     * The name is the `label` attribute, else the slotted label text (which
     * is not displayed in the icon-only sizes). Without either the button is
     * unnamed, which is reported once.
     */
    let label = this.getAttribute("label")
    if (label === null || label.trim() === "") {
      label = ""
      const labelSlot = this.$(".label slot")
      const nodes = labelSlot !== null ? labelSlot.assignedNodes({ flatten: true }) : []
      for (let index = 0; index < nodes.length; index = index + 1) {
        label = label + nodes[index].textContent
      }
      label = label.trim()
    }

    if (label.length > 0) {
      this._button.setAttribute("aria-label", label)
    } else {
      this._button.removeAttribute("aria-label")
      if (this._warnedMissingLabel === false) {
        this._warnedMissingLabel = true
        console.warn("mj-fab: set the `label` attribute so the button has an accessible name.", this)
      }
    }

    if (isSpeedDial === true) {
      this._button.setAttribute("aria-haspopup", "menu")
      this._button.setAttribute("aria-expanded", expanded === true ? "true" : "false")
    } else {
      this._button.removeAttribute("aria-haspopup")
      this._button.removeAttribute("aria-expanded")
    }

    if (this._speedDialList !== null) {
      if (expanded === true) {
        this._speedDialList.removeAttribute("aria-hidden")
      } else {
        this._speedDialList.setAttribute("aria-hidden", "true")
      }
      if (label.length > 0) {
        this._speedDialList.setAttribute("aria-label", label)
      } else {
        this._speedDialList.removeAttribute("aria-label")
      }
    }
    return
  }

  _onClick(event) {
    const blocked = this.hasAttribute("disabled") || this.hasAttribute("loading")
    if (blocked === true) {
      event.stopImmediatePropagation()
      event.preventDefault()
      return
    }

    const isSpeedDial = this.hasAttribute("speed-dial")
    if (isSpeedDial === true) {
      const opening = this._isExpanded() === false
      this.expanded = opening
      if (opening === true) {
        const items = this._getItems()
        if (items.length > 0) {
          this._focusItem(items, 0, 1)
        }
      }
      return
    }

    this.emit("mj-click", { originalEvent: event })
    return
  }

  /* Arrow Down / Arrow Up on the trigger open the dial on its first / last action. */
  _onButtonKeydown(event) {
    const isSpeedDial = this.hasAttribute("speed-dial")
    const isArrow = event.key === "ArrowDown" || event.key === "ArrowUp"
    const blocked = this.hasAttribute("disabled") || this.hasAttribute("loading")
    if (isSpeedDial === false || isArrow === false || blocked === true) {
      return
    }

    event.preventDefault()
    this.expanded = true

    const items = this._getItems()
    if (items.length > 0) {
      if (event.key === "ArrowDown") {
        this._focusItem(items, 0, 1)
      } else {
        this._focusItem(items, items.length - 1, -1)
      }
    }
    return
  }

  /* Roving focus between the speed-dial actions. */
  _onListKeydown(event) {
    const items = this._getItems()
    if (items.length === 0) {
      return
    }

    const current = this._focusedItemIndex(items)
    let handled = true

    if (event.key === "ArrowDown") {
      this._focusItem(items, current + 1, 1)
    } else if (event.key === "ArrowUp") {
      this._focusItem(items, current - 1, -1)
    } else if (event.key === "Home") {
      this._focusItem(items, 0, 1)
    } else if (event.key === "End") {
      this._focusItem(items, items.length - 1, -1)
    } else {
      handled = false
    }

    if (handled === true) {
      event.preventDefault()
      event.stopPropagation()
    }
    return
  }

  /* Choosing an action reports it, collapses the dial and returns focus. */
  _onItemClick(event) {
    const items = this._getItems()
    const path = event.composedPath()

    let chosen = null
    for (let index = 0; index < items.length; index = index + 1) {
      if (path.indexOf(items[index]) >= 0) {
        chosen = items[index]
        break
      }
    }

    if (chosen === null || this._isItemDisabled(chosen) === true) {
      return
    }

    const value = chosen.getAttribute("value")
    this.emit("mj-select", { item: chosen, value: value })

    if (this._isExpanded() === true) {
      this.expanded = false
      this._button.focus()
    }
    return
  }

  /*
   * Escape closes the dial only when the key was pressed inside the
   * component, so it never pulls focus away from another control.
   */
  _onKeydown(event) {
    if (event.key === "Escape" && this._isExpanded() === true) {
      event.stopPropagation()
      this.expanded = false
      this._button.focus()
    }
    return
  }

  /* Close the dial when focus moves to an element outside the component. */
  _onFocusOut(event) {
    const next = event.relatedTarget
    if (next === null || next === undefined) {
      return
    }

    const stillInside = next === this || this.contains(next) === true
    if (stillInside === false && this._isExpanded() === true) {
      this.expanded = false
    }
    return
  }

  _onDocClick(event) {
    if (this._isExpanded() === true && this.contains(event.target) === false) {
      this.expanded = false
    }
    return
  }

  /* ----- scriptable API ----- */

  get expanded() {
    const value = this._isExpanded()
    return value
  }

  /* mj-expanded is emitted by the attribute handler when the state changes. */
  set expanded(value) {
    this.reflectBoolean("expanded", Boolean(value))
    return
  }

  get loading() {
    const value = this.hasAttribute("loading")
    return value
  }

  set loading(value) {
    this.reflectBoolean("loading", Boolean(value))
    return
  }

  get disabled() {
    const value = this.hasAttribute("disabled")
    return value
  }

  set disabled(value) {
    this.reflectBoolean("disabled", Boolean(value))
    return
  }

  /*
   * Activates the button as a user click would (mj-click, or the speed dial
   * with speed-dial). HTMLElement.click() would only dispatch a click at the
   * host, which never reaches the inner button. Disabled / busy states are
   * honoured by the inner handler.
   */
  click() {
    if (this._button !== undefined && this._button !== null) {
      this._button.click()
    }
    return
  }

  focus(options) {
    if (this._button !== undefined && this._button !== null) {
      this._button.focus(options)
    }
    return
  }
}
