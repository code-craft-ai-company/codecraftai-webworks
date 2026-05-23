# Command Palette Spec

- **Tag:** `<mj-command-palette>`
- **Class / file:** `MjCommandPalette` / `mjcommandpalette.js`
- **Category:** Dialogs, overlays & popups
- **Primary or Variant:** Primary
- **Synonyms covered:** Command palette, Command menu, Command launcher, Quick open
- **Phase:** P2
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-command-palette>` is a keyboard-first, searchable command launcher. It combines a modal dialog with a Combobox-style fuzzy-search input over a flat or grouped list of application commands. It is triggered by a global keyboard shortcut, shows recently used commands, and supports grouped result sets with keyboard navigation.

## 2. When to use / when not to use

Use to provide a power-user shortcut interface giving fast access to any application action without requiring pointer navigation through menus. Use when the application has more than ~15 distinct commands spread across multiple menus. Do not use as the sole entry point for an action — all commands must also be reachable through the standard UI. Do not use as a data search interface (use a Search input or Combobox).

## 3. Anatomy

- **`<mj-dialog>` root** — modal container; provides focus trap, backdrop, Esc handling, and `role="dialog"`.
- **Search input** — prominently placed text field at the top for filtering commands.
- **Results list** — `<ul role="listbox">` of filtered command items.
- **Group headers** — non-interactive section labels within the results.
- **Command item** — each result row with icon, label, optional keyboard shortcut hint, and category.
- **Empty state** — "No matching commands" when the query produces no results.
- **Recent commands section** — shown when the query is empty; lists the most recently used commands.
- **Footer bar** — optional hint legend (ArrowUp/Down to navigate, Enter to select, Esc to dismiss).

## 4. Variants & modes

| Variant | `variant` value | Notes |
|---------|----------------|-------|
| Command launcher (default) | `commands` | Searches and executes application commands |
| Navigation mode | `navigation` | Results are page/route links; Enter navigates |
| Mixed | `mixed` | Commands and navigation links in separate groups |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `open` | boolean | `false` | Yes | Opens/closes the command palette |
| `variant` | `commands` \| `navigation` \| `mixed` | `commands` | Yes | Search result type |
| `placeholder` | string | `"Type a command…"` | Yes | Input placeholder text |
| `max-results` | number | `20` | Yes | Maximum number of items shown in the results list |
| `max-recent` | number | `5` | Yes | Maximum number of recent commands shown when query is empty |
| `debounce` | number | `120` | Yes | Milliseconds to debounce the search query before filtering |
| `global-shortcut` | string | `"Meta+k,Ctrl+k"` | Yes | Comma-separated key combos that open the palette; format: `Modifier+Key` |
| `label` | string | `"Command palette"` | Yes | `aria-label` for the dialog |
| `empty-message` | string | `"No matching commands"` | Yes | Text shown when no results match |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `commands` | `CommandDescriptor[]` | Full list of available commands; `CommandDescriptor` has `{ id, label, icon?, shortcut?, group?, keywords?, action, href?, disabled? }` |
| `query` | `string` | Current search query |
| `results` | `CommandDescriptor[]` | Currently displayed (filtered) commands |
| `recentIds` | `string[]` | Ordered IDs of recently executed commands; persisted to `localStorage` |
| `activeItem` | `CommandDescriptor \| null` | The currently highlighted result item |

## 7. Slots

| Slot | Description |
|------|-------------|
| `input-prefix` | Icon or content before the search input (default: search icon) |
| `empty` | Custom empty state content |
| `footer` | Custom footer content replacing the built-in hint legend |
| `item-prefix` | Per-item slot for custom icon rendering |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-command-palette-open` | `{}` | Yes | No | Fired after the palette opens |
| `mj-command-palette-close` | `{ reason: 'escape' \| 'select' \| 'backdrop' \| 'api' }` | Yes | No | Fired after the palette closes |
| `mj-command-palette-query` | `{ query: string }` | Yes | No | Fired when the search query changes |
| `mj-command-palette-select` | `{ command: CommandDescriptor }` | Yes | Yes | Fired when a command is selected; cancelable to prevent default execution |
| `mj-command-palette-results` | `{ results: CommandDescriptor[], query: string }` | Yes | No | Fired after the filtered results list updates |

## 9. CSS parts & custom properties

**Parts:**
- `::part(dialog)` — the underlying `<mj-dialog>` element
- `::part(input-wrapper)` — the search input container row
- `::part(input)` — the search `<input>` element
- `::part(results)` — the `<ul role="listbox">` results container
- `::part(group-header)` — result group label
- `::part(item)` — individual command result `<li>` element
- `::part(item-icon)` — item icon container
- `::part(item-label)` — item label text
- `::part(item-shortcut)` — keyboard shortcut hint text
- `::part(empty)` — the empty state container
- `::part(footer)` — the hint legend bar

**Custom properties:**
- `--mj-cp-width` — palette dialog width (default: `38rem`)
- `--mj-cp-max-height` — results list max-height (default: `60vh`)
- `--mj-cp-input-height` — search input row height (default: `3.5rem`)
- `--mj-cp-item-height` — each result row height (default: `2.5rem`)
- `--mj-cp-bg` — palette background (default: `var(--mj-color-surface)`)
- `--mj-cp-radius` — border radius (default: `var(--mj-radius-xl)`)
- `--mj-cp-shadow` — box shadow (default: `var(--mj-elevation-5)`)
- `--mj-cp-highlight-bg` — active/hovered item background (default: `var(--mj-color-primary-subtle)`)

## 10. States

- **Closed:** Dialog hidden; global shortcut listener active.
- **Open — empty query:** Recent commands shown; search input focused.
- **Open — query active:** Filtered results shown; active item highlighted.
- **Open — no results:** Empty state shown.
- **Open — loading** (async source): Spinner/skeleton shown in results while filtering.
- **Item active (focused):** Highlighted via CSS and `aria-selected="true"`.
- **Item disabled:** `aria-disabled="true"` on the item; not navigable.
- **Reduced motion:** No open/close animation.

## 11. Behavior & interactions

**Global shortcut:** On `connectedCallback`, the component registers a `keydown` listener on `window` for the combos in `global-shortcut`. Matching the shortcut fires `mj-command-palette-open` (indirectly via setting `open=true`). The shortcut is unregistered on `disconnectedCallback`.

**Opening:** `<mj-dialog>` opens modally. Focus moves to the search input immediately (not the dialog root). If `query` was previously set, it is cleared.

**Filtering:** As the user types, the component debounces input by `debounce` ms then runs fuzzy-match filtering over `commands`. Matching scores on: exact label prefix > keyword match > substring > character-scatter. Results are ranked by score, then recency. `mj-command-palette-query` and `mj-command-palette-results` fire after each filter pass.

**Empty query:** When query is empty, `recentIds` are used to build a "Recent" section (up to `max-recent` items). All other groups are hidden.

**Async results:** If a caller provides an async `filterFn` property, the component calls it with the query and awaits the result, showing a loading state in the interim.

**Item selection:** Enter on the active item, or clicking an item, fires `mj-command-palette-select`. If not canceled, the command's `action()` function is called (or `href` is navigated). The command ID is prepended to `recentIds` (deduplicated, capped at `max-recent`), persisted to `localStorage` under a namespaced key.

**Closing:** Esc closes the palette. Focus returns to the element that was focused when the palette opened.

**Focus management:** `<mj-dialog>` manages the focus trap. The search input receives focus on open. Arrow-key navigation moves the active item, not DOM focus (the input retains focus; `aria-activedescendant` pattern).

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Meta+K` or `Ctrl+K` (configurable) | Opens the command palette from anywhere |
| `ArrowDown` | Moves the active result item down (wraps to first) |
| `ArrowUp` | Moves the active result item up (wraps to last) |
| `Enter` | Selects and executes the active command |
| `Escape` | Closes the palette; focus returns to previous element |
| `Tab` | Moves focus from input to footer actions (if any); does not navigate result items |
| `PageDown` | Moves active item down by 5 rows |
| `PageUp` | Moves active item up by 5 rows |

## 13. Accessibility

- **Roles:** `<mj-dialog>` provides `role="dialog"` and `aria-modal="true"`. The search input has `role="combobox"`, `aria-autocomplete="list"`, `aria-controls="[results-id]"`, and `aria-activedescendant="[active-item-id]"`. The results list has `role="listbox"`. Each item has `role="option"` and `aria-selected="true/false"`.
- **`aria-label`** on the dialog from the `label` attribute.
- **Live region:** A `aria-live="polite"` status region announces result counts: "5 commands found" and "No matching commands" after each filter.
- **Keyboard shortcut hints:** Item shortcut text is wrapped in `<kbd>` elements for semantic meaning.
- **Group headers:** `role="group"` with `aria-label` on each group `<li>`, or a visually-only `role="presentation"` heading — choose the `role="group"` approach for AT discoverability.
- **Background inert:** `<mj-dialog>` (modal) applies `inert` to background content.
- **Focus:** Input retains focus throughout result navigation; `aria-activedescendant` tracks the active item so AT announces each item as the user arrows through.
- **Empty state:** Announced via the `aria-live` status region; not via the listbox directly.

## 14. Form participation

N/A. The palette executes commands, it does not submit form data.

## 15. Internationalization & RTL

- `placeholder`, `label`, `empty-message` are overridable.
- Group heading labels ("Recent", "Actions", "Navigation") are overridable via `group-label-*` attributes or a localization hook.
- Footer hint text is overridable via the `footer` slot.
- RTL: The input icon and item icons switch sides; item layout mirrors.
- The fuzzy-match algorithm treats all strings as Unicode; no ASCII-only assumptions.

## 16. Progressive enhancement / SSR

Without JS, the global shortcut does not register and the palette is not available. Application menus and navigation must provide full access to all commands. On upgrade, the component registers the shortcut and provides the palette as an enhancement. The server may render the `<mj-command-palette>` element silently in the page; it has no visible rendering when closed.

## 17. Dependencies

- **Section 6:** Focus utilities (focus trap via `<mj-dialog>`), Design-token stylesheet, Live-region service.
- **`<mj-dialog>`** — modal container, focus trap, Esc handling.
- **`<mj-overlay>`** — transitively via `<mj-dialog>`.

## 18. Edge cases & error handling

- **No commands registered:** Opens with empty query showing an empty state immediately.
- **`localStorage` unavailable** (private browsing, quota exceeded): `recentIds` falls back to an in-memory array; silent catch; no error shown to user.
- **Async `filterFn` throws:** Error caught; empty state shown with a generic "Search unavailable" message; error logged to console.
- **Very long command labels:** Text truncates with ellipsis; full label in `title` attribute for native tooltip.
- **Global shortcut conflicts with browser shortcut:** `Ctrl+K` is reserved by browsers for focus on address bar; the component's handler runs after `preventDefault()` but browsers may still intercept. Document this limitation; allow `global-shortcut` to be customized.
- **Palette opened while another modal is open:** `<mj-dialog>` stacking handles z-index; focus trap stacks correctly.
- **`max-results` set to 0:** No results shown; warn in console.

## 19. Acceptance criteria

- [ ] Global shortcut (default Ctrl+K / Meta+K) opens the palette.
- [ ] Focus moves to the search input immediately on open.
- [ ] Typing filters commands; results update after debounce.
- [ ] `aria-activedescendant` tracks the highlighted item as ArrowUp/Down navigate.
- [ ] Each result item has `role="option"` and correct `aria-selected`.
- [ ] Enter selects the active command; `mj-command-palette-select` fires.
- [ ] Command `action()` is called unless the event is canceled.
- [ ] Recently used commands appear in the "Recent" section when query is empty.
- [ ] Recent IDs persist to `localStorage` and survive page reload.
- [ ] Esc closes the palette; focus returns to the previously focused element.
- [ ] Background content is `inert` while palette is open.
- [ ] Live region announces result count after each filter.
- [ ] Empty state shown and announced when no results match.
- [ ] `global-shortcut` listener is removed on `disconnectedCallback`.
- [ ] axe-core reports zero violations in open state.

## 20. Open questions

- Should the component ship a built-in fuzzy-match algorithm or require the caller to provide a `filterFn`? A built-in default with an override option seems correct.
- Should `recentIds` be namespaced per page/app to avoid collisions across multiple apps sharing the same origin?
- Should the palette support multi-step commands (e.g., "Move to folder → [folder picker step]")?
