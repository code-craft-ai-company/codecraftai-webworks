/*
 * chord.js
 *
 * Chord diagram renderer.
 *
 * Registers: "chord"
 *
 * ctx.raw shape:
 *   nodes: [{ id, label? }]       (optional: nodes named only in `links` are
 *                                  added automatically)
 *   links: [{ source, target, value }]
 *
 * Layout:
 *   - Links are summed into a directed matrix m[i][j] (duplicates add up;
 *     links whose value is not a positive number are ignored).
 *   - One ribbon per node pair. When both directions are given, the ribbon
 *     is m[i][j] wide where it leaves i and m[j][i] wide at j, so direction
 *     stays readable; a one-way flow has the same width at both ends (the
 *     data may list each pair once, the upper triangle). The ribbon takes
 *     the colour of the node that sends more.
 *   - A self-link m[i][i] is drawn as a loop back into the node's own arc.
 *   - Each node's arc is exactly as long as the ribbon ends it holds, so
 *     every part of an arc is connected to a ribbon.
 *   - The ring radius leaves room for the group labels; labels too long for
 *     the space are shortened (the full name is in the tooltip and table).
 *
 * Orientation: n/a -- radial layout only.
 *
 * Accessibility: arcs and ribbons are focusable marks with an aria-label;
 * the accessible table lists every directed flow (source, target, value).
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, arcPath } from "../svgdraw.js";


const MAX_GAP_ANGLE = 0.04;   /* radians of gap between arc segments */
const MAX_ARC_THICKNESS = 18; /* ring thickness in px */
const LABEL_OFFSET = 8;
const LABEL_FONT_SIZE = 11;
const CHAR_WIDTH = 5.9;
const EDGE_PADDING = 6;
const MIN_RADIUS = 30;


function _toKey(value) {
  /*
   * The map key of a node id; null and undefined have no key.
   */
  if (value === null || value === undefined) {
    return null;
  }
  return String(value);
}


function _linkValue(link) {
  /*
   * The drawable value of a link: a finite number above zero, else null.
   */
  const value = link !== null && typeof link === "object" ? link.value : null;
  if (typeof value !== "number" || Number.isFinite(value) === false || value <= 0) {
    return null;
  }
  return value;
}


function _truncate(text, maxWidth) {
  /*
   * Shorten a label to roughly maxWidth pixels with an ellipsis.
   */
  const maxChars = Math.max(Math.floor(maxWidth / CHAR_WIDTH), 1);
  if (text.length <= maxChars) {
    return text;
  }
  if (maxChars <= 1) {
    return "…";
  }
  return text.slice(0, maxChars - 1) + "…";
}


function _buildMatrix(raw) {
  /*
   * Build the node list and the directed value matrix without changing the
   * raw data.
   *
   * :returns: { nodes: [{ id, label }], matrix } where matrix[i][j] is the
   *     summed value of the links from node i to node j.
   */
  const rawNodes = (raw && Array.isArray(raw.nodes)) ? raw.nodes : [];
  const rawLinks = (raw && Array.isArray(raw.links)) ? raw.links : [];

  const nodes = [];
  const indexMap = new Map();
  const addNode = (id, label) => {
    indexMap.set(id, nodes.length);
    nodes.push({ id: id, label: label });
  };

  for (let index = 0; index < rawNodes.length; index = index + 1) {
    const entry = rawNodes[index];
    if (entry === null || typeof entry !== "object") {
      continue;
    }
    const id = _toKey(entry.id);
    if (id === null || indexMap.has(id) === true) {
      continue;
    }
    const label = entry.label !== undefined && entry.label !== null && String(entry.label) !== "" ?
      String(entry.label) : id;
    addNode(id, label);
  }

  const pending = [];
  for (let index = 0; index < rawLinks.length; index = index + 1) {
    const entry = rawLinks[index];
    const value = _linkValue(entry);
    if (value === null) {
      continue;
    }
    const sourceId = _toKey(entry.source);
    const targetId = _toKey(entry.target);
    if (sourceId === null || targetId === null) {
      continue;
    }
    if (indexMap.has(sourceId) === false) {
      addNode(sourceId, sourceId);
    }
    if (indexMap.has(targetId) === false) {
      addNode(targetId, targetId);
    }
    pending.push({ si: indexMap.get(sourceId), ti: indexMap.get(targetId), value: value });
  }

  const matrix = [];
  for (let i = 0; i < nodes.length; i = i + 1) {
    const row = [];
    for (let j = 0; j < nodes.length; j = j + 1) {
      row.push(0);
    }
    matrix.push(row);
  }
  for (let index = 0; index < pending.length; index = index + 1) {
    const entry = pending[index];
    matrix[entry.si][entry.ti] = matrix[entry.si][entry.ti] + entry.value;
  }
  return { nodes: nodes, matrix: matrix };
}


function _buildChords(nodes, matrix) {
  /*
   * One chord per connected pair (and per self-link), with the width each
   * end takes on its node's arc.
   *
   * :returns: { chords, totals } -- chords are { i, j, endI, endJ, forward,
   *     backward }; totals[i] is the sum of the ends on node i.
   */
  const chords = [];
  const totals = nodes.map(() => 0);
  for (let i = 0; i < nodes.length; i = i + 1) {
    for (let j = i; j < nodes.length; j = j + 1) {
      const forward = matrix[i][j];
      const backward = matrix[j][i];
      if (i === j) {
        if (forward > 0) {
          chords.push({ i: i, j: j, endI: forward, endJ: 0, forward: forward, backward: 0 });
          totals[i] = totals[i] + forward;
        }
        continue;
      }
      if (forward <= 0 && backward <= 0) {
        continue;
      }
      let endI = forward;
      let endJ = backward;
      if (forward <= 0) {
        endI = backward;
      } else if (backward <= 0) {
        endJ = forward;
      }
      chords.push({ i: i, j: j, endI: endI, endJ: endJ, forward: forward, backward: backward });
      totals[i] = totals[i] + endI;
      totals[j] = totals[j] + endJ;
    }
  }
  return { chords: chords, totals: totals };
}


function _chordRibbonPath(cx, cy, radius, sa1, ea1, sa2, ea2) {
  /*
   * Build a chord ribbon between two arc spans: along the first span
   * (clockwise), a quadratic curve through the centre to the second span,
   * along it (clockwise), and back through the centre.
   */
  const pointAt = (angle) => {
    return {
      x: cx + radius * Math.sin(angle),
      y: cy - radius * Math.cos(angle)
    };
  };

  const largeArc1 = (ea1 - sa1) > Math.PI ? 1 : 0;
  const largeArc2 = (ea2 - sa2) > Math.PI ? 1 : 0;

  const arcStart1 = pointAt(sa1);
  const arcEnd1 = pointAt(ea1);
  const arcStart2 = pointAt(sa2);
  const arcEnd2 = pointAt(ea2);
  const c = `${cx.toFixed(2)},${cy.toFixed(2)}`;

  const data = `M${arcStart1.x.toFixed(2)},${arcStart1.y.toFixed(2)} ` +
    `A${radius},${radius} 0 ${largeArc1} 1 ${arcEnd1.x.toFixed(2)},${arcEnd1.y.toFixed(2)} ` +
    `Q${c} ${arcStart2.x.toFixed(2)},${arcStart2.y.toFixed(2)} ` +
    `A${radius},${radius} 0 ${largeArc2} 1 ${arcEnd2.x.toFixed(2)},${arcEnd2.y.toFixed(2)} ` +
    `Q${c} ${arcStart1.x.toFixed(2)},${arcStart1.y.toFixed(2)} Z`;
  return data;
}


function _selfRibbonPath(cx, cy, radius, sa, ea) {
  /*
   * Build a self-link loop: along the span and back through a point inside
   * the ring, a petal that stays attached to its own arc.
   */
  const mid = (sa + ea) / 2;
  const depth = radius * 0.45;
  const start = { x: cx + radius * Math.sin(sa), y: cy - radius * Math.cos(sa) };
  const end = { x: cx + radius * Math.sin(ea), y: cy - radius * Math.cos(ea) };
  const control = { x: cx + depth * Math.sin(mid), y: cy - depth * Math.cos(mid) };
  const largeArc = (ea - sa) > Math.PI ? 1 : 0;
  const data = `M${start.x.toFixed(2)},${start.y.toFixed(2)} ` +
    `A${radius},${radius} 0 ${largeArc} 1 ${end.x.toFixed(2)},${end.y.toFixed(2)} ` +
    `Q${control.x.toFixed(2)},${control.y.toFixed(2)} ${start.x.toFixed(2)},${start.y.toFixed(2)} Z`;
  return data;
}


function _buildTable(nodes, matrix) {
  /*
   * The accessible table: one row per directed flow.
   */
  const rows = [];
  for (let i = 0; i < nodes.length; i = i + 1) {
    for (let j = 0; j < nodes.length; j = j + 1) {
      if (matrix[i][j] > 0) {
        rows.push([nodes[i].label, nodes[j].label, matrix[i][j]]);
      }
    }
  }
  return { columns: ["Source", "Target", "Value"], rows: rows, caption: "Flows between groups" };
}


function _isEmpty(model) {
  /*
   * Nothing to draw: no link with a positive value.
   */
  const raw = model !== null && model !== undefined ? model.raw : null;
  const links = (raw && Array.isArray(raw.links)) ? raw.links : [];
  const drawable = links.some((link) => {
    return _linkValue(link) !== null && _toKey(link.source) !== null && _toKey(link.target) !== null;
  });
  return drawable === false;
}


function _activate(element, handler) {
  /*
   * Wire click and Enter / Space to a mark's handler.
   */
  element.addEventListener("click", handler);
  element.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      handler();
    }
  });
}


export function render(ctx) {
  /*
   * Render a chord diagram.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const root = svgEl("g", { part: "plot" }, []);

  const { nodes, matrix } = _buildMatrix(ctx.raw);
  if (nodes.length === 0) {
    return root;
  }
  ctx.setTable(_buildTable(nodes, matrix));

  const { chords, totals } = _buildChords(nodes, matrix);
  const grandTotal = totals.reduce((acc, v) => acc + v, 0);
  if (grandTotal <= 0) {
    return root;
  }

  /* Only nodes with flow take part in the ring. */
  const active = [];
  for (let i = 0; i < nodes.length; i = i + 1) {
    if (totals[i] > 0) {
      active.push(i);
    }
  }

  /* Ring radius: leave room for the widest label left and right. */
  let longest = 0;
  for (let k = 0; k < active.length; k = k + 1) {
    longest = Math.max(longest, nodes[active[k]].label.length);
  }
  const halfW = ctx.width / 2;
  const halfH = ctx.height / 2;
  const verticalRadius = halfH - LABEL_OFFSET - LABEL_FONT_SIZE - EDGE_PADDING;
  let labelWidth = longest * CHAR_WIDTH;
  let outerRadius = Math.min(halfW - LABEL_OFFSET - labelWidth - EDGE_PADDING, verticalRadius);
  const wantedRadius = Math.min(verticalRadius, halfW * 0.42);
  if (outerRadius < wantedRadius) {
    /* Too narrow for the full labels: shorten them, keep a usable ring. */
    outerRadius = Math.max(Math.min(wantedRadius, verticalRadius), MIN_RADIUS);
    labelWidth = Math.max(halfW - LABEL_OFFSET - outerRadius - EDGE_PADDING, CHAR_WIDTH * 3);
  }
  if (outerRadius < 10) {
    return root;
  }
  const thickness = Math.min(MAX_ARC_THICKNESS, Math.max(outerRadius * 0.12, 4));
  const innerRadius = outerRadius - thickness;
  const cx = halfW;
  const cy = halfH;

  /* Angular extent of each node proportional to the ribbon ends it holds. */
  const gap = active.length > 1 ? Math.min(MAX_GAP_ANGLE, (Math.PI * 0.5) / active.length) : 0;
  const flowRange = (2 * Math.PI) - gap * active.length;
  const unit = flowRange / grandTotal;

  const nodeAngles = nodes.map(() => null);
  let cursor = 0;
  for (let k = 0; k < active.length; k = k + 1) {
    const i = active[k];
    const span = totals[i] * unit;
    nodeAngles[i] = { start: cursor, end: cursor + span };
    cursor = cursor + span + gap;
  }

  /* Ask for the node colours in data order so each node keeps its slot. */
  for (let i = 0; i < nodes.length; i = i + 1) {
    ctx.colorFor(nodes[i].id);
  }

  /* Per-node cursor for ribbon anchors within the arc. */
  const chordCursor = nodeAngles.map((angles) => angles !== null ? angles.start : 0);

  const ribbonLayer = svgEl("g", { part: "chords" }, []);
  const arcLayer = svgEl("g", { part: "arcs" }, []);
  const labelLayer = svgEl("g", { "aria-hidden": "true", "pointer-events": "none" }, []);
  root.appendChild(ribbonLayer);
  root.appendChild(arcLayer);
  root.appendChild(labelLayer);

  /* Ribbons (behind the arcs). */
  for (let index = 0; index < chords.length; index = index + 1) {
    const chord = chords[index];
    const nodeI = nodes[chord.i];
    const nodeJ = nodes[chord.j];

    let ribbonD = "";
    let text = "";
    let sender = nodeI;
    if (chord.i === chord.j) {
      const sa = chordCursor[chord.i];
      const ea = sa + chord.endI * unit;
      chordCursor[chord.i] = ea;
      ribbonD = _selfRibbonPath(cx, cy, innerRadius, sa, ea);
      text = `${nodeI.label} → ${nodeI.label}: ${formatNumber(chord.forward)}`;
    } else {
      const sa1 = chordCursor[chord.i];
      const ea1 = sa1 + chord.endI * unit;
      const sa2 = chordCursor[chord.j];
      const ea2 = sa2 + chord.endJ * unit;
      chordCursor[chord.i] = ea1;
      chordCursor[chord.j] = ea2;
      ribbonD = _chordRibbonPath(cx, cy, innerRadius, sa1, ea1, sa2, ea2);

      const parts = [];
      if (chord.forward > 0) {
        parts.push(`${nodeI.label} → ${nodeJ.label}: ${formatNumber(chord.forward)}`);
      }
      if (chord.backward > 0) {
        parts.push(`${nodeJ.label} → ${nodeI.label}: ${formatNumber(chord.backward)}`);
      }
      text = parts.join(", ");
      sender = chord.backward > chord.forward ? nodeJ : nodeI;
    }

    const color = ctx.colorFor(sender.id);
    const ribbon = svgEl("path", {
      d: ribbonD,
      fill: color,
      "fill-opacity": "0.6",
      stroke: color,
      "stroke-opacity": "0.9",
      "stroke-width": "0.5",
      part: "chord",
      tabindex: "0",
      role: "img",
      "aria-label": text
    }, [svgEl("title", null, text)]);

    _activate(ribbon, () => {
      ctx.emit("mj-chart-chord-click", {
        source: nodeI.id,
        target: nodeJ.id,
        value: chord.forward,
        reverseValue: chord.backward
      });
    });
    ribbonLayer.appendChild(ribbon);
  }

  /* Arc segments and labels. */
  for (let k = 0; k < active.length; k = k + 1) {
    const i = active[k];
    const node = nodes[i];
    const angles = nodeAngles[i];
    const color = ctx.colorFor(node.id);

    let sent = 0;
    let received = 0;
    for (let j = 0; j < nodes.length; j = j + 1) {
      sent = sent + matrix[i][j];
      received = received + matrix[j][i];
    }
    const text = `${node.label}: sends ${formatNumber(sent)}, receives ${formatNumber(received)}`;

    const arc = svgEl("path", {
      d: arcPath(cx, cy, innerRadius, outerRadius, angles.start, angles.end),
      fill: color,
      part: "arc",
      tabindex: "0",
      role: "img",
      "aria-label": text
    }, [svgEl("title", null, text)]);

    _activate(arc, () => {
      ctx.emit("mj-chart-node-click", {
        id: node.id,
        label: node.label,
        total: totals[i],
        sent: sent,
        received: received
      });
    });
    arcLayer.appendChild(arc);

    /* Label outside the arc: centred near the top and bottom of the ring. */
    const midAngle = (angles.start + angles.end) / 2;
    const labelRadius = outerRadius + LABEL_OFFSET;
    const sin = Math.sin(midAngle);
    const cos = Math.cos(midAngle);
    const lx = cx + labelRadius * sin;
    const ly = cy - labelRadius * cos;
    let anchor = sin >= 0 ? "start" : "end";
    let baseline = "middle";
    let room = labelWidth;
    if (Math.abs(sin) < 0.35) {
      anchor = "middle";
      baseline = cos > 0 ? "auto" : "hanging";
      room = Math.max(labelWidth, Math.min(ctx.width - 2 * EDGE_PADDING, labelWidth * 2));
    }
    labelLayer.appendChild(svgEl("text", {
      x: lx.toFixed(2),
      y: ly.toFixed(2),
      "text-anchor": anchor,
      "dominant-baseline": baseline,
      "font-size": LABEL_FONT_SIZE,
      fill: "var(--mj-text, #14181f)"
    }, _truncate(node.label, room)));
  }

  return root;
}


registerRenderer("chord", render, { legend: "none", isEmpty: _isEmpty });
