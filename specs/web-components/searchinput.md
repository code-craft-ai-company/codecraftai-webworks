# Search Input Spec

- **Tag:** `<mj-search-input>`
- **Class / file:** `SearchInput` / `searchinput.js`
- **Category:** Text & data-entry controls
- **Primary or Variant:** Primary
- **Synonyms covered:** Search bar, Search field
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-search-input>` is a text field tuned for search interactions. It wraps a
native `<input type="search">` and adds a leading search icon, a clear button, an
optional suggestions popup (Combobox pattern), and submit-on-Enter semantics. The
component uses `role="search"` on its landmark wrapper so screen readers identify
it as a search region.

## 2. When to use / when not to use
**Use** for site-wide search, in-page filtering, or any keyword-based lookup where
the user types free text and results are fetched or filtered in response. **Do not
use** for selecting a value from a fixed list — prefer `<mj-combobox>`. **Do not
use** when the field is inside a larger form as a general text entry — prefer
`<mj-text-field>`.

## 3. Anatomy
- **Search landmark** (`part="search"`) — `<div role="search">` wrapping the entire component.
- **Field wrapper** (`part="field"`) — flex row containing the icon, input, and buttons.
- **Search icon** (`part="search-icon"`) — leading magnifier glyph; purely decorative.
- **Native input** (`part="input"`) — `<input type="search">` with `role="searchbox"` explicitly set.
- **Clear button** (`part="clear-button"`) — dismisses the current query; visible only when value is non-empty.
- **Submit button** (`part="submit-button"`) — optional explicit search trigger (shown when `show-submit-button`).
- **Suggestions popup** (`part="popup"`) — anchored listbox of suggestions; composed from the Section 6 overlay engine.
- **Suggestion option** (`part="option"`) — individual suggestion item in the popup.
- **Loading indicator** (`part="loading"`) — spinner shown while suggestions are fetching.
- **Help text** (`part="help"`) — optional hint below the field.

## 4. Variants & modes
| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Simple | — (no `suggestions`) | Input + clear; submits on Enter |
| With suggestions | `suggestions` property set | Opens a Combobox popup as the user types |
| With submit button | `show-submit-button` | Adds an explicit search button beside the input |
| Loading | `loading` | Spinner replaces or supplements the clear button |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `name` | string | `"q"` | yes | Field name for form submission |
| `value` | string | `""` | yes | Current search query |
| `placeholder` | string | `"Search"` | yes | Placeholder; localizable |
| `label` | string | `"Search"` | yes | Accessible label for the input; localizable |
| `help-text` | string | `""` | yes | Hint text below the field |
| `disabled` | boolean | `false` | yes | Disables the control |
| `readonly` | boolean | `false` | yes | Prevents text changes |
| `required` | boolean | `false` | yes | Required for form validation |
| `maxlength` | number | — | yes | Maximum query length |
| `autocomplete` | string | `"off"` | yes | Forwarded to native input (`"off"` prevents native suggestions interfering with the popup) |
| `show-submit-button` | boolean | `false` | yes | Renders an explicit submit button |
| `submit-label` | string | `"Search"` | yes | Accessible label for the submit button; localizable |
| `loading` | boolean | `false` | yes | Shows loading state in the suggestions area |
| `debounce` | number | `300` | yes | Milliseconds to debounce `mj-query-change` before fetching suggestions |
| `min-chars` | number | `1` | yes | Minimum characters before `mj-query-change` fires |
| `no-clear-button` | boolean | `false` | yes | Hides the clear button |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `suggestions` | `Array<{ value: string, label: string, description?: string }>` | Suggestion items to display in the popup; set programmatically |
| `validity` | `ValidityState` | Delegates to `ElementInternals.validity` |
| `validationMessage` | string | Delegates to `ElementInternals.validationMessage` |

## 7. Slots
| Slot | Description |
|------|-------------|
| `search-icon` | Replace the default search icon |
| `submit-icon` | Replace the default submit button icon |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-input` | `{ value: string }` | yes | no | Fires on every keystroke |
| `mj-query-change` | `{ value: string }` | yes | no | Debounced; fires after `debounce` ms when value meets `min-chars` |
| `mj-search` | `{ value: string }` | yes | yes | Fires on Enter or submit-button click; cancel to prevent default form submit |
| `mj-clear` | `{ previousValue: string }` | yes | no | Fires when the clear button is activated |
| `mj-suggestion-select` | `{ suggestion: { value: string, label: string } }` | yes | no | Fires when the user picks a suggestion from the popup |

## 9. CSS parts & custom properties
**Parts:** `search`, `field`, `input`, `search-icon`, `clear-button`, `submit-button`, `popup`, `option`, `loading`, `help`.

| Custom property | Default token | Description |
|-----------------|---------------|-------------|
| `--mj-search-bg` | `--mj-color-surface-input` | Input background |
| `--mj-search-border-radius` | `--mj-radius-full` | Full pill radius by default |
| `--mj-search-border-color` | `--mj-color-border-default` | Border at rest |
| `--mj-search-border-color-focus` | `--mj-color-border-focus` | Border when focused |
| `--mj-search-icon-color` | `--mj-color-icon-subtle` | Search icon fill |
| `--mj-search-popup-bg` | `--mj-color-surface-overlay` | Suggestion popup background |
| `--mj-search-popup-shadow` | `--mj-shadow-lg` | Suggestion popup elevation |
| `--mj-search-option-bg-hover` | `--mj-color-surface-hover` | Highlighted suggestion row |

## 10. States
| State | Visual effect | ARIA effect |
|-------|---------------|-------------|
| Default | Neutral border, dimmed search icon | `role="searchbox"` on input |
| Focus-visible | Focus ring | `aria-expanded="true"` if popup opens |
| Loading | Spinner visible; options replaced with loading message | `aria-busy="true"` on popup |
| Suggestions open | Popup visible below field | `aria-controls` on input points to listbox |
| Suggestion highlighted | Row background token | `aria-activedescendant` on input |
| Disabled | Reduced opacity | `aria-disabled="true"` |
| Cleared | Clear button hidden; search icon restored | — |

## 11. Behavior & interactions
- On input, after `debounce` ms and if value length ≥ `min-chars`, `mj-query-change` fires so the host can update the `suggestions` property.
- When `suggestions` is set and non-empty, the popup opens; when `suggestions` is empty and `loading` is false, the popup closes.
- Suggestion selection copies `suggestion.value` into the input, closes the popup, and fires `mj-suggestion-select` followed by `mj-search`.
- The clear button resets value to `""`, closes the popup, fires `mj-clear`, and returns focus to the input.
- Enter key while the popup is open and no suggestion is highlighted submits the typed query. Enter while a suggestion is highlighted selects it.
- If `show-submit-button` and a form ancestor exists, `mj-search` (if not cancelled) triggers `form.requestSubmit()`.
- The popup uses the Section 6 overlay/positioning engine for flip/shift collision handling.
- The popup closes on Escape and on outside click (light-dismiss).

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` / `Shift+Tab` | Move focus to/from the field; closes popup |
| `Enter` | Submit query (if popup closed or no suggestion highlighted); select highlighted suggestion |
| `Escape` | Clear the active suggestion highlight; second press clears value |
| `Arrow Down` | Open popup if suggestions available; move highlight to next suggestion |
| `Arrow Up` | Move highlight to previous suggestion; wrap to last |
| `Home` | Move caret to start of input (no popup interaction) |
| `End` | Move caret to end of input (no popup interaction) |

## 13. Accessibility
- The `<div role="search">` wrapper creates a search landmark; it carries an
  accessible name from the `label` attribute via `aria-label`.
- The native input uses `role="searchbox"` and is linked to the suggestions listbox
  via `aria-controls` and `aria-activedescendant`.
- `aria-expanded` on the input reflects the popup open/closed state.
- The popup element has `role="listbox"`; each suggestion has `role="option"` and
  a unique `id`.
- The loading spinner is `role="status"` with a localizable "Loading suggestions"
  text; the text is announced politely.
- The clear button is a `<button>` with `aria-label="Clear search"` (localizable).
- On suggestion selection, focus returns to the input.

## 14. Form participation
- `formAssociated = true`; uses `ElementInternals`.
- Contributes `name`/`value` pair on form submit.
- Supports `required` and `maxlength` constraint validation.
- Form reset reverts value to the `value` attribute (or `""`) and closes the popup.
- `checkValidity()` and `reportValidity()` delegate to `ElementInternals`.

## 15. Internationalization & RTL
- `placeholder`, `label`, `submit-label`, clear-button aria-label, loading text,
  and no-suggestions text are all overridable via the shared localization hook.
- In RTL, the search icon appears on the right (inline-end), the clear/submit
  buttons on the left (inline-start); popup alignment flips accordingly.

## 16. Progressive enhancement / SSR
- Server renders the component with a standard `<input type="search">` and a
  `<button type="submit">` so search works without scripting.
- The `<form role="search">` wrapper provides semantic correctness in no-JS context.
- On upgrade the component adopts the existing input value without layout shift.

## 17. Dependencies
- **Registry + base element helper** (§6).
- **Design-token stylesheet** (§6).
- **Overlay/positioning engine** (§6) — popup placement.
- **Form-association helper** (§6).
- **Live-region service** (§6) — loading and no-results announcements.
- **Localization hook** (§6).
- **`<mj-text-field>`** — shares field anatomy patterns (not composed directly; shares tokens and parts conventions).

## 18. Edge cases & error handling
- `suggestions` set to an empty array while `loading` is true: show loading spinner, not "no results".
- `suggestions` set after the user has already cleared the field: ignore; do not open popup.
- Very long suggestion labels: clamp with ellipsis via `text-overflow`; full label in `title` attribute.
- Rapid typing faster than `debounce`: only the last value triggers `mj-query-change`; previous pending timers are cancelled.
- Suggestions popup exceeds viewport height: overflow scrolls inside the popup container.
- `min-chars` set to 0: `mj-query-change` fires immediately on focus with empty string — useful for showing recent searches.

## 19. Acceptance criteria
- [ ] `role="search"` landmark present with correct accessible name.
- [ ] `role="searchbox"` on input; `role="listbox"` on popup.
- [ ] `mj-query-change` fires debounced with correct value after `min-chars` threshold.
- [ ] Popup opens when `suggestions` is non-empty; closes on Escape, outside click, and clear.
- [ ] Arrow navigation highlights suggestions; Enter selects highlighted or submits query.
- [ ] `mj-search` fires on Enter and submit-button click; `mj-suggestion-select` on option pick.
- [ ] Clear button resets value and returns focus to input.
- [ ] Loading spinner shown while `loading` is true; "loading" status announced.
- [ ] Form submit includes `name`/`value`; form reset restores value.
- [ ] RTL layout verified with swapped icon positions.
- [ ] axe audit passes with zero violations in all popup states.

## 20. Open questions
- Should the component expose a "recent searches" slot for pre-populated suggestions on focus with empty value?
- Should suggestion matching (highlighting matched substrings) be done inside the component or delegated entirely to the host?
- Should a `group` property be supported on suggestion items to render grouped sections in the popup?
