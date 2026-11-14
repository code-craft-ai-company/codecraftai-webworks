/*
 * mjlistbox.js
 *
 * <mj-listbox> — permanently-visible scrollable list supporting single and
 * multiple selection, keyboard navigation through aria-activedescendant, and
 * form participation.
 *
 * Options are the <mj-option> descendants of the host; options inside an
 * <mj-optgroup label="..."> are listed under that heading in a role="group"
 * container, and a `disabled` group disables its options. A
 * MutationObserver keeps the list in step with them, so options added,
 * removed or relabelled after the first render show up without re-creating
 * the element.
 *
 * The `value` attribute is the default selection (what a form reset
 * restores); the live selection is held in `_selectedValues` and survives a
 * move in the DOM. In multiple mode a plain click or Space toggles one
 * option, Shift extends a range from the anchor option, and Ctrl/Cmd+A
 * selects or clears everything.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { announce } from "../core/announcer.js";
import { t } from "../core/intl.js";

const STYLES = `
:host {
  display: block;
}

.listbox {
  display: block;
  min-height: var(--mj-listbox-min-height, 8rem);
  max-height: var(--mj-listbox-max-height, 24rem);
  overflow-y: auto;
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-listbox-border-radius, var(--mj-radius-md));
  background: var(--mj-surface);
  outline: none;
}
.listbox:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.option {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  padding: var(--mj-listbox-option-padding, var(--mj-space-2) var(--mj-space-3));
  min-height: var(--mj-listbox-option-height, var(--mj-control-height-md));
  cursor: pointer;
  user-select: none;
  color: var(--mj-text);
  font-size: var(--mj-font-size-md);
}
.option:hover { background: var(--mj-bg-muted); }
/*
 * A selected option is tinted with the accent and carries the check mark in
 * both modes, so the selection is visible in either theme and is not shown
 * by colour alone.
 */
.option[aria-selected="true"] {
  background: var(--mj-listbox-selected-bg, color-mix(in srgb, var(--mj-accent) 16%, transparent));
  font-weight: var(--mj-font-weight-medium);
}
.option[aria-disabled="true"] { opacity: 0.45; cursor: not-allowed; }
.option.focused { outline: 2px solid var(--mj-focus-ring); outline-offset: -2px; }

:host([size="sm"]) .option { min-height: var(--mj-control-height-sm); font-size: var(--mj-font-size-sm); padding: var(--mj-space-1) var(--mj-space-3); }
:host([size="lg"]) .option { min-height: var(--mj-control-height-lg); font-size: var(--mj-font-size-lg); }

.check {
  width: 1em; height: 1em; flex-shrink: 0;
  color: var(--mj-accent);
  visibility: hidden;
}
.option[aria-selected="true"] .check { visibility: visible; }

.optgroup { padding: 0; }
.optgroup-label {
  padding: var(--mj-space-1) var(--mj-space-3);
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text-muted);
  font-weight: var(--mj-font-weight-medium);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
/*
 * The empty message is a sibling of the listbox (a listbox owns only options
 * and groups) laid over the top of the empty box. A click on its text falls
 * through to the listbox; slotted elements such as links still take it.
 */
.frame { position: relative; }
.empty {
  position: absolute;
  inset-block-start: 1px;
  inset-inline: 1px;
  padding: var(--mj-space-4);
  color: var(--mj-text-muted);
  text-align: center;
  font-size: var(--mj-font-size-sm);
  pointer-events: none;
}
.empty ::slotted(*) { pointer-events: auto; }
:host([disabled]) .listbox,
:host([disabled]) .empty { opacity: 0.55; pointer-events: none; }
:host([invalid]) .listbox { border-color: var(--mj-color-danger); }
:host(:state(user-invalid)) .listbox { border-color: var(--mj-color-danger); }
`;

const CHECK_ICON_MARKUP =
  '<svg class="check" part="option-checkbox" aria-hidden="true" viewBox="0 0 16 16" fill="currentColor"><path d="M13.5 3.5 6 11 2.5 7.5l1-1L6 9 12.5 2.5z"/></svg>'

/* Option attributes whose changes alter what the list shows. */
const OPTION_ATTRIBUTES = ["value", "disabled", "label"]

/*
 * Text content of `node` with the subtree of `skip` left out, whitespace
 * collapsed. Used to read a wrapping <label> without the listbox's own
 * option text.
 */
function textExcluding(node, skip) {
  const parts = []
  const visit = (current) => {
    if (current === skip) {
      return
    }
    if (current.nodeType === Node.TEXT_NODE) {
      parts.push(current.textContent)
      return
    }
    const children = current.childNodes
    for (let index = 0; index < children.length; index = index + 1) {
      visit(children[index])
    }
  }
  visit(node)
  const rtnval = parts.join(" ").replace(/\s+/g, " ").trim()
  return rtnval
}

export class MjListbox extends FormControlMixin(MjElement) {
  static tagName = "mj-listbox";
  static styles = STYLES;
  static watched = [
    "value", "multiple", "disabled", "readonly", "required", "invalid", "size",
    "label", "aria-label", "aria-labelledby"
  ];

  constructor() {
    super()
    this._initFormControl()
    this._selectedValues = new Set()
    this._focusedIndex = -1
    this._optionData = []

    /* Range selection: the option a Shift range starts from, and the
       selection that existed when that anchor was set. */
    this._anchorIndex = -1
    this._rangeBase = []

    /* The `multiple` state the selection was last normalised for. */
    this._appliedMultiple = null

    /* True while an ancestor <fieldset disabled> disables the control. */
    this._formDisabled = false

    /* The `value` attribute change applied before the first render, if any. */
    this._preRenderValue = null

    this._listboxId = nextId("mj-listbox")
  }

  render() {
    const markup = `
      <div class="frame">
        <div
          class="listbox"
          part="listbox"
          id="${this._listboxId}"
          role="listbox"
          tabindex="0"
        ></div>
        <div class="empty" part="empty" id="${this._listboxId}-empty" hidden>
          <slot name="empty"></slot>
        </div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._el = this.$(".listbox")
    this._emptyEl = this.$(".empty")
    this.listen(this._el, "keydown", this._onKeydown.bind(this))
    this.listen(this._el, "click", this._onClick.bind(this))
    this.listen(this._el, "focus", this._onFocus.bind(this))
    this.listen(this, "click", this._onHostClick.bind(this))

    this._appliedMultiple = this.hasAttribute("multiple")

    this._observeOptions()
    this._buildOptions()
    this._syncFormValue()
    this._syncAccessibility()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "value" && this._isReplayedValue(newValue) === false) {
      this._applyValueString(newValue || "")
    }
    if (name === "multiple") {
      this._onMultipleChanged(newValue !== null)
    }
    if (
      name === "disabled" || name === "invalid" || name === "readonly" || name === "required" ||
      name === "multiple" || name === "label" || name === "aria-label" || name === "aria-labelledby"
    ) {
      this._syncAccessibility()
    }
    if (name === "required" && this._internals !== undefined) {
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

  /*
   * `multiple` was switched. Before the first render the selection is parsed
   * again from the `value` attribute, because the attributes may arrive in
   * either order. At runtime the selection goes back to the default given by
   * the `value` attribute so a single-select never holds several values.
   */
  _onMultipleChanged(isMultiple) {
    if (this._appliedMultiple === isMultiple) {
      return
    }

    const firstTime = this._appliedMultiple === null
    this._appliedMultiple = isMultiple

    if (firstTime === true && this.hasAttribute("value") === false) {
      /* Nothing to re-parse; keep a value assigned through the property. */
      this._applyValueString(Array.from(this._selectedValues).join(","))
    } else {
      this._applyValueString(this.getAttribute("value") || "")
    }
    return
  }

  /* ----- option management ----- */

  _getOptionEls() {
    const els = Array.from(this.querySelectorAll("mj-option"))
    return els
  }

  /*
   * Rebuild the list whenever the <mj-option> children change. Mutation
   * records are delivered once per microtask checkpoint, so a consumer that
   * appends many options in a loop causes a single rebuild.
   */
  _observeOptions() {
    if (typeof MutationObserver !== "function") {
      return
    }
    const observer = new MutationObserver((records) => {
      this._onOptionsMutated(records)
    })
    observer.observe(this, {
      childList: true,
      subtree: true,
      characterData: true,
      attributes: true,
      attributeFilter: OPTION_ATTRIBUTES
    })
    this.onTeardown(() => {
      observer.disconnect()
    })
    return
  }

  _onOptionsMutated(records) {
    const relevant = records.some((record) => {
      return record.type !== "attributes" || record.target !== this
    })
    if (relevant === false || this._el === undefined || this._el === null) {
      return
    }

    /* Keep the active option by element, not by position. */
    const focusedItem = this._optionData[this._focusedIndex]
    const focusedEl = focusedItem !== undefined ? focusedItem.el : null

    this._buildOptions()

    const restored = this._optionData.findIndex((item) => item.el === focusedEl)
    this._focusedIndex = restored
    this._anchorIndex = -1
    this._syncOptionStates()
    return
  }

  /*
   * The value an <mj-option> stands for: its `value` attribute, or its text
   * when the attribute is absent (as a native <option> does).
   */
  _optionValue(optionEl, label) {
    let value = label
    if (optionEl.hasAttribute("value") === true) {
      value = optionEl.getAttribute("value")
    }
    return value
  }

  /*
   * The shadow node that holds the options of an <mj-optgroup>: a
   * role="group" container named by its heading row.
   */
  _buildGroupNode(groupEl) {
    const labelId = nextId("mj-lb-group")

    const groupNode = document.createElement("div")
    groupNode.className = "optgroup"
    groupNode.setAttribute("part", "optgroup")
    groupNode.setAttribute("role", "group")
    groupNode.setAttribute("aria-labelledby", labelId)

    const labelNode = document.createElement("div")
    labelNode.className = "optgroup-label"
    labelNode.setAttribute("part", "optgroup-label")
    labelNode.id = labelId
    labelNode.textContent = groupEl.getAttribute("label") || ""
    groupNode.appendChild(labelNode)

    return groupNode
  }

  /*
   * Build one row per <mj-option>. Rows are created with DOM APIs and
   * textContent, never markup: option labels are usually application data.
   * The options of one <mj-optgroup> are contiguous in document order, so
   * the rows keep the order of `_optionData` with or without groups.
   */
  _buildOptions() {
    const optionEls = this._getOptionEls()
    this._el.replaceChildren()
    this._optionData = []

    /* The empty message is outside the listbox and describes it while shown. */
    const isEmpty = optionEls.length === 0
    this._emptyEl.hidden = isEmpty === false
    if (isEmpty === true) {
      this._emptyEl.querySelector("slot").textContent = t("mj.select.noOptions")
      this._el.setAttribute("aria-describedby", this._emptyEl.id)
      this._focusedIndex = -1
      this._el.removeAttribute("aria-activedescendant")
      return
    }
    this._el.removeAttribute("aria-describedby")

    /* <mj-optgroup> element -> the group node built for it. */
    const groupNodes = new Map()

    optionEls.forEach((optionEl, index) => {
      const groupEl = optionEl.closest("mj-optgroup")
      const inGroup = groupEl !== null && this.contains(groupEl) === true
      const label = optionEl.getAttribute("label") || optionEl.textContent.trim()
      const item = {
        id: nextId("mj-lb-opt"),
        value: this._optionValue(optionEl, label),
        label: label,
        disabled: optionEl.hasAttribute("disabled") || (inGroup === true && groupEl.hasAttribute("disabled")),
        index: index,
        el: optionEl
      }
      optionEl._mjId = item.id
      this._optionData.push(item)

      const node = document.createElement("div")
      node.className = "option"
      node.setAttribute("part", "option")
      node.setAttribute("role", "option")
      node.id = item.id
      node.dataset.index = String(item.index)
      if (item.disabled === true) {
        node.setAttribute("aria-disabled", "true")
      }
      node.innerHTML = CHECK_ICON_MARKUP

      const labelEl = document.createElement("span")
      labelEl.className = "option-label"
      labelEl.setAttribute("part", "option-label")
      labelEl.textContent = item.label
      node.appendChild(labelEl)

      let container = this._el
      if (inGroup === true) {
        if (groupNodes.has(groupEl) === false) {
          const groupNode = this._buildGroupNode(groupEl)
          groupNodes.set(groupEl, groupNode)
          this._el.appendChild(groupNode)
        }
        container = groupNodes.get(groupEl)
      }
      container.appendChild(node)
    })

    this._syncOptionStates()
    return
  }

  _optionNodes() {
    const nodes = Array.from(this._el.querySelectorAll(".option"))
    return nodes
  }

  /*
   * Bring aria-selected, the active-option marker and
   * aria-activedescendant in line with the fields. The rows themselves are
   * left in place.
   */
  _syncOptionStates() {
    if (this._el === undefined || this._el === null) {
      return
    }

    const nodes = this._optionNodes()
    let activeId = null

    nodes.forEach((node, index) => {
      const item = this._optionData[index]
      const selected = item !== undefined && this._selectedValues.has(item.value)
      node.setAttribute("aria-selected", selected === true ? "true" : "false")

      const focused = index === this._focusedIndex
      node.classList.toggle("focused", focused)
      if (focused === true) {
        activeId = node.id
      }
    })

    if (activeId !== null) {
      this._el.setAttribute("aria-activedescendant", activeId)
    } else {
      this._el.removeAttribute("aria-activedescendant")
    }
    return
  }

  /*
   * Replace the selection with the values in `text`: a comma-separated list
   * in multiple mode, one value otherwise. Emits nothing -- used for the
   * `value` attribute and property, form reset and restore.
   */
  _applyValueString(text) {
    const source = text === null || text === undefined ? "" : String(text)
    this._selectedValues.clear()

    if (this.hasAttribute("multiple") === true) {
      source.split(",").forEach((part) => {
        const trimmed = part.trim()
        if (trimmed.length > 0) {
          this._selectedValues.add(trimmed)
        }
      })
    } else if (source.length > 0) {
      this._selectedValues.add(source)
    }

    this._anchorIndex = -1
    this._syncFormValue()
    this._syncOptionStates()
    return
  }

  _syncFormValue() {
    const vals = Array.from(this._selectedValues)
    this._setFormValue(vals.join(","))
    return
  }

  /* ----- selection ----- */

  _canChange() {
    const allowed = this.hasAttribute("readonly") === false && this._isDisabled() === false
    return allowed
  }

  /*
   * Change the selection from a user action on the option at `index`.
   *   mode "replace"  single-select: this option becomes the selection
   *   mode "toggle"   multiple: flip this option, and make it the range anchor
   *   mode "range"    multiple: select from the anchor through this option,
   *                   on top of what was selected when the anchor was set
   */
  _select(index, mode) {
    if (this._canChange() === false) {
      return
    }

    const item = this._optionData[index]
    if (item === undefined || item.disabled === true) {
      return
    }

    const previousValues = Array.from(this._selectedValues)

    if (mode === "range" && this._anchorIndex >= 0) {
      const start = Math.min(this._anchorIndex, index)
      const end = Math.max(this._anchorIndex, index)
      this._selectedValues = new Set(this._rangeBase)
      for (let position = start; position <= end; position = position + 1) {
        const candidate = this._optionData[position]
        if (candidate !== undefined && candidate.disabled !== true) {
          this._selectedValues.add(candidate.value)
        }
      }
    } else if (mode === "replace") {
      this._selectedValues.clear()
      this._selectedValues.add(item.value)
      this._anchorIndex = index
      this._rangeBase = []
    } else {
      if (this._selectedValues.has(item.value) === true) {
        this._selectedValues.delete(item.value)
      } else {
        this._selectedValues.add(item.value)
      }
      this._anchorIndex = index
      this._rangeBase = Array.from(this._selectedValues).filter((value) => value !== item.value)
    }

    this._focusedIndex = index
    this._finishSelectionChange(previousValues)
    this._scrollIntoView(index)
    return
  }

  /* Select every enabled option, or clear the selection when all are selected. */
  _toggleAll() {
    if (this._canChange() === false) {
      return
    }

    const enabled = this._optionData.filter((item) => item.disabled !== true)
    const allSelected = enabled.every((item) => this._selectedValues.has(item.value))
    const previousValues = Array.from(this._selectedValues)

    enabled.forEach((item) => {
      if (allSelected === true) {
        this._selectedValues.delete(item.value)
      } else {
        this._selectedValues.add(item.value)
      }
    })

    this._anchorIndex = -1
    this._finishSelectionChange(previousValues)
    return
  }

  /*
   * Common tail of every user selection change: update the form value and
   * the rows, then report the change if the selection really differs.
   */
  _finishSelectionChange(previousValues) {
    this._syncFormValue()
    this._syncOptionStates()

    const newValues = Array.from(this._selectedValues)
    const changed =
      newValues.length !== previousValues.length ||
      newValues.some((value) => previousValues.includes(value) === false)

    if (changed === true) {
      this.emit("mj-change", {
        value: newValues.join(","),
        values: newValues,
        previousValues: previousValues
      })

      if (this.hasAttribute("multiple") === true) {
        announce(t("mj.listbox.selectedCount", { count: newValues.length }), "polite")
      }
    }
    return
  }

  _scrollIntoView(index) {
    const node = this._optionNodes()[index]
    if (node !== undefined) {
      node.scrollIntoView({ block: "nearest" })
    }
    return
  }

  /* ----- event handlers ----- */

  _onClick(event) {
    const optEl = event.target instanceof Element ? event.target.closest(".option") : null
    if (optEl === null) {
      return
    }
    if (this._isDisabled() === true) {
      return
    }

    const index = parseInt(optEl.dataset.index, 10)
    const isMulti = this.hasAttribute("multiple")

    /* The clicked option becomes the active one even when it cannot change. */
    this._focusedIndex = index
    this._syncOptionStates()

    if (isMulti === false) {
      this._select(index, "replace")
    } else if (event.shiftKey === true) {
      this._select(index, "range")
    } else {
      this._select(index, "toggle")
    }
    this._el.focus()
    return
  }

  /*
   * A click aimed at the host itself (not at a row inside it) is what an
   * associated <label> dispatches when it is clicked: move focus to the list
   * the way a native control would.
   */
  _onHostClick(event) {
    const origin = event.composedPath()[0]
    if (origin === this && this._el !== undefined && this._isDisabled() === false) {
      this._el.focus()
    }
    return
  }

  /*
   * Focus arriving on the list needs an active option for the arrow keys to
   * start from: the first selected option, or the first enabled one.
   */
  _onFocus() {
    /* An associated <label> may have been attached or reworded since. */
    this._syncAccessibility()

    if (this._focusedIndex >= 0 || this._optionData.length === 0) {
      return
    }

    let start = this._optionData.findIndex((item) => {
      return item.disabled !== true && this._selectedValues.has(item.value)
    })
    if (start < 0) {
      start = this._optionData.findIndex((item) => item.disabled !== true)
    }
    if (start >= 0) {
      this._focusedIndex = start
      this._syncOptionStates()
    }
    return
  }

  /* Index of the nearest enabled option from `from` in direction `delta`, or -1. */
  _nextEnabledIndex(from, delta) {
    const count = this._optionData.length
    let found = -1
    let position = from + delta

    while (position >= 0 && position < count) {
      if (this._optionData[position].disabled !== true) {
        found = position
        break
      }
      position = position + delta
    }

    return found
  }

  _onKeydown(event) {
    const count = this._optionData.length
    if (count === 0 || this._isDisabled() === true) {
      return
    }

    const current = this._focusedIndex >= 0 ? this._focusedIndex : -1
    const isMulti = this.hasAttribute("multiple")
    const extend = event.shiftKey === true && isMulti === true
    const commandKey = event.ctrlKey === true || event.metaKey === true

    let target = -1

    if (event.key === "ArrowDown") {
      event.preventDefault()
      target = this._nextEnabledIndex(current, 1)
    } else if (event.key === "ArrowUp") {
      event.preventDefault()
      target = this._nextEnabledIndex(current >= 0 ? current : count, -1)
    } else if (event.key === "Home") {
      event.preventDefault()
      target = this._nextEnabledIndex(-1, 1)
    } else if (event.key === "End") {
      event.preventDefault()
      target = this._nextEnabledIndex(count, -1)
    } else if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      if (current >= 0) {
        if (isMulti === false) {
          this._select(current, "replace")
        } else if (event.shiftKey === true) {
          this._select(current, "range")
        } else {
          this._select(current, "toggle")
        }
      }
    } else if (commandKey === true && (event.key === "a" || event.key === "A")) {
      if (isMulti === true) {
        event.preventDefault()
        this._toggleAll()
      }
    } else if (event.key.length === 1 && commandKey === false && event.altKey === false) {
      this._typeaheadNav(event.key)
    }

    if (target >= 0) {
      if (extend === true) {
        if (this._anchorIndex < 0) {
          /* The range starts at the option focus is leaving. */
          this._anchorIndex = current >= 0 ? current : target
          this._rangeBase = Array.from(this._selectedValues)
        }
        this._select(target, "range")
        if (this._focusedIndex !== target) {
          /* readonly: the selection stays, focus still moves. */
          this._moveFocusOnly(target)
        }
      } else {
        this._moveFocusOnly(target)
      }
    }
    return
  }

  _typeaheadNav(char) {
    const needle = char.toLowerCase()
    const start = this._focusedIndex + 1
    const data = this._optionData
    const count = data.length

    for (let offset = 0; offset < count; offset = offset + 1) {
      const index = (start + offset) % count
      const item = data[index]
      if (item.disabled !== true && item.label.toLowerCase().startsWith(needle)) {
        this._moveFocusOnly(index)
        break
      }
    }
    return
  }

  _moveFocusOnly(index) {
    this._focusedIndex = index
    this._syncOptionStates()
    this._scrollIntoView(index)
    this.emit("mj-option-focus", { option: this._optionData[index] })
    return
  }

  /* ----- accessibility ----- */

  /*
   * The text that names the listbox: the `label` attribute, then the host's
   * `aria-label`, then the elements named by the host's `aria-labelledby`,
   * then any <label> associated with the host (wrapping or `for`).
   */
  _computeAccessibleName() {
    const labelAttr = (this.getAttribute("label") || "").trim()
    if (labelAttr.length > 0) {
      return labelAttr
    }
    const ariaLabel = (this.getAttribute("aria-label") || "").trim()
    if (ariaLabel.length > 0) {
      return ariaLabel
    }
    const labelledBy = (this.getAttribute("aria-labelledby") || "").trim()
    if (labelledBy.length > 0) {
      const root = this.getRootNode()
      const texts = []
      labelledBy.split(/\s+/).forEach((id) => {
        const target = typeof root.getElementById === "function" ? root.getElementById(id) : null
        if (target !== null) {
          texts.push(textExcluding(target, this))
        }
      })
      const joined = texts.filter((text) => text.length > 0).join(" ")
      if (joined.length > 0) {
        return joined
      }
    }
    let labels = []
    try {
      labels = this._internals !== null && this._internals.labels ? Array.from(this._internals.labels) : []
    } catch (error) {
      labels = []
    }
    const rtnval = labels
      .map((labelEl) => textExcluding(labelEl, this))
      .filter((text) => text.length > 0)
      .join(" ")
    return rtnval
  }

  _setBooleanAria(name, on) {
    if (on === true) {
      this._el.setAttribute(name, "true")
    } else {
      this._el.removeAttribute(name)
    }
    return
  }

  /* One place that mirrors every host state onto the role="listbox" element. */
  _syncAccessibility() {
    if (this._el === undefined || this._el === null) {
      return
    }

    const name = this._computeAccessibleName()
    if (name.length > 0) {
      this._el.setAttribute("aria-label", name)
    } else {
      this._el.removeAttribute("aria-label")
    }

    const disabled = this._isDisabled()
    this._setBooleanAria("aria-multiselectable", this.hasAttribute("multiple"))
    this._setBooleanAria("aria-invalid", this.hasAttribute("invalid") || this._isUserInvalid() === true)
    this._setBooleanAria("aria-disabled", disabled)
    this._setBooleanAria("aria-readonly", this.hasAttribute("readonly"))
    this._setBooleanAria("aria-required", this.hasAttribute("required"))

    /* A disabled list leaves the tab order. */
    this._el.tabIndex = disabled === true ? -1 : 0
    return
  }

  /*
   * A required listbox with nothing selected reports valueMissing with its
   * own message ("At least one selection is required."), or with the
   * `required-message` attribute when the page gives one. FormControlMixin
   * reports that case with the generic core.required text before any
   * component check runs, so the message is replaced here, after it.
   */
  _refreshValidity() {
    super._refreshValidity()

    const validity = this.validity
    const ownMessage = this.hasAttribute("required-message") === false
    if (validity !== null && validity.valueMissing === true && ownMessage === true) {
      const message = t("mj.listbox.selectionRequired")
      const anchor = this._validationAnchor()
      if (anchor !== null && anchor !== undefined && anchor !== this) {
        this._internals.setValidity({ valueMissing: true }, message, anchor)
      } else {
        this._internals.setValidity({ valueMissing: true }, message)
      }
      if (this._isUserInvalid() === true) {
        this.onInvalid(message)
      }
    }
    return
  }

  /*
   * FormControlMixin hooks: a failed validation (an mj-form submit) marks the
   * control invalid, as the `invalid` attribute does, until it is valid again.
   */
  onInvalid(message) {
    if (this._el !== undefined && this._el !== null) {
      this._syncAccessibility()
    }
    return
  }

  onValidityRestored() {
    if (this._el !== undefined && this._el !== null) {
      this._syncAccessibility()
    }
    return
  }

  _validationAnchor() {
    return this._el || this
  }

  /* ----- form callbacks ----- */

  /* Reset goes back to the default selection given by the `value` attribute. */
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
    this._syncAccessibility()
    return
  }

  /* ----- scriptable API ----- */

  get selectedValues() {
    return Array.from(this._selectedValues)
  }

  /*
   * Assigning `value` replaces the selection and updates the rows. The
   * `value` attribute keeps the default selection for form reset.
   */
  set value(val) {
    this._applyValueString(val)
    return
  }

  get value() {
    return Array.from(this._selectedValues).join(",")
  }

  /* Every <mj-option> of the listbox, in document order. */
  get options() {
    return this._getOptionEls()
  }

  focus() {
    if (this._el !== undefined) {
      this._el.focus()
    }
    return
  }
}
