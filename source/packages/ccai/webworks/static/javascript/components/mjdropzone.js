/*
 * mjdropzone.js
 *
 * <mj-dropzone> -- drag-and-drop file upload zone with keyboard/click
 * alternative, type/size validation, per-file progress, and form association.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { announce } from "../core/announcer.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";

/* Upper bound on the files taken from one dropped folder tree. */
const MAX_FOLDER_FILES = 1000;

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

:host([disabled]) .drop-target,
.drop-target[aria-disabled="true"] {
  opacity: 0.55;
  cursor: not-allowed;
}

.browse-btn:disabled {
  cursor: not-allowed;
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
  margin: 0;
}

.constraint-text[hidden] { display: none; }

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

.file-input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
  width: 1px;
  height: 1px;
}

.error-list {
  list-style: none;
  padding: 0;
  margin: var(--mj-space-3) 0 0;
  display: flex;
  flex-direction: column;
  gap: var(--mj-space-2);
}

.error-list[hidden] { display: none; }

.error-item {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  padding: var(--mj-space-2) var(--mj-space-3);
  background: var(--mj-color-danger-surface);
  border: 1px solid var(--mj-color-danger);
  border-radius: var(--mj-radius-sm);
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
}

.error-name {
  font-weight: var(--mj-font-weight-medium, 500);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-inline-size: 40%;
}

.error-reason {
  flex: 1;
  color: var(--mj-color-danger);
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

/* Clamp an upload progress value to a whole percentage between 0 and 100. */
function clampProgress(value) {
  let progress = Number(value)
  if (Number.isFinite(progress) === false) {
    progress = 0
  }
  progress = Math.max(0, Math.min(100, Math.round(progress)))
  return progress
}

export class MjDropzone extends FormControlMixin(MjElement) {
  static tagName = "mj-dropzone";
  static styles = STYLES;
  static watched = [
    "accept", "multiple", "max-size", "max-files", "disabled", "compact", "show-list",
    "label", "browse-label", "drag-label", "name", "required"
  ];

  constructor() {
    super()
    this._initFormControl()
    this._value = null
    this._files = []
    this._rejectedFiles = []
    this._formDisabled = false
    this._dropTarget = null
    this._fileInput = null
    this._fileListEl = null
    this._errorListEl = null
    this._browseBtn = null
    this._constraintEl = null
    this._instructionsEl = null
    this._dragCounter = 0
  }

  render() {
    const markup = html`
      <div class="drop-target" role="region" part="drop-target">
        <div class="drop-icon" part="icon">
          <slot name="icon">&#9729;</slot>
        </div>
        <div class="drop-instructions" part="instructions">
          <slot name="instructions"><span class="drag-label"></span></slot>
        </div>
        <button class="browse-btn" part="browse-button" type="button"></button>
        <p class="constraint-text" part="constraint-text" hidden></p>
      </div>
      <ul class="file-list" part="file-list" hidden aria-label="${t("mj.dropzone.selectedFilesLabel")}"></ul>
      <ul class="error-list" part="error-list" hidden aria-label="${t("mj.dropzone.rejectedFilesLabel")}"></ul>
      <input class="file-input" type="file" aria-hidden="true" tabindex="-1">
    `
    return markup
  }

  afterRender() {
    this._dropTarget = this.$(".drop-target")
    this._fileListEl = this.$(".file-list")
    this._errorListEl = this.$(".error-list")
    this._fileInput = this.$("input[type=file]")
    this._browseBtn = this.$(".browse-btn")
    this._constraintEl = this.$(".constraint-text")
    this._instructionsEl = this.$(".drag-label")
    this._dragCounter = 0

    this.listen(this._browseBtn, "click", this._onBrowseClick.bind(this))
    this.listen(this._fileInput, "change", this._onInputChange.bind(this))
    this.listen(this._dropTarget, "dragenter", this._onDragEnter.bind(this))
    this.listen(this._dropTarget, "dragover", this._onDragOver.bind(this))
    this.listen(this._dropTarget, "dragleave", this._onDragLeave.bind(this))
    this.listen(this._dropTarget, "drop", this._onDrop.bind(this))

    /* One delegated listener per list, so re-rendering rows registers nothing. */
    this.listen(this._fileListEl, "click", this._onFileListClick.bind(this))
    this.listen(this._fileListEl, "keydown", this._onFileListKeydown.bind(this))
    this.listen(this._errorListEl, "click", this._onErrorListClick.bind(this))

    /* Files queued before a reconnect are still held, so show them again. */
    this._syncControls()
    this._renderFileList()
    this._renderErrorList()
    this._updateFormValue()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._dropTarget === undefined || this._dropTarget === null) {
      return
    }

    if (name === "name" || name === "required") {
      this._updateFormValue()
    } else if (name === "show-list") {
      this._renderFileList()
    } else {
      this._syncControls()
    }
    return
  }

  /* A disabled fieldset ancestor disables the control like the attribute does. */
  onFormDisabled(disabled) {
    this._formDisabled = disabled === true
    this._syncControls()
    return
  }

  /* Form reset empties the selection, as it does for a native file input. */
  formResetCallback() {
    this._discardAll()
    return
  }

  /* Files cannot be restored from session history; start empty. */
  formStateRestoreCallback(state) {
    return
  }

  _isInert() {
    const inert = this.hasAttribute("disabled") === true || this._formDisabled === true
    return inert
  }

  _isMultiple() {
    const multiple = this.getAttribute("multiple") !== "false"
    return multiple
  }

  /*
   * Apply every attribute-derived piece of state to the shadow DOM: labels,
   * the constraint text, the native input's accept/multiple and the disabled
   * state. Called after render and whenever a watched attribute changes.
   */
  _syncControls() {
    if (this._dropTarget === undefined || this._dropTarget === null) {
      return
    }

    const label = this.getAttribute("label") || t("mj.dropzone.label")
    const browseLabel = this.getAttribute("browse-label") || t("mj.dropzone.browse")
    const dragLabel = this.getAttribute("drag-label") || t("mj.dropzone.dragLabel")
    const accept = this.getAttribute("accept") || ""
    const maxSize = parseInt(this.getAttribute("max-size") || "0", 10)
    const inert = this._isInert()

    this._dropTarget.setAttribute("aria-label", label)
    this._browseBtn.textContent = browseLabel
    this._instructionsEl.textContent = dragLabel

    const constraintParts = []
    if (accept.length > 0) {
      constraintParts.push(accept)
    }
    if (maxSize > 0) {
      constraintParts.push(t("mj.dropzone.maxSizePerFile", { size: formatSize(maxSize) }))
    }
    this._constraintEl.textContent = constraintParts.join(" · ")
    this._constraintEl.hidden = constraintParts.length === 0

    if (accept.length > 0) {
      this._fileInput.setAttribute("accept", accept)
    } else {
      this._fileInput.removeAttribute("accept")
    }
    this._fileInput.multiple = this._isMultiple()
    this._fileInput.disabled = inert
    this._browseBtn.disabled = inert

    if (inert === true) {
      this._dropTarget.setAttribute("aria-disabled", "true")
      this._dragCounter = 0
      this.removeAttribute("drag-over")
      this.removeAttribute("drag-invalid")
    } else {
      this._dropTarget.removeAttribute("aria-disabled")
    }

    const removeButtons = this.$all(".file-remove-btn")
    for (let i = 0; i < removeButtons.length; i = i + 1) {
      removeButtons[i].disabled = inert
    }
    return
  }

  _onBrowseClick() {
    if (this._isInert() === true) {
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

  /* True when the drag carries files (not text, links or page elements). */
  _dragHasFiles(event) {
    let hasFiles = false
    const dt = event.dataTransfer
    if (dt !== null && dt !== undefined && dt.types !== undefined && dt.types !== null) {
      hasFiles = Array.from(dt.types).indexOf("Files") >= 0
    }
    return hasFiles
  }

  /*
   * Decide whether a drag in progress can be accepted. File names are not
   * readable until the drop, so only MIME patterns can be judged here: the
   * drag is invalid when the accept list holds MIME patterns only and a
   * dragged file reports a type that matches none of them.
   */
  _dragIsInvalid(event) {
    let invalid = false
    const accept = this.getAttribute("accept") || ""
    const patterns = accept.split(",").map((part) => part.trim()).filter((part) => part.length > 0)
    const hasExtensionPattern = patterns.some((pattern) => pattern.startsWith("."))
    const items = event.dataTransfer !== null && event.dataTransfer !== undefined ? event.dataTransfer.items : null

    if (patterns.length > 0 && hasExtensionPattern === false && items !== null && items !== undefined) {
      for (let i = 0; i < items.length; i = i + 1) {
        const item = items[i]
        if (item.kind === "file" && item.type.length > 0) {
          const candidate = { type: item.type, name: "" }
          if (this._fileMatchesAccept(candidate, accept) === false) {
            invalid = true
          }
        }
      }
    }
    return invalid
  }

  _onDragEnter(event) {
    if (this._isInert() === true || this._dragHasFiles(event) === false) {
      return
    }
    event.preventDefault()
    this._dragCounter = this._dragCounter + 1
    if (this._dragCounter === 1) {
      const invalid = this._dragIsInvalid(event)
      this.setAttribute("drag-over", "")
      this.toggleAttribute("drag-invalid", invalid)
      this._dropTarget.setAttribute("aria-dropeffect", invalid === true ? "none" : "copy")
      this.emit("mj-drag-enter", {})
    }
    return
  }

  _onDragOver(event) {
    if (this._isInert() === true || this._dragHasFiles(event) === false) {
      return
    }
    event.preventDefault()
    event.dataTransfer.dropEffect = this.hasAttribute("drag-invalid") === true ? "none" : "copy"
    return
  }

  _onDragLeave() {
    if (this._dragCounter === 0) {
      return
    }
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
    if (this._dragHasFiles(event) === false) {
      return
    }
    event.preventDefault()
    this._dragCounter = 0
    this.removeAttribute("drag-over")
    this.removeAttribute("drag-invalid")
    this._dropTarget.setAttribute("aria-dropeffect", "none")

    if (this._isInert() === true) {
      return
    }

    const dt = event.dataTransfer

    /*
     * Entries must be read while the event is being dispatched; the item
     * list is emptied afterwards. A drop that contains a folder is expanded
     * to the files inside it, otherwise the plain file list is used.
     */
    const entries = []
    let hasDirectory = false
    const items = dt.items
    if (items !== undefined && items !== null) {
      for (let i = 0; i < items.length; i = i + 1) {
        const item = items[i]
        if (item.kind === "file" && typeof item.webkitGetAsEntry === "function") {
          const entry = item.webkitGetAsEntry()
          if (entry !== null && entry !== undefined) {
            entries.push(entry)
            if (entry.isDirectory === true) {
              hasDirectory = true
            }
          }
        }
      }
    }

    if (hasDirectory === true) {
      this._collectEntryFiles(entries).then((files) => {
        this._processFiles(files)
      })
    } else {
      const fileArray = Array.from(dt.files)
      this._processFiles(fileArray)
    }
    return
  }

  /*
   * Resolve file-system entries (from a dropped folder) to File objects,
   * walking directories breadth-first. Stops at max-files when set, and at
   * MAX_FOLDER_FILES otherwise, so a huge tree cannot stall the page.
   */
  async _collectEntryFiles(entries) {
    const maxFiles = parseInt(this.getAttribute("max-files") || "0", 10)
    const limit = maxFiles > 0 ? maxFiles + 1 : MAX_FOLDER_FILES
    const files = []
    const queue = entries.slice()

    while (queue.length > 0 && files.length < limit) {
      const entry = queue.shift()

      if (entry.isFile === true) {
        const file = await new Promise((resolve) => {
          entry.file(resolve, () => { resolve(null) })
        })
        if (file !== null) {
          files.push(file)
        }
      } else if (entry.isDirectory === true) {
        const reader = entry.createReader()
        let batch = []
        /* readEntries returns the listing in chunks until an empty one. */
        do {
          batch = await new Promise((resolve) => {
            reader.readEntries(resolve, () => { resolve([]) })
          })
          for (let i = 0; i < batch.length; i = i + 1) {
            queue.push(batch[i])
          }
        } while (batch.length > 0)
      }
    }

    return files
  }

  _processFiles(rawFiles) {
    if (this._isInert() === true) {
      return
    }

    const accept = this.getAttribute("accept") || ""
    const maxSize = parseInt(this.getAttribute("max-size") || "0", 10)
    const maxFiles = parseInt(this.getAttribute("max-files") || "0", 10)
    const multiple = this._isMultiple()

    const accepted = []
    const rejected = []

    for (let i = 0; i < rawFiles.length; i = i + 1) {
      const file = rawFiles[i]
      let reason = null

      if (accept.length > 0 && this._fileMatchesAccept(file, accept) === false) {
        reason = t("mj.dropzone.typeNotAllowed", { type: file.type || t("mj.dropzone.unknownType") })
      } else if (maxSize > 0 && file.size > maxSize) {
        reason = t("mj.dropzone.tooLarge", { size: formatSize(file.size), max: formatSize(maxSize) })
      }

      if (reason !== null) {
        rejected.push({ id: nextId("mj-file-rejected"), file: file, reason: reason })
      } else {
        accepted.push(file)
      }
    }

    let actualAccepted = accepted
    let replacedEntries = []

    if (multiple === false) {
      /* Single-file mode: the first accepted file replaces the current one. */
      actualAccepted = accepted.slice(0, 1)
      for (let i = 1; i < accepted.length; i = i + 1) {
        rejected.push({ id: nextId("mj-file-rejected"), file: accepted[i], reason: t("mj.dropzone.onlyOneFile") })
      }
      if (actualAccepted.length > 0) {
        replacedEntries = this._files
        this._files = []
      }
    } else if (maxFiles > 0 && this._files.length + accepted.length > maxFiles) {
      const room = Math.max(0, maxFiles - this._files.length)
      const overflow = accepted.slice(room)
      actualAccepted = accepted.slice(0, room)
      for (let i = 0; i < overflow.length; i = i + 1) {
        rejected.push({ id: nextId("mj-file-rejected"), file: overflow[i], reason: t("mj.dropzone.maxFilesExceeded") })
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

    for (let i = 0; i < replacedEntries.length; i = i + 1) {
      const replaced = replacedEntries[i]
      this.emit("mj-file-remove", { fileId: replaced.id, file: replaced.file })
    }

    if (rejected.length > 0) {
      this._rejectedFiles = this._rejectedFiles.concat(rejected)
      this.emit("mj-files-rejected", { rejectedFiles: rejected })
      announce(t("mj.dropzone.rejectedAnnouncement", { count: rejected.length }), "polite")
    }

    if (newEntries.length > 0) {
      this._updateFormValue()
      this.emit("mj-files-added", { files: newEntries })
      announce(t("mj.dropzone.addedAnnouncement", { count: newEntries.length }), "polite")
    }

    this._renderFileList()
    this._renderErrorList()

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
        const typeGroup = pattern.slice(0, -1)
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

  /*
   * Rebuild the file rows from `_files`. Used when files are added or
   * removed; progress updates go through `_updateRow` so the other rows
   * (and the focus inside them) are left alone.
   */
  _renderFileList() {
    if (this._fileListEl === undefined || this._fileListEl === null) {
      return
    }

    const showList = this.getAttribute("show-list") !== "false"
    this._fileListEl.textContent = ""

    if (this._files.length === 0 || showList === false) {
      this._fileListEl.hidden = true
      return
    }

    this._fileListEl.hidden = false
    const inert = this._isInert()

    for (let i = 0; i < this._files.length; i = i + 1) {
      const entry = this._files[i]
      const li = document.createElement("li")
      li.className = "file-item"
      li.setAttribute("part", "file-item")
      li.setAttribute("data-file-id", entry.id)

      li.innerHTML = String(html`
        <span class="file-name" part="file-name" title="${entry.file.name}">${entry.file.name}</span>
        <span class="file-size" part="file-size">${formatSize(entry.file.size)}</span>
        <span class="file-status"></span>
        <button class="file-remove-btn" part="file-remove" type="button"
                aria-label="${t("mj.dropzone.removeFile", { name: entry.file.name })}" data-file-id="${entry.id}">&#x2715;</button>
      `)

      li.querySelector(".file-remove-btn").disabled = inert
      this._fileListEl.appendChild(li)
      this._updateRow(entry)
    }
    return
  }

  _findRow(fileId) {
    let found = null
    if (this._fileListEl !== undefined && this._fileListEl !== null) {
      const rows = this._fileListEl.querySelectorAll(".file-item")
      for (let i = 0; i < rows.length; i = i + 1) {
        if (rows[i].getAttribute("data-file-id") === fileId) {
          found = rows[i]
        }
      }
    }
    return found
  }

  /*
   * Bring one row's status area in line with its entry. An existing
   * progress bar is updated in place so its width transition animates.
   */
  _updateRow(entry) {
    const row = this._findRow(entry.id)
    if (row === null) {
      return
    }

    const statusEl = row.querySelector(".file-status")
    const shownStatus = statusEl.getAttribute("data-status")

    if (entry.status === "uploading") {
      const progress = clampProgress(entry.progress)
      let progressEl = statusEl.querySelector(".file-progress")

      if (shownStatus !== "uploading" || progressEl === null) {
        statusEl.textContent = ""
        progressEl = document.createElement("div")
        progressEl.className = "file-progress"
        progressEl.setAttribute("part", "file-progress")
        progressEl.setAttribute("role", "progressbar")
        progressEl.setAttribute("aria-valuemin", "0")
        progressEl.setAttribute("aria-valuemax", "100")
        progressEl.setAttribute("aria-label", t("mj.dropzone.uploading", { name: entry.file.name }))
        const barEl = document.createElement("div")
        barEl.className = "file-progress-bar"
        progressEl.appendChild(barEl)
        statusEl.appendChild(progressEl)
      }

      progressEl.setAttribute("aria-valuenow", String(progress))
      progressEl.querySelector(".file-progress-bar").style.width = `${progress}%`
    } else if (entry.status === "done") {
      if (shownStatus !== "done") {
        statusEl.textContent = ""
        const doneEl = document.createElement("span")
        doneEl.className = "file-status-done"
        doneEl.setAttribute("role", "img")
        doneEl.setAttribute("aria-label", t("mj.dropzone.uploadComplete"))
        doneEl.textContent = "✓"
        statusEl.appendChild(doneEl)
      }
    } else if (entry.status === "error") {
      statusEl.textContent = ""
      const errorEl = document.createElement("span")
      errorEl.className = "file-status-error"
      errorEl.setAttribute("part", "file-error")
      errorEl.textContent = entry.error || t("mj.dropzone.uploadError")
      statusEl.appendChild(errorEl)
    } else {
      statusEl.textContent = ""
    }

    statusEl.setAttribute("data-status", entry.status)
    return
  }

  /* Rejected files stay listed, with the reason, until dismissed. */
  _renderErrorList() {
    if (this._errorListEl === undefined || this._errorListEl === null) {
      return
    }

    this._errorListEl.textContent = ""
    this._errorListEl.hidden = this._rejectedFiles.length === 0
    const inert = this._isInert()

    /*
     * A rejected-file row is part `error-item`; `file-error` stays the error
     * text of a failed upload inside a queued file's row.
     */
    for (let i = 0; i < this._rejectedFiles.length; i = i + 1) {
      const rejection = this._rejectedFiles[i]
      const li = document.createElement("li")
      li.className = "error-item"
      li.setAttribute("part", "error-item")
      li.setAttribute("data-rejected-id", rejection.id)

      li.innerHTML = String(html`
        <span class="error-name" part="error-name" title="${rejection.file.name}">${rejection.file.name}</span>
        <span class="error-reason" part="error-reason">${rejection.reason}</span>
        <button class="file-remove-btn error-dismiss-btn" part="error-dismiss" type="button"
                aria-label="${t("mj.dropzone.dismissError", { name: rejection.file.name })}">&#x2715;</button>
      `)

      li.querySelector(".error-dismiss-btn").disabled = inert
      this._errorListEl.appendChild(li)
    }
    return
  }

  _onFileListClick(event) {
    const button = event.target.closest(".file-remove-btn")
    if (button === null) {
      return
    }
    this._removeFromUi(button.getAttribute("data-file-id"))
    return
  }

  _onFileListKeydown(event) {
    if (event.key !== "Delete" && event.key !== "Backspace") {
      return
    }
    const button = event.target.closest(".file-remove-btn")
    if (button === null) {
      return
    }
    event.preventDefault()
    this._removeFromUi(button.getAttribute("data-file-id"))
    return
  }

  _onErrorListClick(event) {
    const button = event.target.closest(".error-dismiss-btn")
    if (button === null || this._isInert() === true) {
      return
    }

    const row = button.closest(".error-item")
    const rejectedId = row.getAttribute("data-rejected-id")
    const rows = Array.from(this._errorListEl.querySelectorAll(".error-item"))
    const position = rows.indexOf(row)

    this._rejectedFiles = this._rejectedFiles.filter((rejection) => rejection.id !== rejectedId)
    this._renderErrorList()

    const buttons = this._errorListEl.querySelectorAll(".error-dismiss-btn")
    if (buttons.length > 0) {
      buttons[Math.min(position, buttons.length - 1)].focus()
    } else {
      this._browseBtn.focus()
    }
    return
  }

  /*
   * Remove a file in response to its remove button and keep keyboard focus
   * on the next row's button (or the browse button when the list empties).
   */
  _removeFromUi(fileId) {
    if (this._isInert() === true) {
      return
    }

    let position = -1
    for (let i = 0; i < this._files.length; i = i + 1) {
      if (this._files[i].id === fileId) {
        position = i
      }
    }

    const removed = this.removeFile(fileId)
    if (removed === true) {
      const buttons = this._fileListEl.querySelectorAll(".file-remove-btn")
      if (buttons.length > 0) {
        buttons[Math.min(position, buttons.length - 1)].focus()
      } else {
        this._browseBtn.focus()
      }
    }
    return
  }

  /*
   * Contribute the queued files to the owning form. ElementInternals takes a
   * File, a string or a FormData -- a FileList is coerced to a string -- so
   * the files are appended to a FormData under the element's name.
   */
  _updateFormValue() {
    const name = this.getAttribute("name") || ""
    let formValue = null

    if (name.length > 0 && this._files.length > 0) {
      formValue = new FormData()
      for (let i = 0; i < this._files.length; i = i + 1) {
        const file = this._files[i].file
        formValue.append(name, file, file.name)
      }
    }

    this._value = this._files.length > 0 ? formValue : null
    if (this._internals !== null) {
      this._internals.setFormValue(formValue)
    }
    this._refreshValidity()
    return
  }

  /* `required` is satisfied by at least one queued file. */
  _refreshValidity() {
    if (this._internals === null) {
      return
    }

    const missing = this.hasAttribute("required") === true && this._files.length === 0
    if (missing === true) {
      const message = this.getAttribute("required-message") || t("mj.dropzone.required")
      const anchor = this._validationAnchor()
      if (anchor !== null && anchor !== undefined) {
        this._internals.setValidity({ valueMissing: true }, message, anchor)
      } else {
        this._internals.setValidity({ valueMissing: true }, message)
      }
    } else {
      this._internals.setValidity({})
    }
    return
  }

  _validationAnchor() {
    const anchor = this._browseBtn !== undefined ? this._browseBtn : null
    return anchor
  }

  /* Empty both lists without emitting per-file events. */
  _discardAll() {
    this._files = []
    this._rejectedFiles = []
    this._updateFormValue()
    this._renderFileList()
    this._renderErrorList()
    return
  }

  /*
   * Update a queued file's upload state: { status, progress, error }.
   * Only the affected row is touched.
   */
  updateFile(fileId, updates) {
    let entry = null
    for (let i = 0; i < this._files.length; i = i + 1) {
      if (this._files[i].id === fileId) {
        entry = this._files[i]
      }
    }

    if (entry !== null && updates !== null && updates !== undefined) {
      const previousStatus = entry.status
      if (updates.status !== undefined) {
        entry.status = updates.status
      }
      if (updates.progress !== undefined) {
        entry.progress = updates.progress
      }
      if (updates.error !== undefined) {
        entry.error = updates.error
      }
      this._updateRow(entry)

      if (entry.status !== previousStatus) {
        if (entry.status === "done") {
          announce(t("mj.dropzone.uploadedAnnouncement", { name: entry.file.name }), "polite")
        } else if (entry.status === "error") {
          announce(t("mj.dropzone.uploadFailedAnnouncement", { name: entry.file.name, error: entry.error || t("mj.dropzone.uploadError") }), "assertive")
        }
      }
    }
    return
  }

  /*
   * Remove one queued file by id. Emits `mj-file-remove` so an upload in
   * progress can be aborted. Returns true when the file was queued.
   */
  removeFile(fileId) {
    let removedEntry = null
    for (let i = 0; i < this._files.length; i = i + 1) {
      if (this._files[i].id === fileId) {
        removedEntry = this._files[i]
      }
    }

    if (removedEntry !== null) {
      this._files = this._files.filter((entry) => entry.id !== fileId)
      this._updateFormValue()
      this.emit("mj-file-remove", { fileId: fileId, file: removedEntry.file })
      announce(t("mj.dropzone.removedAnnouncement", { name: removedEntry.file.name }), "assertive")
      this._renderFileList()
    }

    const removed = removedEntry !== null
    return removed
  }

  /* Empty the selection and the rejected-file list, e.g. after an upload. */
  clear() {
    this._discardAll()
    return
  }

  get files() {
    return this._files
  }

  get rejectedFiles() {
    return this._rejectedFiles
  }

  /*
   * Like a native file input, the value is the first file's name and can
   * only be assigned the empty string, which clears the selection.
   */
  get value() {
    const name = this._files.length > 0 ? this._files[0].file.name : ""
    return name
  }

  set value(next) {
    if (next === "" || next === null || next === undefined) {
      this._discardAll()
    }
    return
  }
}
