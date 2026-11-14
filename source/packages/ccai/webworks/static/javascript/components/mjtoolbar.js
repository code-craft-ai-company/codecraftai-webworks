/*
 * mjtoolbar.js
 *
 * <mj-toolbar> -- strip of grouped controls implementing the WAI-ARIA APG
 * Toolbar pattern: one tab stop, arrow keys move between the items.
 *
 * Roving tabindex: exactly one item is in the tab order. For a custom
 * element item (<mj-button>, <mj-toggle-button>, ...) the tab stop is its
 * inner control, never the host, so Tab lands on something that Enter and
 * Space activate. Keys a control needs for itself (the caret keys of a text
 * field, the arrows of a select or slider) are left to the control.
 *
 * Overflow: in a horizontal toolbar the direct children that do not fit are
 * moved, as they are, into a popup opened by the "More actions" button. They
 * are reassigned to an internal slot rather than cloned, so every control
 * keeps its state, value and listeners. `mj-toolbar-overflow-change` fires
 * whenever the set of overflowed items changes.
 *
 * Variants: `action-bar` floats the toolbar and shows it only while `active`
 * is set. `ribbon` currently renders as a plain toolbar (the tabbed ribbon of
 * the spec is not implemented yet).
 *
 * Shift with an arrow, Home or End is never taken for moving between items:
 * in a text field it extends the selection.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { autoPosition } from "../core/overlay.js";
import { deepActiveElement } from "../core/focustrap.js";
import { t } from "../core/intl.js";

/* The slot a direct child is reassigned to while it is in the overflow popup. */
const OVERFLOW_SLOT = "mj-toolbar-overflow";

/* Elements that are toolbar items. `[data-toolbar-item]` marks anything else. */
const ITEM_SELECTOR = [
  "button",
  "a[href]",
  "input:not([type='hidden'])",
  "select",
  "textarea",
  "[tabindex]",
  "[data-toolbar-item]",
  "mj-button",
  "mj-toggle-button",
  "mj-menu-button",
  "mj-split-button",
  "mj-select",
  "mj-combobox",
  "mj-search-input",
  "mj-text-field",
  "mj-number-field",
  "mj-copy-button",
  "mj-download-button",
  "mj-share-button",
  "mj-favorite-button",
  "mj-upload-button",
  "mj-disclosure-button"
].join(",");

/* The control inside a custom element's shadow root that takes the tab stop. */
const INNER_FOCUSABLE_SELECTOR = "button, input:not([type='hidden']), select, textarea, a[href], [tabindex]";

/* Input types in which the horizontal arrows move a text caret. */
const TEXT_INPUT_TYPES = ["text", "search", "url", "tel", "email", "password"];

/* Input types that use every arrow key themselves. */
const ARROW_INPUT_TYPES = ["number", "range", "radio", "date", "time", "datetime-local", "month", "week"];

const STYLES = `
:host {
  display: block;
  position: relative;
}

.toolbar-root {
  display: flex;
  align-items: center;
  gap: var(--mj-toolbar-group-gap, var(--mj-space-3));
  min-block-size: var(--mj-toolbar-height, var(--mj-control-height-md));
  padding: 0 var(--mj-space-2);
  background: var(--mj-toolbar-bg, var(--mj-surface));
  border-block-end: 1px solid var(--mj-toolbar-border, var(--mj-border));
  overflow: hidden;
}

:host([orientation="vertical"]) .toolbar-root {
  flex-direction: column;
  align-items: stretch;
  min-block-size: unset;
  min-inline-size: var(--mj-toolbar-height, var(--mj-control-height-md));
  border-block-end: none;
  border-inline-end: 1px solid var(--mj-toolbar-border, var(--mj-border));
  padding: var(--mj-space-2) 0;
}

:host([disabled]) .toolbar-root {
  opacity: 0.55;
}

/* Centred without a physical offset, so it is centred in either direction. */
:host([variant="action-bar"]) .toolbar-root {
  position: absolute;
  inset-inline: 0;
  inline-size: fit-content;
  max-inline-size: 100%;
  margin-inline: auto;
  border-radius: var(--mj-radius-lg);
  box-shadow: var(--mj-elevation-3);
  border-block-end: none;
  transition: opacity var(--mj-motion-fast) var(--mj-motion-ease),
              translate var(--mj-motion-fast) var(--mj-motion-ease);
}

/*
 * An inactive action bar is taken out of the tab order and the accessibility
 * tree (visibility is inherited by the slotted controls), once it has faded.
 */
:host([variant="action-bar"]:not([active])) .toolbar-root {
  opacity: 0;
  translate: 0 var(--mj-space-2);
  visibility: hidden;
  transition: opacity var(--mj-motion-fast) var(--mj-motion-ease),
              translate var(--mj-motion-fast) var(--mj-motion-ease),
              visibility 0s linear var(--mj-motion-fast);
}

.slot-wrapper {
  display: contents;
}

::slotted(*) {
  flex-shrink: 0;
}

.overflow-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-inline-start: auto;
  min-inline-size: var(--mj-control-height-sm);
  min-block-size: var(--mj-control-height-sm);
  padding: 0 var(--mj-space-2);
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--mj-radius-sm);
  color: var(--mj-text);
  font: inherit;
  cursor: pointer;
}

.overflow-btn[hidden] { display: none; }

.overflow-btn:hover,
.overflow-btn[aria-expanded="true"] {
  background: var(--mj-bg-muted);
}

.overflow-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: calc(-1 * var(--mj-focus-ring-width));
}

.overflow-panel {
  position: fixed;
  z-index: var(--mj-layer-popover);
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: var(--mj-toolbar-gap, var(--mj-space-1));
  min-inline-size: 160px;
  max-block-size: calc(100vh - var(--mj-space-4));
  overflow-y: auto;
  padding: var(--mj-space-2);
  background: var(--mj-surface-raised);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-md);
  box-shadow: var(--mj-elevation-2);
}

.overflow-panel[hidden] { display: none; }
`;

/* True when `key` moves the caret (rather than leaving the field) in a text input. */
function caretNeedsKey(input, key) {
  let needed = true

  try {
    const start = input.selectionStart
    const end = input.selectionEnd
    if (start !== null && start === end) {
      if (key === "ArrowLeft" && start === 0) {
        needed = false
      } else if (key === "ArrowRight" && end === input.value.length) {
        needed = false
      }
    }
  } catch (error) {
    /* The input type has no selection API: assume the key is the field's. */
    needed = true
  }

  return needed
}

/*
 * True when `control` uses `key` for its own operation, in which case the
 * toolbar must not take it for moving between items (APG toolbar guidance).
 */
function controlNeedsKey(control, key) {
  let needed = false

  if (control instanceof Element) {
    const horizontal = key === "ArrowLeft" || key === "ArrowRight"
    const vertical = key === "ArrowUp" || key === "ArrowDown"
    const edge = key === "Home" || key === "End"
    const tag = control.localName
    const role = control.getAttribute("role")

    if (tag === "textarea" || control.isContentEditable === true) {
      needed = true
    } else if (tag === "select") {
      needed = vertical === true || edge === true
    } else if (tag === "input") {
      const type = (control.getAttribute("type") || "text").toLowerCase()
      if (TEXT_INPUT_TYPES.indexOf(type) >= 0) {
        if (horizontal === true) {
          needed = caretNeedsKey(control, key)
        } else if (edge === true) {
          needed = true
        }
      } else if (ARROW_INPUT_TYPES.indexOf(type) >= 0) {
        needed = true
      }
    } else if (role === "slider" || role === "spinbutton" || role === "textbox") {
      needed = true
    } else if (role === "combobox" || role === "listbox") {
      needed = vertical === true
    }
  }

  return needed
}

/* True when two lists hold the same elements in the same order. */
function sameElements(first, second) {
  let same = first.length === second.length
  for (let index = 0; index < first.length && same === true; index = index + 1) {
    if (first[index] !== second[index]) {
      same = false
    }
  }
  return same
}

export class MjToolbar extends MjElement {
  static tagName = "mj-toolbar";
  static styles = STYLES;
  static watched = [
    "variant", "label", "labelledby", "orientation", "active", "disabled",
    "overflow-button-label"
  ];

  constructor() {
    super()
    this._root = null
    this._slot = null
    this._overflowBtn = null
    this._overflowPanel = null

    this._resizeObserver = null
    this._mutationObserver = null
    this._positionDispose = null

    /*
     * The roving items in order: { element, target, inPanel }. `element` is
     * the item the author slotted, `target` the node that takes the tab stop
     * and focus (the inner control of a custom element), `inPanel` whether
     * the item currently sits in the overflow popup.
     */
    this._items = []
    this._activeElement = null

    /* Direct children (layout units) the toolbar was last laid out for. */
    this._units = []
    this._observedUnits = new WeakSet()
    this._overflowItems = []
    this._layoutQueued = false
    this._pendingDefinitions = {}

    this._toolbarId = nextId("mj-toolbar")
  }

  render() {
    const markup = `
      <div class="toolbar-root" role="toolbar" part="root">
        <slot class="slot-wrapper"></slot>
        <button class="overflow-btn" part="overflow-button" type="button" hidden
                aria-expanded="false">
          <slot name="overflow-icon"><span aria-hidden="true">&#8943;</span></slot>
        </button>
        <div class="overflow-panel" part="overflow-menu" role="group" hidden>
          <slot name="${OVERFLOW_SLOT}"></slot>
        </div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._root = this.$(".toolbar-root")
    this._slot = this.$("slot:not([name])")
    this._overflowBtn = this.$(".overflow-btn")
    this._overflowPanel = this.$(".overflow-panel")
    this._positionDispose = null
    this._layoutQueued = false
    this._observedUnits = new WeakSet()

    const panelId = `${this._toolbarId}-overflow`
    this._root.id = this._toolbarId
    this._overflowPanel.id = panelId
    this._overflowBtn.setAttribute("aria-controls", panelId)

    this._syncAria()

    this.listen(this._slot, "slotchange", this._onSlotChange.bind(this))
    this.listen(this._root, "keydown", this._onKeydown.bind(this))
    this.listen(this._root, "focusin", this._onFocusIn.bind(this))
    this.listen(this._root, "focusout", this._onFocusOut.bind(this))
    this.listen(this._root, "click", this._onRootClick.bind(this))
    this.listen(this._overflowBtn, "click", this._onOverflowClick.bind(this))
    this.listen(document, "pointerdown", this._onDocumentPointerDown.bind(this))

    if (typeof ResizeObserver === "function") {
      this._resizeObserver = new ResizeObserver(this._queueLayout.bind(this))
      this._resizeObserver.observe(this._root)
    }

    /* Items added, removed, relabelled or disabled inside a slotted group. */
    if (typeof MutationObserver === "function") {
      this._mutationObserver = new MutationObserver(this._queueLayout.bind(this))
      this._mutationObserver.observe(this, {
        childList: true,
        subtree: true,
        characterData: true,
        attributes: true,
        attributeFilter: ["disabled", "hidden", "aria-disabled", "data-toolbar-item"]
      })
    }

    this.onTeardown(() => {
      if (this._resizeObserver !== null) {
        this._resizeObserver.disconnect()
        this._resizeObserver = null
      }
      if (this._mutationObserver !== null) {
        this._mutationObserver.disconnect()
        this._mutationObserver = null
      }
      this._stopPositioning()
    })

    this._layout()
    return
  }

  /* ----- accessible name and state ----- */

  /*
   * Name the toolbar. `labelledby` wins over `label`; because an IDREF
   * cannot point from the shadow root to an element outside it, the text of
   * the referenced element is copied into aria-label.
   */
  _syncAria() {
    if (this._root === undefined || this._root === null) {
      return
    }

    let name = this.getAttribute("label") || ""

    const labelledby = this.getAttribute("labelledby") || ""
    if (labelledby.length > 0) {
      const scope = this.getRootNode()
      let labelElement = null
      if (scope !== null && typeof scope.getElementById === "function") {
        labelElement = scope.getElementById(labelledby)
      }
      if (labelElement !== null) {
        name = labelElement.textContent.trim()
      }
    }

    if (name.length > 0) {
      this._root.setAttribute("aria-label", name)
    } else {
      this._root.removeAttribute("aria-label")
    }

    this._root.setAttribute("aria-orientation", this._orientation())

    /* A disabled toolbar is inert: its controls take neither focus nor clicks. */
    if (this.hasAttribute("disabled") === true) {
      this._root.setAttribute("aria-disabled", "true")
      this._root.setAttribute("inert", "")
    } else {
      this._root.removeAttribute("aria-disabled")
      this._root.removeAttribute("inert")
    }

    const overflowLabel = this.getAttribute("overflow-button-label") || t("mj.toolbar.moreActions")
    this._overflowBtn.setAttribute("aria-label", overflowLabel)
    this._overflowPanel.setAttribute("aria-label", overflowLabel)
    return
  }

  _orientation() {
    const orientation = this.getAttribute("orientation") === "vertical" ? "vertical" : "horizontal"
    return orientation
  }

  /* ----- items and roving tabindex ----- */

  /* The direct children the toolbar lays out: default-slot and overflowed ones. */
  _layoutUnits() {
    const units = []
    const children = this.children
    for (let index = 0; index < children.length; index = index + 1) {
      const child = children[index]
      const slotName = child.getAttribute("slot")
      if (slotName === null || slotName === "" || slotName === OVERFLOW_SLOT) {
        units.push(child)
      }
    }
    return units
  }

  /* The items inside one direct child: the child itself, or the items it groups. */
  _itemElementsOf(unit) {
    const found = []

    if (unit.matches(ITEM_SELECTOR) === true) {
      found.push(unit)
    } else {
      const nested = unit.querySelectorAll(ITEM_SELECTOR)
      for (let index = 0; index < nested.length; index = index + 1) {
        const candidate = nested[index]
        /* A control inside another item belongs to that item. */
        const owner = candidate.parentElement !== null ? candidate.parentElement.closest(ITEM_SELECTOR) : null
        if (owner === null || unit.contains(owner) === false) {
          found.push(candidate)
        }
      }
    }

    return found
  }

  /*
   * The node of an item that takes the tab stop: the inner control of a
   * custom element, the element itself otherwise (including a custom
   * element that is focusable as a whole, which carries its own tabindex).
   * null while a custom element has not rendered yet.
   */
  _focusTargetOf(element) {
    let target = element

    const isCustomElement = element.localName.indexOf("-") >= 0
    if (isCustomElement === true && element.hasAttribute("tabindex") === false) {
      target = null
      if (element.shadowRoot !== null && element.shadowRoot !== undefined) {
        target = element.shadowRoot.querySelector(INNER_FOCUSABLE_SELECTOR)
      }
      if (target === null) {
        this._refreshWhenDefined(element.localName)
      }
    }

    return target
  }

  /* Collect the items again once a not-yet-registered custom element is defined. */
  _refreshWhenDefined(tagName) {
    if (this._pendingDefinitions[tagName] === true) {
      return
    }
    this._pendingDefinitions[tagName] = true
    customElements.whenDefined(tagName).then(() => {
      this._pendingDefinitions[tagName] = false
      this._queueLayout()
    })
    return
  }

  _isUsable(element) {
    const disabled =
      element.hasAttribute("disabled") === true ||
      element.getAttribute("aria-disabled") === "true"
    const rendered = element.getClientRects().length > 0
    const usable = disabled === false && rendered === true
    return usable
  }

  /* Rebuild the roving item list from the slotted content and re-apply the tab stop. */
  _refreshItems() {
    const items = []
    const overflowItems = []
    const units = this._layoutUnits()

    const collect = (inPanel) => {
      for (let index = 0; index < units.length; index = index + 1) {
        const unit = units[index]
        const unitInPanel = unit.getAttribute("slot") === OVERFLOW_SLOT
        if (unitInPanel === inPanel) {
          const elements = this._itemElementsOf(unit)
          for (let position = 0; position < elements.length; position = position + 1) {
            const element = elements[position]
            if (inPanel === true) {
              overflowItems.push(element)
            }
            if (this._isUsable(element) === true) {
              const target = this._focusTargetOf(element)
              if (target !== null) {
                items.push({ element: element, target: target, inPanel: inPanel })
              }
            }
          }
        }
      }
    }

    collect(false)
    if (this._overflowBtn.hidden === false) {
      items.push({ element: this._overflowBtn, target: this._overflowBtn, inPanel: false })
    }
    collect(true)

    this._items = items

    if (sameElements(overflowItems, this._overflowItems) === false) {
      this._overflowItems = overflowItems
      this.emit("mj-toolbar-overflow-change", {
        overflowCount: overflowItems.length,
        overflowItems: overflowItems.slice()
      })
    }

    this._syncTabStops()
    return
  }

  _indexOfElement(element) {
    let found = -1
    for (let index = 0; index < this._items.length && found < 0; index = index + 1) {
      if (this._items[index].element === element) {
        found = index
      }
    }
    return found
  }

  /* Exactly one item is in the tab order: the active one, else the first. */
  _syncTabStops() {
    let activeIndex = this._indexOfElement(this._activeElement)
    if (activeIndex < 0) {
      activeIndex = 0
      this._activeElement = this._items.length > 0 ? this._items[0].element : null
    }

    for (let index = 0; index < this._items.length; index = index + 1) {
      const item = this._items[index]
      item.target.tabIndex = index === activeIndex ? 0 : -1
    }
    return
  }

  _focusItem(index) {
    const item = this._items[index]
    if (item !== undefined) {
      this._activeElement = item.element
      this._syncTabStops()
      item.target.focus()
    }
    return
  }

  /* The index of the item whose focus target is `node`, or -1. */
  _itemIndexOfNode(node) {
    let found = -1
    for (let index = 0; index < this._items.length && found < 0; index = index + 1) {
      if (this._items[index].target === node) {
        found = index
      }
    }
    return found
  }

  /* The index of the item `event` came from, or -1. */
  _itemIndexOfEvent(event) {
    let found = -1
    const path = event.composedPath()
    for (let position = 0; position < path.length && found < 0; position = position + 1) {
      const node = path[position]
      if (node === this._root) {
        break
      }
      found = this._indexOfElement(node)
    }
    return found
  }

  _onSlotChange() {
    /* Reassigning a child to the overflow slot fires slotchange too; only a changed set of children needs a new layout. */
    if (sameElements(this._layoutUnits(), this._units) === false) {
      this._queueLayout()
    } else {
      this._refreshItems()
    }
    return
  }

  /* Keep the tab stop on the item that received focus, however it got it. */
  _onFocusIn(event) {
    const index = this._itemIndexOfEvent(event)
    if (index >= 0 && this._items[index].element !== this._activeElement) {
      this._activeElement = this._items[index].element
      this._syncTabStops()
    }
    return
  }

  /* Focus left the toolbar: the overflow popup closes. */
  _onFocusOut(event) {
    const next = event.relatedTarget
    const staysInside =
      next instanceof Node &&
      (this.contains(next) === true || this.shadowRoot.contains(next) === true)
    if (staysInside === false && next !== null) {
      this._closeOverflow(false)
    }
    return
  }

  _onKeydown(event) {
    /*
     * Shift + an arrow, Home or End extends a text selection (or is some
     * control's own chord); the toolbar pattern defines no Shift moves.
     */
    const navigationKey =
      event.key === "ArrowLeft" || event.key === "ArrowRight" || event.key === "ArrowUp" ||
      event.key === "ArrowDown" || event.key === "Home" || event.key === "End"
    const modified =
      event.ctrlKey === true || event.altKey === true || event.metaKey === true ||
      (event.shiftKey === true && navigationKey === true)
    if (event.defaultPrevented === true || modified === true) {
      return
    }

    const index = this._itemIndexOfEvent(event)
    if (index < 0) {
      return
    }

    const item = this._items[index]
    const origin = event.composedPath()[0]
    const panelOpen = this._overflowPanel.hidden === false

    if (event.key === "Escape") {
      if (panelOpen === true) {
        event.preventDefault()
        this._closeOverflow(true)
      }
      return
    }

    /* ArrowDown on the overflow button opens the popup and enters it. */
    if (item.element === this._overflowBtn && event.key === "ArrowDown" && this._orientation() === "horizontal") {
      event.preventDefault()
      this._openOverflow(true)
      return
    }

    /*
     * Items in the popup are stacked, so the vertical arrows move between
     * them; the horizontal ones do as well, which is the way past a control
     * (a select) that keeps the vertical arrows for itself.
     */
    const vertical = item.inPanel === true || this._orientation() === "vertical"
    const horizontal = item.inPanel === true || this._orientation() === "horizontal"
    const rightToLeft = getComputedStyle(this).direction === "rtl"
    let step = 0
    let destination = -1

    /* The items that share the current item's container, in order. */
    const scope = []
    for (let position = 0; position < this._items.length; position = position + 1) {
      if (this._items[position].inPanel === item.inPanel) {
        scope.push(position)
      }
    }
    const scopePosition = scope.indexOf(index)

    if (vertical === true && event.key === "ArrowDown") {
      step = 1
    } else if (vertical === true && event.key === "ArrowUp") {
      step = -1
    } else if (horizontal === true && event.key === "ArrowRight") {
      step = rightToLeft === true ? -1 : 1
    } else if (horizontal === true && event.key === "ArrowLeft") {
      step = rightToLeft === true ? 1 : -1
    }

    if (step !== 0) {
      destination = scope[(scopePosition + step + scope.length) % scope.length]
    } else if (event.key === "Home") {
      destination = scope[0]
    } else if (event.key === "End") {
      destination = scope[scope.length - 1]
    }

    if (destination >= 0 && controlNeedsKey(origin, event.key) === false) {
      event.preventDefault()
      this._focusItem(destination)
    }
    return
  }

  /* ----- overflow ----- */

  /* Coalesce resize / mutation notifications into one layout pass per frame. */
  _queueLayout() {
    if (this._layoutQueued === true) {
      return
    }
    this._layoutQueued = true
    requestAnimationFrame(() => {
      if (this._layoutQueued === true) {
        this._layoutQueued = false
        if (this._root !== null && this.isConnected === true) {
          this._layout()
        }
      }
    })
    return
  }

  /*
   * Decide which direct children fit in the strip and move the rest into the
   * overflow popup. Everything is first put back so it can be measured at
   * its natural size; the trailing children that end beyond the space left
   * beside the "More actions" button are then reassigned to the overflow
   * slot. A vertical toolbar never overflows.
   *
   * The "More actions" button is not hidden for the measurement (it sits
   * after the children and does not move them), so it keeps focus if it has
   * it.
   */
  _layout() {
    const units = this._layoutUnits()
    this._units = units
    const focusedBefore = deepActiveElement()

    for (let index = 0; index < units.length; index = index + 1) {
      const unit = units[index]
      if (unit.getAttribute("slot") === OVERFLOW_SLOT) {
        unit.removeAttribute("slot")
      }
      /* A child that changes size (a new label, a late upgrade) needs a new layout. */
      if (this._resizeObserver !== null && this._observedUnits.has(unit) === false) {
        this._observedUnits.add(unit)
        this._resizeObserver.observe(unit)
      }
    }

    let firstOverflowed = units.length
    let overflowing = false

    if (this._orientation() === "horizontal" && units.length > 0) {
      const rightToLeft = getComputedStyle(this).direction === "rtl"
      const rootStyle = getComputedStyle(this._root)
      const rootRect = this._root.getBoundingClientRect()
      const paddingEnd = parseFloat(rootStyle.paddingInlineEnd) || 0
      const gap = parseFloat(rootStyle.columnGap) || 0

      /*
       * Distance from the inline-start edge of the strip to the inline-end
       * edge of each child, and the room there is for them.
       */
      const extents = []
      for (let index = 0; index < units.length; index = index + 1) {
        const rect = units[index].getBoundingClientRect()
        const extent = rightToLeft === true ? rootRect.right - rect.left : rect.right - rootRect.left
        extents.push(rect.width > 0 ? extent : 0)
      }

      let furthest = 0
      for (let index = 0; index < extents.length; index = index + 1) {
        furthest = Math.max(furthest, extents[index])
      }

      const room = rootRect.width - paddingEnd
      if (furthest > room + 0.5) {
        overflowing = true
        this._overflowBtn.hidden = false
        const buttonWidth = this._overflowBtn.getBoundingClientRect().width
        const roomBesideButton = room - buttonWidth - gap

        firstOverflowed = 0
        for (let index = 0; index < units.length; index = index + 1) {
          if (extents[index] <= roomBesideButton + 0.5) {
            firstOverflowed = index + 1
          } else {
            break
          }
        }
      }
    }

    for (let index = firstOverflowed; index < units.length; index = index + 1) {
      units[index].setAttribute("slot", OVERFLOW_SLOT)
    }

    if (overflowing === false) {
      this._closeOverflow(false)
      this._overflowBtn.hidden = true
    }

    this._refreshItems()

    /* A control that was moved between the strip and the open popup keeps focus. */
    if (
      focusedBefore instanceof HTMLElement &&
      focusedBefore !== deepActiveElement() &&
      focusedBefore.getClientRects().length > 0 &&
      this._itemIndexOfNode(focusedBefore) >= 0
    ) {
      focusedBefore.focus()
    }
    return
  }

  _openOverflow(focusFirst) {
    if (this._overflowBtn.hidden === true) {
      return
    }

    if (this._overflowPanel.hidden === true) {
      this._overflowPanel.hidden = false
      this._overflowBtn.setAttribute("aria-expanded", "true")

      const rightToLeft = getComputedStyle(this).direction === "rtl"
      this._positionDispose = autoPosition(this._overflowPanel, this._overflowBtn, {
        placement: rightToLeft === true ? "bottom-start" : "bottom-end",
        offset: 4,
        padding: 4
      })

      /* The popup's items are rendered now and join the roving set. */
      this._refreshItems()
    }

    if (focusFirst === true) {
      for (let index = 0; index < this._items.length; index = index + 1) {
        if (this._items[index].inPanel === true) {
          this._focusItem(index)
          break
        }
      }
    }
    return
  }

  _stopPositioning() {
    if (this._positionDispose !== null) {
      this._positionDispose()
      this._positionDispose = null
    }
    return
  }

  _closeOverflow(focusButton) {
    if (this._overflowPanel === null || this._overflowPanel.hidden === true) {
      return
    }

    this._stopPositioning()
    this._overflowPanel.hidden = true
    this._overflowBtn.setAttribute("aria-expanded", "false")
    this._refreshItems()

    if (focusButton === true) {
      this._focusItem(this._indexOfElement(this._overflowBtn))
    }
    return
  }

  _onOverflowClick() {
    if (this._overflowPanel.hidden === true) {
      this._openOverflow(false)
    } else {
      this._closeOverflow(false)
    }
    return
  }

  /*
   * Activating a plain button (or link) in the popup carries out its action
   * and closes the popup; toggles, selects and fields keep it open.
   */
  _onRootClick(event) {
    const index = this._itemIndexOfEvent(event)
    if (index < 0 || this._items[index].inPanel === false) {
      return
    }

    const element = this._items[index].element
    const plainButton =
      element.matches("button, a[href], mj-button") === true &&
      element.hasAttribute("aria-pressed") === false
    if (plainButton === true) {
      this._closeOverflow(true)
    }
    return
  }

  _onDocumentPointerDown(event) {
    if (this._overflowPanel !== null && this._overflowPanel.hidden === false) {
      if (event.composedPath().indexOf(this) < 0) {
        this._closeOverflow(false)
      }
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._root === undefined || this._root === null) {
      return
    }

    this._syncAria()
    if (name === "orientation" || name === "variant" || name === "active") {
      this._queueLayout()
    }
    return
  }

  /* The toolbar items currently reachable with the arrow keys, in order. */
  get items() {
    const found = []
    for (let index = 0; index < this._items.length; index = index + 1) {
      if (this._items[index].element !== this._overflowBtn) {
        found.push(this._items[index].element)
      }
    }
    return found
  }

  /* The items currently moved into the overflow popup. */
  get overflowItems() {
    const found = this._overflowItems.slice()
    return found
  }
}
