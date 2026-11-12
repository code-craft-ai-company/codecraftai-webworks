/*
 * journey.js
 *
 * User journey map renderer  ("user-journey")
 * Session flow / navigation flow renderer  ("session-flow")
 *
 * ── user-journey JSON shape (ctx.raw) ──────────────────────────────────────
 *   steps[]           { label, score, touchpoints[], pain_points[] }
 *   score_range       [min, max]  (default [1, 5]; widened to the data when
 *                     invalid)
 *   personas[]        optional multi-persona layout: an array of step arrays,
 *                     or of { name, steps[] } objects
 *
 * Steps are placed by position (step i of every persona shares column i), so
 * repeated labels ("Email" twice) keep their own columns. A step without a
 * numeric score is a gap in the line; scores are clamped into score_range.
 * Each persona has its own colour and, with two or more personas, a legend
 * entry. Node size encodes the number of touchpoints; a red dot marks steps
 * with pain points.
 *
 * ── session-flow JSON shape (ctx.raw) ──────────────────────────────────────
 *   nodes[]           { id, label }
 *   links[]           { source, target, value }
 *
 * A Sankey-style layout: nodes are placed in columns by their longest path
 * from an entry page, a node's size is max(inflow, outflow), and links are
 * bands whose widths stack along the node edges and add up to the node size.
 * Cycles (back-navigation such as product -> catalog, or a self-link) are
 * detected with a depth-first search; those links do not take part in the
 * column layout and are drawn as return arcs below the flow.
 *
 * Orientation (both types): "horizontal" (default; steps / levels run left
 * to right) or "vertical" (top to bottom).
 *
 * Interaction: steps emit `mj-chart-journey-click` { label, score,
 * touchpoints, pain_points, persona, index }; flow nodes emit
 * `mj-chart-flow-click` { id, label, flow, inflow, outflow }.
 *
 * Registers: "user-journey", "session-flow"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, linePath, formatNumber } from "../svgdraw.js";
import { linearScale } from "../scales.js";

const CHAR_WIDTH = 0.58


function _fitText(text, maxWidth, fontSize) {
  /*
   * Shorten a label with an ellipsis so it fits about maxWidth pixels.
   */
  const value = String(text)
  const capacity = Math.floor(maxWidth / (fontSize * CHAR_WIDTH))
  if (value.length <= capacity) {
    return value
  }
  if (capacity <= 1) {
    return "…"
  }
  return value.slice(0, capacity - 1) + "…"
}


function _textWidth(text, fontSize) {
  /*
   * Estimated rendered width of a label.
   */
  const width = String(text).length * fontSize * CHAR_WIDTH
  return width
}


function _onActivate(element, handler) {
  /*
   * Run a handler on click and on Enter / Space.
   */
  element.addEventListener("click", handler)
  element.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      handler()
    }
  })
  return
}


/* ── user-journey ────────────────────────────────────────────────────────── */

function _readPersonas(raw) {
  /*
   * The personas of a journey: [{ name, steps }], each step an object.
   */
  const personas = []
  if (Array.isArray(raw.personas) === true) {
    for (let index = 0; index < raw.personas.length; index = index + 1) {
      const entry = raw.personas[index]
      let steps = null
      let name = `Persona ${index + 1}`
      if (Array.isArray(entry) === true) {
        steps = entry
      } else if (entry !== null && typeof entry === "object" && Array.isArray(entry.steps) === true) {
        steps = entry.steps
        if (entry.name !== undefined && entry.name !== null) {
          name = String(entry.name)
        }
      }
      if (steps !== null) {
        personas.push({
          name: name,
          steps: steps.map((step) => (step !== null && typeof step === "object" ? step : {}))
        })
      }
    }
  } else if (Array.isArray(raw.steps) === true) {
    personas.push({
      name: "Journey",
      steps: raw.steps.map((step) => (step !== null && typeof step === "object" ? step : {}))
    })
  }
  return personas
}


function _scoreOf(step) {
  /*
   * A step's score, or null when it has none.
   */
  const score = typeof step.score === "number" && Number.isFinite(step.score) === true
    ? step.score
    : null
  return score
}


function _renderJourney(ctx) {
  /*
   * Render a user journey map.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const personas = _readPersonas(raw)
  const root = svgEl("g", { part: "plot" }, [])

  let stepCount = 0
  for (let pi = 0; pi < personas.length; pi = pi + 1) {
    stepCount = Math.max(stepCount, personas[pi].steps.length)
  }
  if (stepCount === 0) {
    return root
  }

  /* Column labels: the first persona that has a label at that position. */
  const stepLabels = []
  for (let si = 0; si < stepCount; si = si + 1) {
    let label = ""
    for (let pi = 0; pi < personas.length; pi = pi + 1) {
      const step = personas[pi].steps[si]
      if (step !== undefined && step.label !== undefined && step.label !== null &&
          String(step.label).length > 0) {
        label = String(step.label)
        break
      }
    }
    stepLabels.push(label.length > 0 ? label : `Step ${si + 1}`)
  }

  /* Score range: the given one when valid, else the data's extent. */
  let scoreMin = null
  let scoreMax = null
  if (Array.isArray(raw.score_range) === true && raw.score_range.length === 2 &&
      Number.isFinite(raw.score_range[0]) === true && Number.isFinite(raw.score_range[1]) === true &&
      raw.score_range[0] < raw.score_range[1]) {
    scoreMin = raw.score_range[0]
    scoreMax = raw.score_range[1]
  } else {
    const scores = []
    personas.forEach((persona) => {
      persona.steps.forEach((step) => {
        const score = _scoreOf(step)
        if (score !== null) {
          scores.push(score)
        }
      })
    })
    scoreMin = scores.length > 0 ? Math.min(...scores) : 1
    scoreMax = scores.length > 0 ? Math.max(...scores) : 5
    if (scoreMin === scoreMax) {
      scoreMin = scoreMin - 1
      scoreMax = scoreMax + 1
    }
  }
  const clampScore = (score) => Math.max(scoreMin, Math.min(scoreMax, score))

  const horizontal = ctx.orientation !== "vertical"
  let longest = 0
  for (let si = 0; si < stepLabels.length; si = si + 1) {
    longest = Math.max(longest, _textWidth(stepLabels[si], 11))
  }
  const margin = horizontal === true
    ? { top: 16, right: 16, bottom: 30, left: 36 }
    : { top: 16, right: 16, bottom: 28, left: Math.min(Math.max(longest + 14, 40), ctx.width * 0.4) }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const plot = svgEl("g", { transform: `translate(${margin.left},${margin.top})` }, [])
  root.appendChild(plot)

  /* Columns by position. */
  const stepSpan = horizontal === true ? plotW : plotH
  const band = stepSpan / stepCount
  const centerOf = (index) => (index + 0.5) * band
  const valScale = horizontal === true
    ? linearScale([scoreMin, scoreMax], [plotH, 0])
    : linearScale([scoreMin, scoreMax], [0, plotW])

  /* Decoration: lanes, gridlines, tick and step labels. */
  const decor = svgEl("g", { "aria-hidden": "true" }, [])
  plot.appendChild(decor)

  for (let si = 0; si < stepCount; si = si + 1) {
    const start = si * band
    if (si % 2 === 0) {
      decor.appendChild(svgEl("rect", horizontal === true
        ? { x: start, y: 0, width: band, height: plotH }
        : { x: 0, y: start, width: plotW, height: band }, []))
      decor.lastChild.setAttribute("fill", "var(--mj-bg-muted, #eef0f3)")
      decor.lastChild.setAttribute("fill-opacity", "0.5")
    }
    const label = stepLabels[si]
    const text = horizontal === true
      ? svgEl("text", {
        x: start + band / 2, y: plotH + 16, "text-anchor": "middle", "font-size": 11,
        fill: "var(--mj-text, #14181f)"
      }, _fitText(label, band - 4, 11))
      : svgEl("text", {
        x: -8, y: start + band / 2 + 4, "text-anchor": "end", "font-size": 11,
        fill: "var(--mj-text, #14181f)"
      }, _fitText(label, margin.left - 12, 11))
    text.appendChild(svgEl("title", null, label))
    decor.appendChild(text)
  }

  const gridTicks = valScale.ticks(5)
  for (let t = 0; t < gridTicks.length; t = t + 1) {
    const tick = gridTicks[t]
    const at = valScale(tick)
    if (horizontal === true) {
      decor.appendChild(svgEl("line", {
        x1: 0, y1: at, x2: plotW, y2: at,
        stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
      }, []))
      decor.appendChild(svgEl("text", {
        x: -8, y: at + 4, "text-anchor": "end", "font-size": 10,
        fill: "var(--mj-text-muted, #5f6673)"
      }, formatNumber(tick, { maximumFractionDigits: 1 })))
    } else {
      decor.appendChild(svgEl("line", {
        x1: at, y1: 0, x2: at, y2: plotH,
        stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
      }, []))
      decor.appendChild(svgEl("text", {
        x: at, y: plotH + 14, "text-anchor": "middle", "font-size": 10,
        fill: "var(--mj-text-muted, #5f6673)"
      }, formatNumber(tick, { maximumFractionDigits: 1 })))
    }
  }

  /* Each persona's emotion line and step nodes. */
  for (let pi = 0; pi < personas.length; pi = pi + 1) {
    const persona = personas[pi]
    const lineColor = ctx.colorFor(pi)

    const points = persona.steps.map((step, si) => {
      const score = _scoreOf(step)
      if (score === null) {
        return null
      }
      const along = centerOf(si)
      const across = valScale(clampScore(score))
      return horizontal === true ? { x: along, y: across } : { x: across, y: along }
    })

    const d = linePath(points)
    if (d !== "") {
      plot.appendChild(svgEl("path", {
        d: d, fill: "none", stroke: lineColor, "stroke-width": 2.5,
        "stroke-linejoin": "round", "stroke-linecap": "round",
        part: "journey-line", "aria-hidden": "true"
      }, []))
    }

    for (let si = 0; si < persona.steps.length; si = si + 1) {
      const point = points[si]
      if (point === null) {
        continue
      }
      const step = persona.steps[si]
      const score = _scoreOf(step)
      const touchpoints = Array.isArray(step.touchpoints) === true ? step.touchpoints : []
      const painPoints = Array.isArray(step.pain_points) === true ? step.pain_points : []
      const nodeR = 4 + Math.min(touchpoints.length * 2, 8)
      const label = stepLabels[si]

      const personaPart = personas.length > 1 ? `${persona.name}, ` : ""
      const ariaLabel = `${personaPart}${label}: score ${formatNumber(score)}` +
        (touchpoints.length > 0 ? `, touchpoints: ${touchpoints.join(", ")}` : "") +
        (painPoints.length > 0 ? `, pain points: ${painPoints.join(", ")}` : "")

      const node = svgEl("g", {
        tabindex: "0", role: "img", "aria-label": ariaLabel, part: "journey-step"
      }, [])
      node.appendChild(svgEl("circle", {
        cx: point.x, cy: point.y, r: nodeR, fill: lineColor,
        stroke: "var(--mj-surface, #ffffff)", "stroke-width": 2
      }, []))
      if (painPoints.length > 0) {
        node.appendChild(svgEl("circle", {
          cx: point.x + nodeR * 0.7, cy: point.y - nodeR * 0.7, r: 4,
          fill: "var(--mj-color-danger, #b91c1c)",
          stroke: "var(--mj-surface, #ffffff)", "stroke-width": 1,
          part: "pain-point"
        }, []))
      }
      node.appendChild(svgEl("title", null, ariaLabel))

      const capturedStep = step
      const personaName = persona.name
      const stepIndex = si
      _onActivate(node, () => {
        ctx.emit("mj-chart-journey-click", {
          label: capturedStep.label,
          score: capturedStep.score,
          touchpoints: capturedStep.touchpoints,
          pain_points: capturedStep.pain_points,
          persona: personaName,
          index: stepIndex
        })
      })
      plot.appendChild(node)
    }
  }

  /* Legend and table. */
  if (personas.length > 1) {
    ctx.setLegend(personas.map((persona, pi) => ({ label: persona.name, color: ctx.colorFor(pi) })))
  }
  const columns = ["Step"]
  personas.forEach((persona) => {
    columns.push(personas.length > 1 ? `${persona.name} score` : "Score")
  })
  columns.push("Touchpoints")
  columns.push("Pain points")
  const rows = stepLabels.map((label, si) => {
    const row = [label]
    const touch = []
    const pain = []
    personas.forEach((persona) => {
      const step = persona.steps[si]
      row.push(step !== undefined ? _scoreOf(step) : null)
      if (step !== undefined && Array.isArray(step.touchpoints) === true) {
        touch.push(...step.touchpoints)
      }
      if (step !== undefined && Array.isArray(step.pain_points) === true) {
        pain.push(...step.pain_points)
      }
    })
    row.push(Array.from(new Set(touch)).join(", "))
    row.push(Array.from(new Set(pain)).join(", "))
    return row
  })
  ctx.setTable({ columns: columns, rows: rows, caption: ctx.label })

  return root
}


/* ── session-flow ─────────────────────────────────────────────────────────── */

function _readFlow(raw) {
  /*
   * Normalise nodes and links: nodes with an id (first wins), links between
   * known nodes with a positive value.
   *
   * :returns: { nodes: [{id, label, source}], links: [{source, target,
   *     value, index}] } -- link ends are node indexes.
   */
  const nodes = []
  const indexOf = new Map()
  const rawNodes = Array.isArray(raw.nodes) === true ? raw.nodes : []
  for (let index = 0; index < rawNodes.length; index = index + 1) {
    const node = rawNodes[index]
    if (node === null || typeof node !== "object" || node.id === undefined || node.id === null) {
      continue
    }
    const id = String(node.id)
    if (indexOf.has(id) === true) {
      continue
    }
    indexOf.set(id, nodes.length)
    const label = node.label !== undefined && node.label !== null ? String(node.label) : id
    nodes.push({ id: id, label: label, source: node })
  }

  const links = []
  const rawLinks = Array.isArray(raw.links) === true ? raw.links : []
  for (let index = 0; index < rawLinks.length; index = index + 1) {
    const link = rawLinks[index]
    if (link === null || typeof link !== "object") {
      continue
    }
    const source = indexOf.get(String(link.source))
    const target = indexOf.get(String(link.target))
    const value = typeof link.value === "number" ? link.value : Number(link.value)
    if (source === undefined || target === undefined || Number.isFinite(value) === false ||
        value <= 0) {
      continue
    }
    links.push({ source: source, target: target, value: value, index: index })
  }

  const flow = { nodes: nodes, links: links }
  return flow
}


function _findBackLinks(nodeCount, links) {
  /*
   * Mark the links that close a cycle. An iterative depth-first search from
   * the entry nodes (no incoming links), then from any node not yet
   * visited, flags a link whose target is still on the search path (and
   * every self-link). Removing the flagged links leaves an acyclic graph.
   *
   * :returns: A Set of link positions (indexes into `links`).
   */
  const outgoing = []
  const incoming = []
  for (let n = 0; n < nodeCount; n = n + 1) {
    outgoing.push([])
    incoming.push(0)
  }
  for (let l = 0; l < links.length; l = l + 1) {
    outgoing[links[l].source].push(l)
    if (links[l].source !== links[l].target) {
      incoming[links[l].target] = incoming[links[l].target] + 1
    }
  }

  const UNSEEN = 0
  const ON_PATH = 1
  const DONE = 2
  const state = new Array(nodeCount).fill(UNSEEN)
  const back = new Set()

  const order = []
  for (let n = 0; n < nodeCount; n = n + 1) {
    if (incoming[n] === 0) {
      order.push(n)
    }
  }
  for (let n = 0; n < nodeCount; n = n + 1) {
    order.push(n)
  }

  for (let o = 0; o < order.length; o = o + 1) {
    const start = order[o]
    if (state[start] !== UNSEEN) {
      continue
    }
    /* Stack frames: [node, position of the next outgoing link to look at]. */
    const stack = [[start, 0]]
    state[start] = ON_PATH
    while (stack.length > 0) {
      const frame = stack[stack.length - 1]
      const node = frame[0]
      if (frame[1] >= outgoing[node].length) {
        state[node] = DONE
        stack.pop()
        continue
      }
      const linkIndex = outgoing[node][frame[1]]
      frame[1] = frame[1] + 1
      const target = links[linkIndex].target
      if (state[target] === ON_PATH) {
        back.add(linkIndex)
      } else if (state[target] === UNSEEN) {
        state[target] = ON_PATH
        stack.push([target, 0])
      }
    }
  }
  return back
}


function _assignLevels(nodeCount, links, back) {
  /*
   * Column of every node: the longest path from an entry node over the
   * acyclic (forward) links, computed in topological order.
   *
   * :returns: An array of levels, one per node.
   */
  const level = new Array(nodeCount).fill(0)
  const indegree = new Array(nodeCount).fill(0)
  const outgoing = []
  for (let n = 0; n < nodeCount; n = n + 1) {
    outgoing.push([])
  }
  for (let l = 0; l < links.length; l = l + 1) {
    if (back.has(l) === true) {
      continue
    }
    outgoing[links[l].source].push(links[l].target)
    indegree[links[l].target] = indegree[links[l].target] + 1
  }

  const queue = []
  for (let n = 0; n < nodeCount; n = n + 1) {
    if (indegree[n] === 0) {
      queue.push(n)
    }
  }
  for (let head = 0; head < queue.length; head = head + 1) {
    const node = queue[head]
    for (let t = 0; t < outgoing[node].length; t = t + 1) {
      const target = outgoing[node][t]
      level[target] = Math.max(level[target], level[node] + 1)
      indegree[target] = indegree[target] - 1
      if (indegree[target] === 0) {
        queue.push(target)
      }
    }
  }
  return level
}


function _bandPath(map, main0, top0, bottom0, main1, top1, bottom1) {
  /*
   * A filled link band between two node edges, as path data. Coordinates
   * are (main, cross); `map` turns them into (x, y).
   */
  const mid = (main0 + main1) / 2
  const p = (main, cross) => {
    const point = map(main, cross)
    return `${point.x.toFixed(2)},${point.y.toFixed(2)}`
  }
  const d = `M${p(main0, top0)} C${p(mid, top0)} ${p(mid, top1)} ${p(main1, top1)} ` +
    `L${p(main1, bottom1)} C${p(mid, bottom1)} ${p(mid, bottom0)} ${p(main0, bottom0)} Z`
  return d
}


function _renderSessionFlow(ctx) {
  /*
   * Render a session-flow (Sankey-style) chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const flow = _readFlow(raw)
  const nodes = flow.nodes
  const links = flow.links
  const root = svgEl("g", { part: "plot" }, [])

  ctx.setTable({
    columns: ["From", "To", "Sessions"],
    rows: links.map((link) => [nodes[link.source].label, nodes[link.target].label, link.value]),
    caption: ctx.label
  })

  if (nodes.length === 0) {
    return root
  }

  const back = _findBackLinks(nodes.length, links)
  const level = _assignLevels(nodes.length, links, back)

  /* Node size: max(inflow, outflow) over all links (a node with no links: 0). */
  const inflow = new Array(nodes.length).fill(0)
  const outflow = new Array(nodes.length).fill(0)
  for (let l = 0; l < links.length; l = l + 1) {
    outflow[links[l].source] = outflow[links[l].source] + links[l].value
    inflow[links[l].target] = inflow[links[l].target] + links[l].value
  }
  const size = nodes.map((node, n) => Math.max(inflow[n], outflow[n]))

  let maxLevel = 0
  for (let n = 0; n < nodes.length; n = n + 1) {
    maxLevel = Math.max(maxLevel, level[n])
  }
  const columns = []
  for (let lvl = 0; lvl <= maxLevel; lvl = lvl + 1) {
    columns.push([])
  }
  for (let n = 0; n < nodes.length; n = n + 1) {
    columns[level[n]].push(n)
  }

  const horizontal = ctx.orientation !== "vertical"
  const hasBack = back.size > 0
  const margin = horizontal === true
    ? { top: 8, right: 8, bottom: hasBack === true ? 26 : 8, left: 8 }
    : { top: 8, right: hasBack === true ? 26 : 8, bottom: 20, left: 8 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)
  const mainLen = horizontal === true ? plotW : plotH
  const crossLen = horizontal === true ? plotH : plotW
  const map = horizontal === true
    ? (main, cross) => ({ x: main, y: cross })
    : (main, cross) => ({ x: cross, y: main })

  const plot = svgEl("g", { transform: `translate(${margin.left},${margin.top})` }, [])
  root.appendChild(plot)

  /* Scale: the busiest column (values plus gaps) fills the cross axis. */
  const nodeThickness = 14
  let largest = 0
  for (let c = 0; c < columns.length; c = c + 1) {
    largest = Math.max(largest, columns[c].length)
  }
  const gap = Math.max(2, Math.min(12, crossLen * 0.3 / Math.max(largest, 1)))
  let unit = Infinity
  for (let c = 0; c < columns.length; c = c + 1) {
    let total = 0
    for (let k = 0; k < columns[c].length; k = k + 1) {
      total = total + size[columns[c][k]]
    }
    const room = crossLen - gap * (columns[c].length - 1)
    if (total > 0) {
      unit = Math.min(unit, Math.max(room, 1) / total)
    }
  }
  if (unit === Infinity) {
    unit = 0
  }
  const minExtent = 2

  /* Node boxes in (main, cross) space; each column is centred. */
  const boxes = new Array(nodes.length)
  const mainStep = maxLevel > 0 ? (mainLen - nodeThickness) / maxLevel : 0
  for (let c = 0; c < columns.length; c = c + 1) {
    const extents = columns[c].map((n) => Math.max(size[n] * unit, minExtent))
    const used = extents.reduce((sum, value) => sum + value, 0) + gap * (columns[c].length - 1)
    let cursor = Math.max((crossLen - used) / 2, 0)
    const main = maxLevel > 0 ? c * mainStep : (mainLen - nodeThickness) / 2
    for (let k = 0; k < columns[c].length; k = k + 1) {
      boxes[columns[c][k]] = { main: main, cross: cursor, extent: extents[k] }
      cursor = cursor + extents[k] + gap
    }
  }

  /* Stack the bands on each node edge, ordered by the far end's position. */
  const outByNode = nodes.map(() => [])
  const inByNode = nodes.map(() => [])
  for (let l = 0; l < links.length; l = l + 1) {
    outByNode[links[l].source].push(l)
    inByNode[links[l].target].push(l)
  }
  const crossCenter = (n) => boxes[n].cross + boxes[n].extent / 2
  const startOffset = new Array(links.length).fill(0)
  const endOffset = new Array(links.length).fill(0)
  for (let n = 0; n < nodes.length; n = n + 1) {
    const outs = outByNode[n].slice().sort((a, b) => {
      return (back.has(a) === true ? 1 : 0) - (back.has(b) === true ? 1 : 0) ||
        crossCenter(links[a].target) - crossCenter(links[b].target)
    })
    let cursor = 0
    for (let k = 0; k < outs.length; k = k + 1) {
      startOffset[outs[k]] = cursor
      cursor = cursor + links[outs[k]].value * unit
    }
    const ins = inByNode[n].slice().sort((a, b) => {
      return (back.has(a) === true ? 1 : 0) - (back.has(b) === true ? 1 : 0) ||
        crossCenter(links[a].source) - crossCenter(links[b].source)
    })
    cursor = 0
    for (let k = 0; k < ins.length; k = k + 1) {
      endOffset[ins[k]] = cursor
      cursor = cursor + links[ins[k]].value * unit
    }
  }

  /* Links. */
  const linkLayer = svgEl("g", { part: "flow-links" }, [])
  plot.appendChild(linkLayer)
  for (let l = 0; l < links.length; l = l + 1) {
    const link = links[l]
    const from = boxes[link.source]
    const to = boxes[link.target]
    const width = Math.max(link.value * unit, 1)
    const color = ctx.colorFor(link.source)
    const title = `${nodes[link.source].label} → ${nodes[link.target].label}: ` +
      `${formatNumber(link.value)}`
    let path = null

    if (back.has(l) === false) {
      const top0 = from.cross + startOffset[l]
      const top1 = to.cross + endOffset[l]
      path = svgEl("path", {
        d: _bandPath(map, from.main + nodeThickness, top0, top0 + width,
          to.main, top1, top1 + width),
        fill: color, "fill-opacity": 0.35, stroke: "none", part: "flow-link"
      }, [])
    } else {
      /* A return arc: out of the source's far edge, below the flow, into the target. */
      const c0 = from.cross + startOffset[l] + width / 2
      const c1 = to.cross + endOffset[l] + width / 2
      const main0 = from.main + nodeThickness
      const main1 = to.main
      const below = crossLen + (horizontal === true ? margin.bottom : margin.right) - width / 2 - 2
      const reach = Math.max(nodeThickness * 2, Math.abs(main0 - main1) * 0.25)
      const edge = horizontal === true ? margin.right : margin.bottom
      const reachOut = Math.max(Math.min(reach, mainLen + edge - main0 - 2), 4)
      const reachIn = Math.max(Math.min(reach, main1 + 6), 4)
      const p = (main, cross) => {
        const point = map(main, cross)
        return `${point.x.toFixed(2)},${point.y.toFixed(2)}`
      }
      const d = `M${p(main0, c0)} C${p(main0 + reachOut, below)} ${p(main1 - reachIn, below)} ` +
        `${p(main1, c1)}`
      path = svgEl("path", {
        d: d, fill: "none", stroke: color, "stroke-opacity": 0.3,
        "stroke-width": width, part: "flow-link flow-return"
      }, [])
    }
    path.appendChild(svgEl("title", null, title))
    linkLayer.appendChild(path)
  }

  /* Nodes and labels. */
  for (let n = 0; n < nodes.length; n = n + 1) {
    const node = nodes[n]
    const box = boxes[n]
    const color = ctx.colorFor(n)
    const ariaLabel = `${node.label}: ${formatNumber(size[n])} sessions ` +
      `(in ${formatNumber(inflow[n])}, out ${formatNumber(outflow[n])})`

    const nodeEl = svgEl("g", {
      tabindex: "0", role: "img", "aria-label": ariaLabel, part: "flow-node"
    }, [])
    const corner = map(box.main, box.cross)
    nodeEl.appendChild(svgEl("rect", {
      x: corner.x, y: corner.y,
      width: horizontal === true ? nodeThickness : box.extent,
      height: horizontal === true ? box.extent : nodeThickness,
      rx: 2, fill: color
    }, []))

    let labelAttrs = null
    let room = 0
    if (horizontal === true) {
      const atEnd = level[n] === maxLevel && maxLevel > 0
      labelAttrs = {
        x: atEnd === true ? box.main - 4 : box.main + nodeThickness + 4,
        y: box.cross + box.extent / 2 + 4,
        "text-anchor": atEnd === true ? "end" : "start"
      }
      room = maxLevel > 0 ? mainStep - nodeThickness - 8 : plotW / 2 - nodeThickness
    } else {
      labelAttrs = {
        x: box.cross + box.extent / 2,
        y: box.main + nodeThickness + 12,
        "text-anchor": "middle"
      }
      room = Math.max(box.extent, 60)
    }
    labelAttrs["font-size"] = 11
    labelAttrs.fill = "var(--mj-text, #14181f)"
    labelAttrs["pointer-events"] = "none"
    nodeEl.appendChild(svgEl("text", labelAttrs, _fitText(node.label, Math.max(room, 24), 11)))
    nodeEl.appendChild(svgEl("title", null, ariaLabel))

    const captured = node
    const index = n
    _onActivate(nodeEl, () => {
      ctx.emit("mj-chart-flow-click", {
        id: captured.source.id,
        label: captured.source.label,
        flow: size[index],
        inflow: inflow[index],
        outflow: outflow[index]
      })
    })
    plot.appendChild(nodeEl)
  }

  return root
}


/* ── entry points ─────────────────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Draw the requested type: "session-flow" draws the flow, "user-journey"
   * the journey map.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  if (ctx.type === "session-flow") {
    const flow = _renderSessionFlow(ctx)
    return flow
  }
  const journey = _renderJourney(ctx)
  return journey
}


registerRenderer("user-journey", render, { orientation: "horizontal", legend: "none" })
registerRenderer("session-flow", render, { orientation: "horizontal", legend: "none" })
