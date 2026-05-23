/*
 * mjhero.js
 *
 * <mj-hero> -- a prominent full-width introductory banner combining a
 * background image/color, heading, body, and optional action buttons.
 */

import { MjElement, nextId } from "../core/mjelement.js";

const STYLES = `
:host {
  display: block;
}

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

.heading-el {
  margin: 0;
  font-size: clamp(var(--mj-font-size-xl), 5vw, var(--mj-font-size-2xl));
  font-weight: var(--mj-font-weight-bold);
  line-height: 1.2;
  color: var(--mj-hero-heading-color, var(--mj-text-on-accent));
}

.body-region {
  color: var(--mj-hero-body-color, var(--mj-text-on-accent));
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

export class MjHero extends MjElement {
  static tagName = "mj-hero";
  static styles = STYLES;
  static watched = [
    "heading", "heading-level", "bg-src", "bg-video", "bg-color",
    "overlay-opacity", "align", "full-height", "min-height"
  ];

  constructor() {
    super()
    this._headingId = nextId("mj-hero-heading")
    this._videoEl = null
  }

  render() {
    const headingLevel = this.getAttribute("heading-level") || "1"
    const heading = this.getAttribute("heading") || ""
    const markup = `
      <section class="root" part="root" aria-labelledby="${this._headingId}">
        <div class="background" part="background" aria-hidden="true"></div>
        <div class="overlay" part="overlay" aria-hidden="true"></div>
        <div class="content" part="content">
          <h${headingLevel} class="heading-el" part="heading" id="${this._headingId}">
            <slot name="heading">${heading}</slot>
          </h${headingLevel}>
          <div class="body-region" part="body"><slot name="body"></slot></div>
          <div class="actions-region" part="actions"><slot name="actions"></slot></div>
          <div class="media-region" part="media"><slot name="media"></slot></div>
        </div>
      </section>
    `
    return markup
  }

  afterRender() {
    this._root = this.$(".root")
    this._bg = this.$(".background")
    this._overlay = this.$(".overlay")
    this._syncBackground()
    this._syncStyles()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._root === undefined) {
      return
    }
    if (name === "bg-src" || name === "bg-video" || name === "bg-color") {
      this._syncBackground()
    } else if (name === "heading" || name === "heading-level") {
      this._rebuildHeading()
    } else {
      this._syncStyles()
    }
    return
  }

  _syncBackground() {
    if (this._bg === null || this._bg === undefined) {
      return
    }

    const bgVideo = this.getAttribute("bg-video") || ""
    const bgSrc = this.getAttribute("bg-src") || ""
    const bgColor = this.getAttribute("bg-color") || ""

    if (bgVideo.length > 0) {
      this._bg.style.backgroundImage = ""
      if (this._videoEl === null) {
        this._videoEl = document.createElement("video")
        this._videoEl.setAttribute("muted", "")
        this._videoEl.setAttribute("playsinline", "")
        this._videoEl.setAttribute("loop", "")
        this._videoEl.style.cssText = "position:absolute;inset:0;width:100%;height:100%;object-fit:cover;"
        this._videoEl.src = bgVideo
        const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches
        if (prefersReduced === false) {
          this._videoEl.setAttribute("autoplay", "")
        }
        this._videoEl.addEventListener("error", () => {
          this.emit("mj-hero-bg-error", { src: bgVideo })
        })
        this._bg.appendChild(this._videoEl)
      } else {
        this._videoEl.src = bgVideo
      }
    } else if (bgSrc.length > 0) {
      if (this._videoEl !== null) {
        this._videoEl.remove()
        this._videoEl = null
      }
      this._bg.style.backgroundImage = `url(${bgSrc})`
      const img = new Image()
      img.src = bgSrc
      img.addEventListener("error", () => {
        this._bg.style.backgroundImage = ""
        if (bgColor.length > 0) {
          this._root.style.background = bgColor
        }
        this.emit("mj-hero-bg-error", { src: bgSrc })
      })
    } else {
      if (this._videoEl !== null) {
        this._videoEl.remove()
        this._videoEl = null
      }
      this._bg.style.backgroundImage = ""
      if (bgColor.length > 0) {
        this.style.setProperty("--mj-hero-bg-color", bgColor)
      }
    }
    return
  }

  _syncStyles() {
    const overlayOpacity = this.getAttribute("overlay-opacity") || "0.4"
    const minHeight = this.getAttribute("min-height") || "40vh"
    const align = this.getAttribute("align") || "center"

    const opacity = Math.max(0, Math.min(1, parseFloat(overlayOpacity) || 0.4))
    this.style.setProperty("--mj-hero-overlay-opacity", String(opacity))
    this.style.setProperty("--mj-hero-min-height", minHeight)

    const justify = align === "start" ? "flex-start" : align === "end" ? "flex-end" : "center"
    this.style.setProperty("--mj-hero-justify", justify)

    const textAlign = align === "start" ? "start" : align === "end" ? "end" : "center"
    this.style.setProperty("--mj-hero-text-align", textAlign)
    return
  }

  _rebuildHeading() {
    const headingEl = this.$(".heading-el")
    if (headingEl === null) {
      return
    }
    const level = this.getAttribute("heading-level") || "1"
    const heading = this.getAttribute("heading") || ""
    if (headingEl.tagName.toLowerCase() !== `h${level}`) {
      const newH = document.createElement(`h${level}`)
      newH.className = "heading-el"
      newH.setAttribute("part", "heading")
      newH.setAttribute("id", this._headingId)
      newH.innerHTML = `<slot name="heading">${heading}</slot>`
      headingEl.parentNode.replaceChild(newH, headingEl)
    } else {
      const slot = headingEl.querySelector("slot[name='heading']")
      if (slot !== null) {
        slot.textContent = heading
      }
    }
    return
  }

  get videoElement() {
    return this._videoEl
  }
}
