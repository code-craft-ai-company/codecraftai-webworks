# Data Table Spec

- **Tag:** `<mj-data-table>`
- **Class / file:** `MjDataTable` / `mjdatatable.js`
- **Category:** Tables, lists & structured data
- **Primary or Variant:** Primary
- **Synonyms covered:** Data table, Grid, Sortable table, Filterable table, Spreadsheet grid
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-data-table>` is a full-featured interactive data grid. It supports column
sorting, per-column filtering, column resize and reorder, pinned columns, row and
cell selection, inline cell editing (spreadsheet mode), and virtualized row
rendering for datasets too large to fully render in the DOM. Data arrives through
a pluggable server-side adapter so the grid integrates with paged REST APIs or
WebSocket streams without coupling to a specific backend.

## 2. When to use / when not to use
**Use** for any interactive tabular dataset where users need to sort, filter, or
edit rows, or when the row count exceeds ~100 and DOM performance matters.
**Do not use** for simple reference tables with no interactivity — use `<mj-table>`
instead. For hierarchical rows use `<mj-tree-grid>`. For spreadsheet-only editing
without the data-source adapter, `spreadsheet` mode of this component is the
correct choice.

## 3. Anatomy
- **Toolbar area** — slot for `<mj-column-picker>`, `<mj-bulk-action-bar>`, search,
  and custom actions above the grid.
- **Column header row** — each header cell contains: sort indicator, resize handle,
  drag handle, pin toggle, and an optional per-column filter input.
- **Pinned-left / pinned-right regions** — sticky column groups rendered in their
  own scroll-synchronized `<div>` elements.
- **Scrollable body** — virtualized row container; only the visible window of rows
  is in the DOM.
- **Virtual row** — one `role="row"` element per rendered slot; recycled via pool.
- **Cell** — `role="gridcell"`; in edit mode becomes an editable region or hosts an
  input control.
- **Footer bar** — row count, page controls, and per-page selector.

## 4. Variants & modes
| Variant | `mode` value | Behavior |
|---------|-------------|----------|
| Grid (default) | `grid` | Row selection, keyboard navigation per APG grid pattern. |
| Spreadsheet | `spreadsheet` | Every cell is editable; Tab/Enter advance focus cell-by-cell. |
| View-only | `view` | No selection or editing; keyboard nav still reads cell values. |

Selection granularity is controlled by `selection` attribute: `none`, `single`,
`multi-row`, `cell`.

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `mode` | `grid\|spreadsheet\|view` | `grid` | yes | Interaction mode. |
| `selection` | `none\|single\|multi-row\|cell` | `none` | yes | Row/cell selection model. |
| `sortable` | boolean | false | yes | Enables sort controls on all columns unless overridden per column. |
| `filterable` | boolean | false | yes | Shows per-column filter inputs in the header. |
| `resizable` | boolean | false | yes | Enables drag-resize handles on column borders. |
| `reorderable` | boolean | false | yes | Enables drag-to-reorder column headers. |
| `row-height` | number | `40` | yes | Fixed row height in px for the virtualization engine. |
| `page-size` | number | `50` | yes | Rows per page when using the paged data adapter. |
| `loading` | boolean | false | yes | Displays skeleton rows and `aria-busy="true"`. |
| `empty-label` | string | `"No results"` | yes | Text shown when the dataset is empty. |
| `select-all` | boolean | false | yes | Shows a select-all checkbox in the header when `selection="multi-row"`. |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `columns` | `ColumnDef[]` | `{ key, label, width?, minWidth?, pinned?: 'left'\|'right', sortable?, filterable?, editable?, renderCell? }` |
| `dataSource` | `DataSourceAdapter` | Adapter implementing `{ fetch(params): Promise<Page> }` where `Page = { rows, total }`. |
| `rows` | `Record<string, unknown>[]` | Direct row data (used instead of `dataSource` for client-side data). |
| `sortState` | `{ key: string, direction: 'asc'\|'desc' } \| null` | Current sort; settable to programmatically sort. |
| `filterState` | `Record<string, string>` | Map of column key to current filter string. |
| `selectedRows` | `Set<string>` | Set of selected row keys (read-only; use `selectRow()` / `clearSelection()`). |
| `selectedCell` | `{ rowKey: string, colKey: string } \| null` | Currently focused cell in `cell` selection mode. |

## 7. Slots
| Slot | Description |
|------|-------------|
| `toolbar` | Content rendered above the column headers (column picker, bulk bar, search). |
| `empty` | Replaces the body when the dataset is empty after filtering. |
| `footer` | Replaces the default pagination footer. |
| `cell-[key]` | Named slot per column key for custom cell rendering; receives row data via `dataset`. |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-sort-change` | `{ key: string, direction: 'asc'\|'desc'\|null }` | true | false | User clicked a column sort control. |
| `mj-filter-change` | `{ key: string, value: string }` | true | false | User changed a column filter value. |
| `mj-column-resize` | `{ key: string, width: number }` | true | false | User finished resizing a column. |
| `mj-column-reorder` | `{ from: number, to: number, key: string }` | true | false | User dropped a column in a new position. |
| `mj-selection-change` | `{ selectedRows: string[], selectedCell: object\|null }` | true | false | Row or cell selection changed. |
| `mj-cell-edit-start` | `{ rowKey: string, colKey: string, value: unknown }` | true | true | Cell entered edit mode; cancelable to prevent editing. |
| `mj-cell-edit-commit` | `{ rowKey: string, colKey: string, oldValue: unknown, newValue: unknown }` | true | true | User committed a cell edit; cancelable to reject. |
| `mj-row-action` | `{ rowKey: string, action: string }` | true | false | A row-level action button was activated. |
| `mj-load-more` | `{ offset: number, pageSize: number }` | true | false | Virtualization engine requests the next page from the adapter. |

## 9. CSS parts & custom properties
**Parts:** `toolbar`, `header-row`, `header-cell`, `sort-indicator`, `resize-handle`,
`body`, `row`, `row-selected`, `cell`, `cell-editing`, `footer`, `pagination`.

| Custom property | Default | Purpose |
|----------------|---------|---------|
| `--mj-dt-row-height` | `40px` | Matches `row-height` attribute; drives virtual row sizing. |
| `--mj-dt-header-bg` | `token(--mj-color-surface-raised)` | Column header background. |
| `--mj-dt-selected-row-bg` | `token(--mj-color-selection-subtle)` | Selected row highlight. |
| `--mj-dt-focus-cell-outline` | `2px solid token(--mj-color-focus)` | Focused cell ring. |
| `--mj-dt-pinned-shadow` | `4px 0 8px rgba(0,0,0,.12)` | Shadow on right edge of pinned columns. |
| `--mj-dt-border-color` | `token(--mj-color-border)` | Row/cell divider color. |

## 10. States
- **default** — grid renders rows; no selection.
- **loading** — `aria-busy="true"` on grid; skeleton rows fill the viewport; spinner in footer.
- **empty** — dataset empty (or filtered to zero rows); `slot="empty"` content shown.
- **row-selected** — selected rows carry `aria-selected="true"` and `--mj-dt-selected-row-bg`.
- **cell-focused** — focused gridcell has `--mj-dt-focus-cell-outline` ring.
- **cell-editing** — active edit cell hosts the editor control; `aria-label="Editing <col> row <n>"`.
- **sorting** — `aria-sort="ascending"` or `"descending"` on the active header cell.
- **column-dragging** — dragged column header has `aria-grabbed="true"` (live region announces drop targets).
- **disabled** — `disabled` attribute disables all interactions; grid cells `aria-disabled="true"`.

## 11. Behavior & interactions
**Virtualization:** The body is a fixed-height scroll container. A `IntersectionObserver`-
and scroll-event-driven engine renders only the rows in the visible window plus an
overscan of `Math.ceil(viewportRows * 0.5)` above and below. Row elements are pooled
and recycled; their `data-row-key` and cell content are swapped on recycle. Total
scroll height is maintained via a spacer element sized to `total * row-height`.

**Sorting:** Clicking a sortable header cycles through `asc → desc → none`. Only one
column is sorted at a time unless the adapter signals multi-sort support. `mj-sort-change`
fires; if `dataSource` is set the adapter is re-fetched; otherwise client-side sort
runs via `Intl.Collator` for strings and numeric compare for numbers.

**Filtering:** Each filterable column shows a text input below the header label. Input
is debounced 300 ms. `mj-filter-change` fires; client-side mode re-runs the filter
predicate over `rows`; server-side mode re-fetches via the adapter.

**Column resize:** Pointer-down on the resize handle begins resize. `pointermove`
adjusts the column's `<col>` width and the corresponding header and body cells.
Minimum width is `minWidth` from the column definition (default 60 px). On
`pointerup`, `mj-column-resize` fires. Keyboard resize: focus the handle, then
`ArrowLeft`/`ArrowRight` adjust by 8 px increments.

**Column reorder:** Pointer-drag on the drag handle shows a ghost of the header.
Drop zones between headers highlight. On drop, the internal column order is
updated and `mj-column-reorder` fires. Keyboard reorder: focus the header cell,
`Space` to grab, `ArrowLeft`/`ArrowRight` to move, `Enter` to drop, `Escape` to cancel.

**Pinned columns:** Columns with `pinned: 'left'` or `'right'` render in a sticky
wrapper that does not scroll horizontally. They are synchronized with the main body's
vertical scroll position.

**Cell editing:** In `grid` mode, double-click or `F2`/`Enter` on a cell emits
`mj-cell-edit-start`. If not canceled, the cell is replaced with an appropriate
editor (text input, select, date, etc.) determined by the column's `type` field.
`Enter` or blur commits; `Escape` cancels. In `spreadsheet` mode every cell is
immediately editable and `Tab`/`Shift+Tab` advance focus.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Arrow keys` | Move focus between gridcells within the grid. |
| `Home` | Move focus to first cell in current row. |
| `End` | Move focus to last cell in current row. |
| `Ctrl+Home` | Move focus to first cell in first row. |
| `Ctrl+End` | Move focus to last cell in last row. |
| `Page Up / Down` | Scroll one viewport height; focus moves to first/last visible row. |
| `Space` | Toggle row selection (multi-row mode); toggle cell selection (cell mode); also grabs column header for reorder. |
| `Shift+Space` | Select contiguous range from anchor row to focused row. |
| `Ctrl+A` | Select all rows (multi-row mode). |
| `Enter` | Activate cell edit; confirm edit if already editing; navigate to next row in spreadsheet mode. |
| `F2` | Enter cell edit mode. |
| `Escape` | Cancel cell edit; cancel column reorder drag. |
| `Tab / Shift+Tab` | Move to next/previous cell in spreadsheet mode; exit grid in grid mode. |
| `ArrowLeft / Right` on resize handle | Adjust column width by 8 px. |
| `ArrowLeft / Right` on grabbed header | Move column left/right during keyboard reorder. |
| `Click on sort header` | Cycle sort: asc → desc → none. |

## 13. Accessibility
- Root element: `role="grid"` with `aria-label` or `aria-labelledby` pointing to a visible caption.
- Column headers: `role="columnheader"` with `aria-sort="ascending|descending|none"` on sortable columns.
- Data cells: `role="gridcell"`; `aria-selected` reflects selection state.
- Row elements: `role="row"`; `aria-selected` on selected rows; `aria-rowindex` and `aria-rowcount` for virtualized grids so AT knows total row count.
- `aria-colcount` and `aria-colindex` on each cell for pinned/virtual column contexts.
- Column reorder: live region announces "Column {label} moved to position {n}" after drop.
- Sort change: live region announces "Sorted by {label} ascending/descending/cleared."
- Filter change: live region announces "{n} results" after debounce settles.
- Bulk selection: `aria-checked="true|false|mixed"` on the select-all checkbox.
- Loading state: `aria-busy="true"` on the grid root; polite live region announces "Loading data."
- Focus management: roving tabindex across gridcells; `aria-activedescendant` not used (native focus preferred for cell editors).

## 14. Form participation
N/A — the grid itself is not a form input. Cell editors within the grid are native
`<input>` elements and participate in the form independently if needed.

## 15. Internationalization & RTL
- Column order reverses in RTL; pinned-left columns appear on the right, pinned-right on the left.
- Sort arrow direction reverses in RTL.
- Text filter comparison is locale-sensitive via `Intl.Collator`.
- All UI strings (`empty-label`, sort/filter aria labels, pagination) are overridable via attributes.
- Date and number cell types format via `Intl.DateTimeFormat` / `Intl.NumberFormat` using the document locale or an explicit `locale` attribute.

## 16. Progressive enhancement / SSR
Server may render a plain `<mj-table>` inside `<mj-data-table>` as a no-JS fallback.
On upgrade, the component reads the table's `<thead>` to infer column definitions if
`columns` is not set, then replaces the `<tbody>` with the virtualized body. No layout
shift because the grid reserves the same height as the original table.

## 17. Dependencies
- `<mj-table>` (SSR fallback semantics).
- `<mj-column-picker>` (toolbar integration).
- `<mj-bulk-action-bar>` (selection toolbar).
- Collection/virtualization utility (§6).
- Data-source adapter interface (§6).
- Focus utilities — roving tabindex (§6).
- Live-region/announcement service (§6).
- Overlay/positioning engine (§6) for column filter popups.
- Localization/formatting hook (§6).

## 18. Edge cases & error handling
- **Empty dataset after filter** — `slot="empty"` shown; clear-filter button offered.
- **DataSource fetch failure** — error state banner inside footer; retry button fires `mj-load-more`.
- **Rows taller than `row-height`** — virtualization engine defaults to `auto` row height measurement mode; performance degrades gracefully.
- **Column definition changes at runtime** — grid re-renders headers; scroll and selection reset.
- **All columns pinned** — horizontal scroll container has zero-width scrollable area; treated as no-scroll.
- **`reorderable` + `pinned` column** — pinned columns are draggable only within their pin group.
- **Cell editor validation failure** — `mj-cell-edit-commit` canceled by caller; cell returns to display mode with `aria-invalid="true"` and an error tooltip.

## 19. Acceptance criteria
- [ ] `role="grid"` with `aria-rowcount`, `aria-colcount` on the root element.
- [ ] Column headers have `role="columnheader"` and `aria-sort` cycles asc/desc/none on click.
- [ ] Gridcells have `role="gridcell"`, `aria-selected`, `aria-rowindex`, `aria-colindex`.
- [ ] Arrow key navigation moves focus among all gridcells; Home/End/Ctrl+Home/Ctrl+End work.
- [ ] Virtualization: only visible rows + overscan in DOM; scroll height maintained via spacer.
- [ ] Client-side sort and filter work without a `dataSource`; server-side adapter is re-fetched on state change.
- [ ] Column resize adjusts width via pointer drag and arrow-key increments; `mj-column-resize` fires.
- [ ] Column reorder works by drag and by keyboard grab-move-drop; `mj-column-reorder` fires.
- [ ] Pinned columns remain visible during horizontal scroll; synchronized vertical scroll.
- [ ] Cell edit: `Enter`/`F2` starts edit; `Enter` commits; `Escape` cancels; `mj-cell-edit-commit` fires.
- [ ] Multi-row selection: checkbox per row + select-all with indeterminate; `Shift+Space` range; `Ctrl+A` all.
- [ ] Live region announces sort, filter count, column move, and loading/empty states.
- [ ] axe audit passes with zero violations.
- [ ] RTL reverses column and pin direction.
- [ ] `loading` state shows skeleton rows and `aria-busy="true"`.

## 20. Open questions
- Should multi-column sort be supported via `Shift+Click`? Needs adapter contract update.
- Editable cell type registry: built-in types (`text`, `number`, `date`, `select`) plus a custom renderer API — confirm the renderer signature.
- Frozen row support (pinned rows at top/bottom) — defer to a later iteration or include now?
