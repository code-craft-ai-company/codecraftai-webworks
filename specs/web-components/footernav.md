# Footer Nav Spec

- **Tag:** `<mj-footer-nav>`
- **Class / file:** `MjFooterNav` / `mjfooternav.js`
- **Category:** Navigation components
- **Primary or Variant:** Primary
- **Synonyms covered:** Footer navigation, Footer links, Site footer nav, Footer link groups
- **Phase:** P2
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-footer-nav>` renders grouped secondary navigation links inside a
`<footer role="contentinfo">` landmark. It organizes links into named column
groups, handles responsive reflow from multi-column to stacked layout on narrow
viewports, and optionally renders legal/copyright text and social links.

## 2. When to use / when not to use
**Use** for the site-wide footer at the bottom of every page containing secondary
navigation (About, Legal, Help, Social) organized into logical groups.
**Do not use** for primary in-page navigation — use `<mj-app-bar>` or
`<mj-side-nav>`. **Do not use** for small contextual link groups within a card
or section — use a plain `<nav>` or `<mj-link>` elements.

## 3. Anatomy
- **Host / `<footer>`** — `<footer role="contentinfo">` landmark.
- **Column groups** (`::part(group)`) — each `<mj-footer-nav-group>` renders a
  `<nav aria-label>` column with a heading and list of links.
- **Group heading** (`::part(group-heading)`) — `<h3>` (or configured heading
  level) labelling each link group; also serves as the `<nav>`'s visible heading.
- **Link list** (`::part(link-list)`) — `<ul>` of `<mj-link>` elements per group.
- **Brand area** (`::part(brand)`) — optional top section for logo and tagline.
- **Legal bar** (`::part(legal)`) — bottom bar with copyright text and legal links.
- **Social links** (`::part(social)`) — optional icon-link cluster for social platforms.

## 4. Variants & modes
| Variant | Attribute | Behavior |
|---------|-----------|----------|
| Multi-column | _(default)_ | Groups render side-by-side; collapses to stacked on narrow viewports |
| Minimal | `variant="minimal"` | Single row of links; no group headings; suited to small footers |
| Centered | `variant="centered"` | All content center-aligned |
| Dark | `variant="dark"` | Dark background token; inverted text tokens (also achievable via CSS custom properties) |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `variant` | string | `"default"` | Yes | Layout variant: `default` \| `minimal` \| `centered` \| `dark` |
| `columns` | number | `0` | Yes | Number of columns for group layout; `0` = auto from group count |
| `heading-level` | number | `3` | Yes | HTML heading level for group headings (2–6) |
| `copyright` | string | `""` | Yes | Copyright text rendered in the legal bar; supports plain text |
| `nav-label` | string | `"Footer"` | Yes | `aria-label` for the host `<footer>`; used by the landmark |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `groups` | `Element[]` | Read-only list of slotted `<mj-footer-nav-group>` elements |

## 7. Slots
| Slot | Description |
|------|-------------|
| `brand` | Logo, wordmark, or tagline above the link columns |
| _(default)_ | `<mj-footer-nav-group>` elements forming the link columns |
| `social` | Social platform icon-links (e.g., `<mj-link>` with icon); rendered as a separate cluster |
| `legal` | Additional legal links or custom legal content placed beside the `copyright` text |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-footer-nav-navigate` | `{ href: string, group: string, originalEvent: MouseEvent }` | Yes | Yes | Fires when a footer link is activated; cancel to intercept |

## 9. CSS parts & custom properties
**Parts**
- `::part(root)` — inner layout container
- `::part(brand)` — brand slot wrapper
- `::part(columns)` — the multi-column grid for link groups
- `::part(group)` — each link group nav element
- `::part(group-heading)` — group title heading
- `::part(link-list)` — `<ul>` of links in a group
- `::part(legal)` — legal/copyright bar
- `::part(social)` — social links cluster

**Custom properties**
| Property | Default | Description |
|----------|---------|-------------|
| `--mj-footer-nav-bg` | `var(--mj-color-surface-subtle)` | Background of the footer |
| `--mj-footer-nav-color` | `var(--mj-color-text-muted)` | Default text color |
| `--mj-footer-nav-columns-gap` | `var(--mj-spacing-8)` | Gap between link-group columns |
| `--mj-footer-nav-padding` | `var(--mj-spacing-10) var(--mj-spacing-6)` | Outer padding |
| `--mj-footer-nav-heading-color` | `var(--mj-color-text-default)` | Group heading text color |
| `--mj-footer-nav-link-color` | `var(--mj-color-link)` | Link color |
| `--mj-footer-nav-legal-border` | `1px solid var(--mj-color-border-muted)` | Top border of the legal bar |
| `--mj-footer-nav-legal-font-size` | `var(--mj-font-size-xs)` | Font size of legal text |

## 10. States
- **default** — multi-column layout; all groups visible.
- **collapsed** — narrow viewport; groups stack vertically; `columns` reduces to 1.
- **hover** — footer links show hover color transition.
- **focus-visible** — footer links show focus rings.
- **dark** — inverted token set applied when `variant="dark"`.

## 11. Behavior & interactions
- Column layout is achieved via CSS Grid; `columns` attribute sets
  `grid-template-columns: repeat({columns}, 1fr)`. When `columns="0"`, it uses
  `repeat(auto-fit, minmax(160px, 1fr))`.
- On narrow viewports (below `--mj-footer-nav-collapse-breakpoint`), groups
  stack to a single column using `@container` queries or media queries.
- If a `<mj-footer-nav-group>` has `collapsible` set, the group heading acts as
  a `<button>` toggle (Disclosure pattern) with `aria-expanded`; useful for
  mobile stacked layouts.
- The `copyright` attribute value is rendered as text inside the legal bar,
  preceded by the `©` symbol and current year unless the full string already
  contains `©`.
- The `mj-footer-nav-navigate` event bubbles from any `<mj-link>` click within
  the component; the `group` detail is the accessible name of the group containing
  the clicked link.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` | Moves through brand links, group links, social links, legal links in DOM order |
| `Enter` | Activates the focused link or group toggle button |
| `Space` | Activates a group toggle button when `collapsible` is set on a group |
| `Shift+Tab` | Reverse focus order |

## 13. Accessibility
- The host renders as `<footer role="contentinfo">`; only one `contentinfo`
  landmark per page is expected.
- Each link group is wrapped in `<nav aria-label="{groupTitle}">` so screen
  readers can navigate between landmark regions within the footer.
- Group headings (`<h3>` by default, configurable via `heading-level`) are
  associated with their nav via `aria-labelledby` on the `<nav>` and are
  visually and semantically the group title.
- Collapsible groups: the toggle button has `aria-expanded` and `aria-controls`
  referencing the link list.
- Social icon links must have a text alternative (via `aria-label` on the link
  or `alt` on a contained image) — the component warns in development if a
  social link has no accessible name.
- Copyright text in the legal bar is plain text; no special ARIA role required.

## 14. Form participation
N/A — `<mj-footer-nav>` is a navigation landmark component.

## 15. Internationalization & RTL
- `nav-label` and group heading text are localizable by authors; no hard-coded
  English outside the `copyright` default format.
- Copyright year: derived from `new Date().getFullYear()` so it is always current.
- In RTL (`dir="rtl"`), the multi-column grid reverses column order via
  `direction: rtl`; the brand slot and social links also follow inline-end
  alignment.
- Group collapse arrow icons flip with `dir`.

## 16. Progressive enhancement / SSR
- Server renders the full footer HTML including all `<nav>` groups and links;
  the footer is fully functional without JS.
- On upgrade: collapsible group behavior is added; the `mj-footer-nav-navigate`
  event is wired; responsive collapse logic is activated.
- `variant="dark"` can be present in server markup; CSS-only dark token
  application works immediately via the adoptable stylesheet.

## 17. Dependencies
- Section 6: Registry + base element helper, design-token stylesheet,
  localization hook.
- `<mj-footer-nav-group>` — companion element for each column of links.
- `<mj-link>` — used for individual footer links within groups.

## 18. Edge cases & error handling
- **No groups slotted**: footer renders with brand and legal bar only; console
  warning emitted.
- **`columns` > actual group count**: no visual issue; extra grid tracks are
  empty.
- **Very long `copyright` string**: wraps naturally within the legal bar; no
  truncation.
- **Group with no links**: group heading renders alone; empty `<ul>` is present
  but invisible.
- **Multiple `<footer>` landmarks**: the component emits a console warning if
  another `<footer role="contentinfo">` or native `<footer>` at page level is
  detected when this component connects.

## 19. Acceptance criteria
- [ ] Renders `<footer role="contentinfo">` landmark.
- [ ] Each link group wrapped in `<nav aria-label="{groupTitle}">`.
- [ ] Multi-column layout at wide viewports; stacked at narrow viewports.
- [ ] `columns` attribute controls grid column count.
- [ ] Collapsible group toggle has `aria-expanded`/`aria-controls`.
- [ ] `copyright` attribute renders formatted text in the legal bar.
- [ ] Social links each have an accessible name; development warning if missing.
- [ ] `mj-footer-nav-navigate` fires with group and href detail on link click.
- [ ] `variant="dark"` applies dark token set.
- [ ] RTL: column order and alignment reverse correctly.
- [ ] SSR: all links functional before script loads.
- [ ] Automated axe checks pass with zero violations.

## 20. Open questions
- Should `<mj-footer-nav>` include a built-in language/region selector slot for
  global sites, or should that be left to the `legal` slot?
- Should the collapsible group behavior auto-activate below a breakpoint
  (responsive accordion) or remain as an explicit opt-in per group?
