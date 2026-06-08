/*
 * mjfilebrowser.js
 *
 * <mj-file-browser> -- three-pane file system navigator with folder tree,
 * file grid/list pane, and optional preview pane. Unified selection model,
 * breadcrumb navigation, and keyboard support.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";

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

:host([preview="none"]) .preview-pane,
:host(:not([preview-open])) .preview-pane {
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
  "folder": "&#128193;",
  "image": "&#128247;",
  "video": "&#127910;",
  "audio": "&#127925;",
  "pdf": "&#128196;",
  "default": "&#128196;"
};

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

export class MjFileBrowser extends MjElement {
  static tagName = "mj-file-browser";
  static styles = STYLES;
  static watched = ["view", "preview", "preview-open", "tree-open", "selection-mode", "show-hidden"];

  constructor() {
    super()
    this._dataSource = null
    this._currentPath = "/"
    this._pathSegments = ["/"]
    this._selectedFiles = []
    this._directoryContents = []
    this._treeNodes = []
    this._contextMenuItems = []
    this._panelFocusIndex = 0
  }

  render() {
    const label = this.getAttribute("label") || "File browser"
    const markup = `
      <div role="application" aria-label="${label}" style="display:contents">
        <nav class="fb-breadcrumb" part="breadcrumb" aria-label="File path">
          <span>/</span>
        </nav>
        <div class="fb-toolbar" part="toolbar">
          <button class="view-btn" aria-pressed="false" data-view="list" aria-label="List view">&#9776;</button>
          <button class="view-btn" aria-pressed="false" data-view="grid" aria-label="Grid view">&#9783;</button>
          <slot name="toolbar-actions"></slot>
        </div>
        <div class="fb-panes" part="panes">
          <div class="tree-pane" part="tree-pane" role="tree" aria-label="Folders" tabindex="0">
            <div class="tree-item" role="treeitem" aria-selected="true" aria-level="1" tabindex="0"
                 data-path="/">/root</div>
          </div>
          <div class="file-pane" part="file-pane" aria-label="Files" tabindex="0">
            <slot name="empty">
              <div class="empty-state">No files</div>
            </slot>
          </div>
          <div class="preview-pane" part="preview-pane" role="region" aria-label="File preview" tabindex="-1">
            <div class="preview-content">
              <p style="color:var(--mj-text-muted);font-size:var(--mj-font-size-xs);">Select a file to preview</p>
            </div>
          </div>
        </div>
        <div class="fb-status-strip" part="status-strip" aria-live="polite">
          <span class="item-count">0 items</span>
          <span class="selection-count"></span>
        </div>
        <div class="live-region" aria-live="polite"></div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._breadcrumbEl = this.$(".fb-breadcrumb")
    this._toolbarEl = this.$(".fb-toolbar")
    this._treePaneEl = this.$(".tree-pane")
    this._filePaneEl = this.$(".file-pane")
    this._previewPaneEl = this.$(".preview-pane")
    this._statusStrip = this.$(".fb-status-strip")
    this._itemCountEl = this.$(".item-count")
    this._selectionCountEl = this.$(".selection-count")
    this._liveEl = this.$(".live-region")

    // View toggle buttons
    const viewBtns = this._toolbarEl.querySelectorAll(".view-btn")
    for (let i = 0; i < viewBtns.length; i = i + 1) {
      const btn = viewBtns[i]
      this.listen(btn, "click", this._onViewChange.bind(this, btn))
    }
    this._updateViewButtons()

    this.listen(this, "keydown", this._onKeydown.bind(this))

    if (this._dataSource !== null) {
      this._navigate("/")
    }

    return
  }

  _updateViewButtons() {
    const view = this.getAttribute("view") || "list"
    const btns = this._toolbarEl.querySelectorAll(".view-btn")
    for (let i = 0; i < btns.length; i = i + 1) {
      const btn = btns[i]
      const btnView = btn.getAttribute("data-view")
      btn.setAttribute("aria-pressed", btnView === view ? "true" : "false")
    }
    return
  }

  _onViewChange(btn) {
    const view = btn.getAttribute("data-view")
    this.setAttribute("view", view)
    this._updateViewButtons()
    this._renderFilePane()
    this.emit("mj-view-change", { view: view })
    return
  }

  _onKeydown(event) {
    if (event.key === "F6") {
      event.preventDefault()
      this._cyclePanelFocus()
    }
    return
  }

  _cyclePanelFocus() {
    const panels = [this._treePaneEl, this._filePaneEl, this._previewPaneEl]
    const names = ["Folder tree", "Files", "Preview"]
    this._panelFocusIndex = (this._panelFocusIndex + 1) % panels.length
    const panel = panels[this._panelFocusIndex]
    if (panel !== null && panel !== undefined) {
      panel.focus()
      announce(`Focus moved to ${names[this._panelFocusIndex]}`, "polite")
    }
    return
  }

  _navigate(path) {
    this._currentPath = path
    this._updateBreadcrumb(path)
    this.emit("mj-folder-navigate", { path: path })

    if (this._dataSource === null) {
      return
    }

    const listPromise = this._dataSource.listDir(path)
    Promise.resolve(listPromise).then((items) => {
      this._directoryContents = items || []
      this._renderFilePane()
      this._updateStatusStrip()
    }).catch(() => {
      this._filePaneEl.innerHTML = `<div class="empty-state" style="color:var(--mj-color-danger)">Failed to load directory</div>`
    })
    return
  }

  _updateBreadcrumb(path) {
    if (this._breadcrumbEl === null) {
      return
    }
    const segments = path === "/" ? ["/"] : ["/"].concat(path.replace(/^\//, "").split("/"))
    this._breadcrumbEl.innerHTML = ""

    for (let i = 0; i < segments.length; i = i + 1) {
      const seg = segments[i]
      const btn = document.createElement("button")
      btn.className = "breadcrumb-seg"
      btn.textContent = seg
      const targetPath = i === 0 ? "/" : "/" + segments.slice(1, i + 1).join("/")
      this.listen(btn, "click", () => this._navigate(targetPath))
      this._breadcrumbEl.appendChild(btn)
      if (i < segments.length - 1) {
        const sep = document.createElement("span")
        sep.className = "breadcrumb-sep"
        sep.textContent = "›"
        this._breadcrumbEl.appendChild(sep)
      }
    }
    return
  }

  _renderFilePane() {
    if (this._filePaneEl === null) {
      return
    }

    const view = this.getAttribute("view") || "list"
    const showHidden = this.hasAttribute("show-hidden")
    let items = this._directoryContents

    if (showHidden === false) {
      items = items.filter((f) => !f.name.startsWith("."))
    }

    if (items.length === 0) {
      this._filePaneEl.innerHTML = `<div class="empty-state"><slot name="empty">No files in this folder</slot></div>`
      return
    }

    if (view === "grid") {
      this._renderGrid(items)
    } else {
      this._renderList(items)
    }
    return
  }

  _renderGrid(items) {
    const grid = document.createElement("div")
    grid.className = "file-grid"
    grid.setAttribute("role", "listbox")
    grid.setAttribute("aria-multiselectable", this.getAttribute("selection-mode") !== "single" ? "true" : "false")
    grid.setAttribute("aria-label", "Files")

    for (let i = 0; i < items.length; i = i + 1) {
      const item = items[i]
      const el = document.createElement("div")
      el.className = "file-grid-item"
      el.setAttribute("role", "option")
      el.setAttribute("aria-selected", "false")
      el.setAttribute("tabindex", i === 0 ? "0" : "-1")
      el.setAttribute("data-path", item.path || item.name)
      el.setAttribute("data-type", item.type || "")
      el.innerHTML = `
        <span class="file-icon" aria-hidden="true">${getFileIcon(item.type)}</span>
        <span class="file-item-name" title="${item.name}">${item.name}</span>
      `
      this.listen(el, "click", this._onFileClick.bind(this, item))
      this.listen(el, "dblclick", this._onFileOpen.bind(this, item))
      this.listen(el, "keydown", this._onFileKeydown.bind(this, item))
      grid.appendChild(el)
    }

    this._filePaneEl.innerHTML = ""
    this._filePaneEl.appendChild(grid)
    return
  }

  _renderList(items) {
    const table = document.createElement("table")
    table.className = "file-list-table"
    table.setAttribute("role", "grid")
    table.setAttribute("aria-label", "Files")
    table.innerHTML = `
      <thead>
        <tr>
          <th scope="col">Name</th>
          <th scope="col">Size</th>
          <th scope="col">Modified</th>
        </tr>
      </thead>
      <tbody></tbody>
    `
    const tbody = table.querySelector("tbody")

    for (let i = 0; i < items.length; i = i + 1) {
      const item = items[i]
      const tr = document.createElement("tr")
      tr.setAttribute("role", "row")
      tr.setAttribute("aria-selected", "false")
      tr.setAttribute("tabindex", i === 0 ? "0" : "-1")
      tr.setAttribute("data-path", item.path || item.name)
      tr.innerHTML = `
        <td role="gridcell">
          <span aria-hidden="true">${getFileIcon(item.type)}</span>
          ${item.name}
        </td>
        <td role="gridcell">${item.size !== undefined ? String(item.size) : "—"}</td>
        <td role="gridcell">${item.modified !== undefined ? String(item.modified) : "—"}</td>
      `
      this.listen(tr, "click", this._onFileClick.bind(this, item))
      this.listen(tr, "dblclick", this._onFileOpen.bind(this, item))
      this.listen(tr, "keydown", this._onFileKeydown.bind(this, item))
      tbody.appendChild(tr)
    }

    this._filePaneEl.innerHTML = ""
    this._filePaneEl.appendChild(table)
    return
  }

  _onFileClick(item, event) {
    const selMode = this.getAttribute("selection-mode") || "multi"

    if (item.type === "folder") {
      this._navigate(item.path || `/${item.name}`)
      return
    }

    if (selMode === "multi" && (event.ctrlKey || event.metaKey)) {
      const idx = this._selectedFiles.findIndex((f) => f.path === item.path)
      if (idx >= 0) {
        this._selectedFiles.splice(idx, 1)
      } else {
        this._selectedFiles.push(item)
      }
    } else {
      this._selectedFiles = [item]
    }

    this._updateSelection()
    this._renderPreview(item)
    this.emit("mj-selection-change", { selectedFiles: this._selectedFiles })
    return
  }

  _onFileOpen(item) {
    if (item.type === "folder") {
      this._navigate(item.path || `/${item.name}`)
      return
    }
    this.emit("mj-file-open", { file: item })
    return
  }

  _onFileKeydown(item, event) {
    if (event.key === "Enter") {
      this._onFileOpen(item)
    } else if (event.key === " ") {
      event.preventDefault()
      this._onFileClick(item, event)
    }
    return
  }

  _updateSelection() {
    const allItems = this._filePaneEl.querySelectorAll("[role='option'], [role='row']")
    for (let i = 0; i < allItems.length; i = i + 1) {
      const el = allItems[i]
      const path = el.getAttribute("data-path")
      const selected = this._selectedFiles.some((f) => (f.path || f.name) === path)
      el.setAttribute("aria-selected", selected ? "true" : "false")
    }
    this._updateStatusStrip()
    return
  }

  _renderPreview(item) {
    if (this._previewPaneEl === null) {
      return
    }
    this._previewPaneEl.innerHTML = `
      <div class="preview-content">
        <div class="preview-title">${item.name}</div>
        <div class="preview-meta">
          <span>Type: ${item.type || "unknown"}</span>
          ${item.size !== undefined ? `<span>Size: ${item.size}</span>` : ""}
          ${item.modified !== undefined ? `<span>Modified: ${item.modified}</span>` : ""}
        </div>
      </div>
    `
    return
  }

  _updateStatusStrip() {
    const totalItems = this._directoryContents.length
    const selectedCount = this._selectedFiles.length

    if (this._itemCountEl !== null) {
      this._itemCountEl.textContent = `${totalItems} ${totalItems === 1 ? "item" : "items"}`
    }
    if (this._selectionCountEl !== null) {
      this._selectionCountEl.textContent = selectedCount > 0
        ? `${selectedCount} selected`
        : ""
    }

    if (selectedCount > 0) {
      announce(`${selectedCount} ${selectedCount === 1 ? "item" : "items"} selected`, "polite")
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "view" && this._filePaneEl !== null) {
      this._renderFilePane()
    }
    return
  }

  get dataSource() {
    return this._dataSource
  }

  set dataSource(source) {
    this._dataSource = source
    if (source !== null && source !== undefined && this._filePaneEl !== null) {
      this._navigate(this._currentPath)
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

  get contextMenuItems() {
    return this._contextMenuItems
  }

  set contextMenuItems(items) {
    this._contextMenuItems = Array.isArray(items) ? items : []
    return
  }
}
