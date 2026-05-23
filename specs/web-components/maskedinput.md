# Masked Input Spec

- **Tag:** `<mj-masked-input>`
- **Class / file:** `MaskedInput` / `maskedinput.js`
- **Category:** Text & data-entry controls
- **Primary or Variant:** Primary
- **Synonyms covered:** Pattern-constrained text input, Format input
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-masked-input>` constrains user input to a configurable character-position
pattern (e.g., phone numbers, credit cards, dates, IP addresses, Social Security
Numbers) while guiding the caret automatically and exposing both the raw
(unmasked) and formatted values. It wraps a native `<input type="text">` and
performs mask enforcement on each keystroke without losing undo history or
breaking assistive technology.

## 2. When to use / when not to use
**Use** when the value must conform to a fixed structural pattern with literal
separator characters (dashes, parens, dots, slashes). **Do not use** for free-form
text — prefer `<mj-text-field>`. **Do not use** for numeric values without
structural formatting — prefer `<mj-number-field>`. **Do not use** for passwords
— prefer `<mj-password-field>`. **Do not use** for OTP codes — prefer
`<mj-otp-input>`.

## 3. Anatomy
- **Field wrapper** (`part="field"`) — flex row containing prefix, input, and suffix.
- **Native input** (`part="input"`) — `<input type="text">` displaying the formatted value.
- **Mask overlay** (`part="mask-overlay"`) — optional ghost text showing the remaining mask positions (e.g., `___-___`); rendered behind the real input.
- **Prefix slot** (`part="prefix"`) — optional icon or label.
- **Suffix slot** (`part="suffix"`) — optional icon or unit.
- **Label** (`part="label"`), **Help text** (`part="help"`), **Error message** (`part="error"`).

## 4. Variants & modes
| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Eager (fills mask positions) | `mode="eager"` (default) | Literal separators auto-inserted as user types |
| Lazy (separators on blur) | `mode="lazy"` | User types raw digits; separators applied on blur |
| With ghost overlay | `show-mask` | Unfilled mask positions shown as `_` behind the input |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `name` | string | `""` | yes | Name for form submission |
| `value` | string | `""` | yes | Formatted (masked) value |
| `mask` | string | `""` | yes | Mask pattern string; `9` = digit, `a` = letter, `*` = alphanumeric, other chars = literals |
| `placeholder-char` | string | `"_"` | yes | Character used to represent unfilled positions in the ghost overlay |
| `mode` | `"eager"\|"lazy"` | `"eager"` | yes | When literal separators are inserted |
| `show-mask` | boolean | `false` | yes | Show the ghost mask overlay |
| `label` | string | `""` | yes | Visible label |
| `help-text` | string | `""` | yes | Hint text |
| `error-message` | string | `""` | yes | Override validation message |
| `required` | boolean | `false` | yes | Field is required |
| `disabled` | boolean | `false` | yes | Disables the field |
| `readonly` | boolean | `false` | yes | Read-only |
| `inputmode` | string | `"text"` | yes | Virtual keyboard hint; `"numeric"` for digit-only masks |
| `autocomplete` | string | `"off"` | yes | Forwarded to native input |
| `size` | `"sm"\|"md"\|"lg"` | `"md"` | yes | Height/font-size scale |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `rawValue` | string | The unmasked value (only editable characters, no literals) |
| `complete` | boolean | Read-only; `true` when all required mask positions are filled |
| `validity` | `ValidityState` | Delegates to `ElementInternals.validity` |
| `validationMessage` | string | Delegates to `ElementInternals.validationMessage` |

## 7. Slots
| Slot | Description |
|------|-------------|
| `prefix` | Icon or label before the input |
| `suffix` | Icon or label after the input |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-input` | `{ value: string, rawValue: string, complete: boolean }` | yes | no | Fires on every accepted keystroke |
| `mj-change` | `{ value: string, rawValue: string, complete: boolean }` | yes | no | Fires on blur when value has changed |
| `mj-complete` | `{ value: string, rawValue: string }` | yes | no | Fires when all mask positions are filled |
| `mj-invalid` | `{ validationMessage: string }` | yes | no | Fires when reportValidity finds the field invalid |

## 9. CSS parts & custom properties
**Parts:** `field`, `input`, `mask-overlay`, `label`, `prefix`, `suffix`, `help`, `error`.

| Custom property | Default token | Description |
|-----------------|---------------|-------------|
| `--mj-mask-bg` | `--mj-color-surface-input` | Input background |
| `--mj-mask-border-color` | `--mj-color-border-default` | Border at rest |
| `--mj-mask-border-color-focus` | `--mj-color-border-focus` | Focus border |
| `--mj-mask-border-color-error` | `--mj-color-border-error` | Error border |
| `--mj-mask-border-radius` | `--mj-radius-md` | Corner radius |
| `--mj-mask-overlay-color` | `--mj-color-text-placeholder` | Ghost mask character color |
| `--mj-mask-font` | `--mj-font-mono` | Monospace font for aligned mask characters |

## 10. States
| State | Visual effect | ARIA effect |
|-------|---------------|-------------|
| Empty | Ghost mask shown if `show-mask`; placeholder-chars visible | — |
| Partially filled | Ghost shows remaining positions | `aria-valuetext` if relevant |
| Complete | All positions filled; `mj-complete` fires | — |
| Invalid (incomplete on blur) | Error border; incomplete message | `aria-invalid="true"` |
| Disabled | Reduced opacity | `aria-disabled="true"` |
| Readonly | Muted background | `aria-readonly="true"` |

## 11. Behavior & interactions
- The mask pattern is parsed once on `connectedCallback` or when `mask` changes.
  Each position is categorized as: editable digit (`9`), editable letter (`a`),
  editable alphanumeric (`*`), or literal (everything else).
- On each `keydown`, the component determines whether the pressed character
  matches the mask type at the current caret position. Matching characters are
  accepted; non-matching characters are rejected silently (no beep). Literals are
  auto-inserted and the caret advances past them automatically in eager mode.
- `rawValue` is derived by extracting only the editable positions from the
  formatted value.
- Backspace removes the character before the caret; if the previous character is a
  literal, the caret moves back past it and removes the preceding editable character.
- Delete removes the character at the caret position (if editable).
- The mask overlay is absolutely positioned behind the transparent text in the
  input. The input background is transparent to allow the overlay to show through.
- `complete` is `true` when all editable positions are filled with a valid
  character.
- Pasting: the pasted text is stripped of non-matching characters and inserted
  position by position into the mask.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `0-9`, `a-z`, `A-Z` | Accept if valid for current mask position; reject silently otherwise |
| `Backspace` | Remove previous editable character; skip back past literals |
| `Delete` | Remove editable character at caret |
| `Arrow Left / Right` | Move caret; skip over literal characters |
| `Home` | Move caret to first editable position |
| `End` | Move caret to last filled position or end of mask |
| `Tab` / `Shift+Tab` | Move focus in/out (native) |
| `Ctrl/Cmd+A` | Select all |

## 13. Accessibility
- The native input carries `aria-label` from the `label` attribute or a linked
  `<label>`, `aria-describedby` pointing to help and error, `aria-invalid`, and
  `aria-required`.
- The mask overlay is `aria-hidden="true"`.
- The `help-text` should describe the expected format (e.g., "Format: (###) ###-####")
  so screen readers convey the expected pattern without relying solely on visual cues.
- `inputmode` is set to `"numeric"` for digit-only masks automatically, improving
  the mobile virtual keyboard.
- Character rejection does not produce an audible error; the help text format
  guidance is the primary accessibility channel for format requirements.

## 14. Form participation
- `formAssociated = true`; uses `ElementInternals`.
- The value submitted to `FormData` is controlled by the `submit-raw` attribute
  (not listed above for simplicity, but planned): when `true`, submits `rawValue`;
  when `false` (default), submits the formatted `value`.
- Supports `required` (valueMissing), and a custom `patternMismatch` if the mask
  is not complete on validation — with a localizable message.
- Form reset restores the `value` attribute (or `""`) and re-applies the mask.
- `checkValidity()` and `reportValidity()` delegate to `ElementInternals`.

## 15. Internationalization & RTL
- `label`, `help-text`, `error-message` are localizable via the shared
  localization hook.
- The mask pattern itself is locale-independent (structural); the `help-text`
  should include a locale-appropriate example.
- In RTL the prefix/suffix swap; the mask fills left-to-right internally
  regardless of document direction (masked inputs are inherently LTR-structured).

## 16. Progressive enhancement / SSR
- Server renders a plain `<input type="text">` with `maxlength` derived from the
  mask length and a `pattern` attribute for basic browser validation.
- On upgrade, the component applies the mask logic to the existing input value
  without clearing it.

## 17. Dependencies
- **Registry + base element helper** (§6).
- **Design-token stylesheet** (§6).
- **Form-association helper** (§6).
- **Localization hook** (§6).

## 18. Edge cases & error handling
- Empty `mask` attribute: the component behaves as a plain text field with no
  masking; a console warning is emitted.
- `value` set programmatically that doesn't match the mask: the value is formatted
  to fit the mask (excess characters are truncated; mismatched characters are
  replaced with the placeholder-char); `mj-change` fires.
- Paste that exactly fills the mask: `mj-complete` fires immediately after the
  paste event.
- Mask containing only literals (no editable positions): an error is thrown at
  parse time; the component renders a read-only display of the literal string.
- `mode="lazy"` and `show-mask`: ghost mask shows placeholder chars even in lazy
  mode; separators are only applied to the real value on blur.

## 19. Acceptance criteria
- [ ] Mask `(999) 999-9999` only accepts digits in editable positions; auto-inserts `(`, `)`, and `-` in eager mode.
- [ ] Backspace removes editable characters and skips back past literals.
- [ ] `rawValue` contains only the editable characters, no literals.
- [ ] `complete` is `true` only when all editable positions are filled.
- [ ] `mj-complete` fires exactly once when the last position is filled.
- [ ] Paste of matching content fills the mask correctly.
- [ ] `show-mask` renders ghost overlay correctly aligned with the input text.
- [ ] `aria-invalid` set on incomplete field after blur when `required`.
- [ ] Form submit sends formatted value (or raw when `submit-raw`).
- [ ] Form reset restores initial value and re-applies mask.
- [ ] axe audit passes with zero violations.

## 20. Open questions
- Should `submit-raw` be a formal attribute in this spec or a future extension?
- Should the mask syntax support an optional-position marker (e.g., `?`) for masks where not all positions are required?
- Should a `masks` property allow an array of masks tried in order (for inputs that can have variable formats, like international phone numbers)?
