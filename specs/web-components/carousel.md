# Carousel Spec

- **Tag:** `<mj-carousel>`
- **Class / file:** `MjCarousel` / `mjcarousel.js`
- **Category:** Layout & content containers (§5.5)
- **Primary or Variant:** Primary
- **Synonyms covered:** Gallery
- **Phase:** P2
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-carousel>` displays a sequence of slides in a bounded viewport, exposing
previous/next controls and slide-picker tabs. It follows the WAI-ARIA Authoring
Practices Guide carousel pattern, including auto-rotation that pauses on user
interaction and is fully stoppable. It solves the need for a consistent,
accessible image gallery, content rotator, and feature highlight component.

## 2. When to use / when not to use

**Use** for a finite set of slides where one slide occupies the full viewport at
a time — hero banners, product image galleries, onboarding steps, featured
articles. **Do not use** when all content should be visible simultaneously — use
`<mj-grid>`. **Do not use** for a continuously loading content stream — use
`<mj-feed>`. **Do not use** auto-rotation for content that users need to read
carefully; prefer `autoplay="false"` in those cases.

## 3. Anatomy

- **root** — the outer landmark container with `role="region"` and an
  accessible name; surfaced as `::part(root)`.
- **slides-container** — the scrollable or absolutely-positioned slide track;
  surfaced as `::part(slides-container)`.
- **slide** — each `<mj-carousel-slide>` child (separate micro-component);
  the currently visible slide has `aria-hidden="false"`, all others
  `aria-hidden="true"`.
- **prev-button** — navigates to the previous slide; surfaced as `::part(prev-button)`.
- **next-button** — navigates to the next slide; surfaced as `::part(next-button)`.
- **autoplay-button** — stops/starts auto-rotation; surfaced as `::part(autoplay-button)`.
- **picker** — a row of tab-like slide-picker buttons; surfaced as `::part(picker)`.
- **picker-item** — individual picker button for each slide; surfaced as `::part(picker-item)`.

## 4. Variants & modes

| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Manual (default) | `autoplay` absent | No auto-rotation; user-controlled only |
| Auto-rotating | `autoplay` boolean | Slides advance automatically; pauses on hover/focus |
| Looping | `loop` boolean | Wraps from last to first slide and vice versa |
| No picker | `show-picker="false"` | Hides the slide-picker row |
| No controls | `show-controls="false"` | Hides prev/next buttons (picker only) |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `current-index` | integer | `0` | Yes | Zero-based index of the currently visible slide |
| `autoplay` | boolean | `false` | Yes | Enables automatic slide advancement |
| `autoplay-interval` | integer (ms) | `5000` | Yes | Milliseconds between auto-advances |
| `loop` | boolean | `false` | Yes | Wraps navigation from last to first slide |
| `show-picker` | boolean | `true` | Yes | Shows the slide-picker (tab) row |
| `show-controls` | boolean | `true` | Yes | Shows prev/next navigation buttons |
| `label` | string | `"Carousel"` | Yes | Accessible name for the carousel region; localizable |
| `transition` | `"slide"` \| `"fade"` \| `"none"` | `"slide"` | Yes | Animation between slides |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `slides` | `MjCarouselSlide[]` (readonly) | Array of all direct `<mj-carousel-slide>` children |
| `playing` | boolean | `true` when auto-rotation is active; settable to start/stop rotation |

## 7. Slots

| Slot | Description |
|------|-------------|
| (default) | One or more `<mj-carousel-slide>` elements |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-carousel-change` | `{ index: number, previousIndex: number, trigger: "user" \| "auto" }` | Yes | Yes | Emitted before the slide changes; cancelable to prevent the advance |
| `mj-carousel-changed` | `{ index: number, previousIndex: number }` | Yes | No | Emitted after the transition completes |
| `mj-carousel-play` | `{}` | Yes | No | Emitted when auto-rotation starts |
| `mj-carousel-pause` | `{}` | Yes | No | Emitted when auto-rotation pauses or is stopped |

## 9. CSS parts & custom properties

**Parts**
- `::part(root)` — outer region container
- `::part(slides-container)` — the slide track
- `::part(prev-button)` — previous slide button
- `::part(next-button)` — next slide button
- `::part(autoplay-button)` — play/pause auto-rotation button
- `::part(picker)` — picker button row container
- `::part(picker-item)` — individual picker button

**Custom properties**
| Property | Default token | Description |
|----------|--------------|-------------|
| `--mj-carousel-slide-duration` | `--mj-motion-duration-md` | Slide transition duration |
| `--mj-carousel-control-size` | `2.5rem` | Width/height of prev/next buttons |
| `--mj-carousel-control-bg` | `--mj-color-surface-overlay` | Control button background |
| `--mj-carousel-picker-gap` | `--mj-space-2` | Gap between picker buttons |
| `--mj-carousel-picker-size` | `0.5rem` | Picker button dot size |
| `--mj-carousel-picker-active-color` | `--mj-color-primary` | Active picker button color |

## 10. States

- **default** — slide at `current-index` visible; others hidden.
- **transitioning** — animation in progress; next/prev buttons temporarily disabled.
- **playing** — auto-rotation interval active.
- **paused** — auto-rotation paused (hover, focus, user stop).
- **focus-within** — focus is inside the carousel; auto-rotation pauses.

## 11. Behavior & interactions

When `autoplay` is set, a `setInterval` timer advances `current-index` by 1
(with loop wrapping if `loop` is set) every `autoplay-interval` ms. The timer is
cleared on `mouseenter`, `focusin`, and when the user activates the autoplay-
button. It resumes on `mouseleave` and `focusout` (unless the user has
permanently stopped it via the autoplay-button).

Slide visibility is controlled by `aria-hidden` on each `<mj-carousel-slide>`.
Non-visible slides have `visibility: hidden` and `position: absolute` so they
are not in the accessibility tree or the keyboard tab order.

When `transition="slide"`, the component uses CSS `translate` and a
`transitionend` listener to swap slides. During the transition, navigation
buttons are disabled to prevent rapid-fire state changes. When
`prefers-reduced-motion: reduce` is active, `transition="none"` is forced.

The `mj-carousel-change` event fires before the transition. Calling
`event.preventDefault()` keeps the carousel on the current slide.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Tab` | Move focus through prev-button, autoplay-button, slides-container, next-button, picker items |
| `Arrow Left` / `Arrow Up` | Previous slide (when focus is in the picker or on a control) |
| `Arrow Right` / `Arrow Down` | Next slide |
| `Home` | Jump to the first slide |
| `End` | Jump to the last slide |
| `Enter` / `Space` | Activate the focused picker item, prev/next/autoplay button |

## 13. Accessibility

- Root has `role="region"` with `aria-label` from the `label` attribute.
- Slides container has `aria-live="off"` during auto-rotation and `aria-live="polite"`
  when the user manually navigates, so screen readers announce the new slide
  without interrupting auto-rotation narration.
- Each `<mj-carousel-slide>` has `role="group"` and `aria-label` (e.g. "Slide 1
  of 5" plus the slide's own label if provided).
- Prev/next buttons have accessible names "Previous slide" and "Next slide"
  (localizable via the `prev-label` and `next-label` attributes).
- Autoplay button toggles between "Start auto-rotation" and "Stop auto-rotation"
  labels and uses `aria-pressed` to reflect state.
- Picker items use `role="tab"` with `aria-selected` matching the current slide;
  the picker row has `role="tablist"` with `aria-label="Choose slide"`.
- Inactive slides have `aria-hidden="true"` so their content is not announced.
- All controls meet the 44 × 44 px minimum touch target size.

## 14. Form participation

N/A — `<mj-carousel>` is a content presentation component and does not
participate in forms.

## 15. Internationalization & RTL

`prev-label`, `next-label`, `autoplay-start-label`, `autoplay-stop-label`, and
`label` attributes are all localizable via the Section 6 localization hook. In
RTL mode the prev/next button positions swap (inline-start/end), and the slide
transition direction reverses. Arrow-key semantics also swap.

## 16. Progressive enhancement / SSR

The server renders all slides as visible block elements inside a container. Before
upgrade the user sees all slides stacked vertically. After upgrade the component
hides all slides except the current one, inserts navigation controls, and applies
the slide track layout. No slide content is removed from the DOM.

## 17. Dependencies

- Section 6: Registry + base element helper; design-token stylesheet; focus
  utilities; localization hook; live-region/announcement service.
- `<mj-carousel-slide>` — companion micro-component (defined in the same file or
  a co-located `mjcarouselslide.js`).

## 18. Edge cases & error handling

- **Single slide** — prev/next buttons and the picker are hidden; no auto-rotation.
- **`loop="false"` at boundaries** — prev-button disabled at index 0; next-button disabled at the last slide.
- **Rapid navigation** — queued navigation requests are debounced; each transition
  must complete before the next begins.
- **Slides added/removed dynamically** — `MutationObserver` on the default slot
  updates the picker and clamps `current-index` if the slide count decreases.
- **`autoplay-interval` set to 0 or negative** — clamped to 1000 ms minimum;
  console warning emitted.

## 19. Acceptance criteria

- [ ] Only the slide at `current-index` is visible; all others are `aria-hidden="true"`.
- [ ] Prev/next buttons navigate slides; `loop` wraps correctly.
- [ ] `autoplay` starts the interval timer; it pauses on hover and focus-within.
- [ ] Auto-rotation resumes on mouseleave/focusout unless the user stopped it via the autoplay-button.
- [ ] `prefers-reduced-motion: reduce` disables slide animation.
- [ ] `mj-carousel-change` is cancelable; cancellation prevents the slide advance.
- [ ] Picker items use `role="tab"` with `aria-selected`; the picker row has `role="tablist"`.
- [ ] Arrow Left/Right navigate slides when focus is on a picker item or control.
- [ ] RTL mode reverses prev/next button positions and slide-advance direction.
- [ ] Automated accessibility check passes with no violations.

## 20. Open questions

- Should `<mj-carousel>` support a `visible-slides` attribute (e.g., `visible-slides="3"`) for showing partial adjacent slides in a "peek" layout?
- Should the slide-picker optionally display slide thumbnails rather than dot indicators?
