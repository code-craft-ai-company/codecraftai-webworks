/*
 * mjmenubar.js
 *
 * <mj-menubar> -- application-level menubar implementing WAI-ARIA APG Menubar
 * pattern. Roving tabindex across top-level items, dropdown menus on activation,
 * hover-to-switch when any menu is open.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { RovingTabindex } from "../core/focustrap.js";

const STYLES = `
:host {
  display: block;
}

.menubar-root {
  display: flex;
  align-items: center;
  gap: 0;
  min-height: var(--mj-menubar-height, var(--mj-control-height-md));
  padding: 0 var(--mj-space-2);
  background: var(--mj-menubar-bg, var(--mj-surface));
  border-bottom: 1px solid var(--mj-menubar-border, var(--mj-border));
  user-select: none;
}

:host([disabled]) .menubar-root {
  opacity: 0.55;
  pointer-events: none;
}

.menu-item-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--mj-space-1);
  padding: var(--mj-menubar-item-padding, 0 var(--mj-space-3));
  min-height: var(--mj-menubar-height, var(--mj-control-height-md));
  background: transparent;
  border: none;
  font: inherit;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  border-radius: 0;
}

.menu-item-btn:hover,
.menu-item-btn[data-open="true"] {
  background: var(--mj-menubar-item-hover-bg, var(--mj-bg-muted));
}

.menu-item-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: calc(-1 * var(--mj-focus-ring-offset));
}

.menu-item-btn[aria-disabled="true"] {
  opacity: 0.45;
  cursor: not-allowed;
}

.menu-dropdown {
  position: fixed;
  z-index: var(--mj-layer-popover);
  background: var(--mj-surface-raised);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-md);
  box-shadow: var(--mj-elevation-2);
  min-width: 160px;
  padding: var(--mj-space-1) 0;
  list-style: none;
  margin: 0;
}

.menu-dropdown[hidden] { display: none; }

.menu-dropdown-item {
  display: flex;
  align-items: center;
  padding: var(--mj-space-2) var(--mj-space-4);
  font: inherit;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
  cursor: pointer;
  background: transparent;
  border: none;
  width: 100%;
  text-align: start;
  white-space: nowrap;
}

.menu-dropdown-item:hover {
  background: var(--mj-bg-muted);
}

.menu-dropdown-item:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: calc(-1 * var(--mj-focus-ring-offset));
}

.menu-dropdown-item[aria-disabled="true"] {
  opacity: 0.45;
  cursor: not-allowed;
}
`;

export class MjMenubar extends MjElement {
  static tagName = "mj-menubar";
  static styles = STYLES;
  static watched = ["label", "compact", "disabled", "active-item"];

  constructor() {
    super()
    this._roving = null
    this._openMenuIndex = -1
    this._itemDefs = []
    this._menubarId = nextId("mj-menubar")
  }

  render() {
    const label = this.getAttribute("label") || "Application menu"
    const markup = `
      <div class="menubar-root" role="menubar" part="root"
           aria-label="${label}" id="${this._menubarId}">
        <slot></slot>
      </div>
    `
    return markup
  }

  afterRender() {
    this._root = this.$(".menubar-root")
    this._slot = this.$("slot")

    this.listen(this._slot, "slotchange", this._buildFromSlot.bind(this))
    this.listen(this._root, "keydown", this._onKeydown.bind(this))

    this._buildFromSlot()
    return
  }

  _buildFromSlot() {
    // Remove injected buttons from previous builds
    const old = this._root.querySelectorAll("[data-mj-menubar-btn]")
    for (let i = 0; i < old.length; i = i + 1) {
      old[i].remove()
    }

    const assigned = this._slot.assignedElements({ flatten: true })
    this._itemDefs = []

    for (let i = 0; i < assigned.length; i = i + 1) {
      const el = assigned[i]
      const label = el.getAttribute("label") || el.textContent.trim()
      const itemId = el.id || nextId("mj-mb-item")
      el.id = itemId

      const btn = document.createElement("button")
      btn.className = "menu-item-btn"
      btn.setAttribute("role", "menuitem")
      btn.setAttribute("aria-haspopup", "menu")
      btn.setAttribute("aria-expanded", "false")
      btn.setAttribute("data-mj-menubar-btn", "")
      btn.setAttribute("data-item-index", String(i))
      btn.tabIndex = i === 0 ? 0 : -1
      btn.textContent = label

      const dropdown = this._buildDropdown(el, i)

      this._root.appendChild(btn)
      this._root.appendChild(dropdown)

      this.listen(btn, "click", this._onItemClick.bind(this, i))
      this.listen(btn, "mouseenter", this._onItemHover.bind(this, i))

      this._itemDefs.push({ btn: btn, dropdown: dropdown, el: el, label: label })
    }

    const btns = this._itemDefs.map((d) => d.btn)
    if (this._roving !== null) {
      this._roving.setItems(btns)
    } else {
      this._roving = new RovingTabindex({ items: btns, orientation: "horizontal", wrap: true })
      const dispose = this._roving.attach(this._root)
      this.onTeardown(dispose)
    }

    return
  }

  _buildDropdown(el, index) {
    const menuItems = el.querySelectorAll("[role='menuitem'], [data-menu-item], li")
    const ul = document.createElement("ul")
    ul.className = "menu-dropdown"
    ul.setAttribute("role", "menu")
    ul.setAttribute("part", "menu")
    ul.hidden = true
    ul.id = nextId("mj-mb-menu")

    if (menuItems.length > 0) {
      for (let i = 0; i < menuItems.length; i = i + 1) {
        const source = menuItems[i]
        const li = document.createElement("li")
        li.setAttribute("role", "presentation")
        const itemBtn = document.createElement("button")
        itemBtn.className = "menu-dropdown-item"
        itemBtn.setAttribute("role", "menuitem")
        itemBtn.tabIndex = -1
        itemBtn.textContent = source.textContent.trim()
        const value = source.getAttribute("value") || source.textContent.trim()
        itemBtn.setAttribute("data-value", value)
        this.listen(itemBtn, "click", this._onMenuItemClick.bind(this, index, value, el.getAttribute("label") || ""))
        li.appendChild(itemBtn)
        ul.appendChild(li)
      }
    }

    // Close dropdown on outside click
    this.listen(document, "click", (e) => {
      if (ul.hidden === false && !this.contains(e.target)) {
        this._closeMenu(index)
      }
    })

    return ul
  }

  _onItemClick(index) {
    if (this._openMenuIndex === index) {
      this._closeMenu(index)
    } else {
      this._openMenu(index)
    }
    return
  }

  _onItemHover(index) {
    if (this._openMenuIndex >= 0 && this._openMenuIndex !== index) {
      this._closeMenu(this._openMenuIndex)
      this._openMenu(index)
    }
    return
  }

  _openMenu(index) {
    const def = this._itemDefs[index]
    if (def === undefined) {
      return
    }
    this._openMenuIndex = index
    def.btn.setAttribute("aria-expanded", "true")
    def.btn.setAttribute("data-open", "true")
    def.dropdown.hidden = false

    // Position below the button
    const rect = def.btn.getBoundingClientRect()
    def.dropdown.style.top = `${rect.bottom}px`
    def.dropdown.style.left = `${rect.left}px`

    this.emit("mj-menubar-open", { item: def.el, menuId: def.dropdown.id })
    return
  }

  _closeMenu(index) {
    const def = this._itemDefs[index]
    if (def === undefined) {
      return
    }
    def.btn.setAttribute("aria-expanded", "false")
    def.btn.removeAttribute("data-open")
    def.dropdown.hidden = true
    if (this._openMenuIndex === index) {
      this._openMenuIndex = -1
    }
    this.emit("mj-menubar-close", { item: def.el, menuId: def.dropdown.id })
    return
  }

  _onMenuItemClick(itemIndex, value, groupLabel) {
    const def = this._itemDefs[itemIndex]
    if (def === undefined) {
      return
    }
    const path = [def.label, value]
    this.emit("mj-menubar-select", { item: def.el, value: value, path: path })
    this._closeMenu(itemIndex)
    def.btn.focus()
    return
  }

  _onKeydown(event) {
    const count = this._itemDefs.length
    if (count === 0) {
      return
    }

    const currentIndex = this._roving !== null ? this._roving.index : 0

    if (event.key === "Escape") {
      if (this._openMenuIndex >= 0) {
        const idx = this._openMenuIndex
        this._closeMenu(idx)
        this._itemDefs[idx].btn.focus()
        event.preventDefault()
      }
    } else if (event.key === "ArrowDown" || event.key === "Enter" || event.key === " ") {
      if (this._openMenuIndex < 0) {
        event.preventDefault()
        this._openMenu(currentIndex)
        const items = this._itemDefs[currentIndex].dropdown.querySelectorAll(".menu-dropdown-item")
        if (items.length > 0) {
          items[0].focus()
        }
      }
    } else if (event.key === "ArrowUp") {
      event.preventDefault()
      this._openMenu(currentIndex)
      const items = this._itemDefs[currentIndex].dropdown.querySelectorAll(".menu-dropdown-item")
      if (items.length > 0) {
        items[items.length - 1].focus()
      }
    } else if (event.key === "Home") {
      event.preventDefault()
      if (this._openMenuIndex >= 0) {
        this._closeMenu(this._openMenuIndex)
      }
      this._roving.focus(0)
    } else if (event.key === "End") {
      event.preventDefault()
      if (this._openMenuIndex >= 0) {
        this._closeMenu(this._openMenuIndex)
      }
      this._roving.focus(count - 1)
    }

    return
  }

  get items() {
    const found = this._itemDefs.map((d) => d.el)
    return found
  }

  get openMenu() {
    if (this._openMenuIndex < 0) {
      return null
    }
    const def = this._itemDefs[this._openMenuIndex]
    return def !== undefined ? def.dropdown : null
  }
}
