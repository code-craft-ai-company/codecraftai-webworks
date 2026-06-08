/*
 * mjoverlay.js
 *
 * <mj-overlay> -- dimming/blocking backdrop primitive composed by dialog,
 * drawer, lightbox, and tour. Not intended for direct use by application
 * authors.
 *
 * Manages:
 *   - Visual backdrop (dim / block / transparent variants)
 *   - Reference-counted scroll lock on <body>
 *   - `inert` on background sibling elements
 *   - `mj-overlay-click` emission for light-dismiss
 */

import { MjElement } from "../core/mjelement.js";

/* Shared scroll-lock reference counter across all overlay instances. */
let _scrollLockCount = 0;

function acquireScrollLock() {
  _scrollLockCount = _scrollLockCount + 1;
  if (_scrollLockCount === 1) {
    document.body.style.overflow = "hidden";
  }
  return
}

function releaseScrollLock() {
  if (_scrollLockCount > 0) {
    _scrollLockCount = _scrollLockCount - 1;
  }
  if (_scrollLockCount === 0) {
    document.body.style.overflow = "";
  }
  return
}

const STYLES = `
:host {
  display: contents;
}

.backdrop {
  position: fixed;
  inset: 0;
  z-index: var(--mj-layer-overlay);
  background: var(--mj-overlay-scrim);
  opacity: 0;
  transition: opacity var(--mj-motion-medium) var(--mj-motion-ease);
  cursor: default;
}

:host([visible]) .backdrop {
  opacity: 1;
}

:host([variant="block"]) .backdrop {
  background: transparent;
}

:host([variant="transparent"]) .backdrop {
  background: transparent;
}

:host(:not([visible])) .backdrop {
  pointer-events: none;
  opacity: 0;
}

@media (prefers-reduced-motion: reduce) {
  .backdrop { transition: none; }
}

@media (forced-colors: active) {
  .backdrop { background: Canvas; opacity: 0.85; }
}
`;

export class MjOverlay extends MjElement {
  static tagName = "mj-overlay";
  static styles = STYLES;
  static watched = ["visible", "variant", "scroll-lock", "inert-target"];

  constructor() {
    super()
    this._inertEls = []
    this._lockHeld = false
    this._backdrop = null
  }

  render() {
    const markup = `<div class="backdrop" part="backdrop" role="presentation" aria-hidden="true"></div>`
    return markup
  }

  afterRender() {
    this._backdrop = this.$(".backdrop")
    this.listen(this._backdrop, "click", this._onBackdropClick.bind(this))
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "visible") {
      if (newValue !== null) {
        this._activate()
      } else {
        this._deactivate()
      }
    }
    return
  }

  onDisconnected() {
    this._forceDeactivate()
    return
  }

  _activate() {
    const doScrollLock = this.getAttribute("scroll-lock") !== "false";
    if (doScrollLock === true && this._lockHeld === false) {
      acquireScrollLock()
      this._lockHeld = true
    }
    this._applyInert()
    this.emit("mj-overlay-visible", {})
    return
  }

  _deactivate() {
    this._releaseInert()
    if (this._lockHeld === true) {
      releaseScrollLock()
      this._lockHeld = false
    }
    this.emit("mj-overlay-hidden", {})
    return
  }

  _forceDeactivate() {
    this._releaseInert()
    if (this._lockHeld === true) {
      releaseScrollLock()
      this._lockHeld = false
    }
    return
  }

  _applyInert() {
    const selector = this.getAttribute("inert-target")
    let targets = []

    if (selector !== null && selector.length > 0) {
      const nodes = document.querySelectorAll(selector)
      targets = Array.from(nodes)
    } else {
      const parent = this.parentElement
      if (parent !== null) {
        const siblings = Array.from(parent.children)
        targets = siblings.filter((el) => el !== this)
      }
    }

    for (let index = 0; index < targets.length; index = index + 1) {
      const el = targets[index]
      if (el.hasAttribute("inert") === false) {
        el.setAttribute("inert", "")
        this._inertEls.push(el)
      }
    }
    return
  }

  _releaseInert() {
    for (let index = 0; index < this._inertEls.length; index = index + 1) {
      const el = this._inertEls[index]
      el.removeAttribute("inert")
    }
    this._inertEls = []
    return
  }

  _onBackdropClick(event) {
    const proceed = this.emit("mj-overlay-click", { target: event.target }, { cancelable: true })
    if (proceed === false) {
      return
    }
    return
  }

  /* Scriptable API */

  get visible() {
    const value = this.hasAttribute("visible")
    return value
  }

  set visible(value) {
    this.reflectBoolean("visible", value === true)
    return
  }

  get lockCount() {
    return _scrollLockCount
  }

  get inertEls() {
    return this._inertEls.slice()
  }

  show() {
    this.visible = true
    return
  }

  hide() {
    this.visible = false
    return
  }
}
