/*
 * upset.js
 *
 * UpSet plot renderer – set-intersection bars + membership matrix.
 *
 * JSON shape (ctx.raw):
 *   sets[]           { name, size }          – individual sets
 *   intersections[]  { sets[], size }         – all named intersections
 *
 * Layout regions:
 *   1. Top: vertical bars for intersection sizes (sorted by size desc)
 *   2. Bottom: dot membership matrix (one row per set, one column per
 *      intersection)
 *   3. Left (bottom region): horizontal bars for individual set sizes
 *
 * `sort` attr: "size" (default) | "degree"
 *
 * Registers: "upset"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber } from "../svgdraw.js";
import { linearScale, bandScale, niceTicks } from "../scales.js";


export function render(ctx) {
  /*
   * Render an UpSet plot.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw
  const sets = (raw !== null && raw !== undefined && Array.isArray(raw.sets))
    ? raw.sets
    : []
  const intersections = (raw !== null && raw !== undefined && Array.isArray(raw.intersections))
    ? raw.intersections
    : []
  const sortMode = ctx.attrs("sort", "size")

  const root = svgEl("g", { part: "plot" }, [])

  if (sets.length === 0 || intersections.length === 0) {
    return root
  }

  /* Sort intersections. */
  const sorted = intersections.slice().sort((a, b) => {
    const av = typeof a.size === "number" ? a.size : 0
    const bv = typeof b.size === "number" ? b.size : 0
    if (sortMode === "degree") {
      const da = Array.isArray(a.sets) ? a.sets.length : 0
      const db = Array.isArray(b.sets) ? b.sets.length : 0
      if (da !== db) {
        return da - db
      }
    }
    return bv - av
  })

  /* Layout constants. */
  const leftBarW = 80
  const setLabelW = 72
  const marginTop = 12
  const marginRight = 12
  const marginBottom = 8
  const topBarFraction = 0.55   /* fraction of height for the top bar region */

  const totalW = Math.max(ctx.width - marginRight, 10)
  const totalH = Math.max(ctx.height - marginTop - marginBottom, 10)

  /* Column band for intersection columns. */
  const colW = Math.max((totalW - leftBarW - setLabelW) / sorted.length, 8)
  const matrixH = totalH * (1 - topBarFraction)
  const rowH = sets.length > 0 ? matrixH / sets.length : 20

  /* Max intersection size for y-scale. */
  let maxInter = 1
  for (let i = 0; i < sorted.length; i = i + 1) {
    const sz = typeof sorted[i].size === "number" ? sorted[i].size : 0
    if (sz > maxInter) { maxInter = sz }
  }

  /* Max individual set size for left bar scale. */
  let maxSetSize = 1
  for (let s = 0; s < sets.length; s = s + 1) {
    const sz = typeof sets[s].size === "number" ? sets[s].size : 0
    if (sz > maxSetSize) { maxSetSize = sz }
  }

  const topBarH = totalH * topBarFraction
  const topBarYScale = linearScale([0, maxInter], [topBarH, 0])
  const leftBarXScale = linearScale([0, maxSetSize], [leftBarW, 0])

  const plot = svgEl("g", {
    transform: `translate(0,${marginTop})`
  }, [])
  root.appendChild(plot)

  /* ── Top bar region ──────────────────────────────────────────── */
  const topBarGroup = svgEl("g", {
    transform: `translate(${setLabelW + leftBarW},0)`
  }, [])
  plot.appendChild(topBarGroup)

  /* Y-axis gridlines for top bars. */
  const topTicks = niceTicks(0, maxInter, 4)
  for (let t = 0; t < topTicks.length; t = t + 1) {
    const tickY = topBarYScale(topTicks[t])
    topBarGroup.appendChild(svgEl("line", {
      x1: 0, y1: tickY,
      x2: sorted.length * colW, y2: tickY,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    topBarGroup.appendChild(svgEl("text", {
      x: -4, y: tickY + 4,
      "text-anchor": "end", "font-size": 10,
      fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(topTicks[t])))
  }

  /* Intersection bars. */
  for (let i = 0; i < sorted.length; i = i + 1) {
    const inter = sorted[i]
    const sz = typeof inter.size === "number" ? inter.size : 0
    const barX = i * colW + colW * 0.1
    const barW = colW * 0.8
    const barY = topBarYScale(sz)
    const barH = topBarH - barY
    const membership = Array.isArray(inter.sets) ? inter.sets : []
    const ariaLabel = `${membership.join(" ∩ ")}: ${formatNumber(sz)}`

    const barEl = svgEl("g", {
      tabindex: "0",
      role: "img",
      "aria-label": ariaLabel,
      part: "upset-bar"
    }, [])

    barEl.appendChild(svgEl("rect", {
      x: barX, y: barY,
      width: barW, height: Math.max(barH, 1),
      rx: 2,
      fill: "var(--mj-color-accent-500, #2563eb)"
    }, []))

    barEl.appendChild(svgEl("title", null, ariaLabel))

    const capturedInter = inter
    const handler = () => {
      ctx.emit("mj-chart-upset-click", {
        sets: capturedInter.sets,
        size: capturedInter.size
      })
    }
    barEl.addEventListener("click", handler)
    barEl.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        handler()
      }
    })

    topBarGroup.appendChild(barEl)
  }

  /* ── Matrix region ───────────────────────────────────────────── */
  const matrixGroup = svgEl("g", {
    transform: `translate(${setLabelW + leftBarW},${topBarH})`
  }, [])
  plot.appendChild(matrixGroup)

  /* Matrix background rows. */
  for (let s = 0; s < sets.length; s = s + 1) {
    matrixGroup.appendChild(svgEl("rect", {
      x: 0, y: s * rowH,
      width: sorted.length * colW, height: rowH,
      fill: s % 2 === 0
        ? "var(--mj-surface-subtle, #f8f9fb)"
        : "var(--mj-surface, #ffffff)"
    }, []))
  }

  /* Dots and connectors for each intersection column. */
  for (let i = 0; i < sorted.length; i = i + 1) {
    const inter = sorted[i]
    const membership = Array.isArray(inter.sets) ? inter.sets : []
    const colCX = i * colW + colW / 2

    /* Compute row indices of participating sets for the connector. */
    const memberRows = []
    for (let s = 0; s < sets.length; s = s + 1) {
      if (membership.includes(sets[s].name)) {
        memberRows.push(s)
      }
    }

    /* Vertical connector between first and last member dot. */
    if (memberRows.length >= 2) {
      const topDot = memberRows[0]
      const botDot = memberRows[memberRows.length - 1]
      matrixGroup.appendChild(svgEl("line", {
        x1: colCX, y1: topDot * rowH + rowH / 2,
        x2: colCX, y2: botDot * rowH + rowH / 2,
        stroke: "var(--mj-color-accent-500, #2563eb)",
        "stroke-width": 3
      }, []))
    }

    /* Dots. */
    for (let s = 0; s < sets.length; s = s + 1) {
      const isMember = membership.includes(sets[s].name)
      matrixGroup.appendChild(svgEl("circle", {
        cx: colCX,
        cy: s * rowH + rowH / 2,
        r: Math.min(rowH * 0.3, 8),
        fill: isMember === true
          ? "var(--mj-color-accent-500, #2563eb)"
          : "var(--mj-border, #e0e3e9)"
      }, []))
    }
  }

  /* ── Left bars (individual set sizes) ───────────────────────── */
  const leftGroup = svgEl("g", {
    transform: `translate(${setLabelW},${topBarH})`
  }, [])
  plot.appendChild(leftGroup)

  for (let s = 0; s < sets.length; s = s + 1) {
    const set = sets[s]
    const sz = typeof set.size === "number" ? set.size : 0
    const barX = leftBarXScale(sz)
    const barW = leftBarW - barX
    const barY = s * rowH + rowH * 0.1
    const barH = rowH * 0.8
    const ariaLabel = `${set.name}: ${formatNumber(sz)}`

    leftGroup.appendChild(svgEl("rect", {
      x: barX, y: barY,
      width: Math.max(barW, 1), height: barH,
      rx: 2,
      fill: "var(--mj-color-accent-300, #80a8ff)",
      part: "upset-set-bar"
    }, []))

    leftGroup.appendChild(svgEl("title", null, ariaLabel))
  }

  /* Set name labels. */
  const labelGroup = svgEl("g", {
    transform: `translate(0,${topBarH})`
  }, [])
  plot.appendChild(labelGroup)

  for (let s = 0; s < sets.length; s = s + 1) {
    labelGroup.appendChild(svgEl("text", {
      x: setLabelW - 4,
      y: s * rowH + rowH / 2 + 4,
      "text-anchor": "end",
      "font-size": 11,
      fill: "var(--mj-text, #14181f)"
    }, escapeHtml(sets[s].name)))
  }

  return root
}


registerRenderer("upset", render)
