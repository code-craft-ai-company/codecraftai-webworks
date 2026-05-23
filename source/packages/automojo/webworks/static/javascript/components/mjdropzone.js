/*
 * mjdropzone.js
 *
 * <mj-dropzone> -- drag-and-drop file upload zone with keyboard/click
 * alternative, type/size validation, per-file progress, and form association.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";

const STYLES = `
:host {
  display: block;
}

.drop-target {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--mj-space-2);
  min-height: var(--mj-dropzone-min-height, 180px);
  border: var(--mj-dropzone-border, 2px dashed var(--mj-border-strong));
  border-radius: var(--mj-dropzone-radius, var(--mj-radius-md));
  background: var(--mj-dropzone-bg, var(--mj-bg-subtle));
  text-align: center;
  padding: var(--mj-space-4);
  transition: border-color var(--mj-motion-fast) var(--mj-motion-ease),
              background var(--mj-motion-fast) var(--mj-motion-ease);
  cursor: default;
}

:host([drag-over]) .drop-target {
  border: var(--mj-dropzone-border-dragover, 2px dashed var(--mj-accent));
  background: var(--mj-dropzone-bg-dragover, color-mix(in srgb, var(--mj-accent) 8%, transparent));
}

:host([drag-invalid]) .drop-target {
  border: 2px dashed var(--mj-color-danger);
  background: var(--mj-color-danger-surface);
}

:host([disabled]) .drop-target {
  opacity: 0.55;
  cursor: not-allowed;
  pointer-events: none;
}

:host([compact]) .drop-target {
  flex-direction: row;
  min-height: var(--mj-control-height-lg);
  padding: var(--mj-space-2) var(--mj-space-4);
}

.drop-icon {
  font-size: 2rem;
  color: var(--mj-text-muted);
  line-height: 1;
}

.drop-instructions {
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text-muted);
}

.browse-btn {
  display: inline-block;
  padding: var(--mj-space-2) var(--mj-space-4);
  background: var(--mj-surface);
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-md);
  font: inherit;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
  cursor: pointer;
}

.browse-btn:hover { background: var(--mj-bg-muted); }
.browse-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.constraint-text {
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
}

.file-list {
  list-style: none;
  padding: 0;
  margin: var(--mj-space-3) 0 0;
  display: flex;
  flex-direction: column;
  gap: var(--mj-space-2);
}

.file-list[hidden] { display: none; }

.file-item {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  padding: var(--mj-space-2) var(--mj-space-3);
  background: var(--mj-surface);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-sm);
  font-size: var(--mj-font-size-sm);
}

.file-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--mj-text);
}

.file-size {
  color: var(--mj-text-muted);
  font-size: var(--mj-font-size-xs);
  white-space: nowrap;
}

.file-progress {
  height: 4px;
  width: 60px;
  background: var(--mj-bg-muted);
  border-radius: var(--mj-radius-pill);
  overflow: hidden;
}

.file-progress-bar {
  height: 100%;
  background: var(--mj-accent);
  transition: width var(--mj-motion-fast) linear;
}

.file-status-done { color: var(--mj-color-success); }
.file-status-error { color: var(--mj-color-danger); font-size: var(--mj-font-size-xs); }

.file-remove-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--mj-text-muted);
  padding: var(--mj-space-1);
  border-radius: var(--mj-radius-sm);
  line-height: 1;
  font-size: var(--mj-font-size-xs);
}

.file-remove-btn:hover { color: var(--mj-color-danger); }
.file-remove-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}

.live-region {
  position: absolute;
  width: 1px; height: 1px;
  margin: -1px; overflow: hidden;
  clip: rect(0 0 0 0);
  clip-path: inset(50%);
  white-space: nowrap;
}
`;

function formatSize(bytes) {
  if (bytes < 1024) {
    return `${bytes} B`
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`
  }
  if (bytes < 1024 * 1024 * 1024) {
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
}

export class MjDropzone extends MjElement {
  static tagName = "mj-dropzone";
  static styles = STYLES;
  static watched = ["accept", "multiple", "max-size", "max-files", "disabled", "compact", "show-list"];
  static formAssociated = true;

  constructor() {
    super()
    this._files = []
    this._rejectedFiles = []
    this._internals = typeof this.attachInternals === "function" ? this.attachInternals() : null
    this._dropTarget = null
    this._fileInput = null
    this._fileListEl = null
    this._liveEl = null
    this._dragCounter = 0
  }

  render() {
    const label = this.getAttribute("label") || "File upload"
    const browseLabel = this.getAttribute("browse-label") || "Browse files"
    const dragLabel = this.getAttribute("drag-label") || "Drag and drop files here, or"
    const accept = this.getAttribute("accept") || ""
    const multiple = this.getAttribute("multiple") !== "false"
    const maxSize = parseInt(this.getAttribute("max-size") || "0", 10)
    const constraintParts = []
    if (accept.length > 0) {
      constraintParts.push(accept)
    }
    if (maxSize > 0) {
      constraintParts.push(`Max ${formatSize(maxSize)} per file`)
    }
    const constraintText = constraintParts.join(" · ")

    const markup = `
      <div class="drop-target" role="region" part="drop-target"
           aria-label="${label}">
        <div class="drop-icon" part="icon">
          <slot name="icon">&#9729;</slot>
        </div>
        <div class="drop-instructions" part="instructions">
          <slot name="instructions">${dragLabel}</slot>
        </div>
        <button class="browse-btn" part="browse-button" type="button">
          ${browseLabel}
        </button>
        ${constraintText.length > 0 ? `<p class="constraint-text" part="constraint-text">${constraintText}</p>` : ""}
      </div>
      <ul class="file-list" part="file-list" hidden aria-label="Selected files"></ul>
      <input type="file" aria-hidden="true" tabindex="-1"
             ${multiple ? "multiple" : ""}
             ${accept.length > 0 ? `accept="${accept}"` : ""}
             style="position:absolute;opacity:0;pointer-events:none;width:1px;height:1px;">
      <div class="live-region" role="status" aria-live="polite"></div>
    `
    return markup
  }

  afterRender() {
    this._dropTarget = this.$(".drop-target")
    this._fileListEl = this.$(".file-list")
    this._fileInput = this.$("input[type=file]")
    this._liveEl = this.$(".live-region")
    this._browseBtn = this.$(".browse-btn")

    this.listen(this._browseBtn, "click", this._onBrowseClick.bind(this))
    this.listen(this._fileInput, "change", this._onInputChange.bind(this))
    this.listen(this._dropTarget, "dragenter", this._onDragEnter.bind(this))
    this.listen(this._dropTarget, "dragover", this._onDragOver.bind(this))
    this.listen(this._dropTarget, "dragleave", this._onDragLeave.bind(this))
    this.listen(this._dropTarget, "drop", this._onDrop.bind(this))

    return
  }

  _onBrowseClick() {
    if (this.hasAttribute("disabled")) {
      return
    }
    this._fileInput.click()
    return
  }

  _onInputChange(event) {
    const rawFiles = event.target.files
    if (rawFiles === null || rawFiles === undefined) {
      return
    }
    const fileArray = Array.from(rawFiles)
    this._processFiles(fileArray)
    this._fileInput.value = ""
    return
  }

  _onDragEnter(event) {
    event.preventDefault()
    this._dragCounter = this._dragCounter + 1
    if (this._dragCounter === 1) {
      this.setAttribute("drag-over", "")
      this._dropTarget.setAttribute("aria-dropeffect", "copy")
      this.emit("mj-drag-enter", {})
    }
    return
  }

  _onDragOver(event) {
    event.preventDefault()
    return
  }

  _onDragLeave() {
    this._dragCounter = this._dragCounter - 1
    if (this._dragCounter <= 0) {
      this._dragCounter = 0
      this.removeAttribute("drag-over")
      this.removeAttribute("drag-invalid")
      this._dropTarget.setAttribute("aria-dropeffect", "none")
      this.emit("mj-drag-leave", {})
    }
    return
  }

  _onDrop(event) {
    event.preventDefault()
    this._dragCounter = 0
    this.removeAttribute("drag-over")
    this.removeAttribute("drag-invalid")

    const dt = event.dataTransfer
    if (dt === null || dt === undefined) {
      return
    }
    const fileArray = Array.from(dt.files)
    this._processFiles(fileArray)
    return
  }

  _processFiles(rawFiles) {
    const accept = this.getAttribute("accept") || ""
    const maxSize = parseInt(this.getAttribute("max-size") || "0", 10)
    const maxFiles = parseInt(this.getAttribute("max-files") || "0", 10)
    const multiple = this.getAttribute("multiple") !== "false"

    const accepted = []
    const rejected = []

    for (let i = 0; i < rawFiles.length; i = i + 1) {
      const file = rawFiles[i]
      let reason = null

      if (accept.length > 0 && !this._fileMatchesAccept(file, accept)) {
        reason = `File type not allowed: ${file.type || "unknown"}`
      } else if (maxSize > 0 && file.size > maxSize) {
        reason = `File too large: ${formatSize(file.size)} (max ${formatSize(maxSize)})`
      }

      if (reason !== null) {
        rejected.push({ file: file, reason: reason })
      } else {
        accepted.push(file)
      }
    }

    if (multiple === false && accepted.length > 0) {
      this._files = []
    }

    let actualAccepted = accepted
    if (maxFiles > 0 && this._files.length + accepted.length > maxFiles) {
      const room = Math.max(0, maxFiles - this._files.length)
      const overflow = accepted.slice(room)
      actualAccepted = accepted.slice(0, room)
      for (let i = 0; i < overflow.length; i = i + 1) {
        rejected.push({ file: overflow[i], reason: "Maximum file count exceeded" })
      }
    }

    const newEntries = []
    for (let i = 0; i < actualAccepted.length; i = i + 1) {
      const entry = {
        id: nextId("mj-file"),
        file: actualAccepted[i],
        status: "queued",
        progress: 0,
        error: undefined
      }
      this._files.push(entry)
      newEntries.push(entry)
    }

    if (rejected.length > 0) {
      this._rejectedFiles = this._rejectedFiles.concat(rejected)
      this.emit("mj-files-rejected", { rejectedFiles: rejected })
      announce(`${rejected.length} file${rejected.length > 1 ? "s" : ""} rejected`, "polite")
    }

    if (newEntries.length > 0) {
      this._updateFormValue()
      this.emit("mj-files-added", { files: newEntries })
      announce(`${newEntries.length} file${newEntries.length > 1 ? "s" : ""} added`, "polite")
    }

    if (this.getAttribute("show-list") !== "false") {
      this._renderFileList()
    }

    return
  }

  _fileMatchesAccept(file, accept) {
    const parts = accept.split(",").map((s) => s.trim())
    for (let i = 0; i < parts.length; i = i + 1) {
      const pattern = parts[i]
      if (pattern === "*/*" || pattern === "") {
        return true
      }
      if (pattern.endsWith("/*")) {
        const typeGroup = pattern.slice(0, -2)
        if (file.type.startsWith(typeGroup)) {
          return true
        }
      }
      if (pattern === file.type) {
        return true
      }
      if (pattern.startsWith(".")) {
        if (file.name.toLowerCase().endsWith(pattern.toLowerCase())) {
          return true
        }
      }
    }
    return false
  }

  _renderFileList() {
    if (this._fileListEl === null) {
      return
    }
    if (this._files.length === 0) {
      this._fileListEl.hidden = true
      this._fileListEl.innerHTML = ""
      return
    }

    this._fileListEl.hidden = false
    this._fileListEl.innerHTML = ""

    for (let i = 0; i < this._files.length; i = i + 1) {
      const entry = this._files[i]
      const li = document.createElement("li")
      li.className = "file-item"
      li.setAttribute("part", "file-item")
      li.setAttribute("data-file-id", entry.id)

      let statusHtml = ""
      if (entry.status === "uploading") {
        statusHtml = `
          <div class="file-progress" role="progressbar"
               aria-valuenow="${entry.progress}" aria-valuemin="0" aria-valuemax="100"
               aria-label="Uploading ${entry.file.name}">
            <div class="file-progress-bar" style="width:${entry.progress}%"></div>
          </div>
        `
      } else if (entry.status === "done") {
        statusHtml = `<span class="file-status-done" aria-label="Upload complete">&#10003;</span>`
      } else if (entry.status === "error") {
        statusHtml = `<span class="file-status-error">${entry.error || "Error"}</span>`
      }

      li.innerHTML = `
        <span class="file-name" part="file-name" title="${entry.file.name}">${entry.file.name}</span>
        <span class="file-size" part="file-size">${formatSize(entry.file.size)}</span>
        ${statusHtml}
        <button class="file-remove-btn" part="file-remove" type="button"
                aria-label="Remove ${entry.file.name}" data-file-id="${entry.id}">&#x2715;</button>
      `

      const removeBtn = li.querySelector(".file-remove-btn")
      if (removeBtn !== null) {
        this.listen(removeBtn, "click", this._onFileRemove.bind(this, entry.id, entry.file))
      }

      this._fileListEl.appendChild(li)
    }
    return
  }

  _onFileRemove(fileId, file) {
    this._files = this._files.filter((f) => f.id !== fileId)
    this._updateFormValue()
    this.emit("mj-file-remove", { fileId: fileId, file: file })
    announce(`${file.name} removed`, "assertive")
    this._renderFileList()
    return
  }

  _updateFormValue() {
    if (this._internals !== null) {
      const dt = new DataTransfer()
      for (let i = 0; i < this._files.length; i = i + 1) {
        dt.items.add(this._files[i].file)
      }
      try {
        this._internals.setFormValue(dt.files)
      } catch (e) {
        // DataTransfer not supported in setFormValue in some browsers
      }
    }
    return
  }

  updateFile(fileId, updates) {
    for (let i = 0; i < this._files.length; i = i + 1) {
      if (this._files[i].id === fileId) {
        const entry = this._files[i]
        if (updates.status !== undefined) {
          entry.status = updates.status
        }
        if (updates.progress !== undefined) {
          entry.progress = updates.progress
        }
        if (updates.error !== undefined) {
          entry.error = updates.error
        }
        break
      }
    }
    if (this.getAttribute("show-list") !== "false") {
      this._renderFileList()
    }
    return
  }

  get files() {
    return this._files
  }

  get rejectedFiles() {
    return this._rejectedFiles
  }
}
