# Toolbar Spec

- **Tag:** `<mj-toolbar>`
- **Class / file:** `Toolbar` / `toolbar.js`
- **Category:** Application & productivity components
- **Primary or Variant:** Primary
- **Synonyms covered:** Command bar, Action bar, Ribbon variant
- **Phase:** P3
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-toolbar>` is a horizontal strip of grouped controls (buttons, toggles, selects, separators) that exposes a single tab stop via roving tabindex. It consolidates the Command bar, Action bar, and (in `variant="ribbon"`) a tabbed multi-row Ribbon without duplicating control implementations. Overflow items that do not fit the current width collapse into a trailing "More" menu button automatically.

## 2. When to use / when not to use
Use for contextual actions applied to the currently selected content or view (text editor toolbars, canvas toolbars, file-action bars). Do not use as a page-level navigation landmark — use `<mj-menubar>` for application menus or `<mj-app-shell>` for the top app-bar. Do not use for a single primary call-to-action; use `<mj-button>` directly.

## 3. Anatomy
- **toolbar root** — `<div role="toolbar">` with `aria-label` or `aria-labelledby`.
- **groups** — one or more `<mj-toolbar-group>` light-DOM children; each maps to a `<div role="group">` with its own label.
- **items** — `<mj-button>`, `<mj-toggle-button>`, `<mj-select>`, `<mj-separator>`, or other focusable primitives slotted into each group.
- **overflow trigger** — an `<mj-menu-button>` injected at the end of the root; hidden when all items fit.
- **overflow menu** — `<mj-menu>` populated with clones of hidden items; positioned by the overlay engine.
- **ribbon tab list** — (ribbon variant only) a `<div role="tablist">` above the toolbar body; each tab switches the visible group row.

## 4. Variants & modes
| Variant / mode | Attribute | Behavior difference |
|----------------|-----------|---------------------|
| Default toolbar | `variant="toolbar"` (default) | Single-row, roving tabindex, overflow menu |
| Command bar | `variant="command-bar"` | Adds an inline `<mj-search-input>` before the overflow trigger |
| Action bar | `variant="action-bar"` | Floats above selected content; auto-shows/hides based on `active` attribute |
| Ribbon | `variant="ribbon"` | Multi-row with a tablist; each tab reveals one group row |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `variant` | `"toolbar"\|"command-bar"\|"action-bar"\|"ribbon"` | `"toolbar"` | Yes | Selects the toolbar variant |
| `label` | string | `""` | Yes | Accessible name; sets `aria-label` on the root |
| `labelledby` | string | `""` | Yes | ID of external heading; sets `aria-labelledby` |
| `orientation` | `"horizontal"\|"vertical"` | `"horizontal"` | Yes | Sets `aria-orientation`; changes arrow-key axis |
| `active` | boolean | `false` | Yes | (action-bar) Shows/hides the bar with animation |
| `overflow-threshold` | number | `0` | No | Minimum px width before overflow kicks in; `0` = auto |
| `disabled` | boolean | `false` | Yes | Disables all child controls as a group |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `items` | `Element[]` | Read-only ordered list of all focusable toolbar items |
| `overflowItems` | `Element[]` | Read-only list of items currently moved to the overflow menu |
| `activeTab` | `string \| null` | (ribbon) ID of the currently selected ribbon tab |

## 7. Slots
| Slot | Description |
|------|-------------|
| (default) | Accepts `<mj-toolbar-group>` or direct focusable items |
| `search` | (command-bar) Replaces the built-in search input with a custom one |
| `overflow-icon` | Icon for the overflow "More" button |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-toolbar-overflow-change` | `{ overflowCount: number, overflowItems: Element[] }` | Yes | No | Fires when the set of overflowed items changes due to resize |
| `mj-toolbar-tab-change` | `{ tabId: string, previousTabId: string }` | Yes | No | (ribbon) Fires when the active ribbon tab changes |

## 9. CSS parts & custom properties
**Parts:** `root`, `group`, `separator`, `overflow-button`, `overflow-menu`, `ribbon-tablist`, `ribbon-tab`.

| Custom property | Default | Description |
|-----------------|---------|-------------|
| `--mj-toolbar-height` | `var(--mj-size-control-md)` | Height of the single-row toolbar |
| `--mj-toolbar-gap` | `var(--mj-space-1)` | Gap between items within a group |
| `--mj-toolbar-group-gap` | `var(--mj-space-3)` | Gap between groups |
| `--mj-toolbar-bg` | `var(--mj-color-surface-2)` | Background of the toolbar strip |
| `--mj-toolbar-border` | `var(--mj-border-subtle)` | Bottom border |
| `--mj-toolbar-ribbon-tab-height` | `var(--mj-size-control-sm)` | Height of ribbon tabs |

## 10. States
- **default** — full-opacity, all items reachable via roving tabindex.
- **disabled** — `aria-disabled="true"` on root; all child controls rendered non-interactive; visually dimmed.
- **overflow-active** — overflow menu button is visible; hidden items have `aria-hidden="true"` in the toolbar DOM and clones appear in the overflow menu.
- **active** (action-bar) — bar slides into view; `active` attribute present.
- **inactive** (action-bar) — bar is visually hidden; `active` attribute absent; `aria-hidden="true"` on root.
- **ribbon-tab-selected** — active ribbon tab has `aria-selected="true"`.

## 11. Behavior & interactions
On mount, a `ResizeObserver` watches the toolbar width. When items overflow the available space, they are hidden (`visibility:hidden; position:absolute`) in place and their clones are appended to the overflow `<mj-menu>`. The overflow button appears. On resize that recovers space, items are restored from the overflow menu in reverse order. Item identity is preserved via `data-toolbar-item-id`. The command-bar search input is never moved to the overflow menu. In ribbon mode, clicking/arrow-keying a tab switches the visible group row with a CSS `display` toggle; the previously active row's focused item is remembered and restored when that tab is re-activated.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` | Moves focus into and out of the toolbar (single tab stop) |
| `ArrowRight` / `ArrowDown` | Moves focus to next enabled item (wraps) |
| `ArrowLeft` / `ArrowUp` | Moves focus to previous enabled item (wraps) |
| `Home` | Focuses first enabled item |
| `End` | Focuses last enabled item |
| `Enter` / `Space` | Activates the focused item |
| `ArrowRight` / `ArrowLeft` on ribbon tabs | Navigates ribbon tabs (roving tabindex within tablist) |

## 13. Accessibility
Root element carries `role="toolbar"` with either `aria-label` or `aria-labelledby`. Groups carry `role="group"` with `aria-label`. Roving tabindex is managed by the Focus utility (§6): exactly one item has `tabindex="0"` at any time; all others have `tabindex="-1"`. When items are moved to the overflow menu their light-DOM originals receive `aria-hidden="true"`. The overflow button announces its purpose via `aria-label="More actions"` (localizable). Ribbon tablist uses `role="tablist"` / `role="tab"` / `aria-selected` / `aria-controls` per APG Tabs pattern but within the toolbar so arrows navigate tabs; `Tab` still exits the toolbar.

## 14. Form participation
N/A — toolbar is a structural widget, not an input. Individual form controls slotted inside participate in forms independently.

## 15. Internationalization & RTL
`label`, `overflow-button-label`, and `more-label` (command-bar search placeholder) are overridable attributes. In RTL (`dir="rtl"`), `ArrowLeft`/`ArrowRight` meanings are swapped to match logical inline direction. Separator orientation adapts. Ribbon tab order remains DOM order but visual position mirrors.

## 16. Progressive enhancement / SSR
Server renders a `<div role="toolbar">` with child buttons as native `<button>` elements. Without JS all items are tab-focusable (no roving tabindex). On upgrade, the element introduces roving tabindex, hides overflow items, and activates the `ResizeObserver`. No layout shift because the toolbar's height is fixed by token.

## 17. Dependencies
- **Foundations:** Registry + base element helper, Design-token stylesheet, Overlay/positioning engine, Focus utilities (roving tabindex), Live-region/announcement service.
- **Components:** `<mj-button>`, `<mj-toggle-button>`, `<mj-menu-button>`, `<mj-menu>`, `<mj-separator>`, `<mj-search-input>` (command-bar variant only).

## 18. Edge cases & error handling
- All items disabled: overflow button also disabled; roving tabindex lands on overflow button last.
- Zero-width container: all items overflow; toolbar shows only the overflow button.
- Dynamically added/removed items: `MutationObserver` triggers re-measurement.
- Ribbon with no tabs: renders as a plain toolbar.
- Conflicting `label` and `labelledby`: `labelledby` takes precedence; a console warning is emitted.
- Items without accessible names: component emits a development-mode warning per item.

## 19. Acceptance criteria
- [ ] Single `Tab` stop enters and exits the toolbar; arrows navigate items.
- [ ] `Home`/`End` reach first/last enabled item.
- [ ] `ResizeObserver` moves items to overflow menu when width is insufficient.
- [ ] Overflow menu items are functional clones of their toolbar originals.
- [ ] `mj-toolbar-overflow-change` fires with correct `overflowCount`.
- [ ] `role="toolbar"` and `aria-label` present on root.
- [ ] Axe scan reports zero violations in all variants.
- [ ] Ribbon tab switch shows correct group row and announces tab name.
- [ ] RTL arrow keys navigate in logically correct direction.
- [ ] All items disabled: toolbar is announced as disabled by screen reader.
- [ ] Light, dark, high-contrast, and RTL rendering verified.

## 20. Open questions
- Should ribbon tabs support drag-to-reorder?
- Is a vertical toolbar (for side-mounted panels) in scope for P3 or deferred?
- Should the overflow menu preserve group separators from the original groups?
