# Menu Spec

- **Tag:** `<mj-menu>`
- **Class / file:** `MjMenu` / `mjmenu.js`
- **Category:** Navigation components
- **Primary or Variant:** Primary
- **Synonyms covered:** Menu, Dropdown menu, Flyout menu, Mega menu, Context menu, Nested submenu, Overflow menu
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-menu>` is a popup menu primitive implementing the WAI-ARIA `menu`/`menuitem`
pattern. It supports dropdown (anchored to a trigger button), flyout (anchored to
a parent menuitem), mega (multi-column panel), and nested submenus. It is composed
by `<mj-menu-button>`, `<mj-split-button>`, and `<mj-app-bar>` and used directly
for context menus and overflow menus.

## 2. When to use / when not to use
**Use** when providing a list of actions or navigation choices in a popup. **Do
not use** for selection from a list of values — use `<mj-select>` or
`<mj-listbox>`. **Do not use** for navigation tabs — use `<mj-tabs>`. **Do not
use** for inline visible lists of options — use `<mj-listbox>`.

## 3. Anatomy
- **Menu popup** (`::part(menu)`) — `<div role="menu" aria-label>` positioned
  by the overlay engine.
- **Menu item** (`::part(item)`) — `<div role="menuitem">` or `role="menuitemcheckbox"` / `role="menuitemradio"`.
- **Item icon** (`::part(item-icon)`) — leading decorative icon; `aria-hidden`.
- **Item label** (`::part(item-label)`) — text label.
- **Item description** (`::part(item-description)`) — optional secondary text.
- **Item shortcut** (`::part(item-shortcut)`) — keyboard shortcut hint; `aria-hidden`.
- **Item arrow** (`::part(item-arrow)`) — submenu indicator; `aria-hidden`.
- **Separator** (`::part(separator)`) — `<div role="separator">`; groups items.
- **Group heading** (`::part(group-heading)`) — `<div role="presentation">` label for an item group.
- **Submenu** — nested `<mj-menu>` anchored to its parent menuitem trigger.
- **Mega panel** (`::part(mega-panel)`) — multi-column layout container used when `variant="mega"`.
- **Backdrop** (`::part(backdrop)`) — optional dimming element for modal-like menus.

## 4. Variants & modes
| Variant | `variant` value | Behavior |
|---------|----------------|----------|
| Dropdown | `dropdown` | Anchored below/above a trigger button; single column |
| Flyout | `flyout` | Opens to the side of a parent `menuitem`; used for nested submenus |
| Mega | `mega` | Wide multi-column panel; columns defined by slotted `<mj-menu-column>` elements |
| Context | `context` | Positioned at pointer coordinates; opened on right-click or context-menu key |

| Activation | `hover-intent` | Behavior |
|-----------|---------------|----------|
| Click | `false` (default) | Opens on trigger click/Enter/Space |
| Hover-intent | `true` | Opens on pointer hover after `hover-delay` ms |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `open` | boolean | `false` | Yes | Whether the menu is visible |
| `variant` | string | `"dropdown"` | Yes | Menu type: `dropdown` \| `flyout` \| `mega` \| `context` |
| `anchor` | string | `""` | Yes | CSS selector or `id` of the trigger element the menu is anchored to |
| `placement` | string | `"bottom-start"` | Yes | Preferred popup placement; overlay engine handles flip/shift |
| `hover-intent` | boolean | `false` | Yes | Opens on hover with intent delay |
| `hover-delay` | number | `200` | Yes | Milliseconds of hover before opening (when `hover-intent` is true) |
| `label` | string | `""` | Yes | `aria-label` for `role="menu"`; required when the trigger's accessible name is insufficient |
| `close-on-select` | boolean | `true` | Yes | Whether selecting a `menuitem` closes the menu |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `items` | `Element[]` | Ordered list of all enabled `<mj-menu-item>` elements |
| `activeItem` | `Element \| null` | Currently keyboard-focused/active menuitem |
| `triggerElement` | `Element \| null` | The element the menu is anchored to (resolved from `anchor` attribute or set directly) |

## 7. Slots
| Slot | Description |
|------|-------------|
| _(default)_ | `<mj-menu-item>`, `<mj-menu-separator>`, and `<mj-menu-group>` elements |
| `column` | `<mj-menu-column>` elements for `variant="mega"` multi-column layout |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-menu-open` | `{ trigger: Element \| null }` | Yes | Yes | Fires before the menu opens; cancel to prevent |
| `mj-menu-close` | `{ reason: "select" \| "escape" \| "blur" \| "external" }` | Yes | Yes | Fires before the menu closes; cancel to prevent |
| `mj-menu-select` | `{ item: Element, value: string, checked: boolean \| null }` | Yes | Yes | Fires when a menuitem is selected; cancel to prevent close when `close-on-select` is true |
| `mj-menu-item-focus` | `{ item: Element }` | Yes | No | Fires when keyboard focus moves to a menuitem |

## 9. CSS parts & custom properties
**Parts**
- `::part(menu)` — the popup `<div role="menu">`
- `::part(item)` — each `<div role="menuitem">` wrapper
- `::part(item-icon)` — leading icon
- `::part(item-label)` — item text
- `::part(item-description)` — secondary description text
- `::part(item-shortcut)` — keyboard shortcut hint
- `::part(item-arrow)` — submenu chevron icon
- `::part(separator)` — `role="separator"` divider
- `::part(group-heading)` — group label text
- `::part(mega-panel)` — mega menu column container

**Custom properties**
| Property | Default | Description |
|----------|---------|-------------|
| `--mj-menu-bg` | `var(--mj-color-surface-overlay)` | Menu popup background |
| `--mj-menu-shadow` | `var(--mj-elevation-4)` | Popup box shadow |
| `--mj-menu-radius` | `var(--mj-radius-md)` | Popup border radius |
| `--mj-menu-min-width` | `160px` | Minimum popup width |
| `--mj-menu-max-height` | `360px` | Maximum popup height before scroll |
| `--mj-menu-item-height` | `40px` | Height of each menu item |
| `--mj-menu-item-padding` | `0 var(--mj-spacing-4)` | Horizontal padding of items |
| `--mj-menu-item-focus-bg` | `var(--mj-color-surface-hover)` | Background of the focused/hovered item |
| `--mj-menu-z-index` | `var(--mj-z-index-menu)` | Stack order |
| `--mj-menu-mega-columns` | `3` | Number of columns in mega variant |

## 10. States
- **closed** — `open` is `false`; popup is not in the DOM (or `display: none`).
- **open** — popup is visible; first item (or previously focused item) receives `aria-activedescendant` focus.
- **item-focused** — the keyboard-active item is highlighted; `aria-activedescendant` on `role="menu"` points to it.
- **item-disabled** — `aria-disabled="true"` on a menuitem; skipped in keyboard navigation.
- **item-checked** — `aria-checked="true"` on `menuitemcheckbox` or `menuitemradio`.
- **submenu-open** — the parent menuitem has `aria-expanded="true"`; submenu popup is visible.

## 11. Behavior & interactions
- The menu uses `aria-activedescendant` on the `role="menu"` element to track
  keyboard focus; the popup itself receives DOM focus, not individual items.
- On open, focus moves to the menu popup element; the first enabled item is set
  as `aria-activedescendant`.
- On close, focus returns to the trigger element.
- Positioning is delegated to the Section 6 overlay engine with the `placement`
  attribute; the engine flips the menu to the opposite side if it would overflow
  the viewport.
- When `hover-intent` is true, a `hover-delay` timer is started on `pointerenter`
  of the trigger; if the pointer leaves before the timer fires, the menu does not
  open. This avoids accidental hover-opens.
- Nested submenus: the parent `<mj-menu-item>` has `aria-haspopup="menu"` and
  `aria-expanded`; the child `<mj-menu variant="flyout">` is anchored to it.
  Arrow Right (LTR) or pointer hover opens the submenu; Arrow Left or Escape
  closes it and returns focus to the parent item.
- Light-dismiss: clicking outside the open menu or its trigger closes the menu
  (dispatches `mj-menu-close` with `reason: "blur"`).
- `close-on-select`: if true (default), selecting a menuitem closes the menu.
  `menuitemcheckbox` and `menuitemradio` items do not close on select by default
  (they toggle state); override with `close-on-select="true"` on those items.
- Mega menu columns are `display: grid` with `--mj-menu-mega-columns` tracks;
  each column is a `<mj-menu-column>` with its own heading and item list.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Enter` / `Space` (on trigger) | Opens the menu; focus moves to menu |
| `Arrow Down` | Moves focus to next enabled item (wraps) |
| `Arrow Up` | Moves focus to previous enabled item (wraps) |
| `Home` | Moves focus to first enabled item |
| `End` | Moves focus to last enabled item |
| `Enter` (on item) | Activates the item; fires `mj-menu-select`; closes if `close-on-select` |
| `Space` (on item) | Toggles `menuitemcheckbox`; selects `menuitemradio`; same as Enter for `menuitem` |
| `Arrow Right` (LTR) | Opens a submenu anchored to the current item |
| `Arrow Left` (LTR) | Closes the current submenu; returns focus to parent item |
| `Escape` | Closes the menu (or closes the active submenu first) |
| `Tab` | Closes the menu; focus moves to next focusable element in the page |
| Character key | Type-ahead: moves focus to the next item whose label starts with that character |

## 13. Accessibility
- The popup has `role="menu"` and `aria-label` (from `label` attribute or the
  trigger's accessible name via `aria-labelledby`).
- Individual items: `role="menuitem"`, `role="menuitemcheckbox"`, or
  `role="menuitemradio"`.
- The menu uses `aria-activedescendant` on the `role="menu"` element; the
  focused item has `id` referenced.
- Trigger element (managed externally by `<mj-menu-button>`): must have
  `aria-haspopup="menu"` and `aria-expanded` reflecting `open`.
- Disabled items: `aria-disabled="true"`; remain in DOM; not skippable but not
  activatable. Keyboard navigation skips them.
- Separators: `role="separator"`; `aria-hidden` is not set so screen readers
  can announce group boundaries.
- Group headings: `role="none"` or `role="presentation"`; associated via
  proximity, not `aria-labelledby` (WAI-ARIA menu pattern does not use
  `role="group"` with `aria-labelledby` for menu item groups).
- Keyboard shortcut hints are `aria-hidden="true"`; they are visual only.

## 14. Form participation
N/A — `<mj-menu>` is an actions/navigation component, not a form control.
`menuitemcheckbox` and `menuitemradio` states are not form values; use
`<mj-select>` / `<mj-checkbox-group>` for form participation.

## 15. Internationalization & RTL
- `label` attribute is localizable by authors.
- Type-ahead uses `Intl.Collator` for locale-aware character matching.
- In RTL (`dir="rtl"`), Arrow Right and Arrow Left submenu behaviors swap:
  Arrow Left opens a submenu; Arrow Right closes it.
- The flyout submenu opens to the inline-start (left in RTL) when space allows;
  the overlay engine handles collision and flips as needed.
- Item shortcut hints are not translated (they reflect keyboard keys, which are
  locale-independent).

## 16. Progressive enhancement / SSR
- Server-side rendering of `<mj-menu>` is limited because menus are dynamic
  overlays; the preferred SSR pattern is to render the trigger button only and
  have the menu appear on first interaction.
- Where a no-JS fallback is required, a `<details>/<summary>` pattern wrapping
  the link list may be used; on upgrade, the component replaces it.
- The `open` attribute in server markup renders the menu visibly on load (useful
  for storybook and screenshot tests).

## 17. Dependencies
- Section 6: Registry + base element helper, design-token stylesheet, overlay/
  positioning engine, focus utilities (`aria-activedescendant` helper),
  localization hook.
- `<mj-menu-item>` — companion element for individual action items.
- `<mj-menu-separator>` — companion element for visual/semantic dividers.
- `<mj-menu-group>` — companion element for grouped item sets.
- `<mj-menu-column>` — companion element for mega-menu columns.

## 18. Edge cases & error handling
- **Empty menu**: popup renders with a "No options" notice (localization key
  `mj.menu.empty`); close on Escape.
- **All items disabled**: keyboard navigation finds no enabled item; focus stays
  on the menu popup; Escape closes it.
- **Deeply nested submenus (> 3 levels)**: supported structurally; authors are
  advised in docs to limit nesting to 2 levels for usability.
- **Menu taller than viewport**: `--mj-menu-max-height` caps height; overflow
  scrolls with keyboard `Arrow Down`/`Up` continuing through scrolled items.
- **Trigger removed from DOM while menu is open**: menu closes; no focus
  restoration target; focus falls to `<body>`.
- **`placement` causes out-of-viewport position**: overlay engine flips and
  shifts; if no valid placement exists, the menu uses the best-fit position and
  clips with scroll.

## 19. Acceptance criteria
- [ ] Renders `role="menu"` popup anchored to the trigger element.
- [ ] `aria-activedescendant` tracks keyboard-focused item.
- [ ] Arrow Down/Up navigation cycles through enabled items; disabled items skipped.
- [ ] Home/End jump to first/last enabled item.
- [ ] Enter activates item; `mj-menu-select` fires; menu closes if `close-on-select`.
- [ ] `menuitemcheckbox` toggles `aria-checked` state.
- [ ] `menuitemradio` sets `aria-checked="true"` on selected; clears others in group.
- [ ] Submenu opens on Arrow Right (LTR); closes on Arrow Left / Escape.
- [ ] Escape closes the menu (or active submenu first); focus returns to trigger.
- [ ] Hover-intent mode: menu opens after `hover-delay` ms; cancels if pointer leaves.
- [ ] Light-dismiss: click outside closes menu.
- [ ] `variant="mega"` renders multi-column layout.
- [ ] Type-ahead jumps to matching item.
- [ ] RTL: arrow-key submenu directions swap.
- [ ] `mj-menu-open` and `mj-menu-close` are cancelable.
- [ ] Automated axe checks pass with zero violations.

## 20. Open questions
- Should `<mj-menu>` own the trigger `aria-haspopup` / `aria-expanded`
  management, or should that remain the responsibility of the wrapping
  `<mj-menu-button>`?
- Should context-menu mode (`variant="context"`) be a separate component to
  keep the surface area of this spec narrower?
