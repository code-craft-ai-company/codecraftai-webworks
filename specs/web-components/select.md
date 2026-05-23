# Select Spec

- **Tag:** `<mj-select>`
- **Class / file:** `MjSelect` / `mjselect.js`
- **Category:** Selection & dropdown-style controls
- **Primary or Variant:** Primary
- **Synonyms covered:** Dropdown, Select box, Dropdown list, Dropdown listbox
- **Phase:** P0
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-select>` is a single-choice dropdown control that enhances a native `<select>` element with rich option content (icons, descriptions, grouping, custom styling) while preserving full keyboard operability and form participation. It solves the styling and content limitations of the native `<select>` without sacrificing accessibility or progressive enhancement.

## 2. When to use / when not to use
**Use** when the user must choose exactly one item from a known, finite list of 4–15 options and space is constrained. **Use** option groups when options have a meaningful hierarchy. **Do not use** when the list exceeds ~30 items — prefer `<mj-combobox>` with search. **Do not use** for binary choices — prefer a checkbox or toggle. **Do not use** when all options should be visible simultaneously — prefer `<mj-listbox>`.

## 3. Anatomy
- **Trigger button** (`part="trigger"`) — shows the selected label/placeholder; opens the popup on click/key.
- **Selected icon** (`part="selected-icon"`) — optional icon mirroring the chosen option's icon.
- **Selected label** (`part="selected-label"`) — text of the current selection.
- **Chevron** (`part="chevron"`) — open/close indicator icon.
- **Popup** (`part="popup"`) — positioned overlay containing the listbox; managed by the overlay engine.
- **Listbox** (`part="listbox"`) — `role="listbox"` container; holds option and optgroup elements.
- **Option** (`part="option"`) — individual choice item (`role="option"`).
- **Option icon** (`part="option-icon"`) — optional leading icon per option.
- **Option description** (`part="option-description"`) — secondary text per option.
- **Optgroup** (`part="optgroup"`) — labeled group of options (`role="group"`).
- **No-results** (`part="no-results"`) — shown when an option list is empty.

## 4. Variants & modes
| Variant / mode | Attribute | Behavior |
|----------------|-----------|----------|
| Default (closed) | — | Trigger visible; popup hidden |
| Open | `open` (boolean) | Popup visible; listbox receives keyboard focus via `aria-activedescendant` |
| With placeholder | `placeholder="…"` | Shows placeholder text when no value is set; placeholder is not a valid option |
| With icons | slot `icon` on `<mj-option>` | Icon renders in trigger and in option rows |
| With descriptions | slot `description` on `<mj-option>` | Secondary text below option label |
| Grouped | `<mj-optgroup>` children | Options organized under labeled groups |
| Disabled | `disabled` (boolean) | Trigger not interactive; value not submitted |
| Read-only | `readonly` (boolean) | Trigger not interactive but value IS submitted |
| Invalid | `invalid` (boolean) | Error styling; `aria-invalid="true"` on combobox |
| Small / large | `size="sm"` \| `"md"` \| `"lg"` | Controls trigger height and option row density |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `name` | string | `""` | Yes | Form field name |
| `value` | string | `""` | Yes | Currently selected option value |
| `placeholder` | string | `""` | Yes | Text shown when no value selected |
| `disabled` | boolean | `false` | Yes | Disables the control |
| `readonly` | boolean | `false` | Yes | Prevents changes; submits current value |
| `required` | boolean | `false` | Yes | Marks field as required for form validation |
| `invalid` | boolean | `false` | Yes | Forces error visual state |
| `open` | boolean | `false` | Yes | Opens/closes the popup programmatically |
| `size` | `"sm"` \| `"md"` \| `"lg"` | `"md"` | Yes | Visual size variant |
| `label` | string | `""` | Yes | Accessible label (alternative to `<label for>`) |
| `autocomplete` | string | `"off"` | Yes | Forwarded to the internal hidden input |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `options` | `MjOption[]` | Live array of all `<mj-option>` descendants |
| `selectedOption` | `MjOption \| null` | Reference to the currently selected option element |
| `validity` | `ValidityState` | Delegated from `ElementInternals` |
| `validationMessage` | `string` | Localizable invalid message |

## 7. Slots
| Slot | Description |
|------|-------------|
| (default) | `<mj-option>` and `<mj-optgroup>` elements |
| `trigger-prefix` | Optional icon/element before the selected label in the trigger |
| `no-results` | Custom empty state content when no options are available |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-change` | `{ value: string, previousValue: string, option: MjOption }` | Yes | No | Fired when selected value changes |
| `mj-open` | `{}` | Yes | Yes | Fired before popup opens; cancel to prevent |
| `mj-close` | `{}` | Yes | No | Fired after popup closes |

## 9. CSS parts & custom properties
**Parts:** `trigger`, `selected-icon`, `selected-label`, `chevron`, `popup`, `listbox`, `option`, `option-icon`, `option-label`, `option-description`, `optgroup`, `optgroup-label`, `no-results`

**Custom properties:**
| Property | Default token | Description |
|----------|---------------|-------------|
| `--mj-select-trigger-height` | `--mj-size-control-md` | Trigger button height |
| `--mj-select-popup-max-height` | `18rem` | Max height of the dropdown popup |
| `--mj-select-popup-min-width` | `trigger width` | Min width of the popup |
| `--mj-select-option-padding` | `--mj-space-2 --mj-space-3` | Padding per option row |
| `--mj-select-border-radius` | `--mj-radius-md` | Trigger and popup corner radius |

## 10. States
| State | Visual effect | ARIA effect |
|-------|--------------|-------------|
| Default | Normal trigger border/fill | — |
| Hover | Trigger border highlights | — |
| Focus-visible | Trigger focus ring | — |
| Open | Chevron rotated; popup visible | `aria-expanded="true"` on trigger |
| Selected option | Option has checkmark; trigger shows label | `aria-selected="true"` on option |
| Disabled | Muted trigger; no pointer events | `aria-disabled="true"`; excluded from tab order |
| Read-only | No pointer cursor; no hover fill | `aria-readonly="true"` |
| Invalid | Error border/icon on trigger | `aria-invalid="true"` on trigger |
| Loading | Spinner replaces chevron | `aria-busy="true"` on listbox |

## 11. Behavior & interactions
- Clicking the trigger toggles the popup open/closed.
- The popup is positioned below the trigger by default; the overlay engine flips it above when there is insufficient viewport space below.
- The popup width matches at minimum the trigger width.
- Clicking an option selects it, closes the popup, and returns focus to the trigger.
- Clicking outside the popup (light-dismiss) closes it without changing the value.
- If `<mj-select>` wraps a native `<select>` in light DOM, it reads the native options on upgrade and keeps them in sync for SSR fallback.
- The popup uses `aria-activedescendant` on the listbox to track the focused option without moving DOM focus out of the trigger.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Enter` / `Space` | Open popup when closed; select focused option when open |
| `ArrowDown` | Open popup if closed; move focus to next option |
| `ArrowUp` | Open popup if closed; move focus to previous option |
| `Home` | Move focus to first option |
| `End` | Move focus to last option |
| `Escape` | Close popup; return focus to trigger; cancel selection |
| `Tab` | Close popup; move focus to next focusable element |
| Printable character | Type-ahead: advance focus to first matching option |

## 13. Accessibility
- Trigger uses `role="combobox"` with `aria-haspopup="listbox"`, `aria-expanded`, and `aria-controls` pointing to the listbox `id`.
- Listbox uses `role="listbox"` with `aria-labelledby` pointing to the trigger's label.
- Each option uses `role="option"` with `aria-selected`.
- Disabled options have `aria-disabled="true"` and are skipped by keyboard navigation.
- Optgroups use `role="group"` with `aria-labelledby` pointing to their label element.
- Selection change is announced via the trigger's accessible name update (the label changes), picked up by screen readers without a live region.
- Minimum touch target for the trigger: 44 × 44 px.

## 14. Form participation
- Form-associated via `ElementInternals`; contributes `name=value` to `FormData`.
- When `required` and no value is set, `validity.valueMissing` is `true`.
- Custom validity message localizable via `setCustomValidity(msg)`.
- On form reset, value reverts to the initial `value` attribute or the first non-disabled option if no default is declared.

## 15. Internationalization & RTL
- Chevron flips horizontally in RTL layouts (CSS `[dir=rtl]` or inherited `direction`).
- Option list order is preserved; collation is the author's responsibility.
- Placeholder and group labels are author-supplied; no built-in English strings.
- Popup repositions correctly in RTL; `inset-inline-start` used for alignment.

## 16. Progressive enhancement / SSR
- Server renders a native `<select>` with `<option>` and `<optgroup>` children inside `<mj-select>`.
- Before upgrade the native `<select>` is fully functional.
- On upgrade the component hides the native `<select>` (visually and from AT), reads its options, builds the custom UI, and keeps the native `<select>` in sync for form submission.
- If scripting is disabled, the native `<select>` is left visible and functional.

## 17. Dependencies
- Section 6: Registry/base element, design tokens, overlay/positioning engine, focus utilities (`aria-activedescendant` helper), form-association helper, live-region service.
- `<mj-option>` — individual option primitive (shared with Listbox, Combobox).
- `<mj-optgroup>` — option group primitive.

## 18. Edge cases & error handling
- Zero options: show `no-results` slot content; trigger is disabled automatically.
- All options disabled: trigger is not disabled; selection is empty; required validation fires.
- Value set via attribute that does not match any option: value is held but no option shows `aria-selected`; triggers `invalid` when form is submitted.
- Very long option labels: truncate with ellipsis in trigger; full text visible on hover via tooltip; options wrap in popup.
- Popup taller than viewport: scrollable listbox capped at `--mj-select-popup-max-height`; selected option scrolled into view on open.
- Dynamic option addition/removal while open: listbox re-renders; `aria-activedescendant` updated.

## 19. Acceptance criteria
- [ ] Selecting an option fires `mj-change` with correct `value` and `previousValue`.
- [ ] `open` attribute toggles popup visibility and `aria-expanded` in sync.
- [ ] Keyboard navigation (arrows, Home, End, Enter, Escape, type-ahead) works without a pointing device.
- [ ] Form submission includes `name=value`; reset restores the original value.
- [ ] `required` with no value fails constraint validation; `reportValidity()` shows a message.
- [ ] Popup flips above trigger when insufficient space below.
- [ ] `disabled` option is skipped by keyboard navigation and cannot be clicked.
- [ ] axe-core reports zero violations in default, open, disabled, and invalid states.
- [ ] RTL layout positions popup correctly and flips chevron.
- [ ] Native `<select>` fallback is functional with scripting disabled.
- [ ] Light and dark themes render without hard-coded colors.

## 20. Open questions
- Should `<mj-select>` support multi-select (via a `multiple` attribute) or is that strictly `<mj-listbox>`'s responsibility?
- Should type-ahead matching be case-insensitive only, or also diacritic-insensitive for i18n correctness?
- What is the correct behavior when `value` is set programmatically while the popup is open?
