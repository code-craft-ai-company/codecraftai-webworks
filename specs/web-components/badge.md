# Badge Spec

- **Tag:** `<mj-badge>`
- **Class / file:** `MjBadge` / `mjbadge.js`
- **Category:** Feedback & status components
- **Primary or Variant:** Primary
- **Synonyms covered:** Counter, Status dot, Presence indicator
- **Phase:** P0
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-badge>` is a small, overlaid or inline indicator that draws attention to a
count, status, or presence state on a parent element. It consolidates three
related patterns: **count** badges (numeric values such as unread message counts),
**dot** badges (a small colored circle with no text, signaling "new" or "active"),
and **status** badges (a colored dot with a text alternative that communicates
online presence or entity state). Status is never conveyed by color alone.

## 2. When to use / when not to use

**Use `count`** to show the number of unread items, notifications, or other
accumulated quantities on an icon or avatar.

**Use `dot`** when the exact count is unimportant and you only need to signal
that something is new or requires attention.

**Use `status`** (Presence indicator) to show online/away/offline/busy state on
an avatar or entity card.

**Do not use** a count badge for a value the user needs to read carefully —
place important numbers in visible body copy instead. Do not use badges to
replace inline text labels; they augment an existing element. Do not use a
colored dot as the sole means of conveying state — always pair it with a
text alternative.

## 3. Anatomy

- **Host wrapper** — `<mj-badge>` acts as a positioning context; the default
  slot holds the element being badged (e.g., an icon, avatar, or button).
- **Indicator** (`part="indicator"`) — the visible badge element; a `<span>`
  overlaid on the slotted content (count/dot) or placed inline (standalone).
- **Count text** (`part="count"`) — the numeric string inside the indicator
  (count variant only).
- **Accessible label** — a visually hidden `<span>` (or `aria-label` on the
  indicator) that provides the full readable description to screen readers.

## 4. Variants & modes

| Variant | `variant` value | Description |
|---------|-----------------|-------------|
| Count | `count` (default) | Displays a numeric count; overflows to `"99+"` by default |
| Dot | `dot` | Small filled circle; no text; signals "new/unread" |
| Status | `status` | Colored dot with text alternative for presence/entity state |

| Status value | `status` attribute | Color token | Default accessible label |
|-------------|-------------------|-------------|------------------------|
| Online | `online` | `--mj-color-status-online` (green) | "Online" |
| Away | `away` | `--mj-color-status-away` (yellow) | "Away" |
| Busy | `busy` | `--mj-color-status-busy` (red) | "Busy" |
| Offline | `offline` | `--mj-color-status-offline` (grey) | "Offline" |
| Do not disturb | `dnd` | `--mj-color-status-dnd` (red) | "Do not disturb" |

Placement modes (applies to count and dot):

| Placement | `placement` value | Description |
|-----------|------------------|-------------|
| Overlap top-end | `top-end` (default) | Overlaid at the top-end corner of the slotted content |
| Overlap top-start | `top-start` | Overlaid at the top-start corner |
| Overlap bottom-end | `bottom-end` | Overlaid at the bottom-end corner |
| Overlap bottom-start | `bottom-start` | Overlaid at the bottom-start corner |
| Inline | `inline` | Renders next to content, not overlaid; use when there is no slotted anchor |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `variant` | `"count"\|"dot"\|"status"` | `"count"` | Yes | Visual variant |
| `count` | number | `0` | Yes | Numeric value for the count variant; `0` hides the badge by default |
| `max` | number | `99` | Yes | Overflow threshold; values above this display as `"<max>+"` |
| `show-zero` | boolean | `false` | Yes | Show the badge when `count` is `0` |
| `status` | `"online"\|"away"\|"busy"\|"offline"\|"dnd"` | `""` | Yes | Presence state for the status variant; also sets the fill color |
| `label` | string | `""` | Yes | Accessible label override; used as `aria-label` on the indicator and in the visually hidden text; required for dot and status variants |
| `placement` | `"top-end"\|"top-start"\|"bottom-end"\|"bottom-start"\|"inline"` | `"top-end"` | Yes | Position of the indicator relative to slotted content |
| `color` | string | `""` | Yes | CSS color or token override for the indicator background; empty uses variant/status defaults |
| `pulse` | boolean | `false` | Yes | Applies a subtle pulsing animation to the dot/status indicator; suppressed when `prefers-reduced-motion: reduce` matches |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `count` | `number` | Current count value; mirrors the `count` attribute |
| `displayCount` | `string` | Read-only; the string shown in the badge: the count, `"<max>+"`, or `""` |
| `hidden` | `boolean` | Read-only; `true` when the badge is not rendered (count `0` and `show-zero` is false) |

## 7. Slots

| Slot | Description |
|------|-------------|
| (default) | The element the badge is anchored to (icon, avatar, button, etc.). When empty, the badge renders inline |
| `indicator` | Replaces the entire indicator element with custom content (advanced override) |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-badge-overflow` | `{ count, max, displayCount }` | Yes | No | Fired when `count` exceeds `max` and the display switches to the overflow string |
| `mj-badge-hide` | `{ count }` | Yes | No | Fired when the badge transitions from visible to hidden (`count` drops to `0` and `show-zero` is false) |
| `mj-badge-show` | `{ count }` | Yes | No | Fired when the badge transitions from hidden to visible |

## 9. CSS parts & custom properties

**Parts**
- `::part(indicator)` — the badge circle/pill element
- `::part(count)` — the text span inside the count indicator

**Custom properties**
| Property | Description |
|----------|-------------|
| `--mj-badge-bg` | Indicator background color |
| `--mj-badge-color` | Indicator text color (count variant) |
| `--mj-badge-border-color` | Outline/ring around the indicator (for contrast against varied backgrounds) |
| `--mj-badge-border-width` | Width of the outline ring |
| `--mj-badge-size` | Diameter of the dot/status indicator, or height of the count pill |
| `--mj-badge-font-size` | Count text font size |
| `--mj-badge-font-weight` | Count text font weight |
| `--mj-badge-border-radius` | Border radius (defaults to `9999px` for a pill/circle shape) |
| `--mj-badge-offset-x` | Horizontal offset from the corner anchor point |
| `--mj-badge-offset-y` | Vertical offset from the corner anchor point |
| `--mj-badge-pulse-color` | Color of the pulse animation ring |

## 10. States

- **hidden** — `count=0` and `show-zero=false`; `display:none` on the indicator.
- **visible** — count > 0 (or `show-zero`), or any status/dot variant.
- **overflow** — `count > max`; indicator displays `"<max>+"`.
- **pulsing** — `pulse=true` and `prefers-reduced-motion` is not `reduce`;
  a subtle ring animation draws attention.
- **inline** — `placement="inline"`; indicator follows normal flow.
- **overlaid** — all non-inline placements; indicator is `position: absolute`
  relative to the host.

## 11. Behavior & interactions

`<mj-badge>` is a non-interactive display component. It contains no focusable
elements of its own. The accessible information it carries must be surfaced via
the containing interactive element (e.g., the icon button it decorates).

**Count display.** The `displayCount` property returns: `""` when hidden;
`String(count)` when `count <= max`; `"${max}+"` when `count > max`.

**Placement.** When the default slot has content, the host element gets
`position: relative` applied (or the host must already establish a stacking
context). The indicator is absolutely positioned at the corner specified by
`placement` plus the `--mj-badge-offset-x/y` values.

**Pulse animation.** A CSS `@keyframes` scales and fades a pseudo-element ring
outward from the indicator. When `prefers-reduced-motion: reduce` is active, the
`pulse` attribute is ignored silently.

**Live announcement.** Badge count changes are not announced automatically, because
numeric ticking is noisy for screen readers. The parent interactive element
(e.g., an icon button) is expected to carry a live `aria-label` such as "Inbox,
3 unread messages". A live-region service utility (§6) may be used for
one-time announcements when the count crosses meaningful thresholds.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| — | No interactive keys; `<mj-badge>` is not focusable |

## 13. Accessibility

- **Role:** the indicator `<span>` carries `role="img"` when a `label` is
  provided and the variant is `dot` or `status`, so screen readers read the
  text alternative. For `count` variant, the indicator is `aria-hidden="true"`
  and the accessible count is expressed via the parent element's `aria-label`.
- **Accessible name:** `label` attribute (or slot override) provides the
  text alternative. For dot/status, `label` is **required** — absence emits a
  console warning.
- **Color:** status states are distinguished by icon/label text in addition to
  color; all indicator colors meet 3:1 contrast against the surrounding surface.
- **Count badges:** the parent interactive element (button, link, avatar) must
  incorporate the count meaning into its own `aria-label`
  (e.g., `aria-label="Notifications, 5 new"`). This component provides a
  `getAriaLabel(template)` helper to assist.
- **Target size:** the badge itself is not interactive; no target size requirement.

## 14. Form participation

N/A — `<mj-badge>` is a display-only component.

## 15. Internationalization & RTL

- The overflow string `"99+"` is a format template overridable via the
  localization hook (`"{max}+"` pattern).
- Status labels ("Online", "Away", etc.) are overridable via the `label`
  attribute or the localization hook.
- In RTL, `top-end` and `top-start` placements swap sides automatically via
  logical CSS `inset-inline-end`/`inset-inline-start`.
- Count numbers use `font-variant-numeric: tabular-nums` to prevent layout
  shift as counts change.

## 16. Progressive enhancement / SSR

Server renders as a `<span>` with the count text and a visually hidden label:
```html
<span class="mj-badge" aria-label="5 unread">5</span>
```
Before JS loads, the badge text is visible and the accessible label is readable.
On upgrade, the custom element adopts the markup, applies positioning, and
enables reactive count updates.

## 17. Dependencies

- **Registry + base element helper** (§6) — lifecycle and attribute reflection.
- **Design-token stylesheet** (§6) — status color tokens, spacing, motion.
- **Live-region/announcement service** (§6) — optional; available to hosts for
  one-time threshold announcements.

## 18. Edge cases & error handling

- **Negative `count`:** clamped to `0`; a console warning is emitted.
- **Non-integer `count`:** rounded to the nearest integer.
- **`variant="dot"` or `"status"` with no `label`:** console warning; renders
  visually but is not accessible.
- **`count` and `status` both set simultaneously:** `variant` takes precedence;
  if `variant="status"`, the `status` attribute drives appearance and `count`
  is ignored.
- **Very large counts (> 9999):** the overflow string renders; the indicator
  grows to fit the text up to `--mj-badge-max-width`, then truncates.
- **Slotted content with no positioning context:** host sets
  `position: relative` on the custom element itself, which acts as the anchor.

## 19. Acceptance criteria

- [ ] Count variant displays the count value and `"<max>+"` when exceeded.
- [ ] `show-zero=false` hides the badge when count is `0`; `show-zero=true` shows it.
- [ ] Dot variant renders a small circle with no text; `label` is required.
- [ ] Status variant renders the correct color token for each status value.
- [ ] `mj-badge-overflow` fires when count exceeds `max`.
- [ ] `placement` positions the indicator at the correct corner in LTR and RTL.
- [ ] `pulse` animation plays when set and is suppressed with `prefers-reduced-motion`.
- [ ] Dot/status indicator carries `role="img"` and `aria-label` from `label`.
- [ ] Count indicator is `aria-hidden`; parent element must carry the count in its label.
- [ ] Missing `label` on dot/status variant emits a console warning.
- [ ] Color token contrast meets 3:1 against typical surface backgrounds.
- [ ] No hard-coded colors; all values resolve from design tokens.
- [ ] Passes automated axe accessibility checks with no violations.

## 20. Open questions

- Should `<mj-badge>` provide a declarative helper attribute (e.g.,
  `aria-target`) that points to a sibling interactive element and automatically
  updates that element's `aria-label` with the count?
- Should the `pulse` animation be tied to `count` changes (auto-pulse on
  increment) rather than a persistent boolean attribute?
- Is an `icon` slot needed inside the count indicator for cases like a small
  verified checkmark?
