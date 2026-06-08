/*
 * mjsplitpane.js
 *
 * <mj-split-pane> -- divides a container into two adjacent resizable regions
 * separated by a keyboard-operable draggable separator.
 */

import { MjElement } from "../core/mjelement.js";

const STEP = 8;

const STYLES = `
:host {
  display: flex;
  overflow: hidden;
  position: relative;
  block-size: 100%;
  inline-size: 100%;
}

:host([orientation="vertical"]) {
  flex-direction: column;
}

.pane {
  overflow: auto;
  min-inline-size: 0;
  min-block-size: 0;
  flex-shrink: 0;
}

.pane-end {
  flex: 1 1 0;
  min-inline-size: 0;
  min-block-size: 0;
  overflow: auto;
}

.separator {
  flex-shrink: 0;
  background: var(--mj-split-separator-color, var(--mj-border));
  inline-size: var(--mj-split-separator-size, 4px);
  block-size: 100%;
  cursor: col-resize;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background var(--mj-motion-fast) var(--mj-motion-ease);
  touch-action: none;
  user-select: none;
}

:host([orientation="vertical"]) .separator {
  block-size: var(--mj-split-separator-size, 4px);
  inline-size: 100%;
  cursor: row-resize;
}

.separator:hover,
.separator:focus-visible {
  background: var(--mj-split-separator-hover-color, var(--mj-accent));
}

.separator:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

:host([disabled]) .separator {
  cursor: default;
  pointer-events: none;
}

.handle {
  width: var(--mj-split-handle-size, 24px);
  height: 4px;
  border-radius: var(--mj-radius-pill);
  background: currentColor;
  opacity: 0.5;
}

:host([orientation="vertical"]) .handle {
  width: 4px;
  height: var(--mj-split-handle-size, 24px);
}
`;

export class MjSplitPane extends MjElement {
  static tagName = "mj-split-pane";
  static styles = STYLES;
  static watched = ["orientation", "initial-size", "min", "max", "disabled", "persist-key"];

  constructor() {
    super()
    this._startPane = null
    this._separator = null
    this._dragging = false
    this._lastSize = null
    this._resizeObserver = null
  }

  render() {
    const initialSize = this.getAttribute("initial-size") || "50%"
    const separatorLabel = this.getAttribute("separator-label") || "Resize"
    const markup = `
      <div class="pane" part="start-pane" style="flex-basis: ${initialSize}">
        <slot name="start"></slot>
      </div>
      <div
        class="separator"
        part="separator"
        role="separator"
        tabindex="0"
        aria-label="${separatorLabel}"
        aria-valuenow="0"
        aria-valuemin="0"
        aria-valuemax="100"
        aria-valuetext="50%"
      >
        <div class="handle" part="separator-handle"></div>
      </div>
      <div class="pane pane-end" part="end-pane">
        <slot name="end"></slot>
      </div>
    `
    return markup
  }

  afterRender() {
    this._startPane = this.$(".pane")
    this._separator = this.$(".separator")
    this._endPane = this.$(".pane-end")

    this.listen(this._separator, "pointerdown", this._onPointerDown.bind(this))
    this.listen(this._separator, "keydown", this._onSepKeyDown.bind(this))
    this.listen(this._separator, "dblclick", this._onDblClick.bind(this))

    this._restorePersisted()
    this._updateAria()
    return
  }

  onConnected() {
    if (typeof ResizeObserver === "function") {
      this._resizeObserver = new ResizeObserver(() => {
        this._updateAria()
      })
      this._resizeObserver.observe(this)
    }
    return
  }

  onDisconnected() {
    if (this._resizeObserver !== null) {
      this._resizeObserver.disconnect()
      this._resizeObserver = null
    }
    return
  }

  _onPointerDown(event) {
    if (this.hasAttribute("disabled")) {
      return
    }
    this._dragging = true
    this._separator.setPointerCapture(event.pointerId)
    this.listen(this._separator, "pointermove", this._onPointerMove.bind(this))
    this.listen(this._separator, "pointerup", this._onPointerUp.bind(this))
    return
  }

  _onPointerMove(event) {
    if (this._dragging === false) {
      return
    }
    const orientation = this.getAttribute("orientation") || "horizontal"
    const rect = this.getBoundingClientRect()
    let newSize

    if (orientation === "vertical") {
      newSize = event.clientY - rect.top
    } else {
      newSize = event.clientX - rect.left
    }

    newSize = this._clampSize(newSize)
    this._applySize(newSize)
    this.emit("mj-split-resize", { size: newSize, ratio: this.ratio })
    return
  }

  _onPointerUp(event) {
    if (this._dragging === false) {
      return
    }
    this._dragging = false
    const newSize = this._getCurrentSize()
    this._persistSize()
    this.emit("mj-split-resize-end", { size: newSize, ratio: this.ratio })
    return
  }

  _onSepKeyDown(event) {
    if (this.hasAttribute("disabled")) {
      return
    }

    const orientation = this.getAttribute("orientation") || "horizontal"
    const isRTL = getComputedStyle(this).direction === "rtl"
    let delta = 0

    if (orientation === "horizontal") {
      if (event.key === "ArrowLeft") {
        delta = isRTL === true ? STEP : -STEP
      } else if (event.key === "ArrowRight") {
        delta = isRTL === true ? -STEP : STEP
      } else if (event.key === "Home") {
        event.preventDefault()
        this._applySize(this._parseMin())
        return
      } else if (event.key === "End") {
        event.preventDefault()
        this._applySize(this._parseMax())
        return
      }
    } else {
      if (event.key === "ArrowUp") {
        delta = -STEP
      } else if (event.key === "ArrowDown") {
        delta = STEP
      } else if (event.key === "Home") {
        event.preventDefault()
        this._applySize(this._parseMin())
        return
      } else if (event.key === "End") {
        event.preventDefault()
        this._applySize(this._parseMax())
        return
      }
    }

    if (delta !== 0) {
      event.preventDefault()
      const current = this._getCurrentSize()
      const newSize = this._clampSize(current + delta)
      this._applySize(newSize)
      this._persistSize()
      this.emit("mj-split-resize-end", { size: newSize, ratio: this.ratio })
    }
    return
  }

  _onDblClick() {
    const collapsible = this.getAttribute("collapsible") || "none"
    if (collapsible === "none") {
      return
    }
    const current = this._getCurrentSize()
    const min = this._parseMin()
    if (Math.abs(current - min) < 2) {
      const last = this._lastSize || this._parseTotalSize() * 0.5
      this._applySize(last)
      this.emit("mj-split-expand", { pane: "start" })
    } else {
      this._lastSize = current
      this._applySize(min)
      this.emit("mj-split-collapse", { pane: "start" })
    }
    return
  }

  _getCurrentSize() {
    const orientation = this.getAttribute("orientation") || "horizontal"
    if (this._startPane === null) {
      return 0
    }
    if (orientation === "vertical") {
      return this._startPane.getBoundingClientRect().height
    }
    return this._startPane.getBoundingClientRect().width
  }

  _parseTotalSize() {
    const orientation = this.getAttribute("orientation") || "horizontal"
    const rect = this.getBoundingClientRect()
    return orientation === "vertical" ? rect.height : rect.width
  }

  _parseMin() {
    const minAttr = this.getAttribute("min") || "80px"
    const parsed = parseFloat(minAttr)
    return Number.isNaN(parsed) === false ? parsed : 80
  }

  _parseMax() {
    const total = this._parseTotalSize()
    const maxAttr = this.getAttribute("max") || ""
    if (maxAttr.length === 0) {
      return total - this._parseMin()
    }
    const parsed = parseFloat(maxAttr)
    return Number.isNaN(parsed) === false ? parsed : total - this._parseMin()
  }

  _clampSize(size) {
    const min = this._parseMin()
    const max = this._parseMax()
    return Math.max(min, Math.min(max, size))
  }

  _applySize(size) {
    if (this._startPane === null) {
      return
    }
    this._startPane.style.flexBasis = size + "px"
    this._startPane.style.flexGrow = "0"
    this._startPane.style.flexShrink = "0"
    this._updateAria()
    return
  }

  _updateAria() {
    if (this._separator === null) {
      return
    }
    const current = this._getCurrentSize()
    const min = this._parseMin()
    const max = this._parseMax()
    this._separator.setAttribute("aria-valuenow", Math.round(current).toString())
    this._separator.setAttribute("aria-valuemin", Math.round(min).toString())
    this._separator.setAttribute("aria-valuemax", Math.round(max).toString())
    this._separator.setAttribute("aria-valuetext", `Start pane: ${Math.round(current)} pixels`)
    return
  }

  _persistSize() {
    const key = this.getAttribute("persist-key") || ""
    if (key.length === 0) {
      return
    }
    try {
      localStorage.setItem(key, String(this._getCurrentSize()))
    } catch (err) {
      // storage not available
    }
    return
  }

  _restorePersisted() {
    const key = this.getAttribute("persist-key") || ""
    if (key.length === 0) {
      return
    }
    try {
      const stored = localStorage.getItem(key)
      if (stored !== null) {
        const size = parseFloat(stored)
        if (Number.isNaN(size) === false) {
          this._applySize(size)
        }
      }
    } catch (err) {
      // storage not available
    }
    return
  }

  get size() {
    return this._getCurrentSize()
  }

  set size(value) {
    const clamped = this._clampSize(Number(value))
    this._applySize(clamped)
    return
  }

  get ratio() {
    const total = this._parseTotalSize()
    if (total === 0) {
      return 0.5
    }
    return this._getCurrentSize() / total
  }
}
