/*
 * ohlc.js
 *
 * OHLC / Candlestick renderer.
 *
 * Registers: "ohlc", "candlestick"
 *
 * ctx.raw.candles: [{ t, o, h, l, c, v }]
 *   t — ISO-8601 date/datetime or epoch ms
 *   o — open price
 *   h — high price
 *   l — low price
 *   c — close price
 *   v — volume (optional, not drawn by this renderer)
 *
 * ctx.attrs("style", "candle") selects drawing mode:
 *   "candle" — filled body rect + wick lines (default)
 *   "ohlc"   — vertical range line + open/close tick marks
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, formatDate } from "../svgdraw.js";
import { linearScale, niceTicks } from "../scales.js";


function _toMs(value) {
  /*
   * Coerce a candle timestamp to epoch milliseconds.
   */
  if (value instanceof Date) {
    return value.getTime()
  }
  const numeric = Number(value)
  if (Number.isNaN(numeric) === false && numeric > 1e9) {
    return numeric
  }
  const parsed = new Date(value)
  const ms = parsed.getTime()
  return ms
}


export function render(ctx) {
  /*
   * Render an OHLC or candlestick chart.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw
  const style = ctx.attrs("style", "candle")

  const root = svgEl("g", { part: "plot" }, [])

  const candles = (raw !== null && raw !== undefined && Array.isArray(raw.candles) === true)
    ? raw.candles
    : []

  if (candles.length === 0) {
    return root
  }

  const margin = { top: 16, right: 16, bottom: 40, left: 64 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  /* Compute price domain. */
  let priceMin = Infinity
  let priceMax = -Infinity
  for (let index = 0; index < candles.length; index = index + 1) {
    const candle = candles[index]
    if (candle.l < priceMin) {
      priceMin = candle.l
    }
    if (candle.h > priceMax) {
      priceMax = candle.h
    }
  }
  if (priceMin === Infinity || priceMax === -Infinity) {
    return root
  }
  const pricePad = (priceMax - priceMin) * 0.05
  priceMin = priceMin - pricePad
  priceMax = priceMax + pricePad

  /* Scales. */
  const priceScale = linearScale([priceMin, priceMax], [plotH, 0])

  const slotW = candles.length > 0 ? plotW / candles.length : plotW
  const bodyW = Math.max(slotW * 0.6, 2)
  const halfBody = bodyW / 2

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Value gridlines + tick labels. */
  const ticks = niceTicks(priceMin, priceMax, 5)
  for (let t = 0; t < ticks.length; t = t + 1) {
    const tick = ticks[t]
    const y = priceScale(tick)
    plot.appendChild(svgEl("line", {
      x1: 0, y1: y, x2: plotW, y2: y,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    plot.appendChild(svgEl("text", {
      x: -8, y: y + 4, "text-anchor": "end",
      "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(tick)))
  }

  /* Draw each candle or OHLC bar. */
  for (let index = 0; index < candles.length; index = index + 1) {
    const candle = candles[index]
    const cx = (index + 0.5) * slotW

    const yHigh = priceScale(candle.h)
    const yLow = priceScale(candle.l)
    const yOpen = priceScale(candle.o)
    const yClose = priceScale(candle.c)

    const bullish = candle.c >= candle.o
    const color = bullish
      ? "var(--mj-chart-positive, #15803d)"
      : "var(--mj-chart-negative, #b91c1c)"

    const label = `${formatDate(new Date(_toMs(candle.t)))} ` +
      `O:${candle.o} H:${candle.h} L:${candle.l} C:${candle.c}`
    const direction = bullish ? "bullish" : "bearish"

    const group = svgEl("g", {
      part: "candle",
      tabindex: "0",
      role: "img",
      "aria-label": `${direction} ${label}`
    }, [])
    group.appendChild(svgEl("title", null, label))

    if (style === "ohlc") {
      /* Vertical range line. */
      group.appendChild(svgEl("line", {
        x1: cx, y1: yHigh, x2: cx, y2: yLow,
        stroke: color, "stroke-width": 1.5
      }, []))
      /* Open tick (left). */
      group.appendChild(svgEl("line", {
        x1: cx - halfBody, y1: yOpen, x2: cx, y2: yOpen,
        stroke: color, "stroke-width": 1.5
      }, []))
      /* Close tick (right). */
      group.appendChild(svgEl("line", {
        x1: cx, y1: yClose, x2: cx + halfBody, y2: yClose,
        stroke: color, "stroke-width": 1.5
      }, []))
    } else {
      /* Upper wick. */
      const bodyTop = Math.min(yOpen, yClose)
      const bodyBot = Math.max(yOpen, yClose)
      group.appendChild(svgEl("line", {
        x1: cx, y1: yHigh, x2: cx, y2: bodyTop,
        stroke: color, "stroke-width": 1.5
      }, []))
      /* Lower wick. */
      group.appendChild(svgEl("line", {
        x1: cx, y1: bodyBot, x2: cx, y2: yLow,
        stroke: color, "stroke-width": 1.5
      }, []))
      /* Body rect. */
      const bodyH = Math.max(Math.abs(yClose - yOpen), 1)
      group.appendChild(svgEl("rect", {
        x: cx - halfBody, y: bodyTop,
        width: bodyW, height: bodyH,
        fill: color, stroke: color, "stroke-width": 0.5
      }, []))
    }

    const handler = () => {
      ctx.emit("mj-chart-candle-click", {
        t: candle.t, o: candle.o, h: candle.h, l: candle.l, c: candle.c,
        direction: direction
      })
    }
    group.addEventListener("click", handler)
    group.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        handler()
      }
    })

    plot.appendChild(group)
  }

  /* Time axis labels — sample every N candles to avoid crowding. */
  const labelEvery = Math.max(1, Math.ceil(candles.length / 8))
  for (let index = 0; index < candles.length; index = index + labelEvery) {
    const candle = candles[index]
    const cx = (index + 0.5) * slotW
    const dateStr = formatDate(new Date(_toMs(candle.t)), { month: "short", day: "numeric" })
    plot.appendChild(svgEl("text", {
      x: cx, y: plotH + 16, "text-anchor": "middle",
      "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, dateStr))
  }

  /* Axis baselines. */
  plot.appendChild(svgEl("line", {
    x1: 0, y1: plotH, x2: plotW, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))
  plot.appendChild(svgEl("line", {
    x1: 0, y1: 0, x2: 0, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))

  return root
}


registerRenderer("ohlc", render)
registerRenderer("candlestick", render)
