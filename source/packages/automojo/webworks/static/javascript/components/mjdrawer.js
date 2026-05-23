/*
 * mjdrawer.js
 *
 * <mj-drawer> -- edge-anchored sliding panel. Supports start/end/top/bottom
 * edges, modal (focus trap + backdrop) and non-modal modes, and swipe-to-
 * dismiss for the bottom-sheet variant.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { trapFocus } from "../core/focustrap.js";

const STYLES = `
:host {
  display: contents;
}

.panel {
  position: fixed;
  z-index: var(--mj-layer-modal);
  background: var(--mj-surface);
  color: var(--mj-text);
  box-shadow: var(--mj-drawer-shadow, var(--mj-elevation-3));
  display: flex;
  flex-direction: column;
  transition: transform var(--mj-motion-medium) var(--mj-motion-ease);
  outline: none;
  overflow: hidden;
}

/* Edge placements */
:host([edge="start"]) .panel, :host(:not([edge])) .panel[data-edge="start"] {
  inset-block: 0; inset-inline-start: 0;
  width: var(--mj-drawer-size, 20rem);
  max-width: 90vw;
  height: 100dvh;
  border-inline-end: 1px solid var(--mj-border);
  border-radius: 0 var(--mj-drawer-radius, var(--mj-radius-lg)) var(--mj-drawer-radius, var(--mj-radius-lg)) 0;
  transform: translateX(-110%);
}

:host([edge="end"]) .panel {
  inset-block: 0; inset-inline-end: 0;
  width: var(--mj-drawer-size, 20rem);
  max-width: 90vw;
  height: 100dvh;
  border-inline-start: 1px solid var(--mj-border);
  border-radius: var(--mj-drawer-radius, var(--mj-radius-lg)) 0 0 var(--mj-drawer-radius, var(--mj-radius-lg));
  transform: translateX(110%);
}

:host(:not([edge])) .panel {
  inset-block: 0; inset-inline-end: 0;
  width: var(--mj-drawer-size, 20rem);
  max-width: 90vw;
  height: 100dvh;
  border-inline-start: 1px solid var(--mj-border);
  border-radius: var(--mj-drawer-radius, var(--mj-radius-lg)) 0 0 var(--mj-drawer-radius, var(--mj-radius-lg));
  transform: translateX(110%);
}

:host([edge="top"]) .panel {
  inset-inline: 0; inset-block-start: 0;
  height: var(--mj-drawer-size, 20rem);
  max-height: 90dvh;
  width: 100%;
  border-block-end: 1px solid var(--mj-border);
  border-radius: 0 0 var(--mj-drawer-radius, var(--mj-radius-lg)) var(--mj-drawer-radius, var(--mj-radius-lg));
  transform: translateY(-110%);
}

:host([edge="bottom"]) .panel {
  inset-inline: 0; inset-block-end: 0;
  height: var(--mj-drawer-size, 20rem);
  max-height: 90dvh;
  width: 100%;
  border-block-start: 1px solid var(--mj-border);
  border-radius: var(--mj-drawer-radius, var(--mj-radius-lg)) var(--mj-drawer-radius, var(--mj-radius-lg)) 0 0;
  transform: translateY(110%);
}

/* Open state — slide in */
:host([open][edge="start"]) .panel,
:host([open]:not([edge])) .panel[data-edge="start"] { transform: translateX(0); }
:host([open][edge="end"]) .panel,
:host([open]:not([edge])) .panel { transform: translateX(0); }
:host([open][edge="top"]) .panel { transform: translateY(0); }
:host([open][edge="bottom"]) .panel { transform: translateY(0); }

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--mj-space-4) var(--mj-drawer-padding, var(--mj-space-5));
  border-bottom: 1px solid var(--mj-border);
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
  overflow-y: auto;
  padding: var(--mj-drawer-padding, var(--mj-space-5));
}

.footer {
  flex-shrink: 0;
  padding: var(--mj-space-4) var(--mj-drawer-padding, var(--mj-space-5));
  border-top: 1px solid var(--mj-border);
}

.footer:empty { display: none; }

.drag-handle {
  display: flex;
  justify-content: center;
  padding: var(--mj-space-2) 0 var(--mj-space-1);
  cursor: grab;
  flex-shrink: 0;
}

.drag-handle-bar {
  width: 2.5rem;
  height: 0.25rem;
  background: var(--mj-border-strong);
  border-radius: var(--mj-radius-pill);
}

:host(:not([edge="bottom"])) .drag-handle { display: none; }

@media (prefers-reduced-motion: reduce) {
  .panel { transition: none; }
}
`;

export class MjDrawer extends MjElement {
  static tagName = "mj-drawer";
  static styles = STYLES;
  static watched = ["open", "edge", "modal", "size", "label", "close-on-backdrop", "no-close-button"];

  constructor() {
    super()
    this._panel = null
    this._overlay = null
    this._trapDispose = null
    this._titleId = nextId("mj-drawer-title")
    this.returnFocusEl = null
    this._touchStartY = null
    this._touchStartX = null
  }

  render() {
    const edge = this.getAttribute("edge") || "end"
    const isModal = this.getAttribute("modal") !== "false"
    const role = isModal === true ? "dialog" : "complementary"
    const ariaModal = isModal === true ? 'aria-modal="true"' : ""
    const label = this.getAttribute("label") || ""
    const labelAttr = label.length > 0
      ? `aria-label="${label}"`
      : `aria-labelledby="${this._titleId}"`
    const closeLabel = this.getAttribute("close-label") || "Close"

    const markup = `
      <div class="panel" part="panel" role="${role}" ${ariaModal} ${labelAttr} tabindex="-1">
        <div class="drag-handle" part="drag-handle" aria-label="Drag to dismiss">
          <slot name="drag-handle"><div class="drag-handle-bar"></div></slot>
        </div>
        <div class="header" part="header">
          <slot name="header">
            <span id="${this._titleId}" class="title" part="title"><slot name="title"></slot></span>
            <button class="close-btn" part="close-button" aria-label="${closeLabel}">&#x2715;</button>
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
    const closeBtn = this.$(".close-btn")

    if (closeBtn !== null) {
      this.listen(closeBtn, "click", () => this._closeDrawer("close-button"))
    }

    this.listen(this._panel, "keydown", this._onKeydown.bind(this))

    const handle = this.$(".drag-handle")
    if (handle !== null) {
      this.listen(handle, "touchstart", this._onTouchStart.bind(this), { passive: true })
      this.listen(handle, "touchmove", this._onTouchMove.bind(this), { passive: true })
      this.listen(handle, "touchend", this._onTouchEnd.bind(this))
    }

    if (this.hasAttribute("open") === true) {
      this._openDrawer("api")
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "open" && this._panel !== null) {
      if (newValue !== null) {
        this._openDrawer("api")
      } else {
        this._closeDrawer("api")
      }
    }
    return
  }

  onDisconnected() {
    this._cleanupTrap()
    this._hideOverlay()
    return
  }

  _openDrawer(reason) {
    if (this._panel === null) {
      return
    }

    this.returnFocusEl = this.returnFocusEl || document.activeElement
    const isModal = this.getAttribute("modal") !== "false"

    if (isModal === true) {
      this._showOverlay()
    }

    if (isModal === true) {
      this._trapDispose = trapFocus(this._panel)
    } else {
      this._panel.focus()
    }

    this.emit("mj-drawer-open", { edge: this.getAttribute("edge") || "end" })
    return
  }

  _closeDrawer(reason) {
    if (this._panel === null) {
      return
    }

    const beforeOk = this.emit("mj-drawer-before-close", { reason: reason }, { cancelable: true })
    if (beforeOk === false) {
      return
    }

    this._cleanupTrap()
    this._hideOverlay()
    this.removeAttribute("open")

    const restoreEl = this.returnFocusEl
    this.returnFocusEl = null
    if (restoreEl !== null && typeof restoreEl.focus === "function") {
      restoreEl.focus()
    }

    this.emit("mj-drawer-close", {
      edge: this.getAttribute("edge") || "end",
      reason: reason
    })
    return
  }

  _cleanupTrap() {
    if (this._trapDispose !== null) {
      this._trapDispose()
      this._trapDispose = null
    }
    return
  }

  _showOverlay() {
    if (this._overlay !== null) {
      return
    }
    const overlay = document.createElement("mj-overlay")
    overlay.setAttribute("visible", "")
    this.listen(overlay, "mj-overlay-click", this._onOverlayClick.bind(this))
    document.body.appendChild(overlay)
    this._overlay = overlay
    return
  }

  _hideOverlay() {
    if (this._overlay === null) {
      return
    }
    this._overlay.remove()
    this._overlay = null
    return
  }

  _onOverlayClick() {
    const closeOnBackdrop = this.getAttribute("close-on-backdrop") !== "false"
    if (closeOnBackdrop === true) {
      this._closeDrawer("backdrop")
    }
    return
  }

  _onKeydown(event) {
    if (event.key === "Escape") {
      event.preventDefault()
      this._closeDrawer("escape")
    }
    return
  }

  _onTouchStart(event) {
    if (this.getAttribute("edge") !== "bottom") {
      return
    }
    const touch = event.touches[0]
    this._touchStartY = touch.clientY
    this._touchStartX = touch.clientX
    return
  }

  _onTouchMove(event) {
    if (this._touchStartY === null) {
      return
    }
    const touch = event.touches[0]
    const deltaY = touch.clientY - this._touchStartY
    if (deltaY > 0) {
      const panelHeight = this._panel.offsetHeight
      const progress = Math.min(deltaY / panelHeight, 1)
      this._panel.style.transform = `translateY(${deltaY}px)`
      this.emit("mj-drawer-swipe", { progress: progress })
    }
    return
  }

  _onTouchEnd(event) {
    if (this._touchStartY === null) {
      return
    }
    const touch = event.changedTouches[0]
    const deltaY = touch.clientY - this._touchStartY
    const panelHeight = this._panel.offsetHeight
    const progress = deltaY / panelHeight

    this._panel.style.transform = ""
    this._touchStartY = null
    this._touchStartX = null

    const swipeEnabled = this.getAttribute("swipe-to-dismiss") !== "false"
    if (swipeEnabled === true && progress > 0.4) {
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

  show() {
    this.setAttribute("open", "")
    return
  }

  close() {
    this._closeDrawer("api")
    return
  }
}
