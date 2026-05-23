# App Shell Spec

- **Tag:** `<mj-app-shell>`
- **Class / file:** `AppShell` / `appshell.js`
- **Category:** Application & productivity components
- **Primary or Variant:** Primary
- **Synonyms covered:** Dock, Workspace switcher, Split view, Inspector panel, Properties panel
- **Phase:** P2
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-app-shell>` is the outermost layout frame for a full-page web application. It composes a top AppBar, a start-side SideNav, a main content area, an optional end-side inspector/properties panel, and a bottom StatusBar into a semantically correct landmark structure. It owns panel-size persistence, responsive collapse behavior, and keyboard-resizable split panes. Sub-patterns (Dock, Workspace switcher, Inspector panel) are realized through slots and attributes rather than separate components.

## 2. When to use / when not to use
Use as the single root layout element for desktop-style web applications that need a persistent navigation structure alongside main content. Do not nest `<mj-app-shell>` instances. Do not use for marketing pages, document sites, or apps that scroll naturally — use semantic HTML landmarks directly.

## 3. Anatomy
- **app-bar region** — slot `app-bar`; hosts `<mj-app-bar>` for branding, nav, and global actions.
- **dock rail** — slot `dock`; optional `<mj-sidenav variant="dock">` pinned launcher strip (icon-only).
- **side-nav region** — slot `nav`; hosts `<mj-sidenav>` for primary navigation.
- **workspace switcher** — slot `workspace`; optional `<mj-select>` or `<mj-menu>` for workspace/project switching within the app-bar or above the nav.
- **main content area** — slot `main` (default); the primary scrollable region; maps to `<main>` landmark.
- **inspector/properties panel** — slot `inspector`; collapsible end-side panel for contextual detail; uses `<mj-split-pane>`.
- **status bar region** — slot `status-bar`; hosts `<mj-status-bar>` pinned to bottom.
- **split handle** — `<mj-split-pane>` separator between main and inspector; `role="separator"` with `aria-valuenow`.

## 4. Variants & modes
| Variant / mode | Attribute | Behavior difference |
|----------------|-----------|---------------------|
| Default | (none) | AppBar + SideNav (static) + Main + StatusBar |
| With inspector | `inspector-open` | Adds resizable inspector panel on the end side |
| With dock | `dock` slot populated | Adds a narrow icon-rail to the far start side |
| Workspace switcher | `workspace` slot populated | Renders workspace chooser above or within the app-bar |
| Split view | `split` | Divides `main` slot into two `<mj-split-pane>` regions |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `nav-open` | boolean | `true` | Yes | Whether the side-nav is expanded |
| `nav-mode` | `"static"\|"collapsible"\|"overlay"` | `"static"` | Yes | Side-nav display mode |
| `inspector-open` | boolean | `false` | Yes | Whether the inspector panel is visible |
| `inspector-size` | number | `320` | No | Inspector panel width in px; persisted to localStorage |
| `nav-size` | number | `240` | No | Side-nav width in px; persisted to localStorage |
| `split` | boolean | `false` | Yes | Enables a two-pane split in the main area |
| `split-ratio` | number | `0.5` | No | Ratio of the primary pane (0–1); persisted |
| `storage-key` | string | `"mj-app-shell"` | Yes | Prefix for localStorage panel-size entries |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `navPanel` | `Element \| null` | Reference to the slotted SideNav element |
| `inspectorPanel` | `Element \| null` | Reference to the slotted inspector element |
| `toggleNav` | `() => void` | Programmatically toggle the side-nav open/closed |
| `toggleInspector` | `() => void` | Programmatically toggle the inspector open/closed |

## 7. Slots
| Slot | Description |
|------|-------------|
| `app-bar` | Top AppBar |
| `dock` | Narrow icon-only dock rail (start-side, outside nav) |
| `workspace` | Workspace switcher control |
| `nav` | Primary side navigation |
| (default / `main`) | Main scrollable content area |
| `split-secondary` | Secondary pane content when `split` is enabled |
| `inspector` | End-side inspector / properties panel |
| `status-bar` | Bottom status bar |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-shell-nav-toggle` | `{ open: boolean }` | Yes | No | Fires when the side-nav opens or closes |
| `mj-shell-inspector-toggle` | `{ open: boolean }` | Yes | No | Fires when the inspector opens or closes |
| `mj-shell-inspector-resize` | `{ size: number }` | Yes | No | Fires on inspector drag-resize (debounced 200 ms) |
| `mj-shell-split-resize` | `{ ratio: number }` | Yes | No | Fires on split-pane drag-resize (debounced 200 ms) |

## 9. CSS parts & custom properties
**Parts:** `root`, `app-bar`, `dock`, `nav`, `main`, `inspector`, `status-bar`, `split-handle`, `nav-toggle-button`.

| Custom property | Default | Description |
|-----------------|---------|-------------|
| `--mj-shell-nav-width` | `240px` | Collapsed/expanded side-nav width (overridden by `nav-size`) |
| `--mj-shell-inspector-width` | `320px` | Inspector default width (overridden by `inspector-size`) |
| `--mj-shell-dock-width` | `48px` | Dock rail width |
| `--mj-shell-appbar-height` | `var(--mj-size-control-lg)` | App-bar height |
| `--mj-shell-statusbar-height` | `22px` | Status-bar height |
| `--mj-shell-bg` | `var(--mj-color-surface-1)` | Root background |
| `--mj-shell-split-handle-size` | `4px` | Width/height of the resize handle |

## 10. States
- **nav-open** — side-nav at full width; `nav-open` attribute present.
- **nav-collapsed** — side-nav at icon-only width (collapsible mode) or hidden (overlay mode); `nav-open` absent.
- **nav-overlay** — nav rendered as an overlay drawer with backdrop; focus trapped; `nav-mode="overlay"`.
- **inspector-open** — inspector panel visible; `inspector-open` attribute present.
- **inspector-closed** — inspector hidden; `inspector-open` absent.
- **split-active** — main area split into two panes; `split` attribute present.
- **resizing** — user is dragging a split handle; `resizing` attribute on the handle for cursor styling.

## 11. Behavior & interactions
Panel sizes are stored in `localStorage` under the `storage-key` prefix and restored on mount. `ResizeObserver` on the root switches `nav-mode` to `"overlay"` automatically when the viewport is narrower than `--mj-shell-breakpoint-nav` (default 768 px). The inspector panel and split pane handle use `<mj-split-pane>` internally; the separator is keyboard-resizable. When the nav is in overlay mode and `nav-open` is set, a backdrop is rendered behind it using the Overlay primitive; focus is trapped in the nav and restored on close. The main slot maps to a `<main>` landmark; clicking the backdrop closes the overlay nav.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` / `Shift+Tab` | Standard focus order through landmarks |
| `F6` | Cycle focus between major panels (app-bar, nav, main, inspector, status-bar) |
| `ArrowLeft` / `ArrowRight` on split handle | Resize the split pane by `--mj-shell-split-step` (default 16 px) |
| `ArrowLeft` / `ArrowRight` on inspector handle | Resize the inspector by the same step |
| `Home` / `End` on a handle | Collapse panel to minimum / expand to maximum |
| `Escape` | Close overlay nav (when in overlay mode) |

## 13. Accessibility
The shell wraps each region in the appropriate HTML5 landmark: `<header>` for the app-bar, `<nav aria-label="Primary navigation">` for the side-nav, `<main>` for the main area, `<aside aria-label="Inspector">` for the inspector, `<footer>` for the status bar. The dock (if slotted) is inside the `<nav>`. All panels have distinct `aria-label`s so screen-reader landmark navigation is unambiguous. Split handles carry `role="separator"`, `aria-orientation="vertical"`, `aria-valuenow`, `aria-valuemin`, and `aria-valuemax`. The nav toggle button has `aria-expanded` reflecting the nav's open state and `aria-controls` pointing to the nav element ID. `F6` panel cycling is announced via a polite live region ("Focus moved to Inspector").

## 14. Form participation
N/A — structural layout component.

## 15. Internationalization & RTL
In RTL (`dir="rtl"`), the side-nav is on the inline-end side and the inspector on the inline-start side (logical CSS properties throughout). The dock rail follows `inline-start`. Accessible labels for nav, inspector, and status-bar are localizable via `nav-label`, `inspector-label`, and `status-bar-label` attributes.

## 16. Progressive enhancement / SSR
Server renders semantic HTML5 landmarks (`<header>`, `<nav>`, `<main>`, `<aside>`, `<footer>`) with visible content. Without JS, the layout is a standard stacked/flex page. On upgrade the component introduces CSS Grid–based panel layout, `ResizeObserver`-driven responsiveness, and localStorage-backed sizing. No content is hidden before upgrade.

## 17. Dependencies
- **Foundations:** Registry + base element helper, Design-token stylesheet, Overlay/positioning engine, Focus utilities (focus trap, focus restore), Live-region/announcement service.
- **Components:** `<mj-app-bar>`, `<mj-sidenav>`, `<mj-split-pane>`, `<mj-status-bar>`, `<mj-button>` (nav toggle), `<mj-menu>` (workspace switcher option).

## 18. Edge cases & error handling
- No `app-bar` slot: layout starts at the top of the viewport with no header bar.
- Inspector larger than half the viewport: clamped to `max(inspector-size, viewport-width * 0.5)`.
- localStorage unavailable (private mode): panel sizes fall back to attribute defaults silently.
- `nav-mode` changes programmatically mid-session: open state is preserved where logically possible.
- Split with no `split-secondary` slot: secondary pane renders as an empty region with an "Empty" placeholder.
- Rapid `nav-open` toggles: animations are queued; duplicate state transitions are no-ops.

## 19. Acceptance criteria
- [ ] All five landmark regions present with distinct accessible names.
- [ ] `F6` cycles focus between regions and announces destination.
- [ ] Split handle keyboard resize works with `ArrowLeft`/`ArrowRight`, `Home`, `End`.
- [ ] Overlay nav traps focus and restores it on close.
- [ ] Panel sizes persist to and restore from `localStorage`.
- [ ] `ResizeObserver` switches to overlay mode below breakpoint.
- [ ] RTL: nav on inline-end, inspector on inline-start.
- [ ] Axe scan reports zero violations.
- [ ] Light, dark, high-contrast, and RTL rendering verified.

## 20. Open questions
- Should `F6` behavior be configurable or follow a fixed panel order?
- Should the workspace switcher be a first-class attribute-driven feature or purely slot-based?
- Should the dock rail support drag-reorder of its icons?
