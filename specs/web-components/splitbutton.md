# Split Button Spec

- **Tag:** `<mj-split-button>`
- **Class / file:** `MjSplitButton` / `mjsplitbutton.js`
- **Category:** Selection & dropdown-style controls
- **Primary or Variant:** Primary
- **Synonyms covered:** Split action button
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-split-button>` combines a primary action button with an adjacent dropdown arrow that opens a menu of alternate actions. The two parts are visually joined but are independently focusable and activatable controls, ensuring the dropdown does not intercept the primary action. This pattern is common in save/save-as, send/schedule, and export/export-as scenarios.

## 2. When to use / when not to use
**Use** when there is one clear default action plus a small number of related but secondary action variants. **Do not use** when all actions are equally prominent — use separate buttons or a `<mj-menu-button>`. **Do not use** when the action alternatives change the default action itself on selection (use a variant where clicking the dropdown item also updates the primary label). **Do not use** for navigation — use a link or `<mj-menu-button>`.

## 3. Anatomy
- **Container** (`part="container"`) — flex row holding both controls.
- **Primary button** (`part="primary"`) — the main action `<button>` element.
- **Primary label** (`part="primary-label"`) — text inside the primary button.
- **Primary icon** (`part="primary-icon"`) — optional leading icon.
- **Divider** (`part="divider"`) — visual separator between the two buttons.
- **Dropdown trigger** (`part="dropdown-trigger"`) — chevron/arrow `<button>` that opens the menu.
- **Dropdown icon** (`part="dropdown-icon"`) — chevron icon inside the trigger.
- **Popup** (`part="popup"`) — positioned menu overlay.
- **Menu** (`part="menu"`) — `role="menu"` container inside the popup.
- **Menu item** (`part="menu-item"`) — each `role="menuitem"` element.

## 4. Variants & modes
| Variant / mode | Attribute | Behavior |
|----------------|-----------|----------|
| Static primary | (default) | Primary button label and action are fixed |
| Dynamic primary | `dynamic` (boolean) | Selecting a menu item updates the primary button's label and action |
| Disabled | `disabled` (boolean) | Both parts disabled |
| Primary disabled only | `primary-disabled` (boolean) | Primary button disabled; dropdown still opens |
| Size variants | `size="sm"` \| `"md"` \| `"lg"` | Propagated to both buttons |
| Variant styles | `variant="primary"` \| `"secondary"` \| `"danger"` | Color/weight of the button pair |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `label` | string | `""` | Yes | Accessible label of the primary button |
| `variant` | `"primary"` \| `"secondary"` \| `"danger"` | `"primary"` | Yes | Visual style variant |
| `size` | `"sm"` \| `"md"` \| `"lg"` | `"md"` | Yes | Size of both buttons |
| `disabled` | boolean | `false` | Yes | Disables both parts |
| `primary-disabled` | boolean | `false` | Yes | Disables only the primary button |
| `open` | boolean | `false` | Yes | Opens/closes the dropdown menu |
| `dynamic` | boolean | `false` | Yes | Primary button adopts last-selected menu item |
| `dropdown-label` | string | `"More actions"` | Yes | Accessible label for the dropdown trigger button |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `menuItems` | `MjMenuItem[]` | Live array of menu item elements |
| `activeItem` | `MjMenuItem \| null` | The menu item whose action mirrors the primary (dynamic mode) |

## 7. Slots
| Slot | Description |
|------|-------------|
| (default) | `<mj-menu-item>` elements for the dropdown menu |
| `primary-icon` | Icon to show inside the primary button |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-primary-click` | `{}` | Yes | No | Fired when the primary button is clicked |
| `mj-menu-select` | `{ item: MjMenuItem, value: string }` | Yes | No | Fired when a menu item is selected |
| `mj-open` | `{}` | Yes | Yes | Fired before the dropdown menu opens |
| `mj-close` | `{}` | Yes | No | Fired after the dropdown menu closes |

## 9. CSS parts & custom properties
**Parts:** `container`, `primary`, `primary-label`, `primary-icon`, `divider`, `dropdown-trigger`, `dropdown-icon`, `popup`, `menu`, `menu-item`

**Custom properties:**
| Property | Default token | Description |
|----------|---------------|-------------|
| `--mj-split-button-height` | `--mj-size-control-md` | Height of both buttons |
| `--mj-split-button-border-radius` | `--mj-radius-md` | Outer border radius |
| `--mj-split-button-divider-color` | `--mj-color-border-contrast` | Color of the divider between the two parts |
| `--mj-split-button-popup-min-width` | `10rem` | Minimum width of the dropdown popup |

## 10. States
| State | Visual effect | ARIA effect |
|-------|--------------|-------------|
| Default | Joined button pair at rest | — |
| Primary hovered | Primary button highlights | — |
| Primary focused | Focus ring on primary button | — |
| Dropdown hovered | Dropdown trigger highlights | — |
| Dropdown focused | Focus ring on dropdown trigger | — |
| Menu open | Chevron rotated; popup visible | `aria-expanded="true"` on dropdown trigger |
| Menu item focused | Row highlighted | `aria-activedescendant` on menu |
| Disabled | Both parts muted | `aria-disabled="true"` on both buttons; `disabled` attribute on `<button>` |
| Primary disabled | Primary muted; dropdown active | `disabled` on primary `<button>` only |

## 11. Behavior & interactions
- Clicking the primary button fires `mj-primary-click` and does NOT open the dropdown.
- Clicking the dropdown trigger opens the menu popup; it does NOT invoke the primary action.
- The menu popup is positioned below the dropdown trigger by default, aligned to the trailing edge; the overlay engine flips/shifts to keep it in viewport.
- Clicking a menu item fires `mj-menu-select`, closes the popup, and returns focus to the dropdown trigger.
- In `dynamic` mode, selecting a menu item also updates the primary button's label and stored action; subsequent primary-button clicks invoke that selected action.
- Light-dismiss (clicking outside) closes the popup without selecting an item.

## 12. Keyboard interaction
| Key | Focus on | Action |
|-----|----------|--------|
| `Tab` | — | Moves focus to primary button, then dropdown trigger, then next element |
| `Enter` / `Space` | Primary button | Fires `mj-primary-click` |
| `Enter` / `Space` / `ArrowDown` | Dropdown trigger | Opens menu; focuses first menu item |
| `ArrowDown` | Menu open | Move focus to next menu item |
| `ArrowUp` | Menu open | Move focus to previous menu item |
| `Home` | Menu open | Focus first menu item |
| `End` | Menu open | Focus last menu item |
| `Enter` / `Space` | Menu item | Select item; close menu; return focus to dropdown trigger |
| `Escape` | Menu open | Close menu; return focus to dropdown trigger |
| `Tab` | Menu open | Close menu; move focus to next focusable element |

## 13. Accessibility
- The primary button has `aria-label` equal to the `label` attribute; it has no `aria-haspopup`.
- The dropdown trigger has `aria-label` equal to `dropdown-label`; it has `aria-haspopup="menu"` and `aria-expanded`.
- The two controls are sibling `<button>` elements so screen readers read them as separate controls in the tab sequence.
- The menu uses `role="menu"` with `aria-labelledby` pointing to the dropdown trigger.
- Each menu item uses `role="menuitem"`.
- Focus is managed via `aria-activedescendant` on the menu container so DOM focus stays on the menu container.
- In dynamic mode, the primary button's accessible name updates when a new item is selected; a polite live region announces the change: "Default action changed to [item label]".

## 14. Form participation
- Not form-associated; split buttons are action controls, not input controls.
- If used inside a `<form>`, the primary button can carry `type="submit"` for a specific use case; the dropdown trigger always has `type="button"`.

## 15. Internationalization & RTL
- In RTL, the primary button is on the right and the dropdown trigger is on the left (visual order reversed).
- The divider remains between them; border-radius flips accordingly.
- `dropdown-label` is author-supplied; a default of "More actions" should be overridden for non-English locales.
- Menu popup aligns to the trailing edge in RTL.

## 16. Progressive enhancement / SSR
- Server renders two `<button>` elements inside `<mj-split-button>`.
- Before upgrade both buttons are individually operable.
- On upgrade, the dropdown trigger is wired to open the popup containing the slotted menu items.
- Without scripting, the primary button is functional; the dropdown trigger is a plain button with no menu behavior.

## 17. Dependencies
- Section 6: Registry/base element, design tokens, overlay/positioning engine, focus utilities (`aria-activedescendant` helper), live-region service.
- `<mj-menu>` / `<mj-menu-item>` — menu and item primitives shared with `<mj-menu-button>`.

## 18. Edge cases & error handling
- No menu items slotted: dropdown trigger is disabled automatically; a console warning is logged.
- Single menu item: the split button is still valid; the item serves as an alternate action.
- Menu item with `disabled`: rendered in the menu but not activatable; `aria-disabled="true"`; skipped by keyboard navigation.
- `dynamic` mode with no item selected: primary button uses the original `label` attribute value.
- Popup clips viewport edge: overlay engine shifts popup horizontally; minimum popup width is respected.

## 19. Acceptance criteria
- [ ] Clicking primary button fires `mj-primary-click`; popup does not open.
- [ ] Clicking dropdown trigger opens popup; `aria-expanded="true"` on trigger.
- [ ] Keyboard navigation in the open menu: arrows, Home, End, Enter, Escape work correctly.
- [ ] Selecting a menu item fires `mj-menu-select`; popup closes; focus returns to dropdown trigger.
- [ ] `dynamic=true`: primary button label updates after menu item selection.
- [ ] Primary button and dropdown trigger are separate tab stops.
- [ ] `aria-haspopup="menu"` and `aria-expanded` correct on dropdown trigger; absent on primary button.
- [ ] axe-core reports zero violations in default, open, disabled, and dynamic states.
- [ ] RTL positions dropdown trigger on the left; menu aligns to trailing edge.

## 20. Open questions
- In `dynamic` mode, should the primary button also fire the newly selected item's action immediately on selection, or only on the next explicit primary-button click?
- Should the popup width be at least as wide as the entire split button, or only as wide as the dropdown trigger portion?
- Should disabled menu items receive focus during keyboard navigation (WAI-ARIA allows either; a project-wide policy is needed)?
