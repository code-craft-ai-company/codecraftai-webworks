/*
 * mjtoc.js
 *
 * <mj-toc> -- in-page table of contents with scroll-spy.
 * Scans headings in a target element and builds anchor links, nested by
 * heading level; or, in manual mode, uses slotted <a href="#id"> links.
 * Scroll-spy marks the link of the section being read: the last heading above
 * the activation line. A MutationObserver rescans dynamic content.
 *
 * WAI-ARIA: nav landmark; aria-current="location" on the active section link.
 */

import { MjElement } from "../core/mjelement.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";

const STYLES = `
:host {
  display: block;
  width: var(--mj-toc-width, 220px);
}
:host([sticky]) {
  position: sticky;
  top: var(--mj-toc-sticky-top, var(--mj-app-bar-height, 0px));
  max-height: calc(100vh - var(--mj-toc-sticky-top, 0px));
  overflow-y: auto;
}

.title {
  font-weight: var(--mj-font-weight-medium);
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
  margin: 0;
  margin-block-end: var(--mj-space-3);
  padding: 0;
}
.title[hidden] { display: none; }

.list,
.nested-list {
  list-style: none;
  margin: 0; padding: 0;
}
.list[hidden] { display: none; }

.item { display: block; }

/* --mj-toc-depth is set per link: 0 for the top level, 1 for the next, ... */
.anchor {
  display: block;
  padding: var(--mj-space-1) var(--mj-space-3);
  padding-inline-start: calc(var(--mj-space-3) + var(--mj-toc-depth, 0) * var(--mj-toc-indent, var(--mj-space-4)));
  font-size: var(--mj-toc-font-size, var(--mj-font-size-sm));
  color: var(--mj-toc-link-color, var(--mj-text-muted));
  text-decoration: none;
  border-inline-start: 2px solid transparent;
  transition: color var(--mj-motion-fast) var(--mj-motion-ease),
              border-color var(--mj-motion-fast) var(--mj-motion-ease);
  border-start-end-radius: var(--mj-radius-sm);
  border-end-end-radius: var(--mj-radius-sm);
  line-height: 1.4;
}
.anchor:hover { color: var(--mj-toc-link-color-hover, var(--mj-text)); }
.anchor:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.anchor[aria-current="location"],
::slotted(a[aria-current="location"]) {
  color: var(--mj-toc-active-color, var(--mj-accent));
  border-inline-start: var(--mj-toc-active-border, 2px solid var(--mj-accent));
  font-weight: var(--mj-font-weight-medium);
}

.empty-notice {
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text-muted);
  padding: var(--mj-space-2) var(--mj-space-3);
}
`;

/* A heading is active once its top is above this fraction of the viewport height. */
const ACTIVATION_LINE = 0.4;

/* Delay (ms) between a content mutation and the rescan it triggers. */
const RESCAN_DELAY = 100;

export class MjToc extends MjElement {
  static tagName = "mj-toc";
  static styles = STYLES;
  static watched = [
    "target", "depth", "heading-selector", "sticky", "nav-label", "heading", "title", "offset"
  ];

  constructor() {
    super()
    this._sections = []

    /* One entry per link, generated or slotted: { id, anchor }. */
    this._links = []

    this._activeId = ""
    this._intersectionObserver = null
    this._mutationObserver = null
    this._rescanTimer = null
    this._activeFrame = null
  }

  render() {
    /* The title text and the nav label are applied in afterRender. */
    const markup = html`
      <nav>
        <slot name="title"><p class="title" part="title" hidden></p></slot>
        <slot></slot>
        <ul class="list" part="list"></ul>
      </nav>
    `
    return markup
  }

  afterRender() {
    this._nav = this.$("nav")
    this._titleEl = this.$(".title")
    this._list = this.$(".list")
    this._slot = this.shadowRoot.querySelector("slot:not([name])")

    this.listen(this._slot, "slotchange", this._onSlotChange.bind(this))

    /* One delegated listener each for generated links and for slotted links. */
    this.listen(this._list, "click", this._onLinkClick.bind(this))
    this.listen(this, "click", this._onLinkClick.bind(this))

    /* Catches jumps that carry a heading across the whole watch band in one step. */
    this.listen(window, "scroll", this._scheduleActiveUpdate.bind(this), { passive: true, capture: true })

    /* Registered once; every rescan reuses the same teardown. */
    this.onTeardown(() => {
      this._disconnectObservers()
    })

    this._syncLabels()
    this._scanTarget()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._list === undefined || this._list === null) {
      return
    }

    if (name === "target" || name === "depth" || name === "heading-selector" || name === "offset") {
      this._scanTarget()
    } else if (name === "nav-label" || name === "heading" || name === "title") {
      this._syncLabels()
    }
    return
  }

  _syncLabels() {
    let navLabel = this.getAttribute("nav-label")
    if (navLabel === null || navLabel.length === 0) {
      navLabel = t("mj.toc.navLabel")
    }
    this._nav.setAttribute("aria-label", navLabel)

    /* `heading` is the visible title; the global `title` attribute is still honoured. */
    let titleText = this.getAttribute("heading")
    if (titleText === null || titleText.length === 0) {
      titleText = this.getAttribute("title")
    }
    if (titleText !== null && titleText.length > 0) {
      this._titleEl.textContent = titleText
      this._titleEl.hidden = false
    } else {
      this._titleEl.textContent = ""
      this._titleEl.hidden = true
    }
    return
  }

  _offset() {
    let offset = parseInt(this.getAttribute("offset"), 10)
    if (Number.isNaN(offset) === true) {
      offset = 0
    }
    return offset
  }

  _onSlotChange() {
    this._scanTarget()
    return
  }

  /* The slotted section links (manual mode): slotted anchors and anchors inside slotted lists. */
  _slottedAnchors() {
    const anchors = []
    const assigned = this._slot.assignedElements({ flatten: true })

    for (let index = 0; index < assigned.length; index = index + 1) {
      const element = assigned[index]
      if (element.matches("a[href]") === true) {
        anchors.push(element)
      } else {
        const nested = element.querySelectorAll("a[href]")
        for (let position = 0; position < nested.length; position = position + 1) {
          anchors.push(nested[position])
        }
      }
    }
    return anchors
  }

  /* The element a `target` value names: an id first, then a CSS selector. */
  _resolveTarget(targetSel) {
    let targetEl = document.getElementById(targetSel)
    if (targetEl === null) {
      try {
        targetEl = document.querySelector(targetSel)
      } catch (error) {
        targetEl = null
      }
    }
    return targetEl
  }

  /*
   * (Re)build the section list and restart the observers. Manual mode --
   * links slotted by the author -- takes precedence over scanning `target`.
   */
  _scanTarget() {
    this._disconnectObservers()

    const manualAnchors = this._slot.assignedElements({ flatten: true }).length > 0
    if (manualAnchors === true) {
      this._list.hidden = true
      this._scanManualLinks()
    } else {
      this._list.hidden = false
      this._scanHeadings()
    }

    const headings = this._sections.map((section) => section.element)
    this._setupIntersectionObserver(headings)
    this._updateActive()
    return
  }

  _scanManualLinks() {
    const anchors = this._slottedAnchors()
    this._sections = []
    this._links = []

    for (let index = 0; index < anchors.length; index = index + 1) {
      const anchor = anchors[index]
      const href = anchor.getAttribute("href")
      const hashAt = href.indexOf("#")

      if (hashAt !== -1 && hashAt < href.length - 1) {
        let id = href.slice(hashAt + 1)
        try {
          id = decodeURIComponent(id)
        } catch (error) {
          /* Not percent-encoded: use the text as written. */
        }

        const element = document.getElementById(id)
        if (element !== null) {
          this._sections.push({ id: id, text: anchor.textContent.trim(), level: 2, element: element })
          this._links.push({ id: id, anchor: anchor })
        }
      }
    }
    return
  }

  _scanHeadings() {
    this._sections = []
    this._links = []

    const targetSel = this.getAttribute("target")
    let targetEl = null
    if (targetSel !== null && targetSel !== "") {
      targetEl = this._resolveTarget(targetSel)
      if (targetEl === null) {
        console.warn(`<mj-toc>: target "${targetSel}" not found`)
      }
    }

    if (targetEl === null) {
      this._list.textContent = ""
      return
    }

    let depth = parseInt(this.getAttribute("depth"), 10)
    if (Number.isNaN(depth) === true || depth < 1) {
      depth = 2
    }

    let selector = this.getAttribute("heading-selector")
    if (selector === null || selector === "") {
      const levels = []
      for (let level = 2; level <= depth + 1; level = level + 1) {
        levels.push("h" + level)
      }
      selector = levels.join(",")
    }

    let headings = []
    try {
      headings = Array.from(targetEl.querySelectorAll(selector))
    } catch (error) {
      console.warn(`<mj-toc>: heading-selector "${selector}" is not a valid selector`)
    }

    this._ensureHeadingIds(headings)
    this._sections = headings.map(function(el) {
      const levelMatch = el.tagName.match(/^H([1-6])$/)
      return {
        id: el.id,
        text: el.textContent.trim(),
        level: levelMatch !== null ? parseInt(levelMatch[1], 10) : 2,
        element: el
      }
    })

    this._buildList()
    this._setupMutationObserver(targetEl)
    return
  }

  /*
   * Give every heading an id. The slug keeps letters and digits of any
   * script; a heading with no usable characters gets "section-N". Ids are
   * unique across the document, not just among the scanned headings.
   */
  _ensureHeadingIds(headings) {
    const usedIds = new Set()

    for (let index = 0; index < headings.length; index = index + 1) {
      const heading = headings[index]

      if (heading.id === "") {
        let slug = heading.textContent.trim()
          .toLowerCase()
          .replace(/[^\p{L}\p{N}]+/gu, "-")
          .replace(/^-+|-+$/g, "")
        if (slug.length === 0) {
          slug = `section-${index + 1}`
        }

        let candidate = slug
        let suffix = 2
        while (usedIds.has(candidate) === true || document.getElementById(candidate) !== null) {
          candidate = slug + "-" + suffix
          suffix = suffix + 1
        }
        heading.id = candidate
      }
      usedIds.add(heading.id)
    }
    return
  }

  /*
   * Render the sections as nested lists: a heading deeper than the one before
   * it starts a sub-list inside that item, so the hierarchy is in the markup
   * and not only in the indent.
   */
  _buildList() {
    this._list.textContent = ""

    if (this._sections.length === 0) {
      const empty = document.createElement("li")
      empty.className = "empty-notice"
      empty.textContent = t("mj.toc.empty")
      this._list.appendChild(empty)
      return
    }

    /* Open lists from the root down; each entry is { level, list, lastItem }. */
    const stack = [{ level: this._sections[0].level, list: this._list, lastItem: null }]

    for (let index = 0; index < this._sections.length; index = index + 1) {
      const section = this._sections[index]

      while (stack.length > 1 && section.level < stack[stack.length - 1].level) {
        stack.pop()
      }

      let top = stack[stack.length - 1]
      if (section.level > top.level && top.lastItem !== null) {
        const nested = document.createElement("ul")
        nested.className = "nested-list"
        top.lastItem.appendChild(nested)
        top = { level: section.level, list: nested, lastItem: null }
        stack.push(top)
      }

      const li = document.createElement("li")
      li.className = "item"
      li.setAttribute("part", "item")

      const anchor = document.createElement("a")
      anchor.className = "anchor"
      anchor.setAttribute("part", "anchor")
      anchor.setAttribute("href", "#" + encodeURIComponent(section.id))
      anchor.dataset.sectionId = section.id
      anchor.style.setProperty("--mj-toc-depth", String(stack.length - 1))
      anchor.textContent = section.text

      if (section.id === this._activeId) {
        anchor.setAttribute("aria-current", "location")
      }

      li.appendChild(anchor)
      top.list.appendChild(li)
      top.lastItem = li

      this._links.push({ id: section.id, anchor: anchor })
    }
    return
  }

  /*
   * The observer reports headings crossing the band between the offset line
   * and the activation line; each report (and each scroll) recomputes the
   * active section from the position of every heading.
   */
  _setupIntersectionObserver(headings) {
    if (headings.length === 0) {
      return
    }

    const bottomMargin = Math.round((1 - ACTIVATION_LINE) * 100)
    this._intersectionObserver = new IntersectionObserver(
      this._scheduleActiveUpdate.bind(this),
      { rootMargin: `${-this._offset()}px 0px -${bottomMargin}% 0px`, threshold: 0 }
    )

    for (let index = 0; index < headings.length; index = index + 1) {
      this._intersectionObserver.observe(headings[index])
    }
    return
  }

  _setupMutationObserver(targetEl) {
    /* Bursts of mutations (live content) collapse into one rescan. */
    this._mutationObserver = new MutationObserver(() => {
      if (this._rescanTimer === null) {
        this._rescanTimer = window.setTimeout(() => {
          this._rescanTimer = null
          this._scanTarget()
        }, RESCAN_DELAY)
      }
    })
    this._mutationObserver.observe(targetEl, { childList: true, subtree: true, characterData: true })
    return
  }

  _scheduleActiveUpdate() {
    if (this._activeFrame === null) {
      this._activeFrame = window.requestAnimationFrame(() => {
        this._activeFrame = null
        this._updateActive()
      })
    }
    return
  }

  /*
   * The active section is the lowest heading whose top has passed the
   * activation line -- whichever direction the page was scrolled in, and
   * whatever order the links are listed in. Nothing is active above the
   * first heading. The event fires only on a change.
   */
  _updateActive() {
    const line = Math.max(this._offset() + 1, window.innerHeight * ACTIVATION_LINE)

    let active = null
    let activeTop = -Infinity
    for (let index = 0; index < this._sections.length; index = index + 1) {
      const section = this._sections[index]
      if (section.element.isConnected === true) {
        const top = section.element.getBoundingClientRect().top
        if (top <= line && top >= activeTop) {
          active = section
          activeTop = top
        }
      }
    }

    const activeId = active !== null ? active.id : ""
    const previousId = this._activeId
    this._activeId = activeId
    this._updateActiveLink(activeId)

    if (activeId !== previousId) {
      this.emit("mj-toc-active-change", {
        id: activeId,
        element: active !== null ? active.element : null,
        previousId: previousId
      })
    }
    return
  }

  _updateActiveLink(activeId) {
    for (let index = 0; index < this._links.length; index = index + 1) {
      const link = this._links[index]
      if (activeId !== "" && link.id === activeId) {
        link.anchor.setAttribute("aria-current", "location")
      } else {
        link.anchor.removeAttribute("aria-current")
      }
    }
    return
  }

  /* Handles a click on a generated link (shadow list) or a slotted link (host). */
  _onLinkClick(event) {
    if (event.defaultPrevented === true) {
      return
    }

    const path = event.composedPath()
    let link = null
    for (let index = 0; index < this._links.length; index = index + 1) {
      if (link === null && path.indexOf(this._links[index].anchor) !== -1) {
        link = this._links[index]
      }
    }
    if (link === null) {
      return
    }

    const id = link.id
    const targetEl = document.getElementById(id)

    const proceed = this.emit("mj-toc-navigate", {
      id: id,
      element: targetEl,
      originalEvent: event
    }, { cancelable: true })

    if (proceed === false) {
      event.preventDefault()
      return
    }

    if (targetEl !== null) {
      event.preventDefault()

      /* Same result as following the link: the hash changes and Back returns. */
      try {
        window.history.pushState(null, "", "#" + encodeURIComponent(id))
      } catch (error) {
        /* History is not available (sandboxed frame); scrolling still works. */
      }

      const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches
      const behavior = prefersReduced === true ? "instant" : (this.getAttribute("scroll-behavior") || "smooth")

      /* The heading must land below a sticky header of `offset` px. */
      const offset = this._offset()
      const previousMargin = targetEl.style.scrollMarginTop
      if (offset > 0) {
        targetEl.style.scrollMarginTop = `${offset}px`
      }
      targetEl.scrollIntoView({ behavior: behavior, block: "start" })
      if (offset > 0) {
        targetEl.style.scrollMarginTop = previousMargin
      }

      if (targetEl.getAttribute("tabindex") === null) {
        targetEl.tabIndex = -1
        targetEl.addEventListener("blur", function onBlur() {
          targetEl.removeAttribute("tabindex")
          targetEl.removeEventListener("blur", onBlur)
        })
      }
      targetEl.focus({ preventScroll: true })
    }
    return
  }

  _disconnectObservers() {
    if (this._intersectionObserver !== null) {
      this._intersectionObserver.disconnect()
      this._intersectionObserver = null
    }
    if (this._mutationObserver !== null) {
      this._mutationObserver.disconnect()
      this._mutationObserver = null
    }
    if (this._rescanTimer !== null) {
      window.clearTimeout(this._rescanTimer)
      this._rescanTimer = null
    }
    if (this._activeFrame !== null) {
      window.cancelAnimationFrame(this._activeFrame)
      this._activeFrame = null
    }
    return
  }

  get activeId() {
    return this._activeId
  }

  get sections() {
    return this._sections.slice()
  }
}
