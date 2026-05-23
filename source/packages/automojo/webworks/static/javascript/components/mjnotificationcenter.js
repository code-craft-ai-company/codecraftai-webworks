/*
 * mjnotificationcenter.js
 *
 * <mj-notification-center> -- persistent notification history panel.
 * Displays, groups, and manages read/unread notifications with dismiss,
 * mark-all-read, and clear-all actions. Roving-tabindex keyboard navigation.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { RovingTabindex } from "../core/focustrap.js";
import { announce } from "../core/announcer.js";

const STYLES = `
:host {
  display: block;
  width: var(--mj-nc-width, 22rem);
  max-height: var(--mj-nc-max-height, 80vh);
  background: var(--mj-surface);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-lg);
  box-shadow: var(--mj-elevation-2);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  color: var(--mj-text);
}

.nc-header {
  display: flex;
  align-items: center;
  padding: var(--mj-space-3) var(--mj-space-4);
  border-bottom: 1px solid var(--mj-border);
  gap: var(--mj-space-2);
  flex-shrink: 0;
}

.nc-title {
  font-weight: var(--mj-font-weight-bold);
  font-size: var(--mj-font-size-md);
  flex: 1;
}

.nc-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.25rem;
  height: 1.25rem;
  padding: 0 0.3rem;
  background: var(--mj-accent);
  color: var(--mj-text-on-accent);
  border-radius: var(--mj-radius-pill);
  font-size: var(--mj-font-size-xs);
  font-weight: var(--mj-font-weight-bold);
}

.nc-badge[aria-hidden="true"] { display: none; }

.nc-action-btn {
  font-size: var(--mj-font-size-xs);
  padding: var(--mj-space-1) var(--mj-space-2);
  background: transparent;
  border: none;
  border-radius: var(--mj-radius-md);
  cursor: pointer;
  color: var(--mj-accent);
}

.nc-action-btn:hover { background: var(--mj-bg-muted); }
.nc-action-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.nc-action-btn:disabled { opacity: 0.45; cursor: not-allowed; }

.nc-list {
  flex: 1;
  overflow-y: auto;
  list-style: none;
  margin: 0;
  padding: 0;
}

.nc-group-header {
  padding: var(--mj-space-2) var(--mj-space-4);
  font-size: var(--mj-font-size-xs);
  font-weight: var(--mj-font-weight-bold);
  color: var(--mj-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: var(--mj-bg-subtle);
}

.nc-item {
  display: flex;
  align-items: flex-start;
  gap: var(--mj-space-3);
  padding: var(--mj-nc-item-padding, var(--mj-space-4));
  border-bottom: 1px solid var(--mj-border);
  cursor: pointer;
  position: relative;
  outline: none;
}

.nc-item[data-unread="true"] {
  background: var(--mj-bg-subtle);
  font-weight: var(--mj-font-weight-medium);
}

.nc-item:hover { background: var(--mj-bg-muted); }
.nc-item:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: -2px;
}

.nc-unread-dot {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: var(--mj-radius-circle);
  background: var(--mj-accent);
  flex-shrink: 0;
  margin-top: 0.4rem;
}

.nc-item[data-unread="false"] .nc-unread-dot { visibility: hidden; }

.nc-item-content { flex: 1; min-width: 0; }

.nc-item-title {
  font-size: var(--mj-font-size-sm);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: var(--mj-space-1);
}

.nc-item-body {
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.nc-item-time {
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
  margin-top: var(--mj-space-1);
}

.nc-dismiss-btn {
  display: none;
  width: 1.5rem;
  height: 1.5rem;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: var(--mj-radius-md);
  cursor: pointer;
  color: var(--mj-text-muted);
  font-size: 0.7rem;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
}

.nc-item:hover .nc-dismiss-btn,
.nc-item:focus-within .nc-dismiss-btn { display: inline-flex; }

.nc-dismiss-btn:hover { background: var(--mj-bg-muted); color: var(--mj-text); }
.nc-dismiss-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.nc-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--mj-space-8) var(--mj-space-4);
  color: var(--mj-text-muted);
  text-align: center;
}

.nc-footer {
  padding: var(--mj-space-3) var(--mj-space-4);
  border-top: 1px solid var(--mj-border);
  flex-shrink: 0;
}

.nc-footer:empty { display: none; }
`;

export class MjNotificationCenter extends MjElement {
  static tagName = "mj-notification-center";
  static styles = STYLES;
  static watched = ["loading", "group-by", "empty-message", "show-mark-all-read", "show-clear-all"];

  constructor() {
    super()
    this._items = []
    this._roving = null
    this._listEl = null
    this._badgeEl = null
  }

  render() {
    const label = this.getAttribute("label") || "Notifications"
    const emptyMsg = this.getAttribute("empty-message") || "No notifications"
    const showMarkAll = this.getAttribute("show-mark-all-read") !== "false"
    const showClearAll = this.getAttribute("show-clear-all") !== "false"

    const markup = `
      <div class="nc-header" part="header">
        <slot name="header">
          <span class="nc-title" part="title">${label}</span>
          <span class="nc-badge" part="badge" aria-hidden="true">0</span>
          ${showMarkAll ? `<button class="nc-action-btn" part="mark-all-read" data-action="mark-all-read">Mark all read</button>` : ""}
          ${showClearAll ? `<button class="nc-action-btn" part="clear-all" data-action="clear-all">Clear all</button>` : ""}
        </slot>
      </div>
      <ul class="nc-list" part="list" role="list" aria-label="${label}"></ul>
      <div class="nc-footer" part="footer"><slot name="footer"></slot></div>
    `
    return markup
  }

  afterRender() {
    this._listEl = this.$(".nc-list")
    this._badgeEl = this.$(".nc-badge")

    this.listen(this.shadowRoot, "click", this._onClick.bind(this))
    this.listen(this._listEl, "keydown", this._onKeydown.bind(this))

    this._roving = new RovingTabindex({
      orientation: "vertical",
      wrap: false
    })

    this._renderList()
    return
  }

  _renderList() {
    if (this._listEl === null) {
      return
    }

    this._listEl.innerHTML = ""

    if (this._items.length === 0) {
      const empty = document.createElement("li")
      empty.className = "nc-empty"
      empty.setAttribute("role", "listitem")
      const emptyMsg = this.getAttribute("empty-message") || "No notifications"
      empty.innerHTML = `<slot name="empty"><span>${emptyMsg}</span></slot>`
      this._listEl.appendChild(empty)
      this._updateBadge()
      return
    }

    const groupBy = this.getAttribute("group-by") || "date"
    const groups = this._groupItems(groupBy)

    for (const group of groups) {
      if (group.label !== null) {
        const header = document.createElement("li")
        header.className = "nc-group-header"
        header.setAttribute("role", "presentation")
        header.setAttribute("part", "group-header")
        header.textContent = group.label
        this._listEl.appendChild(header)
      }

      for (const item of group.items) {
        const li = this._buildItemEl(item)
        this._listEl.appendChild(li)
      }
    }

    const itemEls = Array.from(this._listEl.querySelectorAll(".nc-item"))
    this._roving.setItems(itemEls)

    this._updateBadge()
    return
  }

  _buildItemEl(item) {
    const li = document.createElement("li")
    li.className = "nc-item"
    li.setAttribute("role", "listitem")
    li.setAttribute("part", "item")
    li.setAttribute("data-item-id", item.id)
    li.setAttribute("data-unread", item.read === true ? "false" : "true")
    li.setAttribute("tabindex", "-1")

    const unreadPrefix = item.read === false ? "Unread: " : ""
    const timeStr = item.timestamp ? this._formatTime(item.timestamp) : ""
    li.setAttribute("aria-label", `${unreadPrefix}${item.title}. ${item.body || ""}. ${timeStr}`)

    li.innerHTML = `
      <span class="nc-unread-dot" part="item-unread" aria-hidden="true"></span>
      <div class="nc-item-content">
        <div class="nc-item-title">${item.title || ""}</div>
        <div class="nc-item-body">${item.body || ""}</div>
        ${timeStr ? `<div class="nc-item-time">${timeStr}</div>` : ""}
      </div>
      <button class="nc-dismiss-btn" part="item-dismiss" aria-label="Dismiss: ${item.title || ""}" data-dismiss-id="${item.id}">&#x2715;</button>
    `

    return li
  }

  _groupItems(groupBy) {
    if (groupBy === "none") {
      return [{ label: null, items: this._items }]
    }

    if (groupBy === "category") {
      const map = new Map()
      for (const item of this._items) {
        const cat = item.category || "Other"
        if (map.has(cat) === false) {
          map.set(cat, [])
        }
        map.get(cat).push(item)
      }
      const groups = []
      for (const [key, items] of map.entries()) {
        groups.push({ label: key, items: items })
      }
      return groups
    }

    const now = new Date()
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const yesterdayStart = new Date(todayStart.getTime() - 86400000)

    const today = []
    const yesterday = []
    const older = []

    for (const item of this._items) {
      if (item.timestamp === undefined || item.timestamp === null) {
        older.push(item)
        continue
      }
      const d = new Date(item.timestamp)
      if (d >= todayStart) {
        today.push(item)
      } else if (d >= yesterdayStart) {
        yesterday.push(item)
      } else {
        older.push(item)
      }
    }

    const groups = []
    if (today.length > 0) {
      groups.push({ label: "Today", items: today })
    }
    if (yesterday.length > 0) {
      groups.push({ label: "Yesterday", items: yesterday })
    }
    if (older.length > 0) {
      groups.push({ label: "Older", items: older })
    }
    return groups
  }

  _formatTime(timestamp) {
    const d = new Date(timestamp)
    if (isNaN(d.getTime()) === true) {
      return ""
    }
    const locale = document.documentElement.lang || undefined
    const now = new Date()
    const diffMs = now.getTime() - d.getTime()
    const diffMin = Math.floor(diffMs / 60000)

    if (diffMin < 1) {
      return "just now"
    }
    if (diffMin < 60) {
      return `${diffMin}m ago`
    }
    if (diffMin < 1440) {
      return `${Math.floor(diffMin / 60)}h ago`
    }
    return d.toLocaleDateString(locale)
  }

  _updateBadge() {
    const count = this.unreadCount
    if (this._badgeEl !== null) {
      this._badgeEl.textContent = String(count)
      this._badgeEl.setAttribute("aria-label", `${count} unread notifications`)
      this._badgeEl.setAttribute("aria-hidden", count === 0 ? "true" : "false")
    }
    const markAllBtn = this.$("[data-action='mark-all-read']")
    if (markAllBtn !== null) {
      markAllBtn.disabled = count === 0
    }
    return
  }

  _onClick(event) {
    const dismissBtn = event.target.closest("[data-dismiss-id]")
    if (dismissBtn !== null) {
      event.stopPropagation()
      const id = dismissBtn.getAttribute("data-dismiss-id")
      this._dismissItem(id)
      return
    }

    const actionBtn = event.target.closest("[data-action]")
    if (actionBtn !== null) {
      const action = actionBtn.getAttribute("data-action")
      if (action === "mark-all-read") {
        this._markAllRead()
      } else if (action === "clear-all") {
        this._clearAll()
      }
      return
    }

    const itemEl = event.target.closest(".nc-item")
    if (itemEl !== null) {
      const id = itemEl.getAttribute("data-item-id")
      this._selectItem(id)
    }
    return
  }

  _onKeydown(event) {
    const item = event.target.closest(".nc-item")
    if (item === null) {
      return
    }

    if (event.key === "Delete" || event.key === "Backspace") {
      event.preventDefault()
      const id = item.getAttribute("data-item-id")
      this._dismissItem(id)
      return
    }

    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      const id = item.getAttribute("data-item-id")
      this._selectItem(id)
      return
    }

    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault()
      const items = Array.from(this._listEl.querySelectorAll(".nc-item"))
      const idx = items.indexOf(item)
      if (event.key === "ArrowDown" && idx < items.length - 1) {
        items[idx + 1].focus()
      } else if (event.key === "ArrowUp" && idx > 0) {
        items[idx - 1].focus()
      }
      return
    }

    if (event.key === "Home") {
      const first = this._listEl.querySelector(".nc-item")
      if (first !== null) {
        first.focus()
      }
      return
    }

    if (event.key === "End") {
      const all = this._listEl.querySelectorAll(".nc-item")
      if (all.length > 0) {
        all[all.length - 1].focus()
      }
      return
    }
    return
  }

  _selectItem(id) {
    const item = this._items.find((i) => i.id === id)
    if (item === undefined) {
      return
    }
    item.read = true
    this._rerenderItem(id)
    this._updateBadge()
    this.emit("mj-notification-read", { item: item })
    this.emit("mj-notification-select", { item: item })
    return
  }

  _dismissItem(id) {
    const item = this._items.find((i) => i.id === id)
    if (item === undefined) {
      return
    }

    const proceed = this.emit("mj-notification-dismiss", { item: item }, { cancelable: true })
    if (proceed === false) {
      return
    }

    const idx = this._items.indexOf(item)
    this._items.splice(idx, 1)

    const itemEl = this._listEl !== null
      ? this._listEl.querySelector(`[data-item-id="${id}"]`)
      : null

    if (itemEl !== null) {
      const nextSibling = itemEl.nextElementSibling
      const prevSibling = itemEl.previousElementSibling
      itemEl.remove()

      const nextItem = (nextSibling && nextSibling.classList.contains("nc-item"))
        ? nextSibling
        : (prevSibling && prevSibling.classList.contains("nc-item") ? prevSibling : null)

      if (nextItem !== null) {
        nextItem.focus()
      }
    }

    if (this._items.length === 0) {
      this._renderList()
    } else {
      this._updateBadge()
    }
    return
  }

  _rerenderItem(id) {
    const item = this._items.find((i) => i.id === id)
    if (item === undefined) {
      return
    }
    const existing = this._listEl !== null
      ? this._listEl.querySelector(`[data-item-id="${id}"]`)
      : null

    if (existing !== null) {
      const newEl = this._buildItemEl(item)
      newEl.tabIndex = existing.tabIndex
      existing.replaceWith(newEl)
    }
    return
  }

  _markAllRead() {
    const count = this._items.filter((i) => i.read === false).length
    for (const item of this._items) {
      item.read = true
    }
    this._renderList()
    this.emit("mj-notification-mark-all-read", { count: count })
    return
  }

  _clearAll() {
    const count = this._items.length
    const proceed = this.emit("mj-notification-clear-all", { count: count }, { cancelable: true })
    if (proceed === false) {
      return
    }
    this._items = []
    this._renderList()
    return
  }

  /* Scriptable API */

  get items() {
    return this._items
  }

  set items(value) {
    this._items = Array.isArray(value) ? value.slice() : []
    if (this._listEl !== null) {
      this._renderList()
    }
    return
  }

  get unreadCount() {
    const count = this._items.filter((i) => i.read === false).length
    return count
  }

  addItem(descriptor) {
    const id = descriptor.id || nextId("mj-notif")
    const item = Object.assign({ id: id, read: false }, descriptor)
    const maxItems = parseInt(this.getAttribute("max-items") || "100", 10)

    const dupeIdx = this._items.findIndex((i) => i.id === item.id)
    if (dupeIdx >= 0) {
      console.error(`<mj-notification-center>: duplicate item id "${item.id}"`)
      return
    }

    this._items.unshift(item)

    if (this._items.length > maxItems) {
      const readIdx = this._items.findLastIndex((i) => i.read === true)
      if (readIdx >= 0) {
        this._items.splice(readIdx, 1)
      } else {
        this._items.pop()
        console.warn("<mj-notification-center>: max-items reached, evicting unread item")
      }
    }

    if (this._listEl !== null) {
      this._renderList()
    }
    announce("New notification: " + (item.title || ""), "polite")
    return
  }
}
