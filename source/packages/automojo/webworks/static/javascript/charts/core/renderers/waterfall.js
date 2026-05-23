/*
 * waterfall.js
 *
 * Waterfall (bridge / cascade) renderer.
 *
 * Registers: "waterfall"
 *
 * ctx.model.categories            -- bar labels
 * ctx.model.series[0].values      -- delta amounts (null = computed bar)
 * ctx.model.series[0].kinds       -- "start" | "delta" | "subtotal" | "total"
 * ctx.orientation                 -- "vertical" (default) | "horizontal"
 *
 * Positive deltas: --mj-chart-positive (falls back to success green)
 * Negative deltas: --mj-chart-negative (falls back to danger red)
 * Start / total / subtotal: --mj-color-neutral-500
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber } from "../svgdraw.js";
import { linearScale, bandScale, niceTicks } from "../scales.js";


const COLOR_POSITIVE = "var(--mj-chart-positive, var(--mj-color-success, #15803d))";
const COLOR_NEGATIVE = "var(--mj-chart-negative, var(--mj-color-danger, #b91c1c))";
const COLOR_NEUTRAL  = "var(--mj-color-neutral-500, #6b7280)";


function _buildBars(categories, values, kinds) {
  /*
   * Compute running totals and the [base, top] pixel-domain value for each
   * bar. Returns an array of { category, value, base, top, kind, color }.
   *
   * :returns: Array of bar descriptors.
   */
  const bars = [];
  let running = 0;

  for (let index = 0; index < categories.length; index = index + 1) {
    const kind = (kinds && kinds[index]) ? kinds[index] : "delta";
    let value = typeof values[index] === "number" ? values[index] : 0;
    let base = 0;
    let top = 0;
    let color = COLOR_NEUTRAL;

    if (kind === "start") {
      base = 0;
      top = value;
      running = value;
      color = COLOR_NEUTRAL;
    } else if (kind === "delta") {
      base = running;
      top = running + value;
      running = running + value;
      color = value >= 0 ? COLOR_POSITIVE : COLOR_NEGATIVE;
    } else if (kind === "subtotal" || kind === "total") {
      value = running;
      base = 0;
      top = running;
      color = COLOR_NEUTRAL;
    }

    bars.push({
      category: categories[index],
      value: value,
      base: base,
      top: top,
      kind: kind,
      color: color
    });
  }
  return bars;
}


export function render(ctx) {
  /*
   * Render a waterfall chart.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const model = ctx.model;
  const horizontal = ctx.orientation === "horizontal";
  const root = svgEl("g", { part: "plot" }, []);

  const categories = model.categories;
  const series = model.series;
  if (categories.length === 0 || series.length === 0) {
    return root;
  }

  const firstSeries = series[0];
  const kinds = firstSeries.kinds || null;
  const bars = _buildBars(categories, firstSeries.values, kinds);

  /* Value domain must span all bases and tops. */
  let valueMin = 0;
  let valueMax = 0;
  for (let index = 0; index < bars.length; index = index + 1) {
    const bar = bars[index];
    if (bar.base < valueMin) {
      valueMin = bar.base;
    }
    if (bar.top < valueMin) {
      valueMin = bar.top;
    }
    if (bar.base > valueMax) {
      valueMax = bar.base;
    }
    if (bar.top > valueMax) {
      valueMax = bar.top;
    }
  }
  if (valueMax === valueMin) {
    valueMax = valueMin + 1;
  }

  const margin = { top: 16, right: 16, bottom: 40, left: 52 };
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10);
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10);

  const catLabels = bars.map((b) => b.category);
  const cat = bandScale(catLabels, [0, horizontal ? plotH : plotW], 0.2);
  const val = horizontal
    ? linearScale([valueMin, valueMax], [0, plotW])
    : linearScale([valueMin, valueMax], [plotH, 0]);

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, []);
  root.appendChild(plot);

  /* Value axis gridlines and tick labels. */
  const ticks = niceTicks(valueMin, valueMax, 5);
  for (let t = 0; t < ticks.length; t = t + 1) {
    const tick = ticks[t];
    if (horizontal === true) {
      const x = val(tick);
      plot.appendChild(svgEl("line", {
        x1: x, y1: 0, x2: x, y2: plotH,
        stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
      }, []));
      plot.appendChild(svgEl("text", {
        x: x, y: plotH + 16, "text-anchor": "middle",
        "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
      }, formatNumber(tick)));
    } else {
      const y = val(tick);
      plot.appendChild(svgEl("line", {
        x1: 0, y1: y, x2: plotW, y2: y,
        stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
      }, []));
      plot.appendChild(svgEl("text", {
        x: -8, y: y + 4, "text-anchor": "end",
        "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
      }, formatNumber(tick)));
    }
  }

  /* Axis baseline at zero. */
  const zero = val(0);
  if (horizontal === true) {
    plot.appendChild(svgEl("line", {
      x1: zero, y1: 0, x2: zero, y2: plotH,
      stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
    }, []));
  } else {
    plot.appendChild(svgEl("line", {
      x1: 0, y1: zero, x2: plotW, y2: zero,
      stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
    }, []));
  }

  const bandwidth = cat.bandwidth();

  /* Draw bars and connectors. */
  for (let index = 0; index < bars.length; index = index + 1) {
    const bar = bars[index];
    const bandStart = cat(bar.category);

    let rect = null;

    if (horizontal === true) {
      const x1 = val(bar.base);
      const x2 = val(bar.top);
      rect = svgEl("rect", {
        x: Math.min(x1, x2).toFixed(2),
        y: bandStart.toFixed(2),
        width: Math.max(Math.abs(x2 - x1), 1).toFixed(2),
        height: Math.max(bandwidth, 1).toFixed(2),
        rx: 2,
        fill: bar.color,
        part: "bar",
        tabindex: "0",
        role: "img",
        "aria-label": `${escapeHtml(bar.category)}: ${formatNumber(bar.value)}`
      }, []);
    } else {
      const y1 = val(bar.base);
      const y2 = val(bar.top);
      rect = svgEl("rect", {
        x: bandStart.toFixed(2),
        y: Math.min(y1, y2).toFixed(2),
        width: Math.max(bandwidth, 1).toFixed(2),
        height: Math.max(Math.abs(y2 - y1), 1).toFixed(2),
        rx: 2,
        fill: bar.color,
        part: "bar",
        tabindex: "0",
        role: "img",
        "aria-label": `${escapeHtml(bar.category)}: ${formatNumber(bar.value)}`
      }, []);
    }

    rect.appendChild(svgEl("title", null, `${bar.category}: ${formatNumber(bar.value)}`));

    const handler = () => {
      ctx.emit("mj-chart-bar-click", {
        category: bar.category,
        value: bar.value,
        kind: bar.kind
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

    /* Connector line to next floating delta bar. */
    if (index < bars.length - 1) {
      const nextBar = bars[index + 1];
      if (nextBar.kind === "delta") {
        const connectY = val(bar.top);
        const nextBandStart = cat(nextBar.category);
        if (horizontal === true) {
          const connectX = val(bar.top);
          plot.appendChild(svgEl("line", {
            x1: connectX.toFixed(2),
            y1: (bandStart + bandwidth).toFixed(2),
            x2: connectX.toFixed(2),
            y2: (nextBandStart).toFixed(2),
            stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1,
            "stroke-dasharray": "3,2"
          }, []));
        } else {
          plot.appendChild(svgEl("line", {
            x1: bandStart.toFixed(2),
            y1: connectY.toFixed(2),
            x2: (nextBandStart + bandwidth).toFixed(2),
            y2: connectY.toFixed(2),
            stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1,
            "stroke-dasharray": "3,2"
          }, []));
        }
      }
    }

    /* Category label. */
    if (horizontal === true) {
      plot.appendChild(svgEl("text", {
        x: -8,
        y: (bandStart + bandwidth / 2 + 4).toFixed(2),
        "text-anchor": "end",
        "font-size": 11,
        fill: "var(--mj-text, #14181f)"
      }, escapeHtml(bar.category)));
    } else {
      plot.appendChild(svgEl("text", {
        x: (bandStart + bandwidth / 2).toFixed(2),
        y: (plotH + 18).toFixed(2),
        "text-anchor": "middle",
        "font-size": 11,
        fill: "var(--mj-text, #14181f)"
      }, escapeHtml(bar.category)));
    }
  }

  return root;
}


registerRenderer("waterfall", render);
