# Pipeline Chart Spec

- **Tag:** `<mj-pipeline-chart>`
- **Class / file:** `PipelineChart` / `pipelinechart.js`
- **Category:** Project-management & configuration-management charts
- **Primary or Variant:** Primary
- **Synonyms covered:** Deployment pipeline, CI/CD pipeline, Build pipeline
- **Phase:** P3
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-pipeline-chart>` renders a CI/CD pipeline as an ordered or parallel stage
flow diagram. It shows stage status, gate/approval nodes, fan-out and fan-in
edges, and supports live status updates. The component replaces static pipeline
diagrams with an interactive, accessible visualization driven by CI API data or
static config.

## 2. When to use / when not to use

**Use** to visualize a CI/CD or deployment pipeline: build → test → security
scan → deploy stages with gating logic and real-time status. **Do not use** for
task scheduling over time (use `<mj-gantt-chart>`), artifact promotion across
environments (use `<mj-env-promotion-chart>`), or branching history (use
`<mj-branch-graph>`). Nearest alternative: `<mj-build-status-board>` for a
high-level grid of many pipelines.

## 3. Anatomy

- **Stage nodes** — boxes representing pipeline stages; contain name, status
  icon+text, duration, and an expand trigger for logs.
- **Gate nodes** — diamond-shaped approval or quality-gate nodes between stages.
- **Edges** — directed arrows connecting stages and gates; fan-out produces
  multiple parallel edges; fan-in converges them.
- **Status legend** — maps status tokens to icons and labels.
- **Log panel** — scrollable text panel revealed on stage expand.
- **Accessible list** — visually hidden `<ol>` listing all stages in order with
  status and duration; always present in the DOM.
- **Live-status indicator** — pulsing badge when `live` is active.

## 4. Variants & modes

| Mode / Variant | Attribute | Behavior |
|---|---|---|
| Horizontal | `orientation="horizontal"` (default) | Stages flow left to right |
| Vertical | `orientation="vertical"` | Stages flow top to bottom |
| Compact | `density="compact"` | Stage boxes show icon and name only |
| Full | `density="full"` (default) | Stage boxes include duration and actor |
| Read-only | `readonly` (boolean) | No approval actions; logs are still viewable |
| Live | `live` (boolean) | SSE or polling via adapter at `poll-interval` ms |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `src` | string | `""` | yes | URL for the CI data-source adapter |
| `adapter` | string | `"static"` | yes | Adapter key: `"static"`, `"github-actions"`, `"gitlab-ci"`, `"jenkins"` |
| `orientation` | `"horizontal"` \| `"vertical"` | `"horizontal"` | yes | Layout direction |
| `density` | `"compact"` \| `"full"` | `"full"` | yes | Detail level on stage nodes |
| `readonly` | boolean | `false` | yes | Prevents approval/gate actions |
| `live` | boolean | `false` | yes | Enables live status updates |
| `poll-interval` | number (ms) | `15000` | yes | Polling interval when `live` is set and SSE unavailable |
| `run-id` | string | `""` | yes | Pipeline run identifier forwarded to the adapter |
| `locale` | string | `""` | yes | BCP 47 locale for duration/timestamp formatting |
| `label-loading` | string | `"Loading pipeline…"` | yes | Overrides loading message |
| `label-empty` | string | `"No pipeline data."` | yes | Overrides empty message |
| `label-error` | string | `"Failed to load pipeline."` | yes | Overrides error message |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `data` | `PipelineData` | Full pipeline object: `{ id, stages, gates, edges, status, startedAt, finishedAt }` |
| `selectedStage` | `StageNode \| null` | Currently selected/expanded stage |
| `overallStatus` | `"pending" \| "running" \| "passed" \| "failed" \| "cancelled"` | Computed from stage statuses |

## 7. Slots

| Slot | Description |
|------|-------------|
| `(default)` | Fallback accessible `<ol>` rendered before upgrade |
| `stage-detail` | Custom template for the log/detail panel |
| `gate-detail` | Custom template for gate approval UI |
| `empty` | Shown when pipeline has no stages |
| `loading` | Shown during adapter fetch |
| `error` | Shown on adapter failure |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-stage-select` | `{ stage: StageNode }` | yes | no | Stage node clicked/activated |
| `mj-stage-deselect` | `{}` | yes | no | Selection cleared |
| `mj-gate-approve` | `{ gate: GateNode, action: "approve" \| "reject" }` | yes | yes | Gate action fired; cancelable to intercept |
| `mj-status-change` | `{ stageId: string, previous: string, current: string }` | yes | no | A stage status changed (live mode) |
| `mj-data-load` | `{ stages: number, runId: string }` | yes | no | After a successful data fetch |
| `mj-error` | `{ message: string, cause: unknown }` | yes | no | Adapter error |

## 9. CSS parts & custom properties

**Parts:**
- `::part(stage-node)` — stage box
- `::part(gate-node)` — approval/gate diamond
- `::part(edge)` — directed arrow between nodes
- `::part(log-panel)` — stage log scroll container
- `::part(status-legend)` — legend container
- `::part(live-indicator)` — pulsing live badge
- `::part(toolbar)` — any zoom/layout controls

**Custom properties:**
- `--mj-stage-width` — stage node width (default `140px`)
- `--mj-stage-gap` — horizontal gap between stages (default `32px`)
- `--mj-status-pending-color` — pending stage border/icon color
- `--mj-status-running-color` — running stage color
- `--mj-status-passed-color` — passed stage color
- `--mj-status-failed-color` — failed stage color
- `--mj-status-skipped-color` — skipped stage color
- `--mj-gate-size` — gate diamond size (default `32px`)
- `--mj-edge-color` — edge arrow color
- `--mj-log-panel-max-height` — max height of log panel (default `320px`)

## 10. States

- **loading** — `aria-busy="true"` on root; loading slot shown.
- **empty** — empty slot shown; accessible label updated.
- **error** — error slot shown; `mj-error` fired.
- **running** — one or more stages have status `running`; live-indicator pulsing.
- **passed** — all stages passed; overall status announced.
- **failed** — one or more stages failed; failed stage highlighted with icon+color
  plus a text badge "Failed" (never color-only).
- **stage-selected** — log panel open; `aria-expanded="true"` on stage trigger.
- **gate-pending** — gate node shows approve/reject controls (when not readonly).

## 11. Behavior & interactions

On load the adapter fetches `PipelineData` from `src`. Stages are laid out by
the rendering adapter in topological order; parallel stages are placed at the
same horizontal (or vertical) position. Fan-out edges diverge from a single
source node; fan-in edges converge into a single target. Clicking or pressing
Enter/Space on a stage node toggles the log panel and fires `mj-stage-select`.
Gate nodes show approve/reject buttons when the pipeline is not readonly; firing
`mj-gate-approve` allows the host application to intercept and confirm before
proceeding. When `live` is set the adapter streams or polls for status changes
and fires `mj-status-change` per changed stage; the DOM patches only the
affected node without a full re-render. Duration values use `Intl.RelativeTimeFormat`
and `Intl.DurationFormat` where available.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Tab` | Move focus between stage nodes, gate nodes, and toolbar controls |
| `Arrow Right` / `Arrow Down` | Move focus to the next stage node in flow order |
| `Arrow Left` / `Arrow Up` | Move focus to the previous stage node |
| `Enter` / `Space` | Toggle log panel on focused stage; activate gate button |
| `Escape` | Close open log panel; deselect stage |
| `Home` | Focus the first stage node |
| `End` | Focus the last stage node |

## 13. Accessibility

- Root element: `role="img"` with `aria-label` summarizing pipeline state
  (e.g. "CI pipeline: 6 stages, status: failed").
- Stage nodes: `role="button"` with `aria-expanded` (log panel open/closed);
  `aria-label` = "{name} stage, status: {status}, duration: {duration}".
- Gate nodes: `role="group"` with `aria-label` = "{name} approval gate";
  approve/reject controls are `<button>` elements with descriptive accessible names.
- Status is conveyed by icon shape + text label, not color alone.
- Log panel: `role="log"` with `aria-label` = "{stage name} logs"; `aria-live="off"`.
- Live-status changes announced via live-region/announcement service:
  "{stage name} status changed to {status}" with `aria-live="polite"`.
- Accessible `<ol>` lists every stage in DOM order; hidden visually with a
  "Show accessible list" disclosure toggle above the chart.
- Minimum touch target size on stage and gate interactive areas: 44×44 px.

## 14. Form participation

N/A — this component is not an input control.

## 15. Internationalization & RTL

- Duration/timestamp labels use `Intl.RelativeTimeFormat` and `Intl.DateTimeFormat`
  with the `locale` attribute.
- All static UI strings overridable via attributes (see §5 `label-*` attributes).
- Additional localizable strings: `label-approve`, `label-reject`, `label-view-logs`,
  `label-collapse-logs`.
- RTL: horizontal layout mirrors left-to-right arrow direction; CSS logical
  properties used throughout.

## 16. Progressive enhancement / SSR

Server renders an `<ol>` of stages with name and status text inside the default
slot. Before the script loads this list is the entire accessible content. On
upgrade the component hides the list visually (the accessible list toggle makes
it re-accessible), then draws the graph diagram without layout shift using a
`height-hint` attribute.

## 17. Dependencies

- §6 data-source adapter interface (adapter keys: `static`, `github-actions`,
  `gitlab-ci`, `jenkins`)
- §6 registry + base element helper
- §6 design-token stylesheet
- §6 live-region/announcement service
- §6 localization/formatting hook (`Intl.DateTimeFormat`, `Intl.RelativeTimeFormat`)
- §5.9 pluggable rendering adapter (SVG layout engine; injected, not bundled)

## 18. Edge cases & error handling

- **Single stage** — no edges rendered; stage shown centered.
- **All stages skipped** — chart renders with all nodes in skipped state; overall
  status reflects "skipped".
- **Circular dependency in edge data** — detected on load; `mj-error` fired with
  "Circular dependency detected in pipeline edges".
- **Stage name overflow** — truncated in node box with `title` tooltip.
- **Adapter fetch fails** — error slot shown; stale data retained if present.
- **Gate action rejected by host** — `mj-gate-approve` cancelable; UI reverts
  gate to pending state if event is cancelled.
- **More than 50 stages** — virtual panning activates; offscreen nodes not
  rendered until scrolled into view.
- **Missing `run-id`** — adapter fetches the most recent run; behavior documented.

## 19. Acceptance criteria

- [ ] Renders stages, gates, and edges from a static `data` property.
- [ ] Status icons and text labels are present for all five statuses.
- [ ] Selecting a stage opens the log panel and fires `mj-stage-select`.
- [ ] Gate approve/reject buttons fire `mj-gate-approve` with correct detail.
- [ ] Keyboard navigation moves focus in topological order per §12.
- [ ] Live status updates patch only changed nodes without full re-render.
- [ ] `mj-status-change` fires for each changed stage in live mode.
- [ ] Accessible `<ol>` is present and lists all stages with statuses.
- [ ] `aria-label` on root reflects stage count and overall status.
- [ ] RTL layout correctly mirrors arrow directions.
- [ ] `prefers-reduced-motion` disables transition animations.
- [ ] axe automated accessibility check passes with zero violations.
- [ ] Empty, loading, and error slots display correctly.

## 20. Open questions

- Should the `github-actions` adapter support GitHub Enterprise Server base URLs?
- Is a "re-run failed stages" action button in scope, and if so, does it fire
  a separate event or reuse `mj-gate-approve`?
- Should the log panel support ANSI color codes in terminal output?
- Is a "waterfall" timing variant (stages on a time axis like Gantt) needed or
  is that a separate component?
