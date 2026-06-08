/*
 * mjsharebutton.js
 *
 * <mj-share-button> -- invokes the platform Web Share API to share a URL,
 * title, and optional text. Falls back to an inline share menu containing
 * at minimum a "Copy link" action and optional consumer-configured targets
 * when the Web Share API is unavailable or when force-menu is set.
 */

import { MjElement } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";

const STYLES = `
:host {
  display: inline-block;
  vertical-align: middle;
  position: relative;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--mj-space-2);
  min-height: var(--mj-share-button-height, var(--mj-control-height-md));
  min-width: var(--mj-target-min);
  padding: 0 var(--mj-space-4);
  font: inherit;
  font-weight: var(--mj-font-weight-medium);
  line-height: 1;
  color: var(--mj-share-button-color, var(--mj-text));
  background: var(--mj-share-button-bg, var(--mj-surface));
  border: 1px solid var(--mj-share-button-border-color, var(--mj-border-strong));
  border-radius: var(--mj-share-button-border-radius, var(--mj-radius-md));
  cursor: pointer;
  user-select: none;
  transition: background var(--mj-motion-fast) var(--mj-motion-ease);
}
.btn:hover { background: var(--mj-bg-muted); }
.btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-share-button-focus-ring-color, var(--mj-focus-ring));
  outline-offset: var(--mj-focus-ring-offset);
}
.btn[aria-expanded="true"] { background: var(--mj-bg-muted); }

/* Variants */
:host([variant="primary"]) .btn  { color: var(--mj-text-on-accent); background: var(--mj-accent); border-color: var(--mj-accent); }
:host([variant="primary"]) .btn:hover { background: var(--mj-accent-hover); border-color: var(--mj-accent-hover); }
:host([variant="tertiary"]) .btn { background: transparent; border-color: transparent; }
:host([variant="tertiary"]) .btn:hover { background: var(--mj-bg-muted); }

/* Sizes */
:host([size="sm"]) .btn { min-height: var(--mj-control-height-sm); padding: 0 var(--mj-space-3); font-size: var(--mj-font-size-sm); }
:host([size="lg"]) .btn { min-height: var(--mj-control-height-lg); padding: 0 var(--mj-space-5); font-size: var(--mj-font-size-lg); }

:host([icon-only]) .btn { padding: 0; aspect-ratio: 1; }
:host([disabled]) .btn  { opacity: 0.55; cursor: not-allowed; }
:host([loading]) .btn   { opacity: 0.55; cursor: progress; }

.spinner {
  width: 1em; height: 1em;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: var(--mj-radius-circle);
  animation: mj-share-spin var(--mj-motion-slow) linear infinite;
}
:host(:not([loading])) .spinner { display: none; }
@keyframes mj-share-spin { to { transform: rotate(360deg); } }

/* Fallback menu */
.fallback-menu {
  position: absolute;
  inset-block-start: calc(100% + var(--mj-space-1));
  inset-inline-start: 0;
  min-width: var(--mj-share-button-menu-width, 12rem);
  background: var(--mj-surface-raised);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-md);
  box-shadow: var(--mj-elevation-2);
  z-index: var(--mj-layer-popover);
  list-style: none;
  margin: 0;
  padding: var(--mj-space-1) 0;
}
.fallback-menu[hidden] { display: none; }

.menu-item {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  width: 100%;
  padding: var(--mj-space-2) var(--mj-space-3);
  font: inherit;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
  background: none;
  border: none;
  cursor: pointer;
  text-align: start;
}
.menu-item:hover { background: var(--mj-bg-muted); }
.menu-item:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: -2px;
}

@media (prefers-reduced-motion: reduce) {
  .btn { transition: none; }
}
`;

export class MjShareButton extends MjElement {
  static tagName = "mj-share-button";
  static styles = STYLES;
  static watched = ["share-url", "share-title", "share-text", "force-menu", "variant", "size", "disabled", "loading", "icon-only", "label", "menu-label"];

  constructor() {
    super()
    this._button = null
    this._menu = null
    this._menuOpen = false
    this._shareTargets = []
    this._shareData = null
  }

  render() {
    const markup = `
      <button class="btn" part="button" type="button">
        <span class="spinner" part="spinner" aria-hidden="true"></span>
        <span class="icon" part="icon" aria-hidden="true"><slot name="icon"></slot></span>
        <span class="label" part="label"><slot></slot></span>
      </button>
      <ul class="fallback-menu" part="fallback-menu" role="menu" hidden>
        <li role="presentation">
          <button class="menu-item copy-link-item" part="menu-item" role="menuitem" type="button">Copy link</button>
        </li>
        <li role="presentation">
          <button class="menu-item email-item" part="menu-item" role="menuitem" type="button">Email</button>
        </li>
        <slot name="menu-item"></slot>
      </ul>
    `
    return markup
  }

  afterRender() {
    this._button = this.$(".btn")
    this._menu = this.$(".fallback-menu")
    this.listen(this._button, "click", this._onClick.bind(this))
    this.listen(this.$(".copy-link-item"), "click", this._onCopyLink.bind(this))
    this.listen(this.$(".email-item"), "click", this._onEmail.bind(this))
    this.listen(document, "keydown", this._onKeydown.bind(this))
    this.listen(document, "click", this._onDocClick.bind(this))
    this._syncAccessibility()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._button !== null) {
      this._syncAccessibility()
    }
    return
  }

  _syncAccessibility() {
    const disabled = this.hasAttribute("disabled")
    const loading = this.hasAttribute("loading")
    const inert = disabled === true || loading === true
    const iconOnly = this.hasAttribute("icon-only")
    const label = this.getAttribute("label") || "Share"
    const menuLabel = this.getAttribute("menu-label") || "Share via"

    this._button.disabled = inert
    this._button.setAttribute("aria-busy", loading === true ? "true" : "false")

    if (this.canShare === false) {
      this._button.setAttribute("aria-haspopup", "menu")
      this._button.setAttribute("aria-expanded", this._menuOpen === true ? "true" : "false")
    } else {
      this._button.removeAttribute("aria-haspopup")
      this._button.removeAttribute("aria-expanded")
    }

    if (iconOnly === true) {
      if (label.length > 0) {
        this._button.setAttribute("aria-label", label)
      } else {
        console.warn("<mj-share-button>: icon-only is set but no label attribute is provided.")
        this._button.setAttribute("aria-label", "")
      }
    } else {
      this._button.removeAttribute("aria-label")
    }

    if (this._menu !== null) {
      this._menu.setAttribute("aria-label", menuLabel)
    }
    return
  }

  _buildShareData() {
    if (this._shareData !== null) {
      return this._shareData
    }
    const shareUrl = this.getAttribute("share-url") || window.location.href
    const shareTitle = this.getAttribute("share-title") || document.title
    const shareText = this.getAttribute("share-text") || undefined
    const data = { url: shareUrl, title: shareTitle }
    if (shareText !== undefined) {
      data.text = shareText
    }
    return data
  }

  _onClick(event) {
    const blocked = this.hasAttribute("disabled") || this.hasAttribute("loading")
    if (blocked === true) {
      event.stopImmediatePropagation()
      event.preventDefault()
      return
    }

    if (this.canShare === true) {
      this._invokeNativeShare()
    } else {
      this._toggleMenu()
    }
    return
  }

  _invokeNativeShare() {
    const data = this._buildShareData()
    this.loading = true

    navigator.share(data).then(() => {
      this.loading = false
      this.emit("mj-share", { method: "native", data: data })
    }).catch((err) => {
      this.loading = false
      if (err.name === "AbortError") {
        return
      }
      this.emit("mj-share-error", { error: err })
    })
    return
  }

  _toggleMenu() {
    if (this._menuOpen === true) {
      this._closeMenu()
    } else {
      this._openMenu()
    }
    return
  }

  _openMenu() {
    this._menuOpen = true
    this._menu.hidden = false
    this._button.setAttribute("aria-expanded", "true")
    this.emit("mj-menu-open", {})
    return
  }

  _closeMenu() {
    this._menuOpen = false
    this._menu.hidden = true
    this._button.setAttribute("aria-expanded", "false")
    this.emit("mj-menu-close", {})
    return
  }

  _onCopyLink() {
    const shareUrl = this.getAttribute("share-url") || window.location.href
    const data = this._buildShareData()

    if (navigator.clipboard !== undefined && navigator.clipboard !== null) {
      navigator.clipboard.writeText(shareUrl).then(() => {
        this._closeMenu()
        this.emit("mj-share-select", { target: "copy-link", data: data })
        announce("Link copied", "polite")
      }).catch(() => {
        this._closeMenu()
      })
    } else {
      this._closeMenu()
    }
    return
  }

  _onEmail() {
    const data = this._buildShareData()
    const subject = encodeURIComponent(data.title || "")
    const body = encodeURIComponent(data.url || "")
    window.open(`mailto:?subject=${subject}&body=${body}`, "_self")
    this._closeMenu()
    this.emit("mj-share-select", { target: "email", data: data })
    return
  }

  _onKeydown(event) {
    if (event.key === "Escape" && this._menuOpen === true) {
      this._closeMenu()
      this._button.focus()
    }
    return
  }

  _onDocClick(event) {
    if (this._menuOpen === true && this.contains(event.target) === false) {
      this._closeMenu()
    }
    return
  }

  /* ----- scriptable API ----- */

  get canShare() {
    const forceMenu = this.hasAttribute("force-menu")
    if (forceMenu === true) {
      return false
    }
    const available = typeof navigator.share === "function"
    return available
  }

  get shareData() {
    return this._shareData
  }

  set shareData(value) {
    this._shareData = value
    return
  }

  get shareTargets() {
    return this._shareTargets
  }

  set shareTargets(value) {
    this._shareTargets = Array.isArray(value) === true ? value : []
    return
  }

  get loading() {
    const value = this.hasAttribute("loading")
    return value
  }

  set loading(value) {
    this.reflectBoolean("loading", value === true)
    return
  }

  get disabled() {
    const value = this.hasAttribute("disabled")
    return value
  }

  set disabled(value) {
    this.reflectBoolean("disabled", value === true)
    return
  }

  focus() {
    this._button.focus()
    return
  }
}
