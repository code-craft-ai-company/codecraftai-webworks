/*
 * mjbulkactionbar.js
 *
 * <mj-bulk-action-bar> -- contextual toolbar shown when rows are selected in
 * a data table, tree grid, or virtual list. Tri-state select-all checkbox,
 * live count label, action buttons, overflow menu, and Escape to clear.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { RovingTabindex } from "../core/focustrap.js";
import { formatNumber } from "../core/intl.js";
import { announce } from "../core/announcer.js";

const STYLES = `
:host {
  display: block;
  font: inherit;
}

.bar {
  display: none;
  align-items: center;
  gap: var(--mj-bab-action-gap, 8px);
  height: var(--mj-bab-height, 48px);
  padding: 0 var(--mj-space-3);
  background: var(--mj-bab-bg, color-mix(in srgb, var(--mj-accent) 8%, var(--mj-surface)));
  border-radius: var(--mj-radius-md);
  border: 1px solid var(--mj-border);
}

:host([visible]) .bar { display: flex; }
:host([position="floating"]) .bar {
  position: sticky;
  bottom: 0;
  z-index: var(--mj-bab-z-index, var(--mj-layer-sticky));
  box-shadow: var(--mj-bab-shadow, var(--mj-elevation-2));
  border-radius: var(--mj-bab-border-radius, var(--mj-radius-md));
}

@media (prefers-reduced-motion: reduce) {
  .bar { transition: none; }
}

.select-all-wrap {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.select-all-cb {
  width: 1rem; height: 1rem;
  accent-color: var(--mj-accent);
  cursor: pointer;
}
.select-all-cb:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.count-label {
  font-size: var(--mj-font-size-sm);
  font-weight: var(--mj-font-weight-medium);
  color: var(--mj-bab-count-color, var(--mj-accent));
  white-space: nowrap;
  min-width: 6ch;
}

.action-group {
  display: flex;
  align-items: center;
  gap: var(--mj-bab-action-gap, 8px);
  flex: 1;
  overflow: hidden;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--mj-space-1);
  padding: var(--mj-space-1) var(--mj-space-3);
  min-height: var(--mj-control-height-sm);
  background: var(--mj-surface);
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-md);
  cursor: pointer;
  font: inherit;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
  white-space: nowrap;
}
.action-btn:hover { background: var(--mj-bg-muted); }
.action-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.action-btn[disabled] { opacity: 0.5; cursor: not-allowed; }
.action-btn.destructive {
  color: var(--mj-color-danger);
  border-color: var(--mj-color-danger);
}

.clear-btn {
  display: inline-flex;
  align-items: center;
  padding: var(--mj-space-1) var(--mj-space-2);
  background: none;
  border: none;
  cursor: pointer;
  color: var(--mj-text-muted);
  font: inherit;
  font-size: 1.2em;
  line-height: 1;
  border-radius: var(--mj-radius-sm);
  flex-shrink: 0;
}
.clear-btn:hover { color: var(--mj-text); background: var(--mj-bg-muted); }
.clear-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.live-region {
  position: absolute; width: 1px; height: 1px;
  overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap;
}
`;

export class MjBulkActionBar extends MjElement {
  static tagName = "mj-bulk-action-bar";
  static styles = STYLES;
  static watched = ["selected-count", "total-count", "visible", "disabled", "select-all-label", "clear-label", "count-label"];

  constructor() {
    super()
    this._selectedKeys = new Set()
    this._actions = []
    this._rovingTabindex = null
  }

  render() {
    const selectAllLabel = this.getAttribute("select-all-label") || "Select all"
    const clearLabel = this.getAttribute("clear-label") || "Clear selection"
    const markup = `
      <div class="bar" part="bar" role="toolbar" aria-label="Bulk actions">
        <div class="select-all-wrap">
          <input type="checkbox"
                 class="select-all-cb"
                 part="select-all-checkbox"
                 aria-label="${selectAllLabel}"
                 aria-checked="false" />
        </div>
        <span class="count-label" part="count-label" aria-live="polite" aria-atomic="true">0 selected</span>
        <div class="action-group" part="action-group" role="group" aria-label="Actions for selected rows">
          <slot name="actions"></slot>
        </div>
        <button class="clear-btn" part="clear-button" aria-label="${clearLabel}" title="${clearLabel}">×</button>
      </div>
      <div class="live-region" aria-live="polite" aria-atomic="true"></div>
    `
    return markup
  }

  afterRender() {
    this._bar = this.$(".bar")
    this._selectAllCb = this.$(".select-all-cb")
    this._countLabel = this.$(".count-label")
    this._actionGroup = this.$(".action-group")
    this._clearBtn = this.$(".clear-btn")
    this._liveRegion = this.$(".live-region")

    this.listen(this._selectAllCb, "change", () => { this._handleSelectAll() })
    this.listen(this._clearBtn, "click", () => { this._handleClear() })
    this.listen(this._bar, "keydown", (e) => {
      if (e.key === "Escape") {
        this._handleClear()
      }
    })

    this._syncState()

    if (this._actions.length > 0) {
      this._renderActions()
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._bar === undefined || this._bar === null) {
      return
    }
    if (name === "selected-count" || name === "total-count") {
      this._syncState()
    }
    if (name === "visible") {
      if (newValue !== null) {
        this._bar.removeAttribute("aria-hidden")
        const count = parseInt(this.getAttribute("selected-count") || "0", 10)
        const countText = this._formatCount(count)
        this._liveRegion.textContent = countText
        announce(countText)
      } else {
        this._bar.setAttribute("aria-hidden", "true")
      }
    }
    if (name === "disabled") {
      const isDisabled = newValue !== null
      this._selectAllCb.disabled = isDisabled
      const btns = this._actionGroup.querySelectorAll(".action-btn")
      for (let i = 0; i < btns.length; i = i + 1) {
        btns[i].disabled = isDisabled
        btns[i].setAttribute("aria-disabled", isDisabled ? "true" : "false")
      }
    }
    if (name === "select-all-label") {
      this._selectAllCb.setAttribute("aria-label", newValue || "Select all")
    }
    if (name === "clear-label") {
      this._clearBtn.setAttribute("aria-label", newValue || "Clear selection")
      this._clearBtn.setAttribute("title", newValue || "Clear selection")
    }
    return
  }

  _syncState() {
    const selected = parseInt(this.getAttribute("selected-count") || "0", 10)
    const total = parseInt(this.getAttribute("total-count") || "0", 10)

    const countText = this._formatCount(selected)
    this._countLabel.textContent = countText

    let checked = false
    let indeterminate = false

    if (total > 0 && selected === total) {
      checked = true
      this._selectAllCb.setAttribute("aria-checked", "true")
    } else if (selected > 0) {
      indeterminate = true
      this._selectAllCb.setAttribute("aria-checked", "mixed")
    } else {
      this._selectAllCb.setAttribute("aria-checked", "false")
    }

    this._selectAllCb.checked = checked
    this._selectAllCb.indeterminate = indeterminate

    if (selected === 0) {
      this.reflectBoolean("visible", false)
    }
    return
  }

  _formatCount(count) {
    const template = this.getAttribute("count-label") || "{n} selected"
    const formatted = formatNumber(count)
    const result = template.split("{n}").join(formatted)
    return result
  }

  _handleSelectAll() {
    const current = this._selectAllCb.getAttribute("aria-checked")
    const selectAll = current === "false" || current === "mixed"
    const proceed = this.emit("mj-select-all", { selectAll: selectAll }, { cancelable: true })
    if (proceed === false) {
      this._selectAllCb.checked = !this._selectAllCb.checked
    }
    return
  }

  _handleClear() {
    this.emit("mj-clear-selection", {})
    this.reflectBoolean("visible", false)
    return
  }

  _renderActions() {
    const existing = this._actionGroup.querySelectorAll(".action-btn")
    for (let i = 0; i < existing.length; i = i + 1) {
      existing[i].remove()
    }

    const isDisabled = this.hasAttribute("disabled")

    for (let idx = 0; idx < this._actions.length; idx = idx + 1) {
      const action = this._actions[idx]
      const btn = document.createElement("button")
      btn.className = action.destructive === true ? "action-btn destructive" : "action-btn"
      btn.setAttribute("part", "action-button")
      btn.setAttribute("data-action-key", action.key)

      if (action.disabled === true || isDisabled === true) {
        btn.disabled = true
        btn.setAttribute("aria-disabled", "true")
      }

      if (action.icon !== undefined) {
        const iconSpan = document.createElement("span")
        iconSpan.setAttribute("aria-hidden", "true")
        iconSpan.textContent = action.icon
        btn.appendChild(iconSpan)
      }

      const labelSpan = document.createElement("span")
      labelSpan.textContent = action.label
      btn.appendChild(labelSpan)

      this.listen(btn, "click", () => {
        this.emit("mj-action", {
          actionKey: action.key,
          selectedKeys: Array.from(this._selectedKeys)
        })
      })

      this._actionGroup.insertBefore(btn, this._actionGroup.querySelector("slot"))
    }

    this._setupRovingTabindex()
    return
  }

  _setupRovingTabindex() {
    const btns = Array.from(this._actionGroup.querySelectorAll(".action-btn"))
    if (btns.length === 0) {
      return
    }
    if (this._rovingTabindex !== null) {
      this._rovingTabindex.setItems(btns)
    } else {
      this._rovingTabindex = new RovingTabindex({ items: btns, orientation: "horizontal", wrap: true })
      const dispose = this._rovingTabindex.attach(this._actionGroup)
      this.onTeardown(dispose)
    }
    return
  }

  /* ----- scriptable API ----- */

  get selectedKeys() {
    return this._selectedKeys
  }

  set selectedKeys(value) {
    this._selectedKeys = value instanceof Set ? value : new Set(value)
    return
  }

  get actions() {
    return this._actions
  }

  set actions(value) {
    this._actions = Array.isArray(value) === true ? value : []
    if (this._actionGroup !== undefined && this._actionGroup !== null) {
      this._renderActions()
    }
    return
  }

  get visible() {
    return this.hasAttribute("visible")
  }

  set visible(value) {
    this.reflectBoolean("visible", value === true)
    return
  }

  get selectedCount() {
    return parseInt(this.getAttribute("selected-count") || "0", 10)
  }

  set selectedCount(value) {
    const num = typeof value === "number" ? value : parseInt(value, 10)
    this.setAttribute("selected-count", String(isNaN(num) === true ? 0 : num))
    return
  }

  get totalCount() {
    return parseInt(this.getAttribute("total-count") || "0", 10)
  }

  set totalCount(value) {
    const num = typeof value === "number" ? value : parseInt(value, 10)
    this.setAttribute("total-count", String(isNaN(num) === true ? 0 : num))
    return
  }

  get disabled() {
    return this.hasAttribute("disabled")
  }

  set disabled(value) {
    this.reflectBoolean("disabled", value === true)
    return
  }
}
