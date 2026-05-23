/*
 * mjsidenav.js
 *
 * <mj-side-nav> -- side navigation panel.
 * Supports static, collapsible, and overlay-drawer modes.
 * Renders as a <nav aria-label> landmark with roving tabindex for items.
 *
 * WAI-ARIA: nav landmark; aria-expanded for groups; aria-current="page" on active item.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { RovingTabindex, trapFocus } from "../core/focustrap.js";
import { t } from "../core/intl.js";

const STYLES = `
:host {
  display: block;
  position: relative;
}
:host([mode="static"]) .root {
  position: relative;
  width: var(--mj-side-nav-width, 240px);
  background: var(--mj-side-nav-bg, var(--mj-surface));
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}
:host([mode="collapsible"]) .root {
  position: relative;
  width: var(--mj-side-nav-width, 240px);
  background: var(--mj-side-nav-bg, var(--mj-surface));
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  transition: width var(--mj-side-nav-transition-duration, var(--mj-motion-medium)) var(--mj-motion-ease);
}
:host([mode="collapsible"]:not([open])) .root { width: 0; overflow: hidden; }
:host([mode="overlay-drawer"]) .root {
  position: fixed;
  inset-block: 0;
  inset-inline-start: 0;
  width: var(--mj-side-nav-width, 240px);
  background: var(--mj-side-nav-bg, var(--mj-surface));
  box-shadow: var(--mj-elevation-3);
  z-index: var(--mj-side-nav-z-index, var(--mj-layer-modal));
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  transform: translateX(-100%);
  transition: transform var(--mj-side-nav-transition-duration, var(--mj-motion-medium)) var(--mj-motion-ease);
}
:host([mode="overlay-drawer"][open]) .root { transform: translateX(0); }
:host([edge="end"][mode="overlay-drawer"]) .root {
  inset-inline-start: auto;
  inset-inline-end: 0;
  transform: translateX(100%);
}
:host([edge="end"][mode="overlay-drawer"][open]) .root { transform: translateX(0); }

.backdrop {
  display: none;
  position: fixed;
  inset: 0;
  background: var(--mj-overlay-scrim);
  z-index: calc(var(--mj-side-nav-z-index, var(--mj-layer-modal)) - 1);
}
:host([mode="overlay-drawer"][open]) .backdrop { display: block; }

.header-area { padding: var(--mj-space-4); flex-shrink: 0; }
.nav-list { list-style: none; margin: 0; padding: var(--mj-space-2) 0; flex: 1; overflow-y: auto; }
.footer-area { padding: var(--mj-space-4); border-top: 1px solid var(--mj-border); flex-shrink: 0; }

.toggle-btn {
  display: flex; align-items: center; justify-content: flex-end;
  width: 100%; padding: var(--mj-space-2) var(--mj-space-4);
  background: none; border: none; cursor: pointer;
  color: var(--mj-text-muted); font: inherit;
  border-top: 1px solid var(--mj-border);
}
:host([mode="static"]) .toggle-btn { display: none; }
:host([mode="overlay-drawer"]) .toggle-btn { display: none; }
.toggle-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

::slotted([aria-current="page"]) {
  color: var(--mj-accent);
  background: var(--mj-bg-muted);
  font-weight: var(--mj-font-weight-medium);
}
::slotted(a), ::slotted(button) {
  display: flex; align-items: center;
  width: 100%;
  padding: 0 var(--mj-space-4);
  min-height: var(--mj-side-nav-item-height, 44px);
  text-decoration: none;
  color: var(--mj-text);
  background: none; border: none; cursor: pointer;
  font: inherit; font-size: var(--mj-font-size-sm);
  border-radius: var(--mj-radius-md);
  transition: background var(--mj-motion-fast) var(--mj-motion-ease);
}
::slotted(a:hover), ::slotted(button:hover) { background: var(--mj-bg-muted); }
`;

export class MjSideNav extends MjElement {
  static tagName = "mj-side-nav";
  static styles = STYLES;
  static watched = ["mode", "open", "edge", "nav-label", "persist-state", "persist-key"];

  constructor() {
    super();
    this._disposeTrap = null;
  }

  render() {
    const navLabel = this.getAttribute("nav-label") || t("mj.sideNav.navLabel") || "Navigation";
    const mode = this.getAttribute("mode") || "static";
    const collapseLabel = t("mj.sideNav.collapse") || "Collapse navigation";

    const markup = `
      <div class="backdrop" part="backdrop" aria-hidden="true"></div>
      <nav class="root" part="root" aria-label="${navLabel}">
        <div class="header-area" part="header"><slot name="header"></slot></div>
        <ul class="nav-list" part="nav-list" role="list">
          <slot></slot>
        </ul>
        ${mode === "collapsible" ? `
          <button class="toggle-btn" part="toggle" aria-label="${collapseLabel}">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
              <path d="M5 2L11 8L5 14" stroke="currentColor" stroke-width="1.5"
                    fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        ` : ""}
        <div class="footer-area" part="footer"><slot name="footer"></slot></div>
      </nav>
    `;
    return markup
  }

  afterRender() {
    this._nav = this.$(".root");
    this._backdrop = this.$(".backdrop");
    this._toggleBtn = this.$(".toggle-btn");

    this.listen(this._backdrop, "click", this._closeDrawer.bind(this));
    this.listen(this, "keydown", this._onKeydown.bind(this));

    if (this._toggleBtn !== null) {
      this.listen(this._toggleBtn, "click", this._onToggleClick.bind(this));
    }

    this._restorePersistedState();
    this._syncOpen();
    return
  }

  onConnected() {
    this._setupItems();
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "open" && this._nav !== undefined) {
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

  _setupItems() {
    const slot = this.shadowRoot.querySelector("slot:not([name])");
    if (slot === null) {
      return
    }
    const items = slot.assignedElements({ flatten: true });
    if (items.length > 0) {
      this._roving = new RovingTabindex({ items: items, orientation: "vertical", wrap: true });
      this.onTeardown(this._roving.attach(this._nav));
    }
    return
  }

  _syncOpen() {
    const open = this.hasAttribute("open");
    const mode = this.getAttribute("mode") || "static";

    if (mode === "overlay-drawer") {
      if (open === true) {
        this._disposeTrap = trapFocus(this._nav);
      } else {
        if (this._disposeTrap !== null) {
          this._disposeTrap();
          this._disposeTrap = null;
        }
      }
    }

    if (mode === "collapsible") {
      const persistState = this.getAttribute("persist-state") !== "false";
      if (persistState === true) {
        const key = this.getAttribute("persist-key") || "mj-side-nav";
        try {
          localStorage.setItem(key, open === true ? "open" : "closed");
        } catch (_err) {
          // storage unavailable
        }
      }
    }
    return
  }

  _restorePersistedState() {
    const mode = this.getAttribute("mode") || "static";
    if (mode !== "collapsible") {
      return
    }
    const persistState = this.getAttribute("persist-state") !== "false";
    if (persistState === false) {
      return
    }
    const key = this.getAttribute("persist-key") || "mj-side-nav";
    let stored = null;
    try {
      stored = localStorage.getItem(key);
    } catch (_err) {
      // storage unavailable
    }
    if (stored === "open") {
      this.setAttribute("open", "");
    } else if (stored === "closed") {
      this.removeAttribute("open");
    }
    return
  }

  _closeDrawer() {
    const proceed = this.emit("mj-side-nav-close", { mode: this.getAttribute("mode") || "static" }, { cancelable: true });
    if (proceed === true) {
      this.removeAttribute("open");
    }
    return
  }

  _onToggleClick() {
    const open = this.hasAttribute("open");
    if (open === true) {
      this._closeDrawer();
    } else {
      const proceed = this.emit("mj-side-nav-open", { mode: this.getAttribute("mode") || "static" }, { cancelable: true });
      if (proceed === true) {
        this.setAttribute("open", "");
      }
    }
    return
  }

  _onKeydown(event) {
    if (event.key === "Escape") {
      const mode = this.getAttribute("mode") || "static";
      if (mode === "overlay-drawer" && this.hasAttribute("open") === true) {
        this._closeDrawer();
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

  get activeItem() {
    const found = this.querySelector("[aria-current='page']");
    return found
  }

  get items() {
    const slot = this.shadowRoot.querySelector("slot:not([name])");
    if (slot === null) {
      return []
    }
    const assigned = slot.assignedElements({ flatten: true });
    return assigned
  }
}
