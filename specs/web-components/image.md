# Image Spec

- **Tag:** `<mj-image>`
- **Class / file:** `MjImage` / `mjimage.js`
- **Category:** Media & visualization
- **Primary or Variant:** Primary
- **Synonyms covered:** Thumbnail, Figure
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-image>` is a lazy-loaded, responsive image element that reserves its aspect
ratio before the image loads to prevent layout shift. It wraps a native `<img>`
(or a `<figure>` when a caption is present) and adds intersection-observer-driven
lazy loading, `srcset`/`sizes` support, decode scheduling, and a blur-up
placeholder strategy. It consolidates the Thumbnail and Figure catalog entries
via configuration.

## 2. When to use / when not to use

**Use** for any image that must reserve space, lazy-load, or carry a caption.
Use the `figure` variant when an accessible caption is needed.
Use `thumbnail` size when showing a compact preview in a list or card.

**Do not use** for purely decorative background images (use CSS instead), for
inline SVG icons (use `<mj-icon>`), or for user avatars (use `<mj-avatar>`
which provides fallback initials).

## 3. Anatomy

- **Container** (`::part(container)`) — block element that enforces aspect-ratio
  reservation via an `aspect-ratio` CSS property; holds the placeholder and image.
- **Placeholder** (`::part(placeholder)`) — low-quality inline SVG or
  `background-color` shown before the image loads; fades out on load.
- **Img** (`::part(img)`) — the native `<img>` element with computed `srcset`,
  `sizes`, `alt`, `decoding="async"`, and `loading="lazy"` (overridden to
  `"eager"` for above-fold images).
- **Caption** (`::part(caption)`) — `<figcaption>` rendered below the image when
  the `caption` attribute or `caption` slot is non-empty; wraps the container in
  a `<figure>`.
- **Overlay slot** — optional overlay content (badges, play buttons) positioned
  absolutely over the image.

## 4. Variants & modes

| Variant / mode | Attribute value | Behavior |
|----------------|----------------|----------|
| Default image | `variant="image"` (default) | Renders `<img>` in a div container |
| Figure | `variant="figure"` | Wraps in `<figure>`/`<figcaption>`; caption slot active |
| Thumbnail | `variant="thumbnail"` | Applies compact sizing tokens; square crop by default |
| Cover | `fit="cover"` | `object-fit: cover`; image fills container |
| Contain | `fit="contain"` | `object-fit: contain`; letterboxed |
| Eager | `loading="eager"` | Skips IntersectionObserver; loads immediately |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `src` | `string` | `""` | Yes | Primary image URL |
| `srcset` | `string` | `""` | Yes | Responsive image candidate list (passed to `<img>`) |
| `sizes` | `string` | `""` | Yes | Media-condition size hints for `srcset` |
| `alt` | `string` | `""` | Yes | Alt text; set to `""` explicitly for decorative images |
| `width` | `number` | `undefined` | Yes | Intrinsic width in px used for aspect-ratio calculation |
| `height` | `number` | `undefined` | Yes | Intrinsic height in px used for aspect-ratio calculation |
| `aspect-ratio` | `string` | `""` | Yes | CSS `aspect-ratio` value (e.g. `"16/9"`) overrides width/height ratio |
| `loading` | `"lazy"\|"eager"` | `"lazy"` | Yes | Loading strategy |
| `fit` | `"cover"\|"contain"\|"fill"\|"scale-down"` | `"cover"` | Yes | `object-fit` mode |
| `variant` | `"image"\|"figure"\|"thumbnail"` | `"image"` | Yes | Structural variant |
| `caption` | `string` | `""` | Yes | Caption text; if set, implies `variant="figure"` |
| `placeholder-color` | `string` | `""` | Yes | Solid color shown while loading (hex or CSS color) |
| `crossorigin` | `"anonymous"\|"use-credentials"` | `""` | Yes | Forwarded to `<img crossorigin>` |
| `decoding` | `"async"\|"sync"\|"auto"` | `"async"` | Yes | Forwarded to `<img decoding>` |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `complete` | `boolean` | `true` when the underlying `<img>.complete` is `true` |
| `naturalWidth` | `number` | Forwarded from the underlying `<img>` |
| `naturalHeight` | `number` | Forwarded from the underlying `<img>` |
| `currentSrc` | `string` | The resolved URL selected from `srcset`, forwarded from `<img>` |

## 7. Slots

| Slot | Description |
|------|-------------|
| `caption` | Replaces the `caption` attribute with rich HTML caption content |
| `overlay` | Absolutely positioned content layered over the image (e.g. a play icon, badge) |
| `placeholder` | Custom placeholder content shown during load (replaces color placeholder) |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-image-load` | `{ src: string, naturalWidth: number, naturalHeight: number }` | Yes | No | Fired when the image has fully loaded |
| `mj-image-error` | `{ src: string }` | Yes | No | Fired when the image fails to load |
| `mj-image-visible` | `{ ratio: number }` | Yes | No | Fired when the image enters the viewport (IntersectionObserver callback) |

## 9. CSS parts & custom properties

**Parts**
- `::part(container)` — outer sizing wrapper
- `::part(img)` — the `<img>` element
- `::part(placeholder)` — pre-load placeholder layer
- `::part(caption)` — `<figcaption>` element
- `::part(overlay)` — overlay slot wrapper

**Custom properties**
| Property | Default | Description |
|----------|---------|-------------|
| `--mj-image-radius` | `var(--mj-radius-md)` | Corner radius of the container |
| `--mj-image-placeholder-color` | `var(--mj-color-surface-2)` | Fallback placeholder background |
| `--mj-image-transition-duration` | `var(--mj-motion-fade)` | Fade-in duration for the loaded image |
| `--mj-image-caption-font-size` | `var(--mj-font-size-sm)` | Caption text size |
| `--mj-image-caption-color` | `var(--mj-color-text-subtle)` | Caption text color |
| `--mj-image-thumbnail-size` | `3rem` | Width and height when `variant="thumbnail"` |

## 10. States

- **loading** — placeholder visible; `img` opacity 0; `aria-busy="true"` on container.
- **loaded** — placeholder fades out; image fades in; `aria-busy` removed.
- **error** — image fails; placeholder replaced with an error icon slot; `mj-image-error` fired.
- **off-screen** — IntersectionObserver has not triggered; `loading="lazy"` images have `src` not yet set on the inner `<img>`.

## 11. Behavior & interactions

The component sets `aspect-ratio` on the container immediately from `width`/`height`
or the `aspect-ratio` attribute so the page reserves space before any network
request is made, preventing cumulative layout shift.

When `loading="lazy"` (default), an `IntersectionObserver` with a `rootMargin`
of `200px` monitors the element. When the image enters the extended viewport the
observer sets `src`/`srcset` on the inner `<img>`, calls `img.decode()`, and then
fades in the image by removing the `loading` class. The observer disconnects after
first intersection.

When `loading="eager"` the `src`/`srcset` are applied immediately in
`connectedCallback` without an observer.

On `src` attribute change the component resets to the loading state and starts
the process again.

The `placeholder` slot content or `placeholder-color` is visible until the
image `load` event fires. On error, the `placeholder` remains visible and the
`mj-image-error` event is dispatched.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| None | The image itself is not interactive; no keyboard interaction applies unless an interactive element is placed in the `overlay` slot, which is managed by that element |

## 13. Accessibility

- The inner `<img>` carries the `alt` attribute verbatim. An empty `alt=""` marks
  the image as decorative and is valid; omitting `alt` is never allowed and
  triggers a console warning.
- When `variant="figure"`, the `<figure>` element contains the `<figcaption>`,
  which is automatically associated by the browser.
- `aria-busy="true"` is set on the container while the image is loading; removed
  on load or error.
- The overlay slot must not contain `aria-hidden` content if that content is
  meaningful; host authors are responsible for naming overlay controls.
- Color is never the sole indicator of image state; the error state uses an icon
  with a text label in addition to any color change.

## 14. Form participation

N/A — `<mj-image>` is a display component with no form value.

## 15. Internationalization & RTL

- The `alt` and `caption` attributes/slots accept any Unicode text.
- In RTL layouts the component applies `dir="rtl"` to the container; `object-position`
  may need to be overridden by the host for portraits where the subject is
  offset to one side.
- No locale-specific formatting logic required.

## 16. Progressive enhancement / SSR

The server renders a standard `<img>` (or `<figure>/<figcaption>`) inside the
custom element tag. Before the script loads the browser displays the raw `<img>`,
which is already meaningful. On upgrade, the component moves the existing `<img>`
into the shadow DOM, applies aspect-ratio reservation, and attaches the
IntersectionObserver without removing the existing content, preventing flash.

## 17. Dependencies

- **Registry + base element helper** (§6) — lifecycle and attribute reflection.
- **Design-token stylesheet** (§6) — all visual values via tokens.
- No other `mj-*` components are composed internally; the `overlay` slot accepts
  any component (e.g. `<mj-badge>`).

## 18. Edge cases & error handling

- `src` and `alt` both absent: logs a console error; renders an empty container.
- `width` or `height` missing with no `aspect-ratio` attribute: no aspect-ratio
  reservation; container collapses until image loads (acceptable degradation,
  warns in dev mode).
- Network failure: error state shown; retry is the host application's
  responsibility via re-setting `src`.
- `srcset` with no matching candidate: browser falls back to `src` per spec.
- Very long `caption` text: caption wraps; `max-height` with `overflow: hidden`
  can be applied via `--mj-image-caption-max-height` token if needed.
- Component moved to a new document (`adoptedCallback`): IntersectionObserver is
  disconnected and reconnected to the new root.

## 19. Acceptance criteria

- [ ] Aspect ratio is reserved via `aspect-ratio` CSS before the image loads.
- [ ] `loading="lazy"` defers `src`/`srcset` assignment until IntersectionObserver fires.
- [ ] `loading="eager"` applies `src`/`srcset` synchronously in `connectedCallback`.
- [ ] `mj-image-load` fires after successful decode with correct `detail` fields.
- [ ] `mj-image-error` fires on network or decode failure.
- [ ] `alt=""` marks the image decorative; omitting `alt` logs a warning.
- [ ] `variant="figure"` renders `<figure>/<figcaption>` structure.
- [ ] `variant="thumbnail"` applies compact size tokens.
- [ ] `fit` attribute correctly maps to `object-fit` on the inner `<img>`.
- [ ] Server-rendered `<img>` is promoted to shadow DOM without content flash.
- [ ] All design tokens resolve; no hard-coded colors or sizes.
- [ ] Automated accessibility checks pass with no violations.
- [ ] IntersectionObserver is disconnected in `disconnectedCallback`.

## 20. Open questions

- Should a blur-up LQIP (Low Quality Image Placeholder) strategy be supported
  natively, or is the `placeholder` slot sufficient for host-provided blur previews?
- Should `<mj-image>` expose a `decode()` method on its public API to allow
  hosts to pre-decode before insertion?
