# Stack Spec

- **Tag:** `<mj-stack>`
- **Class / file:** `MjStack` / `mjstack.js`
- **Category:** Layout & content containers (§5.5)
- **Primary or Variant:** Primary
- **Synonyms covered:** Directional spacing layout primitive
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-stack>` is a one-dimensional layout primitive that arranges slotted children
along a single axis (horizontal or vertical) with uniform gap spacing from design
tokens. It replaces ad-hoc flexbox CSS in templates and ensures consistent
inter-element spacing without per-component style overrides.

## 2. When to use / when not to use

**Use** when you need a linear sequence of elements with consistent spacing —
button rows, form field columns, icon-label pairs, navigation link lists.
**Do not use** for two-dimensional layouts — use `<mj-grid>`. **Do not use**
when items need individually varying gaps or complex alignment across two axes.
**Do not use** as a replacement for list semantics — use `<ul>`/`<ol>` for lists
and style them separately if needed.

## 3. Anatomy

- **root** — a `<div>` with `display: flex` applied, surfaced as `::part(root)`.
- **default slot** — all direct children become flex items.

## 4. Variants & modes

| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Vertical (default) | `direction="vertical"` | `flex-direction: column` |
| Horizontal | `direction="horizontal"` | `flex-direction: row` |
| Wrap | `wrap` boolean | `flex-wrap: wrap` — items wrap to new lines |
| Reversed | `reverse` boolean | `flex-direction: column-reverse` or `row-reverse` |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `direction` | `"vertical"` \| `"horizontal"` | `"vertical"` | Yes | Primary axis of the stack |
| `gap` | `"none"` \| `"xs"` \| `"sm"` \| `"md"` \| `"lg"` \| `"xl"` | `"md"` | Yes | Space between children using spacing tokens |
| `align` | `"start"` \| `"center"` \| `"end"` \| `"stretch"` \| `"baseline"` | `"stretch"` | Yes | Cross-axis alignment (`align-items`) |
| `justify` | `"start"` \| `"center"` \| `"end"` \| `"between"` \| `"around"` \| `"evenly"` | `"start"` | Yes | Main-axis distribution (`justify-content`) |
| `wrap` | boolean | `false` | Yes | Allows items to wrap onto multiple lines |
| `reverse` | boolean | `false` | Yes | Reverses the flex direction |
| `inline` | boolean | `false` | Yes | Uses `display: inline-flex` instead of `display: flex` |

## 6. Properties

No complex properties beyond reflected attributes.

| Property | Type | Description |
|----------|------|-------------|
| `childCount` | number (readonly) | Number of direct slotted children; useful for styling via JS |

## 7. Slots

| Slot | Description |
|------|-------------|
| (default) | Stack children; each becomes a flex item |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| — | — | — | — | No component-specific events; stack is purely presentational |

## 9. CSS parts & custom properties

**Parts**
- `::part(root)` — the flex container element

**Custom properties**
| Property | Default token | Description |
|----------|--------------|-------------|
| `--mj-stack-gap` | resolved from `gap` attribute | Gap between flex items |
| `--mj-stack-direction` | resolved from `direction` + `reverse` | Flex direction value |
| `--mj-stack-align` | resolved from `align` | `align-items` value |
| `--mj-stack-justify` | resolved from `justify` | `justify-content` value |

## 10. States

- **default** — flex container with configured gap and alignment.
- No hover, focus, or interactive states; the stack does not intercept user input.

## 11. Behavior & interactions

`<mj-stack>` renders a single shadow-root flex container and slots all children
into it. Attribute changes update the corresponding CSS custom property on the
host; no JavaScript layout logic runs. Because children are slotted rather than
moved, slotchange events trigger no recalculation — all layout is declarative CSS.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| (none) | Stack is not interactive; keyboard behavior is determined entirely by slotted children |

## 13. Accessibility

- The root `<div>` has no ARIA role; it is presentational.
- `reverse` attribute reverses the visual order but not the DOM order; this can
  create a mismatch between reading order and visual order. Authors should use
  `reverse` only when the source order is still logical (e.g., reversing a list
  that reads equally well in both directions, or for RTL-specific adjustments).
- A warning is logged in development mode when `reverse` is set on a stack
  containing focusable children, reminding authors to verify focus order.

## 14. Form participation

N/A — `<mj-stack>` is a layout primitive and does not participate in forms.

## 15. Internationalization & RTL

`direction="horizontal"` uses `flex-direction: row` which automatically respects
the writing direction when CSS logical properties are applied to the gap. For RTL
the visual order of horizontal stacks is mirrored by the browser. The `reverse`
attribute inverts the flex direction on top of the writing mode; this may be
needed to counteract automatic RTL reversal in specific cases and must be
documented in usage examples.

## 16. Progressive enhancement / SSR

The server renders children as a plain block or inline sequence. After upgrade
the component applies the flex container via shadow DOM. No children are moved;
the only visible change is the addition of gap and alignment.

## 17. Dependencies

- Section 6: Registry + base element helper; design-token stylesheet.

## 18. Edge cases & error handling

- **Single child** — renders normally; gap has no visible effect.
- **Zero children** — root collapses; no visible output.
- **`wrap` + `reverse`** — wrap direction also reverses; this is standard flexbox
  behavior and is intentional.
- **`justify="between"` with one child** — single child is placed at the start;
  no visual gap artifact.
- **`inline` + block-level children** — children establish their own block
  formatting context; the stack container is inline-flex.

## 19. Acceptance criteria

- [ ] `direction="horizontal"` applies `flex-direction: row`.
- [ ] `direction="vertical"` applies `flex-direction: column`.
- [ ] `gap` attribute maps to the correct spacing token.
- [ ] `align` attribute sets `align-items` correctly for each value.
- [ ] `justify` attribute sets `justify-content` correctly for each value.
- [ ] `wrap` boolean enables `flex-wrap: wrap`.
- [ ] `reverse` combines with `direction` to produce the correct reversed flex direction.
- [ ] `inline` switches to `display: inline-flex`.
- [ ] RTL horizontal stacks mirror visual order.
- [ ] Development warning fires when `reverse` is used with focusable children.
- [ ] Automated accessibility check passes with no violations.

## 20. Open questions

- Should `<mj-stack>` support a `divider` slot or attribute to automatically
  insert `<mj-divider>` between each child, or should authors slot dividers manually?
- Is a responsive `direction` attribute (e.g., `direction="vertical md:horizontal"`)
  within scope for this component or is that a CSS media-query concern?
