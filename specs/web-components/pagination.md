# Pagination Spec

- **Tag:** `<mj-pagination>`
- **Class / file:** `MjPagination` / `mjpagination.js`
- **Category:** Navigation components
- **Primary or Variant:** Primary
- **Synonyms covered:** Pagination, Pager, Page navigation
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-pagination>` is a navigation component for moving through paged result sets.
It renders Previous/Next controls and a configurable set of numbered page links,
with the current page marked using `aria-current="page"`. It optionally includes
a page-size selector and a compact pager variant for space-constrained contexts.

## 2. When to use / when not to use
**Use** when results or content are split into discrete pages and users need to
navigate between them. **Do not use** for infinite-scroll lists — use
`<mj-virtualized-list>` with a "load more" trigger. **Do not use** for step-by-step
form navigation — use `<mj-wizard>`. **Do not use** for tab-like views — use
`<mj-tabs>`.

## 3. Anatomy
- **Host / `<nav>`** — `<nav aria-label="Pagination">` landmark.
- **Previous button** (`::part(prev)`) — navigates to the prior page.
- **Page list** (`::part(page-list)`) — `<ol>` of page number buttons/links.
- **Page item** (`::part(page-item)`) — each `<li>` wrapping a page button.
- **Page button** (`::part(page-btn)`) — `<button>` or `<a>` for each page number.
- **Ellipsis** (`::part(ellipsis)`) — `…` indicating omitted page range.
- **Next button** (`::part(next)`) — navigates to the following page.
- **Page-size selector** (`::part(page-size)`) — optional `<mj-select>` for rows-per-page.
- **Summary** (`::part(summary)`) — optional "Showing X–Y of Z" text.

## 4. Variants & modes
| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Full | _(default)_ | Prev + numbered pages + Next |
| Compact | `variant="compact"` | Prev + "Page X of Y" label + Next; no individual page numbers |
| Simple | `variant="simple"` | Prev/Next only; no page numbers |
| With page size | `show-page-size` | Adds a page-size dropdown |
| With summary | `show-summary` | Adds a "Showing X–Y of Z results" label |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `page` | number | `1` | Yes | Current 1-based page number |
| `total-pages` | number | `1` | Yes | Total number of pages |
| `total-items` | number | `0` | Yes | Total result count; used to compute summary text |
| `page-size` | number | `10` | Yes | Items per page; also drives the page-size selector |
| `page-size-options` | string | `"10,25,50,100"` | Yes | Comma-separated list of page-size options |
| `sibling-count` | number | `1` | Yes | Number of page buttons shown on each side of the current page |
| `boundary-count` | number | `1` | Yes | Number of page buttons always shown at start and end |
| `variant` | string | `"full"` | Yes | Display variant: `full` \| `compact` \| `simple` |
| `show-page-size` | boolean | `false` | Yes | Shows the page-size selector |
| `show-summary` | boolean | `false` | Yes | Shows the "Showing X–Y of Z" summary |
| `nav-label` | string | `"Pagination"` | Yes | `aria-label` for the `<nav>` landmark |
| `disabled` | boolean | `false` | Yes | Disables all controls |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `hasPrevious` | boolean | Read-only; `true` when `page > 1` |
| `hasNext` | boolean | Read-only; `true` when `page < totalPages` |
| `pageRange` | `[number, number]` | Read-only; `[firstItemIndex, lastItemIndex]` of the current page (0-based) |

## 7. Slots
| Slot | Description |
|------|-------------|
| `prev-label` | Custom content for the Previous button (default: left-arrow icon + "Previous" text) |
| `next-label` | Custom content for the Next button (default: "Next" text + right-arrow icon) |
| `summary` | Custom summary content; overrides the auto-generated "Showing X–Y of Z" text |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-pagination-change` | `{ page: number, previousPage: number, pageSize: number }` | Yes | Yes | Fires when the page or page size changes; cancel to block and handle manually |
| `mj-pagination-page-size-change` | `{ pageSize: number, previousPageSize: number }` | Yes | Yes | Fires specifically when the page-size selector changes |

## 9. CSS parts & custom properties
**Parts**
- `::part(root)` — inner layout flex wrapper
- `::part(prev)` — Previous button
- `::part(next)` — Next button
- `::part(page-list)` — the `<ol>` of page items
- `::part(page-item)` — each `<li>`
- `::part(page-btn)` — each page number button/link
- `::part(ellipsis)` — the ellipsis `<li>` elements
- `::part(page-size)` — the page-size select wrapper
- `::part(summary)` — the results summary text

**Custom properties**
| Property | Default | Description |
|----------|---------|-------------|
| `--mj-pagination-btn-size` | `36px` | Width and height of page number buttons |
| `--mj-pagination-btn-gap` | `var(--mj-spacing-1)` | Gap between buttons in the list |
| `--mj-pagination-current-bg` | `var(--mj-color-primary)` | Background of the current page button |
| `--mj-pagination-current-color` | `var(--mj-color-on-primary)` | Text color of the current page button |
| `--mj-pagination-btn-radius` | `var(--mj-radius-sm)` | Border radius of page buttons |
| `--mj-pagination-font-size` | `var(--mj-font-size-sm)` | Font size for all controls |

## 10. States
- **default** — page 1 active; Previous disabled.
- **last-page** — `page === total-pages`; Next disabled.
- **current-page** — page button has `aria-current="page"` and active token styling.
- **hover** — page buttons show hover background.
- **focus-visible** — focused button shows focus ring.
- **disabled** — all controls have `aria-disabled="true"`; no interaction.
- **single-page** — `total-pages === 1`; Prev and Next both disabled; no numbered pages beyond 1.

## 11. Behavior & interactions
- Page buttons are `<button>` elements by default; if an `href-template` attribute
  is provided (e.g., `"/results?page={page}"`), they are rendered as `<a>` links
  for native navigation and deep-linking.
- Ellipsis items are inserted when the page range would leave gaps:
  `boundary-count` pages always visible at start/end; `sibling-count` pages
  visible around the current page; gaps become `…`.
- When `page` or `total-pages` changes externally (attribute change), the
  component re-renders the page list and updates `aria-current`.
- When `show-page-size` is true, changing the page-size selector fires
  `mj-pagination-page-size-change`; unless canceled, `page` resets to 1 and
  `mj-pagination-change` fires.
- Compact variant shows "Page {page} of {totalPages}" as a text node between
  Prev and Next; no numbered page list.
- Summary text is generated from `total-items`, `page`, and `page-size`;
  overridable via the `summary` slot.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` | Moves focus through Prev, page buttons, Next, page-size select in DOM order |
| `Enter` | Activates the focused page button, Prev, or Next |
| `Space` | Activates a focused `<button>` page control |
| `Shift+Tab` | Reverse focus order |

## 13. Accessibility
- The landmark is `<nav aria-label="Pagination">` (value overridable via `nav-label`).
- The page list is `<ol>` (ordered) to convey sequence.
- The current page button has `aria-current="page"`.
- Disabled Prev/Next buttons have `aria-disabled="true"` and `disabled` attribute.
- Each page button has an accessible name: "Page {n}" (localized via
  `mj.pagination.pageLabel`). The current page button name reads
  "Page {n}, current" via an `aria-label` override.
- Ellipsis items are `aria-hidden="true"` spans, not interactive.
- Previous/Next icons are `aria-hidden`; button text conveys the action.
- The summary text is associated with the nav via `aria-describedby` or placed
  within the `<nav>` for screen-reader context.

## 14. Form participation
N/A — `<mj-pagination>` is a navigation component, not a form control.

## 15. Internationalization & RTL
- `nav-label` is localizable; key `mj.pagination.navLabel`.
- Page button label: `mj.pagination.pageLabel` with `{page}` interpolation.
- Current page button: `mj.pagination.currentPageLabel` with `{page}`.
- Previous/Next labels: `mj.pagination.previous` / `mj.pagination.next`.
- Compact variant label: `mj.pagination.pageOf` with `{page}` and `{total}`.
- Summary template: `mj.pagination.summary` with `{from}`, `{to}`, `{total}`.
- In RTL, Previous and Next buttons swap positions; arrow icons flip via CSS
  `transform: scaleX(-1)` or logical-property equivalents.

## 16. Progressive enhancement / SSR
- Server renders the pagination with `<a href="/results?page=N">` links when
  `href-template` is known server-side; navigation works without JS.
- On upgrade: `<button>` mode replaces link navigation if no `href-template` is
  provided; ARIA roles and `aria-current` are applied.
- The `page` and `total-pages` attributes can be set in server markup; the
  component renders immediately from those values.

## 17. Dependencies
- Section 6: Registry + base element helper, design-token stylesheet,
  localization hook.
- `<mj-select>` — used for the page-size selector when `show-page-size` is true.

## 18. Edge cases & error handling
- **`page` > `total-pages`**: clamped to `total-pages`; console warning emitted.
- **`page` < 1**: clamped to 1.
- **`total-pages` = 0**: component renders with all controls disabled.
- **`total-pages` = 1**: only one page button rendered; Prev and Next disabled.
- **`sibling-count` + `boundary-count` exceeds `total-pages`**: no ellipsis
  rendered; all page numbers shown.
- **Long `total-pages` number (e.g., 9999)**: page buttons do not shrink; the
  `sibling-count` and `boundary-count` defaults keep the rendered count small.

## 19. Acceptance criteria
- [ ] Renders `<nav aria-label="Pagination">` with `<ol>` page list.
- [ ] Current page button has `aria-current="page"`.
- [ ] Previous disabled on page 1; Next disabled on last page.
- [ ] Ellipsis inserted correctly for large page counts.
- [ ] `mj-pagination-change` fires and is cancelable on page change.
- [ ] `href-template` mode renders `<a>` links for all page buttons.
- [ ] `variant="compact"` shows "Page X of Y" only.
- [ ] `show-page-size` adds page-size select; change fires `mj-pagination-page-size-change`.
- [ ] `show-summary` shows "Showing X–Y of Z results" text.
- [ ] RTL: Prev/Next swap; arrow icons flip.
- [ ] SSR: `<a>` link navigation functional before script loads.
- [ ] Automated axe checks pass with zero violations.

## 20. Open questions
- Should the `href-template` pattern support hash-based routing (e.g.,
  `"#page={page}"`) in addition to query-string routing?
- Should a "jump to page" input be a built-in variant or a separate composable
  component?
