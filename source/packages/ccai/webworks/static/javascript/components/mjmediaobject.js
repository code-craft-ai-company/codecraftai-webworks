/*
 * mjmediaobject.js
 *
 * <mj-media-object> -- places a fixed-size media element beside a variable-width
 * text block. The foundational pattern for comment rows, list items with avatars,
 * notification rows, and settings rows.
 *
 * The media region is `media-size` wide (3rem by default). A slotted image,
 * video, canvas or svg is scaled to that width; any other element keeps its
 * own size and the region grows to hold it. The region is removed while
 * nothing is slotted into it. With `stack-at` (a length) the media stacks
 * above the content whenever the component is narrower than that length.
 *
 * A custom property is written on the host only for an attribute that is
 * present, so stylesheet rules such as
 * `mj-media-object { --mj-media-object-gap: 2rem }` apply whenever the
 * matching attribute is absent. The properties written by attributes belong
 * to one media object: the host resets them, so a nested media object (a
 * reply in a comment thread) never inherits the gap, alignment or media size
 * of the one around it.
 *
 * `align` is also the legacy HTML presentational attribute, which browsers
 * map to `text-align` on any element; the host takes its text alignment from
 * its parent instead, so `align` only aligns the media and the content.
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

/*
 * Per-element properties: an inline value written by an attribute or an
 * author rule on the element wins over this reset, an ancestor's value does
 * not reach the media object.
 */
:host {
  --mj-media-object-gap: initial;
  --mj-media-object-align: initial;
  --mj-media-object-media-size: initial;
}

/* Cancel the legacy align => text-align presentational hint. */
:host([align]) { text-align: inherit; }

.root {
  position: relative;
  display: flex;
  flex-direction: var(--mj-media-object-direction, row);
  align-items: var(--mj-media-object-align, flex-start);
  gap: var(--mj-media-object-gap, var(--mj-space-4));
}

.media {
  flex: 0 0 auto;
  inline-size: var(--mj-media-object-media-size, 3rem);
  min-inline-size: min-content;
}

.media.empty {
  display: none;
}

.content {
  flex: 1 1 0;
  min-inline-size: 0;
}

:host([media-position="end"]) .media {
  order: 1;
}

/* Below the stack-at width the media sits above the content. */
.root.stacked {
  flex-direction: column;
}

.root.stacked .media {
  order: 0;
}

.root.stacked .content {
  flex: 0 1 auto;
  align-self: stretch;
}

/* Replaced media fills the media region and keeps its proportions. */
::slotted(img[slot="media"]),
::slotted(video[slot="media"]),
::slotted(canvas[slot="media"]),
::slotted(svg[slot="media"]) {
  display: block;
  inline-size: 100%;
  max-inline-size: 100%;
  block-size: auto;
}
`;

/*
 * Resolve a length written as a number ("480"), in px, rem or em to pixels.
 * Returns null for anything else.
 */
function resolveLength(text, element) {
  let pixels = null

  if (text !== null && text !== undefined) {
    const match = /^\s*(\d*\.?\d+)\s*(px|rem|em)?\s*$/.exec(text)

    if (match !== null) {
      const amount = parseFloat(match[1])
      const unit = match[2] !== undefined ? match[2] : "px"

      if (unit === "px") {
        pixels = amount
      } else if (unit === "rem") {
        pixels = amount * parseFloat(window.getComputedStyle(document.documentElement).fontSize)
      } else {
        pixels = amount * parseFloat(window.getComputedStyle(element).fontSize)
      }
    }
  }

  return pixels
}

export class MjMediaObject extends MjElement {
  static tagName = "mj-media-object";
  static styles = STYLES;
  static watched = ["media-position", "gap", "align", "media-size", "stack-at"];

  constructor() {
    super()
    this._root = null
    this._mediaEl = null
    this._mediaSlot = null
    this._resizeObserver = null
    this._stackFrame = null
  }

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
    this._mediaSlot = this.$("slot[name='media']")
    this.listen(this._mediaSlot, "slotchange", this._syncMediaRegion.bind(this))
    this._syncStyles()
    this._syncMediaRegion()
    return
  }

  onConnected() {
    this._syncStackObserver()
    this.onTeardown(() => {
      this._stopStackObserver()
    })
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._root === undefined || this._root === null) {
      return
    }

    this._syncStyles()
    if (name === "stack-at") {
      this._syncStackObserver()
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

  _syncStyles() {
    if (this._root === null || this._root === undefined) {
      return
    }

    const gap = this.getAttribute("gap")
    const align = this.getAttribute("align")
    const mediaSize = this.getAttribute("media-size")

    let alignValue = null
    if (align !== null && align.length > 0) {
      alignValue = align === "start" ? "flex-start" : align === "end" ? "flex-end" : align
    }

    this._setCustomProperty("--mj-media-object-gap", gap !== null ? (GAP_MAP[gap] || GAP_MAP.md) : null)
    this._setCustomProperty("--mj-media-object-align", alignValue)
    this._setCustomProperty("--mj-media-object-media-size", mediaSize !== null && mediaSize.length > 0 ? mediaSize : null)
    return
  }

  /* Remove the media region (and with it the gap) while its slot is empty. */
  _syncMediaRegion() {
    if (this._mediaEl === null || this._mediaSlot === null) {
      return
    }

    const hasMedia = this._mediaSlot.assignedNodes({ flatten: true }).length > 0
    this._mediaEl.classList.toggle("empty", hasMedia === false)
    return
  }

  /* ----- stack-at ----- */

  /*
   * Watch the host width only while `stack-at` holds a usable length. The
   * breakpoint is a per-element attribute value, which a container query in
   * the shared stylesheet cannot read, so the comparison is made here.
   */
  _syncStackObserver() {
    const breakpoint = resolveLength(this.getAttribute("stack-at"), this)

    if (breakpoint === null) {
      this._stopStackObserver()
      if (this._root !== null && this._root !== undefined) {
        this._root.classList.remove("stacked")
      }
    } else {
      if (this._resizeObserver === null && typeof ResizeObserver === "function" && this.isConnected === true) {
        this._resizeObserver = new ResizeObserver(() => {
          this._scheduleStackCheck()
        })
        this._resizeObserver.observe(this)
      }
      this._applyStacking()
    }
    return
  }

  _stopStackObserver() {
    if (this._resizeObserver !== null) {
      this._resizeObserver.disconnect()
      this._resizeObserver = null
    }
    if (this._stackFrame !== null) {
      window.cancelAnimationFrame(this._stackFrame)
      this._stackFrame = null
    }
    return
  }

  _scheduleStackCheck() {
    if (this._stackFrame !== null) {
      return
    }
    this._stackFrame = window.requestAnimationFrame(() => {
      this._stackFrame = null
      this._applyStacking()
    })
    return
  }

  _applyStacking() {
    if (this._root === null || this._root === undefined) {
      return
    }

    const breakpoint = resolveLength(this.getAttribute("stack-at"), this)
    const width = this.clientWidth
    const stacked = breakpoint !== null && width > 0 && width < breakpoint
    this._root.classList.toggle("stacked", stacked)
    return
  }

  /* True while the media is stacked above the content (see `stack-at`). */
  get stacked() {
    const stacked = this._root !== null && this._root !== undefined && this._root.classList.contains("stacked")
    return stacked
  }

  get contentElement() {
    return this.$(".content") || null
  }
}
