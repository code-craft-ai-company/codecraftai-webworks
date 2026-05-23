# OTP Input Spec

- **Tag:** `<mj-otp-input>`
- **Class / file:** `OtpInput` / `otpinput.js`
- **Category:** Text & data-entry controls
- **Primary or Variant:** Primary
- **Synonyms covered:** Verification code input, PIN input, MFA code input, One-time password input
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-otp-input>` is a fixed-length segmented entry control for verification codes,
PINs, and one-time passwords. Despite appearing as N separate boxes, the component
is a single form-associated element that submits one concatenated value. It
provides automatic caret advancement on each character, Backspace navigation, and
one-paste-fills-all behavior with numeric or alphanumeric input modes.

## 2. When to use / when not to use
**Use** for 4–8 character verification codes (SMS OTP, email OTP, TOTP, app PINs).
**Do not use** for general numeric entry — prefer `<mj-number-field>`. **Do not
use** for structured masked values (credit cards, phone numbers) — prefer
`<mj-masked-input>`. **Do not use** for codes longer than 8 characters — a single
`<mj-text-field>` with an appropriate `maxlength` is clearer.

## 3. Anatomy
- **Segment group** (`part="group"`) — `role="group"` container wrapping all segments.
- **Segment** (`part="segment"`) — individual `<input>` element for one code character.
- **Separator** (`part="separator"`) — optional decorative divider between groups of segments (e.g., between position 3 and 4 of a 6-digit code).
- **Label** (`part="label"`) — visible label above the group.
- **Help text** (`part="help"`).
- **Error message** (`part="error"`).

## 4. Variants & modes
| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Numeric | `inputtype="numeric"` (default) | Accepts digits only; `inputmode="numeric"` on segments |
| Alphanumeric | `inputtype="alphanumeric"` | Accepts `[A-Z0-9]` (case-insensitive); `inputmode="text"` |
| Password | `inputtype="password"` | Digits accepted; each segment is type `"password"` |
| Grouped | `group-at` set | Separator rendered between specified positions |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `name` | string | `""` | yes | Name submitted with the concatenated value |
| `length` | number | `6` | yes | Number of segments (code length) |
| `inputtype` | `"numeric"\|"alphanumeric"\|"password"` | `"numeric"` | yes | Character type accepted and inputmode applied |
| `label` | string | `""` | yes | Visible label above the group |
| `help-text` | string | `""` | yes | Hint text |
| `error-message` | string | `""` | yes | Override validation message |
| `required` | boolean | `false` | yes | All segments must be filled |
| `disabled` | boolean | `false` | yes | Disables all segments |
| `readonly` | boolean | `false` | yes | Read-only display |
| `autocomplete` | string | `"one-time-code"` | yes | Forwarded to each segment (default enables SMS autofill on mobile) |
| `group-at` | number | — | yes | Position (1-based) after which a separator is rendered |
| `size` | `"sm"\|"md"\|"lg"` | `"md"` | yes | Segment box size scale |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `value` | string | Get/set the concatenated code value (e.g., `"123456"`); setting fills segments |
| `complete` | boolean | Read-only; `true` when all segments are filled |
| `validity` | `ValidityState` | Delegates to `ElementInternals.validity` |
| `validationMessage` | string | Delegates to `ElementInternals.validationMessage` |

## 7. Slots
| Slot | Description |
|------|-------------|
| `separator` | Custom separator element rendered at the `group-at` position |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-input` | `{ value: string, complete: boolean }` | yes | no | Fires on every character entry or deletion |
| `mj-change` | `{ value: string }` | yes | no | Fires when all segments are filled or the group loses focus |
| `mj-complete` | `{ value: string }` | yes | no | Fires exactly once when the last segment is filled |
| `mj-invalid` | `{ validationMessage: string }` | yes | no | Fires when reportValidity finds the field invalid |

## 9. CSS parts & custom properties
**Parts:** `group`, `segment`, `separator`, `label`, `help`, `error`.

| Custom property | Default token | Description |
|-----------------|---------------|-------------|
| `--mj-otp-segment-size` | size-scale token | Width and height of each segment box |
| `--mj-otp-segment-bg` | `--mj-color-surface-input` | Segment background |
| `--mj-otp-segment-border-color` | `--mj-color-border-default` | Segment border |
| `--mj-otp-segment-border-color-focus` | `--mj-color-border-focus` | Segment border when focused |
| `--mj-otp-segment-border-color-filled` | `--mj-color-border-emphasis` | Segment border when filled |
| `--mj-otp-segment-border-color-error` | `--mj-color-border-error` | Segment border when invalid |
| `--mj-otp-segment-border-radius` | `--mj-radius-md` | Segment corner radius |
| `--mj-otp-segment-font-size` | `--mj-text-xl` | Character font size |
| `--mj-otp-gap` | `--mj-space-2` | Gap between segment boxes |
| `--mj-otp-separator-color` | `--mj-color-text-subtle` | Separator character color |

## 10. States
| State | Visual effect | ARIA effect |
|-------|---------------|-------------|
| Empty | All segments show empty placeholder | — |
| Partially filled | Filled segments styled with `--mj-otp-segment-border-color-filled` | — |
| Complete | All segments filled; `mj-complete` fires; focus stays on last segment | `aria-valuenow` on group |
| Invalid | All segments red border; error message shown | `aria-invalid="true"` on each segment |
| Disabled | All segments greyed; no focus | `aria-disabled="true"` on all segments |
| Readonly | Segments display value; not focusable | — |

## 11. Behavior & interactions
- The component renders exactly `length` `<input>` elements inside the Shadow DOM.
- Each segment accepts exactly one character. When a character is entered, the
  value is stored and focus advances to the next unfilled segment automatically.
- Backspace on a filled segment clears it and keeps focus. Backspace on an empty
  segment moves focus to the previous segment and clears it.
- Arrow Right/Left moves focus between segments without clearing.
- Paste event on any segment: the pasted string is stripped of invalid characters
  and distributed one character per segment starting from the focused segment
  (or from segment 0 if the full code length matches). After a full paste,
  focus moves to the last filled segment and `mj-complete` fires if all are filled.
- `autocomplete="one-time-code"` on each segment enables the browser SMS OTP
  autofill on supported mobile browsers; the browser fills all segments at once.
- `inputtype="password"` uses `type="password"` on each segment; characters are
  masked individually.
- The `value` property getter concatenates all segment values; the setter splits
  the string and distributes characters to segments.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `0-9` (numeric mode) | Enter digit; advance to next segment |
| `A-Z`, `0-9` (alphanumeric mode) | Enter character (upcased); advance to next segment |
| `Backspace` (filled segment) | Clear this segment; stay focused |
| `Backspace` (empty segment) | Move focus to previous segment; clear it |
| `Delete` | Clear this segment; do not move focus |
| `Arrow Right` | Move focus to next segment |
| `Arrow Left` | Move focus to previous segment |
| `Tab` | Move focus to the first unfilled segment in order; if all filled, exit the group |
| `Shift+Tab` | Move focus backwards out of the group |

## 13. Accessibility
- The segment group has `role="group"` with `aria-label` from the `label` attribute
  or a linked `<label>`.
- Each segment `<input>` has `aria-label` of the form `"Digit {n} of {length}"`
  or `"Character {n} of {length}"` depending on `inputtype` (localizable with
  position and length interpolated).
- `aria-invalid="true"` is set on all segments when the group fails validation.
- `aria-required="true"` is set on the first segment when `required`.
- `aria-describedby` on the first segment references the help and error IDs.
- A single polite live-region announces completion: "Code entered" (localizable).
- The separator is `aria-hidden="true"`.

## 14. Form participation
- `formAssociated = true`; uses `ElementInternals`.
- Submits the concatenated value as one `name`/`value` pair in `FormData`.
- `required` validation: `valueMissing` when any segment is empty (i.e.,
  `complete` is `false`).
- A custom `patternMismatch` validity is set when any segment contains an invalid
  character type (e.g., a letter in numeric mode) — rare but possible via
  programmatic set.
- Form reset clears all segments (sets `value` to `""`) and clears validation.
- `checkValidity()` and `reportValidity()` delegate to `ElementInternals`.

## 15. Internationalization & RTL
- Segment `aria-label` format strings are localizable (position/length
  interpolation).
- Completion announcement is localizable.
- In RTL, segment visual order is right-to-left; focus advancement order remains
  left-to-right logically (first entered character is always in position 0).
  The component should be tested to confirm natural RTL entry feels correct for
  the OTP use case.

## 16. Progressive enhancement / SSR
- Server renders a single `<input type="text" maxlength="{length}" inputmode="numeric">`
  so the code can be entered in a single field without script.
- On upgrade, if the existing input has a value, the component splits it into
  segments.

## 17. Dependencies
- **Registry + base element helper** (§6).
- **Design-token stylesheet** (§6).
- **Form-association helper** (§6).
- **Live-region service** (§6) — completion announcement.
- **Localization hook** (§6).

## 18. Edge cases & error handling
- `length` changed at runtime: segments are re-rendered; existing value is
  truncated or padded with empty positions as needed.
- Paste of a string shorter than `length`: fills from the focused segment;
  remaining segments stay empty.
- Paste of a string longer than `length`: fills all segments from position 0;
  excess characters discarded.
- `value` set programmatically with more characters than `length`: excess are
  silently truncated.
- `autocomplete="one-time-code"` browser autofill arriving as a single string in
  the first segment's `input` event: detected by checking if `event.data.length > 1`
  during the input handler; distributed across all segments automatically.

## 19. Acceptance criteria
- [ ] `length=6` renders exactly 6 segment inputs; `length=4` renders 4.
- [ ] Typing a valid digit auto-advances focus to the next segment.
- [ ] Backspace on empty segment moves focus to previous segment and clears it.
- [ ] Paste of "123456" fills all 6 segments; `mj-complete` fires.
- [ ] `mj-complete` fires exactly once per fill; not on subsequent keystrokes.
- [ ] `value` getter returns concatenated string; setter distributes characters.
- [ ] `autocomplete="one-time-code"` present on each segment input.
- [ ] `aria-label` on each segment includes correct ordinal position.
- [ ] `required` + empty segments: `reportValidity()` sets `aria-invalid` and shows error message.
- [ ] Form submit sends single concatenated value; form reset clears all segments.
- [ ] `inputtype="password"` masks each character individually.
- [ ] axe audit passes in all states.

## 20. Open questions
- Should `mj-complete` fire again if the user edits a segment after the code was complete?
- Should the component support a `mask-char` attribute for displaying a custom placeholder in each segment box?
- Should there be a built-in resend-code button/link slot for the common OTP UX pattern?
