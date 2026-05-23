# Media Object Spec

- **Tag:** `<mj-media-object>`
- **Class / file:** `MjMediaObject` / `mjmediaobject.js`
- **Category:** Layout & content containers (§5.5)
- **Primary or Variant:** Primary
- **Synonyms covered:** Media-beside-text layout primitive
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-media-object>` is a layout primitive that places a fixed-size media element
(image, avatar, icon) beside a variable-width text block. It is the foundational
pattern behind comment rows, list items with avatars, notification rows, and
settings rows — any pattern where a small visual is anchored to the left or right
of accompanying text.

## 2. When to use / when not to use

**Use** when a fixed-size image or icon anchors a block of text to one side —
comment entries, list items with avatars, chat messages, settings rows, email
preview rows. **Do not use** for a full-bleed media section — use `<mj-card>`
with the media slot. **Do not use** for a two-column grid with equal-width
content — use `<mj-grid>`.

## 3. Anatomy

- **root** — the flex container; surfaced as `::part(root)`.
- **media** — the fixed-size region holding the image, avatar, or icon (slot
  `media`); surfaced as `::part(media)`.
- **content** — the flexible text region (default slot); surfaced as
  `::part(content)`.

## 4. Variants & modes

| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Media start (default) | `media-position="start"` | Media on the inline-start side |
| Media end | `media-position="end"` | Media on the inline-end side |
| Stack below breakpoint | `stack-at` set | At container widths below `stack-at`, media stacks above content |
| Center-aligned | `align="center"` | Media and content aligned to the vertical center |
| Top-aligned | `align="start"` (default) | Media aligned to the top of the content |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `media-position` | `"start"` \| `"end"` | `"start"` | Yes | Which side the media region appears on |
| `gap` | `"none"` \| `"xs"` \| `"sm"` \| `"md"` \| `"lg"` \| `"xl"` | `"md"` | Yes | Gap between the media and content regions |
| `align` | `"start"` \| `"center"` \| `"end"` | `"start"` | Yes | Cross-axis (vertical) alignment of the media relative to the content |
| `stack-at` | string | `""` | Yes | CSS container query or media query breakpoint at which the layout stacks vertically |
| `media-size` | string | `""` | Yes | Explicit width for the media region (e.g. `"3rem"`); overrides token default |

## 6. Properties

No complex properties beyond reflected attributes.

| Property | Type | Description |
|----------|------|-------------|
| `contentElement` | `HTMLElement` (readonly) | Reference to the internal content wrapper for measurement |

## 7. Slots

| Slot | Description |
|------|-------------|
| `media` | The fixed-size media element (image, avatar, icon) |
| (default) | Text content, titles, descriptions, metadata beside the media |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| — | — | — | — | No component-specific events; this is a purely presentational layout component |

## 9. CSS parts & custom properties

**Parts**
- `::part(root)` — the flex container
- `::part(media)` — the media region wrapper
- `::part(content)` — the content region wrapper

**Custom properties**
| Property | Default token | Description |
|----------|--------------|-------------|
| `--mj-media-object-gap` | resolved from `gap` attribute | Gap between media and content |
| `--mj-media-object-media-size` | `3rem` | Width of the media region; overridden by `media-size` attribute |
| `--mj-media-object-align` | resolved from `align` attribute | Flex `align-items` value |

## 10. States

- **default** — horizontal layout with media at the start.
- **stacked** — vertical layout when `stack-at` breakpoint is met.

## 11. Behavior & interactions

`<mj-media-object>` is a pure CSS flexbox layout component. No JavaScript
calculations are performed for layout. When `stack-at` is provided, a CSS
`@container` or `@media` rule is applied via the shadow stylesheet to switch to
`flex-direction: column` at the specified breakpoint. No event listeners or
observers are set up beyond those required by the base element helper.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| (none) | Component is not interactive; keyboard behavior is determined by slotted content |

## 13. Accessibility

- The root `<div>` has no ARIA role; the component is presentational.
- The media slot and content slot carry their own semantics (e.g., `<img alt="...">`).
- The component does not alter the reading order; DOM source order matches visual
  order in `media-position="start"` mode.
- In `media-position="end"` mode visual order does not match DOM order; authors
  should verify that the logical reading order (DOM order) remains sensible.

## 14. Form participation

N/A — `<mj-media-object>` is a layout primitive and does not participate in forms.

## 15. Internationalization & RTL

All spacing and positioning use CSS logical properties (`margin-inline-start`,
`padding-inline-end`) so the media-to-content direction follows the writing mode
automatically in RTL contexts. No localizable strings are rendered by the component.

## 16. Progressive enhancement / SSR

The server renders the media and content as adjacent elements with inline flex
styles. Before upgrade they are displayed side-by-side via native flex support.
After upgrade the component applies token-backed spacing and part hooks. No
content changes; only styling tokens are swapped.

## 17. Dependencies

- Section 6: Registry + base element helper; design-token stylesheet.

## 18. Edge cases & error handling

- **No media slot content** — media region collapses to zero width; content takes
  full width.
- **No content slot content** — content region is empty; media region is visible.
- **`media-size` set to `0` or a negative value** — clamped to `1px`; console
  warning emitted.
- **`stack-at` set to an unsupported query** — CSS engine ignores the rule; no
  stacking occurs; console warning emitted in development mode.

## 19. Acceptance criteria

- [ ] Media slot content appears at the inline-start by default.
- [ ] `media-position="end"` moves media to the inline-end side.
- [ ] `gap` attribute applies the correct spacing token between media and content.
- [ ] `align` controls vertical alignment of the media and content.
- [ ] `stack-at` triggers vertical stacking at the specified breakpoint.
- [ ] `media-size` overrides the default media region width.
- [ ] RTL layout uses logical properties; media-start means inline-start in both LTR and RTL.
- [ ] Automated accessibility check passes with no violations.

## 20. Open questions

- Should `<mj-media-object>` support a `media-position="top"` and `"bottom"` for
  vertically-oriented media-plus-text layouts (similar to a figure + caption
  arrangement), or is that a separate use case for `<mj-card>`?
- Should `stack-at` accept a named breakpoint token (e.g., `"sm"`) from the design
  system, or should it always be a raw CSS media/container query value?
