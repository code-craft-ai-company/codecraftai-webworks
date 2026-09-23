/*
 * mjbreadcrumb.js
 *
 * <mj-breadcrumb> -- ordered hierarchy trail with <nav> landmark.
 * Renders an <ol> of links. The last item (or item with `current` attribute)
 * receives aria-current="page". Supports collapsing intermediate items.
 *
 * WAI-ARIA: nav landmark; ol for ordered items; aria-current="page" on current.
 */

import { MjElement, nextId } from "../core/mjelement.js";
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
.item {
  display: flex;
  align-items: center;
}
.item a {
  color: var(--mj-breadcrumb-link-color, var(--mj-accent));
  text-decoration: none;
}
.item a:hover { text-decoration: underline; }
.item a:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
  border-radius: 2px;
}
.item[data-current] span {
  color: var(--mj-breadcrumb-current-color, var(--mj-text));
  font-weight: var(--mj-font-weight-medium);
}
.separator {
  color: var(--mj-breadcrumb-separator-color, var(--mj-text-muted));
  padding-inline: var(--mj-breadcrumb-separator-gap, var(--mj-space-2));
  user-select: none;
}
.ellipsis { display: flex; align-items: center; }
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

export class MjBreadcrumb extends MjElement {
  static tagName = "mj-breadcrumb";
  static styles = STYLES;
  static watched = ["nav-label", "separator", "max-visible", "always-show-last"];

  constructor() {
    super();
    this._collapsed = true;
    this._navId = nextId("mj-breadcrumb-nav");
  }

  render() {
    const navLabel = this.getAttribute("nav-label") || t("mj.breadcrumb.navLabel") || "Breadcrumb";

    const markup = `
      <nav aria-label="${navLabel}" id="${this._navId}">
        <ol class="list" part="list">
          <slot></slot>
        </ol>
      </nav>
    `;
    return markup
  }

  afterRender() {
    this._list = this.$(".list");
    this._slot = this.shadowRoot.querySelector("slot");

    this.listen(this._slot, "slotchange", this._onSlotChange.bind(this));
    this._buildList();
    return
  }

  _onSlotChange() {
    this._buildList();
    return
  }

  _buildList() {
    const existing = this._list.querySelectorAll(".item, .ellipsis-item");
    existing.forEach(function(el) { el.remove(); });

    const items = this._slot.assignedElements({ flatten: true });
    if (items.length === 0) {
      return
    }

    const separator = this.getAttribute("separator") || "/";
    const maxVisible = parseInt(this.getAttribute("max-visible") || "0", 10);
    const alwaysShowLast = parseInt(this.getAttribute("always-show-last") || "1", 10);

    let visibleItems = items;
    let hiddenItems = [];
    let showEllipsis = false;

    if (maxVisible > 0 && items.length > maxVisible && this._collapsed === true) {
      const firstCount = 1;
      const lastCount = alwaysShowLast;
      const firstItems = items.slice(0, firstCount);
      hiddenItems = items.slice(firstCount, items.length - lastCount);
      const lastItems = items.slice(items.length - lastCount);
      visibleItems = firstItems.concat(lastItems);
      showEllipsis = hiddenItems.length > 0;
    }

    const lastItem = items[items.length - 1];

    for (let index = 0; index < visibleItems.length; index = index + 1) {
      const item = visibleItems[index];
      const isCurrent = item === lastItem || item.hasAttribute("current");
      const li = document.createElement("li");
      li.className = "item";
      li.setAttribute("part", "item");

      if (isCurrent === true) {
        li.dataset.current = "";
        li.setAttribute("part", "item current");
        const anchor = item.querySelector("a");
        if (anchor !== null) {
          anchor.removeAttribute("href");
          anchor.setAttribute("aria-current", "page");
          anchor.setAttribute("role", "link");
        }
      }

      li.appendChild(item);

      const insertionIndex = showEllipsis === true && index === 1
        ? null
        : index;

      if (showEllipsis === true && index === 1) {
        const ellipsisLi = this._buildEllipsis(hiddenItems.length);
        if (index > 0) {
          this._list.appendChild(this._buildSeparator(separator));
        }
        this._list.appendChild(ellipsisLi);
        this._list.appendChild(this._buildSeparator(separator));
      } else if (index > 0) {
        this._list.appendChild(this._buildSeparator(separator));
      }

      this._list.appendChild(li);
    }
    return
  }

  _buildSeparator(sep) {
    const span = document.createElement("span");
    span.className = "separator";
    span.setAttribute("part", "separator");
    span.setAttribute("aria-hidden", "true");
    span.textContent = sep;
    return span
  }

  _buildEllipsis(count) {
    const li = document.createElement("li");
    li.className = "ellipsis-item";
    li.setAttribute("part", "ellipsis");

    const expandLabel = t("mj.breadcrumb.expand", { count: count }) || `Show ${count} hidden breadcrumbs`;
    const btn = document.createElement("button");
    btn.className = "expand-btn";
    btn.setAttribute("part", "expand-btn");
    btn.setAttribute("aria-label", expandLabel);
    btn.textContent = "…";

    this.listen(btn, "click", this._onExpand.bind(this));
    li.appendChild(btn);
    return li
  }

  _onExpand() {
    const proceed = this.emit("mj-breadcrumb-expand", {}, { cancelable: true });
    if (proceed === true) {
      this._collapsed = false;
      this._buildList();
    }
    return
  }

  get items() {
    const slot = this.shadowRoot.querySelector("slot");
    if (slot === null) {
      return []
    }
    return slot.assignedElements({ flatten: true })
  }

  get collapsed() {
    return this._collapsed
  }

  set collapsed(value) {
    this._collapsed = value === true;
    this._buildList();
    return
  }
}
