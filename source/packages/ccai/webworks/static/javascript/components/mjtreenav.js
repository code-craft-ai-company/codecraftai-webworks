/*
 * mjtreenav.js
 *
 * <mj-tree-nav> -- hierarchical navigation tree implementing WAI-ARIA tree/treeitem.
 * Uses aria-activedescendant on the tree root for keyboard focus management.
 * Supports expand/collapse, auto-expand of current item's ancestors, and persist-state.
 *
 * WAI-ARIA: nav landmark; ul role=tree; li role=treeitem; aria-expanded; aria-current="page".
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { t } from "../core/intl.js";

const STYLES = `
:host { display: block; }

nav { font-size: var(--mj-tree-nav-font-size, var(--mj-font-size-sm)); }

.tree {
  list-style: none;
  margin: 0; padding: 0;
  outline: none;
}
.tree:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.item { list-style: none; }

.item-row {
  display: flex;
  align-items: center;
  height: var(--mj-tree-nav-item-height, 36px);
  padding-inline-end: var(--mj-space-2);
  cursor: pointer;
  border-radius: var(--mj-radius-sm);
  transition: background var(--mj-motion-fast) var(--mj-motion-ease);
  position: relative;
}
.item-row:hover { background: var(--mj-tree-nav-bg-hover, var(--mj-bg-muted)); }

.item[data-active="true"] > .item-row {
  background: var(--mj-tree-nav-bg-active, var(--mj-bg-muted));
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: -2px;
}

.item[aria-current="page"] > .item-row {
  background: var(--mj-tree-nav-bg-active, var(--mj-bg-muted));
  border-inline-start: var(--mj-tree-nav-active-border, 2px solid var(--mj-accent));
}
.item[aria-current="page"] > .item-row .item-link {
  color: var(--mj-tree-nav-color-active, var(--mj-accent));
  font-weight: var(--mj-font-weight-medium);
}

.toggle-btn {
  display: flex; align-items: center; justify-content: center;
  width: var(--mj-tree-nav-toggle-size, 20px);
  height: var(--mj-tree-nav-toggle-size, 20px);
  flex-shrink: 0;
  background: none; border: none; cursor: pointer;
  color: var(--mj-text-muted);
  padding: 0;
  border-radius: var(--mj-radius-sm);
  transition: transform var(--mj-tree-nav-transition-duration, var(--mj-motion-fast)) var(--mj-motion-ease);
}
.toggle-btn[aria-hidden="true"] { visibility: hidden; }
.item[aria-expanded="true"] > .item-row .toggle-btn { transform: rotate(90deg); }

.item-link {
  flex: 1;
  display: flex; align-items: center;
  height: 100%;
  gap: var(--mj-space-2);
  text-decoration: none;
  color: var(--mj-text);
  min-width: 0;
  padding-inline-start: var(--mj-space-1);
}
.item-label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.item-icon { flex-shrink: 0; }

.child-tree {
  list-style: none;
  margin: 0; padding: 0;
  padding-inline-start: calc(var(--mj-tree-nav-indent, var(--mj-space-5)));
}
.item[aria-expanded="false"] > .child-tree { display: none; }
.item:not([aria-expanded]) > .child-tree { display: none; }

:host([compact]) .item-row { height: 28px; }
`;

export class MjTreeNav extends MjElement {
  static tagName = "mj-tree-nav";
  static styles = STYLES;
  static watched = ["nav-label", "current", "parent-toggle", "compact", "auto-expand", "persist-state", "persist-key"];

  constructor() {
    super();
    this._treeId = nextId("mj-tree");
    this._activeItemId = null;
    this._flatItems = [];
  }

  render() {
    const navLabel = this.getAttribute("nav-label") || t("mj.treeNav.navLabel") || "Navigation";
    const markup = `
      <nav aria-label="${navLabel}">
        <ul class="tree" part="tree"
          role="tree"
          id="${this._treeId}"
          tabindex="0"
          aria-label="${navLabel}">
          <slot></slot>
        </ul>
      </nav>
    `;
    return markup
  }

  afterRender() {
    this._tree = this.$(".tree");
    this._slot = this.shadowRoot.querySelector("slot");

    this.listen(this._slot, "slotchange", this._onSlotChange.bind(this));
    this.listen(this._tree, "keydown", this._onKeydown.bind(this));
    this.listen(this._tree, "click", this._onClick.bind(this));

    this._buildTree();
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "current" && this._tree !== undefined) {
      this._applyCurrent();
    }
    return
  }

  _onSlotChange() {
    this._buildTree();
    return
  }

  _buildTree() {
    const items = this._slot.assignedElements({ flatten: true });
    this._processItems(items, this._tree, 1, items.length, 0);
    this._flatItems = this._collectFlatItems(this._tree);
    this._applyCurrent();
    this._restorePersistedState();
    return
  }

  _processItems(items, container, level, setsize, posOffset) {
    for (let i = 0; i < items.length; i = i + 1) {
      const item = items[i];
      if (item.nodeType !== Node.ELEMENT_NODE) {
        continue
      }

      const li = item.tagName === "LI" ? item : null;
      if (li === null) {
        continue
      }

      if (li.id === "") {
        li.id = nextId("mj-treeitem");
      }

      li.setAttribute("role", "treeitem");
      li.setAttribute("aria-level", String(level));
      li.setAttribute("aria-setsize", String(setsize));
      li.setAttribute("aria-posinset", String(posOffset + i + 1));

      const childUl = li.querySelector(":scope > ul, :scope > ol");
      if (childUl !== null) {
        childUl.setAttribute("role", "group");
        childUl.className = "child-tree";
        childUl.setAttribute("part", "child-tree");
        if (li.getAttribute("aria-expanded") === null) {
          li.setAttribute("aria-expanded", "false");
        }
        const children = Array.from(childUl.children);
        this._processItems(children, childUl, level + 1, children.length, 0);

        const row = this._ensureRow(li);
        this._ensureToggle(row, li);
      } else {
        const row = this._ensureRow(li);
        const toggleSlot = row.querySelector(".toggle-btn");
        if (toggleSlot !== null) {
          toggleSlot.setAttribute("aria-hidden", "true");
        }
      }

      const link = li.querySelector(":scope > a, :scope > .item-row > a");
      if (link !== null) {
        link.classList.add("item-link");
        link.setAttribute("part", "item-link");
        link.setAttribute("tabindex", "-1");
      }
    }
    return
  }

  _ensureRow(li) {
    let row = li.querySelector(":scope > .item-row");
    if (row !== null) {
      return row
    }
    row = document.createElement("div");
    row.className = "item-row";
    row.setAttribute("part", "item-row");

    const existingChildren = Array.from(li.childNodes);
    li.insertBefore(row, li.firstChild);

    for (let i = 0; i < existingChildren.length; i = i + 1) {
      const child = existingChildren[i];
      const isChildTree = child.nodeType === Node.ELEMENT_NODE &&
        (child.tagName === "UL" || child.tagName === "OL");
      if (isChildTree === false) {
        row.appendChild(child);
      }
    }
    return row
  }

  _ensureToggle(row, li) {
    if (row.querySelector(".toggle-btn") !== null) {
      return
    }
    const btn = document.createElement("button");
    btn.className = "toggle-btn";
    btn.setAttribute("part", "toggle");
    btn.setAttribute("type", "button");
    btn.setAttribute("tabindex", "-1");
    btn.setAttribute("aria-hidden", "true");
    btn.innerHTML = `<svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="3 2 9 6 3 10"/></svg>`;
    row.insertBefore(btn, row.firstChild);
    return
  }

  _collectFlatItems(tree) {
    const flat = [];
    const walk = (ul) => {
      const children = Array.from(ul.children);
      for (let i = 0; i < children.length; i = i + 1) {
        const li = children[i];
        if (li.getAttribute("role") !== "treeitem") {
          continue
        }
        flat.push(li);
        const expanded = li.getAttribute("aria-expanded");
        if (expanded === "true") {
          const childUl = li.querySelector(":scope > ul[role='group'], :scope > ol[role='group']");
          if (childUl !== null) {
            walk(childUl);
          }
        }
      }
    };
    walk(tree);
    return flat
  }

  _applyCurrent() {
    const current = this.getAttribute("current");
    if (current === null || current === "") {
      return
    }

    const allItems = this._tree.querySelectorAll("[role='treeitem']");
    for (let i = 0; i < allItems.length; i = i + 1) {
      allItems[i].removeAttribute("aria-current");
    }

    let currentItem = document.getElementById(current);
    if (currentItem === null) {
      currentItem = Array.from(allItems).find(function(item) {
        const link = item.querySelector("a");
        return link !== null && (link.getAttribute("href") === current || link.id === current);
      });
    }

    if (currentItem !== undefined && currentItem !== null) {
      currentItem.setAttribute("aria-current", "page");
      if (this.getAttribute("auto-expand") !== "false") {
        this._expandAncestors(currentItem);
      }
    }

    this._flatItems = this._collectFlatItems(this._tree);
    return
  }

  _expandAncestors(item) {
    let parent = item.parentElement;
    while (parent !== null && parent !== this._tree) {
      if (parent.getAttribute("role") === "treeitem") {
        parent.setAttribute("aria-expanded", "true");
      }
      parent = parent.parentElement;
    }
    return
  }

  _restorePersistedState() {
    if (this.getAttribute("persist-state") !== "true") {
      return
    }
    const key = this.getAttribute("persist-key") || "mj-tree-nav";
    let stored = null;
    try {
      stored = sessionStorage.getItem(key);
    } catch (_err) {
      return
    }
    if (stored === null) {
      return
    }
    let state = null;
    try {
      state = JSON.parse(stored);
    } catch (_err) {
      return
    }
    if (state === null || typeof state !== "object") {
      return
    }
    const ids = Object.keys(state);
    for (let i = 0; i < ids.length; i = i + 1) {
      const el = document.getElementById(ids[i]);
      if (el !== null) {
        el.setAttribute("aria-expanded", state[ids[i]] === true ? "true" : "false");
      }
    }
    this._flatItems = this._collectFlatItems(this._tree);
    return
  }

  _persistState() {
    if (this.getAttribute("persist-state") !== "true") {
      return
    }
    const key = this.getAttribute("persist-key") || "mj-tree-nav";
    const expandableItems = this._tree.querySelectorAll("[role='treeitem'][aria-expanded]");
    const state = {};
    for (let i = 0; i < expandableItems.length; i = i + 1) {
      const item = expandableItems[i];
      state[item.id] = item.getAttribute("aria-expanded") === "true";
    }
    try {
      sessionStorage.setItem(key, JSON.stringify(state));
    } catch (_err) {
      // storage unavailable
    }
    return
  }

  _setActiveItem(item) {
    const current = this._tree.querySelector("[data-active='true']");
    if (current !== null) {
      current.removeAttribute("data-active");
    }
    if (item !== null) {
      item.setAttribute("data-active", "true");
      this._tree.setAttribute("aria-activedescendant", item.id);
      this._activeItemId = item.id;
      this.emit("mj-tree-nav-focus", { item: item });
    } else {
      this._tree.removeAttribute("aria-activedescendant");
      this._activeItemId = null;
    }
    return
  }

  _getActiveIndex() {
    if (this._activeItemId === null) {
      return -1
    }
    for (let i = 0; i < this._flatItems.length; i = i + 1) {
      if (this._flatItems[i].id === this._activeItemId) {
        return i
      }
    }
    return -1
  }

  _onClick(event) {
    const li = event.target.closest("[role='treeitem']");
    if (li === null) {
      return
    }

    const toggleBtn = event.target.closest(".toggle-btn");
    if (toggleBtn !== null) {
      this._toggleExpand(li);
      this._setActiveItem(li);
      event.stopPropagation();
      return
    }

    const link = event.target.closest("a.item-link, a");
    if (link !== null) {
      const href = link.getAttribute("href") || "";
      const proceed = this.emit("mj-tree-nav-navigate", { item: li, href: href }, { cancelable: true });
      if (proceed === false) {
        event.preventDefault();
      }
    }

    this._setActiveItem(li);
    this._flatItems = this._collectFlatItems(this._tree);
    return
  }

  _toggleExpand(li) {
    const expanded = li.getAttribute("aria-expanded");
    if (expanded === null) {
      return
    }

    if (expanded === "false") {
      const proceed = this.emit("mj-tree-nav-expand", { item: li, id: li.id }, { cancelable: true });
      if (proceed === true) {
        li.setAttribute("aria-expanded", "true");
      }
    } else {
      const proceed = this.emit("mj-tree-nav-collapse", { item: li, id: li.id }, { cancelable: true });
      if (proceed === true) {
        li.setAttribute("aria-expanded", "false");
      }
    }

    this._flatItems = this._collectFlatItems(this._tree);
    this._persistState();
    return
  }

  _onKeydown(event) {
    const activeIndex = this._getActiveIndex();
    const items = this._flatItems;

    if (event.key === "ArrowDown") {
      event.preventDefault();
      const next = activeIndex < items.length - 1 ? activeIndex + 1 : activeIndex;
      this._setActiveItem(items[next]);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      const prev = activeIndex > 0 ? activeIndex - 1 : 0;
      this._setActiveItem(items[prev]);
    } else if (event.key === "ArrowRight") {
      event.preventDefault();
      if (activeIndex >= 0) {
        const item = items[activeIndex];
        const expanded = item.getAttribute("aria-expanded");
        if (expanded === "false") {
          const proceed = this.emit("mj-tree-nav-expand", { item: item, id: item.id }, { cancelable: true });
          if (proceed === true) {
            item.setAttribute("aria-expanded", "true");
            this._flatItems = this._collectFlatItems(this._tree);
          }
        } else if (expanded === "true") {
          const childItems = this._collectFlatItems(this._tree);
          const childIndex = childItems.findIndex(function(el) { return el.id === item.id; });
          if (childIndex < childItems.length - 1) {
            this._flatItems = childItems;
            this._setActiveItem(childItems[childIndex + 1]);
          }
        }
      }
    } else if (event.key === "ArrowLeft") {
      event.preventDefault();
      if (activeIndex >= 0) {
        const item = items[activeIndex];
        const expanded = item.getAttribute("aria-expanded");
        if (expanded === "true") {
          const proceed = this.emit("mj-tree-nav-collapse", { item: item, id: item.id }, { cancelable: true });
          if (proceed === true) {
            item.setAttribute("aria-expanded", "false");
            this._flatItems = this._collectFlatItems(this._tree);
          }
        } else {
          const parent = item.closest("[role='group']")?.closest("[role='treeitem']");
          if (parent !== null && parent !== undefined) {
            this._setActiveItem(parent);
            this._flatItems = this._collectFlatItems(this._tree);
          }
        }
      }
    } else if (event.key === "Home") {
      event.preventDefault();
      if (items.length > 0) {
        this._setActiveItem(items[0]);
      }
    } else if (event.key === "End") {
      event.preventDefault();
      if (items.length > 0) {
        this._setActiveItem(items[items.length - 1]);
      }
    } else if (event.key === "Enter") {
      event.preventDefault();
      if (activeIndex >= 0) {
        const item = items[activeIndex];
        const link = item.querySelector("a");
        if (link !== null) {
          link.click();
        }
      }
    } else if (event.key === " ") {
      event.preventDefault();
      if (activeIndex >= 0) {
        this._toggleExpand(items[activeIndex]);
      }
    } else if (event.key === "*") {
      event.preventDefault();
      if (activeIndex >= 0) {
        this._expandAllSiblings(items[activeIndex]);
      }
    } else if (event.key.length === 1) {
      this._typeAhead(event.key);
    }
    return
  }

  _expandAllSiblings(item) {
    const parent = item.closest("[role='group']") || this._tree;
    const siblings = Array.from(parent.querySelectorAll(":scope > [role='treeitem'][aria-expanded]"));
    for (let i = 0; i < siblings.length; i = i + 1) {
      siblings[i].setAttribute("aria-expanded", "true");
    }
    this._flatItems = this._collectFlatItems(this._tree);
    this._persistState();
    return
  }

  _typeAhead(char) {
    const lower = char.toLowerCase();
    const startIndex = this._getActiveIndex() + 1;
    const items = this._flatItems;

    for (let i = 0; i < items.length; i = i + 1) {
      const idx = (startIndex + i) % items.length;
      const label = items[idx].querySelector(".item-label, a")?.textContent.trim().toLowerCase() || "";
      if (label.startsWith(lower) === true) {
        this._setActiveItem(items[idx]);
        return
      }
    }
    return
  }

  get currentItem() {
    const found = this._tree.querySelector("[aria-current='page']");
    return found
  }

  get expandedItems() {
    const items = this._tree.querySelectorAll("[role='treeitem'][aria-expanded='true']");
    return Array.from(items)
  }

  get activeItem() {
    if (this._activeItemId === null) {
      return null
    }
    return document.getElementById(this._activeItemId)
  }
}
