/*
 * tornado.js
 *
 * Tornado / sensitivity renderer.
 *
 * Registers:
 *   "tornado" — paired horizontal bars from a centre baseline, one row per
 *               input, rows sorted top-to-bottom by spread (widest first).
 *               `low` and `high` are the output values when the input is at
 *               its low and its high setting, so an inverse driver (low input
 *               gives the higher output) simply has its bars swapped.
 *
 * variant="butterfly" treats low / high as magnitudes drawn to the left and
 * right of the baseline (a population pyramid, two-sided comparison); rows
 * keep the data order and values are shown as magnitudes on both sides.
 *
 * ctx.raw shape:
 *   baseline: number            central reference value (default 0)
 *   low_label?, high_label?     legend names of the two bar colours
 *                               (default "Low input" / "High input", in
 *                               butterfly mode "Left" / "Right")
 *   series: [{ name, values: [{ label, low, high }] }]
 * Numeric strings are accepted; a missing or non-numeric side draws no bar.
 *
 * Events:
 *   mj-chart-bar-click { label, side, value, baseline }
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { linearScale, bandScale, niceTicks } from "../scales.js";


const LABEL_FONT = 11;
const VALUE_FONT = 10;
const CHAR_WIDTH = 0.56;


function _textWidth(text, fontSize) {
  /*
   * Approximate rendered width of a label.
   */
  const width = String(text).length * fontSize * CHAR_WIDTH
  return width
}


function _fitText(text, maxWidth, fontSize) {
  /*
   * Shorten a label with an ellipsis so it fits a width ("" if hopeless).
   */
  const value = String(text)
  let fitted = value
  if (_textWidth(value, fontSize) > maxWidth) {
    const maxChars = Math.floor(maxWidth / (fontSize * CHAR_WIDTH)) - 1
    fitted = maxChars >= 2 ? value.slice(0, maxChars) + "…" : ""
  }
  return fitted
}


function _number(value) {
  /*
   * A finite number from a number or numeric string, else null.
   */
  if (value === null || value === undefined || value === "") {
    return null
  }
  const numeric = Number(value)
  const result = Number.isFinite(numeric) === true ? numeric : null
  return result
}


function _compact(value) {
  /*
   * Short value label for the bar ends ("4.2M").
   */
  const text = formatNumber(value, { notation: "compact", maximumFractionDigits: 2 })
  return text
}


export function render(ctx) {
  /*
   * Render a tornado/sensitivity chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const baselineValue = _number(raw.baseline)
  const baseline = baselineValue !== null ? baselineValue : 0
  const seriesArr = Array.isArray(raw.series) ? raw.series : []

  const isButterfly = ctx.attrs("style", "") === "butterfly" || ctx.type === "butterfly"
  const lowName = typeof raw.low_label === "string" && raw.low_label !== ""
    ? raw.low_label : (isButterfly === true ? "Left" : "Low input")
  const highName = typeof raw.high_label === "string" && raw.high_label !== ""
    ? raw.high_label : (isButterfly === true ? "Right" : "High input")
  const lowColor = ctx.colorFor(lowName)
  const highColor = ctx.colorFor(highName)

  const root = svgEl("g", { part: "plot" }, [])

  /* Rows: { label, low, high, lowShown, highShown } in output units. */
  const rows = []
  for (let s = 0; s < seriesArr.length; s = s + 1) {
    const series = seriesArr[s]
    if (series === null || typeof series !== "object" || Array.isArray(series.values) === false) {
      continue
    }
    for (let v = 0; v < series.values.length; v = v + 1) {
      const entry = series.values[v]
      if (entry === null || typeof entry !== "object") {
        continue
      }
      const low = _number(entry.low)
      const high = _number(entry.high)
      let lowValue = low
      let highValue = high
      if (isButterfly === true) {
        lowValue = low !== null ? baseline - Math.abs(low) : null
        highValue = high !== null ? baseline + Math.abs(high) : null
      }
      rows.push({
        label: entry.label !== undefined && entry.label !== null ? String(entry.label) : "",
        low: lowValue,
        high: highValue,
        lowShown: isButterfly === true && low !== null ? Math.abs(low) : low,
        highShown: isButterfly === true && high !== null ? Math.abs(high) : high,
        order: rows.length
      })
    }
  }

  ctx.setLegend([{ label: lowName, color: lowColor }, { label: highName, color: highColor }])
  ctx.setTable({
    columns: ["Input", lowName, highName, "Baseline", "Spread"],
    rows: rows.map((row) => [
      row.label,
      row.lowShown !== null ? row.lowShown : "",
      row.highShown !== null ? row.highShown : "",
      baseline,
      row.low !== null && row.high !== null ? Math.abs(row.high - row.low) : ""
    ])
  })

  if (rows.length === 0) {
    return root
  }

  /* Tornado: widest spread first (a missing side counts from baseline). */
  if (isButterfly === false) {
    const spreadOf = (row) => {
      const lowSide = row.low !== null ? row.low : baseline
      const highSide = row.high !== null ? row.high : baseline
      return Math.abs(highSide - lowSide)
    }
    rows.sort((a, b) => {
      const difference = spreadOf(b) - spreadOf(a)
      return difference !== 0 ? difference : a.order - b.order
    })
  }

  /* Value domain: both ends of every row, whichever side they are on. */
  let domainMin = baseline
  let domainMax = baseline
  for (let index = 0; index < rows.length; index = index + 1) {
    const values = [rows[index].low, rows[index].high]
    for (let k = 0; k < values.length; k = k + 1) {
      if (values[k] !== null) {
        domainMin = Math.min(domainMin, values[k])
        domainMax = Math.max(domainMax, values[k])
      }
    }
  }
  if (domainMin === domainMax) {
    const spread = Math.max(Math.abs(baseline) * 0.1, 1)
    domainMin = domainMin - spread
    domainMax = domainMax + spread
  }
  /* Room for the end-of-bar value labels. */
  const domainPad = (domainMax - domainMin) * 0.12
  domainMin = domainMin - domainPad
  domainMax = domainMax + domainPad

  let longest = 0
  for (let index = 0; index < rows.length; index = index + 1) {
    longest = Math.max(longest, _textWidth(rows[index].label, LABEL_FONT))
  }
  const gutter = Math.min(Math.max(longest + 16, 48), Math.max(ctx.width * 0.35, 48))

  const margin = { top: 12, right: 16, bottom: 28, left: gutter }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const valScale = linearScale([domainMin, domainMax], [0, plotW])
  const rowScale = bandScale(rows.map((row, index) => index), [0, plotH], 0.2)
  const bandwidth = rowScale.bandwidth()
  const baseX = valScale(baseline)

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)
  const axis = svgEl("g", { "aria-hidden": "true" }, [])
  const marks = svgEl("g", null, [])
  const labels = svgEl("g", { "aria-hidden": "true" }, [])
  plot.appendChild(axis)
  plot.appendChild(marks)
  plot.appendChild(labels)

  /* Value axis (bottom); butterfly shows distances from the baseline. */
  const ticks = niceTicks(domainMin, domainMax, Math.max(4, Math.floor(plotW / 90)))
  for (let t = 0; t < ticks.length; t = t + 1) {
    const x = valScale(ticks[t])
    axis.appendChild(svgEl("line", {
      x1: x, y1: 0, x2: x, y2: plotH,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    const shown = isButterfly === true ? Math.abs(ticks[t] - baseline) : ticks[t]
    axis.appendChild(svgEl("text", {
      x: x, y: plotH + 16, "text-anchor": "middle",
      "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, _compact(shown)))
  }
  axis.appendChild(svgEl("line", {
    x1: 0, y1: plotH, x2: plotW, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))

  for (let index = 0; index < rows.length; index = index + 1) {
    const row = rows[index]
    const rowY = rowScale.at(index)
    const barH = Math.max(bandwidth, 2)

    labels.appendChild(svgEl("text", {
      x: -8, y: rowY + barH / 2 + 4,
      "text-anchor": "end", "font-size": LABEL_FONT,
      fill: "var(--mj-text, #14181f)"
    }, _fitText(row.label, margin.left - 12, LABEL_FONT)))

    const sides = [
      { side: "low", value: row.low, shown: row.lowShown, color: lowColor, name: lowName },
      { side: "high", value: row.high, shown: row.highShown, color: highColor, name: highName }
    ]
    for (let k = 0; k < sides.length; k = k + 1) {
      const side = sides[k]
      if (side.value === null) {
        continue
      }
      const endX = valScale(side.value)
      const barX = Math.min(endX, baseX)
      const barW = Math.abs(endX - baseX)
      const ariaLabel = `${row.label}, ${side.name}: ${formatNumber(side.shown)}`
      if (barW > 0) {
        const bar = svgEl("rect", {
          x: barX, y: rowY, width: barW, height: barH, rx: 2,
          fill: side.color, part: "bar",
          tabindex: "0", role: "img", "aria-label": ariaLabel
        }, [])
        bar.appendChild(svgEl("title", null, ariaLabel))
        const emitRow = row
        const emitSide = side
        const clickHandler = () => {
          ctx.emit("mj-chart-bar-click", {
            label: emitRow.label,
            side: emitSide.side,
            value: emitSide.shown,
            baseline: baseline
          })
        }
        bar.addEventListener("click", clickHandler)
        bar.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault()
            clickHandler()
          }
        })
        marks.appendChild(bar)
      }

      /* Value at the outer end of the bar, when the row is tall enough. */
      const leftOfBase = endX < baseX
      const valueText = _compact(side.shown)
      const valueW = _textWidth(valueText, VALUE_FONT) + 4
      const fits = leftOfBase === true ? endX - valueW >= 0 : endX + valueW <= plotW + margin.right - 2
      if (barH >= 9 && barW > 0 && fits === true) {
        labels.appendChild(svgEl("text", {
          x: leftOfBase === true ? endX - 4 : endX + 4,
          y: rowY + barH / 2 + 3.5,
          "text-anchor": leftOfBase === true ? "end" : "start",
          "font-size": VALUE_FONT, fill: "var(--mj-text-muted, #6b7280)"
        }, valueText))
      }
    }
  }

  /* Baseline with its value. */
  axis.appendChild(svgEl("line", {
    x1: baseX, y1: 0, x2: baseX, y2: plotH,
    stroke: "var(--mj-text-muted, #6b7280)", "stroke-width": 1.5
  }, []))
  labels.appendChild(svgEl("text", {
    x: baseX, y: -2, "text-anchor": "middle", "font-size": VALUE_FONT,
    fill: "var(--mj-text, #14181f)"
  }, isButterfly === true ? "" : `Base ${_compact(baseline)}`))

  return root
}


function _isEmpty(model) {
  /*
   * Nothing to draw when no series has a row (a bare baseline is not data).
   */
  const raw = model !== null && model !== undefined && model.raw !== null && model.raw !== undefined
    ? model.raw : {}
  const series = Array.isArray(raw.series) === true ? raw.series : []
  const hasRow = series.some((entry) => entry !== null && typeof entry === "object" &&
    Array.isArray(entry.values) === true && entry.values.length > 0)
  return hasRow === false
}


registerRenderer("tornado", render, { orientation: "horizontal", isEmpty: _isEmpty });
