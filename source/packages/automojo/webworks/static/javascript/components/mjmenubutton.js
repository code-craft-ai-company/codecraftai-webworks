/*
 * mjmenubutton.js
 *
 * <mj-menu-button> — single trigger button that opens an actions menu.
 * Covers kebab/meatball/overflow menus.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { autoPosition } from "../core/overlay.js";

const STYLES = `
:host { display: inline-block; vertical-align: middle; }

.trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--mj-space-2);
  min-height: var(--mj-menu-button-trigger-size, var(--mj-control-height-md));
  min-width: var(--mj-menu-button-trigger-size, var(--mj-control-height-md));
  padding: 0 var(--mj-space-3);
  font: inherit;
  font-weight: var(--mj-font-weight-medium);
  color: var(--mj-text);
  background: var(--mj-surface);
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-md);
  cursor: pointer;
  user-select: none;
  transition: background var(--mj-motion-fast);
}
:host([icon-only]) .trigger { padding: 0; }
.trigger:hover { background: var(--mj-bg-muted); }
.trigger:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
:host([disabled]) .trigger { opacity: 0.55; cursor: not-allowed; pointer-events: none; }

:host([size="sm"]) .trigger { min-height: var(--mj-control-height-sm); font-size: var(--mj-font-size-sm); }
:host([size="lg"]) .trigger { min-height: var(--mj-control-height-lg); font-size: var(--mj-font-size-lg); }

.trigger-label { }
:host([icon-only]) .trigger-label { display: none; }

.popup {
  position: fixed;
  background: var(--mj-surface-raised, var(--mj-surface));
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-menu-border-radius, var(--mj-radius-md));
  box-shadow: var(--mj-elevation-2);
  min-width: var(--mj-menu-popup-min-width, 10rem);
  max-height: var(--mj-menu-popup-max-height, 24rem);
  overflow-y: auto;
  z-index: var(--mj-layer-popover);
  display: none;
}
:host([open]) .popup { display: block; }

.menu { padding: var(--mj-space-1) 0; }

.menu-item {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  padding: var(--mj-menu-item-padding, var(--mj-space-2) var(--mj-space-3));
  min-height: var(--mj-menu-item-height, var(--mj-control-height-md));
  cursor: pointer;
  color: var(--mj-text);
  font-size: var(--mj-font-size-md);
  user-select: none;
}
.menu-item:hover, .menu-item.focused { background: var(--mj-bg-muted); }
.menu-item[aria-disabled="true"] { opacity: 0.45; cursor: not-allowed; }
.menu-item[data-variant="danger"] { color: var(--mj-color-danger); }

.menu-separator {
  height: 1px;
  background: var(--mj-menu-separator-color, var(--mj-border));
  margin: var(--mj-space-1) 0;
}

.menu-group-label {
  padding: var(--mj-space-1) var(--mj-space-3);
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
  font-weight: var(--mj-font-weight-medium);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.shortcut {
  margin-inline-start: auto;
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
}
`;

export class MjMenuButton extends MjElement {
  static tagName = "mj-menu-button";
  static styles = STYLES;
  static watched = ["label", "icon-only", "disabled", "open", "placement", "size"];

  constructor() {
    super()
    this._itemData = []
    this._focusedIndex = -1
    this._disposePosition = null
    this._menuId = nextId("mj-mb-menu")
    this._triggerId = nextId("mj-mb-tr")
  }

  render() {
    const label = this.getAttribute("label") || ""
    const markup = `
      <button
        class="trigger"
        part="trigger"
        id="${this._triggerId}"
        type="button"
        aria-haspopup="menu"
        aria-expanded="false"
        aria-controls="${this._menuId}"
        ${label.length > 0 ? `aria-label="${label}"` : ""}
      >
        <slot name="trigger-icon"></slot>
        <span class="trigger-label" part="trigger-label">${label}</span>
      </button>
      <div class="popup" part="popup">
        <div
          class="menu"
          part="menu"
          id="${this._menuId}"
          role="menu"
          aria-labelledby="${this._triggerId}"
          tabindex="-1"
        ></div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._trigger = this.$(".trigger")
    this._popup = this.$(".popup")
    this._menu = this.$(".menu")

    this.listen(this._trigger, "click", this._onTriggerClick.bind(this))
    this.listen(this._trigger, "keydown", this._onTriggerKeydown.bind(this))
    this.listen(this._menu, "keydown", this._onMenuKeydown.bind(this))
    this.listen(document, "click", this._onDocClick.bind(this))
    this.listen(document, "focusin", this._onDocFocusin.bind(this))

    this._buildMenu()

    const slot = this.shadowRoot.querySelector("slot:not([name])")
    if (slot !== null) {
      this.listen(slot, "slotchange", () => this._buildMenu())
    }

    this._checkLabel()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "open") {
      this._syncOpen()
    }
    if (name === "label" && this._trigger !== undefined) {
      this._trigger.setAttribute("aria-label", newValue || "")
      const lbl = this._trigger.querySelector(".trigger-label")
      if (lbl !== null) {
        lbl.textContent = newValue || ""
      }
    }
    if (name === "disabled" && this._trigger !== undefined) {
      this._trigger.disabled = this.hasAttribute("disabled")
    }
    return
  }

  _checkLabel() {
    const iconOnly = this.hasAttribute("icon-only")
    if (iconOnly === true) {
      const label = this.getAttribute("label") || this.getAttribute("aria-label") || ""
      if (label.length === 0) {
        console.error("<mj-menu-button>: icon-only mode requires a label or aria-label attribute.")
        this._trigger.setAttribute("aria-label", "Actions")
      }
    }
    return
  }

  _buildMenu() {
    const allChildren = Array.from(this.childNodes)
    const itemEls = Array.from(this.querySelectorAll("mj-menu-item"))

    if (itemEls.length === 0) {
      this._trigger.disabled = true
      console.warn("<mj-menu-button>: no menu items slotted.")
      return
    }

    this._itemData = itemEls.map((el, idx) => ({
      id: nextId("mj-mb-mi"),
      label: el.textContent.trim(),
      value: el.getAttribute("value") || "",
      disabled: el.hasAttribute("disabled"),
      variant: el.getAttribute("variant") || "",
      shortcut: el.getAttribute("shortcut") || "",
      index: idx,
      el: el
    }))

    let html = ""
    this._itemData.forEach((item) => {
      const disabledAttr = item.disabled === true ? ' aria-disabled="true"' : ""
      const variantAttr = item.variant.length > 0 ? ` data-variant="${item.variant}"` : ""
      const shortcutHtml = item.shortcut.length > 0 ? `<span class="shortcut" aria-hidden="true">${item.shortcut}</span>` : ""
      html += `<div
        class="menu-item"
        part="menu-item"
        role="menuitem"
        id="${item.id}"
        data-value="${item.value}"
        data-index="${item.index}"
        tabindex="-1"
        ${disabledAttr}${variantAttr}
      >
        <span class="menu-item-label" part="menu-item-label">${item.label}</span>
        ${shortcutHtml}
      </div>`
    })
    this._menu.innerHTML = html

    const items = this._menu.querySelectorAll(".menu-item")
    items.forEach((item) => {
      this.listen(item, "click", this._onItemClick.bind(this))
    })
    return
  }

  _syncOpen() {
    const isOpen = this.hasAttribute("open")
    this._trigger.setAttribute("aria-expanded", isOpen === true ? "true" : "false")
    if (isOpen === true) {
      const placement = this.getAttribute("placement") || "bottom-start"
      this._disposePosition = autoPosition(this._popup, this._trigger, { placement })
      this._focusedIndex = 0
      this._moveFocus(0)
    } else {
      if (this._disposePosition !== null) {
        this._disposePosition()
        this._disposePosition = null
      }
      this._focusedIndex = -1
      this._clearFocus()
    }
    return
  }

  _open(focusLast) {
    if (this.hasAttribute("disabled")) {
      return
    }
    const proceed = this.emit("mj-open", {}, { cancelable: true })
    if (proceed === false) {
      return
    }
    this.setAttribute("open", "")
    if (focusLast === true) {
      const count = this._itemData.length
      if (count > 0) {
        this._moveFocus(count - 1)
      }
    }
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

  _clearFocus() {
    const items = this._menu.querySelectorAll(".menu-item")
    items.forEach((el) => el.classList.remove("focused"))
    this._menu.removeAttribute("aria-activedescendant")
    return
  }

  _onTriggerClick() {
    if (this.hasAttribute("open")) {
      this._close()
    } else {
      this._open(false)
    }
    return
  }

  _onTriggerKeydown(event) {
    if (event.key === "ArrowDown" || event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      this._open(false)
    } else if (event.key === "ArrowUp") {
      event.preventDefault()
      this._open(true)
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
        this._activateItem(item)
      }
    } else if (event.key === "Escape") {
      this._close()
      this._trigger.focus()
    } else if (event.key === "Tab") {
      this._close()
    }
    return
  }

  _onItemClick(event) {
    const node = event.currentTarget
    if (node.getAttribute("aria-disabled") === "true") {
      return
    }
    this._activateItem(node)
    return
  }

  _activateItem(node) {
    const idx = parseInt(node.dataset.index, 10)
    const data = this._itemData[idx]
    this.emit("mj-select", {
      item: data !== undefined ? data.el : null,
      value: node.dataset.value
    })
    this._close()
    this._trigger.focus()
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

  _onDocFocusin(event) {
    if (this.hasAttribute("open") === false) {
      return
    }
    const inside = event.composedPath().includes(this)
    if (inside === false) {
      this._close()
    }
    return
  }

  get open() {
    return this.hasAttribute("open")
  }

  set open(value) {
    if (value === true) {
      this._open(false)
    } else {
      this._close()
    }
    return
  }

  get menuItems() {
    return Array.from(this.querySelectorAll("mj-menu-item"))
  }

  focus() {
    if (this._trigger !== undefined) {
      this._trigger.focus()
    }
    return
  }
}
