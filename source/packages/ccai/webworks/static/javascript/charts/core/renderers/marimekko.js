/*
 * marimekko.js
 *
 * Marimekko (Mekko / mosaic bar) renderer.
 *
 * Registers: "marimekko"
 *
 * ctx.model.categories  -- column labels (e.g. countries)
 * ctx.model.series      -- breakdown series; values[i] = magnitude for column i
 *
 * Column widths are proportional to column totals as a share of the grand
 * total. Segment heights within each column are normalized to 100%.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber } from "../svgdraw.js";
import { linearScale, niceTicks } from "../scales.js";


export function render(ctx) {
  /*
   * Render a Marimekko chart.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const model = ctx.model;
  const root = svgEl("g", { part: "plot" }, []);

  const categories = model.categories;
  const series = model.series;
  if (categories.length === 0 || series.length === 0) {
    return root;
  }

  /* Column totals. */
  const colTotals = [];
  for (let c = 0; c < categories.length; c = c + 1) {
    let total = 0;
    for (let s = 0; s < series.length; s = s + 1) {
      const v = series[s].values[c];
      total = total + (typeof v === "number" ? Math.abs(v) : 0);
    }
    colTotals.push(total);
  }

  let grandTotal = 0;
  for (let c = 0; c < colTotals.length; c = c + 1) {
    grandTotal = grandTotal + colTotals[c];
  }
  if (grandTotal === 0) {
    return root;
  }

  const margin = { top: 16, right: 16, bottom: 40, left: 52 };
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10);
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10);

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, []);
  root.appendChild(plot);

  /* Y axis: 0–100% with gridlines. */
  const yScale = linearScale([0, 100], [plotH, 0]);
  const yTicks = niceTicks(0, 100, 5);
  for (let t = 0; t < yTicks.length; t = t + 1) {
    const tick = yTicks[t];
    const y = yScale(tick);
    plot.appendChild(svgEl("line", {
      x1: 0, y1: y.toFixed(2), x2: plotW, y2: y.toFixed(2),
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []));
    plot.appendChild(svgEl("text", {
      x: -8, y: (y + 4).toFixed(2), "text-anchor": "end",
      "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, `${tick}%`));
  }

  /* Axis baseline. */
  plot.appendChild(svgEl("line", {
    x1: 0, y1: plotH, x2: plotW, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []));

  /* Columns. */
  let xCursor = 0;
  for (let c = 0; c < categories.length; c = c + 1) {
    const category = categories[c];
    const colTotal = colTotals[c];
    const colWidthFraction = colTotal / grandTotal;
    const colWidthPx = colWidthFraction * plotW;

    let yCursor = 100;

    for (let s = 0; s < series.length; s = s + 1) {
      const rawValue = series[s].values[c];
      const value = typeof rawValue === "number" ? rawValue : 0;
      const pct = colTotal > 0 ? (Math.abs(value) / colTotal) * 100 : 0;
      const color = ctx.colorFor(series[s].name);

      const segTop = yScale(yCursor);
      const segBot = yScale(yCursor - pct);
      const segH = Math.abs(segBot - segTop);

      const rect = svgEl("rect", {
        x: xCursor.toFixed(2),
        y: Math.min(segTop, segBot).toFixed(2),
        width: Math.max(colWidthPx - 1, 1).toFixed(2),
        height: Math.max(segH, 1).toFixed(2),
        fill: color,
        part: "segment",
        tabindex: "0",
        role: "img",
        "aria-label": `${escapeHtml(series[s].name)}, ${escapeHtml(category)}: ${formatNumber(value)} (${pct.toFixed(1)}%)`
      }, []);

      rect.appendChild(svgEl("title", null,
        `${series[s].name}, ${category}: ${formatNumber(value)} (${pct.toFixed(1)}%)`));

      const handler = () => {
        ctx.emit("mj-chart-segment-click", {
          series: series[s].name,
          category: category,
          value: value,
          pct: pct
        });
      };
      rect.addEventListener("click", handler);
      rect.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          handler();
        }
      });

      plot.appendChild(rect);

      /* Segment label when tall enough. */
      if (segH >= 14 && colWidthPx >= 24) {
        const midY = Math.min(segTop, segBot) + segH / 2;
        plot.appendChild(svgEl("text", {
          x: (xCursor + colWidthPx / 2).toFixed(2),
          y: midY.toFixed(2),
          "text-anchor": "middle",
          "dominant-baseline": "middle",
          "font-size": 10,
          fill: "var(--mj-surface, #ffffff)",
          "pointer-events": "none"
        }, `${pct.toFixed(0)}%`));
      }

      yCursor = yCursor - pct;
    }

    /* Column separator. */
    if (c < categories.length - 1) {
      const sepX = xCursor + colWidthPx;
      plot.appendChild(svgEl("line", {
        x1: sepX.toFixed(2), y1: 0,
        x2: sepX.toFixed(2), y2: plotH,
        stroke: "var(--mj-surface, #ffffff)", "stroke-width": 2
      }, []));
    }

    /* Category label. */
    plot.appendChild(svgEl("text", {
      x: (xCursor + colWidthPx / 2).toFixed(2),
      y: (plotH + 16).toFixed(2),
      "text-anchor": "middle",
      "font-size": 11,
      fill: "var(--mj-text, #14181f)"
    }, escapeHtml(category)));

    /* Width annotation below category label. */
    if (colWidthPx >= 28) {
      plot.appendChild(svgEl("text", {
        x: (xCursor + colWidthPx / 2).toFixed(2),
        y: (plotH + 28).toFixed(2),
        "text-anchor": "middle",
        "font-size": 9,
        fill: "var(--mj-text-muted, #6b7280)"
      }, `${(colWidthFraction * 100).toFixed(0)}%`));
    }

    xCursor = xCursor + colWidthPx;
  }

  return root;
}


registerRenderer("marimekko", render);
