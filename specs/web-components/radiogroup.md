# Radio Group Spec

- **Tag:** `<mj-radio-group>`
- **Class / file:** `MjRadioGroup` / `mjradiogroup.js`
- **Category:** Selection & dropdown-style controls
- **Primary or Variant:** Primary
- **Synonyms covered:** Radio group, Mutually exclusive choice set
- **Phase:** P0
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-radio-group>` presents a set of mutually exclusive options where exactly one (or zero, before first interaction) may be selected. It wraps `<mj-radio>` child elements and manages roving tabindex, group-level ARIA, and form participation so the pattern conforms to the WAI-ARIA `radiogroup` / `radio` authoring practice.

## 2. When to use / when not to use
**Use** when the user must choose exactly one option from 2–7 visible choices. **Use** when all options should be visible simultaneously (unlike `<mj-select>`). **Do not use** when there are more than ~7 options — prefer `<mj-select>`. **Do not use** for independent on/off choices — use `<mj-checkbox-group>`. **Do not use** when the choice is binary and phrased as on/off — use a checkbox or toggle button.

## 3. Anatomy
- **Group container** (`part="group"`) — `role="radiogroup"` wrapper.
- **Group label** (`part="group-label"`) — visible `<legend>`-equivalent text; referenced by `aria-labelledby`.
- **Radio** (`part="radio"`) — individual `<mj-radio>` child; contains a visual control and label.
- **Radio input** (`part="radio-input"`) — the circular visual indicator.
- **Radio label** (`part="radio-label"`) — text label beside the indicator.
- **Radio description** (`part="radio-description"`) — optional secondary text per option.
- **Help text** (`part="help"`) — group-level hint text below the group.
- **Error message** (`part="error"`) — group-level error message when invalid.

## 4. Variants & modes
| Variant / mode | Attribute | Behavior |
|----------------|-----------|----------|
| Vertical (default) | `orientation="vertical"` | Radios stacked in a column |
| Horizontal | `orientation="horizontal"` | Radios arranged in a row |
| With descriptions | slot `description` on `<mj-radio>` | Secondary text under each radio label |
| Button-style | `variant="button"` | Radios styled as toggle buttons; same semantics |
| Disabled group | `disabled` | All radios disabled |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `name` | string | `""` | Yes | Form field name shared by all radios in the group |
| `value` | string | `""` | Yes | Value of the currently selected radio |
| `disabled` | boolean | `false` | Yes | Disables all radios in the group |
| `required` | boolean | `false` | Yes | A selection is required for form validity |
| `readonly` | boolean | `false` | Yes | Selection cannot be changed; value is submitted |
| `invalid` | boolean | `false` | Yes | Forces error visual and ARIA state on the group |
| `orientation` | `"vertical"` \| `"horizontal"` | `"vertical"` | Yes | Layout direction of radio options |
| `variant` | `"default"` \| `"button"` | `"default"` | Yes | Visual presentation style |
| `label` | string | `""` | Yes | Accessible group label (alternative to slotting a label) |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `radios` | `MjRadio[]` | Live array of child `<mj-radio>` elements |
| `selectedRadio` | `MjRadio \| null` | Currently selected `<mj-radio>` element |
| `validity` | `ValidityState` | Delegated from `ElementInternals` |
| `validationMessage` | `string` | Localizable invalid message |

## 7. Slots
| Slot | Description |
|------|-------------|
| `label` | Group label element (renders as group heading) |
| (default) | `<mj-radio>` elements |
| `help` | Help text below the group |
| `error` | Error message shown when invalid |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-change` | `{ value: string, previousValue: string, radio: MjRadio }` | Yes | No | Fired when the selected radio changes |

## 9. CSS parts & custom properties
**Parts:** `group`, `group-label`, `radio`, `radio-input`, `radio-label`, `radio-description`, `help`, `error`

**Custom properties:**
| Property | Default token | Description |
|----------|---------------|-------------|
| `--mj-radio-group-gap` | `--mj-space-2` | Gap between radio items |
| `--mj-radio-size` | `1rem` | Diameter of the radio circle indicator |
| `--mj-radio-color` | `--mj-color-accent` | Selected state fill color |
| `--mj-radio-border-color` | `--mj-color-border` | Unselected border color |
| `--mj-radio-label-gap` | `--mj-space-2` | Gap between indicator and label |

## 10. States
| State | Visual effect | ARIA effect |
|-------|--------------|-------------|
| Unselected radio | Empty circle | `aria-checked="false"` |
| Selected radio | Filled circle with dot | `aria-checked="true"` |
| Focused radio | Focus ring around indicator | Part of roving tabindex |
| Hover radio | Border highlight on indicator | — |
| Disabled radio | Muted indicator and label | `aria-disabled="true"` |
| Disabled group | All radios muted | `aria-disabled="true"` on group |
| Invalid group | Error border/icon; error message shown | `aria-invalid="true"` on group |
| Readonly | No pointer cursor; no keyboard change | `aria-readonly="true"` on group |

## 11. Behavior & interactions
- Only one radio in the group can be selected at a time; selecting a radio deselects all others.
- Roving tabindex: only the selected radio (or the first radio if none selected) is in the tab sequence. Arrow keys move focus and selection among radios.
- `<mj-radio>` elements with `disabled` are skipped by arrow-key navigation.
- Clicking a radio that is already selected does nothing (no deselect).
- In `readonly` mode, arrow keys and clicks do not change the selection.
- `variant="button"` renders radios as styled buttons but retains the same `radiogroup`/`radio` semantics.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` | Enter the group (focuses the selected or first radio); leave the group |
| `ArrowDown` / `ArrowRight` | Move focus and selection to the next radio |
| `ArrowUp` / `ArrowLeft` | Move focus and selection to the previous radio |
| `Space` | Select the focused radio (if not already selected) |
| `Home` | Move focus and selection to the first radio |
| `End` | Move focus and selection to the last radio |

## 13. Accessibility
- Container has `role="radiogroup"` with `aria-labelledby` pointing to the group label element's `id`.
- Each radio has `role="radio"` with `aria-checked` (`"true"` or `"false"`) and `aria-labelledby` pointing to its label.
- Disabled radios have `aria-disabled="true"` and are excluded from roving tabindex.
- Error state adds `aria-describedby` on the group pointing to the error message element.
- Help text is associated via `aria-describedby` on the group.
- Selection change announces via the newly focused radio's label (inherent in roving tabindex; no explicit live region needed).
- Minimum touch target per radio: 44 × 44 px.

## 14. Form participation
- Form-associated via `ElementInternals` on `<mj-radio-group>`.
- Contributes `name=value` where `value` is the `value` attribute of the selected `<mj-radio>`.
- On form reset, reverts to the radio whose `checked` attribute was present on initial parse, or empty.
- `required`: `validity.valueMissing` when no radio is selected.
- Custom validity messages localizable via `setCustomValidity(msg)` on the group.

## 15. Internationalization & RTL
- In RTL, the radio indicator appears on the right side of the label; `margin-inline-end` used.
- Horizontal orientation reverses visual order in RTL but `values` array order is preserved.
- All label and description text is author-supplied; no built-in English strings.

## 16. Progressive enhancement / SSR
- Server renders a `<fieldset>` with a `<legend>` and `<input type="radio">` elements inside `<mj-radio-group>`.
- Before upgrade the native radios are fully functional.
- On upgrade, native inputs are hidden and replaced with the custom UI; the group reads `name`, `value`, and `checked` from the native inputs.
- Without scripting, native radios render and function normally.

## 17. Dependencies
- Section 6: Registry/base element, design tokens, focus utilities (roving tabindex), form-association helper.
- `<mj-radio>` — individual radio primitive (companion element defined in the same module).

## 18. Edge cases & error handling
- Single radio in group: valid; user can select it but cannot deselect it via keyboard.
- All radios disabled: group is navigable but nothing can be selected; `required` validation fails on submit.
- `value` set to a string matching no child radio: no radio is checked; state is held but no visual selection.
- Radios added or removed dynamically: roving tabindex recalculates; if the selected radio is removed, `value` is cleared.
- `orientation="horizontal"` with many options: wraps in a flex container; no truncation of labels.

## 19. Acceptance criteria
- [ ] Clicking a radio selects it and deselects all others; `mj-change` fires.
- [ ] Arrow keys move focus and selection; `Tab` moves through the group as a single stop.
- [ ] Only the selected (or first) radio is in the tab sequence at any time.
- [ ] `required` with no selection fails `checkValidity()`.
- [ ] Form submission includes `name=value` for the selected radio.
- [ ] `aria-checked="true"` present on selected radio; `"false"` on all others.
- [ ] `role="radiogroup"` on container; `role="radio"` on each option.
- [ ] Disabled radios are skipped by arrow navigation; cannot be clicked.
- [ ] axe-core reports zero violations in default, selected, disabled, and invalid states.
- [ ] RTL layout positions indicator on the trailing side of labels.

## 20. Open questions
- Should `<mj-radio-group>` support a "deselect" affordance (clicking the selected radio deselects it) similar to some UI systems, or always require a selection once made?
- Should `variant="button"` be a separate `<mj-segmented-control>` concern or is it appropriate here?
- Should `<mj-radio>` be a standalone form-associated element, or only valid inside `<mj-radio-group>`?
