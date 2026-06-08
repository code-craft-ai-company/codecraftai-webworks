/*
 * volume.js
 *
 * Trading-volume renderer.
 *
 * Registers:
 *   "volume" — vertical bars over a time axis; bar color follows price
 *              direction (bullish/bearish) or a uniform series color
 *              depending on the `color-mode` attribute.
 *
 * ctx.raw shape (reuses candles envelope):
 *   candles: [{ t, v, o?, c?, h?, l? }]
 *
 * color-mode:
 *   "direction" (default) — bullish (c >= o) uses --mj-chart-positive;
 *                           bearish uses --mj-chart-negative.
 *   "series"              — uniform series color from colorFor(0).
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatDate, formatNumber } from "../svgdraw.js";
import { timeScale, linearScale, niceTicks } from "../scales.js";


export function render(ctx) {
  /*
   * Render a trading-volume bar chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw
  const candles = (raw !== null && raw !== undefined && Array.isArray(raw.candles))
    ? raw.candles : []

  const colorMode = ctx.attrs("color-mode", "direction")

  const root = svgEl("g", { part: "plot" }, [])

  if (candles.length === 0) {
    return root
  }

  /* Filter to candles that have a volume value. */
  const withVolume = candles.filter((candle) => {
    const hasV = candle.v !== undefined && candle.v !== null && candle.v !== ""
    return hasV
  })

  if (withVolume.length === 0) {
    return root
  }

  /* Date domain. */
  let dateMin = null
  let dateMax = null
  let volumeMax = 0

  for (let index = 0; index < withVolume.length; index = index + 1) {
    const candle = withVolume[index]
    const date = new Date(candle.t)
    const vol = typeof candle.v === "number" ? candle.v : parseFloat(candle.v) || 0
    if (dateMin === null || date < dateMin) {
      dateMin = date
    }
    if (dateMax === null || date > dateMax) {
      dateMax = date
    }
    if (vol > volumeMax) {
      volumeMax = vol
    }
  }

  if (dateMin === null) {
    dateMin = new Date()
  }
  if (dateMax === null) {
    dateMax = new Date(dateMin.getTime() + 86400000)
  }
  if (volumeMax === 0) {
    volumeMax = 1
  }

  /* Pad the time domain by half a bar on each side. */
  const margin = { top: 16, right: 16, bottom: 40, left: 64 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const timePad = withVolume.length > 1
    ? ((dateMax.getTime() - dateMin.getTime()) / (withVolume.length - 1)) / 2
    : 86400000 / 2
  const paddedMin = new Date(dateMin.getTime() - timePad)
  const paddedMax = new Date(dateMax.getTime() + timePad)

  const timeScaleFn = timeScale([paddedMin, paddedMax], [0, plotW])
  const valScale = linearScale([0, volumeMax], [plotH, 0])

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Value axis ticks (left side). */
  const ticks = niceTicks(0, volumeMax, 5)
  for (let t = 0; t < ticks.length; t = t + 1) {
    const tick = ticks[t]
    const y = valScale(tick)
    plot.appendChild(svgEl("line", {
      x1: 0, y1: y, x2: plotW, y2: y,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    plot.appendChild(svgEl("text", {
      x: -8, y: y + 4, "text-anchor": "end",
      "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(tick, { notation: "compact" })))
  }

  /* Time axis ticks (bottom). */
  const tickCount = Math.max(2, Math.floor(plotW / 70))
  const timeTicks = timeScaleFn.ticks(tickCount)
  const spanDays = (dateMax.getTime() - dateMin.getTime()) / 86400000

  for (let t = 0; t < timeTicks.length; t = t + 1) {
    const tick = timeTicks[t]
    const x = timeScaleFn(tick)
    plot.appendChild(svgEl("line", {
      x1: x, y1: plotH, x2: x, y2: plotH + 4,
      stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1
    }, []))
    plot.appendChild(svgEl("text", {
      x: x, y: plotH + 16, "text-anchor": "middle",
      "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, formatDate(tick, spanDays <= 180
      ? { month: "short", day: "numeric" }
      : { year: "numeric", month: "short" })))
  }

  /* Axis baseline. */
  plot.appendChild(svgEl("line", {
    x1: 0, y1: plotH, x2: plotW, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))

  /* Volume bars. */
  const barW = withVolume.length > 1
    ? Math.max((plotW / withVolume.length) * 0.7, 1)
    : 10

  for (let index = 0; index < withVolume.length; index = index + 1) {
    const candle = withVolume[index]
    const date = new Date(candle.t)
    const vol = typeof candle.v === "number" ? candle.v : parseFloat(candle.v) || 0
    const open = typeof candle.o === "number" ? candle.o : null
    const close = typeof candle.c === "number" ? candle.c : null

    const cx = timeScaleFn(date)
    const barX = cx - barW / 2
    const barY = valScale(vol)
    const barH = plotH - barY

    let barColor = ctx.colorFor(0)
    if (colorMode === "direction") {
      if (open !== null && close !== null) {
        barColor = close >= open
          ? "var(--mj-chart-positive, var(--mj-color-success, #15803d))"
          : "var(--mj-chart-negative, var(--mj-color-danger, #b91c1c))"
      }
    }

    const dirLabel = (open !== null && close !== null)
      ? (close >= open ? "bullish" : "bearish") : ""
    const ariaLabel = `Volume ${formatDate(date)}: ${formatNumber(vol)}` +
      (dirLabel !== "" ? ` (${dirLabel})` : "")

    const bar = svgEl("rect", {
      x: barX, y: barY, width: barW, height: Math.max(barH, 1),
      fill: barColor, "fill-opacity": 0.75, part: "bar"
    }, [])
    bar.setAttribute("tabindex", "0")
    bar.setAttribute("role", "img")
    bar.setAttribute("aria-label", ariaLabel)
    bar.appendChild(svgEl("title", null, ariaLabel))

    const emitCandle = candle
    const clickHandler = () => {
      ctx.emit("mj-chart-bar-click", {
        date: emitCandle.t,
        volume: emitCandle.v,
        open: emitCandle.o,
        close: emitCandle.c
      })
    }
    bar.addEventListener("click", clickHandler)
    bar.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        clickHandler()
      }
    })
    plot.appendChild(bar)
  }

  return root
}


registerRenderer("volume", render);
