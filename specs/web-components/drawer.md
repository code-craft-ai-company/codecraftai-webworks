# Drawer Spec

- **Tag:** `<mj-drawer>`
- **Class / file:** `MjDrawer` / `mjdrawer.js`
- **Category:** Dialogs, overlays & popups
- **Primary or Variant:** Primary
- **Synonyms covered:** Drawer, Sheet, Bottom sheet, Side panel, Slide-over
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-drawer>` is an edge-anchored panel that slides in from one side of the viewport. It supports modal and non-modal modes and covers side panels, action sheets, and bottom sheets. In modal mode it traps focus and dims the background via `<mj-overlay>`. Bottom-sheet behavior is selected by setting `edge="bottom"`.

## 2. When to use / when not to use

Use when supplemental content, navigation, or detailed actions need a large, structured surface without fully blocking the primary content. Use `edge="bottom"` (Bottom sheet) for mobile-style action sheets or filter panes. Do not use for focused confirmations requiring an immediate decision (use `<mj-dialog>`). Do not use as the primary navigation rail — use `<mj-side-nav>` in its `overlay-drawer` mode for that. Avoid using non-modal drawers for critical alerts.

## 3. Anatomy

- **`<mj-overlay>` backdrop** — dimming layer shown behind modal drawers.
- **Panel** — the sliding container anchored to the viewport edge.
- **Header** — title, optional subtitle, and close button.
- **Body** — scrollable content area.
- **Footer** — optional sticky action bar.
- **Drag handle** — visible grip for swipe-to-dismiss on touch devices (bottom sheet).
- **Close button** — labeled icon button in the header.

## 4. Variants & modes

| Variant | `edge` value | `modal` | Notes |
|---------|-------------|---------|-------|
| Start drawer | `start` | `true` (default) | Slides in from the inline-start edge |
| End drawer | `end` | `true` | Slides in from the inline-end edge |
| Top sheet | `top` | `true` | Slides in from the top |
| Bottom sheet | `bottom` | `true` | Slides in from the bottom; drag handle shown |
| Non-modal side panel | `start` or `end` | `false` | No backdrop; no focus trap; coexists with page content |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `open` | boolean | `false` | Yes | Controls open/closed state |
| `edge` | `start` \| `end` \| `top` \| `bottom` | `end` | Yes | Viewport edge the panel slides from |
| `modal` | boolean | `true` | Yes | Whether the drawer traps focus and shows a backdrop |
| `size` | string | `20rem` | Yes | Width (start/end) or height (top/bottom) of the panel |
| `label` | string | `""` | Yes | `aria-label` for the drawer panel; falls back to title slot |
| `close-on-backdrop` | boolean | `true` | Yes | Whether clicking the backdrop closes the drawer |
| `no-close-button` | boolean | `false` | Yes | Hides the built-in close button |
| `swipe-to-dismiss` | boolean | `true` | Yes | Enables swipe gesture dismissal on touch (bottom sheet) |
| `return-focus-id` | string | `""` | Yes | ID of element to restore focus to on close |
| `persistent` | boolean | `false` | Yes | Non-modal drawer that pushes content rather than overlaying it |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `returnFocusEl` | `HTMLElement \| null` | Element to receive focus on close |
| `panelEl` | `HTMLElement` | The internal panel container element |
| `dragProgress` | `number` | 0–1 progress of an active swipe gesture (bottom sheet) |

## 7. Slots

| Slot | Description |
|------|-------------|
| `(default)` | Main body content |
| `header` | Custom header; replaces built-in title + close button |
| `title` | Drawer title text; used for `aria-labelledby` |
| `footer` | Sticky footer content |
| `drag-handle` | Custom drag handle element (bottom sheet) |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-drawer-open` | `{ edge: string }` | Yes | No | Fired after the drawer opens and transitions complete |
| `mj-drawer-close` | `{ edge: string, reason: 'close-button' \| 'backdrop' \| 'escape' \| 'swipe' \| 'api' }` | Yes | No | Fired after the drawer closes |
| `mj-drawer-before-close` | `{ reason }` | Yes | Yes | Fired before closing; cancelable |
| `mj-drawer-swipe` | `{ progress: number }` | Yes | No | Fired during active swipe; `progress` is 0–1 |

## 9. CSS parts & custom properties

**Parts:**
- `::part(panel)` — the sliding panel
- `::part(header)` — the header bar
- `::part(title)` — the title element
- `::part(close-button)` — the header close button
- `::part(body)` — the scrollable content area
- `::part(footer)` — the sticky footer
- `::part(drag-handle)` — the swipe handle (bottom sheet)
- `::part(overlay)` — the backdrop overlay

**Custom properties:**
- `--mj-drawer-size` — panel width or height override (default: inherits `size` attribute)
- `--mj-drawer-padding` — body padding (default: `var(--mj-space-5)`)
- `--mj-drawer-radius` — corner radius on the exposed edges (default: `var(--mj-radius-lg)`)
- `--mj-drawer-shadow` — panel shadow (default: `var(--mj-elevation-4)`)
- `--mj-drawer-bg` — panel background (default: `var(--mj-color-surface)`)
- `--mj-drawer-z-index` — z-index (default: `var(--mj-z-drawer)`)
- `--mj-drawer-duration` — slide animation duration (default: `var(--mj-duration-enter)`)

## 10. States

- **Closed:** Panel off-screen; `open` attribute absent; `inert` on panel.
- **Opening:** Slide-in transition in progress; `aria-busy="true"` on panel during transition.
- **Open:** Panel fully visible; focus trapped when modal; `aria-expanded` on trigger if wired.
- **Closing:** Slide-out transition; focus restoration queued.
- **Swiping (bottom sheet):** `dragProgress` > 0; panel partially translated.
- **Non-modal / persistent:** Panel coexists with page; `margin-inline-start/end` applied to main content when `persistent=true`.
- **Reduced motion:** Transitions suppressed; panel appears/disappears instantly.

## 11. Behavior & interactions

**Opening:** Setting `open=true` or calling `show()` triggers the slide-in animation. When `modal=true`, `<mj-overlay>` appears, siblings receive `inert`, and the Section 6 focus-trap utility is installed. Focus moves to the first focusable element in the panel.

**Closing:** Triggered by Esc, backdrop click (when `close-on-backdrop=true`), the close button, swipe gesture, or `close()`. `mj-drawer-before-close` fires; if not canceled, the panel slides out, `inert` is removed, and focus returns to `returnFocusEl`.

**Persistent mode:** `persistent=true` with `modal=false` causes the panel to push the adjacent content region. The host page layout must cooperate via a CSS custom property `--mj-drawer-offset` that the component updates.

**Swipe-to-dismiss (bottom sheet):** On `touchstart` on the drag handle or panel header, the component tracks `touchmove` delta and translates the panel via CSS transform. A release at > 40% displacement or velocity > 0.5 px/ms triggers close. Below threshold, the panel snaps back.

**Scroll behavior:** Body content scrolls within the panel. Touch scroll on the body content is distinguished from drag-to-dismiss by a direction lock (vertical scroll on inner content, dismiss gesture only when scroll is at the top).

**Scroll lock:** `overflow: hidden` on `<body>` when modal (shared scroll-lock utility).

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Escape` | Closes the drawer |
| `Tab` | Cycles focus forward within the panel (modal mode wraps) |
| `Shift+Tab` | Cycles focus backward within the panel (modal mode wraps) |
| `Space` or `Enter` on close button | Closes the drawer |

## 13. Accessibility

- **Role:** The panel element has `role="dialog"` and `aria-modal="true"` when modal; non-modal drawers use `role="complementary"` or `role="region"` with a distinct accessible name.
- **Naming:** `aria-labelledby` points to the title slot element; falls back to `aria-label` from `label` attribute.
- **Inertness:** All sibling content receives `inert` when modal, preventing background keyboard/AT navigation.
- **Focus management:** On open, focus moves to first focusable element in the panel. On close, focus returns to the triggering element.
- **Drag handle:** Labeled `aria-label="Drag to dismiss"` for screen readers; also provides a keyboard-activatable close button in the header.
- **Swipe gesture:** Swipe-to-dismiss is a progressive enhancement; keyboard dismissal via Esc is always available.
- **`aria-hidden` on close:** Panel gets `aria-hidden="true"` after close animation completes.

## 14. Form participation

N/A. The drawer is a container; form controls inside it are part of their enclosing form by normal DOM relationships.

## 15. Internationalization & RTL

- `edge="start"` and `edge="end"` resolve to left and right per the document's `dir` attribute.
- Built-in strings: `close-label` attribute overrides the close button's accessible name (default: `"Close"`).
- RTL: slide direction inverts for start/end edges; drag handle position mirrors.

## 16. Progressive enhancement / SSR

Server renders the drawer panel as a `<section>` or `<aside>` with slotted content. Without JS, the panel is displayed as a static adjacent block (not modal). On upgrade, the component adds transitions, focus management, and the overlay. Use `hidden` attribute on the server to hide modal drawers by default.

## 17. Dependencies

- **Section 6:** Focus-trap utility, Overlay/positioning engine, Live-region service, Design-token stylesheet.
- **`<mj-overlay>`** — backdrop and scroll lock.
- **`<mj-button>`** — close button.

## 18. Edge cases & error handling

- **No focusable content in panel:** Focus falls back to the panel element itself (`tabindex="-1"`).
- **Panel taller/wider than viewport:** Panel constrains to 100% of the relevant viewport dimension; body scrolls.
- **`persistent=true` with `modal=true`:** Conflict; `modal=true` takes precedence; warning logged.
- **Bottom sheet opened programmatically while keyboard scroll is active:** Scroll lock prevents body scroll; inner scroll still works.
- **Swipe started outside drag handle area:** Gesture only begins on the handle or panel header to avoid blocking inner scroll.
- **Animation interrupted by rapid open/close calls:** Transition is canceled immediately; element snaps to target state.

## 19. Acceptance criteria

- [ ] Panel slides in from the correct edge for each `edge` value.
- [ ] Modal drawer traps focus; Tab and Shift+Tab cycle within the panel.
- [ ] Esc closes the drawer; `mj-drawer-before-close` fires and is cancelable.
- [ ] Background receives `inert` when modal; AT cannot navigate outside the panel.
- [ ] Focus restored to the triggering element on close.
- [ ] Backdrop click closes when `close-on-backdrop=true`; does not close when `false`.
- [ ] Bottom sheet swipe-to-dismiss closes at > 40% displacement; snaps back below threshold.
- [ ] `mj-drawer-swipe` events fire with correct `progress` values during gesture.
- [ ] `persistent=true` non-modal drawer pushes page content without overlap.
- [ ] `edge="start"/"end"` swap sides in RTL documents.
- [ ] `aria-modal="true"` and `role="dialog"` present on modal panel.
- [ ] Close button accessible name is configurable via `close-label`.
- [ ] Reduced-motion: no slide animation; instant show/hide.
- [ ] axe-core reports zero violations in open state.

## 20. Open questions

- Should `persistent=true` be implemented in phase 1 or deferred to phase 2 (requires host layout cooperation)?
- Should the drag handle be shown for all edges or only `bottom` by default?
- Is there a use case for a `resizable` attribute (user-draggable size handle on the exposed edge)?
