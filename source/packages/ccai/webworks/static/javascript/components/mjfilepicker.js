/*
 * mjfilepicker.js
 *
 * <mj-file-picker> — drag-and-drop file input with validation, image previews,
 * and optional immediate upload. Form-associated.
 *
 * State lives in `_fileItems` (one `{ id, file, status, progress, objectUrl,
 * xhr }` per selected file); the file list is built from it with DOM APIs, so
 * a file name never passes through markup. The form receives the File
 * objects themselves, one entry per file under the control's name.
 *
 * Upload options (used when `upload-url` is set):
 *   uploadHeaders      property: `{ name: value }` request headers, e.g. a CSRF token
 *   with-credentials   attribute: send cookies on cross-origin uploads
 *   retry(file)        method: upload a failed file again
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { announce } from "../core/announcer.js";
import { t } from "../core/intl.js";
import { html } from "../core/html.js";

const STYLES = `
:host { display: block; }

.dropzone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: var(--mj-file-picker-dropzone-min-height, 8rem);
  border: var(--mj-file-picker-dropzone-border, 2px dashed var(--mj-border-strong));
  border-radius: var(--mj-file-picker-border-radius, var(--mj-radius-md));
  padding: var(--mj-space-4);
  text-align: center;
  cursor: pointer;
  transition: border-color var(--mj-motion-fast), background var(--mj-motion-fast);
  background: var(--mj-surface);
}
.dropzone.drag-over {
  border: var(--mj-file-picker-dropzone-active-border, 2px dashed var(--mj-accent));
  background: var(--mj-file-picker-dropzone-active-bg, var(--mj-bg-subtle));
}
:host([disabled]) .dropzone { opacity: 0.55; pointer-events: none; }
:host([invalid]) .dropzone { border-color: var(--mj-color-danger); }
.dropzone:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

/* Button variant: only the choose button, no drop area. */
:host([variant="button"]) .dropzone {
  display: inline-flex;
  min-height: 0;
  border: none;
  padding: 0;
  background: none;
  cursor: default;
}
:host([variant="button"]) .dropzone-icon,
:host([variant="button"]) .dropzone-label,
:host([variant="button"]) .dropzone-hint { display: none; }
:host([variant="button"]) .choose-btn { margin-block-start: 0; }

.native-input {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  clip-path: inset(50%);
  opacity: 0;
}

.dropzone-icon { font-size: 2rem; margin-block-end: var(--mj-space-2); color: var(--mj-text-muted); }
.dropzone-label { color: var(--mj-text); font-size: var(--mj-font-size-md); margin-block-end: var(--mj-space-1); }
.dropzone-hint { font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }

.choose-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--mj-space-2);
  padding: var(--mj-space-1) var(--mj-space-3);
  background: var(--mj-accent);
  color: var(--mj-text-on-accent);
  border: none;
  border-radius: var(--mj-radius-md);
  font: inherit;
  font-size: var(--mj-font-size-sm);
  cursor: pointer;
  margin-block-start: var(--mj-space-2);
}
.choose-btn:hover { background: var(--mj-accent-hover); }
.choose-btn:disabled { cursor: not-allowed; }
.choose-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.file-list {
  margin-block-start: var(--mj-space-3);
  display: flex;
  flex-direction: column;
  gap: var(--mj-space-2);
}
.file-item {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  padding: var(--mj-space-2) var(--mj-space-3);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-md);
  background: var(--mj-surface);
}
.file-preview {
  width: var(--mj-file-picker-preview-size, 3rem);
  height: var(--mj-file-picker-preview-size, 3rem);
  object-fit: cover;
  border-radius: var(--mj-radius-sm);
  flex-shrink: 0;
}
.file-icon {
  width: var(--mj-file-picker-preview-size, 3rem);
  height: var(--mj-file-picker-preview-size, 3rem);
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--mj-bg-muted);
  border-radius: var(--mj-radius-sm);
  flex-shrink: 0;
  color: var(--mj-text-muted);
  font-size: 1.5rem;
}
.file-info { flex: 1; min-width: 0; }
.file-name {
  font-size: var(--mj-font-size-sm);
  font-weight: var(--mj-font-weight-medium);
  color: var(--mj-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.file-size { font-size: var(--mj-font-size-xs); color: var(--mj-text-muted); }
.file-status { font-size: var(--mj-font-size-xs); }
.file-status.success { color: var(--mj-color-success); }
.file-status.error { color: var(--mj-color-danger); }

.progress-bar {
  height: 4px;
  background: var(--mj-bg-muted);
  border-radius: var(--mj-radius-pill);
  margin-block-start: var(--mj-space-1);
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: var(--mj-accent);
  border-radius: var(--mj-radius-pill);
  transition: width var(--mj-motion-fast);
}

.remove-btn {
  flex-shrink: 0;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--mj-text-muted);
  padding: var(--mj-space-1);
  border-radius: var(--mj-radius-sm);
}
.remove-btn:hover { color: var(--mj-color-danger); }
.remove-btn:disabled { cursor: not-allowed; opacity: 0.55; }
.retry-btn {
  flex-shrink: 0;
  padding: var(--mj-space-1) var(--mj-space-2);
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-sm);
  background: var(--mj-surface);
  color: var(--mj-text);
  font: inherit;
  font-size: var(--mj-font-size-xs);
  cursor: pointer;
}
.retry-btn:hover { background: var(--mj-bg-muted); }
.retry-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}
.remove-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}

.error-msg {
  margin-block-start: var(--mj-space-2);
  font-size: var(--mj-font-size-sm);
  color: var(--mj-color-danger);
}
.error-msg p { margin: 0; }
`;

function formatBytes(bytes) {
  if (bytes < 1024) {
    return `${bytes} B`
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

/* A file that is ready to upload shows no status text. */
const STATUS_TEXT_KEYS = {
  uploading: "mj.filePicker.statusUploading",
  success: "mj.filePicker.statusUploaded",
  error: "mj.filePicker.statusFailed"
};

export class MjFilePicker extends FormControlMixin(MjElement) {
  static tagName = "mj-file-picker";
  static styles = STYLES;
  static watched = [
    "name", "multiple", "accept", "max-size", "max-files", "disabled", "required",
    "variant", "upload-url", "label", "dropzone-label", "with-credentials"
  ];

  constructor() {
    super()
    this._initFormControl()

    /* One entry per selected file; `files` is derived from it. */
    this._fileItems = []

    /* Validation messages of the latest selection, all shown until the next one. */
    this._errors = []

    this._uploadHeaders = {}
    this._formDisabled = false
    this._nativeInput = null
    this._dragCounter = 0
  }

  render() {
    const markup = html`
      <div class="dropzone" part="dropzone" role="group" aria-label="${t("mj.filePicker.dropzoneRegion")}" tabindex="0">
        <span class="dropzone-icon" part="dropzone-icon" aria-hidden="true">
          <slot name="icon">📁</slot>
        </span>
        <span class="dropzone-label" part="dropzone-label"></span>
        <span class="dropzone-hint" part="dropzone-hint"><slot name="hint"></slot></span>
        <button class="choose-btn" part="choose-button" type="button"></button>
        <input class="native-input" type="file" tabindex="-1" aria-hidden="true" />
      </div>
      <div class="file-list" part="file-list" role="list"></div>
      <div class="error-msg" part="error" role="alert" hidden></div>
    `
    return markup
  }

  afterRender() {
    this._dropzone = this.$(".dropzone")
    this._fileList = this.$(".file-list")
    this._errorMsg = this.$(".error-msg")
    this._chooseBtn = this.$(".choose-btn")
    this._dropzoneLabel = this.$(".dropzone-label")

    /*
     * The native chooser lives in the shadow root and is rendered with it, so
     * a reconnect never leaves a second one behind.
     */
    this._nativeInput = this.$(".native-input")

    this.listen(this._chooseBtn, "click", this._onChooseClick.bind(this))
    this.listen(this._dropzone, "click", this._onDropzoneClick.bind(this))
    this.listen(this._dropzone, "keydown", this._onDropzoneKeydown.bind(this))
    this.listen(this._dropzone, "dragover", this._onDragOver.bind(this))
    this.listen(this._dropzone, "dragenter", this._onDragEnter.bind(this))
    this.listen(this._dropzone, "dragleave", this._onDragLeave.bind(this))
    this.listen(this._dropzone, "drop", this._onDrop.bind(this))
    this.listen(this._nativeInput, "change", this._onNativeChange.bind(this))
    this.listen(this._nativeInput, "click", (event) => {
      /* The chooser's own click must not look like a dropzone click. */
      event.stopPropagation()
    })

    /* One delegated listener; the rows are rebuilt when files come and go. */
    this.listen(this._fileList, "click", this._onFileListClick.bind(this))

    /* Everything below paints the fresh shadow DOM from the fields. */
    this._syncLabels()
    this._syncNativeInput()
    this._syncDisabled()
    this._renderFileList()
    this._renderErrors()
    this._syncFormValue()

    /* Uploads interrupted by a disconnect start again. */
    this._uploadPending()
    return
  }

  onDisconnected() {
    /* Stop requests in flight and release the preview blobs. */
    for (let index = 0; index < this._fileItems.length; index = index + 1) {
      const item = this._fileItems[index]
      this._abortUpload(item)
      this._revokePreview(item)
    }
    this._dragCounter = 0
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "label" || name === "dropzone-label") {
      this._syncLabels()
    }
    if (name === "accept" || name === "multiple") {
      this._syncNativeInput()
    }
    if (name === "disabled" || name === "variant") {
      this._syncDisabled()
    }
    if (name === "name") {
      this._syncFormValue()
    }
    if (name === "required") {
      this._refreshValidity()
    }
    if (name === "upload-url") {
      this._uploadPending()
    }
    return
  }

  onFormDisabled(disabled) {
    this._formDisabled = disabled === true
    this._syncDisabled()
    return
  }

  _isDisabled() {
    const disabled = this.hasAttribute("disabled") === true || this._formDisabled === true
    return disabled
  }

  _syncLabels() {
    if (this._chooseBtn === undefined || this._chooseBtn === null) {
      return
    }
    this._dropzoneLabel.textContent = this.getAttribute("dropzone-label") || t("mj.filePicker.dropzoneLabel")
    this._chooseBtn.textContent = this.getAttribute("label") || t("mj.filePicker.chooseFiles")
    return
  }

  /* Forward `accept` and `multiple` to the native chooser. */
  _syncNativeInput() {
    if (this._nativeInput === undefined || this._nativeInput === null) {
      return
    }
    this._nativeInput.multiple = this.hasAttribute("multiple")
    this._nativeInput.accept = this.getAttribute("accept") || ""
    return
  }

  /* A disabled picker has no tab stops and no working buttons. */
  _syncDisabled() {
    if (this._dropzone === undefined || this._dropzone === null) {
      return
    }
    const disabled = this._isDisabled()
    const buttonVariant = this.getAttribute("variant") === "button"

    this._chooseBtn.disabled = disabled
    this._nativeInput.disabled = disabled
    this._dropzone.tabIndex = disabled === true || buttonVariant === true ? -1 : 0
    if (disabled === true) {
      this._dropzone.setAttribute("aria-disabled", "true")
    } else {
      this._dropzone.removeAttribute("aria-disabled")
    }

    const rowButtons = this._fileList.querySelectorAll("button")
    rowButtons.forEach((button) => {
      button.disabled = disabled
    })
    return
  }

  _openChooser() {
    if (this._isDisabled() === false) {
      this._nativeInput.click()
    }
    return
  }

  _onChooseClick(event) {
    event.stopPropagation()
    this._openChooser()
    return
  }

  _onDropzoneClick(event) {
    if (event.target === this._chooseBtn || this.getAttribute("variant") === "button") {
      return
    }
    this._openChooser()
    return
  }

  _onDropzoneKeydown(event) {
    /* Keys pressed on the choose button are the button's own business. */
    if (event.target !== this._dropzone) {
      return
    }
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      this._openChooser()
    }
    return
  }

  _onDragOver(event) {
    event.preventDefault()
    return
  }

  _onDragEnter() {
    if (this._isDisabled() === true) {
      return
    }
    this._dragCounter = this._dragCounter + 1
    if (this._dragCounter === 1) {
      this._dropzone.classList.add("drag-over")
      announce(t("mj.filePicker.dropHere"), "polite")
      this.emit("mj-drag-enter", {})
    }
    return
  }

  _onDragLeave() {
    if (this._dragCounter === 0) {
      return
    }
    this._dragCounter = this._dragCounter - 1
    if (this._dragCounter === 0) {
      this._dropzone.classList.remove("drag-over")
      this.emit("mj-drag-leave", {})
    }
    return
  }

  _onDrop(event) {
    event.preventDefault()
    this._dragCounter = 0
    this._dropzone.classList.remove("drag-over")
    if (this._isDisabled() === true) {
      return
    }

    const droppedFiles = event.dataTransfer !== null && event.dataTransfer !== undefined
      ? Array.from(event.dataTransfer.files)
      : []
    this._addFiles(droppedFiles)
    return
  }

  _onNativeChange(event) {
    /* The chooser's `change` is internal; the component emits its own. */
    event.stopPropagation()
    if (this._isDisabled() === true) {
      this._nativeInput.value = ""
      return
    }
    const selected = Array.from(this._nativeInput.files || [])
    this._nativeInput.value = ""
    this._addFiles(selected)
    return
  }

  /* Does `file` match the `accept` list (extensions, type/*, exact MIME types)? */
  _isAccepted(file, accept) {
    let accepted = true

    if (accept.length > 0) {
      const fileName = file.name.toLowerCase()
      const fileType = (file.type || "").toLowerCase()
      const acceptTypes = accept.split(",").map((entry) => entry.trim().toLowerCase()).filter((entry) => entry.length > 0)
      accepted = acceptTypes.some((type) => {
        let matches = false
        if (type.startsWith(".") === true) {
          matches = fileName.endsWith(type)
        } else if (type.endsWith("/*") === true) {
          matches = fileType.startsWith(type.slice(0, -1))
        } else {
          matches = fileType === type
        }
        return matches
      })
    }

    return accepted
  }

  /*
   * Validate and take over newly chosen or dropped files. Without `multiple`
   * only the first valid file is kept and it replaces the current one; when
   * no file is valid the current selection stays as it is.
   */
  _addFiles(newFiles) {
    const maxSize = parseInt(this.getAttribute("max-size") || "0", 10)
    const maxFiles = parseInt(this.getAttribute("max-files") || "0", 10)
    const accept = this.getAttribute("accept") || ""
    const isMultiple = this.hasAttribute("multiple")

    this._errors = []
    const accepted = []

    for (let index = 0; index < newFiles.length; index = index + 1) {
      const file = newFiles[index]

      if (isMultiple === false && accepted.length >= 1) {
        /* A single-file picker takes one file per selection. */
        break
      }

      if (this._isAccepted(file, accept) === false) {
        this.emit("mj-file-error", { file: file, error: "type" })
        this._errors.push(t("mj.filePicker.typeError", { name: file.name }))
        continue
      }

      if (maxSize > 0 && file.size > maxSize) {
        this.emit("mj-file-error", { file: file, error: "size" })
        this._errors.push(t("mj.filePicker.sizeError", { name: file.name }))
        continue
      }

      const count = isMultiple === true ? this._fileItems.length + accepted.length : accepted.length
      if (maxFiles > 0 && count >= maxFiles) {
        this.emit("mj-file-error", { file: file, error: "count" })
        this._errors.push(t("mj.filePicker.countError", { max: maxFiles }))
        continue
      }

      const proceed = this.emit("mj-file-add", { file: file }, { cancelable: true })
      if (proceed === false) {
        continue
      }

      accepted.push(file)
    }

    this._renderErrors()
    if (this._errors.length > 0) {
      announce(this._errors.join(" "), "assertive")
    }

    if (accepted.length === 0) {
      return
    }

    if (isMultiple === false) {
      /* The new file replaces the old one: stop its upload, free its preview. */
      for (let index = 0; index < this._fileItems.length; index = index + 1) {
        this._discardItem(this._fileItems[index])
      }
      this._fileItems = []
    }

    for (let index = 0; index < accepted.length; index = index + 1) {
      this._fileItems.push({
        file: accepted[index],
        status: "ready",
        progress: 0,
        id: nextId("mj-fi"),
        objectUrl: undefined,
        xhr: null
      })
    }

    this._syncFormValue()
    this._renderFileList()
    this.emit("mj-change", { files: this.files })
    this._uploadPending()
    return
  }

  /*
   * Hand the File objects to the form, one entry per file under the
   * control's name. `_value` holds the joined names so the mixin's `required`
   * check sees an empty picker as empty.
   */
  _syncFormValue() {
    const files = this.files
    const name = this.getAttribute("name") || ""

    this._value = files.map((file) => file.name).join(",")
    if (this._internals !== null && this._internals !== undefined) {
      const formData = new FormData()
      if (name.length > 0) {
        for (let index = 0; index < files.length; index = index + 1) {
          formData.append(name, files[index])
        }
      }
      this._internals.setFormValue(formData)
    }
    this._refreshValidity()
    return
  }

  /* ----- file list ----- */

  _revokePreview(item) {
    if (item.objectUrl !== undefined) {
      URL.revokeObjectURL(item.objectUrl)
      item.objectUrl = undefined
    }
    return
  }

  /* Stop an upload in flight. The item goes back to "ready" without events. */
  _abortUpload(item) {
    if (item.xhr !== null) {
      const xhr = item.xhr
      item.xhr = null
      xhr.abort()
      item.status = "ready"
      item.progress = 0
    }
    return
  }

  _discardItem(item) {
    this._abortUpload(item)
    this._revokePreview(item)
    return
  }

  /* Build one row with DOM APIs: the file name is only ever text. */
  _buildRow(item) {
    const fileName = item.file.name
    const isImage = (item.file.type || "").startsWith("image/")

    const row = document.createElement("div")
    row.className = "file-item"
    row.setAttribute("part", "file-item")
    row.setAttribute("role", "listitem")
    row.dataset.id = item.id

    if (isImage === true) {
      if (item.objectUrl === undefined) {
        item.objectUrl = URL.createObjectURL(item.file)
      }
      const preview = document.createElement("img")
      preview.className = "file-preview"
      preview.setAttribute("part", "file-preview")
      preview.src = item.objectUrl
      preview.alt = ""
      row.appendChild(preview)
    } else {
      const icon = document.createElement("span")
      icon.className = "file-icon"
      icon.setAttribute("part", "file-preview")
      icon.setAttribute("aria-hidden", "true")
      icon.textContent = "📄"
      row.appendChild(icon)
    }

    const info = document.createElement("div")
    info.className = "file-info"

    const nameEl = document.createElement("div")
    nameEl.className = "file-name"
    nameEl.setAttribute("part", "file-name")
    nameEl.textContent = fileName
    info.appendChild(nameEl)

    const sizeEl = document.createElement("div")
    sizeEl.className = "file-size"
    sizeEl.setAttribute("part", "file-size")
    sizeEl.textContent = formatBytes(item.file.size)
    info.appendChild(sizeEl)

    const statusEl = document.createElement("div")
    statusEl.className = "file-status"
    statusEl.setAttribute("part", "file-status")
    info.appendChild(statusEl)

    const progressBar = document.createElement("div")
    progressBar.className = "progress-bar"
    progressBar.setAttribute("part", "file-progress")
    progressBar.setAttribute("role", "progressbar")
    progressBar.setAttribute("aria-valuemin", "0")
    progressBar.setAttribute("aria-valuemax", "100")
    progressBar.setAttribute("aria-label", t("mj.filePicker.progressLabel", { name: fileName }))
    const progressFill = document.createElement("div")
    progressFill.className = "progress-fill"
    progressBar.appendChild(progressFill)
    info.appendChild(progressBar)

    row.appendChild(info)

    const retryBtn = document.createElement("button")
    retryBtn.type = "button"
    retryBtn.className = "retry-btn"
    retryBtn.setAttribute("part", "file-retry")
    retryBtn.setAttribute("aria-label", t("mj.filePicker.retryLabel", { name: fileName }))
    retryBtn.dataset.action = "retry"
    retryBtn.textContent = t("mj.filePicker.retry")
    row.appendChild(retryBtn)

    const removeBtn = document.createElement("button")
    removeBtn.type = "button"
    removeBtn.className = "remove-btn"
    removeBtn.setAttribute("part", "file-remove")
    removeBtn.setAttribute("aria-label", `${t("core.remove")} ${fileName}`)
    removeBtn.dataset.action = "remove"
    removeBtn.innerHTML = `<svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
      <path d="M12 4 8 8l4 4-1 1-4-4-4 4-1-1 4-4-4-4 1-1 4 4 4-4z"/>
    </svg>`
    row.appendChild(removeBtn)

    this._updateRow(item, row)
    return row
  }

  /*
   * Bring one row's status, progress bar and buttons in line with its item.
   * Upload progress goes through here, so the other rows, the thumbnails and
   * a focused button are left alone.
   */
  _updateRow(item, existingRow) {
    let row = existingRow
    if (row === undefined || row === null) {
      const rows = Array.from(this._fileList.querySelectorAll(".file-item"))
      row = rows.find((candidate) => candidate.dataset.id === item.id)
    }
    if (row === undefined || row === null) {
      return
    }

    const statusEl = row.querySelector(".file-status")
    const statusKey = STATUS_TEXT_KEYS[item.status]
    statusEl.textContent = statusKey !== undefined ? t(statusKey) : ""
    statusEl.classList.toggle("success", item.status === "success")
    statusEl.classList.toggle("error", item.status === "error")
    statusEl.hidden = statusEl.textContent.length === 0

    const progressBar = row.querySelector(".progress-bar")
    progressBar.hidden = item.status !== "uploading"
    progressBar.setAttribute("aria-valuenow", String(item.progress))
    progressBar.querySelector(".progress-fill").style.width = `${item.progress}%`

    const retryBtn = row.querySelector(".retry-btn")
    retryBtn.hidden = item.status !== "error"

    const disabled = this._isDisabled()
    retryBtn.disabled = disabled
    row.querySelector(".remove-btn").disabled = disabled
    return
  }

  _renderFileList() {
    if (this._fileList === undefined || this._fileList === null) {
      return
    }
    this._fileList.textContent = ""
    for (let index = 0; index < this._fileItems.length; index = index + 1) {
      this._fileList.appendChild(this._buildRow(this._fileItems[index]))
    }
    return
  }

  _onFileListClick(event) {
    const button = event.target.closest("button[data-action]")
    if (button === null || this._isDisabled() === true) {
      return
    }
    const row = button.closest(".file-item")
    const item = this._fileItems.find((candidate) => candidate.id === row.dataset.id)
    if (item === undefined) {
      return
    }
    if (button.dataset.action === "remove") {
      this._removeFile(item.id)
    } else if (button.dataset.action === "retry") {
      this.retry(item.file)
    }
    return
  }

  _removeFile(itemId) {
    const idx = this._fileItems.findIndex((i) => i.id === itemId)
    if (idx < 0) {
      return
    }
    const item = this._fileItems[idx]

    /* Keep focus in the list: the next row's remove button, else the chooser. */
    const rows = Array.from(this._fileList.querySelectorAll(".file-item"))
    const hadFocus = rows[idx] !== undefined && rows[idx].contains(this.shadowRoot.activeElement)

    this._discardItem(item)
    this._fileItems.splice(idx, 1)
    this._syncFormValue()
    this._renderFileList()

    if (hadFocus === true) {
      const remaining = this._fileList.querySelectorAll(".remove-btn")
      if (remaining.length > 0) {
        remaining[Math.min(idx, remaining.length - 1)].focus()
      } else {
        this._chooseBtn.focus()
      }
    }

    this.emit("mj-file-remove", { file: item.file })
    this.emit("mj-change", { files: this.files })
    return
  }

  /* Show every validation message of the latest selection until the next one. */
  _renderErrors() {
    if (this._errorMsg === undefined || this._errorMsg === null) {
      return
    }
    this._errorMsg.textContent = ""
    for (let index = 0; index < this._errors.length; index = index + 1) {
      const line = document.createElement("p")
      line.textContent = this._errors[index]
      this._errorMsg.appendChild(line)
    }
    this._errorMsg.hidden = this._errors.length === 0
    return
  }

  /* ----- upload ----- */

  /* Start the upload of every file that is waiting, when `upload-url` is set. */
  _uploadPending() {
    const uploadUrl = this.getAttribute("upload-url") || ""
    if (uploadUrl.length === 0 || this.isConnected === false) {
      return
    }
    for (let index = 0; index < this._fileItems.length; index = index + 1) {
      const item = this._fileItems[index]
      if (item.status === "ready") {
        this._uploadItem(item, uploadUrl)
      }
    }
    return
  }

  _uploadItem(item, uploadUrl) {
    item.status = "uploading"
    item.progress = 0
    this._updateRow(item)

    const formData = new FormData()
    formData.append(this.getAttribute("name") || "file", item.file)

    const xhr = new XMLHttpRequest()
    item.xhr = xhr
    xhr.open("POST", uploadUrl)
    xhr.withCredentials = this.hasAttribute("with-credentials")

    const headerNames = Object.keys(this._uploadHeaders)
    for (let index = 0; index < headerNames.length; index = index + 1) {
      const headerName = headerNames[index]
      xhr.setRequestHeader(headerName, String(this._uploadHeaders[headerName]))
    }

    const fail = (message) => {
      if (item.xhr !== xhr) {
        return
      }
      item.xhr = null
      item.status = "error"
      this._updateRow(item)
      this.emit("mj-upload-error", { file: item.file, error: new Error(message) })
      announce(t("mj.filePicker.uploadFailed", { name: item.file.name }), "assertive")
    }

    xhr.upload.addEventListener("progress", (event) => {
      if (item.xhr === xhr && event.lengthComputable === true) {
        item.progress = Math.round((event.loaded / event.total) * 100)
        this._updateRow(item)
        this.emit("mj-upload-progress", {
          file: item.file,
          loaded: event.loaded,
          total: event.total,
          percent: item.progress
        })
      }
    })

    xhr.addEventListener("load", () => {
      if (item.xhr !== xhr) {
        return
      }
      /* Only a 2xx answer means the server took the file. */
      if (xhr.status >= 200 && xhr.status < 300) {
        item.xhr = null
        item.status = "success"
        item.progress = 100
        this._updateRow(item)
        this.emit("mj-upload-success", { file: item.file, response: xhr.responseText })
        announce(t("mj.filePicker.uploaded", { name: item.file.name }), "polite")
      } else {
        fail(`Upload failed with status ${xhr.status}`)
      }
    })

    xhr.addEventListener("error", () => {
      fail("Upload failed")
    })

    xhr.send(formData)
    return
  }

  _validationAnchor() {
    const anchor = this._chooseBtn !== undefined ? this._chooseBtn : null
    return anchor
  }

  onFormReset() {
    for (let index = 0; index < this._fileItems.length; index = index + 1) {
      this._discardItem(this._fileItems[index])
    }
    this._fileItems = []
    this._errors = []
    this._syncFormValue()
    this._renderFileList()
    this._renderErrors()
    return
  }

  /* ----- scriptable API ----- */

  get files() {
    const files = this._fileItems.map((item) => item.file)
    return files
  }

  get fileItems() {
    return this._fileItems.slice()
  }

  /* The selected file names joined with commas (the File objects are in `files`). */
  get value() {
    return this._value
  }

  /* Like a native file input, the value can only be cleared from script. */
  set value(next) {
    if (next === "" || next === null || next === undefined) {
      this.onFormReset()
    }
    return
  }

  /* Request headers sent with every upload, e.g. `{ "X-CSRF-Token": token }`. */
  get uploadHeaders() {
    return Object.assign({}, this._uploadHeaders)
  }

  set uploadHeaders(headers) {
    this._uploadHeaders = headers !== null && typeof headers === "object" ? Object.assign({}, headers) : {}
    return
  }

  /* Upload a failed file again. `file` is one of `files`. */
  retry(file) {
    const uploadUrl = this.getAttribute("upload-url") || ""
    const item = this._fileItems.find((candidate) => candidate.file === file)
    if (item !== undefined && item.status === "error" && uploadUrl.length > 0) {
      this._uploadItem(item, uploadUrl)
    }
    return
  }

  focus(options) {
    if (this._chooseBtn !== undefined && this._chooseBtn !== null) {
      this._chooseBtn.focus(options)
    }
    return
  }
}
