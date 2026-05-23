/*
 * mjform.js
 *
 * <mj-form> -- wraps a native <form> to coordinate submission across all
 * form-associated child controls, aggregate validity, trigger field-level and
 * summary-level validation reporting, and emit structured events. It is the
 * authoritative submission orchestrator for its subtree.
 */

import { MjElement } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";

const STYLES = `
:host {
  display: block;
}

.form {
  display: flex;
  flex-direction: column;
  gap: var(--mj-form-gap, var(--mj-space-4));
  max-width: var(--mj-form-max-width, none);
}

.status {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0 0 0 0);
  clip-path: inset(50%);
  white-space: nowrap;
}
`;

export class MjForm extends MjElement {
  static tagName = "mj-form";
  static styles = STYLES;
  static watched = ["action", "method", "enctype", "novalidate", "validate", "loading", "autocomplete"];

  constructor() {
    super()
    this._submitted = false
    this._form = null
    this._statusEl = null
  }

  render() {
    const markup = `
      <form class="form" part="form">
        <slot name="summary"></slot>
        <slot></slot>
      </form>
      <span class="status" aria-live="polite" aria-atomic="true"></span>
    `
    return markup
  }

  afterRender() {
    this._form = this.$(".form")
    this._statusEl = this.$(".status")
    this._syncFormAttributes()
    this.listen(this._form, "submit", this._onNativeSubmit.bind(this))
    this.listen(this._form, "reset", this._onNativeReset.bind(this))
    this.listen(this, "mj-change", this._onChildChange.bind(this))
    this.listen(this, "mj-blur", this._onChildBlur.bind(this))
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._form === null) {
      return
    }
    this._syncFormAttributes()
    return
  }

  _syncFormAttributes() {
    const action = this.getAttribute("action") || ""
    const method = this.getAttribute("method") || "post"
    const enctype = this.getAttribute("enctype") || "application/x-www-form-urlencoded"
    const autocomplete = this.getAttribute("autocomplete") || "on"

    this._form.action = action
    this._form.method = method
    this._form.enctype = enctype
    this._form.autocomplete = autocomplete

    if (this.hasAttribute("novalidate")) {
      this._form.setAttribute("novalidate", "")
    } else {
      this._form.removeAttribute("novalidate")
    }
    return
  }

  _collectControls() {
    const controls = []
    const all = this.querySelectorAll("*")
    for (let index = 0; index < all.length; index = index + 1) {
      const el = all[index]
      const hasMjTag = el.tagName.toLowerCase().startsWith("mj-")
      const hasCheckValidity = typeof el.checkValidity === "function"
      const hasName = el.hasAttribute("name") || el.name !== undefined
      if (hasMjTag === true && hasCheckValidity === true && hasName === true) {
        controls.push(el)
      } else if ((el.tagName === "INPUT" || el.tagName === "SELECT" || el.tagName === "TEXTAREA") && el.name !== "") {
        controls.push(el)
      }
    }
    return controls
  }

  _buildFormValue() {
    const formData = new FormData(this._form)
    const value = {}
    for (const [key, val] of formData.entries()) {
      if (value[key] === undefined) {
        value[key] = []
      }
      value[key].push(val)
    }
    return { formData, value }
  }

  _onNativeSubmit(event) {
    event.preventDefault()
    this._handleSubmit()
    return
  }

  _onNativeReset(event) {
    event.preventDefault()
    const proceed = this.emit("mj-reset", {}, { cancelable: true })
    if (proceed === false) {
      return
    }
    this._submitted = false
    this._form.reset()
    const summary = this.querySelector("mj-validation-summary")
    if (summary !== null && summary !== undefined) {
      summary.errors = []
    }
    return
  }

  _onChildChange(event) {
    if (this._submitted === false) {
      return
    }
    const mode = this.getAttribute("validate") || "submit"
    if (mode !== "aggressive") {
      return
    }
    const target = event.target
    if (typeof target.reportValidity === "function") {
      target.reportValidity()
    }
    return
  }

  _onChildBlur(event) {
    if (this._submitted === false) {
      return
    }
    const mode = this.getAttribute("validate") || "submit"
    if (mode !== "eager" && mode !== "aggressive") {
      return
    }
    const target = event.target
    if (typeof target.reportValidity === "function") {
      target.reportValidity()
    }
    return
  }

  _handleSubmit() {
    if (this.hasAttribute("loading")) {
      return
    }

    this._submitted = true
    const novalidate = this.hasAttribute("novalidate")
    const controls = this._collectControls()
    const invalid = []

    if (novalidate === false) {
      for (let index = 0; index < controls.length; index = index + 1) {
        const ctrl = controls[index]
        const valid = typeof ctrl.checkValidity === "function" ? ctrl.checkValidity() : true
        if (valid === false) {
          invalid.push(ctrl)
        }
      }
    }

    if (invalid.length > 0) {
      const summary = invalid.map((ctrl) => {
        const msg = ctrl.validationMessage || ""
        const name = ctrl.getAttribute("name") || ctrl.name || ""
        return { name, message: msg }
      })
      this.emit("mj-invalid", { controls: invalid, summary })
      const summaryEl = this.querySelector("mj-validation-summary")
      if (summaryEl !== null && summaryEl !== undefined) {
        const errors = invalid.map((ctrl) => {
          const controlId = ctrl.id || ctrl.getAttribute("name") || ""
          const labelEl = this.querySelector(`mj-label[for="${controlId}"]`)
          const label = labelEl !== null ? labelEl.textContent.trim() : controlId
          const message = ctrl.validationMessage || ""
          return { controlId, label, message }
        })
        summaryEl.errors = errors
      }
      if (invalid.length > 0 && typeof invalid[0].focus === "function") {
        invalid[0].focus()
      }
      return
    }

    const { formData, value } = this._buildFormValue()
    const valid = true

    const proceed = this.emit("mj-submit", { formData, value, valid }, { cancelable: true })
    if (proceed === false) {
      return
    }

    const submittingLabel = this.getAttribute("submitting-label") || "Submitting…"
    if (this._statusEl !== null) {
      this._statusEl.textContent = submittingLabel
    }

    const action = this.getAttribute("action")
    if (action !== null && action !== "") {
      this._form.submit()
    }
    return
  }

  /* ----- scriptable API ----- */

  get elements() {
    const coll = this._form !== null ? this._form.elements : null
    return coll
  }

  get valid() {
    const controls = this._collectControls()
    for (let index = 0; index < controls.length; index = index + 1) {
      const ctrl = controls[index]
      const ok = typeof ctrl.checkValidity === "function" ? ctrl.checkValidity() : true
      if (ok === false) {
        return false
      }
    }
    return true
  }

  get value() {
    const { value } = this._buildFormValue()
    return value
  }

  get loading() {
    return this.hasAttribute("loading")
  }

  set loading(val) {
    this.reflectBoolean("loading", val === true)
    if (val === false && this._statusEl !== null) {
      this._statusEl.textContent = ""
    }
    return
  }

  submit() {
    this._handleSubmit()
    return
  }

  reset() {
    this._onNativeReset(new Event("reset"))
    return
  }
}
