# Password Field Spec

- **Tag:** `<mj-password-field>`
- **Class / file:** `PasswordField` / `passwordfield.js`
- **Category:** Text & data-entry controls
- **Primary or Variant:** Primary
- **Synonyms covered:** Password input, Masked password entry
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-password-field>` wraps `<input type="password">` and adds a show/hide
visibility toggle, an optional caps-lock warning hint, and an optional
strength-meter bar — all in an accessible, form-associated custom element. It is
distinct from `<mj-text-field>` because of the specialized UX and security
requirements around masked entry.

## 2. When to use / when not to use
**Use** for password, passphrase, PIN, and secret-key entry. **Do not use** for
general text that merely wants a reveal toggle — in that case extend
`<mj-text-field>` with a suffix slot button. **Do not use** `<mj-password-field>`
where a `<mj-masked-input>` pattern would be more appropriate (credit-card
numbers, etc.).

## 3. Anatomy
- **Field wrapper** (`part="field"`) — flex row containing the input and controls.
- **Native input** (`part="input"`) — `<input type="password">` or `type="text"` when visible.
- **Toggle button** (`part="toggle-button"`) — show/hide password; persistent in the suffix area.
- **Caps-lock hint** (`part="caps-lock-hint"`) — warning strip shown when Caps Lock is detected.
- **Strength meter** (`part="strength-meter"`) — horizontal bar showing password strength.
- **Strength label** (`part="strength-label"`) — textual strength description ("Weak", "Fair", "Strong").
- **Label** (`part="label"`), **Help text** (`part="help"`), **Error message** (`part="error"`).

## 4. Variants & modes
| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Default | — | Masked input with toggle; no strength meter |
| With strength meter | `show-strength` | Strength bar and label appear below the field |
| With caps-lock hint | `show-caps-hint` | Caps-lock warning shown when active |
| Visible (toggled) | `visible` (reflects) | Input switches to `type="text"`; icon changes |
| New password | `new-password` | Sets `autocomplete="new-password"` |
| Current password | `current-password` | Sets `autocomplete="current-password"` (default) |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `name` | string | `""` | yes | Name submitted with form data |
| `value` | string | `""` | yes | Current field value |
| `placeholder` | string | `""` | yes | Placeholder for the input |
| `label` | string | `""` | yes | Visible label above the field |
| `help-text` | string | `""` | yes | Hint text below the field |
| `error-message` | string | `""` | yes | Override for the validation message |
| `required` | boolean | `false` | yes | Field is required |
| `disabled` | boolean | `false` | yes | Field is disabled |
| `readonly` | boolean | `false` | yes | Field is read-only |
| `minlength` | number | — | yes | Minimum character count |
| `maxlength` | number | — | yes | Maximum character count |
| `visible` | boolean | `false` | yes | Whether the password is currently revealed |
| `new-password` | boolean | `false` | yes | Sets `autocomplete="new-password"` |
| `current-password` | boolean | `false` | yes | Sets `autocomplete="current-password"` |
| `show-strength` | boolean | `false` | yes | Renders the strength meter |
| `show-caps-hint` | boolean | `false` | yes | Enables caps-lock detection and warning |
| `size` | `"sm"\|"md"\|"lg"` | `"md"` | yes | Height/font-size scale |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `strength` | `0\|1\|2\|3\|4` | Read-only computed strength score (0=empty, 1=very weak, 2=weak, 3=fair, 4=strong) |
| `strengthLabel` | string | Localizable label for the current strength score |
| `validity` | `ValidityState` | Delegates to `ElementInternals.validity` |
| `validationMessage` | string | Delegates to `ElementInternals.validationMessage` |

## 7. Slots
| Slot | Description |
|------|-------------|
| `prefix` | Icon or label before the input (e.g., a lock icon) |
| `strength-indicator` | Replace the default strength bar with a custom element |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-input` | `{ value: string }` | yes | no | Fires on every keystroke |
| `mj-change` | `{ value: string }` | yes | no | Fires on blur with value change |
| `mj-visibility-change` | `{ visible: boolean }` | yes | no | Fires when show/hide is toggled |
| `mj-strength-change` | `{ score: number, label: string }` | yes | no | Fires when strength score changes |
| `mj-invalid` | `{ validationMessage: string }` | yes | no | Fires when reportValidity finds the field invalid |

## 9. CSS parts & custom properties
**Parts:** `field`, `input`, `label`, `toggle-button`, `caps-lock-hint`, `strength-meter`, `strength-fill`, `strength-label`, `help`, `error`.

| Custom property | Default token | Description |
|-----------------|---------------|-------------|
| `--mj-pwd-bg` | `--mj-color-surface-input` | Input background |
| `--mj-pwd-border-color` | `--mj-color-border-default` | Border at rest |
| `--mj-pwd-border-color-focus` | `--mj-color-border-focus` | Border when focused |
| `--mj-pwd-border-color-error` | `--mj-color-border-error` | Border when invalid |
| `--mj-pwd-border-radius` | `--mj-radius-md` | Corner radius |
| `--mj-pwd-strength-height` | `4px` | Strength bar height |
| `--mj-pwd-strength-color-1` | `--mj-color-danger-500` | Very weak fill color |
| `--mj-pwd-strength-color-2` | `--mj-color-warning-500` | Weak fill color |
| `--mj-pwd-strength-color-3` | `--mj-color-caution-400` | Fair fill color |
| `--mj-pwd-strength-color-4` | `--mj-color-success-500` | Strong fill color |
| `--mj-pwd-caps-bg` | `--mj-color-warning-50` | Caps-lock hint background |

## 10. States
| State | Visual effect | ARIA effect |
|-------|---------------|-------------|
| Default (masked) | Bullet characters; show-eye icon on toggle | `input type="password"` |
| Visible | Plain text; hide-eye icon on toggle | `input type="text"`; `aria-label` updated |
| Caps lock active | Caps-lock hint strip shown | Live region announces "Caps Lock is on" |
| Strength updating | Strength bar fill animates to new width | `aria-valuenow` on meter updates |
| Invalid | Error border and message | `aria-invalid="true"` |
| Disabled | Reduced opacity; toggle hidden | `aria-disabled="true"` |
| Readonly | No toggle shown | `aria-readonly="true"` |

## 11. Behavior & interactions
- On each `input` event the component updates `ElementInternals` value, emits `mj-input`, and if `show-strength` is set recalculates strength score using a built-in heuristic (entropy + pattern checks). The strength heuristic does not transmit the password off-device.
- Activating the toggle button flips `visible`, changes the native input type, updates the icon aria-label, and emits `mj-visibility-change`. Focus stays on the input.
- Caps-lock detection uses the `keydown` event's `getModifierState("CapsLock")`; the hint appears on focus when CapsLock is active and disappears when deactivated.
- When `show-strength` is enabled the strength bar width and fill color transition on score change (respects `prefers-reduced-motion`).
- `autocomplete` attribute is derived from `new-password` / `current-password` flags; both set is a console warning; `current-password` wins.
- Validation runs on blur; `reportValidity()` runs immediately.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` | Focus enters field; second Tab moves to toggle button; third Tab exits |
| `Shift+Tab` | Reverse focus order |
| `Enter` (on toggle) | Toggle visibility |
| `Space` (on toggle) | Toggle visibility |
| Any printable key (in input) | Native password entry behavior |
| `Escape` (when visible) | Hide the password again; keep focus on input |

## 13. Accessibility
- The native `<input>` receives `aria-label` from the `label` attribute if no
  visible label element is linked, or a `<label>` is rendered and linked via id.
- `aria-describedby` references help-text and error IDs when present.
- `aria-invalid="true"` on invalid state.
- Toggle button is a real `<button>`; its `aria-label` alternates between
  "Show password" and "Hide password" (both localizable) and is also reflected
  in `aria-pressed`.
- The strength meter has `role="meter"`, `aria-valuemin="0"`, `aria-valuemax="4"`,
  `aria-valuenow="{score}"`, and `aria-valuetext="{strengthLabel}"`.
- Caps-lock hint uses `role="alert"` so it is announced immediately when it appears.
- Password value is never placed in an ARIA property or live region.

## 14. Form participation
- `formAssociated = true`; uses `ElementInternals`.
- Contributes `name`/`value` to `FormData` on submit.
- Supports `required`, `minlength`, `maxlength` constraint validation.
- Custom validity messages are localizable (e.g., "Password must be at least 8 characters").
- Form reset clears the value, hides the password (resets `visible` to false), and clears validation state.
- `checkValidity()` and `reportValidity()` delegate to `ElementInternals`.

## 15. Internationalization & RTL
- Localizable strings: toggle button labels, caps-lock message, strength labels
  (`"Very weak"`, `"Weak"`, `"Fair"`, `"Strong"`), validation messages.
- In RTL the toggle button appears on the inline-start side (left in RTL); the
  prefix slot moves to inline-end. Input `dir` inherits from document.

## 16. Progressive enhancement / SSR
- Server renders `<input type="password">` with a visible label; toggle requires
  script but the password entry itself works without it.
- On upgrade the component wraps the existing input in place without clearing its
  value.

## 17. Dependencies
- **Registry + base element helper** (§6).
- **Design-token stylesheet** (§6).
- **Form-association helper** (§6).
- **Live-region service** (§6) — caps-lock alert.
- **Localization hook** (§6).

## 18. Edge cases & error handling
- `visible` set while `disabled`: toggle button is hidden; visibility cannot be changed.
- `readonly` with password: the value is still masked; toggle is hidden to prevent read-only password exposure surprise.
- `minlength` exceeds `maxlength`: a console error is thrown and `minlength` is ignored.
- Strength meter with an empty value: score is 0, bar is empty; "Enter a password" label shown.
- Very long passwords (>1000 chars): strength calculation capped at 500 chars to avoid perf issues; a `console.warn` is emitted.
- `new-password` and `current-password` both set: `current-password` wins; console warning issued.

## 19. Acceptance criteria
- [ ] Input type toggles between `"password"` and `"text"` on toggle button activation.
- [ ] Toggle button aria-label alternates correctly and `aria-pressed` reflects state.
- [ ] `mj-visibility-change` fires on each toggle with correct `visible` payload.
- [ ] Caps-lock hint appears/disappears based on `getModifierState("CapsLock")` and `show-caps-hint` attribute.
- [ ] Strength score changes fire `mj-strength-change`; strength meter `aria-valuenow` and `aria-valuetext` update.
- [ ] Strength bar colors match the score tier and transition respects `prefers-reduced-motion`.
- [ ] `autocomplete` attribute on the native input is correct based on the flag attributes.
- [ ] Form submit includes name/value; form reset clears value and resets `visible` to false.
- [ ] `required` and `minlength` violations produce correct validation messages.
- [ ] axe audit passes in masked and visible modes.
- [ ] Password value does not appear in any ARIA property or live region.

## 20. Open questions
- Should the strength heuristic be pluggable (allow hosts to inject a custom scorer such as zxcvbn)?
- Should the caps-lock hint also appear on `mousemove` (as some browsers do) or only on `keydown`?
- Should `visible` be a persisted default or reset to `false` on every form reset?
