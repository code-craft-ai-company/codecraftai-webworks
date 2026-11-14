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
 * `registerDockChild` / `unregisterDockChild` so adding a docked mj-* child
 * or changing its `dock` attribute re-runs the parent layout automatically.
 * Plain (non mj-*) children are covered by the observers mj-dock-layout
 * installs on the elements `getDockChildren` returns.
 *
 * Sizing contract
 *   - A band (`top`, `bottom`, `start`, `end`) keeps the size its author gave
 *     it along the axis it consumes: `height` for top/bottom, `width` for
 *     start/end, from an inline style or a stylesheet. Without one it takes
 *     the size of its content. The engine only writes the size ACROSS the
 *     band, which always spans the free rectangle.
 *   - A `fill` child is sized on both axes to the rectangle that is left.
 *   - Every inline property the engine writes is recorded per child, with the
 *     value the author had there, and is put back when the child stops being
 *     docked (or changes edge), so nothing sticks to an undocked element.
 */

const DOCK_EDGES = ["top", "bottom", "start", "end", "fill"];

/* Sizes closer than this many pixels are treated as equal. */
const SIZE_TOLERANCE = 0.01;

/*
 * What the engine wrote on each docked child:
 *   container  the dock container that manages the child
 *   saved      { cssProperty: { value, priority } } -- the author's inline
 *              value of every property the engine overwrote
 *   visible / width / height
 *              the child's box measured at the end of the last layout pass
 */
const CHILD_STATE = new WeakMap();

/*
 * The result of the last layout pass per container:
 *   width / height   the padding box the children were laid out in
 *   managed          the children that were docked in that pass
 */
const CONTAINER_STATE = new WeakMap();

/*
 * The elements a dock container lays out: its element children, where a
 * <slot> child stands for the elements assigned to it. That lets an
 * mj-dock-layout placed inside another component's shadow root dock the
 * content slotted into that component.
 */
export function getDockChildren(container) {
  const children = []
  const direct = Array.from(container.children)

  for (let index = 0; index < direct.length; index = index + 1) {
    const child = direct[index]
    const isSlot = child.localName === "slot" && typeof child.assignedElements === "function"

    if (isSlot === true) {
      const assigned = child.assignedElements({ flatten: true })
      for (let slotIndex = 0; slotIndex < assigned.length; slotIndex = slotIndex + 1) {
        children.push(assigned[slotIndex])
      }
    } else {
      children.push(child)
    }
  }

  return children
}

/*
 * Find the mj-dock-layout that lays out `node`, matching `getDockChildren`:
 * the node's parent when that is a dock layout; otherwise, for a slotted
 * node, the layout whose `<slot>` child the node is assigned to, following
 * the chain of assigned slots. The slot of the layout's OWN shadow root is
 * never the answer: its parent is the shadow root, which is why the walk
 * checks each node's parent before stepping to its assigned slot. Returns
 * null when the node is not a dock child of any layout (a node that was just
 * removed has no parent any more; the layout's own child observer covers
 * that case).
 */
function findDockLayout(node) {
  let layout = null
  let current = node

  while (layout === null && current !== null && current !== undefined) {
    const parent = current.parentNode
    if (parent !== null && parent !== undefined && parent.localName === "mj-dock-layout") {
      layout = parent
    } else {
      current = current.assignedSlot
    }
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

/* The dock edge of a child, or null when it is not docked. */
function dockEdgeOf(child) {
  const value = child.getAttribute("dock")
  let edge = null

  if (value !== null && DOCK_EDGES.indexOf(value) >= 0) {
    edge = value
  }

  return edge
}

/* Parse a computed pixel length; `auto`, `normal` and `none` count as 0. */
function parsePixels(text) {
  const parsed = parseFloat(text)
  const pixels = Number.isNaN(parsed) === true ? 0 : parsed
  return pixels
}

/* Format a pixel length for an inline style, rounded to 1/100 px. */
function toPixels(value) {
  const rounded = Math.round(value * 100) / 100
  const text = `${rounded}px`
  return text
}

function sizesDiffer(first, second) {
  const differ = Math.abs(first - second) > SIZE_TOLERANCE
  return differ
}

/*
 * The container's padding box in layout pixels -- the rectangle absolutely
 * positioned children are placed against. `clientWidth` / `clientHeight` give
 * it rounded to whole pixels and are not affected by a CSS transform; the
 * computed size supplies the fraction when it describes the same box (it
 * does not when a scrollbar takes room or the element is not rendered).
 */
function measureContainer(container, computed) {
  let width = container.clientWidth
  let height = container.clientHeight

  let preciseWidth = parseFloat(computed.width)
  let preciseHeight = parseFloat(computed.height)

  if (computed.boxSizing === "border-box") {
    preciseWidth = preciseWidth - parsePixels(computed.borderLeftWidth) - parsePixels(computed.borderRightWidth)
    preciseHeight = preciseHeight - parsePixels(computed.borderTopWidth) - parsePixels(computed.borderBottomWidth)
  } else {
    preciseWidth = preciseWidth + parsePixels(computed.paddingLeft) + parsePixels(computed.paddingRight)
    preciseHeight = preciseHeight + parsePixels(computed.paddingTop) + parsePixels(computed.paddingBottom)
  }

  if (Number.isNaN(preciseWidth) === false && Math.abs(preciseWidth - width) < 1) {
    width = preciseWidth
  }
  if (Number.isNaN(preciseHeight) === false && Math.abs(preciseHeight - height) < 1) {
    height = preciseHeight
  }

  const size = { width: width, height: height }
  return size
}

/*
 * The border box of a child in layout pixels. A child that is `display: none`
 * (the `hidden` attribute, or any stylesheet rule) is reported as not visible
 * with a zero size. The computed width / height of a rendered border-box
 * element is its used border-box size, including fractions; the offset size
 * is the fallback for boxes whose computed size is not a length.
 */
function measureChild(child, computed) {
  const box = { visible: false, width: 0, height: 0 }

  if (computed.display !== "none") {
    box.visible = true

    const width = parseFloat(computed.width)
    const height = parseFloat(computed.height)
    const usable = computed.boxSizing === "border-box" &&
      Number.isNaN(width) === false && Number.isNaN(height) === false

    if (usable === true) {
      box.width = width
      box.height = height
    } else {
      box.width = child.offsetWidth
      box.height = child.offsetHeight
    }
  }

  return box
}

/* The child's margins, with the inline pair named relative to the container. */
function readMargins(computed, containerRtl) {
  const left = parsePixels(computed.marginLeft)
  const right = parsePixels(computed.marginRight)

  const margins = {
    top: parsePixels(computed.marginTop),
    bottom: parsePixels(computed.marginBottom),
    start: containerRtl === true ? right : left,
    end: containerRtl === true ? left : right
  }
  return margins
}

/*
 * Return the engine's record for `child`, creating it on first use. A child
 * that was managed by a different container is released first so the styles
 * the other container wrote do not leak into this one.
 */
function claimDockChild(child, container) {
  let state = CHILD_STATE.get(child)

  if (state !== undefined && state.container !== container) {
    releaseDockChild(child)
    state = undefined
  }

  if (state === undefined) {
    state = { container: container, saved: {}, visible: false, width: 0, height: 0 }
    CHILD_STATE.set(child, state)
  }

  return state
}

/* Put back the author's inline value of one property the engine overwrote. */
function restoreDockStyle(child, state, name) {
  const original = state.saved[name]

  if (original !== undefined) {
    if (original.value.length > 0) {
      child.style.setProperty(name, original.value, original.priority)
    } else {
      child.style.removeProperty(name)
    }
    delete state.saved[name]
  }

  return
}

/*
 * Write `styles` ({ cssProperty: value }) on the child. The first time a
 * property is written the author's inline value is saved. Properties the
 * engine wrote in an earlier pass that are not part of `styles` any more
 * (the child changed edge) are restored to the author's value.
 */
function applyDockStyles(child, state, styles) {
  const savedNames = Object.keys(state.saved)
  for (let index = 0; index < savedNames.length; index = index + 1) {
    const name = savedNames[index]
    if (styles[name] === undefined) {
      restoreDockStyle(child, state, name)
    }
  }

  const names = Object.keys(styles)
  for (let index = 0; index < names.length; index = index + 1) {
    const name = names[index]
    const value = styles[name]

    if (state.saved[name] === undefined) {
      state.saved[name] = {
        value: child.style.getPropertyValue(name),
        priority: child.style.getPropertyPriority(name)
      }
    }

    if (child.style.getPropertyValue(name) !== value) {
      child.style.setProperty(name, value)
    }
  }

  return
}

/*
 * Stop managing a child: restore every inline property the engine wrote to
 * the author's value and forget the record. The child returns to normal flow.
 */
export function releaseDockChild(child) {
  const state = CHILD_STATE.get(child)

  if (state !== undefined) {
    const savedNames = Object.keys(state.saved)
    for (let index = 0; index < savedNames.length; index = index + 1) {
      restoreDockStyle(child, state, savedNames[index])
    }
    CHILD_STATE.delete(child)
  }

  return
}

/*
 * Edge-consumption docking layout. Each docked child is absolutely positioned
 * inside `container` and consumes a band from the remaining free rectangle, in
 * DOM order. Children with `dock="fill"` share whatever rectangle is left,
 * side by side along the inline axis.
 *
 * The free rectangle starts at the container's padding edge, so padding on
 * the container insets the whole layout, and the container's `row-gap` /
 * `column-gap` are kept between a band and whatever follows it. `start` and
 * `end` follow the container's direction (they swap sides in RTL). A child's
 * margins are honored: its margin box is what consumes the band. A child that
 * is `display: none` consumes nothing.
 *
 * The container must be positioned (mj-dock-layout sets `position: relative`).
 * Returns true when a layout pass ran, false when the container is not
 * rendered and nothing was touched.
 */
export function layoutDock(container) {
  const containerStyle = window.getComputedStyle(container)
  const size = measureContainer(container, containerStyle)

  if (size.width === 0 && size.height === 0) {
    return false
  }

  const containerRtl = containerStyle.direction === "rtl"
  const rowGap = parsePixels(containerStyle.rowGap)
  const columnGap = parsePixels(containerStyle.columnGap)
  const paddingLeft = parsePixels(containerStyle.paddingLeft)
  const paddingRight = parsePixels(containerStyle.paddingRight)

  /* Distance of each side of the free rectangle from the padding box edge. */
  const free = {
    top: parsePixels(containerStyle.paddingTop),
    bottom: parsePixels(containerStyle.paddingBottom),
    start: containerRtl === true ? paddingRight : paddingLeft,
    end: containerRtl === true ? paddingLeft : paddingRight
  }

  const children = getDockChildren(container)
  const docked = []
  for (let index = 0; index < children.length; index = index + 1) {
    if (dockEdgeOf(children[index]) !== null) {
      docked.push(children[index])
    }
  }

  /* Children this container docked before that are not docked any more. */
  const previous = CONTAINER_STATE.get(container)
  if (previous !== undefined) {
    for (let index = 0; index < previous.managed.length; index = index + 1) {
      const former = previous.managed[index]
      const formerState = CHILD_STATE.get(former)
      const stillOurs = formerState !== undefined && formerState.container === container
      if (stillOurs === true && docked.indexOf(former) < 0) {
        releaseDockChild(former)
      }
    }
  }

  const fills = []

  for (let index = 0; index < docked.length; index = index + 1) {
    const child = docked[index]
    const edge = dockEdgeOf(child)
    const childStyle = window.getComputedStyle(child)
    const state = claimDockChild(child, container)

    if (childStyle.display === "none") {
      continue
    }

    /*
     * Logical insets resolve against the CHILD's direction. When it differs
     * from the container's (a dir="ltr" panel in an RTL layout) the
     * container's start side is the child's inline end.
     */
    const childRtl = childStyle.direction === "rtl"
    const startProperty = childRtl === containerRtl ? "inset-inline-start" : "inset-inline-end"
    const endProperty = childRtl === containerRtl ? "inset-inline-end" : "inset-inline-start"
    const margins = readMargins(childStyle, containerRtl)

    if (edge === "fill") {
      fills.push({ child: child, state: state, margins: margins, startProperty: startProperty })
      continue
    }

    const freeWidth = Math.max(0, size.width - free.start - free.end)
    const freeHeight = Math.max(0, size.height - free.top - free.bottom)
    const bandWidth = Math.max(0, freeWidth - margins.start - margins.end)
    const bandHeight = Math.max(0, freeHeight - margins.top - margins.bottom)

    const styles = { "position": "absolute", "box-sizing": "border-box" }

    if (edge === "top") {
      styles["top"] = toPixels(free.top)
      styles[startProperty] = toPixels(free.start)
      styles["width"] = toPixels(bandWidth)
    } else if (edge === "bottom") {
      styles["bottom"] = toPixels(free.bottom)
      styles[startProperty] = toPixels(free.start)
      styles["width"] = toPixels(bandWidth)
    } else if (edge === "start") {
      styles[startProperty] = toPixels(free.start)
      styles["top"] = toPixels(free.top)
      styles["height"] = toPixels(bandHeight)
    } else {
      styles[endProperty] = toPixels(free.end)
      styles["top"] = toPixels(free.top)
      styles["height"] = toPixels(bandHeight)
    }

    applyDockStyles(child, state, styles)

    /* Measured after the write: the cross size can change the band's size. */
    const box = measureChild(child, childStyle)

    if (edge === "top") {
      free.top = free.top + box.height + margins.top + margins.bottom + rowGap
    } else if (edge === "bottom") {
      free.bottom = free.bottom + box.height + margins.top + margins.bottom + rowGap
    } else if (edge === "start") {
      free.start = free.start + box.width + margins.start + margins.end + columnGap
    } else {
      free.end = free.end + box.width + margins.start + margins.end + columnGap
    }
  }

  /* Distribute the remaining rectangle across all visible fill children. */
  const fillCount = fills.length
  if (fillCount > 0) {
    const freeWidth = Math.max(0, size.width - free.start - free.end)
    const freeHeight = Math.max(0, size.height - free.top - free.bottom)
    const slice = Math.max(0, (freeWidth - columnGap * (fillCount - 1)) / fillCount)

    for (let index = 0; index < fillCount; index = index + 1) {
      const fill = fills[index]
      const styles = { "position": "absolute", "box-sizing": "border-box" }

      styles["top"] = toPixels(free.top)
      styles[fill.startProperty] = toPixels(free.start + (slice + columnGap) * index)
      styles["width"] = toPixels(Math.max(0, slice - fill.margins.start - fill.margins.end))
      styles["height"] = toPixels(Math.max(0, freeHeight - fill.margins.top - fill.margins.bottom))

      applyDockStyles(fill.child, fill.state, styles)
    }
  }

  /* Remember the resulting geometry so `isDockLayoutStale` can compare. */
  for (let index = 0; index < docked.length; index = index + 1) {
    const child = docked[index]
    const state = CHILD_STATE.get(child)
    const box = measureChild(child, window.getComputedStyle(child))
    state.visible = box.visible
    state.width = box.width
    state.height = box.height
  }

  CONTAINER_STATE.set(container, { width: size.width, height: size.height, managed: docked })

  return true
}

/*
 * Tell whether the container or one of its docked children has a different
 * size (or visibility) than the last layout pass left it with. Resize
 * observers call this so the size changes the engine itself causes do not
 * schedule another pass.
 */
export function isDockLayoutStale(container) {
  const record = CONTAINER_STATE.get(container)
  let stale = false

  if (record === undefined) {
    stale = true
  } else {
    const size = measureContainer(container, window.getComputedStyle(container))
    if (sizesDiffer(size.width, record.width) === true || sizesDiffer(size.height, record.height) === true) {
      stale = true
    }

    for (let index = 0; index < record.managed.length && stale === false; index = index + 1) {
      const child = record.managed[index]
      const state = CHILD_STATE.get(child)

      if (state === undefined) {
        stale = true
      } else {
        const box = measureChild(child, window.getComputedStyle(child))
        if (
          box.visible !== state.visible ||
          sizesDiffer(box.width, state.width) === true ||
          sizesDiffer(box.height, state.height) === true
        ) {
          stale = true
        }
      }
    }
  }

  return stale
}
