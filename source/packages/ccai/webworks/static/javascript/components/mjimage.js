/*
 * mjimage.js
 *
 * <mj-image> -- lazy-loaded, responsive image with aspect-ratio reservation,
 * IntersectionObserver-driven loading, srcset/sizes support, and optional
 * figure/caption variant.
 *
 * Structure: an outer <figure> holds the ratio box (`part="container"`) and,
 * as a sibling below it, the <figcaption>. The ratio box clips the image, the
 * placeholder, the error state and the overlay; the caption is never clipped.
 *
 * Synonyms covered: Thumbnail, Figure.
 */

import { MjElement } from "../core/mjelement.js";
import { t } from "../core/intl.js";

/* Key of the text shown in the error state when the image has no alternative text. */
const DEFAULT_ERROR_LABEL_KEY = "mj.image.loadError";

const STYLES = `
:host {
  display: block;
}
:host([variant="thumbnail"]) {
  display: inline-block;
}

figure {
  margin: 0;
  padding: 0;
}

.container {
  position: relative;
  overflow: hidden;
  border-radius: var(--mj-image-radius, var(--mj-radius-md));
  background: var(--_placeholder, var(--mj-image-placeholder-color, var(--mj-bg-muted)));
  line-height: 0;
}
:host([variant="thumbnail"]) .container {
  inline-size: var(--mj-image-thumbnail-size, 3rem);
  block-size: var(--mj-image-thumbnail-size, 3rem);
}

.img {
  display: block;
  inline-size: 100%;
  block-size: 100%;
  object-fit: var(--_fit, cover);
  opacity: 0;
  transition: opacity var(--mj-image-transition-duration, var(--mj-motion-medium)) var(--mj-motion-ease);
}
.img.loaded { opacity: 1; }

.placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--_placeholder, var(--mj-image-placeholder-color, var(--mj-bg-muted)));
  transition: opacity var(--mj-image-transition-duration, var(--mj-motion-medium)) var(--mj-motion-ease);
}
.placeholder.hidden { opacity: 0; pointer-events: none; }

.error {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--mj-space-1);
  padding: var(--mj-space-2);
  box-sizing: border-box;
  background: var(--_placeholder, var(--mj-image-placeholder-color, var(--mj-bg-muted)));
  color: var(--mj-text-muted);
  font-size: var(--mj-font-size-sm);
  line-height: var(--mj-line-height, 1.4);
  text-align: center;
  overflow: hidden;
}
.error[hidden] { display: none; }

.error-icon {
  inline-size: 1.5rem;
  block-size: 1.5rem;
  flex-shrink: 0;
}

/* A thumbnail has no room for the label; it stays available to assistive technology. */
:host([variant="thumbnail"]) .error-text {
  position: absolute;
  inline-size: 1px;
  block-size: 1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
}

.overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.overlay ::slotted(*) { pointer-events: auto; }

figcaption {
  font-size: var(--mj-image-caption-font-size, var(--mj-font-size-sm));
  color: var(--mj-image-caption-color, var(--mj-text-muted));
  padding-block-start: var(--mj-space-2);
  line-height: var(--mj-line-height, 1.4);
}
figcaption[hidden] { display: none; }
.caption-text[hidden] { display: none; }
`;

export class MjImage extends MjElement {
  static tagName = "mj-image";
  static styles = STYLES;
  static watched = ["src", "srcset", "sizes", "alt", "width", "height",
    "aspect-ratio", "loading", "fit", "variant", "caption",
    "placeholder-color", "crossorigin", "decoding"];

  constructor() {
    super()
    this._observer = null
    this._img = null
    this._placeholder = null
    this._container = null
    this._caption = null
    this._captionText = null
    this._captionSlot = null
    this._errorEl = null
    this._errorText = null

    /* True once src/srcset have been handed to the inner <img>. */
    this._srcApplied = false

    /* True while the inner <img> is in the failed state. */
    this._failed = false

    /* The missing-alt warning is logged once per element. */
    this._warnedAlt = false
  }

  render() {
    const markup = `
      <figure part="figure" class="figure">
        <div class="container" part="container">
          <div class="placeholder" part="placeholder" aria-hidden="true">
            <slot name="placeholder"></slot>
          </div>
          <img class="img" part="img" decoding="async" />
          <div class="error" part="error" aria-hidden="true" hidden>
            <svg class="error-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"
              stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <rect x="3" y="4" width="18" height="16" rx="2"/>
              <path d="M3 16l5-5 4 4"/>
              <path d="M4 4l16 16"/>
            </svg>
            <span class="error-text"></span>
          </div>
          <div class="overlay" part="overlay">
            <slot name="overlay"></slot>
          </div>
        </div>
        <figcaption class="caption" part="caption" hidden><span class="caption-text"></span><slot name="caption"></slot></figcaption>
      </figure>
    `
    return markup
  }

  afterRender() {
    this._img = this.$(".img")
    this._placeholder = this.$(".placeholder")
    this._container = this.$(".container")
    this._caption = this.$(".caption")
    this._captionText = this.$(".caption-text")
    this._captionSlot = this.$("slot[name='caption']")
    this._errorEl = this.$(".error")
    this._errorText = this.$(".error-text")

    this._srcApplied = false
    this._failed = false

    this.listen(this._img, "load", this._onLoad.bind(this))
    this.listen(this._img, "error", this._onError.bind(this))
    this.listen(this._captionSlot, "slotchange", () => { this._syncCaption() })

    this._applyStaticAttrs()
    this._scheduleLoad()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._img === null || this._img === undefined) {
      return
    }

    if (name === "src" || name === "srcset" || name === "sizes") {
      if (oldValue !== newValue) {
        this._reset()
        this._scheduleLoad()
      }
    } else if (name === "loading") {
      /*
       * A lazy image that is still waiting for its observer starts loading
       * as soon as it is switched to eager. An image that already has its
       * source is left alone.
       */
      if (this._srcApplied === false) {
        this._reset()
        this._scheduleLoad()
      }
    } else {
      this._applyStaticAttrs()
    }
    return
  }

  /*
   * Mirror the presentational attributes onto the shadow DOM. Every branch
   * has a matching removal so an attribute that is taken away stops applying.
   * The loading state (aria-busy) is not touched here.
   */
  _applyStaticAttrs() {
    const alt = this.getAttribute("alt")
    if (alt === null) {
      if (this._warnedAlt === false) {
        console.warn("<mj-image>: `alt` attribute is missing. Set alt=\"\" for decorative images.")
        this._warnedAlt = true
      }
      this._img.setAttribute("alt", "")
    } else {
      this._img.setAttribute("alt", alt)
    }

    const decoding = this.getAttribute("decoding") || "async"
    this._img.setAttribute("decoding", decoding)

    const crossorigin = this.getAttribute("crossorigin")
    if (crossorigin !== null) {
      this._img.setAttribute("crossorigin", crossorigin)
    } else {
      this._img.removeAttribute("crossorigin")
    }

    const fit = this.getAttribute("fit") || "cover"
    this._container.style.setProperty("--_fit", fit)

    const ratio = this.getAttribute("aspect-ratio")
    const width = this.getAttribute("width")
    const height = this.getAttribute("height")
    const widthNumber = parseFloat(width)
    const heightNumber = parseFloat(height)
    if (ratio !== null && ratio.length > 0) {
      this._container.style.aspectRatio = ratio
    } else if (widthNumber > 0 && heightNumber > 0) {
      this._container.style.aspectRatio = `${widthNumber} / ${heightNumber}`
    } else {
      this._container.style.removeProperty("aspect-ratio")
    }

    if (width !== null) {
      this._img.setAttribute("width", width)
    } else {
      this._img.removeAttribute("width")
    }
    if (height !== null) {
      this._img.setAttribute("height", height)
    } else {
      this._img.removeAttribute("height")
    }

    const placeholderColor = this.getAttribute("placeholder-color")
    if (placeholderColor !== null && placeholderColor.length > 0) {
      this._container.style.setProperty("--_placeholder", placeholderColor)
    } else {
      this._container.style.removeProperty("--_placeholder")
    }

    this._syncCaption()
    this._syncErrorLabel()
    return
  }

  /*
   * The figcaption shows when the `caption` attribute has text or the
   * `caption` slot has content. Slotted content replaces the attribute text.
   */
  _syncCaption() {
    const caption = this.getAttribute("caption") || ""
    const slotted = this._captionSlot.assignedNodes({ flatten: true })
    const hasSlotted = slotted.length > 0

    this._captionText.textContent = caption
    this._captionText.hidden = hasSlotted === true

    const visible = hasSlotted === true || caption.length > 0
    this._caption.hidden = visible === false
    return
  }

  /*
   * The error state shows the alternative text, so a failed image still tells
   * a sighted user what was meant to be there. The inner <img> keeps carrying
   * the alt for assistive technology (and a decorative image stays silent, as
   * a native one does), so the visible copy is `aria-hidden` in the markup.
   */
  _syncErrorLabel() {
    const alt = this.getAttribute("alt") || ""
    if (alt.length > 0) {
      this._errorText.textContent = alt
    } else {
      this._errorText.textContent = t(DEFAULT_ERROR_LABEL_KEY)
    }
    return
  }

  _reset() {
    this._img.removeAttribute("src")
    this._img.removeAttribute("srcset")
    this._img.removeAttribute("sizes")
    this._img.classList.remove("loaded")
    this._placeholder.classList.remove("hidden")
    this._errorEl.hidden = true
    this._container.removeAttribute("aria-busy")
    this._srcApplied = false
    this._failed = false

    if (this._observer !== null) {
      this._observer.disconnect()
      this._observer = null
    }
    return
  }

  _scheduleLoad() {
    const src = this.getAttribute("src") || ""
    const srcset = this.getAttribute("srcset") || ""
    if (src.length === 0 && srcset.length === 0) {
      return
    }

    /* A load is pending from here until the img reports load or error. */
    this._container.setAttribute("aria-busy", "true")

    const strategy = this.getAttribute("loading") || "lazy"
    if (strategy === "eager") {
      this._applySrc()
      return
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0]
        if (entry.isIntersecting === true) {
          this.emit("mj-image-visible", { ratio: entry.intersectionRatio })
          observer.disconnect()
          if (this._observer === observer) {
            this._observer = null
          }
          this._applySrc()
        }
      },
      { rootMargin: "200px" }
    )
    this._observer = observer
    observer.observe(this)
    return
  }

  _applySrc() {
    const src = this.getAttribute("src") || ""
    const srcset = this.getAttribute("srcset") || ""
    const sizes = this.getAttribute("sizes") || ""

    this._srcApplied = true

    /* sizes must be in place before srcset so the first candidate is right. */
    if (sizes.length > 0) { this._img.setAttribute("sizes", sizes) }
    if (srcset.length > 0) { this._img.setAttribute("srcset", srcset) }
    if (src.length > 0) { this._img.setAttribute("src", src) }
    return
  }

  _onLoad() {
    this._failed = false
    this._img.classList.add("loaded")
    this._placeholder.classList.add("hidden")
    this._errorEl.hidden = true
    this._container.removeAttribute("aria-busy")

    this.emit("mj-image-load", {
      src: this._img.currentSrc || this._img.src,
      naturalWidth: this._img.naturalWidth,
      naturalHeight: this._img.naturalHeight
    })
    return
  }

  _onError() {
    this._failed = true
    this._img.classList.remove("loaded")
    this._placeholder.classList.add("hidden")
    this._syncErrorLabel()
    this._errorEl.hidden = false
    this._container.removeAttribute("aria-busy")
    this.emit("mj-image-error", { src: this.getAttribute("src") || "" })
    return
  }

  onDisconnected() {
    if (this._observer !== null) {
      this._observer.disconnect()
      this._observer = null
    }
    return
  }

  /* ----- scriptable API ----- */

  get complete() {
    const value = this._img !== null && this._img.complete === true
    return value
  }

  get naturalWidth() {
    const value = this._img !== null ? this._img.naturalWidth : 0
    return value
  }

  get naturalHeight() {
    const value = this._img !== null ? this._img.naturalHeight : 0
    return value
  }

  get currentSrc() {
    const value = this._img !== null ? this._img.currentSrc : ""
    return value
  }

  /* True when the last load attempt failed. */
  get failed() {
    return this._failed
  }
}
