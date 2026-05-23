/*
 * mjsegmentedcontrol.js
 *
 * <mj-segmented-control> — compact connected row of segments acting as
 * radio-select, independent toggles, or an action toolbar.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { RovingTabindex } from "../core/focustrap.js";

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

:host([size="sm"]) .segment { font-size: var(--mj-font-size-xs); padding: 0 var(--mj-space-2); }
:host([size="lg"]) .segment { font-size: var(--mj-font-size-md); padding: 0 var(--mj-space-4); }

:host([disabled]) .segment { opacity: 0.45; pointer-events: none; }
`;

export class MjSegmentedControl extends MjElement {
  static tagName = "mj-segmented-control";
  static styles = STYLES;
  static watched = ["mode", "value", "disabled", "stretch", "size"];

  constructor() {
    super()
    this._selectedValues = new Set()
    this._segmentData = []
    this._roving = null
    this._containerId = nextId("mj-sc")
  }

  render() {
    const mode = this.getAttribute("mode") || "select"
    const label = this.getAttribute("label") || ""
    const ariaLabel = label.length > 0 ? `aria-label="${label}"` : ""

    let containerRole = "radiogroup"
    if (mode === "toggle") {
      containerRole = "group"
    } else if (mode === "action") {
      containerRole = "toolbar"
    }

    const markup = `
      <div
        class="container"
        part="container"
        id="${this._containerId}"
        role="${containerRole}"
        ${ariaLabel}
      ></div>
    `
    return markup
  }

  afterRender() {
    this._container = this.$(".container")
    const slot = this.shadowRoot.querySelector("slot")
    if (slot !== null) {
      this.listen(slot, "slotchange", () => this._buildSegments())
    }
    this._buildSegments()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "value") {
      this._initValues()
    }
    if (name === "mode") {
      this._buildSegments()
    }
    if (name === "disabled") {
      this._syncDisabled()
    }
    return
  }

  _getSegmentEls() {
    return Array.from(this.querySelectorAll("mj-segment"))
  }

  _buildSegments() {
    const mode = this.getAttribute("mode") || "select"
    const els = this._getSegmentEls()

    this._segmentData = els.map((el, idx) => ({
      id: nextId("mj-seg"),
      value: el.getAttribute("value") || String(idx),
      label: el.textContent.trim(),
      disabled: el.hasAttribute("disabled"),
      index: idx,
      el: el
    }))

    this._initValues()

    let html = ""
    this._segmentData.forEach((item) => {
      const value = item.value
      const disabled = item.disabled === true || this.hasAttribute("disabled")
      const disabledAttr = disabled === true ? " disabled" : ""
      const tabindex = this._getTabindex(item, mode)

      let stateAttr = ""
      if (mode === "select") {
        const checked = this._selectedValues.has(value)
        stateAttr = `role="radio" aria-checked="${checked === true ? "true" : "false"}"`
      } else if (mode === "toggle") {
        const pressed = this._selectedValues.has(value)
        stateAttr = `role="button" aria-pressed="${pressed === true ? "true" : "false"}"`
      } else {
        stateAttr = `role="button"`
      }

      html += `<button
        class="segment"
        part="segment"
        id="${item.id}"
        ${stateAttr}
        tabindex="${tabindex}"
        data-value="${value}"
        data-index="${item.index}"
        ${disabledAttr}
      >
        <span class="segment-label" part="segment-label">${item.label}</span>
      </button>`
    })

    this._container.innerHTML = html

    const btns = this._container.querySelectorAll(".segment")
    btns.forEach((btn) => {
      this.listen(btn, "click", this._onSegmentClick.bind(this))
    })

    if (mode === "select") {
      this._setupRoving()
    }
    return
  }

  _getTabindex(item, mode) {
    if (mode === "select") {
      const isSelected = this._selectedValues.has(item.value)
      const isFirst = item.index === 0
      const anySelected = this._selectedValues.size > 0
      return (isSelected === true || (anySelected === false && isFirst === true)) ? "0" : "-1"
    }
    return item.disabled === true ? "-1" : "0"
  }

  _initValues() {
    const attrVal = this.getAttribute("value") || ""
    this._selectedValues.clear()
    if (attrVal.length > 0) {
      attrVal.split(",").forEach((v) => {
        const t = v.trim()
        if (t.length > 0) {
          this._selectedValues.add(t)
        }
      })
    }
    if (this._container !== undefined) {
      this._updateSegmentStates()
    }
    return
  }

  _updateSegmentStates() {
    const mode = this.getAttribute("mode") || "select"
    const btns = this._container.querySelectorAll(".segment")
    btns.forEach((btn) => {
      const val = btn.dataset.value
      if (mode === "select") {
        btn.setAttribute("aria-checked", this._selectedValues.has(val) === true ? "true" : "false")
      } else if (mode === "toggle") {
        btn.setAttribute("aria-pressed", this._selectedValues.has(val) === true ? "true" : "false")
      }
    })
    return
  }

  _setupRoving() {
    if (this._roving !== null) {
      this._roving._disposeHandler && this._roving._disposeHandler()
    }
    const items = Array.from(this._container.querySelectorAll(".segment:not([disabled])"))
    this._roving = new RovingTabindex({
      items: items,
      orientation: "horizontal",
      wrap: true
    })
    const selected = items.findIndex((btn) => btn.getAttribute("aria-checked") === "true")
    this._roving.index = selected >= 0 ? selected : 0
    const dispose = this._roving.attach(this._container)
    this._roving._disposeHandler = dispose
    return
  }

  _onSegmentClick(event) {
    const btn = event.currentTarget
    if (btn.disabled === true) {
      return
    }
    const mode = this.getAttribute("mode") || "select"
    const value = btn.dataset.value

    if (mode === "action") {
      const data = this._segmentData[parseInt(btn.dataset.index, 10)]
      this.emit("mj-action", { segment: data !== undefined ? data.el : null })
      return
    }

    if (mode === "select") {
      const prevValues = Array.from(this._selectedValues)
      this._selectedValues.clear()
      this._selectedValues.add(value)
      this.setAttribute("value", value)
      this._updateSegmentStates()
      this._setupRoving()
      const idx = parseInt(btn.dataset.index, 10)
      const data = this._segmentData[idx]
      this.emit("mj-change", {
        value: value,
        values: [value],
        segment: data !== undefined ? data.el : null,
        selected: true
      })
    } else if (mode === "toggle") {
      const wasOn = this._selectedValues.has(value)
      if (wasOn === true) {
        this._selectedValues.delete(value)
      } else {
        this._selectedValues.add(value)
      }
      const vals = Array.from(this._selectedValues)
      this.setAttribute("value", vals.join(","))
      this._updateSegmentStates()
      const idx = parseInt(btn.dataset.index, 10)
      const data = this._segmentData[idx]
      this.emit("mj-change", {
        value: value,
        values: vals,
        segment: data !== undefined ? data.el : null,
        selected: !wasOn
      })
    }
    return
  }

  _syncDisabled() {
    if (this._container === undefined) {
      return
    }
    const disabled = this.hasAttribute("disabled")
    const btns = this._container.querySelectorAll(".segment")
    btns.forEach((btn) => {
      btn.disabled = disabled
    })
    return
  }

  get segments() {
    return this._getSegmentEls()
  }

  get value() {
    return Array.from(this._selectedValues).join(",")
  }

  set value(val) {
    this.setAttribute("value", val)
    return
  }

  focus() {
    const first = this._container !== undefined ? this._container.querySelector("[tabindex='0']") : null
    if (first !== null) {
      first.focus()
    }
    return
  }
}
