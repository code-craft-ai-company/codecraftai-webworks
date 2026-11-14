/*
 * mjmenubar.js
 *
 * <mj-menubar> -- application-level menubar implementing the WAI-ARIA APG
 * Menubar pattern: roving tabindex across the top-level items, dropdown menus
 * on activation, arrow-key navigation inside an open menu, and
 * hover-to-switch while any menu is open.
 *
 * The slotted children are a declarative menu DEFINITION, not content: each
 * child element is one top-level menu (its `label` attribute, or its own
 * text outside its entries, names it) and its descendants marked
 * `data-menu-item`, role="menuitem" or <li> are the entries of its dropdown.
 * <hr>, role="separator" and `data-menu-separator` descendants (an <li>
 * among them) become separators,
 * and a `disabled` attribute disables a menu or an entry. The definition is
 * never displayed; the component renders buttons and menus from it and
 * rebuilds them whenever the definition changes.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { autoPosition } from "../core/overlay.js";
import { t } from "../core/intl.js";

/* Descendants of a top-level definition that become dropdown entries or separators. */
const ENTRY_SELECTOR = "[role='menuitem'], [data-menu-item], li";
const SEPARATOR_SELECTOR = "hr, [role='separator'], [data-menu-separator]";

const STYLES = `
:host {
  display: block;
}

.menubar-root {
  display: flex;
  align-items: center;
  gap: 0;
  min-block-size: var(--mj-menubar-height, var(--mj-control-height-md));
  padding: 0 var(--mj-space-2);
  background: var(--mj-menubar-bg, var(--mj-surface));
  border-block-end: 1px solid var(--mj-menubar-border, var(--mj-border));
  user-select: none;
}

:host([disabled]) .menubar-root {
  opacity: 0.55;
}

.menubar-entry {
  display: flex;
  min-inline-size: 0;
}

.menu-item-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--mj-space-1);
  padding: var(--mj-menubar-item-padding, 0 var(--mj-space-3));
  min-block-size: var(--mj-menubar-height, var(--mj-control-height-md));
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

:host([compact]) .menubar-root,
:host([compact]) .menu-item-btn {
  min-block-size: var(--mj-menubar-height, var(--mj-control-height-sm));
}

:host([compact]) .menu-item-btn {
  padding: var(--mj-menubar-item-padding, 0 var(--mj-space-2));
}

.menu-item-btn:hover {
  background: var(--mj-menubar-item-hover-bg, var(--mj-bg-muted));
}

.menu-item-btn[aria-expanded="true"] {
  background: var(--mj-menubar-item-active-bg, var(--mj-bg-muted));
}

.menu-item-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: calc(-1 * var(--mj-focus-ring-width));
}

.menu-item-btn[aria-disabled="true"],
.menu-item-btn:disabled {
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
  min-inline-size: 160px;
  max-block-size: calc(100vh - var(--mj-space-4));
  overflow-y: auto;
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
  inline-size: 100%;
  text-align: start;
  white-space: nowrap;
}

.menu-dropdown-item:hover,
.menu-dropdown-item:focus {
  background: var(--mj-bg-muted);
}

.menu-dropdown-item:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: calc(-1 * var(--mj-focus-ring-width));
}

.menu-dropdown-item[aria-disabled="true"] {
  opacity: 0.45;
  cursor: not-allowed;
}

.menu-separator {
  block-size: 1px;
  margin: var(--mj-space-1) 0;
  background: var(--mj-border);
}

.empty-menu {
  padding: var(--mj-space-2) var(--mj-space-4);
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text-muted);
}
`;

/* The visible name of an entry definition: its `label`, else its text. */
function definitionLabel(element) {
  const explicit = element.getAttribute("label")
  const label = explicit !== null && explicit.length > 0 ? explicit : element.textContent.trim()
  return label
}

/*
 * The visible name of a top-level definition: its `label`, else its own
 * text -- the text outside its entries and separators, so
 * `<li>File <ul><li>New</li></ul></li>` is named "File", not "File New".
 */
function menuLabel(definition) {
  let label = ""

  const explicit = definition.getAttribute("label")
  if (explicit !== null && explicit.length > 0) {
    label = explicit
  } else {
    const parts = []
    const nodes = definition.childNodes
    for (let index = 0; index < nodes.length; index = index + 1) {
      const node = nodes[index]
      if (node.nodeType === Node.TEXT_NODE) {
        parts.push(node.textContent)
      } else if (node.nodeType === Node.ELEMENT_NODE) {
        const isEntry = node.matches(`${ENTRY_SELECTOR}, ${SEPARATOR_SELECTOR}`) === true
        const holdsEntries = node.querySelector(`${ENTRY_SELECTOR}, ${SEPARATOR_SELECTOR}`) !== null
        if (isEntry === false && holdsEntries === false) {
          parts.push(node.textContent)
        }
      }
    }
    label = parts.join(" ").replace(/\s+/g, " ").trim()
  }

  return label
}

export class MjMenubar extends MjElement {
  static tagName = "mj-menubar";
  static styles = STYLES;
  static watched = ["label", "compact", "disabled", "active-item"];

  constructor() {
    super()
    this._root = null
    this._slot = null

    /*
     * One record per top-level menu:
     * { definition, label, key, disabled, button, menu, items }, where items
     * is a list of { definition, label, value, disabled, button }.
     */
    this._entries = []

    /* Index of the top-level item that holds the bar's single tab stop. */
    this._activeIndex = 0
    this._openIndex = -1
    this._positionDispose = null

    this._definitionObserver = null
    this._rebuildQueued = false

    /* True while the component itself writes `active-item`. */
    this._reflectingActiveItem = false
  }

  render() {
    const markup = `
      <div class="menubar-root" role="menubar" part="root"></div>
      <div hidden><slot></slot></div>
    `
    return markup
  }

  afterRender() {
    this._root = this.$(".menubar-root")
    this._slot = this.$("slot")
    this._entries = []
    this._openIndex = -1
    this._positionDispose = null
    this._rebuildQueued = false

    this._syncLabel()

    this.listen(this._slot, "slotchange", this._onSlotChange.bind(this))
    this.listen(this._root, "click", this._onClick.bind(this))
    this.listen(this._root, "mousedown", this._onMouseDown.bind(this))
    this.listen(this._root, "mouseover", this._onMouseOver.bind(this))
    this.listen(this._root, "keydown", this._onKeydown.bind(this))
    this.listen(this._root, "focusin", this._onFocusIn.bind(this))
    this.listen(this._root, "focusout", this._onFocusOut.bind(this))
    this.listen(document, "pointerdown", this._onDocumentPointerDown.bind(this))

    /* Edits inside a definition (new entries, renamed labels) do not fire slotchange. */
    if (typeof MutationObserver === "function") {
      this._definitionObserver = new MutationObserver(this._onDefinitionMutation.bind(this))
      this._definitionObserver.observe(this, {
        childList: true,
        subtree: true,
        characterData: true,
        attributes: true,
        attributeFilter: ["label", "value", "disabled", "data-menu-item", "data-menu-separator", "role"]
      })
    }

    this.onTeardown(() => {
      if (this._definitionObserver !== null) {
        this._definitionObserver.disconnect()
        this._definitionObserver = null
      }
      this._stopPositioning()
    })

    this._rebuild()
    return
  }

  _syncLabel() {
    if (this._root === undefined || this._root === null) {
      return
    }
    const label = this.getAttribute("label") || t("mj.menubar.label")
    this._root.setAttribute("aria-label", label)
    return
  }

  /* ----- building the bar from the slotted definition ----- */

  /* Rebuild when the set of top-level definitions is not the one the bar was built from. */
  _onSlotChange() {
    const definitions = this._slot.assignedElements({ flatten: true })

    let unchanged = definitions.length === this._entries.length
    for (let index = 0; index < definitions.length && unchanged === true; index = index + 1) {
      if (definitions[index] !== this._entries[index].definition) {
        unchanged = false
      }
    }

    if (unchanged === false) {
      this._queueRebuild()
    }
    return
  }

  /* Rebuild after an edit inside the definition; the host's own attributes are not part of it. */
  _onDefinitionMutation(records) {
    let relevant = false
    for (let index = 0; index < records.length && relevant === false; index = index + 1) {
      const record = records[index]
      if (record.type !== "attributes" || record.target !== this) {
        relevant = true
      }
    }

    if (relevant === true) {
      this._queueRebuild()
    }
    return
  }

  /* Coalesce a burst of definition changes into one rebuild. */
  _queueRebuild() {
    if (this._rebuildQueued === true) {
      return
    }
    this._rebuildQueued = true
    queueMicrotask(() => {
      if (this._rebuildQueued === true) {
        this._rebuildQueued = false
        if (this._root !== null && this.isConnected === true) {
          this._rebuild()
        }
      }
    })
    return
  }

  _rebuild() {
    const hadFocus = this.shadowRoot.activeElement !== null

    /* A menu that is open is opened again afterwards, if its definition is still there. */
    let reopenKey = null
    if (this._openIndex >= 0) {
      reopenKey = this._entries[this._openIndex].key
      this._closeMenu(false)
    }

    /* The buttons and menus of the previous build go away with their container. */
    this._root.textContent = ""
    this._entries = []

    const barDisabled = this.hasAttribute("disabled")
    const definitions = this._slot.assignedElements({ flatten: true })

    for (let index = 0; index < definitions.length; index = index + 1) {
      const entry = this._buildEntry(definitions[index], index, barDisabled)
      this._entries.push(entry)
      this._root.appendChild(entry.wrapper)
    }

    if (barDisabled === true) {
      this._root.setAttribute("aria-disabled", "true")
    } else {
      this._root.removeAttribute("aria-disabled")
    }

    if (this._activeIndex >= this._entries.length) {
      this._activeIndex = this._entries.length > 0 ? this._entries.length - 1 : 0
    }
    this._syncTabStops()

    if (hadFocus === true && barDisabled === false && this._entries.length > 0) {
      this._entries[this._activeIndex].button.focus()
    }

    if (reopenKey !== null) {
      this._openByKey(reopenKey)
    } else {
      this._openFromActiveItemAttribute()
    }
    return
  }

  _buildEntry(definition, index, barDisabled) {
    const label = menuLabel(definition)
    const disabled = definition.hasAttribute("disabled")

    const wrapper = document.createElement("div")
    wrapper.className = "menubar-entry"
    wrapper.setAttribute("role", "none")

    const menu = document.createElement("ul")
    menu.className = "menu-dropdown"
    menu.setAttribute("role", "menu")
    menu.setAttribute("part", "menu")
    menu.setAttribute("aria-label", label)
    menu.setAttribute("data-entry-index", String(index))
    menu.hidden = true
    menu.id = nextId("mj-mb-menu")

    const button = document.createElement("button")
    button.type = "button"
    button.className = "menu-item-btn"
    button.setAttribute("part", "item")
    button.setAttribute("role", "menuitem")
    button.setAttribute("aria-haspopup", "menu")
    button.setAttribute("aria-expanded", "false")
    button.setAttribute("aria-controls", menu.id)
    button.setAttribute("data-mj-menubar-btn", "")
    button.setAttribute("data-entry-index", String(index))
    button.textContent = label
    if (barDisabled === true) {
      /* A disabled bar is out of the tab order altogether. */
      button.disabled = true
    } else if (disabled === true) {
      /* A single disabled menu stays reachable so it can be read, but does not open. */
      button.setAttribute("aria-disabled", "true")
    }

    const items = this._buildMenuItems(definition, menu)

    wrapper.appendChild(button)
    wrapper.appendChild(menu)

    const key = definition.id || definition.getAttribute("value") || label
    const entry = {
      definition: definition,
      label: label,
      key: key,
      disabled: disabled === true || barDisabled === true,
      wrapper: wrapper,
      button: button,
      menu: menu,
      items: items
    }
    return entry
  }

  _buildMenuItems(definition, menu) {
    const items = []
    const sources = definition.querySelectorAll(`${ENTRY_SELECTOR}, ${SEPARATOR_SELECTOR}`)

    for (let index = 0; index < sources.length; index = index + 1) {
      const source = sources[index]
      const row = document.createElement("li")

      /* Separators first: an <li role="separator"> also matches the entry selector (li). */
      if (source.matches(SEPARATOR_SELECTOR) === false) {
        const label = definitionLabel(source)
        const value = source.getAttribute("value") || label
        const disabled = source.hasAttribute("disabled")

        const button = document.createElement("button")
        button.type = "button"
        button.className = "menu-dropdown-item"
        button.setAttribute("role", "menuitem")
        button.setAttribute("data-item-index", String(items.length))
        button.setAttribute("data-value", value)
        button.tabIndex = -1
        button.textContent = label
        if (disabled === true) {
          button.setAttribute("aria-disabled", "true")
        }

        row.setAttribute("role", "none")
        row.appendChild(button)
        items.push({ definition: source, label: label, value: value, disabled: disabled, button: button })
      } else {
        row.className = "menu-separator"
        row.setAttribute("role", "separator")
      }

      menu.appendChild(row)
    }

    if (items.length === 0) {
      const empty = document.createElement("li")
      empty.className = "empty-menu"
      empty.setAttribute("role", "none")
      empty.textContent = t("mj.menubar.noItems")
      menu.appendChild(empty)
    }

    return items
  }

  /* Exactly one top-level item is in the tab order. */
  _syncTabStops() {
    for (let index = 0; index < this._entries.length; index = index + 1) {
      this._entries[index].button.tabIndex = index === this._activeIndex ? 0 : -1
    }
    return
  }

  _focusTopLevel(index) {
    if (index >= 0 && index < this._entries.length) {
      this._activeIndex = index
      this._syncTabStops()
      this._entries[index].button.focus()
    }
    return
  }

  /* ----- opening and closing ----- */

  _openMenu(index) {
    const entry = this._entries[index]
    if (entry === undefined || entry.disabled === true || this._openIndex === index) {
      return
    }

    /* Only one menu is open at a time. */
    if (this._openIndex >= 0) {
      this._closeMenu(false)
    }

    this._openIndex = index
    entry.button.setAttribute("aria-expanded", "true")
    entry.menu.hidden = false

    /*
     * The shared overlay engine keeps the menu under its button while the
     * page scrolls or resizes and flips / shifts it at the viewport edges.
     * It aligns to the inline-start edge of the button in either direction.
     */
    const rightToLeft = getComputedStyle(this).direction === "rtl"
    this._positionDispose = autoPosition(entry.menu, entry.button, {
      placement: rightToLeft === true ? "bottom-end" : "bottom-start",
      offset: 0,
      padding: 4
    })

    this._reflectActiveItem(entry.key)
    this.emit("mj-menubar-open", { item: entry.definition, menuId: entry.menu.id })
    return
  }

  _stopPositioning() {
    if (this._positionDispose !== null) {
      this._positionDispose()
      this._positionDispose = null
    }
    return
  }

  /* Close the open menu; `focusButton` returns focus to its top-level item. */
  _closeMenu(focusButton) {
    const index = this._openIndex
    const entry = this._entries[index]
    if (entry === undefined) {
      this._openIndex = -1
      return
    }

    this._stopPositioning()
    this._openIndex = -1
    entry.button.setAttribute("aria-expanded", "false")
    entry.menu.hidden = true

    if (focusButton === true) {
      this._focusTopLevel(index)
    }

    this._reflectActiveItem(null)
    this.emit("mj-menubar-close", { item: entry.definition, menuId: entry.menu.id })
    return
  }

  /* Mirror the open menu in the `active-item` attribute. */
  _reflectActiveItem(key) {
    this._reflectingActiveItem = true
    try {
      if (key === null || key.length === 0) {
        this.removeAttribute("active-item")
      } else {
        this.setAttribute("active-item", key)
      }
    } finally {
      this._reflectingActiveItem = false
    }
    return
  }

  /* An author set `active-item`: open the menu it names (or close, when empty). */
  _openFromActiveItemAttribute() {
    const wanted = this.getAttribute("active-item")

    if (wanted === null || wanted.length === 0) {
      if (this._openIndex >= 0) {
        this._closeMenu(false)
      }
      return
    }

    this._openByKey(wanted)
    return
  }

  /* Open the menu whose key (id, value or label of its definition) is `key`. */
  _openByKey(key) {
    let opened = false
    for (let index = 0; index < this._entries.length && opened === false; index = index + 1) {
      if (this._entries[index].key === key) {
        this._openMenu(index)
        opened = true
      }
    }
    return
  }

  /* Focus an entry of the open menu; `position` is "first", "last" or an index. */
  _focusMenuItem(position) {
    const entry = this._entries[this._openIndex]
    if (entry === undefined || entry.items.length === 0) {
      return
    }

    let index = 0
    if (position === "last") {
      index = entry.items.length - 1
    } else if (position !== "first") {
      index = position
    }
    entry.items[index].button.focus()
    return
  }

  /* ----- pointer ----- */

  _entryIndexOf(node) {
    let index = -1
    if (node instanceof Element) {
      const holder = node.closest("[data-entry-index]")
      if (holder !== null) {
        index = parseInt(holder.getAttribute("data-entry-index"), 10)
      }
    }
    return index
  }

  _onClick(event) {
    const target = event.target
    if (!(target instanceof Element) || this.hasAttribute("disabled") === true) {
      return
    }

    const topLevel = target.closest(".menu-item-btn")
    const menuItem = target.closest(".menu-dropdown-item")

    if (topLevel !== null) {
      const index = this._entryIndexOf(topLevel)
      this._activeIndex = index
      this._syncTabStops()
      if (this._openIndex === index) {
        this._closeMenu(false)
      } else {
        this._openMenu(index)
      }
    } else if (menuItem !== null) {
      this._selectMenuItem(this._entryIndexOf(menuItem), parseInt(menuItem.getAttribute("data-item-index"), 10))
    }
    return
  }

  /*
   * Pressing the pointer inside a menu must not move focus out of the
   * component (some browsers do not focus a clicked button), which would
   * close the menu before the click arrives.
   */
  _onMouseDown(event) {
    const target = event.target
    if (target instanceof Element && target.closest(".menu-dropdown") !== null) {
      event.preventDefault()
    }
    return
  }

  /* Hover-to-switch: with a menu open, pointing at another top-level item opens its menu. */
  _onMouseOver(event) {
    const target = event.target
    if (!(target instanceof Element) || this._openIndex < 0) {
      return
    }
    const topLevel = target.closest(".menu-item-btn")
    if (topLevel !== null) {
      const index = this._entryIndexOf(topLevel)
      if (index !== this._openIndex && this._entries[index] !== undefined && this._entries[index].disabled === false) {
        this._openMenu(index)
      }
    }
    return
  }

  _onDocumentPointerDown(event) {
    if (this._openIndex >= 0 && event.composedPath().indexOf(this) < 0) {
      this._closeMenu(false)
    }
    return
  }

  _selectMenuItem(entryIndex, itemIndex) {
    const entry = this._entries[entryIndex]
    if (entry === undefined) {
      return
    }
    const item = entry.items[itemIndex]
    if (item === undefined || item.disabled === true) {
      return
    }

    this._closeMenu(true)
    this.emit("mj-menubar-select", {
      item: entry.definition,
      menuItem: item.definition,
      value: item.value,
      path: [entry.label, item.label]
    })
    return
  }

  /* ----- focus ----- */

  /* Keep the roving tab stop on the top-level item that received focus (pointer included). */
  _onFocusIn(event) {
    const target = event.target
    if (target instanceof Element && target.classList.contains("menu-item-btn") === true) {
      const index = this._entryIndexOf(target)
      if (index >= 0 && index !== this._activeIndex) {
        this._activeIndex = index
        this._syncTabStops()
      }
    }
    return
  }

  /* Focus left the component (Tab, or a click elsewhere): close the open menu. */
  _onFocusOut(event) {
    const next = event.relatedTarget
    const staysInside = next instanceof Node && this.shadowRoot.contains(next) === true
    if (staysInside === false && this._openIndex >= 0) {
      this._closeMenu(false)
    }
    return
  }

  /* ----- keyboard ----- */

  /* The top-level index `delta` steps away from `index`, wrapping around. */
  _wrapIndex(index, delta, count) {
    const wrapped = (index + delta + count) % count
    return wrapped
  }

  /*
   * The index of the next label after `fromIndex` (wrapping) that starts
   * with `character`, or -1.
   */
  _typeaheadIndex(labels, fromIndex, character) {
    let found = -1
    const wanted = character.toLocaleLowerCase()
    for (let offset = 1; offset <= labels.length && found < 0; offset = offset + 1) {
      const index = (fromIndex + offset) % labels.length
      if (labels[index].toLocaleLowerCase().startsWith(wanted) === true) {
        found = index
      }
    }
    return found
  }

  _isPrintable(event) {
    const printable =
      event.key.length === 1 && event.key !== " " &&
      event.ctrlKey === false && event.altKey === false && event.metaKey === false
    return printable
  }

  _onKeydown(event) {
    const target = event.target
    if (!(target instanceof Element) || this._entries.length === 0 || this.hasAttribute("disabled") === true) {
      return
    }

    /* In a right-to-left bar the next top-level item is to the left. */
    const rightToLeft = getComputedStyle(this).direction === "rtl"
    let inlineStep = 0
    if (event.key === "ArrowRight") {
      inlineStep = rightToLeft === true ? -1 : 1
    } else if (event.key === "ArrowLeft") {
      inlineStep = rightToLeft === true ? 1 : -1
    }

    if (target.classList.contains("menu-item-btn") === true) {
      this._onTopLevelKeydown(event, this._entryIndexOf(target), inlineStep)
    } else if (target.classList.contains("menu-dropdown-item") === true) {
      this._onMenuItemKeydown(event, this._entryIndexOf(target), inlineStep)
    }
    return
  }

  _onTopLevelKeydown(event, index, inlineStep) {
    const count = this._entries.length
    const menuWasOpen = this._openIndex >= 0
    let handled = true
    let moveTo = -1

    if (inlineStep !== 0) {
      moveTo = this._wrapIndex(index, inlineStep, count)
    } else if (event.key === "Home") {
      moveTo = 0
    } else if (event.key === "End") {
      moveTo = count - 1
    } else if (event.key === "ArrowDown" || event.key === "Enter" || event.key === " ") {
      this._openMenu(index)
      if (this._openIndex === index) {
        this._focusMenuItem("first")
      }
    } else if (event.key === "ArrowUp") {
      this._openMenu(index)
      if (this._openIndex === index) {
        this._focusMenuItem("last")
      }
    } else if (event.key === "Escape") {
      if (menuWasOpen === true) {
        this._closeMenu(true)
      } else {
        handled = false
      }
    } else if (this._isPrintable(event) === true) {
      const labels = this._entries.map((entry) => entry.label)
      moveTo = this._typeaheadIndex(labels, index, event.key)
      handled = moveTo >= 0
    } else {
      handled = false
    }

    if (moveTo >= 0) {
      /* Moving along the bar with a menu open carries the open state along. */
      this._focusTopLevel(moveTo)
      if (menuWasOpen === true) {
        this._closeMenu(false)
        this._openMenu(moveTo)
      }
    }

    if (handled === true) {
      event.preventDefault()
    }
    return
  }

  _onMenuItemKeydown(event, entryIndex, inlineStep) {
    const entry = this._entries[entryIndex]
    if (entry === undefined) {
      return
    }

    const itemCount = entry.items.length
    const itemIndex = parseInt(event.target.getAttribute("data-item-index"), 10)
    let handled = true

    if (event.key === "ArrowDown") {
      this._focusMenuItem(this._wrapIndex(itemIndex, 1, itemCount))
    } else if (event.key === "ArrowUp") {
      this._focusMenuItem(this._wrapIndex(itemIndex, -1, itemCount))
    } else if (event.key === "Home") {
      this._focusMenuItem("first")
    } else if (event.key === "End") {
      this._focusMenuItem("last")
    } else if (event.key === "Escape") {
      this._closeMenu(true)
    } else if (inlineStep !== 0) {
      /* Left / Right in a menu: go to the neighbouring menu, skipping disabled ones. */
      const count = this._entries.length
      let neighbour = this._wrapIndex(entryIndex, inlineStep, count)
      let guard = 0
      while (this._entries[neighbour].disabled === true && guard < count) {
        neighbour = this._wrapIndex(neighbour, inlineStep, count)
        guard = guard + 1
      }
      this._focusTopLevel(neighbour)
      this._closeMenu(false)
      this._openMenu(neighbour)
      if (this._openIndex === neighbour) {
        this._focusMenuItem("first")
      }
    } else if (event.key === "Enter" || event.key === " ") {
      this._selectMenuItem(entryIndex, itemIndex)
    } else if (this._isPrintable(event) === true) {
      const labels = entry.items.map((item) => item.label)
      const match = this._typeaheadIndex(labels, itemIndex, event.key)
      if (match >= 0) {
        this._focusMenuItem(match)
      } else {
        handled = false
      }
    } else {
      handled = false
    }

    if (handled === true) {
      event.preventDefault()
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._root === undefined || this._root === null) {
      return
    }

    if (name === "label") {
      this._syncLabel()
    } else if (name === "disabled") {
      this._rebuild()
    } else if (name === "active-item" && this._reflectingActiveItem === false) {
      this._openFromActiveItemAttribute()
    }
    return
  }

  /* The top-level definition elements, in order. */
  get items() {
    const found = this._entries.map((entry) => entry.definition)
    return found
  }

  /* The open dropdown (role="menu") element, or null. */
  get openMenu() {
    const entry = this._entries[this._openIndex]
    const menu = entry !== undefined ? entry.menu : null
    return menu
  }
}
