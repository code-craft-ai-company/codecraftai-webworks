# Milestone Timeline Spec

- **Tag:** `<mj-milestone-timeline>`
- **Class / file:** `MjMilestoneTimeline` / `components/mjmilestonetimeline.js` (base: `components/pmchartwrapper.js`)
- **Category:** Project-management & configuration-management charts
- **Primary or Variant:** Variant — a convenience wrapper for `<mj-chart type="milestone" dim-past>`
- **Synonyms covered:** Milestone timeline, Release timeline, Key dates
- **Status:** Implemented (wrapper since WW-1498)

> `<mj-milestone-timeline>` is `<mj-chart type="milestone">` with the type fixed,
> `dim-past` on and the marker data shape of this component family. Drawing
> (shape and colour by kind, labels in tiers, phase bands, the today line, past
> markers faded), keyboard support, the data table and data loading are the
> chart's: see [chart.md](chart.md) (§21) and the `milestone` chart-type page.
> This spec records only what differs.

## 1. Purpose and when to use

The lightest timeline: one axis of named markers with phases and a today line.
Use `<mj-gantt-chart>` for durations and dependencies.

## 2. Data shape (mapped onto the chart type)

```
{ markers: [{ name, date, type, description }], phases: [{ name, start, end }] }
```

| Wrapper field | Chart type field |
|---|---|
| `markers` | `events` |
| `name` (else "Marker N") | `label` |
| `type` (release, freeze, tag, milestone; missing = milestone) | `kind` (release diamond green, freeze triangle amber, tag circle info, milestone circle accent) |
| `description` | `description` (tooltip, table, detail panel) |
| `phases[].name` | `label` |

A marker with an invalid date or outside the `start-date` / `end-date` window is
listed in the data table but not drawn.

## 3. Attributes

| Attribute | Chart type option | Notes |
|---|---|---|
| `start-date`, `end-date` | same | fix the window (date-only end inclusive) |
| `density` | same | compact: smaller labels cut at about 12 characters |
| `today-marker` | `today` | default on |
| — | `dim-past` | always on: markers more than a day before now are faded and their accessible name ends with past / today / upcoming |
| `src` | — | as on `<mj-chart>` |

The chart is 200 px tall unless the page sets a height (`--mj-chart-min-height`).

## 4. Properties and events

| Property | Description |
|---|---|
| `data` | The data above; assigning draws at once, clears the selection, emits `mj-data-load` |
| `selectedMarker` | The selected marker object, or null |

| Event | `detail` | From |
|---|---|---|
| `mj-marker-select` | `{ marker }` | `mj-chart-event-click`; opens the inline detail panel |
| `mj-marker-deselect` | `{}` | the detail panel closed |
| `mj-data-load` | `{ markers, phases }` | first draw of each data object |
| `mj-error` | `{ message }` | `mj-chart-error` |

## 5. Slots and parts

- Slots: `marker-detail` (extra detail-panel content), `empty`.
- Parts: `toolbar`, `detail-popover`, the chart's `surface`, `svg`, `message`,
  `table data-table`, and the renderer's `marker`, `marker-label`, `phase-band`,
  `time-axis`, `today-marker`, `today-label`.

## 6. Migration (behaviour changes from the standalone implementation)

- The accessible ordered list (`ol`, part `a11y-list`) is replaced by the chart's
  data table (Event / Date / Group / Status / Kind / Description), disclosed by the
  toolbar button; the state word "current" is now "today".
- Labels are placed in tiers that depend on the chart height (were up to three
  fixed rows each side); the axis is padded by 5 % of the span (was three days).
- The chart fits its width (no sideways scrolling at 2 px/day).
- Parts `wrapper`, `a11y-list` and `empty-state` are gone; error texts are the
  chart's generic messages (detail in `mj-error`); the default-slot fallback is not
  shown. Markers are `role="img"` with `aria-current` for the selection.
