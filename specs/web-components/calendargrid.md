# Calendar Grid Spec

- **Tag:** `<mj-calendar>`
- **Class / file:** `MjCalendar` / `mjcalendar.js`
- **Category:** Tables, lists & structured data
- **Primary or Variant:** Primary
- **Synonyms covered:** Calendar grid, Month view, Week view, Day view, Event calendar, Release calendar
- **Phase:** P2
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-calendar>` renders a calendar in month, week, or day view with event
rendering, keyboard date navigation, and accessible `grid` semantics. It shares
its calendar engine (locale-aware date math, week-start, date range calculations)
with `<mj-date-picker>` so logic is not duplicated. It is the presentation layer
for events or markers over a time grid, and is the base for the Release calendar
in the PM/SCM chart family.

## 2. When to use / when not to use
**Use** when the primary goal is to display and navigate events on a calendar
layout. **Do not use** for simple date selection without event data — use
`<mj-date-picker>`. For a compact inline date picker within a form field use
`<mj-date-picker mode="inline">`. For Gantt or milestone timelines use the
PM/SCM chart components.

## 3. Anatomy
- **Header bar** — current period label (month name, week range, or date); previous/next navigation buttons; view switcher.
- **Day-of-week header row** — `role="row"` with `role="columnheader"` cells (Sun–Sat or Mon–Sun depending on locale).
- **Calendar grid** — `role="grid"` containing weeks as `role="row"` and days as `role="gridcell"`.
- **Day cell** — contains the date number, event chips, and an overflow indicator ("+ N more").
- **Event chip** — colored pill rendering a single event; truncated label with full title in tooltip.
- **Time grid (week/day view)** — hourly row grid with event blocks positioned by start/end time.
- **All-day row** — top row in week/day view for all-day events.
- **Now indicator** — horizontal line at the current time in week/day view.

## 4. Variants & modes
| Variant | `view` value | Behavior |
|---------|-------------|----------|
| Month | `month` (default) | 4–6 week rows; each cell shows date + event chips. |
| Week | `week` | 7 columns × 24 hour rows; events as positioned blocks. |
| Day | `day` | 1 column × 24 hour rows; all-day row at top. |
| Agenda | `agenda` | Linear list of upcoming events grouped by date; no grid. |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `view` | `month\|week\|day\|agenda` | `month` | yes | Calendar display mode. |
| `value` | string (ISO 8601 date) | today | yes | Currently displayed date (anchor for the view period). |
| `min` | string (ISO date) | `""` | yes | Earliest navigable date; cells before this are `aria-disabled`. |
| `max` | string (ISO date) | `""` | yes | Latest navigable date. |
| `first-day-of-week` | number `0–6` | locale default | yes | 0 = Sunday, 1 = Monday, etc. |
| `locale` | string | document locale | yes | BCP 47 locale for formatting. |
| `show-week-numbers` | boolean | false | yes | Shows ISO week number in the leftmost column. |
| `readonly` | boolean | false | yes | Disables event creation and date selection; navigation still works. |
| `loading` | boolean | false | yes | Shows skeleton grid and `aria-busy="true"`. |
| `event-overflow` | number | `3` | yes | Max event chips per cell before overflow indicator. |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `events` | `CalendarEvent[]` | `{ id, title, start: Date, end: Date, allDay?: boolean, color?: string, data?: unknown }` |
| `dataSource` | `CalendarDataSourceAdapter` | `{ fetchEvents(start: Date, end: Date): Promise<CalendarEvent[]> }` — called on view/period change. |
| `displayedPeriod` | `{ start: Date, end: Date }` | Read-only; the date range currently shown. |

## 7. Slots
| Slot | Description |
|------|-------------|
| `event` | Template cloned for each event chip; receives `data-event-id`. |
| `day-header` | Custom day cell header content (above date number). |
| `toolbar-start` | Content inserted at the start of the header bar. |
| `toolbar-end` | Content inserted at the end of the header bar (e.g., view switcher override). |
| `empty` | Shown when no events exist in the current period. |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-date-select` | `{ date: string }` | true | false | User clicked/activated a day cell. |
| `mj-event-click` | `{ eventId: string, event: CalendarEvent }` | true | false | User activated an event chip. |
| `mj-period-change` | `{ start: string, end: string, view: string }` | true | false | Navigation moved to a new period. |
| `mj-event-create` | `{ date: string, startTime?: string }` | true | true | User initiated event creation (e.g., clicking empty time slot); cancel to suppress. |
| `mj-event-move` | `{ eventId: string, newStart: string, newEnd: string }` | true | true | User dragged an event to a new date/time; cancel to reject. |
| `mj-view-change` | `{ view: string }` | true | false | User switched calendar view. |

## 9. CSS parts & custom properties
**Parts:** `header`, `prev-button`, `next-button`, `view-switcher`, `grid`,
`week-row`, `day-cell`, `day-number`, `day-cell-today`, `day-cell-other-month`,
`event-chip`, `event-overflow`, `time-grid`, `time-label`, `now-indicator`,
`all-day-row`.

| Custom property | Default | Purpose |
|----------------|---------|---------|
| `--mj-cal-cell-min-height` | `80px` | Minimum height of a month-view day cell. |
| `--mj-cal-today-bg` | `token(--mj-color-primary-subtle)` | Today cell background. |
| `--mj-cal-other-month-opacity` | `0.4` | Opacity for days outside the current month. |
| `--mj-cal-event-radius` | `token(--mj-radius-sm)` | Event chip border radius. |
| `--mj-cal-now-color` | `token(--mj-color-error)` | Now indicator line color. |
| `--mj-cal-weekend-bg` | `token(--mj-color-surface-subtle)` | Weekend column background (week/day view). |
| `--mj-cal-time-col-width` | `48px` | Width of the time label column in week/day view. |

## 10. States
- **default** — current period rendered; today highlighted.
- **loading** — `aria-busy="true"` on grid; skeleton cells shown while events fetch.
- **day-selected** — clicked day cell `aria-selected="true"`.
- **today** — today's cell carries `aria-current="date"` and `--mj-cal-today-bg`.
- **out-of-range** — cells before `min` or after `max` have `aria-disabled="true"`.
- **event-overflow** — cell shows "+ N more" button when event count exceeds `event-overflow`.
- **event-selected** — focused event chip `aria-selected="true"`.

## 11. Behavior & interactions
**Calendar engine:** Shared with `<mj-date-picker>` as a utility module. Handles
locale-aware week-start, month boundary calculations, leap years, DST transitions,
and ISO week numbering. Week and day views divide each day into configurable
time-slot rows (default 60-minute slots, configurable via `--mj-cal-slot-height`).

**Event rendering:** On period change, if `dataSource` is set, `fetchEvents` is
called with the displayed range. While fetching, `loading` is set. Events are
sorted by start time and positioned. In month view, multi-day events span cells
using CSS grid placement. In week/day view, overlapping events are laid out in
columns with calculated widths (conflict resolution).

**Navigation:** Previous/Next buttons decrement/increment the period by one
month/week/day. The `value` attribute and property update to the new anchor date
and `mj-period-change` fires.

**Event creation (non-readonly):** Click/tap on an empty time slot fires
`mj-event-create`. If not canceled, a placeholder event chip is shown and the
caller is expected to open an event form. Event move via drag: `mj-event-move`
fires on drop; cancel reverts the ghost.

**Overflow popover:** Clicking "+ N more" opens a popover listing all events for
that day. The popover is managed by the shared overlay/positioning engine.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Arrow Left / Right` | Move focus to previous/next day cell. |
| `Arrow Up / Down` | Move focus to same weekday in the previous/next week. |
| `Page Up` | Navigate to previous month/week. |
| `Page Down` | Navigate to next month/week. |
| `Home` | Move focus to the first day of the current week (in month/week view). |
| `End` | Move focus to the last day of the current week. |
| `Ctrl+Home` | Navigate to first day of the current month. |
| `Ctrl+End` | Navigate to last day of the current month. |
| `Enter` / `Space` | Emit `mj-date-select` for focused day; or `mj-event-click` for focused event chip. |
| `Tab` | Move focus from day grid to event chips within the focused day, then to next day. |
| `Escape` | Dismiss overflow popover; cancel in-progress event creation. |

## 13. Accessibility
- Grid root: `role="grid"` with `aria-label="Calendar, {Month Year}"` updated on navigation.
- Day-of-week header cells: `role="columnheader"` with full weekday name in `aria-label` (abbreviated in visible text).
- Day cells: `role="gridcell"` with `aria-label="{day ordinal} {month} {year}{, N events}"`.
- Today cell: `aria-current="date"`.
- Out-of-range cells: `aria-disabled="true"`.
- Event chips: `role="button"` or `<button>` with `aria-label="{event title}, {start time}–{end time}"`.
- Overflow button: `aria-label="{N} more events on {date}"`.
- Period change: live region (`aria-live="polite"`) announces "Showing {month year}" after navigation.
- Loading: `aria-busy="true"` on grid; live region announces "Loading events."
- `prefers-reduced-motion`: event drag animations disabled; now indicator pulse disabled.
- Event colors must not be the only differentiator between event types; icon or label required.

## 14. Form participation
N/A when used as an event calendar. When used as a date picker (shared engine with
`<mj-date-picker>`), the picker component handles form participation.

## 15. Internationalization & RTL
- Week grid column order reverses in RTL.
- First day of week defaults from locale BCP 47 data; overridable via `first-day-of-week`.
- Date labels, month names, and weekday names from `Intl.DateTimeFormat`.
- ISO week numbers via `Intl` or a locale-aware calculation utility.
- All user-facing strings (navigation labels, "more events" text) overridable via attributes.

## 16. Progressive enhancement / SSR
Server renders a month grid as a native `<table>` with events as `<ul>/<li>` within
each cell. Before JS the calendar is readable; links on events provide navigation.
On upgrade the component replaces the table with the interactive `role="grid"`,
attaches keyboard navigation, and fires `mj-period-change` to load live event data.

## 17. Dependencies
- Calendar engine utility (shared with `<mj-date-picker>`) — date math, locale formatting (§6 localization hook).
- Collection/virtualization utility (§6) — agenda view list.
- Overlay/positioning engine (§6) — overflow popover.
- Live-region/announcement service (§6).
- Design-token stylesheet (§6).
- `<mj-button>` for navigation controls and view switcher.
- `<mj-popover>` for overflow event list.

## 18. Edge cases & error handling
- **`dataSource` fetch fails** — error alert shown inside calendar header; retry button re-fetches.
- **Events spanning month boundaries** — multi-day event chips clipped at row edges with continuation indicators.
- **DST transition days** — calendar engine normalizes all times to UTC for position calculations.
- **Overlapping events** — conflict resolution splits cells into sub-columns; minimum event chip width is `--mj-cal-min-event-width`.
- **Zero-length events** — rendered as a single-slot chip.
- **`max < min`** — entire calendar disabled; console error logged.
- **Very long event titles** — truncated with ellipsis; full title in `aria-label` and tooltip.

## 19. Acceptance criteria
- [ ] `role="grid"` with `aria-label` updated on navigation; `role="columnheader"` on weekday headers.
- [ ] Day cells `role="gridcell"`; today cell `aria-current="date"`; out-of-range `aria-disabled="true"`.
- [ ] Arrow key navigation moves between day cells as documented; Page Up/Down changes period.
- [ ] `mj-period-change` fires on navigation; `dataSource.fetchEvents` called with new range.
- [ ] Events render as `<button>` elements with descriptive `aria-label`; `mj-event-click` fires.
- [ ] Multi-day events span correct cells in month view.
- [ ] Overflow "+N more" opens popover listing events; popover is keyboard dismissible.
- [ ] Live region announces new period after navigation.
- [ ] `loading` shows skeleton cells and `aria-busy="true"`.
- [ ] Week/day view: events positioned by time; overlapping events in sub-columns; now indicator shown.
- [ ] First day of week follows locale default; overridable by `first-day-of-week`.
- [ ] axe audit passes with zero violations.
- [ ] RTL: column order reversed; navigation arrow directions mirrored.

## 20. Open questions
- Should drag-to-create (draw a time range) be in scope for P2 or deferred?
- Should the `agenda` view use `role="feed"` with incremental loading?
- Is timezone (IANA zone) support required at launch, or is UTC-normalized display sufficient?
