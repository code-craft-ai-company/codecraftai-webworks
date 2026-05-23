/*
 * contextmenu.js
 *
 * A lightweight, accessible popup context-menu used by the MjElement base
 * class so every mj-* component can carry a right-click / Shift+F10 context
 * menu. The menu is a plain light-DOM element appended to <body>; it is not a
 * custom element, so the base class has no dependency on any component.
 *
 *   openContextMenu(items, x, y, { onSelect, label })
 *   closeContextMenu()
 *
 * An item is { label, value, disabled } or { separator: true }. Only one
 * context menu is open at a time.
 */

const MENU_STYLE_ID = "mj-context-menu-styles";

const MENU_CSS = `
.mj-ctx-menu {
  position: fixed; margin: 0; min-width: 11rem; max-width: 22rem;
  padding: var(--mj-space-1, 0.25rem);
  z-index: var(--mj-layer-popover, 1200);
  background: var(--mj-surface-raised, var(--mj-surface, #ffffff));
  color: var(--mj-text, #14181f);
  border: 1px solid var(--mj-border, #e0e3e9);
  border-radius: var(--mj-radius-md, 0.5rem);
  box-shadow: var(--mj-elevation-3, 0 8px 24px rgba(20, 24, 31, 0.18));
  font-family: var(--mj-font-sans, system-ui, sans-serif);
  font-size: var(--mj-font-size-sm, 0.875rem);
}
.mj-ctx-item {
  display: flex; align-items: center; gap: var(--mj-space-2, 0.5rem);
  padding: var(--mj-space-2, 0.5rem) var(--mj-space-3, 0.75rem);
  border-radius: var(--mj-radius-sm, 0.25rem);
  cursor: pointer; user-select: none; white-space: nowrap;
}
.mj-ctx-item:focus { outline: none; }
.mj-ctx-item[aria-disabled="true"] { opacity: 0.5; cursor: not-allowed; }
.mj-ctx-item.mj-ctx-active:not([aria-disabled="true"]) {
  background: var(--mj-accent, #2563eb);
  color: var(--mj-text-on-accent, #ffffff);
}
.mj-ctx-sep {
  height: 1px; margin: var(--mj-space-1, 0.25rem) 0;
  background: var(--mj-border, #e0e3e9);
}
@media (forced-colors: active) {
  .mj-ctx-item.mj-ctx-active:not([aria-disabled="true"]) {
    background: Highlight; color: HighlightText;
  }
}
`;

/* The single currently-open menu, or null. */
let activeMenu = null;


function ensureStyles() {
  /*
   * Inject the shared menu stylesheet into the document head once.
   */
  const existing = document.getElementById(MENU_STYLE_ID)
  if (existing !== null) {
    return
  }

  const styleEl = document.createElement("style")
  styleEl.id = MENU_STYLE_ID
  styleEl.textContent = MENU_CSS
  document.head.appendChild(styleEl)
  return
}


export function closeContextMenu() {
  /*
   * Close the currently-open context menu, if any.
   */
  if (activeMenu !== null) {
    const menu = activeMenu
    activeMenu = null
    menu.dispose()
  }
  return
}


export function openContextMenu(items, anchorX, anchorY, options) {
  /*
   * Open a context menu of `items` at the viewport coordinate
   * (anchorX, anchorY). `options.onSelect(item)` is invoked when an enabled
   * item is chosen; `options.label` sets the menu's accessible name.
   *
   * Returns an object with a `close()` method.
   */
  closeContextMenu()
  ensureStyles()

  const opts = options || {}
  let onSelect = function () { return }
  if (typeof opts.onSelect === "function") {
    onSelect = opts.onSelect
  }

  const itemList = Array.isArray(items) ? items : []

  const menu = document.createElement("div")
  menu.className = "mj-ctx-menu"
  menu.setAttribute("role", "menu")
  if (opts.label !== undefined && opts.label !== null) {
    menu.setAttribute("aria-label", opts.label)
  }

  const itemEls = []

  for (let index = 0; index < itemList.length; index = index + 1) {
    const item = itemList[index]

    if (item !== null && item.separator === true) {
      const separator = document.createElement("div")
      separator.className = "mj-ctx-sep"
      separator.setAttribute("role", "separator")
      menu.appendChild(separator)
      continue
    }

    const itemEl = document.createElement("div")
    itemEl.className = "mj-ctx-item"
    itemEl.setAttribute("role", "menuitem")
    itemEl.setAttribute("tabindex", "-1")

    let label = ""
    if (item !== null && item.label !== undefined) {
      label = String(item.label)
    } else if (item !== null && item.value !== undefined) {
      label = String(item.value)
    }
    itemEl.textContent = label

    const disabled = item !== null && item.disabled === true
    if (disabled === true) {
      itemEl.setAttribute("aria-disabled", "true")
    }

    itemEl._mjItem = item
    itemEl._mjDisabled = disabled
    menu.appendChild(itemEl)
    itemEls.push(itemEl)
  }

  document.body.appendChild(menu)

  /* Position with viewport clamping so the menu is always fully visible. */
  const rect = menu.getBoundingClientRect()
  let posX = anchorX
  let posY = anchorY
  const margin = 4

  if (posX + rect.width > window.innerWidth) {
    posX = window.innerWidth - rect.width - margin
  }
  if (posY + rect.height > window.innerHeight) {
    posY = window.innerHeight - rect.height - margin
  }
  if (posX < margin) {
    posX = margin
  }
  if (posY < margin) {
    posY = margin
  }
  menu.style.left = `${posX}px`
  menu.style.top = `${posY}px`

  let activeIndex = -1

  const setActive = (nextIndex) => {
    if (activeIndex >= 0 && activeIndex < itemEls.length) {
      itemEls[activeIndex].classList.remove("mj-ctx-active")
    }
    activeIndex = nextIndex
    if (activeIndex >= 0 && activeIndex < itemEls.length) {
      const activeEl = itemEls[activeIndex]
      activeEl.classList.add("mj-ctx-active")
      activeEl.focus()
    }
    return
  }

  const moveActive = (delta) => {
    const count = itemEls.length
    if (count === 0) {
      return
    }
    let candidate = activeIndex
    for (let step = 0; step < count; step = step + 1) {
      candidate = (candidate + delta + count) % count
      if (itemEls[candidate]._mjDisabled === false) {
        break
      }
    }
    setActive(candidate)
    return
  }

  const choose = (itemEl) => {
    if (itemEl._mjDisabled === true) {
      return
    }
    const chosen = itemEl._mjItem
    closeContextMenu()
    onSelect(chosen)
    return
  }

  const onClick = (event) => {
    const itemEl = event.target.closest(".mj-ctx-item")
    if (itemEl !== null && menu.contains(itemEl) === true) {
      choose(itemEl)
    }
    return
  }

  const onKeydown = (event) => {
    if (event.key === "ArrowDown") {
      event.preventDefault()
      moveActive(1)
    } else if (event.key === "ArrowUp") {
      event.preventDefault()
      moveActive(-1)
    } else if (event.key === "Home") {
      event.preventDefault()
      activeIndex = itemEls.length - 1
      moveActive(1)
    } else if (event.key === "End") {
      event.preventDefault()
      activeIndex = 0
      moveActive(-1)
    } else if (event.key === "Escape") {
      event.preventDefault()
      closeContextMenu()
    } else if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      if (activeIndex >= 0) {
        choose(itemEls[activeIndex])
      }
    }
    return
  }

  const onOutsidePointer = (event) => {
    if (menu.contains(event.target) === false) {
      closeContextMenu()
    }
    return
  }

  const onDismiss = () => {
    closeContextMenu()
    return
  }

  menu.addEventListener("click", onClick)
  menu.addEventListener("keydown", onKeydown)
  window.addEventListener("scroll", onDismiss, true)
  window.addEventListener("resize", onDismiss)
  window.addEventListener("blur", onDismiss)

  /* Defer the outside-pointer listener so the opening event is not caught. */
  const armTimer = window.setTimeout(() => {
    document.addEventListener("pointerdown", onOutsidePointer, true)
  }, 0)

  const previousFocus = document.activeElement

  const dispose = () => {
    window.clearTimeout(armTimer)
    menu.removeEventListener("click", onClick)
    menu.removeEventListener("keydown", onKeydown)
    document.removeEventListener("pointerdown", onOutsidePointer, true)
    window.removeEventListener("scroll", onDismiss, true)
    window.removeEventListener("resize", onDismiss)
    window.removeEventListener("blur", onDismiss)
    if (menu.parentNode !== null) {
      menu.parentNode.removeChild(menu)
    }
    if (previousFocus !== null && typeof previousFocus.focus === "function") {
      previousFocus.focus()
    }
    return
  }

  activeMenu = { menu: menu, dispose: dispose }

  /* Move focus to the first enabled item. */
  moveActive(1)

  const handle = { close: closeContextMenu }
  return handle
}
