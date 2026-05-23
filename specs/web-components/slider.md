# Slider Spec

- **Tag:** `<mj-slider>`
- **Class / file:** `Slider` / `slider.js`
- **Category:** Text & data-entry controls
- **Primary or Variant:** Primary
- **Synonyms covered:** Range slider, Dual-thumb range slider, Range input
- **Phase:** P0
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-slider>` is a single or dual-thumb range control for selecting a numeric
value or a [min, max] value range. It wraps the WAI-ARIA `slider` pattern,
provides tick mark and value-label rendering, and participates in form submission
as a single value (single-thumb) or two separate values (dual-thumb). It replaces
the native `<input type="range">` with a design-system-consistent, accessible
implementation.

## 2. When to use / when not to use
**Use** for continuous or stepped numeric selection where the range boundaries are
meaningful context (volume, brightness, price filter, date range). **Do not use**
for precise numeric entry where typing is more appropriate — prefer
`<mj-number-field>`. **Do not use** when the value must be incremented one step
at a time with hold-to-repeat — prefer `<mj-number-field>` spinner mode.

## 3. Anatomy
- **Track** (`part="track"`) — the horizontal (or vertical) rail.
- **Fill** (`part="fill"`) — colored portion of the track indicating the selected range.
- **Thumb** (`part="thumb"`) — draggable handle; one (single) or two (range).
- **Thumb A** (`part="thumb-a"`) — the lower-value thumb in range mode.
- **Thumb B** (`part="thumb-b"`) — the upper-value thumb in range mode.
- **Value label** (`part="value-label"`) — floating bubble showing the current value near the thumb.
- **Tick marks** (`part="ticks"`) — optional step markers along the track.
- **Tick label** (`part="tick-label"`) — optional text labels at specific tick positions.
- **Label** (`part="label"`), **Help text** (`part="help"`), **Error message** (`part="error"`).

## 4. Variants & modes
| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Single thumb | — (default) | One thumb; one value submitted |
| Range (dual thumb) | `range` | Two thumbs; two values (start and end) submitted |
| Vertical | `orientation="vertical"` | Track is vertical; Up/Down arrows adjust value |
| With tick marks | `ticks` | Tick marks rendered at each step |
| With tick labels | `tick-labels` property | Labeled ticks at specified positions |
| With value label | `show-value-label` | Value bubble shown above thumb |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `name` | string | `""` | yes | Name for single-thumb form submission |
| `name-start` | string | `""` | yes | Name for the lower value in range mode |
| `name-end` | string | `""` | yes | Name for the upper value in range mode |
| `value` | string | `""` | yes | Current value (single) or lower value (range) |
| `value-end` | string | `""` | yes | Upper value in range mode |
| `min` | number | `0` | yes | Minimum value |
| `max` | number | `100` | yes | Maximum value |
| `step` | number | `1` | yes | Step granularity |
| `range` | boolean | `false` | yes | Enable dual-thumb range mode |
| `orientation` | `"horizontal"\|"vertical"` | `"horizontal"` | yes | Slider orientation |
| `disabled` | boolean | `false` | yes | Disables the slider |
| `readonly` | boolean | `false` | yes | Prevents value changes |
| `required` | boolean | `false` | yes | Field is required (non-default value) |
| `ticks` | boolean | `false` | yes | Show tick marks at each step position |
| `show-value-label` | boolean | `false` | yes | Show value bubble above the thumb during drag |
| `label` | string | `""` | yes | Visible label above the slider |
| `help-text` | string | `""` | yes | Hint text below the slider |
| `error-message` | string | `""` | yes | Override validation message |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `valueAsNumber` | number | Current value as a number (single mode) |
| `valueStartAsNumber` | number | Lower value as a number (range mode) |
| `valueEndAsNumber` | number | Upper value as a number (range mode) |
| `tickLabels` | `Array<{ value: number, label: string }>` | Custom labels at specific tick positions |
| `validity` | `ValidityState` | Delegates to `ElementInternals.validity` |
| `validationMessage` | string | Delegates to `ElementInternals.validationMessage` |

## 7. Slots
| Slot | Description |
|------|-------------|
| `start-label` | Label at the start (min) end of the track |
| `end-label` | Label at the end (max) end of the track |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-input` | `{ value: number, valueEnd?: number }` | yes | no | Fires continuously during drag |
| `mj-change` | `{ value: number, valueEnd?: number }` | yes | no | Fires when the thumb is released or a key sets a new value |
| `mj-invalid` | `{ validationMessage: string }` | yes | no | Fires when reportValidity finds the field invalid |

## 9. CSS parts & custom properties
**Parts:** `track`, `fill`, `thumb`, `thumb-a`, `thumb-b`, `value-label`, `ticks`, `tick-label`, `label`, `help`, `error`.

| Custom property | Default token | Description |
|-----------------|---------------|-------------|
| `--mj-slider-track-height` | `4px` | Track thickness (horizontal) |
| `--mj-slider-track-bg` | `--mj-color-surface-subtle` | Unfilled track color |
| `--mj-slider-fill-bg` | `--mj-color-primary-500` | Filled portion color |
| `--mj-slider-thumb-size` | `20px` | Thumb diameter |
| `--mj-slider-thumb-bg` | `--mj-color-surface-default` | Thumb background |
| `--mj-slider-thumb-border` | `--mj-color-primary-500` | Thumb border color |
| `--mj-slider-thumb-shadow-focus` | `--mj-shadow-focus-ring` | Thumb focus ring |
| `--mj-slider-tick-size` | `4px` | Tick mark diameter |
| `--mj-slider-tick-color` | `--mj-color-border-subtle` | Tick color |
| `--mj-slider-value-label-bg` | `--mj-color-surface-inverse` | Value bubble background |
| `--mj-slider-value-label-color` | `--mj-color-text-inverse` | Value bubble text |

## 10. States
| State | Visual effect | ARIA effect |
|-------|---------------|-------------|
| Default | Thumb at rest; fill indicates current value | `aria-valuenow`, `aria-valuemin`, `aria-valuemax`, `aria-valuetext` |
| Hover | Thumb scales slightly | — |
| Focus-visible | Focus ring on thumb | Focus ring via `--mj-slider-thumb-shadow-focus` |
| Dragging | Value label shown (if `show-value-label`); thumb moves | `aria-valuenow` updates |
| Disabled | Track and thumb greyed; no interaction | `aria-disabled="true"` |
| Readonly | Thumb visible but not draggable; no keyboard change | `aria-readonly="true"` |
| Invalid | Error message shown | `aria-invalid="true"` (on `aria-group` container) |

## 11. Behavior & interactions
- Pointer down on the thumb initiates a drag. `pointermove` updates the value and
  fires `mj-input`. `pointerup` fires `mj-change`.
- Pointer down on the track (not the thumb) moves the active thumb to the nearest
  step position and fires `mj-change`.
- In range mode, when two thumbs overlap, the thumb being dragged passes through
  the other. The component ensures `value <= value-end` at all times.
- Ticks are rendered as decorative elements along the track at step intervals.
  When ticks are more than 50 along the track, they are hidden to avoid visual
  clutter (with a console warning to use a coarser `step`).
- The value label shows the formatted `Intl.NumberFormat` value; it is only
  visible during drag and keyboard changes when `show-value-label` is true.
- `prefers-reduced-motion`: thumb transition and value-label fade are disabled.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Arrow Right` / `Arrow Up` | Increase value by `step`; clamp to `max` |
| `Arrow Left` / `Arrow Down` | Decrease value by `step`; clamp to `min` |
| `Page Up` | Increase value by `step × 10`; clamp to `max` |
| `Page Down` | Decrease value by `step × 10`; clamp to `min` |
| `Home` | Set value to `min` |
| `End` | Set value to `max` |
| `Tab` | Move focus between thumb-a and thumb-b (range mode); then out of component |
| `Shift+Tab` | Reverse focus |

## 13. Accessibility
- Each thumb has `role="slider"` with `aria-valuenow`, `aria-valuemin`,
  `aria-valuemax`, and `aria-valuetext` (locale-formatted value string, e.g.,
  "$50" for currency contexts).
- In single mode, the thumb also has `aria-label` from the `label` attribute.
- In range mode, thumb-a has `aria-label="Minimum {label}"` and thumb-b has
  `aria-label="Maximum {label}"` (localizable).
- `aria-orientation` is set to `"horizontal"` or `"vertical"`.
- Tick labels, start/end slot labels, and help text are linked via
  `aria-describedby`.
- Value changes during keyboard interaction fire `mj-change` immediately (not
  debounced) so screen readers announce the current value via `aria-valuenow`.
- The track itself is `aria-hidden="true"`; the fill is decorative.

## 14. Form participation
- `formAssociated = true`; uses `ElementInternals`.
- Single mode: submits `name`/`value` (the numeric string without locale formatting).
- Range mode: submits `name-start`/`value` and `name-end`/`value-end` as two
  separate `FormData` entries.
- `required` validation: `valueMissing` when `value` equals `min` (i.e., the
  user has not moved from the default start position) — only when `required` is
  explicitly set.
- Form reset restores `value` and `value-end` to the `value` and `value-end`
  attribute values (or `min` and `max` respectively if absent).
- `checkValidity()` and `reportValidity()` delegate to `ElementInternals`.

## 15. Internationalization & RTL
- `aria-valuetext` is formatted via `Intl.NumberFormat` using the document locale.
- `tick-labels` strings are passed through directly (host responsibility for locale).
- In RTL, the track visual direction flips: left side is max, right side is min.
  Arrow Right still increases value; this matches WAI-ARIA guidance for RTL sliders.
- `orientation="vertical"`: Arrow Up increases, Arrow Down decreases regardless
  of RTL.

## 16. Progressive enhancement / SSR
- Server renders `<input type="range" min max step value>` with a visible label.
  Native range input is functional without script.
- On upgrade, the component reads `min`, `max`, `step`, and `value` from the
  existing input and renders the custom track, thumb, and ticks.

## 17. Dependencies
- **Registry + base element helper** (§6).
- **Design-token stylesheet** (§6).
- **Form-association helper** (§6).
- **Localization/formatting hook** (§6) — `aria-valuetext` formatting.

## 18. Edge cases & error handling
- `min >= max`: console error; slider renders at 0% fill; value clamped to `min`.
- `step` larger than `(max - min)`: step is clamped to `(max - min)`; only two
  positions are accessible (min and max).
- `value` outside `[min, max]` set via attribute: clamped on upgrade.
- Range mode: `value > value-end` set via attributes: values are swapped silently.
- Track width too narrow for all ticks (>100 ticks): ticks are hidden; console
  warning emitted.
- Pointer drag released outside the browser window: `pointerup` is captured on
  `window` so the drag ends correctly.

## 19. Acceptance criteria
- [ ] Single-thumb: Arrow keys change value by `step`; Page Up/Down by `step×10`; Home/End to extremes.
- [ ] Range mode: Tab moves focus between thumbs; each thumb independently adjustable.
- [ ] `aria-valuenow`, `aria-valuemin`, `aria-valuemax`, `aria-valuetext` correct on each thumb.
- [ ] Track click moves closest thumb (or active thumb) to nearest step position.
- [ ] `mj-input` fires continuously during drag; `mj-change` fires on pointer release.
- [ ] Value label shows during drag when `show-value-label` is set.
- [ ] Tick marks rendered at correct step intervals; hidden when count > 50.
- [ ] Disabled: no interaction; `aria-disabled` set.
- [ ] Form submit includes correct values; form reset restores initial values.
- [ ] RTL: track direction flips; Arrow Right still increases value.
- [ ] axe audit passes with zero violations in single and range modes.

## 20. Open questions
- Should `step="any"` (continuous movement) be supported for use cases like color lightness?
- Should the value label be persistent (always visible) as a separate mode, not just during drag?
- Should range mode enforce a minimum gap (`min-range`) between the two thumb values?
