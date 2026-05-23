# Popover Spec

- **Tag:** `<mj-popover>`
- **Class / file:** `MjPopover` / `mjpopover.js`
- **Category:** Dialogs, overlays & popups
- **Primary or Variant:** Primary
- **Synonyms covered:** Popover, Hovercard, Help bubble, Callout (overlay form)
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-popover>` is an anchored, non-modal overlay that may contain interactive content such as links, buttons, and forms. It is positioned relative to a trigger element using the Section 6 overlay/positioning engine and supports the browser native `popover` API where available. It covers rich overlay use cases including informational hovercards and contextual help bubbles.

## 2. When to use / when not to use

Use when you need an anchored overlay richer than a tooltip — one that may contain interactive content or structured information. Use the `hover` trigger mode for hovercards (brief contextual previews on pointer hover). Use for help bubbles that explain a field or feature. Do not use for transient status messages (use `<mj-toast-region>`), modal blocking interactions (use `<mj-dialog>`), or simple non-interactive hints (use `<mj-tooltip>`). Do not place required-form controls inside a popover.

## 3. Anatomy

- **Trigger element** — the slotted element (or `trigger-id` target) that opens and closes the popover.
- **Popup panel** — the positioned overlay container holding slotted content.
- **Arrow / caret** — optional decorative pointer indicating the anchor.
- **Close button** — optional built-in close control for non-hover triggers.
- **Content area** — default slot for arbitrary interactive or informational content.

## 4. Variants & modes

| Variant | `variant` value | Trigger | Notes |
|---------|----------------|---------|-------|
| Popover (default) | `popover` | click / focus | General-purpose anchored overlay |
| Hovercard | `hovercard` | `hover-intent` (200 ms delay) | Opens on pointer-enter; closes on pointer-leave + delay |
| Help bubble | `help` | click | Icon-button trigger; informational content only |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `open` | boolean | `false` | Yes | Controls open/closed state |
| `variant` | `popover` \| `hovercard` \| `help` | `popover` | Yes | Selects behavioral mode |
| `trigger-id` | string | `""` | Yes | ID of an external element to act as the trigger |
| `placement` | `top` \| `bottom` \| `start` \| `end` \| `top-start` \| `top-end` \| `bottom-start` \| `bottom-end` | `bottom` | Yes | Preferred placement; engine flips/shifts on collision |
| `offset` | number | `8` | Yes | Distance in px between anchor and popup panel |
| `hover-delay` | number | `200` | Yes | Milliseconds before hovercard opens on pointer-enter |
| `hover-out-delay` | number | `300` | Yes | Milliseconds before hovercard closes on pointer-leave |
| `arrow` | boolean | `true` | Yes | Shows or hides the arrow/caret |
| `light-dismiss` | boolean | `true` | Yes | Whether clicking outside or pressing Esc closes the popover |
| `no-close-button` | boolean | `false` | Yes | Hides the built-in close button |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `triggerEl` | `HTMLElement \| null` | Resolved trigger element (from slot or `trigger-id`) |
| `popupEl` | `HTMLElement` | The internal popup panel element |
| `computedPlacement` | `string` | Actual placement after collision resolution |

## 7. Slots

| Slot | Description |
|------|-------------|
| `trigger` | The activating element; receives `aria-expanded` and `aria-haspopup` |
| `(default)` | Popover body content (may be interactive) |
| `header` | Optional heading area inside the popup |
| `footer` | Optional footer actions inside the popup |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-popover-open` | `{ placement: string }` | Yes | No | Fired after the popover opens and is positioned |
| `mj-popover-close` | `{ reason: 'escape' \| 'light-dismiss' \| 'trigger' \| 'api' }` | Yes | No | Fired after the popover closes |
| `mj-popover-before-open` | `{}` | Yes | Yes | Fired before opening; cancelable |
| `mj-popover-before-close` | `{ reason }` | Yes | Yes | Fired before closing; cancelable |
| `mj-popover-placement-change` | `{ placement: string }` | Yes | No | Fired when computed placement changes due to collision |

## 9. CSS parts & custom properties

**Parts:**
- `::part(popup)` — the popup panel container
- `::part(arrow)` — the directional arrow/caret element
- `::part(header)` — the optional header area
- `::part(body)` — the content area
- `::part(footer)` — the optional footer area
- `::part(close-button)` — the built-in close button

**Custom properties:**
- `--mj-popover-width` — popup panel width (default: `18rem`)
- `--mj-popover-padding` — panel padding (default: `var(--mj-space-4)`)
- `--mj-popover-radius` — border radius (default: `var(--mj-radius-md)`)
- `--mj-popover-shadow` — box shadow (default: `var(--mj-elevation-3)`)
- `--mj-popover-bg` — background color (default: `var(--mj-color-surface)`)
- `--mj-popover-arrow-size` — arrow dimensions (default: `8px`)
- `--mj-popover-z-index` — z-index (default: `var(--mj-z-popover)`)

## 10. States

- **Closed (default):** Popup panel is hidden; trigger shows `aria-expanded="false"`.
- **Open:** Popup panel visible in top layer (via `popover` API or positioning engine); trigger shows `aria-expanded="true"`.
- **Hover-intent pending:** Hover delay timer active; popup not yet shown.
- **Flipped:** `computedPlacement` differs from `placement`; `data-placement` attribute updated for arrow CSS.
- **Reduced motion:** Open/close transitions suppressed.

## 11. Behavior & interactions

**Opening:** For click/focus triggers, activating the trigger element (click or Enter/Space) sets `open=true`. The Section 6 positioning engine anchors the popup to the trigger, resolving placement with flip and shift on viewport collision. The `popover` API (`showPopover()`) is used where browser-supported; otherwise the panel is appended to the document body and positioned via absolute coordinates.

**Hovercard mode:** On `pointerenter` of the trigger, a timer (`hover-delay`) starts. If the pointer leaves before the timer fires, the timer is canceled. On open, a second timer (`hover-out-delay`) starts when the pointer leaves both the trigger and the popup panel; reaching zero closes the popover. Moving the pointer back onto either element cancels the out-timer.

**Focus management (non-modal):** Focus is NOT trapped. When the popover opens via keyboard, focus moves into the popup (first focusable element). Tab continues through the popup's content and then exits naturally. Closing the popover returns focus to the trigger element.

**Light dismiss:** Clicks outside the trigger + popup area and Escape key close the popover (when `light-dismiss=true`). The `mj-popover-before-close` event is fired and is cancelable.

**Positioning updates:** A `ResizeObserver` on the trigger and popup, and a `scroll` event listener on all scroll ancestors, re-run the positioning engine on every change to keep the popup anchored correctly.

**Scroll behavior:** The popup scrolls its own content if taller than `--mj-popover-max-height`; the page scrolls normally behind it.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Enter` or `Space` on trigger | Opens or closes the popover |
| `Escape` | Closes the popover; focus returns to the trigger |
| `Tab` | Moves focus forward through popup content; exits popup when content exhausted |
| `Shift+Tab` | Moves focus backward through popup content; exits popup when content exhausted |

## 13. Accessibility

- **Roles:** The popup panel uses no explicit landmark role by default (content is generic). The `trigger` slot element receives `aria-haspopup="dialog"` (or `"true"` for generic popovers) and `aria-expanded="false"/"true"` reflecting open state.
- **`aria-controls`:** Trigger element's `aria-controls` attribute is set to the popup panel's ID.
- **Naming:** The popup panel is labeled by its header slot content via `aria-labelledby`; if no header, the popover is described by `aria-label` or document context.
- **Focus management:** On keyboard open, focus moves to the first focusable element inside the popup. On close, focus returns to the trigger.
- **Hovercard mode:** Only accessible via keyboard trigger; pure hover is not sufficient. The hovercard must be dismissible with Esc.
- **No focus trap:** Being non-modal, Tab may exit the popup naturally; this is intentional.
- **`aria-live`:** Not used; content is not dynamically changing after open.

## 14. Form participation

N/A. `<mj-popover>` is not form-associated. Form controls placed inside a popover are part of their own form context.

## 15. Internationalization & RTL

- Close button label defaults to `"Close"` and is overridable via `close-label` attribute.
- RTL: `start`/`end` placements resolve to left/right per document direction. The arrow shifts accordingly. The positioning engine consumes the `dir` attribute.

## 16. Progressive enhancement / SSR

Server renders `<mj-popover>` with slotted trigger and content. Without JS, the popover panel is visible as static adjacent content (or hidden with CSS). On upgrade, the component manages show/hide, positioning, and focus. A `<details>/<summary>` fallback inside the slot is recommended for help-bubble content.

## 17. Dependencies

- **Section 6:** Overlay/positioning engine (anchor, flip, shift, top-layer), Focus utilities (focus restore), Design-token stylesheet.
- **`<mj-button>`** — built-in close button.

## 18. Edge cases & error handling

- **Trigger element not found** (`trigger-id` invalid): A console error is logged; popover does not open.
- **Popup taller than viewport:** Popup constrains to `100vh` minus offset and scrolls internally.
- **`popover` API unsupported:** Falls back to absolute-positioned DOM injection with equivalent stacking.
- **Multiple popovers open simultaneously:** Each manages its own state independently; light-dismiss closes all on outside click unless nested.
- **Hovercard with no interactive content:** Acceptable; functions as a rich tooltip. Ensure `role="tooltip"` is not misused here — keep generic role.
- **Trigger removed from DOM while open:** Popover closes immediately; focus falls back to `document.body`.
- **Rapid open/close:** Animation frames are debounced; positioning is not recalculated more than once per frame.

## 19. Acceptance criteria

- [ ] Popover opens anchored to its trigger with correct placement.
- [ ] Viewport collision causes automatic flip/shift; `mj-popover-placement-change` fires.
- [ ] Esc closes the popover; focus returns to trigger.
- [ ] Light-dismiss on outside click closes the popover.
- [ ] `aria-expanded` and `aria-controls` on trigger are correct in open and closed states.
- [ ] Hovercard opens after `hover-delay`; closes after `hover-out-delay` when pointer leaves both trigger and popup.
- [ ] Tab navigates through popup content and exits without trapping.
- [ ] On keyboard open, first focusable element inside popup receives focus.
- [ ] `light-dismiss=false` prevents Esc and outside-click from closing.
- [ ] RTL placement (`start`/`end`) reflects document `dir` correctly.
- [ ] Native `popover` API used when available; fallback works in non-supporting browsers.
- [ ] axe-core reports zero violations in open state.
- [ ] Reduced-motion: no transition animation fires.

## 20. Open questions

- Should `hovercard` variant support a `trigger-focus` sub-mode (opens on focus, not just hover) as a separate attribute?
- Should the positioning engine be configured via a single `positioning-options` property (object) or individual attributes per axis?
- Do we need a `singleton` mode where only one `<mj-popover>` can be open at a time across a given scope?
