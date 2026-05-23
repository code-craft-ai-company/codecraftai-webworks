/*
 * mjappshell.js
 *
 * <mj-app-shell> -- outermost layout frame composing AppBar, SideNav, main
 * content area, inspector panel, and StatusBar into correct landmark structure.
 * Supports panel persistence, responsive collapse, and keyboard panel cycling.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { trapFocus } from "../core/focustrap.js";
import { announce } from "../core/announcer.js";

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

header.app-bar {
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

nav.side-nav {
  grid-area: nav;
  width: var(--mj-shell-nav-width, 240px);
  overflow: hidden auto;
  border-inline-end: 1px solid var(--mj-border);
  background: var(--mj-surface);
  transition: width var(--mj-motion-medium) var(--mj-motion-ease);
  position: relative;
}

:host([nav-mode="overlay"]) nav.side-nav {
  position: fixed;
  inset-block: 0;
  inset-inline-start: 0;
  z-index: var(--mj-layer-overlay);
  width: var(--mj-shell-nav-width, 240px);
  transform: translateX(-100%);
  transition: transform var(--mj-motion-medium) var(--mj-motion-ease);
  box-shadow: var(--mj-elevation-3);
}

:host([nav-mode="overlay"][nav-open]) nav.side-nav {
  transform: translateX(0);
}

:host(:not([nav-open])) nav.side-nav {
  width: 0;
}

:host([nav-mode="collapsible"]:not([nav-open])) nav.side-nav {
  width: var(--mj-shell-dock-width, 48px);
}

main.main-area {
  grid-area: main;
  overflow: auto;
  background: var(--mj-bg);
  min-width: 0;
  min-height: 0;
}

aside.inspector {
  grid-area: inspector;
  width: var(--mj-shell-inspector-width, 320px);
  overflow: hidden auto;
  border-inline-start: 1px solid var(--mj-border);
  background: var(--mj-surface);
  transition: width var(--mj-motion-medium) var(--mj-motion-ease);
}

:host(:not([inspector-open])) aside.inspector {
  width: 0;
  overflow: hidden;
}

footer.status-bar {
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

export class MjAppShell extends MjElement {
  static tagName = "mj-app-shell";
  static styles = STYLES;
  static watched = [
    "nav-open", "nav-mode", "inspector-open",
    "inspector-size", "nav-size", "storage-key", "split"
  ];

  constructor() {
    super()
    this._trapDispose = null
    this._resizeObserver = null
    this._inspectorDragActive = false
    this._panelNames = ["app-bar", "nav", "main", "inspector", "status-bar"]
    this._panelFocusIndex = 0
  }

  render() {
    const navLabel = this.getAttribute("nav-label") || "Primary navigation"
    const inspectorLabel = this.getAttribute("inspector-label") || "Inspector"
    const markup = `
      <div class="overlay-backdrop" part="backdrop"></div>
      <header class="app-bar" part="app-bar">
        <slot name="app-bar"></slot>
      </header>
      <div class="dock" part="dock">
        <slot name="dock"></slot>
      </div>
      <nav class="side-nav" part="nav" aria-label="${navLabel}" id="mj-shell-nav">
        <slot name="workspace"></slot>
        <slot name="nav"></slot>
      </nav>
      <main class="main-area" part="main" id="mj-shell-main">
        <slot></slot>
        <slot name="main"></slot>
      </main>
      <aside class="inspector" part="inspector" aria-label="${inspectorLabel}" id="mj-shell-inspector">
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
    this._navEl = this.$("nav.side-nav")
    this._mainEl = this.$("main.main-area")
    this._inspectorEl = this.$("aside.inspector")

    this._restoreSizes()

    this.listen(this._backdrop, "click", this._onBackdropClick.bind(this))
    this.listen(this, "keydown", this._onKeydown.bind(this))

    if (typeof ResizeObserver === "function") {
      this._resizeObserver = new ResizeObserver(this._onResize.bind(this))
      this._resizeObserver.observe(this)
      this.onTeardown(() => {
        if (this._resizeObserver !== null) {
          this._resizeObserver.disconnect()
          this._resizeObserver = null
        }
      })
    }

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

  _onBackdropClick() {
    this.navOpen = false
    return
  }

  _onKeydown(event) {
    if (event.key === "F6") {
      event.preventDefault()
      this._cycleFocus()
    } else if (event.key === "Escape") {
      const navMode = this.getAttribute("nav-mode") || "static"
      if (navMode === "overlay" && this.hasAttribute("nav-open")) {
        this.navOpen = false
      }
    }
    return
  }

  _cycleFocus() {
    const panels = [
      this.$("header.app-bar"),
      this._navEl,
      this._mainEl,
      this._inspectorEl,
      this.$("footer.status-bar")
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

  _onResize(entries) {
    for (let i = 0; i < entries.length; i = i + 1) {
      const width = entries[i].contentRect.width
      const breakpoint = 768
      if (width < breakpoint) {
        this.setAttribute("nav-mode", "overlay")
      } else {
        const currentMode = this.getAttribute("nav-mode") || "static"
        if (currentMode === "overlay") {
          this.setAttribute("nav-mode", "static")
        }
      }
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "nav-open") {
      const open = newValue !== null
      if (open === true && this.getAttribute("nav-mode") === "overlay") {
        if (this._trapDispose !== null) {
          this._trapDispose()
          this._trapDispose = null
        }
        const navEl = this._navEl
        if (navEl !== null) {
          this._trapDispose = trapFocus(navEl)
          this.onTeardown(() => {
            if (this._trapDispose !== null) {
              this._trapDispose()
              this._trapDispose = null
            }
          })
        }
      } else {
        if (this._trapDispose !== null) {
          this._trapDispose()
          this._trapDispose = null
        }
      }
      this.emit("mj-shell-nav-toggle", { open: open })
    }

    if (name === "inspector-open") {
      const open = newValue !== null
      this.emit("mj-shell-inspector-toggle", { open: open })
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
