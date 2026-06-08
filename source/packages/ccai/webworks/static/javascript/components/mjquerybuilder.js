/*
 * mjquerybuilder.js
 *
 * <mj-query-builder> -- visual editor for compound boolean filter expressions
 * composed of conditions joined by AND/OR operators, with nesting support.
 * Outputs a structured QueryGroup JSON tree.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";

const STYLES = `
:host {
  display: block;
}

.qb-root {
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
}

.qb-group {
  border: 1px solid var(--mj-qb-group-border, var(--mj-border));
  border-radius: var(--mj-radius-md);
  background: var(--mj-qb-group-bg, var(--mj-surface));
  padding: var(--mj-space-3);
  margin-block-start: var(--mj-qb-row-gap, var(--mj-space-2));
}

.qb-group:first-child {
  margin-block-start: 0;
}

.qb-group-header {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  margin-block-end: var(--mj-space-2);
}

.combinator-btn {
  display: inline-flex;
  gap: 2px;
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-sm);
  overflow: hidden;
  background: var(--mj-surface);
}

.combinator-option {
  padding: var(--mj-space-1) var(--mj-space-2);
  background: transparent;
  border: none;
  cursor: pointer;
  font: inherit;
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
  font-weight: var(--mj-font-weight-medium);
}

.combinator-option[aria-pressed="true"] {
  background: var(--mj-accent);
  color: var(--mj-text-on-accent);
}

.combinator-option:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: calc(-1 * var(--mj-focus-ring-offset));
}

.remove-group-btn {
  margin-inline-start: auto;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--mj-text-muted);
  padding: var(--mj-space-1);
  border-radius: var(--mj-radius-sm);
  font-size: var(--mj-font-size-xs);
}

.remove-group-btn:hover { color: var(--mj-color-danger); }

.qb-rules {
  display: flex;
  flex-direction: column;
  gap: var(--mj-qb-row-gap, var(--mj-space-2));
}

.qb-rule {
  display: flex;
  align-items: center;
  gap: var(--mj-qb-rule-gap, var(--mj-space-2));
  flex-wrap: wrap;
}

.rule-select, .rule-input {
  flex: 1;
  min-width: 80px;
  padding: var(--mj-space-1) var(--mj-space-2);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-sm);
  background: var(--mj-surface);
  font: inherit;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
}

.rule-select:focus-visible, .rule-input:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}

.rule-select[aria-invalid="true"], .rule-input[aria-invalid="true"] {
  border-color: var(--mj-color-danger);
}

.remove-rule-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--mj-text-muted);
  padding: var(--mj-space-1);
  border-radius: var(--mj-radius-sm);
  line-height: 1;
}

.remove-rule-btn:hover { color: var(--mj-color-danger); }

.qb-actions {
  display: flex;
  gap: var(--mj-space-2);
  margin-block-start: var(--mj-space-3);
}

.add-btn {
  padding: var(--mj-space-1) var(--mj-space-3);
  background: transparent;
  border: 1px dashed var(--mj-border);
  border-radius: var(--mj-radius-sm);
  font: inherit;
  font-size: var(--mj-font-size-xs);
  color: var(--mj-accent);
  cursor: pointer;
}

.add-btn:hover { background: var(--mj-bg-muted); }
.add-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}

.empty-placeholder {
  color: var(--mj-text-muted);
  font-size: var(--mj-font-size-xs);
  font-style: italic;
  padding: var(--mj-space-2) 0;
}

.preview-panel {
  margin-block-start: var(--mj-space-4);
  padding: var(--mj-space-3);
  background: var(--mj-bg-subtle);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-sm);
}

.preview-panel[hidden] { display: none; }

pre {
  margin: 0;
  font-family: var(--mj-font-mono);
  font-size: var(--mj-font-size-xs);
  white-space: pre-wrap;
  word-break: break-all;
  color: var(--mj-text);
}
`;

const DEFAULT_OPERATORS = {
  string: ["equals", "contains", "starts with", "ends with", "is empty", "is not empty"],
  number: ["=", "!=", ">", "<", ">=", "<=", "is empty"],
  date: ["is", "is before", "is after", "is between"],
  boolean: ["is true", "is false"],
  select: ["is", "is not", "is any of"]
};

export class MjQueryBuilder extends MjElement {
  static tagName = "mj-query-builder";
  static styles = STYLES;
  static watched = ["readonly", "max-depth", "show-preview", "label"];

  constructor() {
    super()
    this._fieldSchema = []
    this._value = { combinator: "AND", rules: [] }
    this._operatorMap = DEFAULT_OPERATORS
  }

  render() {
    const label = this.getAttribute("label") || "Query builder"
    const markup = `
      <div class="qb-root" role="region" aria-label="${label}" part="root">
        <div class="qb-group-container"></div>
        <div class="preview-panel" part="preview" hidden>
          <pre aria-label="Query expression"></pre>
        </div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._container = this.$(".qb-group-container")
    this._previewPanel = this.$(".preview-panel")
    this._previewPre = this.$("pre")

    this._renderGroup(this._value, this._container, 0, true)
    this._updatePreview()
    return
  }

  _renderGroup(group, container, depth, isRoot) {
    container.innerHTML = ""

    const groupEl = document.createElement("div")
    groupEl.className = "qb-group"
    groupEl.setAttribute("role", "group")
    groupEl.setAttribute("part", "group")
    groupEl.setAttribute("aria-label", `Condition group, ${group.combinator}`)

    const header = document.createElement("div")
    header.className = "qb-group-header"
    header.setAttribute("part", "group-header")

    const combinatorEl = document.createElement("div")
    combinatorEl.className = "combinator-btn"
    combinatorEl.setAttribute("part", "combinator")

    const andBtn = document.createElement("button")
    andBtn.className = "combinator-option"
    andBtn.textContent = "AND"
    andBtn.setAttribute("aria-pressed", group.combinator === "AND" ? "true" : "false")
    andBtn.setAttribute("type", "button")

    const orBtn = document.createElement("button")
    orBtn.className = "combinator-option"
    orBtn.textContent = "OR"
    orBtn.setAttribute("aria-pressed", group.combinator === "OR" ? "true" : "false")
    orBtn.setAttribute("type", "button")

    this.listen(andBtn, "click", () => this._setCombinator(group, "AND", andBtn, orBtn))
    this.listen(orBtn, "click", () => this._setCombinator(group, "OR", andBtn, orBtn))

    combinatorEl.appendChild(andBtn)
    combinatorEl.appendChild(orBtn)
    header.appendChild(combinatorEl)

    if (isRoot === false) {
      const removeGroupBtn = document.createElement("button")
      removeGroupBtn.className = "remove-group-btn"
      removeGroupBtn.setAttribute("part", "remove-group")
      removeGroupBtn.setAttribute("aria-label", "Remove condition group")
      removeGroupBtn.setAttribute("type", "button")
      removeGroupBtn.textContent = "✕ Remove group"
      this.listen(removeGroupBtn, "click", () => {
        container.innerHTML = ""
        this._removeGroupFromValue(group)
        announce("Condition group removed", "polite")
      })
      header.appendChild(removeGroupBtn)
    }

    groupEl.appendChild(header)

    const rulesEl = document.createElement("div")
    rulesEl.className = "qb-rules"

    if (group.rules.length === 0) {
      const placeholder = document.createElement("p")
      placeholder.className = "empty-placeholder"
      placeholder.textContent = "Add a condition"
      rulesEl.appendChild(placeholder)
    }

    for (let i = 0; i < group.rules.length; i = i + 1) {
      const rule = group.rules[i]
      if (rule.rules !== undefined) {
        const subContainer = document.createElement("div")
        this._renderGroup(rule, subContainer, depth + 1, false)
        rulesEl.appendChild(subContainer)
      } else {
        const ruleEl = this._buildRuleEl(rule, group, i)
        rulesEl.appendChild(ruleEl)
      }
    }

    groupEl.appendChild(rulesEl)

    const actions = document.createElement("div")
    actions.className = "qb-actions"

    const addRuleLabel = this.getAttribute("add-rule-label") || "Add condition"
    const addRuleBtn = document.createElement("button")
    addRuleBtn.className = "add-btn"
    addRuleBtn.setAttribute("part", "add-rule")
    addRuleBtn.setAttribute("type", "button")
    addRuleBtn.textContent = `+ ${addRuleLabel}`
    this.listen(addRuleBtn, "click", () => this._addRule(group, groupEl, rulesEl))
    actions.appendChild(addRuleBtn)

    const maxDepth = parseInt(this.getAttribute("max-depth") || "3", 10)
    if (depth < maxDepth) {
      const addGroupLabel = this.getAttribute("add-group-label") || "Add group"
      const addGroupBtn = document.createElement("button")
      addGroupBtn.className = "add-btn"
      addGroupBtn.setAttribute("part", "add-group")
      addGroupBtn.setAttribute("type", "button")
      addGroupBtn.textContent = `+ ${addGroupLabel}`
      this.listen(addGroupBtn, "click", () => this._addGroup(group, groupEl, rulesEl, depth))
      actions.appendChild(addGroupBtn)
    }

    groupEl.appendChild(actions)
    container.appendChild(groupEl)
    return
  }

  _buildRuleEl(rule, parentGroup, ruleIndex) {
    const ruleEl = document.createElement("div")
    ruleEl.className = "qb-rule"
    ruleEl.setAttribute("role", "group")
    ruleEl.setAttribute("part", "rule-row")
    ruleEl.setAttribute("aria-label", `Condition ${ruleIndex + 1}`)

    const readonly = this.hasAttribute("readonly")

    // Field selector
    const fieldSel = document.createElement("select")
    fieldSel.className = "rule-select"
    fieldSel.setAttribute("part", "field-select")
    fieldSel.setAttribute("aria-label", "Field")
    if (readonly === true) {
      fieldSel.disabled = true
    }
    if (rule.field === null) {
      fieldSel.setAttribute("aria-invalid", "true")
    }

    const emptyOpt = document.createElement("option")
    emptyOpt.value = ""
    emptyOpt.textContent = this._fieldSchema.length === 0 ? "No fields configured" : "Select field…"
    fieldSel.appendChild(emptyOpt)

    for (let i = 0; i < this._fieldSchema.length; i = i + 1) {
      const f = this._fieldSchema[i]
      const opt = document.createElement("option")
      opt.value = f.id
      opt.textContent = f.label
      opt.selected = rule.field === f.id
      fieldSel.appendChild(opt)
    }

    // Operator selector
    const opSel = document.createElement("select")
    opSel.className = "rule-select"
    opSel.setAttribute("part", "operator-select")
    opSel.setAttribute("aria-label", "Operator")
    if (readonly === true) {
      opSel.disabled = true
    }
    if (rule.operator === null) {
      opSel.setAttribute("aria-invalid", "true")
    }

    this._populateOperators(opSel, rule.field)
    if (rule.operator !== null) {
      opSel.value = rule.operator
    }

    // Value input
    const valueInput = document.createElement("input")
    valueInput.className = "rule-input"
    valueInput.setAttribute("part", "value-input")
    valueInput.setAttribute("aria-label", "Value")
    valueInput.setAttribute("type", "text")
    valueInput.value = rule.value !== null ? String(rule.value) : ""
    if (readonly === true) {
      valueInput.disabled = true
    }
    if (rule.value === null && rule.field !== null && rule.operator !== null) {
      valueInput.setAttribute("aria-invalid", "true")
    }

    // Remove button
    const removeBtn = document.createElement("button")
    removeBtn.className = "remove-rule-btn"
    removeBtn.setAttribute("part", "remove-rule")
    removeBtn.setAttribute("aria-label", `Remove condition ${ruleIndex + 1}`)
    removeBtn.setAttribute("type", "button")
    removeBtn.textContent = "✕"
    if (readonly === true) {
      removeBtn.disabled = true
    }

    this.listen(fieldSel, "change", () => {
      rule.field = fieldSel.value || null
      rule.operator = null
      rule.value = null
      this._populateOperators(opSel, rule.field)
      opSel.value = ""
      valueInput.value = ""
      this._emitChange()
    })

    this.listen(opSel, "change", () => {
      rule.operator = opSel.value || null
      this._emitChange()
    })

    this.listen(valueInput, "input", () => {
      rule.value = valueInput.value.length > 0 ? valueInput.value : null
      this._emitChange()
    })

    this.listen(removeBtn, "click", () => {
      const idx = parentGroup.rules.indexOf(rule)
      if (idx >= 0) {
        parentGroup.rules.splice(idx, 1)
      }
      ruleEl.remove()
      announce("Condition removed", "polite")
      this._emitChange()
    })

    ruleEl.appendChild(fieldSel)
    ruleEl.appendChild(opSel)
    ruleEl.appendChild(valueInput)
    ruleEl.appendChild(removeBtn)
    return ruleEl
  }

  _populateOperators(select, fieldId) {
    select.innerHTML = ""
    const empty = document.createElement("option")
    empty.value = ""
    empty.textContent = "Select operator…"
    select.appendChild(empty)

    if (fieldId === null || fieldId === "") {
      return
    }

    const fieldDef = this._fieldSchema.find((f) => f.id === fieldId)
    const fieldType = fieldDef !== undefined ? (fieldDef.type || "string") : "string"
    const operators = this._operatorMap[fieldType] || this._operatorMap["string"] || []

    for (let i = 0; i < operators.length; i = i + 1) {
      const opt = document.createElement("option")
      opt.value = operators[i]
      opt.textContent = operators[i]
      select.appendChild(opt)
    }
    return
  }

  _setCombinator(group, combinator, andBtn, orBtn) {
    group.combinator = combinator
    andBtn.setAttribute("aria-pressed", combinator === "AND" ? "true" : "false")
    orBtn.setAttribute("aria-pressed", combinator === "OR" ? "true" : "false")
    announce(`Group operator changed to ${combinator}`, "polite")
    this._emitChange()
    return
  }

  _addRule(group, groupEl, rulesEl) {
    const rule = { id: nextId("mj-rule"), field: null, operator: null, value: null }
    group.rules.push(rule)
    const index = group.rules.length - 1
    const ruleEl = this._buildRuleEl(rule, group, index)

    // Remove empty placeholder if present
    const placeholder = rulesEl.querySelector(".empty-placeholder")
    if (placeholder !== null) {
      placeholder.remove()
    }

    rulesEl.appendChild(ruleEl)
    this._emitChange()
    return
  }

  _addGroup(parentGroup, groupEl, rulesEl, depth) {
    const subGroup = { combinator: "AND", rules: [] }
    parentGroup.rules.push(subGroup)
    const subContainer = document.createElement("div")
    this._renderGroup(subGroup, subContainer, depth + 1, false)

    const placeholder = rulesEl.querySelector(".empty-placeholder")
    if (placeholder !== null) {
      placeholder.remove()
    }

    rulesEl.appendChild(subContainer)
    this._emitChange()
    return
  }

  _removeGroupFromValue(group) {
    this._removeGroupRecursive(this._value, group)
    this._emitChange()
    return
  }

  _removeGroupRecursive(parent, target) {
    const idx = parent.rules.indexOf(target)
    if (idx >= 0) {
      parent.rules.splice(idx, 1)
      return true
    }
    for (let i = 0; i < parent.rules.length; i = i + 1) {
      const rule = parent.rules[i]
      if (rule.rules !== undefined) {
        const found = this._removeGroupRecursive(rule, target)
        if (found === true) {
          return true
        }
      }
    }
    return false
  }

  _emitChange() {
    this._updatePreview()
    this._checkValidity()
    this.emit("mj-query-change", { value: this._value })
    return
  }

  _checkValidity() {
    const errors = this._validateGroup(this._value, [])
    const valid = errors.length === 0
    this.emit("mj-query-valid", { valid: valid, errors: errors })
    return
  }

  _validateGroup(group, errors) {
    for (let i = 0; i < group.rules.length; i = i + 1) {
      const rule = group.rules[i]
      if (rule.rules !== undefined) {
        this._validateGroup(rule, errors)
      } else {
        if (rule.field === null || rule.operator === null) {
          errors.push({ ruleId: rule.id, message: "Condition is incomplete" })
        }
      }
    }
    return errors
  }

  _updatePreview() {
    if (this._previewPre === null) {
      return
    }
    const show = this.hasAttribute("show-preview")
    if (this._previewPanel !== null) {
      this._previewPanel.hidden = !show
    }
    if (show === true) {
      this._previewPre.textContent = JSON.stringify(this._value, null, 2)
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "show-preview") {
      this._updatePreview()
    }
    return
  }

  get fieldSchema() {
    return this._fieldSchema
  }

  set fieldSchema(schema) {
    this._fieldSchema = Array.isArray(schema) ? schema : []
    if (this._container !== null) {
      this._renderGroup(this._value, this._container, 0, true)
    }
    return
  }

  get value() {
    return this._value
  }

  set value(v) {
    this._value = v !== null && v !== undefined ? v : { combinator: "AND", rules: [] }
    if (this._container !== null) {
      this._renderGroup(this._value, this._container, 0, true)
      this._updatePreview()
    }
    return
  }

  get operatorMap() {
    return this._operatorMap
  }

  set operatorMap(map) {
    this._operatorMap = map !== null && map !== undefined ? map : DEFAULT_OPERATORS
    return
  }
}
