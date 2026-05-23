/*
 * mjtabs.js
 *
 * <mj-tabs> -- WAI-ARIA tablist/tab/tabpanel composite component.
 * Roving tabindex on tab buttons; automatic or manual activation.
 * Links slotted <mj-tab slot="tab"> elements to <mj-tab-panel> elements by index.
 *
 * WAI-ARIA: role=tablist; role=tab; role=tabpanel; aria-selected; aria-controls; aria-labelledby.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { RovingTabindex } from "../core/focustrap.js";

const STYLES = `
:host { display: block; }

.tablist-wrapper {
  display: flex;
  align-items: stretch;
  overflow: hidden;
  border-bottom: 1px solid var(--mj-border);
  position: relative;
}
:host([orientation="vertical"]) .tablist-wrapper {
  flex-direction: column;
  border-bottom: none;
  border-inline-end: 1px solid var(--mj-border);
  width: fit-content;
}
:host([orientation="vertical"]) { display: flex; align-items: flex-start; }

.tablist {
  display: flex;
  gap: var(--mj-tabs-tab-gap, var(--mj-space-1));
  overflow: hidden;
  flex: 1;
}
:host([orientation="vertical"]) .tablist { flex-direction: column; }

.tab-slot-wrapper { display: contents; }

.panels { flex: 1; }

.indicator {
  position: absolute;
  bottom: 0;
  height: var(--mj-tabs-indicator-height, 2px);
  background: var(--mj-tabs-indicator-color, var(--mj-accent));
  transition: left var(--mj-tabs-transition-duration, var(--mj-motion-fast)) var(--mj-motion-ease),
              width var(--mj-tabs-transition-duration, var(--mj-motion-fast)) var(--mj-motion-ease);
  pointer-events: none;
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
  outline-offset: var(--mj-focus-ring-offset);
}
::slotted([slot="tab"][aria-disabled="true"]) { opacity: 0.45; cursor: not-allowed; }

::slotted(:not([slot])) {
  padding: var(--mj-tabs-panel-padding, var(--mj-space-5));
  outline: none;
}
::slotted([hidden]) { display: none !important; }
`;

export class MjTabs extends MjElement {
  static tagName = "mj-tabs";
  static styles = STYLES;
  static watched = ["selected", "variant", "orientation", "activation", "tablist-label"];

  constructor() {
    super();
    this._tabs = [];
    this._panels = [];
    this._roving = null;
  }

  render() {
    const tablistLabel = this.getAttribute("tablist-label") || "";
    const orientation = this.getAttribute("orientation") || "horizontal";

    const markup = `
      <div class="tablist-wrapper">
        <div class="tablist" part="tablist" role="tablist"
          aria-label="${tablistLabel}"
          aria-orientation="${orientation}">
          <slot name="tab"></slot>
        </div>
        <span class="indicator" part="indicator" aria-hidden="true"></span>
      </div>
      <div class="panels" part="panels">
        <slot></slot>
      </div>
    `;
    return markup
  }

  afterRender() {
    this._tabSlot = this.shadowRoot.querySelector("slot[name='tab']");
    this._panelSlot = this.shadowRoot.querySelector("slot:not([name])");
    this._tablist = this.$(".tablist");
    this._indicator = this.$(".indicator");

    this.listen(this._tabSlot, "slotchange", this._onSlotsChange.bind(this));
    this.listen(this._panelSlot, "slotchange", this._onSlotsChange.bind(this));
    this.listen(this._tablist, "keydown", this._onKeydown.bind(this));

    this._initComposite();
    return
  }

  _onSlotsChange() {
    this._initComposite();
    return
  }

  _initComposite() {
    this._tabs = this._tabSlot.assignedElements({ flatten: true });
    this._panels = this._panelSlot.assignedElements({ flatten: true });

    const count = Math.min(this._tabs.length, this._panels.length);

    for (let index = 0; index < count; index = index + 1) {
      const tab = this._tabs[index];
      const panel = this._panels[index];

      if (tab.id === null || tab.id === "") {
        tab.id = nextId("mj-tab");
      }
      if (panel.id === null || panel.id === "") {
        panel.id = nextId("mj-tabpanel");
      }

      tab.setAttribute("role", "tab");
      tab.setAttribute("aria-controls", panel.id);
      panel.setAttribute("role", "tabpanel");
      panel.setAttribute("aria-labelledby", tab.id);
      panel.setAttribute("tabindex", "0");
    }

    const selectedId = this.getAttribute("selected");
    let selectedIndex = 0;

    if (selectedId !== null && selectedId !== "") {
      const found = this._tabs.findIndex(function(t) { return t.id === selectedId; });
      if (found !== -1) {
        selectedIndex = found;
      }
    }

    this._activateTab(selectedIndex, false);

    if (this._roving !== null) {
      this._roving.setItems(this._tabs);
    } else if (this._tabs.length > 0) {
      const orientation = this.getAttribute("orientation") === "vertical" ? "vertical" : "horizontal";
      this._roving = new RovingTabindex({ items: this._tabs, orientation: orientation, wrap: true });
      this.onTeardown(this._roving.attach(this._tablist));
    }

    if (this._roving !== null) {
      this._roving.index = selectedIndex;
      this._roving._sync();
    }
    return
  }

  _activateTab(index, fireEvent) {
    if (index < 0 || index >= this._tabs.length) {
      return
    }

    const previousTab = this._tabs.find(function(t) { return t.getAttribute("aria-selected") === "true"; });
    const previousId = previousTab !== undefined ? previousTab.id : "";

    for (let i = 0; i < this._tabs.length; i = i + 1) {
      const tab = this._tabs[i];
      const panel = this._panels[i];
      const isSelected = i === index;

      tab.setAttribute("aria-selected", isSelected === true ? "true" : "false");
      tab.tabIndex = isSelected === true ? 0 : -1;

      if (panel !== undefined) {
        if (isSelected === true) {
          panel.removeAttribute("hidden");
        } else {
          panel.setAttribute("hidden", "");
        }
      }
    }

    const selectedTab = this._tabs[index];
    this.setAttribute("selected", selectedTab.id);

    if (fireEvent === true) {
      const selectedPanel = this._panels[index];
      this.emit("mj-tabs-change", {
        selectedId: selectedTab.id,
        previousId: previousId,
        selectedTab: selectedTab,
        selectedPanel: selectedPanel || null
      });
    }

    this._updateIndicator(index);
    return
  }

  _updateIndicator(index) {
    if (this._indicator === null || this._tabs.length === 0) {
      return
    }
    const tab = this._tabs[index];
    if (tab === undefined) {
      return
    }
    const tabRect = tab.getBoundingClientRect();
    const listRect = this._tablist.getBoundingClientRect();
    this._indicator.style.left = (tabRect.left - listRect.left) + "px";
    this._indicator.style.width = tabRect.width + "px";
    return
  }

  _onKeydown(event) {
    const orientation = this.getAttribute("orientation") || "horizontal";
    const activation = this.getAttribute("activation") || "automatic";
    const isHorizontal = orientation === "horizontal";

    const nextKey = isHorizontal === true ? "ArrowRight" : "ArrowDown";
    const prevKey = isHorizontal === true ? "ArrowLeft" : "ArrowUp";

    let handled = false;

    if (event.key === nextKey || event.key === prevKey) {
      handled = true;
    } else if (event.key === "Home" || event.key === "End") {
      handled = true;
    } else if ((event.key === "Enter" || event.key === " ") && activation === "manual") {
      handled = true;
      const focusedTab = document.activeElement;
      const focusedIndex = this._tabs.indexOf(focusedTab);
      if (focusedIndex !== -1) {
        event.preventDefault();
        this._activateTab(focusedIndex, true);
        return
      }
    }

    if (handled === false) {
      return
    }

    if (event.key !== "Enter" && event.key !== " ") {
      event.preventDefault();
      if (this._roving !== null) {
        this._roving._handleKeydown(event);
      }
      if (activation === "automatic") {
        this._activateTab(this._roving !== null ? this._roving.index : 0, true);
      }
    }
    return
  }

  get selectedTab() {
    const found = this._tabs.find(function(t) { return t.getAttribute("aria-selected") === "true"; });
    return found !== undefined ? found : null
  }

  get selectedPanel() {
    const index = this._tabs.findIndex(function(t) { return t.getAttribute("aria-selected") === "true"; });
    if (index === -1) {
      return null
    }
    return this._panels[index] || null
  }

  get tabs() {
    return this._tabs.slice()
  }
}
