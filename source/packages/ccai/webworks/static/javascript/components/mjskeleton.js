/*
 * mjskeleton.js
 *
 * <mj-skeleton> -- a loading placeholder that mimics the shape of content that
 * is about to load. The shapes are hidden from assistive technology.
 *
 * Announcement: a placeholder is usually built from several skeletons, and
 * each one saying "Loading" would repeat it. Only ONE connected skeleton --
 * the first one, ignoring those with announce="false" -- carries the polite
 * status region with the loading label; every other skeleton exposes
 * nothing at all. When the announcing skeleton goes away the next one takes
 * over.
 */

import { MjElement } from "../core/mjelement.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";

/* Connected skeletons in connection order; the first eligible one announces. */
const CONNECTED_SKELETONS = [];

function electAnnouncer() {
  let elected = false

  for (let index = 0; index < CONNECTED_SKELETONS.length; index = index + 1) {
    const skeleton = CONNECTED_SKELETONS[index]
    const eligible = elected === false && skeleton.getAttribute("announce") !== "false"
    skeleton._setAnnouncing(eligible)
    if (eligible === true) {
      elected = true
    }
  }
  return
}

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

/* A circle is as tall as it is wide, whatever unit the width uses. */
:host([variant="circle"]) {
  border-radius: var(--mj-radius-circle);
  block-size: auto;
  aspect-ratio: 1;
  flex-shrink: 0;
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

/* The last of several lines is shorter, like the end of a paragraph. */
.line:last-child:not(:first-child) {
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
  static watched = ["variant", "width", "height", "lines", "animated", "loading-label", "radius", "announce"];

  constructor() {
    super()
    this._mqListener = null
    this._status = null
    this._announcing = false

    /* The shape the shadow DOM was built for, so it is rebuilt only on a change. */
    this._renderedShape = null
  }

  /* "rectangle", "circle" or "text:<line count>". */
  _shapeKey() {
    const variant = this.getAttribute("variant") || "rectangle"
    let key = variant

    if (variant === "text") {
      const lines = parseInt(this.getAttribute("lines") || "1", 10)
      const lineCount = Number.isNaN(lines) === true ? 1 : Math.max(1, Math.min(50, lines))
      key = `text:${lineCount}`
    }

    return key
  }

  render() {
    const shape = this._shapeKey()
    let inner = html`<div class="shimmer" part="shimmer"></div>`

    if (shape.startsWith("text:") === true) {
      const lineCount = parseInt(shape.slice(5), 10)
      const lines = []
      for (let index = 0; index < lineCount; index = index + 1) {
        lines.push(html`<div class="line" aria-hidden="true"><div class="shimmer" part="shimmer"></div></div>`)
      }
      inner = lines
    }

    this._renderedShape = shape
    const markup = html`
      <div class="root" part="root" aria-hidden="true">${inner}</div>
      <span class="status" role="status" aria-live="polite" hidden></span>
    `
    return markup
  }

  afterRender() {
    this._status = this.$(".status")
    this._syncDimensions()
    this._syncStatus()
    this._attachMotionListener()
    return
  }

  onConnected() {
    CONNECTED_SKELETONS.push(this)
    electAnnouncer()

    this.onTeardown(() => {
      const index = CONNECTED_SKELETONS.indexOf(this)
      if (index >= 0) {
        CONNECTED_SKELETONS.splice(index, 1)
      }
      this._announcing = false
      electAnnouncer()
    })
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
    if (this._status === undefined || this._status === null) {
      return
    }

    if (name === "variant" || name === "lines") {
      if (this._shapeKey() !== this._renderedShape) {
        this.shadowRoot.innerHTML = String(this.render())
        this._status = this.$(".status")
        this._syncStatus()
      }
      this._syncDimensions()
    } else if (name === "loading-label") {
      this._syncStatus()
    } else if (name === "announce") {
      electAnnouncer()
    } else {
      this._syncDimensions()
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

  _syncDimensions() {
    const width = this.getAttribute("width")
    const height = this.getAttribute("height")
    const radius = this.getAttribute("radius")

    this._setCustomProperty("--mj-skeleton-width", width !== null && width.length > 0 ? width : null)
    this._setCustomProperty("--mj-skeleton-height", height !== null && height.length > 0 ? height : null)
    this._setCustomProperty("--mj-skeleton-radius", radius !== null && radius.length > 0 ? radius : null)
    return
  }

  /* Called by `electAnnouncer`: whether this skeleton carries the status. */
  _setAnnouncing(announcing) {
    this._announcing = announcing
    this._syncStatus()
    return
  }

  _syncStatus() {
    if (this._status === null || this._status === undefined) {
      return
    }

    const label = this.getAttribute("loading-label")
    this._status.textContent = label !== null && label.length > 0 ? label : t("core.loading")
    this._status.hidden = this._announcing === false
    return
  }

  _attachMotionListener() {
    if (this._mqListener !== null) {
      return
    }
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)")
    this._mqListener = () => {
      this._syncDimensions()
    }
    mq.addEventListener("change", this._mqListener)
    return
  }

  /* True for the one skeleton that carries the loading announcement. */
  get announcing() {
    return this._announcing
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
