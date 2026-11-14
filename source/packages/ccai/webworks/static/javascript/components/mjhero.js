/*
 * mjhero.js
 *
 * <mj-hero> -- a prominent full-width introductory banner combining a
 * background image/color, heading, body, and optional action buttons.
 *
 * Background layers, bottom to top: the `bg-color` (default: the accent
 * color), the `bg-src` image or `bg-video` video, the contrast scrim (only
 * over an image or video), then the content. A background video is muted,
 * looped and inline; it autoplays unless the user prefers reduced motion,
 * and a pause / play button lets the user stop it.
 *
 * The heading comes from the `heading` attribute or the `heading` slot. With
 * neither, no heading element is exposed and the section is not labelled.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { html, safeUrl } from "../core/html.js";
import { t } from "../core/intl.js";

const DEFAULT_HEADING_LEVEL = 1;
const DEFAULT_OVERLAY_OPACITY = 0.4;

const STYLES = `
:host {
  display: block;
}

/*
 * The properties written by attributes belong to one hero: an inline value
 * written by the attribute or an author rule on the element wins over this
 * reset, but content slotted into the hero never inherits them.
 */
:host {
  --mj-hero-bg-color: initial;
  --mj-hero-overlay-opacity: initial;
  --mj-hero-min-height: initial;
  --mj-hero-justify: initial;
  --mj-hero-text-align: initial;
}

/*
 * \`align\` is also the legacy HTML presentational attribute (text-align on
 * any element). The content region sets its own text alignment from
 * \`align\`; everything else follows the parent.
 */
:host([align]) { text-align: inherit; }

.root {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: var(--mj-hero-justify, center);
  min-block-size: var(--mj-hero-min-height, 40vh);
  overflow: hidden;
  background: var(--mj-hero-bg-color, var(--mj-accent));
}

:host([full-height]) .root {
  min-block-size: 100dvh;
}

.background {
  position: absolute;
  inset: 0;
  background-size: cover;
  background-position: center;
  z-index: 0;
}

.background video {
  position: absolute;
  inset: 0;
  inline-size: 100%;
  block-size: 100%;
  object-fit: cover;
}

.overlay {
  position: absolute;
  inset: 0;
  background: var(--mj-hero-overlay-color, #000000);
  opacity: var(--mj-hero-overlay-opacity, 0.4);
  z-index: 1;
}

.content {
  position: relative;
  z-index: 2;
  inline-size: 100%;
  max-inline-size: var(--mj-hero-content-max-width, 72rem);
  margin-inline: auto;
  padding-block: var(--mj-hero-padding-block, var(--mj-space-8));
  padding-inline: var(--mj-space-5);
  text-align: var(--mj-hero-text-align, center);
  display: flex;
  flex-direction: column;
  gap: var(--mj-space-4);
}

/*
 * Default text colour: --mj-text-on-accent pairs with the default accent
 * background. Over the scrim of an image or video (black by default) the
 * text is light in both themes; in the dark theme --mj-text-on-accent is
 * dark and would sit on a darkened picture.
 */
.root {
  --mj-hero-text-color: var(--mj-text-on-accent);
}

.root[data-scrim] {
  --mj-hero-text-color: var(--mj-color-neutral-0);
}

.heading-el {
  margin: 0;
  font-size: clamp(var(--mj-font-size-xl), 5vw, var(--mj-font-size-2xl));
  font-weight: var(--mj-font-weight-bold);
  line-height: 1.2;
  color: var(--mj-hero-heading-color, var(--mj-hero-text-color, var(--mj-text-on-accent)));
}

.body-region {
  color: var(--mj-hero-body-color, var(--mj-hero-text-color, var(--mj-text-on-accent)));
}

.actions-region {
  display: flex;
  flex-wrap: wrap;
  gap: var(--mj-hero-actions-gap, var(--mj-space-3));
  justify-content: var(--mj-hero-justify, center);
}

.media-region {
  position: relative;
  z-index: 2;
}

.video-toggle {
  position: absolute;
  inset-block-end: var(--mj-space-3);
  inset-inline-end: var(--mj-space-3);
  z-index: 3;
  inline-size: var(--mj-target-min);
  block-size: var(--mj-target-min);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-circle);
  background: var(--mj-surface);
  color: var(--mj-text);
  cursor: pointer;
}

.video-toggle:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.video-toggle svg {
  inline-size: 1rem;
  block-size: 1rem;
  fill: currentColor;
}

.video-toggle .icon-play,
.video-toggle[data-playing="true"] .icon-pause {
  display: block;
}

.video-toggle .icon-pause,
.video-toggle[data-playing="true"] .icon-play {
  display: none;
}

:host([align="start"]) .content,
:host([align="start"]) .actions-region {
  align-items: flex-start;
  text-align: start;
}

:host([align="end"]) .content,
:host([align="end"]) .actions-region {
  align-items: flex-end;
  text-align: end;
}
`;

/* Quote a URL for use inside CSS url(""). */
function cssUrl(value) {
  const escaped = String(value).replace(/[\r\n\f]/g, "").replace(/["\\]/g, "\\$&")
  const text = `url("${escaped}")`
  return text
}

export class MjHero extends MjElement {
  static tagName = "mj-hero";
  static styles = STYLES;
  static watched = [
    "heading", "heading-level", "bg-src", "bg-video", "bg-color", "video-poster",
    "overlay-opacity", "align", "full-height", "min-height"
  ];

  constructor() {
    super()
    this._headingId = nextId("mj-hero-heading")
    this._videoEl = null
    this._root = null
    this._bg = null
    this._overlay = null
    this._headingEl = null
    this._headingText = null
    this._videoToggle = null

    /* The image source being loaded; errors of superseded sources are ignored. */
    this._pendingImageSrc = null
  }

  render() {
    const markup = html`
      <section class="root" part="root">
        <div class="background" part="background" aria-hidden="true"></div>
        <div class="overlay" part="overlay" aria-hidden="true" hidden></div>
        <div class="content" part="content">
          <h1 class="heading-el" part="heading" id="${this._headingId}">
            <slot name="heading"><span class="heading-text"></span></slot>
          </h1>
          <div class="body-region" part="body"><slot name="body"></slot></div>
          <div class="actions-region" part="actions"><slot name="actions"></slot></div>
          <div class="media-region" part="media"><slot name="media"></slot></div>
        </div>
        <button type="button" class="video-toggle" part="video-toggle" hidden>
          <svg class="icon-pause" aria-hidden="true" viewBox="0 0 16 16"><rect x="3" y="2" width="4" height="12"></rect><rect x="9" y="2" width="4" height="12"></rect></svg>
          <svg class="icon-play" aria-hidden="true" viewBox="0 0 16 16"><path d="M4 2 L14 8 L4 14 Z"></path></svg>
        </button>
      </section>
    `
    return markup
  }

  afterRender() {
    this._root = this.$(".root")
    this._bg = this.$(".background")
    this._overlay = this.$(".overlay")
    this._headingEl = this.$(".heading-el")
    this._headingText = this.$(".heading-text")
    this._videoToggle = this.$(".video-toggle")

    /* A re-render (after a real removal) starts with an empty background. */
    this._videoEl = null
    this._pendingImageSrc = null

    this.listen(this._videoToggle, "click", this._onVideoToggle.bind(this))

    /* slotchange bubbles to the shadow root; it survives a heading-level swap. */
    this.listen(this.shadowRoot, "slotchange", (event) => {
      if (event.target.getAttribute("name") === "heading") {
        this._syncHeadingPresence()
      }
    })

    this._rebuildHeading()
    this._syncBackground()
    this._syncStyles()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._root === undefined || this._root === null) {
      return
    }

    if (name === "bg-src" || name === "bg-video" || name === "bg-color" || name === "video-poster") {
      this._syncBackground()
    } else if (name === "heading" || name === "heading-level") {
      this._rebuildHeading()
    } else {
      this._syncStyles()
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

  /* ----- background ----- */

  _syncBackground() {
    if (this._bg === null || this._bg === undefined) {
      return
    }

    const bgVideo = safeUrl(this.getAttribute("bg-video") || "", "")
    const bgSrc = safeUrl(this.getAttribute("bg-src") || "", "")
    const bgColor = this.getAttribute("bg-color")

    this._setCustomProperty("--mj-hero-bg-color", bgColor !== null && bgColor.length > 0 ? bgColor : null)

    if (bgVideo.length > 0) {
      this._pendingImageSrc = null
      this._bg.style.backgroundImage = ""
      this._syncVideo(bgVideo)
    } else {
      this._removeVideo()
      if (bgSrc.length > 0) {
        this._showImage(bgSrc)
      } else {
        this._pendingImageSrc = null
        this._bg.style.backgroundImage = ""
      }
    }

    /* The scrim is there for contrast over an image or video only. */
    this._setScrim(bgVideo.length > 0 || bgSrc.length > 0)
    return
  }

  /*
   * Show or hide the scrim. While it shows, the content text defaults to
   * the light colour (see the stylesheet). A background that failed to
   * load is gone, so the scrim goes with it and the plain colour shows.
   */
  _setScrim(visible) {
    this._overlay.hidden = visible === false
    this._root.toggleAttribute("data-scrim", visible === true)
    return
  }

  _showImage(src) {
    this._bg.style.backgroundImage = cssUrl(src)

    if (this._pendingImageSrc === src) {
      return
    }
    this._pendingImageSrc = src

    const probe = new Image()
    probe.addEventListener("error", () => {
      /* Only the source still asked for may clear the image. */
      if (this._pendingImageSrc === src) {
        this._pendingImageSrc = null
        this._bg.style.backgroundImage = ""
        this._setScrim(false)
        this.emit("mj-hero-bg-error", { src: src })
      }
    })
    probe.src = src
    return
  }

  _syncVideo(src) {
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches

    if (this._videoEl === null) {
      const video = document.createElement("video")
      /*
       * The properties, not only the attributes: on a script-created element
       * the `muted` attribute sets only the default, and an unmuted video is
       * not allowed to autoplay.
       */
      video.muted = true
      video.defaultMuted = true
      video.loop = true
      video.playsInline = true
      video.autoplay = reducedMotion === false
      video.setAttribute("aria-hidden", "true")
      /*
       * The element is reused when `bg-video` changes, so the failed source
       * is read from the element, not from this closure; only the source
       * still asked for reports.
       */
      video.addEventListener("error", () => {
        const failedSrc = video.getAttribute("src") || ""
        if (this._videoEl === video && safeUrl(this.getAttribute("bg-video") || "", "") === failedSrc) {
          this._setScrim(false)
          this.emit("mj-hero-bg-error", { src: failedSrc })
        }
      })
      video.addEventListener("play", this._syncVideoToggle.bind(this))
      video.addEventListener("pause", this._syncVideoToggle.bind(this))
      this._videoEl = video
      this._bg.appendChild(video)
    }

    const poster = safeUrl(this.getAttribute("video-poster") || "", "")
    if (poster.length > 0) {
      this._videoEl.poster = poster
    } else {
      this._videoEl.removeAttribute("poster")
    }

    if (this._videoEl.getAttribute("src") !== src) {
      this._videoEl.src = src
    }

    this._videoToggle.hidden = false
    this._syncVideoToggle()
    return
  }

  _removeVideo() {
    if (this._videoEl !== null) {
      this._videoEl.pause()
      this._videoEl.remove()
      this._videoEl = null
    }
    this._videoToggle.hidden = true
    return
  }

  _syncVideoToggle() {
    const playing = this._videoEl !== null && this._videoEl.paused === false
    this._videoToggle.setAttribute("data-playing", playing === true ? "true" : "false")
    this._videoToggle.setAttribute(
      "aria-label",
      playing === true ? t("mj.hero.pauseVideo") : t("mj.hero.playVideo")
    )
    return
  }

  _onVideoToggle() {
    if (this._videoEl === null) {
      return
    }

    if (this._videoEl.paused === true) {
      const started = this._videoEl.play()
      if (started !== undefined && typeof started.catch === "function") {
        started.catch(() => {
          this._syncVideoToggle()
        })
      }
    } else {
      this._videoEl.pause()
    }
    this._syncVideoToggle()
    return
  }

  /* ----- styles ----- */

  _syncStyles() {
    if (this._root === null || this._root === undefined) {
      return
    }

    const overlayOpacity = this.getAttribute("overlay-opacity")
    const minHeight = this.getAttribute("min-height")
    const align = this.getAttribute("align")

    let opacity = null
    if (overlayOpacity !== null && overlayOpacity.trim().length > 0) {
      const parsed = Number(overlayOpacity)
      const value = Number.isNaN(parsed) === true ? DEFAULT_OVERLAY_OPACITY : parsed
      opacity = String(Math.max(0, Math.min(1, value)))
    }
    this._setCustomProperty("--mj-hero-overlay-opacity", opacity)
    this._setCustomProperty("--mj-hero-min-height", minHeight !== null && minHeight.length > 0 ? minHeight : null)

    let justify = null
    let textAlign = null
    if (align === "start") {
      justify = "flex-start"
      textAlign = "start"
    } else if (align === "end") {
      justify = "flex-end"
      textAlign = "end"
    } else if (align !== null) {
      justify = "center"
      textAlign = "center"
    }
    this._setCustomProperty("--mj-hero-justify", justify)
    this._setCustomProperty("--mj-hero-text-align", textAlign)
    return
  }

  /* ----- heading ----- */

  /* The heading level from `heading-level`, limited to 1-6. */
  _headingLevel() {
    const parsed = parseInt(this.getAttribute("heading-level") || "", 10)
    let level = DEFAULT_HEADING_LEVEL
    if (Number.isNaN(parsed) === false && parsed >= 1 && parsed <= 6) {
      level = parsed
    }
    return level
  }

  /*
   * Bring the heading element in line with `heading-level` (replacing the
   * element, and moving its slot across, when the level changes) and the
   * `heading` text, which is the fallback content of the heading slot.
   */
  _rebuildHeading() {
    if (this._headingEl === null || this._headingEl === undefined) {
      return
    }

    const tagName = `h${this._headingLevel()}`

    if (this._headingEl.localName !== tagName) {
      const replacement = document.createElement(tagName)
      replacement.className = "heading-el"
      replacement.setAttribute("part", "heading")
      replacement.id = this._headingId
      while (this._headingEl.firstChild !== null) {
        replacement.appendChild(this._headingEl.firstChild)
      }
      this._headingEl.replaceWith(replacement)
      this._headingEl = replacement
    }

    this._headingText.textContent = this.getAttribute("heading") || ""
    this._syncHeadingPresence()
    return
  }

  /* Expose the heading (and label the section by it) only when it has text. */
  _syncHeadingPresence() {
    const slot = this._headingEl.querySelector("slot[name='heading']")
    const slotted = slot !== null && slot.assignedNodes({ flatten: false }).length > 0
    const heading = this.getAttribute("heading") || ""
    const present = slotted === true || heading.length > 0

    this._headingEl.hidden = present === false
    if (present === true) {
      this._root.setAttribute("aria-labelledby", this._headingId)
    } else {
      this._root.removeAttribute("aria-labelledby")
    }
    return
  }

  get videoElement() {
    return this._videoEl
  }
}
