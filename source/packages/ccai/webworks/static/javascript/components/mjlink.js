/*
 * mjlink.js
 *
 * <mj-link> -- styled navigation hyperlink built on a real <a> element.
 * Supports default, subtle, and standalone variants, external-link handling,
 * disabled state, and optional visited-cue suppression.
 *
 * WAI-ARIA: native <a> provides link role. No explicit role needed.
 */

import { MjElement } from "../core/mjelement.js";
import { html, raw, safeUrl } from "../core/html.js";
import { t } from "../core/intl.js";

/* Box-with-arrow icon shown after an external link (static markup). */
const EXTERNAL_ICON = raw(
  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="none" ' +
  'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">' +
  '<path d="M6 2H3a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V10"/>' +
  '<polyline points="10 2 14 2 14 6"/>' +
  '<line x1="14" y1="2" x2="7" y2="9"/>' +
  '</svg>'
);

const STYLES = `
:host {
  display: inline;
}
:host([variant="standalone"]) {
  display: block;
}

.anchor {
  color: var(--mj-link-color, var(--mj-accent));
  text-decoration: underline;
  text-underline-offset: var(--mj-link-underline-offset, 2px);
  cursor: pointer;
  font: inherit;
  transition: color var(--mj-motion-fast) var(--mj-motion-ease);
}
.anchor:hover {
  color: var(--mj-link-color-hover, var(--mj-accent-hover));
}
:host([visited-cue]:not([visited-cue="false"])) .anchor:visited {
  color: var(--mj-link-color-visited, var(--mj-text-muted));
}
.anchor:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
  border-radius: var(--mj-radius-sm);
}
:host([variant="subtle"]) .anchor {
  text-decoration: none;
}
:host([variant="subtle"]) .anchor:hover,
:host([variant="subtle"]) .anchor:focus-visible {
  text-decoration: underline;
}
:host([variant="standalone"]) .anchor {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  font-weight: var(--mj-font-weight-medium);
  text-decoration: none;
  min-height: var(--mj-target-min);
}
:host([variant="standalone"]) .anchor:hover {
  text-decoration: underline;
}
:host([disabled]) .anchor {
  color: var(--mj-link-color-disabled, var(--mj-text-muted));
  cursor: not-allowed;
  pointer-events: none;
}

.prefix {
  display: inline-flex;
  align-items: center;
}
/* An empty prefix takes no room (no flex gap before the text when standalone). */
.prefix[hidden] { display: none; }
.external-icon {
  display: inline-flex;
  width: var(--mj-link-external-icon-size, 0.875em);
  height: var(--mj-link-external-icon-size, 0.875em);
  margin-inline-start: 0.25em;
  vertical-align: middle;
}
:host(:not([external])) .external-icon { display: none; }
:host(:not([external])) .external-label { display: none; }

.external-label {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  clip-path: inset(50%);
  white-space: nowrap;
}
`;

export class MjLink extends MjElement {
  static tagName = "mj-link";
  static styles = STYLES;
  static watched = ["href", "target", "rel", "download", "external", "variant", "disabled", "visited-cue"];

  render() {
    /*
     * The anchor is rendered without any author-supplied value: href, target,
     * rel and download are applied by `_syncAnchor` through setAttribute, so
     * no attribute text is ever parsed as markup.
     *
     * The children of the anchor are written without any whitespace between
     * them: the host is an inline element in running text, so a line break
     * here would render as an underlined space before or after the link text.
     */
    const prefix = html`<span class="prefix" part="prefix"><slot name="prefix"></slot></span>`
    const externalIcon = html`<span class="external-icon" part="external-icon" aria-hidden="true">${EXTERNAL_ICON}</span>`
    const externalLabel = html`<span class="external-label">, ${t("mj.link.externalLabel")}</span>`

    const markup = html`<a class="anchor" part="anchor">${prefix}<slot></slot>${externalIcon}${externalLabel}</a>`
    return markup
  }

  afterRender() {
    this._anchor = this.$(".anchor")
    this._prefix = this.$(".prefix")
    this._prefixSlot = this.$("slot[name='prefix']")
    this.listen(this._anchor, "click", this._onClick.bind(this))
    this.listen(this._prefixSlot, "slotchange", this._syncPrefix.bind(this))
    this._syncAnchor()
    this._syncPrefix()
    return
  }

  /* Hide the prefix wrapper while nothing is slotted into it. */
  _syncPrefix() {
    const hasPrefix = this._prefixSlot.assignedNodes({ flatten: true }).length > 0
    this._prefix.hidden = hasPrefix === false
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._anchor === undefined || this._anchor === null) {
      return
    }
    this._syncAnchor()
    return
  }

  /* Set an attribute on the inner anchor, or remove it when the value is empty. */
  _setOrRemove(name, value) {
    if (value !== null && value !== undefined && value.length > 0) {
      this._anchor.setAttribute(name, value)
    } else {
      this._anchor.removeAttribute(name)
    }
    return
  }

  /*
   * Bring the inner anchor in line with the host attributes. Every branch
   * either sets or removes its attribute, so a value taken away from the host
   * never lingers on the anchor.
   */
  _syncAnchor() {
    const anchor = this._anchor
    const disabled = this.hasAttribute("disabled")
    const external = this.hasAttribute("external")
    const hrefAttr = this.getAttribute("href")
    const targetAttr = this.getAttribute("target")
    const relAttr = this.getAttribute("rel")
    const download = this.getAttribute("download")

    if (disabled === true) {
      /*
       * A disabled link has no destination but is still announced as a link
       * and stays in the tab order (spec sec.13).
       */
      anchor.removeAttribute("href")
      anchor.setAttribute("role", "link")
      anchor.setAttribute("tabindex", "0")
      anchor.setAttribute("aria-disabled", "true")
    } else {
      anchor.removeAttribute("role")
      anchor.removeAttribute("tabindex")
      anchor.setAttribute("aria-disabled", "false")

      /* Without a host href the anchor is an inert placeholder, not a link to this page. */
      if (hrefAttr !== null) {
        anchor.setAttribute("href", safeUrl(hrefAttr))
      } else {
        anchor.removeAttribute("href")
      }
    }

    let target = targetAttr !== null ? targetAttr : ""
    if (external === true && target.length === 0) {
      target = "_blank"
    }

    /* A new browsing context must never receive a reference to this window. */
    let rel = relAttr !== null ? relAttr.trim() : ""
    const relTokens = rel.toLowerCase().split(/\s+/)
    const opensNewContext = target.toLowerCase() === "_blank"
    if (external === true || opensNewContext === true) {
      if (relTokens.indexOf("noopener") === -1) {
        rel = rel + (rel.length > 0 ? " " : "") + "noopener"
      }
    }
    if (external === true && relTokens.indexOf("noreferrer") === -1) {
      rel = rel + (rel.length > 0 ? " " : "") + "noreferrer"
    }

    this._setOrRemove("target", target)
    this._setOrRemove("rel", rel)

    if (download !== null) {
      anchor.setAttribute("download", download)
    } else {
      anchor.removeAttribute("download")
    }
    return
  }

  _onClick(event) {
    const disabled = this.hasAttribute("disabled")
    if (disabled === true) {
      event.preventDefault()
      event.stopImmediatePropagation()
      return
    }

    const href = this.getAttribute("href") || ""
    const external = this.hasAttribute("external")
    const proceed = this.emit("mj-link-click", {
      href: href,
      external: external,
      originalEvent: event
    }, { cancelable: true })

    if (proceed === false) {
      event.preventDefault()
    }
    return
  }

  get anchorElement() {
    return this._anchor || null
  }

  get disabled() {
    return this.hasAttribute("disabled")
  }

  set disabled(value) {
    this.reflectBoolean("disabled", value === true)
    return
  }
}
