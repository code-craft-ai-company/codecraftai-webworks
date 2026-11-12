/*
 * overlay.js
 *
 * The overlay layer shared by popover, tooltip, menu, select, combobox,
 * context-menu, dialog, drawer and similar components. Three things live
 * here:
 *
 *   1. Anchored positioning -- `position` / `autoPosition` place a floating
 *      element against an anchor with collision-aware flip and shift, and
 *      keep it there while the page scrolls or resizes.
 *
 *   2. The top layer -- where the browser supports the Popover API a floating
 *      element is shown in the top layer, so it is neither offset by a
 *      transformed ancestor nor clipped by one with `overflow: hidden` (an
 *      open dialog, drawer or popover). Without the Popover API the element
 *      stays `position: fixed` and the offset of its containing block is
 *      compensated instead.
 *
 *   3. The layer stack -- open surfaces (dialog, drawer, lightbox, command
 *      palette, tour, popover) register themselves so that Escape closes
 *      only the topmost one, and so that body-level helpers (toasts, live
 *      regions, the base-class context menu) can move inside the topmost
 *      modal surface, where they stay visible and interactive.
 */

import { flatParent, flatContains } from "./focustrap.js";

const PLACEMENTS = [
  "top", "top-start", "top-end",
  "bottom", "bottom-start", "bottom-end",
  "start", "start-top", "start-bottom",
  "end", "end-top", "end-bottom"
];

const OPPOSITE = {
  top: "bottom", bottom: "top", start: "end", end: "start"
};

/* autoPosition follows a moving anchor until it keeps still this long. */
const SETTLE_STABLE_FRAMES = 10;
const SETTLE_MAX_MS = 2000;

/* ------------------------------------------------------------------------
 * Top layer
 * ------------------------------------------------------------------------ */

/* Marks an element this module put in the top layer (and may take out). */
const TOP_LAYER_ATTRIBUTE = "data-mj-top-layer";

/*
 * The user-agent stylesheet gives every [popover] element `inset: 0`,
 * `margin: auto`, a border, padding, `overflow: auto` and system colors.
 * A component's popup never asked for those, so they are neutralised with a
 * zero-specificity rule: anything the component's own stylesheet declares
 * still wins.
 */
const TOP_LAYER_CSS = `
:where([data-mj-top-layer]) {
  inset: auto;
  margin: 0;
  border: 0 none;
  padding: 0;
  overflow: visible;
  width: auto;
  height: auto;
  color: inherit;
  background-color: transparent;
}
`;

let topLayerSheet = null;

/*
 * Counts every element entering the top layer. An element whose own number
 * equals the counter is the topmost one and need not be raised again.
 */
let topLayerSequence = 0;
const topLayerOrder = new WeakMap();

export function supportsTopLayer() {
  const supported = typeof HTMLElement !== "undefined" &&
    typeof HTMLElement.prototype.showPopover === "function"
  return supported
}

function adoptTopLayerSheet(root) {
  if (topLayerSheet === null) {
    topLayerSheet = new CSSStyleSheet()
    topLayerSheet.replaceSync(TOP_LAYER_CSS)
  }

  const canAdopt = root !== null && root !== undefined && Array.isArray(root.adoptedStyleSheets) === true
  if (canAdopt === true && root.adoptedStyleSheets.includes(topLayerSheet) === false) {
    /* First, so every other sheet of the root overrides it. */
    root.adoptedStyleSheets = [topLayerSheet, ...root.adoptedStyleSheets]
  }
  return
}

/*
 * Tell this module that something it does not manage (a native modal
 * <dialog>) entered the top layer, so popups shown earlier are raised above
 * it the next time they are positioned.
 */
export function noteTopLayerChange() {
  topLayerSequence = topLayerSequence + 1
  return
}

function isInTopLayer(element) {
  let inTopLayer = false
  if (supportsTopLayer() === true && element.hasAttribute(TOP_LAYER_ATTRIBUTE) === true) {
    inTopLayer = element.matches(":popover-open")
  }
  return inTopLayer
}

/*
 * Show `element` in the top layer, above everything shown before it. Calling
 * it again for an element that is already there raises it to the top.
 * Returns false (and changes nothing) when the Popover API is missing, the
 * element is not connected, or the element manages a `popover` attribute of
 * its own.
 */
export function showInTopLayer(element) {
  let shown = false

  const managed = element.hasAttribute(TOP_LAYER_ATTRIBUTE)
  const ownsPopover = managed === false && element.hasAttribute("popover")

  if (supportsTopLayer() === true && element.isConnected === true && ownsPopover === false) {
    adoptTopLayerSheet(element.getRootNode())
    element.setAttribute(TOP_LAYER_ATTRIBUTE, "")
    element.setAttribute("popover", "manual")

    try {
      if (element.matches(":popover-open") === true) {
        element.hidePopover()
      }
      element.showPopover()
      shown = true
    } catch (error) {
      /* The browser refused (e.g. removed while opening): stay position: fixed. */
      element.removeAttribute("popover")
      element.removeAttribute(TOP_LAYER_ATTRIBUTE)
    }

    if (shown === true) {
      topLayerSequence = topLayerSequence + 1
      topLayerOrder.set(element, topLayerSequence)
    }
  }

  return shown
}

/* Take an element shown with `showInTopLayer` out of the top layer again. */
export function removeFromTopLayer(element) {
  if (element.hasAttribute(TOP_LAYER_ATTRIBUTE) === true) {
    try {
      if (element.matches(":popover-open") === true) {
        element.hidePopover()
      }
    } catch (error) {
      /* Already hidden by the browser (element was disconnected). */
    }
    element.removeAttribute("popover")
    element.removeAttribute(TOP_LAYER_ATTRIBUTE)
    topLayerOrder.delete(element)
  }
  return
}

/* Put `element` in the top layer unless it already is the topmost entry. */
function ensureTopmost(element) {
  if (supportsTopLayer() === true) {
    const isTopmost = isInTopLayer(element) === true && topLayerOrder.get(element) === topLayerSequence
    if (isTopmost === false) {
      showInTopLayer(element)
    }
  }
  return
}

/* ------------------------------------------------------------------------
 * Anchored positioning
 * ------------------------------------------------------------------------ */

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
 * True when an element with this computed style is the containing block of
 * its `position: fixed` descendants.
 */
function containsFixedDescendants(style) {
  const contain = style.contain || ""
  const willChange = style.willChange || ""
  const containerType = style.containerType || "normal"
  const backdropFilter = style.backdropFilter || "none"

  const contains = style.transform !== "none" ||
    style.perspective !== "none" ||
    style.filter !== "none" ||
    backdropFilter !== "none" ||
    /paint|layout|strict|content/.test(contain) === true ||
    /transform|perspective|filter/.test(willChange) === true ||
    containerType !== "normal"

  return contains
}

/*
 * The viewport coordinate that `left: 0; top: 0` resolves to for `floating`.
 * In the top layer that is the viewport origin. Otherwise the nearest
 * ancestor with a transform, filter or containment is the containing block
 * of a fixed element, and its padding-box corner is the origin.
 */
function fixedOrigin(floating) {
  const origin = { x: 0, y: 0 }

  if (isInTopLayer(floating) === false) {
    let ancestor = flatParent(floating)
    while (ancestor !== null) {
      const style = window.getComputedStyle(ancestor)
      if (containsFixedDescendants(style) === true) {
        const rect = ancestor.getBoundingClientRect()
        origin.x = rect.left + ancestor.clientLeft
        origin.y = rect.top + ancestor.clientTop
        break
      }
      ancestor = flatParent(ancestor)
    }
  }

  return origin
}

/*
 * Compute the (x, y) for `floating` given an `anchor` rect, the floating
 * element's size, the requested side and alignment, and a gap offset.
 * `start` and `end` are logical: they follow the anchor's direction, so in
 * RTL the `start` side is the right-hand side and a `-start` alignment lines
 * up the right-hand edges.
 */
function computeCoords(anchorRect, floatSize, side, align, offset, rtl) {
  let x = 0
  let y = 0

  const leftSide = (side === "start" && rtl === false) || (side === "end" && rtl === true)
  const rightSide = (side === "end" && rtl === false) || (side === "start" && rtl === true)

  if (side === "top") {
    y = anchorRect.top - floatSize.height - offset
  } else if (side === "bottom") {
    y = anchorRect.bottom + offset
  } else if (leftSide === true) {
    x = anchorRect.left - floatSize.width - offset
  } else if (rightSide === true) {
    x = anchorRect.right + offset
  }

  const vertical = side === "top" || side === "bottom"
  if (vertical === true) {
    const alignLeft = (align === "start" && rtl === false) || (align === "end" && rtl === true)
    const alignRight = (align === "end" && rtl === false) || (align === "start" && rtl === true)

    if (alignLeft === true) {
      x = anchorRect.left
    } else if (alignRight === true) {
      x = anchorRect.right - floatSize.width
    } else {
      x = anchorRect.left + (anchorRect.width - floatSize.width) / 2
    }
  } else {
    if (align === "top") {
      y = anchorRect.top
    } else if (align === "bottom") {
      y = anchorRect.bottom - floatSize.height
    } else {
      y = anchorRect.top + (anchorRect.height - floatSize.height) / 2
    }
  }

  const coords = { x: x, y: y }
  return coords
}

/*
 * How far the floating box sticks out of the viewport along the axis of its
 * side (vertical for top/bottom, horizontal for start/end). Zero when it
 * fits. The cross axis is deliberately ignored: shifting fixes that.
 */
function mainAxisOverflow(coords, floatSize, view, side) {
  let overflow = 0

  if (side === "top" || side === "bottom") {
    overflow = Math.max(0, view.top - coords.y) + Math.max(0, coords.y + floatSize.height - view.bottom)
  } else {
    overflow = Math.max(0, view.left - coords.x) + Math.max(0, coords.x + floatSize.width - view.right)
  }

  return overflow
}

function clampToViewport(coords, floatSize, view, padding) {
  let x = coords.x
  let y = coords.y

  const maxX = view.right - floatSize.width - padding
  const minX = view.left + padding
  if (x > maxX) {
    x = maxX
  }
  if (x < minX) {
    x = minX
  }

  const maxY = view.bottom - floatSize.height - padding
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
 * options:
 *   placement         one of PLACEMENTS (default "bottom").
 *   offset            gap between anchor and floating element (default 6).
 *   padding           minimum distance kept from the viewport edge (default 8).
 *   flip              false to never move to the opposite side.
 *   shift             false to never slide along the viewport edge.
 *   topLayer          false to leave the element where it is instead of
 *                     showing it in the top layer.
 *   constrain         true to cap the element's height to the space left on
 *                     the chosen side (top / bottom placements).
 *   hideWhenDetached  true to hide the element while its anchor is scrolled
 *                     completely out of the viewport.
 *   arrow             true to publish `--mj-anchor-offset` on the floating
 *                     element: the distance from its start edge to the
 *                     centre of the anchor, for placing an arrow.
 *
 * Returns the resolved placement string (the side may have flipped). The
 * same value is written to the `data-mj-placement` attribute.
 */
export function position(floating, anchor, options) {
  const opts = options || {}
  const placement = opts.placement || "bottom"
  const offset = opts.offset === undefined ? 6 : opts.offset
  const padding = opts.padding === undefined ? 8 : opts.padding
  const allowFlip = opts.flip !== false
  const allowShift = opts.shift !== false

  if (opts.topLayer !== false) {
    ensureTopmost(floating)
  }

  const parts = placement.split("-")
  let side = parts[0]
  const align = parts.length > 1 ? parts[1] : "center"
  const vertical = side === "top" || side === "bottom"
  const rtl = window.getComputedStyle(anchor).direction === "rtl"

  const anchorRect = anchor.getBoundingClientRect()
  floating.style.position = "fixed"
  floating.style.top = "0"
  floating.style.left = "0"
  if (opts.constrain === true) {
    floating.style.maxHeight = ""
  }

  const measured = floating.getBoundingClientRect()
  const floatSize = { width: measured.width, height: measured.height }
  const view = viewportRect()
  const origin = fixedOrigin(floating)

  let coords = computeCoords(anchorRect, floatSize, side, align, offset, rtl)

  if (allowFlip === true) {
    /*
     * Flip on the main axis only. A popup that overflows sideways is fixed
     * by shifting; rejecting the flip for that reason would leave it on the
     * side where it does not fit and slide it over its own anchor.
     */
    const overflow = mainAxisOverflow(coords, floatSize, view, side)
    if (overflow > 0) {
      const flippedSide = OPPOSITE[side]
      const flippedCoords = computeCoords(anchorRect, floatSize, flippedSide, align, offset, rtl)
      const flippedOverflow = mainAxisOverflow(flippedCoords, floatSize, view, flippedSide)
      if (flippedOverflow < overflow) {
        side = flippedSide
        coords = flippedCoords
      }
    }
  }

  if (opts.constrain === true && vertical === true) {
    let available = view.bottom - anchorRect.bottom - offset - padding
    if (side === "top") {
      available = anchorRect.top - view.top - offset - padding
    }

    const minimumUseful = 48
    if (floatSize.height > available && available >= minimumUseful) {
      floating.style.maxHeight = `${Math.floor(available)}px`
      floatSize.height = Math.floor(available)
      coords = computeCoords(anchorRect, floatSize, side, align, offset, rtl)
    }
  }

  if (allowShift === true) {
    coords = clampToViewport(coords, floatSize, view, padding)
  }

  floating.style.left = `${Math.round(coords.x - origin.x)}px`
  floating.style.top = `${Math.round(coords.y - origin.y)}px`
  floating.style.zIndex = "var(--mj-layer-popover)"

  if (opts.hideWhenDetached === true) {
    const detached = anchorRect.bottom < view.top || anchorRect.top > view.bottom ||
      anchorRect.right < view.left || anchorRect.left > view.right
    floating.style.visibility = detached === true ? "hidden" : ""
  }

  if (opts.arrow === true) {
    let anchorOffset = anchorRect.top + anchorRect.height / 2 - coords.y
    if (vertical === true) {
      anchorOffset = anchorRect.left + anchorRect.width / 2 - coords.x
    }
    floating.style.setProperty("--mj-anchor-offset", `${Math.round(anchorOffset)}px`)
  }

  const resolved = align === "center" ? side : `${side}-${align}`
  floating.setAttribute("data-mj-placement", resolved)
  return resolved
}

/*
 * Position `floating` at the viewport point (x, y), the way a context menu
 * opens at the pointer: it extends to the inline end and downwards from the
 * point, opens towards the other side where that would overflow, and is
 * finally shifted to stay fully inside the viewport.
 *
 * options:
 *   padding    minimum distance kept from the viewport edge (default 4).
 *   constrain  true to cap the height to the viewport (the element should
 *              scroll its own overflow).
 *   topLayer   false to leave the element where it is instead of showing it
 *              in the top layer.
 *
 * Returns the viewport coordinate of the element's top-left corner.
 */
export function positionAtPoint(floating, x, y, options) {
  const opts = options || {}
  const padding = opts.padding === undefined ? 4 : opts.padding

  if (opts.topLayer !== false) {
    ensureTopmost(floating)
  }

  floating.style.position = "fixed"
  floating.style.top = "0"
  floating.style.left = "0"
  if (opts.constrain === true) {
    floating.style.maxHeight = `${Math.max(0, window.innerHeight - padding * 2)}px`
  }

  const rect = floating.getBoundingClientRect()
  const view = viewportRect()
  const origin = fixedOrigin(floating)
  const rtl = window.getComputedStyle(floating).direction === "rtl"

  /* In RTL a menu extends to the left of the pointer. */
  let posX = rtl === true ? x - rect.width : x
  if (rtl === false && posX + rect.width > view.right - padding && x - rect.width >= view.left + padding) {
    posX = x - rect.width
  } else if (rtl === true && posX < view.left + padding && x + rect.width <= view.right - padding) {
    posX = x
  }

  let posY = y
  if (posY + rect.height > view.bottom - padding && y - rect.height >= view.top + padding) {
    posY = y - rect.height
  }

  const clamped = clampToViewport({ x: posX, y: posY }, rect, view, padding)

  floating.style.left = `${Math.round(clamped.x - origin.x)}px`
  floating.style.top = `${Math.round(clamped.y - origin.y)}px`
  floating.style.zIndex = "var(--mj-layer-popover)"
  return clamped
}

/*
 * Floating elements currently tracked by `autoPosition`, i.e. the anchored
 * popups that are open right now. Used to tell whether an Escape key press
 * belongs to an open popup rather than to the surface around it.
 */
const openFloats = new Set();

/*
 * Keep `floating` positioned against `anchor` while scrolling/resizing.
 * Takes the options of `position`, plus:
 *
 *   onPlacement(resolved)  called when the resolved placement changes.
 *
 * Scroll and resize updates are coalesced into one per animation frame.
 * Returns a dispose function that stops tracking and takes the element out
 * of the top layer again.
 */
export function autoPosition(floating, anchor, options) {
  const opts = options || {}
  const useTopLayer = opts.topLayer !== false

  /* The element enters the top layer once; updates only move it. */
  const followOptions = Object.assign({}, opts, { topLayer: false })

  let lastPlacement = null
  let frame = null
  let disposed = false

  const update = () => {
    if (disposed === true) {
      return
    }
    const resolved = position(floating, anchor, followOptions)
    if (resolved !== lastPlacement) {
      lastPlacement = resolved
      if (typeof opts.onPlacement === "function") {
        opts.onPlacement(resolved)
      }
    }
    return
  }

  const scheduleUpdate = () => {
    if (frame === null) {
      frame = window.requestAnimationFrame(() => {
        frame = null
        update()
      })
    }
    return
  }

  /*
   * The anchor can move without any scroll, resize or size change: a popup
   * opened while its dialog or drawer is still animating in. Right after
   * opening, the anchor is therefore followed every frame until it has kept
   * still for SETTLE_STABLE_FRAMES frames (at most SETTLE_MAX_MS).
   */
  let settleFrame = null
  let stableFrames = 0
  let lastAnchorBox = ""
  const settleStart = Date.now()

  const followWhileSettling = () => {
    settleFrame = null
    if (disposed === true) {
      return
    }

    const rect = anchor.getBoundingClientRect()
    const box = `${rect.left},${rect.top},${rect.width},${rect.height}`
    if (box !== lastAnchorBox) {
      lastAnchorBox = box
      stableFrames = 0
      update()
    } else {
      stableFrames = stableFrames + 1
    }

    const settled = stableFrames >= SETTLE_STABLE_FRAMES || Date.now() - settleStart > SETTLE_MAX_MS
    if (settled === false) {
      settleFrame = window.requestAnimationFrame(followWhileSettling)
    }
    return
  }

  if (useTopLayer === true) {
    showInTopLayer(floating)
  }

  const record = { floating: floating, anchor: anchor }
  openFloats.add(record)
  ensureKeyListeners()

  update()
  const firstRect = anchor.getBoundingClientRect()
  lastAnchorBox = `${firstRect.left},${firstRect.top},${firstRect.width},${firstRect.height}`
  settleFrame = window.requestAnimationFrame(followWhileSettling)

  window.addEventListener("scroll", scheduleUpdate, true)
  window.addEventListener("resize", scheduleUpdate)

  let observer = null
  if (typeof ResizeObserver === "function") {
    observer = new ResizeObserver(update)
    observer.observe(anchor)
    observer.observe(floating)
  }

  const dispose = () => {
    disposed = true
    openFloats.delete(record)
    window.removeEventListener("scroll", scheduleUpdate, true)
    window.removeEventListener("resize", scheduleUpdate)
    if (frame !== null) {
      window.cancelAnimationFrame(frame)
      frame = null
    }
    if (settleFrame !== null) {
      window.cancelAnimationFrame(settleFrame)
      settleFrame = null
    }
    if (observer !== null) {
      observer.disconnect()
    }
    if (useTopLayer === true) {
      removeFromTopLayer(floating)
    }
  }

  return dispose
}

/* ------------------------------------------------------------------------
 * Layer stack
 * ------------------------------------------------------------------------ */

/* Open layers, oldest first. The last entry is the topmost layer. */
const layerStack = [];
const layerListeners = [];

/* Escape key events a layer has already acted on. */
const claimedEscapes = new WeakSet();

/* Escape key event -> the open popups whose owner component saw the key. */
const popupEscapes = new WeakMap();

let keyListenersInstalled = false;

/*
 * The topmost layer at stack position `fromIndex` or above that closes on
 * Escape wherever focus is (it registered `onEscape`); null when there is
 * none. Layers without `onEscape` (a non-modal dialog or side panel) only
 * close while focus is inside them, so they are skipped here.
 */
function topEscapeLayer(fromIndex) {
  let found = null

  for (let index = layerStack.length - 1; index >= fromIndex; index = index - 1) {
    if (layerStack[index].onEscape !== null) {
      found = layerStack[index]
      break
    }
  }

  return found
}

/*
 * Before any component handler runs, note which open anchored popups the
 * Escape key was pressed in. By the time a surrounding dialog sees the key
 * the popup has usually closed itself, so the dialog could no longer tell.
 */
function onWindowKeydownCapture(event) {
  if (event.key !== "Escape" || openFloats.size === 0) {
    return
  }

  const path = event.composedPath()
  const owners = []

  for (const record of openFloats) {
    const root = record.floating.getRootNode()
    const host = root instanceof ShadowRoot ? root.host : null
    const involved = path.includes(record.floating) === true ||
      path.includes(record.anchor) === true ||
      (host !== null && path.includes(host) === true)
    if (involved === true) {
      owners.push(record.floating)
    }
  }

  if (owners.length > 0) {
    popupEscapes.set(event, owners)
  }
  return
}

/*
 * Escape that no component handled (focus was outside every surface, or on
 * a surface that is not the topmost layer): the topmost layer takes it.
 */
function onWindowKeydown(event) {
  if (event.key !== "Escape" || layerStack.length === 0) {
    return
  }

  const handled = event.defaultPrevented === true ||
    claimedEscapes.has(event) === true ||
    popupEscapes.has(event) === true
  if (handled === true) {
    return
  }

  const top = topEscapeLayer(0)
  if (top !== null) {
    claimedEscapes.add(event)
    event.preventDefault()
    top.onEscape(event)
  }
  return
}

function ensureKeyListeners() {
  if (keyListenersInstalled === false) {
    keyListenersInstalled = true
    window.addEventListener("keydown", onWindowKeydownCapture, true)
    window.addEventListener("keydown", onWindowKeydown)
  }
  return
}

function notifyLayerListeners() {
  rehomeLiveRegions()

  const listeners = layerListeners.slice()
  for (let index = 0; index < listeners.length; index = index + 1) {
    listeners[index]()
  }
  return
}

/*
 * Register an open surface.
 *
 * options:
 *   surface   -- the element that holds the layer's content.
 *   modal     -- true when everything outside the surface is unavailable.
 *   onEscape  -- called when Escape reaches this layer while focus is not
 *                inside it (the layer's own key handler covers the rest).
 *                Leave it out for a surface that sits beside the page and
 *                should close on Escape only while focus is inside it.
 *
 * Returns the layer record; pass it to `removeLayer` when the surface
 * closes and to `claimEscape` from the surface's key handler.
 */
export function pushLayer(options) {
  const opts = options || {}
  const layer = {
    surface: opts.surface || null,
    modal: opts.modal === true,
    onEscape: typeof opts.onEscape === "function" ? opts.onEscape : null
  }

  layerStack.push(layer)
  ensureKeyListeners()
  notifyLayerListeners()
  return layer
}

export function removeLayer(layer) {
  const index = layerStack.indexOf(layer)
  if (index >= 0) {
    layerStack.splice(index, 1)
    notifyLayerListeners()
  }
  return
}

/* The surface of the topmost modal layer, or null when no modal is open. */
export function topModalSurface() {
  let surface = null

  for (let index = layerStack.length - 1; index >= 0; index = index - 1) {
    const layer = layerStack[index]
    if (layer.modal === true && layer.surface !== null && layer.surface.isConnected === true) {
      surface = layer.surface
      break
    }
  }

  return surface
}

/* True while at least one modal layer is open. */
export function hasModalLayer() {
  const open = topModalSurface() !== null
  return open
}

/*
 * Call `listener` whenever a layer opens or closes. Returns a function that
 * removes the listener again.
 */
export function onLayerChange(listener) {
  layerListeners.push(listener)
  const unsubscribe = () => {
    const index = layerListeners.indexOf(listener)
    if (index >= 0) {
      layerListeners.splice(index, 1)
    }
  }
  return unsubscribe
}

/*
 * Ask whether `layer` may act on this Escape key press. Each press closes
 * exactly one thing, innermost first, so the answer is no when:
 *
 *   - another layer already acted on it, or a component inside called
 *     preventDefault() to say it handled the key;
 *   - the key was pressed in an anchored popup (select, combobox, menu,
 *     date picker...) that is open inside this layer -- the popup closes;
 *   - a layer above `layer` closes on Escape -- that one is asked to close
 *     instead, right here.
 *
 * Whatever the answer, the event has been dealt with once this returns: the
 * caller may call preventDefault() on it unconditionally.
 */
export function claimEscape(event, layer) {
  let granted = true

  if (event.defaultPrevented === true || claimedEscapes.has(event) === true) {
    granted = false
  }

  if (granted === true) {
    const popups = popupEscapes.get(event) || []
    const surface = layer !== undefined && layer !== null ? layer.surface : null

    for (let index = 0; index < popups.length; index = index + 1) {
      const popup = popups[index]
      const isOwnSurface = popup === surface
      const isInside = surface === null || flatContains(surface, popup) === true
      if (isOwnSurface === false && isInside === true) {
        granted = false
        break
      }
    }
  }

  if (granted === true && layer !== undefined && layer !== null) {
    const position = layerStack.indexOf(layer)
    const above = position >= 0 ? topEscapeLayer(position + 1) : null
    if (above !== null) {
      granted = false
      claimedEscapes.add(event)
      above.onEscape(event)
    }
  }

  if (granted === true) {
    claimedEscapes.add(event)
  }

  return granted
}

/* ------------------------------------------------------------------------
 * Live regions under a modal layer
 * ------------------------------------------------------------------------ */

/*
 * A modal surface makes the rest of the document inert, and inert content
 * is not exposed to assistive technology -- including the body-level live
 * regions of core/announcer.js, so `announce()` would be silent while a
 * dialog is open. While a modal layer is open the live regions are moved
 * inside its surface; they return to <body> when the last modal closes.
 */
const LIVE_REGION_SELECTOR = ".mj-live-region";

const movedLiveRegions = [];
let liveRegionObserver = null;

function rehomeLiveRegions() {
  if (typeof document === "undefined" || document.body === null) {
    return
  }

  const surface = topModalSurface()

  if (surface !== null) {
    const atBody = Array.from(document.body.querySelectorAll(`:scope > ${LIVE_REGION_SELECTOR}`))
    for (let index = 0; index < atBody.length; index = index + 1) {
      if (movedLiveRegions.includes(atBody[index]) === false) {
        movedLiveRegions.push(atBody[index])
      }
    }

    for (let index = 0; index < movedLiveRegions.length; index = index + 1) {
      const region = movedLiveRegions[index]
      if (region.parentNode !== surface) {
        surface.appendChild(region)
      }
    }

    /* The announcer creates its regions on first use, possibly after this. */
    if (liveRegionObserver === null && typeof MutationObserver === "function") {
      liveRegionObserver = new MutationObserver(() => {
        const added = document.body.querySelector(`:scope > ${LIVE_REGION_SELECTOR}`)
        if (added !== null) {
          rehomeLiveRegions()
        }
      })
      liveRegionObserver.observe(document.body, { childList: true })
    }
  } else {
    if (liveRegionObserver !== null) {
      liveRegionObserver.disconnect()
      liveRegionObserver = null
    }

    while (movedLiveRegions.length > 0) {
      const region = movedLiveRegions.pop()
      if (region.parentNode !== document.body) {
        document.body.appendChild(region)
      }
    }
  }

  return
}

export { PLACEMENTS };
