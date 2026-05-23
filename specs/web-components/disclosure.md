# Disclosure Spec

- **Tag:** `<mj-disclosure>`
- **Class / file:** `MjDisclosure` / `mjdisclosure.js`
- **Category:** Layout & content containers (§5.5)
- **Primary or Variant:** Primary
- **Synonyms covered:** Details/summary, Expander, Collapse panel
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-disclosure>` is a single show/hide region consisting of a trigger button
and a collapsible content panel. It enhances native `<details>`/`<summary>`
semantics with animated height transitions, design-token styling, and the ARIA
button + region pattern required when the `<details>` element's native behavior
is insufficient (e.g., when the panel must be controlled by a parent
`<mj-accordion>`).

## 2. When to use / when not to use

**Use** for a single show/hide region — an FAQ answer, a collapsible settings
block, a "read more" section. **Use** as the building block inside
`<mj-accordion>`. **Do not use** when the content should always be visible —
use `<mj-surface>` or a plain section. **Do not use** as a navigation pattern
— use `<mj-tabs>` or `<mj-side-nav>`.

## 3. Anatomy

- **trigger** — the button element the user activates to toggle the panel;
  surfaced as `::part(trigger)`. Contains the `summary` slot content and an
  expand/collapse indicator icon.
- **indicator** — a chevron or caret icon inside the trigger; surfaced as
  `::part(indicator)`.
- **panel** — the collapsible region; rendered as a `<div>` with
  `role="region"` and `aria-labelledby` pointing to the trigger; surfaced as
  `::part(panel)`.
- **default slot** — content placed inside the panel.
- **summary slot** — content placed inside the trigger button (replaces the
  `heading` attribute for rich trigger markup).

## 4. Variants & modes

| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Closed (default) | `open` absent | Panel is hidden; trigger shows expand indicator |
| Open | `open` boolean | Panel is visible; trigger shows collapse indicator |
| Animated | `animated` (default true) | Height transitions using `max-height` animation respecting `prefers-reduced-motion` |
| Indicator start | `indicator-position="start"` | Chevron placed before the heading text |
| Indicator end | `indicator-position="end"` (default) | Chevron placed after the heading text |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `open` | boolean | `false` | Yes | Controls whether the panel is expanded |
| `heading` | string | `""` | Yes | Plain-text label for the trigger button when `summary` slot is unused |
| `heading-level` | `"none"` \| `"1"`–`"6"` | `"none"` | Yes | Wraps the trigger in a heading element at this level for document outline; `"none"` omits the wrapper |
| `disabled` | boolean | `false` | Yes | Disables the trigger; panel state is preserved but cannot be toggled |
| `animated` | boolean | `true` | Yes | Enables height animation; set to false to disable regardless of motion preference |
| `indicator-position` | `"start"` \| `"end"` | `"end"` | Yes | Position of the expand/collapse indicator relative to the heading |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `open` | boolean | Reflects the `open` attribute; setting to `true` expands the panel programmatically |
| `panelElement` | `HTMLElement` (readonly) | Reference to the internal panel `<div>` for measurement |

## 7. Slots

| Slot | Description |
|------|-------------|
| `summary` | Rich content inside the trigger button; replaces `heading` attribute text |
| (default) | Content rendered inside the collapsible panel |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-disclosure-open` | `{}` | Yes | No | Emitted after the panel finishes opening |
| `mj-disclosure-close` | `{}` | Yes | No | Emitted after the panel finishes closing |
| `mj-disclosure-toggle` | `{ open: boolean }` | Yes | Yes | Emitted when the trigger is activated, before state changes; canceling prevents the toggle |

## 9. CSS parts & custom properties

**Parts**
- `::part(trigger)` — the button element
- `::part(indicator)` — the chevron icon inside the trigger
- `::part(panel)` — the collapsible panel region

**Custom properties**
| Property | Default token | Description |
|----------|--------------|-------------|
| `--mj-disclosure-trigger-bg` | `transparent` | Trigger background color |
| `--mj-disclosure-trigger-color` | `--mj-color-text-primary` | Trigger text color |
| `--mj-disclosure-trigger-padding` | `--mj-space-3 --mj-space-4` | Trigger padding |
| `--mj-disclosure-panel-padding` | `--mj-space-4` | Panel internal padding |
| `--mj-disclosure-border` | `--mj-color-border` | Bottom border of the trigger |
| `--mj-disclosure-duration` | `--mj-motion-duration-md` | Height animation duration |
| `--mj-disclosure-indicator-size` | `1.25rem` | Indicator icon size |

## 10. States

- **closed** — panel hidden (`display: none` after animation completes); trigger shows expand indicator.
- **open** — panel visible; trigger shows collapse indicator; `aria-expanded="true"`.
- **animating-open** — panel transitioning from `max-height: 0` to measured content height.
- **animating-close** — panel transitioning from content height to `max-height: 0`.
- **disabled** — trigger has `aria-disabled="true"` and is removed from the tab sequence.
- **focus-visible** — trigger shows `--mj-focus-ring` outline.

## 11. Behavior & interactions

The trigger is a `<button>` element. On activation the component reads
`panelElement.scrollHeight` to determine the target `max-height` and begins a
CSS transition. After the transition ends (`transitionend` event) the panel is
set to `display: none` (when closing) or `max-height: none` (when open, to allow
dynamic content growth). When `prefers-reduced-motion: reduce` is active, or when
`animated` is `false`, the transition duration is set to 0ms and the toggle is
instantaneous.

The `mj-disclosure-toggle` event fires before the state change. If a listener
calls `event.preventDefault()`, the toggle is suppressed. This allows
`<mj-accordion>` to intercept the event and manage single-open behavior.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Enter` | Toggle the panel open/closed when the trigger is focused |
| `Space` | Toggle the panel open/closed when the trigger is focused |
| `Tab` | Move focus out of the trigger to the next focusable element; when panel is open, Tab enters the panel content |
| `Shift+Tab` | Move focus to the previous focusable element |

## 13. Accessibility

- Trigger is a `<button>` with `aria-expanded` (`"true"` when open, `"false"`
  when closed) and `aria-controls` pointing to the panel's `id`.
- Panel has `role="region"` and `aria-labelledby` pointing to the trigger's `id`.
- The `region` role is only applied when the panel has an accessible name; if
  `heading` is empty and no `summary` slot content is present, the panel uses
  `role="group"` instead.
- When `heading-level` is set, a heading element wraps the trigger so the panel
  appears in the document outline; the heading has no focus behavior of its own.
- Disabled trigger: `aria-disabled="true"`, `tabindex="-1"`.
- Indicator icon is `aria-hidden="true"`.
- Minimum touch target for the trigger: 44 × 44 px.

## 14. Form participation

N/A — `<mj-disclosure>` is a disclosure widget and does not participate in forms.

## 15. Internationalization & RTL

In RTL mode the indicator icon is mirrored horizontally using CSS
`transform: scaleX(-1)` so the chevron points in the correct cultural direction.
The `heading` attribute string is rendered as-is; authors supply localized text.
`indicator-position` follows the inline axis and uses logical CSS margins.

## 16. Progressive enhancement / SSR

The server renders `<mj-disclosure>` as a native `<details>`/`<summary>` pair.
Before the script loads the browser provides built-in disclosure behavior. After
upgrade the component replaces the `<details>` with a `<button>` + `<div>` inside
shadow DOM while moving the original content into the default slot. If `open` was
set on the `<details>`, the panel opens after upgrade.

## 17. Dependencies

- Section 6: Registry + base element helper; design-token stylesheet; focus
  utilities.
- Used by `<mj-accordion>` as the panel building block.

## 18. Edge cases & error handling

- **No `heading` and no `summary` slot** — trigger renders with no visible label;
  a console warning is emitted. `aria-label` on `<mj-disclosure>` can provide an
  accessible name.
- **Dynamic panel content growth** — after opening, `max-height: none` is set so
  content can grow freely; no re-animation is triggered.
- **Rapid toggle clicks** — if the user clicks again during an animation, the
  animation reverses from its current position.
- **`open` set programmatically during animation** — the ongoing animation is
  cancelled and the new target state is applied immediately.

## 19. Acceptance criteria

- [ ] Clicking the trigger toggles the `open` attribute and the panel visibility.
- [ ] `mj-disclosure-toggle` event fires before state change; `preventDefault()` suppresses the toggle.
- [ ] `mj-disclosure-open` fires after the panel finishes opening.
- [ ] `mj-disclosure-close` fires after the panel finishes closing.
- [ ] Trigger `aria-expanded` matches the `open` state.
- [ ] Panel `aria-labelledby` points to the trigger id.
- [ ] Animation uses `max-height` transition and respects `prefers-reduced-motion`.
- [ ] `disabled` attribute sets `aria-disabled="true"` and `tabindex="-1"` on the trigger.
- [ ] RTL mode mirrors the indicator icon.
- [ ] SSR upgrade from `<details>/<summary>` preserves open/closed state.
- [ ] Automated accessibility check passes with no violations.

## 20. Open questions

- Should `<mj-disclosure>` expose a `persist` attribute to save open/closed state to `localStorage` by a given key?
- Is a `lazy` attribute that defers rendering the panel content until first open useful, given that deferred rendering can affect SSR upgrade fidelity?
