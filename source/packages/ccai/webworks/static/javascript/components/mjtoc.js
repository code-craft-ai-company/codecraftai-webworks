/*
 * mjtoc.js
 *
 * <mj-toc> -- in-page table of contents with scroll-spy.
 * Scans headings in a target element and builds anchor links.
 * Uses IntersectionObserver for scroll-spy; MutationObserver for dynamic content.
 *
 * WAI-ARIA: nav landmark; aria-current="true" on active section link.
 */

import { MjElement, nextId } from "../core/mjelement.js";
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
  margin-bottom: var(--mj-space-3);
  padding: 0;
}

.list,
.nested-list {
  list-style: none;
  margin: 0; padding: 0;
}

.item { display: flex; }

.anchor {
  display: block;
  width: 100%;
  padding: var(--mj-space-1) var(--mj-space-3);
  font-size: var(--mj-toc-font-size, var(--mj-font-size-sm));
  color: var(--mj-toc-link-color, var(--mj-text-muted));
  text-decoration: none;
  border-inline-start: 2px solid transparent;
  transition: color var(--mj-motion-fast) var(--mj-motion-ease),
              border-color var(--mj-motion-fast) var(--mj-motion-ease);
  border-radius: 0 var(--mj-radius-sm) var(--mj-radius-sm) 0;
  line-height: 1.4;
}
.anchor:hover { color: var(--mj-toc-link-color-hover, var(--mj-text)); }
.anchor:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.anchor[aria-current="true"] {
  color: var(--mj-toc-active-color, var(--mj-accent));
  border-inline-start: var(--mj-toc-active-border, 2px solid var(--mj-accent));
  font-weight: var(--mj-font-weight-medium);
}

.nested-list .anchor {
  padding-inline-start: calc(var(--mj-space-3) + var(--mj-toc-indent, var(--mj-space-4)));
}
.nested-list .nested-list .anchor {
  padding-inline-start: calc(var(--mj-space-3) + calc(var(--mj-toc-indent, var(--mj-space-4)) * 2));
}

.empty-notice {
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text-muted);
  padding: var(--mj-space-2) var(--mj-space-3);
}
`;

export class MjToc extends MjElement {
  static tagName = "mj-toc";
  static styles = STYLES;
  static watched = ["target", "depth", "heading-selector", "sticky", "nav-label", "title", "offset"];

  constructor() {
    super();
    this._sections = [];
    this._activeId = "";
    this._intersectionObserver = null;
    this._mutationObserver = null;
  }

  render() {
    const navLabel = this.getAttribute("nav-label") || t("mj.toc.navLabel") || "On this page";
    const titleText = this.getAttribute("title") || "";

    const markup = `
      <nav aria-label="${navLabel}">
        ${titleText.length > 0 ? `<p class="title" part="title">${titleText}</p>` : ""}
        <slot></slot>
        <ul class="list" part="list" id="mj-toc-list"></ul>
      </nav>
    `;
    return markup
  }

  afterRender() {
    this._list = this.$(".list");
    this._slot = this.shadowRoot.querySelector("slot");

    if (this._slot !== null) {
      this.listen(this._slot, "slotchange", this._onSlotChange.bind(this));
    }

    this._scanTarget();
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "target" || name === "depth" || name === "heading-selector") {
      this._scanTarget();
    }
    return
  }

  onDisconnected() {
    this._disconnectObservers();
    return
  }

  _onSlotChange() {
    const assigned = this._slot.assignedElements({ flatten: true });
    if (assigned.length > 0) {
      this._list.style.display = "none";
    } else {
      this._list.style.display = "";
      this._scanTarget();
    }
    return
  }

  _scanTarget() {
    this._disconnectObservers();

    const targetSel = this.getAttribute("target");
    if (targetSel === null || targetSel === "") {
      return
    }

    const targetEl = document.querySelector(targetSel);
    if (targetEl === null) {
      console.warn(`<mj-toc>: target "${targetSel}" not found`);
      return
    }

    const depth = parseInt(this.getAttribute("depth") || "2", 10);
    let selector = this.getAttribute("heading-selector");
    if (selector === null || selector === "") {
      const levels = [];
      for (let level = 2; level <= depth + 1; level = level + 1) {
        levels.push("h" + level);
      }
      selector = levels.join(",");
    }

    const headings = Array.from(targetEl.querySelectorAll(selector));
    this._ensureHeadingIds(headings);
    this._sections = headings.map(function(el) {
      return {
        id: el.id,
        text: el.textContent.trim(),
        level: parseInt(el.tagName.slice(1), 10),
        element: el
      };
    });

    this._buildList();
    this._setupIntersectionObserver(headings, targetEl);
    this._setupMutationObserver(targetEl, selector);
    return
  }

  _ensureHeadingIds(headings) {
    const usedIds = new Set();
    for (let i = 0; i < headings.length; i = i + 1) {
      const heading = headings[i];
      if (heading.id === "") {
        let slug = heading.textContent.trim()
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, "-")
          .replace(/^-|-$/g, "");
        let candidate = slug;
        let suffix = 2;
        while (usedIds.has(candidate) === true) {
          candidate = slug + "-" + suffix;
          suffix = suffix + 1;
        }
        heading.id = candidate;
        console.info(`<mj-toc>: assigned id "${candidate}" to heading "${heading.textContent.trim()}"`);
      }
      usedIds.add(heading.id);
    }
    return
  }

  _buildList() {
    this._list.innerHTML = "";

    if (this._sections.length === 0) {
      const empty = document.createElement("li");
      empty.className = "empty-notice";
      empty.textContent = t("mj.toc.empty") || "No sections found";
      this._list.appendChild(empty);
      return
    }

    const minLevel = this._sections.reduce(function(min, s) { return Math.min(min, s.level); }, 99);

    for (let i = 0; i < this._sections.length; i = i + 1) {
      const section = this._sections[i];
      const li = document.createElement("li");
      li.className = "item";
      li.setAttribute("part", "item");

      const anchor = document.createElement("a");
      anchor.className = "anchor";
      anchor.setAttribute("part", "anchor");
      anchor.setAttribute("href", "#" + section.id);
      anchor.dataset.sectionId = section.id;

      if (section.level > minLevel) {
        anchor.style.paddingInlineStart = `calc(var(--mj-space-3) + calc(${section.level - minLevel} * var(--mj-toc-indent, var(--mj-space-4))))`;
      }

      if (section.id === this._activeId) {
        anchor.setAttribute("aria-current", "true");
      }

      anchor.textContent = section.text;
      this.listen(anchor, "click", this._onLinkClick.bind(this));
      li.appendChild(anchor);
      this._list.appendChild(li);
    }
    return
  }

  _setupIntersectionObserver(headings, targetEl) {
    if (headings.length === 0) {
      return
    }
    const offset = parseInt(this.getAttribute("offset") || "0", 10);
    const rootMarginTop = -offset + "px";

    this._intersectionObserver = new IntersectionObserver(
      this._onIntersection.bind(this),
      { rootMargin: `${rootMarginTop} 0px -60% 0px`, threshold: 0 }
    );

    for (let i = 0; i < headings.length; i = i + 1) {
      this._intersectionObserver.observe(headings[i]);
    }

    this.onTeardown(() => {
      if (this._intersectionObserver !== null) {
        this._intersectionObserver.disconnect();
        this._intersectionObserver = null;
      }
    });
    return
  }

  _setupMutationObserver(targetEl, selector) {
    this._mutationObserver = new MutationObserver(() => {
      this._scanTarget();
    });
    this._mutationObserver.observe(targetEl, { childList: true, subtree: true });
    this.onTeardown(() => {
      if (this._mutationObserver !== null) {
        this._mutationObserver.disconnect();
        this._mutationObserver = null;
      }
    });
    return
  }

  _onIntersection(entries) {
    let topmost = null;
    let topmostY = Infinity;

    for (let i = 0; i < entries.length; i = i + 1) {
      const entry = entries[i];
      if (entry.isIntersecting === true) {
        const y = entry.boundingClientRect.top;
        if (y < topmostY) {
          topmostY = y;
          topmost = entry.target;
        }
      }
    }

    if (topmost !== null) {
      const previousId = this._activeId;
      this._activeId = topmost.id;
      this._updateActiveLink(this._activeId);
      this.emit("mj-toc-active-change", {
        id: this._activeId,
        element: topmost,
        previousId: previousId
      });
    }
    return
  }

  _updateActiveLink(activeId) {
    const anchors = this._list.querySelectorAll(".anchor");
    for (let i = 0; i < anchors.length; i = i + 1) {
      const anchor = anchors[i];
      if (anchor.dataset.sectionId === activeId) {
        anchor.setAttribute("aria-current", "true");
      } else {
        anchor.removeAttribute("aria-current");
      }
    }
    return
  }

  _onLinkClick(event) {
    const anchor = event.currentTarget;
    const id = anchor.dataset.sectionId;
    const targetEl = document.getElementById(id);

    const proceed = this.emit("mj-toc-navigate", {
      id: id,
      element: targetEl,
      originalEvent: event
    }, { cancelable: true });

    if (proceed === false) {
      event.preventDefault();
      return
    }

    if (targetEl !== null) {
      event.preventDefault();
      const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      const behavior = prefersReduced === true ? "instant" : (this.getAttribute("scroll-behavior") || "smooth");
      targetEl.scrollIntoView({ behavior: behavior });

      if (targetEl.tabIndex === -1 || targetEl.getAttribute("tabindex") === null) {
        targetEl.tabIndex = -1;
        targetEl.addEventListener("blur", function onBlur() {
          targetEl.removeAttribute("tabindex");
          targetEl.removeEventListener("blur", onBlur);
        });
      }
      targetEl.focus({ preventScroll: true });
    }
    return
  }

  _disconnectObservers() {
    if (this._intersectionObserver !== null) {
      this._intersectionObserver.disconnect();
      this._intersectionObserver = null;
    }
    if (this._mutationObserver !== null) {
      this._mutationObserver.disconnect();
      this._mutationObserver = null;
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
