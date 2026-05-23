# Split Pane Spec

- **Tag:** `<mj-split-pane>`
- **Class / file:** `MjSplitPane` / `mjsplitpane.js`
- **Category:** Layout & content containers (§5.5)
- **Primary or Variant:** Primary
- **Synonyms covered:** Resizable pane
- **Phase:** P2
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-split-pane>` divides its container into two adjacent resizable regions
separated by a draggable separator. It solves the common application shell
pattern of a primary content area alongside a sidebar, inspector panel, or file
tree that the user can resize to their preference. The separator is keyboard-
operable and exposes the ARIA `separator` role.

## 2. When to use / when not to use

**Use** when users need control over how much screen space each adjacent region
occupies — master/detail layouts, code editor + preview, file tree + content.
**Do not use** for decorative visual dividers between content — use `<mj-divider>`.
**Do not use** when the regions are not intended to be resized — use `<mj-grid>`
or `<mj-stack>`.

## 3. Anatomy

- **start-pane** — the first region (slot `start`); surfaced as `::part(start-pane)`.
- **separator** — the draggable/keyboard-resizable divider; surfaced as
  `::part(separator)`. Rendered as a `<div>` with `role="separator"`.
- **separator-handle** — a visual drag handle inside the separator; surfaced as
  `::part(separator-handle)`.
- **end-pane** — the second region (slot `end`); surfaced as `::part(end-pane)`.

## 4. Variants & modes

| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Horizontal split (default) | `orientation="horizontal"` | Start pane on the left, end pane on the right |
| Vertical split | `orientation="vertical"` | Start pane on top, end pane on the bottom |
| Collapsible start | `collapsible="start"` | Start pane can be collapsed to its `min` size by double-clicking the separator or via a keyboard shortcut |
| Collapsible end | `collapsible="end"` | End pane can be collapsed similarly |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `orientation` | `"horizontal"` \| `"vertical"` | `"horizontal"` | Yes | Axis of the split |
| `initial-size` | string | `"50%"` | Yes | Initial size of the start pane as a CSS length or percentage |
| `min` | string | `"80px"` | Yes | Minimum size of the start pane; end pane is also constrained symmetrically |
| `max` | string | `"calc(100% - 80px)"` | Yes | Maximum size of the start pane |
| `collapsible` | `"none"` \| `"start"` \| `"end"` \| `"both"` | `"none"` | Yes | Which pane(s) can be collapsed by double-click or keyboard |
| `persist-key` | string | `""` | Yes | When set, the split ratio is saved to and restored from `localStorage` under this key |
| `disabled` | boolean | `false` | Yes | Locks the separator; no dragging or keyboard resizing |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `size` | number | Current pixel size of the start pane; settable programmatically |
| `ratio` | number | Current split ratio (0–1) as a fraction of the total container size |

## 7. Slots

| Slot | Description |
|------|-------------|
| `start` | Content for the first (start) pane |
| `end` | Content for the second (end) pane |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-split-resize` | `{ size: number, ratio: number }` | Yes | No | Emitted continuously while the user drags the separator |
| `mj-split-resize-end` | `{ size: number, ratio: number }` | Yes | No | Emitted once when dragging ends or a keyboard resize step completes |
| `mj-split-collapse` | `{ pane: "start" \| "end" }` | Yes | No | Emitted when a pane is collapsed |
| `mj-split-expand` | `{ pane: "start" \| "end" }` | Yes | No | Emitted when a collapsed pane is expanded |

## 9. CSS parts & custom properties

**Parts**
- `::part(start-pane)` — the start region container
- `::part(separator)` — the separator element
- `::part(separator-handle)` — the visual drag handle
- `::part(end-pane)` — the end region container

**Custom properties**
| Property | Default token | Description |
|----------|--------------|-------------|
| `--mj-split-separator-size` | `4px` | Width (horizontal) or height (vertical) of the separator hit area |
| `--mj-split-separator-color` | `--mj-color-border` | Separator visual color |
| `--mj-split-separator-hover-color` | `--mj-color-primary` | Separator color on hover/focus |
| `--mj-split-handle-size` | `24px` | Length of the visible drag handle |
| `--mj-split-transition` | `--mj-motion-duration-fast` | Transition for keyboard resize steps |

## 10. States

- **default** — separator at `initial-size`; both panes visible.
- **dragging** — pointer captured; separator tracks the pointer; `mj-split-resize` events fire.
- **focus-visible** — separator has `--mj-focus-ring` outline; ready for keyboard resize.
- **disabled** — separator is not draggable; keyboard resize keys do nothing; `aria-disabled="true"`.
- **collapsed-start** — start pane at `min` size; separator at the minimum position.
- **collapsed-end** — end pane at `min` size; separator at the maximum position.

## 11. Behavior & interactions

On `pointerdown` on the separator, the component sets `pointer-capture` and
listens to `pointermove` events to compute the new start-pane size. The size is
clamped between `min` and `max`. `mj-split-resize` fires on each `pointermove`.
`mj-split-resize-end` fires on `pointerup`.

Double-clicking the separator (when `collapsible` is set) collapses the
corresponding pane to its `min` size. A second double-click restores the pane to
the last non-collapsed size.

When `persist-key` is set, the ratio is written to `localStorage` on
`mj-split-resize-end` and read in `connectedCallback` to restore the previous
layout.

`ResizeObserver` on the container recalculates pane sizes when the container
is resized so the ratio is preserved on layout changes.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Tab` | Move focus to the separator |
| `Arrow Left` / `Arrow Up` | Decrease the start pane by one step (default 8px) |
| `Arrow Right` / `Arrow Down` | Increase the start pane by one step |
| `Home` | Set start pane to its `min` size (collapses it) |
| `End` | Set start pane to its `max` size |
| `Enter` | Toggle collapse/expand the collapsible pane (when `collapsible` is set) |
| `F6` | Move focus between panes and the separator (standard split pane keyboard convention) |

## 13. Accessibility

- Separator `<div>` has `role="separator"` and `aria-orientation` matching the
  component's `orientation` attribute.
- `aria-valuenow` on the separator reflects the current start-pane size as a
  pixel value; `aria-valuemin` and `aria-valuemax` reflect `min` and `max`.
- `aria-valuetext` provides a human-readable description, e.g. "Start pane:
  320 pixels" — overridable via the `label-format` attribute.
- When `disabled`, the separator has `aria-disabled="true"`.
- The separator has an accessible name via `aria-label` (default "Resize") —
  overridable via the `separator-label` attribute.
- Focus is never trapped in either pane; focus moves naturally through slotted content.

## 14. Form participation

N/A — `<mj-split-pane>` is a layout component and does not participate in forms.

## 15. Internationalization & RTL

In RTL contexts with `orientation="horizontal"`, the logical meaning of "start"
and "end" panes follows the inline direction. Arrow key behavior is flipped:
`Arrow Left` increases the start pane (which is on the right in RTL). The
component reads `dir` from the nearest ancestor and adjusts key bindings
accordingly.

`separator-label` and `aria-valuetext` use the Section 6 localization hook.

## 16. Progressive enhancement / SSR

The server renders two sibling `<div>` elements for start and end panes. Without
JavaScript they are displayed as a static side-by-side layout via CSS. After
upgrade the component inserts the separator and enables drag/keyboard resize.
The initial layout uses the `initial-size` CSS value applied as an inline style
on the start pane so the proportions are correct before upgrade.

## 17. Dependencies

- Section 6: Registry + base element helper; design-token stylesheet; focus
  utilities; localization hook.
- `ResizeObserver`, `PointerEvent` (native browser APIs).

## 18. Edge cases & error handling

- **Container collapses to zero width** — pane sizes clamp to `min`; no negative sizes.
- **`min` > `max`** — the component clamps `min` to `max`; console warning emitted.
- **`initial-size` outside `[min, max]`** — clamped silently on first render.
- **`persist-key` collision** — two instances with the same key share the ratio;
  authors are responsible for unique keys.
- **Orientation change at runtime** — component re-reads pane sizes and re-applies
  the ratio to the new axis; `persist-key` state is reset.

## 19. Acceptance criteria

- [ ] Dragging the separator resizes both panes; `mj-split-resize` fires on each move.
- [ ] Arrow keys resize by one step; Home/End jump to min/max.
- [ ] `aria-valuenow` updates to reflect the current start-pane pixel size.
- [ ] `persist-key` saves and restores the ratio via `localStorage`.
- [ ] Double-click on the separator collapses/expands the collapsible pane.
- [ ] `disabled` prevents all resizing; separator is `aria-disabled="true"`.
- [ ] RTL horizontal split reverses Arrow Left/Right behavior.
- [ ] `ResizeObserver` preserves the ratio when the container is resized.
- [ ] Automated accessibility check passes with no violations.

## 20. Open questions

- Should `<mj-split-pane>` support more than two panes (a three-way split) via additional slots, or does that require nesting two instances?
- Should the keyboard step size be configurable via an attribute (e.g., `step="16"`)?
