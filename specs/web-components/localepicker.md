# Locale Picker Spec

- **Tag:** `<mj-locale-picker>`
- **Class / file:** `MjLocalePicker` / `mjlocalepicker.js`
- **Category:** Selection & dropdown-style controls
- **Primary or Variant:** Primary
- **Synonyms covered:** Language picker, Country/region picker
- **Phase:** P2
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-locale-picker>` is a specialized `<mj-combobox>` over a locale dataset — language tags, country/region codes, or full locale strings (language + region). It displays native-language names alongside the region flag (country mode) or ISO code, supports search by name or code, and emits a BCP 47 locale tag or ISO 3166-1 alpha-2 country code as its value.

## 2. When to use / when not to use
**Use** for language preference, country/region selection in address forms, and locale configuration. **Use `mode="language"`** when the user selects a UI or content language. **Use `mode="country"`** for selecting a country or region (e.g., shipping address). **Use `mode="locale"`** for a combined language + country selection. **Do not use** for timezone selection — use a separate timezone picker built on `Intl.supportedValuesOf("timeZone")`. **Do not use** when the list is a small custom set — use `<mj-select>` or `<mj-combobox>`.

## 3. Anatomy
- **Input** (`part="input"`) — text field showing the selected locale's display name; also the search field.
- **Trigger icon** (`part="trigger-icon"`) — flag emoji or globe icon reflecting the current selection.
- **Clear button** (`part="clear"`) — removes the selection when `clearable`.
- **Popup** (`part="popup"`) — positioned overlay with the filtered listbox.
- **Listbox** (`part="listbox"`) — `role="listbox"` of locale options.
- **Option** (`part="option"`) — single locale row (`role="option"`).
- **Option flag** (`part="option-flag"`) — flag emoji or SVG (country/locale modes).
- **Option native name** (`part="option-native-name"`) — name in the locale's own language (e.g., "Français").
- **Option english name** (`part="option-english-name"`) — name in the UI language (e.g., "French").
- **Option code** (`part="option-code"`) — the BCP 47 tag or ISO code (e.g., "fr-FR").
- **No-results** (`part="no-results"`) — empty state when search yields nothing.

## 4. Variants & modes
| Variant / mode | `mode` value | Value format | Dataset |
|----------------|-------------|-------------|---------|
| Language | `"language"` | BCP 47 language tag (e.g., `"fr"`) | IETF language subtag registry |
| Country/region | `"country"` | ISO 3166-1 alpha-2 (e.g., `"FR"`) | ISO 3166 country list |
| Locale | `"locale"` | BCP 47 locale (e.g., `"fr-FR"`) | CLDR-derived locale list |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `name` | string | `""` | Yes | Form field name |
| `value` | string | `""` | Yes | Selected locale code (BCP 47 or ISO 3166 per mode) |
| `mode` | `"language"` \| `"country"` \| `"locale"` | `"language"` | Yes | Dataset and value format |
| `display-locale` | string | `navigator.language` | Yes | BCP 47 tag used for the English-side display name |
| `show-native-name` | boolean | `true` | Yes | Show native-language name alongside display name |
| `show-code` | boolean | `false` | Yes | Show ISO/BCP 47 code in the option row |
| `show-flag` | boolean | `true` | Yes | Show flag emoji or icon (country/locale modes) |
| `clearable` | boolean | `false` | Yes | Shows clear button when value is set |
| `disabled` | boolean | `false` | Yes | Disables the control |
| `required` | boolean | `false` | Yes | A selection is required |
| `placeholder` | string | `"Select a language"` | Yes | Input placeholder (auto-adjusts per mode) |
| `allowed` | string | `""` | Yes | JSON array of allowed codes; empty = all |
| `excluded` | string | `""` | Yes | JSON array of codes to exclude |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `selectedLocale` | `LocaleItem \| null` | Full locale object for the selected item: `{ code, nativeName, displayName, flag? }` |
| `inputValue` | `string` | Current text in the search input |
| `validity` | `ValidityState` | Delegated from `ElementInternals` |
| `validationMessage` | `string` | Localizable invalid message |
| `dataSource` | `LocaleDataSource \| null` | Custom locale dataset (overrides built-in) |

**`LocaleItem` shape:**
```
{
  code: string;         // BCP 47 tag or ISO 3166 alpha-2
  nativeName: string;   // e.g., "Français"
  displayName: string;  // e.g., "French" in the display-locale
  flag?: string;        // Flag emoji or image URL
}
```

## 7. Slots
| Slot | Description |
|------|-------------|
| `no-results` | Custom empty search state |
| `trigger-icon` | Custom icon to replace the default flag/globe in the trigger |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-change` | `{ value: string, locale: LocaleItem \| null }` | Yes | No | Fired when selection changes |
| `mj-input` | `{ inputValue: string }` | Yes | No | Fired on each keystroke in the search field |
| `mj-open` | `{}` | Yes | Yes | Fired before popup opens |
| `mj-close` | `{}` | Yes | No | Fired after popup closes |
| `mj-clear` | `{}` | Yes | No | Fired when clear button is activated |

## 9. CSS parts & custom properties
**Parts:** `input`, `trigger-icon`, `clear`, `popup`, `listbox`, `option`, `option-flag`, `option-native-name`, `option-english-name`, `option-code`, `no-results`

**Custom properties:**
| Property | Default token | Description |
|----------|---------------|-------------|
| `--mj-locale-picker-popup-max-height` | `18rem` | Maximum popup height |
| `--mj-locale-picker-option-height` | `2.5rem` | Row height per option |
| `--mj-locale-picker-flag-size` | `1.25rem` | Flag emoji font size |
| `--mj-locale-picker-code-color` | `--mj-color-text-subtle` | Color of the code badge |
| `--mj-locale-picker-border-radius` | `--mj-radius-md` | Input and popup corner radius |

## 10. States
| State | Visual effect | ARIA effect |
|-------|--------------|-------------|
| Default | Input shows display name of selected locale (or placeholder) | — |
| Open / searching | Popup visible; options filtered | `aria-expanded="true"`; `aria-autocomplete="list"` |
| Option focused | Row highlighted | `aria-activedescendant` on input |
| Option selected | Checkmark; input filled | `aria-selected="true"` |
| No results | No-results slot shown | Status live region |
| Disabled | Muted; no interactions | `aria-disabled="true"` |
| Invalid | Error border | `aria-invalid="true"` |

## 11. Behavior & interactions
- On focus, the popup opens with the full list (or the filtered list if text is already present).
- Typing filters by native name, display name, and code simultaneously using case/diacritic-insensitive matching.
- Selecting an option commits its `code` as `value`, fills the input with its `displayName`, and closes the popup.
- Blurring without selecting reverts the input to the display name of the current committed value.
- The `allowed` filter restricts the visible list to specified codes; `excluded` removes codes.
- Flags in country/locale modes are Unicode flag emoji sequences (`\uD83C\uDDF-🇿` pairs) rendered via the system font; no image downloads required.
- The built-in dataset is lazy-loaded on first open to avoid parse cost at page load.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| Any printable key | Type into search; filter list; open popup |
| `ArrowDown` | Open popup; move focus to next option |
| `ArrowUp` | Move focus to previous option |
| `Home` | Focus first option |
| `End` | Focus last option |
| `Enter` | Commit focused option |
| `Escape` | Close popup; revert input to current value |
| `Tab` | Commit or revert; move focus |
| `Backspace` | Delete last character; re-filter |
| `Alt+ArrowDown` | Open popup without changing input |
| `Alt+ArrowUp` | Close popup without changing value |

## 13. Accessibility
- Follows the WAI-ARIA Combobox pattern (same as `<mj-combobox>`): `role="combobox"` on input, `aria-haspopup="listbox"`, `aria-expanded`, `aria-autocomplete="list"`, `aria-controls` referencing listbox.
- Each option: `role="option"`, `aria-selected`, `aria-label` combining native name and display name (e.g., "Français – French").
- Flag emoji in options are `aria-hidden="true"` (decorative; the text names convey the identity).
- No-results status announced via polite live region: "No languages found for 'xyz'".
- The trigger-icon (flag/globe) in the input area is `aria-hidden="true"`.
- All interactive elements meet the 44 × 44 px touch target.

## 14. Form participation
- Form-associated via `ElementInternals`; contributes `name=value` where `value` is the BCP 47 tag or ISO code.
- `required`: `validity.valueMissing` when `value` is empty.
- On form reset, reverts to the initial `value` attribute.

## 15. Internationalization & RTL
- `display-locale` controls the language of the "English name" column; defaults to `navigator.language`.
- Native names are rendered in their own script and direction; the option row may contain mixed-direction text (e.g., Hebrew name in an LTR UI). Each option uses `dir="auto"` on the native-name span.
- The component's own UI (input, clear button) mirrors in RTL.
- Sorting of options uses `Intl.Collator` with the `display-locale` for culturally correct ordering.
- `placeholder` is author-supplied; default English strings must be overridden for non-English UIs.

## 16. Progressive enhancement / SSR
- Server renders a `<select>` with `<option>` elements representing available locales inside `<mj-locale-picker>`.
- Before upgrade the native select is functional.
- On upgrade, the native select is hidden; the component builds the combobox UI.
- Without scripting, the native select renders and submits the locale code.

## 17. Dependencies
- Section 6: Registry/base element, design tokens, overlay/positioning engine, focus utilities (`aria-activedescendant` helper), form-association helper, live-region service, localization hook (`Intl.DisplayNames`, `Intl.Collator`), data-source adapter.
- `<mj-combobox>` semantics and behavior reused (this component IS a combobox specialization).
- Built-in locale dataset (CLDR-derived; lazy-loaded JSON bundle).

## 18. Edge cases & error handling
- `value` set to a code not in the dataset: input shows the raw code string; no option is highlighted; no error thrown.
- `allowed` and `excluded` both contain the same code: `excluded` wins.
- All locales excluded: empty list; required validation always fails; console warning logged.
- Dataset load failure (network): component falls back to the `allowed` list if provided as static options; error live region announces "Failed to load language list".
- Mixed-script native names: `dir="auto"` handles bidirectionality at the option level.
- Very long native or display names: truncated with ellipsis; full text in `aria-label`.

## 19. Acceptance criteria
- [ ] Typing filters by native name, display name, and code simultaneously.
- [ ] Selecting an option commits the code as `value`; `mj-change` fires with `locale` object.
- [ ] Flag emoji rendered correctly for country/locale modes; `aria-hidden="true"` on flag spans.
- [ ] `aria-label` on each option combines native and display names.
- [ ] `allowed` restricts visible options; `excluded` removes codes.
- [ ] `Intl.Collator` used for sorting; `Intl.DisplayNames` for display names.
- [ ] `required` with empty value fails `checkValidity()`.
- [ ] Native select fallback functional without scripting.
- [ ] axe-core reports zero violations in open, searching, and disabled states.
- [ ] RTL layout mirrors input; native-name spans use `dir="auto"`.

## 20. Open questions
- Should `mode="locale"` allow selecting language without a country subtag (e.g., just "fr") or force a full locale (e.g., "fr-FR")?
- Should the dataset be versioned and updatable independently of the component (e.g., via a CDN URL attribute)?
- Should the component expose a `favorites` mechanism for recently or frequently used languages?
