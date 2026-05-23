# Disclosure Button Spec

- **Tag:** `<mj-disclosure-button>`
- **Class / file:** `MjDisclosureButton` / `mjdisclosurebutton.js`
- **Category:** Buttons & actions (§5.3)
- **Primary or Variant:** Primary
- **Synonyms covered:** Disclosure button, Expand/collapse button, Show/hide button
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-disclosure-button>` is a button that shows or hides a related content region.
It exposes `aria-expanded` and `aria-controls` so assistive technology can
understand the relationship between the trigger and the controlled panel. It covers
every "expand/collapse" and "show/hide" affordance that is not part of a full
`<mj-accordion>` (which manages a group of disclosures). It is the trigger half of
the Disclosure pattern (APG); the panel itself is an arbitrary element identified by
`controls`.

## 2. When to use / when not to use

Use when a single section of content needs to be independently shown or hidden by
the user (FAQ answer, advanced options, description overflow). Do not use for
mutually exclusive panels — use `<mj-accordion>` or `<mj-tabs>`. Do not use to
toggle a persistent on/off action state — use `<mj-toggle-button>`. Do not use to
open an overlay or dialog — use `<mj-dialog>` / `<mj-popover>` triggers. The
`<mj-accordion>` component composes `<mj-disclosure-button>` internally.

## 3. Anatomy

- **Host element** — the custom element; no visual surface of its own.
- **button (part)** — inner `<button>` with `aria-expanded` and `aria-controls`;
  the focusable target.
- **label (part)** — default slot holding the trigger label text.
- **chevron (part)** — optional decorative arrow icon that rotates to indicate
  expanded/collapsed state; rendered from an internal template, not a slot.

## 4. Variants & modes

The button appearance inherits `variant` and `size` from the same token system as
`<mj-button>`. The key behavioral dimension is:

| Mode               | `chevron` attribute | Description |
|--------------------|---------------------|-------------|
| Label only         | `false`             | No decorative chevron; label alone communicates state |
| Label + chevron    | `true`              | Chevron rotates 180° when expanded |
| Icon button        | `false` + `icon-only` | Icon-only trigger; `label` attribute required for name |

## 5. Attributes

| Attribute    | Type                           | Default      | Reflects | Description |
|--------------|--------------------------------|--------------|----------|-------------|
| `expanded`   | boolean                        | `false`      | Yes      | Current disclosure state; maps to `aria-expanded` |
| `controls`   | string (id or CSS selector)    | —            | Yes      | `id` of the controlled panel element |
| `variant`    | `primary\|secondary\|tertiary` | `tertiary`   | Yes      | Visual emphasis; typically tertiary for disclosure triggers |
| `size`       | `sm\|md\|lg`                   | `md`         | Yes      | Token-mapped height and padding |
| `disabled`   | boolean                        | `false`      | Yes      | Disables interaction; `aria-disabled="true"` |
| `chevron`    | boolean                        | `true`       | Yes      | Show/hide the decorative rotating chevron icon |
| `icon-only`  | boolean                        | `false`      | Yes      | Visually hides label; requires `label` for accessible name |
| `label`      | string                         | —            | Yes      | Accessible name override when `icon-only` is set |

## 6. Properties

| Property    | Type                      | Description |
|-------------|---------------------------|-------------|
| `expanded`  | `boolean`                 | Reflects `expanded` attribute; settable programmatically |
| `controls`  | `string`                  | Reflects `controls` attribute |
| `panelEl`   | `Element \| null`         | Resolved panel element from `controls` at runtime (read-only) |

## 7. Slots

| Slot        | Description |
|-------------|-------------|
| (default)   | Trigger label text |
| `icon`      | Optional leading icon (e.g. section icon accompanying the label) |

## 8. Events

| Event          | `detail`                                          | Bubbles | Cancelable | Description |
|----------------|---------------------------------------------------|---------|------------|-------------|
| `mj-change`    | `{ expanded: boolean, originalEvent: Event }`     | Yes     | Yes        | Fires before `expanded` changes; canceling prevents the state change |
| `mj-expanded`  | `{ expanded: boolean }`                           | Yes     | No         | Fires after the `expanded` state has changed |

## 9. CSS parts & custom properties

**Parts**
- `::part(button)` — inner `<button>`; receives `[aria-expanded]` attribute
- `::part(label)` — label text wrapper
- `::part(icon)` — leading icon wrapper
- `::part(chevron)` — rotating chevron indicator

**Custom properties**
| Property | Description |
|---|---|
| `--mj-disclosure-button-color` | Label/icon color |
| `--mj-disclosure-button-color-expanded` | Color when expanded |
| `--mj-disclosure-button-bg` | Background in collapsed state |
| `--mj-disclosure-button-bg-expanded` | Background in expanded state |
| `--mj-disclosure-button-border-radius` | Corner radius |
| `--mj-disclosure-button-chevron-size` | Chevron icon size |
| `--mj-disclosure-button-chevron-transition` | Chevron rotation transition duration |
| `--mj-disclosure-button-focus-ring-color` | Focus ring color |
| `--mj-disclosure-button-padding-x` | Horizontal padding |
| `--mj-disclosure-button-height` | Height (size token) |

## 10. States

| State         | Visual effect | ARIA effect |
|---------------|---------------|-------------|
| collapsed     | Resting colors; chevron pointing down/right | `aria-expanded="false"` |
| expanded      | Expanded token colors; chevron rotated 180° | `aria-expanded="true"` |
| hover         | Tinted overlay | — |
| focus-visible | 2 px focus ring | — |
| active        | Pressed tint | — |
| disabled      | Reduced opacity; no pointer events | `aria-disabled="true"` |

## 11. Behavior & interactions

- Activation fires `mj-change` (cancelable). If not cancelled, `expanded` is toggled
  and `mj-expanded` is fired.
- The component does not directly show/hide the panel; it only manages its own
  `expanded` state. Consumers are responsible for reacting to `mj-expanded` (or
  observing the `expanded` attribute) to show/hide the panel. Exception: when
  `controls` references an element in the same document, the component automatically
  sets `aria-controls` on the inner `<button>` pointing at that element's `id`.
- The chevron rotates 180° when `expanded` is true, with a CSS transition governed
  by `--mj-disclosure-button-chevron-transition`. `prefers-reduced-motion` disables
  the transition.
- When `<mj-disclosure-button>` is used inside `<mj-accordion>`, the accordion sets
  `expanded` and listens for `mj-change` events externally; the disclosure button
  itself has no knowledge of the accordion context.
- Panel visibility is not managed here: it is either controlled by the consumer
  script reacting to events, or by `<mj-accordion>` / `<mj-disclosure>` wrappers
  that pair this button with a panel element.

## 12. Keyboard interaction

| Key         | Action |
|-------------|--------|
| `Space`     | Toggles `expanded` state |
| `Enter`     | Toggles `expanded` state |
| `Tab`       | Moves focus to next focusable element |
| `Shift+Tab` | Moves focus to previous focusable element |

## 13. Accessibility

- The inner `<button>` has `aria-expanded="true"` or `aria-expanded="false"`.
- `aria-controls` is set to the id of the controlled panel when `controls` resolves
  to a valid element with an `id`.
- If `controls` does not resolve, a console warning is emitted and `aria-controls`
  is omitted; the button still functions as a visual toggle.
- When `icon-only` is set, `aria-label` is set from `label`; absence of `label`
  triggers a console warning.
- The chevron is `aria-hidden="true"` — it is decorative; state is communicated by
  `aria-expanded` alone.
- Minimum target size: 44 × 44 CSS px.

## 14. Form participation

N/A. `<mj-disclosure-button>` is not a form-associated element.

## 15. Internationalization & RTL

- In RTL, the chevron icon points left when collapsed and rotates appropriately
  when expanded, using CSS logical transforms.
- Label text is rendered from the default slot and is not managed by this component.
- The `label` attribute (for icon-only mode) is localizable via the shared
  localization hook.

## 16. Progressive enhancement / SSR

Server renders `<mj-disclosure-button controls="panel-1">Show details</mj-disclosure-button>`.
Before upgrade, the element is unstyled inline content. When scripting is unavailable
the content region identified by `controls` should be rendered visible by default
(server sets the panel to shown) so no content is inaccessible. On upgrade, the
component takes over state management and can collapse the panel to the server-default
state.

## 17. Dependencies

- **Registry + base element helper** (§6)
- **Design-token stylesheet** (§6)
- **Localization hook** (§6) — `label` override
- `<mj-accordion>` composes this component as its item trigger (P1)
- `<mj-disclosure>` (P1) — the paired panel/wrapper component for full disclosure patterns

## 18. Edge cases & error handling

- `controls` references an element without an `id`: the component assigns a generated
  `id` to the target element and uses it; logs an info message.
- `controls` references a non-existent id: `aria-controls` is omitted; console warning.
- `expanded` toggled programmatically when `disabled`: property updates and `aria-expanded`
  reflects; the disabled state only prevents user-initiated activation.
- Long label text: button grows horizontally; chevron stays aligned to the trailing edge.
- `mj-change` cancelled: `expanded` stays unchanged; `mj-expanded` not fired; chevron
  does not rotate.

## 19. Acceptance criteria

- [ ] `expanded` attribute/property toggles on activation; reflects to `aria-expanded`.
- [ ] `aria-controls` is set to the controlled panel's id when `controls` resolves.
- [ ] `mj-change` fires before state changes and is cancelable.
- [ ] `mj-expanded` fires after state changes with correct `expanded` value.
- [ ] Chevron rotates 180° when `expanded`; rotation is suppressed under `prefers-reduced-motion`.
- [ ] `disabled` blocks activation and sets `aria-disabled="true"`.
- [ ] Chevron is `aria-hidden="true"` in all states.
- [ ] `icon-only` without `label` emits a console warning.
- [ ] `icon-only` with `label` sets `aria-label` on inner `<button>`.
- [ ] `controls` targeting element without `id` auto-assigns an id with info log.
- [ ] Keyboard: Space and Enter toggle; Tab navigates naturally.
- [ ] Minimum target size 44 × 44 CSS px.
- [ ] axe scan zero violations in expanded and collapsed states.
- [ ] Light, dark, high-contrast, RTL rendering verified.

## 20. Open questions

- Should `<mj-disclosure-button>` also directly toggle `hidden` / `aria-hidden` on
  the panel element when `controls` resolves, or leave all panel state to consumers?
  Direct management would simplify common usage but may conflict with animation
  libraries.
- Should `expanded` default to `true` be supported for panels that begin open?
  (Currently: yes, via the `expanded` attribute.)
- Confirm whether the chevron direction convention is down=collapsed / up=expanded
  (vertical content) or right=collapsed / down=expanded (tree-style).
