/*
 * mjfilterpanel.js
 *
 * <mj-filter-panel> -- faceted filter panel with applied chips, sort control,
 * collapsible accordion groups, and live filter-change events.
 *
 * Facet data is untrusted (group and option labels are often built from
 * user-generated values such as tags or author names), so the groups, the
 * chips and the sort options are created with DOM APIs and text nodes.
 *
 *   filterConfig   [{ id, label, type: "checkbox" | "radio",
 *                     options: [{ value, label, count? }] }]
 *   sortOptions    [{ value, label }]; the sort control is shown only when
 *                  there is something to sort by
 *   value          { sort: { field, direction }, filters: { [groupId]: ... } }
 *                  -- an array of option values for a checkbox group, a
 *                  single option value (or null) for a radio group. Option
 *                  values keep their type; they are never read back from an
 *                  attribute string.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { formatNumber, t } from "../core/intl.js";

const STYLES = `
:host {
  display: block;
}

:host([layout="sidebar"]) {
  inline-size: var(--mj-filter-panel-width, 280px);
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
  inline-size: 100%;
  padding: var(--mj-space-3) var(--mj-space-4);
  background: transparent;
  border: none;
  border-block-end: 1px solid var(--mj-border);
  font: inherit;
  font-weight: var(--mj-font-weight-medium);
  cursor: pointer;
  color: var(--mj-text);
}

.panel-toggle-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: calc(-1 * var(--mj-focus-ring-width));
}

.panel-toggle-btn[aria-expanded="false"] .panel-toggle-icon {
  rotate: 180deg;
}

:host(:not([collapsible])) .panel-toggle-btn { display: none; }

.chips-bar {
  display: flex;
  flex-wrap: wrap;
  gap: var(--mj-filter-chips-gap, var(--mj-space-1));
  padding: var(--mj-space-2) var(--mj-space-3);
  align-items: center;
  border-block-end: 1px solid var(--mj-border);
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
  overflow-wrap: anywhere;
}

.chip-remove {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  padding-inline-start: var(--mj-space-1);
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

.clear-all-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  border-radius: var(--mj-radius-sm);
}

.sort-control {
  padding: var(--mj-space-2) var(--mj-space-3);
  border-block-end: 1px solid var(--mj-border);
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
}

.sort-control[hidden] { display: none; }

.sort-label {
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
}

.sort-select {
  flex: 1;
  min-inline-size: 0;
  padding: var(--mj-space-1) var(--mj-space-2);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-sm);
  background: var(--mj-surface);
  font: inherit;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
}

.sort-direction-btn {
  padding: var(--mj-space-1) var(--mj-space-2);
  background: none;
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-sm);
  cursor: pointer;
  color: var(--mj-text);
  font: inherit;
  line-height: 1;
}

.sort-direction-btn[disabled] {
  opacity: 0.45;
  cursor: not-allowed;
}

.sort-select:focus-visible,
.sort-direction-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.filter-groups {
  display: flex;
  flex-direction: column;
  gap: var(--mj-filter-group-gap, var(--mj-space-2));
}

.filter-group {
  border-block-end: 1px solid var(--mj-border);
}

/* Inline layout: the groups sit side by side and wrap. */
:host([layout="inline"]) .filter-groups {
  flex-direction: row;
  flex-wrap: wrap;
  align-items: flex-start;
  padding: var(--mj-space-2);
}

:host([layout="inline"]) .filter-group {
  flex: 0 1 auto;
  min-inline-size: 160px;
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-md);
}

.group-header-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--mj-space-2);
  inline-size: 100%;
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
  outline-offset: calc(-1 * var(--mj-focus-ring-width));
}

.group-badge {
  background: var(--mj-filter-count-badge-bg, var(--mj-bg-muted));
  color: var(--mj-accent);
  font-size: var(--mj-font-size-xs);
  padding: 1px var(--mj-space-2);
  border-radius: var(--mj-radius-pill);
  font-weight: var(--mj-font-weight-regular);
}

.group-badge[hidden] { display: none; }

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
  overflow-wrap: anywhere;
}

.option-item input {
  accent-color: var(--mj-accent);
  flex-shrink: 0;
}

.option-count {
  margin-inline-start: auto;
  color: var(--mj-text-muted);
  font-size: var(--mj-font-size-xs);
}

.no-options {
  margin: 0;
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
}

.result-count {
  padding: var(--mj-space-2) var(--mj-space-3);
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
  border-block-start: 1px solid var(--mj-border);
  text-align: center;
}

.result-count[hidden] { display: none; }
`;

/* Option values are compared by their text, so 5 and "5" select the same option. */
function sameValue(first, second) {
  const same = String(first) === String(second)
  return same
}

function isBlank(value) {
  const blank = value === null || value === undefined || value === ""
  return blank
}

/*
 * Bring an assigned filter state into the full shape, so later code never
 * meets a missing `sort` or `filters`. Arrays are copied; the caller's
 * object is not kept.
 */
function normaliseState(state) {
  const normalised = { sort: { field: "", direction: "asc" }, filters: {} }

  if (state !== null && state !== undefined && typeof state === "object") {
    const sort = state.sort
    if (sort !== null && sort !== undefined && typeof sort === "object") {
      normalised.sort.field = isBlank(sort.field) === true ? "" : String(sort.field)
      normalised.sort.direction = sort.direction === "desc" ? "desc" : "asc"
    }

    const filters = state.filters
    if (filters !== null && filters !== undefined && typeof filters === "object") {
      const groupIds = Object.keys(filters)
      for (let index = 0; index < groupIds.length; index = index + 1) {
        const groupId = groupIds[index]
        const selection = filters[groupId]
        normalised.filters[groupId] = Array.isArray(selection) === true ? selection.slice() : selection
      }
    }
  }

  return normalised
}

export class MjFilterPanel extends MjElement {
  static tagName = "mj-filter-panel";
  static styles = STYLES;
  static watched = ["layout", "collapsible", "open", "label", "total-count", "sort-label"];

  constructor() {
    super()

    /* Shadow references; null until the first render. */
    this._rootEl = null
    this._toggleBtn = null
    this._toggleLabel = null
    this._chipsBar = null
    this._sortControl = null
    this._sortLabelEl = null
    this._sortSelect = null
    this._sortDirectionBtn = null
    this._groupsEl = null
    this._resultCount = null

    this._filterConfig = []
    this._sortOptions = []
    this._value = normaliseState(null)

    /* Ids for the groups, by config index: the config's own id or a generated one. */
    this._groupIds = []
    this._groupExpanded = {}

    /* The applied filters the chips were last rendered from, by chip index. */
    this._renderedChips = []

    this._panelId = nextId("mj-filter-panel")
  }

  render() {
    const markup = `
      <div class="panel-root" part="root">
        <slot name="header"></slot>
        <button class="panel-toggle-btn" part="panel-toggle" type="button" aria-expanded="true">
          <span class="panel-toggle-label"></span>
          <span class="panel-toggle-icon" aria-hidden="true">&#8963;</span>
        </button>
        <div class="panel-body">
          <div class="chips-bar" part="chips-bar" role="group" hidden></div>
          <div class="sort-control" part="sort-control" hidden>
            <label class="sort-label"></label>
            <select class="sort-select" part="sort-select"></select>
            <button class="sort-direction-btn" part="sort-direction" type="button"></button>
          </div>
          <div class="filter-groups" part="groups"></div>
          <div class="result-count" part="result-count" role="status" hidden></div>
        </div>
        <slot name="footer"></slot>
      </div>
    `
    return markup
  }

  afterRender() {
    this._rootEl = this.$(".panel-root")
    this._toggleBtn = this.$(".panel-toggle-btn")
    this._toggleLabel = this.$(".panel-toggle-label")
    this._chipsBar = this.$(".chips-bar")
    this._sortControl = this.$(".sort-control")
    this._sortLabelEl = this.$(".sort-label")
    this._sortSelect = this.$(".sort-select")
    this._sortDirectionBtn = this.$(".sort-direction-btn")
    this._groupsEl = this.$(".filter-groups")
    this._resultCount = this.$(".result-count")

    this._chipsBar.setAttribute("aria-label", t("mj.filterPanel.appliedFilters"))

    const sortSelectId = `${this._panelId}-sort`
    this._sortSelect.id = sortSelectId
    this._sortLabelEl.setAttribute("for", sortSelectId)

    /*
     * One listener per stable container: the groups and chips are rebuilt
     * often, and listeners on the rebuilt nodes would pile up.
     */
    this.listen(this._toggleBtn, "click", this._onPanelToggle.bind(this))
    this.listen(this._sortSelect, "change", this._onSortFieldChange.bind(this))
    this.listen(this._sortDirectionBtn, "click", this._onSortDirectionClick.bind(this))
    this.listen(this._groupsEl, "click", this._onGroupsClick.bind(this))
    this.listen(this._groupsEl, "change", this._onGroupsChange.bind(this))
    this.listen(this._chipsBar, "click", this._onChipsClick.bind(this))

    this._syncRoot()
    this._renderSort()
    this._renderGroups()
    this._renderChips()
    this._renderCount()
    return
  }

  /* ----- root: role, name and collapsed state ----- */

  _syncRoot() {
    if (this._rootEl === undefined || this._rootEl === null) {
      return
    }

    const label = this.getAttribute("label") || t("mj.filterPanel.label")
    const inline = this.getAttribute("layout") === "inline"

    /* A sidebar is a complementary landmark; an inline panel is a plain group. */
    this._rootEl.setAttribute("role", inline === true ? "group" : "complementary")
    this._rootEl.setAttribute("aria-label", label)
    this._toggleLabel.textContent = label

    /* Without `collapsible` the panel is always expanded, whatever `open` says. */
    const expanded = this.hasAttribute("collapsible") === false || this.hasAttribute("open") === true
    this._toggleBtn.setAttribute("aria-expanded", expanded === true ? "true" : "false")
    return
  }

  _onPanelToggle() {
    const open = this.hasAttribute("open")
    this.reflectBoolean("open", open === false)
    this.emit("mj-panel-toggle", { open: open === false })
    return
  }

  /* ----- sort ----- */

  _directionLabel() {
    const label = this._value.sort.direction === "desc" ? t("mj.filterPanel.sortDescending") : t("mj.filterPanel.sortAscending")
    return label
  }

  /* Rebuild the sort control from `sortOptions` and show the current `value.sort`. */
  _renderSort() {
    if (this._sortControl === undefined || this._sortControl === null) {
      return
    }

    const sortLabel = this.getAttribute("sort-label") || t("mj.filterPanel.sortBy")
    this._sortLabelEl.textContent = sortLabel

    this._sortSelect.textContent = ""
    const defaultOption = document.createElement("option")
    defaultOption.value = ""
    defaultOption.textContent = t("mj.filterPanel.defaultSort")
    this._sortSelect.appendChild(defaultOption)

    for (let index = 0; index < this._sortOptions.length; index = index + 1) {
      const entry = this._sortOptions[index]
      const option = document.createElement("option")
      option.value = String(entry.value)
      option.textContent = isBlank(entry.label) === true ? String(entry.value) : String(entry.label)
      this._sortSelect.appendChild(option)
    }

    /* Nothing to sort by: the control would only offer "Default". */
    this._sortControl.hidden = this._sortOptions.length === 0

    this._syncSort()
    return
  }

  /* Show `value.sort` in the select and on the direction button. */
  _syncSort() {
    if (this._sortSelect === undefined || this._sortSelect === null) {
      return
    }

    const sort = this._value.sort
    this._sortSelect.value = sort.field
    if (this._sortSelect.value !== sort.field) {
      /* The field is not among the options; the select falls back to Default. */
      this._sortSelect.value = ""
    }

    const descending = sort.direction === "desc"
    this._sortDirectionBtn.textContent = descending === true ? "↓" : "↑"
    this._sortDirectionBtn.setAttribute("aria-label", this._directionLabel())
    this._sortDirectionBtn.setAttribute("title", this._directionLabel())
    /* A direction means nothing while no sort field is chosen. */
    this._sortDirectionBtn.disabled = sort.field === ""
    return
  }

  _onSortFieldChange() {
    this._value.sort.field = this._sortSelect.value
    this._syncSort()
    this._emitChange("sort")
    return
  }

  _onSortDirectionClick() {
    this._value.sort.direction = this._value.sort.direction === "asc" ? "desc" : "asc"
    this._syncSort()
    this._emitChange("sort")
    return
  }

  /* ----- groups ----- */

  _groupIndexOfId(groupId) {
    const index = this._groupIds.indexOf(groupId)
    return index
  }

  _groupType(group) {
    const type = group.type === "radio" ? "radio" : "checkbox"
    return type
  }

  _groupOptions(group) {
    const options = Array.isArray(group.options) === true ? group.options : []
    return options
  }

  /* True when `option` is part of the group's current selection. */
  _isSelected(group, groupId, option) {
    const selection = this._value.filters[groupId]
    let selected = false

    if (Array.isArray(selection) === true) {
      selected = selection.some((entry) => sameValue(entry, option.value))
    } else if (isBlank(selection) === false) {
      /* A radio group (or a single programmatic value) holds a scalar. */
      selected = sameValue(selection, option.value)
    }

    return selected
  }

  _countSelected(groupId) {
    const selection = this._value.filters[groupId]
    let count = 0
    if (Array.isArray(selection) === true) {
      count = selection.length
    } else if (isBlank(selection) === false) {
      count = 1
    }
    return count
  }

  _renderGroups() {
    if (this._groupsEl === undefined || this._groupsEl === null) {
      return
    }

    this._groupsEl.textContent = ""

    for (let index = 0; index < this._filterConfig.length; index = index + 1) {
      const group = this._filterConfig[index]
      const groupId = this._groupIds[index]
      const expanded = this._groupExpanded[groupId] !== false
      const bodyId = `${this._panelId}-group-${index}`

      const groupEl = document.createElement("div")
      groupEl.className = "filter-group"
      groupEl.setAttribute("part", "group")
      groupEl.setAttribute("data-group-index", String(index))
      groupEl.setAttribute("data-group-id", groupId)

      const header = document.createElement("button")
      header.type = "button"
      header.className = "group-header-btn"
      header.setAttribute("part", "group-header")
      header.setAttribute("aria-expanded", expanded === true ? "true" : "false")
      header.setAttribute("aria-controls", bodyId)

      const title = document.createElement("span")
      title.textContent = isBlank(group.label) === true ? groupId : String(group.label)
      header.appendChild(title)

      const badge = document.createElement("span")
      badge.className = "group-badge"
      header.appendChild(badge)

      const body = document.createElement("div")
      body.className = "group-body"
      body.setAttribute("part", "group-body")
      body.id = bodyId
      body.hidden = expanded === false
      this._fillGroupBody(body, group, groupId, index)

      groupEl.appendChild(header)
      groupEl.appendChild(body)
      this._groupsEl.appendChild(groupEl)

      this._syncGroupBadge(groupEl, groupId)
    }
    return
  }

  _fillGroupBody(body, group, groupId, groupIndex) {
    const options = this._groupOptions(group)
    const inputType = this._groupType(group)

    if (options.length === 0) {
      const empty = document.createElement("p")
      empty.className = "no-options"
      empty.textContent = t("mj.filterPanel.noOptions")
      body.appendChild(empty)
      return
    }

    for (let index = 0; index < options.length; index = index + 1) {
      const option = options[index]

      const row = document.createElement("label")
      row.className = "option-item"

      const input = document.createElement("input")
      input.type = inputType
      if (inputType === "radio") {
        input.name = `${this._panelId}-group-${groupIndex}`
      }
      /* The index leads back to the option object, so its value keeps its type. */
      input.setAttribute("data-option-index", String(index))
      input.checked = this._isSelected(group, groupId, option)
      row.appendChild(input)

      const text = document.createElement("span")
      text.textContent = isBlank(option.label) === true ? String(option.value) : String(option.label)
      row.appendChild(text)

      if (typeof option.count === "number") {
        const count = document.createElement("span")
        count.className = "option-count"
        count.textContent = formatNumber(option.count)
        row.appendChild(count)
      }

      body.appendChild(row)
    }
    return
  }

  /* Show how many options of a group are selected on its header. */
  _syncGroupBadge(groupEl, groupId) {
    const badge = groupEl.querySelector(".group-badge")
    if (badge !== null) {
      const selectedCount = this._countSelected(groupId)
      badge.hidden = selectedCount === 0
      badge.textContent = selectedCount > 0 ? String(selectedCount) : ""
      if (selectedCount > 0) {
        badge.setAttribute("aria-label", t("mj.filterPanel.selectedCount", { count: selectedCount }))
      } else {
        badge.removeAttribute("aria-label")
      }
    }
    return
  }

  _groupElementOf(node) {
    const groupEl = node instanceof Element ? node.closest(".filter-group") : null
    return groupEl
  }

  /* Expand / collapse a group from its header. */
  _onGroupsClick(event) {
    const target = event.target
    const header = target instanceof Element ? target.closest(".group-header-btn") : null
    const groupEl = header !== null ? this._groupElementOf(header) : null
    if (groupEl === null) {
      return
    }

    const groupId = this._groupIds[parseInt(groupEl.getAttribute("data-group-index"), 10)]
    const expanded = header.getAttribute("aria-expanded") !== "true"
    header.setAttribute("aria-expanded", expanded === true ? "true" : "false")
    this._groupExpanded[groupId] = expanded

    const body = groupEl.querySelector(".group-body")
    if (body !== null) {
      body.hidden = expanded === false
    }
    return
  }

  /* An option was checked or unchecked: read the group's selection back. */
  _onGroupsChange(event) {
    const groupEl = this._groupElementOf(event.target)
    if (groupEl === null) {
      return
    }

    const groupIndex = parseInt(groupEl.getAttribute("data-group-index"), 10)
    const group = this._filterConfig[groupIndex]
    const groupId = this._groupIds[groupIndex]
    if (group === undefined) {
      return
    }

    const options = this._groupOptions(group)
    const selected = []
    const checkedInputs = groupEl.querySelectorAll("input:checked")
    for (let index = 0; index < checkedInputs.length; index = index + 1) {
      const option = options[parseInt(checkedInputs[index].getAttribute("data-option-index"), 10)]
      if (option !== undefined) {
        selected.push(option.value)
      }
    }

    if (this._groupType(group) === "radio") {
      this._value.filters[groupId] = selected.length > 0 ? selected[0] : null
    } else {
      this._value.filters[groupId] = selected
    }

    this._syncGroupBadge(groupEl, groupId)
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

  /* ----- applied-filter chips ----- */

  _renderChips() {
    if (this._chipsBar === undefined || this._chipsBar === null) {
      return
    }

    const applied = this.appliedFilters
    this._renderedChips = applied
    this._chipsBar.textContent = ""
    this._chipsBar.hidden = applied.length === 0

    for (let index = 0; index < applied.length; index = index + 1) {
      const filter = applied[index]

      const chip = document.createElement("span")
      chip.className = "chip"

      const text = document.createElement("span")
      text.textContent = filter.label
      chip.appendChild(text)

      const remove = document.createElement("button")
      remove.type = "button"
      remove.className = "chip-remove"
      remove.setAttribute("aria-label", t("mj.filterPanel.removeFilter", { label: filter.label }))
      remove.setAttribute("data-chip-index", String(index))
      remove.textContent = "✕"
      chip.appendChild(remove)

      this._chipsBar.appendChild(chip)
    }

    if (applied.length > 0) {
      const clear = document.createElement("button")
      clear.type = "button"
      clear.className = "clear-all-btn"
      clear.setAttribute("part", "clear-all")
      clear.textContent = t("mj.filterPanel.clearAll")
      this._chipsBar.appendChild(clear)
    }
    return
  }

  _onChipsClick(event) {
    const target = event.target
    if (!(target instanceof Element)) {
      return
    }

    const remove = target.closest(".chip-remove")
    if (remove !== null) {
      this._removeChip(parseInt(remove.getAttribute("data-chip-index"), 10))
    } else if (target.closest(".clear-all-btn") !== null) {
      this._clearAll()
    }
    return
  }

  /*
   * After the chips were rebuilt, put focus where the removed control was:
   * on the chip that took its place, else on the last chip, else -- with no
   * chips left -- on the header of the group the filter belonged to.
   */
  _focusAfterChipChange(chipIndex, groupId) {
    const removeButtons = this._chipsBar.querySelectorAll(".chip-remove")
    let focusTarget = null

    if (removeButtons.length > 0) {
      const index = Math.min(chipIndex, removeButtons.length - 1)
      focusTarget = removeButtons[index]
    } else {
      const groupIndex = groupId !== null ? this._groupIndexOfId(groupId) : -1
      const headers = this._groupsEl.querySelectorAll(".group-header-btn")
      if (groupIndex >= 0 && groupIndex < headers.length) {
        focusTarget = headers[groupIndex]
      } else if (headers.length > 0) {
        focusTarget = headers[0]
      }
    }

    if (focusTarget !== null) {
      focusTarget.focus()
    }
    return
  }

  _removeChip(chipIndex) {
    const filter = this._renderedChips[chipIndex]
    if (filter === undefined) {
      return
    }

    const groupId = filter.groupId
    const current = this._value.filters[groupId]
    if (Array.isArray(current) === true) {
      this._value.filters[groupId] = current.filter((entry) => sameValue(entry, filter.value) === false)
    } else {
      this._value.filters[groupId] = null
    }

    this._renderGroups()
    this._renderChips()
    this._focusAfterChipChange(chipIndex, groupId)

    this.emit("mj-chip-remove", { groupId: groupId, value: filter.value })
    this._emitChange(groupId)
    return
  }

  _clearAll() {
    this._value.filters = {}
    this._renderGroups()
    this._renderChips()
    this._focusAfterChipChange(0, null)

    this.emit("mj-filter-clear", {})
    this._emitChange("clear")
    return
  }

  /* ----- result count ----- */

  _renderCount() {
    if (this._resultCount === undefined || this._resultCount === null) {
      return
    }

    const total = this.getAttribute("total-count")
    if (total === null) {
      this._resultCount.hidden = true
      this._resultCount.textContent = ""
    } else {
      const parsed = parseInt(total, 10)
      const count = Number.isFinite(parsed) === true ? parsed : 0
      const text = t("mj.filterPanel.resultCount", { count: count, countText: formatNumber(count) })
      this._resultCount.hidden = false
      /* role="status": a changed count is announced once, by this region. */
      if (this._resultCount.textContent !== text) {
        this._resultCount.textContent = text
      }
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "total-count") {
      this._renderCount()
    } else if (name === "sort-label") {
      this._renderSort()
    } else if (name === "label" || name === "layout" || name === "open" || name === "collapsible") {
      this._syncRoot()
    }
    return
  }

  /* ----- scriptable API ----- */

  get filterConfig() {
    return this._filterConfig
  }

  set filterConfig(config) {
    this._filterConfig = Array.isArray(config) === true ? config.filter((group) => group !== null && typeof group === "object") : []

    this._groupIds = []
    for (let index = 0; index < this._filterConfig.length; index = index + 1) {
      const group = this._filterConfig[index]
      const groupId = isBlank(group.id) === true ? nextId("mj-fg") : String(group.id)
      this._groupIds.push(groupId)
    }

    this._renderGroups()
    this._renderChips()
    return
  }

  /* The sort fields offered by the sort control: [{ value, label }]. */
  get sortOptions() {
    return this._sortOptions
  }

  set sortOptions(options) {
    this._sortOptions = Array.isArray(options) === true ? options.filter((entry) => entry !== null && typeof entry === "object" && isBlank(entry.value) === false) : []
    this._renderSort()
    return
  }

  get value() {
    return this._value
  }

  set value(state) {
    this._value = normaliseState(state)
    this._syncSort()
    this._renderGroups()
    this._renderChips()
    return
  }

  /*
   * The active filters as { groupId, label, value }, one per selected
   * option. The label reads "<group label>: <option label>".
   */
  get appliedFilters() {
    const applied = []
    const groupIds = Object.keys(this._value.filters)

    for (let index = 0; index < groupIds.length; index = index + 1) {
      const groupId = groupIds[index]
      const selection = this._value.filters[groupId]
      const group = this._filterConfig[this._groupIndexOfId(groupId)]
      const groupLabel = group !== undefined && isBlank(group.label) === false ? String(group.label) : groupId
      const options = group !== undefined ? this._groupOptions(group) : []

      let values = []
      if (Array.isArray(selection) === true) {
        values = selection
      } else if (isBlank(selection) === false) {
        values = [selection]
      }

      for (let position = 0; position < values.length; position = position + 1) {
        const value = values[position]
        const option = options.find((entry) => sameValue(entry.value, value))
        const optionLabel = option !== undefined && isBlank(option.label) === false ? String(option.label) : String(value)
        applied.push({ groupId: groupId, label: `${groupLabel}: ${optionLabel}`, value: value })
      }
    }

    return applied
  }
}
