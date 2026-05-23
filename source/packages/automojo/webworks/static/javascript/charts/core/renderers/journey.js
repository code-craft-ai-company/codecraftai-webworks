/*
 * journey.js
 *
 * User journey map renderer  ("user-journey")
 * Session flow / navigation flow renderer  ("session-flow")
 *
 * ── user-journey JSON shape (ctx.raw) ──────────────────────────────────────
 *   steps[]           { label, score, touchpoints[], pain_points[] }
 *   score_range       [min, max]  (default [1, 5])
 *   personas[]        optional array of step arrays for multi-persona layout
 *
 * ── session-flow JSON shape (ctx.raw) ──────────────────────────────────────
 *   nodes[]           { id, label }
 *   links[]           { source, target, value }
 *
 * Registers: "user-journey", "session-flow"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, linePath, escapeHtml, formatNumber } from "../svgdraw.js";
import { linearScale, bandScale } from "../scales.js";


/* ── user-journey ────────────────────────────────────────────────────────── */

function _renderJourney(ctx) {
  /*
   * Render a user journey map.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw
  const steps = (raw !== null && raw !== undefined && Array.isArray(raw.steps))
    ? raw.steps
    : []
  const scoreRange = (raw !== null && raw !== undefined && Array.isArray(raw.score_range))
    ? raw.score_range
    : [1, 5]
  /* Support multi-persona: personas is array of step-arrays. */
  const personas = (raw !== null && raw !== undefined && Array.isArray(raw.personas))
    ? raw.personas
    : (steps.length > 0 ? [steps] : [])

  const root = svgEl("g", { part: "plot" }, [])

  if (personas.length === 0 || personas[0].length === 0) {
    return root
  }

  const horizontal = ctx.orientation !== "vertical"
  const margin = { top: 24, right: 16, bottom: 60, left: 60 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Use the first persona's steps as the canonical step labels. */
  const stepLabels = personas[0].map((s) => s.label || "")
  const scoreMin = scoreRange[0]
  const scoreMax = scoreRange[1]

  const catScale = bandScale(stepLabels, [0, horizontal ? plotW : plotH], 0.15)
  const valScale = horizontal
    ? linearScale([scoreMin, scoreMax], [plotH, 0])
    : linearScale([scoreMin, scoreMax], [0, plotW])

  /* Gridlines. */
  const gridTicks = [scoreMin, (scoreMin + scoreMax) / 2, scoreMax]
  for (let t = 0; t < gridTicks.length; t = t + 1) {
    const tick = gridTicks[t]
    if (horizontal === true) {
      const yg = valScale(tick)
      plot.appendChild(svgEl("line", {
        x1: 0, y1: yg, x2: plotW, y2: yg,
        stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
      }, []))
      plot.appendChild(svgEl("text", {
        x: -8, y: yg + 4,
        "text-anchor": "end", "font-size": 10,
        fill: "var(--mj-text-muted, #6b7280)"
      }, formatNumber(tick, { maximumFractionDigits: 1 })))
    } else {
      const xg = valScale(tick)
      plot.appendChild(svgEl("line", {
        x1: xg, y1: 0, x2: xg, y2: plotH,
        stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
      }, []))
      plot.appendChild(svgEl("text", {
        x: xg, y: plotH + 14,
        "text-anchor": "middle", "font-size": 10,
        fill: "var(--mj-text-muted, #6b7280)"
      }, formatNumber(tick, { maximumFractionDigits: 1 })))
    }
  }

  /* Step lane backgrounds and labels. */
  for (let si = 0; si < stepLabels.length; si = si + 1) {
    const lbl = stepLabels[si]
    const bandStart = catScale(lbl)
    const bw = catScale.bandwidth()

    if (horizontal === true) {
      plot.appendChild(svgEl("rect", {
        x: bandStart, y: 0, width: bw, height: plotH,
        fill: si % 2 === 0
          ? "var(--mj-surface-subtle, #f8f9fb)"
          : "var(--mj-surface, #ffffff)",
        opacity: 0.4
      }, []))
      plot.appendChild(svgEl("text", {
        x: bandStart + bw / 2, y: plotH + 16,
        "text-anchor": "middle", "font-size": 11,
        fill: "var(--mj-text, #14181f)"
      }, escapeHtml(lbl)))
    } else {
      plot.appendChild(svgEl("rect", {
        x: 0, y: bandStart, width: plotW, height: bw,
        fill: si % 2 === 0
          ? "var(--mj-surface-subtle, #f8f9fb)"
          : "var(--mj-surface, #ffffff)",
        opacity: 0.4
      }, []))
      plot.appendChild(svgEl("text", {
        x: -8, y: bandStart + bw / 2 + 4,
        "text-anchor": "end", "font-size": 11,
        fill: "var(--mj-text, #14181f)"
      }, escapeHtml(lbl)))
    }
  }

  /* Draw each persona's emotion line and step nodes. */
  for (let pi = 0; pi < personas.length; pi = pi + 1) {
    const persona = personas[pi]
    const lineColor = ctx.colorFor(pi)

    const points = []
    for (let si = 0; si < persona.length; si = si + 1) {
      const step = persona[si]
      const lbl = step.label || ""
      const score = typeof step.score === "number" ? step.score : scoreMin
      const catCenter = catScale.center(lbl)
      const valPos = valScale(score)
      const px = horizontal ? catCenter : valPos
      const py = horizontal ? valPos : catCenter
      points.push({ x: px, y: py })
    }

    /* Emotion line. */
    const lineDPath = linePath(points)
    if (lineDPath !== "") {
      plot.appendChild(svgEl("path", {
        d: lineDPath,
        fill: "none",
        stroke: lineColor,
        "stroke-width": 2.5,
        "stroke-linejoin": "round",
        "stroke-linecap": "round"
      }, []))
    }

    /* Step nodes. */
    for (let si = 0; si < persona.length; si = si + 1) {
      const step = persona[si]
      const lbl = step.label || ""
      const score = typeof step.score === "number" ? step.score : scoreMin
      const touchpoints = Array.isArray(step.touchpoints) ? step.touchpoints : []
      const painPoints = Array.isArray(step.pain_points) ? step.pain_points : []
      const nodeR = 4 + Math.min(touchpoints.length * 2, 8)

      const catCenter = catScale.center(lbl)
      const valPos = valScale(score)
      const nx = horizontal ? catCenter : valPos
      const ny = horizontal ? valPos : catCenter

      const ariaLabel = `${lbl}: score ${score}` +
        (touchpoints.length > 0 ? `, touchpoints: ${touchpoints.join(", ")}` : "") +
        (painPoints.length > 0 ? `, pain points: ${painPoints.join(", ")}` : "")

      const node = svgEl("g", {
        tabindex: "0",
        role: "img",
        "aria-label": ariaLabel,
        part: "journey-step"
      }, [])

      node.appendChild(svgEl("circle", {
        cx: nx, cy: ny, r: nodeR,
        fill: lineColor,
        stroke: "var(--mj-surface, #ffffff)",
        "stroke-width": 2
      }, []))

      /* Pain-point marker. */
      if (painPoints.length > 0) {
        node.appendChild(svgEl("circle", {
          cx: nx + nodeR * 0.7,
          cy: ny - nodeR * 0.7,
          r: 4,
          fill: "var(--mj-color-danger, #b91c1c)"
        }, []))
      }

      node.appendChild(svgEl("title", null, ariaLabel))

      const capturedStep = step
      const handler = () => {
        ctx.emit("mj-chart-journey-click", {
          label: capturedStep.label,
          score: capturedStep.score,
          touchpoints: capturedStep.touchpoints,
          pain_points: capturedStep.pain_points
        })
      }
      node.addEventListener("click", handler)
      node.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })

      plot.appendChild(node)
    }
  }

  return root
}


/* ── session-flow ─────────────────────────────────────────────────────────── */

function _computeLevels(nodes, links) {
  /*
   * Assign a depth level (column) to each node based on link topology.
   * Nodes with no incoming links are level 0.
   *
   * :returns: Map of node id -> level number.
   */
  const inDegree = {}
  const nodeIds = nodes.map((n) => n.id)
  for (let i = 0; i < nodeIds.length; i = i + 1) {
    inDegree[nodeIds[i]] = 0
  }
  for (let l = 0; l < links.length; l = l + 1) {
    const tgt = links[l].target
    if (inDegree[tgt] !== undefined) {
      inDegree[tgt] = inDegree[tgt] + 1
    }
  }

  /* BFS level assignment. */
  const level = {}
  const queue = []
  for (let i = 0; i < nodeIds.length; i = i + 1) {
    if (inDegree[nodeIds[i]] === 0) {
      level[nodeIds[i]] = 0
      queue.push(nodeIds[i])
    }
  }

  let qi = 0
  while (qi < queue.length) {
    const current = queue[qi]
    qi = qi + 1
    for (let l = 0; l < links.length; l = l + 1) {
      const link = links[l]
      if (link.source === current) {
        const newLevel = level[current] + 1
        if (level[link.target] === undefined || level[link.target] < newLevel) {
          level[link.target] = newLevel
          queue.push(link.target)
        }
      }
    }
  }

  /* Assign level 0 to any unreachable nodes. */
  for (let i = 0; i < nodeIds.length; i = i + 1) {
    if (level[nodeIds[i]] === undefined) {
      level[nodeIds[i]] = 0
    }
  }

  return level
}


function _renderSessionFlow(ctx) {
  /*
   * Render a session-flow (Sankey-like) chart.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw
  const nodes = (raw !== null && raw !== undefined && Array.isArray(raw.nodes))
    ? raw.nodes
    : []
  const links = (raw !== null && raw !== undefined && Array.isArray(raw.links))
    ? raw.links
    : []

  const root = svgEl("g", { part: "plot" }, [])

  if (nodes.length === 0) {
    return root
  }

  const horizontal = ctx.orientation !== "vertical"
  const margin = { top: 16, right: 80, bottom: 16, left: 16 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Assign levels. */
  const levels = _computeLevels(nodes, links)

  /* Group nodes by level. */
  let maxLevel = 0
  for (const id in levels) {
    if (levels[id] > maxLevel) {
      maxLevel = levels[id]
    }
  }

  const byLevel = {}
  for (let lvl = 0; lvl <= maxLevel; lvl = lvl + 1) {
    byLevel[lvl] = []
  }
  for (let i = 0; i < nodes.length; i = i + 1) {
    const nodeId = nodes[i].id
    const lvl = levels[nodeId]
    byLevel[lvl].push(nodes[i])
  }

  /* Compute total flow per node. */
  const nodeFlow = {}
  for (let i = 0; i < nodes.length; i = i + 1) {
    nodeFlow[nodes[i].id] = 0
  }
  for (let l = 0; l < links.length; l = l + 1) {
    const link = links[l]
    const val = typeof link.value === "number" ? link.value : 0
    if (nodeFlow[link.source] !== undefined) {
      nodeFlow[link.source] = nodeFlow[link.source] + val
    }
    if (nodeFlow[link.target] !== undefined) {
      nodeFlow[link.target] = nodeFlow[link.target] + val
    }
  }

  /* Compute layout positions. */
  const nodeRect = {}
  const numLevels = maxLevel + 1
  const nodeW = horizontal ? 24 : plotW / numLevels - 8
  const nodeH = horizontal ? plotH / numLevels - 8 : 24

  /* Max flow for sizing. */
  let maxFlow = 1
  for (const id in nodeFlow) {
    if (nodeFlow[id] > maxFlow) {
      maxFlow = nodeFlow[id]
    }
  }

  const levelXScale = linearScale([0, maxLevel], [0, horizontal ? plotW - nodeW : plotH - nodeH])

  for (let lvl = 0; lvl <= maxLevel; lvl = lvl + 1) {
    const lvlNodes = byLevel[lvl]
    const count = lvlNodes.length
    const mainPos = levelXScale(lvl)

    for (let ni = 0; ni < count; ni = ni + 1) {
      const flow = nodeFlow[lvlNodes[ni].id] || 1
      const barH = Math.max((flow / maxFlow) * (horizontal ? plotH * 0.4 : plotW * 0.4), 8)
      const crossStart = (horizontal ? plotH : plotW) * (ni + 1) / (count + 1) - barH / 2

      if (horizontal === true) {
        nodeRect[lvlNodes[ni].id] = {
          x: mainPos, y: crossStart,
          w: nodeW, h: barH
        }
      } else {
        nodeRect[lvlNodes[ni].id] = {
          x: crossStart, y: mainPos,
          w: barH, h: nodeH
        }
      }
    }
  }

  /* Draw links as bezier bands. */
  for (let l = 0; l < links.length; l = l + 1) {
    const link = links[l]
    const srcRect = nodeRect[link.source]
    const tgtRect = nodeRect[link.target]
    if (srcRect === undefined || tgtRect === undefined) {
      continue
    }

    const val = typeof link.value === "number" ? link.value : 0
    const thickness = Math.max((val / maxFlow) * 20, 1)

    let x1, y1, x2, y2, cpx1, cpy1, cpx2, cpy2
    if (horizontal === true) {
      x1 = srcRect.x + srcRect.w
      y1 = srcRect.y + srcRect.h / 2
      x2 = tgtRect.x
      y2 = tgtRect.y + tgtRect.h / 2
      const midX = (x1 + x2) / 2
      cpx1 = midX
      cpy1 = y1
      cpx2 = midX
      cpy2 = y2
    } else {
      x1 = srcRect.x + srcRect.w / 2
      y1 = srcRect.y + srcRect.h
      x2 = tgtRect.x + tgtRect.w / 2
      y2 = tgtRect.y
      const midY = (y1 + y2) / 2
      cpx1 = x1
      cpy1 = midY
      cpx2 = x2
      cpy2 = midY
    }

    const d = `M${x1.toFixed(2)},${y1.toFixed(2)} ` +
      `C${cpx1.toFixed(2)},${cpy1.toFixed(2)} ` +
      `${cpx2.toFixed(2)},${cpy2.toFixed(2)} ` +
      `${x2.toFixed(2)},${y2.toFixed(2)}`

    const linkEl = svgEl("path", {
      d: d,
      fill: "none",
      stroke: ctx.colorFor(0),
      "stroke-width": thickness,
      opacity: 0.4,
      part: "flow-link"
    }, [])
    linkEl.appendChild(svgEl("title", null,
      `${link.source} → ${link.target}: ${formatNumber(val)}`))
    plot.appendChild(linkEl)
  }

  /* Draw nodes. */
  for (let i = 0; i < nodes.length; i = i + 1) {
    const node = nodes[i]
    const rect = nodeRect[node.id]
    if (rect === undefined) {
      continue
    }

    const nodeColor = ctx.colorFor(levels[node.id] || 0)
    const ariaLabel = `${node.label || node.id}: flow ${formatNumber(nodeFlow[node.id] || 0)}`

    const nodeEl = svgEl("g", {
      tabindex: "0",
      role: "img",
      "aria-label": ariaLabel,
      part: "flow-node"
    }, [])

    nodeEl.appendChild(svgEl("rect", {
      x: rect.x, y: rect.y,
      width: rect.w, height: rect.h,
      rx: 3,
      fill: nodeColor
    }, []))

    nodeEl.appendChild(svgEl("text", {
      x: rect.x + rect.w + 4,
      y: rect.y + rect.h / 2 + 4,
      "font-size": 11,
      fill: "var(--mj-text, #14181f)"
    }, escapeHtml(node.label || node.id)))

    nodeEl.appendChild(svgEl("title", null, ariaLabel))

    const capturedNode = node
    const handler = () => {
      ctx.emit("mj-chart-flow-click", {
        id: capturedNode.id,
        label: capturedNode.label,
        flow: nodeFlow[capturedNode.id]
      })
    }
    nodeEl.addEventListener("click", handler)
    nodeEl.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        handler()
      }
    })

    plot.appendChild(nodeEl)
  }

  return root
}


/* ── entry points ─────────────────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Dispatch to the correct sub-renderer based on type.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw
  const isFlow = raw !== null && raw !== undefined &&
    Array.isArray(raw.nodes) && Array.isArray(raw.links)

  if (isFlow === true) {
    const result = _renderSessionFlow(ctx)
    return result
  }

  const result = _renderJourney(ctx)
  return result
}


registerRenderer("user-journey", render)
registerRenderer("session-flow", render)
