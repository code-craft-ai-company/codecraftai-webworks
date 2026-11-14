/*
 * mjfilebrowser.js
 *
 * <mj-file-browser> -- three-pane file system navigator with folder tree,
 * file grid/list pane, and optional preview pane. Unified selection model,
 * breadcrumb navigation, and keyboard support.
 */

import { MjElement } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";

const STYLES = `
:host {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  background: var(--mj-fb-bg, var(--mj-bg));
  border: 1px solid var(--mj-fb-border, var(--mj-border));
  border-radius: var(--mj-radius-md);
  overflow: hidden;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
}

/*
 * As a dock band the host must not claim the whole dock container along the
 * axis the band consumes (see static/styles/base.css, Docking).
 */
:host([dock="top"]),
:host([dock="bottom"]) {
  block-size: auto;
}

:host([dock="start"]),
:host([dock="end"]) {
  inline-size: auto;
}

.fb-breadcrumb {
  display: flex;
  align-items: center;
  gap: var(--mj-space-1);
  padding: var(--mj-space-2) var(--mj-space-3);
  border-bottom: 1px solid var(--mj-fb-border, var(--mj-border));
  background: var(--mj-surface);
  font-size: var(--mj-font-size-xs);
  flex-wrap: wrap;
  min-height: var(--mj-control-height-sm);
}

.breadcrumb-seg {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--mj-accent);
  font: inherit;
  font-size: var(--mj-font-size-xs);
  padding: 0;
}

.breadcrumb-seg:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  border-radius: var(--mj-radius-sm);
}

.breadcrumb-sep { color: var(--mj-text-muted); }

.fb-panes {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.tree-pane {
  width: var(--mj-fb-tree-width, 220px);
  border-inline-end: 1px solid var(--mj-fb-border, var(--mj-border));
  overflow-y: auto;
  background: var(--mj-surface);
  flex-shrink: 0;
}

:host([tree-open="false"]) .tree-pane { display: none; }

.file-pane {
  flex: 1;
  overflow-y: auto;
  background: var(--mj-bg);
  min-width: 0;
}

.preview-pane {
  width: var(--mj-fb-preview-width, 300px);
  border-inline-start: 1px solid var(--mj-fb-border, var(--mj-border));
  overflow-y: auto;
  background: var(--mj-surface);
  flex-shrink: 0;
}

.preview-pane[hidden] {
  display: none;
}

.fb-toolbar {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  padding: var(--mj-space-2) var(--mj-space-3);
  border-bottom: 1px solid var(--mj-fb-border, var(--mj-border));
  background: var(--mj-surface);
}

.view-btn {
  padding: var(--mj-space-1) var(--mj-space-2);
  background: none;
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-sm);
  cursor: pointer;
  font: inherit;
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text);
}

.view-btn[aria-pressed="true"] {
  background: var(--mj-accent);
  color: var(--mj-text-on-accent);
  border-color: var(--mj-accent);
}

.tree-item {
  display: flex;
  align-items: center;
  gap: var(--mj-space-1);
  padding: var(--mj-space-1) var(--mj-space-3);
  cursor: pointer;
  user-select: none;
  font-size: var(--mj-font-size-sm);
}

.tree-item:hover { background: var(--mj-bg-muted); }

.tree-item-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tree-expander {
  display: inline-block;
  inline-size: 1em;
  flex-shrink: 0;
  color: var(--mj-text-muted);
  font-size: var(--mj-font-size-xs);
  text-align: center;
}
.tree-item[aria-selected="true"] { background: var(--mj-bg-muted); color: var(--mj-accent); }
.tree-item:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: calc(-1 * var(--mj-focus-ring-offset));
}

.tree-expand-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0 var(--mj-space-1);
  color: var(--mj-text-muted);
  font-size: 0.6em;
  line-height: 1;
}

.file-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(var(--mj-fb-grid-item-size, 96px), 1fr));
  gap: var(--mj-fb-grid-gap, var(--mj-space-3));
  padding: var(--mj-space-3);
}

.file-list-table {
  width: 100%;
  border-collapse: collapse;
}

.file-list-table th, .file-list-table td {
  padding: var(--mj-space-2) var(--mj-space-3);
  text-align: start;
  border-bottom: 1px solid var(--mj-border);
  font-size: var(--mj-font-size-sm);
}

.file-list-table th {
  background: var(--mj-bg-subtle);
  font-weight: var(--mj-font-weight-medium);
  color: var(--mj-text-muted);
}

.file-list-table tr:hover td { background: var(--mj-bg-subtle); }

.file-list-table tr[aria-selected="true"] td {
  background: var(--mj-bg-muted);
}

.file-list-table tr:focus-visible td {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}

.file-grid-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--mj-space-1);
  padding: var(--mj-space-2);
  border-radius: var(--mj-radius-md);
  cursor: pointer;
  text-align: center;
  outline: none;
}

.file-grid-item:hover { background: var(--mj-bg-muted); }
.file-grid-item[aria-selected="true"] { background: var(--mj-bg-muted); }
.file-grid-item:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}

.file-icon {
  font-size: 2.5rem;
  line-height: 1;
}

.file-item-name {
  font-size: var(--mj-font-size-xs);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 90px;
}

.fb-status-strip {
  padding: var(--mj-space-1) var(--mj-space-3);
  border-top: 1px solid var(--mj-fb-border, var(--mj-border));
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
  background: var(--mj-surface);
  display: flex;
  gap: var(--mj-space-3);
}

.empty-state {
  padding: var(--mj-space-6);
  text-align: center;
  color: var(--mj-text-muted);
}

.empty-state.is-error { color: var(--mj-color-danger); }

.retry-btn {
  display: block;
  margin: var(--mj-space-2) auto 0;
  padding: var(--mj-space-1) var(--mj-space-3);
  background: var(--mj-surface);
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-sm);
  font: inherit;
  color: var(--mj-text);
  cursor: pointer;
}

.retry-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}

.file-pane[aria-busy="true"] {
  opacity: 0.6;
}

.file-pane:focus-visible,
.preview-pane:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: calc(-1 * var(--mj-focus-ring-width));
}

.preview-hint {
  color: var(--mj-text-muted);
  font-size: var(--mj-font-size-xs);
  margin: 0;
}

.preview-content {
  padding: var(--mj-space-3);
}

.preview-title {
  font-weight: var(--mj-font-weight-medium);
  margin-bottom: var(--mj-space-2);
  word-break: break-all;
}

.preview-meta {
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
  display: flex;
  flex-direction: column;
  gap: var(--mj-space-1);
}

.live-region {
  position: absolute;
  width: 1px; height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  clip-path: inset(50%);
  white-space: nowrap;
}
`;

const FILE_ICONS = {
  "folder": "\u{1F4C1}",
  "image": "\u{1F4F7}",
  "video": "\u{1F3A6}",
  "audio": "\u{1F3B5}",
  "pdf": "\u{1F4C4}",
  "default": "\u{1F4C4}"
};

const TREE_COLLAPSED_GLYPH = "▸";
const TREE_EXPANDED_GLYPH = "▾";

function getFileIcon(type) {
  if (type === "folder") {
    return FILE_ICONS.folder
  }
  if (typeof type === "string" && type.startsWith("image/")) {
    return FILE_ICONS.image
  }
  if (typeof type === "string" && type.startsWith("video/")) {
    return FILE_ICONS.video
  }
  if (typeof type === "string" && type.startsWith("audio/")) {
    return FILE_ICONS.audio
  }
  if (type === "application/pdf") {
    return FILE_ICONS.pdf
  }
  return FILE_ICONS.default
}

/* Bring a path to the canonical form: leading slash, no trailing slash. */
function normalisePath(path) {
  let text = typeof path === "string" ? path.trim() : ""
  if (text.startsWith("/") === false) {
    text = `/${text}`
  }
  if (text.length > 1) {
    text = text.replace(/\/+$/, "")
  }
  if (text.length === 0) {
    text = "/"
  }
  return text
}

function joinPath(base, name) {
  const joined = base === "/" ? `/${name}` : `${base}/${name}`
  return joined
}

export class MjFileBrowser extends MjElement {
  static tagName = "mj-file-browser";
  static styles = STYLES;
  static watched = ["view", "preview", "preview-open", "tree-open", "selection-mode", "show-hidden", "label"];

  constructor() {
    super()
    this._dataSource = null
    this._currentPath = "/"
    this._selectedFiles = []
    this._directoryContents = []

    /* The path whose listing `_directoryContents` holds, or null. */
    this._loadedPath = null
    this._loadFailed = false

    /* True while a listing request is in flight; the file pane shows a loading state. */
    this._loading = false

    /* Incremented per listing request; a response with an older number is stale. */
    this._navSequence = 0

    /*
     * Folder tree state by path:
     *   { path, name, parentPath, expanded, loaded, childPaths }
     * Filled from the folder entries of every listing the data source returns.
     */
    this._treeNodes = {}
    this._treeNodes["/"] = { path: "/", name: "/", parentPath: null, expanded: true, loaded: false, childPaths: [] }
    this._treeFocusPath = "/"

    /* Roving focus and range-selection anchor in the file pane, by item key. */
    this._focusedKey = null
    this._anchorKey = null

    this._panelFocusIndex = 0

    this._rootEl = null
    this._breadcrumbEl = null
    this._toolbarEl = null
    this._treePaneEl = null
    this._filePaneEl = null
    this._previewPaneEl = null
    this._itemCountEl = null
    this._selectionCountEl = null
  }

  render() {
    const markup = html`
      <div class="fb-root" role="application" part="root" style="display:contents">
        <nav class="fb-breadcrumb" part="breadcrumb" aria-label="${t("mj.fileBrowser.pathLabel")}"></nav>
        <div class="fb-toolbar" part="toolbar">
          <button class="view-btn" type="button" aria-pressed="false" data-view="list" aria-label="${t("mj.fileBrowser.listView")}">&#9776;</button>
          <button class="view-btn" type="button" aria-pressed="false" data-view="grid" aria-label="${t("mj.fileBrowser.gridView")}">&#9783;</button>
          <slot name="toolbar-actions"></slot>
        </div>
        <div class="fb-panes" part="panes">
          <div class="tree-pane" part="tree-pane" role="tree" aria-label="${t("mj.fileBrowser.foldersLabel")}"></div>
          <div class="file-pane" part="file-pane" role="group" aria-label="${t("mj.fileBrowser.filesLabel")}" tabindex="-1"></div>
          <div class="preview-pane" part="preview-pane" role="region" aria-label="${t("mj.fileBrowser.previewLabel")}" tabindex="-1" hidden></div>
        </div>
        <div class="fb-status-strip" part="status-strip">
          <span class="item-count">${t("mj.fileBrowser.itemCount", { count: 0 })}</span>
          <span class="selection-count"></span>
        </div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._rootEl = this.$(".fb-root")
    this._breadcrumbEl = this.$(".fb-breadcrumb")
    this._toolbarEl = this.$(".fb-toolbar")
    this._treePaneEl = this.$(".tree-pane")
    this._filePaneEl = this.$(".file-pane")
    this._previewPaneEl = this.$(".preview-pane")
    this._itemCountEl = this.$(".item-count")
    this._selectionCountEl = this.$(".selection-count")

    /* Delegated listeners: re-rendering a pane registers nothing new. */
    this.listen(this._toolbarEl, "click", this._onToolbarClick.bind(this))
    this.listen(this._breadcrumbEl, "click", this._onBreadcrumbClick.bind(this))
    this.listen(this._treePaneEl, "click", this._onTreeClick.bind(this))
    this.listen(this._treePaneEl, "keydown", this._onTreeKeydown.bind(this))
    this.listen(this._filePaneEl, "click", this._onFilePaneClick.bind(this))
    this.listen(this._filePaneEl, "dblclick", this._onFilePaneDblClick.bind(this))
    this.listen(this._filePaneEl, "keydown", this._onFilePaneKeydown.bind(this))
    this.listen(this._filePaneEl, "contextmenu", this._onFilePaneContextMenu.bind(this))
    this.listen(this, "keydown", this._onKeydown.bind(this))
    this.listen(this, "mj-context-select", this._onContextSelect.bind(this))

    /*
     * Rebuild every pane from the fields, so a reconnect shows the folder
     * the user was in rather than the root.
     */
    this._rootEl.setAttribute("aria-label", this.getAttribute("label") || t("mj.fileBrowser.label"))
    this._updateViewButtons()
    this._updateBreadcrumb()
    this._renderTree()

    if (this._dataSource !== null && this._loadedPath !== this._currentPath) {
      this._renderFilePane()
      this._loadDirectory()
    } else {
      this._renderFilePane()
    }
    this._renderPreview()

    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._filePaneEl === undefined || this._filePaneEl === null) {
      return
    }

    if (name === "view") {
      this._updateViewButtons()
      this._renderFilePane()
    } else if (name === "show-hidden") {
      this._dropHiddenFromSelection()
      this._renderTree()
      this._renderFilePane()
    } else if (name === "selection-mode") {
      if (this._selectionMode() === "single" && this._selectedFiles.length > 1) {
        this._setSelection([this._selectedFiles[0]])
      }
      this._renderFilePane()
    } else if (name === "preview" || name === "preview-open") {
      this._syncPreviewVisibility()
    } else if (name === "label") {
      this._rootEl.setAttribute("aria-label", newValue || t("mj.fileBrowser.label"))
    }
    return
  }

  /* ----- small state helpers ----- */

  _view() {
    const view = this.getAttribute("view") === "grid" ? "grid" : "list"
    return view
  }

  _selectionMode() {
    const mode = this.getAttribute("selection-mode") === "single" ? "single" : "multi"
    return mode
  }

  _itemKey(item) {
    const key = String(item.path || item.name)
    return key
  }

  _itemPath(item) {
    const path = item.path ? normalisePath(item.path) : joinPath(this._currentPath, String(item.name))
    return path
  }

  _isHidden(item) {
    const hidden = String(item.name || "").startsWith(".")
    return hidden
  }

  /* The items of the current folder that the file pane shows, in order. */
  _visibleItems() {
    let items = this._directoryContents
    if (this.hasAttribute("show-hidden") === false) {
      items = items.filter((item) => this._isHidden(item) === false)
    }
    return items
  }

  /*
   * Hidden items that are no longer shown leave the selection (and stop
   * being the focused item or the range anchor), so no action works on
   * files the user cannot see. Emits mj-selection-change only when the
   * selection actually changed.
   */
  _dropHiddenFromSelection() {
    if (this.hasAttribute("show-hidden") === true) {
      return
    }

    const visible = this._selectedFiles.filter((item) => this._isHidden(item) === false)
    if (visible.length !== this._selectedFiles.length) {
      this._setSelection(visible)
    }

    const visibleKeys = this._visibleItems().map((item) => this._itemKey(item))
    if (this._focusedKey !== null && visibleKeys.indexOf(this._focusedKey) < 0) {
      this._focusedKey = null
    }
    if (this._anchorKey !== null && visibleKeys.indexOf(this._anchorKey) < 0) {
      this._anchorKey = null
    }
    return
  }

  _isSelected(item) {
    const key = this._itemKey(item)
    const selected = this._selectedFiles.some((file) => this._itemKey(file) === key)
    return selected
  }

  _indexOfKey(items, key) {
    let found = -1
    for (let i = 0; i < items.length; i = i + 1) {
      if (this._itemKey(items[i]) === key) {
        found = i
        break
      }
    }
    return found
  }

  /* ----- toolbar ----- */

  _updateViewButtons() {
    const view = this._view()
    const btns = this._toolbarEl.querySelectorAll(".view-btn")
    for (let i = 0; i < btns.length; i = i + 1) {
      const btn = btns[i]
      const btnView = btn.getAttribute("data-view")
      btn.setAttribute("aria-pressed", btnView === view ? "true" : "false")
    }
    return
  }

  _onToolbarClick(event) {
    const btn = event.target.closest(".view-btn")
    if (btn === null) {
      return
    }
    const view = btn.getAttribute("data-view")
    if (view !== this._view()) {
      /* The attribute handler redraws the buttons and the pane. */
      this.setAttribute("view", view)
    }
    this.emit("mj-view-change", { view: view })
    return
  }

  /* ----- pane focus cycling ----- */

  _onKeydown(event) {
    if (event.key === "F6") {
      event.preventDefault()
      this._cyclePanelFocus(event.shiftKey === true ? -1 : 1)
    }
    return
  }

  /*
   * Move focus to the next visible pane. Hidden panes are skipped, so the
   * announcement always names a pane that actually received focus. `name`
   * identifies a pane; `label` is the localized name that is announced.
   */
  _cyclePanelFocus(step) {
    const panels = []
    if (this.getAttribute("tree-open") !== "false") {
      panels.push({ name: "Folder tree", label: t("mj.fileBrowser.panelTree"), focus: () => this._focusTree() })
    }
    panels.push({ name: "Files", label: t("mj.fileBrowser.panelFiles"), focus: () => this._focusFilePane() })
    if (this._previewPaneEl.hidden === false) {
      panels.push({ name: "Preview", label: t("mj.fileBrowser.panelPreview"), focus: () => this._previewPaneEl.focus() })
    }

    const active = this.shadowRoot.activeElement
    let current = -1
    if (active !== null) {
      if (this._treePaneEl.contains(active) === true) {
        current = panels.findIndex((panel) => panel.name === "Folder tree")
      } else if (this._filePaneEl.contains(active) === true) {
        current = panels.findIndex((panel) => panel.name === "Files")
      } else if (this._previewPaneEl.contains(active) === true) {
        current = panels.findIndex((panel) => panel.name === "Preview")
      }
    }

    /* From outside every pane, F6 starts at the first pane and Shift+F6 at the last. */
    let next = 0
    if (current < 0) {
      next = step > 0 ? 0 : panels.length - 1
    } else {
      next = (current + step + panels.length) % panels.length
    }
    this._panelFocusIndex = next
    panels[next].focus()
    announce(t("mj.fileBrowser.focusMoved", { panel: panels[next].label }), "polite")
    return
  }

  _focusTree() {
    const item = this._treePaneEl.querySelector(".tree-item[tabindex='0']")
    if (item !== null) {
      item.focus()
    }
    return
  }

  _focusFilePane() {
    const item = this._filePaneEl.querySelector("[data-index][tabindex='0']")
    if (item !== null) {
      item.focus()
    } else {
      this._filePaneEl.focus()
    }
    return
  }

  /* ----- navigation and loading ----- */

  _navigate(path) {
    const target = normalisePath(path)
    this._currentPath = target
    this._focusedKey = null
    this._anchorKey = null
    this._treeFocusPath = target
    this._ensureTreePath(target)

    /* A selection belongs to the folder it was made in. */
    this._setSelection([])

    /*
     * The previous folder's items go at once: left on screen until the new
     * listing arrives they could still be opened, and an item without a
     * `path` would then resolve against the new folder.
     */
    if (this._dataSource !== null) {
      this._directoryContents = []
      this._loadedPath = null
      this._loadFailed = false
    }

    this._updateBreadcrumb()
    this._renderTree()
    this.emit("mj-folder-navigate", { path: target })

    if (this._dataSource !== null) {
      this._loadDirectory()
    }
    return
  }

  /*
   * Ask the data source for the current folder. Each request carries a
   * sequence number; a response that arrives after a newer request was
   * issued is dropped, so a slow folder cannot overwrite the current one.
   */
  _loadDirectory() {
    if (this._dataSource === null || this._filePaneEl === null) {
      return
    }

    this._navSequence = this._navSequence + 1
    const sequence = this._navSequence
    const path = this._currentPath

    this._loading = true
    this._filePaneEl.setAttribute("aria-busy", "true")
    this._renderFilePane()

    this._requestListing(path).then(
      (items) => {
        if (sequence === this._navSequence) {
          this._loading = false
          this._directoryContents = items
          this._loadedPath = path
          this._loadFailed = false
          this._recordFolders(path, items)
          this._filePaneEl.removeAttribute("aria-busy")
          this._renderTree()
          this._renderFilePane()
        }
      },
      (error) => {
        if (sequence === this._navSequence) {
          this._loading = false
          this._directoryContents = []
          this._loadedPath = null
          this._loadFailed = true
          this._filePaneEl.removeAttribute("aria-busy")
          this._renderFilePane()
          announce(t("mj.fileBrowser.loadFailed"), "assertive")
        }
      }
    )
    return
  }

  /* listDir may return an array or a promise, or throw; always yield a promise of an array. */
  _requestListing(path) {
    let request = null
    try {
      request = Promise.resolve(this._dataSource.listDir(path))
    } catch (error) {
      request = Promise.reject(error)
    }
    const listing = request.then((items) => {
      const list = Array.isArray(items) === true ? items : []
      return list
    })
    return listing
  }

  /* ----- breadcrumb ----- */

  _updateBreadcrumb() {
    if (this._breadcrumbEl === null) {
      return
    }
    const path = this._currentPath
    const segments = path === "/" ? ["/"] : ["/"].concat(path.replace(/^\//, "").split("/"))
    this._breadcrumbEl.textContent = ""

    for (let i = 0; i < segments.length; i = i + 1) {
      const seg = segments[i]
      const btn = document.createElement("button")
      btn.className = "breadcrumb-seg"
      btn.type = "button"
      btn.textContent = seg
      const targetPath = i === 0 ? "/" : "/" + segments.slice(1, i + 1).join("/")
      btn.setAttribute("data-path", targetPath)
      if (i === segments.length - 1) {
        btn.setAttribute("aria-current", "page")
      }
      this._breadcrumbEl.appendChild(btn)
      if (i < segments.length - 1) {
        const sep = document.createElement("span")
        sep.className = "breadcrumb-sep"
        sep.setAttribute("aria-hidden", "true")
        sep.textContent = "›"
        this._breadcrumbEl.appendChild(sep)
      }
    }
    return
  }

  _onBreadcrumbClick(event) {
    const btn = event.target.closest(".breadcrumb-seg")
    if (btn === null) {
      return
    }
    this._navigate(btn.getAttribute("data-path"))
    return
  }

  /* ----- folder tree ----- */

  /* Make sure `path` and each of its ancestors has a tree node, expanded down to it. */
  _ensureTreePath(path) {
    if (path === "/") {
      return
    }
    const segments = path.replace(/^\//, "").split("/")
    let parentPath = "/"

    for (let i = 0; i < segments.length; i = i + 1) {
      const nodePath = joinPath(parentPath, segments[i])
      const parent = this._treeNodes[parentPath]

      if (this._treeNodes[nodePath] === undefined) {
        this._treeNodes[nodePath] = {
          path: nodePath, name: segments[i], parentPath: parentPath,
          expanded: false, loaded: false, childPaths: []
        }
      }
      if (parent.childPaths.indexOf(nodePath) < 0) {
        parent.childPaths.push(nodePath)
      }
      parent.expanded = true
      parentPath = nodePath
    }
    return
  }

  /* Record the folders of a listing as the children of the tree node for `path`. */
  _recordFolders(path, items) {
    this._ensureTreePath(path)
    const node = this._treeNodes[path]
    const childPaths = []

    for (let i = 0; i < items.length; i = i + 1) {
      const item = items[i]
      if (item.type === "folder") {
        const childPath = item.path ? normalisePath(item.path) : joinPath(path, String(item.name))
        const existing = this._treeNodes[childPath]
        if (existing === undefined) {
          this._treeNodes[childPath] = {
            path: childPath, name: String(item.name), parentPath: path,
            expanded: false, loaded: false, childPaths: []
          }
        } else {
          existing.name = String(item.name)
          existing.parentPath = path
        }
        childPaths.push(childPath)
      }
    }

    node.childPaths = childPaths
    node.loaded = true
    return
  }

  /* The tree nodes currently shown, depth-first, each with its level. */
  _visibleTreeRows() {
    const rows = []
    const showHidden = this.hasAttribute("show-hidden")

    const visit = (path, level) => {
      const node = this._treeNodes[path]
      if (node === undefined) {
        return
      }
      if (level > 1 && showHidden === false && node.name.startsWith(".") === true) {
        return
      }
      rows.push({ node: node, level: level })
      if (node.expanded === true) {
        for (let i = 0; i < node.childPaths.length; i = i + 1) {
          visit(node.childPaths[i], level + 1)
        }
      }
      return
    }

    visit("/", 1)
    return rows
  }

  _renderTree() {
    if (this._treePaneEl === null) {
      return
    }

    const hadFocus = this.shadowRoot.activeElement !== null &&
      this._treePaneEl.contains(this.shadowRoot.activeElement) === true
    const rows = this._visibleTreeRows()

    let focusPath = this._treeFocusPath
    if (rows.some((row) => row.node.path === focusPath) === false) {
      focusPath = "/"
      this._treeFocusPath = focusPath
    }

    this._treePaneEl.textContent = ""

    for (let i = 0; i < rows.length; i = i + 1) {
      const node = rows[i].node
      const level = rows[i].level
      const isLeaf = node.loaded === true && node.childPaths.length === 0

      const itemEl = document.createElement("div")
      itemEl.className = "tree-item"
      itemEl.setAttribute("role", "treeitem")
      itemEl.setAttribute("aria-level", String(level))
      itemEl.setAttribute("aria-selected", node.path === this._currentPath ? "true" : "false")
      itemEl.setAttribute("tabindex", node.path === focusPath ? "0" : "-1")
      itemEl.setAttribute("data-path", node.path)
      itemEl.style.paddingInlineStart = `calc(var(--mj-space-3) + ${level - 1} * var(--mj-space-4))`
      if (isLeaf === false) {
        itemEl.setAttribute("aria-expanded", node.expanded === true ? "true" : "false")
      }

      const expanderEl = document.createElement("span")
      expanderEl.className = "tree-expander"
      expanderEl.setAttribute("aria-hidden", "true")
      if (isLeaf === false) {
        expanderEl.textContent = node.expanded === true ? TREE_EXPANDED_GLYPH : TREE_COLLAPSED_GLYPH
      }

      const labelEl = document.createElement("span")
      labelEl.className = "tree-item-label"
      labelEl.textContent = node.name

      itemEl.appendChild(expanderEl)
      itemEl.appendChild(labelEl)
      this._treePaneEl.appendChild(itemEl)
    }

    if (hadFocus === true) {
      this._focusTree()
    }
    return
  }

  _setTreeExpanded(path, expanded) {
    const node = this._treeNodes[path]
    if (node === undefined) {
      return
    }

    node.expanded = expanded
    this._renderTree()

    if (expanded === true && node.loaded === false && this._dataSource !== null) {
      /* Fetch the folder's children without navigating into it. */
      this._requestListing(path).then(
        (items) => {
          this._recordFolders(path, items)
          this._renderTree()
        },
        (error) => {
          node.expanded = false
          this._renderTree()
          announce(t("mj.fileBrowser.loadFailed"), "assertive")
        }
      )
    }
    return
  }

  _moveTreeFocus(path) {
    this._treeFocusPath = path
    const items = this._treePaneEl.querySelectorAll(".tree-item")
    for (let i = 0; i < items.length; i = i + 1) {
      const isTarget = items[i].getAttribute("data-path") === path
      items[i].setAttribute("tabindex", isTarget === true ? "0" : "-1")
      if (isTarget === true) {
        items[i].focus()
      }
    }
    return
  }

  _onTreeClick(event) {
    const itemEl = event.target.closest(".tree-item")
    if (itemEl === null) {
      return
    }
    const path = itemEl.getAttribute("data-path")
    const node = this._treeNodes[path]

    if (event.target.closest(".tree-expander") !== null && itemEl.hasAttribute("aria-expanded") === true) {
      this._treeFocusPath = path
      this._setTreeExpanded(path, node.expanded === false)
    } else {
      this._navigate(path)
    }
    return
  }

  /* APG tree view keys. */
  _onTreeKeydown(event) {
    const itemEl = event.target.closest(".tree-item")
    if (itemEl === null) {
      return
    }

    const path = itemEl.getAttribute("data-path")
    const node = this._treeNodes[path]
    const rows = this._visibleTreeRows()

    /* The item that has focus is the one a re-render must focus again. */
    this._treeFocusPath = path
    const position = rows.findIndex((row) => row.node.path === path)
    const isLeaf = node.loaded === true && node.childPaths.length === 0
    let handled = true

    if (event.key === "ArrowDown") {
      if (position < rows.length - 1) {
        this._moveTreeFocus(rows[position + 1].node.path)
      }
    } else if (event.key === "ArrowUp") {
      if (position > 0) {
        this._moveTreeFocus(rows[position - 1].node.path)
      }
    } else if (event.key === "Home") {
      this._moveTreeFocus(rows[0].node.path)
    } else if (event.key === "End") {
      this._moveTreeFocus(rows[rows.length - 1].node.path)
    } else if (event.key === "ArrowRight") {
      if (isLeaf === false && node.expanded === false) {
        this._setTreeExpanded(path, true)
      } else if (node.expanded === true && position < rows.length - 1 && rows[position + 1].level > rows[position].level) {
        this._moveTreeFocus(rows[position + 1].node.path)
      }
    } else if (event.key === "ArrowLeft") {
      if (isLeaf === false && node.expanded === true) {
        this._setTreeExpanded(path, false)
      } else if (node.parentPath !== null) {
        this._moveTreeFocus(node.parentPath)
      }
    } else if (event.key === "Enter" || event.key === " ") {
      this._navigate(path)
    } else {
      handled = false
    }

    if (handled === true) {
      event.preventDefault()
      event.stopPropagation()
    }
    return
  }

  /* ----- file pane ----- */

  _renderFilePane() {
    if (this._filePaneEl === null) {
      return
    }

    const hadFocus = this.shadowRoot.activeElement !== null &&
      this._filePaneEl.contains(this.shadowRoot.activeElement) === true
    const items = this._visibleItems()

    this._filePaneEl.textContent = ""

    if (this._loadFailed === true) {
      const errorEl = document.createElement("div")
      errorEl.className = "empty-state is-error"
      errorEl.setAttribute("role", "alert")
      errorEl.textContent = t("mj.fileBrowser.loadFailed")
      const retryBtn = document.createElement("button")
      retryBtn.className = "retry-btn"
      retryBtn.type = "button"
      retryBtn.textContent = t("mj.fileBrowser.retry")
      errorEl.appendChild(retryBtn)
      this._filePaneEl.appendChild(errorEl)
    } else if (this._loading === true && items.length === 0) {
      const loadingEl = document.createElement("div")
      loadingEl.className = "empty-state is-loading"
      loadingEl.textContent = t("core.loading")
      this._filePaneEl.appendChild(loadingEl)
    } else if (items.length === 0) {
      const emptyEl = document.createElement("div")
      emptyEl.className = "empty-state"
      const slotEl = document.createElement("slot")
      slotEl.name = "empty"
      slotEl.textContent = this._loadedPath === null ? t("mj.fileBrowser.noFiles") : t("mj.fileBrowser.emptyFolder")
      emptyEl.appendChild(slotEl)
      this._filePaneEl.appendChild(emptyEl)
    } else if (this._view() === "grid") {
      this._renderGrid(items)
    } else {
      this._renderList(items)
    }

    this._applyRovingTabindex()
    this._updateSelection()

    if (hadFocus === true) {
      this._focusFilePane()
    }
    return
  }

  _renderGrid(items) {
    const grid = document.createElement("div")
    grid.className = "file-grid"
    grid.setAttribute("part", "file-grid")
    grid.setAttribute("role", "listbox")
    grid.setAttribute("aria-multiselectable", this._selectionMode() === "multi" ? "true" : "false")
    grid.setAttribute("aria-label", t("mj.fileBrowser.filesLabel"))

    for (let i = 0; i < items.length; i = i + 1) {
      const item = items[i]
      const el = document.createElement("div")
      el.className = "file-grid-item"
      el.setAttribute("part", "file-item")
      el.setAttribute("role", "option")
      el.setAttribute("aria-selected", "false")
      el.setAttribute("tabindex", "-1")
      el.setAttribute("data-index", String(i))
      el.setAttribute("data-path", this._itemKey(item))
      el.setAttribute("data-type", item.type || "")
      el.innerHTML = String(html`
        <span class="file-icon" part="file-icon" aria-hidden="true">${getFileIcon(item.type)}</span>
        <span class="file-item-name" part="file-name" title="${item.name}">${item.name}</span>
      `)
      grid.appendChild(el)
    }

    this._filePaneEl.appendChild(grid)
    return
  }

  _renderList(items) {
    const table = document.createElement("table")
    table.className = "file-list-table"
    table.setAttribute("role", "grid")
    table.setAttribute("aria-multiselectable", this._selectionMode() === "multi" ? "true" : "false")
    table.setAttribute("aria-label", t("mj.fileBrowser.filesLabel"))
    table.innerHTML = String(html`
      <thead>
        <tr>
          <th scope="col">${t("mj.fileBrowser.columnName")}</th>
          <th scope="col">${t("mj.fileBrowser.columnSize")}</th>
          <th scope="col">${t("mj.fileBrowser.columnModified")}</th>
        </tr>
      </thead>
      <tbody></tbody>
    `)
    const tbody = table.querySelector("tbody")

    for (let i = 0; i < items.length; i = i + 1) {
      const item = items[i]
      const size = item.size !== undefined && item.size !== null ? String(item.size) : "—"
      const modified = item.modified !== undefined && item.modified !== null ? String(item.modified) : "—"
      const tr = document.createElement("tr")
      tr.setAttribute("part", "file-item")
      tr.setAttribute("role", "row")
      tr.setAttribute("aria-selected", "false")
      tr.setAttribute("tabindex", "-1")
      tr.setAttribute("data-index", String(i))
      tr.setAttribute("data-path", this._itemKey(item))
      tr.setAttribute("data-type", item.type || "")
      tr.innerHTML = String(html`
        <td role="gridcell">
          <span part="file-icon" aria-hidden="true">${getFileIcon(item.type)}</span>
          <span part="file-name">${item.name}</span>
        </td>
        <td role="gridcell">${size}</td>
        <td role="gridcell">${modified}</td>
      `)
      tbody.appendChild(tr)
    }

    this._filePaneEl.appendChild(table)
    return
  }

  /* Exactly one item is in the tab order: the last focused one, else the first. */
  _applyRovingTabindex() {
    const elements = this._filePaneEl.querySelectorAll("[data-index]")
    const items = this._visibleItems()
    let focusIndex = this._focusedKey !== null ? this._indexOfKey(items, this._focusedKey) : -1
    if (focusIndex < 0) {
      focusIndex = 0
    }

    for (let i = 0; i < elements.length; i = i + 1) {
      elements[i].setAttribute("tabindex", i === focusIndex ? "0" : "-1")
    }
    return
  }

  _focusItemAt(index) {
    const items = this._visibleItems()
    if (index < 0 || index >= items.length) {
      return
    }
    this._focusedKey = this._itemKey(items[index])
    this._applyRovingTabindex()
    const element = this._filePaneEl.querySelector(`[data-index="${index}"]`)
    if (element !== null) {
      element.focus()
    }
    return
  }

  /* Resolve the item element an event happened on to { index, item }, or null. */
  _hitItem(event) {
    let hit = null
    const element = event.target.closest("[data-index]")
    if (element !== null && this._filePaneEl.contains(element) === true) {
      const index = parseInt(element.getAttribute("data-index"), 10)
      const items = this._visibleItems()
      if (index >= 0 && index < items.length) {
        hit = { index: index, item: items[index] }
      }
    }
    return hit
  }

  _onFilePaneClick(event) {
    if (event.target.closest(".retry-btn") !== null) {
      this._loadFailed = false
      this._renderFilePane()
      this._loadDirectory()
      return
    }

    const hit = this._hitItem(event)
    if (hit === null) {
      return
    }

    /* A click selects, for folders as well; opening needs a double-click or Enter. */
    const items = this._visibleItems()
    const multi = this._selectionMode() === "multi"
    this._focusedKey = this._itemKey(hit.item)
    this._applyRovingTabindex()

    if (multi === true && event.shiftKey === true) {
      this._selectRangeTo(hit.index)
    } else if (multi === true && (event.ctrlKey === true || event.metaKey === true)) {
      this._toggleSelected(hit.item)
      this._anchorKey = this._itemKey(hit.item)
    } else {
      this._anchorKey = this._itemKey(hit.item)
      this._setSelection([hit.item])
    }
    return
  }

  _onFilePaneDblClick(event) {
    const hit = this._hitItem(event)
    if (hit !== null) {
      this._openItem(hit.item)
    }
    return
  }

  /* Right-clicking an item that is not selected selects it before the menu opens. */
  _onFilePaneContextMenu(event) {
    const hit = this._hitItem(event)
    if (hit !== null && this._isSelected(hit.item) === false) {
      this._anchorKey = this._itemKey(hit.item)
      this._setSelection([hit.item])
    }
    return
  }

  _openItem(item) {
    if (item.type === "folder") {
      const hadFocus = this.shadowRoot.activeElement !== null &&
        this._filePaneEl.contains(this.shadowRoot.activeElement) === true
      this._navigate(this._itemPath(item))
      if (hadFocus === true) {
        /* The focused row is about to be replaced; keep focus in the pane. */
        this._filePaneEl.focus()
      }
    } else {
      this.emit("mj-file-open", { file: item })
    }
    return
  }

  /* Number of items per visual row: 1 in list view, the column count in grid view. */
  _itemsPerRow() {
    let perRow = 1
    if (this._view() === "grid") {
      const elements = this._filePaneEl.querySelectorAll("[data-index]")
      if (elements.length > 0) {
        const firstTop = elements[0].offsetTop
        perRow = 0
        for (let i = 0; i < elements.length; i = i + 1) {
          if (elements[i].offsetTop === firstTop) {
            perRow = perRow + 1
          }
        }
      }
    }
    return perRow
  }

  /*
   * File pane keys: arrows move focus and selection (Shift extends the
   * range, Ctrl/Cmd moves focus only), Home/End, Space toggles, Enter opens,
   * Ctrl/Cmd+A selects everything.
   */
  _onFilePaneKeydown(event) {
    const items = this._visibleItems()
    if (items.length === 0 || event.target.closest(".retry-btn") !== null) {
      return
    }

    const hit = this._hitItem(event)
    const multi = this._selectionMode() === "multi"
    const modifier = event.ctrlKey === true || event.metaKey === true
    const current = hit !== null ? hit.index : -1
    const isGrid = this._view() === "grid"
    const rtl = getComputedStyle(this).direction === "rtl"
    let target = -1
    let handled = true

    if (event.key === "ArrowDown") {
      target = current < 0 ? 0 : current + this._itemsPerRow()
    } else if (event.key === "ArrowUp") {
      target = current < 0 ? 0 : current - this._itemsPerRow()
    } else if (event.key === "ArrowRight" && isGrid === true) {
      target = current < 0 ? 0 : current + (rtl === true ? -1 : 1)
    } else if (event.key === "ArrowLeft" && isGrid === true) {
      target = current < 0 ? 0 : current + (rtl === true ? 1 : -1)
    } else if (event.key === "Home") {
      target = 0
    } else if (event.key === "End") {
      target = items.length - 1
    } else if (event.key === "Enter" && hit !== null) {
      this._openItem(hit.item)
    } else if (event.key === " " && hit !== null) {
      if (multi === true) {
        this._toggleSelected(hit.item)
      } else {
        this._setSelection([hit.item])
      }
      this._anchorKey = this._itemKey(hit.item)
    } else if ((event.key === "a" || event.key === "A") && modifier === true && multi === true) {
      this._setSelection(items.slice())
    } else {
      handled = false
    }

    if (target >= 0 && target < items.length && target !== current) {
      this._focusItemAt(target)
      if (multi === true && event.shiftKey === true) {
        this._selectRangeTo(target)
      } else if (modifier === false) {
        this._anchorKey = this._itemKey(items[target])
        this._setSelection([items[target]])
      }
    }

    if (handled === true) {
      event.preventDefault()
    }
    return
  }

  /* ----- selection ----- */

  _toggleSelected(item) {
    const key = this._itemKey(item)
    let next = []
    if (this._isSelected(item) === true) {
      next = this._selectedFiles.filter((file) => this._itemKey(file) !== key)
    } else {
      next = this._selectedFiles.concat([item])
    }
    this._setSelection(next)
    return
  }

  /* Select every item between the anchor and `index`, inclusive. */
  _selectRangeTo(index) {
    const items = this._visibleItems()
    let anchorIndex = this._anchorKey !== null ? this._indexOfKey(items, this._anchorKey) : -1
    if (anchorIndex < 0) {
      anchorIndex = index
      this._anchorKey = this._itemKey(items[index])
    }
    const from = Math.min(anchorIndex, index)
    const to = Math.max(anchorIndex, index)
    this._setSelection(items.slice(from, to + 1))
    return
  }

  /*
   * Replace the selection. Emits `mj-selection-change` and announces the
   * count only when the set of selected items actually changed.
   */
  _setSelection(nextItems) {
    const previousKeys = this._selectedFiles.map((file) => this._itemKey(file)).join("\n")
    const nextKeys = nextItems.map((file) => this._itemKey(file)).join("\n")
    this._selectedFiles = nextItems

    if (this._filePaneEl !== null) {
      this._updateSelection()
      this._renderPreview()
    }

    if (previousKeys !== nextKeys) {
      this.emit("mj-selection-change", { selectedFiles: this._selectedFiles })
      const count = nextItems.length
      if (count > 0) {
        announce(t("mj.fileBrowser.itemsSelected", { count: count }), "polite")
      }
    }
    return
  }

  /* Reflect `_selectedFiles` onto the rendered items and the status strip. */
  _updateSelection() {
    const elements = this._filePaneEl.querySelectorAll("[data-index]")
    const items = this._visibleItems()
    for (let i = 0; i < elements.length; i = i + 1) {
      const selected = i < items.length && this._isSelected(items[i]) === true
      elements[i].setAttribute("aria-selected", selected === true ? "true" : "false")
    }
    this._updateStatusStrip()
    return
  }

  /* ----- preview ----- */

  /*
   * The preview pane shows when `preview` is not "none" and either
   * `preview-open` is set or -- in the default auto mode -- something is
   * selected. `preview-open="false"` keeps it closed.
   */
  _syncPreviewVisibility() {
    if (this._previewPaneEl === null) {
      return
    }
    const mode = this.getAttribute("preview") || "auto"
    const openValue = this.getAttribute("preview-open")
    let visible = false
    if (mode !== "none" && openValue !== "false") {
      visible = openValue !== null || this._selectedFiles.length > 0
    }
    this._previewPaneEl.hidden = visible === false
    return
  }

  _renderPreview() {
    if (this._previewPaneEl === null) {
      return
    }

    const count = this._selectedFiles.length
    let content = null

    if (count === 0) {
      content = html`<p class="preview-hint">${t("mj.fileBrowser.previewHint")}</p>`
    } else if (count > 1) {
      content = html`<div class="preview-title">${t("mj.fileBrowser.itemsSelected", { count: count })}</div>`
    } else {
      const item = this._selectedFiles[0]
      const hasSize = item.size !== undefined && item.size !== null
      const hasModified = item.modified !== undefined && item.modified !== null
      content = html`
        <div class="preview-title">${item.name}</div>
        <div class="preview-meta">
          <span>${t("mj.fileBrowser.previewType", { type: item.type || t("mj.fileBrowser.unknownType") })}</span>
          ${hasSize === true ? html`<span>${t("mj.fileBrowser.previewSize", { size: item.size })}</span>` : ""}
          ${hasModified === true ? html`<span>${t("mj.fileBrowser.previewModified", { modified: item.modified })}</span>` : ""}
        </div>
      `
    }

    this._previewPaneEl.innerHTML = String(html`<div class="preview-content">${content}</div>`)
    this._syncPreviewVisibility()
    return
  }

  _updateStatusStrip() {
    const totalItems = this._visibleItems().length
    const selectedCount = this._selectedFiles.length

    if (this._itemCountEl !== null) {
      this._itemCountEl.textContent = t("mj.fileBrowser.itemCount", { count: totalItems })
    }
    if (this._selectionCountEl !== null) {
      this._selectionCountEl.textContent = selectedCount > 0
        ? t("mj.fileBrowser.selectedCount", { count: selectedCount })
        : ""
    }
    return
  }

  /* ----- context menu ----- */

  /*
   * The inherited context menu reports the chosen item with
   * `mj-context-select`; the file browser adds the files it applies to.
   */
  _onContextSelect(event) {
    if (event.detail.source !== this) {
      return
    }
    this.emit("mj-context-action", {
      action: event.detail.value,
      item: event.detail.item,
      files: this._selectedFiles.slice()
    })
    return
  }

  /* ----- public API ----- */

  get dataSource() {
    return this._dataSource
  }

  set dataSource(source) {
    this._dataSource = source !== undefined ? source : null
    this._loadedPath = null
    this._loadFailed = false
    this._directoryContents = []

    /* A new source has its own folders: forget the old tree below the root. */
    this._treeNodes = {}
    this._treeNodes["/"] = { path: "/", name: "/", parentPath: null, expanded: true, loaded: false, childPaths: [] }
    this._ensureTreePath(this._currentPath)

    if (this._filePaneEl !== null) {
      this._setSelection([])
      this._renderTree()
      this._renderFilePane()
      if (this._dataSource !== null) {
        this._loadDirectory()
      }
    }
    return
  }

  get currentPath() {
    return this._currentPath
  }

  set currentPath(path) {
    this._navigate(path)
    return
  }

  get selectedFiles() {
    return this._selectedFiles
  }

  /*
   * Items offered when the user right-clicks (or presses the context-menu
   * key on) the browser: { label, value, disabled } or { separator: true }.
   * Choosing one emits `mj-context-action` with { action, item, files }.
   */
  get contextMenuItems() {
    const items = this._contextMenuItems !== null ? this._contextMenuItems : []
    return items
  }

  set contextMenuItems(items) {
    this.setContextMenu(Array.isArray(items) === true ? items : [])
    return
  }
}
