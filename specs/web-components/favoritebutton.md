# Favorite Button Spec

- **Tag:** `<mj-favorite-button>`
- **Class / file:** `MjFavoriteButton` / `mjfavoritebutton.js`
- **Category:** Buttons & actions (§5.3)
- **Primary or Variant:** Primary
- **Synonyms covered:** Favorite button, Like button, Bookmark button, Heart button,
  Save button (toggle variant)
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-favorite-button>` is a toggle button for marking content as liked, favorited,
or bookmarked. It builds on the toggle button pattern (`aria-pressed`) and adds
optimistic UI (the visual state updates immediately on activation), an optional
visible count display, and a rollback path for when the persisted operation fails.
It satisfies the Like, Favorite, and Bookmark catalog entries because they all share
this same interaction model — they differ only in icon and label.

## 2. When to use / when not to use

Use for any user-facing action that marks content as favored and whose state should
persist (typically via an API call). This component manages the optimistic update and
rollback; the consumer provides the persistence logic by handling the `mj-change`
event. Do not use for transient, in-session-only toggles — use `<mj-toggle-button>`
instead. Do not use for selection within a multi-select list — use checkboxes or a
selectable listbox. Distinguish from `<mj-toggle-button>` in that this component
explicitly models persistence and count display; `<mj-toggle-button>` is the simpler,
sessionless form.

## 3. Anatomy

- **Host element** — the custom element; handles optimistic state logic.
- **button (part)** — inner `<button>` with `aria-pressed`; the focusable target.
- **icon-off (part)** — icon shown when not favorited (`slot="icon-off"`).
- **icon-on (part)** — icon shown when favorited (`slot="icon-on"`).
- **label (part)** — default slot for visible label text (optional).
- **count (part)** — displays the numeric count when `count` is set.

## 4. Variants & modes

| Mode / flavor   | `flavor` value   | Default icons | Default labels |
|-----------------|------------------|---------------|----------------|
| Favorite        | `favorite`       | Star (outline / filled) | "Favorite" / "Unfavorite" |
| Like            | `like`           | Heart (outline / filled) | "Like" / "Unlike" |
| Bookmark        | `bookmark`       | Bookmark (outline / filled) | "Bookmark" / "Remove bookmark" |

The `flavor` attribute selects the default internal icon and accessible label set.
Consumer-provided `icon-off` / `icon-on` slots and `label-off` / `label-on`
attributes override these defaults entirely.

## 5. Attributes

| Attribute      | Type                                  | Default         | Reflects | Description |
|----------------|---------------------------------------|-----------------|----------|-------------|
| `pressed`      | boolean                               | `false`         | Yes      | Current favorited state; maps to `aria-pressed` |
| `flavor`       | `favorite\|like\|bookmark`            | `favorite`      | Yes      | Selects default icons and accessible labels |
| `count`        | number                                | —               | Yes      | Visible count (e.g. like count); omit to hide count |
| `count-max`    | number                                | `9999`          | Yes      | Maximum before count displays as `{count-max}+` |
| `label-off`    | string                                | (flavor default)| Yes      | Accessible label when `pressed` is false |
| `label-on`     | string                                | (flavor default)| Yes      | Accessible label when `pressed` is true |
| `variant`      | `primary\|secondary\|tertiary`        | `tertiary`      | Yes      | Visual emphasis |
| `size`         | `sm\|md\|lg`                          | `md`            | Yes      | Token-mapped dimensions |
| `disabled`     | boolean                               | `false`         | Yes      | Disables interaction; `aria-disabled="true"` |
| `pending`      | boolean                               | `false`         | Yes      | Indicates an in-flight persistence operation; `aria-busy="true"` |
| `icon-only`    | boolean                               | `false`         | Yes      | Hides text label; `label-off` / `label-on` become `aria-label` |

## 6. Properties

| Property        | Type                                   | Description |
|-----------------|----------------------------------------|-------------|
| `pressed`       | `boolean`                              | Reflects `pressed` attribute; settable programmatically |
| `pending`       | `boolean`                              | Reflects `pending` attribute; consumer sets to indicate async in-flight |
| `count`         | `number \| undefined`                  | Reflects `count` attribute |
| `optimisticPressed` | `boolean` (read-only)             | The visual state after optimistic update, before server confirmation |

## 7. Slots

| Slot         | Description |
|--------------|-------------|
| (default)    | Visible text label (optional; shown alongside count) |
| `icon-off`   | Icon displayed when `pressed` is false |
| `icon-on`    | Icon displayed when `pressed` is true |

## 8. Events

| Event            | `detail`                                                               | Bubbles | Cancelable | Description |
|------------------|------------------------------------------------------------------------|---------|------------|-------------|
| `mj-change`      | `{ pressed: boolean, previousPressed: boolean, originalEvent: Event }` | Yes     | Yes        | Fires before visual state changes; cancel to prevent optimistic update |
| `mj-pressed`     | `{ pressed: boolean }`                                                 | Yes     | No         | Fires after optimistic state changes |
| `mj-rollback`    | `{ pressed: boolean }`                                                 | Yes     | No         | Fires when `rollback()` is called; `pressed` is the restored value |

## 9. CSS parts & custom properties

**Parts**
- `::part(button)` — inner `<button>`
- `::part(icon-off)` — off-state icon wrapper
- `::part(icon-on)` — on-state icon wrapper
- `::part(label)` — label text wrapper
- `::part(count)` — count display

**Custom properties**
| Property | Description |
|---|---|
| `--mj-favorite-button-color-off` | Icon/label color in unfavorited state |
| `--mj-favorite-button-color-on` | Icon/label color in favorited state |
| `--mj-favorite-button-bg-off` | Background in unfavorited state |
| `--mj-favorite-button-bg-on` | Background in favorited state |
| `--mj-favorite-button-border-radius` | Corner radius |
| `--mj-favorite-button-height` | Height (size token) |
| `--mj-favorite-button-count-font-size` | Font size of count display |
| `--mj-favorite-button-focus-ring-color` | Focus ring color |
| `--mj-favorite-button-animation-duration` | Duration of the pop/bounce animation on press |

## 10. States

| State         | Visual effect | ARIA effect |
|---------------|---------------|-------------|
| off (default) | Outline/unfilled icon; off-color tokens | `aria-pressed="false"` |
| on            | Filled icon; on-color tokens; optional scale animation | `aria-pressed="true"` |
| pending       | Spinner overlaying icon; off/on colors unchanged | `aria-busy="true"` |
| hover         | Tinted overlay | — |
| focus-visible | 2 px focus ring | — |
| active        | Pressed tint | — |
| disabled      | Reduced opacity; no pointer events | `aria-disabled="true"` |

## 11. Behavior & interactions

- **Optimistic update**: On activation, `mj-change` fires (cancelable). If not
  cancelled, `optimisticPressed` and the visual state flip immediately (before any
  server call). `mj-pressed` fires with the new optimistic value. The consumer
  should then start the persistence operation and set `pending="true"`.
- **Rollback**: The consumer calls `element.rollback()` if the persistence operation
  fails. This reverts `pressed` and the visual state to the previous value and fires
  `mj-rollback`. The consumer should clear `pending` on both success and failure.
- **Count update**: When `count` changes (via attribute or property), the displayed
  count updates and a live-region polite announcement is made if the change is
  significant (configurable threshold; default: any change).
- **Pending state**: While `pending` is true, additional activations are blocked to
  prevent double-submission. The spinner is shown over the icon.
- **Animation**: On transition to `pressed=true`, a brief scale/pop CSS animation
  plays (like/heart burst). `prefers-reduced-motion` suppresses it.
- The component does not initiate any network requests; persistence is entirely the
  consumer's responsibility via the `mj-change` / `mj-pressed` event flow.

## 12. Keyboard interaction

| Key         | Action |
|-------------|--------|
| `Space`     | Toggles `pressed` state (fires `mj-change`) |
| `Enter`     | Toggles `pressed` state |
| `Tab`       | Moves focus to next focusable element |
| `Shift+Tab` | Moves focus to previous focusable element |

## 13. Accessibility

- The inner `<button>` has `aria-pressed="true"` or `aria-pressed="false"` matching
  the current visual (`optimisticPressed`) state.
- `aria-label` is dynamically set: `label-off` when not pressed, `label-on` when
  pressed. This is always set (even when a visible label exists) to ensure a
  state-aware name is read.
- Count is included in the accessible label when present, e.g. "Like (42)". The
  count part is `aria-live="polite"` so count changes are announced without
  interrupting the user.
- `aria-busy="true"` is set when `pending` is true.
- Icons are `aria-hidden="true"`.
- Minimum target size: 44 × 44 CSS px.
- Contrast: on-state icon color must meet 3:1 against background in both light and
  dark themes.

## 14. Form participation

N/A. `<mj-favorite-button>` is an action button, not a form-associated element. Its
`pressed` state is not submitted in form data.

## 15. Internationalization & RTL

- `label-off` and `label-on` are localizable via the shared localization hook;
  flavor defaults ("Favorite", "Unfavorite", etc.) are English and must be overridden
  for other locales.
- Count formatting (e.g. `1.2K` abbreviations) uses `Intl.NumberFormat` with
  `notation: "compact"` when count exceeds a configurable threshold.
- RTL: icon and label order mirrors via CSS logical properties. Directional icons
  do not apply to favorite/like/bookmark glyphs.

## 16. Progressive enhancement / SSR

Server renders `<mj-favorite-button pressed count="42" label-on="Unfavorite" label-off="Favorite">Favorite</mj-favorite-button>`.
Before upgrade, the element displays as inline text; no interactive behavior. On
upgrade, the inner `<button>`, icon slots, and count are rendered. The server-supplied
`pressed` attribute initializes the correct visual state immediately without a flash.

## 17. Dependencies

- **Registry + base element helper** (§6)
- **Design-token stylesheet** (§6)
- **Live-region service** (§6) — count change and state-change announcements
- **Localization hook** (§6) — `label-off`, `label-on` strings; `Intl.NumberFormat`
  for count formatting

## 18. Edge cases & error handling

- `rollback()` called when no optimistic update is pending: no-op; console info message.
- `rollback()` called multiple times: each call reverts to the state before the most
  recent activation.
- `count` set to a negative number: rendered as `0`.
- `count` set to a non-integer: floored to integer.
- `count` exceeds `count-max`: displayed as `{count-max}+`.
- `pending` set to true without a prior activation (consumer-driven loading state):
  the component shows the spinner but does not alter `pressed`.
- `disabled` + `pending` simultaneously: `disabled` takes precedence; `pending`
  spinner is not shown.
- `mj-change` cancelled: `optimisticPressed` does not change; `mj-pressed` not fired.

## 19. Acceptance criteria

- [ ] Activation fires `mj-change` with correct `pressed` and `previousPressed` values; cancellation prevents update.
- [ ] Optimistic visual state flips immediately on uncancelled activation.
- [ ] `mj-pressed` fires after optimistic state change.
- [ ] `rollback()` restores previous `pressed` state and fires `mj-rollback`.
- [ ] `pending="true"` shows spinner, sets `aria-busy="true"`, blocks additional activations.
- [ ] `count` displays formatted value; overflow above `count-max` shows `{count-max}+`.
- [ ] Count changes trigger polite live-region announcement.
- [ ] `aria-pressed` reflects `optimisticPressed` state.
- [ ] `aria-label` uses `label-on` when pressed, `label-off` when not pressed.
- [ ] `flavor` attribute selects correct default icons and labels.
- [ ] Consumer-provided `icon-off` / `icon-on` slots override flavor defaults.
- [ ] Press animation plays on favoriting; is suppressed under `prefers-reduced-motion`.
- [ ] `disabled` blocks activation and sets `aria-disabled="true"`.
- [ ] Keyboard: Space and Enter toggle pressed state; Tab navigates naturally.
- [ ] Minimum target size 44 × 44 CSS px.
- [ ] axe scan zero violations in pressed, unpressed, and pending states.
- [ ] Light, dark, high-contrast, RTL rendering verified.

## 20. Open questions

- Should `rollback()` be the only rollback mechanism, or should a `rollback` boolean
  attribute also be supported for server-side re-render flows?
- Should count abbreviation (e.g. `42K`) be opt-in via an `abbreviate-count`
  attribute, or always applied above a threshold?
- Confirm whether `flavor` is the right API for selecting icon/label presets versus
  requiring consumers to always provide slots; the `flavor` approach reduces slot
  boilerplate for common use-cases.
- Should a maximum pending-state timeout be built in (e.g. auto-rollback after 10 s)
  or left entirely to the consumer?
