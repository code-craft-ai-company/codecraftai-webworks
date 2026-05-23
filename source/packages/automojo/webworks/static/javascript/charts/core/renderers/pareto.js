/*
 * pareto.js
 *
 * Pareto chart renderer (sorted bars + cumulative % line on secondary axis).
 *
 * Registers: "pareto"
 *
 * ctx.model.categories       -- defect / category labels
 * ctx.model.series[0].values -- frequencies / counts (need not be pre-sorted)
 * ctx.model.meta["pareto-line"] -- set false to suppress 80% reference line
 *
 * Left Y axis:  absolute count, linear [0, grand total]
 * Right Y axis: cumulative %, linear [0, 100]
 * X axis:       categories sorted descending by value
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber, linePath } from "../svgdraw.js";
import { linearScale, bandScale, niceTicks } from "../scales.js";


export function render(ctx) {
  /*
   * Render a Pareto chart.
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
  const showParetoLine = !(model.meta && model.meta["pareto-line"] === false);

  /* Sort categories by descending value. */
  const indexed = categories.map((cat, index) => {
    const v = firstSeries.values[index];
    return { category: cat, value: typeof v === "number" ? v : 0, origIndex: index };
  });
  indexed.sort((a, b) => b.value - a.value);

  const sortedCats = indexed.map((entry) => entry.category);
  const sortedVals = indexed.map((entry) => entry.value);

  /* Grand total and cumulative percentages. */
  let grandTotal = 0;
  for (let index = 0; index < sortedVals.length; index = index + 1) {
    grandTotal = grandTotal + sortedVals[index];
  }
  if (grandTotal === 0) {
    return root;
  }

  const cumPcts = [];
  let cumSum = 0;
  for (let index = 0; index < sortedVals.length; index = index + 1) {
    cumSum = cumSum + sortedVals[index];
    cumPcts.push((cumSum / grandTotal) * 100);
  }

  const margin = { top: 16, right: 52, bottom: 40, left: 52 };
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10);
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10);

  const cat = bandScale(sortedCats, [0, plotW], 0.15);
  const leftVal = linearScale([0, grandTotal], [plotH, 0]);
  const rightVal = linearScale([0, 100], [plotH, 0]);

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, []);
  root.appendChild(plot);

  /* Left axis gridlines and tick labels (absolute counts). */
  const leftTicks = niceTicks(0, grandTotal, 5);
  for (let t = 0; t < leftTicks.length; t = t + 1) {
    const tick = leftTicks[t];
    const y = leftVal(tick);
    plot.appendChild(svgEl("line", {
      x1: 0, y1: y.toFixed(2), x2: plotW, y2: y.toFixed(2),
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []));
    plot.appendChild(svgEl("text", {
      x: -8, y: (y + 4).toFixed(2), "text-anchor": "end",
      "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(tick)));
  }

  /* Right axis tick labels (cumulative %). */
  const rightTicks = niceTicks(0, 100, 5);
  for (let t = 0; t < rightTicks.length; t = t + 1) {
    const tick = rightTicks[t];
    const y = rightVal(tick);
    plot.appendChild(svgEl("text", {
      x: plotW + 8, y: (y + 4).toFixed(2), "text-anchor": "start",
      "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, `${tick}%`));
  }

  /* Axis baseline. */
  plot.appendChild(svgEl("line", {
    x1: 0, y1: plotH, x2: plotW, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []));

  /* Left axis line. */
  plot.appendChild(svgEl("line", {
    x1: 0, y1: 0, x2: 0, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []));

  /* Right axis line. */
  plot.appendChild(svgEl("line", {
    x1: plotW, y1: 0, x2: plotW, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []));

  const bandwidth = cat.bandwidth();
  const barColor = ctx.colorFor(0);

  /* Draw sorted bars. */
  for (let index = 0; index < sortedCats.length; index = index + 1) {
    const category = sortedCats[index];
    const value = sortedVals[index];
    const bandStart = cat(category);
    const barTop = leftVal(value);
    const barH = Math.max(plotH - barTop, 1);

    const rect = svgEl("rect", {
      x: bandStart.toFixed(2),
      y: barTop.toFixed(2),
      width: Math.max(bandwidth, 1).toFixed(2),
      height: barH.toFixed(2),
      rx: 2,
      fill: barColor,
      part: "bar",
      tabindex: "0",
      role: "img",
      "aria-label": `${escapeHtml(category)}: ${formatNumber(value)} (${cumPcts[index].toFixed(1)}% cumulative)`
    }, []);

    rect.appendChild(svgEl("title", null,
      `${category}: ${formatNumber(value)} (${cumPcts[index].toFixed(1)}% cumulative)`));

    const handler = () => {
      ctx.emit("mj-chart-bar-click", {
        category: category,
        value: value,
        cumulativePct: cumPcts[index]
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

    /* Category label. */
    plot.appendChild(svgEl("text", {
      x: (bandStart + bandwidth / 2).toFixed(2),
      y: (plotH + 18).toFixed(2),
      "text-anchor": "middle",
      "font-size": 11,
      fill: "var(--mj-text, #14181f)"
    }, escapeHtml(category)));
  }

  /* Cumulative % line. */
  const linePoints = [];
  for (let index = 0; index < sortedCats.length; index = index + 1) {
    const category = sortedCats[index];
    const bandStart = cat(category);
    const dotX = bandStart + bandwidth / 2;
    const dotY = rightVal(cumPcts[index]);
    linePoints.push({ x: dotX, y: dotY });
  }

  const pathData = linePath(linePoints);
  if (pathData !== "") {
    plot.appendChild(svgEl("path", {
      d: pathData,
      fill: "none",
      stroke: "var(--mj-color-danger, #b91c1c)",
      "stroke-width": 2
    }, []));
  }

  /* Dots on cumulative line. */
  for (let index = 0; index < linePoints.length; index = index + 1) {
    const pt = linePoints[index];
    const category = sortedCats[index];
    const cumulativePct = cumPcts[index];

    const dot = svgEl("circle", {
      cx: pt.x.toFixed(2),
      cy: pt.y.toFixed(2),
      r: 4,
      fill: "var(--mj-color-danger, #b91c1c)",
      stroke: "var(--mj-surface, #ffffff)",
      "stroke-width": 1.5,
      part: "dot",
      tabindex: "0",
      role: "img",
      "aria-label": `${escapeHtml(category)}: ${cumulativePct.toFixed(1)}% cumulative`
    }, []);

    dot.appendChild(svgEl("title", null,
      `${category}: ${cumulativePct.toFixed(1)}% cumulative`));

    const dotHandler = () => {
      ctx.emit("mj-chart-dot-click", {
        category: category,
        cumulativePct: cumulativePct
      });
    };
    dot.addEventListener("click", dotHandler);
    dot.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        dotHandler();
      }
    });
    plot.appendChild(dot);
  }

  /* 80% reference line. */
  if (showParetoLine === true) {
    const refY = rightVal(80);
    plot.appendChild(svgEl("line", {
      x1: 0, y1: refY.toFixed(2),
      x2: plotW, y2: refY.toFixed(2),
      stroke: "var(--mj-color-warning, #b45309)",
      "stroke-width": 1,
      "stroke-dasharray": "6,3"
    }, []));
    plot.appendChild(svgEl("text", {
      x: (plotW - 2).toFixed(2),
      y: (refY - 4).toFixed(2),
      "text-anchor": "end",
      "font-size": 10,
      fill: "var(--mj-color-warning, #b45309)"
    }, "80%"));
  }

  return root;
}


registerRenderer("pareto", render);
