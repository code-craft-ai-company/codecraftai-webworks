# Combobox Spec

- **Tag:** `<mj-combobox>`
- **Class / file:** `MjCombobox` / `mjcombobox.js`
- **Category:** Selection & dropdown-style controls
- **Primary or Variant:** Primary
- **Synonyms covered:** Autocomplete, Typeahead, Searchable select, Filterable select
- **Phase:** P0
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-combobox>` combines a text input with a filtered popup list, allowing users to type characters and see matching options narrowed in real time. It covers autocomplete, typeahead, searchable select, and filterable select patterns. It supports both synchronous (slotted options) and asynchronous (data-source adapter) option sets, with debounced filtering, highlighted substrings, loading/error states, and optional free-text entry.

## 2. When to use / when not to use
**Use** when an option set is large (>30 items) or unknown until the user types. **Use** for searchable dropdowns, tag suggestions, or city/country inputs. **Do not use** for small known lists — prefer `<mj-select>`. **Do not use** when multiple values should be selected as chips — prefer `<mj-tag-picker>`. **Do not use** when the list must always be visible — prefer `<mj-listbox>`.

## 3. Anatomy
- **Input** (`part="input"`) — text `<input>` element the user types into.
- **Clear button** (`part="clear"`) — removes the current value; shown when `clearable` and a value exists.
- **Toggle button** (`part="toggle"`) — optional chevron to open/close the popup explicitly.
- **Loading indicator** (`part="loading"`) — spinner shown while async options are fetching.
- **Popup** (`part="popup"`) — positioned overlay managed by the overlay engine.
- **Listbox** (`part="listbox"`) — `role="listbox"` within the popup.
- **Option** (`part="option"`) — each match row (`role="option"`); contains highlighted text spans.
- **Option match** (`part="option-match"`) — `<mark>` wrapper around the matched substring.
- **No-results** (`part="no-results"`) — shown when filter yields zero matches.
- **Error state** (`part="error-inline"`) — shown when async load fails.

## 4. Variants & modes
| Variant / mode | Attribute | Behavior |
|----------------|-----------|----------|
| Filterable select | `free-text` absent | User must select from list; typed text filters options; input reverts on blur if no match |
| Free-text | `free-text` (boolean) | User may submit any string; list is a suggestion overlay |
| Sync options | `<mj-option>` children | Options filtered client-side; no network call |
| Async | `src` attribute or `dataSource` property | Options fetched on query; loading/error states shown |
| Clearable | `clearable` (boolean) | Shows clear button when a value is present |
| With groups | `<mj-optgroup>` children | Grouped option sections |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `name` | string | `""` | Yes | Form field name |
| `value` | string | `""` | Yes | Committed selected/entered value |
| `placeholder` | string | `""` | Yes | Input placeholder text |
| `disabled` | boolean | `false` | Yes | Disables the control |
| `readonly` | boolean | `false` | Yes | Prevents input; submits current value |
| `required` | boolean | `false` | Yes | Field required for form validity |
| `invalid` | boolean | `false` | Yes | Forces error visual/ARIA state |
| `free-text` | boolean | `false` | Yes | Allows values not in the option list |
| `clearable` | boolean | `false` | Yes | Shows clear button when value is set |
| `debounce` | number | `300` | Yes | Milliseconds to debounce input before filtering |
| `min-chars` | number | `1` | Yes | Minimum characters before popup opens |
| `open` | boolean | `false` | Yes | Opens/closes the popup programmatically |
| `src` | string | `""` | Yes | URL for async option fetching; query appended as `?q=` |
| `autocomplete` | string | `"off"` | Yes | Native `autocomplete` attribute for the inner input |
| `size` | `"sm"` \| `"md"` \| `"lg"` | `"md"` | Yes | Visual size variant |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `inputValue` | `string` | Current text in the input (may differ from `value` before commit) |
| `dataSource` | `DataSourceAdapter \| null` | Programmatic async option provider (overrides `src`) |
| `options` | `MjOption[]` | Currently displayed option elements |
| `validity` | `ValidityState` | Delegated from `ElementInternals` |
| `validationMessage` | `string` | Localizable invalid message |
| `filterFn` | `(option: MjOption, query: string) => boolean` | Custom client-side filter function |

## 7. Slots
| Slot | Description |
|------|-------------|
| (default) | `<mj-option>` and `<mj-optgroup>` for sync mode |
| `no-results` | Custom empty/no-match message |
| `loading` | Custom loading indicator content |
| `error` | Custom error state content (async failure) |
| `prefix` | Icon or element before the input |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-change` | `{ value: string, option: MjOption \| null }` | Yes | No | Fired on committed selection or free-text entry (on blur/Enter) |
| `mj-input` | `{ inputValue: string }` | Yes | No | Fired on every keystroke |
| `mj-open` | `{}` | Yes | Yes | Fired before popup opens |
| `mj-close` | `{}` | Yes | No | Fired after popup closes |
| `mj-filter` | `{ query: string, results: MjOption[] }` | Yes | No | Fired after filtering completes (sync or async) |
| `mj-error` | `{ error: Error }` | Yes | No | Fired when async data source fails |
| `mj-clear` | `{}` | Yes | No | Fired when the clear button is activated |

## 9. CSS parts & custom properties
**Parts:** `input`, `clear`, `toggle`, `loading`, `popup`, `listbox`, `option`, `option-match`, `option-icon`, `option-label`, `option-description`, `no-results`, `error-inline`, `prefix`

**Custom properties:**
| Property | Default token | Description |
|----------|---------------|-------------|
| `--mj-combobox-popup-max-height` | `18rem` | Max height of option popup |
| `--mj-combobox-popup-min-width` | `trigger width` | Minimum popup width |
| `--mj-combobox-match-color` | `--mj-color-accent` | Color of highlighted match text |
| `--mj-combobox-input-height` | `--mj-size-control-md` | Input field height |
| `--mj-combobox-border-radius` | `--mj-radius-md` | Input and popup corner radius |

## 10. States
| State | Visual effect | ARIA effect |
|-------|--------------|-------------|
| Default | Normal input border | — |
| Focused | Input focus ring; popup opens if text ≥ min-chars | `aria-expanded="true"` |
| Typing | Options filtered; no-results or list shown | `aria-autocomplete="list"` |
| Loading | Spinner in trailing slot | `aria-busy="true"` on listbox |
| Option focused | Highlighted row | `aria-activedescendant` on input |
| Option selected | Checkmark; input fills with label | `aria-selected="true"` |
| Disabled | Muted input; no interactions | `aria-disabled="true"`; `disabled` on inner input |
| Invalid | Error border/icon | `aria-invalid="true"` on input |
| No results | No-results slot visible | Status live region: "No results" |
| Error (async) | Error slot visible | Alert live region: error description |

## 11. Behavior & interactions
- Typing at least `min-chars` characters opens the popup after `debounce` ms.
- In filterable-select mode (default), if the user blurs without selecting, the input reverts to the label of the current `value`, or clears if no value is set.
- In free-text mode, blurring commits whatever is in the input as the `value`.
- Selecting an option sets `value` to the option's value, fills the input with the option's label, closes the popup, and fires `mj-change`.
- The clear button sets `value` to `""`, clears the input, and fires `mj-change` then `mj-clear`.
- Async mode: after debounce, `dataSource.query(inputValue)` is called; a loading indicator is shown until the promise resolves; on rejection, the error state is shown.
- Matched substrings in option labels are wrapped in `<mark>` elements for visual highlighting.
- Popup positioning follows the overlay engine: below the input by default, flips above if insufficient space.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| Any printable key | Type into input; filter options; open popup if min-chars met |
| `ArrowDown` | Open popup; move focus to next option |
| `ArrowUp` | Move focus to previous option |
| `Home` | Move focus to first option (when popup open) |
| `End` | Move focus to last option (when popup open) |
| `Enter` | Select focused option; close popup; commit value |
| `Escape` | Close popup; revert input to current value (filterable mode) |
| `Tab` | Commit (free-text) or revert (filterable) and move focus |
| `Backspace` | Delete last character; re-filter |
| `Alt+ArrowDown` | Open popup without changing input |
| `Alt+ArrowUp` | Close popup without changing value |

## 13. Accessibility
- Input has `role="combobox"`, `aria-autocomplete="list"`, `aria-haspopup="listbox"`, `aria-expanded`, and `aria-controls` referencing the listbox `id`.
- `aria-activedescendant` on the input tracks the focused option element's `id`.
- Listbox has `role="listbox"` with `aria-labelledby` referencing the input's label.
- Each option has `role="option"` and `aria-selected`.
- `<mark>` elements in matched substrings use `aria-hidden="true"` (the full text is still readable by AT through the parent option's text content).
- No-results status announced via a polite live region.
- Async error announced via an assertive live region.
- Minimum touch target: 44 × 44 px on the input and clear/toggle buttons.

## 14. Form participation
- Form-associated via `ElementInternals`; contributes `name=value` to `FormData`.
- In filterable mode, only a valid option value (or empty string) is committed.
- In free-text mode, the typed string is the value.
- `required`: `validity.valueMissing` when `value === ""`.
- On form reset, `value` reverts to the initial `value` attribute and the input is filled with the corresponding label.

## 15. Internationalization & RTL
- Clear and toggle buttons flip position in RTL.
- Prefix slot moves to the trailing edge in RTL.
- Matched substring highlighting is Unicode-aware; `String.prototype.normalize` used before comparison.
- Async queries use the raw input string; locale collation is the data-source's responsibility.
- No built-in English strings; "No results" and error messages are localizable via the `no-results` and `error` slots.

## 16. Progressive enhancement / SSR
- Server renders a native `<input>` (or `<select>`) inside `<mj-combobox>`.
- Before upgrade the input accepts free text.
- On upgrade, the component replaces the native element with the enhanced combobox UI; slotted `<mj-option>` elements provide the sync option set.
- Without scripting: if a native `<select>` is inside, it functions as a standard dropdown; if a native `<input>` is inside, it accepts free text.

## 17. Dependencies
- Section 6: Registry/base element, design tokens, overlay/positioning engine, focus utilities (`aria-activedescendant` helper), form-association helper, live-region service, data-source adapter, collection utility.
- `<mj-option>` — shared option primitive.
- `<mj-optgroup>` — shared option group primitive.

## 18. Edge cases & error handling
- Zero results from async source: show no-results slot; do not close popup.
- Network failure in async mode: show error slot; retain last successful results if any.
- `min-chars` set to 0: popup opens on focus with the full unfiltered list.
- `debounce` set to 0: filter runs synchronously on each keystroke (use with small sync sets only).
- User pastes a long string: filtering runs once after the paste event, not per character.
- `value` set programmatically to a string not in the option list in filterable mode: input shows the value string; validation marks invalid.
- Popup height exceeds viewport: scrollable listbox; selected option scrolled into view on open.
- Dynamic option insertion during async load: merge results; avoid duplicate keys.

## 19. Acceptance criteria
- [ ] Typing triggers filtering after `debounce` ms; popup opens when `min-chars` are typed.
- [ ] Matching substrings are wrapped in `<mark>` elements within option labels.
- [ ] Selecting an option fires `mj-change` with correct `value` and `option`.
- [ ] In filterable mode, blurring without selecting reverts input to the last committed label.
- [ ] In free-text mode, blurring fires `mj-change` with the typed string as `value`.
- [ ] Async mode shows loading indicator while fetching; fires `mj-error` on rejection.
- [ ] `ArrowDown`/`ArrowUp` navigate options; `Enter` commits; `Escape` reverts.
- [ ] `aria-activedescendant` on input matches the `id` of the focused option.
- [ ] `required` with empty value fails `checkValidity()`.
- [ ] axe-core reports zero violations in default, open, loading, error, and no-results states.
- [ ] RTL layout positions clear/toggle correctly; popup aligns to trailing edge.

## 20. Open questions
- Should the component fire `mj-change` immediately on option click (before popup close animation) or after?
- Should async mode cache query results to avoid redundant network requests, or leave caching to the data-source adapter?
- Is there a maximum number of visible options in the popup before virtualization kicks in, and what is that threshold?
