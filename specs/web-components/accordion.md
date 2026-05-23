# Accordion Spec

- **Tag:** `<mj-accordion>`
- **Class / file:** `MjAccordion` / `mjaccordion.js`
- **Category:** Layout & content containers (§5.5)
- **Primary or Variant:** Primary
- **Synonyms covered:** Accordion group; composes `<mj-disclosure>` items
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-accordion>` groups multiple `<mj-disclosure>` panels and coordinates their
open/closed state so that the ensemble behaves as a coherent accordion widget.
It handles single-open (only one panel at a time) and multi-open modes, animated
height transitions, and the keyboard navigation pattern defined by the WAI-ARIA
Authoring Practices Guide for the Accordion pattern.

## 2. When to use / when not to use

**Use** when a page has several related sections where only one (or a few) are
likely to need reading at once and vertical space is at a premium — FAQs,
settings categories, feature lists. **Do not use** when all content should be
visible simultaneously — use plain sections or `<mj-stack>` with `<mj-surface>`
panels. **Do not use** as a navigation widget — use `<mj-tabs>` when sections
map to distinct views, or `<mj-side-nav>` for hierarchical navigation.

## 3. Anatomy

- **root** — the outer element rendered as a plain `<div>`; surfaced as
  `::part(root)`.
- **default slot** — expects one or more `<mj-disclosure>` children, each
  representing one accordion panel.
- Individual panel anatomy is defined in `disclosure.md`.

## 4. Variants & modes

| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Single-open (default) | `allow-multiple` absent | Only one `<mj-disclosure>` may be open at a time; opening one closes the others |
| Multi-open | `allow-multiple` boolean | Any number of panels may be open simultaneously |
| Bordered | `bordered` boolean | Draws a border around the accordion and between panels |
| Flush | `flush` boolean | Removes outer border; panels share the page background |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `allow-multiple` | boolean | `false` | Yes | When set, multiple panels may be open at the same time |
| `bordered` | boolean | `true` | Yes | Draws outer border and dividers between panels |
| `flush` | boolean | `false` | Yes | Removes outer padding and blends with the page background |
| `disabled` | boolean | `false` | Yes | Disables all child disclosures; propagated to each `<mj-disclosure>` child |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `openPanels` | `MjDisclosure[]` (readonly) | Array of currently open `<mj-disclosure>` child elements |
| `panels` | `MjDisclosure[]` (readonly) | Array of all direct `<mj-disclosure>` child elements |

## 7. Slots

| Slot | Description |
|------|-------------|
| (default) | One or more `<mj-disclosure>` elements forming the accordion items |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-accordion-open` | `{ panel: MjDisclosure, index: number }` | Yes | No | Emitted after a panel opens |
| `mj-accordion-close` | `{ panel: MjDisclosure, index: number }` | Yes | No | Emitted after a panel closes |

## 9. CSS parts & custom properties

**Parts**
- `::part(root)` — the accordion container `<div>`

**Custom properties**
| Property | Default token | Description |
|----------|--------------|-------------|
| `--mj-accordion-border` | `--mj-color-border` | Border color for panel dividers and outer border |
| `--mj-accordion-radius` | `--mj-radius-md` | Outer container corner radius |
| `--mj-accordion-gap` | `0` | Gap between panels when `bordered` is false |

## 10. States

- **default** — all panels in their initial open/closed state.
- **disabled** — all panels non-interactive; triggers and headers are `aria-disabled="true"`.
- **single-open** — at most one panel open; opening a second collapses the first with an animated transition.
- **multi-open** — any combination of panels open simultaneously.

## 11. Behavior & interactions

On `connectedCallback`, the accordion queries its slotted `<mj-disclosure>`
children and attaches a `mj-disclosure-open` listener to each. In single-open
mode, this listener closes all other panels by calling `panel.open = false` on
each sibling. The accordion does not manage the animation itself — each
`<mj-disclosure>` handles its own height transition.

When `disabled` changes, the new value is propagated to all child disclosures'
`disabled` property. When new `<mj-disclosure>` children are slotted in
dynamically, a `MutationObserver` on the default slot re-runs the child scan and
attaches listeners.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Tab` | Move focus to the next disclosure trigger in reading order |
| `Shift+Tab` | Move focus to the previous disclosure trigger |
| `Enter` / `Space` | Toggle the focused disclosure panel open/closed |
| `Home` | Move focus to the first disclosure trigger (within the accordion) |
| `End` | Move focus to the last disclosure trigger (within the accordion) |
| `Arrow Down` | Move focus to the next disclosure trigger |
| `Arrow Up` | Move focus to the previous disclosure trigger |

## 13. Accessibility

- The accordion root has no ARIA role; individual `<mj-disclosure>` elements
  expose the `button` + `region` pattern (see `disclosure.md`).
- The accordion manages roving focus among its child triggers via the arrow-key
  handler so users can traverse panels without excess Tab stops.
- When a panel closes in single-open mode, focus is not moved; the trigger that
  was just activated retains focus.
- When `disabled`, all child triggers have `aria-disabled="true"` and are
  removed from the tab sequence.
- Home/End key support follows the optional APG accordion keyboard pattern.

## 14. Form participation

N/A — `<mj-accordion>` is a disclosure group and does not participate in forms.

## 15. Internationalization & RTL

No localizable strings are owned by `<mj-accordion>`. Panel labels are supplied
by slotted `<mj-disclosure>` children. Border and layout use logical properties
for RTL compatibility.

## 16. Progressive enhancement / SSR

The server renders `<mj-disclosure>` children as native `<details>`/`<summary>`
elements. Before upgrade the browser provides built-in disclosure behavior. After
upgrade the accordion coordinates state and adds keyboard navigation. The
transition is seamless because the content is already visible/hidden via native
`<details>`.

## 17. Dependencies

- Section 6: Registry + base element helper; design-token stylesheet; focus
  utilities (roving tabindex).
- `<mj-disclosure>` — required child component; see `disclosure.md`.

## 18. Edge cases & error handling

- **Non-`<mj-disclosure>` children** — ignored by the accordion's state management;
  a console warning is emitted in development mode.
- **All panels closed in single-open mode** — allowed; the accordion does not
  force one panel open.
- **`allow-multiple` toggled at runtime** — when switched to single-open with
  multiple panels open, all panels beyond the first open one are closed.
- **Dynamically added `<mj-disclosure>`** — picked up by the `MutationObserver`
  and registered for state coordination.
- **Deeply nested accordions** — inner accordions manage only their own children;
  arrow-key navigation does not cross accordion boundaries.

## 19. Acceptance criteria

- [ ] Single-open mode: opening panel B while panel A is open closes panel A.
- [ ] Multi-open mode: any number of panels may be open simultaneously.
- [ ] `Home`/`End` move focus to the first/last trigger.
- [ ] `Arrow Down`/`Up` cycle focus among disclosure triggers.
- [ ] `disabled` propagates to all child `<mj-disclosure>` elements.
- [ ] `mj-accordion-open` and `mj-accordion-close` events fire with correct panel reference and index.
- [ ] SSR upgrade from `<details>/<summary>` preserves open/closed state.
- [ ] `allow-multiple` toggled to false with multiple panels open closes all but the first.
- [ ] Automated accessibility check passes with no violations.

## 20. Open questions

- Should the accordion support a `default-open` attribute to specify which panel index is open on load (e.g. `default-open="0"`)?
- Should `Home`/`End` be limited to the accordion scope or operate within the full page Tab order? (APG marks them as optional.)
