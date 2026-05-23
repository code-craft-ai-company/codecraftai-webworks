# Release Calendar Spec

- **Tag:** `<mj-release-calendar>`
- **Class / file:** `ReleaseCalendar` / `releasecalendar.js`
- **Category:** Project-management & configuration-management charts
- **Primary or Variant:** Primary
- **Synonyms covered:** Release calendar, Deployment calendar, Key-date calendar
- **Phase:** P3
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-release-calendar>` renders releases, feature freezes, code-freeze windows,
deployment blackouts, and key project dates on a month/week/day calendar grid.
It reuses the Calendar grid component from §5.8 and the shared milestone/marker
model from §6, adding release-specific marker types and a compact event-chip
rendering mode suited for high-density scheduling calendars.

## 2. When to use / when not to use

**Use** when the audience thinks in calendar terms (month view, week view) about
release dates, freeze windows, and on-call schedules. **Do not use** for
sprint-level task scheduling (use `<mj-gantt-chart>`) or for a single linear
axis of milestones (use `<mj-milestone-timeline>`). Nearest alternative:
`<mj-milestone-timeline>` for a purely linear axis view.

## 3. Anatomy

- **Calendar grid** — month, week, or day grid reused from the §5.8 Calendar
  grid component; navigable by month/week.
- **Event chips** — compact colored chips placed on calendar day cells; carry
  marker type, name, and optional duration span.
- **Multi-day event bars** — chips that span across adjacent day cells for events
  with a duration (e.g. freeze windows, blackouts).
- **Marker type icons** — per-chip icon distinguishing release, freeze,
  blackout, milestone, and holiday.
- **Detail popover** — appears on chip activation; shows full event metadata.
- **Month/week/day toggle** — view switcher in the calendar header.
- **Navigation controls** — previous/next period and "today" button.
- **Accessible event list** — `<ol>` of all events in chronological order.

## 4. Variants & modes

| Mode / Variant | Attribute | Behavior |
|---|---|---|
| Month view | `view="month"` (default) | Full month grid; multi-day bars span cells |
| Week view | `view="week"` | 7-column week grid with time lanes |
| Day view | `view="day"` | Single-day time column |
| Read-only | `readonly` (boolean, default) | No event editing; only viewing |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `src` | string | `""` | yes | URL for the data-source adapter |
| `adapter` | string | `"static"` | yes | Adapter key: `"static"`, `"github"`, `"jira"`, `"ical"` |
| `view` | `"month"` \| `"week"` \| `"day"` | `"month"` | yes | Calendar grid granularity |
| `current-date` | string (ISO 8601) | `""` | yes | The date to navigate to on load; defaults to today |
| `today-marker` | boolean | `true` | yes | Highlight today's cell |
| `readonly` | boolean | `false` | yes | Disables editing actions |
| `first-day-of-week` | number (0–6) | `0` | yes | 0=Sunday, 1=Monday; locale-aware default |
| `locale` | string | `""` | yes | BCP 47 locale for day/month names |
| `label-loading` | string | `"Loading calendar…"` | yes | Loading message |
| `label-empty` | string | `"No events."` | yes | Empty message |
| `label-error` | string | `"Failed to load calendar."` | yes | Error message |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `data` | `CalendarData` | `{ events: CalendarEvent[] }` where each event has `{ id, name, type, startDate, endDate, description, url }` |
| `selectedEvent` | `CalendarEvent \| null` | Currently selected event |
| `visiblePeriod` | `{ start: Date, end: Date }` | Currently displayed calendar period |

## 7. Slots

| Slot | Description |
|------|-------------|
| `(default)` | Fallback `<ol>` of events rendered before upgrade |
| `event-detail` | Custom detail popover for a selected event |
| `empty` | Shown when no events are present |
| `loading` | Shown during adapter fetch |
| `error` | Shown on adapter failure |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-event-select` | `{ event: CalendarEvent }` | yes | no | Event chip activated |
| `mj-event-deselect` | `{}` | yes | no | Selection cleared |
| `mj-period-change` | `{ start: string, end: string, view: string }` | yes | no | Calendar navigated to a new period |
| `mj-view-change` | `{ view: string }` | yes | no | View mode switched |
| `mj-data-load` | `{ events: number }` | yes | no | Data loaded |
| `mj-error` | `{ message: string, cause: unknown }` | yes | no | Adapter error |

## 9. CSS parts & custom properties

**Parts:**
- `::part(calendar-grid)` — the underlying calendar grid
- `::part(day-cell)` — individual day cell
- `::part(event-chip)` — compact event chip in a cell
- `::part(event-bar)` — multi-day spanning bar
- `::part(event-icon)` — icon within a chip
- `::part(detail-popover)` — event detail overlay
- `::part(nav-controls)` — previous/next/today navigation
- `::part(view-switcher)` — month/week/day toggle
- `::part(today-cell)` — today's day cell highlight

**Custom properties:**
- `--mj-event-release-color` — chip color for `type=release`
- `--mj-event-freeze-color` — chip color for `type=freeze`
- `--mj-event-blackout-color` — chip color for `type=blackout`
- `--mj-event-milestone-color` — chip color for `type=milestone`
- `--mj-event-holiday-color` — chip color for `type=holiday`
- `--mj-chip-height` — event chip height (default `20px`)
- `--mj-today-highlight-color` — today cell background color
- `--mj-grid-border-color` — cell border color

## 10. States

- **loading** — `aria-busy="true"`; loading slot shown.
- **empty** — no events in visible period; empty slot shown; grid still renders.
- **error** — error slot shown.
- **event-selected** — chip or bar highlighted; detail popover open.
- **today-highlighted** — today's cell has distinct background.
- **freeze-day** — days within a freeze event have a background tint on the cell.

## 11. Behavior & interactions

The calendar grid is provided by the §5.8 Calendar grid component, configured
for read-only date display (no date selection). Event chips are placed in day
cells by the component, sorted by start time within each cell. When more than
3 events exist in a day cell, a "+N more" overflow chip is shown; activating it
opens a popover listing all events for that day. Multi-day events render as
spanning bars across cells, following the same layout rules as the §5.8 calendar
event rendering. The `adapter` fetches events for the current visible period on
each `mj-period-change`; the adapter is called with `{ start, end }` ISO strings.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Tab` | Move focus through navigation controls, view switcher, then event chips in day order |
| `Arrow Left` / `Arrow Right` | Move focus between event chips within the same week row |
| `Arrow Up` / `Arrow Down` | Move focus between weeks |
| `Enter` / `Space` | Activate focused event chip (open detail popover) |
| `Escape` | Close detail popover; deselect event |
| `Page Up` | Navigate to previous period |
| `Page Down` | Navigate to next period |
| `Home` | Navigate to today |

## 13. Accessibility

- Root: `role="region"` with `aria-label` = "Release calendar, {month year} –
  {n} events".
- Calendar grid inherits the `grid` role from the §5.8 Calendar grid component;
  each day cell is `role="gridcell"`.
- Event chips: `role="button"` with `aria-label` = "{name}, {type}, {date}" for
  single-day events; "{name}, {type}, {start date} to {end date}" for multi-day.
- Overflow chip: `role="button"` `aria-label` = "{n} more events on {date}".
- Navigation buttons: previous `aria-label` = "Previous {view}"; next = "Next
  {view}"; today = "Go to today".
- View switcher: `role="radiogroup"` with `role="radio"` items; or Tabs pattern
  if visually rendered as tabs.
- Accessible event list: `<ol>` in chronological order; each `<li>` contains
  event name, type, and formatted date/range; revealed via "Show event list"
  disclosure toggle.
- Freeze windows: freeze-background tinted cells include `aria-label` suffix
  "in freeze window" on each affected day cell.

## 14. Form participation

N/A.

## 15. Internationalization & RTL

- Day and month names use `Intl.DateTimeFormat` with `locale` attribute.
- `first-day-of-week` defaults to locale-appropriate value when `locale` is set
  and no explicit value is supplied.
- All UI strings overridable: `label-loading`, `label-empty`, `label-error`,
  `label-today`, `label-previous`, `label-next`, `label-month`, `label-week`,
  `label-day`, `label-more-events`, `label-show-list`.
- RTL: calendar grid mirrors (days flow right-to-left); event chips mirror;
  popover positioned on the appropriate side.

## 16. Progressive enhancement / SSR

Server renders an `<ol>` of events in chronological order inside the default
slot. On upgrade the component hides the list visually (re-accessible via toggle)
and initializes the calendar grid.

## 17. Dependencies

- §5.8 Calendar grid component (grid structure, keyboard navigation, date cells)
- §6 milestone/marker model (event types: release, freeze, milestone, blackout,
  holiday)
- §6 data-source adapter interface (adapter keys: `static`, `github`, `jira`,
  `ical`)
- §6 registry + base element helper
- §6 design-token stylesheet
- §6 overlay/positioning engine (detail popover)
- §6 localization/formatting hook (`Intl.DateTimeFormat`)

## 18. Edge cases & error handling

- **No events in visible period** — empty slot content shown; navigation still
  works.
- **Events outside visible period** — clipped; not rendered.
- **Overlapping multi-day bars in same row** — bars stacked vertically within
  the row; "+N more" overflow after 3 rows.
- **Event with `endDate` before `startDate`** — dates swapped with console warning.
- **Adapter failure** — error slot shown; stale data for the previous period retained.
- **`ical` adapter with recurring events** — events expanded to individual
  occurrences within the requested window by the adapter.

## 19. Acceptance criteria

- [ ] Events render in correct day cells from static `data`.
- [ ] Multi-day events span across multiple cells as bars.
- [ ] Today's cell is highlighted when `today-marker` is true.
- [ ] Selecting an event chip fires `mj-event-select` and opens detail popover.
- [ ] Previous/next navigation fires `mj-period-change` and fetches new data.
- [ ] View switcher changes `view` and fires `mj-view-change`.
- [ ] Keyboard navigation per §12 covers chips, nav controls, and view switcher.
- [ ] Accessible event list present with all events in chronological order.
- [ ] Freeze-window cells include "in freeze window" in their accessible label.
- [ ] `locale` attribute changes day and month names.
- [ ] RTL layout mirrors correctly.
- [ ] axe automated accessibility check passes with zero violations.

## 20. Open questions

- Should the `ical` adapter handle iCalendar subscription URLs directly, or
  does the server proxy/expand the iCalendar feed before serving the adapter URL?
- Is a "deployment blackout" type that locks its day cells from event creation
  (in a future editable mode) needed, or is it a visual-only marker for now?
