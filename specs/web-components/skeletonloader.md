# Skeleton Loader Spec

- **Tag:** `<mj-skeleton>`
- **Class / file:** `MjSkeleton` / `mjskeletonloader.js`
- **Category:** Layout & content containers (§5.5)
- **Primary or Variant:** Primary
- **Synonyms covered:** Skeleton screen
- **Phase:** P2
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-skeleton>` is a loading placeholder that mimics the shape of the content
that is about to load. It is marked `aria-hidden="true"` so assistive technology
ignores the decorative shimmer, while an accessible "Loading…" status is
announced via a sibling live region. It prevents layout shift by matching the
real content's dimensions before the data arrives.

## 2. When to use / when not to use

**Use** when loading a defined content shape that is known before the data
arrives — a card, a list row, a user avatar + name, a paragraph block. **Do not
use** when the content shape is completely unknown — display a spinner instead.
**Do not use** when loading is near-instantaneous (< 300 ms) — no placeholder
is needed. **Do not use** as a replacement for an error state — use `<mj-alert>`.

## 3. Anatomy

- **root** — a `<div>` that is `aria-hidden="true"`; surfaced as `::part(root)`.
- **shimmer-overlay** — an absolutely-positioned `<div>` with the animated
  gradient shimmer; surfaced as `::part(shimmer)`.
- The component itself renders as a single rectangular (or shaped) placeholder.
  Multiple skeletons are composed by slotting them inside a `<mj-stack>` or
  `<mj-grid>` that mirrors the real content layout.
- **status (live region)** — a separate visually-hidden `<span role="status">`
  inside the shadow root that announces the loading state to screen readers.

## 4. Variants & modes

| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Rectangle (default) | `variant="rectangle"` | Rectangular block with configurable dimensions |
| Circle | `variant="circle"` | Circular placeholder (equal width/height, `border-radius: 50%`) |
| Text | `variant="text"` | Narrow, text-line-height placeholder; multiple `lines` supported |
| Animated (default) | `animated` | Shimmer gradient sweeps across the block |
| Static | `animated="false"` | Solid muted fill; used when `prefers-reduced-motion: reduce` |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `variant` | `"rectangle"` \| `"circle"` \| `"text"` | `"rectangle"` | Yes | Shape of the skeleton placeholder |
| `width` | string | `"100%"` | Yes | CSS width of the skeleton |
| `height` | string | `"1rem"` | Yes | CSS height of the skeleton (overridden by `lines` for `variant="text"`) |
| `lines` | integer | `1` | Yes | Number of text lines (only for `variant="text"`); last line is 80% width |
| `animated` | boolean | `true` | Yes | Enables the shimmer animation |
| `loading-label` | string | `"Loading"` | Yes | Text announced in the live region; localizable |
| `radius` | string | `""` | Yes | CSS border-radius override; ignored when `variant="circle"` |

## 6. Properties

No complex properties beyond reflected attributes.

| Property | Type | Description |
|----------|------|-------------|
| `animating` | boolean (readonly) | `true` when the shimmer animation is active (respects `prefers-reduced-motion`) |

## 7. Slots

`<mj-skeleton>` accepts no child slots. It is a self-contained placeholder shape.

| Slot | Description |
|------|-------------|
| (none) | No slots; `<mj-skeleton>` renders its own internal placeholder |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| — | — | — | — | No component-specific events; skeletons are replaced by real content when loading completes |

## 9. CSS parts & custom properties

**Parts**
- `::part(root)` — the outer placeholder container
- `::part(shimmer)` — the animated gradient overlay

**Custom properties**
| Property | Default token | Description |
|----------|--------------|-------------|
| `--mj-skeleton-bg` | `--mj-color-skeleton-base` | Base color of the placeholder |
| `--mj-skeleton-shimmer-color` | `--mj-color-skeleton-highlight` | Highlight color of the shimmer gradient |
| `--mj-skeleton-radius` | `--mj-radius-sm` | Default corner radius for rectangles |
| `--mj-skeleton-duration` | `1.5s` | Duration of one shimmer cycle |
| `--mj-skeleton-line-height` | `1em` | Height of each text-line placeholder |
| `--mj-skeleton-line-gap` | `0.5em` | Gap between text lines in multi-line mode |

## 10. States

- **animated** — shimmer gradient sweeps from inline-start to inline-end on a loop.
- **static** — solid muted fill; active when `animated="false"` or when
  `prefers-reduced-motion: reduce` is detected.

## 11. Behavior & interactions

The component is entirely presentational. On `connectedCallback`, the component
checks `window.matchMedia('(prefers-reduced-motion: reduce)')` and sets
`animating = false` when matched, overriding the `animated` attribute. A
`MediaQueryList` listener is attached and torn down on `disconnectedCallback` to
respond to system-level motion preference changes at runtime.

The shimmer animation uses a CSS `@keyframes` rule with a `background-position`
sweep on a `linear-gradient`. No JavaScript timers are used for the animation.

For `variant="text"` with `lines > 1`, the component renders N sibling
placeholder lines inside the shadow root, with the last line at 80% width.

The live-region `<span role="status">` contains `loading-label` text so screen
readers announce the loading state once on first render. The span is not
continuously updated.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| (none) | `<mj-skeleton>` is not focusable and has no keyboard interaction |

## 13. Accessibility

- Root `<div>` is `aria-hidden="true"`; the shimmer is purely decorative.
- A visually-hidden `<span role="status" aria-live="polite">` inside the shadow
  root announces the `loading-label` when the component is first inserted so
  screen-reader users know content is loading.
- The status span text is cleared once the consuming application removes the
  skeleton and inserts real content; this prevents stale announcements.
- No tabindex; no role on the root element visible to AT.
- Shimmer animation respects `prefers-reduced-motion: reduce` by replacing the
  animation with a static fill.

## 14. Form participation

N/A — `<mj-skeleton>` is a display component and does not participate in forms.

## 15. Internationalization & RTL

The shimmer gradient sweeps in the inline direction; in RTL the gradient
reverses so the sweep moves from inline-end to inline-start via
`background-position` and logical gradient keywords. The `loading-label` string
is routed through the Section 6 localization hook.

## 16. Progressive enhancement / SSR

The server can render `<mj-skeleton>` with a `width` and `height` inline style so
the space is reserved before the script loads. Without scripting the element
shows as a muted rectangle. After upgrade the component applies the shimmer
animation and the live-region announcement.

## 17. Dependencies

- Section 6: Registry + base element helper; design-token stylesheet; live-region/
  announcement service (for the initial "Loading" status announcement).
- Used internally by `<mj-card>` when its `loading` attribute is set.

## 18. Edge cases & error handling

- **`variant="circle"` with differing `width` and `height`** — height is set
  equal to the computed width to maintain a circle; console warning emitted.
- **`lines="0"` for text variant** — treated as `lines="1"`; console warning emitted.
- **`animated` attribute toggled at runtime** — the shimmer animation is started
  or stopped without re-rendering the element.
- **`prefers-reduced-motion` changes at runtime** — `MediaQueryList` listener
  updates `animating` state immediately.
- **Skeleton left in DOM after content loads** — the skeleton remains visible
  indefinitely; authors are responsible for removing it or hiding it when content
  is ready.

## 19. Acceptance criteria

- [ ] Root element is `aria-hidden="true"`.
- [ ] Live-region `<span role="status">` contains `loading-label` text on first render.
- [ ] `variant="circle"` renders a circle (equal width/height, `border-radius: 50%`).
- [ ] `variant="text"` with `lines="3"` renders three text-line placeholders with the last at 80% width.
- [ ] Shimmer animation runs in animated mode; stops in static mode.
- [ ] `prefers-reduced-motion: reduce` disables the shimmer and applies a static fill.
- [ ] RTL mode reverses the shimmer sweep direction.
- [ ] `MediaQueryList` listener is removed on `disconnectedCallback`.
- [ ] Automated accessibility check passes with no violations (skeleton is hidden from AT).

## 20. Open questions

- Should `<mj-skeleton>` expose a `count` attribute to render N identical adjacent
  placeholder shapes (e.g., a list of 5 skeleton rows) without requiring N
  instances in the markup?
- Should the live-region announcement be opt-out via a `no-announce` boolean to
  avoid duplicate announcements when many skeletons are on the page simultaneously?
