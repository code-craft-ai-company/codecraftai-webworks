/*
 * mjstack.js
 *
 * <mj-stack> -- a one-dimensional flexbox layout primitive that arranges
 * slotted children along a single axis with uniform gap spacing.
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
:host { display: block; }
:host([inline]) { display: inline-block; }

.root {
  display: flex;
  flex-direction: var(--mj-stack-direction, column);
  gap: var(--mj-stack-gap, var(--mj-space-4));
  align-items: var(--mj-stack-align, stretch);
  justify-content: var(--mj-stack-justify, flex-start);
  flex-wrap: var(--mj-stack-wrap, nowrap);
}
:host([inline]) .root { display: inline-flex; }
`;

export class MjStack extends MjElement {
  static tagName = "mj-stack";
  static styles = STYLES;
  static watched = ["direction", "gap", "align", "justify", "wrap", "reverse", "inline"];

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
    if (this._root !== undefined) {
      this._syncStyles()
    }
    return
  }

  _syncStyles() {
    if (this._root === null || this._root === undefined) {
      return
    }

    const direction = this.getAttribute("direction") || "vertical"
    const gap = this.getAttribute("gap") || "md"
    const align = this.getAttribute("align") || "stretch"
    const justify = this.getAttribute("justify") || "start"
    const wrap = this.hasAttribute("wrap")
    const reverse = this.hasAttribute("reverse")

    let flexDir
    if (direction === "horizontal") {
      flexDir = reverse === true ? "row-reverse" : "row"
    } else {
      flexDir = reverse === true ? "column-reverse" : "column"
    }

    const gapVal = GAP_MAP[gap] || GAP_MAP.md
    const justifyVal = JUSTIFY_MAP[justify] || "flex-start"

    this.style.setProperty("--mj-stack-direction", flexDir)
    this.style.setProperty("--mj-stack-gap", gapVal)
    this.style.setProperty("--mj-stack-align", align)
    this.style.setProperty("--mj-stack-justify", justifyVal)
    this.style.setProperty("--mj-stack-wrap", wrap === true ? "wrap" : "nowrap")
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
