# Tabs Spec

- **Tag:** `<mj-tabs>`
- **Class / file:** `MjTabs` / `mjtabs.js`
- **Category:** Navigation components
- **Primary or Variant:** Primary
- **Synonyms covered:** Tabs, Tab list, Tab panel, Tab group, Pills (pill-styled variant)
- **Phase:** P0
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-tabs>` is a composite component implementing the WAI-ARIA `tablist`/`tab`/
`tabpanel` pattern. It organizes content into mutually exclusive views, with a
strip of tab controls that show one panel at a time. It covers the Pills visual
variant via the `variant` attribute and supports both automatic (follows focus)
and manual (requires Enter/Space) panel activation.

## 2. When to use / when not to use
**Use** when content can be logically divided into distinct sections where only
one is relevant at a time. **Do not use** for navigation between different URLs —
use `<mj-app-bar>` or `<mj-side-nav>` instead. **Do not use** when all sections
need to be visible simultaneously — use `<mj-accordion>`. **Do not use** when the
sections are steps in a process — use `<mj-nav-stepper>`.

## 3. Anatomy
- **Host element** — the outer wrapper; not a landmark.
- **Tab list** (`::part(tablist)`) — `<div role="tablist" aria-label>` containing all tab buttons.
- **Tab** (`::part(tab)`) — each `<button role="tab">` control; one per panel.
- **Tab indicator** (`::part(indicator)`) — animated underline/pill indicator tracking the active tab.
- **Overflow controls** (`::part(scroll-prev)` / `::part(scroll-next)`) — arrow buttons when the tab list overflows its container.
- **Panel** (`::part(panel)`) — each `<div role="tabpanel">` content region.

## 4. Variants & modes
| Variant | `variant` value | Behavior |
|---------|----------------|----------|
| Default (underline) | `underline` | Active tab has an animated underline indicator |
| Pills | `pills` | Tabs styled as filled pill/chip buttons |
| Enclosed | `enclosed` | Tabs sit on a bordered box; active tab is visually connected to the panel |
| Vertical | `orientation="vertical"` | Tab list on the left; panels to the right |

| Activation | `activation` value | Behavior |
|-----------|-------------------|----------|
| Automatic | `automatic` | Focus moves to a tab and immediately activates its panel |
| Manual | `manual` | Arrow keys move focus; Enter/Space activates the focused tab |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `selected` | string | `""` | Yes | `id` of the currently active tab; reflects two-way |
| `variant` | string | `"underline"` | Yes | Visual style: `underline` \| `pills` \| `enclosed` |
| `orientation` | string | `"horizontal"` | Yes | Layout: `horizontal` \| `vertical` |
| `activation` | string | `"automatic"` | Yes | Panel activation model: `automatic` \| `manual` |
| `tablist-label` | string | `""` | Yes | `aria-label` for the `tablist`; required when no visible heading labels the group |
| `scrollable` | boolean | `false` | Yes | Enables overflow scrolling with arrow controls when tab list overflows |
| `lazy` | boolean | `true` | Yes | Defers rendering of non-selected panel content until first selection |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `selectedTab` | `Element \| null` | Reference to the currently selected `<mj-tab>` element |
| `selectedPanel` | `Element \| null` | Reference to the currently visible `<mj-tab-panel>` element |
| `tabs` | `Element[]` | Ordered array of all `<mj-tab>` elements |

## 7. Slots
| Slot | Description |
|------|-------------|
| `tab` | `<mj-tab>` elements; render as the tab buttons in the tablist |
| _(default)_ | `<mj-tab-panel>` elements; each panel's content |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-tabs-change` | `{ selectedId: string, previousId: string, selectedTab: Element, selectedPanel: Element }` | Yes | Yes | Fires before a new tab is activated; cancel to prevent the change |
| `mj-tabs-changed` | `{ selectedId: string, previousId: string }` | Yes | No | Fires after the panel transition completes |

## 9. CSS parts & custom properties
**Parts**
- `::part(tablist)` — the `<div role="tablist">` strip
- `::part(tab)` — individual tab `<button>` elements (use `:state()` / attribute selectors for selected/disabled)
- `::part(indicator)` — the active-tab underline/fill indicator
- `::part(scroll-prev)` / `::part(scroll-next)` — overflow scroll arrow buttons
- `::part(panels)` — wrapper around all panel elements
- `::part(panel)` — individual `<div role="tabpanel">`

**Custom properties**
| Property | Default | Description |
|----------|---------|-------------|
| `--mj-tabs-indicator-color` | `var(--mj-color-primary)` | Active indicator color |
| `--mj-tabs-indicator-height` | `2px` | Underline indicator thickness |
| `--mj-tabs-tab-gap` | `var(--mj-spacing-1)` | Gap between tab buttons |
| `--mj-tabs-tab-padding` | `var(--mj-spacing-2) var(--mj-spacing-4)` | Padding inside each tab |
| `--mj-tabs-font-weight-selected` | `600` | Font weight of selected tab |
| `--mj-tabs-panel-padding` | `var(--mj-spacing-5)` | Padding inside each panel |
| `--mj-tabs-transition-duration` | `var(--mj-motion-duration-short)` | Indicator animation duration |

## 10. States
- **default** — first tab selected; others deselected.
- **selected** — the active tab has `aria-selected="true"`; tabindex `0`; panel visible.
- **deselected** — inactive tabs have `aria-selected="false"`; tabindex `-1`; panels hidden (`hidden` attribute or `display: none`).
- **focused** — currently keyboard-focused tab shows focus-visible ring.
- **disabled** — tab has `aria-disabled="true"`; skipped in arrow-key navigation.
- **hover** — tab shows hover background token.
- **loading** — a tab panel can be in loading state while async content resolves; spinner shown within the panel.

## 11. Behavior & interactions
- Tabs implement the WAI-ARIA `tablist`/`tab`/`tabpanel` pattern with roving
  `tabindex`: the selected tab has `tabindex="0"`, all others have `tabindex="-1"`.
- In `automatic` activation, focus moves and the panel changes in one step.
- In `manual` activation, arrow keys move focus among tabs (updating
  `tabindex`); Enter or Space activates the focused tab.
- Disabled tabs are skipped in arrow-key navigation; they cannot be activated.
- Panel content is rendered lazily when `lazy` is true: the HTML inside
  `<mj-tab-panel>` is not rendered into the DOM until that panel is first
  activated. Once rendered, it stays in the DOM (just hidden).
- When `scrollable` is true and the tab list overflows, prev/next arrow buttons
  appear; they scroll the strip and are hidden/disabled at the respective edges.
- The active-tab indicator animates to the new tab position using a CSS
  transform transition; reduced motion shortens the duration to `0ms`.
- `<mj-tab>` and `<mj-tab-panel>` are linked by matching `id`/`aria-controls`
  and `aria-labelledby` attributes, which the composite sets automatically based
  on slot order or explicit `panel` attribute on `<mj-tab>`.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` | Moves focus into the tablist (lands on selected tab) or out to panel content |
| `Arrow Right` / `Arrow Down` | Moves focus to next tab (wraps); activates it if `activation="automatic"` |
| `Arrow Left` / `Arrow Up` | Moves focus to previous tab (wraps); activates if `activation="automatic"` |
| `Home` | Moves focus to first enabled tab; activates if automatic |
| `End` | Moves focus to last enabled tab; activates if automatic |
| `Enter` / `Space` | Activates the focused tab (required in `manual` activation) |
| `Delete` | Removes a removable tab (when tab has `removable` attribute); focus moves to nearest enabled tab |

## 13. Accessibility
- `role="tablist"` on the tab strip; `aria-label` from `tablist-label` attribute.
- Each tab: `role="tab"`, `aria-selected`, `aria-controls="{panelId}"`,
  `aria-disabled` when disabled.
- Each panel: `role="tabpanel"`, `aria-labelledby="{tabId}"`, `tabindex="0"` so
  it is reachable by Tab.
- Hidden panels use the `hidden` attribute (not just CSS `display: none`) to
  ensure they are absent from the accessibility tree.
- The indicator is `aria-hidden="true"`.
- Overflow scroll arrows have accessible names: `mj.tabs.scrollPrev` /
  `mj.tabs.scrollNext`.
- `prefers-reduced-motion`: indicator transition duration is `0ms`; no
  cross-fade animation on panels.

## 14. Form participation
N/A — `<mj-tabs>` is a navigation/content-organization component.

## 15. Internationalization & RTL
- `tablist-label` is localizable; default is `""` (authors must provide a value).
- Overflow button labels: `mj.tabs.scrollPrev` / `mj.tabs.scrollNext`.
- In RTL, `Arrow Right` and `Arrow Left` semantics are flipped so right moves
  to the previous tab and left moves to the next (matches RTL reading direction).
- In RTL with `orientation="horizontal"`, the tab list layout reverses; the
  indicator moves accordingly.
- In `orientation="vertical"` RTL, the tab list moves to the inline-end (right).

## 16. Progressive enhancement / SSR
- Server renders:
  ```html
  <mj-tabs selected="tab1">
    <mj-tab slot="tab" id="tab1" panel="panel1">Overview</mj-tab>
    <mj-tab slot="tab" id="tab2" panel="panel2">Details</mj-tab>
    <mj-tab-panel id="panel1">…</mj-tab-panel>
    <mj-tab-panel id="panel2" hidden>…</mj-tab-panel>
  </mj-tabs>
  ```
- Before upgrade: panels with `hidden` are absent; the selected panel's content
  is visible; links/headings within panels are accessible.
- On upgrade: ARIA roles, `tabindex`, and keyboard navigation are added;
  animated indicator is inserted.

## 17. Dependencies
- Section 6: Registry + base element helper, design-token stylesheet,
  localization hook.
- `<mj-tab>` — companion element for individual tab buttons.
- `<mj-tab-panel>` — companion element for panel content areas.

## 18. Edge cases & error handling
- **No tabs slotted**: empty tablist renders; console warning emitted.
- **`selected` references unknown id**: first enabled tab is selected as fallback.
- **All tabs disabled**: no tab can be activated; a console error is logged.
- **Single tab**: tablist renders with one tab; panel always visible; arrow keys
  have no effect.
- **Tab added/removed dynamically**: `MutationObserver` on the `tab` slot
  re-associates controls and panels; if the removed tab was selected, focus
  moves to the nearest enabled tab.
- **Panel content taller than viewport**: panels are naturally scrollable; no
  fixed height is imposed.

## 19. Acceptance criteria
- [ ] Renders `role="tablist"` with `role="tab"` and `role="tabpanel"` children correctly.
- [ ] `aria-selected`, `aria-controls`, `aria-labelledby`, `tabindex` set correctly.
- [ ] Selected panel visible; others have `hidden` attribute.
- [ ] `automatic` mode: arrow key focus change activates panel immediately.
- [ ] `manual` mode: arrow key moves focus only; Enter/Space activates.
- [ ] `lazy`: non-selected panel content not in DOM until first activation.
- [ ] `scrollable`: overflow arrows appear; disabled at edges.
- [ ] `mj-tabs-change` fires and is cancelable; canceling prevents tab switch.
- [ ] Indicator animates to new tab; animation disabled under `prefers-reduced-motion`.
- [ ] Disabled tabs skipped in keyboard navigation.
- [ ] RTL: arrow key semantics and layout correct.
- [ ] SSR: selected panel visible; others hidden before script loads.
- [ ] Automated axe checks pass with zero violations.

## 20. Open questions
- Should `variant="pills"` be part of this component or a separate
  `<mj-pills>` element (given that pills are also used as filter chips)?
- Should removable tabs (with delete affordance) be a separate attribute on
  `<mj-tab>` or a mode on `<mj-tabs>`?
