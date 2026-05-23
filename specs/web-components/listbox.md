# Listbox Spec

- **Tag:** `<mj-listbox>`
- **Class / file:** `MjListbox` / `mjlistbox.js`
- **Category:** Selection & dropdown-style controls
- **Primary or Variant:** Primary
- **Synonyms covered:** Multi-select listbox
- **Phase:** P0
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-listbox>` is a permanently visible scrollable list of selectable options. Unlike `<mj-select>`, its options are always on screen — no trigger or popup is involved. It supports both single-select and multiple-select modes with shift-click and ctrl-click range selection, making it suitable for selection panels, filter sidebars, and transfer-list panes.

## 2. When to use / when not to use
**Use** when 5 or more items need to be visible simultaneously and the user may select one or many. **Use multi mode** when the user needs to pick several values (e.g., a permission set). **Do not use** for fewer than 4 items where a radio group or checkbox group would read more clearly. **Do not use** inside a popup — that is `<mj-select>`'s listbox. **Do not use** for navigation links — prefer `<mj-tree-navigation>` or a `<nav>` list.

## 3. Anatomy
- **Listbox container** (`part="listbox"`) — the `role="listbox"` scroll region.
- **Option** (`part="option"`) — each selectable row (`role="option"`).
- **Option checkbox** (`part="option-checkbox"`) — visible check indicator in multi mode.
- **Option icon** (`part="option-icon"`) — optional leading icon.
- **Option label** (`part="option-label"`) — primary text.
- **Option description** (`part="option-description"`) — secondary text.
- **Optgroup** (`part="optgroup"`) — labeled group (`role="group"`).
- **Optgroup label** (`part="optgroup-label"`) — group heading.
- **Empty state** (`part="empty"`) — shown when no options are slotted.

## 4. Variants & modes
| Variant / mode | Attribute | Behavior |
|----------------|-----------|----------|
| Single select | `multiple` absent | One option selected at a time; roving tabindex |
| Multiple select | `multiple` (boolean) | Shift+click range; Ctrl+click toggle; checkboxes visible |
| With optgroups | `<mj-optgroup>` children | Sections with non-selectable group headers |
| Compact | `size="sm"` | Reduced option row height |
| Full-height | `size="lg"` | Increased row height |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `name` | string | `""` | Yes | Form field name; in multi mode values are comma-joined |
| `value` | string | `""` | Yes | Selected value(s); comma-separated in multi mode |
| `multiple` | boolean | `false` | Yes | Enables multi-selection mode |
| `disabled` | boolean | `false` | Yes | Disables the entire listbox |
| `required` | boolean | `false` | Yes | At least one selection required for form validity |
| `readonly` | boolean | `false` | Yes | Selection cannot be changed; value is submitted |
| `size` | `"sm"` \| `"md"` \| `"lg"` | `"md"` | Yes | Visual density variant |
| `label` | string | `""` | Yes | Accessible label (when no external `<label>` is used) |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `options` | `MjOption[]` | Live array of all `<mj-option>` descendants |
| `selectedOptions` | `MjOption[]` | Currently selected option elements |
| `selectedValues` | `string[]` | Array of selected `value` strings |
| `validity` | `ValidityState` | Delegated from `ElementInternals` |
| `validationMessage` | `string` | Localizable invalid message |

## 7. Slots
| Slot | Description |
|------|-------------|
| (default) | `<mj-option>` and `<mj-optgroup>` elements |
| `empty` | Custom content displayed when no options are slotted |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-change` | `{ values: string[], previousValues: string[], selectedOptions: MjOption[] }` | Yes | No | Fired when selection changes |
| `mj-option-focus` | `{ option: MjOption }` | Yes | No | Fired when keyboard focus moves to an option |

## 9. CSS parts & custom properties
**Parts:** `listbox`, `option`, `option-checkbox`, `option-icon`, `option-label`, `option-description`, `optgroup`, `optgroup-label`, `empty`

**Custom properties:**
| Property | Default token | Description |
|----------|---------------|-------------|
| `--mj-listbox-min-height` | `8rem` | Minimum scrolling area height |
| `--mj-listbox-max-height` | `24rem` | Maximum height before scroll |
| `--mj-listbox-option-height` | `--mj-size-control-md` | Row height in default size |
| `--mj-listbox-option-padding` | `--mj-space-2 --mj-space-3` | Horizontal/vertical option padding |
| `--mj-listbox-border-radius` | `--mj-radius-md` | Container corner radius |
| `--mj-listbox-selected-bg` | `--mj-color-selected-subtle` | Selected row background |

## 10. States
| State | Visual effect | ARIA effect |
|-------|--------------|-------------|
| Default | Normal border/fill on container | — |
| Option hover | Subtle highlight on hovered row | — |
| Option focused | Focus ring on focused row | `aria-activedescendant` updated on listbox |
| Option selected | Check indicator; highlighted background | `aria-selected="true"` |
| Option disabled | Muted row; no pointer events | `aria-disabled="true"` |
| Listbox disabled | All rows muted; no interactions | `aria-disabled="true"` on listbox |
| Required invalid | Error border on container | `aria-invalid="true"` on listbox |
| Empty | `empty` slot content shown | — |

## 11. Behavior & interactions
- In single mode, clicking an option deselects any previous selection and selects the clicked option.
- In multi mode, clicking an option toggles its selection. Shift+click selects a contiguous range from the last clicked option to the current. Ctrl+click (Cmd+click on macOS) toggles individual items without clearing others.
- `aria-activedescendant` on the listbox element tracks the focused option; DOM focus remains on the listbox itself.
- Scrollable container scrolls the focused option into view when keyboard focus moves.
- When `multiple` is toggled at runtime, selection is cleared to avoid inconsistent state.
- A `readonly` listbox allows keyboard navigation and visual focus but ignores activation keys.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `ArrowDown` | Move focus to next option (wraps at bottom in single mode) |
| `ArrowUp` | Move focus to previous option (wraps at top in single mode) |
| `Home` | Move focus to first option |
| `End` | Move focus to last option |
| `Enter` / `Space` | Toggle selection of focused option |
| `Shift+ArrowDown` | Extend selection downward (multi mode) |
| `Shift+ArrowUp` | Extend selection upward (multi mode) |
| `Shift+Home` | Extend selection to first option (multi mode) |
| `Shift+End` | Extend selection to last option (multi mode) |
| `Ctrl+A` | Select all options (multi mode) |
| Printable character | Type-ahead: focus first matching option |

## 13. Accessibility
- Container has `role="listbox"` with `aria-multiselectable="true"` when `multiple`.
- `aria-label` or `aria-labelledby` applied from the `label` attribute or an associated external label.
- Each option has `role="option"` and `aria-selected`.
- Disabled options have `aria-disabled="true"` and are still focusable (WCAG 2.1 convention for listbox) but not activatable.
- Optgroups use `role="group"` with `aria-labelledby`.
- The listbox itself holds tab focus; options are navigated via `aria-activedescendant`.
- Selection change in multi mode announces count via a polite live region: e.g., "3 items selected".

## 14. Form participation
- Form-associated via `ElementInternals`.
- Single mode: contributes `name=value`.
- Multi mode: appends one `name=value` entry per selected value in `FormData` (matching native `<select multiple>` behavior).
- On form reset, reverts to the initial `value` attribute.
- `required` in single mode: `validity.valueMissing` when nothing is selected. In multi mode: at least one selection required.

## 15. Internationalization & RTL
- Option layout mirrors in RTL: checkbox and icon on the right side.
- Group labels and option text are author-supplied; no built-in English strings.
- Type-ahead uses locale-insensitive prefix matching by default; an author-supplied `collator` property allows locale-aware matching.

## 16. Progressive enhancement / SSR
- Server renders a native `<select multiple>` (or `<select>`) with `<option>` and `<optgroup>` children inside `<mj-listbox>`.
- Before upgrade the native control functions normally.
- On upgrade, the component hides the native element, reads its options, and builds the custom UI; the hidden native element stays in sync for form submission.
- Without scripting, the native element is displayed and functional.

## 17. Dependencies
- Section 6: Registry/base element, design tokens, focus utilities (`aria-activedescendant` helper), form-association helper, live-region service, collection utility.
- `<mj-option>` — shared option primitive.
- `<mj-optgroup>` — shared option group primitive.

## 18. Edge cases & error handling
- Zero options: empty state slot shown; `required` validation fires immediately if the form is submitted.
- All options disabled: listbox is keyboard-navigable but `required` validation will fail.
- `value` attribute references a non-existent option: value is stored but no option is marked selected; no error thrown.
- Very long labels: text truncates with ellipsis; full text in `title`/tooltip.
- Large option sets (>200): the collection utility applies virtual scrolling; `aria-setsize` and `aria-posinset` are set on each rendered option.
- Programmatic selection change while `readonly`: silently ignored; a console warning is logged.

## 19. Acceptance criteria
- [ ] Single mode: clicking option A then option B results in only option B selected; `mj-change` fires with correct `values`.
- [ ] Multi mode: Shift+click selects a range; Ctrl+click toggles individual items.
- [ ] `ArrowDown`/`ArrowUp` move focus; `Enter`/`Space` toggle selection.
- [ ] `aria-activedescendant` on the listbox matches the `id` of the focused option.
- [ ] `aria-multiselectable="true"` present when `multiple`; absent otherwise.
- [ ] Form submission includes all selected values; form reset restores original selection.
- [ ] `required` with no selection causes `checkValidity()` to return `false`.
- [ ] axe-core reports zero violations in single, multi, disabled, and empty states.
- [ ] RTL layout positions checkboxes and icons on the trailing side.
- [ ] Virtual scrolling activates when more than 200 options are slotted.

## 20. Open questions
- Should optgroup headers be focusable (skip-through on arrow navigation) or completely skipped?
- Should `Ctrl+A` deselect all if all are already selected (toggle-all), or always select all?
- Is a `filter` slot (inline search input above the list) in scope for this component or exclusively `<mj-transfer-list>`?
