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
 *
 * Showing errors: a failed `checkValidity()` / `reportValidity()` (for
 * example an <mj-form> submit) fires the native `invalid` event on the host.
 * The mixin then marks the control as user-invalid until it is valid again:
 * `_isUserInvalid()` returns true, the `user-invalid` custom state is set
 * (style it with `:host(:state(user-invalid))`), and the hooks
 * `onInvalid(message)` / `onValidityRestored()` let the component render and
 * remove its inline error. The default hooks only set / remove
 * `aria-invalid` on the validation anchor when its role supports it.
 */

import { t } from "./intl.js";

/* Roles on which aria-invalid is a supported state (WAI-ARIA 1.2). */
const ARIA_INVALID_ROLES = [
  "application", "checkbox", "columnheader", "combobox", "gridcell", "listbox", "radiogroup",
  "rowheader", "searchbox", "slider", "spinbutton", "switch", "textbox", "tree", "treegrid"
];

function supportsAriaInvalid(element) {
  const role = element.getAttribute("role")
  let supported = false
  if (role !== null) {
    supported = ARIA_INVALID_ROLES.indexOf(role) !== -1
  } else {
    const tag = element.localName
    const type = (element.getAttribute("type") || "").toLowerCase()
    supported = tag === "textarea" || tag === "select" ||
      (tag === "input" && ["button", "submit", "reset", "image", "hidden"].indexOf(type) === -1)
  }
  return supported
}

/*
 * The <label> whose click is being dispatched right now. Clicking a label
 * makes the browser click the labelled control; for a form-associated
 * custom element that click is aimed at the host itself, which is not
 * focusable, so focus would stay where it was. The label is recorded in the
 * capture phase so the control can tell that click from any other click on
 * its host and move focus into itself, as a native control does.
 */
let labelBeingClicked = null;
let labelTrackerInstalled = false;

function installLabelTracker() {
  if (labelTrackerInstalled === true || typeof document === "undefined") {
    return
  }
  labelTrackerInstalled = true

  document.addEventListener("click", (event) => {
    const origin = event.composedPath()[0]
    const label = origin instanceof Element ? origin.closest("label") : null
    if (label !== null) {
      labelBeingClicked = label
      window.setTimeout(() => {
        if (labelBeingClicked === label) {
          labelBeingClicked = null
        }
      }, 0)
    }
  }, true)
  return
}

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

      /* True from a native `invalid` event until the control is valid again. */
      this._userInvalid = false
      this._userInvalidAnchor = null

      /*
       * The host's own event: no teardown is needed, the listener lives and
       * dies with the element, and it must work before the first render.
       */
      this.addEventListener("invalid", this._onFormControlInvalid.bind(this))

      installLabelTracker()
      this.addEventListener("click", this._onFormControlLabelClick.bind(this))
      return
    }

    /*
     * A click of one of this control's labels (see `labelBeingClicked`)
     * focuses the control when focus is not inside it already.
     */
    _onFormControlLabelClick(event) {
      const aimedAtHost = event.composedPath()[0] === this
      let fromOwnLabel = false

      if (aimedAtHost === true && labelBeingClicked !== null && this._internals !== null) {
        const labels = this._internals.labels
        fromOwnLabel = labels !== undefined && labels !== null && Array.from(labels).includes(labelBeingClicked)
      }

      if (fromOwnLabel === true && this.isDisabled === false && this.matches(":focus-within") === false) {
        this.focus()
      }
      return
    }

    /* The control failed validation where the user can see it (see header). */
    _onFormControlInvalid(event) {
      this._userInvalid = true
      this._setCustomState("user-invalid", true)
      this.onInvalid(this.validationMessage)
      return
    }

    /* True while the control shows a failed validation (see header). */
    _isUserInvalid() {
      return this._userInvalid === true
    }

    _setCustomState(name, enabled) {
      const states = this._internals !== null ? this._internals.states : undefined
      if (states !== undefined && states !== null) {
        try {
          if (enabled === true) {
            states.add(name)
          } else {
            states.delete(name)
          }
        } catch (error) {
          /* Older engines only accept the legacy "--name" form; skip it. */
        }
      }
      return
    }

    /*
     * Constraint validation has to reflect the control from the moment it
     * joins a form: an untouched `required` control is invalid, exactly as a
     * native one is. Validity is therefore computed on every connect, after
     * the component has rendered and applied its initial value.
     */
    connectedCallback() {
      super.connectedCallback()
      if (this._internals !== undefined) {
        this._refreshValidity()
      }
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
        message = this.getAttribute("required-message") || t("core.required")
      } else {
        const custom = this._customValidity()
        if (custom !== "" && custom !== null && custom !== undefined) {
          flags = { customError: true }
          message = custom
        }
      }

      if (message === "") {
        this._internals.setValidity({})
      } else if (anchor !== null && anchor !== undefined && anchor !== this) {
        this._internals.setValidity(flags, message, anchor)
      } else {
        /*
         * setValidity() accepts only a shadow-including descendant as the
         * anchor; passing the host itself throws NotFoundError.
         */
        this._internals.setValidity(flags, message)
      }

      if (this._userInvalid === true) {
        if (message === "") {
          this._userInvalid = false
          this._setCustomState("user-invalid", false)
          this.onValidityRestored()
        } else {
          /* Still invalid, possibly for another reason: refresh the shown text. */
          this.onInvalid(message)
        }
      }
      return
    }

    /*
     * Components override to supply the focusable element for validation UI.
     * The default is the first form control in the shadow DOM, or null when
     * there is none.
     */
    _validationAnchor() {
      let anchor = null
      if (this.shadowRoot !== null && this.shadowRoot !== undefined) {
        anchor = this.shadowRoot.querySelector("input, textarea, select, button, [tabindex]")
      }
      return anchor
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

    /*
     * Default error hooks: mark the validation anchor aria-invalid while the
     * control is user-invalid, when the anchor is a native field or has a
     * role that supports aria-invalid. Components with an inline error
     * element override them (and may call super).
     */
    onInvalid(message) {
      const anchor = this._validationAnchor()
      if (anchor !== null && anchor !== undefined && supportsAriaInvalid(anchor) === true) {
        if (anchor.getAttribute("aria-invalid") !== "true") {
          anchor.setAttribute("aria-invalid", "true")
          this._userInvalidAnchor = anchor
        }
      }
      return
    }

    onValidityRestored() {
      const anchor = this._userInvalidAnchor
      this._userInvalidAnchor = null
      if (anchor !== null && this.hasAttribute("invalid") === false) {
        anchor.removeAttribute("aria-invalid")
      }
      return
    }
  }

  return FormControl
}
