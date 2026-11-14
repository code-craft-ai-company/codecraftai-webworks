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
 * With `href-template` (e.g. "/results?page={page}") the page controls are
 * real links; `show-page-size` adds a page-size selector. The UI is rebuilt on
 * every change and keyboard focus is put back on the equivalent control.
 *
 * WAI-ARIA: nav landmark; aria-current="page" on current page button.
 */

import { MjElement } from "../core/mjelement.js";
import { safeUrl } from "../core/html.js";
import { t } from "../core/intl.js";

const DEFAULT_PAGE_SIZE = 10;
const DEFAULT_PAGE_SIZE_OPTIONS = [10, 25, 50, 100];

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
.page-btn,
.ctrl-btn { box-sizing: border-box; text-decoration: none; }
.ctrl-btn[disabled],
.ctrl-btn[aria-disabled="true"],
.page-btn[aria-disabled="true"] { opacity: 0.45; cursor: not-allowed; }
/* The arrows follow the reading direction. */
.arrow { display: inline-block; }
:host(:dir(rtl)) .arrow { transform: scaleX(-1); }
.page-size {
  display: inline-flex;
  align-items: center;
  gap: var(--mj-space-2);
  color: var(--mj-text-muted);
}
.page-size select {
  height: var(--mj-pagination-btn-size, 36px);
  padding: 0 var(--mj-space-2);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-pagination-btn-radius, var(--mj-radius-sm));
  background: var(--mj-surface);
  color: var(--mj-text);
  font: inherit;
}
.page-size select:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
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
  const parsed = parseInt(raw, 10)
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
    "show-single-page", "nav-label", "disabled", "href-template",
    "show-page-size", "page-size-options"
  ];

  render() {
    const markup = `
      <nav part="nav">
        <div class="root" part="root"></div>
      </nav>
    `
    return markup
  }

  afterRender() {
    this._nav = this.$("nav")
    this._root = this.$(".root")
    this.listen(this._root, "click", this._onRootClick.bind(this))
    this.listen(this._root, "change", this._onRootChange.bind(this))
    this._rebuildUI()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._root !== undefined && this._root !== null) {
      this._rebuildUI()
    }
    return
  }

  /* ----- derived state ----- */

  _pageSize() {
    const parsed = parseCount(this.getAttribute("page-size"))
    const rtnval = parsed !== null && parsed > 0 ? parsed : DEFAULT_PAGE_SIZE
    return rtnval
  }

  _totalItems() {
    const rtnval = parseCount(this.getAttribute("total-items"))
    return rtnval
  }

  /*
   * The page count: an explicit `total-pages` wins; otherwise it is derived
   * from `total-items` / `page-size`. Never less than 1.
   */
  _totalPages() {
    const explicit = parseCount(this.getAttribute("total-pages"))
    if (explicit !== null) {
      return Math.max(1, explicit)
    }
    const totalItems = this._totalItems()
    if (totalItems !== null) {
      return Math.max(1, Math.ceil(totalItems / this._pageSize()))
    }
    return 1
  }

  /* The current page, clamped into [1, totalPages]. */
  _currentPage(totalPages) {
    const parsed = parseInt(this.getAttribute("page") || "1", 10)
    const requested = Number.isNaN(parsed) === true ? 1 : parsed
    const rtnval = Math.min(Math.max(1, requested), totalPages)
    return rtnval
  }

  _summaryVisible() {
    if (this.hasAttribute("show-summary") === true) {
      return true
    }
    const rtnval = this._totalItems() !== null && this.hasAttribute("hide-summary") === false
    return rtnval
  }

  /* The page sizes offered by the selector; always includes the current size. */
  _pageSizeOptions() {
    let options = []
    const raw = this.getAttribute("page-size-options")

    if (raw !== null) {
      const parts = raw.split(",")
      for (let index = 0; index < parts.length; index = index + 1) {
        const parsed = parseCount(parts[index].trim())
        if (parsed !== null && parsed > 0 && options.indexOf(parsed) === -1) {
          options.push(parsed)
        }
      }
    }
    if (options.length === 0) {
      options = DEFAULT_PAGE_SIZE_OPTIONS.slice()
    }

    const current = this._pageSize()
    if (options.indexOf(current) === -1) {
      options.push(current)
    }
    options.sort(function(a, b) { return a - b })
    return options
  }

  /* The link for a page when `href-template` is set, otherwise null. */
  _hrefFor(page) {
    let href = null
    const template = this.getAttribute("href-template")
    if (template !== null && template.length > 0) {
      href = safeUrl(template.split("{page}").join(String(page)))
    }
    return href
  }

  /* ----- rendering ----- */

  /*
   * Identify the control that has focus so `_restoreFocus` can find its
   * replacement: "prev", "next", "page-size", or "page:<number>".
   */
  _focusedControlKey() {
    let key = null
    const active = this.shadowRoot.activeElement

    if (active !== null && this._root.contains(active) === true) {
      if (active.classList.contains("page-btn") === true) {
        key = `page:${active.textContent}`
      } else if (active.classList.contains("ctrl-btn") === true) {
        key = active.getAttribute("part")
      } else if (active.matches("select") === true) {
        key = "page-size"
      }
    }
    return key
  }

  /*
   * The rebuild replaced the focused control. Focus its equivalent; when that
   * one is now disabled or gone (Next on the last page, a page number that
   * scrolled out of the list) fall back to the current page, then to the
   * other direction control.
   */
  _restoreFocus(key) {
    const isUsable = (element) => {
      return element !== null && element.getAttribute("aria-disabled") !== "true" && element.hasAttribute("disabled") === false
    }

    const candidates = []
    if (key === "page-size") {
      candidates.push(this._root.querySelector(".page-size select"))
    } else if (key === "prev" || key === "next") {
      candidates.push(this._root.querySelector(`.ctrl-btn[part='${key}']`))
    } else {
      const wanted = key.slice("page:".length)
      const pageButtons = this._root.querySelectorAll(".page-btn")
      for (let index = 0; index < pageButtons.length; index = index + 1) {
        if (pageButtons[index].textContent === wanted) {
          candidates.push(pageButtons[index])
        }
      }
    }
    candidates.push(this._root.querySelector(".page-btn[aria-current='page']"))
    candidates.push(this._root.querySelector(".ctrl-btn[part='prev']"))
    candidates.push(this._root.querySelector(".ctrl-btn[part='next']"))

    let restored = false
    for (let index = 0; index < candidates.length && restored === false; index = index + 1) {
      if (isUsable(candidates[index]) === true) {
        candidates[index].focus()
        restored = true
      }
    }
    return
  }

  _rebuildUI() {
    const focusKey = this._focusedControlKey()

    this._root.replaceChildren()

    const totalPages = this._totalPages()
    const page = this._currentPage(totalPages)
    const variant = this.getAttribute("variant") || "full"
    const disabled = this.hasAttribute("disabled")

    this.reflectBoolean("single-page", totalPages <= 1)
    this._nav.setAttribute("aria-label", this.getAttribute("nav-label") || t("mj.pagination.navLabel"))

    const prevBtn = this._createCtrlBtn("prev", page - 1, page <= 1 || disabled === true)
    this._root.appendChild(prevBtn)

    if (variant === "compact") {
      const label = document.createElement("span")
      label.className = "compact-label"
      label.setAttribute("part", "compact-label")
      label.textContent = t("mj.pagination.pageOf", { page: page, total: totalPages })
      this._root.appendChild(label)
    } else if (variant !== "simple") {
      const ol = this._buildPageList(page, totalPages, disabled)
      this._root.appendChild(ol)
    }

    const nextBtn = this._createCtrlBtn("next", page + 1, page >= totalPages || disabled === true)
    this._root.appendChild(nextBtn)

    if (this.hasAttribute("show-page-size") === true) {
      this._root.appendChild(this._buildPageSizeSelect(disabled))
    }

    if (this._summaryVisible() === true) {
      const summary = this._buildSummary(page)
      this._root.appendChild(summary)
    }

    if (focusKey !== null) {
      this._restoreFocus(focusKey)
    }
    return
  }

  /*
   * A page control: a <button>, or an <a> when `href-template` is set. A
   * usable control carries its target page in data-page; a disabled one
   * carries none (and, as a link, no href).
   */
  _createPageControl(className, targetPage, isDisabled) {
    const href = this._hrefFor(targetPage)
    const control = document.createElement(href !== null ? "a" : "button")
    control.className = className

    if (href === null) {
      control.setAttribute("type", "button")
    }

    if (isDisabled === true) {
      control.setAttribute("aria-disabled", "true")
      if (href === null) {
        control.setAttribute("disabled", "")
      } else {
        control.setAttribute("role", "link")
      }
    } else {
      control.dataset.page = String(targetPage)
      if (href !== null) {
        control.setAttribute("href", href)
      }
    }
    return control
  }

  _createCtrlBtn(action, targetPage, isDisabled) {
    const btn = this._createPageControl("ctrl-btn", targetPage, isDisabled)
    btn.setAttribute("part", action)

    /* The default label is the fallback of a slot, so authors can replace it. */
    const slot = document.createElement("slot")
    slot.setAttribute("name", action === "prev" ? "prev-label" : "next-label")

    const arrow = document.createElement("span")
    arrow.className = "arrow"
    arrow.setAttribute("aria-hidden", "true")
    arrow.textContent = action === "prev" ? "←" : "→"
    const text = document.createElement("span")
    text.textContent = action === "prev" ? t("mj.pagination.previous") : t("mj.pagination.next")
    if (action === "prev") {
      slot.append(arrow, text)
    } else {
      slot.append(text, arrow)
    }

    btn.appendChild(slot)
    return btn
  }

  _buildPageList(currentPage, totalPages, disabled) {
    const siblingCount = parseInt(this.getAttribute("sibling-count") || "1", 10)
    const boundaryCount = parseInt(this.getAttribute("boundary-count") || "1", 10)
    const pages = this._computePageRange(currentPage, totalPages, siblingCount, boundaryCount)

    const ol = document.createElement("ol")
    ol.className = "page-list"
    ol.setAttribute("part", "page-list")

    let prevPage = null
    for (let i = 0; i < pages.length; i = i + 1) {
      const p = pages[i]

      if (prevPage !== null && p > prevPage + 1) {
        const ellipsisLi = document.createElement("li")
        ellipsisLi.setAttribute("part", "ellipsis")
        const ellipsis = document.createElement("span")
        ellipsis.className = "ellipsis"
        ellipsis.setAttribute("aria-hidden", "true")
        ellipsis.textContent = "…"
        ellipsisLi.appendChild(ellipsis)
        ol.appendChild(ellipsisLi)
      }

      const li = document.createElement("li")
      li.setAttribute("part", "page-item")

      /*
       * Numbered buttons stay focusable when the pager is disabled (they only
       * get aria-disabled), so `disabled` does not drop keyboard focus.
       */
      const btn = this._createPageControl("page-btn", p, false)
      btn.setAttribute("part", "page-btn")

      const isCurrent = p === currentPage
      if (isCurrent === true) {
        btn.setAttribute("aria-current", "page")
        btn.setAttribute("aria-label", t("mj.pagination.currentPageLabel", { page: p }))
      } else {
        btn.setAttribute("aria-label", t("mj.pagination.pageLabel", { page: p }))
      }

      btn.textContent = String(p)

      if (disabled === true) {
        delete btn.dataset.page
        btn.removeAttribute("href")
        btn.setAttribute("aria-disabled", "true")
      }

      li.appendChild(btn)
      ol.appendChild(li)
      prevPage = p
    }
    return ol
  }

  _computePageRange(current, total, siblings, boundary) {
    const pages = new Set()

    for (let i = 1; i <= Math.min(boundary, total); i = i + 1) {
      pages.add(i)
    }
    for (let i = Math.max(total - boundary + 1, 1); i <= total; i = i + 1) {
      pages.add(i)
    }
    for (let i = Math.max(1, current - siblings); i <= Math.min(total, current + siblings); i = i + 1) {
      pages.add(i)
    }

    const sorted = Array.from(pages).sort(function(a, b) { return a - b })
    return sorted
  }

  _buildPageSizeSelect(disabled) {
    const wrapper = document.createElement("label")
    wrapper.className = "page-size"
    wrapper.setAttribute("part", "page-size")

    const caption = document.createElement("span")
    caption.textContent = t("mj.pagination.pageSize")

    const select = document.createElement("select")
    const options = this._pageSizeOptions()
    const current = this._pageSize()
    for (let index = 0; index < options.length; index = index + 1) {
      const option = document.createElement("option")
      option.value = String(options[index])
      option.textContent = String(options[index])
      option.selected = options[index] === current
      select.appendChild(option)
    }
    select.disabled = disabled === true

    wrapper.append(caption, select)
    return wrapper
  }

  _buildSummary(page) {
    const totalItems = this._totalItems() || 0
    const pageSize = this._pageSize()
    const from = totalItems === 0 ? 0 : (page - 1) * pageSize + 1
    const to = Math.min(page * pageSize, totalItems)
    const div = document.createElement("div")
    div.className = "summary"
    div.setAttribute("part", "summary")

    /* The generated text is the fallback of the `summary` slot. */
    const slot = document.createElement("slot")
    slot.setAttribute("name", "summary")
    slot.textContent = t("mj.pagination.summary", { from: from, to: to, total: totalItems })
    div.appendChild(slot)
    return div
  }

  /* ----- interaction ----- */

  /*
   * One delegated listener for every page control: page and Previous/Next
   * controls carry their target page in data-page; disabled ones carry none.
   */
  _onRootClick(event) {
    const target = event.target instanceof Element ? event.target.closest("button, a") : null
    if (target === null) {
      return
    }
    if (target.dataset.page === undefined) {
      /* A disabled link must not navigate anywhere. */
      event.preventDefault()
      return
    }

    const isLink = target.matches("a") === true
    const modified = event.ctrlKey === true || event.metaKey === true || event.shiftKey === true || event.altKey === true
    if (isLink === true && modified === true) {
      /* Open-in-new-tab and friends are left to the browser. */
      return
    }

    const page = parseInt(target.dataset.page, 10)
    if (Number.isNaN(page) === false) {
      const navigated = this._navigateTo(page)
      if (isLink === true && navigated === false) {
        /* Canceled (the application routes itself) or already on that page. */
        event.preventDefault()
      }
    }
    return
  }

  _onRootChange(event) {
    const select = event.target instanceof Element ? event.target.closest(".page-size select") : null
    if (select === null) {
      return
    }

    /* The native change event of the inner select is not the component's event. */
    event.stopPropagation()

    const previousPageSize = this._pageSize()
    const pageSize = parseInt(select.value, 10)
    if (Number.isNaN(pageSize) === true || pageSize === previousPageSize) {
      return
    }

    const proceed = this.emit("mj-pagination-page-size-change", {
      pageSize: pageSize,
      previousPageSize: previousPageSize
    }, { cancelable: true })

    if (proceed === false) {
      select.value = String(previousPageSize)
      return
    }

    /* Keep the first item of the current page on screen under the new size. */
    const previousPage = this._currentPage(this._totalPages())
    const firstItemIndex = (previousPage - 1) * previousPageSize
    const page = Math.floor(firstItemIndex / pageSize) + 1

    this.setAttribute("page-size", String(pageSize))
    this.setAttribute("page", String(page))

    this.emit("mj-pagination-change", {
      page: this._currentPage(this._totalPages()),
      previousPage: previousPage,
      pageSize: pageSize
    })
    return
  }

  /* Returns true when the pager moved to `page`. */
  _navigateTo(page) {
    const totalPages = this._totalPages()
    const current = this._currentPage(totalPages)
    const next = Math.min(Math.max(1, page), totalPages)
    if (next === current) {
      return false
    }
    const proceed = this.emit("mj-pagination-change", {
      page: next,
      previousPage: current,
      pageSize: this._pageSize()
    }, { cancelable: true })
    if (proceed === true) {
      this.setAttribute("page", String(next))
    }
    return proceed
  }

  /* ----- scriptable API ----- */

  get totalPages() {
    return this._totalPages()
  }

  get hasPrevious() {
    return this._currentPage(this._totalPages()) > 1
  }

  get hasNext() {
    const total = this._totalPages()
    return this._currentPage(total) < total
  }

  /*
   * [firstItemIndex, lastItemIndex] of the current page, 0-based. When
   * `total-items` is known the upper bound never passes the last item.
   */
  get pageRange() {
    const page = this._currentPage(this._totalPages())
    const pageSize = this._pageSize()
    const first = (page - 1) * pageSize
    let last = first + pageSize - 1

    const totalItems = this._totalItems()
    if (totalItems !== null) {
      last = Math.max(first, Math.min(last, totalItems - 1))
    }
    return [first, last]
  }
}
