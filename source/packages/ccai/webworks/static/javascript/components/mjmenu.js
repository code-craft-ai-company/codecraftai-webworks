/*
 * mjmenu.js
 *
 * <mj-menu> -- WAI-ARIA menu/menuitem popup primitive.
 * Keyboard focus is real DOM focus that roves over the slotted items (an ID
 * reference such as aria-activedescendant cannot point from the shadow menu
 * to light-DOM items); overlay.js positions the popup against its trigger.
 * The dropdown variant is implemented; `mega` only widens the popup.
 *
 * Items are chosen with the keyboard (Enter / Space) or the pointer (click).
 * Opening and closing go through one path each, and the cancelable
 * `mj-menu-open` / `mj-menu-close` events fire before anything changes.
 *
 * WAI-ARIA: role=menu; role=menuitem; role=menuitemcheckbox; role=menuitemradio.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { deepActiveElement } from "../core/focustrap.js";
import { html } from "../core/html.js";
import { autoPosition } from "../core/overlay.js";
import { t } from "../core/intl.js";

const STYLES = `
:host { display: contents; }

.menu {
  position: fixed;
  z-index: var(--mj-menu-z-index, var(--mj-layer-popover));
  min-width: var(--mj-menu-min-width, 160px);
  max-height: var(--mj-menu-max-height, 360px);
  overflow-y: auto;
  background: var(--mj-menu-bg, var(--mj-surface));
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-menu-radius, var(--mj-radius-md));
  box-shadow: var(--mj-menu-shadow, var(--mj-elevation-3));
  padding: var(--mj-space-1) 0;
  outline: none;
}
:host(:not([open])) .menu { display: none; }

/* Items are slotted light-DOM nodes, so every item rule is a ::slotted rule. */
::slotted([role="menuitem"]),
::slotted([role="menuitemcheckbox"]),
::slotted([role="menuitemradio"]) {
  display: flex;
  align-items: center;
  gap: var(--mj-space-3);
  box-sizing: border-box;
  width: 100%;
  min-height: var(--mj-menu-item-height, 40px);
  margin: 0;
  padding: var(--mj-menu-item-padding, 0 var(--mj-space-4));
  border: none;
  background: none;
  cursor: pointer;
  user-select: none;
  font: inherit;
  font-size: var(--mj-font-size-sm);
  text-align: start;
  text-decoration: none;
  color: var(--mj-text);
  transition: background var(--mj-motion-fast) var(--mj-motion-ease);
  outline: none;
}
::slotted([data-active="true"]) { background: var(--mj-menu-item-focus-bg, var(--mj-bg-muted)); }
::slotted([data-active="true"]:focus-visible) {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: calc(0px - var(--mj-focus-ring-width));
}
::slotted([aria-disabled="true"]),
::slotted([disabled]) { opacity: 0.45; cursor: not-allowed; }

/* Checkable items reserve a leading column for their check mark. */
::slotted([role="menuitemcheckbox"])::before,
::slotted([role="menuitemradio"])::before {
  content: "";
  flex-shrink: 0;
  width: 1em;
  text-align: center;
}
::slotted([role="menuitemcheckbox"][aria-checked="true"])::before { content: "\\2713"; }
::slotted([role="menuitemradio"][aria-checked="true"])::before { content: "\\2022"; }

::slotted([role="separator"]),
::slotted(hr) {
  display: block;
  height: 1px;
  border: none;
  background: var(--mj-border);
  margin: var(--mj-space-1) 0;
}

::slotted([role="presentation"]),
::slotted([role="none"]) {
  display: block;
  padding: var(--mj-space-2) var(--mj-space-4) var(--mj-space-1);
  font-size: var(--mj-font-size-xs);
  font-weight: var(--mj-font-weight-medium);
  color: var(--mj-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.empty-notice {
  padding: var(--mj-space-2) var(--mj-space-4);
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text-muted);
}

:host([variant="mega"]) .menu {
  min-width: min(480px, 100vw);
}
`;

/*
 * Items nested in a slotted wrapper (a role="group" around a set of radio
 * items, say) are not slotted themselves, so no ::slotted rule reaches them.
 * These rules give them, and the separators and captions next to them, the
 * same look; they are adopted into the tree the menu lives in (the document,
 * or the shadow root of an enclosing component). `:where()` keeps their
 * specificity at zero, so any page rule still wins, as it does over the
 * ::slotted rules for direct children. A nested <mj-menu> is left alone.
 */
const NESTED = ":where(mj-menu > :not(mj-menu))";
const LIGHT_STYLES = `
${NESTED} :where([role="menuitem"], [role="menuitemcheckbox"], [role="menuitemradio"], [data-menu-item]) {
  display: flex;
  align-items: center;
  gap: var(--mj-space-3);
  box-sizing: border-box;
  width: 100%;
  min-height: var(--mj-menu-item-height, 40px);
  margin: 0;
  padding: var(--mj-menu-item-padding, 0 var(--mj-space-4));
  border: none;
  background: none;
  cursor: pointer;
  user-select: none;
  font: inherit;
  font-size: var(--mj-font-size-sm);
  text-align: start;
  text-decoration: none;
  color: var(--mj-text);
  transition: background var(--mj-motion-fast) var(--mj-motion-ease);
  outline: none;
}
${NESTED} :where([data-active="true"]) { background: var(--mj-menu-item-focus-bg, var(--mj-bg-muted)); }
${NESTED} :where([data-active="true"]:focus-visible) {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: calc(0px - var(--mj-focus-ring-width));
}
${NESTED} :where([role^="menuitem"][aria-disabled="true"], [role^="menuitem"][disabled]) {
  opacity: 0.45;
  cursor: not-allowed;
}
${NESTED} :where([role="menuitemcheckbox"], [role="menuitemradio"])::before {
  content: "";
  flex-shrink: 0;
  width: 1em;
  text-align: center;
}
${NESTED} :where([role="menuitemcheckbox"][aria-checked="true"])::before { content: "\\2713"; }
${NESTED} :where([role="menuitemradio"][aria-checked="true"])::before { content: "\\2022"; }
${NESTED} :where([role="separator"], hr) {
  display: block;
  height: 1px;
  border: none;
  background: var(--mj-border);
  margin: var(--mj-space-1) 0;
}
${NESTED} :where([role="presentation"], [role="none"]):where(:not(:has([role^="menuitem"], [data-menu-item]))) {
  display: block;
  padding: var(--mj-space-2) var(--mj-space-4) var(--mj-space-1);
  font-size: var(--mj-font-size-xs);
  font-weight: var(--mj-font-weight-medium);
  color: var(--mj-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
`;

let lightSheet = null;

/*
 * Adopt the nested-item rules into the tree a menu lives in (the document,
 * or the shadow root of an enclosing component). Idempotent.
 */
function adoptLightStyles(root) {
  if (root === null || root === undefined || root.adoptedStyleSheets === undefined) {
    return
  }
  if (lightSheet === null) {
    lightSheet = new CSSStyleSheet()
    lightSheet.replaceSync(LIGHT_STYLES)
  }
  if (root.adoptedStyleSheets.indexOf(lightSheet) === -1) {
    root.adoptedStyleSheets = [...root.adoptedStyleSheets, lightSheet]
  }
  return
}


const ITEM_ROLES = ["menuitem", "menuitemcheckbox", "menuitemradio"];
const NESTED_ITEM_SELECTOR =
  "[role='menuitem'], [role='menuitemcheckbox'], [role='menuitemradio'], [data-menu-item]";

export class MjMenu extends MjElement {
  static tagName = "mj-menu";
  static styles = STYLES;
  static watched = ["open", "variant", "anchor", "placement", "label", "close-on-select"];

  constructor() {
    super()
    this._menuId = nextId("mj-menu")
    this._itemEls = []
    this._activeItem = null
    this._disposePosition = null

    /* True from a completed open until the matching close. */
    this._showing = false

    /* Reason of a close this component already announced, until the attribute callback runs. */
    this._announcedCloseReason = null

    /* A trigger element assigned through the `triggerElement` property. */
    this._triggerOverride = null
  }

  render() {
    const markup = html`
      <div class="menu" part="menu"
        role="menu"
        id="${this._menuId}"
        tabindex="-1">
        <slot></slot>
        <div class="empty-notice" part="empty-notice" hidden>${t("mj.menu.empty")}</div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._menu = this.$(".menu")
    this._emptyNotice = this.$(".empty-notice")
    this._slot = this.shadowRoot.querySelector("slot")

    adoptLightStyles(this.getRootNode())

    this.listen(this._menu, "keydown", this._onKeydown.bind(this))
    this.listen(this._menu, "click", this._onClick.bind(this))
    this.listen(this._menu, "mouseover", this._onMouseOver.bind(this))
    this.listen(this._slot, "slotchange", this._onSlotChange.bind(this))

    this.listen(document, "mousedown", this._onDocMousedown.bind(this))
    this.listen(document, "keydown", this._onDocKeydown.bind(this))

    this.onTeardown(() => {
      /* Removed from the page: nothing is announced, the popup state is just dropped. */
      this._stopPositioning()
      this._showing = false
    })

    this._buildItems()
    this._syncLabel()

    if (this.hasAttribute("open") === true) {
      this._openMenu()
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._menu === undefined || this._menu === null) {
      return
    }

    if (name === "open") {
      if (newValue !== null) {
        this._openMenu()
      } else {
        this._onOpenRemoved()
      }
    } else if (name === "label" || name === "anchor") {
      this._syncLabel()
      if (name === "anchor" && this._showing === true) {
        this._startPositioning()
      }
    } else if (name === "placement" && this._showing === true) {
      this._startPositioning()
    }
    return
  }

  _onSlotChange() {
    this._buildItems()
    return
  }

  /*
   * Name the menu: the `label` attribute, else the trigger's accessible name.
   * The trigger lives outside this shadow root, so aria-labelledby cannot
   * reference it; its name is copied instead. No name: no (empty) aria-label.
   */
  _syncLabel() {
    let label = this.getAttribute("label")

    if (label === null || label.length === 0) {
      const trigger = this._getTrigger()
      if (trigger !== null) {
        label = trigger.getAttribute("aria-label")
        if (label === null || label.length === 0) {
          label = trigger.textContent.trim()
        }
      }
    }

    if (label !== null && label.length > 0) {
      this._menu.setAttribute("aria-label", label)
    } else {
      this._menu.removeAttribute("aria-label")
    }
    return
  }

  _isItem(element) {
    const role = element.getAttribute("role")
    const isItem =
      ITEM_ROLES.indexOf(role) !== -1 ||
      element.classList.contains("item") === true ||
      element.hasAttribute("data-menu-item") === true
    return isItem
  }

  _registerItem(item) {
    if (item.id === "") {
      item.id = nextId("mj-menuitem")
    }
    if (item.hasAttribute("role") === false) {
      item.setAttribute("role", "menuitem")
    }
    item.setAttribute("tabindex", "-1")
    this._itemEls.push(item)
    return
  }

  /*
   * Collect the menu items: slotted items, and items nested inside slotted
   * wrappers such as a role="group". Idempotent -- it runs on every slot
   * change and every open.
   */
  _buildItems() {
    const assigned = this._slot.assignedElements({ flatten: true })
    this._itemEls = []

    for (let index = 0; index < assigned.length; index = index + 1) {
      const element = assigned[index]

      if (this._isItem(element) === true) {
        this._registerItem(element)
      } else if (element.matches("mj-menu") === false) {
        const nested = element.querySelectorAll(NESTED_ITEM_SELECTOR)
        for (let position = 0; position < nested.length; position = position + 1) {
          this._registerItem(nested[position])
        }
      }
    }

    if (this._itemEls.length === 0) {
      this._emptyNotice.removeAttribute("hidden")
    } else {
      this._emptyNotice.setAttribute("hidden", "")
    }

    if (this._activeItem !== null && this._itemEls.indexOf(this._activeItem) === -1) {
      this._activeItem.removeAttribute("data-active")
      this._activeItem = null
    }
    return
  }

  _isDisabled(item) {
    const disabled = item.getAttribute("aria-disabled") === "true" || item.hasAttribute("disabled") === true
    return disabled
  }

  /* The enabled items, in order. */
  _getItems() {
    const enabled = this._itemEls.filter((item) => {
      return this._isDisabled(item) === false
    })
    return enabled
  }

  /* The registered item an event passed through, or null. */
  _itemFromEvent(event) {
    let found = null
    const path = event.composedPath()

    for (let index = 0; index < this._itemEls.length; index = index + 1) {
      if (found === null && path.indexOf(this._itemEls[index]) !== -1) {
        found = this._itemEls[index]
      }
    }
    return found
  }

  /*
   * Open: announce first (cancelable), then show. A request while already
   * showing is ignored, so repeated `open` writes and the attribute replay
   * after the first render never stack listeners or observers.
   */
  _openMenu() {
    if (this._showing === true) {
      return
    }

    const trigger = this._getTrigger()
    const proceed = this.emit("mj-menu-open", { trigger: trigger }, { cancelable: true })
    if (proceed === false) {
      /* Take the attribute back; `_showing` is false so no close is announced. */
      this.removeAttribute("open")
      return
    }

    this._showing = true
    this._buildItems()
    this._syncLabel()

    if (trigger !== null) {
      trigger.setAttribute("aria-expanded", "true")
    }
    this._startPositioning()

    const items = this._getItems()
    if (items.length > 0) {
      this._setActive(items[0], true)
    } else {
      this._menu.focus()
    }
    return
  }

  /*
   * Ask to close for `reason`. The cancelable `mj-menu-close` fires before
   * the attribute changes; the attribute callback then finishes the close
   * without announcing it a second time.
   */
  _requestClose(reason) {
    if (this._showing === false) {
      if (this.hasAttribute("open") === true) {
        this.removeAttribute("open")
      }
      return
    }

    const proceed = this.emit("mj-menu-close", { reason: reason }, { cancelable: true })
    if (proceed === true) {
      this._announcedCloseReason = reason
      this.removeAttribute("open")
      this._announcedCloseReason = null
    }
    return
  }

  /* The `open` attribute was removed -- by `_requestClose` or from outside. */
  _onOpenRemoved() {
    if (this._showing === false) {
      return
    }

    if (this._announcedCloseReason === null) {
      const proceed = this.emit("mj-menu-close", { reason: "external" }, { cancelable: true })
      if (proceed === false) {
        /* Canceled: restore the attribute; `_showing` is still true so nothing reopens. */
        this.setAttribute("open", "")
        return
      }
    }

    this._finishClose()
    return
  }

  _finishClose() {
    const active = deepActiveElement()
    const focusWasInside =
      active !== null && (this.contains(active) === true || this.shadowRoot.contains(active) === true)

    this._showing = false
    this._stopPositioning()
    this._clearActive()

    const trigger = this._getTrigger()
    if (trigger !== null) {
      trigger.setAttribute("aria-expanded", "false")
      /* Focus returns to the trigger only when the menu held it. */
      if (focusWasInside === true) {
        trigger.focus()
      }
    }
    return
  }

  _startPositioning() {
    this._stopPositioning()

    const trigger = this._getTrigger()
    if (trigger !== null) {
      const placement = this.getAttribute("placement") || "bottom-start"
      this._disposePosition = autoPosition(this._menu, trigger, { placement: placement })
    }
    return
  }

  _stopPositioning() {
    if (this._disposePosition !== null) {
      this._disposePosition()
      this._disposePosition = null
    }
    return
  }

  /*
   * Resolve the trigger: an element assigned to `triggerElement`, else the
   * `anchor` attribute read as an id (in this element's tree, then in the
   * document) and only then as a CSS selector. An invalid selector resolves
   * to no trigger instead of throwing.
   */
  _getTrigger() {
    let found = this._triggerOverride

    const anchor = this.getAttribute("anchor")
    if (found === null && anchor !== null && anchor !== "") {
      const root = this.getRootNode()
      if (typeof root.getElementById === "function") {
        found = root.getElementById(anchor)
      }
      if (found === null) {
        found = document.getElementById(anchor)
      }
      if (found === null) {
        try {
          found = document.querySelector(anchor)
        } catch (error) {
          found = null
        }
      }
    }
    return found
  }

  /* Make `item` the active one: highlighted, and focused when `moveFocus` is true. */
  _setActive(item, moveFocus) {
    if (this._activeItem !== item) {
      this._clearActive()
      this._activeItem = item
      item.setAttribute("data-active", "true")
      this.emit("mj-menu-item-focus", { item: item })
    }

    if (moveFocus === true) {
      item.focus({ preventScroll: true })
      item.scrollIntoView({ block: "nearest" })
    }
    return
  }

  _clearActive() {
    if (this._activeItem !== null) {
      this._activeItem.removeAttribute("data-active")
      this._activeItem = null
    }
    return
  }

  _onKeydown(event) {
    if (event.altKey === true || event.ctrlKey === true || event.metaKey === true) {
      return
    }

    const items = this._getItems()
    const count = items.length
    const activeIndex = this._activeItem !== null ? items.indexOf(this._activeItem) : -1

    if (event.key === "Tab") {
      /* Focus goes back to the trigger; the default action then moves on from there. */
      this._requestClose("blur")
    } else if (count === 0) {
      /* Nothing to navigate. */
    } else if (event.key === "ArrowDown") {
      event.preventDefault()
      this._setActive(items[activeIndex < count - 1 ? activeIndex + 1 : 0], true)
    } else if (event.key === "ArrowUp") {
      event.preventDefault()
      this._setActive(items[activeIndex > 0 ? activeIndex - 1 : count - 1], true)
    } else if (event.key === "Home") {
      event.preventDefault()
      this._setActive(items[0], true)
    } else if (event.key === "End") {
      event.preventDefault()
      this._setActive(items[count - 1], true)
    } else if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      if (activeIndex !== -1) {
        /*
         * A real click: the author's own click handlers and a link item's
         * navigation run, and `_onClick` performs the selection.
         */
        items[activeIndex].click()
      }
    } else if (event.key.length === 1) {
      this._typeAhead(event.key)
    }
    return
  }

  _typeAhead(char) {
    const items = this._getItems()
    const lower = char.toLowerCase()
    const activeIndex = this._activeItem !== null ? items.indexOf(this._activeItem) : -1
    const startIndex = activeIndex + 1

    let matched = false
    for (let offset = 0; offset < items.length && matched === false; offset = offset + 1) {
      const index = (startIndex + offset) % items.length
      const label = items[index].textContent.trim().toLowerCase()
      if (label.startsWith(lower) === true) {
        this._setActive(items[index], true)
        matched = true
      }
    }
    return
  }

  _onClick(event) {
    const item = this._itemFromEvent(event)
    if (item !== null) {
      if (this._isDisabled(item) === true) {
        event.preventDefault()
      } else {
        this._activateItem(item)
      }
    }
    return
  }

  _onMouseOver(event) {
    const item = this._itemFromEvent(event)
    if (item !== null && this._isDisabled(item) === false && item !== this._activeItem) {
      /* Highlight follows the pointer; focus moves without scrolling the list. */
      this._setActive(item, false)
      item.focus({ preventScroll: true })
    }
    return
  }

  /* The radio items that share a group with `item` (a role="group" wrapper, or the menu). */
  _radioGroupOf(item) {
    const group = item.closest("[role='group']")
    const inOwnGroup = group !== null && this.contains(group) === true

    const radios = this._itemEls.filter((candidate) => {
      let sameGroup = false
      if (candidate.getAttribute("role") === "menuitemradio") {
        const candidateGroup = candidate.closest("[role='group']")
        if (inOwnGroup === true) {
          sameGroup = candidateGroup === group
        } else {
          sameGroup = candidateGroup === null || this.contains(candidateGroup) === false
        }
      }
      return sameGroup
    })
    return radios
  }

  /*
   * Choose `item`. The cancelable `mj-menu-select` fires first and reports
   * the checked state the item is about to get; only when it is not
   * canceled does a checkbox item toggle, a radio item check (unchecking
   * the other radios of its group) and the menu close.
   */
  _activateItem(item) {
    const role = item.getAttribute("role") || "menuitem"

    let checkedBool = null
    if (role === "menuitemcheckbox") {
      checkedBool = item.getAttribute("aria-checked") !== "true"
    } else if (role === "menuitemradio") {
      checkedBool = true
    } else {
      const checked = item.getAttribute("aria-checked")
      checkedBool = checked === "true" ? true : checked === "false" ? false : null
    }

    const value = item.getAttribute("value") || item.textContent.trim()

    const proceed = this.emit("mj-menu-select", {
      item: item,
      value: value,
      checked: checkedBool
    }, { cancelable: true })

    if (proceed === false) {
      return
    }

    if (role === "menuitemcheckbox") {
      item.setAttribute("aria-checked", checkedBool === true ? "true" : "false")
    } else if (role === "menuitemradio") {
      const radios = this._radioGroupOf(item)
      for (let index = 0; index < radios.length; index = index + 1) {
        if (radios[index] !== item) {
          radios[index].setAttribute("aria-checked", "false")
        }
      }
      item.setAttribute("aria-checked", "true")
    }

    const closeOnSelect = this.getAttribute("close-on-select") !== "false"
    if (closeOnSelect === true) {
      this._requestClose("select")
    }
    return
  }

  _onDocMousedown(event) {
    if (this._showing === false) {
      return
    }

    /* composedPath sees through the slot: light-DOM items are inside this host. */
    const path = event.composedPath()
    const inMenu = path.indexOf(this) !== -1
    const trigger = this._getTrigger()
    const inTrigger = trigger !== null && path.indexOf(trigger) !== -1

    if (inMenu === false && inTrigger === false) {
      this._requestClose("blur")
    }
    return
  }

  _onDocKeydown(event) {
    if (event.key === "Escape" && this._showing === true) {
      event.stopPropagation()
      this._requestClose("escape")
    }
    return
  }

  /* Open the menu (same as setting `open`). */
  show() {
    this.setAttribute("open", "")
    return
  }

  /* Close the menu, announcing `mj-menu-close` with reason "external". */
  hide() {
    this._requestClose("external")
    return
  }

  get items() {
    return this._getItems()
  }

  get activeItem() {
    return this._activeItem
  }

  get triggerElement() {
    let trigger = null
    if (this.isConnected === true) {
      trigger = this._getTrigger()
    }
    return trigger
  }

  set triggerElement(element) {
    this._triggerOverride = element instanceof Element ? element : null
    if (this._menu !== undefined && this._menu !== null) {
      this._syncLabel()
      if (this._showing === true) {
        this._startPositioning()
      }
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
}
