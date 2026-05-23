# Divider Spec

- **Tag:** `<mj-divider>`
- **Class / file:** `MjDivider` / `mjdivider.js`
- **Category:** Layout & content containers (§5.5)
- **Primary or Variant:** Primary
- **Synonyms covered:** Separator
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-divider>` provides a visual and/or semantic line that separates adjacent
content regions. When it conveys structure (e.g., separating groups in a menu or
list), it uses `role="separator"`; when it is purely decorative it uses
`role="none"`. It supports horizontal and vertical orientations, optional label
text, and full theming via design tokens.

## 2. When to use / when not to use

**Use** to visually separate groups of related items in a menu, list, form
section, or navigation panel. **Use** the semantic variant when the separation
conveys grouping that would otherwise not be evident to screen-reader users.
**Do not use** as a structural layout tool — use `<mj-stack>` gap or `<mj-grid>`
for layout spacing. **Do not use** if a heading already provides sufficient
grouping context; redundant separators add visual noise.

## 3. Anatomy

- **root** — an `<hr>` element (horizontal default) or a `<div>` element
  (when `orientation="vertical"` or `label` is present, since `<hr>` cannot hold
  content); surfaced as `::part(root)`.
- **label** — optional centered label text inside the divider line (slot `label`
  or `label` attribute); surfaced as `::part(label)`.
- **line-start** / **line-end** — the line segments flanking the label (rendered
  only when a label is present); surfaced as `::part(line-start)` and
  `::part(line-end)`.

## 4. Variants & modes

| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Horizontal (default) | `orientation="horizontal"` | Full-width line across the block axis |
| Vertical | `orientation="vertical"` | Line along the inline axis within a flex container |
| Semantic | `decorative` absent | `role="separator"` (conveying grouping) |
| Decorative | `decorative` boolean | `role="none"` + `aria-hidden="true"` |
| Labeled | `label` set | Line with centered text label |
| Dashed | `variant="dashed"` | Dashed border instead of solid |
| Dotted | `variant="dotted"` | Dotted border |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `orientation` | `"horizontal"` \| `"vertical"` | `"horizontal"` | Yes | Axis of the dividing line |
| `decorative` | boolean | `false` | Yes | When set, the divider has `role="none"` and `aria-hidden="true"` |
| `label` | string | `""` | Yes | Plain-text label centered on the line |
| `variant` | `"solid"` \| `"dashed"` \| `"dotted"` | `"solid"` | Yes | Line style |
| `thickness` | `"thin"` \| `"medium"` \| `"thick"` | `"thin"` | Yes | Line thickness using border-width tokens |
| `spacing` | `"none"` \| `"xs"` \| `"sm"` \| `"md"` \| `"lg"` | `"md"` | Yes | Margin above and below (horizontal) or before and after (vertical) |

## 6. Properties

No complex properties beyond reflected attributes.

| Property | Type | Description |
|----------|------|-------------|
| `isDecorative` | boolean (readonly) | `true` when the divider has `role="none"` |

## 7. Slots

| Slot | Description |
|------|-------------|
| `label` | Rich label content centered on the divider line; replaces the `label` attribute text |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| — | — | — | — | No component-specific events; divider is purely presentational |

## 9. CSS parts & custom properties

**Parts**
- `::part(root)` — the root element (`<hr>` or `<div>`)
- `::part(label)` — the label text wrapper
- `::part(line-start)` — line segment before the label
- `::part(line-end)` — line segment after the label

**Custom properties**
| Property | Default token | Description |
|----------|--------------|-------------|
| `--mj-divider-color` | `--mj-color-border` | Line color |
| `--mj-divider-thickness` | resolved from `thickness` | Border width |
| `--mj-divider-spacing` | resolved from `spacing` | Block-axis margin (horizontal) or inline-axis margin (vertical) |
| `--mj-divider-label-color` | `--mj-color-text-secondary` | Label text color |
| `--mj-divider-label-bg` | `--mj-color-surface` | Label text background (for line-overlap masking) |
| `--mj-divider-label-gap` | `--mj-space-3` | Gap between the label and each line segment |

## 10. States

- **default** — solid line with the configured orientation and spacing.
- **labeled** — two line segments flanking centered label text.
- **decorative** — `aria-hidden="true"`, `role="none"`; ignored by AT.

## 11. Behavior & interactions

`<mj-divider>` is purely presentational. When `label` is set (or the `label`
slot has content), the root is rendered as a `<div>` with a flex layout and two
`<span>` line segments flanking the label. The line segments use a bottom border
on a thin `<span>` with `flex: 1` to produce the extending line effect.

When no label is set, the root is an `<hr>` element (horizontal) or a `<div>`
with `border-inline-start` (vertical). The `<hr>` is the preferred element for
horizontal semantic dividers because it carries the `separator` role implicitly.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| (none) | `<mj-divider>` is not focusable and has no keyboard interaction |

## 13. Accessibility

- Horizontal semantic divider: root is `<hr>` with implicit `role="separator"`.
  `aria-orientation="horizontal"` is the default and need not be set explicitly.
- Vertical semantic divider: root is `<div role="separator" aria-orientation="vertical">`.
- Decorative divider: `aria-hidden="true"` and `role="none"` regardless of element.
- When a `label` is present and the divider is semantic, `aria-label` is set on
  the root to include the label text so screen readers can announce "separator:
  Or" or similar.
- The label slot content must be text-only for semantic dividers; interactive
  content in the label is not supported.

## 14. Form participation

N/A — `<mj-divider>` is a structural/decorative component and does not participate
in forms.

## 15. Internationalization & RTL

In RTL mode, `orientation="vertical"` uses `border-inline-end` instead of
`border-inline-start`, placing the visual divider on the correct side. The
`spacing` margin uses logical properties (`margin-block` for horizontal,
`margin-inline` for vertical). The `label` attribute string is rendered as-is;
authors supply localized text.

## 16. Progressive enhancement / SSR

The server renders `<mj-divider>` as a plain `<hr>` or `<div>` with a bottom
border via inline style. Before upgrade the line is displayed as a native
horizontal rule or styled div. After upgrade the component applies token-backed
colors, spacing, and the labeled layout if a label is present. No content changes;
the only visual delta is the token application.

## 17. Dependencies

- Section 6: Registry + base element helper; design-token stylesheet.

## 18. Edge cases & error handling

- **`label` + `orientation="vertical"`** — labeled dividers are only supported
  horizontally; a console warning is emitted and the label is hidden when
  orientation is vertical.
- **`label` slot contains interactive content** — interactive children inside a
  divider label are flagged with a console warning; this pattern is not supported
  and produces an invalid ARIA structure.
- **`decorative` and `label` both set** — `decorative` takes precedence; the
  label renders visually but the root is `aria-hidden="true"`.
- **Very long label text** — label wraps; line segments shrink to their minimum
  size and may disappear on very narrow containers.

## 19. Acceptance criteria

- [ ] Default (horizontal, no label) renders as `<hr>` with `role="separator"`.
- [ ] `orientation="vertical"` renders as `<div role="separator" aria-orientation="vertical">`.
- [ ] `decorative` adds `aria-hidden="true"` and `role="none"`.
- [ ] `label` attribute renders label text centered with line segments on each side.
- [ ] `variant="dashed"` renders a dashed border.
- [ ] `thickness="thick"` applies the correct border-width token.
- [ ] `spacing="lg"` applies the correct block-axis margin token.
- [ ] RTL mode uses logical CSS properties for spacing and border placement.
- [ ] Semantic divider with label sets `aria-label` on the root to include label text.
- [ ] Automated accessibility check passes with no violations.

## 20. Open questions

- Should `<mj-divider>` support a gradient color via a `gradient` attribute (e.g., fade from the border color to transparent at the edges) for decorative use cases?
- Should the label support an `icon` attribute to render a design-system icon instead of text (e.g., a small star or "or" symbol)?
