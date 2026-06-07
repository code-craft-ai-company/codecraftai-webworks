/*
 * mjwizard.js
 *
 * <mj-wizard> -- multi-step guided flow composing <mj-nav-stepper>.
 * Manages one visible step at a time; handles Back/Next/Submit navigation;
 * validates forms on Next in linear mode; moves focus on step change.
 *
 * WAI-ARIA: role=group + aria-label; live region announces step changes.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { getFocusable } from "../core/focustrap.js";
import { t } from "../core/intl.js";

const STYLES = `
:host { display: block; }

.root {
  display: flex;
  flex-direction: column;
  min-height: var(--mj-wizard-min-height, 320px);
}
:host([stepper-position="side"]) .root {
  flex-direction: row;
  align-items: flex-start;
}

.stepper-area {
  flex-shrink: 0;
}
:host([stepper-position="side"]) .stepper-area {
  width: var(--mj-wizard-stepper-width, 200px);
  padding: var(--mj-space-5);
  border-inline-end: 1px solid var(--mj-border);
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
  border-top: var(--mj-wizard-nav-bar-border, 1px solid var(--mj-border));
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

::slotted(*) { display: none; }
::slotted([data-active]) { display: block; }
`;

export class MjWizard extends MjElement {
  static tagName = "mj-wizard";
  static styles = STYLES;
  static watched = ["current", "linear", "stepper-position", "label", "next-label", "back-label", "submit-label"];

  constructor() {
    super();
    this._announceId = nextId("mj-wizard-announce");
  }

  render() {
    const label = this.getAttribute("label") || t("mj.wizard.label") || "Wizard";
    const nextLabel = this.getAttribute("next-label") || t("mj.wizard.next") || "Next";
    const backLabel = this.getAttribute("back-label") || t("mj.wizard.back") || "Back";
    const submitLabel = this.getAttribute("submit-label") || t("mj.wizard.submit") || "Submit";

    const markup = `
      <div role="group" aria-label="${label}" class="root" part="root">
        <div class="stepper-area" part="stepper">
          <mj-nav-stepper orientation="horizontal" current="0"></mj-nav-stepper>
        </div>
        <div class="content" part="content">
          <div class="panel" part="panel" tabindex="-1">
            <slot></slot>
          </div>
        </div>
        <div class="nav-bar" part="nav-bar">
          <button class="nav-btn" part="back-btn" type="button" data-action="back">
            ${backLabel}
          </button>
          <div style="display:flex;gap:var(--mj-space-3)">
            <button class="nav-btn primary" part="next-btn" type="button" data-action="next">
              ${nextLabel}
            </button>
            <button class="nav-btn primary" part="submit-btn" type="button" data-action="submit">
              ${submitLabel}
            </button>
          </div>
        </div>
        <div id="${this._announceId}" class="announce" role="status" aria-live="polite" aria-atomic="true"></div>
      </div>
    `;
    return markup
  }

  afterRender() {
    this._slot = this.shadowRoot.querySelector("slot");
    this._panel = this.$(".panel");
    this._stepper = this.$("mj-nav-stepper");
    this._announceEl = this.$(`#${this._announceId}`);
    this._backBtn = this.$("[data-action='back']");
    this._nextBtn = this.$("[data-action='next']");
    this._submitBtn = this.$("[data-action='submit']");

    this.listen(this._backBtn, "click", this._onBack.bind(this));
    this.listen(this._nextBtn, "click", this._onNext.bind(this));
    this.listen(this._submitBtn, "click", this._onSubmit.bind(this));
    this.listen(this._slot, "slotchange", this._onSlotChange.bind(this));

    this._buildSteps();
    return
  }

  _onSlotChange() {
    this._buildSteps();
    return
  }

  _buildSteps() {
    this._stepEls = this._slot.assignedElements({ flatten: true });
    this._updateStepper();
    this._showStep(parseInt(this.getAttribute("current") || "0", 10), false);
    return
  }

  _updateStepper() {
    if (this._stepper === null) {
      return
    }
    this._stepper.innerHTML = "";
    for (let i = 0; i < this._stepEls.length; i = i + 1) {
      const step = this._stepEls[i];
      const navStep = document.createElement("mj-nav-step");
      navStep.textContent = step.getAttribute("label") || step.querySelector("h2, h3, [data-title]")?.textContent.trim() || `Step ${i + 1}`;
      this._stepper.appendChild(navStep);
    }
    return
  }

  _showStep(index, fireEvent) {
    const count = this._stepEls.length;
    if (count === 0) {
      return
    }

    const clamped = Math.max(0, Math.min(index, count - 1));

    for (let i = 0; i < count; i = i + 1) {
      if (i === clamped) {
        this._stepEls[i].setAttribute("data-active", "");
        this._stepEls[i].removeAttribute("hidden");
      } else {
        this._stepEls[i].removeAttribute("data-active");
        this._stepEls[i].setAttribute("hidden", "");
      }
    }

    this.setAttribute("current", String(clamped));
    if (this._stepper !== null) {
      this._stepper.setAttribute("current", String(clamped));
    }

    const isFirst = clamped === 0;
    const isLast = clamped === count - 1;

    this._backBtn.style.visibility = isFirst === true ? "hidden" : "visible";
    this._nextBtn.style.display = isLast === true ? "none" : "inline-flex";
    this._submitBtn.style.display = isLast === true ? "inline-flex" : "none";

    const stepTitle = this._stepEls[clamped]?.getAttribute("label") || `Step ${clamped + 1}`;
    this._announceEl.textContent = "";
    window.requestAnimationFrame(() => {
      this._announceEl.textContent = `Step ${clamped + 1} of ${count}: ${stepTitle}`;
    });

    const focusable = getFocusable(this._panel);
    const target = focusable.length > 0 ? focusable[0] : this._panel;
    if (typeof target.focus === "function") {
      target.focus();
    }

    if (fireEvent === true) {
      this.emit("mj-wizard-step-enter", { index: clamped, step: this._stepEls[clamped] });
    }
    return
  }

  _validateCurrentStep() {
    const current = parseInt(this.getAttribute("current") || "0", 10);
    const stepEl = this._stepEls[current];
    if (stepEl === undefined) {
      return true
    }
    const forms = Array.from(stepEl.querySelectorAll("form"));
    if (forms.length === 0) {
      return true
    }
    for (let i = 0; i < forms.length; i = i + 1) {
      if (forms[i].checkValidity() === false) {
        forms[i].reportValidity();
        return false
      }
    }
    return true
  }

  _onBack() {
    const current = parseInt(this.getAttribute("current") || "0", 10);
    const to = current - 1;
    const proceed = this.emit("mj-wizard-before-change", {
      from: current, to: to, direction: "back"
    }, { cancelable: true });
    if (proceed === true) {
      this.emit("mj-wizard-step-leave", { index: current, step: this._stepEls[current] });
      this._showStep(to, true);
      this.emit("mj-wizard-change", { from: current, to: to, direction: "back" });
    }
    return
  }

  _onNext() {
    const linear = this.getAttribute("linear") !== "false";
    if (linear === true && this._validateCurrentStep() === false) {
      return
    }
    const current = parseInt(this.getAttribute("current") || "0", 10);
    const to = current + 1;
    const proceed = this.emit("mj-wizard-before-change", {
      from: current, to: to, direction: "next"
    }, { cancelable: true });
    if (proceed === true) {
      this.emit("mj-wizard-step-leave", { index: current, step: this._stepEls[current] });
      this._showStep(to, true);
      this.emit("mj-wizard-change", { from: current, to: to, direction: "next" });
    }
    return
  }

  _onSubmit() {
    let formData = null;
    const allForms = this.querySelectorAll("form");
    if (allForms.length > 0) {
      formData = new FormData();
      allForms.forEach(function(form) {
        new FormData(form).forEach(function(val, key) {
          formData.append(key, val);
        });
      });
    }
    const proceed = this.emit("mj-wizard-submit", { formData: formData }, { cancelable: true });
    if (proceed === true) {
      this.emit("mj-wizard-complete", {});
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "current" && this._stepEls !== undefined) {
      this._showStep(parseInt(newValue || "0", 10), false);
    }
    return
  }

  get steps() {
    return this._stepEls || []
  }

  get currentStep() {
    const steps = this._stepEls || [];
    const index = parseInt(this.getAttribute("current") || "0", 10);
    return steps[index] || null
  }

  get isFirstStep() {
    return parseInt(this.getAttribute("current") || "0", 10) === 0
  }

  get isLastStep() {
    const steps = this._stepEls || [];
    const index = parseInt(this.getAttribute("current") || "0", 10);
    return index === steps.length - 1
  }
}
