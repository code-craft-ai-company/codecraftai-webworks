/*
 * mjappbar.js
 *
 * <mj-app-bar> -- top-of-page navigation and branding bar.
 * Renders a <header role="banner"> landmark with brand, nav, and actions slots.
 * A page has one banner: a bar inside a landmark or a sectioning element
 * (article, aside, main, nav, section, a dialog) -- including the region an
 * enclosing <mj-app-shell> made the banner -- is not the page banner, and of
 * the other bars only the first one connected is, unless the page already
 * has a banner of its own. A bar that is not the banner renders its
 * <header> with role="none".
 * Handles responsive collapse to a mobile drawer on narrow viewports: below
 * the collapse breakpoint the `navigation` slot is re-parented into the
 * drawer (unless `mobile-navigation` content overrides it), so the same
 * light-DOM links are reachable in both layouts.
 *
 * WAI-ARIA: header role="banner"; nav aria-label; toggle aria-expanded/aria-controls;
 * the open drawer is a modal dialog holding a labelled nav.
 *
 * Inside an <mj-app-shell> that has navigation of its own (`nav` or
 * `workspace` content) the shell owns the navigation: the bar's toggle calls
 * `shell.toggleNav()` and mirrors `shell.navOpen` in its aria-expanded and
 * label, and the bar's own drawer never opens. The cancelable
 * mj-app-bar-open / mj-app-bar-close events still fire first. Set
 * `hide-nav-toggle` on the shell to use the bar's toggle instead of the
 * shell's own: the bar's toggle replaces the shell's, so it is shown exactly
 * when the shell hides its own (`hide-nav-toggle`) and the shell's nav can be
 * opened and closed (the shell is narrow, or its `nav-mode` is `overlay` or
 * `collapsible`) -- whether or not the bar has navigation of its own. The
 * bar's own `navigation` links stay in the bar at every width (scrolling
 * inline when they do not fit), because the drawer they would collapse into
 * is never opened.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { trapFocus, flatParent } from "../core/focustrap.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";

/* Viewport widths (px) of the named `collapse-breakpoint` values. */
const COLLAPSE_BREAKPOINTS = { sm: 640, md: 768, lg: 1024 };
const DEFAULT_COLLAPSE_BREAKPOINT = 768;
const DEFAULT_SCROLL_THRESHOLD = 16;

/*
 * Ancestors inside which a <header> is not the page banner: sectioning
 * content, every landmark (a banner must be top level) and dialogs.
 */
const BANNER_SCOPE_SELECTOR = [
  "article", "aside", "main", "nav", "section", "header", "footer", "dialog",
  "[role='article']", "[role='banner']", "[role='complementary']", "[role='contentinfo']",
  "[role='main']", "[role='navigation']", "[role='region']", "[role='search']", "[role='form']",
  "[role='dialog']", "[role='alertdialog']"
].join(", ");

/* The connected bars, in the order they were connected. */
const connectedBars = [];

/*
 * True when no flat-tree ancestor of `element` (crossing slots and shadow
 * roots) is a landmark, a sectioning element or a dialog.
 */
function isAtPageLevel(element) {
  let pageLevel = true
  let ancestor = flatParent(element)

  while (ancestor !== null && pageLevel === true) {
    if (ancestor.matches(BANNER_SCOPE_SELECTOR) === true) {
      pageLevel = false
    }
    ancestor = flatParent(ancestor)
  }
  return pageLevel
}

/* True when the page's light DOM already has a banner outside every app bar. */
function pageHasOwnBanner() {
  let found = false
  const candidates = document.querySelectorAll("header, [role='banner']")

  for (let index = 0; index < candidates.length && found === false; index = index + 1) {
    const candidate = candidates[index]
    const role = candidate.getAttribute("role")
    const isBanner = role === null || role === "banner"
    if (isBanner === true && candidate.closest("mj-app-bar") === null && isAtPageLevel(candidate) === true) {
      found = true
    }
  }
  return found
}

/*
 * Give the banner landmark to one bar: the first connected bar at page
 * level, unless the page has a banner of its own. Every other bar renders a
 * plain header. Run whenever a bar is connected or removed and whenever an
 * enclosing shell's layout changes.
 */
function syncBannerLandmarks() {
  let bannerTaken = pageHasOwnBanner()

  for (let index = 0; index < connectedBars.length; index = index + 1) {
    const bar = connectedBars[index]
    const isBanner = bannerTaken === false && isAtPageLevel(bar) === true
    bar._applyBannerRole(isBanner)
    if (isBanner === true) {
      bannerTaken = true
    }
  }
  return
}

const STYLES = `
:host {
  display: block;
  position: relative;
  z-index: var(--mj-app-bar-z-index, var(--mj-layer-sticky));
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
:host([compact]) .root,
:host([variant="compact"]) .root {
  height: var(--mj-app-bar-height-compact, 40px);
  padding-inline: var(--mj-app-bar-padding-inline, var(--mj-space-4));
  gap: var(--mj-space-3);
  font-size: var(--mj-font-size-sm);
}
:host([variant="floating"]) .root {
  margin: var(--mj-space-3);
  border-radius: var(--mj-radius-lg);
  box-shadow: var(--mj-app-bar-elevation, var(--mj-elevation-3));
}
:host([transparent]) .root,
:host([variant="transparent"]) .root { background: transparent; box-shadow: none; }
:host([transparent][scrolled]) .root,
:host([variant="transparent"][scrolled]) .root {
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

/*
 * The drawer and its backdrop exist only in the collapsed layout. A closed
 * drawer is moved off-screen toward the inline start AND made invisible, so
 * its content leaves the tab order and the accessibility tree.
 */
.drawer {
  display: none;
  position: fixed;
  inset-block: 0;
  inset-inline-start: 0;
  width: min(280px, 85vw);
  background: var(--mj-surface);
  box-shadow: var(--mj-elevation-3);
  z-index: var(--mj-layer-modal);
  transform: translateX(-100%);
  visibility: hidden;
  transition: transform var(--mj-motion-medium) var(--mj-motion-ease),
              visibility 0s linear var(--mj-motion-medium);
  overflow-y: auto;
  padding: var(--mj-space-5);
}
:host(:dir(rtl)) .drawer { transform: translateX(100%); }
.drawer-nav { display: flex; flex-direction: column; gap: var(--mj-space-3); }

.backdrop {
  display: none;
  position: fixed;
  inset: 0;
  background: var(--mj-overlay-scrim);
  z-index: calc(var(--mj-layer-modal) - 1);
}

.root[data-collapsed] .nav { display: none; }
.root[data-collapsed] .toggle { display: flex; }

/*
 * Inside a shell that owns the navigation the bar's links never move into
 * the drawer: they stay in the bar and scroll inline when they do not fit.
 * The toggle (driving the shell's nav) is shown or hidden by _syncLayout.
 */
.root[data-shell] .nav {
  display: flex;
  min-inline-size: 0;
  overflow-x: auto;
}
.root[data-shell] .toggle { display: flex; }
.drawer[data-collapsed] { display: block; }
:host([open]) .drawer[data-collapsed] {
  transform: translateX(0);
  visibility: visible;
  transition-delay: 0s;
}
:host([open]) .backdrop[data-collapsed] { display: block; }

/* No navigation slotted: no empty nav landmark, no drawer toggle. */
.nav[hidden],
.toggle[hidden],
.drawer[hidden],
.backdrop[hidden] { display: none !important; }
`;

export class MjAppBar extends MjElement {
  static tagName = "mj-app-bar";
  static styles = STYLES;
  static watched = [
    "open", "sticky", "transparent", "scrolled", "nav-label", "scroll-threshold",
    "collapse-breakpoint", "variant", "compact"
  ];

  constructor() {
    super()
    this._drawerId = nextId("mj-appbar-drawer")
    this._disposeTrap = null

    /* True while the viewport is narrower than the collapse breakpoint. */
    this._collapsed = false
    this._disposeBreakpoint = null

    /* The document overflow value replaced by the scroll lock, or null when not locked. */
    this._lockedOverflow = null
  }

  render() {
    const navLabel = this._resolveNavLabel()

    const markup = html`
      <header class="root" part="root">
        <div class="brand" part="brand"><slot name="brand"></slot></div>
        <nav class="nav" part="nav" aria-label="${navLabel}">
          <slot name="navigation"></slot>
        </nav>
        <div class="actions" part="actions"><slot name="actions"></slot></div>
        <button class="toggle" part="toggle" type="button"
          aria-expanded="false"
          aria-controls="${this._drawerId}"
          aria-label="${t("mj.appBar.openNav")}">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <rect y="3" width="20" height="2" rx="1"/>
            <rect y="9" width="20" height="2" rx="1"/>
            <rect y="15" width="20" height="2" rx="1"/>
          </svg>
        </button>
      </header>
      <div class="backdrop" part="backdrop" aria-hidden="true"></div>
      <div class="drawer" part="drawer" id="${this._drawerId}"
           role="dialog" aria-modal="true" aria-label="${navLabel}">
        <nav class="drawer-nav" aria-label="${navLabel}">
          <slot name="mobile-navigation"></slot>
        </nav>
      </div>
    `
    return markup
  }

  afterRender() {
    this._root = this.$(".root")
    this._toggle = this.$(".toggle")
    this._drawer = this.$(".drawer")
    this._drawerNav = this.$(".drawer-nav")
    this._backdrop = this.$(".backdrop")
    this._navEl = this.$(".nav")
    this._navigationSlot = this.$("slot[name='navigation']")
    this._mobileSlot = this.$("slot[name='mobile-navigation']")

    this.listen(this._toggle, "click", this._onToggleClick.bind(this))
    this.listen(this._backdrop, "click", this._onBackdropClick.bind(this))
    this.listen(this, "keydown", this._onKeydown.bind(this))

    this.listen(this._navigationSlot, "slotchange", this._syncLayout.bind(this))
    this.listen(this._mobileSlot, "slotchange", this._syncLayout.bind(this))

    connectedBars.push(this)

    this._watchShell()
    this._watchBreakpoint()
    this._setupScrollSpy()
    this._syncLayout()

    /*
     * Components around this one may give an ancestor its landmark role
     * after this bar rendered (they are registered later): decide the
     * banner once more when they have rendered.
     */
    let landmarkFrame = requestAnimationFrame(() => {
      landmarkFrame = null
      syncBannerLandmarks()
    })

    this.onTeardown(() => {
      if (landmarkFrame !== null) {
        cancelAnimationFrame(landmarkFrame)
        landmarkFrame = null
      }
      const position = connectedBars.indexOf(this)
      if (position >= 0) {
        connectedBars.splice(position, 1)
      }
      syncBannerLandmarks()
      this._stopWatchingBreakpoint()
      this._releaseDrawer(false)
    })
    return
  }

  /* Render the header as the banner landmark, or as a plain header (see syncBannerLandmarks). */
  _applyBannerRole(isBanner) {
    if (this._root !== undefined && this._root !== null) {
      this._root.setAttribute("role", isBanner === true ? "banner" : "none")
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._toggle === undefined || this._toggle === null) {
      return
    }

    if (name === "open") {
      this._syncOpen()
    } else if (name === "nav-label") {
      const navLabel = this._resolveNavLabel()
      this._navEl.setAttribute("aria-label", navLabel)
      this._drawer.setAttribute("aria-label", navLabel)
      this._drawerNav.setAttribute("aria-label", navLabel)
    } else if (name === "collapse-breakpoint") {
      this._watchBreakpoint()
      this._syncLayout()
    } else if (name === "scroll-threshold") {
      this._syncScrolled(false)
    }
    return
  }

  _resolveNavLabel() {
    let navLabel = this.getAttribute("nav-label")
    if (navLabel === null || navLabel.length === 0) {
      navLabel = t("mj.appBar.navLabel")
    }
    return navLabel
  }

  /* The collapse breakpoint in px: a named size (sm/md/lg) or a pixel number. */
  _breakpointPx() {
    let pixels = DEFAULT_COLLAPSE_BREAKPOINT
    const value = this.getAttribute("collapse-breakpoint")

    if (value !== null) {
      const named = COLLAPSE_BREAKPOINTS[value.trim().toLowerCase()]
      const parsed = parseInt(value, 10)
      if (named !== undefined) {
        pixels = named
      } else if (Number.isNaN(parsed) === false && parsed > 0) {
        pixels = parsed
      }
    }
    return pixels
  }

  /* Track the viewport against the collapse breakpoint. */
  _watchBreakpoint() {
    this._stopWatchingBreakpoint()

    const query = window.matchMedia(`not all and (min-width: ${this._breakpointPx()}px)`)
    const onChange = () => {
      this._collapsed = query.matches
      this._syncLayout()
    }
    query.addEventListener("change", onChange)
    this._disposeBreakpoint = () => {
      query.removeEventListener("change", onChange)
    }

    this._collapsed = query.matches
    return
  }

  _stopWatchingBreakpoint() {
    if (this._disposeBreakpoint !== null) {
      this._disposeBreakpoint()
      this._disposeBreakpoint = null
    }
    return
  }

  /*
   * Follow an enclosing <mj-app-shell>: its nav toggle event (the toggle's
   * aria-expanded), its `narrow` / `nav-mode` / `hide-nav-toggle` attributes
   * (whether the bar's toggle is wanted) and its children (whether it has
   * navigation of its own). The shell is registered after this element, so
   * the layout is synced once more when it has been.
   */
  _watchShell() {
    const shellHost = this.closest("mj-app-shell")
    if (shellHost === null) {
      return
    }

    this.listen(shellHost, "mj-shell-nav-toggle", this._syncOpen.bind(this))

    const observer = new MutationObserver(() => {
      this._syncLayout()
    })
    observer.observe(shellHost, {
      attributes: true,
      attributeFilter: ["narrow", "nav-mode", "hide-nav-toggle"],
      childList: true
    })
    this.onTeardown(() => {
      observer.disconnect()
    })

    if (customElements.get("mj-app-shell") === undefined) {
      customElements.whenDefined("mj-app-shell").then(() => {
        if (this.isConnected === true && this._toggle !== undefined && this._toggle !== null) {
          this._syncLayout()
        }
      })
    }
    return
  }

  /*
   * Whether the bar shows its toggle for the shell: the bar's toggle stands
   * in for the shell's own, so it is wanted when the shell hides its own
   * (`hide-nav-toggle`) and the shell's nav can be opened and closed
   * (`shell.navToggleable`: the shell is narrow, or its nav-mode is
   * `overlay` or `collapsible`). Never two toggles for one nav.
   */
  _shellWantsBarToggle(shell) {
    const wanted = shell.navToggleable === true && shell.hasAttribute("hide-nav-toggle") === true
    return wanted
  }

  /*
   * Apply the collapsed / expanded layout and the presence of navigation.
   *
   * The nav landmark, the mobile drawer, and its toggle exist only for
   * slotted navigation. Without any, they are hidden so the bar exposes no
   * empty navigation landmark and no toggle that opens an empty drawer.
   *
   * A slot can project its content in one place only, so the single
   * `navigation` slot lives in the bar while expanded and is moved into the
   * drawer while collapsed -- unless `mobile-navigation` content is supplied,
   * which then is what the drawer shows.
   *
   * Inside a shell that owns the navigation there is no drawer and no
   * collapsed layout: the `navigation` slot stays in the bar, and the toggle
   * (which drives the shell's nav) stands in for the shell's own toggle.
   *
   * The banner landmark is decided again first: an enclosing shell's
   * changes (which also land here) can move the bar in or out of a landmark.
   */
  _syncLayout() {
    syncBannerLandmarks()

    const navigation = this.querySelectorAll(":scope > [slot='navigation']").length > 0
    const mobileNavigation = this.querySelectorAll(":scope > [slot='mobile-navigation']").length > 0
    const shell = this._owningShell()
    const shellMode = shell !== null
    const hasDrawerContent = shellMode === false && (navigation === true || mobileNavigation === true)
    const collapsed = this._collapsed === true && shellMode === false

    const slotBelongsInDrawer = collapsed === true && mobileNavigation === false
    const slotHome = slotBelongsInDrawer === true ? this._drawerNav : this._navEl
    if (this._navigationSlot.parentNode !== slotHome) {
      slotHome.appendChild(this._navigationSlot)
    }

    let toggleWanted = hasDrawerContent
    if (shellMode === true) {
      toggleWanted = this._shellWantsBarToggle(shell)
    }

    this._navEl.hidden = navigation === false
    this._toggle.hidden = toggleWanted === false
    this._drawer.hidden = hasDrawerContent === false
    this._backdrop.hidden = hasDrawerContent === false

    this._root.toggleAttribute("data-shell", shellMode)
    this._root.toggleAttribute("data-collapsed", collapsed)
    this._drawer.toggleAttribute("data-collapsed", collapsed)
    this._backdrop.toggleAttribute("data-collapsed", collapsed)

    this._syncOpen()
    return
  }

  /*
   * Reflect `open` onto the toggle and make the drawer modal while it is
   * actually showing (open, collapsed layout, something to show). Safe to
   * call repeatedly: the focus trap and scroll lock are taken only once.
   */
  _syncOpen() {
    const shell = this._owningShell()
    if (shell !== null) {
      /* The shell's nav panel lives in another shadow tree: no aria-controls. */
      const shellOpen = shell.navOpen === true
      this._toggle.removeAttribute("aria-controls")
      this._toggle.setAttribute("aria-expanded", shellOpen === true ? "true" : "false")
      this._toggle.setAttribute("aria-label", shellOpen === true ? t("mj.appBar.closeNav") : t("mj.appBar.openNav"))
      this._releaseDrawer(false)
      return
    }

    const open = this.hasAttribute("open")
    this._toggle.setAttribute("aria-controls", this._drawerId)
    this._toggle.setAttribute("aria-expanded", open === true ? "true" : "false")
    this._toggle.setAttribute("aria-label", open === true ? t("mj.appBar.closeNav") : t("mj.appBar.openNav"))

    const drawerShowing = open === true && this._collapsed === true && this._drawer.hidden === false

    if (drawerShowing === true) {
      if (this._disposeTrap === null) {
        this._lockedOverflow = document.documentElement.style.overflow
        document.documentElement.style.overflow = "hidden"
        this._disposeTrap = trapFocus(this._drawer)
      }
    } else {
      this._releaseDrawer(open === false)
    }
    return
  }

  /* Drop the focus trap and the page scroll lock taken by an open drawer. */
  _releaseDrawer(focusToggle) {
    if (this._disposeTrap !== null) {
      this._disposeTrap({ restoreFocus: false })
      this._disposeTrap = null
      if (focusToggle === true) {
        this._toggle.focus()
      }
    }

    if (this._lockedOverflow !== null) {
      document.documentElement.style.overflow = this._lockedOverflow
      this._lockedOverflow = null
    }
    return
  }

  _scrollThreshold() {
    let threshold = DEFAULT_SCROLL_THRESHOLD
    const parsed = parseInt(this.getAttribute("scroll-threshold"), 10)
    if (Number.isNaN(parsed) === false && parsed >= 0) {
      threshold = parsed
    }
    return threshold
  }

  /*
   * How far the content under the bar has scrolled: the window offset, or
   * the offset of the nearest scrolling ancestor when the page scrolls
   * inside an overflow container.
   */
  _scrollOffset() {
    let offset = window.scrollY
    let node = this.parentNode

    while (node !== null && node !== undefined && node !== document) {
      if (node instanceof ShadowRoot) {
        node = node.host
      } else {
        if (node instanceof Element && node.scrollTop > offset) {
          offset = node.scrollTop
        }
        node = node.parentNode
      }
    }
    return offset
  }

  _syncScrolled(announce) {
    const wasScrolled = this.hasAttribute("scrolled")
    const offset = this._scrollOffset()
    const isScrolled = offset > this._scrollThreshold()

    if (isScrolled !== wasScrolled) {
      this.reflectBoolean("scrolled", isScrolled)
      if (announce === true) {
        this.emit("mj-app-bar-scroll", { scrolled: isScrolled, scrollY: offset })
      }
    }
    return
  }

  /*
   * Scroll events do not bubble, but a capturing listener on the window sees
   * the scroll of every container in the document, so a bar inside an
   * overflow container is tracked as well. The state is computed once at
   * setup: a page restored at a scrolled position starts `scrolled`.
   */
  _setupScrollSpy() {
    const onScroll = () => {
      this._syncScrolled(true)
    }
    this.listen(window, "scroll", onScroll, { passive: true, capture: true })
    this._syncScrolled(false)
    return
  }

  /*
   * The enclosing <mj-app-shell> when it has navigation of its own (see the
   * header), else null.
   */
  _owningShell() {
    let shell = null
    const candidate = this.closest("mj-app-shell")
    if (candidate !== null && typeof candidate.toggleNav === "function") {
      const shellNav = candidate.querySelector(":scope > [slot='nav'], :scope > [slot='workspace']")
      if (shellNav !== null) {
        shell = candidate
      }
    }
    return shell
  }

  _onToggleClick() {
    const shell = this._owningShell()
    if (shell !== null) {
      const eventName = shell.navOpen === true ? "mj-app-bar-close" : "mj-app-bar-open"
      const proceed = this.emit(eventName, {}, { cancelable: true })
      if (proceed === true) {
        shell.toggleNav()
        this._syncOpen()
      }
      return
    }

    const open = this.hasAttribute("open")
    if (open === false) {
      const proceed = this.emit("mj-app-bar-open", {}, { cancelable: true })
      if (proceed === true) {
        this.setAttribute("open", "")
      }
    } else {
      const proceed = this.emit("mj-app-bar-close", {}, { cancelable: true })
      if (proceed === true) {
        this.removeAttribute("open")
      }
    }
    return
  }

  _onBackdropClick() {
    const proceed = this.emit("mj-app-bar-close", {}, { cancelable: true })
    if (proceed === true) {
      this.removeAttribute("open")
    }
    return
  }

  _onKeydown(event) {
    if (event.key === "Escape" && this.hasAttribute("open") === true) {
      const proceed = this.emit("mj-app-bar-close", {}, { cancelable: true })
      if (proceed === true) {
        this.removeAttribute("open")
      }
    }
    return
  }

  get open() {
    return this.hasAttribute("open")
  }

  set open(value) {
    this.reflectBoolean("open", value === true)
    return
  }

  get scrolled() {
    return this.hasAttribute("scrolled")
  }

  get drawerElement() {
    return this._drawer || null
  }
}
