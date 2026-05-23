/*
 * funnel.js
 *
 * Funnel / conversion-funnel renderer.
 *
 * Registers: "funnel"
 *
 * ctx.model shape (common envelope):
 *   categories: string[]   stage names
 *   series[0].values: number[]   stage counts / rates
 *
 * Modes:
 *   default  — trapezoid segments narrow toward the last stage (funnel)
 *   pyramid  — segments widen toward the last stage (via mode="pyramid")
 *
 * Orientation:
 *   "vertical"   stages top → bottom (default)
 *   "horizontal" stages left → right
 *
 * SVG primitives: <polygon> per segment, <text> for stage and value labels.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber } from "../svgdraw.js";
import { linearScale } from "../scales.js";


const MARGIN = { top: 16, right: 80, bottom: 16, left: 80 };
const SEGMENT_GAP = 4;


export function render(ctx) {
  /*
   * Render a funnel or pyramid chart.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const model = ctx.model;
  const mode = ctx.attrs("mode", "funnel");
  const isPyramid = mode === "pyramid";
  const horizontal = ctx.orientation === "horizontal";

  const root = svgEl("g", { part: "plot" }, []);

  const categories = model.categories;
  const series = model.series;

  if (categories === undefined || categories.length === 0 ||
      series === undefined || series.length === 0) {
    return root;
  }

  const values = series[0].values;
  if (values === undefined || values.length === 0) {
    return root;
  }

  const plotW = Math.max(ctx.width - MARGIN.left - MARGIN.right, 10);
  const plotH = Math.max(ctx.height - MARGIN.top - MARGIN.bottom, 10);

  const plot = svgEl("g", { transform: `translate(${MARGIN.left},${MARGIN.top})` }, []);
  root.appendChild(plot);

  const n = categories.length;
  const numericValues = values.map((v) => typeof v === "number" ? v : 0);
  const maxValue = Math.max(...numericValues, 1);

  /* Each stage gets equal space along the primary axis. */
  const primarySpan = horizontal ? plotW : plotH;
  const crossSpan = horizontal ? plotH : plotW;
  const segmentStep = (primarySpan - SEGMENT_GAP * (n - 1)) / n;

  /* Half-width scale: maps value to half of cross-span. */
  const halfWidthScale = linearScale([0, maxValue], [0, crossSpan / 2]);

  for (let i = 0; i < n; i = i + 1) {
    const value = numericValues[i];
    const nextValue = i + 1 < n ? numericValues[i + 1] : 0;

    /* In pyramid mode the final stage is wider, so reverse the roles. */
    const topValue = isPyramid ? nextValue : value;
    const bottomValue = isPyramid ? value : nextValue;

    const primaryStart = i * (segmentStep + SEGMENT_GAP);
    const primaryEnd = primaryStart + segmentStep;

    const halfTop = halfWidthScale(value);
    const halfBottom = i + 1 < n ? halfWidthScale(nextValue) : halfWidthScale(0);
    const crossCenter = crossSpan / 2;

    let pts;
    if (horizontal === true) {
      /* Left edge: y = crossCenter ± halfTop
         Right edge: y = crossCenter ± halfBottom */
      const lT = crossCenter - halfTop;
      const lB = crossCenter + halfTop;
      const rT = crossCenter - halfBottom;
      const rB = crossCenter + halfBottom;
      pts = `${primaryStart.toFixed(2)},${lT.toFixed(2)} ` +
        `${primaryEnd.toFixed(2)},${rT.toFixed(2)} ` +
        `${primaryEnd.toFixed(2)},${rB.toFixed(2)} ` +
        `${primaryStart.toFixed(2)},${lB.toFixed(2)}`;
    } else {
      /* Top edge: x = crossCenter ± halfTop
         Bottom edge: x = crossCenter ± halfBottom */
      const tL = crossCenter - halfTop;
      const tR = crossCenter + halfTop;
      const bL = crossCenter - halfBottom;
      const bR = crossCenter + halfBottom;
      pts = `${tL.toFixed(2)},${primaryStart.toFixed(2)} ` +
        `${tR.toFixed(2)},${primaryStart.toFixed(2)} ` +
        `${bR.toFixed(2)},${primaryEnd.toFixed(2)} ` +
        `${bL.toFixed(2)},${primaryEnd.toFixed(2)}`;
    }

    const color = ctx.colorFor(i);
    const category = categories[i];

    const polygon = svgEl("polygon", {
      points: pts,
      fill: color,
      "fill-opacity": "0.85",
      stroke: "var(--mj-bg, #ffffff)",
      "stroke-width": SEGMENT_GAP,
      part: "segment",
      tabindex: "0",
      role: "img",
      "aria-label": `${escapeHtml(category)}: ${formatNumber(value)}`
    }, []);
    polygon.appendChild(svgEl("title", null,
      `${category}: ${formatNumber(value)}`));

    const capturedCategory = category;
    const capturedValue = value;
    const capturedIndex = i;
    const clickHandler = () => {
      ctx.emit("mj-chart-segment-click", {
        category: capturedCategory,
        value: capturedValue,
        index: capturedIndex
      });
    };
    polygon.addEventListener("click", clickHandler);
    polygon.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        clickHandler();
      }
    });
    plot.appendChild(polygon);

    /* Stage label and value label. */
    const midPrimary = primaryStart + segmentStep / 2;

    if (horizontal === true) {
      /* Label left of the segment. */
      plot.appendChild(svgEl("text", {
        x: (primaryStart - 6).toFixed(2),
        y: (crossCenter + 4).toFixed(2),
        "text-anchor": "end",
        "font-size": 11,
        fill: "var(--mj-text, #14181f)"
      }, escapeHtml(category)));
      /* Value label centered in segment. */
      plot.appendChild(svgEl("text", {
        x: midPrimary.toFixed(2),
        y: (crossCenter + 4).toFixed(2),
        "text-anchor": "middle",
        "font-size": 11,
        fill: "var(--mj-text-on-accent, #ffffff)",
        "font-weight": "600"
      }, formatNumber(value)));
    } else {
      /* Label right of the segment. */
      plot.appendChild(svgEl("text", {
        x: (crossSpan + 6).toFixed(2),
        y: (midPrimary + 4).toFixed(2),
        "text-anchor": "start",
        "font-size": 11,
        fill: "var(--mj-text, #14181f)"
      }, escapeHtml(category)));
      /* Value label centered in segment. */
      plot.appendChild(svgEl("text", {
        x: (crossCenter).toFixed(2),
        y: (midPrimary + 4).toFixed(2),
        "text-anchor": "middle",
        "font-size": 11,
        fill: "var(--mj-text-on-accent, #ffffff)",
        "font-weight": "600"
      }, formatNumber(value)));
    }

    /* Drop-off percentage annotation between stages. */
    if (i + 1 < n && numericValues[i] > 0) {
      const dropPct = ((numericValues[i] - numericValues[i + 1]) / numericValues[i] * 100).toFixed(1);
      const gapPrimary = primaryEnd + SEGMENT_GAP / 2;
      if (horizontal === true) {
        plot.appendChild(svgEl("text", {
          x: gapPrimary.toFixed(2),
          y: (crossCenter - halfBottom - 4).toFixed(2),
          "text-anchor": "middle",
          "font-size": 10,
          fill: "var(--mj-text-muted, #6b7280)"
        }, `-${dropPct}%`));
      } else {
        plot.appendChild(svgEl("text", {
          x: (crossCenter + halfBottom + 4).toFixed(2),
          y: gapPrimary.toFixed(2),
          "text-anchor": "start",
          "font-size": 10,
          fill: "var(--mj-text-muted, #6b7280)"
        }, `-${dropPct}%`));
      }
    }
  }

  return root;
}


registerRenderer("funnel", render);
