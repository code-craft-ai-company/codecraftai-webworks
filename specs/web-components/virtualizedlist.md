# Virtualized List Spec

- **Tag:** `<mj-virtual-list>`
- **Class / file:** `MjVirtualList` / `mjvirtuallist.js`
- **Category:** Tables, lists & structured data
- **Primary or Variant:** Primary
- **Synonyms covered:** Virtualized list, Infinite-scroll list, Windowed list
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-virtual-list>` renders arbitrarily large one-dimensional lists with windowed
(virtualized) DOM rendering so that only the items visible in the scroll viewport
plus a small overscan are in the DOM at any time. It supports fixed and variable
item heights, infinite/incremental loading via a data adapter, and a non-scroll
"Load more" alternative for keyboard and AT users. It is the correct choice for
feeds, search results, log streams, and any list whose item count is unknown or
large enough to cause performance problems in a full render.

## 2. When to use / when not to use
**Use** when the list has more than ~200 items, when items arrive incrementally
(streaming/infinite), or when item rendering is expensive. **Do not use** for
small, static lists — use `<mj-list>`. For tabular data use `<mj-data-table>`.
For hierarchical lists use `<mj-tree-grid>`.

## 3. Anatomy
- **Scroll container** — fixed-height `<div>` with `overflow-y: auto`; the component's
  Shadow DOM root.
- **Spacer top / bottom** — zero-content `<div>` elements whose heights encode the
  positions of un-rendered items above and below the window.
- **Item pool** — a fixed-size array of DOM nodes that are repositioned and have their
  content swapped as the user scrolls (recycling/pooling strategy).
- **Load-more sentinel** — an `IntersectionObserver` target at the bottom; triggers
  the next page fetch when it enters the viewport.
- **Load-more button** — always-visible fallback button at the bottom of the list
  for keyboard/AT users; announces item count after each load.
- **Status region** — `aria-live="polite"` region announcing count changes, errors,
  and end-of-list.

## 4. Variants & modes
| Variant | `load-strategy` value | Behavior |
|---------|----------------------|----------|
| Infinite scroll | `intersection` (default) | Sentinel triggers fetch automatically. |
| Manual load | `manual` | Only the "Load more" button triggers fetch. |
| Paged | `paged` | Fetches a full page; renders with pagination controls at bottom. |

Item sizing mode via `item-size`:
- `fixed` (default) — all items share `--mj-vl-item-height`; positioning is O(1).
- `variable` — item heights are measured on render and cached; re-measured on resize.

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `load-strategy` | `intersection\|manual\|paged` | `intersection` | yes | How new items are loaded. |
| `item-size` | `fixed\|variable` | `fixed` | yes | Item height mode. |
| `item-height` | number | `48` | yes | Fixed item height in px (`fixed` mode only). |
| `overscan` | number | `3` | yes | Items rendered above and below the visible window. |
| `page-size` | number | `50` | yes | Items requested per adapter fetch. |
| `total` | number | `-1` | yes | Known total item count; `-1` means unknown. |
| `loading` | boolean | false | yes | True while a fetch is in progress. |
| `error` | boolean | false | yes | True after a fetch failure. |
| `end-of-list` | boolean | false | yes | True when adapter reports no more items. |
| `load-more-label` | string | `"Load more"` | yes | Accessible label for the manual load button. |
| `empty-label` | string | `"No items"` | yes | Text shown when list is empty. |
| `orientation` | `vertical\|horizontal` | `vertical` | yes | Scroll axis. |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `dataSource` | `ListDataSourceAdapter` | `{ fetch(offset: number, count: number): Promise<{ items: unknown[], total?: number }> }` |
| `items` | `unknown[]` | Client-side data array; used instead of `dataSource`. Setting appends to or replaces the internal list depending on `appendItems()` vs. direct assignment. |
| `renderItem` | `(item: unknown, index: number) => HTMLElement \| string` | Custom item renderer function; if not set, the `item` slot template is cloned. |
| `keyExtractor` | `(item: unknown, index: number) => string` | Returns a stable string key for each item; used for DOM recycling identity. |

## 7. Slots
| Slot | Description |
|------|-------------|
| `item` | Template element whose content is cloned and populated for each rendered item. Receives `data-index` and `data-key` attributes. |
| `loading` | Content shown while a fetch is in progress (default: spinner + text). |
| `error` | Content shown after a fetch failure; should contain a retry action. |
| `empty` | Content shown when the list has zero items. |
| `end` | Content shown after the last item when `end-of-list` is true. |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-load-more` | `{ offset: number, pageSize: number }` | true | false | Fired when a new page should be loaded (intersection or manual). |
| `mj-items-rendered` | `{ startIndex: number, endIndex: number, total: number }` | true | false | Fired after each render window update. |
| `mj-scroll-end` | `{ scrollTop: number }` | true | false | Fired when user scrolls to or near the bottom. |
| `mj-item-click` | `{ index: number, key: string, item: unknown }` | true | false | Fired when a rendered item is clicked/activated. |

## 9. CSS parts & custom properties
**Parts:** `container`, `item`, `spacer-top`, `spacer-bottom`, `load-more-button`,
`loading-indicator`, `error-state`, `empty-state`, `end-state`, `status-region`.

| Custom property | Default | Purpose |
|----------------|---------|---------|
| `--mj-vl-item-height` | `48px` | Fixed item height (synced with `item-height` attribute). |
| `--mj-vl-container-height` | `400px` | Scroll container height. |
| `--mj-vl-gap` | `0px` | Gap between items. |
| `--mj-vl-padding` | `0px` | Padding inside scroll container. |
| `--mj-vl-focus-outline` | `2px solid token(--mj-color-focus)` | Focus ring on interactive items. |

## 10. States
- **default** — items visible; normal scroll.
- **loading** — spinner shown; `aria-busy="true"` on the scroll container; `loading` attribute present.
- **loading-more** — existing items visible; spinner shown at bottom.
- **error** — `slot="error"` shown at bottom; `error` attribute present.
- **empty** — `slot="empty"` shown; `total === 0`.
- **end-of-list** — `slot="end"` shown; `end-of-list` attribute present; load-more button hidden.

## 11. Behavior & interactions
**Windowed rendering:** The scroll container fires `scroll` events (throttled via
`requestAnimationFrame`). The engine calculates the first visible index as
`Math.floor(scrollTop / itemHeight)` in fixed mode, or via a binary search over the
cached height array in variable mode. It renders items in the range
`[firstVisible - overscan, lastVisible + overscan]` clamped to `[0, items.length)`.
Spacer heights encode the un-rendered regions.

**Item pooling:** A pool of `Math.min(visibleCount + 2*overscan, items.length)` DOM
nodes is maintained. As the window shifts, items sliding out of view are
repopulated with new data and repositioned using `transform: translateY()` (avoids
layout thrash). `keyExtractor` provides stable identity for items that have
in-DOM state (e.g., expanded accordions within items).

**Infinite scroll (`intersection` mode):** An `IntersectionObserver` watches the
bottom sentinel. When it enters the viewport and `loading` is false and
`end-of-list` is false, `mj-load-more` is fired. The adapter resolves with new
items which are appended to the internal list. If the adapter returns fewer items
than `page-size`, `end-of-list` is set to `true`.

**Manual load:** The "Load more" button is always visible (below the last item) when
`end-of-list` is false. Click emits `mj-load-more`. In `intersection` mode the
button is also shown as a non-scroll fallback but the sentinel remains active.

**Variable height mode:** On first render each item's height is measured via
`getBoundingClientRect()`. Heights are cached by key. On window resize, a
`ResizeObserver` on the container triggers a re-measurement pass. The spacer
heights and scroll position are corrected.

**Stable scroll position:** When new items are prepended (streaming mode), the
scroll position is adjusted by the pixel height of prepended items so the user's
viewport does not jump.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` | Moves focus to the next focusable element (items with links/buttons, load-more button). |
| `Arrow Down / Up` | No built-in item navigation (list is not a composite widget); browser native scroll. |
| `Enter` / `Space` | Activates a focused item's primary action or the load-more button. |
| `Page Down / Up` | Scrolls the container by one viewport height. |
| `Home` / `End` | Scrolls to the top/bottom of the list (when scroll container is focused). |

## 13. Accessibility
- Scroll container: `role="feed"` for streaming/incremental content (WAI-ARIA `feed` pattern); `aria-busy` reflects loading state.
- Each item: `role="article"` (within a `feed`); `aria-posinset` and `aria-setsize` reflect index and total when known.
- When `total` is `-1`, `aria-setsize="-1"` signals unknown total to AT.
- Load-more button: `aria-label` set to `load-more-label` attribute; `aria-disabled` when loading.
- Status region: `aria-live="polite"` announces "{n} items loaded" after each page, "End of list reached", and error messages.
- Error state: `role="alert"` used for fetch errors to announce urgently.
- Empty state: announced via `role="status"` politely.

## 14. Form participation
N/A — display/navigation component.

## 15. Internationalization & RTL
- `orientation="horizontal"` uses `dir`-aware scroll axis (`scrollLeft` adjusted for RTL).
- All UI strings (`load-more-label`, `empty-label`, status announcements) are overridable via attributes.
- Live region text must be provided pre-translated by the caller or via the localization hook.

## 16. Progressive enhancement / SSR
Server renders the first page of items as a plain `<ul>/<li>` structure inside
`<mj-virtual-list>`. Before JS the full first page is readable and a standard
`<a>` pagination link loads the next page. On upgrade the component replaces the
static list with the windowed container, sets `items` to the server-rendered data,
and attaches the scroll/intersection engine.

## 17. Dependencies
- Collection/virtualization utility (§6).
- Data-source adapter interface (§6).
- Live-region/announcement service (§6).
- Base element helper (§6).
- Design-token stylesheet (§6).

## 18. Edge cases & error handling
- **Adapter fetch fails** — `error` state set; `slot="error"` shown; `mj-load-more` can be retried by the user.
- **Items prepended at index 0** — scroll position corrected by prepended item heights to prevent jump.
- **`total` decreases** (item deleted externally) — component clamps rendered range; `aria-setsize` updated.
- **`item-height` changed after render** — pool is rebuilt and scroll position recalculated.
- **Container height is zero** — no items rendered; observer registered but not triggered until height becomes positive.
- **All items hidden by external filter** — `slot="empty"` shown even if `total > 0`.

## 19. Acceptance criteria
- [ ] Only visible rows + overscan in DOM; spacer heights encode un-rendered items.
- [ ] `role="feed"` on container; each item `role="article"` with `aria-posinset` and `aria-setsize`.
- [ ] `aria-busy="true"` during loading; polite live region announces count after each page.
- [ ] `intersection` mode: sentinel triggers `mj-load-more`; items append; `end-of-list` set when adapter exhausted.
- [ ] `manual` mode: load-more button always visible; triggers `mj-load-more` on click/Enter.
- [ ] Variable height mode: heights measured and cached; spacers correct; scroll position stable on resize.
- [ ] Stable scroll when items prepended.
- [ ] Error state: `role="alert"` announced; retry action re-fires `mj-load-more`.
- [ ] Empty state: `slot="empty"` shown when `items.length === 0`.
- [ ] `Home`/`End` scroll to top/bottom of container.
- [ ] SSR: first page readable without JS.
- [ ] axe audit passes with zero violations.

## 20. Open questions
- Should horizontal virtualization (`orientation="horizontal"`) be in scope for P1 or deferred?
- Should a `pull-to-refresh` affordance be included for mobile touch contexts?
- Key-based item identity: should `keyExtractor` be required or optional with a fallback to index?
