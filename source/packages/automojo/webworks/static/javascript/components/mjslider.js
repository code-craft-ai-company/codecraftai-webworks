/*
 * mjslider.js
 *
 * <mj-slider> -- single or dual-thumb range slider with tick marks,
 * value label, and full keyboard support.
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

.slider-wrap {
  position: relative;
  padding: var(--mj-space-3) 0;
  touch-action: none;
}

.track {
  position: relative;
  height: 4px;
  background: var(--mj-bg-muted);
  border-radius: var(--mj-radius-pill);
}

.fill {
  position: absolute;
  height: 100%;
  background: var(--mj-accent);
  border-radius: var(--mj-radius-pill);
  pointer-events: none;
}

.thumb {
  position: absolute;
  top: 50%;
  width: 20px;
  height: 20px;
  background: var(--mj-surface);
  border: 2px solid var(--mj-accent);
  border-radius: var(--mj-radius-circle);
  transform: translate(-50%, -50%);
  cursor: pointer;
  touch-action: none;
  transition: box-shadow var(--mj-motion-fast) var(--mj-motion-ease);
  outline: none;
}
.thumb:focus-visible {
  box-shadow: 0 0 0 var(--mj-focus-ring-width) var(--mj-focus-ring);
}
.thumb:hover {
  transform: translate(-50%, -50%) scale(1.15);
}
.thumb[aria-disabled="true"] { cursor: not-allowed; opacity: 0.55; }

.value-label {
  position: absolute;
  bottom: calc(100% + var(--mj-space-2));
  left: 50%;
  transform: translateX(-50%);
  background: var(--mj-text);
  color: var(--mj-surface);
  font-size: var(--mj-font-size-xs);
  padding: 2px var(--mj-space-1);
  border-radius: var(--mj-radius-sm);
  white-space: nowrap;
  pointer-events: none;
  display: none;
}
.thumb[data-active] .value-label { display: block; }

.ticks {
  position: absolute;
  inset-inline-start: 0;
  inset-inline-end: 0;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
}
.tick {
  position: absolute;
  width: 4px;
  height: 4px;
  background: var(--mj-border-strong);
  border-radius: var(--mj-radius-circle);
  transform: translateX(-50%) translateY(-50%);
  top: 50%;
}

.track-labels {
  display: flex;
  justify-content: space-between;
  margin-top: var(--mj-space-1);
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
}

.below { margin-top: var(--mj-space-2); }
.help { font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }
.help:empty { display: none; }
.error { font-size: var(--mj-font-size-sm); color: var(--mj-color-danger); display: none; }
.error[data-visible] { display: block; }

:host([disabled]) .slider-wrap { opacity: 0.55; pointer-events: none; }
:host([orientation="vertical"]) .slider-wrap { padding: 0 var(--mj-space-3); width: 4px; height: 200px; }
`;

export class MjSlider extends FormControlMixin(MjElement) {
  static tagName = "mj-slider";
  static styles = STYLES;
  static watched = [
    "label", "help-text", "error-message", "value", "value-end",
    "min", "max", "step", "range", "orientation",
    "disabled", "readonly", "required", "ticks", "show-value-label",
    "name-start", "name-end"
  ];

  constructor() {
    super();
    this._initFormControl();
    this._dragging = null;
    this._valueA = 0;
    this._valueB = 100;
    this._helpId = nextId("mjsl-help");
    this._errorId = nextId("mjsl-error");
    this._thumbAId = nextId("mjsl-thumb-a");
    this._thumbBId = nextId("mjsl-thumb-b");
  }

  render() {
    const markup = `
      <label class="label" part="label"></label>
      <div class="slider-wrap" part="slider-wrap">
        <div class="track" part="track">
          <div class="fill" part="fill"></div>
          <div class="ticks" part="ticks" aria-hidden="true"></div>
          <div class="thumb" part="thumb thumb-a" id="${this._thumbAId}"
            role="slider" tabindex="0"
            aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"
          >
            <span class="value-label" part="value-label"></span>
          </div>
          <div class="thumb" part="thumb thumb-b" id="${this._thumbBId}"
            role="slider" tabindex="0"
            aria-valuemin="0" aria-valuemax="100" aria-valuenow="100"
            hidden
          >
            <span class="value-label" part="value-label"></span>
          </div>
        </div>
        <div class="track-labels">
          <slot name="start-label"></slot>
          <slot name="end-label"></slot>
        </div>
      </div>
      <div class="below">
        <span class="help" part="help" id="${this._helpId}"></span>
        <span class="error" part="error" id="${this._errorId}" role="alert"></span>
      </div>
    `;
    return markup;
  }

  afterRender() {
    this._labelEl = this.$(".label");
    this._trackEl = this.$(".track");
    this._fillEl = this.$(".fill");
    this._ticksEl = this.$(".ticks");
    this._thumbA = this.$(`#${this._thumbAId}`);
    this._thumbB = this.$(`#${this._thumbBId}`);
    this._helpEl = this.$(".help");
    this._errorEl = this.$(".error");

    this._syncAll();

    this.listen(this._thumbA, "pointerdown", (e) => this._onPointerdown(e, "a"));
    this.listen(this._thumbB, "pointerdown", (e) => this._onPointerdown(e, "b"));
    this.listen(window, "pointermove", this._onPointermove.bind(this));
    this.listen(window, "pointerup", this._onPointerup.bind(this));
    this.listen(this._thumbA, "keydown", (e) => this._onKeydown(e, "a"));
    this.listen(this._thumbB, "keydown", (e) => this._onKeydown(e, "b"));
    this.listen(this._trackEl, "click", this._onTrackClick.bind(this));
    return;
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._thumbA === undefined) {
      return;
    }
    this._syncAll();
    return;
  }

  _getMin() { return parseFloat(this.getAttribute("min") || "0"); }
  _getMax() { return parseFloat(this.getAttribute("max") || "100"); }
  _getStep() { return parseFloat(this.getAttribute("step") || "1"); }

  _clamp(val) {
    return Math.min(this._getMax(), Math.max(this._getMin(), val));
  }

  _snapToStep(val) {
    const step = this._getStep();
    const min = this._getMin();
    return Math.round((val - min) / step) * step + min;
  }

  _percent(val) {
    const min = this._getMin();
    const max = this._getMax();
    if (max === min) {
      return 0;
    }
    return ((val - min) / (max - min)) * 100;
  }

  _syncAll() {
    const label = this.getAttribute("label") || "";
    const helpText = this.getAttribute("help-text") || "";
    const disabled = this.hasAttribute("disabled");
    const readonly = this.hasAttribute("readonly");
    const required = this.hasAttribute("required");
    const isRange = this.hasAttribute("range");
    const showTicks = this.hasAttribute("ticks");
    const min = this._getMin();
    const max = this._getMax();
    const step = this._getStep();

    const valAttr = this.getAttribute("value");
    const valEndAttr = this.getAttribute("value-end");
    this._valueA = valAttr !== null ? this._clamp(parseFloat(valAttr)) : min;
    this._valueB = valEndAttr !== null ? this._clamp(parseFloat(valEndAttr)) : max;

    this._labelEl.textContent = label;
    this._helpEl.textContent = helpText;

    const orientation = this.getAttribute("orientation") || "horizontal";
    this._thumbA.setAttribute("aria-orientation", orientation);
    this._thumbA.setAttribute("aria-label", isRange ? `Minimum ${label}` : label);
    this._thumbA.setAttribute("aria-valuemin", String(min));
    this._thumbA.setAttribute("aria-valuemax", String(max));
    this._thumbA.setAttribute("aria-disabled", disabled || readonly ? "true" : "false");
    this._thumbA.setAttribute("aria-required", required ? "true" : "false");

    this._thumbB.hidden = !isRange;
    if (isRange) {
      this._thumbB.setAttribute("aria-orientation", orientation);
      this._thumbB.setAttribute("aria-label", `Maximum ${label}`);
      this._thumbB.setAttribute("aria-valuemin", String(min));
      this._thumbB.setAttribute("aria-valuemax", String(max));
      this._thumbB.setAttribute("aria-disabled", disabled || readonly ? "true" : "false");
    }

    if (showTicks) {
      this._renderTicks(min, max, step);
    } else {
      this._ticksEl.innerHTML = "";
    }

    this._updatePositions();
    return;
  }

  _renderTicks(min, max, step) {
    const count = Math.round((max - min) / step) + 1;
    if (count > 50) {
      this._ticksEl.innerHTML = "";
      console.warn("[mj-slider] too many ticks; hiding tick marks");
      return;
    }
    this._ticksEl.innerHTML = "";
    for (let i = 0; i < count; i = i + 1) {
      const val = min + i * step;
      const pct = this._percent(val);
      const tick = document.createElement("span");
      tick.className = "tick";
      tick.style.insetInlineStart = `${pct}%`;
      this._ticksEl.appendChild(tick);
    }
    return;
  }

  _updatePositions() {
    const pctA = this._percent(this._valueA);
    this._thumbA.style.insetInlineStart = `${pctA}%`;
    this._thumbA.setAttribute("aria-valuenow", String(this._valueA));
    this._thumbA.setAttribute("aria-valuetext", this._formatValue(this._valueA));
    const labelA = this._thumbA.querySelector(".value-label");
    if (labelA !== null) {
      labelA.textContent = this._formatValue(this._valueA);
    }

    const isRange = this.hasAttribute("range");
    if (isRange) {
      const pctB = this._percent(this._valueB);
      this._thumbB.style.insetInlineStart = `${pctB}%`;
      this._thumbB.setAttribute("aria-valuenow", String(this._valueB));
      this._thumbB.setAttribute("aria-valuetext", this._formatValue(this._valueB));
      const labelB = this._thumbB.querySelector(".value-label");
      if (labelB !== null) {
        labelB.textContent = this._formatValue(this._valueB);
      }
      const minPct = Math.min(pctA, pctB);
      const maxPct = Math.max(pctA, pctB);
      this._fillEl.style.insetInlineStart = `${minPct}%`;
      this._fillEl.style.width = `${maxPct - minPct}%`;
    } else {
      this._fillEl.style.insetInlineStart = "0";
      this._fillEl.style.width = `${pctA}%`;
    }

    this._setFormValue(String(this._valueA));
    return;
  }

  _formatValue(val) {
    const lang = document.documentElement.lang || navigator.language || "en-US";
    return new Intl.NumberFormat(lang).format(val);
  }

  _posToValue(clientX) {
    const rect = this._trackEl.getBoundingClientRect();
    const pct = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
    const min = this._getMin();
    const max = this._getMax();
    const rawVal = min + pct * (max - min);
    return this._clamp(this._snapToStep(rawVal));
  }

  _onPointerdown(event, thumb) {
    if (this.hasAttribute("disabled") || this.hasAttribute("readonly")) {
      return;
    }
    event.preventDefault();
    this._dragging = thumb;
    const el = thumb === "a" ? this._thumbA : this._thumbB;
    el.setAttribute("data-active", "");
    el.setPointerCapture(event.pointerId);
    return;
  }

  _onPointermove(event) {
    if (this._dragging === null) {
      return;
    }
    const val = this._posToValue(event.clientX);
    const showLabel = this.hasAttribute("show-value-label");

    if (this._dragging === "a") {
      const isRange = this.hasAttribute("range");
      this._valueA = isRange ? Math.min(val, this._valueB) : val;
    } else {
      this._valueB = Math.max(val, this._valueA);
    }

    this._updatePositions();
    this.emit("mj-input", { value: this._valueA, valueEnd: this.hasAttribute("range") ? this._valueB : undefined });
    return;
  }

  _onPointerup(event) {
    if (this._dragging === null) {
      return;
    }
    const el = this._dragging === "a" ? this._thumbA : this._thumbB;
    el.removeAttribute("data-active");
    this._dragging = null;
    this.emit("mj-change", { value: this._valueA, valueEnd: this.hasAttribute("range") ? this._valueB : undefined });
    return;
  }

  _onTrackClick(event) {
    if (this.hasAttribute("disabled") || this.hasAttribute("readonly")) {
      return;
    }
    if (event.target === this._thumbA || event.target === this._thumbB) {
      return;
    }
    const val = this._posToValue(event.clientX);
    const isRange = this.hasAttribute("range");

    if (!isRange) {
      this._valueA = val;
    } else {
      const distA = Math.abs(val - this._valueA);
      const distB = Math.abs(val - this._valueB);
      if (distA <= distB) {
        this._valueA = Math.min(val, this._valueB);
      } else {
        this._valueB = Math.max(val, this._valueA);
      }
    }

    this._updatePositions();
    this.emit("mj-change", { value: this._valueA, valueEnd: isRange ? this._valueB : undefined });
    return;
  }

  _onKeydown(event, thumb) {
    if (this.hasAttribute("disabled") || this.hasAttribute("readonly")) {
      return;
    }
    const step = this._getStep();
    const min = this._getMin();
    const max = this._getMax();
    const key = event.key;
    const isRange = this.hasAttribute("range");

    let delta = 0;
    if (key === "ArrowRight" || key === "ArrowUp") {
      delta = step;
    } else if (key === "ArrowLeft" || key === "ArrowDown") {
      delta = -step;
    } else if (key === "PageUp") {
      delta = step * 10;
    } else if (key === "PageDown") {
      delta = -step * 10;
    } else if (key === "Home") {
      delta = min - (thumb === "a" ? this._valueA : this._valueB);
    } else if (key === "End") {
      delta = max - (thumb === "a" ? this._valueA : this._valueB);
    } else {
      return;
    }

    event.preventDefault();

    if (thumb === "a") {
      const next = this._clamp(this._snapToStep(this._valueA + delta));
      this._valueA = isRange ? Math.min(next, this._valueB) : next;
    } else {
      const next = this._clamp(this._snapToStep(this._valueB + delta));
      this._valueB = Math.max(next, this._valueA);
    }

    this._updatePositions();
    this.emit("mj-change", { value: this._valueA, valueEnd: isRange ? this._valueB : undefined });
    return;
  }

  onFormReset(initial) {
    const min = this._getMin();
    const max = this._getMax();
    this._valueA = initial.length > 0 ? this._clamp(parseFloat(initial)) : min;
    const initialEnd = this.getAttribute("value-end");
    this._valueB = initialEnd !== null ? this._clamp(parseFloat(initialEnd)) : max;
    if (this._trackEl !== undefined) {
      this._updatePositions();
    }
    return;
  }

  get valueAsNumber() {
    return this._valueA;
  }

  get valueStartAsNumber() {
    return this._valueA;
  }

  get valueEndAsNumber() {
    return this._valueB;
  }

  get tickLabels() {
    return this._tickLabels || [];
  }

  set tickLabels(arr) {
    this._tickLabels = Array.isArray(arr) ? arr : [];
    return;
  }

  focus() {
    if (this._thumbA !== undefined) {
      this._thumbA.focus();
    }
    return;
  }
}
