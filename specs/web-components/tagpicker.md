# Tag Picker Spec

- **Tag:** `<mj-tag-picker>`
- **Class / file:** `MjTagPicker` / `mjtagpicker.js`
- **Category:** Selection & dropdown-style controls
- **Primary or Variant:** Primary
- **Synonyms covered:** People picker, Token input (for selection), Multi-value combobox
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-tag-picker>` is a combobox that yields multiple values as removable chip tokens. The user types to search from a suggestion list and selects items that appear as chips inside the input field. It covers people/user pickers, multi-tag inputs, and any scenario where multiple discrete values need to be chosen from a searchable set. Values can optionally be free-text (not constrained to the suggestion list).

## 2. When to use / when not to use
**Use** when the user must select multiple named values from a large or dynamic set (users, tags, skills, permissions). **Use** the people-picker pattern by supplying an async data source with user avatars. **Do not use** for a small, fully known set of independent toggles — use `<mj-checkbox-group>`. **Do not use** when values are free-text only (no suggestions) — use `<mj-token-input>` (5.2). **Do not use** when only one value is needed — use `<mj-combobox>`.

## 3. Anatomy
- **Container** (`part="container"`) — click anywhere to focus the input.
- **Token list** (`part="token-list"`) — flex-wrapped list of selected chip tokens.
- **Token** (`part="token"`) — individual chip for a selected value.
- **Token avatar** (`part="token-avatar"`) — optional image/initials (people-picker mode).
- **Token label** (`part="token-label"`) — display text of the token.
- **Token remove** (`part="token-remove"`) — × button to remove this token.
- **Input** (`part="input"`) — text field for typing and searching.
- **Popup** (`part="popup"`) — positioned overlay with suggestions.
- **Listbox** (`part="listbox"`) — `role="listbox"` inside the popup.
- **Option** (`part="option"`) — suggestion row (`role="option"`).
- **Option avatar** (`part="option-avatar"`) — optional avatar in each suggestion.
- **Option label** (`part="option-label"`) — primary text; matched substring wrapped in `<mark>`.
- **Option meta** (`part="option-meta"`) — secondary info (e.g., email, department).
- **No-results** (`part="no-results"`) — shown when search yields nothing.
- **Loading** (`part="loading"`) — shown while async data source fetches.
- **Max-count hint** (`part="max-count"`) — shown when `max-count` is reached.

## 4. Variants & modes
| Variant / mode | Attribute | Behavior |
|----------------|-----------|----------|
| Suggestion-bound (default) | `free-text` absent | Only values from the suggestion list are accepted |
| Free-text | `free-text` (boolean) | Any typed string becomes a valid token (on Enter/comma) |
| People picker | `type="person"` | Options show avatars; tokens show avatars |
| Tag input | `type="tag"` (default) | Plain text tokens; no avatars |
| Async | `src` or `dataSource` | Suggestions fetched per query |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `name` | string | `""` | Yes | Form field name; each token submitted as `name=value` |
| `value` | string | `""` | Yes | Comma-separated list of selected token values |
| `type` | `"tag"` \| `"person"` | `"tag"` | Yes | Visual mode |
| `placeholder` | string | `""` | Yes | Input placeholder when no tokens are selected |
| `disabled` | boolean | `false` | Yes | Disables the control |
| `readonly` | boolean | `false` | Yes | Tokens cannot be removed; no new tokens added |
| `required` | boolean | `false` | Yes | At least one token required |
| `free-text` | boolean | `false` | Yes | Allows arbitrary text tokens |
| `max-count` | number | `0` | Yes | Maximum number of tokens; 0 = unlimited |
| `debounce` | number | `200` | Yes | Search debounce in ms |
| `min-chars` | number | `1` | Yes | Minimum characters before suggestions appear |
| `src` | string | `""` | Yes | URL for async suggestions; query appended as `?q=` |
| `duplicate-values` | boolean | `false` | Yes | Allow duplicate token values |
| `delimiter` | string | `","` | Yes | Character(s) that commit a free-text token |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `tokens` | `TokenItem[]` | Array of selected token objects: `{ value, label, avatar? }` |
| `inputValue` | `string` | Current text in the search input |
| `dataSource` | `DataSourceAdapter \| null` | Programmatic async suggestion provider |
| `validity` | `ValidityState` | Delegated from `ElementInternals` |
| `validationMessage` | `string` | Localizable invalid message |

## 7. Slots
| Slot | Description |
|------|-------------|
| (default) | `<mj-option>` elements for sync suggestion list |
| `no-results` | Custom empty suggestion state |
| `loading` | Custom loading indicator |
| `max-count` | Custom max-count reached hint |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-change` | `{ tokens: TokenItem[], values: string[] }` | Yes | No | Fired when tokens change |
| `mj-token-add` | `{ token: TokenItem }` | Yes | Yes | Fired before a token is added; cancel to prevent |
| `mj-token-remove` | `{ token: TokenItem }` | Yes | No | Fired when a token is removed |
| `mj-input` | `{ inputValue: string }` | Yes | No | Fired on each keystroke |
| `mj-open` | `{}` | Yes | Yes | Fired before suggestion popup opens |
| `mj-close` | `{}` | Yes | No | Fired after popup closes |
| `mj-max-count` | `{ count: number }` | Yes | No | Fired when max-count is reached and add is attempted |

## 9. CSS parts & custom properties
**Parts:** `container`, `token-list`, `token`, `token-avatar`, `token-label`, `token-remove`, `input`, `popup`, `listbox`, `option`, `option-avatar`, `option-label`, `option-meta`, `no-results`, `loading`, `max-count`

**Custom properties:**
| Property | Default token | Description |
|----------|---------------|-------------|
| `--mj-tag-picker-min-height` | `--mj-size-control-md` | Minimum container height |
| `--mj-tag-picker-popup-max-height` | `16rem` | Maximum suggestion popup height |
| `--mj-tag-picker-token-radius` | `--mj-radius-full` | Token chip corner radius |
| `--mj-tag-picker-token-bg` | `--mj-color-surface-subtle` | Token chip background |
| `--mj-tag-picker-token-gap` | `--mj-space-1` | Gap between token chips |
| `--mj-tag-picker-avatar-size` | `1.25rem` | Avatar size within tokens and options |
| `--mj-tag-picker-border-radius` | `--mj-radius-md` | Container corner radius |

## 10. States
| State | Visual effect | ARIA effect |
|-------|--------------|-------------|
| Default (empty) | Placeholder shown | — |
| Has tokens | Chips + input visible | — |
| Input focused | Container focus ring; popup opens on min-chars | `aria-expanded="true"` |
| Suggestion focused | Option highlighted | `aria-activedescendant` on input |
| Loading | Spinner in popup | `aria-busy="true"` on listbox |
| No results | No-results slot | Status live region |
| Max count reached | Input disabled; max-count hint | Live region: "Maximum N tags reached" |
| Token focused | Token has focus ring | Natural tab focus on token remove button |
| Disabled | Container muted; no interactions | `aria-disabled="true"` |
| Readonly | Tokens shown without remove buttons | `aria-readonly="true"` |
| Invalid | Error border on container | `aria-invalid="true"` |

## 11. Behavior & interactions
- Clicking anywhere on the container (not on a token remove button) moves focus to the input.
- Typing at least `min-chars` characters opens the suggestion popup (after `debounce` ms).
- Clicking a suggestion adds it as a token, clears the input, and fires `mj-token-add` then `mj-change`.
- In `free-text` mode, pressing Enter or the configured `delimiter` character commits the current input text as a token.
- Pressing Backspace in an empty input focuses the last token's remove button; pressing Backspace again (or Delete) removes that token.
- Each token's remove button removes the token and fires `mj-token-remove` then `mj-change`.
- If `max-count` is reached, the input is disabled and the popup does not open; `mj-max-count` fires when an add is attempted.
- Duplicate values are rejected unless `duplicate-values` is set; `mj-token-add` fires and can be canceled by the author.
- In `type="person"` mode, each option row shows an avatar (image or initials fallback) and the token chip includes the avatar.

## 12. Keyboard interaction
| Key | Context | Action |
|-----|---------|--------|
| Printable key | Input | Type; filter suggestions; open popup |
| `Enter` | Input with suggestion focused | Add focused suggestion as token |
| `Enter` | Input (free-text mode) | Add current input text as token |
| Configured `delimiter` | Input (free-text mode) | Add current input text as token |
| `Backspace` | Empty input | Focus last token's remove button |
| `Delete` / `Backspace` | Token remove button focused | Remove the token |
| `ArrowDown` | Input | Open popup; focus next suggestion |
| `ArrowUp` | Input | Focus previous suggestion |
| `Home` | Popup open | Focus first suggestion |
| `End` | Popup open | Focus last suggestion |
| `Escape` | Popup open | Close popup; clear input; keep tokens |
| `ArrowLeft` | Input at position 0 | Move focus to last token's remove button |
| `ArrowRight` | Token remove button | Move focus to next token or input |
| `Tab` | — | Move focus out of the component |

## 13. Accessibility
- Container has `role="group"` with `aria-label` or `aria-labelledby`.
- Input has `role="combobox"`, `aria-haspopup="listbox"`, `aria-expanded`, `aria-autocomplete="list"`, `aria-controls` referencing the listbox.
- `aria-activedescendant` on the input tracks the focused suggestion option.
- Each token is a `<span>` wrapping the label and a `<button>` for removal; the remove button has `aria-label="Remove [token label]"`.
- The token list is announced as a sequence of chip labels when the user navigates into it.
- Adding a token announces via a polite live region: "[label] added. N tags selected."
- Removing a token announces: "[label] removed. N tags selected."
- Max-count reached announces: "Maximum [N] tags reached."
- No-results status via polite live region.
- Minimum touch target for token remove buttons: 44 × 44 px (or a larger hit area via padding).

## 14. Form participation
- Form-associated via `ElementInternals`; each token appends `name=value` to `FormData`.
- `required`: `validity.valueMissing` when `tokens` is empty.
- On form reset, all tokens are cleared; the initial `value` attribute's comma-separated codes are restored.

## 15. Internationalization & RTL
- Token chips and suggestions mirror layout in RTL (chips flow from right; remove button on left).
- Input text direction follows `dir` attribute; user may type in any script.
- Live region strings are localizable via the `l10n` hook.
- Matched substring highlighting in suggestions is Unicode-normalized before comparison.
- `delimiter` should be reviewed for locales that use comma as a decimal separator.

## 16. Progressive enhancement / SSR
- Server renders a `<select multiple>` with pre-selected `<option>` elements inside `<mj-tag-picker>`.
- Before upgrade the native multi-select is functional.
- On upgrade, the native select is hidden; selected options become the initial token set; the component builds the combobox UI.
- Without scripting, the native multi-select is functional.

## 17. Dependencies
- Section 6: Registry/base element, design tokens, overlay/positioning engine, focus utilities (`aria-activedescendant` helper), form-association helper, live-region service, data-source adapter.
- `<mj-option>` — shared option primitive for sync suggestion list.

## 18. Edge cases & error handling
- `max-count=1`: behaves like a single-value combobox with a chip token instead of an input value.
- Suggestion list returns a value already in the token set with `duplicate-values=false`: option is shown but grayed out; selecting it is a no-op.
- `mj-token-add` canceled by event handler: token is not added; input text is retained.
- Async source fails: error slot shown in popup; existing tokens are unaffected.
- Very many tokens (>20): container scrolls vertically; oldest tokens are still reachable.
- `value` attribute contains codes not in the data source: tokens are created with the code as both label and value; no error thrown.
- Paste of a delimited string (free-text mode): split by delimiter; each part added as a token after validation.

## 19. Acceptance criteria
- [ ] Typing triggers suggestions after `min-chars` and `debounce`; selecting adds a chip token.
- [ ] Free-text mode: Enter/delimiter commits typed text as a token.
- [ ] Backspace in empty input focuses last token remove; second Backspace removes the token.
- [ ] `mj-token-add` fires before adding; canceling the event prevents the add.
- [ ] `max-count` blocks further additions; live region announces the limit.
- [ ] Token remove button has `aria-label="Remove [label]"`; removing announces via live region.
- [ ] `aria-activedescendant` on input tracks focused suggestion.
- [ ] `required` with no tokens fails `checkValidity()`.
- [ ] Form submission includes one `name=value` per token.
- [ ] axe-core reports zero violations in empty, with-tokens, open, and max-count states.
- [ ] RTL layout mirrors chips and suggestions.

## 20. Open questions
- Should tokens be drag-reorderable, and if so, does the order affect the `FormData` submission order?
- Should the component expose a `validate-token` callback property for async per-token validation (e.g., checking if a username exists before adding)?
- Is a "create new" option (e.g., "Add tag 'new-tag'") within the suggestion list in scope, or does free-text mode cover that pattern?
