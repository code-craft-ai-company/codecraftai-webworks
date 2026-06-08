/*
 * mjaspectratio.js
 *
 * <mj-aspect-ratio> -- constrains slotted content to a fixed aspect ratio
 * regardless of container width. Eliminates layout shift for images/videos.
 */

import { MjElement } from "../core/mjelement.js";

const RATIO_ALIASES = {
  "16x9": "16/9",
  "4x3": "4/3",
  "1x1": "1/1",
  "3x2": "3/2",
  "9x16": "9/16"
};

const STYLES = `
:host {
  display: block;
  aspect-ratio: var(--mj-ar-ratio, 16/9);
  position: relative;
  overflow: hidden;
  background: var(--mj-ar-bg, var(--mj-bg-muted));
}

.inner {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

::slotted(img),
::slotted(video) {
  width: 100%;
  height: 100%;
  object-fit: var(--mj-ar-fit, cover);
  object-position: var(--mj-ar-position, center);
}
`;

export class MjAspectRatio extends MjElement {
  static tagName = "mj-aspect-ratio";
  static styles = STYLES;
  static watched = ["ratio", "fit", "position"];

  render() {
    const markup = `
      <div class="inner" part="inner root">
        <slot></slot>
      </div>
    `
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

  _resolveRatio(raw) {
    if (raw === null || raw.length === 0) {
      return "16/9"
    }

    if (RATIO_ALIASES[raw] !== undefined) {
      return RATIO_ALIASES[raw]
    }

    if (/^\d+\/\d+$/.test(raw) === true || /^\d+(\.\d+)?$/.test(raw) === true) {
      return raw
    }

    console.warn(`[mj-aspect-ratio] Unknown ratio "${raw}", falling back to 16/9.`)
    return "16/9"
  }

  _syncStyles() {
    const ratio = this.getAttribute("ratio") || "16/9"
    const fit = this.getAttribute("fit") || "cover"
    const position = this.getAttribute("position") || "center"

    const resolved = this._resolveRatio(ratio)

    this.style.setProperty("--mj-ar-ratio", resolved)
    this.style.setProperty("--mj-ar-fit", fit)
    this.style.setProperty("--mj-ar-position", position)
    return
  }

  get resolvedRatio() {
    const ratio = this.getAttribute("ratio") || "16/9"
    const resolved = this._resolveRatio(ratio)
    return resolved
  }
}
