/*
 * mjbulkactionbar.js
 *
 * <mj-bulk-action-bar> -- contextual toolbar shown when rows are selected in
 * a data table, tree grid, or virtual list. Tri-state select-all checkbox,
 * count label, action buttons, and Escape to clear.
 *
 * Visibility: the `visible` attribute shows the bar. The component sets it
 * when `selected-count` rises above zero and removes it when the count drops
 * back to zero; a host may also set or remove it directly at any time.
 *
 * Actions that do not fit on one line wrap onto further lines (a "More
 * actions" overflow menu is not implemented), so none is ever clipped.
 *
 * `returnFocusTo` (an element) receives focus when the bar hides while focus
 * is inside it -- typically the grid the selection belongs to.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { RovingTabindex } from "../core/focustrap.js";
import { formatNumber, t } from "../core/intl.js";
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
  min-block-size: var(--mj-bab-height, 48px);
  box-sizing: border-box;
  padding: var(--mj-space-1) var(--mj-space-3);
  background: var(--mj-bab-bg, color-mix(in srgb, var(--mj-accent) 8%, var(--mj-surface)));
  border-radius: var(--mj-radius-md);
  border: 1px solid var(--mj-border);
}

:host([visible]) .bar { display: flex; }

/* Sticky positioning belongs on the host: the bar fills it exactly. */
:host([position="floating"]) {
  position: sticky;
  inset-block-end: 0;
  z-index: var(--mj-bab-z-index, var(--mj-layer-sticky));
}
:host([position="floating"]) .bar {
  box-shadow: var(--mj-bab-shadow, var(--mj-elevation-2));
  border-radius: var(--mj-bab-border-radius, var(--mj-radius-md));
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

/* Actions wrap instead of being clipped when the bar is narrow. */
.action-group {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--mj-bab-action-gap, 8px);
  flex: 1;
  min-inline-size: 0;
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
.clear-btn[disabled] { opacity: 0.5; cursor: not-allowed; }
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
    this._returnFocusTo = null

    /* The count seen by the last sync, to detect crossing zero. */
    this._lastCount = 0

    /* The count text last sent to the announcer while the bar is shown. */
    this._announcedText = null
  }

  render() {
    /* Labels are applied in afterRender with setAttribute, never as markup. */
    const markup = `
      <div class="bar" part="bar" role="toolbar">
        <div class="select-all-wrap">
          <input type="checkbox"
                 class="select-all-cb"
                 part="select-all-checkbox"
                 aria-checked="false" />
        </div>
        <span class="count-label" part="count-label"></span>
        <div class="action-group" part="action-group" role="group">
          <slot name="actions"></slot>
        </div>
        <button type="button" class="clear-btn" part="clear-button">×</button>
      </div>
    `
    return markup
  }

  afterRender() {
    this._bar = this.$(".bar")
    this._selectAllCb = this.$(".select-all-cb")
    this._countLabel = this.$(".count-label")
    this._actionGroup = this.$(".action-group")
    this._clearBtn = this.$(".clear-btn")

    /* The previous controller was attached to a shadow tree that is gone. */
    this._rovingTabindex = null

    this.listen(this._selectAllCb, "change", () => { this._handleSelectAll() })
    this.listen(this._clearBtn, "click", () => { this._handleClear() })
    this.listen(this._actionGroup, "click", this._onActionClick.bind(this))
    this.listen(this._bar, "keydown", (e) => {
      if (e.key === "Escape") {
        this._handleClear()
      }
    })

    this._syncLabels()
    this._syncState()
    this._renderActions()
    this._syncDisabled()
    this._syncVisible()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._bar === undefined || this._bar === null) {
      return
    }
    if (name === "selected-count" || name === "total-count" || name === "count-label") {
      this._syncState()
    }
    if (name === "visible") {
      this._syncVisible()
    }
    if (name === "disabled") {
      this._syncDisabled()
    }
    if (name === "select-all-label" || name === "clear-label") {
      this._syncLabels()
    }
    return
  }

  _syncLabels() {
    const selectAllLabel = this.getAttribute("select-all-label") || t("core.selectAll")
    const clearLabel = this.getAttribute("clear-label") || t("mj.bulkActionBar.clearSelection")
    this._bar.setAttribute("aria-label", t("mj.bulkActionBar.toolbarLabel"))
    this._actionGroup.setAttribute("aria-label", t("mj.bulkActionBar.actionsLabel"))
    this._selectAllCb.setAttribute("aria-label", selectAllLabel)
    this._clearBtn.setAttribute("aria-label", clearLabel)
    this._clearBtn.setAttribute("title", clearLabel)
    return
  }

  _readCount(name) {
    const parsed = parseInt(this.getAttribute(name) || "0", 10)
    const count = Number.isNaN(parsed) === true || parsed < 0 ? 0 : parsed
    return count
  }

  /* Mirror the counts into the label, the tri-state checkbox and `visible`. */
  _syncState() {
    const selected = this._readCount("selected-count")
    const total = this._readCount("total-count")

    this._countLabel.textContent = this._formatCount(selected)

    let checked = false
    let indeterminate = false
    let ariaChecked = "false"

    if (total > 0 && selected >= total) {
      checked = true
      ariaChecked = "true"
    } else if (selected > 0) {
      indeterminate = true
      ariaChecked = "mixed"
    }

    this._selectAllCb.checked = checked
    this._selectAllCb.indeterminate = indeterminate
    this._selectAllCb.setAttribute("aria-checked", ariaChecked)

    /*
     * The bar follows the count only when it crosses zero, so a host that
     * sets or removes `visible` itself is not overruled on every sync.
     */
    const previous = this._lastCount
    this._lastCount = selected
    if (selected > 0 && previous === 0) {
      this.reflectBoolean("visible", true)
    } else if (selected === 0 && previous > 0) {
      this.reflectBoolean("visible", false)
    }

    this._announceCount()
    return
  }

  _syncVisible() {
    const visible = this.hasAttribute("visible")
    if (visible === true) {
      this._bar.removeAttribute("aria-hidden")
      this._announceCount()
    } else {
      this._bar.setAttribute("aria-hidden", "true")
      this._announcedText = null

      /* Hiding the bar must not drop focus onto <body>. */
      const focusInside = this.shadowRoot.activeElement !== null || this.contains(document.activeElement)
      if (focusInside === true && this._returnFocusTo !== null && typeof this._returnFocusTo.focus === "function") {
        this._returnFocusTo.focus()
      }
    }
    return
  }

  /* One announcement per change of the visible count (single live region). */
  _announceCount() {
    if (this.hasAttribute("visible") === false) {
      return
    }
    const text = this._countLabel.textContent
    if (text !== this._announcedText) {
      this._announcedText = text
      announce(text)
    }
    return
  }

  /* Apply `disabled` to every control; an action's own `disabled` is kept. */
  _syncDisabled() {
    const isDisabled = this.hasAttribute("disabled")
    this._selectAllCb.disabled = isDisabled
    this._clearBtn.disabled = isDisabled

    const btns = this._actionGroup.querySelectorAll(".action-btn")
    for (let i = 0; i < btns.length; i = i + 1) {
      const action = this._actions[parseInt(btns[i].getAttribute("data-action-index"), 10)]
      const actionDisabled = action !== undefined && action.disabled === true
      const buttonDisabled = isDisabled === true || actionDisabled === true
      btns[i].disabled = buttonDisabled
      btns[i].setAttribute("aria-disabled", buttonDisabled === true ? "true" : "false")
    }

    /* Slotted actions are the host's elements: make the group inert instead. */
    this._actionGroup.inert = isDisabled
    if (isDisabled === true) {
      this._actionGroup.setAttribute("aria-disabled", "true")
    } else {
      this._actionGroup.removeAttribute("aria-disabled")
    }

    if (this._rovingTabindex !== null) {
      this._rovingTabindex.setItems(Array.from(btns))
    }
    return
  }

  _formatCount(count) {
    const template = this.getAttribute("count-label")
    const formatted = formatNumber(count)
    let result = ""
    if (template !== null && template.length > 0) {
      result = template.split("{n}").join(formatted)
    } else {
      result = t("mj.bulkActionBar.selected", { count: count, countText: formatted })
    }
    return result
  }

  _handleSelectAll() {
    const current = this._selectAllCb.getAttribute("aria-checked")
    const selectAll = current === "false" || current === "mixed"
    this.emit("mj-select-all", { selectAll: selectAll }, { cancelable: true })

    /*
     * The native click already flipped the checkbox. Put it back in line
     * with the counts: they changed if the host applied the request, and
     * they still describe the truth if it canceled or ignored it.
     */
    this._syncState()
    return
  }

  _handleClear() {
    /* Emit first: the host can move focus back to its grid before the bar hides. */
    this.emit("mj-clear-selection", {})
    this.reflectBoolean("visible", false)
    return
  }

  _onActionClick(event) {
    const target = event.target
    if (!(target instanceof Element)) {
      return
    }
    const btn = target.closest(".action-btn")
    if (btn === null || btn.disabled === true) {
      return
    }
    const action = this._actions[parseInt(btn.getAttribute("data-action-index"), 10)]
    if (action === undefined) {
      return
    }
    this.emit("mj-action", {
      actionKey: action.key,
      selectedKeys: Array.from(this._selectedKeys)
    })
    return
  }

  _renderActions() {
    const existing = this._actionGroup.querySelectorAll(".action-btn")
    for (let i = 0; i < existing.length; i = i + 1) {
      existing[i].remove()
    }

    const slot = this._actionGroup.querySelector("slot")

    for (let idx = 0; idx < this._actions.length; idx = idx + 1) {
      const action = this._actions[idx]
      const btn = document.createElement("button")
      btn.type = "button"
      btn.className = action.destructive === true ? "action-btn destructive" : "action-btn"
      btn.setAttribute("part", "action-button")
      btn.setAttribute("data-action-key", action.key)
      btn.setAttribute("data-action-index", String(idx))

      if (action.icon !== undefined && action.icon !== null) {
        const iconSpan = document.createElement("span")
        iconSpan.setAttribute("aria-hidden", "true")
        iconSpan.textContent = action.icon
        btn.appendChild(iconSpan)
      }

      const labelSpan = document.createElement("span")
      labelSpan.textContent = action.label
      btn.appendChild(labelSpan)

      this._actionGroup.insertBefore(btn, slot)
    }

    this._setupRovingTabindex()
    this._syncDisabled()
    return
  }

  _setupRovingTabindex() {
    const btns = Array.from(this._actionGroup.querySelectorAll(".action-btn"))
    if (this._rovingTabindex !== null) {
      this._rovingTabindex.setItems(btns)
    } else if (btns.length > 0) {
      const roving = new RovingTabindex({ items: btns, orientation: "horizontal", wrap: true })
      const dispose = roving.attach(this._actionGroup)
      this._rovingTabindex = roving
      this.onTeardown(() => {
        dispose()
        if (this._rovingTabindex === roving) {
          this._rovingTabindex = null
        }
      })
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

  /* Element that takes focus when the bar hides while focus is inside it. */
  get returnFocusTo() {
    return this._returnFocusTo
  }

  set returnFocusTo(element) {
    this._returnFocusTo = element instanceof Element ? element : null
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
