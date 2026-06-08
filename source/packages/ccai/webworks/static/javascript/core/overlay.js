/*
 * overlay.js
 *
 * Anchored-overlay positioning engine shared by popover, tooltip, menu,
 * select, combobox, context-menu, and similar components. Positions a
 * floating element relative to an anchor element with collision-aware flip
 * and shift, and keeps it positioned while the page scrolls or resizes.
 */

const PLACEMENTS = [
  "top", "top-start", "top-end",
  "bottom", "bottom-start", "bottom-end",
  "start", "start-top", "start-bottom",
  "end", "end-top", "end-bottom"
];

const OPPOSITE = {
  top: "bottom", bottom: "top", start: "end", end: "start"
};

function viewportRect() {
  const rect = {
    left: 0,
    top: 0,
    right: window.innerWidth,
    bottom: window.innerHeight
  }
  return rect
}

/*
 * Compute the (x, y) for `floating` given an `anchor` rect, the floating
 * element's size, the requested side and alignment, and a gap offset.
 */
function computeCoords(anchorRect, floatRect, side, align, offset) {
  let x = 0
  let y = 0

  if (side === "top") {
    y = anchorRect.top - floatRect.height - offset
  } else if (side === "bottom") {
    y = anchorRect.bottom + offset
  } else if (side === "start") {
    x = anchorRect.left - floatRect.width - offset
  } else if (side === "end") {
    x = anchorRect.right + offset
  }

  const vertical = side === "top" || side === "bottom"
  if (vertical === true) {
    if (align === "start") {
      x = anchorRect.left
    } else if (align === "end") {
      x = anchorRect.right - floatRect.width
    } else {
      x = anchorRect.left + (anchorRect.width - floatRect.width) / 2
    }
  } else {
    if (align === "top") {
      y = anchorRect.top
    } else if (align === "bottom") {
      y = anchorRect.bottom - floatRect.height
    } else {
      y = anchorRect.top + (anchorRect.height - floatRect.height) / 2
    }
  }

  const coords = { x: x, y: y }
  return coords
}

function fitsInViewport(coords, floatRect, view) {
  const withinX = coords.x >= view.left && coords.x + floatRect.width <= view.right
  const withinY = coords.y >= view.top && coords.y + floatRect.height <= view.bottom
  const fits = withinX === true && withinY === true
  return fits
}

function clampToViewport(coords, floatRect, view, padding) {
  let x = coords.x
  let y = coords.y

  const maxX = view.right - floatRect.width - padding
  const minX = view.left + padding
  if (x > maxX) {
    x = maxX
  }
  if (x < minX) {
    x = minX
  }

  const maxY = view.bottom - floatRect.height - padding
  const minY = view.top + padding
  if (y > maxY) {
    y = maxY
  }
  if (y < minY) {
    y = minY
  }

  const clamped = { x: x, y: y }
  return clamped
}

/*
 * Position `floating` against `anchor`.
 *
 * options: { placement, offset, padding, flip, shift }
 * placement is one of PLACEMENTS. Returns the resolved placement string.
 */
export function position(floating, anchor, options) {
  const opts = options || {}
  const placement = opts.placement || "bottom"
  const offset = opts.offset === undefined ? 6 : opts.offset
  const padding = opts.padding === undefined ? 8 : opts.padding
  const allowFlip = opts.flip !== false
  const allowShift = opts.shift !== false

  const parts = placement.split("-")
  let side = parts[0]
  const align = parts.length > 1 ? parts[1] : "center"

  const anchorRect = anchor.getBoundingClientRect()
  floating.style.position = "fixed"
  floating.style.top = "0"
  floating.style.left = "0"
  const floatRect = floating.getBoundingClientRect()
  const view = viewportRect()

  let coords = computeCoords(anchorRect, floatRect, side, align, offset)

  if (allowFlip === true) {
    const fits = fitsInViewport(coords, floatRect, view)
    if (fits === false) {
      const flippedSide = OPPOSITE[side]
      const flippedCoords = computeCoords(anchorRect, floatRect, flippedSide, align, offset)
      const flippedFits = fitsInViewport(flippedCoords, floatRect, view)
      if (flippedFits === true) {
        side = flippedSide
        coords = flippedCoords
      }
    }
  }

  if (allowShift === true) {
    coords = clampToViewport(coords, floatRect, view, padding)
  }

  floating.style.left = `${Math.round(coords.x)}px`
  floating.style.top = `${Math.round(coords.y)}px`
  floating.style.zIndex = "var(--mj-layer-popover)"

  const resolved = align === "center" ? side : `${side}-${align}`
  return resolved
}

/*
 * Keep `floating` positioned against `anchor` while scrolling/resizing.
 * Returns a dispose function that stops tracking.
 */
export function autoPosition(floating, anchor, options) {
  const update = () => {
    position(floating, anchor, options)
  }

  update()
  window.addEventListener("scroll", update, true)
  window.addEventListener("resize", update)

  let observer = null
  if (typeof ResizeObserver === "function") {
    observer = new ResizeObserver(update)
    observer.observe(anchor)
    observer.observe(floating)
  }

  const dispose = () => {
    window.removeEventListener("scroll", update, true)
    window.removeEventListener("resize", update)
    if (observer !== null) {
      observer.disconnect()
    }
  }

  return dispose
}

export { PLACEMENTS };
