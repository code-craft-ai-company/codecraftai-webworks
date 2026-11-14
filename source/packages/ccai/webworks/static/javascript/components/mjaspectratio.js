/*
 * mjaspectratio.js
 *
 * <mj-aspect-ratio> -- constrains slotted content to a fixed aspect ratio
 * regardless of container width. Eliminates layout shift for images/videos.
 *
 * Every slotted child is stretched over the ratio box -- an image, a video,
 * an iframe, a canvas or a plain container alike. `fit` / `position` apply
 * to replaced media only (they have no meaning for other elements).
 */

import { MjElement } from "../core/mjelement.js";

const DEFAULT_RATIO = "16/9";

/* The ratio a non-positive value is clamped to. */
const SQUARE_RATIO = "1/1";

const STYLES = `
/*
 * The properties written by \`ratio\`, \`fit\` and \`position\` belong to one
 * box: an inline value written by the attribute or an author rule on the
 * element wins over this reset, but a nested box never inherits them.
 */
:host {
  --mj-ar-ratio: initial;
  --mj-ar-fit: initial;
  --mj-ar-position: initial;
}

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

::slotted(*) {
  box-sizing: border-box;
  inline-size: 100%;
  block-size: 100%;
}

::slotted(img),
::slotted(video),
::slotted(canvas),
::slotted(svg),
::slotted(iframe),
::slotted(embed),
::slotted(object) {
  display: block;
}

::slotted(iframe) {
  border: 0;
}

::slotted(img),
::slotted(video) {
  object-fit: var(--mj-ar-fit, cover);
  object-position: var(--mj-ar-position, center);
}
`;

export class MjAspectRatio extends MjElement {
  static tagName = "mj-aspect-ratio";
  static styles = STYLES;
  static watched = ["ratio", "fit", "position"];

  constructor() {
    super()

    /* The last value a warning was printed for, so each is reported once. */
    this._warnedRatio = null
  }

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

  _warnOnce(raw, message) {
    if (this._warnedRatio !== raw) {
      this._warnedRatio = raw
      console.warn(message)
    }
    return
  }

  /*
   * Turn the `ratio` attribute into a CSS aspect-ratio value. Accepted forms:
   * a single positive number ("1.5"), or width and height separated by "/",
   * ":" or "x" with optional spaces ("16/9", "16 / 9", "16:9", "16x9").
   * A zero width or height is clamped to 1/1; anything else that cannot be
   * read falls back to 16/9. Both cases warn once per value.
   */
  _resolveRatio(raw) {
    let resolved = DEFAULT_RATIO
    const text = raw !== null && raw !== undefined ? raw.trim() : ""

    if (text.length > 0) {
      const pair = /^(\d*\.?\d+)\s*[/:xX]\s*(\d*\.?\d+)$/.exec(text)
      const single = /^(\d*\.?\d+)$/.exec(text)

      if (pair !== null) {
        const width = parseFloat(pair[1])
        const height = parseFloat(pair[2])
        if (width > 0 && height > 0) {
          resolved = `${width}/${height}`
        } else {
          resolved = SQUARE_RATIO
          this._warnOnce(raw, `[mj-aspect-ratio] Ratio "${raw}" is not positive, using 1/1.`)
        }
      } else if (single !== null) {
        const value = parseFloat(single[1])
        if (value > 0) {
          resolved = String(value)
        } else {
          resolved = SQUARE_RATIO
          this._warnOnce(raw, `[mj-aspect-ratio] Ratio "${raw}" is not positive, using 1/1.`)
        }
      } else {
        this._warnOnce(raw, `[mj-aspect-ratio] Unknown ratio "${raw}", falling back to 16/9.`)
      }
    }

    return resolved
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
    const ratio = this.getAttribute("ratio")
    const fit = this.getAttribute("fit")
    const position = this.getAttribute("position")

    this._setCustomProperty("--mj-ar-ratio", ratio !== null ? this._resolveRatio(ratio) : null)
    this._setCustomProperty("--mj-ar-fit", fit !== null && fit.length > 0 ? fit : null)
    this._setCustomProperty("--mj-ar-position", position !== null && position.length > 0 ? position : null)
    return
  }

  get resolvedRatio() {
    const resolved = this._resolveRatio(this.getAttribute("ratio"))
    return resolved
  }
}
