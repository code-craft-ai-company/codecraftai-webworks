/*
 * mjsparkline.js
 *
 * <mj-sparkline> -- compact inline SVG trend chart supporting line, area, bar,
 * and win/loss types. Built-in SVG renderer with no external dependencies.
 * Paired text or a `label` attribute provides the accessible equivalent.
 */

import { MjElement } from "../core/mjelement.js";

const STYLES = `
:host {
  display: inline-block;
  vertical-align: middle;
}

.container {
  display: inline-block;
  line-height: 0;
}

svg {
  display: block;
  overflow: visible;
}

.line {
  fill: none;
  stroke: var(--mj-sparkline-color, var(--mj-accent));
  stroke-width: var(--mj-sparkline-stroke-width, 1.5px);
  stroke-linecap: round;
  stroke-linejoin: round;
}
.area {
  fill: var(--mj-sparkline-color, var(--mj-accent));
  opacity: var(--mj-sparkline-area-opacity, 0.2);
}
.bar-pos {
  fill: var(--mj-sparkline-color, var(--mj-accent));
}
.bar-neg {
  fill: var(--mj-sparkline-negative-color, var(--mj-color-danger, #dc2626));
}
.end-dot {
  fill: var(--mj-sparkline-color, var(--mj-accent));
}
.reference-line {
  stroke: var(--mj-sparkline-reference-color, var(--mj-border));
  stroke-width: 1;
  stroke-dasharray: var(--mj-sparkline-reference-dash, 3 2);
}
`;

export class MjSparkline extends MjElement {
  static tagName = "mj-sparkline";
  static styles = STYLES;
  static watched = ["values", "type", "width", "height", "show-end-dot",
    "reference-value", "curve", "label", "animated"];

  constructor() {
    super()
    this._svgEl = null
  }

  render() {
    const markup = `
      <div class="container" part="container">
        <svg part="svg"></svg>
      </div>
    `
    return markup
  }

  afterRender() {
    this._svgEl = this.$("svg")
    this._wireClicks()
    this._draw()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._svgEl === null || this._svgEl === undefined) { return }
    this._draw()
    return
  }

  _draw() {
    const W = parseInt(this.getAttribute("width") || "80", 10)
    const H = parseInt(this.getAttribute("height") || "24", 10)
    const label = this.getAttribute("label") || ""

    this._svgEl.setAttribute("viewBox", `0 0 ${W} ${H}`)
    this._svgEl.setAttribute("width", String(W))
    this._svgEl.setAttribute("height", String(H))

    if (label.length > 0) {
      this._svgEl.setAttribute("role", "img")
      this._svgEl.setAttribute("aria-label", label)
      this._svgEl.removeAttribute("aria-hidden")
    } else {
      this._svgEl.setAttribute("aria-hidden", "true")
      this._svgEl.removeAttribute("role")
      this._svgEl.removeAttribute("aria-label")
    }

    const vals = this.parsedValues
    const type = this.getAttribute("type") || "line"

    this._svgEl.innerHTML = ""

    const valid = vals.filter(v => isNaN(v) === false)
    if (valid.length === 0) {
      const mid = H / 2
      this._svgEl.innerHTML = `<line x1="0" y1="${mid}" x2="${W}" y2="${mid}" class="line" part="line"/>`
      this.emit("mj-sparkline-render", { type: type, pointCount: 0 })
      return
    }

    const refVal = parseFloat(this.getAttribute("reference-value") || "")
    const hasRef = isNaN(refVal) === false

    const pad = 2
    const minV = this.min
    const maxV = this.max
    const range = maxV - minV === 0 ? 1 : maxV - minV

    const scaleY = (v) => {
      const y = pad + (H - 2 * pad) * (1 - (v - minV) / range)
      return y
    }
    const scaleX = (i) => {
      const n = vals.length
      const x = n > 1 ? (i / (n - 1)) * W : W / 2
      return x
    }

    const refY = hasRef ? scaleY(refVal) : H / 2

    if (type === "bar") {
      this._drawBars(vals, W, H, pad, scaleX, scaleY, refY)
    } else if (type === "win-loss") {
      this._drawWinLoss(vals, W, H, pad, scaleX)
    } else {
      this._drawLinePath(vals, W, H, type === "area", scaleX, scaleY, refY)
    }

    if (hasRef === true) {
      this._svgEl.innerHTML += `<line class="reference-line" part="reference-line"
        x1="0" y1="${refY.toFixed(1)}" x2="${W}" y2="${refY.toFixed(1)}"/>`
    }

    if (this.hasAttribute("show-end-dot") === true) {
      const lastIdx = this._lastValidIndex(vals)
      if (lastIdx >= 0) {
        const lx = scaleX(lastIdx)
        const lv = vals[lastIdx]
        const ly = scaleY(lv)
        const r = parseFloat(getComputedStyle(this._svgEl).getPropertyValue("--mj-sparkline-end-dot-radius")) || 3
        this._svgEl.innerHTML += `<circle class="end-dot" part="end-dot"
          cx="${lx.toFixed(1)}" cy="${ly.toFixed(1)}" r="${r}"
          style="cursor:pointer" data-idx="${lastIdx}"/>`
      }
    }

    if (this.hasAttribute("animated") === true) {
      const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches
      if (reduced === false) {
        const path = this._svgEl.querySelector("path.line, path[part='line']")
        if (path !== null) {
          const len = path.getTotalLength ? path.getTotalLength() : 300
          path.style.strokeDasharray = String(len)
          path.style.strokeDashoffset = String(len)
          path.style.transition = `stroke-dashoffset var(--mj-sparkline-transition, var(--mj-motion-medium)) var(--mj-motion-ease)`
          requestAnimationFrame(() => { path.style.strokeDashoffset = "0" })
        }
      }
    }

    this.emit("mj-sparkline-render", { type: type, pointCount: valid.length })
    return
  }

  _wireClicks() {
    this.listen(this._svgEl, "click", (e) => {
      const target = e.target
      if (target === null || target === this._svgEl) { return }

      const idx = parseInt(target.getAttribute("data-idx") || "", 10)
      if (isNaN(idx) === true) { return }

      const vals = this.parsedValues
      const value = vals[idx]
      this.emit("mj-sparkline-click", { index: idx, value: value })
    })
    return
  }

  _drawLinePath(vals, W, H, area, scaleX, scaleY, refY) {
    let linePath = ""
    let areaPath = ""
    let started = false
    let firstX = 0
    let lastX = 0

    for (let i = 0; i < vals.length; i = i + 1) {
      const v = vals[i]
      if (isNaN(v) === true) {
        started = false
        continue
      }
      const x = scaleX(i)
      const y = scaleY(v)
      if (started === false) {
        linePath += `M${x.toFixed(1)},${y.toFixed(1)}`
        if (area === true) { areaPath += `M${x.toFixed(1)},${refY.toFixed(1)} L${x.toFixed(1)},${y.toFixed(1)}` }
        firstX = x
        started = true
      } else {
        linePath += ` L${x.toFixed(1)},${y.toFixed(1)}`
        if (area === true) { areaPath += ` L${x.toFixed(1)},${y.toFixed(1)}` }
      }
      lastX = x
    }

    if (area === true && areaPath.length > 0) {
      areaPath += ` L${lastX.toFixed(1)},${refY.toFixed(1)} Z`
      this._svgEl.innerHTML += `<path class="area" part="area" d="${areaPath}"/>`
    }
    if (linePath.length > 0) {
      this._svgEl.innerHTML += `<path class="line" part="line" d="${linePath}"/>`
    }
    return
  }

  _drawBars(vals, W, H, pad, scaleX, scaleY, refY) {
    const n = vals.length
    const barW = Math.max(1, W / n - 1)
    const gap = parseFloat(getComputedStyle(this._svgEl).getPropertyValue("--mj-sparkline-bar-gap")) || 1

    for (let i = 0; i < n; i = i + 1) {
      const v = vals[i]
      if (isNaN(v) === true) { continue }
      const x = scaleX(i) - barW / 2
      const y = scaleY(v)
      const isPos = v >= 0
      const barTop = isPos ? y : refY
      const barH = Math.abs(refY - y)
      const cls = isPos ? "bar-pos" : "bar-neg"
      this._svgEl.innerHTML += `<rect class="${cls}" part="bar"
        x="${(x + gap / 2).toFixed(1)}" y="${barTop.toFixed(1)}"
        width="${Math.max(1, barW - gap).toFixed(1)}" height="${Math.max(1, barH).toFixed(1)}" rx="1"
        style="cursor:pointer" data-idx="${i}"/>`
    }
    return
  }

  _drawWinLoss(vals, W, H, pad, scaleX) {
    const n = vals.length
    const barW = Math.max(1, W / n - 1)
    const colH = (H - 2 * pad) / 2 - 1
    const midY = H / 2

    for (let i = 0; i < n; i = i + 1) {
      const v = vals[i]
      if (isNaN(v) === true) { continue }
      const x = scaleX(i) - barW / 2
      const isWin = v > 0
      const y = isWin ? midY - colH - 1 : midY + 1
      const cls = isWin ? "bar-pos" : "bar-neg"
      this._svgEl.innerHTML += `<rect class="${cls}" part="win-loss-col"
        x="${(x + 0.5).toFixed(1)}" y="${y.toFixed(1)}"
        width="${Math.max(1, barW - 1).toFixed(1)}" height="${colH.toFixed(1)}" rx="1"
        style="cursor:pointer" data-idx="${i}"/>`
    }
    return
  }

  _lastValidIndex(vals) {
    for (let i = vals.length - 1; i >= 0; i = i - 1) {
      if (isNaN(vals[i]) === false) { return i }
    }
    return -1
  }

  /* ----- scriptable API ----- */

  get parsedValues() {
    const raw = this.getAttribute("values") || ""
    if (raw.length === 0) { return [] }
    const parts = raw.split(",")
    const nums = parts.map(p => parseFloat(p.trim()))
    return nums
  }

  get min() {
    const valid = this.parsedValues.filter(v => isNaN(v) === false)
    if (valid.length === 0) { return 0 }
    return Math.min(...valid)
  }

  get max() {
    const valid = this.parsedValues.filter(v => isNaN(v) === false)
    if (valid.length === 0) { return 0 }
    return Math.max(...valid)
  }

  get last() {
    const valid = this.parsedValues.filter(v => isNaN(v) === false)
    if (valid.length === 0) { return NaN }
    return valid[valid.length - 1]
  }
}
