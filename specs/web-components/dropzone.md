# Dropzone Spec

- **Tag:** `<mj-dropzone>`
- **Class / file:** `Dropzone` / `dropzone.js`
- **Category:** Application & productivity components
- **Primary or Variant:** Primary
- **Synonyms covered:** Upload dropzone, Drag-and-drop upload zone
- **Phase:** P2
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-dropzone>` is a drag-and-drop file upload zone that also provides a keyboard and click alternative via an embedded file picker. It handles type and size validation, shows per-file progress and error states, and announces all state changes to screen readers via live regions. It is form-associated and contributes selected files to `FormData`.

## 2. When to use / when not to use
Use when users need to upload one or more files, with an invitation to drag files over the target area. Do not use for selecting files without an upload intent — use `<mj-file-picker>`. Do not use for a single-file "avatar upload" thumbnail — use `<mj-avatar>` with its built-in upload slot.

## 3. Anatomy
- **drop target** — large bordered region that receives drag events; visually distinct on drag-over.
- **icon** — decorative upload-cloud or file icon; slotable.
- **instruction text** — "Drag files here or" prompt text.
- **browse button** — `<mj-button>` that opens the underlying `<input type="file">`.
- **constraint text** — accepted types and max size displayed below the button.
- **file list** — `<ul>` of accepted files with name, size, progress bar, and remove button.
- **error list** — `<mj-alert severity="error">` items for rejected files with reason.
- **live region** — hidden `<div role="status" aria-live="polite">` for all announcements.
- **hidden file input** — `<input type="file" tabindex="-1">` for the keyboard/click path.

## 4. Variants & modes
| Variant / mode | Attribute | Behavior difference |
|----------------|-----------|---------------------|
| Default | (none) | Full-size bordered drop zone with instruction text |
| Compact | `compact` | Smaller zone; icon and instruction on one line |
| Single file | `multiple="false"` | Accepts only one file; replaces on second drop |
| Inline list | `show-list` (default `true`) | Shows the accepted file list within the component |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `accept` | string | `""` | Yes | MIME types or extensions (same syntax as `<input type=file>`) |
| `multiple` | boolean | `true` | Yes | Allow multiple files |
| `max-size` | number | `0` | Yes | Max file size in bytes per file; `0` = unlimited |
| `max-files` | number | `0` | Yes | Max number of files; `0` = unlimited |
| `disabled` | boolean | `false` | Yes | Disables all interaction |
| `show-list` | boolean | `true` | Yes | Shows accepted file list below the drop zone |
| `compact` | boolean | `false` | Yes | Compact layout variant |
| `label` | string | `"File upload"` | Yes | Accessible name for the region |
| `browse-label` | string | `"Browse files"` | Yes | Label for the browse button |
| `drag-label` | string | `"Drag and drop files here, or"` | Yes | Instruction text |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `files` | `FileEntry[]` | Current accepted files: `{ id, file, status: "queued"\|"uploading"\|"done"\|"error", progress: number, error?: string }` |
| `rejectedFiles` | `RejectedFile[]` | Files that failed validation: `{ file, reason: string }` |

## 7. Slots
| Slot | Description |
|------|-------------|
| `icon` | Custom upload icon; defaults to a built-in cloud-upload SVG |
| `instructions` | Replaces the default instruction text |
| `file-actions` | Additional action buttons per file in the file list (receives `file` via context) |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-files-added` | `{ files: FileEntry[] }` | Yes | No | Fires when accepted files are added via drop or browse |
| `mj-files-rejected` | `{ rejectedFiles: RejectedFile[] }` | Yes | No | Fires when files fail type/size/count validation |
| `mj-file-remove` | `{ fileId: string, file: File }` | Yes | No | Fires when a file is removed from the list |
| `mj-drag-enter` | `{}` | Yes | No | Fires when a drag enters the drop target |
| `mj-drag-leave` | `{}` | Yes | No | Fires when a drag leaves the drop target |

## 9. CSS parts & custom properties
**Parts:** `root`, `drop-target`, `icon`, `instructions`, `browse-button`, `constraint-text`, `file-list`, `file-item`, `file-name`, `file-size`, `file-progress`, `file-remove`, `file-error`, `error-list`.

| Custom property | Default | Description |
|-----------------|---------|-------------|
| `--mj-dropzone-min-height` | `180px` | Minimum height of the drop target |
| `--mj-dropzone-border` | `2px dashed var(--mj-color-border)` | Border of the drop target |
| `--mj-dropzone-border-dragover` | `2px dashed var(--mj-color-accent)` | Border when drag is over |
| `--mj-dropzone-bg` | `var(--mj-color-surface-1)` | Background of the drop target |
| `--mj-dropzone-bg-dragover` | `var(--mj-color-accent-subtle)` | Background when drag is over |
| `--mj-dropzone-radius` | `var(--mj-radius-md)` | Border radius |

## 10. States
- **default** — idle; dashed border.
- **drag-over** — a drag event is over the zone; accent border and background; `aria-dropeffect="copy"`.
- **drag-invalid** — dragged files fail type/size/count check during drag; red border; `aria-dropeffect="none"`.
- **disabled** — `aria-disabled="true"`; no pointer or drop events processed; visually dimmed.
- **has-files** — file list section visible below the zone.
- **file-uploading** — individual file has progress bar; `aria-valuenow` on the progress element.
- **file-error** — individual file shows error message with `aria-live="assertive"` announcement.
- **file-done** — individual file shows success checkmark.

## 11. Behavior & interactions
`dragenter`, `dragover`, `dragleave`, and `drop` are handled on the drop target. On `drop`, files are extracted from `event.dataTransfer.files`, validated against `accept`, `max-size`, `max-files`, and `multiple`. Accepted files are added to `files`; rejected files go to `rejectedFiles`; both events fire. The consumer is responsible for actual upload logic; it sets `file.status` and `file.progress` on the `FileEntry` objects in `files` and the component re-renders accordingly. The browse button triggers `input.click()` on the hidden file input; the file input's `change` event feeds the same validation pipeline. `multiple="false"` replaces the existing file list with the new file on each add.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `Tab` | Focuses the browse button (primary tab stop in the zone) |
| `Enter` / `Space` on browse button | Opens the file picker dialog |
| `Tab` to file list | Focuses first file item's remove button |
| `Delete` / `Backspace` on remove button | Removes the file; fires `mj-file-remove`; focus moves to next item or browse button |
| `Escape` | Cancels an in-progress drag if supported by the browser |

## 13. Accessibility
The drop target region has `role="region"` and `aria-label` from the `label` attribute. During drag, `aria-dropeffect="copy"` is set on the target; for invalid drags, `aria-dropeffect="none"`. The browse button is the sole keyboard entry point for the zone; the hidden file input is `tabindex="-1"` and `aria-hidden="true"`. All state changes (files added, files rejected, upload progress, upload complete, upload error) are announced via the polite live region. File remove announcements use assertive politeness. Each file's progress bar carries `role="progressbar"`, `aria-valuenow`, `aria-valuemin="0"`, `aria-valuemax="100"`, and `aria-label="Uploading {filename}"`.

## 14. Form participation
The component is form-associated via `ElementInternals`. On form submission it sets the `FormData` entry using `setFormValue` with the `files` array. `name` attribute required for form participation. Constraint validation: if `required` is set and `files` is empty, the element is invalid with message "Please select a file."

## 15. Internationalization & RTL
All user-visible strings (`drag-label`, `browse-label`, `constraint-text` template, announcement messages) are overridable via attributes or the localization hook. File sizes are formatted with `Intl.NumberFormat` using SI prefixes (KB, MB, GB). In RTL, the layout of icon + instructions reverses; the file list is right-aligned.

## 16. Progressive enhancement / SSR
Server renders an `<input type="file">` with `name`, `accept`, and `multiple` attributes inside a `<label>`. Without JS users can select files and submit the form normally. On upgrade the component enhances the native input, adds the drop zone UI, and intercepts the form submission for progress tracking.

## 17. Dependencies
- **Foundations:** Registry + base element helper, Design-token stylesheet, Form-association helper, Live-region/announcement service, Localization/formatting hook.
- **Components:** `<mj-button>`, `<mj-progress>`, `<mj-alert>`, `<mj-chip>` (file tag display).

## 18. Edge cases & error handling
- Drop of a folder: `webkitGetAsEntry()` traversal attempted; files extracted recursively up to `max-files`.
- Zero-byte file: accepted unless the consumer adds a `min-size` check; no built-in rejection.
- `accept` mismatch detected only by MIME type, not extension: extension-only fallback check applied.
- `max-files` exceeded in a single drop: first N files accepted; remainder rejected; single `mj-files-rejected` event lists all.
- Drag from another browser tab: `dataTransfer.files` may be empty; dropzone shows "Cannot determine file type" and rejects gracefully.
- File removed while upload in progress: consumer must abort the upload; `mj-file-remove` fires so consumer can cancel.

## 19. Acceptance criteria
- [ ] `mj-files-added` fires with correctly validated `FileEntry[]` on drop and on browse.
- [ ] `mj-files-rejected` fires for each validation failure with `reason` string.
- [ ] `aria-dropeffect` toggles correctly during valid and invalid drags.
- [ ] Browse button opens file picker and feeds the same pipeline.
- [ ] Progress bar reflects consumer-set `progress` value; `aria-valuenow` accurate.
- [ ] Form-associated: files in `FormData` under `name`.
- [ ] `required` + empty files: form submission blocked with validation message.
- [ ] Live region announcements for add, reject, complete, and error.
- [ ] Axe scan reports zero violations.
- [ ] Light, dark, high-contrast, and RTL rendering verified.

## 20. Open questions
- Should the component provide a built-in upload mechanism (fetch + progress) configurable via an `upload-url` attribute, or remain purely UI?
- Should folder drag-and-drop be in scope for the initial P2 delivery?
