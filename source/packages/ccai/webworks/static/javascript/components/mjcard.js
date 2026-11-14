/*
 * mjcard.js
 *
 * <mj-card> -- a contained content surface grouping media, header, body, and
 * footer into a visually distinct card unit.
 *
 * Clickable cards (`href`): a transparent link is stretched over the card,
 * so the media, header and body navigate when clicked. The footer -- the
 * place for actions -- and interactive elements slotted directly into the
 * header or body (links, buttons, form controls, anything with a tabindex)
 * are stacked ABOVE that link and keep working on their own. Interactive
 * content nested deeper inside the body must be raised by its author with
 * `position: relative; z-index: 2`.
 *
 * Stacking inside the card (the card is its own stacking context):
 *   0  media, header, body         2  footer and slotted interactive elements
 *   1  the stretched link          3  the loading shimmer
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { html, safeUrl } from "../core/html.js";
import { t } from "../core/intl.js";

/* The longest accessible name derived from the card's own text. */
const LINK_LABEL_LIMIT = 120;

const STYLES = `
:host {
  display: flex;
  flex-direction: column;
}

/*
 * The properties written by \`elevation\` and \`aspect-ratio\` belong to one
 * card: an inline value written by the attribute or an author rule on the
 * element wins over this reset, but a card nested in a card's body never
 * inherits the elevation or media ratio of the card around it.
 */
:host {
  --mj-card-shadow: initial;
  --mj-card-border-width: initial;
  --mj-card-media-ratio: initial;
}

/*
 * disabled switches off the card link only. The shared base sheet turns
 * pointer events off for every disabled host, which would also block the
 * footer actions and the body content; undo that here.
 */
:host([disabled]) {
  pointer-events: auto;
  cursor: auto;
}

.card {
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  background: var(--mj-card-bg, var(--mj-surface));
  border-radius: var(--mj-card-radius, var(--mj-radius-md));
  box-shadow: var(--mj-card-shadow, var(--mj-elevation-2));
  border: var(--mj-card-border-width, 0) solid var(--mj-card-border, var(--mj-border));
  overflow: hidden;
  position: relative;
  isolation: isolate;
  min-block-size: var(--mj-space-7);
}

/*
 * Horizontal: media beside the content. The row wraps, so when the card is
 * too narrow to leave the content its minimum width the content drops below
 * the media and the card reads as a vertical one.
 */
:host([orientation="horizontal"]) .card {
  flex-flow: row wrap;
}

.media-region {
  position: relative;
  flex-shrink: 0;
  overflow: hidden;
  aspect-ratio: var(--mj-card-media-ratio, auto);
}

.media-region.empty {
  display: none;
}

:host([orientation="horizontal"]) .media-region {
  flex: 1 1 clamp(8rem, 35%, 20rem);
}

.badge-region {
  position: absolute;
  inset-block-start: var(--mj-space-2);
  inset-inline-end: var(--mj-space-2);
  z-index: 0;
}

.content {
  display: flex;
  flex-direction: column;
  gap: var(--mj-card-gap, var(--mj-space-2));
  flex: 1;
  min-inline-size: 0;
}

:host([orientation="horizontal"]) .content {
  flex: 999 1 var(--mj-card-content-min-width, 12rem);
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
  overflow-wrap: anywhere;
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
  position: relative;
  z-index: 2;
  padding: var(--mj-card-padding, var(--mj-space-4));
  padding-block-start: 0;
}

.card-link {
  position: absolute;
  inset: 0;
  z-index: 1;
  border-radius: inherit;
  text-decoration: none;
  color: transparent;
}

.card-link:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: calc(-1 * var(--mj-focus-ring-width));
}

.card-link[aria-disabled="true"] {
  pointer-events: none;
}

/* Interactive elements slotted straight into the header or body. */
::slotted(a),
::slotted(button),
::slotted(input),
::slotted(select),
::slotted(textarea),
::slotted(label),
::slotted(details),
::slotted([tabindex]),
::slotted([role="button"]),
::slotted([role="link"]),
::slotted(mj-button),
::slotted(mj-link) {
  position: relative;
  z-index: 2;
}

.shimmer {
  position: absolute;
  inset: 0;
  z-index: 3;
  background: linear-gradient(90deg,
    var(--mj-bg-muted) 25%,
    var(--mj-bg-subtle) 50%,
    var(--mj-bg-muted) 75%);
  background-size: 200% 100%;
  animation: mj-shimmer var(--mj-card-shimmer-duration, 1.5s) linear infinite;
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
  static watched = [
    "heading", "subheading", "href", "orientation", "elevation", "loading",
    "aspect-ratio", "aria-label"
  ];

  constructor() {
    super()
    this._headingLevel = 3
    this._headingId = nextId("mj-card-heading")
    this._card = null
    this._link = null
    this._headerAttr = null
    this._mediaRegion = null
    this._content = null
    this._status = null

    /* The loading state last announced, so the status changes only on a change. */
    this._announcedLoading = false
  }

  render() {
    const markup = html`
      <article class="card" part="root">
        <div class="shimmer" aria-hidden="true"></div>
        <div class="media-region" part="media">
          <slot name="media"></slot>
          <div class="badge-region" part="badge"><slot name="badge"><slot name="badge-inner"></slot></slot></div>
        </div>
        <div class="content">
          <div class="header-region" part="header">
            <slot name="header"><div class="header-attr" part="header-attr"></div></slot>
          </div>
          <div class="body-region" part="body"><slot></slot></div>
          <div class="footer-region" part="footer"><slot name="footer"></slot></div>
        </div>
        <span class="mj-visually-hidden status" role="status"></span>
      </article>
    `
    return markup
  }

  afterRender() {
    this._card = this.$(".card")
    this._headerAttr = this.$(".header-attr")
    this._mediaRegion = this.$(".media-region")
    this._content = this.$(".content")
    this._status = this.$(".status")
    this._link = null

    const mediaSlot = this.$("slot[name='media']")
    const headerSlot = this.$("slot[name='header']")
    this.listen(mediaSlot, "slotchange", this._syncMediaRegion.bind(this))
    this.listen(headerSlot, "slotchange", this._syncLink.bind(this))
    this.listen(this._card, "click", this._onCardClick.bind(this))

    this._announcedLoading = this.hasAttribute("loading")
    this._syncCard()
    this._syncMediaRegion()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._card === undefined || this._card === null) {
      return
    }
    this._syncCard()
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

  _syncCard() {
    if (this._card === null || this._card === undefined) {
      return
    }

    this._syncElevation()
    this._syncHeader()
    this._syncLoading()
    this._syncLink()
    return
  }

  _syncElevation() {
    const elevation = this.getAttribute("elevation")
    let shadow = null
    let borderWidth = null

    if (elevation === "flat") {
      shadow = "none"
      borderWidth = "0"
    } else if (elevation === "outlined") {
      shadow = "none"
      borderWidth = "1px"
    } else if (elevation !== null) {
      shadow = "var(--mj-elevation-2)"
      borderWidth = "0"
    }

    this._setCustomProperty("--mj-card-shadow", shadow)
    this._setCustomProperty("--mj-card-border-width", borderWidth)

    /* aspect-ratio applies to the media region; an unusable value is ignored. */
    const ratio = this.getAttribute("aspect-ratio")
    const usable = ratio !== null && ratio.trim().length > 0 &&
      (typeof CSS === "undefined" || CSS.supports("aspect-ratio", ratio) === true)
    this._setCustomProperty("--mj-card-media-ratio", usable === true ? ratio.trim() : null)
    return
  }

  /*
   * Build the attribute-driven header (the fallback content of the header
   * slot) with DOM nodes; the attribute text only ever becomes text.
   */
  _syncHeader() {
    if (this._headerAttr === null || this._headerAttr === undefined) {
      return
    }

    const heading = this.getAttribute("heading") || ""
    const subheading = this.getAttribute("subheading") || ""

    this._headerAttr.textContent = ""

    if (heading.length > 0) {
      const headingEl = document.createElement(`h${this._headingLevel}`)
      headingEl.className = "heading"
      headingEl.id = this._headingId
      headingEl.textContent = heading
      this._headerAttr.appendChild(headingEl)
    }

    if (subheading.length > 0) {
      const subheadingEl = document.createElement("p")
      subheadingEl.className = "subheading"
      subheadingEl.textContent = subheading
      this._headerAttr.appendChild(subheadingEl)
    }
    return
  }

  /*
   * While loading the shimmer covers the card, the regions underneath are
   * inert (not focusable, not exposed) and a status region says so; it says
   * "Loaded" once when loading ends.
   */
  _syncLoading() {
    const loading = this.hasAttribute("loading")
    this._card.setAttribute("aria-busy", loading === true ? "true" : "false")

    this._mediaRegion.toggleAttribute("inert", loading)
    this._content.toggleAttribute("inert", loading)

    if (loading !== this._announcedLoading) {
      this._announcedLoading = loading
      this._status.textContent = loading === true ? t("core.loading") : t("mj.card.loaded")
    } else if (loading === true) {
      this._status.textContent = t("core.loading")
    }
    return
  }

  /* Hide the media region (and the badge on it) while no media is slotted. */
  _syncMediaRegion() {
    if (this._mediaRegion === null || this._mediaRegion === undefined) {
      return
    }

    const slot = this._mediaRegion.querySelector("slot[name='media']")
    const hasMedia = slot !== null && slot.assignedNodes({ flatten: true }).length > 0
    this._mediaRegion.classList.toggle("empty", hasMedia === false)
    return
  }

  /* ----- card link ----- */

  /*
   * The accessible name of the card link when it cannot simply point at the
   * generated heading: the host's aria-label, the text slotted into the
   * header, or the start of the card's own text.
   */
  _linkLabel() {
    let label = this.getAttribute("aria-label") || ""

    if (label.trim().length === 0) {
      const headerSlot = this.$("slot[name='header']")
      const slotted = headerSlot !== null ? headerSlot.assignedNodes() : []
      const parts = []
      for (let index = 0; index < slotted.length; index = index + 1) {
        parts.push(slotted[index].textContent || "")
      }
      label = parts.join(" ")
    }

    if (label.trim().length === 0) {
      label = this.getAttribute("heading") || ""
    }

    if (label.trim().length === 0) {
      label = this.textContent || ""
    }

    const compact = label.replace(/\s+/g, " ").trim().slice(0, LINK_LABEL_LIMIT)
    return compact
  }

  /*
   * Create, update or remove the stretched link from the current `href`,
   * `disabled` and labelling state. Runs on every sync, so a later change
   * of any of them is reflected.
   */
  _syncLink() {
    if (this._card === null || this._card === undefined) {
      return
    }

    const href = this.getAttribute("href") || ""

    if (href.length === 0) {
      if (this._link !== null) {
        this._link.remove()
        this._link = null
      }
      return
    }

    if (this._link === null) {
      this._link = document.createElement("a")
      this._link.className = "card-link"
      this._link.setAttribute("part", "link")
      this._card.prepend(this._link)
    }

    /* Script-bearing schemes are replaced by an inert fragment link. */
    this._link.setAttribute("href", safeUrl(href))

    const loading = this.hasAttribute("loading")
    if (this.hasAttribute("disabled") === true || loading === true) {
      this._link.setAttribute("aria-disabled", "true")
      this._link.setAttribute("tabindex", "-1")
    } else {
      this._link.removeAttribute("aria-disabled")
      this._link.removeAttribute("tabindex")
    }

    const headerSlot = this.$("slot[name='header']")
    const headerSlotted = headerSlot !== null && headerSlot.assignedNodes().length > 0
    const hostLabel = this.getAttribute("aria-label") || ""
    const heading = this.getAttribute("heading") || ""
    const useHeadingElement = hostLabel.trim().length === 0 && headerSlotted === false && heading.length > 0

    if (useHeadingElement === true) {
      /* Same shadow tree as the link, so the id reference resolves. */
      this._link.setAttribute("aria-labelledby", this._headingId)
      this._link.removeAttribute("aria-label")
    } else {
      this._link.removeAttribute("aria-labelledby")
      const label = this._linkLabel()
      if (label.length > 0) {
        this._link.setAttribute("aria-label", label)
      } else {
        this._link.removeAttribute("aria-label")
      }
    }
    return
  }

  /*
   * Activation of the card link. A disabled (or loading) card does not
   * navigate; otherwise `mj-card-click` tells listeners, and the browser
   * follows the link.
   */
  _onCardClick(event) {
    if (this._link === null || event.composedPath()[0] !== this._link) {
      return
    }

    if (this._link.getAttribute("aria-disabled") === "true") {
      event.preventDefault()
      return
    }

    this.emit("mj-card-click", { originalEvent: event })
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

  /* The stretched link element while `href` is set, otherwise null. */
  get linkElement() {
    return this._link
  }
}
