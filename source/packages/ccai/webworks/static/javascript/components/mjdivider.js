/*
 * mjdivider.js
 *
 * <mj-divider> -- a visual/semantic line separating adjacent content regions.
 * Supports horizontal/vertical orientation, optional label, and line variants.
 */

import { MjElement } from "../core/mjelement.js";

const SPACING_MAP = {
  none: "0",
  xs: "var(--mj-space-1)",
  sm: "var(--mj-space-2)",
  md: "var(--mj-space-4)",
  lg: "var(--mj-space-5)"
};

const THICKNESS_MAP = {
  thin: "1px",
  medium: "2px",
  thick: "4px"
};

const STYLES = `
:host {
  display: block;
}
:host([orientation="vertical"]) {
  display: inline-block;
  block-size: 100%;
  align-self: stretch;
}

.root-hr {
  border: none;
  border-block-start: var(--mj-divider-thickness, 1px) var(--mj-divider-variant, solid) var(--mj-divider-color, var(--mj-border));
  margin-block: var(--mj-divider-spacing, var(--mj-space-4));
  width: 100%;
}

.root-div {
  display: flex;
  align-items: center;
  gap: var(--mj-divider-label-gap, var(--mj-space-3));
  margin-block: var(--mj-divider-spacing, var(--mj-space-4));
  color: var(--mj-divider-label-color, var(--mj-text-muted));
  font-size: var(--mj-font-size-sm);
}

.root-div.vertical {
  flex-direction: column;
  margin-block: 0;
  margin-inline: var(--mj-divider-spacing, var(--mj-space-4));
  block-size: 100%;
}

.line {
  flex: 1;
  display: block;
  border-block-start: var(--mj-divider-thickness, 1px) var(--mj-divider-variant, solid) var(--mj-divider-color, var(--mj-border));
}

.root-div.vertical .line {
  border-block-start: none;
  border-inline-start: var(--mj-divider-thickness, 1px) var(--mj-divider-variant, solid) var(--mj-divider-color, var(--mj-border));
  inline-size: 0;
  block-size: auto;
}

.root-vertical {
  border: none;
  border-inline-start: var(--mj-divider-thickness, 1px) var(--mj-divider-variant, solid) var(--mj-divider-color, var(--mj-border));
  margin-inline: var(--mj-divider-spacing, var(--mj-space-4));
  block-size: 100%;
  align-self: stretch;
}

.label {
  white-space: nowrap;
  background: var(--mj-divider-label-bg, var(--mj-surface));
  padding-inline: var(--mj-space-2);
}
`;

export class MjDivider extends MjElement {
  static tagName = "mj-divider";
  static styles = STYLES;
  static watched = ["orientation", "decorative", "label", "variant", "thickness", "spacing"];

  render() {
    const markup = this._buildMarkup()
    return markup
  }

  afterRender() {
    this._syncStyles()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this.shadowRoot !== null) {
      this.shadowRoot.innerHTML = this._buildMarkup()
      this._syncStyles()
    }
    return
  }

  _buildMarkup() {
    const orientation = this.getAttribute("orientation") || "horizontal"
    const decorative = this.hasAttribute("decorative")
    const label = this.getAttribute("label") || ""
    const hasLabel = label.length > 0

    if (orientation === "vertical") {
      const role = decorative === true ? "none" : "separator"
      const ariaHidden = decorative === true ? ' aria-hidden="true"' : ""
      const ariaOrientation = decorative === true ? "" : ' aria-orientation="vertical"'
      return `<div class="root-vertical" part="root" role="${role}"${ariaHidden}${ariaOrientation}></div>`
    }

    if (hasLabel === true) {
      const role = decorative === true ? "none" : "separator"
      const ariaHidden = decorative === true ? ' aria-hidden="true"' : ""
      const ariaLabel = decorative === false && label.length > 0 ? ` aria-label="${label}"` : ""
      return `
        <div class="root-div" part="root" role="${role}"${ariaHidden}${ariaLabel}>
          <span class="line" part="line-start"></span>
          <span class="label" part="label"><slot name="label">${label}</slot></span>
          <span class="line" part="line-end"></span>
        </div>
      `
    }

    if (decorative === true) {
      return `<hr class="root-hr" part="root" role="none" aria-hidden="true" />`
    }

    return `<hr class="root-hr" part="root" />`
  }

  _syncStyles() {
    const variant = this.getAttribute("variant") || "solid"
    const thickness = this.getAttribute("thickness") || "thin"
    const spacing = this.getAttribute("spacing") || "md"

    const thicknessVal = THICKNESS_MAP[thickness] || THICKNESS_MAP.thin
    const spacingVal = SPACING_MAP[spacing] || SPACING_MAP.md

    this.style.setProperty("--mj-divider-variant", variant)
    this.style.setProperty("--mj-divider-thickness", thicknessVal)
    this.style.setProperty("--mj-divider-spacing", spacingVal)
    return
  }

  get isDecorative() {
    return this.hasAttribute("decorative")
  }
}
