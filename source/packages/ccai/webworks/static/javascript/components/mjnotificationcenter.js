/*
 * mjnotificationcenter.js
 *
 * <mj-notification-center> -- persistent notification history panel.
 * Displays, groups, and manages read/unread notifications with dismiss,
 * mark-all-read, and clear-all actions. Roving-tabindex keyboard navigation.
 *
 * Every value that comes from a notification (title, body, id, href,
 * avatar) is written with textContent / setAttribute, never as markup:
 * notification text is typically written by other users.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { html, safeUrl } from "../core/html.js";
import { t, formatRelativeTime, getLocale } from "../core/intl.js";
import { RovingTabindex, deepActiveElement } from "../core/focustrap.js";
import { announce } from "../core/announcer.js";

/* Skeleton rows shown while `loading` is set. */
const SKELETON_ROWS = 3;

const STYLES = `
:host {
  display: flex;
  flex-direction: column;
  width: var(--mj-nc-width, 22rem);
  max-height: var(--mj-nc-max-height, 80vh);
  background: var(--mj-nc-bg, var(--mj-surface));
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-lg);
  box-shadow: var(--mj-elevation-2);
  overflow: hidden;
  color: var(--mj-text);
}

.nc-header {
  display: flex;
  align-items: center;
  padding: var(--mj-space-3) var(--mj-space-4);
  border-block-end: 1px solid var(--mj-border);
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

.nc-action-btn[hidden] { display: none; }
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
  border-block-end: 1px solid var(--mj-border);
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
  background: var(--mj-nc-unread-color, var(--mj-accent));
  flex-shrink: 0;
  margin-block-start: 0.4rem;
}

.nc-item[data-unread="false"] .nc-unread-dot { visibility: hidden; }

.nc-item[data-severity="error"] .nc-unread-dot { background: var(--mj-color-danger); }
.nc-item[data-severity="warning"] .nc-unread-dot { background: var(--mj-color-warning); }
.nc-item[data-severity="success"] .nc-unread-dot { background: var(--mj-color-success); }

.nc-avatar {
  width: 2rem;
  height: 2rem;
  border-radius: var(--mj-radius-circle);
  object-fit: cover;
  flex-shrink: 0;
}

.nc-item-content { flex: 1; min-width: 0; }

.nc-item-title {
  font-size: var(--mj-font-size-sm);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-block-end: var(--mj-space-1);
}

.nc-item-body {
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.nc-item-body:empty, .nc-item-time:empty { display: none; }

.nc-item-time {
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
  margin-block-start: var(--mj-space-1);
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

.nc-skeleton {
  display: flex;
  flex-direction: column;
  gap: var(--mj-space-2);
  padding: var(--mj-nc-item-padding, var(--mj-space-4));
  border-block-end: 1px solid var(--mj-border);
}

.nc-skeleton-line {
  height: 0.75rem;
  border-radius: var(--mj-radius-sm);
  background: var(--mj-bg-muted);
  animation: mj-nc-pulse 1.2s ease-in-out infinite;
}

.nc-skeleton-line.short { width: 60%; }

@keyframes mj-nc-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.45; }
}

.nc-footer {
  padding: var(--mj-space-3) var(--mj-space-4);
  border-block-start: 1px solid var(--mj-border);
  flex-shrink: 0;
}

.nc-footer[hidden] { display: none; }

@media (prefers-reduced-motion: reduce) {
  .nc-skeleton-line { animation: none; }
}
`;

/* Upper-case the first letter, as the locale does it ("today" -> "Today"). */
function capitalize(text) {
  let result = text
  if (text.length > 0) {
    result = text.charAt(0).toLocaleUpperCase(getLocale()) + text.slice(1)
  }
  return result
}

export class MjNotificationCenter extends MjElement {
  static tagName = "mj-notification-center";
  static styles = STYLES;
  static watched = [
    "loading", "group-by", "empty-message", "show-mark-all-read", "show-clear-all", "label",
    "max-items", "mark-all-read-label", "clear-all-label", "dismiss-label", "unread-label",
    "older-label"
  ];

  constructor() {
    super()
    this._items = []
    this._roving = null
    this._rovingDispose = null
    this._listEl = null
    this._titleEl = null
    this._badgeEl = null
    this._markAllBtn = null
    this._clearAllBtn = null
    this._footerEl = null

    /* notification id -> its list element. Ids are never used in selectors. */
    this._itemEls = new Map()

    /* Id of the item that was focused or activated last. */
    this._selectedId = null
  }

  render() {
    const markup = html`
      <div class="nc-header" part="header">
        <slot name="header">
          <span class="nc-title" part="title"></span>
          <span class="nc-badge" part="badge" aria-hidden="true">0</span>
          <button class="nc-action-btn" part="mark-all-read" type="button" data-action="mark-all-read"></button>
          <button class="nc-action-btn" part="clear-all" type="button" data-action="clear-all"></button>
        </slot>
      </div>
      <ul class="nc-list" part="list" role="list"></ul>
      <div class="nc-footer" part="footer"><slot name="footer"></slot></div>
    `
    return markup
  }

  afterRender() {
    this._listEl = this.$(".nc-list")
    this._titleEl = this.$(".nc-title")
    this._badgeEl = this.$(".nc-badge")
    this._markAllBtn = this.$("[data-action='mark-all-read']")
    this._clearAllBtn = this.$("[data-action='clear-all']")
    this._footerEl = this.$(".nc-footer")

    this.listen(this.shadowRoot, "click", this._onClick.bind(this))
    this.listen(this._listEl, "keydown", this._onKeydown.bind(this))
    this.listen(this._listEl, "focusin", this._onFocusIn.bind(this))
    this.listen(this.$("slot[name='footer']"), "slotchange", this._syncFooter.bind(this))

    /* Arrow keys, Home and End move the single tab stop between items. */
    this._roving = new RovingTabindex({
      orientation: "vertical",
      wrap: false
    })
    this._rovingDispose = this._roving.attach(this._listEl)
    this.onTeardown(this._rovingDispose)

    this._applyHeader()
    this._syncFooter()
    this._renderList()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._listEl === undefined || this._listEl === null) {
      return
    }

    if (name === "label" || name === "mark-all-read-label" || name === "clear-all-label" ||
        name === "show-mark-all-read" || name === "show-clear-all") {
      this._applyHeader()
    } else if (name === "max-items") {
      if (this._enforceMaxItems() === true) {
        this._renderList()
      }
    } else {
      this._renderList()
    }
    return
  }

  /* ----- normalisation ----- */

  /*
   * Every item has a string id and a boolean `read` (anything but true is
   * unread), so the badge, the unread styling and `unreadCount` agree.
   */
  _normalizeItem(item) {
    if (item.id === undefined || item.id === null || String(item.id).length === 0) {
      item.id = nextId("mj-notif")
    } else {
      item.id = String(item.id)
    }
    item.read = item.read === true
    return item
  }

  _maxItems() {
    const parsed = parseInt(this.getAttribute("max-items") || "", 10)
    const max = Number.isFinite(parsed) === true && parsed > 0 ? parsed : 100
    return max
  }

  /* Evict items beyond `max-items`: read ones first, then the oldest. */
  _enforceMaxItems() {
    let evicted = false
    const maxItems = this._maxItems()

    while (this._items.length > maxItems) {
      evicted = true
      const readIdx = this._items.findLastIndex((entry) => entry.read === true)
      if (readIdx >= 0) {
        this._items.splice(readIdx, 1)
      } else {
        this._items.pop()
        console.warn("<mj-notification-center>: max-items reached, evicting unread item")
      }
    }
    return evicted
  }

  /* ----- strings ----- */

  _label() {
    const label = this.getAttribute("label") || t("mj.notificationCenter.label")
    return label
  }

  _dismissLabel() {
    const label = this.getAttribute("dismiss-label") || t("mj.notificationCenter.dismiss")
    return label
  }

  _unreadLabel() {
    const label = this.getAttribute("unread-label") || t("mj.notificationCenter.unread")
    return label
  }

  /* ----- rendering ----- */

  _applyHeader() {
    const label = this._label()
    this._titleEl.textContent = label
    this._listEl.setAttribute("aria-label", label)

    this._markAllBtn.textContent = this.getAttribute("mark-all-read-label") || t("mj.notificationCenter.markAllRead")
    this._clearAllBtn.textContent = this.getAttribute("clear-all-label") || t("mj.notificationCenter.clearAll")
    this._markAllBtn.hidden = this.getAttribute("show-mark-all-read") === "false"
    this._clearAllBtn.hidden = this.getAttribute("show-clear-all") === "false"
    this._updateBadge()
    return
  }

  _syncFooter() {
    const footerSlot = this.$("slot[name='footer']")
    this._footerEl.hidden = footerSlot.assignedNodes().length === 0
    return
  }

  /*
   * Rebuild the list from `_items`. The focused item keeps focus across the
   * rebuild (an item with the same id gets it back).
   */
  _renderList() {
    if (this._listEl === null) {
      return
    }

    const active = deepActiveElement()
    let focusedId = null
    for (const [id, element] of this._itemEls.entries()) {
      if (element === active) {
        focusedId = id
      }
    }

    this._listEl.textContent = ""
    this._itemEls.clear()

    const loading = this.hasAttribute("loading") === true && this.getAttribute("loading") !== "false"
    this._listEl.setAttribute("aria-busy", loading === true ? "true" : "false")

    if (loading === true) {
      for (let index = 0; index < SKELETON_ROWS; index = index + 1) {
        const skeleton = document.createElement("li")
        skeleton.className = "nc-skeleton"
        skeleton.setAttribute("part", "skeleton")
        skeleton.setAttribute("aria-hidden", "true")
        const line = document.createElement("div")
        line.className = "nc-skeleton-line"
        const shortLine = document.createElement("div")
        shortLine.className = "nc-skeleton-line short"
        skeleton.appendChild(line)
        skeleton.appendChild(shortLine)
        this._listEl.appendChild(skeleton)
      }
      this._roving.setItems([])
      this._updateBadge()
      return
    }

    if (this._items.length === 0) {
      const empty = document.createElement("li")
      empty.className = "nc-empty"
      empty.setAttribute("part", "empty")
      empty.setAttribute("role", "listitem")

      const slot = document.createElement("slot")
      slot.setAttribute("name", "empty")
      const message = document.createElement("span")
      message.textContent = this.getAttribute("empty-message") || t("mj.notificationCenter.empty")
      slot.appendChild(message)
      empty.appendChild(slot)

      this._listEl.appendChild(empty)
      this._roving.setItems([])
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
        this._itemEls.set(item.id, li)
        this._listEl.appendChild(li)
      }
    }

    const itemEls = Array.from(this._itemEls.values())
    const order = Array.from(this._listEl.querySelectorAll(".nc-item"))
    const keepId = focusedId !== null ? focusedId : this._selectedId
    const keepEl = keepId !== null ? this._itemEls.get(keepId) : undefined
    this._roving.index = keepEl !== undefined ? order.indexOf(keepEl) : 0
    this._roving.setItems(order.length > 0 ? order : itemEls)

    if (focusedId !== null && keepEl !== undefined) {
      keepEl.focus()
    }

    this._updateBadge()
    return
  }

  _buildItemEl(item) {
    const li = document.createElement("li")
    li.className = "nc-item"
    li.setAttribute("role", "listitem")
    li.setAttribute("part", "item")
    li.setAttribute("tabindex", "-1")
    li._mjItemId = item.id

    if (typeof item.severity === "string" && item.severity.length > 0) {
      li.setAttribute("data-severity", item.severity)
    }

    const dot = document.createElement("span")
    dot.className = "nc-unread-dot"
    dot.setAttribute("part", "item-unread")
    dot.setAttribute("aria-hidden", "true")
    li.appendChild(dot)

    const avatarSrc = safeUrl(item.avatarSrc, "")
    if (avatarSrc.length > 0) {
      const avatar = document.createElement("img")
      avatar.className = "nc-avatar"
      avatar.setAttribute("part", "item-avatar")
      avatar.setAttribute("src", avatarSrc)
      avatar.setAttribute("alt", item.avatarAlt !== undefined && item.avatarAlt !== null ? String(item.avatarAlt) : "")
      li.appendChild(avatar)
    }

    const content = document.createElement("div")
    content.className = "nc-item-content"

    const title = document.createElement("div")
    title.className = "nc-item-title"
    title.textContent = this._text(item.title)
    content.appendChild(title)

    const body = document.createElement("div")
    body.className = "nc-item-body"
    body.textContent = this._text(item.body)
    content.appendChild(body)

    const time = document.createElement("div")
    time.className = "nc-item-time"
    time.textContent = item.timestamp ? this._formatTime(item.timestamp) : ""
    content.appendChild(time)

    li.appendChild(content)

    const dismissBtn = document.createElement("button")
    dismissBtn.className = "nc-dismiss-btn"
    dismissBtn.setAttribute("type", "button")
    dismissBtn.setAttribute("part", "item-dismiss")
    dismissBtn.setAttribute("data-dismiss", "")
    dismissBtn.textContent = "✕"
    li.appendChild(dismissBtn)

    this._applyItemState(li, item)
    return li
  }

  _text(value) {
    const text = value !== undefined && value !== null ? String(value) : ""
    return text
  }

  /* The parts of an item element that change when it is read. */
  _applyItemState(li, item) {
    li.setAttribute("data-unread", item.read === true ? "false" : "true")

    const unreadPrefix = item.read === true ? "" : `${this._unreadLabel()}: `
    const timeStr = item.timestamp ? this._formatTime(item.timestamp) : ""
    const parts = [this._text(item.title), this._text(item.body), timeStr].filter((part) => part.length > 0)
    li.setAttribute("aria-label", `${unreadPrefix}${parts.join(". ")}`)

    const dismissBtn = li.querySelector(".nc-dismiss-btn")
    dismissBtn.setAttribute("aria-label", `${this._dismissLabel()}: ${this._text(item.title)}`)
    return
  }

  _groupItems(groupBy) {
    if (groupBy === "none") {
      return [{ label: null, items: this._items }]
    }

    if (groupBy === "category") {
      const map = new Map()
      for (const item of this._items) {
        const cat = item.category !== undefined && item.category !== null && String(item.category).length > 0
          ? String(item.category)
          : t("mj.notificationCenter.otherCategory")
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
    const yesterdayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1)

    const today = []
    const yesterday = []
    const older = []

    for (const item of this._items) {
      const d = item.timestamp !== undefined && item.timestamp !== null ? new Date(item.timestamp) : null
      if (d === null || isNaN(d.getTime()) === true) {
        older.push(item)
      } else if (d >= todayStart) {
        today.push(item)
      } else if (d >= yesterdayStart) {
        yesterday.push(item)
      } else {
        older.push(item)
      }
    }

    const groups = []
    if (today.length > 0) {
      groups.push({ label: capitalize(formatRelativeTime(0, "day")), items: today })
    }
    if (yesterday.length > 0) {
      groups.push({ label: capitalize(formatRelativeTime(-1, "day")), items: yesterday })
    }
    if (older.length > 0) {
      groups.push({ label: this.getAttribute("older-label") || t("mj.notificationCenter.older"), items: older })
    }
    return groups
  }

  /* Relative for the last day ("5 minutes ago"), a locale date before that. */
  _formatTime(timestamp) {
    const d = new Date(timestamp)
    if (isNaN(d.getTime()) === true) {
      return ""
    }

    const diffMs = Date.now() - d.getTime()
    const diffMin = Math.floor(diffMs / 60000)
    let text = ""

    if (diffMin < 1) {
      text = formatRelativeTime(0, "second")
    } else if (diffMin < 60) {
      text = formatRelativeTime(-diffMin, "minute")
    } else if (diffMin < 1440) {
      text = formatRelativeTime(-Math.floor(diffMin / 60), "hour")
    } else {
      text = d.toLocaleDateString(getLocale())
    }
    return text
  }

  _updateBadge() {
    const count = this.unreadCount
    if (this._badgeEl !== null) {
      this._badgeEl.textContent = String(count)
      this._badgeEl.setAttribute("aria-label", t("mj.notificationCenter.unreadCount", { count: count }))
      this._badgeEl.setAttribute("aria-hidden", count === 0 ? "true" : "false")
    }
    if (this._markAllBtn !== null) {
      this._markAllBtn.disabled = count === 0
    }
    if (this._clearAllBtn !== null) {
      this._clearAllBtn.disabled = this._items.length === 0
    }
    return
  }

  /* ----- events ----- */

  _itemIdOf(element) {
    const itemEl = element !== null ? element.closest(".nc-item") : null
    const id = itemEl !== null && itemEl._mjItemId !== undefined ? itemEl._mjItemId : null
    return id
  }

  _onClick(event) {
    const dismissBtn = event.target.closest("[data-dismiss]")
    if (dismissBtn !== null) {
      event.stopPropagation()
      this._dismissItem(this._itemIdOf(dismissBtn), true)
      return
    }

    const actionBtn = event.target.closest("[data-action]")
    if (actionBtn !== null && actionBtn.getRootNode() === this.shadowRoot) {
      const action = actionBtn.getAttribute("data-action")
      if (action === "mark-all-read") {
        this._markAllRead()
      } else if (action === "clear-all") {
        this._clearAll()
      }
      return
    }

    const id = this._itemIdOf(event.target)
    if (id !== null) {
      this._selectItem(id)
    }
    return
  }

  _onFocusIn(event) {
    const id = this._itemIdOf(event.target)
    if (id !== null) {
      this._selectedId = id
    }
    return
  }

  _onKeydown(event) {
    const item = event.target.closest(".nc-item")
    if (item === null) {
      return
    }

    /*
     * Keys pressed on the item's own Dismiss button belong to the button:
     * Enter / Space activate it like any button.
     */
    const onItem = event.target === item

    if (onItem === true && (event.key === "Delete" || event.key === "Backspace")) {
      event.preventDefault()
      this._dismissItem(item._mjItemId, true)
      return
    }

    if (onItem === true && (event.key === "Enter" || event.key === " ")) {
      event.preventDefault()
      this._selectItem(item._mjItemId)
      return
    }
    return
  }

  /* Mark one item read. Returns true when its state changed. */
  _markItemRead(id) {
    const item = this._items.find((entry) => entry.id === id)
    if (item === undefined || item.read === true) {
      return false
    }

    item.read = true

    /* Updated in place: the element (and focus on it) survives. */
    const element = this._itemEls.get(id)
    if (element !== undefined) {
      this._applyItemState(element, item)
    }
    this._updateBadge()
    this.emit("mj-notification-read", { item: item })
    return true
  }

  _selectItem(id) {
    const item = this._items.find((entry) => entry.id === id)
    if (item === undefined) {
      return
    }

    this._selectedId = id
    this._markItemRead(id)
    this.emit("mj-notification-select", { item: item })

    /* An item with a link navigates, like activating a link would. */
    const href = safeUrl(item.href, "")
    if (href.length > 0 && href !== "#") {
      window.location.assign(href)
    }
    return
  }

  /*
   * Remove one item. With `cancelable`, `mj-notification-dismiss` is fired
   * first and can veto it. Focus moves to the neighbouring item when it was
   * inside the list.
   */
  _dismissItem(id, cancelable) {
    const item = this._items.find((entry) => entry.id === id)
    if (item === undefined) {
      return false
    }

    if (cancelable === true) {
      const proceed = this.emit("mj-notification-dismiss", { item: item }, { cancelable: true })
      if (proceed === false) {
        return false
      }
    }

    /* The item after it in display order takes its place; else the one before. */
    const order = Array.from(this._listEl.querySelectorAll(".nc-item"))
    const element = this._itemEls.get(id)
    const position = element !== undefined ? order.indexOf(element) : -1
    let neighbour = null
    if (position >= 0) {
      neighbour = order[position + 1] || order[position - 1] || null
    }

    const active = deepActiveElement()
    const focusWasInList = active !== null && this._listEl.contains(active) === true

    this._items.splice(this._items.indexOf(item), 1)
    if (this._selectedId === id) {
      this._selectedId = neighbour !== null ? neighbour._mjItemId : null
    }

    /* A full rebuild also drops a group header that has no items left. */
    this._renderList()

    if (focusWasInList === true) {
      const target = neighbour !== null ? this._itemEls.get(neighbour._mjItemId) : undefined
      if (target !== undefined) {
        this._roving.focus(this._roving.items.indexOf(target))
      } else {
        this._listEl.setAttribute("tabindex", "-1")
        this._listEl.focus()
      }
    }
    return true
  }

  _markAllRead() {
    const count = this._items.filter((entry) => entry.read === false).length
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
    this._selectedId = null
    this._renderList()
    return
  }

  /* Scriptable API */

  get items() {
    return this._items
  }

  set items(value) {
    const list = Array.isArray(value) ? value.slice() : []
    const valid = list.filter((entry) => entry !== null && typeof entry === "object")
    for (const item of valid) {
      this._normalizeItem(item)
    }
    this._items = valid
    this._enforceMaxItems()
    if (this._listEl !== null) {
      this._renderList()
    }
    return
  }

  get unreadCount() {
    const count = this._items.filter((entry) => entry.read === false).length
    return count
  }

  /* The item that was focused or activated last, or null. */
  get selectedItem() {
    const item = this._items.find((entry) => entry.id === this._selectedId)
    return item !== undefined ? item : null
  }

  addItem(descriptor) {
    const source = descriptor !== null && typeof descriptor === "object" ? descriptor : {}
    const item = this._normalizeItem(Object.assign({ read: false }, source))

    const dupeIdx = this._items.findIndex((entry) => entry.id === item.id)
    if (dupeIdx >= 0) {
      console.error(`<mj-notification-center>: duplicate item id "${item.id}"`)
      return
    }

    this._items.unshift(item)
    this._enforceMaxItems()

    if (this._listEl !== null) {
      this._renderList()
    }
    announce(t("mj.notificationCenter.newNotification", { title: this._text(item.title) }), "polite")
    return
  }

  /* Mark one item read (fires mj-notification-read when it was unread). */
  markRead(id) {
    const changed = this._markItemRead(String(id))
    return changed
  }

  markAllRead() {
    this._markAllRead()
    return
  }

  /* Remove one item; fires the cancelable mj-notification-dismiss first. */
  dismiss(id) {
    const removed = this._dismissItem(String(id), true)
    return removed
  }

  /* Remove one item without asking (no event). */
  remove(id) {
    const removed = this._dismissItem(String(id), false)
    return removed
  }

  clearAll() {
    this._clearAll()
    return
  }
}
