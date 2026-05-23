/*
 * mosaic.js
 *
 * Mosaic plot (spine plot / contingency mosaic) renderer.
 *
 * Registers: "mosaic"
 *
 * ctx.model.categories        -- column variable levels (e.g. passenger class)
 * ctx.model.series            -- row variable levels; series[s].values[c] = cell frequency
 * ctx.model.meta["equal-widths"] -- true → spine plot (all columns equal width)
 * ctx.model.meta["residuals"]    -- true → color by Pearson residual (not yet rendered;
 *                                   the flag is respected via --mj-chart-positive/negative)
 *
 * Column widths are proportional to column marginal totals (unless equal-widths).
 * Segment heights within each column are proportional to conditional frequency.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber } from "../svgdraw.js";
import { linearScale, niceTicks } from "../scales.js";


export function render(ctx) {
  /*
   * Render a mosaic plot.
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

  const equalWidths = model.meta && model.meta["equal-widths"] === true;

  /* Column marginal totals. */
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

  const margin = { top: 16, right: 16, bottom: 48, left: 16 };
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10);
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10);

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, []);
  root.appendChild(plot);

  /* Y axis: 0–100% gridlines. */
  const yScale = linearScale([0, 100], [plotH, 0]);
  const yTicks = niceTicks(0, 100, 5);
  for (let t = 0; t < yTicks.length; t = t + 1) {
    const tick = yTicks[t];
    const y = yScale(tick);
    plot.appendChild(svgEl("line", {
      x1: 0, y1: y.toFixed(2), x2: plotW, y2: y.toFixed(2),
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []));
  }

  /* Axis baseline. */
  plot.appendChild(svgEl("line", {
    x1: 0, y1: plotH, x2: plotW, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []));

  const colCount = categories.length;
  const gapPx = colCount > 1 ? Math.min(4, plotW * 0.01) : 0;
  const totalGap = gapPx * (colCount - 1);
  const availW = plotW - totalGap;

  let xCursor = 0;
  for (let c = 0; c < categories.length; c = c + 1) {
    const category = categories[c];
    const colTotal = colTotals[c];
    const colWidthFraction = equalWidths ? (1 / colCount) : (colTotal / grandTotal);
    const colWidthPx = colWidthFraction * availW;

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
        width: Math.max(colWidthPx, 1).toFixed(2),
        height: Math.max(segH, 1).toFixed(2),
        fill: color,
        part: "cell",
        tabindex: "0",
        role: "img",
        "aria-label": `${escapeHtml(series[s].name)}, ${escapeHtml(category)}: ${formatNumber(value)} (${pct.toFixed(1)}%)`
      }, []);

      rect.appendChild(svgEl("title", null,
        `${series[s].name}, ${category}: ${formatNumber(value)} (${pct.toFixed(1)}%)`));

      const handler = () => {
        ctx.emit("mj-chart-cell-click", {
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

      /* Row label inside cell when tall enough. */
      if (segH >= 14 && colWidthPx >= 30) {
        const midY = Math.min(segTop, segBot) + segH / 2;
        plot.appendChild(svgEl("text", {
          x: (xCursor + colWidthPx / 2).toFixed(2),
          y: midY.toFixed(2),
          "text-anchor": "middle",
          "dominant-baseline": "middle",
          "font-size": 10,
          fill: "var(--mj-surface, #ffffff)",
          "pointer-events": "none"
        }, escapeHtml(series[s].name)));
      }

      yCursor = yCursor - pct;
    }

    /* Category label. */
    const labelX = xCursor + colWidthPx / 2;
    plot.appendChild(svgEl("text", {
      x: labelX.toFixed(2),
      y: (plotH + 16).toFixed(2),
      "text-anchor": "middle",
      "font-size": 11,
      fill: "var(--mj-text, #14181f)"
    }, escapeHtml(category)));

    /* Column marginal total. */
    plot.appendChild(svgEl("text", {
      x: labelX.toFixed(2),
      y: (plotH + 30).toFixed(2),
      "text-anchor": "middle",
      "font-size": 9,
      fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(colTotal)));

    xCursor = xCursor + colWidthPx + gapPx;
  }

  /* Row (series) labels on right edge. */
  let yCursorRight = 100;
  for (let s = 0; s < series.length; s = s + 1) {
    /* Use the last column proportions to place right-side labels. */
    const lastCol = categories.length - 1;
    const lastTotal = colTotals[lastCol];
    const rawLast = series[s].values[lastCol];
    const valueLast = typeof rawLast === "number" ? rawLast : 0;
    const pctLast = lastTotal > 0 ? (Math.abs(valueLast) / lastTotal) * 100 : 0;

    const midPct = yCursorRight - pctLast / 2;
    const midY = yScale(midPct);

    plot.appendChild(svgEl("text", {
      x: (plotW + 6).toFixed(2),
      y: midY.toFixed(2),
      "text-anchor": "start",
      "dominant-baseline": "middle",
      "font-size": 10,
      fill: "var(--mj-text-muted, #6b7280)"
    }, escapeHtml(series[s].name)));

    yCursorRight = yCursorRight - pctLast;
  }

  return root;
}


registerRenderer("mosaic", render);
