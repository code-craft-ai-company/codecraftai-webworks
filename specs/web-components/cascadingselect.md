# Cascading Select Spec

- **Tag:** `<mj-cascading-select>`
- **Class / file:** `MjCascadingSelect` / `mjcascadingselect.js`
- **Category:** Selection & dropdown-style controls
- **Primary or Variant:** Primary
- **Synonyms covered:** Dependent dropdown
- **Phase:** P2
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-cascading-select>` renders a ordered chain of `<mj-select>` controls where each level's available options depend on the selection made in the previous level. Common uses include Country → Region → City, Category → Subcategory → Item, and Make → Model → Trim automotive selectors. Each level can load its options asynchronously after its parent value is committed.

## 2. When to use / when not to use
**Use** when option sets form a strict hierarchy and downstream choices are meaningless without an upstream selection. **Do not use** for independent, non-hierarchical selections — use separate `<mj-select>` components. **Do not use** when the tree depth is variable and unknown at design time — consider `<mj-tree-selector>`. **Do not use** when all levels have small, fully known option sets that could fit in a single grouped `<mj-select>`.

## 3. Anatomy
- **Level container** (`part="levels"`) — flex/grid wrapper housing all level selects.
- **Level** (`part="level"`) — individual `<mj-select>` (or loading placeholder) for one step in the chain.
- **Level label** (`part="level-label"`) — visible label above/beside each level's select.
- **Level loading** (`part="level-loading"`) — skeleton or spinner shown while a level's options fetch.
- **Level error** (`part="level-error"`) — inline error when a level's fetch fails.

## 4. Variants & modes
| Variant / mode | Attribute | Behavior |
|----------------|-----------|----------|
| Static | `levels` JSON without `src` | All options pre-defined; no async |
| Async per level | `src` on each level config | Options fetched when parent value changes |
| Horizontal | `orientation="horizontal"` | Levels arranged in a row |
| Vertical | `orientation="vertical"` | Levels stacked in a column |
| Compact | `size="sm"` | Propagated to all child selects |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `name` | string | `""` | Yes | Base name; each level contributes `name[0]`, `name[1]`, etc., or per-level names |
| `value` | string | `""` | Yes | JSON-encoded array of selected values, one per level |
| `disabled` | boolean | `false` | Yes | Disables all levels |
| `required` | boolean | `false` | Yes | All levels must have a selection for validity |
| `orientation` | `"horizontal"` \| `"vertical"` | `"horizontal"` | Yes | Layout direction of levels |
| `size` | `"sm"` \| `"md"` \| `"lg"` | `"md"` | Yes | Size propagated to all child selects |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `levels` | `CascadeLevelConfig[]` | Array of level definitions: `{ name, label, placeholder, src?, options?, dataSource? }` |
| `values` | `string[]` | Current selected value per level (index matches level order) |
| `validity` | `ValidityState` | Delegated from `ElementInternals` |
| `validationMessage` | `string` | Localizable message (first incomplete required level) |

**`CascadeLevelConfig` shape:**
```
{
  name: string;           // form field name for this level
  label: string;          // visible label
  placeholder?: string;   // select placeholder
  options?: { value: string; label: string }[];  // static options for first level or fallback
  src?: string;           // URL template; {parentValue} interpolated
  dataSource?: DataSourceAdapter;
}
```

## 7. Slots
| Slot | Description |
|------|-------------|
| (default) | Slotted `<mj-select>` elements when using light-DOM composition instead of the `levels` property |
| `level-loading` | Custom per-level loading state (replaces the default skeleton) |
| `level-error` | Custom per-level error content |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-change` | `{ levelIndex: number, value: string, values: string[] }` | Yes | No | Fired when any level value changes |
| `mj-level-load-start` | `{ levelIndex: number, parentValue: string }` | Yes | No | Fired before async fetch for a level |
| `mj-level-load-end` | `{ levelIndex: number, options: object[] }` | Yes | No | Fired after successful async fetch |
| `mj-level-error` | `{ levelIndex: number, error: Error }` | Yes | No | Fired when a level's fetch fails |
| `mj-complete` | `{ values: string[] }` | Yes | No | Fired when all levels have a value |

## 9. CSS parts & custom properties
**Parts:** `levels`, `level`, `level-label`, `level-loading`, `level-error`

**Custom properties:**
| Property | Default token | Description |
|----------|---------------|-------------|
| `--mj-cascading-select-gap` | `--mj-space-3` | Gap between level selects |
| `--mj-cascading-select-level-min-width` | `10rem` | Minimum width per level select |
| `--mj-cascading-select-level-loading-height` | `--mj-size-control-md` | Height of loading skeleton |

## 10. States
| State | Visual effect | ARIA effect |
|-------|--------------|-------------|
| Default | All available levels rendered | — |
| Level pending | Level select replaced by loading placeholder | `aria-busy="true"` on level container |
| Level disabled | Level select is disabled/muted | `aria-disabled="true"` on level select |
| Level error | Error message replaces select | Error live region announced |
| Downstream cleared | Downstream selects reset to placeholder | Value attribute updated |
| All complete | No loading states; `mj-complete` fired | — |
| Disabled (all) | All levels disabled | `aria-disabled="true"` on container |
| Invalid | Incomplete required level highlighted | `aria-invalid="true"` on first incomplete level |

## 11. Behavior & interactions
- When a level's value changes, all downstream levels are immediately reset to their placeholder (empty value).
- After the reset, if the changed level has a `src` or `dataSource` defined for the next level, an async fetch is triggered for the next level's options, keyed to the parent's selected value.
- While a level is fetching, its select is rendered as a disabled skeleton/loading indicator.
- If a level fetch fails, the error state is shown for that level; downstream levels remain disabled.
- Retrying a failed level re-fetches with the same parent value.
- When `disabled` is toggled at runtime, all child selects are updated.
- Programmatic assignment of `values` array: each level is set in order; downstream options are loaded as needed.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` | Move through each level's select in DOM order |
| Within each `<mj-select>` | All keys from the Select spec apply (arrows, Enter, Escape, type-ahead) |
| `Tab` after last level | Move focus outside the component |

## 13. Accessibility
- Each level's `<mj-select>` has its own visible label (from `level-label` part) associated via `aria-labelledby` or a `<label>` element.
- When a level is loading, a live region announces "Loading [Level Label] options".
- When a level load fails, an alert live region announces the error.
- When a downstream level resets, no announcement is made (the visual reset is sufficient for sighted users; screen reader users re-read the now-empty select label on next focus).
- The container element has `role="group"` with an `aria-labelledby` referencing a group label if one is provided.

## 14. Form participation
- Form-associated via `ElementInternals`; each level contributes its own `name=value` entry to `FormData` using the per-level `name` from `CascadeLevelConfig`.
- If a level has no selection, it contributes an empty string (or is omitted based on `required`).
- `required`: all levels must have a non-empty value; the first missing level triggers `valueMissing`.
- On form reset, all levels revert to empty; the first level's static options are reloaded.

## 15. Internationalization & RTL
- Levels reorder visually in RTL (flex-direction reversal for horizontal orientation) but the data order in `values` and `FormData` remains left-to-right (first level first).
- Level labels and placeholders are author-supplied.
- Loading and error messages are provided via slots; no built-in English strings.

## 16. Progressive enhancement / SSR
- Server can render multiple `<mj-select>` elements inside `<mj-cascading-select>` with static options.
- Before upgrade, each nested `<mj-select>` (or native `<select>`) is independently operable.
- On upgrade, the component wires up change listeners across the chain.
- Without scripting, the statically-rendered selects remain functional (dynamic loading is unavailable, but static options work).

## 17. Dependencies
- Section 6: Registry/base element, design tokens, live-region service, form-association helper, data-source adapter.
- `<mj-select>` — each level is an `<mj-select>` instance.

## 18. Edge cases & error handling
- Level fetch returns zero options: downstream select is shown as empty with its placeholder; if `required`, validation fails.
- Parent value changes while downstream level is still fetching: abort the in-flight request and start a new fetch.
- `levels` property set with more items than were initially rendered: component re-renders the level list.
- Circular dependency in `src` URL templates: not detected; authors are responsible for non-circular configs.
- Setting `values` programmatically skipping intermediate levels: intermediate levels are loaded in series before the final level is set.

## 19. Acceptance criteria
- [ ] Selecting a value in level N clears all levels N+1 and beyond.
- [ ] Async fetch for level N+1 is triggered after level N value changes; loading state shown.
- [ ] `mj-change` fires with correct `levelIndex`, `value`, and `values`.
- [ ] `mj-complete` fires only when all levels have a non-empty value.
- [ ] `mj-level-error` fires and error state shown when async fetch rejects.
- [ ] `required` with any empty level fails `checkValidity()`.
- [ ] Form submission includes one `name=value` pair per level.
- [ ] axe-core reports zero violations in default, loading, error, and complete states.
- [ ] In-flight fetch is aborted when parent level changes before the fetch resolves.

## 20. Open questions
- Should level labels be required or optional (with a fallback to a positional default like "Level 1")?
- Should the component support more than one selection per level (i.e., multi-select cascades)?
- How should the `values` setter behave when intermediate level options have not been fetched yet — queue and apply sequentially, or require the caller to manage ordering?
