/*
 * mjfilterpanel.js
 *
 * <mj-filter-panel> -- faceted filter sidebar with applied chips, sort control,
 * collapsible accordion groups, and live filter-change events.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";
import { formatNumber } from "../core/intl.js";

const STYLES = `
:host {
  display: block;
}

:host([layout="sidebar"]) {
  width: var(--mj-filter-panel-width, 280px);
}

:host([collapsible]:not([open])) .panel-body {
  display: none;
}

.panel-root {
  background: var(--mj-surface);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-md);
  overflow: hidden;
}

:host([layout="sidebar"]) .panel-root {
  border: none;
  border-radius: 0;
  border-inline-end: 1px solid var(--mj-border);
}

.panel-toggle-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: var(--mj-space-3) var(--mj-space-4);
  background: transparent;
  border: none;
  border-bottom: 1px solid var(--mj-border);
  font: inherit;
  font-weight: var(--mj-font-weight-medium);
  cursor: pointer;
  color: var(--mj-text);
}

:host(:not([collapsible])) .panel-toggle-btn { display: none; }

.chips-bar {
  display: flex;
  flex-wrap: wrap;
  gap: var(--mj-filter-chips-gap, var(--mj-space-1));
  padding: var(--mj-space-2) var(--mj-space-3);
  align-items: center;
  border-bottom: 1px solid var(--mj-border);
}

.chips-bar[hidden] { display: none; }

.chip {
  display: inline-flex;
  align-items: center;
  gap: var(--mj-space-1);
  padding: var(--mj-space-1) var(--mj-space-2);
  background: var(--mj-bg-muted);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-pill);
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text);
}

.chip-remove {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0 0 0 var(--mj-space-1);
  color: var(--mj-text-muted);
  font-size: var(--mj-font-size-xs);
  line-height: 1;
}

.chip-remove:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  border-radius: var(--mj-radius-sm);
}

.clear-all-btn {
  margin-inline-start: auto;
  background: none;
  border: none;
  cursor: pointer;
  font: inherit;
  font-size: var(--mj-font-size-xs);
  color: var(--mj-accent);
  padding: var(--mj-space-1);
}

.sort-control {
  padding: var(--mj-space-2) var(--mj-space-3);
  border-bottom: 1px solid var(--mj-border);
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
}

.sort-select {
  flex: 1;
  padding: var(--mj-space-1) var(--mj-space-2);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-sm);
  background: var(--mj-surface);
  font: inherit;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
}

.sort-direction-btn {
  padding: var(--mj-space-1);
  background: none;
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-sm);
  cursor: pointer;
  color: var(--mj-text-muted);
  line-height: 1;
}

.filter-groups {
  display: flex;
  flex-direction: column;
  gap: var(--mj-filter-group-gap, var(--mj-space-2));
}

.filter-group {
  border-bottom: 1px solid var(--mj-border);
}

.group-header-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: var(--mj-space-3) var(--mj-space-4);
  background: transparent;
  border: none;
  font: inherit;
  font-weight: var(--mj-font-weight-medium);
  font-size: var(--mj-font-size-sm);
  cursor: pointer;
  color: var(--mj-text);
  text-align: start;
}

.group-header-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: calc(-1 * var(--mj-focus-ring-offset));
}

.group-badge {
  background: var(--mj-filter-count-badge-bg, var(--mj-bg-muted));
  color: var(--mj-accent);
  font-size: var(--mj-font-size-xs);
  padding: 1px var(--mj-space-2);
  border-radius: var(--mj-radius-pill);
  font-weight: var(--mj-font-weight-regular);
}

.group-body {
  padding: var(--mj-space-2) var(--mj-space-4) var(--mj-space-3);
}

.group-body[hidden] { display: none; }

.option-item {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  padding: var(--mj-space-1) 0;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
}

.option-item input {
  accent-color: var(--mj-accent);
}

.result-count {
  padding: var(--mj-space-2) var(--mj-space-3);
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
  border-top: 1px solid var(--mj-border);
  text-align: center;
}

.result-count[hidden] { display: none; }
`;

export class MjFilterPanel extends MjElement {
  static tagName = "mj-filter-panel";
  static styles = STYLES;
  static watched = ["layout", "collapsible", "open", "label", "total-count", "sort-label"];

  constructor() {
    super()
    this._filterConfig = []
    this._value = { sort: { field: "", direction: "asc" }, filters: {} }
    this._groupExpanded = {}
  }

  render() {
    const label = this.getAttribute("label") || "Filters"
    const layout = this.getAttribute("layout") || "sidebar"
    const role = layout === "sidebar" ? `aside` : `div`
    const markup = `
      <${role} class="panel-root" part="root" aria-label="${label}">
        <slot name="header"></slot>
        <button class="panel-toggle-btn" part="panel-toggle"
                aria-expanded="true">
          <span>${label}</span>
          <span aria-hidden="true">&#8963;</span>
        </button>
        <div class="panel-body">
          <div class="chips-bar" part="chips-bar" hidden
               aria-label="Applied filters"></div>
          <div class="sort-control" part="sort-control"></div>
          <div class="filter-groups" part="groups"></div>
          <div class="result-count" part="result-count" hidden
               aria-live="polite"></div>
        </div>
        <slot name="footer"></slot>
      </${role}>
    `
    return markup
  }

  afterRender() {
    this._chipsBar = this.$(".chips-bar")
    this._sortControl = this.$(".sort-control")
    this._groupsEl = this.$(".filter-groups")
    this._resultCount = this.$(".result-count")
    this._toggleBtn = this.$(".panel-toggle-btn")

    if (this._toggleBtn !== null) {
      this.listen(this._toggleBtn, "click", this._onPanelToggle.bind(this))
    }

    this._renderSort()
    this._renderGroups()
    this._renderCount()
    return
  }

  _onPanelToggle() {
    const open = this.hasAttribute("open")
    if (open === true) {
      this.removeAttribute("open")
    } else {
      this.setAttribute("open", "")
    }
    this.emit("mj-panel-toggle", { open: !open })
    return
  }

  _renderSort() {
    if (this._sortControl === null) {
      return
    }
    const sortLabel = this.getAttribute("sort-label") || "Sort by"
    this._sortControl.innerHTML = `
      <label class="sort-label" style="font-size:var(--mj-font-size-xs);color:var(--mj-text-muted);">
        ${sortLabel}
      </label>
      <select class="sort-select" part="sort-select" aria-label="${sortLabel}">
        <option value="">Default</option>
      </select>
      <button class="sort-direction-btn" part="sort-direction"
              aria-label="Toggle sort direction" title="Toggle sort direction">&#8597;</button>
    `
    const sel = this._sortControl.querySelector(".sort-select")
    const dirBtn = this._sortControl.querySelector(".sort-direction-btn")
    if (sel !== null) {
      this.listen(sel, "change", (e) => {
        this._value.sort.field = e.target.value
        this._emitChange("sort")
      })
    }
    if (dirBtn !== null) {
      this.listen(dirBtn, "click", () => {
        this._value.sort.direction = this._value.sort.direction === "asc" ? "desc" : "asc"
        this._emitChange("sort")
      })
    }
    return
  }

  _renderGroups() {
    if (this._groupsEl === null) {
      return
    }
    this._groupsEl.innerHTML = ""

    for (let i = 0; i < this._filterConfig.length; i = i + 1) {
      const group = this._filterConfig[i]
      const groupId = group.id || nextId("mj-fg")
      const bodyId = nextId("mj-fg-body")
      const expanded = this._groupExpanded[groupId] !== false
      const selectedCount = this._countSelected(groupId)
      const badgeHtml = selectedCount > 0
        ? `<span class="group-badge" aria-label="${selectedCount} selected">${selectedCount}</span>`
        : ""

      const groupEl = document.createElement("div")
      groupEl.className = "filter-group"
      groupEl.setAttribute("part", "group")
      groupEl.setAttribute("data-group-id", groupId)
      groupEl.innerHTML = `
        <button class="group-header-btn" part="group-header"
                aria-expanded="${expanded}"
                aria-controls="${bodyId}">
          <span>${group.label}</span>
          ${badgeHtml}
        </button>
        <div class="group-body" part="group-body" id="${bodyId}"
             ${expanded ? "" : "hidden"}>
          ${this._renderGroupBody(group, groupId)}
        </div>
      `
      const btn = groupEl.querySelector(".group-header-btn")
      if (btn !== null) {
        this.listen(btn, "click", this._onGroupToggle.bind(this, groupId, btn, bodyId))
      }
      this._listenGroupOptions(groupEl, group, groupId)
      this._groupsEl.appendChild(groupEl)
    }
    return
  }

  _renderGroupBody(group, groupId) {
    const type = group.type || "checkbox"
    const options = group.options || []
    const currentValues = this._value.filters[groupId] || []

    if (options.length === 0) {
      return `<p style="font-size:var(--mj-font-size-xs);color:var(--mj-text-muted);">No options available</p>`
    }

    let html = ""
    for (let i = 0; i < options.length; i = i + 1) {
      const opt = options[i]
      const optId = nextId("mj-fo")
      const checked = Array.isArray(currentValues) && currentValues.indexOf(opt.value) >= 0
      const inputType = type === "radio" ? "radio" : "checkbox"
      const name = type === "radio" ? `mj-filter-${groupId}` : undefined
      const nameAttr = name !== undefined ? `name="${name}"` : ""
      html += `
        <label class="option-item" for="${optId}">
          <input type="${inputType}" id="${optId}" ${nameAttr}
                 value="${opt.value}" ${checked ? "checked" : ""}
                 data-group="${groupId}" data-value="${opt.value}">
          ${opt.label}
        </label>
      `
    }
    return html
  }

  _onGroupToggle(groupId, btn, bodyId) {
    const expanded = btn.getAttribute("aria-expanded") === "true"
    const newExpanded = !expanded
    btn.setAttribute("aria-expanded", String(newExpanded))
    this._groupExpanded[groupId] = newExpanded
    const body = this._groupsEl.querySelector(`#${bodyId}`)
    if (body !== null) {
      body.hidden = !newExpanded
    }
    return
  }

  _listenGroupOptions(groupEl, group, groupId) {
    const inputs = groupEl.querySelectorAll("input")
    for (let i = 0; i < inputs.length; i = i + 1) {
      const input = inputs[i]
      this.listen(input, "change", this._onOptionChange.bind(this, groupId, group.type))
    }
    return
  }

  _onOptionChange(groupId, type) {
    const groupEl = this._groupsEl.querySelector(`[data-group-id="${groupId}"]`)
    if (groupEl === null) {
      return
    }
    const inputs = groupEl.querySelectorAll("input:checked")
    const selected = []
    for (let i = 0; i < inputs.length; i = i + 1) {
      selected.push(inputs[i].getAttribute("data-value"))
    }

    if (type === "radio") {
      this._value.filters[groupId] = selected.length > 0 ? selected[0] : null
    } else {
      this._value.filters[groupId] = selected
    }

    this._renderChips()
    this._emitChange(groupId)
    return
  }

  _emitChange(changedGroup) {
    this.emit("mj-filter-change", {
      value: this._value,
      changedGroup: changedGroup
    })
    return
  }

  _renderChips() {
    if (this._chipsBar === null) {
      return
    }
    const applied = this.appliedFilters
    if (applied.length === 0) {
      this._chipsBar.hidden = true
      return
    }

    this._chipsBar.hidden = false
    let html = ""
    for (let i = 0; i < applied.length; i = i + 1) {
      const f = applied[i]
      html += `
        <span class="chip">
          ${f.label}
          <button class="chip-remove" aria-label="Remove ${f.label}"
                  data-group="${f.groupId}" data-value="${f.value}">&#x2715;</button>
        </span>
      `
    }
    html += `<button class="clear-all-btn" part="clear-all">Clear all</button>`
    this._chipsBar.innerHTML = html

    const clearBtn = this._chipsBar.querySelector(".clear-all-btn")
    if (clearBtn !== null) {
      this.listen(clearBtn, "click", this._onClearAll.bind(this))
    }
    const removebtns = this._chipsBar.querySelectorAll(".chip-remove")
    for (let i = 0; i < removebtns.length; i = i + 1) {
      const btn = removebtns[i]
      this.listen(btn, "click", this._onChipRemove.bind(this, btn))
    }
    return
  }

  _onChipRemove(btn) {
    const groupId = btn.getAttribute("data-group")
    const value = btn.getAttribute("data-value")
    const current = this._value.filters[groupId]
    if (Array.isArray(current)) {
      this._value.filters[groupId] = current.filter((v) => v !== value)
    } else {
      this._value.filters[groupId] = null
    }
    this.emit("mj-chip-remove", { groupId: groupId, value: value })
    this._renderGroups()
    this._renderChips()
    this._emitChange(groupId)
    return
  }

  _onClearAll() {
    this._value.filters = {}
    this._renderGroups()
    this._renderChips()
    this.emit("mj-filter-clear", {})
    this._emitChange("clear")
    return
  }

  _renderCount() {
    if (this._resultCount === null) {
      return
    }
    const total = this.getAttribute("total-count")
    if (total === null) {
      this._resultCount.hidden = true
      return
    }
    const count = parseInt(total, 10)
    this._resultCount.hidden = false
    this._resultCount.textContent = `Showing ${formatNumber(isNaN(count) ? 0 : count)} results`
    return
  }

  _countSelected(groupId) {
    const v = this._value.filters[groupId]
    if (Array.isArray(v)) {
      return v.length
    }
    return v !== null && v !== undefined && v !== "" ? 1 : 0
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "total-count") {
      this._renderCount()
      const count = parseInt(newValue || "0", 10)
      announce(`Showing ${formatNumber(isNaN(count) ? 0 : count)} results`, "polite")
    }
    if (name === "open" && this._toggleBtn !== null) {
      this._toggleBtn.setAttribute("aria-expanded", String(newValue !== null))
    }
    return
  }

  get filterConfig() {
    return this._filterConfig
  }

  set filterConfig(config) {
    this._filterConfig = Array.isArray(config) ? config : []
    if (this._groupsEl !== null) {
      this._renderGroups()
    }
    return
  }

  get value() {
    return this._value
  }

  set value(v) {
    this._value = v !== null && v !== undefined ? v : { sort: { field: "", direction: "asc" }, filters: {} }
    if (this._groupsEl !== null) {
      this._renderGroups()
      this._renderChips()
    }
    return
  }

  get appliedFilters() {
    const result = []
    const groupIds = Object.keys(this._value.filters)
    for (let i = 0; i < groupIds.length; i = i + 1) {
      const groupId = groupIds[i]
      const v = this._value.filters[groupId]
      const groupDef = this._filterConfig.find((g) => g.id === groupId)
      const groupLabel = groupDef !== undefined ? groupDef.label : groupId

      if (Array.isArray(v)) {
        for (let j = 0; j < v.length; j = j + 1) {
          result.push({ groupId: groupId, label: `${groupLabel}: ${v[j]}`, value: v[j] })
        }
      } else if (v !== null && v !== undefined && v !== "") {
        result.push({ groupId: groupId, label: `${groupLabel}: ${v}`, value: v })
      }
    }
    return result
  }
}
