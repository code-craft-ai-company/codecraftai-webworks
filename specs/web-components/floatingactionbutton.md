# Floating Action Button Spec

- **Tag:** `<mj-fab>`
- **Class / file:** `MjFab` / `mjfab.js`
- **Category:** Buttons & actions (§5.3)
- **Primary or Variant:** Primary
- **Synonyms covered:** Floating action button, FAB, Speed dial (multi-action variant)
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-fab>` provides a prominent, fixed-position button for the single most important
action available on a screen (e.g. "Compose", "Add", "Create"). It floats above the
content layer via an elevated surface and is always reachable regardless of scroll
position. It intentionally hosts only one primary action to avoid competing with
other page affordances.

## 2. When to use / when not to use

Use when one action is so dominant that it warrants persistent, elevated visibility
across the full page scroll. Do not use for secondary or destructive actions. Do not
place more than one FAB on a single screen. When multiple related actions are needed,
consider a speed-dial variant (sub-actions revealed on expand) rather than multiple
FABs. For actions that are contextually scoped to a section rather than the whole
page, use an `<mj-button variant="primary">` inline instead.

## 3. Anatomy

- **Host element** — fixed-positioned container; manages placement and z-index via
  design tokens.
- **button (part)** — inner `<button>` element; the actual interactive target.
- **icon (part)** — required icon slot; the primary visual identifier of the action.
- **label (part)** — optional visible label slot; shown in the "extended" size.
- **speed-dial-list (part)** — `<ul>` of sub-action buttons revealed when
  `expanded` (speed-dial mode only).

## 4. Variants & modes

| Mode           | `size` value | Label visible | Description |
|----------------|--------------|---------------|-------------|
| Standard FAB   | `md`         | No            | Icon-only circular button |
| Mini FAB       | `sm`         | No            | Smaller circular variant for dense layouts |
| Large FAB      | `lg`         | No            | Larger circular for prominent placement |
| Extended FAB   | `extended`   | Yes           | Pill-shaped with icon + visible text label |
| Speed dial     | any + `speed-dial` attribute | Yes (sub-items) | Expands to reveal sub-action buttons |

## 5. Attributes

| Attribute      | Type                              | Default       | Reflects | Description |
|----------------|-----------------------------------|---------------|----------|-------------|
| `size`         | `sm\|md\|lg\|extended`            | `md`          | Yes      | Controls shape and dimensions |
| `label`        | string                            | —             | Yes      | Accessible name; visible text when `size="extended"` |
| `position`     | `bottom-end\|bottom-start\|top-end\|top-start` | `bottom-end` | Yes | Viewport corner for fixed placement |
| `disabled`     | boolean                           | `false`       | Yes      | Disables interaction; `aria-disabled="true"` |
| `loading`      | boolean                           | `false`       | Yes      | Shows spinner; `aria-busy="true"` |
| `speed-dial`   | boolean                           | `false`       | Yes      | Enables speed-dial sub-action mode |
| `expanded`     | boolean                           | `false`       | Yes      | Speed-dial open state; `aria-expanded` on trigger |
| `offset-x`     | string (CSS length)               | `1rem`        | Yes      | Horizontal offset from the viewport edge |
| `offset-y`     | string (CSS length)               | `1rem`        | Yes      | Vertical offset from the viewport edge |

## 6. Properties

| Property    | Type      | Description |
|-------------|-----------|-------------|
| `expanded`  | `boolean` | Reflects speed-dial open state; settable programmatically |
| `loading`   | `boolean` | Reflects `loading` attribute |

## 7. Slots

| Slot             | Description |
|------------------|-------------|
| `icon`           | Required icon for the primary action |
| (default)        | Visible label text (rendered only when `size="extended"`) |
| `speed-dial-item`| One or more `<mj-fab-item>` sub-actions in speed-dial mode |

## 8. Events

| Event             | `detail`                                         | Bubbles | Cancelable | Description |
|-------------------|--------------------------------------------------|---------|------------|-------------|
| `mj-click`        | `{ originalEvent: MouseEvent \| KeyboardEvent }` | Yes     | No         | Primary button activated |
| `mj-expanded`     | `{ expanded: boolean }`                          | Yes     | No         | Speed-dial open/close state changed |

## 9. CSS parts & custom properties

**Parts**
- `::part(button)` — inner `<button>` element
- `::part(icon)` — icon wrapper
- `::part(label)` — label text wrapper (extended mode)
- `::part(speed-dial-list)` — sub-action list container
- `::part(spinner)` — loading spinner

**Custom properties**
| Property | Description |
|---|---|
| `--mj-fab-bg` | Background color |
| `--mj-fab-color` | Icon/label color |
| `--mj-fab-size` | Diameter for standard/mini/large modes |
| `--mj-fab-border-radius` | Corner radius (full circle for icon-only; pill for extended) |
| `--mj-fab-elevation` | Box-shadow elevation token |
| `--mj-fab-z-index` | Stacking order (default from elevation z-index tokens) |
| `--mj-fab-offset-x` | Horizontal viewport offset |
| `--mj-fab-offset-y` | Vertical viewport offset |
| `--mj-fab-focus-ring-color` | Focus ring color |
| `--mj-fab-speed-dial-gap` | Gap between sub-action buttons in speed-dial list |

## 10. States

| State         | Visual effect | ARIA effect |
|---------------|---------------|-------------|
| default       | Elevated surface at rest | — |
| hover         | Increased elevation / tinted background | — |
| focus-visible | 2 px focus ring | — |
| active        | Pressed/depressed tint, reduced elevation | — |
| disabled      | Reduced opacity, no pointer events | `aria-disabled="true"` |
| loading       | Spinner replaces icon | `aria-busy="true"` |
| expanded      | Speed-dial list visible; trigger rotated 45° | `aria-expanded="true"` |

## 11. Behavior & interactions

- The FAB is `position: fixed` relative to the viewport at the corner specified by
  `position`, offset by `offset-x` / `offset-y`.
- On narrow viewports the component shrinks from `extended` to icon-only automatically
  when the `size="extended"` layout would overflow; the label becomes the
  `aria-label` in that case.
- In speed-dial mode, activating the primary button toggles `expanded`. Sub-actions
  animate in (slide + fade) from the primary button direction. Clicking outside or
  pressing Escape closes the speed dial and returns focus to the primary button.
- `prefers-reduced-motion`: speed-dial open/close animations are skipped; icon
  rotation is suppressed.
- The FAB avoids overlapping the browser's virtual keyboard on mobile by listening
  to the `visualViewport` resize event and adjusting `offset-y`.
- Content scroll must not obscure interactive page content: the component emits its
  natural size to consumers via a CSS custom property on `:host` so page layouts can
  add matching bottom padding.

## 12. Keyboard interaction

| Key            | Action |
|----------------|--------|
| `Tab`          | Moves focus to the FAB from the tab sequence |
| `Space`        | Activates primary button (or toggles speed-dial) |
| `Enter`        | Activates primary button (or toggles speed-dial) |
| `Escape`       | Closes speed-dial if open; focus returns to primary button |
| `Arrow Up`     | In speed-dial open state: moves focus to previous sub-action |
| `Arrow Down`   | In speed-dial open state: moves focus to next sub-action |

## 13. Accessibility

- Inner `<button>` carries the native button role.
- `aria-label` is always set from the `label` attribute; in extended mode it
  duplicates the visible label to ensure consistent naming.
- In speed-dial mode: primary button has `aria-expanded` and `aria-haspopup="menu"`;
  the sub-action list has `role="menu"`; each sub-action has `role="menuitem"`.
- Speed-dial sub-actions are hidden from the accessibility tree (`aria-hidden="true"`)
  when `expanded` is false.
- Minimum target size: 44 × 44 CSS px for `sm` and `md`; `lg` and `extended` are
  naturally larger.
- Focus is never trapped; the FAB is a normal tab stop.

## 14. Form participation

N/A. The FAB is not a form-associated element. Its inner `<button>` uses
`type="button"` always.

## 15. Internationalization & RTL

- `position="bottom-end"` resolves to bottom-right in LTR and bottom-left in RTL
  using CSS logical properties (`inset-inline-end`).
- `position="bottom-start"` resolves to the opposite corner accordingly.
- The `label` attribute string is the localizable text; it is overridden via the
  shared localization hook.
- Speed-dial animation direction reverses in RTL.

## 16. Progressive enhancement / SSR

Server renders `<mj-fab label="Compose"><svg slot="icon">…</svg></mj-fab>`. Before
upgrade the element is display-block but not fixed-positioned; base tokens can apply
a minimal style. On upgrade the inner `<button>` is created in Shadow DOM, the icon
slot is wired, and `position: fixed` is applied. No layout shift because the host is
not part of normal document flow after upgrade.

## 17. Dependencies

- **Registry + base element helper** (§6)
- **Design-token stylesheet** (§6) — elevation, color, spacing, z-index
- **Live-region service** (§6) — loading/busy announcements
- **Localization hook** (§6) — label strings
- `<mj-spinner>` (Progress, P0) — loading state
- `<mj-button>` (P0) — sub-action items in speed-dial mode reuse button internals

## 18. Edge cases & error handling

- `label` attribute absent: component warns to console; `aria-label` falls back to
  empty string; screen readers announce the button with no name.
- `speed-dial` set with no `speed-dial-item` slots: no list is rendered; `expanded`
  attribute has no effect.
- Viewport too small for the FAB at the chosen corner (e.g. FAB overlaps system UI
  chrome): `offset-x`/`offset-y` can be increased; no automatic repositioning.
- Both `disabled` and `loading`: `disabled` takes precedence.
- `expanded` set to `true` when `speed-dial` is false: attribute is ignored.

## 19. Acceptance criteria

- [ ] FAB renders fixed at the correct viewport corner for each `position` value.
- [ ] `size` values (`sm`, `md`, `lg`, `extended`) produce correct dimensions from tokens.
- [ ] `extended` size shows visible label; icon-only sizes hide label and set `aria-label`.
- [ ] `disabled` sets `aria-disabled="true"` and blocks `mj-click`.
- [ ] `loading` shows spinner, sets `aria-busy="true"`, blocks activation.
- [ ] Speed-dial: activating the primary button toggles `expanded` and shows sub-actions.
- [ ] Speed-dial: Escape closes the list and returns focus to primary button.
- [ ] Speed-dial: Arrow keys navigate sub-actions; Tab exits the FAB.
- [ ] RTL: `bottom-end`/`bottom-start` positions resolve to correct logical sides.
- [ ] `prefers-reduced-motion`: animations are skipped.
- [ ] Minimum tap target 44 × 44 CSS px for `sm` and `md`.
- [ ] axe scan reports zero violations in standard and speed-dial open states.
- [ ] Light, dark, high-contrast, and forced-colors rendering verified.

## 20. Open questions

- Should speed-dial sub-actions use `role="menu"` / `role="menuitem"` (action
  semantics) or individual `<mj-button>` elements with no menu wrapper? Menu
  pattern implies a distinct keyboard model; confirm with UX.
- Should the FAB optionally hide/collapse when the user scrolls down (to reduce
  occlusion) and re-appear on scroll up, following Material Design behavior?
- Confirm whether `<mj-fab-item>` is its own registered custom element or an
  internal implementation detail.
