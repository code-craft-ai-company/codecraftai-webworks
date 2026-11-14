/*
 * mjbutton.js
 *
 * <mj-button> -- the primary action component and the REFERENCE pattern for
 * the whole mj-* library. Other components follow the structure used here:
 *   - extend MjElement (or a mixin of it),
 *   - declare `tagName`, `styles`, `watched`,
 *   - build shadow DOM in `render`, wire events in `afterRender`,
 *   - reflect state via attributes, expose scriptable properties,
 *   - emit namespaced `mj-*` events,
 *   - source every visual value from a design token (themeable),
 *   - expose ::part() hooks,
 *   - participate in docking/anchoring through MjElement.
 *
 * Catalog synonyms (primary/secondary/tertiary/link/icon/submit/reset/close/
 * back/next/previous/toolbar buttons) are all variants here, not separate
 * components.
 *
 * Form participation (type="submit" / type="reset"):
 *   1. The button first dispatches a composed, bubbling, cancelable
 *      `mj-submit-request` / `mj-reset-request` event with
 *      detail { submitter: <this button> }. A container that owns the form
 *      logic (<mj-form>) handles the request and cancels the event.
 *   2. When nobody cancels it, the button acts on its native form owner:
 *      submit goes through `form.requestSubmit()` with a transient native
 *      submit button that carries this button's name/value/form* attributes,
 *      so the pair reaches FormData and `event.submitter` is set; reset calls
 *      `form.reset()`.
 *   3. Enter in a single-line text control of the form activates the button
 *      when it is the form's default (first) submit button, exactly as HTML
 *      implicit submission does for a native submit button.
 */

import { MjElement } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";
import { t } from "../core/intl.js";

const STYLES = `
:host {
  display: inline-block;
  vertical-align: middle;
}
:host([block]) { display: block; }

.btn {
  --mj-button-variant-bg: var(--mj-surface);
  --mj-button-variant-color: var(--mj-text);
  --mj-button-variant-border-color: var(--mj-border-strong);

  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--mj-button-gap, var(--mj-space-2));
  min-height: var(--mj-button-height, var(--mj-control-height-md));
  min-width: var(--mj-button-min-width, var(--mj-target-min));
  padding: var(--mj-button-padding-y, 0) var(--mj-button-padding-x, var(--mj-space-4));
  font: inherit;
  font-size: var(--mj-button-font-size, inherit);
  font-weight: var(--mj-button-font-weight, var(--mj-font-weight-medium));
  line-height: 1;
  color: var(--mj-button-color, var(--mj-button-variant-color, var(--mj-text)));
  background: var(--mj-button-bg, var(--mj-button-variant-bg, var(--mj-surface)));
  border: 1px solid var(--mj-button-border-color, var(--mj-button-variant-border-color, var(--mj-border-strong)));
  border-radius: var(--mj-button-border-radius, var(--mj-radius-md));
  cursor: pointer;
  user-select: none;
  transition: background var(--mj-motion-fast) var(--mj-motion-ease),
              border-color var(--mj-motion-fast) var(--mj-motion-ease);
}
.btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-button-focus-ring-color, var(--mj-focus-ring));
  outline-offset: var(--mj-focus-ring-offset);
}

/* Variants */
:host([variant="primary"]) .btn {
  --mj-button-variant-color: var(--mj-text-on-accent);
  --mj-button-variant-bg: var(--mj-accent);
  --mj-button-variant-border-color: var(--mj-accent);
}
:host([variant="primary"]) .btn:hover {
  --mj-button-variant-bg: var(--mj-accent-hover);
  --mj-button-variant-border-color: var(--mj-accent-hover);
}
:host([variant="primary"]) .btn:active { --mj-button-variant-bg: var(--mj-accent-active); }

:host([variant="secondary"]) .btn:hover { --mj-button-variant-bg: var(--mj-bg-muted); }

:host([variant="tertiary"]) .btn,
:host([variant="link"]) .btn {
  --mj-button-variant-bg: transparent;
  --mj-button-variant-border-color: transparent;
}
:host([variant="tertiary"]) .btn:hover { --mj-button-variant-bg: var(--mj-bg-muted); }
:host([variant="link"]) .btn {
  --mj-button-variant-color: var(--mj-accent);
  text-decoration: underline;
  padding-inline: var(--mj-button-padding-x, var(--mj-space-1));
  min-width: var(--mj-button-min-width, auto);
}

/* Sizes */
:host([size="sm"]) .btn {
  min-height: var(--mj-button-height, var(--mj-control-height-sm));
  padding: var(--mj-button-padding-y, 0) var(--mj-button-padding-x, var(--mj-space-3));
  font-size: var(--mj-button-font-size, var(--mj-font-size-sm));
}
:host([size="lg"]) .btn {
  min-height: var(--mj-button-height, var(--mj-control-height-lg));
  padding: var(--mj-button-padding-y, 0) var(--mj-button-padding-x, var(--mj-space-5));
  font-size: var(--mj-button-font-size, var(--mj-font-size-lg));
}

/* Icon-only: the label stays in the accessibility tree but is not shown. */
:host([icon-only]) .btn { padding: 0; aspect-ratio: 1; }
:host([icon-only]) .label {
  position: absolute;
  width: 1px; height: 1px; margin: -1px; padding: 0; border: 0;
  overflow: hidden; clip: rect(0 0 0 0); clip-path: inset(50%); white-space: nowrap;
}

/*
 * States. The inner button is never natively disabled: it keeps focus and
 * its tab stop, and announces the state through aria-disabled / aria-busy.
 */
.btn[aria-disabled="true"] { opacity: 0.55; cursor: not-allowed; }
.btn[aria-busy="true"] { cursor: progress; }

.spinner {
  width: 1em; height: 1em;
  border: 2px solid currentColor;
  border-inline-end-color: transparent;
  border-radius: var(--mj-radius-circle);
  animation: mj-spin var(--mj-motion-slow) linear infinite;
}
:host(:not([loading])) .spinner { display: none; }
@keyframes mj-spin { to { transform: rotate(360deg); } }

::slotted([slot="icon"]),
::slotted([slot="trailing-icon"]) { display: inline-flex; }
`;

/* Host ARIA state attributes copied verbatim onto the inner <button>. */
const FORWARDED_ARIA_ATTRIBUTES = [
  "aria-expanded", "aria-haspopup", "aria-pressed", "aria-current", "aria-description"
];

/*
 * Host ARIA attributes that hold id references, with the element-reflection
 * property that carries the relationship. The ids name elements in the tree
 * the host lives in; an id attribute on the shadow <button> could never
 * resolve them, so the referenced elements are assigned directly.
 */
const FORWARDED_ARIA_REFERENCES = {
  "aria-controls": "ariaControlsElements",
  "aria-describedby": "ariaDescribedByElements",
  "aria-labelledby": "ariaLabelledByElements"
};

/* <input> types whose Enter key performs implicit form submission. */
const IMPLICIT_SUBMISSION_INPUT_TYPES = [
  "text", "search", "url", "tel", "email", "password",
  "date", "month", "week", "time", "datetime-local", "number"
];

/* Host attributes copied onto the transient native submitter. */
const SUBMITTER_ATTRIBUTES = [
  "name", "value", "formaction", "formenctype", "formmethod", "formnovalidate", "formtarget"
];

export class MjButton extends MjElement {
  static tagName = "mj-button";
  static styles = STYLES;
  static watched = [
    "variant", "size", "type", "loading", "icon-only", "block", "label",
    "aria-label", "aria-labelledby", "aria-describedby", "aria-controls",
    "aria-expanded", "aria-haspopup", "aria-pressed", "aria-current", "aria-description"
  ];
  static formAssociated = true;

  constructor() {
    super()
    if (typeof this.attachInternals === "function") {
      this._internals = this.attachInternals()
    } else {
      this._internals = null
    }

    this._button = null

    /* True while an ancestor <fieldset disabled> disables this control. */
    this._formDisabled = false

    /* Loading state last announced, so a repeated sync does not re-announce. */
    this._announcedLoading = false

    /* True once the missing-accessible-name warning was logged. */
    this._warnedMissingName = false

    /* Implicit-submission wiring on the form owner. */
    this._wiredForm = null
    this._submitSeenDuringEnter = false
    this._onFormKeydownCapture = this._handleFormKeydownCapture.bind(this)
    this._onFormKeydown = this._handleFormKeydown.bind(this)
    this._onFormSubmit = this._handleFormSubmit.bind(this)
  }

  render() {
    const markup = `
      <button class="btn" part="button" type="button">
        <span class="spinner" part="spinner" aria-hidden="true"></span>
        <slot name="icon" part="icon"></slot>
        <span class="label" part="label"><slot></slot></span>
        <slot name="trailing-icon" part="trailing-icon"></slot>
      </button>
    `
    return markup
  }

  afterRender() {
    this._button = this.$(".btn")
    this.listen(this._button, "click", this._onClick.bind(this))

    /* Elements referenced by id may have been added since the last sync. */
    this.listen(this._button, "focus", this._syncAriaReferences.bind(this))

    this._announcedLoading = this.hasAttribute("loading")
    this._syncAccessibility()
    return
  }

  onConnected() {
    this._wireForm()
    return
  }

  onDisconnected() {
    this._unwireForm()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._button === undefined || this._button === null) {
      return
    }

    this._syncAccessibility()

    if (name === "loading") {
      this._announceLoading()
    }
    return
  }

  /* ----- form-associated custom element callbacks ----- */

  formAssociatedCallback(form) {
    if (this._connected === true) {
      this._wireForm()
    }
    return
  }

  formDisabledCallback(disabled) {
    this._formDisabled = disabled === true
    if (this._button !== undefined && this._button !== null) {
      this._syncAccessibility()
    }
    return
  }

  /*
   * True when activation must be ignored: the button is disabled (by its own
   * attribute or by an ancestor <fieldset disabled>) or busy.
   */
  _isInert() {
    const disabled = this.hasAttribute("disabled") === true || this._formDisabled === true
    const loading = this.hasAttribute("loading")
    const inert = disabled === true || loading === true
    return inert
  }

  /* Keep the inner control's ARIA state in sync with the host. */
  _syncAccessibility() {
    const disabled = this.hasAttribute("disabled") === true || this._formDisabled === true
    const loading = this.hasAttribute("loading")

    /*
     * aria-disabled instead of the native `disabled` property: the control
     * keeps keyboard focus when it turns busy or disabled and stays
     * discoverable; activation is blocked in `_onClick`.
     */
    if (disabled === true || loading === true) {
      this._button.setAttribute("aria-disabled", "true")
    } else {
      this._button.removeAttribute("aria-disabled")
    }

    /* `disabled` takes precedence over `loading`. */
    const busy = loading === true && disabled === false
    this._button.setAttribute("aria-busy", busy === true ? "true" : "false")

    this._syncAccessibleName()

    for (let index = 0; index < FORWARDED_ARIA_ATTRIBUTES.length; index = index + 1) {
      const attributeName = FORWARDED_ARIA_ATTRIBUTES[index]
      const attributeValue = this.getAttribute(attributeName)
      if (attributeValue !== null) {
        this._button.setAttribute(attributeName, attributeValue)
      } else {
        this._button.removeAttribute(attributeName)
      }
    }

    this._syncAriaReferences()
    return
  }

  /*
   * The accessible name comes from `label`, then the host `aria-label`, then
   * the slotted text (which stays in the accessibility tree in icon-only
   * mode). An icon-only button with none of them is reported once.
   */
  _syncAccessibleName() {
    let accessibleName = this.getAttribute("label")
    if (accessibleName === null || accessibleName === "") {
      accessibleName = this.getAttribute("aria-label")
    }

    if (accessibleName !== null && accessibleName !== "") {
      this._button.setAttribute("aria-label", accessibleName)
    } else {
      this._button.removeAttribute("aria-label")

      const iconOnly = this.hasAttribute("icon-only")
      const labelledBy = this.getAttribute("aria-labelledby")
      const slottedText = this.textContent !== null ? this.textContent.trim() : ""
      const unnamed = iconOnly === true && labelledBy === null && slottedText === ""
      if (unnamed === true && this._warnedMissingName === false) {
        this._warnedMissingName = true
        console.warn("mj-button: an icon-only button needs a `label` attribute for its accessible name.", this)
      }
    }
    return
  }

  /*
   * Resolve the host's ARIA id references in the host's own tree and hand
   * the elements to the inner button.
   */
  _syncAriaReferences() {
    if (this._button === undefined || this._button === null) {
      return
    }

    const root = this.getRootNode()
    const attributeNames = Object.keys(FORWARDED_ARIA_REFERENCES)

    for (let index = 0; index < attributeNames.length; index = index + 1) {
      const attributeName = attributeNames[index]
      const propertyName = FORWARDED_ARIA_REFERENCES[attributeName]
      const supported = propertyName in this._button
      const attributeValue = this.getAttribute(attributeName)

      if (supported === false) {
        /* No element reflection: the best available is the raw id list. */
        if (attributeValue !== null) {
          this._button.setAttribute(attributeName, attributeValue)
        } else {
          this._button.removeAttribute(attributeName)
        }
        continue
      }

      const referenced = []
      if (attributeValue !== null && typeof root.getElementById === "function") {
        const ids = attributeValue.split(/\s+/)
        for (let idIndex = 0; idIndex < ids.length; idIndex = idIndex + 1) {
          const id = ids[idIndex]
          const element = id !== "" ? root.getElementById(id) : null
          if (element !== null) {
            referenced.push(element)
          }
        }
      }

      this._button[propertyName] = referenced.length > 0 ? referenced : null
    }
    return
  }

  /*
   * Announce entry to and exit from the loading state. Runs only on a real
   * transition so a replayed or repeated attribute change stays silent.
   */
  _announceLoading() {
    const loading = this.hasAttribute("loading")
    if (loading === this._announcedLoading) {
      return
    }
    this._announcedLoading = loading

    let message = ""
    if (loading === true) {
      const loadingLabel = this.getAttribute("loading-label")
      message = loadingLabel !== null && loadingLabel !== "" ? loadingLabel : t("core.loading")
    } else {
      const doneLabel = this.getAttribute("done-label")
      message = doneLabel !== null && doneLabel !== "" ? doneLabel : t("mj.button.done")
    }

    announce(message, "polite")
    return
  }

  _onClick(event) {
    if (this._isInert() === true) {
      event.stopImmediatePropagation()
      event.preventDefault()
      return
    }

    const proceed = this.emit("mj-click", { source: this, originalEvent: event }, { cancelable: true })
    if (proceed === false) {
      return
    }

    const type = this.getAttribute("type") || "button"
    if (type === "submit" || type === "reset") {
      this._requestFormAction(type)
    }
    return
  }

  /*
   * Submit or reset the form this button belongs to. A container that owns
   * the form logic (<mj-form>) answers the request event and cancels it; when
   * nobody does, the native form owner is used.
   */
  _requestFormAction(type) {
    const requestName = type === "submit" ? "mj-submit-request" : "mj-reset-request"
    const unhandled = this.emit(requestName, { submitter: this }, { cancelable: true })
    if (unhandled === false) {
      return
    }

    const form = this.form
    if (form !== null && form !== undefined) {
      if (type === "submit") {
        this._submitNativeForm(form)
      } else {
        form.reset()
      }
      return
    }

    /*
     * No native form owner and nobody answered the request: an <mj-form>
     * ancestor that predates the request events is driven through its API.
     */
    const container = this.closest("mj-form")
    if (container !== null) {
      if (type === "submit" && typeof container.submit === "function") {
        container.submit()
      } else if (type === "reset" && typeof container.reset === "function") {
        container.reset()
      }
    }
    return
  }

  /*
   * Submit `form` with this button as the submitter. A custom element cannot
   * be passed to requestSubmit(), so a hidden native submit button carrying
   * this button's name/value/form* attributes stands in for the duration of
   * the call: the pair reaches FormData and `event.submitter` is set.
   */
  _submitNativeForm(form) {
    const submitter = document.createElement("button")
    submitter.type = "submit"
    submitter.hidden = true
    submitter.tabIndex = -1
    submitter.setAttribute("aria-hidden", "true")
    submitter.setAttribute("data-mj-submitter", "")

    for (let index = 0; index < SUBMITTER_ATTRIBUTES.length; index = index + 1) {
      const attributeName = SUBMITTER_ATTRIBUTES[index]
      const attributeValue = this.getAttribute(attributeName)
      if (attributeValue !== null) {
        submitter.setAttribute(attributeName, attributeValue)
      }
    }

    form.appendChild(submitter)
    try {
      form.requestSubmit(submitter)
    } finally {
      submitter.remove()
    }
    return
  }

  /* ----- implicit submission (Enter in a text control of the form) ----- */

  _wireForm() {
    const form = this.form

    if (form === this._wiredForm) {
      return
    }
    this._unwireForm()

    if (form !== null && form !== undefined) {
      form.addEventListener("keydown", this._onFormKeydownCapture, true)
      form.addEventListener("keydown", this._onFormKeydown)
      form.addEventListener("submit", this._onFormSubmit, true)
      this._wiredForm = form
    }
    return
  }

  _unwireForm() {
    const form = this._wiredForm
    if (form !== null) {
      form.removeEventListener("keydown", this._onFormKeydownCapture, true)
      form.removeEventListener("keydown", this._onFormKeydown)
      form.removeEventListener("submit", this._onFormSubmit, true)
      this._wiredForm = null
    }
    return
  }

  _handleFormKeydownCapture(event) {
    if (event.key === "Enter") {
      this._submitSeenDuringEnter = false
    }
    return
  }

  _handleFormSubmit(event) {
    this._submitSeenDuringEnter = true
    return
  }

  /*
   * HTML implicit submission: Enter in a single-line text control activates
   * the form's default button. The browser does that only for native submit
   * buttons, and never for a text control inside another component's shadow
   * root, so this button does it when it is the default button.
   */
  _handleFormKeydown(event) {
    const form = this._wiredForm

    const isPlainEnter =
      event.key === "Enter" &&
      event.isComposing !== true &&
      event.ctrlKey === false &&
      event.altKey === false &&
      event.metaKey === false
    if (isPlainEnter === false || event.defaultPrevented === true) {
      return
    }

    if (this.getAttribute("type") !== "submit") {
      return
    }

    /* A control that handled Enter itself has already submitted the form. */
    if (this._submitSeenDuringEnter === true) {
      return
    }

    const path = event.composedPath()
    const source = path.length > 0 ? path[0] : null
    if (this._isImplicitSubmissionField(form, source) === false) {
      return
    }

    if (this._findDefaultButton(form) !== this) {
      return
    }

    /* Keeps the browser from submitting a second time on its own. */
    event.preventDefault()
    this.click()
    return
  }

  /*
   * True when `source` is a single-line text <input> owned by `form`, either
   * directly or through the form-associated component whose shadow root
   * contains it.
   */
  _isImplicitSubmissionField(form, source) {
    let isField = false

    const isTextInput =
      source !== null &&
      source.localName === "input" &&
      IMPLICIT_SUBMISSION_INPUT_TYPES.indexOf(source.type) >= 0

    if (isTextInput === true) {
      if (source.form === form) {
        isField = true
      } else {
        /* Climb out of nested shadow roots to the element in the form's tree. */
        const formRoot = form.getRootNode()
        let owner = source
        let ownerRoot = owner.getRootNode()
        while (ownerRoot !== formRoot && ownerRoot.host !== undefined && ownerRoot.host !== null) {
          owner = ownerRoot.host
          ownerRoot = owner.getRootNode()
        }

        const elements = form.elements
        for (let index = 0; index < elements.length; index = index + 1) {
          if (elements[index] === owner) {
            isField = true
            break
          }
        }
      }
    }

    return isField
  }

  /*
   * The form's default button: its first submit button in tree order,
   * counting native submit buttons and mj-button type="submit" alike.
   */
  _findDefaultButton(form) {
    let defaultButton = null

    const elements = form.elements
    for (let index = 0; index < elements.length; index = index + 1) {
      const element = elements[index]
      const isNativeSubmit =
        (element.localName === "button" || element.localName === "input") &&
        element.type === "submit"
      const isMjSubmit =
        element.localName === "mj-button" && element.getAttribute("type") === "submit"

      if (isNativeSubmit === true || isMjSubmit === true) {
        defaultButton = element
        break
      }
    }

    return defaultButton
  }

  /* ----- scriptable API ----- */

  get loading() {
    const value = this.hasAttribute("loading")
    return value
  }

  set loading(value) {
    this.reflectBoolean("loading", Boolean(value))
    return
  }

  get disabled() {
    const value = this.hasAttribute("disabled")
    return value
  }

  set disabled(value) {
    this.reflectBoolean("disabled", Boolean(value))
    return
  }

  /* The form this button belongs to, or null. */
  get form() {
    const owner = this._internals !== null ? this._internals.form : null
    return owner
  }

  /* Programmatically activate the button. */
  click() {
    if (this._button !== undefined && this._button !== null) {
      this._button.click()
    }
    return
  }

  focus(options) {
    if (this._button !== undefined && this._button !== null) {
      this._button.focus(options)
    }
    return
  }
}
