# Tooltip Spec

- **Tag:** `<mj-tooltip>`
- **Class / file:** `MjTooltip` / `mjtooltip.js`
- **Category:** Feedback & status components
- **Primary or Variant:** Primary
- **Synonyms covered:** Help tip, Hint
- **Phase:** P0
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-tooltip>` displays a short, supplemental text hint anchored to a trigger
element. It appears on pointer hover or keyboard focus and disappears when the
pointer leaves or focus moves away. Tooltips use `role="tooltip"` and are linked
to their trigger via `aria-describedby`, so screen readers announce the hint
after the trigger's own accessible name. Tooltips never contain interactive
content and are never the only source of essential information.

## 2. When to use / when not to use

**Use** to provide brief supplemental context for controls whose visible label
is abbreviated (icon-only buttons, truncated text) or where a short clarifying
phrase helps without cluttering the UI.

**Do not use** for information that is essential to completing a task — essential
information must be persistently visible. Do not use for rich or interactive
content (links, buttons, forms) — use `<mj-popover>` instead. Do not use on
elements that are not focusable — tooltips must be reachable by keyboard via the
trigger's focus state. Do not use when a visible label suffices.

## 3. Anatomy

- **Trigger slot** (`part="trigger"`) — `<slot name="trigger">` holds the element
  that owns the tooltip (a button, input, icon, etc.).
- **Popup** (`part="popup"`) — the positioned tooltip bubble; `role="tooltip"`;
  hidden when not open.
- **Arrow** (`part="arrow"`) — optional directional caret pointing toward the
  trigger; `aria-hidden`.
- **Content** (`part="content"`) — `<slot>` (default) inside the popup for the
  tooltip text.

## 4. Variants & modes

| Placement | `placement` value | Description |
|-----------|------------------|-------------|
| Top (default) | `top` | Tooltip appears above the trigger; flips to bottom if insufficient space |
| Bottom | `bottom` | Tooltip appears below; flips to top |
| Start | `start` | Tooltip appears at the inline-start side; flips to end |
| End | `end` | Tooltip appears at the inline-end side; flips to start |
| Top-start | `top-start` | Top-aligned, anchored to the start edge of the trigger |
| Top-end | `top-end` | Top-aligned, anchored to the end edge |
| Bottom-start | `bottom-start` | Bottom-aligned, start edge |
| Bottom-end | `bottom-end` | Bottom-aligned, end edge |

| Trigger event | `trigger` value | Description |
|--------------|----------------|-------------|
| Hover + focus (default) | `hover focus` | Shows on `pointerenter` or `focusin`; hides on `pointerleave` or `focusout` |
| Focus only | `focus` | Shows only on keyboard focus; no pointer hover activation |
| Hover only | `hover` | Shows on pointer hover only; not keyboard-accessible (only valid for decorative hints already reachable another way) |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `content` | string | `""` | Yes | Tooltip text; convenience alternative to using the default slot; slot takes precedence |
| `placement` | string | `"top"` | Yes | Preferred placement relative to the trigger; the overlay engine flips/shifts as needed |
| `trigger` | string | `"hover focus"` | Yes | Space-separated list of trigger events: `hover`, `focus` |
| `show-delay` | number (ms) | `300` | Yes | Delay before the tooltip appears after the trigger condition is met |
| `hide-delay` | number (ms) | `100` | Yes | Delay before the tooltip hides after the trigger condition ends |
| `open` | boolean | `false` | Yes | Programmatic open state; setting `true` shows the tooltip regardless of trigger events |
| `disabled` | boolean | `false` | Yes | Disables the tooltip entirely; the trigger remains functional |
| `arrow` | boolean | `true` | Yes | Renders the directional caret arrow |
| `max-width` | number (px) | `280` | Yes | Maximum width of the tooltip bubble in CSS px |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `open` | `boolean` | Programmatic show/hide; mirrors the `open` attribute |
| `triggerElement` | `Element \| null` | Read-only; the resolved trigger element (the first element in the `trigger` slot, or the previous sibling if the wrapper pattern is used) |

## 7. Slots

| Slot | Description |
|------|-------------|
| `trigger` | The element that activates the tooltip (button, icon, input, etc.) |
| (default) | Tooltip text content; may include simple inline markup (em, strong, code) but no interactive elements |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-tooltip-show` | `{ trigger: "hover"\|"focus"\|"api" }` | Yes | Yes | Fired when the tooltip begins to appear; canceling prevents display |
| `mj-tooltip-hide` | `{ trigger: "hover"\|"focus"\|"api"\|"escape" }` | Yes | Yes | Fired when the tooltip begins to hide; canceling keeps it visible |

## 9. CSS parts & custom properties

**Parts**
- `::part(trigger)` — trigger slot wrapper
- `::part(popup)` — tooltip bubble
- `::part(arrow)` — directional caret
- `::part(content)` — content wrapper inside the bubble

**Custom properties**
| Property | Description |
|----------|-------------|
| `--mj-tooltip-bg` | Tooltip background color |
| `--mj-tooltip-color` | Tooltip text color |
| `--mj-tooltip-border-color` | Tooltip border color (optional outline) |
| `--mj-tooltip-border-radius` | Corner radius |
| `--mj-tooltip-padding-block` | Block-axis padding |
| `--mj-tooltip-padding-inline` | Inline-axis padding |
| `--mj-tooltip-font-size` | Tooltip text font size |
| `--mj-tooltip-max-width` | Maximum bubble width (mirrors the `max-width` attribute default) |
| `--mj-tooltip-shadow` | Box shadow / elevation |
| `--mj-tooltip-arrow-size` | Caret size |
| `--mj-tooltip-z-index` | Stacking context z-index |
| `--mj-tooltip-animation-duration` | Show/hide fade/scale animation duration |
| `--mj-tooltip-offset` | Distance between trigger and bubble |

## 10. States

- **hidden** — `open=false`; popup is `display:none`; not in the accessibility tree.
- **entering** — CSS fade/scale-in animation plays after the show delay elapses.
- **visible** — `open=true`; popup is shown and the trigger's `aria-describedby`
  points to the tooltip id.
- **exiting** — CSS fade/scale-out animation plays before `display:none` is set.
- **disabled** — `disabled=true`; tooltip never shows; trigger is unaffected.
- **keyboard-triggered** — visible due to `focusin`; `Escape` dismisses.
- **programmatically-open** — `open=true` set by script; persists until
  `open=false` is set or a hide trigger fires.

## 11. Behavior & interactions

**Association.** The tooltip popup is assigned a unique `id` (`mj-tooltip-<uid>`).
On show, `aria-describedby="${id}"` is set on the trigger element. On hide, the
attribute is removed. This wires the AT description without moving focus.

**Show/hide timing.** A `show-delay` timer starts when the trigger condition is
met. If the condition ends before the timer fires, the timer is canceled and the
tooltip is never shown. A `hide-delay` timer debounces pointer movement between
the trigger and the tooltip bubble (allowing the pointer to travel over the
tooltip without dismissal).

**Pointer over the tooltip.** When the pointer moves from the trigger onto the
tooltip bubble itself, the hide timer is cleared. Moving off either element
restarts the hide timer.

**Escape key.** When the tooltip is visible and focus is on or within the trigger,
pressing `Escape` hides the tooltip and fires `mj-tooltip-hide` with
`reason="escape"`. Focus remains on the trigger.

**Positioning.** Placement is computed by the overlay/positioning engine (§6):
the preferred `placement` is used when space allows; the engine flips to the
opposite side and shifts along the axis to keep the bubble within the viewport.
The `arrow` part rotates to point toward the trigger after placement is resolved.

**Reduced motion.** When `prefers-reduced-motion: reduce` matches, the enter/exit
animations are replaced with an instant opacity change (no scale/translate).

**Content rule enforcement.** If the default slot contains an interactive element
(a, button, input, etc.), the component logs a console error. Interactive content
inside a tooltip is a WCAG failure; use `<mj-popover>` for such cases.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Tab` / `Shift+Tab` | Moving focus onto the trigger element shows the tooltip (after `show-delay`); moving focus away hides it (after `hide-delay`) |
| `Escape` | Hides the tooltip when focus is on the trigger and the tooltip is visible; focus stays on the trigger |

The tooltip itself is never in the tab order (`tabindex="-1"` on the popup
element). No keys navigate into the tooltip.

## 13. Accessibility

- **Role:** `role="tooltip"` on the popup element.
- **Association:** `aria-describedby` on the trigger element points to the
  tooltip's `id` when visible; removed when hidden. The tooltip is therefore
  not announced on its own — it augments the trigger's description.
- **Focus:** the tooltip popup is never focused. It does not trap focus. The
  trigger remains fully operable while the tooltip is shown.
- **Content restriction:** no interactive elements in the tooltip; WCAG 1.4.13
  (Content on Hover or Focus) requires: content is hoverable (pointer can move
  over it without hiding it), dismissible (`Escape`), and persistent (stays
  until pointer/focus leaves or the user dismisses).
- **Hidden state:** when `open=false`, the popup has `display:none` and is
  removed from the accessibility tree so AT does not read stale content.
- **Color:** tooltip background meets 4.5:1 contrast ratio for text; 3:1 for
  the border against the page background.
- **Target size:** tooltip itself is not interactive; no target size requirement.
  The trigger must still meet its own target-size requirements independently.

## 14. Form participation

N/A — `<mj-tooltip>` is a display-only component.

## 15. Internationalization & RTL

- Tooltip text is entirely host-supplied via the `content` attribute or default
  slot; no internal strings to localize.
- In RTL contexts, `start`/`end` placements are resolved using logical directions
  by the overlay/positioning engine.
- The `arrow` caret direction adjusts to the resolved placement after the engine
  flips/shifts; this is placement-side-based, not LTR/RTL-based.
- If the trigger element carries `lang`, the tooltip inherits it automatically
  as it is a descendant in the composed tree.

## 16. Progressive enhancement / SSR

Server renders the trigger with a native `title` attribute as a no-JS fallback:
```html
<button title="Save your changes" aria-describedby="tip-1">Save</button>
<span id="tip-1" role="tooltip" hidden>Save your changes</span>
```
Before JS loads, the browser shows the native tooltip on hover. On upgrade, the
custom element replaces the `title` attribute (to suppress the native tooltip)
and manages the custom popup. The hidden `<span>` fallback is adopted into the
shadow DOM.

## 17. Dependencies

- **Registry + base element helper** (§6) — lifecycle and attribute reflection.
- **Design-token stylesheet** (§6) — color, spacing, radius, elevation, motion.
- **Overlay/positioning engine** (§6) — placement computation, flip, shift,
  and viewport collision detection.

## 18. Edge cases & error handling

- **No trigger slot content:** the component cannot attach `aria-describedby`
  without a trigger element; a console error is emitted and the tooltip is
  disabled until a trigger element is present.
- **Trigger element removed from the DOM:** the `MutationObserver` in
  `disconnectedCallback` cleans up the `aria-describedby` reference.
- **Interactive content in the default slot:** console error; the content is
  still rendered but the implementation cannot guarantee WCAG 1.4.13 compliance.
- **`content` attribute and default slot both present:** slot content takes
  precedence; `content` attribute is used only when the slot is empty.
- **Very long content text:** the bubble wraps at `--mj-tooltip-max-width`;
  text does not truncate; the bubble grows in height.
- **Tooltip near viewport edges:** the overlay engine shifts the bubble inward;
  the arrow shifts along the bubble edge to continue pointing at the trigger.
- **Multiple tooltips:** each instance is independent; no global singleton
  ensures only one is visible at a time (the 300 ms show delay provides natural
  mutual exclusion in practice, but hosts may implement a tooltip manager if
  strict singleton behavior is needed).

## 19. Acceptance criteria

- [ ] Tooltip shows after `show-delay` on `pointerenter` and `focusin`.
- [ ] Tooltip hides after `hide-delay` on `pointerleave` and `focusout`.
- [ ] Pointer moving from trigger to tooltip bubble cancels the hide timer.
- [ ] `Escape` key hides the tooltip; focus remains on the trigger.
- [ ] `aria-describedby` is set on the trigger when visible; removed when hidden.
- [ ] `role="tooltip"` is present on the popup element.
- [ ] Popup is `display:none` when hidden; not in the accessibility tree.
- [ ] `mj-tooltip-show` and `mj-tooltip-hide` fire with correct `trigger` values.
- [ ] Canceling `mj-tooltip-show` prevents display; canceling `mj-tooltip-hide` keeps it visible.
- [ ] Placement flips when insufficient viewport space exists in the preferred direction.
- [ ] Arrow rotates to point toward the trigger after placement resolution.
- [ ] Enter/exit animations respect `prefers-reduced-motion`.
- [ ] Interactive content in the slot emits a console error.
- [ ] Native `title` attribute is suppressed on upgrade to prevent double-tooltip.
- [ ] No hard-coded colors; all values resolve from design tokens.
- [ ] Passes automated axe accessibility checks with no violations.
- [ ] WCAG 1.4.13 satisfied: hoverable, dismissible with Escape, persistent.

## 20. Open questions

- Should a global tooltip manager (singleton controller) be provided as an
  optional coordination layer to enforce at-most-one-visible behavior?
- Should `show-delay` default to `0` for `focus`-triggered tooltips only
  (matching common UX guidance that keyboard users should see tooltips immediately)?
- Is a `rich` mode needed for multi-line content with a heading, or should
  that always redirect to `<mj-popover>`?
- Should the component support a `for` attribute (pointing to a trigger by id)
  as an alternative to the `trigger` slot, for cases where wrapping the trigger
  is not practical?
