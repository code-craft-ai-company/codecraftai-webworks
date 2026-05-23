# Number Field Spec

- **Tag:** `<mj-number-field>`
- **Class / file:** `NumberField` / `numberfield.js`
- **Category:** Text & data-entry controls
- **Primary or Variant:** Primary
- **Synonyms covered:** Number input, Currency input, Percentage input, Stepper input, Spinner input
- **Phase:** P0
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-number-field>` is the single implementation covering numeric, currency, and
percentage inputs. It wraps `<input type="text" inputmode="decimal">` (not
`type="number"`) to allow locale-aware display formatting while submitting a
normalized numeric value. It adds explicit increment/decrement spinner buttons
with hold-to-repeat behavior, locale-aware grouping separators and currency
symbols, and clamping on blur.

## 2. When to use / when not to use
**Use** for any numeric value the user types or steps through: quantities, prices,
percentages, measurements. **Do not use** for identifiers that happen to be
numeric (phone numbers → `<mj-typed-field type="tel">`, zip codes →
`<mj-masked-input>`). **Do not use** for a range selection where both endpoints
are shown — prefer `<mj-slider>`.

## 3. Anatomy
- **Field wrapper** (`part="field"`) — flex row containing prefix, input, suffix, and spinner buttons.
- **Native input** (`part="input"`) — `<input type="text" inputmode="decimal" role="spinbutton">`.
- **Prefix slot** (`part="prefix"`) — currency symbol or unit label before the value.
- **Suffix slot** (`part="suffix"`) — unit label after the value (e.g., `%`, `kg`).
- **Decrement button** (`part="decrement-button"`) — steps the value down by `step`.
- **Increment button** (`part="increment-button"`) — steps the value up by `step`.
- **Label** (`part="label"`), **Help text** (`part="help"`), **Error message** (`part="error"`).

## 4. Variants & modes
| Variant | `format` value | Behavior |
|---------|---------------|----------|
| Plain number | `"number"` | No symbol; locale grouping only |
| Currency | `"currency"` | Locale currency symbol shown; `currency-code` required |
| Percentage | `"percent"` | Trailing `%` suffix; value 0–100 maps to 0–1 for `Intl` |
| Stepper | `spinner-position="side"` | Increment/decrement buttons beside input |
| Stacked stepper | `spinner-position="stacked"` | Increment above, decrement below the input |
| No spinner | `no-spinner` | Buttons hidden; keyboard arrows still work |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `name` | string | `""` | yes | Name for form submission |
| `value` | string | `""` | yes | Current raw numeric value (locale-independent) |
| `min` | number | — | yes | Minimum allowed value |
| `max` | number | — | yes | Maximum allowed value |
| `step` | number | `1` | yes | Step size for spinner and arrow keys |
| `format` | `"number"\|"currency"\|"percent"` | `"number"` | yes | Display format mode |
| `currency-code` | string | `"USD"` | yes | ISO 4217 currency code; used when `format="currency"` |
| `fraction-digits` | number | — | yes | Fixed decimal places; defaults by format (2 for currency) |
| `min-fraction-digits` | number | — | yes | Minimum decimal places |
| `max-fraction-digits` | number | — | yes | Maximum decimal places |
| `locale` | string | — | yes | Override locale for `Intl.NumberFormat`; defaults to `document.documentElement.lang` |
| `label` | string | `""` | yes | Visible label above the field |
| `help-text` | string | `""` | yes | Hint text below the field |
| `error-message` | string | `""` | yes | Override validation message |
| `required` | boolean | `false` | yes | Field is required |
| `disabled` | boolean | `false` | yes | Disables the field and buttons |
| `readonly` | boolean | `false` | yes | Prevents changes |
| `placeholder` | string | `""` | yes | Placeholder text |
| `spinner-position` | `"side"\|"stacked"` | `"side"` | yes | Spinner button layout |
| `no-spinner` | boolean | `false` | yes | Hides spinner buttons |
| `size` | `"sm"\|"md"\|"lg"` | `"md"` | yes | Height/font-size scale |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `valueAsNumber` | number | The current value as a JavaScript number; `NaN` if empty or unparseable |
| `formattedValue` | string | The locale-formatted display string (read-only) |
| `validity` | `ValidityState` | Delegates to `ElementInternals.validity` |
| `validationMessage` | string | Delegates to `ElementInternals.validationMessage` |

## 7. Slots
| Slot | Description |
|------|-------------|
| `prefix` | Currency symbol, unit, or icon before the input (overrides auto-symbol) |
| `suffix` | Unit label or icon after the input (overrides auto-suffix) |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-input` | `{ value: string, valueAsNumber: number }` | yes | no | Fires on every keystroke |
| `mj-change` | `{ value: string, valueAsNumber: number }` | yes | no | Fires on blur after clamping/parsing |
| `mj-increment` | `{ value: string, valueAsNumber: number }` | yes | no | Fires when spinner increments |
| `mj-decrement` | `{ value: string, valueAsNumber: number }` | yes | no | Fires when spinner decrements |
| `mj-invalid` | `{ validationMessage: string }` | yes | no | Fires when reportValidity finds the field invalid |

## 9. CSS parts & custom properties
**Parts:** `field`, `input`, `label`, `prefix`, `suffix`, `decrement-button`, `increment-button`, `help`, `error`.

| Custom property | Default token | Description |
|-----------------|---------------|-------------|
| `--mj-num-bg` | `--mj-color-surface-input` | Input background |
| `--mj-num-border-color` | `--mj-color-border-default` | Border at rest |
| `--mj-num-border-color-focus` | `--mj-color-border-focus` | Border when focused |
| `--mj-num-border-color-error` | `--mj-color-border-error` | Border when invalid |
| `--mj-num-border-radius` | `--mj-radius-md` | Corner radius |
| `--mj-num-spinner-bg` | `--mj-color-surface-subtle` | Spinner button background |
| `--mj-num-spinner-bg-hover` | `--mj-color-surface-hover` | Spinner button hover |
| `--mj-num-spinner-color` | `--mj-color-icon-default` | Spinner icon color |

## 10. States
| State | Visual effect | ARIA effect |
|-------|---------------|-------------|
| Default | Neutral border; formatted value shown | `role="spinbutton"` on input |
| Focus-visible | Focus ring; raw value editable | `aria-valuenow`, `aria-valuemin`, `aria-valuemax` on input |
| At minimum | Decrement button disabled | `aria-disabled="true"` on decrement button |
| At maximum | Increment button disabled | `aria-disabled="true"` on increment button |
| Invalid | Error border; message shown | `aria-invalid="true"` |
| Disabled | All controls reduced opacity | `aria-disabled="true"` on input and buttons |
| Readonly | No spinner; muted background | `aria-readonly="true"` on input |

## 11. Behavior & interactions
- The input displays the locale-formatted value at rest; on focus it switches to
  the raw parseable string so the user can edit directly.
- On blur: the raw value is parsed using `Intl.NumberFormat` parsing (locale-aware
  decimal separator); if parseable it is clamped to `[min, max]`, stored as the
  canonical value, and the formatted display string is computed; if unparseable
  the field is marked invalid with a "Invalid number" message.
- Spinner buttons step by `step`. Holding a spinner button activates
  hold-to-repeat: after 600 ms initial delay, repeat fires every 100 ms.
- Arrow Up/Down in the input steps by `step` (matches the spinbutton pattern).
- Page Up/Down steps by `step * 10`.
- For `format="currency"`, `Intl.NumberFormat` with `style: "currency"` and
  `currency: currencyCode` formats the display; the submitted value is the raw number.
- For `format="percent"`, the internal value is stored as 0–100; submitted as
  the 0–100 string; formatted display divides by 100 for `Intl.NumberFormat`.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` / `Shift+Tab` | Move focus to/from field; then to increment; then decrement |
| `Arrow Up` | Increment by `step`; clamp to `max` |
| `Arrow Down` | Decrement by `step`; clamp to `min` |
| `Page Up` | Increment by `step × 10`; clamp to `max` |
| `Page Down` | Decrement by `step × 10`; clamp to `min` |
| `Home` | Set value to `min` (if defined) |
| `End` | Set value to `max` (if defined) |
| `Enter` | Parse and commit current typed value; run validation |
| Any digit / decimal separator / sign | Native text entry (filtered to numeric chars for locale) |

## 13. Accessibility
- The native input carries `role="spinbutton"`, `aria-valuenow`, `aria-valuemin`,
  and `aria-valuemax` (omitted when `min`/`max` are not set).
- `aria-valuetext` provides the locale-formatted string so screen readers
  announce "one hundred dollars" rather than "100".
- Increment and decrement buttons are real `<button>` elements with
  `aria-label="Increase"` / `"Decrease"` (localizable); they include `aria-controls`
  pointing to the input's id.
- When a button is disabled (at min/max), it carries `aria-disabled="true"` and
  cannot receive focus.
- `aria-invalid` and `aria-describedby` for error and help text follow the
  same pattern as `<mj-text-field>`.

## 14. Form participation
- `formAssociated = true`; uses `ElementInternals`.
- Submits `name`/raw-number `value` pair (locale-independent; no grouping separators).
- For `format="percent"`, submitted value is the 0–100 number as a string.
- Supports `required` (valueMissing), `rangeUnderflow` (below `min`), `rangeOverflow`
  (above `max`), `stepMismatch`, `badInput` (unparseable) constraint validation —
  all with localizable custom messages.
- Form reset restores value to the `value` attribute (or `""`) and clears validation.
- `checkValidity()` and `reportValidity()` delegate to `ElementInternals`.

## 15. Internationalization & RTL
- `Intl.NumberFormat` used for display formatting; locale resolved from the
  `locale` attribute, then `document.documentElement.lang`, then `navigator.language`.
- Decimal and grouping separators are locale-derived; the input parser accepts
  both the locale separator and the ASCII period to accommodate copy-paste.
- Currency symbol position (before/after value) is locale-driven.
- In RTL, prefix and suffix slots swap visual positions; spinner buttons remain
  at the end per the spinbutton convention.

## 16. Progressive enhancement / SSR
- Server renders `<input type="number" min max step>` with a visible label so
  numeric entry works without script.
- On upgrade, the component reads `value` from the existing input, converts it
  to the formatted display, and replaces the native spinner with the custom buttons.

## 17. Dependencies
- **Registry + base element helper** (§6).
- **Design-token stylesheet** (§6).
- **Form-association helper** (§6).
- **Localization/formatting hook** (§6) — `Intl.NumberFormat` wrapper.
- **Localization hook** (§6) — button labels and validation messages.

## 18. Edge cases & error handling
- `min > max`: console error; `max` is ignored.
- `step` set to 0 or negative: console error; step defaults to 1.
- Value pasted with foreign locale separators: attempt best-effort parse; if
  ambiguous (`1.000` could be 1 or 1000), treat as invalid and show `badInput`.
- `fraction-digits` set on a `format="percent"` field: applied to the display
  percentage, not the raw 0–1 value.
- Hold-to-repeat interrupted by mouse-up or pointer-cancel: repeat stops immediately.
- Very large or very small numbers exceeding `Number.MAX_SAFE_INTEGER`:
  emit console warning; clamp to safe range.

## 19. Acceptance criteria
- [ ] Display shows locale-formatted value at rest; raw number on focus.
- [ ] `format="currency"` renders currency symbol in correct locale position.
- [ ] `format="percent"` appends `%` suffix and submits 0–100 value.
- [ ] Arrow Up/Down, Page Up/Down, Home/End apply correct increments.
- [ ] Spinner buttons step and clamp; hold-to-repeat fires after 600 ms.
- [ ] Increment/decrement buttons disabled and `aria-disabled` at min/max boundaries.
- [ ] `role="spinbutton"` with correct `aria-valuenow`, `aria-valuemin`, `aria-valuemax`, `aria-valuetext`.
- [ ] Unparseable input marks field invalid with `badInput`; parseable but out-of-range uses `rangeUnderflow`/`rangeOverflow`.
- [ ] Form submit sends raw numeric value without locale separators.
- [ ] Form reset restores original value and clears validation state.
- [ ] axe audit passes in all states and both spinner positions.

## 20. Open questions
- Should `valueAsNumber` be settable (e.g., `field.valueAsNumber = 42`) or
  read-only (only value string is settable)?
- Should `format="currency"` accept a slot for a custom currency symbol rather
  than always relying on `Intl`?
- Should the hold-to-repeat acceleration increase the step size over time
  (progressive stepping)?
