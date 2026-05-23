/*
 * waffle.js
 *
 * Waffle (unit grid) renderer.
 *
 * Registers: "waffle"
 *
 * ctx.model.categories        -- category labels
 * ctx.model.series[0].values  -- cell count per category; must sum to cols*rows
 * ctx.model.meta.grid         -- optional { cols, rows }; default 10x10
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber } from "../svgdraw.js";


export function render(ctx) {
  /*
   * Render a waffle chart.
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

  const firstSeries = series[0];

  const grid = (model.meta && model.meta.grid) ? model.meta.grid : {};
  const cols = (typeof grid.cols === "number" && grid.cols > 0) ? grid.cols : 10;
  const rows = (typeof grid.rows === "number" && grid.rows > 0) ? grid.rows : 10;
  const totalCells = cols * rows;

  /* Normalize values to cell counts. */
  let rawTotal = 0;
  for (let index = 0; index < firstSeries.values.length; index = index + 1) {
    const v = firstSeries.values[index];
    rawTotal = rawTotal + (typeof v === "number" ? v : 0);
  }
  if (rawTotal === 0) {
    return root;
  }

  /* Assign cells per category proportionally, no cell left behind. */
  const cellCounts = [];
  let assignedTotal = 0;
  for (let index = 0; index < categories.length; index = index + 1) {
    const v = typeof firstSeries.values[index] === "number" ? firstSeries.values[index] : 0;
    const exact = (v / rawTotal) * totalCells;
    const floored = Math.floor(exact);
    cellCounts.push({ index: index, count: floored, remainder: exact - floored });
    assignedTotal = assignedTotal + floored;
  }

  /* Distribute remaining cells by largest remainder. */
  let remaining = totalCells - assignedTotal;
  cellCounts.sort((a, b) => b.remainder - a.remainder);
  for (let k = 0; k < remaining; k = k + 1) {
    cellCounts[k].count = cellCounts[k].count + 1;
  }
  cellCounts.sort((a, b) => a.index - b.index);

  /* Build flat cell-to-category map (reading order: left→right, top→bottom). */
  const cellCategory = [];
  for (let catIndex = 0; catIndex < categories.length; catIndex = catIndex + 1) {
    for (let c = 0; c < cellCounts[catIndex].count; c = c + 1) {
      cellCategory.push(catIndex);
    }
  }
  while (cellCategory.length < totalCells) {
    cellCategory.push(categories.length - 1);
  }

  const margin = { top: 16, right: 16, bottom: 16, left: 16 };
  const plotW = Math.max(ctx.width - margin.left - margin.right, cols);
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, rows);

  const cellW = plotW / cols;
  const cellH = plotH / rows;
  const gap = Math.min(cellW, cellH) * 0.1;

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, []);
  root.appendChild(plot);

  for (let row = 0; row < rows; row = row + 1) {
    for (let col = 0; col < cols; col = col + 1) {
      const cellIndex = row * cols + col;
      const catIndex = cellCategory[cellIndex];
      const color = ctx.colorFor(catIndex);
      const catLabel = categories[catIndex];
      const value = typeof firstSeries.values[catIndex] === "number" ? firstSeries.values[catIndex] : 0;
      const fraction = value / rawTotal;

      const x = col * cellW + gap / 2;
      const y = row * cellH + gap / 2;
      const w = Math.max(cellW - gap, 1);
      const h = Math.max(cellH - gap, 1);

      const cell = svgEl("rect", {
        x: x.toFixed(2), y: y.toFixed(2),
        width: w.toFixed(2), height: h.toFixed(2),
        rx: Math.min(w, h) * 0.1,
        fill: color,
        part: "cell",
        tabindex: "0",
        role: "img",
        "aria-label": `${escapeHtml(catLabel)}: ${formatNumber(value)} (${(fraction * 100).toFixed(1)}%)`
      }, []);

      cell.appendChild(svgEl("title", null,
        `${catLabel}: ${formatNumber(value)} (${(fraction * 100).toFixed(1)}%)`));

      const handler = () => {
        ctx.emit("mj-chart-cell-click", {
          category: catLabel,
          value: value,
          fraction: fraction
        });
      };
      cell.addEventListener("click", handler);
      cell.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          handler();
        }
      });

      plot.appendChild(cell);
    }
  }

  return root;
}


registerRenderer("waffle", render);
