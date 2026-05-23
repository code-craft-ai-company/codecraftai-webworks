# Text Field Spec

- **Tag:** `<mj-text-field>`
- **Class / file:** `TextField` / `textfield.js`
- **Category:** Text & data-entry controls
- **Primary or Variant:** Primary
- **Synonyms covered:** Text input, Single-line text input
- **Phase:** P0
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-text-field>` is the foundational single-line text entry control. It wraps a
native `<input type="text">` inside Shadow DOM, adding design-system styling,
label/help/error association, prefix/suffix slots, and character counter — while
remaining a fully form-associated custom element that participates in `FormData`
and constraint validation exactly as a native input would.

## 2. When to use / when not to use
**Use** for free-form short text: names, titles, identifiers, search queries, any
value that fits on one line. **Do not use** when the input type is numeric
(`<mj-number-field>`), has a pattern mask (`<mj-masked-input>`), requires multiple
lines (`<mj-textarea>`), or is a password (`<mj-password-field>`). For type-specific
semantics (email, url, tel) use `<mj-typed-field>`.

## 3. Anatomy
- **Root host** — the custom element; receives focus styles via `:host`.
- **Field wrapper** (`part="field"`) — flex container that lays out prefix, input, suffix, and any trailing icon.
- **Prefix slot** (`slot="prefix"`) — optional icon or text placed before the input.
- **Native input** (`part="input"`) — the real `<input>` element; receives all native attributes.
- **Suffix slot** (`slot="suffix"`) — optional icon, unit label, or action placed after the input.
- **Clear button** (`part="clear-button"`) — appears when `clearable` and value is non-empty.
- **Label** (`part="label"`) — visible label rendered above or floating over the field.
- **Help text** (`part="help"`) — supplementary hint rendered below the field.
- **Error message** (`part="error"`) — validation message rendered below the field when invalid.
- **Character counter** (`part="counter"`) — live counter rendered at the trailing end below the field.

## 4. Variants & modes
| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Default (outlined) | `variant="outlined"` | Border surrounds the field wrapper |
| Filled | `variant="filled"` | Field has a filled background, underline only |
| Plain | `variant="plain"` | No border or background; for dense in-table use |
| With prefix | `slot="prefix"` populated | Prefix region shown; input left-padding adjusted |
| With suffix | `slot="suffix"` populated | Suffix region shown; input right-padding adjusted |
| Clearable | `clearable` | Clear button appears when value is non-empty |
| With counter | `maxlength` set | Character counter shown below field |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `name` | string | `""` | yes | Field name submitted with form data |
| `value` | string | `""` | yes | Current field value |
| `placeholder` | string | `""` | yes | Placeholder text; never replaces a visible label |
| `label` | string | `""` | yes | Visible label text rendered above the input |
| `help-text` | string | `""` | yes | Supplementary hint text below the field |
| `error-message` | string | `""` | yes | Overrides browser validation message when set |
| `variant` | `"outlined"\|"filled"\|"plain"` | `"outlined"` | yes | Visual style variant |
| `size` | `"sm"\|"md"\|"lg"` | `"md"` | yes | Height/font-size token scale |
| `maxlength` | number | — | yes | Maximum character count; enables counter |
| `minlength` | number | — | yes | Minimum character count for validation |
| `pattern` | string | — | yes | Regex pattern for constraint validation |
| `required` | boolean | `false` | yes | Marks the field required |
| `disabled` | boolean | `false` | yes | Disables the field |
| `readonly` | boolean | `false` | yes | Makes the field read-only |
| `clearable` | boolean | `false` | yes | Shows a clear button when value is non-empty |
| `autocomplete` | string | `"on"` | yes | Forwarded to the native input |
| `autofocus` | boolean | `false` | yes | Focuses the field on connect |
| `spellcheck` | boolean | `true` | yes | Forwarded to the native input |
| `inputmode` | string | `"text"` | yes | Virtual keyboard hint forwarded to native input |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `validity` | `ValidityState` | Read-only; delegates to `ElementInternals.validity` |
| `validationMessage` | string | Read-only; delegates to `ElementInternals.validationMessage` |
| `willValidate` | boolean | Read-only; `true` when the field participates in validation |
| `internals` | `ElementInternals` | The attached internals instance (read-only) |

## 7. Slots
| Slot | Description |
|------|-------------|
| `prefix` | Icon, currency symbol, or short label before the input text |
| `suffix` | Icon, unit label, or inline action after the input text |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-input` | `{ value: string }` | yes | no | Fires on every keystroke (mirrors native `input`) |
| `mj-change` | `{ value: string }` | yes | no | Fires on blur when value has changed (mirrors native `change`) |
| `mj-clear` | `{ previousValue: string }` | yes | no | Fires when the clear button is activated |
| `mj-invalid` | `{ validationMessage: string }` | yes | no | Fires when `reportValidity()` finds the field invalid |

## 9. CSS parts & custom properties
**Parts:** `field`, `input`, `label`, `prefix`, `suffix`, `clear-button`, `help`, `error`, `counter`.

| Custom property | Default token | Description |
|-----------------|---------------|-------------|
| `--mj-field-bg` | `--mj-color-surface-input` | Input background |
| `--mj-field-border-color` | `--mj-color-border-default` | Border color at rest |
| `--mj-field-border-color-focus` | `--mj-color-border-focus` | Border color when focused |
| `--mj-field-border-color-error` | `--mj-color-border-error` | Border color when invalid |
| `--mj-field-border-radius` | `--mj-radius-md` | Corner radius |
| `--mj-field-font-size` | `--mj-text-md` | Input font size |
| `--mj-field-height` | size-variant token | Control height |
| `--mj-field-padding-x` | `--mj-space-3` | Horizontal padding inside input |
| `--mj-field-color-placeholder` | `--mj-color-text-placeholder` | Placeholder text color |
| `--mj-field-color-error` | `--mj-color-text-error` | Error message text color |

## 10. States
| State | Visual effect | ARIA effect |
|-------|---------------|-------------|
| Default | Neutral border | — |
| Hover | Border brightens | — |
| Focus-visible | `--mj-field-border-color-focus` ring | `aria-describedby` links to help/error |
| Disabled | Reduced opacity; no pointer events | `aria-disabled="true"` on host; input `disabled` |
| Readonly | No border highlight; muted background | `aria-readonly="true"` on input |
| Invalid | `--mj-field-border-color-error`; error message shown | `aria-invalid="true"` on input |
| Filled (has value) | Clear button appears when `clearable` | — |

## 11. Behavior & interactions
- The native `<input type="text">` inside Shadow DOM receives all native attribute
  forwarding for autocomplete, spellcheck, inputmode, etc.
- On every `input` event the component updates its `ElementInternals` value and
  emits `mj-input`.
- On `change` (blur with value change) the component emits `mj-change` and
  runs constraint validation, toggling `aria-invalid` and the error message.
- When `clearable` and value is non-empty, the clear button is shown. Activating
  it resets value to `""`, emits `mj-clear`, then `mj-change`, and returns focus
  to the input.
- `maxlength` enables the character counter which updates politely via a live
  region. Counter text is localizable (`"{current}/{max}"`).
- Validation runs on blur by default; calling `reportValidity()` runs it
  immediately and focuses the field if invalid.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` | Moves focus into/out of the field (native behavior) |
| `Shift+Tab` | Reverses focus |
| `Escape` | If clear button is focused, clears and returns focus to input |
| `Enter` | Submits associated form when `type` of enclosing form allows |
| Any printable key | Appends character at caret (native behavior) |

## 13. Accessibility
- The native `<input>` carries `aria-label` derived from the `label` attribute
  when no visible `<label>` element is associated, or a visible `<label>` is
  rendered and programmatically linked via `htmlFor`/`id`.
- `aria-describedby` references the help-text and error-message ids when those
  regions are non-empty.
- `aria-invalid="true"` is set on the input when the field fails validation.
- `aria-required="true"` mirrors the `required` attribute on the input.
- The clear button is a real `<button>` with `aria-label="Clear"` (localizable).
- The character counter uses `role="status"` to announce changes politely.
- Focus is never lost on clear — it is explicitly returned to the input.

## 14. Form participation
- Implements `formAssociated = true` and uses `ElementInternals`.
- Contributes `name`/`value` pair to `FormData` on submit.
- Supports `required`, `minlength`, `maxlength`, `pattern` constraint validation
  via `setValidity()` with localizable custom messages.
- `checkValidity()` and `reportValidity()` are delegated to `ElementInternals`.
- On form reset, value reverts to the `value` attribute (or `""` if absent) and
  validation state is cleared.
- Participates in `form.elements`, `form.checkValidity()`, and label association.

## 15. Internationalization & RTL
- `label`, `help-text`, `error-message`, `placeholder`, and the clear-button
  label are all overridable strings sourced from the shared localization hook.
- The character counter format string (`"{current}/{max}"`) is localizable.
- In RTL (`dir="rtl"`), prefix and suffix slots swap visual positions; the clear
  button moves to the start end; the input direction inherits from the document.

## 16. Progressive enhancement / SSR
- Server renders `<mj-text-field>` with a `<input type="text">` inside a
  `<noscript>`-safe wrapper so the field is usable before script loads.
- On upgrade the component adopts the existing input's value without a value
  reset or layout shift.
- The `label` attribute is rendered as a visible `<label>` element in the
  server-side template; the component preserves this association on upgrade.

## 17. Dependencies
- **Registry + base element helper** (§6) — lifecycle, attribute/property reflection.
- **Design-token stylesheet** (§6) — all visual values via tokens.
- **Form-association helper** (§6) — `ElementInternals` wrapper, constraint validation.
- **Live-region service** (§6) — character counter announcements.
- **Localization hook** (§6) — all user-facing strings.

## 18. Edge cases & error handling
- `maxlength` set to 0: counter shows `"0/0"`; typing is blocked by native input.
- `value` longer than `maxlength` set via property: input is clamped; a warning
  is emitted to the console.
- `label` and `aria-label` both set: `aria-label` wins; a console warning is
  issued to alert the developer.
- Slot content changes after connect: prefix/suffix layout is re-measured via
  `MutationObserver` and padding is recalculated.
- `readonly` and `clearable` both set: the clear button is hidden.
- `disabled` and `required` both set: the field does not participate in
  constraint validation (matches native `<input>` behavior).

## 19. Acceptance criteria
- [ ] Renders visible label, help text, error message, and counter correctly.
- [ ] Prefix and suffix slots render and update input padding dynamically.
- [ ] Clear button appears only when `clearable` and value is non-empty; activates via click and Enter/Space.
- [ ] `mj-input` fires on every keystroke; `mj-change` fires only on blur with value change.
- [ ] `aria-invalid` and error message toggle correctly on blur validation.
- [ ] `aria-describedby` references active help and error IDs.
- [ ] Form submit includes the correct `name`/`value` pair.
- [ ] Form reset restores the original `value` attribute value.
- [ ] `checkValidity()` and `reportValidity()` return correct results for all constraint rules.
- [ ] Character counter updates on input and is announced politely.
- [ ] RTL layout swaps prefix/suffix positions.
- [ ] All states render correctly in light, dark, high-contrast, and forced-colors modes.
- [ ] axe audit passes with zero violations.
- [ ] Keyboard-only use covers all interactions.

## 20. Open questions
- Should `label` support rich content (slotted HTML) or remain a plain string attribute?
- Should the outlined variant support a floating/material-style label animation?
- What is the exact debounce strategy for `mj-input` events on low-powered devices?
