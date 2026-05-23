# Token Input Spec

- **Tag:** `<mj-token-input>`
- **Class / file:** `TokenInput` / `tokeninput.js`
- **Category:** Text & data-entry controls
- **Primary or Variant:** Primary
- **Synonyms covered:** Tag input, Chip input, Multi-value text input
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-token-input>` collects a list of discrete values (tokens/chips) entered by
the user as free text or selected from an optional suggestion popup. Each token is
displayed as a removable chip inline with the input. The component is form-
associated, submitting one entry per token under the same `name`. It covers the
Tag input, Chip input, and People picker (when paired with async suggestions)
catalog entries.

## 2. When to use / when not to use
**Use** when the user needs to enter multiple discrete values: email recipients,
tags, labels, skills, keywords. **Use** with the `suggestions` property for
constrained lists (people picker). **Do not use** when the value is a single
item — prefer `<mj-text-field>` or `<mj-combobox>`. **Do not use** when the
order of items must be drag-rearrangeable — that requires a sortable token list
which is a future extension.

## 3. Anatomy
- **Container** (`part="container"`) — wraps all chips and the input; click anywhere to focus the input.
- **Token chip** (`part="token"`) — individual chip for each committed value.
- **Token label** (`part="token-label"`) — the text content of a chip.
- **Token remove button** (`part="token-remove"`) — `×` button inside each chip; removes that token.
- **Input** (`part="input"`) — `<input type="text">` for entering the next token.
- **Suggestions popup** (`part="popup"`) — optional anchored listbox (same pattern as `<mj-search-input>`).
- **Label** (`part="label"`), **Help text** (`part="help"`), **Error message** (`part="error"`).

## 4. Variants & modes
| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Free-form | — | Any typed text can be committed as a token |
| Constrained | `suggestions` property set | Only values from the suggestion popup are accepted |
| Max count | `max-tokens` | No more than N tokens allowed |
| With validation | `validate-token` property | Each token is individually validated before commit |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `name` | string | `""` | yes | Name used for each token entry in FormData |
| `placeholder` | string | `""` | yes | Placeholder in the input when no tokens and no input |
| `label` | string | `""` | yes | Visible label above the component |
| `help-text` | string | `""` | yes | Hint text below the component |
| `error-message` | string | `""` | yes | Override validation message |
| `delimiters` | string | `",\n"` | yes | Characters that commit the current input as a token (comma and Enter by default) |
| `max-tokens` | number | — | yes | Maximum number of tokens allowed |
| `allow-duplicates` | boolean | `false` | yes | Whether duplicate token values are accepted |
| `required` | boolean | `false` | yes | At least one token must be present |
| `disabled` | boolean | `false` | yes | Disables all interaction |
| `readonly` | boolean | `false` | yes | Displays tokens without removal or input |
| `trim` | boolean | `true` | yes | Trim whitespace from token values before committing |
| `loading` | boolean | `false` | yes | Shows loading state in the suggestions popup |
| `debounce` | number | `300` | yes | Milliseconds to debounce `mj-query-change` |
| `min-chars` | number | `1` | yes | Minimum characters before `mj-query-change` fires |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `tokens` | `string[]` | Get/set the array of current token values |
| `suggestions` | `Array<{ value: string, label: string }>` | Suggestion items for the popup |
| `validateToken` | `(value: string) => boolean \| string` | Optional per-token validator; return `true` to accept, a string to reject with that message |
| `validity` | `ValidityState` | Delegates to `ElementInternals.validity` |
| `validationMessage` | string | Delegates to `ElementInternals.validationMessage` |

## 7. Slots
| Slot | Description |
|------|-------------|
| `token-icon` | Optional icon shown inside each chip (same for all tokens) |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-token-add` | `{ value: string, tokens: string[] }` | yes | yes | Fires before a token is added; cancel to reject |
| `mj-token-remove` | `{ value: string, tokens: string[] }` | yes | yes | Fires before a token is removed; cancel to keep |
| `mj-change` | `{ tokens: string[] }` | yes | no | Fires after the token list changes (add or remove) |
| `mj-query-change` | `{ value: string }` | yes | no | Debounced; fires when input text meets `min-chars` |
| `mj-suggestion-select` | `{ suggestion: { value: string, label: string } }` | yes | no | Fires when a suggestion is chosen from the popup |
| `mj-invalid` | `{ validationMessage: string }` | yes | no | Fires when reportValidity finds the component invalid |

## 9. CSS parts & custom properties
**Parts:** `container`, `token`, `token-label`, `token-remove`, `input`, `popup`, `label`, `help`, `error`.

| Custom property | Default token | Description |
|-----------------|---------------|-------------|
| `--mj-token-container-bg` | `--mj-color-surface-input` | Container background |
| `--mj-token-container-border` | `--mj-color-border-default` | Container border |
| `--mj-token-container-border-focus` | `--mj-color-border-focus` | Border when the input is focused |
| `--mj-token-container-border-radius` | `--mj-radius-md` | Outer corner radius |
| `--mj-token-chip-bg` | `--mj-color-chip-bg` | Individual chip background |
| `--mj-token-chip-color` | `--mj-color-chip-text` | Chip text color |
| `--mj-token-chip-border-radius` | `--mj-radius-full` | Chip corner radius |
| `--mj-token-remove-color` | `--mj-color-icon-subtle` | Remove button icon color |
| `--mj-token-popup-bg` | `--mj-color-surface-overlay` | Suggestion popup background |

## 10. States
| State | Visual effect | ARIA effect |
|-------|---------------|-------------|
| Empty | Placeholder shown | `aria-placeholder` on input |
| Tokens present | Chips shown inline before the input | — |
| Input focused | Container focus ring | `aria-expanded` on input if popup open |
| Max tokens reached | Input hidden; max-count message shown | `aria-disabled` on input region |
| Token rejected | Flash rejection animation on rejected chip; error shown below | `aria-live` announces rejection reason |
| Invalid (required) | Error border; message | `aria-invalid="true"` on host region |
| Disabled | All chips and input greyed; no interaction | `aria-disabled="true"` |
| Readonly | Chips displayed without remove buttons; no input | — |

## 11. Behavior & interactions
- The container intercepts clicks outside the input to focus the input.
- When the user types a character listed in `delimiters`, the current input text is trimmed (if `trim`) and processed as a token commit. If `validateToken` is set, the value is passed to it; rejection shows the returned message below the container and fires `mj-invalid` locally (not the global validation system).
- Duplicate check: if `allow-duplicates` is `false` and the value already exists in `tokens`, the commit is silently rejected; the duplicate chip receives a flash highlight.
- Backspace with an empty input focuses and selects the last chip (marks it for pending removal). A second Backspace removes it. Pressing any other key deselects the chip.
- When `max-tokens` is reached the input is hidden and an accessible message is shown ("Maximum {max-tokens} tags reached").
- Paste of a delimited string (e.g., `"alpha, beta, gamma"`) splits on the `delimiters` and creates multiple tokens at once.
- The suggestions popup follows the same pattern as `<mj-search-input>`: listbox, `aria-activedescendant`, Arrow navigation, Enter selects.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Enter` / (delimiter char) | Commit current input text as a token |
| `Backspace` (empty input) | Select last token for pending removal |
| `Backspace` (token selected) | Remove selected token; focus input |
| `Delete` (token selected) | Remove selected token; focus input |
| `Arrow Left` (empty input) | Move focus to last token chip |
| `Arrow Right` (chip focused) | Move focus to next chip; if last chip, focus input |
| `Arrow Left` (chip focused) | Move focus to previous chip |
| `Escape` | Close suggestions popup; deselect focused chip |
| `Arrow Down` | Open popup (if suggestions available); move to first suggestion |
| `Arrow Up` | Move to last suggestion in popup |
| `Tab` | Commit non-empty input as a token (if any text present); then move focus out |

## 13. Accessibility
- The container has `role="group"` with `aria-label` from the `label` attribute.
- The input has `aria-label="Add tag"` (localizable) and `aria-describedby`
  pointing to help, error, and (when popup open) the listbox via `aria-controls`.
- `aria-expanded` on the input reflects popup state.
- Each chip has `role="option"` within a wrapping `role="listbox"` to convey the
  list structure; selected (pending removal) chip has `aria-selected="true"`.
- Remove buttons are `<button>` elements with `aria-label="Remove {tokenValue}"`
  (localizable with value interpolated).
- When a token is added or removed, a polite live-region announcement confirms
  the action (e.g., "alpha added", "beta removed").
- When max-tokens is reached, an assertive live-region announces the limit.

## 14. Form participation
- `formAssociated = true`; uses `ElementInternals`.
- Each token in `tokens` is appended to `FormData` under the same `name` key,
  producing a multi-value form submission (standard `name[]` behavior).
- `required` validation: `valueMissing` when `tokens.length === 0`.
- Form reset clears all tokens back to the initial token set from the `value`
  attribute (comma-separated initial values) and clears validation state.
- `checkValidity()` and `reportValidity()` delegate to `ElementInternals`.

## 15. Internationalization & RTL
- Localizable strings: placeholder, "Add tag" label, "Remove {value}" label,
  max-tokens message, duplicate rejection message, add/remove live-region
  announcements.
- In RTL, chips flow right-to-left; the input is at the left end; Arrow Left/Right
  semantics for chip navigation remain logical (Left = move toward start).
- `delimiters` may need locale adjustment (e.g., semicolons in some locales).

## 16. Progressive enhancement / SSR
- Server renders a `<textarea>` with a comma-separated initial value; the user
  can edit the CSV directly without script.
- On upgrade, the component splits the textarea value on commas to populate
  initial tokens.

## 17. Dependencies
- **Registry + base element helper** (§6).
- **Design-token stylesheet** (§6).
- **Overlay/positioning engine** (§6) — suggestions popup.
- **Form-association helper** (§6).
- **Live-region service** (§6) — add/remove announcements.
- **Localization hook** (§6).
- **`<mj-chip>`** (5.6) — chip rendering is delegated to the Chip component.

## 18. Edge cases & error handling
- `max-tokens=0`: all token creation is blocked; input is always hidden.
- Very long token values: chips truncate at `--mj-token-chip-max-width` with
  ellipsis; full value in `title` and `aria-label`.
- Paste of 100+ tokens: processed synchronously up to `max-tokens`; remaining
  values discarded; a polite announcement states how many were added.
- `validateToken` throws an exception: caught; token is rejected with a generic
  "Invalid value" message; error is logged.
- `tokens` set programmatically with duplicates when `allow-duplicates=false`:
  duplicates are silently removed; `mj-change` fires with the deduplicated list.

## 19. Acceptance criteria
- [ ] Typing a delimiter commits the input text as a chip; input clears.
- [ ] Duplicate rejection (when `allow-duplicates=false`) flashes the existing chip and does not create a new one.
- [ ] Backspace on empty input selects last chip; second Backspace removes it.
- [ ] Arrow Left/Right navigate chips from the input; focus is visible.
- [ ] Remove button removes the chip; live-region announces removal.
- [ ] Paste of `"alpha, beta, gamma"` creates three tokens.
- [ ] `max-tokens` reached: input hidden; assertive announcement fires.
- [ ] `mj-token-add` is cancelable; `mj-token-remove` is cancelable.
- [ ] Form submit includes one FormData entry per token under `name`.
- [ ] Form reset restores initial tokens from the `value` attribute.
- [ ] `required` validation fires when `tokens` is empty.
- [ ] axe audit passes in all states (empty, with chips, popup open).

## 20. Open questions
- Should chips be drag-sortable (requires a sortable DnD primitive)?
- Should the component support a `token-renderer` slot for rich chip content (avatars, icons per-token)?
- Should there be a `min-tokens` attribute parallel to `max-tokens`?
