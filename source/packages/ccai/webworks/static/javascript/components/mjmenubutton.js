/*
 * mjmenubutton.js
 *
 * <mj-menu-button> — single trigger button that opens an actions menu.
 * Covers kebab/meatball/overflow menus.
 *
 * The menu is built from the host's children:
 *   <mj-menu-item value variant shortcut disabled>   an action row
 *   <mj-menu-item type="checkbox|radio" checked>     a checkable row
 *   <mj-menu-separator>                              a divider
 *   <mj-menu-group label="...">                      a labelled group of rows
 * A MutationObserver keeps the menu in step with them.
 *
 * Opening the menu moves DOM focus to the role="menu" element, which tracks
 * the active item through aria-activedescendant: Arrow keys, Home and End
 * move it, Enter or Space activate it, Escape closes and returns focus to
 * the trigger, Tab closes and moves on.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { autoPosition } from "../core/overlay.js";
import { t } from "../core/intl.js";

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
.trigger:hover:not(:disabled) { background: var(--mj-bg-muted); }
.trigger:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.trigger:disabled { opacity: 0.55; cursor: not-allowed; }
:host([disabled]) .trigger { pointer-events: none; }

:host([size="sm"]) .trigger { min-height: var(--mj-control-height-sm); font-size: var(--mj-font-size-sm); }
:host([size="lg"]) .trigger { min-height: var(--mj-control-height-lg); font-size: var(--mj-font-size-lg); }

.trigger-label:empty { display: none; }
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

.menu { padding: var(--mj-space-1) 0; outline: none; }

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

.menu-item-check { width: 1em; height: 1em; flex-shrink: 0; visibility: hidden; }
.menu-item[aria-checked="true"] .menu-item-check { visibility: visible; }

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

const CHECK_ICON_MARKUP =
  '<svg class="menu-item-check" aria-hidden="true" viewBox="0 0 16 16" fill="currentColor"><path d="M13.5 3.5 6 11 2.5 7.5l1-1L6 9 12.5 2.5z"/></svg>'

/* Child attributes whose changes alter what the menu shows. */
const ITEM_ATTRIBUTES = ["value", "disabled", "variant", "shortcut", "type", "checked", "label"]

export class MjMenuButton extends MjElement {
  static tagName = "mj-menu-button";
  static styles = STYLES;
  static watched = ["label", "aria-label", "icon-only", "disabled", "open", "placement", "size"];

  constructor() {
    super()
    this._itemData = []
    this._focusedIndex = -1
    this._disposePosition = null

    /* Set by _open(): which item to activate and that focus should move. */
    this._openFocus = null

    /* The missing-label error of an icon-only trigger is logged once. */
    this._missingLabelReported = false

    this._menuId = nextId("mj-mb-menu")
    this._triggerId = nextId("mj-mb-tr")
  }

  render() {
    const markup = `
      <button
        class="trigger"
        part="trigger"
        id="${this._triggerId}"
        type="button"
        aria-haspopup="menu"
        aria-expanded="false"
        aria-controls="${this._menuId}"
      >
        <slot name="trigger-icon"></slot>
        <span class="trigger-label" part="trigger-label"></span>
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
    this._triggerLabel = this.$(".trigger-label")
    this._popup = this.$(".popup")
    this._menu = this.$(".menu")

    this.listen(this._trigger, "click", this._onTriggerClick.bind(this))
    this.listen(this._trigger, "keydown", this._onTriggerKeydown.bind(this))
    this.listen(this._menu, "keydown", this._onMenuKeydown.bind(this))

    /* One delegated pair of listeners serves every menu item. */
    this.listen(this._menu, "click", this._onItemClick.bind(this))
    this.listen(this._menu, "mouseover", this._onItemHover.bind(this))

    this.listen(document, "click", this._onDocClick.bind(this))
    this.listen(document, "focusin", this._onDocFocusin.bind(this))

    this._observeItems()
    this._buildMenu()
    this._syncTrigger()

    /* `open` present at first render, or still set when the element is re-inserted. */
    this._syncOpen()
    return
  }

  onDisconnected() {
    this._stopPositioning()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "open" || name === "placement") {
      this._syncOpen()
    }
    if (name === "label" || name === "aria-label" || name === "icon-only" || name === "disabled") {
      this._syncTrigger()
    }
    return
  }

  /*
   * Text, accessible name and disabled state of the trigger. The name is the
   * `label` attribute, else the host's `aria-label`; an icon-only trigger
   * with neither is reported and falls back to a generic name. A menu with
   * no items leaves the trigger nothing to open.
   */
  _syncTrigger() {
    if (this._trigger === undefined || this._trigger === null) {
      return
    }

    const label = this.getAttribute("label") || ""
    const name = label.length > 0 ? label : (this.getAttribute("aria-label") || "")
    this._triggerLabel.textContent = label

    if (name.length > 0) {
      this._trigger.setAttribute("aria-label", name)
    } else if (this.hasAttribute("icon-only") === true) {
      if (this._missingLabelReported === false) {
        console.error("<mj-menu-button>: icon-only mode requires a label or aria-label attribute.")
        this._missingLabelReported = true
      }
      this._trigger.setAttribute("aria-label", t("mj.menuButton.defaultLabel"))
    } else {
      this._trigger.removeAttribute("aria-label")
    }

    const disabled = this.hasAttribute("disabled")
    this._trigger.disabled = disabled === true || this._itemData.length === 0
    if (disabled === true) {
      this._close(false)
    }
    return
  }

  /* ----- menu building ----- */

  /*
   * Rebuild the menu whenever the item children change, so items added
   * after the first render appear and an initially empty menu becomes usable.
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
        this._syncTrigger()
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
   * Build the row for one <mj-menu-item> and its record. Rows are created
   * with DOM APIs and textContent: item text, shortcut and variant are
   * application data, never markup.
   */
  _buildItem(el, index) {
    const type = el.getAttribute("type") || ""
    const checkable = type === "checkbox" || type === "radio"
    const shortcut = el.getAttribute("shortcut") || ""
    const variant = el.getAttribute("variant") || ""
    const disabled = el.hasAttribute("disabled")

    const label = el.textContent.replace(/\s+/g, " ").trim()

    const node = document.createElement("div")
    node.className = "menu-item"
    node.setAttribute("part", "menu-item")
    node.id = nextId("mj-mb-mi")
    node.dataset.index = String(index)
    node.tabIndex = -1

    if (type === "checkbox") {
      node.setAttribute("role", "menuitemcheckbox")
    } else if (type === "radio") {
      node.setAttribute("role", "menuitemradio")
    } else {
      node.setAttribute("role", "menuitem")
    }
    if (checkable === true) {
      node.setAttribute("aria-checked", el.hasAttribute("checked") === true ? "true" : "false")
      node.innerHTML = CHECK_ICON_MARKUP
    }
    if (disabled === true) {
      node.setAttribute("aria-disabled", "true")
    }
    if (variant.length > 0) {
      node.dataset.variant = variant
    }

    const labelEl = document.createElement("span")
    labelEl.className = "menu-item-label"
    labelEl.setAttribute("part", "menu-item-label")
    labelEl.textContent = label
    node.appendChild(labelEl)

    if (shortcut.length > 0) {
      const shortcutEl = document.createElement("span")
      shortcutEl.className = "shortcut"
      shortcutEl.setAttribute("part", "menu-item-shortcut")
      shortcutEl.setAttribute("aria-hidden", "true")
      shortcutEl.textContent = shortcut
      node.appendChild(shortcutEl)
    }

    const item = {
      id: node.id,
      label: label,
      value: el.hasAttribute("value") === true ? el.getAttribute("value") : label,
      disabled: disabled,
      type: type,
      index: index,
      el: el,
      node: node
    }
    return item
  }

  /*
   * Walk the host's children in order and mirror them into the menu:
   * items, separators and labelled groups. Other wrapper elements are
   * looked through; anything assigned to a named slot is left alone.
   */
  _buildMenu() {
    /* Keep the active item by element across the rebuild. */
    const activeBefore = this._itemData[this._focusedIndex]
    const activeEl = activeBefore !== undefined ? activeBefore.el : null

    this._menu.replaceChildren()
    this._itemData = []

    const visit = (parentEl, container) => {
      Array.from(parentEl.children).forEach((child) => {
        const tag = child.localName

        if (tag === "mj-menu-item") {
          const item = this._buildItem(child, this._itemData.length)
          this._itemData.push(item)
          container.appendChild(item.node)
        } else if (tag === "mj-menu-separator") {
          const separator = document.createElement("div")
          separator.className = "menu-separator"
          separator.setAttribute("part", "menu-separator")
          separator.setAttribute("role", "separator")
          container.appendChild(separator)
        } else if (tag === "mj-menu-group") {
          const groupNode = document.createElement("div")
          groupNode.className = "menu-group"
          groupNode.setAttribute("part", "menu-group")
          groupNode.setAttribute("role", "group")

          const groupLabel = child.getAttribute("label") || ""
          if (groupLabel.length > 0) {
            const labelNode = document.createElement("div")
            labelNode.className = "menu-group-label"
            labelNode.setAttribute("part", "menu-group-label")
            labelNode.id = nextId("mj-mb-grp")
            labelNode.textContent = groupLabel
            groupNode.setAttribute("aria-labelledby", labelNode.id)
            groupNode.appendChild(labelNode)
          }

          container.appendChild(groupNode)
          visit(child, groupNode)
        } else if (child.hasAttribute("slot") === false) {
          visit(child, container)
        }
      })
    }
    visit(this, this._menu)

    const restored = this._itemData.findIndex((item) => item.el === activeEl)
    this._focusedIndex = -1
    this._menu.removeAttribute("aria-activedescendant")
    if (this.hasAttribute("open") === true) {
      this._moveFocus(restored >= 0 ? restored : this._stepEnabled(-1, 1))
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
    if (this._trigger === undefined || this._trigger === null) {
      return
    }

    const isOpen = this.hasAttribute("open")
    this._trigger.setAttribute("aria-expanded", isOpen === true ? "true" : "false")
    this._stopPositioning()

    if (isOpen === true) {
      const placement = this.getAttribute("placement") || "bottom-start"
      this._disposePosition = autoPosition(this._popup, this._trigger, { placement: placement })

      const wanted = this._openFocus
      this._openFocus = null
      if (wanted === "last") {
        this._moveFocus(this._stepEnabled(this._itemData.length, -1))
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

  /* Open the menu with the first (default) or last item active. */
  _open(focusLast) {
    if (this.hasAttribute("disabled") === true || this.hasAttribute("open") === true) {
      return
    }
    const proceed = this.emit("mj-open", {}, { cancelable: true })
    if (proceed === false) {
      return
    }
    this._openFocus = focusLast === true ? "last" : "first"
    this.setAttribute("open", "")
    return
  }

  /* Close the menu; `restoreFocus` puts focus back on the trigger. */
  _close(restoreFocus) {
    if (this.hasAttribute("open") === false) {
      return
    }
    this.removeAttribute("open")
    this.emit("mj-close", {})
    if (restoreFocus === true && this._trigger !== undefined && this._trigger !== null) {
      this._trigger.focus()
    }
    return
  }

  /*
   * Index of the next enabled item from `from` in direction `delta`,
   * wrapping round; -1 when no item is enabled.
   */
  _stepEnabled(from, delta) {
    const count = this._itemData.length
    let found = -1

    for (let offset = 1; offset <= count; offset = offset + 1) {
      const index = (((from + delta * offset) % count) + count) % count
      if (this._itemData[index].disabled !== true) {
        found = index
        break
      }
    }

    return found
  }

  _moveFocus(index) {
    this._itemData.forEach((item) => item.node.classList.remove("focused"))
    const item = this._itemData[index]
    if (item !== undefined) {
      item.node.classList.add("focused")
      item.node.scrollIntoView({ block: "nearest" })
      this._menu.setAttribute("aria-activedescendant", item.id)
      this._focusedIndex = index
    }
    return
  }

  _clearFocus() {
    this._itemData.forEach((item) => item.node.classList.remove("focused"))
    this._menu.removeAttribute("aria-activedescendant")
    this._focusedIndex = -1
    return
  }

  /* ----- event handlers ----- */

  _onTriggerClick() {
    if (this.hasAttribute("open")) {
      this._close(true)
    } else {
      this._open(false)
    }
    return
  }

  _onTriggerKeydown(event) {
    if (this.hasAttribute("open") === true) {
      /* Open with focus still on the trigger: the menu keys work from here too. */
      this._onMenuKeydown(event)
      return
    }

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
    const count = this._itemData.length

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
      const item = this._itemData[this._focusedIndex]
      if (item !== undefined && item.disabled !== true) {
        this._activateItem(item)
      }
    } else if (event.key === "Escape") {
      /* Consumed here so an enclosing dialog does not close as well. */
      event.preventDefault()
      this._close(true)
    } else if (event.key === "Tab") {
      /* Tab leaves from the trigger, so it lands on the next control. */
      this._trigger.focus()
      this._close(false)
    }
    return
  }

  _itemFor(event) {
    const node = event.target instanceof Element ? event.target.closest(".menu-item") : null
    const item = node !== null ? this._itemData[parseInt(node.dataset.index, 10)] : undefined
    return item
  }

  _onItemClick(event) {
    const item = this._itemFor(event)
    if (item === undefined || item.disabled === true) {
      return
    }
    this._activateItem(item)
    return
  }

  _onItemHover(event) {
    const item = this._itemFor(event)
    if (item !== undefined && item.disabled !== true && item.index !== this._focusedIndex) {
      this._moveFocus(item.index)
    }
    return
  }

  /*
   * A checkable item records its state in the `checked` attribute of its
   * <mj-menu-item>: a checkbox flips, a radio becomes the only checked radio
   * among its siblings. Returns the new state, or null for a plain item.
   */
  _updateChecked(item) {
    let checked = null

    if (item.type === "checkbox") {
      checked = item.el.hasAttribute("checked") === false
      item.el.toggleAttribute("checked", checked)
    } else if (item.type === "radio") {
      checked = true
      const siblings = Array.from(item.el.parentNode.children)
      siblings.forEach((sibling) => {
        if (sibling.localName === "mj-menu-item" && sibling.getAttribute("type") === "radio") {
          sibling.toggleAttribute("checked", sibling === item.el)
        }
      })
    }

    return checked
  }

  _activateItem(item) {
    const checked = this._updateChecked(item)
    const detail = { item: item.el, value: item.value }
    if (checked !== null) {
      detail.checked = checked
    }

    this.emit("mj-select", detail)
    this._close(true)
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

  _onDocFocusin(event) {
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
      this._open(false)
    } else {
      this._close(false)
    }
    return
  }

  get menuItems() {
    return Array.from(this.querySelectorAll("mj-menu-item"))
  }

  /* The <mj-menu-item> that is currently the active descendant, or null. */
  get focusedItem() {
    const item = this._itemData[this._focusedIndex]
    const element = item !== undefined ? item.el : null
    return element
  }

  focus() {
    if (this._trigger !== undefined) {
      this._trigger.focus()
    }
    return
  }
}
