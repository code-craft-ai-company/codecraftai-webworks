# Web Component Development Plan

## 1. Purpose & Scope

This plan defines the requirements for a library of reusable web components served
from `automojo-webworks`. Components are authored as native **Custom Elements**
(Web Components) and live in:

- Scripts: `source/packages/automojo/webworks/static/javascript/components`
- Styles:  `source/packages/automojo/webworks/static/styles`

The catalog is intentionally large and contains many synonymous entries. A core
goal of this plan is to **consolidate synonyms onto a single implementation** so
the library stays small, consistent, and maintainable. Each named component below
is mapped either to a primary component or declared a distinct component.

"Implement to the best extent possible" is interpreted as: every component must
meet the **universal requirements** in Section 3, and the **category** and
**per-component** requirements that follow. Where a browser-native element or an
existing `automojo-*` package already provides the capability, the component must
wrap/reuse it rather than reimplement it.

## 2. Goals & Non-Goals

**Goals**
- A coherent, accessible, themeable component set usable from server-rendered
  `webworks` templates with zero build step required for consumers.
- Progressive enhancement: components degrade to usable native HTML when scripting
  is unavailable, wherever the underlying semantics allow it.
- Predictable API surface: consistent attribute, property, event, and slot naming.

**Non-Goals**
- A client-side SPA framework. Components are standalone and framework-agnostic.
- Bundling a charting/mapping engine in-house — visualization components wrap a
  pluggable rendering adapter (see Section 5.9).

## 3. Universal Requirements (apply to every component)

Every component in the catalog MUST satisfy the following before it is considered
complete.

### 3.1 Custom Element standard
- Authored as an autonomous custom element extending `HTMLElement` (or a
  `customized built-in` only where it materially helps progressive enhancement).
- Registered through a shared registry helper; registration is idempotent and
  guarded so double-loading the script does not throw.
- Tag names are namespaced with the `mj-` prefix (e.g. `<mj-select>`,
  `<mj-modal>`). One class per file; the file is named after the class in all
  lowercase with no underscores, consistent with repository naming conventions.
- Implements the relevant lifecycle callbacks (`connectedCallback`,
  `disconnectedCallback`, `attributeChangedCallback`, `adoptedCallback`) and
  cleans up every listener, timer, and observer on disconnect.

### 3.2 Shadow DOM & styling
- Uses Shadow DOM (`mode: "open"`) for encapsulation unless form participation or
  light-DOM composition makes that impractical, in which case the exception is
  documented in the component header.
- Styles are delivered via adoptable stylesheets / `<template>` and never via
  per-instance inline `<style>` duplication.
- Exposes a documented theming surface: CSS custom properties for color, spacing,
  radius, typography, and `::part()` hooks for structural sub-elements.
- No hard-coded colors, fonts, or sizes — all visual values resolve from design
  tokens (Section 3.7).

### 3.3 Accessibility (WCAG 2.2 AA)
- Correct ARIA role, states, and properties for the component pattern, matching
  the WAI-ARIA Authoring Practices Guide.
- Full keyboard operability: every pointer interaction has a keyboard equivalent;
  focus order is logical; focus is visible.
- Focus management: overlays trap focus and restore it on close; composite
  widgets implement roving tabindex or `aria-activedescendant`.
- Screen-reader verified names/descriptions; live regions used for async status.
- Respects `prefers-reduced-motion`, `prefers-color-scheme`, and forced-colors.
- Minimum target size and contrast requirements met.

### 3.4 Events & API
- Emits `CustomEvent`s with a consistent, namespaced naming scheme; events are
  documented with their `detail` payload, bubbling, and cancelability.
- Public state is reflected between attributes and properties per the standard
  conventions (boolean attributes presence-based; complex state via properties).
- Components are configurable via attributes for static/server-rendered use and
  via properties for scripted use; both paths produce identical behavior.
- No global state; no reliance on a specific outer framework.

### 3.5 Form participation
- Any input-like component is a **form-associated custom element** using
  `ElementInternals` — it contributes a value, participates in `FormData`, supports
  `name`, `disabled`, `required`, validation, and form reset/restore.
- Constraint validation is exposed (`validity`, `validationMessage`,
  `checkValidity`, `reportValidity`); custom validity messages are localizable.

### 3.6 Progressive enhancement & SSR
- Renders meaningful, styled content from server markup before the script loads;
  upgrades in place without layout shift.
- Where a native element exists (`<select>`, `<input>`, `<dialog>`, `<details>`),
  the component enhances it or mirrors its semantics so non-JS fallback works.

### 3.7 Theming & design tokens
- A single tokens stylesheet defines color, spacing, typography, elevation,
  radius, motion, and z-index layers; components consume only tokens.
- Light and dark themes supported via tokens; high-contrast supported via
  forced-colors styling.

### 3.8 Internationalization
- All user-facing strings are overridable via attributes/properties or a shared
  localization hook; no hard-coded English in logic.
- Full RTL support driven by the `dir` attribute.
- Locale-aware formatting (numbers, dates, currency, collation) uses the platform
  `Intl` APIs.

### 3.9 Performance
- Lazy-initialize expensive work; defer rendering off-screen content.
- Long collections must virtualize (see list/table categories).
- No layout thrash; batch DOM writes; use `ResizeObserver`/`IntersectionObserver`
  rather than polling.
- Each component ships as an independently importable module for tree-shaking;
  shared logic lives in common utility modules, reused not duplicated.

### 3.10 Testing
- Unit/behavior tests for rendering, attribute/property reflection, events, and
  keyboard interaction.
- Automated accessibility checks (axe-style) in the component test suite.
- Tests live under the matching test hierarchy and run via the repository
  `testbase` singlehost flow.

### 3.11 Documentation
- Each component ships a doc entry: purpose, anatomy, attributes, properties,
  events, slots, CSS parts/custom properties, accessibility notes, and examples.
- A living gallery/demo page renders every component and every documented state.

## 4. Synonym Consolidation Policy

Many catalog entries are synonyms or thin variants. The catalog below marks each
group with a **Primary** component; synonyms are satisfied by configuration
(attributes, slots, variants) of the primary rather than separate code. Variant
names that imply a meaningfully different interaction get their own component.

## 5. Component Catalog

Format per entry: **Name** *(synonyms)* — purpose. *Must:* the requirements that
go beyond the universal set in Section 3.

### 5.1 Selection & dropdown-style controls

*Category shared requirements:* `combobox`/`listbox`/`option` ARIA pattern;
type-ahead; keyboard navigation (arrows, Home/End, Esc, Enter); single vs. multiple
selection modes; option grouping; disabled options; empty/no-results state;
form-associated value; popup positioning that flips/shifts within the viewport.

- **Select** *(Dropdown, Select box, Dropdown list, Dropdown listbox)* — Primary
  single-choice control. *Must:* enhance native `<select>`; support option groups,
  icons, descriptions, and a placeholder; closed state shows the chosen label.
- **Listbox** *(Multi-select listbox)* — always-visible options list. *Must:*
  single and multiple modes; multi mode supports shift/ctrl range selection.
- **Combobox** *(Autocomplete, Typeahead, Searchable select, Filterable select)* —
  text input bound to a filtered option popup. *Must:* async option sources with
  loading/error states; debounced filtering; free-text vs. must-match modes;
  highlight of matched substrings.
- **Cascading select** *(Dependent dropdown)* — chained selects where each level's
  options depend on the prior selection. *Must:* per-level loading state; reset of
  downstream levels when an upstream value changes.
- **Option picker / Picker** — generic single/multi option chooser; satisfied by
  Select/Listbox variants.
- **Radio group** — mutually exclusive choice set. *Must:* `radiogroup`/`radio`
  roles; roving tabindex; one tab stop; required validation on the group.
- **Checkbox group** — multiple independent choices. *Must:* group labelling;
  optional "select all" with indeterminate parent state; aggregated value.
- **Segmented control** *(Toggle group, Button group)* — Primary inline choice/
  action cluster. *Must:* single-select (radio semantics) and multi-select
  (toggle) modes; action-only mode for `Button group`.
- **Split button** *(Split action button)* — default action plus an attached menu
  of alternates. *Must:* two distinct, separately labelled controls; menu uses the
  Menu pattern.
- **Menu button** *(Kebab/Meatball/Overflow menu button)* — button that opens an
  actions menu. *Must:* `aria-haspopup`; menu follows the `menu`/`menuitem`
  pattern; satisfied by Menu button + Menu primitives.
- **Context menu / Command menu** — see Section 5.7 (overlays).
- **Color picker** — choose a color. *Must:* enhance `<input type=color>`;
  optional swatches, alpha, and hex/rgb/hsl input; eyedropper where supported.
- **Date picker / Time picker / Date-time picker / Range picker / Calendar
  picker** — Primary **DatePicker** with mode attribute (`date`, `time`,
  `datetime`, `range`). *Must:* calendar grid pattern; min/max/disabled dates;
  locale-aware; keyboard date navigation; text-entry fallback.
- **File picker** *(Image picker, Upload button)* — choose files. *Must:* enhance
  `<input type=file>`; drag-and-drop; type/size constraints; preview for images.
- **Emoji picker / Icon picker / Font picker** — searchable asset grids. *Must:*
  virtualized grid; search; recent/favorites; category navigation.
- **Language picker / Country/region picker** — specialized Combobox over a
  locale dataset. *Must:* flag/native-name display; search by name or code.
- **Tag picker** *(People picker)* — Combobox that yields multiple chip values.
  *Must:* token rendering, removal, max-count, async suggestions.
- **Tree selector** *(Hierarchical selector)* — selection within a tree. *Must:*
  `tree` pattern; expand/collapse; single/multi/checkbox selection with
  parent/child tri-state.
- **Transfer list** *(Dual listbox)* — move items between two lists. *Must:* two
  Listboxes plus move controls; keyboard move; filter per side.

### 5.2 Text & data-entry controls

*Category shared requirements:* form-associated; label/help/error wiring via
`aria-describedby`/`aria-invalid`; placeholder ≠ label; live validation policy
(on blur / on submit); clearable affordance where useful.

- **Text field** *(Text input)* — Primary single-line text. *Must:* enhance
  `<input>`; prefix/suffix slots; label, help, error, character counter.
- **Search input / Search bar** — text field tuned for search. *Must:* search
  role semantics; clear button; optional suggestions (Combobox); submit on Enter.
- **Password field** — masked entry. *Must:* show/hide toggle; caps-lock hint;
  optional strength meter; never autocompletes against the wrong field.
- **Email / URL / Telephone field** — typed text fields. *Must:* correct
  `type`/`inputmode`/`autocomplete`; format validation with localized messages.
- **Number input / Currency input / Percentage input** — Primary **NumberField**
  with format mode. *Must:* min/max/step; locale-aware grouping and symbols;
  spinner controls; clamp and parse on blur.
- **Textarea** — multi-line text. *Must:* enhance `<textarea>`; optional
  auto-grow; min/max rows; counter.
- **Rich text editor** — formatted text editing. *Must:* accessible toolbar;
  semantic HTML output (sanitized); keyboard shortcuts; paste cleanup.
- **Markdown editor** — markdown authoring. *Must:* edit/preview split; toolbar
  maps to markdown syntax; output is raw markdown.
- **Code editor** — code authoring. *Must:* pluggable syntax engine; line numbers;
  monospaced; tab handling that does not trap keyboard focus.
- **Inline editable text** *(Contenteditable region)* — click/enter to edit text
  in place. *Must:* explicit edit/commit/cancel; Esc cancels; Enter commits;
  emits change only on commit.
- **Masked input** — pattern-constrained text. *Must:* configurable mask; caret
  handling; raw vs. formatted value both exposed.
- **Token input** *(Tag input, Chip input)* — Primary **TokenInput** producing a
  list of chips. *Must:* add via Enter/comma/paste; remove via Backspace/click;
  duplicate and max-count rules; optional validation per token.
- **OTP / verification code input** — fixed-length segmented code entry. *Must:*
  one logical value; auto-advance/backspace; paste fills all cells; numeric
  inputmode.
- **Slider / Range slider** — Primary **Slider** with single and dual-thumb
  modes. *Must:* `slider` pattern; arrow/Home/End/PageUp-Down; step; tick marks;
  value label.
- **Stepper / Spinner input** — increment/decrement a value. *Must:* satisfied by
  NumberField spinner mode; explicit +/- buttons with hold-to-repeat.
- **Rating input** *(Star rating)* — choose a rating. *Must:* radio-group
  semantics; half-step option; read-only display mode; keyboard selectable.
- **Captcha** — human-verification field. *Must:* pluggable provider adapter;
  accessible alternative; exposes a form-associated token; never blocks keyboard
  users without an alternative.
- **Hidden input** — non-visual value carrier. *Must:* satisfied by native
  `<input type=hidden>`; provided only as a convenience wrapper.
- **Form / Fieldset / Legend / Label / Help text / Error message / Validation
  summary / Character counter / Word counter** — form-structure primitives.
  *Must:* Form coordinates submit and aggregate validity; Fieldset/Legend group
  related controls; Label/Help/Error associate by id; Validation summary lists
  errors with in-page links to each invalid control; counters update via live
  region politely.

### 5.3 Buttons & actions

*Category shared requirements:* Primary **Button** with `variant`
(`primary`/`secondary`/`tertiary`/`link`), `size`, `icon`-only, `loading`,
`disabled`, and `type` (`button`/`submit`/`reset`) attributes — most named
"buttons" below are variants, not separate components. All buttons: real
`<button>` semantics, keyboard activation, focus-visible, min target size, busy
state announced.

- **Button** and variants — **Primary/Secondary/Tertiary button**, **Link
  button**, **Icon button**, **Submit/Reset/Cancel/Close/Back/Next/Previous
  button**, **Toolbar button** — all satisfied by Button configuration. *Must:*
  Close/Cancel buttons carry an accessible name even when icon-only; Link button
  is a button styled as a link, never an anchor used as a button.
- **Floating action button** — prominent fixed-position primary action. *Must:*
  fixed placement that avoids overlapping content; reachable in tab order.
- **Toggle button** — on/off action. *Must:* `aria-pressed`; distinct from a
  Checkbox (action, not form value) — documented when to use which.
- **Disclosure button / Expand-collapse button** — shows/hides related content.
  *Must:* `aria-expanded` + `aria-controls`; pairs with Disclosure (5.5).
- **Copy button** — copies text to clipboard. *Must:* uses async Clipboard API;
  transient "copied" confirmation via live region; failure feedback.
- **Download / Upload / Share button** — *Must:* Download wraps an anchor with
  `download`; Upload pairs with File picker; Share uses Web Share API with a
  fallback menu.
- **Like/favorite button / Bookmark button** — toggle with persisted state.
  *Must:* Toggle button semantics; optimistic UI with rollback on failure;
  count display optional.
- **Overflow / Kebab / Meatball / Split action button** — see Menu button and
  Split button in 5.1; listed here as action entry points.

### 5.4 Navigation components

*Category shared requirements:* use `<nav>` landmarks with distinct accessible
names; current location marked with `aria-current`; keyboard-operable; mobile/
responsive collapse behavior defined.

- **Link** — navigation hyperlink. *Must:* real `<a>`; external/visited cues;
  never a div with a click handler.
- **Navigation bar** *(Top app bar, Header)* — Primary **AppBar** for top-level
  navigation/branding/actions. *Must:* responsive collapse; sticky option;
  landmark roles.
- **Sidebar / Side navigation / Drawer navigation** — Primary **SideNav** with
  `mode` (`static`/`collapsible`/`overlay-drawer`). *Must:* overlay mode traps
  focus and is dismissible; collapsible mode persists state.
- **Breadcrumb** — hierarchy trail. *Must:* ordered list in a labelled `nav`;
  last item `aria-current=page`; truncation/overflow for long trails.
- **Tabs / Tab list / Tab panel** — Primary **Tabs** composite. *Must:* `tablist`/
  `tab`/`tabpanel` roles; arrow-key navigation; manual vs. automatic activation;
  panels lazy-rendered.
- **Pills** — pill-styled tabs or filters; satisfied by Tabs/Segmented variants.
- **Stepper / Wizard** — Primary **Stepper (navigation)** showing ordered steps.
  *Must:* current/complete/error step states; linear vs. non-linear navigation;
  distinct from the numeric Stepper in 5.2 (different tag).
- **Pagination / Pager** — page navigation for results. *Must:* labelled nav;
  prev/next + page links or compact pager; current page `aria-current`; page-size
  control optional.
- **Table of contents / Anchor links** — in-page section navigation. *Must:*
  scroll-spy highlights the active section; smooth scroll respects reduced motion.
- **Skip link** — bypass to main content. *Must:* first focusable element;
  visible on focus; targets the main landmark.
- **Footer navigation** — grouped secondary links in a `contentinfo` landmark.
- **Mega menu / Dropdown menu / Flyout menu** — Primary **Menu** with multi-column
  and nested submenu support. *Must:* `menu`/`menuitem` pattern; keyboard
  traversal across columns and submenus; hover-intent delay; dismiss on Esc/blur.
- **Tree navigation** — navigable tree of links. *Must:* `tree` pattern; expand/
  collapse; current page marked.
- **Sitemap** — full structured link index; static, satisfied by nested lists.
- **Command palette** — see 5.7 (overlays).

### 5.5 Layout & content containers

*Category shared requirements:* layout components are structural and largely
presentational; they expose slots for content and resize responsively; they add
ARIA only where they convey grouping/landmarks.

- **Card** *(Data card)* — grouped content surface. *Must:* media/header/body/
  footer slots; optional whole-card link/action with a single accessible target.
- **Panel / Section / Container** — generic surfaces/wrappers. *Must:* satisfied
  by a Surface primitive with elevation/padding variants; Section maps to
  `<section>` with a heading.
- **Grid / Stack / Spacer / Aspect-ratio box** — layout primitives. *Must:*
  token-based spacing; Grid exposes columns/gap; Stack exposes direction/gap;
  Aspect-ratio box uses `aspect-ratio`; presentational only.
- **Sidebar / Drawer** — see SideNav (5.4) and Drawer (5.7) for the overlay form.
- **Accordion / Disclosure / Details-summary / Expander / Collapse panel** —
  Primary **Accordion** (group) built on **Disclosure** (single). *Must:*
  enhance native `<details>/<summary>`; single- or multi-open mode; animated
  height respecting reduced motion; `aria-expanded`/`aria-controls`.
- **Split pane / Resizable pane** — adjustable adjacent regions. *Must:* keyboard-
  resizable separator (`separator` role); min/max sizes; persisted ratio.
- **Scroll area** — styled scroll container. *Must:* native scrolling preserved;
  keyboard scroll; custom scrollbars never remove accessibility.
- **Carousel / Gallery** — Primary **Carousel**. *Must:* APG carousel pattern;
  prev/next + slide pickers; auto-rotation pauses on hover/focus and is
  user-stoppable; not focus-trapping.
- **Masonry grid / Feed** — Primary **Feed** (`feed` role for streaming content)
  and a Masonry layout variant of Grid. *Must:* Feed supports incremental load
  and article semantics.
- **Timeline** — chronological list. *Must:* ordered list semantics; satisfied
  here and reused by 5.8/5.10.
- **Media object** — image/icon beside text block. *Must:* simple layout
  primitive with media + content slots.
- **Hero section** — prominent intro banner. *Must:* heading-led; background
  media must not reduce text contrast.
- **Empty state / Placeholder** — no-content messaging. *Must:* icon/illustration,
  message, and optional primary action; informative, not just decorative.
- **Skeleton loader / Skeleton screen** — loading placeholder. *Must:* marked
  `aria-hidden` with an accessible "loading" status elsewhere; respects reduced
  motion; matches the real content's layout to avoid shift.
- **Divider / Separator** — visual/semantic separation. *Must:* `separator` role
  when semantic, decorative otherwise; horizontal and vertical.

### 5.6 Feedback & status components

*Category shared requirements:* status is conveyed by more than color; severity
is mapped to consistent tokens/icons; transient messages use live regions with
appropriate politeness.

- **Alert / Banner / Inline message / Callout** — Primary **Alert** with
  `severity` (`info`/`success`/`warning`/`error`) and placement variants. *Must:*
  `alert` role for urgent, `status` for non-urgent; optional dismiss; optional
  action slot. Banner is a page-width Alert variant; Callout is an inline
  emphasis variant.
- **Notification / Toast / Snackbar** — Primary **Toast** managed by a **Toast
  region**. *Must:* non-modal, auto-dismiss with pause-on-hover/focus; queueing;
  assertive vs. polite by severity; reachable by keyboard; never the only channel
  for critical info.
- **Status message / Error/Warning/Success/Info message** — satisfied by Alert
  severity variants and form Error message (5.2).
- **Progress bar / Progress ring** — Primary **Progress** with `bar`/`ring`
  variants. *Must:* `progressbar` role; determinate and indeterminate; value text;
  reduced-motion safe.
- **Spinner / Loading indicator** — indeterminate activity. *Must:* accessible
  loading status; respects reduced motion; satisfied by Progress indeterminate.
- **Badge / Counter / Status dot** — Primary **Badge** with `count`/`dot`/`status`
  variants. *Must:* count badge announces its meaning ("3 unread"); dot has a
  text alternative; numeric overflow ("99+").
- **Pill / Chip / Tag** — Primary **Chip** with `static`/`removable`/
  `selectable` variants. *Must:* removable chips have a labelled remove control;
  selectable chips expose pressed/selected state.
- **Presence indicator** — online/away/offline state. *Must:* Status-dot variant
  with a text alternative.
- **Tooltip** — pointer/focus-triggered hint. *Must:* `tooltip` role; shows on
  hover and focus; dismissible with Esc; never contains interactive content;
  not the only source of essential info.
- **Popover / Help bubble** — richer transient overlay; see Popover (5.7).

### 5.7 Dialogs, overlays & popups

*Category shared requirements:* a shared overlay engine handles positioning
(anchor, flip, shift, collision), stacking/z-index layering, light-dismiss,
scroll/focus management, and the top-layer (`popover` API / `<dialog>`) where
available. Modal surfaces trap focus and restore it on close; non-modal surfaces
do not trap focus.

- **Modal dialog / Non-modal dialog** — Primary **Dialog** built on native
  `<dialog>`. *Must:* `modal` and `non-modal` modes; labelled by its heading;
  Esc closes; focus trapped (modal) and restored; background inert when modal.
- **Alert dialog / Confirmation dialog / Prompt dialog** — Dialog variants.
  *Must:* `alertdialog` role; initial focus on the safest action; Confirmation
  resolves a boolean; Prompt collects and returns input.
- **Popover / Hovercard / Help bubble / Callout** — Primary **Popover**, anchored
  non-modal overlay that may contain interactive content. *Must:* trigger
  `aria-expanded`/`aria-haspopup`; light-dismiss; Esc closes; positioned by the
  overlay engine. Hovercard is a hover-intent Popover variant.
- **Tooltip** — see 5.6.
- **Drawer / Sheet / Bottom sheet** — Primary **Drawer** with edge attribute
  (`start`/`end`/`top`/`bottom`) — bottom edge is the Bottom sheet. *Must:* modal
  and non-modal modes; swipe-to-dismiss on touch; focus rules per mode.
- **Lightbox** — full-screen media viewer. *Must:* modal Dialog; prev/next
  navigation; zoom; caption; Esc closes.
- **Overlay / Backdrop** — dimming/blocking layer primitive. *Must:* reused by
  Dialog/Drawer/Lightbox; manages inertness and scroll lock; not used alone.
- **Toast region / Notification center / Notification inbox** — Primary **Toast
  region** for transient toasts plus a **Notification center** panel for
  persistent history. *Must:* center lists read/unread items, supports
  dismiss/mark-read, and is keyboard navigable.
- **Context menu** — pointer/keyboard-invoked actions menu. *Must:* Menu pattern;
  opens on right-click and on the context-menu key; positioned at the pointer;
  Esc closes; focus restored.
- **Dropdown menu / Flyout** — see Menu (5.4).
- **Command palette / Command menu** — searchable command launcher. *Must:* modal
  Dialog + Combobox; fuzzy search; keyboard-first; grouped results; recent
  commands; global shortcut to open.
- **Tour popover / Onboarding coach mark** — Primary **Tour** sequencing anchored
  Popovers. *Must:* step progress, next/back/skip, focus moved to each step,
  spotlight on the target, fully dismissible and resumable.

### 5.8 Tables, lists & structured data

*Category shared requirements:* correct semantics (`table`/`grid`/`treegrid`,
list roles); large datasets virtualize; sorting/filtering state announced;
selection model consistent across table and list.

- **Table** — static tabular data. *Must:* native `<table>` semantics; caption;
  scoped headers; responsive strategy for narrow viewports.
- **Data table / Grid / Sortable table / Filterable table / Spreadsheet grid** —
  Primary **DataTable**, an interactive `grid`. *Must:* column sort, filter,
  resize, reorder, pin; virtualized rows; cell/row keyboard navigation; editable
  cells optional (spreadsheet mode); server-side data adapter.
- **Tree grid** — hierarchical rows. *Must:* `treegrid` pattern; expand/collapse
  rows; same column features as DataTable.
- **List / Ordered list / Unordered list / Description list** — list primitives.
  *Must:* correct native list semantics; Description list for term/definition
  pairs.
- **Virtualized list / Infinite-scroll list** — large/streaming lists. *Must:*
  windowed rendering; stable scroll position; infinite scroll has a non-scroll
  "load more" alternative and announces new items.
- **Feed / Timeline** — see 5.5; reused here for activity data.
- **Kanban board** — columned card board. *Must:* accessible drag-and-drop with a
  keyboard alternative for moving cards; column WIP counts; live-region move
  announcements.
- **Calendar grid** — month/week/day grid. *Must:* `grid` semantics; keyboard date
  navigation; event rendering; shares the calendar engine with DatePicker.
- **Column picker / Sort control / Bulk action bar / Row selector** — DataTable
  companion controls. *Must:* Column picker toggles visibility/order; Sort control
  exposes current sort; Row selector supports row + select-all with indeterminate
  state; Bulk action bar appears on selection and announces the selected count.
- **Detail view / Master-detail view** — record display and split list+detail.
  *Must:* Master-detail keeps list and detail in sync; selection drives detail;
  responsive collapse to stacked navigation on narrow viewports.

### 5.9 Media & visualization components

*Category shared requirements:* media elements provide text alternatives,
captions, and full keyboard control; visualization components must not encode
information in color alone and must expose an accessible data alternative
(table/summary).

- **Image / Thumbnail / Figure** — Primary **Image** with lazy-load,
  `aspect-ratio` reservation, responsive `srcset`, and decode handling.
  *Must:* meaningful `alt` or explicit decorative marking; Figure adds caption.
- **Avatar** — user/entity image. *Must:* image, initials, and icon fallbacks;
  optional Presence indicator; accessible name.
- **Video player / Audio player / Media controls** — Primary **MediaPlayer** with
  `video`/`audio` modes and a shared **Media controls** part. *Must:* native
  media element under the hood; keyboard-operable controls; captions/subtitles/
  transcripts; volume, speed, scrubbing; respects reduced motion for autoplay.
- **Gallery / Carousel / Lightbox** — see 5.5 / 5.7.
- **Chart** *(Line/Bar/Pie/Donut/Area chart, Scatter plot, Heatmap)* — Primary
  **Chart** with a `type` attribute and a **pluggable rendering adapter** (no
  charting engine reimplemented in-house). *Must:* accessible data table
  alternative; series labels not color-only; responsive resize; tooltips
  keyboard-reachable.
- **Map / Interactive map** — Primary **Map** wrapping a pluggable map provider
  adapter. *Must:* keyboard pan/zoom; accessible markers with names; non-map
  fallback (list of locations).
- **Gauge / Meter** — single-value indicators. *Must:* `meter` role with min/max/
  optimum; thresholds not color-only; value text.
- **Sparkline** — compact inline trend. *Must:* decorative-or-described; paired
  with a text value.
- **Diagram / Graph viewer** — node/edge visualization. *Must:* pluggable layout
  adapter; pan/zoom with keyboard; selectable nodes with accessible names;
  textual structure alternative.

### 5.10 Application & productivity components

*Category shared requirements:* these are composite, app-shell-scale components
assembled from primitives in 5.1–5.9; they must reuse those primitives rather
than re-implement controls, and define responsive behavior for desktop and
narrow viewports.

- **Toolbar / Menubar / Command bar / Action bar / Ribbon** — Primary **Toolbar**
  (`toolbar` pattern, roving tabindex) and **Menubar** (`menubar` pattern).
  *Must:* overflow handling into a menu; grouped controls; Ribbon is a tabbed
  Toolbar variant; Command bar adds an inline search/command entry.
- **Status bar** — persistent bottom info strip. *Must:* `status` live region for
  dynamic items; non-essential, non-blocking.
- **App shell** *(Dock, Workspace switcher, Split view, Inspector panel,
  Properties panel)* — Primary **AppShell** layout composing AppBar, SideNav,
  content, and optional inspector. *Must:* landmark structure; persisted panel
  sizes/collapse; Split view uses Split pane; Inspector/Properties panels are
  contextual side panels; Workspace switcher is a Select/Menu over workspaces;
  Dock is a pinned launcher rail.
- **Search results** — result list with relevance metadata. *Must:* result count
  announced; empty state; pagination or infinite-scroll list; keyboard navigable.
- **Filter panel / Sort control / Faceted filter / Query builder** — Primary
  **FilterPanel** with **Faceted filter** facets and a **Query builder** for
  compound conditions. *Must:* applied filters shown as removable Chips; clear-all;
  Query builder supports nested AND/OR groups with full keyboard editing; current
  result count surfaced.
- **Drag-and-drop zone / Upload dropzone** — Primary **Dropzone**. *Must:* visible
  drag-over state; keyboard/click alternative (opens File picker); type/size
  validation; per-file progress and error states; announcements via live region.
- **File browser / Folder tree / Preview pane** — Primary **FileBrowser**
  composing Folder tree (Tree), a file DataTable/Grid, and a Preview pane.
  *Must:* keyboard navigation across panes; selection model; breadcrumb path;
  preview for common types with a safe fallback.
- **Activity feed / Comments thread** — Primary **Feed**-based activity stream and
  a threaded **Comments** component. *Must:* incremental load; relative
  timestamps with absolute on hover/focus; Comments supports nesting, reply,
  edit, delete, and the Mention input.
- **Mention input** — text entry with `@`/`#` mention triggers. *Must:* trigger
  detection; Combobox suggestion popup; tokens that carry an id and a display
  label; keyboard selection and removal.
- **Chat composer / Chat message / Notification inbox** — Primary **ChatComposer**
  (Textarea + Mention input + attachments + send) and **ChatMessage** (author,
  timestamp, content, status, reactions). *Must:* composer send via Enter with a
  configurable modifier for newline; messages expose delivery/read status; new
  messages announced politely; Notification inbox satisfied by Notification
  center (5.7).

### 5.11 Project-management & configuration-management charts

*Category shared requirements:* these are timeline/graph visualizations for
planning and SCM. Each MUST follow the visualization rules in 5.9 (no
color-only encoding, an accessible data-table/list alternative, responsive
resize, keyboard-reachable detail) and use the pluggable rendering and layout
adapters rather than a bespoke engine. All time-axis charts share a common
**time-axis utility** (zoom, pan, today marker, locale-aware tick labels) and a
common **milestone/marker model** (named markers with a date, type, and
optional phase band). Data is supplied through the Section 6 data-source
adapter so charts can render from VCS/CI APIs or static config.

- **Release branching & merge chart** *(Branch network, Commit history graph,
  Git graph)* — Primary **BranchGraph** rendering branches, commits, and merge
  edges over time. *Must:* lanes per branch with merge/branch-point edges;
  overlaid **milestone markers** and **key-date markers** (release, freeze,
  tag); **phase bands** spanning date ranges (e.g. development, stabilization,
  release); commit/branch nodes are selectable with accessible names and detail;
  collapse/expand of branch lanes; tag and release annotations.
- **Pipeline flow chart** *(Deployment pipeline, CI/CD pipeline, Build pipeline)*
  — Primary **PipelineChart** rendering ordered/parallel stages and their
  transitions. *Must:* per-stage status (pending/running/passed/failed/skipped)
  not color-only; gates/approvals and fan-out/fan-in edges; stage selection with
  logs/detail; live status updates announced via live region; horizontal and
  vertical layout.
- **Gantt chart** — task bars across a time axis. *Must:* task rows with
  start/end, dependency arrows, % complete, today marker, milestone diamonds,
  phase bands; keyboard navigation across tasks; collapsible task groups.
- **Roadmap chart** *(Now/Next/Later, release roadmap)* — initiatives grouped by
  timeframe or release. *Must:* swimlane rows, time or bucket columns, milestone
  markers, drag-free read mode with an editable variant flag.
- **Milestone timeline** — Primary **MilestoneTimeline**, a single-axis chart of
  key dates and phases. *Must:* reuses the shared milestone/marker model;
  past/current/upcoming states; phase bands; satisfied by reuse from the
  Timeline component (5.5) plus the time-axis utility.
- **Burndown / Burnup chart** — remaining vs. completed work over a sprint/
  release. *Must:* ideal vs. actual series, scope-change indicators, data-table
  alternative.
- **Cumulative flow diagram** — stacked work-state areas over time. *Must:*
  per-state bands, WIP/lead-time callouts, accessible series labels.
- **Velocity chart** — completed work per iteration. *Must:* per-sprint bars,
  committed vs. completed, rolling average.
- **Dependency graph** *(Critical path / PERT chart)* — node/edge graph of work
  items or modules. *Must:* reuse the Diagram/Graph viewer (5.9); highlight the
  critical path; cycle detection; selectable nodes with detail.
- **Workflow / state diagram** *(Swimlane diagram)* — states/transitions or
  cross-actor process flow. *Must:* reuse Diagram/Graph viewer; swimlane rows
  for actors; current-state highlight.
- **Release calendar** — releases/freezes/key dates on a calendar. *Must:*
  reuse Calendar grid (5.8); marker model for release/freeze/milestone entries.
- **Environment promotion chart** — artifact promotion across environments
  (dev → staging → prod). *Must:* environments as columns/stages, current
  deployed version per environment, promotion edges and approval gates;
  satisfied as a PipelineChart variant.
- **Build / release status board** — grid of pipelines/branches with current
  build and deploy status. *Must:* reuse DataTable (5.8) with status cells and
  live updates.

## 6. Cross-Component Foundations (build first)

These shared modules must be built before or alongside the components and reused
everywhere — no component reimplements them:

- Registry + base element helper (lifecycle, attribute/property reflection).
- Design-token stylesheet and theming utilities.
- Overlay/positioning engine (anchor, flip, shift, top-layer, stacking).
- Focus utilities (focus trap, focus restore, roving tabindex,
  `aria-activedescendant` helper).
- Form-association helper around `ElementInternals` and constraint validation.
- Live-region/announcement service.
- Localization/formatting hook over `Intl`.
- Collection/virtualization utility (shared by lists, tables, grids, pickers).
- Data-source adapter interface (async, paged, filterable) for Combobox,
  DataTable, Search results, etc.

## 7. Implementation Phasing

**Phase 0 — Foundations.** All modules in Section 6, tokens, the demo gallery
harness, and the component test scaffolding.

**Phase 1 — Core primitives (P0).** Button, Text field, Textarea, NumberField,
Select, Listbox, Combobox, Radio group, Checkbox group, Slider, Form/Fieldset/
Label/Help/Error, Link, Alert, Toast, Dialog, Tabs, Accordion, Card, Table,
Badge, Chip, Tooltip, Spinner/Progress, Image, Avatar.

**Phase 2 — Composite controls (P1).** DatePicker, Color/File pickers, TokenInput,
OTP input, Rating, Menu/Menu button/Context menu, Split button, Segmented
control, Popover, Drawer, Pagination, Breadcrumb, AppBar, SideNav, DataTable,
Virtualized list, Carousel, Empty/Skeleton states, Stepper (navigation), Wizard.

**Phase 3 — Advanced & app-scale (P2).** Tree selector, Transfer list, Cascading
select, Rich text / Markdown / Code editors, Tree grid, Kanban board, Calendar
grid, Command palette, FilterPanel/Faceted filter/Query builder, AppShell,
FileBrowser, MediaPlayer, Notification center, Tour/coach marks.

**Phase 4 — Visualization & productivity (P3).** Chart family, Map, Gauge/Meter,
Sparkline, Diagram/Graph viewer, Activity feed, Comments thread, Mention input,
ChatComposer/ChatMessage, Ribbon/Command bar, Inspector/Properties panels,
Masonry/Feed, Timeline, Lightbox. PM/SCM charts: BranchGraph, PipelineChart,
Gantt chart, Roadmap, MilestoneTimeline, Burndown/Burnup, Cumulative flow,
Velocity chart, Dependency/critical-path graph, Workflow/state diagram, Release
calendar, Environment promotion chart, Build/release status board (the time-axis
utility and milestone/marker model are built first, with the Section 6
visualization adapters).

Phasing rule: a component is not started until every primitive it composes is
complete and tested.

## 8. Definition of Done (per component)

A component is complete only when all of the following hold:

1. Meets every applicable universal requirement in Section 3.
2. Meets its category and per-component requirements in Section 5.
3. Reuses Section 6 foundations and existing `automojo-*` code rather than
   duplicating functionality.
4. Behavior, attribute/property reflection, event, and keyboard tests pass under
   the `testbase` singlehost flow.
5. Automated accessibility checks pass with no violations.
6. Documentation entry and demo-gallery states are published.
7. Server-rendered (no-JS) fallback verified where the pattern allows it.
8. Light, dark, high-contrast, and RTL rendering verified.
