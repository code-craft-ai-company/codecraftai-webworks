# Side Nav Spec

- **Tag:** `<mj-side-nav>`
- **Class / file:** `MjSideNav` / `mjsidenav.js`
- **Category:** Navigation components
- **Primary or Variant:** Primary
- **Synonyms covered:** Sidebar, Side navigation, Drawer navigation, Nav drawer
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-side-nav>` is a side navigation panel that supports three operational
modes: always-visible static rail, user-collapsible panel, and overlay drawer.
It houses hierarchical navigation links with optional section groups, icons, and
nested sub-navigation, providing the primary vertical navigation pattern for
application shells.

## 2. When to use / when not to use
**Use** for application-level vertical navigation that persists across pages or
sections. **Use `mode="overlay-drawer"`** for mobile or narrow viewport nav that
overlays content. **Do not use** for in-page content navigation — use `<mj-toc>`
or `<mj-tabs>`. **Do not use** for top-level site nav — use `<mj-app-bar>`.

## 3. Anatomy
- **Host element** — renders as `<nav aria-label>` landmark.
- **Header area** (`::part(header)`) — optional logo/title at the top; wraps the `header` slot.
- **Navigation list** (`::part(nav-list)`) — `<ul>` containing slotted nav items.
- **Section group** (`::part(group)`) — optional labelled group headers within the list.
- **Toggle button** (`::part(toggle)`) — collapse/expand control in `collapsible` mode.
- **Overlay backdrop** (`::part(backdrop)`) — dimming layer in `overlay-drawer` mode.
- **Footer area** (`::part(footer)`) — bottom-pinned slot for secondary links/avatar.

## 4. Variants & modes
| Mode | `mode` value | Behavior |
|------|-------------|----------|
| Static | `static` | Always visible; takes up layout space; no open/close control |
| Collapsible | `collapsible` | Toggleable panel; collapses to icon-only rail or fully hidden; state persisted |
| Overlay drawer | `overlay-drawer` | Slides in over content; backdrop behind; focus trapped while open |

| Variant | `variant` value | Behavior |
|---------|----------------|----------|
| Full | `full` | Shows icons + labels |
| Rail | `rail` | Icons only; labels in tooltips; width `--mj-side-nav-rail-width` |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `mode` | string | `"static"` | Yes | Operational mode: `static` \| `collapsible` \| `overlay-drawer` |
| `variant` | string | `"full"` | Yes | Display variant: `full` \| `rail` |
| `open` | boolean | `false` | Yes | Whether the nav is expanded (collapsible) or visible (overlay-drawer) |
| `edge` | string | `"start"` | Yes | Which edge the drawer slides from: `start` \| `end` |
| `nav-label` | string | `"Navigation"` | Yes | `aria-label` for the `<nav>` landmark |
| `persist-state` | boolean | `true` | Yes | Saves `open` state to `localStorage` in `collapsible` mode |
| `persist-key` | string | `"mj-side-nav"` | Yes | `localStorage` key used for state persistence |
| `width` | string | `""` | Yes | Inline override for nav width; takes precedence over CSS custom property |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `activeItem` | `Element \| null` | The currently active nav item element (has `aria-current="page"`) |
| `items` | `Element[]` | All focusable nav item elements in DOM order |

## 7. Slots
| Slot | Description |
|------|-------------|
| `header` | Logo, app name, or top branding placed above the nav list |
| _(default)_ | `<mj-side-nav-item>` elements or `<mj-side-nav-group>` elements forming the nav tree |
| `footer` | Bottom-pinned content: user profile, settings link, sign-out |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-side-nav-open` | `{ mode: string }` | Yes | Yes | Fires when the nav opens (overlay-drawer) or expands (collapsible) |
| `mj-side-nav-close` | `{ mode: string }` | Yes | Yes | Fires when the nav closes or collapses |
| `mj-side-nav-navigate` | `{ item: Element, href: string }` | Yes | Yes | Fires when a nav item link is activated; cancel to intercept routing |

## 9. CSS parts & custom properties
**Parts**
- `::part(root)` — inner layout wrapper
- `::part(header)` — header slot container
- `::part(nav-list)` — the `<ul>` nav list
- `::part(toggle)` — collapse/expand button
- `::part(backdrop)` — overlay backdrop element
- `::part(footer)` — footer slot container

**Custom properties**
| Property | Default | Description |
|----------|---------|-------------|
| `--mj-side-nav-width` | `240px` | Expanded width |
| `--mj-side-nav-rail-width` | `64px` | Rail-only (icon) width |
| `--mj-side-nav-bg` | `var(--mj-color-surface-nav)` | Background color |
| `--mj-side-nav-z-index` | `var(--mj-z-index-drawer)` | Stack order in overlay mode |
| `--mj-side-nav-transition-duration` | `var(--mj-motion-duration-medium)` | Slide animation duration |
| `--mj-side-nav-item-height` | `44px` | Block size of each nav item |
| `--mj-side-nav-indent` | `var(--mj-spacing-5)` | Per-level indent for nested items |

## 10. States
- **default** — static; always visible; full-width.
- **open** — collapsible expanded or overlay-drawer visible; `open` attribute present.
- **collapsed** — collapsible in rail or hidden state; `open` absent.
- **focus-visible** — individual nav items show focus rings.
- **active** — the item matching the current URL has `aria-current="page"` and active token styling.
- **hover** — nav items show hover background.
- **disabled** — individual nav items can be disabled via `aria-disabled`.
- **overlay-open** — backdrop visible; page content `inert`.

## 11. Behavior & interactions
- In `overlay-drawer` mode, opening the nav slides the panel in from `edge`
  (default: `start`). The Section 6 focus-trap utility traps focus within the
  panel. Clicking the backdrop or pressing Escape closes the drawer and returns
  focus to the element that triggered opening.
- In `collapsible` mode, the toggle button switches between expanded and
  rail/hidden states. If `persist-state` is true, the state is saved to
  `localStorage` under `persist-key` and restored on next page load.
- When collapsing to `rail` variant, icon-only items show a tooltip (via
  `<mj-tooltip>`) with the link label.
- Nested sub-navigation groups use a disclosure pattern: clicking a group
  header expands/collapses the child list with `aria-expanded` on the group
  trigger.
- The nav uses `ResizeObserver` on the host to auto-switch from `static` to
  `overlay-drawer` when the viewport width falls below
  `--mj-side-nav-collapse-breakpoint`.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` | Moves focus through nav items and interactive controls in DOM order |
| `Enter` / `Space` | Activates focused nav link or toggles a group disclosure |
| `Escape` | Closes overlay-drawer; returns focus to opener |
| `Arrow Down` | Moves focus to next nav item (roving tabindex within the list) |
| `Arrow Up` | Moves focus to previous nav item |
| `Home` | Moves focus to first nav item |
| `End` | Moves focus to last nav item |
| `Arrow Right` | Expands a collapsed group; moves into child items |
| `Arrow Left` | Collapses an expanded group; moves to parent item |

## 13. Accessibility
- Host renders as `<nav aria-label="Navigation">` (value overridable via `nav-label`).
- The current-page item has `aria-current="page"`; set either by attribute on
  the slotted `<mj-side-nav-item>` or by the nav matching `href` to `location.pathname`.
- Group headers use `role="button"` with `aria-expanded` and `aria-controls`
  referencing the child list.
- In overlay-drawer mode, the backdrop has `aria-hidden="true"`; the rest of
  the page is made `inert`; the close/toggle button is the first focusable
  element inside the panel.
- Toggle button in collapsible mode has an accessible name ("Collapse navigation"
  / "Expand navigation") via the localization hook.
- Rail variant: icon-only items must have `aria-label` matching the link text;
  tooltip provides the visible label.

## 14. Form participation
N/A — `<mj-side-nav>` is a navigation landmark, not a form control.

## 15. Internationalization & RTL
- `nav-label` is localizable; localization key `mj.sideNav.navLabel`.
- Toggle button labels: `mj.sideNav.collapse` / `mj.sideNav.expand`.
- Close button (overlay): `mj.sideNav.close`.
- In RTL, `edge="start"` becomes the inline-end (right) side; `edge="end"` becomes inline-start (left); slide animation direction reverses.
- Item indent direction reverses in RTL.

## 16. Progressive enhancement / SSR
- Server markup: `<mj-side-nav><a href="...">...</a></mj-side-nav>` renders as
  a visible list of links without any JS.
- On upgrade, the component wraps links in Shadow DOM structure, adds ARIA,
  group disclosure, and mode behavior without removing the links.
- In `collapsible` mode, the server can emit `open` in the markup for the
  default-expanded state; the component reads and respects it before restoring
  persisted state.

## 17. Dependencies
- Section 6: Registry + base element helper, design-token stylesheet, focus-trap
  utility, localization hook.
- `<mj-side-nav-item>` — companion element for individual nav entries (defined
  in its own spec; composed here).
- `<mj-side-nav-group>` — companion element for labelled nav groups.
- `<mj-tooltip>` — used for rail-mode icon label tooltips.

## 18. Edge cases & error handling
- **No items slotted**: nav renders as empty landmark; no error.
- **`mode="overlay-drawer"` without a programmatic opener**: the `open` attribute
  can be toggled by the host page or by `<mj-app-bar>`; the component does not
  render its own opener button in this mode.
- **`persist-state` with conflicting `open` attribute**: persisted value wins;
  the `open` attribute in markup is used only on first load before storage is
  read.
- **Deep nesting (>3 levels)**: supported structurally; visual indent may
  overflow narrow rail — authors are warned in docs to limit nesting to 2 levels.
- **Rapid open/close**: animation is interruptible; the component uses
  `transitionend` to finalize state rather than a fixed timeout.

## 19. Acceptance criteria
- [ ] Renders `<nav aria-label>` landmark in all modes.
- [ ] `static` mode: nav always visible; no toggle button.
- [ ] `collapsible` mode: toggle expands/collapses; `open` attribute reflects state; `mj-side-nav-open` / `mj-side-nav-close` fire.
- [ ] `collapsible` + `persist-state`: state persists across page loads in localStorage.
- [ ] `overlay-drawer` mode: backdrop visible when open; focus trapped; Escape closes and restores focus.
- [ ] Current-page item has `aria-current="page"`.
- [ ] Group items toggle with `aria-expanded`; child list shows/hides.
- [ ] Rail variant: icon-only; tooltip shows label on hover/focus.
- [ ] Keyboard: Arrow Up/Down navigate items; Arrow Right/Left handle groups.
- [ ] RTL: slide direction and indent reverse.
- [ ] SSR: slotted links usable before script loads.
- [ ] Automated axe checks pass with zero violations.

## 20. Open questions
- Should `<mj-side-nav>` auto-detect the current page by comparing item `href`
  values against `location.pathname`, or must the author explicitly set
  `aria-current="page"` on the active item?
- Should the collapsible rail variant be a separate `variant` value or a
  separate `mode`?
