/*
 * mjpagination.js
 *
 * <mj-pagination> -- page navigation component.
 * Renders Previous/Next and numbered page buttons inside a <nav> landmark.
 * Supports ellipsis for large page counts, compact and simple variants.
 *
 * WAI-ARIA: nav landmark; aria-current="page" on current page button.
 */

import { MjElement } from "../core/mjelement.js";
import { t } from "../core/intl.js";

const STYLES = `
:host { display: block; }

nav {
  font-size: var(--mj-pagination-font-size, var(--mj-font-size-sm));
}
.root {
  display: flex;
  align-items: center;
  gap: var(--mj-space-3);
  flex-wrap: wrap;
}
.page-list {
  display: flex;
  align-items: center;
  list-style: none;
  margin: 0; padding: 0;
  gap: var(--mj-pagination-btn-gap, var(--mj-space-1));
}
.page-btn,
.ctrl-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: var(--mj-pagination-btn-size, 36px);
  height: var(--mj-pagination-btn-size, 36px);
  padding: 0 var(--mj-space-2);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-pagination-btn-radius, var(--mj-radius-sm));
  background: var(--mj-surface);
  color: var(--mj-text);
  cursor: pointer;
  font: inherit;
  font-size: var(--mj-pagination-font-size, var(--mj-font-size-sm));
  transition: background var(--mj-motion-fast) var(--mj-motion-ease),
              border-color var(--mj-motion-fast) var(--mj-motion-ease);
  white-space: nowrap;
}
.page-btn:hover:not([aria-disabled="true"]),
.ctrl-btn:hover:not([disabled]) { background: var(--mj-bg-muted); }
.page-btn:focus-visible,
.ctrl-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.page-btn[aria-current="page"] {
  background: var(--mj-pagination-current-bg, var(--mj-accent));
  color: var(--mj-pagination-current-color, var(--mj-text-on-accent));
  border-color: var(--mj-accent);
  font-weight: var(--mj-font-weight-medium);
}
.ctrl-btn[disabled],
.ctrl-btn[aria-disabled="true"] { opacity: 0.45; cursor: not-allowed; }
.ellipsis { display: flex; align-items: center; padding: 0 var(--mj-space-2); color: var(--mj-text-muted); }
.compact-label { color: var(--mj-text-muted); white-space: nowrap; }
.summary { color: var(--mj-text-muted); font-size: var(--mj-pagination-font-size, var(--mj-font-size-sm)); }
`;

export class MjPagination extends MjElement {
  static tagName = "mj-pagination";
  static styles = STYLES;
  static watched = ["page", "total-pages", "total-items", "page-size", "sibling-count", "boundary-count", "variant", "show-summary", "nav-label", "disabled"];

  render() {
    const navLabel = this.getAttribute("nav-label") || t("mj.pagination.navLabel") || "Pagination";
    const markup = `
      <nav aria-label="${navLabel}">
        <div class="root" part="root"></div>
      </nav>
    `;
    return markup
  }

  afterRender() {
    this._root = this.$(".root");
    this._rebuildUI();
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._root !== undefined && this._root !== null) {
      this._rebuildUI();
    }
    return
  }

  _rebuildUI() {
    this._root.innerHTML = "";

    const page = Math.max(1, parseInt(this.getAttribute("page") || "1", 10));
    const totalPages = Math.max(1, parseInt(this.getAttribute("total-pages") || "1", 10));
    const variant = this.getAttribute("variant") || "full";
    const disabled = this.hasAttribute("disabled");
    const showSummary = this.hasAttribute("show-summary");
    const prevLabel = t("mj.pagination.previous") || "Previous";
    const nextLabel = t("mj.pagination.next") || "Next";

    const prevBtn = this._createCtrlBtn(prevLabel, "prev", page <= 1 || disabled === true);
    this._root.appendChild(prevBtn);

    if (variant === "compact") {
      const label = document.createElement("span");
      label.className = "compact-label";
      label.setAttribute("part", "compact-label");
      label.textContent = `Page ${page} of ${totalPages}`;
      this._root.appendChild(label);
    } else if (variant !== "simple") {
      const ol = this._buildPageList(page, totalPages, disabled);
      this._root.appendChild(ol);
    }

    const nextBtn = this._createCtrlBtn(nextLabel, "next", page >= totalPages || disabled === true);
    this._root.appendChild(nextBtn);

    if (showSummary === true) {
      const summary = this._buildSummary(page);
      this._root.appendChild(summary);
    }
    return
  }

  _createCtrlBtn(label, action, isDisabled) {
    const btn = document.createElement("button");
    btn.className = "ctrl-btn";
    btn.setAttribute("part", action);
    btn.setAttribute("type", "button");
    btn.textContent = action === "prev" ? `← ${label}` : `${label} →`;
    if (isDisabled === true) {
      btn.setAttribute("disabled", "");
      btn.setAttribute("aria-disabled", "true");
    }
    this.listen(btn, "click", () => {
      if (isDisabled === true) {
        return
      }
      const page = parseInt(this.getAttribute("page") || "1", 10);
      const to = action === "prev" ? page - 1 : page + 1;
      this._navigateTo(to);
    });
    return btn
  }

  _buildPageList(currentPage, totalPages, disabled) {
    const siblingCount = parseInt(this.getAttribute("sibling-count") || "1", 10);
    const boundaryCount = parseInt(this.getAttribute("boundary-count") || "1", 10);
    const pages = this._computePageRange(currentPage, totalPages, siblingCount, boundaryCount);

    const ol = document.createElement("ol");
    ol.className = "page-list";
    ol.setAttribute("part", "page-list");

    let prevPage = null;
    for (let i = 0; i < pages.length; i = i + 1) {
      const p = pages[i];

      if (prevPage !== null && p > prevPage + 1) {
        const ellipsisLi = document.createElement("li");
        ellipsisLi.setAttribute("part", "ellipsis");
        const ellipsis = document.createElement("span");
        ellipsis.className = "ellipsis";
        ellipsis.setAttribute("aria-hidden", "true");
        ellipsis.textContent = "…";
        ellipsisLi.appendChild(ellipsis);
        ol.appendChild(ellipsisLi);
      }

      const li = document.createElement("li");
      li.setAttribute("part", "page-item");
      const btn = document.createElement("button");
      btn.className = "page-btn";
      btn.setAttribute("part", "page-btn");
      btn.setAttribute("type", "button");

      const isCurrent = p === currentPage;
      if (isCurrent === true) {
        btn.setAttribute("aria-current", "page");
        btn.setAttribute("aria-label", `Page ${p}, current`);
      } else {
        btn.setAttribute("aria-label", `Page ${p}`);
      }

      btn.textContent = String(p);

      if (disabled === false) {
        const pageNum = p;
        this.listen(btn, "click", () => {
          this._navigateTo(pageNum);
        });
      } else {
        btn.setAttribute("aria-disabled", "true");
      }

      li.appendChild(btn);
      ol.appendChild(li);
      prevPage = p;
    }
    return ol
  }

  _computePageRange(current, total, siblings, boundary) {
    const pages = new Set();

    for (let i = 1; i <= Math.min(boundary, total); i = i + 1) {
      pages.add(i);
    }
    for (let i = Math.max(total - boundary + 1, 1); i <= total; i = i + 1) {
      pages.add(i);
    }
    for (let i = Math.max(1, current - siblings); i <= Math.min(total, current + siblings); i = i + 1) {
      pages.add(i);
    }

    const sorted = Array.from(pages).sort(function(a, b) { return a - b; });
    return sorted
  }

  _buildSummary(page) {
    const totalItems = parseInt(this.getAttribute("total-items") || "0", 10);
    const pageSize = parseInt(this.getAttribute("page-size") || "10", 10);
    const from = (page - 1) * pageSize + 1;
    const to = Math.min(page * pageSize, totalItems);
    const div = document.createElement("div");
    div.className = "summary";
    div.setAttribute("part", "summary");
    div.textContent = `Showing ${from}–${to} of ${totalItems}`;
    return div
  }

  _navigateTo(page) {
    const current = parseInt(this.getAttribute("page") || "1", 10);
    const pageSize = parseInt(this.getAttribute("page-size") || "10", 10);
    const proceed = this.emit("mj-pagination-change", {
      page: page,
      previousPage: current,
      pageSize: pageSize
    }, { cancelable: true });
    if (proceed === true) {
      this.setAttribute("page", String(page));
    }
    return
  }

  get hasPrevious() {
    return parseInt(this.getAttribute("page") || "1", 10) > 1
  }

  get hasNext() {
    const page = parseInt(this.getAttribute("page") || "1", 10);
    const total = parseInt(this.getAttribute("total-pages") || "1", 10);
    return page < total
  }

  get pageRange() {
    const page = parseInt(this.getAttribute("page") || "1", 10);
    const pageSize = parseInt(this.getAttribute("page-size") || "10", 10);
    const first = (page - 1) * pageSize;
    const last = first + pageSize - 1;
    return [first, last]
  }
}
