# Gauge Spec

- **Tag:** `<mj-gauge>`
- **Class / file:** `MjGauge` / `mjgauge.js`
- **Category:** Media & visualization
- **Primary or Variant:** Primary
- **Synonyms covered:** Meter, Single-value gauge
- **Phase:** P3
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-gauge>` displays a single numeric value within a defined range, rendered as
an arc or linear meter. It uses the semantic `meter` ARIA role, exposes
configurable threshold bands (low/medium/high/critical), and ensures threshold
regions are distinguished by shape or pattern — not color alone. A text value is
always visible alongside the visual indicator.

## 2. When to use / when not to use

**Use** for KPI dashboards, resource utilization displays (CPU, memory, storage),
and any single-value scalar metric that benefits from a visual range indicator.

**Do not use** for progress toward completion of a task (use `<mj-progress>`
instead), for multi-value comparisons (use `<mj-chart type="bar">`), or for
compact inline trends (use `<mj-sparkline>`).

## 3. Anatomy

- **Container** (`::part(container)`) — outermost element; holds the track, fill,
  and all label sub-parts.
- **Track** (`::part(track)`) — the full arc or linear bar representing the entire
  range; renders threshold band segments within it.
- **Fill** (`::part(fill)`) — the colored+patterned segment showing the current
  value position.
- **Needle** (`::part(needle)`) — optional pointer on arc gauges indicating the
  exact value position.
- **Value label** (`::part(value-label)`) — visible numeric text with unit.
- **Min label** (`::part(min-label)`) — optional label at the minimum end of the track.
- **Max label** (`::part(max-label)`) — optional label at the maximum end of the track.
- **Threshold markers** (`::part(threshold-markers)`) — tick marks or segment
  boundaries rendered on the track at threshold values.
- **Title** (`::part(title)`) — optional label above the gauge identifying the metric.

## 4. Variants & modes

| Variant / mode | Attribute value | Behavior |
|----------------|----------------|----------|
| Arc gauge | `shape="arc"` (default) | Semi-circular or full-circle arc rendered via SVG |
| Linear gauge | `shape="linear"` | Horizontal bar meter |
| With needle | `show-needle` (boolean, arc only) | SVG needle pointer overlaid on the arc |
| With threshold bands | `thresholds` property set | Track divided into visually distinct colored+patterned bands |
| Read-only | (always) | Gauge is display-only; no interactive value editing |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `value` | `number` | `0` | Yes | Current value to display |
| `min` | `number` | `0` | Yes | Minimum of the range |
| `max` | `number` | `100` | Yes | Maximum of the range |
| `low` | `number` | `""` | Yes | Upper boundary of the "low" zone (maps to `<meter low>`) |
| `high` | `number` | `""` | Yes | Lower boundary of the "high" zone (maps to `<meter high>`) |
| `optimum` | `number` | `""` | Yes | Optimum value hint (maps to `<meter optimum>`; drives color selection) |
| `unit` | `string` | `""` | Yes | Unit string appended to the value label (e.g. `"%"`, `"GB"`) |
| `title` | `string` | `""` | Yes | Metric name shown above the gauge |
| `shape` | `"arc"\|"linear"` | `"arc"` | Yes | Visual shape |
| `show-needle` | `boolean` | `false` | Yes | Show a needle pointer (arc only) |
| `show-min-max` | `boolean` | `true` | Yes | Show min/max labels at track ends |
| `arc-degrees` | `number` | `240` | Yes | Arc span in degrees (arc shape only); common values: 180, 240, 360 |
| `animated` | `boolean` | `true` | Yes | Animate fill transitions; suppressed under `prefers-reduced-motion` |
| `precision` | `number` | `0` | Yes | Decimal places for the formatted value label |
| `locale` | `string` | `""` | Yes | BCP 47 locale for number formatting; defaults to document locale |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `thresholds` | `GaugeThreshold[]` | Array of `{ value: number, label: string, color: string, pattern: string }` objects defining band boundaries and their visual encoding |
| `formattedValue` | `string` | Read-only; the localized value string as displayed in the label |

## 7. Slots

| Slot | Description |
|------|-------------|
| `value-label` | Custom value display replacing the auto-formatted label |
| `title` | Rich HTML title replacing the `title` attribute |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-gauge-value-change` | `{ value: number, previousValue: number, threshold: string \| null }` | Yes | No | Fired when the `value` attribute/property changes; `threshold` is the label of the band the new value falls within, or `null` |

## 9. CSS parts & custom properties

**Parts**
- `::part(container)`, `::part(track)`, `::part(fill)`
- `::part(needle)`, `::part(value-label)`, `::part(min-label)`, `::part(max-label)`
- `::part(threshold-markers)`, `::part(title)`

**Custom properties**
| Property | Default | Description |
|----------|---------|-------------|
| `--mj-gauge-size` | `8rem` | Diameter (arc) or width (linear) of the gauge |
| `--mj-gauge-track-width` | `0.75rem` | Stroke width of the arc or height of the linear bar |
| `--mj-gauge-track-color` | `var(--mj-color-surface-3)` | Unfilled track color |
| `--mj-gauge-fill-color` | `var(--mj-color-primary)` | Fill color for the value region (overridden by threshold band color) |
| `--mj-gauge-fill-pattern` | `none` | Fill pattern (overridden by threshold band pattern) |
| `--mj-gauge-needle-color` | `var(--mj-color-text-primary)` | Needle color |
| `--mj-gauge-value-font-size` | `var(--mj-font-size-xl)` | Value label font size |
| `--mj-gauge-title-font-size` | `var(--mj-font-size-sm)` | Title font size |
| `--mj-gauge-title-color` | `var(--mj-color-text-subtle)` | Title text color |
| `--mj-gauge-transition-duration` | `var(--mj-motion-standard)` | Fill animation duration |

## 10. States

- **default** — static value displayed; fill shows current value position.
- **animated** — `value` changed; fill animates from previous to new position;
  suppressed when `prefers-reduced-motion: reduce` or `animated="false"`.
- **threshold-low** — value within the low band; low-band color and pattern applied.
- **threshold-optimum** — value within the optimum/normal band.
- **threshold-high** — value within the high band.
- **threshold-critical** — value at or above the highest threshold.
- **overflow** — `value > max`: fill clamps at 100%; value label shows actual value.
- **underflow** — `value < min`: fill clamps at 0%; value label shows actual value.

## 11. Behavior & interactions

The component renders its visual gauge as an inline SVG (arc) or a styled `<div>`
(linear). Arc geometry is computed from `arc-degrees`, `min`, `max`, and `value`.

When `value` changes, the fill element is animated via a CSS transition on the
`stroke-dashoffset` (arc) or `width` (linear). The transition is removed when
`prefers-reduced-motion: reduce` is active or `animated="false"`.

Threshold bands are rendered as contiguous segments on the track, each with its
own color token and a distinct SVG pattern fill (stripes, dots, cross-hatch) so
they are distinguishable without color vision. The fill element adopts the color
and pattern of the band that the current `value` falls within.

A visually hidden native `<meter>` element (with `min`, `max`, `value`, `low`,
`high`, `optimum` attributes) sits inside the shadow DOM to provide native
semantics; the visual gauge is `aria-hidden="true"`.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| None | The gauge is a read-only display component; no keyboard interaction required |

(When the gauge is embedded in a focusable context such as a dashboard card, the
host element manages focus. The gauge's accessible value is exposed via the
`<meter>` role.)

## 13. Accessibility

- A native `<meter>` element is present in the shadow DOM with `min`, `max`,
  `value`, `low`, `high`, and `optimum` attributes mirroring the component
  attributes. This provides the `meter` role and correct `aria-valuenow`,
  `aria-valuemin`, `aria-valuemax` to assistive technology automatically.
- `aria-label` on the `<meter>` is set to the `title` attribute value, or to a
  localized default ("Gauge") if `title` is absent.
- The visual SVG/div gauge is `aria-hidden="true"`.
- The value label text is visually visible and is not the sole representation;
  the `<meter>` provides the semantic value independently.
- Threshold bands are never distinguished by color alone: each band uses a
  distinct SVG pattern in addition to a color token.
- In high-contrast / forced-colors mode, pattern fills use `currentColor` and
  `transparent` to remain visible.

## 14. Form participation

N/A — `<mj-gauge>` is a display component with no form value.

## 15. Internationalization & RTL

- The `formattedValue` property and the displayed value label use `Intl.NumberFormat`
  with the `locale` attribute (or document locale) and the `precision` attribute
  for fraction digits.
- The `unit` string is appended as-is after the formatted number; it is the host's
  responsibility to localize it.
- In RTL mode, the linear gauge bar fills from the right end; the arc gauge is
  unaffected (radial).
- Min/max labels swap visual positions in RTL for the linear variant.

## 16. Progressive enhancement / SSR

The server renders a native `<meter min="0" max="100" value="73">73%</meter>`
inside `<mj-gauge>`. Without scripting the native meter is displayed by the browser.
On upgrade the component wraps the native meter in the shadow DOM structure and
applies the visual gauge; the native meter's values are read and used as the
initial attribute values if the component attributes are not explicitly set.

## 17. Dependencies

- **Registry + base element helper** (§6) — lifecycle, attribute reflection.
- **Design-token stylesheet** (§6) — color, pattern, and motion tokens.
- **Localization hook** (§6) — value label formatting and ARIA label strings.

## 18. Edge cases & error handling

- `value` outside `[min, max]`: clamped for visual rendering; actual value preserved
  in the `<meter>` and the value label.
- `min >= max`: logs a console error; gauge renders empty track with value label.
- `thresholds` array is unsorted: sorted by `value` ascending internally; a
  console warning is logged.
- `arc-degrees` outside `[90, 360]`: clamped to the valid range with a warning.
- No `title` attribute: ARIA label defaults to "Gauge" (localized); a console
  info message recommends providing a descriptive title.
- `animated` with rapid value changes: only the latest `value` is used as the
  animation target; intermediate values are skipped.

## 19. Acceptance criteria

- [ ] Arc gauge renders correct SVG geometry for arbitrary `arc-degrees` values.
- [ ] Linear gauge renders correct fill width for `value` within `[min, max]`.
- [ ] Threshold bands render distinct colors AND patterns (no color-only encoding).
- [ ] `mj-gauge-value-change` fires with correct `threshold` label on value change.
- [ ] Fill animation runs on value change; suppressed under `prefers-reduced-motion`.
- [ ] Native `<meter>` is present in shadow DOM with correct `min`/`max`/`value`/`low`/`high`/`optimum`.
- [ ] `aria-label` on `<meter>` reflects `title` attribute.
- [ ] Visual gauge is `aria-hidden="true"`.
- [ ] Value label uses `Intl.NumberFormat` with correct `locale` and `precision`.
- [ ] Value clamped for display when outside `[min, max]`; label shows actual value.
- [ ] RTL linear gauge fills from the end edge.
- [ ] Forced-colors mode maintains pattern visibility.
- [ ] Automated accessibility checks pass with no violations.

## 20. Open questions

- Should animated needle movement use a CSS transition or a `requestAnimationFrame`
  loop for smoother arcing?
- Should the `thresholds` property accept a simplified string attribute format
  (e.g. `thresholds="50:low,80:high,95:critical"`) for SSR convenience?
