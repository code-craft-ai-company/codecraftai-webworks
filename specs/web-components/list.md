# List Spec

- **Tag:** `<mj-list>`
- **Class / file:** `MjList` / `mjlist.js`
- **Category:** Tables, lists & structured data
- **Primary or Variant:** Primary
- **Synonyms covered:** Ordered list, Unordered list, Description list, Definition list
- **Phase:** P0
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-list>` is a semantic list primitive that renders ordered (`<ol>`), unordered
(`<ul>`), or description (`<dl>`) lists with consistent token-driven spacing,
optional icons/counters, nested levels, and accessible semantics. It covers all
three standard HTML list types from a single component, controlled by the `type`
attribute. It does not virtualize — for large or streaming lists use
`<mj-virtual-list>`.

## 2. When to use / when not to use
**Use** when presenting a finite, static or slowly-changing set of items where the
full list fits in the viewport without performance concern (up to ~200 items). Use
`type="description"` for term/definition pairs (glossaries, metadata panels). Use
`type="ordered"` for sequential steps or ranked content. **Do not use** for
interactive navigation — use `<mj-side-nav>` or `role="listbox"` components. For
large datasets use `<mj-virtual-list>`. For selectable rows use `<mj-data-table>`.

## 3. Anatomy
- **List root** — `<ul>`, `<ol>`, or `<dl>` rendered in shadow DOM or upgraded from
  light-DOM markup.
- **List item** — `<li>` (ordered/unordered) or `<dt>`/`<dd>` pair (description).
- **Item marker** — `::marker` pseudo or custom icon slot per item; ordered lists
  support `counter-style` via token.
- **Nested list** — child `<mj-list>` inside an item creates an indented sub-list;
  level depth tracked via CSS `--mj-list-level` custom property.

## 4. Variants & modes
| Variant | `type` value | Element rendered | Behavior |
|---------|-------------|-----------------|----------|
| Unordered | `unordered` (default) | `<ul>` | Bullet markers; order not implied. |
| Ordered | `ordered` | `<ol>` | Numeric or alpha counters; order implied. |
| Description | `description` | `<dl>` | Term (`<dt>`) + definition (`<dd>`) pairs. |

Visual density controlled by `density`: `default` | `compact` | `spacious`.
List style controlled by `marker`: `bullet` | `disc` | `circle` | `square` |
`decimal` | `alpha` | `roman` | `none`.

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `type` | `unordered\|ordered\|description` | `unordered` | yes | HTML list type rendered. |
| `marker` | `bullet\|disc\|circle\|square\|decimal\|alpha\|roman\|none` | `bullet` | yes | Marker/counter style. |
| `density` | `default\|compact\|spacious` | `default` | yes | Vertical spacing between items. |
| `nested` | boolean | false | yes | Applies nested-list indent styles when this list is inside another `<mj-list>`. |
| `dividers` | boolean | false | yes | Renders a `<hr>`-equivalent separator between items. |
| `start` | number | `1` | yes | Starting counter value (ordered lists only; maps to `<ol start>`). |
| `reversed` | boolean | false | yes | Reverses counter direction (ordered only; maps to `<ol reversed>`). |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `items` | `ListItem[]` | `{ label: string, description?: string, icon?: string, href?: string, children?: ListItem[] }` — programmatic data path; generates the list from JS. |

## 7. Slots
| Slot | Description |
|------|-------------|
| (default) | Light-DOM `<li>`, `<dt>`/`<dd>` elements upgraded in place. |
| `item-icon` | Per-item icon slot (description: per-term); injected by callers using named slot pattern `slot="item-icon"` on child elements. |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-item-click` | `{ index: number, label: string, href?: string }` | true | false | Fired when a list item with `href` or `data-action` is activated by click or `Enter`. |

## 9. CSS parts & custom properties
**Parts:** `list`, `item`, `term`, `definition`, `marker`, `divider`.

| Custom property | Default | Purpose |
|----------------|---------|---------|
| `--mj-list-gap` | `6px` | Vertical gap between list items. |
| `--mj-list-gap-compact` | `2px` | Gap in compact density. |
| `--mj-list-gap-spacious` | `12px` | Gap in spacious density. |
| `--mj-list-indent` | `20px` | Left indent per nesting level. |
| `--mj-list-marker-color` | `token(--mj-color-text-subtle)` | Marker/counter color. |
| `--mj-list-divider-color` | `token(--mj-color-border)` | Divider line color. |
| `--mj-list-term-weight` | `600` | Font weight for `<dt>` terms. |

## 10. States
- **default** — list renders all items; no interactive state.
- **empty** — `items` is empty and no slotted children; component renders nothing (no empty state UI; caller handles).
- **nested** — `nested` attribute true; `--mj-list-indent` multiplied by computed depth.
- **dividers** — horizontal rules between items.

## 11. Behavior & interactions
When the `items` property is set, the component generates list markup from the
array and ignores slotted light DOM. When `items` is not set, the component upgrades
light-DOM `<li>` / `<dt>` / `<dd>` elements by wrapping them in the adopted
stylesheet scope. Nested `<mj-list>` elements inside `<li>` slots automatically
receive `nested` attribute set by the parent.

Items with an `href` property (or `<a>` inside a `<li>`) are keyboard-operable
links; `mj-item-click` fires alongside native link navigation. Items with
`data-action` but no `href` are button-like and emit `mj-item-click` only.

The `description` type groups consecutive `<dt>`/`<dd>` elements rendered from the
`items` array as `{ label (term), description (definition) }` pairs. Multiple
definitions per term are supported by passing `description` as a string array.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` | Moves focus to the next focusable element within an item (link or button). |
| `Enter` / `Space` | Activates an item's link or action button. |
| `Arrow Down / Up` | No built-in navigation (list is not a composite widget); browser native scroll applies. |

## 13. Accessibility
- Renders native `<ul>`, `<ol>`, or `<dl>`; list semantics are implicit and correct without added ARIA.
- `marker="none"` adds `list-style: none`; when browsers strip list semantics for this CSS value, `role="list"` is explicitly added to preserve semantics (Safari workaround).
- Description list: `<dt>` elements have an implicit role of `term`; `<dd>` have `definition`.
- Nested lists: nesting level is conveyed by native element nesting; no additional `aria-level` needed.
- Icon-only item labels must include a visually-hidden text alternative.
- Dividers use `<hr aria-hidden="true">` — decorative.

## 14. Form participation
N/A — display component; no form value.

## 15. Internationalization & RTL
- In RTL, indent shifts to the right side; marker position follows `dir`.
- `counter-style` for `alpha` and `roman` uses `Intl`-aware counter styles where supported.
- Item labels passed via the `items` property must be pre-translated by the caller.

## 16. Progressive enhancement / SSR
Server renders a standard `<ul>/<ol>/<dl>` inside `<mj-list>`. Before JS loads the
native list is fully readable. On upgrade, the component adopts the token-based
stylesheet and applies density/divider/marker attributes with no layout shift.

## 17. Dependencies
- Design-token stylesheet (§6).
- Base element helper (§6).
- No other components; `<mj-virtual-list>` is a separate component for large datasets.

## 18. Edge cases & error handling
- **`type="description"` with odd items count** — last item without a pair renders `<dt>` only; no error.
- **Deeply nested lists (>5 levels)** — indent continues to apply; no cap enforced; callers responsible for readability.
- **Mixed `<li>` and `<dt>`/`<dd>` in light DOM** — `type` attribute determines interpretation; mismatched elements are wrapped in the correct container and a console warning is logged.
- **`items` property set on a component with light-DOM children** — property data wins; light DOM is hidden via `slot` redirection; warning logged.

## 19. Acceptance criteria
- [ ] `type="unordered"` renders `<ul>` with `<li>` children; `type="ordered"` renders `<ol>`; `type="description"` renders `<dl>` with `<dt>`/`<dd>`.
- [ ] `marker="none"` adds `role="list"` to preserve list semantics in Safari.
- [ ] `density` attribute applies correct `--mj-list-gap` token variant.
- [ ] `dividers` attribute renders `<hr aria-hidden="true">` between items.
- [ ] `nested` attribute applies `--mj-list-indent` indentation.
- [ ] `items` property generates correct markup including nested children.
- [ ] `start` and `reversed` attributes map to `<ol start>` and `<ol reversed>`.
- [ ] SSR: light-DOM `<ul>/<ol>/<dl>` readable without JS; upgraded in place.
- [ ] `mj-item-click` fires on link/action item activation via mouse and keyboard.
- [ ] axe audit: zero violations for all three list types.
- [ ] RTL: indent and marker on correct side.

## 20. Open questions
- Should `<mj-list>` support a `selectable` mode (listbox semantics) or is that always delegated to `<mj-listbox>`?
- Should description list support multi-term/multi-definition grouping (`<div>` wrapper inside `<dl>`) for styling?
