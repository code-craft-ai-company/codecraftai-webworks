/*
 * mjsidenav.js
 *
 * <mj-side-nav> -- side navigation panel.
 * Supports static, collapsible, and overlay-drawer modes.
 * Renders as a <nav aria-label> landmark with roving tabindex for items.
 *
 * A collapsed `collapsible` nav shrinks to a narrow rail that still shows the
 * toggle button, so it can always be expanded again. An open `overlay-drawer`
 * is a modal dialog: focus is trapped, the page behind is inert and does not
 * scroll.
 *
 * WAI-ARIA: nav landmark; aria-expanded on the toggle; aria-current="page" on
 * the active item; role="dialog" aria-modal="true" on an open overlay drawer.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { RovingTabindex, trapFocus } from "../core/focustrap.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";

const STYLES = `
:host {
  display: block;
  position: relative;
}
.root {
  position: relative;
  width: var(--mj-side-nav-width, 240px);
  background: var(--mj-side-nav-bg, var(--mj-surface));
  height: 100%;
  display: flex;
  flex-direction: column;
}
.panel {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

/* collapsible: the panel hides, the root shrinks to a rail holding the toggle. */
:host([mode="collapsible"]) .root {
  overflow: hidden;
  transition: width var(--mj-side-nav-transition-duration, var(--mj-motion-medium)) var(--mj-motion-ease);
}
:host([mode="collapsible"]:not([open])) .root {
  width: var(--mj-side-nav-collapsed-width, var(--mj-target-min));
}
:host([mode="collapsible"]) .panel {
  transition: visibility 0s linear 0s;
}
:host([mode="collapsible"]:not([open])) .panel {
  visibility: hidden;
  transition-delay: var(--mj-side-nav-transition-duration, var(--mj-motion-medium));
}

/*
 * overlay-drawer: a closed drawer sits off-screen past its own edge and is
 * invisible, which also takes its items out of the tab order.
 */
:host([mode="overlay-drawer"]) .root {
  position: fixed;
  inset-block: 0;
  inset-inline-start: 0;
  height: auto;
  box-shadow: var(--mj-elevation-3);
  z-index: var(--mj-side-nav-z-index, var(--mj-layer-modal));
  transform: translateX(-100%);
  visibility: hidden;
  transition: transform var(--mj-side-nav-transition-duration, var(--mj-motion-medium)) var(--mj-motion-ease),
              visibility 0s linear var(--mj-side-nav-transition-duration, var(--mj-motion-medium));
}
:host([edge="end"][mode="overlay-drawer"]) .root {
  inset-inline-start: auto;
  inset-inline-end: 0;
  transform: translateX(100%);
}
:host([mode="overlay-drawer"]:dir(rtl)) .root { transform: translateX(100%); }
:host([edge="end"][mode="overlay-drawer"]:dir(rtl)) .root { transform: translateX(-100%); }
:host([mode="overlay-drawer"][open]) .root {
  transform: translateX(0);
  visibility: visible;
  transition-delay: 0s;
}

.backdrop {
  display: none;
  position: fixed;
  inset: 0;
  background: var(--mj-overlay-scrim);
  z-index: calc(var(--mj-side-nav-z-index, var(--mj-layer-modal)) - 1);
}
:host([mode="overlay-drawer"][open]) .backdrop { display: block; }

.header-area { padding: var(--mj-space-4); flex-shrink: 0; }
.nav-list { margin: 0; padding: var(--mj-space-2) 0; flex: 1; overflow-y: auto; }
.footer-area { padding: var(--mj-space-4); border-block-start: 1px solid var(--mj-border); flex-shrink: 0; }

.toggle-btn {
  display: none;
  align-items: center; justify-content: flex-end;
  flex-shrink: 0;
  width: 100%; min-height: var(--mj-target-min);
  padding: var(--mj-space-2) var(--mj-space-4);
  background: none; border: none; cursor: pointer;
  color: var(--mj-text-muted); font: inherit;
  border-block-start: 1px solid var(--mj-border);
}
:host([mode="collapsible"]) .toggle-btn { display: flex; }
:host([mode="collapsible"]:not([open])) .toggle-btn { justify-content: center; padding-inline: 0; }
.toggle-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: calc(0px - var(--mj-focus-ring-width));
}
/* The chevron points toward the direction the panel will move. */
:host([open]) .toggle-btn svg { transform: scaleX(-1); }
:host(:dir(rtl)) .toggle-btn svg { transform: scaleX(-1); }
:host([open]:dir(rtl)) .toggle-btn svg { transform: none; }

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

/* Slotted elements the roving tabindex manages; anything else is left alone. */
const NAV_ITEM_SELECTOR = "a[href], button, [role='link'], [role='button'], [tabindex]";

export class MjSideNav extends MjElement {
  static tagName = "mj-side-nav";
  static styles = STYLES;
  static watched = ["mode", "open", "edge", "nav-label", "persist-state", "persist-key"];

  constructor() {
    super()
    this._panelId = nextId("mj-side-nav-panel")
    this._disposeTrap = null
    this._roving = null

    /* Page elements made inert by an open overlay drawer. */
    this._inertedElements = []

    /* The document overflow value replaced by the scroll lock, or null when not locked. */
    this._lockedOverflow = null
  }

  render() {
    /*
     * The toggle is always rendered (CSS shows it in collapsible mode only)
     * and sits outside the collapsing panel, so a `mode` change after the
     * first render needs no re-render and a collapsed nav keeps its toggle.
     */
    const markup = html`
      <div class="backdrop" part="backdrop" aria-hidden="true"></div>
      <nav class="root" part="root" aria-label="${this._resolveNavLabel()}">
        <div class="panel" id="${this._panelId}">
          <div class="header-area" part="header"><slot name="header"></slot></div>
          <div class="nav-list" part="nav-list">
            <slot></slot>
          </div>
          <div class="footer-area" part="footer"><slot name="footer"></slot></div>
        </div>
        <button class="toggle-btn" part="toggle" type="button"
                aria-controls="${this._panelId}" aria-expanded="false">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
            <path d="M5 2L11 8L5 14" stroke="currentColor" stroke-width="1.5"
                  fill="none" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </nav>
    `
    return markup
  }

  afterRender() {
    this._nav = this.$(".root")
    this._backdrop = this.$(".backdrop")
    this._toggleBtn = this.$(".toggle-btn")
    this._navList = this.$(".nav-list")
    this._itemSlot = this.$("slot:not([name])")

    this._roving = new RovingTabindex({ items: [], orientation: "vertical", wrap: true })

    this.listen(this._backdrop, "click", this._closeDrawer.bind(this))
    this.listen(this, "keydown", this._onKeydown.bind(this))
    this.listen(this._toggleBtn, "click", this._onToggleClick.bind(this))

    /* Roving keys are handled for the item list only, never header or footer content. */
    this.listen(this._navList, "keydown", this._onListKeydown.bind(this))
    this.listen(this._navList, "focusin", this._onListFocusIn.bind(this))
    this.listen(this._itemSlot, "slotchange", this._setupItems.bind(this))

    this.onTeardown(() => {
      this._releaseModal(false)
    })

    this._restorePersistedState()
    this._setupItems()
    this._syncOpen()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._nav === undefined || this._nav === null) {
      return
    }

    if (name === "open") {
      this._syncOpen()
      this._persistState()
    } else if (name === "mode") {
      this._syncOpen()
    } else if (name === "nav-label") {
      this._nav.setAttribute("aria-label", this._resolveNavLabel())
    }
    return
  }

  _resolveNavLabel() {
    let navLabel = this.getAttribute("nav-label")
    if (navLabel === null || navLabel.length === 0) {
      navLabel = t("mj.sideNav.navLabel")
    }
    return navLabel
  }

  _mode() {
    let mode = this.getAttribute("mode")
    if (mode !== "collapsible" && mode !== "overlay-drawer") {
      mode = "static"
    }
    return mode
  }

  /*
   * The navigation items in DOM order: slotted links and buttons, and those
   * nested inside slotted wrappers (groups, list items). Headings, dividers
   * and other non-interactive content are not items.
   */
  _collectItems() {
    const items = []
    const assigned = this._itemSlot.assignedElements({ flatten: true })

    for (let index = 0; index < assigned.length; index = index + 1) {
      const element = assigned[index]
      if (element.matches(NAV_ITEM_SELECTOR) === true) {
        items.push(element)
      } else {
        const nested = element.querySelectorAll(NAV_ITEM_SELECTOR)
        for (let position = 0; position < nested.length; position = position + 1) {
          items.push(nested[position])
        }
      }
    }
    return items
  }

  /* (Re)build the roving item list; runs on first render and on every slot change. */
  _setupItems() {
    const items = this._collectItems()
    const previous = this._roving.items[this._roving.index]

    let activeIndex = items.indexOf(previous)
    if (activeIndex === -1) {
      /* Start on the current page when there is one, otherwise on the first item. */
      activeIndex = 0
      for (let index = 0; index < items.length; index = index + 1) {
        if (items[index].getAttribute("aria-current") === "page") {
          activeIndex = index
          break
        }
      }
    }

    this._roving.index = activeIndex
    this._roving.setItems(items)
    return
  }

  /* Index of the managed item that contains `node`, or -1. */
  _itemIndexOf(node) {
    let found = -1
    const items = this._roving.items

    for (let index = 0; index < items.length; index = index + 1) {
      if (found === -1 && (items[index] === node || items[index].contains(node) === true)) {
        found = index
      }
    }
    return found
  }

  _onListFocusIn(event) {
    /* Keep the roving position in step with focus moved by click or Tab. */
    const index = this._itemIndexOf(event.target)
    if (index >= 0 && index !== this._roving.index) {
      this._roving.index = index
      this._roving.setItems(this._roving.items)
    }
    return
  }

  _onListKeydown(event) {
    const index = this._itemIndexOf(event.target)
    if (index === -1 || event.altKey === true || event.ctrlKey === true || event.metaKey === true) {
      return
    }

    const count = this._roving.items.length
    let next = -1

    if (event.key === "ArrowDown") {
      next = index + 1 >= count ? 0 : index + 1
    } else if (event.key === "ArrowUp") {
      next = index - 1 < 0 ? count - 1 : index - 1
    } else if (event.key === "Home") {
      next = 0
    } else if (event.key === "End") {
      next = count - 1
    }

    if (next >= 0) {
      event.preventDefault()
      this._roving.focus(next)
    }
    return
  }

  /*
   * Bring the toggle and the modal state in line with `open` and `mode`.
   * Safe to call repeatedly: the focus trap is taken once per opening and
   * released when the drawer closes or the mode stops being overlay-drawer.
   */
  _syncOpen() {
    const open = this.hasAttribute("open")
    const mode = this._mode()

    this._toggleBtn.setAttribute("aria-expanded", open === true ? "true" : "false")
    this._toggleBtn.setAttribute(
      "aria-label",
      open === true ? t("mj.sideNav.collapse") : t("mj.sideNav.expand")
    )

    if (mode === "overlay-drawer" && open === true) {
      this._nav.setAttribute("role", "dialog")
      this._nav.setAttribute("aria-modal", "true")
      if (this._disposeTrap === null) {
        this._setBackgroundInert()
        this._lockedOverflow = document.documentElement.style.overflow
        document.documentElement.style.overflow = "hidden"
        this._disposeTrap = trapFocus(this._nav)
      }
    } else {
      this._nav.removeAttribute("role")
      this._nav.removeAttribute("aria-modal")
      this._releaseModal(mode === "overlay-drawer")
    }
    return
  }

  /*
   * Make everything outside this element inert: the siblings of the host and
   * of each of its ancestors up to the document body.
   */
  _setBackgroundInert() {
    let node = this

    while (node !== null && node !== undefined && node !== document.body && node !== document.documentElement) {
      let parent = node.parentNode
      if (parent instanceof ShadowRoot) {
        parent = parent.host
        node = parent
        continue
      }
      if (parent === null || parent === undefined || !(parent instanceof Element)) {
        break
      }

      const siblings = Array.from(parent.children)
      for (let index = 0; index < siblings.length; index = index + 1) {
        const sibling = siblings[index]
        if (sibling !== node && sibling.inert !== true) {
          sibling.inert = true
          this._inertedElements.push(sibling)
        }
      }
      node = parent
    }
    return
  }

  /* Undo everything an open overlay drawer did to the page. */
  _releaseModal(restoreFocus) {
    for (let index = 0; index < this._inertedElements.length; index = index + 1) {
      this._inertedElements[index].inert = false
    }
    this._inertedElements = []

    if (this._lockedOverflow !== null) {
      document.documentElement.style.overflow = this._lockedOverflow
      this._lockedOverflow = null
    }

    if (this._disposeTrap !== null) {
      /* Focus goes back to the opener only now that it is no longer inert. */
      this._disposeTrap({ restoreFocus: restoreFocus })
      this._disposeTrap = null
    }
    return
  }

  _persistEnabled() {
    const enabled = this._mode() === "collapsible" && this.getAttribute("persist-state") !== "false"
    return enabled
  }

  _persistKey() {
    let key = this.getAttribute("persist-key")
    if (key === null || key.length === 0) {
      key = "mj-side-nav"
    }
    return key
  }

  _persistState() {
    if (this._persistEnabled() === true) {
      try {
        localStorage.setItem(this._persistKey(), this.hasAttribute("open") === true ? "open" : "closed")
      } catch (_err) {
        // storage unavailable
      }
    }
    return
  }

  _restorePersistedState() {
    if (this._persistEnabled() === false) {
      return
    }

    let stored = null
    try {
      stored = localStorage.getItem(this._persistKey())
    } catch (_err) {
      // storage unavailable
    }

    if (stored === "open") {
      this.setAttribute("open", "")
    } else if (stored === "closed") {
      this.removeAttribute("open")
    }
    return
  }

  /* Open the nav (expand / show the drawer). Emits the cancelable mj-side-nav-open. */
  show() {
    if (this.hasAttribute("open") === false) {
      const proceed = this.emit("mj-side-nav-open", { mode: this._mode() }, { cancelable: true })
      if (proceed === true) {
        this.setAttribute("open", "")
      }
    }
    return
  }

  /* Close the nav (collapse / hide the drawer). Emits the cancelable mj-side-nav-close. */
  hide() {
    if (this.hasAttribute("open") === true) {
      this._closeDrawer()
    }
    return
  }

  _closeDrawer() {
    const proceed = this.emit("mj-side-nav-close", { mode: this._mode() }, { cancelable: true })
    if (proceed === true) {
      this.removeAttribute("open")
    }
    return
  }

  _onToggleClick() {
    if (this.hasAttribute("open") === true) {
      this.hide()
    } else {
      this.show()
    }
    return
  }

  _onKeydown(event) {
    if (event.key === "Escape") {
      if (this._mode() === "overlay-drawer" && this.hasAttribute("open") === true) {
        this._closeDrawer()
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

  get activeItem() {
    const found = this.querySelector("[aria-current='page']")
    return found
  }

  get items() {
    let items = []
    if (this._itemSlot !== undefined && this._itemSlot !== null) {
      items = this._collectItems()
    }
    return items
  }
}
