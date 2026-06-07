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
  "audio[controls]",
  "video[controls]",
  "details>summary:first-of-type"
].join(",");

/*
 * Return focusable descendants of `root` in document order. Crosses into open
 * shadow roots so composed overlays trap correctly.
 */
export function getFocusable(root) {
  const results = []

  const visit = (node) => {
    const candidates = node.querySelectorAll(FOCUSABLE_SELECTOR)
    for (let index = 0; index < candidates.length; index = index + 1) {
      const candidate = candidates[index]
      const visible = candidate.offsetParent !== null || candidate.getClientRects().length > 0
      if (visible === true) {
        results.push(candidate)
      }
      if (candidate.shadowRoot !== null && candidate.shadowRoot !== undefined) {
        visit(candidate.shadowRoot)
      }
    }
  }

  visit(root)
  return results
}

/*
 * Trap Tab/Shift+Tab focus within `container`. Moves initial focus to the
 * first focusable element (or `initial` when supplied). Returns a dispose
 * function that releases the trap and restores focus to the previously
 * focused element.
 */
export function trapFocus(container, initial) {
  const previouslyFocused = document.activeElement

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
    const active = container.getRootNode().activeElement

    if (event.shiftKey === true && active === first) {
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

  const dispose = () => {
    container.removeEventListener("keydown", onKeydown)
    if (previouslyFocused !== null && typeof previouslyFocused.focus === "function") {
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
