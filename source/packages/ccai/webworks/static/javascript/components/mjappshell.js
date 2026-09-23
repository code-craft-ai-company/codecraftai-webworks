/*
 * mjappshell.js
 *
 * <mj-app-shell> -- outermost layout frame composing AppBar, SideNav, main
 * content area, inspector panel, and StatusBar into correct landmark structure.
 * Supports panel persistence, responsive collapse, and keyboard panel cycling.
 *
 * Landmarks: the shell wraps its regions in landmarks only where the slotted
 * content does not already provide one, so a page never exposes nested or
 * duplicate landmarks. The main region is a `main` landmark unless the
 * slotted content is itself a <main> (or role="main"); the nav region is a
 * `navigation` landmark unless the slotted content is a navigation landmark
 * (<nav>, role="navigation", <mj-side-nav>, <mj-tree-nav>). The dock,
 * inspector, and status bar are not rendered while their slots are empty.
 *
 * Responsive behavior: below the `--mj-shell-breakpoint-nav` width (default
 * 768px) the nav becomes an overlay drawer. Entering overlay mode closes the
 * drawer (and leaving it restores the wide-layout open state), so a narrow
 * viewport never loads with the drawer covering the content. While the
 * overlay drawer is open, focus is moved into it and trapped there, the rest
 * of the shell is inert, and Escape closes it wherever focus is.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { trapFocus } from "../core/focustrap.js";
import { announce } from "../core/announcer.js";
import { t } from "../core/intl.js";

const DEFAULT_NAV_BREAKPOINT_PX = 768;

/* Slotted elements that render their own navigation landmark. */
const NAVIGATION_LANDMARK_SELECTOR = "nav, [role='navigation'], mj-side-nav, mj-tree-nav";
/* Slotted elements that are themselves the main landmark. */
const MAIN_LANDMARK_SELECTOR = "main, [role='main']";

const STYLES = `
:host {
  display: grid;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: var(--mj-shell-bg, var(--mj-bg));
  grid-template-rows: auto 1fr auto;
  grid-template-columns: auto auto 1fr auto;
  grid-template-areas:
    "appbar  appbar   appbar    appbar"
    "dock    nav      main      inspector"
    "statusbar statusbar statusbar statusbar";
  position: relative;
}

:host([nav-mode="overlay"]) {
  grid-template-columns: auto 0 1fr auto;
}

[hidden] { display: none !important; }

.app-bar {
  grid-area: appbar;
  z-index: var(--mj-layer-sticky);
}

.dock {
  grid-area: dock;
  width: var(--mj-shell-dock-width, 48px);
  overflow: hidden;
  border-inline-end: 1px solid var(--mj-border);
  background: var(--mj-surface);
}

.side-nav {
  grid-area: nav;
  width: var(--mj-shell-nav-width, 240px);
  overflow: hidden auto;
  border-inline-end: 1px solid var(--mj-border);
  background: var(--mj-surface);
  transition: width var(--mj-motion-medium) var(--mj-motion-ease);
  position: relative;
}

:host([nav-mode="overlay"]) .side-nav {
  position: fixed;
  inset-block: 0;
  inset-inline-start: 0;
  z-index: var(--mj-layer-overlay);
  width: var(--mj-shell-nav-width, 240px);
  transform: translateX(-100%);
  visibility: hidden;
  transition: transform var(--mj-motion-medium) var(--mj-motion-ease),
              visibility 0s linear var(--mj-motion-medium);
  box-shadow: var(--mj-elevation-3);
}

:host([nav-mode="overlay"][nav-open]) .side-nav {
  transform: translateX(0);
  visibility: visible;
  transition: transform var(--mj-motion-medium) var(--mj-motion-ease);
}

:host(:not([nav-open])) .side-nav {
  width: 0;
}

:host([nav-mode="collapsible"]:not([nav-open])) .side-nav {
  width: var(--mj-shell-dock-width, 48px);
}

.main-area {
  grid-area: main;
  overflow: auto;
  background: var(--mj-bg);
  min-width: 0;
  min-height: 0;
}

.inspector {
  grid-area: inspector;
  width: var(--mj-shell-inspector-width, 320px);
  overflow: hidden auto;
  border-inline-start: 1px solid var(--mj-border);
  background: var(--mj-surface);
  transition: width var(--mj-motion-medium) var(--mj-motion-ease);
}

:host(:not([inspector-open])) .inspector {
  width: 0;
  overflow: hidden;
}

.status-bar {
  grid-area: statusbar;
  z-index: var(--mj-layer-docked);
}

.overlay-backdrop {
  display: none;
  position: fixed;
  inset: 0;
  background: var(--mj-overlay-scrim);
  z-index: calc(var(--mj-layer-overlay) - 1);
}

:host([nav-mode="overlay"][nav-open]) .overlay-backdrop {
  display: block;
}

.no-motion,
.no-motion * {
  transition: none !important;
}

.split-handle {
  width: 4px;
  cursor: col-resize;
  background: transparent;
  z-index: 1;
  flex-shrink: 0;
  border: none;
  padding: 0;
}

.split-handle:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}

.split-handle:hover {
  background: var(--mj-accent);
  opacity: 0.4;
}

.nav-toggle {
  position: absolute;
  inset-block-start: var(--mj-space-2);
  inset-inline-end: var(--mj-space-2);
  z-index: 1;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: var(--mj-space-1);
  border-radius: var(--mj-radius-sm);
  color: var(--mj-text-muted);
  font-size: var(--mj-font-size-md);
  line-height: 1;
}

.nav-toggle:hover { background: var(--mj-bg-muted); }
.nav-toggle:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}
`;

/*
 * Parse a CSS length used as a breakpoint. Supports px, rem, and em (both
 * resolved against the root font size); returns null for anything else.
 */
function parseBreakpoint(raw) {
  const value = String(raw || "").trim()
  if (value.length === 0) {
    return null
  }
  const match = value.match(/^(-?[0-9]*\.?[0-9]+)(px|rem|em)?$/)
  if (match === null) {
    return null
  }
  const amount = parseFloat(match[1])
  const unit = match[2] || "px"
  if (unit === "px") {
    return amount
  }
  const rootSize = parseFloat(getComputedStyle(document.documentElement).fontSize) || 16
  return amount * rootSize
}

export class MjAppShell extends MjElement {
  static tagName = "mj-app-shell";
  static styles = STYLES;
  static watched = [
    "nav-open", "nav-mode", "inspector-open",
    "inspector-size", "nav-size", "storage-key", "split",
    "nav-label", "inspector-label"
  ];

  constructor() {
    super()
    this._trapDispose = null
    this._resizeObserver = null
    this._inspectorDragActive = false
    this._panelNames = ["app-bar", "nav", "main", "inspector", "status-bar"]
    this._panelFocusIndex = 0
    this._wideNavMode = null
    this._wideNavOpen = null
    this._modeSettled = false
    this._applyingMode = false
    this._onDocumentKeydown = this._handleDocumentKeydown.bind(this)
    this._documentKeydownAttached = false
  }

  render() {
    const markup = `
      <div class="overlay-backdrop" part="backdrop"></div>
      <header class="app-bar" part="app-bar">
        <slot name="app-bar"></slot>
      </header>
      <div class="dock" part="dock">
        <slot name="dock"></slot>
      </div>
      <div class="side-nav" part="nav" id="mj-shell-nav">
        <slot name="workspace"></slot>
        <slot name="nav"></slot>
      </div>
      <div class="main-area" part="main" id="mj-shell-main">
        <slot></slot>
        <slot name="main"></slot>
      </div>
      <aside class="inspector" part="inspector" id="mj-shell-inspector">
        <slot name="inspector"></slot>
      </aside>
      <footer class="status-bar" part="status-bar">
        <slot name="status-bar"></slot>
      </footer>
    `
    return markup
  }

  afterRender() {
    this._backdrop = this.$(".overlay-backdrop")
    this._appBarEl = this.$(".app-bar")
    this._dockEl = this.$(".dock")
    this._navEl = this.$(".side-nav")
    this._mainEl = this.$(".main-area")
    this._inspectorEl = this.$(".inspector")
    this._statusBarEl = this.$(".status-bar")

    this._restoreSizes()

    this.listen(this._backdrop, "click", this._onBackdropClick.bind(this))
    this.listen(this, "keydown", this._onKeydown.bind(this))

    const slots = this.shadowRoot.querySelectorAll("slot")
    for (let index = 0; index < slots.length; index = index + 1) {
      this.listen(slots[index], "slotchange", this._syncRegions.bind(this))
    }
    this._syncRegions()

    if (typeof ResizeObserver === "function") {
      this._resizeObserver = new ResizeObserver(this._onResize.bind(this))
      this._resizeObserver.observe(this)
    }
    this.onTeardown(() => {
      if (this._resizeObserver !== null) {
        this._resizeObserver.disconnect()
        this._resizeObserver = null
      }
      this._releaseOverlay(false)
    })

    return
  }

  _storageKey() {
    return this.getAttribute("storage-key") || "mj-app-shell"
  }

  _restoreSizes() {
    try {
      const navSize = localStorage.getItem(`${this._storageKey()}-nav-size`)
      if (navSize !== null) {
        this.style.setProperty("--mj-shell-nav-width", `${navSize}px`)
      }
      const inspectorSize = localStorage.getItem(`${this._storageKey()}-inspector-size`)
      if (inspectorSize !== null) {
        this.style.setProperty("--mj-shell-inspector-width", `${inspectorSize}px`)
      }
    } catch (e) {
      // localStorage unavailable (private mode)
    }
    return
  }

  /* ----- landmarks and empty regions ----- */

  _assigned(slotName) {
    const selector = slotName === "" ? "slot:not([name])" : `slot[name='${slotName}']`
    const slot = this.shadowRoot.querySelector(selector)
    if (slot === null) {
      return []
    }
    const assigned = slot.assignedElements({ flatten: true })
    return assigned
  }

  /*
   * Give each region the landmark role only when its content does not bring
   * its own, and hide the regions whose slots are empty.
   */
  _syncRegions() {
    if (this._mainEl === undefined) {
      return
    }

    const mainContent = this._assigned("").concat(this._assigned("main"))
    const providesMain = mainContent.some((el) => el.matches(MAIN_LANDMARK_SELECTOR))
    if (providesMain === true) {
      this._mainEl.removeAttribute("role")
    } else {
      this._mainEl.setAttribute("role", "main")
    }

    const navContent = this._assigned("workspace").concat(this._assigned("nav"))
    const providesNav = navContent.some((el) => el.matches(NAVIGATION_LANDMARK_SELECTOR))
    if (providesNav === true || navContent.length === 0) {
      this._navEl.removeAttribute("role")
      this._navEl.removeAttribute("aria-label")
    } else {
      this._navEl.setAttribute("role", "navigation")
      this._navEl.setAttribute("aria-label", this.getAttribute("nav-label") || t("mj.appShell.navLabel"))
    }

    this._dockEl.hidden = this._assigned("dock").length === 0
    this._statusBarEl.hidden = this._assigned("status-bar").length === 0
    this._inspectorEl.hidden = this._assigned("inspector").length === 0
    this._inspectorEl.setAttribute("aria-label", this.getAttribute("inspector-label") || t("mj.appShell.inspectorLabel"))
    return
  }

  /* ----- responsive nav mode ----- */

  _navBreakpoint() {
    const raw = getComputedStyle(this).getPropertyValue("--mj-shell-breakpoint-nav")
    const parsed = parseBreakpoint(raw)
    const rtnval = parsed !== null ? parsed : DEFAULT_NAV_BREAKPOINT_PX
    return rtnval
  }

  _onResize(entries) {
    if (entries.length === 0) {
      return
    }
    const width = entries[entries.length - 1].contentRect.width
    const overlay = width < this._navBreakpoint()

    // The first measurement settles the initial layout before the first
    // paint; apply it without the drawer/width transitions so a narrow
    // viewport does not animate the nav away on every page load.
    const firstSettle = this._modeSettled === false
    if (firstSettle === true) {
      this._suppressMotion()
    }
    this._applyNavMode(overlay)
    this._modeSettled = true
    return
  }

  _suppressMotion() {
    const regions = [this._navEl, this._mainEl, this._inspectorEl]
    regions.forEach((region) => region.classList.add("no-motion"))
    const release = () => {
      regions.forEach((region) => region.classList.remove("no-motion"))
    }
    if (typeof requestAnimationFrame === "function") {
      requestAnimationFrame(() => {
        requestAnimationFrame(release)
      })
    } else {
      setTimeout(release, 50)
    }
    return
  }

  /*
   * Switch between the overlay drawer and the wide layout. Entering overlay
   * mode remembers the wide mode and open state and closes the drawer;
   * leaving it restores both.
   */
  _applyNavMode(overlay) {
    const currentMode = this.getAttribute("nav-mode") || "static"
    this._applyingMode = true
    try {
      if (overlay === true && currentMode !== "overlay") {
        this._wideNavMode = currentMode
        this._wideNavOpen = this.hasAttribute("nav-open")
        this.setAttribute("nav-mode", "overlay")
        this.removeAttribute("nav-open")
      } else if (overlay === false && currentMode === "overlay") {
        const restoreMode = this._wideNavMode !== null ? this._wideNavMode : "static"
        this.setAttribute("nav-mode", restoreMode)
        const restoreOpen = this._wideNavOpen !== null ? this._wideNavOpen : true
        this.reflectBoolean("nav-open", restoreOpen === true)
      }
    } finally {
      this._applyingMode = false
    }
    return
  }

  _isOverlay() {
    return this.getAttribute("nav-mode") === "overlay"
  }

  /* ----- overlay drawer ----- */

  _openOverlay() {
    if (this._trapDispose !== null) {
      return
    }
    // Move focus into the drawer first (trapFocus does), then make the rest
    // of the shell inert so neither Tab nor assistive technology can reach
    // the content behind the drawer.
    this._trapDispose = trapFocus(this._navEl)
    this._setBackgroundInert(true)
    if (this._documentKeydownAttached === false) {
      document.addEventListener("keydown", this._onDocumentKeydown)
      this._documentKeydownAttached = true
    }
    return
  }

  /*
   * Undo _openOverlay. `restoreFocus` returns focus to the element that had
   * it before the drawer opened (the toggle, usually).
   */
  _releaseOverlay(restoreFocus) {
    if (this._documentKeydownAttached === true) {
      document.removeEventListener("keydown", this._onDocumentKeydown)
      this._documentKeydownAttached = false
    }
    this._setBackgroundInert(false)
    if (this._trapDispose !== null) {
      const dispose = this._trapDispose
      this._trapDispose = null
      dispose({ restoreFocus: restoreFocus === true })
    }
    return
  }

  _setBackgroundInert(inert) {
    const regions = [this._appBarEl, this._dockEl, this._mainEl, this._inspectorEl, this._statusBarEl]
    regions.forEach((region) => {
      if (region === null || region === undefined) {
        return
      }
      if (inert === true) {
        region.setAttribute("inert", "")
      } else {
        region.removeAttribute("inert")
      }
    })
    return
  }

  _closeOverlayFromKey(event) {
    if (event.key !== "Escape" || event.defaultPrevented === true) {
      return
    }
    if (this._isOverlay() === false || this.hasAttribute("nav-open") === false) {
      return
    }
    event.preventDefault()
    this.navOpen = false
    return
  }

  _handleDocumentKeydown(event) {
    this._closeOverlayFromKey(event)
    return
  }

  _onBackdropClick() {
    this.navOpen = false
    return
  }

  _onKeydown(event) {
    if (event.key === "F6") {
      event.preventDefault()
      this._cycleFocus()
    } else if (event.key === "Escape") {
      this._closeOverlayFromKey(event)
    }
    return
  }

  _cycleFocus() {
    const panels = [
      this._appBarEl,
      this._navEl,
      this._mainEl,
      this._inspectorEl,
      this._statusBarEl
    ]

    this._panelFocusIndex = (this._panelFocusIndex + 1) % panels.length
    const panel = panels[this._panelFocusIndex]
    if (panel !== null && panel !== undefined) {
      panel.focus()
      const names = ["App bar", "Navigation", "Main content", "Inspector", "Status bar"]
      announce(`Focus moved to ${names[this._panelFocusIndex]}`, "polite")
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "nav-open") {
      const open = newValue !== null
      if (this._isOverlay() === true) {
        if (open === true) {
          this._openOverlay()
        } else {
          this._releaseOverlay(true)
        }
      } else {
        this._releaseOverlay(false)
        if (this._applyingMode === false) {
          this._wideNavOpen = open
        }
      }
      if ((oldValue !== null) !== open) {
        this.emit("mj-shell-nav-toggle", { open: open })
      }
    }

    if (name === "nav-mode" && this._navEl !== undefined) {
      if (newValue !== "overlay") {
        this._releaseOverlay(false)
      } else if (this.hasAttribute("nav-open") === true && this._applyingMode === false) {
        this._openOverlay()
      }
    }

    if (name === "inspector-open") {
      const open = newValue !== null
      this.emit("mj-shell-inspector-toggle", { open: open })
    }

    if (name === "nav-label" || name === "inspector-label") {
      this._syncRegions()
    }

    return
  }

  get navOpen() {
    return this.hasAttribute("nav-open")
  }

  set navOpen(value) {
    this.reflectBoolean("nav-open", value === true)
    return
  }

  get inspectorOpen() {
    return this.hasAttribute("inspector-open")
  }

  set inspectorOpen(value) {
    this.reflectBoolean("inspector-open", value === true)
    return
  }

  toggleNav() {
    this.navOpen = !this.navOpen
    return
  }

  toggleInspector() {
    this.inspectorOpen = !this.inspectorOpen
    return
  }

  get navPanel() {
    const slot = this.$("slot[name='nav']")
    if (slot === null) {
      return null
    }
    const assigned = slot.assignedElements()
    return assigned.length > 0 ? assigned[0] : null
  }

  get inspectorPanel() {
    const slot = this.$("slot[name='inspector']")
    if (slot === null) {
      return null
    }
    const assigned = slot.assignedElements()
    return assigned.length > 0 ? assigned[0] : null
  }
}
