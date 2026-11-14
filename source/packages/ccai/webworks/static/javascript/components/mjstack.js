/*
 * mjstack.js
 *
 * <mj-stack> -- a one-dimensional flexbox layout primitive that arranges
 * slotted children along a single axis with uniform gap spacing.
 *
 * The host is itself a flex container whose only item, the stack, grows to
 * fill it. A stack with a fixed height, or one stretched by a grid, flex or
 * dock parent, therefore has the full height available for `justify`,
 * flexible spacers and cross-axis alignment.
 *
 * A custom property is written on the host only for an attribute that is
 * present, so stylesheet rules such as `mj-stack { --mj-stack-gap: 2rem }`
 * apply whenever the matching attribute is absent. The properties belong to
 * one stack: the host resets them, so a nested stack never inherits the
 * direction, gap or alignment of the stack around it.
 *
 * `align` is also the legacy HTML presentational attribute, which browsers
 * map to `text-align` on any element; the host takes its text alignment from
 * its parent instead, so `align` only aligns the children.
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

const JUSTIFY_MAP = {
  start: "flex-start",
  center: "center",
  end: "flex-end",
  between: "space-between",
  around: "space-around",
  evenly: "space-evenly"
};

const STYLES = `
:host {
  display: flex;
  flex-direction: column;
}
:host([inline]) { display: inline-flex; }

/*
 * Per-element layout properties: an inline value written by an attribute or
 * an author rule on the element wins over this reset, an ancestor's value
 * does not reach the stack.
 */
:host {
  --mj-stack-direction: initial;
  --mj-stack-gap: initial;
  --mj-stack-align: initial;
  --mj-stack-justify: initial;
  --mj-stack-wrap: initial;
}

/* Cancel the legacy align => text-align presentational hint. */
:host([align]) { text-align: inherit; }

.root {
  position: relative;
  flex: 1 1 auto;
  min-inline-size: 0;
  display: flex;
  flex-direction: var(--mj-stack-direction, column);
  gap: var(--mj-stack-gap, var(--mj-space-4));
  align-items: var(--mj-stack-align, stretch);
  justify-content: var(--mj-stack-justify, flex-start);
  flex-wrap: var(--mj-stack-wrap, nowrap);
}
`;

export class MjStack extends MjElement {
  static tagName = "mj-stack";
  static styles = STYLES;
  static watched = ["direction", "gap", "align", "justify", "wrap", "reverse", "inline"];

  constructor() {
    super()
    this._root = null
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

  onAttributeChanged(name, oldValue, newValue) {
    if (this._root === undefined || this._root === null) {
      return
    }
    this._syncStyles()
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
    if (this._root === null || this._root === undefined) {
      return
    }

    const direction = this.getAttribute("direction")
    const gap = this.getAttribute("gap")
    const align = this.getAttribute("align")
    const justify = this.getAttribute("justify")
    const wrap = this.hasAttribute("wrap")
    const reverse = this.hasAttribute("reverse")

    let flexDirection = null
    if (direction === "horizontal") {
      flexDirection = reverse === true ? "row-reverse" : "row"
    } else if (direction !== null || reverse === true) {
      flexDirection = reverse === true ? "column-reverse" : "column"
    }

    this._setCustomProperty("--mj-stack-direction", flexDirection)
    this._setCustomProperty("--mj-stack-gap", gap !== null ? (GAP_MAP[gap] || GAP_MAP.md) : null)
    this._setCustomProperty("--mj-stack-align", align !== null && align.length > 0 ? align : null)
    this._setCustomProperty("--mj-stack-justify", justify !== null ? (JUSTIFY_MAP[justify] || "flex-start") : null)
    this._setCustomProperty("--mj-stack-wrap", wrap === true ? "wrap" : null)
    return
  }

  get childCount() {
    const slot = this._root !== null && this._root !== undefined ? this._root.querySelector("slot") : null
    if (slot === null) {
      return 0
    }
    const count = slot.assignedElements().length
    return count
  }
}
