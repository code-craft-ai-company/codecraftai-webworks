/*
 * mjassetpicker.js
 *
 * <mj-asset-picker> — searchable, categorized, virtualized grid picker for
 * emoji, icons, fonts, or author-supplied visual assets.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { autoPosition } from "../core/overlay.js";
import { trapFocus } from "../core/focustrap.js";
import { announce } from "../core/announcer.js";

const STYLES = `
:host { display: inline-block; vertical-align: middle; }

.trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: var(--mj-control-height-md);
  min-height: var(--mj-control-height-md);
  padding: 0 var(--mj-space-3);
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-md);
  background: var(--mj-surface);
  cursor: pointer;
  font: inherit;
  color: var(--mj-text);
  gap: var(--mj-space-2);
}
.trigger:hover { background: var(--mj-bg-muted); }
.trigger:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
:host([disabled]) .trigger { opacity: 0.55; cursor: not-allowed; pointer-events: none; }

.popup {
  position: fixed;
  width: var(--mj-asset-picker-popup-width, 20rem);
  height: var(--mj-asset-picker-popup-height, 24rem);
  background: var(--mj-surface-raised, var(--mj-surface));
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-md);
  box-shadow: var(--mj-elevation-3);
  z-index: var(--mj-layer-popover);
  display: none;
  flex-direction: column;
}
:host([open]) .popup { display: flex; }

.search-wrapper {
  padding: var(--mj-space-2) var(--mj-space-3);
  border-bottom: 1px solid var(--mj-border);
  flex-shrink: 0;
}
.search-input {
  width: 100%;
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-sm);
  padding: var(--mj-space-1) var(--mj-space-2);
  font: inherit;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
  background: var(--mj-surface);
}
.search-input:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); }

.body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.category-nav {
  width: var(--mj-asset-picker-category-width, 3rem);
  border-inline-end: 1px solid var(--mj-border);
  overflow-y: auto;
  flex-shrink: 0;
  padding: var(--mj-space-1) 0;
}
.category-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: var(--mj-asset-picker-cell-size, 2rem);
  padding: var(--mj-space-1);
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.2rem;
  border-radius: 0;
}
.category-btn:hover, .category-btn[aria-selected="true"] { background: var(--mj-bg-muted); }
.category-btn:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: -2px; }

.asset-area {
  flex: 1;
  overflow-y: auto;
  padding: var(--mj-space-2);
}
.asset-grid {
  display: grid;
  grid-template-columns: repeat(var(--mj-asset-picker-cols, 8), var(--mj-asset-picker-cell-size, 2rem));
  gap: 2px;
}
.asset-cell {
  width: var(--mj-asset-picker-cell-size, 2rem);
  height: var(--mj-asset-picker-cell-size, 2rem);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--mj-asset-picker-font-size, 1.25rem);
  border-radius: var(--mj-asset-picker-cell-radius, var(--mj-radius-sm));
  cursor: pointer;
  border: 2px solid transparent;
  background: none;
  padding: 0;
}
.asset-cell:hover { background: var(--mj-bg-muted); }
.asset-cell:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.asset-cell[aria-selected="true"] {
  background: var(--mj-asset-picker-selected-bg, var(--mj-bg-subtle));
  border-color: var(--mj-accent);
}

.no-results {
  padding: var(--mj-space-4);
  text-align: center;
  color: var(--mj-text-muted);
  font-size: var(--mj-font-size-sm);
}

.section-label {
  font-size: var(--mj-font-size-xs);
  font-weight: var(--mj-font-weight-medium);
  color: var(--mj-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: var(--mj-space-1) 0;
  margin-bottom: var(--mj-space-1);
}
`;

/* Minimal built-in emoji dataset for demo purposes */
const BUILTIN_EMOJI = [
  { id: "😀", label: "grinning face", category: "Smileys" },
  { id: "😂", label: "face with tears of joy", category: "Smileys" },
  { id: "❤️", label: "red heart", category: "Symbols" },
  { id: "👍", label: "thumbs up", category: "People" },
  { id: "🎉", label: "party popper", category: "Activities" },
  { id: "🔥", label: "fire", category: "Travel" },
  { id: "⭐", label: "star", category: "Symbols" },
  { id: "🌟", label: "glowing star", category: "Symbols" },
  { id: "💯", label: "hundred points", category: "Symbols" },
  { id: "🚀", label: "rocket", category: "Travel" }
]

export class MjAssetPicker extends MjElement {
  static tagName = "mj-asset-picker";
  static styles = STYLES;
  static watched = ["value", "open", "disabled", "type", "columns", "cell-size", "multiple"];

  constructor() {
    super()
    this._value = ""
    this._selectedIds = new Set()
    this._assets = []
    this._filteredAssets = []
    this._activeCategory = null
    this._disposePosition = null
    this._disposeTrap = null
    this._searchTimer = null
    this._recentAssets = []
    this._triggerId = nextId("mj-ap-tr")
    this._popupId = nextId("mj-ap-popup")
    this._gridId = nextId("mj-ap-grid")
  }

  render() {
    const markup = `
      <button
        class="trigger"
        part="trigger"
        id="${this._triggerId}"
        type="button"
        aria-haspopup="dialog"
        aria-expanded="false"
        aria-label="Asset picker"
      >
        <slot name="trigger">
          <span class="trigger-value">&#9786;</span>
        </slot>
      </button>
      <div class="popup" part="popup" id="${this._popupId}" role="dialog" aria-label="Choose an asset">
        <div class="search-wrapper">
          <input
            class="search-input"
            part="search"
            type="text"
            placeholder="${this.getAttribute("search-placeholder") || "Search"}"
            aria-label="Search assets"
            autocomplete="off"
          />
        </div>
        <div class="body">
          <div class="category-nav" part="category-nav" role="tablist" aria-label="Categories"></div>
          <div class="asset-area" part="asset-area">
            <div
              class="asset-grid"
              part="asset-grid"
              id="${this._gridId}"
              role="grid"
              aria-label="Assets"
            ></div>
          </div>
        </div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._trigger = this.$(".trigger")
    this._popup = this.$(".popup")
    this._searchInput = this.$(".search-input")
    this._categoryNav = this.$(".category-nav")
    this._assetGrid = this.$(".asset-grid")
    this._assetArea = this.$(".asset-area")

    this.listen(this._trigger, "click", this._onTriggerClick.bind(this))
    this.listen(this._searchInput, "input", this._onSearch.bind(this))
    this.listen(document, "click", this._onDocClick.bind(this))

    this._loadAssets()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "value") {
      this._selectedIds.clear()
      if (newValue !== null && newValue.length > 0) {
        newValue.split(",").forEach((v) => this._selectedIds.add(v.trim()))
      }
      this._value = newValue || ""
    }
    if (name === "open") {
      this._syncOpen()
    }
    if (name === "columns" || name === "cell-size") {
      this._updateGridStyle()
    }
    return
  }

  _loadAssets() {
    const type = this.getAttribute("type") || "emoji"
    if (this._dataSource !== undefined && this._dataSource !== null) {
      return
    }
    if (type === "emoji") {
      this._assets = BUILTIN_EMOJI.slice()
    } else {
      this._assets = []
    }
    this._filteredAssets = this._assets.slice()
    if (this._assetGrid !== undefined) {
      this._renderGrid()
      this._renderCategories()
    }
    return
  }

  _updateGridStyle() {
    if (this._assetGrid === undefined) {
      return
    }
    const cols = this.getAttribute("columns") || "8"
    const cellSize = this.getAttribute("cell-size") || "2rem"
    this._assetGrid.style.gridTemplateColumns = `repeat(${cols}, ${cellSize})`
    return
  }

  _getCategories() {
    const cats = new Set()
    this._assets.forEach((a) => {
      if (a.category !== undefined) {
        cats.add(a.category)
      }
    })
    return Array.from(cats)
  }

  _renderCategories() {
    const cats = this._getCategories()
    if (cats.length === 0) {
      return
    }
    let html = ""
    cats.forEach((cat, idx) => {
      const icon = this._assets.find((a) => a.category === cat)
      html += `<button
        class="category-btn"
        part="category-button"
        type="button"
        role="tab"
        aria-selected="${idx === 0 ? "true" : "false"}"
        aria-label="${cat}"
        data-category="${cat}"
        title="${cat}"
      >${icon !== undefined ? icon.id : cat[0]}</button>`
    })
    this._categoryNav.innerHTML = html
    if (this._activeCategory === null && cats.length > 0) {
      this._activeCategory = cats[0]
    }
    const catBtns = this._categoryNav.querySelectorAll(".category-btn")
    catBtns.forEach((btn) => {
      this.listen(btn, "click", () => {
        catBtns.forEach((b) => b.setAttribute("aria-selected", "false"))
        btn.setAttribute("aria-selected", "true")
        this._activeCategory = btn.dataset.category
        this._filteredAssets = this._assets.filter((a) => a.category === this._activeCategory)
        this._renderGrid()
      })
    })
    return
  }

  _renderGrid() {
    if (this._filteredAssets.length === 0) {
      this._assetGrid.innerHTML = `<div class="no-results" part="no-results"><slot name="no-results">No results</slot></div>`
      return
    }

    const cols = parseInt(this.getAttribute("columns") || "8", 10)
    let html = `<div role="row">`
    this._filteredAssets.forEach((asset, idx) => {
      if (idx > 0 && idx % cols === 0) {
        html += `</div><div role="row">`
      }
      const selected = this._selectedIds.has(asset.id) ? ' aria-selected="true"' : ' aria-selected="false"'
      html += `<div role="gridcell">
        <button
          class="asset-cell"
          part="asset-cell"
          type="button"
          aria-label="${asset.label}"
          data-id="${asset.id}"
          ${selected}
          tabindex="${idx === 0 ? "0" : "-1"}"
        >${asset.id}</button>
      </div>`
    })
    html += `</div>`
    this._assetGrid.innerHTML = html

    const cells = this._assetGrid.querySelectorAll(".asset-cell")
    cells.forEach((cell) => {
      this.listen(cell, "click", this._onAssetClick.bind(this))
    })

    this.listen(this._assetGrid, "keydown", this._onGridKeydown.bind(this))
    return
  }

  _onSearch() {
    clearTimeout(this._searchTimer)
    this._searchTimer = setTimeout(() => {
      const q = this._searchInput.value.toLowerCase().trim()
      if (q.length === 0) {
        this._filteredAssets = this._activeCategory !== null
          ? this._assets.filter((a) => a.category === this._activeCategory)
          : this._assets.slice()
      } else {
        this._filteredAssets = this._assets.filter((a) =>
          a.label.toLowerCase().includes(q) || a.id.includes(q)
        )
      }
      this._renderGrid()
      announce(`${this._filteredAssets.length} results`, "polite")
      this.emit("mj-search", { query: q, results: this._filteredAssets })
    }, 150)
    return
  }

  _onAssetClick(event) {
    const btn = event.currentTarget
    const id = btn.dataset.id
    const asset = this._assets.find((a) => a.id === id)
    const isMultiple = this.hasAttribute("multiple")

    if (isMultiple === false) {
      this._selectedIds.clear()
      this._selectedIds.add(id)
    } else {
      if (this._selectedIds.has(id)) {
        this._selectedIds.delete(id)
      } else {
        this._selectedIds.add(id)
      }
    }

    const newValue = Array.from(this._selectedIds).join(",")
    this._value = newValue
    this.setAttribute("value", newValue)

    if (asset !== undefined) {
      this._updateTrigger(asset)
      this._trackRecent(asset)
    }

    this.emit("mj-change", {
      value: newValue,
      asset: asset || null,
      assets: Array.from(this._selectedIds).map((sid) => this._assets.find((a) => a.id === sid)).filter(Boolean)
    })

    this._renderGrid()

    if (isMultiple === false) {
      this._close()
    }
    return
  }

  _onGridKeydown(event) {
    const cells = Array.from(this._assetGrid.querySelectorAll(".asset-cell"))
    const count = cells.length
    if (count === 0) {
      return
    }

    const current = cells.findIndex((c) => c === document.activeElement || c === this.shadowRoot.activeElement)
    const cols = parseInt(this.getAttribute("columns") || "8", 10)

    let next = current
    if (event.key === "ArrowRight") {
      next = Math.min(current + 1, count - 1)
    } else if (event.key === "ArrowLeft") {
      next = Math.max(current - 1, 0)
    } else if (event.key === "ArrowDown") {
      next = Math.min(current + cols, count - 1)
    } else if (event.key === "ArrowUp") {
      next = Math.max(current - cols, 0)
    } else if (event.key === "Home") {
      next = 0
    } else if (event.key === "End") {
      next = count - 1
    } else if (event.ctrlKey === true && event.key === "Home") {
      next = 0
    } else if (event.ctrlKey === true && event.key === "End") {
      next = count - 1
    } else {
      return
    }

    event.preventDefault()
    cells.forEach((c) => { c.tabIndex = -1 })
    cells[next].tabIndex = 0
    cells[next].focus()
    return
  }

  _updateTrigger(asset) {
    const triggerValue = this._trigger.querySelector(".trigger-value")
    if (triggerValue !== null) {
      triggerValue.textContent = asset.id
    }
    this._trigger.setAttribute("aria-label", `Asset picker, current: ${asset.label}`)
    return
  }

  _trackRecent(asset) {
    this._recentAssets = this._recentAssets.filter((a) => a.id !== asset.id)
    this._recentAssets.unshift(asset)
    const maxRecents = parseInt(this.getAttribute("recents-count") || "18", 10)
    if (this._recentAssets.length > maxRecents) {
      this._recentAssets = this._recentAssets.slice(0, maxRecents)
    }
    try {
      const key = `mj-asset-picker-recents-${this.getAttribute("type") || "emoji"}`
      localStorage.setItem(key, JSON.stringify(this._recentAssets.map((a) => a.id)))
    } catch {
      /* localStorage unavailable */
    }
    return
  }

  _syncOpen() {
    const isOpen = this.hasAttribute("open")
    this._trigger.setAttribute("aria-expanded", isOpen === true ? "true" : "false")
    if (isOpen === true) {
      this._disposePosition = autoPosition(this._popup, this._trigger, { placement: "bottom-start" })
      this._disposeTrap = trapFocus(this._popup, this._searchInput)
    } else {
      if (this._disposePosition !== null) {
        this._disposePosition()
        this._disposePosition = null
      }
      if (this._disposeTrap !== null) {
        this._disposeTrap()
        this._disposeTrap = null
      }
    }
    return
  }

  _open() {
    if (this.hasAttribute("disabled")) {
      return
    }
    const proceed = this.emit("mj-open", {}, { cancelable: true })
    if (proceed === false) {
      return
    }
    this.setAttribute("open", "")
    return
  }

  _close() {
    if (this.hasAttribute("open") === false) {
      return
    }
    this.removeAttribute("open")
    this.emit("mj-close", {})
    return
  }

  _onTriggerClick() {
    if (this.hasAttribute("open")) {
      this._close()
    } else {
      this._open()
    }
    return
  }

  _onDocClick(event) {
    if (this.hasAttribute("open") === false) {
      return
    }
    const inside = event.composedPath().includes(this)
    if (inside === false) {
      this._close()
    }
    return
  }

  get open() {
    return this.hasAttribute("open")
  }

  set open(value) {
    if (value === true) {
      this._open()
    } else {
      this._close()
    }
    return
  }

  get value() {
    return this._value
  }

  set value(val) {
    this.setAttribute("value", val)
    return
  }

  get recentAssets() {
    return this._recentAssets.slice()
  }

  focus() {
    if (this._trigger !== undefined) {
      this._trigger.focus()
    }
    return
  }
}
