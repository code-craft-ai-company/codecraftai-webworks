/*
 * mjsplitbutton.js
 *
 * <mj-split-button> — primary action button paired with a dropdown trigger
 * that opens a menu of alternate actions.
 *
 * Menu items are the <mj-menu-item> descendants of the host; a
 * MutationObserver keeps the menu in step with them. Opening the menu moves
 * DOM focus to the role="menu" element, which tracks the active item through
 * aria-activedescendant: Arrow keys, Home and End move it, Enter or Space
 * choose it, Escape closes and returns focus to the dropdown trigger, Tab
 * closes and moves on.
 *
 * In `dynamic` mode the item chosen last becomes the primary action: the
 * primary label shows it, `activeItem` returns it and `mj-primary-click`
 * carries its value and element.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { autoPosition } from "../core/overlay.js";
import { announce } from "../core/announcer.js";
import { t } from "../core/intl.js";

const STYLES = `
:host { display: inline-flex; vertical-align: middle; }

.container {
  display: inline-flex;
  align-items: stretch;
  border-radius: var(--mj-split-button-border-radius, var(--mj-radius-md));
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
  position: relative;
  transition: background var(--mj-motion-fast);
}
/* The buttons carry the rounded corners themselves so the container does not
   have to clip its overflow, which would cut off their focus rings. */
.primary {
  flex: 1;
  gap: var(--mj-space-2);
  padding: 0 var(--mj-space-4);
  color: var(--mj-text-on-accent);
  background: var(--mj-accent);
  border-start-start-radius: var(--mj-split-button-border-radius, var(--mj-radius-md));
  border-end-start-radius: var(--mj-split-button-border-radius, var(--mj-radius-md));
}
.primary:hover:not(:disabled) { background: var(--mj-accent-hover); }
.primary:focus-visible,
.dropdown-trigger:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
  z-index: 1;
}

.divider {
  width: 1px;
  background: var(--mj-split-button-divider-color, color-mix(in srgb, var(--mj-text-on-accent) 30%, var(--mj-accent)));
  flex-shrink: 0;
}

.dropdown-trigger {
  padding: 0 var(--mj-space-3);
  color: var(--mj-text-on-accent);
  background: var(--mj-accent);
  border-start-end-radius: var(--mj-split-button-border-radius, var(--mj-radius-md));
  border-end-end-radius: var(--mj-split-button-border-radius, var(--mj-radius-md));
}
.dropdown-trigger:hover:not(:disabled) { background: var(--mj-accent-hover); }
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
:host([variant="secondary"]) .primary:hover:not(:disabled),
:host([variant="secondary"]) .dropdown-trigger:hover:not(:disabled) { background: var(--mj-bg-muted); }
:host([variant="secondary"]) .divider { background: var(--mj-border-strong); }

:host([variant="danger"]) .primary,
:host([variant="danger"]) .dropdown-trigger {
  background: var(--mj-color-danger);
  color: var(--mj-text-on-accent);
}
:host([variant="danger"]) .primary:hover:not(:disabled),
:host([variant="danger"]) .dropdown-trigger:hover:not(:disabled) {
  background: color-mix(in srgb, var(--mj-color-danger) 85%, var(--mj-text));
}
:host([variant="danger"]) .divider {
  background: var(--mj-split-button-divider-color, color-mix(in srgb, var(--mj-text-on-accent) 30%, var(--mj-color-danger)));
}

.primary:disabled,
.dropdown-trigger:disabled { opacity: 0.55; cursor: not-allowed; }
:host([disabled]) .primary,
:host([disabled]) .dropdown-trigger { pointer-events: none; }

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

.menu { padding: var(--mj-space-1) 0; outline: none; }
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

/* <mj-menu-item> attributes whose changes alter what the menu shows. */
const ITEM_ATTRIBUTES = ["value", "disabled"]

export class MjSplitButton extends MjElement {
  static tagName = "mj-split-button";
  static styles = STYLES;
  static watched = ["label", "variant", "size", "disabled", "primary-disabled", "open", "dynamic", "dropdown-label"];

  constructor() {
    super()
    this._menuItems = []
    this._focusedIndex = -1
    this._disposePosition = null

    /* Dynamic mode: the <mj-menu-item> the primary button stands for. */
    this._activeItemEl = null

    /* Set by _open(): which item to activate and that focus should move. */
    this._openFocus = null

    this._menuId = nextId("mj-sb-menu")
    this._dropdownId = nextId("mj-sb-dd")
  }

  render() {
    const markup = `
      <div class="container" part="container">
        <button class="primary" part="primary" type="button">
          <slot name="primary-icon"></slot>
          <span class="primary-label" part="primary-label"></span>
        </button>
        <span class="divider" part="divider" aria-hidden="true"></span>
        <button
          class="dropdown-trigger"
          part="dropdown-trigger"
          id="${this._dropdownId}"
          type="button"
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
    this._primaryLabel = this.$(".primary-label")
    this._dropdownBtn = this.$(".dropdown-trigger")
    this._popup = this.$(".popup")
    this._menu = this.$(".menu")

    this.listen(this._primaryBtn, "click", this._onPrimaryClick.bind(this))
    this.listen(this._dropdownBtn, "click", this._onDropdownClick.bind(this))
    this.listen(this._dropdownBtn, "keydown", this._onDropdownKeydown.bind(this))
    this.listen(this._menu, "keydown", this._onMenuKeydown.bind(this))

    /* One delegated pair of listeners serves every menu item. */
    this.listen(this._menu, "click", this._onMenuItemClick.bind(this))
    this.listen(this._menu, "mouseover", this._onMenuItemHover.bind(this))

    this.listen(this._popup, "focusout", this._onPopupFocusOut.bind(this))
    this.listen(document, "click", this._onDocClick.bind(this))

    this._observeItems()
    this._buildMenu()
    this._syncLabels()
    this._syncDisabled()

    /* `open` present at first render, or still set when the element is re-inserted. */
    this._syncOpen()
    return
  }

  onDisconnected() {
    this._stopPositioning()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "open") {
      this._syncOpen()
    }
    if (name === "label" || name === "dropdown-label" || name === "dynamic") {
      this._syncLabels()
    }
    if (name === "disabled" || name === "primary-disabled") {
      this._syncDisabled()
    }
    return
  }

  /* ----- menu building ----- */

  /*
   * Rebuild the menu whenever the <mj-menu-item> children change, so items
   * added after the first render appear and an initially empty menu becomes
   * usable.
   */
  _observeItems() {
    if (typeof MutationObserver !== "function") {
      return
    }
    const observer = new MutationObserver((records) => {
      const relevant = records.some((record) => {
        return record.type !== "attributes" || record.target !== this
      })
      if (relevant === true && this._menu !== undefined && this._menu !== null) {
        this._buildMenu()
        this._syncLabels()
        this._syncDisabled()
      }
    })
    observer.observe(this, {
      childList: true,
      subtree: true,
      characterData: true,
      attributes: true,
      attributeFilter: ITEM_ATTRIBUTES
    })
    this.onTeardown(() => {
      observer.disconnect()
    })
    return
  }

  /*
   * Build one role="menuitem" row per <mj-menu-item>, with DOM APIs and
   * textContent: item text is application data, never markup.
   */
  _buildMenu() {
    const itemEls = Array.from(this.querySelectorAll("mj-menu-item"))

    /* Keep the active item by element across the rebuild. */
    const activeBefore = this._menuItems[this._focusedIndex]
    const activeEl = activeBefore !== undefined ? activeBefore.el : null

    this._menu.replaceChildren()
    this._menuItems = itemEls.map((el, idx) => {
      const label = el.textContent.replace(/\s+/g, " ").trim()

      const node = document.createElement("div")
      node.className = "menu-item"
      node.setAttribute("part", "menu-item")
      node.setAttribute("role", "menuitem")
      node.id = nextId("mj-sb-mi")
      node.dataset.index = String(idx)
      node.tabIndex = -1

      const disabled = el.hasAttribute("disabled")
      if (disabled === true) {
        node.setAttribute("aria-disabled", "true")
      }

      const labelEl = document.createElement("span")
      labelEl.className = "menu-item-label"
      labelEl.setAttribute("part", "menu-item-label")
      labelEl.textContent = label
      node.appendChild(labelEl)

      this._menu.appendChild(node)

      const item = {
        id: node.id,
        label: label,
        value: el.hasAttribute("value") === true ? el.getAttribute("value") : label,
        disabled: disabled,
        index: idx,
        el: el,
        node: node
      }
      return item
    })

    if (this._activeItemEl !== null && itemEls.includes(this._activeItemEl) === false) {
      /* The item behind the dynamic primary action was removed. */
      this._activeItemEl = null
    }

    const restored = this._menuItems.findIndex((item) => item.el === activeEl)
    this._focusedIndex = -1
    this._menu.removeAttribute("aria-activedescendant")
    if (this.hasAttribute("open") === true) {
      this._moveFocus(restored >= 0 ? restored : this._stepEnabled(-1, 1))
    }
    return
  }

  /* The record of the item the dynamic primary action stands for, if any. */
  _activeItem() {
    let item = undefined
    if (this.hasAttribute("dynamic") === true && this._activeItemEl !== null) {
      item = this._menuItems.find((candidate) => candidate.el === this._activeItemEl)
    }
    return item
  }

  /* Text and accessible names of the two buttons. */
  _syncLabels() {
    if (this._primaryBtn === undefined || this._primaryBtn === null) {
      return
    }

    const activeItem = this._activeItem()
    const label = activeItem !== undefined ? activeItem.label : (this.getAttribute("label") || "")

    this._primaryLabel.textContent = label
    if (label.length > 0) {
      this._primaryBtn.setAttribute("aria-label", label)
    } else {
      this._primaryBtn.removeAttribute("aria-label")
    }

    this._dropdownBtn.setAttribute("aria-label", this.getAttribute("dropdown-label") || t("mj.splitButton.moreActions"))
    return
  }

  /*
   * `disabled` turns both buttons off, `primary-disabled` only the primary
   * one; a menu without items leaves nothing for the dropdown to open.
   */
  _syncDisabled() {
    if (this._primaryBtn === undefined || this._primaryBtn === null) {
      return
    }

    const disabled = this.hasAttribute("disabled")
    this._primaryBtn.disabled = disabled === true || this.hasAttribute("primary-disabled") === true
    this._dropdownBtn.disabled = disabled === true || this._menuItems.length === 0

    if (disabled === true) {
      this._close(false)
    }
    return
  }

  /* ----- open/close ----- */

  _stopPositioning() {
    if (this._disposePosition !== null) {
      this._disposePosition()
      this._disposePosition = null
    }
    return
  }

  /*
   * Bring the popup and the trigger in line with the `open` attribute. Safe
   * to call repeatedly: the positioner is replaced, never stacked. DOM focus
   * moves into the menu only when the menu was opened through _open().
   */
  _syncOpen() {
    if (this._dropdownBtn === undefined || this._dropdownBtn === null) {
      return
    }

    const isOpen = this.hasAttribute("open")
    this._dropdownBtn.setAttribute("aria-expanded", isOpen === true ? "true" : "false")
    this._stopPositioning()

    if (isOpen === true) {
      this._disposePosition = autoPosition(this._popup, this._dropdownBtn, {
        placement: "bottom-end"
      })

      const wanted = this._openFocus
      this._openFocus = null
      if (wanted === "last") {
        this._moveFocus(this._stepEnabled(this._menuItems.length, -1))
      } else if (wanted === "first" || this._focusedIndex < 0) {
        this._moveFocus(this._stepEnabled(-1, 1))
      }
      if (wanted !== null) {
        this._menu.focus()
      }
    } else {
      this._clearFocus()
    }
    return
  }

  /* Open the menu with the first ("first") or last ("last") item active. */
  _open(focusTarget) {
    if (this.hasAttribute("disabled") === true || this.hasAttribute("open") === true) {
      return
    }
    const proceed = this.emit("mj-open", {}, { cancelable: true })
    if (proceed === false) {
      return
    }
    this._openFocus = focusTarget === "last" ? "last" : "first"
    this.setAttribute("open", "")
    return
  }

  /* Close the menu; `restoreFocus` puts focus back on the dropdown trigger. */
  _close(restoreFocus) {
    if (this.hasAttribute("open") === false) {
      return
    }
    this.removeAttribute("open")
    this.emit("mj-close", {})
    if (restoreFocus === true && this._dropdownBtn !== undefined && this._dropdownBtn !== null) {
      this._dropdownBtn.focus()
    }
    return
  }

  /*
   * Index of the next enabled item from `from` in direction `delta`,
   * wrapping round; -1 when no item is enabled.
   */
  _stepEnabled(from, delta) {
    const count = this._menuItems.length
    let found = -1

    for (let offset = 1; offset <= count; offset = offset + 1) {
      const index = (((from + delta * offset) % count) + count) % count
      if (this._menuItems[index].disabled !== true) {
        found = index
        break
      }
    }

    return found
  }

  _moveFocus(index) {
    this._menuItems.forEach((item) => item.node.classList.remove("focused"))
    const item = this._menuItems[index]
    if (item !== undefined) {
      item.node.classList.add("focused")
      item.node.scrollIntoView({ block: "nearest" })
      this._menu.setAttribute("aria-activedescendant", item.id)
      this._focusedIndex = index
    }
    return
  }

  _clearFocus() {
    this._menuItems.forEach((item) => item.node.classList.remove("focused"))
    this._menu.removeAttribute("aria-activedescendant")
    this._focusedIndex = -1
    return
  }

  /* ----- event handlers ----- */

  _onPrimaryClick() {
    if (this.hasAttribute("disabled") || this.hasAttribute("primary-disabled")) {
      return
    }
    const activeItem = this._activeItem()
    this.emit("mj-primary-click", {
      value: activeItem !== undefined ? activeItem.value : "",
      item: activeItem !== undefined ? activeItem.el : null
    })
    return
  }

  _onDropdownClick() {
    if (this.hasAttribute("disabled")) {
      return
    }
    if (this.hasAttribute("open")) {
      this._close(true)
    } else {
      this._open("first")
    }
    return
  }

  _onDropdownKeydown(event) {
    if (this.hasAttribute("open") === true) {
      /* Open with focus still on the trigger: the menu keys work from here too. */
      this._onMenuKeydown(event)
      return
    }

    if (event.key === "ArrowDown" || event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      this._open("first")
    } else if (event.key === "ArrowUp") {
      event.preventDefault()
      this._open("last")
    }
    return
  }

  _onMenuKeydown(event) {
    const count = this._menuItems.length

    if (event.key === "ArrowDown") {
      event.preventDefault()
      this._moveFocus(this._stepEnabled(this._focusedIndex, 1))
    } else if (event.key === "ArrowUp") {
      event.preventDefault()
      const from = this._focusedIndex >= 0 ? this._focusedIndex : count
      this._moveFocus(this._stepEnabled(from, -1))
    } else if (event.key === "Home") {
      event.preventDefault()
      this._moveFocus(this._stepEnabled(-1, 1))
    } else if (event.key === "End") {
      event.preventDefault()
      this._moveFocus(this._stepEnabled(count, -1))
    } else if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      const item = this._menuItems[this._focusedIndex]
      if (item !== undefined && item.disabled !== true) {
        this._selectItem(item)
      }
    } else if (event.key === "Escape") {
      /* Consumed here so an enclosing dialog does not close as well. */
      event.preventDefault()
      this._close(true)
    } else if (event.key === "Tab") {
      /* Tab leaves from the trigger, so it lands on the next control. */
      this._dropdownBtn.focus()
      this._close(false)
    }
    return
  }

  _itemFor(event) {
    const node = event.target instanceof Element ? event.target.closest(".menu-item") : null
    const item = node !== null ? this._menuItems[parseInt(node.dataset.index, 10)] : undefined
    return item
  }

  _onMenuItemClick(event) {
    const item = this._itemFor(event)
    if (item === undefined || item.disabled === true) {
      return
    }
    this._selectItem(item)
    return
  }

  _onMenuItemHover(event) {
    const item = this._itemFor(event)
    if (item !== undefined && item.disabled !== true && item.index !== this._focusedIndex) {
      this._moveFocus(item.index)
    }
    return
  }

  _selectItem(item) {
    this.emit("mj-menu-select", {
      item: item.el,
      value: item.value
    })

    if (this.hasAttribute("dynamic") === true) {
      /* Held in a field so the label survives a re-render. */
      this._activeItemEl = item.el
      this._syncLabels()
      announce(t("mj.splitButton.defaultChanged", { label: item.label }), "polite")
    }

    this._close(true)
    return
  }

  /* Focus left the menu for somewhere outside this control: light dismiss. */
  _onPopupFocusOut(event) {
    const next = event.relatedTarget
    const staysInside = next instanceof Node && this.shadowRoot.contains(next) === true
    if (staysInside === false) {
      this._close(false)
    }
    return
  }

  _onDocClick(event) {
    if (this.hasAttribute("open") === false) {
      return
    }
    const inside = event.composedPath().includes(this)
    if (inside === false) {
      this._close(false)
    }
    return
  }

  /* ----- scriptable API ----- */

  get open() {
    return this.hasAttribute("open")
  }

  set open(value) {
    if (value === true) {
      this._open("first")
    } else {
      this._close(false)
    }
    return
  }

  get menuItems() {
    return Array.from(this.querySelectorAll("mj-menu-item"))
  }

  /* Dynamic mode: the <mj-menu-item> the primary button stands for, or null. */
  get activeItem() {
    const item = this._activeItem()
    const element = item !== undefined ? item.el : null
    return element
  }

  set activeItem(element) {
    this._activeItemEl = element instanceof Element ? element : null
    this._syncLabels()
    return
  }
}
