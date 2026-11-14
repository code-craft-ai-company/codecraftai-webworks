/*
 * mjwizard.js
 *
 * <mj-wizard> -- multi-step guided flow composing <mj-nav-stepper>.
 * Manages one visible step at a time; handles Back/Next/Submit navigation;
 * validates the current step on Next and Submit in linear mode; moves focus
 * into the new step when the user changes step.
 *
 * Every user-driven step change -- the built-in buttons, a click on the
 * embedded stepper, and the public next() / back() / goTo() methods -- takes
 * the same path: validation, the cancelable `mj-wizard-before-change`, then
 * the step switch and its events.
 *
 * WAI-ARIA: role=group + aria-label; live region announces step changes.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { getFocusable } from "../core/focustrap.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";

const STYLES = `
:host { display: block; }

.root {
  display: flex;
  flex-direction: column;
  min-height: var(--mj-wizard-min-height, 320px);
}
/*
 * Side stepper: a two-column grid. The stepper fills the start column over
 * the full height; the step content and, under it, the button bar share the
 * end column.
 */
:host([stepper-position="side"]) .root {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  grid-template-rows: minmax(0, 1fr) auto;
}

.stepper-area {
  flex-shrink: 0;
}
:host([stepper-position="side"]) .stepper-area {
  grid-column: 1;
  grid-row: 1 / span 2;
  width: var(--mj-wizard-stepper-width, 200px);
  padding: var(--mj-space-5);
  border-inline-end: 1px solid var(--mj-border);
}
:host([stepper-position="side"]) .content {
  grid-column: 2;
  grid-row: 1;
}
:host([stepper-position="side"]) .nav-bar {
  grid-column: 2;
  grid-row: 2;
}
:host([stepper-position="none"]) .stepper-area { display: none; }

.content {
  flex: 1;
  padding: var(--mj-wizard-content-padding, var(--mj-space-6));
  overflow: auto;
}

.nav-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--mj-wizard-nav-bar-padding, var(--mj-space-4) var(--mj-space-6));
  border-block-start: var(--mj-wizard-nav-bar-border, 1px solid var(--mj-border));
  flex-shrink: 0;
}

.nav-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--mj-space-2);
  padding: 0 var(--mj-space-4);
  min-height: var(--mj-control-height-md);
  font: inherit;
  font-weight: var(--mj-font-weight-medium);
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-md);
  cursor: pointer;
  background: var(--mj-surface);
  color: var(--mj-text);
  transition: background var(--mj-motion-fast) var(--mj-motion-ease);
}
.nav-btn:hover { background: var(--mj-bg-muted); }
.nav-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.nav-btn[aria-disabled="true"] { opacity: 0.55; cursor: not-allowed; }
.nav-btn[hidden] { display: none; }
.nav-btn.back[data-first] { visibility: hidden; }
.forward { display: flex; gap: var(--mj-space-3); }
.nav-btn.primary {
  background: var(--mj-accent);
  color: var(--mj-text-on-accent);
  border-color: var(--mj-accent);
}
.nav-btn.primary:hover { background: var(--mj-accent-hover); border-color: var(--mj-accent-hover); }

.announce {
  position: absolute;
  width: 1px; height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  clip-path: inset(50%);
  white-space: nowrap;
}

/* Steps: only the active one shows. The actions slot is not affected. */
slot:not([name])::slotted(*) { display: none; }
slot:not([name])::slotted([data-active]) { display: block; }
.panel { outline: none; }
`;

export class MjWizard extends MjElement {
  static tagName = "mj-wizard";
  static styles = STYLES;
  static watched = ["current", "linear", "stepper-position", "label", "next-label", "back-label", "submit-label"];

  constructor() {
    super()
    this._announceId = nextId("mj-wizard-announce")
    this._stepEls = []

    /* Index of the step being shown; -1 until the first step is shown. */
    this._currentIndex = -1
  }

  render() {
    /*
     * Labels are applied in afterRender through textContent / setAttribute.
     * The built-in buttons are the fallback content of the `actions` slot,
     * so slotting a custom button bar replaces them.
     */
    const markup = html`
      <div role="group" class="root" part="root">
        <div class="stepper-area" part="stepper">
          <mj-nav-stepper current="0"></mj-nav-stepper>
        </div>
        <div class="content" part="content">
          <div class="panel" part="panel" tabindex="-1">
            <slot></slot>
          </div>
        </div>
        <div class="nav-bar" part="nav-bar">
          <slot name="actions">
            <button class="nav-btn back" part="back-btn" type="button" data-action="back"></button>
            <div class="forward">
              <button class="nav-btn primary" part="next-btn" type="button" data-action="next"></button>
              <button class="nav-btn primary" part="submit-btn" type="button" data-action="submit"></button>
            </div>
          </slot>
        </div>
        <div id="${this._announceId}" class="announce" role="status" aria-live="polite" aria-atomic="true"></div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._root = this.$(".root")
    this._slot = this.shadowRoot.querySelector("slot:not([name])")
    this._panel = this.$(".panel")
    this._stepper = this.$("mj-nav-stepper")
    this._announceEl = this.$(".announce")
    this._backBtn = this.$("[data-action='back']")
    this._nextBtn = this.$("[data-action='next']")
    this._submitBtn = this.$("[data-action='submit']")

    this.listen(this._backBtn, "click", this._onBack.bind(this))
    this.listen(this._nextBtn, "click", this._onNext.bind(this))
    this.listen(this._submitBtn, "click", this._onSubmit.bind(this))
    this.listen(this._slot, "slotchange", this._onSlotChange.bind(this))
    this.listen(this._stepper, "mj-nav-stepper-change", this._onStepperChange.bind(this))

    this._syncLabels()
    this._syncStepperOptions()
    this._buildSteps()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._root === undefined || this._root === null) {
      return
    }

    if (name === "current") {
      /*
       * `_showStep` reflects the index back to this attribute; the comparison
       * with the index already showing ends that round trip.
       */
      const index = this._clampIndex(this._parseIndex(newValue))
      if (index !== this._currentIndex) {
        this._showStep(index, { moveFocus: false, announce: true })
      }
    } else if (name === "linear" || name === "stepper-position") {
      this._syncStepperOptions()
    } else if (
      name === "label" ||
      name === "next-label" ||
      name === "back-label" ||
      name === "submit-label"
    ) {
      this._syncLabels()
    }
    return
  }

  _labelFor(attribute, key) {
    let label = this.getAttribute(attribute)
    if (label === null || label.length === 0) {
      label = t(key)
    }
    return label
  }

  _syncLabels() {
    this._root.setAttribute("aria-label", this._labelFor("label", "mj.wizard.label"))
    this._backBtn.textContent = this._labelFor("back-label", "mj.wizard.back")
    this._nextBtn.textContent = this._labelFor("next-label", "mj.wizard.next")
    this._submitBtn.textContent = this._labelFor("submit-label", "mj.wizard.submit")
    return
  }

  /* The embedded stepper follows the wizard's layout and navigation mode. */
  _syncStepperOptions() {
    const side = this.getAttribute("stepper-position") === "side"
    this._stepper.setAttribute("orientation", side === true ? "vertical" : "horizontal")
    this._stepper.setAttribute("linear", this._isLinear() === true ? "true" : "false")
    return
  }

  _isLinear() {
    const linear = this.getAttribute("linear") !== "false"
    return linear
  }

  _parseIndex(value) {
    let index = parseInt(value, 10)
    if (Number.isNaN(index) === true) {
      index = 0
    }
    return index
  }

  _clampIndex(index) {
    const count = this._stepEls.length
    const clamped = Math.max(0, Math.min(index, count - 1))
    return clamped
  }

  _onSlotChange() {
    this._buildSteps()
    return
  }

  _buildSteps() {
    this._stepEls = this._slot.assignedElements({ flatten: true })
    this._updateStepper()
    this._showStep(this._parseIndex(this.getAttribute("current")), { moveFocus: false, announce: false })
    return
  }

  _stepTitle(index) {
    const step = this._stepEls[index]
    let title = ""

    if (step !== undefined) {
      const labelAttr = step.getAttribute("label")
      if (labelAttr !== null && labelAttr.length > 0) {
        title = labelAttr
      } else {
        const heading = step.querySelector("h2, h3, [data-title]")
        if (heading !== null) {
          title = heading.textContent.trim()
        }
      }
    }

    if (title.length === 0) {
      title = t("mj.wizard.stepFallback", { n: index + 1 })
    }
    return title
  }

  _updateStepper() {
    this._stepper.textContent = ""
    for (let index = 0; index < this._stepEls.length; index = index + 1) {
      const navStep = document.createElement("mj-nav-step")
      navStep.textContent = this._stepTitle(index)
      this._stepper.appendChild(navStep)
    }
    return
  }

  /*
   * Show the step at `index` (clamped). `options.moveFocus` is true only for
   * a step change the user made; `options.announce` is false for the initial
   * render and slot changes, which are not step changes.
   */
  _showStep(index, options) {
    const count = this._stepEls.length
    if (count === 0) {
      this._currentIndex = -1
      return
    }

    const clamped = this._clampIndex(index)
    this._currentIndex = clamped

    for (let position = 0; position < count; position = position + 1) {
      const step = this._stepEls[position]
      if (position === clamped) {
        step.setAttribute("data-active", "")
        step.removeAttribute("hidden")
      } else {
        step.removeAttribute("data-active")
        step.setAttribute("hidden", "")
      }
    }

    const reflected = String(clamped)
    if (this.getAttribute("current") !== reflected) {
      this.setAttribute("current", reflected)
    }
    if (this._stepper.getAttribute("current") !== reflected) {
      this._stepper.setAttribute("current", reflected)
    }

    const isFirst = clamped === 0
    const isLast = clamped === count - 1

    this._backBtn.toggleAttribute("data-first", isFirst)
    this._nextBtn.hidden = isLast === true
    this._submitBtn.hidden = isLast === false

    if (options.announce === true) {
      const announcement = t("mj.wizard.stepAnnouncement", { n: clamped + 1, total: count, title: this._stepTitle(clamped) })
      this._announceEl.textContent = ""
      window.requestAnimationFrame(() => {
        this._announceEl.textContent = announcement
      })
    }

    if (options.moveFocus === true) {
      const focusable = getFocusable(this._panel)
      const target = focusable.length > 0 ? focusable[0] : this._panel
      if (typeof target.focus === "function") {
        target.focus()
      }
    }
    return
  }

  /*
   * The elements of a step that can be validated: the step itself when it is
   * a form (or a form control), and every form, native control and mj-* form
   * control inside it.
   */
  _validatables(stepEl) {
    const found = []
    const candidates = [stepEl].concat(Array.from(stepEl.querySelectorAll("*")))

    for (let index = 0; index < candidates.length; index = index + 1) {
      const candidate = candidates[index]
      if (typeof candidate.checkValidity === "function") {
        found.push(candidate)
      }
    }
    return found
  }

  /* Check a step; with `report` true the first invalid element shows its message. */
  _validateStep(index, report) {
    let valid = true
    const stepEl = this._stepEls[index]

    if (stepEl !== undefined) {
      const validatables = this._validatables(stepEl)
      for (let position = 0; position < validatables.length && valid === true; position = position + 1) {
        const element = validatables[position]
        if (element.checkValidity() === false) {
          valid = false
          if (report === true && typeof element.reportValidity === "function") {
            element.reportValidity()
          }
        }
      }
    }
    return valid
  }

  /*
   * The single path for a user-driven step change. Returns true when the
   * wizard moved to `to`.
   */
  _navigate(to, direction) {
    const from = this._currentIndex
    let moved = false

    if (from >= 0 && to >= 0 && to < this._stepEls.length && to !== from) {
      let allowed = true

      /* Moving forward in linear mode requires the current step to be valid. */
      if (to > from && this._isLinear() === true) {
        allowed = this._validateStep(from, true)
      }

      if (allowed === true) {
        allowed = this.emit("mj-wizard-before-change", {
          from: from, to: to, direction: direction
        }, { cancelable: true })
      }

      if (allowed === true) {
        this.emit("mj-wizard-step-leave", { index: from, step: this._stepEls[from] })
        this._showStep(to, { moveFocus: true, announce: true })
        this.emit("mj-wizard-step-enter", { index: to, step: this._stepEls[to] })
        this.emit("mj-wizard-change", { from: from, to: to, direction: direction })
        moved = true
      }
    }
    return moved
  }

  _onBack() {
    this.back()
    return
  }

  _onNext() {
    this.next()
    return
  }

  /*
   * A click on the embedded stepper. The wizard owns `current`, so the
   * stepper's own change is always canceled and the request goes through
   * `_navigate`; the internal event does not leave the wizard.
   */
  _onStepperChange(event) {
    event.preventDefault()
    event.stopPropagation()
    this._navigate(event.detail.index, "jump")
    return
  }

  _onSubmit() {
    this.submit()
    return
  }

  /* Go to the next step. Returns true when the step changed. */
  next() {
    const moved = this._navigate(this._currentIndex + 1, "next")
    return moved
  }

  /* Go to the previous step. Returns true when the step changed. */
  back() {
    const moved = this._navigate(this._currentIndex - 1, "back")
    return moved
  }

  /* Jump to the step at `index`. Returns true when the step changed. */
  goTo(index) {
    const moved = this._navigate(this._parseIndex(index), "jump")
    return moved
  }

  /*
   * Submit the wizard: validate the current step (linear mode), then emit the
   * cancelable `mj-wizard-submit` and, when not canceled, `mj-wizard-complete`.
   * Returns true when the wizard completed.
   */
  submit() {
    let completed = false

    let allowed = true
    if (this._isLinear() === true && this._currentIndex >= 0) {
      allowed = this._validateStep(this._currentIndex, true)
    }

    if (allowed === true) {
      let formData = null
      const allForms = this.querySelectorAll("form")
      if (allForms.length > 0) {
        formData = new FormData()
        allForms.forEach(function(form) {
          new FormData(form).forEach(function(val, key) {
            formData.append(key, val)
          })
        })
      }

      const proceed = this.emit("mj-wizard-submit", { formData: formData }, { cancelable: true })
      if (proceed === true) {
        this.emit("mj-wizard-complete", {})
        completed = true
      }
    }
    return completed
  }

  get steps() {
    return this._stepEls.slice()
  }

  get currentStep() {
    return this._stepEls[this._currentIndex] || null
  }

  get isFirstStep() {
    return this._currentIndex <= 0
  }

  get isLastStep() {
    return this._currentIndex === this._stepEls.length - 1
  }

  /* True when the current step's forms and controls are all valid (nothing is reported). */
  get valid() {
    const valid = this._validateStep(this._currentIndex, false)
    return valid
  }
}
