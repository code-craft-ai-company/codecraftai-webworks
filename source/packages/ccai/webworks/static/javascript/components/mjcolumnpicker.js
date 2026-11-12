/*
 * mjcolumnpicker.js
 *
 * <mj-column-picker> -- column visibility toggle and reorder panel for
 * data tables and tree grids. A trigger button opens a non-modal popover
 * (positioned by the core overlay engine, so it flips and shifts to stay in
 * the viewport) with a checkbox list.
 *
 * apply-mode="immediate" (default) reports every change as it happens;
 * apply-mode="deferred" collects visibility and order changes in a pending
 * copy that is committed by Apply and discarded when the panel closes.
 *
 * Reorder: drag a handle with the pointer, or focus a handle and press Space
 * to grab, ArrowUp / ArrowDown to move, Enter (or Space) to drop, Escape to
 * put the column back. Locked columns keep their position and visibility.
 *
 * Reset restores `defaultColumns`, or -- when that was never set -- the
 * first `columns` assignment.
 *
 * Events: mj-picker-open, mj-picker-close, mj-column-visibility-change,
 * mj-column-reorder, mj-columns-reset, mj-columns-apply.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";
import { t } from "../core/intl.js";
import { trapFocus } from "../core/focustrap.js";
import { autoPosition } from "../core/overlay.js";

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

/* Placed with position: fixed by the overlay engine while open. */
.panel {
  display: none;
  position: fixed;
  inset-block-start: 0;
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
  touch-action: none;
}
.drag-handle:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: 2px;
}
.drag-handle[aria-pressed="true"] { cursor: grabbing; color: var(--mj-accent); }
.handle-placeholder { inline-size: 1.2em; flex-shrink: 0; }

.col-toggle {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  flex: 1;
  min-inline-size: 0;
  align-self: stretch;
  cursor: pointer;
}
.col-toggle.is-locked { cursor: default; }

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

.live-region, .locked-description {
  position: absolute; width: 1px; height: 1px;
  overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap;
}
`;

function cloneColumns(columns) {
  const copy = columns.map((col) => Object.assign({}, col))
  return copy
}

export class MjColumnPicker extends MjElement {
  static tagName = "mj-column-picker";
  static styles = STYLES;
  static watched = ["apply-mode", "variant", "label", "open", "disabled", "reorderable", "min-visible"];

  constructor() {
    super()
    this._columns = []
    this._defaultColumns = []
    this._hasExplicitDefaults = false
    this._hasDefaultSnapshot = false

    /* Deferred mode: the copy being edited while the panel is open. */
    this._pendingColumns = null

    /* Keyboard / pointer reorder in progress: key of the grabbed column. */
    this._grabKey = null
    this._grabOriginalOrder = null
    this._pointerDrag = null
    this._suppressHandleClick = false

    this._isOpen = false
    this._releaseFocusTrap = null
    this._stopPositioning = null
    this._panelId = nextId("mj-cp-panel")
    this._lockedDescId = nextId("mj-cp-locked")
  }

  render() {
    /* Labels are applied in afterRender with textContent / setAttribute. */
    const markup = `
      <button type="button" class="trigger-btn" part="trigger-button"
              aria-haspopup="dialog"
              aria-expanded="false"
              aria-controls="${this._panelId}">
        <span aria-hidden="true">⊞</span>
        <span class="trigger-label"></span>
      </button>
      <div class="panel" part="panel"
           id="${this._panelId}"
           role="dialog"
           aria-hidden="true">
        <div class="panel-header-slot" part="panel-header">
          <slot name="panel-header"><span class="panel-title"></span></slot>
        </div>
        <ul class="column-list" part="column-list" role="list"></ul>
        <div class="panel-footer" part="panel-footer">
          <button type="button" class="footer-btn" part="reset-button"></button>
          <slot name="panel-footer"></slot>
          <button type="button" class="footer-btn primary apply-btn" part="apply-button"></button>
        </div>
        <span class="locked-description" id="${this._lockedDescId}"></span>
      </div>
      <div class="live-region" aria-live="assertive" aria-atomic="true"></div>
    `
    return markup
  }

  afterRender() {
    this._triggerBtn = this.$(".trigger-btn")
    this._triggerLabel = this.$(".trigger-label")
    this._panel = this.$(".panel")
    this._panelTitle = this.$(".panel-title")
    this._columnList = this.$(".column-list")
    this._resetBtn = this.$(".footer-btn[part='reset-button']")
    this._applyBtn = this.$(".apply-btn")
    this._liveRegion = this.$(".live-region")
    this._resetBtn.textContent = t("mj.columnPicker.reset")
    this._applyBtn.textContent = t("mj.columnPicker.apply")
    this.$(".locked-description").textContent = t("mj.columnPicker.lockedDescription")
    this._isOpen = false
    this._grabKey = null
    this._pointerDrag = null

    /* A native <button> clicks on Enter / Space; no keydown handler needed. */
    this.listen(this._triggerBtn, "click", () => { this._toggle() })
    this.listen(this._resetBtn, "click", () => { this._handleReset() })
    this.listen(this._applyBtn, "click", () => { this._handleApply() })

    /* Delegated list listeners: rows are moved and rebuilt freely. */
    this.listen(this._columnList, "change", this._onListChange.bind(this))
    this.listen(this._columnList, "click", this._onListClick.bind(this))
    this.listen(this._columnList, "keydown", this._onListKeydown.bind(this))
    this.listen(this._columnList, "pointerdown", this._onHandlePointerDown.bind(this))
    this.listen(this._columnList, "pointermove", this._onHandlePointerMove.bind(this))
    this.listen(this._columnList, "pointerup", this._onHandlePointerUp.bind(this))
    this.listen(this._columnList, "pointercancel", this._onHandlePointerUp.bind(this))

    this.listen(document, "click", (e) => {
      if (this.hasAttribute("open") === true && e.composedPath().indexOf(this) < 0) {
        this._close()
      }
    })

    this.listen(document, "keydown", (e) => {
      if (e.key === "Escape" && this.hasAttribute("open") === true) {
        this._close()
      }
    })

    this.onTeardown(() => { this._teardownOpenState() })

    this._syncLabel()
    this._syncDisabled()
    this._syncApplyMode()
    this._renderColumnList()

    if (this.hasAttribute("open") === true) {
      this._openPanel()
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
      this._syncDisabled()
    }
    if (name === "label") {
      this._syncLabel()
    }
    if (name === "apply-mode") {
      this._syncApplyMode()
    }
    if (name === "reorderable") {
      this._renderColumnList()
    }
    return
  }

  /* ----- attribute state ----- */

  _syncLabel() {
    const label = this.getAttribute("label") || t("mj.columnPicker.label")
    this._triggerBtn.setAttribute("aria-label", label)
    this._triggerLabel.textContent = label
    this._panelTitle.textContent = label
    this._panel.setAttribute("aria-label", t("mj.columnPicker.panelLabel", { label: label }))
    return
  }

  _syncDisabled() {
    const isDisabled = this.hasAttribute("disabled")
    this._triggerBtn.disabled = isDisabled
    if (isDisabled === true && this.hasAttribute("open") === true) {
      this._close()
    }
    return
  }

  _isDeferred() {
    const deferred = (this.getAttribute("apply-mode") || "immediate") === "deferred"
    return deferred
  }

  _syncApplyMode() {
    const deferred = this._isDeferred()
    this._applyBtn.style.display = deferred === true ? "" : "none"
    if (this._isOpen === true) {
      this._pendingColumns = deferred === true ? cloneColumns(this._columns) : null
      this._renderColumnList()
    }
    return
  }

  /* The columns being edited: the pending copy in deferred mode. */
  _workingColumns() {
    const working = this._pendingColumns !== null ? this._pendingColumns : this._columns
    return working
  }

  /* ----- open / close ----- */

  _toggle() {
    if (this.hasAttribute("open") === true) {
      this._close()
    } else {
      this._open()
    }
    return
  }

  _open() {
    if (this.hasAttribute("disabled") === false) {
      this.setAttribute("open", "")
    }
    return
  }

  _close() {
    this.removeAttribute("open")
    return
  }

  _openPanel() {
    if (this._isOpen === true) {
      return
    }
    this._isOpen = true
    this._pendingColumns = this._isDeferred() === true ? cloneColumns(this._columns) : null
    this._panel.setAttribute("aria-hidden", "false")
    this._triggerBtn.setAttribute("aria-expanded", "true")
    this._renderColumnList()
    this._stopPositioning = autoPosition(this._panel, this._triggerBtn, { placement: "bottom-start", offset: 4 })
    this._releaseFocusTrap = trapFocus(this._panel)
    this.emit("mj-picker-open", {})
    return
  }

  _closePanel() {
    if (this._isOpen === false) {
      return
    }

    /* Where focus is decides whether the trigger takes it back. */
    const active = this.shadowRoot.activeElement
    const focusWasInPanel = active !== null && this._panel.contains(active) === true

    if (this._grabKey !== null) {
      this._cancelGrab()
    }
    this._teardownOpenState(focusWasInPanel)
    this._pendingColumns = null
    this._panel.setAttribute("aria-hidden", "true")
    this._triggerBtn.setAttribute("aria-expanded", "false")

    if (focusWasInPanel === true) {
      this._triggerBtn.focus()
    }
    this.emit("mj-picker-close", {})
    return
  }

  /* Release the focus trap and the positioning listeners. */
  _teardownOpenState(restoreFocus) {
    if (this._releaseFocusTrap !== null) {
      /* The trap restores focus only when focus was still inside the panel. */
      this._releaseFocusTrap({ restoreFocus: restoreFocus === true })
      this._releaseFocusTrap = null
    }
    if (this._stopPositioning !== null) {
      this._stopPositioning()
      this._stopPositioning = null
    }
    this._isOpen = false
    return
  }

  /* ----- list rendering ----- */

  _renderColumnList() {
    this._columnList.replaceChildren()
    const reorderable = this.getAttribute("reorderable") !== "false"
    const cols = this._workingColumns()

    for (let idx = 0; idx < cols.length; idx = idx + 1) {
      const col = cols[idx]
      const label = col.label !== undefined && col.label !== null ? String(col.label) : String(col.key)
      const li = document.createElement("li")
      li.className = "column-item"
      li.setAttribute("part", "column-item")
      li.setAttribute("role", "listitem")
      li.setAttribute("data-col-key", col.key)

      if (reorderable === true && col.locked !== true) {
        const handle = document.createElement("button")
        handle.type = "button"
        handle.className = "drag-handle"
        handle.setAttribute("part", "column-drag-handle")
        handle.setAttribute("aria-label", t("mj.columnPicker.reorderColumn", { label: label }))
        handle.setAttribute("aria-pressed", "false")
        handle.textContent = "⠿"
        li.appendChild(handle)
      } else {
        const placeholder = document.createElement("span")
        placeholder.className = "handle-placeholder"
        li.appendChild(placeholder)
      }

      /* A real <label>: clicking the column name toggles its checkbox. */
      const toggle = document.createElement("label")
      toggle.className = col.locked === true ? "col-toggle is-locked" : "col-toggle"

      const checkbox = document.createElement("input")
      checkbox.type = "checkbox"
      checkbox.className = "col-checkbox"
      checkbox.setAttribute("part", "column-checkbox")
      checkbox.checked = col.visible !== false
      if (col.locked === true) {
        checkbox.disabled = true
        checkbox.setAttribute("aria-describedby", this._lockedDescId)
      }
      toggle.appendChild(checkbox)

      const labelEl = document.createElement("span")
      labelEl.className = col.visible !== false ? "col-label" : "col-label hidden-col"
      labelEl.setAttribute("part", "column-label")
      labelEl.textContent = label
      toggle.appendChild(labelEl)

      li.appendChild(toggle)
      this._columnList.appendChild(li)
    }
    return
  }

  _itemForKey(key) {
    let found = null
    const items = this._columnList.children
    for (let i = 0; i < items.length; i = i + 1) {
      if (items[i].getAttribute("data-col-key") === String(key)) {
        found = items[i]
        break
      }
    }
    return found
  }

  _keyFromEvent(event) {
    let key = null
    if (event.target instanceof Element) {
      const li = event.target.closest(".column-item")
      if (li !== null) {
        key = li.getAttribute("data-col-key")
      }
    }
    return key
  }

  _indexOfKey(key) {
    const index = this._workingColumns().findIndex((c) => String(c.key) === String(key))
    return index
  }

  /* ----- visibility ----- */

  _onListChange(event) {
    const checkbox = event.target
    if (!(checkbox instanceof HTMLInputElement) || checkbox.classList.contains("col-checkbox") === false) {
      return
    }
    const key = this._keyFromEvent(event)
    if (key !== null) {
      this._handleVisibilityChange(key, checkbox)
    }
    return
  }

  _handleVisibilityChange(key, checkbox) {
    const visible = checkbox.checked
    const parsedMin = parseInt(this.getAttribute("min-visible") || "1", 10)
    const minVisible = Number.isNaN(parsedMin) === true ? 1 : parsedMin
    const cols = this._workingColumns()
    const colIdx = this._indexOfKey(key)
    if (colIdx < 0) {
      return
    }
    const col = cols[colIdx]

    if (visible === false) {
      /* Counted in the copy being edited, so deferred mode is held to it too. */
      const remaining = cols.filter((c) => c.visible !== false && c !== col)
      if (remaining.length < minVisible) {
        this._liveRegion.textContent = t("mj.columnPicker.minVisible", { count: minVisible })
        checkbox.checked = true
        return
      }
    }

    col.visible = visible
    const labelEl = checkbox.parentElement.querySelector(".col-label")
    if (labelEl !== null) {
      labelEl.className = visible === true ? "col-label" : "col-label hidden-col"
    }

    if (this._isDeferred() === false) {
      this.emit("mj-column-visibility-change", {
        key: col.key,
        visible: visible,
        columns: this._columns.slice()
      })
      announce(visible === true
        ? t("mj.columnPicker.columnShown", { label: col.label })
        : t("mj.columnPicker.columnHidden", { label: col.label }))
    }
    return
  }

  /* ----- reorder: shared ----- */

  _startGrab(key) {
    this._grabKey = key
    this._grabOriginalOrder = this._workingColumns().slice()
    const li = this._itemForKey(key)
    if (li !== null) {
      li.classList.add("grabbed")
      const handle = li.querySelector(".drag-handle")
      if (handle !== null) {
        handle.setAttribute("aria-pressed", "true")
      }
    }
    return
  }

  _clearGrabUI() {
    const grabbed = this._columnList.querySelectorAll(".grabbed")
    for (let i = 0; i < grabbed.length; i = i + 1) {
      grabbed[i].classList.remove("grabbed")
      const handle = grabbed[i].querySelector(".drag-handle")
      if (handle !== null) {
        handle.setAttribute("aria-pressed", "false")
      }
    }
    return
  }

  /*
   * Move the grabbed column to `targetIdx`. The array entry and the row
   * element are both moved (the list is not rebuilt), and focus stays on
   * the row's handle so the keyboard interaction can continue.
   */
  _moveGrabbedTo(targetIdx) {
    const cols = this._workingColumns()
    const fromIdx = this._indexOfKey(this._grabKey)
    if (fromIdx < 0 || targetIdx < 0 || targetIdx >= cols.length || targetIdx === fromIdx) {
      return
    }
    if (cols[targetIdx].locked === true) {
      return
    }

    /* Swap with the target so locked columns in between keep their place. */
    const moved = cols[fromIdx]
    cols[fromIdx] = cols[targetIdx]
    cols[targetIdx] = moved

    const movedEl = this._itemForKey(moved.key)
    const otherEl = this._itemForKey(cols[fromIdx].key)
    const hadFocus = movedEl.contains(this.shadowRoot.activeElement)
    const marker = document.createComment("")
    this._columnList.replaceChild(marker, movedEl)
    this._columnList.replaceChild(movedEl, otherEl)
    this._columnList.replaceChild(otherEl, marker)

    if (hadFocus === true) {
      const handle = movedEl.querySelector(".drag-handle")
      if (handle !== null) {
        handle.focus()
      }
    }

    this._liveRegion.textContent = t("mj.columnPicker.movedToPositionOf", { label: moved.label, position: targetIdx + 1, total: cols.length })
    return
  }

  /* Step the grabbed column up (-1) or down (+1), skipping locked columns. */
  _moveGrabbed(delta) {
    if (this._grabKey === null) {
      return
    }
    const cols = this._workingColumns()
    let targetIdx = this._indexOfKey(this._grabKey) + delta
    while (targetIdx >= 0 && targetIdx < cols.length && cols[targetIdx].locked === true) {
      targetIdx = targetIdx + delta
    }
    this._moveGrabbedTo(targetIdx)
    return
  }

  _confirmGrab() {
    if (this._grabKey === null) {
      return
    }
    const key = this._grabKey
    const original = this._grabOriginalOrder
    const cols = this._workingColumns()
    const from = original.findIndex((c) => String(c.key) === String(key))
    const to = this._indexOfKey(key)
    this._grabKey = null
    this._grabOriginalOrder = null
    this._clearGrabUI()

    if (from === to) {
      return
    }
    if (this._isDeferred() === false) {
      this.emit("mj-column-reorder", {
        key: cols[to].key,
        from: from,
        to: to,
        columns: this._columns.slice()
      })
    }
    announce(t("mj.columnPicker.movedToPosition", { label: cols[to].label, position: to + 1 }))
    return
  }

  /* Put every column back where it was when the grab started. */
  _cancelGrab() {
    if (this._grabKey === null) {
      return
    }
    const key = this._grabKey
    const original = this._grabOriginalOrder
    const cols = this._workingColumns()
    const hadFocus = this._columnList.contains(this.shadowRoot.activeElement)

    cols.splice(0, cols.length, ...original)
    this._grabKey = null
    this._grabOriginalOrder = null
    this._renderColumnList()

    if (hadFocus === true) {
      const li = this._itemForKey(key)
      const handle = li !== null ? li.querySelector(".drag-handle") : null
      if (handle !== null) {
        handle.focus()
      }
    }
    this._liveRegion.textContent = t("mj.columnPicker.reorderCanceled")
    return
  }

  /* ----- reorder: keyboard and click ----- */

  _onListClick(event) {
    const target = event.target
    if (!(target instanceof Element) || target.closest(".drag-handle") === null) {
      return
    }
    if (this._suppressHandleClick === true) {
      /* The click that ends a pointer drag. */
      this._suppressHandleClick = false
      return
    }
    /* Space / Enter on the handle arrive here as a click as well. */
    const key = this._keyFromEvent(event)
    if (this._grabKey !== null && this._grabKey === key) {
      this._confirmGrab()
    } else {
      if (this._grabKey !== null) {
        this._confirmGrab()
      }
      this._startGrab(key)
      this._liveRegion.textContent = t("mj.columnPicker.grabbed")
    }
    return
  }

  _onListKeydown(event) {
    const target = event.target
    if (!(target instanceof Element) || target.closest(".drag-handle") === null) {
      return
    }
    const key = this._keyFromEvent(event)
    if (this._grabKey === null || this._grabKey !== key) {
      return
    }

    if (event.key === "ArrowUp") {
      event.preventDefault()
      this._moveGrabbed(-1)
    } else if (event.key === "ArrowDown") {
      event.preventDefault()
      this._moveGrabbed(1)
    } else if (event.key === "Escape") {
      /* Cancels the move only; the panel stays open. */
      event.preventDefault()
      event.stopPropagation()
      this._cancelGrab()
    } else if (event.key === "Tab") {
      this._confirmGrab()
    }
    return
  }

  /* ----- reorder: pointer drag ----- */

  _onHandlePointerDown(event) {
    const target = event.target
    if (!(target instanceof Element) || target.closest(".drag-handle") === null) {
      return
    }
    if (event.button !== undefined && event.button !== 0) {
      return
    }
    const handle = target.closest(".drag-handle")
    this._pointerDrag = {
      key: this._keyFromEvent(event),
      startY: event.clientY,
      moved: false,
      startedGrab: false,
      handle: handle
    }
    if (typeof handle.setPointerCapture === "function" && event.pointerId !== undefined) {
      try {
        handle.setPointerCapture(event.pointerId)
      } catch (error) {
        /* Synthetic events carry no active pointer. */
      }
    }
    return
  }

  _onHandlePointerMove(event) {
    const drag = this._pointerDrag
    if (drag === null) {
      return
    }
    if (drag.moved === false && Math.abs(event.clientY - drag.startY) < 4) {
      return
    }
    if (drag.moved === false) {
      drag.moved = true
      if (this._grabKey !== drag.key) {
        if (this._grabKey !== null) {
          this._confirmGrab()
        }
        this._startGrab(drag.key)
        drag.startedGrab = true
      }
    }

    /* The row under the pointer is where the grabbed column goes. */
    const items = this._columnList.children
    let targetIdx = -1
    for (let i = 0; i < items.length; i = i + 1) {
      const rect = items[i].getBoundingClientRect()
      if (event.clientY >= rect.top && event.clientY < rect.bottom) {
        targetIdx = i
        break
      }
    }
    if (targetIdx >= 0) {
      this._moveGrabbedTo(targetIdx)
    }
    return
  }

  _onHandlePointerUp(event) {
    const drag = this._pointerDrag
    if (drag === null) {
      return
    }
    this._pointerDrag = null
    if (drag.moved === true) {
      this._confirmGrab()
      this._suppressHandleClick = true
      window.setTimeout(() => { this._suppressHandleClick = false }, 0)
    }
    return
  }

  /* ----- reset / apply ----- */

  _handleReset() {
    this._grabKey = null
    this._grabOriginalOrder = null
    this._columns = cloneColumns(this._defaultColumns)
    this._pendingColumns = this._isDeferred() === true && this._isOpen === true ? cloneColumns(this._columns) : null
    this._renderColumnList()
    this.emit("mj-columns-reset", { columns: this._columns.slice() })
    announce(t("mj.columnPicker.columnsReset"))
    return
  }

  _handleApply() {
    if (this._grabKey !== null) {
      this._confirmGrab()
    }
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
    this._columns = Array.isArray(value) === true ? cloneColumns(value) : []

    /* Without explicit defaults, the first assignment is what Reset restores. */
    if (this._hasExplicitDefaults === false && this._hasDefaultSnapshot === false && this._columns.length > 0) {
      this._defaultColumns = cloneColumns(this._columns)
      this._hasDefaultSnapshot = true
    }

    if (this._columnList !== undefined && this._columnList !== null) {
      this._grabKey = null
      this._grabOriginalOrder = null
      this._pendingColumns = this._isDeferred() === true && this._isOpen === true ? cloneColumns(this._columns) : null
      this._renderColumnList()
    }
    return
  }

  get defaultColumns() {
    return this._defaultColumns
  }

  set defaultColumns(value) {
    this._defaultColumns = Array.isArray(value) === true ? cloneColumns(value) : []
    this._hasExplicitDefaults = Array.isArray(value) === true
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
