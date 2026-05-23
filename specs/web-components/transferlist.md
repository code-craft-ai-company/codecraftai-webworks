# Transfer List Spec

- **Tag:** `<mj-transfer-list>`
- **Class / file:** `MjTransferList` / `mjtransferlist.js`
- **Category:** Selection & dropdown-style controls
- **Primary or Variant:** Primary
- **Synonyms covered:** Dual listbox
- **Phase:** P2
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-transfer-list>` presents two side-by-side `<mj-listbox>` instances — a source list and a target list — with controls to move items between them. The component is the standard implementation of the "dual listbox" / "shuttle box" pattern. It is used for assignment flows such as assigning roles to users, picking columns for a report, or ordering selected items in a sequence.

## 2. When to use / when not to use
**Use** when the distinction between "available" and "selected" must be visually explicit as two separate lists, and when items can be reordered within the target list. **Use** when both the full available set and the current selection need to be visible simultaneously. **Do not use** when a checkbox group or multi-select listbox communicates the selection clearly — those are lower-complexity alternatives. **Do not use** when the source and target lists are unrelated datasets — the component is designed for moving items within a single pool.

## 3. Anatomy
- **Container** (`part="container"`) — flex row of source, controls, and target panes.
- **Source pane** (`part="source-pane"`) — left/start listbox region.
- **Source header** (`part="source-header"`) — label and item count for the source list.
- **Source search** (`part="source-search"`) — optional filter input for the source list.
- **Source listbox** (`part="source-listbox"`) — `<mj-listbox>` of available items.
- **Controls** (`part="controls"`) — column of move buttons between the two lists.
- **Move-right button** (`part="move-right"`) — move selected source items to target.
- **Move-all-right button** (`part="move-all-right"`) — move all source items to target.
- **Move-left button** (`part="move-left"`) — move selected target items back to source.
- **Move-all-left button** (`part="move-all-left"`) — move all target items back to source.
- **Move-up button** (`part="move-up"`) — reorder selected target item up.
- **Move-down button** (`part="move-down"`) — reorder selected target item down.
- **Target pane** (`part="target-pane"`) — right/end listbox region.
- **Target header** (`part="target-header"`) — label and item count for the target list.
- **Target search** (`part="target-search"`) — optional filter input for the target list.
- **Target listbox** (`part="target-listbox"`) — `<mj-listbox>` of selected items.
- **Empty source** (`part="empty-source"`) — shown when the source list is empty.
- **Empty target** (`part="empty-target"`) — shown when the target list is empty.

## 4. Variants & modes
| Variant / mode | Attribute | Behavior |
|----------------|-----------|----------|
| Default | — | Bidirectional move; no reorder |
| With reorder | `reorder` (boolean) | Move-up/down buttons visible in target pane |
| With search | `searchable` (boolean) | Filter inputs shown above both lists |
| Vertical | `orientation="vertical"` | Lists stacked; controls between them (horizontal arrows) |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `name` | string | `""` | Yes | Form field name; target list values submitted |
| `value` | string | `""` | Yes | Comma-separated values currently in the target list |
| `disabled` | boolean | `false` | Yes | Disables all interactions |
| `required` | boolean | `false` | Yes | Target list must be non-empty |
| `reorder` | boolean | `false` | Yes | Shows move-up/down buttons for target ordering |
| `searchable` | boolean | `false` | Yes | Shows filter inputs above each list |
| `orientation` | `"horizontal"` \| `"vertical"` | `"horizontal"` | Yes | Layout direction |
| `source-label` | string | `"Available"` | Yes | Accessible label for the source pane |
| `target-label` | string | `"Selected"` | Yes | Accessible label for the target pane |
| `max-target` | number | `0` | Yes | Maximum items allowed in target; 0 = unlimited |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `sourceItems` | `TransferItem[]` | Items currently in the source list |
| `targetItems` | `TransferItem[]` | Items currently in the target list (in display order) |
| `allItems` | `TransferItem[]` | Combined full item pool (source + target) |
| `validity` | `ValidityState` | Delegated from `ElementInternals` |
| `validationMessage` | `string` | Localizable invalid message |

**`TransferItem` shape:**
```
{
  value: string;
  label: string;
  icon?: string;
  disabled?: boolean;
}
```

## 7. Slots
| Slot | Description |
|------|-------------|
| (default) | `<mj-option>` elements defining the full item pool; items with `selected` start in the target list |
| `source-header` | Custom source pane header content |
| `target-header` | Custom target pane header content |
| `empty-source` | Custom empty-source state |
| `empty-target` | Custom empty-target state |
| `controls` | Fully custom controls column (replaces default move buttons) |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-change` | `{ targetValues: string[], sourceValues: string[] }` | Yes | No | Fired after any move operation |
| `mj-move` | `{ items: TransferItem[], direction: "to-target" \| "to-source" }` | Yes | Yes | Fired before a move; cancel to prevent |
| `mj-reorder` | `{ item: TransferItem, fromIndex: number, toIndex: number }` | Yes | No | Fired when target item is reordered |

## 9. CSS parts & custom properties
**Parts:** `container`, `source-pane`, `source-header`, `source-search`, `source-listbox`, `controls`, `move-right`, `move-all-right`, `move-left`, `move-all-left`, `move-up`, `move-down`, `target-pane`, `target-header`, `target-search`, `target-listbox`, `empty-source`, `empty-target`

**Custom properties:**
| Property | Default token | Description |
|----------|---------------|-------------|
| `--mj-transfer-list-pane-min-width` | `12rem` | Minimum width of each pane |
| `--mj-transfer-list-pane-height` | `16rem` | Height of both listboxes |
| `--mj-transfer-list-controls-gap` | `--mj-space-2` | Gap between move buttons |
| `--mj-transfer-list-controls-width` | `3rem` | Width of the controls column |
| `--mj-transfer-list-gap` | `--mj-space-4` | Gap between panes and controls |
| `--mj-transfer-list-border-radius` | `--mj-radius-md` | Pane container corner radius |

## 10. States
| State | Visual effect | ARIA effect |
|-------|--------------|-------------|
| Source item selected | Highlighted row | `aria-selected="true"` |
| Target item selected | Highlighted row | `aria-selected="true"` |
| Move button active | Enabled; solid appearance | — |
| Move button disabled | Muted; no pointer events | `disabled` on `<button>` |
| Move-all disabled | Muted when source/target is empty | `disabled` on `<button>` |
| Max target reached | To-target buttons disabled | `aria-disabled="true"`; live region |
| Source empty | Empty-source slot shown | — |
| Target empty | Empty-target slot shown | — |
| Disabled (all) | All interactions muted | `aria-disabled="true"` on both listboxes |
| Invalid | Error border on target pane | `aria-invalid="true"` on target listbox |

## 11. Behavior & interactions
- Items are selected in the source listbox using the standard `<mj-listbox>` multi-selection interactions (click, Shift+click, Ctrl+click, arrow keys, Shift+arrow).
- The "move right" button moves all selected source items to the end of the target list; the button is disabled when no source items are selected.
- The "move all right" button moves all non-disabled source items to the target.
- The "move left" button moves all selected target items back to the source; the button is disabled when no target items are selected.
- The "move all left" button moves all non-disabled target items back to the source.
- `reorder` mode: when exactly one target item is selected, the move-up/down buttons are enabled; clicking moves that item one position in the target list.
- `max-target` enforcement: move buttons that would exceed the limit are disabled; attempting to move via keyboard announces the limit via a live region.
- After a move, focus is set to the corresponding button (if it remains enabled) or to the listbox that received the items.
- `searchable` mode: typing in a list's search input filters its visible items without removing them from the underlying data.

## 12. Keyboard interaction
| Key | Context | Action |
|-----|---------|--------|
| All `<mj-listbox>` keys | Either listbox | Standard listbox navigation and selection (see Listbox spec) |
| `Tab` | — | Move focus: source search (if shown) → source listbox → move buttons → target listbox → target search (if shown) → move-up/down (if shown) |
| `Enter` / `Space` | Move button focused | Execute the move |
| `Ctrl+ArrowRight` | Source item focused | Move selected source items to target (keyboard shortcut) |
| `Ctrl+ArrowLeft` | Target item focused | Move selected target items to source |
| `Ctrl+ArrowUp` | Target item focused | Move selected target item up (reorder mode) |
| `Ctrl+ArrowDown` | Target item focused | Move selected target item down (reorder mode) |

## 13. Accessibility
- Each pane has `role="region"` with `aria-labelledby` pointing to its header element.
- Each embedded `<mj-listbox>` follows the listbox accessibility pattern (see Listbox spec).
- Move buttons have descriptive `aria-label` values: "Move selected to [target-label]", "Move all to [target-label]", "Move selected to [source-label]", "Move all to [source-label]", "Move up", "Move down".
- When a move completes, a polite live region announces: "N item(s) moved to [target/source label]. [target-label] now contains M items."
- When `max-target` is reached, a polite live region announces: "Maximum [N] items reached in [target-label]."
- The controls column has `role="group"` with `aria-label="Move controls"`.
- Move buttons are disabled (`disabled` attribute) when there is nothing to move; `aria-disabled` is not used separately.

## 14. Form participation
- Form-associated via `ElementInternals`; each target item contributes `name=value` to `FormData` in target-list order.
- Source items are not submitted.
- `required`: `validity.valueMissing` when the target list is empty.
- On form reset, all items return to their initial side (as defined by the `selected` attribute on slotted `<mj-option>` elements); target order reverts to the initial order.

## 15. Internationalization & RTL
- In RTL, source pane is on the right and target pane is on the left; move-right becomes move-left visually (the semantic direction is the same: source → target).
- All button labels (`source-label`, `target-label`) are author-supplied; default English strings ("Available", "Selected") must be overridden for non-English UIs.
- Move button `aria-label` strings are constructed from the localized `source-label` and `target-label` values.
- Search inputs inside each pane follow RTL text direction.

## 16. Progressive enhancement / SSR
- Server renders two `<select multiple>` elements (source and target) with `<option>` children inside `<mj-transfer-list>`.
- Before upgrade both native selects are independently operable.
- On upgrade, the native selects are hidden; the component builds the two `<mj-listbox>` instances from the native option data; the target native select stays in sync for form submission.
- Without scripting, the two native selects are functional; the move buttons are not available, but the user can manually manage both selects.

## 17. Dependencies
- Section 6: Registry/base element, design tokens, focus utilities, form-association helper, live-region service.
- `<mj-listbox>` — both panes are `<mj-listbox>` instances.
- `<mj-option>` — declarative item primitive.

## 18. Edge cases & error handling
- Source list is empty on initial render: source pane shows `empty-source` slot; move-right and move-all-right buttons are disabled.
- Target list is empty: target pane shows `empty-target` slot; `required` validation fails.
- Moving an item while `mj-move` is canceled: item stays in its current list; no state change.
- `max-target` set to a value less than the current number of target items: existing items stay; move buttons are disabled until items are moved back to source.
- Very large item pool (>500): items are rendered via the `<mj-listbox>` virtualization; search filtering performs client-side.
- `reorder` with multiple target items selected: move-up/down buttons are disabled (they require exactly one item selected); a tooltip explains this.
- Disabled items in a move-all operation: disabled items are not moved; they stay in their current list.

## 19. Acceptance criteria
- [ ] Move-right button moves selected source items to target; `mj-change` fires with updated values.
- [ ] Move-all-right moves all non-disabled source items; move-all-left reverses.
- [ ] `mj-move` event fires before move; canceling prevents the move.
- [ ] `reorder=true`: move-up/down reorder a single selected target item; `mj-reorder` fires.
- [ ] Source and target pane `aria-labelledby` points to their respective header.
- [ ] Move button `aria-label` values include source/target labels.
- [ ] Live region announces count after each move.
- [ ] `required` with empty target fails `checkValidity()`.
- [ ] Form submission includes one `name=value` per target item in display order.
- [ ] `Ctrl+ArrowRight` from a source item moves it to target; `Ctrl+ArrowLeft` moves it back.
- [ ] axe-core reports zero violations in default, reorder, searchable, and disabled states.
- [ ] RTL layout swaps pane positions; move buttons remain semantically correct.

## 20. Open questions
- Should the search inputs filter only the visible list or also affect which items are moved by move-all?
- Should drag-and-drop between the two panes (and within the target for reordering) be in scope for this component?
- Should the component support a "locked" mode where some target items cannot be moved back to source?
