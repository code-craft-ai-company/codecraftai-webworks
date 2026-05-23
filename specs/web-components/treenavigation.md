# Tree Navigation Spec

- **Tag:** `<mj-tree-nav>`
- **Class / file:** `MjTreeNav` / `mjtreenav.js`
- **Category:** Navigation components
- **Primary or Variant:** Primary
- **Synonyms covered:** Tree navigation, Folder tree nav, Hierarchical navigation, Nav tree
- **Phase:** P2
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-tree-nav>` is a hierarchical navigable tree component implementing the
WAI-ARIA `tree`/`treeitem` pattern. Each node is a link to a URL with expand/
collapse control for parent nodes. The current-page node is marked with
`aria-current="page"`. It is used for sidebar file trees, documentation site
navigation, and any content with deep hierarchical structure.

## 2. When to use / when not to use
**Use** when navigation content has a deep hierarchy (three or more levels) where
parent nodes act as both navigation links and structural containers for child
links. **Do not use** for flat or two-level navigation — use `<mj-side-nav>`.
**Do not use** for selection of a value from a hierarchy — use `<mj-tree-selector>`.
**Do not use** for file-system browsing with selection — use `<mj-file-browser>`.

## 3. Anatomy
- **Host / `<nav>`** — `<nav aria-label>` landmark wrapping the tree.
- **Tree root** (`::part(tree)`) — `<ul role="tree">` containing top-level items.
- **Tree item** (`::part(item)`) — `<li role="treeitem">` for each node.
- **Item row** (`::part(item-row)`) — flex container holding the expand toggle, icon, and link.
- **Expand toggle** (`::part(toggle)`) — `<button>` with `aria-expanded`; shown on parent nodes.
- **Item icon** (`::part(item-icon)`) — optional decorative icon (`aria-hidden`).
- **Item link** (`::part(item-link)`) — `<a>` anchor for the node's URL.
- **Item label** (`::part(item-label)`) — text label of the node.
- **Child tree** (`::part(child-tree)`) — `<ul role="group">` containing child `<mj-tree-nav-item>` elements.
- **Item badge** (`::part(item-badge)`) — optional count or status badge beside the label.

## 4. Variants & modes
| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Default | _(none)_ | Links with expand/collapse; parent nodes are also navigable links |
| Parent-as-toggle | `parent-toggle` | Clicking the parent node label toggles the child group; a separate link icon navigates |
| Compact | `compact` | Reduced item height; used in dense sidebars |
| With icons | _(per item)_ | Each `<mj-tree-nav-item>` may have an `icon` attribute or slot |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `nav-label` | string | `"Navigation"` | Yes | `aria-label` for the `<nav>` landmark |
| `current` | string | `""` | Yes | `id` or `href` of the currently active item; used to set `aria-current="page"` |
| `parent-toggle` | boolean | `false` | Yes | When true, the parent item label toggles expand/collapse instead of navigating |
| `compact` | boolean | `false` | Yes | Reduces item block size |
| `auto-expand` | boolean | `true` | Yes | Automatically expands ancestors of the `current` item on connect |
| `persist-state` | boolean | `false` | Yes | Saves expanded/collapsed state per node to `sessionStorage` |
| `persist-key` | string | `"mj-tree-nav"` | Yes | `sessionStorage` key prefix for persisted expand state |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `currentItem` | `Element \| null` | Read-only; the `<mj-tree-nav-item>` with `aria-current="page"` |
| `expandedItems` | `Element[]` | Read-only list of all currently expanded parent items |
| `activeItem` | `Element \| null` | The item with current keyboard focus (`aria-activedescendant` target) |

## 7. Slots
| Slot | Description |
|------|-------------|
| _(default)_ | `<mj-tree-nav-item>` elements at the root level |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-tree-nav-expand` | `{ item: Element, id: string }` | Yes | Yes | Fires when a parent node is about to expand; cancel to prevent |
| `mj-tree-nav-collapse` | `{ item: Element, id: string }` | Yes | Yes | Fires when a parent node is about to collapse; cancel to prevent |
| `mj-tree-nav-navigate` | `{ item: Element, href: string }` | Yes | Yes | Fires when a tree item link is activated; cancel to intercept routing |
| `mj-tree-nav-focus` | `{ item: Element }` | Yes | No | Fires when keyboard focus moves to a tree item |

## 9. CSS parts & custom properties
**Parts**
- `::part(tree)` — root `<ul role="tree">`
- `::part(item)` — each `<li role="treeitem">`
- `::part(item-row)` — row flex container
- `::part(toggle)` — expand/collapse button
- `::part(item-icon)` — node icon
- `::part(item-link)` — the `<a>` anchor
- `::part(item-label)` — text label span
- `::part(item-badge)` — optional badge
- `::part(child-tree)` — nested `<ul role="group">`

**Custom properties**
| Property | Default | Description |
|----------|---------|-------------|
| `--mj-tree-nav-item-height` | `36px` | Block size per item row |
| `--mj-tree-nav-indent` | `var(--mj-spacing-5)` | Per-level indentation |
| `--mj-tree-nav-bg-hover` | `var(--mj-color-surface-hover)` | Row hover background |
| `--mj-tree-nav-bg-active` | `var(--mj-color-surface-selected)` | Current-page row background |
| `--mj-tree-nav-color-active` | `var(--mj-color-primary)` | Current-page link text color |
| `--mj-tree-nav-active-border` | `2px solid var(--mj-color-primary)` | Start-edge border for current item |
| `--mj-tree-nav-font-size` | `var(--mj-font-size-sm)` | Font size for item labels |
| `--mj-tree-nav-toggle-size` | `20px` | Size of the expand/collapse toggle button |
| `--mj-tree-nav-transition-duration` | `var(--mj-motion-duration-short)` | Expand/collapse animation duration |

## 10. States
- **default** — all items at rest; current item highlighted.
- **expanded** — parent item child group is visible; toggle has `aria-expanded="true"`.
- **collapsed** — parent item child group is hidden; toggle has `aria-expanded="false"`.
- **current** — item matching the current URL has `aria-current="page"` and active token styling.
- **focused** — the keyboard-active item is tracked via `aria-activedescendant`.
- **hover** — row shows hover background token.
- **disabled** — item link is `aria-disabled="true"`; not navigable.
- **loading** — a lazy-loaded subtree is pending; toggle shows spinner.

## 11. Behavior & interactions
- The tree uses `role="tree"` with `aria-activedescendant` on the tree element
  to track keyboard focus; the tree element itself receives DOM focus (`tabindex="0"`).
- Individual items are not directly focusable; they are identified by `id` and
  referenced via `aria-activedescendant`.
- Expand/collapse: clicking the toggle button or Arrow Right/Left toggles the
  child group. Collapsing animates with a CSS height transition respecting
  `prefers-reduced-motion`.
- `auto-expand`: on `connectedCallback`, the component walks up from the `current`
  item and expands all ancestor nodes.
- `persist-state`: the expanded/collapsed state of each item (keyed by item `id`
  or index) is stored in `sessionStorage`; restored on page load.
- Lazy loading: `<mj-tree-nav-item>` may have a `src` attribute pointing to a
  URL from which child items are fetched (JSON array of item descriptors) on
  first expand. During fetch, a spinner replaces the child list; on error, an
  inline error message is shown.
- `parent-toggle` mode: clicking the item label text toggles the child group;
  a secondary icon-button provides the navigation link.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` | Moves DOM focus into the tree (single tab stop); Tab again moves out |
| `Arrow Down` | Moves `aria-activedescendant` to next visible item in the flattened tree order |
| `Arrow Up` | Moves to previous visible item |
| `Arrow Right` | Expands a collapsed parent item; if already expanded, moves to first child |
| `Arrow Left` | Collapses an expanded parent item; if already collapsed, moves to parent item |
| `Home` | Moves to the first item in the tree |
| `End` | Moves to the last visible item in the tree |
| `Enter` | Activates the current item's link (navigates) |
| `Space` | Toggles expand/collapse of the current parent item without navigating |
| `*` | Expands all sibling items at the same level as the current item |
| Character key | Type-ahead: moves to next item whose label starts with that character |

## 13. Accessibility
- Root element: `<ul role="tree" aria-label="{nav-label}" tabindex="0" aria-activedescendant="{activeId}">`.
- Each parent item: `<li role="treeitem" aria-expanded="{expanded}" aria-level="{n}" aria-setsize="{m}" aria-posinset="{i}" id="{id}">`.
- Each leaf item: `<li role="treeitem" aria-level="{n}" aria-setsize="{m}" aria-posinset="{i}" id="{id}">`.
- Current page item: `aria-current="page"` on the `role="treeitem"` element.
- Child group: `<ul role="group">`.
- Expand toggle is `aria-hidden="true"` because expand/collapse is signalled by
  `aria-expanded` on the `role="treeitem"` — the button is a pointer affordance only.
- Disabled items: `aria-disabled="true"`; skipped by Arrow key navigation.
- Loading state: `aria-busy="true"` on the parent item; spinner is `aria-hidden`.
- `nav-label` is the `aria-label` on the `<nav>` landmark and separately on the
  `role="tree"` list (they may differ if the page provides an external heading).

## 14. Form participation
N/A — `<mj-tree-nav>` is a navigation component, not a form control.

## 15. Internationalization & RTL
- `nav-label` is localizable; key `mj.treeNav.navLabel`.
- Loading state label: `mj.treeNav.loading`.
- Error label: `mj.treeNav.loadError`.
- Expand/collapse toggle labels (visual tooltip): `mj.treeNav.expand` /
  `mj.treeNav.collapse` with `{label}` interpolation.
- In RTL (`dir="rtl"`), indentation is applied to the inline-end (right);
  toggle icons flip horizontally; Arrow Right/Left keyboard behavior swaps
  (right collapses, left expands) to match reading direction convention.

## 16. Progressive enhancement / SSR
- Server renders a nested `<ul>`/`<li>`/`<a>` structure; all links are
  functional before JS loads.
- Expanded/collapsed state in SSR: collapsed child lists have `hidden` attribute;
  expanded ones do not.
- On upgrade: the component adds `role="tree"` / `role="treeitem"`, toggle
  buttons, `aria-activedescendant` focus management, and animation — without
  removing or cloning the link content.
- `current` attribute in server markup triggers `auto-expand` of ancestor nodes
  after upgrade.

## 17. Dependencies
- Section 6: Registry + base element helper, design-token stylesheet, focus
  utilities (`aria-activedescendant` helper), localization hook, data-source
  adapter (for lazy-loaded subtrees).
- `<mj-tree-nav-item>` — companion element for individual tree nodes.
- `<mj-spinner>` / `<mj-progress>` — used for lazy-load pending state.

## 18. Edge cases & error handling
- **No items slotted**: empty `<ul role="tree">` renders with the landmark;
  console warning emitted.
- **`current` matches no item**: no item receives `aria-current`; no ancestor
  expansion; console warning emitted.
- **Circular `src` references** (lazy-load): the component detects if a loaded
  subtree contains the same `id` as a parent and aborts with an error.
- **`persist-state` with item count change**: stale keys in `sessionStorage` are
  ignored; unknown items default to collapsed.
- **Very deep nesting (> 5 levels)**: supported but authors warned in docs;
  visual indentation may exceed container width — `--mj-tree-nav-indent` can be
  reduced.
- **Rapid expand/collapse**: animation is interruptible via CSS; state is
  committed immediately; the `transitionend` handler only updates
  `aria-hidden` / `hidden` on the child list.
- **Lazy-load network error**: toggle stays expanded; child list shows an
  inline retry link; `aria-busy` is cleared.

## 19. Acceptance criteria
- [ ] Renders `<nav aria-label>` wrapping `<ul role="tree">`.
- [ ] Each node: `role="treeitem"` with correct `aria-level`, `aria-setsize`, `aria-posinset`.
- [ ] Current page item has `aria-current="page"` and active styling.
- [ ] Parent nodes have `aria-expanded`; toggle button shows expand/collapse affordance.
- [ ] Arrow Down/Up navigates visible items via `aria-activedescendant`.
- [ ] Arrow Right expands collapsed parent; Arrow Left collapses expanded parent.
- [ ] Home/End jump to first/last visible item.
- [ ] Enter navigates; Space toggles expand without navigating.
- [ ] `*` expands all siblings.
- [ ] `auto-expand` expands ancestors of `current` on connect.
- [ ] `persist-state` restores expand/collapse across page loads.
- [ ] Lazy-load: spinner on expand; items populated on success; retry on error.
- [ ] RTL: indentation and arrow-key semantics reverse correctly.
- [ ] SSR: nested `<ul>`/`<a>` links functional before script loads.
- [ ] Automated axe checks pass with zero violations.

## 20. Open questions
- Should `<mj-tree-nav>` share its tree-management logic with `<mj-tree-selector>`
  (selection mode) via a common base class or utility module?
- Should lazy-loaded child items be fetched as JSON (requiring a schema) or as
  HTML fragments (simpler SSR integration)?
