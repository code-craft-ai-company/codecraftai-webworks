/*
 * mjtoastregion.js
 *
 * <mj-toast-region> -- singleton placement and queuing manager for transient
 * notification toasts. Controls the fixed-position region, enforces the
 * max-visible limit, manages auto-dismiss with hover/focus pause, and
 * sequences queued toasts.
 *
 *   const id = region.add({ message, title, severity, duration, actions })
 *   region.update(id, { message: "Still working..." })
 *   region.dismiss(id)
 *   region.dismissAll()
 *
 * `message` and `title` are always rendered as text. `severity` is "info"
 * (default), "success", "warning" or "error". `duration` is milliseconds;
 * 0 keeps the toast until it is dismissed. An action is
 * { label, id, onClick, dismiss } and renders a button in the toast.
 *
 * All state lives in fields, so the visible toasts are rebuilt when the
 * element is rendered again after a move in the document. While a modal
 * surface is open the region's list is shown inside that surface (the rest
 * of the page is inert there), and it always sits in the top layer so a
 * dialog cannot cover it.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";
import { t } from "../core/intl.js";
import {
  showInTopLayer, removeFromTopLayer, topModalSurface, onLayerChange
} from "../core/overlay.js";

/* Fallback removal delay when the dismiss animation never reports its end. */
const REMOVE_FALLBACK_MS = 400;

const SEVERITIES = ["info", "success", "warning", "error"];

const PLACEMENTS = [
  "bottom-end", "bottom-start", "bottom-center", "top-end", "top-start", "top-center"
];

/* Custom properties a page may set on the host; carried along when the
   region is shown inside a modal surface, where they no longer inherit. */
const INHERITED_PROPERTIES = [
  "--mj-toast-region-gap", "--mj-toast-region-offset-x",
  "--mj-toast-region-offset-y", "--mj-toast-max-width"
];

/*
 * Styles of the region and its toasts. They select on the region element
 * only (never on :host), so the same sheet works when the region is moved
 * into another component's shadow root.
 */
const REGION_STYLES = `
.region {
  position: fixed;
  box-sizing: border-box;
  margin: 0;
  padding: 0;
  border: 0 none;
  background: transparent;
  overflow: visible;
  z-index: var(--mj-layer-toast);
  pointer-events: none;
  max-width: var(--mj-toast-max-width, 24rem);
  inset-block-end: var(--mj-toast-region-offset-y, var(--mj-toast-region-attribute-offset-y, var(--mj-space-4)));
  inset-inline-end: var(--mj-toast-region-offset-x, var(--mj-toast-region-attribute-offset-x, var(--mj-space-4)));
}

.region[data-placement="bottom-start"] {
  inset-inline-end: auto;
  inset-inline-start: var(--mj-toast-region-offset-x, var(--mj-toast-region-attribute-offset-x, var(--mj-space-4)));
}

.region[data-placement="bottom-center"] {
  inset-inline: 0;
  margin-inline: auto;
  width: fit-content;
}

.region[data-placement="top-end"] {
  inset-block-end: auto;
  inset-block-start: var(--mj-toast-region-offset-y, var(--mj-toast-region-attribute-offset-y, var(--mj-space-4)));
}

.region[data-placement="top-start"] {
  inset-block-end: auto;
  inset-block-start: var(--mj-toast-region-offset-y, var(--mj-toast-region-attribute-offset-y, var(--mj-space-4)));
  inset-inline-end: auto;
  inset-inline-start: var(--mj-toast-region-offset-x, var(--mj-toast-region-attribute-offset-x, var(--mj-space-4)));
}

.region[data-placement="top-center"] {
  inset-block-end: auto;
  inset-block-start: var(--mj-toast-region-offset-y, var(--mj-toast-region-attribute-offset-y, var(--mj-space-4)));
  inset-inline: 0;
  margin-inline: auto;
  width: fit-content;
}

.region .toast-list {
  display: flex;
  flex-direction: column;
  gap: var(--mj-toast-region-gap, var(--mj-toast-region-attribute-gap, var(--mj-space-3)));
  list-style: none;
  margin: 0;
  padding: 0;
}

/* Bottom placements grow upwards: the newest toast is nearest the edge. */
.region[data-placement^="bottom"] .toast-list {
  flex-direction: column-reverse;
}

.region .toast-item {
  pointer-events: auto;
  display: flex;
  align-items: flex-start;
  gap: var(--mj-space-3);
  padding: var(--mj-space-3) var(--mj-space-4);
  background: var(--mj-surface-raised, var(--mj-surface));
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-md);
  box-shadow: var(--mj-elevation-2);
  color: var(--mj-text);
  font-size: var(--mj-font-size-sm);
  animation: mj-toast-in var(--mj-motion-medium) var(--mj-motion-ease) both;
}

.region .toast-item[data-dismissing] {
  animation: mj-toast-out var(--mj-motion-medium) var(--mj-motion-ease) both;
}

@keyframes mj-toast-in {
  from { opacity: 0; transform: translateY(0.5rem); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes mj-toast-out {
  from { opacity: 1; transform: translateY(0); }
  to   { opacity: 0; transform: translateY(0.5rem); }
}

.region .toast-severity {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: var(--mj-radius-circle);
  flex-shrink: 0;
  margin-block-start: 0.35rem;
}

.region .toast-item[data-severity="error"] .toast-severity   { background: var(--mj-color-danger); }
.region .toast-item[data-severity="warning"] .toast-severity { background: var(--mj-color-warning); }
.region .toast-item[data-severity="success"] .toast-severity { background: var(--mj-color-success); }
.region .toast-item[data-severity="info"] .toast-severity    { background: var(--mj-color-info); }

.region .toast-body { flex: 1; min-width: 0; }
.region .toast-title { margin: 0; font-weight: var(--mj-font-weight-bold); }
.region .toast-title[hidden] { display: none; }
.region .toast-message { margin: 0; overflow-wrap: anywhere; }

.region .toast-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--mj-space-2);
  margin-block-start: var(--mj-space-2);
}

.region .toast-actions:empty { display: none; }

.region .toast-action {
  padding: var(--mj-space-1) var(--mj-space-2);
  font: inherit;
  font-size: var(--mj-font-size-xs);
  font-weight: var(--mj-font-weight-medium);
  background: transparent;
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-md);
  color: var(--mj-text);
  cursor: pointer;
}

.region .toast-action:hover { background: var(--mj-bg-muted); }

.region .toast-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: var(--mj-radius-md);
  cursor: pointer;
  color: var(--mj-text-muted);
  flex-shrink: 0;
  font-size: 0.75rem;
}

.region .toast-close:hover { background: var(--mj-bg-muted); color: var(--mj-text); }
.region .toast-close:focus-visible,
.region .toast-action:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

@media (prefers-reduced-motion: reduce) {
  .region .toast-item, .region .toast-item[data-dismissing] { animation: none; }
}
`;

const STYLES = `
:host {
  display: contents;
}
${REGION_STYLES}
`;

/* REGION_STYLES as a sheet a modal surface's root can adopt. */
let portableSheet = null;

function adoptRegionStyles(root) {
  if (portableSheet === null) {
    portableSheet = new CSSStyleSheet()
    portableSheet.replaceSync(REGION_STYLES)
  }

  const canAdopt = root !== null && root !== undefined && Array.isArray(root.adoptedStyleSheets) === true
  if (canAdopt === true && root.adoptedStyleSheets.includes(portableSheet) === false) {
    root.adoptedStyleSheets = [...root.adoptedStyleSheets, portableSheet]
  }
  return
}

export class MjToastRegion extends MjElement {
  static tagName = "mj-toast-region";
  static styles = STYLES;
  static watched = [
    "placement", "max-visible", "region-label", "dismiss-label", "gap", "offset-x", "offset-y"
  ];

  constructor() {
    super()

    /* Descriptors waiting for a free slot, oldest first. */
    this._queue = []

    /* Descriptors currently shown, oldest first. */
    this._visible = []

    /* toast id -> { timerId, end, remaining } for toasts that auto-dismiss. */
    this._timers = new Map()

    /* toast id -> its <li> element. */
    this._elements = new Map()

    this._regionEl = null
    this._listEl = null

    /* Auto-dismiss is paused while the pointer or keyboard focus is inside. */
    this._hovered = false
    this._focusWithin = false
    this._paused = false
  }

  render() {
    const markup = `
      <div class="region" part="region" role="region">
        <ol class="toast-list" role="list"></ol>
      </div>
    `
    return markup
  }

  afterRender() {
    this._regionEl = this.$(".region")
    this._listEl = this.$(".toast-list")
    this._hovered = false
    this._focusWithin = false
    this._paused = false

    this.listen(this._regionEl, "pointerenter", this._onPointerEnter.bind(this))
    this.listen(this._regionEl, "pointerleave", this._onPointerLeave.bind(this))
    this.listen(this._regionEl, "focusin", this._onFocusIn.bind(this))
    this.listen(this._regionEl, "focusout", this._onFocusOut.bind(this))
    this.listen(this._regionEl, "keydown", this._onKeydown.bind(this))
    this.listen(this._regionEl, "click", this._onClick.bind(this))
    this.listen(this, "mj-toast-request", this._onToastRequest.bind(this))

    /* Follow modal surfaces opening and closing. */
    const unsubscribe = onLayerChange(this._placeRegion.bind(this))
    this.onTeardown(unsubscribe)
    this.onTeardown(this._onTeardown.bind(this))

    this._applyLabels()
    this._applyPlacement()
    this._applySpacing()

    /*
     * Rebuild from state: toasts that were visible before a re-render come
     * back (with the time they had left), and toasts added before the first
     * render are shown now.
     */
    this._elements.clear()
    for (let index = 0; index < this._visible.length; index = index + 1) {
      const descriptor = this._visible[index]
      const element = this._buildToast(descriptor)
      this._elements.set(descriptor.id, element)
      this._listEl.appendChild(element)
    }
    this._resumeTimers()
    this._promoteQueued()
    this._placeRegion()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._regionEl === undefined || this._regionEl === null) {
      return
    }

    if (name === "placement") {
      this._applyPlacement()
    } else if (name === "max-visible") {
      this._promoteQueued()
    } else if (name === "region-label" || name === "dismiss-label") {
      this._applyLabels()
    } else if (name === "gap" || name === "offset-x" || name === "offset-y") {
      this._applySpacing()
    }
    return
  }

  /*
   * Runs when the element really leaves the document. Countdowns stop (the
   * time left is kept) and the list comes home from the top layer or from a
   * modal surface, so nothing is left behind.
   */
  _onTeardown() {
    this._pauseTimers()

    if (this._regionEl !== null) {
      removeFromTopLayer(this._regionEl)
      if (this._regionEl.parentNode !== this.shadowRoot) {
        this.shadowRoot.appendChild(this._regionEl)
      }
    }
    return
  }

  /* ----- attribute-driven rendering ----- */

  _applyLabels() {
    this._regionEl.setAttribute("aria-label", this.getAttribute("region-label") || t("mj.toastRegion.label"))

    const dismissLabel = this._dismissLabel()
    const closeButtons = this._regionEl.querySelectorAll(".toast-close")
    for (let index = 0; index < closeButtons.length; index = index + 1) {
      closeButtons[index].setAttribute("aria-label", dismissLabel)
    }
    return
  }

  _dismissLabel() {
    const label = this.getAttribute("dismiss-label") || t("mj.toastRegion.dismiss")
    return label
  }

  _applyPlacement() {
    const requested = this.getAttribute("placement") || ""
    const placement = PLACEMENTS.indexOf(requested) >= 0 ? requested : "bottom-end"
    this._regionEl.setAttribute("data-placement", placement)
    return
  }

  /* `gap`, `offset-x` and `offset-y` are defaults a custom property overrides. */
  _applySpacing() {
    const names = ["gap", "offset-x", "offset-y"]
    for (let index = 0; index < names.length; index = index + 1) {
      const name = names[index]
      const value = this.getAttribute(name)
      const property = `--mj-toast-region-attribute-${name}`
      const valid = value !== null && value.trim().length > 0 && CSS.supports("margin-top", value) === true
      if (valid === true) {
        this._regionEl.style.setProperty(property, value)
      } else {
        this._regionEl.style.removeProperty(property)
      }
    }
    return
  }

  /*
   * Put the region where it can be seen and used. With toasts showing it is
   * in the top layer (raised above anything shown before); while a modal
   * surface is open it is moved inside that surface, because everything
   * outside a modal is inert. Empty, it rests in its own shadow root.
   */
  _placeRegion() {
    if (this._regionEl === null) {
      return
    }

    const hasToasts = this._elements.size > 0
    const surface = hasToasts === true ? topModalSurface() : null
    const home = surface !== null ? surface : this.shadowRoot

    if (this._regionEl.parentNode !== home) {
      removeFromTopLayer(this._regionEl)

      if (surface !== null) {
        adoptRegionStyles(surface.getRootNode())
        const hostStyle = window.getComputedStyle(this)
        for (let index = 0; index < INHERITED_PROPERTIES.length; index = index + 1) {
          const property = INHERITED_PROPERTIES[index]
          const value = hostStyle.getPropertyValue(property).trim()
          if (value.length > 0) {
            this._regionEl.style.setProperty(property, value)
          }
        }
      } else {
        for (let index = 0; index < INHERITED_PROPERTIES.length; index = index + 1) {
          this._regionEl.style.removeProperty(INHERITED_PROPERTIES[index])
        }
      }

      home.appendChild(this._regionEl)
    }

    if (hasToasts === true) {
      showInTopLayer(this._regionEl)
    } else {
      removeFromTopLayer(this._regionEl)
    }
    return
  }

  /* ----- pause on hover / focus ----- */

  _onPointerEnter() {
    this._hovered = true
    this._syncPause()
    return
  }

  _onPointerLeave() {
    this._hovered = false
    this._syncPause()
    return
  }

  _onFocusIn() {
    this._focusWithin = true
    this._syncPause()
    return
  }

  _onFocusOut(event) {
    const next = event.relatedTarget
    this._focusWithin = next !== null && this._regionEl.contains(next) === true
    this._syncPause()
    return
  }

  /* Countdowns run only while neither the pointer nor focus is inside. */
  _syncPause() {
    const shouldPause = this._hovered === true || this._focusWithin === true
    if (shouldPause === this._paused) {
      return
    }

    this._paused = shouldPause
    if (shouldPause === true) {
      this._pauseTimers()
    } else {
      this._resumeTimers()
    }
    return
  }

  _pauseTimers() {
    for (const timerInfo of this._timers.values()) {
      if (timerInfo.timerId !== null) {
        window.clearTimeout(timerInfo.timerId)
        timerInfo.remaining = Math.max(0, timerInfo.end - Date.now())
        timerInfo.timerId = null
      }
    }
    return
  }

  _resumeTimers() {
    if (this._paused === true || this._regionEl === null) {
      return
    }

    for (const [id, timerInfo] of this._timers.entries()) {
      if (timerInfo.timerId === null) {
        timerInfo.end = Date.now() + timerInfo.remaining
        timerInfo.timerId = window.setTimeout(() => {
          this._dismiss(id, "auto")
        }, timerInfo.remaining)
      }
    }
    return
  }

  /* Start (or restart) the countdown of a visible toast. */
  _startTimer(descriptor) {
    const existing = this._timers.get(descriptor.id)
    if (existing !== undefined && existing.timerId !== null) {
      window.clearTimeout(existing.timerId)
    }
    this._timers.delete(descriptor.id)

    const duration = this._durationOf(descriptor)
    if (duration <= 0) {
      return
    }

    /* Created idle; `_resumeTimers` starts it unless the region is paused. */
    this._timers.set(descriptor.id, { timerId: null, end: 0, remaining: duration })
    this._resumeTimers()
    return
  }

  _durationOf(descriptor) {
    let duration = descriptor.severity === "error" ? 8000 : 5000
    const requested = Number(descriptor.duration)
    if (descriptor.duration !== undefined && descriptor.duration !== null && Number.isFinite(requested) === true) {
      duration = Math.max(0, requested)
    }
    return duration
  }

  /* ----- events ----- */

  _onKeydown(event) {
    if (event.key !== "Escape") {
      return
    }

    const item = event.target.closest(".toast-item")
    if (item !== null) {
      /* Handled here: a dialog hosting the region must not close as well. */
      event.preventDefault()
      event.stopPropagation()
      this._dismiss(item.getAttribute("data-toast-id"), "user")
    }
    return
  }

  _onClick(event) {
    const item = event.target.closest(".toast-item")
    if (item === null) {
      return
    }
    const toastId = item.getAttribute("data-toast-id")

    if (event.target.closest(".toast-close") !== null) {
      this._dismiss(toastId, "user")
      return
    }

    const actionButton = event.target.closest(".toast-action")
    if (actionButton !== null) {
      const descriptor = this._visible.find((entry) => entry.id === toastId)
      const actions = descriptor !== undefined && Array.isArray(descriptor.actions) ? descriptor.actions : []
      const action = actions[parseInt(actionButton.getAttribute("data-action-index") || "-1", 10)]
      if (action === undefined) {
        return
      }

      this.emit("mj-toast-action", { id: toastId, action: action })
      if (typeof action.onClick === "function") {
        action.onClick(action)
      }
      if (action.dismiss !== false) {
        this._dismiss(toastId, "user")
      }
    }
    return
  }

  _onToastRequest(event) {
    /* `mj-toast-request` with a descriptor in `detail` is the event form of add(). */
    if (event.detail !== null && typeof event.detail === "object") {
      this.add(event.detail)
    }
    return
  }

  /* ----- toasts ----- */

  _maxVisible() {
    const parsed = parseInt(this.getAttribute("max-visible") || "", 10)
    const max = Number.isFinite(parsed) === true && parsed > 0 ? parsed : 3
    return max
  }

  /* Copy a caller's descriptor into the shape the region works with. */
  _normalize(descriptor) {
    const source = descriptor !== null && typeof descriptor === "object" ? descriptor : {}
    const hasId = source.id !== undefined && source.id !== null && String(source.id).length > 0
    const item = Object.assign({}, source, {
      id: hasId === true ? String(source.id) : nextId("mj-toast"),
      severity: SEVERITIES.indexOf(source.severity) >= 0 ? source.severity : "info"
    })
    return item
  }

  add(descriptor) {
    const item = this._normalize(descriptor)
    const id = item.id

    this.emit("mj-toast-add", { id: id, descriptor: item })

    /* Before the first render there is no list yet: the toast waits. */
    const canShow = this._regionEl !== null && this._visible.length < this._maxVisible()
    if (canShow === true) {
      this._show(item)
    } else {
      this._queue.push(item)
    }
    return id
  }

  /*
   * Build the <li> for a toast. Everything that comes from the descriptor
   * is written with textContent / setAttribute: a message is text, never
   * markup.
   */
  _buildToast(descriptor) {
    const li = document.createElement("li")
    li.className = "toast-item"
    li.setAttribute("part", "toast")
    li.setAttribute("data-toast-id", descriptor.id)
    li.setAttribute("data-severity", descriptor.severity)

    const dot = document.createElement("span")
    dot.className = "toast-severity"
    dot.setAttribute("aria-hidden", "true")
    li.appendChild(dot)

    const body = document.createElement("div")
    body.className = "toast-body"

    const title = document.createElement("p")
    title.className = "toast-title"
    body.appendChild(title)

    const message = document.createElement("p")
    message.className = "toast-message"
    body.appendChild(message)

    const actions = document.createElement("div")
    actions.className = "toast-actions"
    body.appendChild(actions)

    li.appendChild(body)

    const closeBtn = document.createElement("button")
    closeBtn.className = "toast-close"
    closeBtn.setAttribute("type", "button")
    closeBtn.setAttribute("part", "toast-close")
    closeBtn.setAttribute("aria-label", this._dismissLabel())
    closeBtn.textContent = "✕"
    li.appendChild(closeBtn)

    this._fillToast(li, descriptor)
    return li
  }

  /* Write the descriptor's text, severity and actions into a toast element. */
  _fillToast(li, descriptor) {
    li.setAttribute("data-severity", descriptor.severity)

    const title = li.querySelector(".toast-title")
    const hasTitle = descriptor.title !== undefined && descriptor.title !== null && String(descriptor.title).length > 0
    title.textContent = hasTitle === true ? String(descriptor.title) : ""
    title.hidden = hasTitle === false

    const message = li.querySelector(".toast-message")
    const hasMessage = descriptor.message !== undefined && descriptor.message !== null
    message.textContent = hasMessage === true ? String(descriptor.message) : ""

    const actions = li.querySelector(".toast-actions")
    actions.textContent = ""
    const actionList = Array.isArray(descriptor.actions) ? descriptor.actions : []
    for (let index = 0; index < actionList.length; index = index + 1) {
      const action = actionList[index]
      if (action === null || typeof action !== "object") {
        continue
      }
      const button = document.createElement("button")
      button.className = "toast-action"
      button.setAttribute("type", "button")
      button.setAttribute("part", "toast-action")
      button.setAttribute("data-action-index", String(index))
      button.textContent = action.label !== undefined && action.label !== null ? String(action.label) : ""
      actions.appendChild(button)
    }
    return
  }

  /* What a screen reader hears when the toast appears. */
  _announce(descriptor) {
    const parts = []
    if (descriptor.title !== undefined && descriptor.title !== null && String(descriptor.title).length > 0) {
      parts.push(String(descriptor.title))
    }
    if (descriptor.message !== undefined && descriptor.message !== null && String(descriptor.message).length > 0) {
      parts.push(String(descriptor.message))
    }

    /*
     * Errors and warnings interrupt; the rest waits its turn. The dedicated
     * polite and assertive live regions of the announcer are used because a
     * region whose politeness is switched on the fly is not reliably read.
     */
    const urgent = descriptor.severity === "error" || descriptor.severity === "warning"
    const forcePolite = this.hasAttribute("polite") === true && this.getAttribute("polite") !== "false"
    const politeness = urgent === true && forcePolite === false ? "assertive" : "polite"

    announce(parts.join(": "), politeness)
    return
  }

  _show(descriptor) {
    const li = this._buildToast(descriptor)
    this._elements.set(descriptor.id, li)
    this._visible.push(descriptor)
    this._listEl.appendChild(li)

    this._placeRegion()
    this._startTimer(descriptor)
    this._announce(descriptor)

    this.emit("mj-toast-show", { id: descriptor.id })
    return
  }

  /* Show waiting toasts while there is room for them. */
  _promoteQueued() {
    if (this._regionEl === null) {
      return
    }
    while (this._queue.length > 0 && this._visible.length < this._maxVisible()) {
      const next = this._queue.shift()
      this._show(next)
    }
    return
  }

  /* Play the exit animation of a toast element, then remove it. */
  _removeElement(li) {
    let removed = false
    const remove = () => {
      if (removed === true) {
        return
      }
      removed = true
      li.remove()

      /* Removing the focused button fires no focusout: recompute. */
      if (this._regionEl !== null) {
        this._focusWithin = this._regionEl.matches(":focus-within")
        this._syncPause()
      }
      this._placeRegion()
    }

    li.setAttribute("data-dismissing", "")
    li.addEventListener("animationend", remove, { once: true })
    window.setTimeout(remove, REMOVE_FALLBACK_MS)
    return
  }

  _dismiss(toastId, reason) {
    const id = String(toastId)

    /* A toast still waiting in the queue is simply dropped. */
    const queuedIndex = this._queue.findIndex((entry) => entry.id === id)
    if (queuedIndex >= 0) {
      this._queue.splice(queuedIndex, 1)
      this.emit("mj-toast-dismiss", { id: id, reason: reason })
      this._emitIfEmpty()
      return true
    }

    const visibleIndex = this._visible.findIndex((entry) => entry.id === id)
    if (visibleIndex < 0) {
      return false
    }

    const timerInfo = this._timers.get(id)
    if (timerInfo !== undefined) {
      if (timerInfo.timerId !== null) {
        window.clearTimeout(timerInfo.timerId)
      }
      this._timers.delete(id)
    }

    this._visible.splice(visibleIndex, 1)

    const li = this._elements.get(id)
    this._elements.delete(id)
    if (li !== undefined) {
      this._removeElement(li)
    }

    this.emit("mj-toast-dismiss", { id: id, reason: reason })

    this._promoteQueued()
    this._emitIfEmpty()
    return true
  }

  _emitIfEmpty() {
    if (this._visible.length === 0 && this._queue.length === 0) {
      this.emit("mj-toast-queue-empty", {})
    }
    return
  }

  /* Scriptable API */

  /*
   * Dismiss one toast, visible or still queued. Returns false when no toast
   * has that id.
   */
  dismiss(id) {
    const dismissed = this._dismiss(id, "api")
    return dismissed
  }

  /*
   * Change a toast in place: any of message, title, severity, actions and
   * duration. A new duration restarts the countdown. Returns false when no
   * toast has that id.
   */
  update(id, changes) {
    const key = String(id)
    const patch = changes !== null && typeof changes === "object" ? changes : {}

    const queued = this._queue.find((entry) => entry.id === key)
    const visible = this._visible.find((entry) => entry.id === key)
    const descriptor = visible !== undefined ? visible : queued
    if (descriptor === undefined) {
      return false
    }

    Object.assign(descriptor, patch, { id: key })
    if (SEVERITIES.indexOf(descriptor.severity) < 0) {
      descriptor.severity = "info"
    }

    if (visible !== undefined) {
      const li = this._elements.get(key)
      if (li !== undefined) {
        this._fillToast(li, descriptor)
      }
      if (patch.duration !== undefined) {
        this._startTimer(descriptor)
      }
    }
    return true
  }

  dismissAll() {
    /* Queue first: dismissing a visible toast would otherwise promote one. */
    const queuedIds = this._queue.map((entry) => entry.id)
    this._queue = []
    for (let index = 0; index < queuedIds.length; index = index + 1) {
      this.emit("mj-toast-dismiss", { id: queuedIds[index], reason: "api" })
    }

    const ids = this._visible.map((entry) => entry.id)
    for (let index = 0; index < ids.length; index = index + 1) {
      this._dismiss(ids[index], "api")
    }

    if (ids.length === 0 && queuedIds.length > 0) {
      this._emitIfEmpty()
    }
    return
  }

  /* Read-only properties */

  get queue() {
    return this._queue.slice()
  }

  get visible() {
    return this._visible.slice()
  }

  get count() {
    return this._visible.length + this._queue.length
  }
}
