/*
 * mjsplitpane.js
 *
 * <mj-split-pane> -- divides a container into two adjacent resizable regions
 * separated by a keyboard-operable draggable separator.
 *
 * Sizing model
 *   - Until the user resizes it, the start pane has the `initial-size` the
 *     author gave (any CSS length or percentage), kept inside `min` / `max`.
 *   - Once the user drags, uses the keyboard or the `size` property is set,
 *     the split is remembered as a RATIO of the container. The ratio is
 *     re-applied whenever the container changes size, so the panes stay in
 *     proportion and the separator can never be pushed out of view.
 *   - The state lives in fields and survives a disconnect / reconnect.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";

/* Pixels moved by one arrow-key press. */
const STEP = 8;

const DEFAULT_MIN = 80;
const DEFAULT_INITIAL_SIZE = "50%";
const DEFAULT_SEPARATOR_LABEL_KEY = "mj.splitPane.resize";

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

/*
 * disabled locks the separator only. The shared base sheet turns pointer
 * events off for every disabled host, which would make the content of both
 * panes unclickable; undo that here and disable just the separator below.
 */
:host([disabled]) {
  pointer-events: auto;
  cursor: auto;
}

/*
 * As a band of an mj-dock-layout the split pane must not claim the whole
 * layout along the axis it consumes; the author sizes it on that axis.
 */
:host([dock="top"]),
:host([dock="bottom"]) {
  block-size: auto;
}

:host([dock="start"]),
:host([dock="end"]) {
  inline-size: auto;
}

.pane {
  position: relative;
  overflow: auto;
  min-inline-size: 0;
  min-block-size: 0;
}

.pane-start {
  flex: 0 0 auto;
}

.pane-end {
  flex: 1 1 0;
}

/* A collapsed pane has no size; keep its content out of the tab order too. */
:host([collapsed="start"]) .pane-start,
:host([collapsed="end"]) .pane-end {
  visibility: hidden;
}

.separator {
  flex: 0 0 auto;
  align-self: stretch;
  background: var(--mj-split-separator-color, var(--mj-border));
  inline-size: var(--mj-split-separator-size, 4px);
  cursor: col-resize;
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background var(--mj-motion-fast) var(--mj-motion-ease);
  touch-action: none;
  user-select: none;
}

:host([orientation="vertical"]) .separator {
  block-size: var(--mj-split-separator-size, 4px);
  inline-size: auto;
  cursor: row-resize;
}

/* Widen the pointer target beyond the thin visible bar. */
.separator::before {
  content: "";
  position: absolute;
  inset-block: 0;
  inset-inline: calc(-1 * var(--mj-split-separator-hit-slop, 6px));
}

:host([orientation="vertical"]) .separator::before {
  inset-inline: 0;
  inset-block: calc(-1 * var(--mj-split-separator-hit-slop, 6px));
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
  position: relative;
  inline-size: 2px;
  block-size: var(--mj-split-handle-size, 24px);
  max-block-size: 100%;
  border-radius: var(--mj-radius-pill);
  background: currentColor;
  opacity: 0.5;
}

:host([orientation="vertical"]) .handle {
  inline-size: var(--mj-split-handle-size, 24px);
  max-inline-size: 100%;
  block-size: 2px;
  max-block-size: none;
}
`;

/*
 * Resolve a length written as a number ("120"), in px, %, rem or em to
 * pixels. Percentages are taken of `total`. Returns null for anything else
 * (calc(), viewport units, keywords), which the caller resolves another way.
 */
function resolveLength(text, total, element) {
  let pixels = null

  if (text !== null && text !== undefined) {
    const match = /^\s*(\d*\.?\d+)\s*(px|%|rem|em)?\s*$/.exec(text)

    if (match !== null) {
      const amount = parseFloat(match[1])
      const unit = match[2] !== undefined ? match[2] : "px"

      if (unit === "px") {
        pixels = amount
      } else if (unit === "%") {
        pixels = total * amount / 100
      } else if (unit === "rem") {
        pixels = amount * parseFloat(window.getComputedStyle(document.documentElement).fontSize)
      } else {
        pixels = amount * parseFloat(window.getComputedStyle(element).fontSize)
      }
    }
  }

  return pixels
}

export class MjSplitPane extends MjElement {
  static tagName = "mj-split-pane";
  static styles = STYLES;
  static watched = [
    "orientation", "initial-size", "min", "max", "disabled", "persist-key",
    "separator-label", "collapsible"
  ];

  constructor() {
    super()
    this._startPaneId = nextId("mj-split-start")
    this._startPane = null
    this._endPane = null
    this._separator = null
    this._resizeObserver = null
    this._layoutFrame = null

    /*
     * The split the user chose, as start-pane size / container size. null
     * until the first resize: the `initial-size` attribute applies until then.
     */
    this._ratio = null

    /* A start-pane size in pixels restored from storage written by an older version. */
    this._legacySize = null

    /* "start" | "end" while a pane is collapsed, otherwise null. */
    this._collapsedPane = null

    /* The start-pane size in pixels that the last layout applied. */
    this._currentSize = 0

    /* Attribute values already acted on, so replayed changes are no-ops. */
    this._appliedInitialSize = null
    this._restoredKey = null

    /* { pointerId, origin, startSize, changed } while the separator is dragged. */
    this._drag = null

    this._warnedMinMax = false
  }

  render() {
    const markup = html`
      <div class="pane pane-start" part="start-pane" id="${this._startPaneId}">
        <slot name="start"></slot>
      </div>
      <div
        class="separator"
        part="separator"
        role="separator"
        tabindex="0"
        aria-controls="${this._startPaneId}"
        aria-valuenow="0"
        aria-valuemin="0"
        aria-valuemax="0"
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
    this._startPane = this.$(".pane-start")
    this._separator = this.$(".separator")
    this._endPane = this.$(".pane-end")

    /*
     * All pointer listeners are registered once. Pointer capture routes the
     * move / up / cancel events of a drag to the separator.
     */
    this.listen(this._separator, "pointerdown", this._onPointerDown.bind(this))
    this.listen(this._separator, "pointermove", this._onPointerMove.bind(this))
    this.listen(this._separator, "pointerup", this._onPointerEnd.bind(this))
    this.listen(this._separator, "pointercancel", this._onPointerEnd.bind(this))
    this.listen(this._separator, "lostpointercapture", this._onPointerEnd.bind(this))
    this.listen(this._separator, "keydown", this._onSeparatorKeyDown.bind(this))
    this.listen(this._separator, "dblclick", this._onDoubleClick.bind(this))

    this._appliedInitialSize = this.getAttribute("initial-size")
    this._restorePersisted()
    this._syncSeparator()
    this._applyLayout()
    return
  }

  onConnected() {
    if (typeof ResizeObserver === "function") {
      this._resizeObserver = new ResizeObserver(() => {
        this._scheduleLayout()
      })
      this._resizeObserver.observe(this)
    }

    this.onTeardown(() => {
      if (this._resizeObserver !== null) {
        this._resizeObserver.disconnect()
        this._resizeObserver = null
      }
      if (this._layoutFrame !== null) {
        window.cancelAnimationFrame(this._layoutFrame)
        this._layoutFrame = null
      }
      this._drag = null
    })
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._separator === undefined || this._separator === null) {
      return
    }

    if (name === "initial-size") {
      /* A new initial size replaces whatever split was in effect. */
      if (newValue !== this._appliedInitialSize) {
        this._appliedInitialSize = newValue
        this._ratio = null
        this._legacySize = null
        this._collapsedPane = null
      }
    } else if (name === "persist-key") {
      this._restorePersisted()
    }

    this._syncSeparator()
    this._applyLayout()
    return
  }

  /* ----- geometry ----- */

  _isVertical() {
    const vertical = this.getAttribute("orientation") === "vertical"
    return vertical
  }

  /* The container size along the split axis, in layout pixels. */
  _totalSize() {
    const total = this._isVertical() === true ? this.clientHeight : this.clientWidth
    return total
  }

  /*
   * The range the start pane may take for a container of `total` pixels:
   *   available  the room both panes share (total minus the separator)
   *   min / max  the bounds of the start pane
   * `min` also protects the end pane when no `max` is given. When the
   * container is too small for both minimums the panes meet in the middle,
   * so neither pane -- nor the separator -- is ever pushed out of view.
   */
  _limits(total) {
    const vertical = this._isVertical()
    const separatorSize = vertical === true ? this._separator.offsetHeight : this._separator.offsetWidth
    const available = Math.max(0, total - separatorSize)

    let min = resolveLength(this.getAttribute("min"), total, this)
    if (min === null) {
      min = DEFAULT_MIN
    }

    const explicitMax = resolveLength(this.getAttribute("max"), total, this)
    let max = 0
    if (explicitMax !== null) {
      if (min > explicitMax && this._warnedMinMax === false) {
        this._warnedMinMax = true
        console.warn("[mj-split-pane] min is larger than max; min is clamped to max.")
      }
      max = Math.min(explicitMax, available)
      min = Math.min(min, max)
    } else {
      max = Math.max(available - min, available / 2)
      min = Math.min(min, available / 2)
    }

    const limits = { available: available, min: min, max: max }
    return limits
  }

  /* The `initial-size` attribute in pixels for a container of `total`. */
  _resolveInitialSize(total) {
    const attribute = this.getAttribute("initial-size")
    const text = attribute !== null && attribute.length > 0 ? attribute : DEFAULT_INITIAL_SIZE
    let size = resolveLength(text, total, this)

    if (size === null) {
      /*
       * Some other CSS length (calc(), vw, ...): let the browser resolve it
       * on the pane and measure the result. An invalid value is dropped by
       * the CSS parser, in which case the split starts in the middle.
       */
      this._startPane.style.flexBasis = ""
      this._startPane.style.flexBasis = text
      if (this._startPane.style.flexBasis.length > 0) {
        size = this._isVertical() === true ? this._startPane.offsetHeight : this._startPane.offsetWidth
      } else {
        size = total / 2
      }
    }

    return size
  }

  /*
   * Size the start pane from the current state (collapsed pane, remembered
   * ratio or initial size), clamped to the limits for the container's
   * current size, and refresh the separator's ARIA values. Idempotent; runs
   * after every state change and whenever the container resizes.
   */
  _applyLayout() {
    if (this._startPane === undefined || this._startPane === null) {
      return
    }

    const total = this._totalSize()

    if (total <= 0) {
      /* Not rendered yet: let CSS hold the size until there is a box to measure. */
      const attribute = this.getAttribute("initial-size")
      const fallback = attribute !== null && attribute.length > 0 ? attribute : DEFAULT_INITIAL_SIZE
      this._startPane.style.flexBasis = this._ratio !== null ? `${this._ratio * 100}%` : fallback
      return
    }

    if (this._legacySize !== null) {
      this._ratio = this._legacySize / total
      this._legacySize = null
    }

    const limits = this._limits(total)
    let size = 0

    if (this._collapsedPane === "start") {
      size = 0
    } else if (this._collapsedPane === "end") {
      size = limits.available
    } else {
      const wanted = this._ratio !== null ? this._ratio * total : this._resolveInitialSize(total)
      size = Math.max(limits.min, Math.min(limits.max, wanted))
    }

    this._currentSize = size
    this._startPane.style.flexBasis = `${size}px`

    if (this._collapsedPane !== null) {
      this.setAttribute("collapsed", this._collapsedPane)
    } else {
      this.removeAttribute("collapsed")
    }

    this._updateAria(limits)
    return
  }

  /* Coalesce container resizes into one layout on the next frame. */
  _scheduleLayout() {
    if (this._layoutFrame !== null) {
      return
    }
    this._layoutFrame = window.requestAnimationFrame(() => {
      this._layoutFrame = null
      this._applyLayout()
    })
    return
  }

  /*
   * The single path for a size chosen by the user or through the `size`
   * property: clamp it, remember it as a ratio, apply it. Returns true when
   * the start pane actually changed. A resize ends a collapsed state.
   */
  _setSize(size) {
    const total = this._totalSize()
    let changed = false

    if (total > 0 && Number.isNaN(size) === false) {
      const limits = this._limits(total)
      const clamped = Math.max(limits.min, Math.min(limits.max, size))
      const previousSize = this._currentSize
      const expandedPane = this._collapsedPane

      this._collapsedPane = null
      this._ratio = clamped / total
      this._applyLayout()

      changed = Math.abs(this._currentSize - previousSize) > 0.01
      if (expandedPane !== null) {
        this.emit("mj-split-expand", { pane: expandedPane })
      }
    }

    return changed
  }

  /* A resize has settled: store it and tell listeners. */
  _settle() {
    this._persist()
    this.emit("mj-split-resize-end", { size: this._currentSize, ratio: this.ratio })
    return
  }

  /* ----- separator state ----- */

  _syncSeparator() {
    const disabled = this.hasAttribute("disabled")
    const label = this.getAttribute("separator-label")

    this._separator.setAttribute(
      "aria-label",
      label !== null && label.length > 0 ? label : t(DEFAULT_SEPARATOR_LABEL_KEY)
    )

    /* A side-by-side split has a VERTICAL separator bar, and the reverse. */
    this._separator.setAttribute("aria-orientation", this._isVertical() === true ? "horizontal" : "vertical")

    if (disabled === true) {
      this._separator.setAttribute("aria-disabled", "true")
      this._separator.setAttribute("tabindex", "-1")
    } else {
      this._separator.removeAttribute("aria-disabled")
      this._separator.setAttribute("tabindex", "0")
    }
    return
  }

  _updateAria(limits) {
    const collapsible = this.getAttribute("collapsible") || "none"
    const startCollapses = collapsible === "start" || collapsible === "both" || this._collapsedPane === "start"
    const endCollapses = collapsible === "end" || collapsible === "both" || this._collapsedPane === "end"

    const current = Math.round(this._currentSize)
    const lowest = startCollapses === true ? 0 : Math.round(limits.min)
    const highest = endCollapses === true ? Math.round(limits.available) : Math.round(limits.max)

    this._separator.setAttribute("aria-valuenow", String(current))
    this._separator.setAttribute("aria-valuemin", String(lowest))
    this._separator.setAttribute("aria-valuemax", String(highest))
    this._separator.setAttribute("aria-valuetext", t("mj.splitPane.startPaneSize", { count: current, size: current }))
    return
  }

  /* ----- pointer ----- */

  /*
   * The pointer position along the split axis in layout pixels, growing
   * toward the END pane. In a right-to-left horizontal split the start pane
   * is on the right, so the axis is mirrored. A CSS transform on an ancestor
   * scales client coordinates; divide it back out.
   */
  _pointerPosition(event) {
    const rect = this.getBoundingClientRect()
    let position = 0

    if (this._isVertical() === true) {
      const scale = this.offsetHeight > 0 && rect.height > 0 ? rect.height / this.offsetHeight : 1
      position = event.clientY / scale
    } else {
      const scale = this.offsetWidth > 0 && rect.width > 0 ? rect.width / this.offsetWidth : 1
      const rtl = window.getComputedStyle(this).direction === "rtl"
      position = rtl === true ? -event.clientX / scale : event.clientX / scale
    }

    return position
  }

  _onPointerDown(event) {
    if (this.hasAttribute("disabled") === true || event.button !== 0) {
      return
    }

    this._drag = {
      pointerId: event.pointerId,
      origin: this._pointerPosition(event),
      startSize: this._currentSize,
      changed: false
    }

    try {
      this._separator.setPointerCapture(event.pointerId)
    } catch (error) {
      /* No active pointer with this id (a synthetic event); drag without capture. */
    }
    return
  }

  _onPointerMove(event) {
    if (this._drag === null || event.pointerId !== this._drag.pointerId) {
      return
    }

    const offset = this._pointerPosition(event) - this._drag.origin
    const changed = this._setSize(this._drag.startSize + offset)

    if (changed === true) {
      this._drag.changed = true
      this.emit("mj-split-resize", { size: this._currentSize, ratio: this.ratio })
    }
    return
  }

  /* pointerup, pointercancel and lostpointercapture all end the drag once. */
  _onPointerEnd(event) {
    if (this._drag === null || event.pointerId !== this._drag.pointerId) {
      return
    }

    const changed = this._drag.changed
    this._drag = null

    try {
      this._separator.releasePointerCapture(event.pointerId)
    } catch (error) {
      /* The capture was already released. */
    }

    if (changed === true) {
      this._settle()
    }
    return
  }

  _onDoubleClick(event) {
    this._toggleCollapse(event.shiftKey === true)
    return
  }

  /* ----- keyboard ----- */

  _onSeparatorKeyDown(event) {
    if (this.hasAttribute("disabled") === true) {
      return
    }

    const total = this._totalSize()
    if (total <= 0) {
      return
    }

    const limits = this._limits(total)
    const vertical = this._isVertical()
    const rtl = window.getComputedStyle(this).direction === "rtl"
    let target = null
    let handled = false

    if (vertical === false && event.key === "ArrowLeft") {
      target = this._currentSize + (rtl === true ? STEP : -STEP)
    } else if (vertical === false && event.key === "ArrowRight") {
      target = this._currentSize + (rtl === true ? -STEP : STEP)
    } else if (vertical === true && event.key === "ArrowUp") {
      target = this._currentSize - STEP
    } else if (vertical === true && event.key === "ArrowDown") {
      target = this._currentSize + STEP
    } else if (event.key === "Home") {
      target = limits.min
    } else if (event.key === "End") {
      target = limits.max
    } else if (event.key === "Enter") {
      handled = this._toggleCollapse(event.shiftKey === true)
    }

    if (target !== null) {
      handled = true
      const changed = this._setSize(target)
      if (changed === true) {
        this._settle()
      }
    }

    if (handled === true) {
      event.preventDefault()
    }
    return
  }

  /* ----- collapse ----- */

  /*
   * Collapse the collapsible pane, or restore it when a pane is collapsed.
   * With collapsible="both" the start pane collapses, or the end pane when
   * `preferEnd` is set (Shift+Enter / Shift+double-click). Returns true
   * when the gesture was acted on.
   */
  _toggleCollapse(preferEnd) {
    const collapsible = this.getAttribute("collapsible") || "none"
    let acted = false

    if (this.hasAttribute("disabled") === false && collapsible !== "none") {
      if (this._collapsedPane !== null) {
        this.expand()
        acted = true
      } else if (collapsible === "start" || collapsible === "end" || collapsible === "both") {
        let pane = collapsible === "end" ? "end" : "start"
        if (collapsible === "both" && preferEnd === true) {
          pane = "end"
        }
        this.collapse(pane)
        acted = true
      }
    }

    return acted
  }

  /*
   * Collapse the "start" or "end" pane to zero size. The split in effect is
   * kept and comes back with `expand()`.
   */
  collapse(pane) {
    const target = pane === "end" ? "end" : "start"
    if (this._collapsedPane === target) {
      return
    }

    if (this._ratio === null) {
      /* Remember the size in effect so expanding returns to it. */
      const total = this._totalSize()
      if (total > 0) {
        this._ratio = this._currentSize / total
      }
    }

    this._collapsedPane = target
    this._applyLayout()
    this.emit("mj-split-collapse", { pane: target })
    this._settle()
    return
  }

  /* Restore the collapsed pane to the split it had before. */
  expand() {
    const pane = this._collapsedPane
    if (pane === null) {
      return
    }

    this._collapsedPane = null
    this._applyLayout()
    this.emit("mj-split-expand", { pane: pane })
    this._settle()
    return
  }

  /* ----- persistence ----- */

  _persist() {
    const key = this.getAttribute("persist-key") || ""
    if (key.length === 0 || this._ratio === null) {
      return
    }

    try {
      const record = { ratio: this._ratio, collapsed: this._collapsedPane }
      localStorage.setItem(key, JSON.stringify(record))
    } catch (error) {
      /* Storage is not available. */
    }
    return
  }

  /*
   * Read the split stored under `persist-key`. Runs once per key so a
   * replayed attribute change or a reconnect does not overwrite the state
   * the element already has. An older version stored the start-pane size in
   * pixels as a bare number; that is converted on the next layout.
   */
  _restorePersisted() {
    const key = this.getAttribute("persist-key") || ""
    if (key.length === 0 || key === this._restoredKey) {
      return
    }
    this._restoredKey = key

    let stored = null
    try {
      stored = JSON.parse(localStorage.getItem(key))
    } catch (error) {
      /* Storage is not available or holds something else. */
    }

    if (typeof stored === "number" && Number.isFinite(stored) === true && stored >= 0) {
      this._legacySize = stored
    } else if (stored !== null && typeof stored === "object") {
      const ratio = Number(stored.ratio)
      if (Number.isFinite(ratio) === true && ratio >= 0 && ratio <= 1) {
        this._ratio = ratio
        this._legacySize = null
        this._collapsedPane = stored.collapsed === "start" || stored.collapsed === "end" ? stored.collapsed : null
      }
    }
    return
  }

  /* ----- public API ----- */

  /* Current size of the start pane in pixels. */
  get size() {
    return this._currentSize
  }

  set size(value) {
    const changed = this._setSize(Number(value))
    if (changed === true) {
      this._settle()
    }
    return
  }

  /* Current size of the start pane as a fraction (0-1) of the container. */
  get ratio() {
    const total = this._totalSize()
    let ratio = 0.5

    if (total > 0) {
      ratio = this._currentSize / total
    } else if (this._ratio !== null) {
      ratio = this._ratio
    }

    return ratio
  }

  /* "start" or "end" while that pane is collapsed, otherwise null. */
  get collapsed() {
    return this._collapsedPane
  }
}
