# Menubar Spec

- **Tag:** `<mj-menubar>`
- **Class / file:** `Menubar` / `menubar.js`
- **Category:** Application & productivity components
- **Primary or Variant:** Primary
- **Synonyms covered:** Application menubar
- **Phase:** P3
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-menubar>` implements the WAI-ARIA APG Menubar pattern: a horizontal bar of top-level menu labels that each open a vertical `<mj-menu>` on activation. It is the primary application-level command surface (File, Edit, View, Help) in desktop-style web apps. It provides roving tabindex across top-level items and full arrow-key traversal into and across submenus.

## 2. When to use / when not to use
Use when the application has a large, hierarchical command set organized by category (typical of desktop productivity apps). Do not use for a small set of page-level links — use `<mj-app-shell>`'s AppBar with nav links instead. Do not use for contextual actions tied to a selection — use `<mj-toolbar>`. Do not use as a navigation landmark for page-to-page links; that is `<nav>` / `<mj-sidenav>`.

## 3. Anatomy
- **menubar root** — `<div role="menubar">` with `aria-label`.
- **top-level items** — `<mj-menubar-item>` children; each renders a `<button role="menuitem">` and owns a `<mj-menu>` popup.
- **dropdown menus** — `<mj-menu>` instances anchored below each top-level item; may contain `<mj-menu-item>`, `<mj-menu-item-checkbox>`, `<mj-menu-item-radio>`, `<mj-separator>`, and nested `<mj-menu>` submenus.
- **submenu indicators** — trailing arrow icons on items that have submenus.

## 4. Variants & modes
| Variant / mode | Attribute | Behavior difference |
|----------------|-----------|---------------------|
| Default | (none) | Full menubar with dropdown menus |
| Compact | `compact` | Reduces top-level item padding for dense layouts |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `label` | string | `"Application menu"` | Yes | Accessible name via `aria-label` on the menubar root |
| `compact` | boolean | `false` | Yes | Reduces item padding |
| `disabled` | boolean | `false` | Yes | Disables all top-level items |
| `active-item` | string | `""` | Yes | ID of the currently open top-level item; reflects open state |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `items` | `Element[]` | Read-only ordered list of top-level `<mj-menubar-item>` elements |
| `openMenu` | `Element \| null` | Reference to the currently open `<mj-menu>`, or `null` |

## 7. Slots
| Slot | Description |
|------|-------------|
| (default) | Accepts `<mj-menubar-item>` elements in desired top-level order |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-menubar-open` | `{ item: Element, menuId: string }` | Yes | No | Fires when a top-level menu opens |
| `mj-menubar-close` | `{ item: Element, menuId: string }` | Yes | No | Fires when a top-level menu closes |
| `mj-menubar-select` | `{ item: Element, value: string, path: string[] }` | Yes | No | Fires when a menu item is activated; `path` is the label breadcrumb |

## 9. CSS parts & custom properties
**Parts:** `root`, `item`, `item-label`, `item-indicator`, `menu`.

| Custom property | Default | Description |
|-----------------|---------|-------------|
| `--mj-menubar-height` | `var(--mj-size-control-md)` | Height of the menubar strip |
| `--mj-menubar-bg` | `var(--mj-color-surface-2)` | Background color |
| `--mj-menubar-item-padding` | `0 var(--mj-space-3)` | Padding of each top-level item |
| `--mj-menubar-item-hover-bg` | `var(--mj-color-neutral-hover)` | Hover background |
| `--mj-menubar-item-active-bg` | `var(--mj-color-neutral-active)` | Open/active background |
| `--mj-menubar-border` | `var(--mj-border-subtle)` | Bottom border of the bar |

## 10. States
- **default** — bar visible, no menu open, first item has `tabindex="0"`.
- **item-hovered** — item shows hover background; no menu opens on hover alone.
- **item-focused** — item has focus-visible ring; shows focused background.
- **menu-open** — top-level item has `aria-expanded="true"`; its `<mj-menu>` is visible; other top-level items gain hover-to-switch behavior.
- **disabled** — `aria-disabled="true"` on root and all items; visually dimmed.

## 11. Behavior & interactions
Clicking or pressing `Enter`/`Space`/`ArrowDown` on a top-level item opens its dropdown menu. While any menu is open, moving the pointer over another top-level item closes the current menu and opens the new one (hover-to-switch). Clicking outside or pressing `Escape` closes the open menu and returns focus to the triggering top-level item. `ArrowLeft`/`ArrowRight` on a top-level item switches focus between top-level items; if a menu is open, it closes the current and opens the next. `ArrowDown` from a top-level item opens the menu and moves focus to the first item. `ArrowUp` opens the menu and focuses the last item. Focus exits the menubar on `Tab` and `Shift+Tab`.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` / `Shift+Tab` | Enter/exit the menubar; single tab stop when no menu open |
| `ArrowRight` | Focus next top-level item (wraps); if menu open, close current and open next |
| `ArrowLeft` | Focus previous top-level item (wraps); if menu open, close current and open previous |
| `Enter` / `Space` / `ArrowDown` | Open the focused top-level item's menu; focus first menu item |
| `ArrowUp` | Open menu; focus last menu item |
| `Escape` | Close open menu; return focus to triggering top-level item |
| `Home` | Focus first top-level item |
| `End` | Focus last top-level item |
| Printable character | Move focus to next top-level item starting with that character |

## 13. Accessibility
Root carries `role="menubar"` and `aria-label`. Each top-level button carries `role="menuitem"`, `aria-haspopup="menu"`, and `aria-expanded` reflecting the open state. Submenus use `<mj-menu>` which carries `role="menu"`. Roving tabindex is managed by the Focus utility: exactly one top-level item is `tabindex="0"` at any time. When a menu is open, focus moves into the menu; the menu itself manages internal roving tabindex per the APG Menu pattern. Screen reader users hear the menubar label, item labels, and whether each item has a submenu.

## 14. Form participation
N/A — menubar items trigger commands, not form values.

## 15. Internationalization & RTL
The `label` attribute is localizable. In RTL (`dir="rtl"`), `ArrowLeft`/`ArrowRight` semantics are flipped to match logical inline direction. Submenus open to the left of their parent item. Menu items with keyboard shortcuts display the shortcut in a trailing `<kbd>` element; shortcut strings are provided by the consumer and are not translated by the component.

## 16. Progressive enhancement / SSR
Server renders a `<nav aria-label="Application menu">` containing an `<ul>` of `<li><a>` items. Without JS, top-level items navigate to anchor URLs (each menu section can be a `<details>/<summary>` fallback). On upgrade, the element replaces `<ul>/<li>/<a>` semantics with `role="menubar"` and injects dropdown `<mj-menu>` instances. Focus management and hover-to-switch activate only after upgrade.

## 17. Dependencies
- **Foundations:** Registry + base element helper, Design-token stylesheet, Overlay/positioning engine, Focus utilities (roving tabindex), Live-region/announcement service.
- **Components:** `<mj-menu>`, `<mj-menu-item>`, `<mj-menu-item-checkbox>`, `<mj-menu-item-radio>`, `<mj-separator>`.

## 18. Edge cases & error handling
- Single top-level item: still renders a menubar; `ArrowLeft`/`ArrowRight` are no-ops (no wrap to self).
- Top-level item with no menu children: renders as a plain `menuitem` (no `aria-haspopup`); activating it fires `mj-menubar-select` directly.
- Very long label: item truncates with `text-overflow: ellipsis`; full label in `title` attribute for tooltip fallback.
- Disabled item: `aria-disabled="true"`; roving tabindex skips it.
- Menu that overflows the viewport: overlay engine flips it upward and shifts horizontally.
- Nested submenus deeper than 3 levels: component emits a development-mode warning; still functional.

## 19. Acceptance criteria
- [ ] `role="menubar"` and `aria-label` present on root.
- [ ] Each top-level item has `role="menuitem"`, `aria-haspopup="menu"`, and correct `aria-expanded`.
- [ ] Roving tabindex: exactly one top-level item is `tabindex="0"`.
- [ ] `ArrowLeft`/`ArrowRight` navigate top-level items; hover-to-switch works when a menu is open.
- [ ] `Escape` closes open menu and returns focus to the top-level item.
- [ ] `mj-menubar-select` fires with correct `path` breadcrumb.
- [ ] Axe scan reports zero violations.
- [ ] RTL: arrow key directions and submenu opening direction are correct.
- [ ] Light, dark, high-contrast, and RTL rendering verified.

## 20. Open questions
- Should keyboard shortcuts defined on menu items be registered globally (e.g., via a command registry) or left to the consumer?
- Should checked state of `menu-item-radio` groups persist across open/close cycles internally?
