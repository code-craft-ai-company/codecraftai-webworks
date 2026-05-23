# Menu Button Spec

- **Tag:** `<mj-menu-button>`
- **Class / file:** `MjMenuButton` / `mjmenubutton.js`
- **Category:** Selection & dropdown-style controls
- **Primary or Variant:** Primary
- **Synonyms covered:** Kebab menu button, Meatball menu button, Overflow menu button
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-menu-button>` is a single button that opens an attached actions menu. It is the standard implementation for overflow (kebab/meatball/ellipsis) menus, contextual action menus, and any scenario where a set of actions must be tucked behind a single trigger. The button has `aria-haspopup="menu"` and the popup follows the WAI-ARIA `menu` / `menuitem` pattern.

## 2. When to use / when not to use
**Use** for contextual row/card actions that would clutter the primary UI if displayed inline. **Use** the icon-only variant (three-dot vertical or horizontal) for compact overflow affordances — always provide an accessible label. **Do not use** when the most common action should be directly accessible — prefer `<mj-split-button>`. **Do not use** for navigation — prefer `<mj-select>` or a nav component. **Do not use** when all actions should always be visible — use a toolbar or button row.

## 3. Anatomy
- **Trigger button** (`part="trigger"`) — the `<button>` element that opens the menu.
- **Trigger label** (`part="trigger-label"`) — optional text label.
- **Trigger icon** (`part="trigger-icon"`) — optional icon (kebab/meatball/chevron).
- **Popup** (`part="popup"`) — positioned overlay managed by the overlay engine.
- **Menu** (`part="menu"`) — `role="menu"` container.
- **Menu item** (`part="menu-item"`) — `role="menuitem"` element.
- **Menu item icon** (`part="menu-item-icon"`) — optional leading icon per item.
- **Menu item label** (`part="menu-item-label"`) — item text.
- **Menu item shortcut** (`part="menu-item-shortcut"`) — keyboard shortcut hint text.
- **Menu separator** (`part="menu-separator"`) — `role="separator"` divider between item groups.
- **Menu group** (`part="menu-group"`) — `role="group"` with optional group label.

## 4. Variants & modes
| Variant / mode | Attribute | Behavior |
|----------------|-----------|----------|
| Icon-only (kebab) | `icon-only` (boolean) | Only icon shown; `aria-label` required |
| Icon + label | (default) | Icon and text label side-by-side |
| Label-only | no icon slotted | Text label only |
| Nested submenu | `<mj-menu-item>` with submenu slot | Item opens a nested popup on hover/arrow |
| Danger item | `variant="danger"` on `<mj-menu-item>` | Destructive styling on that item |
| Size variants | `size="sm"` \| `"md"` \| `"lg"` | Trigger button size |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `label` | string | `""` | Yes | Accessible label for the trigger button |
| `icon-only` | boolean | `false` | Yes | Hides the text label; icon only is shown |
| `disabled` | boolean | `false` | Yes | Disables the trigger; menu cannot open |
| `open` | boolean | `false` | Yes | Opens/closes the menu programmatically |
| `placement` | `"bottom-start"` \| `"bottom-end"` \| `"top-start"` \| `"top-end"` | `"bottom-start"` | Yes | Preferred popup placement before flip/shift |
| `size` | `"sm"` \| `"md"` \| `"lg"` | `"md"` | Yes | Visual size of the trigger |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `menuItems` | `MjMenuItem[]` | Live array of `<mj-menu-item>` elements |
| `focusedItem` | `MjMenuItem \| null` | Currently keyboard-focused menu item |

## 7. Slots
| Slot | Description |
|------|-------------|
| (default) | `<mj-menu-item>`, `<mj-menu-separator>`, and `<mj-menu-group>` elements |
| `trigger-icon` | Icon element rendered inside the trigger button |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-open` | `{}` | Yes | Yes | Fired before menu opens; cancel to prevent |
| `mj-close` | `{}` | Yes | No | Fired after menu closes |
| `mj-select` | `{ item: MjMenuItem, value: string }` | Yes | No | Fired when a menu item is activated |

## 9. CSS parts & custom properties
**Parts:** `trigger`, `trigger-label`, `trigger-icon`, `popup`, `menu`, `menu-item`, `menu-item-icon`, `menu-item-label`, `menu-item-shortcut`, `menu-separator`, `menu-group`, `menu-group-label`

**Custom properties:**
| Property | Default token | Description |
|----------|---------------|-------------|
| `--mj-menu-button-trigger-size` | `--mj-size-control-md` | Trigger button height (and width in icon-only mode) |
| `--mj-menu-popup-min-width` | `10rem` | Minimum popup width |
| `--mj-menu-popup-max-height` | `24rem` | Maximum popup height |
| `--mj-menu-item-height` | `2.25rem` | Height of each menu item row |
| `--mj-menu-item-padding` | `--mj-space-2 --mj-space-3` | Padding inside each item |
| `--mj-menu-border-radius` | `--mj-radius-md` | Popup corner radius |
| `--mj-menu-separator-color` | `--mj-color-border-subtle` | Color of separator lines |

## 10. States
| State | Visual effect | ARIA effect |
|-------|--------------|-------------|
| Default | Trigger at rest | `aria-expanded="false"` |
| Trigger hovered | Hover tint | — |
| Trigger focused | Focus ring | — |
| Menu open | Popup visible | `aria-expanded="true"` |
| Item focused | Row highlighted | `aria-activedescendant` on menu |
| Item with submenu open | Submenu popup visible | `aria-expanded="true"` on item |
| Item danger | Red/error text color | — |
| Item disabled | Muted text; no pointer events | `aria-disabled="true"` |
| Trigger disabled | Muted trigger | `disabled` on `<button>` |

## 11. Behavior & interactions
- Clicking the trigger opens the popup and focuses the first non-disabled menu item via `aria-activedescendant`.
- Clicking a menu item fires `mj-select`, closes the popup, and returns focus to the trigger.
- Light-dismiss (click outside or focus outside) closes the popup without selecting.
- Menu items with submenus: hovering with a 200 ms intent delay opens the submenu; the delay is cancelable if focus moves away.
- The popup is positioned by the overlay engine using the `placement` attribute; it flips and shifts to stay within the viewport.
- `icon-only` triggers must have an `aria-label` or `label` attribute; the component logs a console error if neither is present.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Enter` / `Space` / `ArrowDown` | Open menu; focus first item |
| `ArrowUp` | Open menu; focus last item |
| `ArrowDown` | Move focus to next item |
| `ArrowUp` | Move focus to previous item |
| `Home` | Focus first item |
| `End` | Focus last item |
| `Enter` / `Space` | Activate focused item |
| `ArrowRight` | Open submenu (if item has submenu); focus first submenu item |
| `ArrowLeft` | Close submenu; return focus to parent item |
| `Escape` | Close menu (or submenu); return focus to trigger (or parent item) |
| `Tab` | Close menu; move focus to next focusable element |

## 13. Accessibility
- Trigger has `role="button"` (is a `<button>` element), `aria-haspopup="menu"`, and `aria-expanded`.
- `aria-controls` on the trigger references the menu element's `id`.
- Menu has `role="menu"` with `aria-labelledby` pointing to the trigger's `id`.
- Each item has `role="menuitem"` (or `menuitemcheckbox` / `menuitemradio` for stateful variants).
- Disabled items have `aria-disabled="true"`; they are still focusable (skipped in keyboard navigation per WAI-ARIA pattern).
- Separators have `role="separator"`.
- Groups have `role="group"` with `aria-labelledby` pointing to the group label.
- Focus is managed via `aria-activedescendant` on the menu; DOM focus remains on the menu element.
- Keyboard shortcut hints in `menu-item-shortcut` are visible but `aria-hidden="true"` (shortcuts work globally; the hint is supplementary).
- Icon-only trigger missing a label: component logs a console error and falls back to `aria-label="Actions"`.

## 14. Form participation
- Not form-associated; `<mj-menu-button>` is an action control, not an input.
- The trigger `<button>` has `type="button"` to prevent accidental form submission.

## 15. Internationalization & RTL
- In RTL, the popup opens on the mirrored side (e.g., `bottom-start` becomes visually bottom-right).
- Item icons are leading in RTL (flip icon positions with `margin-inline-end`).
- Keyboard shortcut hints are displayed as-is (platform-specific; e.g., "⌘K" not translated).
- `label` and item text are author-supplied; no built-in English strings except the fallback `aria-label` for unlabeled icon-only triggers (which must be overridden).

## 16. Progressive enhancement / SSR
- Server renders a `<button>` trigger and a hidden `<ul>` of `<li>` menu items inside `<mj-menu-button>`.
- Before upgrade, the menu is not interactive (no JS to open it); the trigger is a plain button.
- On upgrade, the component wires open/close logic; the `<ul>` is replaced with the ARIA `menu` structure.
- Without scripting: the trigger button is rendered but the menu cannot open; a `noscript` fallback with visible links is recommended for critical actions.

## 17. Dependencies
- Section 6: Registry/base element, design tokens, overlay/positioning engine, focus utilities (`aria-activedescendant` helper).
- `<mj-menu-item>` — menu item primitive.
- `<mj-menu-separator>` — separator primitive.
- `<mj-menu-group>` — group primitive.

## 18. Edge cases & error handling
- No menu items slotted: trigger is disabled; a console warning is logged.
- All items disabled: menu opens; keyboard navigation yields no activatable item; `Escape` still closes.
- Menu item added/removed dynamically while menu is open: item list re-renders; `aria-activedescendant` stays valid or resets to the first item.
- Popup obscured by viewport edge: overlay engine shifts; minimum `--mj-menu-popup-min-width` is maintained.
- `icon-only` without `aria-label` or `label`: fallback `aria-label="Actions"` applied; error logged.
- Very long item labels: text truncates with ellipsis; full text visible on hover via `title` tooltip.

## 19. Acceptance criteria
- [ ] Clicking trigger opens popup; `aria-expanded="true"`; first item receives `aria-activedescendant`.
- [ ] Activating an item fires `mj-select` with correct `item` and `value`; popup closes.
- [ ] Escape closes popup and returns focus to trigger.
- [ ] `ArrowDown` / `ArrowUp` / `Home` / `End` navigate items.
- [ ] Disabled items are skipped by keyboard navigation; cannot be clicked.
- [ ] `role="menu"` on popup container; `role="menuitem"` on each item; `role="separator"` on separators.
- [ ] `aria-haspopup="menu"` and `aria-expanded` correct on trigger.
- [ ] Icon-only trigger without label logs an error; fallback `aria-label` applied.
- [ ] axe-core reports zero violations in default, open, and disabled states.
- [ ] RTL popup opens on the correct side; icon positions mirror.

## 20. Open questions
- Should `menuitemcheckbox` and `menuitemradio` be in scope for this component or deferred to a separate stateful menu variant?
- Should nested submenus be limited to a single level deep, or is arbitrary depth supported?
- Should hover intent delay for submenu open be configurable via an attribute?
