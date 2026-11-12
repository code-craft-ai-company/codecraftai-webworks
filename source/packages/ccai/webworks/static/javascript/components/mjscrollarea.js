/*
 * mjscrollarea.js
 *
 * <mj-scroll-area> -- a scrollable region with consistently styled, theme-aware
 * scrollbars while preserving native scroll behavior and keyboard scrollability.
 *
 * Sizing: the host is a column flex container and the viewport fills it, so
 * the area scrolls with a fixed `height` and equally with only a
 * `max-height` (the viewport grows with its content up to the limit).
 *
 * Scrollbars are the browser's own, styled with `scrollbar-color` and
 * `scrollbar-width`:
 *   native                    leave the platform styling untouched
 *   scrollbar-visibility      auto (default): shown when the content overflows
 *                             always: the scrollbar track is always reserved
 *                             hover: the thumb is drawn only while the pointer
 *                             is over the area or focus is inside it
 *
 * Keyboard: the viewport is a tab stop only while its content overflows, so
 * keyboard users can scroll it. A `tabindex` on the host is moved to the
 * viewport (the element that actually scrolls) and then always applies.
 */

import { MjElement } from "../core/mjelement.js";

/* Quiet period after the last scroll event when `scrollend` is not supported. */
const SCROLL_IDLE_MS = 150;

const STYLES = `
:host {
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

/*
 * The properties written by \`overflow-x\`, \`overflow-y\` and
 * \`scroll-padding\` belong to one scroll area: an inline value written by
 * the attribute or an author rule on the element wins over this reset, but a
 * nested scroll area never inherits them.
 */
:host {
  --mj-scroll-overflow-x: initial;
  --mj-scroll-overflow-y: initial;
  --mj-scroll-padding: initial;
}

.viewport {
  flex: 1 1 auto;
  min-block-size: 0;
  inline-size: 100%;
  overflow-x: var(--mj-scroll-overflow-x, hidden);
  overflow-y: var(--mj-scroll-overflow-y, auto);
  scrollbar-width: var(--mj-scroll-scrollbar-width, thin);
  scrollbar-color: var(--mj-scroll-thumb-color, var(--mj-border-strong)) var(--mj-scroll-track-color, transparent);
  scroll-padding: var(--mj-scroll-padding, 0);
  box-sizing: border-box;
  -webkit-overflow-scrolling: touch;
}

:host([native]) .viewport {
  scrollbar-width: auto;
  scrollbar-color: auto;
}

:host([scrollbar-visibility="always"]) .viewport {
  scrollbar-gutter: stable;
}

:host([scrollbar-visibility="hover"]:not([native])) .viewport {
  scrollbar-gutter: stable;
  scrollbar-color: transparent transparent;
}

:host([scrollbar-visibility="hover"]:not([native]):hover) .viewport,
:host([scrollbar-visibility="hover"]:not([native]):focus-within) .viewport {
  scrollbar-color: var(--mj-scroll-thumb-color, var(--mj-border-strong)) var(--mj-scroll-track-color, transparent);
}

.viewport:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: calc(-1 * var(--mj-focus-ring-offset));
}
`;

export class MjScrollArea extends MjElement {
  static tagName = "mj-scroll-area";
  static styles = STYLES;
  static watched = [
    "overflow-x", "overflow-y", "native", "scrollbar-visibility", "scroll-padding",
    "tabindex", "aria-label", "aria-labelledby"
  ];

  constructor() {
    super()
    this._viewport = null
    this._slot = null
    this._scrollRafId = null
    this._scrollIdleTimer = null
    this._resizeObserver = null
    this._observedContent = []

    /* A tabindex the author put on the host, moved to the viewport; null when none. */
    this._viewportTabIndex = null
    this._movingTabIndex = false
  }

  render() {
    const markup = `
      <div class="viewport" part="viewport" role="region">
        <slot></slot>
      </div>
    `
    return markup
  }

  afterRender() {
    this._viewport = this.$(".viewport")
    this._slot = this.$("slot")
    this.listen(this._viewport, "scroll", this._onScroll.bind(this))
    if ("onscrollend" in this._viewport) {
      this.listen(this._viewport, "scrollend", this._onScrollEnd.bind(this))
    }
    this.listen(this._slot, "slotchange", this._observeContent.bind(this))

    this._adoptHostTabIndex()
    this._syncStyles()
    this._syncLabel()
    return
  }

  onConnected() {
    /* Overflow changes when the viewport or the content changes size. */
    if (typeof ResizeObserver === "function") {
      this._resizeObserver = new ResizeObserver(() => {
        this._syncFocusability()
      })
      this._resizeObserver.observe(this._viewport)
      this._observedContent = []
      this._observeContent()
    }

    this.onTeardown(() => {
      if (this._resizeObserver !== null) {
        this._resizeObserver.disconnect()
        this._resizeObserver = null
      }
      this._observedContent = []
      if (this._scrollRafId !== null) {
        window.cancelAnimationFrame(this._scrollRafId)
        this._scrollRafId = null
      }
      if (this._scrollIdleTimer !== null) {
        window.clearTimeout(this._scrollIdleTimer)
        this._scrollIdleTimer = null
      }
    })
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._viewport === undefined || this._viewport === null) {
      return
    }

    if (name === "tabindex") {
      this._adoptHostTabIndex()
    } else if (name === "aria-label" || name === "aria-labelledby") {
      this._syncLabel()
    } else {
      this._syncStyles()
    }
    return
  }

  /*
   * Set a custom property on the host, or remove it when `value` is null so
   * the stylesheet (the component default or an author rule) applies.
   */
  _setCustomProperty(name, value) {
    if (value === null) {
      this.style.removeProperty(name)
    } else {
      this.style.setProperty(name, value)
    }
    return
  }

  _syncStyles() {
    if (this._viewport === null || this._viewport === undefined) {
      return
    }

    const overflowX = this.getAttribute("overflow-x")
    const overflowY = this.getAttribute("overflow-y")
    const scrollPadding = this.getAttribute("scroll-padding")

    this._setCustomProperty("--mj-scroll-overflow-x", overflowX !== null && overflowX.length > 0 ? overflowX : null)
    this._setCustomProperty("--mj-scroll-overflow-y", overflowY !== null && overflowY.length > 0 ? overflowY : null)
    this._setCustomProperty("--mj-scroll-padding", scrollPadding !== null && scrollPadding.length > 0 ? scrollPadding : null)

    this._syncFocusability()
    return
  }

  /*
   * Name the region from the host's aria-label. An aria-labelledby on the
   * host refers to light-DOM ids, which the viewport inside the shadow tree
   * cannot reference, so the text of the referenced elements is used.
   */
  _syncLabel() {
    const label = this.getAttribute("aria-label") || ""
    const labelledBy = this.getAttribute("aria-labelledby") || ""
    let name = label.trim()

    if (name.length === 0 && labelledBy.trim().length > 0) {
      const root = this.getRootNode()
      const ids = labelledBy.trim().split(/\s+/)
      const parts = []
      for (let index = 0; index < ids.length; index = index + 1) {
        const target = typeof root.getElementById === "function" ? root.getElementById(ids[index]) : null
        if (target !== null) {
          parts.push(target.textContent.trim())
        }
      }
      name = parts.join(" ").trim()
    }

    if (name.length > 0) {
      this._viewport.setAttribute("aria-label", name)
    } else {
      this._viewport.removeAttribute("aria-label")
    }
    return
  }

  /* Move a tabindex placed on the host to the viewport. */
  _adoptHostTabIndex() {
    if (this._movingTabIndex === true) {
      return
    }

    const hostTabIndex = this.getAttribute("tabindex")
    if (hostTabIndex !== null) {
      this._viewportTabIndex = hostTabIndex
      this._movingTabIndex = true
      this.removeAttribute("tabindex")
      this._movingTabIndex = false
    }

    this._syncFocusability()
    return
  }

  _overflows() {
    const viewport = this._viewport
    const overflows = viewport.scrollHeight > viewport.clientHeight + 1 ||
      viewport.scrollWidth > viewport.clientWidth + 1
    return overflows
  }

  /* The viewport is a tab stop while there is something to scroll. */
  _syncFocusability() {
    if (this._viewport === null || this._viewport === undefined) {
      return
    }

    if (this._viewportTabIndex !== null) {
      this._viewport.setAttribute("tabindex", this._viewportTabIndex)
    } else if (this._overflows() === true) {
      this._viewport.setAttribute("tabindex", "0")
    } else {
      this._viewport.removeAttribute("tabindex")
    }
    return
  }

  /* Keep the resize observer on the elements currently slotted. */
  _observeContent() {
    if (this._resizeObserver === null || this._slot === null) {
      this._syncFocusability()
      return
    }

    const content = this._slot.assignedElements({ flatten: true })
    for (let index = 0; index < this._observedContent.length; index = index + 1) {
      if (content.indexOf(this._observedContent[index]) < 0) {
        this._resizeObserver.unobserve(this._observedContent[index])
      }
    }
    for (let index = 0; index < content.length; index = index + 1) {
      if (this._observedContent.indexOf(content[index]) < 0) {
        this._resizeObserver.observe(content[index])
      }
    }
    this._observedContent = content

    this._syncFocusability()
    return
  }

  _onScroll() {
    if (this._scrollRafId !== null) {
      return
    }
    this._scrollRafId = window.requestAnimationFrame(() => {
      this._scrollRafId = null
      if (this._viewport === null) {
        return
      }
      this.emit("mj-scroll", {
        scrollTop: this._viewport.scrollTop,
        scrollLeft: this._viewport.scrollLeft,
        scrollHeight: this._viewport.scrollHeight,
        scrollWidth: this._viewport.scrollWidth
      })

      /* Where the native `scrollend` exists it reports the end; no timer then. */
      if (("onscrollend" in this._viewport) === false) {
        if (this._scrollIdleTimer !== null) {
          window.clearTimeout(this._scrollIdleTimer)
        }
        this._scrollIdleTimer = window.setTimeout(() => {
          this._scrollIdleTimer = null
          this._onScrollEnd()
        }, SCROLL_IDLE_MS)
      }
    })
    return
  }

  _onScrollEnd() {
    if (this._viewport === null) {
      return
    }
    this.emit("mj-scroll-end", {
      scrollTop: this._viewport.scrollTop,
      scrollLeft: this._viewport.scrollLeft
    })
    return
  }

  get scrollTop() {
    return this._viewport !== null ? this._viewport.scrollTop : 0
  }

  set scrollTop(value) {
    if (this._viewport !== null) {
      this._viewport.scrollTop = value
    }
    return
  }

  get scrollLeft() {
    return this._viewport !== null ? this._viewport.scrollLeft : 0
  }

  set scrollLeft(value) {
    if (this._viewport !== null) {
      this._viewport.scrollLeft = value
    }
    return
  }

  get scrollHeight() {
    return this._viewport !== null ? this._viewport.scrollHeight : 0
  }

  get scrollWidth() {
    return this._viewport !== null ? this._viewport.scrollWidth : 0
  }
}
