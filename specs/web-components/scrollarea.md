# Scroll Area Spec

- **Tag:** `<mj-scroll-area>`
- **Class / file:** `MjScrollArea` / `mjscrollarea.js`
- **Category:** Layout & content containers (§5.5)
- **Primary or Variant:** Primary
- **Synonyms covered:** Styled scroll container
- **Phase:** P2
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-scroll-area>` wraps a scrollable region with consistently styled, theme-
aware scrollbars while preserving native scroll behavior, momentum scrolling,
and keyboard scrollability. It solves the cross-browser inconsistency of
`scrollbar-color`/`scrollbar-width` and the common need for custom-styled
scrollbars that still work correctly with assistive technology.

## 2. When to use / when not to use

**Use** when you need a constrained-height container with styled overflow
scrolling — a chat message list, a virtualized item list, a code block, a long
dropdown option list. **Do not use** when the native page scroll is intended —
do not wrap the whole page body. **Do not use** when custom scrollbar aesthetics
are not needed and native scrollbars are acceptable; in that case use a plain
element with `overflow: auto`.

## 3. Anatomy

- **viewport** — the scrollable `<div>` with `overflow: auto` that clips content;
  surfaced as `::part(viewport)`.
- **default slot** — all content placed inside the viewport.
- **scrollbar-x** — horizontal scrollbar track and thumb; surfaced as
  `::part(scrollbar-x)`.
- **scrollbar-y** — vertical scrollbar track and thumb; surfaced as
  `::part(scrollbar-y)`.
- **thumb-x** / **thumb-y** — the draggable thumb elements inside each scrollbar;
  surfaced as `::part(thumb-x)` and `::part(thumb-y)`.
- **corner** — the corner fill element when both scrollbars are visible;
  surfaced as `::part(corner)`.

## 4. Variants & modes

| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Vertical only (default) | `overflow-x="hidden"` | Only vertical scrollbar shown |
| Both axes | `overflow-x="auto"` | Both scrollbars shown when content overflows |
| Horizontal only | `overflow-y="hidden"` + `overflow-x="auto"` | Only horizontal scrollbar |
| Native fallback | `native` boolean | Uses native browser scrollbars; no custom rendering |
| Always visible | `scrollbar-visibility="always"` | Scrollbar always rendered even when content fits |
| Auto-hide | `scrollbar-visibility="auto"` (default) | Scrollbar appears on hover/scroll, fades after idle |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `overflow-x` | `"auto"` \| `"hidden"` \| `"scroll"` | `"hidden"` | Yes | Horizontal overflow policy |
| `overflow-y` | `"auto"` \| `"hidden"` \| `"scroll"` | `"auto"` | Yes | Vertical overflow policy |
| `scrollbar-visibility` | `"auto"` \| `"always"` \| `"hover"` | `"auto"` | Yes | Controls when the scrollbar is visible |
| `native` | boolean | `false` | Yes | Use native scrollbars without custom rendering |
| `scroll-padding` | string | `"0"` | Yes | CSS `scroll-padding` applied to the viewport for scroll-snap compatibility |
| `tabindex` | string | `"0"` | Yes | Tabindex of the viewport element; defaults to `0` so the region is keyboard-scrollable |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `scrollTop` | number | Proxy for `viewport.scrollTop`; readable and settable |
| `scrollLeft` | number | Proxy for `viewport.scrollLeft`; readable and settable |
| `scrollHeight` | number (readonly) | Proxy for `viewport.scrollHeight` |
| `scrollWidth` | number (readonly) | Proxy for `viewport.scrollWidth` |

## 7. Slots

| Slot | Description |
|------|-------------|
| (default) | Scrollable content; any element or text |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-scroll` | `{ scrollTop: number, scrollLeft: number, scrollHeight: number, scrollWidth: number }` | Yes | No | Throttled proxy of the native `scroll` event on the viewport |
| `mj-scroll-end` | `{ scrollTop: number, scrollLeft: number }` | Yes | No | Emitted when scroll momentum ends (via `scrollend` where available, or a 150 ms idle fallback) |

## 9. CSS parts & custom properties

**Parts**
- `::part(viewport)` — the scrollable container
- `::part(scrollbar-y)` — vertical scrollbar track
- `::part(scrollbar-x)` — horizontal scrollbar track
- `::part(thumb-y)` — vertical scrollbar thumb
- `::part(thumb-x)` — horizontal scrollbar thumb
- `::part(corner)` — corner fill between both scrollbars

**Custom properties**
| Property | Default token | Description |
|----------|--------------|-------------|
| `--mj-scroll-thumb-color` | `--mj-color-scrollbar-thumb` | Scrollbar thumb color |
| `--mj-scroll-track-color` | `--mj-color-scrollbar-track` | Scrollbar track color |
| `--mj-scroll-thumb-width` | `6px` | Thumb/track width |
| `--mj-scroll-thumb-radius` | `--mj-radius-full` | Thumb border radius |
| `--mj-scroll-fade-duration` | `--mj-motion-duration-md` | Duration of thumb fade in/out |

## 10. States

- **default** — viewport at initial scroll position; scrollbar visible or hidden per `scrollbar-visibility`.
- **scrolling** — thumb position updates as the user scrolls; auto-hide fade timer resets.
- **thumb-hover** — thumb color lightens to provide drag affordance.
- **thumb-active** — thumb is being dragged.
- **overflow-hidden** — no scrollbar rendered when content does not overflow.

## 11. Behavior & interactions

The component overlays custom scrollbar elements on top of the viewport. On
browsers that support `scrollbar-width: none`, the native scrollbar is hidden
while a custom overlay scrollbar tracks the scroll position via the `scroll` event.
The custom thumb size is proportional to `viewport.clientHeight / viewport.scrollHeight`.

Dragging the thumb updates `viewport.scrollTop` proportionally. Clicking the
track above/below the thumb scrolls by one viewport height.

In `native` mode, custom overlay scrollbars are not rendered and the component
applies only `scrollbar-color` and `scrollbar-width` CSS properties.

The `scroll` event is throttled to `requestAnimationFrame` to avoid layout
thrash. The `mj-scroll-end` event uses the native `scrollend` event when
available and falls back to a 150 ms idle timer.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Tab` | Move focus to the viewport (which has `tabindex="0"`) |
| `Arrow Up` / `Arrow Down` | Scroll vertically by one line |
| `Arrow Left` / `Arrow Right` | Scroll horizontally by one line |
| `Page Up` / `Page Down` | Scroll vertically by one viewport height |
| `Home` | Scroll to the top |
| `End` | Scroll to the bottom |

## 13. Accessibility

- The viewport has `tabindex="0"` by default so keyboard users can scroll it
  without requiring a pointer.
- The viewport has `role="region"` and must be given an accessible name via
  `aria-label` on `<mj-scroll-area>` (a console warning is emitted in development
  mode if no label is provided).
- Custom scrollbar thumb elements are `aria-hidden="true"` and `tabindex="-1"`;
  they convey no information to assistive technology. Keyboard scroll is provided
  by the native browser behavior on the focused viewport.
- No color-only encoding is used in scrollbar styling.
- Touch devices use native momentum scroll (`-webkit-overflow-scrolling: touch`
  equivalent via `overflow: auto`).

## 14. Form participation

N/A — `<mj-scroll-area>` is a layout component and does not participate in forms.

## 15. Internationalization & RTL

In RTL mode the vertical scrollbar moves to the left side (inline-start) using
CSS logical properties. Horizontal scroll direction follows the writing mode.
`scrollLeft` values are handled with the RTL sign convention consistent with the
browser's native behavior.

## 16. Progressive enhancement / SSR

The server renders `<mj-scroll-area>` as a plain `<div>` with
`overflow: auto; max-height: var(--mj-scroll-area-height, 100%)`. Before upgrade
the native scrollbar is used. After upgrade the component overlays the custom
scrollbar. No content moves; only the scrollbar appearance changes.

## 17. Dependencies

- Section 6: Registry + base element helper; design-token stylesheet.
- `ResizeObserver` — to recalculate thumb size when the viewport or content
  dimensions change.
- `scrollend` event (native, with idle-timer fallback).

## 18. Edge cases & error handling

- **Content shorter than viewport** — scrollbar is hidden (when `overflow-y="auto"`); no thumb rendered.
- **Viewport height changes** — `ResizeObserver` recalculates thumb proportions.
- **Both `overflow-x` and `overflow-y` set to `"hidden"`** — no scroll possible; a console warning is emitted.
- **`native` mode on browsers without `scrollbar-color` support** — scrollbar renders in the native platform style; no fallback styling is applied.
- **Dynamically added tall content** — `MutationObserver` on the slot content triggers thumb recalculation.

## 19. Acceptance criteria

- [ ] Vertical scroll is keyboard-accessible via Arrow keys, Page Up/Down, Home, End.
- [ ] Custom thumb size is proportional to viewport/content height ratio.
- [ ] `scrollbar-visibility="always"` keeps the scrollbar visible even when content fits.
- [ ] `scrollbar-visibility="auto"` fades the scrollbar after 1.5 s of inactivity.
- [ ] `native` mode uses `scrollbar-color`/`scrollbar-width` without overlay elements.
- [ ] RTL mode positions the vertical scrollbar at the inline-start.
- [ ] `mj-scroll` event fires (throttled) on scroll; `mj-scroll-end` fires when scrolling stops.
- [ ] Viewport has `role="region"` with an accessible name.
- [ ] Custom thumb elements are `aria-hidden="true"`.
- [ ] Automated accessibility check passes with no violations.

## 20. Open questions

- Should `<mj-scroll-area>` expose a `snap` attribute that applies `scroll-snap-type` to the viewport, enabling integration with snap-based carousels?
- Is a `shadow-top`/`shadow-bottom` gradient overlay for indicating overflow content within scope of this component?
