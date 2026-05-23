/*
 * mjappbar.js
 *
 * <mj-app-bar> -- top-of-page navigation and branding bar.
 * Renders a <header role="banner"> landmark with brand, nav, and actions slots.
 * Handles responsive collapse to a mobile drawer on narrow viewports.
 *
 * WAI-ARIA: header role="banner"; nav aria-label; toggle aria-expanded/aria-controls.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { trapFocus } from "../core/focustrap.js";
import { t } from "../core/intl.js";

const STYLES = `
:host {
  display: block;
  position: relative;
  z-index: var(--mj-layer-sticky);
}
:host([sticky]) { position: sticky; top: 0; }

.root {
  display: flex;
  align-items: center;
  height: var(--mj-app-bar-height, 56px);
  padding-inline: var(--mj-app-bar-padding-inline, var(--mj-space-5));
  background: var(--mj-app-bar-bg, var(--mj-surface));
  box-shadow: var(--mj-app-bar-elevation, var(--mj-elevation-2));
  gap: var(--mj-space-4);
}
:host([transparent]) .root { background: transparent; box-shadow: none; }
:host([transparent][scrolled]) .root {
  background: var(--mj-app-bar-bg-scrolled, var(--mj-surface));
  box-shadow: var(--mj-app-bar-elevation, var(--mj-elevation-2));
  transition: background var(--mj-motion-medium) var(--mj-motion-ease),
              box-shadow var(--mj-motion-medium) var(--mj-motion-ease);
}

.brand { display: flex; align-items: center; flex-shrink: 0; }
.nav { display: flex; align-items: center; flex: 1; gap: var(--mj-space-4); }
.actions { display: flex; align-items: center; gap: var(--mj-space-2); margin-inline-start: auto; }

.toggle {
  display: none;
  align-items: center;
  justify-content: center;
  width: 40px; height: 40px;
  background: none; border: none; cursor: pointer;
  border-radius: var(--mj-radius-md);
  color: var(--mj-text);
}
.toggle:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.drawer {
  position: fixed;
  inset-block: 0;
  inset-inline-start: 0;
  width: min(280px, 85vw);
  background: var(--mj-surface);
  box-shadow: var(--mj-elevation-3);
  z-index: var(--mj-layer-modal);
  transform: translateX(-100%);
  transition: transform var(--mj-motion-medium) var(--mj-motion-ease);
  overflow-y: auto;
  padding: var(--mj-space-5);
}
:host([open]) .drawer { transform: translateX(0); }

.backdrop {
  display: none;
  position: fixed;
  inset: 0;
  background: var(--mj-overlay-scrim);
  z-index: calc(var(--mj-layer-modal) - 1);
}
:host([open]) .backdrop { display: block; }

@media (max-width: 767px) {
  .nav { display: none; }
  .toggle { display: flex; }
}
@media (min-width: 768px) {
  .drawer { display: none; }
  .backdrop { display: none !important; }
}
`;

export class MjAppBar extends MjElement {
  static tagName = "mj-app-bar";
  static styles = STYLES;
  static watched = ["open", "sticky", "transparent", "scrolled", "nav-label", "scroll-threshold"];

  constructor() {
    super();
    this._drawerId = nextId("mj-appbar-drawer");
    this._disposeTrap = null;
  }

  render() {
    const navLabel = this.getAttribute("nav-label") || t("mj.appBar.navLabel") || "Main";
    const openLabel = t("mj.appBar.openNav") || "Open navigation";

    const markup = `
      <div class="root" part="root">
        <div class="brand" part="brand"><slot name="brand"></slot></div>
        <nav class="nav" part="nav" aria-label="${navLabel}">
          <slot name="navigation"></slot>
        </nav>
        <div class="actions" part="actions"><slot name="actions"></slot></div>
        <button class="toggle" part="toggle"
          aria-expanded="false"
          aria-controls="${this._drawerId}"
          aria-label="${openLabel}">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <rect y="3" width="20" height="2" rx="1"/>
            <rect y="9" width="20" height="2" rx="1"/>
            <rect y="15" width="20" height="2" rx="1"/>
          </svg>
        </button>
      </div>
      <div class="backdrop" part="backdrop" aria-hidden="true"></div>
      <div class="drawer" part="drawer" id="${this._drawerId}">
        <slot name="mobile-navigation"><slot name="navigation"></slot></slot>
      </div>
    `;
    return markup
  }

  afterRender() {
    this._toggle = this.$(".toggle");
    this._drawer = this.$(".drawer");
    this._backdrop = this.$(".backdrop");

    this.listen(this._toggle, "click", this._onToggleClick.bind(this));
    this.listen(this._backdrop, "click", this._onBackdropClick.bind(this));
    this.listen(this, "keydown", this._onKeydown.bind(this));

    this._setupScrollSpy();
    this._syncOpen();
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "open" && this._toggle !== undefined) {
      this._syncOpen();
    }
    return
  }

  onDisconnected() {
    if (this._disposeTrap !== null) {
      this._disposeTrap();
      this._disposeTrap = null;
    }
    return
  }

  _syncOpen() {
    const open = this.hasAttribute("open");
    this._toggle.setAttribute("aria-expanded", open === true ? "true" : "false");

    const openLabel = t("mj.appBar.openNav") || "Open navigation";
    const closeLabel = t("mj.appBar.closeNav") || "Close navigation";
    this._toggle.setAttribute("aria-label", open === true ? closeLabel : openLabel);

    if (open === true) {
      this._disposeTrap = trapFocus(this._drawer);
    } else {
      if (this._disposeTrap !== null) {
        this._disposeTrap();
        this._disposeTrap = null;
        this._toggle.focus();
      }
    }
    return
  }

  _setupScrollSpy() {
    const threshold = parseInt(this.getAttribute("scroll-threshold") || "16", 10);
    const onScroll = () => {
      const wasScrolled = this.hasAttribute("scrolled");
      const isScrolled = window.scrollY > threshold;
      if (isScrolled !== wasScrolled) {
        this.reflectBoolean("scrolled", isScrolled);
        this.emit("mj-app-bar-scroll", { scrolled: isScrolled, scrollY: window.scrollY });
      }
    };
    this.listen(window, "scroll", onScroll, { passive: true });
    return
  }

  _onToggleClick() {
    const open = this.hasAttribute("open");
    if (open === false) {
      const proceed = this.emit("mj-app-bar-open", {}, { cancelable: true });
      if (proceed === true) {
        this.setAttribute("open", "");
      }
    } else {
      const proceed = this.emit("mj-app-bar-close", {}, { cancelable: true });
      if (proceed === true) {
        this.removeAttribute("open");
      }
    }
    return
  }

  _onBackdropClick() {
    const proceed = this.emit("mj-app-bar-close", {}, { cancelable: true });
    if (proceed === true) {
      this.removeAttribute("open");
    }
    return
  }

  _onKeydown(event) {
    if (event.key === "Escape" && this.hasAttribute("open") === true) {
      const proceed = this.emit("mj-app-bar-close", {}, { cancelable: true });
      if (proceed === true) {
        this.removeAttribute("open");
      }
    }
    return
  }

  get open() {
    return this.hasAttribute("open")
  }

  set open(value) {
    this.reflectBoolean("open", value === true);
    return
  }

  get scrolled() {
    return this.hasAttribute("scrolled")
  }

  get drawerElement() {
    return this._drawer || null
  }
}
