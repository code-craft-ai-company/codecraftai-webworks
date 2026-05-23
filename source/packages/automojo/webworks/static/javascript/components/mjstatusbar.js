/*
 * mjstatusbar.js
 *
 * <mj-status-bar> -- persistent horizontal strip pinned to the bottom of the
 * application viewport. Three-section layout (start / center / end) with a
 * polite live region for programmatic announcements.
 */

import { MjElement } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";

const STYLES = `
:host {
  display: block;
}

:host([hidden]) {
  display: none;
}

.statusbar-root {
  display: flex;
  align-items: center;
  min-height: var(--mj-statusbar-height, 22px);
  background: var(--mj-statusbar-bg, var(--mj-bg-subtle));
  border-top: 1px solid var(--mj-statusbar-border, var(--mj-border));
  font-size: var(--mj-statusbar-font-size, var(--mj-font-size-xs));
  color: var(--mj-statusbar-color, var(--mj-text-muted));
  overflow: hidden;
  padding: 0;
  gap: 0;
}

.section {
  display: flex;
  align-items: center;
  overflow: hidden;
  flex-shrink: 0;
}

.section-start {
  justify-content: flex-start;
}

.section-center {
  flex: 1;
  justify-content: center;
  min-width: 0;
}

.section-end {
  justify-content: flex-end;
  margin-inline-start: auto;
}

:host([variant="minimal"]) .section-center,
:host([variant="minimal"]) .section-end {
  display: none;
}

.live-region {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  clip-path: inset(50%);
  white-space: nowrap;
}

::slotted([interactive]) {
  cursor: pointer;
  background: transparent;
  border: none;
  padding: var(--mj-statusbar-item-padding, 0 var(--mj-space-2));
  font: inherit;
  font-size: inherit;
  color: inherit;
  min-height: 24px;
  min-width: 24px;
}

::slotted([interactive]:hover) {
  background: var(--mj-bg-muted);
}

::slotted([interactive]:focus-visible) {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: calc(-1 * var(--mj-focus-ring-offset));
}

::slotted(*) {
  padding: var(--mj-statusbar-item-padding, 0 var(--mj-space-2));
  white-space: nowrap;
}

::slotted([severity="info"]) { color: var(--mj-color-info); }
::slotted([severity="success"]) { color: var(--mj-color-success); }
::slotted([severity="warning"]) { color: var(--mj-color-warning); }
::slotted([severity="error"]) { color: var(--mj-color-danger); }
`;

export class MjStatusBar extends MjElement {
  static tagName = "mj-status-bar";
  static styles = STYLES;
  static watched = ["label", "variant"];

  constructor() {
    super()
    this._liveEl = null
    this._announceQueue = []
    this._announceTimer = null
  }

  render() {
    const label = this.getAttribute("label") || "Status bar"
    const markup = `
      <footer class="statusbar-root" role="status" part="root" aria-label="${label}">
        <div class="section section-start" part="section-start">
          <slot name="start"></slot>
        </div>
        <div class="section section-center" part="section-center">
          <slot></slot>
        </div>
        <div class="section section-end" part="section-end">
          <slot name="end"></slot>
        </div>
        <div class="live-region" part="live-region"
             role="status" aria-live="polite" aria-atomic="false"></div>
      </footer>
    `
    return markup
  }

  afterRender() {
    this._liveEl = this.$(".live-region")
    this.listen(this, "click", this._onItemClick.bind(this))
    return
  }

  _onItemClick(event) {
    const target = event.target
    if (target === null) {
      return
    }
    const item = target.closest("[interactive]")
    if (item === null || item === undefined) {
      return
    }
    const itemId = item.id || ""
    const value = item.getAttribute("value") || item.textContent.trim()
    this.emit("mj-status-item-click", { itemId: itemId, value: value })
    return
  }

  /*
   * Programmatically inject a message into the live region.
   * Messages are queued with a 150 ms minimum gap to prevent overlap.
   */
  announce(message, politeness) {
    const poli = politeness || "polite"
    this._announceQueue.push({ message: message, politeness: poli })
    if (this._announceTimer === null) {
      this._processQueue()
    }
    return
  }

  _processQueue() {
    if (this._announceQueue.length === 0) {
      this._announceTimer = null
      return
    }

    const entry = this._announceQueue.shift()
    announce(entry.message, entry.politeness)

    if (this._liveEl !== null) {
      this._liveEl.textContent = ""
      window.requestAnimationFrame(() => {
        if (this._liveEl !== null) {
          this._liveEl.textContent = entry.message
        }
      })
    }

    this._announceTimer = window.setTimeout(() => {
      this._announceTimer = null
      this._processQueue()
    }, 150)

    this.onTeardown(() => {
      if (this._announceTimer !== null) {
        window.clearTimeout(this._announceTimer)
        this._announceTimer = null
      }
    })

    return
  }

  get items() {
    const starts = this.$all("[slot='start']")
    const ends = this.$all("[slot='end']")
    const centers = this.$all(":not([slot])")
    const found = [...starts, ...centers, ...ends]
    return found
  }
}
