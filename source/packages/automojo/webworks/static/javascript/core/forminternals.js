/*
 * forminternals.js
 *
 * FormControlMixin -- a mixin applied to input-like components so they become
 * form-associated custom elements via ElementInternals. It contributes a
 * value to FormData, supports `name`/`disabled`/`required`, participates in
 * constraint validation, and restores on form reset.
 *
 * Usage:
 *   export class MjTextField extends FormControlMixin(MjElement) { ... }
 *   ...then call `this._initFormControl()` in the constructor and
 *   `this._setFormValue(value)` whenever the value changes.
 */

export function FormControlMixin(Base) {
  class FormControl extends Base {
    static formAssociated = true;

    _initFormControl() {
      if (typeof this.attachInternals === "function") {
        this._internals = this.attachInternals()
      } else {
        this._internals = null
      }
      this._value = ""
      return
    }

    /* Reflect the current value into the owning form. */
    _setFormValue(value) {
      this._value = value
      if (this._internals !== null) {
        this._internals.setFormValue(value)
      }
      this._refreshValidity()
      return
    }

    get value() {
      return this._value
    }

    set value(next) {
      this._setFormValue(next)
      return
    }

    get form() {
      const owner = this._internals !== null ? this._internals.form : null
      return owner
    }

    get validity() {
      const state = this._internals !== null ? this._internals.validity : null
      return state
    }

    get validationMessage() {
      const message = this._internals !== null ? this._internals.validationMessage : ""
      return message
    }

    /*
     * Re-evaluate built-in constraints. Components override `_customValidity`
     * to return either an empty string (valid) or a localized message.
     */
    _refreshValidity() {
      if (this._internals === null) {
        return
      }

      const required = this.hasAttribute("required")
      const isEmpty = this._value === "" || this._value === null || this._value === undefined

      let message = ""
      let flags = {}
      let anchor = this._validationAnchor()

      if (required === true && isEmpty === true) {
        flags = { valueMissing: true }
        message = this.getAttribute("required-message") || "This field is required."
      } else {
        const custom = this._customValidity()
        if (custom !== "" && custom !== null && custom !== undefined) {
          flags = { customError: true }
          message = custom
        }
      }

      if (message === "") {
        this._internals.setValidity({})
      } else {
        this._internals.setValidity(flags, message, anchor)
      }
      return
    }

    /* Components override to supply the focusable element for validation UI. */
    _validationAnchor() {
      return this
    }

    /* Components override to add component-specific validation. */
    _customValidity() {
      return ""
    }

    checkValidity() {
      const valid = this._internals !== null ? this._internals.checkValidity() : true
      return valid
    }

    reportValidity() {
      const valid = this._internals !== null ? this._internals.reportValidity() : true
      return valid
    }

    /* Called by the form on reset -- components override to clear UI. */
    formResetCallback() {
      const initial = this.getAttribute("value") || ""
      this._setFormValue(initial)
      this.onFormReset(initial)
      return
    }

    /* Called when the form state is restored (bfcache / autofill). */
    formStateRestoreCallback(state) {
      this._setFormValue(state)
      this.onFormRestore(state)
      return
    }

    formDisabledCallback(disabled) {
      this.onFormDisabled(disabled)
      return
    }

    onFormReset(initial) { return }
    onFormRestore(state) { return }
    onFormDisabled(disabled) { return }
  }

  return FormControl
}
