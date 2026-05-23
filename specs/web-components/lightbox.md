# Lightbox Spec

- **Tag:** `<mj-lightbox>`
- **Class / file:** `MjLightbox` / `mjlightbox.js`
- **Category:** Dialogs, overlays & popups
- **Primary or Variant:** Primary
- **Synonyms covered:** Lightbox, Full-screen media viewer, Image viewer, Gallery overlay
- **Phase:** P3
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-lightbox>` is a full-screen modal media viewer that presents images, videos, or other media items with prev/next navigation, zoom, and captions. It operates as a modal dialog (built on `<mj-dialog>`) with keyboard and pointer navigation across an ordered set of media items, and supports swipe gestures on touch devices.

## 2. When to use / when not to use

Use to display a gallery of images or media full-screen when the user selects a thumbnail or trigger. Use when the media item warrants a focused, distraction-free viewing experience with navigation across a set. Do not use as a general-purpose modal container — use `<mj-dialog>` instead. Do not auto-open on page load (violates expected user interaction flow).

## 3. Anatomy

- **`<mj-dialog>` root** — provides modal semantics, focus trap, backdrop, and Esc handling.
- **Media viewport** — the constrained area displaying the current media item.
- **Media element** — `<img>`, `<video>`, or slotted custom media per item.
- **Zoom container** — wrapper enabling CSS transform-based zoom and pan.
- **Caption bar** — displays item title and description below the media.
- **Toolbar** — contains close, zoom-in, zoom-out, zoom-reset, and download buttons.
- **Prev/Next buttons** — edge-positioned navigation controls.
- **Thumbnail strip** — optional scrollable row of item thumbnails.
- **Progress indicator** — "N of M" text counter.

## 4. Variants & modes

| Variant | `variant` value | Notes |
|---------|----------------|-------|
| Image lightbox | `image` (default) | `<img>` media with zoom/pan |
| Video lightbox | `video` | `<video>` media; zoom disabled; playback controls |
| Mixed | `mixed` | Items may be image or video; type per item |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `open` | boolean | `false` | Yes | Opens the lightbox |
| `variant` | `image` \| `video` \| `mixed` | `image` | Yes | Default media type for items |
| `current-index` | number | `0` | Yes | Zero-based index of the currently displayed item |
| `loop` | boolean | `true` | Yes | Whether prev/next wraps at the ends |
| `zoom-enabled` | boolean | `true` | Yes | Enables zoom controls (image variant) |
| `max-zoom` | number | `4` | Yes | Maximum zoom multiplier |
| `show-thumbnails` | boolean | `false` | Yes | Shows the thumbnail strip |
| `show-caption` | boolean | `true` | Yes | Shows the caption bar |
| `show-counter` | boolean | `true` | Yes | Shows the "N of M" counter |
| `download-enabled` | boolean | `false` | Yes | Shows the download button in the toolbar |
| `label` | string | `"Media viewer"` | Yes | `aria-label` for the dialog |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `items` | `LightboxItem[]` | Array of media item descriptors; `LightboxItem` has `{ src, alt, type, caption, downloadSrc }` |
| `currentItem` | `LightboxItem \| null` | The currently displayed item |
| `zoomLevel` | `number` | Current zoom multiplier (1 = fit, up to `max-zoom`) |
| `isPanning` | `boolean` | Whether a pointer-drag pan is active |

## 7. Slots

| Slot | Description |
|------|-------------|
| `(default)` | Trigger elements; `<mj-lightbox-item>` children define the item set |
| `toolbar-actions` | Additional toolbar buttons after built-ins |
| `caption` | Custom caption content for the current item (overrides `items[n].caption`) |
| `prev-icon` | Custom icon for the Prev button |
| `next-icon` | Custom icon for the Next button |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-lightbox-open` | `{ index: number, item: LightboxItem }` | Yes | No | Fired after the lightbox opens |
| `mj-lightbox-close` | `{ reason: 'escape' \| 'backdrop' \| 'close-button' \| 'api' }` | Yes | No | Fired after the lightbox closes |
| `mj-lightbox-change` | `{ index: number, previousIndex: number, item: LightboxItem }` | Yes | No | Fired when the displayed item changes |
| `mj-lightbox-zoom` | `{ level: number }` | Yes | No | Fired when the zoom level changes |
| `mj-lightbox-download` | `{ item: LightboxItem }` | Yes | Yes | Fired when the download button is activated; cancelable to prevent default |

## 9. CSS parts & custom properties

**Parts:**
- `::part(dialog)` — the underlying `<mj-dialog>` element
- `::part(viewport)` — the media display area
- `::part(media)` — the current media element (`img` or `video`)
- `::part(zoom-container)` — the zoom/pan wrapper
- `::part(toolbar)` — the top toolbar bar
- `::part(caption-bar)` — the caption/counter bar
- `::part(prev-button)` — the Prev navigation button
- `::part(next-button)` — the Next navigation button
- `::part(thumbnail-strip)` — the thumbnail row container
- `::part(thumbnail)` — individual thumbnail buttons

**Custom properties:**
- `--mj-lightbox-bg` — background color (default: `var(--mj-color-black-alpha-90)`)
- `--mj-lightbox-toolbar-bg` — toolbar background (default: `rgba(0,0,0,0.6)`)
- `--mj-lightbox-caption-bg` — caption bar background (default: `rgba(0,0,0,0.6)`)
- `--mj-lightbox-control-color` — icon button color (default: `var(--mj-color-white)`)
- `--mj-lightbox-z-index` — z-index (default: `var(--mj-z-lightbox)`)
- `--mj-lightbox-transition-duration` — item change animation duration (default: `var(--mj-duration-enter)`)

## 10. States

- **Closed:** `open` absent; underlying dialog hidden.
- **Open — normal:** Current item displayed at fit-zoom; prev/next buttons visible.
- **Zoomed in:** `zoomLevel > 1`; pan via pointer drag or keyboard; zoom-out button enabled.
- **Zoomed out (fit):** `zoomLevel = 1`; zoom-out button disabled.
- **Panning:** Pointer held and dragged; cursor changes to grab/grabbing.
- **At start (no loop):** Prev button disabled when `current-index=0` and `loop=false`.
- **At end (no loop):** Next button disabled when `current-index=items.length-1` and `loop=false`.
- **Loading:** Current media item loading; skeleton/spinner shown in viewport.
- **Error:** Media load failed; error illustration and message shown.
- **Reduced motion:** Slide transition between items suppressed; zoom transition disabled.

## 11. Behavior & interactions

**Opening:** A trigger element (thumbnail or link with `data-lightbox` or inside the default slot) activates the lightbox. The component records the trigger element for focus restore, opens `<mj-dialog>` in modal mode, and displays `items[current-index]`. Focus moves to the close button (or the dialog root if no interactive toolbar element).

**Navigation:** Prev/Next buttons and arrow keys advance through `items`. When `loop=true`, advancing past the last item wraps to the first and vice versa. Navigation fires `mj-lightbox-change`. Each item transition uses a crossfade or slide animation respecting `prefers-reduced-motion`.

**Zoom (image):** Zoom-in button, keyboard `+`, double-click, and pinch-zoom gesture increase `zoomLevel` by 0.5× up to `max-zoom`. Zoom-out and keyboard `-` decrease. Double-click toggles between fit and 2×. At zoom > 1, the media is pannable by pointer drag, keyboard arrow keys (in pan mode, toggled by activating the media area), and trackpad two-finger drag.

**Video variant:** Zoom disabled. The `<video>` element's native controls are exposed. Prev/Next navigate the item set (pauses current video before transition).

**Swipe navigation (touch):** A horizontal swipe gesture > 30% of viewport width triggers prev/next navigation. Vertical swipe has no effect (reserved for native scroll).

**Focus management:** `<mj-dialog>` handles the focus trap. On close, focus returns to the element that activated the lightbox.

**Scroll lock:** Inherited from `<mj-dialog>` modal behavior.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `ArrowLeft` or `ArrowUp` | Navigate to the previous item |
| `ArrowRight` or `ArrowDown` | Navigate to the next item |
| `+` or `=` | Zoom in (image variant) |
| `-` | Zoom out (image variant) |
| `0` | Reset zoom to fit (image variant) |
| `Escape` | Close the lightbox |
| `Tab` / `Shift+Tab` | Move focus among toolbar controls and nav buttons |
| Arrow keys (when media focused at zoom > 1) | Pan the zoomed image |
| `Home` | Jump to first item |
| `End` | Jump to last item |

## 13. Accessibility

- **Role:** The root is `<mj-dialog>` with `role="dialog"` and `aria-label="Media viewer"` (or the `label` attribute value).
- **`aria-modal="true"`** on the dialog; background content is `inert`.
- **Live region:** A polite `aria-live` region announces item changes: "Image 2 of 10: [alt text or caption]".
- **Media alt text:** Each `<img>` uses `alt` from `LightboxItem.alt`; decorative items use `alt=""`.
- **Controls naming:** Prev/Next buttons have accessible names "Previous" and "Next" (overridable via attributes). Zoom-in: "Zoom in". Zoom-out: "Zoom out". Reset zoom: "Reset zoom". Close: "Close".
- **Thumbnail strip:** Each thumbnail button has an accessible name from the item caption or alt; currently displayed item's thumbnail has `aria-current="true"`.
- **Keyboard zoom/pan availability:** Zoom and pan are keyboard-accessible through dedicated keys; no action requires pointer-only interaction.
- **Focus management:** On open, focus moves to the close button. On close, focus returns to the triggering element.

## 14. Form participation

N/A.

## 15. Internationalization & RTL

- All built-in button labels ("Previous", "Next", "Close", "Zoom in", "Zoom out", "Reset zoom", "Download") are overridable via `prev-label`, `next-label`, `close-label`, `zoom-in-label`, `zoom-out-label`, `zoom-reset-label`, `download-label` attributes.
- Counter format defaults to `"{current} of {total}"`; overridable via `counter-format` attribute using `{current}` and `{total}` tokens.
- RTL: Prev/Next semantics swap arrows and swipe directions; arrow key navigation follows logical direction.

## 16. Progressive enhancement / SSR

Server renders trigger thumbnails as plain `<a href="[full-src]">` links pointing to the full image. Without JS, users navigate directly to the full image URL. On upgrade, the component intercepts link activations and opens the lightbox instead.

## 17. Dependencies

- **Section 6:** Focus-trap utility, Design-token stylesheet, Live-region service.
- **`<mj-dialog>`** — modal container, focus trap, backdrop, Esc handling.
- **`<mj-overlay>`** — transitively via `<mj-dialog>`.
- **`<mj-button>`** — toolbar and navigation buttons.

## 18. Edge cases & error handling

- **Empty `items` array:** Lightbox does not open; console warning logged.
- **`current-index` out of range:** Clamped to valid range; warning logged.
- **Image load error:** Displays an error illustration with the alt text as a message; Next/Prev still work.
- **Video autoplay blocked:** Video displays a prominent play button; no error state shown.
- **Single item:** Prev/Next buttons are hidden; thumbnail strip not shown.
- **Very tall/wide images at zoom=1:** Media fits within the viewport with `object-fit: contain`; letterboxing applied.
- **Rapid navigation:** Item transitions are queued; at most one pending transition; intermediate items are skipped cleanly.
- **Mixed type items:** Each item's `type` field governs rendering; switching between image and video pauses video playback.

## 19. Acceptance criteria

- [ ] Lightbox opens in full-screen modal mode with focus on the close button.
- [ ] Esc closes the lightbox; focus returns to the triggering element.
- [ ] ArrowLeft/ArrowRight navigate items; `mj-lightbox-change` fires on each change.
- [ ] Background content is `inert` while lightbox is open.
- [ ] `aria-live` region announces the current item on navigation.
- [ ] Zoom-in, zoom-out, and reset work via keyboard keys and toolbar buttons.
- [ ] Panning is possible at zoom > 1 via arrow keys and pointer drag.
- [ ] Swipe left/right navigates items on touch devices.
- [ ] Loop wraps correctly; prev/next disable when `loop=false` at boundaries.
- [ ] Image load errors display an accessible error state; navigation continues.
- [ ] Thumbnail strip shows correct `aria-current` on the current item.
- [ ] All toolbar button accessible names are correct and overridable.
- [ ] Counter format is correct and localizable.
- [ ] RTL arrow key navigation is reversed.
- [ ] Reduced-motion disables slide and zoom animations.
- [ ] axe-core reports zero violations in open state.

## 20. Open questions

- Should zoom/pan state persist when navigating between items, or reset to fit on each navigation?
- Should `<mj-lightbox-item>` be a formal sub-element spec or an inline data structure only?
- Should the thumbnail strip support lazy loading of thumbnails (via `IntersectionObserver`)?
