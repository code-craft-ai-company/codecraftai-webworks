/*
 * cohort.js
 *
 * Cohort retention grid renderer.
 *
 * JSON shape (ctx.raw):
 *   cohorts[]          array of { label, size, periods[] }
 *     label            cohort row label
 *     size             cohort starting size
 *     periods[]        retention rates (0–1) or absolute counts per period
 *   period_labels[]    column header labels ("Week 0", "Week 1", …)
 *   mode               "rate" (default) | "count"
 *
 * Also registers "retention" as an alias for the same renderer.
 *
 * Registers: "cohort", "retention"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, escapeHtml } from "../svgdraw.js";
import { linearScale } from "../scales.js";


/* Sequential color tokens – lightest (low) to darkest (high). */
const SEQ_TOKENS = [
  "var(--mj-chart-sequential-1, #eff6ff)",
  "var(--mj-chart-sequential-2, #bfdbfe)",
  "var(--mj-chart-sequential-3, #93c5fd)",
  "var(--mj-chart-sequential-4, #60a5fa)",
  "var(--mj-chart-sequential-5, #3b82f6)",
  "var(--mj-chart-sequential-6, #2563eb)",
  "var(--mj-chart-sequential-7, #1d4ed8)"
]


function _seqColor(rate) {
  /*
   * Map a 0–1 retention rate to a sequential color token.
   *
   * :returns: A CSS color string.
   */
  const clamped = Math.max(0, Math.min(1, rate))
  const idx = Math.round(clamped * (SEQ_TOKENS.length - 1))
  const color = SEQ_TOKENS[idx]
  return color
}


export function render(ctx) {
  /*
   * Render a cohort retention grid.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw
  const cohorts = (raw !== null && raw !== undefined && Array.isArray(raw.cohorts))
    ? raw.cohorts
    : []
  const periodLabels = (raw !== null && raw !== undefined && Array.isArray(raw.period_labels))
    ? raw.period_labels
    : []
  const mode = ctx.attrs("mode", "rate")

  const root = svgEl("g", { part: "plot" }, [])

  if (cohorts.length === 0) {
    return root
  }

  /* Determine max period count across all cohorts. */
  let maxPeriods = 0
  for (let r = 0; r < cohorts.length; r = r + 1) {
    const len = Array.isArray(cohorts[r].periods) ? cohorts[r].periods.length : 0
    if (len > maxPeriods) {
      maxPeriods = len
    }
  }

  if (maxPeriods === 0) {
    return root
  }

  /* Layout. */
  const marginLeft = 80
  const marginTop = 32
  const marginRight = 8
  const marginBottom = 8

  const gridW = Math.max(ctx.width - marginLeft - marginRight, 10)
  const gridH = Math.max(ctx.height - marginTop - marginBottom, 10)

  const cellW = gridW / maxPeriods
  const cellH = gridH / cohorts.length

  const plot = svgEl("g", {
    transform: `translate(${marginLeft},${marginTop})`
  }, [])
  root.appendChild(plot)

  /* Period column headers. */
  for (let p = 0; p < maxPeriods; p = p + 1) {
    const label = (p < periodLabels.length) ? periodLabels[p] : `P${p}`
    plot.appendChild(svgEl("text", {
      x: p * cellW + cellW / 2,
      y: -8,
      "text-anchor": "middle",
      "font-size": 10,
      fill: "var(--mj-text-muted, #6b7280)"
    }, escapeHtml(label)))
  }

  /* Cells. */
  for (let r = 0; r < cohorts.length; r = r + 1) {
    const cohort = cohorts[r]
    const periods = Array.isArray(cohort.periods) ? cohort.periods : []
    const cohortSize = typeof cohort.size === "number" ? cohort.size : 0

    /* Row label. */
    plot.appendChild(svgEl("text", {
      x: -6,
      y: r * cellH + cellH / 2 + 4,
      "text-anchor": "end",
      "font-size": 11,
      fill: "var(--mj-text, #14181f)"
    }, escapeHtml(cohort.label || String(r))))

    for (let p = 0; p < maxPeriods; p = p + 1) {
      if (p >= periods.length) {
        /* Gray out missing periods (cohort not yet old enough). */
        plot.appendChild(svgEl("rect", {
          x: p * cellW, y: r * cellH,
          width: cellW - 1, height: cellH - 1,
          fill: "var(--mj-surface-subtle, #f8f9fb)"
        }, []))
        continue
      }

      const rawVal = periods[p]
      const numVal = typeof rawVal === "number" ? rawVal : 0

      /* Compute display rate (0–1) for color, display string for text. */
      let rate = numVal
      let displayStr = ""
      if (mode === "count") {
        rate = cohortSize > 0 ? numVal / cohortSize : 0
        displayStr = formatNumber(numVal)
      } else {
        /* rate mode: values expected as 0–1 */
        rate = numVal > 1 ? numVal / 100 : numVal
        displayStr = formatNumber(rate * 100, { maximumFractionDigits: 0 }) + "%"
      }

      const cellColor = _seqColor(rate)
      /* Use dark text on light cells, light text on dark cells. */
      const textFill = rate > 0.55
        ? "var(--mj-text-on-accent, #ffffff)"
        : "var(--mj-text, #14181f)"

      const cellLabel = escapeHtml(cohort.label || String(r))
      const periodLabel = p < periodLabels.length ? periodLabels[p] : `Period ${p}`
      const ariaLabel = `${cellLabel}, ${periodLabel}: ${displayStr}`

      const cell = svgEl("g", {
        tabindex: "0",
        role: "img",
        "aria-label": ariaLabel,
        part: "cohort-cell"
      }, [])

      cell.appendChild(svgEl("rect", {
        x: p * cellW, y: r * cellH,
        width: cellW - 1, height: cellH - 1,
        fill: cellColor
      }, []))

      if (cellH >= 14 && cellW >= 28) {
        cell.appendChild(svgEl("text", {
          x: p * cellW + cellW / 2,
          y: r * cellH + cellH / 2 + 4,
          "text-anchor": "middle",
          "font-size": Math.min(11, cellH * 0.45),
          fill: textFill
        }, displayStr))
      }

      cell.appendChild(svgEl("title", null, ariaLabel))

      const capturedR = r
      const capturedP = p
      const capturedVal = numVal
      const capturedRate = rate
      const handler = () => {
        ctx.emit("mj-chart-cohort-click", {
          cohort: cohorts[capturedR].label,
          period: capturedP,
          value: capturedVal,
          rate: capturedRate
        })
      }
      cell.addEventListener("click", handler)
      cell.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })

      plot.appendChild(cell)
    }
  }

  return root
}


registerRenderer("cohort", render)
registerRenderer("retention", render)
