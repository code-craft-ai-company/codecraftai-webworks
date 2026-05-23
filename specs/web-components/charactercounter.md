# Character Counter Spec

- **Tag:** `<mj-character-counter>`
- **Class / file:** `MjCharacterCounter` / `mjcharactercounter.js`
- **Category:** Text & data-entry controls — form-structure primitives
- **Primary or Variant:** Primary
- **Synonyms covered:** Character counter, Word counter, Character count, Word count
- **Phase:** P0
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-character-counter>` displays a live character or word count for a text input
or textarea, showing remaining capacity (or current count) relative to an optional
maximum. Updates are announced to screen readers via a polite live region so users
are informed of approaching limits without disruptive interruptions. It pairs with
`<mj-text-field>` and `<mj-textarea>` but can be associated with any `<input>` or
`<textarea>` by `id`.

## 2. When to use / when not to use
**Use** whenever a text field has a `maxlength` constraint that the user should be
aware of — post composer fields, bio inputs, SMS message fields, search queries
with token limits. **Use** word-count mode for rich text editors and textarea
inputs measured by words rather than characters.
**Do not use** if there is no meaningful limit and no value in showing the count.
**Do not use** on password fields (character count could assist attackers guessing
lengths). **Do not use** on numeric inputs; use `<mj-number-field>` min/max hints
instead.

## 3. Anatomy
- **Shadow `<output>` or `<span>`** — the visible counter text; `<output>` is
  preferred as it is a live region for form outputs.
- **Count span** — the current count or remaining count number.
- **Separator span** — optional "/" separator (shown only when `max` is set and
  `format="used/max"`).
- **Max span** — the maximum value (shown only in `"used/max"` format).
- **Status live region** — a visually-hidden `role="status"` `<span>` that
  announces threshold warnings (e.g., "10 characters remaining") politely.

## 4. Variants & modes
| Variant | Attribute | Description |
|---------|-----------|-------------|
| Characters remaining | `mode="remaining"` (default) | Shows `max − current` when `max` is set; shows current count when `max` is absent |
| Characters used | `mode="used"` | Shows current count (up/max format optional) |
| Used/max | `format="used/max"` | Displays "42 / 280" format regardless of `mode` |
| Word count | `unit="words"` | Counts whitespace-delimited words instead of Unicode characters |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `for` | string | `""` | Yes | ID of the associated `<input>` or `<textarea>`; the counter listens for `input` events on that element |
| `max` | number \| `""` | `""` | Yes | Maximum character (or word) count; when set, enables limit-based display and threshold warnings |
| `mode` | `"remaining"` \| `"used"` | `"remaining"` | Yes | Controls whether the displayed number is the remaining capacity or the used count |
| `unit` | `"characters"` \| `"words"` | `"characters"` | Yes | Whether to count Unicode characters or whitespace-delimited words |
| `format` | `"compact"` \| `"used/max"` | `"compact"` | Yes | `"compact"` shows a single number; `"used/max"` shows "N / Max" |
| `warn-at` | number \| `""` | `""` | Yes | Percentage (0–100) of `max` at which the counter switches to warning color; e.g., `80` warns at 80% used |
| `error-at` | number \| `""` | `100` | Yes | Percentage (0–100) of `max` at which the counter switches to error color and is included in `aria-describedby` as an error |
| `announce-at` | number \| `""` | `90` | Yes | Percentage (0–100) of `max` at which the live region starts announcing every change |
| `announce-interval` | number | `10` | Yes | When below `announce-at`, the live region only announces at multiples of this many remaining characters (e.g., every 10) |
| `disabled` | boolean | `false` | Yes | Renders the counter at reduced opacity when the associated control is disabled |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `current` | `number` | Read-only. Current character (or word) count of the associated control |
| `remaining` | `number \| null` | Read-only. Characters (or words) remaining until `max`; `null` when no `max` is set |
| `exceeded` | `boolean` | Read-only. `true` when `current > max` |
| `control` | `HTMLInputElement \| HTMLTextAreaElement \| null` | The resolved associated control |

## 7. Slots
No user-facing slots. The counter is fully generated from its attributes and the
control's current value.

| Slot | Description |
|------|-------------|
| — | No slots |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-count-change` | `{ current: number, remaining: number \| null, exceeded: boolean, unit: "characters" \| "words" }` | Yes | No | Fires on every count update (i.e., on each `input` event from the associated control) |
| `mj-warn` | `{ current: number, remaining: number, threshold: number }` | Yes | No | Fires once when the count crosses the `warn-at` threshold (entering warning zone) |
| `mj-exceed` | `{ current: number, max: number }` | Yes | No | Fires once when the count crosses `max` (entering exceeded state) |
| `mj-recover` | `{ current: number, max: number }` | Yes | No | Fires once when the count drops back at or below `max` after being exceeded |

## 9. CSS parts & custom properties
| Part / Property | Description |
|-----------------|-------------|
| `::part(counter)` | The outer `<output>` element |
| `::part(count)` | The span containing the displayed count number |
| `::part(separator)` | The "/" separator span (used/max format only) |
| `::part(max)` | The span containing the max value (used/max format only) |
| `--mj-counter-color` | Default text color (default: `var(--mj-color-text-secondary)`) |
| `--mj-counter-warn-color` | Text color in warning state (default: `var(--mj-color-text-warning)`) |
| `--mj-counter-error-color` | Text color in error/exceeded state (default: `var(--mj-color-text-error)`) |
| `--mj-counter-disabled-color` | Text color when disabled (default: `var(--mj-color-text-disabled)`) |
| `--mj-counter-font-size` | Font size (default: `var(--mj-font-size-xs)`) |

## 10. States
- **default** — normal secondary-color text; count displayed according to `mode`
  and `format`.
- **warning** — count has crossed the `warn-at` threshold; text switches to
  `--mj-counter-warn-color`; a polite announcement is triggered once.
- **error / exceeded** — count has crossed `max` (i.e., `exceeded === true`); text
  switches to `--mj-counter-error-color`; the counter's `id` is added to the
  control's `aria-describedby`; `aria-invalid="true"` is set on the control.
- **disabled** — text rendered at `--mj-counter-disabled-color`; no events fired.
- **no-max** — no `max` attribute; always renders in default color; no warning or
  error thresholds apply.

## 11. Behavior & interactions
- On `connectedCallback`, the component resolves the target control via `for` and
  attaches an `input` event listener.
- On each `input` event:
  1. Counts the control's `.value` (characters: `[...value].length`; words:
     `value.trim().split(/\s+/).filter(w => w.length > 0).length`).
  2. Updates `current`, `remaining`, and `exceeded`.
  3. Updates the displayed text.
  4. Determines whether to update the live region based on `announce-at` and
     `announce-interval`.
  5. Fires `mj-count-change`.
  6. Fires threshold events (`mj-warn`, `mj-exceed`, `mj-recover`) when crossing
     boundaries; these fire at most once per direction per crossing.
- The live region announcement text template is: `"{remaining} {unit} remaining"`.
  When exceeded: `"{over} {unit} over the limit"`.
- When the associated control is a `<mj-text-field>` or `<mj-textarea>`, the
  component additionally reads the shadow-root `maxlength` from the inner input and
  uses it as the `max` value if no explicit `max` attribute is provided.
- The counter does not enforce `maxlength`; enforcement remains on the control.
- On `disconnectedCallback`, the `input` listener is removed.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| — | `<mj-character-counter>` is not focusable; no keyboard interaction |
| _(any key in associated control)_ | Triggers an `input` event on the control which the counter observes; no direct key handling on the counter itself |

## 13. Accessibility
- The `<output>` element is an implicit live region (`aria-live="polite"`) per the
  HTML spec, but the component uses a separate visually-hidden `role="status"` span
  for controlled announcement to prevent every single character change from being
  announced (which would be extremely noisy). The visible `<output>` does not have
  `aria-live`; only the hidden status span does.
- Announcements occur only at `announce-at` threshold and at `announce-interval`
  multiples of remaining count. Below the threshold, updates are silent.
- When `exceeded`, the component's `id` is appended to the control's
  `aria-describedby` so the error count is read on focus; `aria-invalid="true"` is
  set on the control. Both are reversed when `exceeded` returns to `false`.
- The counter text is not the control's accessible name. It supplements the label
  and help text via `aria-describedby` when in error state only.
- All states (warning, error) are conveyed in both color and text (the number
  remaining makes the situation clear) — color is not the sole indicator.

## 14. Form participation
Not form-associated. Contributes no value to `FormData`. It manages `aria-invalid`
on the target control as a side-effect of `exceeded` state.

## 15. Internationalization & RTL
- Announcement template strings ("remaining", "over the limit") are overridable via
  `remaining-label` and `exceeded-label` attributes and the shared localization hook.
- The count number itself is formatted via `Intl.NumberFormat` using the document
  locale so digit grouping is locale-correct.
- Word counting uses a locale-agnostic whitespace split; CJK text (which does not
  use spaces) is counted by character regardless of `unit="words"` — a console
  warning is logged when CJK content is detected in word mode.
- In RTL layouts, the "N / Max" format renders in logical order (number on the
  right, max on the left) using CSS logical properties.

## 16. Progressive enhancement / SSR
Server renders as a `<output class="mj-character-counter">N / Max</output>` with
a static count. On upgrade, the component attaches the `input` listener and updates
the count dynamically. Without scripting, the static server-rendered count gives
users an initial reference but does not update.

## 17. Dependencies
- `web-component-development-plan.md` §6: Registry + base element helper,
  Live-region/announcement service, Localization/formatting hook, Design-token
  stylesheet.
- Typically composed inside `<mj-text-field>` or `<mj-textarea>` via a dedicated
  counter slot on those components.
- Peer form-structure primitives: `<mj-label>`, `<mj-help-text>`, `<mj-error-message>`.

## 18. Edge cases & error handling
- `for` target not found at connection: retried via `MutationObserver`; console
  warning logged.
- `max` set to `0` or negative: treated as absent; a console error is logged.
- `warn-at` >= `error-at`: a console warning is logged; `error-at` behavior takes
  precedence in the overlap range.
- Control value changes programmatically (not via user input): `input` event is
  not fired by the browser; callers must dispatch a synthetic `input` event or
  call the counter's `sync()` method.
- Unicode surrogate pairs and emoji sequences: character count uses
  `[...value].length` (iterator-based) which counts grapheme clusters correctly for
  BMP characters but not for all complex sequences — documented limitation.
- Very high counts (> 10,000 words or characters): no performance concern; no
  virtualization needed.

## 19. Acceptance criteria
- [ ] Typing in the associated control updates the displayed count in real time.
- [ ] In `mode="remaining"` with `max=280`, typing 30 characters displays "250"
      (compact) or "30 / 280" (used/max format).
- [ ] Typing beyond `max` sets `exceeded = true`, switches text to error color,
      adds counter `id` to `aria-describedby`, sets `aria-invalid="true"` on the
      control, and fires `mj-exceed`.
- [ ] Deleting characters below `max` fires `mj-recover` and reverses all error-state
      changes.
- [ ] Live region announces "10 characters remaining" at `announce-at=90%` for a
      field with `max=100`; announces every keystroke below 10 remaining.
- [ ] `unit="words"` counts words correctly for English prose.
- [ ] Count number uses locale-appropriate digit formatting.
- [ ] `disabled` renders counter at disabled color; no events fire.
- [ ] No-JS: server-rendered static count is visible.
- [ ] Axe-core reports zero violations; color is not the sole indicator of state.

## 20. Open questions
- Should `sync()` be a public method for callers who update control values
  programmatically, or should the component observe value changes via
  `MutationObserver` on the `value` property?
- Should grapheme-cluster-aware character counting (using `Intl.Segmenter`) be the
  default, or an opt-in via a `grapheme-clusters` attribute, given it is more
  expensive and not universally supported?
