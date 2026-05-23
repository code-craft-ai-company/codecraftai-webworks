# Table Spec

- **Tag:** `<mj-table>`
- **Class / file:** `MjTable` / `mjtable.js`
- **Category:** Tables, lists & structured data
- **Primary or Variant:** Primary
- **Synonyms covered:** Table, Static table, Responsive table
- **Phase:** P0
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-table>` renders static, read-only tabular data using native `<table>` semantics.
It provides scoped column headers, an optional caption, striped/bordered/compact
density variants, and a responsive strategy (horizontal scroll, column priority
hiding, or stacked-card mode) for narrow viewports. It does not sort, filter, or
virtualize — use `<mj-data-table>` for interactive grids.

## 2. When to use / when not to use
**Use** when presenting reference data whose rows are not selectable, sortable,
or editable and whose row count fits in the viewport without virtualization (< ~200
rows). **Do not use** when users need to sort, filter, select rows, resize columns,
or when the dataset is large enough to require windowed rendering — use
`<mj-data-table>` instead. For a single key/value mapping, prefer a description
list (`<mj-list type="description">`).

## 3. Anatomy
- **Caption** — optional `<caption>` element; slotted or set via `caption` attribute.
- **Column group** — `<colgroup>/<col>` elements generated from the column definition;
  carries width hints.
- **Header row** — `<thead><tr>` with `<th scope="col">` for each column.
- **Body** — `<tbody>` containing data `<tr>` elements with `<td>` cells.
- **Footer row** (optional) — `<tfoot><tr>` with summary cells; slotted.
- **Responsive wrapper** — `<div role="region" aria-label="…" tabindex="0">` scroll
  container applied automatically when the table overflows.

## 4. Variants & modes
| Variant | `variant` value | Behavior |
|---------|----------------|----------|
| Default | `default` | Bordered header; no row stripes. |
| Striped | `striped` | Alternating `--mj-table-stripe-bg` on odd rows. |
| Bordered | `bordered` | Cell borders on all sides. |
| Compact | `compact` | Reduced `--mj-table-cell-padding-y` for dense displays. |

Responsive strategy is set via `responsive`:
- `scroll` (default) — wraps in an overflow-x scroll region.
- `priority` — columns with `data-priority` lower than the viewport breakpoint are
  hidden; a disclosure link reveals them.
- `stack` — each row collapses to a labeled key/value card below `--mj-table-stack-breakpoint`.

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `caption` | string | `""` | yes | Visible `<caption>` text; empty hides the element. |
| `variant` | `default\|striped\|bordered\|compact` | `default` | yes | Visual density/style variant. |
| `responsive` | `scroll\|priority\|stack` | `scroll` | yes | Narrow-viewport strategy. |
| `sticky-header` | boolean | false | yes | Pins `<thead>` on vertical scroll. |
| `col-widths` | string | `""` | no | Comma-separated pixel/percent widths applied to `<col>` elements. |
| `summary` | string | `""` | yes | Sets `aria-describedby` helper text for AT users. |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `columns` | `ColumnDef[]` | Array of `{ key, label, width?, priority? }` objects; drives `<thead>` and `<col>` generation. |
| `rows` | `Record<string, unknown>[]` | Array of row data objects keyed by `ColumnDef.key`. Setting replaces `<tbody>` content. |

## 7. Slots
| Slot | Description |
|------|-------------|
| (default) | Light-DOM `<table>` markup; upgraded in place (SSR path). |
| `caption` | Overrides the `caption` attribute with rich content. |
| `footer` | Content placed inside `<tfoot>`. |
| `empty` | Shown in place of `<tbody>` when `rows` is empty; defaults to an "No data" row spanning all columns. |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-table-overflow` | `{ overflowing: boolean }` | true | false | Fired when the table's scroll overflow state changes (on resize). |

## 9. CSS parts & custom properties
**Parts:** `table`, `caption`, `thead`, `tbody`, `tfoot`, `tr`, `th`, `td`, `scroll-wrapper`.

| Custom property | Default | Purpose |
|----------------|---------|---------|
| `--mj-table-border-color` | `token(--mj-color-border)` | Cell/row border color. |
| `--mj-table-header-bg` | `token(--mj-color-surface-raised)` | Header row background. |
| `--mj-table-stripe-bg` | `token(--mj-color-surface-subtle)` | Odd-row stripe background. |
| `--mj-table-cell-padding-x` | `12px` | Horizontal cell padding. |
| `--mj-table-cell-padding-y` | `10px` | Vertical cell padding (reduced in compact). |
| `--mj-table-stack-breakpoint` | `480px` | Container width below which stack mode activates. |

## 10. States
- **default** — table renders normally; no interactive state.
- **loading** — `loading` attribute shows a skeleton overlay (`aria-busy="true"` on the wrapper).
- **empty** — `rows` is empty or no `<tbody>` children; `slot="empty"` content displayed.
- **overflow** — scroll wrapper gains a shadow/fade cue; `mj-table-overflow` event fires.
- **sticky-header active** — `<thead>` has `position: sticky; top: 0` and an elevation shadow.

## 11. Behavior & interactions
Data can be supplied as light-DOM `<table>` markup (SSR) or via the `columns`/`rows`
properties. When both are present, property data takes precedence and the light-DOM
table is replaced. The `col-widths` attribute is parsed as a comma-separated list
and applied to `<col width>` in order; omitted positions inherit natural widths.
In `priority` responsive mode, `ResizeObserver` on the scroll wrapper evaluates
each column's `data-priority` (integer 1 = always visible, higher = hidden first)
against a token-driven breakpoint ladder; hidden columns are grouped into a
"Show more" disclosure row. In `stack` mode each `<td>` gains a `data-label`
attribute copied from its matching `<th>` for the CSS `::before` label trick.
No row interactions are wired; pointer cursor is default.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` | Moves focus into/through the scroll wrapper (when overflow) so keyboard users can scroll. |
| `Arrow Left / Right` | Scrolls the overflow wrapper horizontally when the wrapper is focused. |

## 13. Accessibility
- Root element is a native `<table>`; `role="table"` is implicit and not duplicated.
- Column headers use `<th scope="col">`; row headers (when first column is a label) use `<th scope="row">`.
- Caption conveyed via `<caption>`; the `summary` attribute value is attached to the scroll wrapper via `aria-describedby` for AT users encountering the scroll region.
- Scroll wrapper: `role="region"` + `aria-label` derived from caption so AT names the scrollable container.
- When `loading`, `aria-busy="true"` on the table and a polite live region announces "Loading table data."
- Empty state row spans all columns and is marked `aria-live="polite"`.
- No color-only encoding; status cells require both icon and text.

## 14. Form participation
N/A — read-only display component.

## 15. Internationalization & RTL
- Column order reverses in RTL (`dir="rtl"`); flexbox/grid row direction follows `dir`.
- `caption` and `summary` strings must be passed translated by the caller.
- `col-widths` values are direction-agnostic (percentage/pixel); no start/end semantics.

## 16. Progressive enhancement / SSR
Server renders a plain `<mj-table><table>…</table></mj-table>`. Before JS loads, the
inner `<table>` is fully readable. On upgrade the component wraps it in the responsive
scroll container and applies variant styles via the adopted stylesheet, with zero layout
shift because the table dimensions are preserved.

## 17. Dependencies
- Design-token stylesheet (§6).
- Base element helper for attribute/property reflection (§6).
- No other components.

## 18. Edge cases & error handling
- **Empty `rows` array** — renders `slot="empty"` content spanning all columns.
- **Mismatched column count** — cells that exceed the `columns` definition are rendered as-is; missing cells render as empty `<td>`.
- **Very long cell content** — cells set `overflow: hidden; text-overflow: ellipsis` by default; full text exposed via `title` attribute and tooltip.
- **Zero-width `col-widths` entry** — treated as `auto`.
- **`priority` mode with no `data-priority` annotations** — all columns remain visible; no hiding occurs.

## 19. Acceptance criteria
- [ ] Native `<table>` with `<caption>`, `<thead>`, `<tbody>`, `<tfoot>` renders correctly for both light-DOM and property-driven data.
- [ ] `scope="col"` on every `<th>` in the header row; `scope="row"` on row-header cells.
- [ ] Striped, bordered, and compact variants apply correct token-based styles.
- [ ] Responsive scroll wrapper: `role="region"`, `aria-label`, `tabindex="0"`, keyboard-scrollable.
- [ ] `sticky-header` pins `<thead>` and shows elevation shadow on scroll.
- [ ] `priority` mode hides correct columns at each breakpoint; disclosure restores them.
- [ ] `stack` mode renders each cell with a `::before` label at the stack breakpoint.
- [ ] Empty state slot is shown when `rows = []`; hidden when rows present.
- [ ] `loading` state sets `aria-busy="true"` and announces via live region.
- [ ] axe audit passes with zero violations.
- [ ] RTL layout reverses column order.
- [ ] Light, dark, high-contrast themes verified.

## 20. Open questions
- Should `priority` mode column restore use a button-triggered drawer or an inline "Show N hidden columns" toggle row?
- Is a footer `<tfoot>` needed for aggregate rows (sum, average), or should callers supply it via the `footer` slot?
