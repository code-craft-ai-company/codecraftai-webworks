/*
 * chord.js
 *
 * Chord diagram renderer.
 *
 * Registers: "chord"
 *
 * ctx.raw shape:
 *   nodes: [{ id, label? }]
 *   links: [{ source, target, value }]
 *
 * Layout:
 *   - Each node occupies an arc segment on a ring proportional to its total
 *     flow (summed link values touching that node).
 *   - Chord ribbons connect pairs of nodes via cubic-Bézier paths anchored
 *     on the ring.
 *   - The renderer symmetrises links automatically (upper triangle only is
 *     enough; both directions may also be supplied).
 *
 * Orientation: n/a — radial layout only.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber, arcPath } from "../svgdraw.js";
import { linearScale } from "../scales.js";


const GAP_ANGLE = 0.03;   /* radians of gap between arc segments */
const ARC_THICKNESS = 18; /* ring thickness in px */


function _buildMatrix(nodes, links) {
  /*
   * Build a symmetric value matrix from the links list.
   * Returns { matrix, totals } where matrix[i][j] = value for node i→j.
   */
  const n = nodes.length;
  const matrix = [];
  const totals = [];
  for (let i = 0; i < n; i = i + 1) {
    matrix.push([]);
    totals.push(0);
    for (let j = 0; j < n; j = j + 1) {
      matrix[i].push(0);
    }
  }

  const indexMap = {};
  for (let i = 0; i < nodes.length; i = i + 1) {
    indexMap[nodes[i].id] = i;
  }

  for (let k = 0; k < links.length; k = k + 1) {
    const link = links[k];
    const value = typeof link.value === "number" ? link.value : 1;
    const si = indexMap[link.source];
    const ti = indexMap[link.target];
    if (si === undefined || ti === undefined) {
      continue;
    }
    matrix[si][ti] = matrix[si][ti] + value;
    matrix[ti][si] = matrix[ti][si] + value;
    totals[si] = totals[si] + value;
    totals[ti] = totals[ti] + value;
  }
  return { matrix: matrix, totals: totals, indexMap: indexMap };
}


function _chordRibbonPath(cx, cy, radius, sa1, ea1, sa2, ea2) {
  /*
   * Build a chord ribbon path between two arc segments.
   * The ribbon uses two cubic-Bézier curves (one per arc end) meeting at the
   * centre point to create a smooth enclosed band.
   */
  const DEG = Math.PI / 180;
  const pointAt = (r, angle) => {
    return {
      x: cx + r * Math.sin(angle),
      y: cy - r * Math.cos(angle)
    };
  };

  const mid1 = (sa1 + ea1) / 2;
  const mid2 = (sa2 + ea2) / 2;

  const p1 = pointAt(radius, mid1);
  const p2 = pointAt(radius, mid2);
  const inner1 = pointAt(radius * 0.05, mid1);
  const inner2 = pointAt(radius * 0.05, mid2);

  const largeArc1 = (ea1 - sa1) > Math.PI ? 1 : 0;
  const largeArc2 = (ea2 - sa2) > Math.PI ? 1 : 0;

  const arcStart1 = pointAt(radius, sa1);
  const arcEnd1 = pointAt(radius, ea1);
  const arcStart2 = pointAt(radius, sa2);
  const arcEnd2 = pointAt(radius, ea2);

  const data = `M${arcStart1.x.toFixed(2)},${arcStart1.y.toFixed(2)} ` +
    `A${radius},${radius} 0 ${largeArc1} 1 ${arcEnd1.x.toFixed(2)},${arcEnd1.y.toFixed(2)} ` +
    `Q${inner2.x.toFixed(2)},${inner2.y.toFixed(2)} ` +
    `${arcStart2.x.toFixed(2)},${arcStart2.y.toFixed(2)} ` +
    `A${radius},${radius} 0 ${largeArc2} 0 ${arcEnd2.x.toFixed(2)},${arcEnd2.y.toFixed(2)} ` +
    `Q${inner1.x.toFixed(2)},${inner1.y.toFixed(2)} ` +
    `${arcStart1.x.toFixed(2)},${arcStart1.y.toFixed(2)} Z`;
  return data;
}


export function render(ctx) {
  /*
   * Render a chord diagram.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw;
  const root = svgEl("g", { part: "plot" }, []);

  const nodes = (raw && Array.isArray(raw.nodes)) ? raw.nodes : [];
  const links = (raw && Array.isArray(raw.links)) ? raw.links : [];

  if (nodes.length === 0) {
    return root;
  }

  const size = Math.min(ctx.width, ctx.height);
  const cx = ctx.width / 2;
  const cy = ctx.height / 2;
  const outerRadius = size / 2 - 40;
  const innerRadius = outerRadius - ARC_THICKNESS;

  if (outerRadius < 10) {
    return root;
  }

  const { matrix, totals, indexMap } = _buildMatrix(nodes, links);

  const grandTotal = totals.reduce((acc, v) => acc + v, 0);
  if (grandTotal === 0) {
    return root;
  }

  /* Assign angular extent to each node proportional to its total flow. */
  const totalGap = GAP_ANGLE * nodes.length;
  const flowRange = (2 * Math.PI) - totalGap;
  const angleScale = linearScale([0, grandTotal], [0, flowRange]);

  const nodeAngles = [];
  let cursor = 0;
  for (let i = 0; i < nodes.length; i = i + 1) {
    const span = angleScale(totals[i]);
    nodeAngles.push({ start: cursor, end: cursor + span });
    cursor = cursor + span + GAP_ANGLE;
  }

  /* Per-node cursor for chord anchor offsets within the arc. */
  const chordCursor = [];
  for (let i = 0; i < nodes.length; i = i + 1) {
    chordCursor.push(nodeAngles[i].start);
  }

  /* Draw chord ribbons (behind arcs). */
  for (let i = 0; i < nodes.length; i = i + 1) {
    for (let j = i + 1; j < nodes.length; j = j + 1) {
      const value = matrix[i][j];
      if (value <= 0) {
        continue;
      }

      const iTotal = totals[i] > 0 ? totals[i] : 1;
      const jTotal = totals[j] > 0 ? totals[j] : 1;
      const iSpan = (nodeAngles[i].end - nodeAngles[i].start) * (value / iTotal);
      const jSpan = (nodeAngles[j].end - nodeAngles[j].start) * (value / jTotal);

      const sa1 = chordCursor[i];
      const ea1 = sa1 + iSpan;
      const sa2 = chordCursor[j];
      const ea2 = sa2 + jSpan;

      chordCursor[i] = ea1;
      chordCursor[j] = ea2;

      const color = ctx.colorFor(i);
      const ribbonD = _chordRibbonPath(cx, cy, innerRadius, sa1, ea1, sa2, ea2);
      const nodeI = nodes[i];
      const nodeJ = nodes[j];
      const capturedValue = value;
      const ribbon = svgEl("path", {
        d: ribbonD,
        fill: color,
        "fill-opacity": "0.55",
        stroke: color,
        "stroke-width": "0.5",
        part: "chord",
        tabindex: "0",
        role: "img",
        "aria-label": `${escapeHtml(nodeI.label || nodeI.id)} ↔ ${escapeHtml(nodeJ.label || nodeJ.id)}: ${formatNumber(capturedValue)}`
      }, []);
      ribbon.appendChild(svgEl("title", null,
        `${nodeI.label || nodeI.id} ↔ ${nodeJ.label || nodeJ.id}: ${formatNumber(capturedValue)}`));

      const clickHandler = () => {
        ctx.emit("mj-chart-chord-click", {
          source: nodeI.id,
          target: nodeJ.id,
          value: capturedValue
        });
      };
      ribbon.addEventListener("click", clickHandler);
      ribbon.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          clickHandler();
        }
      });
      root.appendChild(ribbon);
    }
  }

  /* Draw arc segments. */
  for (let i = 0; i < nodes.length; i = i + 1) {
    const node = nodes[i];
    const angles = nodeAngles[i];
    const color = ctx.colorFor(i);

    const arcD = arcPath(cx, cy, innerRadius, outerRadius, angles.start, angles.end);
    const arc = svgEl("path", {
      d: arcD,
      fill: color,
      part: "arc",
      tabindex: "0",
      role: "img",
      "aria-label": `${escapeHtml(node.label || node.id)}: ${formatNumber(totals[i])}`
    }, []);
    arc.appendChild(svgEl("title", null,
      `${node.label || node.id}: ${formatNumber(totals[i])}`));

    const capturedNode = node;
    const capturedTotal = totals[i];
    const arcClickHandler = () => {
      ctx.emit("mj-chart-node-click", {
        id: capturedNode.id,
        label: capturedNode.label || capturedNode.id,
        total: capturedTotal
      });
    };
    arc.addEventListener("click", arcClickHandler);
    arc.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        arcClickHandler();
      }
    });
    root.appendChild(arc);

    /* Label outside the arc. */
    const midAngle = (angles.start + angles.end) / 2;
    const labelRadius = outerRadius + 14;
    const lx = cx + labelRadius * Math.sin(midAngle);
    const ly = cy - labelRadius * Math.cos(midAngle);
    const anchor = Math.sin(midAngle) >= 0 ? "start" : "end";
    root.appendChild(svgEl("text", {
      x: lx.toFixed(2),
      y: ly.toFixed(2),
      "text-anchor": anchor,
      "dominant-baseline": "middle",
      "font-size": 11,
      fill: "var(--mj-text, #14181f)"
    }, escapeHtml(node.label || node.id)));
  }

  return root;
}


registerRenderer("chord", render);
