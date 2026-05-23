# Tree Grid Spec

- **Tag:** `<mj-tree-grid>`
- **Class / file:** `MjTreeGrid` / `mjtreegrid.js`
- **Category:** Tables, lists & structured data
- **Primary or Variant:** Primary
- **Synonyms covered:** Tree grid, Hierarchical data grid, Nested row table
- **Phase:** P2
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-tree-grid>` renders hierarchical tabular data where each row can contain
child rows that are expanded or collapsed in place. It follows the WAI-ARIA
`treegrid` pattern, combining row-level tree navigation with full column features
inherited from `<mj-data-table>` (sort, filter, resize, reorder, pin). It is the
correct choice when rows have a parent/child relationship that must be visible
within a columnar layout — e.g., file systems, org charts, nested tasks, or
bill-of-materials views.

## 2. When to use / when not to use
**Use** when data is hierarchical and each level shares the same columns (depth ≥ 2,
parent rows meaningful alongside children). **Do not use** for flat tabular data —
use `<mj-data-table>`. For tree navigation without columns use the `tree` pattern
(`<mj-side-nav>` or a tree selector). For deeply nested trees with mixed-depth items
where column alignment is unimportant, consider `<mj-list>` with nesting.

## 3. Anatomy
- **Column header row** — identical to `<mj-data-table>`; supports sort, resize, reorder.
- **Tree row** — `role="row"` with `aria-level`, `aria-expanded`, `aria-setsize`, `aria-posinset`.
- **Expander cell** — first column cell contains an expand/collapse toggle button; indented by `level * --mj-tg-indent`.
- **Leaf row** — row with no children; no expander rendered; `aria-expanded` omitted.
- **Children group** — collapsible container of child rows; rendered immediately after their parent row in DOM order.
- **Virtualized body** — same windowed render engine as `<mj-data-table>`; flattened row list with depth metadata.

## 4. Variants & modes
| Variant | `mode` value | Behavior |
|---------|-------------|----------|
| Grid (default) | `grid` | Row/cell selection; full column features. |
| View-only | `view` | Expand/collapse only; no selection or editing. |
| Editable | `edit` | Cells editable (same as DataTable spreadsheet mode per column). |

Lazy child loading is enabled by setting `load-children` (boolean); child rows are
fetched via the `dataSource` adapter when a parent is first expanded.

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `mode` | `grid\|view\|edit` | `grid` | yes | Interaction mode. |
| `selection` | `none\|single\|multi-row` | `none` | yes | Row selection model. |
| `sortable` | boolean | false | yes | Enables sort on all columns. |
| `filterable` | boolean | false | yes | Shows per-column filter inputs. |
| `resizable` | boolean | false | yes | Enables column resize. |
| `reorderable` | boolean | false | yes | Enables column drag-reorder. |
| `load-children` | boolean | false | yes | Defers child row fetch to first expand. |
| `expand-depth` | number | `1` | yes | Levels auto-expanded on initial render (0 = all collapsed). |
| `row-height` | number | `40` | yes | Fixed row height in px. |
| `loading` | boolean | false | yes | Shows skeleton and `aria-busy="true"`. |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `columns` | `ColumnDef[]` | Same shape as `<mj-data-table>`; first column hosts the expander. |
| `rows` | `TreeRowDef[]` | `{ key, data, children?: TreeRowDef[], hasChildren?: boolean }` — `hasChildren` enables lazy load without pre-fetching children. |
| `dataSource` | `TreeDataSourceAdapter` | `{ fetchRoots(params): Promise<Page>, fetchChildren(parentKey, params): Promise<Page> }`. |
| `expandedKeys` | `Set<string>` | Currently expanded row keys; settable to programmatically control expansion. |
| `selectedRows` | `Set<string>` | Selected row keys; read-only externally. |

## 7. Slots
| Slot | Description |
|------|-------------|
| `toolbar` | Above the header: column picker, bulk action bar, search. |
| `empty` | Shown when root-level dataset is empty. |
| `empty-children` | Shown inside an expanded parent that has zero children. |
| `footer` | Replaces the default footer/pagination bar. |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-row-expand` | `{ key: string, level: number }` | true | true | Row is about to expand; cancel to prevent. |
| `mj-row-collapse` | `{ key: string, level: number }` | true | true | Row is about to collapse; cancel to prevent. |
| `mj-children-load` | `{ parentKey: string, rows: TreeRowDef[] }` | true | false | Lazy-loaded children have arrived. |
| `mj-children-error` | `{ parentKey: string, error: Error }` | true | false | Child fetch failed. |
| `mj-sort-change` | `{ key: string, direction: 'asc'\|'desc'\|null }` | true | false | Column sort toggled. |
| `mj-filter-change` | `{ key: string, value: string }` | true | false | Column filter changed. |
| `mj-selection-change` | `{ selectedRows: string[] }` | true | false | Row selection changed. |
| `mj-column-resize` | `{ key: string, width: number }` | true | false | Column resized. |
| `mj-column-reorder` | `{ from: number, to: number, key: string }` | true | false | Column reordered. |

## 9. CSS parts & custom properties
**Parts:** `toolbar`, `header-row`, `header-cell`, `body`, `row`, `row-expanded`,
`row-selected`, `expander-cell`, `expander-button`, `cell`, `footer`.

| Custom property | Default | Purpose |
|----------------|---------|---------|
| `--mj-tg-indent` | `20px` | Horizontal indent per tree level. |
| `--mj-tg-expander-size` | `20px` | Width/height of the expand/collapse toggle. |
| `--mj-tg-row-height` | `40px` | Row height (synced with `row-height` attribute). |
| `--mj-tg-selected-bg` | `token(--mj-color-selection-subtle)` | Selected row background. |
| `--mj-tg-hover-bg` | `token(--mj-color-surface-hover)` | Row hover background. |
| `--mj-tg-connector-color` | `token(--mj-color-border)` | Tree connector line color. |

## 10. States
- **default** — flat root rows visible; all collapsed to `expand-depth`.
- **expanded** — parent row shows `aria-expanded="true"`; children in DOM.
- **collapsed** — parent row shows `aria-expanded="false"`; children removed from DOM (not just hidden).
- **loading-children** — expander shows a spinner; `aria-label="Loading children"`.
- **error-children** — expander shows error icon; inline retry available.
- **row-selected** — `aria-selected="true"`; `--mj-tg-selected-bg` applied.
- **loading** (root) — `aria-busy="true"`; skeleton rows fill first page.
- **empty** — root dataset empty; `slot="empty"` shown.

## 11. Behavior & interactions
**Flattened virtual list:** The tree is maintained as a logical tree but rendered as
a flattened array of visible rows. Expanding a parent inserts its children into the
flat list at the correct position; collapsing removes them. The virtualization engine
operates on this flat list identically to `<mj-data-table>`.

**Expand/collapse toggle:** Clicking the expander button or pressing `ArrowRight` on
a collapsed parent fires `mj-row-expand`. If `load-children` is true and the row's
`children` array is not yet populated, the adapter's `fetchChildren` is called;
the row enters `loading-children` state until the promise resolves. On resolution,
`mj-children-load` fires and children are inserted into the flat list.

**Sorting:** Sorts only within each sibling group; parent/child hierarchy is
preserved. Top-level rows sort among themselves; children sort among their siblings.
The sort indicator and `aria-sort` on the header cell reflect the active sort.

**Filtering:** Rows not matching the filter predicate are hidden from the flat list.
If a child matches, its parent chain is kept visible (ancestors forced visible).
Filter count announced via live region: "{n} rows visible."

**Selection:** `multi-row` mode supports `Shift+Click`/`Shift+Space` for contiguous
selection within a sibling group and across groups. `Ctrl+A` selects all visible
(non-hidden-by-filter) rows. No automatic parent/child cascade selection — this
must be handled by the caller via `mj-selection-change`.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Arrow Down / Up` | Move focus to next/previous row in the visible flat list. |
| `Arrow Right` | If collapsed parent: expand. If expanded parent: move focus to first child. If leaf: no-op. |
| `Arrow Left` | If expanded parent: collapse. If child or collapsed parent: move focus to parent row. |
| `Home` | Move focus to first row. |
| `End` | Move focus to last visible row. |
| `Enter` | Toggle expand/collapse of focused parent row. |
| `Space` | Toggle row selection. |
| `Shift+Space` | Extend selection from anchor to focused row. |
| `Ctrl+A` | Select all visible rows. |
| `Arrow Left / Right` on a cell (non-expander) | Move focus between cells in the row (grid cell navigation). |
| `F2` | Enter edit mode on focused cell (edit mode). |
| `Escape` | Cancel cell edit; cancel in-progress lazy child load. |
| `Tab` | Move focus out of the grid (standard tab order). |

## 13. Accessibility
- Root: `role="treegrid"` with `aria-label` or `aria-labelledby`.
- Row: `role="row"` with `aria-level` (1-based depth), `aria-setsize` (sibling count), `aria-posinset` (1-based sibling position), `aria-expanded` (parent rows only).
- Expander button: `role="button"` with `aria-label="Expand {row label}"` or `"Collapse {row label}"`.
- Cells: `role="gridcell"`; first cell `role="rowheader"` when it contains the row label.
- `aria-rowcount` and `aria-rowindex` on rows for virtualized contexts.
- Live region: expansion/collapse announces "Row {label} expanded, {n} children" or "collapsed."
- Lazy load: expander aria-label changes to "Loading children for {label}" during fetch; on completion "Children loaded."
- Filter: live region announces count changes.
- High-contrast: connector lines must use `CanvasText` or `ButtonText` token.

## 14. Form participation
N/A — display/navigation component; cell editors are native inputs.

## 15. Internationalization & RTL
- In RTL, tree indent direction reverses; expander arrow rotation mirrors.
- Connector lines render on the right in RTL.
- All UI strings (expander labels, loading text, error messages, empty labels) are overridable via attributes.
- Sort and filter use `Intl.Collator` for locale-correct string ordering.
- Date/number cells format via `Intl` APIs.

## 16. Progressive enhancement / SSR
Server may render a nested `<ul>/<li>` structure inside `<mj-tree-grid>`. On upgrade
the component converts the nested list into its internal tree row data structure and
renders the column grid. Without JS the nested list provides navigable content.

## 17. Dependencies
- `<mj-data-table>` (column features, virtualization engine, sort/filter, resize/reorder are shared).
- Collection/virtualization utility (§6) — tree-aware flat-list mode.
- Data-source adapter interface (§6) — extended with `fetchChildren`.
- Focus utilities (§6).
- Live-region/announcement service (§6).
- Localization/formatting hook (§6).

## 18. Edge cases & error handling
- **Circular references in row data** — detected at data ingestion; offending rows logged and skipped.
- **`fetchChildren` rejects** — row enters `error-children` state; retry button re-calls adapter.
- **Filter hides all children but not parent** — parent remains visible with an "all children hidden" note in the expander cell.
- **`expand-depth` exceeds actual tree depth** — no error; simply stops at leaf rows.
- **Sorting with lazy-loaded children** — only loaded children are sorted; unloaded children are fetched on expand and sorted on arrival.
- **Very deep trees (>20 levels)** — indent does not exceed container width; `--mj-tg-indent` is clamped.

## 19. Acceptance criteria
- [ ] `role="treegrid"` on root; `role="row"` rows carry `aria-level`, `aria-setsize`, `aria-posinset`.
- [ ] Parent rows have `aria-expanded="true|false"`; leaf rows omit `aria-expanded`.
- [ ] `ArrowRight` expands collapsed parent and moves focus to first child; `ArrowLeft` collapses and moves to parent.
- [ ] Lazy child loading: spinner shown; `mj-children-load` fires on success; `mj-children-error` on failure.
- [ ] Virtualization: only visible rows in DOM; `aria-rowcount` reflects total.
- [ ] Sort operates per sibling group; hierarchy preserved.
- [ ] Filter: ancestor rows of matching children remain visible; count announced.
- [ ] Multi-row selection: `Shift+Space` extends range; `Ctrl+A` selects all visible.
- [ ] Column resize, reorder, and pin work identically to `<mj-data-table>`.
- [ ] Live region announces expand/collapse, load, and filter count.
- [ ] axe audit passes with zero violations.
- [ ] RTL: indent on right, expander arrow mirrored, connector lines on right.

## 20. Open questions
- Should parent/child selection cascade (tri-state checkbox) be built in or left to the caller?
- Multi-column sort within sibling groups — implement alongside DataTable multi-sort?
- Maximum supported tree depth before indent wrapping becomes a UX problem — define a token max.
