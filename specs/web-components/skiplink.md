# Skip Link Spec

- **Tag:** `<mj-skip-link>`
- **Class / file:** `MjSkipLink` / `mjskiplink.js`
- **Category:** Navigation components
- **Primary or Variant:** Primary
- **Synonyms covered:** Skip link, Skip navigation, Skip to content, Bypass block
- **Phase:** P0
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-skip-link>` is the first focusable element on a page. It renders a visually
hidden anchor that becomes visible when focused, allowing keyboard and
screen-reader users to bypass repetitive navigation and jump directly to the main
content landmark. It satisfies WCAG 2.4.1 Bypass Blocks (Level A).

## 2. When to use / when not to use
**Always use** this component (or an equivalent) as the very first focusable
element on pages with repeated navigation. Place it before `<mj-app-bar>` in the
DOM order. **Do not** use this in place of proper semantic landmark structure —
it supplements, not replaces, correct landmark usage. **Do not** use more than
one `<mj-skip-link>` that targets the same destination per page.

## 3. Anatomy
- **Host element** — renders as a `<div>` wrapper; not itself focusable.
- **Anchor** (`::part(anchor)`) — the real `<a href="#targetId">` that is the
  focusable skip link.
- **Label** (`::part(label)`) — text content of the anchor; either from the
  `label` attribute or the default slot.

## 4. Variants & modes
| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Default | _(none)_ | Single link to `target` (typically `#main`) |
| Multiple targets | _(multiple `<mj-skip-link>` instances)_ | One per skip destination; each is a sibling component |
| Custom position | `variant="inline"` | Always visible; not hidden off-screen; used in constrained custom shells |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `target` | string | `"#main"` | Yes | `href` of the skip-link anchor; the `id` of the destination landmark |
| `label` | string | `"Skip to main content"` | Yes | Visible and accessible text of the link |
| `variant` | string | `"default"` | Yes | `default` (visually hidden until focus) \| `inline` (always visible) |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `anchorElement` | `HTMLAnchorElement` | Read-only reference to the inner `<a>` element |

## 7. Slots
| Slot | Description |
|------|-------------|
| _(default)_ | Link label text; overrides the `label` attribute when provided |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-skip-link-activate` | `{ target: string, originalEvent: MouseEvent \| KeyboardEvent }` | Yes | Yes | Fires when the skip link is activated; cancel to handle scroll/focus manually |

## 9. CSS parts & custom properties
**Parts**
- `::part(anchor)` — the `<a>` element
- `::part(label)` — the text label span inside the anchor

**Custom properties**
| Property | Default | Description |
|----------|---------|-------------|
| `--mj-skip-link-bg` | `var(--mj-color-primary)` | Background of the visible skip link |
| `--mj-skip-link-color` | `var(--mj-color-on-primary)` | Text color |
| `--mj-skip-link-padding` | `var(--mj-spacing-3) var(--mj-spacing-5)` | Padding around the label |
| `--mj-skip-link-radius` | `var(--mj-radius-sm)` | Border radius |
| `--mj-skip-link-z-index` | `var(--mj-z-index-skip-link)` | Stack order when visible |
| `--mj-skip-link-offset-top` | `var(--mj-spacing-3)` | Distance from the top of the viewport when focused |
| `--mj-skip-link-offset-start` | `var(--mj-spacing-3)` | Distance from the inline-start edge when focused |

## 10. States
- **default (hidden)** — the anchor is positioned off-screen via
  `clip` / `clip-path` technique; not visible but reachable by Tab.
- **focus-visible** — the anchor moves into the viewport (top-left corner);
  full background and text color visible; high-contrast mode supported.
- **activated** — the user has pressed Enter; focus moves to the target element.
- **inline** — variant where the link is always visible; no hidden/focus toggle.

## 11. Behavior & interactions
- The anchor is positioned off-screen using a CSS technique that keeps it in the
  accessibility tree and tab order (`position: absolute; left: -9999px` or
  `clip-path: inset(100%)`). It becomes visible on `:focus-visible` via CSS
  transition to `left: var(--mj-skip-link-offset-start)`.
- When activated (Enter key or click), the component:
  1. Fires `mj-skip-link-activate`; if not canceled:
  2. Finds the target element by `document.querySelector(target)`.
  3. If the target is not natively focusable, temporarily sets `tabindex="-1"`.
  4. Calls `target.focus()`.
  5. Optionally calls `target.scrollIntoView({ behavior: "instant" })`.
- The temporary `tabindex="-1"` is removed on the next `blur` event of the
  target to avoid leaving it in the tab order.
- `prefers-reduced-motion`: the show/hide animation is suppressed; the link
  appears/disappears immediately.
- The component must be the first child of `<body>` (or the first focusable
  element in the layout) to be effective. A console warning is emitted in
  development if it detects that other focusable elements precede it in the DOM.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` | First Tab press on the page focuses the skip link; the link becomes visible |
| `Enter` | Activates the skip link; moves focus to the target landmark |
| `Shift+Tab` (from main) | Does not return to the skip link; it remains hidden unless reached by forward Tab |

## 13. Accessibility
- The anchor has a clear, descriptive visible label when focused.
- The link satisfies WCAG 2.4.1 Bypass Blocks (Level A).
- When activated, focus moves to the target landmark element (e.g., `<main
  id="main">`), which screen readers announce by its role and label.
- The skip link itself is not wrapped in any ARIA landmark to avoid polluting the
  landmark map.
- In high-contrast / forced-colors mode, the link's background and text are
  mapped to `ButtonFace` and `ButtonText` system colors.
- The visible link must meet WCAG 1.4.3 contrast requirements (4.5:1 for normal
  text or 3:1 for large text).
- Target size when focused: minimum 24×24 CSS px per WCAG 2.5.8 (practically
  will be much larger due to padding).

## 14. Form participation
N/A — `<mj-skip-link>` is a navigation accessibility aid, not a form control.

## 15. Internationalization & RTL
- `label` is localizable via attribute or the localization key
  `mj.skipLink.label` (default: "Skip to main content").
- In RTL, when the link becomes visible, it aligns to the inline-end (right)
  edge using logical properties (`inset-inline-start` / `inset-inline-end`).
- RTL does not change the functional behavior.

## 16. Progressive enhancement / SSR
- Server renders:
  ```html
  <mj-skip-link target="#main" label="Skip to main content">
    Skip to main content
  </mj-skip-link>
  ```
- Before upgrade: the inner `<a href="#main">` functions as a native anchor;
  clicking it scrolls to and focuses the `#main` element via browser-native
  anchor behavior.
- On upgrade: the component adds the off-screen hiding CSS and the focus-
  management enhancement; the native anchor fallback is replaced in place.

## 17. Dependencies
- Section 6: Registry + base element helper, design-token stylesheet,
  localization hook.
- No other `mj-*` components required.

## 18. Edge cases & error handling
- **`target` element not found in DOM**: the link is still rendered and
  functional; clicking it fires `mj-skip-link-activate` but logs a console
  error and performs no focus movement.
- **`target` element is not focusable and has no `tabindex`**: the component
  adds `tabindex="-1"` temporarily; if the element is hidden (`display: none`),
  it cannot receive focus — a console warning is emitted.
- **Multiple `<mj-skip-link>` instances**: each renders independently; the first
  in DOM order is the first Tab stop; subsequent skip links follow.
- **`variant="inline"`**: the link is always visible; no focus/visibility toggle;
  useful for embedding in custom app shells where the normal position is not
  first in DOM.
- **CSS custom property overrides cause low contrast**: the component does not
  enforce contrast at runtime; authors are responsible for maintaining WCAG
  compliance when overriding tokens.

## 19. Acceptance criteria
- [ ] First Tab press on the page focuses the skip link and makes it visible.
- [ ] Skip link anchor is in the DOM and keyboard-reachable at all times.
- [ ] Enter activation moves focus to the `target` element.
- [ ] Target element receives `tabindex="-1"` temporarily if not natively focusable.
- [ ] `mj-skip-link-activate` fires and is cancelable.
- [ ] Link visible in focused state meets WCAG 4.5:1 contrast.
- [ ] `variant="inline"` is always visible regardless of focus state.
- [ ] High-contrast (forced-colors) mode renders correctly using system colors.
- [ ] RTL: link appears at inline-end when focused.
- [ ] `prefers-reduced-motion`: no show/hide animation.
- [ ] SSR: native `<a href="#main">` functional before script loads.
- [ ] Automated axe checks pass with zero violations.

## 20. Open questions
- Should the component emit a warning if it detects it is not the first
  focusable element in the `<body>`? This would require scanning the DOM on
  `connectedCallback`, which could be expensive on large pages.
- Should `<mj-skip-link>` support multiple named targets in a single instance
  (e.g., skip to navigation, skip to search, skip to main) via a list attribute?
