/*
 * mjmediaobject.js
 *
 * <mj-media-object> -- places a fixed-size media element beside a variable-width
 * text block. The foundational pattern for comment rows, list items with avatars,
 * notification rows, and settings rows.
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
:host {
  display: block;
}

.root {
  display: flex;
  flex-direction: var(--mj-media-object-direction, row);
  align-items: var(--mj-media-object-align, flex-start);
  gap: var(--mj-media-object-gap, var(--mj-space-4));
}

.media {
  flex-shrink: 0;
  inline-size: var(--mj-media-object-media-size, 3rem);
}

.content {
  flex: 1 1 0;
  min-inline-size: 0;
}

:host([media-position="end"]) .media {
  order: 1;
}
`;

export class MjMediaObject extends MjElement {
  static tagName = "mj-media-object";
  static styles = STYLES;
  static watched = ["media-position", "gap", "align", "media-size"];

  render() {
    const markup = `
      <div class="root" part="root">
        <div class="media" part="media"><slot name="media"></slot></div>
        <div class="content" part="content"><slot></slot></div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._root = this.$(".root")
    this._mediaEl = this.$(".media")
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

    const gap = this.getAttribute("gap") || "md"
    const align = this.getAttribute("align") || "start"
    const mediaSize = this.getAttribute("media-size") || ""

    const gapVal = GAP_MAP[gap] || GAP_MAP.md
    const alignVal = align === "start" ? "flex-start" : align === "end" ? "flex-end" : align

    this.style.setProperty("--mj-media-object-gap", gapVal)
    this.style.setProperty("--mj-media-object-align", alignVal)

    if (mediaSize.length > 0) {
      this.style.setProperty("--mj-media-object-media-size", mediaSize)
    } else {
      this.style.setProperty("--mj-media-object-media-size", "3rem")
    }
    return
  }

  get contentElement() {
    return this.$(".content") || null
  }
}
