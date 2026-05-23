# Error Message Spec

- **Tag:** `<mj-error-message>`
- **Class / file:** `MjErrorMessage` / `mjerrormessage.js`
- **Category:** Text & data-entry controls — form-structure primitives
- **Primary or Variant:** Primary
- **Synonyms covered:** Error message, Field error, Validation message, Inline error
- **Phase:** P0
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-error-message>` displays a field-level validation error beneath (or beside) a
form control. It is linked to the control via `aria-describedby` and exposed as a
polite live region so screen readers announce the error when it appears or changes.
It is semantically distinct from help text (always visible guidance) and from the
validation summary (page-level error list).

## 2. When to use / when not to use
**Use** for every field-level validation error — required-field violations, format
errors, range errors, async server-side validation failures.
**Do not use** for non-error statuses (info, success, warning); use `<mj-alert>`
or `<mj-help-text>` for those. **Do not use** as a replacement for the label.
**Do not use** for page-level summaries; use `<mj-validation-summary>`.

## 3. Anatomy
- **Shadow `<span role="alert">` (or live region `<span>`)** — announces the error
  text when it appears.
- **Icon slot** — optional leading error icon (e.g., an exclamation-circle glyph);
  decorative and `aria-hidden`.
- **Default slot** — the error message text.

## 4. Variants & modes
| Variant | Attribute | Description |
|---------|-----------|-------------|
| Default | _(none)_ | Field-level inline error; hidden until `visible` is set |
| Always-rendered | `always-render` | Element stays in the DOM (invisible) even when there is no error, preventing layout shift when it appears |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `for` | string | `""` | Yes | ID of the control this error describes; the component adds its `id` to the control's `aria-describedby` and sets `aria-invalid="true"` on the control when `visible` |
| `id` | string | _(auto-generated)_ | Yes | Stable ID used as the `aria-describedby` target |
| `visible` | boolean | `false` | Yes | When `true`, the error text is displayed and live-region announcement is triggered |
| `always-render` | boolean | `false` | Yes | When `true`, the element occupies layout space even when not `visible`, preventing reflow |
| `message` | string | `""` | Yes | Error text as an attribute; alternative to slotting text; useful for scripted updates |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `control` | `HTMLElement \| null` | The resolved form control from the `for` attribute |
| `text` | `string` | The current error message text; reflects either `message` attribute or slot text content |

## 7. Slots
| Slot | Description |
|------|-------------|
| `icon` | Optional error icon; must be `aria-hidden="true"` |
| _(default)_ | The error message text |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-show` | `{ message: string }` | Yes | No | Fires when the error transitions from hidden to visible |
| `mj-hide` | `{}` | Yes | No | Fires when the error transitions from visible to hidden |

## 9. CSS parts & custom properties
| Part / Property | Description |
|-----------------|-------------|
| `::part(container)` | The inner error text `<span>` |
| `::part(icon)` | The icon slot wrapper |
| `--mj-error-color` | Error text color (default: `var(--mj-color-text-error)`) |
| `--mj-error-font-size` | Font size (default: `var(--mj-font-size-xs)`) |
| `--mj-error-icon-size` | Icon size (default: `var(--mj-space-4)`) |
| `--mj-error-gap` | Gap between icon and text (default: `var(--mj-space-1)`) |
| `--mj-error-margin-top` | Top margin relative to the control (default: `var(--mj-space-1)`) |

## 10. States
- **hidden** (default) — `[visible]` absent; element has `display: none` (or is
  visually hidden if `always-render` is set); `id` is not in the control's
  `aria-describedby`; `aria-invalid` is not set on the control.
- **visible** — `[visible]` present; error text is displayed; `id` is in the
  control's `aria-describedby`; `aria-invalid="true"` is set on the control; the
  live region announces the text.
- **always-render / hidden** — element occupies space but text is invisible
  (`visibility: hidden` or equivalent); `aria-hidden="true"` on the container to
  suppress announcement.
- **always-render / visible** — same as visible; layout does not shift because
  element already occupies space.

## 11. Behavior & interactions
- On `connectedCallback` and `for` change, the component resolves the target
  control. When `visible` transitions to `true`:
  1. Adds its `id` to the control's `aria-describedby`.
  2. Sets `aria-invalid="true"` on the control.
  3. Updates the live region text to trigger announcement.
- When `visible` transitions to `false`:
  1. Removes its `id` from `aria-describedby`.
  2. Removes `aria-invalid` from the control (unless the control manages its own
     invalid state independently).
  3. Clears the live region text.
- Updating `message` while `visible` is `true` updates the live region text,
  triggering a new announcement.
- The component does not decide when to show/hide itself; that is the responsibility
  of the parent control or the `<mj-form>` orchestrator.
- `always-render` is intended for steady-state layout contexts; when set, the
  element is always present in the DOM with `visibility: hidden` when not visible.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| — | `<mj-error-message>` is not focusable; no keyboard interaction |

## 13. Accessibility
- The inner container uses `role="alert"` when `visible` is set for the first time
  to trigger an assertive announcement. Subsequent text changes within the visible
  state use a `role="status"` polite update to avoid interrupting the user.
- `aria-invalid="true"` is set directly on the associated native control (or on the
  shadow-root native input of a `<mj-*>` control) so constraint-validation APIs
  report correctly.
- The error icon in the `icon` slot must carry `aria-hidden="true"` because the
  error state is conveyed in text; the icon is decorative reinforcement only.
- Error text must also convey the problem in words (not by color alone) to satisfy
  WCAG 1.4.1.
- When `always-render` is set and the message is hidden, the container has
  `aria-hidden="true"` so the invisible text is not read.

## 14. Form participation
Not form-associated. Contributes no value to `FormData`. The component manages
`aria-invalid` on the target control as a side-effect; it does not own validity
state.

## 15. Internationalization & RTL
- Error text is author-provided and may be in any language.
- In RTL layouts, icon and text follow logical inline direction.
- No locale-specific transformations are applied; localized error messages are
  supplied via the `message` attribute or slot by the owning control or form logic.

## 16. Progressive enhancement / SSR
Server renders as `<span id="…" class="mj-error-message" role="alert" hidden>…</span>`
with `aria-describedby` and `aria-invalid` already set on the associated control.
The component upgrades in place, mapping server attributes to its `visible` property.
Without scripting, the error message is revealed by the server setting `hidden`
attribute absence (i.e., the server renders the element without `hidden` when the
form has been submitted with errors).

## 17. Dependencies
- `web-component-development-plan.md` §6: Registry + base element helper,
  Live-region/announcement service, Design-token stylesheet.
- Peer form-structure primitives: `<mj-label>`, `<mj-help-text>`.
- `<mj-form>` drives `visible` on submission; `<mj-validation-summary>` reads
  errors from associated controls.
- Optional: `<mj-icon>` in the `icon` slot.

## 18. Edge cases & error handling
- `for` target not found at connection time: the component retries via
  `MutationObserver`; a console warning is logged.
- `message` attribute and default slot both populated: `message` attribute takes
  precedence for the live-region text; slot content is displayed visually.
- `visible` toggled rapidly (e.g., on each keystroke in aggressive validation mode):
  live-region announcements are debounced by 300 ms to avoid spamming screen readers.
- No error text provided (empty slot and empty `message`): `visible` is ignored;
  `aria-invalid` is not set; a console error is logged in development builds.
- Multiple `<mj-error-message>` elements with the same `for` value: each adds its
  `id` to `aria-describedby`; all errors are announced; unusual but valid.

## 19. Acceptance criteria
- [ ] Setting `visible` on an `<mj-error-message for="ctrl-id">` adds its `id` to
      `#ctrl-id`'s `aria-describedby` and sets `aria-invalid="true"` on `#ctrl-id`.
- [ ] Unsetting `visible` removes the `id` from `aria-describedby` and removes
      `aria-invalid` from the control.
- [ ] A screen reader announces the error text when `visible` transitions to `true`.
- [ ] Rapid `visible` toggles debounce live-region announcements at 300 ms.
- [ ] `always-render` prevents layout reflow when the error appears.
- [ ] Error text and icon are displayed in the correct error color from design tokens.
- [ ] RTL: icon appears on logical inline-end side of the text.
- [ ] No-JS: server-rendered `role="alert"` without `hidden` is visible immediately.
- [ ] Axe-core reports zero violations.

## 20. Open questions
- Should the assertive/polite live-region politeness be configurable via an
  `announce` attribute (`"assertive"` | `"polite"`)? Assertive is correct for the
  first appearance, but polite for in-place updates — should this switch be
  automatic or author-controlled?
- Should `<mj-error-message>` also support a `severity` attribute
  (`"error"` | `"warning"`) for future use where a warning (not error) state is
  needed inline?
