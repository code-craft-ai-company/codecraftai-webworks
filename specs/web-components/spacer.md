# Spacer Spec

- **Tag:** `<mj-spacer>`
- **Class / file:** `MjSpacer` / `mjspacer.js`
- **Category:** Layout & content containers (§5.5)
- **Primary or Variant:** Primary
- **Synonyms covered:** Flexible spacing primitive
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-spacer>` inserts a fixed or flexible blank space between sibling elements.
Inside a `<mj-stack>` or flex/grid container it can either consume a fixed size
from design tokens or grow to fill available space (`flex: 1 1 0`). It replaces
ad-hoc margin hacks and `<br>` abuse with an intentional, accessible, themeable
gap element.

## 2. When to use / when not to use

**Use** inside `<mj-stack>` or other flex containers to push trailing elements
to the far end (e.g., title on the left, action button on the right). **Use** for
a precise fixed gap that differs from the parent stack's uniform gap. **Do not
use** to add space around a component — use the component's own margin/padding
tokens or the parent stack's `gap` attribute. **Do not use** as a general
layout mechanism in place of a proper grid or stack.

## 3. Anatomy

- **root** — a single `<span>` with `display: block` (or `display: inline-block`
  in inline contexts) — surfaced as `::part(root)`. Contains no child content.

## 4. Variants & modes

| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Fixed | `size` set | Renders at a fixed width/height from the spacing token scale |
| Flexible (default) | no `size` | `flex: 1 1 0`; grows to fill available flex space |
| Axis-specific | `axis` set | Controls whether the fixed `size` applies to `width`, `height`, or both |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `size` | `"xs"` \| `"sm"` \| `"md"` \| `"lg"` \| `"xl"` \| `"2xl"` \| CSS length string | `""` | Yes | Fixed spacer dimension; when empty the spacer is flexible |
| `axis` | `"both"` \| `"horizontal"` \| `"vertical"` | `"both"` | Yes | Which axis `size` applies to; only relevant when `size` is set |

## 6. Properties

No complex properties beyond reflected attributes.

| Property | Type | Description |
|----------|------|-------------|
| `flex` | boolean (readonly) | `true` when the spacer is in flexible (no `size`) mode |

## 7. Slots

| Slot | Description |
|------|-------------|
| (none) | `<mj-spacer>` accepts no children; any slotted content is not rendered |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| — | — | — | — | No events; spacer is purely presentational |

## 9. CSS parts & custom properties

**Parts**
- `::part(root)` — the spacer block element

**Custom properties**
| Property | Default token | Description |
|----------|--------------|-------------|
| `--mj-spacer-size` | resolved from `size` token or `0` | Explicit dimension when in fixed mode |
| `--mj-spacer-flex` | `1 1 0` in flexible mode, `0 0 auto` in fixed mode | Flex shorthand applied to the root |

## 10. States

- **flexible** — `flex: 1 1 0`; expands to fill remaining space in a flex container.
- **fixed** — explicit width and/or height; `flex: 0 0 auto`.

## 11. Behavior & interactions

`<mj-spacer>` renders an empty block element. In flexible mode it uses
`flex: 1 1 0` so it absorbs all available space in a flex container. In fixed
mode `size` maps to a spacing token value and is applied to the appropriate axis.
The component contains no interactive content and performs no JavaScript beyond
attribute reflection.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| (none) | `<mj-spacer>` is not focusable and has no keyboard interaction |

## 13. Accessibility

- The root `<span>` has `aria-hidden="true"` and `role="none"` so screen readers
  skip it entirely.
- The spacer contains no text or interactive content and conveys no information
  to assistive technology.

## 14. Form participation

N/A — `<mj-spacer>` is a presentational layout element and does not participate
in forms.

## 15. Internationalization & RTL

In RTL contexts, `axis="horizontal"` spacing is applied using logical properties
(`inline-size`) so the behavior is consistent with the writing direction.
`axis="vertical"` uses `block-size`. No localizable strings are present.

## 16. Progressive enhancement / SSR

The server can render `<mj-spacer>` as an empty `<span>` with inline style
`flex: 1 1 0` or a fixed size. After upgrade the component replaces those inline
styles with shadow-root token-backed styles. No content is affected.

## 17. Dependencies

- Section 6: Registry + base element helper; design-token stylesheet.

## 18. Edge cases & error handling

- **Invalid `size` token name** — unknown names fall back to `0`; a console
  warning is emitted in development mode.
- **`size` with a raw CSS length** — arbitrary lengths are accepted as-is
  (e.g. `size="200px"`, `size="2rem"`).
- **`<mj-spacer>` outside a flex/grid container** — in block context the spacer
  renders with the specified fixed size or zero height if flexible; the flexible
  mode is effectively a no-op outside flex/grid.
- **Slotted children** — any children placed inside `<mj-spacer>` are not
  rendered (the shadow root's default slot is absent).

## 19. Acceptance criteria

- [ ] Default (no `size`) renders as a flex-grow element that fills available space.
- [ ] `size="lg"` renders at the `--mj-space-lg` token value.
- [ ] `axis="horizontal"` applies `size` only to the inline dimension.
- [ ] `axis="vertical"` applies `size` only to the block dimension.
- [ ] Root element is `aria-hidden="true"` with `role="none"`.
- [ ] Invalid token name falls back to `0` with a console warning.
- [ ] RTL uses logical properties for horizontal axis sizing.
- [ ] Automated accessibility check passes with no violations.

## 20. Open questions

- Should `<mj-spacer>` support a `min` and `max` attribute for clamped flexible sizing (e.g., grow but not beyond a maximum)?
- Is there value in a responsive `size` attribute that changes at breakpoints, or should that remain a CSS-only concern?
