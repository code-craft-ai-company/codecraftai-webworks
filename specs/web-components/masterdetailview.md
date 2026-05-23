# Master-Detail View Spec

- **Tag:** `<mj-master-detail>`
- **Class / file:** `MjMasterDetail` / `mjmasterdetail.js`
- **Category:** Tables, lists & structured data
- **Primary or Variant:** Primary
- **Synonyms covered:** Master-detail view, List-detail view, Detail view, Split view
- **Phase:** P2
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-master-detail>` is a split-panel layout component that keeps a navigable
master list (or table) synchronized with a contextual detail view. Selecting an
item in the master panel loads and displays its details in the detail panel. On
narrow viewports the layout collapses to a stacked navigation pattern — master
and detail panels are shown one at a time with explicit back navigation. The
component is the canonical "email client" / "settings panel" / "record browser"
pattern.

## 2. When to use / when not to use
**Use** when the user needs to browse a list of items and view/edit one item's
details at a time, and where keeping both panels simultaneously visible on wide
screens improves efficiency. **Do not use** for simple navigation menus (use
`<mj-side-nav>`), for complex multi-pane editors (use `<mj-app-shell>`), or for
data tables without a rich per-row detail — use `<mj-data-table>` with a row
expand pattern instead.

## 3. Anatomy
- **Root** — `<div>` with `role="group"` and `aria-label`; flex/grid container for the two panels.
- **Master panel** — `<section>` with `role="navigation"` or `role="list"` depending on context; hosts the item list or `<mj-data-table>`.
- **Divider** — resizable `<div role="separator">` between panels; draggable; keyboard-resizable.
- **Detail panel** — `<section>` with `aria-label` updated to the selected item's name; hosts the detail content slot.
- **Back button** — visible only in stacked/mobile mode; returns from detail to master.
- **Empty-detail state** — shown in the detail panel when no item is selected.

## 4. Variants & modes
| Variant | `layout` value | Behavior |
|---------|---------------|----------|
| Side-by-side | `side-by-side` (default) | Master and detail shown simultaneously; resizable divider. |
| Stacked | `stacked` | Master and detail each fill the container; only one shown at a time. |
| Auto | `auto` | Side-by-side above `--mj-md-breakpoint`; stacked below. |

Master panel content type via `master-type`:
- `list` (default) — hosts a `<mj-list>` or slotted list items.
- `table` — hosts a `<mj-data-table>`.
- `custom` — caller provides full master panel content via slot.

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `layout` | `side-by-side\|stacked\|auto` | `auto` | yes | Panel layout strategy. |
| `master-type` | `list\|table\|custom` | `list` | yes | Type of content in the master panel. |
| `selected-key` | string | `""` | yes | Key of the currently selected item; setting navigates to that item's detail. |
| `master-width` | string | `"320px"` | yes | CSS width of the master panel (side-by-side mode). |
| `resizable` | boolean | true | yes | Whether the divider can be dragged to resize panels. |
| `loading-detail` | boolean | false | yes | Shows skeleton in detail panel; `aria-busy="true"` on detail section. |
| `back-label` | string | `"Back"` | yes | Accessible label for the back button in stacked mode. |
| `detail-label` | string | `"Detail"` | yes | Base `aria-label` for the detail panel; appended with selected item name. |
| `master-label` | string | `"List"` | yes | `aria-label` for the master panel. |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `items` | `MasterItem[]` | `{ key: string, label: string, meta?: string, data?: unknown }` — drives the master list when `master-type="list"`. |
| `columns` | `ColumnDef[]` | Column definitions forwarded to the internal `<mj-data-table>` when `master-type="table"`. |
| `dataSource` | `DataSourceAdapter` | Forwarded to the internal `<mj-data-table>` or list. |
| `detailDataSource` | `(key: string) => Promise<unknown>` | Async function that resolves detail data for a given item key; result passed to `slot="detail"` via `dataset`. |

## 7. Slots
| Slot | Description |
|------|-------------|
| `master` | Full custom master panel content (used when `master-type="custom"`). |
| `master-item` | Template cloned per item in list mode; receives `data-key`, `data-label`. |
| `detail` | Detail panel content; the host element receives `data-selected-key` when an item is selected. |
| `detail-empty` | Content shown in the detail panel when no item is selected. |
| `detail-loading` | Content shown while `loading-detail` is true. |
| `detail-error` | Content shown when `detailDataSource` rejects. |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-item-select` | `{ key: string, item: MasterItem }` | true | true | User selected an item in the master panel; cancel to prevent navigation. |
| `mj-detail-load` | `{ key: string, data: unknown }` | true | false | Detail data resolved from `detailDataSource`. |
| `mj-detail-error` | `{ key: string, error: Error }` | true | false | Detail data fetch failed. |
| `mj-panel-resize` | `{ masterWidth: number }` | true | false | Divider was dragged; new master panel width reported. |
| `mj-back` | `{}` | true | false | User activated the back button in stacked mode. |
| `mj-layout-change` | `{ layout: 'side-by-side'\|'stacked' }` | true | false | Layout switched at the `--mj-md-breakpoint` boundary. |

## 9. CSS parts & custom properties
**Parts:** `root`, `master-panel`, `divider`, `detail-panel`, `back-button`,
`detail-empty`, `detail-loading`, `detail-error`.

| Custom property | Default | Purpose |
|----------------|---------|---------|
| `--mj-md-master-width` | `320px` | Master panel width in side-by-side mode. |
| `--mj-md-master-min-width` | `200px` | Minimum master panel width during resize. |
| `--mj-md-master-max-width` | `60%` | Maximum master panel width during resize. |
| `--mj-md-breakpoint` | `640px` | Container width below which layout switches to stacked. |
| `--mj-md-divider-width` | `4px` | Width of the resizable divider. |
| `--mj-md-divider-color` | `token(--mj-color-border)` | Divider color. |
| `--mj-md-selected-item-bg` | `token(--mj-color-selection-subtle)` | Selected item background in master list. |
| `--mj-md-detail-bg` | `token(--mj-color-surface)` | Detail panel background. |

## 10. States
- **no-selection** — `selected-key` is empty; `slot="detail-empty"` shown; detail panel `aria-label="{detail-label}"`.
- **item-selected** — selected item highlighted in master (`aria-selected="true"`); detail panel content shown; `aria-label` includes item label.
- **loading-detail** — `aria-busy="true"` on detail section; `slot="detail-loading"` shown.
- **error-detail** — `slot="detail-error"` shown; retry available.
- **stacked-master** — in stacked mode, master panel is the active view.
- **stacked-detail** — in stacked mode, detail panel is the active view; back button visible.
- **resizing** — divider being dragged; cursor `col-resize`; live region announces width.

## 11. Behavior & interactions
**Selection and detail loading:** When the user selects an item (click, `Enter`,
or `Space`), `mj-item-select` fires. If not canceled, `selected-key` updates,
the master item receives `aria-selected="true"`, and the detail panel shows
`slot="detail-loading"`. If `detailDataSource` is set, the function is called with
the item key. On resolution, `mj-detail-load` fires and `slot="detail"` is shown
with the resolved data available via `data-*` attributes or a shared detail model.
If no `detailDataSource` is set, `slot="detail"` is shown immediately.

**Responsive layout (`auto` mode):** A `ResizeObserver` on the host tracks
container width. When width drops below `--mj-md-breakpoint`, `layout` switches
to `stacked` and `mj-layout-change` fires. In stacked mode, selecting an item
navigates to the detail view (master panel hidden via `display:none` with
`aria-hidden="true"`). The back button returns to master view.

**Panel resize:** In side-by-side mode with `resizable`, the divider tracks
`pointermove` and adjusts `--mj-md-master-width`. Min/max are clamped. On
`pointerup`, `mj-panel-resize` fires. Keyboard: `ArrowLeft`/`ArrowRight` adjust
by 8 px increments when the divider is focused.

**Detail URL sync:** If the consumer sets a `data-url` on items, the component
emits `mj-item-select` and it is the caller's responsibility to update the URL;
the component does not manipulate `history` directly.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Arrow Down / Up` (master focus) | Move focus to next/previous list item in the master panel. |
| `Enter` / `Space` (master item) | Select item; fire `mj-item-select`; load detail. |
| `Tab` | Move focus from master panel to divider to detail panel. |
| `ArrowLeft / Right` (divider focused) | Resize master panel by 8 px increments. |
| `Home` (divider) | Set master panel to minimum width. |
| `End` (divider) | Set master panel to maximum width. |
| `Enter` / `Space` (back button) | Return to master view in stacked mode; fire `mj-back`. |
| `Escape` (detail panel focus) | In stacked mode, return to master view; fire `mj-back`. |

## 13. Accessibility
- Root: `role="group"` with `aria-label` describing the overall component purpose.
- Master panel: `role="navigation"` (when items are navigation links) or `role="list"` with `aria-label` from `master-label`.
- Selected master item: `aria-selected="true"`; `aria-current="true"` when items are navigational.
- Divider: `role="separator"` with `aria-orientation="vertical"`, `aria-valuenow` (current master width px), `aria-valuemin`, `aria-valuemax`, and `aria-label="Resize panels"`.
- Detail panel: `<section>` with `aria-label="{detail-label}: {selected item label}"` or base label when empty.
- `aria-busy="true"` on detail section during loading.
- In stacked mode: hidden panel receives `aria-hidden="true"` and `inert`; active panel is fully visible.
- Back button: `aria-label` from `back-label` attribute.
- Live region: announces "Showing detail for {item label}" after navigation; "No item selected" when selection cleared.

## 14. Form participation
N/A — layout and navigation component. Editors within the detail slot handle their own form participation.

## 15. Internationalization & RTL
- In RTL, master panel is on the right; divider `aria-orientation` unchanged but resize directions flip.
- `back-label`, `detail-label`, `master-label`, and live region strings are overridable via attributes.
- Date/number metadata in master items formatted via the localization hook.

## 16. Progressive enhancement / SSR
Server renders master list as a `<nav>/<ul>/<li>` with `<a>` links, and the detail
area as a `<section>` with the default/first item's content. Without JS the links
navigate to full-page detail routes. On upgrade the component intercepts navigation,
updates panels in place, and attaches the responsive layout and resize logic.

## 17. Dependencies
- `<mj-data-table>` (when `master-type="table"`).
- `<mj-list>` (when `master-type="list"`).
- Focus utilities — `inert` management for stacked mode (§6).
- Live-region/announcement service (§6).
- Data-source adapter interface (§6).
- Design-token stylesheet (§6).
- Base element helper (§6).
- `<mj-button>` for back button.

## 18. Edge cases & error handling
- **`detailDataSource` rejects** — `loading-detail` cleared; `slot="detail-error"` shown; retry button re-calls with same key.
- **`selected-key` set to a key not in `items`** — detail loaded if `detailDataSource` present; master list shows no item selected.
- **Resize below `master-min-width`** — clamped; divider does not move further.
- **Stacked layout at initial render** — if container is already narrow, render in stacked-master mode immediately without animation.
- **Selection during loading-detail** — in-flight `detailDataSource` call is aborted (via `AbortController`); new call starts.
- **No items in master** — empty state handled by the slotted master content (caller responsibility).

## 19. Acceptance criteria
- [ ] Side-by-side layout: master and detail panels visible; resizable divider with `role="separator"` and `aria-value*`.
- [ ] `auto` layout: `ResizeObserver` triggers stacked mode below `--mj-md-breakpoint`; `mj-layout-change` fires.
- [ ] Stacked mode: only one panel visible at a time; hidden panel has `aria-hidden="true"` and `inert`.
- [ ] Item selection: `mj-item-select` fires; `selected-key` updates; selected item `aria-selected="true"`.
- [ ] `detailDataSource` called on selection; `loading-detail` state shown; detail rendered on resolve.
- [ ] Error state shown on `detailDataSource` rejection; retry reloads.
- [ ] Back button visible in stacked detail mode; `mj-back` fires; master panel restored.
- [ ] Divider keyboard resize: `ArrowLeft`/`Right` adjust width; `Home`/`End` go to min/max.
- [ ] Detail panel `aria-label` updated with selected item label; live region announces navigation.
- [ ] `master-type="table"` renders internal `<mj-data-table>`; selection drives detail.
- [ ] axe audit passes in both side-by-side and stacked modes.
- [ ] RTL: master panel on right; resize directions correct.

## 20. Open questions
- Should the component manage URL history (`history.pushState`) natively or always leave that to the caller?
- Should `master-type="table"` support row-level actions (e.g., delete) from within the master panel, or is that always a caller concern?
- Multiple simultaneous detail panels (split detail) — out of scope for P2?
