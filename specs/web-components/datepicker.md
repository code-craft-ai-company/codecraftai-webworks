# Date Picker Spec

- **Tag:** `<mj-date-picker>`
- **Class / file:** `MjDatePicker` / `mjdatepicker.js`
- **Category:** Selection & dropdown-style controls
- **Primary or Variant:** Primary
- **Synonyms covered:** Time picker, Date-time picker, Range picker, Calendar picker
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-date-picker>` is a unified date, time, datetime, and date-range picker. A single `mode` attribute selects the active variant. The calendar grid pattern (WAI-ARIA APG) is used for date navigation. Locale-aware formatting and a text-entry fallback ensure the control is accessible and usable globally.

## 2. When to use / when not to use
**Use `mode="date"`** for selecting a single calendar date. **Use `mode="time"`** for selecting a clock time. **Use `mode="datetime"`** for a combined date and time. **Use `mode="range"`** for selecting a start and end date. **Do not use** for relative durations — use a number field with a unit selector. **Do not use** when a free-text date string is acceptable — use a plain text field with format hint.

## 3. Anatomy
- **Input** (`part="input"`) — formatted text display of the current value; opens the popup on click.
- **Calendar trigger** (`part="calendar-trigger"`) — icon button to open the calendar popup.
- **Clear button** (`part="clear"`) — removes the current value when `clearable`.
- **Popup** (`part="popup"`) — positioned overlay containing the calendar and/or time panel.
- **Calendar header** (`part="calendar-header"`) — month/year navigation controls.
- **Prev button** (`part="prev"`) — navigate to the previous month.
- **Next button** (`part="next"`) — navigate to the next month.
- **Month selector** (`part="month-selector"`) — dropdown for month; converts header to a month grid.
- **Year selector** (`part="year-selector"`) — dropdown for year.
- **Day grid** (`part="day-grid"`) — `role="grid"` calendar table.
- **Day cell** (`part="day-cell"`) — `role="gridcell"` for each day (`role="button"` inside).
- **Week row** (`part="week-row"`) — `role="row"` for each week.
- **Week header** (`part="week-header"`) — abbreviated day name column headers.
- **Time panel** (`part="time-panel"`) — hour/minute/second/AM-PM spinners (datetime/time modes).
- **Range start** (`part="range-start"`) — highlighted start date cell (range mode).
- **Range end** (`part="range-end"`) — highlighted end date cell (range mode).
- **Range fill** (`part="range-fill"`) — cells between start and end highlighted (range mode).

## 4. Variants & modes
| Variant / mode | `mode` value | Behavior |
|----------------|-------------|----------|
| Date | `"date"` | Single date selection; calendar grid |
| Time | `"time"` | Time-only; spinner panel; no calendar |
| Datetime | `"datetime"` | Calendar + time panel |
| Range | `"range"` | Two-date selection; range highlight on grid |
| Inline | `inline` (boolean) | Calendar rendered inline; no popup |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `name` | string | `""` | Yes | Form field name |
| `value` | string | `""` | Yes | Selected value in ISO 8601 format (`YYYY-MM-DD`, `HH:mm`, `YYYY-MM-DDTHH:mm`, or `YYYY-MM-DD/YYYY-MM-DD`) |
| `mode` | `"date"` \| `"time"` \| `"datetime"` \| `"range"` | `"date"` | Yes | Picker mode |
| `min` | string | `""` | Yes | Minimum selectable date/time (ISO 8601) |
| `max` | string | `""` | Yes | Maximum selectable date/time (ISO 8601) |
| `disabled` | boolean | `false` | Yes | Disables the control |
| `readonly` | boolean | `false` | Yes | Value cannot be changed; submitted as-is |
| `required` | boolean | `false` | Yes | A value is required for validity |
| `clearable` | boolean | `false` | Yes | Shows a clear button when a value is selected |
| `inline` | boolean | `false` | Yes | Renders calendar inline; no popup |
| `open` | boolean | `false` | Yes | Opens/closes the popup programmatically |
| `locale` | string | `""` | Yes | BCP 47 locale tag for formatting (defaults to `navigator.language`) |
| `first-day-of-week` | number | `0` | Yes | 0 = Sunday, 1 = Monday (overrides locale default) |
| `disabled-dates` | string | `""` | Yes | JSON array of ISO date strings or ranges to disable |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `valueAsDate` | `Date \| null` | Current value as a `Date` object (date/datetime modes) |
| `startDate` | `Date \| null` | Range start date (range mode) |
| `endDate` | `Date \| null` | Range end date (range mode) |
| `displayMonth` | `Date` | The currently visible month in the calendar |
| `validity` | `ValidityState` | Delegated from `ElementInternals` |
| `validationMessage` | `string` | Localizable invalid message |
| `isDateDisabled` | `(date: Date) => boolean` | Custom function for per-date disabling |

## 7. Slots
| Slot | Description |
|------|-------------|
| `trigger-icon` | Custom calendar icon for the trigger button |
| `day-content` | Custom content renderer per day cell (receives the date) |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-change` | `{ value: string, date: Date \| null, startDate: Date \| null, endDate: Date \| null }` | Yes | No | Fired when a date/time is committed |
| `mj-input` | `{ inputValue: string }` | Yes | No | Fired on text input change before commit |
| `mj-open` | `{}` | Yes | Yes | Fired before popup opens |
| `mj-close` | `{}` | Yes | No | Fired after popup closes |
| `mj-month-change` | `{ month: number, year: number }` | Yes | No | Fired when the calendar navigates to a new month |

## 9. CSS parts & custom properties
**Parts:** `input`, `calendar-trigger`, `clear`, `popup`, `calendar-header`, `prev`, `next`, `month-selector`, `year-selector`, `day-grid`, `day-cell`, `week-row`, `week-header`, `time-panel`, `range-start`, `range-end`, `range-fill`

**Custom properties:**
| Property | Default token | Description |
|----------|---------------|-------------|
| `--mj-date-picker-popup-width` | `20rem` | Width of the calendar popup |
| `--mj-date-picker-cell-size` | `2.25rem` | Width and height of each day cell |
| `--mj-date-picker-selected-color` | `--mj-color-accent` | Background of selected day |
| `--mj-date-picker-range-fill-color` | `--mj-color-selected-subtle` | Background of range-fill cells |
| `--mj-date-picker-today-border` | `1px solid --mj-color-accent` | Border style for today's date cell |
| `--mj-date-picker-disabled-opacity` | `0.4` | Opacity for disabled day cells |

## 10. States
| State | Visual effect | ARIA effect |
|-------|--------------|-------------|
| Default | Input shows formatted value or placeholder | — |
| Open | Popup visible | `aria-expanded="true"` on trigger |
| Today | Distinct border on today's cell | `aria-label` includes "today" |
| Selected date | Filled circle | `aria-selected="true"` on cell |
| Range start/end | Filled circle with half-fill toward range | `aria-selected="true"` on cells |
| Range fill | Subtle background tint on inner cells | `aria-selected="true"` on cells |
| Hovered date | Hover tint | — |
| Focused date | Focus ring on cell | Roving `tabindex="0"` on focused cell |
| Disabled date | Muted; no pointer events | `aria-disabled="true"` on cell |
| Out-of-month | Muted; optionally hidden | `aria-disabled="true"` |
| Invalid | Error border on input | `aria-invalid="true"` |
| Disabled control | Input and trigger muted | `aria-disabled="true"` |

## 11. Behavior & interactions
- Clicking the input or calendar-trigger icon opens the popup.
- The text input accepts typed dates in the locale-appropriate format; on blur or Enter the typed value is parsed and committed.
- In range mode, the first click sets the start date; the second click sets the end date; hovering between sets a preview fill; clicking a date earlier than the start swaps start and end.
- Disabled dates and dates outside `min`/`max` cannot be selected; they are visually muted and skipped by keyboard navigation.
- Month navigation (prev/next) animates page-turn direction; `prefers-reduced-motion` disables the animation.
- Clicking the month or year in the header switches the calendar to a month or year selection grid.
- In datetime mode, the time panel below the calendar allows adjusting hours and minutes (with seconds optional via `show-seconds` attribute).

## 12. Keyboard interaction
| Key | Context | Action |
|-----|---------|--------|
| `Enter` / `Space` | Input / trigger | Open popup |
| `Escape` | Popup open | Close popup; restore previous value |
| `ArrowLeft` | Calendar grid | Move focus to previous day |
| `ArrowRight` | Calendar grid | Move focus to next day |
| `ArrowUp` | Calendar grid | Move focus up one week |
| `ArrowDown` | Calendar grid | Move focus down one week |
| `Home` | Calendar grid | Move focus to first day of week |
| `End` | Calendar grid | Move focus to last day of week |
| `PageUp` | Calendar grid | Navigate to previous month |
| `PageDown` | Calendar grid | Navigate to next month |
| `Shift+PageUp` | Calendar grid | Navigate to previous year |
| `Shift+PageDown` | Calendar grid | Navigate to next year |
| `Enter` / `Space` | Day cell | Select focused date (or set start/end in range mode) |
| `Tab` | Popup | Move through header controls, grid, time panel |

## 13. Accessibility
- Input has `role="combobox"`, `aria-haspopup="dialog"`, `aria-expanded`, `aria-autocomplete="none"`.
- Calendar popup has `role="dialog"` with `aria-label` (e.g., "Choose a date").
- Day grid has `role="grid"` with `aria-label` for the displayed month and year.
- Week rows have `role="row"`; day cells have `role="gridcell"` with a nested `<button>` for activation.
- Focused day cell button has `aria-label` with the full formatted date (e.g., "Wednesday, June 14, 2023").
- Today's cell button includes "today" in its `aria-label`.
- `aria-selected="true"` on selected day cells.
- `aria-disabled="true"` on disabled or out-of-range day cells; these cells are still rendered but their buttons are disabled.
- Month navigation buttons: `aria-label="Previous month"` / `"Next month"`.
- Live region announces navigation: "June 2023" on month change.
- Focus is trapped in the popup; restoring to the trigger on close.

## 14. Form participation
- Form-associated via `ElementInternals`; contributes `name=value` in ISO 8601 format.
- Range mode: two values submitted as `name[start]=...` and `name[end]=...`, or a single slash-joined value depending on the `range-format` attribute.
- `required`: `validity.valueMissing` when `value` is empty.
- On form reset, reverts to the initial `value` attribute.
- Date outside `min`/`max`: `validity.rangeUnderflow` / `validity.rangeOverflow`.

## 15. Internationalization & RTL
- Day names, month names, and date formatting use `Intl.DateTimeFormat` with the configured `locale`.
- `first-day-of-week` overrides the locale default for the first column of the calendar.
- In RTL, the calendar grid columns mirror (Sunday on the left in LTR; on the right in RTL unless `first-day-of-week` is set).
- Prev/next arrows flip in RTL.
- Time format (12h vs 24h) follows the locale's convention.

## 16. Progressive enhancement / SSR
- Server renders `<input type="date">` (or `type="datetime-local"`) inside `<mj-date-picker>`.
- Before upgrade the native input is functional.
- On upgrade, the native input is hidden; the component takes over formatting and the popup calendar.
- Without scripting, the native date input renders and is functional.

## 17. Dependencies
- Section 6: Registry/base element, design tokens, overlay/positioning engine, focus utilities (focus trap, roving tabindex in grid), form-association helper, live-region service, localization hook over `Intl`.

## 18. Edge cases & error handling
- `min > max`: component logs a console error; all dates are disabled; required validation always fails.
- Typed date doesn't parse: field enters error state; previous value retained.
- `disabled-dates` includes the current `value`: value is retained but shown with a warning; form validation marks invalid.
- Range mode: user clicks the same date for start and end — a single-day range is valid.
- Month navigation reaches `min`/`max` boundary: prev/next button disabled accordingly.
- Popup taller than viewport: calendar scrolls internally; focus management still works.
- Locale not recognized by `Intl.DateTimeFormat`: component falls back to `"en-US"` and logs a warning.

## 19. Acceptance criteria
- [ ] `mode="date"`: selecting a date fires `mj-change` with ISO date string and `Date` object.
- [ ] `mode="range"`: first click sets start; second click sets end; preview fill shown on hover.
- [ ] `mode="time"`: time spinners commit on Enter/blur; `mj-change` fires with ISO time string.
- [ ] `mode="datetime"`: both date and time must be set before `mj-change` fires a complete value.
- [ ] Arrow keys navigate the calendar grid; PageUp/Down navigate months.
- [ ] `min`/`max` dates: out-of-range cells disabled; keyboard navigation skips them.
- [ ] `aria-selected="true"` on selected cells; `aria-disabled="true"` on disabled cells.
- [ ] Focus trapped in popup; restored to trigger on close.
- [ ] Month navigation announces new month via live region.
- [ ] axe-core reports zero violations in date, range, and time modes.
- [ ] RTL layout mirrors calendar; `Intl.DateTimeFormat` used for formatting.
- [ ] Form submission includes correct ISO value; form reset restores initial value.

## 20. Open questions
- Should the calendar grid show 6 weeks always (fixed height) or a variable number of weeks per month?
- Should week numbers be optionally displayed as a leading column?
- Is the time panel a spinner (input+arrows) or a dropdown list of times at a configurable step interval?
