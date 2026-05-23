# Bulk Action Bar Spec

- **Tag:** `<mj-bulk-action-bar>`
- **Class / file:** `MjBulkActionBar` / `mjbulkactionbar.js`
- **Category:** Tables, lists & structured data
- **Primary or Variant:** Primary
- **Synonyms covered:** Bulk action bar, Row selector, Selection toolbar, Multi-select action bar
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-bulk-action-bar>` is a contextual toolbar that appears when one or more rows
are selected in a `<mj-data-table>`, `<mj-tree-grid>`, or `<mj-virtual-list>`. It
displays the selected item count, a select-all/clear-all control, and a set of
actions that operate on the selection. The count is announced to screen readers
via a live region whenever it changes. It replaces the default toolbar while a
selection is active and dismisses when the selection is cleared.

## 2. When to use / when not to use
**Use** whenever a grid or list allows multi-row selection and needs contextual
batch actions (delete, export, assign, archive). **Do not use** for single-item
actions — place those as row-level action buttons. For global toolbar actions
unrelated to selection use a standard `<mj-toolbar>`. Do not use this component
without a connected grid that provides selection state.

## 3. Anatomy
- **Bar root** — `<div role="toolbar">` fixed or inline at the top of the grid; visually replaces the standard toolbar when selection is active.
- **Select-all checkbox** — tri-state (none/some/all) checkbox; `aria-label="Select all"`.
- **Count badge** — "N selected" label; `aria-live="polite"` region for screen-reader announcements.
- **Action group** — `<div role="group">` containing action buttons supplied via the `actions` slot.
- **Clear button** — "×" or "Clear selection" button; deselects all rows and dismisses the bar.
- **Overflow menu** — appears when action buttons overflow the bar width; uses `<mj-menu>`.

## 4. Variants & modes
| Variant | `position` value | Behavior |
|---------|----------------|----------|
| Inline | `inline` (default) | Bar is part of the normal document flow above the grid. |
| Floating | `floating` | Bar floats at the bottom of the viewport over the grid. |
| Replace-toolbar | `replace-toolbar` | Replaces a sibling `[slot="toolbar"]` when selection is active; toolbar restored on clear. |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `selected-count` | number | `0` | yes | Number of selected rows; drives count label and tri-state checkbox. |
| `total-count` | number | `0` | yes | Total number of rows; used to calculate all-selected state. |
| `position` | `inline\|floating\|replace-toolbar` | `inline` | yes | Bar placement strategy. |
| `visible` | boolean | false | yes | When true the bar is shown; when false it is hidden (set by the host grid). |
| `select-all-label` | string | `"Select all"` | yes | Accessible label for the select-all checkbox. |
| `clear-label` | string | `"Clear selection"` | yes | Accessible label for the clear button. |
| `count-label` | string | `"{n} selected"` | yes | Template string for the count; `{n}` replaced with the count. |
| `disabled` | boolean | false | yes | Disables all action buttons and the select-all checkbox. |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `selectedKeys` | `Set<string>` | The keys of currently selected rows; read-only reflection of the host grid's selection. |
| `actions` | `BulkAction[]` | `{ key: string, label: string, icon?: string, disabled?: boolean, destructive?: boolean }` — action button definitions when not using the `actions` slot. |

## 7. Slots
| Slot | Description |
|------|-------------|
| `actions` | Custom action buttons placed between the count label and the clear button. |
| `count` | Custom count label content; replaces the default `"{n} selected"` text. |
| `leading` | Content before the select-all checkbox (e.g., a custom icon). |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-select-all` | `{ selectAll: boolean }` | true | true | User toggled the select-all checkbox; `selectAll` is true for all, false for none. Cancel to prevent the state change. |
| `mj-clear-selection` | `{}` | true | false | User pressed the Clear selection button. |
| `mj-action` | `{ actionKey: string, selectedKeys: string[] }` | true | false | User pressed one of the action buttons; `selectedKeys` is the array of selected row keys. |
| `mj-overflow-action` | `{ actionKey: string, selectedKeys: string[] }` | true | false | User selected an action from the overflow menu. |

## 9. CSS parts & custom properties
**Parts:** `bar`, `select-all-checkbox`, `count-label`, `action-group`, `action-button`,
`clear-button`, `overflow-button`.

| Custom property | Default | Purpose |
|----------------|---------|---------|
| `--mj-bab-bg` | `token(--mj-color-primary-subtle)` | Bar background when visible. |
| `--mj-bab-height` | `48px` | Bar height. |
| `--mj-bab-border-radius` | `token(--mj-radius-md)` | Bar border radius (floating mode). |
| `--mj-bab-z-index` | `token(--mj-z-sticky)` | Z-index for floating mode. |
| `--mj-bab-count-color` | `token(--mj-color-primary)` | Color of the count text. |
| `--mj-bab-action-gap` | `8px` | Gap between action buttons. |
| `--mj-bab-shadow` | `token(--mj-shadow-md)` | Shadow applied in floating mode. |

## 10. States
- **hidden** — `visible=false`; bar not rendered (or `display:none`); `aria-hidden="true"`.
- **visible-partial** — `selected-count > 0` and `selected-count < total-count`; checkbox `aria-checked="mixed"`.
- **visible-all** — `selected-count === total-count && total-count > 0`; checkbox `aria-checked="true"`.
- **visible-none** — `selected-count === 0`; bar hides automatically.
- **disabled** — all actions and checkbox disabled; `aria-disabled="true"` on each.
- **floating** — bar positioned fixed at bottom of viewport with shadow.
- **overflow-active** — some action buttons hidden into overflow menu.

## 11. Behavior & interactions
**Visibility:** The bar watches the `visible` attribute. When it becomes `true`, the
bar animates in (slide-down for inline, slide-up for floating), focus is optionally
moved to the first action button (configurable via `autofocus-on-show` attribute),
and the live region announces "{n} rows selected." When `selected-count` drops to
zero, `visible` should be set to `false` by the host grid, and the bar fades out;
focus is restored to the previously focused grid cell.

**Select-all tri-state:** The checkbox reflects three states — none (`aria-checked="false"`), some (`aria-checked="mixed"`), all (`aria-checked="true"`). Clicking the
checkbox in `false` or `mixed` state fires `mj-select-all` with `selectAll=true`.
Clicking in `true` state fires `mj-select-all` with `selectAll=false`. The host
grid listens and updates its own selection; `selected-count` is then updated by the
host.

**Count announcement:** Every time `selected-count` changes, the live region
updates. The `count-label` attribute template (`"{n} selected"` by default) is
filled with the current count and placed in the `aria-live="polite"` region. For
large counts (> 1000) the count is formatted via the localization hook.

**Overflow handling:** A `ResizeObserver` on the action group detects when buttons
overflow. Overflow buttons are moved into an `<mj-menu>` triggered by an "More
actions" button. The order of overflow matches the visual order (last buttons
overflow first).

**Floating mode:** The bar is positioned at the bottom of the scroll container
using `position: sticky; bottom: 0` within the grid wrapper, or `position: fixed`
at the viewport bottom. It does not obscure the last row — the grid adds bottom
padding equal to the bar height when floating and visible.

**Action buttons:** Buttons defined in `actions` or `slot="actions"` receive the
current `selectedKeys` when clicked, and `mj-action` fires. Destructive actions
(`destructive: true`) are colored with the error token and placed last in order.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` | Moves focus between select-all checkbox, action buttons, overflow menu button, and clear button. |
| `Space` on select-all checkbox | Toggle select-all / clear-all state; fire `mj-select-all`. |
| `Enter` / `Space` on action button | Fire `mj-action` for that button's key. |
| `Enter` / `Space` on clear button | Clear selection; fire `mj-clear-selection`. |
| `Escape` | Clear selection (equivalent to clear button); dismiss bar. |
| `ArrowLeft / Right` (within toolbar) | Move focus between action buttons (roving tabindex within the action group). |

## 13. Accessibility
- Root: `role="toolbar"` with `aria-label="Bulk actions"` (or from an `aria-label` attribute); `aria-controls` pointing to the associated grid's `id`.
- Select-all checkbox: `role="checkbox"` (or native `<input type="checkbox">`); `aria-checked="true|false|mixed"` (tri-state); `aria-label` from `select-all-label`.
- Count label: wrapped in `aria-live="polite"` region; also `aria-atomic="true"` so the full phrase is re-read on each update.
- Action group: `role="group"` with `aria-label="Actions for selected rows"`.
- Clear button: `aria-label` from `clear-label`; always present when bar is visible.
- Hidden bar: `aria-hidden="true"` and `display:none` so it is entirely removed from the AT tree.
- Destructive actions: labelled with their action name only; not color-only; icon + label required.
- Overflow menu button: `aria-haspopup="menu"`, `aria-label="More actions"`.
- When bar becomes visible: live region immediately announces `"{n} rows selected"`.
- `prefers-reduced-motion`: slide animation disabled; bar appears/disappears instantly.

## 14. Form participation
N/A — action bar is a navigation/command component; it does not submit values.

## 15. Internationalization & RTL
- In RTL, action group order reverses; clear button remains at the trailing end.
- `count-label`, `select-all-label`, `clear-label` attributes accept pre-translated strings.
- The `{n}` placeholder in `count-label` is formatted via `Intl.NumberFormat` for locale-correct grouping separators.
- Live region text uses the same formatted string.

## 16. Progressive enhancement / SSR
Without JS the bar is not rendered (selection requires scripting). The SSR
fallback relies on the host grid's own no-JS fallback (e.g., native checkboxes
with a form submit for batch actions). On upgrade the bar is injected by the host
grid when selection is first activated.

## 17. Dependencies
- `<mj-data-table>` / `<mj-tree-grid>` / `<mj-virtual-list>` — host grids that drive `selected-count` and `selectedKeys`.
- `<mj-menu>` — overflow actions menu.
- `<mj-button>` — action buttons and clear button.
- Live-region/announcement service (§6).
- Focus utilities — roving tabindex within toolbar (§6).
- Overlay/positioning engine (§6) — overflow menu.
- Design-token stylesheet (§6).
- Localization/formatting hook (§6) — count formatting.

## 18. Edge cases & error handling
- **`selected-count` > `total-count`** — impossible but guarded; treated as all-selected and console warning logged.
- **`total-count = 0`** — select-all checkbox disabled; count label shows "0 selected"; bar hides.
- **All actions disabled** — bar remains visible with count and clear button only; action group hidden.
- **Very long action labels** — truncated with ellipsis; full label in `aria-label` and tooltip.
- **Bar in floating mode + sticky table header** — z-index layering must ensure bar is above table header; token `--mj-z-sticky + 1`.
- **`Escape` key conflict with open overflow menu** — `Escape` first closes the menu; second `Escape` clears selection.

## 19. Acceptance criteria
- [ ] Bar hidden (`aria-hidden="true"`, `display:none`) when `visible=false`; shown when `visible=true`.
- [ ] `role="toolbar"` with `aria-controls` pointing to associated grid.
- [ ] Select-all checkbox: tri-state `aria-checked` reflects none/some/all correctly.
- [ ] `mj-select-all` fires with correct `selectAll` boolean on checkbox toggle.
- [ ] Count label in `aria-live="polite"` region; updated every time `selected-count` changes.
- [ ] Count formatted via `Intl.NumberFormat`.
- [ ] `mj-action` fires with `actionKey` and `selectedKeys` array on action button press.
- [ ] Clear button fires `mj-clear-selection`; `Escape` key also clears.
- [ ] `ResizeObserver` moves overflow actions into `<mj-menu>` when bar overflows.
- [ ] Roving tabindex within action group; `ArrowLeft`/`Right` move focus.
- [ ] Floating mode: grid padding bottom = bar height; bar does not obscure content.
- [ ] Destructive action buttons styled with error token + icon.
- [ ] axe audit passes with zero violations in visible and hidden states.
- [ ] RTL: action group order reversed.
- [ ] `prefers-reduced-motion`: no slide animation.

## 20. Open questions
- Should the bar support a "Select across all pages" affordance when `dataSource` is paged and only the current page is selected?
- Should destructive actions always require a confirmation dialog, or is that the caller's responsibility?
- Should the floating mode bar use `position:sticky` within the grid scroll container or `position:fixed` at the viewport?
