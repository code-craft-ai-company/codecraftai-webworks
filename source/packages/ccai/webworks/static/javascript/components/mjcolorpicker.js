/*
 * mjcolorpicker.js
 *
 * <mj-color-picker> — rich color chooser with hue/saturation/brightness
 * canvas, sliders, a text input, and a swatch palette.
 *
 * The colour is held as HSV plus alpha (`_hue`, `_sat`, `_val`, `_alpha`),
 * the same model the canvas draws: x is saturation, y is value. Every other
 * representation (hex, rgb(), hsl(), the `color` object) is derived from it,
 * so a value never drifts through a round trip.
 *
 * The `value` attribute is the INITIAL colour. Picking a colour updates the
 * `value` property and the form value but is not written back to the
 * attribute, so a form reset can restore what the author wrote.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { autoPosition } from "../core/overlay.js";
import { announce } from "../core/announcer.js";
import { trapFocus } from "../core/focustrap.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";

const STYLES = `
:host { display: inline-block; vertical-align: middle; }

.trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--mj-control-height-md);
  height: var(--mj-control-height-md);
  border: 2px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-md);
  cursor: pointer;
  padding: 2px;
  background: var(--mj-surface);
}
.trigger:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.trigger-swatch, .preview-swatch, .swatch, .alpha-slider {
  /* Checkerboard so a translucent colour reads as translucent. */
  background-image:
    linear-gradient(var(--swatch-color, transparent), var(--swatch-color, transparent)),
    repeating-conic-gradient(var(--mj-color-neutral-300) 0% 25%, var(--mj-color-neutral-0) 0% 50%);
  background-size: auto, 8px 8px;
}
.trigger-swatch {
  width: 100%;
  height: 100%;
  border-radius: calc(var(--mj-radius-md) - 2px);
}
:host([disabled]) .trigger,
:host(:disabled) .trigger { opacity: 0.55; cursor: not-allowed; }
:host([readonly]) .trigger { cursor: default; }
:host([invalid]) .trigger { border-color: var(--mj-color-danger); }

.popup {
  position: fixed;
  width: var(--mj-color-picker-popup-width, 16rem);
  background: var(--mj-surface-raised, var(--mj-surface));
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-color-picker-border-radius, var(--mj-radius-md));
  box-shadow: var(--mj-elevation-3);
  z-index: var(--mj-layer-popover);
  display: none;
  padding: var(--mj-space-3);
}
:host([open]) .popup { display: block; }

/* Inline: the picker surface sits in the page and there is no trigger. */
:host([inline]) { display: block; }
:host([inline]) .trigger { display: none; }
:host([inline]) .popup {
  display: block;
  position: static;
  box-shadow: none;
}

.canvas-wrapper {
  position: relative;
  height: var(--mj-color-picker-canvas-height, 10rem);
  border-radius: var(--mj-radius-sm);
  margin-block-end: var(--mj-space-2);
  cursor: crosshair;
  touch-action: none;
}
.canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border-radius: var(--mj-radius-sm);
}
.canvas-thumb {
  position: absolute;
  width: var(--mj-color-picker-thumb-size, 1rem);
  height: var(--mj-color-picker-thumb-size, 1rem);
  border-radius: var(--mj-radius-circle);
  border: 2px solid white;
  box-shadow: 0 0 0 1px rgba(0,0,0,0.5);
  transform: translate(-50%, -50%);
}
.canvas-thumb:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.slider-row, .alpha-row {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  margin-block-end: var(--mj-space-2);
}
.preview-swatch {
  width: var(--mj-control-height-sm);
  height: var(--mj-control-height-sm);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-sm);
  flex-shrink: 0;
}
.hue-slider, .alpha-slider {
  flex: 1;
  min-width: 0;
  height: var(--mj-color-picker-slider-height, 0.75rem);
  border-radius: var(--mj-radius-pill);
  -webkit-appearance: none;
  appearance: none;
  cursor: pointer;
  outline: none;
  margin: 0;
}
.hue-slider {
  background: linear-gradient(to right,
    hsl(0,100%,50%), hsl(30,100%,50%), hsl(60,100%,50%), hsl(90,100%,50%),
    hsl(120,100%,50%), hsl(150,100%,50%), hsl(180,100%,50%), hsl(210,100%,50%),
    hsl(240,100%,50%), hsl(270,100%,50%), hsl(300,100%,50%), hsl(330,100%,50%),
    hsl(360,100%,50%));
}
.alpha-slider {
  --swatch-color: transparent;
  background-image:
    linear-gradient(to right, transparent, var(--opaque-color, #000)),
    repeating-conic-gradient(var(--mj-color-neutral-300) 0% 25%, var(--mj-color-neutral-0) 0% 50%);
}
.hue-slider:focus-visible, .alpha-slider:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.hue-slider::-webkit-slider-thumb,
.alpha-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: var(--mj-color-picker-thumb-size, 1rem);
  height: var(--mj-color-picker-thumb-size, 1rem);
  border-radius: var(--mj-radius-circle);
  background: white;
  border: 2px solid var(--mj-border-strong);
  box-shadow: 0 1px 3px rgba(0,0,0,0.3);
  cursor: pointer;
}
.hue-slider::-moz-range-thumb,
.alpha-slider::-moz-range-thumb {
  width: var(--mj-color-picker-thumb-size, 1rem);
  height: var(--mj-color-picker-thumb-size, 1rem);
  border-radius: var(--mj-radius-circle);
  background: white;
  border: 2px solid var(--mj-border-strong);
  cursor: pointer;
}

.inputs-row {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  margin-block-end: var(--mj-space-2);
}
.hex-input {
  flex: 1;
  min-width: 0;
  padding: var(--mj-space-1) var(--mj-space-2);
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-sm);
  font: inherit;
  font-size: var(--mj-font-size-sm);
  font-family: var(--mj-font-mono);
  color: var(--mj-text);
  background: var(--mj-surface);
}
.hex-input:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}
.hex-input.invalid { border-color: var(--mj-color-danger); }
.eyedropper {
  flex-shrink: 0;
  height: var(--mj-control-height-sm);
  padding: 0 var(--mj-space-2);
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-sm);
  background: var(--mj-surface);
  color: var(--mj-text);
  font: inherit;
  font-size: var(--mj-font-size-sm);
  cursor: pointer;
}
.eyedropper:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.swatch-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, var(--mj-color-picker-swatch-size, 1.5rem));
  gap: var(--mj-color-picker-swatch-gap, var(--mj-space-1));
}
.swatch {
  width: var(--mj-color-picker-swatch-size, 1.5rem);
  height: var(--mj-color-picker-swatch-size, 1.5rem);
  border-radius: var(--mj-radius-sm);
  border: 2px solid var(--mj-border);
  cursor: pointer;
  padding: 0;
}
.swatch:hover { border-color: var(--mj-accent); }
.swatch:focus-visible {
  border-color: var(--mj-accent);
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: 1px;
}
.swatch[aria-pressed="true"] {
  border-color: var(--mj-accent);
  box-shadow: 0 0 0 1px var(--mj-accent);
}

:host([no-alpha]) .alpha-row { display: none; }

/* Swatch-only: the palette is the whole picker. */
:host([swatches-only]) .canvas-wrapper,
:host([swatches-only]) .slider-row,
:host([swatches-only]) .alpha-row,
:host([swatches-only]) .inputs-row { display: none; }
`;

const DEFAULT_COLOR = "#000000";

/* ----- colour maths: r, g, b are 0-255; h is 0-360; s, v, l are 0-100; a is 0-1 ----- */

function clamp(value, low, high) {
  let result = value
  if (result < low) {
    result = low
  }
  if (result > high) {
    result = high
  }
  return result
}

function rgbToHsv(r, g, b) {
  const rn = r / 255
  const gn = g / 255
  const bn = b / 255
  const max = Math.max(rn, gn, bn)
  const min = Math.min(rn, gn, bn)
  const delta = max - min

  let h = 0
  if (delta !== 0) {
    if (max === rn) {
      h = ((gn - bn) / delta) % 6
    } else if (max === gn) {
      h = (bn - rn) / delta + 2
    } else {
      h = (rn - gn) / delta + 4
    }
    h = h * 60
    if (h < 0) {
      h = h + 360
    }
  }

  const s = max === 0 ? 0 : (delta / max) * 100
  const v = max * 100
  const hsv = { h: h, s: s, v: v }
  return hsv
}

function hsvToRgb(h, s, v) {
  const hue = ((h % 360) + 360) % 360
  const sn = s / 100
  const vn = v / 100
  const c = vn * sn
  const x = c * (1 - Math.abs((hue / 60) % 2 - 1))
  const m = vn - c

  let rp = 0
  let gp = 0
  let bp = 0
  const sector = Math.floor(hue / 60)
  if (sector === 0) { rp = c; gp = x }
  else if (sector === 1) { rp = x; gp = c }
  else if (sector === 2) { gp = c; bp = x }
  else if (sector === 3) { gp = x; bp = c }
  else if (sector === 4) { rp = x; bp = c }
  else { rp = c; bp = x }

  const rgb = {
    r: Math.round((rp + m) * 255),
    g: Math.round((gp + m) * 255),
    b: Math.round((bp + m) * 255)
  }
  return rgb
}

function rgbToHsl(r, g, b) {
  const rn = r / 255
  const gn = g / 255
  const bn = b / 255
  const max = Math.max(rn, gn, bn)
  const min = Math.min(rn, gn, bn)
  const l = (max + min) / 2

  let h = 0
  let s = 0
  if (max !== min) {
    const d = max - min
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min)
    if (max === rn) {
      h = ((gn - bn) / d + (gn < bn ? 6 : 0)) / 6
    } else if (max === gn) {
      h = ((bn - rn) / d + 2) / 6
    } else {
      h = ((rn - gn) / d + 4) / 6
    }
  }

  const hsl = { h: Math.round(h * 360), s: Math.round(s * 100), l: Math.round(l * 100) }
  return hsl
}

function toHexByte(value) {
  const text = clamp(Math.round(value), 0, 255).toString(16).padStart(2, "0")
  return text
}

let parseContext = null;

/*
 * Parse a CSS colour string into `{ r, g, b, a }`, or null when it is not a
 * colour. Hex notation (#rgb, #rgba, #rrggbb, #rrggbbaa) is decoded directly;
 * anything else the browser accepts as a colour (rgb(), hsl(), names) is
 * resolved through a 2D canvas context.
 */
function parseColor(text) {
  let parsed = null

  if (typeof text !== "string") {
    return parsed
  }
  const trimmed = text.trim()

  const hexMatch = trimmed.match(/^#([0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$/)
  if (hexMatch !== null) {
    let digits = hexMatch[1]
    if (digits.length <= 4) {
      /* #rgb / #rgba: every digit is doubled. */
      digits = digits.split("").map((digit) => digit + digit).join("")
    }
    parsed = {
      r: parseInt(digits.slice(0, 2), 16),
      g: parseInt(digits.slice(2, 4), 16),
      b: parseInt(digits.slice(4, 6), 16),
      a: digits.length === 8 ? Math.round((parseInt(digits.slice(6, 8), 16) / 255) * 1000) / 1000 : 1
    }
    return parsed
  }

  const supported = typeof CSS !== "undefined" && typeof CSS.supports === "function" &&
    trimmed.length > 0 && trimmed.startsWith("#") === false && CSS.supports("color", trimmed) === true
  if (supported === true) {
    if (parseContext === null) {
      parseContext = document.createElement("canvas").getContext("2d")
    }
    if (parseContext !== null) {
      parseContext.fillStyle = "#000000"
      parseContext.fillStyle = trimmed
      const resolved = String(parseContext.fillStyle)

      if (resolved.startsWith("#") === true) {
        parsed = parseColor(resolved)
      } else {
        const numbers = resolved.match(/-?\d*\.?\d+/g)
        if (numbers !== null && numbers.length >= 3) {
          parsed = {
            r: clamp(Number(numbers[0]), 0, 255),
            g: clamp(Number(numbers[1]), 0, 255),
            b: clamp(Number(numbers[2]), 0, 255),
            a: numbers.length >= 4 ? clamp(Number(numbers[3]), 0, 1) : 1
          }
        }
      }
    }
  }

  return parsed
}

export class MjColorPicker extends FormControlMixin(MjElement) {
  static tagName = "mj-color-picker";
  static styles = STYLES;
  static watched = [
    "value", "open", "disabled", "readonly", "invalid", "no-alpha", "format",
    "swatches", "swatches-only", "eyedropper", "inline"
  ];

  constructor() {
    super()
    this._initFormControl()

    /* The colour, as drawn: hue 0-360, saturation and value 0-100, alpha 0-1. */
    this._hue = 0
    this._sat = 0
    this._val = 0
    this._alpha = 1
    this._value = DEFAULT_COLOR

    /* The colour when the popup opened; Escape goes back to it. */
    this._colorBeforeOpen = null

    this._isDragging = false
    this._disposePosition = null
    this._disposeTrap = null
    this._popupId = nextId("mj-cp-popup")
    this._triggerId = nextId("mj-cp-tr")

    /* True when the `value` attribute was applied before the first render. */
    this._valueReplayPending = false

    /* True while an ancestor <fieldset disabled> disables the control. */
    this._formDisabled = false

    this._trigger = null
    this._popup = null
  }

  render() {
    const markup = html`
      <button
        class="trigger"
        part="trigger"
        id="${this._triggerId}"
        type="button"
        aria-haspopup="dialog"
        aria-expanded="false"
        aria-controls="${this._popupId}"
        aria-label="${t("mj.colorPicker.triggerLabel")}"
      >
        <span class="trigger-swatch" part="trigger-swatch"></span>
      </button>
      <div class="popup" part="popup" id="${this._popupId}" role="dialog" aria-label="${t("mj.colorPicker.dialogLabel")}">
        <div class="canvas-wrapper" part="canvas">
          <canvas class="canvas" part="canvas-bg" width="256" height="160" aria-hidden="true"></canvas>
          <div class="canvas-thumb" part="canvas-thumb" role="slider"
            aria-label="${t("mj.colorPicker.canvasLabel")}"
            aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"
            aria-valuetext="${t("mj.colorPicker.canvasValueText", { saturation: 0, brightness: 0 })}"
            tabindex="0"
          ></div>
        </div>
        <div class="slider-row">
          <span class="preview-swatch" part="preview"></span>
          <input
            type="range"
            class="hue-slider"
            part="hue-slider"
            aria-label="${t("mj.colorPicker.hueLabel")}"
            aria-valuetext="${t("mj.colorPicker.hueValueText", { count: 0 })}"
            min="0" max="360" step="1" value="0"
          />
        </div>
        <div class="alpha-row">
          <input
            type="range"
            class="alpha-slider"
            part="alpha-slider"
            aria-label="${t("mj.colorPicker.alphaLabel")}"
            aria-valuetext="100%"
            min="0" max="100" step="1" value="100"
          />
        </div>
        <div class="inputs-row">
          <input class="hex-input" part="format-inputs" type="text" aria-label="${t("mj.colorPicker.valueLabel")}" spellcheck="false" autocomplete="off" />
          <button class="eyedropper" part="eyedropper" type="button" hidden>${t("mj.colorPicker.eyedropper")}</button>
        </div>
        <div class="swatch-grid" part="swatch-grid" role="group" aria-label="${t("mj.colorPicker.swatchesLabel")}"></div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._trigger = this.$(".trigger")
    this._popup = this.$(".popup")
    this._canvas = this.$(".canvas")
    this._canvasWrapper = this.$(".canvas-wrapper")
    this._canvasThumb = this.$(".canvas-thumb")
    this._hueSlider = this.$(".hue-slider")
    this._alphaSlider = this.$(".alpha-slider")
    this._hexInput = this.$(".hex-input")
    this._previewSwatch = this.$(".preview-swatch")
    this._swatchGrid = this.$(".swatch-grid")
    this._triggerSwatch = this.$(".trigger-swatch")
    this._eyedropperButton = this.$(".eyedropper")

    this.listen(this._trigger, "click", this._onTriggerClick.bind(this))
    this.listen(this._hueSlider, "input", this._onHueInput.bind(this))
    this.listen(this._hueSlider, "change", this._onSliderCommit.bind(this))
    this.listen(this._alphaSlider, "input", this._onAlphaInput.bind(this))
    this.listen(this._alphaSlider, "change", this._onSliderCommit.bind(this))
    this.listen(this._hexInput, "change", this._onTextChange.bind(this))
    this.listen(this._canvasWrapper, "pointerdown", this._onCanvasPointerDown.bind(this))
    this.listen(this._canvasWrapper, "pointermove", this._onCanvasPointerMove.bind(this))
    this.listen(this._canvasWrapper, "pointerup", this._onCanvasPointerUp.bind(this))
    this.listen(this._canvasWrapper, "pointercancel", this._onCanvasPointerUp.bind(this))
    this.listen(this._canvasThumb, "keydown", this._onCanvasKeydown.bind(this))
    this.listen(this._swatchGrid, "click", this._onSwatchClick.bind(this))
    this.listen(this._eyedropperButton, "click", this._onEyedropperClick.bind(this))
    this.listen(document, "click", this._onDocClick.bind(this))
    this.listen(document, "keydown", this._onDocKeydown.bind(this))

    /* Everything below paints the fresh shadow DOM from the fields. */
    this._setFormValue(this._formatValue())
    this._buildSwatches()
    this._syncEyedropper()
    this._syncEditable()
    this._syncUI()
    this._syncOpen()
    return
  }

  onDisconnected() {
    /* A removed picker must not keep tracking scroll/resize or trapping Tab. */
    this._releaseOverlay()
    this._isDragging = false
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "value") {
      if (this._rendered === false) {
        this._valueReplayPending = true
        this._applyColorString(newValue)
      } else if (this._valueReplayPending === true) {
        /* The same change was applied before the first render. */
        this._valueReplayPending = false
      } else {
        this._applyColorString(newValue)
      }
    }
    if (name === "format" || name === "no-alpha") {
      if (name === "no-alpha" && newValue !== null) {
        this._alpha = 1
      }
      this._setFormValue(this._formatValue())
      this._syncUI()
    }
    if (name === "swatches") {
      this._buildSwatches()
    }
    if (name === "eyedropper") {
      this._syncEyedropper()
    }
    if (name === "disabled" || name === "readonly") {
      this._syncEditable()
    }
    if (name === "open" || name === "inline") {
      this._syncOpen()
    }
    return
  }

  onFormReset(initial) {
    this._applyColorString(initial)
    return
  }

  onFormRestore(state) {
    if (typeof state === "string") {
      this._applyColorString(state)
    }
    return
  }

  /* An ancestor <fieldset disabled> was switched on or off. */
  onFormDisabled(disabled) {
    this._formDisabled = disabled === true
    this._syncEditable()
    return
  }

  /*
   * Take a colour from a string (attribute, property, form reset). An empty
   * or unparseable string falls back to black. No event is emitted.
   */
  _applyColorString(colorStr) {
    let parsed = parseColor(colorStr)
    if (parsed === null) {
      if (colorStr !== null && colorStr !== undefined && colorStr !== "") {
        console.warn(`mj-color-picker: "${colorStr}" is not a color; using ${DEFAULT_COLOR}`)
      }
      parsed = parseColor(DEFAULT_COLOR)
    }
    this._setRgb(parsed)
    this._setFormValue(this._formatValue())
    this._syncUI()
    return
  }

  /* Store an `{ r, g, b, a }` colour as HSV. A grey keeps the current hue. */
  _setRgb(rgb) {
    const hsv = rgbToHsv(rgb.r, rgb.g, rgb.b)
    const achromatic = hsv.s === 0 || hsv.v === 0
    if (achromatic === false) {
      this._hue = hsv.h
    }
    this._sat = hsv.s
    this._val = hsv.v
    this._alpha = this.hasAttribute("no-alpha") === true ? 1 : rgb.a
    return
  }

  _currentRgb() {
    const rgb = hsvToRgb(this._hue, this._sat, this._val)
    return rgb
  }

  /* `#rrggbb`, or `#rrggbbaa` when the colour is translucent. */
  _currentHex() {
    const rgb = this._currentRgb()
    let hex = `#${toHexByte(rgb.r)}${toHexByte(rgb.g)}${toHexByte(rgb.b)}`
    if (this._alpha < 1) {
      hex = hex + toHexByte(this._alpha * 255)
    }
    return hex
  }

  _alphaText() {
    const text = String(Math.round(this._alpha * 100) / 100)
    return text
  }

  _currentRgbString() {
    const rgb = this._currentRgb()
    let text = `rgb(${rgb.r}, ${rgb.g}, ${rgb.b})`
    if (this._alpha < 1) {
      text = `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${this._alphaText()})`
    }
    return text
  }

  _currentHslString() {
    const rgb = this._currentRgb()
    const hsl = rgbToHsl(rgb.r, rgb.g, rgb.b)
    let text = `hsl(${hsl.h}, ${hsl.s}%, ${hsl.l}%)`
    if (this._alpha < 1) {
      text = `hsla(${hsl.h}, ${hsl.s}%, ${hsl.l}%, ${this._alphaText()})`
    }
    return text
  }

  /* The value in the notation the `format` attribute asks for. */
  _formatValue() {
    const format = this.getAttribute("format") || "hex"
    let formatted = this._currentHex()
    if (format === "rgb") {
      formatted = this._currentRgbString()
    } else if (format === "hsl") {
      formatted = this._currentHslString()
    }
    return formatted
  }

  /* The `{ h, s, l, a }` object carried by events and the `color` property. */
  _colorObject() {
    const rgb = this._currentRgb()
    const hsl = rgbToHsl(rgb.r, rgb.g, rgb.b)
    const color = { h: hsl.h, s: hsl.s, l: hsl.l, a: this._alpha }
    return color
  }

  _syncUI() {
    if (this._hueSlider === undefined || this._hueSlider === null) {
      return
    }
    const rgb = this._currentRgb()
    const opaque = `rgb(${rgb.r}, ${rgb.g}, ${rgb.b})`
    const shown = `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${this._alpha})`
    const formatted = this._formatValue()

    this._triggerSwatch.style.setProperty("--swatch-color", shown)
    this._previewSwatch.style.setProperty("--swatch-color", shown)
    this._alphaSlider.style.setProperty("--opaque-color", opaque)

    const hue = Math.round(this._hue)
    this._hueSlider.value = String(hue)
    this._hueSlider.setAttribute("aria-valuetext", t("mj.colorPicker.hueValueText", { count: hue }))

    const alphaPercent = Math.round(this._alpha * 100)
    this._alphaSlider.value = String(alphaPercent)
    this._alphaSlider.setAttribute("aria-valuetext", `${alphaPercent}%`)

    /* Do not rewrite the text field under the user's caret. */
    if (this.shadowRoot.activeElement !== this._hexInput) {
      this._hexInput.value = formatted
    }
    this._hexInput.classList.remove("invalid")
    this._trigger.setAttribute("aria-label", t("mj.colorPicker.triggerLabelCurrent", { color: formatted }))

    const sat = Math.round(this._sat)
    const val = Math.round(this._val)
    this._canvasThumb.setAttribute("aria-valuenow", String(sat))
    this._canvasThumb.setAttribute("aria-valuetext", t("mj.colorPicker.canvasValueText", { saturation: sat, brightness: val }))

    this._redrawCanvas()
    this._positionThumb()
    this._markSelectedSwatch()
    return
  }

  /* White to the pure hue across, transparent to black down: the HSV plane. */
  _redrawCanvas() {
    if (this._canvas === undefined || this._canvas === null) {
      return
    }
    const ctx = this._canvas.getContext("2d")
    if (ctx === null) {
      return
    }
    const w = this._canvas.width
    const h = this._canvas.height
    const hue = Math.round(this._hue)

    const satGrad = ctx.createLinearGradient(0, 0, w, 0)
    satGrad.addColorStop(0, "#ffffff")
    satGrad.addColorStop(1, `hsl(${hue}, 100%, 50%)`)
    ctx.fillStyle = satGrad
    ctx.fillRect(0, 0, w, h)

    const valGrad = ctx.createLinearGradient(0, 0, 0, h)
    valGrad.addColorStop(0, "rgba(0,0,0,0)")
    valGrad.addColorStop(1, "rgba(0,0,0,1)")
    ctx.fillStyle = valGrad
    ctx.fillRect(0, 0, w, h)
    return
  }

  /* Percentages, so the thumb is right even while the popup is not laid out. */
  _positionThumb() {
    if (this._canvasThumb === undefined || this._canvasThumb === null) {
      return
    }
    this._canvasThumb.style.left = `${this._sat}%`
    this._canvasThumb.style.top = `${100 - this._val}%`
    return
  }

  /* Disabled by its own attribute or by an ancestor <fieldset disabled>. */
  _isDisabled() {
    const disabled = this.hasAttribute("disabled") === true || this._formDisabled === true
    return disabled
  }

  _isEditable() {
    const blocked = this._isDisabled() === true || this.hasAttribute("readonly") === true
    return blocked === false
  }

  _onCanvasPointerDown(event) {
    if (this._isEditable() === false) {
      return
    }
    if (event.button !== undefined && event.button !== 0) {
      return
    }
    event.preventDefault()
    this._isDragging = true
    if (typeof this._canvasWrapper.setPointerCapture === "function" && event.pointerId !== undefined) {
      try {
        this._canvasWrapper.setPointerCapture(event.pointerId)
      } catch (error) {
        /* Synthetic pointers cannot be captured; dragging still works inside the canvas. */
      }
    }
    this._canvasThumb.focus()
    this._updateFromCanvas(event)
    this._emitInput()
    return
  }

  _onCanvasPointerMove(event) {
    if (this._isDragging === true) {
      this._updateFromCanvas(event)
      this._emitInput()
    }
    return
  }

  _onCanvasPointerUp() {
    if (this._isDragging === true) {
      this._isDragging = false
      this._commitColor()
    }
    return
  }

  _updateFromCanvas(event) {
    const rect = this._canvasWrapper.getBoundingClientRect()
    if (rect.width === 0 || rect.height === 0) {
      return
    }
    const x = clamp(event.clientX - rect.left, 0, rect.width)
    const y = clamp(event.clientY - rect.top, 0, rect.height)
    this._sat = (x / rect.width) * 100
    this._val = (1 - y / rect.height) * 100
    this._setFormValue(this._formatValue())
    this._syncUI()
    return
  }

  _onCanvasKeydown(event) {
    if (this._isEditable() === false) {
      return
    }
    const step = event.shiftKey === true ? 10 : 1
    if (event.key === "ArrowRight") {
      this._sat = clamp(Math.round(this._sat) + step, 0, 100)
    } else if (event.key === "ArrowLeft") {
      this._sat = clamp(Math.round(this._sat) - step, 0, 100)
    } else if (event.key === "ArrowUp") {
      this._val = clamp(Math.round(this._val) + step, 0, 100)
    } else if (event.key === "ArrowDown") {
      this._val = clamp(Math.round(this._val) - step, 0, 100)
    } else {
      return
    }
    event.preventDefault()
    this._syncUI()
    this._commitColor()
    return
  }

  _onHueInput() {
    if (this._isEditable() === false) {
      this._syncUI()
      return
    }
    this._hue = parseInt(this._hueSlider.value, 10)
    this._setFormValue(this._formatValue())
    this._syncUI()
    this._emitInput()
    return
  }

  _onAlphaInput() {
    if (this._isEditable() === false) {
      this._syncUI()
      return
    }
    this._alpha = parseInt(this._alphaSlider.value, 10) / 100
    this._setFormValue(this._formatValue())
    this._syncUI()
    this._emitInput()
    return
  }

  /* A slider's native `change` fires when the drag or key step is finished. */
  _onSliderCommit() {
    if (this._isEditable() === true) {
      this._commitColor()
    }
    return
  }

  _onTextChange() {
    if (this._isEditable() === false) {
      this._syncUI()
      return
    }
    let text = this._hexInput.value.trim()
    if (/^[0-9a-fA-F]{3,8}$/.test(text) === true) {
      /* A bare hex number is accepted without its "#". */
      text = `#${text}`
    }
    const parsed = parseColor(text)
    if (parsed === null) {
      this._hexInput.classList.add("invalid")
      return
    }
    this._setRgb(parsed)
    this._hexInput.value = this._formatValue()
    this._syncUI()
    this._commitColor()
    return
  }

  _emitInput() {
    this.emit("mj-input", { value: this._formatValue(), color: this._colorObject() })
    return
  }

  /* The user settled on a colour: update the form value and announce it. */
  _commitColor() {
    const formatted = this._formatValue()
    this._setFormValue(formatted)
    this.emit("mj-change", { value: formatted, color: this._colorObject() })
    announce(t("mj.colorPicker.colorUpdated", { color: formatted }), "polite")
    return
  }

  /* The swatch colours from the `swatches` attribute (a JSON array of strings). */
  get swatchList() {
    const swatchesAttr = this.getAttribute("swatches") || ""
    let colors = []
    if (swatchesAttr.length > 0) {
      try {
        const parsed = JSON.parse(swatchesAttr)
        if (Array.isArray(parsed) === true) {
          colors = parsed.filter((entry) => typeof entry === "string")
        }
      } catch (error) {
        colors = []
      }
    }
    return colors
  }

  /*
   * Build the palette with DOM APIs: a swatch string never reaches markup,
   * and one that is not a colour is left out.
   */
  _buildSwatches() {
    if (this._swatchGrid === undefined || this._swatchGrid === null) {
      return
    }
    this._swatchGrid.textContent = ""

    const colors = this.swatchList
    for (let index = 0; index < colors.length; index = index + 1) {
      const color = colors[index]
      const parsed = parseColor(color)
      if (parsed !== null) {
        const button = document.createElement("button")
        button.type = "button"
        button.className = "swatch"
        button.setAttribute("part", "swatch")
        button.setAttribute("aria-label", color)
        button.setAttribute("aria-pressed", "false")
        button.dataset.color = color
        button.style.setProperty("--swatch-color", `rgba(${parsed.r}, ${parsed.g}, ${parsed.b}, ${parsed.a})`)
        this._swatchGrid.appendChild(button)
      }
    }

    this._swatchGrid.hidden = this._swatchGrid.children.length === 0
    if (this.hasAttribute("swatches-only") === true && this._swatchGrid.children.length === 0) {
      console.warn("mj-color-picker: swatches-only is set but there are no swatches")
    }
    this._markSelectedSwatch()
    return
  }

  _markSelectedSwatch() {
    if (this._swatchGrid === undefined || this._swatchGrid === null) {
      return
    }
    const current = this._currentHex()
    const swatches = this._swatchGrid.querySelectorAll(".swatch")
    swatches.forEach((swatch) => {
      const parsed = parseColor(swatch.dataset.color)
      let hex = ""
      if (parsed !== null) {
        hex = `#${toHexByte(parsed.r)}${toHexByte(parsed.g)}${toHexByte(parsed.b)}`
        if (parsed.a < 1) {
          hex = hex + toHexByte(parsed.a * 255)
        }
      }
      swatch.setAttribute("aria-pressed", hex === current ? "true" : "false")
    })
    return
  }

  _onSwatchClick(event) {
    const swatch = event.target.closest(".swatch")
    if (swatch === null || this._isEditable() === false) {
      return
    }
    const parsed = parseColor(swatch.dataset.color)
    if (parsed === null) {
      return
    }
    this._setRgb(parsed)
    this._syncUI()
    this._commitColor()
    if (this.hasAttribute("inline") === false) {
      this._colorBeforeOpen = null
      this._close()
    }
    return
  }

  /* The eyedropper button exists only where the browser has the API. */
  _syncEyedropper() {
    if (this._eyedropperButton === undefined || this._eyedropperButton === null) {
      return
    }
    const available = typeof window.EyeDropper === "function"
    this._eyedropperButton.hidden = (this.hasAttribute("eyedropper") === true && available === true) === false
    this._eyedropperButton.setAttribute("aria-label", t("mj.colorPicker.eyedropperLabel"))
    return
  }

  _onEyedropperClick() {
    if (this._isEditable() === false || typeof window.EyeDropper !== "function") {
      return
    }
    const dropper = new window.EyeDropper()
    dropper.open().then((result) => {
      const parsed = parseColor(result.sRGBHex)
      if (parsed !== null) {
        this._setRgb(parsed)
        this._syncUI()
        this._commitColor()
      }
    }).catch(() => {
      /* The user dismissed the eyedropper. */
    })
    return
  }

  /*
   * Mirror disabled / readonly onto the trigger. A disabled picker's trigger
   * is disabled; a readonly one stays focusable (its label still reads the
   * colour) but is marked aria-disabled and no longer announces a popup. An
   * open popup closes when the picker stops being editable.
   */
  _syncEditable() {
    if (this._trigger === undefined || this._trigger === null) {
      return
    }
    const disabled = this._isDisabled()
    const readonly = this.hasAttribute("readonly")
    this._trigger.disabled = disabled
    if (readonly === true && disabled === false) {
      this._trigger.setAttribute("aria-disabled", "true")
      this._trigger.removeAttribute("aria-haspopup")
    } else {
      this._trigger.removeAttribute("aria-disabled")
      this._trigger.setAttribute("aria-haspopup", "dialog")
    }
    if (this._isEditable() === false && this.hasAttribute("open") === true) {
      this._close()
    }
    return
  }

  /* Stop tracking the popup position and release the focus trap. */
  _releaseOverlay() {
    if (this._disposePosition !== null) {
      this._disposePosition()
      this._disposePosition = null
    }
    if (this._disposeTrap !== null) {
      /* Where focus goes on close is decided by `_syncOpen`, not by the trap. */
      this._disposeTrap({ restoreFocus: false })
      this._disposeTrap = null
    }
    return
  }

  /*
   * Bring the overlay machinery in line with the `open` attribute. Safe to
   * call before the first render (it returns) and repeatedly.
   */
  _syncOpen() {
    if (this._trigger === undefined || this._trigger === null) {
      return
    }
    const inline = this.hasAttribute("inline")
    const isOpen = this.hasAttribute("open") === true && inline === false
    this._trigger.setAttribute("aria-expanded", isOpen === true ? "true" : "false")

    if (inline === true) {
      /* The surface is part of the page: clear what a popup placement left. */
      this._releaseOverlay()
      this._popup.style.position = ""
      this._popup.style.left = ""
      this._popup.style.top = ""
    }

    if (isOpen === true) {
      if (this._disposePosition === null) {
        this._colorBeforeOpen = { hue: this._hue, sat: this._sat, val: this._val, alpha: this._alpha }
        this._disposePosition = autoPosition(this._popup, this._trigger, { placement: "bottom-start" })
        this._disposeTrap = trapFocus(this._popup)
      }
      this._syncUI()
    } else if (inline === false) {
      /*
       * Focus returns to the trigger only when it was still inside the popup
       * (Escape, a swatch pick). After an outside click focus is already
       * where the user put it and must stay there.
       */
      const wasOpen = this._disposePosition !== null
      const focusInside = this._popup.contains(this.shadowRoot.activeElement)
      this._releaseOverlay()
      if (wasOpen === true && focusInside === true) {
        this._trigger.focus()
      }
    }
    return
  }

  _open() {
    if (this._isEditable() === false || this.hasAttribute("inline") === true) {
      return
    }
    const proceed = this.emit("mj-open", {}, { cancelable: true })
    if (proceed === false) {
      return
    }
    this.setAttribute("open", "")
    return
  }

  _close() {
    if (this.hasAttribute("open") === false) {
      return
    }
    this.removeAttribute("open")
    this.emit("mj-close", {})
    return
  }

  _onTriggerClick() {
    if (this.hasAttribute("open")) {
      this._close()
    } else {
      this._open()
    }
    return
  }

  _onDocClick(event) {
    if (this.hasAttribute("open") === false) {
      return
    }
    const inside = event.composedPath().includes(this)
    if (inside === false) {
      this._close()
    }
    return
  }

  /* Escape closes the popup and goes back to the colour it opened with. */
  _onDocKeydown(event) {
    if (event.key !== "Escape" || this.hasAttribute("open") === false || this.hasAttribute("inline") === true) {
      return
    }
    event.preventDefault()

    const before = this._colorBeforeOpen
    if (before !== null) {
      const changed = before.hue !== this._hue || before.sat !== this._sat ||
        before.val !== this._val || before.alpha !== this._alpha
      if (changed === true) {
        this._hue = before.hue
        this._sat = before.sat
        this._val = before.val
        this._alpha = before.alpha
        this._syncUI()
        this._commitColor()
      }
    }

    this._close()
    this._trigger.focus()
    return
  }

  _validationAnchor() {
    const anchor = this._trigger !== undefined ? this._trigger : null
    return anchor
  }

  /* ----- scriptable API ----- */

  /* The current colour in the notation selected by `format`. */
  get value() {
    return this._value
  }

  set value(next) {
    this._applyColorString(next)
    return
  }

  get hexValue() {
    return this._currentHex()
  }

  get rgbValue() {
    return this._currentRgbString()
  }

  get hslValue() {
    return this._currentHslString()
  }

  get color() {
    return this._colorObject()
  }

  get open() {
    return this.hasAttribute("open")
  }

  set open(value) {
    if (value === true) {
      this._open()
    } else {
      this._close()
    }
    return
  }

  focus(options) {
    if (this.hasAttribute("inline") === true && this._canvasThumb !== undefined && this._canvasThumb !== null) {
      this._canvasThumb.focus(options)
    } else if (this._trigger !== undefined && this._trigger !== null) {
      this._trigger.focus(options)
    }
    return
  }
}
