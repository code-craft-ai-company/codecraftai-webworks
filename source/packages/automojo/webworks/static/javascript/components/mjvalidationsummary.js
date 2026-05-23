/*
 * mjvalidationsummary.js
 *
 * <mj-validation-summary> -- aggregates field-level validation errors from a
 * <mj-form> into a prominent, keyboard-reachable list. Each error item is a
 * link that moves focus to the invalid control. Hidden until the form fires
 * mj-invalid; cleared when mj-submit fires.
 */

import { MjElement, nextId } from "../core/mjelement.js";

const STYLES = `
:host {
  display: block;
}

:host(:not([visible]):not([always-render])) {
  display: none;
}

:host([always-render]:not([visible])) .container {
  visibility: hidden;
}

.container {
  background: var(--mj-summary-bg, var(--mj-color-danger-surface, #fdecec));
  border: 1px solid var(--mj-summary-border-color, var(--mj-color-danger, #b91c1c));
  border-radius: var(--mj-summary-border-radius, var(--mj-radius-md));
  padding: var(--mj-summary-padding, var(--mj-space-4));
  outline: none;
}

.container:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.icon-wrap {
  display: inline-flex;
  vertical-align: middle;
  margin-inline-end: var(--mj-space-2);
}

.heading {
  margin: 0 0 var(--mj-summary-gap, var(--mj-space-2));
  font-size: var(--mj-font-size-md);
  font-weight: var(--mj-font-weight-bold);
  color: var(--mj-summary-heading-color, var(--mj-color-danger, #b91c1c));
}

.list {
  margin: 0;
  padding-inline-start: var(--mj-space-5);
  display: flex;
  flex-direction: column;
  gap: var(--mj-space-1);
}

.list-item {
  font-size: var(--mj-font-size-sm);
}

.error-link {
  color: var(--mj-summary-link-color, var(--mj-accent));
  text-decoration: underline;
}

.error-link:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
`;

export class MjValidationSummary extends MjElement {
  static tagName = "mj-validation-summary";
  static styles = STYLES;
  static watched = ["for", "visible", "heading-level", "heading-text", "always-render", "manual", "focus-on-show"];

  constructor() {
    super()
    this._errors = []
    this._formRef = null
    this._formObserver = null
    this._containerId = nextId("mj-summary")
  }

  render() {
    const markup = `
      <div class="container" part="container" role="alert" tabindex="-1" id="${this._containerId}">
        <slot name="icon"></slot>
        <slot name="heading"></slot>
        <div class="heading-wrap"></div>
        <ul class="list" part="list"></ul>
      </div>
    `
    return markup
  }

  afterRender() {
    this._containerEl = this.$(".container")
    this._headingWrap = this.$(".heading-wrap")
    this._listEl = this.$(".list")
    this._syncForAttribute()
    return
  }

  onConnected() {
    this._syncForAttribute()
    return
  }

  onDisconnected() {
    this._detachFormListener()
    if (this._formObserver !== null) {
      this._formObserver.disconnect()
      this._formObserver = null
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "for") {
      this._detachFormListener()
      this._formRef = null
      this._syncForAttribute()
    }
    if (name === "visible") {
      if (newValue === null) {
        if (this._containerEl !== null) {
          this._containerEl.setAttribute("aria-hidden", "true")
        }
      }
    }
    return
  }

  _syncForAttribute() {
    const forValue = this.getAttribute("for") || ""
    if (forValue.length === 0) {
      return
    }
    const form = document.getElementById(forValue)
    if (form === null) {
      this._watchForForm(forValue)
      return
    }
    this._attachFormListeners(form)
    return
  }

  _attachFormListeners(form) {
    this._formRef = form
    const onInvalid = this._onFormInvalid.bind(this)
    const onSubmit = this._onFormSubmit.bind(this)
    form.addEventListener("mj-invalid", onInvalid)
    form.addEventListener("mj-submit", onSubmit)
    this.onTeardown(() => {
      form.removeEventListener("mj-invalid", onInvalid)
      form.removeEventListener("mj-submit", onSubmit)
    })
    return
  }

  _detachFormListener() {
    return
  }

  _onFormInvalid(event) {
    if (this.hasAttribute("manual")) {
      return
    }
    const errors = event.detail.summary || []
    const controls = event.detail.controls || []
    const mapped = controls.map((ctrl, index) => {
      const controlId = ctrl.id || ctrl.getAttribute("name") || ""
      const labelEl = ctrl.closest !== undefined ? document.querySelector(`mj-label[for="${controlId}"]`) : null
      const label = labelEl !== null && labelEl !== undefined ? labelEl.textContent.trim() : controlId
      const message = ctrl.validationMessage || (errors[index] !== undefined ? errors[index].message : "")
      return { controlId, label, message }
    })
    this.errors = mapped
    return
  }

  _onFormSubmit() {
    if (this.hasAttribute("manual") === false) {
      this.errors = []
    }
    return
  }

  _renderErrors() {
    const level = this.getAttribute("heading-level") || "2"
    const template = this.getAttribute("heading-text") || "{count} error(s) prevented this form from being submitted"
    const count = this._errors.length
    const headingText = template.split("{count}").join(String(count))

    this._headingWrap.innerHTML = `<h${level} class="heading" part="heading">${headingText}</h${level}>`

    const items = this._errors.map((err) => {
      const href = err.controlId.length > 0 ? `#${err.controlId}` : "#"
      const linkText = err.label.length > 0 ? `${err.label}: ${err.message}` : err.message
      return `<li class="list-item" part="item"><a class="error-link" part="link" href="${href}">${linkText}</a></li>`
    })
    this._listEl.innerHTML = items.join("")

    const links = this._listEl.querySelectorAll(".error-link")
    for (let index = 0; index < links.length; index = index + 1) {
      const link = links[index]
      const err = this._errors[index]
      this.listen(link, "click", (event) => {
        event.preventDefault()
        const target = document.getElementById(err.controlId)
        if (target !== null) {
          target.scrollIntoView({ block: "nearest" })
          if (typeof target.focus === "function") {
            target.focus()
          }
        }
        this.emit("mj-error-click", { controlId: err.controlId, label: err.label, message: err.message })
      })
    }
    return
  }

  _watchForForm(forValue) {
    if (this._formObserver !== null) {
      this._formObserver.disconnect()
    }
    this._formObserver = new MutationObserver(() => {
      const form = document.getElementById(forValue)
      if (form !== null) {
        this._formObserver.disconnect()
        this._formObserver = null
        this._attachFormListeners(form)
      }
    })
    this._formObserver.observe(document.body, { childList: true, subtree: true })
    this.onTeardown(() => {
      if (this._formObserver !== null) {
        this._formObserver.disconnect()
        this._formObserver = null
      }
    })
    return
  }

  /* ----- scriptable API ----- */

  get errors() {
    return this._errors
  }

  set errors(value) {
    this._errors = value !== null && value !== undefined ? value : []
    const hasErrors = this._errors.length > 0

    if (this._listEl === null) {
      return
    }

    if (hasErrors === true) {
      this._renderErrors()
      this.setAttribute("visible", "")
      if (this._containerEl !== null) {
        this._containerEl.removeAttribute("aria-hidden")
      }
      this.emit("mj-show", { errors: this._errors, count: this._errors.length })
      const focusOnShow = this.getAttribute("focus-on-show")
      if (focusOnShow !== "false" && this._containerEl !== null) {
        this._containerEl.focus()
      }
    } else {
      this._headingWrap.innerHTML = ""
      this._listEl.innerHTML = ""
      this.removeAttribute("visible")
      if (this._containerEl !== null) {
        this._containerEl.setAttribute("aria-hidden", "true")
      }
      this.emit("mj-hide", {})
    }
    return
  }

  get count() {
    return this._errors.length
  }
}
