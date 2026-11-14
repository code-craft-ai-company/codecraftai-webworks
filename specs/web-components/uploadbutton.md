# Upload Button Spec

- **Tag:** `<mj-upload-button>`
- **Class / file:** `MjUploadButton` / `mjuploadbutton.js`
- **Category:** Buttons & actions (§5.3)
- **Primary or Variant:** Primary
- **Synonyms covered:** Upload button, File upload button
- **Phase:** P1
- **Status:** Implemented (this spec documents the shipped behavior of `mjuploadbutton.js`)

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-upload-button>` is a button-styled control that lets the user choose files,
either through the native file picker or by dropping files on it (or on another
element named by `drop-target`). Every pick or drop is filtered by `accept` and
`max-size` and reported through one event, `mj-upload-select`, with the considered
files split into accepted and rejected ones. The accepted files become the
selection: `files` returns them, their name or count is shown next to the button,
and they are submitted with the owning `<form>` under `name`. A pick or drop in
which every file is rejected keeps the previous selection. It satisfies the
"Upload pairs with File picker" entry of plan §5.3 as the compact button form. It
does not upload anything itself.

## 2. When to use / when not to use

Use for a compact "Upload" / "Attach" / "Import" action: a toolbar button, a form
field that takes one or a few files, or a button inside a page-defined drop area
(`drop-target`). Use it when the page uploads the files itself on
`mj-upload-select`, or lets the form submit them.

Do not use it when the user needs to see and manage a list of files (per-file
rows, previews, removal, progress, immediate upload to `upload-url`) — use
`<mj-file-picker>`. For a large, always-visible drop area use `<mj-dropzone>`. To
save a file use `<mj-download-button>`; for other actions use `<mj-button>`.

`filepicker.md` and `sharebutton.md` no longer list "Upload button" as a synonym;
this dedicated component covers the button form.

## 3. Anatomy

- **Host element** — `display: inline-block` (`block` with the `block` attribute),
  `position: relative`. By default it is also the drop surface.
- **button (part)** — the inner native `<button type="button">`; the only focusable
  target. It carries `aria-label`, `aria-busy` and `disabled` (no `aria-required`,
  which the button role does not allow; see §13).
- **spinner (part)** — a ring before the content inside the button,
  `aria-hidden="true"`, shown only while `loading` is set.
- **Default slot** — inside the button: the visible text and an optional icon.
- **summary (part)** — a `<span>` after the button showing the selected file's name,
  or the file count; `hidden` while nothing is selected and not displayed with
  `icon-only`.
- **file-input (part)** — the native `<input type="file">`, visually hidden
  (1 px clip), `tabindex="-1"`, `aria-hidden="true"`. It opens the picker and
  receives `accept`, `multiple`, `capture`, `name` and `disabled`. Its `click` and
  native `input` events are stopped at the input and never reach the host.
- **Drop surface** — the host, or the element matched by `drop-target` (outside the
  component).

## 4. Variants & modes

| Mode / variant     | Attribute                 | Description |
|--------------------|---------------------------|-------------|
| Default (outlined) | (no `variant`)            | `--mj-surface` background with a `--mj-border-strong` border. Any value other than the two below renders this way |
| Primary            | `variant="primary"`       | Accent background and border, `--mj-text-on-accent` text |
| Tertiary           | `variant="tertiary"`      | Transparent background and border |
| Sizes              | `size="sm"` / `size="lg"` | Smaller / larger min-height, padding and font size. Any other value (including `md`) is the medium size |
| Icon-only          | `icon-only`               | Zero padding, 1:1 aspect ratio; the summary is not displayed. The author supplies `label` |
| Block              | `block`                   | Host is `display: block`; the button is full width |
| Single file        | (no `multiple`)           | Only the first offered file of a pick or drop is considered |
| Multiple files     | `multiple`                | Every offered file is considered |
| Own drop surface   | (no `drop-target`)        | Files dropped on the host are taken |
| External drop surface | `drop-target="<selector>"` | Files dropped on the matched element are taken; the host is no longer a drop surface |

There is no `link` variant (unlike `<mj-download-button>`).

## 5. Attributes

| Attribute     | Type                         | Default | Reflects | Description |
|---------------|------------------------------|---------|----------|-------------|
| `accept`      | comma-separated list         | —       | No       | Extensions (`.csv`), MIME types (`text/csv`) and wildcards (`image/*`). Forwarded to the file input (filters the picker) and applied to every pick and drop (§11) |
| `multiple`    | boolean                      | `false` | Yes      | Allows more than one file; forwarded to the file input. Without it only the first offered file is considered |
| `max-size`    | size (bytes, optional unit)  | —       | No       | Maximum size per file: a non-negative number, optionally followed by a unit suffix `B`, `KB`, `MB` or `GB` (case-insensitive, optional space, decimals allowed; `KiB` / `MiB` / `GiB` are accepted as aliases). Units are 1024-based, the base the library uses to display sizes: `200KB` = 204,800 bytes, `2MB` = 2,097,152 bytes, `1.5 MB` = 1,572,864 bytes. A plain number is bytes. Absent, empty or `0` means no limit. Any other value (`abc`, `-5`, `1e6`, `2TB`) is ignored, so there is no limit, and a `console.warn` is logged once per value |
| `capture`     | string                       | —       | No       | Forwarded verbatim to the file input when non-empty (`user`, `environment`) |
| `name`        | string                       | —       | No       | Form field name the accepted files are submitted under. Also copied to the inner input, which does not take part in the outer form |
| `required`    | boolean                      | `false` | Yes      | An empty selection is invalid (`valueMissing`). Not exposed as `aria-required` (not allowed on the button role); state it in the visible label (§13) |
| `drop-target` | CSS selector                 | —       | No       | Element that accepts drops instead of the host, looked up in the host's root node (§11) |
| `variant`     | `primary\|tertiary`          | —       | No       | Visual emphasis (§4). CSS only |
| `size`        | `sm\|lg`                     | —       | No       | Control size (§4). CSS only |
| `label`       | string                       | —       | No       | Accessible name: copied to the button's `aria-label` when non-empty |
| `loading`     | boolean                      | `false` | No       | Busy: spinner, `aria-busy="true"`, picks and drops ignored; the button stays focusable. There is no `loading` property |
| `disabled`    | boolean                      | `false` | Yes      | Disables the inner button and input; picks and drops ignored |
| `icon-only`   | boolean                      | `false` | No       | Square button; hides the summary. CSS only |
| `block`       | boolean                      | `false` | No       | Full-width layout. CSS only |

`drag-over` is a state attribute the component sets on the host while a drag is
over the drop surface and removes when it leaves or drops; it is not observed and
should not be set by authors.

Common MjElement attributes (`dock`, `anchor`, `theme`, `hidden`, `context-menu`)
behave as on every component.

## 6. Properties

| Property            | Type                       | Description |
|---------------------|----------------------------|-------------|
| `files`             | `File[] \| null`           | Read-only. The accepted files of the current selection, or `null` when nothing is selected. Returns the component's own array, not a copy |
| `multiple`          | `boolean`                  | Reflects `multiple`; a truthy value sets the attribute, a falsy value removes it |
| `required`          | `boolean`                  | Reflects `required`; a truthy value sets the attribute, a falsy value removes it |
| `disabled`          | `boolean`                  | Reflects `disabled`; a truthy value sets the attribute, a falsy value removes it. Reads the attribute only, so it is `false` while an ancestor `<fieldset disabled>` disables the control |
| `form`              | `HTMLFormElement \| null`  | Read-only. The form owner from `ElementInternals`; `null` without `ElementInternals` |
| `validity`          | `ValidityState \| null`    | Read-only. From `ElementInternals`; `null` without it |
| `validationMessage` | `string`                   | Read-only. From `ElementInternals`; `""` without it |

`accept`, `max-size`, `capture`, `name`, `drop-target`, `label`, `loading`,
`variant`, `size`, `icon-only` and `block` have no properties; set them as
attributes. There is no `value`, `name`, `type`, `willValidate`, `labels` or
`setCustomValidity()`.

**Methods**

| Method             | Description |
|--------------------|-------------|
| `clear()`          | Empties the selection and the inner input, publishes an empty form value, refreshes validity and hides the summary. Emits no event and makes no announcement |
| `click()`          | Clicks the inner button, so the picker opens as on a user click. Browsers open the picker only during a user gesture. Does nothing while `disabled` (or fieldset-disabled) or `loading`, or before the first render. `HTMLElement.click()` would only dispatch a click at the host, which never reaches the inner button |
| `checkValidity()`  | `ElementInternals.checkValidity()`; `true` without `ElementInternals` |
| `reportValidity()` | `ElementInternals.reportValidity()`; `true` without `ElementInternals` |

## 7. Slots

| Slot      | Description |
|-----------|-------------|
| (default) | Button content: text and an optional inline icon. It sits inside the native button, so it must not contain interactive content |

## 8. Events

| Event              | `detail` | Bubbles | Composed | Cancelable | Description |
|--------------------|----------|---------|----------|------------|-------------|
| `mj-upload-select` | `{ files: File[], accepted: File[], rejected: { file: File, reason: 'accept'\|'max-size' }[], source: 'picker'\|'drop' }` | Yes | Yes | No | Fires after each picker selection, and after each drop that carries at least one file while the control is not disabled or loading. The selection, form value, validity and summary are already updated |

- `files` lists the files that were considered: every offered file with
  `multiple`, only the first one without it. Files cut by the single-file rule
  appear in neither `accepted` nor `rejected`.
- A file failing both checks is rejected with reason `accept` (the type check comes
  first).
- The event is not emitted by `clear()`, a form reset, attribute changes, a drop
  without files, or a pick or drop ignored because the control is inert.
- A pick or drop in which no file is accepted still emits the event (with an empty
  `accepted`), but the selection, form value, validity and summary stay as they
  were.
- The component emits no `mj-change` and no bare `change` or `input` event. The
  inner file input's native `input` event (composed) is stopped at the input, and
  its `change` event does not leave the shadow root, so neither reaches the host.
- Opening the picker calls `click()` on the hidden input from the button's click
  listener. That synthetic click is stopped at the input, so a `click` listener on
  the host runs once per activation (for the inner button's click).

## 9. CSS parts & custom properties

**Parts**
- `::part(button)` — inner native `<button>`
- `::part(spinner)` — busy spinner
- `::part(summary)` — selected file name or file count
- `::part(file-input)` — the visually hidden native file input

**Custom properties**

| Property | Description |
|---|---|
| `--mj-upload-button-height` | Minimum height of the medium size (default `--mj-control-height-md`). `size="sm"` / `size="lg"` use `--mj-control-height-sm` / `--mj-control-height-lg` instead |
| `--mj-upload-button-font-weight` | Font weight (default `--mj-font-weight-medium`) |
| `--mj-upload-button-color` | Text color (default `--mj-text`); not used by `primary` (`--mj-text-on-accent`) |
| `--mj-upload-button-bg` | Background (default `--mj-surface`); not used by `primary` or `tertiary` |
| `--mj-upload-button-border-color` | Border color (default `--mj-border-strong`); not used by `primary` or `tertiary` |
| `--mj-upload-button-border-radius` | Corner radius (default `--mj-radius-md`) |
| `--mj-upload-button-focus-ring-color` | Focus ring color (default `--mj-focus-ring`) |
| `--mj-upload-button-dragover-border-color` | Border color while `drag-over` is set (default `--mj-accent`) |
| `--mj-upload-button-dragover-bg` | Background while `drag-over` is set (default `--mj-bg-muted`) |
| `--mj-upload-button-summary-font-size` | Summary font size (default `--mj-font-size-sm`) |
| `--mj-upload-button-summary-color` | Summary text color (default `--mj-text-muted`) |

The hover background (`--mj-bg-muted`; `--mj-accent-hover` for `primary`) and the
variant colors use library tokens directly and have no component property. While
`drag-over` is set on a `primary` button the text switches from
`--mj-text-on-accent` to `--mj-upload-button-color` (default `--mj-text`), because
the drag-over background replaces the accent fill. The spinner size is `1em` and
its color `currentColor`.

## 10. States

| State                 | Visual effect | ARIA effect |
|-----------------------|---------------|-------------|
| default               | Variant colors; summary hidden | `aria-busy="false"` |
| hover                 | `--mj-bg-muted` background (`--mj-accent-hover` for `primary`) | — |
| focus-visible         | Focus ring on the inner button | — |
| selected              | Summary shows the file name (one file) or the file count | — (announced once, §13) |
| drag-over             | Host carries `drag-over`; drag-over border and background on the button, over any variant (`primary` text switches to `--mj-text`) | — |
| loading               | Spinner shown; 55 % opacity; `pointer-events: none` on the button | `aria-busy="true"`; the button is not disabled and stays focusable |
| disabled              | 55 % opacity; `pointer-events: none` on the button | Native `disabled` on the button and the input; not focusable |
| disabled by fieldset  | Same as disabled (through `.btn:disabled`); no `disabled` attribute on the host | Same as disabled |
| required, empty       | No visual change | `validity.valueMissing` is `true`; no `aria-required` (§13) |

There is no pressed (`:active`) style and no invalid styling.

## 11. Behavior & interactions

- **Picker.** A click on the inner button (pointer, Enter, Space or `click()`)
  calls `click()` on the hidden file input unless the control is disabled (own
  attribute or fieldset) or `loading`. The browser shows its picker, filtered by
  `accept` and limited by `multiple`; `capture` is passed through. On the input's
  `change` the chosen files are copied, the input's value is emptied (so choosing
  the same file again fires `change` again), and the files are processed with
  `source: 'picker'`. The inert check runs when the picker opens; a pick that
  returns after `disabled` or `loading` was set is still processed. The component
  does not listen for the input's `cancel` event; cancelling the picker leaves the
  selection as it is.
- **Drop.** The drop surface gets `dragover`, `dragleave` and `drop` listeners.
  - `dragover` while not inert: `preventDefault()`, sets `drag-over` on the host,
    `dropEffect = "copy"`. The drag's data types are not checked, so text and link
    drags highlight too.
  - `dragleave`: removes `drag-over` when the event target is the surface itself or
    `relatedTarget` is `null`.
  - `drop` while not inert: `preventDefault()`, removes `drag-over`, and processes
    `dataTransfer.files` with `source: 'drop'` when there is at least one file. A
    drop without files is swallowed with no event.
  - While inert, `dragover` and `drop` are not cancelled, so the browser's default
    applies (a dropped file is usually opened in the tab unless the page prevents
    it).
- **Drop surface resolution.** On connect, and when `drop-target` changes while
  connected, the selector is run with `getRootNode().querySelector()` — the
  document, or the shadow root that contains the host. The first match becomes the
  surface. No match keeps the host, silently; an invalid selector keeps the host
  and logs a `console.warn`. The lookup is not repeated when the DOM changes later.
  Listeners are removed on a real disconnect and kept on a same-parent reorder.
  `drag-over` is always set on the host, not on the external surface; style the
  surface from the page, for example with
  `#zone:has(mj-upload-button[drag-over])`.
- **Selection processing** (picker and drop alike):
  1. Without `multiple`, only the first offered file is kept.
  2. Each file is checked against `accept`, then `max-size` (read as described in
     §5; an unreadable value means no limit).
  3. When at least one file was accepted, the accepted files replace the previous
     selection (selections do not accumulate), the form value is published,
     validity refreshed (§14) and the summary updated. When no file was accepted
     the previous selection, form value, validity and summary are kept.
  4. `mj-upload-select` is emitted.
  5. When at least one file was accepted, `mj.uploadButton.selected` is announced
     politely through the shared live region.
- **`accept` matching.** Split on commas, trimmed, empty tokens ignored,
  case-insensitive. A token starting with `.` matches a file name ending with it; a
  token ending with `/*` matches a MIME type starting with the part before `*`
  (`image/*` matches `image/png`); any other token must equal the file's MIME type.
  An absent, empty or whitespace-only `accept` accepts every file. A file whose
  browser-reported MIME type is empty can match only extension tokens.
- **Summary.** One selected file shows its name; more show
  `mj.uploadButton.fileCount` ("3 files"); none hides the summary.
- **Attribute changes.** `accept`, `multiple`, `capture`, `name` and the disabled
  state are re-forwarded to the input, and `label`, the disabled state and
  `loading` to the button, on every observed attribute change. `name` and
  `required` changes also republish the form value and validity. Changing
  `accept`, `max-size` or `multiple` does not re-filter an existing selection.
- **No network.** The component performs no upload, fetch, progress reporting,
  abort or error handling. The page uploads from `mj-upload-select` or through form
  submission; `loading` is a busy flag the page sets and clears.
- **Re-render.** A locale change, or reconnecting after a removal, renders the
  shadow DOM again; the selection is kept and the summary, validity and drop
  listeners are restored.

## 12. Keyboard interaction

| Key         | Action |
|-------------|--------|
| `Enter`     | Opens the file picker (native button behavior) |
| `Space`     | Opens the file picker (native button behavior) |
| `Tab`       | Moves focus to the next focusable element |
| `Shift+Tab` | Moves focus to the previous focusable element |

There is no custom key handling. The picker is the keyboard path; dropping is
pointer-only. A disabled control is not focusable; a `loading` control is, and
Enter / Space on it do nothing. The hidden file input is never a tab stop.
`element.focus()` (MjElement) focuses the inner button when it is enabled.

## 13. Accessibility

- Role: native `<button>`. Name from the slotted content, or `label` (as
  `aria-label`). `icon-only` buttons need `label`; there is no default name.
- `aria-busy` is always present: `"true"` while `loading`, `"false"` otherwise.
  Unlike `<mj-download-button>`, `loading` does not set `aria-disabled`.
- `disabled` (own or fieldset) uses the native `disabled` attribute on the button.
- `required` is not put on the button as `aria-required`: that attribute is not
  supported for the `button` role in WAI-ARIA 1.2. The required state is enforced
  through validation (`valueMissing`, `reportValidity()` anchored at the button);
  the page should say in the visible text or `label` that a file is required (for
  example "Attach resume (required)").
- The file input is `aria-hidden="true"`, `tabindex="-1"` and visually hidden.
- The summary is plain text after the button and is not referenced by the button
  (`aria-describedby`); a screen-reader user hears the selection through the polite
  announcement "{count} file(s) selected", which names no files. Rejections, `clear()`
  and form reset are not announced; the page announces rejections from
  `mj-upload-select`.
- `reportValidity()` anchors the browser's message at the inner button. The
  component sets no `aria-invalid` and renders no inline error.
- `drag-over` is visual only. The picker satisfies the single-pointer alternative
  to dragging (WCAG 2.5.7).
- Target size: `min-width: var(--mj-target-min)` always applies; the medium
  min-height is `--mj-control-height-md`.

## 14. Form participation

- Form-associated (`static formAssociated = true`); `ElementInternals` is attached
  in the constructor when the browser supports it. It does not use the shared
  `FormControlMixin` (`core/forminternals.js`).
- **Value:** a `FormData` holding each accepted file under `name`, passed to
  `setFormValue()`. With no `name` or an empty selection the value is `null`, so
  nothing is submitted (a native file input submits an empty file part instead).
  As with a native file input, a native submission sends the file contents only
  when the form uses `enctype="multipart/form-data"`.
- **Validation:** with `required` and an empty selection, `valueMissing` is set
  with the message from `t("core.required")` ("This field is required."), anchored
  at the inner button. Validity is refreshed on every selection change, `clear()`,
  render, and `name` / `required` change. Rejected files never enter the value and
  do not make the control invalid.
- **Reset:** `formResetCallback` calls `clear()`; no event is emitted.
- **Disabled:** the own `disabled` attribute or an ancestor `<fieldset disabled>`
  (`formDisabledCallback`) disables the inner button and input and blocks drops. By
  platform rules a disabled form-associated element is not submitted and is barred
  from constraint validation.
- **Restore:** there is no `formStateRestoreCallback`; the selection is not
  restored on history navigation or autofill.
- **Without `ElementInternals`:** no submission, `form` and `validity` are `null`,
  `validationMessage` is `""`, `checkValidity()` and `reportValidity()` return
  `true`.

## 15. Internationalization & RTL

- Strings read through `t()` from `core/intl.js`:
  - `mj.uploadButton.selected` — announcement; plural forms "{count} file selected"
    / "{count} files selected"
  - `mj.uploadButton.fileCount` — summary for more than one file; "{count} file" /
    "{count} files"
  - `core.required` — `valueMissing` message, "This field is required."
- `setLocale()` / `registerStrings()` render the component again (MjElement
  default), so the summary and the validation message follow the new locale; an
  announcement already made is not repeated.
- File names are shown as text (`textContent`) with `overflow-wrap: anywhere`.
- The console warning for an invalid `drop-target` is English and not localized.
- The summary uses `margin-inline-start`, and the button lays out as inline flex
  with a gap, so both mirror in RTL. The spinner's open segment uses
  `border-inline-end-color`.
- Under `prefers-reduced-motion: reduce` the transitions and the spinner rotation
  are turned off.

## 16. Progressive enhancement / SSR

Server renders
`<mj-upload-button name="resume" accept=".pdf" required>Attach resume</mj-upload-button>`.
Before upgrade only the text shows; there is no file input, so nothing can be
chosen or submitted. On upgrade the button, hidden input, summary and form
association appear. A light-DOM `<input type="file">` cannot serve as the fallback
inside the element (it would be slotted into the button). Forms that must work
without JavaScript render a native file input instead (for example in
`<noscript>`). A server cannot pre-populate the selection.

## 17. Dependencies

- **Registry + base element helper** (§6) — `MjElement` (`render`, `afterRender`,
  `onConnected` / `onDisconnected`, `onAttributeChanged`, `listen`, `emit`,
  `focus()`, docking / anchoring)
- **Form-association** — platform `ElementInternals` (`setFormValue`,
  `setValidity`, `formResetCallback`, `formDisabledCallback`)
- **Live-region announcer** (§6) — `announce()` from `core/announcer.js`
- **Localization hook** (§6) — `t()` for the announcement, summary and validation
  message
- **Design-token stylesheet** (§6)
- Consumers: `<mj-toolbar>` treats `mj-upload-button` as a toolbar item
- Related: `<mj-file-picker>`, `<mj-dropzone>`, `<mj-download-button>`, `<mj-button>`

## 18. Edge cases & error handling

- `max-size="abc"`, `"-5"`, `"1e6"` or an unknown unit (`"2TB"`): ignored (no
  limit) with one console warning per value. `"2MB"` is 2,097,152 bytes; `"2mb"`
  and `"2 MB"` are the same.
- `accept="*/*"` is not special-cased: in the component's filter it matches no
  file, even though the picker may offer every file.
- A pick or drop where every file is rejected keeps a previously valid selection,
  its summary and its validity; the event reports the rejections. Nothing is
  announced.
- Several files dropped without `multiple`: only the first is considered. If it is
  rejected, the others are not tried, and they are absent from the event detail.
- Changing `multiple`, `accept` or `max-size` after a selection leaves the selection
  as it is (it may now hold several files, or files the new filter would reject).
- Mutating the array returned by `files` changes what `files` returns and the
  summary on its next update, but not the submitted value; treat it as read-only.
- `drop-target` that matches nothing, is invalid, or names an element in a different
  shadow root: the host stays the drop surface. An element added after the lookup
  is not picked up until `drop-target` changes or the host is reconnected.
- Several upload buttons with the same `drop-target`: each handles the drop and each
  takes the files.
- A `drop-target` container holding text fields: text dragged into those fields is
  swallowed by the surface's `drop` handler.
- `drag-over` is cleared only by a `dragleave` whose target is the surface or whose
  `relatedTarget` is `null`, or by a drop while not inert. Leaving the surface
  directly from a descendant can leave it set until the next such event; becoming
  inert during a drag does not clear it either.
- With `variant="primary"` the drag-over background replaces the accent background;
  the text switches to `--mj-upload-button-color` (default `--mj-text`) so it keeps
  its contrast during the drag.
- `disabled` or `loading` set while the picker is open: the returning pick is still
  processed and emitted.
- A `click` listener on the host runs once per activation: the synthetic click of
  the hidden input and its native `input` event are stopped inside the shadow root.
- `loading` can only be toggled through the attribute; there is no property.

## 19. Acceptance criteria

- [ ] Clicking the button (or Enter / Space) opens the file picker; `click()` does the same during a user gesture.
- [ ] While `disabled`, fieldset-disabled or `loading`, activation and drops are ignored.
- [ ] A pick emits `mj-upload-select` with `source: 'picker'`; picking the same file again emits again.
- [ ] A drop of files on the host emits `mj-upload-select` with `source: 'drop'`; a drop without files emits nothing.
- [ ] `drop-target` moves the drop surface to the matched element; no match or an invalid selector keeps the host (warning for invalid).
- [ ] `drag-over` is set on the host during a drag over the surface and removed on leave and drop.
- [ ] `accept` filters by extension, `type/*` wildcard and exact MIME type, case-insensitively.
- [ ] `max-size` rejects larger files with reason `max-size`; plain bytes and `B` / `KB` / `MB` / `GB` suffixes (1024-based, case-insensitive) are read; absent, `0` or an unreadable value means no limit (with one warning for the unreadable value).
- [ ] Without `multiple` only the first offered file is considered.
- [ ] Only accepted files become `files`; an all-rejected pick or drop leaves the previous selection (`null` when there was none).
- [ ] The summary shows the file name for one file and the localized count for more, and is hidden when empty or `icon-only`.
- [ ] `mj-upload-select` bubbles, is composed and is not cancelable; its detail matches §8.
- [ ] Accepted files are submitted under `name`; nothing is submitted without `name` or selection.
- [ ] `required` with no selection sets `valueMissing` with the localized message; a selection clears it.
- [ ] Form reset and `clear()` empty the selection without an event.
- [ ] `<fieldset disabled>` disables the button and input.
- [ ] A polite announcement with the accepted count follows each selection with accepted files.
- [ ] `aria-busy` tracks `loading`; `label` becomes the button's `aria-label`; the button never carries `aria-required`.
- [ ] A host `click` listener runs once per activation; the inner input's native `input` event does not reach the host.
- [ ] axe scan zero violations in the default, selected, loading, disabled and icon-only (with `label`) states.
- [ ] Light, dark, high-contrast, reduced-motion and RTL rendering verified.

## 20. Open questions

- Should files cut by the single-file rule be reported (for example as rejected
  with reason `multiple`) so the page can tell the user?
- Should the component emit an `mj-change` / `change` pair like other form controls?
  (The leaked native `input` event and the duplicate host `click` are now stopped.)
- Should the summary be linked to the button (`aria-describedby`) and rejections be
  announced?
- Should the component adopt `FormControlMixin` for a `user-invalid` state, inline
  error and `setCustomValidity()`, and expose `name`, `value`, `willValidate` and
  `labels`?
- Should an associated `<label for>` name the inner button?
- Should there be a `loading` property, as on `<mj-download-button>`?
- Should `dragover` highlight only drags that carry files, so text drops into a
  `drop-target` container keep working?
- Should `drag-over` (or a custom state) be set on the external drop surface too?
- Should `variant="secondary"` be an explicit value, as on `<mj-button>`? Today it
  renders as the default outlined style; the catalog examples use the default.
- Should the component offer an opt-in upload (URL, progress, abort, errors), or is
  that permanently `<mj-file-picker>`'s role?
