/*
 * mjskiplink.js
 *
 * <mj-skip-link> -- visually hidden anchor that becomes visible on focus.
 * Satisfies WCAG 2.4.1 Bypass Blocks. Must be the first focusable element.
 * On activation moves focus to the target landmark element.
 *
 * WAI-ARIA: native <a> provides link role. No ARIA landmark on host.
 */

import { MjElement } from "../core/mjelement.js";
import { t } from "../core/intl.js";

const STYLES = `
:host { display: block; }

.anchor {
  position: absolute;
  inset-inline-start: -9999px;
  top: var(--mj-skip-link-offset-top, var(--mj-space-3));
  z-index: var(--mj-skip-link-z-index, var(--mj-layer-toast));
  display: inline-flex;
  align-items: center;
  padding: var(--mj-skip-link-padding, var(--mj-space-3) var(--mj-space-5));
  background: var(--mj-skip-link-bg, var(--mj-accent));
  color: var(--mj-skip-link-color, var(--mj-text-on-accent));
  font: inherit;
  font-weight: var(--mj-font-weight-medium);
  text-decoration: none;
  border-radius: var(--mj-skip-link-radius, var(--mj-radius-sm));
  white-space: nowrap;
  transition: none;
}
.anchor:focus-visible {
  inset-inline-start: var(--mj-skip-link-offset-start, var(--mj-space-3));
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
:host([variant="inline"]) .anchor {
  position: static;
}
@media (prefers-reduced-motion: reduce) {
  .anchor { transition: none; }
}
@media (forced-colors: active) {
  .anchor {
    background: ButtonFace;
    color: ButtonText;
    border: 1px solid ButtonText;
  }
}
`;

export class MjSkipLink extends MjElement {
  static tagName = "mj-skip-link";
  static styles = STYLES;
  static watched = ["target", "label", "variant"];

  render() {
    const target = this.getAttribute("target") || "#main";
    const label = this.getAttribute("label") || t("mj.skipLink.label") || "Skip to main content";
    const variant = this.getAttribute("variant") || "default";

    const markup = `
      <a class="anchor" part="anchor" href="${target}">
        <span class="label" part="label">
          <slot>${label}</slot>
        </span>
      </a>
    `;
    return markup
  }

  afterRender() {
    this._anchor = this.$(".anchor");
    this.listen(this._anchor, "click", this._onActivate.bind(this));
    this.listen(this._anchor, "keydown", this._onKeydown.bind(this));
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
    const target = this.getAttribute("target") || "#main";
    const label = this.getAttribute("label") || t("mj.skipLink.label") || "Skip to main content";
    this._anchor.setAttribute("href", target);
    return
  }

  _onActivate(event) {
    const target = this.getAttribute("target") || "#main";
    const proceed = this.emit("mj-skip-link-activate", {
      target: target,
      originalEvent: event
    }, { cancelable: true });

    if (proceed === false) {
      event.preventDefault();
      return
    }

    const targetEl = document.querySelector(target);
    if (targetEl === null) {
      console.error(`<mj-skip-link>: target "${target}" not found in DOM`);
      return
    }

    event.preventDefault();

    const isNativelyFocusable = typeof targetEl.focus === "function" &&
      targetEl.getAttribute("tabindex") !== null ||
      ["a", "button", "input", "select", "textarea"].indexOf(targetEl.tagName.toLowerCase()) !== -1;

    if (isNativelyFocusable === false) {
      targetEl.tabIndex = -1;
      const onBlur = function() {
        targetEl.removeAttribute("tabindex");
        targetEl.removeEventListener("blur", onBlur);
      };
      targetEl.addEventListener("blur", onBlur);
    }

    targetEl.focus();
    return
  }

  _onKeydown(event) {
    if (event.key === "Enter") {
      this._onActivate(event);
    }
    return
  }

  get anchorElement() {
    return this._anchor || null
  }
}
