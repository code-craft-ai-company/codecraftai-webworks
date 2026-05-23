/*
 * mjnavstepper.js
 *
 * <mj-nav-stepper> -- ordered step-indicator navigation component.
 * Renders an <ol> of steps with status indicators. Supports horizontal/vertical
 * orientation and linear/non-linear navigation.
 *
 * WAI-ARIA: ol conveys order; aria-current="step" on current; aria-disabled on upcoming in linear mode.
 */

import { MjElement, nextId } from "../core/mjelement.js";

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
  padding-bottom: var(--mj-space-6);
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
  color: #fff;
}
.step[data-status="error"] .indicator {
  background: var(--mj-nav-stepper-indicator-bg-error, var(--mj-color-danger));
  color: #fff;
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
.step[data-status="complete"] + .step .connector,
.step[data-status="complete"] > .connector {
  background: var(--mj-nav-stepper-connector-color-complete, var(--mj-color-success));
}
:host([orientation="vertical"]) .connector {
  width: var(--mj-nav-stepper-connector-width, 2px);
  height: var(--mj-space-6);
  margin: var(--mj-space-1) 0;
  margin-inline-start: calc(var(--mj-nav-stepper-indicator-size, 32px) / 2);
  position: absolute;
  top: calc(var(--mj-nav-stepper-indicator-size, 32px) + var(--mj-space-2));
  left: var(--mj-space-2);
}
:host([compact]) .label { display: none; }
`;

export class MjNavStepper extends MjElement {
  static tagName = "mj-nav-stepper";
  static styles = STYLES;
  static watched = ["current", "orientation", "linear", "compact", "label"];

  render() {
    const label = this.getAttribute("label") || "Progress";
    const markup = `
      <ol class="list" part="list" aria-label="${label}">
        <slot></slot>
      </ol>
    `;
    return markup
  }

  afterRender() {
    this._list = this.$(".list");
    this._slot = this.shadowRoot.querySelector("slot");
    this.listen(this._slot, "slotchange", this._onSlotChange.bind(this));
    this.listen(this._list, "click", this._onClick.bind(this));
    this._buildSteps();
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "current" && this._list !== undefined) {
      this._buildSteps();
    }
    return
  }

  _onSlotChange() {
    this._buildSteps();
    return
  }

  _buildSteps() {
    const steps = this._getSteps();
    const current = parseInt(this.getAttribute("current") || "0", 10);
    const linear = this.getAttribute("linear") !== "false";
    const orientation = this.getAttribute("orientation") || "horizontal";

    const existingItems = this._list.querySelectorAll("li.step, span.connector");
    existingItems.forEach(function(el) { el.remove(); });

    for (let index = 0; index < steps.length; index = index + 1) {
      const step = steps[index];
      const statusAttr = step.getAttribute("status") || "";
      let status = statusAttr;

      if (status === "" || status === "upcoming" || status === "current") {
        if (index < current) {
          status = "complete";
        } else if (index === current) {
          status = "current";
        } else {
          status = "upcoming";
        }
      }

      const isCurrent = index === current;
      const isNavigable = status === "complete" || status === "error" ||
        (linear === false && status !== "disabled");
      const isDisabled = linear === true && status === "upcoming";

      const li = document.createElement("li");
      li.className = "step";
      li.setAttribute("part", "step");
      li.dataset.status = status;
      li.dataset.index = String(index);

      const labelText = step.textContent.trim();
      const stepNum = index + 1;
      const ariaLabel = `Step ${stepNum}: ${labelText} – ${status}`;

      const btn = document.createElement("button");
      btn.className = "step-btn";
      btn.setAttribute("part", "link");
      btn.setAttribute("type", "button");
      btn.setAttribute("aria-disabled", isDisabled === true ? "true" : "false");
      btn.setAttribute("aria-label", ariaLabel);

      if (isCurrent === true) {
        btn.setAttribute("aria-current", "step");
      }

      const indicator = document.createElement("span");
      indicator.className = "indicator";
      indicator.setAttribute("part", "indicator");
      indicator.setAttribute("aria-hidden", "true");

      if (status === "complete") {
        indicator.innerHTML = `<svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="2 7 6 11 12 3"/></svg>`;
      } else if (status === "error") {
        indicator.innerHTML = `<svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><line x1="7" y1="4" x2="7" y2="8"/><circle cx="7" cy="11" r="0.5" fill="currentColor"/></svg>`;
      } else {
        indicator.textContent = String(stepNum);
      }

      const labelSpan = document.createElement("span");
      labelSpan.className = "label";
      labelSpan.setAttribute("part", "label");
      labelSpan.textContent = labelText;

      btn.appendChild(indicator);
      btn.appendChild(labelSpan);
      li.appendChild(btn);

      if (index < steps.length - 1 && orientation === "horizontal") {
        const connector = document.createElement("span");
        connector.className = "connector";
        connector.setAttribute("part", "connector");
        connector.setAttribute("aria-hidden", "true");
        li.appendChild(connector);
      }

      this._list.appendChild(li);
    }
    return
  }

  _getSteps() {
    if (this._slot === undefined || this._slot === null) {
      return []
    }
    return this._slot.assignedElements({ flatten: true })
  }

  _onClick(event) {
    const li = event.target.closest("li.step");
    if (li === null) {
      return
    }
    const btn = li.querySelector(".step-btn");
    if (btn !== null && btn.getAttribute("aria-disabled") === "true") {
      return
    }
    const index = parseInt(li.dataset.index || "0", 10);
    const previousIndex = parseInt(this.getAttribute("current") || "0", 10);

    const proceed = this.emit("mj-nav-stepper-change", {
      index: index,
      previousIndex: previousIndex,
      step: this._getSteps()[index]
    }, { cancelable: true });

    if (proceed === true) {
      this.setAttribute("current", String(index));
    }
    return
  }

  get steps() {
    return this._getSteps()
  }

  get currentStep() {
    const steps = this._getSteps();
    const current = parseInt(this.getAttribute("current") || "0", 10);
    return steps[current] || null
  }

  get completedCount() {
    const steps = this._getSteps();
    let count = 0;
    for (let i = 0; i < steps.length; i = i + 1) {
      if (steps[i].getAttribute("status") === "complete") {
        count = count + 1;
      }
    }
    return count
  }
}
