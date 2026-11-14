/*
 * mjcheckboxgroup.js
 *
 * <mj-checkbox-group> — labeled group of independent boolean choices with
 * optional tri-state "select all" parent checkbox and form participation.
 *
 * Checkboxes are the <mj-checkbox> descendants of the host. Each one is
 * rendered as a role="checkbox" row whose label is a copy of the checkbox's
 * own nodes and whose description is a copy of its `slot="description"`
 * children. A MutationObserver keeps the rows in step with the
 * <mj-checkbox> elements.
 *
 * The `value` attribute is the default (a comma-separated list, restored by
 * a form reset); the live state is `_checkedValues`, which survives a move
 * in the DOM and is what the `value` property reads and writes.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { t } from "../core/intl.js";

const STYLES = `
:host { display: block; }

.group {
  display: flex;
  flex-direction: column;
  gap: var(--mj-checkbox-group-gap, var(--mj-space-2));
}

.checkbox-items {
  display: flex;
  flex-direction: column;
  gap: var(--mj-checkbox-group-gap, var(--mj-space-2));
}
:host([orientation="horizontal"]) .checkbox-items {
  flex-direction: row;
  flex-wrap: wrap;
  gap: var(--mj-checkbox-group-gap, var(--mj-space-2) var(--mj-space-4));
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

.checkbox-item {
  display: flex;
  align-items: center;
  gap: var(--mj-checkbox-label-gap, var(--mj-space-2));
  cursor: pointer;
  min-height: var(--mj-target-min);
  outline: none;
}
.checkbox-item[aria-disabled="true"] { opacity: 0.45; cursor: not-allowed; }

.checkbox-control {
  flex-shrink: 0;
  width: var(--mj-checkbox-size, 1rem);
  height: var(--mj-checkbox-size, 1rem);
  border: 2px solid var(--mj-checkbox-border-color, var(--mj-border-strong));
  border-radius: var(--mj-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--mj-surface);
  transition: background var(--mj-motion-fast), border-color var(--mj-motion-fast);
  outline: none;
}
.checkbox-item:focus-visible .checkbox-control {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.checkbox-item[aria-checked="true"] .checkbox-control {
  background: var(--mj-checkbox-color, var(--mj-accent));
  border-color: var(--mj-checkbox-color, var(--mj-accent));
}
.checkbox-item[aria-checked="mixed"] .checkbox-control {
  background: var(--mj-checkbox-indeterminate-color, var(--mj-accent));
  border-color: var(--mj-checkbox-indeterminate-color, var(--mj-accent));
}

.check-icon, .mixed-icon {
  width: 0.75em; height: 0.75em;
  color: var(--mj-text-on-accent);
  display: none;
}
.checkbox-item[aria-checked="true"] .check-icon { display: block; }
.checkbox-item[aria-checked="mixed"] .mixed-icon { display: block; }

.checkbox-text { display: flex; flex-direction: column; gap: 2px; flex: 1; }
.checkbox-label { color: var(--mj-text); }
.checkbox-description { font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }
.checkbox-description:empty { display: none; }

.select-all-wrapper {
  padding-bottom: var(--mj-space-2);
  border-bottom: 1px solid var(--mj-border);
  margin-bottom: var(--mj-space-1);
}
:host(:not([select-all])) .select-all-wrapper { display: none; }

.group[aria-disabled="true"] .checkbox-item { opacity: 0.45; cursor: not-allowed; pointer-events: none; }
:host([invalid]) .group { outline: 2px solid var(--mj-color-danger); border-radius: var(--mj-radius-md); padding: var(--mj-space-1); }
`;

/* The box of a checkbox row: static markup, no interpolated values. */
const CONTROL_MARKUP = `
  <svg class="check-icon" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
    <path d="M13.5 3.5 6 11 2.5 7.5l1-1L6 9 12.5 2.5z"/>
  </svg>
  <svg class="mixed-icon" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
    <path d="M3 8h10v1.5H3z"/>
  </svg>
`

/* <mj-checkbox> attributes whose changes alter what a row shows. */
const CHECKBOX_ATTRIBUTES = ["value", "disabled", "slot"]

/*
 * Build an empty role="checkbox" row: the box plus a label and a description
 * container the caller fills with text or copied nodes.
 */
function buildCheckboxRow(id) {
  const node = document.createElement("div")
  node.className = "checkbox-item"
  node.setAttribute("part", "checkbox")
  node.setAttribute("role", "checkbox")
  node.id = id
  node.setAttribute("aria-checked", "false")
  node.setAttribute("aria-labelledby", `${id}-label`)
  node.tabIndex = 0

  const control = document.createElement("span")
  control.className = "checkbox-control"
  control.setAttribute("part", "checkbox-input")
  control.setAttribute("aria-hidden", "true")
  control.innerHTML = CONTROL_MARKUP
  node.appendChild(control)

  const text = document.createElement("span")
  text.className = "checkbox-text"

  const labelEl = document.createElement("span")
  labelEl.className = "checkbox-label"
  labelEl.setAttribute("part", "checkbox-label")
  labelEl.id = `${id}-label`
  text.appendChild(labelEl)

  const descriptionEl = document.createElement("span")
  descriptionEl.className = "checkbox-description"
  descriptionEl.setAttribute("part", "checkbox-description")
  descriptionEl.id = `${id}-desc`
  text.appendChild(descriptionEl)

  node.appendChild(text)

  const row = { node: node, labelEl: labelEl, descriptionEl: descriptionEl }
  return row
}

export class MjCheckboxGroup extends FormControlMixin(MjElement) {
  static tagName = "mj-checkbox-group";
  static styles = STYLES;
  static watched = [
    "value", "disabled", "readonly", "required", "invalid", "select-all", "select-all-label",
    "orientation", "label", "aria-label"
  ];

  constructor() {
    super()
    this._initFormControl()
    this._checkedValues = new Set()
    this._checkboxData = []

    /* True while an ancestor <fieldset disabled> disables the control. */
    this._formDisabled = false

    /* The `value` attribute change applied before the first render, if any. */
    this._preRenderValue = null

    this._groupId = nextId("mj-cg")
    this._labelId = nextId("mj-cg-label")
    this._helpId = nextId("mj-cg-help")
    this._errorId = nextId("mj-cg-err")
  }

  render() {
    const markup = `
      <div
        class="group"
        part="group"
        role="group"
      >
        <span class="group-label" part="group-label" id="${this._labelId}"><slot name="label"></slot></span>
        <div class="select-all-wrapper" part="select-all"></div>
        <div class="checkbox-items" part="checkboxes"></div>
        <span class="help" part="help" id="${this._helpId}"><slot name="help"></slot></span>
        <span class="error" part="error" id="${this._errorId}" role="alert"><slot name="error"><span class="error-text"></span></slot></span>
      </div>
    `
    return markup
  }

  afterRender() {
    this._group = this.$(".group")
    this._itemsEl = this.$(".checkbox-items")

    const selectAllRow = buildCheckboxRow(nextId("mj-sa"))
    selectAllRow.node.classList.add("select-all")
    this._selectAllEl = selectAllRow.node
    this._selectAllLabelEl = selectAllRow.labelEl
    this._selectAllWrapper = this.$(".select-all-wrapper")

    /* One delegated pair of listeners serves the select-all and every row. */
    this.listen(this._group, "click", this._onClick.bind(this))
    this.listen(this._group, "keydown", this._onKeydown.bind(this))

    this._observeCheckboxes()
    this._syncSelectAllLabel()
    this._syncSelectAllPresence()
    this._buildCheckboxes()
    this._syncFormValue()
    this._syncAccessibility()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "value" && this._isReplayedValue(newValue) === false) {
      this._applyValueString(newValue || "")
    }
    if (name === "select-all-label") {
      this._syncSelectAllLabel()
    }
    if (name === "select-all") {
      this._syncSelectAllPresence()
    }
    if (
      name === "invalid" || name === "disabled" || name === "readonly" || name === "required" ||
      name === "label" || name === "aria-label"
    ) {
      this._syncAccessibility()
      this._syncItems()
    }
    if (name === "required" && this._internals !== undefined) {
      this._refreshValidity()
    }
    return
  }

  /*
   * The base class delivers an attribute change that arrived before the first
   * render a second time once the shadow DOM exists. For `value` the first
   * delivery already stored the checked values, and applying it again would
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

  _canChange() {
    const allowed = this._isDisabled() === false && this.hasAttribute("readonly") === false
    return allowed
  }

  /* ----- checkbox rows ----- */

  _getMjCheckboxes() {
    return Array.from(this.querySelectorAll("mj-checkbox"))
  }

  /*
   * Rebuild the rows whenever the <mj-checkbox> children change. Mutation
   * records are delivered once per microtask checkpoint, so adding several
   * checkboxes in a loop causes a single rebuild.
   */
  _observeCheckboxes() {
    if (typeof MutationObserver !== "function") {
      return
    }
    const observer = new MutationObserver((records) => {
      const relevant = records.some((record) => {
        return record.type !== "attributes" || record.target !== this
      })
      if (relevant === true && this._itemsEl !== undefined && this._itemsEl !== null) {
        this._buildCheckboxes()
      }
    })
    observer.observe(this, {
      childList: true,
      subtree: true,
      characterData: true,
      attributes: true,
      attributeFilter: CHECKBOX_ATTRIBUTES
    })
    this.onTeardown(() => {
      observer.disconnect()
    })
    return
  }

  /*
   * Build one row per <mj-checkbox>. The label and description are copies of
   * the checkbox's own nodes (cloneNode), never markup assembled from
   * strings, so nothing is re-parsed as HTML.
   */
  _buildCheckboxes() {
    /* A rebuild replaces the rows; remember which checkbox had focus. */
    const active = this.shadowRoot.activeElement
    const activeItem = active !== null ? this._checkboxData[parseInt(active.dataset.index, 10)] : undefined
    const focusedEl = activeItem !== undefined ? activeItem.el : null

    const els = this._getMjCheckboxes()
    this._itemsEl.replaceChildren()

    this._checkboxData = els.map((el, index) => {
      const row = buildCheckboxRow(nextId("mj-cb"))
      row.node.dataset.index = String(index)

      Array.from(el.childNodes).forEach((child) => {
        const isDescription =
          child.nodeType === Node.ELEMENT_NODE && child.getAttribute("slot") === "description"
        const copy = child.cloneNode(true)
        if (isDescription === true) {
          copy.removeAttribute("slot")
          row.descriptionEl.appendChild(copy)
        } else {
          row.labelEl.appendChild(copy)
        }
      })
      if (row.descriptionEl.childNodes.length > 0) {
        row.node.setAttribute("aria-describedby", row.descriptionEl.id)
      }

      const labelText = row.labelEl.textContent.replace(/\s+/g, " ").trim()
      const item = {
        id: row.node.id,
        /* Without a `value` attribute the label text is the value. */
        value: el.hasAttribute("value") === true ? el.getAttribute("value") : labelText,
        label: labelText,
        disabled: el.hasAttribute("disabled"),
        index: index,
        el: el,
        node: row.node
      }
      this._itemsEl.appendChild(row.node)
      return item
    })

    this._syncItems()

    const refocus = this._checkboxData.find((item) => item.el === focusedEl)
    if (focusedEl !== null && refocus !== undefined) {
      refocus.node.focus()
    }
    return
  }

  _syncSelectAllLabel() {
    if (this._selectAllLabelEl === undefined || this._selectAllLabelEl === null) {
      return
    }
    this._selectAllLabelEl.textContent = this.getAttribute("select-all-label") || t("core.selectAll")
    return
  }

  /* The select-all checkbox exists only while the `select-all` attribute is set. */
  _syncSelectAllPresence() {
    if (this._selectAllWrapper === undefined || this._selectAllWrapper === null) {
      return
    }
    const wanted = this.hasAttribute("select-all")
    const present = this._selectAllEl.parentNode === this._selectAllWrapper
    if (wanted === true && present === false) {
      this._selectAllWrapper.appendChild(this._selectAllEl)
    } else if (wanted === false && present === true) {
      this._selectAllEl.remove()
    }
    return
  }

  /*
   * Bring every row in line with the fields: checked state, disabled state
   * and tab order, then the tri-state of the select-all checkbox.
   */
  _syncItems() {
    if (this._itemsEl === undefined || this._itemsEl === null) {
      return
    }

    const groupDisabled = this._isDisabled()
    const readonly = this.hasAttribute("readonly")

    this._checkboxData.forEach((item) => {
      const checked = this._checkedValues.has(item.value)
      item.node.setAttribute("aria-checked", checked === true ? "true" : "false")
      if (item.disabled === true) {
        item.node.setAttribute("aria-disabled", "true")
      } else {
        item.node.removeAttribute("aria-disabled")
      }
      if (readonly === true) {
        item.node.setAttribute("aria-readonly", "true")
      } else {
        item.node.removeAttribute("aria-readonly")
      }
      /* Disabled checkboxes, and all of a disabled group, leave the tab order. */
      item.node.tabIndex = item.disabled === true || groupDisabled === true ? -1 : 0
    })

    this._selectAllEl.tabIndex = groupDisabled === true ? -1 : 0
    this._updateSelectAll()
    return
  }

  _updateSelectAll() {
    if (this._selectAllEl === undefined || this._selectAllEl === null) {
      return
    }
    const state = this.selectAllState
    if (state === "all") {
      this._selectAllEl.setAttribute("aria-checked", "true")
    } else if (state === "some") {
      this._selectAllEl.setAttribute("aria-checked", "mixed")
    } else {
      this._selectAllEl.setAttribute("aria-checked", "false")
    }
    return
  }

  /*
   * Replace the checked values with the comma-separated list in `text`.
   * Emits nothing -- used for the `value` attribute and property, form reset
   * and restore.
   */
  _applyValueString(text) {
    const source = text === null || text === undefined ? "" : String(text)
    this._checkedValues.clear()
    source.split(",").forEach((part) => {
      const trimmed = part.trim()
      if (trimmed.length > 0) {
        this._checkedValues.add(trimmed)
      }
    })
    this._syncFormValue()
    this._syncItems()
    return
  }

  get selectAllState() {
    const enabled = this._checkboxData.filter((d) => d.disabled !== true)
    if (enabled.length === 0) {
      return "none"
    }
    const checkedCount = enabled.filter((d) => this._checkedValues.has(d.value)).length
    if (checkedCount === 0) {
      return "none"
    }
    if (checkedCount === enabled.length) {
      return "all"
    }
    return "some"
  }

  get checkedValues() {
    return Array.from(this._checkedValues)
  }

  /* ----- event handlers ----- */

  _rowFor(event) {
    const node = event.target instanceof Element ? event.target.closest(".checkbox-item") : null
    return node
  }

  /* Toggle the row a click or key press landed on, if it may change. */
  _activateRow(node) {
    if (this._canChange() === false || node.getAttribute("aria-disabled") === "true") {
      return
    }
    if (node === this._selectAllEl) {
      this._toggleAll()
    } else {
      this._toggleIndex(parseInt(node.dataset.index, 10))
    }
    return
  }

  _onClick(event) {
    const node = this._rowFor(event)
    if (node === null) {
      return
    }
    this._activateRow(node)
    return
  }

  _onKeydown(event) {
    const node = this._rowFor(event)
    if (node === null) {
      return
    }
    if (event.key === " " || event.key === "Enter") {
      event.preventDefault()
      this._activateRow(node)
    }
    return
  }

  /*
   * Toggle one checkbox, identified by its position among the <mj-checkbox>
   * elements (two checkboxes may share a label, so text cannot identify it).
   */
  _toggleIndex(index) {
    const item = this._checkboxData[index]
    if (item === undefined || item.disabled === true) {
      return
    }

    const wasChecked = this._checkedValues.has(item.value)
    if (wasChecked === true) {
      this._checkedValues.delete(item.value)
    } else {
      this._checkedValues.add(item.value)
    }

    this._syncFormValue()
    this._syncItems()

    this.emit("mj-change", {
      value: this.value,
      checkedValues: this.checkedValues,
      changedCheckbox: item.el,
      checked: !wasChecked
    })
    return
  }

  _toggleAll() {
    const checkAll = this.selectAllState !== "all"

    this._checkboxData.forEach((item) => {
      if (item.disabled !== true) {
        if (checkAll === true) {
          this._checkedValues.add(item.value)
        } else {
          this._checkedValues.delete(item.value)
        }
      }
    })

    this._syncFormValue()
    this._syncItems()

    this.emit("mj-select-all", { checked: checkAll })
    this.emit("mj-change", {
      value: this.value,
      checkedValues: this.checkedValues,
      changedCheckbox: null,
      checked: checkAll
    })
    return
  }

  _syncFormValue() {
    const vals = Array.from(this._checkedValues)
    this._setFormValue(vals.join(","))
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

  /* One place that mirrors the host state onto the role="group" element. */
  _syncAccessibility() {
    if (this._group === undefined || this._group === null) {
      return
    }

    const invalid = this.hasAttribute("invalid") || this._isUserInvalid() === true
    this._setGroupAria("aria-invalid", invalid)
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
   * A required group with nothing checked reports valueMissing with its own
   * message ("At least one option must be selected."), or with the
   * `required-message` attribute when the page gives one. FormControlMixin
   * reports that case with the generic core.required text before any
   * component check runs, so the message is replaced here, after it.
   */
  _refreshValidity() {
    super._refreshValidity()

    const validity = this.validity
    const ownMessage = this.hasAttribute("required-message") === false
    if (validity !== null && validity.valueMissing === true && ownMessage === true) {
      const message = t("mj.checkboxGroup.selectionRequired")
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
      anchor = this._itemsEl.querySelector(".checkbox-item[tabindex='0']") || this._itemsEl.querySelector(".checkbox-item")
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
    this._syncAccessibility()
    this._syncItems()
    return
  }

  /* ----- scriptable API ----- */

  /*
   * Assigning `value` (a comma-separated list) replaces the checked values
   * and updates the rows. The `value` attribute keeps the default for form
   * reset.
   */
  get value() {
    return Array.from(this._checkedValues).join(",")
  }

  set value(next) {
    this._applyValueString(next)
    return
  }

  get checkboxes() {
    return this._getMjCheckboxes()
  }

  focus() {
    const first = this._group !== undefined && this._group !== null
      ? this._group.querySelector(".checkbox-item[tabindex='0']")
      : null
    if (first !== null) {
      first.focus()
    }
    return
  }
}
