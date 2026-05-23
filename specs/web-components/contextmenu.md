# Context Menu Spec

- **Tag:** `<mj-context-menu>`
- **Class / file:** `MjContextMenu` / `mjcontextmenu.js`
- **Category:** Dialogs, overlays & popups
- **Primary or Variant:** Primary
- **Synonyms covered:** Context menu, Right-click menu, Contextual actions menu
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-context-menu>` is a pointer- or keyboard-invoked actions menu that appears at the cursor position or adjacent to the focused element. It follows the WAI-ARIA `menu` / `menuitem` pattern, opens on right-click or the ContextMenu key, and is positioned by the Section 6 overlay engine. It supports grouped items, separators, submenus, checkable items, and disabled items.

## 2. When to use / when not to use

Use for contextual, target-specific actions that apply to a particular element (file, row, canvas object). Use when right-click or ContextMenu-key invocation is appropriate for the interaction context. Do not use as a primary navigation mechanism (use a `<nav>` or Sidebar). Do not use for a small, fixed set of toggle options (use a Popover or Segmented control). Context menus should not be the only way to access critical actions — always pair with visible alternatives.

## 3. Anatomy

- **Target zone** — the slotted element that listens for `contextmenu` and ContextMenu-key events.
- **Menu panel** — positioned `<ul role="menu">` appearing at the event coordinates.
- **Menu item** — `<li role="menuitem">` for standard actions.
- **Checkbox menu item** — `<li role="menuitemcheckbox">` for toggleable states.
- **Radio menu item** — `<li role="menuitemradio">` for mutually exclusive choices within a group.
- **Submenu** — nested `<mj-context-menu>` or `<ul role="menu">` triggered by a menuitem with `aria-haspopup`.
- **Separator** — `<li role="separator">` for visual grouping.
- **Group label** — optional non-interactive `<li role="presentation">` heading.

## 4. Variants & modes

| Variant | `variant` value | Notes |
|---------|----------------|-------|
| Standard (default) | `menu` | General-purpose action list |
| Checkbox group | `checkbox-group` | All items are `menuitemcheckbox` |
| Radio group | `radio-group` | Items within a group are `menuitemradio` |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `open` | boolean | `false` | Yes | Controls open/closed state |
| `variant` | `menu` \| `checkbox-group` \| `radio-group` | `menu` | Yes | Default item type for all items |
| `target-id` | string | `""` | Yes | ID of an external element to attach contextmenu events to; defaults to the default slot content |
| `label` | string | `"Actions"` | Yes | `aria-label` for the menu element |
| `placement` | `auto` \| `top` \| `bottom` \| `start` \| `end` | `auto` | Yes | Preferred popup placement; `auto` uses cursor position |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `items` | `MenuItemDescriptor[]` | Programmatic item definition; `MenuItemDescriptor` has `{ id, label, icon?, disabled?, checked?, type?, group?, submenu? }` |
| `openCoords` | `{ x: number, y: number } \| null` | Coordinates at which the menu was opened (pointer-based) |
| `targetEl` | `HTMLElement \| null` | The resolved target element receiving contextmenu events |

## 7. Slots

| Slot | Description |
|------|-------------|
| `(default)` | The target element that the context menu attaches to |
| `items` | Static `<mj-menu-item>` children declaring the menu structure |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-context-menu-open` | `{ x: number, y: number, targetEl: HTMLElement }` | Yes | No | Fired after the menu opens |
| `mj-context-menu-close` | `{ reason: 'escape' \| 'item-select' \| 'light-dismiss' \| 'api' }` | Yes | No | Fired after the menu closes |
| `mj-context-menu-select` | `{ item: MenuItemDescriptor, checked?: boolean }` | Yes | No | Fired when a menu item is activated |
| `mj-context-menu-before-open` | `{ x: number, y: number }` | Yes | Yes | Fired before opening; cancelable to suppress the menu |

## 9. CSS parts & custom properties

**Parts:**
- `::part(menu)` — the `<ul role="menu">` container
- `::part(item)` — individual `<li>` menu items
- `::part(separator)` — separator items
- `::part(group-label)` — group heading labels
- `::part(submenu-arrow)` — the indicator on items with submenus

**Custom properties:**
- `--mj-context-menu-width` — menu min-width (default: `12rem`)
- `--mj-context-menu-padding` — menu vertical padding (default: `var(--mj-space-1)`)
- `--mj-context-menu-item-height` — item row height (default: `2.25rem`)
- `--mj-context-menu-radius` — border radius (default: `var(--mj-radius-md)`)
- `--mj-context-menu-shadow` — box shadow (default: `var(--mj-elevation-3)`)
- `--mj-context-menu-bg` — background (default: `var(--mj-color-surface)`)
- `--mj-context-menu-z-index` — z-index (default: `var(--mj-z-menu)`)

## 10. States

- **Closed:** Menu panel not rendered; `open` absent.
- **Open:** Menu visible at computed position; focus inside the menu.
- **Item focused:** Focused `menuitem` has `aria-selected`-style highlight (not aria-selected — menus use `aria-activedescendant` or roving tabindex).
- **Item disabled:** `menuitem` has `aria-disabled="true"`; not activatable but still navigable.
- **Item checked:** `menuitemcheckbox` / `menuitemradio` has `aria-checked="true"`.
- **Submenu open:** Parent item has `aria-expanded="true"`; child menu is visible.

## 11. Behavior & interactions

**Opening (pointer):** A right-click (`contextmenu` event) on the target zone fires `mj-context-menu-before-open`. If not canceled, `open=true` is set and the menu is positioned at `{ x: event.clientX, y: event.clientY }`. The browser's native context menu is suppressed via `preventDefault()`.

**Opening (keyboard):** The ContextMenu key or Shift+F10 while the target has focus fires `mj-context-menu-before-open` and opens the menu adjacent to the focused element (not at cursor position) using the positioning engine with `placement` attribute.

**Positioning:** The Section 6 overlay engine places the menu at the pointer coordinates or adjacent to the target. Viewport collision causes flip and shift to keep the menu fully visible.

**Focus on open:** Focus moves to the first non-disabled menu item.

**Item activation:** Pressing Enter or Space, or clicking a `menuitem`, fires `mj-context-menu-select` and closes the menu (unless the item opens a submenu or is a checkbox/radio item with `close-on-select=false`).

**Checkbox/radio items:** Activation toggles `checked` state (checkbox) or sets the selected radio within its group. `mj-context-menu-select` fires with the updated `checked` value.

**Submenus:** Arrow-right opens a submenu adjacent to the parent item; arrow-left closes it. Mouse hover on a submenu-bearing item opens it after a 150 ms delay.

**Light dismiss:** Clicking outside the menu or losing focus closes the menu with `reason: 'light-dismiss'`.

**Focus restore:** On close, focus returns to the element that was focused when the menu opened (the target element or its nearest focusable ancestor).

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `ArrowDown` | Moves focus to the next menu item (wraps to first) |
| `ArrowUp` | Moves focus to the previous menu item (wraps to last) |
| `ArrowRight` | Opens a submenu (if present); otherwise no-op |
| `ArrowLeft` | Closes the current submenu and returns focus to parent item |
| `Enter` or `Space` | Activates the focused item |
| `Escape` | Closes the menu (or closes submenu and returns to parent) |
| `Home` | Moves focus to the first menu item |
| `End` | Moves focus to the last menu item |
| `Tab` | Closes the menu and moves focus forward in the document |
| Printable character | Type-ahead jumps to the next item beginning with that character |

## 13. Accessibility

- **Roles:** Root menu panel: `role="menu"` with `aria-label` from `label` attribute. Each item: `role="menuitem"`, `role="menuitemcheckbox"`, or `role="menuitemradio"` as appropriate. Separators: `role="separator"`. Group labels: `role="presentation"` (or `role="group"` with `aria-label` for named groups).
- **Focus management:** Focus moves into the menu on open (first non-disabled item). Focus is returned to the triggering element on close.
- **`aria-disabled="true"`** on disabled items; they remain in the DOM and Tab sequence is bypassed (arrow keys still visit them, per APG `menu` pattern, but activation is blocked).
- **`aria-checked`** on `menuitemcheckbox` / `menuitemradio` items reflects current checked state.
- **`aria-haspopup="menu"` and `aria-expanded`** on items with submenus.
- **`aria-activedescendant`** approach or roving tabindex used for item focus; consistent with the Section 6 focus utility.
- **Context menu key:** Shift+F10 must open the menu even when the contextmenu event is otherwise suppressed.
- **No focus trap:** The menu is non-modal; Tab exits the menu and closes it.

## 14. Form participation

N/A. Menu item selections communicate via events, not form values.

## 15. Internationalization & RTL

- `label` attribute (default `"Actions"`) is the localized accessible name.
- RTL: Submenu arrows point left; the submenu opens to the left of the parent item; all placement directions invert.
- Item labels are supplied by the caller and must be localized by the caller.

## 16. Progressive enhancement / SSR

Server renders the target element without a context menu. Without JS, right-click shows the browser's native context menu. On upgrade, the component intercepts the `contextmenu` event and shows the custom menu. A `<noscript>` inline toolbar with the same actions should be provided for critical operations.

## 17. Dependencies

- **Section 6:** Overlay/positioning engine, Focus utilities (focus restore, roving tabindex), Design-token stylesheet.
- **`<mj-menu-item>`** — individual item sub-element (or declarative slot items).

## 18. Edge cases & error handling

- **All items disabled:** Menu opens; focus moves to the first item (still navigable); no item can be activated.
- **Menu opens at viewport edge:** Positioning engine flips/shifts to keep menu fully visible; may override `placement`.
- **Target element removed from DOM while menu is open:** Menu closes; focus falls back to `document.body`.
- **Nested submenus deeper than 3 levels:** Allowed but discouraged; each level is independently positioned.
- **`contextmenu` event on `<input>` or `<textarea>`:** The browser's native spellcheck menu and our custom menu may conflict. The component does not suppress the native menu on text fields unless `suppress-native` attribute is set.
- **Rapid open/close from programmatic calls:** Menu renders synchronously; no queuing issues.

## 19. Acceptance criteria

- [ ] Right-click on target opens menu at pointer coordinates; browser native menu is suppressed.
- [ ] ContextMenu key / Shift+F10 opens menu adjacent to the focused element.
- [ ] `mj-context-menu-before-open` fires and is cancelable.
- [ ] Arrow keys navigate items; wrapping at top/bottom.
- [ ] Enter/Space activates item; menu closes; `mj-context-menu-select` fires.
- [ ] Escape closes the menu; focus returns to the target.
- [ ] Light-dismiss closes menu on outside click.
- [ ] Disabled items have `aria-disabled="true"` and cannot be activated.
- [ ] Checkbox items toggle `aria-checked` on activation.
- [ ] Radio items set `aria-checked` to the selected item in the group.
- [ ] Submenus open on ArrowRight / hover; close on ArrowLeft / Escape.
- [ ] `role="menu"` and `aria-label` are present on the menu panel.
- [ ] Focus moves to the first non-disabled item on open; returns to target on close.
- [ ] RTL layout mirrors submenu arrow and placement.
- [ ] Type-ahead character navigation jumps to matching item.
- [ ] axe-core reports zero violations in open state.

## 20. Open questions

- Should `<mj-context-menu>` share its menu rendering with `<mj-menu>` (navigation menu, 5.4) via a common `<mj-menu-panel>` primitive, or maintain a separate implementation?
- Should there be a `virtual-target` mode where the caller passes coordinates directly (for canvas-based UIs where right-click target is not a DOM element)?
- Should submenus be inline (`variant="submenu"` on a nested `<mj-context-menu>`) or declared via `items` descriptors only?
