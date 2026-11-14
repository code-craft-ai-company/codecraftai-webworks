/*
 * mjnavstepper.js
 *
 * <mj-nav-stepper> -- ordered step-indicator navigation component.
 * Renders an <ol> of steps with status indicators. Supports horizontal/vertical
 * orientation and linear/non-linear navigation.
 *
 * The slotted elements are the step data (label text, `status` attribute);
 * they are not displayed themselves. The rendered list is rebuilt whenever a
 * watched attribute, the set of steps, a step's `status` or its text changes.
 *
 * WAI-ARIA: ol conveys order; aria-current="step" on current; aria-disabled on
 * steps that cannot be navigated to (upcoming in linear mode, disabled).
 */

import { MjElement } from "../core/mjelement.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";

const STYLES = `
:host { display: block; }

.list {
  display: flex;
  list-style: none;
  margin: 0; padding: 0;
  gap: 0;
}
:host([orientation="vertical"]) .list { flex-direction: column; }

.step {
  display: flex;
  align-items: center;
  flex: 1;
  position: relative;
}
:host([orientation="vertical"]) .step {
  flex-direction: column;
  align-items: flex-start;
  flex: none;
}

.step-btn {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  background: none;
  border: none;
  cursor: pointer;
  font: inherit;
  font-size: var(--mj-nav-stepper-font-size, var(--mj-font-size-sm));
  color: var(--mj-text);
  padding: var(--mj-space-2);
  border-radius: var(--mj-radius-md);
  text-decoration: none;
}
.step-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.step-btn[aria-disabled="true"] { cursor: not-allowed; opacity: 0.5; }
.step-btn[aria-current="step"] { cursor: default; }
.step-btn[aria-disabled="true"]:hover { background: none; }
.step-btn:not([aria-disabled="true"]):hover { background: var(--mj-bg-muted); }

.indicator {
  width: var(--mj-nav-stepper-indicator-size, 32px);
  height: var(--mj-nav-stepper-indicator-size, 32px);
  border-radius: var(--mj-radius-circle);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--mj-font-size-sm);
  font-weight: var(--mj-font-weight-medium);
  flex-shrink: 0;
  background: var(--mj-nav-stepper-indicator-bg-upcoming, var(--mj-bg-muted));
  color: var(--mj-text-muted);
  border: 2px solid transparent;
  transition: background var(--mj-motion-fast) var(--mj-motion-ease),
              border-color var(--mj-motion-fast) var(--mj-motion-ease);
}
.step[data-status="current"] .indicator {
  background: var(--mj-nav-stepper-indicator-bg-current, var(--mj-accent));
  color: var(--mj-text-on-accent);
  border-color: var(--mj-accent);
}
.step[data-status="complete"] .indicator {
  background: var(--mj-nav-stepper-indicator-bg-complete, var(--mj-color-success));
  color: var(--mj-nav-stepper-indicator-color-complete, var(--mj-text-on-accent));
}
.step[data-status="error"] .indicator {
  background: var(--mj-nav-stepper-indicator-bg-error, var(--mj-color-danger));
  color: var(--mj-nav-stepper-indicator-color-error, var(--mj-text-on-accent));
}

.label { font-weight: var(--mj-font-weight-medium); }
.step[data-status="current"] .label { color: var(--mj-accent); }

.connector {
  flex: 1;
  height: var(--mj-nav-stepper-connector-width, 2px);
  background: var(--mj-nav-stepper-connector-color, var(--mj-border));
  margin: 0 var(--mj-space-2);
  transition: background var(--mj-motion-fast) var(--mj-motion-ease);
}
.step[data-status="complete"] > .connector {
  background: var(--mj-nav-stepper-connector-color-complete, var(--mj-color-success));
}
:host([orientation="vertical"]) .connector {
  flex: none;
  width: var(--mj-nav-stepper-connector-width, 2px);
  height: var(--mj-space-6);
  margin: var(--mj-space-1) 0;
  /* Centred under the indicator: button padding plus half the indicator. */
  margin-inline-start: calc(var(--mj-space-2) + var(--mj-nav-stepper-indicator-size, 32px) / 2 - var(--mj-nav-stepper-connector-width, 2px) / 2);
}
:host([compact]) .label { display: none; }

/* The slotted elements are the step data; the list above is what is shown. */
.source { display: none; }
`;

/* Words used for a step's status in its accessible name. */
const STATUS_WORD_KEYS = {
  complete: "mj.navStepper.status.complete",
  current: "mj.navStepper.status.current",
  upcoming: "mj.navStepper.status.upcoming",
  error: "mj.navStepper.status.error",
  disabled: "mj.navStepper.status.disabled"
};

const COMPLETE_ICON = `<svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="2 7 6 11 12 3"/></svg>`;
const ERROR_ICON = `<svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><line x1="7" y1="4" x2="7" y2="8"/><circle cx="7" cy="11" r="0.5" fill="currentColor"/></svg>`;

export class MjNavStepper extends MjElement {
  static tagName = "mj-nav-stepper";
  static styles = STYLES;
  static watched = ["current", "orientation", "linear", "compact", "label"];

  constructor() {
    super()

    /* True while every step is complete; `mj-nav-stepper-complete` fires when it turns true. */
    this._allComplete = false
  }

  render() {
    const markup = html`
      <ol class="list" part="list"></ol>
      <div class="source"><slot></slot></div>
    `
    return markup
  }

  afterRender() {
    this._list = this.$(".list")
    this._slot = this.shadowRoot.querySelector("slot")
    this.listen(this._slot, "slotchange", this._onSlotChange.bind(this))
    this.listen(this._list, "click", this._onClick.bind(this))

    /*
     * A step's status or label can change at any time (e.g. status="error"
     * after validation). Only the light DOM is observed; the rebuild writes
     * to the shadow list, so it never triggers itself.
     */
    const observer = new MutationObserver(() => {
      this._buildSteps()
      this._announceCompletion()
    })
    observer.observe(this, {
      subtree: true,
      childList: true,
      characterData: true,
      attributes: true,
      attributeFilter: ["status"]
    })
    this.onTeardown(() => {
      observer.disconnect()
    })

    this._buildSteps()
    this._allComplete = this._isAllComplete()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._list === undefined || this._list === null) {
      return
    }

    if (name === "current") {
      /*
       * Moving `current` past the last step makes every step complete. The
       * completion is announced once per transition (`_allComplete` was set
       * in afterRender), so the replay of the initial attributes after the
       * first render announces nothing.
       */
      this._buildSteps()
      this._announceCompletion()
    } else if (
      name === "orientation" ||
      name === "linear" ||
      name === "compact" ||
      name === "label"
    ) {
      this._buildSteps()
    }
    return
  }

  _onSlotChange() {
    this._buildSteps()
    return
  }

  _currentIndex() {
    let current = parseInt(this.getAttribute("current"), 10)
    if (Number.isNaN(current) === true || current < 0) {
      current = 0
    }
    return current
  }

  _isLinear() {
    const linear = this.getAttribute("linear") !== "false"
    return linear
  }

  /*
   * The status a step is rendered with: an explicit complete / error /
   * disabled status wins; otherwise it follows from the step's position
   * relative to `current`.
   */
  _statusOf(step, index, current) {
    let status = step.getAttribute("status") || ""

    if (status !== "complete" && status !== "error" && status !== "disabled") {
      if (index < current) {
        status = "complete"
      } else if (index === current) {
        status = "current"
      } else {
        status = "upcoming"
      }
    }
    return status
  }

  /* Whether the user may navigate to a step with this status. */
  _isNavigable(status) {
    const navigable =
      status === "complete" ||
      status === "error" ||
      (this._isLinear() === false && status !== "disabled")
    return navigable
  }

  _buildSteps() {
    const steps = this._getSteps()
    const current = this._currentIndex()

    let label = this.getAttribute("label")
    if (label === null || label.length === 0) {
      label = t("mj.navStepper.label")
    }
    this._list.setAttribute("aria-label", label)

    this._list.textContent = ""

    for (let index = 0; index < steps.length; index = index + 1) {
      const step = steps[index]
      const status = this._statusOf(step, index, current)
      const isCurrent = index === current
      const isDisabled = isCurrent === false && this._isNavigable(status) === false

      const li = document.createElement("li")
      li.className = "step"
      li.setAttribute("part", "step")
      li.dataset.status = status
      li.dataset.index = String(index)

      const labelText = step.textContent.trim()
      const stepNum = index + 1
      const statusWord = STATUS_WORD_KEYS[status] !== undefined ? t(STATUS_WORD_KEYS[status]) : status
      const ariaLabel = t("mj.navStepper.stepLabel", { n: stepNum, status: statusWord, label: labelText })

      const btn = document.createElement("button")
      btn.className = "step-btn"
      btn.setAttribute("part", "link")
      btn.setAttribute("type", "button")
      btn.setAttribute("aria-disabled", isDisabled === true ? "true" : "false")
      btn.setAttribute("aria-label", ariaLabel)

      if (isDisabled === true) {
        /* Not navigable: stays in the DOM but is skipped by Tab. */
        btn.setAttribute("tabindex", "-1")
      }
      if (isCurrent === true) {
        btn.setAttribute("aria-current", "step")
      }

      const indicator = document.createElement("span")
      indicator.className = "indicator"
      indicator.setAttribute("part", "indicator")
      indicator.setAttribute("aria-hidden", "true")

      if (status === "complete") {
        indicator.innerHTML = COMPLETE_ICON
      } else if (status === "error") {
        indicator.innerHTML = ERROR_ICON
      } else {
        indicator.textContent = String(stepNum)
      }

      const labelSpan = document.createElement("span")
      labelSpan.className = "label"
      labelSpan.setAttribute("part", "label")
      labelSpan.textContent = labelText

      if (this.hasAttribute("compact") === true) {
        btn.setAttribute("title", labelText)
      }

      btn.appendChild(indicator)
      btn.appendChild(labelSpan)
      li.appendChild(btn)

      if (index < steps.length - 1) {
        const connector = document.createElement("span")
        connector.className = "connector"
        connector.setAttribute("part", "connector")
        connector.setAttribute("aria-hidden", "true")
        li.appendChild(connector)
      }

      this._list.appendChild(li)
    }
    return
  }

  _getSteps() {
    let steps = []
    if (this._slot !== undefined && this._slot !== null) {
      steps = this._slot.assignedElements({ flatten: true })
    }
    return steps
  }

  _isAllComplete() {
    const total = this._getSteps().length
    const allComplete = total > 0 && this.completedCount === total
    return allComplete
  }

  /* Emit `mj-nav-stepper-complete` once, when the last step becomes complete. */
  _announceCompletion() {
    const allComplete = this._isAllComplete()
    if (allComplete === true && this._allComplete === false) {
      const total = this._getSteps().length
      this.emit("mj-nav-stepper-complete", { completedCount: total, total: total })
    }
    this._allComplete = allComplete
    return
  }

  _onClick(event) {
    const li = event.target.closest("li.step")
    if (li === null) {
      return
    }
    const btn = li.querySelector(".step-btn")
    if (btn !== null && btn.getAttribute("aria-disabled") === "true") {
      return
    }
    const index = parseInt(li.dataset.index || "0", 10)
    const previousIndex = this._currentIndex()

    /* Activating the step that is already current changes nothing. */
    if (index === previousIndex) {
      return
    }

    const proceed = this.emit("mj-nav-stepper-change", {
      index: index,
      previousIndex: previousIndex,
      step: this._getSteps()[index]
    }, { cancelable: true })

    if (proceed === true) {
      this.setAttribute("current", String(index))
    }
    return
  }

  get steps() {
    return this._getSteps()
  }

  get currentStep() {
    const steps = this._getSteps()
    return steps[this._currentIndex()] || null
  }

  /* Number of steps rendered as complete -- explicitly, or by position before `current`. */
  get completedCount() {
    const steps = this._getSteps()
    const current = this._currentIndex()
    let count = 0
    for (let index = 0; index < steps.length; index = index + 1) {
      if (this._statusOf(steps[index], index, current) === "complete") {
        count = count + 1
      }
    }
    return count
  }
}
