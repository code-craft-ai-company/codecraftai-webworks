/*
 * mjskeleton.js
 *
 * <mj-skeleton> -- a loading placeholder that mimics the shape of content that
 * is about to load. Marked aria-hidden; announces loading state via a live region.
 */

import { MjElement } from "../core/mjelement.js";

const STYLES = `
:host {
  display: block;
  inline-size: var(--mj-skeleton-width, 100%);
  block-size: var(--mj-skeleton-height, 1rem);
  position: relative;
  overflow: hidden;
  border-radius: var(--mj-skeleton-radius, var(--mj-radius-sm));
  background: var(--mj-skeleton-bg, var(--mj-bg-muted));
}

:host([variant="circle"]) {
  border-radius: var(--mj-radius-circle);
  block-size: var(--mj-skeleton-width, 1rem);
}

:host([variant="text"]) {
  block-size: auto;
  background: transparent;
}

.shimmer {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    90deg,
    transparent 0%,
    var(--mj-skeleton-shimmer-color, var(--mj-bg-subtle)) 50%,
    transparent 100%
  );
  background-size: 200% 100%;
  animation: mj-skeleton-shimmer var(--mj-skeleton-duration, 1.5s) linear infinite;
}

@keyframes mj-skeleton-shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

@media (prefers-reduced-motion: reduce) {
  .shimmer { animation: none; background: transparent; }
}

:host([animated="false"]) .shimmer {
  animation: none;
  background: transparent;
}

.line {
  block-size: var(--mj-skeleton-line-height, 1em);
  background: var(--mj-skeleton-bg, var(--mj-bg-muted));
  border-radius: var(--mj-skeleton-radius, var(--mj-radius-sm));
  position: relative;
  overflow: hidden;
}

.line + .line {
  margin-block-start: var(--mj-skeleton-line-gap, 0.5em);
}

.line:last-child {
  inline-size: 80%;
}

.line .shimmer {
  position: absolute;
  inset: 0;
}

.status {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0,0,0,0);
  white-space: nowrap;
}
`;

export class MjSkeleton extends MjElement {
  static tagName = "mj-skeleton";
  static styles = STYLES;
  static watched = ["variant", "width", "height", "lines", "animated", "loading-label", "radius"];

  constructor() {
    super()
    this._mqListener = null
  }

  render() {
    const loadingLabel = this.getAttribute("loading-label") || "Loading"
    const variant = this.getAttribute("variant") || "rectangle"
    const lines = parseInt(this.getAttribute("lines") || "1", 10)

    let inner = ""
    if (variant === "text") {
      const lineCount = Math.max(1, lines)
      for (let i = 0; i < lineCount; i = i + 1) {
        inner += `<div class="line" aria-hidden="true"><div class="shimmer" part="shimmer"></div></div>`
      }
    } else {
      inner = `<div class="shimmer" part="shimmer"></div>`
    }

    const markup = `
      <div class="root" part="root" aria-hidden="true">
        ${inner}
      </div>
      <span class="status" role="status" aria-live="polite">${loadingLabel}</span>
    `
    return markup
  }

  afterRender() {
    this._syncDimensions()
    this._attachMotionListener()
    return
  }

  onConnected() {
    return
  }

  onDisconnected() {
    if (this._mqListener !== null) {
      const mq = window.matchMedia("(prefers-reduced-motion: reduce)")
      mq.removeEventListener("change", this._mqListener)
      this._mqListener = null
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "variant" || name === "lines") {
      if (this.shadowRoot !== null) {
        this.shadowRoot.innerHTML = this.render()
        this._syncDimensions()
      }
    } else {
      this._syncDimensions()
    }
    return
  }

  _syncDimensions() {
    const width = this.getAttribute("width") || "100%"
    const height = this.getAttribute("height") || "1rem"
    const radius = this.getAttribute("radius") || ""

    this.style.setProperty("--mj-skeleton-width", width)
    this.style.setProperty("--mj-skeleton-height", height)
    if (radius.length > 0) {
      this.style.setProperty("--mj-skeleton-radius", radius)
    }
    return
  }

  _attachMotionListener() {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)")
    this._mqListener = () => {
      this._syncDimensions()
    }
    mq.addEventListener("change", this._mqListener)
    return
  }

  get animating() {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)")
    if (mq.matches === true) {
      return false
    }
    const animated = this.getAttribute("animated")
    return animated !== "false"
  }
}
