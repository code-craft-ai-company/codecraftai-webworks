/*
 * mjdivider.js
 *
 * <mj-divider> -- a visual/semantic line separating adjacent content regions.
 * Supports horizontal/vertical orientation, optional label, and line variants.
 *
 * The label comes from the `label` attribute or from content placed in
 * slot="label" (the slot wins). With a label the line is drawn on both sides
 * of it, in either orientation. A vertical divider fills the height of a
 * stretching flex or grid row; elsewhere it is at least one line tall.
 *
 * The markup is built once; attribute changes only update it, so the label
 * text is never parsed as HTML.
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
  display: inline-flex;
  vertical-align: middle;
  align-self: stretch;
  min-block-size: 1em;
}

.root {
  display: flex;
  align-items: center;
  gap: var(--mj-divider-label-gap, var(--mj-space-3));
  margin-block: var(--mj-divider-spacing, var(--mj-space-4));
  color: var(--mj-divider-label-color, var(--mj-text-muted));
  font-size: var(--mj-font-size-sm);
}

.root.vertical {
  flex: 1 1 auto;
  flex-direction: column;
  margin-block: 0;
  margin-inline: var(--mj-divider-spacing, var(--mj-space-4));
  min-block-size: 1em;
}

.line {
  flex: 1 1 0;
  display: block;
  border-block-start: var(--mj-divider-thickness, 1px) var(--mj-divider-variant, solid) var(--mj-divider-color, var(--mj-border));
}

.root.vertical .line {
  border-block-start: none;
  border-inline-start: var(--mj-divider-thickness, 1px) var(--mj-divider-variant, solid) var(--mj-divider-color, var(--mj-border));
  inline-size: 0;
}

/* Without a label one line runs the full length. */
.root.unlabelled .label,
.root.unlabelled .line-end {
  display: none;
}

.root.unlabelled {
  gap: 0;
}

.label {
  white-space: nowrap;
  background: var(--mj-divider-label-bg, transparent);
  padding-inline: var(--mj-space-2);
}

.root.vertical .label {
  padding-inline: 0;
  padding-block: var(--mj-space-2);
}
`;

export class MjDivider extends MjElement {
  static tagName = "mj-divider";
  static styles = STYLES;
  static watched = ["orientation", "decorative", "label", "variant", "thickness", "spacing"];

  constructor() {
    super()
    this._root = null
    this._labelText = null
    this._labelSlot = null
  }

  render() {
    const markup = `
      <div class="root unlabelled" part="root">
        <span class="line line-start" part="line-start"></span>
        <span class="label" part="label"><slot name="label"><span class="label-text"></span></slot></span>
        <span class="line line-end" part="line-end"></span>
      </div>
    `
    return markup
  }

  afterRender() {
    this._root = this.$(".root")
    this._labelText = this.$(".label-text")
    this._labelSlot = this.$("slot[name='label']")
    this.listen(this._labelSlot, "slotchange", this._syncSemantics.bind(this))
    this._syncSemantics()
    this._syncStyles()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._root === undefined || this._root === null) {
      return
    }

    if (name === "variant" || name === "thickness" || name === "spacing") {
      this._syncStyles()
    } else {
      this._syncSemantics()
    }
    return
  }

  /*
   * The label as plain text: slotted label content first, else the
   * attribute. Not flattened: a flattened unassigned slot would report its
   * fallback content (the attribute text) as slotted content.
   */
  _labelString() {
    const slotted = this._labelSlot.assignedNodes()
    let text = ""

    if (slotted.length > 0) {
      const parts = []
      for (let index = 0; index < slotted.length; index = index + 1) {
        parts.push(slotted[index].textContent || "")
      }
      text = parts.join(" ")
    } else {
      text = this.getAttribute("label") || ""
    }

    const compact = text.replace(/\s+/g, " ").trim()
    return compact
  }

  /* Orientation, label and the separator role / name. */
  _syncSemantics() {
    const vertical = this.getAttribute("orientation") === "vertical"
    const decorative = this.hasAttribute("decorative")
    const hasSlottedLabel = this._labelSlot.assignedNodes().length > 0
    const attributeLabel = this.getAttribute("label") || ""
    const labelled = hasSlottedLabel === true || attributeLabel.length > 0

    this._labelText.textContent = attributeLabel
    this._root.classList.toggle("vertical", vertical)
    this._root.classList.toggle("unlabelled", labelled === false)

    if (decorative === true) {
      this._root.setAttribute("role", "none")
      this._root.setAttribute("aria-hidden", "true")
      this._root.removeAttribute("aria-orientation")
      this._root.removeAttribute("aria-label")
    } else {
      this._root.setAttribute("role", "separator")
      this._root.removeAttribute("aria-hidden")
      this._root.setAttribute("aria-orientation", vertical === true ? "vertical" : "horizontal")

      const name = labelled === true ? this._labelString() : ""
      if (name.length > 0) {
        this._root.setAttribute("aria-label", name)
      } else {
        this._root.removeAttribute("aria-label")
      }
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

  _syncStyles() {
    const variant = this.getAttribute("variant")
    const thickness = this.getAttribute("thickness")
    const spacing = this.getAttribute("spacing")

    const variants = ["solid", "dashed", "dotted", "double"]
    const variantValue = variant !== null && variants.indexOf(variant) >= 0 ? variant : null
    const thicknessValue = thickness !== null ? (THICKNESS_MAP[thickness] || THICKNESS_MAP.thin) : null
    const spacingValue = spacing !== null ? (SPACING_MAP[spacing] || SPACING_MAP.md) : null

    this._setCustomProperty("--mj-divider-variant", variantValue)
    this._setCustomProperty("--mj-divider-thickness", thicknessValue)
    this._setCustomProperty("--mj-divider-spacing", spacingValue)
    return
  }

  get isDecorative() {
    return this.hasAttribute("decorative")
  }
}
