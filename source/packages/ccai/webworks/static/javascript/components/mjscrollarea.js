/*
 * mjscrollarea.js
 *
 * <mj-scroll-area> -- a scrollable region with consistently styled, theme-aware
 * scrollbars while preserving native scroll behavior and keyboard scrollability.
 */

import { MjElement } from "../core/mjelement.js";

const STYLES = `
:host {
  display: block;
  position: relative;
  overflow: hidden;
}

.viewport {
  overflow-x: var(--mj-scroll-overflow-x, hidden);
  overflow-y: var(--mj-scroll-overflow-y, auto);
  block-size: 100%;
  inline-size: 100%;
  scrollbar-width: var(--mj-scroll-scrollbar-width, thin);
  scrollbar-color: var(--mj-scroll-thumb-color, var(--mj-border-strong)) var(--mj-scroll-track-color, transparent);
  scroll-padding: var(--mj-scroll-padding, 0);
  box-sizing: border-box;
  -webkit-overflow-scrolling: touch;
}

.viewport:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: calc(-1 * var(--mj-focus-ring-offset));
}
`;

export class MjScrollArea extends MjElement {
  static tagName = "mj-scroll-area";
  static styles = STYLES;
  static watched = ["overflow-x", "overflow-y", "native", "scrollbar-visibility", "scroll-padding", "tabindex"];

  constructor() {
    super()
    this._viewport = null
    this._scrollRafId = null
    this._scrollIdleTimer = null
  }

  render() {
    const tabIdx = this.getAttribute("tabindex") || "0"
    const label = this.getAttribute("aria-label") || ""
    const markup = `
      <div
        class="viewport"
        part="viewport"
        role="region"
        tabindex="${tabIdx}"
        ${label.length > 0 ? `aria-label="${label}"` : ""}
      >
        <slot></slot>
      </div>
    `
    return markup
  }

  afterRender() {
    this._viewport = this.$(".viewport")
    this._syncStyles()
    this.listen(this._viewport, "scroll", this._onScroll.bind(this))
    if ("onscrollend" in this._viewport) {
      this.listen(this._viewport, "scrollend", this._onScrollEnd.bind(this))
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._viewport !== undefined) {
      this._syncStyles()
    }
    return
  }

  _syncStyles() {
    if (this._viewport === null || this._viewport === undefined) {
      return
    }

    const overflowX = this.getAttribute("overflow-x") || "hidden"
    const overflowY = this.getAttribute("overflow-y") || "auto"
    const scrollPadding = this.getAttribute("scroll-padding") || "0"
    const tabIdx = this.getAttribute("tabindex") || "0"

    this.style.setProperty("--mj-scroll-overflow-x", overflowX)
    this.style.setProperty("--mj-scroll-overflow-y", overflowY)
    this.style.setProperty("--mj-scroll-padding", scrollPadding)
    this._viewport.setAttribute("tabindex", tabIdx)

    const label = this.getAttribute("aria-label") || ""
    if (label.length > 0) {
      this._viewport.setAttribute("aria-label", label)
    }
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

      if (this._scrollIdleTimer !== null) {
        clearTimeout(this._scrollIdleTimer)
      }
      this._scrollIdleTimer = setTimeout(() => {
        this._scrollIdleTimer = null
        this._onScrollEnd()
      }, 150)
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
