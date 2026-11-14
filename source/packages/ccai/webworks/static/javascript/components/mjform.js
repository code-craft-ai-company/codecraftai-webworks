/*
 * mjform.js
 *
 * <mj-form> -- coordinates submission across all form controls placed inside
 * it, aggregates validity, triggers field-level and summary-level validation
 * reporting, and emits structured events. It is the authoritative submission
 * orchestrator for its subtree.
 *
 * How the controls are owned
 * --------------------------
 * A form owns the controls that are its DOM descendants, or that name it in
 * their `form` attribute. Slotted content is neither a DOM descendant of
 * anything in the shadow root, so a <form> rendered there owns nothing. The
 * component therefore keeps one real <form> -- the "owner form" -- in its
 * light DOM (hidden, never rendered) and points every control inside the
 * host at it through the `form` attribute. From then on the platform does
 * the work: FormData contains native values and ElementInternals values,
 * native submit and reset buttons act on the form, `control.form` is set,
 * form reset reaches `formResetCallback`, and a native `action` submission
 * posts the real data.
 *
 * Contracts with other components
 * -------------------------------
 *   - <mj-button type="submit|reset"> dispatches a cancelable
 *     `mj-submit-request` / `mj-reset-request` event with
 *     detail { submitter }. The form answers the request and cancels it.
 *   - A control renders its own inline error when it receives the native
 *     `invalid` event, which `checkValidity()` raises on a failed submit.
 *   - A value-bearing component that is not form-associated still takes
 *     part when it has a `name` attribute and a `value` property; optional
 *     `checkValidity()` / `validationMessage` / `formResetCallback()` are
 *     used when present.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";
import {
  NATIVE_CONTROL_SELECTOR, isCustomElement, isFormAssociatedCustomElement, listFormControls, DisabledPropagation
} from "../core/formcontrols.js";

/* Re-exported for modules that imported them from here before they moved to core. */
export { isFormAssociatedCustomElement, listFormControls, DisabledPropagation } from "../core/formcontrols.js";

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

/* ----- form constants ----- */

/* Ids generated for owner forms start with this, so they can be recognised. */
const OWNER_FORM_ID_PREFIX = "mj-form-owner";

/* <input> types whose Enter key performs implicit form submission. */
const IMPLICIT_SUBMISSION_INPUT_TYPES = [
  "text", "search", "url", "tel", "email", "password",
  "date", "month", "week", "time", "datetime-local", "number"
];

/* ----- <mj-form> ----- */

export class MjForm extends MjElement {
  static tagName = "mj-form";
  static styles = STYLES;
  static watched = [
    "action", "method", "enctype", "novalidate", "validate", "loading", "autocomplete",
    "target", "submitting-label", "aria-label", "aria-labelledby"
  ];

  constructor() {
    super()

    /* True after the first submit attempt; gates eager/aggressive validation. */
    this._submitted = false

    /* Counts handled submit attempts, to detect a submit made during a key event. */
    this._submitSerial = 0
    this._serialAtEnter = 0

    this._formEl = null
    this._statusEl = null

    /* The light-DOM <form> that owns the controls. */
    this._ownerForm = null
    this._createdOwnerForm = false
    this._nested = false
    this._controlObserver = null

    /* Custom element names seen before their definition was registered. */
    this._pendingDefinitions = new Set()

    this._formDisabled = new DisabledPropagation()
    this._loadingDisabled = new DisabledPropagation()

    /* True when this component gave the host role="form". */
    this._setRole = false

    this._onOwnerSubmit = this._handleOwnerSubmit.bind(this)
    this._onOwnerReset = this._handleOwnerReset.bind(this)
    this._onOwnerFormData = this._handleOwnerFormData.bind(this)
  }

  render() {
    const markup = html`
      <div class="form" part="form">
        <slot name="summary"></slot>
        <slot></slot>
      </div>
      <span class="status" role="status" aria-live="polite" aria-atomic="true"></span>
    `
    return markup
  }

  afterRender() {
    this._formEl = this.$(".form")
    this._statusEl = this.$(".status")

    this.listen(this, "mj-submit-request", this._onSubmitRequest.bind(this))
    this.listen(this, "mj-reset-request", this._onResetRequest.bind(this))
    this.listen(this, "keydown", this._onKeydownCapture.bind(this), true)
    this.listen(this, "keydown", this._onKeydown.bind(this))
    this.listen(this, "focusout", this._onChildBlur.bind(this))
    this.listen(this, "change", this._onChildChange.bind(this))
    this.listen(this, "input", this._onChildChange.bind(this))
    return
  }

  onConnected() {
    const outer = this.parentElement !== null ? this.parentElement.closest("mj-form") : null
    this._nested = outer !== null

    if (this._nested === true) {
      console.error("[mj-form] <mj-form> must not be nested inside another <mj-form>; the inner form is ignored.", this)
      return
    }

    this._ensureOwnerForm()
    this._syncFormAttributes()
    this._associateControls()
    this._observeControls()
    this._syncAccessibleName()
    this._syncDisabled()
    this._syncLoading()
    return
  }

  onDisconnected() {
    this._releaseOwnerForm()
    this._formDisabled.release()
    this._loadingDisabled.release()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._formEl === undefined || this._formEl === null || this._ownerForm === null) {
      return
    }

    if (name === "disabled") {
      this._syncDisabled()
    } else if (name === "loading" || name === "submitting-label") {
      this._syncLoading()
    } else if (name === "aria-label" || name === "aria-labelledby") {
      this._syncAccessibleName()
    } else {
      this._syncFormAttributes()
    }
    return
  }

  /* ----- owner form ----- */

  /*
   * Find or create the light-DOM form that owns the controls. A <form> the
   * author (or the server) placed directly inside the host is adopted;
   * otherwise a hidden one is appended. It is assigned to a slot that does
   * not exist, so it is never rendered.
   */
  _ensureOwnerForm() {
    let form = this.querySelector(":scope > form[data-mj-form-owner]")
    let created = form !== null

    if (form === null) {
      form = this.querySelector(":scope > form")
    }

    if (form === null) {
      form = document.createElement("form")
      form.setAttribute("data-mj-form-owner", "")
      form.setAttribute("slot", "mj-form-owner")
      form.hidden = true
      this.appendChild(form)
      created = true
    }

    /* A cloned host carries a copy of the id: make it unique in this tree. */
    const root = this.getRootNode()
    const idInUse = form.id.length > 0 && root.querySelectorAll(`#${CSS.escape(form.id)}`).length > 1
    if (form.id.length === 0 || idInUse === true) {
      form.id = nextId(OWNER_FORM_ID_PREFIX)
    }

    /* Validation is run by this component, never by the browser's bubbles. */
    form.noValidate = true

    form.addEventListener("submit", this._onOwnerSubmit)
    form.addEventListener("reset", this._onOwnerReset)
    form.addEventListener("formdata", this._onOwnerFormData)

    this._ownerForm = form
    this._createdOwnerForm = created
    return
  }

  _releaseOwnerForm() {
    if (this._controlObserver !== null) {
      this._controlObserver.disconnect()
      this._controlObserver = null
    }
    if (this._ownerForm !== null) {
      this._ownerForm.removeEventListener("submit", this._onOwnerSubmit)
      this._ownerForm.removeEventListener("reset", this._onOwnerReset)
      this._ownerForm.removeEventListener("formdata", this._onOwnerFormData)
      this._ownerForm = null
    }
    return
  }

  _syncFormAttributes() {
    const form = this._ownerForm
    if (form === null) {
      return
    }

    const mirrored = ["action", "method", "enctype", "autocomplete", "target"]
    for (let index = 0; index < mirrored.length; index = index + 1) {
      const name = mirrored[index]
      const value = this.getAttribute(name)
      if (value !== null) {
        form.setAttribute(name, value)
      } else if (this._createdOwnerForm === true) {
        form.removeAttribute(name)
      }
    }

    if (this._createdOwnerForm === true && this.hasAttribute("method") === false) {
      form.setAttribute("method", "post")
    }
    return
  }

  /*
   * Point every control inside the host at the owner form. Controls that
   * are DOM descendants of the owner form are owned already; a control
   * whose `form` attribute was written by the author is left alone.
   */
  _associateControls() {
    const form = this._ownerForm
    if (form === null) {
      return
    }

    const all = this.querySelectorAll("*")
    for (let index = 0; index < all.length; index = index + 1) {
      const element = all[index]

      let listed = element.matches(NATIVE_CONTROL_SELECTOR) === true
      if (listed === false && isCustomElement(element) === true) {
        if (customElements.get(element.localName) === undefined) {
          /* Not defined yet: look again once it has been upgraded. */
          this._associateWhenDefined(element.localName)
        } else {
          listed = isFormAssociatedCustomElement(element) === true
        }
      }

      if (listed === false || element === form || form.contains(element) === true) {
        continue
      }
      if (element.closest("mj-form") !== this || element.closest("form") !== null) {
        continue
      }

      const current = element.getAttribute("form")
      const generated = current !== null && current.startsWith(OWNER_FORM_ID_PREFIX) === true
      if (current === null || (generated === true && current !== form.id)) {
        element.setAttribute("form", form.id)
      }
    }
    return
  }

  _associateWhenDefined(localName) {
    if (this._pendingDefinitions.has(localName) === true) {
      return
    }
    this._pendingDefinitions.add(localName)

    customElements.whenDefined(localName).then(() => {
      this._pendingDefinitions.delete(localName)
      if (this._ownerForm !== null) {
        this._associateControls()
        this._syncDisabled()
      }
    })
    return
  }

  /* Remove the generated `form` attribute from controls that left the host. */
  _dissociateRemoved(node) {
    if (node.nodeType !== Node.ELEMENT_NODE || this._ownerForm === null || this.contains(node) === true) {
      return
    }

    const formId = this._ownerForm.id
    const candidates = [node].concat(Array.from(node.querySelectorAll("[form]")))
    for (let index = 0; index < candidates.length; index = index + 1) {
      const candidate = candidates[index]
      if (candidate.getAttribute("form") === formId) {
        candidate.removeAttribute("form")
      }
    }
    return
  }

  /* Controls added or removed later are picked up as they change. */
  _observeControls() {
    if (this._controlObserver !== null) {
      this._controlObserver.disconnect()
    }

    this._controlObserver = new MutationObserver((records) => {
      for (let index = 0; index < records.length; index = index + 1) {
        const removed = records[index].removedNodes
        for (let position = 0; position < removed.length; position = position + 1) {
          this._dissociateRemoved(removed[position])
        }
      }
      this._associateControls()
      if (this.hasAttribute("disabled") === true) {
        this._syncDisabled()
      }
      if (this.hasAttribute("loading") === true) {
        this._syncLoading()
      }
    })
    this._controlObserver.observe(this, { childList: true, subtree: true })
    return
  }

  /* ----- control collection ----- */

  /*
   * Every control of this form: the elements the owner form owns, followed
   * by the custom elements that take part through the value contract only.
   */
  _collectControls() {
    const controls = []
    if (this._ownerForm === null) {
      return controls
    }

    this._associateControls()

    const owned = Array.from(this._ownerForm.elements)
    for (let index = 0; index < owned.length; index = index + 1) {
      controls.push(owned[index])
    }

    const extras = this._contractControls()
    for (let index = 0; index < extras.length; index = index + 1) {
      controls.push(extras[index])
    }
    return controls
  }

  /*
   * Custom elements inside the host that are not form-associated but have a
   * `name` attribute and a `value` property. Their value is appended to the
   * form data by hand.
   */
  _contractControls() {
    const extras = []
    const candidates = listFormControls(this)

    for (let index = 0; index < candidates.length; index = index + 1) {
      const candidate = candidates[index]
      const custom = isCustomElement(candidate) === true
      if (custom === true && isFormAssociatedCustomElement(candidate) === false) {
        extras.push(candidate)
      }
    }
    return extras
  }

  /* The submit buttons of the form, native and mj-button, in document order. */
  _submitButtons() {
    const buttons = []
    const controls = this._collectControls()

    for (let index = 0; index < controls.length; index = index + 1) {
      const control = controls[index]
      const native = (control instanceof HTMLButtonElement && control.type === "submit") ||
        (control instanceof HTMLInputElement && (control.type === "submit" || control.type === "image"))
      const custom = isCustomElement(control) === true && control.getAttribute("type") === "submit"
      const transient = control.hasAttribute("data-mj-submitter")
      if ((native === true || custom === true) && transient === false) {
        buttons.push(control)
      }
    }
    return buttons
  }

  /* ----- form data ----- */

  /* Add the values of the contract-only controls to a FormData being built. */
  _handleOwnerFormData(event) {
    const extras = this._contractControls()

    for (let index = 0; index < extras.length; index = index + 1) {
      const control = extras[index]
      const name = control.getAttribute("name") || ""
      if (name.length === 0 || control.hasAttribute("disabled") === true || !("value" in control)) {
        continue
      }

      const value = control.value
      const values = Array.isArray(value) === true ? value : [value]
      for (let position = 0; position < values.length; position = position + 1) {
        const entry = values[position]
        if (entry === null || entry === undefined) {
          continue
        }
        if (entry instanceof Blob) {
          event.formData.append(name, entry)
        } else if (typeof entry === "object") {
          event.formData.append(name, JSON.stringify(entry))
        } else {
          event.formData.append(name, String(entry))
        }
      }
    }
    return
  }

  /*
   * Build the FormData of the form and the matching plain object, in which
   * every name maps to the list of its values.
   */
  _buildFormValue(submitter) {
    let formData = null

    if (this._ownerForm === null) {
      formData = new FormData()
    } else {
      const nativeSubmitter = submitter !== null && submitter !== undefined &&
        (submitter instanceof HTMLButtonElement || submitter instanceof HTMLInputElement) &&
        submitter.form === this._ownerForm

      if (nativeSubmitter === true) {
        formData = new FormData(this._ownerForm, submitter)
      } else {
        formData = new FormData(this._ownerForm)

        /* A custom submit button contributes its name/value pair as well. */
        if (submitter !== null && submitter !== undefined && typeof submitter.getAttribute === "function") {
          const name = submitter.getAttribute("name") || ""
          if (name.length > 0) {
            formData.append(name, submitter.getAttribute("value") || "")
          }
        }
      }
    }

    const value = {}
    for (const [key, entry] of formData.entries()) {
      if (value[key] === undefined) {
        value[key] = []
      }
      value[key].push(entry)
    }

    const built = { formData: formData, value: value }
    return built
  }

  /* ----- submit and reset requests ----- */

  _ownsSubmitter(submitter) {
    let owns = false
    if (submitter !== null && submitter !== undefined && this._ownerForm !== null) {
      const form = submitter.form
      if (form !== null && form !== undefined) {
        owns = form === this._ownerForm
      } else if (typeof submitter.closest === "function") {
        owns = submitter.closest("mj-form") === this && submitter.hasAttribute("form") === false
      }
    }
    return owns
  }

  /* <mj-button type="submit"> (or any component using the same request). */
  _onSubmitRequest(event) {
    const submitter = event.detail !== null && event.detail !== undefined ? event.detail.submitter : null
    if (this._ownsSubmitter(submitter) === false) {
      return
    }
    event.preventDefault()
    this._handleSubmit(submitter)
    return
  }

  _onResetRequest(event) {
    const submitter = event.detail !== null && event.detail !== undefined ? event.detail.submitter : null
    if (this._ownsSubmitter(submitter) === false) {
      return
    }
    event.preventDefault()
    this.reset()
    return
  }

  /* A native submit button, requestSubmit(), or a component calling it. */
  _handleOwnerSubmit(event) {
    event.preventDefault()
    this._handleSubmit(event.submitter)
    return
  }

  /*
   * A native reset button or reset(). `mj-reset` can veto it; otherwise the
   * browser resets the native controls and calls `formResetCallback` on
   * the form-associated ones, and the rest is reset here.
   */
  _handleOwnerReset(event) {
    const proceed = this.emit("mj-reset", {}, { cancelable: true })
    if (proceed === false) {
      event.preventDefault()
      return
    }

    this._submitted = false

    const extras = this._contractControls()
    for (let index = 0; index < extras.length; index = index + 1) {
      const control = extras[index]
      if (typeof control.formResetCallback === "function") {
        control.formResetCallback()
      } else if (typeof control.reset === "function") {
        control.reset()
      }
    }

    /* The controls hold their reset values once this event has finished. */
    queueMicrotask(() => {
      this._refreshErrorMessages(false)
    })
    return
  }

  /* ----- implicit submission (Enter in a single-line text control) ----- */

  _onKeydownCapture(event) {
    if (event.key === "Enter") {
      this._serialAtEnter = this._submitSerial
    }
    return
  }

  /*
   * Enter in a single-line text control submits the form, as it does in a
   * native form. The browser only does this for native inputs when the
   * form has a native submit button, and never for the input inside an
   * mj-* control, so the form does it for both. A control that uses Enter
   * itself (a combobox, a token input, an inline edit) prevents the
   * default and is left alone.
   */
  _onKeydown(event) {
    const plainEnter = event.key === "Enter" && event.isComposing !== true &&
      event.ctrlKey === false && event.altKey === false && event.metaKey === false && event.shiftKey === false

    if (plainEnter === false || event.defaultPrevented === true || this._ownerForm === null) {
      return
    }
    if (this._submitSerial !== this._serialAtEnter) {
      /* A control already submitted the form while handling this key. */
      return
    }

    const path = event.composedPath()
    const origin = path.length > 0 ? path[0] : null
    const isTextInput = origin instanceof HTMLInputElement &&
      IMPLICIT_SUBMISSION_INPUT_TYPES.indexOf(origin.type) !== -1
    if (isTextInput === false) {
      return
    }

    /* An input that drives a popup uses Enter to choose from it. */
    const hasPopup = origin.getAttribute("role") === "combobox" ||
      origin.hasAttribute("aria-autocomplete") === true ||
      origin.hasAttribute("aria-haspopup") === true ||
      origin.hasAttribute("list") === true
    if (hasPopup === true) {
      return
    }

    /* The input itself, or the mj-* control it lives in, must be ours. */
    let owned = false
    for (let index = 0; index < path.length && path[index] !== this; index = index + 1) {
      const node = path[index]
      if (node instanceof Element && node.form === this._ownerForm) {
        owned = true
      }
    }
    if (owned === false) {
      return
    }

    /* Handled here, so the browser's own implicit submission must not run too. */
    event.preventDefault()

    const buttons = this._submitButtons()
    if (buttons.length > 0) {
      const defaultButton = buttons[0]
      if (defaultButton.disabled !== true && defaultButton.hasAttribute("disabled") === false) {
        defaultButton.click()
      }
    } else {
      this._handleSubmit(null)
    }
    return
  }

  /* ----- validation ----- */

  /*
   * The text that names `control` to the user: an <mj-label for>, the
   * control's own `label` attribute, a native <label>, aria-label, and
   * finally its name.
   */
  _labelFor(control) {
    let label = ""

    if (control.id.length > 0) {
      const root = this.getRootNode()
      const labelEl = root.querySelector(`mj-label[for="${CSS.escape(control.id)}"]`)
      if (labelEl !== null) {
        label = labelEl.textContent.trim()
      }
    }
    if (label.length === 0) {
      label = (control.getAttribute("label") || "").trim()
    }
    if (label.length === 0 && control.labels !== null && control.labels !== undefined && control.labels.length > 0) {
      label = control.labels[0].textContent.trim()
    }
    if (label.length === 0) {
      label = (control.getAttribute("aria-label") || "").trim()
    }
    if (label.length === 0) {
      label = control.getAttribute("name") || ""
    }
    return label
  }

  _describeInvalid(control) {
    const name = control.getAttribute("name") || ""
    const entry = {
      control: control,
      controlId: control.id.length > 0 ? control.id : name,
      name: name,
      label: this._labelFor(control),
      message: typeof control.validationMessage === "string" ? control.validationMessage : ""
    }
    return entry
  }

  /*
   * The <mj-error-message auto> elements in this tree that belong to a
   * control of this form are told to re-evaluate their control.
   */
  _refreshErrorMessages(show) {
    const root = this.getRootNode()
    const messages = root.querySelectorAll("mj-error-message[auto][for]")

    for (let index = 0; index < messages.length; index = index + 1) {
      const message = messages[index]
      const control = message.control
      const ours = control !== null && control !== undefined && this.contains(control) === true
      if (ours === true && typeof message.refresh === "function") {
        message.refresh(show)
      }
    }
    return
  }

  /* The validation summary this form feeds, if it shows one. */
  _activeSummary() {
    let summary = this.querySelector("mj-validation-summary")

    if (summary === null && this.id.length > 0) {
      const root = this.getRootNode()
      summary = root.querySelector(`mj-validation-summary[for="${CSS.escape(this.id)}"]`)
    }
    return summary
  }

  /* Run constraint validation on one control; `invalid` renders its error. */
  _validateControl(control) {
    let valid = true
    if (typeof control.checkValidity === "function") {
      valid = control.checkValidity() !== false
    }
    return valid
  }

  /* eager / aggressive re-validation after the first submit attempt. */
  _revalidateFrom(event, modes) {
    if (this._submitted === false || this._ownerForm === null) {
      return
    }
    const mode = this.getAttribute("validate") || "submit"
    if (modes.indexOf(mode) === -1 || this.hasAttribute("novalidate") === true) {
      return
    }

    const controls = this._collectControls()
    const path = event.composedPath()
    for (let index = 0; index < path.length && path[index] !== this; index = index + 1) {
      if (controls.indexOf(path[index]) !== -1) {
        this._validateControl(path[index])
        this._refreshErrorMessages(true)
      }
    }
    return
  }

  _onChildChange(event) {
    this._revalidateFrom(event, ["aggressive"])
    return
  }

  _onChildBlur(event) {
    this._revalidateFrom(event, ["eager", "aggressive"])
    return
  }

  /*
   * One submit attempt: validate, then either report the invalid controls
   * (mj-invalid, inline errors, summary, focus) or emit mj-submit and, when
   * an action is set and the event was not cancelled, submit natively.
   */
  _handleSubmit(submitter) {
    if (this.hasAttribute("loading") === true || this._nested === true || this._ownerForm === null) {
      return
    }

    this._submitSerial = this._submitSerial + 1
    this._submitted = true

    const skipValidation = this.hasAttribute("novalidate") === true ||
      (submitter !== null && submitter !== undefined && typeof submitter.hasAttribute === "function" &&
        submitter.hasAttribute("formnovalidate") === true)

    const controls = this._collectControls()
    const invalid = []

    if (skipValidation === false) {
      for (let index = 0; index < controls.length; index = index + 1) {
        if (this._validateControl(controls[index]) === false) {
          invalid.push(controls[index])
        }
      }
      this._refreshErrorMessages(true)
    }

    if (invalid.length > 0) {
      const errors = invalid.map((control) => this._describeInvalid(control))
      const summary = errors.map((entry) => {
        return { name: entry.name, message: entry.message }
      })

      /* A validation summary listens for this event and lists `errors`. */
      this.emit("mj-invalid", { controls: invalid, summary: summary, errors: errors })

      const summaryEl = this._activeSummary()
      const summaryTakesFocus = summaryEl !== null &&
        summaryEl.hasAttribute("visible") === true &&
        summaryEl.getAttribute("focus-on-show") !== "false"

      if (summaryTakesFocus === false && typeof invalid[0].focus === "function") {
        invalid[0].focus()
      }
      return
    }

    const built = this._buildFormValue(submitter)
    const proceed = this.emit(
      "mj-submit",
      { formData: built.formData, value: built.value, valid: true, submitter: submitter || null },
      { cancelable: true }
    )
    if (proceed === false) {
      return
    }

    const action = this.getAttribute("action") || ""
    const method = (this.getAttribute("method") || "").toLowerCase()
    if (action.length > 0 || method === "dialog") {
      /* submit() posts the owner form's real data and raises no event. */
      this._ownerForm.submit()
    }
    return
  }

  /* ----- state reflected from attributes ----- */

  /* `disabled` disables every control inside the form, and restores them. */
  _syncDisabled() {
    if (this.hasAttribute("disabled") === true) {
      this._formDisabled.apply(listFormControls(this))
    } else {
      this._formDisabled.release()
    }
    return
  }

  /*
   * While `loading`, the form is busy: assistive technology is told once,
   * the submit buttons are disabled, and both are undone when it ends.
   */
  _syncLoading() {
    const loading = this.hasAttribute("loading")

    if (loading === true) {
      this.setAttribute("aria-busy", "true")
      this._loadingDisabled.apply(this._submitButtons())
      const label = this.getAttribute("submitting-label") || t("mj.form.submitting")
      if (this._statusEl !== null && this._statusEl.textContent !== label) {
        this._statusEl.textContent = label
      }
    } else {
      this.removeAttribute("aria-busy")
      this._loadingDisabled.release()
      if (this._statusEl !== null) {
        this._statusEl.textContent = ""
      }
    }
    return
  }

  /* A form with an accessible name is a landmark: give the host the role. */
  _syncAccessibleName() {
    const named = this.hasAttribute("aria-label") === true || this.hasAttribute("aria-labelledby") === true

    if (named === true && this.hasAttribute("role") === false) {
      this.setAttribute("role", "form")
      this._setRole = true
    } else if (named === false && this._setRole === true) {
      this.removeAttribute("role")
      this._setRole = false
    }
    return
  }

  /* ----- scriptable API ----- */

  /* The owner form's controls (HTMLFormControlsCollection), or null. */
  get elements() {
    let collection = null
    if (this._ownerForm !== null) {
      this._associateControls()
      collection = this._ownerForm.elements
    }
    return collection
  }

  /* True when every control of the form satisfies its constraints. */
  get valid() {
    const controls = this._collectControls()
    let allValid = true

    for (let index = 0; index < controls.length; index = index + 1) {
      const control = controls[index]
      let ok = true
      if (control.validity !== null && control.validity !== undefined) {
        ok = control.willValidate === false || control.validity.valid === true
      } else if (typeof control.checkValidity === "function") {
        ok = control.checkValidity() !== false
      }
      if (ok === false) {
        allValid = false
      }
    }
    return allValid
  }

  /* Snapshot of the form's values: { name: [value, ...] }. */
  get value() {
    this._associateControls()
    const built = this._buildFormValue(null)
    return built.value
  }

  get loading() {
    return this.hasAttribute("loading")
  }

  set loading(val) {
    this.reflectBoolean("loading", Boolean(val) === true)
    return
  }

  /* Validate and submit, exactly as activating a submit button does. */
  submit() {
    this._handleSubmit(null)
    return
  }

  requestSubmit(submitter) {
    this._handleSubmit(submitter !== undefined ? submitter : null)
    return
  }

  /* Reset every control; `mj-reset` can cancel it. */
  reset() {
    if (this._ownerForm !== null) {
      this._ownerForm.reset()
    }
    return
  }
}
