/*
 * mjrating.js
 *
 * <mj-rating> -- star (or custom icon) rating input using the radiogroup
 * ARIA pattern with hover preview, half-step support, and form participation.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";

const STYLES = `
:host {
  display: block;
  font-family: var(--mj-font-sans);
  font-size: var(--mj-font-size-md);
}

.label {
  display: block;
  margin-bottom: var(--mj-space-1);
  font-size: var(--mj-font-size-sm);
  font-weight: var(--mj-font-weight-medium);
  color: var(--mj-text);
}
.label:empty { display: none; }

.group {
  display: inline-flex;
  align-items: center;
  gap: var(--mj-space-1);
  flex-wrap: wrap;
}

.item {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--mj-border-strong);
  font-size: 1.5rem;
  line-height: 1;
  transition: color var(--mj-motion-fast) var(--mj-motion-ease), transform var(--mj-motion-fast);
  outline: none;
  border-radius: var(--mj-radius-sm);
}
:host([size="sm"]) .item { font-size: 1.25rem; }
:host([size="lg"]) .item { font-size: 2rem; }

.item[aria-checked="true"] { color: var(--mj-color-warning); }
.item[data-hover] { color: var(--mj-color-warning); transform: scale(1.15); }
.item:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

:host([readonly]) .item { cursor: default; pointer-events: none; }
:host([disabled]) .item { opacity: 0.4; cursor: not-allowed; pointer-events: none; }

.value-label {
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text-muted);
  margin-inline-start: var(--mj-space-2);
}
.value-label[hidden] { display: none; }

.below { margin-top: var(--mj-space-1); }
.help { font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }
.help:empty { display: none; }
.error { font-size: var(--mj-font-size-sm); color: var(--mj-color-danger); display: none; }
.error[data-visible] { display: block; }
`;

export class MjRating extends FormControlMixin(MjElement) {
  static tagName = "mj-rating";
  static styles = STYLES;
  static watched = [
    "label", "help-text", "error-message", "value", "max",
    "required", "disabled", "readonly", "half-steps",
    "show-value-label", "icon", "icon-color", "size", "value-label-format"
  ];

  constructor() {
    super();
    this._initFormControl();
    this._hoverValue = 0;
    this._groupId = nextId("mjrt-group");
    this._helpId = nextId("mjrt-help");
    this._errorId = nextId("mjrt-error");
  }

  render() {
    const markup = `
      <label class="label" part="label"></label>
      <div class="group" part="group" role="radiogroup" id="${this._groupId}"></div>
      <span class="value-label" part="value-label" hidden></span>
      <div class="below">
        <span class="help" part="help" id="${this._helpId}"></span>
        <span class="error" part="error" id="${this._errorId}" role="alert"></span>
      </div>
    `;
    return markup;
  }

  afterRender() {
    this._labelEl = this.$(".label");
    this._groupEl = this.$(".group");
    this._valueLabelEl = this.$(".value-label");
    this._helpEl = this.$(".help");
    this._errorEl = this.$(".error");

    this._buildItems();
    this._syncAll();
    return;
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._groupEl === undefined) {
      return;
    }
    const rebuild = ["max", "half-steps", "icon"].includes(name);
    if (rebuild) {
      this._buildItems();
    }
    this._syncAll();
    return;
  }

  _getMax() {
    const m = parseInt(this.getAttribute("max") || "5", 10);
    if (m <= 0) {
      return 5;
    }
    if (m > 10) {
      console.warn("[mj-rating] max capped at 10");
      return 10;
    }
    return m;
  }

  _getCurrentValue() {
    return parseFloat(this.getAttribute("value") || "0") || 0;
  }

  _buildItems() {
    this._groupEl.innerHTML = "";
    const max = this._getMax();
    const halfSteps = this.hasAttribute("half-steps");

    for (let i = 1; i <= max; i = i + 1) {
      if (halfSteps) {
        const halfItem = this._createItem(i - 0.5);
        const fullItem = this._createItem(i);
        this._groupEl.appendChild(halfItem);
        this._groupEl.appendChild(fullItem);
      } else {
        const item = this._createItem(i);
        this._groupEl.appendChild(item);
      }
    }
    return;
  }

  _createItem(val) {
    const item = document.createElement("span");
    item.className = "item";
    item.setAttribute("part", "item");
    item.setAttribute("role", "radio");
    item.setAttribute("aria-checked", "false");
    item.setAttribute("data-value", String(val));
    item.setAttribute("aria-label", this._itemLabel(val));
    item.textContent = "★";
    item.tabIndex = -1;

    item.addEventListener("click", () => this._onItemClick(val));
    item.addEventListener("mouseenter", () => this._onItemHover(val));
    item.addEventListener("mouseleave", () => this._onItemLeave());
    item.addEventListener("keydown", (e) => this._onItemKeydown(e, val));
    return item;
  }

  _itemLabel(val) {
    const max = this._getMax();
    const icon = this.getAttribute("icon") || "star";
    if (val % 1 !== 0) {
      return `${val} ${icon}s`;
    }
    return `${val} ${val === 1 ? icon : icon + "s"} out of ${max}`;
  }

  _syncAll() {
    const label = this.getAttribute("label") || "";
    const helpText = this.getAttribute("help-text") || "";
    const disabled = this.hasAttribute("disabled");
    const readonly = this.hasAttribute("readonly");
    const required = this.hasAttribute("required");
    const showValueLabel = this.hasAttribute("show-value-label");
    const currentVal = this._getCurrentValue();
    const max = this._getMax();

    this._labelEl.textContent = label;
    this._helpEl.textContent = helpText;

    const groupEl = this.$(".group");
    if (groupEl !== null) {
      groupEl.setAttribute("aria-label", label.length > 0 ? label : "Rating");
      groupEl.setAttribute("aria-required", required ? "true" : "false");
      groupEl.setAttribute("aria-disabled", disabled ? "true" : "false");
      if (readonly) {
        groupEl.setAttribute("aria-readonly", "true");
        const fmt = this.getAttribute("value-label-format") || "{value} out of {max} stars";
        groupEl.setAttribute("aria-label", fmt.replace("{value}", String(currentVal)).replace("{max}", String(max)));
      } else {
        groupEl.removeAttribute("aria-readonly");
      }
    }

    this._updateItemStates(currentVal);
    this._updateValueLabel(currentVal, max);

    const ids = [];
    if (helpText.length > 0) {
      ids.push(this._helpId);
    }
    if (this._errorEl.hasAttribute("data-visible")) {
      ids.push(this._errorId);
    }
    if (ids.length > 0) {
      groupEl.setAttribute("aria-describedby", ids.join(" "));
    }

    this._setRovingTabindex(currentVal);
    return;
  }

  _updateItemStates(currentVal, hoverVal) {
    const displayVal = hoverVal !== undefined ? hoverVal : currentVal;
    const items = this._groupEl.querySelectorAll(".item");
    items.forEach(item => {
      const itemVal = parseFloat(item.getAttribute("data-value") || "0");
      const isFilled = itemVal <= displayVal;
      item.setAttribute("aria-checked", itemVal === currentVal ? "true" : "false");
      if (isFilled) {
        item.setAttribute("data-hover", "");
        item.style.color = "var(--mj-color-warning)";
      } else {
        item.removeAttribute("data-hover");
        item.style.color = "";
      }
      if (itemVal === currentVal) {
        item.style.color = "var(--mj-color-warning)";
      }
    });
    return;
  }

  _updateValueLabel(currentVal, max) {
    const showValueLabel = this.hasAttribute("show-value-label");
    this._valueLabelEl.hidden = !showValueLabel;
    if (showValueLabel) {
      const fmt = this.getAttribute("value-label-format") || "{value} out of {max}";
      this._valueLabelEl.textContent = fmt.replace("{value}", String(currentVal)).replace("{max}", String(max));
    }
    return;
  }

  _setRovingTabindex(currentVal) {
    const readonly = this.hasAttribute("readonly");
    const items = this._groupEl.querySelectorAll(".item");
    let found = false;
    items.forEach(item => {
      const itemVal = parseFloat(item.getAttribute("data-value") || "0");
      if (!readonly) {
        if (currentVal > 0 && itemVal === currentVal) {
          item.tabIndex = 0;
          found = true;
        } else if (!found && currentVal === 0 && itemVal === 1) {
          item.tabIndex = 0;
          found = true;
        } else {
          item.tabIndex = -1;
        }
      } else {
        item.tabIndex = -1;
      }
    });
    return;
  }

  _onItemClick(val) {
    if (this.hasAttribute("disabled") || this.hasAttribute("readonly")) {
      return;
    }
    const currentVal = this._getCurrentValue();
    const required = this.hasAttribute("required");

    let newVal = val;
    if (val === currentVal && !required) {
      newVal = 0;
    }

    const prev = currentVal;
    const notCanceled = this.emit("mj-change", { value: newVal, previousValue: prev }, { cancelable: true });
    if (!notCanceled) {
      return;
    }

    this.setAttribute("value", String(newVal));
    this._setFormValue(String(newVal));
    this._syncAll();
    return;
  }

  _onItemHover(val) {
    if (this.hasAttribute("disabled") || this.hasAttribute("readonly")) {
      return;
    }
    this._hoverValue = val;
    const currentVal = this._getCurrentValue();
    this._updateItemStates(currentVal, val);
    this.emit("mj-hover", { hoverValue: val });
    return;
  }

  _onItemLeave() {
    this._hoverValue = 0;
    const currentVal = this._getCurrentValue();
    this._updateItemStates(currentVal);
    return;
  }

  _onItemKeydown(event, val) {
    const key = event.key;
    const halfSteps = this.hasAttribute("half-steps");
    const step = halfSteps ? 0.5 : 1;
    const max = this._getMax();
    const currentVal = this._getCurrentValue();
    const required = this.hasAttribute("required");

    if (key === "ArrowRight" || key === "ArrowUp") {
      event.preventDefault();
      const next = Math.min(max, currentVal + step);
      this._onItemClick(next);
      return;
    }
    if (key === "ArrowLeft" || key === "ArrowDown") {
      event.preventDefault();
      const next = Math.max(required ? step : 0, currentVal - step);
      this._onItemClick(next);
      return;
    }
    if (key === "Home") {
      event.preventDefault();
      this._onItemClick(step);
      return;
    }
    if (key === "End") {
      event.preventDefault();
      this._onItemClick(max);
      return;
    }
    if (key === "Delete" || key === "Backspace") {
      event.preventDefault();
      if (!required) {
        this._onItemClick(0);
      }
      return;
    }
    return;
  }

  _runValidation() {
    this._refreshValidity();
    const msg = this.validationMessage;
    const overrideMsg = this.getAttribute("error-message") || "";
    const displayMsg = overrideMsg.length > 0 ? overrideMsg : msg;

    if (displayMsg.length > 0) {
      this._errorEl.textContent = displayMsg;
      this._errorEl.setAttribute("data-visible", "");
      this._groupEl.setAttribute("aria-invalid", "true");
      this.emit("mj-invalid", { validationMessage: displayMsg });
    } else {
      this._errorEl.removeAttribute("data-visible");
      this._groupEl.setAttribute("aria-invalid", "false");
    }
    return;
  }

  _customValidity() {
    const required = this.hasAttribute("required");
    const currentVal = this._getCurrentValue();
    if (required && currentVal === 0) {
      return "Please select a rating.";
    }
    return "";
  }

  onFormReset(initial) {
    const val = initial.length > 0 ? parseFloat(initial) : 0;
    this.setAttribute("value", String(val));
    this._setFormValue(String(val));
    if (this._groupEl !== undefined) {
      this._syncAll();
    }
    return;
  }

  get valueAsNumber() {
    return this._getCurrentValue();
  }

  get value() {
    return this.getAttribute("value") || "0";
  }

  set value(next) {
    const val = parseFloat(next) || 0;
    this.setAttribute("value", String(val));
    this._setFormValue(String(val));
    if (this._groupEl !== undefined) {
      this._syncAll();
    }
    return;
  }

  focus() {
    const items = this._groupEl !== undefined ? this._groupEl.querySelectorAll(".item[tabindex='0']") : [];
    if (items.length > 0) {
      items[0].focus();
    }
    return;
  }
}
