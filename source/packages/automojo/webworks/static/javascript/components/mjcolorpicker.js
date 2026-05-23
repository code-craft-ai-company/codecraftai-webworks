/*
 * mjcolorpicker.js
 *
 * <mj-color-picker> — rich color chooser with hue/saturation/brightness
 * canvas, sliders, text inputs, and swatch palette.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { autoPosition } from "../core/overlay.js";
import { announce } from "../core/announcer.js";
import { trapFocus } from "../core/focustrap.js";

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
.trigger-swatch {
  width: 100%;
  height: 100%;
  border-radius: calc(var(--mj-radius-md) - 2px);
  background: var(--current-color, #000);
}
:host([disabled]) .trigger { opacity: 0.55; cursor: not-allowed; }
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

.canvas-wrapper {
  position: relative;
  height: var(--mj-color-picker-canvas-height, 10rem);
  border-radius: var(--mj-radius-sm);
  margin-bottom: var(--mj-space-2);
  overflow: hidden;
  cursor: crosshair;
}
.canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}
.canvas-thumb {
  position: absolute;
  width: var(--mj-color-picker-thumb-size, 1rem);
  height: var(--mj-color-picker-thumb-size, 1rem);
  border-radius: 50%;
  border: 2px solid white;
  box-shadow: 0 0 0 1px rgba(0,0,0,0.3);
  transform: translate(-50%, -50%);
  pointer-events: none;
}

.slider-row {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  margin-bottom: var(--mj-space-2);
}
.preview-swatch {
  width: var(--mj-control-height-sm);
  height: var(--mj-color-picker-slider-height, 0.75rem);
  border-radius: var(--mj-radius-sm);
  flex-shrink: 0;
}
.hue-slider, .alpha-slider {
  flex: 1;
  height: var(--mj-color-picker-slider-height, 0.75rem);
  border-radius: var(--mj-radius-pill);
  -webkit-appearance: none;
  appearance: none;
  cursor: pointer;
  outline: none;
}
.hue-slider {
  background: linear-gradient(to right,
    hsl(0,100%,50%), hsl(30,100%,50%), hsl(60,100%,50%), hsl(90,100%,50%),
    hsl(120,100%,50%), hsl(150,100%,50%), hsl(180,100%,50%), hsl(210,100%,50%),
    hsl(240,100%,50%), hsl(270,100%,50%), hsl(300,100%,50%), hsl(330,100%,50%),
    hsl(360,100%,50%));
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
  border-radius: 50%;
  background: white;
  border: 2px solid var(--mj-border-strong);
  box-shadow: 0 1px 3px rgba(0,0,0,0.3);
  cursor: pointer;
}

.inputs-row {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  margin-bottom: var(--mj-space-2);
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

.swatch-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, var(--mj-color-picker-swatch-size, 1.5rem));
  gap: var(--mj-color-picker-swatch-gap, var(--mj-space-1));
}
.swatch {
  width: var(--mj-color-picker-swatch-size, 1.5rem);
  height: var(--mj-color-picker-swatch-size, 1.5rem);
  border-radius: var(--mj-radius-sm);
  border: 2px solid transparent;
  cursor: pointer;
  padding: 0;
}
.swatch:hover, .swatch:focus-visible {
  border-color: var(--mj-accent);
  outline: none;
}
.swatch[aria-selected="true"] { border-color: var(--mj-accent); }

:host(:not([no-alpha])) .alpha-row { display: flex; align-items: center; gap: var(--mj-space-2); margin-bottom: var(--mj-space-2); }
:host([no-alpha]) .alpha-row { display: none; }
`;

function hexToHsl(hex) {
  let r = 0
  let g = 0
  let b = 0
  const clean = hex.replace("#", "")
  if (clean.length === 6) {
    r = parseInt(clean.slice(0, 2), 16) / 255
    g = parseInt(clean.slice(2, 4), 16) / 255
    b = parseInt(clean.slice(4, 6), 16) / 255
  }
  const max = Math.max(r, g, b)
  const min = Math.min(r, g, b)
  const l = (max + min) / 2
  let h = 0
  let s = 0
  if (max !== min) {
    const d = max - min
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min)
    if (max === r) {
      h = ((g - b) / d + (g < b ? 6 : 0)) / 6
    } else if (max === g) {
      h = ((b - r) / d + 2) / 6
    } else {
      h = ((r - g) / d + 4) / 6
    }
  }
  return { h: Math.round(h * 360), s: Math.round(s * 100), l: Math.round(l * 100), a: 1 }
}

function hslToHex(h, s, l) {
  const hNorm = h / 360
  const sNorm = s / 100
  const lNorm = l / 100
  const c = (1 - Math.abs(2 * lNorm - 1)) * sNorm
  const x = c * (1 - Math.abs((hNorm * 6) % 2 - 1))
  const m = lNorm - c / 2
  let rp = 0
  let gp = 0
  let bp = 0
  const sector = Math.floor(hNorm * 6)
  if (sector === 0) { rp = c; gp = x }
  else if (sector === 1) { rp = x; gp = c }
  else if (sector === 2) { gp = c; bp = x }
  else if (sector === 3) { gp = x; bp = c }
  else if (sector === 4) { rp = x; bp = c }
  else { rp = c; bp = x }
  const r = Math.round((rp + m) * 255)
  const g = Math.round((gp + m) * 255)
  const b = Math.round((bp + m) * 255)
  const toHex = (n) => n.toString(16).padStart(2, "0")
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`
}

export class MjColorPicker extends FormControlMixin(MjElement) {
  static tagName = "mj-color-picker";
  static styles = STYLES;
  static watched = ["value", "open", "disabled", "invalid", "no-alpha", "format", "swatches-only", "eyedropper"];

  constructor() {
    super()
    this._initFormControl()
    this._hsl = { h: 0, s: 0, l: 0, a: 1 }
    this._sat = 0
    this._bri = 100
    this._isDragging = false
    this._disposePosition = null
    this._disposeTrap = null
    this._popupId = nextId("mj-cp-popup")
    this._triggerId = nextId("mj-cp-tr")
  }

  render() {
    const markup = `
      <button
        class="trigger"
        part="trigger"
        id="${this._triggerId}"
        type="button"
        aria-haspopup="dialog"
        aria-expanded="false"
        aria-label="Color picker"
      >
        <span class="trigger-swatch" part="trigger-swatch"></span>
      </button>
      <div class="popup" part="popup" id="${this._popupId}" role="dialog" aria-label="Choose a color">
        <div class="canvas-wrapper" part="canvas">
          <canvas class="canvas" part="canvas-bg" aria-hidden="true"></canvas>
          <div class="canvas-thumb" part="canvas-thumb" role="slider"
            aria-label="Saturation and brightness"
            aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"
            tabindex="0"
          ></div>
        </div>
        <div class="slider-row">
          <span class="preview-swatch" part="preview"></span>
          <input
            type="range"
            class="hue-slider"
            part="hue-slider"
            role="slider"
            aria-label="Hue"
            aria-valuemin="0"
            aria-valuemax="360"
            aria-valuenow="0"
            min="0" max="360" step="1" value="0"
          />
        </div>
        <div class="alpha-row">
          <input
            type="range"
            class="alpha-slider"
            part="alpha-slider"
            role="slider"
            aria-label="Opacity"
            aria-valuemin="0"
            aria-valuemax="100"
            aria-valuenow="100"
            min="0" max="100" step="1" value="100"
          />
        </div>
        <div class="inputs-row">
          <input class="hex-input" part="format-inputs" type="text" aria-label="Hex color" spellcheck="false" />
        </div>
        <div class="swatch-grid" part="swatch-grid"></div>
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

    this.listen(this._trigger, "click", this._onTriggerClick.bind(this))
    this.listen(this._hueSlider, "input", this._onHueChange.bind(this))
    this.listen(this._alphaSlider, "input", this._onAlphaChange.bind(this))
    this.listen(this._hexInput, "change", this._onHexChange.bind(this))
    this.listen(this._canvasWrapper, "mousedown", this._onCanvasMousedown.bind(this))
    this.listen(this._canvasThumb, "keydown", this._onCanvasKeydown.bind(this))
    this.listen(document, "click", this._onDocClick.bind(this))
    this.listen(document, "keydown", this._onDocKeydown.bind(this))

    const attrVal = this.getAttribute("value") || "#000000"
    this._applyColorString(attrVal)
    this._buildSwatches()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "value" && this._trigger !== undefined) {
      this._applyColorString(newValue || "#000000")
    }
    if (name === "open") {
      this._syncOpen()
    }
    return
  }

  _applyColorString(colorStr) {
    if (colorStr.startsWith("#") && (colorStr.length === 4 || colorStr.length === 7)) {
      const hsl = hexToHsl(colorStr)
      this._hsl = hsl
      this._sat = hsl.s
      this._bri = hsl.l
      this._setFormValue(colorStr)
      this._syncUI()
    }
    return
  }

  _syncUI() {
    if (this._hueSlider === undefined) {
      return
    }
    const hex = hslToHex(this._hsl.h, this._sat, this._bri)
    this._triggerSwatch.style.background = hex
    this._previewSwatch.style.background = hex
    this._hueSlider.value = this._hsl.h
    this._hueSlider.setAttribute("aria-valuenow", String(this._hsl.h))
    if (this._alphaSlider !== null) {
      this._alphaSlider.value = Math.round(this._hsl.a * 100)
    }
    this._hexInput.value = hex
    this._hexInput.classList.remove("invalid")
    this._trigger.setAttribute("aria-label", `Color picker, current color: ${hex}`)
    this._redrawCanvas()
    this._positionThumb()
    return
  }

  _redrawCanvas() {
    if (this._canvas === null) {
      return
    }
    const w = this._canvas.offsetWidth || 200
    const h = this._canvas.offsetHeight || 160
    this._canvas.width = w
    this._canvas.height = h
    const ctx = this._canvas.getContext("2d")
    const hue = this._hsl.h

    const satGrad = ctx.createLinearGradient(0, 0, w, 0)
    satGrad.addColorStop(0, `hsl(${hue}, 0%, 100%)`)
    satGrad.addColorStop(1, `hsl(${hue}, 100%, 50%)`)
    ctx.fillStyle = satGrad
    ctx.fillRect(0, 0, w, h)

    const briGrad = ctx.createLinearGradient(0, 0, 0, h)
    briGrad.addColorStop(0, "rgba(0,0,0,0)")
    briGrad.addColorStop(1, "rgba(0,0,0,1)")
    ctx.fillStyle = briGrad
    ctx.fillRect(0, 0, w, h)
    return
  }

  _positionThumb() {
    if (this._canvasThumb === null || this._canvasWrapper === null) {
      return
    }
    const w = this._canvasWrapper.offsetWidth
    const h = this._canvasWrapper.offsetHeight
    const x = (this._sat / 100) * w
    const y = (1 - this._bri / 100) * h
    this._canvasThumb.style.left = `${x}px`
    this._canvasThumb.style.top = `${y}px`
    return
  }

  _onCanvasMousedown(event) {
    this._isDragging = true
    this._updateFromCanvas(event)

    const onMove = (e) => {
      if (this._isDragging === true) {
        this._updateFromCanvas(e)
        this.emit("mj-input", { value: this._currentHex(), color: this._hsl })
      }
    }
    const onUp = () => {
      this._isDragging = false
      document.removeEventListener("mousemove", onMove)
      document.removeEventListener("mouseup", onUp)
      this._commitColor()
    }
    document.addEventListener("mousemove", onMove)
    document.addEventListener("mouseup", onUp)
    return
  }

  _updateFromCanvas(event) {
    const rect = this._canvasWrapper.getBoundingClientRect()
    const x = Math.max(0, Math.min(event.clientX - rect.left, rect.width))
    const y = Math.max(0, Math.min(event.clientY - rect.top, rect.height))
    this._sat = Math.round((x / rect.width) * 100)
    this._bri = Math.round((1 - y / rect.height) * 100)
    this._syncUI()
    return
  }

  _onCanvasKeydown(event) {
    const step = event.shiftKey === true ? 10 : 1
    if (event.key === "ArrowRight") {
      event.preventDefault()
      this._sat = Math.min(100, this._sat + step)
    } else if (event.key === "ArrowLeft") {
      event.preventDefault()
      this._sat = Math.max(0, this._sat - step)
    } else if (event.key === "ArrowUp") {
      event.preventDefault()
      this._bri = Math.min(100, this._bri + step)
    } else if (event.key === "ArrowDown") {
      event.preventDefault()
      this._bri = Math.max(0, this._bri - step)
    } else {
      return
    }
    this._syncUI()
    this._commitColor()
    return
  }

  _onHueChange() {
    this._hsl.h = parseInt(this._hueSlider.value, 10)
    this._hueSlider.setAttribute("aria-valuenow", String(this._hsl.h))
    this._syncUI()
    this.emit("mj-input", { value: this._currentHex(), color: this._hsl })
    this._commitColor()
    return
  }

  _onAlphaChange() {
    this._hsl.a = parseInt(this._alphaSlider.value, 10) / 100
    this._alphaSlider.setAttribute("aria-valuenow", String(Math.round(this._hsl.a * 100)))
    this.emit("mj-input", { value: this._currentHex(), color: this._hsl })
    this._commitColor()
    return
  }

  _onHexChange() {
    const val = this._hexInput.value.trim()
    const hexRe = /^#?[0-9a-fA-F]{6}$/
    if (hexRe.test(val) === false) {
      this._hexInput.classList.add("invalid")
      return
    }
    const hex = val.startsWith("#") ? val : `#${val}`
    this._applyColorString(hex)
    this._commitColor()
    return
  }

  _commitColor() {
    const hex = this._currentHex()
    this._setFormValue(hex)
    this.setAttribute("value", hex)
    this.emit("mj-change", { value: hex, color: this._hsl })
    announce(`Color updated: ${hex}`, "polite")
    return
  }

  _currentHex() {
    return hslToHex(this._hsl.h, this._sat, this._bri)
  }

  _buildSwatches() {
    const swatchesAttr = this.getAttribute("swatches") || ""
    if (swatchesAttr.length === 0) {
      return
    }
    let colors = []
    try {
      colors = JSON.parse(swatchesAttr)
    } catch {
      return
    }
    let html = ""
    colors.forEach((color) => {
      html += `<button
        class="swatch"
        part="swatch"
        type="button"
        style="background:${color}"
        aria-label="${color}"
        data-color="${color}"
      ></button>`
    })
    this._swatchGrid.innerHTML = html
    const swatches = this._swatchGrid.querySelectorAll(".swatch")
    swatches.forEach((s) => {
      this.listen(s, "click", (e) => {
        this._applyColorString(e.currentTarget.dataset.color)
        this._commitColor()
        if (this.hasAttribute("inline") === false) {
          this._close()
        }
      })
    })
    return
  }

  _syncOpen() {
    const isOpen = this.hasAttribute("open")
    this._trigger.setAttribute("aria-expanded", isOpen === true ? "true" : "false")
    if (isOpen === true) {
      this._disposePosition = autoPosition(this._popup, this._trigger, { placement: "bottom-start" })
      this._disposeTrap = trapFocus(this._popup)
      setTimeout(() => this._redrawCanvas(), 0)
    } else {
      if (this._disposePosition !== null) {
        this._disposePosition()
        this._disposePosition = null
      }
      if (this._disposeTrap !== null) {
        this._disposeTrap()
        this._disposeTrap = null
      }
    }
    return
  }

  _open() {
    if (this.hasAttribute("disabled") || this.hasAttribute("readonly")) {
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

  _onDocKeydown(event) {
    if (event.key === "Escape" && this.hasAttribute("open")) {
      this._close()
      this._trigger.focus()
    }
    return
  }

  _validationAnchor() {
    return this._trigger || this
  }

  /* ----- scriptable API ----- */

  get hexValue() {
    return this._currentHex()
  }

  get color() {
    return Object.assign({}, this._hsl)
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

  focus() {
    if (this._trigger !== undefined) {
      this._trigger.focus()
    }
    return
  }
}
