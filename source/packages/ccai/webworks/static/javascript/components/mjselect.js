/*
 * mjselect.js
 *
 * <mj-select> — single-choice dropdown with rich option content, keyboard
 * navigation, and full form participation via ElementInternals.
 *
 * Options are the <mj-option> descendants of the host. A MutationObserver
 * keeps the listbox in step with them, so options added, removed, or
 * relabelled after the first render (for example once an async fetch
 * resolves) show up without the consumer re-creating the element.
 *
 * The combobox trigger takes its accessible name from the host `label`
 * attribute, the host `aria-label` / `aria-labelledby`, or an associated
 * <label> element, in that order, through `aria-labelledby` on a label
 * element inside the shadow root.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { autoPosition } from "../core/overlay.js";
import { announce } from "../core/announcer.js";
import { t } from "../core/intl.js";

const STYLES = `
:host {
  display: inline-block;
  position: relative;
  vertical-align: middle;
}
:host([block]) { display: block; }

.trigger {
  display: inline-flex;
  align-items: center;
  gap: var(--mj-space-2);
  min-height: var(--mj-control-height-md);
  min-width: var(--mj-target-min);
  width: 100%;
  padding: 0 var(--mj-space-3);
  font: inherit;
  font-size: var(--mj-font-size-md);
  color: var(--mj-text);
  background: var(--mj-surface);
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-select-border-radius, var(--mj-radius-md));
  cursor: pointer;
  user-select: none;
  transition: border-color var(--mj-motion-fast) var(--mj-motion-ease);
  text-align: start;
}
.trigger:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.trigger:hover:not([disabled]) { border-color: var(--mj-accent); }

:host([size="sm"]) .trigger { min-height: var(--mj-control-height-sm); font-size: var(--mj-font-size-sm); }
:host([size="lg"]) .trigger { min-height: var(--mj-control-height-lg); font-size: var(--mj-font-size-lg); }

.label { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.placeholder { color: var(--mj-text-muted); }
.chevron {
  width: 1em; height: 1em; flex-shrink: 0;
  transition: transform var(--mj-motion-fast) var(--mj-motion-ease);
}
:host([open]) .chevron { transform: rotate(180deg); }

:host([disabled]) .trigger { opacity: 0.55; cursor: not-allowed; }
:host([invalid]) .trigger { border-color: var(--mj-color-danger); }
:host([readonly]) .trigger { cursor: default; }

.popup {
  position: fixed;
  background: var(--mj-surface-raised, var(--mj-surface));
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-select-border-radius, var(--mj-radius-md));
  box-shadow: var(--mj-elevation-2);
  min-width: var(--mj-select-popup-min-width, 0);
  max-height: var(--mj-select-popup-max-height, 18rem);
  overflow-y: auto;
  z-index: var(--mj-layer-popover);
  display: none;
}
:host([open]) .popup { display: block; }

.listbox { padding: var(--mj-space-1) 0; }

.option {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  padding: var(--mj-select-option-padding, var(--mj-space-2) var(--mj-space-3));
  cursor: pointer;
  user-select: none;
  font-size: var(--mj-font-size-md);
  color: var(--mj-text);
}
.option:hover { background: var(--mj-bg-muted); }
.option[aria-selected="true"] { background: var(--mj-bg-subtle); font-weight: var(--mj-font-weight-medium); }
.option[aria-disabled="true"] { opacity: 0.45; cursor: not-allowed; }
.option.focused { background: var(--mj-bg-muted); outline: none; }

.optgroup-label {
  padding: var(--mj-space-1) var(--mj-space-3);
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text-muted);
  font-weight: var(--mj-font-weight-medium);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.no-results {
  padding: var(--mj-space-3);
  color: var(--mj-text-muted);
  text-align: center;
  font-size: var(--mj-font-size-sm);
}
.check { width: 1em; height: 1em; flex-shrink: 0; opacity: 0; }
.option[aria-selected="true"] .check { opacity: 1; }
`;

const CHECK_ICON_MARKUP =
  '<svg class="check" aria-hidden="true" viewBox="0 0 16 16" fill="currentColor"><path d="M13.5 3.5 6 11 2.5 7.5l1-1L6 9 12.5 2.5z"/></svg>'

/*
 * Option attributes whose changes alter what the listbox shows. Changes to
 * other attributes (and to the host's own attributes, which the component
 * observes through attributeChangedCallback) do not trigger a rebuild.
 */
const OPTION_ATTRIBUTES = ["value", "disabled", "label"]

/*
 * Text content of `node` with the subtree of `skip` left out, whitespace
 * collapsed. Used to read a wrapping <label> without the select's own
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

export class MjSelect extends FormControlMixin(MjElement) {
  static tagName = "mj-select";
  static styles = STYLES;
  static watched = [
    "value", "open", "disabled", "readonly", "invalid", "placeholder", "size",
    "label", "aria-label", "aria-labelledby"
  ];

  constructor() {
    super()
    this._initFormControl()
    this._focusedIndex = -1
    this._typeahead = ""
    this._typeaheadTimer = null
    this._disposePosition = null
    this._optionData = []
    this._listboxId = nextId("mj-select-lb")
    this._triggerId = nextId("mj-select-tr")
    this._labelId = nextId("mj-select-lbl")
  }

  render() {
    const markup = `
      <span class="mj-visually-hidden" id="${this._labelId}" hidden></span>
      <button
        class="trigger"
        part="trigger"
        id="${this._triggerId}"
        role="combobox"
        aria-haspopup="listbox"
        aria-expanded="false"
        aria-controls="${this._listboxId}"
        type="button"
      >
        <span class="label" part="selected-label"></span>
        <svg class="chevron" part="chevron" aria-hidden="true" viewBox="0 0 16 16" fill="currentColor">
          <path d="M8 10.5 3 5.5h10z"/>
        </svg>
      </button>
      <div class="popup" part="popup">
        <div
          class="listbox"
          part="listbox"
          id="${this._listboxId}"
          role="listbox"
          tabindex="-1"
        ></div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._trigger = this.$(".trigger")
    this._popup = this.$(".popup")
    this._listbox = this.$(".listbox")
    this._nameEl = this.$(`#${this._labelId}`)

    this.listen(this._trigger, "click", this._onTriggerClick.bind(this))
    this.listen(this._trigger, "keydown", this._onKeydown.bind(this))
    this.listen(this._trigger, "focus", this._syncAccessibleName.bind(this))
    this.listen(this._listbox, "click", this._onOptionClick.bind(this))
    this.listen(this._listbox, "mouseover", this._onOptionHover.bind(this))
    this.listen(this, "click", this._onHostClick.bind(this))
    this.listen(document, "click", this._onDocClick.bind(this))

    this._observeOptions()
    this._buildOptions()
    this._syncTriggerLabel()
    this._syncAccessibleName()
    this._syncAccessibility()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "value") {
      this._setFormValue(newValue || "")
      this._syncTriggerLabel()
      this._updateOptionSelected()
    }
    if (name === "open" && this._trigger !== undefined) {
      this._syncOpen()
    }
    if (name === "disabled" || name === "readonly" || name === "invalid") {
      this._syncAccessibility()
    }
    if (name === "placeholder") {
      this._syncTriggerLabel()
    }
    if (name === "label" || name === "aria-label" || name === "aria-labelledby") {
      this._syncAccessibleName()
    }
    return
  }

  /* ----- option building ----- */

  _getOptionEls() {
    const els = Array.from(this.querySelectorAll("mj-option"))
    return els
  }

  /*
   * Rebuild the listbox whenever the <mj-option> children change. Mutation
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
    if (relevant === false || this._listbox === undefined) {
      return
    }
    this._buildOptions()
    this._syncTriggerLabel()
    if (this.hasAttribute("open") === true) {
      const current = this._currentOptionIndex()
      this._moveFocus(current >= 0 ? current : 0)
    }
    return
  }

  _buildOptions() {
    const optionEls = this._getOptionEls()
    this._listbox.replaceChildren()
    this._optionData = []

    if (optionEls.length === 0) {
      const empty = document.createElement("div")
      empty.className = "no-results"
      empty.setAttribute("part", "no-results")
      const slot = document.createElement("slot")
      slot.name = "no-results"
      slot.textContent = t("mj.select.noOptions")
      empty.appendChild(slot)
      this._listbox.appendChild(empty)
      return
    }

    optionEls.forEach((opt, idx) => {
      const item = {
        id: nextId("mj-opt"),
        value: opt.getAttribute("value") || "",
        label: opt.getAttribute("label") || opt.textContent.trim(),
        disabled: opt.hasAttribute("disabled"),
        index: idx
      }
      opt._mjId = item.id
      this._optionData.push(item)

      // Built with DOM APIs, never markup: option labels are often
      // user-supplied data (project names, integration names).
      const node = document.createElement("div")
      node.className = "option"
      node.setAttribute("part", "option")
      node.setAttribute("role", "option")
      node.id = item.id
      node.dataset.value = item.value
      node.dataset.index = String(item.index)
      node.setAttribute("aria-selected", item.value === this._value ? "true" : "false")
      if (item.disabled === true) {
        node.setAttribute("aria-disabled", "true")
      }
      node.innerHTML = CHECK_ICON_MARKUP
      const labelEl = document.createElement("span")
      labelEl.className = "option-label"
      labelEl.setAttribute("part", "option-label")
      labelEl.textContent = item.label
      node.appendChild(labelEl)
      this._listbox.appendChild(node)
    })
    return
  }

  _syncTriggerLabel() {
    if (this._trigger === undefined) {
      return
    }
    const labelEl = this._trigger.querySelector(".label")
    if (labelEl === null) {
      return
    }
    const val = this._value || ""
    const data = this._optionData || []
    const match = data.find((d) => d.value === val)
    if (match !== undefined) {
      labelEl.textContent = match.label
      labelEl.classList.remove("placeholder")
    } else {
      const ph = this.getAttribute("placeholder") || ""
      labelEl.textContent = ph
      labelEl.classList.add("placeholder")
    }
    return
  }

  _updateOptionSelected() {
    if (this._listbox === undefined) {
      return
    }
    const opts = this._listbox.querySelectorAll(".option")
    opts.forEach((opt) => {
      const selected = opt.dataset.value === this._value
      opt.setAttribute("aria-selected", selected === true ? "true" : "false")
    })
    return
  }

  /* ----- accessible name ----- */

  /*
   * The text that names the combobox: the `label` attribute, then the host's
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

  _syncAccessibleName() {
    if (this._trigger === undefined || this._nameEl === null) {
      return
    }
    const name = this._computeAccessibleName()
    if (name.length > 0) {
      this._nameEl.textContent = name
      this._trigger.setAttribute("aria-labelledby", this._labelId)
      this._listbox.setAttribute("aria-labelledby", this._labelId)
    } else {
      this._nameEl.textContent = ""
      this._trigger.removeAttribute("aria-labelledby")
      this._listbox.removeAttribute("aria-labelledby")
    }
    return
  }

  /* ----- open/close ----- */

  _syncOpen() {
    const isOpen = this.hasAttribute("open")
    this._trigger.setAttribute("aria-expanded", isOpen === true ? "true" : "false")

    if (isOpen === true) {
      this._popup.style.minWidth = `${this._trigger.offsetWidth}px`
      this._disposePosition = autoPosition(this._popup, this._trigger, {
        placement: "bottom-start"
      })
      this._focusedIndex = this._currentOptionIndex()
      this._moveFocus(this._focusedIndex >= 0 ? this._focusedIndex : 0)
    } else {
      if (this._disposePosition !== null) {
        this._disposePosition()
        this._disposePosition = null
      }
      this._clearFocus()
    }
    return
  }

  _open() {
    if (this.hasAttribute("disabled") || this.hasAttribute("readonly")) {
      return
    }
    const proceed = this.emit("mj-open", {}, { cancelable: true })
    if (proceed === false) {
      return
    }
    this.setAttribute("open", "")
    return
  }

  _close() {
    if (this.hasAttribute("open") === false) {
      return
    }
    this.removeAttribute("open")
    this.emit("mj-close", {})
    this._trigger.focus()
    return
  }

  _currentOptionIndex() {
    const data = this._optionData || []
    const idx = data.findIndex((d) => d.value === this._value && d.disabled !== true)
    return idx
  }

  _moveFocus(index) {
    const opts = this._listbox.querySelectorAll(".option")
    opts.forEach((el) => el.classList.remove("focused"))
    if (index < 0 || index >= opts.length) {
      this._trigger.removeAttribute("aria-activedescendant")
      this._focusedIndex = -1
      return
    }
    this._focusedIndex = index
    const focused = opts[index]
    focused.classList.add("focused")
    focused.scrollIntoView({ block: "nearest" })
    this._trigger.setAttribute("aria-activedescendant", focused.id)
    return
  }

  _clearFocus() {
    const opts = this._listbox.querySelectorAll(".option")
    opts.forEach((el) => el.classList.remove("focused"))
    this._trigger.removeAttribute("aria-activedescendant")
    this._focusedIndex = -1
    return
  }

  /* ----- event handlers ----- */

  _onTriggerClick() {
    if (this.hasAttribute("open")) {
      this._close()
    } else {
      this._open()
    }
    return
  }

  /*
   * A click aimed at the host itself (not at the trigger inside it) is what
   * an associated <label> dispatches when it is clicked: move focus to the
   * combobox the way a native control would.
   */
  _onHostClick(event) {
    const origin = event.composedPath()[0]
    if (origin === this && this._trigger !== undefined) {
      this._trigger.focus()
    }
    return
  }

  _optionNodeFor(event) {
    const target = event.target instanceof Element ? event.target.closest(".option") : null
    return target
  }

  _onOptionClick(event) {
    const node = this._optionNodeFor(event)
    if (node === null || node.getAttribute("aria-disabled") === "true") {
      return
    }
    this._selectValue(node.dataset.value)
    return
  }

  _onOptionHover(event) {
    const node = this._optionNodeFor(event)
    if (node === null) {
      return
    }
    const index = parseInt(node.dataset.index, 10)
    if (index !== this._focusedIndex) {
      this._moveFocus(index)
    }
    return
  }

  _onDocClick(event) {
    if (this.hasAttribute("open") === false) {
      return
    }
    const inside = event.composedPath().includes(this)
    if (inside === false) {
      this._close()
    }
    return
  }

  _onKeydown(event) {
    const isOpen = this.hasAttribute("open")

    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      if (isOpen === false) {
        this._open()
      } else {
        const focused = this._listbox.querySelector(".option.focused")
        if (focused !== null && focused.getAttribute("aria-disabled") !== "true") {
          this._selectValue(focused.dataset.value)
        }
      }
    } else if (event.key === "Escape") {
      if (isOpen === true) {
        event.preventDefault()
        this._close()
      }
    } else if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault()
      if (isOpen === false) {
        this._open()
        return
      }
      const delta = event.key === "ArrowDown" ? 1 : -1
      const allOpts = Array.from(this._listbox.querySelectorAll(".option"))
      const current = this._focusedIndex >= 0 ? this._focusedIndex : -1
      let next = current + delta
      while (next >= 0 && next < allOpts.length) {
        if (allOpts[next].getAttribute("aria-disabled") !== "true") {
          break
        }
        next = next + delta
      }
      if (next >= 0 && next < allOpts.length) {
        this._moveFocus(next)
      }
    } else if (event.key === "Home") {
      event.preventDefault()
      if (isOpen === true) {
        this._moveFocus(0)
      }
    } else if (event.key === "End") {
      event.preventDefault()
      if (isOpen === true) {
        const allOpts = this._listbox.querySelectorAll(".option")
        this._moveFocus(allOpts.length - 1)
      }
    } else if (event.key === "Tab") {
      if (isOpen === true) {
        this._close()
      }
    } else if (event.key.length === 1) {
      if (isOpen === true) {
        this._typeaheadMatch(event.key)
      }
    }
    return
  }

  _typeaheadMatch(char) {
    clearTimeout(this._typeaheadTimer)
    this._typeahead = this._typeahead + char.toLowerCase()
    this._typeaheadTimer = setTimeout(() => {
      this._typeahead = ""
    }, 500)

    const allOpts = Array.from(this._listbox.querySelectorAll(".option"))
    const match = allOpts.find((el) => {
      const label = el.querySelector(".option-label")
      const text = label !== null ? label.textContent.toLowerCase() : ""
      return text.startsWith(this._typeahead) && el.getAttribute("aria-disabled") !== "true"
    })
    if (match !== null && match !== undefined) {
      const index = parseInt(match.dataset.index, 10)
      this._moveFocus(index)
    }
    return
  }

  _selectValue(newValue) {
    const previousValue = this._value
    this._setFormValue(newValue)
    this.setAttribute("value", newValue)
    this._syncTriggerLabel()
    this._updateOptionSelected()
    this.emit("mj-change", { value: newValue, previousValue: previousValue })
    this._close()
    return
  }

  /* ----- accessibility ----- */

  _syncAccessibility() {
    if (this._trigger === undefined) {
      return
    }
    const disabled = this.hasAttribute("disabled")
    this._trigger.disabled = disabled
    const readonly = this.hasAttribute("readonly")
    if (readonly === true) {
      this._trigger.setAttribute("aria-readonly", "true")
    } else {
      this._trigger.removeAttribute("aria-readonly")
    }
    const invalid = this.hasAttribute("invalid")
    if (invalid === true) {
      this._trigger.setAttribute("aria-invalid", "true")
    } else {
      this._trigger.removeAttribute("aria-invalid")
    }
    return
  }

  _validationAnchor() {
    return this._trigger || this
  }

  /* ----- scriptable API ----- */

  /*
   * Assigning `value` updates the trigger text and the selected option, not
   * only the submitted form value -- including when the matching option only
   * arrives later.
   */
  get value() {
    return this._value
  }

  set value(next) {
    const normalized = next === null || next === undefined ? "" : String(next)
    this._setFormValue(normalized)
    this._syncTriggerLabel()
    this._updateOptionSelected()
    return
  }

  get open() {
    return this.hasAttribute("open")
  }

  set open(value) {
    if (value === true) {
      this._open()
    } else {
      this._close()
    }
    return
  }

  get disabled() {
    return this.hasAttribute("disabled")
  }

  set disabled(value) {
    this.reflectBoolean("disabled", value === true)
    return
  }

  focus() {
    if (this._trigger !== undefined) {
      this._trigger.focus()
    }
    return
  }
}
