/*
 * formcontrols.js
 *
 * Form-control helpers shared by the form containers (<mj-form>,
 * <mj-fieldset>): find the controls in a subtree -- native listed elements,
 * form-associated custom elements, and custom elements that follow the
 * value contract -- and disable / re-enable them on behalf of one owner.
 *
 * Usage:
 *   import { listFormControls, DisabledPropagation } from "../core/formcontrols.js";
 *   const propagation = new DisabledPropagation()
 *   propagation.apply(listFormControls(this))   // ... later: propagation.release()
 */

/* Native elements that take part in a form ("listed" elements). */
export const NATIVE_CONTROL_SELECTOR = "input, select, textarea, button, output, object, fieldset";

/* True for an autonomous custom element (its tag name contains a dash). */
export function isCustomElement(element) {
  const custom = element.localName.indexOf("-") !== -1
  return custom
}

/* True for a custom element that is form-associated (ElementInternals). */
export function isFormAssociatedCustomElement(element) {
  let associated = false
  if (isCustomElement(element) === true) {
    associated = element.constructor.formAssociated === true
  }
  return associated
}

/*
 * The form controls among the light-DOM descendants of `container`, in
 * document order: native listed elements, form-associated custom elements,
 * and custom elements that follow the value contract (a `name` attribute
 * with a `value` property, or a `checkValidity()` method). Controls that
 * belong to a nested <mj-form> are left to that form.
 */
export function listFormControls(container) {
  const controls = []
  const all = container.querySelectorAll("*")

  for (let index = 0; index < all.length; index = index + 1) {
    const element = all[index]
    let isControl = false

    if (element.matches(NATIVE_CONTROL_SELECTOR) === true) {
      isControl = true
    } else if (isCustomElement(element) === true) {
      const followsContract = element.hasAttribute("name") === true && "value" in element
      isControl = isFormAssociatedCustomElement(element) === true ||
        typeof element.checkValidity === "function" ||
        followsContract === true
    }

    if (isControl === true) {
      const owner = element.closest("mj-form")
      const nested = owner !== null && owner !== container && container.contains(owner) === true
      if (nested === false) {
        controls.push(element)
      }
    }
  }

  return controls
}

/*
 * Disables controls on behalf of one owner (a disabled <mj-form> or
 * <mj-fieldset>, a loading form) and later re-enables exactly the controls
 * it disabled, so a control the author disabled stays disabled.
 */
export class DisabledPropagation {
  constructor() {
    this._disabledByOwner = new Set()
  }

  /* Disable every control in `controls` that is not disabled already. */
  apply(controls) {
    for (let index = 0; index < controls.length; index = index + 1) {
      const control = controls[index]
      if (control.hasAttribute("disabled") === false) {
        control.setAttribute("disabled", "")
        this._disabledByOwner.add(control)
      }
    }
    return
  }

  /* Re-enable the controls this owner disabled. */
  release() {
    this._disabledByOwner.forEach((control) => {
      control.removeAttribute("disabled")
    })
    this._disabledByOwner.clear()
    return
  }

  get active() {
    const active = this._disabledByOwner.size > 0
    return active
  }
}
