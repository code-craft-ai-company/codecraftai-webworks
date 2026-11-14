/*
 * volume.js
 *
 * Trading-volume renderer.
 *
 * Registers:
 *   "volume" — vertical bars, one per trading session; bar colour follows
 *              price direction (rising / falling) or a uniform series colour
 *              depending on the `color-mode` attribute.
 *
 * ctx.raw shape (reuses the candles envelope):
 *   candles: [{ t, v, o?, c?, h?, l? }]   numeric strings are accepted
 *
 * Sessions use the same equal slots, margins and date labels as the
 * ohlc / candlestick renderer, so a price chart and a volume chart of the
 * same data at the same width line up. Dense data is merged the same way.
 *
 * color-mode:
 *   "direction" (default) — close >= open uses the rising colour, else the
 *                           falling colour (sessions without open / close use
 *                           the series colour); falling bars are also drawn
 *                           at a lower opacity so direction is not colour-only
 *   "series"              — uniform series colour
 *
 * Events:
 *   mj-chart-bar-click { date, volume, open, close, count }
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { linearScale, niceDomain, niceTicks } from "../scales.js";
import {
  SESSION_MARGIN, UP_COLOR, DOWN_COLOR, readCandles, aggregateSessions,
  drawSessionAxis, sessionText
} from "./ohlc.js";


export function render(ctx) {
  /*
   * Render a trading-volume bar chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const colorMode = ctx.attrs("color-mode", "direction")
  const byDirection = colorMode !== "series"
  const seriesColor = ctx.colorFor(0)

  const root = svgEl("g", { part: "plot" }, [])

  const allSessions = readCandles(ctx.raw)
  ctx.setTable({
    columns: ["Date", "Volume", "Open", "Close", "Direction"],
    rows: allSessions.map((entry) => [
      sessionText(entry),
      entry.v !== null ? entry.v : "",
      entry.o !== null ? entry.o : "",
      entry.c !== null ? entry.c : "",
      entry.o !== null ? (entry.c >= entry.o ? "rising" : "falling") : ""
    ])
  })
  ctx.setLegend(byDirection === true
    ? [{ label: "Close ≥ open", color: UP_COLOR }, { label: "Close < open", color: DOWN_COLOR }]
    : [{ label: "Volume", color: seriesColor }])

  const margin = SESSION_MARGIN
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)
  const sessions = aggregateSessions(allSessions, plotW)

  let volumeMax = 0
  let anyVolume = false
  for (let index = 0; index < sessions.length; index = index + 1) {
    if (sessions[index].v !== null && sessions[index].v >= 0) {
      anyVolume = true
      volumeMax = Math.max(volumeMax, sessions[index].v)
    }
  }
  if (anyVolume === false) {
    return root
  }
  const domain = niceDomain(0, volumeMax > 0 ? volumeMax : 1, 5)
  const valScale = linearScale(domain, [plotH, 0])
  const slotW = plotW / sessions.length
  const barW = Math.min(Math.max(slotW * 0.6, 1), 24)

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)
  const axis = svgEl("g", { "aria-hidden": "true" }, [])
  const marks = svgEl("g", null, [])
  plot.appendChild(axis)
  plot.appendChild(marks)

  const ticks = niceTicks(domain[0], domain[1], 5)
  for (let t = 0; t < ticks.length; t = t + 1) {
    const y = valScale(ticks[t])
    axis.appendChild(svgEl("line", {
      x1: 0, y1: y, x2: plotW, y2: y,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    axis.appendChild(svgEl("text", {
      x: -8, y: y + 4, "text-anchor": "end",
      "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(ticks[t], { notation: "compact" })))
  }
  drawSessionAxis(axis, sessions, slotW, plotW, plotH)
  axis.appendChild(svgEl("line", {
    x1: 0, y1: plotH, x2: plotW, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))

  for (let index = 0; index < sessions.length; index = index + 1) {
    const session = sessions[index]
    if (session.v === null || session.v < 0) {
      continue
    }
    const cx = (index + 0.5) * slotW
    const barY = valScale(session.v)
    const hasDirection = session.o !== null && session.c !== null
    const rising = hasDirection === true && session.c >= session.o

    let barColor = seriesColor
    let opacity = 0.8
    if (byDirection === true && hasDirection === true) {
      barColor = rising === true ? UP_COLOR : DOWN_COLOR
      opacity = rising === true ? 0.85 : 0.55
    }

    const direction = hasDirection === true ? (rising === true ? "rising" : "falling") : ""
    const ariaLabel = `Volume ${sessionText(session)}: ${formatNumber(session.v)}` +
      (direction !== "" ? ` (${direction})` : "")

    const bar = svgEl("rect", {
      x: cx - barW / 2, y: barY, width: barW, height: Math.max(plotH - barY, 1),
      fill: barColor, "fill-opacity": opacity, stroke: barColor, "stroke-width": slotW < 4 ? 0 : 1,
      part: "bar", tabindex: "0", role: "img", "aria-label": ariaLabel
    }, [])
    bar.appendChild(svgEl("title", null, ariaLabel))

    const emitSession = session
    const clickHandler = () => {
      ctx.emit("mj-chart-bar-click", {
        date: emitSession.source.t,
        volume: emitSession.v,
        open: emitSession.o,
        close: emitSession.c,
        count: emitSession.count
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

  return root
}


registerRenderer("volume", render, { minHeight: 200 });
