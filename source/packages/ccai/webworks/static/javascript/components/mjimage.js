/*
 * mjimage.js
 *
 * <mj-image> -- lazy-loaded, responsive image with aspect-ratio reservation,
 * IntersectionObserver-driven loading, srcset/sizes support, and optional
 * figure/caption variant.
 *
 * Synonyms covered: Thumbnail, Figure.
 */

import { MjElement } from "../core/mjelement.js";

const STYLES = `
:host {
  display: block;
}
:host([variant="thumbnail"]) {
  display: inline-block;
}

.container {
  position: relative;
  overflow: hidden;
  border-radius: var(--mj-image-radius, var(--mj-radius-md));
  background: var(--mj-image-placeholder-color, var(--mj-bg-muted));
  line-height: 0;
}
:host([variant="thumbnail"]) .container {
  width: var(--mj-image-thumbnail-size, 3rem);
  height: var(--mj-image-thumbnail-size, 3rem);
}

.img {
  display: block;
  width: 100%;
  height: 100%;
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
  background: var(--mj-image-placeholder-color, var(--mj-bg-muted));
  transition: opacity var(--mj-image-transition-duration, var(--mj-motion-medium)) var(--mj-motion-ease);
}
.placeholder.hidden { opacity: 0; pointer-events: none; }

.placeholder-slot { display: contents; }

.overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.overlay ::slotted(*) { pointer-events: auto; }

figure {
  margin: 0;
  padding: 0;
}

figcaption {
  font-size: var(--mj-image-caption-font-size, var(--mj-font-size-sm));
  color: var(--mj-image-caption-color, var(--mj-text-muted));
  padding-top: var(--mj-space-2);
  line-height: var(--mj-line-height);
}

.error-icon {
  color: var(--mj-text-muted);
  font-size: var(--mj-font-size-lg);
}
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
  }

  render() {
    const markup = `
      <figure part="container" class="container">
        <div class="placeholder" part="placeholder" aria-hidden="true">
          <slot name="placeholder">
            <span class="placeholder-slot"></span>
          </slot>
        </div>
        <img class="img" part="img" decoding="async" />
        <div class="overlay" part="overlay">
          <slot name="overlay"></slot>
        </div>
        <figcaption class="caption" part="caption" hidden>
          <slot name="caption"></slot>
        </figcaption>
      </figure>
    `
    return markup
  }

  afterRender() {
    this._img = this.$(".img")
    this._placeholder = this.$(".placeholder")
    this._container = this.$(".container")
    this._caption = this.$(".caption")

    this.listen(this._img, "load", this._onLoad.bind(this))
    this.listen(this._img, "error", this._onError.bind(this))

    this._applyStaticAttrs()
    this._scheduleLoad()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._img === null || this._img === undefined) {
      return
    }
    if (name === "src" || name === "srcset" || name === "sizes") {
      this._reset()
      this._scheduleLoad()
    } else {
      this._applyStaticAttrs()
    }
    return
  }

  _applyStaticAttrs() {
    const alt = this.getAttribute("alt")
    if (alt === null) {
      console.warn("<mj-image>: `alt` attribute is missing. Set alt=\"\" for decorative images.")
      this._img.setAttribute("alt", "")
    } else {
      this._img.setAttribute("alt", alt)
    }

    const decoding = this.getAttribute("decoding") || "async"
    this._img.setAttribute("decoding", decoding)

    const crossorigin = this.getAttribute("crossorigin")
    if (crossorigin !== null) {
      this._img.setAttribute("crossorigin", crossorigin)
    }

    const fit = this.getAttribute("fit") || "cover"
    this._container.style.setProperty("--_fit", fit)

    const ar = this.getAttribute("aspect-ratio")
    const w = this.getAttribute("width")
    const h = this.getAttribute("height")
    if (ar !== null && ar.length > 0) {
      this._container.style.aspectRatio = ar
    } else if (w !== null && h !== null) {
      this._container.style.aspectRatio = `${w} / ${h}`
    }

    if (w !== null) { this._img.setAttribute("width", w) }
    if (h !== null) { this._img.setAttribute("height", h) }

    const caption = this.getAttribute("caption")
    if (caption !== null && caption.length > 0) {
      this._caption.textContent = caption
      this._caption.removeAttribute("hidden")
    }

    const placeholderColor = this.getAttribute("placeholder-color")
    if (placeholderColor !== null && placeholderColor.length > 0) {
      this._container.style.background = placeholderColor
      this._placeholder.style.background = placeholderColor
    }

    this._container.setAttribute("aria-busy", "true")
    return
  }

  _reset() {
    this._img.removeAttribute("src")
    this._img.removeAttribute("srcset")
    this._img.classList.remove("loaded")
    this._placeholder.classList.remove("hidden")
    this._container.setAttribute("aria-busy", "true")

    if (this._observer !== null) {
      this._observer.disconnect()
      this._observer = null
    }
    return
  }

  _scheduleLoad() {
    const src = this.getAttribute("src") || ""
    if (src.length === 0) {
      return
    }

    const strategy = this.getAttribute("loading") || "lazy"
    if (strategy === "eager") {
      this._applySrc()
      return
    }

    this._observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0]
        if (entry.isIntersecting === true) {
          this.emit("mj-image-visible", { ratio: entry.intersectionRatio })
          this._applySrc()
          this._observer.disconnect()
          this._observer = null
        }
      },
      { rootMargin: "200px" }
    )
    this._observer.observe(this)
    return
  }

  _applySrc() {
    const src = this.getAttribute("src") || ""
    const srcset = this.getAttribute("srcset") || ""
    const sizes = this.getAttribute("sizes") || ""

    if (src.length > 0) { this._img.setAttribute("src", src) }
    if (srcset.length > 0) { this._img.setAttribute("srcset", srcset) }
    if (sizes.length > 0) { this._img.setAttribute("sizes", sizes) }
    return
  }

  _onLoad() {
    this._img.classList.add("loaded")
    this._placeholder.classList.add("hidden")
    this._container.removeAttribute("aria-busy")

    this.emit("mj-image-load", {
      src: this._img.currentSrc || this._img.src,
      naturalWidth: this._img.naturalWidth,
      naturalHeight: this._img.naturalHeight
    })
    return
  }

  _onError() {
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
}
