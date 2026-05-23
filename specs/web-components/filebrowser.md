# File Browser Spec

- **Tag:** `<mj-file-browser>`
- **Class / file:** `FileBrowser` / `filebrowser.js`
- **Category:** Application & productivity components
- **Primary or Variant:** Primary
- **Synonyms covered:** Folder tree, File grid, Preview pane
- **Phase:** P2
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose
`<mj-file-browser>` is a three-pane file system navigator composing a folder tree on the left, a file grid or list in the center, and an optional preview pane on the right. It provides a unified selection model, breadcrumb path navigation, context menu actions, and keyboard navigation across all three panes.

## 2. When to use / when not to use
Use to expose a hierarchical file or asset store to users who need to browse, select, preview, and act on files (CMS asset browsers, cloud storage UIs, media libraries). Do not use for simple single-file upload — use `<mj-dropzone>`. Do not use for a flat list of documents without hierarchy — use `<mj-data-table>`.

## 3. Anatomy
- **root** — outer `<div>` with `role="application"` and `aria-label`.
- **breadcrumb nav** — `<mj-breadcrumb>` spanning the full width above the panes.
- **folder tree pane** — `<mj-sidenav>`-styled panel hosting a `<mj-tree-selector>` for folders.
- **file pane** — center region with a view-mode toggle; renders either `<mj-data-table>` (list) or a CSS-Grid-based icon grid.
- **preview pane** — end-side collapsible panel showing `<mj-image>`, `<mj-media-player>`, a text preview, or a metadata card depending on file type.
- **toolbar** — `<mj-toolbar>` above the file pane with view toggle, sort, and action buttons.
- **context menu** — `<mj-context-menu>` on right-click or context-menu key on a file/folder item.
- **split handles** — `<mj-split-pane>` separators between the three panes; keyboard resizable.
- **status bar strip** — file count and selection count at the bottom.

## 4. Variants & modes
| Variant / mode | Attribute | Behavior difference |
|----------------|-----------|---------------------|
| Three-pane | (default) | Tree + file grid + preview |
| Two-pane | `preview="none"` | Tree + file grid only |
| Grid view | `view="grid"` | Files displayed as icon grid with name labels |
| List view | `view="list"` (default) | Files in a sortable `<mj-data-table>` |
| Detail view | `view="details"` | List with additional metadata columns |

## 5. Attributes
| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `view` | `"list"\|"grid"\|"details"` | `"list"` | Yes | File pane view mode |
| `preview` | `"auto"\|"none"` | `"auto"` | Yes | Preview pane visibility mode |
| `preview-open` | boolean | `true` | Yes | Whether the preview pane is currently visible |
| `tree-open` | boolean | `true` | Yes | Whether the folder tree pane is visible |
| `label` | string | `"File browser"` | Yes | Accessible name for the component root |
| `selection-mode` | `"single"\|"multi"` | `"multi"` | Yes | File selection mode |
| `show-hidden` | boolean | `false` | Yes | Include hidden files (names starting with `.`) |

## 6. Properties
| Property | Type | Description |
|----------|------|-------------|
| `dataSource` | `FileBrowserDataSource` | Adapter providing `listDir(path)`, `stat(path)`, `getPreview(path)` |
| `currentPath` | `string` | Current directory path; setting it navigates to that directory |
| `selectedFiles` | `FileEntry[]` | Currently selected files: `{ path, name, type, size, modified }` |
| `contextMenuItems` | `MenuItem[]` | Additional items injected into the context menu |

## 7. Slots
| Slot | Description |
|------|-------------|
| `toolbar-actions` | Additional `<mj-button>` items appended to the toolbar |
| `preview-{mimeType}` | Custom preview renderer for a specific MIME type (receives `file` via context) |
| `empty` | Empty state shown when a directory has no files |

## 8. Events
| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-file-open` | `{ file: FileEntry }` | Yes | No | Fires on double-click or Enter on a file |
| `mj-folder-navigate` | `{ path: string }` | Yes | No | Fires when the user navigates into a folder |
| `mj-selection-change` | `{ selectedFiles: FileEntry[] }` | Yes | No | Fires when file selection changes |
| `mj-view-change` | `{ view: string }` | Yes | No | Fires when the view mode changes |
| `mj-context-action` | `{ action: string, files: FileEntry[] }` | Yes | No | Fires when a context menu action is activated |

## 9. CSS parts & custom properties
**Parts:** `root`, `breadcrumb`, `tree-pane`, `file-pane`, `preview-pane`, `toolbar`, `file-grid`, `file-item`, `file-icon`, `file-name`, `split-handle-tree`, `split-handle-preview`, `status-strip`.

| Custom property | Default | Description |
|-----------------|---------|-------------|
| `--mj-fb-tree-width` | `220px` | Initial folder tree pane width |
| `--mj-fb-preview-width` | `300px` | Initial preview pane width |
| `--mj-fb-grid-item-size` | `96px` | Icon size in grid view |
| `--mj-fb-grid-gap` | `var(--mj-space-3)` | Gap between grid items |
| `--mj-fb-bg` | `var(--mj-color-surface-1)` | Component background |
| `--mj-fb-border` | `var(--mj-border-subtle)` | Pane separator border |

## 10. States
- **default** — three panes visible; directory loaded; no selection.
- **loading** — directory contents loading; `<mj-skeleton-loader>` in the file pane.
- **empty** — directory has no files; empty state shown.
- **file-selected** — one or more files selected; preview pane shows first selection's preview; toolbar actions enabled.
- **multi-selected** — multiple files selected; preview pane shows "N items selected" summary.
- **folder-selected** — a folder is highlighted in the tree; file pane shows its contents.
- **drag-reorder** — items being dragged (if consumer enables drag-move via context menu).

## 11. Behavior & interactions
Clicking a folder in the tree pane calls `dataSource.listDir(path)`, updates `currentPath`, and re-renders the file pane. The breadcrumb updates to reflect the new path; each breadcrumb segment is a clickable link that navigates up. Clicking a file selects it; double-clicking (or Enter) emits `mj-file-open`. In multi-selection mode, `Shift+Click` extends selection and `Ctrl/Cmd+Click` toggles individual items. The preview pane calls `dataSource.getPreview(path)` for the selected file and renders the appropriate preview component. Pane widths are persisted to `localStorage`. `F6` cycles keyboard focus between the three panes.

## 12. Keyboard interaction
| Key | Action |
|-----|--------|
| `F6` | Cycle focus between folder tree, file pane, and preview pane |
| `ArrowUp` / `ArrowDown` (tree) | Navigate folder tree items |
| `ArrowRight` (tree) | Expand a collapsed folder |
| `ArrowLeft` (tree) | Collapse an expanded folder or go to parent |
| `Enter` (tree folder) | Navigate into folder; update file pane |
| `ArrowUp` / `ArrowDown` (file list) | Move selection |
| `ArrowLeft` / `ArrowRight` (file grid) | Move selection across grid columns |
| `Enter` (file) | Open file; emit `mj-file-open` |
| `Space` (file) | Toggle selection without navigating |
| `Shift+Arrow` | Extend selection |
| `Ctrl+A` / `Cmd+A` | Select all files in current directory |
| `Delete` | Trigger delete action on selected files via context |
| `F2` | Rename selected file (opens inline rename) |
| `Context menu key` | Open context menu for selected file(s) |

## 13. Accessibility
Root carries `role="application"` with `aria-label`. The folder tree is a `<mj-tree-selector>` with `role="tree"`. The file pane in list/details mode is a `<mj-data-table>` with `role="grid"`. In icon grid mode, the grid is a `<div role="listbox" aria-multiselectable="true">` with each item as `role="option"`. Selection changes are announced via a polite live region: "3 items selected". `F6` transitions are announced: "Focus moved to Preview pane". The preview pane has `role="region"` with `aria-label="File preview"`. Context menu follows the APG Menu pattern. Breadcrumb follows the APG Breadcrumb pattern with `aria-current="page"` on the current segment.

## 14. Form participation
N/A in isolation. When embedded inside a `<form>` with a `name` attribute, the component can act as a form-associated file selector; selected file paths are contributed to `FormData` as a newline-separated string.

## 15. Internationalization & RTL
All labels, toolbar button titles, and empty-state messages are localizable. File sizes formatted with `Intl.NumberFormat`. Dates formatted with `Intl.DateTimeFormat`. In RTL, the folder tree moves to the inline-end side and the preview pane to the inline-start side.

## 16. Progressive enhancement / SSR
Server renders a styled `<nav>` for the breadcrumb and a `<ul>` for the directory listing with `<a>` links. Without JS, users can navigate by following links (directory listing pattern). On upgrade the component replaces the list with the interactive three-pane layout.

## 17. Dependencies
- **Foundations:** Registry + base element helper, Design-token stylesheet, Overlay/positioning engine, Focus utilities, Live-region/announcement service, Data-source adapter interface, Collection/virtualization utility.
- **Components:** `<mj-tree-selector>`, `<mj-data-table>`, `<mj-breadcrumb>`, `<mj-toolbar>`, `<mj-split-pane>`, `<mj-context-menu>`, `<mj-image>`, `<mj-media-player>`, `<mj-skeleton-loader>`, `<mj-empty-state>`, `<mj-button>`.

## 18. Edge cases & error handling
- `dataSource.listDir` fails: error alert shown in the file pane; tree node marked with error icon.
- Very large directories (10,000+ files): file pane virtualizes using the Collection utility.
- File with unknown MIME type: preview pane shows a generic file icon and metadata card only.
- File renamed externally between listing and open: `mj-file-open` consumer receives stale path; consumer must handle not-found from the server.
- Breadcrumb path too long for available width: middle segments truncated with a `…` overflow menu.

## 19. Acceptance criteria
- [ ] Clicking a folder updates the file pane and breadcrumb; `mj-folder-navigate` fires.
- [ ] File selection in multi-mode: Shift/Ctrl extend correctly; `mj-selection-change` fires.
- [ ] Double-click and Enter both emit `mj-file-open`.
- [ ] `F6` cycles focus between panes and announces the destination.
- [ ] Preview pane shows type-appropriate preview on selection.
- [ ] Pane widths persisted to and restored from `localStorage`.
- [ ] Context menu opens on right-click and context-menu key.
- [ ] Axe scan reports zero violations in list, grid, and details views.
- [ ] Light, dark, high-contrast, and RTL rendering verified.

## 20. Open questions
- Should cut/copy/paste file operations be in scope for P2 or deferred?
- Should drag-and-drop file move between folders be supported, with a keyboard alternative?
