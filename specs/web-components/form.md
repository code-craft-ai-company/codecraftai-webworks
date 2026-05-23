# Form Spec

- **Tag:** `<mj-form>`
- **Class / file:** `MjForm` / `mjform.js`
- **Category:** Text & data-entry controls — form-structure primitives
- **Primary or Variant:** Primary
- **Synonyms covered:** Form
- **Phase:** P0
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-form>` wraps a native `<form>` element to coordinate submission across all
form-associated child controls (`<mj-*>` and native inputs), aggregate validity
state, trigger field-level and summary-level validation reporting, and emit
structured events carrying all control values as a typed payload. It is the
authoritative submission orchestrator so page code does not need to manually
iterate over controls.

## 2. When to use / when not to use
**Use** whenever a page collects user input that must be submitted or validated as
a unit — login, registration, settings, checkout, search-filter forms.
**Do not use** for a single isolated control whose value is handled inline; use the
control directly. Do not nest `<mj-form>` inside another `<mj-form>`.

## 3. Anatomy
- **Light-DOM `<form>` wrapper** — the component renders a single `<form>` in its
  shadow root; slotted content (all `<mj-*>` controls and submit buttons) falls
  inside that form's subtree so native form participation works.
- **Default slot** — all controls, fieldsets, and submit/reset buttons.
- **Validation summary slot** — optional `<mj-validation-summary>` placed before or
  after the control group; the form drives the summary's error list on submission.

## 4. Variants & modes
| Mode | Attribute | Description |
|------|-----------|-------------|
| Standard | _(default)_ | Validates on submit; shows errors after first submit attempt |
| Eager | `validate="eager"` | Validates each control on blur after first submit attempt |
| Aggressive | `validate="aggressive"` | Validates each control on every change after first submit attempt |
| Submit-only | `novalidate` | Disables built-in constraint validation; host handles errors |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `action` | string | `""` | Yes | Maps to the inner `<form action>` |
| `method` | `"get"` \| `"post"` \| `"dialog"` | `"post"` | Yes | Maps to inner `<form method>` |
| `enctype` | string | `"application/x-www-form-urlencoded"` | Yes | Maps to inner `<form enctype>` |
| `novalidate` | boolean | `false` | Yes | Suppresses built-in validation; maps to `novalidate` on inner form |
| `validate` | `"submit"` \| `"eager"` \| `"aggressive"` | `"submit"` | Yes | Controls when field-level validation runs |
| `disabled` | boolean | `false` | Yes | Sets all child form-associated controls to disabled |
| `loading` | boolean | `false` | Yes | Entered after submit; disables submission until resolved |
| `autocomplete` | `"on"` \| `"off"` | `"on"` | Yes | Maps to inner `<form autocomplete>` |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `elements` | `HTMLFormControlsCollection` | Delegates to inner `<form>.elements`; includes `<mj-*>` internals |
| `valid` | `boolean` | `true` when all form-associated controls report no validity errors |
| `value` | `Record<string, FormDataEntryValue \| FormDataEntryValue[]>` | Current snapshot of all named control values as a plain object |

## 7. Slots
| Slot | Description |
|------|-------------|
| _(default)_ | All form controls, fieldsets, labels, and action buttons |
| `summary` | Intended for `<mj-validation-summary>`; rendered before the default slot in the shadow DOM |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-submit` | `{ formData: FormData, value: Record<string, FormDataEntryValue[]>, valid: boolean }` | Yes | Yes | Fires before native submit; canceling prevents native submission |
| `mj-reset` | `{}` | Yes | Yes | Fires before native reset; canceling prevents reset |
| `mj-invalid` | `{ controls: MjFormControl[], summary: { name: string, message: string }[] }` | Yes | No | Fires when submission is blocked by invalid controls |
| `mj-change` | `{ name: string, value: FormDataEntryValue, formValue: Record<string, FormDataEntryValue[]> }` | Yes | No | Bubbles up from any child control change |

## 9. CSS parts & custom properties
| Part / Property | Description |
|-----------------|-------------|
| `::part(form)` | The inner `<form>` element |
| `--mj-form-gap` | Gap between slotted rows (default: `var(--mj-space-4)`) |
| `--mj-form-max-width` | Optional max-width constraint (default: `none`) |

## 10. States
- **default** — form is pristine; no validation messages shown.
- **loading** — `[loading]` attribute present; submit button shows busy state; form
  inputs remain interactive unless `disabled` is also set.
- **invalid** — one or more controls are invalid after a submit attempt; summary
  and field errors are visible; `aria-invalid` is not placed on the form element
  itself (errors live on individual controls).
- **disabled** — all slotted controls receive `disabled`; submit button is disabled.

## 11. Behavior & interactions
On submit-button activation or programmatic `submit()`, the component:
1. Calls `checkValidity()` on every form-associated `<mj-*>` control and every
   native control inside the slot.
2. If any control is invalid, fires `mj-invalid`, marks the first invalid control
   as focused, and (if a `<mj-validation-summary>` is slotted) populates it.
3. If all controls are valid (or `novalidate` is set), fires `mj-submit`. If not
   canceled, delegates to the inner `<form>.submit()`.
4. During an async submission handler, the host can set `loading` to block re-submission.
5. On reset, every `<mj-*>` control's `reset()` method is called; `mj-reset` fires
   before the inner form reset. The validation summary is cleared.
6. In `eager`/`aggressive` validation modes, the form listens for `mj-change`/
   `mj-blur` on child controls and calls `reportValidity()` on the changed control
   only after the form has been submitted at least once.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Enter` (in single-line input) | Submits the form (native browser default preserved) |
| `Enter` / `Space` (on submit button) | Submits the form |
| `Tab` / `Shift+Tab` | Moves focus through controls in DOM order |

## 13. Accessibility
- The inner `<form>` has no implicit ARIA role; it acts as a landmark only when it
  has an accessible name. If the page has a single form and a visible heading,
  authors should supply `aria-labelledby` on `<mj-form>`, which is forwarded to the
  inner `<form>`.
- When submission fails validation, focus is moved to the first invalid control and
  `mj-invalid` is fired. If a `<mj-validation-summary>` is present it is populated
  and can be configured to receive focus instead (see validationsummary.md).
- `loading` state is announced by placing a visually-hidden live-region status
  message ("Submitting…") inside the shadow DOM that is cleared on completion.

## 14. Form participation
`<mj-form>` is not itself form-associated — it IS the form boundary. It does not
contribute a value to any outer form. The inner `<form>` element owns all
`ElementInternals`-based child associations.

## 15. Internationalization & RTL
- The "Submitting…" status string (§13) is overridable via a `submitting-label`
  attribute and the shared localization hook.
- Layout direction follows the inherited `dir` attribute on the shadow host.
- No locale-specific formatting; individual controls handle their own formatting.

## 16. Progressive enhancement / SSR
Server-renders as a plain `<form>` with `method`/`action` filled. On upgrade, the
component wraps the server-rendered form markup, preserving existing control names
and values. If scripting is unavailable the inner `<form>` submits natively via its
`action`/`method` attributes without JavaScript interception.

## 17. Dependencies
- `web-component-development-plan.md` §6: Registry + base element helper,
  Form-association helper, Live-region/announcement service, Design-token stylesheet.
- `<mj-validation-summary>` (optional companion; see validationsummary.md).
- `<mj-fieldset>`, `<mj-label>`, `<mj-help-text>`, `<mj-error-message>` as structural peers.

## 18. Edge cases & error handling
- Nested `<mj-form>` elements are detected on `connectedCallback`; a console error
  is logged and the inner component does not create a second `<form>` element.
- Controls dynamically added after connection are discovered via a `MutationObserver`
  on the default slot and included in the next validity check.
- If `action` is empty and `method` is `"get"`, submission navigates to the current
  URL — the same native behavior; no special handling needed.
- When `loading` is set and the user activates submit again, the event is ignored
  and no duplicate `mj-submit` is fired.
- A form with zero named controls fires `mj-submit` with an empty `formData` and
  `value`; it does not throw.

## 19. Acceptance criteria
- [ ] Submitting a form with all valid controls fires `mj-submit` with correct
      `formData` and `value` payload; canceling the event prevents native submit.
- [ ] Submitting a form with one or more invalid controls fires `mj-invalid` (not
      `mj-submit`), moves focus to the first invalid control, and populates an
      associated `<mj-validation-summary>`.
- [ ] `validate="eager"` calls `reportValidity()` on a control after its blur,
      only after the form has been submitted at least once.
- [ ] `validate="aggressive"` calls `reportValidity()` on a control on each change,
      only after the form has been submitted at least once.
- [ ] Setting `loading` disables the submit button and announces "Submitting…".
- [ ] `reset()` restores all `<mj-*>` controls and clears the validation summary.
- [ ] Keyboard-only user can submit and reset the form without a pointing device.
- [ ] Axe-core reports zero violations on a fully populated form.
- [ ] No-JS: form submits natively via `action`/`method` with all control values.

## 20. Open questions
- Should `<mj-form>` support a `target` attribute (for iframe targets or `_blank`)
  or document that authors use a native `<form>` in those cases?
- Should `mj-submit` carry the full `FormData` or only a plain object? (Both are
  currently specified; confirm which is primary.)
