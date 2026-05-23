# Query Builder Spec

- **Tag:** `<mj-query-builder>`
- **Class / file:** `QueryBuilder` / `querybuilder.js`
- **Category:** Application & productivity components
- **Primary or Variant:** Primary
- **Synonyms covered:** Compound condition builder, Rule builder, Filter expression editor
- **Phase:** P2
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-query-builder>` is a visual editor for building compound boolean filter expressions composed of conditions joined by AND/OR operators, which may themselves be nested into sub-groups. It outputs a structured query object (JSON tree) suitable for driving a search, filter, or rule engine. Full keyboard editing of every rule and group is required.

## 2. When to use / when not to use
Use when users need to construct complex multi-field filter queries with nested AND/OR logic (e.g., saved search, audience segmentation, access rule editor). Do not use for simple one-field filtering — use `<mj-filter-panel>`. Do not use as a code editor for raw query languages (SQL, OData); use `<mj-code-editor>`.

## 3. Anatomy
- **query root group** — the outermost `<mj-qb-group>` which cannot be deleted.
- **group** — a bordered region containing a combinator toggle (AND/OR) and a list of children (rules and sub-groups).
- **combinator toggle** — `<mj-segmented-control>` selecting `"AND"` or `"OR"` for the group.
- **rule row** — a horizontal row with: field selector, operator selector, value input(s), and a remove button.
- **field selector** — `<mj-select>` over the consumer-provided field schema.
- **operator selector** — `<mj-select>` populated based on the selected field's type.
- **value input** — dynamically rendered based on operator (text field, number, date picker, multi-select, range slider, or empty for unary operators like `is empty`).
- **add rule button** — appends a new blank rule row to the group.
- **add group button** — appends a new nested sub-group.
- **remove group button** — removes a sub-group and all its children (root group has no remove button).
- **expression preview** — optional read-only text representation of the current query.

## 4. Variants & modes
| Variant / mode | Attribute | Behavior difference |
|----------------|-----------|---------------------|
| Default | (none) | Editable tree with add/remove controls |
| Read-only | `readonly` | Controls disabled; structure visible but not editable |
| Max depth | `max-depth` | Limits nesting to N group levels |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `readonly` | boolean | `false` | Yes | Disables all editing controls |
| `max-depth` | number | `3` | Yes | Maximum nesting depth for sub-groups |
| `show-preview` | boolean | `false` | Yes | Shows the expression preview panel |
| `label` | string | `"Query builder"` | Yes | Accessible name for the component root |
| `add-rule-label` | string | `"Add condition"` | Yes | Label for the add-rule button |
| `add-group-label` | string | `"Add group"` | Yes | Label for the add-group button |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `fieldSchema` | `FieldDef[]` | Array of `{ id, label, type, operators?, options? }` defining available fields |
| `value` | `QueryGroup` | Current query tree: `{ combinator, rules: (QueryRule \| QueryGroup)[] }` |
| `operatorMap` | `Record<FieldType, OperatorDef[]>` | Overrides the default operator list per field type |

## 7. Slots
| Slot | Description |
|------|-------------|
| `value-input-{operatorId}` | Custom value input for a specific operator, receives `field` and `rule` via context |
| `preview` | Replaces the built-in expression preview panel |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-query-change` | `{ value: QueryGroup }` | Yes | No | Fires on every change to the query tree |
| `mj-query-valid` | `{ valid: boolean, errors: ValidationError[] }` | Yes | No | Fires when validity changes (all rules have field, operator, and value) |

## 9. CSS parts & custom properties
**Parts:** `root`, `group`, `group-header`, `combinator`, `rule-row`, `field-select`, `operator-select`, `value-input`, `add-rule`, `add-group`, `remove-rule`, `remove-group`, `preview`.

| Custom property | Default | Description |
|-----------------|---------|-------------|
| `--mj-qb-group-indent` | `var(--mj-space-5)` | Left indent per nesting level |
| `--mj-qb-group-border` | `var(--mj-border-subtle)` | Border of each group container |
| `--mj-qb-group-bg` | `var(--mj-color-surface-2)` | Background of nested groups |
| `--mj-qb-rule-gap` | `var(--mj-space-2)` | Gap between controls within a rule row |
| `--mj-qb-row-gap` | `var(--mj-space-2)` | Gap between rule rows |

## 10. States
- **default** — editable; at least one rule group present.
- **readonly** — all controls disabled; `aria-readonly="true"` on the root.
- **rule-invalid** — a rule row with no field, operator, or value selected; highlighted with error color; `aria-invalid="true"` on the offending input.
- **empty-group** — a group with no rules; shows "Add a condition" placeholder.
- **max-depth-reached** — "Add group" button hidden/disabled when depth limit is met.
- **loading-options** — field or operator selects show spinner while options load asynchronously.

## 11. Behavior & interactions
The query tree is maintained as an immutable value; every edit produces a new `value` tree and emits `mj-query-change`. Adding a rule appends `{ id: uuid(), field: null, operator: null, value: null }` to the group's `rules` array. Selecting a field populates the operator select with `operatorMap[field.type]`. Selecting an operator renders the appropriate value input. Selecting a different field resets operator and value. Removing the last rule from a non-root group offers a confirmation if `confirm-empty-group` attribute is set; otherwise the group itself is removed. Moving a rule between groups is not supported in the UI but can be done via the `value` property.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` / `Shift+Tab` | Navigate through all controls in the builder |
| `Enter` / `Space` | Activate focused button (add rule, add group, remove) |
| `ArrowLeft` / `ArrowRight` | Switch AND/OR combinator on the focused combinator toggle |
| `Delete` on focused remove button | Removes the rule or group; focus moves to previous rule or group header |
| `Escape` | Closes any open select dropdown within a rule |

## 13. Accessibility
The root carries `role="region"` and `aria-label` from the `label` attribute. Each group is a `<div role="group">` with `aria-label="Condition group, AND"` (or OR). The combinator toggle announces state changes via a polite live region: "Group operator changed to OR". Rule rows have `role="group"` with an auto-generated label ("Condition N"). Each remove button is `aria-label="Remove condition N"`. When a rule is removed a polite announcement confirms: "Condition removed". Invalid rules announce `aria-invalid="true"` on the offending value input. The expression preview is a `<pre aria-label="Query expression">` in read-only text.

## 14. Form participation
The component is form-associated; it contributes the JSON-serialized `value` tree to `FormData` under the element's `name` attribute. Validity: the component is invalid if any rule has a `null` field, operator, or value (for non-unary operators). Custom validity message: "One or more conditions are incomplete."

## 15. Internationalization & RTL
All button labels (`add-rule-label`, `add-group-label`, remove labels), combinator labels ("AND", "OR"), and validation messages are overridable via attributes or the localization hook. In RTL, group indentation is on the inline-end side; rule rows flow from end to start.

## 16. Progressive enhancement / SSR
Server renders the initial query as a `<form>` with hidden JSON input. Without JS the form is a static representation; the user cannot edit interactively. On upgrade the component replaces the static markup with the fully interactive tree. Existing query value is read from the hidden input's `value` attribute to restore state.

## 17. Dependencies
- **Foundations:** Registry + base element helper, Design-token stylesheet, Form-association helper, Live-region/announcement service, Localization/formatting hook.
- **Components:** `<mj-select>`, `<mj-segmented-control>`, `<mj-text-field>`, `<mj-number-field>`, `<mj-date-picker>`, `<mj-checkbox-group>`, `<mj-slider>`, `<mj-button>`.

## 18. Edge cases & error handling
- `fieldSchema` is empty: field selects show "No fields configured" disabled option; add-rule button disabled.
- `value` set with a depth exceeding `max-depth`: excess groups are rendered read-only with a warning.
- Circular `QueryGroup` reference in `value`: detected on set; error thrown; previous value retained.
- Field removed from `fieldSchema` while a rule uses it: rule shows the field ID in red as "Unknown field"; rule is marked invalid.
- Very large rule trees (50+ rules): no virtualization needed at this scale; performance tested to 100 rules.

## 19. Acceptance criteria
- [ ] `mj-query-change` fires with a structurally valid `QueryGroup` on every edit.
- [ ] AND/OR combinator toggle changes the group operator and emits a change event.
- [ ] Adding a sub-group nests a new group inside the current group.
- [ ] `max-depth` prevents adding groups beyond the limit.
- [ ] Invalid rules marked with `aria-invalid`; `mj-query-valid` fires `{ valid: false }`.
- [ ] Form-associated: serialized value appears in `FormData`.
- [ ] Keyboard: all controls reachable; remove focuses previous sibling.
- [ ] Axe scan reports zero violations.
- [ ] RTL: group indentation flips to inline-end.
- [ ] Light, dark, high-contrast, and RTL rendering verified.

## 20. Open questions
- Should drag-and-drop rule reordering within a group be in scope for P2?
- Should the expression preview support a human-readable NL format as well as a technical JSON view?
