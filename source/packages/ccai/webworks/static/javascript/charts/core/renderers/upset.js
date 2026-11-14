/*
 * upset.js
 *
 * UpSet plot renderer – set-intersection bars + membership matrix.
 *
 * JSON shape (ctx.raw):
 *   sets[]           { name, size }          – individual sets
 *   intersections[]  { sets[], size }        – named intersections, drawn
 *                    as given (exclusive or inclusive, as the data says);
 *                    entries naming an unknown set are dropped and a
 *                    repeated combination is drawn once
 *   elements[]       optional { sets[] } (or plain arrays of set names), one
 *                    per element: when present the EXCLUSIVE intersections
 *                    and the set sizes are computed from it, and
 *                    `intersections` / `sets[].size` are not needed
 *   max_columns      optional cap on the number of intersection columns
 *
 * Layout regions:
 *   1. Top: vertical bars for intersection sizes with value labels
 *   2. Bottom: dot membership matrix (one row per set, one column per
 *      intersection, members joined by a line)
 *   3. Bottom left: horizontal bars for individual set sizes with values
 *
 * Columns are sized to the width; when there are more intersections than
 * fit (about 14px per column) the largest are shown and a "+N more" note
 * names how many were left out (they stay in the accessible table).
 *
 * `sort` attr: "size" (default) | "degree"
 *
 * Interaction: intersection bars emit `mj-chart-upset-click` { sets, size };
 * set bars emit `mj-chart-upset-set-click` { name, size }.
 *
 * Registers: "upset"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { linearScale, niceTicks } from "../scales.js";

const MIN_COLUMN = 14
const CHAR_WIDTH = 0.6


function _number(value) {
  /*
   * A finite, non-negative number, else 0.
   */
  const numeric = typeof value === "number" && Number.isFinite(value) === true ? Math.max(value, 0) : 0
  return numeric
}


function _readData(raw) {
  /*
   * Normalise sets and intersections (computed from elements when given).
   *
   * :returns: { sets: [{name, size}], intersections: [{members, names,
   *     size}], dropped: count of intersections that named unknown sets }
   */
  const sets = []
  const indexOf = new Map()
  const list = Array.isArray(raw.sets) === true ? raw.sets : []
  for (let index = 0; index < list.length; index = index + 1) {
    const entry = list[index]
    const name = entry !== null && typeof entry === "object" && entry.name !== undefined && entry.name !== null
      ? String(entry.name)
      : (typeof entry === "string" ? entry : null)
    if (name === null || indexOf.has(name) === true) {
      continue
    }
    indexOf.set(name, sets.length)
    sets.push({ name: name, size: entry !== null && typeof entry === "object" ? _number(entry.size) : 0 })
  }

  const combos = new Map()
  let dropped = 0
  const addCombo = (names, size, accumulate) => {
    const members = []
    for (let m = 0; m < names.length; m = m + 1) {
      const position = indexOf.get(String(names[m]))
      if (position === undefined) {
        return false
      }
      if (members.indexOf(position) < 0) {
        members.push(position)
      }
    }
    if (members.length === 0) {
      return false
    }
    members.sort((a, b) => a - b)
    const key = members.join(",")
    if (combos.has(key) === true) {
      if (accumulate === true) {
        combos.get(key).size = combos.get(key).size + size
      }
      return true
    }
    combos.set(key, { members: members, names: members.map((m) => sets[m].name), size: size })
    return true
  }

  const elements = Array.isArray(raw.elements) === true ? raw.elements : null
  if (elements !== null) {
    /* Exclusive intersections and set sizes from element memberships. */
    sets.forEach((set) => {
      set.size = 0
    })
    for (let index = 0; index < elements.length; index = index + 1) {
      const entry = elements[index]
      const names = Array.isArray(entry) === true
        ? entry
        : (entry !== null && typeof entry === "object" && Array.isArray(entry.sets) === true ? entry.sets : null)
      if (names === null) {
        continue
      }
      const known = Array.from(new Set(names.map((name) => String(name)))).filter((name) => indexOf.has(name))
      if (known.length === 0) {
        continue
      }
      known.forEach((name) => {
        sets[indexOf.get(name)].size = sets[indexOf.get(name)].size + 1
      })
      addCombo(known, 1, true)
    }
  } else {
    const given = Array.isArray(raw.intersections) === true ? raw.intersections : []
    for (let index = 0; index < given.length; index = index + 1) {
      const entry = given[index]
      if (entry === null || typeof entry !== "object" || Array.isArray(entry.sets) === false) {
        continue
      }
      if (addCombo(entry.sets, _number(entry.size), false) === false) {
        dropped = dropped + 1
      }
    }
  }

  return { sets: sets, intersections: Array.from(combos.values()), dropped: dropped }
}


function _activate(element, handler) {
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


export function render(ctx) {
  /*
   * Render an UpSet plot.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const data = _readData(raw)
  const sets = data.sets
  const sortMode = ctx.attrs("sort", "size")
  const root = svgEl("g", { part: "plot" }, [])

  const sorted = data.intersections.slice().sort((a, b) => {
    if (sortMode === "degree" && a.members.length !== b.members.length) {
      return a.members.length - b.members.length
    }
    return b.size - a.size
  })

  const tableRows = sorted.map((item) => [item.names.join(" ∩ "), item.members.length, item.size])
  sets.forEach((set) => {
    tableRows.push([`${set.name} (set total)`, 1, set.size])
  })
  ctx.setTable({ columns: ["Intersection", "Sets", "Size"], rows: tableRows, caption: ctx.label })

  if (sets.length === 0 || sorted.length === 0) {
    return root
  }

  /* Layout. */
  let longest = 0
  sets.forEach((set) => {
    longest = Math.max(longest, set.name.length * 11 * CHAR_WIDTH)
  })
  const setLabelW = Math.min(Math.max(longest + 8, 40), ctx.width * 0.22)
  const leftBarW = Math.min(Math.max(ctx.width * 0.16, 60), 120)
  const margin = { top: 20, right: 12, bottom: 18, left: 4 }
  const matrixX = margin.left + leftBarW + setLabelW
  const availableW = Math.max(ctx.width - matrixX - margin.right, 20)
  const totalH = Math.max(ctx.height - margin.top - margin.bottom, 20)

  let capacity = Math.max(Math.floor(availableW / MIN_COLUMN), 1)
  if (Number.isInteger(raw.max_columns) === true && raw.max_columns > 0) {
    capacity = Math.min(capacity, raw.max_columns)
  }
  let shown = sorted
  let hidden = 0
  if (sorted.length > capacity) {
    shown = sorted.slice().sort((a, b) => b.size - a.size).slice(0, capacity)
    shown = sorted.filter((item) => shown.indexOf(item) >= 0)
    hidden = sorted.length - shown.length
  }

  const colW = availableW / shown.length
  const matrixH = Math.min(totalH * 0.45, sets.length * 24)
  const rowH = matrixH / sets.length
  const topBarH = totalH - matrixH - 6
  const dotR = Math.max(Math.min(rowH * 0.3, colW * 0.32, 7), 1.5)
  const barColor = ctx.colorFor(0)

  let maxInter = 0
  shown.forEach((item) => {
    maxInter = Math.max(maxInter, item.size)
  })
  const ticks = niceTicks(0, Math.max(maxInter, 1), 4)
  const topValue = Math.max(ticks[ticks.length - 1], maxInter, 1)
  const topY = linearScale([0, topValue], [topBarH, 0])

  let maxSet = 0
  sets.forEach((set) => {
    maxSet = Math.max(maxSet, set.size)
  })
  const setX = linearScale([0, Math.max(maxSet, 1)], [leftBarW, 0])

  const plot = svgEl("g", { transform: `translate(0,${margin.top})` }, [])
  root.appendChild(plot)

  /* ── Top bars ─────────────────────────────────────────────────── */
  const top = svgEl("g", { transform: `translate(${matrixX},0)` }, [])
  plot.appendChild(top)
  const grid = svgEl("g", { "aria-hidden": "true" }, [])
  top.appendChild(grid)
  for (let t = 0; t < ticks.length; t = t + 1) {
    const y = topY(ticks[t])
    grid.appendChild(svgEl("line", {
      x1: 0, y1: y, x2: shown.length * colW, y2: y,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    grid.appendChild(svgEl("text", {
      x: -4, y: y + 3, "text-anchor": "end", "font-size": 10, fill: "var(--mj-text-muted, #5f6673)"
    }, formatNumber(ticks[t], { notation: "compact", maximumFractionDigits: 1 })))
  }
  grid.appendChild(svgEl("text", {
    x: -4, y: -10, "text-anchor": "end", "font-size": 10, fill: "var(--mj-text-muted, #5f6673)"
  }, "Intersection"))

  const valueFont = 9
  for (let i = 0; i < shown.length; i = i + 1) {
    const item = shown[i]
    const y = topY(item.size)
    const label = `${item.names.join(" ∩ ")}: ${formatNumber(item.size)}`
    const bar = svgEl("g", { tabindex: "0", role: "img", "aria-label": label, part: "upset-bar" }, [])
    bar.appendChild(svgEl("rect", {
      x: (i * colW + colW * 0.12).toFixed(2), y: y.toFixed(2),
      width: Math.max(colW * 0.76, 1).toFixed(2), height: Math.max(topBarH - y, 0.5).toFixed(2),
      rx: 1.5, fill: barColor
    }, []))
    const text = formatNumber(item.size, { notation: "compact", maximumFractionDigits: 1 })
    if (text.length * valueFont * CHAR_WIDTH <= colW + 2) {
      bar.appendChild(svgEl("text", {
        x: (i * colW + colW / 2).toFixed(2), y: (y - 3).toFixed(2), "text-anchor": "middle",
        "font-size": valueFont, fill: "var(--mj-text, #14181f)", "aria-hidden": "true"
      }, text))
    }
    bar.appendChild(svgEl("title", null, label))
    const captured = item
    _activate(bar, () => {
      ctx.emit("mj-chart-upset-click", { sets: captured.names, size: captured.size })
    })
    top.appendChild(bar)
  }
  if (hidden > 0) {
    top.appendChild(svgEl("text", {
      x: shown.length * colW, y: -4, "text-anchor": "end", "font-size": 10,
      fill: "var(--mj-text-muted, #5f6673)", part: "upset-more"
    }, `+${hidden} more (smallest) not shown`))
  }

  /* ── Matrix ───────────────────────────────────────────────────── */
  const matrixY = topBarH + 6
  const matrix = svgEl("g", { transform: `translate(${matrixX},${matrixY})`, "aria-hidden": "true" }, [])
  plot.appendChild(matrix)
  for (let s = 0; s < sets.length; s = s + 1) {
    if (s % 2 === 0) {
      matrix.appendChild(svgEl("rect", {
        x: -setLabelW - leftBarW, y: s * rowH, width: shown.length * colW + setLabelW + leftBarW,
        height: rowH, fill: "var(--mj-bg-muted, #eef0f3)", "fill-opacity": 0.55
      }, []))
    }
  }
  for (let i = 0; i < shown.length; i = i + 1) {
    const item = shown[i]
    const cx = i * colW + colW / 2
    if (item.members.length >= 2) {
      const first = item.members[0]
      const last = item.members[item.members.length - 1]
      matrix.appendChild(svgEl("line", {
        x1: cx, y1: first * rowH + rowH / 2, x2: cx, y2: last * rowH + rowH / 2,
        stroke: barColor, "stroke-width": Math.max(dotR * 0.6, 1.5)
      }, []))
    }
    for (let s = 0; s < sets.length; s = s + 1) {
      const member = item.members.indexOf(s) >= 0
      matrix.appendChild(svgEl("circle", {
        cx: cx.toFixed(2), cy: (s * rowH + rowH / 2).toFixed(2), r: dotR.toFixed(2),
        fill: member === true ? barColor : "var(--mj-border, #e0e3e9)"
      }, []))
    }
  }

  /* ── Set-size bars and set names ──────────────────────────────── */
  const left = svgEl("g", { transform: `translate(${margin.left},${matrixY})` }, [])
  plot.appendChild(left)
  for (let s = 0; s < sets.length; s = s + 1) {
    const set = sets[s]
    const x = setX(set.size)
    const label = `${set.name}: ${formatNumber(set.size)}`
    const group = svgEl("g", { tabindex: "0", role: "img", "aria-label": label, part: "upset-set" }, [])
    group.appendChild(svgEl("rect", {
      x: x.toFixed(2), y: (s * rowH + rowH * 0.15).toFixed(2),
      width: Math.max(leftBarW - x, 0.5).toFixed(2), height: Math.max(rowH * 0.7, 1).toFixed(2),
      rx: 1.5, fill: barColor, "fill-opacity": 0.6, part: "upset-set-bar"
    }, []))
    const valueText = formatNumber(set.size, { notation: "compact", maximumFractionDigits: 1 })
    const inside = leftBarW - x > valueText.length * valueFont * CHAR_WIDTH + 6
    group.appendChild(svgEl("text", {
      x: inside === true ? (x + 3).toFixed(2) : (x - 3).toFixed(2),
      y: (s * rowH + rowH / 2 + 3).toFixed(2),
      "text-anchor": inside === true ? "start" : "end", "font-size": valueFont,
      fill: "var(--mj-text, #14181f)", "aria-hidden": "true"
    }, valueText))
    const capacityChars = Math.max(Math.floor((setLabelW - 6) / (11 * CHAR_WIDTH)), 1)
    const name = set.name.length > capacityChars ? set.name.slice(0, Math.max(capacityChars - 1, 1)) + "…" : set.name
    group.appendChild(svgEl("text", {
      x: leftBarW + setLabelW - 6, y: (s * rowH + rowH / 2 + 4).toFixed(2), "text-anchor": "end",
      "font-size": 11, fill: "var(--mj-text, #14181f)", "aria-hidden": "true"
    }, name))
    group.appendChild(svgEl("title", null, label))
    const captured = set
    _activate(group, () => {
      ctx.emit("mj-chart-upset-set-click", { name: captured.name, size: captured.size })
    })
    left.appendChild(group)
  }
  left.appendChild(svgEl("text", {
    x: leftBarW, y: matrixH + 13, "text-anchor": "end", "font-size": 10,
    fill: "var(--mj-text-muted, #5f6673)", "aria-hidden": "true"
  }, "Set size"))

  return root
}


registerRenderer("upset", render, { legend: "none" })
