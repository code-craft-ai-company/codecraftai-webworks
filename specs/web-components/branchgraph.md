# Branch Graph Spec

- **Tag:** `<mj-branch-graph>`
- **Class / file:** `BranchGraph` / `branchgraph.js`
- **Category:** Project-management & configuration-management charts
- **Primary or Variant:** Primary
- **Synonyms covered:** Branch network, Commit history graph, Git graph
- **Phase:** P3
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-branch-graph>` renders a release branching and merge chart showing branch
lanes, individual commits, merge/branch-point edges, milestone and key-date
markers, and phase bands over a shared time axis. It replaces ad-hoc SVG
diagrams and static screenshots with an interactive, accessible visualization
driven by VCS API data or static config.

## 2. When to use / when not to use

**Use** to visualize a repository's branching strategy, release trains, or
merge history alongside key project dates (feature freezes, release tags,
hotfix windows). **Do not use** for pipeline stage flows (use
`<mj-pipeline-chart>`) or for flat task scheduling (use `<mj-gantt-chart>`).
Nearest alternatives: `<mj-milestone-timeline>` for date-only views,
`<mj-pipeline-chart>` for CI stage flows.

## 3. Anatomy

- **Time axis** — shared horizontal ruler produced by the time-axis utility;
  supports zoom, pan, today marker, and locale-aware tick labels.
- **Branch lanes** — one horizontal swim-lane per branch; lanes are collapsible.
- **Commit nodes** — circles or diamonds on a branch lane positioned by date;
  carry SHA, message, author, and tags.
- **Merge/branch-point edges** — arcs or diagonal lines connecting commit nodes
  across lanes.
- **Milestone markers** — named vertical markers (release, freeze, tag) from the
  shared milestone/marker model; rendered above the axis.
- **Phase bands** — colored date-range spans (e.g. development, stabilization,
  release) rendered behind the lanes.
- **Legend** — maps lane color, marker type, and phase color to labels.
- **Detail panel** — appears on node/marker selection; shows full metadata.
- **Accessible data table** — `<table>` alternative listing branches, commits,
  and markers; hidden visually but available to assistive technology.

## 4. Variants & modes

| Mode / Variant | Attribute | Behavior |
|---|---|---|
| Compact | `density="compact"` | Commit nodes omit author labels; lane height reduced |
| Full | `density="full"` (default) | All commit labels visible |
| Horizontal | `orientation="horizontal"` (default) | Time flows left to right |
| Vertical | `orientation="vertical"` | Time flows top to bottom |
| Read-only | `readonly` (boolean) | No node selection; no lane collapse controls |
| Live | `live` (boolean) | Polls the data-source adapter at `poll-interval` ms |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `src` | string | `""` | yes | URL for the data-source adapter endpoint |
| `adapter` | string | `"static"` | yes | Adapter key: `"static"`, `"github"`, `"gitlab"`, `"gitea"` |
| `start-date` | string (ISO 8601) | `""` | yes | Left bound of the visible time window |
| `end-date` | string (ISO 8601) | `""` | yes | Right bound of the visible time window |
| `orientation` | `"horizontal"` \| `"vertical"` | `"horizontal"` | yes | Layout direction of time axis |
| `density` | `"compact"` \| `"full"` | `"full"` | yes | Label verbosity on commit nodes |
| `readonly` | boolean | `false` | yes | Disables collapse controls and node selection |
| `live` | boolean | `false` | yes | Enables polling via data-source adapter |
| `poll-interval` | number (ms) | `30000` | yes | Polling interval when `live` is set |
| `today-marker` | boolean | `true` | yes | Shows a "today" marker on the time axis |
| `max-lanes` | number | `20` | yes | Maximum number of branch lanes before virtual scroll activates |
| `locale` | string | `""` | yes | BCP 47 locale for axis tick formatting; defaults to `navigator.language` |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `data` | `BranchGraphData` | Full graph data object: `{ branches, commits, merges, markers, phases }` |
| `selectedNode` | `CommitNode \| null` | Currently selected commit node |
| `selectedMarker` | `Marker \| null` | Currently selected milestone marker |
| `visibleRange` | `{ start: Date, end: Date }` | Current visible time window after zoom/pan |
| `collapsedLanes` | `Set<string>` | Branch names whose lanes are currently collapsed |

## 7. Slots

| Slot | Description |
|------|-------------|
| `(default)` | Fallback accessible content (e.g. `<table>`) rendered before upgrade |
| `legend` | Custom legend markup replacing the auto-generated legend |
| `detail-panel` | Custom detail panel template; receives selected node data via a property |
| `empty` | Content shown when `data.branches` is empty |
| `loading` | Content shown while the adapter fetch is in progress |
| `error` | Content shown when the adapter fetch fails |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-node-select` | `{ node: CommitNode, branch: string }` | yes | no | Fired when a commit node is selected |
| `mj-node-deselect` | `{ node: CommitNode }` | yes | no | Fired when a commit node is deselected |
| `mj-marker-select` | `{ marker: Marker }` | yes | no | Fired when a milestone marker is selected |
| `mj-lane-collapse` | `{ branch: string, collapsed: boolean }` | yes | no | Fired when a branch lane is collapsed or expanded |
| `mj-range-change` | `{ start: string, end: string }` | yes | no | Fired when the visible time window changes via zoom/pan |
| `mj-data-load` | `{ branches: number, commits: number }` | yes | no | Fired after a successful data fetch |
| `mj-error` | `{ message: string, cause: unknown }` | yes | no | Fired when the data-source adapter returns an error |

## 9. CSS parts & custom properties

**Parts:**
- `::part(time-axis)` — the horizontal or vertical ruler
- `::part(lane)` — individual branch swim-lane container
- `::part(lane-label)` — branch name label at the start of a lane
- `::part(commit-node)` — individual commit circle/diamond
- `::part(merge-edge)` — SVG arc or line for merge/branch edges
- `::part(phase-band)` — colored background span for a phase
- `::part(milestone-marker)` — vertical marker line and label
- `::part(detail-panel)` — node/marker detail overlay
- `::part(legend)` — legend container
- `::part(toolbar)` — zoom/pan control bar

**Custom properties:**
- `--mj-bg-graph` — canvas background color
- `--mj-lane-height` — height of a single branch lane (default `48px`)
- `--mj-lane-gap` — vertical gap between lanes (default `8px`)
- `--mj-commit-radius` — commit node radius (default `6px`)
- `--mj-merge-edge-color` — merge arc stroke color
- `--mj-marker-release-color` — milestone marker color for `type=release`
- `--mj-marker-freeze-color` — milestone marker color for `type=freeze`
- `--mj-marker-tag-color` — milestone marker color for `type=tag`
- `--mj-phase-opacity` — opacity of phase band fills (default `0.12`)
- `--mj-axis-tick-color` — tick label color

## 10. States

- **default** — graph renders with all lanes and the visible time window.
- **loading** — skeleton lanes shown; `aria-busy="true"` on root; loading slot visible.
- **empty** — no branches; empty slot shown; `aria-label` updated to indicate empty.
- **error** — error slot shown; previous data cleared; error event fired.
- **node-selected** — selected commit node highlighted; `aria-selected="true"` on node element; detail panel open.
- **marker-selected** — milestone marker highlighted; detail panel shows marker metadata.
- **lane-collapsed** — lane row reduced to label only; collapse button `aria-expanded="false"`.
- **zoomed** — `visibleRange` narrower than full date range; zoom-reset control becomes visible.
- **live-polling** — pulsing indicator in toolbar; data refreshed at `poll-interval`.

## 11. Behavior & interactions

The time-axis utility manages zoom (pinch/scroll wheel/button) and pan (drag/
keyboard). On data load the visible range defaults to `start-date`/`end-date`
attributes; if neither is set the range spans from the earliest commit to the
latest marker. Commit nodes receive pointer and keyboard focus; clicking or
pressing Enter/Space opens the detail panel and fires `mj-node-select`. Merge
edges are decorative SVG paths without focusable targets. Lane collapse toggles
are `<button>` elements in the lane label. Phase bands are rendered as SVG
`<rect>` elements behind lane content and carry `aria-hidden="true"`. The
rendering adapter is injected via the `adapter` attribute; the component calls
`adapter.fetch(src, { start, end })` and receives a `BranchGraphData` object.
When `live` is set, the adapter is polled and the graph diff-updates in place
without full re-render.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Tab` | Move focus between interactive elements: toolbar controls, lane collapse buttons, commit nodes, markers |
| `Arrow Left` / `Arrow Right` | Pan the time axis when toolbar has focus; move focus between commits in a lane when a node has focus |
| `Arrow Up` / `Arrow Down` | Move focus between branch lanes |
| `+` / `-` | Zoom in / zoom out on the time axis |
| `Enter` / `Space` | Select the focused commit node or marker; toggle lane collapse on collapse button |
| `Escape` | Deselect node/marker; close detail panel |
| `Home` / `End` | Jump focus to first / last commit node in the current lane |
| `0` | Reset zoom to the full date range |

## 13. Accessibility

- Root element role: `img` with `aria-label` summarizing the graph
  (e.g. "Branch graph: 5 branches, 128 commits, 4 milestones").
- Commit nodes: `role="button"` with `aria-label` = "Commit {sha7}: {message}, {date}".
- Milestone markers: `role="button"` with `aria-label` = "{name} {type} marker, {date}".
- Lane collapse buttons: `aria-expanded` reflects open/collapsed state;
  `aria-controls` points to the lane content ID.
- Detail panel: `role="dialog"` with `aria-modal="false"` (non-modal);
  `aria-labelledby` points to the node/marker heading inside.
- Live-polling updates: announced via the live-region/announcement service as
  "Graph updated: {n} new commits" with `aria-live="polite"`.
- Accessible data table: a visually hidden `<table>` with columns Branch, SHA,
  Message, Author, Date, Tags is always present; visible via "Show data table"
  disclosure button above the graph.
- Color is supplemented by shape (circles = commits, diamonds = tags) and
  pattern fills on phase bands.
- Respects `prefers-reduced-motion` by disabling pan/zoom animation.

## 14. Form participation

N/A — this component is not an input control and does not participate in forms.

## 15. Internationalization & RTL

- Axis tick labels use `Intl.DateTimeFormat` with the `locale` attribute.
- Branch names, commit messages, and marker names are rendered verbatim (consumer
  responsibility for locale).
- All UI strings (zoom controls, collapse label, empty/loading/error messages)
  are overridable via attributes: `label-zoom-in`, `label-zoom-out`,
  `label-reset-zoom`, `label-collapse`, `label-expand`, `label-loading`,
  `label-empty`, `label-error`.
- RTL: when `dir="rtl"` the time axis flows right-to-left; lane labels appear on
  the right; the horizontal layout mirrors correctly via CSS logical properties.

## 16. Progressive enhancement / SSR

Server renders a `<table>` or `<ol>` of branches and commits inside the default
slot. Before the script loads, this table is the only content and is fully
accessible. On upgrade the component hides the slot content visually (it remains
accessible via the accessible data table toggle), initializes the rendering
adapter, and draws the graph canvas without layout shift (the host element's
`min-height` is set by a server-side attribute `height-hint`).

## 17. Dependencies

- §6 time-axis utility (zoom, pan, today marker, tick labels)
- §6 milestone/marker model (named markers with date, type, phase band)
- §6 data-source adapter interface (adapter keys: `static`, `github`, `gitlab`,
  `gitea`)
- §6 registry + base element helper
- §6 design-token stylesheet
- §6 live-region/announcement service
- §6 localization/formatting hook (`Intl.DateTimeFormat`)
- §5.9 pluggable rendering adapter (SVG or Canvas; injected, not bundled)

## 18. Edge cases & error handling

- **Empty repo** — no branches or commits: empty slot shown; accessible label
  updated to "No branch data available".
- **Single branch** — single lane renders without merge edges.
- **Overlapping commits** — commits on the same date are stacked or jittered
  within the lane.
- **Very long branch names** — lane labels truncate with `title` tooltip.
- **Adapter fetch failure** — error slot shown; `mj-error` fired with message;
  stale data retained if previously loaded.
- **`start-date` after `end-date`** — component logs a warning and swaps them.
- **More than `max-lanes` branches** — virtual scroll activates; offscreen lanes
  are not rendered; lane count announced.
- **Missing `src` with `adapter` != `"static"`** — `mj-error` fired immediately
  with "No src provided for adapter".
- **Zero-length phase band** — phase bands where start equals end are omitted.

## 19. Acceptance criteria

- [ ] Renders branch lanes, commit nodes, and merge edges from a static `data`
      property without a network request.
- [ ] Milestone markers and phase bands appear at correct time positions.
- [ ] Lane collapse button toggles lane visibility and fires `mj-lane-collapse`.
- [ ] Zoom and pan adjust `visibleRange` and reposition all nodes/markers.
- [ ] Selecting a commit node fires `mj-node-select` and opens the detail panel.
- [ ] Keyboard navigation moves focus through nodes, lanes, and markers per §12.
- [ ] Accessible data table is present in the DOM and contains all commits.
- [ ] `aria-label` on root reflects current branch and commit counts.
- [ ] Live polling fires `mj-data-load` and updates graph without full re-render.
- [ ] `locale` attribute changes axis tick labels without a page reload.
- [ ] RTL layout mirrors correctly when `dir="rtl"`.
- [ ] `prefers-reduced-motion` disables animation.
- [ ] axe automated accessibility check passes with zero violations.
- [ ] Empty, loading, and error states display the correct slots.
- [ ] `max-lanes` overflow activates virtual scroll.

## 20. Open questions

- Should merge edges support hover-highlight of the entire merge chain (all
  commits between branch point and merge commit), or only the single edge?
- What is the maximum practical commit count before the rendering adapter must
  switch from SVG to Canvas for performance?
- Should the `github` adapter support GitHub Enterprise Server endpoints, and
  if so, what is the base-URL attribute name?
- Is a "compare branches" mode (diff overlay between two selected branches)
  in scope for P3 or deferred?
