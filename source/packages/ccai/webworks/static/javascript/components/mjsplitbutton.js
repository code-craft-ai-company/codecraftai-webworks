/*
 * mjsplitbutton.js
 *
 * <mj-split-button> — primary action button paired with a dropdown trigger
 * that opens a menu of alternate actions.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { autoPosition } from "../core/overlay.js";
import { announce } from "../core/announcer.js";

const STYLES = `
:host { display: inline-flex; vertical-align: middle; }

.container {
  display: inline-flex;
  align-items: stretch;
  border-radius: var(--mj-split-button-border-radius, var(--mj-radius-md));
  overflow: hidden;
  box-shadow: 0 0 0 1px var(--mj-border-strong);
}

.primary, .dropdown-trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: var(--mj-split-button-height, var(--mj-control-height-md));
  font: inherit;
  font-weight: var(--mj-font-weight-medium);
  cursor: pointer;
  border: none;
  transition: background var(--mj-motion-fast);
}
.primary {
  flex: 1;
  gap: var(--mj-space-2);
  padding: 0 var(--mj-space-4);
  color: var(--mj-text-on-accent);
  background: var(--mj-accent);
}
.primary:hover { background: var(--mj-accent-hover); }
.primary:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.divider {
  width: 1px;
  background: var(--mj-split-button-divider-color, rgba(255,255,255,0.3));
  flex-shrink: 0;
}

.dropdown-trigger {
  padding: 0 var(--mj-space-3);
  color: var(--mj-text-on-accent);
  background: var(--mj-accent);
}
.dropdown-trigger:hover { background: var(--mj-accent-hover); }
.dropdown-trigger:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.chevron {
  width: 1em; height: 1em;
  transition: transform var(--mj-motion-fast);
}
:host([open]) .chevron { transform: rotate(180deg); }

/* Variants */
:host([variant="secondary"]) .primary,
:host([variant="secondary"]) .dropdown-trigger {
  color: var(--mj-text);
  background: var(--mj-surface);
}
:host([variant="secondary"]) .primary:hover,
:host([variant="secondary"]) .dropdown-trigger:hover { background: var(--mj-bg-muted); }
:host([variant="secondary"]) .divider { background: var(--mj-border-strong); }

:host([variant="danger"]) .primary,
:host([variant="danger"]) .dropdown-trigger {
  background: var(--mj-color-danger);
  color: white;
}
:host([variant="danger"]) .divider { background: rgba(255,255,255,0.3); }

:host([disabled]) .primary,
:host([disabled]) .dropdown-trigger { opacity: 0.55; cursor: not-allowed; pointer-events: none; }

:host([size="sm"]) .primary,
:host([size="sm"]) .dropdown-trigger { min-height: var(--mj-control-height-sm); font-size: var(--mj-font-size-sm); }
:host([size="lg"]) .primary,
:host([size="lg"]) .dropdown-trigger { min-height: var(--mj-control-height-lg); font-size: var(--mj-font-size-lg); }

.popup {
  position: fixed;
  background: var(--mj-surface-raised, var(--mj-surface));
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-md);
  box-shadow: var(--mj-elevation-2);
  min-width: var(--mj-split-button-popup-min-width, 10rem);
  z-index: var(--mj-layer-popover);
  display: none;
}
:host([open]) .popup { display: block; }

.menu { padding: var(--mj-space-1) 0; }
.menu-item {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  padding: var(--mj-space-2) var(--mj-space-3);
  cursor: pointer;
  color: var(--mj-text);
  font-size: var(--mj-font-size-md);
}
.menu-item:hover, .menu-item.focused { background: var(--mj-bg-muted); }
.menu-item[aria-disabled="true"] { opacity: 0.45; cursor: not-allowed; }
`;

export class MjSplitButton extends MjElement {
  static tagName = "mj-split-button";
  static styles = STYLES;
  static watched = ["label", "variant", "size", "disabled", "primary-disabled", "open", "dynamic", "dropdown-label"];

  constructor() {
    super()
    this._menuItems = []
    this._focusedIndex = -1
    this._disposePosition = null
    this._menuId = nextId("mj-sb-menu")
    this._dropdownId = nextId("mj-sb-dd")
  }

  render() {
    const label = this.getAttribute("label") || ""
    const dropdownLabel = this.getAttribute("dropdown-label") || "More actions"
    const markup = `
      <div class="container" part="container">
        <button class="primary" part="primary" type="button" aria-label="${label}">
          <slot name="primary-icon"></slot>
          <span class="primary-label" part="primary-label">${label}</span>
        </button>
        <span class="divider" part="divider" aria-hidden="true"></span>
        <button
          class="dropdown-trigger"
          part="dropdown-trigger"
          id="${this._dropdownId}"
          type="button"
          aria-label="${dropdownLabel}"
          aria-haspopup="menu"
          aria-expanded="false"
          aria-controls="${this._menuId}"
        >
          <svg class="chevron" part="dropdown-icon" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
            <path d="M8 10.5 3 5.5h10z"/>
          </svg>
        </button>
      </div>
      <div class="popup" part="popup">
        <div
          class="menu"
          part="menu"
          id="${this._menuId}"
          role="menu"
          aria-labelledby="${this._dropdownId}"
          tabindex="-1"
        ></div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._primaryBtn = this.$(".primary")
    this._dropdownBtn = this.$(".dropdown-trigger")
    this._popup = this.$(".popup")
    this._menu = this.$(".menu")

    this.listen(this._primaryBtn, "click", this._onPrimaryClick.bind(this))
    this.listen(this._dropdownBtn, "click", this._onDropdownClick.bind(this))
    this.listen(this._dropdownBtn, "keydown", this._onDropdownKeydown.bind(this))
    this.listen(this._menu, "keydown", this._onMenuKeydown.bind(this))
    this.listen(document, "click", this._onDocClick.bind(this))

    this._buildMenu()

    const slot = this.shadowRoot.querySelector("slot:not([name])")
    if (slot !== null) {
      this.listen(slot, "slotchange", () => this._buildMenu())
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "open") {
      this._syncOpen()
    }
    if (name === "label" && this._primaryBtn !== undefined) {
      this._primaryBtn.setAttribute("aria-label", newValue || "")
      const lbl = this._primaryBtn.querySelector(".primary-label")
      if (lbl !== null) {
        lbl.textContent = newValue || ""
      }
    }
    if (name === "disabled") {
      this._syncDisabled()
    }
    return
  }

  _buildMenu() {
    const itemEls = Array.from(this.querySelectorAll("mj-menu-item"))
    if (itemEls.length === 0) {
      this._dropdownBtn.disabled = true
      return
    }

    this._menuItems = itemEls.map((el, idx) => ({
      id: nextId("mj-sb-mi"),
      label: el.textContent.trim(),
      value: el.getAttribute("value") || "",
      disabled: el.hasAttribute("disabled"),
      index: idx,
      el: el
    }))

    let html = ""
    this._menuItems.forEach((item) => {
      const disabledAttr = item.disabled === true ? ' aria-disabled="true"' : ""
      html += `<div
        class="menu-item"
        part="menu-item"
        role="menuitem"
        id="${item.id}"
        data-value="${item.value}"
        data-index="${item.index}"
        tabindex="-1"
        ${disabledAttr}
      ><span class="menu-item-label" part="menu-item-label">${item.label}</span></div>`
    })
    this._menu.innerHTML = html

    const items = this._menu.querySelectorAll(".menu-item")
    items.forEach((item) => {
      this.listen(item, "click", this._onMenuItemClick.bind(this))
    })
    return
  }

  _syncOpen() {
    const isOpen = this.hasAttribute("open")
    this._dropdownBtn.setAttribute("aria-expanded", isOpen === true ? "true" : "false")
    if (isOpen === true) {
      this._disposePosition = autoPosition(this._popup, this._dropdownBtn, {
        placement: "bottom-end"
      })
      this._focusedIndex = 0
      this._moveFocus(0)
    } else {
      if (this._disposePosition !== null) {
        this._disposePosition()
        this._disposePosition = null
      }
      this._focusedIndex = -1
    }
    return
  }

  _open() {
    if (this.hasAttribute("disabled")) {
      return
    }
    const proceed = this.emit("mj-open", {}, { cancelable: true })
    if (proceed === false) {
      return
    }
    this.setAttribute("open", "")
    return
  }

  _close() {
    if (this.hasAttribute("open") === false) {
      return
    }
    this.removeAttribute("open")
    this.emit("mj-close", {})
    return
  }

  _moveFocus(index) {
    const items = Array.from(this._menu.querySelectorAll(".menu-item"))
    items.forEach((el) => el.classList.remove("focused"))
    const item = items[index]
    if (item !== undefined) {
      item.classList.add("focused")
      this._menu.setAttribute("aria-activedescendant", item.id)
      this._focusedIndex = index
    }
    return
  }

  _onPrimaryClick() {
    if (this.hasAttribute("disabled") || this.hasAttribute("primary-disabled")) {
      return
    }
    this.emit("mj-primary-click", {})
    return
  }

  _onDropdownClick() {
    if (this.hasAttribute("disabled")) {
      return
    }
    if (this.hasAttribute("open")) {
      this._close()
    } else {
      this._open()
    }
    return
  }

  _onDropdownKeydown(event) {
    if (event.key === "ArrowDown" || event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      this._open()
    } else if (event.key === "ArrowUp") {
      event.preventDefault()
      this._open()
      const count = this._menuItems.length
      if (count > 0) {
        this._moveFocus(count - 1)
      }
    }
    return
  }

  _onMenuKeydown(event) {
    const items = Array.from(this._menu.querySelectorAll(".menu-item"))
    const count = items.length
    if (count === 0) {
      return
    }

    if (event.key === "ArrowDown") {
      event.preventDefault()
      const next = (this._focusedIndex + 1) % count
      this._moveFocus(next)
    } else if (event.key === "ArrowUp") {
      event.preventDefault()
      const prev = (this._focusedIndex - 1 + count) % count
      this._moveFocus(prev)
    } else if (event.key === "Home") {
      event.preventDefault()
      this._moveFocus(0)
    } else if (event.key === "End") {
      event.preventDefault()
      this._moveFocus(count - 1)
    } else if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      const item = items[this._focusedIndex]
      if (item !== undefined && item.getAttribute("aria-disabled") !== "true") {
        this._selectItem(item)
      }
    } else if (event.key === "Escape" || event.key === "Tab") {
      this._close()
      this._dropdownBtn.focus()
    }
    return
  }

  _onMenuItemClick(event) {
    const node = event.currentTarget
    if (node.getAttribute("aria-disabled") === "true") {
      return
    }
    this._selectItem(node)
    return
  }

  _selectItem(node) {
    const value = node.dataset.value
    const idx = parseInt(node.dataset.index, 10)
    const data = this._menuItems[idx]

    this.emit("mj-menu-select", {
      item: data !== undefined ? data.el : null,
      value: value
    })

    if (this.hasAttribute("dynamic") === true) {
      const label = node.querySelector(".menu-item-label")
      const labelText = label !== null ? label.textContent : ""
      if (this._primaryBtn !== undefined) {
        this._primaryBtn.setAttribute("aria-label", labelText)
        const lbl = this._primaryBtn.querySelector(".primary-label")
        if (lbl !== null) {
          lbl.textContent = labelText
        }
      }
      announce(`Default action changed to ${labelText}`, "polite")
    }

    this._close()
    this._dropdownBtn.focus()
    return
  }

  _onDocClick(event) {
    if (this.hasAttribute("open") === false) {
      return
    }
    const inside = event.composedPath().includes(this)
    if (inside === false) {
      this._close()
    }
    return
  }

  _syncDisabled() {
    if (this._primaryBtn === undefined) {
      return
    }
    const disabled = this.hasAttribute("disabled")
    this._primaryBtn.disabled = disabled
    this._dropdownBtn.disabled = disabled
    return
  }

  get open() {
    return this.hasAttribute("open")
  }

  set open(value) {
    if (value === true) {
      this._open()
    } else {
      this._close()
    }
    return
  }

  get menuItems() {
    return Array.from(this.querySelectorAll("mj-menu-item"))
  }
}
