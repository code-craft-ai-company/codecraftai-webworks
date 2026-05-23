# Feed Spec

- **Tag:** `<mj-feed>`
- **Class / file:** `MjFeed` / `mjfeed.js`
- **Category:** Layout & content containers (§5.5)
- **Primary or Variant:** Primary
- **Synonyms covered:** Activity feed, streaming content list
- **Phase:** P3
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-feed>` is a scrollable list of feed articles (items of type `article`) that
supports incremental loading as the user scrolls. It implements the WAI-ARIA
`feed` role, which allows screen-reader users to browse articles with dedicated
keyboard shortcuts and understand when more items are loading. It solves the
accessibility and UX needs of activity timelines, news streams, search results,
and social-media-style content lists.

## 2. When to use / when not to use

**Use** for a growing or paginated list of article-type content items that share
a common structure (author, timestamp, content, actions) and that may load
incrementally — social feeds, notification histories, activity timelines.
**Do not use** for a finite static list of navigation links — use a plain `<ul>`.
**Do not use** for tabular data — use `<mj-data-table>`. **Do not use** for
a sequential set of slides — use `<mj-carousel>`.

## 3. Anatomy

- **root** — rendered as a `<div>` with `role="feed"`; surfaced as `::part(root)`.
- **items-container** — scrollable container holding `<mj-feed-item>` children;
  surfaced as `::part(items-container)`.
- **load-more-trigger** — an `IntersectionObserver` sentinel element at the bottom
  of the list that fires a load request.
- **load-more-button** — an explicit "Load more" button as a non-scroll alternative
  to infinite scroll; surfaced as `::part(load-more-button)`.
- **loading-indicator** — shown while new items are fetching; surfaced as
  `::part(loading-indicator)`.
- **empty-state slot** — displayed when there are no items (slot `empty`).

## 4. Variants & modes

| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Infinite scroll (default) | `load-mode="scroll"` | `IntersectionObserver` sentinel triggers `mj-feed-load-more` |
| Button load | `load-mode="button"` | Shows a "Load more" button; no scroll sentinel |
| Static | `load-mode="none"` | No incremental loading; shows only initially slotted items |
| Reverse (newest-first) | `reversed` boolean | Items are inserted and displayed newest-first |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `load-mode` | `"scroll"` \| `"button"` \| `"none"` | `"scroll"` | Yes | How additional items are triggered |
| `loading` | boolean | `false` | Yes | When set, shows the loading indicator and disables the load-more button |
| `has-more` | boolean | `true` | Yes | When false, hides the load-more trigger/button (all items loaded) |
| `reversed` | boolean | `false` | Yes | Feed is in newest-first order |
| `load-more-label` | string | `"Load more"` | Yes | Accessible label for the load-more button; localizable |
| `loading-label` | string | `"Loading"` | Yes | Live-region announcement text while items are loading; localizable |
| `aria-busy` | boolean | `false` | Yes (reflected from `loading`) | Reflects the loading state; set automatically |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `items` | `MjFeedItem[]` (readonly) | Array of all direct `<mj-feed-item>` children |
| `itemCount` | number (readonly) | Number of currently rendered feed items |

## 7. Slots

| Slot | Description |
|------|-------------|
| (default) | One or more `<mj-feed-item>` elements |
| `empty` | Content shown when there are no items and `loading` is false |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-feed-load-more` | `{ itemCount: number }` | Yes | No | Emitted when the scroll sentinel is reached or the load-more button is activated |
| `mj-feed-item-focus` | `{ item: MjFeedItem, index: number }` | Yes | No | Emitted when a feed item receives focus via the feed keyboard navigation |

## 9. CSS parts & custom properties

**Parts**
- `::part(root)` — the feed container with `role="feed"`
- `::part(items-container)` — the scrollable items region
- `::part(load-more-button)` — the explicit load-more button
- `::part(loading-indicator)` — the loading state indicator
- `::part(empty)` — the empty state container

**Custom properties**
| Property | Default token | Description |
|----------|--------------|-------------|
| `--mj-feed-gap` | `--mj-space-4` | Gap between feed items |
| `--mj-feed-max-width` | `none` | Maximum width of the items container |
| `--mj-feed-padding` | `0` | Padding around the items container |

## 10. States

- **default** — items displayed; load-more trigger active.
- **loading** — `aria-busy="true"` on root; loading indicator visible; load-more button disabled.
- **all-loaded** — `has-more="false"`; load-more trigger/button hidden.
- **empty** — no items slotted; `empty` slot content displayed.

## 11. Behavior & interactions

In `load-mode="scroll"` mode an `IntersectionObserver` watches a sentinel element
placed after the last feed item. When the sentinel enters the viewport and `loading`
is false and `has-more` is true, `mj-feed-load-more` is emitted. The consuming
application must handle this event, fetch additional items, append `<mj-feed-item>`
children, and then clear the `loading` attribute.

In `load-mode="button"` mode the sentinel is replaced by the load-more button.

New items appended to the default slot are announced via a polite live region:
"N new items added" (N is the count of newly added items, using the Section 6
localization hook).

When `reversed` is set, items are rendered in `flex-direction: column-reverse`
so the newest item appears at the top, and the scroll sentinel is at the top as
well for prepend-style feeds.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Page Down` | Move focus to the next feed item (APG feed pattern) |
| `Page Up` | Move focus to the previous feed item |
| `Ctrl+End` | Move focus to the last feed item |
| `Ctrl+Home` | Move focus to the first feed item |
| `Tab` | Move focus through interactive elements inside the focused feed item |

## 13. Accessibility

- Root element has `role="feed"` and `aria-busy` reflecting the `loading` state.
- Each `<mj-feed-item>` has `role="article"` and must have an accessible name
  (from a heading or `aria-label`).
- Feed items expose their position: `aria-setsize` and `aria-posinset` are set
  on each `<mj-feed-item>`. When total count is unknown (streaming), `aria-setsize`
  is set to `-1`.
- `Page Down`/`Page Up` move focus between articles per the APG feed pattern;
  this is managed by a keydown listener on the feed root.
- A polite live region announces new item counts when items are appended.
- The load-more button has a clear accessible name and is disabled while loading.

## 14. Form participation

N/A — `<mj-feed>` is a content list component and does not participate in forms.

## 15. Internationalization & RTL

`load-more-label` and `loading-label` and the "N new items" announcement are
routed through the Section 6 localization hook. RTL layout uses logical CSS
properties. Timestamps inside `<mj-feed-item>` are formatted by the item
component using `Intl.DateTimeFormat`.

## 16. Progressive enhancement / SSR

The server renders a list of `<mj-feed-item>` elements (static articles). Before
upgrade a plain semantic list is presented. After upgrade the component attaches
the `role="feed"`, the `IntersectionObserver` sentinel, and the keyboard
navigation. The SSR items remain in the DOM unchanged.

## 17. Dependencies

- Section 6: Registry + base element helper; design-token stylesheet; live-region/
  announcement service; localization hook; collection/virtualization utility
  (optional, for very long feeds).
- `<mj-feed-item>` — companion micro-component (`mjfeeditem.js`).
- `<mj-empty-state>` — recommended for the `empty` slot.
- `IntersectionObserver` (native browser API).

## 18. Edge cases & error handling

- **Load failure** — the consuming application must set `loading="false"` and
  display an error (e.g., an Alert) inside the `empty` slot or via a Toast;
  the feed itself does not handle network errors.
- **`has-more` set to false before all items render** — load-more trigger/button
  is hidden immediately; no sentinel firing.
- **Very long feeds** — `<mj-feed>` does not virtualize by default; the optional
  `virtualize` boolean attribute activates the Section 6 windowed list engine.
- **Items removed from the DOM** — `aria-posinset` is re-calculated across all
  remaining items via a `MutationObserver` on the default slot.
- **`reversed` toggled at runtime** — layout re-applies; `aria-posinset` order
  is recalculated.

## 19. Acceptance criteria

- [ ] Root has `role="feed"` and `aria-busy` reflects the `loading` attribute.
- [ ] Each `<mj-feed-item>` has `role="article"` with `aria-setsize` and `aria-posinset`.
- [ ] `Page Down`/`Page Up` move focus between feed items.
- [ ] `load-mode="scroll"` emits `mj-feed-load-more` when the sentinel enters the viewport.
- [ ] `load-mode="button"` shows a button that emits `mj-feed-load-more` on activation.
- [ ] `has-more="false"` hides the sentinel/button.
- [ ] Polite live region announces new item count when items are appended.
- [ ] `empty` slot content is shown when no items are slotted and `loading` is false.
- [ ] `reversed` displays items newest-first.
- [ ] Automated accessibility check passes with no violations.

## 20. Open questions

- Should `aria-setsize` be left as `-1` until the application explicitly sets the total count via a `total-count` attribute, to avoid misleading screen-reader users when the full set size is unknown?
- Should the virtualization option be a boolean `virtualize` attribute or should it be delegated entirely to the application via a custom slot and `IntersectionObserver`?
