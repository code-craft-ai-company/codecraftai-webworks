/*
 * mjquerybuilder.js
 *
 * <mj-query-builder> -- visual editor for compound boolean filter expressions
 * composed of conditions joined by AND/OR operators, with nesting support.
 * Outputs a structured QueryGroup JSON tree:
 *
 *   group  { combinator: "AND" | "OR", rules: [rule | group, ...] }
 *   rule   { id, field, operator, value }
 *
 * The component owns its tree. A value that is assigned is copied and
 * normalised, `value` returns a copy, and every `mj-query-change` carries a
 * fresh copy, so neither side can change the other's data by accident.
 *
 * Operators have a stable `id` (what is stored in `rule.operator`) and a
 * separate display `label`, plus an `arity` that decides the value editor:
 * 0 (no value, e.g. "is empty"), 1 (one value), 2 (a from / to pair, stored
 * as [from, to]) or "list" (several values, stored as an array). The editor
 * also follows the field type: number and date inputs for those types, a
 * select for a field with `options`. `operatorMap` and a field's own
 * `operators` accept plain strings (id and label alike) or
 * { id, label, arity } objects.
 *
 * The element is form-associated: it submits the JSON tree under its `name`
 * and is invalid while a condition is incomplete (customError), or, with
 * `required`, while the query has no condition at all (valueMissing).
 *
 * `operatorMap` returns a copy, like `value`: changing it changes nothing
 * until it is assigned back, and the built-in defaults are never exposed.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { announce } from "../core/announcer.js";
import { t } from "../core/intl.js";

const DEFAULT_MAX_DEPTH = 3;

/* Nesting beyond this is cut off when a value is assigned (also stops cycles). */
const MAX_TREE_DEPTH = 32;

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
  outline-offset: calc(-1 * var(--mj-focus-ring-width));
}

.remove-group-btn {
  margin-inline-start: auto;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--mj-text-muted);
  padding: var(--mj-space-1);
  border-radius: var(--mj-radius-sm);
  font: inherit;
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

.rule-values {
  display: flex;
  flex: 2;
  gap: var(--mj-qb-rule-gap, var(--mj-space-2));
  min-inline-size: 80px;
}

.rule-values:empty {
  display: none;
}

.rule-select, .rule-input {
  flex: 1;
  min-inline-size: 80px;
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
  font: inherit;
  line-height: 1;
}

.remove-rule-btn:hover { color: var(--mj-color-danger); }

.remove-rule-btn:focus-visible,
.remove-group-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}

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

button[disabled] {
  opacity: 0.55;
  cursor: not-allowed;
}

.empty-placeholder {
  margin: 0;
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

/*
 * The built-in operators per field type. The ids are the values stored in a
 * rule and stay as they are; a localised UI supplies its own labels through
 * `operatorMap`.
 */
const DEFAULT_OPERATORS = Object.freeze({
  string: Object.freeze(["equals", "contains", "starts with", "ends with", "is empty", "is not empty"]),
  number: Object.freeze(["=", "!=", ">", "<", ">=", "<=", "is between", "is empty"]),
  date: Object.freeze(["is", "is before", "is after", "is between"]),
  boolean: Object.freeze(["is true", "is false"]),
  select: Object.freeze(["is", "is not", "is any of"])
});

/*
 * A copy of an operator map: a new object with a new array per field type
 * and a new object per { id, label, arity } entry.
 */
function cloneOperatorMap(map) {
  const copy = {}
  const types = Object.keys(map)
  for (let index = 0; index < types.length; index = index + 1) {
    const type = types[index]
    const entries = map[type]
    if (Array.isArray(entries) === true) {
      copy[type] = entries.map((entry) => {
        const cloned = entry !== null && typeof entry === "object" ? Object.assign({}, entry) : entry
        return cloned
      })
    } else {
      copy[type] = entries
    }
  }
  return copy
}

/*
 * Display labels of the built-in operators, resolved through `t()` when the
 * operators come from DEFAULT_OPERATORS. Symbol operators (=, <, ...) have
 * no entry and show their id.
 */
const OPERATOR_LABEL_KEYS = {
  "equals": "mj.queryBuilder.operatorEquals",
  "contains": "mj.queryBuilder.operatorContains",
  "starts with": "mj.queryBuilder.operatorStartsWith",
  "ends with": "mj.queryBuilder.operatorEndsWith",
  "is empty": "mj.queryBuilder.operatorIsEmpty",
  "is not empty": "mj.queryBuilder.operatorIsNotEmpty",
  "is between": "mj.queryBuilder.operatorIsBetween",
  "is": "mj.queryBuilder.operatorIs",
  "is before": "mj.queryBuilder.operatorIsBefore",
  "is after": "mj.queryBuilder.operatorIsAfter",
  "is true": "mj.queryBuilder.operatorIsTrue",
  "is false": "mj.queryBuilder.operatorIsFalse",
  "is not": "mj.queryBuilder.operatorIsNot",
  "is any of": "mj.queryBuilder.operatorIsAnyOf"
};

/* Display labels of the group combinators; the stored values stay AND / OR. */
const COMBINATOR_LABEL_KEYS = {
  AND: "mj.queryBuilder.combinatorAnd",
  OR: "mj.queryBuilder.combinatorOr"
};

/* Arity of the operators that are not a plain one-value comparison. */
const OPERATOR_ARITY = {
  "is empty": 0,
  "is not empty": 0,
  "is true": 0,
  "is false": 0,
  "is null": 0,
  "is not null": 0,
  "is between": 2,
  "between": 2,
  "is any of": "list",
  "is none of": "list",
  "in": "list",
  "not in": "list"
};

function isBlank(value) {
  const blank = value === null || value === undefined || value === ""
  return blank
}

/* Bring a string or { id, label, arity } operator entry into the full shape. */
function normaliseOperator(entry) {
  let operator = null

  if (typeof entry === "string") {
    operator = { id: entry, label: entry, arity: 1 }
  } else if (entry !== null && typeof entry === "object") {
    const id = isBlank(entry.id) === false ? entry.id : entry.value
    if (isBlank(id) === false) {
      operator = {
        id: String(id),
        label: isBlank(entry.label) === false ? String(entry.label) : String(id),
        arity: entry.arity
      }
    }
  }

  if (operator !== null) {
    const known = operator.arity === 0 || operator.arity === 1 || operator.arity === 2 || operator.arity === "list"
    if (known === false || typeof entry === "string") {
      const inferred = OPERATOR_ARITY[operator.id]
      operator.arity = inferred !== undefined ? inferred : 1
    }
  }

  return operator
}

/*
 * Copy a query group, normalising it on the way: a combinator of AND / OR, a
 * `rules` array, every rule with an id and with `field`, `operator` and
 * `value` present (null when missing). Nodes nested deeper than
 * MAX_TREE_DEPTH -- which includes a tree that contains itself -- are
 * dropped.
 */
function cloneGroup(source, depth) {
  const group = { combinator: "AND", rules: [] }

  if (source !== null && source !== undefined && typeof source === "object") {
    group.combinator = String(source.combinator).toUpperCase() === "OR" ? "OR" : "AND"

    const rules = Array.isArray(source.rules) === true ? source.rules : []
    for (let index = 0; index < rules.length; index = index + 1) {
      const entry = rules[index]
      if (entry !== null && entry !== undefined && typeof entry === "object") {
        if (entry.rules !== undefined) {
          if (depth < MAX_TREE_DEPTH) {
            group.rules.push(cloneGroup(entry, depth + 1))
          }
        } else {
          group.rules.push(cloneRule(entry))
        }
      }
    }
  }

  return group
}

function cloneRule(source) {
  const sourceValue = source.value
  let value = null
  if (Array.isArray(sourceValue) === true) {
    value = sourceValue.slice()
  } else if (sourceValue !== undefined) {
    value = sourceValue
  }

  const rule = {
    id: isBlank(source.id) === false ? source.id : nextId("mj-rule"),
    field: isBlank(source.field) === false ? source.field : null,
    operator: isBlank(source.operator) === false ? source.operator : null,
    value: value
  }
  return rule
}

export class MjQueryBuilder extends FormControlMixin(MjElement) {
  static tagName = "mj-query-builder";
  static styles = STYLES;
  static watched = [
    "readonly", "max-depth", "show-preview", "label",
    "add-rule-label", "add-group-label", "required", "name"
  ];

  constructor() {
    super()
    this._initFormControl()

    /* Shadow references; null until the first render. */
    this._rootEl = null
    this._container = null
    this._previewPanel = null
    this._previewPre = null

    this._fieldSchema = []
    this._operatorMap = DEFAULT_OPERATORS

    /* The component's own query tree. (`_value` is the mixin's form value: the JSON text.) */
    this._tree = cloneGroup(null, 0)

    /*
     * Ids of the rules the user has worked on. Only those are marked invalid
     * while incomplete, so a freshly added row is not shown as an error.
     */
    this._touchedRules = new Set()
    this._showAllInvalid = false
    this._formDisabled = false

    this._syncFormValue()
  }

  render() {
    const markup = `
      <div class="qb-root" role="region" part="root">
        <div class="qb-group-container"></div>
        <div class="preview-panel" part="preview" hidden>
          <pre tabindex="0"></pre>
        </div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._rootEl = this.$(".qb-root")
    this._container = this.$(".qb-group-container")
    this._previewPanel = this.$(".preview-panel")
    this._previewPre = this.$("pre")
    this._previewPre.setAttribute("aria-label", t("mj.queryBuilder.expressionLabel"))

    this._syncLabel()

    /*
     * One set of listeners on the stable container: the groups and rules
     * below it are rebuilt on every structural change.
     */
    this.listen(this._container, "click", this._onClick.bind(this))
    this.listen(this._container, "change", this._onChange.bind(this))
    this.listen(this._container, "input", this._onInput.bind(this))

    this._renderTree(null)
    this._updatePreview()
    return
  }

  _syncLabel() {
    if (this._rootEl === undefined || this._rootEl === null) {
      return
    }
    const label = this.getAttribute("label") || t("mj.queryBuilder.label")
    this._rootEl.setAttribute("aria-label", label)
    return
  }

  /* True when nothing may be edited: readonly, disabled, or disabled through the form. */
  _isLocked() {
    const locked =
      this.hasAttribute("readonly") === true ||
      this.hasAttribute("disabled") === true ||
      this._formDisabled === true
    return locked
  }

  _maxDepth() {
    const parsed = parseInt(this.getAttribute("max-depth") || "", 10)
    const maxDepth = Number.isFinite(parsed) === true && parsed >= 0 ? parsed : DEFAULT_MAX_DEPTH
    return maxDepth
  }

  /* ----- schema and operators ----- */

  _fieldDef(fieldId) {
    let found = null
    if (isBlank(fieldId) === false) {
      for (let index = 0; index < this._fieldSchema.length && found === null; index = index + 1) {
        if (String(this._fieldSchema[index].id) === String(fieldId)) {
          found = this._fieldSchema[index]
        }
      }
    }
    return found
  }

  _fieldType(fieldDef) {
    const type = fieldDef !== null && isBlank(fieldDef.type) === false ? String(fieldDef.type) : "string"
    return type
  }

  /* The operators offered for a field: its own list, else the map entry for its type. */
  _operatorsFor(fieldDef) {
    let entries = []
    let builtIn = false

    if (fieldDef !== null && Array.isArray(fieldDef.operators) === true) {
      entries = fieldDef.operators
    } else {
      builtIn = this._operatorMap === DEFAULT_OPERATORS
      const map = this._operatorMap
      const byType = map[this._fieldType(fieldDef)]
      if (Array.isArray(byType) === true) {
        entries = byType
      } else if (Array.isArray(map["string"]) === true) {
        entries = map["string"]
      }
    }

    const operators = []
    for (let index = 0; index < entries.length; index = index + 1) {
      const operator = normaliseOperator(entries[index])
      if (operator !== null) {
        if (builtIn === true && OPERATOR_LABEL_KEYS[operator.id] !== undefined) {
          operator.label = t(OPERATOR_LABEL_KEYS[operator.id])
        }
        operators.push(operator)
      }
    }
    return operators
  }

  _operatorDef(fieldDef, operatorId) {
    let found = null
    if (isBlank(operatorId) === false) {
      const operators = this._operatorsFor(fieldDef)
      for (let index = 0; index < operators.length && found === null; index = index + 1) {
        if (operators[index].id === String(operatorId)) {
          found = operators[index]
        }
      }
      if (found === null) {
        /* An operator the schema does not list (an older saved query) is kept as it is. */
        found = normaliseOperator(String(operatorId))
      }
    }
    return found
  }

  /* The field's choices as [{ value, label }], or an empty list. */
  _fieldOptions(fieldDef) {
    const options = []
    const source = fieldDef !== null && Array.isArray(fieldDef.options) === true ? fieldDef.options : []
    for (let index = 0; index < source.length; index = index + 1) {
      const entry = source[index]
      if (entry !== null && typeof entry === "object") {
        options.push({ value: entry.value, label: isBlank(entry.label) === false ? String(entry.label) : String(entry.value) })
      } else {
        options.push({ value: entry, label: String(entry) })
      }
    }
    return options
  }

  /*
   * The kind of value editor a rule needs: "none", "text", "number", "date",
   * "choice" (a select over the field's options), "choices" (a multi-select),
   * "text-list" (comma separated), or "range-number" / "range-date" /
   * "range-text" (a from / to pair).
   */
  _editorKind(fieldDef, operator) {
    let kind = "none"

    if (operator !== null && operator.arity !== 0) {
      const type = this._fieldType(fieldDef)
      const hasOptions = this._fieldOptions(fieldDef).length > 0
      let base = "text"
      if (type === "number") {
        base = "number"
      } else if (type === "date") {
        base = "date"
      }

      if (operator.arity === 2) {
        kind = `range-${base}`
      } else if (operator.arity === "list") {
        kind = hasOptions === true ? "choices" : "text-list"
      } else if (hasOptions === true) {
        kind = "choice"
      } else {
        kind = base
      }
    }

    return kind
  }

  /* True when a rule's operator needs a value that the rule does not have. */
  _valueMissing(rule, operator) {
    let missing = false

    if (operator !== null && operator.arity !== 0) {
      const value = rule.value
      if (operator.arity === 2) {
        missing =
          Array.isArray(value) === false || value.length < 2 ||
          isBlank(value[0]) === true || isBlank(value[1]) === true
      } else if (operator.arity === "list") {
        missing = Array.isArray(value) === false || value.length === 0
      } else {
        missing = isBlank(value) === true
      }
    }

    return missing
  }

  /* ----- tree access by path ("" is the root, "0.2" the third child of the first child) ----- */

  _nodeAt(path) {
    let node = this._tree
    if (path !== "") {
      const steps = path.split(".")
      for (let index = 0; index < steps.length && node !== undefined; index = index + 1) {
        node = node.rules !== undefined ? node.rules[parseInt(steps[index], 10)] : undefined
      }
    }
    const found = node !== undefined ? node : null
    return found
  }

  _parentPath(path) {
    const cut = path.lastIndexOf(".")
    const parent = cut >= 0 ? path.slice(0, cut) : ""
    return parent
  }

  _indexInParent(path) {
    const cut = path.lastIndexOf(".")
    const index = parseInt(cut >= 0 ? path.slice(cut + 1) : path, 10)
    return index
  }

  _childPath(parentPath, index) {
    const path = parentPath === "" ? String(index) : `${parentPath}.${index}`
    return path
  }

  /* ----- rendering ----- */

  /*
   * Rebuild the editor from the tree. `focusKey` names the control that
   * should have focus afterwards; null keeps focus on the control that has
   * it now (controls are identified by "<path>:<control>").
   */
  _renderTree(focusKey) {
    if (this._container === undefined || this._container === null) {
      return
    }

    let wantedKey = focusKey
    if (wantedKey === null) {
      const active = this.shadowRoot.activeElement
      if (active !== null && active.hasAttribute("data-focus-key") === true) {
        wantedKey = active.getAttribute("data-focus-key")
      }
    }

    this._container.textContent = ""
    this._container.appendChild(this._buildGroup(this._tree, "", 0))

    if (wantedKey !== null) {
      const controls = this._container.querySelectorAll("[data-focus-key]")
      for (let index = 0; index < controls.length; index = index + 1) {
        if (controls[index].getAttribute("data-focus-key") === wantedKey) {
          controls[index].focus()
          break
        }
      }
    }
    return
  }

  /* Create a button that carries its action, the path it acts on and its focus key. */
  _buildButton(className, part, action, path, text) {
    const button = document.createElement("button")
    button.type = "button"
    button.className = className
    if (part !== null) {
      button.setAttribute("part", part)
    }
    button.setAttribute("data-action", action)
    button.setAttribute("data-path", path)
    button.setAttribute("data-focus-key", `${path}:${action}`)
    button.textContent = text
    button.disabled = this._isLocked()
    return button
  }

  _buildGroup(group, path, depth) {
    const groupEl = document.createElement("div")
    groupEl.className = "qb-group"
    groupEl.setAttribute("role", "group")
    groupEl.setAttribute("part", "group")
    groupEl.setAttribute("aria-label", t("mj.queryBuilder.groupLabel", { combinator: t(COMBINATOR_LABEL_KEYS[group.combinator]) }))

    const header = document.createElement("div")
    header.className = "qb-group-header"
    header.setAttribute("part", "group-header")

    const combinatorEl = document.createElement("div")
    combinatorEl.className = "combinator-btn"
    combinatorEl.setAttribute("part", "combinator")
    combinatorEl.setAttribute("role", "group")
    combinatorEl.setAttribute("aria-label", t("mj.queryBuilder.combineWith"))

    const combinators = ["AND", "OR"]
    for (let index = 0; index < combinators.length; index = index + 1) {
      const combinator = combinators[index]
      const button = this._buildButton("combinator-option", null, "combinator", path, t(COMBINATOR_LABEL_KEYS[combinator]))
      button.setAttribute("data-value", combinator)
      button.setAttribute("data-focus-key", `${path}:combinator-${combinator}`)
      button.setAttribute("aria-pressed", group.combinator === combinator ? "true" : "false")
      combinatorEl.appendChild(button)
    }
    header.appendChild(combinatorEl)

    if (path !== "") {
      const removeGroup = this._buildButton("remove-group-btn", "remove-group", "remove-group", path, `✕ ${t("mj.queryBuilder.removeGroup")}`)
      removeGroup.setAttribute("aria-label", t("mj.queryBuilder.removeGroupLabel"))
      header.appendChild(removeGroup)
    }
    groupEl.appendChild(header)

    const rulesEl = document.createElement("div")
    rulesEl.className = "qb-rules"

    if (group.rules.length === 0) {
      const placeholder = document.createElement("p")
      placeholder.className = "empty-placeholder"
      placeholder.textContent = t("mj.queryBuilder.emptyGroup")
      rulesEl.appendChild(placeholder)
    }

    /* Conditions are numbered within their group, groups are not counted. */
    let ruleNumber = 0
    for (let index = 0; index < group.rules.length; index = index + 1) {
      const child = group.rules[index]
      const childPath = this._childPath(path, index)
      if (child.rules !== undefined) {
        rulesEl.appendChild(this._buildGroup(child, childPath, depth + 1))
      } else {
        ruleNumber = ruleNumber + 1
        rulesEl.appendChild(this._buildRule(child, childPath, ruleNumber))
      }
    }
    groupEl.appendChild(rulesEl)

    const actions = document.createElement("div")
    actions.className = "qb-actions"

    const addRuleLabel = this.getAttribute("add-rule-label") || t("mj.queryBuilder.addCondition")
    actions.appendChild(this._buildButton("add-btn", "add-rule", "add-rule", path, `+ ${addRuleLabel}`))

    if (depth < this._maxDepth()) {
      const addGroupLabel = this.getAttribute("add-group-label") || t("mj.queryBuilder.addGroup")
      actions.appendChild(this._buildButton("add-btn", "add-group", "add-group", path, `+ ${addGroupLabel}`))
    }
    groupEl.appendChild(actions)

    return groupEl
  }

  _buildRule(rule, path, ruleNumber) {
    const locked = this._isLocked()
    const fieldDef = this._fieldDef(rule.field)
    const operator = this._operatorDef(fieldDef, rule.operator)
    const showInvalid = this._showAllInvalid === true || this._touchedRules.has(rule.id) === true

    const ruleEl = document.createElement("div")
    ruleEl.className = "qb-rule"
    ruleEl.setAttribute("role", "group")
    ruleEl.setAttribute("part", "rule-row")
    ruleEl.setAttribute("aria-label", t("mj.queryBuilder.ruleLabel", { number: ruleNumber }))
    ruleEl.setAttribute("data-path", path)

    /* Field selector. */
    const fieldSelect = document.createElement("select")
    fieldSelect.className = "rule-select"
    fieldSelect.setAttribute("part", "field-select")
    fieldSelect.setAttribute("aria-label", t("mj.queryBuilder.field"))
    fieldSelect.setAttribute("data-control", "field")
    fieldSelect.setAttribute("data-focus-key", `${path}:field`)
    fieldSelect.disabled = locked

    const noField = document.createElement("option")
    noField.value = ""
    noField.textContent = this._fieldSchema.length === 0 ? t("mj.queryBuilder.noFields") : t("mj.queryBuilder.selectField")
    fieldSelect.appendChild(noField)

    let fieldListed = false
    for (let index = 0; index < this._fieldSchema.length; index = index + 1) {
      const candidate = this._fieldSchema[index]
      const option = document.createElement("option")
      option.value = String(candidate.id)
      option.textContent = isBlank(candidate.label) === false ? String(candidate.label) : String(candidate.id)
      if (rule.field !== null && String(candidate.id) === String(rule.field)) {
        option.selected = true
        fieldListed = true
      }
      fieldSelect.appendChild(option)
    }
    if (rule.field !== null && fieldListed === false) {
      /* A field the schema does not (yet) know stays visible and stays in the tree. */
      const unknown = document.createElement("option")
      unknown.value = String(rule.field)
      unknown.textContent = String(rule.field)
      unknown.selected = true
      fieldSelect.appendChild(unknown)
    }
    if (showInvalid === true && rule.field === null) {
      fieldSelect.setAttribute("aria-invalid", "true")
    }

    /* Operator selector. */
    const operatorSelect = document.createElement("select")
    operatorSelect.className = "rule-select"
    operatorSelect.setAttribute("part", "operator-select")
    operatorSelect.setAttribute("aria-label", t("mj.queryBuilder.operator"))
    operatorSelect.setAttribute("data-control", "operator")
    operatorSelect.setAttribute("data-focus-key", `${path}:operator`)
    operatorSelect.disabled = locked

    const noOperator = document.createElement("option")
    noOperator.value = ""
    noOperator.textContent = t("mj.queryBuilder.selectOperator")
    operatorSelect.appendChild(noOperator)

    if (rule.field !== null) {
      const operators = this._operatorsFor(fieldDef)
      let operatorListed = false
      for (let index = 0; index < operators.length; index = index + 1) {
        const option = document.createElement("option")
        option.value = operators[index].id
        option.textContent = operators[index].label
        if (rule.operator !== null && operators[index].id === String(rule.operator)) {
          option.selected = true
          operatorListed = true
        }
        operatorSelect.appendChild(option)
      }
      if (operator !== null && operatorListed === false) {
        const unknown = document.createElement("option")
        unknown.value = operator.id
        unknown.textContent = operator.label
        unknown.selected = true
        operatorSelect.appendChild(unknown)
      }
    }
    if (showInvalid === true && rule.field !== null && rule.operator === null) {
      operatorSelect.setAttribute("aria-invalid", "true")
    }

    /* Value editor(s), chosen from the field type and the operator's arity. */
    const valuesEl = document.createElement("div")
    valuesEl.className = "rule-values"
    const kind = this._editorKind(fieldDef, operator)
    valuesEl.setAttribute("data-editor", kind)
    this._fillValueEditor(valuesEl, kind, rule, fieldDef, path, locked)
    if (showInvalid === true && this._valueMissing(rule, operator) === true) {
      this._markValueInvalid(valuesEl, true)
    }

    const removeRule = this._buildButton("remove-rule-btn", "remove-rule", "remove-rule", path, "✕")
    removeRule.setAttribute("aria-label", t("mj.queryBuilder.removeRuleLabel", { number: ruleNumber }))

    ruleEl.appendChild(fieldSelect)
    ruleEl.appendChild(operatorSelect)
    ruleEl.appendChild(valuesEl)
    ruleEl.appendChild(removeRule)
    return ruleEl
  }

  _buildValueInput(type, label, focusKey, value, locked) {
    const input = document.createElement("input")
    input.className = "rule-input"
    input.setAttribute("part", "value-input")
    input.setAttribute("type", type)
    input.setAttribute("aria-label", label)
    input.setAttribute("data-control", "value")
    input.setAttribute("data-focus-key", focusKey)
    input.value = isBlank(value) === true ? "" : String(value)
    input.disabled = locked
    return input
  }

  _fillValueEditor(valuesEl, kind, rule, fieldDef, path, locked) {
    const value = rule.value

    if (kind === "text" || kind === "number" || kind === "date") {
      valuesEl.appendChild(this._buildValueInput(kind, t("mj.queryBuilder.value"), `${path}:value`, Array.isArray(value) === true ? "" : value, locked))
    } else if (kind === "text-list") {
      const joined = Array.isArray(value) === true ? value.join(", ") : value
      const input = this._buildValueInput("text", t("mj.queryBuilder.valuesList"), `${path}:value`, joined, locked)
      valuesEl.appendChild(input)
    } else if (kind === "range-text" || kind === "range-number" || kind === "range-date") {
      const inputType = kind.slice("range-".length)
      const pair = Array.isArray(value) === true ? value : [null, null]
      valuesEl.appendChild(this._buildValueInput(inputType, t("mj.queryBuilder.rangeFrom"), `${path}:value`, pair[0], locked))
      valuesEl.appendChild(this._buildValueInput(inputType, t("mj.queryBuilder.rangeTo"), `${path}:value-to`, pair[1], locked))
    } else if (kind === "choice" || kind === "choices") {
      const multiple = kind === "choices"
      const options = this._fieldOptions(fieldDef)
      const selectedValues = Array.isArray(value) === true ? value : [value]

      const select = document.createElement("select")
      select.className = "rule-select"
      select.setAttribute("part", "value-input")
      select.setAttribute("aria-label", multiple === true ? t("mj.queryBuilder.values") : t("mj.queryBuilder.value"))
      select.setAttribute("data-control", "value")
      select.setAttribute("data-focus-key", `${path}:value`)
      select.multiple = multiple
      select.disabled = locked

      if (multiple === false) {
        const none = document.createElement("option")
        none.value = ""
        none.textContent = t("mj.queryBuilder.selectValue")
        select.appendChild(none)
      }

      for (let index = 0; index < options.length; index = index + 1) {
        const option = document.createElement("option")
        /* The index leads back to the option, so its value keeps its type. */
        option.value = String(index)
        option.textContent = options[index].label
        option.selected = selectedValues.some((entry) => isBlank(entry) === false && String(entry) === String(options[index].value))
        select.appendChild(option)
      }
      valuesEl.appendChild(select)
    }
    return
  }

  _markValueInvalid(valuesEl, invalid) {
    const controls = valuesEl.querySelectorAll("[data-control='value']")
    for (let index = 0; index < controls.length; index = index + 1) {
      if (invalid === true) {
        controls[index].setAttribute("aria-invalid", "true")
      } else {
        controls[index].removeAttribute("aria-invalid")
      }
    }
    return
  }

  /* Read a rule's value back from its editor, in the type the editor stands for. */
  _readValue(valuesEl, fieldDef) {
    const kind = valuesEl.getAttribute("data-editor")
    const controls = valuesEl.querySelectorAll("[data-control='value']")
    let value = null

    const readInput = (input, inputKind) => {
      let entry = null
      if (input.value !== "") {
        if (inputKind === "number") {
          const parsed = Number(input.value)
          entry = Number.isFinite(parsed) === true ? parsed : null
        } else {
          entry = input.value
        }
      }
      return entry
    }

    if (controls.length === 0) {
      value = null
    } else if (kind === "text" || kind === "number" || kind === "date") {
      value = readInput(controls[0], kind)
    } else if (kind === "text-list") {
      const parts = controls[0].value.split(",").map((part) => part.trim()).filter((part) => part.length > 0)
      value = parts.length > 0 ? parts : null
    } else if (kind === "range-text" || kind === "range-number" || kind === "range-date") {
      const inputKind = kind.slice("range-".length)
      const from = readInput(controls[0], inputKind)
      const to = controls.length > 1 ? readInput(controls[1], inputKind) : null
      value = from === null && to === null ? null : [from, to]
    } else if (kind === "choice" || kind === "choices") {
      const options = this._fieldOptions(fieldDef)
      const chosen = []
      const selected = controls[0].selectedOptions
      for (let index = 0; index < selected.length; index = index + 1) {
        const option = options[parseInt(selected[index].value, 10)]
        if (option !== undefined) {
          chosen.push(option.value)
        }
      }
      if (kind === "choices") {
        value = chosen.length > 0 ? chosen : null
      } else {
        value = chosen.length > 0 ? chosen[0] : null
      }
    }

    return value
  }

  /* ----- editing ----- */

  _onClick(event) {
    const target = event.target
    const button = target instanceof Element ? target.closest("button[data-action]") : null
    if (button === null || this._isLocked() === true) {
      return
    }

    const action = button.getAttribute("data-action")
    const path = button.getAttribute("data-path")

    if (action === "combinator") {
      this._setCombinator(path, button.getAttribute("data-value"))
    } else if (action === "add-rule") {
      this._addRule(path)
    } else if (action === "add-group") {
      this._addGroup(path)
    } else if (action === "remove-rule" || action === "remove-group") {
      this._removeNode(path, action === "remove-group")
    }
    return
  }

  _setCombinator(path, combinator) {
    const group = this._nodeAt(path)
    if (group === null || group.combinator === combinator) {
      return
    }
    group.combinator = combinator === "OR" ? "OR" : "AND"
    this._renderTree(`${path}:combinator-${group.combinator}`)
    announce(t("mj.queryBuilder.combinatorChanged", { combinator: t(COMBINATOR_LABEL_KEYS[group.combinator]) }), "polite")
    this._emitChange()
    return
  }

  _addRule(path) {
    const group = this._nodeAt(path)
    if (group === null) {
      return
    }
    group.rules.push({ id: nextId("mj-rule"), field: null, operator: null, value: null })
    this._renderTree(`${this._childPath(path, group.rules.length - 1)}:field`)
    this._emitChange()
    return
  }

  _addGroup(path) {
    const group = this._nodeAt(path)
    if (group === null) {
      return
    }
    group.rules.push({ combinator: "AND", rules: [] })
    this._renderTree(`${this._childPath(path, group.rules.length - 1)}:add-rule`)
    this._emitChange()
    return
  }

  /*
   * Remove a rule or group. Focus goes to the entry before the removed one
   * (its remove button), else to the entry that took its place, else to the
   * group's "Add condition" button, so it never falls back to the page.
   */
  _removeNode(path, isGroup) {
    const parentPath = this._parentPath(path)
    const parent = this._nodeAt(parentPath)
    const index = this._indexInParent(path)
    if (parent === null || parent.rules[index] === undefined) {
      return
    }

    const removed = parent.rules.splice(index, 1)[0]
    if (removed.rules === undefined) {
      this._touchedRules.delete(removed.id)
    }

    let focusKey = `${parentPath}:add-rule`
    if (parent.rules.length > 0) {
      const neighbourIndex = index > 0 ? index - 1 : 0
      const neighbour = parent.rules[neighbourIndex]
      const neighbourPath = this._childPath(parentPath, neighbourIndex)
      focusKey = neighbour.rules !== undefined ? `${neighbourPath}:remove-group` : `${neighbourPath}:remove-rule`
    }

    this._renderTree(focusKey)
    announce(isGroup === true ? t("mj.queryBuilder.groupRemoved") : t("mj.queryBuilder.ruleRemoved"), "polite")
    this._emitChange()
    return
  }

  _ruleElementOf(node) {
    const ruleEl = node instanceof Element ? node.closest(".qb-rule") : null
    return ruleEl
  }

  /* A field, operator or committed value changed. */
  _onChange(event) {
    const control = event.target
    const ruleEl = this._ruleElementOf(control)
    if (ruleEl === null || this._isLocked() === true) {
      return
    }

    const path = ruleEl.getAttribute("data-path")
    const rule = this._nodeAt(path)
    if (rule === null) {
      return
    }

    const role = control.getAttribute("data-control")
    this._touchedRules.add(rule.id)

    if (role === "field") {
      rule.field = control.value !== "" ? control.value : null
      rule.operator = null
      rule.value = null
      this._renderTree(`${path}:field`)
      this._emitChange()
    } else if (role === "operator") {
      const fieldDef = this._fieldDef(rule.field)
      const previousKind = this._editorKind(fieldDef, this._operatorDef(fieldDef, rule.operator))
      rule.operator = control.value !== "" ? control.value : null
      const nextKind = this._editorKind(fieldDef, this._operatorDef(fieldDef, rule.operator))
      if (nextKind !== previousKind) {
        /* A different editor cannot show the old value. */
        rule.value = null
      }
      this._renderTree(`${path}:operator`)
      this._emitChange()
    } else if (role === "value") {
      this._commitValue(ruleEl, rule)
    }
    return
  }

  /* Typing in a value input updates the tree without rebuilding the row. */
  _onInput(event) {
    const control = event.target
    const ruleEl = this._ruleElementOf(control)
    if (ruleEl === null || control.getAttribute("data-control") !== "value" || this._isLocked() === true) {
      return
    }

    const rule = this._nodeAt(ruleEl.getAttribute("data-path"))
    if (rule !== null && control.localName === "input") {
      this._touchedRules.add(rule.id)
      this._commitValue(ruleEl, rule)
    }
    return
  }

  _commitValue(ruleEl, rule) {
    const fieldDef = this._fieldDef(rule.field)
    const valuesEl = ruleEl.querySelector(".rule-values")
    const next = this._readValue(valuesEl, fieldDef)

    const changed = JSON.stringify(next) !== JSON.stringify(rule.value)
    rule.value = next

    const operator = this._operatorDef(fieldDef, rule.operator)
    this._markValueInvalid(valuesEl, this._valueMissing(rule, operator))

    if (changed === true) {
      this._emitChange()
    }
    return
  }

  /* ----- value, validity and events ----- */

  _validate(group, errors) {
    for (let index = 0; index < group.rules.length; index = index + 1) {
      const entry = group.rules[index]
      if (entry.rules !== undefined) {
        this._validate(entry, errors)
      } else {
        const fieldDef = this._fieldDef(entry.field)
        const operator = this._operatorDef(fieldDef, entry.operator)
        const incomplete =
          entry.field === null || entry.operator === null ||
          this._valueMissing(entry, operator) === true
        if (incomplete === true) {
          errors.push({ ruleId: entry.id, message: t("mj.queryBuilder.ruleIncomplete") })
        }
      }
    }
    return errors
  }

  /*
   * The mixin sees only the JSON text, which is never empty, so it reports
   * an empty query under `required` as the custom error from
   * `_customValidity`. Re-flag that case as valueMissing, as a native
   * required control would be, with the same message.
   */
  _refreshValidity() {
    super._refreshValidity()

    const emptyRequired =
      this._internals !== null && this._internals !== undefined &&
      this._tree !== undefined && this._tree.rules.length === 0 &&
      this.hasAttribute("required") === true
    if (emptyRequired === true) {
      const message = t("mj.queryBuilder.empty")
      const anchor = this._validationAnchor()
      if (anchor !== null && anchor !== undefined && anchor !== this) {
        this._internals.setValidity({ valueMissing: true }, message, anchor)
      } else {
        this._internals.setValidity({ valueMissing: true }, message)
      }
    }
    return
  }

  /* FormControlMixin hook: the message while the query cannot be submitted. */
  _customValidity() {
    let message = ""
    if (this._tree !== undefined) {
      if (this._validate(this._tree, []).length > 0) {
        message = t("mj.queryBuilder.incomplete")
      } else if (this.hasAttribute("required") === true && this._tree.rules.length === 0) {
        message = t("mj.queryBuilder.empty")
      }
    }
    return message
  }

  /* Hand the JSON tree to the owning form and refresh validity. */
  _syncFormValue() {
    this._setFormValue(JSON.stringify(this._tree))
    return
  }

  _emitChange() {
    this._updatePreview()
    this._syncFormValue()

    const errors = this._validate(this._tree, [])
    this.emit("mj-query-change", { value: cloneGroup(this._tree, 0) })
    this.emit("mj-query-valid", { valid: errors.length === 0, errors: errors })
    return
  }

  _updatePreview() {
    if (this._previewPre === undefined || this._previewPre === null) {
      return
    }
    const show = this.hasAttribute("show-preview")
    this._previewPanel.hidden = show === false
    this._previewPre.textContent = show === true ? JSON.stringify(this._tree, null, 2) : ""
    return
  }

  /* Show every incomplete condition as invalid, then report through the form API. */
  reportValidity() {
    this._showAllInvalid = true
    this._renderTree(null)
    const valid = super.reportValidity()
    return valid
  }

  formResetCallback() {
    this._tree = cloneGroup(null, 0)
    this._touchedRules = new Set()
    this._showAllInvalid = false
    this._renderTree(null)
    this._updatePreview()
    this._syncFormValue()
    return
  }

  formStateRestoreCallback(state) {
    let restored = null
    try {
      restored = JSON.parse(state)
    } catch (error) {
      restored = null
    }
    this.value = restored
    return
  }

  onFormDisabled(disabled) {
    this._formDisabled = disabled === true
    this._renderTree(null)
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "label") {
      this._syncLabel()
    } else if (name === "show-preview") {
      this._updatePreview()
    } else if (name === "required") {
      this._refreshValidity()
    } else if (
      name === "readonly" || name === "disabled" || name === "max-depth" ||
      name === "add-rule-label" || name === "add-group-label"
    ) {
      this._renderTree(null)
    }
    return
  }

  /* ----- scriptable API ----- */

  get fieldSchema() {
    return this._fieldSchema
  }

  set fieldSchema(schema) {
    this._fieldSchema = Array.isArray(schema) === true ? schema.filter((field) => field !== null && typeof field === "object") : []
    this._renderTree(null)
    this._refreshValidity()
    return
  }

  /* A copy of the query tree; changing it does not change the builder. */
  get value() {
    const copy = cloneGroup(this._tree, 0)
    return copy
  }

  set value(tree) {
    this._tree = cloneGroup(tree, 0)
    this._touchedRules = new Set()
    this._showAllInvalid = false
    this._renderTree(null)
    this._updatePreview()
    this._syncFormValue()
    return
  }

  /* A copy of the operators per field type; assign a map to change them. */
  get operatorMap() {
    const copy = cloneOperatorMap(this._operatorMap)
    return copy
  }

  set operatorMap(map) {
    this._operatorMap = map !== null && map !== undefined && typeof map === "object" ? cloneOperatorMap(map) : DEFAULT_OPERATORS
    this._renderTree(null)
    this._refreshValidity()
    return
  }
}
