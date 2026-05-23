/*
 * mjcolumnpicker.js
 *
 * <mj-column-picker> -- column visibility toggle and reorder panel for
 * data tables and tree grids. Opens a dialog with checkbox list.
 * Supports immediate and deferred apply modes, locked columns, and
 * keyboard drag-reorder.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";
import { trapFocus } from "../core/focustrap.js";

const STYLES = `
:host {
  display: inline-block;
  position: relative;
  font: inherit;
}

.trigger-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--mj-space-1);
  padding: var(--mj-space-1) var(--mj-space-3);
  min-height: var(--mj-control-height-md);
  background: var(--mj-surface);
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-md);
  cursor: pointer;
  font: inherit;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
}
.trigger-btn:hover { background: var(--mj-bg-muted); }
.trigger-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.trigger-btn[disabled] { opacity: 0.5; cursor: not-allowed; pointer-events: none; }

.panel {
  display: none;
  position: absolute;
  top: calc(100% + 4px);
  inset-inline-start: 0;
  z-index: var(--mj-layer-popover);
  width: var(--mj-cp-panel-width, 240px);
  max-height: var(--mj-cp-panel-max-height, 360px);
  overflow-y: auto;
  background: var(--mj-surface-raised);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-md);
  box-shadow: var(--mj-elevation-2);
  flex-direction: column;
}
.panel[aria-hidden="false"] { display: flex; }

.panel-header-slot {
  padding: var(--mj-space-2) var(--mj-space-3);
  border-bottom: 1px solid var(--mj-border);
  font-weight: var(--mj-font-weight-medium);
  font-size: var(--mj-font-size-sm);
}

.column-list {
  list-style: none;
  margin: 0;
  padding: var(--mj-space-1) 0;
  flex: 1;
  overflow-y: auto;
}

.column-item {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  padding: 0 var(--mj-space-3);
  height: var(--mj-cp-item-height, 36px);
  cursor: default;
}
.column-item:hover { background: var(--mj-bg-muted); }
.column-item.grabbed { background: color-mix(in srgb, var(--mj-accent) 12%, transparent); }

.drag-handle {
  cursor: grab;
  color: var(--mj-cp-drag-handle-color, var(--mj-text-muted));
  background: none;
  border: none;
  padding: 0;
  font-size: 1em;
  flex-shrink: 0;
  line-height: 1;
}
.drag-handle:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: 2px;
}
.drag-handle[disabled] { visibility: hidden; }

.col-checkbox { flex-shrink: 0; accent-color: var(--mj-cp-checked-color, var(--mj-accent)); }
.col-label { flex: 1; font-size: var(--mj-font-size-sm); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.col-label.hidden-col { opacity: 0.5; }

.panel-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--mj-space-2);
  padding: var(--mj-space-2) var(--mj-space-3);
  border-top: 1px solid var(--mj-border);
}

.footer-btn {
  padding: var(--mj-space-1) var(--mj-space-3);
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-sm);
  background: var(--mj-surface);
  cursor: pointer;
  font: inherit;
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text);
}
.footer-btn:hover { background: var(--mj-bg-muted); }
.footer-btn.primary { background: var(--mj-accent); color: var(--mj-text-on-accent); border-color: var(--mj-accent); }
.footer-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.live-region {
  position: absolute; width: 1px; height: 1px;
  overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap;
}
`;

export class MjColumnPicker extends MjElement {
  static tagName = "mj-column-picker";
  static styles = STYLES;
  static watched = ["apply-mode", "variant", "label", "open", "disabled", "reorderable", "min-visible"];

  constructor() {
    super()
    this._columns = []
    this._defaultColumns = []
    this._pendingColumns = null
    this._grabIndex = null
    this._releaseFocusTrap = null
    this._panelId = nextId("mj-cp-panel")
  }

  render() {
    const label = this.getAttribute("label") || "Columns"
    const markup = `
      <button class="trigger-btn" part="trigger-button"
              aria-haspopup="dialog"
              aria-expanded="false"
              aria-label="${label}">
        ⊞ ${label}
      </button>
      <div class="panel" part="panel"
           id="${this._panelId}"
           role="dialog"
           aria-label="${label} picker"
           aria-modal="true"
           aria-hidden="true">
        <div class="panel-header-slot" part="panel-header">
          <slot name="panel-header">${label}</slot>
        </div>
        <ul class="column-list" part="column-list" role="list"></ul>
        <div class="panel-footer" part="panel-footer">
          <button class="footer-btn" part="reset-button">Reset</button>
          <slot name="panel-footer"></slot>
          <button class="footer-btn primary apply-btn" part="apply-button" style="display:none">Apply</button>
        </div>
      </div>
      <div class="live-region" aria-live="assertive" aria-atomic="true"></div>
    `
    return markup
  }

  afterRender() {
    this._triggerBtn = this.$(".trigger-btn")
    this._panel = this.$(".panel")
    this._columnList = this.$(".column-list")
    this._resetBtn = this.$(".footer-btn[part='reset-button']")
    this._applyBtn = this.$(".apply-btn")
    this._liveRegion = this.$(".live-region")

    this.listen(this._triggerBtn, "click", () => { this._toggle() })
    this.listen(this._triggerBtn, "keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault()
        this._toggle()
      }
    })

    this.listen(this._resetBtn, "click", () => { this._handleReset() })
    this.listen(this._applyBtn, "click", () => { this._handleApply() })

    const applyMode = this.getAttribute("apply-mode") || "immediate"
    if (applyMode === "deferred") {
      this._applyBtn.style.display = ""
    }

    this.listen(document, "click", (e) => {
      if (this.hasAttribute("open") === true && this.contains(e.target) === false) {
        this._close()
      }
    })

    this.listen(document, "keydown", (e) => {
      if (e.key === "Escape" && this.hasAttribute("open") === true) {
        this._close()
      }
    })

    if (this._columns.length > 0) {
      this._renderColumnList()
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._triggerBtn === undefined || this._triggerBtn === null) {
      return
    }
    if (name === "open") {
      if (newValue !== null) {
        this._openPanel()
      } else {
        this._closePanel()
      }
    }
    if (name === "disabled") {
      if (newValue !== null) {
        this._triggerBtn.setAttribute("disabled", "")
      } else {
        this._triggerBtn.removeAttribute("disabled")
      }
    }
    if (name === "label") {
      this._triggerBtn.setAttribute("aria-label", newValue || "Columns")
    }
    return
  }

  _toggle() {
    if (this.hasAttribute("open") === true) {
      this._close()
    } else {
      this._open()
    }
    return
  }

  _open() {
    this.setAttribute("open", "")
    return
  }

  _close() {
    this.removeAttribute("open")
    return
  }

  _openPanel() {
    this._panel.setAttribute("aria-hidden", "false")
    this._triggerBtn.setAttribute("aria-expanded", "true")
    this._renderColumnList()
    this._releaseFocusTrap = trapFocus(this._panel)
    this.emit("mj-picker-open", {})
    return
  }

  _closePanel() {
    this._panel.setAttribute("aria-hidden", "true")
    this._triggerBtn.setAttribute("aria-expanded", "false")
    this._pendingColumns = null
    if (this._releaseFocusTrap !== null) {
      this._releaseFocusTrap()
      this._releaseFocusTrap = null
    }
    this._triggerBtn.focus()
    this.emit("mj-picker-close", {})
    return
  }

  _renderColumnList() {
    this._columnList.innerHTML = ""
    const reorderable = this.getAttribute("reorderable") !== "false"
    const cols = this._columns

    for (let idx = 0; idx < cols.length; idx = idx + 1) {
      const col = cols[idx]
      const li = document.createElement("li")
      li.className = "column-item"
      li.setAttribute("part", "column-item")
      li.setAttribute("role", "listitem")
      li.setAttribute("data-col-key", col.key)
      li.setAttribute("data-idx", String(idx))

      if (reorderable === true && col.locked !== true) {
        const handle = document.createElement("button")
        handle.className = "drag-handle"
        handle.setAttribute("part", "column-drag-handle")
        handle.setAttribute("aria-label", `Reorder ${col.label}`)
        handle.setAttribute("aria-grabbed", "false")
        handle.textContent = "⠿"
        this.listen(handle, "click", () => { this._toggleGrab(idx, handle, li) })
        this.listen(handle, "keydown", (e) => {
          if (e.key === " ") {
            e.preventDefault()
            this._toggleGrab(idx, handle, li)
          } else if (this._grabIndex !== null && this._grabIndex === idx) {
            if (e.key === "ArrowUp") {
              e.preventDefault()
              this._moveGrabbed(-1)
            } else if (e.key === "ArrowDown") {
              e.preventDefault()
              this._moveGrabbed(1)
            } else if (e.key === "Enter") {
              e.preventDefault()
              this._confirmGrab()
            } else if (e.key === "Escape") {
              e.preventDefault()
              this._cancelGrab()
            }
          }
        })
        li.appendChild(handle)
      } else {
        const placeholder = document.createElement("span")
        placeholder.style.width = "1.2em"
        placeholder.style.flexShrink = "0"
        li.appendChild(placeholder)
      }

      const checkbox = document.createElement("input")
      checkbox.type = "checkbox"
      checkbox.className = "col-checkbox"
      checkbox.setAttribute("part", "column-checkbox")
      checkbox.setAttribute("aria-label", col.label)
      checkbox.checked = col.visible !== false
      if (col.locked === true) {
        checkbox.disabled = true
        checkbox.setAttribute("aria-describedby", `locked-${col.key}`)
      }
      this.listen(checkbox, "change", () => { this._handleVisibilityChange(col.key, checkbox.checked) })
      li.appendChild(checkbox)

      const labelEl = document.createElement("span")
      labelEl.className = col.visible !== false ? "col-label" : "col-label hidden-col"
      labelEl.setAttribute("part", "column-label")
      labelEl.textContent = col.label
      li.appendChild(labelEl)

      this._columnList.appendChild(li)
    }
    return
  }

  _handleVisibilityChange(key, visible) {
    const applyMode = this.getAttribute("apply-mode") || "immediate"
    const minVisible = parseInt(this.getAttribute("min-visible") || "1", 10)

    const colIdx = this._columns.findIndex((c) => c.key === key)
    if (colIdx < 0) {
      return
    }

    if (visible === false) {
      const currentVisible = this._columns.filter((c) => c.visible !== false && c.key !== key)
      if (currentVisible.length < minVisible) {
        this._liveRegion.textContent = "At least one column must remain visible."
        const checkbox = this._columnList.querySelector(`[data-col-key="${key}"] .col-checkbox`)
        if (checkbox !== null) {
          checkbox.checked = true
        }
        return
      }
    }

    if (applyMode === "immediate") {
      this._columns[colIdx].visible = visible
      this.emit("mj-column-visibility-change", {
        key: key,
        visible: visible,
        columns: this._columns.slice()
      })
      announce(`Column ${this._columns[colIdx].label} ${visible === true ? "shown" : "hidden"}.`)
    } else {
      if (this._pendingColumns === null) {
        this._pendingColumns = this._columns.map((c) => Object.assign({}, c))
      }
      const pending = this._pendingColumns.find((c) => c.key === key)
      if (pending !== undefined) {
        pending.visible = visible
      }
    }
    return
  }

  _toggleGrab(idx, handle, li) {
    if (this._grabIndex === idx) {
      this._cancelGrab()
      return
    }
    if (this._grabIndex !== null) {
      this._cancelGrab()
    }
    this._grabIndex = idx
    this._grabOriginalIdx = idx
    li.classList.add("grabbed")
    handle.setAttribute("aria-grabbed", "true")
    return
  }

  _moveGrabbed(delta) {
    if (this._grabIndex === null) {
      return
    }
    const newIdx = this._grabIndex + delta
    if (newIdx < 0 || newIdx >= this._columns.length) {
      return
    }

    const cols = this._columns
    const temp = cols[this._grabIndex]
    cols[this._grabIndex] = cols[newIdx]
    cols[newIdx] = temp
    this._grabIndex = newIdx
    this._renderColumnList()

    const col = this._columns[newIdx]
    this._liveRegion.textContent = `${col.label} moved to position ${newIdx + 1}.`
    return
  }

  _confirmGrab() {
    if (this._grabIndex === null) {
      return
    }
    const from = this._grabOriginalIdx
    const to = this._grabIndex
    this._grabIndex = null
    this._grabOriginalIdx = null
    this._renderColumnList()

    this.emit("mj-column-reorder", {
      key: this._columns[to].key,
      from: from,
      to: to,
      columns: this._columns.slice()
    })
    announce("Columns reordered.")
    return
  }

  _cancelGrab() {
    if (this._grabIndex === null) {
      return
    }
    const from = this._grabIndex
    const to = this._grabOriginalIdx
    const cols = this._columns
    const moved = cols.splice(from, 1)[0]
    cols.splice(to, 0, moved)
    this._grabIndex = null
    this._grabOriginalIdx = null
    this._renderColumnList()
    return
  }

  _handleReset() {
    this._columns = this._defaultColumns.map((c) => Object.assign({}, c))
    this._pendingColumns = null
    this._renderColumnList()
    this.emit("mj-columns-reset", { columns: this._columns.slice() })
    return
  }

  _handleApply() {
    if (this._pendingColumns !== null) {
      this._columns = this._pendingColumns
      this._pendingColumns = null
    }
    this.emit("mj-columns-apply", { columns: this._columns.slice() })
    this._close()
    return
  }

  /* ----- scriptable API ----- */

  get columns() {
    return this._columns
  }

  set columns(value) {
    this._columns = Array.isArray(value) === true ? value.map((c) => Object.assign({}, c)) : []
    if (this._columnList !== undefined && this._columnList !== null && this.hasAttribute("open") === true) {
      this._pendingColumns = null
      this._renderColumnList()
    }
    return
  }

  get defaultColumns() {
    return this._defaultColumns
  }

  set defaultColumns(value) {
    this._defaultColumns = Array.isArray(value) === true ? value.map((c) => Object.assign({}, c)) : []
    return
  }

  get open() {
    return this.hasAttribute("open")
  }

  set open(value) {
    this.reflectBoolean("open", value === true)
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
