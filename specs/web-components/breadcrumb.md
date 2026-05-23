# Breadcrumb Spec

- **Tag:** `<mj-breadcrumb>`
- **Class / file:** `MjBreadcrumb` / `mjbreadcrumb.js`
- **Category:** Navigation components
- **Primary or Variant:** Primary
- **Synonyms covered:** Breadcrumb, Breadcrumb trail, Hierarchy trail
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-breadcrumb>` renders an ordered hierarchy trail showing the current page's
location within the site or application structure. It provides a labelled `<nav>`
landmark containing an `<ol>` of links, with the last item marked as the current
page using `aria-current="page"`. It handles overflow of long trails via
collapsing intermediate items behind an expand control.

## 2. When to use / when not to use
**Use** when content is organized in a hierarchy of three or more levels and
users benefit from knowing their location and being able to navigate upward.
**Do not use** for flat navigation or when there is only one level above the
current page — a single back link is sufficient in that case. Do not use as a
replacement for primary navigation.

## 3. Anatomy
- **Host / `<nav>`** — `<nav aria-label="Breadcrumb">` landmark.
- **Ordered list** (`::part(list)`) — `<ol>` containing breadcrumb items.
- **Item** (`::part(item)`) — each `<li>` wrapping a link or current-page label.
- **Separator** (`::part(separator)`) — visual glyph between items (decorative, `aria-hidden`).
- **Ellipsis item** (`::part(ellipsis)`) — collapsed items replaced by a `…` expand button.
- **Expand button** (`::part(expand-btn)`) — button that reveals collapsed intermediate items.

## 4. Variants & modes
| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Default | _(none)_ | Full trail; no collapsing |
| Collapsing | `max-visible` | Shows first + last N items; hides middle items behind ellipsis expand button |
| Custom separator | `separator` | Overrides the default `/` separator character or SVG |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `nav-label` | string | `"Breadcrumb"` | Yes | `aria-label` for the `<nav>` landmark |
| `separator` | string | `"/"` | Yes | Separator glyph or text rendered between items |
| `max-visible` | number | `0` | Yes | Maximum items to show before collapsing; `0` = no limit |
| `always-show-first` | boolean | `true` | Yes | When collapsing, the first item (root) is always visible |
| `always-show-last` | number | `1` | Yes | Number of trailing items always visible when collapsing |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `items` | `Element[]` | Read-only ordered array of slotted breadcrumb item elements |
| `collapsed` | boolean | Whether intermediate items are currently collapsed; settable to toggle programmatically |

## 7. Slots
| Slot | Description |
|------|-------------|
| _(default)_ | `<mj-breadcrumb-item>` elements in hierarchy order (first = root, last = current page) |
| `separator` | Custom separator content; overrides the `separator` attribute |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-breadcrumb-expand` | `{}` | Yes | Yes | Fires when the ellipsis expand button is activated; cancel to suppress expansion |
| `mj-breadcrumb-navigate` | `{ item: Element, href: string, index: number }` | Yes | Yes | Fires when a breadcrumb link is clicked; cancel to intercept routing |

## 9. CSS parts & custom properties
**Parts**
- `::part(list)` — the `<ol>` element
- `::part(item)` — each `<li>` element
- `::part(separator)` — separator wrapper span
- `::part(ellipsis)` — the collapsed-items placeholder `<li>`
- `::part(expand-btn)` — the expand button within the ellipsis item
- `::part(current)` — the `<li>` and its content for the current-page item

**Custom properties**
| Property | Default | Description |
|----------|---------|-------------|
| `--mj-breadcrumb-separator-color` | `var(--mj-color-text-muted)` | Separator text/icon color |
| `--mj-breadcrumb-separator-gap` | `var(--mj-spacing-2)` | Space on each side of the separator |
| `--mj-breadcrumb-font-size` | `var(--mj-font-size-sm)` | Font size for all items |
| `--mj-breadcrumb-current-color` | `var(--mj-color-text-default)` | Text color of the current-page item |
| `--mj-breadcrumb-link-color` | `var(--mj-color-link)` | Link color for ancestor items |

## 10. States
- **default** — all items visible; last item is current page (not a link).
- **collapsed** — intermediate items hidden; ellipsis + expand button visible.
- **expanded** — previously collapsed items revealed after expand activation.
- **focus-visible** — link items and expand button show focus rings.
- **hover** — link items show hover color transition.

## 11. Behavior & interactions
- The last slotted `<mj-breadcrumb-item>` is automatically treated as the
  current page: it is rendered as non-link text with `aria-current="page"`.
  Authors may set `current` on an item explicitly to override this.
- Separator elements are injected between items by the component; authors do not
  place them in markup. Separators are `aria-hidden="true"` spans.
- When `max-visible` is set and the item count exceeds it, the component
  collapses items between the first `always-show-first` items and the last
  `always-show-last` items, replacing them with an ellipsis `<button>`.
- Activating the expand button sets `collapsed = false`, renders all items, and
  moves focus to the first previously-hidden item.
- Collapsing is one-shot per page load: once expanded, the trail stays expanded.
- Items are re-evaluated on slot change (via `MutationObserver` on the default
  slot) to handle dynamic breadcrumb updates.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` | Moves focus through ancestor links then the expand button (if visible) |
| `Enter` | Activates the focused link or the expand button |
| `Shift+Tab` | Reverse focus order through the trail |

## 13. Accessibility
- The landmark is `<nav aria-label="Breadcrumb">` (WAI-ARIA Authoring Practices
  Breadcrumb pattern).
- The list is `<ol>` (ordered) to convey hierarchy.
- The current-page item has `aria-current="page"` and is not an interactive link.
- Separators are `aria-hidden="true"` to prevent them being read as content.
- The expand button has an accessible name via the localization key
  `mj.breadcrumb.expand` (default: "Show hidden breadcrumbs"); when expanded,
  the button is removed from the DOM.
- When items are collapsed, the hidden count is announced on the expand button:
  e.g., "Show 3 hidden breadcrumbs".

## 14. Form participation
N/A — `<mj-breadcrumb>` is a navigation component.

## 15. Internationalization & RTL
- `nav-label` is localizable; key `mj.breadcrumb.navLabel`.
- Expand button label: `mj.breadcrumb.expand` with a `{count}` interpolation.
- The default `/` separator is appropriate for LTR. In RTL contexts, the
  separator renders with reversed visual flow (CSS `direction: rtl` on the list
  is sufficient; a `\` separator is not automatically substituted — authors should
  supply a directionally neutral separator like `›` via the `separator` attribute).
- The `separator` slot supports SVG icons that auto-flip with `dir`.

## 16. Progressive enhancement / SSR
- Server renders:
  ```html
  <mj-breadcrumb>
    <mj-breadcrumb-item href="/"><a href="/">Home</a></mj-breadcrumb-item>
    <mj-breadcrumb-item href="/docs"><a href="/docs">Docs</a></mj-breadcrumb-item>
    <mj-breadcrumb-item>Components</mj-breadcrumb-item>
  </mj-breadcrumb>
  ```
- Before upgrade: links are functional; last item is plain text; no ARIA or
  landmark semantics.
- On upgrade: `<nav>` landmark is added, `<ol>` wraps items, separators are
  injected, `aria-current="page"` applied to last item.

## 17. Dependencies
- Section 6: Registry + base element helper, design-token stylesheet,
  localization hook.
- `<mj-breadcrumb-item>` — companion element for individual crumb entries.
- No other `mj-*` components required.

## 18. Edge cases & error handling
- **Single item**: the sole item is treated as current-page with no links; no
  separator is rendered. The landmark still renders for consistency.
- **Zero items**: empty `<nav>` is rendered; a console warning is emitted.
- **`max-visible` larger than item count**: collapse logic is skipped; full trail shown.
- **Dynamic items added/removed**: `MutationObserver` on the slot triggers
  re-render of the list, separators, and current-page annotation.
- **Very long item label**: item text truncates with ellipsis and `title` tooltip
  at `--mj-breadcrumb-item-max-width` (default: `200px`).
- **`current` set on a non-last item**: the explicitly marked item receives
  `aria-current="page"`; the last item does not automatically receive it.

## 19. Acceptance criteria
- [ ] Renders `<nav aria-label="Breadcrumb">` with an `<ol>`.
- [ ] Last item (or item with `current`) has `aria-current="page"` and is not a link.
- [ ] Separators are `aria-hidden` and rendered between items automatically.
- [ ] `max-visible` collapses intermediate items behind expand button.
- [ ] Expand button announces hidden count; activating it reveals all items and moves focus.
- [ ] `mj-breadcrumb-navigate` fires and is cancelable on link click.
- [ ] Dynamic item addition/removal via slot updates the rendered list.
- [ ] RTL: list order and separator direction correct.
- [ ] SSR: links functional before script loads.
- [ ] Automated axe checks pass with zero violations.

## 20. Open questions
- Should collapsed items re-collapse when navigating back, or always stay
  expanded once opened?
- Should the current item (last crumb) support an optional dropdown to show
  sibling pages at the same level?
