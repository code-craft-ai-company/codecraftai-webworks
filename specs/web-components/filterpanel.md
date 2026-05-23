# Filter Panel Spec

- **Tag:** `<mj-filter-panel>`
- **Class / file:** `FilterPanel` / `filterpanel.js`
- **Category:** Application & productivity components
- **Primary or Variant:** Primary
- **Synonyms covered:** Faceted filter, Sort control, Applied filter chips
- **Phase:** P2
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-filter-panel>` provides a structured sidebar or inline panel for faceted filtering and sorting of a data set. It renders one or more filter groups (each a collapsible section with checkboxes, radios, range sliders, or date inputs), a sort control, an applied-filter chips strip, and a clear-all action. The component emits a unified filter-change event so the host can re-query the data source without managing individual control states.

## 2. When to use / when not to use
Use alongside `<mj-search-results>`, `<mj-data-table>`, or any filterable list to give users control over facets. Do not use for a single filter control — use the appropriate individual control (`<mj-checkbox-group>`, `<mj-select>`) directly. For compound programmatic queries with nested AND/OR logic, use `<mj-query-builder>` instead.

## 3. Anatomy
- **panel root** — `<aside aria-label="Filters">` or `<div>` if inline.
- **applied chips bar** — horizontal scrollable strip of removable `<mj-chip>` tokens, one per active filter value; "Clear all" button at the end.
- **sort control** — `<mj-select>` for sort field and a toggle button for sort direction.
- **filter groups** — `<mj-accordion>` sections; each group has a label and a count badge showing selected items.
- **facet content** — inside each accordion section: `<mj-checkbox-group>`, `<mj-radio-group>`, `<mj-slider>`, or `<mj-date-picker>` depending on `type`.
- **show-more link** — within a facet list; expands from a capped list to the full set.
- **result count** — optional "N results" text updated in response to `total-count` property.

## 4. Variants & modes
| Variant / mode | Attribute | Behavior difference |
|----------------|-----------|---------------------|
| Sidebar | `layout="sidebar"` (default) | Vertical stacked accordion groups |
| Inline / horizontal | `layout="inline"` | Groups rendered as horizontal pills/dropdowns |
| Collapsible panel | `collapsible` | The entire filter panel has a hide/show toggle |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `layout` | `"sidebar"\|"inline"` | `"sidebar"` | Yes | Visual layout of filter groups |
| `collapsible` | boolean | `false` | Yes | Adds a toggle to collapse the entire panel |
| `open` | boolean | `true` | Yes | (collapsible) Whether the panel is currently expanded |
| `label` | string | `"Filters"` | Yes | Accessible name for the panel landmark |
| `total-count` | number | — | Yes | Result count to display; updates live region |
| `sort-label` | string | `"Sort by"` | Yes | Label for the sort select |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `filterConfig` | `FilterGroupConfig[]` | Array defining groups: `{ id, label, type, options?, min?, max?, step? }` |
| `value` | `FilterState` | Current filter state: `{ sort: { field, direction }, filters: Record<groupId, any> }` |
| `appliedFilters` | `AppliedFilter[]` | Read-only derived list of active filter chips: `{ groupId, label, value }` |

## 7. Slots
| Slot | Description |
|------|-------------|
| `header` | Content above the applied chips bar (e.g., a title or search input) |
| `footer` | Content below all filter groups (e.g., an apply button in non-live mode) |
| `group-{id}` | Custom content to replace a generated filter group's body |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-filter-change` | `{ value: FilterState, changedGroup: string \| "sort" \| "clear" }` | Yes | No | Fires whenever any filter or sort value changes |
| `mj-filter-clear` | `{}` | Yes | No | Fires when "Clear all" is activated |
| `mj-chip-remove` | `{ groupId: string, value: any }` | Yes | No | Fires when a single applied chip is removed |
| `mj-panel-toggle` | `{ open: boolean }` | Yes | No | Fires when the collapsible panel opens or closes |

## 9. CSS parts & custom properties
**Parts:** `root`, `chips-bar`, `clear-all`, `sort-control`, `group`, `group-header`, `group-body`, `show-more`, `result-count`.

| Custom property | Default | Description |
|-----------------|---------|-------------|
| `--mj-filter-panel-width` | `280px` | Width in sidebar layout |
| `--mj-filter-group-gap` | `var(--mj-space-2)` | Gap between accordion groups |
| `--mj-filter-chips-gap` | `var(--mj-space-1)` | Gap between applied filter chips |
| `--mj-filter-count-badge-bg` | `var(--mj-color-accent-subtle)` | Background for group selected-count badge |

## 10. States
- **default** — panel open, no filters applied, sort at default.
- **filters-applied** — chips bar visible with one or more chips; "Clear all" enabled.
- **group-expanded** — accordion section open; facet controls visible.
- **group-collapsed** — accordion section closed; selected count badge visible if any values selected in that group.
- **panel-collapsed** — `collapsible` + `open=false`; panel hidden; toggle button visible.
- **loading** — `<mj-skeleton-loader>` inside groups while options load asynchronously.
- **disabled** — all controls disabled; visually dimmed.

## 11. Behavior & interactions
Filter changes are applied immediately (live mode) by default. Each control change updates the `value` property and emits `mj-filter-change`. Applied filter chips are derived from `value`; removing a chip removes the corresponding value from the relevant group. "Clear all" resets `value` to its default state and emits `mj-filter-clear`. The sort control emits a change that updates `value.sort`; `mj-filter-change` fires with `changedGroup="sort"`. Async option loading is supported per group: if `options` is a Promise, a skeleton is shown until resolution. "Show more" in a facet list expands from a `cap` (default 5) to all options, with a collapse link.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` / `Shift+Tab` | Navigate through all controls in the panel |
| `Enter` / `Space` | Activate a checkbox, radio, or accordion header |
| `ArrowUp` / `ArrowDown` | Navigate options within a radio group |
| `Delete` / `Backspace` on chip | Remove the focused applied filter chip |
| `Escape` | Collapse open sort select dropdown |

## 13. Accessibility
The panel root is `<aside aria-label="Filters">` in sidebar layout. The applied chips bar has `aria-label="Applied filters"`. Each chip has a labelled remove button (e.g., `aria-label="Remove Category: Books"`). The sort select uses standard `<mj-select>` accessibility. Accordion groups delegate to `<mj-accordion>` which manages `aria-expanded` / `aria-controls`. Result count updates are announced via a polite live region: "Showing N results". Group selected-count badges are `aria-label="N selected"` on the accordion trigger. All facet controls (checkbox group, radio group, slider) are their own accessible primitives.

## 14. Form participation
N/A — the filter panel drives a data query, not a form submission. Individual controls inside may be form-associated, but the panel as a whole is not.

## 15. Internationalization & RTL
All user-facing strings (`label`, `sort-label`, "Clear all", "Show more", "Show less", "N results") are overridable via attributes or the localization hook. Counts are formatted with `Intl.NumberFormat`. In RTL, the chips bar scroll direction and sort direction icon flip appropriately using logical CSS.

## 16. Progressive enhancement / SSR
Server renders filter groups as `<details>/<summary>` elements with native checkboxes/radios. Without JS, selecting options and submitting a surrounding `<form>` applies filters via URL parameters. On upgrade, the component replaces `<details>` with `<mj-accordion>`, enhances controls with `<mj-checkbox-group>` etc., and switches to live filter-change events instead of form submission.

## 17. Dependencies
- **Foundations:** Registry + base element helper, Design-token stylesheet, Live-region/announcement service, Localization/formatting hook.
- **Components:** `<mj-accordion>`, `<mj-checkbox-group>`, `<mj-radio-group>`, `<mj-slider>`, `<mj-date-picker>`, `<mj-select>`, `<mj-chip>`, `<mj-button>`, `<mj-skeleton-loader>`, `<mj-badge>`.

## 18. Edge cases & error handling
- Empty `filterConfig`: panel renders only the sort control and result count.
- Group with zero matching options: group header shown but body shows "No options available".
- All options selected in a group: "Clear group" link appears inside the group body.
- `total-count` drops to 0 while filters applied: empty-state message shown; chips remain visible for removal.
- Conflicting `layout="inline"` with many groups: groups wrap into rows; not hidden.
- Async option load failure: error message shown inside the group with a retry button.

## 19. Acceptance criteria
- [ ] `mj-filter-change` fires with complete `FilterState` on every filter change.
- [ ] Applied chips bar renders one chip per active filter value; removing a chip updates `value`.
- [ ] "Clear all" resets all groups and emits `mj-filter-clear`.
- [ ] Accordion groups show selected-count badge when collapsed and filters are active.
- [ ] Result count live region announces on `total-count` change.
- [ ] Keyboard: all controls reachable and operable.
- [ ] RTL: chips bar and sort direction flip correctly.
- [ ] Axe scan reports zero violations.
- [ ] Light, dark, high-contrast, and RTL rendering verified.

## 20. Open questions
- Should an explicit "Apply" mode (non-live) be supported via a `live` boolean attribute?
- Should the component own URL-param serialization of `FilterState`, or leave that to the consumer?
