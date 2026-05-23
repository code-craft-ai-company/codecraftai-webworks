/*
 * mjcontextmenu.js
 *
 * <mj-context-menu> -- pointer- or keyboard-invoked actions menu. Opens on
 * right-click or ContextMenu key at cursor position; supports grouped items,
 * separators, checkbox/radio items, and type-ahead navigation.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { position } from "../core/overlay.js";

const STYLES = `
:host {
  display: contents;
}

.menu {
  position: fixed;
  z-index: var(--mj-layer-popover);
  min-width: var(--mj-context-menu-width, 12rem);
  padding: var(--mj-context-menu-padding, var(--mj-space-1)) 0;
  background: var(--mj-surface);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-context-menu-radius, var(--mj-radius-md));
  box-shadow: var(--mj-context-menu-shadow, var(--mj-elevation-3));
  color: var(--mj-text);
  list-style: none;
  margin: 0;
  outline: none;
  opacity: 0;
  transform: scale(0.97);
  transition: opacity var(--mj-motion-fast) var(--mj-motion-ease),
              transform var(--mj-motion-fast) var(--mj-motion-ease);
}

:host([open]) .menu {
  opacity: 1;
  transform: scale(1);
}

:host(:not([open])) .menu {
  pointer-events: none;
  visibility: hidden;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
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
.menu-item[data-active="true"] {
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

.menu-item .item-label { flex: 1; }

.menu-item .submenu-arrow {
  font-size: 0.65rem;
  color: var(--mj-text-muted);
}

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
  .menu { transition: none; }
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
    this._activeIndex = -1
    this._menuItems = []
    this._menuId = nextId("mj-ctxmenu")
    this.items = []
    this.openCoords = null
  }

  render() {
    const label = this.getAttribute("label") || "Actions"
    const markup = `
      <slot></slot>
      <ul class="menu" part="menu" role="menu" id="${this._menuId}" aria-label="${label}" tabindex="-1"></ul>
    `
    return markup
  }

  afterRender() {
    this._menuEl = this.$(".menu")
    this._resolveTarget()
    this.listen(this._menuEl, "keydown", this._onMenuKeydown.bind(this))
    this.listen(this._menuEl, "click", this._onMenuClick.bind(this))

    if (this.hasAttribute("open") === true) {
      this._renderMenu()
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "open" && this._menuEl !== null) {
      if (newValue !== null) {
        this._renderMenu()
        this._focusFirstItem()
      } else {
        this._activeIndex = -1
      }
    }
    if (name === "target-id") {
      this._resolveTarget()
    }
    return
  }

  onDisconnected() {
    if (this._lightDismissHandler !== undefined) {
      window.removeEventListener("pointerdown", this._lightDismissHandler, true)
    }
    return
  }

  _resolveTarget() {
    if (this._targetEl !== null) {
      this._targetEl.removeEventListener("contextmenu", this._onContextMenu)
      this._targetEl.removeEventListener("keydown", this._onTargetKeydown)
    }

    const targetId = this.getAttribute("target-id")
    let el = null

    if (targetId !== null && targetId.length > 0) {
      el = document.getElementById(targetId)
      if (el === null) {
        console.error(`<mj-context-menu>: target-id "${targetId}" not found`)
        return
      }
    } else {
      const slot = this.shadowRoot.querySelector("slot:not([name])")
      if (slot !== null) {
        const assigned = slot.assignedElements()
        el = assigned.length > 0 ? assigned[0] : null
      }
    }

    this._targetEl = el

    if (el !== null) {
      this._onContextMenu = this._handleContextMenu.bind(this)
      this._onTargetKeydown = this._handleTargetKeydown.bind(this)
      el.addEventListener("contextmenu", this._onContextMenu)
      el.addEventListener("keydown", this._onTargetKeydown)
    }
    return
  }

  _handleContextMenu(event) {
    event.preventDefault()
    const x = event.clientX
    const y = event.clientY

    const proceed = this.emit(
      "mj-context-menu-before-open",
      { x: x, y: y },
      { cancelable: true }
    )
    if (proceed === false) {
      return
    }

    this._lastFocused = document.activeElement
    this.openCoords = { x: x, y: y }
    this._positionAtCoords(x, y)
    this.setAttribute("open", "")
    this._installLightDismiss()
    this.emit("mj-context-menu-open", { x: x, y: y, targetEl: this._targetEl })
    return
  }

  _handleTargetKeydown(event) {
    const isContextKey = event.key === "ContextMenu" || (event.key === "F10" && event.shiftKey)
    if (isContextKey === false) {
      return
    }
    event.preventDefault()

    const proceed = this.emit(
      "mj-context-menu-before-open",
      { x: 0, y: 0 },
      { cancelable: true }
    )
    if (proceed === false) {
      return
    }

    this._lastFocused = document.activeElement
    this.openCoords = null

    const rect = this._targetEl !== null ? this._targetEl.getBoundingClientRect() : null
    if (rect !== null) {
      this._positionAtCoords(rect.left, rect.bottom + 4)
    }

    this.setAttribute("open", "")
    this._installLightDismiss()
    this.emit("mj-context-menu-open", { x: 0, y: 0, targetEl: this._targetEl })
    return
  }

  _positionAtCoords(x, y) {
    if (this._menuEl === null) {
      return
    }

    this._menuEl.style.position = "fixed"
    this._menuEl.style.left = `${x}px`
    this._menuEl.style.top = `${y}px`
    this._menuEl.style.zIndex = "var(--mj-layer-popover)"

    requestAnimationFrame(() => {
      if (this._menuEl === null) {
        return
      }
      const rect = this._menuEl.getBoundingClientRect()
      const vw = window.innerWidth
      const vh = window.innerHeight

      let adjustedX = x
      let adjustedY = y

      if (x + rect.width > vw) {
        adjustedX = Math.max(0, x - rect.width)
      }
      if (y + rect.height > vh) {
        adjustedY = Math.max(0, y - rect.height)
      }

      this._menuEl.style.left = `${adjustedX}px`
      this._menuEl.style.top = `${adjustedY}px`
    })
    return
  }

  _renderMenu() {
    if (this._menuEl === null) {
      return
    }
    this._menuEl.innerHTML = ""
    this._menuItems = []

    for (let index = 0; index < this.items.length; index = index + 1) {
      const descriptor = this.items[index]
      const el = this._buildItem(descriptor, index)
      this._menuEl.appendChild(el)
      if (descriptor.type !== "separator" && descriptor.type !== "group") {
        this._menuItems.push(el)
      }
    }
    return
  }

  _buildItem(descriptor, index) {
    if (descriptor.type === "separator") {
      const li = document.createElement("li")
      li.className = "separator"
      li.setAttribute("role", "separator")
      li.setAttribute("part", "separator")
      return li
    }

    if (descriptor.type === "group") {
      const li = document.createElement("li")
      li.className = "group-label"
      li.setAttribute("role", "presentation")
      li.setAttribute("part", "group-label")
      li.textContent = descriptor.label || ""
      return li
    }

    const li = document.createElement("li")
    li.setAttribute("role", descriptor.type === "checkbox" ? "menuitemcheckbox" : "menuitem")
    li.setAttribute("part", "item")
    li.setAttribute("data-item-id", descriptor.id || String(index))
    li.setAttribute("data-item-index", String(index))
    li.setAttribute("tabindex", "-1")
    li.className = "menu-item"

    if (descriptor.disabled === true) {
      li.setAttribute("aria-disabled", "true")
    }

    if (descriptor.type === "checkbox") {
      li.setAttribute("aria-checked", descriptor.checked === true ? "true" : "false")
    }

    if (descriptor.submenu !== undefined) {
      li.setAttribute("aria-haspopup", "menu")
      li.setAttribute("aria-expanded", "false")
    }

    const checkIcon = descriptor.type === "checkbox"
      ? `<span class="check-icon" aria-hidden="true">${descriptor.checked === true ? "&#x2713;" : ""}</span>`
      : `<span class="check-icon" aria-hidden="true"></span>`

    const submenuArrow = descriptor.submenu !== undefined
      ? `<span class="submenu-arrow" part="submenu-arrow" aria-hidden="true">&#x276f;</span>`
      : ""

    li.innerHTML = `
      ${checkIcon}
      <span class="item-label">${descriptor.label || ""}</span>
      ${submenuArrow}
    `

    return li
  }

  _focusFirstItem() {
    const first = this._menuItems.find((el) => el.getAttribute("aria-disabled") !== "true")
    if (first !== undefined) {
      first.focus()
      this._activeIndex = this._menuItems.indexOf(first)
    } else if (this._menuItems.length > 0) {
      this._menuItems[0].focus()
      this._activeIndex = 0
    }
    return
  }

  _installLightDismiss() {
    if (this._lightDismissHandler !== undefined) {
      return
    }
    this._lightDismissHandler = (event) => {
      const inside = this.contains(event.target) || this.shadowRoot.contains(event.target)
      if (inside === false) {
        this._closeMenu("light-dismiss")
      }
    }
    window.addEventListener("pointerdown", this._lightDismissHandler, true)
    return
  }

  _closeMenu(reason) {
    this.removeAttribute("open")

    if (this._lightDismissHandler !== undefined) {
      window.removeEventListener("pointerdown", this._lightDismissHandler, true)
      this._lightDismissHandler = undefined
    }

    const restoreEl = this._lastFocused
    this._lastFocused = null
    if (restoreEl !== null && typeof restoreEl.focus === "function") {
      restoreEl.focus()
    }

    this.emit("mj-context-menu-close", { reason: reason })
    return
  }

  _onMenuKeydown(event) {
    const items = this._menuItems.filter((el) => el.getAttribute("aria-disabled") !== "true")
    const count = items.length

    if (count === 0) {
      if (event.key === "Escape") {
        this._closeMenu("escape")
      }
      return
    }

    let currentIdx = items.findIndex((el) => el === document.activeElement || el === this.shadowRoot.activeElement)
    if (currentIdx < 0) {
      currentIdx = 0
    }

    if (event.key === "ArrowDown") {
      event.preventDefault()
      const next = (currentIdx + 1) % count
      items[next].focus()
      return
    }

    if (event.key === "ArrowUp") {
      event.preventDefault()
      const prev = (currentIdx - 1 + count) % count
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

    if (event.key === "Escape" || event.key === "Tab") {
      this._closeMenu("escape")
      return
    }

    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      const focused = this._menuItems.find(
        (el) => el === document.activeElement || el === this.shadowRoot.activeElement
      )
      if (focused !== undefined) {
        this._activateItem(focused)
      }
      return
    }

    /* Type-ahead */
    if (event.key.length === 1) {
      const char = event.key.toLowerCase()
      const startIdx = (currentIdx + 1) % count
      let found = null

      for (let i = 0; i < count; i = i + 1) {
        const checkIdx = (startIdx + i) % count
        const label = items[checkIdx].querySelector(".item-label")
        if (label !== null && label.textContent.trim().toLowerCase().startsWith(char) === true) {
          found = items[checkIdx]
          break
        }
      }

      if (found !== null) {
        found.focus()
      }
      return
    }
    return
  }

  _onMenuClick(event) {
    const itemEl = event.target.closest(".menu-item")
    if (itemEl === null) {
      return
    }
    if (itemEl.getAttribute("aria-disabled") === "true") {
      return
    }
    this._activateItem(itemEl)
    return
  }

  _activateItem(itemEl) {
    const idx = parseInt(itemEl.getAttribute("data-item-index") || "0", 10)
    const descriptor = this.items[idx]
    if (descriptor === undefined) {
      return
    }

    if (descriptor.type === "checkbox") {
      const checked = itemEl.getAttribute("aria-checked") === "true"
      descriptor.checked = !checked
      itemEl.setAttribute("aria-checked", descriptor.checked === true ? "true" : "false")
      const checkIcon = itemEl.querySelector(".check-icon")
      if (checkIcon !== null) {
        checkIcon.innerHTML = descriptor.checked === true ? "&#x2713;" : ""
      }
      this.emit("mj-context-menu-select", { item: descriptor, checked: descriptor.checked })
      return
    }

    this.emit("mj-context-menu-select", { item: descriptor })

    if (descriptor.submenu === undefined) {
      this._closeMenu("item-select")
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

  get targetEl() {
    return this._targetEl
  }

  show(x, y) {
    if (x !== undefined && y !== undefined) {
      this.openCoords = { x: x, y: y }
      this._positionAtCoords(x, y)
    }
    this._renderMenu()
    this.setAttribute("open", "")
    this._installLightDismiss()
    this._focusFirstItem()
    return
  }

  close() {
    this._closeMenu("api")
    return
  }
}
