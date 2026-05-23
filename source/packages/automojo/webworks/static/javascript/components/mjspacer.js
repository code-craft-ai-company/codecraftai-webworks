/*
 * mjspacer.js
 *
 * <mj-spacer> -- a fixed or flexible blank space between sibling elements.
 * Inside flex/grid containers it either consumes a fixed token size or grows
 * to fill available space.
 */

import { MjElement } from "../core/mjelement.js";

const SIZE_MAP = {
  xs: "var(--mj-space-1)",
  sm: "var(--mj-space-2)",
  md: "var(--mj-space-4)",
  lg: "var(--mj-space-5)",
  xl: "var(--mj-space-6)",
  "2xl": "var(--mj-space-7)"
};

const STYLES = `
:host {
  display: block;
  flex: var(--mj-spacer-flex, 1 1 0);
  inline-size: var(--mj-spacer-inline-size, auto);
  block-size: var(--mj-spacer-block-size, auto);
  min-inline-size: 0;
  min-block-size: 0;
}
`;

export class MjSpacer extends MjElement {
  static tagName = "mj-spacer";
  static styles = STYLES;
  static watched = ["size", "axis"];

  render() {
    const markup = `<span part="root" aria-hidden="true" role="none"></span>`
    return markup
  }

  afterRender() {
    this._syncStyles()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    this._syncStyles()
    return
  }

  _syncStyles() {
    const sizeAttr = this.getAttribute("size") || ""
    const axis = this.getAttribute("axis") || "both"

    if (sizeAttr.length === 0) {
      this.style.setProperty("--mj-spacer-flex", "1 1 0")
      this.style.setProperty("--mj-spacer-inline-size", "auto")
      this.style.setProperty("--mj-spacer-block-size", "auto")
      return
    }

    const sizeVal = SIZE_MAP[sizeAttr] || sizeAttr
    this.style.setProperty("--mj-spacer-flex", "0 0 auto")

    if (axis === "horizontal") {
      this.style.setProperty("--mj-spacer-inline-size", sizeVal)
      this.style.setProperty("--mj-spacer-block-size", "auto")
    } else if (axis === "vertical") {
      this.style.setProperty("--mj-spacer-inline-size", "auto")
      this.style.setProperty("--mj-spacer-block-size", sizeVal)
    } else {
      this.style.setProperty("--mj-spacer-inline-size", sizeVal)
      this.style.setProperty("--mj-spacer-block-size", sizeVal)
    }
    return
  }

  get flex() {
    const sizeAttr = this.getAttribute("size") || ""
    return sizeAttr.length === 0
  }
}
