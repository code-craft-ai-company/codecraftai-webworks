/*
 * mjmenu.js
 *
 * <mj-menu> -- WAI-ARIA menu/menuitem popup primitive.
 * Uses aria-activedescendant for keyboard focus management; overlay.js for positioning.
 * Supports dropdown, flyout, mega, and context variants.
 *
 * WAI-ARIA: role=menu; aria-activedescendant; role=menuitem; role=menuitemcheckbox; role=menuitemradio.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { autoPosition } from "../core/overlay.js";

const STYLES = `
:host { display: contents; }

.menu {
  position: fixed;
  z-index: var(--mj-menu-z-index, var(--mj-layer-popover));
  min-width: var(--mj-menu-min-width, 160px);
  max-height: var(--mj-menu-max-height, 360px);
  overflow-y: auto;
  background: var(--mj-menu-bg, var(--mj-surface));
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-menu-radius, var(--mj-radius-md));
  box-shadow: var(--mj-menu-shadow, var(--mj-elevation-3));
  padding: var(--mj-space-1) 0;
  outline: none;
}
:host(:not([open])) .menu { display: none; }

.item {
  display: flex;
  align-items: center;
  gap: var(--mj-space-3);
  height: var(--mj-menu-item-height, 40px);
  padding: var(--mj-menu-item-padding, 0 var(--mj-space-4));
  cursor: pointer;
  user-select: none;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
  transition: background var(--mj-motion-fast) var(--mj-motion-ease);
  outline: none;
}
.item[data-active="true"] { background: var(--mj-menu-item-focus-bg, var(--mj-bg-muted)); }
.item[aria-disabled="true"] { opacity: 0.45; cursor: not-allowed; }
.item-icon { flex-shrink: 0; width: 16px; height: 16px; display: flex; align-items: center; }
.item-label { flex: 1; }
.item-description { font-size: var(--mj-font-size-xs); color: var(--mj-text-muted); }
.item-shortcut { font-size: var(--mj-font-size-xs); color: var(--mj-text-muted); margin-inline-start: auto; }
.item-arrow { margin-inline-start: auto; color: var(--mj-text-muted); }

.separator {
  height: 1px;
  background: var(--mj-border);
  margin: var(--mj-space-1) 0;
}

.group-heading {
  padding: var(--mj-space-2) var(--mj-space-4) var(--mj-space-1);
  font-size: var(--mj-font-size-xs);
  font-weight: var(--mj-font-weight-medium);
  color: var(--mj-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.empty-notice {
  padding: var(--mj-space-2) var(--mj-space-4);
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text-muted);
}

:host([variant="mega"]) .menu {
  min-width: 480px;
}
.mega-panel {
  display: grid;
  grid-template-columns: repeat(var(--mj-menu-mega-columns, 3), 1fr);
  gap: var(--mj-space-4);
  padding: var(--mj-space-4);
}
`;

export class MjMenu extends MjElement {
  static tagName = "mj-menu";
  static styles = STYLES;
  static watched = ["open", "variant", "anchor", "placement", "label", "close-on-select"];

  constructor() {
    super();
    this._menuId = nextId("mj-menu");
    this._activeIndex = -1;
    this._disposePosition = null;
    this._hoverTimer = null;
  }

  render() {
    const label = this.getAttribute("label") || "";
    const markup = `
      <div class="menu" part="menu"
        role="menu"
        id="${this._menuId}"
        aria-label="${label}"
        tabindex="-1">
        <slot></slot>
        <div class="empty-notice" part="empty-notice" hidden></div>
      </div>
    `;
    return markup
  }

  afterRender() {
    this._menu = this.$(".menu");
    this._emptyNotice = this.$(".empty-notice");
    this._slot = this.shadowRoot.querySelector("slot");

    this.listen(this._menu, "keydown", this._onKeydown.bind(this));
    this.listen(this._slot, "slotchange", this._onSlotChange.bind(this));

    this.listen(document, "mousedown", this._onDocMousedown.bind(this));
    this.listen(document, "keydown", this._onDocKeydown.bind(this));

    if (this.hasAttribute("open") === true) {
      this._openMenu();
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "open" && this._menu !== undefined) {
      if (newValue !== null) {
        this._openMenu();
      } else {
        this._closeMenu("external");
      }
    }
    return
  }

  onDisconnected() {
    this._stopPositioning();
    return
  }

  _onSlotChange() {
    this._buildItems();
    return
  }

  _buildItems() {
    const items = this._slot.assignedElements({ flatten: true });
    this._itemEls = [];

    for (let i = 0; i < items.length; i = i + 1) {
      const item = items[i];
      const role = item.getAttribute("role") || item.tagName.toLowerCase();

      if (role === "menuitem" || role === "menuitemcheckbox" || role === "menuitemradio" ||
          item.classList.contains("item") || item.getAttribute("data-menu-item") !== null) {

        if (item.id === "") {
          item.id = nextId("mj-menuitem");
        }
        item.className = (item.className + " item").trim();
        item.setAttribute("part", "item");
        item.setAttribute("role", item.getAttribute("role") || "menuitem");
        item.setAttribute("tabindex", "-1");
        this._itemEls.push(item);
      }
    }

    if (this._itemEls.length === 0) {
      this._emptyNotice.removeAttribute("hidden");
    } else {
      this._emptyNotice.setAttribute("hidden", "");
    }
    return
  }

  _getItems() {
    if (this._itemEls === undefined) {
      return []
    }
    return this._itemEls.filter(function(item) {
      return item.getAttribute("aria-disabled") !== "true";
    })
  }

  _openMenu() {
    const proceed = this.emit("mj-menu-open", { trigger: this._getTrigger() }, { cancelable: true });
    if (proceed === false) {
      return
    }

    this._buildItems();
    this._activeIndex = -1;

    const trigger = this._getTrigger();
    if (trigger !== null) {
      trigger.setAttribute("aria-expanded", "true");
      const placement = this.getAttribute("placement") || "bottom-start";
      this._disposePosition = autoPosition(this._menu, trigger, { placement: placement });
    }

    this._menu.focus();
    this._setActive(0);
    return
  }

  _closeMenu(reason) {
    const proceed = this.emit("mj-menu-close", { reason: reason }, { cancelable: true });
    if (proceed === false) {
      return
    }

    this._stopPositioning();
    this._clearActive();

    const trigger = this._getTrigger();
    if (trigger !== null) {
      trigger.setAttribute("aria-expanded", "false");
      trigger.focus();
    }
    return
  }

  _stopPositioning() {
    if (this._disposePosition !== null) {
      this._disposePosition();
      this._disposePosition = null;
    }
    return
  }

  _getTrigger() {
    const anchorSel = this.getAttribute("anchor");
    if (anchorSel === null || anchorSel === "") {
      return null
    }
    const found = document.querySelector(anchorSel) || document.getElementById(anchorSel);
    return found
  }

  _setActive(index) {
    const items = this._getItems();
    this._clearActive();
    if (index < 0 || index >= items.length) {
      return
    }
    this._activeIndex = index;
    const item = items[index];
    item.setAttribute("data-active", "true");
    this._menu.setAttribute("aria-activedescendant", item.id);
    item.scrollIntoView({ block: "nearest" });
    this.emit("mj-menu-item-focus", { item: item });
    return
  }

  _clearActive() {
    const items = this._getItems();
    for (let i = 0; i < items.length; i = i + 1) {
      items[i].removeAttribute("data-active");
    }
    this._menu.removeAttribute("aria-activedescendant");
    return
  }

  _onKeydown(event) {
    const items = this._getItems();
    const count = items.length;

    if (event.key === "ArrowDown") {
      event.preventDefault();
      const next = this._activeIndex < count - 1 ? this._activeIndex + 1 : 0;
      this._setActive(next);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      const prev = this._activeIndex > 0 ? this._activeIndex - 1 : count - 1;
      this._setActive(prev);
    } else if (event.key === "Home") {
      event.preventDefault();
      this._setActive(0);
    } else if (event.key === "End") {
      event.preventDefault();
      this._setActive(count - 1);
    } else if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      if (this._activeIndex >= 0 && this._activeIndex < count) {
        this._activateItem(items[this._activeIndex]);
      }
    } else if (event.key === "Tab") {
      this.removeAttribute("open");
      this._closeMenu("external");
    } else if (event.key.length === 1) {
      this._typeAhead(event.key);
    }
    return
  }

  _typeAhead(char) {
    const items = this._getItems();
    const lower = char.toLowerCase();
    const startIndex = this._activeIndex + 1;

    for (let i = 0; i < items.length; i = i + 1) {
      const idx = (startIndex + i) % items.length;
      const label = items[idx].textContent.trim().toLowerCase();
      if (label.startsWith(lower) === true) {
        this._setActive(idx);
        return
      }
    }
    return
  }

  _activateItem(item) {
    const role = item.getAttribute("role") || "menuitem";

    if (role === "menuitemcheckbox") {
      const checked = item.getAttribute("aria-checked") === "true";
      item.setAttribute("aria-checked", checked === false ? "true" : "false");
    } else if (role === "menuitemradio") {
      const group = item.closest("[role='group']") || this._menu;
      const radios = group.querySelectorAll("[role='menuitemradio']");
      radios.forEach(function(r) { r.setAttribute("aria-checked", "false"); });
      item.setAttribute("aria-checked", "true");
    }

    const value = item.getAttribute("value") || item.textContent.trim();
    const checked = item.getAttribute("aria-checked");
    const checkedBool = checked === "true" ? true : checked === "false" ? false : null;

    const proceed = this.emit("mj-menu-select", {
      item: item,
      value: value,
      checked: checkedBool
    }, { cancelable: true });

    const closeOnSelect = this.getAttribute("close-on-select") !== "false";
    if (closeOnSelect === true && proceed !== false) {
      this.removeAttribute("open");
      this._closeMenu("select");
    }
    return
  }

  _onDocMousedown(event) {
    if (this.hasAttribute("open") === false) {
      return
    }
    const inMenu = this._menu.contains(event.target);
    const trigger = this._getTrigger();
    const inTrigger = trigger !== null && trigger.contains(event.target);

    if (inMenu === false && inTrigger === false) {
      this.removeAttribute("open");
      this._closeMenu("blur");
    }
    return
  }

  _onDocKeydown(event) {
    if (event.key === "Escape" && this.hasAttribute("open") === true) {
      event.stopPropagation();
      this.removeAttribute("open");
      this._closeMenu("escape");
    }
    return
  }

  get items() {
    return this._getItems()
  }

  get activeItem() {
    const items = this._getItems();
    if (this._activeIndex < 0 || this._activeIndex >= items.length) {
      return null
    }
    return items[this._activeIndex]
  }

  get triggerElement() {
    return this._getTrigger()
  }

  get open() {
    return this.hasAttribute("open")
  }

  set open(value) {
    this.reflectBoolean("open", value === true);
    return
  }
}
