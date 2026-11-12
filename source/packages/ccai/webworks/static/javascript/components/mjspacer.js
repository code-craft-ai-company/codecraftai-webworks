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

  /*
   * A custom property is written on the host only while `size` is present;
   * without it the stylesheet defaults (a flexible spacer) apply and an
   * author rule such as `mj-spacer { --mj-spacer-flex: 2 1 0 }` is honored.
   */
  _syncStyles() {
    const sizeAttr = this.getAttribute("size") || ""
    const axis = this.getAttribute("axis") || "both"

    let flex = null
    let inlineSize = null
    let blockSize = null

    if (sizeAttr.length > 0) {
      const sizeVal = SIZE_MAP[sizeAttr] || sizeAttr
      flex = "0 0 auto"

      if (axis === "horizontal") {
        inlineSize = sizeVal
      } else if (axis === "vertical") {
        blockSize = sizeVal
      } else {
        inlineSize = sizeVal
        blockSize = sizeVal
      }
    }

    this._setCustomProperty("--mj-spacer-flex", flex)
    this._setCustomProperty("--mj-spacer-inline-size", inlineSize)
    this._setCustomProperty("--mj-spacer-block-size", blockSize)
    return
  }

  get flex() {
    const sizeAttr = this.getAttribute("size") || ""
    return sizeAttr.length === 0
  }
}
