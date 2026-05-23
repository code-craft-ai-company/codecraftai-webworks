# Aspect Ratio Box Spec

- **Tag:** `<mj-aspect-ratio>`
- **Class / file:** `MjAspectRatio` / `mjaspectratiobox.js`
- **Category:** Layout & content containers (§5.5)
- **Primary or Variant:** Primary
- **Synonyms covered:** Aspect ratio box
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-aspect-ratio>` constrains its slotted content to a fixed aspect ratio
regardless of the container width. It eliminates layout shift caused by images
and videos loading by reserving the correct amount of vertical space before the
media element is ready, and ensures consistent proportions for tiles, thumbnails,
map embeds, and video players.

## 2. When to use / when not to use

**Use** when you need a box whose height is always a fixed proportion of its
width — video embeds, image thumbnails, map frames, avatar placeholders.
**Do not use** when content must determine its own height — use a plain container.
**Do not use** as a replacement for the `aspect-ratio` CSS property on a single
known element; wrap with `<mj-aspect-ratio>` only when the proportion must be
enforced on a slot that could receive arbitrary content.

## 3. Anatomy

- **root** — an outer `<div>` sized by its width; the CSS `aspect-ratio` property
  is applied here, surfaced as `::part(root)`.
- **inner** — a `<div>` that is absolutely positioned to fill the root, surfaced
  as `::part(inner)`.
- **default slot** — slotted content fills the inner container.

## 4. Variants & modes

| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Custom ratio | `ratio="W/H"` | Any valid CSS `aspect-ratio` value (e.g. `"16/9"`, `"1"`, `"4/3"`) |
| Named ratios | `ratio="16x9"` etc. | Shorthand aliases: `16x9`, `4x3`, `1x1`, `3x2`, `9x16` resolved to CSS values |
| Contain | `fit="contain"` | Slotted content uses `object-fit: contain` (for `<img>`/`<video>` children) |
| Cover | `fit="cover"` (default) | Slotted content uses `object-fit: cover` |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `ratio` | string | `"16/9"` | Yes | CSS `aspect-ratio` value or named alias (`16x9`, `4x3`, `1x1`, `3x2`, `9x16`) |
| `fit` | `"cover"` \| `"contain"` \| `"fill"` \| `"none"` | `"cover"` | Yes | `object-fit` applied to a direct `<img>` or `<video>` child |
| `position` | string | `"center"` | Yes | `object-position` applied to a direct `<img>` or `<video>` child |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `resolvedRatio` | string (readonly) | The CSS `aspect-ratio` value actually applied after alias resolution |

## 7. Slots

| Slot | Description |
|------|-------------|
| (default) | The content to constrain; typically an `<img>`, `<video>`, `<iframe>`, or a container |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| — | — | — | — | No component-specific events |

## 9. CSS parts & custom properties

**Parts**
- `::part(root)` — the outer aspect-ratio container
- `::part(inner)` — the absolutely-positioned inner fill container

**Custom properties**
| Property | Default token | Description |
|----------|--------------|-------------|
| `--mj-ar-ratio` | resolved from `ratio` | CSS `aspect-ratio` value |
| `--mj-ar-fit` | resolved from `fit` | `object-fit` applied to media children |
| `--mj-ar-position` | resolved from `position` | `object-position` applied to media children |
| `--mj-ar-bg` | `--mj-color-surface-muted` | Background color of the container before media loads |

## 10. States

- **default** — box renders at full container width with the specified aspect ratio.
- **loading** — background color fills the reserved space before the media element reports a loaded state; prevents layout shift.

## 11. Behavior & interactions

The component applies `aspect-ratio` directly on the root host element. The inner
`<div>` fills the root with `position: absolute; inset: 0`. Slotted `<img>` and
`<video>` children have `object-fit` and `object-position` applied via a
`::slotted(img), ::slotted(video)` rule in the shadow stylesheet so authors need
not add these styles manually. No JavaScript calculations are performed for the
layout; pure CSS `aspect-ratio` is used.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| (none) | Component is not interactive; keyboard behavior is determined by slotted content |

## 13. Accessibility

- The component is purely presentational; its root `<div>` has no ARIA role.
- Slotted `<img>` elements must carry their own `alt` attributes; the component
  does not add or modify `alt` text.
- If the slot is used for a decorative background image, authors must add
  `aria-hidden="true"` to the slotted element.
- No focus management or live regions are needed.

## 14. Form participation

N/A — `<mj-aspect-ratio>` is a layout primitive and does not participate in forms.

## 15. Internationalization & RTL

No text content or direction-sensitive layout. `object-position` defaults to
`center`; authors can set a logical position value (e.g. `object-position: start
center`) when needed.

## 16. Progressive enhancement / SSR

The server can emit `<mj-aspect-ratio style="aspect-ratio: 16/9">` with a plain
`<img>` child. Before upgrade the browser applies native `aspect-ratio` from the
inline style. After upgrade the shadow root takes over and the inline style is
removed. No layout shift occurs if the ratio matches.

## 17. Dependencies

- Section 6: Registry + base element helper; design-token stylesheet.

## 18. Edge cases & error handling

- **Unknown `ratio` alias** — falls back to `16/9`; console warning emitted.
- **`ratio` set to `0` or a negative value** — clamped to `1/1`; console warning emitted.
- **Slotted content taller than the ratio box** — overflow is hidden by default
  via `overflow: hidden` on the inner container; authors can override via
  `::part(inner)`.
- **`<iframe>` children** — `object-fit` does not apply to `<iframe>`; the
  component's CSS does not attempt to apply it.
- **No slotted content** — box renders at the correct aspect ratio with the
  background color visible.

## 19. Acceptance criteria

- [ ] `ratio="16/9"` reserves height equal to `width * 9 / 16`.
- [ ] Named aliases (`16x9`, `4x3`, `1x1`, `3x2`, `9x16`) resolve to the correct CSS values.
- [ ] Slotted `<img>` receives `object-fit` from the `fit` attribute.
- [ ] Slotted `<img>` receives `object-position` from the `position` attribute.
- [ ] No layout shift when switching from SSR markup to upgraded component with matching ratio.
- [ ] Unknown `ratio` falls back to `16/9` with a console warning.
- [ ] Overflow content is clipped at the inner container boundary.
- [ ] Automated accessibility check passes with no violations.

## 20. Open questions

- Should `<mj-aspect-ratio>` expose a `height-based` mode where the height is fixed and the width scales proportionally (useful for full-height viewports)?
- Should named ratios be extensible via a static registration API, or is the fixed alias set sufficient?
