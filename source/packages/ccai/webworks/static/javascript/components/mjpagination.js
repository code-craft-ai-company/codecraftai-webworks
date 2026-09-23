/*
 * mjpagination.js
 *
 * <mj-pagination> -- page navigation component.
 * Renders Previous/Next and numbered page buttons inside a <nav> landmark.
 * Supports ellipsis for large page counts, compact and simple variants.
 *
 * The page count comes from `total-pages` when it is set; otherwise it is
 * derived from `total-items` and `page-size`, so a list view that only knows
 * its row count still gets working page buttons. When everything fits on one
 * page the pager hides itself (the host carries the read-only `single-page`
 * state attribute) unless `show-single-page` is set.
 *
 * WAI-ARIA: nav landmark; aria-current="page" on current page button.
 */

import { MjElement } from "../core/mjelement.js";
import { t } from "../core/intl.js";

const DEFAULT_PAGE_SIZE = 10;

/*
 * The single-page rule is !important because consumers commonly give the host
 * a layout display (e.g. "display: flex" on a pager class); an important
 * declaration inside the shadow tree wins over the page's normal ones.
 */
const STYLES = `
:host { display: block; }
:host([single-page]:not([show-single-page])) { display: none !important; }

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
  flex-wrap: wrap;
  list-style: none;
  margin: 0; padding: 0;
  gap: var(--mj-pagination-btn-gap, var(--mj-space-1));
}
.page-btn,
.ctrl-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--mj-space-1);
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

/*
 * Parse a non-negative integer attribute value. Returns null when the value
 * is absent or not a usable number, so callers can tell "unset" from "0".
 */
function parseCount(raw) {
  if (raw === null || raw === undefined) {
    return null
  }
  const parsed = parseInt(raw, 10);
  if (Number.isNaN(parsed) === true || parsed < 0) {
    return null
  }
  return parsed
}

export class MjPagination extends MjElement {
  static tagName = "mj-pagination";
  static styles = STYLES;
  static watched = [
    "page", "total-pages", "total-items", "page-size", "sibling-count",
    "boundary-count", "variant", "show-summary", "hide-summary",
    "show-single-page", "nav-label", "disabled"
  ];

  render() {
    const markup = `
      <nav part="nav">
        <div class="root" part="root"></div>
      </nav>
    `;
    return markup
  }

  afterRender() {
    this._nav = this.$("nav");
    this._root = this.$(".root");
    this.listen(this._root, "click", this._onRootClick.bind(this));
    this._rebuildUI();
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._root !== undefined && this._root !== null) {
      this._rebuildUI();
    }
    return
  }

  /* ----- derived state ----- */

  _pageSize() {
    const parsed = parseCount(this.getAttribute("page-size"));
    const rtnval = parsed !== null && parsed > 0 ? parsed : DEFAULT_PAGE_SIZE;
    return rtnval
  }

  _totalItems() {
    const rtnval = parseCount(this.getAttribute("total-items"));
    return rtnval
  }

  /*
   * The page count: an explicit `total-pages` wins; otherwise it is derived
   * from `total-items` / `page-size`. Never less than 1.
   */
  _totalPages() {
    const explicit = parseCount(this.getAttribute("total-pages"));
    if (explicit !== null) {
      return Math.max(1, explicit)
    }
    const totalItems = this._totalItems();
    if (totalItems !== null) {
      return Math.max(1, Math.ceil(totalItems / this._pageSize()))
    }
    return 1
  }

  /* The current page, clamped into [1, totalPages]. */
  _currentPage(totalPages) {
    const parsed = parseInt(this.getAttribute("page") || "1", 10);
    const requested = Number.isNaN(parsed) === true ? 1 : parsed;
    const rtnval = Math.min(Math.max(1, requested), totalPages);
    return rtnval
  }

  _summaryVisible() {
    if (this.hasAttribute("show-summary") === true) {
      return true
    }
    const rtnval = this._totalItems() !== null && this.hasAttribute("hide-summary") === false;
    return rtnval
  }

  /* ----- rendering ----- */

  _rebuildUI() {
    this._root.replaceChildren();

    const totalPages = this._totalPages();
    const page = this._currentPage(totalPages);
    const variant = this.getAttribute("variant") || "full";
    const disabled = this.hasAttribute("disabled");

    this.reflectBoolean("single-page", totalPages <= 1);
    this._nav.setAttribute("aria-label", this.getAttribute("nav-label") || t("mj.pagination.navLabel"));

    const prevBtn = this._createCtrlBtn("prev", page - 1, page <= 1 || disabled === true);
    this._root.appendChild(prevBtn);

    if (variant === "compact") {
      const label = document.createElement("span");
      label.className = "compact-label";
      label.setAttribute("part", "compact-label");
      label.textContent = t("mj.pagination.pageOf", { page: page, total: totalPages });
      this._root.appendChild(label);
    } else if (variant !== "simple") {
      const ol = this._buildPageList(page, totalPages, disabled);
      this._root.appendChild(ol);
    }

    const nextBtn = this._createCtrlBtn("next", page + 1, page >= totalPages || disabled === true);
    this._root.appendChild(nextBtn);

    if (this._summaryVisible() === true) {
      const summary = this._buildSummary(page);
      this._root.appendChild(summary);
    }
    return
  }

  _createCtrlBtn(action, targetPage, isDisabled) {
    const btn = document.createElement("button");
    btn.className = "ctrl-btn";
    btn.setAttribute("part", action);
    btn.setAttribute("type", "button");

    const arrow = document.createElement("span");
    arrow.setAttribute("aria-hidden", "true");
    arrow.textContent = action === "prev" ? "←" : "→";
    const text = document.createElement("span");
    text.textContent = action === "prev" ? t("mj.pagination.previous") : t("mj.pagination.next");
    if (action === "prev") {
      btn.append(arrow, text);
    } else {
      btn.append(text, arrow);
    }

    if (isDisabled === true) {
      btn.setAttribute("disabled", "");
      btn.setAttribute("aria-disabled", "true");
    } else {
      btn.dataset.page = String(targetPage);
    }
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
        btn.setAttribute("aria-label", t("mj.pagination.currentPageLabel", { page: p }));
      } else {
        btn.setAttribute("aria-label", t("mj.pagination.pageLabel", { page: p }));
      }

      btn.textContent = String(p);

      if (disabled === false) {
        btn.dataset.page = String(p);
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
    const totalItems = this._totalItems() || 0;
    const pageSize = this._pageSize();
    const from = totalItems === 0 ? 0 : (page - 1) * pageSize + 1;
    const to = Math.min(page * pageSize, totalItems);
    const div = document.createElement("div");
    div.className = "summary";
    div.setAttribute("part", "summary");
    div.textContent = t("mj.pagination.summary", { from: from, to: to, total: totalItems });
    return div
  }

  /* ----- interaction ----- */

  /*
   * One delegated listener for every button: page and Previous/Next buttons
   * carry their target page in data-page; disabled ones carry none.
   */
  _onRootClick(event) {
    const target = event.target instanceof Element ? event.target.closest("button") : null;
    if (target === null || target.dataset.page === undefined) {
      return
    }
    const page = parseInt(target.dataset.page, 10);
    if (Number.isNaN(page) === false) {
      this._navigateTo(page);
    }
    return
  }

  _navigateTo(page) {
    const totalPages = this._totalPages();
    const current = this._currentPage(totalPages);
    const next = Math.min(Math.max(1, page), totalPages);
    if (next === current) {
      return
    }
    const proceed = this.emit("mj-pagination-change", {
      page: next,
      previousPage: current,
      pageSize: this._pageSize()
    }, { cancelable: true });
    if (proceed === true) {
      this.setAttribute("page", String(next));
    }
    return
  }

  /* ----- scriptable API ----- */

  get totalPages() {
    return this._totalPages()
  }

  get hasPrevious() {
    return this._currentPage(this._totalPages()) > 1
  }

  get hasNext() {
    const total = this._totalPages();
    return this._currentPage(total) < total
  }

  get pageRange() {
    const page = this._currentPage(this._totalPages());
    const pageSize = this._pageSize();
    const first = (page - 1) * pageSize;
    const last = first + pageSize - 1;
    return [first, last]
  }
}
