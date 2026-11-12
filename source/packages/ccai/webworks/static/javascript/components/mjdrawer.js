/*
 * mjdrawer.js
 *
 * <mj-drawer> -- edge-anchored sliding panel. Supports start/end/top/bottom
 * edges, modal (focus trap + backdrop + inert background) and non-modal
 * modes, and drag-to-dismiss for the bottom-sheet variant.
 *
 * A closed drawer is inert and hidden, so its content is neither focusable
 * nor exposed to assistive technology. An open modal drawer is shown in the
 * top layer above its <mj-overlay> backdrop.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";
import { trapFocus, deepActiveElement, flatContains } from "../core/focustrap.js";
import { pushLayer, removeLayer, claimEscape, topModalSurface } from "../core/overlay.js";

/* Fraction of the panel height a drag must cover to dismiss the sheet. */
const SWIPE_DISMISS_THRESHOLD = 0.4;

const STYLES = `
:host {
  display: contents;
}

/*
 * Closed state. The panel is moved off its edge AND hidden: "visibility"
 * waits for the slide-out to finish, then takes the panel out of hit
 * testing and the tab order. The open state below has NO transform or
 * translate, so position: fixed popups opened inside the panel are not
 * positioned against it.
 */
.panel {
  position: fixed;
  z-index: var(--mj-layer-modal);
  box-sizing: border-box;
  margin: 0;
  padding: 0;
  border: 0 none;
  background: var(--mj-surface);
  color: var(--mj-text);
  box-shadow: var(--mj-drawer-shadow, var(--mj-elevation-3));
  display: flex;
  flex-direction: column;
  outline: none;
  visibility: hidden;
  transition: translate var(--mj-motion-medium) var(--mj-motion-ease),
              visibility 0s linear var(--mj-motion-medium);
}

/* Inline-end edge (the default). */
:host(:not([edge])) .panel,
:host([edge="end"]) .panel {
  inset-block: 0;
  inset-inline: auto 0;
  inline-size: var(--mj-drawer-size, var(--mj-drawer-attribute-size, 20rem));
  max-inline-size: 90vw;
  block-size: 100dvh;
  border-inline-start: 1px solid var(--mj-border);
  border-start-start-radius: var(--mj-drawer-radius, var(--mj-radius-lg));
  border-end-start-radius: var(--mj-drawer-radius, var(--mj-radius-lg));
  translate: 110% 0;
}

/* Inline-start edge. */
:host([edge="start"]) .panel {
  inset-block: 0;
  inset-inline: 0 auto;
  inline-size: var(--mj-drawer-size, var(--mj-drawer-attribute-size, 20rem));
  max-inline-size: 90vw;
  block-size: 100dvh;
  border-inline-end: 1px solid var(--mj-border);
  border-start-end-radius: var(--mj-drawer-radius, var(--mj-radius-lg));
  border-end-end-radius: var(--mj-drawer-radius, var(--mj-radius-lg));
  translate: -110% 0;
}

/*
 * In a right-to-left document the inline edges swap sides, so the closed
 * panel has to leave in the opposite physical direction.
 */
:host(:dir(rtl):not([edge])) .panel { translate: -110% 0; }
:host(:dir(rtl)[edge="end"]) .panel { translate: -110% 0; }
:host(:dir(rtl)[edge="start"]) .panel { translate: 110% 0; }

:host([edge="top"]) .panel {
  inset-inline: 0;
  inset-block: 0 auto;
  block-size: var(--mj-drawer-size, var(--mj-drawer-attribute-size, 20rem));
  max-block-size: 90dvh;
  inline-size: 100%;
  border-block-end: 1px solid var(--mj-border);
  border-end-start-radius: var(--mj-drawer-radius, var(--mj-radius-lg));
  border-end-end-radius: var(--mj-drawer-radius, var(--mj-radius-lg));
  translate: 0 -110%;
}

:host([edge="bottom"]) .panel {
  inset-inline: 0;
  inset-block: auto 0;
  block-size: var(--mj-drawer-size, var(--mj-drawer-attribute-size, 20rem));
  max-block-size: 90dvh;
  inline-size: 100%;
  border-block-start: 1px solid var(--mj-border);
  border-start-start-radius: var(--mj-drawer-radius, var(--mj-radius-lg));
  border-start-end-radius: var(--mj-drawer-radius, var(--mj-radius-lg));
  translate: 0 110%;
}

/* Open state -- slide in. Listed last so it wins over every edge rule. */
:host([open]) .panel,
:host([open]:not([edge])) .panel,
:host([open][edge]) .panel {
  translate: none;
  visibility: visible;
  transition: translate var(--mj-motion-medium) var(--mj-motion-ease),
              visibility 0s;
}

/* The sheet follows the finger directly while it is being dragged. */
.panel[data-dragging] {
  transition: none;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--mj-space-4) var(--mj-drawer-padding, var(--mj-space-5));
  border-block-end: 1px solid var(--mj-border);
  flex-shrink: 0;
}

.title {
  font-size: var(--mj-font-size-lg);
  font-weight: var(--mj-font-weight-bold);
  margin: 0;
  flex: 1;
}

.close-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: var(--mj-radius-md);
  cursor: pointer;
  color: var(--mj-text-muted);
  font-size: var(--mj-font-size-lg);
  line-height: 1;
}

.close-btn:hover { background: var(--mj-bg-muted); color: var(--mj-text); }
.close-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

:host([no-close-button]) .close-btn { display: none; }

.body {
  flex: 1;
  min-block-size: 0;
  overflow-y: auto;
  padding: var(--mj-drawer-padding, var(--mj-space-5));
}

.footer {
  flex-shrink: 0;
  padding: var(--mj-space-4) var(--mj-drawer-padding, var(--mj-space-5));
  border-block-start: 1px solid var(--mj-border);
}

.footer[hidden] { display: none; }

.drag-handle {
  display: flex;
  justify-content: center;
  padding: var(--mj-space-2) 0 var(--mj-space-1);
  cursor: grab;
  flex-shrink: 0;
  touch-action: none;
}

.drag-handle-bar {
  width: 2.5rem;
  height: 0.25rem;
  background: var(--mj-border-strong);
  border-radius: var(--mj-radius-pill);
}

:host(:not([edge="bottom"])) .drag-handle { display: none; }

@media (prefers-reduced-motion: reduce) {
  .panel,
  :host([open]) .panel { transition: none; }
}
`;

export class MjDrawer extends MjElement {
  static tagName = "mj-drawer";
  static styles = STYLES;
  static watched = [
    "open", "edge", "modal", "size", "label", "close-label",
    "close-on-backdrop", "no-close-button"
  ];

  constructor() {
    super()
    this._panel = null
    this._footer = null
    this._closeBtn = null
    this._overlay = null
    this._layer = null
    this._trapDispose = null
    this._titleId = nextId("mj-drawer-title")
    this._onOverlayClickBound = this._onOverlayClick.bind(this)

    /* True from a successful open until the close has completed. */
    this._isOpen = false

    /* How the drawer is currently open: true with backdrop and focus trap. */
    this._openedModal = false

    /* Drag-to-dismiss state of the bottom sheet. */
    this._dragStartY = null
    this._dragPointerId = null
    this._dragProgress = 0

    this.returnFocusEl = null
  }

  render() {
    const markup = html`
      <div class="panel" part="panel" tabindex="-1" inert>
        <div class="drag-handle" part="drag-handle" aria-hidden="true">
          <slot name="drag-handle"><div class="drag-handle-bar"></div></slot>
        </div>
        <div class="header" part="header">
          <slot name="header">
            <span id="${this._titleId}" class="title" part="title"><slot name="title"></slot></span>
            <button class="close-btn" part="close-button" type="button">&#x2715;</button>
          </slot>
        </div>
        <div class="body" part="body"><slot></slot></div>
        <div class="footer" part="footer"><slot name="footer"></slot></div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._panel = this.$(".panel")
    this._footer = this.$(".footer")
    this._closeBtn = this.$(".close-btn")

    this.listen(this._closeBtn, "click", () => this._closeDrawer("close-button"))
    this.listen(this._panel, "keydown", this._onKeydown.bind(this))

    const footerSlot = this.$("slot[name='footer']")
    this.listen(footerSlot, "slotchange", this._syncFooter.bind(this))

    const handle = this.$(".drag-handle")
    this.listen(handle, "pointerdown", this._onHandlePointerDown.bind(this))
    this.listen(handle, "pointermove", this._onHandlePointerMove.bind(this))
    this.listen(handle, "pointerup", this._onHandlePointerUp.bind(this))
    this.listen(handle, "pointercancel", this._onHandlePointerUp.bind(this))

    this._applyLabels()
    this._applySemantics()
    this._applySize()
    this._syncFooter()

    if (this.hasAttribute("open") === true) {
      this._openDrawer()
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._panel === undefined || this._panel === null) {
      return
    }

    if (name === "open") {
      if (newValue !== null) {
        this._openDrawer()
      } else if (this._isOpen === true) {
        const closed = this._closeDrawer("api")
        if (closed === false) {
          /* The close was vetoed: the attribute must keep matching reality. */
          this.setAttribute("open", "")
        }
      }
    } else if (name === "modal") {
      this._applyModalMode()
    } else if (name === "label" || name === "close-label") {
      this._applyLabels()
    } else if (name === "size") {
      this._applySize()
    }
    return
  }

  onDisconnected() {
    /* Removed while open: release everything without events or refocus. */
    if (this._isOpen === true) {
      this._leaveOpenState()
      this._isOpen = false
    }
    return
  }

  _edge() {
    const edge = this.getAttribute("edge") || "end"
    return edge
  }

  /* ----- attribute-driven rendering ----- */

  _applyLabels() {
    const label = this.getAttribute("label") || ""
    if (label.length > 0) {
      this._panel.setAttribute("aria-label", label)
      this._panel.removeAttribute("aria-labelledby")
    } else {
      this._panel.removeAttribute("aria-label")
      this._panel.setAttribute("aria-labelledby", this._titleId)
    }

    this._closeBtn.setAttribute("aria-label", this.getAttribute("close-label") || t("core.close"))
    return
  }

  /*
   * A modal drawer is a dialog; a non-modal one is a complementary region
   * beside the page and must not claim `aria-modal`, which tells assistive
   * technology to ignore everything else.
   */
  _applySemantics() {
    const modal = this.getAttribute("modal") !== "false"
    this._panel.setAttribute("role", modal === true ? "dialog" : "complementary")

    if (modal === true) {
      this._panel.setAttribute("aria-modal", "true")
    } else {
      this._panel.removeAttribute("aria-modal")
    }
    return
  }

  /* `size` sets the panel width (start/end) or height (top/bottom). */
  _applySize() {
    const size = this.getAttribute("size")
    const valid = size !== null && size.trim().length > 0 && CSS.supports("width", size) === true
    if (valid === true) {
      this._panel.style.setProperty("--mj-drawer-attribute-size", size)
    } else {
      this._panel.style.removeProperty("--mj-drawer-attribute-size")
    }
    return
  }

  /* The footer bar shows only when something is slotted into it. */
  _syncFooter() {
    const footerSlot = this.$("slot[name='footer']")
    const hasSlotted = footerSlot !== null && footerSlot.assignedNodes().length > 0
    this._footer.hidden = hasSlotted === false
    return
  }

  /* `modal` changed while open: add or drop backdrop, inert and focus trap. */
  _applyModalMode() {
    const wantsModal = this.getAttribute("modal") !== "false"
    if (this._isOpen === true && wantsModal !== this._openedModal) {
      this._leaveOpenState()
      this._enterOpenState()
    } else {
      this._applySemantics()
    }
    return
  }

  /* ----- open / close ----- */

  _openDrawer() {
    if (this._panel === null || this._isOpen === true || this.isConnected === false) {
      return
    }

    if (this.returnFocusEl === null) {
      this.returnFocusEl = this._resolveReturnFocus()
    }

    this._isOpen = true
    this._enterOpenState()

    this.emit("mj-drawer-open", { edge: this._edge() })
    return
  }

  _resolveReturnFocus() {
    let target = null

    const returnId = this.getAttribute("return-focus-id")
    if (returnId !== null && returnId.length > 0) {
      target = document.getElementById(returnId)
    }
    if (target === null) {
      target = deepActiveElement()
    }
    return target
  }

  _enterOpenState() {
    const modal = this.getAttribute("modal") !== "false"
    this._openedModal = modal
    this._panel.removeAttribute("inert")
    this._applySemantics()

    if (modal === true) {
      this._showOverlay()
      this._layer = pushLayer({
        surface: this._panel,
        modal: true,
        onEscape: () => {
          this._closeDrawer("escape")
        }
      })
      this._trapDispose = trapFocus(this._panel, this.querySelector("[autofocus]"), { contain: true })
    } else {
      /* Beside the page: Escape closes it only while focus is inside. */
      this._layer = pushLayer({ surface: this._panel, modal: false })
      this._panel.focus()
    }
    return
  }

  _leaveOpenState() {
    if (this._layer !== null) {
      removeLayer(this._layer)
      this._layer = null
    }

    if (this._trapDispose !== null) {
      /* Focus is restored by the caller, once nothing is inert any more. */
      this._trapDispose({ restoreFocus: false })
      this._trapDispose = null
    }

    this._hideOverlay()

    if (this._panel !== null) {
      this._panel.setAttribute("inert", "")
      this._panel.removeAttribute("data-dragging")
      this._panel.style.translate = ""
    }
    this._dragStartY = null
    this._dragPointerId = null
    this._dragProgress = 0
    return
  }

  /*
   * Close the drawer. Returns true when it closed and false when it was not
   * open or a `mj-drawer-before-close` listener vetoed the close.
   */
  _closeDrawer(reason) {
    if (this._panel === null || this._isOpen === false) {
      return false
    }

    const proceed = this.emit("mj-drawer-before-close", { reason: reason }, { cancelable: true })
    if (proceed === false) {
      return false
    }

    this._isOpen = false
    this._leaveOpenState()
    this._applySemantics()

    if (this.hasAttribute("open") === true) {
      this.removeAttribute("open")
    }

    const restoreEl = this.returnFocusEl
    this.returnFocusEl = null
    if (restoreEl !== null && restoreEl.isConnected === true && typeof restoreEl.focus === "function") {
      restoreEl.focus()
    }

    this.emit("mj-drawer-close", {
      edge: this._edge(),
      reason: reason
    })
    return true
  }

  /*
   * The backdrop. <mj-overlay> dims the page, makes everything except the
   * panel inert, locks scrolling and stacks backdrop and panel in the top
   * layer. It is appended inside the modal surface the drawer sits in, when
   * there is one, because content outside a modal is inert.
   */
  _showOverlay() {
    if (this._overlay !== null) {
      return
    }

    const overlay = document.createElement("mj-overlay")
    overlay.surface = this._panel
    overlay.setAttribute("top-layer", "")
    overlay.setAttribute("visible", "")
    overlay.addEventListener("mj-overlay-click", this._onOverlayClickBound)

    const modalSurface = topModalSurface()
    const insideModal = modalSurface !== null && flatContains(modalSurface, this) === true
    const container = insideModal === true ? modalSurface : document.body
    container.appendChild(overlay)

    this._overlay = overlay
    return
  }

  _hideOverlay() {
    if (this._overlay === null) {
      return
    }

    const overlay = this._overlay
    this._overlay = null
    overlay.removeEventListener("mj-overlay-click", this._onOverlayClickBound)

    if (typeof overlay.retire === "function") {
      overlay.retire()
    } else {
      overlay.remove()
    }
    return
  }

  _onOverlayClick(event) {
    /* A listener that cancelled the click vetoes the dismissal. */
    if (event.defaultPrevented === true) {
      return
    }
    if (this.getAttribute("close-on-backdrop") !== "false") {
      this._closeDrawer("backdrop")
    }
    return
  }

  _onKeydown(event) {
    if (event.key === "Escape") {
      /*
       * One Escape closes one thing: a popup open inside the panel, or a
       * layer above it, goes first and the drawer stays.
       */
      const mine = claimEscape(event, this._layer)
      event.preventDefault()
      if (mine === true) {
        this._closeDrawer("escape")
      }
    }
    return
  }

  /* ----- drag to dismiss (bottom sheet) ----- */

  _onHandlePointerDown(event) {
    const draggable = this._isOpen === true &&
      this._edge() === "bottom" &&
      this.getAttribute("swipe-to-dismiss") !== "false"
    if (draggable === false) {
      return
    }

    this._dragStartY = event.clientY
    this._dragPointerId = event.pointerId
    this._dragProgress = 0
    this._panel.setAttribute("data-dragging", "")

    if (typeof event.currentTarget.setPointerCapture === "function") {
      try {
        event.currentTarget.setPointerCapture(event.pointerId)
      } catch (error) {
        /* The pointer is already gone; the drag simply will not track. */
      }
    }
    return
  }

  _onHandlePointerMove(event) {
    if (this._dragStartY === null || event.pointerId !== this._dragPointerId) {
      return
    }

    const deltaY = Math.max(0, event.clientY - this._dragStartY)
    const panelHeight = this._panel.offsetHeight
    this._dragProgress = panelHeight > 0 ? Math.min(deltaY / panelHeight, 1) : 0
    this._panel.style.translate = `0 ${deltaY}px`
    this.emit("mj-drawer-swipe", { progress: this._dragProgress })
    return
  }

  _onHandlePointerUp(event) {
    if (this._dragStartY === null || event.pointerId !== this._dragPointerId) {
      return
    }

    const progress = this._dragProgress
    this._dragStartY = null
    this._dragPointerId = null
    this._dragProgress = 0
    this._panel.removeAttribute("data-dragging")
    this._panel.style.translate = ""

    if (event.type === "pointerup" && progress > SWIPE_DISMISS_THRESHOLD) {
      this._closeDrawer("swipe")
    }
    return
  }

  /* Scriptable API */

  get open() {
    return this.hasAttribute("open")
  }

  set open(value) {
    this.reflectBoolean("open", value === true)
    return
  }

  get panelEl() {
    return this._panel
  }

  /* 0-1 progress of an active drag on the bottom sheet's handle. */
  get dragProgress() {
    return this._dragProgress
  }

  show() {
    this.setAttribute("open", "")
    return
  }

  close() {
    this._closeDrawer("api")
    return
  }
}
