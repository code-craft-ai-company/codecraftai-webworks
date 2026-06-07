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
import { t } from "../core/intl.js";

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
  border-radius: 2px;
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
    const href = this.getAttribute("href") || "";
    const disabled = this.hasAttribute("disabled");
    const externalLabel = t("mj.link.externalLabel") || "opens in a new tab";

    const markup = `
      <a class="anchor" part="anchor"${disabled === false ? ` href="${href}"` : ""}
         aria-disabled="${disabled === true ? "true" : "false"}">
        <span class="prefix" part="prefix"><slot name="prefix"></slot></span>
        <slot></slot>
        <span class="external-icon" part="external-icon" aria-hidden="true">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="none"
               stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M6 2H3a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V10"/>
            <polyline points="10 2 14 2 14 6"/>
            <line x1="14" y1="2" x2="7" y2="9"/>
          </svg>
        </span>
        <span class="external-label">, ${externalLabel}</span>
      </a>
    `;
    return markup
  }

  afterRender() {
    this._anchor = this.$(".anchor");
    this.listen(this._anchor, "click", this._onClick.bind(this));
    this._syncAnchor();
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._anchor === undefined || this._anchor === null) {
      return
    }
    this._syncAnchor();
    return
  }

  _syncAnchor() {
    const anchor = this._anchor;
    const disabled = this.hasAttribute("disabled");
    const external = this.hasAttribute("external");
    const href = this.getAttribute("href") || "";
    const targetAttr = this.getAttribute("target");
    const relAttr = this.getAttribute("rel") || "";
    const download = this.getAttribute("download");

    if (disabled === true) {
      anchor.removeAttribute("href");
      anchor.setAttribute("aria-disabled", "true");
    } else {
      anchor.setAttribute("href", href);
      anchor.setAttribute("aria-disabled", "false");
    }

    if (external === true) {
      const target = targetAttr !== null ? targetAttr : "_blank";
      anchor.setAttribute("target", target);
      let rel = relAttr;
      if (rel.indexOf("noopener") === -1) {
        rel = rel + (rel.length > 0 ? " " : "") + "noopener noreferrer";
      }
      anchor.setAttribute("rel", rel);
    } else {
      if (targetAttr !== null) {
        anchor.setAttribute("target", targetAttr);
      }
      if (relAttr.length > 0) {
        anchor.setAttribute("rel", relAttr);
      }
    }

    if (download !== null) {
      anchor.setAttribute("download", download);
    } else {
      anchor.removeAttribute("download");
    }
    return
  }

  _onClick(event) {
    const disabled = this.hasAttribute("disabled");
    if (disabled === true) {
      event.preventDefault();
      event.stopImmediatePropagation();
      return
    }

    const href = this.getAttribute("href") || "";
    const external = this.hasAttribute("external");
    const proceed = this.emit("mj-link-click", {
      href: href,
      external: external,
      originalEvent: event
    }, { cancelable: true });

    if (proceed === false) {
      event.preventDefault();
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
    this.reflectBoolean("disabled", value === true);
    return
  }
}
