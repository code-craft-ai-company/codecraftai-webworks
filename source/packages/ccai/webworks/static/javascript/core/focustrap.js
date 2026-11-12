/*
 * focustrap.js
 *
 * Focus management utilities shared by overlays and composite widgets:
 *   - flatParent / flatContains: ancestry in the flat tree (through slots and
 *     shadow roots), which is what focus, inertness and events follow.
 *   - getFocusable: ordered list of tabbable elements in a root.
 *   - trapFocus: confine Tab focus within a container; restore on release.
 *   - RovingTabindex: single-tab-stop keyboard navigation for composites
 *     (toolbars, radio groups, menus, listboxes, tabs).
 */

const FOCUSABLE_SELECTOR = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled]):not([type=hidden])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  "[tabindex]:not([tabindex='-1'])",
  "[contenteditable]:not([contenteditable='false'])",
  "audio[controls]",
  "video[controls]",
  "details>summary:first-of-type"
].join(",");

/*
 * Contained traps that are currently active, innermost last. Only the last
 * one pulls stray focus back, so a modal opened from inside another modal
 * does not fight the one beneath it.
 */
const containedTraps = [];

/*
 * The parent of `node` in the flat tree: the <slot> a node is assigned to,
 * the host of the shadow root a node sits directly in, and the DOM parent
 * otherwise. Returns null above the document element.
 */
export function flatParent(node) {
  let parent = null

  if (node !== null && node !== undefined) {
    const slot = node.assignedSlot
    if (slot !== null && slot !== undefined) {
      parent = slot
    } else if (node.parentNode instanceof ShadowRoot) {
      parent = node.parentNode.host
    } else if (node.parentNode instanceof Element) {
      parent = node.parentNode
    }
  }

  return parent
}

/*
 * True when `node` is `container` or one of its flat-tree descendants, i.e.
 * the node is rendered inside the container even when it lives in another
 * shadow root or is projected through a slot.
 */
export function flatContains(container, node) {
  let contained = false
  let current = node

  while (current !== null && current !== undefined) {
    if (current === container) {
      contained = true
      break
    }
    current = flatParent(current)
  }

  return contained
}

/*
 * The element children of `node` in the flat tree: a <slot>'s assigned
 * elements (or its fallback content when nothing is assigned), a shadow
 * host's shadow root content, and plain children otherwise.
 */
function flatChildren(node) {
  if (node instanceof HTMLSlotElement) {
    const assigned = node.assignedElements({ flatten: true })
    if (assigned.length > 0) {
      return assigned
    }
    return Array.from(node.children)
  }
  if (node instanceof Element && node.shadowRoot !== null && node.shadowRoot !== undefined) {
    return Array.from(node.shadowRoot.children)
  }
  return Array.from(node.children)
}

/*
 * True when the element has a layout box and is not hidden with
 * `visibility`. A box alone is not enough: a closed popup that keeps its box
 * under `visibility: hidden` cannot take focus.
 */
function isVisible(element) {
  let visible = element.offsetParent !== null || element.getClientRects().length > 0

  if (visible === true) {
    const style = window.getComputedStyle(element)
    visible = style.visibility === "visible"
  }

  return visible
}

/*
 * Only one radio button of a group is a tab stop: the checked one, or the
 * first enabled one when nothing in the group is checked.
 */
function isRadioTabStop(radio) {
  let tabStop = true

  if (radio.checked === false && radio.name !== "") {
    const scope = radio.form !== null ? radio.form : radio.getRootNode()
    const radios = Array.from(scope.querySelectorAll("input[type='radio']"))
    const group = radios.filter((candidate) => {
      const sameGroup = candidate.name === radio.name && candidate.form === radio.form
      return sameGroup === true && candidate.disabled === false
    })

    const checked = group.find((candidate) => candidate.checked === true)
    if (checked !== undefined) {
      tabStop = false
    } else {
      tabStop = group[0] === radio
    }
  }

  return tabStop
}

function isTabbable(element) {
  let tabbable = element.matches(FOCUSABLE_SELECTOR) === true && element.tabIndex >= 0

  if (tabbable === true) {
    tabbable = isVisible(element)
  }

  if (tabbable === true && element instanceof HTMLInputElement && element.type === "radio") {
    tabbable = isRadioTabStop(element)
  }

  return tabbable
}

/*
 * Return the tabbable elements under `root` (an element, shadow root, or
 * document) in flat-tree order: open shadow roots are entered and slotted
 * content is visited where its slot sits, so a trap on a shadow container
 * that only holds <slot>s still finds the light-DOM controls projected into
 * it. Skipped: elements taken out of the tab order (tabindex="-1", e.g. the
 * inactive items of a roving-tabindex group), elements that are not rendered
 * or are hidden with `visibility`, everything inside an `inert` subtree or a
 * closed <details>, and the radio buttons of a group that are not its tab
 * stop.
 */
export function getFocusable(root) {
  const results = []

  const visit = (node) => {
    const children = flatChildren(node)
    for (let index = 0; index < children.length; index = index + 1) {
      const child = children[index]

      if (child.inert === true) {
        continue
      }

      if (isTabbable(child) === true) {
        results.push(child)
      }

      if (child instanceof HTMLDetailsElement && child.open === false) {
        /* Only the summary of a closed <details> can be reached. */
        const summary = child.querySelector(":scope > summary")
        if (summary !== null && summary.inert === false) {
          if (isTabbable(summary) === true) {
            results.push(summary)
          }
          visit(summary)
        }
        continue
      }

      visit(child)
    }
  }

  visit(root)
  return results
}

/*
 * The element that really has focus, following focus down through open
 * shadow roots (document.activeElement stops at the outermost shadow host).
 */
export function deepActiveElement() {
  let active = document.activeElement
  while (active !== null && active.shadowRoot !== null && active.shadowRoot !== undefined && active.shadowRoot.activeElement !== null) {
    active = active.shadowRoot.activeElement
  }
  return active
}

/*
 * Trap Tab/Shift+Tab focus within `container`. Moves initial focus to the
 * first focusable element (or `initial` when supplied). Returns a dispose
 * function that releases the trap and restores focus to the previously
 * focused element.
 *
 * options:
 *   contain  -- true for a modal surface. Besides wrapping Tab inside the
 *               container, focus that ends up outside it (the focused node
 *               was removed, a click landed on the backdrop, script focused
 *               something else) is brought back: on the next Tab, and as
 *               soon as another element outside the container takes focus.
 *               Leave it off for non-modal popups, where clicking elsewhere
 *               on the page must be able to move focus away.
 */
export function trapFocus(container, initial, options) {
  const opts = options || {}
  const contain = opts.contain === true
  const previouslyFocused = deepActiveElement()

  const trap = { container: container }
  let lastFocusedInside = null

  const isInnermostTrap = () => {
    const innermost = containedTraps[containedTraps.length - 1] === trap
    return innermost
  }

  const focusEdge = (backwards) => {
    const focusable = getFocusable(container)
    let target = container
    if (focusable.length > 0) {
      target = backwards === true ? focusable[focusable.length - 1] : focusable[0]
    }
    if (typeof target.focus === "function") {
      target.focus()
    }
    return
  }

  const onKeydown = (event) => {
    if (event.key !== "Tab") {
      return
    }

    const focusable = getFocusable(container)
    if (focusable.length === 0) {
      event.preventDefault()
      return
    }

    const first = focusable[0]
    const last = focusable[focusable.length - 1]
    const active = deepActiveElement()

    if (focusable.includes(active) === false) {
      // Focus sits on something outside the tab sequence (a roving item
      // with tabindex="-1", a plain focused container): wrap into the
      // sequence instead of letting the browser leave the container.
      event.preventDefault()
      if (event.shiftKey === true) {
        last.focus()
      } else {
        first.focus()
      }
    } else if (event.shiftKey === true && active === first) {
      event.preventDefault()
      last.focus()
    } else if (event.shiftKey === false && active === last) {
      event.preventDefault()
      first.focus()
    }
    return
  }

  /*
   * Tab pressed while focus is not inside the container (it fell back to
   * <body>): the container's own listener never sees the key, so the trap
   * catches it on the document and re-enters the container.
   */
  const onDocumentKeydown = (event) => {
    if (event.key !== "Tab" || isInnermostTrap() === false) {
      return
    }

    const active = deepActiveElement()
    if (active !== null && flatContains(container, active) === true) {
      return
    }

    event.preventDefault()
    focusEdge(event.shiftKey === true)
    return
  }

  /* Another element outside the container took focus: bring it back. */
  const onDocumentFocusin = (event) => {
    if (isInnermostTrap() === false) {
      return
    }

    const path = event.composedPath()
    const target = path.length > 0 ? path[0] : event.target

    if (flatContains(container, target) === true) {
      lastFocusedInside = target
      return
    }

    const canReturn = lastFocusedInside !== null &&
      lastFocusedInside.isConnected === true &&
      flatContains(container, lastFocusedInside) === true

    if (canReturn === true) {
      lastFocusedInside.focus()
    } else {
      focusEdge(false)
    }
    return
  }

  container.addEventListener("keydown", onKeydown)

  if (contain === true) {
    containedTraps.push(trap)
    document.addEventListener("keydown", onDocumentKeydown, true)
    document.addEventListener("focusin", onDocumentFocusin, true)
  }

  const target = initial || getFocusable(container)[0] || container
  if (target !== null && typeof target.focus === "function") {
    target.focus()
  }

  /*
   * Release the trap. Focus returns to the element focused before the trap
   * was set unless `options.restoreFocus` is false (used when the container
   * stops being modal without closing, e.g. a drawer that becomes a static
   * sidebar, or when the caller restores focus itself after it has released
   * the inert background).
   */
  const dispose = (disposeOptions) => {
    container.removeEventListener("keydown", onKeydown)

    if (contain === true) {
      document.removeEventListener("keydown", onDocumentKeydown, true)
      document.removeEventListener("focusin", onDocumentFocusin, true)
      const position = containedTraps.indexOf(trap)
      if (position >= 0) {
        containedTraps.splice(position, 1)
      }
    }

    const restore = disposeOptions === undefined || disposeOptions === null || disposeOptions.restoreFocus !== false
    if (restore === true && previouslyFocused !== null && typeof previouslyFocused.focus === "function") {
      previouslyFocused.focus()
    }
  }

  return dispose
}

/*
 * Roving tabindex controller. Keeps exactly one item in the tab order; arrow
 * keys move the active item. Used by composite widgets per the WAI-ARIA APG.
 *
 * options:
 *   items         -- the elements that take part.
 *   orientation   -- "horizontal" (default) or "vertical".
 *   wrap          -- false to stop at the ends (default: wrap around).
 *   skipDisabled  -- false to let arrow keys land on disabled items
 *                    (default: disabled and aria-disabled items are skipped).
 *
 * While attached, the controller follows focus: an item focused with the
 * pointer or from script becomes the tab stop and the origin of the next
 * arrow key. Horizontal arrow keys follow the reading direction, so under
 * `dir="rtl"` ArrowLeft moves to the next item.
 */
export class RovingTabindex {
  constructor(options) {
    const opts = options || {}
    this.items = opts.items || []
    this.orientation = opts.orientation || "horizontal"
    this.wrap = opts.wrap !== false
    this.skipDisabled = opts.skipDisabled !== false
    this.index = 0
    this._container = null
    this._onKeydown = this._handleKeydown.bind(this)
    this._onFocusin = this._handleFocusin.bind(this)
  }

  setItems(items) {
    this.items = items
    if (this.index >= items.length) {
      this.index = items.length > 0 ? items.length - 1 : 0
    }

    /* The tab stop must be an item the user can actually land on. */
    if (items.length > 0 && this._isDisabled(items[this.index]) === true) {
      const firstEnabled = this._edgeIndex(false)
      if (firstEnabled >= 0) {
        this.index = firstEnabled
      }
    }

    this._sync()
    return
  }

  _isDisabled(item) {
    let disabled = false
    if (this.skipDisabled === true && item !== undefined && item !== null) {
      disabled = item.disabled === true || item.getAttribute("aria-disabled") === "true"
    }
    return disabled
  }

  /* Index of the first (or, with `fromEnd`, the last) enabled item; -1 if none. */
  _edgeIndex(fromEnd) {
    const count = this.items.length
    let found = -1

    for (let offset = 0; offset < count; offset = offset + 1) {
      const position = fromEnd === true ? count - 1 - offset : offset
      if (this._isDisabled(this.items[position]) === false) {
        found = position
        break
      }
    }

    return found
  }

  _sync() {
    for (let position = 0; position < this.items.length; position = position + 1) {
      const item = this.items[position]
      const isActive = position === this.index
      item.tabIndex = isActive === true ? 0 : -1
    }
    return
  }

  focus(index) {
    if (index < 0 || index >= this.items.length) {
      return
    }
    this.index = index
    this._sync()
    this.items[this.index].focus()
    return
  }

  _step(delta) {
    const count = this.items.length
    let next = this.index
    let found = -1

    for (let attempt = 0; attempt < count; attempt = attempt + 1) {
      next = next + delta

      if (next < 0) {
        if (this.wrap === false) {
          break
        }
        next = count - 1
      }
      if (next >= count) {
        if (this.wrap === false) {
          break
        }
        next = 0
      }

      if (this._isDisabled(this.items[next]) === false) {
        found = next
        break
      }
    }

    if (found >= 0) {
      this.focus(found)
    }
    return
  }

  _isRtl() {
    let reference = this._container
    if (reference === null && this.items.length > 0) {
      reference = this.items[0]
    }

    let rtl = false
    if (reference !== null && reference !== undefined) {
      rtl = window.getComputedStyle(reference).direction === "rtl"
    }
    return rtl
  }

  _handleKeydown(event) {
    const horizontal = this.orientation === "horizontal"
    let nextKey = horizontal === true ? "ArrowRight" : "ArrowDown"
    let prevKey = horizontal === true ? "ArrowLeft" : "ArrowUp"

    if (horizontal === true && this._isRtl() === true) {
      nextKey = "ArrowLeft"
      prevKey = "ArrowRight"
    }

    if (event.key === nextKey) {
      event.preventDefault()
      this._step(1)
    } else if (event.key === prevKey) {
      event.preventDefault()
      this._step(-1)
    } else if (event.key === "Home") {
      event.preventDefault()
      const first = this._edgeIndex(false)
      if (first >= 0) {
        this.focus(first)
      }
    } else if (event.key === "End") {
      event.preventDefault()
      const last = this._edgeIndex(true)
      if (last >= 0) {
        this.focus(last)
      }
    }
    return
  }

  /*
   * An item took focus by some other route than the arrow keys (a click, a
   * Tab landing, script): make it the tab stop so the next arrow key starts
   * from where the user is.
   */
  _handleFocusin(event) {
    const position = this.items.indexOf(event.target)
    if (position >= 0 && position !== this.index) {
      this.index = position
      this._sync()
    }
    return
  }

  /* Attach keyboard handling to a container element. Returns a disposer. */
  attach(container) {
    this._container = container
    container.addEventListener("keydown", this._onKeydown)
    container.addEventListener("focusin", this._onFocusin)
    this._sync()
    const dispose = () => {
      container.removeEventListener("keydown", this._onKeydown)
      container.removeEventListener("focusin", this._onFocusin)
    }
    return dispose
  }
}
