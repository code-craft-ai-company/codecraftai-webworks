# Table of Contents Spec

- **Tag:** `<mj-toc>`
- **Class / file:** `MjToc` / `mjtoc.js`
- **Category:** Navigation components
- **Primary or Variant:** Primary
- **Synonyms covered:** Table of contents, TOC, Anchor links, In-page navigation, Scroll spy nav
- **Phase:** P2
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-toc>` is an in-page section navigation component that renders a list of
anchor links derived from headings within a target content region. It uses
`IntersectionObserver` to highlight the link for the section currently in the
viewport (scroll-spy) and scrolls the target into view smoothly when a link is
activated, respecting `prefers-reduced-motion`.

## 2. When to use / when not to use
**Use** for long-form documentation, articles, or settings pages where users need
quick access to named sections within a single page. **Do not use** for cross-page
navigation — use `<mj-side-nav>` or `<mj-app-bar>`. **Do not use** for tabbed
content — use `<mj-tabs>`. **Do not use** when the content has fewer than three
sections; a brief page does not benefit from a TOC.

## 3. Anatomy
- **Host / `<nav>`** — `<nav aria-label="On this page">` landmark.
- **Title** (`::part(title)`) — optional visible heading above the link list (e.g., "On this page").
- **Link list** (`::part(list)`) — `<ul>` of anchor-link items.
- **Link item** (`::part(item)`) — each `<li>` containing the anchor.
- **Anchor** (`::part(anchor)`) — `<a href="#sectionId">` linking to the target heading.
- **Nested list** (`::part(nested-list)`) — `<ul>` for sub-section links when `depth > 1`.

## 4. Variants & modes
| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Auto-generated | `target` | Scans headings in the referenced element; builds list dynamically |
| Manual | _(no `target`)_ | Uses slotted `<a>` elements directly; no auto-scan |
| Sticky | `sticky` | `position: sticky` so the TOC stays in view during scroll |
| Flat | `depth="1"` | Only top-level headings (H2); no nesting |
| Nested | `depth="2"` or `"3"` | Includes sub-headings; visually indented |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `target` | string | `""` | Yes | CSS selector or `id` of the content element whose headings are scanned |
| `depth` | number | `2` | Yes | Heading depth to include: `1` = H2 only, `2` = H2+H3, `3` = H2–H4 |
| `heading-selector` | string | `"h2,h3,h4"` | Yes | Custom selector for scannable headings (overrides `depth`) |
| `sticky` | boolean | `false` | Yes | Makes the TOC `position: sticky` with `top: var(--mj-toc-sticky-top)` |
| `scroll-behavior` | string | `"smooth"` | Yes | `smooth` \| `instant`; overrides per-link scroll behavior |
| `nav-label` | string | `"On this page"` | Yes | `aria-label` for the `<nav>` landmark |
| `title` | string | `""` | Yes | Visible heading text shown above the link list; empty hides the title element |
| `offset` | number | `0` | Yes | Scroll offset in pixels to account for sticky headers when computing active section |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `activeId` | string | Read-only; the `id` of the currently active section heading |
| `sections` | `{ id: string, text: string, level: number, element: Element }[]` | Read-only list of detected sections |

## 7. Slots
| Slot | Description |
|------|-------------|
| _(default)_ | Manual `<a href="#id">` elements; used when `target` is not set |
| `title` | Custom title content above the list; overrides the `title` attribute rendered heading |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-toc-active-change` | `{ id: string, element: Element, previousId: string }` | Yes | No | Fires when scroll-spy changes the active section |
| `mj-toc-navigate` | `{ id: string, element: Element, originalEvent: MouseEvent }` | Yes | Yes | Fires when a TOC link is clicked; cancel to prevent scroll and handle manually |

## 9. CSS parts & custom properties
**Parts**
- `::part(root)` — inner layout wrapper
- `::part(title)` — the visible title heading element
- `::part(list)` — the top-level `<ul>`
- `::part(item)` — each `<li>` item
- `::part(anchor)` — each `<a>` link
- `::part(nested-list)` — nested `<ul>` for sub-sections

**Custom properties**
| Property | Default | Description |
|----------|---------|-------------|
| `--mj-toc-sticky-top` | `var(--mj-app-bar-height, 0px)` | Offset from top when sticky |
| `--mj-toc-width` | `220px` | Preferred width of the TOC panel |
| `--mj-toc-font-size` | `var(--mj-font-size-sm)` | Font size for TOC links |
| `--mj-toc-active-color` | `var(--mj-color-primary)` | Text color of the active link |
| `--mj-toc-active-border` | `2px solid var(--mj-color-primary)` | Left/start border on the active link |
| `--mj-toc-indent` | `var(--mj-spacing-4)` | Per-level indentation for nested items |
| `--mj-toc-link-color` | `var(--mj-color-text-muted)` | Default link color |
| `--mj-toc-link-color-hover` | `var(--mj-color-text-default)` | Link hover color |

## 10. States
- **default** — all links at rest; no active link if nothing is scrolled into view.
- **active** — the link for the in-viewport section has `aria-current="true"` and active styling.
- **hover** — link shows hover color token.
- **focus-visible** — focused link shows focus ring.
- **sticky** — `position: sticky; top: --mj-toc-sticky-top` applied; scrolls with the sidebar.
- **empty** — `target` element has no matching headings; TOC renders with the title only and a "No sections found" notice.

## 11. Behavior & interactions
- When `target` is set, the component runs a `MutationObserver` on the target
  element to detect heading changes (useful for dynamically loaded content) and
  rebuilds the link list when headings are added or removed.
- An `IntersectionObserver` watches all detected heading elements with a root
  margin compensating for `offset` and any sticky app bar. When a heading enters
  the top region of the viewport, its corresponding TOC link becomes active.
- Multiple headings can intersect simultaneously; the component selects the one
  with the highest scroll position (topmost visible heading) as active.
- Clicking a TOC link scrolls the target heading into view using
  `scrollIntoView({ behavior: scroll-behavior })`. If `prefers-reduced-motion`
  is active, `scroll-behavior` is forced to `instant` regardless of the attribute.
- After click-scroll, focus moves to the target heading element (which must have
  `tabindex="-1"` if not natively focusable) for screen-reader announcement.
- The `activeId` property updates reactively as the user scrolls; no debounce
  is applied to the `mj-toc-active-change` event, but `IntersectionObserver`
  inherently batches updates per frame.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` | Moves focus through TOC anchor links in DOM order |
| `Enter` | Activates the focused anchor; scrolls to the target heading; fires `mj-toc-navigate` |
| `Shift+Tab` | Reverse focus through links |

## 13. Accessibility
- The landmark is `<nav aria-label="On this page">` (overridable via `nav-label`).
- The active section link has `aria-current="true"` (not `"page"` — it is a
  within-page section, not a different page).
- After scroll-navigation, focus moves to the target heading (via `focus()` on
  the heading with `tabindex="-1"`), so screen readers announce the section.
- The TOC title, if rendered, is a `<p>` or `<span>` with appropriate styling
  (not a heading `<h2>` to avoid disrupting the document outline).
- Nested lists are properly nested `<ul>` within `<li>`, preserving list
  semantics for screen readers.
- When the target element has no headings, a live region politely announces
  "No sections found" so screen readers are informed.

## 14. Form participation
N/A — `<mj-toc>` is a navigation component.

## 15. Internationalization & RTL
- `nav-label` localizable; key `mj.toc.navLabel`.
- `title` text localizable; key `mj.toc.title` (default: "On this page").
- Empty state message: `mj.toc.empty`.
- In RTL, the active indicator border moves from the inline-start (left in LTR)
  to the inline-end (right in RTL); indentation direction reverses.
- TOC link text is derived from heading `textContent`; locale-specific
  characters are preserved as-is.

## 16. Progressive enhancement / SSR
- Server can render `<mj-toc>` with explicit `<a>` elements in the default slot
  (manual mode); these are navigable before JS loads.
- When `target` is used, server markup may omit the link list; after upgrade,
  the component scans and generates the list. There is a brief FOUC window;
  mitigate by server-rendering a skeleton list that the component replaces.
- The `sticky` attribute can be in server markup; a CSS-only rule applies
  `position: sticky` immediately on parse.

## 17. Dependencies
- Section 6: Registry + base element helper, design-token stylesheet,
  localization hook.
- Platform APIs: `IntersectionObserver`, `MutationObserver`, `scrollIntoView`.
- No other `mj-*` components required.

## 18. Edge cases & error handling
- **`target` selector matches nothing**: component logs a console warning; renders
  an empty `<nav>` landmark with no links.
- **Heading has no `id`**: the component auto-generates a slug `id` from the
  heading's `textContent` and sets it on the heading element; a console info is
  logged.
- **Duplicate heading text**: auto-generated slugs get a numeric suffix
  (`-2`, `-3`) to stay unique.
- **Very long heading text**: TOC link truncates with ellipsis at
  `--mj-toc-link-max-width`; full text in `title` tooltip.
- **`depth` exceeds available heading levels**: no error; only matching headings
  are included.
- **Dynamic content changes (headings added/removed via JS)**: `MutationObserver`
  triggers rebuild; active link is revalidated.

## 19. Acceptance criteria
- [ ] Renders `<nav aria-label="On this page">` with `<ul>` of anchor links.
- [ ] `target` mode: scans headings and builds link list automatically.
- [ ] Active link has `aria-current="true"` and active styling as page scrolls.
- [ ] Click scroll: heading scrolls into view; focus moves to heading.
- [ ] `prefers-reduced-motion`: scroll behavior forced to `instant`.
- [ ] `depth` controls which heading levels are included.
- [ ] Nested sub-sections indented in a nested `<ul>`.
- [ ] `sticky` mode: TOC stays visible during scroll.
- [ ] `mj-toc-navigate` fires and is cancelable.
- [ ] `mj-toc-active-change` fires with correct `id` on scroll.
- [ ] Headings without `id` get auto-generated slug IDs.
- [ ] RTL: active border on inline-end; indent reversed.
- [ ] SSR (manual mode): links functional before script loads.
- [ ] Automated axe checks pass with zero violations.

## 20. Open questions
- Should the component support numbered (ordered) sections by rendering an
  `<ol>` instead of `<ul>`, reflecting the document heading hierarchy?
- Should `mj-toc` handle scroll-spy coordination with multiple TOC instances on
  the same page (e.g., a sidebar TOC and an inline mini-TOC)?
