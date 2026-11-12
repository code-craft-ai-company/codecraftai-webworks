/*
 * mjgrid.js
 *
 * <mj-grid> -- a responsive CSS Grid layout primitive.
 *
 * Column modes
 *   - auto (default): as many columns of at least `min-col-width` as fit.
 *   - columns="N": exactly N equal columns. The tracks may shrink to any
 *     width, so the grid never overflows a narrow container.
 *   - columns="N" together with `min-col-width`: AT MOST N columns, each at
 *     least `min-col-width` wide; the count drops as the container narrows.
 *   - layout="masonry": items flow into balanced columns of their own
 *     height (CSS multi-column), using the same `columns` / `min-col-width`
 *     settings. Items keep their DOM order, top to bottom within a column.
 *
 * A custom property is written on the host only for an attribute that is
 * present, so stylesheet rules such as `mj-grid { --mj-grid-gap: 2rem }`
 * apply whenever the matching attribute is absent. The properties belong to
 * one grid: the host resets them, so a nested grid never inherits the
 * columns, gaps or alignment of the grid around it.
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

const DEFAULT_MIN_COL_WIDTH = "16rem";

/* The column gap as the stylesheet resolves it; used inside track maths. */
const COLUMN_GAP = "var(--mj-grid-col-gap, var(--mj-grid-gap, var(--mj-space-4)))";

const STYLES = `
:host { display: block; }

/*
 * Per-element layout properties: an inline value written by an attribute or
 * an author rule on the element wins over this reset, an ancestor's value
 * does not reach the grid.
 */
:host {
  --mj-grid-template-columns: initial;
  --mj-grid-column-count: initial;
  --mj-grid-masonry-col-width: initial;
  --mj-grid-min-col: initial;
  --mj-grid-gap: initial;
  --mj-grid-col-gap: initial;
  --mj-grid-row-gap: initial;
  --mj-grid-align: initial;
}

.root {
  position: relative;
  display: grid;
  grid-template-columns: var(
    --mj-grid-template-columns,
    repeat(auto-fill, minmax(min(var(--mj-grid-min-col, 16rem), 100%), 1fr))
  );
  gap: var(--mj-grid-gap, var(--mj-space-4));
  column-gap: var(--mj-grid-col-gap, var(--mj-grid-gap, var(--mj-space-4)));
  row-gap: var(--mj-grid-row-gap, var(--mj-grid-gap, var(--mj-space-4)));
  align-items: var(--mj-grid-align, stretch);
}

:host([dense]) .root {
  grid-auto-flow: dense;
}

/*
 * Masonry: balanced columns of variable-height items. Rows do not exist in
 * a multi-column box, so the row gap is a margin under every item and the
 * margin of the last row is taken back off the container.
 */
:host([layout="masonry"]) .root {
  display: block;
  column-count: var(--mj-grid-column-count, auto);
  column-width: var(--mj-grid-masonry-col-width, var(--mj-grid-min-col, 16rem));
  margin-block-end: calc(-1 * var(--mj-grid-row-gap, var(--mj-grid-gap, var(--mj-space-4))));
}

:host([layout="masonry"]) ::slotted(*) {
  break-inside: avoid;
  margin-block: 0 var(--mj-grid-row-gap, var(--mj-grid-gap, var(--mj-space-4)));
}
`;

export class MjGrid extends MjElement {
  static tagName = "mj-grid";
  static styles = STYLES;
  static watched = ["columns", "min-col-width", "gap", "col-gap", "row-gap", "layout", "dense", "align-items"];

  constructor() {
    super()
    this._root = null
    this._resizeObserver = null
    this._layoutFrame = null
    this._warnedMinColWidth = null
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

    this.onTeardown(() => {
      if (this._resizeObserver !== null) {
        this._resizeObserver.disconnect()
        this._resizeObserver = null
      }
      if (this._layoutFrame !== null) {
        window.cancelAnimationFrame(this._layoutFrame)
        this._layoutFrame = null
      }
    })
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._root === undefined || this._root === null) {
      return
    }

    this._syncStyles()

    /* The column count may have changed; report it like a resize does. */
    if (oldValue !== newValue) {
      this._scheduleEmitLayout()
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

  /* The fixed column count from `columns`, or 0 for the auto mode. */
  _fixedColumnCount() {
    const columns = this.getAttribute("columns") || "auto"
    const parsed = parseInt(columns, 10)
    let count = 0

    if (columns !== "auto" && Number.isNaN(parsed) === false && parsed > 0) {
      count = parsed
    }

    return count
  }

  /*
   * The `min-col-width` attribute when it is a usable CSS length, otherwise
   * null. An unusable value would invalidate the whole track list.
   */
  _minColWidth() {
    const attribute = this.getAttribute("min-col-width")
    let width = null

    if (attribute !== null && attribute.trim().length > 0) {
      const supported = typeof CSS === "undefined" || CSS.supports("inline-size", attribute) === true
      if (supported === true) {
        width = attribute.trim()
      } else if (this._warnedMinColWidth !== attribute) {
        this._warnedMinColWidth = attribute
        console.warn(`[mj-grid] min-col-width "${attribute}" is not a CSS length; using ${DEFAULT_MIN_COL_WIDTH}.`)
      }
    }

    return width
  }

  _syncStyles() {
    if (this._root === null || this._root === undefined) {
      return
    }

    const columnCount = this._fixedColumnCount()
    const minColWidth = this._minColWidth()
    const gap = this.getAttribute("gap")
    const colGap = this.getAttribute("col-gap")
    const rowGap = this.getAttribute("row-gap")
    const alignItems = this.getAttribute("align-items")

    let template = null
    let masonryColumnWidth = null

    if (columnCount > 0 && minColWidth !== null) {
      /*
       * At most `columnCount` columns: a track is never narrower than an
       * equal share of the row, so no more than that many fit, and never
       * narrower than min-col-width (or the container itself), so the count
       * drops when the container is too narrow for all of them.
       */
      const share = `(100% - ${columnCount - 1} * ${COLUMN_GAP}) / ${columnCount}`
      template = `repeat(auto-fill, minmax(max(min(${minColWidth}, 100%), ${share}), 1fr))`
    } else if (columnCount > 0) {
      template = `repeat(${columnCount}, minmax(0, 1fr))`
      masonryColumnWidth = "auto"
    }

    this._setCustomProperty("--mj-grid-template-columns", template)
    this._setCustomProperty("--mj-grid-column-count", columnCount > 0 ? String(columnCount) : null)
    this._setCustomProperty("--mj-grid-masonry-col-width", masonryColumnWidth)
    this._setCustomProperty("--mj-grid-min-col", minColWidth)

    this._setCustomProperty("--mj-grid-gap", gap !== null ? (GAP_MAP[gap] || GAP_MAP.md) : null)
    this._setCustomProperty("--mj-grid-col-gap", colGap !== null && GAP_MAP[colGap] !== undefined ? GAP_MAP[colGap] : null)
    this._setCustomProperty("--mj-grid-row-gap", rowGap !== null && GAP_MAP[rowGap] !== undefined ? GAP_MAP[rowGap] : null)
    this._setCustomProperty("--mj-grid-align", alignItems !== null && alignItems.length > 0 ? alignItems : null)
    return
  }

  /*
   * The number of columns currently laid out, or 0 while the grid is not
   * rendered (display: none or detached), when no layout exists to count.
   */
  _countColumns() {
    let count = 0
    const rendered = this._root !== null && this._root !== undefined && this._root.getClientRects().length > 0

    if (rendered === true && this.getAttribute("layout") === "masonry") {
      /* Multi-column boxes expose no track list; count distinct item columns. */
      const slot = this._root.querySelector("slot")
      const items = slot !== null ? slot.assignedElements({ flatten: true }) : []
      const offsets = []
      for (let index = 0; index < items.length; index = index + 1) {
        const rects = items[index].getClientRects()
        if (rects.length > 0) {
          const offset = Math.round(rects[0].left)
          if (offsets.indexOf(offset) < 0) {
            offsets.push(offset)
          }
        }
      }
      count = offsets.length
    } else if (rendered === true) {
      const tracks = window.getComputedStyle(this._root).getPropertyValue("grid-template-columns").trim()
      if (tracks.length > 0 && tracks !== "none") {
        count = tracks.split(/\s+/).length
      }
    }

    return count
  }

  _scheduleEmitLayout() {
    if (this._layoutFrame !== null) {
      return
    }
    this._layoutFrame = window.requestAnimationFrame(() => {
      this._layoutFrame = null
      const columns = this._countColumns()
      if (columns > 0) {
        const masonry = this.getAttribute("layout") === "masonry"
        this.emit("mj-grid-layout", { columns: columns, masonry: masonry }, { bubbles: false })
      }
    })
    return
  }

  /*
   * True when the browser lays out masonry natively. The masonry layout is
   * currently always built with CSS multi-column, so this is false.
   */
  get masonrySupported() {
    return false
  }
}
