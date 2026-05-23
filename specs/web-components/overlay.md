# Overlay Spec

- **Tag:** `<mj-overlay>`
- **Class / file:** `MjOverlay` / `mjoverlay.js`
- **Category:** Dialogs, overlays & popups
- **Primary or Variant:** Primary
- **Synonyms covered:** Overlay, Backdrop, Scrim, Dimmer
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-overlay>` is a dimming and blocking layer primitive that sits between page content and a floating surface (dialog, drawer, lightbox). It manages scroll lock, `inert` on background content, visual dimming, and optional click-to-dismiss. It is not used as a standalone feature — it is composed by `<mj-dialog>`, `<mj-drawer>`, and `<mj-lightbox>` and is never rendered directly by application authors.

## 2. When to use / when not to use

`<mj-overlay>` is an implementation primitive. Application authors use `<mj-dialog>`, `<mj-drawer>`, or `<mj-lightbox>` and receive the overlay as part of those components. Do not place `<mj-overlay>` standalone in application templates. If a custom floating surface needs a backdrop, compose `<mj-overlay>` inside a custom component following the same patterns.

## 3. Anatomy

- **Backdrop element** — full-viewport `<div>` (or pseudo-element) positioned fixed, covering the viewport.
- **Inert manager** — logic that applies/removes `inert` on sibling DOM trees.
- **Scroll-lock coordinator** — reference-counted utility that sets `overflow: hidden` on `<body>`.
- **Click zone** — the transparent click target that emits `mj-overlay-click`.

## 4. Variants & modes

| Variant | `variant` value | Notes |
|---------|----------------|-------|
| Dimming (default) | `dim` | Semi-transparent dark backdrop |
| Blocking (no dim) | `block` | Invisible but blocks pointer events |
| Transparent | `transparent` | Passes through visually; blocks keyboard via `inert` |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `visible` | boolean | `false` | Yes | Renders and displays the overlay |
| `variant` | `dim` \| `block` \| `transparent` | `dim` | Yes | Visual mode of the backdrop |
| `scroll-lock` | boolean | `true` | Yes | Applies scroll lock to `<body>` when visible |
| `inert-target` | string | `""` | Yes | CSS selector for elements to mark `inert`; defaults to siblings of the overlay's containing surface |
| `z-index` | number | — | Yes | Explicit z-index; defaults to `var(--mj-z-overlay)` from tokens |
| `animation` | boolean | `true` | Yes | Whether the backdrop fades in/out |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `lockCount` | `number` | Current reference count for scroll lock (shared across overlay instances) |
| `inertEls` | `HTMLElement[]` | Elements currently marked `inert` by this instance |

## 7. Slots

| Slot | Description |
|------|-------------|
| (none) | `<mj-overlay>` has no content slots; it is a purely visual/behavioral primitive |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-overlay-click` | `{ target: HTMLElement }` | Yes | Yes | Fired when the backdrop area is clicked; parent component cancels to prevent light-dismiss |
| `mj-overlay-visible` | `{}` | Yes | No | Fired after the backdrop finishes its enter transition |
| `mj-overlay-hidden` | `{}` | Yes | No | Fired after the backdrop finishes its exit transition |

## 9. CSS parts & custom properties

**Parts:**
- `::part(backdrop)` — the backdrop element

**Custom properties:**
- `--mj-overlay-color` — backdrop fill color (default: `var(--mj-color-black-alpha-50)`)
- `--mj-overlay-z-index` — z-index of the backdrop (default: `var(--mj-z-overlay)`)
- `--mj-overlay-duration` — fade duration (default: `var(--mj-duration-enter)`)
- `--mj-overlay-blur` — optional backdrop blur radius (default: `0`)

## 10. States

- **Hidden (default):** `visible` absent; backdrop not rendered (or `display: none`).
- **Visible:** `visible` present; backdrop covers the viewport; scroll locked if `scroll-lock=true`; inert applied.
- **Entering:** Fade-in animation in progress.
- **Exiting:** Fade-out animation in progress; `inert` and scroll lock released after animation completes.
- **Reduced motion:** Fade animation disabled; instant show/hide.

## 11. Behavior & interactions

**Activation:** The parent surface sets `visible=true`. The overlay renders the backdrop, applies `inert` to target elements (computed from `inert-target` selector or auto-detected siblings of the parent surface), and increments the shared scroll-lock counter. If `scroll-lock=true` and the counter transitions from 0 to 1, `overflow: hidden` is set on `<body>`.

**Deactivation:** The parent surface sets `visible=false`. The exit animation begins (if `animation=true`). After the animation completes (via `transitionend`), `inert` is removed, the scroll-lock counter is decremented, and `overflow: hidden` is removed if the counter reaches 0.

**Stacking:** Multiple overlays may coexist (e.g., a dialog inside a drawer). Each independently manages its own `inert` targets and increments the shared scroll-lock counter. The highest `z-index` overlay is the one visually on top.

**Click handling:** Pointer events on the backdrop element fire `mj-overlay-click` on the overlay. The parent component listens for this event and decides whether to close. If the parent cancels the event, nothing further happens (e.g., when `close-on-backdrop=false`).

**Inert management:** The overlay adds `inert` to each matched `inert-target` element, storing references to restore them. On deactivation, `inert` is removed from stored elements only; no other elements are touched.

**Forced-colors mode:** In Windows High Contrast, the backdrop uses `ButtonFace` / `Canvas` to remain visible.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| (none) | The overlay itself is not keyboard-interactive; focus management is the responsibility of the parent surface |

## 13. Accessibility

- **Role:** The backdrop element has `role="presentation"` — it is purely visual.
- **`aria-hidden="true"`** on the backdrop element so screen readers ignore it.
- **Inertness:** The key accessibility contribution of `<mj-overlay>` is applying `inert` to background content, which hides it from AT and prevents keyboard navigation outside the modal surface.
- **Scroll lock:** Prevents the page behind a modal from scrolling, which avoids confusing positional context changes for AT users.
- **No keyboard trap:** The overlay does not trap focus; the parent surface is responsible for that.
- **Focus:** `<mj-overlay>` never holds or moves focus.

## 14. Form participation

N/A.

## 15. Internationalization & RTL

No user-visible strings or direction-sensitive layout. `<mj-overlay>` covers the full viewport regardless of direction.

## 16. Progressive enhancement / SSR

Server renders an absent or hidden `<mj-overlay>`. Without JS, the backdrop does not appear; the parent surface degrades per its own progressive enhancement strategy. On upgrade, the overlay is controlled programmatically by the parent.

## 17. Dependencies

- **Section 6:** Design-token stylesheet (for color/z-index/duration tokens), shared scroll-lock utility.
- No other components — `<mj-overlay>` is a foundation primitive, not a composite.

## 18. Edge cases & error handling

- **`inert-target` selector matches no elements:** No-op with a console warning; overlay still shows.
- **Multiple rapid `visible` toggles:** Transition is canceled and restarted; the lock counter remains consistent because it is adjusted only on settled state changes (visible→hidden or hidden→visible), not during transitions.
- **`<body>` scroll already locked by another mechanism:** The reference counter prevents double-locking or premature unlocking.
- **Overlay destroyed while visible:** `disconnectedCallback` releases scroll lock and removes `inert` from all tracked elements.
- **High-contrast mode:** Backdrop may be rendered as a `Canvas` color block; ensured by forced-colors CSS.
- **`z-index` conflict:** The overlay's `z-index` is set via the `--mj-z-overlay` token; parent surfaces set their own `z-index` one unit higher via their own token.

## 19. Acceptance criteria

- [ ] Backdrop appears with fade-in when `visible=true` and disappears with fade-out when `visible=false`.
- [ ] Scroll lock is applied to `<body>` when first overlay becomes visible; released when last overlay is hidden.
- [ ] `inert` is applied to correct elements on show and removed on hide.
- [ ] `mj-overlay-click` fires when backdrop is clicked; canceling prevents propagation to parent dismiss logic.
- [ ] Multiple stacked overlays each manage their own inert targets; scroll lock counter is correct.
- [ ] `role="presentation"` and `aria-hidden="true"` present on backdrop.
- [ ] `disconnectedCallback` releases all locks and inert assignments.
- [ ] Reduced-motion: no fade animation; instant show/hide.
- [ ] Forced-colors mode: backdrop is visible.
- [ ] `variant="block"` shows an invisible click-blocking layer; `variant="transparent"` applies no visual change.

## 20. Open questions

- Should the shared scroll-lock utility be a standalone ES module importable by non-overlay code, or tightly coupled to `<mj-overlay>`?
- Should `inert-target` default auto-detection walk to the document body and mark all siblings of the containing stacking context, or only direct siblings of the parent surface?
- Is a `blur-behind` effect (CSS `backdrop-filter: blur()`) a configuration attribute or left entirely to `--mj-overlay-blur`?
