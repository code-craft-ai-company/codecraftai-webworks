# Checkbox Group Spec

- **Tag:** `<mj-checkbox-group>`
- **Class / file:** `MjCheckboxGroup` / `mjcheckboxgroup.js`
- **Category:** Selection & dropdown-style controls
- **Primary or Variant:** Primary
- **Synonyms covered:** Checkbox group, Multi-select checkbox list
- **Phase:** P0
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-checkbox-group>` renders a labeled group of independent boolean choices, each represented by an `<mj-checkbox>` child. It optionally provides a "select all" parent checkbox that reflects the tri-state (none / some / all) of its children and drives bulk toggle. The group exposes an aggregated value array and a single form field name, making it easy to wire to a form.

## 2. When to use / when not to use
**Use** when the user may pick any combination of options (zero to all). **Use "select all"** when bulk selection/deselection is a common task. **Do not use** for mutually exclusive choices — prefer `<mj-radio-group>`. **Do not use** for a single boolean toggle — prefer a standalone `<mj-checkbox>` or `<mj-toggle>`. **Do not use** when options are numerous or searchable — combine with `<mj-listbox>` in multi mode.

## 3. Anatomy
- **Group container** (`part="group"`) — `role="group"` wrapper.
- **Group label** (`part="group-label"`) — visible heading for the group; referenced by `aria-labelledby`.
- **Select-all checkbox** (`part="select-all"`) — optional parent `<mj-checkbox>` with indeterminate state.
- **Checkbox** (`part="checkbox"`) — each child `<mj-checkbox>` element.
- **Checkbox input** (`part="checkbox-input"`) — the square visual indicator.
- **Checkbox label** (`part="checkbox-label"`) — text label.
- **Checkbox description** (`part="checkbox-description"`) — optional secondary text.
- **Help text** (`part="help"`) — group-level hint text.
- **Error message** (`part="error"`) — group-level error when invalid.

## 4. Variants & modes
| Variant / mode | Attribute | Behavior |
|----------------|-----------|----------|
| Vertical (default) | `orientation="vertical"` | Checkboxes stacked |
| Horizontal | `orientation="horizontal"` | Checkboxes in a row |
| With select-all | `select-all` (boolean) | Adds parent checkbox; tri-state reflects children |
| With descriptions | slot `description` on `<mj-checkbox>` | Secondary text per item |
| Disabled group | `disabled` | All checkboxes disabled |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `name` | string | `""` | Yes | Form field name; each checked value is submitted as `name=value` |
| `value` | string | `""` | Yes | Comma-separated list of checked values |
| `disabled` | boolean | `false` | Yes | Disables all checkboxes |
| `required` | boolean | `false` | Yes | At least one checkbox must be checked |
| `readonly` | boolean | `false` | Yes | Prevents changes; submits current value |
| `invalid` | boolean | `false` | Yes | Forces error visual and ARIA state |
| `select-all` | boolean | `false` | Yes | Shows a "select all" checkbox above the group |
| `select-all-label` | string | `"Select all"` | Yes | Label for the select-all checkbox |
| `orientation` | `"vertical"` \| `"horizontal"` | `"vertical"` | Yes | Layout direction |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `checkboxes` | `MjCheckbox[]` | Live array of child `<mj-checkbox>` elements (excludes the select-all) |
| `checkedValues` | `string[]` | Array of `value` strings for all checked checkboxes |
| `selectAllState` | `"none"` \| `"some"` \| `"all"` | Current tri-state of the select-all checkbox |
| `validity` | `ValidityState` | Delegated from `ElementInternals` |
| `validationMessage` | `string` | Localizable invalid message |

## 7. Slots
| Slot | Description |
|------|-------------|
| `label` | Group label element |
| (default) | `<mj-checkbox>` elements |
| `help` | Help text below the group |
| `error` | Error message shown when invalid |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-change` | `{ checkedValues: string[], changedCheckbox: MjCheckbox, checked: boolean }` | Yes | No | Fired when any checkbox changes |
| `mj-select-all` | `{ checked: boolean }` | Yes | No | Fired when the select-all checkbox is toggled |

## 9. CSS parts & custom properties
**Parts:** `group`, `group-label`, `select-all`, `checkbox`, `checkbox-input`, `checkbox-label`, `checkbox-description`, `help`, `error`

**Custom properties:**
| Property | Default token | Description |
|----------|---------------|-------------|
| `--mj-checkbox-group-gap` | `--mj-space-2` | Gap between checkbox items |
| `--mj-checkbox-size` | `1rem` | Width and height of the checkbox indicator |
| `--mj-checkbox-color` | `--mj-color-accent` | Checked fill color |
| `--mj-checkbox-border-color` | `--mj-color-border` | Unchecked border color |
| `--mj-checkbox-indeterminate-color` | `--mj-color-accent` | Indeterminate state fill color |
| `--mj-checkbox-label-gap` | `--mj-space-2` | Gap between indicator and label |

## 10. States
| State | Visual effect | ARIA effect |
|-------|--------------|-------------|
| Unchecked | Empty square | `aria-checked="false"` |
| Checked | Checkmark in filled square | `aria-checked="true"` |
| Indeterminate (select-all) | Dash in filled square | `aria-checked="mixed"` |
| Focused | Focus ring around indicator | Native focus |
| Hover | Border highlight | — |
| Disabled item | Muted indicator and label | `aria-disabled="true"` |
| Disabled group | All items muted | `aria-disabled="true"` on group |
| Invalid group | Error border; error message shown | `aria-invalid="true"` on group |
| Readonly | No pointer cursor; no change | `aria-readonly="true"` on group |

## 11. Behavior & interactions
- Each `<mj-checkbox>` operates independently; checking one does not affect others.
- When `select-all` is enabled:
  - If all child checkboxes are checked, the select-all shows "checked" (`aria-checked="true"`).
  - If none are checked, the select-all shows "unchecked" (`aria-checked="false"`).
  - If some are checked, the select-all shows "indeterminate" (`aria-checked="mixed"`).
  - Clicking the select-all when `"none"` or `"some"` checks all non-disabled checkboxes.
  - Clicking the select-all when `"all"` unchecks all non-disabled checkboxes.
- Disabled checkboxes are excluded from the select-all calculation.
- In `readonly` mode, clicks and keyboard activation are ignored.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` | Move focus to each checkbox in DOM order (each is an independent tab stop) |
| `Space` | Toggle the focused checkbox |
| `Enter` | Toggle the focused checkbox (consistent with button behavior) |

## 13. Accessibility
- Container has `role="group"` with `aria-labelledby` pointing to the group label's `id`.
- Each `<mj-checkbox>` has `role="checkbox"` with `aria-checked` (`"true"`, `"false"`, or `"mixed"` for select-all).
- The select-all checkbox has `aria-checked="mixed"` in the indeterminate state per WAI-ARIA spec.
- Error message is associated via `aria-describedby` on the group.
- Help text is associated via `aria-describedby` on the group.
- `aria-invalid="true"` on the group container when `invalid`.
- Each checkbox is an independent tab stop (unlike radio group); this is correct WAI-ARIA behavior for checkbox groups.
- Minimum touch target per checkbox: 44 × 44 px.

## 14. Form participation
- Form-associated via `ElementInternals` on `<mj-checkbox-group>`.
- Each checked value appended to `FormData` as `name=value` (matching native `<input type="checkbox">` behavior); unchecked values are not submitted.
- On form reset, reverts to the initially `checked` child checkboxes.
- `required`: `validity.valueMissing` when no checkbox is checked.

## 15. Internationalization & RTL
- In RTL, checkbox indicator appears on the right; `margin-inline-end` used for spacing.
- The `select-all-label` attribute is the only built-in string; it should be overridden for non-English locales.
- Horizontal orientation reverses visual order in RTL; `FormData` order follows DOM order regardless.

## 16. Progressive enhancement / SSR
- Server renders a `<fieldset>` with `<legend>` and `<input type="checkbox">` elements.
- Before upgrade, native checkboxes are fully functional.
- On upgrade, native inputs are hidden; the component reads `name`, `value`, and `checked` from each native input and builds the custom UI; a hidden native input mirrors each checked state for form submission.
- Without scripting, native checkboxes render and function normally.

## 17. Dependencies
- Section 6: Registry/base element, design tokens, form-association helper, live-region service.
- `<mj-checkbox>` — individual checkbox primitive (companion element).

## 18. Edge cases & error handling
- All checkboxes disabled: group is navigable; `required` validation will always fail.
- `value` attribute references values not matching any child: no checkboxes are checked; state held until children are added.
- Checkboxes added or removed dynamically: select-all state recalculates immediately.
- Clicking select-all when all children are disabled: no-op.
- Very many checkboxes (>50): layout remains scrollable within the group's natural height; no virtualization needed (full-DOM is intentional for checkbox groups).

## 19. Acceptance criteria
- [ ] Checking a checkbox fires `mj-change` with `checkedValues` containing all currently checked values.
- [ ] Select-all shows indeterminate state when some-but-not-all are checked.
- [ ] Clicking select-all from indeterminate checks all non-disabled; from all-checked unchecks all.
- [ ] `aria-checked="mixed"` on select-all in indeterminate state.
- [ ] `required` with no checked boxes fails `checkValidity()`.
- [ ] Form submission includes one `name=value` entry per checked checkbox; unchecked are absent.
- [ ] `Tab` moves focus through each checkbox independently.
- [ ] `Space` toggles the focused checkbox.
- [ ] axe-core reports zero violations in default, indeterminate, disabled, and invalid states.
- [ ] RTL positions indicator on the trailing side.

## 20. Open questions
- Should the component support nested checkbox groups (sub-groups with their own select-all)?
- Should disabled checkboxes be included or excluded from the indeterminate count for the select-all?
- Is a maximum number of checkboxes per group recommended, or left entirely to the author?
