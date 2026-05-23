# Toggle Button Spec

- **Tag:** `<mj-toggle-button>`
- **Class / file:** `MjToggleButton` / `mjtogglebutton.js`
- **Category:** Buttons & actions (§5.3)
- **Primary or Variant:** Primary
- **Synonyms covered:** Toggle button, On/off action button
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-toggle-button>` is a stateful button that represents a binary on/off action.
It exposes `aria-pressed` to communicate its pressed/unpressed state to assistive
technology. Unlike a checkbox it is an action trigger (something happens immediately
when pressed) rather than a persistent form value; unlike `<mj-disclosure-button>`
it does not semantically show or hide a related content region.

## 2. When to use / when not to use

Use for actions with a persistent toggled state that takes immediate effect, such as
enabling bold formatting in a toolbar, muting audio, or pinning an item. Do not use
when the state is a form input value — use a checkbox instead. Do not use to
show/hide content — use `<mj-disclosure-button>`. Do not use for mutually exclusive
choices — use `<mj-segmented-control>` or a radio group. Distinguish from
`<mj-favorite-button>` which layers persistence and optimistic UI concerns on top of
the toggle pattern.

## 3. Anatomy

- **Host element** — the custom element; receives focus.
- **button (part)** — inner `<button>` with `aria-pressed`; the actual focusable target.
- **icon-off (part)** — icon shown when the button is not pressed (`slot="icon-off"`).
- **icon-on (part)** — icon shown when the button is pressed (`slot="icon-on"`).
- **label (part)** — default slot wrapping the button label.

## 4. Variants & modes

The toggle button inherits the `variant` and `size` attribute set of `<mj-button>`.
It adds two orthogonal modes:

| Mode attribute       | Value     | Description |
|----------------------|-----------|-------------|
| `icon-only`          | boolean   | Label is visually hidden; `label` attribute provides accessible name |
| `variant`            | `primary\|secondary\|tertiary` | Visual emphasis; `link` variant is not applicable |

Toggled vs. untoggled appearance is driven by the `pressed` state and CSS `[pressed]`
part selectors backed by design tokens; there are no separate variant names for the
two states.

## 5. Attributes

| Attribute    | Type                               | Default      | Reflects | Description |
|--------------|------------------------------------|--------------|----------|-------------|
| `pressed`    | boolean                            | `false`      | Yes      | Current toggle state; maps to `aria-pressed` |
| `variant`    | `primary\|secondary\|tertiary`     | `secondary`  | Yes      | Visual emphasis tier |
| `size`       | `sm\|md\|lg`                       | `md`         | Yes      | Token-mapped height and padding |
| `disabled`   | boolean                            | `false`      | Yes      | Disables interaction; `aria-disabled="true"` |
| `loading`    | boolean                            | `false`      | Yes      | Shows spinner; `aria-busy="true"` |
| `icon-only`  | boolean                            | `false`      | Yes      | Visually hides label; requires `label` for accessible name |
| `label`      | string                             | —            | Yes      | Accessible name override; required when `icon-only` is set |

## 6. Properties

| Property  | Type      | Description |
|-----------|-----------|-------------|
| `pressed` | `boolean` | Reflects the `pressed` attribute; toggles on activation unless prevented |
| `disabled`| `boolean` | Reflects `disabled` attribute |
| `loading` | `boolean` | Reflects `loading` attribute |

## 7. Slots

| Slot        | Description |
|-------------|-------------|
| (default)   | Button label text |
| `icon-off`  | Icon shown when `pressed` is false |
| `icon-on`   | Icon shown when `pressed` is true |

## 8. Events

| Event          | `detail`                                              | Bubbles | Cancelable | Description |
|----------------|-------------------------------------------------------|---------|------------|-------------|
| `mj-change`    | `{ pressed: boolean, originalEvent: Event }`          | Yes     | Yes        | Fired before `pressed` changes; canceling prevents the state change |
| `mj-pressed`   | `{ pressed: boolean }`                                | Yes     | No         | Fired after the `pressed` state has changed |

## 9. CSS parts & custom properties

**Parts**
- `::part(button)` — inner `<button>` element; gains `[aria-pressed="true"]` attribute
- `::part(icon-off)` — off-state icon wrapper
- `::part(icon-on)` — on-state icon wrapper
- `::part(label)` — label text wrapper
- `::part(spinner)` — loading spinner

**Custom properties**
| Property | Description |
|---|---|
| `--mj-toggle-button-bg` | Background in unpressed state |
| `--mj-toggle-button-bg-pressed` | Background in pressed state |
| `--mj-toggle-button-color` | Label/icon color in unpressed state |
| `--mj-toggle-button-color-pressed` | Label/icon color in pressed state |
| `--mj-toggle-button-border-color` | Border in unpressed state |
| `--mj-toggle-button-border-color-pressed` | Border in pressed state |
| `--mj-toggle-button-border-radius` | Corner radius |
| `--mj-toggle-button-height` | Height (size-mapped token) |
| `--mj-toggle-button-padding-x` | Horizontal padding |
| `--mj-toggle-button-focus-ring-color` | Focus ring color |

## 10. States

| State         | Visual effect | ARIA effect |
|---------------|---------------|-------------|
| default (off) | Resting unpressed token colors | `aria-pressed="false"` |
| default (on)  | Pressed token colors (`--mj-toggle-button-bg-pressed`, etc.) | `aria-pressed="true"` |
| hover         | Tinted overlay on current state colors | — |
| focus-visible | 2 px focus ring | — |
| active        | Pressed/depressed tint | — |
| disabled      | Reduced opacity; no pointer events | `aria-disabled="true"` on inner `<button>` |
| loading       | Spinner; label visually hidden | `aria-busy="true"` |

## 11. Behavior & interactions

- Activation (click or Space/Enter) fires `mj-change` with `cancelable: true`.
  If the event is not cancelled, `pressed` is toggled and `mj-pressed` is fired.
- While `loading` is true, activation is blocked; the current `pressed` state is
  preserved and displayed.
- `icon-off` is shown when `pressed` is false; `icon-on` is shown when `pressed` is
  true. If only one icon slot is provided it is shown in both states.
- Transition between pressed/unpressed uses a short CSS transition on background and
  color driven by `prefers-reduced-motion`-aware tokens.
- The component does not manage persistence; the consuming application is responsible
  for persisting state across sessions.

## 12. Keyboard interaction

| Key         | Action |
|-------------|--------|
| `Space`     | Toggles `pressed` state (native `<button>` activation) |
| `Enter`     | Toggles `pressed` state |
| `Tab`       | Moves focus to next focusable element |
| `Shift+Tab` | Moves focus to previous focusable element |

## 13. Accessibility

- The inner `<button>` has `aria-pressed="true"` or `aria-pressed="false"` matching
  the current `pressed` state.
- When `icon-only` is set, `aria-label` on the inner `<button>` is set from the
  `label` attribute; absence of `label` triggers a console warning.
- The accessible name must communicate both the action and, when icon-only, the
  meaning of both states (e.g. "Mute" not "Muted/Unmuted"). Consider providing
  two distinct `label` values for off/on states via `label-off` / `label-on`
  attributes (see Open questions).
- Minimum contrast: 4.5:1 for text; icon contrast checked in both pressed and
  unpressed states.
- Minimum target size: 44 × 44 CSS px.

## 14. Form participation

N/A. `<mj-toggle-button>` is an action button, not a form input. Its `pressed`
state is not submitted in form data. Use a checkbox for form-associated boolean
input.

## 15. Internationalization & RTL

- In RTL layouts, icon and label order mirrors via CSS logical properties.
- `label`, `label-off`, and `label-on` are localizable via the shared localization
  hook.
- Directional icons (if used) flip in RTL the same as `<mj-button>`.

## 16. Progressive enhancement / SSR

Server renders `<mj-toggle-button pressed label="Mute">Mute</mj-toggle-button>`.
Before upgrade the element displays as an unstyled inline element. Base token styles
can apply minimal appearance. On upgrade the shadow `<button>` with `aria-pressed`
is created. The slotted label is preserved.

## 17. Dependencies

- **Registry + base element helper** (§6)
- **Design-token stylesheet** (§6)
- **Live-region service** (§6) — state-change announcements (optional, configurable)
- **Localization hook** (§6) — `label`, `label-off`, `label-on` strings
- `<mj-spinner>` (Progress, P0) — loading state

## 18. Edge cases & error handling

- `icon-only` set without `label`: console warning; `aria-label` is empty string.
- `pressed` attribute present without a value (`<mj-toggle-button pressed>`):
  treated as `pressed="true"` (boolean attribute semantics).
- `disabled` + `loading` simultaneously: `disabled` takes precedence.
- `mj-change` cancelled by consumer: `pressed` property stays at its current value;
  no `mj-pressed` event is fired; visual state does not change.
- Both `icon-off` and `icon-on` absent: no icon rendered; label-only layout used.

## 19. Acceptance criteria

- [ ] `pressed` attribute/property toggles on activation; reflects to `aria-pressed`.
- [ ] `mj-change` fires with correct `pressed` value before state changes; cancellation prevents change.
- [ ] `mj-pressed` fires after state changes with correct `pressed` value.
- [ ] `icon-off` is visible when `pressed` is false; `icon-on` when `pressed` is true.
- [ ] `disabled` blocks activation and sets `aria-disabled="true"`.
- [ ] `loading` blocks activation, shows spinner, sets `aria-busy="true"`.
- [ ] `icon-only` without `label` attribute emits a console warning.
- [ ] `icon-only` with `label` sets `aria-label` on inner `<button>`.
- [ ] Keyboard: Space and Enter toggle pressed state; Tab navigates naturally.
- [ ] Minimum target size 44 × 44 CSS px for all `size` values.
- [ ] axe scan reports zero violations in pressed and unpressed states.
- [ ] Light, dark, high-contrast, and RTL rendering verified.

## 20. Open questions

- Should `label-off` / `label-on` attributes be supported to allow the accessible
  name to change based on pressed state (e.g. "Mute" when off, "Unmute" when on)?
  This is a common pattern but can confuse users if not carefully designed.
- Should `<mj-toggle-button>` be usable inside `<mj-segmented-control>` as an
  item? If so, the segmented control manages the `pressed` state and roving tabindex
  externally.
- Confirm the default `variant` value: `secondary` (outlined) is proposed because it
  naturally differentiates toggled/untoggled states without conflicting with primary
  action prominence.
