# Hero Section Spec

- **Tag:** `<mj-hero>`
- **Class / file:** `MjHero` / `mjherosection.js`
- **Category:** Layout & content containers (§5.5)
- **Primary or Variant:** Primary
- **Synonyms covered:** Hero banner, Prominent intro banner
- **Phase:** P2
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-hero>` is a prominent full-width or full-viewport-height introductory banner
that combines a background image or color, a heading, a supporting body, and
optional action buttons. It solves the need for a visually impactful page entry
point that still meets WCAG contrast requirements, provides a logical document
hierarchy, and degrades gracefully when scripting is unavailable.

## 2. When to use / when not to use

**Use** at the top of a marketing page, landing page, or feature overview to
establish context and direct the user's primary action. **Do not use** inside a
narrow column or panel where the full-width impact is lost — use `<mj-card>` or
`<mj-surface>` instead. **Do not use** as a generic section wrapper; its visual
weight implies primary importance.

## 3. Anatomy

- **root** — outer `<section>` element carrying the landmark; surfaced as `::part(root)`.
- **background** — `<div>` holding the background image or color; surfaced as
  `::part(background)`. Marked `aria-hidden="true"`.
- **overlay** — a semi-transparent scrim over the background for text contrast;
  surfaced as `::part(overlay)`.
- **content** — centered content wrapper; surfaced as `::part(content)`.
- **heading** — the primary `<h1>`–`<h3>` element (rendered from the `heading`
  attribute or `heading` slot); surfaced as `::part(heading)`.
- **body** — supporting paragraph text (slot `body`); surfaced as `::part(body)`.
- **actions** — action button row (slot `actions`); surfaced as `::part(actions)`.
- **media** — optional foreground media (slot `media`) rendered over the background.

## 4. Variants & modes

| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Default | — | Background color, centered content, standard padding |
| Image background | `bg-src` set | Background image with overlay scrim |
| Video background | `bg-video` set | Background video (muted, autoplay, loop); respects `prefers-reduced-motion` |
| Full-height | `full-height` boolean | `min-height: 100dvh` |
| Left-aligned | `align="start"` | Content aligned to the inline-start |
| Right-aligned | `align="end"` | Content aligned to the inline-end |
| Centered (default) | `align="center"` | Content centered horizontally |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `heading` | string | `""` | Yes | Plain-text heading; used when the `heading` slot is empty |
| `heading-level` | `"1"` \| `"2"` \| `"3"` | `"1"` | Yes | Heading element level for the rendered heading |
| `bg-src` | string | `""` | Yes | URL of the background image |
| `bg-video` | string | `""` | Yes | URL of a background video (MP4 or WebM) |
| `bg-color` | string | `""` | Yes | CSS color value or token for the background when no image/video is set |
| `overlay-opacity` | number | `0.4` | Yes | Opacity (0–1) of the contrast scrim over a background image/video |
| `align` | `"start"` \| `"center"` \| `"end"` | `"center"` | Yes | Horizontal alignment of the content region |
| `full-height` | boolean | `false` | Yes | Makes the hero fill the full viewport height |
| `min-height` | string | `"40vh"` | Yes | CSS min-height for the hero; overridden by `full-height` |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `videoElement` | `HTMLVideoElement \| null` (readonly) | Reference to the internal background `<video>` element when `bg-video` is set |

## 7. Slots

| Slot | Description |
|------|-------------|
| `heading` | Rich heading markup; replaces the `heading` attribute text |
| `body` | Supporting body copy, typically one or two sentences |
| `actions` | Primary and secondary action buttons |
| `media` | Foreground media (illustration, product image) rendered above the background |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-hero-bg-error` | `{ src: string }` | Yes | No | Emitted when the background image or video fails to load |

## 9. CSS parts & custom properties

**Parts**
- `::part(root)` — the `<section>` landmark
- `::part(background)` — background image/video container
- `::part(overlay)` — contrast scrim
- `::part(content)` — the centered content wrapper
- `::part(heading)` — the heading element
- `::part(body)` — the body text container
- `::part(actions)` — the actions row
- `::part(media)` — the foreground media slot wrapper

**Custom properties**
| Property | Default token | Description |
|----------|--------------|-------------|
| `--mj-hero-bg-color` | `--mj-color-primary` | Background color when no image/video |
| `--mj-hero-overlay-color` | `#000000` | Color of the contrast scrim |
| `--mj-hero-overlay-opacity` | resolved from `overlay-opacity` | Scrim opacity |
| `--mj-hero-content-max-width` | `--mj-breakpoint-lg` | Max width of the content region |
| `--mj-hero-padding-block` | `--mj-space-16` | Top/bottom padding of the content |
| `--mj-hero-heading-color` | `--mj-color-text-on-primary` | Heading text color |
| `--mj-hero-body-color` | `--mj-color-text-on-primary-muted` | Body text color |
| `--mj-hero-actions-gap` | `--mj-space-3` | Gap between action buttons |

## 10. States

- **default** — background color, content visible.
- **image-loaded** — background image rendered; scrim applied.
- **image-error** — background image failed; falls back to `bg-color`; `mj-hero-bg-error` emitted.
- **video-playing** — background video playing (muted autoplay).
- **reduced-motion** — when `prefers-reduced-motion: reduce`, background video is paused and replaced with its poster image.

## 11. Behavior & interactions

When `bg-src` is set, the background image is applied as a CSS `background-image`
on the background `<div>`. An `<img>` element with `src` equal to `bg-src` is
created off-screen to detect load errors; on error `mj-hero-bg-error` fires and
`bg-color` is used as the fallback background.

When `bg-video` is set, a `<video muted autoplay loop playsinline>` element is
rendered inside the background `<div>`. If `prefers-reduced-motion: reduce` is
detected, `autoplay` is removed and the video is paused. Authors should supply a
`poster` via the `video-poster` attribute so a static image is shown when the
video is paused.

The scrim `<div>` is rendered between the background and the content layer with
`position: absolute; inset: 0; background: var(--mj-hero-overlay-color);
opacity: var(--mj-hero-overlay-opacity)`. Authors must ensure that the resulting
contrast between heading/body text and the combined background+scrim meets the
WCAG AA 4.5:1 ratio for normal text and 3:1 for large text.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Tab` | Move focus through slotted action buttons in the actions slot |
| `Enter` / `Space` | Activate the focused button |

## 13. Accessibility

- Root is a `<section>` element; it becomes a `region` landmark when it has an
  accessible name. The component derives the accessible name from the heading text
  automatically via `aria-labelledby`.
- Background image and video elements are `aria-hidden="true"`; they are purely
  decorative.
- The overlay scrim must be thick enough to ensure WCAG AA contrast of heading
  and body text over the background; the component emits a development-mode
  console warning when `overlay-opacity` is below 0.3 and a dark scrim is used.
- Heading level is configurable via `heading-level` to fit the document outline.
- All action buttons in the `actions` slot must have accessible names.
- Minimum touch target size for action buttons: 44 × 44 px.

## 14. Form participation

N/A — `<mj-hero>` is a presentational layout component and does not participate
in forms.

## 15. Internationalization & RTL

`align` uses CSS logical values (`start`/`end`); content alignment follows the
writing direction. Text in the `heading` and `body` slots is supplied by the
author in the correct locale. The `heading` attribute string is rendered as-is.
No Intl formatting is performed by this component.

## 16. Progressive enhancement / SSR

The server renders the hero as a `<section>` with a heading, body paragraph, and
action links. Background image is applied via an inline `style` attribute. Before
upgrade the content is fully legible as semantic HTML. After upgrade the shadow
DOM applies token-backed spacing, the scrim overlay, and background image/video
handling.

## 17. Dependencies

- Section 6: Registry + base element helper; design-token stylesheet.
- No other `mj-` components are required, though the `actions` slot typically
  contains `<mj-button>` components.

## 18. Edge cases & error handling

- **No heading provided** — root `<section>` has no accessible name; a console
  warning is emitted. Authors must supply a heading or `aria-label`.
- **Both `bg-src` and `bg-video` set** — `bg-video` takes precedence; `bg-src`
  is ignored.
- **`overlay-opacity` outside 0–1** — clamped; console warning emitted.
- **Very long heading text** — truncation is not applied; text wraps naturally.
- **`full-height` on a page with a sticky header** — the hero occupies 100dvh
  including the header area; authors should apply a `padding-block-start` or use
  CSS anchor positioning to account for the header height.

## 19. Acceptance criteria

- [ ] Root is a `<section>` with `aria-labelledby` pointing to the heading element.
- [ ] Background image is applied to the background `<div>`, not as an `<img>`.
- [ ] Background `<div>` is `aria-hidden="true"`.
- [ ] Scrim opacity is controlled by `overlay-opacity`; falls within 0–1.
- [ ] `bg-video` renders a `<video muted autoplay loop>`; paused when `prefers-reduced-motion: reduce`.
- [ ] `mj-hero-bg-error` fires when the background image fails to load.
- [ ] `full-height` sets `min-height: 100dvh`.
- [ ] `align` positions content correctly for `start`, `center`, and `end` values.
- [ ] Heading level is controlled by `heading-level` attribute.
- [ ] Automated accessibility check passes with no violations.

## 20. Open questions

- Should a built-in contrast checker emit a warning when the computed contrast ratio between text tokens and the background (including the scrim) falls below WCAG AA thresholds?
- Should the `bg-video` element expose a `video-poster` attribute to set the poster frame shown while the video is paused under `prefers-reduced-motion`?
