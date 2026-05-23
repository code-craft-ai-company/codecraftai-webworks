# Activity Feed Spec

- **Tag:** `<mj-activity-feed>`
- **Class / file:** `ActivityFeed` / `activityfeed.js`
- **Category:** Application & productivity components
- **Primary or Variant:** Primary
- **Synonyms covered:** Activity stream, Event feed, Audit log feed
- **Phase:** P3
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-activity-feed>` renders a chronological, reverse-chronological, or grouped stream of activity events (user actions, system events, audit entries) with author avatars, relative timestamps, action descriptions, and optional metadata. It supports incremental loading of older items, real-time prepending of new items, and correct `feed` ARIA semantics for screen readers.

## 2. When to use / when not to use
Use for displaying a running log of user or system activity where events arrive over time and older events can be loaded on demand (project activity, audit trails, notification history). Do not use for threaded conversational content — use `<mj-comments>`. Do not use for a simple list of records — use `<mj-data-table>`.

## 3. Anatomy
- **feed root** — `<div role="feed" aria-busy="false">` with `aria-label`.
- **new-items banner** — dismissible `<mj-button>` strip that appears when new items arrive in real-time: "N new events. Click to view."
- **activity items** — `<article>` elements inside the feed; each has `aria-labelledby` pointing to the item's heading.
- **item avatar** — `<mj-avatar>` of the acting user or system.
- **item header** — actor name, action description, and relative timestamp `<time>`.
- **item body** — optional rich content (comment text, metadata diff, link).
- **item actions** — optional action links or buttons (e.g., "View", "Reply").
- **load-more trigger** — "Load older activity" `<mj-button>` or IntersectionObserver sentinel.
- **empty state** — `<mj-empty-state>` when no events exist.

## 4. Variants & modes
| Variant / mode | Attribute | Behavior difference |
|----------------|-----------|---------------------|
| Compact | `compact` | Avatar smaller; body hidden; single-line items |
| Grouped | `group-by="date"` | Items grouped under date headings |
| Real-time | `realtime` | New items prepended via `addItem()`; new-items banner shown |
| Load-more button | `load-mode="button"` (default) | Explicit button to load older items |
| Infinite scroll | `load-mode="infinite"` | IntersectionObserver at the bottom |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `label` | string | `"Activity feed"` | Yes | `aria-label` on the feed root |
| `compact` | boolean | `false` | Yes | Compact single-line variant |
| `group-by` | `""\|"date"` | `""` | Yes | Groups items under date headings |
| `load-mode` | `"button"\|"infinite"` | `"button"` | Yes | Load-older strategy |
| `realtime` | boolean | `false` | Yes | Enables real-time new-item prepend with banner |
| `empty-message` | string | `"No activity yet."` | Yes | Message for the empty state |
| `timestamp-format` | `"relative"\|"absolute"\|"both"` | `"relative"` | Yes | How timestamps are displayed |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `items` | `ActivityItem[]` | Current list of items: `{ id, actor, action, body?, timestamp, meta? }` |
| `dataSource` | `DataSourceAdapter \| null` | Async source; called with cursor for paged load |
| `addItem` | `(item: ActivityItem) => void` | Prepends a new item in real-time; increments banner count |
| `newItemCount` | number | Read-only count of prepended items not yet scrolled into view |

## 7. Slots
| Slot | Description |
|------|-------------|
| `item-{type}` | Custom template for a specific activity `type`; receives `item` via context |
| `empty` | Replaces the built-in empty state |
| `loading` | Replaces the built-in skeleton placeholders |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-load-older` | `{ cursor: string \| null }` | Yes | No | Fires when user requests older items |
| `mj-new-items-viewed` | `{ count: number }` | Yes | No | Fires when the new-items banner is dismissed |
| `mj-item-action` | `{ itemId: string, action: string }` | Yes | No | Fires when an item action button is activated |

## 9. CSS parts & custom properties
**Parts:** `root`, `new-banner`, `item`, `item-avatar`, `item-header`, `item-actor`, `item-action-text`, `item-timestamp`, `item-body`, `item-actions`, `group-heading`, `load-more`, `empty-state`.

| Custom property | Default | Description |
|-----------------|---------|-------------|
| `--mj-feed-gap` | `var(--mj-space-4)` | Gap between activity items |
| `--mj-feed-avatar-size` | `var(--mj-size-avatar-sm)` | Avatar size |
| `--mj-feed-line-color` | `var(--mj-color-border)` | Color of the connecting timeline line |
| `--mj-feed-line-width` | `2px` | Width of the timeline line |
| `--mj-feed-timestamp-color` | `var(--mj-color-text-secondary)` | Timestamp text color |
| `--mj-feed-new-banner-bg` | `var(--mj-color-accent-subtle)` | New-items banner background |

## 10. States
- **default** — feed loaded, items displayed.
- **loading** — initial load; skeleton placeholders shown; `aria-busy="true"`.
- **loading-older** — load-more spinner appended at the bottom; `aria-busy="true"`.
- **empty** — no items; empty state displayed.
- **has-new** — `realtime` mode; banner showing new-item count.
- **error** — data source failure; error alert with retry.

## 11. Behavior & interactions
On mount, if `dataSource` is set, the component calls `dataSource.fetch({ cursor: null })` and renders returned items. The `cursor` for the next page is stored internally. On "Load older", it calls `dataSource.fetch({ cursor: lastCursor })` and appends results. Relative timestamps are computed with `Intl.RelativeTimeFormat` and refreshed every 60 seconds. When `timestamp-format="both"`, the `<time>` element shows the relative label and has a `title` / `aria-label` with the absolute formatted date. When `realtime` is enabled and `addItem()` is called, the new item is prepended to the DOM; if the feed is not scrolled to the top, a sticky banner counts new items. Dismissing the banner scrolls to the top.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` / `Shift+Tab` | Navigate between focusable elements (links, buttons, load-more) |
| `Page Down` (within feed) | Advance to next article per APG Feed pattern |
| `Page Up` (within feed) | Return to previous article |
| `Home` (within feed) | Move to first article |
| `End` (within feed) | Move to last article |
| `Enter` / `Space` on new-banner | Scroll feed to top; dismiss banner |

## 13. Accessibility
Root carries `role="feed"` with `aria-label` and `aria-busy` reflecting load state. Each item is an `<article>` with `aria-labelledby` pointing to the item heading (actor + action line). `aria-setsize="-1"` and `aria-posinset` are set per item when total count is unknown. The new-items banner is `role="status"` with polite live region. When new items are prepended, the feed announces "N new activities" politely. Timestamps are `<time datetime="ISO-8601">` with human-readable content; absolute form provided via `aria-label` when `timestamp-format="relative"`. Relative timestamps automatically update; each update is NOT re-announced (no live region on the timestamp itself).

## 14. Form participation
N/A — display component.

## 15. Internationalization & RTL
All user-facing strings (empty message, new-banner label, load-more label) are overridable. Timestamps use `Intl.RelativeTimeFormat` and `Intl.DateTimeFormat` with document locale. In RTL, the avatar appears on the inline-end side and the timeline line on the inline-end.

## 16. Progressive enhancement / SSR
Server renders a `<section>` with a `<ul>` of activity items as static HTML. Without JS, all items are visible as plain text. On upgrade the component attaches the `role="feed"` pattern, live timestamp refresh, real-time prepend, and load-more behavior.

## 17. Dependencies
- **Foundations:** Registry + base element helper, Design-token stylesheet, Live-region/announcement service, Data-source adapter interface, Localization/formatting hook.
- **Components:** `<mj-avatar>`, `<mj-button>`, `<mj-skeleton-loader>`, `<mj-empty-state>`, `<mj-alert>`.

## 18. Edge cases & error handling
- Duplicate item IDs: component deduplicates by `id`; a console warning is emitted.
- `addItem()` called while initial load is in progress: items queued and prepended after load.
- Very long `body` content: clamped to 4 lines with a "Show more" inline toggle.
- Group-by date with missing timestamps: items placed in an "Unknown date" group.
- Load-older returns empty array: "Load older" button hidden; "All activity loaded" announced politely.

## 19. Acceptance criteria
- [ ] `role="feed"` with `aria-label` and correct `aria-busy` state.
- [ ] Each item is `<article>` with `aria-labelledby` pointing to its heading.
- [ ] Page Down/Up navigate between articles per APG Feed pattern.
- [ ] Relative timestamps refresh every 60 s without live-region re-announcement.
- [ ] `addItem()` prepends item; banner count increments; scroll-to-top dismisses banner.
- [ ] `mj-load-older` fires with correct cursor on load-more activation.
- [ ] Empty state visible when `items` is empty and not loading.
- [ ] Axe scan reports zero violations.
- [ ] Light, dark, high-contrast, and RTL rendering verified.

## 20. Open questions
- Should items support inline reactions (emoji reactions) natively, or only via the `item-actions` slot?
- Should grouped-by-date grouping render a sticky date heading on scroll?
