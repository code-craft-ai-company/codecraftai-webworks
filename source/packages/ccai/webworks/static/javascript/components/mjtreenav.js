/*
 * mjtreenav.js
 *
 * <mj-tree-nav> -- hierarchical navigation tree implementing WAI-ARIA tree/treeitem.
 * Supports expand/collapse, auto-expand of current item's ancestors, and persist-state.
 *
 * The tree items are the author's own <li> elements in the light DOM. Two
 * things follow from that:
 *   - Their styles cannot live in the shadow stylesheet (it does not reach
 *     light-DOM descendants), so the item rules are adopted into the document
 *     (or the enclosing shadow root), scoped to `mj-tree-nav`.
 *   - An ID reference such as aria-activedescendant cannot point from the
 *     shadow tree element to them, so keyboard focus is real DOM focus that
 *     roves over the items (roving tabindex).
 *
 * WAI-ARIA: nav landmark; ul role=tree; li role=treeitem; aria-expanded; aria-current="page".
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";

const STYLES = `
:host { display: block; }

nav { font-size: var(--mj-tree-nav-font-size, var(--mj-font-size-sm)); }

.tree {
  list-style: none;
  margin: 0; padding: 0;
  outline: none;
}
`;

/* Rules for the light-DOM items; adopted once per document / shadow root. */
const LIGHT_STYLES = `
mj-tree-nav li[role="treeitem"] {
  list-style: none;
  outline: none;
}

mj-tree-nav .item-row {
  display: flex;
  align-items: center;
  height: var(--mj-tree-nav-item-height, 36px);
  padding-inline-end: var(--mj-space-2);
  cursor: pointer;
  border-radius: var(--mj-radius-sm);
  transition: background var(--mj-motion-fast) var(--mj-motion-ease);
  position: relative;
}
mj-tree-nav[compact] .item-row { height: var(--mj-tree-nav-item-height-compact, 28px); }
mj-tree-nav .item-row:hover { background: var(--mj-tree-nav-bg-hover, var(--mj-bg-muted)); }

/* Leaf rows keep the space a toggle would take, so labels line up. */
mj-tree-nav li[role="treeitem"]:not([aria-expanded]) > .item-row {
  padding-inline-start: var(--mj-tree-nav-toggle-size, 20px);
}

mj-tree-nav li[role="treeitem"]:focus-visible > .item-row {
  background: var(--mj-tree-nav-bg-hover, var(--mj-bg-muted));
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: calc(0px - var(--mj-focus-ring-width));
}

mj-tree-nav li[role="treeitem"][aria-current="page"] > .item-row {
  background: var(--mj-tree-nav-bg-active, var(--mj-bg-muted));
  box-shadow: inset var(--mj-tree-nav-active-border-width, 2px) 0 0 var(--mj-tree-nav-active-border-color, var(--mj-accent));
}
mj-tree-nav:dir(rtl) li[role="treeitem"][aria-current="page"] > .item-row {
  box-shadow: inset calc(0px - var(--mj-tree-nav-active-border-width, 2px)) 0 0 var(--mj-tree-nav-active-border-color, var(--mj-accent));
}
mj-tree-nav li[role="treeitem"][aria-current="page"] > .item-row .item-link {
  color: var(--mj-tree-nav-color-active, var(--mj-accent));
  font-weight: var(--mj-font-weight-medium);
}

mj-tree-nav .toggle-btn {
  display: flex; align-items: center; justify-content: center;
  width: var(--mj-tree-nav-toggle-size, 20px);
  height: var(--mj-tree-nav-toggle-size, 20px);
  flex-shrink: 0;
  background: none; border: none; cursor: pointer;
  color: var(--mj-text-muted);
  padding: 0;
  border-radius: var(--mj-radius-sm);
}
mj-tree-nav .toggle-btn svg {
  transition: transform var(--mj-tree-nav-transition-duration, var(--mj-motion-fast)) var(--mj-motion-ease);
}
mj-tree-nav:dir(rtl) .toggle-btn svg { transform: scaleX(-1); }
mj-tree-nav li[role="treeitem"][aria-expanded="true"] > .item-row .toggle-btn svg { transform: rotate(90deg); }

mj-tree-nav .item-link {
  flex: 1;
  display: flex; align-items: center;
  height: 100%;
  gap: var(--mj-space-2);
  text-decoration: none;
  color: var(--mj-text);
  min-width: 0;
  padding-inline-start: var(--mj-space-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
mj-tree-nav .item-link[aria-disabled="true"] { opacity: 0.5; cursor: not-allowed; }

mj-tree-nav .child-tree {
  list-style: none;
  margin: 0; padding: 0;
  padding-inline-start: var(--mj-tree-nav-indent, var(--mj-space-5));
}
mj-tree-nav li[role="treeitem"][aria-expanded="false"] > .child-tree { display: none; }
mj-tree-nav li[role="treeitem"]:not([aria-expanded]) > .child-tree { display: none; }
`;

const TOGGLE_ICON = `<svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="3 2 9 6 3 10"/></svg>`;

let lightSheet = null;

/*
 * Adopt the light-DOM item rules into the tree a component lives in (the
 * document, or the shadow root of an enclosing component). Idempotent.
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

export class MjTreeNav extends MjElement {
  static tagName = "mj-tree-nav";
  static styles = STYLES;
  static watched = ["nav-label", "current", "parent-toggle", "compact", "auto-expand", "persist-state", "persist-key"];

  constructor() {
    super()
    this._treeId = nextId("mj-tree")

    /* The item holding the roving tab stop (and focus, while the tree is focused). */
    this._activeItem = null

    /* The item this component marked aria-current="page" from `current`. */
    this._currentItem = null

    /* Visible items in document order (collapsed branches excluded). */
    this._flatItems = []

    /* Items whose id was generated here; such ids are not stable across pages. */
    this._generatedIds = new WeakSet()

    this._stateRestored = false
    this._mutationObserver = null
  }

  render() {
    const markup = html`
      <nav>
        <ul class="tree" part="tree" role="tree" id="${this._treeId}">
          <slot></slot>
        </ul>
      </nav>
    `
    return markup
  }

  afterRender() {
    this._nav = this.$("nav")
    this._tree = this.$(".tree")
    this._slot = this.shadowRoot.querySelector("slot")

    this.listen(this._tree, "keydown", this._onKeydown.bind(this))
    this.listen(this._tree, "click", this._onClick.bind(this))
    this.listen(this._tree, "focusin", this._onFocusIn.bind(this))

    /*
     * Items can be added anywhere in the light-DOM tree at any time (lazy
     * branches); every such change reprocesses the tree. The component's own
     * edits are discarded with takeRecords() so a build never re-triggers.
     */
    this._mutationObserver = new MutationObserver(() => {
      this._buildTree()
    })
    this._mutationObserver.observe(this, { childList: true, subtree: true })
    this.onTeardown(() => {
      this._mutationObserver.disconnect()
      this._mutationObserver = null
      this._stateRestored = false
    })

    this._syncLabel()
    this._buildTree()
    return
  }

  onConnected() {
    adoptLightStyles(this.getRootNode())
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._tree === undefined || this._tree === null) {
      return
    }

    if (name === "current" || name === "auto-expand") {
      this._applyCurrent()
      this._refreshFlatItems()
      this._discardOwnMutations()
    } else if (name === "nav-label") {
      this._syncLabel()
    }
    return
  }

  _syncLabel() {
    let navLabel = this.getAttribute("nav-label")
    if (navLabel === null || navLabel.length === 0) {
      navLabel = t("mj.treeNav.navLabel")
    }
    this._nav.setAttribute("aria-label", navLabel)
    this._tree.setAttribute("aria-label", navLabel)
    return
  }

  _isEnabled(name) {
    const enabled = this.hasAttribute(name) === true && this.getAttribute(name) !== "false"
    return enabled
  }

  _discardOwnMutations() {
    if (this._mutationObserver !== null) {
      this._mutationObserver.takeRecords()
    }
    return
  }

  /* The top-level <li> items. */
  _rootItems() {
    const assigned = this._slot.assignedElements({ flatten: true })
    const items = assigned.filter((element) => element.tagName === "LI")
    return items
  }

  /* Every treeitem of this tree, in document order. */
  _allItems() {
    const items = []
    const walk = (list) => {
      for (let index = 0; index < list.length; index = index + 1) {
        const li = list[index]
        items.push(li)
        const childList = this._childListOf(li)
        if (childList !== null) {
          walk(Array.from(childList.children).filter((child) => child.tagName === "LI"))
        }
      }
    }
    walk(this._rootItems())
    return items
  }

  _childListOf(li) {
    const childList = li.querySelector(":scope > ul, :scope > ol")
    return childList
  }

  _linkOf(li) {
    const link = li.querySelector(":scope > .item-row a, :scope > a")
    return link
  }

  _buildTree() {
    const rootItems = this._rootItems()
    this._processItems(rootItems, 1)

    /* Saved state first, so auto-expand of the current item has the last word. */
    if (this._stateRestored === false) {
      this._stateRestored = true
      this._restorePersistedState()
    }

    this._applyCurrent()
    this._refreshFlatItems()
    this._discardOwnMutations()
    return
  }

  /* Wire one level of items (and, recursively, their children). Idempotent. */
  _processItems(items, level) {
    for (let index = 0; index < items.length; index = index + 1) {
      const li = items[index]

      if (li.id === "") {
        li.id = nextId("mj-treeitem")
        this._generatedIds.add(li)
      }

      li.setAttribute("role", "treeitem")
      li.setAttribute("aria-level", String(level))
      li.setAttribute("aria-setsize", String(items.length))
      li.setAttribute("aria-posinset", String(index + 1))
      if (li.hasAttribute("tabindex") === false) {
        li.setAttribute("tabindex", "-1")
      }

      const row = this._ensureRow(li)
      const childList = this._childListOf(li)

      if (childList !== null) {
        childList.setAttribute("role", "group")
        childList.classList.add("child-tree")
        if (li.getAttribute("aria-expanded") === null) {
          li.setAttribute("aria-expanded", "false")
        }
        this._ensureToggle(row)

        const children = Array.from(childList.children).filter((child) => child.tagName === "LI")
        this._processItems(children, level + 1)
      } else {
        /* A leaf (or a parent that lost its children) has no toggle and no expanded state. */
        const staleToggle = row.querySelector(":scope > .toggle-btn")
        if (staleToggle !== null) {
          staleToggle.remove()
        }
        li.removeAttribute("aria-expanded")
      }

      const link = this._linkOf(li)
      if (link !== null) {
        link.classList.add("item-link")
        link.setAttribute("tabindex", "-1")
      }
    }
    return
  }

  /* Wrap an item's own content (everything except its child list) in a row. */
  _ensureRow(li) {
    let row = li.querySelector(":scope > .item-row")
    if (row === null) {
      row = document.createElement("div")
      row.className = "item-row"
      li.insertBefore(row, li.firstChild)
    }

    const children = Array.from(li.childNodes)
    for (let index = 0; index < children.length; index = index + 1) {
      const child = children[index]
      const isChildTree = child.nodeType === Node.ELEMENT_NODE &&
        (child.tagName === "UL" || child.tagName === "OL")
      if (child !== row && isChildTree === false) {
        row.appendChild(child)
      }
    }
    return row
  }

  _ensureToggle(row) {
    if (row.querySelector(":scope > .toggle-btn") !== null) {
      return
    }
    /* Decorative for assistive technology: aria-expanded on the item carries the state. */
    const btn = document.createElement("button")
    btn.className = "toggle-btn"
    btn.setAttribute("type", "button")
    btn.setAttribute("tabindex", "-1")
    btn.setAttribute("aria-hidden", "true")
    btn.innerHTML = TOGGLE_ICON
    row.insertBefore(btn, row.firstChild)
    return
  }

  _collectFlatItems() {
    const flat = []
    const walk = (list) => {
      for (let index = 0; index < list.length; index = index + 1) {
        const li = list[index]
        flat.push(li)
        if (li.getAttribute("aria-expanded") === "true") {
          const childList = this._childListOf(li)
          if (childList !== null) {
            walk(Array.from(childList.children).filter((child) => child.tagName === "LI"))
          }
        }
      }
    }
    walk(this._rootItems())
    return flat
  }

  /*
   * Recompute the visible items and keep exactly one of them in the tab
   * order: the active item while it is visible, else its nearest visible
   * ancestor, else the current page, else the first item.
   */
  _refreshFlatItems() {
    this._flatItems = this._collectFlatItems()

    let stop = this._activeItem
    while (stop !== null && this._flatItems.indexOf(stop) === -1) {
      stop = this._parentItemOf(stop)
    }
    if (stop === null && this._currentItem !== null && this._flatItems.indexOf(this._currentItem) !== -1) {
      stop = this._currentItem
    }
    if (stop === null && this._flatItems.length > 0) {
      stop = this._flatItems[0]
    }

    if (stop !== this._activeItem) {
      const hadFocus = this._activeItem !== null && this._activeItem.contains(document.activeElement) === true
      this._setActiveItem(stop, hadFocus)
    } else if (stop !== null) {
      stop.setAttribute("tabindex", "0")
    }
    return
  }

  _parentItemOf(li) {
    let parentItem = null
    const group = li.parentElement
    if (group !== null && group !== this && this.contains(group) === true) {
      const candidate = group.parentElement
      if (candidate !== null && candidate.getAttribute("role") === "treeitem") {
        parentItem = candidate
      }
    }
    return parentItem
  }

  /* Mark the item named by `current` (an item id, a link href or a link id) within this tree. */
  _applyCurrent() {
    if (this._currentItem !== null) {
      this._currentItem.removeAttribute("aria-current")
      this._currentItem = null
    }

    const current = this.getAttribute("current")
    if (current === null || current === "") {
      return
    }

    const allItems = this._allItems()
    let currentItem = null
    for (let index = 0; index < allItems.length && currentItem === null; index = index + 1) {
      const item = allItems[index]
      const link = this._linkOf(item)
      const matchesLink = link !== null && (link.getAttribute("href") === current || link.id === current)
      if (item.id === current || matchesLink === true) {
        currentItem = item
      }
    }

    if (currentItem !== null) {
      currentItem.setAttribute("aria-current", "page")
      this._currentItem = currentItem
      if (this.getAttribute("auto-expand") !== "false") {
        this._expandAncestors(currentItem)
      }
    }
    return
  }

  _expandAncestors(item) {
    let parent = this._parentItemOf(item)
    while (parent !== null) {
      parent.setAttribute("aria-expanded", "true")
      parent = this._parentItemOf(parent)
    }
    return
  }

  /*
   * A key for an item that is the same on every page load: its own id when
   * the author gave it one, else its link target, else its position path.
   */
  _stateKeyOf(li) {
    let key = ""
    const link = this._linkOf(li)

    if (li.id !== "" && this._generatedIds.has(li) === false) {
      key = `id:${li.id}`
    } else if (link !== null && link.getAttribute("href") !== null && link.getAttribute("href") !== "#") {
      key = `href:${link.getAttribute("href")}`
    } else {
      const positions = []
      let node = li
      while (node !== null) {
        positions.unshift(node.getAttribute("aria-posinset"))
        node = this._parentItemOf(node)
      }
      key = `path:${positions.join("/")}`
    }
    return key
  }

  _storageKey() {
    let key = this.getAttribute("persist-key")
    if (key === null || key.length === 0) {
      key = "mj-tree-nav"
    }
    return key
  }

  _restorePersistedState() {
    if (this._isEnabled("persist-state") === false) {
      return
    }

    let state = null
    try {
      const stored = sessionStorage.getItem(this._storageKey())
      state = stored !== null ? JSON.parse(stored) : null
    } catch (_err) {
      state = null
    }
    if (state === null || typeof state !== "object") {
      return
    }

    /* Only items of this tree are touched; stale keys match nothing and are ignored. */
    const allItems = this._allItems()
    for (let index = 0; index < allItems.length; index = index + 1) {
      const item = allItems[index]
      if (item.hasAttribute("aria-expanded") === true) {
        const saved = state[this._stateKeyOf(item)]
        if (saved === true || saved === false) {
          item.setAttribute("aria-expanded", saved === true ? "true" : "false")
        }
      }
    }
    return
  }

  _persistState() {
    if (this._isEnabled("persist-state") === false) {
      return
    }

    const state = {}
    const allItems = this._allItems()
    for (let index = 0; index < allItems.length; index = index + 1) {
      const item = allItems[index]
      if (item.hasAttribute("aria-expanded") === true) {
        state[this._stateKeyOf(item)] = item.getAttribute("aria-expanded") === "true"
      }
    }

    try {
      sessionStorage.setItem(this._storageKey(), JSON.stringify(state))
    } catch (_err) {
      // storage unavailable
    }
    return
  }

  /*
   * Move the roving tab stop to `item`; with `moveFocus` true the item also
   * takes DOM focus and its row is scrolled into view.
   */
  _setActiveItem(item, moveFocus) {
    const previous = this._activeItem

    if (previous !== null && previous !== item) {
      previous.removeAttribute("data-active")
      previous.setAttribute("tabindex", "-1")
    }

    this._activeItem = item

    if (item !== null) {
      item.setAttribute("data-active", "true")
      item.setAttribute("tabindex", "0")

      if (moveFocus === true) {
        item.focus({ preventScroll: true })
        const row = item.querySelector(":scope > .item-row")
        if (row !== null) {
          row.scrollIntoView({ block: "nearest", inline: "nearest" })
        }
      }

      if (previous !== item) {
        this.emit("mj-tree-nav-focus", { item: item })
      }
    }
    return
  }

  /* The treeitem of this tree that an event came from, or null. */
  _itemFromEvent(event) {
    let item = null
    if (event.target instanceof Element) {
      const candidate = event.target.closest("[role='treeitem']")
      if (candidate !== null && this.contains(candidate) === true) {
        item = candidate
      }
    }
    return item
  }

  _onFocusIn(event) {
    /* Focus arriving by Tab or pointer makes that item the active one. */
    const item = this._itemFromEvent(event)
    if (item !== null && item !== this._activeItem) {
      this._setActiveItem(item, false)
    }
    return
  }

  _onClick(event) {
    const li = this._itemFromEvent(event)
    if (li === null) {
      return
    }

    const isParent = li.hasAttribute("aria-expanded")
    const toggleBtn = event.target.closest(".toggle-btn")
    const onOwnRow = event.target.closest(".item-row") === li.querySelector(":scope > .item-row")

    if (toggleBtn !== null) {
      this._toggleExpand(li)
      this._setActiveItem(li, true)
      event.stopPropagation()
      return
    }

    const link = event.target.closest("a")
    const linkDisabled = link !== null && link.getAttribute("aria-disabled") === "true"

    if (isParent === true && onOwnRow === true && this._isEnabled("parent-toggle") === true) {
      /* parent-toggle: the parent's label opens and closes the branch instead of navigating. */
      event.preventDefault()
      this._toggleExpand(li)
    } else if (linkDisabled === true) {
      event.preventDefault()
    } else if (link !== null && li.contains(link) === true) {
      const href = link.getAttribute("href") || ""
      const proceed = this.emit("mj-tree-nav-navigate", { item: li, href: href }, { cancelable: true })
      if (proceed === false) {
        event.preventDefault()
      }
    }

    this._setActiveItem(li, true)
    return
  }

  /* Expand or collapse a parent item; both directions are cancelable. Returns true on change. */
  _setExpanded(li, expand) {
    let changed = false
    const expanded = li.getAttribute("aria-expanded")

    if (expanded !== null && (expanded === "true") !== expand) {
      const eventName = expand === true ? "mj-tree-nav-expand" : "mj-tree-nav-collapse"
      const proceed = this.emit(eventName, { item: li, id: li.id }, { cancelable: true })
      if (proceed === true) {
        li.setAttribute("aria-expanded", expand === true ? "true" : "false")
        changed = true
        this._refreshFlatItems()
        this._persistState()
      }
    }
    return changed
  }

  _toggleExpand(li) {
    const expanded = li.getAttribute("aria-expanded")
    if (expanded !== null) {
      this._setExpanded(li, expanded === "false")
    }
    return
  }

  _onKeydown(event) {
    if (event.altKey === true || event.ctrlKey === true || event.metaKey === true) {
      return
    }

    const items = this._flatItems
    if (items.length === 0) {
      return
    }

    /* The item the key applies to: where the event came from, else the tab stop. */
    let item = this._itemFromEvent(event)
    if (item === null || items.indexOf(item) === -1) {
      item = this._activeItem
    }
    const activeIndex = item !== null ? items.indexOf(item) : -1

    const isRtl = getComputedStyle(this).direction === "rtl"
    const openKey = isRtl === true ? "ArrowLeft" : "ArrowRight"
    const closeKey = isRtl === true ? "ArrowRight" : "ArrowLeft"

    if (event.key === "ArrowDown") {
      event.preventDefault()
      const next = activeIndex < items.length - 1 ? activeIndex + 1 : activeIndex
      this._setActiveItem(items[Math.max(next, 0)], true)
    } else if (event.key === "ArrowUp") {
      event.preventDefault()
      const prev = activeIndex > 0 ? activeIndex - 1 : 0
      this._setActiveItem(items[prev], true)
    } else if (event.key === openKey) {
      event.preventDefault()
      if (activeIndex >= 0) {
        const expanded = item.getAttribute("aria-expanded")
        if (expanded === "false") {
          this._setExpanded(item, true)
        } else if (expanded === "true") {
          /* Already open: move to the first child. */
          const visible = this._flatItems
          const position = visible.indexOf(item)
          if (position !== -1 && position < visible.length - 1 && this._parentItemOf(visible[position + 1]) === item) {
            this._setActiveItem(visible[position + 1], true)
          }
        }
      }
    } else if (event.key === closeKey) {
      event.preventDefault()
      if (activeIndex >= 0) {
        if (item.getAttribute("aria-expanded") === "true") {
          this._setExpanded(item, false)
        } else {
          const parent = this._parentItemOf(item)
          if (parent !== null) {
            this._setActiveItem(parent, true)
          }
        }
      }
    } else if (event.key === "Home") {
      event.preventDefault()
      this._setActiveItem(items[0], true)
    } else if (event.key === "End") {
      event.preventDefault()
      this._setActiveItem(items[items.length - 1], true)
    } else if (event.key === "Enter") {
      event.preventDefault()
      if (activeIndex >= 0) {
        const link = this._linkOf(item)
        if (link !== null) {
          link.click()
        }
      }
    } else if (event.key === " ") {
      event.preventDefault()
      if (activeIndex >= 0) {
        this._toggleExpand(item)
      }
    } else if (event.key === "*") {
      event.preventDefault()
      if (activeIndex >= 0) {
        this._expandAllSiblings(item)
      }
    } else if (event.key.length === 1) {
      this._typeAhead(event.key, activeIndex)
    }
    return
  }

  _expandAllSiblings(item) {
    const parent = this._parentItemOf(item)
    let siblings = this._rootItems()
    if (parent !== null) {
      const childList = this._childListOf(parent)
      siblings = Array.from(childList.children).filter((child) => child.tagName === "LI")
    }

    for (let index = 0; index < siblings.length; index = index + 1) {
      if (siblings[index].hasAttribute("aria-expanded") === true) {
        siblings[index].setAttribute("aria-expanded", "true")
      }
    }
    this._refreshFlatItems()
    this._persistState()
    return
  }

  _labelOf(li) {
    const row = li.querySelector(":scope > .item-row")
    const label = row !== null ? row.textContent.trim().toLowerCase() : ""
    return label
  }

  _typeAhead(char, activeIndex) {
    const lower = char.toLowerCase()
    const startIndex = activeIndex + 1
    const items = this._flatItems

    let matched = false
    for (let offset = 0; offset < items.length && matched === false; offset = offset + 1) {
      const index = (startIndex + offset) % items.length
      if (this._labelOf(items[index]).startsWith(lower) === true) {
        this._setActiveItem(items[index], true)
        matched = true
      }
    }
    return
  }

  get currentItem() {
    let found = this._currentItem
    if (found === null) {
      /* An item the author marked directly, without the `current` attribute. */
      found = this.querySelector("[role='treeitem'][aria-current='page']")
    }
    return found
  }

  get expandedItems() {
    const items = this._allItems().filter((item) => item.getAttribute("aria-expanded") === "true")
    return items
  }

  get activeItem() {
    return this._activeItem
  }
}
