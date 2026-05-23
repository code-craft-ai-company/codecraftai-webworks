# Asset Picker Spec

- **Tag:** `<mj-asset-picker>`
- **Class / file:** `MjAssetPicker` / `mjassetpicker.js`
- **Category:** Selection & dropdown-style controls
- **Primary or Variant:** Primary
- **Synonyms covered:** Emoji picker, Icon picker, Font picker
- **Phase:** P2
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-asset-picker>` is a searchable, categorized, virtualized grid picker for discrete visual assets: emoji, icons, fonts, or any author-supplied set of named visual items. The same component covers all three synonym variants through the `type` attribute and a pluggable asset data source. It supports recent/favorites tracking, category navigation, and keyboard-navigable grid selection.

## 2. When to use / when not to use
**Use** for emoji selection in a chat or comment composer. **Use** for icon selection in a design tool or CMS. **Use** for font selection in a typography control. **Do not use** when the asset set is fewer than ~20 items — use `<mj-select>` or `<mj-listbox>`. **Do not use** for file/image uploads — use `<mj-file-picker>`. **Do not use** for locale data selection — use `<mj-locale-picker>`.

## 3. Anatomy
- **Trigger** (`part="trigger"`) — button showing the selected asset (or a placeholder).
- **Popup** (`part="popup"`) — positioned overlay containing the full picker panel.
- **Search input** (`part="search"`) — text field for filtering assets by name/keyword.
- **Category nav** (`part="category-nav"`) — vertical or horizontal category tab strip.
- **Category button** (`part="category-button"`) — individual category selector.
- **Asset grid** (`part="asset-grid"`) — virtualized `role="grid"` of asset cells.
- **Asset cell** (`part="asset-cell"`) — `role="gridcell"` containing a single asset button.
- **Asset image** (`part="asset-image"`) — the visual: emoji glyph, icon SVG, or font preview.
- **Asset label** (`part="asset-label"`) — accessible name tooltip below or beside the asset.
- **Recents section** (`part="recents"`) — most recently selected assets.
- **Favorites section** (`part="favorites"`) — user-starred assets.
- **No-results** (`part="no-results"`) — empty state when search yields nothing.
- **Skin-tone picker** (`part="skin-tone"`) — emoji-specific tone modifier selector.

## 4. Variants & modes
| Variant / mode | `type` value | Data source behavior |
|----------------|-------------|---------------------|
| Emoji | `"emoji"` | Built-in Unicode emoji dataset or author-supplied |
| Icon | `"icon"` | Author-supplied SVG icon set via `dataSource` |
| Font | `"font"` | Author-supplied font list; preview renders sample text |
| Custom | `"custom"` | Fully author-supplied asset dataset |
| Inline | `inline` (boolean) | Grid rendered inline; no popup trigger |
| Multi-select | `multiple` (boolean) | Multiple assets can be selected simultaneously |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `name` | string | `""` | Yes | Form field name |
| `value` | string | `""` | Yes | Selected asset identifier (comma-separated in multi mode) |
| `type` | `"emoji"` \| `"icon"` \| `"font"` \| `"custom"` | `"emoji"` | Yes | Asset type; affects data source and rendering |
| `multiple` | boolean | `false` | Yes | Allow multiple asset selection |
| `disabled` | boolean | `false` | Yes | Disables the picker |
| `required` | boolean | `false` | Yes | A selection is required |
| `open` | boolean | `false` | Yes | Opens/closes the popup |
| `inline` | boolean | `false` | Yes | Renders picker inline |
| `search-placeholder` | string | `"Search"` | Yes | Placeholder text in the search field |
| `show-recents` | boolean | `true` | Yes | Show recent selections section |
| `recents-count` | number | `18` | Yes | Maximum items in the recents section |
| `show-skin-tone` | boolean | `false` | Yes | Show skin tone selector (emoji type only) |
| `columns` | number | `8` | Yes | Number of columns in the asset grid |
| `cell-size` | string | `"2rem"` | Yes | Size of each asset cell; forwarded as CSS |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `dataSource` | `AssetDataSource \| null` | Programmatic asset provider (`{ categories, search(query), getAsset(id) }`) |
| `selectedAssets` | `AssetItem[]` | Array of currently selected asset objects |
| `recentAssets` | `AssetItem[]` | Recently selected assets (backed by `localStorage`) |
| `skinTone` | `0 \| 1 \| 2 \| 3 \| 4 \| 5` | Current emoji skin tone modifier (0 = default) |
| `validity` | `ValidityState` | Delegated from `ElementInternals` |
| `validationMessage` | `string` | Localizable invalid message |

## 7. Slots
| Slot | Description |
|------|-------------|
| `trigger` | Custom trigger element |
| `no-results` | Custom empty search state content |
| `loading` | Custom loading indicator while data source initializes |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-change` | `{ value: string, asset: AssetItem \| null, assets: AssetItem[] }` | Yes | No | Fired when selection changes |
| `mj-search` | `{ query: string, results: AssetItem[] }` | Yes | No | Fired after each search |
| `mj-open` | `{}` | Yes | Yes | Fired before popup opens |
| `mj-close` | `{}` | Yes | No | Fired after popup closes |
| `mj-skin-tone-change` | `{ skinTone: number }` | Yes | No | Fired when skin tone changes (emoji mode) |

## 9. CSS parts & custom properties
**Parts:** `trigger`, `popup`, `search`, `category-nav`, `category-button`, `asset-grid`, `asset-cell`, `asset-image`, `asset-label`, `recents`, `favorites`, `no-results`, `skin-tone`

**Custom properties:**
| Property | Default token | Description |
|----------|---------------|-------------|
| `--mj-asset-picker-popup-width` | `20rem` | Width of the picker popup |
| `--mj-asset-picker-popup-height` | `24rem` | Height of the picker popup |
| `--mj-asset-picker-cell-size` | `2rem` | Width and height of each asset cell |
| `--mj-asset-picker-cell-radius` | `--mj-radius-sm` | Corner radius of cells |
| `--mj-asset-picker-font-size` | `1.25rem` | Font size for emoji/icon display |
| `--mj-asset-picker-selected-bg` | `--mj-color-selected-subtle` | Background of selected cell |
| `--mj-asset-picker-category-width` | `3rem` | Width of the category sidebar |

## 10. States
| State | Visual effect | ARIA effect |
|-------|--------------|-------------|
| Default (closed) | Trigger shows selected asset or placeholder | — |
| Open | Popup visible; search focused | `aria-expanded="true"` on trigger |
| Searching | Grid filters in real time | Live region: "N results for [query]" |
| No results | No-results slot visible | — |
| Asset focused | Cell focus ring | Roving tabindex; `aria-activedescendant` |
| Asset selected | Selected background; checkmark badge | `aria-selected="true"` on cell |
| Loading | Spinner in popup | `aria-busy="true"` on grid |
| Disabled | Trigger muted; no interactions | `aria-disabled="true"` |

## 11. Behavior & interactions
- Opening the popup focuses the search input.
- Typing in the search input filters the asset grid with debounce (150 ms default).
- Clicking an asset selects it, fires `mj-change`, and closes the popup (single mode). In multi mode, clicking toggles the asset without closing.
- Selected assets are tracked in `recentAssets` (backed by `localStorage` under a namespace keyed to `type`).
- Category navigation scrolls the virtual grid to the category's starting index.
- The virtual grid renders only visible rows; `aria-rowcount` and `aria-setsize`/`aria-posinset` are set on cells.
- Skin tone selection (emoji mode): a swatch popover appears; selecting a tone applies it to all subsequent emoji and to the current selection if applicable.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Enter` / `Space` | Open popup (trigger); select focused asset (grid) |
| `ArrowRight` | Move focus to next asset in row |
| `ArrowLeft` | Move focus to previous asset in row |
| `ArrowDown` | Move focus to asset in next row (same column) |
| `ArrowUp` | Move focus to asset in previous row (same column) |
| `Home` | Move focus to first asset in current row |
| `End` | Move focus to last asset in current row |
| `Ctrl+Home` | Move focus to first asset in grid |
| `Ctrl+End` | Move focus to last asset in grid |
| `Tab` | Cycle: search input → category nav → asset grid → skin-tone button |
| `Escape` | Close popup; return focus to trigger |
| Printable character | Types into search field (when grid has focus, transfers to search) |

## 13. Accessibility
- Trigger `<button>` has `aria-haspopup="dialog"` and `aria-expanded`; `aria-label` includes the name of the selected asset (e.g., "Emoji picker, current: thumbs up").
- Popup has `role="dialog"` with `aria-label` (e.g., "Choose an emoji").
- Asset grid has `role="grid"` with `aria-label` for the active category, `aria-rowcount`, and `aria-colcount`.
- Each grid row has `role="row"`; each cell has `role="gridcell"`.
- Asset button within each cell has `aria-label` equal to the asset's name (e.g., "thumbs up") and `aria-selected`.
- Search result count announced via polite live region: "24 results for 'heart'".
- Category buttons have `aria-selected` / `aria-pressed` to reflect the active category.
- Skin-tone picker has `role="radiogroup"` with individual `role="radio"` swatches.

## 14. Form participation
- Form-associated via `ElementInternals`; contributes `name=value` (or `name=id1,id2,...` in multi mode).
- `required`: `validity.valueMissing` when `value` is empty.
- On form reset, `value` reverts to the initial `value` attribute; recents are not cleared.

## 15. Internationalization & RTL
- `search-placeholder` is author-supplied and should be translated.
- Emoji names are sourced from the Unicode CLDR data included in the data source; the data source should provide locale-appropriate names.
- In RTL, the category nav may be on the right side; grid scrolls from the right; search input mirrors.
- Skin tone modifier names are provided by the emoji data source.

## 16. Progressive enhancement / SSR
- Server renders a `<select>` or `<input type="hidden">` with the current value inside `<mj-asset-picker>`.
- Before upgrade, the hidden input retains the value for form submission.
- On upgrade, the picker UI is built; the hidden input stays in sync.
- Without scripting, the hidden input submits the pre-set value; no interactive picker is available.

## 17. Dependencies
- Section 6: Registry/base element, design tokens, overlay/positioning engine, focus utilities (roving tabindex in grid), form-association helper, live-region service, collection/virtualization utility, data-source adapter.
- Built-in emoji data set (Unicode 15.0 subset, lazy-loaded); replaceable via `dataSource`.

## 18. Edge cases & error handling
- Data source returns zero categories: grid is empty; search works if the source supports it.
- Search returns 0 results: no-results slot shown; category nav hidden.
- Very large asset sets (>5000): virtualization handles rendering; initial category load may be deferred.
- `value` set to an ID not in the data source: trigger shows a "?" placeholder; no asset is highlighted.
- `localStorage` unavailable: recents are held in memory for the session only; no error is thrown.
- Popup taller than viewport: grid area scrolls; search and categories stay pinned.

## 19. Acceptance criteria
- [ ] Typing in search filters the grid within 150 ms debounce; live region announces result count.
- [ ] Clicking an asset fires `mj-change` with correct `value` and `asset`; popup closes (single mode).
- [ ] Arrow keys navigate the grid; `Ctrl+Home`/`Ctrl+End` reach first/last asset.
- [ ] `aria-rowcount`, `aria-colcount`, `aria-setsize`, `aria-posinset` correct on virtual grid.
- [ ] Recents section populates after selection; backed by `localStorage`.
- [ ] Skin tone selector changes `skinTone` property and fires `mj-skin-tone-change`.
- [ ] `required` with no selection fails `checkValidity()`.
- [ ] axe-core reports zero violations in open, searching, and selected states.
- [ ] RTL layout mirrors grid and category nav.
- [ ] Virtual scrolling renders only visible rows; grid scrolls without layout shift.

## 20. Open questions
- Should favorites be persisted to `localStorage` alongside recents, or is that an author-managed concern?
- Should `type="font"` render a live preview of the user's typed sample text, or a static character specimen?
- How should the component handle emoji that render differently across operating systems (e.g., ZWJ sequences, platform fallback glyphs)?
