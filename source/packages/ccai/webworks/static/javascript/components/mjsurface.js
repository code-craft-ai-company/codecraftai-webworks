/*
 * mjsurface.js
 *
 * <mj-surface> -- a generic content wrapper providing elevation, background,
 * padding, and radius treatment. Consolidates Panel, Section, and Container
 * synonyms into one component configured by attributes.
 */

import { MjElement } from "../core/mjelement.js";

const PADDING_MAP = {
  none: "0",
  sm: "var(--mj-space-2)",
  md: "var(--mj-space-4)",
  lg: "var(--mj-space-5)",
  xl: "var(--mj-space-6)"
};

const RADIUS_MAP = {
  none: "0",
  sm: "var(--mj-radius-sm)",
  md: "var(--mj-radius-md)",
  lg: "var(--mj-radius-lg)",
  full: "var(--mj-radius-pill)"
};

const STYLES = `
:host {
  display: block;
}

.root {
  background: var(--mj-surface-bg, var(--mj-surface));
  padding: var(--mj-surface-padding, var(--mj-space-4));
  border-radius: var(--mj-surface-radius, var(--mj-radius-md));
  box-shadow: var(--mj-surface-shadow, none);
  border: var(--mj-surface-border-width, 0) solid var(--mj-surface-border, var(--mj-border));
  max-width: var(--mj-surface-max-width, none);
  margin-inline: var(--mj-surface-margin-inline, 0);
  box-sizing: border-box;
}
`;

export class MjSurface extends MjElement {
  static tagName = "mj-surface";
  static styles = STYLES;
  static watched = ["elevation", "padding", "radius", "role-hint", "max-width", "full-bleed"];

  render() {
    const roleHint = this.getAttribute("role-hint") || "generic";
    const tag = roleHint === "section" ? "section" : "div";
    const markup = `<${tag} class="root" part="root"><slot></slot></${tag}>`
    return markup
  }

  afterRender() {
    this._root = this.$(".root")
    this._syncStyles()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._root !== undefined) {
      if (name === "role-hint") {
        this._rebuildRoot()
      } else {
        this._syncStyles()
      }
    }
    return
  }

  _rebuildRoot() {
    const roleHint = this.getAttribute("role-hint") || "generic"
    const tag = roleHint === "section" ? "section" : "div"
    const slot = this._root !== null ? this._root.innerHTML : "<slot></slot>"
    const newRoot = document.createElement(tag)
    newRoot.className = "root"
    newRoot.setAttribute("part", "root")
    newRoot.innerHTML = slot
    if (this._root !== null && this._root.parentNode !== null) {
      this._root.parentNode.replaceChild(newRoot, this._root)
    }
    this._root = newRoot
    this._syncStyles()
    return
  }

  _syncStyles() {
    if (this._root === null || this._root === undefined) {
      return
    }

    const fullBleed = this.hasAttribute("full-bleed")
    const elevation = this.getAttribute("elevation") || "flat"
    const padding = this.getAttribute("padding") || "md"
    const radius = this.getAttribute("radius") || "md"
    const maxWidth = this.getAttribute("max-width") || ""

    const paddingVal = fullBleed === true ? "0" : (PADDING_MAP[padding] || PADDING_MAP.md)
    const radiusVal = fullBleed === true ? "0" : (RADIUS_MAP[radius] || RADIUS_MAP.md)

    let shadow = "none"
    let borderWidth = "0"

    if (elevation === "outlined") {
      borderWidth = "1px"
    } else if (elevation === "raised") {
      shadow = "var(--mj-elevation-2)"
    } else if (elevation === "overlay") {
      shadow = "var(--mj-elevation-3)"
    }

    this.style.setProperty("--mj-surface-padding", paddingVal)
    this.style.setProperty("--mj-surface-radius", radiusVal)
    this.style.setProperty("--mj-surface-shadow", shadow)
    this.style.setProperty("--mj-surface-border-width", borderWidth)

    if (maxWidth !== null && maxWidth.length > 0) {
      this.style.setProperty("--mj-surface-max-width", maxWidth)
      this.style.setProperty("--mj-surface-margin-inline", "auto")
    } else {
      this.style.setProperty("--mj-surface-max-width", "none")
      this.style.setProperty("--mj-surface-margin-inline", "0")
    }
    return
  }

  get contentElement() {
    return this._root || null
  }
}
