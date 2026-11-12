/*
 * mjsearchresults.js
 *
 * <mj-search-results> -- ranked list of search results with count bar, empty
 * state, loading state, error state, highlight support, and pagination,
 * a "Load more" button or infinite scroll.
 *
 * Result data is untrusted (titles and snippets usually come from
 * user-generated content, the empty message usually echoes the query), so
 * every row is built with DOM APIs and text nodes; result URLs pass through
 * `safeUrl`. Highlighting splits the raw snippet text once and wraps the
 * matching segments in <mark> elements.
 *
 * With a `dataSource` ({ query({ offset, limit }) } returning
 * { items, total }, or a promise of it) the component fetches the current
 * page itself: when the source is set, and again whenever `page` or
 * `page-size` change. A response that arrives after a newer request was
 * started is ignored; a failed request shows the error state and fires
 * `mj-results-error`. A response without a `total` is read as "at least
 * this many": a full page offers more, a short page is the end.
 *
 * Loading more (Load more, infinite scroll) keeps the results on screen and
 * adds placeholder rows below them; only a page change replaces the list
 * with placeholders.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { html, safeUrl } from "../core/html.js";
import { t, formatNumber, formatDate } from "../core/intl.js";

const DEFAULT_PAGE_SIZE = 10;
const SKELETON_COUNT = 3;

const LOAD_MODES = ["paginate", "button", "infinite"];

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

.result-list:focus { outline: none; }

.result-list:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.result-item {
  border-block-end: 1px solid var(--mj-border);
  padding-block-end: var(--mj-space-4);
}

.result-item:last-child {
  border-block-end: none;
}

.result-title {
  display: block;
  font-size: var(--mj-font-size-md);
  font-weight: var(--mj-font-weight-medium);
  color: var(--mj-results-title-color, var(--mj-accent));
  text-decoration: none;
  margin-block-end: var(--mj-space-1);
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
  color: var(--mj-results-url-color, var(--mj-text-muted));
  margin-block-end: var(--mj-space-1);
  direction: ltr;
  text-align: start;
  overflow-wrap: anywhere;
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
  margin-block-start: var(--mj-space-1);
}

/* Compact: title and URL only, closer together. */
:host([compact]) .result-list {
  gap: var(--mj-results-gap, var(--mj-space-2));
}

:host([compact]) .result-item {
  padding-block-end: var(--mj-space-2);
}

:host([compact]) .result-snippet,
:host([compact]) .result-meta {
  display: none;
}

/*
 * The highlight sets its own text colour, so it stays readable whatever the
 * surrounding colour is; both tokens are defined for the light and the dark
 * theme.
 */
mark {
  background: var(--mj-results-highlight-bg, var(--mj-color-warning-surface));
  color: var(--mj-results-highlight-color, var(--mj-text));
  border-radius: var(--mj-radius-sm);
  padding: 0 2px;
}

.empty-state {
  padding: var(--mj-space-6);
  text-align: center;
  color: var(--mj-text-muted);
}

.error-state {
  padding: var(--mj-space-3) var(--mj-space-4);
  border: 1px solid var(--mj-color-danger);
  border-radius: var(--mj-radius-md);
  background: var(--mj-color-danger-surface);
  color: var(--mj-color-danger);
  font-size: var(--mj-font-size-sm);
}

.error-state[hidden] { display: none; }

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

.skeleton-title { height: 20px; width: 60%; margin-block-end: var(--mj-space-1); }
.skeleton-url { height: 14px; width: 40%; margin-block-end: var(--mj-space-2); }
.skeleton-snippet { height: 14px; width: 100%; }

.pagination-bar {
  margin-block-start: var(--mj-space-4);
  display: flex;
  gap: var(--mj-space-2);
  align-items: center;
}

.pagination-bar[hidden] { display: none; }

.page-btn {
  padding: var(--mj-space-2) var(--mj-space-3);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-sm);
  background: var(--mj-surface);
  color: var(--mj-text);
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

.page-status {
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text-muted);
}

.load-more-btn {
  display: block;
  inline-size: 100%;
  margin-block-start: var(--mj-space-4);
  padding: var(--mj-space-3);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-md);
  background: var(--mj-surface);
  color: var(--mj-text);
  cursor: pointer;
  font: inherit;
  font-size: var(--mj-font-size-sm);
  text-align: center;
}

.load-more-btn[hidden] { display: none; }
.load-more-btn:hover { background: var(--mj-bg-muted); }
.load-more-btn[aria-disabled="true"] { cursor: progress; opacity: 0.6; }
.load-more-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.sentinel { height: 1px; }
`;

/* A positive integer from an attribute value, or `fallback`. */
function positiveInteger(raw, fallback) {
  const parsed = parseInt(raw === null || raw === undefined ? "" : raw, 10)
  const value = Number.isFinite(parsed) === true && parsed > 0 ? parsed : fallback
  return value
}

/* Escape the characters that are special in a regular expression. */
function escapeRegExp(text) {
  const escaped = text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
  return escaped
}

/*
 * Format a result date for display. A `YYYY-MM-DD` string is a calendar day
 * and is shown as that day in the viewer's time zone; other strings and Date
 * objects go through `formatDate`. Anything that is not a date is shown as
 * it was given.
 */
function formatResultDate(value) {
  let formatted = ""

  if (value !== null && value !== undefined && value !== "") {
    let date = null
    const dayMatch = typeof value === "string" ? value.match(/^(\d{4})-(\d{2})-(\d{2})$/) : null

    if (dayMatch !== null) {
      date = new Date(Number(dayMatch[1]), Number(dayMatch[2]) - 1, Number(dayMatch[3]))
    } else if (value instanceof Date) {
      date = value
    } else {
      date = new Date(value)
    }

    if (Number.isNaN(date.getTime()) === true) {
      formatted = String(value)
    } else {
      formatted = formatDate(date)
    }
  }

  return formatted
}

export class MjSearchResults extends MjElement {
  static tagName = "mj-search-results";
  static styles = STYLES;
  static watched = [
    "total-count", "loading", "load-mode", "page", "page-size",
    "empty-message", "empty-suggestion", "compact", "highlight-term"
  ];

  constructor() {
    super()

    /* Shadow references; null until the first render. */
    this._countEl = null
    this._errorEl = null
    this._listEl = null
    this._paginationEl = null
    this._prevBtn = null
    this._nextBtn = null
    this._pageStatusEl = null
    this._loadMoreBtn = null
    this._sentinel = null

    this._results = []
    this._dataSource = null
    this._error = null

    /* Identifies the newest dataSource request; older responses are dropped. */
    this._requestSerial = 0

    /* "page:pageSize" of the last dataSource request, so a repeat is not re-sent. */
    this._fetchedKey = null

    /* True while a dataSource request adds results after the ones shown. */
    this._appendPending = false

    /*
     * True when the last dataSource response had no total but a full page:
     * `total-count` is then only a lower bound and more can be requested.
     */
    this._moreHint = false

    /* True while the component itself writes `total-count`. */
    this._writingTotal = false

    this._intersectionObserver = null
    this._listId = nextId("mj-sr-list")
    this._countId = nextId("mj-sr-count")
  }

  render() {
    const markup = html`
      <div class="count-bar" role="status" part="count-bar" id="${this._countId}"></div>
      <div class="error-state" role="alert" part="error-state" hidden></div>
      <ul class="result-list" role="list" part="result-list" id="${this._listId}"
          tabindex="-1" aria-label="${t("mj.searchResults.listLabel")}"></ul>
      <nav class="pagination-bar" part="pagination" hidden>
        <button class="page-btn" type="button" data-action="prev"></button>
        <span class="page-status"></span>
        <button class="page-btn" type="button" data-action="next"></button>
      </nav>
      <button class="load-more-btn" type="button" part="load-more" hidden>${t("mj.searchResults.loadMore")}</button>
      <div class="sentinel" aria-hidden="true"></div>
    `
    return markup
  }

  afterRender() {
    this._countEl = this.$(".count-bar")
    this._errorEl = this.$(".error-state")
    this._listEl = this.$(".result-list")
    this._paginationEl = this.$(".pagination-bar")
    this._prevBtn = this.$("[data-action='prev']")
    this._nextBtn = this.$("[data-action='next']")
    this._pageStatusEl = this.$(".page-status")
    this._loadMoreBtn = this.$(".load-more-btn")
    this._sentinel = this.$(".sentinel")

    this._paginationEl.setAttribute("aria-label", t("mj.pagination.navLabel"))
    this._prevBtn.textContent = t("mj.pagination.previous")
    this._nextBtn.textContent = t("mj.pagination.next")

    this.listen(this._prevBtn, "click", this._onPageButton.bind(this, -1))
    this.listen(this._nextBtn, "click", this._onPageButton.bind(this, 1))
    this.listen(this._loadMoreBtn, "click", this._onLoadMore.bind(this))
    this.listen(this._listEl, "click", this._onResultClick.bind(this))

    this.onTeardown(() => {
      this._disconnectInfiniteScroll()
      /* A response still in flight belongs to the DOM that is going away. */
      this._requestSerial = this._requestSerial + 1
    })

    this._renderResults()

    /* A dataSource assigned before the element was attached is queried now. */
    if (this._dataSource !== null) {
      this._fetchedKey = null
      this._fetchFromSource(false)
    }
    return
  }

  /* ----- attribute readers ----- */

  _loadMode() {
    const requested = this.getAttribute("load-mode")
    const mode = LOAD_MODES.indexOf(requested) >= 0 ? requested : "paginate"
    return mode
  }

  _page() {
    const page = positiveInteger(this.getAttribute("page"), 1)
    return page
  }

  _pageSize() {
    const pageSize = positiveInteger(this.getAttribute("page-size"), DEFAULT_PAGE_SIZE)
    return pageSize
  }

  _totalCount() {
    const parsed = parseInt(this.getAttribute("total-count") || "0", 10)
    const total = Number.isFinite(parsed) === true && parsed > 0 ? parsed : 0
    return total
  }

  /*
   * "1 result" / "1,240 results", using the plural rules of the active
   * locale; "20+ results" while the total is only a lower bound.
   */
  _countText(count) {
    const suffix = this._moreHint === true ? "+" : ""
    const text = t("mj.searchResults.count", { count: count, countText: formatNumber(count) + suffix })
    return text
  }

  /*
   * True when the list keeps its results while loading and shows the
   * placeholders below them: a dataSource request for more results, or the
   * host loading more in the button / infinite modes. A page change
   * replaces the list instead.
   */
  _isAppending(loading) {
    let appending = false
    if (loading === true && this._results.length > 0) {
      if (this._dataSource !== null) {
        appending = this._appendPending === true
      } else {
        appending = this._loadMode() !== "paginate"
      }
    }
    return appending
  }

  /* ----- rendering ----- */

  /*
   * Rebuild the list from the current results and attributes, then bring
   * the count bar, the error state and all three paging controls in line.
   */
  _renderResults() {
    if (this._listEl === undefined || this._listEl === null) {
      return
    }

    const loading = this.hasAttribute("loading")
    const appending = this._isAppending(loading)
    const loadMoreHadFocus = this.shadowRoot.activeElement === this._loadMoreBtn

    const countText = this._countText(this._totalCount())
    if (this._countEl.textContent !== countText) {
      /* role="status": the changed count is announced once, by this region. */
      this._countEl.textContent = countText
    }

    this._listEl.setAttribute("aria-busy", loading === true ? "true" : "false")
    this._listEl.textContent = ""

    if (this._error !== null) {
      this._errorEl.textContent = this._error
      this._errorEl.hidden = false
    } else {
      this._errorEl.textContent = ""
      this._errorEl.hidden = true
    }

    if (loading === true && appending === false) {
      this._listEl.innerHTML = String(this._skeletonMarkup(SKELETON_COUNT))
    } else if (this._results.length === 0) {
      if (this._error === null) {
        this._listEl.appendChild(this._buildEmptyState())
      }
    } else {
      const highlighter = this._buildHighlighter(this.getAttribute("highlight-term") || "")
      for (let index = 0; index < this._results.length; index = index + 1) {
        this._listEl.appendChild(this._buildResultItem(this._results[index], index, highlighter))
      }
      if (appending === true) {
        this._listEl.insertAdjacentHTML("beforeend", String(this._skeletonMarkup(1)))
      }
    }

    this._syncControls()

    /* The Load more button that had focus is gone (no more results): keep focus in the list. */
    if (loadMoreHadFocus === true && this._loadMoreBtn.hidden === true) {
      this._listEl.focus({ preventScroll: true })
    }
    return
  }

  _skeletonMarkup(count) {
    const rows = []
    for (let index = 0; index < count; index = index + 1) {
      rows.push(html`
        <li aria-hidden="true">
          <div class="skeleton skeleton-title"></div>
          <div class="skeleton skeleton-url"></div>
          <div class="skeleton skeleton-snippet"></div>
        </li>
      `)
    }
    const markup = html`${rows}`
    return markup
  }

  _buildEmptyState() {
    const item = document.createElement("li")
    item.className = "empty-state"
    item.setAttribute("part", "empty-state")

    const slot = document.createElement("slot")
    slot.name = "empty"

    const message = document.createElement("p")
    message.textContent = this.getAttribute("empty-message") || t("mj.searchResults.empty")
    slot.appendChild(message)

    const suggestionText = this.getAttribute("empty-suggestion") || ""
    if (suggestionText.length > 0) {
      const suggestion = document.createElement("p")
      suggestion.textContent = suggestionText
      slot.appendChild(suggestion)
    }

    item.appendChild(slot)
    return item
  }

  /*
   * One regular expression for all highlight terms (longest first, so a
   * term that contains another wins), or null when there is nothing to
   * highlight.
   */
  _buildHighlighter(termText) {
    let highlighter = null

    const terms = termText.trim().split(/\s+/).filter((term) => term.length > 0)
    if (terms.length > 0) {
      terms.sort((first, second) => second.length - first.length)
      const alternatives = terms.map((term) => escapeRegExp(term))
      highlighter = new RegExp(`(${alternatives.join("|")})`, "gi")
    }

    return highlighter
  }

  /*
   * Append `text` to `parent`, wrapping the segments that match
   * `highlighter` in <mark>. The raw text is split first and every segment
   * becomes a text node, so neither the text nor a term can produce markup.
   */
  _appendHighlighted(parent, text, highlighter) {
    if (highlighter === null) {
      parent.appendChild(document.createTextNode(text))
      return
    }

    /* A capturing split puts the matches at the odd positions. */
    const segments = text.split(highlighter)
    for (let index = 0; index < segments.length; index = index + 1) {
      const segment = segments[index]
      if (segment.length > 0) {
        if (index % 2 === 1) {
          const mark = document.createElement("mark")
          mark.textContent = segment
          parent.appendChild(mark)
        } else {
          parent.appendChild(document.createTextNode(segment))
        }
      }
    }
    return
  }

  _buildResultItem(result, index, highlighter) {
    const record = result !== null && result !== undefined ? result : {}
    const urlText = record.url !== null && record.url !== undefined ? String(record.url) : ""

    const item = document.createElement("li")
    item.className = "result-item"
    item.setAttribute("part", "result-item")
    item.setAttribute("data-result-index", String(index))

    const title = document.createElement("a")
    title.className = "result-title"
    title.setAttribute("part", "result-title")
    title.setAttribute("href", safeUrl(urlText.length > 0 ? urlText : "#"))
    if (record.id !== null && record.id !== undefined) {
      title.setAttribute("data-result-id", String(record.id))
    }
    title.textContent = record.title !== null && record.title !== undefined ? String(record.title) : ""
    item.appendChild(title)

    const url = document.createElement("div")
    url.className = "result-url"
    url.setAttribute("part", "result-url")
    url.textContent = urlText
    item.appendChild(url)

    const snippet = document.createElement("div")
    snippet.className = "result-snippet"
    snippet.setAttribute("part", "result-snippet")
    const snippetText = record.snippet !== null && record.snippet !== undefined ? String(record.snippet) : ""
    this._appendHighlighted(snippet, snippetText, highlighter)
    item.appendChild(snippet)

    const metaParts = []
    if (record.category !== null && record.category !== undefined && record.category !== "") {
      metaParts.push(String(record.category))
    }
    const dateText = formatResultDate(record.date)
    if (dateText.length > 0) {
      metaParts.push(dateText)
    }
    if (metaParts.length > 0) {
      const meta = document.createElement("div")
      meta.className = "result-meta"
      meta.setAttribute("part", "result-meta")
      meta.textContent = metaParts.join(" · ")
      item.appendChild(meta)
    }

    return item
  }

  /*
   * Show exactly the paging control that belongs to the current load-mode
   * and state: the pagination bar (paginate), the Load more button (button)
   * or the scroll observer (infinite).
   */
  _syncControls() {
    const mode = this._loadMode()
    const loading = this.hasAttribute("loading")
    const total = this._totalCount()
    const hasResults = this._results.length > 0
    const moreAvailable = hasResults === true && (this._results.length < total || this._moreHint === true)
    const appending = this._isAppending(loading)

    /* Pagination: kept in place while a page loads so the layout does not jump. */
    const page = this._page()
    let totalPages = Math.max(1, Math.ceil(total / this._pageSize()))
    if (this._moreHint === true) {
      totalPages = Math.max(totalPages, page + 1)
    }
    const showPagination =
      mode === "paginate" && totalPages > 1 && (hasResults === true || loading === true)
    this._paginationEl.hidden = showPagination === false
    this._prevBtn.disabled = page <= 1 || loading === true
    this._nextBtn.disabled = page >= totalPages || loading === true
    this._pageStatusEl.textContent = t("mj.pagination.pageOf", { page: page, total: totalPages })

    /* While more results load the button stays where it is, inert, so focus is not lost. */
    const showLoadMore = mode === "button" && ((moreAvailable === true && loading === false) || appending === true)
    this._loadMoreBtn.hidden = showLoadMore === false
    if (appending === true) {
      this._loadMoreBtn.setAttribute("aria-disabled", "true")
    } else {
      this._loadMoreBtn.removeAttribute("aria-disabled")
    }

    if (mode === "infinite" && moreAvailable === true && loading === false) {
      this._armInfiniteScroll()
    } else {
      this._disconnectInfiniteScroll()
    }
    return
  }

  /* ----- paging ----- */

  _onPageButton(step) {
    const nextPage = this._page() + step
    if (nextPage < 1) {
      return
    }

    /*
     * The clicked button may be disabled by the new page (first / last), so
     * focus moves to the list, which stays in place while its rows change.
     */
    this._listEl.focus()

    this.setAttribute("page", String(nextPage))
    this.emit("mj-page-change", { page: nextPage, pageSize: this._pageSize() })
    return
  }

  /*
   * (Re)start watching the sentinel below the list. Observing afresh reports
   * the current state, so a sentinel that is still in view after a short
   * page was appended asks for the next page again.
   */
  _armInfiniteScroll() {
    if (typeof IntersectionObserver === "undefined" || this._sentinel === null) {
      return
    }

    if (this._intersectionObserver === null) {
      this._intersectionObserver = new IntersectionObserver((entries) => {
        for (let index = 0; index < entries.length; index = index + 1) {
          if (entries[index].isIntersecting === true && this.hasAttribute("loading") === false) {
            this._onLoadMore()
          }
        }
      }, { threshold: 0.1 })
    } else {
      this._intersectionObserver.unobserve(this._sentinel)
    }
    this._intersectionObserver.observe(this._sentinel)
    return
  }

  _disconnectInfiniteScroll() {
    if (this._intersectionObserver !== null) {
      this._intersectionObserver.disconnect()
      this._intersectionObserver = null
    }
    return
  }

  /*
   * More results are wanted (Load more button or the scroll sentinel). The
   * page reported is the one that follows the results already shown.
   */
  _onLoadMore() {
    /* One request at a time: the button is inert and the sentinel waits while loading. */
    if (this.hasAttribute("loading") === true) {
      return
    }

    const pageSize = this._pageSize()
    const nextPage = Math.floor(this._results.length / pageSize) + 1
    this.emit("mj-load-more", { page: nextPage, pageSize: pageSize })

    if (this._dataSource !== null) {
      this._fetchFromSource(true)
    }
    return
  }

  _onResultClick(event) {
    const target = event.target
    if (!(target instanceof Element)) {
      return
    }

    const link = target.closest(".result-title")
    const row = link !== null ? link.closest(".result-item") : null
    if (row !== null) {
      const index = parseInt(row.getAttribute("data-result-index") || "0", 10)
      const result = this._results[index]
      if (result !== undefined) {
        this.emit("mj-result-select", { result: result, index: index })
      }
    }
    return
  }

  /* ----- data source ----- */

  /*
   * Query the data source. `append` adds the next batch after the results
   * already shown (Load more / infinite scroll); otherwise the current page
   * replaces them.
   */
  _fetchFromSource(append) {
    const source = this._dataSource
    if (source === null || source === undefined || this._listEl === null) {
      return
    }

    const page = this._page()
    const pageSize = this._pageSize()
    const offset = append === true ? this._results.length : (page - 1) * pageSize

    if (append === false) {
      this._fetchedKey = `${page}:${pageSize}`
    }

    this._requestSerial = this._requestSerial + 1
    const serial = this._requestSerial

    this._error = null
    this._appendPending = append === true
    this.setAttribute("loading", "")

    let pending = null
    try {
      pending = source.query({ offset: offset, limit: pageSize, page: page, pageSize: pageSize })
    } catch (error) {
      pending = Promise.reject(error)
    }

    Promise.resolve(pending).then((response) => {
      if (serial === this._requestSerial) {
        const payload = response !== null && response !== undefined ? response : {}
        const items = Array.isArray(payload.items) === true ? payload.items : []
        this._results = append === true ? this._results.concat(items) : items
        this._applyResponseTotal(payload.total, offset, items.length, pageSize)
        /* Cleared only now, so no intermediate render drops the results. */
        this._appendPending = false
        this.removeAttribute("loading")
        this._renderResults()
      }
    }).catch((error) => {
      if (serial === this._requestSerial) {
        this._error = t("mj.searchResults.loadError")
        this._appendPending = false
        this.removeAttribute("loading")
        this._renderResults()
        this.emit("mj-results-error", { error: error })
      }
    })

    return
  }

  /*
   * Record the total a dataSource response reported. Without one, what is
   * known is a lower bound (`offset + count`): a full page says more may
   * follow, a short page is the end.
   */
  _applyResponseTotal(total, offset, count, pageSize) {
    let reported = null
    if (total !== null && total !== undefined && total !== "") {
      const parsed = Number(total)
      if (Number.isFinite(parsed) === true && parsed >= 0) {
        reported = Math.floor(parsed)
      }
    }

    let written = reported
    if (reported === null) {
      this._moreHint = count >= pageSize
      written = offset + count
    } else {
      this._moreHint = false
    }

    this._writingTotal = true
    this.setAttribute("total-count", String(written))
    this._writingTotal = false
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._listEl === undefined || this._listEl === null) {
      return
    }

    /* A total the page sets is exact again. */
    if (name === "total-count" && this._writingTotal === false) {
      this._moreHint = false
    }

    const pagingChanged = name === "page" || name === "page-size"
    const key = `${this._page()}:${this._pageSize()}`
    if (pagingChanged === true && this._dataSource !== null && key !== this._fetchedKey) {
      /* The fetch re-renders (loading state first, results when they arrive). */
      this._fetchFromSource(false)
    } else {
      this._renderResults()
    }
    return
  }

  /* ----- scriptable API ----- */

  get results() {
    return this._results
  }

  set results(value) {
    this._results = Array.isArray(value) === true ? value : []
    this._error = null
    this._moreHint = false
    this._renderResults()
    return
  }

  get dataSource() {
    return this._dataSource
  }

  set dataSource(source) {
    this._dataSource = source !== undefined ? source : null
    this._fetchedKey = null
    if (this._dataSource !== null) {
      /* Before the first render there is nothing to show yet; afterRender fetches. */
      this._fetchFromSource(false)
    }
    return
  }
}
