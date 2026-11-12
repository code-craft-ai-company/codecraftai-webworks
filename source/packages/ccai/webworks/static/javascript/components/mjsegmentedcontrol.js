/*
 * mjsegmentedcontrol.js
 *
 * <mj-segmented-control> — compact connected row of segments acting as
 * radio-select, independent toggles, or an action toolbar.
 *
 * Segments are the <mj-segment> descendants of the host. Each one is
 * rendered as a <button> whose content is a copy of the segment's own nodes
 * (so icons and badges are kept) and whose `aria-label` / `title` are
 * forwarded. A MutationObserver keeps the buttons in step with the
 * <mj-segment> elements.
 *
 * Modes:
 *   select  role="radiogroup"; one roving tab stop; the arrow keys of both
 *           axes, Home and End move focus and select the segment they land on.
 *   toggle  role="group" of aria-pressed buttons; each one is a tab stop.
 *   action  role="toolbar"; one roving tab stop moved by the arrow keys;
 *           activating a segment fires `mj-action`.
 *
 * In select and toggle modes the control is form-associated: it submits its
 * value under `name`, supports `required` and restores the `value` attribute
 * (the default) on form reset. A user selection never rewrites the attribute.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";

const STYLES = `
:host { display: inline-block; vertical-align: middle; }
:host([stretch]) { display: block; }

.container {
  display: inline-flex;
  background: var(--mj-bg-muted);
  border-radius: var(--mj-segmented-border-radius, var(--mj-radius-md));
  padding: 2px;
  gap: var(--mj-segmented-gap, 2px);
  position: relative;
  min-height: var(--mj-segmented-height, var(--mj-control-height-md));
}
:host([stretch]) .container { display: flex; width: 100%; }

.segment {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--mj-space-1);
  padding: 0 var(--mj-space-3);
  font: inherit;
  font-size: var(--mj-font-size-sm);
  font-weight: var(--mj-font-weight-medium);
  color: var(--mj-text-muted);
  background: transparent;
  border: none;
  border-radius: var(--mj-segmented-segment-radius, var(--mj-radius-sm));
  cursor: pointer;
  position: relative;
  z-index: 1;
  transition: color var(--mj-motion-fast);
  white-space: nowrap;
  user-select: none;
}
:host([stretch]) .segment { flex: 1; }
.segment:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.segment:hover:not([disabled]):not([aria-disabled="true"]) { color: var(--mj-text); }
.segment[aria-checked="true"],
.segment[aria-pressed="true"] {
  color: var(--mj-text);
  background: var(--mj-surface);
  box-shadow: var(--mj-elevation-1);
}
.segment[disabled],
.segment[aria-disabled="true"] { opacity: 0.45; cursor: not-allowed; }

.segment-label { display: inline-flex; align-items: center; gap: var(--mj-space-1); }

:host([size="sm"]) .segment { font-size: var(--mj-font-size-xs); padding: 0 var(--mj-space-2); }
:host([size="lg"]) .segment { font-size: var(--mj-font-size-md); padding: 0 var(--mj-space-4); }

:host([disabled]) .segment { opacity: 0.45; pointer-events: none; }
`;

/* <mj-segment> attributes whose changes alter what a button shows. */
const SEGMENT_ATTRIBUTES = ["value", "disabled", "aria-label", "label", "title"]

export class MjSegmentedControl extends FormControlMixin(MjElement) {
  static tagName = "mj-segmented-control";
  static styles = STYLES;
  static watched = [
    "mode", "value", "disabled", "required", "stretch", "size", "label", "aria-label"
  ];

  constructor() {
    super()
    this._initFormControl()

    /*
     * The selected values in the order they were chosen. Select mode uses
     * only the first one; keeping the whole list means `value` and `mode`
     * may be assigned in either order.
     */
    this._selectedValues = new Set()
    this._segmentData = []

    /* Action mode: the segment that holds the toolbar's tab stop. */
    this._toolbarStop = -1

    /* True while an ancestor <fieldset disabled> disables the control. */
    this._formDisabled = false

    /* The `value` attribute change applied before the first render, if any. */
    this._preRenderValue = null

    this._containerId = nextId("mj-sc")
  }

  render() {
    const markup = `
      <div
        class="container"
        part="container"
        id="${this._containerId}"
      ></div>
    `
    return markup
  }

  afterRender() {
    this._container = this.$(".container")

    /* One delegated pair of listeners serves every segment button. */
    this.listen(this._container, "click", this._onSegmentClick.bind(this))
    this.listen(this._container, "keydown", this._onKeydown.bind(this))
    this.listen(this._container, "focusin", this._onFocusIn.bind(this))

    this._observeSegments()
    this._syncContainer()
    this._buildSegments()
    this._syncFormValue()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "value" && this._isReplayedValue(newValue) === false) {
      this._applyValueString(newValue || "")
    }
    if (name === "mode") {
      this._syncContainer()
      this._syncSegmentStates()
      this._syncFormValue()
    }
    if (name === "disabled") {
      this._syncContainer()
      this._syncSegmentStates()
    }
    if (name === "label" || name === "aria-label") {
      this._syncContainer()
    }
    if (name === "required" && this._internals !== undefined) {
      this._syncContainer()
      this._refreshValidity()
    }
    return
  }

  /*
   * The base class delivers an attribute change that arrived before the first
   * render a second time once the shadow DOM exists. For `value` the first
   * delivery already stored the selection, and applying it again would
   * discard a `value` property assigned in between. Returns true for that
   * repeat.
   */
  _isReplayedValue(newValue) {
    let replayed = false

    if (this._rendered === false) {
      this._preRenderValue = { value: newValue }
    } else if (this._preRenderValue !== null) {
      replayed = this._preRenderValue.value === newValue
      this._preRenderValue = null
    }

    return replayed
  }

  /* Disabled by its own attribute or by an ancestor <fieldset disabled>. */
  _isDisabled() {
    const disabled = this.hasAttribute("disabled") === true || this._formDisabled === true
    return disabled
  }

  /* "select" (default), "toggle" or "action". */
  _mode() {
    const attr = this.getAttribute("mode")
    const mode = attr === "toggle" || attr === "action" ? attr : "select"
    return mode
  }

  /* ----- segments ----- */

  _getSegmentEls() {
    return Array.from(this.querySelectorAll("mj-segment"))
  }

  /*
   * Rebuild the buttons whenever the <mj-segment> children change. Mutation
   * records are delivered once per microtask checkpoint, so adding several
   * segments in a loop causes a single rebuild.
   */
  _observeSegments() {
    if (typeof MutationObserver !== "function") {
      return
    }
    const observer = new MutationObserver((records) => {
      const relevant = records.some((record) => {
        return record.type !== "attributes" || record.target !== this
      })
      if (relevant === true && this._container !== undefined && this._container !== null) {
        this._buildSegments()
      }
    })
    observer.observe(this, {
      childList: true,
      subtree: true,
      characterData: true,
      attributes: true,
      attributeFilter: SEGMENT_ATTRIBUTES
    })
    this.onTeardown(() => {
      observer.disconnect()
    })
    return
  }

  /*
   * Build one <button> per <mj-segment>. The content is a copy of the
   * segment's own nodes (cloneNode), never markup assembled from strings, so
   * icons and badges are kept and nothing is re-parsed as HTML.
   */
  _buildSegments() {
    /* A rebuild replaces the buttons; remember which segment had focus. */
    const active = this.shadowRoot.activeElement
    const activeItem = active !== null ? this._segmentData[parseInt(active.dataset.index, 10)] : undefined
    const focusedEl = activeItem !== undefined ? activeItem.el : null

    const els = this._getSegmentEls()
    this._container.replaceChildren()

    this._segmentData = els.map((el, index) => {
      const node = document.createElement("button")
      node.type = "button"
      node.className = "segment"
      node.setAttribute("part", "segment")
      node.id = nextId("mj-seg")
      node.dataset.index = String(index)

      const labelEl = document.createElement("span")
      labelEl.className = "segment-label"
      labelEl.setAttribute("part", "segment-label")
      Array.from(el.childNodes).forEach((child) => {
        labelEl.appendChild(child.cloneNode(true))
      })
      node.appendChild(labelEl)

      /* An icon-only segment is named by its aria-label (or label). */
      const ariaLabel = el.getAttribute("aria-label") || el.getAttribute("label") || ""
      if (ariaLabel.length > 0) {
        node.setAttribute("aria-label", ariaLabel)
      }
      const title = el.getAttribute("title") || ""
      if (title.length > 0) {
        node.title = title
      }

      const item = {
        id: node.id,
        value: el.hasAttribute("value") === true ? el.getAttribute("value") : String(index),
        label: labelEl.textContent.replace(/\s+/g, " ").trim(),
        disabled: el.hasAttribute("disabled"),
        index: index,
        el: el,
        node: node
      }
      this._container.appendChild(node)
      return item
    })

    this._syncSegmentStates()

    const refocus = this._segmentData.find((item) => item.el === focusedEl)
    if (focusedEl !== null && refocus !== undefined && refocus.node.disabled === false) {
      refocus.node.focus()
    }
    return
  }

  /* Select mode: index of the selected segment, or -1. */
  _selectedIndex() {
    let index = -1
    const values = Array.from(this._selectedValues)
    if (values.length > 0) {
      index = this._segmentData.findIndex((item) => item.value === values[0])
    }
    return index
  }

  _isSelected(item, mode) {
    let selected = false
    if (mode === "select") {
      selected = item.index === this._selectedIndex()
    } else if (mode === "toggle") {
      selected = this._selectedValues.has(item.value)
    }
    return selected
  }

  _firstEnabledIndex() {
    const index = this._segmentData.findIndex((item) => item.node.disabled === false)
    return index
  }

  /*
   * Bring every button in line with the fields and the mode: role, checked
   * or pressed state, disabled state (the segment's own flag OR the
   * control's) and tab order.
   */
  _syncSegmentStates() {
    if (this._container === undefined || this._container === null) {
      return
    }

    const mode = this._mode()
    const groupDisabled = this._isDisabled()

    this._segmentData.forEach((item) => {
      const node = item.node
      node.disabled = item.disabled === true || groupDisabled === true

      const selected = this._isSelected(item, mode)
      if (mode === "select") {
        node.setAttribute("role", "radio")
        node.setAttribute("aria-checked", selected === true ? "true" : "false")
        node.removeAttribute("aria-pressed")
      } else if (mode === "toggle") {
        node.removeAttribute("role")
        node.removeAttribute("aria-checked")
        node.setAttribute("aria-pressed", selected === true ? "true" : "false")
      } else {
        node.removeAttribute("role")
        node.removeAttribute("aria-checked")
        node.removeAttribute("aria-pressed")
      }
    })

    /* Select and action modes have one roving tab stop. */
    let stop = -1
    if (mode === "select") {
      const selectedIndex = this._selectedIndex()
      const usable = selectedIndex >= 0 && this._segmentData[selectedIndex].node.disabled === false
      stop = usable === true ? selectedIndex : this._firstEnabledIndex()
    } else if (mode === "action") {
      const kept = this._segmentData[this._toolbarStop]
      const usable = kept !== undefined && kept.node.disabled === false
      stop = usable === true ? this._toolbarStop : this._firstEnabledIndex()
    }

    this._segmentData.forEach((item) => {
      if (mode === "toggle") {
        item.node.tabIndex = 0
      } else {
        item.node.tabIndex = item.index === stop ? 0 : -1
      }
    })
    return
  }

  /* Role, name and state of the container for the current mode. */
  _syncContainer() {
    if (this._container === undefined || this._container === null) {
      return
    }

    const mode = this._mode()
    let role = "radiogroup"
    if (mode === "toggle") {
      role = "group"
    } else if (mode === "action") {
      role = "toolbar"
    }
    this._container.setAttribute("role", role)

    const name = this.getAttribute("label") || this.getAttribute("aria-label") || ""
    if (name.length > 0) {
      this._container.setAttribute("aria-label", name)
    } else {
      this._container.removeAttribute("aria-label")
    }

    if (this._isDisabled() === true) {
      this._container.setAttribute("aria-disabled", "true")
    } else {
      this._container.removeAttribute("aria-disabled")
    }

    if (mode === "select" && this.hasAttribute("required") === true) {
      this._container.setAttribute("aria-required", "true")
    } else {
      this._container.removeAttribute("aria-required")
    }
    return
  }

  /*
   * Replace the selection with the comma-separated list in `text`. Emits
   * nothing -- used for the `value` attribute and property, form reset and
   * restore.
   */
  _applyValueString(text) {
    const source = text === null || text === undefined ? "" : String(text)
    this._selectedValues.clear()
    source.split(",").forEach((part) => {
      const trimmed = part.trim()
      if (trimmed.length > 0) {
        this._selectedValues.add(trimmed)
      }
    })
    this._syncFormValue()
    this._syncSegmentStates()
    return
  }

  /* The value as submitted: one value (select), a comma list (toggle), nothing (action). */
  _currentValue() {
    const mode = this._mode()
    const values = Array.from(this._selectedValues)
    let value = ""
    if (mode === "select") {
      value = values.length > 0 ? values[0] : ""
    } else if (mode === "toggle") {
      value = values.join(",")
    }
    return value
  }

  _syncFormValue() {
    this._setFormValue(this._currentValue())
    if (this._mode() === "action" && this._internals !== null) {
      /* An action toolbar holds no state and submits no entry. */
      this._internals.setFormValue(null)
    }
    return
  }

  /* ----- event handlers ----- */

  _itemFor(event) {
    const node = event.target instanceof Element ? event.target.closest(".segment") : null
    const item = node !== null ? this._segmentData[parseInt(node.dataset.index, 10)] : undefined
    return item
  }

  _onSegmentClick(event) {
    const item = this._itemFor(event)
    if (item === undefined || item.node.disabled === true) {
      return
    }
    this._activate(item)
    return
  }

  /* Action mode: the toolbar's tab stop follows focus, pointer focus included. */
  _onFocusIn(event) {
    const item = this._itemFor(event)
    if (item !== undefined && this._mode() === "action") {
      this._toolbarStop = item.index
      this._syncSegmentStates()
    }
    return
  }

  /*
   * A user activation of a segment. The `value` attribute is left alone: it
   * is the default a form reset goes back to.
   */
  _activate(item) {
    const mode = this._mode()

    if (mode === "action") {
      this.emit("mj-action", { segment: item.el, value: item.value })
      return
    }

    if (mode === "select") {
      if (item.index === this._selectedIndex()) {
        /* Already selected: nothing changes, nothing is reported. */
        return
      }
      this._selectedValues.clear()
      this._selectedValues.add(item.value)
      this._syncFormValue()
      this._syncSegmentStates()
      this.emit("mj-change", {
        value: item.value,
        values: [item.value],
        segment: item.el,
        selected: true
      })
      return
    }

    const wasOn = this._selectedValues.has(item.value)
    if (wasOn === true) {
      this._selectedValues.delete(item.value)
    } else {
      this._selectedValues.add(item.value)
    }
    this._syncFormValue()
    this._syncSegmentStates()
    this.emit("mj-change", {
      value: item.value,
      values: Array.from(this._selectedValues),
      segment: item.el,
      selected: !wasOn
    })
    return
  }

  /*
   * Index of the next enabled segment from `from` in direction `delta`,
   * wrapping round; -1 when no segment is enabled.
   */
  _stepEnabled(from, delta) {
    const count = this._segmentData.length
    let found = -1

    for (let offset = 1; offset <= count; offset = offset + 1) {
      const index = (((from + delta * offset) % count) + count) % count
      if (this._segmentData[index].node.disabled === false) {
        found = index
        break
      }
    }

    return found
  }

  _onKeydown(event) {
    const mode = this._mode()
    const item = this._itemFor(event)
    if (item === undefined || mode === "toggle") {
      /* Toggle buttons are separate tab stops; Space and Enter are native. */
      return
    }

    const count = this._segmentData.length
    const rtl = getComputedStyle(this).direction === "rtl"
    const forwardInline = rtl === true ? "ArrowLeft" : "ArrowRight"
    const backwardInline = rtl === true ? "ArrowRight" : "ArrowLeft"

    /* A radiogroup takes both arrow axes; a horizontal toolbar the inline one. */
    const forward = event.key === forwardInline || (mode === "select" && event.key === "ArrowDown")
    const backward = event.key === backwardInline || (mode === "select" && event.key === "ArrowUp")

    let target = -1
    if (forward === true) {
      target = this._stepEnabled(item.index, 1)
    } else if (backward === true) {
      target = this._stepEnabled(item.index, -1)
    } else if (event.key === "Home") {
      target = this._stepEnabled(-1, 1)
    } else if (event.key === "End") {
      target = this._stepEnabled(count, -1)
    }

    if (target >= 0) {
      event.preventDefault()
      const next = this._segmentData[target]
      if (mode === "select") {
        /* Selection follows focus, as in a native radio group. */
        this._activate(next)
      } else {
        this._toolbarStop = target
        this._syncSegmentStates()
      }
      next.node.focus()
    }
    return
  }

  _validationAnchor() {
    let anchor = null
    if (this._container !== undefined && this._container !== null) {
      anchor = this._container.querySelector(".segment:not([disabled])")
    }
    return anchor
  }

  /* ----- form callbacks ----- */

  /* Reset goes back to the default given by the `value` attribute. */
  onFormReset(initial) {
    this._applyValueString(initial)
    return
  }

  onFormRestore(state) {
    this._applyValueString(typeof state === "string" ? state : "")
    return
  }

  /* An ancestor <fieldset disabled> was switched on or off. */
  onFormDisabled(disabled) {
    this._formDisabled = disabled === true
    this._syncContainer()
    this._syncSegmentStates()
    return
  }

  /* ----- scriptable API ----- */

  get segments() {
    return this._getSegmentEls()
  }

  /* Select mode: the <mj-segment> that is selected, or null. */
  get selectedSegment() {
    const index = this._mode() === "select" ? this._selectedIndex() : -1
    const segment = index >= 0 ? this._segmentData[index].el : null
    return segment
  }

  /* Toggle mode: the <mj-segment> elements that are pressed. */
  get selectedSegments() {
    const mode = this._mode()
    const pressed = this._segmentData
      .filter((item) => this._isSelected(item, mode) === true)
      .map((item) => item.el)
    return pressed
  }

  /*
   * Assigning `value` moves the selection and the submitted form value. The
   * `value` attribute keeps the default for form reset.
   */
  get value() {
    return this._currentValue()
  }

  set value(val) {
    this._applyValueString(val)
    return
  }

  focus() {
    let target = null
    if (this._container !== undefined && this._container !== null) {
      target = this._container.querySelector(".segment[tabindex='0']:not([disabled])")
    }
    if (target !== null) {
      target.focus()
    }
    return
  }
}
