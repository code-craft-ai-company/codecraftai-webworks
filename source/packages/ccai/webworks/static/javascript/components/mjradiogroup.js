/*
 * mjradiogroup.js
 *
 * <mj-radio-group> — mutually exclusive radio group with roving tabindex,
 * ARIA radiogroup semantics, and form participation.
 *
 * Radios are the <mj-radio> descendants of the host. Each one is rendered as
 * a role="radio" row whose label is a copy of the radio's own nodes and
 * whose description is a copy of its `slot="description"` children. A
 * MutationObserver keeps the rows in step with the <mj-radio> elements.
 *
 * Keyboard (WAI-ARIA radio group): Tab enters on the checked radio, or the
 * first enabled one; the arrow keys of both axes, Home and End move focus
 * and check the radio they land on; Space checks the focused radio.
 *
 * The `value` attribute is the default value (what a form reset restores);
 * the live value is the `value` property.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";

const STYLES = `
:host { display: block; }

.group {
  display: flex;
  flex-direction: column;
  gap: var(--mj-radio-group-gap, var(--mj-space-2));
}

.radio-items {
  display: flex;
  flex-direction: column;
  gap: var(--mj-radio-group-gap, var(--mj-space-2));
}
:host([orientation="horizontal"]) .radio-items {
  flex-direction: row;
  flex-wrap: wrap;
  gap: var(--mj-radio-group-gap, var(--mj-space-2) var(--mj-space-4));
}

.group-label {
  font-weight: var(--mj-font-weight-medium);
  margin-bottom: var(--mj-space-1);
  color: var(--mj-text);
}

.help, .error {
  font-size: var(--mj-font-size-sm);
  margin-top: var(--mj-space-1);
}
.help { color: var(--mj-text-muted); }
.error { color: var(--mj-color-danger); }
/* Shown for the \`invalid\` attribute, or after a failed validation (data-visible). */
:host(:not([invalid])) .error:not([data-visible]) { display: none; }

.radio-item {
  display: flex;
  gap: var(--mj-radio-label-gap, var(--mj-space-2));
  cursor: pointer;
  min-height: var(--mj-target-min);
  align-items: center;
  outline: none;
}
.radio-item[aria-disabled="true"] { opacity: 0.45; cursor: not-allowed; }

.radio-control {
  flex-shrink: 0;
  width: var(--mj-radio-size, 1rem);
  height: var(--mj-radio-size, 1rem);
  border-radius: 50%;
  border: 2px solid var(--mj-radio-border-color, var(--mj-border-strong));
  display: flex;
  align-items: center;
  justify-content: center;
  transition: border-color var(--mj-motion-fast);
  outline: none;
}
.radio-item[aria-checked="true"] .radio-control {
  border-color: var(--mj-radio-color, var(--mj-accent));
  background: var(--mj-radio-color, var(--mj-accent));
}
.radio-item:focus-visible .radio-control {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.radio-dot {
  width: 40%;
  height: 40%;
  border-radius: 50%;
  background: var(--mj-text-on-accent);
  opacity: 0;
  transition: opacity var(--mj-motion-fast);
}
.radio-item[aria-checked="true"] .radio-dot { opacity: 1; }

.radio-text { display: flex; flex-direction: column; gap: 2px; }
.radio-label { color: var(--mj-text); }
.radio-description { font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }
.radio-description:empty { display: none; }

/* Button variant */
:host([variant="button"]) .radio-item {
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-md);
  padding: var(--mj-space-2) var(--mj-space-3);
  min-height: var(--mj-control-height-md);
  gap: var(--mj-space-2);
}
:host([variant="button"]) .radio-item[aria-checked="true"] {
  border-color: var(--mj-accent);
  background: var(--mj-bg-subtle);
}
:host([variant="button"]) .radio-item:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
:host([variant="button"]) .radio-control { display: none; }

.group[aria-disabled="true"] .radio-item { opacity: 0.45; cursor: not-allowed; pointer-events: none; }
:host([invalid]) .group { outline: 2px solid var(--mj-color-danger); border-radius: var(--mj-radius-md); padding: var(--mj-space-1); }
`;

/* <mj-radio> attributes whose changes alter what a row shows. */
const RADIO_ATTRIBUTES = ["value", "disabled", "slot"]

export class MjRadioGroup extends FormControlMixin(MjElement) {
  static tagName = "mj-radio-group";
  static styles = STYLES;
  static watched = [
    "value", "disabled", "readonly", "required", "invalid", "orientation", "variant",
    "label", "aria-label"
  ];

  constructor() {
    super()
    this._initFormControl()
    this._radioData = []

    /* True while an ancestor <fieldset disabled> disables the control. */
    this._formDisabled = false

    /* The `value` attribute change applied before the first render, if any. */
    this._preRenderValue = null

    this._groupId = nextId("mj-rg")
    this._labelId = nextId("mj-rg-label")
    this._helpId = nextId("mj-rg-help")
    this._errorId = nextId("mj-rg-err")
  }

  render() {
    const markup = `
      <div
        class="group"
        part="group"
        role="radiogroup"
      >
        <span class="group-label" part="group-label" id="${this._labelId}"><slot name="label"></slot></span>
        <div class="radio-items" part="radios"></div>
        <span class="help" part="help" id="${this._helpId}"><slot name="help"></slot></span>
        <span class="error" part="error" id="${this._errorId}" role="alert"><slot name="error"><span class="error-text"></span></slot></span>
      </div>
    `
    return markup
  }

  afterRender() {
    this._group = this.$(".group")
    this._itemsEl = this.$(".radio-items")

    /* One delegated pair of listeners serves every radio row. */
    this.listen(this._itemsEl, "click", this._onRadioClick.bind(this))
    this.listen(this._itemsEl, "keydown", this._onKeydown.bind(this))

    this._observeRadios()
    this._buildRadios()
    this._syncAccessibility()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "value" && this._isReplayedValue(newValue) === false) {
      this._setFormValue(newValue || "")
      this._syncChecked()
    }
    if (
      name === "disabled" || name === "invalid" || name === "readonly" || name === "required" ||
      name === "label" || name === "aria-label"
    ) {
      this._syncAccessibility()
    }
    if (name === "disabled") {
      this._syncChecked()
    }
    if (name === "required" && this._internals !== undefined) {
      this._refreshValidity()
    }
    return
  }

  /*
   * The base class delivers an attribute change that arrived before the first
   * render a second time once the shadow DOM exists. For `value` the first
   * delivery already stored the value, and applying it again would discard a
   * `value` property assigned in between. Returns true for that repeat.
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

  /* ----- radio rows ----- */

  _getMjRadios() {
    return Array.from(this.querySelectorAll("mj-radio"))
  }

  /*
   * Rebuild the rows whenever the <mj-radio> children change. Mutation
   * records are delivered once per microtask checkpoint, so adding several
   * radios in a loop causes a single rebuild.
   */
  _observeRadios() {
    if (typeof MutationObserver !== "function") {
      return
    }
    const observer = new MutationObserver((records) => {
      const relevant = records.some((record) => {
        return record.type !== "attributes" || record.target !== this
      })
      if (relevant === true && this._itemsEl !== undefined && this._itemsEl !== null) {
        this._buildRadios()
      }
    })
    observer.observe(this, {
      childList: true,
      subtree: true,
      characterData: true,
      attributes: true,
      attributeFilter: RADIO_ATTRIBUTES
    })
    this.onTeardown(() => {
      observer.disconnect()
    })
    return
  }

  _itemNodes() {
    const nodes = Array.from(this._itemsEl.querySelectorAll(".radio-item"))
    return nodes
  }

  /*
   * Build one row for an <mj-radio>. The label and description are copies of
   * the radio's own nodes (cloneNode), never markup assembled from strings,
   * so rich content is kept and nothing is re-parsed as HTML.
   */
  _buildRadioNode(radioEl, index) {
    const id = nextId("mj-radio")

    const node = document.createElement("div")
    node.className = "radio-item"
    node.setAttribute("part", "radio")
    node.setAttribute("role", "radio")
    node.id = id
    node.setAttribute("aria-checked", "false")
    node.setAttribute("aria-labelledby", `${id}-label`)
    node.tabIndex = -1
    node.dataset.index = String(index)

    const control = document.createElement("span")
    control.className = "radio-control"
    control.setAttribute("part", "radio-input")
    control.setAttribute("aria-hidden", "true")
    const dot = document.createElement("span")
    dot.className = "radio-dot"
    control.appendChild(dot)
    node.appendChild(control)

    const text = document.createElement("span")
    text.className = "radio-text"

    const labelEl = document.createElement("span")
    labelEl.className = "radio-label"
    labelEl.setAttribute("part", "radio-label")
    labelEl.id = `${id}-label`

    const descriptionEl = document.createElement("span")
    descriptionEl.className = "radio-description"
    descriptionEl.setAttribute("part", "radio-description")
    descriptionEl.id = `${id}-desc`

    Array.from(radioEl.childNodes).forEach((child) => {
      const isDescription =
        child.nodeType === Node.ELEMENT_NODE && child.getAttribute("slot") === "description"
      const copy = child.cloneNode(true)
      if (isDescription === true) {
        copy.removeAttribute("slot")
        descriptionEl.appendChild(copy)
      } else {
        labelEl.appendChild(copy)
      }
    })

    text.appendChild(labelEl)
    text.appendChild(descriptionEl)
    node.appendChild(text)

    if (descriptionEl.childNodes.length > 0) {
      node.setAttribute("aria-describedby", descriptionEl.id)
    }

    const labelText = labelEl.textContent.replace(/\s+/g, " ").trim()
    const disabled = radioEl.hasAttribute("disabled")
    if (disabled === true) {
      node.setAttribute("aria-disabled", "true")
    }

    const item = {
      id: id,
      /* Without a `value` attribute the label text is the value. */
      value: radioEl.hasAttribute("value") === true ? radioEl.getAttribute("value") : labelText,
      label: labelText,
      disabled: disabled,
      index: index,
      el: radioEl,
      node: node
    }
    return item
  }

  _buildRadios() {
    /* A rebuild replaces the rows; remember which radio had focus. */
    const active = this.shadowRoot.activeElement
    const activeItem = active !== null ? this._radioData[parseInt(active.dataset.index, 10)] : undefined
    const focusedEl = activeItem !== undefined ? activeItem.el : null

    const radios = this._getMjRadios()
    this._itemsEl.replaceChildren()
    this._radioData = radios.map((radioEl, index) => {
      const item = this._buildRadioNode(radioEl, index)
      this._itemsEl.appendChild(item.node)
      return item
    })

    this._syncChecked()

    const refocus = this._radioData.find((item) => item.el === focusedEl)
    if (focusedEl !== null && refocus !== undefined) {
      refocus.node.focus()
    }
    return
  }

  /* Index of the radio that carries the current value, or -1. */
  _checkedIndex() {
    const value = this._value || ""
    const index = this._radioData.findIndex((item) => item.value === value)
    return index
  }

  /*
   * Mark the checked radio and place the group's single tab stop: on the
   * checked radio when it is enabled, otherwise on the first enabled radio,
   * so the group is always reachable. A disabled group has no tab stop.
   */
  _syncChecked() {
    if (this._itemsEl === undefined || this._itemsEl === null) {
      return
    }

    const checkedIndex = this._checkedIndex()
    this._radioData.forEach((item) => {
      item.node.setAttribute("aria-checked", item.index === checkedIndex ? "true" : "false")
    })

    let tabStop = -1
    if (this._isDisabled() === false) {
      if (checkedIndex >= 0 && this._radioData[checkedIndex].disabled !== true) {
        tabStop = checkedIndex
      } else {
        tabStop = this._radioData.findIndex((item) => item.disabled !== true)
      }
    }
    this._setTabStop(tabStop)
    return
  }

  _setTabStop(index) {
    this._radioData.forEach((item) => {
      item.node.tabIndex = item.index === index ? 0 : -1
    })
    return
  }

  /* ----- event handlers ----- */

  _itemFor(event) {
    const node = event.target instanceof Element ? event.target.closest(".radio-item") : null
    const item = node !== null ? this._radioData[parseInt(node.dataset.index, 10)] : undefined
    return item
  }

  _onRadioClick(event) {
    const item = this._itemFor(event)
    if (item === undefined || item.disabled === true) {
      return
    }
    if (this._isDisabled() === true || this.hasAttribute("readonly") === true) {
      return
    }
    this._selectIndex(item.index)
    return
  }

  /*
   * Index of the next enabled radio from `from` in direction `delta`,
   * wrapping round; -1 when no radio is enabled.
   */
  _stepEnabled(from, delta) {
    const count = this._radioData.length
    let found = -1

    for (let offset = 1; offset <= count; offset = offset + 1) {
      const index = (((from + delta * offset) % count) + count) % count
      if (this._radioData[index].disabled !== true) {
        found = index
        break
      }
    }

    return found
  }

  _onKeydown(event) {
    const item = this._itemFor(event)
    if (item === undefined || this._isDisabled() === true) {
      return
    }

    const count = this._radioData.length
    const rtl = getComputedStyle(this).direction === "rtl"
    const forwardInline = rtl === true ? "ArrowLeft" : "ArrowRight"
    const backwardInline = rtl === true ? "ArrowRight" : "ArrowLeft"

    let target = -1

    if (event.key === " ") {
      event.preventDefault()
      if (item.disabled !== true && this.hasAttribute("readonly") === false) {
        this._selectIndex(item.index)
      }
    } else if (event.key === "ArrowDown" || event.key === forwardInline) {
      event.preventDefault()
      target = this._stepEnabled(item.index, 1)
    } else if (event.key === "ArrowUp" || event.key === backwardInline) {
      event.preventDefault()
      target = this._stepEnabled(item.index, -1)
    } else if (event.key === "Home") {
      event.preventDefault()
      target = this._stepEnabled(-1, 1)
    } else if (event.key === "End") {
      event.preventDefault()
      target = this._stepEnabled(count, -1)
    }

    if (target >= 0) {
      /* Focus moves first; the radio it lands on becomes the selection. */
      this._setTabStop(target)
      this._radioData[target].node.focus()
      if (this.hasAttribute("readonly") === false) {
        this._selectIndex(target)
      }
    }
    return
  }

  /*
   * A user selection. The `value` attribute is left alone: it is the default
   * value a form reset goes back to. Choosing the radio that is already
   * checked changes nothing and reports nothing.
   */
  _selectIndex(index) {
    const item = this._radioData[index]
    if (item === undefined) {
      return
    }

    const previousValue = this._value
    if (item.value === previousValue) {
      return
    }

    this._setFormValue(item.value)
    this._syncChecked()

    this.emit("mj-change", {
      value: item.value,
      previousValue: previousValue,
      radio: item.el
    })
    return
  }

  /* ----- accessibility ----- */

  _setGroupAria(name, on) {
    if (on === true) {
      this._group.setAttribute(name, "true")
    } else {
      this._group.removeAttribute(name)
    }
    return
  }

  /* One place that mirrors the host state onto the role="radiogroup" element. */
  _syncAccessibility() {
    if (this._group === undefined || this._group === null) {
      return
    }

    const invalid = this.hasAttribute("invalid") || this._isUserInvalid() === true
    this._setGroupAria("aria-invalid", invalid)
    this._setGroupAria("aria-required", this.hasAttribute("required"))
    this._setGroupAria("aria-readonly", this.hasAttribute("readonly"))
    this._setGroupAria("aria-disabled", this._isDisabled())

    /* Named by the `label` / `aria-label` attribute, else by the label slot. */
    const name = this.getAttribute("label") || this.getAttribute("aria-label") || ""
    if (name.length > 0) {
      this._group.setAttribute("aria-label", name)
      this._group.removeAttribute("aria-labelledby")
    } else {
      this._group.removeAttribute("aria-label")
      this._group.setAttribute("aria-labelledby", this._labelId)
    }

    /* The error text only describes the group while it is shown. */
    const describedBy = invalid === true ? `${this._helpId} ${this._errorId}` : this._helpId
    this._group.setAttribute("aria-describedby", describedBy)
    return
  }

  /*
   * FormControlMixin hooks: after a failed validation (an mj-form submit) the
   * error region shows the validation message, unless the page slotted its
   * own error text, until the group is valid again.
   */
  onInvalid(message) {
    this._renderValidationError(message)
    return
  }

  onValidityRestored() {
    this._renderValidationError("")
    return
  }

  _renderValidationError(message) {
    if (this._group === undefined || this._group === null) {
      return
    }
    const errorEl = this.$(".error")
    const textEl = this.$(".error-text")
    textEl.textContent = message
    if (message.length > 0) {
      errorEl.setAttribute("data-visible", "")
    } else {
      errorEl.removeAttribute("data-visible")
    }
    this._syncAccessibility()
    return
  }

  _validationAnchor() {
    let anchor = null
    if (this._itemsEl !== undefined && this._itemsEl !== null) {
      anchor = this._itemsEl.querySelector(".radio-item[tabindex='0']") || this._itemsEl.querySelector(".radio-item")
    }
    return anchor
  }

  /* ----- form callbacks ----- */

  /* The base class has already restored the form value; show it. */
  onFormReset(initial) {
    this._syncChecked()
    return
  }

  onFormRestore(state) {
    this._syncChecked()
    return
  }

  /* An ancestor <fieldset disabled> was switched on or off. */
  onFormDisabled(disabled) {
    this._formDisabled = disabled === true
    this._syncAccessibility()
    this._syncChecked()
    return
  }

  /* ----- scriptable API ----- */

  /*
   * Assigning `value` moves the checked radio as well as the submitted form
   * value. The `value` attribute keeps the default for form reset.
   */
  get value() {
    return this._value
  }

  set value(next) {
    const normalized = next === null || next === undefined ? "" : String(next)
    this._setFormValue(normalized)
    this._syncChecked()
    return
  }

  get radios() {
    return this._getMjRadios()
  }

  get selectedRadio() {
    const index = this._checkedIndex()
    const radio = index >= 0 ? this._radioData[index].el : null
    return radio
  }

  focus() {
    const stop = this._itemsEl !== undefined ? this._itemsEl.querySelector("[tabindex='0']") : null
    if (stop !== null) {
      stop.focus()
    }
    return
  }
}
