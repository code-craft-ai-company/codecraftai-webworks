# Empty State Spec

- **Tag:** `<mj-empty-state>`
- **Class / file:** `MjEmptyState` / `mjemptystate.js`
- **Category:** Layout & content containers (§5.5)
- **Primary or Variant:** Primary
- **Synonyms covered:** Placeholder
- **Phase:** P2
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-empty-state>` displays a meaningful no-content message when a list, table,
or feed contains no items. It provides a consistent, accessible structure for the
icon/illustration, heading, description, and optional primary action that guides
the user toward the next step. It is informative and actionable, not merely
decorative.

## 2. When to use / when not to use

**Use** inside a data table, list, search result area, or feed when there are no
items to display — empty inbox, no search results, first-time user with no data.
**Do not use** for loading states — use `<mj-skeleton>`. **Do not use** for
error states — use `<mj-alert>` with severity `"error"`. **Do not use** as a
full-page splash screen — use `<mj-hero>` for landing page content.

## 3. Anatomy

- **root** — a `<div>` container; surfaced as `::part(root)`.
- **illustration** — the optional icon or illustration region (slot `illustration`);
  surfaced as `::part(illustration)`.
- **heading** — the primary message heading (from `heading` attribute or slot
  `heading`); surfaced as `::part(heading)`.
- **description** — supporting explanatory text (slot `description`); surfaced
  as `::part(description)`.
- **actions** — primary and secondary action buttons (slot `actions`); surfaced
  as `::part(actions)`.

## 4. Variants & modes

| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Default | — | Centered layout; icon above heading |
| Compact | `compact` boolean | Reduced padding and icon size; for use inside small containers |
| No illustration | `show-illustration="false"` | Illustration slot and wrapper hidden |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `heading` | string | `""` | Yes | Plain-text empty-state message heading |
| `heading-level` | `"2"` \| `"3"` \| `"4"` | `"3"` | Yes | Heading element level rendered from the `heading` attribute |
| `compact` | boolean | `false` | Yes | Renders a smaller, denser layout |
| `show-illustration` | boolean | `true` | Yes | Controls visibility of the illustration region |

## 6. Properties

No complex properties beyond reflected attributes.

| Property | Type | Description |
|----------|------|-------------|
| `hasActions` | boolean (readonly) | `true` when the `actions` slot has slotted content |

## 7. Slots

| Slot | Description |
|------|-------------|
| `illustration` | An SVG icon, illustration image, or other visual element |
| `heading` | Rich heading markup; replaces the `heading` attribute text |
| `description` | One or two sentences explaining why the state is empty and what the user can do |
| `actions` | One or two buttons for primary and secondary actions |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| — | — | — | — | No component-specific events; action events bubble from slotted buttons |

## 9. CSS parts & custom properties

**Parts**
- `::part(root)` — the outer container
- `::part(illustration)` — the illustration wrapper
- `::part(heading)` — the heading element
- `::part(description)` — the description wrapper
- `::part(actions)` — the actions row

**Custom properties**
| Property | Default token | Description |
|----------|--------------|-------------|
| `--mj-empty-state-padding` | `--mj-space-8` | Internal padding around content |
| `--mj-empty-state-max-width` | `24rem` | Maximum width of the content block |
| `--mj-empty-state-illustration-size` | `5rem` | Width/height of the illustration region |
| `--mj-empty-state-gap` | `--mj-space-4` | Vertical gap between illustration, heading, description, actions |
| `--mj-empty-state-heading-color` | `--mj-color-text-primary` | Heading color |
| `--mj-empty-state-description-color` | `--mj-color-text-secondary` | Description color |

## 10. States

- **default** — all regions displayed with the configured illustration and text.
- **compact** — reduced padding, illustration size, and gap.
- **no-illustration** — illustration region hidden; heading is the topmost element.
- **no-actions** — actions slot hidden when empty.

## 11. Behavior & interactions

`<mj-empty-state>` is purely presentational. It detects whether the `actions`
slot has content via a `slotchange` listener and conditionally hides the actions
region to avoid rendering an empty spacer. Similarly, the `illustration` region is
only rendered when `show-illustration` is true and the slot has content.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Tab` | Move focus through slotted action buttons |
| `Enter` / `Space` | Activate the focused action button |

## 13. Accessibility

- The root `<div>` has no ARIA role; the empty state is read in document order.
- The heading element (e.g., `<h3>`) provides context for screen readers.
- The illustration slot must contain either a meaningful `<img alt="...">` or an
  `aria-hidden="true"` decorative element; the component does not modify `alt`
  text.
- Action buttons in the `actions` slot must have clear, specific labels (e.g.,
  "Create your first project", not just "Create").
- No live-region is used; the empty state is static content.

## 14. Form participation

N/A — `<mj-empty-state>` is a display component and does not participate in forms.

## 15. Internationalization & RTL

All spacing uses logical CSS properties. The `heading` attribute string and slot
text are supplied by the author in the correct locale. No Intl formatting is
performed by the component.

## 16. Progressive enhancement / SSR

The server renders the empty state as a plain `<div>` with a heading, paragraph,
and optional button. After upgrade the component applies token-backed spacing and
`::part()` hooks. No content changes; the empty state is equally legible before
and after upgrade.

## 17. Dependencies

- Section 6: Registry + base element helper; design-token stylesheet.
- Typically used inside `<mj-feed>` (empty slot), `<mj-data-table>`, or any
  container that conditionally shows it.

## 18. Edge cases & error handling

- **No heading provided** — the heading element is omitted; a console warning is
  emitted in development mode because an empty state without a heading provides
  no context.
- **No description and no actions** — the component renders only the illustration
  and heading; it is still useful, though less actionable.
- **Both `heading` attribute and `heading` slot provided** — the slot takes
  precedence; the attribute text is ignored.
- **`compact` + large illustration** — authors should supply a smaller illustration
  for compact contexts; the `--mj-empty-state-illustration-size` token shrinks
  the region but does not scale vector content.

## 19. Acceptance criteria

- [ ] `heading` attribute renders as the correct heading level element.
- [ ] `illustration` slot content is rendered above the heading.
- [ ] `description` slot content is rendered below the heading.
- [ ] `actions` slot is hidden when empty; visible and positioned when content is slotted.
- [ ] `compact` reduces padding, illustration size, and gap.
- [ ] `show-illustration="false"` hides the illustration region.
- [ ] Decorative illustration with `aria-hidden="true"` is not announced by screen readers.
- [ ] Action buttons are reachable via Tab; their labels are clear and specific.
- [ ] Automated accessibility check passes with no violations.
- [ ] SSR upgrade produces no visible layout shift.

## 20. Open questions

- Should `<mj-empty-state>` accept an `icon` attribute (icon identifier from the
  design system icon set) as a shorthand for slotting an icon into the illustration slot?
- Should the component expose a `context` attribute (e.g., `"search"`, `"first-use"`,
  `"error"`) to select from pre-built illustration + copy combinations from the
  design system?
