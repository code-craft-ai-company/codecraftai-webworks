/*
 * focustrap.js
 *
 * Focus management utilities shared by overlays and composite widgets:
 *   - getFocusable: ordered list of focusable elements in a root.
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

function isVisible(element) {
  const visible = element.offsetParent !== null || element.getClientRects().length > 0
  return visible
}

/*
 * Return the tabbable elements under `root` (an element, shadow root, or
 * document) in flat-tree order: open shadow roots are entered and slotted
 * content is visited where its slot sits, so a trap on a shadow container
 * that only holds <slot>s still finds the light-DOM controls projected into
 * it. Elements taken out of the tab order (tabindex="-1", e.g. the inactive
 * items of a roving-tabindex group) and invisible elements are skipped.
 */
export function getFocusable(root) {
  const results = []

  const visit = (node) => {
    const children = flatChildren(node)
    for (let index = 0; index < children.length; index = index + 1) {
      const child = children[index]
      if (child.matches(FOCUSABLE_SELECTOR) === true && child.tabIndex >= 0 && isVisible(child) === true) {
        results.push(child)
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
 */
export function trapFocus(container, initial) {
  const previouslyFocused = deepActiveElement()

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

  container.addEventListener("keydown", onKeydown)

  const target = initial || getFocusable(container)[0] || container
  if (target !== null && typeof target.focus === "function") {
    target.focus()
  }

  /*
   * Release the trap. Focus returns to the element focused before the trap
   * was set unless `options.restoreFocus` is false (used when the container
   * stops being modal without closing, e.g. a drawer that becomes a static
   * sidebar).
   */
  const dispose = (options) => {
    container.removeEventListener("keydown", onKeydown)
    const restore = options === undefined || options === null || options.restoreFocus !== false
    if (restore === true && previouslyFocused !== null && typeof previouslyFocused.focus === "function") {
      previouslyFocused.focus()
    }
  }

  return dispose
}

/*
 * Roving tabindex controller. Keeps exactly one item in the tab order; arrow
 * keys move the active item. Used by composite widgets per the WAI-ARIA APG.
 */
export class RovingTabindex {
  constructor(options) {
    const opts = options || {}
    this.items = opts.items || []
    this.orientation = opts.orientation || "horizontal"
    this.wrap = opts.wrap !== false
    this.index = 0
    this._onKeydown = this._handleKeydown.bind(this)
  }

  setItems(items) {
    this.items = items
    if (this.index >= items.length) {
      this.index = items.length > 0 ? items.length - 1 : 0
    }
    this._sync()
    return
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
    let next = this.index + delta
    const count = this.items.length

    if (next < 0) {
      next = this.wrap === true ? count - 1 : 0
    }
    if (next >= count) {
      next = this.wrap === true ? 0 : count - 1
    }

    this.focus(next)
    return
  }

  _handleKeydown(event) {
    const horizontal = this.orientation === "horizontal"
    const nextKey = horizontal === true ? "ArrowRight" : "ArrowDown"
    const prevKey = horizontal === true ? "ArrowLeft" : "ArrowUp"

    if (event.key === nextKey) {
      event.preventDefault()
      this._step(1)
    } else if (event.key === prevKey) {
      event.preventDefault()
      this._step(-1)
    } else if (event.key === "Home") {
      event.preventDefault()
      this.focus(0)
    } else if (event.key === "End") {
      event.preventDefault()
      this.focus(this.items.length - 1)
    }
    return
  }

  /* Attach keyboard handling to a container element. Returns a disposer. */
  attach(container) {
    container.addEventListener("keydown", this._onKeydown)
    this._sync()
    const dispose = () => {
      container.removeEventListener("keydown", this._onKeydown)
    }
    return dispose
  }
}
