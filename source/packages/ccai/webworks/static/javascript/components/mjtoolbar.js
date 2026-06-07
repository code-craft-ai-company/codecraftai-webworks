/*
 * mjtoolbar.js
 *
 * <mj-toolbar> -- horizontal strip of grouped controls with roving tabindex,
 * overflow menu, and optional ribbon variant. Implements WAI-ARIA APG Toolbar.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { RovingTabindex } from "../core/focustrap.js";

const STYLES = `
:host {
  display: block;
  position: relative;
}

.toolbar-root {
  display: flex;
  align-items: center;
  gap: var(--mj-toolbar-group-gap, var(--mj-space-3));
  min-height: var(--mj-toolbar-height, var(--mj-control-height-md));
  padding: 0 var(--mj-space-2);
  background: var(--mj-toolbar-bg, var(--mj-surface));
  border-bottom: 1px solid var(--mj-toolbar-border, var(--mj-border));
  overflow: hidden;
}

:host([orientation="vertical"]) .toolbar-root {
  flex-direction: column;
  align-items: stretch;
  min-height: unset;
  min-width: var(--mj-toolbar-height, var(--mj-control-height-md));
  border-bottom: none;
  border-inline-end: 1px solid var(--mj-toolbar-border, var(--mj-border));
  padding: var(--mj-space-2) 0;
}

:host([disabled]) .toolbar-root {
  opacity: 0.55;
  pointer-events: none;
}

:host([variant="action-bar"]) .toolbar-root {
  position: absolute;
  inset-inline-start: 50%;
  translate: -50% 0;
  border-radius: var(--mj-radius-lg);
  box-shadow: var(--mj-elevation-3);
  border-bottom: none;
  transition: opacity var(--mj-motion-fast) var(--mj-motion-ease),
              translate var(--mj-motion-fast) var(--mj-motion-ease);
}

:host([variant="action-bar"]:not([active])) .toolbar-root {
  opacity: 0;
  pointer-events: none;
  translate: -50% var(--mj-space-2);
}

.toolbar-group {
  display: flex;
  align-items: center;
  gap: var(--mj-toolbar-gap, var(--mj-space-1));
}

:host([orientation="vertical"]) .toolbar-group {
  flex-direction: column;
}

.overflow-btn {
  margin-inline-start: auto;
  flex-shrink: 0;
}

.overflow-btn[hidden] { display: none; }

.ribbon-tablist {
  display: flex;
  gap: var(--mj-space-1);
  padding: 0 var(--mj-space-2);
  border-bottom: 1px solid var(--mj-border);
  background: var(--mj-surface);
}

.ribbon-tab {
  padding: 0 var(--mj-space-3);
  min-height: var(--mj-toolbar-ribbon-tab-height, var(--mj-control-height-sm));
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  font: inherit;
  color: var(--mj-text-muted);
}

.ribbon-tab[aria-selected="true"] {
  color: var(--mj-accent);
  border-bottom-color: var(--mj-accent);
}

.ribbon-tab:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.slot-wrapper {
  display: contents;
}
`;

const FOCUSABLE = [
  "button:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  "[tabindex]:not([tabindex='-1'])",
  "mj-button:not([disabled])",
  "mj-toggle-button:not([disabled])"
].join(",");

export class MjToolbar extends MjElement {
  static tagName = "mj-toolbar";
  static styles = STYLES;
  static watched = ["variant", "label", "labelledby", "orientation", "active", "disabled"];

  constructor() {
    super()
    this._roving = null
    this._resizeObserver = null
    this._mutationObserver = null
    this._overflowItems = []
    this._toolbarId = nextId("mj-toolbar")
  }

  render() {
    const variant = this.getAttribute("variant") || "toolbar"
    const orientation = this.getAttribute("orientation") || "horizontal"
    const labelAttr = this.getAttribute("label") || ""
    const labelledby = this.getAttribute("labelledby") || ""
    const ariaLabel = labelAttr.length > 0 ? `aria-label="${labelAttr}"` : ""
    const ariaLabelledby = labelledby.length > 0 ? `aria-labelledby="${labelledby}"` : ""
    const ariaOrientation = `aria-orientation="${orientation}"`

    const ribbonTabs = variant === "ribbon" ? `<div class="ribbon-tablist" role="tablist" part="ribbon-tablist"></div>` : ""

    const markup = `
      ${ribbonTabs}
      <div class="toolbar-root" role="toolbar" part="root" id="${this._toolbarId}"
           ${ariaLabel} ${ariaLabelledby} ${ariaOrientation}>
        <slot class="slot-wrapper"></slot>
        <button class="overflow-btn" part="overflow-button" hidden
                aria-label="More actions" aria-haspopup="menu">
          <slot name="overflow-icon">&#8943;</slot>
        </button>
      </div>
    `
    return markup
  }

  afterRender() {
    this._root = this.$(".toolbar-root")
    this._overflowBtn = this.$(".overflow-btn")
    this._slot = this.$("slot:not([name])")

    this._setupRoving()

    this.listen(this._slot, "slotchange", this._onSlotChange.bind(this))
    this.listen(this._overflowBtn, "click", this._onOverflowClick.bind(this))

    if (typeof ResizeObserver === "function") {
      this._resizeObserver = new ResizeObserver(this._onResize.bind(this))
      this._resizeObserver.observe(this._root)
      this.onTeardown(() => {
        if (this._resizeObserver !== null) {
          this._resizeObserver.disconnect()
          this._resizeObserver = null
        }
      })
    }

    return
  }

  _getItems() {
    const assignedNodes = this._slot !== null ? this._slot.assignedElements({ flatten: true }) : []
    const items = []
    for (let i = 0; i < assignedNodes.length; i = i + 1) {
      const node = assignedNodes[i]
      const focusables = node.querySelectorAll(FOCUSABLE)
      if (focusables.length > 0) {
        for (let j = 0; j < focusables.length; j = j + 1) {
          items.push(focusables[j])
        }
      } else if (node.matches && node.matches(FOCUSABLE)) {
        items.push(node)
      }
    }
    return items
  }

  _setupRoving() {
    const orientation = this.getAttribute("orientation") || "horizontal"
    if (this._roving !== null) {
      this._roving = null
    }
    const items = this._getItems()
    this._roving = new RovingTabindex({
      items: items,
      orientation: orientation,
      wrap: true
    })
    const dispose = this._roving.attach(this._root)
    this.onTeardown(dispose)
    return
  }

  _onSlotChange() {
    const items = this._getItems()
    if (this._roving !== null) {
      this._roving.setItems(items)
    }
    return
  }

  _onResize() {
    this._checkOverflow()
    return
  }

  _checkOverflow() {
    // Basic overflow detection: compare scrollWidth vs clientWidth
    const hasOverflow = this._root.scrollWidth > this._root.clientWidth
    if (hasOverflow === true) {
      this._overflowBtn.hidden = false
    } else {
      this._overflowBtn.hidden = true
    }
    return
  }

  _onOverflowClick() {
    this.emit("mj-toolbar-overflow-change", {
      overflowCount: this._overflowItems.length,
      overflowItems: this._overflowItems
    })
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "orientation" && this._roving !== null) {
      this._roving.orientation = newValue || "horizontal"
    }
    return
  }

  get items() {
    const found = this._getItems()
    return found
  }

  get overflowItems() {
    return this._overflowItems
  }
}
