# Notification Center Spec

- **Tag:** `<mj-notification-center>`
- **Class / file:** `MjNotificationCenter` / `mjnotificationcenter.js`
- **Category:** Dialogs, overlays & popups / Feedback & status
- **Primary or Variant:** Primary
- **Synonyms covered:** Notification center, Notification inbox, Notification panel, Notification history
- **Phase:** P2
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-notification-center>` is a persistent notification history panel. While `<mj-toast-region>` handles transient auto-dismissing messages, this component stores, displays, and manages a scrollable list of past and current notifications. It supports read/unread state, grouping, dismissal, and mark-all-read. It is typically surfaced inside a `<mj-drawer>` or a `<mj-popover>` triggered by a bell icon button.

## 2. When to use / when not to use

Use when the application generates notifications that users need to revisit — activity alerts, system messages, approvals, or mentions. Pair with `<mj-toast-region>` so real-time alerts surface as toasts and are archived here. Do not use as a real-time chat interface (use ChatMessage + Feed). Do not replace inline form errors or critical alerts (use Alert/Dialog).

## 3. Anatomy

- **Panel container** — the root, scrollable list of notification items.
- **Header bar** — title, unread count badge, "Mark all read" and "Clear all" actions.
- **Notification item** — each entry with icon/avatar, title, body, timestamp, read/unread indicator, and dismiss button.
- **Group headers** — optional date-based or category-based section labels.
- **Empty state** — illustration and message when no notifications exist.
- **Loading state** — skeleton items while data is being fetched.
- **Footer** — optional "Load more" or pagination control.

## 4. Variants & modes

| Variant | `variant` value | Notes |
|---------|----------------|-------|
| Panel (default) | `panel` | Standalone scrollable list, composable inside Drawer or Popover |
| Inline | `inline` | Embedded in page content; no floating surface |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `variant` | `panel` \| `inline` | `panel` | Yes | Display mode |
| `max-items` | number | `100` | Yes | Maximum number of stored items; oldest are evicted |
| `group-by` | `none` \| `date` \| `category` | `date` | Yes | Grouping strategy for notification items |
| `show-mark-all-read` | boolean | `true` | Yes | Shows the "Mark all read" toolbar action |
| `show-clear-all` | boolean | `true` | Yes | Shows the "Clear all" toolbar action |
| `loading` | boolean | `false` | Yes | Shows loading skeleton state |
| `empty-message` | string | `"No notifications"` | Yes | Message shown in empty state |
| `label` | string | `"Notifications"` | Yes | Accessible name for the panel region |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `items` | `NotificationItem[]` | The full list of notification items; `NotificationItem` has `{ id, title, body, timestamp, read, category, severity, href, avatarSrc, avatarAlt }` |
| `unreadCount` | `number` | Count of items where `read === false` |
| `selectedItem` | `NotificationItem \| null` | The currently focused/selected item |

## 7. Slots

| Slot | Description |
|------|-------------|
| `header` | Custom header content replacing the built-in title + actions bar |
| `empty` | Custom empty state content |
| `footer` | Footer area (e.g., "View all notifications" link) |
| `item-icon` | Per-item icon override; receives item data via `data-item-id` |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-notification-select` | `{ item: NotificationItem }` | Yes | No | Fired when a notification item is activated (click or Enter) |
| `mj-notification-dismiss` | `{ item: NotificationItem }` | Yes | Yes | Fired when a single item is dismissed; cancelable to prevent removal |
| `mj-notification-read` | `{ item: NotificationItem }` | Yes | No | Fired when a single item is marked read |
| `mj-notification-mark-all-read` | `{ count: number }` | Yes | No | Fired when "Mark all read" is activated |
| `mj-notification-clear-all` | `{ count: number }` | Yes | Yes | Fired when "Clear all" is activated; cancelable |
| `mj-notification-load-more` | `{ offset: number }` | Yes | No | Fired when the "Load more" footer control is activated |

## 9. CSS parts & custom properties

**Parts:**
- `::part(panel)` — the outer panel container
- `::part(header)` — the header bar
- `::part(title)` — the panel title text
- `::part(badge)` — the unread count badge
- `::part(mark-all-read)` — the "Mark all read" button
- `::part(clear-all)` — the "Clear all" button
- `::part(list)` — the `<ul>` list of items
- `::part(group-header)` — section group label
- `::part(item)` — individual notification item
- `::part(item-unread)` — the unread dot indicator
- `::part(item-dismiss)` — the per-item dismiss button
- `::part(empty)` — the empty state container
- `::part(footer)` — the footer area

**Custom properties:**
- `--mj-nc-width` — panel width (default: `22rem`)
- `--mj-nc-max-height` — panel max-height (default: `80vh`)
- `--mj-nc-item-padding` — notification item padding (default: `var(--mj-space-4)`)
- `--mj-nc-unread-color` — unread indicator color (default: `var(--mj-color-primary)`)
- `--mj-nc-bg` — panel background (default: `var(--mj-color-surface)`)

## 10. States

- **Empty:** No items; empty state shown.
- **Loading:** `loading=true`; skeleton items rendered; list items are `aria-hidden`.
- **All read:** `unreadCount === 0`; "Mark all read" button disabled.
- **Has unread:** `unreadCount > 0`; header badge shows count.
- **Item unread:** Item's `read === false`; unread dot shown; item has stronger visual weight.
- **Item read:** Item's `read === true`; normal visual weight; dot hidden.
- **Item focused:** `:focus-visible` on item; keyboard navigation cue.
- **Item hovered:** Dismiss button revealed on item.

## 11. Behavior & interactions

**Population:** Callers set `items` property directly or append `<mj-notification-item>` children (which are projected into the list and auto-parsed into the `items` array on upgrade).

**Reading:** When a notification item is clicked (or Enter pressed while focused), `mj-notification-select` fires and the item is automatically marked `read` unless the event handler sets `item.read` manually before the component settles. If the item has an `href`, navigation is the default action.

**Mark all read:** Activating the header action sets `read = true` on all items, fires `mj-notification-mark-all-read`, and updates `unreadCount` to 0.

**Dismiss:** The per-item dismiss button fires `mj-notification-dismiss`. If not canceled, the item is removed from `items` with an exit animation.

**Clear all:** Fires `mj-notification-clear-all`. If not canceled, all items are removed.

**Grouping by date:** Items are sorted descending by `timestamp` and grouped into sections: "Today", "Yesterday", and older date labels (locale-formatted). `group-by="category"` groups by `item.category` string.

**Virtualization:** When `items.length > 50`, the list virtualizes using the Section 6 collection utility to keep render performance stable.

**Load more:** When a footer "Load more" control is present (via footer slot or a built-in `load-more` attribute), activating it fires `mj-notification-load-more` with the current `offset`.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Tab` | Moves focus into the panel; first stop is the header action area |
| `ArrowDown` | Moves focus to the next notification item |
| `ArrowUp` | Moves focus to the previous notification item |
| `Enter` or `Space` on item | Activates the item (marks read, fires `mj-notification-select`) |
| `Delete` or `Backspace` on item | Dismisses the focused item |
| `Home` | Moves focus to the first item |
| `End` | Moves focus to the last item |
| `Tab` on item | Moves focus to the item's dismiss button or next interactive element |

## 13. Accessibility

- **Role:** The panel is a `role="region"` with `aria-label` from the `label` attribute. The list of items is a `<ul>` with `role="list"`.
- **Unread count:** The header badge is a `<span>` with `aria-label="N unread notifications"` (not just the number).
- **Item role:** Each item is `role="listitem"` with full title, truncated body, and relative timestamp composed into the accessible name via `aria-label` or `aria-labelledby` + `aria-describedby`.
- **Unread state:** Items with `read === false` have `aria-label` including "Unread: " prefix so AT announces state.
- **Dismiss button:** Each item's dismiss button has `aria-label="Dismiss: [item title]"`.
- **Live region:** When new items are added dynamically (real-time push), a separate `aria-live="polite"` region announces the count change: "3 new notifications".
- **Focus management:** When an item is dismissed, focus moves to the next item; if the last item, focus moves to the previous.
- **Loading state:** Skeleton items are `aria-hidden="true"`; an `aria-live` status region announces "Loading notifications".
- **Keyboard navigation:** Arrow-key navigation among items uses roving tabindex.

## 14. Form participation

N/A.

## 15. Internationalization & RTL

- Built-in strings: `label`, `empty-message`, group-header labels ("Today", "Yesterday"), "Mark all read", "Clear all", "Load more" — all overridable via attributes or a localization hook.
- Date group labels use `Intl.DateTimeFormat` with the document locale.
- RTL: layout mirrors; dismiss button switches sides; unread dot switches to opposite side.

## 16. Progressive enhancement / SSR

Server renders the notification list as an `<ol>` of `<li>` items with timestamp and title. Without JS, the list is readable. On upgrade, the component adds grouping, unread state, dismiss controls, keyboard navigation, and live-region updates.

## 17. Dependencies

- **Section 6:** Design-token stylesheet, Collection/virtualization utility, Live-region service.
- **`<mj-badge>`** — unread count badge in the header.
- **`<mj-button>`** — dismiss, "Mark all read", "Clear all", "Load more" buttons.
- **`<mj-avatar>`** — per-item avatar image (optional).
- **`<mj-empty-state>`** — empty state illustration and message.

## 18. Edge cases & error handling

- **`max-items` exceeded:** The oldest `read` items are evicted first; if all items are unread, oldest items are evicted regardless, with a console warning.
- **Items with identical `id`:** Duplicate IDs log an error; the first instance is kept.
- **Very long title or body:** Title truncates to one line with `text-overflow: ellipsis`; body truncates to two lines. Full text is in the DOM for AT.
- **No timestamp:** Item is placed at the end of the list (no grouping header).
- **Rapid push of new items:** Items are batched into a single DOM update per animation frame to avoid thrashing.
- **Item `href` is invalid:** Navigation fails silently; the `mj-notification-select` event still fires.

## 19. Acceptance criteria

- [ ] Items render with correct title, body, timestamp, and read/unread state.
- [ ] `group-by="date"` correctly groups items with locale-formatted headers.
- [ ] Activating an item marks it read and fires `mj-notification-select`.
- [ ] Dismissing an item removes it with exit animation; fires `mj-notification-dismiss`.
- [ ] "Mark all read" sets all items to `read=true` and fires `mj-notification-mark-all-read`.
- [ ] "Clear all" removes all items (if not canceled) and fires `mj-notification-clear-all`.
- [ ] Unread count badge reflects `unreadCount` correctly.
- [ ] Arrow-key navigation moves focus among items via roving tabindex.
- [ ] Delete/Backspace dismisses focused item; focus moves to adjacent item.
- [ ] Live region announces new items added dynamically.
- [ ] Virtualization keeps render performance stable at > 50 items.
- [ ] Loading skeleton is `aria-hidden`; loading status announced via live region.
- [ ] RTL layout mirrors correctly.
- [ ] axe-core reports zero violations.

## 20. Open questions

- Should `<mj-notification-center>` implement its own data-source adapter interface to support server-side pagination, or is the `mj-notification-load-more` event pattern sufficient?
- Should items support action buttons inline (e.g., "Approve" / "Reject") as a structured field in `NotificationItem`, or only via the `item-icon` slot?
- Should "Mark all read" operate on all items or only the currently visible page when paginated?
