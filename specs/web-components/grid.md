# Grid Spec

- **Tag:** `<mj-grid>`
- **Class / file:** `MjGrid` / `mjgrid.js`
- **Category:** Layout & content containers (§5.5)
- **Primary or Variant:** Primary
- **Synonyms covered:** Masonry layout (variant via `layout="masonry"`)
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-grid>` is a responsive grid layout primitive that places slotted children
into a CSS Grid or CSS Masonry layout. It exposes column count, gap, and
min-column-width as design-token-backed attributes, allowing consistent spacing
across the library without per-page CSS overrides. The Masonry variant uses the
CSS `masonry` value for `grid-template-rows` (progressive enhancement) with a
JavaScript column-stacking fallback.

## 2. When to use / when not to use

**Use** when slotted items should align to a multi-column grid — card galleries,
image grids, dashboard tiles, form field rows. **Use** `layout="masonry"` for
variable-height content where strict row alignment is undesirable. **Do not use**
for a single horizontal or vertical sequence — use `<mj-stack>`. **Do not use**
when items need explicit named grid areas with complex spanning — author the CSS
Grid directly on a `<mj-surface>` or plain element instead.

## 3. Anatomy

- **root** — a single `<div>` with `display: grid` applied, surfaced as
  `::part(root)`.
- **default slot** — all grid children rendered into the root container.

## 4. Variants & modes

| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Auto-fill | `columns="auto"` (default) | `repeat(auto-fill, minmax(--mj-grid-min-col, 1fr))` |
| Fixed columns | `columns="N"` (integer) | `repeat(N, 1fr)` — N columns always |
| Masonry | `layout="masonry"` | uses CSS `masonry` if supported, JS fallback otherwise |
| Dense packing | `dense` boolean | adds `grid-auto-flow: dense` to fill gaps |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `columns` | `"auto"` \| integer string | `"auto"` | Yes | Number of columns or `"auto"` for responsive fill |
| `min-col-width` | string | `"16rem"` | Yes | CSS length; minimum column width in auto-fill mode |
| `gap` | `"none"` \| `"xs"` \| `"sm"` \| `"md"` \| `"lg"` \| `"xl"` | `"md"` | Yes | Gap between cells using spacing tokens |
| `col-gap` | `"none"` \| `"xs"` \| `"sm"` \| `"md"` \| `"lg"` \| `"xl"` | `""` | Yes | Column-specific gap override; falls back to `gap` |
| `row-gap` | `"none"` \| `"xs"` \| `"sm"` \| `"md"` \| `"lg"` \| `"xl"` | `""` | Yes | Row-specific gap override; falls back to `gap` |
| `layout` | `"grid"` \| `"masonry"` | `"grid"` | Yes | Layout algorithm |
| `dense` | boolean | `false` | Yes | Enables dense auto-placement to fill holes |
| `align-items` | `"start"` \| `"center"` \| `"end"` \| `"stretch"` | `"stretch"` | Yes | Cross-axis alignment of all cells |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `masonrySupported` | boolean (readonly) | `true` if the browser natively supports CSS masonry; `false` when the JS fallback is active |

## 7. Slots

| Slot | Description |
|------|-------------|
| (default) | Grid child elements; each direct child occupies one or more grid cells |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-grid-layout` | `{ columns: number, masonry: boolean }` | No | No | Emitted after the grid recalculates its column count (resize or attribute change) |

## 9. CSS parts & custom properties

**Parts**
- `::part(root)` — the grid container element

**Custom properties**
| Property | Default token | Description |
|----------|--------------|-------------|
| `--mj-grid-columns` | resolved from `columns` attribute | Explicit column count or `auto` |
| `--mj-grid-min-col` | resolved from `min-col-width` | Minimum column width for auto-fill |
| `--mj-grid-gap` | resolved from `gap` attribute | Uniform gap between cells |
| `--mj-grid-col-gap` | `--mj-grid-gap` | Column gap (overrides gap when set) |
| `--mj-grid-row-gap` | `--mj-grid-gap` | Row gap (overrides gap when set) |
| `--mj-grid-align` | `stretch` | `align-items` value |

## 10. States

- **default** — grid renders children into the configured columns.
- **resizing** — `ResizeObserver` triggers layout recalculation; `mj-grid-layout` event fires.
- **masonry-fallback** — when `layout="masonry"` and native support is absent, a JS stacking algorithm is used; `masonrySupported` is `false`.

## 11. Behavior & interactions

`<mj-grid>` uses a `ResizeObserver` on itself to detect container width changes
and recalculate the effective column count in auto-fill mode. In masonry mode
with no native support, the component measures each child's height after load/
resize and repositions them into the shortest column using absolute positioning
on the root. The root's height is then set explicitly. This calculation is
debounced with `requestAnimationFrame` to avoid layout thrash. On disconnect,
the `ResizeObserver` and any child `ResizeObserver`s are disconnected.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| (none) | Grid itself is not interactive; keyboard behavior is determined entirely by slotted children |

## 13. Accessibility

- `<mj-grid>` is presentational. The root `<div>` has no ARIA role; grid items
  carry their own semantics.
- Masonry reordering via the JS fallback preserves DOM order (source order ==
  visual order) so screen reader and keyboard order remain coherent.
- Authors must not rely on visual column order for logical reading order; content
  must make sense in source order.

## 14. Form participation

N/A — `<mj-grid>` is a layout primitive and does not participate in forms.

## 15. Internationalization & RTL

Column direction follows the writing mode. In RTL contexts columns fill from
the inline-end side. CSS Grid with logical properties handles this automatically;
the masonry JS fallback reads `direction` from the computed style to determine
column fill direction.

## 16. Progressive enhancement / SSR

The server renders children as a block-level list or a plain flex/grid container.
After upgrade the component applies the token-backed CSS Grid declaration via the
shadow root stylesheet. Because the default slot is used, no children are moved
in the DOM.

## 17. Dependencies

- Section 6: Registry + base element helper; design-token stylesheet.
- `ResizeObserver` (native browser API, no polyfill bundled).

## 18. Edge cases & error handling

- **`columns` set to 0 or a negative integer** — clamped to 1; console warning emitted.
- **`min-col-width` larger than the container** — browser auto-fill produces a single column; no error.
- **`layout="masonry"` with `dense`** — `dense` has no effect in masonry mode; console warning emitted.
- **Slotted children added or removed** — `MutationObserver` triggers masonry recalculation.
- **Children with unknown dimensions (images loading)** — `load` events on `<img>` children trigger a masonry recalculation.

## 19. Acceptance criteria

- [ ] `columns="3"` always renders exactly 3 columns regardless of container width.
- [ ] `columns="auto"` produces responsive fill based on `min-col-width`.
- [ ] `gap` attribute maps to the correct spacing token.
- [ ] `col-gap` and `row-gap` override `gap` independently.
- [ ] `layout="masonry"` activates native masonry when available.
- [ ] JS masonry fallback stacks items into the shortest column; DOM order is preserved.
- [ ] `mj-grid-layout` event fires with correct `columns` count after resize.
- [ ] `dense` adds `grid-auto-flow: dense`.
- [ ] RTL layout fills columns from the correct side.
- [ ] `ResizeObserver` is disconnected on `disconnectedCallback`.
- [ ] Automated accessibility check passes with no violations.

## 20. Open questions

- Should `<mj-grid>` support named grid areas via a `template` attribute (e.g., `"a b b / c b b"`) for more complex layouts, or should that remain a pure CSS concern?
- Is the masonry JS fallback worth the complexity given CSS masonry browser support trajectory? Should the fallback be a separate opt-in?
