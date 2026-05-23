# Typed Text Field Spec

- **Tag:** `<mj-typed-field>`
- **Class / file:** `TypedTextField` / `typedtextfield.js`
- **Category:** Text & data-entry controls
- **Primary or Variant:** Primary
- **Synonyms covered:** Email field, URL field, Telephone field
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-typed-field>` is a single-line text field for semantically typed values —
email addresses, URLs, and telephone numbers. It wraps the correct native
`<input type="email|url|tel">`, applies the matching `inputmode` and `autocomplete`
hints, and provides localized format-validation messages beyond what browsers
supply by default. One component covers all three types via the `type` attribute.

## 2. When to use / when not to use
**Use** when the expected value has a specific semantic type with native browser
validation and virtual-keyboard support (email, url, tel). **Do not use** for
arbitrary text — prefer `<mj-text-field>`. **Do not use** for numeric values —
prefer `<mj-number-field>`. **Do not use** for pattern-masked values (credit
cards, etc.) — prefer `<mj-masked-input>`.

## 3. Anatomy
- **Field wrapper** (`part="field"`) — flex row containing prefix, input, suffix.
- **Native input** (`part="input"`) — `<input type="email|url|tel">` with matching `inputmode` and `autocomplete`.
- **Prefix slot** (`part="prefix"`) — optional icon (e.g., mail icon for email).
- **Suffix slot** (`part="suffix"`) — optional action or unit.
- **Format hint** (`part="format-hint"`) — inline example shown on focus (e.g., "user@example.com").
- **Label** (`part="label"`), **Help text** (`part="help"`), **Error message** (`part="error"`).

## 4. Variants & modes
| Variant | `type` value | Native input type | `inputmode` | Default `autocomplete` |
|---------|-------------|-------------------|-------------|----------------------|
| Email | `"email"` | `email` | `email` | `email` |
| Multiple emails | `"email"` + `multiple` | `email` | `email` | `email` |
| URL | `"url"` | `url` | `url` | `url` |
| Telephone | `"tel"` | `tel` | `tel` | `tel` |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `type` | `"email"\|"url"\|"tel"` | `"email"` | yes | Semantic type; drives native input type, inputmode, autocomplete |
| `name` | string | `""` | yes | Name submitted with form data |
| `value` | string | `""` | yes | Current value |
| `placeholder` | string | `""` | yes | Placeholder text |
| `label` | string | `""` | yes | Visible label text |
| `help-text` | string | `""` | yes | Hint text below field |
| `error-message` | string | `""` | yes | Override validation message |
| `required` | boolean | `false` | yes | Field is required |
| `disabled` | boolean | `false` | yes | Disables the field |
| `readonly` | boolean | `false` | yes | Makes the field read-only |
| `multiple` | boolean | `false` | yes | For `type="email"`: allows comma-separated list of addresses |
| `maxlength` | number | — | yes | Maximum character count |
| `minlength` | number | — | yes | Minimum character count |
| `autocomplete` | string | (derived from `type`) | yes | Overrides the derived autocomplete value |
| `show-format-hint` | boolean | `false` | yes | Shows an example format hint on focus |
| `format-hint` | string | (derived from `type`) | yes | Override for the format hint example text |
| `size` | `"sm"\|"md"\|"lg"` | `"md"` | yes | Height/font-size scale |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `validity` | `ValidityState` | Delegates to `ElementInternals.validity` |
| `validationMessage` | string | Delegates to `ElementInternals.validationMessage` |
| `willValidate` | boolean | True when the field participates in constraint validation |

## 7. Slots
| Slot | Description |
|------|-------------|
| `prefix` | Icon or label before the input (e.g., mail/link/phone icon) |
| `suffix` | Icon, action, or label after the input |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-input` | `{ value: string }` | yes | no | Fires on every keystroke |
| `mj-change` | `{ value: string }` | yes | no | Fires on blur when value has changed |
| `mj-invalid` | `{ validationMessage: string, validityState: ValidityState }` | yes | no | Fires when reportValidity finds the field invalid |

## 9. CSS parts & custom properties
**Parts:** `field`, `input`, `label`, `prefix`, `suffix`, `format-hint`, `help`, `error`.

| Custom property | Default token | Description |
|-----------------|---------------|-------------|
| `--mj-typed-bg` | `--mj-color-surface-input` | Input background |
| `--mj-typed-border-color` | `--mj-color-border-default` | Border at rest |
| `--mj-typed-border-color-focus` | `--mj-color-border-focus` | Border when focused |
| `--mj-typed-border-color-error` | `--mj-color-border-error` | Border when invalid |
| `--mj-typed-border-radius` | `--mj-radius-md` | Corner radius |
| `--mj-typed-hint-color` | `--mj-color-text-subtle` | Format hint text color |

## 10. States
| State | Visual effect | ARIA effect |
|-------|---------------|-------------|
| Default | Neutral border | `type`-specific input role |
| Focus-visible | Focus ring; format hint appears if `show-format-hint` | `aria-describedby` includes hint id |
| Invalid (typeMismatch) | Error border; type-specific localized message | `aria-invalid="true"` |
| Invalid (valueMissing) | Error border; required message | `aria-invalid="true"` |
| Disabled | Reduced opacity | `aria-disabled="true"` |
| Readonly | Muted background | `aria-readonly="true"` |

## 11. Behavior & interactions
- The `type` attribute determines the native input type. Changing `type` at
  runtime re-renders the inner input with the correct type and clears the value
  to avoid type-format mismatches.
- Derived defaults per type:
  - `email`: `inputmode="email"`, `autocomplete="email"`, format hint `"user@example.com"`.
  - `url`: `inputmode="url"`, `autocomplete="url"`, format hint `"https://example.com"`.
  - `tel`: `inputmode="tel"`, `autocomplete="tel"`, format hint `"+1 (555) 000-0000"`.
- For `type="email"` with `multiple`, the value is a comma-separated list;
  validation checks each address individually and reports the first failure.
- Validation runs on blur. Custom validation messages are used for `typeMismatch`
  (localized email/url/tel format messages) and `valueMissing` (localized required
  message).
- The format hint is a `<span>` below the input that appears on focus and hides
  on blur. It is not the placeholder.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` / `Shift+Tab` | Move focus in/out of the field |
| `Enter` | Submit enclosing form if valid |
| Any printable key | Native text entry at caret |

## 13. Accessibility
- The native input type provides browser-native semantics appropriate for each
  type (email, url, tel).
- `aria-label` derived from `label` attribute or linked `<label>` element.
- `aria-describedby` references help-text, format-hint (when visible), and error IDs.
- `aria-invalid="true"` on the native input when validation fails.
- `aria-required="true"` mirrors the `required` attribute.
- The format hint is associated via `aria-describedby` so screen readers announce
  it on focus.

## 14. Form participation
- `formAssociated = true`; uses `ElementInternals`.
- Contributes `name`/`value` pair to `FormData`.
- For `type="email"` with `multiple`, submits a comma-separated value.
- Constraint validation: `typeMismatch`, `valueMissing`, `tooLong`, `tooShort` —
  all with localizable custom messages.
- Form reset restores value to the `value` attribute (or `""`) and clears
  validation state.
- `checkValidity()` and `reportValidity()` delegate to `ElementInternals`.

## 15. Internationalization & RTL
- Format-hint strings and all validation messages are localizable via the shared
  localization hook and keyed by type (e.g., `typed-field.email.format-hint`,
  `typed-field.email.type-mismatch`).
- Phone number format hint adapts to `navigator.language` locale by default
  (NANP format for en-US, E.164 for others); overridable via `format-hint`.
- In RTL, prefix and suffix swap visual positions; input `dir` inherits from
  the document.

## 16. Progressive enhancement / SSR
- Server renders `<input type="email|url|tel">` with a `<label>`; native validation
  works without script.
- On upgrade the component adopts the existing input value without layout shift.

## 17. Dependencies
- **Registry + base element helper** (§6).
- **Design-token stylesheet** (§6).
- **Form-association helper** (§6).
- **Localization hook** (§6) — format hints and validation messages.

## 18. Edge cases & error handling
- `type` changed at runtime with a value already present: the value is cleared
  and `mj-change` fires with `""` to alert the host.
- `multiple` set on `type="url"` or `type="tel"`: attribute is ignored; console
  warning issued (multiple is only valid for email inputs).
- Very long email (>254 chars): `maxlength` enforced; `tooLong` validity reported.
- URL without a scheme: `typeMismatch` reported with a hint to include `https://`.
- `autocomplete` overridden to `"off"` while `type="email"`: allowed; the
  override takes precedence.

## 19. Acceptance criteria
- [ ] `type="email"` renders `<input type="email">` with `inputmode="email"` and `autocomplete="email"`.
- [ ] `type="url"` renders `<input type="url">` with `inputmode="url"` and `autocomplete="url"`.
- [ ] `type="tel"` renders `<input type="tel">` with `inputmode="tel"` and `autocomplete="tel"`.
- [ ] `typeMismatch` fires `mj-invalid` with a localized type-specific message.
- [ ] `valueMissing`, `tooLong`, `tooShort` constraints work correctly.
- [ ] `multiple` on email accepts comma-separated list; validates each address.
- [ ] Format hint appears on focus when `show-format-hint`; hidden on blur.
- [ ] Form submit includes correct `name`/`value`; reset restores original value.
- [ ] `aria-invalid`, `aria-required`, `aria-describedby` correct in all states.
- [ ] Changing `type` at runtime clears the value and re-renders correctly.
- [ ] axe audit passes with zero violations.

## 20. Open questions
- Should `type="email"` with `multiple` validate addresses against a domain
  allowlist attribute for enterprise scenarios?
- Should URL validation reject non-https schemes by default (configurable)?
- Should a `tel` value be formatted into a display-friendly format on blur while
  keeping the raw value for submission?
