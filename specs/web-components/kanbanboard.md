# Kanban Board Spec

- **Tag:** `<mj-kanban>`
- **Class / file:** `MjKanban` / `mjkanban.js`
- **Category:** Tables, lists & structured data
- **Primary or Variant:** Primary
- **Synonyms covered:** Kanban board, Task board, Card board, Swim-lane board
- **Phase:** P2
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-kanban>` renders a multi-column card board for visualizing and managing work
items across workflow states (e.g., To Do → In Progress → Done). Cards are
movable between columns via pointer drag-and-drop and via a full keyboard move
interface. Each column displays a WIP (work-in-progress) limit and current count.
Card moves are announced via live region so screen-reader users receive immediate
feedback. The board is backed by a data adapter for server-side persistence.

## 2. When to use / when not to use
**Use** for workflow management, task tracking, or any UI where items progress
through discrete named stages and the visual column metaphor is meaningful.
**Do not use** for purely tabular data — use `<mj-data-table>`. For time-based
scheduling use `<mj-calendar>`. For hierarchical data use `<mj-tree-grid>`.

## 3. Anatomy
- **Board** — horizontal scroll container holding all columns; `role="application"` with `aria-label`.
- **Column** — named `<section>` with `role="group"` and `aria-label` matching the column label.
- **Column header** — title, item count badge, WIP limit indicator, and optional column actions menu.
- **Column body** — scrollable card list; `role="list"`.
- **Card** — `role="listitem"` containing card content; draggable.
- **Card drag handle** — explicit drag affordance; `role="button"` with `aria-grabbed`.
- **Drop zone** — highlighted insertion indicator shown between cards during drag.
- **Add-card slot** — per-column slot for an "Add card" trigger at the bottom.
- **Announcement region** — `aria-live="assertive"` region for move confirmations.

## 4. Variants & modes
| Variant | `mode` value | Behavior |
|---------|-------------|----------|
| Interactive | `interactive` (default) | Drag-and-drop + keyboard move enabled. |
| Read-only | `readonly` | Cards are visible and focusable but not movable. |

Column layout via `layout`:
- `fixed-width` (default) — all columns share `--mj-kanban-col-width`.
- `fluid` — columns share available width equally.
- `scroll` — board scrolls horizontally; columns maintain fixed width.

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `mode` | `interactive\|readonly` | `interactive` | yes | Enables or disables card moves. |
| `layout` | `fixed-width\|fluid\|scroll` | `scroll` | yes | Column sizing strategy. |
| `col-width` | number | `280` | yes | Column width in px for `fixed-width`/`scroll` layouts. |
| `wip-limits` | boolean | false | yes | Shows WIP limit indicators on columns. |
| `loading` | boolean | false | yes | Shows skeleton columns; `aria-busy="true"`. |
| `max-cols` | number | `0` | yes | Max visible columns before horizontal scroll (0 = unlimited). |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `columns` | `KanbanColumn[]` | `{ id, label, wipLimit?: number, cards: KanbanCard[] }` — full board definition. |
| `dataSource` | `KanbanDataAdapter` | `{ fetchBoard(): Promise<KanbanColumn[]>, moveCard(cardId, toColumnId, toIndex): Promise<void> }` |
| `renderCard` | `(card: KanbanCard) => HTMLElement \| string` | Custom card renderer; used when no `card` slot template is present. |

## 7. Slots
| Slot | Description |
|------|-------------|
| `card` | Template cloned for each card; receives `data-card-id`, `data-col-id` attributes. |
| `column-header-[id]` | Named per-column slot for custom header content. |
| `add-card-[id]` | Named per-column slot for the add-card trigger at the bottom. |
| `empty-[id]` | Named per-column slot for empty-column state. |
| `loading` | Content shown while `loading` is true. |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-card-move-start` | `{ cardId: string, fromColId: string, fromIndex: number }` | true | true | Card drag/keyboard move begins; cancel to prevent. |
| `mj-card-move` | `{ cardId: string, fromColId: string, toColId: string, toIndex: number }` | true | true | Card dropped/placed; cancel to reject move (reverts UI). |
| `mj-card-move-complete` | `{ cardId: string, fromColId: string, toColId: string, toIndex: number }` | true | false | Adapter confirmed the move. |
| `mj-card-move-error` | `{ cardId: string, error: Error }` | true | false | Adapter rejected the move; card reverted. |
| `mj-card-click` | `{ cardId: string, colId: string }` | true | false | Card body clicked/activated (not drag handle). |
| `mj-col-wip-exceeded` | `{ colId: string, count: number, limit: number }` | true | false | Card dropped into a column exceeding its WIP limit. |

## 9. CSS parts & custom properties
**Parts:** `board`, `column`, `column-header`, `column-body`, `column-footer`,
`card`, `card-handle`, `drop-zone`, `wip-indicator`, `add-card`.

| Custom property | Default | Purpose |
|----------------|---------|---------|
| `--mj-kanban-col-width` | `280px` | Column width in fixed/scroll layouts. |
| `--mj-kanban-col-gap` | `12px` | Gap between columns. |
| `--mj-kanban-card-gap` | `8px` | Gap between cards within a column. |
| `--mj-kanban-col-bg` | `token(--mj-color-surface-subtle)` | Column background. |
| `--mj-kanban-card-bg` | `token(--mj-color-surface)` | Card background. |
| `--mj-kanban-card-radius` | `token(--mj-radius-md)` | Card border radius. |
| `--mj-kanban-drop-zone-color` | `token(--mj-color-focus)` | Drop zone indicator color. |
| `--mj-kanban-wip-ok-color` | `token(--mj-color-success)` | WIP count within limit. |
| `--mj-kanban-wip-exceeded-color` | `token(--mj-color-warning)` | WIP count at or over limit. |
| `--mj-kanban-drag-opacity` | `0.5` | Opacity of dragged card ghost. |

## 10. States
- **default** — cards render in columns; no active drag.
- **dragging** — dragged card: `aria-grabbed="true"`; source column body has `aria-dropeffect="move"` on valid drop targets.
- **drag-over** — column or inter-card gap highlighted with drop zone indicator.
- **loading** — `aria-busy="true"`; skeleton columns shown.
- **wip-exceeded** — column header WIP count shown in `--mj-kanban-wip-exceeded-color`.
- **keyboard-move-mode** — card in keyboard move mode shows persistent move controls; board live region updated.
- **readonly** — drag handles hidden; cards not keyboard-movable; `mode="readonly"`.

## 11. Behavior & interactions
**Pointer drag-and-drop:** On `pointerdown` on a card's drag handle, the card
enters dragging state. A ghost element follows the pointer. As the pointer moves
over columns or inter-card gaps, drop zones highlight and the live region
announces "Moving card to {column} column, position {n}." On `pointerup`, the
card is tentatively placed; `mj-card-move` fires. If not canceled, the adapter's
`moveCard` is called. On adapter success, `mj-card-move-complete` fires. On
failure, the card reverts to its origin and `mj-card-move-error` fires.

**Keyboard move mode:** When a card's drag handle has focus, pressing `Space` or
`Enter` enters keyboard move mode. A status bar appears below the column header
showing movement instructions. `ArrowLeft`/`ArrowRight` move the card between
columns; `ArrowUp`/`ArrowDown` adjust position within a column; `Enter` confirms
the move (fires `mj-card-move`); `Escape` cancels and returns the card to its
original position. The announcement region fires on each positional change.

**WIP limits:** When a column's `wipLimit` is set and the card count equals or
exceeds it, the WIP indicator turns to the exceeded color. A drop onto such a column
fires `mj-col-wip-exceeded` but does not block the move (blocking vs. warning is
caller-controlled by canceling `mj-card-move`).

**Touch:** On touch devices, a long-press (300 ms) on the drag handle initiates
drag. A visual elevation change on the card confirms touch-drag start.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` | Moves focus between cards and column controls in DOM order. |
| `Space` or `Enter` on drag handle | Enter keyboard move mode for the focused card. |
| `ArrowLeft / Right` (move mode) | Move card to previous/next column; announce column name and new count. |
| `ArrowUp / Down` (move mode) | Move card up/down within its current column; announce new position. |
| `Enter` (move mode) | Confirm card placement; emit `mj-card-move`. |
| `Escape` (move mode) | Cancel move; return card to original position; announce "Move canceled." |
| `Tab` (move mode) | Blocked — Tab stays within move mode to prevent accidental exit. |
| `Enter` or `Space` on card body | Emit `mj-card-click` (open card detail). |

## 13. Accessibility
- Board root: `role="application"` with `aria-label="Kanban board"` (or from `aria-label` attribute) so AT announces the interactive application mode.
- Columns: `role="group"` inside a `<section>`; `aria-label="{column label} ({count} cards)"`.
- Column card list: `role="list"`.
- Cards: `role="listitem"`; focusable via `tabindex="0"`; `aria-label` derived from card title.
- Drag handle button: `aria-label="Move card: {card title}"`, `aria-pressed="false"` (true in move mode), `aria-grabbed` reflects drag state.
- Drop targets during drag: `aria-dropeffect="move"` on valid columns.
- Announcement region: `role="status"` (`aria-live="assertive"`) announces every positional change during move mode and final placement/cancellation.
- WIP exceeded: column header badge has `aria-label="{count} of {limit} WIP limit — exceeded"`.
- No color-only WIP status — exceeded state also adds a warning icon.

## 14. Form participation
N/A — the board does not contribute a form value.

## 15. Internationalization & RTL
- In RTL, column order is reversed (rightmost column is first); `ArrowLeft` in move mode moves to the next (rightward in DOM) column.
- All UI strings (move mode instructions, announcements, WIP labels) are overridable via attributes or the localization hook.
- Column labels and card titles must be pre-translated by the caller.

## 16. Progressive enhancement / SSR
Server renders each column as a `<section>` with a heading and an `<ul>` of card
summaries. Without JS the board is readable and navigable. On upgrade the
component attaches drag handling, creates the ghost element, and initializes the
announcement region. Column widths and gaps are preserved so upgrade causes no
layout shift.

## 17. Dependencies
- Focus utilities — focus trap during keyboard move mode (§6).
- Live-region/announcement service (§6).
- Data-source adapter interface (§6).
- Design-token stylesheet (§6).
- Base element helper (§6).
- `<mj-badge>` for WIP count indicators.
- `<mj-button>` for drag handle and add-card trigger.

## 18. Edge cases & error handling
- **Adapter `moveCard` rejects** — card reverts to origin; `mj-card-move-error` fires; error toast recommended.
- **Move to same position** — `mj-card-move` fires but adapter call is skipped (no-op detected by comparing origin and destination).
- **Column with zero cards** — `slot="empty-[id]"` shown; dropping a card onto an empty column positions it at index 0.
- **Drag outside board boundaries** — drag canceled; card returns to origin; pointer capture released.
- **Long card titles** — card text truncated with ellipsis; full title in `title` attribute and `aria-label`.
- **Many columns exceeding viewport** — horizontal scroll activated; keyboard column-to-column navigation wraps correctly.

## 19. Acceptance criteria
- [ ] Board renders columns with correct heading, card list, and WIP indicator.
- [ ] Pointer drag-and-drop moves a card; ghost follows pointer; drop zone highlights.
- [ ] `mj-card-move` fires on drop; adapter `moveCard` called; `mj-card-move-complete` on success.
- [ ] Adapter failure reverts card position; `mj-card-move-error` fires.
- [ ] Keyboard move mode: `Space`/`Enter` on handle enters mode; arrow keys reposition; `Enter` confirms; `Escape` cancels.
- [ ] Live region announces every positional change and final outcome.
- [ ] `role="application"` on board; `role="group"` on columns; `role="list"`/`"listitem"` on card lists/cards.
- [ ] `aria-grabbed` and `aria-dropeffect` correctly set during drag.
- [ ] WIP exceeded: color + icon change; `mj-col-wip-exceeded` fires.
- [ ] Empty column shows `slot="empty-[id]"`; card can be dropped into it.
- [ ] axe audit passes with zero violations in default and keyboard-move states.
- [ ] RTL: column order reversed; move mode arrow directions adjusted.

## 20. Open questions
- Should WIP limit violations block the move (cancel `mj-card-move` internally) or remain advisory?
- Should swimlane rows (grouping cards by assignee within each column) be a P2 extension?
- Multi-card drag selection — include or defer beyond P2?
