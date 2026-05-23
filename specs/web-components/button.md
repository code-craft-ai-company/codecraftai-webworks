# Button Spec

- **Tag:** `<mj-button>`
- **Class / file:** `MjButton` / `mjbutton.js`
- **Category:** Buttons & actions (§5.3)
- **Primary or Variant:** Primary
- **Synonyms covered:** Primary button, Secondary button, Tertiary button, Link button,
  Icon button, Submit button, Reset button, Cancel button, Close button, Back button,
  Next button, Previous button, Toolbar button
- **Phase:** P0
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-button>` is the single button primitive for the entire library. Every named
"button" in the catalog (primary, secondary, tertiary, link, icon, submit, reset,
cancel, close, back, next, previous, toolbar) is satisfied by a combination of
`variant`, `size`, `type`, `icon`, and `icon-only` attributes on this one element.
This consolidation prevents API fragmentation and guarantees consistent behavior,
theming, and accessibility across all button use-cases.

## 2. When to use / when not to use

Use `<mj-button>` for any user-triggered action that does not navigate to a new
document. For navigation use `<mj-link>` (a real `<a>`). Do not use a plain `<div>`
or `<span>` with a click handler as a button. Toggle actions with persistent on/off
state belong in `<mj-toggle-button>`. Disclosure/expand actions belong in
`<mj-disclosure-button>`. The icon-only variant is acceptable for toolbars provided
a visible label or tooltip is also present.

## 3. Anatomy

- **Host element** — the custom element itself; receives focus; maps to a native
  `<button>` inside shadow DOM.
- **button (part)** — the inner `<button>` element; carries all ARIA and type
  attributes; is the actual focus target.
- **icon (part)** — optional leading icon container (`<slot name="icon">`).
- **label (part)** — the default slot wrapping button label text.
- **trailing-icon (part)** — optional trailing icon container (`<slot name="trailing-icon">`).
- **spinner (part)** — `<mj-spinner>` shown during the loading state, replacing the
  label visually while the accessible name is preserved.

## 4. Variants & modes

All catalog variant names are satisfied by attribute configuration, not separate
components. The `variant` attribute selects the visual tier:

| Variant name (catalog) | `variant` value | `type` value | Notes |
|------------------------|-----------------|--------------|-------|
| Primary button         | `primary`       | `button`     | Filled, highest emphasis |
| Secondary button       | `secondary`     | `button`     | Outlined or tonal |
| Tertiary button        | `tertiary`      | `button`     | Text/ghost, lowest emphasis |
| Link button            | `link`          | `button`     | Styled as a hyperlink; still a `<button>`, never an `<a>` |
| Icon button            | `primary` (or any) | `button` | `icon-only` attribute present; requires `label` for accessible name |
| Submit button          | any             | `submit`     | Participates in form submission |
| Reset button           | any             | `reset`      | Resets the associated form |
| Cancel button          | `secondary`     | `button`     | Conventionally positioned before the primary action |
| Close button           | `tertiary`      | `button`     | `icon-only`; label defaults to "Close" for accessible name |
| Back button            | `secondary`     | `button`     | `icon` slot contains chevron-left; label "Back" |
| Next button            | `primary`       | `button`     | `icon` in trailing slot; label "Next" |
| Previous button        | `secondary`     | `button`     | Equivalent to Back in multi-step contexts |
| Toolbar button         | `tertiary`      | `button`     | Compact size; used inside `<mj-toolbar>` |

## 5. Attributes

| Attribute    | Type                                            | Default    | Reflects | Description |
|--------------|-------------------------------------------------|------------|----------|-------------|
| `variant`    | `primary\|secondary\|tertiary\|link`            | `primary`  | Yes      | Visual emphasis tier |
| `size`       | `sm\|md\|lg`                                    | `md`       | Yes      | Token-mapped height and padding |
| `type`       | `button\|submit\|reset`                         | `button`   | Yes      | Forwarded to inner `<button>` |
| `name`       | string                                          | —          | Yes      | Forwarded to inner `<button>` for form data |
| `value`      | string                                          | —          | Yes      | Forwarded to inner `<button>` for form data |
| `disabled`   | boolean                                         | `false`    | Yes      | Disables interaction; sets `aria-disabled` |
| `loading`    | boolean                                         | `false`    | Yes      | Shows spinner; sets `aria-busy="true"`; prevents clicks |
| `icon-only`  | boolean                                         | `false`    | Yes      | Hides label text visually; `label` attribute becomes the accessible name |
| `label`      | string                                          | —          | Yes      | Accessible name override; required when `icon-only` is set |
| `form`       | string (id)                                     | —          | Yes      | Associates button with a specific `<form>` by id |
| `autofocus`  | boolean                                         | `false`    | Yes      | Forwards to inner `<button>` |

## 6. Properties

| Property        | Type      | Description |
|-----------------|-----------|-------------|
| `loading`       | `boolean` | Reflects the `loading` attribute; settable programmatically |
| `disabled`      | `boolean` | Reflects the `disabled` attribute |
| `form`          | `HTMLFormElement \| null` | The associated form element resolved at runtime |

## 7. Slots

| Slot             | Description |
|------------------|-------------|
| (default)        | Button label text |
| `icon`           | Leading icon (e.g. `<mj-icon>` or `<svg>`) |
| `trailing-icon`  | Trailing icon; used for Next/dropdown-arrow patterns |

## 8. Events

| Event        | `detail`                  | Bubbles | Cancelable | Description |
|--------------|---------------------------|---------|------------|-------------|
| `mj-click`   | `{ originalEvent: MouseEvent \| KeyboardEvent }` | Yes | No | Fired after a non-disabled, non-loading click or keyboard activation |

## 9. CSS parts & custom properties

**Parts**
- `::part(button)` — the inner `<button>` element
- `::part(icon)` — leading icon wrapper
- `::part(label)` — label text wrapper
- `::part(trailing-icon)` — trailing icon wrapper
- `::part(spinner)` — loading spinner wrapper

**Custom properties**
| Property | Description |
|---|---|
| `--mj-button-bg` | Background color (resolved from variant token by default) |
| `--mj-button-color` | Label/icon color |
| `--mj-button-border-color` | Border color |
| `--mj-button-border-radius` | Corner radius |
| `--mj-button-padding-x` | Horizontal padding |
| `--mj-button-padding-y` | Vertical padding |
| `--mj-button-font-size` | Font size |
| `--mj-button-font-weight` | Font weight |
| `--mj-button-gap` | Gap between icon and label |
| `--mj-button-min-width` | Minimum width |
| `--mj-button-height` | Height (size-mapped token) |
| `--mj-button-focus-ring-color` | Focus ring color |

## 10. States

| State            | Visual effect | ARIA effect |
|------------------|---------------|-------------|
| default          | Resting token colors | — |
| hover            | Tinted background per variant token | — |
| focus-visible    | 2 px focus ring (`--mj-button-focus-ring-color`) | — |
| active           | Pressed/depressed tint | — |
| disabled         | Reduced opacity; no pointer events | `aria-disabled="true"` on inner `<button>` |
| loading          | Spinner replaces label visually; label hidden with `aria-hidden` on spinner | `aria-busy="true"` on inner `<button>` |

## 11. Behavior & interactions

- Clicking a non-disabled, non-loading button fires `mj-click` then the inner
  `<button>`'s native click, which handles form submission/reset.
- While `loading` is true all pointer events are ignored and the button is
  effectively inert without being `disabled` (so it remains in tab order and screen
  readers can query its busy state).
- The `disabled` attribute maps to `aria-disabled="true"` on the inner `<button>`
  rather than the native `disabled` attribute, keeping the element focusable so
  assistive technology can discover it.
- When `icon-only` is set, the default slot content is wrapped in a `visually-hidden`
  span; the `label` attribute (or slotted text) is exposed as `aria-label` on the
  inner `<button>`.
- Minimum target size is 44 × 44 CSS pixels for all sizes (padding is adjusted so
  the visual size may be smaller while the tap/click target is not).

## 12. Keyboard interaction

| Key              | Action |
|------------------|--------|
| `Space`          | Activates the button (native `<button>` behavior) |
| `Enter`          | Activates the button (native `<button>` behavior) |
| `Tab`            | Moves focus to next focusable element |
| `Shift+Tab`      | Moves focus to previous focusable element |

## 13. Accessibility

- The inner shadow `<button>` carries the native button role; no explicit `role`
  override is needed.
- When `label` attribute is present or default-slot text is non-empty, the
  accessible name is computed from that text.
- When `icon-only` is set, `aria-label` is set to `label` attribute value; if
  `label` is absent the component emits a console warning and falls back to any
  slotted text.
- Close/Cancel buttons that are icon-only must have `label="Close"` / `label="Cancel"`.
- `aria-busy="true"` is set during loading; a live-region announcement ("Loading…" /
  "Done") is dispatched via the shared live-region service.
- Minimum contrast: 4.5:1 for text labels; 3:1 for large text and icon-only variants.
- Minimum target size: 44 × 44 CSS px (WCAG 2.5.5).

## 14. Form participation

`<mj-button>` is a form-associated custom element. When `type="submit"` or
`type="reset"` the inner `<button>` triggers the owning form's submit/reset
natively. The `name`/`value` attributes are forwarded so the button can contribute
to `FormData` on submit (e.g. which submit button was clicked). `ElementInternals`
is used for association; the `form` attribute (by id) overrides the implicit owner.
Reset behavior: no internal state to reset.

## 15. Internationalization & RTL

- In RTL layouts (`dir="rtl"`) the icon and label order is visually mirrored;
  flexbox `direction` follows the inherited `dir`.
- The loading accessible label ("Loading", "Done") is provided via the shared
  localization hook and is overridable via the `loading-label` and `done-label`
  attributes.
- Icon glyphs that are directional (chevron-left/right for Back/Next) flip
  automatically in RTL via `transform: scaleX(-1)` governed by a token flag.

## 16. Progressive enhancement / SSR

Server renders `<mj-button variant="primary" type="submit">Save</mj-button>`.
Before the script loads the browser displays unstyled text; base styles from the
tokens stylesheet (loaded separately) can style the host element as a button
fallback. On upgrade the shadow DOM renders the inner `<button>` and the slotted
label re-appears inside it with no layout shift because the host has a reserved
`display: inline-flex` from the stylesheet.

## 17. Dependencies

- **Registry + base element helper** (§6) — lifecycle, attribute reflection
- **Design-token stylesheet** (§6) — all visual values
- **Live-region service** (§6) — loading/done announcements
- **Localization hook** (§6) — `loading-label`, `done-label` strings
- `<mj-spinner>` (Progress, P0) — rendered during loading state

## 18. Edge cases & error handling

- `icon-only` set without `label` attribute and no slotted text: warn to console,
  set `aria-label=""` (empty); component still renders.
- Both `disabled` and `loading` set simultaneously: `disabled` takes precedence
  visually; `aria-disabled` is set; `aria-busy` is not set.
- Very long label text: the button grows horizontally up to `--mj-button-min-width`
  then allows wrapping; the min-target-size guarantee applies to the height only.
- `type="submit"` inside a form with no `action`: native browser behavior applies
  (same-page submit).
- `form` attribute references a non-existent id: property returns `null`; behaves
  as un-associated.

## 19. Acceptance criteria

- [ ] Renders an inner `<button>` with correct `type` attribute in Shadow DOM.
- [ ] All `variant` values apply distinct, token-sourced visual styles.
- [ ] All `size` values (`sm`/`md`/`lg`) produce correct heights and padding from tokens.
- [ ] `disabled` sets `aria-disabled="true"` and blocks `mj-click`; element remains focusable.
- [ ] `loading` shows the spinner, hides the label visually, sets `aria-busy="true"`, blocks clicks.
- [ ] `icon-only` without `label` logs a console warning; with `label` sets `aria-label` correctly.
- [ ] `type="submit"` triggers form submission; `type="reset"` triggers form reset.
- [ ] `name`/`value` appear in `FormData` on submit.
- [ ] Keyboard: Space and Enter activate; Tab moves focus naturally.
- [ ] Minimum tap target is 44 × 44 CSS px for all sizes.
- [ ] RTL: icon/label order mirrors; directional icons flip.
- [ ] Loading label announced via live region on state entry and exit.
- [ ] axe accessibility scan reports zero violations in all documented states.
- [ ] Light, dark, high-contrast, and forced-colors rendering verified.

## 20. Open questions

- Should `disabled` use the native `disabled` attribute (removes from tab order)
  or `aria-disabled` (keeps in tab order)? Current decision: `aria-disabled` to
  keep discoverability. Confirm with UX.
- Should `loading` automatically set `disabled` after a configurable timeout to
  prevent double-submission, or leave that to the consumer?
- Confirm final icon-flip token strategy for RTL directional icons (CSS logical
  properties vs. `scaleX(-1)` transform).
