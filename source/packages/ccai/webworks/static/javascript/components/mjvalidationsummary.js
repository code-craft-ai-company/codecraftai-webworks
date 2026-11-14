/*
 * mjvalidationsummary.js
 *
 * <mj-validation-summary> -- aggregates field-level validation errors from a
 * <mj-form> into a prominent, keyboard-reachable list. Each error item is a
 * link that moves focus to the invalid control. Hidden until the form fires
 * mj-invalid; cleared when the form submits or resets, and entries disappear
 * as their controls become valid.
 *
 * The form is the element named by `for`, or, without `for`, the <mj-form>
 * the summary is placed in. `manual` turns the automatic wiring off; the
 * page then assigns the `errors` property itself.
 *
 * Pruning changes the summary's height, which moves everything below it.
 * While a pointer button is held anywhere in the document the pruning is
 * postponed until the press has ended (and its click has been delivered),
 * so a button that moves would not swallow the click that blurred a field.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";
import { findById, waitForId } from "../core/aria.js";

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

.heading {
  margin: 0 0 var(--mj-summary-gap, var(--mj-space-2));
  font-size: var(--mj-font-size-md);
  font-weight: var(--mj-font-weight-bold);
  color: var(--mj-summary-heading-color, var(--mj-color-danger, #b91c1c));
}

.heading-wrap[hidden] {
  display: none;
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
  cursor: pointer;
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
    this._containerId = nextId("mj-summary")

    /* Shadow references; null until the first render. */
    this._containerEl = null
    this._headingWrap = null
    this._headingSlot = null
    this._listEl = null

    /* The form currently listened to, and how to stop waiting for it. */
    this._formRef = null
    this._stopWaiting = null

    /*
     * Incremented whenever errors are assigned (by the form or the page); a
     * clear queued by submit / reset is dropped when errors arrived after
     * it was queued.
     */
    this._errorGeneration = 0

    /* True while a pointer button is held; pruning waits for its release. */
    this._pointerHeld = false
    this._refreshPending = false
    this._refreshTimer = null

    this._onFormInvalid = this._handleFormInvalid.bind(this)
    this._onFormSubmit = this._handleFormCleared.bind(this)
    this._onFormReset = this._handleFormCleared.bind(this)
    this._onFormActivity = this._handleFormActivity.bind(this)
  }

  render() {
    const markup = html`
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
    this._headingSlot = this.$("slot[name='heading']")
    this._listEl = this.$(".list")

    /* One delegated listener serves every error link, whatever is rendered. */
    this.listen(this._listEl, "click", this._onListClick.bind(this))
    this.listen(this._headingSlot, "slotchange", this._syncHeadingSlot.bind(this))

    /* Pointer presses anywhere hold back pruning (see the file header). */
    const doc = this.ownerDocument
    this._pointerHeld = false
    this.listen(doc, "pointerdown", this._onPointerDown.bind(this), true)
    this.listen(doc, "pointerup", this._onPointerRelease.bind(this), true)
    this.listen(doc, "pointercancel", this._onPointerRelease.bind(this), true)
    this.onTeardown(() => {
      this._clearRefreshTimer()
      this._pointerHeld = false
      this._refreshPending = false
    })

    /* The shadow DOM is new: draw the errors the element already holds. */
    this._renderErrors()
    this._syncHiddenState()
    return
  }

  onConnected() {
    this._attachForm()
    return
  }

  onDisconnected() {
    this._detachForm()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._listEl === undefined || this._listEl === null) {
      return
    }

    if (name === "for" || name === "manual") {
      this._detachForm()
      this._attachForm()
    }
    if (name === "heading-text" || name === "heading-level") {
      this._renderHeading()
    }
    if (name === "visible" || name === "always-render") {
      this._syncHiddenState()
    }
    return
  }

  /* ----- form wiring ----- */

  /*
   * Listen to the form. This is the single place listeners are added, and
   * it is a no-op while a form is attached, so the lifecycle can call it
   * repeatedly without stacking handlers.
   */
  _attachForm() {
    if (this._formRef !== null || this.isConnected === false || this.hasAttribute("manual") === true) {
      return
    }

    const forValue = this.getAttribute("for") || ""
    let form = null

    if (forValue.length > 0) {
      form = findById(this, forValue)
      if (form === null) {
        if (this._stopWaiting === null) {
          this._stopWaiting = waitForId(this, forValue, () => {
            this._stopWaiting = null
            this._attachForm()
          })
        }
        return
      }
    } else {
      form = this.closest("mj-form")
    }

    if (form === null) {
      return
    }

    this._formRef = form
    form.addEventListener("mj-invalid", this._onFormInvalid)
    form.addEventListener("mj-submit", this._onFormSubmit)
    form.addEventListener("mj-reset", this._onFormReset)
    form.addEventListener("focusout", this._onFormActivity)
    form.addEventListener("change", this._onFormActivity)
    return
  }

  _detachForm() {
    if (this._stopWaiting !== null) {
      this._stopWaiting()
      this._stopWaiting = null
    }

    const form = this._formRef
    if (form !== null) {
      form.removeEventListener("mj-invalid", this._onFormInvalid)
      form.removeEventListener("mj-submit", this._onFormSubmit)
      form.removeEventListener("mj-reset", this._onFormReset)
      form.removeEventListener("focusout", this._onFormActivity)
      form.removeEventListener("change", this._onFormActivity)
      this._formRef = null
    }
    return
  }

  /*
   * The form reported invalid controls. Controls also emit `mj-invalid`
   * for their own errors and those events bubble through the form, so only
   * the form's own event is used.
   */
  _handleFormInvalid(event) {
    if (event.target !== this._formRef) {
      return
    }

    const detail = event.detail || {}
    let entries = []

    if (Array.isArray(detail.errors) === true) {
      entries = detail.errors
    } else {
      const controls = Array.isArray(detail.controls) === true ? detail.controls : []
      const summary = Array.isArray(detail.summary) === true ? detail.summary : []
      entries = controls.map((control, index) => {
        const name = control.getAttribute("name") || ""
        const fallback = summary[index] !== undefined ? summary[index].message : ""
        const entry = {
          control: control,
          controlId: control.id || name,
          name: name,
          label: control.getAttribute("label") || name,
          message: control.validationMessage || fallback
        }
        return entry
      })
    }

    this.errors = entries
    return
  }

  /*
   * A successful submit or a reset clears the summary. Both events are
   * cancelable, so the summary waits until every listener has run. A
   * submit attempt that reported new errors in the meantime (for example
   * `form.reset(); form.submit()` in one task) wins over the queued clear.
   */
  _handleFormCleared(event) {
    if (event.target !== this._formRef) {
      return
    }
    const generation = this._errorGeneration
    queueMicrotask(() => {
      if (generation !== this._errorGeneration) {
        return
      }
      if (event.defaultPrevented === false || event.type === "mj-submit") {
        if (this._errors.length > 0) {
          this.errors = []
        }
      }
    })
    return
  }

  /*
   * The user changed or left a field: drop the entries that are now valid,
   * unless a pointer press is in progress (see the file header).
   */
  _handleFormActivity() {
    if (this._pointerHeld === true) {
      this._refreshPending = true
      return
    }
    this.refresh()
    return
  }

  _onPointerDown(event) {
    this._pointerHeld = true
    return
  }

  /*
   * The press ended. Its click is dispatched right after pointerup in the
   * same input task, so the postponed pruning runs in a later task.
   */
  _onPointerRelease(event) {
    this._pointerHeld = false
    if (this._refreshPending === true && this._refreshTimer === null) {
      this._refreshTimer = setTimeout(() => {
        this._refreshTimer = null
        if (this._pointerHeld === false && this._refreshPending === true) {
          this._refreshPending = false
          this.refresh()
        }
      }, 0)
    }
    return
  }

  _clearRefreshTimer() {
    if (this._refreshTimer !== null) {
      clearTimeout(this._refreshTimer)
      this._refreshTimer = null
    }
    return
  }

  /*
   * Remove the entries whose control has become valid. Entries without a
   * control reference (set by the page) are kept.
   */
  refresh() {
    if (this._errors.length === 0) {
      return
    }

    const remaining = []
    for (let index = 0; index < this._errors.length; index = index + 1) {
      const entry = this._errors[index]
      const control = this._resolveControl(entry)
      const hasValidity = control !== null && control.validity !== null && control.validity !== undefined
      if (hasValidity === false || control.validity.valid === false) {
        remaining.push(entry)
      }
    }

    if (remaining.length !== this._errors.length) {
      this._applyErrors(remaining, false)
    }
    return
  }

  /* ----- rendering ----- */

  _syncHiddenState() {
    if (this.hasAttribute("visible") === true) {
      this._containerEl.removeAttribute("aria-hidden")
    } else {
      this._containerEl.setAttribute("aria-hidden", "true")
    }
    return
  }

  /* A slotted heading replaces the generated one. */
  _syncHeadingSlot() {
    const assigned = this._headingSlot.assignedNodes({ flatten: true })
    this._headingWrap.hidden = assigned.length > 0
    return
  }

  _renderHeading() {
    this._headingWrap.textContent = ""
    this._syncHeadingSlot()

    const count = this._errors.length
    if (count === 0) {
      return
    }

    /* Only h1-h6 can be created from the attribute; anything else is h2. */
    const parsedLevel = parseInt(this.getAttribute("heading-level") || "2", 10)
    const level = isNaN(parsedLevel) === false && parsedLevel >= 1 && parsedLevel <= 6 ? parsedLevel : 2

    /* An author `heading-text` may contain a {count} token. */
    const template = this.getAttribute("heading-text") || ""
    let text = ""
    if (template.length > 0) {
      text = template.split("{count}").join(String(count))
    } else {
      text = t("mj.validationSummary.heading", { count: count })
    }

    const heading = document.createElement(`h${level}`)
    heading.className = "heading"
    heading.setAttribute("part", "heading")
    heading.textContent = text
    this._headingWrap.appendChild(heading)
    return
  }

  _entryText(entry, field) {
    const value = entry !== null && entry !== undefined ? entry[field] : ""
    const text = value !== null && value !== undefined ? String(value) : ""
    return text
  }

  /* Build the list with DOM nodes; labels and messages are plain text. */
  _renderErrors() {
    if (this._listEl === undefined || this._listEl === null) {
      return
    }

    this._renderHeading()
    this._listEl.textContent = ""

    for (let index = 0; index < this._errors.length; index = index + 1) {
      const entry = this._errors[index]
      const label = this._entryText(entry, "label")
      const message = this._entryText(entry, "message")
      const control = this._resolveControl(entry)

      const item = document.createElement("li")
      item.className = "list-item"
      item.setAttribute("part", "item")

      const link = document.createElement("a")
      link.className = "error-link"
      link.setAttribute("part", "link")
      link.setAttribute("data-index", String(index))
      link.href = control !== null && control.id.length > 0 ? `#${encodeURIComponent(control.id)}` : "#"
      link.textContent = label.length > 0 ? `${label}: ${message}` : message

      item.appendChild(link)
      this._listEl.appendChild(item)
    }
    return
  }

  /*
   * The control an entry points at: the element reference the form put in
   * the entry, else the element with the entry's id, else the control with
   * that name inside the form.
   */
  _resolveControl(entry) {
    let control = null

    if (entry !== null && entry !== undefined) {
      if (entry.control instanceof Element) {
        control = entry.control
      } else {
        const controlId = this._entryText(entry, "controlId")
        if (controlId.length > 0) {
          control = findById(this, controlId)
          if (control === null) {
            const scope = this._formRef !== null ? this._formRef : this.getRootNode()
            control = scope.querySelector(`[name="${CSS.escape(controlId)}"]`)
          }
        }
      }
    }
    return control
  }

  _onListClick(event) {
    const link = event.target.closest(".error-link")
    if (link === null) {
      return
    }
    event.preventDefault()

    const entry = this._errors[parseInt(link.getAttribute("data-index"), 10)]
    if (entry === undefined) {
      return
    }

    const control = this._resolveControl(entry)
    if (control !== null) {
      control.scrollIntoView({ block: "nearest" })
      if (typeof control.focus === "function") {
        control.focus()
      }
    }

    this.emit("mj-error-click", {
      controlId: this._entryText(entry, "controlId"),
      label: this._entryText(entry, "label"),
      message: this._entryText(entry, "message"),
      control: control
    })
    return
  }

  /*
   * Store and draw `entries`. `takeFocus` is true when a submit attempt
   * produced them; pruning entries must never move focus.
   */
  _applyErrors(entries, takeFocus) {
    const hadErrors = this._errors.length > 0
    this._errors = Array.isArray(entries) === true ? entries.slice() : []
    const hasErrors = this._errors.length > 0

    if (this._listEl === undefined || this._listEl === null) {
      /* Not rendered yet: afterRender draws the stored errors. */
      this.reflectBoolean("visible", hasErrors)
      return
    }

    this._renderErrors()

    if (hasErrors === true) {
      this.setAttribute("visible", "")
      this._syncHiddenState()
      if (takeFocus === true) {
        this.emit("mj-show", { errors: this._errors, count: this._errors.length })
        if (this.getAttribute("focus-on-show") !== "false") {
          this._containerEl.focus()
        }
      }
    } else {
      this.removeAttribute("visible")
      this._syncHiddenState()
      if (hadErrors === true) {
        this.emit("mj-hide", {})
      }
    }
    return
  }

  /* ----- scriptable API ----- */

  get errors() {
    return this._errors
  }

  /*
   * Entries are { label, message, controlId } and may carry `control`, the
   * element itself, which is used for focus when the control has no id.
   */
  set errors(value) {
    this._errorGeneration = this._errorGeneration + 1
    this._applyErrors(value, true)
    return
  }

  get count() {
    return this._errors.length
  }
}
