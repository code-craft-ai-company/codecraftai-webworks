/*
 * mjcard.js
 *
 * <mj-card> -- a contained content surface grouping media, header, body, and
 * footer into a visually distinct card unit.
 */

import { MjElement, nextId } from "../core/mjelement.js";

const STYLES = `
:host {
  display: block;
}

.card {
  display: flex;
  flex-direction: column;
  background: var(--mj-card-bg, var(--mj-surface));
  border-radius: var(--mj-card-radius, var(--mj-radius-md));
  box-shadow: var(--mj-card-shadow, var(--mj-elevation-2));
  border: var(--mj-card-border-width, 0) solid var(--mj-card-border, var(--mj-border));
  overflow: hidden;
  position: relative;
  min-block-size: var(--mj-space-7);
}

:host([orientation="horizontal"]) .card {
  flex-direction: row;
}

.media-region {
  position: relative;
  flex-shrink: 0;
}

:host([orientation="horizontal"]) .media-region {
  inline-size: clamp(8rem, 35%, 20rem);
}

.badge-region {
  position: absolute;
  inset-block-start: var(--mj-space-2);
  inset-inline-end: var(--mj-space-2);
  z-index: 1;
}

.content {
  display: flex;
  flex-direction: column;
  gap: var(--mj-card-gap, var(--mj-space-2));
  flex: 1;
}

.header-region {
  padding: var(--mj-card-padding, var(--mj-space-4));
  padding-block-end: 0;
}

.heading {
  margin: 0;
  font-size: var(--mj-font-size-lg);
  font-weight: var(--mj-font-weight-bold);
  color: var(--mj-text);
  overflow: hidden;
  text-overflow: ellipsis;
}

.subheading {
  margin: var(--mj-space-1) 0 0;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text-muted);
}

.body-region {
  padding: var(--mj-card-padding, var(--mj-space-4));
  padding-block: 0;
  flex: 1;
  color: var(--mj-text);
}

.footer-region {
  padding: var(--mj-card-padding, var(--mj-space-4));
  padding-block-start: 0;
}

.card-link {
  position: absolute;
  inset: 0;
  z-index: 0;
  border-radius: inherit;
  text-decoration: none;
  color: transparent;
}

.card-link:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.shimmer {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg,
    var(--mj-bg-muted) 25%,
    var(--mj-bg-subtle) 50%,
    var(--mj-bg-muted) 75%);
  background-size: 200% 100%;
  animation: mj-shimmer var(--mj-motion-slow) linear infinite;
}

@keyframes mj-shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

@media (prefers-reduced-motion: reduce) {
  .shimmer { animation: none; background: var(--mj-bg-muted); }
}

:host(:not([loading])) .shimmer { display: none; }

::slotted([slot="media"]) { display: block; width: 100%; height: 100%; object-fit: cover; }
`;

export class MjCard extends MjElement {
  static tagName = "mj-card";
  static styles = STYLES;
  static watched = ["heading", "subheading", "href", "orientation", "elevation", "loading", "aspect-ratio"];

  constructor() {
    super()
    this._headingLevel = 3
  }

  render() {
    const markup = `
      <article class="card" part="root">
        <div class="shimmer" aria-hidden="true"></div>
        <div class="media-region" part="media">
          <slot name="badge"><div class="badge-region" part="badge"><slot name="badge-inner"></slot></div></slot>
          <slot name="media"></slot>
        </div>
        <div class="content">
          <div class="header-region" part="header">
            <slot name="header"><div class="header-attr" part="header-attr"></div></slot>
          </div>
          <div class="body-region" part="body"><slot></slot></div>
          <div class="footer-region" part="footer"><slot name="footer"></slot></div>
        </div>
      </article>
    `
    return markup
  }

  afterRender() {
    this._card = this.$(".card")
    this._headerAttr = this.$(".header-attr")
    this._syncCard()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._card !== undefined) {
      this._syncCard()
    }
    return
  }

  _syncCard() {
    if (this._card === null || this._card === undefined) {
      return
    }

    const elevation = this.getAttribute("elevation") || "raised"
    let shadow = "var(--mj-elevation-2)"
    let borderWidth = "0"
    if (elevation === "flat") {
      shadow = "none"
    } else if (elevation === "outlined") {
      shadow = "none"
      borderWidth = "1px"
    }
    this.style.setProperty("--mj-card-shadow", shadow)
    this.style.setProperty("--mj-card-border-width", borderWidth)

    const loading = this.hasAttribute("loading")
    this._card.setAttribute("aria-busy", loading === true ? "true" : "false")

    const href = this.getAttribute("href") || ""
    const existingLink = this.$(".card-link")
    if (href.length > 0) {
      if (existingLink === null) {
        const link = document.createElement("a")
        link.className = "card-link"
        link.setAttribute("part", "link")
        link.href = href
        if (this.hasAttribute("disabled")) {
          link.setAttribute("aria-disabled", "true")
          link.setAttribute("tabindex", "-1")
        }
        this._card.prepend(link)
      } else {
        existingLink.href = href
      }
    } else if (existingLink !== null) {
      existingLink.remove()
    }

    if (this._headerAttr !== null && this._headerAttr !== undefined) {
      const heading = this.getAttribute("heading") || ""
      const subheading = this.getAttribute("subheading") || ""
      const level = this._headingLevel
      let html = ""
      if (heading.length > 0) {
        html += `<h${level} class="heading" title="${heading}">${heading}</h${level}>`
      }
      if (subheading.length > 0) {
        html += `<p class="subheading">${subheading}</p>`
      }
      this._headerAttr.innerHTML = html
    }
    return
  }

  get headingLevel() {
    return this._headingLevel
  }

  set headingLevel(value) {
    const clamped = Math.max(1, Math.min(6, parseInt(value, 10) || 3))
    this._headingLevel = clamped
    this._syncCard()
    return
  }
}
