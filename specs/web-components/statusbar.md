# Status Bar Spec

- **Tag:** `<mj-status-bar>`
- **Class / file:** `StatusBar` / `statusbar.js`
- **Category:** Application & productivity components
- **Primary or Variant:** Primary
- **Synonyms covered:** Status bar, Application status strip
- **Phase:** P3
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-status-bar>` is a persistent, non-blocking horizontal strip pinned to the bottom of the application viewport. It surfaces low-priority ambient information (cursor position, selection count, language mode, sync status, progress) and announces dynamic changes to screen readers via a `status` live region. It is informational only and never blocks interaction.

## 2. When to use / when not to use
Use for ambient application-state indicators that users benefit from glancing at but do not need to act on immediately (e.g., VS Code-style status bar). Do not use for urgent alerts or errors — use `<mj-alert>` or `<mj-toast>` instead. Do not use as a toolbar; interactive controls in the status bar must be limited to lightweight toggles or indicator-buttons that open a small popover.

## 3. Anatomy
- **root bar** — `<footer role="contentinfo">` or `<div role="status">` depending on placement; contains a live region.
- **left section** — slot for primary status items (e.g., mode indicator, position).
- **center section** — slot for globally scoped info (e.g., workspace name).
- **right section** — slot for secondary items (e.g., encoding, line-ending, zoom).
- **status item** — `<mj-status-item>` child; a small labeled indicator, optionally button-like.
- **separator** — `<mj-separator orientation="vertical">` between logical groups of items.
- **live region** — a visually hidden `<div role="status" aria-live="polite" aria-atomic="false">` that receives programmatic announcements.

## 4. Variants & modes
| Variant / mode | Attribute | Behavior difference |
|----------------|-----------|---------------------|
| Default | (none) | Three-section layout (start / center / end) |
| Minimal | `variant="minimal"` | Only the start section; reduced height |
| Colored | `severity` on individual items | Item background tinted by severity token |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `label` | string | `"Status bar"` | Yes | Accessible name for the status bar region |
| `variant` | `"default"\|"minimal"` | `"default"` | Yes | Layout variant |
| `hidden` | boolean | `false` | Yes | Hides the entire bar; `aria-hidden="true"` applied |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `announce` | `(message: string, politeness?: "polite"\|"assertive") => void` | Programmatically inject a message into the live region |
| `items` | `Element[]` | Read-only list of all slotted `<mj-status-item>` elements |

## 7. Slots
| Slot | Description |
|------|-------------|
| `start` | Left-aligned status items |
| (default) | Center-aligned content |
| `end` | Right-aligned status items |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-status-item-click` | `{ itemId: string, value: string }` | Yes | No | Fires when an interactive `<mj-status-item>` is clicked or activated |

## 9. CSS parts & custom properties
**Parts:** `root`, `section-start`, `section-center`, `section-end`, `live-region`.

| Custom property | Default | Description |
|-----------------|---------|-------------|
| `--mj-statusbar-height` | `22px` | Height of the bar |
| `--mj-statusbar-bg` | `var(--mj-color-surface-3)` | Background color |
| `--mj-statusbar-color` | `var(--mj-color-text-secondary)` | Default text color |
| `--mj-statusbar-font-size` | `var(--mj-font-size-xs)` | Font size for items |
| `--mj-statusbar-border` | `var(--mj-border-subtle)` | Top border |
| `--mj-statusbar-item-padding` | `0 var(--mj-space-2)` | Padding of each status item |

## 10. States
- **default** — bar visible, items rendered, live region active.
- **hidden** — `hidden` attribute set; bar not rendered; `aria-hidden="true"`.
- **item-hover** — interactive status item shows hover background.
- **item-focus-visible** — interactive status item shows focus ring.
- **item-active** — interactive item shows pressed state briefly.
- **severity-info / warning / error / success** — individual items carry `severity` attribute; background tinted by corresponding token.

## 11. Behavior & interactions
Status items are primarily display-only. If a `<mj-status-item>` has `interactive` attribute it renders as a `<button>` and can open a `<mj-popover>` (e.g., language selector). When a consumer sets a status item's text content programmatically, the item's change is not automatically announced; the consumer must call `statusBar.announce(message)` to push a human-readable summary to the live region. The live region uses `polite` by default; `assertive` is available for error-severity announcements but should be used sparingly. The bar is `position: sticky; bottom: 0` within its containing `<mj-app-shell>` or `<body>`.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` | Moves focus to the next interactive status item (if any) |
| `Shift+Tab` | Moves focus to the previous interactive status item |
| `Enter` / `Space` | Activates the focused interactive status item |
| `Escape` | Closes any popover opened by an interactive status item |

## 13. Accessibility
The root element uses `role="status"` with `aria-live="polite"` for the live region, keeping in a visually-hidden child `<div>` to avoid spurious re-reads of the entire bar. Static display items are `aria-hidden="true"` from the accessibility tree unless they convey unique meaningful state (in which case they carry `aria-label`). Interactive items are real `<button>` elements with descriptive `aria-label`s — never icon-only without a label. The bar is not a landmark; it is decorative chrome. Minimum tap/click target size for interactive items is 24 × 24 px per WCAG 2.2 §2.5.8.

## 14. Form participation
N/A — status bar is purely informational.

## 15. Internationalization & RTL
The `label` attribute and each `<mj-status-item>`'s `label` attribute are localizable. In RTL, start/end sections swap visual positions (CSS logical properties `inline-start` / `inline-end`). Numeric values (line number, column, zoom %) are formatted via `Intl.NumberFormat` using the document's locale.

## 16. Progressive enhancement / SSR
Server renders a `<footer>` with plain text spans for each status item. Without JS the content is visible as static text. On upgrade the component introduces the live region, interactive button wrapping for interactive items, and applies token-based styling. No layout shift because the bar height is fixed.

## 17. Dependencies
- **Foundations:** Registry + base element helper, Design-token stylesheet, Live-region/announcement service, Localization/formatting hook.
- **Components:** `<mj-status-item>` (internal sub-element), `<mj-separator>`, `<mj-popover>` (used by interactive items).

## 18. Edge cases & error handling
- No slotted items: bar renders as an empty strip with correct height (does not collapse).
- Overflow of items in a section: items clip with `overflow: hidden`; no wrapping to a second row.
- `announce()` called faster than screen readers can process: messages are queued by the live-region service with a minimum 150 ms gap.
- `severity="error"` item: tinted background must maintain 4.5:1 contrast ratio for text.
- `hidden` toggled rapidly: CSS transition on `height` debounced to prevent jank.

## 19. Acceptance criteria
- [ ] `role="status"` live region present and receives `announce()` text.
- [ ] Polite announcements do not interrupt ongoing screen reader speech.
- [ ] Interactive items render as `<button>` with `aria-label`.
- [ ] RTL: start and end sections visually swap; numeric formatting uses document locale.
- [ ] Bar stays pinned to bottom of `<mj-app-shell>` viewport.
- [ ] Axe scan reports zero violations.
- [ ] Severity tinted items maintain 4.5:1 text contrast.
- [ ] Light, dark, high-contrast, and RTL rendering verified.

## 20. Open questions
- Should the component provide a built-in "progress" item that directly mirrors a `<mj-progress>` value, or should consumers slot one in?
- Is a vertical status bar (for side-panel applications) in scope?
