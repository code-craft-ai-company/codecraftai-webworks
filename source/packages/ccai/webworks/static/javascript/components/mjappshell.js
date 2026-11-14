/*
 * mjappshell.js
 *
 * <mj-app-shell> -- outermost layout frame composing AppBar, SideNav, main
 * content area, inspector panel, and StatusBar into correct landmark structure.
 * Supports resizable regions with persisted sizes, responsive collapse, and
 * keyboard panel cycling.
 *
 * Landmarks: the shell gives a region a landmark role only where the slotted
 * content does not already provide one, so a page never exposes nested or
 * duplicate landmarks. That holds for the banner (<header>, role="banner",
 * <mj-app-bar>), the navigation (<nav>, role="navigation", <mj-side-nav>,
 * <mj-tree-nav>), the main region (<main>, role="main"), the inspector
 * (<aside>, role="complementary") and the status bar (<footer>,
 * role="contentinfo"; <mj-status-bar> is a plain group, so the shell supplies
 * the landmark around it). A region whose slots are empty is not rendered at
 * all.
 *
 * Responsive behavior: below the `--mj-shell-breakpoint-nav` width (default
 * 768px) the shell is "narrow". The author's `nav-mode` attribute is never
 * rewritten; the narrow state is reflected in the `narrow` attribute instead
 * and makes both the nav and the inspector overlay drawers. Entering the
 * narrow layout closes both (and leaving it restores the wide-layout open
 * state), so a narrow viewport never loads with a drawer covering the
 * content. While an overlay drawer is open, focus is moved into it and
 * trapped there, the rest of the shell is inert, and Escape closes it
 * wherever focus is. `nav-mode="overlay"` asks for the drawer at every width.
 *
 * Resizing: the nav and the inspector each have a separator handle
 * (role="separator") that is dragged with the pointer or moved with
 * ArrowLeft / ArrowRight / Home / End. With `split` the main area is divided
 * into two panes separated by a third handle. The handles live in the
 * workspace column, at its edges and between the panes, so the main
 * landmark the shell supplies there holds them (no handle sits outside
 * every landmark). A page that slots its own <main> keeps that landmark,
 * and the shell then supplies none for the handles to sit in. Sizes come from `nav-size`,
 * `inspector-size` and `split-ratio`, are written to localStorage under the
 * `storage-key` prefix whenever the user changes them, and are restored on
 * the next load. A stored size wins over the attribute at load; a later
 * change of the attribute applies. Changing `storage-key` switches to the
 * sizes stored under the new prefix.
 *
 * Keyboard: F6 / Shift+F6 move focus to the next / previous visible region,
 * starting from the region that holds focus (from the dock or a separator,
 * the region beyond it in that direction).
 *
 * Skip link: the main region lives in the shadow root, where no fragment URL
 * reaches, so the built-in skip link is a link without an href that calls
 * `focusMain()`. A link slotted into `skip-link` is wired the same way unless
 * its href names an element outside the main content (or another page), in
 * which case the browser follows it.
 */

import { MjElement } from "../core/mjelement.js";
import { trapFocus, deepActiveElement } from "../core/focustrap.js";
import { announce } from "../core/announcer.js";
import { t } from "../core/intl.js";

const DEFAULT_NAV_BREAKPOINT_PX = 768;

/* Distance one arrow-key press moves a separator, unless --mj-shell-split-step says otherwise. */
const DEFAULT_RESIZE_STEP_PX = 16;

/* Resize events and the localStorage write wait for the size to settle. */
const RESIZE_SETTLE_MS = 200;

/* A side region never takes more than this share of the shell in the wide layout. */
const MAX_REGION_SHARE = 0.5;

const NAV_SIZE_LIMITS = { fallback: 240, min: 160, max: 480 };
const INSPECTOR_SIZE_LIMITS = { fallback: 320, min: 200, max: 640 };
const SPLIT_RATIO_LIMITS = { fallback: 0.5, min: 0.1, max: 0.9 };

/* Slotted elements that render their own landmark, per region. */
const BANNER_LANDMARK_SELECTOR = "header, [role='banner'], mj-app-bar";
const NAVIGATION_LANDMARK_SELECTOR = "nav, [role='navigation'], mj-side-nav, mj-tree-nav";
const MAIN_LANDMARK_SELECTOR = "main, [role='main']";
const COMPLEMENTARY_LANDMARK_SELECTOR = "aside, [role='complementary']";
const CONTENTINFO_LANDMARK_SELECTOR = "footer, [role='contentinfo']";

const NAV_MODES = ["static", "collapsible", "overlay"];

const STYLES = `
:host {
  display: grid;
  position: relative;
  inline-size: 100%;
  block-size: var(--mj-shell-height, 100dvh);
  /*
   * clip, not hidden: a hidden overflow is still a scroll container, and
   * moving focus into a drawer that is sliding in from off-screen would
   * scroll the whole shell sideways (hidden stays as the fallback).
   */
  overflow: hidden;
  overflow: clip;
  background: var(--mj-shell-bg, var(--mj-bg));
  grid-template-rows: auto minmax(0, 1fr) auto;
  grid-template-columns: auto auto minmax(0, 1fr) auto;
  grid-template-areas:
    "appbar    appbar    appbar    appbar"
    "dock      nav       main      inspector"
    "statusbar statusbar statusbar statusbar";
}

:host([hidden]) { display: none; }

[hidden] { display: none !important; }

.region:focus { outline: none; }

.region:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: calc(-1 * var(--mj-focus-ring-width));
}

.skip-link {
  position: absolute;
  grid-area: 1 / 1 / -1 / -1;
  inset-block-start: var(--mj-space-2);
  inset-inline-start: var(--mj-space-2);
  z-index: var(--mj-layer-modal);
  padding: var(--mj-space-2) var(--mj-space-3);
  border-radius: var(--mj-radius-sm);
  background: var(--mj-surface-raised);
  color: var(--mj-accent);
  box-shadow: var(--mj-elevation-2);
  font-size: var(--mj-font-size-sm);
  text-decoration: underline;
  cursor: pointer;
  translate: 0 -300%;
}

.skip-link:focus {
  translate: 0 0;
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.app-bar {
  grid-area: appbar;
  display: flex;
  align-items: center;
  min-inline-size: 0;
  z-index: var(--mj-layer-sticky);
  background: var(--mj-shell-appbar-bg, var(--mj-surface));
}

.app-bar-content {
  flex: 1 1 auto;
  min-inline-size: 0;
}

.nav-toggle {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  inline-size: var(--mj-control-height-lg);
  block-size: var(--mj-control-height-lg);
  margin-inline: var(--mj-space-1);
  padding: 0;
  background: transparent;
  border: none;
  border-radius: var(--mj-radius-sm);
  color: var(--mj-text);
  cursor: pointer;
}

.nav-toggle svg {
  inline-size: 1.25rem;
  block-size: 1.25rem;
}

.nav-toggle:hover { background: var(--mj-bg-muted); }

.nav-toggle:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: calc(-1 * var(--mj-focus-ring-width));
}

.dock {
  grid-area: dock;
  inline-size: var(--mj-shell-dock-width, 48px);
  overflow: hidden;
  border-inline-end: 1px solid var(--mj-border);
  background: var(--mj-surface);
}

/* ----- side nav ----- */

.side-nav {
  grid-area: nav;
  inline-size: var(--mj-shell-nav-current, var(--mj-shell-nav-width, 240px));
  max-inline-size: var(--mj-shell-region-max, 50vw);
  overflow: hidden auto;
  border-inline-end: 1px solid var(--mj-border);
  background: var(--mj-surface);
  transition: inline-size var(--mj-motion-medium) var(--mj-motion-ease);
}

/*
 * A closed region is taken out of the tab order and the accessibility tree
 * with visibility:hidden, switched once the closing transition has run.
 */
:host(:not([nav-open])) .side-nav {
  inline-size: 0;
  border-inline-end-width: 0;
  visibility: hidden;
  transition: inline-size var(--mj-motion-medium) var(--mj-motion-ease),
              visibility 0s linear var(--mj-motion-medium);
}

:host([nav-mode="collapsible"]:not([nav-open]):not([narrow])) .side-nav {
  inline-size: var(--mj-shell-dock-width, 48px);
  border-inline-end-width: 1px;
  visibility: visible;
}

:host(:is([narrow], [nav-mode="overlay"])) .side-nav {
  position: absolute;
  grid-area: 1 / 1 / -1 / -1;
  inset-block: 0;
  inset-inline-start: 0;
  inline-size: var(--mj-shell-nav-current, var(--mj-shell-nav-width, 240px));
  max-inline-size: 85%;
  z-index: var(--mj-layer-overlay);
  border-inline-end-width: 1px;
  box-shadow: var(--mj-elevation-3);
  visibility: visible;
  transition: inset-inline-start var(--mj-motion-medium) var(--mj-motion-ease);
}

:host(:is([narrow], [nav-mode="overlay"]):not([nav-open])) .side-nav {
  inset-inline-start: -100%;
  box-shadow: none;
  visibility: hidden;
  transition: inset-inline-start var(--mj-motion-medium) var(--mj-motion-ease),
              visibility 0s linear var(--mj-motion-medium);
}

/* ----- main area and split view -----
 *
 * The workspace holds, in a row: the nav handle, the main region, the split
 * handle, the second pane and the inspector handle. It carries the main
 * landmark (unless the slotted content brings its own), so the handles are
 * inside a landmark.
 */

.workspace {
  grid-area: main;
  display: flex;
  min-inline-size: 0;
  min-block-size: 0;
}

.main-area {
  flex: 1 1 0;
  overflow: auto;
  background: var(--mj-bg);
  min-inline-size: 0;
  min-block-size: 0;
}

.split-secondary {
  flex: 0 0 calc((1 - var(--mj-shell-split-current, 0.5)) * 100%);
  overflow: auto;
  background: var(--mj-bg);
  border-inline-start: 1px solid var(--mj-border);
  min-inline-size: 0;
  min-block-size: 0;
}

.split-placeholder {
  margin: 0;
  padding: var(--mj-space-4);
  color: var(--mj-text-muted);
  font-size: var(--mj-font-size-sm);
}

/* ----- inspector ----- */

.inspector {
  grid-area: inspector;
  inline-size: var(--mj-shell-inspector-current, var(--mj-shell-inspector-width, 320px));
  max-inline-size: var(--mj-shell-region-max, 50vw);
  overflow: hidden auto;
  border-inline-start: 1px solid var(--mj-border);
  background: var(--mj-surface);
  transition: inline-size var(--mj-motion-medium) var(--mj-motion-ease);
}

:host(:not([inspector-open])) .inspector {
  inline-size: 0;
  border-inline-start-width: 0;
  visibility: hidden;
  transition: inline-size var(--mj-motion-medium) var(--mj-motion-ease),
              visibility 0s linear var(--mj-motion-medium);
}

:host([narrow]) .inspector {
  position: absolute;
  grid-area: 1 / 1 / -1 / -1;
  inset-block: 0;
  inset-inline-end: 0;
  inline-size: var(--mj-shell-inspector-current, var(--mj-shell-inspector-width, 320px));
  max-inline-size: 85%;
  z-index: var(--mj-layer-overlay);
  border-inline-start-width: 1px;
  box-shadow: var(--mj-elevation-3);
  visibility: visible;
  transition: inset-inline-end var(--mj-motion-medium) var(--mj-motion-ease);
}

:host([narrow]:not([inspector-open])) .inspector {
  inset-inline-end: -100%;
  box-shadow: none;
  visibility: hidden;
  transition: inset-inline-end var(--mj-motion-medium) var(--mj-motion-ease),
              visibility 0s linear var(--mj-motion-medium);
}

.status-bar {
  grid-area: statusbar;
  z-index: var(--mj-layer-docked);
}

.overlay-backdrop {
  position: absolute;
  grid-area: 1 / 1 / -1 / -1;
  inset: 0;
  background: var(--mj-overlay-scrim);
  z-index: calc(var(--mj-layer-overlay) - 1);
}

.no-motion,
.no-motion * {
  transition: none !important;
}

/* ----- separator handles -----
 *
 * A handle takes no room in the layout: it is a zero-width item of the
 * workspace row whose hit area straddles the border between the two regions
 * it separates (the nav and inspector handles reach over the workspace edge
 * onto the neighbouring column's border).
 */

.split-handle {
  position: relative;
  flex: 0 0 0;
  inline-size: 0;
  z-index: 2;
  outline: none;
  touch-action: none;
}

.split-handle::before {
  content: "";
  position: absolute;
  inset-block: 0;
  inset-inline-start: calc(-1 * var(--mj-shell-split-handle-size, 4px));
  inline-size: calc(2 * var(--mj-shell-split-handle-size, 4px));
  cursor: col-resize;
  background: transparent;
  transition: background var(--mj-motion-fast) var(--mj-motion-ease);
}

.split-handle:hover::before,
.split-handle[resizing]::before {
  background: var(--mj-accent);
  opacity: 0.4;
}

.split-handle:focus-visible::before {
  background: var(--mj-focus-ring);
  opacity: 1;
}

`;

/*
 * Parse a CSS length used as a breakpoint or step. Supports px, rem, and em
 * (both resolved against the root font size); returns null for anything else.
 */
function parseLength(raw) {
  let parsed = null

  const value = String(raw || "").trim()
  const match = value.match(/^(-?[0-9]*\.?[0-9]+)(px|rem|em)?$/)
  if (match !== null) {
    const amount = parseFloat(match[1])
    const unit = match[2] || "px"
    if (unit === "px") {
      parsed = amount
    } else {
      const rootSize = parseFloat(getComputedStyle(document.documentElement).fontSize) || 16
      parsed = amount * rootSize
    }
  }

  return parsed
}

/* Parse a finite number from an attribute or storage string; null when it is not one. */
function parseNumber(raw) {
  let parsed = null

  if (raw !== null && raw !== undefined && String(raw).trim().length > 0) {
    const amount = Number(raw)
    if (Number.isFinite(amount) === true) {
      parsed = amount
    }
  }

  return parsed
}

/*
 * True when `node` is `ancestor` or sits below it in the flat tree, following
 * slot assignment and shadow hosts upward.
 */
function composedContains(ancestor, node) {
  let found = false
  let current = node

  while (current !== null && current !== undefined && found === false) {
    if (current === ancestor) {
      found = true
    } else if (current.assignedSlot !== null && current.assignedSlot !== undefined) {
      current = current.assignedSlot
    } else if (current.parentNode !== null && current.parentNode !== undefined) {
      current = current.parentNode
    } else {
      current = current.host
    }
  }

  return found
}

export class MjAppShell extends MjElement {
  static tagName = "mj-app-shell";
  static styles = STYLES;
  static watched = [
    "nav-open", "nav-mode", "inspector-open",
    "inspector-size", "nav-size", "storage-key", "split", "split-ratio",
    "nav-label", "inspector-label", "status-bar-label", "hide-nav-toggle"
  ];

  constructor() {
    super()

    /* Shadow references; null until the first render. */
    this._backdrop = null
    this._skipLink = null
    this._appBarEl = null
    this._navToggle = null
    this._dockEl = null
    this._navEl = null
    this._workspaceEl = null
    this._mainEl = null
    this._secondaryEl = null
    this._inspectorEl = null
    this._statusBarEl = null
    this._resizers = null

    this._resizeObserver = null

    /* True while the shell is narrower than the nav breakpoint. */
    this._narrow = false
    this._modeSettled = false
    this._shellWidth = 0

    /* Open state of the wide layout, remembered while the shell is narrow. */
    this._wideNavOpen = null
    this._wideInspectorOpen = null

    /* Open state last reported through the toggle events. */
    this._reportedOpen = { nav: false, inspector: false }

    /* The region currently shown as a modal drawer: "nav", "inspector" or null. */
    this._modalName = null
    this._trapDispose = null

    /*
     * Explicit region sizes: px for nav and inspector, a 0-1 ratio for the
     * split. null means "use the CSS default". They live here so they survive
     * a re-render.
     */
    this._sizes = { nav: null, inspector: null, split: null }
    this._sizesRestored = false

    /*
     * The `nav-size` / `inspector-size` / `split-ratio` text last taken into
     * account, per resizer. The replay of the markup value after the first
     * render is then recognised and does not overwrite a restored size.
     */
    this._appliedSizeAttributes = { nav: null, inspector: null, split: null }

    /* The localStorage prefix the current sizes belong to. */
    this._storagePrefix = null

    /* The separator drag in progress, or null. */
    this._drag = null

    this._mainScrollFrame = null
  }

  render() {
    const markup = `
      <slot name="skip-link"><a class="skip-link" part="skip-link" role="link" tabindex="0"></a></slot>
      <div class="app-bar region" part="app-bar" id="mj-shell-app-bar" tabindex="-1">
        <button class="nav-toggle" part="nav-toggle-button" type="button"
                aria-controls="mj-shell-nav" aria-expanded="false" hidden>
          <slot name="nav-toggle-icon">
            <svg viewBox="0 0 20 20" aria-hidden="true" focusable="false">
              <path d="M3 5h14M3 10h14M3 15h14" fill="none" stroke="currentColor"
                    stroke-width="1.75" stroke-linecap="round"></path>
            </svg>
          </slot>
        </button>
        <div class="app-bar-content"><slot name="app-bar"></slot></div>
      </div>
      <div class="dock" part="dock">
        <slot name="dock"></slot>
      </div>
      <div class="side-nav region" part="nav" id="mj-shell-nav" tabindex="-1">
        <slot name="workspace"></slot>
        <slot name="nav"></slot>
      </div>
      <div class="workspace">
        <div class="split-handle nav-handle" part="split-handle" role="separator"
             tabindex="0" aria-orientation="vertical" aria-controls="mj-shell-nav" hidden></div>
        <div class="main-area region" part="main" id="mj-shell-main" tabindex="-1">
          <slot></slot>
          <slot name="main"></slot>
        </div>
        <div class="split-handle pane-handle" part="split-handle" role="separator"
             tabindex="0" aria-orientation="vertical" aria-controls="mj-shell-main" hidden></div>
        <div class="split-secondary region" part="split-secondary" id="mj-shell-split-secondary"
             role="region" tabindex="-1" hidden>
          <slot name="split-secondary"><p class="split-placeholder"></p></slot>
        </div>
        <div class="split-handle inspector-handle" part="split-handle" role="separator"
             tabindex="0" aria-orientation="vertical" aria-controls="mj-shell-inspector" hidden></div>
      </div>
      <div class="inspector region" part="inspector" id="mj-shell-inspector" tabindex="-1">
        <slot name="inspector"></slot>
      </div>
      <div class="status-bar region" part="status-bar" id="mj-shell-status-bar" tabindex="-1">
        <slot name="status-bar"></slot>
      </div>
      <div class="overlay-backdrop" part="backdrop" hidden></div>
    `
    return markup
  }

  afterRender() {
    this._backdrop = this.$(".overlay-backdrop")
    this._skipLink = this.$(".skip-link")
    this._appBarEl = this.$(".app-bar")
    this._navToggle = this.$(".nav-toggle")
    this._dockEl = this.$(".dock")
    this._navEl = this.$(".side-nav")
    this._workspaceEl = this.$(".workspace")
    this._mainEl = this.$(".main-area")
    this._secondaryEl = this.$(".split-secondary")
    this._inspectorEl = this.$(".inspector")
    this._statusBarEl = this.$(".status-bar")

    this._skipLink.textContent = t("mj.skipLink.label")
    this.$(".split-placeholder").textContent = t("mj.appShell.splitEmpty")

    this._modalName = null
    this._trapDispose = null
    this._drag = null
    this._modeSettled = false
    this._reportedOpen = {
      nav: this.hasAttribute("nav-open"),
      inspector: this.hasAttribute("inspector-open")
    }

    this._buildResizers()
    this._restoreSizes()

    this.listen(this._backdrop, "click", this._onBackdropClick.bind(this))
    this.listen(this.$("slot[name='skip-link']"), "click", this._onSkipLinkClick.bind(this))
    this.listen(this._skipLink, "keydown", this._onSkipLinkKeydown.bind(this))
    this.listen(this._navToggle, "click", this._onNavToggleClick.bind(this))
    this.listen(this._navEl, "click", this._onNavClick.bind(this))
    this.listen(this._mainEl, "scroll", this._onMainScroll.bind(this), { passive: true })
    this.listen(document, "keydown", this._onDocumentKeydown.bind(this))

    const slots = this.shadowRoot.querySelectorAll("slot")
    for (let index = 0; index < slots.length; index = index + 1) {
      this.listen(slots[index], "slotchange", this._onSlotChange.bind(this))
    }

    this._syncLayout()

    if (typeof ResizeObserver === "function") {
      this._resizeObserver = new ResizeObserver(this._onResize.bind(this))
      this._resizeObserver.observe(this)
    } else {
      /* No measurement will arrive: treat the layout as wide and settled. */
      this._modeSettled = true
      this._syncModal(false)
    }

    this.onTeardown(() => {
      if (this._resizeObserver !== null) {
        this._resizeObserver.disconnect()
        this._resizeObserver = null
      }
      if (this._mainScrollFrame !== null) {
        cancelAnimationFrame(this._mainScrollFrame)
        this._mainScrollFrame = null
      }
      this._flushResizers()
      this._releaseModal(false)
    })

    return
  }

  /* ----- landmarks, empty regions and control state ----- */

  _assigned(slotName) {
    const selector = slotName === "" ? "slot:not([name])" : `slot[name='${slotName}']`
    const slot = this.shadowRoot.querySelector(selector)
    let assigned = []
    if (slot !== null) {
      assigned = slot.assignedElements({ flatten: true })
    }
    return assigned
  }

  /*
   * Give `region` the landmark `role` (and accessible name) unless the
   * slotted content brings that landmark itself.
   */
  _applyLandmark(region, content, landmarkSelector, role, label) {
    const provided = content.some((element) => element.matches(landmarkSelector))

    if (provided === true || content.length === 0) {
      region.removeAttribute("role")
      region.removeAttribute("aria-label")
    } else {
      region.setAttribute("role", role)
      if (label !== null) {
        region.setAttribute("aria-label", label)
      } else {
        region.removeAttribute("aria-label")
      }
    }
    return
  }

  _navLabel() {
    const label = this.getAttribute("nav-label") || t("mj.appShell.navLabel")
    return label
  }

  _inspectorLabel() {
    const label = this.getAttribute("inspector-label") || t("mj.appShell.inspectorLabel")
    return label
  }

  _statusBarLabel() {
    const label = this.getAttribute("status-bar-label") || t("mj.appShell.statusBarLabel")
    return label
  }

  /*
   * The nav mode in effect: the overlay drawer while the shell is narrow, the
   * author's `nav-mode` otherwise.
   */
  _effectiveNavMode() {
    let mode = "overlay"

    if (this._narrow === false) {
      const requested = this.getAttribute("nav-mode")
      mode = NAV_MODES.indexOf(requested) >= 0 ? requested : "static"
    }

    return mode
  }

  /*
   * Bring every region in line with the slotted content and the current
   * attributes: landmark roles, hidden empty regions, the nav toggle and the
   * separator handles. Safe to call at any time after the first render.
   */
  _syncLayout() {
    if (this._mainEl === undefined || this._mainEl === null) {
      return
    }

    const appBarContent = this._assigned("app-bar")
    const navContent = this._assigned("workspace").concat(this._assigned("nav"))
    const mainContent = this._assigned("").concat(this._assigned("main"))
    const inspectorContent = this._assigned("inspector")
    const statusBarContent = this._assigned("status-bar")

    const hasNav = navContent.length > 0
    const navMode = this._effectiveNavMode()
    const navOpen = this.hasAttribute("nav-open")
    const inspectorOpen = this.hasAttribute("inspector-open")
    const split = this.hasAttribute("split")

    /*
     * Landmarks. The main region always exists, so it is never "empty". The
     * main landmark goes on the workspace around the main region, which
     * also holds the separator handles and the second pane.
     */
    this._applyLandmark(this._appBarEl, appBarContent, BANNER_LANDMARK_SELECTOR, "banner", null)
    this._applyLandmark(this._navEl, navContent, NAVIGATION_LANDMARK_SELECTOR, "navigation", this._navLabel())
    this._applyLandmark(this._inspectorEl, inspectorContent, COMPLEMENTARY_LANDMARK_SELECTOR, "complementary", this._inspectorLabel())
    this._applyLandmark(this._statusBarEl, statusBarContent, CONTENTINFO_LANDMARK_SELECTOR, "contentinfo", this._statusBarLabel())

    const providesMain = mainContent.some((element) => element.matches(MAIN_LANDMARK_SELECTOR))
    if (providesMain === true) {
      this._workspaceEl.removeAttribute("role")
    } else {
      this._workspaceEl.setAttribute("role", "main")
    }

    /* The nav toggle: offered wherever the nav can be opened and closed. */
    const toggleWanted =
      hasNav === true &&
      this.hasAttribute("hide-nav-toggle") === false &&
      (navMode === "overlay" || navMode === "collapsible")
    this._navToggle.hidden = toggleWanted === false
    this._navToggle.setAttribute("aria-expanded", navOpen === true ? "true" : "false")
    this._navToggle.setAttribute("aria-label", navOpen === true ? t("mj.appBar.closeNav") : t("mj.appBar.openNav"))

    /* Empty regions take no space and expose no landmark. */
    this._appBarEl.hidden = appBarContent.length === 0 && toggleWanted === false
    this._dockEl.hidden = this._assigned("dock").length === 0
    this._navEl.hidden = hasNav === false
    this._inspectorEl.hidden = inspectorContent.length === 0
    this._statusBarEl.hidden = statusBarContent.length === 0

    /* Split view. */
    this._secondaryEl.hidden = split === false
    this._secondaryEl.setAttribute("aria-label", t("mj.appShell.secondaryLabel"))

    /* Separator handles exist only beside an open, in-flow region. */
    const navResizable = hasNav === true && navOpen === true && navMode !== "overlay"
    const inspectorResizable = inspectorContent.length > 0 && inspectorOpen === true && this._narrow === false
    this._resizers.nav.handle.hidden = navResizable === false
    this._resizers.inspector.handle.hidden = inspectorResizable === false
    this._resizers.split.handle.hidden = split === false

    this._syncHandles()
    return
  }

  _onSlotChange() {
    this._syncLayout()
    if (this._modeSettled === true) {
      this._syncModal(false)
    }
    return
  }

  /* ----- responsive layout ----- */

  _navBreakpoint() {
    const raw = getComputedStyle(this).getPropertyValue("--mj-shell-breakpoint-nav")
    const parsed = parseLength(raw)
    const breakpoint = parsed !== null ? parsed : DEFAULT_NAV_BREAKPOINT_PX
    return breakpoint
  }

  _onResize(entries) {
    if (entries.length === 0) {
      return
    }

    const width = entries[entries.length - 1].contentRect.width
    this._shellWidth = width

    /* The side regions may take at most a share of the shell (wide layout). */
    const regionMax = `${Math.round(width * MAX_REGION_SHARE)}px`
    this._navEl.style.setProperty("--mj-shell-region-max", regionMax)
    this._inspectorEl.style.setProperty("--mj-shell-region-max", regionMax)

    /*
     * The first measurement settles the initial layout before the first
     * paint; apply it without the drawer/width transitions so a narrow
     * viewport does not animate the regions away on every page load.
     */
    if (this._modeSettled === false) {
      this._suppressMotion()
    }

    this._applyNarrow(width < this._navBreakpoint())
    this._modeSettled = true

    this._syncLayout()
    this._syncModal(false)
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
   * Enter or leave the narrow layout. Entering remembers the wide-layout
   * open state of the nav and the inspector and closes both; leaving
   * restores it. The author's `nav-mode` is left alone.
   */
  _applyNarrow(narrow) {
    if (narrow === this._narrow) {
      return
    }

    this._narrow = narrow
    this.reflectBoolean("narrow", narrow)

    if (narrow === true) {
      this._wideNavOpen = this.hasAttribute("nav-open")
      this._wideInspectorOpen = this.hasAttribute("inspector-open")
      this.removeAttribute("nav-open")
      this.removeAttribute("inspector-open")
    } else {
      if (this._wideNavOpen !== null) {
        this.reflectBoolean("nav-open", this._wideNavOpen === true)
      }
      if (this._wideInspectorOpen !== null) {
        this.reflectBoolean("inspector-open", this._wideInspectorOpen === true)
      }
    }
    return
  }

  /* ----- modal overlay drawers ----- */

  /* The region that should currently be a modal drawer, or null. */
  _wantedModalName() {
    let name = null

    const navIsDrawer =
      this._navEl.hidden === false &&
      this._effectiveNavMode() === "overlay" &&
      this.hasAttribute("nav-open") === true
    const inspectorIsDrawer =
      this._narrow === true &&
      this._inspectorEl.hidden === false &&
      this.hasAttribute("inspector-open") === true

    if (navIsDrawer === true) {
      name = "nav"
    } else if (inspectorIsDrawer === true) {
      name = "inspector"
    }

    return name
  }

  /*
   * Open, swap or release the modal drawer so it matches the attributes.
   * `restoreFocus` says whether a released drawer hands focus back to the
   * element that had it before the drawer opened.
   */
  _syncModal(restoreFocus) {
    const wanted = this._wantedModalName()

    if (wanted !== this._modalName) {
      this._releaseModal(restoreFocus === true && wanted === null)
      if (wanted !== null) {
        this._openModal(wanted)
      }
    }
    return
  }

  _modalRegion(name) {
    const region = name === "nav" ? this._navEl : this._inspectorEl
    return region
  }

  _openModal(name) {
    const region = this._modalRegion(name)

    /*
     * Move focus into the drawer first (trapFocus does), then make the rest
     * of the shell inert so neither Tab nor assistive technology can reach
     * the content behind the drawer.
     */
    this._modalName = name
    this._trapDispose = trapFocus(region)
    this._setBackgroundInert(region)
    this._backdrop.hidden = false
    return
  }

  _releaseModal(restoreFocus) {
    if (this._backdrop !== null) {
      this._backdrop.hidden = true
    }
    this._setBackgroundInert(null)
    this._modalName = null

    if (this._trapDispose !== null) {
      const dispose = this._trapDispose
      this._trapDispose = null
      dispose({ restoreFocus: restoreFocus === true })
    }
    return
  }

  /* Make every region except `modalRegion` inert; null clears the state. */
  _setBackgroundInert(modalRegion) {
    const regions = [
      this._appBarEl, this._dockEl, this._navEl, this._workspaceEl,
      this._inspectorEl, this._statusBarEl
    ]
    if (this._resizers !== null) {
      regions.push(this._resizers.nav.handle, this._resizers.inspector.handle)
    }

    for (let index = 0; index < regions.length; index = index + 1) {
      const region = regions[index]
      if (region !== null && region !== undefined) {
        if (modalRegion !== null && region !== modalRegion) {
          region.setAttribute("inert", "")
        } else {
          region.removeAttribute("inert")
        }
      }
    }
    return
  }

  _closeModal() {
    if (this._modalName === "nav") {
      this.navOpen = false
    } else if (this._modalName === "inspector") {
      this.inspectorOpen = false
    }
    return
  }

  _onBackdropClick() {
    this._closeModal()
    return
  }

  _onNavToggleClick() {
    this.toggleNav()
    return
  }

  /*
   * Following a link in the open overlay drawer closes the drawer and moves
   * focus to the main region, where the link's destination is shown.
   */
  _onNavClick(event) {
    if (this._modalName !== "nav") {
      return
    }

    const path = event.composedPath()
    let followedLink = false
    for (let index = 0; index < path.length && followedLink === false; index = index + 1) {
      const node = path[index]
      if (node === this._navEl) {
        break
      }
      if (node instanceof Element && node.matches("a[href], [role='link']") === true) {
        followedLink = true
      }
    }

    if (followedLink === true) {
      this._releaseModal(false)
      this.navOpen = false
      this.focusMain()
    }
    return
  }

  /*
   * A click inside the `skip-link` slot: the built-in link (its fallback
   * content) or the author's. The activated link moves focus to the main
   * region unless the browser can follow it to a target of its own (see
   * `_skipLinkTargetsMain`) or a listener already called preventDefault().
   */
  _onSkipLinkClick(event) {
    if (event.defaultPrevented === true) {
      return
    }

    const slot = event.currentTarget
    const path = event.composedPath()
    let link = null
    for (let index = 0; index < path.length && link === null; index = index + 1) {
      const node = path[index]
      if (node === slot) {
        break
      }
      if (node instanceof Element && node.matches("a, button, [role='link'], [role='button']") === true) {
        link = node
      }
    }

    if (link !== null && this._skipLinkTargetsMain(link) === true) {
      event.preventDefault()
      this.focusMain()
    }
    return
  }

  /*
   * True when activating `link` should move focus to the main region: it has
   * no href (the built-in link, a button), an empty fragment or the old
   * `#mj-shell-main` target, a fragment that names no element in its tree,
   * or one that names an element inside the main content. A fragment for an
   * element elsewhere, or a link to another page, is left to the browser.
   */
  _skipLinkTargetsMain(link) {
    let targetsMain = true

    const href = link.getAttribute("href")
    if (href !== null) {
      if (href.startsWith("#") === false) {
        targetsMain = false
      } else if (href.length > 1 && href !== "#mj-shell-main") {
        let id = href.substring(1)
        try {
          id = decodeURIComponent(id)
        } catch (error) {
          /* A malformed escape: look the raw text up instead. */
        }
        const root = link.getRootNode()
        const target = typeof root.getElementById === "function" ? root.getElementById(id) : null
        if (target !== null) {
          targetsMain = composedContains(this._mainEl, target)
        }
      }
    }

    return targetsMain
  }

  /* The built-in skip link has no href, so Enter does not click it by itself. */
  _onSkipLinkKeydown(event) {
    if (event.key === "Enter" && event.defaultPrevented === false) {
      event.preventDefault()
      this.focusMain()
    }
    return
  }

  _onMainScroll() {
    if (this._mainScrollFrame !== null) {
      return
    }
    this._mainScrollFrame = requestAnimationFrame(() => {
      this._mainScrollFrame = null
      this.emit("mj-shell-main-scroll", {
        scrollTop: this._mainEl.scrollTop,
        scrollLeft: this._mainEl.scrollLeft
      })
    })
    return
  }

  /* ----- keyboard: Escape and F6 ----- */

  _onDocumentKeydown(event) {
    if (event.key === "Escape") {
      if (event.defaultPrevented === false && this._modalName !== null) {
        event.preventDefault()
        this._closeModal()
      }
    } else if (event.key === "F6") {
      const plain = event.ctrlKey === false && event.altKey === false && event.metaKey === false
      if (plain === true && event.defaultPrevented === false) {
        this._onPanelKey(event)
      }
    }
    return
  }

  /*
   * Every part of the layout that can hold focus, in visual order. `stop`
   * marks the regions F6 can move to right now; the dock and the separator
   * handles are not F6 regions, but they still tell where focus is, so F6
   * from one of them moves on to the region beyond it.
   */
  _panelSequence() {
    const navReachable =
      this.hasAttribute("nav-open") === true || this._effectiveNavMode() === "collapsible"
    const candidates = [
      { region: this._appBarEl, name: t("mj.appShell.appBarLabel"), reachable: true },
      { region: this._dockEl, name: "", reachable: false },
      { region: this._navEl, name: this._navLabel(), reachable: navReachable },
      { region: this._resizers.nav.handle, name: "", reachable: false },
      { region: this._mainEl, name: t("mj.appShell.mainLabel"), reachable: true },
      { region: this._resizers.split.handle, name: "", reachable: false },
      { region: this._secondaryEl, name: t("mj.appShell.secondaryLabel"), reachable: true },
      { region: this._resizers.inspector.handle, name: "", reachable: false },
      { region: this._inspectorEl, name: this._inspectorLabel(), reachable: this.hasAttribute("inspector-open") },
      { region: this._statusBarEl, name: this._statusBarLabel(), reachable: true }
    ]

    for (let index = 0; index < candidates.length; index = index + 1) {
      const candidate = candidates[index]
      candidate.stop = candidate.reachable === true && candidate.region.hidden === false
    }
    return candidates
  }

  /*
   * F6 / Shift+F6: move focus to the next / previous region, counted from the
   * part of the layout that holds focus (from outside every region: the first
   * / last one). The key is left to the browser when focus is in some other
   * part of the page, while a drawer is modal, or when there is nowhere to go.
   */
  _onPanelKey(event) {
    const active = deepActiveElement()
    const nothingFocused =
      active === null || active === document.body || active === document.documentElement
    const insideShell = nothingFocused === false && composedContains(this, active) === true

    if (this._modalName !== null || (insideShell === false && nothingFocused === false)) {
      return
    }

    const sequence = this._panelSequence()
    const stopCount = sequence.filter((entry) => entry.stop === true).length

    let position = -1
    if (insideShell === true) {
      for (let index = 0; index < sequence.length && position < 0; index = index + 1) {
        if (composedContains(sequence[index].region, active) === true) {
          position = index
        }
      }
    }

    const onStop = position >= 0 && sequence[position].stop === true
    if (stopCount === 0 || (onStop === true && stopCount < 2)) {
      return
    }

    /* From outside every part, the first step lands on the first (or last) entry. */
    const step = event.shiftKey === true ? -1 : 1
    let index = position
    if (position < 0) {
      index = step > 0 ? -1 : sequence.length
    }

    let target = null
    for (let moved = 0; moved < sequence.length && target === null; moved = moved + 1) {
      index = (index + step + sequence.length) % sequence.length
      if (sequence[index].stop === true && index !== position) {
        target = sequence[index]
      }
    }

    if (target !== null) {
      event.preventDefault()
      target.region.focus()
      announce(t("mj.appShell.focusMoved", { name: target.name }), "polite")
    }
    return
  }

  /* ----- resizable regions ----- */

  /*
   * One descriptor per separator. `unit` is "px" (the region's width) or
   * "ratio" (the primary pane's share of the split main area); `growsToward`
   * is the inline direction in which moving the handle enlarges the value.
   */
  _buildResizers() {
    this._resizers = {
      nav: {
        name: "nav",
        handle: this.$(".nav-handle"),
        target: this._navEl,
        unit: "px",
        attribute: "nav-size",
        property: "--mj-shell-nav-current",
        storageSuffix: "nav-size",
        eventName: "mj-shell-nav-resize",
        limits: NAV_SIZE_LIMITS,
        growsToward: "end",
        label: t("mj.appShell.resizeNav"),
        timer: null
      },
      inspector: {
        name: "inspector",
        handle: this.$(".inspector-handle"),
        target: this._inspectorEl,
        unit: "px",
        attribute: "inspector-size",
        property: "--mj-shell-inspector-current",
        storageSuffix: "inspector-size",
        eventName: "mj-shell-inspector-resize",
        limits: INSPECTOR_SIZE_LIMITS,
        growsToward: "start",
        label: t("mj.appShell.resizeInspector"),
        timer: null
      },
      split: {
        name: "split",
        handle: this.$(".pane-handle"),
        target: this._workspaceEl,
        unit: "ratio",
        attribute: "split-ratio",
        property: "--mj-shell-split-current",
        storageSuffix: "split-ratio",
        eventName: "mj-shell-split-resize",
        limits: SPLIT_RATIO_LIMITS,
        growsToward: "end",
        label: t("mj.appShell.resizePanes"),
        timer: null
      }
    }

    const names = Object.keys(this._resizers)
    for (let index = 0; index < names.length; index = index + 1) {
      const resizer = this._resizers[names[index]]
      resizer.handle.setAttribute("aria-label", resizer.label)
      this.listen(resizer.handle, "keydown", this._onHandleKeydown.bind(this, resizer))
      this.listen(resizer.handle, "pointerdown", this._onHandlePointerDown.bind(this, resizer))
      this.listen(resizer.handle, "pointermove", this._onHandlePointerMove.bind(this, resizer))
      this.listen(resizer.handle, "pointerup", this._onHandlePointerEnd.bind(this, resizer))
      this.listen(resizer.handle, "pointercancel", this._onHandlePointerEnd.bind(this, resizer))
    }
    return
  }

  /* The `storage-key` prefix in the markup, or the default one. */
  _requestedStoragePrefix() {
    const prefix = this.getAttribute("storage-key") || "mj-app-shell"
    return prefix
  }

  _storageKey(resizer) {
    const prefix = this._storagePrefix !== null ? this._storagePrefix : this._requestedStoragePrefix()
    const key = `${prefix}-${resizer.storageSuffix}`
    return key
  }

  _readStoredSize(resizer) {
    let stored = null
    try {
      stored = parseNumber(window.localStorage.getItem(this._storageKey(resizer)))
    } catch (error) {
      /* localStorage unavailable (private mode): fall back to the attributes. */
      stored = null
    }
    return stored
  }

  _writeStoredSize(resizer, value) {
    try {
      window.localStorage.setItem(this._storageKey(resizer), String(value))
    } catch (error) {
      /* localStorage unavailable or full: the size simply is not persisted. */
    }
    return
  }

  /*
   * Establish the region sizes: a size the user stored earlier wins over the
   * `nav-size` / `inspector-size` / `split-ratio` attribute. Runs once; after
   * a re-render the sizes already held in `_sizes` are applied again. The
   * attribute text seen here is recorded, so its replay after the first
   * render (see MjElement) is not mistaken for a change.
   */
  _restoreSizes() {
    const names = Object.keys(this._resizers)

    if (this._sizesRestored === false) {
      this._storagePrefix = this._requestedStoragePrefix()
    }

    for (let index = 0; index < names.length; index = index + 1) {
      const resizer = this._resizers[names[index]]

      if (this._sizesRestored === false) {
        const attributeText = this.getAttribute(resizer.attribute)
        this._appliedSizeAttributes[resizer.name] = attributeText

        let initial = this._readStoredSize(resizer)
        if (initial === null) {
          initial = parseNumber(attributeText)
        }
        this._sizes[resizer.name] = initial !== null ? this._clampSize(resizer, initial) : null
      }

      this._applySize(resizer)
    }

    this._sizesRestored = true
    return
  }

  /*
   * `storage-key` changed after the first render: settle what is pending
   * under the old prefix, then take the sizes stored under the new one. A
   * region with nothing stored there keeps its current size, which is
   * stored under the new prefix with the next resize.
   */
  _switchStoragePrefix() {
    const requested = this._requestedStoragePrefix()
    if (this._sizesRestored === false || requested === this._storagePrefix) {
      return
    }

    this._flushResizers()
    this._storagePrefix = requested

    const names = Object.keys(this._resizers)
    for (let index = 0; index < names.length; index = index + 1) {
      const resizer = this._resizers[names[index]]
      const stored = this._readStoredSize(resizer)
      if (stored !== null) {
        this._sizes[resizer.name] = this._clampSize(resizer, stored)
        this._applySize(resizer)
      }
    }

    this._syncHandles()
    return
  }

  /* The allowed range of a resizer's value at the current shell width. */
  _sizeBounds(resizer) {
    const bounds = { min: resizer.limits.min, max: resizer.limits.max }

    if (resizer.unit === "px" && this._shellWidth > 0) {
      const share = Math.round(this._shellWidth * MAX_REGION_SHARE)
      bounds.max = Math.max(bounds.min, Math.min(bounds.max, share))
    }

    return bounds
  }

  _clampSize(resizer, value) {
    const bounds = this._sizeBounds(resizer)
    let clamped = Math.min(bounds.max, Math.max(bounds.min, value))

    if (resizer.unit === "px") {
      clamped = Math.round(clamped)
    } else {
      clamped = Math.round(clamped * 1000) / 1000
    }

    return clamped
  }

  /*
   * The value a resizer has right now: the explicit size, else what CSS
   * produced, kept inside the range allowed at the current shell width.
   */
  _currentSize(resizer) {
    let size = this._sizes[resizer.name]

    if (size === null) {
      if (resizer.unit === "px") {
        const measured = resizer.target.getBoundingClientRect().width
        size = measured > 0 ? Math.round(measured) : resizer.limits.fallback
      } else {
        size = resizer.limits.fallback
      }
    }

    const bounds = this._sizeBounds(resizer)
    size = Math.min(bounds.max, Math.max(bounds.min, size))
    return size
  }

  /* Write the explicit size (or its absence) to the shadow DOM. */
  _applySize(resizer) {
    const size = this._sizes[resizer.name]

    if (size === null) {
      resizer.target.style.removeProperty(resizer.property)
    } else if (resizer.unit === "px") {
      resizer.target.style.setProperty(resizer.property, `${size}px`)
    } else {
      resizer.target.style.setProperty(resizer.property, String(size))
    }
    return
  }

  /* Refresh the separator's value attributes for assistive technology. */
  _syncHandle(resizer) {
    const handle = resizer.handle
    const bounds = this._sizeBounds(resizer)
    const size = this._currentSize(resizer)

    if (resizer.unit === "px") {
      handle.setAttribute("aria-valuemin", String(bounds.min))
      handle.setAttribute("aria-valuemax", String(bounds.max))
      handle.setAttribute("aria-valuenow", String(size))
      handle.setAttribute("aria-valuetext", t("mj.appShell.sizePixels", { count: size }))
    } else {
      const percent = Math.round(size * 100)
      handle.setAttribute("aria-valuemin", String(Math.round(bounds.min * 100)))
      handle.setAttribute("aria-valuemax", String(Math.round(bounds.max * 100)))
      handle.setAttribute("aria-valuenow", String(percent))
      handle.setAttribute("aria-valuetext", t("mj.appShell.sizePercent", { count: percent }))
    }
    return
  }

  _syncHandles() {
    if (this._resizers === null) {
      return
    }
    const names = Object.keys(this._resizers)
    for (let index = 0; index < names.length; index = index + 1) {
      const resizer = this._resizers[names[index]]
      if (resizer.handle.hidden === false) {
        this._syncHandle(resizer)
      }
    }
    return
  }

  /*
   * Set a region size on the user's behalf: clamp it, show it, and -- once it
   * has stopped changing -- persist it and report it.
   */
  _resizeTo(resizer, value) {
    const clamped = this._clampSize(resizer, value)

    if (clamped !== this._sizes[resizer.name]) {
      this._sizes[resizer.name] = clamped
      this._applySize(resizer)
      this._syncHandle(resizer)

      if (resizer.timer !== null) {
        window.clearTimeout(resizer.timer)
      }
      resizer.timer = window.setTimeout(() => {
        resizer.timer = null
        this._commitSize(resizer)
      }, RESIZE_SETTLE_MS)
    }
    return
  }

  _commitSize(resizer) {
    const size = this._sizes[resizer.name]
    if (size !== null) {
      this._writeStoredSize(resizer, size)
      const detail = resizer.unit === "px" ? { size: size } : { ratio: size }
      this.emit(resizer.eventName, detail)
    }
    return
  }

  /* On teardown: persist a size that was still waiting for its settle timer. */
  _flushResizers() {
    if (this._resizers === null) {
      return
    }
    const names = Object.keys(this._resizers)
    for (let index = 0; index < names.length; index = index + 1) {
      const resizer = this._resizers[names[index]]
      if (resizer.timer !== null) {
        window.clearTimeout(resizer.timer)
        resizer.timer = null
        const size = this._sizes[resizer.name]
        if (size !== null) {
          this._writeStoredSize(resizer, size)
        }
      }
    }
    return
  }

  /*
   * An author changed `nav-size` / `inspector-size` / `split-ratio`. The
   * text already taken into account (the markup value replayed after the
   * first render, which `_restoreSizes` weighed against the stored size) is
   * not applied again.
   */
  _applySizeAttribute(resizer) {
    const attributeText = this.getAttribute(resizer.attribute)
    if (attributeText === this._appliedSizeAttributes[resizer.name]) {
      return
    }
    this._appliedSizeAttributes[resizer.name] = attributeText

    const requested = parseNumber(attributeText)
    this._sizes[resizer.name] = requested !== null ? this._clampSize(resizer, requested) : null
    this._applySize(resizer)
    if (resizer.handle.hidden === false) {
      this._syncHandle(resizer)
    }
    return
  }

  /*
   * How far the value changes when the handle moves one px toward the
   * physical right: +1 or -1 for px resizers, scaled by the split width for
   * the ratio. Accounts for the text direction.
   */
  _valuePerPixel(resizer) {
    const rightToLeft = getComputedStyle(this).direction === "rtl"
    let sign = resizer.growsToward === "end" ? 1 : -1
    if (rightToLeft === true) {
      sign = -1 * sign
    }

    let scale = 1
    if (resizer.unit === "ratio") {
      const extent = resizer.target.getBoundingClientRect().width
      scale = extent > 0 ? 1 / extent : 0
    }

    const perPixel = sign * scale
    return perPixel
  }

  _resizeStep() {
    const raw = getComputedStyle(this).getPropertyValue("--mj-shell-split-step")
    const parsed = parseLength(raw)
    const step = parsed !== null && parsed > 0 ? parsed : DEFAULT_RESIZE_STEP_PX
    return step
  }

  _onHandleKeydown(resizer, event) {
    const bounds = this._sizeBounds(resizer)
    let next = null

    if (event.key === "ArrowLeft") {
      next = this._currentSize(resizer) - this._resizeStep() * this._valuePerPixel(resizer)
    } else if (event.key === "ArrowRight") {
      next = this._currentSize(resizer) + this._resizeStep() * this._valuePerPixel(resizer)
    } else if (event.key === "Home") {
      next = bounds.min
    } else if (event.key === "End") {
      next = bounds.max
    }

    if (next !== null) {
      event.preventDefault()
      event.stopPropagation()
      this._resizeTo(resizer, next)
    }
    return
  }

  _onHandlePointerDown(resizer, event) {
    if (event.button !== 0) {
      return
    }

    event.preventDefault()
    resizer.handle.focus()
    try {
      resizer.handle.setPointerCapture(event.pointerId)
    } catch (error) {
      /* Synthetic pointers cannot be captured; the drag still works. */
    }

    resizer.handle.setAttribute("resizing", "")
    resizer.target.classList.add("no-motion")
    this._drag = {
      resizer: resizer,
      pointerId: event.pointerId,
      startX: event.clientX,
      startSize: this._currentSize(resizer),
      valuePerPixel: this._valuePerPixel(resizer)
    }
    return
  }

  _onHandlePointerMove(resizer, event) {
    const drag = this._drag
    if (drag === null || drag.resizer !== resizer || drag.pointerId !== event.pointerId) {
      return
    }
    const moved = event.clientX - drag.startX
    this._resizeTo(resizer, drag.startSize + moved * drag.valuePerPixel)
    return
  }

  _onHandlePointerEnd(resizer, event) {
    const drag = this._drag
    if (drag === null || drag.resizer !== resizer) {
      return
    }

    this._drag = null
    resizer.handle.removeAttribute("resizing")
    resizer.target.classList.remove("no-motion")
    try {
      resizer.handle.releasePointerCapture(event.pointerId)
    } catch (error) {
      /* Nothing was captured. */
    }
    return
  }

  /* ----- attributes ----- */

  /*
   * Report an open-state change through its toggle event, once per actual
   * change. Attribute writes that leave the state as it was (and the replay
   * of the initial attributes) report nothing.
   */
  _reportOpen(name, eventName) {
    const attribute = name === "nav" ? "nav-open" : "inspector-open"
    const open = this.hasAttribute(attribute)

    if (open !== this._reportedOpen[name]) {
      this._reportedOpen[name] = open
      this.emit(eventName, { open: open })
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._navEl === undefined || this._navEl === null) {
      return
    }

    if (name === "nav-open" || name === "inspector-open") {
      /* A narrow shell shows one drawer at a time. */
      if (newValue !== null && this._narrow === true) {
        const other = name === "nav-open" ? "inspector-open" : "nav-open"
        if (this.hasAttribute(other) === true) {
          this.removeAttribute(other)
        }
      }

      this._syncLayout()
      if (this._modeSettled === true) {
        this._syncModal(true)
      }

      if (name === "nav-open") {
        this._reportOpen("nav", "mj-shell-nav-toggle")
      } else {
        this._reportOpen("inspector", "mj-shell-inspector-toggle")
      }
    } else if (name === "nav-mode") {
      this._syncLayout()
      if (this._modeSettled === true) {
        this._syncModal(false)
      }
    } else if (name === "nav-size") {
      this._applySizeAttribute(this._resizers.nav)
    } else if (name === "inspector-size") {
      this._applySizeAttribute(this._resizers.inspector)
    } else if (name === "split-ratio") {
      this._applySizeAttribute(this._resizers.split)
    } else if (name === "storage-key") {
      this._switchStoragePrefix()
    } else if (
      name === "split" || name === "nav-label" || name === "inspector-label" ||
      name === "status-bar-label" || name === "hide-nav-toggle"
    ) {
      this._syncLayout()
    }

    return
  }

  /* ----- scriptable API ----- */

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

  /* True while the shell is below the nav breakpoint (drawers instead of columns). */
  get narrow() {
    return this._narrow
  }

  /*
   * True when the shell has navigation that can be opened and closed right
   * now: the narrow layout, or `nav-mode` overlay / collapsible. This is
   * where the built-in toggle is offered (unless `hide-nav-toggle`); an
   * `mj-app-bar` standing in for that toggle can read it.
   */
  get navToggleable() {
    let toggleable = false
    if (this._mainEl !== null && this._mainEl !== undefined) {
      const hasNav = this._assigned("workspace").length + this._assigned("nav").length > 0
      const mode = this._effectiveNavMode()
      toggleable = hasNav === true && (mode === "overlay" || mode === "collapsible")
    }
    return toggleable
  }

  toggleNav() {
    this.navOpen = !this.navOpen
    return
  }

  toggleInspector() {
    this.inspectorOpen = !this.inspectorOpen
    return
  }

  /*
   * The main region: the element that scrolls the main content and the
   * target of the skip link. It is focusable (tabindex="-1").
   */
  get mainRegion() {
    return this._mainEl
  }

  /* Move focus to the main region, as the built-in skip link does. */
  focusMain() {
    if (this._mainEl !== null && this._mainEl !== undefined) {
      this._mainEl.focus()
    }
    return
  }

  get navPanel() {
    const assigned = this._assigned("nav")
    const panel = assigned.length > 0 ? assigned[0] : null
    return panel
  }

  get inspectorPanel() {
    const assigned = this._assigned("inspector")
    const panel = assigned.length > 0 ? assigned[0] : null
    return panel
  }
}
