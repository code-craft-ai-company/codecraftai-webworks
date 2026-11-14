/*
 * contextmenu.js
 *
 * A lightweight, accessible popup context-menu used by the MjElement base
 * class so every mj-* component can carry a right-click / Shift+F10 context
 * menu. The menu is a plain element, not a custom element, so the base class
 * has no dependency on any component. It is appended to <body> -- or, while
 * a modal surface (dialog, drawer...) is open, inside that surface, because
 * everything outside a modal is inert -- and shown in the top layer.
 *
 *   openContextMenu(items, x, y, { onSelect, label })
 *   closeContextMenu()
 *
 * An item is { label, value, disabled } or { separator: true }. Only one
 * context menu is open at a time.
 */

import { deepActiveElement } from "./focustrap.js";
import { positionAtPoint, removeFromTopLayer, topModalSurface } from "./overlay.js";
import { t } from "./intl.js";

const MENU_STYLE_ID = "mj-context-menu-styles";

const MENU_CSS = `
.mj-ctx-menu {
  position: fixed; margin: 0; min-width: 11rem; max-width: 22rem;
  overflow-y: auto;
  box-sizing: border-box;
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

/* Characters typed within this window extend the type-ahead search. */
const TYPE_AHEAD_RESET_MS = 600;

/* The single currently-open menu, or null. */
let activeMenu = null;

/*
 * True from the moment a menu opens until the current task ends. One
 * `contextmenu` event travels through every nested component that carries a
 * menu; only the innermost one -- the first to ask -- may open its menu.
 */
let openedInThisTask = false;

/* Stylesheet adopted by shadow roots that host a menu. */
let menuSheet = null;


function ensureStyles(root) {
  /*
   * Make the menu stylesheet available in `root`: once in the document head
   * for a menu appended to <body>, or adopted by the shadow root of the
   * modal surface the menu is appended to.
   */
  if (root instanceof ShadowRoot) {
    if (menuSheet === null) {
      menuSheet = new CSSStyleSheet()
      menuSheet.replaceSync(MENU_CSS)
    }
    if (root.adoptedStyleSheets.includes(menuSheet) === false) {
      root.adoptedStyleSheets = [...root.adoptedStyleSheets, menuSheet]
    }
    return
  }

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
  const handle = { close: closeContextMenu }

  if (openedInThisTask === true && activeMenu !== null) {
    /*
     * The same event already opened the menu of a component nested inside
     * the caller. The inner menu stays; the outer request is dropped.
     */
    return handle
  }

  closeContextMenu()

  const opts = options || {}
  let onSelect = function () { return }
  if (typeof opts.onSelect === "function") {
    onSelect = opts.onSelect
  }

  const itemList = Array.isArray(items) ? items : []

  /* Captured before the menu takes focus, down through shadow roots. */
  const previousFocus = deepActiveElement()

  const menu = document.createElement("div")
  menu.className = "mj-ctx-menu"
  menu.setAttribute("role", "menu")
  menu.setAttribute("tabindex", "-1")

  /* Accessible name used when the caller supplies no `label`. */
  let menuLabel = t("mj.contextMenu.popupLabel")
  if (opts.label !== undefined && opts.label !== null && String(opts.label).length > 0) {
    menuLabel = String(opts.label)
  }
  menu.setAttribute("aria-label", menuLabel)

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
    itemEl._mjLabel = label.trim().toLowerCase()
    menu.appendChild(itemEl)
    itemEls.push(itemEl)
  }

  /*
   * Inside the topmost modal surface when one is open: content outside a
   * modal is inert, so a menu on <body> could be neither seen nor used.
   */
  const modalSurface = topModalSurface()
  const container = modalSurface !== null ? modalSurface : document.body
  ensureStyles(container.getRootNode())
  container.appendChild(menu)

  /*
   * In the top layer, at the pointer, kept fully inside the viewport; a menu
   * taller than the viewport scrolls.
   */
  positionAtPoint(menu, anchorX, anchorY, { padding: 4, constrain: true })

  let activeIndex = -1

  const setActive = (nextIndex, moveFocus) => {
    if (activeIndex >= 0 && activeIndex < itemEls.length) {
      itemEls[activeIndex].classList.remove("mj-ctx-active")
    }
    activeIndex = nextIndex
    if (activeIndex >= 0 && activeIndex < itemEls.length) {
      const activeEl = itemEls[activeIndex]
      activeEl.classList.add("mj-ctx-active")
      if (moveFocus !== false) {
        activeEl.focus()
      }
    }
    return
  }

  /*
   * The first enabled item found walking `delta` steps at a time from
   * `fromIndex` (exclusive), wrapping around; -1 when every item is disabled.
   */
  const findEnabled = (fromIndex, delta) => {
    const count = itemEls.length
    let found = -1
    let candidate = fromIndex

    for (let step = 0; step < count; step = step + 1) {
      candidate = (candidate + delta + count) % count
      if (itemEls[candidate]._mjDisabled === false) {
        found = candidate
        break
      }
    }

    return found
  }

  const moveActive = (delta) => {
    if (itemEls.length === 0) {
      return
    }
    const next = findEnabled(activeIndex, delta)
    if (next >= 0) {
      setActive(next)
    }
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

  /* The item under the pointer is the active one, as in a native menu. */
  const onPointerMove = (event) => {
    const itemEl = event.target.closest(".mj-ctx-item")
    if (itemEl === null || menu.contains(itemEl) === false) {
      return
    }
    const hovered = itemEls.indexOf(itemEl)
    if (hovered >= 0 && hovered !== activeIndex && itemEl._mjDisabled === false) {
      setActive(hovered)
    }
    return
  }

  let typeAheadText = ""
  let typeAheadTimer = null

  const typeAhead = (character) => {
    if (typeAheadTimer !== null) {
      window.clearTimeout(typeAheadTimer)
    }
    typeAheadText = typeAheadText + character.toLowerCase()
    typeAheadTimer = window.setTimeout(() => {
      typeAheadText = ""
      typeAheadTimer = null
    }, TYPE_AHEAD_RESET_MS)

    /* A repeated single letter cycles through the items starting with it. */
    const count = itemEls.length
    const start = typeAheadText.length === 1 ? activeIndex + 1 : Math.max(activeIndex, 0)
    for (let step = 0; step < count; step = step + 1) {
      const candidate = (start + step + count) % count
      const itemEl = itemEls[candidate]
      if (itemEl._mjDisabled === false && itemEl._mjLabel.startsWith(typeAheadText) === true) {
        setActive(candidate)
        break
      }
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
      const first = findEnabled(-1, 1)
      if (first >= 0) {
        setActive(first)
      }
    } else if (event.key === "End") {
      event.preventDefault()
      const last = findEnabled(itemEls.length, -1)
      if (last >= 0) {
        setActive(last)
      }
    } else if (event.key === "Escape") {
      /* Handled here: a dialog around the menu must not close as well. */
      event.preventDefault()
      event.stopPropagation()
      closeContextMenu()
    } else if (event.key === "Tab") {
      closeContextMenu()
    } else if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      if (activeIndex >= 0) {
        choose(itemEls[activeIndex])
      }
    } else if (event.key.length === 1 && event.ctrlKey === false && event.metaKey === false && event.altKey === false) {
      event.preventDefault()
      typeAhead(event.key)
    }
    return
  }

  const onOutsidePointer = (event) => {
    /* composedPath: the menu may sit inside a modal surface's shadow root. */
    if (event.composedPath().includes(menu) === false) {
      closeContextMenu()
    }
    return
  }

  const onDismiss = (event) => {
    /* Scrolling the menu's own overflow must not dismiss it. */
    if (event !== undefined && event.type === "scroll" && event.target === menu) {
      return
    }
    closeContextMenu()
    return
  }

  /*
   * A viewport resize keeps the menu open and inside the viewport, as the
   * anchored popups of core/overlay.js do. The viewport can change size
   * because of the menu itself -- an iframe that grows to fit its content,
   * a mobile browser bar or keyboard -- so closing here would dismiss the
   * menu the moment it opened.
   */
  let resizeFrame = null
  const onResize = () => {
    if (resizeFrame === null) {
      resizeFrame = window.requestAnimationFrame(() => {
        resizeFrame = null
        positionAtPoint(menu, anchorX, anchorY, { padding: 4, constrain: true, topLayer: false })
      })
    }
    return
  }

  menu.addEventListener("click", onClick)
  menu.addEventListener("pointermove", onPointerMove)
  menu.addEventListener("keydown", onKeydown)
  window.addEventListener("scroll", onDismiss, true)
  window.addEventListener("resize", onResize)
  window.addEventListener("blur", onDismiss)

  /* Defer the outside-pointer listener so the opening event is not caught. */
  const armTimer = window.setTimeout(() => {
    document.addEventListener("pointerdown", onOutsidePointer, true)
  }, 0)

  openedInThisTask = true
  window.setTimeout(() => {
    openedInThisTask = false
  }, 0)

  const dispose = () => {
    window.clearTimeout(armTimer)
    if (typeAheadTimer !== null) {
      window.clearTimeout(typeAheadTimer)
    }
    if (resizeFrame !== null) {
      window.cancelAnimationFrame(resizeFrame)
      resizeFrame = null
    }
    menu.removeEventListener("click", onClick)
    menu.removeEventListener("pointermove", onPointerMove)
    menu.removeEventListener("keydown", onKeydown)
    document.removeEventListener("pointerdown", onOutsidePointer, true)
    window.removeEventListener("scroll", onDismiss, true)
    window.removeEventListener("resize", onResize)
    window.removeEventListener("blur", onDismiss)

    /* Only pull focus back if it is still in the menu (or was lost with it). */
    const focusedNow = deepActiveElement()
    const focusInMenu = focusedNow === null || focusedNow === document.body || menu.contains(focusedNow) === true

    removeFromTopLayer(menu)
    if (menu.parentNode !== null) {
      menu.parentNode.removeChild(menu)
    }

    if (focusInMenu === true && previousFocus !== null && typeof previousFocus.focus === "function") {
      previousFocus.focus()
    }
    return
  }

  activeMenu = { menu: menu, dispose: dispose }

  /* Move focus to the first enabled item, or to the menu when there is none. */
  moveActive(1)
  if (activeIndex < 0) {
    menu.focus()
  }

  return handle
}
