# Link Spec

- **Tag:** `<mj-link>`
- **Class / file:** `MjLink` / `mjlink.js`
- **Category:** Navigation components
- **Primary or Variant:** Primary
- **Synonyms covered:** Link, Anchor link, Navigation hyperlink, Inline link
- **Phase:** P0
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-link>` is a styled navigation hyperlink built on a real `<a>` element. It
provides consistent visual treatment for inline, navigation, and external links
while adding built-in affordances for external destinations (icon + `target`
handling) and visited-state cues — ensuring links are never implemented as
`<div>` or `<button>` with click handlers.

## 2. When to use / when not to use
**Use** when navigating to a URL (same-page anchor, internal page, or external
site). **Do not use** to trigger an action with no URL — use `<mj-button
variant="link">` instead. For nav landmark menus, prefer `<mj-side-nav>` or
`<mj-app-bar>` which compose `<mj-link>` internally.

## 3. Anatomy
- **Host element** (`<mj-link>`) — the custom element shell.
- **Inner `<a>`** (`::part(anchor)`) — the real anchor that carries `href`,
  `target`, `rel`, `download`, and all native link semantics.
- **Prefix slot** — optional icon/badge before the label.
- **Default slot** — link label text.
- **External icon** (`::part(external-icon)`) — auto-rendered `aria-hidden`
  icon appended when `external` is present; hidden from the accessibility tree.

## 4. Variants & modes
| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Default | _(none)_ | Standard inline link; inherits surrounding text color and underline token |
| External | `external` | Appends an external-link icon; sets `target="_blank"` and `rel="noopener noreferrer"` unless overridden |
| Subtle | `variant="subtle"` | Reduced visual weight; underline only on hover/focus; used inside card surfaces |
| Standalone | `variant="standalone"` | Block-level link with leading icon affordance; used in navigation lists |
| Disabled | `disabled` | Renders without `href`; `aria-disabled="true"`; pointer events removed |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `href` | string | `""` | Yes | Destination URL passed to the inner `<a>` |
| `target` | string | `""` | Yes | Browsing context (`_blank`, `_self`, etc.) |
| `rel` | string | `""` | Yes | Link relationship; automatically includes `noopener noreferrer` when `external` is set |
| `download` | string | `""` | Yes | When present, triggers download; value is the suggested filename |
| `external` | boolean | `false` | Yes | Marks the link as external; adds icon and sets safe `target`/`rel` defaults |
| `variant` | string | `"default"` | Yes | Visual style: `default` \| `subtle` \| `standalone` |
| `disabled` | boolean | `false` | Yes | Removes `href`, sets `aria-disabled="true"`, suppresses pointer events |
| `visited-cue` | boolean | `true` | Yes | Enables the visited-state color token; set to `false` to suppress |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `anchorElement` | `HTMLAnchorElement` | Read-only reference to the inner `<a>` for scripted use |

## 7. Slots
| Slot | Description |
|------|-------------|
| _(default)_ | Link label; required for an accessible name |
| `prefix` | Leading icon or decoration placed before the label text |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-link-click` | `{ href: string, external: boolean, originalEvent: MouseEvent }` | Yes | Yes | Fires before navigation; cancel to intercept |

## 9. CSS parts & custom properties
**Parts**
- `::part(anchor)` — the inner `<a>` element
- `::part(external-icon)` — the external-link SVG icon
- `::part(prefix)` — wrapper around the prefix slot

**Custom properties**
| Property | Default | Description |
|----------|---------|-------------|
| `--mj-link-color` | `var(--mj-color-link)` | Default text color |
| `--mj-link-color-visited` | `var(--mj-color-link-visited)` | Visited-state color |
| `--mj-link-color-hover` | `var(--mj-color-link-hover)` | Hover/focus color |
| `--mj-link-color-disabled` | `var(--mj-color-text-disabled)` | Disabled color |
| `--mj-link-underline-offset` | `2px` | `text-underline-offset` value |
| `--mj-link-external-icon-size` | `0.875em` | Inline size of the external icon |

## 10. States
- **default** — underlined in `--mj-link-color`; cursor pointer.
- **hover** — color shifts to `--mj-link-color-hover`; underline always visible.
- **focus-visible** — focus ring using `--mj-color-focus-ring`; minimum 3:1 contrast against adjacent color.
- **active** — slightly darker token applied during mouse-down.
- **visited** — color shifts to `--mj-link-color-visited` when `visited-cue` is true.
- **disabled** — `aria-disabled="true"`; `href` absent; `--mj-link-color-disabled`; `cursor: not-allowed`.
- **external** — external icon visible; `rel`/`target` auto-set.

## 11. Behavior & interactions
- The inner `<a>` is always the real focusable/clickable element; the host
  element is `display: contents` or inline so surrounding text flow is unaffected.
- When `external` is set and `target` is not explicitly provided, `target` is
  set to `"_blank"` and `rel` is forced to include `noopener noreferrer`.
- Clicking a `disabled` link fires no navigation and emits no `mj-link-click`.
- `mj-link-click` is dispatched synchronously before the browser follows the
  anchor; canceling the event calls `preventDefault()` on the inner click.
- The external icon is `aria-hidden="true"` and has no role; its presence is
  conveyed to screen readers via the visually-hidden supplementary text set
  through the `external-label` localization key (e.g. "opens in a new tab").

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` | Moves focus to the link (if not disabled) |
| `Enter` | Activates the link; same as a left-click |
| `Shift+Tab` | Moves focus away from the link |

## 13. Accessibility
- Role: native `<a>` provides the `link` role automatically; no explicit ARIA
  role needed.
- Accessible name: derived from slot text content; authors must ensure
  descriptive labels (not just "click here").
- `aria-disabled="true"` used instead of the `disabled` attribute (which has no
  effect on `<a>`); the element remains in the tab order but announces as
  disabled.
- External icon is `aria-hidden`; a visually-hidden span appends the
  locale-key string (default: ", opens in a new tab") so screen readers announce
  the context.
- `visited-cue` color must maintain at least 3:1 contrast against the page
  background per WCAG 1.4.11 Non-text Contrast.
- Minimum touch/click target: 24×24 CSS px (WCAG 2.5.8 Target Size Minimum).

## 14. Form participation
N/A — `<mj-link>` is a navigation element, not a form control.

## 15. Internationalization & RTL
- The external-icon visually-hidden label is provided through the shared
  localization hook; key: `mj.link.externalLabel`; default: "opens in a new tab".
- In RTL contexts (`dir="rtl"`), the external icon flips horizontally via
  `transform: scaleX(-1)` so it points in the natural reading direction.
- The prefix slot content is logically before the label in both LTR and RTL; CSS
  `flex-direction` reversal is applied when `dir="rtl"` is inherited or set.

## 16. Progressive enhancement / SSR
- Server renders a plain `<a href="...">label</a>` inside the custom element tag.
- Before the script loads, the native anchor is fully functional.
- On upgrade, the component wraps the slotted content into Shadow DOM, adds the
  external icon if needed, and applies token-driven styles — no content shift.
- The `external` attribute can be present in server markup; the icon is added
  only after upgrade, so SSR markup need not include it.

## 17. Dependencies
- Section 6: Registry + base element helper; design-token stylesheet.
- No other `mj-*` components required.

## 18. Edge cases & error handling
- **Empty `href`**: renders an anchor with `href=""`; the element is still
  focusable but navigates to the current URL. Authors should use `disabled`
  instead of an empty `href` when no destination exists.
- **Long label text**: wraps naturally; no truncation by default; `variant="standalone"` may apply `text-overflow: ellipsis` with `title` fallback.
- **Both `disabled` and `href`**: `disabled` takes precedence; `href` is removed
  from the inner anchor.
- **Missing slot text**: no accessible name is generated; the component emits a
  console warning in development mode.
- **`download` on `external`**: both attributes can coexist; `rel` is still
  forced to include `noopener noreferrer`.

## 19. Acceptance criteria
- [ ] Renders a real `<a>` element as the interactive target in all configurations.
- [ ] `external` attribute appends icon, sets `target="_blank"`, forces safe `rel`.
- [ ] Visually-hidden external label is announced by screen readers.
- [ ] `disabled` removes `href`, sets `aria-disabled="true"`, suppresses click and event.
- [ ] `mj-link-click` fires and is cancelable; canceling prevents navigation.
- [ ] `visited-cue=false` suppresses `:visited` color styling.
- [ ] All color states meet WCAG 2.2 AA contrast ratios.
- [ ] Focus ring is visible and meets 3:1 contrast.
- [ ] Keyboard: Tab focuses link; Enter activates it.
- [ ] RTL: external icon and prefix slot reverse correctly.
- [ ] SSR: plain `<a>` in server markup functions before script loads.
- [ ] Automated axe checks pass with zero violations.

## 20. Open questions
- Should `<mj-link>` support a `router-link` mode (intercept and delegate to a
  client-side router) via a global hook, or leave that entirely to the
  `mj-link-click` event handler pattern?
- Should `visited-cue` default to `false` in navigation contexts (sidebar, app
  bar) where visited styling is rarely desirable?
