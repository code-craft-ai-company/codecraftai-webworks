/*
 * mjsearchresults.js
 *
 * <mj-search-results> -- ranked list of search results with count bar, empty
 * state, loading state, highlight support, and pagination or infinite scroll.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";
import { formatNumber } from "../core/intl.js";

const STYLES = `
:host {
  display: block;
}

.count-bar {
  font-size: var(--mj-results-count-size, var(--mj-font-size-sm));
  color: var(--mj-text-muted);
  padding: var(--mj-space-2) 0;
}

.result-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--mj-results-gap, var(--mj-space-4));
}

.result-item {
  border-bottom: 1px solid var(--mj-border);
  padding-bottom: var(--mj-space-4);
}

.result-item:last-child {
  border-bottom: none;
}

.result-title {
  display: block;
  font-size: var(--mj-font-size-md);
  font-weight: var(--mj-font-weight-medium);
  color: var(--mj-results-title-color, var(--mj-accent));
  text-decoration: none;
  margin-bottom: var(--mj-space-1);
}

.result-title:hover {
  text-decoration: underline;
}

.result-title:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
  border-radius: var(--mj-radius-sm);
}

.result-url {
  font-size: var(--mj-font-size-xs);
  color: var(--mj-results-url-color, var(--mj-color-success, #15803d));
  margin-bottom: var(--mj-space-1);
  direction: ltr;
}

.result-snippet {
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.result-meta {
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
  margin-top: var(--mj-space-1);
}

mark {
  background: var(--mj-results-highlight-bg, #fef08a);
  color: var(--mj-results-highlight-color, inherit);
  border-radius: var(--mj-radius-sm);
  padding: 0 2px;
}

.empty-state {
  padding: var(--mj-space-6);
  text-align: center;
  color: var(--mj-text-muted);
}

.loading-state {
  display: flex;
  flex-direction: column;
  gap: var(--mj-space-4);
}

.skeleton {
  background: linear-gradient(90deg, var(--mj-bg-muted) 25%, var(--mj-bg-subtle) 50%, var(--mj-bg-muted) 75%);
  background-size: 200% 100%;
  animation: mj-shimmer var(--mj-motion-slow) ease-in-out infinite;
  border-radius: var(--mj-radius-sm);
}

@keyframes mj-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.skeleton-title { height: 20px; width: 60%; margin-bottom: var(--mj-space-1); }
.skeleton-url { height: 14px; width: 40%; margin-bottom: var(--mj-space-2); }
.skeleton-snippet { height: 14px; width: 100%; }

.pagination-bar {
  margin-top: var(--mj-space-4);
  display: flex;
  gap: var(--mj-space-2);
  align-items: center;
}

.page-btn {
  padding: var(--mj-space-2) var(--mj-space-3);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-sm);
  background: var(--mj-surface);
  cursor: pointer;
  font: inherit;
  font-size: var(--mj-font-size-sm);
}

.page-btn:hover { background: var(--mj-bg-muted); }
.page-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.page-btn[disabled] { opacity: 0.45; cursor: not-allowed; }

.load-more-btn {
  display: block;
  width: 100%;
  margin-top: var(--mj-space-4);
  padding: var(--mj-space-3);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-md);
  background: var(--mj-surface);
  cursor: pointer;
  font: inherit;
  font-size: var(--mj-font-size-sm);
  text-align: center;
}

.load-more-btn:hover { background: var(--mj-bg-muted); }
.sentinel { height: 1px; }
`;

export class MjSearchResults extends MjElement {
  static tagName = "mj-search-results";
  static styles = STYLES;
  static watched = [
    "total-count", "loading", "load-mode", "page",
    "page-size", "empty-message", "compact", "highlight-term"
  ];

  constructor() {
    super()
    this._results = []
    this._dataSource = null
    this._intersectionObserver = null
    this._listId = nextId("mj-sr-list")
    this._countId = nextId("mj-sr-count")
  }

  render() {
    const markup = `
      <div class="count-bar" role="status" aria-live="polite"
           part="count-bar" id="${this._countId}"></div>
      <ul class="result-list" role="list" part="result-list"
          id="${this._listId}" aria-live="polite"></ul>
      <div class="pagination-bar" part="pagination" hidden></div>
      <button class="load-more-btn" part="load-more" hidden>Load more</button>
      <div class="sentinel" aria-hidden="true"></div>
    `
    return markup
  }

  afterRender() {
    this._countEl = this.$(".count-bar")
    this._listEl = this.$(".result-list")
    this._paginationEl = this.$(".pagination-bar")
    this._loadMoreBtn = this.$(".load-more-btn")
    this._sentinel = this.$(".sentinel")

    this.listen(this._loadMoreBtn, "click", this._onLoadMore.bind(this))
    this.listen(this._listEl, "click", this._onResultClick.bind(this))

    this._renderResults()
    this._setupInfiniteScroll()
    return
  }

  _renderResults() {
    const loading = this.hasAttribute("loading")
    const loadMode = this.getAttribute("load-mode") || "paginate"
    const totalCount = parseInt(this.getAttribute("total-count") || "0", 10)
    const emptyMsg = this.getAttribute("empty-message") || "No results found."

    if (this._listEl === null) {
      return
    }

    // Count bar
    const countNum = isNaN(totalCount) ? 0 : totalCount
    this._countEl.textContent = `${formatNumber(countNum)} ${countNum === 1 ? "result" : "results"}`
    this._listEl.setAttribute("aria-busy", loading === true ? "true" : "false")

    if (loading === true) {
      this._listEl.innerHTML = this._renderSkeletons(3)
      return
    }

    if (this._results.length === 0) {
      this._listEl.innerHTML = `
        <li class="empty-state" part="empty-state">
          <slot name="empty">
            <p>${emptyMsg}</p>
            <p>${this.getAttribute("empty-suggestion") || ""}</p>
          </slot>
        </li>
      `
      return
    }

    const term = this.getAttribute("highlight-term") || ""
    let html = ""
    for (let i = 0; i < this._results.length; i = i + 1) {
      const r = this._results[i]
      const snippet = term.length > 0 ? this._highlight(r.snippet || "", term) : (r.snippet || "")
      const meta = r.date ? `<div class="result-meta" part="result-meta">${r.date}</div>` : ""
      html += `
        <li class="result-item" part="result-item" data-result-index="${i}">
          <a class="result-title" part="result-title" href="${r.url || "#"}"
             data-result-id="${r.id}">${this._escapeHtml(r.title || "")}</a>
          <div class="result-url" part="result-url">${this._escapeHtml(r.url || "")}</div>
          <div class="result-snippet" part="result-snippet">${snippet}</div>
          ${meta}
        </li>
      `
    }
    this._listEl.innerHTML = html

    // Pagination
    if (loadMode === "paginate") {
      this._renderPagination(totalCount)
    } else if (loadMode === "button") {
      this._loadMoreBtn.hidden = false
    }

    return
  }

  _renderPagination(total) {
    const pageSize = parseInt(this.getAttribute("page-size") || "10", 10)
    const page = parseInt(this.getAttribute("page") || "1", 10)
    const totalPages = Math.ceil(total / pageSize)

    if (totalPages <= 1) {
      this._paginationEl.hidden = true
      return
    }

    this._paginationEl.hidden = false
    this._paginationEl.innerHTML = `
      <button class="page-btn" ${page <= 1 ? "disabled" : ""} data-action="prev">Previous</button>
      <span>Page ${page} of ${totalPages}</span>
      <button class="page-btn" ${page >= totalPages ? "disabled" : ""} data-action="next">Next</button>
    `

    const prevBtn = this._paginationEl.querySelector("[data-action='prev']")
    const nextBtn = this._paginationEl.querySelector("[data-action='next']")
    if (prevBtn !== null) {
      this.listen(prevBtn, "click", () => this._changePage(page - 1))
    }
    if (nextBtn !== null) {
      this.listen(nextBtn, "click", () => this._changePage(page + 1))
    }
    return
  }

  _changePage(newPage) {
    this.setAttribute("page", String(newPage))
    this.emit("mj-page-change", {
      page: newPage,
      pageSize: parseInt(this.getAttribute("page-size") || "10", 10)
    })
    return
  }

  _setupInfiniteScroll() {
    const loadMode = this.getAttribute("load-mode") || "paginate"
    if (loadMode !== "infinite") {
      return
    }
    if (typeof IntersectionObserver === "undefined") {
      return
    }
    this._intersectionObserver = new IntersectionObserver((entries) => {
      for (let i = 0; i < entries.length; i = i + 1) {
        if (entries[i].isIntersecting === true && !this.hasAttribute("loading")) {
          this._onLoadMore()
        }
      }
    }, { threshold: 0.1 })

    if (this._sentinel !== null) {
      this._intersectionObserver.observe(this._sentinel)
    }
    this.onTeardown(() => {
      if (this._intersectionObserver !== null) {
        this._intersectionObserver.disconnect()
        this._intersectionObserver = null
      }
    })
    return
  }

  _onLoadMore() {
    const page = parseInt(this.getAttribute("page") || "1", 10)
    const pageSize = parseInt(this.getAttribute("page-size") || "10", 10)
    this.emit("mj-load-more", { page: page + 1, pageSize: pageSize })
    return
  }

  _onResultClick(event) {
    const link = event.target.closest(".result-title")
    if (link === null) {
      return
    }
    const li = link.closest(".result-item")
    if (li === null) {
      return
    }
    const index = parseInt(li.getAttribute("data-result-index") || "0", 10)
    const result = this._results[index]
    if (result === undefined) {
      return
    }
    this.emit("mj-result-select", { result: result, index: index })
    return
  }

  _highlight(text, term) {
    const terms = term.trim().split(/\s+/)
    let escaped = this._escapeHtml(text)
    for (let i = 0; i < terms.length; i = i + 1) {
      if (terms[i].length === 0) {
        continue
      }
      // Escape regex special chars in the term
      const safeterm = terms[i].replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
      const re = new RegExp(`(${safeterm})`, "gi")
      escaped = escaped.replace(re, "<mark>$1</mark>")
    }
    return escaped
  }

  _escapeHtml(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
  }

  _renderSkeletons(count) {
    let html = ""
    for (let i = 0; i < count; i = i + 1) {
      html += `
        <li>
          <div class="skeleton skeleton-title"></div>
          <div class="skeleton skeleton-url"></div>
          <div class="skeleton skeleton-snippet"></div>
        </li>
      `
    }
    return html
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._listEl !== null) {
      this._renderResults()
    }
    if (name === "total-count" && newValue !== oldValue) {
      const count = parseInt(newValue || "0", 10)
      announce(`${formatNumber(count)} ${count === 1 ? "result" : "results"} loaded`, "polite")
    }
    return
  }

  get results() {
    return this._results
  }

  set results(value) {
    this._results = Array.isArray(value) ? value : []
    if (this._listEl !== null) {
      this._renderResults()
    }
    return
  }

  get dataSource() {
    return this._dataSource
  }

  set dataSource(source) {
    this._dataSource = source
    if (source !== null && source !== undefined) {
      this._fetchFromSource()
    }
    return
  }

  _fetchFromSource() {
    if (this._dataSource === null) {
      return
    }
    const page = parseInt(this.getAttribute("page") || "1", 10)
    const pageSize = parseInt(this.getAttribute("page-size") || "10", 10)
    this.setAttribute("loading", "")

    const promise = this._dataSource.query({
      offset: (page - 1) * pageSize,
      limit: pageSize
    })

    Promise.resolve(promise).then((result) => {
      this._results = result.items || []
      this.setAttribute("total-count", String(result.total || 0))
      this.removeAttribute("loading")
      this._renderResults()
    }).catch(() => {
      this.removeAttribute("loading")
    })

    return
  }
}
