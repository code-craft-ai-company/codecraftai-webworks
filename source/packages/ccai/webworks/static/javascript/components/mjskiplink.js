/*
 * mjskiplink.js
 *
 * <mj-skip-link> -- visually hidden anchor that becomes visible on focus.
 * Satisfies WCAG 2.4.1 Bypass Blocks. Must be the first focusable element.
 * On activation moves focus to the target landmark element.
 *
 * `target` is the id of the destination, written as "#main" or "main"; a CSS
 * selector is accepted as well. The anchor always carries a fragment href, so
 * it can never navigate to another document.
 *
 * WAI-ARIA: native <a> provides link role. No ARIA landmark on host.
 */

import { MjElement } from "../core/mjelement.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";

const DEFAULT_TARGET = "#main";

/* A target written as a bare id ("main-content") rather than a selector ("#main-content"). */
const BARE_ID_PATTERN = /^[A-Za-z0-9_-]+$/;

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
    /* href and the label text are applied by `_syncAnchor`, never parsed as markup. */
    const markup = html`
      <a class="anchor" part="anchor" href="#">
        <span class="label" part="label">
          <slot></slot>
        </span>
      </a>
    `
    return markup
  }

  afterRender() {
    this._anchor = this.$(".anchor")
    this._labelSlot = this.$("slot")

    /* Enter on the anchor produces a click, so one listener covers keyboard and pointer. */
    this.listen(this._anchor, "click", this._onActivate.bind(this))
    this._syncAnchor()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._anchor === undefined || this._anchor === null) {
      return
    }
    this._syncAnchor()
    return
  }

  _target() {
    let target = this.getAttribute("target")
    if (target === null || target.trim().length === 0) {
      target = DEFAULT_TARGET
    }
    return target.trim()
  }

  /*
   * Find the destination element: `#id` and a bare id are looked up by id;
   * anything else (or an id that does not exist) is tried as a CSS selector.
   * Returns null when nothing matches or the selector is invalid.
   */
  _resolveTarget() {
    const target = this._target()
    let element = null

    if (target.charAt(0) === "#") {
      element = document.getElementById(target.slice(1))
    } else if (BARE_ID_PATTERN.test(target) === true) {
      element = document.getElementById(target)
    }

    if (element === null) {
      try {
        element = document.querySelector(target)
      } catch (error) {
        element = null
      }
    }
    return element
  }

  /* The fragment the anchor points at: "#id" for id targets, else the matched element's id. */
  _fragmentHref() {
    const target = this._target()
    let href = "#"

    if (target.charAt(0) === "#") {
      href = target
    } else if (BARE_ID_PATTERN.test(target) === true) {
      href = `#${target}`
    } else {
      const element = this._resolveTarget()
      if (element !== null && element.id !== "") {
        href = `#${element.id}`
      }
    }
    return href
  }

  _syncAnchor() {
    let label = this.getAttribute("label")
    if (label === null || label.length === 0) {
      label = t("mj.skipLink.label")
    }

    /* The label is the fallback content of the slot; slotted content replaces it. */
    this._labelSlot.textContent = label
    this._anchor.setAttribute("href", this._fragmentHref())
    return
  }

  _onActivate(event) {
    const target = this._target()
    const proceed = this.emit("mj-skip-link-activate", {
      target: target,
      originalEvent: event
    }, { cancelable: true })

    /*
     * The component moves focus itself. The native jump is always suppressed:
     * a canceled event means the application handles it, and an unresolved
     * target must not send the browser anywhere.
     */
    event.preventDefault()

    if (proceed === false) {
      return
    }

    const targetEl = this._resolveTarget()
    if (targetEl === null) {
      console.error(`<mj-skip-link>: target "${target}" not found in DOM`)
      return
    }

    const isFocusable = targetEl.hasAttribute("tabindex") === true || targetEl.tabIndex >= 0

    if (isFocusable === false) {
      targetEl.tabIndex = -1
      const onBlur = function() {
        targetEl.removeAttribute("tabindex")
        targetEl.removeEventListener("blur", onBlur)
      }
      targetEl.addEventListener("blur", onBlur)
    }

    targetEl.focus()
    return
  }

  get anchorElement() {
    return this._anchor || null
  }
}
