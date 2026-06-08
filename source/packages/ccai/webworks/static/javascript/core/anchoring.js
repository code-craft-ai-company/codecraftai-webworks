/*
 * anchoring.js
 *
 * Docking engine for mj-* layout containers.
 *
 * Anchoring (pinning a component to a corner/edge of a positioned container)
 * is pure CSS -- see the `:host([anchor])` rules in base.css. Docking, where
 * children consume edges of a container in order and a `fill` child takes the
 * remainder, is order-dependent and therefore computed here in JS.
 *
 * mj-dock-layout calls `layoutDock(container)`; MjElement calls
 * `registerDockChild` / `unregisterDockChild` so adding or removing a docked
 * child re-runs the parent layout automatically.
 */

const DOCK_EDGES = ["top", "bottom", "start", "end", "fill"];

/*
 * Find the nearest enclosing mj-dock-layout for a docked child, crossing
 * shadow boundaries via assignedSlot where needed.
 */
function findDockLayout(node) {
  let current = node.parentNode
  let layout = null

  while (current !== null && current !== undefined) {
    const tag = current.tagName
    if (tag !== null && tag !== undefined && tag.toLowerCase() === "mj-dock-layout") {
      layout = current
      break
    }
    current = current.parentNode
  }

  return layout
}

/*
 * Notify the enclosing dock layout that its children changed and a relayout
 * is needed.
 */
export function registerDockChild(child) {
  const layout = findDockLayout(child)
  if (layout !== null && typeof layout.requestLayout === "function") {
    layout.requestLayout()
  }
  return
}

export function unregisterDockChild(child) {
  const layout = findDockLayout(child)
  if (layout !== null && typeof layout.requestLayout === "function") {
    layout.requestLayout()
  }
  return
}

/*
 * Edge-consumption docking layout. Each docked child is absolutely positioned
 * inside `container` and consumes a band from the remaining free rectangle, in
 * DOM order. Children with `dock="fill"` share whatever rectangle is left.
 *
 * The container must be `position: relative` (mj-dock-layout sets this).
 */
export function layoutDock(container) {
  const rect = container.getBoundingClientRect()
  const width = rect.width
  const height = rect.height

  if (width === 0 && height === 0) {
    return
  }

  const allChildren = Array.from(container.children)
  const docked = allChildren.filter((child) => {
    const value = child.getAttribute("dock")
    const isDocked = value !== null && DOCK_EDGES.indexOf(value) >= 0
    return isDocked
  })

  let top = 0
  let left = 0
  let right = width
  let bottom = height
  const fills = []

  for (let index = 0; index < docked.length; index = index + 1) {
    const child = docked[index]
    const edge = child.getAttribute("dock")
    child.style.position = "absolute"
    child.style.boxSizing = "border-box"

    if (edge === "fill") {
      fills.push(child)
      continue
    }

    if (edge === "top") {
      child.style.insetInlineStart = `${left}px`
      child.style.insetInlineEnd = `${width - right}px`
      child.style.top = `${top}px`
      child.style.bottom = ""
      child.style.height = ""
      const consumed = child.offsetHeight
      top = top + consumed
    } else if (edge === "bottom") {
      child.style.insetInlineStart = `${left}px`
      child.style.insetInlineEnd = `${width - right}px`
      child.style.top = ""
      child.style.bottom = `${height - bottom}px`
      child.style.height = ""
      const consumed = child.offsetHeight
      bottom = bottom - consumed
    } else if (edge === "start") {
      child.style.insetInlineStart = `${left}px`
      child.style.insetInlineEnd = ""
      child.style.top = `${top}px`
      child.style.bottom = `${height - bottom}px`
      child.style.width = ""
      const consumed = child.offsetWidth
      left = left + consumed
    } else if (edge === "end") {
      child.style.insetInlineEnd = `${width - right}px`
      child.style.insetInlineStart = ""
      child.style.top = `${top}px`
      child.style.bottom = `${height - bottom}px`
      child.style.width = ""
      const consumed = child.offsetWidth
      right = right - consumed
    }
  }

  /* Distribute the remaining rectangle across all fill children. */
  const fillCount = fills.length
  if (fillCount > 0) {
    const slice = (right - left) / fillCount
    for (let index = 0; index < fillCount; index = index + 1) {
      const child = fills[index]
      child.style.position = "absolute"
      child.style.boxSizing = "border-box"
      child.style.top = `${top}px`
      child.style.bottom = `${height - bottom}px`
      child.style.insetInlineStart = `${left + slice * index}px`
      child.style.width = `${slice}px`
    }
  }

  return
}
