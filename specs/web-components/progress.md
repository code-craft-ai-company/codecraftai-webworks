# Progress Spec

- **Tag:** `<mj-progress>`
- **Class / file:** `MjProgress` / `mjprogress.js`
- **Category:** Feedback & status components
- **Primary or Variant:** Primary
- **Synonyms covered:** Progress bar, Progress ring, Spinner, Loading indicator
- **Phase:** P0
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-progress>` communicates the status of an ongoing operation. It covers two
visual shapes — a horizontal **bar** and a circular **ring** — and two
operational modes — **determinate** (a known percentage complete) and
**indeterminate** (activity is occurring but progress is unknown). The Spinner
synonym is the ring variant in indeterminate mode. All variants share one
implementation to ensure consistent semantics, theming, and motion behavior.

## 2. When to use / when not to use

**Use** `bar` when progress fits a linear concept (file upload, multi-step
process) and a percentage is meaningful or unknown. Use `ring` (spinner) inline
with content, inside buttons, or where a compact indicator fits better.

**Do not use** when the operation completes in under ~300 ms — an abrupt flash
of a spinner is more distracting than nothing. Do not use `<mj-progress>` for
discrete step navigation — use the Stepper (navigation) component (§5.4).
Do not use to express a quantity as a proportion of a range — use `<meter>`
or the Gauge component (§5.9).

## 3. Anatomy

**Bar variant**
- **Track** (`part="track"`) — the background rail representing the full range.
- **Fill** (`part="fill"`) — the colored indicator showing current progress.
- **Label** (`part="label"`) — optional text label from `<slot name="label">`.
- **Value text** (`part="value-text"`) — optional numeric value display
  (`32%`, `4 of 12`) from the `value-text` attribute or `<slot name="value-text">`.

**Ring variant**
- **SVG container** (`part="ring"`) — an SVG circle track and stroke fill.
- **Track circle** (`part="ring-track"`) — background SVG circle.
- **Fill circle** (`part="ring-fill"`) — animated SVG `stroke-dashoffset` fill.
- **Center slot** (`part="center"`) — `<slot name="center">` for optional icon
  or percentage inside the ring.
- **Label** (`part="label"`) — text label below or beside the ring.

## 4. Variants & modes

| Shape | `variant` value | Description |
|-------|-----------------|-------------|
| Bar | `bar` (default) | Horizontal progress bar |
| Ring | `ring` | Circular progress ring / spinner |

| Mode | `indeterminate` | `value` range | Description |
|------|-----------------|---------------|-------------|
| Determinate | `false` (default) | `0` – `max` | Shows specific progress |
| Indeterminate | `true` | ignored | Animation loops; no value conveyed |

| Size | `size` value | Description |
|------|-------------|-------------|
| Small | `sm` | Compact use in buttons or tight layouts |
| Medium | `md` (default) | Standard use |
| Large | `lg` | Feature-area or page-level loading |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `variant` | `"bar"\|"ring"` | `"bar"` | Yes | Visual shape |
| `value` | number | `0` | Yes | Current progress value; ignored when `indeterminate` is set |
| `max` | number | `100` | Yes | Maximum value; used to compute the percentage |
| `indeterminate` | boolean | `false` | Yes | Switches to indeterminate animation mode |
| `size` | `"sm"\|"md"\|"lg"` | `"md"` | Yes | Size variant |
| `label` | string | `""` | Yes | Accessible label for the progress indicator; also visible as a text label when `show-label` is set |
| `show-label` | boolean | `false` | Yes | Renders the `label` text visibly above the indicator |
| `value-text` | string | `""` | Yes | Human-readable value string (e.g., `"32%"`, `"4 of 12 files"`); used as `aria-valuetext` and rendered when `show-value` is set |
| `show-value` | boolean | `false` | Yes | Renders the `value-text` visibly |
| `color` | string | `""` | Yes | Token name or CSS custom property override for the fill color; empty uses the default severity/brand token |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `value` | `number` | Current progress; setting this also removes `indeterminate` |
| `percentage` | `number` | Read-only; `value / max * 100` rounded to one decimal |

## 7. Slots

| Slot | Description |
|------|-------------|
| `label` | Custom label content; overrides the `label` attribute when provided |
| `value-text` | Custom value text content; overrides `value-text` attribute |
| `center` | Ring variant only — content rendered inside the ring (icon, percentage text) |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-progress-complete` | `{ value, max }` | Yes | No | Fired when `value` reaches `max` in determinate mode |
| `mj-progress-change` | `{ value, max, percentage }` | Yes | No | Fired whenever `value` or `max` changes |

## 9. CSS parts & custom properties

**Parts (bar)**
- `::part(track)` — background rail
- `::part(fill)` — progress fill
- `::part(label)` — label text wrapper
- `::part(value-text)` — value text wrapper

**Parts (ring)**
- `::part(ring)` — SVG root
- `::part(ring-track)` — background circle
- `::part(ring-fill)` — progress stroke
- `::part(center)` — center content wrapper
- `::part(label)` — label text wrapper

**Custom properties**
| Property | Description |
|----------|-------------|
| `--mj-progress-track-color` | Track (background) color |
| `--mj-progress-fill-color` | Fill (progress) color |
| `--mj-progress-height` | Bar height (bar variant) |
| `--mj-progress-border-radius` | Bar corner radius |
| `--mj-progress-ring-size` | Ring diameter (ring variant) |
| `--mj-progress-ring-stroke-width` | Ring stroke width |
| `--mj-progress-animation-duration` | Duration of the indeterminate animation cycle |
| `--mj-progress-label-gap` | Gap between label and indicator |

## 10. States

- **determinate** — `indeterminate=false`; fill width/dashoffset proportional to
  `value/max`; `aria-valuenow`, `aria-valuemin`, `aria-valuemax` are set.
- **indeterminate** — `indeterminate=true`; CSS looping animation; ARIA value
  attributes removed from the element.
- **complete** — `value === max`; `mj-progress-complete` is fired; host may
  apply a completion style via `[value][max]` CSS attribute selector.
- **reduced-motion** — when `prefers-reduced-motion: reduce` matches, the
  indeterminate animation is replaced with a static pulsing opacity animation
  that does not translate or rotate.

## 11. Behavior & interactions

`<mj-progress>` is a purely visual/ARIA component with no pointer interaction.

**Determinate fill.** The fill element's width (bar) or `stroke-dashoffset`
(ring) is calculated as `(value / max) * 100%`. Transitions are applied to
the fill via CSS (`transition: width 200ms ease, stroke-dashoffset 200ms ease`)
so value updates animate smoothly. Reduced-motion users receive instant updates.

**Indeterminate animation.** The bar variant uses a CSS `@keyframes` that slides
a gradient fill left-to-right repeatedly. The ring variant rotates the SVG and
animates `stroke-dashoffset` to simulate an arc chasing its tail. Both
animations are defined in the component stylesheet and respect `prefers-reduced-motion`.

**Accessible label requirement.** If neither `label` nor `aria-label` nor
`aria-labelledby` is supplied, the component logs a console warning; the
`progressbar` role with no accessible name is an accessibility failure.

**Ring center slot.** For the ring variant, the center slot is absolutely
positioned within the SVG viewBox bounding rectangle. Content there should be
kept simple (a single icon or short percentage string).

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| — | No interactive keys; `<mj-progress>` is not focusable by default |

The component has `tabindex="-1"` and is not in the tab sequence. If a host
wishes to expose the current value, they should place visible `value-text` near
the indicator or use a live region (see §13).

## 13. Accessibility

- **Role:** `role="progressbar"` on the indicator element.
- **Properties (determinate):** `aria-valuenow` = current integer value;
  `aria-valuemin="0"`; `aria-valuemax` = `max`; `aria-valuetext` = `value-text`
  when provided.
- **Properties (indeterminate):** `aria-valuenow`, `aria-valuemin`, and
  `aria-valuemax` are omitted (their absence signals indeterminate to AT).
- **Accessible name:** resolved from (in priority order): `aria-labelledby`,
  `aria-label`, `label` attribute. Name is required; missing name emits a warning.
- **Live region:** if the host needs updates announced (e.g., "Upload 50% complete"),
  they wrap `<mj-progress>` in an `aria-live="polite"` region or supply
  `value-text` inside one. The component itself does not own a live region to
  avoid over-announcement on every value tick.
- **Color:** progress fill uses a brand token; the track provides a visible
  background; fill color meets 3:1 contrast against the track.
- **Reduced motion:** indeterminate animations replaced with low-motion
  equivalents when `prefers-reduced-motion: reduce` matches.

## 14. Form participation

N/A — `<mj-progress>` is a display-only component.

## 15. Internationalization & RTL

- `value-text` is fully host-controlled and may include locale-formatted numbers
  (e.g., `Intl.NumberFormat` for percentage).
- In RTL, the bar fill grows from right-to-left; achieved via logical CSS
  (`inline-start` origin) and `transform-origin` adjustment.
- The indeterminate bar animation direction reverses in RTL so the sweep appears
  to travel in the natural reading direction.
- The ring animation direction is not LTR/RTL-sensitive; no change needed.

## 16. Progressive enhancement / SSR

Server-renders as:
```html
<div role="progressbar" aria-valuenow="42" aria-valuemin="0" aria-valuemax="100"
     aria-valuetext="42%" aria-label="Uploading file">
  <div class="mj-progress-fill" style="width:42%"></div>
</div>
```
Before JS loads, the user sees a styled bar at the correct position. On upgrade,
the custom element adopts this markup into its shadow root, replacing the
inline style with its reactive property system.

## 17. Dependencies

- **Registry + base element helper** (§6) — lifecycle and attribute reflection.
- **Design-token stylesheet** (§6) — fill/track color tokens, spacing, motion.
- **No other components required.**

## 18. Edge cases & error handling

- **`value > max`:** clamped to `max`; a console warning is emitted.
- **`value < 0`:** clamped to `0`.
- **`max <= 0`:** defaults to `100`; a console error is emitted.
- **`indeterminate` set while `value` has a non-zero value:** the stored value is
  preserved and restored when `indeterminate` is removed.
- **No accessible name:** console warning; `progressbar` without a name fails
  WCAG 4.1.2; hosts must supply one.
- **Ring variant with a very long center slot text:** text overflows the SVG
  bounding box; the center slot is `overflow: hidden` by default.
- **Rapid value updates:** CSS transitions handle visual smoothing; updating
  `value` faster than the transition duration queues transitions cleanly via
  the browser compositor.

## 19. Acceptance criteria

- [ ] Bar variant renders at `value/max * 100%` width in determinate mode.
- [ ] Ring variant renders correct `stroke-dashoffset` in determinate mode.
- [ ] Indeterminate mode removes ARIA value attributes and starts animation.
- [ ] `aria-valuenow`, `aria-valuemin`, `aria-valuemax`, `aria-valuetext` are
      correct in determinate mode.
- [ ] `aria-label` is set from the `label` attribute.
- [ ] `mj-progress-complete` fires when `value` reaches `max`.
- [ ] `mj-progress-change` fires on every value/max change.
- [ ] Indeterminate animation is replaced with reduced-motion equivalent when
      `prefers-reduced-motion: reduce` matches.
- [ ] RTL bar fill grows from the correct origin.
- [ ] `value > max` clamps to `max` with a console warning.
- [ ] Missing accessible name emits a console warning.
- [ ] No hard-coded colors; all values resolve from design tokens.
- [ ] Passes automated axe accessibility checks with no violations.

## 20. Open questions

- Should `<mj-progress>` emit value-change events throttled to avoid
  firing hundreds of times during a streaming upload, or leave throttling
  to the host?
- Is a `buffer` attribute needed for video-style buffered/loaded dual-fill bars?
- Should the `complete` state apply a visual flourish (icon swap, color shift)
  by default, or leave that entirely to host styling?
