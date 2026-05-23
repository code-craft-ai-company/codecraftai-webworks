# Segmented Control Spec

- **Tag:** `<mj-segmented-control>`
- **Class / file:** `MjSegmentedControl` / `mjsegmentedcontrol.js`
- **Category:** Selection & dropdown-style controls
- **Primary or Variant:** Primary
- **Synonyms covered:** Toggle group, Button group
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-segmented-control>` renders a compact, connected row of segments that act as either a mutually exclusive selector (radio semantics) or a set of independent toggles (checkbox semantics), or a group of action buttons (no persistent state). It is the primary implementation behind "Toggle group" and "Button group" synonyms, distinguished by its `mode` attribute.

## 2. When to use / when not to use
**Use `mode="select"`** for view-mode switches (Grid / List / Map), alignment selectors, or any mutually exclusive inline choice where a full-width `<mj-radio-group>` would be disproportionate. **Use `mode="toggle"`** for multi-select filters or independently toggled options within a toolbar. **Use `mode="action"`** for a grouped set of related action buttons (Bold, Italic, Underline). **Do not use** for navigation — prefer `<mj-tabs>`. **Do not use** when the choices have natural descriptions or icons that need vertical layout — prefer `<mj-radio-group>`. **Do not use** for more than ~6 segments; beyond that the layout breaks at narrow widths.

## 3. Anatomy
- **Container** (`part="container"`) — flex row of segments; `role="radiogroup"`, `role="group"`, or `toolbar` depending on `mode`.
- **Segment** (`part="segment"`) — individual button element.
- **Segment icon** (`part="segment-icon"`) — optional leading icon.
- **Segment label** (`part="segment-label"`) — text label.
- **Segment badge** (`part="segment-badge"`) — optional count badge.
- **Indicator** (`part="indicator"`) — animated sliding background that tracks the selected segment (select mode only).

## 4. Variants & modes
| Variant / mode | `mode` value | Semantics | ARIA role |
|----------------|-------------|-----------|-----------|
| Single-select (default) | `"select"` | Mutually exclusive; one segment active | `radiogroup` on container; `radio` on segments; roving tabindex |
| Multi-toggle | `"toggle"` | Independent on/off per segment | `group` on container; each segment is `button` with `aria-pressed` |
| Action group | `"action"` | No persistent state; each is a simple action | `toolbar` on container; each is `button` |
| Icon-only | `icon-only` attribute on segments | Label hidden; icon only | `aria-label` required on each segment |
| Full-width | `stretch` (boolean) | Segments share equal width filling parent | — |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `mode` | `"select"` \| `"toggle"` \| `"action"` | `"select"` | Yes | Interaction and semantics mode |
| `name` | string | `""` | Yes | Form field name (select/toggle modes) |
| `value` | string | `""` | Yes | Selected segment value (select mode); comma-separated in toggle mode |
| `disabled` | boolean | `false` | Yes | Disables all segments |
| `required` | boolean | `false` | Yes | A selection is required (select mode) |
| `stretch` | boolean | `false` | Yes | Segments stretch to fill available width equally |
| `size` | `"sm"` \| `"md"` \| `"lg"` | `"md"` | Yes | Visual size variant |
| `label` | string | `""` | Yes | Accessible label for the group |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `segments` | `MjSegment[]` | Live array of child `<mj-segment>` elements |
| `selectedSegment` | `MjSegment \| null` | Currently selected segment (select mode) |
| `selectedSegments` | `MjSegment[]` | Currently active segments (toggle mode) |
| `validity` | `ValidityState` | Delegated from `ElementInternals` (select/toggle modes) |
| `validationMessage` | `string` | Localizable invalid message |

## 7. Slots
| Slot | Description |
|------|-------------|
| (default) | `<mj-segment>` elements |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-change` | `{ value: string, values: string[], segment: MjSegment, selected: boolean }` | Yes | No | Fired when selection or toggle state changes |
| `mj-action` | `{ segment: MjSegment }` | Yes | No | Fired when an action-mode segment is activated |

## 9. CSS parts & custom properties
**Parts:** `container`, `segment`, `segment-icon`, `segment-label`, `segment-badge`, `indicator`

**Custom properties:**
| Property | Default token | Description |
|----------|---------------|-------------|
| `--mj-segmented-height` | `--mj-size-control-md` | Height of the control |
| `--mj-segmented-bg` | `--mj-color-surface-subtle` | Background of the unselected track |
| `--mj-segmented-selected-bg` | `--mj-color-surface` | Background of the selected segment |
| `--mj-segmented-border-radius` | `--mj-radius-md` | Outer container radius |
| `--mj-segmented-segment-radius` | `--mj-radius-sm` | Per-segment indicator radius |
| `--mj-segmented-gap` | `2px` | Gap between segments |
| `--mj-segmented-indicator-transition` | `150ms ease` | Sliding indicator animation duration |

## 10. States
| State | Visual effect | ARIA effect |
|-------|--------------|-------------|
| Unselected segment | No indicator fill | `aria-checked="false"` (select) / `aria-pressed="false"` (toggle) |
| Selected segment | Indicator slides under segment; label bold | `aria-checked="true"` (select) / `aria-pressed="true"` (toggle) |
| Focused segment | Focus ring around segment | Roving tabindex (select); normal focus (toggle/action) |
| Hover segment | Subtle hover tint | — |
| Disabled segment | Muted; no pointer events | `aria-disabled="true"` |
| Disabled group | All segments muted | `aria-disabled="true"` on container |

## 11. Behavior & interactions
- **Select mode**: clicking a segment selects it and deselects the previous; roving tabindex applies (single tab stop).
- **Toggle mode**: clicking a segment toggles it independently; all segments are separate tab stops.
- **Action mode**: clicking a segment fires `mj-action`; no persistent selection state; all segments are tab stops.
- The sliding indicator is animated via a CSS transition on `transform`; the animation is skipped when `prefers-reduced-motion: reduce`.
- `disabled` on the group disables all segments; `disabled` on an individual `<mj-segment>` disables only that segment.

## 12. Keyboard interaction
| Key | Mode | Action |
|-----|------|--------|
| `Tab` | All | Enter / leave the group; in select mode one tab stop |
| `ArrowRight` / `ArrowDown` | Select | Move focus and selection to next segment |
| `ArrowLeft` / `ArrowUp` | Select | Move focus and selection to previous segment |
| `Home` | Select | Move focus and selection to first segment |
| `End` | Select | Move focus and selection to last segment |
| `Space` / `Enter` | Toggle, Action | Activate the focused segment |
| `Tab` | Toggle, Action | Move between individual segments |

## 13. Accessibility
- **Select mode**: container `role="radiogroup"` + `aria-label`/`aria-labelledby`; each segment `role="radio"` + `aria-checked`; roving tabindex.
- **Toggle mode**: container `role="group"` + `aria-label`; each segment `role="button"` + `aria-pressed`.
- **Action mode**: container `role="toolbar"` + `aria-label`; each segment `role="button"`.
- Icon-only segments must have `aria-label` on the segment element.
- Disabled segments: `aria-disabled="true"`; in select mode, skipped by roving tabindex; in toggle/action mode, removed from tab sequence.
- Badge counts are announced inline as part of the segment's accessible name (e.g., "Grid view, 3 items").

## 14. Form participation
- **Select mode**: form-associated via `ElementInternals`; contributes `name=value`.
- **Toggle mode**: contributes one `name=value` per active segment in `FormData`.
- **Action mode**: not form-associated; `name` and `value` attributes are ignored.
- On form reset (select/toggle modes): reverts to initial `value` attribute.
- `required` (select mode): `validity.valueMissing` when no segment is selected.

## 15. Internationalization & RTL
- In RTL, segments are visually reversed (flex `row-reverse`); the selected indicator tracks the RTL-reversed position.
- Data order in `value`/`values` and `FormData` follows DOM order, independent of visual order.
- All segment labels are author-supplied; no built-in English strings.
- Sliding indicator animation direction inverts in RTL.

## 16. Progressive enhancement / SSR
- Server renders `<button>` elements or `<input type="radio">` / `<input type="checkbox">` elements inside `<mj-segmented-control>`.
- Before upgrade, the native controls are operable.
- On upgrade, native elements are hidden; the component builds the visual layer; for form-associated modes, hidden inputs mirror the state.
- Without scripting: radio/checkbox inputs render and function; button group renders as plain buttons.

## 17. Dependencies
- Section 6: Registry/base element, design tokens, focus utilities (roving tabindex), form-association helper.
- `<mj-segment>` — individual segment primitive (companion element).

## 18. Edge cases & error handling
- Single segment: valid; functions as a standalone toggle (toggle mode) or an always-selected radio (select mode).
- All segments disabled: select mode still has one tab stop; required validation fails.
- `value` not matching any child in select mode: no segment is selected; validation fails if `required`.
- Segments added/removed dynamically in select mode: roving tabindex recalculates.
- Overflow at narrow widths: segments wrap if `stretch` is false; if `stretch` is true, text truncates with ellipsis and a tooltip.
- `prefers-reduced-motion`: sliding indicator snaps without animation.

## 19. Acceptance criteria
- [ ] Select mode: clicking a segment selects it; previous selection is cleared; `mj-change` fires.
- [ ] Toggle mode: clicking a segment toggles it independently; `mj-change` fires per toggle.
- [ ] Action mode: clicking a segment fires `mj-action`; no visual selection state persists.
- [ ] Arrow keys navigate and select in select mode; `Tab` is the only key in toggle/action mode.
- [ ] `role="radiogroup"` / `"group"` / `"toolbar"` correct per mode.
- [ ] Sliding indicator animates to correct segment; snaps with `prefers-reduced-motion`.
- [ ] Form submission includes correct `name=value`; form reset restores initial value.
- [ ] axe-core reports zero violations in select, toggle, and action modes.
- [ ] RTL layout reverses segments; indicator tracks the correct segment.

## 20. Open questions
- Should `mode="select"` allow deselecting the active segment (making the value empty), or enforce always-one-selected?
- Is a vertical orientation variant (`orientation="vertical"`) needed for toolbar-style toolbars?
- Should the component automatically convert to an overflow menu when there is insufficient horizontal space?
