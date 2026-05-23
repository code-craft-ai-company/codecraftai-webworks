# File Picker Spec

- **Tag:** `<mj-file-picker>`
- **Class / file:** `MjFilePicker` / `mjfilepicker.js`
- **Category:** Selection & dropdown-style controls
- **Primary or Variant:** Primary
- **Synonyms covered:** Image picker, Upload button
- **Phase:** P1
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-file-picker>` enhances `<input type="file">` with a drag-and-drop zone, file type and size validation, per-file progress indicators, and image previews. It exposes a `FileList`-compatible property and participates in forms. The drag-and-drop zone also serves as the visual target for files dragged from the OS; a click on the zone or an explicit "Choose files" button opens the native file dialog.

## 2. When to use / when not to use
**Use** when users need to upload one or more files from their device, optionally with image previews or upload progress. **Use** the compact `button` variant when a dropzone is disproportionate to the context. **Do not use** as a camera capture control — use `capture` attribute on the native input. **Do not use** for asset selection from a media library — use `<mj-asset-picker>`.

## 3. Anatomy
- **Dropzone** (`part="dropzone"`) — the primary drag-and-drop target area.
- **Dropzone icon** (`part="dropzone-icon"`) — upload/file illustration or icon.
- **Dropzone label** (`part="dropzone-label"`) — primary instruction text.
- **Dropzone hint** (`part="dropzone-hint"`) — secondary info (accepted types, max size).
- **Choose button** (`part="choose-button"`) — activates the native file dialog.
- **File list** (`part="file-list"`) — list of selected/uploading files.
- **File item** (`part="file-item"`) — row for one file; contains preview, name, size, status, remove.
- **File preview** (`part="file-preview"`) — thumbnail for image files.
- **File name** (`part="file-name"`) — file name text.
- **File size** (`part="file-size"`) — human-readable file size.
- **File status** (`part="file-status"`) — "ready", "uploading", "error", "success".
- **File progress** (`part="file-progress"`) — progress bar per file.
- **File remove** (`part="file-remove"`) — button to remove the file from the list.
- **Error message** (`part="error"`) — field-level error (e.g., type or size violation).

## 4. Variants & modes
| Variant / mode | Attribute | Behavior |
|----------------|-----------|----------|
| Dropzone (default) | — | Full drag-and-drop zone with button |
| Button-only | `variant="button"` | Compact "Choose file" button; no dropzone area |
| Single file | `multiple` absent | Only one file may be selected at a time |
| Multi-file | `multiple` (boolean) | Multiple files may be selected |
| Image-only preview | `accept="image/*"` | Thumbnails generated for image files |
| Immediate upload | `upload-url` attribute | Files are uploaded after selection |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `name` | string | `""` | Yes | Form field name |
| `multiple` | boolean | `false` | Yes | Allow multiple file selection |
| `accept` | string | `""` | Yes | Comma-separated MIME types or extensions (forwarded to native input) |
| `max-size` | number | `0` | Yes | Maximum file size in bytes; 0 = unlimited |
| `max-files` | number | `0` | Yes | Maximum number of files; 0 = unlimited |
| `disabled` | boolean | `false` | Yes | Disables the control |
| `required` | boolean | `false` | Yes | At least one file required for validity |
| `variant` | `"dropzone"` \| `"button"` | `"dropzone"` | Yes | Layout variant |
| `upload-url` | string | `""` | Yes | URL for immediate XHR/fetch upload after selection |
| `label` | string | `"Choose files"` | Yes | Accessible label for the choose button |
| `dropzone-label` | string | `"Drag files here or"` | Yes | Instruction text in the dropzone |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `files` | `File[]` | Array of currently selected `File` objects |
| `fileItems` | `MjFileItem[]` | Array of internal file item state objects (file, status, progress, error) |
| `validity` | `ValidityState` | Delegated from `ElementInternals` |
| `validationMessage` | `string` | Localizable invalid message |

## 7. Slots
| Slot | Description |
|------|-------------|
| `icon` | Custom icon/illustration in the dropzone |
| `hint` | Custom hint text below the dropzone label |
| `file-item` | Custom file row template (receives file data via part attributes) |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-change` | `{ files: File[] }` | Yes | No | Fired when the file selection changes |
| `mj-file-add` | `{ file: File }` | Yes | Yes | Fired when a file is added; cancel to reject |
| `mj-file-remove` | `{ file: File }` | Yes | No | Fired when a file is removed from the list |
| `mj-file-error` | `{ file: File, error: "type" \| "size" \| "count" }` | Yes | No | Fired when a file fails validation |
| `mj-upload-progress` | `{ file: File, loaded: number, total: number, percent: number }` | Yes | No | Fired during upload (if `upload-url` set) |
| `mj-upload-success` | `{ file: File, response: unknown }` | Yes | No | Fired when upload completes |
| `mj-upload-error` | `{ file: File, error: Error }` | Yes | No | Fired when upload fails |
| `mj-drag-enter` | `{}` | Yes | No | Fired when files are dragged into the dropzone |
| `mj-drag-leave` | `{}` | Yes | No | Fired when drag leaves the dropzone |

## 9. CSS parts & custom properties
**Parts:** `dropzone`, `dropzone-icon`, `dropzone-label`, `dropzone-hint`, `choose-button`, `file-list`, `file-item`, `file-preview`, `file-name`, `file-size`, `file-status`, `file-progress`, `file-remove`, `error`

**Custom properties:**
| Property | Default token | Description |
|----------|---------------|-------------|
| `--mj-file-picker-dropzone-min-height` | `8rem` | Minimum height of the dropzone area |
| `--mj-file-picker-dropzone-border` | `2px dashed --mj-color-border` | Dropzone border style |
| `--mj-file-picker-dropzone-active-border` | `2px dashed --mj-color-accent` | Border when file is dragged over |
| `--mj-file-picker-dropzone-active-bg` | `--mj-color-selected-subtle` | Background when file is dragged over |
| `--mj-file-picker-preview-size` | `3rem` | Width and height of image thumbnails |
| `--mj-file-picker-border-radius` | `--mj-radius-md` | Dropzone corner radius |

## 10. States
| State | Visual effect | ARIA effect |
|-------|--------------|-------------|
| Default (empty) | Dropzone with icon and label | — |
| Drag over | Highlighted border and background | Live region: "Drop files to upload" |
| Files selected | File list shown | — |
| File uploading | Progress bar per item | `aria-valuenow` on progress |
| File upload success | Success icon on item | Live region: "[filename] uploaded" |
| File upload error | Error icon and message on item | Live region: "[filename] upload failed" |
| File validation error | Error message below dropzone | Error live region per failed file |
| Disabled | Muted dropzone; no interactions | `aria-disabled="true"`; `disabled` on choose button |
| Invalid | Error border; error message | `aria-invalid="true"` |

## 11. Behavior & interactions
- Clicking the dropzone or the "Choose files" button opens the native file dialog.
- Files dragged over the dropzone trigger the `drag-over` state; dropping adds them to the file list.
- Each added file is validated against `accept`, `max-size`, and `max-files`; invalid files fire `mj-file-error` and are rejected (not added to the list); the error reason is shown inline.
- Valid files are added to the file list; `mj-change` fires with the updated `files` array.
- If `upload-url` is set, valid files begin uploading immediately via `fetch` with a `FormData` body.
- Removing a file from the list fires `mj-file-remove`; if that file was uploading, the upload is aborted.
- In single-file mode, adding a new file replaces the previous file.
- Image files (detected by MIME type starting with `image/`) generate a thumbnail via `URL.createObjectURL`.

## 12. Keyboard interaction
| Key | Focus on | Action |
|-----|----------|--------|
| `Enter` / `Space` | Dropzone or choose button | Open native file dialog |
| `Tab` | — | Move through choose button and each file item's remove button |
| `Enter` / `Space` | File remove button | Remove that file from the list |
| `Delete` / `Backspace` | Focused file item | Remove that file from the list |

## 13. Accessibility
- Dropzone container has `role="region"` with `aria-label` (e.g., "File upload dropzone").
- The "Choose files" button is a `<button>` with a clear `aria-label` that includes what types are accepted.
- The hidden native `<input type="file">` is programmatically associated and triggered by the button; it is `aria-hidden="true"`.
- Each file item in the list has an accessible name combining the file name and its status.
- Remove buttons have `aria-label="Remove [filename]"`.
- Upload progress bars use `role="progressbar"` with `aria-valuenow`, `aria-valuemin="0"`, `aria-valuemax="100"`, and `aria-label="[filename] upload progress"`.
- Drag-enter state announces via a polite live region: "Drop files here to upload".
- File add/remove/error/success events announce via polite live region.
- Minimum target size for the remove button: 44 × 44 px.

## 14. Form participation
- Form-associated via `ElementInternals`; each selected file is appended to `FormData` as `name=file`.
- If `upload-url` is used and files are uploaded eagerly, the component may instead submit server-returned file identifiers.
- `required`: `validity.valueMissing` when `files` is empty.
- On form reset, all selected files are cleared.

## 15. Internationalization & RTL
- `label` and `dropzone-label` attributes are author-supplied and should be translated.
- The component contains default English strings for the choose button and dropzone label; these are overridable via the `label` and `dropzone-label` attributes.
- Error messages for type/size/count violations are exposed via `validationMessage`; localizable via `setCustomValidity`.
- In RTL, the dropzone icon and text mirror layout; the file list items mirror.

## 16. Progressive enhancement / SSR
- Server renders `<input type="file" name="..." accept="..." multiple>` inside `<mj-file-picker>`.
- Before upgrade the native input is functional.
- On upgrade, the native input is hidden (`aria-hidden`, moved off-screen); the drag-and-drop zone is built; the native input is triggered programmatically on choose-button click.
- Without scripting, the native `<input type="file">` renders and functions normally.

## 17. Dependencies
- Section 6: Registry/base element, design tokens, form-association helper, live-region service.
- `URL.createObjectURL` — for image preview generation (platform API).
- `fetch` / `XMLHttpRequest` — for immediate upload mode.

## 18. Edge cases & error handling
- File larger than `max-size`: rejected with `mj-file-error`; error shown below dropzone.
- File type not in `accept`: rejected; browser `accept` attribute alone is insufficient (authors can bypass it); the component also validates client-side.
- `max-files` exceeded: excess files rejected with `mj-file-error`; error shown.
- Duplicate file (same name + size + lastModified): allowed by default; deduplicate behavior controlled by a `no-duplicates` attribute.
- Network failure during upload: `mj-upload-error` fires; retry button shown per item.
- Drag-and-drop of a folder: only files within are extracted (via `DataTransferItem.webkitGetAsEntry`); the folder itself is not added.
- Very large image for preview: thumbnail generated at a capped resolution using a canvas; the original `File` object is unchanged.

## 19. Acceptance criteria
- [ ] Clicking the choose button opens the native file dialog; selected files appear in the list.
- [ ] Dragging files onto the dropzone adds them to the list; `mj-change` fires.
- [ ] Files violating `accept`, `max-size`, or `max-files` are rejected; `mj-file-error` fires with correct `error` type.
- [ ] Remove button removes the file from `files` array; `mj-file-remove` fires.
- [ ] Image files generate thumbnail previews.
- [ ] If `upload-url` is set, files upload immediately; `mj-upload-progress` and `mj-upload-success`/`mj-upload-error` fire.
- [ ] `required` with empty `files` fails `checkValidity()`.
- [ ] `role="progressbar"` with correct ARIA attributes on upload progress bars.
- [ ] axe-core reports zero violations in empty, selected, uploading, and error states.
- [ ] Without scripting, native `<input type="file">` is functional.

## 20. Open questions
- Should the component support chunked/resumable uploads, or only simple single-request uploads?
- Should `mj-file-add` being cancelable allow the author to return a transformed `File` object from the event?
- How should file ordering be managed when new files are added to an existing list — prepend, append, or allow drag-to-reorder?
