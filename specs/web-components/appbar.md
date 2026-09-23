# App Bar Spec

- **Tag:** `<mj-app-bar>`
- **Class / file:** `MjAppBar` / `mjappbar.js`
- **Category:** Navigation components
- **Primary or Variant:** Primary
- **Synonyms covered:** Navigation bar, Top app bar, Header, App header, Top nav
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-app-bar>` is the primary top-of-page navigation and branding bar. It
provides a `<header>` landmark containing a logo/brand slot, a primary nav slot,
and an actions slot, while handling responsive collapse to a hamburger menu on
narrow viewports. It is the canonical implementation for the Top app bar, Header,
and Navigation bar patterns.

## 2. When to use / when not to use
**Use** for the single top-level navigation bar that appears on every page.
**Do not use** for in-page section navigation — use `<mj-tabs>` or `<mj-toc>`.
**Do not use** as a secondary sidebar navigation — use `<mj-side-nav>`.
When the application requires both a top bar and a side nav, compose them in
`<mj-app-shell>`.

## 3. Anatomy
- **Host / `<header>`** — landmark element with `role="banner"`.
- **Brand area** (`::part(brand)`) — logo + app name; wraps the `brand` slot.
- **Nav area** (`::part(nav)`) — `<nav aria-label>` wrapping the `navigation` slot; hidden at breakpoint and moved into the mobile drawer.
- **Actions area** (`::part(actions)`) — trailing slot for icon buttons, avatars, notifications.
- **Mobile toggle** (`::part(toggle)`) — hamburger button; visible below `--mj-app-bar-collapse-breakpoint`.
- **Mobile drawer** (`::part(drawer)`) — collapsed nav content rendered in an overlay `<mj-side-nav mode="overlay-drawer">`.
- **Skip-link target** — the bar renders with `id` hookable by `<mj-skip-link>`.

## 4. Variants & modes
| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Default | _(none)_ | Static position; scrolls with the page |
| Sticky | `sticky` | `position: sticky; top: 0`; stays visible on scroll |
| Floating | `variant="floating"` | Elevated card style that lifts above content on scroll |
| Compact | `compact` | Reduced block size; smaller logo/text; used in dense UIs |
| Transparent | `transparent` | No background on load; gains background on scroll (hero overlap) |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `sticky` | boolean | `false` | Yes | Applies sticky positioning |
| `variant` | string | `"default"` | Yes | Visual style: `default` \| `floating` \| `compact` \| `transparent` |
| `transparent` | boolean | `false` | Yes | Starts with no background; gains background after `scroll-threshold` px scrolled |
| `scroll-threshold` | number | `16` | Yes | Pixels scrolled before background appears when `transparent` |
| `nav-label` | string | `"Main"` | Yes | `aria-label` for the inner `<nav>` landmark |
| `open` | boolean | `false` | Yes | Whether the mobile drawer is open; reflected; settable by script |
| `collapse-breakpoint` | string | `"md"` | Yes | Token breakpoint name (`sm`/`md`/`lg`) at which nav collapses |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `scrolled` | boolean | Read-only; `true` when page scroll exceeds `scroll-threshold`; reflected as attribute for CSS targeting |
| `drawerElement` | `Element \| null` | Reference to the internal mobile drawer instance |

## 7. Slots
| Slot | Description |
|------|-------------|
| `brand` | Logo image, wordmark, or app name link; renders in the leading brand area |
| `navigation` | `<mj-link>` elements or nav lists for the primary nav; collapsed into drawer on narrow viewports |
| `actions` | Trailing controls: icon buttons, avatar, notification badge |
| `mobile-navigation` | Optional override slot for mobile drawer content; falls back to mirroring `navigation` |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-app-bar-open` | `{}` | Yes | Yes | Fires when the mobile drawer opens; cancel to prevent |
| `mj-app-bar-close` | `{}` | Yes | Yes | Fires when the mobile drawer closes; cancel to prevent |
| `mj-app-bar-scroll` | `{ scrolled: boolean, scrollY: number }` | Yes | No | Fires when `scrolled` state changes |

## 9. CSS parts & custom properties
**Parts**
- `::part(root)` — inner layout wrapper
- `::part(brand)` — brand/logo container
- `::part(nav)` — desktop nav `<nav>` element
- `::part(actions)` — trailing actions container
- `::part(toggle)` — mobile hamburger button
- `::part(drawer)` — mobile overlay drawer

**Custom properties**
| Property | Default | Description |
|----------|---------|-------------|
| `--mj-app-bar-height` | `56px` | Block size of the bar |
| `--mj-app-bar-bg` | `var(--mj-color-surface-nav)` | Background color |
| `--mj-app-bar-bg-scrolled` | `var(--mj-color-surface-nav)` | Background when scrolled (relevant for `transparent`) |
| `--mj-app-bar-elevation` | `var(--mj-elevation-2)` | Box shadow |
| `--mj-app-bar-z-index` | `var(--mj-z-index-app-bar)` | Stack order |
| `--mj-app-bar-padding-inline` | `var(--mj-spacing-5)` | Horizontal padding |
| `--mj-app-bar-collapse-breakpoint` | `768px` | Pixel width below which nav collapses |

## 10. States
- **default** — static bar at top of document flow.
- **scrolled** — `scrolled` attribute present; background appears when `transparent`; elevation token applied.
- **open** — mobile drawer visible; toggle button has `aria-expanded="true"`.
- **sticky** — bar remains at top of viewport during scroll.
- **focus-visible** — all interactive children show focus rings; bar itself is not focusable.

## 11. Behavior & interactions
- On viewports narrower than `--mj-app-bar-collapse-breakpoint`, the
  `navigation` slot content is hidden and the mobile toggle button is shown.
- Activating the toggle opens an `<mj-side-nav mode="overlay-drawer">` that
  contains either the `mobile-navigation` slot or a clone of the `navigation`
  slot content.
- The overlay drawer traps focus per the `<mj-side-nav>` spec; closing it
  returns focus to the toggle button.
- With nothing in the `navigation` slot the bar renders no navigation
  landmark (an empty `<nav>` would still be announced), and with nothing in
  either the `navigation` or the `mobile-navigation` slot it renders no mobile
  toggle, drawer, or backdrop -- a bar that only carries brand and actions
  never offers a button that opens an empty drawer.
- When `transparent` is set, a `scroll` listener (passive, using
  `IntersectionObserver` on a sentinel element to avoid scroll-handler jank)
  toggles the `scrolled` attribute.
- The bar uses `ResizeObserver` to re-evaluate the collapse state without media
  query polling.
- In `sticky` mode, the bar occupies space in the document flow (not `fixed`),
  ensuring content below is not obscured without compensating top-padding.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` | Moves through brand, nav links, action controls in DOM order |
| `Enter` / `Space` | Activates the focused interactive element |
| `Escape` | Closes the mobile drawer when open; returns focus to toggle |
| `Tab` (in open drawer) | Cycles focus within the drawer (trap active) |

## 13. Accessibility
- The host renders as `<header role="banner">`; only one `<header>` with
  `role="banner"` should exist per page.
- The desktop nav is `<nav aria-label="Main">` (overridable via `nav-label`).
- The mobile toggle has `aria-expanded` reflecting `open`, `aria-controls`
  pointing to the drawer's `id`, and an accessible name ("Open navigation"
  / "Close navigation") managed by the localization hook.
- Current page link within the nav must carry `aria-current="page"` — this is
  the responsibility of the slotted `<mj-link>` elements, not the bar itself.
- When the mobile drawer is open, the rest of the page is made `inert` via the
  Section 6 focus-trap utility.
- The bar itself does not receive focus; skip-link target IDs on the main
  content landmark are provided by the page, not the bar.

## 14. Form participation
N/A — `<mj-app-bar>` is a navigation landmark, not a form control.

## 15. Internationalization & RTL
- `nav-label` attribute is localizable; the component also reads from the
  localization hook key `mj.appBar.navLabel` as a fallback.
- Toggle button labels: `mj.appBar.openNav` / `mj.appBar.closeNav`.
- In RTL (`dir="rtl"`), brand area moves to the inline-end (right) and actions
  to the inline-start (left); achieved via `flex-direction: row-reverse` in the
  RTL style block.

## 16. Progressive enhancement / SSR
- Server renders `<mj-app-bar>` with a `<header>` wrapping slotted landmarks.
- Before upgrade, slotted links are visible and navigable as a standard header.
- On upgrade, the component adds the collapse logic, mobile toggle, and drawer
  without removing or re-rendering the nav links.
- The `sticky` attribute can be present in server markup; a small CSS-only rule
  in the element's adoptable stylesheet applies `position: sticky` immediately.

## 17. Dependencies
- Section 6: Registry + base element helper, design-token stylesheet, overlay /
  focus-trap utility, localization hook.
- `<mj-side-nav mode="overlay-drawer">` — used for the mobile nav drawer.
- `<mj-link>` — expected in the navigation slot for consistent link styling.

## 18. Edge cases & error handling
- **No `navigation` slot content**: toggle button is hidden; bar shows only brand
  and actions.
- **Very long brand name**: brand area truncates with ellipsis at 50% of bar width.
- **Many action items**: actions slot wraps; component does not auto-hide overflow
  — authors should use an overflow `<mj-menu>` for dense action sets.
- **Nested `<header>` landmark**: if a second `<mj-app-bar>` is mounted (e.g.,
  inside a story), it uses `role="navigation"` for the inner nav only to avoid
  duplicate `banner` landmarks; a console warning is emitted.
- **`scroll-threshold` on a non-scrolling page**: the `scrolled` attribute never
  sets; no error thrown.

## 19. Acceptance criteria
- [ ] Renders `<header role="banner">` containing `<nav aria-label>`.
- [ ] Desktop: nav slot content is visible; toggle button hidden.
- [ ] Mobile: nav slot hidden; toggle visible; toggle opens/closes the drawer.
- [ ] `open` attribute toggles the drawer; `mj-app-bar-open` / `mj-app-bar-close` events fire.
- [ ] Sticky mode: bar remains at top of viewport on scroll.
- [ ] Transparent mode: background absent initially; appears after `scroll-threshold` px.
- [ ] `mj-app-bar-scroll` event fires with correct payload on scroll state change.
- [ ] Toggle has `aria-expanded` / `aria-controls` reflecting drawer state.
- [ ] Drawer traps focus; Escape closes it and restores focus to toggle.
- [ ] RTL: layout reverses; brand on right, actions on left.
- [ ] SSR fallback: header landmark and nav links functional before script loads.
- [ ] Automated axe checks pass with zero violations.

## 20. Open questions
- Should `<mj-app-bar>` own a second-level sub-nav slot (mega menu row), or
  should mega menus be composed via the `actions` slot and `<mj-menu>`?
- Should the mobile drawer be an internal shadow element or a separately
  slotted `<mj-side-nav>` in light DOM for flexibility?
