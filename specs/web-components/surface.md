# Surface Spec

- **Tag:** `<mj-surface>`
- **Class / file:** `MjSurface` / `mjsurface.js`
- **Category:** Layout & content containers (§5.5)
- **Primary or Variant:** Primary
- **Synonyms covered:** Panel, Section, Container
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-surface>` is a generic content wrapper that provides a consistent
elevation, background, padding, and radius treatment. It consolidates the Panel,
Section, and Container synonyms into a single component configured by attributes,
avoiding duplicate implementations for what is fundamentally the same layout
primitive with different visual weight.

## 2. When to use / when not to use

**Use** for any rectangular region that needs a distinct background, border, or
shadow to separate it from its surroundings — e.g., a settings panel, a page
section, a centered content container. **Do not use** for a named content card
with media/header/footer — use `<mj-card>` instead. **Do not use** as a
transparent layout wrapper with no visual differentiation — use `<mj-stack>` or
`<mj-grid>` for invisible spacing primitives.

## 3. Anatomy

- **root** — the single container element; rendered as `<section>` when
  `role-hint="section"` is set, as `<div>` otherwise.
- **default slot** — all child content placed inside the surface.

## 4. Variants & modes

| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Flat | `elevation="flat"` | transparent background, no shadow, no border |
| Outlined | `elevation="outlined"` | themed border, no shadow |
| Raised | `elevation="raised"` | `--mj-elevation-2` shadow |
| Overlay | `elevation="overlay"` | `--mj-elevation-4` shadow; used for floating panels |
| Section | `role-hint="section"` | root renders as `<section>`; expects a heading child |
| Container | `max-width` set | centers content at a max width with auto side margins |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `elevation` | `"flat"` \| `"outlined"` \| `"raised"` \| `"overlay"` | `"flat"` | Yes | Visual depth treatment |
| `padding` | `"none"` \| `"sm"` \| `"md"` \| `"lg"` \| `"xl"` | `"md"` | Yes | Internal padding size using spacing tokens |
| `radius` | `"none"` \| `"sm"` \| `"md"` \| `"lg"` \| `"full"` | `"md"` | Yes | Corner radius using radius tokens |
| `role-hint` | `"generic"` \| `"section"` | `"generic"` | Yes | Controls the rendered HTML element and ARIA semantics |
| `max-width` | string | `""` | Yes | CSS max-width value; when set, surface centers itself with auto margins |
| `full-bleed` | boolean | `false` | Yes | Removes padding and radius; content reaches the edges |

## 6. Properties

No complex properties beyond reflected attributes.

| Property | Type | Description |
|----------|------|-------------|
| `contentElement` | `HTMLElement` | Read-only reference to the internal root element for programmatic measurement |

## 7. Slots

| Slot | Description |
|------|-------------|
| (default) | All surface content |

## 8. Events

No component-specific events. The surface is purely structural and emits no
custom events.

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| — | — | — | — | No events; see universal lifecycle events in §3 |

## 9. CSS parts & custom properties

**Parts**
- `::part(root)` — the outer container element

**Custom properties**
| Property | Default token | Description |
|----------|--------------|-------------|
| `--mj-surface-bg` | `--mj-color-surface` | Background color |
| `--mj-surface-border` | `--mj-color-border` | Border color when `elevation="outlined"` |
| `--mj-surface-shadow` | varies by elevation | Box shadow |
| `--mj-surface-radius` | resolved from `radius` attribute | Corner radius |
| `--mj-surface-padding` | resolved from `padding` attribute | Internal padding |
| `--mj-surface-max-width` | `none` | Max content width; mirrors `max-width` attribute |

## 10. States

- **default** — renders with the configured elevation and padding.
- **focus-visible** — no focus ring on the surface itself; child elements manage their own focus styles.

## 11. Behavior & interactions

`<mj-surface>` is fully presentational. It applies design tokens to its shadow
root container and slots all child content without intercepting pointer or
keyboard events. `ResizeObserver` is used internally only if a consumer sets
`max-width` and the component needs to emit a resize notification — otherwise no
observers are created. The component does not add scroll, overflow clipping, or
event delegation.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| (none) | Surface itself is not interactive; keyboard behavior is entirely determined by slotted content |

## 13. Accessibility

- When `role-hint="section"` the root is a `<section>` element, which has an
  implicit `region` landmark only when it has an accessible name. Authors must
  supply a heading child or `aria-label` on `<mj-surface>` to activate the
  landmark.
- When `role-hint="generic"` (default) the rendered `<div>` has no implicit ARIA
  role; no extra roles are added by the component.
- The surface does not alter the focus order or tab sequence of its children.

## 14. Form participation

N/A — `<mj-surface>` is a layout wrapper and does not participate in forms.

## 15. Internationalization & RTL

All spacing, padding, and border-radius use CSS logical properties so the
component is RTL-ready without component-level changes. No localizable strings
are rendered by this component.

## 16. Progressive enhancement / SSR

The server can render a plain `<section>` or `<div>` with inline or class-based
styles. After upgrade the component replaces those with design-token-backed
shadow styles. Child content is unchanged; no layout shift beyond shadow-root
padding adjustments.

## 17. Dependencies

- Section 6: Registry + base element helper; design-token stylesheet.

## 18. Edge cases & error handling

- **`role-hint="section"` without a heading child** — renders a `<section>` but
  the landmark is not announced by screen readers due to the missing name;
  a console warning is emitted in development mode.
- **`full-bleed` + `padding`** — `full-bleed` overrides `padding`; padding is
  set to zero regardless of the `padding` attribute value.
- **Very long `max-width` values** — validated against a CSS length pattern;
  invalid values fall back to `none` and a console warning is emitted.
- **Nested surfaces** — stacking elevation values is intentional; authors are
  responsible for ensuring visual hierarchy is coherent.

## 19. Acceptance criteria

- [ ] `elevation` attribute applies correct shadow/border token combination for each value.
- [ ] `padding` attribute maps to the correct spacing token at each size.
- [ ] `radius` attribute maps to the correct radius token at each size.
- [ ] `role-hint="section"` renders a `<section>` element in the shadow root.
- [ ] `max-width` centers the surface with auto side margins.
- [ ] `full-bleed` removes all padding and radius.
- [ ] RTL layout uses logical properties throughout.
- [ ] No custom events are emitted; no event listeners are leaked on disconnect.
- [ ] Automated accessibility check passes with no violations.
- [ ] SSR upgrade produces no visible layout shift.

## 20. Open questions

- Should `<mj-surface>` support a `color-scheme` attribute to independently toggle light/dark regardless of the page theme?
- Is a `sticky` attribute for position sticky surfaces within the scope of this component or should that be a CSS concern for consumers?
