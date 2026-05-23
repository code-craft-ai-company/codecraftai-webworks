# <Component Name> Spec

- **Tag:** `<mj-...>`
- **Class / file:** `<ClassName>` / `<classname>.js`
- **Category:** <catalog category>
- **Primary or Variant:** Primary | Variant of `<Primary>`
- **Synonyms covered:** <names from the catalog this spec satisfies>
- **Phase:** P0 | P1 | P2 | P3
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
One paragraph: what the component is and the problem it solves.

## 2. When to use / when not to use
Guidance and the nearest alternative components.

## 3. Anatomy
Structural sub-elements and their roles (header, body, trigger, popup, etc.).

## 4. Variants & modes
Each variant/mode, the attribute that selects it, and how behavior differs.

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|

## 6. Properties
Properties not mirrored 1:1 by attributes (complex/object state).
| Property | Type | Description |
|----------|------|-------------|

## 7. Slots
| Slot | Description |
|------|-------------|

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|

## 9. CSS parts & custom properties
`::part()` hooks and component-specific `--mj-*` custom properties.

## 10. States
default, hover, focus-visible, active, selected, disabled, readonly, invalid,
loading, empty, expanded — list those that apply and their visual/ARIA effect.

## 11. Behavior & interactions
Pointer interactions, async behavior, timing, positioning, edge transitions.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|

## 13. Accessibility
Roles, ARIA states/properties, focus management, live-region announcements,
target size, contrast notes specific to this component.

## 14. Form participation
For input-like components only: contributed value, `name`, validation rules,
custom validity messages, reset/restore behavior. Otherwise "N/A".

## 15. Internationalization & RTL
Localizable strings, locale-aware formatting, RTL-specific behavior.

## 16. Progressive enhancement / SSR
The no-JS fallback and how the component upgrades server markup.

## 17. Dependencies
Section 6 foundations and other components this one composes/reuses.

## 18. Edge cases & error handling
Empty data, overflow, long content, async failure, conflicting attributes.

## 19. Acceptance criteria
Checklist of testable conditions that define "done" for this component.

## 20. Open questions
Unresolved design/scope questions.
