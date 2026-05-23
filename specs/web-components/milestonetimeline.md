# Milestone Timeline Spec

- **Tag:** `<mj-milestone-timeline>`
- **Class / file:** `MilestoneTimeline` / `milestonetimeline.js`
- **Category:** Project-management & configuration-management charts
- **Primary or Variant:** Primary
- **Synonyms covered:** Milestone timeline, Key-date timeline
- **Phase:** P3
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-milestone-timeline>` renders a single horizontal (or vertical) axis of
named milestones, key dates, and phase bands. It is the lightest timeline
visualization in the library: no task bars, no dependency arrows — just an
annotated time axis that communicates when important events happen. It reuses the
shared milestone/marker model and the time-axis utility from §6, and composes on
the Timeline primitive from §5.5.

## 2. When to use / when not to use

**Use** when stakeholders need a quick overview of key dates (feature freezes,
release dates, code reviews, holidays) without task-scheduling detail. **Do not
use** when tasks and dependencies matter (use `<mj-gantt-chart>`), or for a
full-initiative roadmap (use `<mj-roadmap-chart>`). Nearest alternative:
`<mj-gantt-chart>` milestone row only.

## 3. Anatomy

- **Time axis** — shared horizontal ruler; zoom, pan, today marker, locale-aware
  tick labels via the time-axis utility.
- **Milestone markers** — named diamonds or circles from the shared
  milestone/marker model; labeled above/below the axis alternating to reduce
  overlap.
- **Phase bands** — colored spans behind the axis (e.g. Alpha, Beta, GA).
- **Past / current / upcoming visual states** — markers styled differently based
  on their date relative to today.
- **Today marker** — vertical line.
- **Accessible list** — visually hidden `<ol>` of all markers with dates.
- **Detail popover** — appears on marker activation; shows name, date, type,
  phase, and optional description.

## 4. Variants & modes

| Mode / Variant | Attribute | Behavior |
|---|---|---|
| Horizontal | `orientation="horizontal"` (default) | Time flows left to right |
| Vertical | `orientation="vertical"` | Time flows top to bottom |
| Compact | `density="compact"` | Smaller markers, no label stagger |
| Full | `density="full"` (default) | Staggered labels above/below axis |
| Read-only | `readonly` (boolean, default) | Markers are informational only |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `src` | string | `""` | yes | URL for the data-source adapter |
| `adapter` | string | `"static"` | yes | Adapter key: `"static"`, `"github"`, `"jira"` |
| `start-date` | string (ISO 8601) | `""` | yes | Left bound of visible window |
| `end-date` | string (ISO 8601) | `""` | yes | Right bound of visible window |
| `orientation` | `"horizontal"` \| `"vertical"` | `"horizontal"` | yes | Layout direction |
| `density` | `"compact"` \| `"full"` | `"full"` | yes | Label verbosity |
| `today-marker` | boolean | `true` | yes | Show today vertical line |
| `readonly` | boolean | `false` | yes | Prevents detail popover interaction actions |
| `locale` | string | `""` | yes | BCP 47 locale for axis formatting |
| `label-loading` | string | `"Loading timeline…"` | yes | Loading message |
| `label-empty` | string | `"No milestones."` | yes | Empty message |
| `label-error` | string | `"Failed to load timeline."` | yes | Error message |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `data` | `TimelineData` | `{ markers: Marker[], phases: Phase[] }` |
| `selectedMarker` | `Marker \| null` | Currently selected marker |
| `visibleRange` | `{ start: Date, end: Date }` | Current visible time window |

## 7. Slots

| Slot | Description |
|------|-------------|
| `(default)` | Fallback `<ol>` rendered before upgrade |
| `marker-detail` | Custom content for the marker detail popover |
| `empty` | Shown when no markers are present |
| `loading` | Shown during adapter fetch |
| `error` | Shown on adapter failure |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-marker-select` | `{ marker: Marker }` | yes | no | Marker activated |
| `mj-marker-deselect` | `{}` | yes | no | Selection cleared |
| `mj-range-change` | `{ start: string, end: string }` | yes | no | Visible range changed via zoom/pan |
| `mj-data-load` | `{ markers: number }` | yes | no | Data loaded successfully |
| `mj-error` | `{ message: string, cause: unknown }` | yes | no | Adapter error |

## 9. CSS parts & custom properties

**Parts:**
- `::part(time-axis)` — the ruler
- `::part(marker)` — individual milestone marker node
- `::part(marker-label)` — text label for a marker
- `::part(phase-band)` — background phase span
- `::part(today-marker)` — today vertical line
- `::part(detail-popover)` — marker detail overlay

**Custom properties:**
- `--mj-timeline-height` — height of the axis area (default `80px`)
- `--mj-marker-size` — diameter of marker circle/diamond (default `12px`)
- `--mj-marker-release-color` — color for `type=release` markers
- `--mj-marker-freeze-color` — color for `type=freeze` markers
- `--mj-marker-tag-color` — color for `type=tag` markers
- `--mj-marker-milestone-color` — color for generic `type=milestone` markers
- `--mj-marker-past-opacity` — opacity of past markers (default `0.5`)
- `--mj-phase-opacity` — phase band fill opacity (default `0.12`)
- `--mj-today-color` — today marker stroke color
- `--mj-axis-tick-color` — tick label color

## 10. States

- **loading** — `aria-busy="true"`; loading slot shown.
- **empty** — empty slot shown; axis still renders.
- **error** — error slot shown.
- **marker-past** — marker before today; reduced opacity; label styled as
  "past" with `data-state="past"`.
- **marker-current** — marker within today's date (same calendar day);
  highlighted ring; `data-state="current"`.
- **marker-upcoming** — marker after today; default appearance.
- **marker-selected** — detail popover open; marker ring thickened;
  `aria-selected="true"` on marker element.

## 11. Behavior & interactions

On load the visible range defaults to `start-date`/`end-date`; if unset it spans
from the earliest to the latest marker plus a 10% margin on each side. Markers
are positioned by the time-axis utility. Overlapping markers (same or adjacent
dates) are staggered on the y-axis. Clicking or pressing Enter/Space on a marker
fires `mj-marker-select` and opens the detail popover. The popover is non-modal;
Escape closes it. Zoom/pan are handled by the time-axis utility; `mj-range-change`
fires on every change. Phase bands are SVG `<rect>` elements drawn behind the axis.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Tab` | Move focus between markers in date order, then toolbar controls |
| `Arrow Left` / `Arrow Right` | Move focus to previous/next marker |
| `Enter` / `Space` | Select focused marker; open detail popover |
| `Escape` | Close detail popover; deselect marker |
| `+` / `-` | Zoom in / zoom out |
| `0` | Reset zoom to fit all markers |
| `Home` / `End` | Focus first / last marker |

## 13. Accessibility

- Root: `role="img"` with `aria-label` = "Milestone timeline: {n} markers,
  {start} to {end}".
- Each marker: `role="button"` with `aria-label` =
  "{name}, {type}, {date}, {past|current|upcoming}".
- Detail popover: `role="tooltip"` when read-only; `role="dialog"` when actions
  are present; `aria-labelledby` points to marker name heading.
- Phase bands: `aria-hidden="true"`.
- Today marker: `aria-hidden="true"` with a visually hidden text node "Today"
  adjacent to it in the accessible list.
- Accessible list: `<ol>` with `<li>` entries for each marker and phase; revealed
  via "Show accessible list" disclosure button.
- Color differences between marker types are supplemented by shape (diamond for
  release, circle for milestone, triangle for freeze).

## 14. Form participation

N/A.

## 15. Internationalization & RTL

- Axis tick labels use `Intl.DateTimeFormat` with `locale` attribute.
- Detail popover date uses `Intl.DateTimeFormat` with `dateStyle: "long"`.
- All UI strings overridable: `label-loading`, `label-empty`, `label-error`,
  `label-today`, `label-show-list`, `label-zoom-in`, `label-zoom-out`,
  `label-reset-zoom`.
- RTL: axis flows right-to-left; marker labels on opposite side; popover
  positioned via overlay engine with RTL-aware placement.

## 16. Progressive enhancement / SSR

Server renders an `<ol>` of milestone entries inside the default slot with marker
name, date, and type as text. On upgrade the component hides the list visually
(re-accessible via the show-list toggle) and draws the axis/markers without
layout shift using `height-hint`.

## 17. Dependencies

- §6 time-axis utility
- §6 milestone/marker model
- §6 data-source adapter interface (adapter keys: `static`, `github`, `jira`)
- §6 registry + base element helper
- §6 design-token stylesheet
- §6 overlay/positioning engine (detail popover)
- §6 live-region/announcement service
- §6 localization/formatting hook
- §5.5 Timeline primitive (ordered list semantics)

## 18. Edge cases & error handling

- **Zero markers** — empty slot shown; axis still renders over the given range.
- **All markers on the same date** — markers stacked vertically; "+N more" label
  if more than 5 overlap.
- **`start-date` after `end-date`** — swapped with warning.
- **Marker date outside `start-date`/`end-date` range** — marker rendered at the
  nearest edge with a clipping indicator.
- **Very long marker name** — label truncated at 40 chars with full name in
  popover.
- **Adapter failure** — error slot shown; stale data retained.

## 19. Acceptance criteria

- [ ] Markers render at correct time positions from static `data`.
- [ ] Past/current/upcoming visual states apply correctly relative to today.
- [ ] Phase bands span the correct date ranges.
- [ ] Today marker appears at the current date.
- [ ] Selecting a marker fires `mj-marker-select` and opens detail popover.
- [ ] Keyboard navigation per §12 works in date order.
- [ ] Accessible list `<ol>` present with all markers and dates.
- [ ] Zoom changes tick labels and repositions markers.
- [ ] RTL layout mirrors correctly.
- [ ] axe automated accessibility check passes with zero violations.
- [ ] Empty, loading, and error states display correct slots.

## 20. Open questions

- Should the detail popover support an edit action (change date/name) or is
  editing always handled externally via the data source?
- Is a "swimlane" variant (multiple parallel timelines stacked) needed, or is
  `<mj-roadmap-chart>` the right choice for multi-row timelines?
