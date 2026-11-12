/*
 * mjtabs.js
 *
 * <mj-tabs> -- WAI-ARIA tablist/tab/tabpanel composite component.
 * Roving tabindex on tab buttons; automatic or manual activation.
 * Links slotted <mj-tab slot="tab"> elements to <mj-tab-panel> elements by index.
 *
 * Tabs are activated by click / tap, by the arrow, Home and End keys
 * (automatic activation) or by Enter / Space on the focused tab (manual
 * activation). Disabled tabs are skipped. A tab strip wider than its
 * container scrolls, with scroll buttons at the edges.
 *
 * WAI-ARIA: role=tablist; role=tab; role=tabpanel; aria-selected; aria-controls; aria-labelledby.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { deepActiveElement } from "../core/focustrap.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";

const STYLES = `
:host { display: block; }

.tablist-wrapper {
  display: flex;
  align-items: stretch;
  border-block-end: 1px solid var(--mj-border);
  position: relative;
}
:host([orientation="vertical"]) .tablist-wrapper {
  flex-direction: column;
  border-block-end: none;
  border-inline-end: 1px solid var(--mj-border);
  width: fit-content;
}
:host([orientation="vertical"]) { display: flex; align-items: flex-start; }

/* The strip scrolls when the tabs do not fit; the scrollbar itself is not shown. */
.tablist {
  display: flex;
  gap: var(--mj-tabs-tab-gap, var(--mj-space-1));
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: none;
  flex: 1;
  min-width: 0;
  position: relative;
}
.tablist::-webkit-scrollbar { display: none; }
:host([orientation="vertical"]) .tablist {
  flex-direction: column;
  overflow-x: hidden;
  overflow-y: auto;
}

.scroll-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: var(--mj-control-height-sm);
  background: none;
  border: none;
  cursor: pointer;
  color: var(--mj-text-muted);
  font: inherit;
}
.scroll-btn:hover { color: var(--mj-text); background: var(--mj-bg-muted); }
.scroll-btn[hidden] { display: none; }
.scroll-btn:disabled { opacity: 0.45; cursor: default; }
:host(:dir(rtl)) .scroll-btn svg { transform: scaleX(-1); }
:host([orientation="vertical"]) .scroll-btn { display: none; }

.panels { flex: 1; min-width: 0; }

/* Positioned from script: under the selected tab, or beside it when vertical. */
.indicator {
  position: absolute;
  inset-block-end: 0;
  height: var(--mj-tabs-indicator-height, 2px);
  background: var(--mj-tabs-indicator-color, var(--mj-accent));
  transition: left var(--mj-tabs-transition-duration, var(--mj-motion-fast)) var(--mj-motion-ease),
              top var(--mj-tabs-transition-duration, var(--mj-motion-fast)) var(--mj-motion-ease),
              width var(--mj-tabs-transition-duration, var(--mj-motion-fast)) var(--mj-motion-ease),
              height var(--mj-tabs-transition-duration, var(--mj-motion-fast)) var(--mj-motion-ease);
  pointer-events: none;
}
:host([orientation="vertical"]) .indicator {
  inset-block-end: auto;
  inset-inline-end: 0;
  width: var(--mj-tabs-indicator-height, 2px);
}
:host([variant="pills"]) .indicator { display: none; }
:host([variant="enclosed"]) .indicator { display: none; }
@media (prefers-reduced-motion: reduce) {
  .indicator { transition: none; }
}

::slotted([slot="tab"]) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  padding: var(--mj-tabs-tab-padding, var(--mj-space-2) var(--mj-space-4));
  background: none;
  border: none;
  cursor: pointer;
  font: inherit;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text-muted);
  white-space: nowrap;
  border-radius: var(--mj-radius-md) var(--mj-radius-md) 0 0;
  transition: color var(--mj-motion-fast) var(--mj-motion-ease),
              background var(--mj-motion-fast) var(--mj-motion-ease);
  min-height: var(--mj-control-height-md);
  position: relative;
}
::slotted([slot="tab"][aria-selected="true"]) {
  color: var(--mj-accent);
  font-weight: var(--mj-tabs-font-weight-selected, 600);
}
::slotted([slot="tab"]:hover) { color: var(--mj-text); background: var(--mj-bg-muted); }
::slotted([slot="tab"]:focus-visible) {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: calc(0px - var(--mj-focus-ring-width));
}
::slotted([slot="tab"][aria-disabled="true"]),
::slotted([slot="tab"][disabled]) { opacity: 0.45; cursor: not-allowed; }

/* pills: each tab is a chip; the selected one is filled. */
:host([variant="pills"]) .tablist-wrapper { border: none; }
:host([variant="pills"]) ::slotted([slot="tab"]) { border-radius: var(--mj-radius-pill); }
:host([variant="pills"]) ::slotted([slot="tab"][aria-selected="true"]) {
  background: var(--mj-accent);
  color: var(--mj-text-on-accent);
}

/* enclosed: the selected tab is a box joined to the panel below it. */
:host([variant="enclosed"]) ::slotted([slot="tab"]) {
  border: 1px solid transparent;
}
:host([variant="enclosed"]) ::slotted([slot="tab"][aria-selected="true"]) {
  background: var(--mj-surface);
  border-color: var(--mj-border);
  border-block-end-color: var(--mj-surface);
  color: var(--mj-text);
}
:host([variant="enclosed"]) .tablist-wrapper { border-block-end: none; }
:host([variant="enclosed"]) .tablist { box-shadow: inset 0 -1px 0 var(--mj-border); }
:host([variant="enclosed"][orientation="vertical"]) .tablist { box-shadow: none; }

::slotted(:not([slot])) {
  padding: var(--mj-tabs-panel-padding, var(--mj-space-5));
  outline: none;
}
::slotted(:not([slot]):focus-visible) {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: calc(0px - var(--mj-focus-ring-width));
}
::slotted([hidden]) { display: none !important; }
`;

export class MjTabs extends MjElement {
  static tagName = "mj-tabs";
  static styles = STYLES;
  static watched = ["selected", "variant", "orientation", "activation", "tablist-label"];

  constructor() {
    super()
    this._tabs = []
    this._panels = []

    /* Index of the selected tab, and of the tab holding the roving tab stop. */
    this._selectedIndex = -1
    this._focusIndex = -1

    this._resizeObserver = null
  }

  render() {
    /* The label and orientation are applied in afterRender through setAttribute. */
    const markup = html`
      <div class="tablist-wrapper">
        <button class="scroll-btn scroll-prev" part="scroll-prev" type="button" tabindex="-1"
                aria-label="${t("mj.tabs.scrollPrev")}" hidden>
          <svg width="12" height="12" viewBox="0 0 16 16" aria-hidden="true">
            <path d="M10 3L5 8l5 5" stroke="currentColor" stroke-width="1.5" fill="none"
                  stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
        <div class="tablist" part="tablist" role="tablist">
          <slot name="tab"></slot>
          <span class="indicator" part="indicator" aria-hidden="true"></span>
        </div>
        <button class="scroll-btn scroll-next" part="scroll-next" type="button" tabindex="-1"
                aria-label="${t("mj.tabs.scrollNext")}" hidden>
          <svg width="12" height="12" viewBox="0 0 16 16" aria-hidden="true">
            <path d="M6 3l5 5-5 5" stroke="currentColor" stroke-width="1.5" fill="none"
                  stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
      <div class="panels" part="panels">
        <slot></slot>
      </div>
    `
    return markup
  }

  afterRender() {
    this._tabSlot = this.shadowRoot.querySelector("slot[name='tab']")
    this._panelSlot = this.shadowRoot.querySelector("slot:not([name])")
    this._tablist = this.$(".tablist")
    this._indicator = this.$(".indicator")
    this._scrollPrev = this.$(".scroll-prev")
    this._scrollNext = this.$(".scroll-next")

    this.listen(this._tabSlot, "slotchange", this._onSlotsChange.bind(this))
    this.listen(this._panelSlot, "slotchange", this._onSlotsChange.bind(this))
    this.listen(this._tablist, "keydown", this._onKeydown.bind(this))
    this.listen(this._tablist, "click", this._onClick.bind(this))
    this.listen(this._tablist, "scroll", this._syncScrollButtons.bind(this), { passive: true })
    this.listen(this._scrollPrev, "click", () => { this._scrollStrip(-1) })
    this.listen(this._scrollNext, "click", () => { this._scrollStrip(1) })

    /* The indicator and scroll buttons follow every size change of the strip or a tab. */
    this._resizeObserver = new ResizeObserver(() => {
      this._updateIndicator()
      this._syncScrollButtons()
    })
    this.onTeardown(() => {
      this._resizeObserver.disconnect()
      this._resizeObserver = null
    })

    this._syncTablistAttributes()
    this._initComposite()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._tablist === undefined || this._tablist === null) {
      return
    }

    if (name === "selected") {
      const index = this._indexOfTabId(newValue)
      if (index !== -1 && index !== this._selectedIndex && this._isDisabled(this._tabs[index]) === false) {
        this._applySelection(index)
      }
    } else if (name === "orientation" || name === "tablist-label") {
      this._syncTablistAttributes()
      this._updateIndicator()
      this._syncScrollButtons()
    } else if (name === "variant") {
      this._updateIndicator()
    }
    return
  }

  _orientation() {
    const orientation = this.getAttribute("orientation") === "vertical" ? "vertical" : "horizontal"
    return orientation
  }

  _syncTablistAttributes() {
    this._tablist.setAttribute("aria-orientation", this._orientation())

    /* An empty aria-label would hide the name a surrounding aria-labelledby could give. */
    const label = this.getAttribute("tablist-label")
    if (label !== null && label.length > 0) {
      this._tablist.setAttribute("aria-label", label)
    } else {
      this._tablist.removeAttribute("aria-label")
    }
    return
  }

  _onSlotsChange() {
    this._initComposite()
    return
  }

  _isDisabled(tab) {
    const disabled = tab.getAttribute("aria-disabled") === "true" || tab.hasAttribute("disabled") === true
    return disabled
  }

  _indexOfTabId(tabId) {
    let found = -1
    if (tabId !== null && tabId !== undefined && tabId !== "") {
      for (let index = 0; index < this._tabs.length; index = index + 1) {
        if (found === -1 && this._tabs[index].id === tabId) {
          found = index
        }
      }
    }
    return found
  }

  /* Index of the first enabled tab at or after `start` moving by `delta`, or -1. */
  _findEnabled(start, delta, wrap) {
    const count = this._tabs.length
    let found = -1
    let index = start

    for (let visited = 0; visited < count && found === -1; visited = visited + 1) {
      if (index < 0 || index >= count) {
        if (wrap === false) {
          break
        }
        index = (index + count) % count
      }
      if (this._isDisabled(this._tabs[index]) === false) {
        found = index
      }
      index = index + delta
    }
    return found
  }

  _initComposite() {
    const previousSelected = this._selectedIndex >= 0 ? this._tabs[this._selectedIndex] : undefined

    this._tabs = this._tabSlot.assignedElements({ flatten: true })
    this._panels = this._panelSlot.assignedElements({ flatten: true })

    const count = Math.min(this._tabs.length, this._panels.length)

    for (let index = 0; index < this._tabs.length; index = index + 1) {
      const tab = this._tabs[index]
      if (tab.id === null || tab.id === "") {
        tab.id = nextId("mj-tab")
      }
      tab.setAttribute("role", "tab")
    }

    for (let index = 0; index < count; index = index + 1) {
      const tab = this._tabs[index]
      const panel = this._panels[index]

      if (panel.id === null || panel.id === "") {
        panel.id = nextId("mj-tabpanel")
      }

      tab.setAttribute("aria-controls", panel.id)
      panel.setAttribute("role", "tabpanel")
      panel.setAttribute("aria-labelledby", tab.id)
      panel.setAttribute("tabindex", "0")
    }

    /*
     * Selection: the tab named by `selected`, else the tab that was selected
     * before the slots changed, else the first enabled tab.
     */
    let selectedIndex = this._indexOfTabId(this.getAttribute("selected"))
    if (selectedIndex !== -1 && this._isDisabled(this._tabs[selectedIndex]) === true) {
      selectedIndex = -1
    }
    if (selectedIndex === -1 && previousSelected !== undefined) {
      selectedIndex = this._tabs.indexOf(previousSelected)
    }
    if (selectedIndex === -1) {
      selectedIndex = this._findEnabled(0, 1, false)
    }

    this._selectedIndex = -1
    this._focusIndex = -1
    if (selectedIndex !== -1) {
      this._applySelection(selectedIndex)
    }

    this._resizeObserver.disconnect()
    this._resizeObserver.observe(this._tablist)
    for (let index = 0; index < this._tabs.length; index = index + 1) {
      this._resizeObserver.observe(this._tabs[index])
    }
    return
  }

  /* Keep exactly one tab in the tab order. */
  _setTabStop(index) {
    this._focusIndex = index
    for (let position = 0; position < this._tabs.length; position = position + 1) {
      this._tabs[position].tabIndex = position === index ? 0 : -1
    }
    return
  }

  /*
   * Make the tab at `index` the selected one: ARIA state, tab stop, panel
   * visibility, the reflected `selected` attribute and the indicator. Emits
   * nothing -- `_activateTab` is the user-driven path that announces it.
   */
  _applySelection(index) {
    this._selectedIndex = index

    for (let position = 0; position < this._tabs.length; position = position + 1) {
      const tab = this._tabs[position]
      const panel = this._panels[position]
      const isSelected = position === index

      tab.setAttribute("aria-selected", isSelected === true ? "true" : "false")

      if (panel !== undefined) {
        if (isSelected === true) {
          panel.removeAttribute("hidden")
        } else {
          panel.setAttribute("hidden", "")
        }
      }
    }

    this._setTabStop(index)

    const selectedTab = this._tabs[index]
    if (this.getAttribute("selected") !== selectedTab.id) {
      this.setAttribute("selected", selectedTab.id)
    }

    this._scrollTabIntoView(selectedTab)
    this._updateIndicator()
    this._syncScrollButtons()
    return
  }

  /*
   * User-driven activation. `mj-tabs-change` fires first and is cancelable;
   * `mj-tabs-changed` follows once the new tab and panel are showing.
   * Returns true when the tab at `index` is selected afterwards.
   */
  _activateTab(index) {
    let activated = false

    if (index >= 0 && index < this._tabs.length && this._isDisabled(this._tabs[index]) === false) {
      if (index === this._selectedIndex) {
        activated = true
      } else {
        const previousTab = this._selectedIndex >= 0 ? this._tabs[this._selectedIndex] : undefined
        const previousId = previousTab !== undefined ? previousTab.id : ""
        const selectedTab = this._tabs[index]
        const selectedPanel = this._panels[index]

        const proceed = this.emit("mj-tabs-change", {
          selectedId: selectedTab.id,
          previousId: previousId,
          selectedTab: selectedTab,
          selectedPanel: selectedPanel || null
        }, { cancelable: true })

        if (proceed === true) {
          this._applySelection(index)
          this.emit("mj-tabs-changed", { selectedId: selectedTab.id, previousId: previousId })
          activated = true
        }
      }
    }
    return activated
  }

  _scrollTabIntoView(tab) {
    if (this._orientation() === "horizontal" && this._tablist.scrollWidth > this._tablist.clientWidth) {
      const tabRect = tab.getBoundingClientRect()
      const listRect = this._tablist.getBoundingClientRect()
      if (tabRect.left < listRect.left) {
        this._tablist.scrollLeft = this._tablist.scrollLeft - (listRect.left - tabRect.left)
      } else if (tabRect.right > listRect.right) {
        this._tablist.scrollLeft = this._tablist.scrollLeft + (tabRect.right - listRect.right)
      }
    }
    return
  }

  /* Place the indicator under the selected tab, or beside it when vertical. */
  _updateIndicator() {
    if (this._indicator === undefined || this._indicator === null) {
      return
    }

    const tab = this._selectedIndex >= 0 ? this._tabs[this._selectedIndex] : undefined
    const style = this._indicator.style

    if (tab === undefined) {
      style.width = "0px"
      style.height = ""
      return
    }

    const tabRect = tab.getBoundingClientRect()
    const listRect = this._tablist.getBoundingClientRect()

    if (this._orientation() === "vertical") {
      style.left = ""
      style.width = ""
      style.top = (tabRect.top - listRect.top + this._tablist.scrollTop) + "px"
      style.height = tabRect.height + "px"
    } else {
      style.top = ""
      style.height = ""
      style.left = (tabRect.left - listRect.left + this._tablist.scrollLeft) + "px"
      style.width = tabRect.width + "px"
    }
    return
  }

  /* Show the scroll buttons only while the strip overflows; disable one at its edge. */
  _syncScrollButtons() {
    if (this._scrollPrev === undefined || this._scrollPrev === null) {
      return
    }

    const list = this._tablist
    const overflow = list.scrollWidth - list.clientWidth
    const overflowing = this._orientation() === "horizontal" && overflow > 1

    this._scrollPrev.hidden = overflowing === false
    this._scrollNext.hidden = overflowing === false

    if (overflowing === true) {
      /* scrollLeft runs 0..overflow in LTR and 0..-overflow in RTL. */
      const travelled = Math.abs(list.scrollLeft)
      this._scrollPrev.disabled = travelled <= 1
      this._scrollNext.disabled = travelled >= overflow - 1
    }
    return
  }

  _scrollStrip(direction) {
    const isRtl = getComputedStyle(this).direction === "rtl"
    const step = this._tablist.clientWidth * 0.8 * direction * (isRtl === true ? -1 : 1)
    this._tablist.scrollBy({ left: step, behavior: "smooth" })
    return
  }

  /* Index of the tab an event came from, or -1. */
  _tabIndexFromEvent(event) {
    let found = -1
    const path = event.composedPath()

    for (let index = 0; index < this._tabs.length; index = index + 1) {
      if (found === -1 && path.indexOf(this._tabs[index]) !== -1) {
        found = index
      }
    }
    return found
  }

  _onClick(event) {
    const index = this._tabIndexFromEvent(event)
    if (index !== -1 && this._isDisabled(this._tabs[index]) === false) {
      const activated = this._activateTab(index)
      if (activated === false) {
        /* Canceled: the tab stop stays on the selected tab. */
        this._setTabStop(this._selectedIndex)
      }
    }
    return
  }

  _onKeydown(event) {
    if (this._tabs.length === 0 || event.altKey === true || event.ctrlKey === true || event.metaKey === true) {
      return
    }

    const activation = this.getAttribute("activation") === "manual" ? "manual" : "automatic"
    const isHorizontal = this._orientation() === "horizontal"
    const isRtl = isHorizontal === true && getComputedStyle(this).direction === "rtl"

    let nextKey = isHorizontal === true ? "ArrowRight" : "ArrowDown"
    let prevKey = isHorizontal === true ? "ArrowLeft" : "ArrowUp"
    if (isRtl === true) {
      nextKey = "ArrowLeft"
      prevKey = "ArrowRight"
    }

    /*
     * The tab the key applies to: the one the event came from, else the one
     * that has focus (also when nested in another shadow root), else the tab
     * stop.
     */
    let current = this._tabIndexFromEvent(event)
    if (current === -1) {
      current = this._tabs.indexOf(deepActiveElement())
    }
    if (current === -1) {
      current = this._focusIndex >= 0 ? this._focusIndex : 0
    }

    let target = -1
    if (event.key === nextKey) {
      target = this._findEnabled(current + 1, 1, true)
    } else if (event.key === prevKey) {
      target = this._findEnabled(current - 1, -1, true)
    } else if (event.key === "Home") {
      target = this._findEnabled(0, 1, false)
    } else if (event.key === "End") {
      target = this._findEnabled(this._tabs.length - 1, -1, false)
    } else if (event.key === "Enter" || event.key === " ") {
      /* Handled here so manual activation does not depend on a native click. */
      if (this._isDisabled(this._tabs[current]) === false) {
        event.preventDefault()
        this._activateTab(current)
      }
    }

    if (target !== -1) {
      event.preventDefault()

      if (activation === "automatic") {
        const activated = this._activateTab(target)
        if (activated === true) {
          this._tabs[target].focus()
        }
      } else {
        this._setTabStop(target)
        this._tabs[target].focus()
        this._scrollTabIntoView(this._tabs[target])
      }
    }
    return
  }

  /* Select a tab by id (or by index). Programmatic: no change events are emitted. */
  select(tabIdOrIndex) {
    let index = -1
    if (typeof tabIdOrIndex === "number") {
      index = tabIdOrIndex
    } else {
      index = this._indexOfTabId(tabIdOrIndex)
    }

    let selected = false
    if (index >= 0 && index < this._tabs.length && this._isDisabled(this._tabs[index]) === false) {
      if (index !== this._selectedIndex) {
        this._applySelection(index)
      }
      selected = true
    }
    return selected
  }

  /* The id of the selected tab ("" when there is none). */
  get selected() {
    const tab = this.selectedTab
    return tab !== null ? tab.id : ""
  }

  set selected(tabId) {
    if (this._tablist === undefined || this._tablist === null) {
      /* Not rendered yet: the attribute is applied by the first render. */
      this.setAttribute("selected", String(tabId))
    } else {
      this.select(tabId)
    }
    return
  }

  get selectedTab() {
    const found = this._selectedIndex >= 0 ? this._tabs[this._selectedIndex] : undefined
    return found !== undefined ? found : null
  }

  get selectedPanel() {
    const found = this._selectedIndex >= 0 ? this._panels[this._selectedIndex] : undefined
    return found !== undefined ? found : null
  }

  get tabs() {
    return this._tabs.slice()
  }
}
