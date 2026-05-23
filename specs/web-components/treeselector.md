# Tree Selector Spec

- **Tag:** `<mj-tree-selector>`
- **Class / file:** `MjTreeSelector` / `mjtreeselector.js`
- **Category:** Selection & dropdown-style controls
- **Primary or Variant:** Primary
- **Synonyms covered:** Hierarchical selector
- **Phase:** P2
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-tree-selector>` presents a hierarchical tree of nodes where users can expand/collapse branches and select nodes using single, multi, or tri-state checkbox selection semantics. Parent nodes reflect the aggregate state of their children (checked/indeterminate/unchecked). Typical uses include category hierarchies, folder/file trees for selection, permission trees, and organizational unit pickers.

## 2. When to use / when not to use
**Use** when the data is inherently hierarchical and the depth is variable. **Use tri-state checkboxes** when parent selection implies child selection. **Do not use** for flat lists — use `<mj-listbox>`. **Do not use** for mutually exclusive hierarchical choices — use a cascading select. **Do not use** for navigation — use `<mj-tree-navigation>`. **Do not use** when the tree depth exceeds 6–7 levels without virtualization; inform users of deep hierarchies with breadcrumb or path display.

## 3. Anatomy
- **Tree root** (`part="tree"`) — `role="tree"` container.
- **Tree item** (`part="tree-item"`) — `role="treeitem"` node row.
- **Item toggle** (`part="item-toggle"`) — expand/collapse chevron button.
- **Item checkbox** (`part="item-checkbox"`) — tri-state checkbox indicator (checkbox selection mode).
- **Item icon** (`part="item-icon"`) — optional node type icon.
- **Item label** (`part="item-label"`) — node display text.
- **Item badge** (`part="item-badge"`) — optional count or status badge.
- **Item children** (`part="item-children"`) — `role="group"` subtree container.
- **Loading node** (`part="item-loading"`) — placeholder while async children load.
- **Empty tree** (`part="empty"`) — shown when tree has no nodes.

## 4. Variants & modes
| Variant / mode | Attribute | Behavior |
|----------------|-----------|----------|
| Single select | `selection="single"` | One node selected at a time; roving tabindex; no checkboxes |
| Multi-select | `selection="multi"` | Multiple nodes selected; no tri-state; Ctrl+click and Shift+click |
| Checkbox (tri-state) | `selection="checkbox"` | Checkboxes with parent tri-state reflecting children |
| No selection | `selection="none"` | Expand/collapse only; read-only tree |
| Async children | `src` or `dataSource` | Child nodes loaded on first expand |
| Single level open | `single-expand` (boolean) | Only one branch open at a time (accordion-style) |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `name` | string | `""` | Yes | Form field name; selected node values submitted |
| `value` | string | `""` | Yes | Comma-separated selected node values |
| `selection` | `"single"` \| `"multi"` \| `"checkbox"` \| `"none"` | `"single"` | Yes | Selection mode |
| `disabled` | boolean | `false` | Yes | Disables all interactions |
| `required` | boolean | `false` | Yes | At least one selection required |
| `single-expand` | boolean | `false` | Yes | Only one branch open at a time |
| `expanded` | string | `""` | Yes | Comma-separated node IDs that are expanded |
| `default-expanded` | string | `"root"` | Yes | Which nodes are expanded on first render (`"root"` = first level) |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `nodes` | `TreeNode[]` | Full tree data (set programmatically or read from light DOM) |
| `selectedNodes` | `TreeNode[]` | Currently selected node objects |
| `expandedNodeIds` | `Set<string>` | IDs of currently expanded branch nodes |
| `validity` | `ValidityState` | Delegated from `ElementInternals` |
| `validationMessage` | `string` | Localizable invalid message |
| `dataSource` | `TreeDataSource \| null` | Async child provider: `{ getChildren(nodeId): Promise<TreeNode[]> }` |

**`TreeNode` shape:**
```
{
  id: string;
  label: string;
  value?: string;           // defaults to id
  icon?: string;            // icon name or URL
  children?: TreeNode[];    // undefined = leaf; [] = known-empty branch
  hasChildren?: boolean;    // true = may have children; triggers async load on expand
  disabled?: boolean;
  badge?: string | number;
}
```

## 7. Slots
| Slot | Description |
|------|-------------|
| (default) | `<mj-tree-item>` elements for declarative tree markup |
| `empty` | Custom empty-tree content |
| `loading` | Custom per-node loading placeholder |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-change` | `{ values: string[], selectedNodes: TreeNode[] }` | Yes | No | Fired when selection changes |
| `mj-expand` | `{ nodeId: string, node: TreeNode }` | Yes | Yes | Fired before a node expands; cancel to prevent |
| `mj-collapse` | `{ nodeId: string, node: TreeNode }` | Yes | No | Fired when a node collapses |
| `mj-node-load-start` | `{ nodeId: string }` | Yes | No | Fired before async children are fetched |
| `mj-node-load-end` | `{ nodeId: string, children: TreeNode[] }` | Yes | No | Fired after async children load |
| `mj-node-error` | `{ nodeId: string, error: Error }` | Yes | No | Fired when async child load fails |

## 9. CSS parts & custom properties
**Parts:** `tree`, `tree-item`, `item-toggle`, `item-checkbox`, `item-icon`, `item-label`, `item-badge`, `item-children`, `item-loading`, `empty`

**Custom properties:**
| Property | Default token | Description |
|----------|---------------|-------------|
| `--mj-tree-item-height` | `2rem` | Height of each tree item row |
| `--mj-tree-item-indent` | `1.25rem` | Per-level indentation |
| `--mj-tree-item-gap` | `--mj-space-2` | Gap between icon, checkbox, and label |
| `--mj-tree-selected-bg` | `--mj-color-selected-subtle` | Selected row background |
| `--mj-tree-toggle-size` | `1.25rem` | Width of the expand/collapse chevron |
| `--mj-tree-checkbox-size` | `1rem` | Checkbox indicator size |
| `--mj-tree-indent-guide-color` | `--mj-color-border-subtle` | Color of optional indent guide lines |

## 10. States
| State | Visual effect | ARIA effect |
|-------|--------------|-------------|
| Collapsed branch | Children hidden; chevron pointing right | `aria-expanded="false"` on treeitem |
| Expanded branch | Children visible; chevron pointing down | `aria-expanded="true"` on treeitem |
| Loading children | Loading placeholder in children slot | `aria-busy="true"` on treeitem |
| Selected (single/multi) | Highlighted row | `aria-selected="true"` |
| Checked (checkbox) | Checkmark in indicator | `aria-checked="true"` |
| Indeterminate (checkbox) | Dash in indicator | `aria-checked="mixed"` |
| Unchecked (checkbox) | Empty indicator | `aria-checked="false"` |
| Focused | Focus ring on item row | `tabindex="0"` on focused item (roving) |
| Disabled node | Muted; no pointer events | `aria-disabled="true"` |
| Disabled tree | All nodes muted | `aria-disabled="true"` on tree |

## 11. Behavior & interactions
- Clicking the toggle chevron expands/collapses the branch; clicking the node row selects it (if not in `selection="none"` mode).
- **Checkbox mode**: checking a parent propagates checked state to all non-disabled children (downward propagation); parent state reflects child aggregate (indeterminate when some children are checked). Unchecking a parent unchecks all children.
- **Multi-select mode**: Ctrl+click toggles individual nodes; Shift+click selects a range of visible nodes between the last clicked node and the current.
- **Single-expand mode**: expanding a node collapses all sibling branches at the same level.
- **Async children**: on first expand of a node with `hasChildren: true`, `dataSource.getChildren(nodeId)` is called; a loading placeholder is shown until the promise resolves.
- Disabled nodes cannot be selected but can be expanded to reveal children.
- `single` selection mode uses roving tabindex; `multi` and `checkbox` modes use the tree's roving tabindex with each item reachable via arrows.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `ArrowDown` | Move focus to next visible tree item |
| `ArrowUp` | Move focus to previous visible tree item |
| `ArrowRight` | Expand focused branch; if already expanded, move focus to first child |
| `ArrowLeft` | Collapse focused expanded branch; if already collapsed, move focus to parent |
| `Home` | Move focus to first visible tree item |
| `End` | Move focus to last visible tree item |
| `Enter` / `Space` | Select or toggle the focused node (select mode); toggle checkbox (checkbox mode) |
| `*` | Expand all siblings of the focused node (same level) |
| Printable character | Type-ahead: focus first matching visible node |

## 13. Accessibility
- Tree root has `role="tree"` with `aria-label` or `aria-labelledby`.
- Each branch/leaf has `role="treeitem"` with `aria-level` (1-indexed depth), `aria-setsize` (count of siblings), `aria-posinset` (1-indexed position among siblings).
- Expanded branches have `aria-expanded="true"`; collapsed branches `aria-expanded="false"`; leaves have no `aria-expanded`.
- Child subtrees have `role="group"`.
- **Checkbox mode**: each treeitem has `aria-checked="true"`, `"false"`, or `"mixed"`.
- **Select modes**: `aria-selected="true"` on selected items.
- Roving tabindex: one `tabindex="0"` in the tree at all times; all others `-1`.
- Async loading: `aria-busy="true"` on the parent treeitem while children are loading; live region announces "Loading [node label] children" and then "Loaded [N] items".
- Expand/collapse live region: "[Node label] expanded" / "collapsed".

## 14. Form participation
- Form-associated via `ElementInternals`; each selected node contributes `name=value` to `FormData`.
- `required`: `validity.valueMissing` when no node is selected (does not apply to `selection="none"` mode).
- On form reset, selection reverts to the initial `value` attribute; expanded state reverts to `default-expanded`.

## 15. Internationalization & RTL
- In RTL, the tree indent is on the right; toggle chevrons point left-for-collapsed and down-for-expanded (chevron direction flips horizontally in RTL).
- `--mj-tree-item-indent` is applied with `padding-inline-start` so RTL is automatic.
- Live region strings (loading, expanded, collapsed) are localizable via the `l10n` hook.
- Type-ahead uses `Intl.Collator` for locale-aware prefix matching.

## 16. Progressive enhancement / SSR
- Server renders a nested `<ul>` / `<li>` structure with disclosure elements inside `<mj-tree-selector>`.
- Before upgrade the nested list is visible and keyboard-navigable as a plain list.
- On upgrade, the component reads the nested structure, builds the ARIA tree, and wires interactivity.
- Without scripting, the nested list is visible; expand/collapse is unavailable; selection is unavailable (a server-side link mechanism handles navigation if needed).

## 17. Dependencies
- Section 6: Registry/base element, design tokens, focus utilities (roving tabindex), form-association helper, live-region service, data-source adapter, collection/virtualization utility (for very large trees).
- `<mj-tree-item>` — declarative node element (companion).

## 18. Edge cases & error handling
- Circular node IDs in `nodes` data: component detects and breaks cycles; logs a console error.
- Async child load fails: error slot shown for that node; node remains expanded (empty); `mj-node-error` fires.
- Checking a parent while some children are still loading: loading children are treated as unchecked; on load completion, they are checked automatically.
- Very large tree (>1000 visible nodes): virtualization renders only visible rows; `aria-setsize`/`aria-posinset` are approximated or set to -1 if the total count is unknown.
- `expanded` attribute updated programmatically while a load is in progress: queue the expand until load resolves.
- `value` references IDs not present in the `nodes` data: values are held; no node is visually selected until the node appears.

## 19. Acceptance criteria
- [ ] Clicking toggle expands/collapses branch; `aria-expanded` toggles; `mj-expand`/`mj-collapse` fires.
- [ ] Checkbox mode: checking a parent checks all children; parent shows indeterminate when some children are checked.
- [ ] Arrow keys navigate all visible nodes; `ArrowRight`/`ArrowLeft` expand/collapse/ascend.
- [ ] Roving tabindex: one `tabindex="0"` at a time.
- [ ] `aria-level`, `aria-setsize`, `aria-posinset` correct on each treeitem.
- [ ] Async children show loading state; live region announces load start and completion.
- [ ] `required` with no selection fails `checkValidity()`.
- [ ] Form submission includes one `name=value` per selected node.
- [ ] axe-core reports zero violations in default, expanded, checkbox, and disabled states.
- [ ] RTL layout indents from the right; chevrons mirror.

## 20. Open questions
- Should upward propagation be supported (checking all children auto-checks the parent) or only downward propagation?
- Should virtual scrolling be mandatory for trees exceeding a configurable threshold, or opt-in?
- Is there a depth limit recommendation, and should the component warn when depth exceeds it?
