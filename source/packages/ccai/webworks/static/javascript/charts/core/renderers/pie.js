/*
 * pie.js
 *
 * Pie and Donut renderer.
 *
 * Registers: "pie", "donut"
 *
 * ctx.model.categories  -- slice labels (up to 12; excess collapsed to "Other")
 * ctx.model.series[0]   -- first series only; .values are the slice magnitudes
 * ctx.attrs("inner-radius", "0") -- fraction 0-1; > 0 activates donut mode
 * ctx.model.meta["center-label"] -- optional string drawn at center (donut)
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, arcPath, formatNumber } from "../svgdraw.js";


const MAX_SLICES = 12;
const TWO_PI = Math.PI * 2;


function _buildSlices(categories, values) {
  /*
   * Collapse excess slices into "Other", compute proportions and angles.
   *
   * :returns: Array of { label, value, startAngle, endAngle }.
   */
  let cats = categories.slice();
  let vals = values.slice();

  if (cats.length > MAX_SLICES) {
    const kept = cats.slice(0, MAX_SLICES - 1);
    const keptVals = vals.slice(0, MAX_SLICES - 1);
    let otherSum = 0;
    for (let index = MAX_SLICES - 1; index < vals.length; index = index + 1) {
      const numeric = typeof vals[index] === "number" ? vals[index] : 0;
      otherSum = otherSum + numeric;
    }
    kept.push("Other");
    keptVals.push(otherSum);
    cats = kept;
    vals = keptVals;
  }

  let total = 0;
  for (let index = 0; index < vals.length; index = index + 1) {
    const numeric = typeof vals[index] === "number" ? vals[index] : 0;
    total = total + numeric;
  }

  if (total === 0) {
    return [];
  }

  const slices = [];
  let cursor = 0;
  for (let index = 0; index < cats.length; index = index + 1) {
    const value = typeof vals[index] === "number" ? vals[index] : 0;
    const fraction = value / total;
    const startAngle = cursor;
    const endAngle = cursor + fraction * TWO_PI;
    slices.push({
      label: cats[index],
      value: value,
      fraction: fraction,
      startAngle: startAngle,
      endAngle: endAngle
    });
    cursor = endAngle;
  }
  return slices;
}


export function render(ctx) {
  /*
   * Render a pie or donut chart.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const model = ctx.model;
  const root = svgEl("g", { part: "plot" }, []);

  const series = model.series;
  const categories = model.categories;
  if (categories.length === 0 || series.length === 0) {
    return root;
  }

  const firstSeries = series[0];
  const slices = _buildSlices(categories, firstSeries.values);
  if (slices.length === 0) {
    return root;
  }

  const innerRadiusAttr = parseFloat(ctx.attrs("inner-radius", "0"));
  const innerFraction = Number.isNaN(innerRadiusAttr) ? 0 : Math.min(Math.max(innerRadiusAttr, 0), 0.95);

  const margin = { top: 16, right: 16, bottom: 16, left: 16 };
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10);
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10);

  const cx = margin.left + plotW / 2;
  const cy = margin.top + plotH / 2;
  const outerRadius = Math.min(plotW, plotH) / 2;
  const innerRadius = outerRadius * innerFraction;

  /* Draw wedges. */
  for (let index = 0; index < slices.length; index = index + 1) {
    const slice = slices[index];
    const color = ctx.colorFor(index);
    const pathData = arcPath(cx, cy, innerRadius, outerRadius, slice.startAngle, slice.endAngle);

    const wedge = svgEl("path", {
      d: pathData,
      fill: color,
      stroke: "var(--mj-surface, #ffffff)",
      "stroke-width": 1.5,
      part: "slice",
      tabindex: "0",
      role: "img",
      "aria-label": `${escapeHtml(slice.label)}: ${formatNumber(slice.value)} (${(slice.fraction * 100).toFixed(1)}%)`
    }, []);

    wedge.appendChild(svgEl("title", null,
      `${slice.label}: ${formatNumber(slice.value)} (${(slice.fraction * 100).toFixed(1)}%)`));

    const handler = () => {
      ctx.emit("mj-chart-slice-click", {
        label: slice.label,
        value: slice.value,
        fraction: slice.fraction
      });
    };
    wedge.addEventListener("click", handler);
    wedge.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        handler();
      }
    });

    root.appendChild(wedge);

    /* Radial label for slices wide enough to label. */
    const midAngle = (slice.startAngle + slice.endAngle) / 2;
    const labelRadius = innerRadius + (outerRadius - innerRadius) * 0.6;
    const lx = cx + labelRadius * Math.sin(midAngle);
    const ly = cy - labelRadius * Math.cos(midAngle);

    if (slice.fraction >= 0.07) {
      root.appendChild(svgEl("text", {
        x: lx.toFixed(2),
        y: ly.toFixed(2),
        "text-anchor": "middle",
        "dominant-baseline": "middle",
        "font-size": 11,
        fill: "var(--mj-surface, #ffffff)",
        "pointer-events": "none"
      }, `${(slice.fraction * 100).toFixed(0)}%`));
    }
  }

  /* Outer leader labels for slices too narrow for internal labels. */
  for (let index = 0; index < slices.length; index = index + 1) {
    const slice = slices[index];
    if (slice.fraction < 0.07) {
      const midAngle = (slice.startAngle + slice.endAngle) / 2;
      const leaderR = outerRadius + 10;
      const labelR = outerRadius + 20;
      const lx1 = cx + outerRadius * Math.sin(midAngle);
      const ly1 = cy - outerRadius * Math.cos(midAngle);
      const lx2 = cx + leaderR * Math.sin(midAngle);
      const ly2 = cy - leaderR * Math.cos(midAngle);
      const lx3 = cx + labelR * Math.sin(midAngle);
      const ly3 = cy - labelR * Math.cos(midAngle);
      const anchor = lx3 >= cx ? "start" : "end";

      root.appendChild(svgEl("line", {
        x1: lx1.toFixed(2), y1: ly1.toFixed(2),
        x2: lx2.toFixed(2), y2: ly2.toFixed(2),
        stroke: "var(--mj-text-muted, #6b7280)", "stroke-width": 1
      }, []));
      root.appendChild(svgEl("text", {
        x: lx3.toFixed(2), y: ly3.toFixed(2),
        "text-anchor": anchor,
        "dominant-baseline": "middle",
        "font-size": 10,
        fill: "var(--mj-text-muted, #6b7280)",
        "pointer-events": "none"
      }, escapeHtml(slice.label)));
    }
  }

  /* Center label (donut mode). */
  const centerLabel = model.meta && model.meta["center-label"];
  if (centerLabel !== null && centerLabel !== undefined && innerRadius > 0) {
    root.appendChild(svgEl("text", {
      x: cx.toFixed(2),
      y: cy.toFixed(2),
      "text-anchor": "middle",
      "dominant-baseline": "middle",
      "font-size": 16,
      "font-weight": "600",
      fill: "var(--mj-text, #14181f)",
      "pointer-events": "none"
    }, escapeHtml(String(centerLabel))));
  }

  return root;
}


registerRenderer("pie", render);
registerRenderer("donut", render);
