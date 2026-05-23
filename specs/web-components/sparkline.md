# Sparkline Spec

- **Tag:** `<mj-sparkline>`
- **Class / file:** `MjSparkline` / `mjsparkline.js`
- **Category:** Media & visualization
- **Primary or Variant:** Primary
- **Synonyms covered:** Inline trend chart
- **Phase:** P3
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-sparkline>` is a compact, word-sized inline chart that communicates a trend
alongside a numeric summary value. It renders a line, bar, or win/loss series
directly in SVG within a constrained bounding box. Because it is decorative or
supplementary to its paired text value, it is either `aria-hidden` (when the
paired text provides the full meaning) or given a concise description.

## 2. When to use / when not to use

**Use** inside table cells, stat cards, and list rows where a trend shape is
informative but a full chart would be too large. Always pair the sparkline with
a visible text value (e.g. "↑ $42.3K") that conveys the same information.

**Do not use** for standalone charts where axis labels, a legend, or a data table
are needed (use `<mj-chart>` instead). Do not use without a paired text value;
the sparkline alone never constitutes the sole data representation.

## 3. Anatomy

- **Container** (`::part(container)`) — inline-block wrapper that constrains width
  and height; aligns with surrounding text baseline.
- **SVG canvas** (`::part(svg)`) — the SVG element; `aria-hidden="true"` when the
  paired text is sufficient; otherwise carries `role="img"` and `aria-label`.
- **Line/area path** (`::part(line)`) — SVG `<path>` for line and area sparklines.
- **Area fill** (`::part(area)`) — SVG `<path>` for the filled region below the
  line in area mode.
- **Bars** (`::part(bar)`) — SVG `<rect>` elements for bar sparklines.
- **Win/loss columns** (`::part(win-loss-col)`) — fixed-height positive/negative
  `<rect>` elements.
- **End dot** (`::part(end-dot)`) — optional circle at the last data point.
- **Reference line** (`::part(reference-line)`) — optional horizontal SVG line at
  a specified value (e.g. zero or a target).

## 4. Variants & modes

| Variant / mode | Attribute value | Behavior |
|----------------|----------------|----------|
| Line | `type="line"` (default) | Continuous polyline through data points |
| Area | `type="area"` | Line with filled area below (or above zero for negative values) |
| Bar | `type="bar"` | Vertical bar per data point; bars colored by positive/negative |
| Win/loss | `type="win-loss"` | Fixed-height positive/negative column per data point |
| With end dot | `show-end-dot` (boolean) | Circle marker at the last data point |
| With reference | `reference-value` attribute set | Horizontal rule at the given value |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `type` | `"line"\|"area"\|"bar"\|"win-loss"` | `"line"` | Yes | Sparkline chart type |
| `values` | `string` | `""` | Yes | Comma-separated numeric data values (e.g. `"10,24,18,30,22"`) |
| `width` | `number` | `80` | Yes | SVG width in px |
| `height` | `number` | `24` | Yes | SVG height in px |
| `show-end-dot` | `boolean` | `false` | Yes | Render a dot at the last data point |
| `reference-value` | `number` | `""` | Yes | Y value of a horizontal reference line |
| `curve` | `"linear"\|"monotone"` | `"linear"` | Yes | Line interpolation (line/area only) |
| `label` | `string` | `""` | Yes | Accessible description; if set, SVG gets `role="img"` + `aria-label`; if empty, SVG is `aria-hidden` |
| `locale` | `string` | `""` | Yes | BCP 47 locale for value formatting |
| `animated` | `boolean` | `false` | Yes | Animate path drawing on first render; suppressed under `prefers-reduced-motion` |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `parsedValues` | `number[]` | Read-only; the `values` attribute parsed to a numeric array; `NaN` entries are gap points |
| `min` | `number` | Read-only; minimum value in `parsedValues` (ignoring `NaN`) |
| `max` | `number` | Read-only; maximum value in `parsedValues` (ignoring `NaN`) |
| `last` | `number` | Read-only; last non-NaN value in `parsedValues` |

## 7. Slots

| Slot | Description |
|------|-------------|
| `(default)` | Fallback text content shown before upgrade and used as the accessible alternative when no `label` attribute is set and JS is absent |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-sparkline-render` | `{ type: string, pointCount: number }` | Yes | No | Fired after SVG is drawn or re-drawn |

## 9. CSS parts & custom properties

**Parts**
- `::part(container)`, `::part(svg)`, `::part(line)`, `::part(area)`
- `::part(bar)`, `::part(win-loss-col)`, `::part(end-dot)`, `::part(reference-line)`

**Custom properties**
| Property | Default | Description |
|----------|---------|-------------|
| `--mj-sparkline-color` | `var(--mj-color-primary)` | Line, area, and positive bar color |
| `--mj-sparkline-negative-color` | `var(--mj-color-danger)` | Color for negative bars/win-loss columns |
| `--mj-sparkline-area-opacity` | `0.2` | Opacity of area fill |
| `--mj-sparkline-stroke-width` | `1.5px` | Line stroke width |
| `--mj-sparkline-end-dot-radius` | `3px` | End dot radius |
| `--mj-sparkline-reference-color` | `var(--mj-color-border)` | Reference line color |
| `--mj-sparkline-reference-dash` | `3 2` | SVG stroke-dasharray for reference line |
| `--mj-sparkline-bar-gap` | `1px` | Gap between bar columns |
| `--mj-sparkline-transition` | `var(--mj-motion-standard)` | Animation duration for path transitions |

## 10. States

- **default** — SVG rendered from `parsedValues`.
- **empty** — `parsedValues` has no valid (non-NaN) entries; SVG is blank;
  container shows a flat line at mid-height.
- **animated** — path is drawn progressively on first render via SVG
  `stroke-dashoffset`; suppressed when `prefers-reduced-motion: reduce`.
- **updating** — `values` attribute changed; SVG re-renders with optional
  transition on the path `d` attribute.

## 11. Behavior & interactions

The component parses the `values` attribute as a comma-separated list of numbers.
Non-numeric tokens become `NaN` and are treated as gap points (line/area have no
segment drawn across a gap; bars skip the column).

SVG path coordinates are computed by mapping the value domain `[min, max]` to the
pixel range `[height - padding, padding]` (Y inverted) and the index domain
`[0, n-1]` to `[0, width]`. For area and bar variants, values below `reference-value`
(or zero if not set) are drawn downward from the reference axis.

For `type="bar"` and `type="win-loss"`, positive values use `--mj-sparkline-color`
and negative values use `--mj-sparkline-negative-color`. Bars are also visually
distinct via height direction (above/below the zero axis) so the distinction is
never color-only.

The sparkline is self-contained; it does not use an external adapter. The SVG
computation is lightweight and synchronous.

When `animated="true"` and `prefers-reduced-motion` is not active, the line path
is drawn using a `stroke-dasharray`/`stroke-dashoffset` animation on mount.

The component listens for `values` attribute changes and re-computes the SVG on
every change.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| None | The sparkline is a display component; no keyboard interaction |

(The sparkline is not individually focusable unless placed inside a focusable
host, such as a table cell with interactive row selection.)

## 13. Accessibility

- When `label` attribute is provided (e.g. `label="Revenue trend: up 12% over 6 months"`),
  the SVG has `role="img"` and `aria-label` equal to that string.
- When `label` is absent, the SVG has `aria-hidden="true"` and the component
  relies on adjacent visible text (e.g. a `<span>` next to `<mj-sparkline>`) to
  communicate the data meaning.
- The default slot content is the no-JS fallback text; it is also used as the
  screen reader visible text if the host does not set `label` (wrapped in a
  visually-hidden span in shadow DOM).
- Positive and negative values in bar/win-loss mode are differentiated by
  direction (above vs. below baseline) and by color — two distinct encodings,
  not color alone.
- Trend direction for line/area is conveyed via the `label` attribute text, not
  by the visual slope alone.

## 14. Form participation

N/A — `<mj-sparkline>` is a display component with no form value.

## 15. Internationalization & RTL

- The `label` attribute text is authored by the host and should be localized by
  the host application.
- `parsedValues` is locale-agnostic (numeric only); the `locale` attribute is used
  only if the component needs to format numbers in a future tooltip feature.
- In RTL mode, the X-axis renders right-to-left (first value at the right edge,
  last value at the left edge) via a `transform="scale(-1,1)"` on the SVG content
  group. The `show-end-dot` dot remains at the visually last (leftmost) point.

## 16. Progressive enhancement / SSR

The server renders a text alternative inside `<mj-sparkline>`: e.g.
`<mj-sparkline values="...">↑ 12% over 6 months</mj-sparkline>`. Without
scripting the text content is displayed inline. On upgrade the component renders
the SVG and moves the text into a visually-hidden span that serves as the
accessible description if `label` is not set.

## 17. Dependencies

- **Registry + base element helper** (§6) — lifecycle, attribute reflection.
- **Design-token stylesheet** (§6) — color and motion tokens.
- **Localization hook** (§6) — future tooltip value formatting.

## 18. Edge cases & error handling

- All values are identical: flat line rendered at mid-height; no division-by-zero
  (min === max clamps the Y scale to a center line).
- Single data point: renders as a dot at the center for line/area; a single bar
  for bar type.
- `NaN` or non-numeric tokens in `values`: treated as gap points; adjacent valid
  segments are still rendered.
- More than 200 data points: rendered at 1 px per point; width may need to be
  increased by the host for legibility; no virtualization needed at this scale.
- `width` or `height` is zero: SVG renders as zero-size; no error thrown.
- `animated` with rapid `values` updates: previous animation is cancelled;
  new animation starts from the current rendered state.

## 19. Acceptance criteria

- [ ] `type="line"` renders a continuous polyline through all non-NaN values.
- [ ] `type="area"` renders a filled area below the line (and above for negatives).
- [ ] `type="bar"` renders positive bars above baseline and negative bars below; colors differ.
- [ ] `type="win-loss"` renders fixed-height up/down columns.
- [ ] `show-end-dot` renders a circle at the last valid data point.
- [ ] `reference-value` renders a dashed horizontal rule at the correct Y position.
- [ ] All-identical values renders a flat center line without errors.
- [ ] NaN tokens produce gaps in line/area; skipped bars in bar/win-loss.
- [ ] `label` present: SVG has `role="img"` + `aria-label`.
- [ ] `label` absent: SVG has `aria-hidden="true"`.
- [ ] RTL mode mirrors the X-axis direction.
- [ ] Animation runs on first render; suppressed under `prefers-reduced-motion`.
- [ ] `mj-sparkline-render` fires after each draw.
- [ ] Automated accessibility checks pass with no violations.

## 20. Open questions

- Should `<mj-sparkline>` support an optional hover/focus tooltip showing exact
  values at each data point? This would require pointer and keyboard interaction
  and a description in this spec.
- Should `curve="monotone"` smoothing be computed in-component or always require
  an external utility (e.g. a tiny path-smoothing library)?
