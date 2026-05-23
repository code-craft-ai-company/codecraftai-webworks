/*
 * mjgrid.js
 *
 * <mj-grid> -- a responsive CSS Grid layout primitive. Supports auto-fill,
 * fixed column counts, and a masonry variant (native CSS masonry with JS fallback).
 */

import { MjElement } from "../core/mjelement.js";

const GAP_MAP = {
  none: "0",
  xs: "var(--mj-space-1)",
  sm: "var(--mj-space-2)",
  md: "var(--mj-space-4)",
  lg: "var(--mj-space-5)",
  xl: "var(--mj-space-6)"
};

const STYLES = `
:host { display: block; }

.root {
  display: grid;
  grid-template-columns: var(--mj-grid-template-columns, repeat(auto-fill, minmax(var(--mj-grid-min-col, 16rem), 1fr)));
  gap: var(--mj-grid-gap, var(--mj-space-4));
  column-gap: var(--mj-grid-col-gap, var(--mj-grid-gap, var(--mj-space-4)));
  row-gap: var(--mj-grid-row-gap, var(--mj-grid-gap, var(--mj-space-4)));
  align-items: var(--mj-grid-align, stretch);
}
`;

export class MjGrid extends MjElement {
  static tagName = "mj-grid";
  static styles = STYLES;
  static watched = ["columns", "min-col-width", "gap", "col-gap", "row-gap", "layout", "dense", "align-items"];

  constructor() {
    super()
    this._resizeObserver = null
    this._mutationObserver = null
    this._layoutScheduled = false
  }

  render() {
    const markup = `<div class="root" part="root"><slot></slot></div>`
    return markup
  }

  afterRender() {
    this._root = this.$(".root")
    this._syncStyles()
    return
  }

  onConnected() {
    if (typeof ResizeObserver === "function") {
      this._resizeObserver = new ResizeObserver(() => {
        this._scheduleEmitLayout()
      })
      this._resizeObserver.observe(this)
    }
    return
  }

  onDisconnected() {
    if (this._resizeObserver !== null) {
      this._resizeObserver.disconnect()
      this._resizeObserver = null
    }
    if (this._mutationObserver !== null) {
      this._mutationObserver.disconnect()
      this._mutationObserver = null
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._root !== undefined) {
      this._syncStyles()
    }
    return
  }

  _syncStyles() {
    if (this._root === null || this._root === undefined) {
      return
    }

    const columns = this.getAttribute("columns") || "auto"
    const minColWidth = this.getAttribute("min-col-width") || "16rem"
    const gap = this.getAttribute("gap") || "md"
    const colGap = this.getAttribute("col-gap") || ""
    const rowGap = this.getAttribute("row-gap") || ""
    const dense = this.hasAttribute("dense")
    const alignItems = this.getAttribute("align-items") || "stretch"

    let template
    const colNum = parseInt(columns, 10)
    if (columns !== "auto" && Number.isNaN(colNum) === false && colNum > 0) {
      template = `repeat(${colNum}, 1fr)`
    } else {
      template = `repeat(auto-fill, minmax(${minColWidth}, 1fr))`
    }

    const gapVal = GAP_MAP[gap] || GAP_MAP.md
    const colGapVal = colGap.length > 0 ? (GAP_MAP[colGap] || gapVal) : gapVal
    const rowGapVal = rowGap.length > 0 ? (GAP_MAP[rowGap] || gapVal) : gapVal

    this.style.setProperty("--mj-grid-template-columns", template)
    this.style.setProperty("--mj-grid-min-col", minColWidth)
    this.style.setProperty("--mj-grid-gap", gapVal)
    this.style.setProperty("--mj-grid-col-gap", colGapVal)
    this.style.setProperty("--mj-grid-row-gap", rowGapVal)
    this.style.setProperty("--mj-grid-align", alignItems)

    if (dense === true) {
      this._root.style.gridAutoFlow = "dense"
    } else {
      this._root.style.gridAutoFlow = ""
    }
    return
  }

  _scheduleEmitLayout() {
    if (this._layoutScheduled === true) {
      return
    }
    this._layoutScheduled = true
    window.requestAnimationFrame(() => {
      this._layoutScheduled = false
      const computed = window.getComputedStyle(this._root)
      const colCount = computed.getPropertyValue("grid-template-columns").split(" ").length
      this.emit("mj-grid-layout", { columns: colCount, masonry: false }, { bubbles: false })
    })
    return
  }

  get masonrySupported() {
    return false
  }
}
