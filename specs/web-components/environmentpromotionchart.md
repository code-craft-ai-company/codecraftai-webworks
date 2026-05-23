# Environment Promotion Chart Spec

- **Tag:** `<mj-env-promotion-chart>`
- **Class / file:** `EnvPromotionChart` / `envpromotionchart.js`
- **Category:** Project-management & configuration-management charts
- **Primary or Variant:** Variant of `<mj-pipeline-chart>`
- **Synonyms covered:** Environment promotion chart, Deployment promotion chart,
  Artifact promotion pipeline
- **Phase:** P3
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-env-promotion-chart>` renders the progression of a software artifact
(build, container image, or package) across deployment environments
(dev → staging → production, or a custom sequence) with approval gates between
each promotion step. It shows the current version deployed in each environment,
the promotion history, and pending gate decisions. It is implemented as a
specialized variant of `<mj-pipeline-chart>` with environment-centric data
semantics and visual conventions.

## 2. When to use / when not to use

**Use** when teams need to visualize which artifact version is deployed where and
what approvals are outstanding. **Do not use** for CI build-stage flows within a
single environment (use `<mj-pipeline-chart>`) or for a high-level grid of many
pipelines (use `<mj-build-status-board>`). Nearest alternative:
`<mj-pipeline-chart>` for generic stage flows.

## 3. Anatomy

- **Environment columns** — one column per environment (dev, staging, uat, prod);
  ordered left to right in promotion order.
- **Artifact row** — a single horizontal track showing the artifact's current
  version in each environment column, with promotion edges between them.
- **Version badge** — shows the artifact version (semver or SHA) currently
  deployed in each environment.
- **Environment health indicator** — traffic-light icon (healthy/degraded/down)
  with a text label; not color-only.
- **Promotion edge** — directed arrow between adjacent environment columns;
  labeled with promotion date/time.
- **Approval gate** — diamond node between environments requiring a manual or
  automated approval before promotion.
- **Gate controls** — approve/reject buttons on pending gates (when not readonly).
- **Promotion history panel** — expandable list of past promotions per environment.
- **Accessible summary list** — `<ol>` of environments with current version,
  health, and gate status.

## 4. Variants & modes

| Mode / Variant | Attribute | Behavior |
|---|---|---|
| Horizontal | `orientation="horizontal"` (default) | Environments flow left to right |
| Vertical | `orientation="vertical"` | Environments stack top to bottom |
| Read-only | `readonly` (boolean, default) | No gate actions |
| Live | `live` (boolean) | Polls or streams for version/gate updates |
| Compact | `density="compact"` | Version badge only; no health label text |
| Full | `density="full"` (default) | Full version badge, health text, and dates |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `src` | string | `""` | yes | URL for the data-source adapter |
| `adapter` | string | `"static"` | yes | Adapter key: `"static"`, `"github-actions"`, `"argocd"`, `"spinnaker"` |
| `orientation` | `"horizontal"` \| `"vertical"` | `"horizontal"` | yes | Layout direction |
| `density` | `"compact"` \| `"full"` | `"full"` | yes | Detail level |
| `readonly` | boolean | `false` | yes | Prevents gate approve/reject actions |
| `live` | boolean | `false` | yes | Enables live updates via polling or SSE |
| `poll-interval` | number (ms) | `30000` | yes | Polling interval in live mode |
| `artifact-id` | string | `""` | yes | Artifact identifier forwarded to the adapter |
| `locale` | string | `""` | yes | BCP 47 locale for date/time formatting |
| `label-loading` | string | `"Loading promotion chart…"` | yes | Loading message |
| `label-empty` | string | `"No environments configured."` | yes | Empty message |
| `label-error` | string | `"Failed to load promotions."` | yes | Error message |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `data` | `PromotionData` | `{ environments: Environment[], gates: Gate[], promotions: PromotionEvent[] }` |
| `selectedEnvironment` | `Environment \| null` | Currently selected environment column |
| `selectedGate` | `Gate \| null` | Currently selected gate node |
| `pendingGates` | `Gate[]` | Gates awaiting approval action (read-only computed) |

## 7. Slots

| Slot | Description |
|------|-------------|
| `(default)` | Fallback `<ol>` rendered before upgrade |
| `environment-detail` | Custom detail panel for a selected environment |
| `gate-detail` | Custom gate approval UI |
| `history-panel` | Custom promotion history content |
| `empty` | Shown when no environments are configured |
| `loading` | Shown during adapter fetch |
| `error` | Shown on adapter failure |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-environment-select` | `{ environment: Environment }` | yes | no | Environment column activated |
| `mj-environment-deselect` | `{}` | yes | no | Selection cleared |
| `mj-gate-action` | `{ gate: Gate, action: "approve" \| "reject", actor: string }` | yes | yes | Gate approve/reject triggered; cancelable |
| `mj-promotion-update` | `{ environment: Environment, version: string }` | yes | no | A version change detected in live mode |
| `mj-data-load` | `{ environments: number, pendingGates: number }` | yes | no | Data loaded |
| `mj-error` | `{ message: string, cause: unknown }` | yes | no | Adapter error |

## 9. CSS parts & custom properties

**Parts:**
- `::part(environment-column)` — individual environment column container
- `::part(environment-header)` — environment name header
- `::part(version-badge)` — current version label
- `::part(health-indicator)` — traffic-light health icon + text
- `::part(promotion-edge)` — arrow between adjacent environments
- `::part(gate-node)` — approval gate diamond
- `::part(gate-controls)` — approve/reject button container
- `::part(history-panel)` — promotion history expandable area
- `::part(live-indicator)` — pulsing live badge

**Custom properties:**
- `--mj-env-column-width` — environment column width (default `180px`)
- `--mj-env-column-gap` — gap between columns (default `48px`)
- `--mj-health-healthy-color` — healthy indicator color
- `--mj-health-degraded-color` — degraded indicator color
- `--mj-health-down-color` — down indicator color
- `--mj-gate-size` — gate diamond size (default `32px`)
- `--mj-gate-pending-color` — pending gate accent color
- `--mj-promotion-edge-color` — promotion arrow stroke color
- `--mj-version-badge-bg` — version badge background

## 10. States

- **loading** — `aria-busy="true"`; loading slot shown.
- **empty** — empty slot shown.
- **error** — error slot shown.
- **environment-selected** — column highlighted; detail panel open.
- **gate-pending** — gate shows approve/reject controls; `data-state="pending"`.
- **gate-approved** — gate shows approved icon + actor name; arrow to next env active.
- **gate-rejected** — gate shows rejected icon; promotion blocked.
- **health-healthy** — green check icon + "Healthy" text on environment header.
- **health-degraded** — yellow warning icon + "Degraded" text.
- **health-down** — red X icon + "Down" text; column visually de-emphasized.
- **live-active** — live-indicator pulsing; `aria-live` region active.

## 11. Behavior & interactions

On load the adapter returns `PromotionData` for the given `artifact-id`.
Environments are rendered in the order provided by `data.environments`. Gates
are placed between adjacent environment pairs where `Gate.fromEnv` and
`Gate.toEnv` match. Clicking an environment column fires `mj-environment-select`
and opens the environment detail panel showing current version, health status,
last promoted date, and a promotion history list. Gate approve/reject buttons
fire `mj-gate-action` (cancelable for confirmation dialogs). In live mode the
adapter is polled or streamed; version changes fire `mj-promotion-update` and
patch the affected environment column without full re-render.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Tab` | Move focus between environment columns, gate nodes, gate action buttons, toolbar |
| `Arrow Left` / `Arrow Right` | Move focus between environment columns |
| `Enter` / `Space` | Select focused environment; activate gate button |
| `Escape` | Deselect; close detail panel |
| `Home` / `End` | Focus first / last environment |

## 13. Accessibility

- Root: `role="img"` with `aria-label` = "Environment promotion chart:
  {artifact-id}, {n} environments, {m} pending gates".
- Environment columns: `role="button"` with `aria-label` = "{env name},
  version: {version}, health: {healthy|degraded|down}, gate: {status}".
- Gate nodes: `role="group"` `aria-label` = "Approval gate between {fromEnv}
  and {toEnv}, status: {pending|approved|rejected}".
- Gate buttons: `<button>` with `aria-label` = "Approve promotion to {toEnv}"
  and "Reject promotion to {toEnv}".
- Health indicators: icon + text label; icon has `aria-hidden="true"`.
- Live update announcements: "{env name} updated to version {version}" via
  live-region/announcement service with `aria-live="polite"`.
- Pending gate announcements (live mode): "Approval required for {toEnv}" with
  `aria-live="assertive"`.
- Accessible summary list: `<ol>` with `<li>` per environment: name, version,
  health, gate status.

## 14. Form participation

N/A.

## 15. Internationalization & RTL

- Promotion dates use `Intl.DateTimeFormat` with `locale` attribute.
- All UI strings overridable: `label-loading`, `label-empty`, `label-error`,
  `label-approve`, `label-reject`, `label-healthy`, `label-degraded`,
  `label-down`, `label-pending`, `label-approved`, `label-rejected`,
  `label-version`, `label-show-list`.
- RTL: environment columns flow right-to-left; promotion arrows mirror; detail
  panels positioned appropriately.

## 16. Progressive enhancement / SSR

Server renders an `<ol>` of environments with version and health inside the
default slot. On upgrade the component hides the list visually (re-accessible
via toggle) and draws the promotion chart without layout shift.

## 17. Dependencies

- `<mj-pipeline-chart>` (base variant; shared stage/gate rendering logic)
- §6 data-source adapter interface (adapter keys: `static`, `github-actions`,
  `argocd`, `spinnaker`)
- §6 registry + base element helper
- §6 design-token stylesheet
- §6 live-region/announcement service
- §6 localization/formatting hook (`Intl.DateTimeFormat`)
- §5.9 pluggable rendering adapter (SVG; shared with PipelineChart)

## 18. Edge cases & error handling

- **Single environment** — no promotion edge; version badge shown alone.
- **Gate with no pending approvers** — gate shown in "auto" state; approval
  fires automatically on data refresh.
- **Health data unavailable** — health indicator shows "Unknown" state with
  dashed border; not an error.
- **Version mismatch across environments** — all versions shown; mismatch is
  expected and not flagged as an error.
- **Adapter failure** — error slot shown; stale data retained.
- **Live update collision** — if two `mj-promotion-update` events fire for the
  same environment within one poll cycle, the last value wins; logged at debug.

## 19. Acceptance criteria

- [ ] Environments render in the order from `data.environments`.
- [ ] Version badges show the current deployed version per environment.
- [ ] Health indicators show icon + text (not color alone).
- [ ] Approval gates render with approve/reject buttons when `!readonly`.
- [ ] Activating an environment column fires `mj-environment-select`.
- [ ] Gate action fires `mj-gate-action` with correct `action` value.
- [ ] `mj-gate-action` is cancelable; cancellation reverts gate to pending state.
- [ ] Live mode fires `mj-promotion-update` on version change.
- [ ] Accessible summary list present in DOM.
- [ ] RTL layout mirrors correctly.
- [ ] axe automated accessibility check passes with zero violations.

## 20. Open questions

- Should the `argocd` adapter expose sync status (synced/out-of-sync/unknown)
  as a fourth health state alongside healthy/degraded/down?
- Is rollback (promoting a previous artifact version) an action on the
  environment detail panel, or out of scope for P3?
