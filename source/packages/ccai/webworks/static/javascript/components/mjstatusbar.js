/*
 * mjstatusbar.js
 *
 * <mj-status-bar> -- persistent horizontal strip pinned to the bottom of the
 * application viewport. Three-section layout (start / center / end) with a
 * polite live region for programmatic announcements.
 *
 * The bar itself is a named group, not a live region and not a landmark:
 * changing the text of an item (a clock, a cursor position) is never read
 * out by itself. Only `announce()` speaks, and it speaks each message once --
 * polite messages through the bar's own visually hidden status region,
 * assertive ones through the shared announcer.
 *
 * Slotted children carrying the `interactive` attribute are clickable items.
 * Native controls (<button>, <a href>) are used as they are; any other
 * element is given role="button", a tab stop and Enter / Space activation.
 */

import { MjElement } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";
import { t } from "../core/intl.js";

/* Minimum gap between two announcements, so one does not cut off the other. */
const ANNOUNCE_GAP_MS = 150;

/* Slotted elements that are operable without help from the bar. */
const NATIVE_CONTROL_SELECTOR = "button, a[href], input, select, textarea, summary";

const STYLES = `
:host {
  display: block;
  position: sticky;
  inset-block-end: 0;
  z-index: var(--mj-layer-docked);
}

:host([hidden]) {
  display: none;
}

.statusbar-root {
  display: flex;
  align-items: center;
  min-block-size: var(--mj-statusbar-height, 22px);
  background: var(--mj-statusbar-bg, var(--mj-bg-subtle));
  border-block-start: 1px solid var(--mj-statusbar-border, var(--mj-border));
  font-size: var(--mj-statusbar-font-size, var(--mj-font-size-xs));
  color: var(--mj-statusbar-color, var(--mj-text-muted));
  overflow: hidden;
  padding: 0;
  gap: 0;
}

/*
 * The side sections keep their content as long as there is room and shrink
 * (clipping their own overflow) before anything is pushed out of the bar.
 */
.section {
  display: flex;
  align-items: center;
  overflow: hidden;
  min-inline-size: 0;
  flex: 0 1 auto;
}

.section-start {
  justify-content: flex-start;
}

.section-center {
  flex: 1 1 0;
  justify-content: center;
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

::slotted(*) {
  padding: var(--mj-statusbar-item-padding, 0 var(--mj-space-2));
  white-space: nowrap;
}

::slotted([interactive]) {
  cursor: pointer;
  background: transparent;
  border: none;
  font: inherit;
  font-size: inherit;
  color: inherit;
  min-block-size: 24px;
  min-inline-size: 24px;
}

::slotted([interactive]:hover) {
  background: var(--mj-bg-muted);
}

::slotted([interactive]:focus-visible) {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: calc(-1 * var(--mj-focus-ring-width));
}

/*
 * Severity items sit on their tinted surface: each status foreground token
 * is defined against its own surface token in both themes, which keeps the
 * small status text at 4.5:1 or better.
 */
::slotted([severity="info"]) {
  background: var(--mj-color-info-surface);
  color: var(--mj-color-info);
}

::slotted([severity="success"]) {
  background: var(--mj-color-success-surface);
  color: var(--mj-color-success);
}

::slotted([severity="warning"]) {
  background: var(--mj-color-warning-surface);
  color: var(--mj-color-warning);
}

::slotted([severity="error"]) {
  background: var(--mj-color-danger-surface);
  color: var(--mj-color-danger);
}
`;

export class MjStatusBar extends MjElement {
  static tagName = "mj-status-bar";
  static styles = STYLES;
  static watched = ["label", "variant"];

  constructor() {
    super()
    this._rootEl = null
    this._liveEl = null
    this._announceQueue = []
    this._announceTimer = null
    this._announceFrame = null
    this._itemObserver = null

    /*
     * What the bar added to an interactive item, so it is taken away again
     * when the item stops being interactive: element -> { role, tabindex }.
     */
    this._upgradedItems = new Map()
  }

  render() {
    const markup = `
      <div class="statusbar-root" role="group" part="root">
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
             role="status" aria-live="polite" aria-atomic="true"></div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._rootEl = this.$(".statusbar-root")
    this._liveEl = this.$(".live-region")

    this._syncLabel()

    this.listen(this, "click", this._onItemClick.bind(this))
    this.listen(this, "keydown", this._onItemKeydown.bind(this))

    const slots = this.$all("slot")
    for (let index = 0; index < slots.length; index = index + 1) {
      this.listen(slots[index], "slotchange", this._syncInteractiveItems.bind(this))
    }

    /*
     * `interactive` may be added to or removed from an item after it was
     * slotted, and an interactive element may be added inside (or removed
     * from) an item that is already slotted, which fires no slotchange.
     */
    if (typeof MutationObserver === "function") {
      this._itemObserver = new MutationObserver(this._syncInteractiveItems.bind(this))
      this._itemObserver.observe(this, {
        attributes: true,
        attributeFilter: ["interactive"],
        childList: true,
        subtree: true
      })
    }

    this.onTeardown(() => {
      if (this._itemObserver !== null) {
        this._itemObserver.disconnect()
        this._itemObserver = null
      }
      if (this._announceTimer !== null) {
        window.clearTimeout(this._announceTimer)
        this._announceTimer = null
      }
      if (this._announceFrame !== null) {
        window.cancelAnimationFrame(this._announceFrame)
        this._announceFrame = null
      }
      this._announceQueue = []
    })

    this._syncInteractiveItems()
    return
  }

  _syncLabel() {
    if (this._rootEl === undefined || this._rootEl === null) {
      return
    }
    const label = this.getAttribute("label") || t("mj.statusBar.label")
    this._rootEl.setAttribute("aria-label", label)
    return
  }

  /* ----- interactive items ----- */

  /* The element among `event`'s targets that is an interactive item of this bar. */
  _interactiveItemOf(event) {
    let item = null

    const target = event.target
    if (target instanceof Element) {
      const candidate = target.closest("[interactive]")
      if (candidate !== null && this.contains(candidate) === true && candidate !== this) {
        item = candidate
      }
    }

    return item
  }

  /*
   * Make every interactive item that is not a native control operable from
   * the keyboard and visible to assistive technology as a button; undo that
   * for items that are no longer interactive. Attributes the author set are
   * left alone.
   */
  _syncInteractiveItems() {
    const current = Array.from(this.querySelectorAll("[interactive]"))

    for (let index = 0; index < current.length; index = index + 1) {
      const item = current[index]
      const native = item.matches(NATIVE_CONTROL_SELECTOR)
      if (native === false && this._upgradedItems.has(item) === false) {
        const added = { role: false, tabindex: false }
        if (item.hasAttribute("role") === false) {
          item.setAttribute("role", "button")
          added.role = true
        }
        if (item.hasAttribute("tabindex") === false) {
          item.setAttribute("tabindex", "0")
          added.tabindex = true
        }
        this._upgradedItems.set(item, added)
      }
    }

    const upgraded = Array.from(this._upgradedItems.keys())
    for (let index = 0; index < upgraded.length; index = index + 1) {
      const item = upgraded[index]
      const stillInteractive = current.indexOf(item) >= 0
      if (stillInteractive === false) {
        const added = this._upgradedItems.get(item)
        if (added.role === true) {
          item.removeAttribute("role")
        }
        if (added.tabindex === true) {
          item.removeAttribute("tabindex")
        }
        this._upgradedItems.delete(item)
      }
    }
    return
  }

  _onItemClick(event) {
    const item = this._interactiveItemOf(event)
    if (item !== null) {
      const itemId = item.id || ""
      const value = item.getAttribute("value") || item.textContent.trim()
      this.emit("mj-status-item-click", { itemId: itemId, value: value })
    }
    return
  }

  /* Enter / Space activate an interactive item that is not a native control. */
  _onItemKeydown(event) {
    const activation = event.key === "Enter" || event.key === " "
    if (activation === false || event.defaultPrevented === true) {
      return
    }

    const item = this._interactiveItemOf(event)
    if (item !== null && event.target === item && item.matches(NATIVE_CONTROL_SELECTOR) === false) {
      event.preventDefault()
      item.click()
    }
    return
  }

  /* ----- announcements ----- */

  /*
   * Announce `message` to assistive technology. Messages are queued with a
   * 150 ms minimum gap to prevent overlap. `politeness` is "polite"
   * (default) or "assertive".
   */
  announce(message, politeness) {
    if (message === null || message === undefined || String(message).length === 0) {
      return
    }

    const level = politeness === "assertive" ? "assertive" : "polite"
    this._announceQueue.push({ message: String(message), politeness: level })
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

    if (entry.politeness === "assertive" || this._liveEl === null) {
      /* The bar has no assertive region of its own; the shared one speaks it. */
      announce(entry.message, entry.politeness)
    } else {
      /* Clear first so repeating the same message is announced again. */
      this._liveEl.textContent = ""
      this._announceFrame = window.requestAnimationFrame(() => {
        this._announceFrame = null
        if (this._liveEl !== null) {
          this._liveEl.textContent = entry.message
        }
      })
    }

    this._announceTimer = window.setTimeout(() => {
      this._announceTimer = null
      this._processQueue()
    }, ANNOUNCE_GAP_MS)

    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "label") {
      this._syncLabel()
    }
    return
  }

  /* The slotted status items, in visual order: start, center, end. */
  get items() {
    const found = []
    const slotSelectors = ["slot[name='start']", "slot:not([name])", "slot[name='end']"]

    if (this.shadowRoot !== null) {
      for (let index = 0; index < slotSelectors.length; index = index + 1) {
        const slot = this.shadowRoot.querySelector(slotSelectors[index])
        if (slot !== null) {
          const assigned = slot.assignedElements({ flatten: true })
          for (let position = 0; position < assigned.length; position = position + 1) {
            found.push(assigned[position])
          }
        }
      }
    }

    return found
  }
}
