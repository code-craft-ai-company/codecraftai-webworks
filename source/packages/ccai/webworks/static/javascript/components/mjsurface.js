/*
 * mjsurface.js
 *
 * <mj-surface> -- a generic content wrapper providing elevation, background,
 * padding, and radius treatment. Consolidates Panel, Section, and Container
 * synonyms into one component configured by attributes.
 *
 * The host is a flex container whose only item, the painted surface, grows
 * to fill it. A surface with an explicit height, or one stretched by a grid,
 * flex or dock parent, is therefore painted over its whole box.
 *
 * `max-width` constrains and centers the painted surface. Together with
 * `full-bleed` the background runs edge to edge and only the CONTENT is
 * constrained and centered.
 *
 * A custom property is written on the host only for an attribute that is
 * present, so stylesheet rules such as
 * `mj-surface { --mj-surface-padding: 2rem }` apply whenever the matching
 * attribute is absent. The properties written by attributes belong to one
 * surface: the host resets them, so a nested surface never inherits the
 * padding, radius, elevation or max-width of the surface around it. The
 * colour properties (`--mj-surface-bg`, `--mj-surface-border`) are not
 * written by attributes and still inherit like theme tokens.
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
  display: flex;
  flex-direction: column;
}

/*
 * Per-element properties: an inline value written by an attribute or an
 * author rule on the element wins over this reset, an ancestor's value does
 * not reach the surface.
 */
:host {
  --mj-surface-padding: initial;
  --mj-surface-radius: initial;
  --mj-surface-shadow: initial;
  --mj-surface-border-width: initial;
  --mj-surface-max-width: initial;
}

.root {
  position: relative;
  flex: 1 1 auto;
  inline-size: 100%;
  max-inline-size: var(--mj-surface-max-width, none);
  margin-inline: auto;
  background: var(--mj-surface-bg, var(--mj-surface));
  padding: var(--mj-surface-padding, var(--mj-space-4));
  border-radius: var(--mj-surface-radius, var(--mj-radius-md));
  box-shadow: var(--mj-surface-shadow, none);
  border: var(--mj-surface-border-width, 0) solid var(--mj-surface-border, var(--mj-border));
  box-sizing: border-box;
}

:host([full-bleed]) .root {
  padding: 0;
  border-radius: 0;
}

/*
 * Full-bleed container: the surface spans the whole width and the inline
 * padding takes up whatever is wider than max-width, centering the content.
 */
:host([full-bleed][max-width]) .root {
  max-inline-size: none;
  padding-inline: max(0px, (100% - var(--mj-surface-max-width, 100%)) / 2);
}
`;

export class MjSurface extends MjElement {
  static tagName = "mj-surface";
  static styles = STYLES;
  static watched = ["elevation", "padding", "radius", "role-hint", "max-width", "full-bleed"];

  constructor() {
    super()
    this._root = null
  }

  render() {
    const tag = this._rootTagName()
    const markup = `<${tag} class="root" part="root"><slot></slot></${tag}>`
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

    if (name === "role-hint") {
      this._rebuildRoot()
    } else {
      this._syncStyles()
    }
    return
  }

  /* `section` for role-hint="section", otherwise a plain `div`. */
  _rootTagName() {
    const roleHint = this.getAttribute("role-hint") || "generic"
    const tag = roleHint === "section" ? "section" : "div"
    return tag
  }

  /*
   * Swap the root element for one of the tag `role-hint` asks for, moving
   * the existing children (the slot) across. Does nothing when the tag is
   * already right, so a replayed attribute change is harmless.
   */
  _rebuildRoot() {
    const tag = this._rootTagName()

    if (this._root.localName !== tag) {
      const newRoot = document.createElement(tag)
      newRoot.className = "root"
      newRoot.setAttribute("part", "root")

      while (this._root.firstChild !== null) {
        newRoot.appendChild(this._root.firstChild)
      }

      if (this._root.parentNode !== null) {
        this._root.parentNode.replaceChild(newRoot, this._root)
      }
      this._root = newRoot
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

    const elevation = this.getAttribute("elevation")
    const padding = this.getAttribute("padding")
    const radius = this.getAttribute("radius")
    const maxWidth = this.getAttribute("max-width")

    let shadow = null
    let borderWidth = null

    if (elevation !== null) {
      shadow = "none"
      borderWidth = "0"
      if (elevation === "outlined") {
        borderWidth = "1px"
      } else if (elevation === "raised") {
        shadow = "var(--mj-elevation-2)"
      } else if (elevation === "overlay") {
        shadow = "var(--mj-elevation-3)"
      }
    }

    this._setCustomProperty("--mj-surface-padding", padding !== null ? (PADDING_MAP[padding] || PADDING_MAP.md) : null)
    this._setCustomProperty("--mj-surface-radius", radius !== null ? (RADIUS_MAP[radius] || RADIUS_MAP.md) : null)
    this._setCustomProperty("--mj-surface-shadow", shadow)
    this._setCustomProperty("--mj-surface-border-width", borderWidth)
    this._setCustomProperty("--mj-surface-max-width", maxWidth !== null && maxWidth.length > 0 ? maxWidth : null)
    return
  }

  get contentElement() {
    return this._root || null
  }
}
