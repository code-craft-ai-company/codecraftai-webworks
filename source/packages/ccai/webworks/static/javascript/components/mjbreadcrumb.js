/*
 * mjbreadcrumb.js
 *
 * <mj-breadcrumb> -- ordered hierarchy trail with <nav> landmark.
 * Renders an <ol> with one <li> per crumb. The crumbs stay in the light DOM
 * (the author's elements are never moved or cloned): each one is projected
 * into its own <li> through a named slot the component assigns. The last
 * item (or the item with the `current` attribute) receives
 * aria-current="page". Supports collapsing intermediate items.
 *
 * WAI-ARIA: nav landmark; ol for ordered items; aria-current="page" on current.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";

const STYLES = `
:host { display: block; }

nav { font-size: var(--mj-breadcrumb-font-size, var(--mj-font-size-sm)); }

.list {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  list-style: none;
  margin: 0;
  padding: 0;
  gap: 0;
}
.item,
.ellipsis-item {
  display: flex;
  align-items: center;
}
::slotted(a) {
  color: var(--mj-breadcrumb-link-color, var(--mj-accent));
  text-decoration: none;
}
::slotted(a[href]:hover) { text-decoration: underline; }
::slotted(a:focus-visible) {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
  border-radius: var(--mj-radius-sm);
}
.item[data-current] ::slotted(*) {
  color: var(--mj-breadcrumb-current-color, var(--mj-text));
  font-weight: var(--mj-font-weight-medium);
}
.separator {
  display: inline-flex;
  align-items: center;
  color: var(--mj-breadcrumb-separator-color, var(--mj-text-muted));
  padding-inline: var(--mj-breadcrumb-separator-gap, var(--mj-space-2));
  user-select: none;
}
.expand-btn {
  background: none; border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-sm);
  padding: 0 var(--mj-space-2); cursor: pointer;
  font: inherit; font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
  min-height: var(--mj-control-height-sm);
}
.expand-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.expand-btn:hover { background: var(--mj-bg-muted); }
`;

/* Name of the light-DOM slot whose content is cloned into every separator. */
const SEPARATOR_SLOT = "separator";

/* Slot-name prefix for visible crumbs, and the name given to collapsed ones. */
const CRUMB_SLOT_PREFIX = "mj-crumb-";
const HIDDEN_CRUMB_SLOT = "mj-crumb-hidden";

export class MjBreadcrumb extends MjElement {
  static tagName = "mj-breadcrumb";
  static styles = STYLES;
  static watched = ["nav-label", "separator", "max-visible", "always-show-first", "always-show-last"];

  constructor() {
    super()
    this._collapsed = true
    this._navId = nextId("mj-breadcrumb-nav")

    /* href values removed from current-page anchors, restored when they stop being current. */
    this._savedHrefs = new WeakMap()

    /* Elements this component put aria-current on. */
    this._markedCurrent = []
  }

  render() {
    const markup = html`
      <nav aria-label="${this._resolveNavLabel()}" id="${this._navId}">
        <ol class="list" part="list"></ol>
      </nav>
    `
    return markup
  }

  afterRender() {
    this._nav = this.$("nav")
    this._list = this.$(".list")

    this.listen(this._list, "click", this._onListClick.bind(this))
    this.listen(this, "click", this._onHostClick.bind(this))

    /*
     * Crumbs are re-evaluated when children are added or removed and when a
     * `current` attribute changes. The component's own writes (slot, href,
     * aria-current) are not observed, so a rebuild never triggers another.
     */
    const observer = new MutationObserver(() => {
      this._buildList()
    })
    observer.observe(this, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["current"]
    })
    this.onTeardown(() => {
      observer.disconnect()
    })

    this._buildList()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._list === undefined || this._list === null) {
      return
    }

    if (name === "nav-label") {
      this._nav.setAttribute("aria-label", this._resolveNavLabel())
    } else if (
      name === "separator" ||
      name === "max-visible" ||
      name === "always-show-first" ||
      name === "always-show-last"
    ) {
      this._buildList()
    }
    return
  }

  _resolveNavLabel() {
    let navLabel = this.getAttribute("nav-label")
    if (navLabel === null || navLabel.length === 0) {
      navLabel = t("mj.breadcrumb.navLabel")
    }
    return navLabel
  }

  /* The crumb elements: every light-DOM child except separator-slot content. */
  _crumbElements() {
    const crumbs = []
    const children = Array.from(this.children)

    for (let index = 0; index < children.length; index = index + 1) {
      const child = children[index]
      if (child.getAttribute("slot") !== SEPARATOR_SLOT) {
        crumbs.push(child)
      }
    }
    return crumbs
  }

  /* The author's custom separator content (slot="separator"), or null. */
  _separatorTemplate() {
    let template = null
    const children = Array.from(this.children)

    for (let index = 0; index < children.length; index = index + 1) {
      const child = children[index]
      if (template === null && child.getAttribute("slot") === SEPARATOR_SLOT) {
        template = child
      }
    }
    return template
  }

  /* The anchor of a crumb: the crumb itself or the first anchor inside it. */
  _anchorOf(item) {
    let anchor = null
    if (item.matches("a") === true) {
      anchor = item
    } else {
      anchor = item.querySelector("a")
    }
    return anchor
  }

  _readCount(name, fallback) {
    let count = fallback
    const text = this.getAttribute(name)
    if (text !== null) {
      const parsed = parseInt(text, 10)
      if (Number.isNaN(parsed) === false && parsed >= 0) {
        count = parsed
      }
    }
    return count
  }

  /*
   * Split the crumbs into the visible ones and the ones hidden behind the
   * ellipsis. `leading` is the number of visible crumbs before the ellipsis.
   *
   * A collapsed trail shows `max-visible` crumbs (the ellipsis is not
   * counted): the first crumb unless `always-show-first="false"`, then the
   * trailing crumbs -- at least `always-show-last` of them, and as many more
   * as `max-visible` leaves room for, since the crumbs nearest the current
   * page are the most useful. When the guaranteed first and last crumbs
   * alone exceed `max-visible`, the guarantees win.
   */
  _partition(items) {
    const maxVisible = this._readCount("max-visible", 0)
    const lastCount = this._readCount("always-show-last", 1)
    const firstCount = this.getAttribute("always-show-first") === "false" ? 0 : 1
    const trailingCount = Math.max(lastCount, maxVisible - firstCount)

    const partition = { visible: items, hidden: [], leading: 0 }

    const canCollapse = maxVisible > 0 && items.length > maxVisible && this._collapsed === true
    if (canCollapse === true && firstCount + trailingCount < items.length) {
      const firstItems = items.slice(0, firstCount)
      const lastItems = items.slice(items.length - trailingCount)
      partition.hidden = items.slice(firstCount, items.length - trailingCount)
      partition.visible = firstItems.concat(lastItems)
      partition.leading = firstCount
    }
    return partition
  }

  /* Undo the current-page marking of the previous build. */
  _clearCurrentMarks() {
    for (let index = 0; index < this._markedCurrent.length; index = index + 1) {
      const element = this._markedCurrent[index]
      element.removeAttribute("aria-current")

      const savedHref = this._savedHrefs.get(element)
      if (savedHref !== undefined) {
        element.setAttribute("href", savedHref)
        this._savedHrefs.delete(element)
      }
    }
    this._markedCurrent = []
    return
  }

  /*
   * Mark a crumb as the current page: aria-current="page" on its anchor (or
   * on the crumb itself when it holds no anchor) and no href, so it is not
   * an interactive link. The href is remembered and restored by
   * `_clearCurrentMarks` when the crumb stops being current.
   */
  _markCurrent(item) {
    const anchor = this._anchorOf(item)
    const target = anchor !== null ? anchor : item

    if (anchor !== null && anchor.hasAttribute("href") === true) {
      this._savedHrefs.set(anchor, anchor.getAttribute("href"))
      anchor.removeAttribute("href")
    }

    target.setAttribute("aria-current", "page")
    this._markedCurrent.push(target)
    return
  }

  _buildList() {
    if (this._list === undefined || this._list === null) {
      return
    }

    this._list.textContent = ""
    this._clearCurrentMarks()

    const items = this._crumbElements()
    const partition = this._partition(items)

    /* An explicit `current` wins; otherwise the last crumb is the current page. */
    const explicitCurrent = items.filter((item) => item.hasAttribute("current") === true)
    const lastItem = items.length > 0 ? items[items.length - 1] : null

    for (let index = 0; index < partition.hidden.length; index = index + 1) {
      this._assignSlot(partition.hidden[index], HIDDEN_CRUMB_SLOT)
    }

    for (let index = 0; index < partition.visible.length; index = index + 1) {
      const item = partition.visible[index]

      if (partition.hidden.length > 0 && index === partition.leading) {
        const ellipsisLi = this._buildEllipsis(partition.hidden.length, this._list.children.length > 0)
        this._list.appendChild(ellipsisLi)
      }

      let isCurrent = item === lastItem
      if (explicitCurrent.length > 0) {
        isCurrent = explicitCurrent.indexOf(item) >= 0
      }

      const slotName = `${CRUMB_SLOT_PREFIX}${index}`
      const li = document.createElement("li")
      li.className = "item"
      li.setAttribute("part", "item")

      if (this._list.children.length > 0) {
        li.appendChild(this._buildSeparator())
      }

      if (isCurrent === true) {
        li.dataset.current = ""
        li.setAttribute("part", "item current")
        this._markCurrent(item)
      }

      const slot = document.createElement("slot")
      slot.setAttribute("name", slotName)
      li.appendChild(slot)

      this._assignSlot(item, slotName)
      this._list.appendChild(li)
    }
    return
  }

  _assignSlot(item, slotName) {
    if (item.getAttribute("slot") !== slotName) {
      item.setAttribute("slot", slotName)
    }
    return
  }

  /*
   * A separator is decorative: the author's slot="separator" content when
   * there is one (cloned, because one element cannot be projected between
   * every pair of crumbs), otherwise the `separator` attribute text.
   */
  _buildSeparator() {
    const span = document.createElement("span")
    span.className = "separator"
    span.setAttribute("part", "separator")
    span.setAttribute("aria-hidden", "true")

    const template = this._separatorTemplate()
    if (template !== null) {
      const copy = template.cloneNode(true)
      copy.removeAttribute("slot")
      copy.removeAttribute("id")
      span.appendChild(copy)
    } else {
      const separator = this.getAttribute("separator")
      span.textContent = separator !== null && separator.length > 0 ? separator : "/"
    }
    return span
  }

  _buildEllipsis(count, withSeparator) {
    const li = document.createElement("li")
    li.className = "ellipsis-item"
    li.setAttribute("part", "ellipsis")

    if (withSeparator === true) {
      li.appendChild(this._buildSeparator())
    }

    const btn = document.createElement("button")
    btn.type = "button"
    btn.className = "expand-btn"
    btn.setAttribute("part", "expand-btn")
    btn.setAttribute("aria-label", t("mj.breadcrumb.expand", { count: count }))
    btn.textContent = "…"

    li.appendChild(btn)
    return li
  }

  _onListClick(event) {
    const button = event.target.closest(".expand-btn")
    if (button !== null) {
      this._onExpand()
    }
    return
  }

  _onExpand() {
    const proceed = this.emit("mj-breadcrumb-expand", {}, { cancelable: true })
    if (proceed === true) {
      const revealed = this._partition(this._crumbElements()).hidden

      this._collapsed = false
      this._buildList()

      /* The expand button is gone: move focus to the first revealed crumb. */
      if (revealed.length > 0) {
        const anchor = this._anchorOf(revealed[0])
        const target = anchor !== null ? anchor : revealed[0]
        target.focus()
      }
    }
    return
  }

  /*
   * A click on a crumb link announces `mj-breadcrumb-navigate` first, so a
   * client-side router can cancel the event and handle the navigation.
   */
  _onHostClick(event) {
    if (event.defaultPrevented === true || !(event.target instanceof Element)) {
      return
    }

    const anchor = event.target.closest("a[href]")
    if (anchor === null || this.contains(anchor) === false) {
      return
    }

    const items = this._crumbElements()
    let clickedIndex = -1
    for (let index = 0; index < items.length; index = index + 1) {
      if (clickedIndex === -1 && items[index].contains(anchor) === true) {
        clickedIndex = index
      }
    }

    if (clickedIndex >= 0) {
      const proceed = this.emit(
        "mj-breadcrumb-navigate",
        { item: items[clickedIndex], href: anchor.getAttribute("href"), index: clickedIndex },
        { cancelable: true }
      )
      if (proceed === false) {
        event.preventDefault()
      }
    }
    return
  }

  get items() {
    const crumbs = this._crumbElements()
    return crumbs
  }

  get collapsed() {
    return this._collapsed
  }

  set collapsed(value) {
    this._collapsed = value === true
    this._buildList()
    return
  }
}
