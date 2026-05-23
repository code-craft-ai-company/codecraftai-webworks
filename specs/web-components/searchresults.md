# Search Results Spec

- **Tag:** `<mj-search-results>`
- **Class / file:** `SearchResults` / `searchresults.js`
- **Category:** Application & productivity components
- **Primary or Variant:** Primary
- **Synonyms covered:** Search result list, Result set
- **Phase:** P3
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-search-results>` renders a ranked list of search results, each with a title, URL/source, snippet with highlighted match terms, and optional relevance metadata (score, category, date). It manages the result count announcement, empty state, loading state, and pagination or infinite-scroll loading. It is designed to bind to the data-source adapter so it can work with any search backend.

## 2. When to use / when not to use
Use for any search interface that returns a ranked, paginated list of items with text snippets and metadata. Do not use for filter-only result grids (use `<mj-filter-panel>` + a `<mj-data-table>`). Do not use for autocomplete suggestion lists (use `<mj-combobox>`).

## 3. Anatomy
- **result count bar** — visually prominent count ("About 1,240 results"); `role="status"` for live announcement.
- **result list** — `<ul role="list">` of result items.
- **result item** — `<li>` with title link (`<a>`), breadcrumb/URL, snippet, and optional metadata chips.
- **match highlight** — `<mark>` elements within the snippet for matched terms.
- **empty state** — `<mj-empty-state>` shown when `results` is an empty array and `loading` is false.
- **loading state** — `<mj-skeleton-loader>` placeholders shown while `loading` is true.
- **pagination / load-more** — `<mj-pagination>` or a "Load more" `<mj-button>` at the bottom, driven by `load-mode`.

## 4. Variants & modes
| Variant / mode | Attribute | Behavior difference |
|----------------|-----------|---------------------|
| Paginated | `load-mode="paginate"` (default) | Shows `<mj-pagination>` below results |
| Infinite scroll | `load-mode="infinite"` | IntersectionObserver triggers `mj-load-more` event |
| Load-more button | `load-mode="button"` | "Load more" button at bottom; non-scroll alternative |
| Compact | `compact` | Reduced spacing; snippet hidden; title + URL only |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `total-count` | number | `0` | Yes | Total result count from the backend; displayed in the count bar |
| `loading` | boolean | `false` | Yes | Shows skeleton placeholders instead of results |
| `load-mode` | `"paginate"\|"infinite"\|"button"` | `"paginate"` | Yes | Pagination strategy |
| `page` | number | `1` | Yes | Current page (paginated mode) |
| `page-size` | number | `10` | Yes | Results per page |
| `empty-message` | string | `"No results found."` | Yes | Message shown in the empty state |
| `empty-suggestion` | string | `""` | Yes | Suggestion text below the empty message |
| `compact` | boolean | `false` | Yes | Compact display variant |
| `highlight-term` | string | `""` | Yes | Term(s) to highlight in snippets (space-separated) |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `results` | `SearchResult[]` | Array of result objects `{ id, title, url, snippet, score?, category?, date?, meta? }` |
| `dataSource` | `DataSourceAdapter \| null` | Pluggable async data source; when set, the component fetches pages automatically |

## 7. Slots
| Slot | Description |
|------|-------------|
| `result-actions` | Additional action buttons per result (scoped via `data-result-id`) |
| `empty` | Replaces the built-in empty state |
| `loading` | Replaces the built-in skeleton placeholders |
| `count-prefix` | Content before the count number (e.g., "About") |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-result-select` | `{ result: SearchResult, index: number }` | Yes | No | Fires when a result title link is activated |
| `mj-page-change` | `{ page: number, pageSize: number }` | Yes | No | Fires when the user navigates to a new page |
| `mj-load-more` | `{ page: number, pageSize: number }` | Yes | No | Fires in infinite/button mode when more results are requested |

## 9. CSS parts & custom properties
**Parts:** `root`, `count-bar`, `result-list`, `result-item`, `result-title`, `result-url`, `result-snippet`, `result-meta`, `empty-state`, `pagination`.

| Custom property | Default | Description |
|-----------------|---------|-------------|
| `--mj-results-gap` | `var(--mj-space-4)` | Gap between result items |
| `--mj-results-title-color` | `var(--mj-color-link)` | Result title link color |
| `--mj-results-url-color` | `var(--mj-color-text-secondary)` | URL/breadcrumb color |
| `--mj-results-highlight-bg` | `var(--mj-color-highlight)` | Background of `<mark>` highlights |
| `--mj-results-highlight-color` | `var(--mj-color-highlight-text)` | Text color of highlights |
| `--mj-results-count-size` | `var(--mj-font-size-sm)` | Font size for the count bar |

## 10. States
- **default** — results list rendered, count bar showing.
- **loading** — skeleton placeholders shown; `loading` attribute set; `aria-busy="true"` on list.
- **empty** — no results; empty state shown; count bar shows "0 results".
- **error** — `dataSource` fetch failed; error alert shown via `<mj-alert severity="error">`.
- **item-focused** — result title link has focus-visible ring.
- **item-hovered** — result title link shows hover underline.

## 11. Behavior & interactions
When `dataSource` is set, the component calls `dataSource.fetch({ page, pageSize, query })` on mount and whenever `page` or `pageSize` changes. Returned items are set on `results`; `total-count` is updated from the response metadata. Match highlights are applied by wrapping occurrences of `highlight-term` tokens in `<mark>` elements using a text-node walker (sanitized against XSS — no innerHTML with user data). In infinite-scroll mode an `IntersectionObserver` targets a sentinel element at the bottom; when visible and not loading, `mj-load-more` is emitted and new results are appended to the list.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` | Moves focus through result title links and any action buttons |
| `Enter` | Activates the focused result link |
| `Tab` to pagination | Reaches page controls; `ArrowLeft`/`ArrowRight` navigate pages |

## 13. Accessibility
The count bar uses `role="status"` and `aria-live="polite"` to announce count changes when results update. The result list is a `<ul>` so screen readers announce item count. Each result title is an `<a>` — real links, not divs. `<mark>` elements carry no ARIA modifications; browsers announce them as highlighted text. While loading, the list root has `aria-busy="true"` and a polite announcement "Loading results" is injected via the live-region service. After load: "N results loaded". The empty state includes a heading and suggestion, not just an image.

## 14. Form participation
N/A — display component.

## 15. Internationalization & RTL
`empty-message`, `empty-suggestion`, and `count-prefix` are localizable attributes. The count number is formatted with `Intl.NumberFormat` using the document locale. Dates in result metadata are formatted with `Intl.DateTimeFormat`. In RTL, the result URL/breadcrumb direction is set to `ltr` explicitly (URLs are always LTR).

## 16. Progressive enhancement / SSR
Server renders the result list as a plain `<ul>` with `<li>` items containing `<a>` links. Without JS the list is fully readable and navigable. On upgrade the component attaches the live-region count bar, adds skeleton loading behavior, and attaches the pagination or infinite-scroll mechanism.

## 17. Dependencies
- **Foundations:** Registry + base element helper, Design-token stylesheet, Live-region/announcement service, Data-source adapter interface, Collection/virtualization utility, Localization/formatting hook.
- **Components:** `<mj-pagination>`, `<mj-button>` (load-more), `<mj-empty-state>`, `<mj-skeleton-loader>`, `<mj-alert>`.

## 18. Edge cases & error handling
- `total-count` larger than actual `results` array: component renders what it has; count bar shows `total-count`.
- Single result: count bar says "1 result" (singular); localization hook manages plural forms.
- Very long snippet: clamped to 3 lines via CSS `-webkit-line-clamp`; full text accessible on the linked page.
- `highlight-term` with regex-special characters: escaped before matching.
- DataSource fetch error: renders an inline `<mj-alert>` with retry button; does not clear previous results.
- All results on one page: pagination hidden (only one page).

## 19. Acceptance criteria
- [ ] Count bar announces changes via live region on every results update.
- [ ] `aria-busy="true"` set during loading; cleared on completion.
- [ ] Empty state rendered (not just blank) when `results` is empty and not loading.
- [ ] `<mark>` highlights visible for each `highlight-term` occurrence in snippets.
- [ ] `mj-result-select` fires with correct `result` and `index`.
- [ ] Infinite scroll: `mj-load-more` fires when sentinel enters viewport; results append.
- [ ] Paginated: `mj-page-change` fires; new page loaded; focus moves to first new result.
- [ ] RTL: URL breadcrumb direction stays LTR.
- [ ] Axe scan reports zero violations.
- [ ] Light, dark, high-contrast, and RTL rendering verified.

## 20. Open questions
- Should result items support keyboard-shortcut quick-open (e.g., number keys 1–9)?
- Should the component own grouping results by category (tabbed or sectioned), or leave that to a wrapper?
