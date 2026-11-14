/*
 * mjcontextmenu.js
 *
 * <mj-context-menu> -- pointer- or keyboard-invoked actions menu. Opens on
 * right-click at the pointer or on the ContextMenu key / Shift+F10 next to
 * the target; supports groups, separators, checkbox and radio items, nested
 * submenus, icons, shortcut hints and type-ahead navigation.
 *
 * Items are supplied through the `items` property:
 *   { id, label, icon?, shortcut?, disabled?, type?, checked?, group?, submenu? }
 * where `type` is "item" (default), "checkbox", "radio", "separator" or
 * "group" (a heading), `group` names the radio group an item belongs to and
 * `submenu` is a nested array of items. Labels, icons and shortcuts are text.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";
import { deepActiveElement } from "../core/focustrap.js";
import { position, positionAtPoint, removeFromTopLayer } from "../core/overlay.js";

/* A submenu opens this long after the pointer comes to rest on its item. */
const SUBMENU_HOVER_DELAY_MS = 150;

/* Characters typed within this window extend the type-ahead search. */
const TYPE_AHEAD_RESET_MS = 600;

const STYLES = `
:host {
  display: contents;
}

.menu {
  position: fixed;
  z-index: var(--mj-context-menu-z-index, var(--mj-layer-popover));
  box-sizing: border-box;
  min-width: var(--mj-context-menu-width, 12rem);
  max-height: calc(100vh - var(--mj-space-2));
  overflow-y: auto;
  padding: var(--mj-context-menu-padding, var(--mj-space-1)) 0;
  background: var(--mj-context-menu-bg, var(--mj-surface));
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-context-menu-radius, var(--mj-radius-md));
  box-shadow: var(--mj-context-menu-shadow, var(--mj-elevation-3));
  color: var(--mj-text);
  list-style: none;
  margin: 0;
  outline: none;
}

:host([open]) .menu {
  animation: mj-context-menu-in var(--mj-motion-fast) var(--mj-motion-ease);
}

:host(:not([open])) .menu {
  pointer-events: none;
  visibility: hidden;
}

@keyframes mj-context-menu-in {
  from { opacity: 0; transform: scale(0.97); }
  to   { opacity: 1; transform: none; }
}

.menu-item {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  box-sizing: border-box;
  padding: 0 var(--mj-space-3);
  height: var(--mj-context-menu-item-height, 2.25rem);
  cursor: pointer;
  font-size: var(--mj-font-size-sm);
  user-select: none;
  outline: none;
  border: none;
  width: 100%;
  background: transparent;
  color: var(--mj-text);
  text-align: start;
  white-space: nowrap;
}

.menu-item:hover,
.menu-item:focus,
.menu-item[aria-expanded="true"] {
  background: var(--mj-bg-muted);
}

.menu-item:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: -2px;
}

.menu-item[aria-disabled="true"] {
  opacity: 0.45;
  cursor: not-allowed;
}

.menu-item .check-icon {
  width: 1rem;
  text-align: center;
  flex-shrink: 0;
  font-size: 0.75rem;
}

.menu-item .item-icon {
  width: 1.25rem;
  text-align: center;
  flex-shrink: 0;
}

.menu-item .item-label { flex: 1; }

.menu-item .item-shortcut {
  color: var(--mj-text-muted);
  font-size: var(--mj-font-size-xs);
  margin-inline-start: var(--mj-space-4);
}

.menu-item .submenu-arrow {
  font-size: 0.65rem;
  color: var(--mj-text-muted);
}

:host(:dir(rtl)) .menu-item .submenu-arrow { transform: scaleX(-1); }

.separator {
  height: 1px;
  background: var(--mj-border);
  margin: var(--mj-space-1) 0;
}

.group-label {
  padding: var(--mj-space-2) var(--mj-space-3) var(--mj-space-1);
  font-size: var(--mj-font-size-xs);
  font-weight: var(--mj-font-weight-bold);
  color: var(--mj-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

@media (prefers-reduced-motion: reduce) {
  :host([open]) .menu { animation: none; }
}
`;

export class MjContextMenu extends MjElement {
  static tagName = "mj-context-menu";
  static styles = STYLES;
  static watched = ["open", "variant", "target-id", "label"];

  constructor() {
    super()
    this._menuEl = null
    this._targetEl = null
    this._lastFocused = null
    this._menuId = nextId("mj-ctxmenu")
    this._items = []

    /* True from a successful open until the close has completed. */
    this._isOpen = false

    /*
     * Open menu levels, outermost first: { listEl, parentItem, itemEls }.
     * Level 0 is the main menu; deeper levels are open submenus.
     */
    this._levels = []

    this._submenuTimer = null
    this._typeAheadText = ""
    this._typeAheadTimer = null
    this._dismissInstalled = false

    this.openCoords = null

    /* One bound function per listener, so each can be removed exactly. */
    this._onContextMenu = this._handleContextMenu.bind(this)
    this._onTargetKeydown = this._handleTargetKeydown.bind(this)
    this._onOutsidePointer = this._handleOutsidePointer.bind(this)
    this._onViewportChange = this._handleViewportChange.bind(this)
    this._onWindowBlur = this._handleWindowBlur.bind(this)
  }

  render() {
    const markup = html`
      <slot></slot>
      <ul class="menu" part="menu" role="menu" id="${this._menuId}" tabindex="-1"></ul>
    `
    return markup
  }

  afterRender() {
    this._menuEl = this.$(".menu")
    this._applyLabel()

    this.listen(this.shadowRoot, "keydown", this._onMenuKeydown.bind(this))
    this.listen(this.shadowRoot, "click", this._onMenuClick.bind(this))
    this.listen(this.shadowRoot, "pointerover", this._onMenuPointerOver.bind(this))

    /* A target slotted after the element connected is wired when it arrives. */
    this.listen(this.$("slot:not([name])"), "slotchange", this._resolveTarget.bind(this))
    this.onTeardown(this._detachTarget.bind(this))

    this._resolveTarget()

    if (this.hasAttribute("open") === true) {
      this._openMenu(null, "api")
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._menuEl === undefined || this._menuEl === null) {
      return
    }

    if (name === "open") {
      /* _openMenu sets the attribute itself after marking the menu open. */
      if (newValue !== null && this._isOpen === false) {
        this._openMenu(this.openCoords, "api")
      } else if (newValue === null && this._isOpen === true) {
        this._closeMenu("api")
      }
    } else if (name === "target-id") {
      this._resolveTarget()
    } else if (name === "label") {
      this._applyLabel()
    } else if (name === "variant") {
      if (this._isOpen === true) {
        this._renderMenu()
      }
    }
    return
  }

  onDisconnected() {
    /* Removed while open: release everything without events or refocus. */
    if (this._isOpen === true) {
      this._isOpen = false
      this._closeSubmenus(0)
      this._removeDismissListeners()
      removeFromTopLayer(this._menuEl)
    }
    return
  }

  _applyLabel() {
    this._menuEl.setAttribute("aria-label", this.getAttribute("label") || t("mj.contextMenu.label"))
    return
  }

  /* ----- target wiring ----- */

  _resolveTarget() {
    const targetId = this.getAttribute("target-id")
    let el = null

    if (targetId !== null && targetId.length > 0) {
      el = document.getElementById(targetId)
      if (el === null) {
        console.error(`<mj-context-menu>: target-id "${targetId}" not found`)
      }
    } else {
      const slot = this.shadowRoot.querySelector("slot:not([name])")
      if (slot !== null) {
        const assigned = slot.assignedElements()
        el = assigned.length > 0 ? assigned[0] : null
      }
    }

    if (el === this._targetEl) {
      return
    }

    this._detachTarget()
    this._targetEl = el

    if (el !== null) {
      el.addEventListener("contextmenu", this._onContextMenu)
      el.addEventListener("keydown", this._onTargetKeydown)
    }
    return
  }

  _detachTarget() {
    if (this._targetEl !== null) {
      this._targetEl.removeEventListener("contextmenu", this._onContextMenu)
      this._targetEl.removeEventListener("keydown", this._onTargetKeydown)
      this._targetEl = null
    }
    return
  }

  _handleContextMenu(event) {
    /*
     * A component inside the target that has a menu of its own already
     * handled this right-click (and called preventDefault): one menu only.
     */
    if (event.defaultPrevented === true) {
      return
    }
    event.preventDefault()
    this._openMenu({ x: event.clientX, y: event.clientY }, "pointer")
    return
  }

  _handleTargetKeydown(event) {
    const isContextKey = event.key === "ContextMenu" || (event.key === "F10" && event.shiftKey === true)
    if (isContextKey === false || event.defaultPrevented === true) {
      return
    }
    event.preventDefault()
    this._openMenu(null, "keyboard")
    return
  }

  /* ----- open / close ----- */

  /*
   * The one way the menu opens -- pointer, keyboard, show() and the `open`
   * attribute all come here. `coords` is a viewport point, or null to open
   * next to the target. Records the element to refocus, positions the menu
   * synchronously, installs light dismiss and moves focus inside.
   */
  _openMenu(coords, reason) {
    if (this._menuEl === null || this.isConnected === false) {
      return false
    }

    const point = coords !== null && coords !== undefined ? coords : null
    const proceed = this.emit(
      "mj-context-menu-before-open",
      { x: point !== null ? point.x : 0, y: point !== null ? point.y : 0, reason: reason },
      { cancelable: true }
    )
    if (proceed === false) {
      if (this._isOpen === false && this.hasAttribute("open") === true) {
        this.removeAttribute("open")
      }
      return false
    }

    const wasOpen = this._isOpen
    if (wasOpen === false) {
      this._lastFocused = deepActiveElement()
    }

    this._isOpen = true
    this.openCoords = point
    if (this.hasAttribute("open") === false) {
      this.setAttribute("open", "")
    }

    this._renderMenu()
    this._placeMenu(point)
    this._installDismissListeners()
    this._focusFirstItem(0)

    this.emit("mj-context-menu-open", {
      x: point !== null ? point.x : 0,
      y: point !== null ? point.y : 0,
      targetEl: this._targetEl
    })
    return true
  }

  _placeMenu(point) {
    if (point !== null) {
      positionAtPoint(this._menuEl, point.x, point.y, { padding: 4, constrain: true })
    } else {
      const anchor = this._targetEl !== null ? this._targetEl : this
      position(this._menuEl, anchor, { placement: "bottom-start", offset: 4, constrain: true })
    }
    return
  }

  _closeMenu(reason) {
    if (this._isOpen === false) {
      return
    }
    this._isOpen = false

    /* Decide about focus before the menu is hidden and focus is lost. */
    const active = deepActiveElement()
    const focusInMenu = active === null || active === document.body ||
      this.shadowRoot.contains(active) === true

    this._closeSubmenus(0)
    this._removeDismissListeners()
    this._clearTypeAhead()
    removeFromTopLayer(this._menuEl)

    if (this.hasAttribute("open") === true) {
      this.removeAttribute("open")
    }

    const restoreEl = this._lastFocused
    this._lastFocused = null
    if (focusInMenu === true && restoreEl !== null && restoreEl.isConnected === true &&
        typeof restoreEl.focus === "function") {
      restoreEl.focus()
    }

    this.emit("mj-context-menu-close", { reason: reason })
    return
  }

  /* ----- light dismiss ----- */

  _installDismissListeners() {
    if (this._dismissInstalled === true) {
      return
    }
    this._dismissInstalled = true
    window.addEventListener("pointerdown", this._onOutsidePointer, true)
    window.addEventListener("scroll", this._onViewportChange, true)
    window.addEventListener("resize", this._onViewportChange)
    window.addEventListener("blur", this._onWindowBlur)
    return
  }

  _removeDismissListeners() {
    if (this._dismissInstalled === false) {
      return
    }
    this._dismissInstalled = false
    window.removeEventListener("pointerdown", this._onOutsidePointer, true)
    window.removeEventListener("scroll", this._onViewportChange, true)
    window.removeEventListener("resize", this._onViewportChange)
    window.removeEventListener("blur", this._onWindowBlur)
    return
  }

  /*
   * Inside means inside one of the menu panels. composedPath is used
   * because a window listener sees a target retargeted to the outermost
   * shadow host; the wrapped target region counts as outside, so a click
   * next to the menu closes it as a native menu would.
   */
  _handleOutsidePointer(event) {
    const path = event.composedPath()
    const inside = this._levels.some((level) => path.includes(level.listEl) === true)
    if (inside === false) {
      this._closeMenu("light-dismiss")
    }
    return
  }

  _handleViewportChange(event) {
    /* Scrolling inside a long menu is not a reason to close it. */
    if (event.type === "scroll") {
      const path = event.composedPath()
      const inside = this._levels.some((level) => path.includes(level.listEl) === true)
      if (inside === true) {
        return
      }
    }
    this._closeMenu("light-dismiss")
    return
  }

  _handleWindowBlur() {
    this._closeMenu("light-dismiss")
    return
  }

  /* ----- rendering ----- */

  _defaultType() {
    const variant = this.getAttribute("variant") || "menu"
    let type = "item"
    if (variant === "checkbox-group") {
      type = "checkbox"
    } else if (variant === "radio-group") {
      type = "radio"
    }
    return type
  }

  _typeOf(descriptor) {
    const type = typeof descriptor.type === "string" && descriptor.type.length > 0
      ? descriptor.type
      : this._defaultType()
    return type
  }

  _renderMenu() {
    if (this._menuEl === null) {
      return
    }
    this._closeSubmenus(0)
    const itemEls = this._fillList(this._menuEl, this._items)
    this._levels = [{ listEl: this._menuEl, parentItem: null, itemEls: itemEls }]
    return
  }

  /* Build the entries of one menu level. Returns its focusable item elements. */
  _fillList(listEl, descriptors) {
    listEl.textContent = ""
    const itemEls = []
    const list = Array.isArray(descriptors) ? descriptors : []

    for (let index = 0; index < list.length; index = index + 1) {
      const descriptor = list[index]
      if (descriptor === null || typeof descriptor !== "object") {
        continue
      }
      const el = this._buildItem(descriptor, index)
      listEl.appendChild(el)
      if (el.classList.contains("menu-item") === true) {
        itemEls.push(el)
      }
    }
    return itemEls
  }

  _buildItem(descriptor, index) {
    const type = this._typeOf(descriptor)

    if (type === "separator") {
      const li = document.createElement("li")
      li.className = "separator"
      li.setAttribute("role", "separator")
      li.setAttribute("part", "separator")
      return li
    }

    if (type === "group") {
      const li = document.createElement("li")
      li.className = "group-label"
      li.setAttribute("role", "presentation")
      li.setAttribute("part", "group-label")
      li.textContent = this._text(descriptor.label)
      return li
    }

    let role = "menuitem"
    if (type === "checkbox") {
      role = "menuitemcheckbox"
    } else if (type === "radio") {
      role = "menuitemradio"
    }

    const li = document.createElement("li")
    li.className = "menu-item"
    li.setAttribute("role", role)
    li.setAttribute("part", "item")
    li.setAttribute("data-item-id", descriptor.id !== undefined && descriptor.id !== null ? String(descriptor.id) : String(index))
    li.setAttribute("data-item-index", String(index))
    li.setAttribute("tabindex", "-1")
    li._mjDescriptor = descriptor

    if (descriptor.disabled === true) {
      li.setAttribute("aria-disabled", "true")
    }

    const checkIcon = document.createElement("span")
    checkIcon.className = "check-icon"
    checkIcon.setAttribute("aria-hidden", "true")
    li.appendChild(checkIcon)

    if (descriptor.icon !== undefined && descriptor.icon !== null && String(descriptor.icon).length > 0) {
      const icon = document.createElement("span")
      icon.className = "item-icon"
      icon.setAttribute("part", "item-icon")
      icon.setAttribute("aria-hidden", "true")
      icon.textContent = String(descriptor.icon)
      li.appendChild(icon)
    }

    const label = document.createElement("span")
    label.className = "item-label"
    label.textContent = this._text(descriptor.label)
    li.appendChild(label)

    if (descriptor.shortcut !== undefined && descriptor.shortcut !== null && String(descriptor.shortcut).length > 0) {
      const shortcut = document.createElement("span")
      shortcut.className = "item-shortcut"
      shortcut.setAttribute("part", "item-shortcut")
      shortcut.textContent = String(descriptor.shortcut)
      li.setAttribute("aria-keyshortcuts", String(descriptor.shortcut))
      li.appendChild(shortcut)
    }

    if (this._hasSubmenu(descriptor) === true) {
      li.setAttribute("aria-haspopup", "menu")
      li.setAttribute("aria-expanded", "false")
      const arrow = document.createElement("span")
      arrow.className = "submenu-arrow"
      arrow.setAttribute("part", "submenu-arrow")
      arrow.setAttribute("aria-hidden", "true")
      arrow.textContent = "❯"
      li.appendChild(arrow)
    }

    this._applyChecked(li)
    return li
  }

  _text(value) {
    const text = value !== undefined && value !== null ? String(value) : ""
    return text
  }

  _hasSubmenu(descriptor) {
    const has = Array.isArray(descriptor.submenu) === true && descriptor.submenu.length > 0
    return has
  }

  _applyChecked(li) {
    const descriptor = li._mjDescriptor
    const type = this._typeOf(descriptor)
    const checkIcon = li.querySelector(".check-icon")

    if (type === "checkbox" || type === "radio") {
      const checked = descriptor.checked === true
      li.setAttribute("aria-checked", checked === true ? "true" : "false")
      let mark = ""
      if (checked === true) {
        mark = type === "radio" ? "●" : "✓"
      }
      checkIcon.textContent = mark
    }
    return
  }

  /* ----- submenus ----- */

  _levelOf(element) {
    let found = -1
    for (let index = 0; index < this._levels.length; index = index + 1) {
      if (this._levels[index].listEl.contains(element) === true) {
        found = index
      }
    }
    return found
  }

  /* Close every submenu deeper than `level` (0 closes all of them). */
  _closeSubmenus(level) {
    this._clearSubmenuTimer()
    while (this._levels.length > level + 1) {
      const closing = this._levels.pop()
      removeFromTopLayer(closing.listEl)
      closing.listEl.remove()
      if (closing.parentItem !== null) {
        closing.parentItem.setAttribute("aria-expanded", "false")
      }
    }
    return
  }

  _openSubmenu(itemEl, focusFirst) {
    const descriptor = itemEl._mjDescriptor
    if (this._hasSubmenu(descriptor) === false || itemEl.getAttribute("aria-disabled") === "true") {
      return
    }

    const level = this._levelOf(itemEl)
    const alreadyOpen = this._levels.length > level + 1 && this._levels[level + 1].parentItem === itemEl
    if (alreadyOpen === false) {
      this._closeSubmenus(level)

      const listEl = document.createElement("ul")
      listEl.className = "menu submenu"
      listEl.setAttribute("part", "menu submenu")
      listEl.setAttribute("role", "menu")
      listEl.setAttribute("tabindex", "-1")
      listEl.setAttribute("aria-label", this._text(descriptor.label))
      this.shadowRoot.appendChild(listEl)

      const itemEls = this._fillList(listEl, descriptor.submenu)
      this._levels.push({ listEl: listEl, parentItem: itemEl, itemEls: itemEls })
      itemEl.setAttribute("aria-expanded", "true")

      /* Beside its item, flipping to the other side when it does not fit. */
      position(listEl, itemEl, { placement: "end-top", offset: 0, constrain: false })
    }

    if (focusFirst === true) {
      this._focusFirstItem(level + 1)
    }
    return
  }

  _clearSubmenuTimer() {
    if (this._submenuTimer !== null) {
      window.clearTimeout(this._submenuTimer)
      this._submenuTimer = null
    }
    return
  }

  /* ----- focus ----- */

  _enabledItems(level) {
    const entry = this._levels[level]
    const items = entry !== undefined
      ? entry.itemEls.filter((el) => el.getAttribute("aria-disabled") !== "true")
      : []
    return items
  }

  _focusFirstItem(level) {
    const entry = this._levels[level]
    if (entry === undefined) {
      return
    }
    const enabled = this._enabledItems(level)
    if (enabled.length > 0) {
      enabled[0].focus()
    } else if (entry.itemEls.length > 0) {
      entry.itemEls[0].focus()
    } else {
      entry.listEl.focus()
    }
    return
  }

  _clearTypeAhead() {
    if (this._typeAheadTimer !== null) {
      window.clearTimeout(this._typeAheadTimer)
      this._typeAheadTimer = null
    }
    this._typeAheadText = ""
    return
  }

  _typeAhead(character, level, currentIdx) {
    if (this._typeAheadTimer !== null) {
      window.clearTimeout(this._typeAheadTimer)
    }
    this._typeAheadText = this._typeAheadText + character.toLowerCase()
    this._typeAheadTimer = window.setTimeout(() => {
      this._typeAheadText = ""
      this._typeAheadTimer = null
    }, TYPE_AHEAD_RESET_MS)

    const items = this._enabledItems(level)
    const count = items.length
    /* A repeated single letter cycles through the items starting with it. */
    const start = this._typeAheadText.length === 1 ? currentIdx + 1 : Math.max(currentIdx, 0)

    for (let step = 0; step < count; step = step + 1) {
      const candidate = items[(start + step + count) % count]
      const label = candidate.querySelector(".item-label")
      if (label !== null && label.textContent.trim().toLowerCase().startsWith(this._typeAheadText) === true) {
        candidate.focus()
        break
      }
    }
    return
  }

  /* ----- events ----- */

  _onMenuKeydown(event) {
    if (this._isOpen === false) {
      return
    }

    const level = this._levelOf(event.target)
    if (level < 0) {
      return
    }

    const items = this._enabledItems(level)
    const count = items.length
    const targetItem = event.target.closest(".menu-item")
    const focused = targetItem !== null ? targetItem : this.shadowRoot.activeElement
    let currentIdx = items.indexOf(focused)

    const rtl = window.getComputedStyle(this._menuEl).direction === "rtl"
    const openKey = rtl === true ? "ArrowLeft" : "ArrowRight"
    const closeKey = rtl === true ? "ArrowRight" : "ArrowLeft"

    if (event.key === "Escape") {
      /* Handled here: a dialog around the menu must not close as well. */
      event.preventDefault()
      event.stopPropagation()
      if (level > 0) {
        const parentItem = this._levels[level].parentItem
        this._closeSubmenus(level - 1)
        parentItem.focus()
      } else {
        this._closeMenu("escape")
      }
      return
    }

    if (event.key === "Tab") {
      this._closeMenu("escape")
      return
    }

    if (event.key === closeKey && level > 0) {
      event.preventDefault()
      const parentItem = this._levels[level].parentItem
      this._closeSubmenus(level - 1)
      parentItem.focus()
      return
    }

    if (event.key === openKey) {
      event.preventDefault()
      if (focused !== null && items.includes(focused) === true && this._hasSubmenu(focused._mjDescriptor) === true) {
        this._openSubmenu(focused, true)
      }
      return
    }

    if (count === 0) {
      return
    }
    if (currentIdx < 0) {
      currentIdx = -1
    }

    if (event.key === "ArrowDown") {
      event.preventDefault()
      items[(currentIdx + 1) % count].focus()
      return
    }

    if (event.key === "ArrowUp") {
      event.preventDefault()
      const prev = currentIdx < 0 ? count - 1 : (currentIdx - 1 + count) % count
      items[prev].focus()
      return
    }

    if (event.key === "Home") {
      event.preventDefault()
      items[0].focus()
      return
    }

    if (event.key === "End") {
      event.preventDefault()
      items[count - 1].focus()
      return
    }

    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      if (focused !== null && items.includes(focused) === true) {
        this._activateItem(focused, true)
      }
      return
    }

    if (event.key.length === 1 && event.ctrlKey === false && event.metaKey === false && event.altKey === false) {
      event.preventDefault()
      this._typeAhead(event.key, level, currentIdx)
    }
    return
  }

  _onMenuClick(event) {
    const itemEl = event.target.closest(".menu-item")
    if (itemEl === null || this._levelOf(itemEl) < 0) {
      return
    }
    if (itemEl.getAttribute("aria-disabled") === "true") {
      return
    }
    this._activateItem(itemEl, false)
    return
  }

  /* The item under the pointer takes focus; a submenu item opens after a pause. */
  _onMenuPointerOver(event) {
    const itemEl = event.target.closest(".menu-item")
    if (itemEl === null || this._isOpen === false) {
      return
    }
    const level = this._levelOf(itemEl)
    if (level < 0) {
      return
    }

    if (this.shadowRoot.activeElement !== itemEl) {
      itemEl.focus({ preventScroll: true })
    }

    this._clearSubmenuTimer()
    this._submenuTimer = window.setTimeout(() => {
      this._submenuTimer = null
      if (this._hasSubmenu(itemEl._mjDescriptor) === true) {
        this._openSubmenu(itemEl, false)
      } else {
        this._closeSubmenus(level)
      }
    }, SUBMENU_HOVER_DELAY_MS)
    return
  }

  _activateItem(itemEl, fromKeyboard) {
    const descriptor = itemEl._mjDescriptor
    if (descriptor === undefined || itemEl.getAttribute("aria-disabled") === "true") {
      return
    }

    if (this._hasSubmenu(descriptor) === true) {
      this._openSubmenu(itemEl, fromKeyboard)
      return
    }

    const type = this._typeOf(descriptor)

    if (type === "checkbox") {
      descriptor.checked = descriptor.checked !== true
      this._applyChecked(itemEl)
      this.emit("mj-context-menu-select", { item: descriptor, checked: descriptor.checked })
      return
    }

    if (type === "radio") {
      /* One checked item per radio group within the same menu level. */
      const level = this._levels[this._levelOf(itemEl)]
      const groupName = descriptor.group !== undefined ? String(descriptor.group) : ""
      for (const other of level.itemEls) {
        const otherDescriptor = other._mjDescriptor
        const otherGroup = otherDescriptor.group !== undefined ? String(otherDescriptor.group) : ""
        if (this._typeOf(otherDescriptor) === "radio" && otherGroup === groupName) {
          otherDescriptor.checked = other === itemEl
          this._applyChecked(other)
        }
      }
      this.emit("mj-context-menu-select", { item: descriptor, checked: true })
      return
    }

    this.emit("mj-context-menu-select", { item: descriptor })
    this._closeMenu("item-select")
    return
  }

  /* Scriptable API */

  /*
   * The menu items. An accessor (not a plain field) so that a value
   * assigned before the element was upgraded is picked up, and so that a
   * menu that is open shows the new items at once.
   */
  get items() {
    return this._items
  }

  set items(value) {
    this._items = Array.isArray(value) ? value : []
    if (this._isOpen === true) {
      this._renderMenu()
      this._placeMenu(this.openCoords)
      this._focusFirstItem(0)
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

  get targetEl() {
    return this._targetEl
  }

  /* Open at the viewport point (x, y), or next to the target without one. */
  show(x, y) {
    const hasPoint = typeof x === "number" && typeof y === "number"
    this._openMenu(hasPoint === true ? { x: x, y: y } : null, "api")
    return
  }

  close() {
    this._closeMenu("api")
    return
  }
}
