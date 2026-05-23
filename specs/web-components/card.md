# Card Spec

- **Tag:** `<mj-card>`
- **Class / file:** `MjCard` / `mjcard.js`
- **Category:** Layout & content containers (§5.5)
- **Primary or Variant:** Primary
- **Synonyms covered:** Data card
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-card>` is a contained content surface that groups related media, a header,
a body, and an optional footer into a visually distinct unit. It solves the
common pattern of displaying a summary of an entity (article, product, person,
event) with a consistent, themeable layout that can stand alone or appear inside
a grid or list.

## 2. When to use / when not to use

**Use** when presenting a self-contained unit of information that benefits from
visual separation (article previews, product tiles, user profiles, event summaries).
**Do not use** for a full-page section layout — use `<mj-surface>` instead.
**Do not use** when list items require simple text-only rows — use a plain list
or `<mj-feed>`. If the card is the sole interactive target on a page region,
consider whether a plain `<article>` or `<section>` suffices.

## 3. Anatomy

- **media** — optional top or side image/video region (slot `media`).
- **header** — card title and optional subtitle (slot `header`; or `heading` +
  `subheading` attributes for plain-text).
- **body** — primary narrative content (default slot).
- **footer** — action row or metadata strip (slot `footer`).
- **badge** — optional overlay label on the media region (slot `badge`).
- **root container** — the outer `<article>` element surfaced as `::part(root)`.

## 4. Variants & modes

| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Default | — | vertical layout: media → header → body → footer |
| Horizontal | `orientation="horizontal"` | media placed at the start, content stacked beside it |
| Clickable | `href` present | whole card is a single link; inner actions are still individually focusable |
| Flat | `elevation="flat"` | no shadow; border only |
| Elevated | `elevation="raised"` | box-shadow from token `--mj-elevation-2` |
| Outlined | `elevation="outlined"` | border, no shadow |
| Loading | `loading` boolean | skeleton shimmer overlays content; `aria-busy="true"` |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `heading` | string | `""` | Yes | Plain-text card title when the `header` slot is not used |
| `subheading` | string | `""` | Yes | Plain-text subtitle below the heading |
| `href` | string | `""` | Yes | When set, wraps the card in a navigable link; the card root becomes the single tab stop |
| `orientation` | `"vertical"` \| `"horizontal"` | `"vertical"` | Yes | Layout axis for media vs. content |
| `elevation` | `"flat"` \| `"outlined"` \| `"raised"` | `"raised"` | Yes | Shadow/border treatment |
| `loading` | boolean | `false` | Yes | Puts the card into a skeleton loading state |
| `disabled` | boolean | `false` | Yes | Mutes interactive affordances and sets `aria-disabled` when `href` is present |
| `aspect-ratio` | string | `""` | Yes | CSS aspect-ratio value applied to the media slot region (e.g. `"16/9"`) |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `headingLevel` | `1`–`6` | Integer; controls the rendered heading element (`h1`–`h6`) inside the header region when `heading` attribute is used. Defaults to `3`. |

## 7. Slots

| Slot | Description |
|------|-------------|
| `media` | Image, video, or other media element placed at the top (vertical) or start (horizontal) |
| `header` | Custom header markup replacing the attribute-driven heading/subheading |
| (default) | Body content — text, lists, nested components |
| `footer` | Action buttons, timestamps, metadata |
| `badge` | Small overlay label or icon rendered over the media region |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-card-click` | `{ originalEvent: PointerEvent }` | Yes | No | Emitted when the card root link is activated; only fires when `href` is set |

## 9. CSS parts & custom properties

**Parts**
- `::part(root)` — the outer `<article>` element
- `::part(media)` — the media region container
- `::part(header)` — header region wrapper
- `::part(body)` — body region wrapper
- `::part(footer)` — footer region wrapper
- `::part(badge)` — badge overlay container

**Custom properties**
| Property | Default token | Description |
|----------|--------------|-------------|
| `--mj-card-bg` | `--mj-color-surface` | Card background color |
| `--mj-card-radius` | `--mj-radius-md` | Corner radius |
| `--mj-card-padding` | `--mj-space-4` | Body/header/footer internal padding |
| `--mj-card-shadow` | `--mj-elevation-2` | Box shadow when `elevation="raised"` |
| `--mj-card-border` | `--mj-color-border` | Border color when `elevation="outlined"` |
| `--mj-card-media-ratio` | `16/9` | Default aspect ratio of the media region |
| `--mj-card-gap` | `--mj-space-2` | Gap between header/body/footer sections |

## 10. States

- **default** — raised card with shadow, full color.
- **hover** — slight elevation increase (shadow deepens one token step) when `href` is set.
- **focus-visible** — 2 px focus ring on the root link using `--mj-focus-ring`; inner buttons retain their own focus rings.
- **loading** — `aria-busy="true"` on root; skeleton shimmer animation on all content regions; respects `prefers-reduced-motion` (shimmer replaced with static muted fill).
- **disabled** — `aria-disabled="true"` on the link; pointer-events none; color tokens shifted to `--mj-color-disabled-fg` and `--mj-color-disabled-bg`.

## 11. Behavior & interactions

When `href` is set the entire card surface acts as a single hyperlink. Inner
interactive elements (buttons in the footer) must remain independently focusable
and must not be nested inside the outer `<a>`. The component achieves this by
rendering an `<a>` overlay that covers only the non-interactive regions, or by
using JavaScript activation while keeping footer actions as separate tab stops.

The `loading` state replaces visible content with animated shimmer blocks whose
dimensions match the expected content layout so that no layout shift occurs when
real content arrives. The `orientation` change from vertical to horizontal is
driven by a CSS custom property so consuming layouts can override it via a media
query without re-instantiating the component.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Tab` | Move focus to the card link (when `href` set) or through focusable slot content |
| `Enter` / `Space` | Activate the card link when the card root is focused |
| `Tab` (within card) | Cycle through footer action buttons independently of the card link |

## 13. Accessibility

- Root element is `<article>` giving an implicit `article` landmark.
- When `heading` attribute is used, the rendered heading element level is controlled by `headingLevel` property to fit document outline.
- When `href` is present the card link receives an accessible name derived from the heading text; authors can override via `aria-label` on the element.
- `loading` state adds `aria-busy="true"` to the root; a sibling live region (polite) announces "Loading" when loading begins and "Loaded" when complete.
- Skeleton shimmer regions are `aria-hidden="true"` and carry no role.
- Badge slot content that conveys information must include visible text or an `aria-label`; purely decorative badges should use `aria-hidden="true"`.
- Minimum touch target for footer actions: 44 × 44 px.

## 14. Form participation

N/A — `<mj-card>` is a layout/display component and does not participate in forms.

## 15. Internationalization & RTL

- In RTL contexts (`dir="rtl"`), horizontal orientation flips the media/content
  order using CSS logical properties (`margin-inline-start`, `padding-inline-end`).
- The `heading` and `subheading` attribute strings are rendered as-is; authors
  supply the correctly localized text server-side.
- No date/number formatting is performed by the component itself.

## 16. Progressive enhancement / SSR

The server can render the card's HTML structure using semantic elements
(`<article>`, headings, `<img>`, `<p>`) before the script loads. After upgrade
the component applies its shadow DOM, slots the existing children, and applies
theme tokens. No content is hidden or re-ordered during upgrade; the layout
shift is limited to shadow-DOM padding/shadow appearance.

## 17. Dependencies

- Section 6: Registry + base element helper; design-token stylesheet.
- `<mj-skeleton>` — used internally to render shimmer blocks in `loading` state.

## 18. Edge cases & error handling

- **No media slot** — media region collapses to zero height; no gap is left.
- **Long heading text** — truncated with ellipsis by default; full text available via `title` attribute on the heading element and visible on hover.
- **Empty card** — renders the outer shell with a min-height token so it does not collapse.
- **`href` + `disabled`** — disabled takes precedence; the link is rendered with `aria-disabled="true"` and `tabindex="-1"`.
- **`orientation="horizontal"` with no media** — content fills full width.
- **Nested interactive elements in body** — authors must ensure they are reachable independently via Tab when `href` wraps the card.

## 19. Acceptance criteria

- [ ] Card renders all four slots (media, header, body, footer) and each is independently styleable via `::part()`.
- [ ] `elevation` attribute applies the correct shadow/border token.
- [ ] `orientation="horizontal"` places media at the inline-start side.
- [ ] When `href` is set, pressing Enter/Space on the focused card activates navigation.
- [ ] Footer buttons remain separately focusable when `href` is set.
- [ ] `loading` attribute sets `aria-busy="true"` and displays shimmer blocks.
- [ ] Shimmer animation is replaced with a static fill when `prefers-reduced-motion: reduce`.
- [ ] RTL layout is correct for horizontal orientation.
- [ ] `disabled` + `href` sets `aria-disabled="true"` and suppresses navigation.
- [ ] Automated accessibility check passes with no violations.
- [ ] No layout shift occurs when upgrading from SSR markup.

## 20. Open questions

- Should the card support a "selected" state (e.g. within a selectable grid) exposing `aria-selected`, or is that delegated to a parent composite widget?
- Is a maximum heading level cap (e.g. always `h2`–`h4`) needed to prevent authors from producing invalid document outlines?
